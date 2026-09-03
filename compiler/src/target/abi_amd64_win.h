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

#include "ast.h"   /* Type, TypeKind */

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

#endif
