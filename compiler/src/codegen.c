#include "codegen.h"
#include "arena.h"
#include <stdio.h>
#include <string.h>

/* ── name mangling: emit $mod__name when sym has an owning module ── */
static void emit_mangled_name(IRBuf *ir, Sym *sym) {
    if (sym && sym->module) {
        ir_emit(ir, "$%s__%s", sym->module, sym->name);
    } else {
        ir_emit(ir, "$%s", sym->name ? sym->name : "?");
    }
}

/* ── side table: map Sym* → IRVal for local vars ── */
#define MAX_LOCALS 512
#define MAX_LOOP_DEPTH 32
typedef struct {
    Sym  *sym;
    IRVal value;        /* SSA temp for immutable, stack slot addr for mutable */
    int   is_stack;     /* 1 if value is a stack slot address */
} LocalEntry;

typedef struct {
    IRBuf      *ir;
    LocalEntry  locals[MAX_LOCALS];
    int         nlocals;
    Type       *current_ret_type;  /* function return type for checking */
    IRVal       sret_slot;        /* hidden return slot for struct returns */
    int         has_sret;         /* 1 if function returns struct via sret */
    /* Loop label stack: top is innermost loop.
       continue_target = where `continue` jumps (for: after body, before i++;
                                             while: same as loop_starts) */
    IRVal       loop_starts[MAX_LOOP_DEPTH];
    IRVal       loop_ends[MAX_LOOP_DEPTH];
    IRVal       loop_continues[MAX_LOOP_DEPTH];
    int         loop_depth;
} CGContext;

static void cg_add_local(CGContext *cg, Sym *sym, IRVal val, int is_stack) {
    if (cg->nlocals < MAX_LOCALS) {
        cg->locals[cg->nlocals].sym = sym;
        cg->locals[cg->nlocals].value = val;
        cg->locals[cg->nlocals].is_stack = is_stack;
        cg->nlocals++;
    }
}

static IRVal cg_find_local(CGContext *cg, Sym *sym, int *is_stack) {
    for (int i = 0; i < cg->nlocals; i++) {
        if (cg->locals[i].sym == sym) {
            if (is_stack) *is_stack = cg->locals[i].is_stack;
            return cg->locals[i].value;
        }
    }
    IRVal zero = {0};
    return zero;
}

/* ── forward ── */
static IRVal cg_expr(CGContext *cg, Node *n);
static void   cg_stmt(CGContext *cg, Node *n);

/* ── helpers ── */
static IRVal ir_new_int(int64_t val) {
    IRVal v;
    v.kind = IRVAL_INT;
    v.ival = val;
    v.qbe_type = 'l';  /* used as offset in pointer arithmetic */
    v.name = NULL;
    return v;
}

/* Emit correct load instruction for the given type.
   Sub-word types (i8/u8/i16/u16/bool) use sign/zero-extension loads
   that always return a word. The caller must pre-allocate `dst` with
   type 'w' (word) for sub-word types, not the sub-word letter. */
static void cg_emit_load(CGContext *cg, IRVal dst, Type *t, IRVal addr) {
    if (!t) {
        ir_emit_load(cg->ir, dst, 'w', addr);
        return;
    }
    if (t->kind == KIND_PRIMITIVE) {
        const char *insn = NULL;
        switch (t->prim) {
        case PRIM_I8:  insn = "loadsb"; break;
        case PRIM_U8:  insn = "loadub"; break;
        case PRIM_BOOL: insn = "loadub"; break;
        case PRIM_I16: insn = "loadsh"; break;
        case PRIM_U16: insn = "loaduh"; break;
        default: break;
        }
        if (insn) {
            /* sub-word: always returns word */
            ir_emit(cg->ir, "    %%t%d =w %s %%t%d\n", dst.id, insn, addr.id);
            return;
        }
    }
    char qt = qbe_type_of(t);
    ir_emit_load(cg->ir, dst, qt, addr);
}

/* Emit correct store instruction for the given type.
   Sub-word types use byte/half stores; struct values are field-by-field copy
   (since QBE has no aggregate store). */
static void cg_copy_struct(CGContext *cg, Type *st, IRVal dst_addr, IRVal src_addr);  /* fwd decl */

static void cg_emit_store(CGContext *cg, Type *t, IRVal val, IRVal addr) {
    if (!t) {
        ir_emit_store(cg->ir, 'w', val, addr);
        return;
    }
    if (t->kind == KIND_STRUCT) {
        /* struct value: `val` is the struct's stack-slot address; copy field-by-field */
        cg_copy_struct(cg, t, addr, val);
        return;
    }
    if (t->kind == KIND_PRIMITIVE) {
        switch (t->prim) {
        case PRIM_I8: case PRIM_U8: case PRIM_BOOL:
            ir_emit(cg->ir, "    storeb %%t%d, %%t%d\n", val.id, addr.id);
            return;
        case PRIM_I16: case PRIM_U16:
            ir_emit(cg->ir, "    storeh %%t%d, %%t%d\n", val.id, addr.id);
            return;
        default: break;
        }
    }
    ir_emit_store(cg->ir, qbe_type_of(t), val, addr);
}

/* Copy a struct value from src_addr to dst_addr, field by field.
   Handles nested structs recursively. */
static void cg_copy_struct(CGContext *cg, Type *st, IRVal dst_addr, IRVal src_addr) {
    if (!st || st->kind != KIND_STRUCT) return;
    for (size_t i = 0; i < st->struct_type.nfields; i++) {
        Type *ft = st->struct_type.fields[i].type;
        size_t offset = st->struct_type.fields[i].offset;
        /* compute field addresses */
        IRVal src_off = ir_new_tmp(cg->ir, 'l');
        IRVal dst_off = ir_new_tmp(cg->ir, 'l');
        if (offset > 0) {
            ir_emit_binary(cg->ir, src_off, "add", src_addr, ir_new_int((int64_t)offset));
            ir_emit_binary(cg->ir, dst_off, "add", dst_addr, ir_new_int((int64_t)offset));
        } else {
            ir_emit(cg->ir, "    %%t%d =l copy %%t%d\n", src_off.id, src_addr.id);
            ir_emit(cg->ir, "    %%t%d =l copy %%t%d\n", dst_off.id, dst_addr.id);
        }
        if (ft->kind == KIND_STRUCT) {
            cg_copy_struct(cg, ft, dst_off, src_off);
        } else {
            IRVal fval = ir_new_tmp(cg->ir, qbe_type_of(ft));
            cg_emit_load(cg, fval, ft, src_off);
            cg_emit_store(cg, ft, fval, dst_off);
        }
    }
}

static IRVal cg_match_pattern(CGContext *cg, IRVal matched, Node *pattern) {
    switch (pattern->kind) {
    case NODE_PATTERN_LIT: {
        NodePatternLit *pl = node_pattern_lit_data(pattern);
        char qt = matched.qbe_type;  /* use same type as matched value */
        IRVal lit = ir_new_tmp(cg->ir, qt);
        ir_emit_copy(cg->ir, lit, pl->value);
        IRVal cmp = ir_new_tmp(cg->ir, 'w');
        ir_emit_binary(cg->ir, cmp, "ceqw", matched, lit);
        return cmp;
    }
    case NODE_PATTERN_WILD: {
        /* always matches */
        IRVal cmp = ir_new_tmp(cg->ir, 'w');
        ir_emit_copy(cg->ir, cmp, 1);
        return cmp;
    }
    case NODE_PATTERN_RANGE: {
        NodePatternRange *pr = node_pattern_range_data(pattern);
        /* lo <= matched */
        IRVal lo_val = cg_expr(cg, pr->lo);
        IRVal cmp_lo = ir_new_tmp(cg->ir, 'w');
        ir_emit_binary(cg->ir, cmp_lo, "cslew", lo_val, matched);
        /* matched <= hi */
        IRVal hi_val = cg_expr(cg, pr->hi);
        IRVal cmp_hi = ir_new_tmp(cg->ir, 'w');
        ir_emit_binary(cg->ir, cmp_hi, "cslew", matched, hi_val);
        /* lo <= matched && matched <= hi */
        IRVal result = ir_new_tmp(cg->ir, 'w');
        ir_emit_binary(cg->ir, result, "and", cmp_lo, cmp_hi);
        return result;
    }
    default: {
        IRVal v = ir_new_tmp(cg->ir, 'w');
        ir_emit_copy(cg->ir, v, 1);
        return v;
    }
    }
}

/* ── codegen for expressions ── */

/* Insert QBE conversion if arg's qbe_type != param's qbe_type.
   v1.0.0: needed so f64 literal → f32 param emits truncd (otherwise
   the caller passes 8 bytes via movsd and the callee reads only 4
   via ucomiss, silently corrupting f32 args). */
static IRVal cg_convert_arg(CGContext *cg, IRVal arg, Type *src_t, Type *dst_t) {
    if (!src_t || !dst_t) return arg;
    if (src_t->kind != KIND_PRIMITIVE || dst_t->kind != KIND_PRIMITIVE) return arg;
    char src_qt = qbe_type_of(src_t);
    char dst_qt = qbe_type_of(dst_t);
    if (src_qt == dst_qt && src_t->prim == dst_t->prim) return arg;
    const char *conv = NULL;
    if (src_qt == 'd' && (dst_qt == 'w' || dst_qt == 'l'))
        conv = (dst_qt == 'l') ? "dtosl" : "dtosi";
    else if (src_qt == 's' && (dst_qt == 'w' || dst_qt == 'l'))
        conv = (dst_qt == 'l') ? "stosl" : "stosi";
    else if ((src_qt == 'w' || src_qt == 'l') && dst_qt == 'd')
        conv = (src_qt == 'l') ? "sltof" : "swtof";
    else if ((src_qt == 'w' || src_qt == 'l') && dst_qt == 's')
        conv = (src_qt == 'l') ? "ultof" : "uwtof";
    else if (src_qt == 's' && dst_qt == 'd') conv = "exts";
    else if (src_qt == 'd' && dst_qt == 's') conv = "truncd";
    if (!conv) return arg;
    IRVal result = ir_new_tmp(cg->ir, dst_qt);
    ir_emit(cg->ir, "    %%t%d =%c %s %%t%d\n",
            result.id, dst_qt, conv, arg.id);
    return result;
}

