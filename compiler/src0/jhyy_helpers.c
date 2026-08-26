// jhyy_helpers.c — C 端唯一 FFI 桥（v1.0 全程存在）
//
// 桥接 jhyy extern fn 拿不到的 libc 资源：
//   - FILE* 流（jhyy 拿不到 stderr/stdout 全局符号地址）
//   - fopen 二进制模式（jhyy extern fn 的 mode 参数是 *u8，C 端需要写 "wb"）
//   - "filename:line:col: " 前缀格式化（jhyy 端不写 stderr 用 printf 变参）
//
// ABI 对齐 jhyy：
//   *u8 (jhyy) ↔ void* (C) 或 char* — 64-bit 指针
//   i32 (jhyy) ↔ int
//   i64 (jhyy) ↔ long long

#include <stdio.h>
#include <stdlib.h>  // atof (v1 sprint 3 commit 4 prefix_float)
#include <string.h>  // strrchr (v1.4.1 jh_paths_init dirname)
#include <sys/stat.h>  // stat (W-035 layout detection — portable file existence check)

#ifdef _WIN32
#include <windows.h>  // GetModuleFileNameA (jh_paths_init) + CreateProcessA etc (W-038 jh_run)
#endif

/* sprintf_lld：i64 参数 sprintf wrapper（jhyy extern 不能 variadic）。
   Windows x64 ABI 下 i64 和 i32 都走 RCX/RDX/R8/R9 GPR，所以转发安全。
   ir.jhyy 用这个 emit %lld 整数字面量（struct 字段偏移等可能 > INT_MAX）。 */
int sprintf_lld(char *buf, const char *fmt, long long val) {
    return sprintf(buf, fmt, val);
}

/* stderr/stdout 流桥（jhyy 拿不到 FILE* 地址）。
   v1.5.6 W-049: runtime.c 调 _setmode(_O_U8TEXT) 把 stdout/stderr 设成 UTF-8
   mode,这里 fputs 直接走 UTF-8 输出,中文正确显示在 chcp 65001 终端。 */
int jh_fputs_stderr(const char *s) {
    return fputs(s, stderr);
}

int jh_fputs_stdout(const char *s) {
    return fputs(s, stdout);
}

/* 二进制模式 fopen（防 CRLF 污染 QBE IL — v0.6 memory feedback）。
   codegen 翻译 sprint 4 时所有写 .il 都走 jh_fopen_wb。 */
void *jh_fopen_wb(const char *path) {
    return fopen(path, "wb");
}

/* "filename:line:col: " 前缀输出到 stderr。
   sema / parser 错误格式跟 C 端保持一致（参考 sema.c 行 8）。 */
int jh_print_loc_stderr(const char *filename, int line, int col) {
    return fprintf(stderr, "%s:%d:%d: ", filename, line, col);
}

/* QBE Windows amd64 backend bug workaround（plan § 1.5 bug #8）：
   jhyy 端 f64 存 struct 字段 emit `movsd %gpr, (%mem)`（用 GP 寄存器，应该 XMM）。
   workaround：在 C 端做这个 store（GCC emit `movsd %xmm0, (%mem)` 正确）。
   用途：ast_new_float 把 f64 字面量存到 NodeFloat.value 字段。 */
void jh_f64_store(void *dst, double val) {
    *(double *)dst = val;
}

/* v1 sprint 3 commit 4：parse_expr prefix_float 需要把 token 文本转 f64。
   jhyy 不能直接调 atof（jhyy 无 f64 → f64 转换 + 字符串扫描），也不能直接收
   f64 extern 返回（QBE Windows amd64 backend SSE return 未验证）。C 端用 store
   模式写 *dst = atof(buf)，jhyy 拿到 f64 后给 ast_new_float。 */
int jh_f64_atof(const char *s, long long len, void *dst) {
    char buf[128];
    long long n = len < 127 ? len : 127;
    for (long long i = 0; i < n; i++) buf[i] = s[i];
    buf[n] = '\0';
    *(double *)dst = atof(buf);
    return 0;
}

/* v1 sprint 3 commit 4：parse_expr prefix_int 解析 `42i32` / `100u8` 后缀。
   返回 PRIM_* 常量（0..10），无后缀或无法识别返回 PRIM_I32 (2)。 */
