#include "target_dispatch.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

Target target_default(void) {
    return TARGET_AMD64_WIN;
}

Target target_parse(const char *s) {
    if (strcmp(s, "amd64_win") == 0)                return TARGET_AMD64_WIN;
    if (strcmp(s, "amd64_win_freestanding") == 0)   return TARGET_AMD64_WIN_FREESTANDING;
    if (strcmp(s, "amd64_sysv") == 0)                return TARGET_AMD64_SYSV;
    if (strcmp(s, "amd64_sysv_freestanding") == 0)   return TARGET_AMD64_SYSV_FREESTANDING;
    fprintf(stderr,
        "unknown target '%s', available: amd64_win, amd64_win_freestanding, amd64_sysv, amd64_sysv_freestanding\n",
        s);
    exit(1);
}

const char *target_name(Target t) {
    switch (t) {
    case TARGET_AMD64_WIN:                 return "amd64_win";
    case TARGET_AMD64_WIN_FREESTANDING:    return "amd64_win_freestanding";
    case TARGET_AMD64_SYSV:                return "amd64_sysv";
    case TARGET_AMD64_SYSV_FREESTANDING:   return "amd64_sysv_freestanding";
    }
    return "amd64_win";  /* unreachable; satisfy -Wreturn-type */
}

/* v2.1.0: hosted + freestanding both emit MS x64 (D-GUI-12). amd64_sysv +
 * amd64_sysv_freestanding both → "amd64_sysv" (QBE -t flag). v2.8.1: STUB
 * name → SYSV (rename only, enum value =2 preserved per cross-side byte-equal
 * invariant). */
const char *target_qbe_flag(Target t) {
    switch (t) {
    case TARGET_AMD64_WIN:
    case TARGET_AMD64_WIN_FREESTANDING:
        return "amd64_win";
    case TARGET_AMD64_SYSV:
    case TARGET_AMD64_SYSV_FREESTANDING:
        return "amd64_sysv";
    }
    return "amd64_win";  /* unreachable; satisfy -Wreturn-type */
}

/* v2.4.0 Stage 1: returns multi-line help text for --help CLI.
 * Mirrors jhyy-side `target_help()` in target_dispatch.jhyy — keep in sync.
 * v2.8.1: 3 → 4 targets (add amd64_sysv_freestanding line).
 */
const char *target_help(void) {
    return "targets:\n"
           "  amd64_win                x86_64-w64-mingw32 (default; hosted Windows)\n"
           "  amd64_win_freestanding   x86_64-w64-none (UEFI; v2.1.0+, OVMF demo v2.3.0)\n"
           "  amd64_sysv               x86_64-linux-none (v2.7.0 ship, jhyy-side codegen)\n"
           "  amd64_sysv_freestanding  x86_64-linux-none-freestanding (v2.7.0 ship, OS M4)\n";
}

/* v2.4.0 Stage 1: short status suffix for error messages.
 * v2.8.1: STUB name → SYSV; add SYSV_FREESTANDING case.
 */
const char *target_status(Target t) {
    switch (t) {
    case TARGET_AMD64_WIN:                 return "(default; hosted Windows)";
    case TARGET_AMD64_WIN_FREESTANDING:    return "(UEFI; v2.1.0+, OVMF demo v2.3.0)";
    case TARGET_AMD64_SYSV:                return "(v2.7.0 ship, jhyy-side codegen)";
    case TARGET_AMD64_SYSV_FREESTANDING:   return "(v2.7.0 ship, OS M4 hard)";
    }
    return "";
}

/* v2.4.0 Stage 1: number of supported targets.
 * v2.8.1: 3 → 4 (added TARGET_AMD64_SYSV_FREESTANDING).
 */
int jh_target_count(void) {
    return 4;
}

/* V2-B v2.6.0 (Unit E Wire): backend mode picker.
 * v2.8.1: C-side codegen (compiler/src/codegen.c) 只 emit Win IL, 所以
 * SYSV + SYSV_FREESTANDING → BACKEND_QBE (跟 v2.6.0/v2.7.0 行为一致,
 * C-side 没 jhyy-side self backend 替代)。Win + WinFreestanding → BACKEND_SELF。
 * QBE_FALLBACK env var (read by main.c / main.jhyy) 仍是 explicit override。
 *
 * 注: jhyy-side `target_backend_mode` 在 v2.7.0 ship 后 4 targets 都 →
 * BACKEND_SELF (jhyy-side codegen 真实现)。C-side 仍 BACKEND_QBE for SYSV 是
 * 因为 C-side codegen.c 不会 emit SysV — 真 path 走 jhyy.exe (production) 时
 * 调 jhyy-side target_backend_mode (跟 C-side 这函数无关)。
 */
BackendMode target_backend_mode(Target t) {
    switch (t) {
    case TARGET_AMD64_WIN:
    case TARGET_AMD64_WIN_FREESTANDING:
        return BACKEND_SELF;
    case TARGET_AMD64_SYSV:
    case TARGET_AMD64_SYSV_FREESTANDING:
        return BACKEND_QBE;
    }
    return BACKEND_QBE;  /* unknown → safe QBE fallback */
}