static IRVal cg_expr(CGContext *cg, Node *n) {
    if (!n) { IRVal v = {0}; return v; }

    switch (n->kind) {
    case NODE_INT: {
        NodeInt *d = node_int_data(n);
        IRVal v = ir_new_tmp(cg->ir, qbe_type_of(n->type));
        ir_emit_copy(cg->ir, v, d->value);
        return v;
    }
    case NODE_BOOL: {
        NodeBool *d = node_bool_data(n);
        IRVal v = ir_new_tmp(cg->ir, 'w');
        ir_emit_copy(cg->ir, v, d->value ? 1 : 0);
        return v;
    }
    case NODE_FLOAT: {
        NodeFloat *d = node_float_data(n);
        double val = d->value;
        char qbe_type_char = 'd';   /* default: f64 */
        char buf[64];

        /* Check type for f32 vs f64 */
        if (n->type && n->type->kind == KIND_PRIMITIVE && n->type->prim == PRIM_F32) {
            qbe_type_char = 's';
        }

        /* Format the value for QBE. QBE uses d_ prefix for double, s_ for single.
           Handle special IEEE 754 values. */
        if (val != val) {  /* NaN */
            snprintf(buf, sizeof(buf), "%c_nan", qbe_type_char);
        } else if (val > 0 && val / val != 1) {  /* +Inf */
            /* isinf check: val > DBL_MAX */
            snprintf(buf, sizeof(buf), "%c_+inf", qbe_type_char);
        } else if (val < 0 && val / val != 1) {  /* -Inf */
            snprintf(buf, sizeof(buf), "%c_-inf", qbe_type_char);
        } else {
            /* Normal float: use %.17g for full precision round-tripping */
            snprintf(buf, sizeof(buf), "%c_%.17g", qbe_type_char, val);
        }

        IRVal v = ir_new_tmp(cg->ir, qbe_type_char);
        ir_emit(cg->ir, "    %%t%d =%c copy %s\n", v.id, qbe_type_char, buf);
        return v;
    }
    case NODE_STRING: {
        NodeString *d = node_string_data(n);
        /* Create a null-terminated string data definition, return its address */
        IRVal str_val = ir_new_data_str(cg->ir, d->chars, d->len);
        /* Copy data label to an SSA temp for use in expressions */
        IRVal v = ir_new_tmp(cg->ir, 'l');
        ir_emit(cg->ir, "    %%t%d =l copy %s\n", v.id, str_val.name);
        return v;
    }
    case NODE_CHAR: {
        NodeChar *d = node_char_data(n);
        IRVal v = ir_new_tmp(cg->ir, 'w');
        ir_emit_copy(cg->ir, v, (unsigned char)d->ch);
        return v;
    }
    case NODE_IDENT: {
        NodeIdent *d = node_ident_data(n);
        /* v0.7 7B: const array reference — emit `copy $name` (QBE uses
           $name as a DYNCONST value directly, no separate addr inst). */
        if (d->sym && d->sym->kind == SYM_CONST) {
            IRVal v = ir_new_tmp(cg->ir, 'l');
            ir_emit(cg->ir, "    %%t%d =l copy $%s\n", v.id, d->sym->name);
            return v;
        }
        int is_stack = 0;
        IRVal loc = cg_find_local(cg, d->sym, &is_stack);
        if (is_stack) {
            /* structs/arrays/slices are always manipulated via address */
            if (n->type && (n->type->kind == KIND_STRUCT ||
                            n->type->kind == KIND_ARRAY ||
                            n->type->kind == KIND_SLICE)) {
                return loc;
            }
            /* load from stack */
            IRVal v = ir_new_tmp(cg->ir, qbe_type_of(n->type));
            cg_emit_load(cg, v, n->type, loc);
            return v;
        }
        return loc; /* SSA value */
    }
    case NODE_UNARY: {
        NodeUnary *d = node_unary_data(n);
        IRVal inner = cg_expr(cg, d->expr);
        switch (d->op) {
        case TOKEN_MINUS: {
            IRVal result = ir_new_tmp(cg->ir, inner.qbe_type);
            IRVal zero = ir_new_tmp(cg->ir, inner.qbe_type);
            ir_emit_copy(cg->ir, zero, 0);
            ir_emit_binary(cg->ir, result, "sub", zero, inner);
            return result;
        }
        case TOKEN_BANG: {
            /* !expr → logical NOT: result = ceqw(expr, 0) */
            IRVal result = ir_new_tmp(cg->ir, 'w');
            IRVal zero = ir_new_tmp(cg->ir, inner.qbe_type ? inner.qbe_type : 'w');
            ir_emit_copy(cg->ir, zero, 0);
            ir_emit_binary(cg->ir, result, "ceqw", inner, zero);
            return result;
        }
        case TOKEN_TILDE: {
            /* ~expr → bitwise NOT: result = xor(expr, -1) */
            IRVal result = ir_new_tmp(cg->ir, inner.qbe_type);
            IRVal neg_one = ir_new_tmp(cg->ir, inner.qbe_type);
            ir_emit_copy(cg->ir, neg_one, -1);
            ir_emit_binary(cg->ir, result, "xor", inner, neg_one);
            return result;
        }
        default:
            return inner;
        }
    }
    case NODE_BINARY: {
        NodeBinary *d = node_binary_data(n);
        IRVal left = cg_expr(cg, d->left);

        /* short-circuit && and || */
        if (d->op == TOKEN_AMPAMP || d->op == TOKEN_PIPEPIPE) {
            IRVal result = ir_new_tmp(cg->ir, 'w');
            IRVal eval_b = ir_new_block(cg->ir, "sc_eval");
            IRVal merge  = ir_new_block(cg->ir, "sc_merge");

            if (d->op == TOKEN_AMPAMP) {
                /* a && b: jnz a, @eval_b, @false(0) */
                IRVal false_block = ir_new_block(cg->ir, "sc_false");
                ir_emit_jnz(cg->ir, left, eval_b, false_block);

                ir_emit_label(cg->ir, false_block);
                IRVal zero = ir_new_tmp(cg->ir, 'w');
                ir_emit_copy(cg->ir, zero, 0);
                ir_emit_jmp(cg->ir, merge);

                ir_emit_label(cg->ir, eval_b);
                IRVal right_and = cg_expr(cg, d->right);
                IRVal rb_and = ir_new_tmp(cg->ir, 'w');
                ir_emit_binary(cg->ir, rb_and, "cnew", right_and, ir_new_int(0));
                ir_emit_jmp(cg->ir, merge);

                ir_emit_label(cg->ir, merge);
                ir_emit_phi(cg->ir, result, 2, false_block, zero, eval_b, rb_and);
            } else {
                /* a || b: jnz a, @true(1), @eval_b */
                IRVal true_block = ir_new_block(cg->ir, "sc_true");
                ir_emit_jnz(cg->ir, left, true_block, eval_b);

                ir_emit_label(cg->ir, true_block);
                IRVal one = ir_new_tmp(cg->ir, 'w');
                ir_emit_copy(cg->ir, one, 1);
                ir_emit_jmp(cg->ir, merge);

                ir_emit_label(cg->ir, eval_b);
                IRVal right_or = cg_expr(cg, d->right);
                IRVal rb_or = ir_new_tmp(cg->ir, 'w');
                ir_emit_binary(cg->ir, rb_or, "cnew", right_or, ir_new_int(0));
                ir_emit_jmp(cg->ir, merge);

                ir_emit_label(cg->ir, merge);
                ir_emit_phi(cg->ir, result, 2, true_block, one, eval_b, rb_or);
            }
            return result;
        }

        /* non-short-circuit: evaluate right eagerly */
        IRVal right = cg_expr(cg, d->right);
        IRVal result = ir_new_tmp(cg->ir, qbe_type_of(n->type));

        /* determine operand width and signedness for comparisons */
        Type *op_type = d->left->type;
        char op_qt = op_type ? qbe_type_of(op_type) : 'w';
        int is_unsigned = 0;
        if (op_type && op_type->kind == KIND_PRIMITIVE) {
            switch (op_type->prim) {
            case PRIM_U8: case PRIM_U16: case PRIM_U32: case PRIM_U64:
                is_unsigned = 1; break;
            default: break;
            }
        }

        const char *op = NULL;
        switch (d->op) {
        case TOKEN_PLUS:  op = "add"; break;
        case TOKEN_MINUS: op = "sub"; break;
        case TOKEN_STAR:  op = "mul"; break;
        case TOKEN_SLASH: op = "div"; break;
        case TOKEN_PERCENT: op = "rem"; break;

        /* comparisons: type-dependent width + signedness */
        case TOKEN_EQEQ:
            if (op_qt == 'l') op = "ceql";
            else if (op_qt == 'd') op = "ceqd";  /* v1.0.0 fix #9: f64 ceqw → ceqd */
            else if (op_qt == 's') op = "ceqs";  /* f32 ceqw → ceqs */
            else op = "ceqw";
            break;
        case TOKEN_BANGEQ:
            if (op_qt == 'l') op = "cnel";
            else if (op_qt == 'd') op = "cned";
            else if (op_qt == 's') op = "cnes";
            else op = "cnew";
            break;
        /* float compares have no signed/unsigned (cltd/cled/cgtd/cged, clts/cles/cgts/cges) */
        case TOKEN_LT:
            if (op_qt == 'l') op = is_unsigned ? "cultl" : "csltl";
            else if (op_qt == 'd') op = "cltd";
            else if (op_qt == 's') op = "clts";
            else op = is_unsigned ? "cultw" : "csltw";
            break;
        case TOKEN_LTEQ:
            if (op_qt == 'l') op = is_unsigned ? "culel" : "cslel";
            else if (op_qt == 'd') op = "cled";
            else if (op_qt == 's') op = "cles";
            else op = is_unsigned ? "culew" : "cslew";
            break;
        case TOKEN_GT:
            if (op_qt == 'l') op = is_unsigned ? "cugtl" : "csgtl";
            else if (op_qt == 'd') op = "cgtd";
            else if (op_qt == 's') op = "cgts";
            else op = is_unsigned ? "cugtw" : "csgtw";
            break;
        case TOKEN_GTEQ:
            if (op_qt == 'l') op = is_unsigned ? "cugel" : "csgel";
            else if (op_qt == 'd') op = "cged";
            else if (op_qt == 's') op = "cges";
            else op = is_unsigned ? "cugew" : "csgew";
            break;

        case TOKEN_AMP:    op = "and"; break;
        case TOKEN_PIPE:   op = "or"; break;
        case TOKEN_CARET:  op = "xor"; break;
        case TOKEN_LTLT:   op = "shl"; break;
        case TOKEN_GTGT:   op = "shr"; break;
        default: op = "add"; break;
        }
        /* v1.0.0 fix #9: coerce right to left's qbe_type for float compares
           (e.g. f32 variable > 1.0f64 literal needs exts/truncd first). */
        if (d->op >= TOKEN_EQEQ && d->op <= TOKEN_GTEQ && left.qbe_type != right.qbe_type) {
            right = cg_convert_arg(cg, right, d->right->type, d->left->type);
        }
        ir_emit_binary(cg->ir, result, op, left, right);
        return result;
    }
    case NODE_CALL: {
        NodeCall *d = node_call_data(n);
        /* Use mangled name if the function sym has a module owner.
           The parser keeps sym->name unchanged; mangling happens here so
           that two modules can both define a function with the same name.
           Extern FFI declarations are NOT mangled. */
        Sym *fn_sym = (d->callee->kind == NODE_IDENT) ? node_ident_data(d->callee)->sym : NULL;
        char mangled[512];
        const char *fn_name;
        if (fn_sym && fn_sym->is_extern) {
            fn_name = fn_sym->name;  /* extern: pass-through name to linker */
        } else if (fn_sym && fn_sym->module) {
            snprintf(mangled, sizeof(mangled), "%s__%s", fn_sym->module, fn_sym->name);
            fn_name = mangled;
        } else {
            fn_name = fn_sym ? fn_sym->name : "?";
        }

        int is_sret = (n->type && n->type->kind == KIND_STRUCT);
        IRVal ret_slot;
        if (is_sret) {
            int rsize = (int)type_size(n->type);
            if (rsize < 4) rsize = 4;
            ret_slot = ir_new_tmp(cg->ir, 'l');
            ir_emit_alloc(cg->ir, ret_slot, rsize);
        }

        /* Evaluate args, copying structs to stack slots */
        int extra = is_sret ? 1 : 0;
        IRVal *args = NULL;
        if (d->nargs + extra > 0)
            args = arena_alloc(cg->ir->arena, (d->nargs + extra) * sizeof(IRVal));
        /* sret: hidden return slot pointer is first argument */
        if (is_sret) args[0] = ret_slot;
        /* parameter types (for v1.0.0: implicit f64→f32 conversion at call site) */
        Type **param_ts = (fn_sym && fn_sym->type && fn_sym->type->kind == KIND_FUNC)
                         ? fn_sym->type->func.params : NULL;
        size_t nparams = (fn_sym && fn_sym->type && fn_sym->type->kind == KIND_FUNC)
                         ? fn_sym->type->func.nparams : 0;
        for (size_t i = 0; i < d->nargs; i++) {
            IRVal arg = cg_expr(cg, d->args[i]);
            Type *at = d->args[i]->type;
            if (at && at->kind == KIND_STRUCT) {
                /* copy struct to a new stack slot for pass-by-value */
                int asize = (int)type_size(at);
                if (asize < 4) asize = 4;
                IRVal copy_slot = ir_new_tmp(cg->ir, 'l');
                ir_emit_alloc(cg->ir, copy_slot, asize);
                cg_copy_struct(cg, at, copy_slot, arg);
                args[extra + i] = copy_slot;
            } else {
                /* implicit conversion (e.g. f64 literal → f32 param via truncd) */
                if (param_ts && i < nparams && param_ts[i]) {
                    arg = cg_convert_arg(cg, arg, at, param_ts[i]);
                }
                args[extra + i] = arg;
            }
        }

        if (is_sret) {
            ir_emit_call_void(cg->ir, fn_name, args, (int)d->nargs + 1);
            return ret_slot;
        }
        char qt = n->type ? qbe_type_of(n->type) : 'w';
        IRVal result = ir_new_tmp(cg->ir, qt);
        ir_emit_call(cg->ir, result, fn_name, args, (int)d->nargs);
        return result;
    }
    case NODE_QUALIFIED_CALL: {
        NodeQualifiedCall *d = node_qualified_call_data(n);
        /* d->resolved was set by sema */
        Sym *fn_sym = d->resolved;
        char mangled[512];
        const char *fn_name;
        if (fn_sym && fn_sym->module) {
            snprintf(mangled, sizeof(mangled), "%s__%s", fn_sym->module, fn_sym->name);
            fn_name = mangled;
        } else {
            fn_name = fn_sym ? fn_sym->name : "?";
        }

        int is_sret = (n->type && n->type->kind == KIND_STRUCT);
        IRVal ret_slot;
        if (is_sret) {
            int rsize = (int)type_size(n->type);
            if (rsize < 4) rsize = 4;
            ret_slot = ir_new_tmp(cg->ir, 'l');
            ir_emit_alloc(cg->ir, ret_slot, rsize);
        }

        int extra = is_sret ? 1 : 0;
        IRVal *args = NULL;
        if (d->nargs + extra > 0)
            args = arena_alloc(cg->ir->arena, (d->nargs + extra) * sizeof(IRVal));
        if (is_sret) args[0] = ret_slot;
        /* parameter types (for v1.0.0: implicit f64→f32 conversion at call site) */
        Type **param_ts = (fn_sym && fn_sym->type && fn_sym->type->kind == KIND_FUNC)
                         ? fn_sym->type->func.params : NULL;
        size_t nparams = (fn_sym && fn_sym->type && fn_sym->type->kind == KIND_FUNC)
                         ? fn_sym->type->func.nparams : 0;
        for (size_t i = 0; i < d->nargs; i++) {
            IRVal arg = cg_expr(cg, d->args[i]);
            Type *at = d->args[i]->type;
            if (at && at->kind == KIND_STRUCT) {
                int asize = (int)type_size(at);
                if (asize < 4) asize = 4;
                IRVal copy_slot = ir_new_tmp(cg->ir, 'l');
                ir_emit_alloc(cg->ir, copy_slot, asize);
                cg_copy_struct(cg, at, copy_slot, arg);
                args[extra + i] = copy_slot;
            } else {
                /* implicit conversion (e.g. f64 literal → f32 param via truncd) */
                if (param_ts && i < nparams && param_ts[i]) {
                    arg = cg_convert_arg(cg, arg, at, param_ts[i]);
                }
                args[extra + i] = arg;
            }
        }

        if (is_sret) {
            ir_emit_call_void(cg->ir, fn_name, args, (int)d->nargs + 1);
            return ret_slot;
        }
        char qt = n->type ? qbe_type_of(n->type) : 'w';
        IRVal result = ir_new_tmp(cg->ir, qt);
        ir_emit_call(cg->ir, result, fn_name, args, (int)d->nargs);
        return result;
    }
    case NODE_IF: {
        NodeIf *d = node_if_data(n);
        IRVal cond = cg_expr(cg, d->cond);

        IRVal then_block = ir_new_block(cg->ir, "then");
        IRVal else_block = ir_new_block(cg->ir, "else");
        IRVal merge_block = ir_new_block(cg->ir, "merge");

        ir_emit_jnz(cg->ir, cond, then_block, else_block);

        /* helper to detect if a body ends with a terminator (return/break/continue) */
        #define body_terminates(body) \
            ((body) && ((body)->kind == NODE_RETURN || \
                        (body)->kind == NODE_BREAK || \
                        (body)->kind == NODE_CONTINUE || \
             ((body)->kind == NODE_BLOCK && node_block_data(body)->nstmts > 0 && \
              (node_block_data(body)->stmts[node_block_data(body)->nstmts - 1]->kind == NODE_RETURN || \
               node_block_data(body)->stmts[node_block_data(body)->nstmts - 1]->kind == NODE_BREAK || \
               node_block_data(body)->stmts[node_block_data(body)->nstmts - 1]->kind == NODE_CONTINUE))))

        /* then */
        ir_emit_label(cg->ir, then_block);
        IRVal then_val = cg_expr(cg, d->then_body);
        int then_returns = body_terminates(d->then_body);
        if (!then_returns) ir_emit_jmp(cg->ir, merge_block);

        /* Pre-allocate trampoline block for nested-if else_body (else if chain).
           Created BEFORE the recursive cg_expr so the inner if's merge block
           can reach it via jmp ep; label ep; jmp outer_merge. */
        int nested_else_if = d->else_body && d->else_body->kind == NODE_IF;
        IRVal nested_phi_block;
        if (nested_else_if) {
            nested_phi_block = ir_new_block(cg->ir, "ep");
        }

        /* else */
        ir_emit_label(cg->ir, else_block);
        if (d->else_body) {
            IRVal else_val = cg_expr(cg, d->else_body);
            int else_returns = body_terminates(d->else_body);
            IRVal else_phi_block = else_block;  /* default: use else_block as phi predecessor */
            if (nested_else_if) {
                /* Inner if's branches converge at inner_merge, then fall through
                   into the trampoline. Use the pre-allocated ep as predecessor. */
                else_phi_block = nested_phi_block;
                ir_emit_jmp(cg->ir, else_phi_block);
                ir_emit_label(cg->ir, else_phi_block);
                ir_emit_jmp(cg->ir, merge_block);
            } else if (!else_returns) {
                /* Use a trampoline block so phi always references a direct predecessor
                   instead of else_block (which may contain non-terminator fallthrough). */
                else_phi_block = ir_new_block(cg->ir, "ep");
                ir_emit_jmp(cg->ir, else_phi_block);
                ir_emit_label(cg->ir, else_phi_block);
                ir_emit_jmp(cg->ir, merge_block);
            }
            /* phi */
            ir_emit_label(cg->ir, merge_block);
            /* Sprint 5A.3: skip phi emission entirely when if expr is void */
            if (n->type && n->type->kind == KIND_VOID) {
                #undef body_terminates
                IRVal v = {0};
                return v;
            }
            if (!then_returns && !else_returns) {
                IRVal result = ir_new_tmp(cg->ir, then_val.qbe_type);
                ir_emit_phi(cg->ir, result, 2, then_block, then_val, else_phi_block, else_val);
                return result;
            }
        } else {
            ir_emit_jmp(cg->ir, merge_block);
            ir_emit_label(cg->ir, merge_block);
        }
        #undef body_terminates

        if (n->type && n->type->kind == KIND_VOID) {
            IRVal v = {0};
            return v;
        }
        return then_val; /* fallback */
    }
    case NODE_BLOCK: {
        NodeBlock *d = node_block_data(n);
        IRVal last = {0};
        for (size_t i = 0; i < d->nstmts; i++) {
            Node *stmt = d->stmts[i];
            if (stmt->kind == NODE_RETURN || stmt->kind == NODE_BREAK || stmt->kind == NODE_CONTINUE) {
                cg_stmt(cg, stmt);
                return last;
            }
            if (stmt->kind == NODE_EXPR_STMT) {
                NodeExprStmt *es = node_expr_stmt_data(stmt);
                if (es->expr->kind == NODE_ASSIGN) {
                    cg_stmt(cg, es->expr);
                } else {
                    /* capture value as potential block return value */
                    last = cg_expr(cg, es->expr);
                }
            } else if (stmt->kind == NODE_IF || stmt->kind == NODE_MATCH || stmt->kind == NODE_BLOCK) {
                /* These expression-statement forms may also yield a value
                   (e.g., `if x { 0 } else { 1 }` as a block's last statement
                   is the block's return value). */
                last = cg_expr(cg, stmt);
            } else {
                cg_stmt(cg, stmt);
            }
        }
        return last;
    }
    case NODE_RETURN: {
        NodeReturn *d = node_return_data(n);
        if (d->expr) {
            IRVal val = cg_expr(cg, d->expr);
            ir_emit_ret(cg->ir, val);
        } else {
            IRVal v = {0};
            ir_emit_ret(cg->ir, v);
        }
        IRVal v = {0};
        return v;
    }
    case NODE_EXPR_STMT: {
        NodeExprStmt *d = node_expr_stmt_data(n);
        return cg_expr(cg, d->expr);
    }

    /* ── cast: expr as Type ── */
    case NODE_CAST: {
        NodeCast *d = node_cast_data(n);
        Type *src_t = d->expr->type;
        Type *dst_t = n->type;
        IRVal inner = cg_expr(cg, d->expr);
        if (!src_t || !dst_t) {
            return inner;
        }
        /* array -> slice: build 16-byte slice struct {ptr, len} */
        if (src_t->kind == KIND_ARRAY && dst_t->kind == KIND_SLICE) {
            IRVal arr_base = inner; /* already a stack slot address (l) */
            int nitems = (int)src_t->array.count;
            IRVal slot = ir_new_tmp(cg->ir, 'l');
            ir_emit_alloc(cg->ir, slot, 16);
            /* field 0: ptr = arr_base */
            ir_emit(cg->ir, "    storel %%t%d, %%t%d\n", arr_base.id, slot.id);
            /* field 8: len = nitems */
            IRVal off8 = ir_new_tmp(cg->ir, 'l');
            ir_emit(cg->ir, "    %%t%d =l add %%t%d, 8\n", off8.id, slot.id);
            IRVal len_v = ir_new_tmp(cg->ir, 'l');
            ir_emit_copy(cg->ir, len_v, (int64_t)nitems);
            ir_emit(cg->ir, "    storel %%t%d, %%t%d\n", len_v.id, off8.id);
            return slot;
        }
        char src_qt = qbe_type_of(src_t);
        char dst_qt = qbe_type_of(dst_t);
        if (src_qt == dst_qt && src_t->kind == dst_t->kind && src_t->prim == dst_t->prim) {
            /* no-op */
            return inner;
        }
        /* sub-word -> word: already word after loadub/loadsb/loaduh/loadsh */
        if ((src_qt == 'b' || src_qt == 'h') && (dst_qt == 'w' || dst_qt == 'l')) {
            IRVal result = ir_new_tmp(cg->ir, dst_qt);
            ir_emit(cg->ir, "    %%t%d =%c copy %%t%d\n", result.id, dst_qt, inner.id);
            return result;
        }
        IRVal result = ir_new_tmp(cg->ir, dst_qt);
        /* pick a QBE conversion instruction */
        const char *conv = NULL;
        if (src_qt == 'd' && (dst_qt == 'w' || dst_qt == 'l'))
            conv = (dst_qt == 'l') ? "dtosl" : "dtosi";
        else if (src_qt == 's' && (dst_qt == 'w' || dst_qt == 'l'))
            conv = (dst_qt == 'l') ? "stosl" : "stosi";
        else if ((src_qt == 'w' || src_qt == 'l') && dst_qt == 'd')
            conv = (src_qt == 'l') ? "sltof" : "swtof";
        else if ((src_qt == 'w' || src_qt == 'l') && dst_qt == 's')
            conv = (src_qt == 'l') ? "ultof" : "uwtof";
        else if (src_qt == 's' && dst_qt == 'd')
            conv = "exts";
        else if (src_qt == 'd' && dst_qt == 's')
            conv = "truncd";
        else if ((src_qt == 'w' || src_qt == 'l') && (dst_qt == 'w' || dst_qt == 'l')) {
            /* integer width change */
            if (dst_qt == 'l') {
                if (src_qt == 'w') {
                    ir_emit(cg->ir, "    %%t%d =l extsw %%t%d\n", result.id, inner.id);
                } else {
                    ir_emit(cg->ir, "    %%t%d =l copy %%t%d\n", result.id, inner.id);
                }
            } else {
                /* narrowing l->w: QBE 'copy' from a long truncates implicitly */
                ir_emit(cg->ir, "    %%t%d =w copy %%t%d\n", result.id, inner.id);
            }
            return result;
        }
        if (!conv) {
            IRVal v = {0};
            return v;
        }
        ir_emit(cg->ir, "    %%t%d =%c %s %%t%d\n",
                result.id, dst_qt, conv, inner.id);
        return result;
    }

    /* ── address-of: &variable ── */
    case NODE_ADDR_OF: {
        NodeAddrOf *d = node_addr_of_data(n);
        /* target must be a local variable with a stack slot */
        if (d->expr->kind == NODE_IDENT) {
            NodeIdent *id = node_ident_data(d->expr);
            int is_stack = 0;
            IRVal val = cg_find_local(cg, id->sym, &is_stack);
            if (is_stack) {
                IRVal result = ir_new_tmp(cg->ir, 'l');
                ir_emit_copy(cg->ir, result, 0);
                /* return the stack slot address */
                return val;
            }
            /* SSA temp: spill to a new stack slot, update local entry, return slot */
            int size = (int)type_size(id->sym->type);
            if (size < 4) size = 4;
            IRVal slot = ir_new_tmp(cg->ir, 'l');
            ir_emit_alloc(cg->ir, slot, size);
            cg_emit_store(cg, id->sym->type, val, slot);
            cg_add_local(cg, id->sym, slot, 1);
            return slot;
        }
        /* fallback: evaluate as expression (won't work for SSA temps) */
        IRVal v = cg_expr(cg, d->expr);
        return v;
    }

    /* ── dereference: *ptr ── */
    case NODE_DEREF: {
        NodeDeref *d = node_deref_data(n);
        IRVal ptr = cg_expr(cg, d->expr);
        /* Pointer-to-struct: return the pointer itself (struct manipulated by address) */
        if (n->type && n->type->kind == KIND_STRUCT) {
            return ptr;
        }
        char qt = n->type ? qbe_type_of(n->type) : 'w';
        IRVal result = ir_new_tmp(cg->ir, qt);
        cg_emit_load(cg, result, n->type, ptr);
        return result;
    }

    /* ── struct literal: TypeName { field: val, ... } ── */
    case NODE_STRUCT_LIT: {
        NodeStructLit *d = node_struct_lit_data(n);
        Type *st = n->type;
        if (!st || st->kind != KIND_STRUCT) {
            IRVal v = {0}; return v;
        }
        int size = (int)type_size(st);
        if (size < 4) size = 4;
        IRVal slot = ir_new_tmp(cg->ir, 'l');
        ir_emit_alloc(cg->ir, slot, size);

        for (size_t i = 0; i < d->nfields; i++) {
            IRVal fval = cg_expr(cg, d->fields[i].value);
            /* find field offset */
            size_t offset = 0;
            for (size_t j = 0; j < st->struct_type.nfields; j++) {
                if (strcmp(st->struct_type.fields[j].name->name, d->fields[i].name) == 0) {
                    offset = st->struct_type.fields[j].offset;
                    break;
                }
            }
            /* compute address = slot + offset */
            IRVal addr = ir_new_tmp(cg->ir, 'l');
            ir_emit_binary(cg->ir, addr, "add", slot, ir_new_int((int64_t)offset));
            cg_emit_store(cg, d->fields[i].value->type, fval, addr);
        }
        return slot;
    }

    /* ── enum variant construction: TypeName::Variant(args) ── */
    case NODE_ENUM_VARIANT: {
        NodeEnumVariant *d = node_enum_variant_data(n);
        Type *et = n->type;
        if (!et || et->kind != KIND_ENUM) {
            IRVal v = {0}; return v;
        }
        int size = (int)type_size(et);
        if (size < 4) size = 4;
        IRVal slot = ir_new_tmp(cg->ir, 'l');
        ir_emit_alloc(cg->ir, slot, size);

        /* find the variant's tag */
        int tag = -1;
        Type *payload_type = NULL;
        for (size_t i = 0; i < et->enum_type.nvariants; i++) {
            if (strcmp(et->enum_type.variants[i].name->name, d->variant_sym->name) == 0) {
                tag = et->enum_type.variants[i].tag;
                payload_type = et->enum_type.variants[i].payload;
                break;
            }
        }

        /* store tag at offset 0 */
        IRVal tag_addr = ir_new_tmp(cg->ir, 'l');
        ir_emit_binary(cg->ir, tag_addr, "add", slot, ir_new_int(0));
        IRVal tag_val = ir_new_tmp(cg->ir, 'w');
        ir_emit_copy(cg->ir, tag_val, tag >= 0 ? tag : 0);
        ir_emit_store(cg->ir, 'w', tag_val, tag_addr);

        /* store payload if present */
        if (d->payload && payload_type) {
            size_t payload_offset = et->enum_type.payload_offset;
            IRVal payload_addr = ir_new_tmp(cg->ir, 'l');
            ir_emit_binary(cg->ir, payload_addr, "add", slot, ir_new_int((int64_t)payload_offset));
            IRVal pval = cg_expr(cg, d->payload);
            cg_emit_store(cg, payload_type, pval, payload_addr);
        }
        return slot;
    }

    /* ── match expression ── */
    case NODE_MATCH: {
        NodeMatch *d = node_match_data(n);
        IRVal matched = cg_expr(cg, d->expr);

        char qt = (n->type && n->type->kind != KIND_VOID) ? qbe_type_of(n->type) : 0;
        IRVal merge_block = ir_new_block(cg->ir, "merge");

        /* collect body blocks and values for phi */
        #define MAX_MATCH_ARMS 32
        IRVal body_blocks[MAX_MATCH_ARMS];
        IRVal body_values[MAX_MATCH_ARMS];
        int nphi = 0;

        /* emit chain of comparisons */
        IRVal next_check = {0};
        for (size_t i = 0; i < d->narms; i++) {
            NodeMatchArm *arm = node_match_arm_data(d->arms[i]);
            IRVal body_block = ir_new_block(cg->ir, "arm");

            if (arm->pattern->kind == NODE_PATTERN_WILD) {
                /* wildcard: always match, jump to body */
                if (next_check.id != 0) {
                    ir_emit_label(cg->ir, next_check);
                    next_check.id = 0;  /* consumed */
                }
                ir_emit_jmp(cg->ir, body_block);
            } else {
                /* literal/range pattern: emit comparison */
                if (next_check.id != 0) {
                    ir_emit_label(cg->ir, next_check);
                    next_check.id = 0;  /* consumed */
                }
                next_check = ir_new_block(cg->ir, "next");
                IRVal cmp = cg_match_pattern(cg, matched, arm->pattern);
                ir_emit_jnz(cg->ir, cmp, body_block, next_check);
            }

            /* body */
            ir_emit_label(cg->ir, body_block);
            IRVal body_val = cg_expr(cg, arm->body);
            int arm_returns = ((arm->body && arm->body->kind == NODE_RETURN) ||
                               (arm->body && arm->body->kind == NODE_BLOCK &&
                                node_block_data(arm->body)->nstmts > 0 &&
                                node_block_data(arm->body)->stmts[node_block_data(arm->body)->nstmts - 1]->kind == NODE_RETURN));
            if (!arm_returns && nphi < MAX_MATCH_ARMS) {
                body_blocks[nphi] = body_block;
                body_values[nphi] = body_val;
                nphi++;
                ir_emit_jmp(cg->ir, merge_block);
            }
        }

        /* if there's a dangling next_check, emit its label. This is the
           fallthrough after the last comparison arm — should be unreachable
           if the match is exhaustive (sema 7A verifies enum coverage).
           Without this label, QBE fails with "block @nextX is used
           undefined" when no arm is a wildcard. */
        if (next_check.id != 0) {
            ir_emit_label(cg->ir, next_check);
            if (nphi > 0) {
                /* unreachable: provide a dummy value of the right type
                   for the phi. ir_new_tmp guarantees a unique SSA name. */
                IRVal undef = ir_new_tmp(cg->ir, qt ? qt : 'w');
                ir_emit_copy(cg->ir, undef, 0);
                body_blocks[nphi] = next_check;
                body_values[nphi] = undef;
                nphi++;
                ir_emit_jmp(cg->ir, merge_block);
            }
            /* if nphi == 0 (void match), no merge needed; just leave the
               block dangling — QBE tolerates an unreferenced label. */
        }

        /* merge with phi */
        ir_emit_label(cg->ir, merge_block);
        if (qt && nphi > 0) {
            IRVal result = ir_new_tmp(cg->ir, qt);
            /* build phi with collected blocks and values */
            ir_emit(cg->ir, "    %%t%d =%c phi ", result.id, qt);
            for (int i = 0; i < nphi; i++) {
                if (i > 0) ir_emit(cg->ir, ", ");
                ir_emit(cg->ir, "@%s %%t%d", body_blocks[i].name, body_values[i].id);
            }
            ir_emit(cg->ir, "\n");
            return result;
        }
        #undef MAX_MATCH_ARMS
        IRVal v = {0};
        return v;
    }

    /* ── array index: arr[i] ── */
    case NODE_INDEX: {
        NodeIndex *d = node_index_data(n);
        Type *arr_type = d->expr->type;
        if (!arr_type || (arr_type->kind != KIND_ARRAY && arr_type->kind != KIND_POINTER && arr_type->kind != KIND_SLICE)) {
            IRVal v = {0}; return v;
        }
        int is_array = (arr_type->kind == KIND_ARRAY);
        int is_slice = (arr_type->kind == KIND_SLICE);
        Type *elem_type = is_array ? arr_type->array.elem
                          : is_slice ? arr_type->slice.elem
                          : arr_type->pointer.elem;
        size_t elem_size = type_size(elem_type);
        char elem_qt = qbe_type_of(elem_type);

        /* get array base address.
           For array-typed identifiers, get the stack slot directly (don't load).
           For SYM_CONST identifiers, use cg_expr to emit `addr $name` (v0.7 7B).
           For slice, cg_expr returns the slot address; load ptr from offset 0. */
        IRVal base;
        if (is_array && d->expr->kind == NODE_IDENT) {
            NodeIdent *id = node_ident_data(d->expr);
            if (id->sym && id->sym->kind == SYM_CONST) {
                base = cg_expr(cg, d->expr);  /* emits `addr $name` */
            } else {
                int is_stack = 0;
                base = cg_find_local(cg, id->sym, &is_stack);
            }
        } else if (is_slice) {
            IRVal slice_addr = cg_expr(cg, d->expr);
            base = ir_new_tmp(cg->ir, 'l');
            ir_emit(cg->ir, "    %%t%d =l loadl %%t%d\n", base.id, slice_addr.id);
        } else {
            base = cg_expr(cg, d->expr);
        }
        /* compute index */
        IRVal idx = cg_expr(cg, d->index);

        /* offset = index * elem_size */
        IRVal offset = ir_new_tmp(cg->ir, 'l');
        if (d->index->kind == NODE_INT) {
            /* constant index: fold at compile time */
            int64_t const_off = node_int_data(d->index)->value * (int64_t)elem_size;
            ir_emit_copy(cg->ir, offset, const_off);
        } else {
            /* convert index to 64-bit for pointer arithmetic */
            IRVal idx64 = ir_new_tmp(cg->ir, 'l');
            if (idx.qbe_type == 'l') {
                idx64 = idx;
            } else {
                ir_emit(cg->ir, "    %%t%d =l extsw %%t%d\n", idx64.id, idx.id);
            }
            IRVal elem_size_val = ir_new_tmp(cg->ir, 'l');
            ir_emit_copy(cg->ir, elem_size_val, (int64_t)elem_size);
            ir_emit_binary(cg->ir, offset, "mul", idx64, elem_size_val);
        }

        /* address = base + offset */
        IRVal addr = ir_new_tmp(cg->ir, 'l');
        ir_emit_binary(cg->ir, addr, "add", base, offset);

        /* Struct element: return the address (struct is manipulated by address,
           matches NODE_DEREF behavior). Caller applies field offset / load. */
        if (elem_type && elem_type->kind == KIND_STRUCT) {
            return addr;
        }

        /* load from computed address.
           For sub-word types (i8/u8/i16/u16/bool) the load returns a word;
           the result temp must be 'w' to match. */
        char result_qt = (elem_type && elem_type->kind == KIND_PRIMITIVE &&
                          (elem_type->prim == PRIM_I8 || elem_type->prim == PRIM_U8 ||
                           elem_type->prim == PRIM_BOOL || elem_type->prim == PRIM_I16 ||
                           elem_type->prim == PRIM_U16))
                         ? 'w' : elem_qt;
        IRVal result = ir_new_tmp(cg->ir, result_qt);
        cg_emit_load(cg, result, elem_type, addr);
        return result;
    }

    /* ── array literal: [1, 2, 3] ── */
    case NODE_ARRAY_LIT: {
        NodeArrayLit *d = node_array_lit_data(n);
        Type *arr_type = n->type;
        if (!arr_type || arr_type->kind != KIND_ARRAY) {
            IRVal v = {0}; return v;
        }
        Type *elem_type = arr_type->array.elem;
        size_t elem_size = type_size(elem_type);
        size_t total_size = elem_size * d->nelems;
        if (total_size < 4) total_size = 4;

        /* allocate stack space for the array */
        IRVal slot = ir_new_tmp(cg->ir, 'l');
        ir_emit_alloc(cg->ir, slot, (int)total_size);

        /* store each element at its offset */
        for (size_t i = 0; i < d->nelems; i++) {
            IRVal elem_val = cg_expr(cg, d->elems[i]);
            if (i == 0) {
                /* offset 0: addr is just the slot */
                cg_emit_store(cg, elem_type, elem_val, slot);
            } else {
                IRVal offset = ir_new_tmp(cg->ir, 'l');
                ir_emit_copy(cg->ir, offset, (int64_t)(i * elem_size));
                IRVal addr = ir_new_tmp(cg->ir, 'l');
                ir_emit_binary(cg->ir, addr, "add", slot, offset);
                cg_emit_store(cg, elem_type, elem_val, addr);
            }
        }
        return slot;
    }

    /* ── slice literal: &[1, 2, 3] ── */
    case NODE_SLICE_LIT: {
        NodeSliceLit *d = node_slice_lit_data(n);
        /* Codegen the underlying array first; this returns its stack slot */
        IRVal arr_slot = cg_expr(cg, d->array);
        /* Build 16-byte slice struct {arr_slot, nitems} */
        NodeArrayLit *al = node_array_lit_data(d->array);
        int nitems = (int)al->nelems;
        IRVal slot = ir_new_tmp(cg->ir, 'l');
        ir_emit_alloc(cg->ir, slot, 16);
        ir_emit(cg->ir, "    storel %%t%d, %%t%d\n", arr_slot.id, slot.id);
        IRVal off8 = ir_new_tmp(cg->ir, 'l');
        ir_emit(cg->ir, "    %%t%d =l add %%t%d, 8\n", off8.id, slot.id);
        IRVal len_v = ir_new_tmp(cg->ir, 'l');
        ir_emit_copy(cg->ir, len_v, (int64_t)nitems);
        ir_emit(cg->ir, "    storel %%t%d, %%t%d\n", len_v.id, off8.id);
        return slot;
    }

    /* ── sub-range: s[a..b] ── */
    case NODE_SLICE_RANGE: {
        NodeSliceRange *d = node_slice_range_data(n);
        Type *bt = d->base->type;
        int is_slice = (bt && bt->kind == KIND_SLICE);
        Type *elem = is_slice ? bt->slice.elem : bt->array.elem;
        size_t esz = type_size(elem);
        if (esz < 4) esz = 4;

        IRVal base;
        if (is_slice) {
            IRVal slice_addr = cg_expr(cg, d->base);
            base = ir_new_tmp(cg->ir, 'l');
            ir_emit(cg->ir, "    %%t%d =l loadl %%t%d\n", base.id, slice_addr.id);
        } else {
            base = cg_expr(cg, d->base);
        }

        IRVal start_v = cg_expr(cg, d->start);
        /* start_off = start * esz */
        IRVal start_off = ir_new_tmp(cg->ir, 'l');
        if (d->start->kind == NODE_INT) {
            ir_emit_copy(cg->ir, start_off, (int64_t)node_int_data(d->start)->value * (int64_t)esz);
        } else {
            IRVal start64 = start_v;
            if (start_v.qbe_type != 'l') {
                start64 = ir_new_tmp(cg->ir, 'l');
                ir_emit(cg->ir, "    %%t%d =l extsw %%t%d\n", start64.id, start_v.id);
            }
            IRVal esz_v = ir_new_tmp(cg->ir, 'l');
            ir_emit_copy(cg->ir, esz_v, (int64_t)esz);
            ir_emit_binary(cg->ir, start_off, "mul", start64, esz_v);
        }
        IRVal new_ptr = ir_new_tmp(cg->ir, 'l');
        ir_emit_binary(cg->ir, new_ptr, "add", base, start_off);

        IRVal end_v = cg_expr(cg, d->end);
        IRVal new_len = ir_new_tmp(cg->ir, 'l');
        if (d->start->kind == NODE_INT && d->end->kind == NODE_INT) {
            ir_emit_copy(cg->ir, new_len,
                         (int64_t)node_int_data(d->end)->value - (int64_t)node_int_data(d->start)->value);
        } else {
            IRVal end64 = end_v;
            if (end_v.qbe_type != 'l') {
                end64 = ir_new_tmp(cg->ir, 'l');
                ir_emit(cg->ir, "    %%t%d =l extsw %%t%d\n", end64.id, end_v.id);
            }
            IRVal start64 = start_v;
            if (start_v.qbe_type != 'l') {
                start64 = ir_new_tmp(cg->ir, 'l');
                ir_emit(cg->ir, "    %%t%d =l extsw %%t%d\n", start64.id, start_v.id);
            }
            ir_emit_binary(cg->ir, new_len, "sub", end64, start64);
        }

        IRVal slot = ir_new_tmp(cg->ir, 'l');
        ir_emit_alloc(cg->ir, slot, 16);
        ir_emit(cg->ir, "    storel %%t%d, %%t%d\n", new_ptr.id, slot.id);
        IRVal off8 = ir_new_tmp(cg->ir, 'l');
        ir_emit(cg->ir, "    %%t%d =l add %%t%d, 8\n", off8.id, slot.id);
        ir_emit(cg->ir, "    storel %%t%d, %%t%d\n", new_len.id, off8.id);
        return slot;
    }

    /* ── field access with pointer auto-deref ── */
    case NODE_FIELD: {
        NodeField *d = node_field_data(n);
        Type *expr_type = d->expr->type;
        if (expr_type && expr_type->kind == KIND_SLICE) {
            /* synthetic .ptr / .len fields, slice value is a 16-byte stack slot */
            IRVal slot = cg_expr(cg, d->expr);
            if (strcmp(d->field, "ptr") == 0) {
                IRVal v = ir_new_tmp(cg->ir, 'l');
                ir_emit(cg->ir, "    %%t%d =l loadl %%t%d\n", v.id, slot.id);
                return v;
            }
            if (strcmp(d->field, "len") == 0) {
                IRVal off = ir_new_tmp(cg->ir, 'l');
                ir_emit(cg->ir, "    %%t%d =l add %%t%d, 8\n", off.id, slot.id);
                IRVal v = ir_new_tmp(cg->ir, 'l');
                ir_emit(cg->ir, "    %%t%d =l loadl %%t%d\n", v.id, off.id);
                return v;
            }
            IRVal v = {0};
            return v;
        }
        if (expr_type && expr_type->kind == KIND_POINTER &&
            expr_type->pointer.elem && expr_type->pointer.elem->kind == KIND_STRUCT) {
            /* pointer-to-struct: load pointer, add offset, load field */
            Type *elem = expr_type->pointer.elem;
            IRVal ptr = cg_expr(cg, d->expr);
            /* find field offset */
            size_t offset = 0;
            Type *field_type = NULL;
            for (size_t i = 0; i < elem->struct_type.nfields; i++) {
                if (strcmp(elem->struct_type.fields[i].name->name, d->field) == 0) {
                    offset = elem->struct_type.fields[i].offset;
                    field_type = elem->struct_type.fields[i].type;
                    break;
                }
            }
            IRVal addr;
            if (offset > 0) {
                addr = ir_new_tmp(cg->ir, 'l');
                ir_emit_binary(cg->ir, addr, "add", ptr, ir_new_int((int64_t)offset));
            } else {
                addr = ptr; /* offset 0: addr is just the pointer */
            }
            IRVal result = ir_new_tmp(cg->ir, field_type ? qbe_type_of(field_type) : 'w');
            cg_emit_load(cg, result, field_type, addr);
            return result;
        }
        /* For struct value field access: the value IS the stack slot pointer */
        IRVal base = cg_expr(cg, d->expr);
        Type *st = expr_type;
        if (!st || st->kind != KIND_STRUCT) {
            IRVal v = {0}; return v;
        }
        size_t offset = 0;
        Type *field_type = NULL;
        for (size_t i = 0; i < st->struct_type.nfields; i++) {
            if (strcmp(st->struct_type.fields[i].name->name, d->field) == 0) {
                offset = st->struct_type.fields[i].offset;
                field_type = st->struct_type.fields[i].type;
                break;
            }
        }
        IRVal addr;
        if (offset > 0) {
            addr = ir_new_tmp(cg->ir, 'l');
            ir_emit_binary(cg->ir, addr, "add", base, ir_new_int((int64_t)offset));
        } else {
            addr = base; /* offset 0 */
        }
        IRVal result = ir_new_tmp(cg->ir, field_type ? qbe_type_of(field_type) : 'w');
        cg_emit_load(cg, result, field_type, addr);
        return result;
    }

    default: {
        IRVal v = {0};
        return v;
    }
    }
}