int jh_int_suffix_prim(const char *s, long long len) {
    for (long long i = 0; i < len; i++) {
        char c = s[i];
        if (c == 'i' || c == 'u') {
            int bits = 0;
            long long j = i + 1;
            while (j < len && s[j] >= '0' && s[j] <= '9') {
                bits = bits * 10 + (s[j] - '0');
                j++;
            }
            if (c == 'i') {
                switch (bits) {
                    case 8:  return 0;  /* PRIM_I8  */
                    case 16: return 1;  /* PRIM_I16 */
                    case 32: return 2;  /* PRIM_I32 */
                    case 64: return 3;  /* PRIM_I64 */
                }
            } else {
                switch (bits) {
                    case 8:  return 4;  /* PRIM_U8  */
                    case 16: return 5;  /* PRIM_U16 */
                    case 32: return 6;  /* PRIM_U32 */
                    case 64: return 7;  /* PRIM_U64 */
                }
            }
            return 2;  /* fallback PRIM_I32 */
        }
    }
    return 2;  /* no suffix → PRIM_I32 */
}

/* v1.0.0 sprint 5：codegen NODE_FLOAT emit f64/f32 literal to StringBuilder。
   jhyy 不能直接 sprintf f64（QBE Windows amd64 backend SSE return 未验证），
   走 C 端 sprintf 写 StringBuilder buf。返回写入字节数。
   用例：codegen.jhyy NODE_FLOAT 块用 sb_append_cstr 占位 "VAL"，改为
         `char fmt_buf[64]; jh_sprintf_f64(fmt_buf, val); sb_append_cstr(buf, fmt_buf);` */

/* __attribute__((used)) 防止 gcc strip unused symbols — jhyy 编 main.jhyy 时
   main.jhyy 不直接调 jh_sprintf_f64，但 codegen.jhyy 调（运行期），gcc 会 strip
   该符号 → jhyy_v1 binary 找不到符号 segfault */
__attribute__((used)) int jh_sprintf_f64(char *buf, double val) {
    return sprintf(buf, "%.17g", val);
}

__attribute__((used)) int jh_sprintf_f32(char *buf, double val) {
    return sprintf(buf, "%.9g", (float)val);
}

/* v1.0.0 sprint 5: debug printf helpers (int / long long) to stderr.
   jhyy extern 不能 variadic, 用 wrapper 接 i32 / i64. */
__attribute__((used)) int jh_fmt_d_stderr(const char *fmt, int val) {
    return fprintf(stderr, fmt, val);
}
__attribute__((used)) int jh_fmt_lld_stderr(const char *fmt, long long val) {
    return fprintf(stderr, fmt, val);
}

/* v1.4.1: 路径硬编码消除 — jhyy 端 codegen 不实现真正的顶层 let mut global
   (g_qbe 等会被常量折叠为 0), 所以路径状态放在 C runtime。
   - jh_paths_init(argv0) 一次: argv[0] 推项目根, 填 4 个 static buffer
   - jh_path_*() 多次读: 返回 const char* 到 static buffer
   ABI: argv0=*u8(i64 ptr), 返回 i32 (=0 OK / !=0 err)
   与 main.c compute_project_root 镜像 (C 端不调这个 fn, jhyy 端才调)。

   v1.4.6 W-017 DEPRECATED: jhyy-side codegen 现在能 emit 真 module-level
   global (QBE data section + mod_globals dict), 不再需要委托 path state 到
   C runtime。本节保留 1-2 sprint 观察期, v1.5 installer 设计时决定删 / 留。
   v1.4.6 后续: 可以逐步从 main.jhyy 移除 extern decl + wrapper, 改用顶层
   `let mut path_qbe: *u8 = ...` 模式, 配合 init 函数一次性写入。
   详见 docs/internal/workarounds.md W-017 superseder 段。 */
static char jh_path_qbe_buf[1024];
static char jh_path_gcc_buf[1024];
static char jh_path_runtime_buf[1024];
static char jh_path_helpers_buf[1024];
static int  jh_paths_initialized = 0;

