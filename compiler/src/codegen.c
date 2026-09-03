#include "codegen.h"
#include "arena.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "target/abi_amd64_win.h"  /* v2.1.0 Stage 1a.1: abi_win_classify_arg */

/* v2.1.0 Stage 1a.2: name mangling moved to abi_win_emit_function_header
 * (in target/abi_amd64_win.c). The compiler's emit_mangled_name helper is
 * no longer needed; ABI module owns the rule. */

/* ── side table: map Sym* → IRVal for local vars ── */
#define MAX_LOCALS 1024
#define MAX_LOOP_DEPTH 32
typedef struct {
    Sym  *sym;
    IRVal value;        /* SSA temp for immutable, stack slot addr for mutable */
    int   is_stack;     /* 1 if value is a stack slot address */
} LocalEntry;

/* v1.4.6 W-017: module-level globals dict (Sym* → QBE data label).
   Mirrors jhyy-side CGModGlobal layout (24 bytes). */
typedef struct {
    Sym        *sym;
    const char *qbe_name;   /* "$<name>" — QBE global identifier */
    char        qbe_type;   /* 'w' / 'l' / 'b' / 's' / 'd' */
} CGModGlobal;

/* CGContext layout MUST match jhyy-side codegen.jhyy CGCONTEXT_SIZE.
   Fields are heap-allocated (calloc) rather than inline arrays so the
   layout is portable between C-side (inline arrays OK but huge) and
   jhyy-side (no fixed-size struct fields). See docs/internal/workarounds.md
   W-005 phase 2 for full diagnosis. */
typedef struct {
    IRBuf       *ir;
    LocalEntry  *locals;             /* calloc'd MAX_LOCALS entries */
    int          nlocals;
    Type        *current_ret_type;
    int64_t      sret_slot_id;       /* temp number for sret slot, -1 if none */
    int          has_sret;
    int          loop_depth;
    /* Loop label stacks: top = innermost loop. continue_target semantics:
         for:   after body, before i++   (loop_continues[depth-1])
         while: same as loop_starts[depth-1] */
    IRVal       *loop_starts;        /* calloc'd MAX_LOOP_DEPTH entries */
    IRVal       *loop_ends;
    IRVal       *loop_continues;
    NodeFuncDecl *current_fn;        /* v1.3.6: current fn (for cg_emit_defers on ret) */
    /* v1.3.5: #[inline] attribute. inline_fns/n_inline_fns is the table of
       all fn decls with is_inline=1 (built by cg_module pass A). When emitting
       a call to one of these, expand the body at the callsite instead of
       emitting `call $name`. current_inline_sym is the sym currently being
       inlined (for recursion guard: detect "I'm inside my own body" and fall
       back to `call`). */
    NodeFuncDecl **inline_fns;
    size_t         n_inline_fns;
    Sym           *current_inline_sym;
    /* v1.4.2: DWARF debug info emit. Layout MUST match jhyy-side CGCONTEXT_SIZE=128.
       last_dbg_line dedups consecutive dbgloc emits (cg_expr fires many times per
       source line; only emit when line changes). dbg_file_emitted tracks whether
       `dbgfile "<src>"` was already written at cg_module top. */
    int           last_dbg_line;
    int           dbg_file_emitted;
    /* v1.4.6 W-017: module-level globals (Sym* → QBE data label). Mirrors
       jhyy-side CGCONTEXT_SIZE: +3 fields (mod_globals ptr + 2*i32 count/cap)
       bumping total size 112 → 128. */
    CGModGlobal   *mod_globals;     /* heap-allocated, NULL when empty */
    int            n_mod_globals;
    int            cap_mod_globals;
} CGContext;

static void cg_add_local(CGContext *cg, Sym *sym, IRVal val, int is_stack) {
    if (cg->nlocals < MAX_LOCALS) {
        cg->locals[cg->nlocals].sym = sym;
        cg->locals[cg->nlocals].value = val;
        cg->locals[cg->nlocals].is_stack = is_stack;
        cg->nlocals++;
    }
}

/* W-005 #2: out-param form avoids struct pass-by-value corruption at GCC -O2.
   Caller passes pointer to a stack-allocated IRVal; cg_find_local writes the
   resolved value through *out. */
static void cg_mod_global_register(CGContext *cg, Sym *sym,
                                   const char *qbe_name, char qbe_type) {
    if (cg->n_mod_globals >= cg->cap_mod_globals) {
        int new_cap = cg->cap_mod_globals ? cg->cap_mod_globals * 2 : 8;
        CGModGlobal *ng = realloc(cg->mod_globals,
                                  new_cap * sizeof(CGModGlobal));
        /* first alloc: realloc(NULL, ...) acts like malloc */
        cg->mod_globals = ng;
        cg->cap_mod_globals = new_cap;
    }
    cg->mod_globals[cg->n_mod_globals].sym       = sym;
    cg->mod_globals[cg->n_mod_globals].qbe_name  = qbe_name;
    cg->mod_globals[cg->n_mod_globals].qbe_type  = qbe_type;
    cg->n_mod_globals++;
}

static int cg_mod_global_lookup(CGContext *cg, Sym *sym, IRVal *out) {
    if (!cg->mod_globals) return 0;
    for (int i = 0; i < cg->n_mod_globals; i++) {
        if (cg->mod_globals[i].sym == sym) {
            IRVal v;
            v.kind     = IRVAL_STR;       /* QBE global data label form */
            v.id       = 0;
            v.ival     = 0;
            v.name     = cg->mod_globals[i].qbe_name;
            v.qbe_type = cg->mod_globals[i].qbe_type;
            *out = v;
            return 1;
        }
    }
    return 0;
}

static void cg_find_local(CGContext *cg, Sym *sym, int *is_stack, IRVal *out) {
    for (int i = 0; i < cg->nlocals; i++) {
        if (cg->locals[i].sym == sym) {
            if (is_stack) *is_stack = cg->locals[i].is_stack;
            *out = cg->locals[i].value;
            return;
        }
    }
    /* v1.4.6 W-017: fallthrough — module-level globals. */
    if (cg_mod_global_lookup(cg, sym, out)) {
        if (is_stack) *is_stack = 0;  /* globals are SSA via load, not stack slot */
        return;
    }
    *out = (IRVal){0};  /* zero sentinel: id=0, kind=IRVAL_TEMP */
}

/* v1.3.5: #[inline] call-site expansion helpers.
   The inline FNS table (built by cg_module pass A) maps Sym* → NodeFuncDecl
   for all functions marked #[inline]. */

/* Look up fn_sym in the inline table; return its decl or NULL. */
static NodeFuncDecl *cg_find_inline_decl(CGContext *cg, Sym *fn_sym) {
    if (!cg->inline_fns || !fn_sym) return NULL;
    for (size_t i = 0; i < cg->n_inline_fns; i++) {
        NodeFuncDecl *fd = cg->inline_fns[i];
        if (fd->sym == fn_sym) return fd;
    }
    return NULL;
}

/* v1.3.5 MVP scope: only support bodies that are a single `return <expr>;`
   statement. Anything else (let, if, loops, multiple stmts) requires full
   control-flow expansion (basic block splitting, ret → jmp, etc.) — left for
   v3.x or future sprint.
   Returns the inner expression node if simple, or NULL. */
static Node *cg_inline_simple_return_expr(Node *body) {
    if (!body || body->kind != NODE_BLOCK) return NULL;
    NodeBlock *bd = node_block_data(body);
    if (bd->nstmts != 1) return NULL;
    Node *stmt = bd->stmts[0];
    if (stmt->kind != NODE_RETURN) return NULL;
    NodeReturn *rd = node_return_data(stmt);
    return rd->expr;  /* may be NULL for `return;` (void), treat as non-inlineable */
}

/* ── forward ── */
static void   cg_expr(CGContext *cg, Node *n, IRVal *out);
static void   cg_stmt(CGContext *cg, Node *n);

/* v1.4.2: DWARF debug info emit helpers.
   QBE's .il syntax for DWARF: `dbgfile "<name>"` (top-level) + `dbgloc <line>`
   in function body (BEFORE the next instruction). QBE translates these into
   `.file N "<name>"` + `.loc N <line>` directives in .s, which gdb reads.
   C-side just emits dbgfile once + dbgloc before each line change. */
static int cg_dbg_emit_file(IRBuf *ir, const char *filename) {
    if (!filename) return 0;
    ir_emit(ir, "dbgfile \"%s\"\n", filename);
    return 1;
}

static int cg_dbg_emit_loc(CGContext *cg, int line) {
    if (line == cg->last_dbg_line) return 0;
    if (line <= 0) return 0;
    ir_emit(cg->ir, "    dbgloc %d\n", line);
    cg->last_dbg_line = line;
    return 1;
}

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
    /* Sprint 4.25 W-005 #2 真修: callers may pass a sentinel IRVal (kind=IRVAL_TEMP,
       id=0) when the value source was unreachable (e.g. cg_func epilogue with
       body = `if c { return A } else { return B }`). Without this guard, the
       inner field-by-field emit loop produces `%%t%d =l copy %%t0` lines that
       QBE rejects with "invalid type for first operand %t0". */
    if (irval_is_undef(src_addr) || irval_is_undef(dst_addr)) return;
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