static void cg_stmt(CGContext *cg, Node *n) {
    switch (n->kind) {
    case NODE_LET: {
        NodeLet *d = node_let_data(n);
        int is_array = (d->sym->type && d->sym->type->kind == KIND_ARRAY);
        int is_struct = (d->sym->type && d->sym->type->kind == KIND_STRUCT);

        if (d->is_mutable || is_array || is_struct) {
            /* For array/struct literal init, use its slot directly (no double alloc) */
            if ((is_array && d->init && d->init->kind == NODE_ARRAY_LIT) ||
                (is_struct && d->init && d->init->kind == NODE_STRUCT_LIT)) {
                IRVal init_val = cg_expr(cg, d->init);
                cg_add_local(cg, d->sym, init_val, 1);
            } else if (is_struct && d->init) {
                /* Struct from function call or other expression: alloc and copy */
                IRVal src = cg_expr(cg, d->init);
                int size = (int)type_size(d->sym->type);
                if (size < 4) size = 4;
                IRVal slot = ir_new_tmp(cg->ir, 'l');
                ir_emit_alloc(cg->ir, slot, size);
                cg_copy_struct(cg, d->sym->type, slot, src);
                cg_add_local(cg, d->sym, slot, 1);
            } else {
                IRVal init_val = cg_expr(cg, d->init);
                int size = (int)type_size(d->sym->type);
                if (size < 4) size = 4;
                IRVal slot = ir_new_tmp(cg->ir, 'l');
                ir_emit_alloc(cg->ir, slot, size);
                cg_emit_store(cg, d->sym->type, init_val, slot);
                cg_add_local(cg, d->sym, slot, 1);
            }
        } else {
            /* immutable struct: keep slot address as SSA value */
            if (is_struct && d->init) {
                IRVal init_val = cg_expr(cg, d->init);
                cg_add_local(cg, d->sym, init_val, 0);
            } else {
                IRVal init_val = cg_expr(cg, d->init);
                cg_add_local(cg, d->sym, init_val, 0);
            }
        }
        break;
    }
    case NODE_ASSIGN: {
        NodeAssign *d = node_assign_data(n);
        IRVal val = cg_expr(cg, d->value);

        if (d->target->kind == NODE_DEREF) {
            /* *ptr = value — store to pointer target */
            NodeDeref *dd = node_deref_data(d->target);
            IRVal ptr = cg_expr(cg, dd->expr);
            cg_emit_store(cg, d->target->type, val, ptr);
        } else if (d->target->kind == NODE_IDENT) {
            /* variable assignment */
            NodeIdent *id = node_ident_data(d->target);
            int is_stack = 0;
            IRVal slot = cg_find_local(cg, id->sym, &is_stack);
            if (is_stack) {
                if (d->target->type && d->target->type->kind == KIND_STRUCT) {
                    /* struct copy: val is source address */
                    cg_copy_struct(cg, d->target->type, slot, val);
                } else {
                    cg_emit_store(cg, d->target->type, val, slot);
                }
            }
        } else if (d->target->kind == NODE_INDEX) {
            /* arr[i] = value */
            NodeIndex *idx = node_index_data(d->target);
            Type *arr_type = idx->expr->type;
            if (arr_type && (arr_type->kind == KIND_ARRAY || arr_type->kind == KIND_POINTER)) {
                int is_array = (arr_type->kind == KIND_ARRAY);
                Type *elem_type = is_array ? arr_type->array.elem : arr_type->pointer.elem;
                size_t elem_size = type_size(elem_type);

                IRVal base;
                if (is_array && idx->expr->kind == NODE_IDENT) {
                    NodeIdent *id = node_ident_data(idx->expr);
                    int is_stack = 0;
                    base = cg_find_local(cg, id->sym, &is_stack);
                } else {
                    base = cg_expr(cg, idx->expr);
                }
                IRVal idx_val = cg_expr(cg, idx->index);

                /* offset = index * elem_size */
                IRVal offset = ir_new_tmp(cg->ir, 'l');
                if (idx->index->kind == NODE_INT) {
                    int64_t const_off = node_int_data(idx->index)->value * (int64_t)elem_size;
                    ir_emit_copy(cg->ir, offset, const_off);
                } else {
                    IRVal idx64 = ir_new_tmp(cg->ir, 'l');
                    if (idx_val.qbe_type == 'l') {
                        idx64 = idx_val;
                    } else {
                        ir_emit(cg->ir, "    %%t%d =l extsw %%t%d\n", idx64.id, idx_val.id);
                    }
                    IRVal es = ir_new_tmp(cg->ir, 'l');
                    ir_emit_copy(cg->ir, es, (int64_t)elem_size);
                    ir_emit_binary(cg->ir, offset, "mul", idx64, es);
                }

                /* address = base + offset */
                IRVal addr = ir_new_tmp(cg->ir, 'l');
                ir_emit_binary(cg->ir, addr, "add", base, offset);
                cg_emit_store(cg, elem_type, val, addr);
            }
        } else if (d->target->kind == NODE_FIELD) {
            /* (*ptr).field = value  OR  ptr->field = value */
            NodeField *df = node_field_data(d->target);
            /* Compute address of field */
            Type *expr_type = df->expr->type;
            Type *struct_type = NULL;
            if (expr_type && expr_type->kind == KIND_POINTER &&
                expr_type->pointer.elem && expr_type->pointer.elem->kind == KIND_STRUCT) {
                struct_type = expr_type->pointer.elem;
            } else if (expr_type && expr_type->kind == KIND_STRUCT) {
                struct_type = expr_type;
            }
            if (struct_type) {
                IRVal base = cg_expr(cg, df->expr);
                size_t offset = 0;
                Type *field_type = NULL;
                for (size_t i = 0; i < struct_type->struct_type.nfields; i++) {
                    if (strcmp(struct_type->struct_type.fields[i].name->name, df->field) == 0) {
                        offset = struct_type->struct_type.fields[i].offset;
                        field_type = struct_type->struct_type.fields[i].type;
                        break;
                    }
                }
                IRVal addr = base;
                if (offset > 0) {
                    addr = ir_new_tmp(cg->ir, 'l');
                    ir_emit_binary(cg->ir, addr, "add", base, ir_new_int((int64_t)offset));
                }
                cg_emit_store(cg, field_type, val, addr);
            }
        }
        break;
    }
    case NODE_RETURN: {
        NodeReturn *dr = node_return_data(n);
        if (dr->expr) {
            if (cg->has_sret) {
                /* struct return via sret: copy to return slot */
                IRVal src = cg_expr(cg, dr->expr);
                cg_copy_struct(cg, cg->current_ret_type, cg->sret_slot, src);
                IRVal v = {0};
                ir_emit_ret(cg->ir, v);
            } else {
                IRVal val = cg_expr(cg, dr->expr);
                ir_emit_ret(cg->ir, val);
            }
        } else {
            IRVal v = {0};
            ir_emit_ret(cg->ir, v);
        }
        break;
    }
    case NODE_BREAK: {
        /* jump to innermost loop's end block */
        if (cg->loop_depth > 0) {
            ir_emit_jmp(cg->ir, cg->loop_ends[cg->loop_depth - 1]);
        }
        break;
    }
    case NODE_CONTINUE: {
        /* jump to innermost loop's continue target (for: post-body, pre-increment) */
        if (cg->loop_depth > 0) {
            ir_emit_jmp(cg->ir, cg->loop_continues[cg->loop_depth - 1]);
        }
        break;
    }
    case NODE_EXPR_STMT: {
        Node *inner = node_expr_stmt_data(n)->expr;
        if (inner->kind == NODE_ASSIGN) {
            cg_stmt(cg, inner);
        } else {
            cg_expr(cg, inner);
        }
        break;
    }
    case NODE_FOR: {
        NodeFor *df = node_for_data(n);
        /* for i in start..end { body }
           Compile as: allocate mutable slot for i, loop with load/compare/increment */
        IRVal start_val = cg_expr(cg, df->start);
        IRVal end_val = cg_expr(cg, df->end);

        /* determine loop variable type */
        Type *var_type = df->var->type;
        if (!var_type) var_type = type_void(); /* fallback */
        char var_qt = qbe_type_of(var_type);
        int var_size = (int)type_size(var_type);
        if (var_size < 1) var_size = 4;

        /* determine if unsigned for comparison */
        int is_unsigned = 0;
        if (var_type->kind == KIND_PRIMITIVE) {
            switch (var_type->prim) {
            case PRIM_U8: case PRIM_U16: case PRIM_U32: case PRIM_U64:
                is_unsigned = 1; break;
            default: break;
            }
        }
        const char *cmp_op = is_unsigned
            ? (var_qt == 'l' ? "cultl" : "cultw")
            : (var_qt == 'l' ? "csltl" : "csltw");

        /* allocate stack slot for loop variable (mutable) */
        IRVal slot = ir_new_tmp(cg->ir, 'l');
        ir_emit_alloc(cg->ir, slot, var_size);
        ir_emit_store(cg->ir, var_qt, start_val, slot);
        cg_add_local(cg, df->var, slot, 1); /* is_stack=1 */

        IRVal loop_hdr = ir_new_block(cg->ir, "loop");
        IRVal body_b   = ir_new_block(cg->ir, "body");
        IRVal incr_b   = ir_new_block(cg->ir, "incr");
        IRVal exit_b   = ir_new_block(cg->ir, "exit");

        /* push loop labels for break/continue */
        if (cg->loop_depth < MAX_LOOP_DEPTH) {
            cg->loop_starts[cg->loop_depth] = loop_hdr;
            cg->loop_ends[cg->loop_depth] = exit_b;
            cg->loop_continues[cg->loop_depth] = incr_b;  /* for: continue jumps to increment */
            cg->loop_depth++;
        }

        ir_emit_jmp(cg->ir, loop_hdr);

        /* loop header: load i, compare with end */
        ir_emit_label(cg->ir, loop_hdr);
        IRVal i_val = ir_new_tmp(cg->ir, var_qt);
        ir_emit_load(cg->ir, i_val, var_qt, slot);
        IRVal cond = ir_new_tmp(cg->ir, 'w');
        ir_emit_binary(cg->ir, cond, cmp_op, i_val, end_val);
        ir_emit_jnz(cg->ir, cond, body_b, exit_b);

        /* body */
        ir_emit_label(cg->ir, body_b);
        cg_expr(cg, df->body);

        /* increment: load i, add 1, store back */
        ir_emit_label(cg->ir, incr_b);
        IRVal current = ir_new_tmp(cg->ir, var_qt);
        ir_emit_load(cg->ir, current, var_qt, slot);
        IRVal next_val = ir_new_tmp(cg->ir, var_qt);
        ir_emit_binary(cg->ir, next_val, "add", current, ir_new_int(1));
        ir_emit_store(cg->ir, var_qt, next_val, slot);
        ir_emit_jmp(cg->ir, loop_hdr);

        ir_emit_label(cg->ir, exit_b);
        if (cg->loop_depth > 0) cg->loop_depth--;
        break;
    }
    case NODE_WHILE: {
        NodeWhile *dw = node_while_data(n);
        IRVal loop_hdr = ir_new_block(cg->ir, "loop");
        IRVal body_b   = ir_new_block(cg->ir, "body");
        IRVal exit_b   = ir_new_block(cg->ir, "exit");

        /* push loop labels for break/continue */
        if (cg->loop_depth < MAX_LOOP_DEPTH) {
            cg->loop_starts[cg->loop_depth] = loop_hdr;
            cg->loop_ends[cg->loop_depth] = exit_b;
            cg->loop_continues[cg->loop_depth] = loop_hdr;  /* while: continue = header */
            cg->loop_depth++;
        }

        ir_emit_jmp(cg->ir, loop_hdr);

        ir_emit_label(cg->ir, loop_hdr);
        IRVal cond = cg_expr(cg, dw->cond);
        ir_emit_jnz(cg->ir, cond, body_b, exit_b);

        ir_emit_label(cg->ir, body_b);
        cg_expr(cg, dw->body);
        ir_emit_jmp(cg->ir, loop_hdr);

        ir_emit_label(cg->ir, exit_b);
        if (cg->loop_depth > 0) cg->loop_depth--;
        break;
    }
    default:
        cg_expr(cg, n);
        break;
    }
}

