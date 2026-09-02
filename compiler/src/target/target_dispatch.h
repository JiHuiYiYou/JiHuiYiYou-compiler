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

/* Triple string for the target — also serves as QBE `-t` flag for v2.0.0.
   Only TARGET_AMD64_WIN is actually passed to QBE; the other two fatal at
   cg_module before QBE invocation. */
const char *target_name(Target t);

#endif