static IRVal cg_match_pattern(CGContext *cg, IRVal matched, Node *pattern, Type *match_type) {
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
        char qt = matched.qbe_type ? matched.qbe_type : 'w';
        /* v1.6.x: lo as NODE_PATTERN_LIT (literal range `1..10`) — manual emit.
           Pre-existing cg_expr call worked for hi=NODE_INT/BOOL/CHAR/IDENT but
           broke for lo=NODE_PATTERN_LIT (cg_expr has no NODE_PATTERN_LIT case →
           falls to default zero IRVal sentinel → QBE reject). */
        IRVal lo_val = {0};
        if (pr->lo->kind == NODE_PATTERN_LIT) {
            NodePatternLit *pl = node_pattern_lit_data(pr->lo);
            lo_val = ir_new_tmp(cg->ir, qt);
            ir_emit_copy(cg->ir, lo_val, pl->value);
        } else {
            cg_expr(cg, pr->lo, &lo_val);
        }
        /* lo <= matched */
        IRVal cmp_lo = ir_new_tmp(cg->ir, 'w');
        ir_emit_binary(cg->ir, cmp_lo, "cslew", lo_val, matched);
        /* matched <= hi — hi parsed via parse_expr(PREC_PRIMARY) on IDENT branch
           so it's always an expression node cg_expr handles (INT/BOOL/CHAR/IDENT). */
        IRVal hi_val = {0};
        cg_expr(cg, pr->hi, &hi_val);
        IRVal cmp_hi = ir_new_tmp(cg->ir, 'w');
        ir_emit_binary(cg->ir, cmp_hi, "cslew", matched, hi_val);
        /* lo <= matched && matched <= hi */
        IRVal result = ir_new_tmp(cg->ir, 'w');
        ir_emit_binary(cg->ir, result, "and", cmp_lo, cmp_hi);
        return result;
    }
    case NODE_PATTERN_ENUM: {
        /* v1.3.7: tag compare + payload slot alias.
           1. Find enum_type from pe->type_sym or by looking up variant_sym->module
              (the enum's name string set by sema).
           2. Find variant tag and payload_offset.
           3. Load tag from matched+0 (word), compare to expected tag → tag_cmp.
           4. If inner is NODE_PATTERN_IDENT, register payload slot alias:
              local.sym = ident.sym, local.value = matched + payload_offset,
              local.is_stack = 1. Body dereferences load from there directly.
              (No copy needed — payload is already in place at slot+payload_offset.) */
        NodePatternEnum *pe = node_pattern_enum_data(pattern);
        if (!pe->variant_sym) {
            /* no variant sym — fallback always-match (defensive) */
            IRVal v = ir_new_tmp(cg->ir, 'w');
            ir_emit_copy(cg->ir, v, 1);
            return v;
        }
        /* Resolve enum_type. Try pe->type_sym first (long form Enum::Variant),
           then fall back to match_type (from NODE_MATCH driver — works for
           short-name form `Some(v)` where type_sym is NULL but match_type
           carries the full enum Type). */
        Type *enum_type = NULL;
        if (pe->type_sym && pe->type_sym->type && pe->type_sym->type->kind == KIND_ENUM) {
            enum_type = pe->type_sym->type;
        } else if (match_type && match_type->kind == KIND_ENUM) {
            enum_type = match_type;
        }
        if (!enum_type) {
            /* no enum type info — fallback always-match (defensive) */
            IRVal v = ir_new_tmp(cg->ir, 'w');
            ir_emit_copy(cg->ir, v, 1);
            return v;
        }

        int expected_tag = -1;
        for (size_t i = 0; i < enum_type->enum_type.nvariants; i++) {
            if (strcmp(enum_type->enum_type.variants[i].name->name,
                       pe->variant_sym->name) == 0) {
                expected_tag = enum_type->enum_type.variants[i].tag;
                break;
            }
        }
        if (expected_tag < 0) {
            /* unknown variant name — fallback always-match (defensive) */
            IRVal v = ir_new_tmp(cg->ir, 'w');
            ir_emit_copy(cg->ir, v, 1);
            return v;
        }

        /* v1.3.7: tag compare + payload slot alias.
           We only do tag compare when the pattern binds a payload (inner is
           IDENT) — i.e. when we actually need to extract the tag. For
           `Some(_)` / `None` (no payload binding), fall through to the
           "always match" default to preserve caller-side semantics (no
           need to peek at the slot). This avoids an ABI mismatch when the
           enum is passed by value (w class) but the caller allocated it on
           stack (l class) — the spilled-w-as-pointer invalidates tag load.
           Tracking: v1.3.7 known limitation, tracked in W-007. */
        if (pe->inner && pe->inner->kind == NODE_PATTERN_IDENT) {
            /* v1.3.7: matched may be a value (w) when the enum is passed by value
               (small enum fits in a register). For tag compare + payload alias we
               need an addressable slot. If matched is w, spill to a temp slot
               first and use that as the slot base. */
            IRVal slot_base = matched;
            if (matched.qbe_type == 'w') {
                IRVal tmp = ir_new_tmp(cg->ir, 'l');
                ir_emit(cg->ir, "    %%t%d =l alloc8 8\n", tmp.id);
                IRVal tmp_addr = ir_new_tmp(cg->ir, 'l');
                ir_emit_binary(cg->ir, tmp_addr, "add", tmp, ir_new_int(0));
                ir_emit(cg->ir, "    storew %%t%d, %%t%d\n", matched.id, tmp_addr.id);
                slot_base = tmp_addr;
            }

            /* load tag from slot_base+0 (word load) */
            IRVal tag_addr = ir_new_tmp(cg->ir, 'l');
            ir_emit_binary(cg->ir, tag_addr, "add", slot_base, ir_new_int(0));
            IRVal loaded_tag = ir_new_tmp(cg->ir, 'w');
            ir_emit(cg->ir, "    %%t%d =w loadw %%t%d\n", loaded_tag.id, tag_addr.id);
            IRVal tag_lit = ir_new_tmp(cg->ir, 'w');
            ir_emit_copy(cg->ir, tag_lit, expected_tag);
            IRVal tag_cmp = ir_new_tmp(cg->ir, 'w');
            ir_emit_binary(cg->ir, tag_cmp, "ceqw", loaded_tag, tag_lit);

            /* payload slot alias (binding only) */
            NodePatternIdent *pi = node_pattern_ident_data(pe->inner);
            Sym *bind_sym = pi->sym;
            IRVal payload_slot = ir_new_tmp(cg->ir, 'l');
            size_t off = (size_t)enum_type->enum_type.payload_offset;
            ir_emit_binary(cg->ir, payload_slot, "add", slot_base, ir_new_int((int64_t)off));
            cg_add_local(cg, bind_sym, payload_slot, 1);

            return tag_cmp;
        }
        /* v1.7.1 patch A3: non-binding enum pattern — 仍 emit tag compare,
           只是 no payload slot alias. 没这 fix 时 `Option::None => 200` 走 fallback cmp=1,
           永远第一 arm 命中 (per docs/internal/workarounds.md § Stage 3 已知限制 +
           W-XXX ACTIVE 段). 跟 src0/codegen.jhyy 镜像. */
        {
            IRVal slot_base2 = matched;
            if (matched.qbe_type == 'w') {
                IRVal tmp2 = ir_new_tmp(cg->ir, 'l');
                ir_emit(cg->ir, "    %%t%d =l alloc8 8\n", tmp2.id);
                IRVal tmp_addr2 = ir_new_tmp(cg->ir, 'l');
                ir_emit_binary(cg->ir, tmp_addr2, "add", tmp2, ir_new_int(0));
                ir_emit(cg->ir, "    storew %%t%d, %%t%d\n", matched.id, tmp_addr2.id);
                slot_base2 = tmp_addr2;
            }
            IRVal tag_addr2 = ir_new_tmp(cg->ir, 'l');
            ir_emit_binary(cg->ir, tag_addr2, "add", slot_base2, ir_new_int(0));
            IRVal loaded_tag2 = ir_new_tmp(cg->ir, 'w');
            ir_emit(cg->ir, "    %%t%d =w loadw %%t%d\n", loaded_tag2.id, tag_addr2.id);
            IRVal tag_lit2 = ir_new_tmp(cg->ir, 'w');
            ir_emit_copy(cg->ir, tag_lit2, expected_tag);
            IRVal tag_cmp2 = ir_new_tmp(cg->ir, 'w');
            ir_emit_binary(cg->ir, tag_cmp2, "ceqw", loaded_tag2, tag_lit2);
            return tag_cmp2;
        }
    }
    case NODE_PATTERN_OR: {
        /* v1.3.7: recurse left+right, combine with `or` */
        NodePatternOr *po = node_pattern_or_data(pattern);
        IRVal cl = cg_match_pattern(cg, matched, po->left, match_type);
        IRVal cr = cg_match_pattern(cg, matched, po->right, match_type);
        IRVal result = ir_new_tmp(cg->ir, 'w');
        ir_emit_binary(cg->ir, result, "or", cl, cr);
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
    else if (src_qt == 'w' && dst_qt == 'l') conv = "extsw";   /* v0.8 bug 11: i32→i64 sign-extend */
    if (!conv) return arg;
    IRVal result = ir_new_tmp(cg->ir, dst_qt);
    ir_emit(cg->ir, "    %%t%d =%c %s %%t%d\n",
            result.id, dst_qt, conv, arg.id);
    return result;
}

/* Bug 2 真修 (v0.9 wip commit 2.85): recursive body terminator check.
 * Detects when a body NODE_IF or NODE_MATCH has all branches terminating
 * (return/break/continue), in which case the parent if/match expression
 * itself terminates control flow (no value flows to phi). The original
 * macro only checked direct NODE_RETURN/BLOCK/BREAK/CONTINUE, missing
 * nested 3-way dispatch (`if A { if B {...} else {...} } else if C {...} else {...}`)
 * which wrongly fell into phi emit path and produced `phi %t0 %t0`
 * referencing sentinel — QBE rejected.
 *
 * Forward decl of cg_expr needed (used for NODE_MATCH arm recurse only via
 * kind check, no actual cg_expr call). */