/* ── function codegen ── */

static void cg_func(IRBuf *ir, Node *n) {
    NodeFuncDecl *fd = node_func_decl_data(n);
    if (fd->is_extern) return; /* no body to emit */

    Type *ret_type = fd->sym->type && fd->sym->type->kind == KIND_FUNC
                     ? fd->sym->type->func.ret : NULL;
    int is_sret = (ret_type && ret_type->kind == KIND_STRUCT);
    char ret_qt = (ret_type && !is_sret) ? qbe_type_of(ret_type) : 0;

    /* emit header (mangled name when function is owned by a module) */
    if (ret_qt)
        ir_emit(ir, "export function %c ", ret_qt), emit_mangled_name(ir, fd->sym), ir_emit(ir, "(");
    else
        ir_emit(ir, "export function "), emit_mangled_name(ir, fd->sym), ir_emit(ir, "(");
    int first = 1;
    /* sret: hidden return slot pointer is first parameter */
    if (is_sret) {
        ir_emit(ir, "l %%ret");
        first = 0;
    }
    for (size_t i = 0; i < fd->nparams; i++) {
        if (!first) ir_emit(ir, ", ");
        first = 0;
        Type *pt = fd->params[i].sym->type;
        if (pt && pt->kind == KIND_STRUCT)
            ir_emit(ir, "l %%%s", fd->params[i].sym->name);
        else
            ir_emit(ir, "%c %%%s", qbe_type_of(pt), fd->params[i].sym->name);
    }
    ir_emit(ir, ") {\n");
    ir_emit_label(ir, ir_new_block(ir, "start"));

    /* setup context */
    CGContext cg;
    cg.ir = ir;
    cg.nlocals = 0;
    cg.current_ret_type = ret_type;
    cg.has_sret = is_sret;
    cg.sret_slot.qbe_type = 0;
    cg.loop_depth = 0;

    /* register sret slot if needed */
    if (is_sret) {
        cg.sret_slot = ir_new_tmp(ir, 'l');
        ir_emit(ir, "    %%t%d =l copy %%ret\n", cg.sret_slot.id);
    }

    /* register params as locals (copy into SSA temps) */
    for (size_t i = 0; i < fd->nparams; i++) {
        Type *pt = fd->params[i].sym->type;
        char qt = (pt && pt->kind == KIND_STRUCT) ? 'l' : qbe_type_of(pt);
        IRVal param_val = ir_new_tmp(ir, qt);
        ir_emit(ir, "    %%t%d =%c copy %%%s\n",
                param_val.id, qt, fd->params[i].sym->name);
        cg_add_local(&cg, fd->params[i].sym, param_val, 0);
    }

    IRVal body_val = cg_expr(&cg, fd->body);

    /* check if body already ended with an explicit return */
    #define body_returns(body) \
        ((body) && ((body)->kind == NODE_RETURN || \
         ((body)->kind == NODE_BLOCK && node_block_data(body)->nstmts > 0 && \
          node_block_data(body)->stmts[node_block_data(body)->nstmts - 1]->kind == NODE_RETURN)))

    if (!body_returns(fd->body)) {
        /* emit ret only if body doesn't already have one */
        if (is_sret) {
            /* copy result to sret slot before returning */
            cg_copy_struct(&cg, ret_type, cg.sret_slot, body_val);
            IRVal v = {0};
            ir_emit_ret(ir, v);
        } else if (ret_qt != 0 && body_val.qbe_type != 0) {
            ir_emit_ret(ir, body_val);
        } else {
            IRVal v = {0};
            ir_emit_ret(ir, v);
        }
    }
    #undef body_returns

    ir_emit(ir, "}\n\n");
}

