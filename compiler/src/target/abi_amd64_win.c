/* v2.1.0: Windows x64 QBE-level ABI shaping (Sprint A Stage 2, sub-step 1).
 *
 * Stage 1a.1: only `abi_win_classify_arg` lives here. Subsequent sub-steps
 * (1a.2–1a.5) add `abi_win_emit_function_header` / `_return` /
 * `_call_prelude` / `_struct_arg_slot`.
 *
 * Mirrors `compiler/src0/target/abi_amd64_win.jhyy` Stage 1. C-side changes
 * are the Stage 0 half of the Stage 2 byte-equal closure invariant
 * (C 编 jhyy-stage0 → jhyy 编 jhyy → ... → closure, see
 * `docs/internal/architecture.md` + `memory:make_clean_too_aggressive`).
 *
 * Scope: per `docs/plans/v2/v2.1.0详细实现方案.md` § 1.4, jhyy-side cannot
 * extract x64 prologue / epilogue / shadow space / register allocation
 * (those are QBE internals — grep 0 hits on `push rbp` / `mov rbp` /
 * `sub rsp` / `rcx` / `rdx` / `r8` / `r9` in this codebase). What the
 * compiler actually owns is signature construction + struct-arg copy
 * patterns. `abi_win_classify_arg` is the type-letter table that drives
 * the signature-construction pass.
 */

#include "target/abi_amd64_win.h"
#include "ir.h"   /* qbe_type_of — non-static, declared in ir.h:45 */
#include "arena.h"  /* arena_alloc for abi_win_emit_call_prelude */

/* v2.1.0 abi_win_classify_arg — Type → QBE type letter.
 *
 * Behaviour is byte-equal to the inline ternary previously embedded in
 * `cg_func` (`compiler/src/codegen.c:2325-2330`) and the corresponding
 * local-register copy at `:2368-2370`. The extracted function is the
 * single source of truth for signature type-letter selection.
 *
 * Returns 'l' for:
 *   - KIND_STRUCT (per ABI § 3 LOCKED, struct always by slot pointer)
 *   - KIND_ARRAY (per plan, arrays always by slot pointer; v2.1.0 keeps
 *     the W-007 enum-large handling)
 *   - KIND_ENUM with total_size > 4 (per W-007 fix)
 *   - i64 / u64 / pointer / slice / func (via qbe_type_of)
 *
 * Returns 'w' for:
 *   - i8/i16/i32/u8/u16/u32/bool (via qbe_type_of)
 *   - KIND_ENUM with total_size <= 4
 *
 * Returns 's' / 'd' for f32 / f64 (via qbe_type_of).
 *
 * Returns 0 for KIND_VOID (via qbe_type_of; though void params are
 * unreachable in jhyy).
 */
char abi_win_classify_arg(Type *t) {
    if (!t) return 'w';
    switch (t->kind) {
    case KIND_STRUCT:
        /* Struct always by slot pointer (l). Alloc happens in
           abi_win_emit_struct_arg_slot (sub-step 5); the call site
           passes the slot SSA. */
        return 'l';
    case KIND_ARRAY:
        /* Array always by slot pointer (l). Same slot pattern as struct.
           v2.1.0 adds this branch — pre-v2.1.0 inline code fell through
           to qbe_type_of's `default: return 'w'` which was wrong for
           array params (rarely used in jhyy today but stage-1 cleanup). */
        return 'l';
    case KIND_ENUM:
        /* W-007 fix: large enums (>4 bytes total_size) by slot pointer
           so caller's slot allocation matches callee's view. Mirrors the
           inline check at codegen.c:2327-2328 / 2368-2369. */
        return (t->enum_type.total_size > 4) ? 'l' : 'w';
    case KIND_PRIMITIVE:
    case KIND_POINTER:
    case KIND_SLICE:
    case KIND_FUNC:
    case KIND_VOID:
    default:
        /* Delegate to qbe_type_of for the cases the compiler has no
           ABI-specific override on. Keeps the existing primitive /
           pointer / slice / func / void / unknown-kind behaviour
           byte-equal. */
        return qbe_type_of(t);
    }
}

/* v2.1.0 abi_win_emit_function_header — QBE signature line + @start.
 *
 * Replaces the inline block at codegen.c:cg_func lines 2308-2330. The
 * extraction is byte-equal refactor — same emission order, same spacing,
 * same name mangling rule.
 *
 * Implementation note: the mangled-name rule is duplicated here (was
 * `codegen.c:emit_mangled_name`) so the ABI module stays self-contained
 * (no codegen-internal include). The two implementations must stay
 * byte-equal; if codegen's mangling ever changes, mirror here.
 */
