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