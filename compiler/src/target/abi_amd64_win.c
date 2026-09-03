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