__attribute__((used)) int jh_paths_init(const char *argv0) {
    char exe_path[1024];
    char dir_path[1024];
    char root[1024];
    char test_path[1024];
    int has_sep = argv0 && (strchr(argv0, '/') || strchr(argv0, '\\'));
#ifdef _WIN32
    if (!has_sep) {
        unsigned long n = GetModuleFileNameA(NULL, exe_path, sizeof(exe_path));
        if (n == 0 || n >= sizeof(exe_path)) return 1;
    } else
#endif
    {
        if (!argv0) return 1;
        snprintf(exe_path, sizeof(exe_path), "%s", argv0);
    }

    /* v1.5.6 W-037: layout detection (取代 v1.4.1 hardcoded dirname × 4).
       原 bug: dirname × 4 假设 jhyy.exe 在 <root>\compiler\build\bin\ (源码树),
       但 installer layout 是 <INSTALLDIR>\bin\jhyy.exe (只有 1 层), dirname × 4
       走到 C:\ → qbe/qbe.exe 找不到 → "QBE failed". 用户 Code Runner 用 installer
       版 jhyy.exe (PATH 排第一) 时 100% 触发.
       修法: 先试 installer layout (sibling qbe.exe), 否则 walk-up 找 <root>\qbe\qbe.exe.
       详情 docs/internal/workarounds.md W-037. */

    /* Normalize path: ensure backslashes for consistent parsing */
    for (char *p = exe_path; *p; p++) if (*p == '/') *p = '\\';

    /* Extract directory containing jhyy.exe */
    char *last = strrchr(exe_path, '\\');
    if (!last) return 1;
    *last = '\0';
    snprintf(dir_path, sizeof(dir_path), "%s", exe_path);

    /* Layout (a) — sibling qbe.exe (installer 布局) */
    snprintf(test_path, sizeof(test_path), "%s\\qbe.exe", dir_path);
    {
        struct stat st;
        if (stat(test_path, &st) == 0) {
            #pragma GCC diagnostic push
            #pragma GCC diagnostic ignored "-Wformat-truncation"
            snprintf(jh_path_qbe_buf,     sizeof(jh_path_qbe_buf),     "%s\\qbe.exe", dir_path);
            snprintf(jh_path_runtime_buf, sizeof(jh_path_runtime_buf), "%s\\runtime.c", dir_path);
            snprintf(jh_path_helpers_buf, sizeof(jh_path_helpers_buf), "%s\\jhyy_helpers.c", dir_path);
            snprintf(jh_path_gcc_buf,     sizeof(jh_path_gcc_buf),     "gcc");
            #pragma GCC diagnostic pop
            jh_paths_initialized = 1;
            return 0;
        }
    }

    /* Layout (b) — source-tree: walk up to find <root>\qbe\qbe.exe */
    snprintf(root, sizeof(root), "%s", dir_path);
    for (int i = 0; i < 8; i++) {
        snprintf(test_path, sizeof(test_path), "%s\\qbe\\qbe.exe", root);
        {
            struct stat st;
            if (stat(test_path, &st) == 0) {
                #pragma GCC diagnostic push
                #pragma GCC diagnostic ignored "-Wformat-truncation"
                snprintf(jh_path_qbe_buf,     sizeof(jh_path_qbe_buf),     "%s\\qbe\\qbe.exe", root);
                snprintf(jh_path_runtime_buf, sizeof(jh_path_runtime_buf), "%s\\compiler\\runtime\\runtime.c", root);
                snprintf(jh_path_helpers_buf, sizeof(jh_path_helpers_buf), "%s\\compiler\\src0\\jhyy_helpers.c", root);
                snprintf(jh_path_gcc_buf,     sizeof(jh_path_gcc_buf),     "gcc");
                #pragma GCC diagnostic pop
                jh_paths_initialized = 1;
                return 0;
            }
        }
        /* walk up one level */
        char *up = strrchr(root, '\\');
        if (!up || up == root) break;  /* reached drive root, give up */
        *up = '\0';
    }
    return 1;  /* no layout matched */
}

__attribute__((used)) const char *jh_path_qbe(void)     { return jh_path_qbe_buf; }
__attribute__((used)) const char *jh_path_gcc(void)     { return jh_path_gcc_buf; }
__attribute__((used)) const char *jh_path_runtime(void) { return jh_path_runtime_buf; }
__attribute__((used)) const char *jh_path_helpers(void) { return jh_path_helpers_buf; }

