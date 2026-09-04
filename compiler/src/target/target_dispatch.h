#ifndef JHYY_TARGET_DISPATCH_H
#define JHYY_TARGET_DISPATCH_H

/* v2.0.0 target dispatcher (Sprint A Stage 1).
 *
 * Three targets are recognized at parse time:
 *   - TARGET_AMD64_WIN              : x86_64-w64-mingw32 (default; v1.x 兼容)
 *   - TARGET_AMD64_WIN_FREESTANDING : x86_64-w64-none (UEFI; ships v2.1.0)
 *   - TARGET_AMD64_SYSV_STUB        : x86_64-linux-none (ships v2.x M2)
 *
 * In v2.0.0 only TARGET_AMD64_WIN reaches codegen. The other two fatal at
 * cg_module entry pointing at the version where they ship. ABI 抽离 in v2.1.0;
 * real freestanding .efi + OVMF demo in v2.3.0.
 *
 * Stage 2 byte-equal closure: tag values are matched 1:1 with jhyy-side
 * constants in compiler/src0/target/target_dispatch.jhyy (Amd64Win=0,
 * Amd64WinFreestanding=1, Amd64SysvStub=2). The closure invariant is .il
 * byte-equal (not binary byte-equal), so this enum is consumed only as a
 * function parameter — no shared memory layout with jhyy-side.
 */
typedef enum {
    TARGET_AMD64_WIN              = 0,
    TARGET_AMD64_WIN_FREESTANDING = 1,
    TARGET_AMD64_SYSV_STUB        = 2,
} Target;

Target target_parse(const char *s);
Target target_default(void);

/* Triple string for the target (user-facing name, e.g. `amd64_win`). */
const char *target_name(Target t);

/* QBE `-t` flag for the target.
 *
 * v2.1.0: TARGET_AMD64_WIN and TARGET_AMD64_WIN_FREESTANDING both map to
 * `"amd64_win"` since the MS x64 calling convention is byte-identical
 * (D-GUI-12). TARGET_AMD64_SYSV_STUB still returns `"amd64_sysv"` so
 * users get the error from QBE if it slips past cg_module dispatch.
 */
const char *target_qbe_flag(Target t);

/* Multi-line help text listing all supported targets + status (v2.4.0).
 * Used by main.c `--help` flag (C-side init path) and reflected 1:1 by
 * jhyy-side `target_help()` in target_dispatch.jhyy. Keep in sync.
 */
const char *target_help(void);

/* Short status suffix for a target (e.g. "(default; hosted Windows)").
 * v2.4.0 Stage 1: used in target error messages.
 */
const char *target_status(Target t);

/* Number of supported targets (v2.4.0).
 * Exposed for callers that need to enumerate targets without hard-coding
 * the count.
 */
int jh_target_count(void);

#endif