static int body_terminates_recursive(Node *body);

/* helper: is last stmt of block a terminator (return/break/continue)? */
static int block_last_is_term(Node *block) {
    if (!block || block->kind != NODE_BLOCK) return 0;
    NodeBlock *bd = node_block_data(block);
    if (bd->nstmts <= 0) return 0;
    Node *last = bd->stmts[bd->nstmts - 1];
    return last && (last->kind == NODE_RETURN ||
                    last->kind == NODE_BREAK ||
                    last->kind == NODE_CONTINUE);
}

static int body_terminates_recursive(Node *body) {
    if (!body) return 0;
    if (body->kind == NODE_RETURN ||
        body->kind == NODE_BREAK  ||
        body->kind == NODE_CONTINUE) return 1;
    if (body->kind == NODE_BLOCK) return block_last_is_term(body);
    if (body->kind == NODE_IF) {
        NodeIf *nid = node_if_data(body);
        int then_t = body_terminates_recursive(nid->then_body);
        int else_t = nid->else_body ? body_terminates_recursive(nid->else_body) : 1;
        return then_t && else_t;
    }
    if (body->kind == NODE_MATCH) {
        NodeMatch *nm = node_match_data(body);
        if (nm->narms <= 0) return 0;
        for (size_t i = 0; i < nm->narms; i++) {
            if (!body_terminates_recursive(nm->arms[i])) return 0;
        }
        return 1;
    }
    return 0;
}