/* v1.5.6 W-034: jh_fullpath — convert relative → absolute path.
   Used by cmd_run to produce absolute exe path, since cmd.exe /C only
   searches PATH (not cwd) for bare basenames. _fullpath is MSVCRT
   (mingw has it); falls back to realpath() on POSIX.
   Returns 0 on success, 1 on failure (out_buf unchanged). */
__attribute__((used)) int jh_fullpath(char *out_buf, const char *rel_path, int max_len) {
#ifdef _WIN32
    return _fullpath(out_buf, rel_path, max_len) != NULL ? 0 : 1;
#else
    return realpath(rel_path, out_buf) != NULL ? 0 : 1;
#endif
}

/* v1.5.6: jh_gcc_path — A 派 Driver 探测层 (类型 4 per
   feedback_compiler_toolchain_path_resolution memory).
   4 层优先级: JHY_GCC env → JHYY_HOME\env.txt → MSYS2 magic → SearchPathA
   → fallback "gcc". Static buf 缓存, jhyy.exe 启动一次性 resolve.
   替代 W-027 v8 Python 侧 30 行 magic (release.yml + regress.py + jh_path_gcc
   三处探测逻辑收敛到这一处).
   v1.5.6 Windows-only; v2.x 加 #ifdef __linux__ / __APPLE__ 分支.
   详见 docs/plans/v1/v1.5.6任务清单 + 概要设计.md § 设计 1. */
static char jh_gcc_path_buf[1024];
static int  jh_gcc_path_initialized = 0;

#ifdef _WIN32
/* windows.h already included at top — GetFileAttributesA + INVALID_FILE_ATTRIBUTES
   come from fileapi.h. SearchPathA also already declared. */

__attribute__((used)) const char *jh_gcc_path(void) {
    if (jh_gcc_path_initialized) return jh_gcc_path_buf;

    /* Priority 1: JHY_GCC env (user/CI explicit override) */
    {
        const char *env_gcc = getenv("JHY_GCC");
        if (env_gcc && env_gcc[0] != '\0') {
            snprintf(jh_gcc_path_buf, sizeof(jh_gcc_path_buf), "%s", env_gcc);
            jh_gcc_path_initialized = 1;
            return jh_gcc_path_buf;
        }
    }

    /* Priority 2: JHYY_HOME\env.txt (单行 KEY=VALUE; 注释行 # 开头跳过) */
    {
        const char *jhyy_home = getenv("JHYY_HOME");
        if (jhyy_home && jhyy_home[0] != '\0') {
            char env_file[1024];
            snprintf(env_file, sizeof(env_file), "%s\\env.txt", jhyy_home);
            FILE *f = fopen(env_file, "r");
            if (f) {
                char line[1024];
                while (fgets(line, sizeof(line), f)) {
                    /* skip comment / blank */
                    const char *p = line;
                    while (*p == ' ' || *p == '\t') p++;
                    if (*p == '#' || *p == '\n' || *p == '\r' || *p == '\0') continue;
                    if (strncmp(p, "JHY_GCC=", 8) != 0) continue;
                    /* p+8 may point into the read-only line buffer; copy to local */
                    char val_buf[1024];
                    snprintf(val_buf, sizeof(val_buf), "%s", p + 8);
                    size_t len = strlen(val_buf);
                    while (len > 0 && (val_buf[len-1] == '\n' || val_buf[len-1] == '\r'))
                        val_buf[--len] = '\0';
                    if (len > 0) {
                        snprintf(jh_gcc_path_buf, sizeof(jh_gcc_path_buf), "%s", val_buf);
                        jh_gcc_path_initialized = 1;
                        fclose(f);
                        return jh_gcc_path_buf;
                    }
                }
                fclose(f);
            }
        }
    }

    /* Priority 3: Windows MSYS2 magic (跟 W-027 v8 同构, 但收敛到 1 处) */
    {
        const char *msys2_magic[] = {
            "C:\\msys64\\ucrt64\\bin\\gcc.exe",
            "C:\\msys64\\mingw64\\bin\\gcc.exe",
            "C:\\msys64\\usr\\bin\\gcc.exe",
            NULL
        };
        for (int i = 0; msys2_magic[i]; i++) {
            if (GetFileAttributesA(msys2_magic[i]) != INVALID_FILE_ATTRIBUTES) {
                snprintf(jh_gcc_path_buf, sizeof(jh_gcc_path_buf), "%s", msys2_magic[i]);
                jh_gcc_path_initialized = 1;
                return jh_gcc_path_buf;
            }
        }
    }

    /* Priority 4: PATH 探测 (Windows API SearchPathA, 比 W-027 v8 用的
       shutil.which / cmd.exe where 稳 — 不依赖 subprocess / encoding) */
    {
        char path_buf[1024];
        unsigned long n = SearchPathA(NULL, "gcc", ".exe", sizeof(path_buf), path_buf, NULL);
        if (n > 0 && n < sizeof(path_buf)) {
            snprintf(jh_gcc_path_buf, sizeof(jh_gcc_path_buf), "%s", path_buf);
            jh_gcc_path_initialized = 1;
            return jh_gcc_path_buf;
        }
    }

    /* Fallback: return "gcc" 走 PATH 解析 (跟 W-027 v8 之前一致; 错误信息保留
       gcc not found → cmd error) */
    snprintf(jh_gcc_path_buf, sizeof(jh_gcc_path_buf), "gcc");
    jh_gcc_path_initialized = 1;
    return jh_gcc_path_buf;
}
#else
/* Linux / macOS: v1.5.6 placeholder (return "gcc" 走 PATH); v2.x sprint 填
   真实多平台探测 (类型 4 升级 + manifest lite 类型 2 注入) */