void abi_win_emit_function_header(
    IRBuf *ir,
    Sym *fn_sym,
    Type *ret_type,
    int is_sret,
    Type **param_types,
    const char **param_names,
    size_t n_params
) {
    char ret_qt = (ret_type && !is_sret) ? abi_win_classify_arg(ret_type) : 0;

    /* `export function [<ret_qt>] $name(` */
    if (ret_qt)
        ir_emit(ir, "export function %c ", ret_qt);
    else
        ir_emit(ir, "export function ");
    /* Name mangling — mirrors codegen.c:emit_mangled_name */
    if (fn_sym && fn_sym->module)
        ir_emit(ir, "$%s__%s", fn_sym->module, fn_sym->name ? fn_sym->name : "?");
    else
        ir_emit(ir, "$%s", fn_sym && fn_sym->name ? fn_sym->name : "?");
    ir_emit(ir, "(");

    int first = 1;
    /* sret: hidden return slot pointer is first parameter */
    if (is_sret) {
        ir_emit(ir, "l %%ret");
        first = 0;
    }
    for (size_t i = 0; i < n_params; i++) {
        if (!first) ir_emit(ir, ", ");
        first = 0;
        ir_emit(ir, "%c %%%s",
                abi_win_classify_arg(param_types[i]),
                param_names[i] ? param_names[i] : "?");
    }
    ir_emit(ir, ") {\n");
    ir_emit_label(ir, ir_new_block(ir, "start"));
}

/* v2.1.0 abi_win_emit_return — QBE function-exit `ret` decision.
 *
 * Replaces 6 inline `ir_emit_ret(...)` sites in codegen.c (3 in cg_stmt
 * NODE_RETURN + 3 in cg_func trailing). The sret copy via cg_copy_struct
 * stays inline at the call sites — abi_win_emit_return only owns the
 * `ret` line emission.
 *
 * Behaviour:
 *   - is_sret == 1 → empty `ret` (caller already wrote struct to sret slot)
 *   - is_sret == 0 && val.qbe_type != 0 → `ret <val>`
 *   - is_sret == 0 && val.qbe_type == 0 → empty `ret` (void / sentinel)
 *
 * Byte-equal refactor: same emission, same condition order.
 */
void abi_win_emit_return(IRBuf *ir, IRVal val, int is_sret) {
    if (is_sret) {
        IRVal v = {0};
        ir_emit_ret(ir, v);
    } else if (val.qbe_type != 0) {
        ir_emit_ret(ir, val);
    } else {
        IRVal v = {0};
        ir_emit_ret(ir, v);
    }
}

/* v2.1.0 abi_win_emit_call_prelude — sret slot alloc + args buffer.
 *
 * Replaces the prelude block at codegen.c:cg_expr NODE_CALL ~lines 964-979
 * and the equivalent block at NODE_QUALIFIED_CALL ~lines 1061-1074. The
 * per-arg struct-copy loop stays inline at the call sites (will be
 * extracted in Stage 1a.5 via `abi_win_emit_struct_arg_slot`).
 *
 * Byte-equal behaviour:
 *   - sret=1: alloc8 ret_slot, args buffer of size n+1, args[0] = ret_slot
 *   - sret=0: args buffer of size n (or NULL if n=0)
 *   - non-sret returns ret_slot = {0}
 */
IRVal abi_win_emit_call_prelude(
    IRBuf *ir,
    struct Arena *arena,
    size_t n_user_args,
    int is_sret,
    int rsize,
    IRVal **out_args
) {
    size_t extra = is_sret ? 1 : 0;
    *out_args = (n_user_args + extra > 0)
        ? (IRVal *)arena_alloc(arena, (n_user_args + extra) * sizeof(IRVal))
        : NULL;
    IRVal ret_slot = {0};
    if (is_sret) {
        ret_slot = ir_new_tmp(ir, 'l');
        ir_emit_alloc(ir, ret_slot, rsize);
        (*out_args)[0] = ret_slot;
    }
    return ret_slot;
}

/* v2.1.0 emit_struct_copy — moved from codegen.c (was `cg_copy_struct`).
 *
 * Copies a struct value from src_addr to dst_addr, field by field.
 * Handles nested structs recursively. The QBE-side field load/store
 * instructions are inlined here (used to call codegen.c's static
 * cg_emit_load / cg_emit_store — which took CGContext). To keep this
 * function ABI-pure (no CGContext dep), the sub-word load/store
 * patterns from cg_emit_load/store are replicated inline.
 *
 * The mirror of this function in codegen.c MUST stay byte-equal to this
 * implementation. Since cg_emit_load/store are private to codegen.c
 * (still static), we don't move the helper functions; instead, the
 * pattern is small enough to inline.
 *
 * Behaviour byte-equal to the original cg_copy_struct:
 *   - skip if st is NULL or not KIND_STRUCT
 *   - skip if src or dst is sentinel IRVal{id=0}
 *   - per field: compute offset addresses, recurse if nested struct,
 *     else load+store (sub-word uses loadub/storeb etc.)
 */