static void cg_expr(CGContext *cg, Node *n, IRVal *out) {
    if (!n) { *out = (IRVal){0}; return; }

    /* v1.4.2: emit `dbgloc <line>` before any IR for this node, if line changed.
       Dedupe via last_dbg_line (cg_expr fires many times per source line —
       once per subexpression — but most share the same line; only the first
       per line produces a dbgloc). Result: roughly 1 dbgloc per source line per
       function. gdb reads the latest .loc for each instruction. */
    if (n->loc.line > 0) {
        cg_dbg_emit_loc(cg, n->loc.line);
    }

    switch (n->kind) {
    case NODE_INT: {
        NodeInt *d = node_int_data(n);
        IRVal v = ir_new_tmp(cg->ir, qbe_type_of(n->type));
        ir_emit_copy(cg->ir, v, d->value);
        *out = (v); return;
    }
    /* v1.3.3: sizeof(TypeName) — sema fills n->type=i64 + node_int_data(value).
       Emit like NODE_INT (value is the compile-time-computed size). */
    case NODE_SIZEOF: {
        NodeInt *d = node_int_data(n);
        IRVal v = ir_new_tmp(cg->ir, qbe_type_of(n->type));
        ir_emit_copy(cg->ir, v, d->value);
        *out = (v); return;
    }
    /* v1.3.1: null → 0 of expected pointer width.
       Sema must have set n->type to KIND_POINTER via context-fill;
       guard with 'w' fallback if somehow unfilled (defensive). */
    case NODE_NULL: {
        char qt = (n->type && n->type->kind == KIND_POINTER) ? 'l' : 'w';
        IRVal v = ir_new_tmp(cg->ir, qt);
        ir_emit_copy(cg->ir, v, 0);
        *out = (v); return;
    }
    case NODE_BOOL: {
        NodeBool *d = node_bool_data(n);
        IRVal v = ir_new_tmp(cg->ir, 'w');
        ir_emit_copy(cg->ir, v, d->value ? 1 : 0);
        *out = (v); return;
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
        *out = (v); return;
    }
    case NODE_STRING: {
        NodeString *d = node_string_data(n);
        /* Create a null-terminated string data definition, return its address */
        IRVal str_val = ir_new_data_str(cg->ir, d->chars, d->len);
        /* Copy data label to an SSA temp for use in expressions */
        IRVal v = ir_new_tmp(cg->ir, 'l');
        ir_emit(cg->ir, "    %%t%d =l copy %s\n", v.id, str_val.name);
        *out = (v); return;
    }
    case NODE_CHAR: {
        NodeChar *d = node_char_data(n);
        IRVal v = ir_new_tmp(cg->ir, 'w');
        /* v1.7.0 Stage 3: drop (unsigned char) cast — ch is now uint32_t,
           BMP codepoints (0x00..0xFF for ASCII, 0x80..0x7FF for 2-byte) fit. */
        ir_emit_copy(cg->ir, v, (int64_t)d->ch);
        *out = (v); return;
    }
    case NODE_IDENT: {
        NodeIdent *d = node_ident_data(n);
        /* v0.7 7B: const array reference — emit `copy $name` (QBE uses
           $name as a DYNCONST value directly, no separate addr inst). */
        if (d->sym && d->sym->kind == SYM_CONST) {
            IRVal v = ir_new_tmp(cg->ir, 'l');
            ir_emit(cg->ir, "    %%t%d =l copy $%s\n", v.id, d->sym->name);
            *out = (v); return;
        }
        int is_stack = 0;
        IRVal loc;
        cg_find_local(cg, d->sym, &is_stack, &loc);
        if (is_stack) {
            /* structs/arrays/slices are always manipulated via address */
            if (n->type && (n->type->kind == KIND_STRUCT ||
                            n->type->kind == KIND_ARRAY ||
                            n->type->kind == KIND_SLICE)) {
                *out = (loc); return;
            }
            /* load from stack */
            IRVal v = ir_new_tmp(cg->ir, qbe_type_of(n->type));
            cg_emit_load(cg, v, n->type, loc);
            *out = (v); return;
        }
        /* v1.4.6 W-017: module-level global (IRVAL_STR addr) — load via
           cg_emit_load which dispatches on addr.kind (loadw $g_x). */
        if (loc.kind == IRVAL_STR) {
            IRVal v = ir_new_tmp(cg->ir, qbe_type_of(n->type));
            cg_emit_load(cg, v, n->type, loc);
            *out = (v); return;
        }
        *out = (loc); return; /* SSA value */
    }
    case NODE_UNARY: {
        NodeUnary *d = node_unary_data(n);
        IRVal inner = {0};
        cg_expr(cg, d->expr, &inner);
        switch (d->op) {
        case TOKEN_MINUS: {
            IRVal result = ir_new_tmp(cg->ir, inner.qbe_type);
            IRVal zero = ir_new_tmp(cg->ir, inner.qbe_type);
            ir_emit_copy(cg->ir, zero, 0);
            ir_emit_binary(cg->ir, result, "sub", zero, inner);
            *out = (result); return;
        }
        case TOKEN_BANG: {
            /* !expr → logical NOT: result = ceqw(expr, 0) */
            IRVal result = ir_new_tmp(cg->ir, 'w');
            IRVal zero = ir_new_tmp(cg->ir, inner.qbe_type ? inner.qbe_type : 'w');
            ir_emit_copy(cg->ir, zero, 0);
            ir_emit_binary(cg->ir, result, "ceqw", inner, zero);
            *out = (result); return;
        }
        case TOKEN_TILDE: {
            /* ~expr → bitwise NOT: result = xor(expr, -1) */
            IRVal result = ir_new_tmp(cg->ir, inner.qbe_type);
            IRVal neg_one = ir_new_tmp(cg->ir, inner.qbe_type);
            ir_emit_copy(cg->ir, neg_one, -1);
            ir_emit_binary(cg->ir, result, "xor", inner, neg_one);
            *out = (result); return;
        }
        default:
            *out = (inner); return;
        }
    }
    case NODE_BINARY: {
        NodeBinary *d = node_binary_data(n);
        IRVal left = {0};
        cg_expr(cg, d->left, &left);

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
                IRVal right_and = {0};
                cg_expr(cg, d->right, &right_and);
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
                IRVal right_or = {0};
                cg_expr(cg, d->right, &right_or);
                IRVal rb_or = ir_new_tmp(cg->ir, 'w');
                ir_emit_binary(cg->ir, rb_or, "cnew", right_or, ir_new_int(0));
                ir_emit_jmp(cg->ir, merge);

                ir_emit_label(cg->ir, merge);
                ir_emit_phi(cg->ir, result, 2, true_block, one, eval_b, rb_or);
            }
            *out = (result); return;
        }

        /* non-short-circuit: evaluate right eagerly */
        IRVal right = {0};
        cg_expr(cg, d->right, &right);

        /* v1.7.0 Stage 2: pointer arithmetic (spec §9.5).
           - *T + int / *T - int → *T (offset = int * sizeof(elem))
           - int + *T → *T (symmetric)
           - *T - *T → i64 (diff in elements = (left - right) / sizeof(elem)) */
        if ((d->op == TOKEN_PLUS || d->op == TOKEN_MINUS) && n->type) {
            int left_is_ptr = (d->left->type && d->left->type->kind == KIND_POINTER);
            int right_is_ptr = (d->right->type && d->right->type->kind == KIND_POINTER);
            int arith_kind = -1; /* 0=plus, 1=minus */
            if (d->op == TOKEN_PLUS) arith_kind = 0;
            else if (d->op == TOKEN_MINUS) arith_kind = 1;

            /* *T +/- int → *T */
            if (left_is_ptr && !right_is_ptr && arith_kind >= 0) {
                Type *elem_type = d->left->type->pointer.elem;
                size_t elem_size = type_size(elem_type);
                IRVal offset = ir_new_tmp(cg->ir, 'l');
                if (d->right->kind == NODE_INT) {
                    int64_t const_off = node_int_data(d->right)->value * (int64_t)elem_size;
                    ir_emit_copy(cg->ir, offset, const_off);
                } else {
                    IRVal r64 = ir_new_tmp(cg->ir, 'l');
                    if (right.qbe_type == 'l') {
                        r64 = right;
                    } else {
                        ir_emit(cg->ir, "    %%t%d =l extsw %%t%d\n", r64.id, right.id);
                    }
                    IRVal es = ir_new_tmp(cg->ir, 'l');
                    ir_emit_copy(cg->ir, es, (int64_t)elem_size);
                    ir_emit_binary(cg->ir, offset, "mul", r64, es);
                }
                IRVal result_ptr = ir_new_tmp(cg->ir, 'l');
                const char *op_name = (arith_kind == 0) ? "add" : "sub";
                ir_emit_binary(cg->ir, result_ptr, op_name, left, offset);
                *out = (result_ptr); return;
            }

            /* int + *T → *T (symmetric) */
            if (!left_is_ptr && right_is_ptr && arith_kind == 0) {
                Type *elem_type = d->right->type->pointer.elem;
                size_t elem_size = type_size(elem_type);
                IRVal offset = ir_new_tmp(cg->ir, 'l');
                if (d->left->kind == NODE_INT) {
                    int64_t const_off = node_int_data(d->left)->value * (int64_t)elem_size;
                    ir_emit_copy(cg->ir, offset, const_off);
                } else {
                    IRVal l64 = ir_new_tmp(cg->ir, 'l');
                    if (left.qbe_type == 'l') {
                        l64 = left;
                    } else {
                        ir_emit(cg->ir, "    %%t%d =l extsw %%t%d\n", l64.id, left.id);
                    }
                    IRVal es = ir_new_tmp(cg->ir, 'l');
                    ir_emit_copy(cg->ir, es, (int64_t)elem_size);
                    ir_emit_binary(cg->ir, offset, "mul", l64, es);
                }
                IRVal result_ptr = ir_new_tmp(cg->ir, 'l');
                ir_emit_binary(cg->ir, result_ptr, "add", offset, right);
                *out = (result_ptr); return;
            }

            /* *T - *T → i64 (diff in elements) */
            if (left_is_ptr && right_is_ptr && arith_kind == 1) {
                Type *elem_type = d->left->type->pointer.elem;
                size_t elem_size = type_size(elem_type);
                IRVal byte_diff = ir_new_tmp(cg->ir, 'l');
                ir_emit_binary(cg->ir, byte_diff, "sub", left, right);
                IRVal elem_sz = ir_new_tmp(cg->ir, 'l');
                ir_emit_copy(cg->ir, elem_sz, (int64_t)elem_size);
                IRVal result_diff = ir_new_tmp(cg->ir, 'l');
                ir_emit_binary(cg->ir, result_diff, "div", byte_diff, elem_sz);
                *out = (result_diff); return;
            }
        }

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
        *out = (result); return;
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

        /* v1.3.5: #[inline] call-site expansion. Try inline first; fall back
           to `call $name` if the body is not a simple `return <expr>;` or
           the call is recursive. */
        NodeFuncDecl *inline_decl = cg_find_inline_decl(cg, fn_sym);
        Node *simple_expr = inline_decl ? cg_inline_simple_return_expr(inline_decl->body) : NULL;
        int try_inline = (inline_decl != NULL)
                      && (cg->current_inline_sym != fn_sym)
                      && (n->type && n->type->kind != KIND_STRUCT)
                      && (simple_expr != NULL);
        if (try_inline) {
            Node *ret_expr = cg_inline_simple_return_expr(inline_decl->body);
            /* Evaluate args into a fresh buffer (using cg_expr, no struct-copy
               / sret — locals use values directly). v1.3.5 MVP: primitive
               args only; struct args fall back to call. */
            IRVal *arg_vals = NULL;
            if (d->nargs > 0) {
                arg_vals = arena_alloc(cg->ir->arena, d->nargs * sizeof(IRVal));
                for (size_t i = 0; i < d->nargs; i++) {
                    IRVal v = {0};
                    cg_expr(cg, d->args[i], &v);
                    arg_vals[i] = v;
                }
            }
            /* Save caller state and substitute params with arg values. */
            int saved_nlocals = cg->nlocals;
            int saved_loop_depth = cg->loop_depth;
            Sym *prev_inline = cg->current_inline_sym;
            cg->current_inline_sym = fn_sym;
            for (size_t i = 0; i < inline_decl->nparams; i++) {
                cg_add_local(cg, inline_decl->params[i].sym, arg_vals[i], 0);
            }
            /* Emit the body return expr. IDENT refs to params resolve to the
               arg IRVals we just registered as locals. */
            cg_expr(cg, ret_expr, out);
            /* Restore caller state. */
            cg->nlocals = saved_nlocals;
            cg->loop_depth = saved_loop_depth;
            cg->current_inline_sym = prev_inline;
            return;
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
            IRVal arg = {0};
            cg_expr(cg, d->args[i], &arg);
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
            *out = (ret_slot); return;
        }
        char qt = n->type ? qbe_type_of(n->type) : 'w';
        IRVal result = ir_new_tmp(cg->ir, qt);
        ir_emit_call(cg->ir, result, fn_name, args, (int)d->nargs);
        *out = (result); return;
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

        /* v1.3.5: #[inline] call-site expansion for qualified calls (e.g.
           module::fn()). Same logic as NODE_CALL but uses d->resolved sym. */
        NodeFuncDecl *inline_decl2 = cg_find_inline_decl(cg, fn_sym);
        Node *simple_expr2 = inline_decl2 ? cg_inline_simple_return_expr(inline_decl2->body) : NULL;
        int try_inline2 = (inline_decl2 != NULL)
                       && (cg->current_inline_sym != fn_sym)
                       && (n->type && n->type->kind != KIND_STRUCT)
                       && (simple_expr2 != NULL);
        if (try_inline2) {
            Node *ret_expr2 = simple_expr2;
            IRVal *arg_vals2 = NULL;
            if (d->nargs > 0) {
                arg_vals2 = arena_alloc(cg->ir->arena, d->nargs * sizeof(IRVal));
                for (size_t i = 0; i < d->nargs; i++) {
                    IRVal v = {0};
                    cg_expr(cg, d->args[i], &v);
                    arg_vals2[i] = v;
                }
            }
            int saved_nlocals2 = cg->nlocals;
            int saved_loop_depth2 = cg->loop_depth;
            Sym *prev_inline2 = cg->current_inline_sym;
            cg->current_inline_sym = fn_sym;
            for (size_t i = 0; i < inline_decl2->nparams; i++) {
                cg_add_local(cg, inline_decl2->params[i].sym, arg_vals2[i], 0);
            }
            cg_expr(cg, ret_expr2, out);
            cg->nlocals = saved_nlocals2;
            cg->loop_depth = saved_loop_depth2;
            cg->current_inline_sym = prev_inline2;
            return;
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
            IRVal arg = {0};
            cg_expr(cg, d->args[i], &arg);
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
            *out = (ret_slot); return;
        }
        char qt = n->type ? qbe_type_of(n->type) : 'w';
        IRVal result = ir_new_tmp(cg->ir, qt);
        ir_emit_call(cg->ir, result, fn_name, args, (int)d->nargs);
        *out = (result); return;
    }
    case NODE_IF: {
        NodeIf *d = node_if_data(n);
        IRVal cond = {0};
        cg_expr(cg, d->cond, &cond);

        IRVal then_block = ir_new_block(cg->ir, "then");
        IRVal else_block = ir_new_block(cg->ir, "else");
        IRVal merge_block = ir_new_block(cg->ir, "merge");

        ir_emit_jnz(cg->ir, cond, then_block, else_block);

        /* then */
        ir_emit_label(cg->ir, then_block);
        IRVal then_val = {0};
        cg_expr(cg, d->then_body, &then_val);
        int then_returns = body_terminates_recursive(d->then_body);
        /* current block after recursion may be a nested merge block (if then_body
           contains its own if/else). Use it as phi predecessor so the value is
           actually defined there. */
        IRVal then_phi_pred = then_block;
        if (!then_returns) {
            then_phi_pred = ir_current_block(cg->ir);
            ir_emit_jmp(cg->ir, merge_block);
        }

        /* else — no trampoline. After recursive cg_expr(else_body), current block
           is whatever block the recursion ended in (else_block for non-nested
           fallthrough, inner_merge for nested else-if). Emit jmp merge directly
           so phi predecessor matches the block that actually defines else_val. */
        ir_emit_label(cg->ir, else_block);
        IRVal else_val = {0};
        int else_returns = 0;
        IRVal else_phi_pred = else_block;
        if (d->else_body) {
            cg_expr(cg, d->else_body, &else_val);
            else_returns = body_terminates_recursive(d->else_body);
            /* current block is now wherever recursion ended (inner_merge for nested).
               Use it as phi predecessor so the value is actually defined there. */
            IRVal cur = ir_current_block(cg->ir);
            else_phi_pred = cur;
            if (!else_returns) ir_emit_jmp(cg->ir, merge_block);
        } else {
            ir_emit_jmp(cg->ir, merge_block);
        }
        /* phi */
        ir_emit_label(cg->ir, merge_block);
        /* Sprint 5A.3: skip phi emission entirely when if expr is void */
        if (n->type && n->type->kind == KIND_VOID) {
            IRVal v = {0};
            *out = (v); return;
        }
        if (d->else_body && !then_returns && !else_returns) {
            IRVal result = ir_new_tmp(cg->ir, then_val.qbe_type);
            ir_emit_phi(cg->ir, result, 2, then_phi_pred, then_val, else_phi_pred, else_val);
            *out = (result); return;
        }

        if (n->type && n->type->kind == KIND_VOID) {
            IRVal v = {0};
            *out = (v); return;
        }
        *out = (then_val); return; /* fallback */
    }
    case NODE_BLOCK: {
        NodeBlock *d = node_block_data(n);
        IRVal last = {0};
        for (size_t i = 0; i < d->nstmts; i++) {
            Node *stmt = d->stmts[i];
            if (stmt->kind == NODE_RETURN || stmt->kind == NODE_BREAK || stmt->kind == NODE_CONTINUE) {
                cg_stmt(cg, stmt);
                *out = (last); return;
            }
            if (stmt->kind == NODE_EXPR_STMT) {
                NodeExprStmt *es = node_expr_stmt_data(stmt);
                if (es->expr->kind == NODE_ASSIGN) {
                    cg_stmt(cg, es->expr);
                } else {
                    /* capture value as potential block return value */
                    cg_expr(cg, es->expr, &last);
                }
            } else if (stmt->kind == NODE_IF || stmt->kind == NODE_MATCH || stmt->kind == NODE_BLOCK) {
                /* These expression-statement forms may also yield a value
                   (e.g., `if x { 0 } else { 1 }` as a block's last statement
                   is the block's return value). */
                cg_expr(cg, stmt, &last);
            } else {
                cg_stmt(cg, stmt);
            }
        }
        *out = (last); return;
    }
    case NODE_RETURN: {
        NodeReturn *d = node_return_data(n);
        if (d->expr) {
            IRVal val = {0};
            cg_expr(cg, d->expr, &val);
            ir_emit_ret(cg->ir, val);
        } else {
            IRVal v = {0};
            ir_emit_ret(cg->ir, v);
        }
        IRVal v = {0};
        *out = (v); return;
    }
    case NODE_EXPR_STMT: {
        NodeExprStmt *d = node_expr_stmt_data(n);
        IRVal __cg_expr_tmp_ret_1 = {0};
        cg_expr(cg, d->expr, &__cg_expr_tmp_ret_1);
        *out = (__cg_expr_tmp_ret_1); return;
    }

    /* ── cast: expr as Type ── */
    case NODE_CAST: {
        NodeCast *d = node_cast_data(n);
        Type *src_t = d->expr->type;
        Type *dst_t = n->type;
        IRVal inner = {0};
        cg_expr(cg, d->expr, &inner);
        if (!src_t || !dst_t) {
            *out = (inner); return;
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
            *out = (slot); return;
        }
        char src_qt = qbe_type_of(src_t);
        char dst_qt = qbe_type_of(dst_t);
        if (src_qt == dst_qt && src_t->kind == dst_t->kind && src_t->prim == dst_t->prim) {
            /* no-op */
            *out = (inner); return;
        }
        /* sub-word -> word or long: must extend through w class.
 * loadub/loadsb/loaduh/loadsh returns w-class already extended.
 * But if we're converting between sub-word and long (w->l or h->l or b->l),
 * we cannot `=l copy` directly — QBE rejects without extuw/extsw.
 * Chain: b/h -> w (copy, already extended by loadub/loadsb/loaduh/loadsh)
 *        w -> l (extuw for unsigned u8/u16, extsw for signed i8/i16)
 */
        if ((src_qt == 'b' || src_qt == 'h') && (dst_qt == 'w' || dst_qt == 'l')) {
            if (dst_qt == 'w') {
                /* b/h -> w: already word after loadub/loadsb/loaduh/loadsh */
                IRVal result = ir_new_tmp(cg->ir, dst_qt);
                ir_emit(cg->ir, "    %%t%d =%c copy %%t%d\n", result.id, dst_qt, inner.id);
                *out = (result); return;
            }
            /* dst == l: must extend w -> l via extuw (unsigned) or extsw (signed) */
            int is_signed = (src_t->prim == PRIM_I8 || src_t->prim == PRIM_I16);
            IRVal w_tmp = ir_new_tmp(cg->ir, 'w');
            ir_emit(cg->ir, "    %%t%d =w copy %%t%d\n", w_tmp.id, inner.id);
            IRVal l_tmp = ir_new_tmp(cg->ir, 'l');
            ir_emit(cg->ir, "    %%t%d =l %s %%t%d\n", l_tmp.id,
                    is_signed ? "extsw" : "extuw", w_tmp.id);
            *out = (l_tmp); return;
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
            *out = (result); return;
        }
        /* Bug 4 真修 (Sprint v1.1.7): narrowing word -> sub-word (w->b, w->h,
           l->b, l->h) has no explicit QBE conversion instruction, AND QBE
           has no b/h temporary type at all (sub-word only appears as
           load/store operand). The cast is a no-op at IR level — the
           consuming load/store instruction (storeb/loadub/storeh/loaduh)
           takes a word-class source and truncates implicitly. Returning
           inner (word-class) is correct; emitting nothing + sentinel
           IRVal{0} was the historical Bug 4 (storeb %t0 sentinel pollution). */
        if (!conv && (src_qt == 'w' || src_qt == 'l') && (dst_qt == 'b' || dst_qt == 'h')) {
            *out = (inner); return;
        }
        if (!conv) {
            IRVal v = {0};
            *out = (v); return;
        }
        ir_emit(cg->ir, "    %%t%d =%c %s %%t%d\n",
                result.id, dst_qt, conv, inner.id);
        *out = (result); return;
    }

    /* ── address-of: &variable ── */
    case NODE_ADDR_OF: {
        NodeAddrOf *d = node_addr_of_data(n);
        /* target must be a local variable with a stack slot */
        if (d->expr->kind == NODE_IDENT) {
            NodeIdent *id = node_ident_data(d->expr);
            int is_stack = 0;
            IRVal val;
            cg_find_local(cg, id->sym, &is_stack, &val);
            if (is_stack) {
                /* return the stack slot address */
                *out = (val); return;
            }
            /* SSA temp: spill to a new stack slot, update local entry, return slot */
            int size = (int)type_size(id->sym->type);
            if (size < 4) size = 4;
            IRVal slot = ir_new_tmp(cg->ir, 'l');
            ir_emit_alloc(cg->ir, slot, size);
            cg_emit_store(cg, id->sym->type, val, slot);
            cg_add_local(cg, id->sym, slot, 1);
            *out = (slot); return;
        }
        /* v1.7.0 Stage 2: &arr[i] should return the element ADDRESS, not the element VALUE.
         * Old behavior: fell through to fallback (line 1291) which calls cg_expr(arr[i]) and
         * loads the value → caller treats value as *T → segfault on p[j] subscript. */
        if (d->expr->kind == NODE_INDEX) {
            NodeIndex *nd = node_index_data(d->expr);
            Type *arr_type = nd->expr->type;
            if (arr_type && arr_type->kind == KIND_ARRAY) {
                Type *elem_type = arr_type->array.elem;
                size_t elem_size = type_size(elem_type);
                IRVal base = {0};
                if (nd->expr->kind == NODE_IDENT) {
                    NodeIdent *id = node_ident_data(nd->expr);
                    if (id->sym && id->sym->kind == SYM_CONST) {
                        cg_expr(cg, nd->expr, &base);
                    } else {
                        int is_stack = 0;
                        cg_find_local(cg, id->sym, &is_stack, &base);
                    }
                } else {
                    cg_expr(cg, nd->expr, &base);
                }
                IRVal idx = {0};
                cg_expr(cg, nd->index, &idx);
                IRVal offset = ir_new_tmp(cg->ir, 'l');
                if (nd->index->kind == NODE_INT) {
                    int64_t const_off = node_int_data(nd->index)->value * (int64_t)elem_size;
                    ir_emit_copy(cg->ir, offset, const_off);
                } else {
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
                IRVal addr = ir_new_tmp(cg->ir, 'l');
                ir_emit_binary(cg->ir, addr, "add", base, offset);
                *out = (addr); return;
            }
        }
        /* Bug 1 真修: &EXPR.field should return the FIELD ADDRESS, not the field value.
         * Old behavior: fell through to cg_expr(d->expr) which loads the field VALUE,
         * then caller dereferences it → reads random memory (or segfault). */
        if (d->expr->kind == NODE_FIELD) {
            NodeField *fd = node_field_data(d->expr);
            Type *expr_type = fd->expr->type;
            /* determine base pointer + field offset (mirror of NODE_FIELD logic, no load) */
            IRVal base = {0};
            if (expr_type && expr_type->kind == KIND_POINTER &&
                expr_type->pointer.elem && expr_type->pointer.elem->kind == KIND_STRUCT) {
                /* (*ptr).field: base = ptr, offset = field offset in pointee struct */
                cg_expr(cg, fd->expr, &base);
                Type *elem = expr_type->pointer.elem;
                size_t offset = 0;
                for (size_t i = 0; i < elem->struct_type.nfields; i++) {
                    if (strcmp(elem->struct_type.fields[i].name->name, fd->field) == 0) {
                        offset = elem->struct_type.fields[i].offset;
                        break;
                    }
                }
                if (offset > 0) {
                    IRVal addr = ir_new_tmp(cg->ir, 'l');
                    ir_emit_binary(cg->ir, addr, "add", base, ir_new_int((int64_t)offset));
                    *out = (addr); return;
                }
                *out = (base); return; /* offset 0: addr is the pointer */
            }
            /* struct value field: base = stack slot of value */
            if (expr_type && expr_type->kind == KIND_STRUCT) {
                cg_expr(cg, fd->expr, &base);
                size_t offset = 0;
                for (size_t i = 0; i < expr_type->struct_type.nfields; i++) {
                    if (strcmp(expr_type->struct_type.fields[i].name->name, fd->field) == 0) {
                        offset = expr_type->struct_type.fields[i].offset;
                        break;
                    }
                }
                if (offset > 0) {
                    IRVal addr = ir_new_tmp(cg->ir, 'l');
                    ir_emit_binary(cg->ir, addr, "add", base, ir_new_int((int64_t)offset));
                    *out = (addr); return;
                }
                *out = (base); return;
            }
            /* fallback: evaluate as expression (won't work for SSA temps) */
            IRVal v = {0};
            cg_expr(cg, d->expr, &v);
            *out = (v); return;
        }
        /* fallback: evaluate as expression (won't work for SSA temps) */
        IRVal v = {0};
        cg_expr(cg, d->expr, &v);
        *out = (v); return;
    }

    /* ── dereference: *ptr ── */
    case NODE_DEREF: {
        NodeDeref *d = node_deref_data(n);
        IRVal ptr = {0};
        cg_expr(cg, d->expr, &ptr);
        /* Pointer-to-struct: return the pointer itself (struct manipulated by address) */
        if (n->type && n->type->kind == KIND_STRUCT) {
            *out = (ptr); return;
        }
        char qt = n->type ? qbe_type_of(n->type) : 'w';
        IRVal result = ir_new_tmp(cg->ir, qt);
        cg_emit_load(cg, result, n->type, ptr);
        *out = (result); return;
    }

    /* ── struct literal: TypeName { field: val, ... } ── */
    case NODE_STRUCT_LIT: {
        NodeStructLit *d = node_struct_lit_data(n);
        Type *st = n->type;
        if (!st || st->kind != KIND_STRUCT) {
            *out = (IRVal){0}; return;
        }
        int size = (int)type_size(st);
        if (size < 4) size = 4;
        IRVal slot = ir_new_tmp(cg->ir, 'l');
        ir_emit_alloc(cg->ir, slot, size);

        for (size_t i = 0; i < d->nfields; i++) {
            IRVal fval = {0};
            cg_expr(cg, d->fields[i].value, &fval);
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
        *out = (slot); return;
    }

    /* ── enum variant construction: TypeName::Variant(args) ── */
    case NODE_ENUM_VARIANT: {
        NodeEnumVariant *d = node_enum_variant_data(n);
        Type *et = n->type;
        if (!et || et->kind != KIND_ENUM) {
            *out = (IRVal){0}; return;
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
            IRVal pval = {0};
            cg_expr(cg, d->payload, &pval);
            cg_emit_store(cg, payload_type, pval, payload_addr);
        }
        *out = (slot); return;
    }

    /* ── match expression ── */
    case NODE_MATCH: {
        NodeMatch *d = node_match_data(n);
        IRVal matched = {0};
        cg_expr(cg, d->expr, &matched);
        /* v1.8.3.2 W-063 真修: pass SUBJECT type (d->expr->type), not match RESULT type
         * (n->type). Short-name enum pattern `Some(v) => v` falls back to match_type
         * for variant resolution (pe->type_sym is NULL). Subject type (`Option` enum)
         * is KIND_ENUM, so enum_type resolution succeeds + payload slot alias is
         * registered via cg_add_local + body loadw emits. Match result type (i32)
         * is not KIND_ENUM → enum_type silently NULL → cg_match_pattern falls
         * through to "always match cmp=1" fallback → @arm body has no loadw for
         * binding `v` → phi @arm %t0 references undefined %t0 → QBE reject.
         * Mirror src0/codegen.jhyy W-063 fix (commit 1671aff).
         */
        Type *match_type = d->expr->type;

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
                IRVal cmp = cg_match_pattern(cg, matched, arm->pattern, match_type);
                ir_emit_jnz(cg->ir, cmp, body_block, next_check);
            }

            /* body */
            ir_emit_label(cg->ir, body_block);
            IRVal body_val = {0};
            cg_expr(cg, arm->body, &body_val);
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
            *out = (result); return;
        }
        #undef MAX_MATCH_ARMS
        IRVal v = {0};
        *out = (v); return;
    }

    /* ── array index: arr[i] ── */
    case NODE_INDEX: {
        NodeIndex *d = node_index_data(n);
        Type *arr_type = d->expr->type;
        if (!arr_type || (arr_type->kind != KIND_ARRAY && arr_type->kind != KIND_POINTER && arr_type->kind != KIND_SLICE)) {
            *out = (IRVal){0}; return;
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
                cg_expr(cg, d->expr, &base);  /* emits `addr $name` */
            } else {
                int is_stack = 0;
                cg_find_local(cg, id->sym, &is_stack, &base);
            }
        } else if (is_slice) {
            IRVal slice_addr = {0};
            cg_expr(cg, d->expr, &slice_addr);
            base = ir_new_tmp(cg->ir, 'l');
            ir_emit(cg->ir, "    %%t%d =l loadl %%t%d\n", base.id, slice_addr.id);
        } else {
            cg_expr(cg, d->expr, &base);
        }
        /* compute index */
        IRVal idx = {0};
        cg_expr(cg, d->index, &idx);

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
            *out = (addr); return;
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
        *out = (result); return;
    }

    /* ── array literal: [1, 2, 3] ── */
    case NODE_ARRAY_LIT: {
        NodeArrayLit *d = node_array_lit_data(n);
        Type *arr_type = n->type;
        if (!arr_type || arr_type->kind != KIND_ARRAY) {
            *out = (IRVal){0}; return;
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
            IRVal elem_val = {0};
            cg_expr(cg, d->elems[i], &elem_val);
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
        *out = (slot); return;
    }

    /* ── slice literal: &[1, 2, 3] ── */
    case NODE_SLICE_LIT: {
        NodeSliceLit *d = node_slice_lit_data(n);
        /* Codegen the underlying array first; this returns its stack slot */
        IRVal arr_slot = {0};
        cg_expr(cg, d->array, &arr_slot);
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
        *out = (slot); return;
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
            IRVal slice_addr = {0};
            cg_expr(cg, d->base, &slice_addr);
            base = ir_new_tmp(cg->ir, 'l');
            ir_emit(cg->ir, "    %%t%d =l loadl %%t%d\n", base.id, slice_addr.id);
        } else {
            cg_expr(cg, d->base, &base);
        }

        IRVal start_v = {0};
        cg_expr(cg, d->start, &start_v);
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

        IRVal end_v = {0};
        cg_expr(cg, d->end, &end_v);
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
        *out = (slot); return;
    }

    /* ── field access with pointer auto-deref ── */
    case NODE_FIELD: {
        NodeField *d = node_field_data(n);
        Type *expr_type = d->expr->type;
        if (expr_type && expr_type->kind == KIND_SLICE) {
            /* synthetic .ptr / .len fields, slice value is a 16-byte stack slot */
            IRVal slot = {0};
            cg_expr(cg, d->expr, &slot);
            if (strcmp(d->field, "ptr") == 0) {
                IRVal v = ir_new_tmp(cg->ir, 'l');
                ir_emit(cg->ir, "    %%t%d =l loadl %%t%d\n", v.id, slot.id);
                *out = (v); return;
            }
            if (strcmp(d->field, "len") == 0) {
                IRVal off = ir_new_tmp(cg->ir, 'l');
                ir_emit(cg->ir, "    %%t%d =l add %%t%d, 8\n", off.id, slot.id);
                IRVal v = ir_new_tmp(cg->ir, 'l');
                ir_emit(cg->ir, "    %%t%d =l loadl %%t%d\n", v.id, off.id);
                *out = (v); return;
            }
            IRVal v = {0};
            *out = (v); return;
        }
        if (expr_type && expr_type->kind == KIND_POINTER &&
            expr_type->pointer.elem && expr_type->pointer.elem->kind == KIND_STRUCT) {
            /* pointer-to-struct: load pointer, add offset, load field */
            Type *elem = expr_type->pointer.elem;
            IRVal ptr = {0};
            cg_expr(cg, d->expr, &ptr);
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
            /* v1.4.6 W-019 mirror: struct field → return addr (don't load) */
            if (field_type && field_type->kind == KIND_STRUCT) {
                *out = (addr); return;
            }
            IRVal result = ir_new_tmp(cg->ir, field_type ? qbe_type_of(field_type) : 'w');
            cg_emit_load(cg, result, field_type, addr);
            *out = (result); return;
        }
        /* For struct value field access: the value IS the stack slot pointer */
        IRVal base = {0};
        cg_expr(cg, d->expr, &base);
        Type *st = expr_type;
        if (!st || st->kind != KIND_STRUCT) {
            *out = (IRVal){0}; return;
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
        /* v1.4.6 W-019 mirror: struct field → return addr (don't load) */
        if (field_type && field_type->kind == KIND_STRUCT) {
            *out = (addr); return;
        }
        IRVal result = ir_new_tmp(cg->ir, field_type ? qbe_type_of(field_type) : 'w');
        cg_emit_load(cg, result, field_type, addr);
        *out = (result); return;
    }

    /* v1.7.1 patch A2 真修: match arm body `=> r = N` 是 NODE_ASSIGN (parser
       parse_expr 直接返回 expr, 不 wrap NODE_EXPR_STMT), 而 cg_expr (codegen.c:549)
       之前没 NODE_ASSIGN case → default 返回 sentinel, storew 不 emit.
       arm body 调 cg_expr 路径 (codegen.c:1579) 必须 handle NODE_ASSIGN — 直接转
       cg_stmt (cg_stmt.c:1949 完整处理 NODE_ASSIGN 各种 target). 跟 src0/codegen.jhyy
       镜像 — jhyy-side cg_expr 也走 cg_stmt 处理. */
    case NODE_ASSIGN: {
        cg_stmt(cg, n);
        IRVal v = {0};
        *out = (v); return;
    }
    default: {
        IRVal v = {0};
        *out = (v); return;
    }
    }
}