__attribute__((used)) const char *jh_gcc_path(void) {
    if (jh_gcc_path_initialized) return jh_gcc_path_buf;
    snprintf(jh_gcc_path_buf, sizeof(jh_gcc_path_buf), "gcc");
    jh_gcc_path_initialized = 1;
    return jh_gcc_path_buf;
}
#endif

/* v1.5.6: jh_gcc_invoke — system() 包装, 内部调 jh_gcc_path() 拿 resolved gcc.
   main.jhyy link_with_gcc 改用此函数 (替代裸 system("gcc ...") 拼 cmd_buf).
   ABI: caller 提供 cmd_args (e.g. "ASM_PATH RUNTIME_C HELPERS_C -o EXE -lm"),
   返回写入字节数 (跟 sprintf_lld 同模式); out_buf 至少 2048 字节. */
__attribute__((used)) int jh_gcc_invoke(char *out_buf, int out_size, const char *args) {
    return snprintf(out_buf, (size_t)out_size, "\"%s\" %s", jh_gcc_path(), args);
}

/* v1.5.6 W-048: temp ASCII path helpers — bypass mingw CRT argv decode on
   Chinese filenames. cmd_buf may have UTF-8 bytes (jhyy-side heap) for paths
   from src0 jhyy string literals; mingw-W64 CRT in MSYS2 gcc re-decodes
   Unicode cmdline to ANSI via CP_ACP, producing mojibake argv on PowerShell.
   Solution: feed gcc ASCII-only paths (always correct), copy .s to temp,
   run gcc there, rename output .exe back to original Chinese location.
   All return 0 on success, -1 on failure. Windows-only. */
#ifdef _WIN32
__attribute__((used)) int jh_mktemp_ascii(const char *tag, char *out, int out_cap) {
    char temp_dir[MAX_PATH];
    if (!GetTempPathA(MAX_PATH, temp_dir)) return -1;
    /* pid + tid + static counter for uniqueness within one jhyy invocation.
       8 hex chars = 4 billion combos; collision vanishingly rare. */
    static unsigned int ctr = 0;
    unsigned int seed = (unsigned int)(GetCurrentProcessId() ^ GetCurrentThreadId() ^ ++ctr);
    int n = _snprintf(out, (size_t)out_cap, "%sjh%s%08x.tmp", temp_dir, tag, seed);
    return (n > 0 && n < out_cap) ? 0 : -1;
}

__attribute__((used)) int jh_file_copy(const char *src, const char *dst) {
    wchar_t wsrc[MAX_PATH], wdst[MAX_PATH];
    if (!MultiByteToWideChar(CP_ACP, 0, src, -1, wsrc, MAX_PATH)) return -1;
    if (!MultiByteToWideChar(CP_ACP, 0, dst, -1, wdst, MAX_PATH)) return -1;
    return CopyFileW(wsrc, wdst, FALSE) ? 0 : -1;
}