void emit_struct_copy(IRBuf *ir, Type *st, IRVal dst_addr, IRVal src_addr) {
    if (!st || st->kind != KIND_STRUCT) return;
    if (irval_is_undef(src_addr) || irval_is_undef(dst_addr)) return;
    for (size_t i = 0; i < st->struct_type.nfields; i++) {
        Type *ft = st->struct_type.fields[i].type;
        size_t offset = st->struct_type.fields[i].offset;
        /* compute field addresses */
        IRVal src_off = ir_new_tmp(ir, 'l');
        IRVal dst_off = ir_new_tmp(ir, 'l');
        if (offset > 0) {
            /* Inline ir_new_int (was static in codegen.c:186; ABI module
               can't depend on codegen-internal helpers). */
            IRVal offset_val;
            offset_val.kind = IRVAL_INT;
            offset_val.ival = (int64_t)offset;
            offset_val.qbe_type = 'l';
            offset_val.name = NULL;
            ir_emit_binary(ir, src_off, "add", src_addr, offset_val);
            ir_emit_binary(ir, dst_off, "add", dst_addr, offset_val);
        } else {
            ir_emit(ir, "    %%t%d =l copy %%t%d\n", src_off.id, src_addr.id);
            ir_emit(ir, "    %%t%d =l copy %%t%d\n", dst_off.id, dst_addr.id);
        }
        if (ft->kind == KIND_STRUCT) {
            emit_struct_copy(ir, ft, dst_off, src_off);
        } else {
            /* Inline cg_emit_load + cg_emit_store for ft (primitive / ptr / etc.) */
            IRVal fval = ir_new_tmp(ir, qbe_type_of(ft));
            /* load */
            if (ft->kind == KIND_PRIMITIVE) {
                const char *insn = NULL;
                switch (ft->prim) {
                case PRIM_I8:   insn = "loadsb"; break;
                case PRIM_U8:   insn = "loadub"; break;
                case PRIM_BOOL: insn = "loadub"; break;
                case PRIM_I16:  insn = "loadsh"; break;
                case PRIM_U16:  insn = "loaduh"; break;
                default: break;
                }
                if (insn) {
                    /* sub-word: always returns word */
                    ir_emit(ir, "    %%t%d =w %s %%t%d\n", fval.id, insn, src_off.id);
                } else {
                    ir_emit_load(ir, fval, qbe_type_of(ft), src_off);
                }
            } else {
                ir_emit_load(ir, fval, qbe_type_of(ft), src_off);
            }
            /* store */
            if (ft->kind == KIND_PRIMITIVE) {
                switch (ft->prim) {
                case PRIM_I8: case PRIM_U8: case PRIM_BOOL:
                    ir_emit(ir, "    storeb %%t%d, %%t%d\n", fval.id, dst_off.id);
                    break;
                case PRIM_I16: case PRIM_U16:
                    ir_emit(ir, "    storeh %%t%d, %%t%d\n", fval.id, dst_off.id);
                    break;
                default:
                    ir_emit_store(ir, qbe_type_of(ft), fval, dst_off);
                    break;
                }
            } else {
                ir_emit_store(ir, qbe_type_of(ft), fval, dst_off);
            }
        }
    }
}

/* v2.1.0 abi_win_emit_struct_arg_slot — pass a struct arg by slot pointer.
 *
 * Per ABI § 3 LOCKED: struct args are passed by slot pointer. Allocate
 * a stack slot of `type_size(struct_type)` bytes (rounded up to 4), copy
 * the source struct into it, and return the slot address IRVal. The
 * caller passes this slot as the actual argument to `call $fn`.
 *
 * Byte-equal refactor of the inline struct-branch in cg_expr NODE_CALL
 * and NODE_QUALIFIED_CALL.
 */
IRVal abi_win_emit_struct_arg_slot(IRBuf *ir, IRVal src, Type *struct_type) {
    int asize = struct_type ? (int)type_size(struct_type) : 0;
    if (asize < 4) asize = 4;
    IRVal copy_slot = ir_new_tmp(ir, 'l');
    ir_emit_alloc(ir, copy_slot, asize);
    emit_struct_copy(ir, struct_type, copy_slot, src);
    return copy_slot;
}
