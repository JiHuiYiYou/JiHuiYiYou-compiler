#ifndef ABI_AMD64_WIN_H
#define ABI_AMD64_WIN_H

/* v2.1.0: Windows x64 QBE-level ABI shaping (Sprint A Stage 2).
 *
 * Mirrors `compiler/src0/target/abi_amd64_win.jhyy`. The 5 functions in this
 * file own all per-target signature construction, sret prepending, struct-arg
 * copy-to-slot, and type classification that previously lived inline in
 * `compiler/src/codegen.c` (`cg_func` / `cg_stmt NODE_RETURN` /
 * `cg_expr NODE_CALL` / `NODE_QUALIFIED_CALL` / `cg_copy_struct`).
 *
 * Scope note: JHYY emits QBE IL, not raw x64. QBE handles rcx/rdx/r8/r9
 * register allocation, 32-byte shadow space, frame layout, and callee-saved
 * register save/restore. The compiler only owns signature construction +
 * struct-arg copy patterns. See `docs/plans/v2/v2.1.0详细实现方案.md` § 1.1.
 */

#include "ast.h"   /* Type, TypeKind, Sym */
#include "ir.h"    /* IRBuf, ir_emit, ir_emit_label, ir_new_block */

/* Classify a JHYY Type as a QBE type letter for function signatures.
 *
 * Returns the QBE type letter as a char:
 *   'w' (word)  — i8/i16/i32/u8/u16/u32/bool, small enum (total_size <= 4)
 *   'l' (long)  — i64/u64, pointer, slice, func, struct, array, large enum
 *   's' (single)— f32
 *   'd' (double)— f64
 *   0           — void
 *
 * Per ABI § 2/3 LOCKED: struct + array always pass by slot pointer (l).
 * W-007 fix: enums with total_size > 4 also pass by slot pointer (l) so
 * the caller's slot allocation matches the callee's view.
 *
 * Mirrors jhyy-side `abi_win_classify_arg` in
 * `compiler/src0/target/abi_amd64_win.jhyy` Stage 1.
 */
char abi_win_classify_arg(Type *t);

/* Emit a QBE IL function signature line + the entry `@start` block label.
 *
 * Replaces the inline block at `codegen.c:cg_func` lines 2308-2330 (the
 * `export function <qt> $name(<args>) {\n@start` construction). The caller
 * is responsible for CGContext bookkeeping (locals reset, has_sret flag,
 * sret slot register + sret param-register, param-local registration) — those
 * stay in `cg_func` since they touch `CGContext` state, not QBE IL.
 *
 * Behaviour:
 *   - ret_type == NULL or is_sret==1 → emit `export function $name(`
 *   - else emit `export function <ret_qt> $name(` where ret_qt =
 *     abi_win_classify_arg(ret_type)
 *   - is_sret==1 prepends `l %ret` as the first parameter (sret hidden
 *     pointer — per ABI § 3 LOCKED, struct return via caller-allocated slot)
 *   - For each (param_types[i], param_names[i]) emit `<qt> %<name>`
 *     comma-separated, qt = abi_win_classify_arg(param_types[i])
 *   - Emit `) {\n` and `@start` label via ir_new_block
 *
 * Name mangling: if `fn_sym->module` is non-NULL, emit `$<module>__<name>`;
 * else `$<name>`. Mirrors codegen.c:emit_mangled_name logic (kept inline
 * here to keep ABI module self-contained — no codegen internal dep).
 *
 * Mirrors jhyy-side `abi_win_emit_function_header` in
 * `compiler/src0/target/abi_amd64_win.jhyy` Stage 1.2.
 */
void abi_win_emit_function_header(
    IRBuf *ir,
    Sym *fn_sym,
    Type *ret_type,
    int is_sret,
    Type **param_types,
    const char **param_names,
    size_t n_params
);

#endif
