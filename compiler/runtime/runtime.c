#include "runtime.h"
#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>

#ifdef _WIN32
#include <windows.h>
#endif

/* v3.0.0 (3d no_std): when a user compiles a .jhyy file with `#[no_std]`,
 * this file is NOT linked (see `main.jhyy link_with_gcc` is_no_std branch).
 * Freestanding replacements live in `compiler/runtime/no_std_core/`:
 *   - panic_handler.jhyy   (M0 stub, divergence loop)
 *   - memcpy.jhyy          (per-byte loop)
 *   - memset.jhyy          (per-byte loop)
 *   - __start_kernel.jhyy  (entry, dispatches to user fn main)
 * Per `jhyy-lang-spec-v4.0.0.md` (the v3.x no_std supplement was folded into
 * it on 2026-10-24), the no_std path uses
 * `-nostartfiles -nodefaultlibs -Wl,--entry=__start_kernel` and links
 * only the user's no_std_core compiled objects (the .jhyy files in that
 * directory). The host's
 * `main → main_jhyy` bridge here is intentionally bypassed in no_std mode
 * (no libc startup, no `int main(int argc, char **argv)` transition).
 *
 * ⚠️ 注释里**不要写注释起始符**(斜杠 + 星号)—— 块注释内再出现它会触发
 * gcc 的 `-Wcomment` 告警("within comment"),而 `-Wall -Wextra` 是本仓的
 * 硬要求(见 Makefile 的 CFLAGS_REPRO)。同类形态历史上真咬过人:
 * W-136「悬空注释吞掉两个 C 桥符号」,而 W-137 修的正是
 * 「`$(CFLAGS_STAGE0)` 未定义 ⇒ `-Wall -Wextra` 一起被丢掉」——
 * 也就是说**当时这条告警是被静音的**,现在开关回来了它就重新露出来。 */

/* v4.0.2 W-074/076: removed unused C-side Arena 24B (`arena_new` /
 * `arena_alloc` / `arena_reset` / `arena_destroy` + `Arena` struct).
 * These were declared + defined since the Stage 0 bootstrap era but
 * have zero callers (real arena paths go through src/arena.c Stage 0
 * or src0/arena.jhyy jhyy-side 40B Arena). Removing the public symbols
 * from runtime.h lets std::arena module drop its `std_` prefix test
 * workaround without ld "multiple definition" conflicts. */

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
    /*
     * stdout **不缓冲**。
     *
     * 为什么:C 运行时给 stdout 的缓冲方式取决于它是不是**交互设备**:
     * - 终端(FILE_TYPE_CHAR):行缓冲/无缓冲 ⇒ printf("请输入一个数字: ")
     *   立刻就显示出来了;
     * - 管道(FILE_TYPE_PIPE):**全缓冲** ⇒ 那句提示一直躺在 4KB 缓冲区里,
     *   直到程序退出才一次性冲出来。
     *
     * 而 stdout 到底是不是终端,取决于**谁在跑这个程序**:
     * - 在 cmd / Windows Terminal 里直接跑 jhyy run ⇒ stdout 是控制台 ⇒ 没事;
     * - 被 IDE、被 CI harness、被 `jhyy run | less` 这种管道包起来 ⇒ stdout
     *   是管道 ⇒ **提示看不见**:程序先问「请输入一个数字:」,可屏幕上一个字
     *   都没有,用户只能瞎猜(用户报过:「有一个输出在输入之前,但他只会在输入
     *   之后打印」—— 那句提示一直卡在缓冲区里,直到程序读完输入才吐出来)。
     *
     * `_IONBF` 让 stdout 跟连控制台时一个样:每次 printf 立即落盘。
     * 代价是每次 printf 一次 write 系统调用 —— 对这种体量的程序无所谓,
     * 而「提示立刻可见」值钱得多。
     *
     * ⚠️ 编译器自己也链 runtime.c,所以 jhyy.exe 的 stdout 同样变成无缓冲 ——
     *    无害:编译时 stdout 是 **0 字节**(进度和诊断全走 stderr,实测过),
     *    只有 `--help` 之类才写 stdout。
     */
    setvbuf(stdout, NULL, _IONBF, 0);
#ifdef _WIN32
    /*
     * 连着**控制台**时,把代码页设成 UTF-8(CP_UTF8)。
     *
     * 为什么:代码页决定「控制台怎么解释程序写出去的字节」。
     * 默认是**系统 OEM 代码页**(中文 Windows = CP936/GBK)⇒ 程序 printf 出去的
     * **UTF-8 字节**会被当成 GBK 解释 ⇒ 屏幕上的中文全是乱码。
     * (实测:伪控制台 ConPTY 里,`printf("请输入一个数字: ")` 显示成
     *  「璇疯緭鍏ヤ竴涓鏁瓧」—— 正是把 UTF-8 字节按 GBK 解的结果。)
     *
     * 设成 CP_UTF8 之后,控制台按 UTF-8 解释 ⇒ 中文正常 ✓。
     *
     * ⚠️ **只在 stdout 是控制台时才设** —— 管道/重定向时字节原样透传,
     *    不该动代码页(IDE 那边按 UTF-8 解管道里的字节;一致性门也是)。
     *
     * ⚠️ 这会改掉**用户那个控制台**的代码页 —— 但那正是我们要的:
     *    之后这个控制台里的所有输出(程序的、cmd 的)都按 UTF-8 走,一致。
     */
    if (GetFileType(GetStdHandle(STD_OUTPUT_HANDLE)) == FILE_TYPE_CHAR) {
        SetConsoleOutputCP(CP_UTF8);
        SetConsoleCP(CP_UTF8);
    }

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
