/* v2.1.0 Stage 2: UEFI-style (freestanding) ABI implementation.
 *
 * Per D-GUI-12, the MS x64 calling convention (rcx/rdx/r8/r9, 32-byte
 * shadow space, callee-saved save/restore) is byte-identical between
 * hosted and freestanding. The 3 signature-shaping functions
 * (function_header / return / call_prelude) delegate to their abi_win_*
 * counterparts. The entry-point and no_crt_init hooks are freestanding
 * specific.
 *
 * Mirrors `compiler/src0/abi_amd64_win_freestanding.jhyy`.
 */

#include "target/abi_amd64_win_freestanding.h"
#include "target/abi_amd64_win.h"   /* delegation to abi_win_* */
#include "ir.h"
#include "arena.h"

/* v2.1.0 Stage 2 § 2.1: function_header — delegate to abi_win_emit_function_header.
 * Byte-equal refactor of hosted path. Future spec drift can land here
 * without touching the hosted ABI.
 */
void abi_fs_emit_function_header(
    IRBuf *ir,
    Sym *fn_sym,
    Type *ret_type,
    int is_sret,
    Type **param_types,
    const char **param_names,
    size_t n_params
) {
    abi_win_emit_function_header(ir, fn_sym, ret_type, is_sret,
                                 param_types, param_names, n_params);
}

/* v2.1.0 Stage 2 § 2.1: return — delegate to abi_win_emit_return. */
void abi_fs_emit_return(IRBuf *ir, IRVal val, int is_sret) {
    abi_win_emit_return(ir, val, is_sret);
}

/* v2.1.0 Stage 2 § 2.1: call_prelude — delegate to abi_win_emit_call_prelude. */
IRVal abi_fs_emit_call_prelude(
    IRBuf *ir,
    struct Arena *arena,
    size_t n_user_args,
    int is_sret,
    int rsize,
    IRVal **out_args
) {
    return abi_win_emit_call_prelude(ir, arena, n_user_args, is_sret, rsize, out_args);
}

/* v2.1.0 Stage 2 § 2.2: emit_entry_point — minimal alias.
 *
 * v2.1.0 ships freestanding .obj only; the user writes their own
 * `main_jhyy` body which is compiled as a normal exported QBE function.
 * No UEFI EFIAPI wrapper is emitted yet (that needs EFI_HANDLE / EFI_SYSTEM_TABLE
 * handling per UEFI spec, deferred to v2.3.0 hello-freestanding.efi).
 *
 * For v2.1.0 the entry point is just a name — QBE's `-t amd64_win` handles
 * the actual ABI. We emit a no-op (return 0) so callers have a hook to
 * extend in v2.x. A real implementation would emit:
 *   - callee-saved save (push rbp, push rbx, ...)
 *   - load args from rcx/r8 (EFI_HANDLE, EFI_SYSTEM_TABLE) if EFI entry
 *   - call user's main_jhyy
 *   - exit via `ret` (UEFI doesn't return) or `hlt`
 */
int abi_fs_emit_entry_point(IRBuf *ir, const char *entry_name) {
    (void)ir;
    (void)entry_name;
    return 1;
}

/* v2.1.0 Stage 2 § 2.3: no_crt_init — no-op.
 *
 * v2.1.0 ships PE/COFF .obj via QBE → GCC link chain. GCC pulls in ucrt
 * startup (__security_cookie etc.) which a true freestanding link (lld-link
 * /subystem:efi) would not provide. v2.1.0 defers the no-crt fixup to
 * v2.3.0 (lld-link + OVMF boot).
 *
 * Hook exists so the dispatch site has a single chokepoint to extend.
 */
int abi_fs_no_crt_init(void) {
    return 1;
}
