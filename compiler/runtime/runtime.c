#include "runtime.h"
#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>

#ifdef _WIN32
#include <windows.h>
#endif

void arena_new(Arena *a, size_t size) {
    a->start = (char *)malloc(size);
    if (!a->start) {
        a->cur = a->end = 0;
        return;
    }
    a->cur = a->start;
    a->end = a->start + size;
}

void *arena_alloc(Arena *a, size_t size, size_t align) {
    uintptr_t mask = align - 1;
    char *p = (char *)(((uintptr_t)a->cur + mask) & ~mask);
    if (p + size > a->end) return 0;
    a->cur = p + size;
    return p;
}

void arena_reset(Arena *a) {
    a->cur = a->start;
}

void arena_destroy(Arena *a) {
    free(a->start);
    a->start = a->cur = a->end = 0;
}

/* v1.5.6 W-047: re-decode Unicode command line to CP_ACP argv.
 *
 * Background: PowerShell 5.1 in non-UTF-8 mode (Windows default) and
 * PowerShell 7+ in UTF-8 mode both pass Unicode command lines to Windows
 * via CreateProcessW. C runtime's `int main(int argc, char **argv)`
 * decodes argv using CP_ACP (CP_ACP=936 GB2312 on Chinese Windows), which
 * depends on the actual Unicode bytes the kernel received.
 *
 * In some terminal configurations (cmd.exe with non-UTF-8 codepage, or PS
 * 5.1 with non-ASCII input), the decoded CP_ACP bytes don't match what
 * Windows can find on disk (e.g. file created with UTF-8 name). Bypass C
 * runtime argv and re-decode directly from the Unicode command line.
 *
 * Fix: GetCommandLineW gives the original Unicode command line that
 * Windows received. CommandLineToArgvW parses it into Unicode argv.
 * WideCharToMultiByte(CP_ACP) converts each Unicode arg to CP_ACP bytes —
 * the encoding fopen / CreateProcessA / etc. expect on Chinese Windows.
 *
 * The new argv array + each arg string are heap-allocated and live until
 * the process exits (no need to free since main_jhyy typically calls exit
 * or returns).
 */
static char **g_argv_a = NULL;
static int   g_argc_a = 0;

int main(int argc, char **argv) {
#ifdef _WIN32
    /* W-047: re-decode argv from Unicode command line */
    LPWSTR wcmd = GetCommandLineW();
    if (wcmd) {
        int wargc = 0;
        LPWSTR *wargv = CommandLineToArgvW(wcmd, &wargc);
        if (wargv && wargc >= 1) {
            g_argv_a = (char **)malloc((size_t)wargc * sizeof(char *));
            if (g_argv_a) {
                g_argc_a = wargc;
                for (int i = 0; i < wargc; i++) {
                    int len = WideCharToMultiByte(CP_ACP, 0, wargv[i], -1,
                                                  NULL, 0, NULL, NULL);
                    if (len <= 0) { g_argv_a[i] = NULL; continue; }
                    g_argv_a[i] = (char *)malloc((size_t)len);
                    if (g_argv_a[i]) {
                        WideCharToMultiByte(CP_ACP, 0, wargv[i], -1,
                                            g_argv_a[i], len, NULL, NULL);
                    }
                }
                argv = g_argv_a;
                argc = g_argc_a;
            }
            LocalFree(wargv);
        }
    }
#endif
    return main_jhyy(argc, argv);
}