/* ── module codegen ── */

/* v0.7 7B: emit one const array element (recursively for struct fields).
   Primitive: writes "w 42" / "b 65" / etc.
   Struct: writes each field value separated by spaces, no outer braces
           (QBE data section is flat — struct is just contiguous fields). */
static void cg_emit_const_data_elem(IRBuf *ir, Node *e, Type *t, int *first);

static void cg_emit_const_prim_data(IRBuf *ir, Node *e, Type *t) {
    char qt = qbe_type_of(t);
    int64_t val = 0;
    if (e->kind == NODE_INT) {
        val = node_int_data(e)->value;
    } else if (e->kind == NODE_BOOL) {
        val = node_bool_data(e)->value ? 1 : 0;
    } else if (e->kind == NODE_FLOAT) {
        /* QBE data section doesn't support f32/f64 literals directly in
           all targets — fall back to bit pattern via int. For now just
           warn: const array of f32/f64 not supported in v0.7. */
        fprintf(stderr, "warning: const array element is float — bit-cast not yet implemented\n");
        val = 0;
    } else {
        fprintf(stderr, "warning: const array element is not a literal — emitting 0\n");
    }
    ir_emit_data(ir, "%c %lld", qt, (long long)val);
}

static void cg_emit_const_data_elem(IRBuf *ir, Node *e, Type *t, int *first) {
    if (!*first) ir_emit_data(ir, ", ");
    if (t->kind == KIND_STRUCT) {
        /* struct literal: emit each field in declaration order */
        NodeStructLit *sl = node_struct_lit_data(e);
        for (size_t i = 0; i < t->struct_type.nfields; i++) {
            const char *fname = t->struct_type.fields[i].name->name;
            /* find matching field init */
            Node *fval = NULL;
            for (size_t j = 0; j < sl->nfields; j++) {
                if (strcmp(sl->fields[j].name, fname) == 0) {
                    fval = sl->fields[j].value;
                    break;
                }
            }
            if (i > 0) ir_emit_data(ir, ", ");
            if (fval) {
                cg_emit_const_prim_data(ir, fval, t->struct_type.fields[i].type);
            } else {
                fprintf(stderr, "warning: struct literal missing field '%s' in const data — emitting 0\n", fname);
                ir_emit_data(ir, "%c 0", qbe_type_of(t->struct_type.fields[i].type));
            }
        }
    } else {
        cg_emit_const_prim_data(ir, e, t);
    }
    *first = 0;
}

void cg_module(IRBuf *ir, Node *module) {
    NodeModule *md = node_module_data(module);
    /* Pass A: emit all const decls as data section (deferred to flush) */
    for (size_t i = 0; i < md->ndeccls; i++) {
        Node *decl = md->decls[i];
        if (decl->kind == NODE_CONST_DECL) {
            NodeConstDecl *d = node_const_decl_data(decl);
            Type *arr_t = d->sym->type;
            if (!arr_t || arr_t->kind != KIND_ARRAY) continue;
            Type *elem_t = arr_t->array.elem;
            size_t n = arr_t->array.count;
            NodeArrayLit *arr = node_array_lit_data(d->init);
            ir_emit_data(ir, "data $%s = { ", d->sym->name);
            int first = 1;
            for (size_t j = 0; j < n; j++) {
                cg_emit_const_data_elem(ir, arr->elems[j], elem_t, &first);
            }
            ir_emit_data(ir, " }\n");
        }
    }
    /* Pass B: emit all functions */
    for (size_t i = 0; i < md->ndeccls; i++) {
        Node *decl = md->decls[i];
        if (decl->kind == NODE_FUNC_DECL) {
            cg_func(ir, decl);
        }
    }
}