__attribute__((used)) int jh_rename_file(const char *src, const char *dst) {
    wchar_t wsrc[MAX_PATH], wdst[MAX_PATH];
    if (!MultiByteToWideChar(CP_ACP, 0, src, -1, wsrc, MAX_PATH)) return -1;
    if (!MultiByteToWideChar(CP_ACP, 0, dst, -1, wdst, MAX_PATH)) return -1;
    return MoveFileExW(wsrc, wdst, MOVEFILE_REPLACE_EXISTING) ? 0 : -1;
}

__attribute__((used)) int jh_unlink_file(const char *path) {
    wchar_t wpath[MAX_PATH];
    if (!MultiByteToWideChar(CP_ACP, 0, path, -1, wpath, MAX_PATH)) return -1;
    return DeleteFileW(wpath) ? 0 : -1;
}
#endif /* _WIN32 W-048 */

/* v1.5.6 W-038: jh_run — bypass cmd.exe /C, use CreateProcessA directly.
   cmd.exe /C parses command line and tokenizes by whitespace, so paths with
   spaces (e.g. "C:\Program Files\...") break cmd_run / run_qbe / link_with_gcc.
   CreateProcessA's command-line parser handles quoted paths properly per
   Win32 rules (first token between matching "" is the application name).
   Returns child exit code (0 = success), -1 on failure.
   Linux/macOS: just call system() (POSIX has no cmd.exe issue).

   v1.5.6 W-039: callers (run_qbe, link_with_gcc via jh_gcc_invoke, cmd_run)
   are responsible for wrapping the exe path in quotes. jh_run passes the
   cmd_line through unchanged — callers have the full path context and can
   quote the actual exe path (not just the first whitespace-delimited token,
   which would be wrong for paths with internal whitespace like
   "C:\Program Files\...").

   v1.5.6 W-045: capture child stderr/stdout via anonymous pipe.
   Without this, when bInheritHandles=FALSE the child gets a fresh console
   and its gcc error output bypasses the parent's stderr →  cmd.exe /c '... 2>&1'
   redirect misses the actual error. W-042 echo only shows cmd_buf, no
   gcc error. With pipe capture, jh_run returns exit code AND caller can read
   the captured output via jh_run_get_output(). Caller (link_with_gcc) prints
   captured output on failure. */
#ifdef _WIN32
static char jh_run_outbuf[16384];
static int  jh_run_outlen = 0;
static int  jh_run_outcap = sizeof(jh_run_outbuf);

__attribute__((used)) const char *jh_run_get_output(void) { return jh_run_outbuf; }
__attribute__((used)) int  jh_run_get_output_len(void) { return jh_run_outlen; }

