#ifndef JHYY_TARGET_DISPATCH_H
#define JHYY_TARGET_DISPATCH_H

/* v2.0.0 target dispatcher (Sprint A Stage 1).
 *
 * Four targets are recognized at parse time:
 *   - TARGET_AMD64_WIN                : x86_64-w64-mingw32 (default; v1.x 兼容)
 *   - TARGET_AMD64_WIN_FREESTANDING   : x86_64-w64-none (UEFI; ships v2.1.0)
 *   - TARGET_AMD64_SYSV               : x86_64-linux-none (ships v2.7.0)
 *   - TARGET_AMD64_SYSV_FREESTANDING  : x86_64-linux-none-freestanding (ships v2.7.0)
 *
 * v2.8.1: STUB name removed (was TARGET_AMD64_SYSV_STUB → TARGET_AMD64_SYSV);
 * enum value `=2` preserved (byte-equal invariant with jhyy-side
 * TARGET_AMD64_SYSV() which returns `2 as i32`). TARGET_AMD64_SYSV_FREESTANDING
 * = 3 NEW (matches jhyy-side).
 *
 * In v2.0.0 only TARGET_AMD64_WIN reaches C-side codegen. The others fatal at
 * cg_module entry pointing at the version where they ship (or, post-v2.8.1,
 * pointing at jhyy-side production binary for SysV/SysVFreestanding). ABI 抽离
 * in v2.1.0; real freestanding .efi + OVMF demo in v2.3.0; real SysV codegen
 * in v2.8.0 (jhyy-side only).
 *
 * Stage 2 byte-equal closure: tag values are matched 1:1 with jhyy-side
 * constants in compiler/src0/target/target_dispatch.jhyy (Amd64Win=0,
 * Amd64WinFreestanding=1, Amd64Sysv=2, Amd64SysvFreestanding=3). The closure
 * invariant is .il byte-equal (not binary byte-equal), so this enum is
 * consumed only as a function parameter — no shared memory layout with
 * jhyy-side.
 */
typedef enum {
    TARGET_AMD64_WIN                 = 0,
    TARGET_AMD64_WIN_FREESTANDING    = 1,
    TARGET_AMD64_SYSV                = 2,
    TARGET_AMD64_SYSV_FREESTANDING   = 3,
} Target;

Target target_parse(const char *s);
Target target_default(void);

/* Triple string for the target (user-facing name, e.g. `amd64_win`). */
const char *target_name(Target t);

/* QBE `-t` flag for the target.
 *
 * v2.1.0: TARGET_AMD64_WIN and TARGET_AMD64_WIN_FREESTANDING both map to
 * `"amd64_win"` since the MS x64 calling convention is byte-identical
 * (D-GUI-12). TARGET_AMD64_SYSV and TARGET_AMD64_SYSV_FREESTANDING both
 * return `"amd64_sysv"`. v2.8.1: STUB name → SYSV (rename only, behavior
 * unchanged).
 *
 * Note: C-side main.c still spawns QBE for the SysV targets if user runs
 * `jhyy_stage0.exe --target=amd64_sysv ...`; this is wrong (QBE doesn't
 * exist anymore for SysV path) — cg_module dispatch in codegen.c fatal
 * before QBE invocation (post-v2.8.1 patch). Use `jhyy.exe` (jhyy-side
 * production) for SysV/SysVFreestanding codegen.
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

/* V2-B v2.6.0 (Unit E Wire): backend mode tag (C-side mirror of jhyy-side
 * `BACKEND_QBE` / `BACKEND_SELF` constants in target_dispatch.jhyy).
 * Stage 2 byte-equal closure: tag values match 1:1 with jhyy-side.
 */
typedef enum {
    BACKEND_QBE  = 0,
    BACKEND_SELF = 1,
} BackendMode;

/* Pick backend mode for target t.
 * v2.8.1: C-side codegen (compiler/src/codegen.c) 只 emit Win IL, 所以
 * SYSV + SYSV_FREESTANDING 都 → BACKEND_QBE (legacy/default 兜底,跟 v2.6.0
 * 行为一致)。Win + WinFreestanding → BACKEND_SELF (jhyy-side 实际处理;
 * C-side 用 BACKEND_SELF 表达 "no QBE spawn needed if 走 jhyy-side path")。
 * 真 SysV/SysVFS codegen 在 jhyy-side codegen_amd64.jhyy (v2.8.0 ship)。
 */
BackendMode target_backend_mode(Target t);

#endif