/* v1.3.6: emit all defers in LIFO order (reverse declaration order) before
   a `ret` instruction. Each defer is a NODE_CALL or NODE_QUALIFIED_CALL; we
   type-check the call via cg_expr to fire any side-effecting IR emission
   (struct copy, etc.), discarding the return value. */
static void cg_emit_defers(CGContext *cg, NodeFuncDecl *fd) {
    if (!fd || fd->ndefers == 0) return;
    for (size_t i = fd->ndefers; i > 0; i--) {
        Node *defer = fd->defers[i - 1];
        NodeDefer *dd = node_defer_data(defer);
        if (dd->expr) {
            IRVal discard = {0};
            cg_expr(cg, dd->expr, &discard);
        }
    }
}

static void cg_stmt(CGContext *cg, Node *n) {
    switch (n->kind) {
    case NODE_DEFER: {
        /* v1.3.6: defer body is emitted by cg_emit_defers before `ret`,
           not at declaration site. No-op here. */
        break;
    }
    case NODE_LET: {
        NodeLet *d = node_let_data(n);
        int is_array = (d->sym->type && d->sym->type->kind == KIND_ARRAY);
        int is_struct = (d->sym->type && d->sym->type->kind == KIND_STRUCT);

        if (d->is_mutable || is_array || is_struct) {
            /* For array/struct literal init, use its slot directly (no double alloc) */
            if ((is_array && d->init && d->init->kind == NODE_ARRAY_LIT) ||
                (is_struct && d->init && d->init->kind == NODE_STRUCT_LIT)) {
                IRVal init_val = {0};
                cg_expr(cg, d->init, &init_val);
                cg_add_local(cg, d->sym, init_val, 1);
            } else if (is_struct && d->init) {
                /* Struct from function call or other expression: alloc and copy */
                IRVal src = {0};
                cg_expr(cg, d->init, &src);
                int size = (int)type_size(d->sym->type);
                if (size < 4) size = 4;
                IRVal slot = ir_new_tmp(cg->ir, 'l');
                ir_emit_alloc(cg->ir, slot, size);
                cg_copy_struct(cg, d->sym->type, slot, src);
                cg_add_local(cg, d->sym, slot, 1);
            } else {
                IRVal init_val = {0};
                cg_expr(cg, d->init, &init_val);
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
                IRVal init_val = {0};
                cg_expr(cg, d->init, &init_val);
                cg_add_local(cg, d->sym, init_val, 0);
            } else {
                IRVal init_val = {0};
                cg_expr(cg, d->init, &init_val);
                cg_add_local(cg, d->sym, init_val, 0);
            }
        }
        break;
    }
    case NODE_ASSIGN: {
        NodeAssign *d = node_assign_data(n);
        IRVal val = {0};
        cg_expr(cg, d->value, &val);

        if (d->target->kind == NODE_DEREF) {
            /* *ptr = value — store to pointer target */
            NodeDeref *dd = node_deref_data(d->target);
            IRVal ptr = {0};
            cg_expr(cg, dd->expr, &ptr);
            cg_emit_store(cg, d->target->type, val, ptr);
        } else if (d->target->kind == NODE_IDENT) {
            /* variable assignment */
            NodeIdent *id = node_ident_data(d->target);
            int is_stack = 0;
            IRVal slot;
            cg_find_local(cg, id->sym, &is_stack, &slot);
            if (is_stack) {
                if (d->target->type && d->target->type->kind == KIND_STRUCT) {
                    /* struct copy: val is source address */
                    cg_copy_struct(cg, d->target->type, slot, val);
                } else {
                    cg_emit_store(cg, d->target->type, val, slot);
                }
            }
            /* v1.4.6 W-017: module-level global — cg_find_local returns
               IRVAL_STR with name = "$g_x". cg_emit_load/Store dispatch
               on addr.kind. */
            else if (slot.kind == IRVAL_STR) {
                cg_emit_store(cg, d->target->type, val, slot);
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
                    cg_find_local(cg, id->sym, &is_stack, &base);
                } else {
                    cg_expr(cg, idx->expr, &base);
                }
                IRVal idx_val = {0};
                cg_expr(cg, idx->index, &idx_val);

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
                IRVal base = {0};
                cg_expr(cg, df->expr, &base);
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
                IRVal src = {0};
                cg_expr(cg, dr->expr, &src);
                IRVal sret_addr = {0};
                sret_addr.id = cg->sret_slot_id;
                sret_addr.qbe_type = 'l';
                /* Sprint 4.25 W-005 #2 真修: skip cg_copy_struct when src is the
                   sentinel (e.g. unreachable expression); cg_copy_struct itself
                   is guarded but skipping early keeps the `ret` clean. */
                if (!irval_is_undef(src)) {
                    cg_copy_struct(cg, cg->current_ret_type, sret_addr, src);
                }
                /* v1.3.6: emit LIFO defers before `ret` */
                cg_emit_defers(cg, cg->current_fn);
                /* v2.1.0 Stage 1a.3: abi_win_emit_return centralises the
                   `ret` line decision. sret branch → empty ret. */
                abi_win_emit_return(cg->ir, src, 1);
            } else {
                IRVal val = {0};
                cg_expr(cg, dr->expr, &val);
                /* v1.3.6: emit LIFO defers before `ret` */
                cg_emit_defers(cg, cg->current_fn);
                /* v2.1.0 Stage 1a.3: abi_win_emit_return — non-sret value. */
                abi_win_emit_return(cg->ir, val, 0);
            }
        } else {
            /* v1.3.6: emit LIFO defers before `ret` (void path) */
            cg_emit_defers(cg, cg->current_fn);
            /* v2.1.0 Stage 1a.3: abi_win_emit_return — void (val undef → empty). */
            abi_win_emit_return(cg->ir, (IRVal){0}, 0);
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
            IRVal __cg_expr_tmp_stmt_2 = {0};
            cg_expr(cg, inner, &__cg_expr_tmp_stmt_2);
        }
        break;
    }
    case NODE_FOR: {
        NodeFor *df = node_for_data(n);
        /* for i in start..end { body }
           Compile as: allocate mutable slot for i, loop with load/compare/increment */
        IRVal start_val = {0};
        cg_expr(cg, df->start, &start_val);
        IRVal end_val = {0};
        cg_expr(cg, df->end, &end_val);

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
        IRVal __cg_expr_tmp_stmt_3 = {0};
        cg_expr(cg, df->body, &__cg_expr_tmp_stmt_3);

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
        IRVal cond = {0};
        cg_expr(cg, dw->cond, &cond);
        ir_emit_jnz(cg->ir, cond, body_b, exit_b);

        ir_emit_label(cg->ir, body_b);
        IRVal __cg_expr_tmp_stmt_4 = {0};
        cg_expr(cg, dw->body, &__cg_expr_tmp_stmt_4);
        ir_emit_jmp(cg->ir, loop_hdr);

        ir_emit_label(cg->ir, exit_b);
        if (cg->loop_depth > 0) cg->loop_depth--;
        break;
    }
    default:
        IRVal __cg_expr_tmp_stmt_5 = {0};
        cg_expr(cg, n, &__cg_expr_tmp_stmt_5);
        break;
    }
}