__attribute__((used)) int jh_run(const char *cmd_line) {
    size_t cmd_len = 0;
    while (cmd_line[cmd_len]) cmd_len++;
    char *cmd_buf = (char *)HeapAlloc(GetProcessHeap(), 0, cmd_len + 1);
    if (!cmd_buf) return -1;
    for (size_t i = 0; i <= cmd_len; i++) cmd_buf[i] = cmd_line[i];

    /* v1.5.6 W-046: convert ANSI cmd_buf → UTF-16 for CreateProcessW.
       CreateProcessA relies on CP_ACP (GB2312 on Chinese Windows) to decode
       ANSI bytes → Unicode argv. When caller (PowerShell in UTF-8 mode) sends
       UTF-8 bytes (e.g. "新建文本文档.jhyy"), Windows decodes as GB2312 →
       mojibake Unicode argv → child (gcc) can't find file → silent exit 1.
       CreateProcessW takes UTF-16 directly, bypassing ANSI codepage entirely. */
    int wlen = MultiByteToWideChar(CP_ACP, 0, cmd_buf, -1, NULL, 0);
    if (wlen <= 0) { HeapFree(GetProcessHeap(), 0, cmd_buf); return -1; }
    wchar_t *wbuf = (wchar_t *)HeapAlloc(GetProcessHeap(), 0, wlen * sizeof(wchar_t));
    if (!wbuf) { HeapFree(GetProcessHeap(), 0, cmd_buf); return -1; }
    MultiByteToWideChar(CP_ACP, 0, cmd_buf, -1, wbuf, wlen);

    /* W-045: anonymous pipe to capture child stderr (and stdout). */
    HANDLE hReadPipe = NULL, hWritePipe = NULL;
    SECURITY_ATTRIBUTES sa;
    ZeroMemory(&sa, sizeof(sa));
    sa.nLength = sizeof(sa);
    sa.bInheritHandle = TRUE;
    sa.lpSecurityDescriptor = NULL;
    if (!CreatePipe(&hReadPipe, &hWritePipe, &sa, 0)) {
        HeapFree(GetProcessHeap(), 0, cmd_buf);
        return -1;
    }
    /* Read end must NOT be inherited by child. */
    SetHandleInformation(hReadPipe, HANDLE_FLAG_INHERIT, 0);

    STARTUPINFOW si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    ZeroMemory(&pi, sizeof(pi));
    si.cb = sizeof(si);
    /* v1.5.6 W-050: capture stderr only, inherit stdout/stdin.
       W-045 originally redirected BOTH stdout and stderr to the pipe, which
       swallowed the user program's output ("Hello, world!" etc.) into the
       pipe buffer that no one read. cmd_run (the user-exe invocation) never
       calls jh_run_get_output, so the buffer was discarded silently.
       Capture stderr for gcc/cc1/qbe error diagnostics; let stdout/stdin pass
       through so the user sees the program output and stdin still works for
       interactive programs (dungeon_game etc). */
    si.hStdError = hWritePipe;
    si.hStdOutput = GetStdHandle(STD_OUTPUT_HANDLE);
    si.hStdInput  = GetStdHandle(STD_INPUT_HANDLE);
    si.dwFlags |= STARTF_USESTDHANDLES;

    jh_run_outlen = 0;
    jh_run_outbuf[0] = '\0';

    BOOL ok = CreateProcessW(NULL, wbuf, NULL, NULL, TRUE, 0, NULL, NULL, &si, &pi);
    HeapFree(GetProcessHeap(), 0, wbuf);
    /* Parent no longer needs write end; close so ReadFile can finish. */
    CloseHandle(hWritePipe);
    if (!ok) {
        CloseHandle(hReadPipe);
        HeapFree(GetProcessHeap(), 0, cmd_buf);
        return -1;
    }
    /* Drain pipe into outbuf (until EOF). */
    {
        DWORD avail = 0;
        while (jh_run_outlen + 1 < jh_run_outcap &&
               PeekNamedPipe(hReadPipe, NULL, 0, NULL, &avail, NULL) && avail > 0) {
            DWORD to_read = (DWORD)((jh_run_outcap - 1 - jh_run_outlen));
            if (to_read > avail) to_read = avail;
            DWORD got = 0;
            if (ReadFile(hReadPipe, jh_run_outbuf + jh_run_outlen, to_read, &got, NULL) && got > 0) {
                jh_run_outlen += (int)got;
                jh_run_outbuf[jh_run_outlen] = '\0';
            } else {
                break;
            }
        }
    }
    WaitForSingleObject(pi.hProcess, INFINITE);
    /* Drain any remaining bytes written between last PeekNamedPipe and child exit. */
    {
        DWORD avail = 0;
        while (jh_run_outlen + 1 < jh_run_outcap &&
               PeekNamedPipe(hReadPipe, NULL, 0, NULL, &avail, NULL) && avail > 0) {
            DWORD to_read = (DWORD)((jh_run_outcap - 1 - jh_run_outlen));
            if (to_read > avail) to_read = avail;
            DWORD got = 0;
            if (ReadFile(hReadPipe, jh_run_outbuf + jh_run_outlen, to_read, &got, NULL) && got > 0) {
                jh_run_outlen += (int)got;
                jh_run_outbuf[jh_run_outlen] = '\0';
            } else { break; }
        }
    }
    DWORD exit_code = 0;
    GetExitCodeProcess(pi.hProcess, &exit_code);
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    CloseHandle(hReadPipe);
    HeapFree(GetProcessHeap(), 0, cmd_buf);
    return (int)exit_code;
}
#else
__attribute__((used)) int jh_run(const char *cmd_line) {
    /* POSIX: shell handles quoting correctly */
    return system(cmd_line);
}
#endif
