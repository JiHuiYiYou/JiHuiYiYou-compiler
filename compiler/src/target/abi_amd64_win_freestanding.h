#ifndef ABI_AMD64_WIN_FREESTANDING_H
#define ABI_AMD64_WIN_FREESTANDING_H

/* v2.1.0 Stage 2: UEFI-style (freestanding) ABI for Windows x64.
 *
 * Mirrors `compiler/src0/abi_amd64_win_freestanding.jhyy`. The MS x64
 * signature shaping (rcx/rdx/r8/r9 + shadow space + caller-allocated
 * sret slot) is byte-identical between hosted and freestanding per
 * decision D-GUI-12 (UEFI 约定 = MS x64); the differences live in:
 *   1. Entry point emission — freestanding wraps the user's main_jhyy
 *      with a freestanding entry stub that handles no ucrt.
 *   2. no_crt_init — no-op in v2.1.0 (QBE/GCC link chain still produces
 *      a PE/COFF .obj; actual .efi link (lld-link) + OVMF boot verify
 *      lands in v2.3.0).
 *
 * See `docs/plans/v2/v2.1.0详细实现方案.md` Stage 2 § 2.1-2.3.
 */

#include "ir.h"      /* IRBuf, ir_emit */
#include "ast.h"     /* Type, Sym */

/* Emit the QBE IL function signature for a freestanding function.
 *
 * Byte-identical to abi_win_emit_function_header (D-GUI-12). Provided
 * as a separate symbol so a future spec drift can land only on the
 * freestanding path without touching the hosted path.
 */
void abi_fs_emit_function_header(
    IRBuf *ir,
    Sym *fn_sym,
    Type *ret_type,
    int is_sret,
    Type **param_types,
    const char **param_names,
    size_t n_params
);

/* Emit the QBE `ret` instruction. Mirrors abi_win_emit_return. */
void abi_fs_emit_return(IRBuf *ir, IRVal val, int is_sret);

/* Set up a call's args buffer + sret slot. Mirrors abi_win_emit_call_prelude. */
IRVal abi_fs_emit_call_prelude(
    IRBuf *ir,
    struct Arena *arena,
    size_t n_user_args,
    int is_sret,
    int rsize,
    IRVal **out_args
);

/* v2.1.0 Stage 2: Emit the freestanding entry point.
 *
 * Wraps the user's main_jhyy (or whichever entry symbol the user names
 * via `#[entry]` — v2.1.0 defaults to `main_jhyy`) with a minimal
 * freestanding entry stub. In v2.1.0 this is a thin alias: the entry
 * point IS the user's main_jhyy (QBE handles the actual prologue via
 * `-t amd64_win`); future v2.x may emit a UEFI-style EFIAPI wrapper
 * (callee-saved + rdi=ImageHandle + rsi=SystemTable).
 *
 * Current implementation: emit a `export function $entry_name {` alias
 * line if needed, otherwise no-op. The user can opt-in to a custom
 * entry name via `#[entry = "my_entry"]` (deferred to v2.x).
 */
int abi_fs_emit_entry_point(IRBuf *ir, const char *entry_name);

/* v2.1.0 Stage 2: no_crt_init — no-op.
 *
 * v2.1.0 ships PE/COFF .obj only; linking happens via QBE → GCC, which
 * still references ucrt startup stubs (`__security_cookie` etc.) that
 * QBE -t amd64_win emits. True ucrt-bypass happens at lld-link / EFI
 * link time (v2.3.0). For v2.1.0 this function is a placeholder so the
 * dispatch site has a single hook point; no QBE IL is emitted.
 */
int abi_fs_no_crt_init(void);

#endif