/* ── function codegen ── */

static void cg_func(CGContext *cg, IRBuf *ir, Node *n, NodeFuncDecl **inline_fns, size_t n_inline_fns) {
    NodeFuncDecl *fd = node_func_decl_data(n);
    if (fd->is_extern) return; /* no body to emit */

    Type *ret_type = fd->sym->type && fd->sym->type->kind == KIND_FUNC
                     ? fd->sym->type->func.ret : NULL;
    int is_sret = (ret_type && ret_type->kind == KIND_STRUCT);
    /* ret_qt is used later in cg_func (body trailing `ret` emission) — keep
       it computed here even though Stage 1a.2's abi_win_emit_function_header
       re-derives it internally. */
    char ret_qt = (ret_type && !is_sret) ? abi_win_classify_arg(ret_type) : 0;

    /* v2.1.0 Stage 1a.2: abi_win_emit_function_header centralises the QBE
       signature line (`export function <qt> $name(<args>) {\n@start`)
       construction. Replaces the prior inline block at lines 2308-2330 of
       the pre-v2.1.0 file. The arrays are transient — arena-allocated
       and discarded after the call returns. */
    size_t np = fd->nparams;
    Type **param_types = np > 0
        ? (Type **)arena_alloc(ir->arena, np * sizeof(Type *)) : NULL;
    const char **param_names = np > 0
        ? (const char **)arena_alloc(ir->arena, np * sizeof(const char *)) : NULL;
    for (size_t i = 0; i < np; i++) {
        param_types[i] = fd->params[i].sym->type;
        param_names[i] = fd->params[i].sym->name;
    }
    abi_win_emit_function_header(ir, fd->sym, ret_type, is_sret,
                                  param_types, param_names, np);

    /* setup context */
    /* v1.4.6 W-017: cg is module-level (allocated in cg_module). cg_func
       only resets per-function state. locals/loop arrays/mod_globals survive. */
    cg->nlocals = 0;
    cg->current_ret_type = ret_type;
    cg->has_sret = is_sret;
    cg->sret_slot_id = -1;
    cg->loop_depth = 0;
    cg->current_fn = fd;  /* v1.3.6: cg_emit_defers reads fd->defers in cg_return */
    /* v1.3.5: #[inline] table + recursion guard. Set current_inline_sym to
       fd->sym so calls to fd from within its own body fall back to `call $fn`
       instead of recursing inline (would infinite-expand). */
    cg->inline_fns = inline_fns;
    cg->n_inline_fns = n_inline_fns;
    cg->current_inline_sym = fd->sym;
    /* v1.4.2: reset last_dbg_line for the new function. The first cg_expr call
       will emit the appropriate dbgloc based on the first stmt/expr's source
       line. (Don't emit from cg_func — it would be redundant with cg_expr's
       first emit if the body starts on the same line as the decl, AND wasteful
       if it starts on a later line.) */
    cg->last_dbg_line = 0;
    cg->dbg_file_emitted = 1;  /* dbgfile emitted in cg_module; reset per-func is irrelevant */

    /* register sret slot if needed */
    if (is_sret) {
        cg->sret_slot_id = ir_new_tmp(ir, 'l').id;
        ir_emit(ir, "    %%t%d =l copy %%ret\n", cg->sret_slot_id);
    }

    /* register params as locals (copy into SSA temps) */
    for (size_t i = 0; i < fd->nparams; i++) {
        Type *pt = fd->params[i].sym->type;
        /* v2.1.0 Stage 1a.1: abi_win_classify_arg centralises the type-letter
           selection for local-register copies (struct → l, large enum → l,
           primitive via qbe_type_of). Replaces the prior inline ternary. */
        char qt = abi_win_classify_arg(pt);
        IRVal param_val = ir_new_tmp(ir, qt);
        ir_emit(ir, "    %%t%d =%c copy %%%s\n",
                param_val.id, qt, fd->params[i].sym->name);
        cg_add_local(cg, fd->params[i].sym, param_val, 0);
    }

    IRVal body_val = {0};
    cg_expr(cg, fd->body, &body_val);

    /* check if body already ended with an explicit return */
    #define body_returns(body) \
        ((body) && ((body)->kind == NODE_RETURN || \
         ((body)->kind == NODE_BLOCK && node_block_data(body)->nstmts > 0 && \
          node_block_data(body)->stmts[node_block_data(body)->nstmts - 1]->kind == NODE_RETURN)))

    if (!body_returns(fd->body)) {
        /* emit ret only if body doesn't already have one */
        if (is_sret) {
            /* copy result to sret slot before returning */
            IRVal sret_addr = {0};
            sret_addr.id = cg->sret_slot_id;
            sret_addr.qbe_type = 'l';
            /* Sprint 4.25 W-005 #2 真修: body_val is sentinel IRVal{id=0} when
               `body_returns()` is syntactic-only (e.g. body is `if c { return A }
               else { return B }` — both arms terminate, but the if-expression
               still produces a value, and codegen returns the pre-return then_val
               which was never overwritten). Without this guard, cg_copy_struct
               emits `copy %t0` and QBE rejects the whole function. */
            if (!irval_is_undef(body_val)) {
                cg_copy_struct(cg, ret_type, sret_addr, body_val);
            }
            /* v2.1.0 Stage 1a.3: abi_win_emit_return — sret branch → empty ret. */
            abi_win_emit_return(ir, body_val, 1);
        } else if (ret_qt != 0 && body_val.qbe_type != 0) {
            /* v2.1.0 Stage 1a.3: abi_win_emit_return — value branch. The
               `ret_qt != 0` guard stays here because ABI doesn't know about
               jhyy return-type rules; abi_win_emit_return only owns the
               `ret` line emission. */
            abi_win_emit_return(ir, body_val, 0);
        } else {
            /* v2.1.0 Stage 1a.3: abi_win_emit_return — void/sentinel branch. */
            abi_win_emit_return(ir, body_val, 0);
        }
    }
    #undef body_returns

    ir_emit(ir, "}\n\n");

    /* v1.4.6 W-017: CGContext is module-level; locals/loop arrays/mod_globals
       are freed by cg_module after Pass B. */
}

