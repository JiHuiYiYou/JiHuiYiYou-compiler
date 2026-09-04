#include "target_dispatch.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

Target target_default(void) {
    return TARGET_AMD64_WIN;
}

Target target_parse(const char *s) {
    if (strcmp(s, "amd64_win") == 0)              return TARGET_AMD64_WIN;
    if (strcmp(s, "amd64_win_freestanding") == 0) return TARGET_AMD64_WIN_FREESTANDING;
    if (strcmp(s, "amd64_sysv") == 0)              return TARGET_AMD64_SYSV_STUB;
    fprintf(stderr,
        "unknown target '%s', available: amd64_win, amd64_win_freestanding (amd64_sysv in v2.x M2)\n",
        s);
    exit(1);
}

const char *target_name(Target t) {
    switch (t) {
    case TARGET_AMD64_WIN:              return "amd64_win";
    case TARGET_AMD64_WIN_FREESTANDING: return "amd64_win_freestanding";
    case TARGET_AMD64_SYSV_STUB:        return "amd64_sysv";
    }
    return "amd64_win";  /* unreachable; satisfy -Wreturn-type */
}

/* v2.1.0: hosted + freestanding both emit MS x64 (D-GUI-12). Only
 * amd64_sysv is a real QBE-different target (ships v2.x M2). */
const char *target_qbe_flag(Target t) {
    switch (t) {
    case TARGET_AMD64_WIN:
    case TARGET_AMD64_WIN_FREESTANDING:
        return "amd64_win";
    case TARGET_AMD64_SYSV_STUB:
        return "amd64_sysv";
    }
    return "amd64_win";  /* unreachable; satisfy -Wreturn-type */
}

/* v2.4.0 Stage 1: returns multi-line help text for --help CLI.
 * Mirrors jhyy-side `target_help()` in target_dispatch.jhyy — keep in sync.
 */
const char *target_help(void) {
    return "targets:\n"
           "  amd64_win                x86_64-w64-mingw32 (default; hosted Windows)\n"
           "  amd64_win_freestanding   x86_64-w64-none (UEFI; v2.1.0+, OVMF demo v2.3.0)\n"
           "  amd64_sysv               x86_64-linux-none (v2.x M2)\n";
}

/* v2.4.0 Stage 1: short status suffix for error messages. */
const char *target_status(Target t) {
    switch (t) {
    case TARGET_AMD64_WIN:              return "(default; hosted Windows)";
    case TARGET_AMD64_WIN_FREESTANDING: return "(UEFI; v2.1.0+, OVMF demo v2.3.0)";
    case TARGET_AMD64_SYSV_STUB:        return "(v2.x M2)";
    }
    return "";
}

/* v2.4.0 Stage 1: number of supported targets. */
int jh_target_count(void) {
    return 3;
}