/* ── module codegen ── */

/* v0.7 7B: emit one const array element (recursively for struct fields).
   Primitive: writes "w 42" / "b 65" / etc.
   Struct: writes each field value separated by spaces, no outer braces
           (QBE data section is flat — struct is just contiguous fields). */
static void cg_emit_const_data_elem(IRBuf *ir, Node *e, Type *t, int *first);

static void cg_emit_const_prim_data(IRBuf *ir, Node *e, Type *t) {
    char qt = qbe_data_type_of(t);  /* v1.6 W-053: data section packs sub-word */
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
                ir_emit_data(ir, "%c 0", qbe_data_type_of(t->struct_type.fields[i].type));
            }
        }
    } else {
        cg_emit_const_prim_data(ir, e, t);
    }
    *first = 0;
}

void cg_module(IRBuf *ir, Node *module, Target t) {
    /* v2.0.0 target dispatch: Amd64Win keeps full v1.x path (fall through to
       the unchanged body below); other targets fatal at entry pointing at the
       version where they ship. ABI 抽离 = v2.1.0; amd64_sysv = v2.x M2. */
    switch (t) {
    case TARGET_AMD64_WIN:
        break;
    case TARGET_AMD64_WIN_FREESTANDING:
        fprintf(stderr,
            "amd64_win_freestanding target: ABI 抽离在 v2.1.0 实现\n");
        exit(1);
    case TARGET_AMD64_SYSV_STUB:
        fprintf(stderr,
            "amd64_sysv target: 实现留 v2.x M2\n");
        exit(1);
    }

    NodeModule *md = node_module_data(module);
    /* v1.4.6 W-017: alloc CGContext at module level (jhyy-side mirror). Locals
       + loop arrays + mod_globals dict live for the whole module — cg_func
       resets only nlocals per function. Mirrors jhyy-side cg_module layout. */
    CGContext cg = {0};
    cg.ir = ir;
    cg.locals        = (LocalEntry*)calloc(MAX_LOCALS,     sizeof(LocalEntry));
    cg.loop_starts   = (IRVal*)     calloc(MAX_LOOP_DEPTH, sizeof(IRVal));
    cg.loop_ends     = (IRVal*)     calloc(MAX_LOOP_DEPTH, sizeof(IRVal));
    cg.loop_continues= (IRVal*)     calloc(MAX_LOOP_DEPTH, sizeof(IRVal));
    /* v1.4.2: emit `dbgfile "<source>"` for DWARF line info.
       QBE: dbgfile → .file N "<name>" in .s. C-side: codegen reads
       module->loc.filename (parser透传 lexer 的 filename),所以直接 emit.
       jhyy-side mirror 同步 (per W-018). */
    if (module->loc.filename) {
        cg_dbg_emit_file(ir, module->loc.filename);
        cg.dbg_file_emitted = 1;
    }
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
        /* v1.4.6 W-017: module-level `let mut g_x: T = expr;` → emit QBE data
           section + register in mod_globals dict for runtime read/write.
           Init expr folded into data section when literal; otherwise zero-init
           + leave runtime init via main() prologue (TODO future sprint). */
        else if (decl->kind == NODE_LET) {
            NodeLet *d = node_let_data(decl);
            if (!d->sym || !d->sym->type) continue;
            Type *lt = d->sym->type;
            /* only primitive globals supported in v1.4.6 MVP */
            if (lt->kind != KIND_PRIMITIVE) continue;
            char qt = qbe_data_type_of(lt);  /* v1.6 W-053: data section packs sub-word */
            if (qt == 0) continue;
            ir_emit_data(ir, "data $%s = { %c ", d->sym->name, qt);
            if (d->init && d->init->kind == NODE_INT) {
                int64_t v = node_int_data(d->init)->value;
                ir_emit_data(ir, "%lld", (long long)v);
            } else {
                ir_emit_data(ir, "0");
            }
            ir_emit_data(ir, " }\n");
            char qname[256];
            snprintf(qname, sizeof(qname), "$%s", d->sym->name);
            cg_mod_global_register(&cg, d->sym,
                                    arena_strdup(ir->arena, qname, strlen(qname)),
                                    qt);
        }
    }
    /* v1.3.5: build #[inline] fn table for call-site expansion lookup.
       Only collects fn decls with is_inline=1. Used by cg_expr NODE_CALL. */
    size_t n_inline = 0;
    for (size_t i = 0; i < md->ndeccls; i++) {
        Node *decl = md->decls[i];
        if (decl->kind == NODE_FUNC_DECL) {
            NodeFuncDecl *fd = node_func_decl_data(decl);
            if (fd->is_inline) n_inline++;
        }
    }
    NodeFuncDecl **inline_fns = NULL;
    if (n_inline > 0) {
        inline_fns = arena_alloc(ir->arena, n_inline * sizeof(NodeFuncDecl*));
        size_t k = 0;
        for (size_t i = 0; i < md->ndeccls; i++) {
            Node *decl = md->decls[i];
            if (decl->kind == NODE_FUNC_DECL) {
                NodeFuncDecl *fd = node_func_decl_data(decl);
                if (fd->is_inline) inline_fns[k++] = fd;
            }
        }
    }
    /* Pass B: emit all functions */
    for (size_t i = 0; i < md->ndeccls; i++) {
        Node *decl = md->decls[i];
        if (decl->kind == NODE_FUNC_DECL) {
            cg_func(&cg, ir, decl, inline_fns, n_inline);
        }
    }
    /* v1.4.6 W-017: free module-level CGContext arrays */
    free(cg.locals);
    free(cg.loop_starts);
    free(cg.loop_ends);
    free(cg.loop_continues);
    free(cg.mod_globals);
}
