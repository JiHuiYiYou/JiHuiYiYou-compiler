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
#include <io.h>       // _open/_close/_read/_write (W-103 std_os_* libc bridge)
#include <fcntl.h>    // O_BINARY / O_CREAT ... (W-103)
#else
#include <fcntl.h>    // open / O_* (W-103 std_os_* libc bridge)
#include <unistd.h>   // close / read / write (W-103)
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

/* v4.0.4 Step 1 (W-101 RCA 1-iter verification, per feedback_rca_first_root_cause):
   jh_dbg_log2 — 5-arg structured logging bridge for jhyy-side codegen tracing.
   Captures W-101 smoking gun: cg_record_temp_slot / cg_offset_for_temp_with_target
   / cg_state_reset_for_function / emit_func_header 时序. 4 i64 values cover all
   sites: (fn_idx, temp_id, slot_off, recorded_or_offset_or_size). label disambiguates
   site via short tag. fflush(stderr) 保证 SEGV 段前 stderr buffer 真 flush。 */
__attribute__((used)) int jh_dbg_log2(const char *label, long long a, long long b, long long c, long long d) {
    int n = fprintf(stderr, "[W101DBG] %s fn=%lld t=%lld slot=%lld extra=%lld\n",
                   label, a, b, c, d);
    fflush(stderr);
    return n;
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

/* v2.11.19 Phase 3a: 把 f64 字面量文本转 IEEE 754 bit pattern (i64)。
   jhyy-side cg_parse_f64_imm_bits 用此走 fractional (N.M) 分支 — 自己解析
   i64 literal 表只 cover integer-valued d_N (0/1/2/3/4/5/10),d_1.5/d_2.5/d_3.14
   等 fractional 全 fallback 0 → 自-backend 的算术结果错 (QBE constant-folding 闭环)。
   C 端 atof → 强转 bits,jhyy-side 拿 i64 bit pattern → emit movabsq $bits, %rax +
   movq %rax, -<off>(%rbp)。
   注:Win64 ABI f64 return 用 XMM0,jhyy extern 不能直接接 f64 — 用 store 模式:
   本函数把解析后的 bits 写到 caller 提供的 8-byte buffer,jhyy-side 读 i64 出来。
   abi/i386 SysV 同 pattern (XMM0 return) — jhyy-side 拿 8-byte heap buf,本函数写回。 */
long long jh_double_to_bits(const char *s, long long len, void *out_buf) {
    char buf[128];
    long long n = len < 127 ? len : 127;
    for (long long i = 0; i < n; i++) buf[i] = s[i];
    buf[n] = '\0';
    double d = atof(buf);
    *(long long *)out_buf = *(long long *)&d;
    return 0;
}

/* v2.11.19 Phase 3a: 把 f32 字面量文本转 IEEE 754 single-precision bit pattern (i32)。
   jhyy-side cg_f32_imm_bits 用此走 true impl (替代 v2.11.15 Iter 1b stub "返 imm_val")。
   store 模式同 jh_double_to_bits:caller 提供 4-byte buf,本函数写回 i32 bits。 */
int jh_float_to_bits(const char *s, long long len, void *out_buf) {
    char buf[128];
    long long n = len < 127 ? len : 127;
    for (long long i = 0; i < n; i++) buf[i] = s[i];
    buf[n] = '\0';
    float f = (float)atof(buf);
    *(int *)out_buf = *(int *)&f;
    return 0;
}

/* v1.7.1 patch A1 — W-042 Tier 3: post-link .exe stat check.
   链接成功 (jh_run 返回 0) 后, stat exe_path 验文件存在且 size > 0.
   抓 gcc "succeeded" 但 produce 0 字节 / missing 文件的 silent corruption case.
   W-042 Tier 1+2 已 ship (Tier 1: invoke_buf echo; Tier 2: stderr pipe capture via W-045).
   Tier 3 是最后一段, ship 后 → W-042 RESOLVED. */
int jh_file_stat_ok(const char *path) {
    struct stat st;
    if (stat(path, &st) != 0) return 0;
    if (!S_ISREG(st.st_mode)) return 0;
    return st.st_size > 0 ? 1 : 0;
}

/* v1.7.0 Stage 5：parse_expr prefix_float 解析 `2.5f32` / `2.5f64` 后缀。
   返回 PRIM_F32 (8) / PRIM_F64 (9), 无后缀或无法识别返回 PRIM_F64 (default)。
   Mirror jh_int_suffix_prim pattern. */
int jh_float_suffix_prim(const char *s, long long len) {
    for (long long i = 0; i < len; i++) {
        char c = s[i];
        if (c == 'f') {
            int bits = 0;
            long long j = i + 1;
            while (j < len && s[j] >= '0' && s[j] <= '9') {
                bits = bits * 10 + (s[j] - '0');
                j++;
            }
            switch (bits) {
                case 32: return 8;  /* PRIM_F32 */
                case 64: return 9;  /* PRIM_F64 */
            }
            return 9;  /* fallback PRIM_F64 */
        }
    }
    return 9;  /* no suffix → PRIM_F64 */
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
   - jh_paths_init(argv0) 一次: argv[0] 推项目根, 填 3 个 static buffer
     (gcc / runtime.c / jhyy_helpers.c)
   - jh_path_*() 多次读: 返回 const char* 到 static buffer
   ABI: argv0=*u8(i64 ptr), 返回 i32 (=0 OK / !=0 err)
   与 main.c compute_project_root 镜像 (C 端不调这个 fn, jhyy 端才调)。

   v4.0.0: QBE 完全移除。QBE_PATH() / jh_path_qbe() 保留 extern linkage 返
   回空字符串(永不调),以便 caller signature 不变。Path probing 只针对
   runtime.c + jhyy_helpers.c (Layout (a) installer 兄弟 vs Layout (b) source-
   tree walk-up)。GCC 路径默认 "gcc" (PATH 解析)。

   详见 docs/internal/build.md "QBE 历史" 段 + docs/plans/v2/v4.0.0-plan.md。 */
static char jh_path_qbe_buf[1024];  /* unused post-v4.0.0; empty string */
static char jh_path_gcc_buf[1024];
static char jh_path_runtime_buf[1024];
static char jh_path_helpers_buf[1024];
static char jh_path_stdlib_buf[1024];  /* W-103: std lib 模块目录 */
static char jh_path_icon_buf[1024];    /* W-127: JHYY "J" 图标 (.ico) */
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
    } else {
        if (!argv0) return 1;
        snprintf(exe_path, sizeof(exe_path), "%s", argv0);
        /* W-127 (v4.0.20): argv[0] 绝对化。
         *
         * 为什么必须:从**相对**路径调用编译器时(make 里的
         * `compiler/build/bin/_boot_anchor.exe` 就是相对路径),推出来的
         * root 是相对的 —— 走到盘根时 root 变成空串,于是
         * jh_path_icon 变成 "\installer\assets\icons\jhyy-icon.ico"。
         * 以反斜杠开头的路径在 Windows 上是「当前**盘**的根目录」,不是
         * 「当前目录」⇒ 永远找不到 ⇒ 图标被静默跳过。
         *
         * 这不只是图标路径的问题:jh_path_runtime / jh_path_helpers /
         * jh_path_stdlib 同样是「相对 root」推出来的,一律带这个坑。
         * 一次绝对化把整类问题消掉。
         */
        {
            char full[MAX_PATH];
            DWORD fl = GetFullPathNameA(exe_path, (DWORD)sizeof(full), full, NULL);
            if (fl > 0 && fl < sizeof(full)) {
                snprintf(exe_path, sizeof(exe_path), "%s", full);
            }
        }
    }
#else
    {
        if (!argv0) return 1;
        snprintf(exe_path, sizeof(exe_path), "%s", argv0);
    }
#endif

    /* v1.5.6 W-037: layout detection (取代 v1.4.1 hardcoded dirname × 4).
       原 bug: dirname × 4 假设 jhyy.exe 在 <root>\compiler\build\bin\ (源码树),
       但 installer layout 是 <INSTALLDIR>\bin\jhyy.exe (只有 1 层), dirname × 4
       走到 C:\ → qbe/qbe.exe 找不到 → "QBE failed". 用户 VSCode 通过 PATH
       调 installer 版 jhyy.exe (PATH 排第一) 时 100% 触发.
       v4.0.0: QBE 移除, probing 目标改为 jhyy_helpers.c (Layout (a) 兄弟 vs
       Layout (b) source-tree walk-up),runtime.c 同 pattern。 */

    /* Normalize path: ensure backslashes for consistent parsing */
    for (char *p = exe_path; *p; p++) if (*p == '/') *p = '\\';

    /* Extract directory containing jhyy.exe */
    char *last = strrchr(exe_path, '\\');
    if (!last) return 1;
    *last = '\0';
    snprintf(dir_path, sizeof(dir_path), "%s", exe_path);

    /* GCC: default to "gcc" (PATH-resolved by gcc/jh_run). Always set. */
    snprintf(jh_path_gcc_buf, sizeof(jh_path_gcc_buf), "gcc");
    /* jh_path_qbe_buf: empty string (post-v4.0.0 QBE removed). */
    jh_path_qbe_buf[0] = '\0';

    /* Layout (a) — installer: runtime.c + jhyy_helpers.c as siblings of jhyy.exe */
    snprintf(test_path, sizeof(test_path), "%s\\jhyy_helpers.c", dir_path);
    {
        struct stat st;
        if (stat(test_path, &st) == 0) {
            #pragma GCC diagnostic push
            #pragma GCC diagnostic ignored "-Wformat-truncation"
            snprintf(jh_path_runtime_buf, sizeof(jh_path_runtime_buf), "%s\\runtime.c", dir_path);
            snprintf(jh_path_helpers_buf, sizeof(jh_path_helpers_buf), "%s\\jhyy_helpers.c", dir_path);
            /* W-103: installer 把 src0/std 下的 .jhyy 模块装到 <bin>/std/ */
            snprintf(jh_path_stdlib_buf, sizeof(jh_path_stdlib_buf), "%s\\std", dir_path);
            /* W-127: installer 把 jhyy-icon.ico 装到 <bin>\ (wxs 的 JhyyIconFile
               组件)。自举链接路径靠它把 "J" 图标嵌进每一个链出来的 exe ——
               v4.0.8 把 jhyy.exe 的产出改到自举编译器后,这条链断了
               (icon 逻辑原本只在 C 侧 compiler/src/main.c 里)。 */
            snprintf(jh_path_icon_buf, sizeof(jh_path_icon_buf), "%s\\jhyy-icon.ico", dir_path);
            #pragma GCC diagnostic pop
            jh_paths_initialized = 1;
            return 0;
        }
    }

    /* Layout (b) — source-tree: walk up to find <root>\compiler\src0\jhyy_helpers.c */
    snprintf(root, sizeof(root), "%s", dir_path);
    for (int i = 0; i < 8; i++) {
        snprintf(test_path, sizeof(test_path), "%s\\compiler\\src0\\jhyy_helpers.c", root);
        {
            struct stat st;
            if (stat(test_path, &st) == 0) {
                #pragma GCC diagnostic push
                #pragma GCC diagnostic ignored "-Wformat-truncation"
                snprintf(jh_path_runtime_buf, sizeof(jh_path_runtime_buf), "%s\\compiler\\runtime\\runtime.c", root);
                snprintf(jh_path_helpers_buf, sizeof(jh_path_helpers_buf), "%s\\compiler\\src0\\jhyy_helpers.c", root);
                snprintf(jh_path_stdlib_buf, sizeof(jh_path_stdlib_buf), "%s\\compiler\\src0\\std", root);
                /* W-127: 源码树布局 —— 图标源在 installer/assets/icons/。
                   (installer/build.ps1 会把同一个 .ico 拷进安装包的 bin\) */
                snprintf(jh_path_icon_buf, sizeof(jh_path_icon_buf),
                         "%s\\installer\\assets\\icons\\jhyy-icon.ico", root);
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
    return 1;  /* no layout matched — runtime.c / jhyy_helpers.c not found */
}

/* W-103 (2026-10-20): std lib 模块目录 —— `import <mod>;` 在 main 文件旁边
   找不到 <mod>.jhyy 时,回落到这里找(<root>/compiler/src0/std/ 或 <bin>/std/)。
   这是 std lib 第一次真正**可被用户代码 import**(之前 std 目录下的 .jhyy 只是源码,
   任何用户程序都够不着 —— 测试全靠 inline 副本,而副本给 mock 背书)。 */
__attribute__((used)) const char *jh_path_stdlib(void) { return jh_path_stdlib_buf; }

__attribute__((used)) const char *jh_path_qbe(void)     { return jh_path_qbe_buf; }  /* v4.0.0: always "" */
__attribute__((used)) const char *jh_path_gcc(void)     { return jh_path_gcc_buf; }
__attribute__((used)) const char *jh_path_runtime(void) { return jh_path_runtime_buf; }
__attribute__((used)) const char *jh_path_helpers(void) { return jh_path_helpers_buf; }

/* W-127 (v4.0.20): JHYY "J" 图标 (.ico) 的绝对路径。
   空串 = 本布局下没有图标资源(自举链接路径据此**跳过**嵌图标,而不是编不出来)。
   两处布局各自在 jh_paths_init 里填:installer = <bin>\jhyy-icon.ico,
   源码树 = <root>\installer\assets\icons\jhyy-icon.ico。 */
__attribute__((used)) const char *jh_path_icon(void) { return jh_path_icon_buf; }

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

/* W-127 (v4.0.20): windres 的路径 —— 用来把 "J" 图标编成 RT_ICON 资源。
 *
 * windres 与 gcc 来自**同一个** mingw-w64 工具链(都在 binutils 里),所以从
 * 已解析出的 gcc 路径**推**出 windres.exe 最稳:gcc 在
 * C:\msys64\ucrt64\bin\gcc.exe ⇒ windres 就在同一个目录。
 * 推不出来(比如 JHY_GCC 指向一个没有同名 windres 的地方)就退回 "windres",
 * 交给 PATH 解析 —— 跟 gcc 的 fallback 同款。
 */
__attribute__((used)) const char *jh_path_windres(void) {
    static char buf[1024];
    if (buf[0] != '\0') return buf;
    const char *gcc = jh_gcc_path();
    const char *slash = strrchr(gcc, '\\');
    if (slash != NULL && slash != gcc) {
        int dlen = (int)(slash - gcc);
        snprintf(buf, sizeof(buf), "%.*s\\windres.exe", dlen, gcc);
#ifdef _WIN32
        if (GetFileAttributesA(buf) != INVALID_FILE_ATTRIBUTES) return buf;
#endif
    }
    snprintf(buf, sizeof(buf), "windres");
    return buf;
}

/* W-127 (v4.0.20): 路径里的 '\' → '/'。
 *
 * windres 读 .rc 时走 gcc -E 预处理,而 gcc -E 把 '\' 当转义符 —— 所以 .rc
 * 里的路径必须写正斜杠(C 侧 compiler/src/main.c:507-509 踩过同一个坑,
 * 那边的注释写的是「用 path_to_fwd() 让前导反斜杠变成正斜杠」)。
 *
 * 为什么这个 helper 放在 C 侧而不是 .jhyy 里:jhyy 语言**没有 1 字节标量
 * 类型**,字节级改写只能借 *i32,而那是 **4 字节**的存 —— 写一个字节会把
 * 后面 3 个字节连带清成 NUL,直接把路径截断。(实测确认:*i32 存法是 4 字节,
 * 见 v4.0.20 的 W-127 记录。)所以这类逐字节活儿一律留在 C 侧。
 */
__attribute__((used)) int jh_path_to_fwd(char *p) {
    if (!p) return -1;
    for (; *p; p++) if (*p == '\\') *p = '/';
    return 0;
}

/* W-127 (v4.0.20): 把 jh_mktemp_ascii 产出的 4 字节 ".tmp" 尾巴换成给定后缀。
 * 后缀 ≤ 4 字节;短于 4 的部分补 NUL( ".tmp" → ".ico" / ".rc" / ".o" )。
 * 同样因为「jhyy 没有 1 字节标量」而留在 C 侧。
 */
__attribute__((used)) int jh_set_tmp_suffix(char *p, const char *suffix) {
    if (!p || !suffix) return -1;
    size_t n = strlen(p);
    if (n < 4) return -1;
    size_t sl = strlen(suffix);
    if (sl > 4) return -1;
    char *base = p + (n - 4);
    memcpy(base, suffix, sl);
    for (size_t i = sl; i < 4; i++) base[i] = '\0';
    return 0;
}

/* W-132 (v4.0.20): 图标资源对象的生命周期。
   jh_gcc_invoke 构造链接命令时把它建出来并记在这里;jh_run 在子进程结束后
   把它删掉(链接期间需要,之后就是垃圾)。 */
static char g_jh_icon_obj[1024];

__attribute__((used)) void jh_icon_obj_store(const char *p) {
    if (!p) { g_jh_icon_obj[0] = '\0'; return; }
    snprintf(g_jh_icon_obj, sizeof(g_jh_icon_obj), "%s", p);
}

/* jh_build_icon_obj 定义在本文件后面(它要用 jh_mktemp_ascii / jh_set_tmp_suffix /
   jh_path_to_fwd),这里前置声明。 */
__attribute__((used)) int jh_build_icon_obj(char *out_obj, int out_cap);

/* v1.5.6: jh_gcc_invoke — system() 包装, 内部调 jh_gcc_path() 拿 resolved gcc.
   main.jhyy link_with_gcc 改用此函数 (替代裸 system("gcc ...") 拼 cmd_buf).
   ABI: caller 提供 cmd_args (e.g. "ASM_PATH RUNTIME_C HELPERS_C -o EXE -lm"),
   返回写入字节数 (跟 sprintf_lld 同模式); out_buf 至少 2048 字节.

   W-132 (v4.0.20): **图标资源对象从这里进链接行**。

   为什么挂钩在 C 侧、而不是在 main.jhyy 的 link_with_gcc 里加几行:
   给 main.jhyy **新增任何局部变量**都会移位模块级 temp 编号 ⇒ 自举产物
   的**行为**会漂移(实测:main_jhyy 里那段 argv 扫描的 `movzbl (%r8)` 1 字节读
   被整条丢掉 ⇒ `--target=` 不再被识别 ⇒ "cannot open file" ⇒ 6 个 sysv
   cross 用例全红)。详见 workarounds.md 的「自举产物行为漂移」那条。

   **⇒ 结论:这条链上的改动一律不进 main.jhyy。** 本函数是链接命令的构造点,
   正好是 C 侧能插手而不动 .jhyy 的位置。 */
__attribute__((used)) int jh_gcc_invoke(char *out_buf, int out_size, const char *args) {
    char ico_obj[1024];
    int ico_rc = jh_build_icon_obj(ico_obj, (int)sizeof(ico_obj));
    if (ico_rc == 0) {
        /* 图标对象插在 .s 前面 —— gcc/mingw 的 .o 顺序无关,放前面便于
           在链接命令里一眼看见它。jh_run 会在子进程结束后把它删掉。 */
        jh_icon_obj_store(ico_obj);
        {
            int n = snprintf(out_buf, (size_t)out_size, "\"%s\" \"%s\" %s",
                             jh_gcc_path(), ico_obj, args);
            if (getenv("JHY_ICON_TRACE")) {
                /* 每进程打印一次完整链接行(排查用,默认安静)。
                   「图标 .o 到底在不在链接行里」必须能一眼看见。 */
                static int reported = 0;
                if (!reported) {
                    reported = 1;
                    fprintf(stderr, "W-132: link line = %s\n", out_buf);
                }
            }
            return n;
        }
    }
    if (ico_rc < 0) {
        /* 失败 = **响亮地**让链接失败,而不是静默产出一个没图标的 exe。
           (v4.0.8 之后图标就是这样一路静到用户在 Explorer 里看见白板。) */
        fprintf(stderr, "W-132: icon embedding failed — 链接将失败\n");
        return snprintf(out_buf, (size_t)out_size,
                        "\"%s\" \"__jhyy_icon_obj_missing__\" %s",
                        jh_gcc_path(), args);
    }
    /* ico_rc == 1:本布局没有图标资源(例如裁剪过的安装)⇒ 跳过,不算错。 */
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
/* W-123 (2026-10-20):临时文件名的唯一性。
 *
 * 原来的 seed = `pid ^ tid ^ ++ctr`,注释写「collision vanishingly rare」——
 * **那个结构会规律性地撞**:
 *
 *   Windows 的 process id 与主线程 thread id 来自**同一个全局计数器**
 *   ⇒ 常见形态是 (pid, tid) = (N, N+1) ⇒ N ^ (N+1) = 1(N 为偶数时)
 *   ⇒ 每两个并发进程里就有一对的 seed **完全相同** ⇒ 两个并发编译抢同一个
 *   临时文件名 ⇒ 后一个的 rename 失败 ⇒ **编译失败**。
 *
 * 实测(2026-10-20):并发编译 32 个文件 → **4 个失败**,报
 *   「W-048: rename temp exe failed (kept at ...\Temp\jhe0000000e.exe)」
 * —— 两次失败的临时文件名**一字不差**(`0000000e` = seed 14 = 1 ^ 15)。
 *
 * 这也是台账里那些「全量里偶发 compile failed、单跑必绿」的 flake 的真凶
 * (2026-10-18 记的 W-106 现象:「删掉 workaround 后 cap_table_basic 偶发
 * compile failed」—— 与本条是**同一个 bug**,跟那个 workaround 无关)。
 *
 * 修法两件事:
 *   1. 换掉裸 XOR —— 用**乘法混合**(Knuth multiplicative hash)把
 *      pid / tid / 计数器 / 毫秒时钟揉成一个 32 位值;
 *   2. **真的独占创建一次**(CREATE_NEW)—— 名字真被占了就让内核拒绝,
 *      换一组 hash 重试(最多 8 次)。这样「唯一」由文件系统保证,
 *      不再依赖「hash 撞的概率很小」这种推理 ✓。
 */
__attribute__((used)) int jh_mktemp_ascii(const char *tag, char *out, int out_cap) {
    char temp_dir[MAX_PATH];
    if (!GetTempPathA(MAX_PATH, temp_dir)) return -1;
    static unsigned int ctr = 0;
    for (int attempt = 0; attempt < 8; attempt++) {
        unsigned int h = (unsigned int)GetCurrentProcessId();
        h = h * 2654435761u;
        h = h ^ ((unsigned int)GetCurrentThreadId() * 2246822519u);
        h = h + (unsigned int)GetTickCount64();
        h = h * 2654435761u;
        h = h ^ (++ctr * 3266489917u);
        int n = _snprintf(out, (size_t)out_cap, "%sjh%s%08x.tmp", temp_dir, tag, h);
        if (n <= 0 || n >= out_cap) return -1;
        /* 独占创建:名字真被占了 → CreateFile 失败 → 换一组 hash 再试 */
        HANDLE fh = CreateFileA(out, GENERIC_WRITE, 0, NULL, CREATE_NEW,
                                FILE_ATTRIBUTE_TEMPORARY, NULL);
        if (fh != INVALID_HANDLE_VALUE) {
            CloseHandle(fh);
            return 0;
        }
    }
    return -1;
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
    /* W-132: 链接结束(图标资源对象只在**链接期间**需要)⇒ 删掉它。
       只在「这条命令确实带了图标对象」时删 —— jh_run 还被 windres 和用户程序
       复用,不能误删别人的文件。 */
    if (g_jh_icon_obj[0] != '\0' && strstr(cmd_line, g_jh_icon_obj) != NULL) {
        DeleteFileA(g_jh_icon_obj);
        g_jh_icon_obj[0] = '\0';
    }
    HeapFree(GetProcessHeap(), 0, cmd_buf);
    return (int)exit_code;
}
#else
__attribute__((used)) int jh_run(const char *cmd_line) {
    /* POSIX: shell handles quoting correctly */
    return system(cmd_line);
}
#endif

/* v2.4.0: jh_setenv — set env var in current process. On Windows this uses
   SetEnvironmentVariableA so the value is in the Win32 env block that
   CreateProcessW inherits (NULL env block → child gets parent's env). On
   POSIX, setenv. Used by main.jhyy:link_with_gcc to fix SOURCE_DATE_EPOCH
   for D26 byte-equal reproducibility. Returns 0 on success, non-zero on
   failure. */
#ifdef _WIN32
__attribute__((used)) int jh_setenv(const char *name, const char *value) {
    if (name == NULL || value == NULL) return 1;
    return SetEnvironmentVariableA(name, value) ? 0 : 1;
}
#else
#include <stdlib.h>
__attribute__((used)) int jh_setenv(const char *name, const char *value) {
    if (name == NULL || value == NULL) return 1;
    return setenv(name, value, 1);
}
#endif

/* v2.5.0: jh_getenv — read env var from current process. Returns a pointer
   to the value string (in the Win32 env block or POSIX environ) on success,
   or NULL if the var is not set. Caller does NOT free the returned pointer.
   Used by main.jhyy:run_backend to honor QBE_FALLBACK=1 env var for
   emergency QBE baseline rollback (per L4 § 1.4). */
#ifdef _WIN32
__attribute__((used)) const char *jh_getenv(const char *name) {
    if (name == NULL) return NULL;
    return getenv(name);
}
#else
__attribute__((used)) const char *jh_getenv(const char *name) {
    if (name == NULL) return NULL;
    return getenv(name);
}
#endif

/* v2.6.1: jh_regalloc_get / jh_regalloc_set — regalloc module-level global
   moved from jhyy-side `let mut g_regalloc_arr` (compiler/src0/codegen_amd64_
   regalloc.jhyy:79) to C-side static. The jhyy-side `let mut` was the only
   module-level mutable state in src0; when `inline_imports` in main.jhyy
   merged the codegen_amd64 import chain, sema Pass 1 (sema.jhyy:1820-1857)
   doesn't handle NODE_LET at module scope → stage0 segfault during compile.
   Moving global state to C-side static sidesteps the issue and matches the
   existing pattern for jh_setenv / jh_getenv. The static is zero-initialized
   at process start (BSS), so regalloc_clear_global() = jh_regalloc_set(NULL). */
static void *g_jh_regalloc_arr = (void *)0;
__attribute__((used)) void *jh_regalloc_get(void) {
    return g_jh_regalloc_arr;
}
__attribute__((used)) int jh_regalloc_set(void *arr) {
    g_jh_regalloc_arr = arr;
    return 0;
}

/* v2.11.5 (W-074.7 alloc-tracking 真修): jh_cgstate_get_temp_slots /
   jh_cgstate_set_temp_slots — 跟 regalloc 同 pattern,C-side static 装当前 CGState
   的 temp_slot_for_id (256-entry i64 array,per-fn alloc slot 表)。
   emit_alloc 写入 alloc'd %tN 的 slot,cg_offset_for_temp[t] 查表(否则 fall through
   formula)。BSS-zero init, set NULL = 关闭 alloc-tracking。Pointer-only: 实际数据
   在 jhyy arena alloc (per-compile lifetime),C-side 只装指针。
   修 nested_struct_deep + struct_val_pass pre-existing bug: alloc'd %tN 之前
   走 formula `-(32 + t*8)` 跟 alloc 真分配的 slot 不一致 → read garbage。 */
static void *g_jh_cgstate_temp_slots = (void *)0;
__attribute__((used)) void *jh_cgstate_get_temp_slots(void) {
    return g_jh_cgstate_temp_slots;
}
__attribute__((used)) int jh_cgstate_set_temp_slots(void *arr) {
    g_jh_cgstate_temp_slots = arr;
    return 0;
}

/* v2.11.8 (W-074.7.8 derived-address tracking 真修): jh_cgstate_get_holds_address /
   jh_cgstate_set_holds_address — same pattern as temp_slots above; C-side static
   holds 256-entry u8 bitmap (parallel to temp_slot_for_id i64 array, but 1 byte/entry)。
   emit_alloc / emit_binop (add/sub on address-holder src1) / emit_copy (TEMP→TEMP of
   address-holder) 写 flag; emit_load/store/loadsub 读 flag 决定 indirect
   (mov<size> (%r8), %reg) vs slot (mov<size> -<off>(%rbp), %reg) dispatch。
   BSS-zero init; query goes through (*s).temp_holds_address in state.jhyy (hot path);
   setter is forward-ref-safe no-op kept for API consistency with temp_slots. */
static void *g_jh_cgstate_holds_address = (void *)0;
/* W-130 (2026-10-24 真修):bitmap 的**实际容量**。
   C 侧以前只能自己猜容量(硬编码 65536),而 jhyy 侧已经按实际 max temp id
   动态扩容(cg_resize_temp_tables)⇒ 两边脱节 ⇒ temp_id >= 65536 的
   address-holder 标记写不进去、读不出来 ⇒ emit_loadsub 退化成 slot direct
   path ⇒ 静默产出错代码(详见 workarounds.md W-130)。
   现在容量**从 jhyy 侧同步过来**,C 侧不再有任何硬编码上界。 */
static long long g_jh_cgstate_holds_cap = 0;
__attribute__((used)) void *jh_cgstate_get_holds_address(void) {
    return g_jh_cgstate_holds_address;
}
/* jh_cgstate_set_holds_table — **原子**地装 bitmap 指针 + 容量。
   单个 C 函数 ⇒ 不存在「cap 已更新 / bitmap 还是旧的」的中间窗口。
   jhyy 侧唯一入口:cg_state_set_holds_address (codegen_amd64_state.jhyy)。 */
__attribute__((used)) int jh_cgstate_set_holds_table(void *bitmap, long long cap) {
    if (bitmap == NULL) return -1;
    if (cap <= 0) return -1;
    g_jh_cgstate_holds_address = bitmap;
    g_jh_cgstate_holds_cap = cap;
    return 0;
}
__attribute__((used)) long long jh_cgstate_get_holds_cap(void) {
    return g_jh_cgstate_holds_cap;
}

/* v4.0.2.2 (W-096 emit-side per-fn-local counter 真修): jh_cgstate_get_state /
   jh_cgstate_set_state — expose current CGState pointer so cg_offset_for_temp
   + cg_local_t_from_global (no state parameter) can read per_fn_base_t[cur_fn_idx]
   做 global t → local t 翻译。Setter 在 cg_state_init 入口调一次 (per-compile
   lifetime),getter hot-path 读。Pattern 跟 jh_cgstate_get_temp_slots 一致
   (C-side static BSS-zero init)。 */

static void *g_jh_cgstate_state = (void *)0;
__attribute__((used)) void *jh_cgstate_get_state(void) {
    return g_jh_cgstate_state;
}
__attribute__((used)) int jh_cgstate_set_state(void *s) {
    g_jh_cgstate_state = s;
    return 0;
}

/* v3.2.4 (W-093 真修 W-092 derived-address bitmap 1024 → 4096):
   jh_cgstate_set_holds_flag / jh_cgstate_get_holds_flag — byte-level access into
   the bitmap. 256 → 1024 (W-090 std_vec_basic max 513) → 4096 (W-093 big_test
   max 1932) → 65536 (v4.0.2.1 W-074.6 sub-bug #3, main.jhyy max 60462)。
   main.jhyy 多 fn + 多 alloc + 多 pointer-arith → max temp_id = 60462, 跨过 4096
   → bounds check no-op → emit_load/store 走 slot direct path → argv[0] deref
   `(*argv_arr)` 退化成 copy → SEGV on any input。
   cg_record_temp_holds_address / cg_is_address_holder (state.jhyy) 调这两个,
   因为 jhyy 没有 u8 direct deref 语法 (*(u8*)p = 1 不支持),走 C-bridge。

   ⚠️ W-130 (2026-10-24):65536 这个硬编码上限**第二次**撞悬崖。
   state.jhyy 侧已按实际 max temp id 动态扩容(cg_resize_temp_tables),
   边界检查也用动态的 state.temp_holds_size ⇒ C 侧再按 65536 判界就脱节了。
   真修:容量从 jhyy 侧经 jh_cgstate_set_holds_table 同步过来,C 侧无硬编码上界。 */
/* W-130:越界 / 容量通道未初始化 / 指针不同步 → 返回**哨兵 -1**。
   ⚠️ get 侧返 0 会被 jhyy 侧当成「这个 temp 不是 address-holder」⇒
   emit_loadsub 走 slot direct path ⇒ **静默产出错代码**。所以必须是 -1。 */
__attribute__((used)) int jh_cgstate_set_holds_flag(void *bitmap, long long idx) {
    if (bitmap == NULL) return -1;
    if (g_jh_cgstate_holds_cap <= 0) return -1;              /* 容量通道未初始化 */
    if (bitmap != g_jh_cgstate_holds_address) return -1;     /* 指针不同步 */
    if (idx < 0 || idx >= g_jh_cgstate_holds_cap) return -1; /* 越界 */
    ((unsigned char *)bitmap)[idx] = 1;
    return 0;
}
__attribute__((used)) int jh_cgstate_get_holds_flag(void *bitmap, long long idx) {
    if (bitmap == NULL) return -1;
    if (g_jh_cgstate_holds_cap <= 0) return -1;
    if (bitmap != g_jh_cgstate_holds_address) return -1;
    if (idx < 0 || idx >= g_jh_cgstate_holds_cap) return -1;
    return ((unsigned char *)bitmap)[idx] != 0 ? 1 : 0;
}

/* v2.6.0: jh_read_file — read entire file into caller-provided buffer.
   Returns:
     0  on success (*out_len set to file size)
    -1  on error (NULL args, file open / read failure)
     1  if file larger than buf_cap (caller should grow + retry)
   Caller owns buf (pre-malloc'd by caller, may be reused across calls).
   No CRLF translation: file opened in binary mode (CreateFileW on Windows,
   fopen("rb") on POSIX). This matches the existing pattern in
   compiler/src0/main.jhyy read_file (fopen "rb") and per
   feedback_qbe_crlf_root_cause: all IL/binary-derived files must use
   "rb"/"wb" / CreateFileW to avoid \n → \r\n conversion on Windows.
   Used by codegen_amd64.jhyy:read_file to replace jhyy-side fopen/fseek/ftell
   (V2-B v2.6.0 I/O consolidation). */
#ifdef _WIN32
__attribute__((used)) int jh_read_file(const char *path, void *out_buf, long long buf_cap, long long *out_len) {
    if (path == NULL || out_buf == NULL || out_len == NULL) return -1;
    wchar_t wpath[MAX_PATH];
    if (!MultiByteToWideChar(CP_ACP, 0, path, -1, wpath, MAX_PATH)) return -1;
    HANDLE h = CreateFileW(wpath, GENERIC_READ, FILE_SHARE_READ, NULL,
                           OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (h == INVALID_HANDLE_VALUE) return -1;
    LARGE_INTEGER fs;
    if (!GetFileSizeEx(h, &fs)) { CloseHandle(h); return -1; }
    long long sz = (long long)fs.QuadPart;
    if (sz > buf_cap) { CloseHandle(h); return 1; }
    DWORD got = 0;
    BOOL ok = ReadFile(h, out_buf, (DWORD)sz, &got, NULL);
    CloseHandle(h);
    if (!ok || (long long)got != sz) return -1;
    *out_len = sz;
    return 0;
}
#else
__attribute__((used)) int jh_read_file(const char *path, void *out_buf, long long buf_cap, long long *out_len) {
    if (path == NULL || out_buf == NULL || out_len == NULL) return -1;
    FILE *fp = fopen(path, "rb");
    if (fp == NULL) return -1;
    if (fseek(fp, 0, SEEK_END) != 0) { fclose(fp); return -1; }
    long long sz = (long long)ftell(fp);
    if (sz < 0) { fclose(fp); return -1; }
    if (fseek(fp, 0, SEEK_SET) != 0) { fclose(fp); return -1; }
    if (sz > buf_cap) { fclose(fp); return 1; }
    size_t got = fread(out_buf, 1, (size_t)sz, fp);
    fclose(fp);
    if ((long long)got != sz) return -1;
    *out_len = sz;
    return 0;
}
#endif

/* v2.6.0: jh_write_file — write buf to file (binary mode, no CRLF).
   Returns 0 on success, -1 on failure.
   Used by codegen_amd64.jhyy:write_file to replace jhyy-side fopen/fwrite
   (V2-B v2.6.0 I/O consolidation). */
#ifdef _WIN32
__attribute__((used)) int jh_write_file(const char *path, const void *buf, long long len) {
    if (path == NULL || buf == NULL || len < 0) return -1;
    wchar_t wpath[MAX_PATH];
    if (!MultiByteToWideChar(CP_ACP, 0, path, -1, wpath, MAX_PATH)) return -1;
    HANDLE h = CreateFileW(wpath, GENERIC_WRITE, 0, NULL,
                           CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (h == INVALID_HANDLE_VALUE) return -1;
    DWORD wrote = 0;
    BOOL ok = WriteFile(h, buf, (DWORD)len, &wrote, NULL);
    CloseHandle(h);
    if (!ok || (long long)wrote != len) return -1;
    return 0;
}
#else
__attribute__((used)) int jh_write_file(const char *path, const void *buf, long long len) {
    if (path == NULL || buf == NULL || len < 0) return -1;
    FILE *fp = fopen(path, "wb");
    if (fp == NULL) return -1;
    size_t wrote = fwrite(buf, 1, (size_t)len, fp);
    fclose(fp);
    if ((long long)wrote != len) return -1;
    return 0;
}
#endif

/* V3-B fix (V2-A wire build break): V2-A wired run_qbe → run_backend in
 * main.jhyy which references `extern fn codegen_amd64_run` (V2-A A5 stub
 * in src0/codegen_amd64.jhyy). The jhyy-side stub is not imported into
 * main.jhyy (single-file compile path: jhyy_stage0 compiles only main.jhyy,
 * codegen_amd64.jhyy never inlined), so the C linker must resolve this
 * symbol from jhyy_helpers.c. Returns non-zero so run_backend falls back
 * to QBE (per L4 § 1.4 QBE_FALLBACK design). Filled in V2-B v2.6.0 when
 * codegen_amd64.parse_and_emit stub is implemented. */
__attribute__((used)) int codegen_amd64_run(const char *il_path, const char *asm_path) {
    (void)il_path; (void)asm_path;
    return -1;  /* not implemented in C side; triggers QBE fallback */
}

/* v4.0.7 (W-097 闭环根因): cg_byte_at 的 C 侧字节读取。
 * jhyy 侧原本用 ptr_add_u8(s, i) 再解引用, 而 ptr_add_u8 的返回 temp 能否
 * 间接加载取决于它是否被标成 address-holder —— 那个标记又来自
 * cg_query_fn_returns_ptr("ptr_add_u8") -> hash_string_n -> cg_byte_at, 构成
 * 循环依赖: 首次进入时标记尚未建立, cg_byte_at 退化成"读指针值低字节", 哈希全错,
 * 标记永远建不起来 (实测 self-backend 少标 1028 个 address-holder)。
 * 这里直接按指针读字节, 完全不经过 ptr_add_u8 / address-holder 机制, 切断循环。 */
__attribute__((used)) int jh_byte_at(const void *p, long long i) {
    return ((const unsigned char *)p)[i];
}

/* v4.0.7 (W-097 闭环根因): 函数名后缀匹配。
 * QBE IL 里的调用名是 mangled 的 (util__ptr_add_u8 / arena__arena_alloc ...),
 * 而 builtin 指针函数清单是未 mangled 的 (ptr_add_u8)。之前在 jhyy 侧做偏移比较,
 * 又依赖 ptr_add_u8 的 address-holder 标记 —— 与 cg_query_fn_returns_ptr 循环依赖。
 * 放到 C 侧一次性比较, 完全绕开 jhyy 指针运算。 */
__attribute__((used)) int jh_name_ends_with(const char *name, long long len,
                                             const char *suffix, long long slen) {
    if (len < slen || slen <= 0) return 0;
    return memcmp(name + (len - slen), suffix, (size_t)slen) == 0 ? 1 : 0;
}

/* ══════════════════════════════════════════════════════════════════════════
   W-103 (2026-10-20 真修): std_os_* 的真 libc bridge
   ══════════════════════════════════════════════════════════════════════════
   std/os.jhyy 的 std_os_open / close / read / write / exit 之前**全是 M0 mock**
   (恒返 fd=42、恒返 n、进程不退出)。M0 的理由是 W-079「QBE amd64_win mixed
   (l,w,w) extern args bug」—— QBE 随 v4.0.0 完全移除,self-backend 不再经过
   QBE,那个理由早已失效(W-079 翻 RESOLVED 时只修了 std_io 那一半,std_os 这半
   没人动过,见 workarounds.md W-103 的 RCA)。

   签名跟 std/os.jhyy 的 std_os_* **1:1 对齐**,jhyy 侧零宽度转换:
     jh_os_open (const char*, int, int)                 -> long long
     jh_os_close(long long)                             -> int
     jh_os_read (long long, void*, long long)           -> long long
     jh_os_write(long long, const void*, long long)    -> long long
     jh_os_exit (int)                                   -> void

   ⚠️ 方向张力(必记):这 5 个 bridge 让 jhyy 程序**又依赖 C runtime**,与 M5
   「删 C runtime / 0-C 闭环」方向相反。取舍 + 卸载路径见 workarounds.md
   W-103「方向张力」段:真要 0-C 时,换掉的是这 5 个 bridge 的**实现**
   (改成 syscall / kernel call),jhyy 侧的 std_os_* 一行都不用动。

   Windows 用 _open/_close/_read/_write(msvcrt);POSIX 用 open/close/read/write。

   ⚠️ **两边的 O_* 常量值不一样** —— std/os.jhyy 里写死的是 **POSIX 值**
   (O_CREAT 0x40 / O_EXCL 0x80 / O_APPEND 0x400 / O_TRUNC 0x200),
   而 Windows 的 _O_* 是 (_O_CREAT **0x100** / _O_EXCL 0x400 /
   _O_APPEND **0x8** / _O_TRUNC 0x200)—— **只有 TRUNC 两边同值**。
   所以下面有一层 jh_os_translate_flags() 逐位翻译;POSIX 侧原样透传。

   ⚠️ 这条翻译的存在本身说明 M0 mock 藏了一个真 bug:mock 从不调 open(2),
   所以 POSIX 的 O_CREAT=64 拿到 Windows 上(0x40 = _O_NOINHERIT)恒错,
   而且错法很隐蔽 —— 文件不存在 + 没 O_CREAT → ENOENT → fd=-1,
   看起来像「路径不对」而不是「flag 值不对」。

   Windows 侧无条件 OR 上 _O_BINARY —— jhyy 的 std_os_* 是**字节**语义
   (POSIX 风格),不强制 binary 的话 CRT 会做 CRLF↔LF 转换,字节级往返就废了。 */

#ifdef _WIN32
#define JH_OS_OPEN  _open
#define JH_OS_CLOSE _close
#define JH_OS_READ  _read
#define JH_OS_WRITE _write
#else
#define JH_OS_OPEN  open
#define JH_OS_CLOSE close
#define JH_OS_READ  read
#define JH_OS_WRITE write
#endif

/* 单次 syscall 的字节上限 —— POSIX 的 read/write 允许部分完成,
   这里循环到读满 n / 写满 n / EOF 为止,语义跟 POSIX 一致。 */
#define JH_OS_CHUNK 0x7ffff000LL

/* POSIX-style open flags -> 平台 flags。
   Windows(_O_*,<fcntl.h>): _O_CREAT 0x100 / _O_EXCL 0x400 / _O_APPEND 0x8 /
   _O_TRUNC 0x200。POSIX(<fcntl.h>): O_CREAT 0x40 / O_EXCL 0x80 /
   O_APPEND 0x400 / O_TRUNC 0x200。**只有 TRUNC 两边同值**,其余全不同。
   std/os.jhyy 里写死的是 POSIX 值(它的注释写着「跟 fcntl.h 一致」),
   所以翻译必须发生在桥这一层 —— jhyy 侧保持 POSIX 语义,平台差异不外泄。

   ⚠️ 这条翻译的存在本身说明 M0 mock 藏了一个真 bug:mock 从不调 open(2),
   所以 POSIX 的 O_CREAT=64 拿到 Windows 上(0x40 = _O_NOINHERIT)恒错,
   而且错法很隐蔽:文件不存在 + 没 O_CREAT -> ENOENT -> fd=-1,
   看起来像「路径不对」而不是「flag 值不对」。 */
static int jh_os_translate_flags(int flags) {
#ifdef _WIN32
    int out = flags & 0x3;             /* O_RDONLY / O_WRONLY / O_RDWR */
    if (flags & 0x40) out |= 0x100;    /* POSIX O_CREAT  -> _O_CREAT  */
    if (flags & 0x80) out |= 0x400;    /* POSIX O_EXCL   -> _O_EXCL   */
    if (flags & 0x200) out |= 0x200;   /* POSIX O_TRUNC  -> _O_TRUNC  */
    if (flags & 0x400) out |= 0x8;     /* POSIX O_APPEND -> _O_APPEND */
    out |= 0x8000;                    /* _O_BINARY —— 字节语义,不做 CRLF 转换 */
    return out;
#else
    return flags;
#endif
}

__attribute__((used)) long long jh_os_open(const char *path, int flags, int mode) {
    if (path == NULL) return -1;
    return (long long)JH_OS_OPEN(path, jh_os_translate_flags(flags), mode);  /* -1 on failure */
}

__attribute__((used)) int jh_os_close(long long fd) {
    if (fd < 0) return -1;
    return JH_OS_CLOSE((int)fd) == 0 ? 0 : -1;
}

__attribute__((used)) long long jh_os_read(long long fd, void *buf, long long n) {
    if (fd < 0 || buf == NULL) return -1;
    if (n <= 0) return 0;
    unsigned char *p = (unsigned char *)buf;
    long long total = 0;
    while (total < n) {
        long long chunk = n - total;
        if (chunk > JH_OS_CHUNK) chunk = JH_OS_CHUNK;
        long long got = (long long)JH_OS_READ((int)fd, p + total, (unsigned int)chunk);
        if (got < 0) return total > 0 ? total : -1;
        if (got == 0) break;              /* EOF */
        total += got;
    }
    return total;
}

__attribute__((used)) long long jh_os_write(long long fd, const void *buf, long long n) {
    if (fd < 0 || buf == NULL) return -1;
    if (n <= 0) return 0;
    const unsigned char *p = (const unsigned char *)buf;
    long long total = 0;
    while (total < n) {
        long long chunk = n - total;
        if (chunk > JH_OS_CHUNK) chunk = JH_OS_CHUNK;
        long long put = (long long)JH_OS_WRITE((int)fd, p + total, (unsigned int)chunk);
        if (put < 0) return total > 0 ? total : -1;
        if (put == 0) break;
        total += put;
    }
    return total;
}

/* exit() 而不是 _exit():前者 flush stdio 缓冲 —— jhyy 程序的 printf 输出
   必须在进程退出前落盘,否则「写完日志再退出」会丢最后一段。 */
__attribute__((used)) void jh_os_exit(int code) {
    exit(code);
}

/* ════════════════════════════════════════════════════════════════════════════
 * W-132 (v4.0.20): 把 JHYY "J" 图标编成 RT_ICON 资源对象,给链接行用
 * ════════════════════════════════════════════════════════════════════════════
 *
 * 背景:嵌图标的 windres 步骤原本**只在 C 侧**有(compiler/src/main.c:503-558)。
 * v4.0.8(commit 1dc6a23, 2026-10-16)把 jhyy.exe 的产出从 C 侧编译器改到
 * **自举编译器**,而自举侧一行图标逻辑都没有 ⇒ 从那以后:
 *   · 每个 jhyy.exe 都不带 RT_ICON 资源
 *     ⇒ installer 的 FileAssoc(DefaultIcon = jhyy.exe,0)取不到图标
 *     ⇒ **所有 .jhyy 文件在 Explorer 里是白板**(见 W-131);
 *   · 用户用 jhyy.exe **编出来的每个程序**也没有 J 图标
 *     (v1.8.1 的原意是两者都带,见 compiler/src/jhyy.rc 的注释)。
 *
 * 为什么整个做在 C 侧、.jhyy 侧只留一次调用:
 *   ① jhyy 语言**没有 1 字节标量类型** —— `*i32` 存是 **4 字节**(实测:
 *      往 *i32 写 0x41 之后按 i32 读回来是 0x414141),逐字节的活儿(路径
 *      '\' → '/'、换临时文件后缀)在 .jhyy 里做会把相邻 3 字节连带清成 NUL
 *      ⇒ 路径直接被截断;
 *   ② 跟 C 侧 main.c:503-558 的既有做法同构(那边也是 windres + 链 .ico.o),
 *      两边行为一致,不会一个能一个不能。
 *
 * 三个**实测**出来的约束(踩过才知道的):
 *   ① windres 的 -i / -o 路径**必须用正斜杠** —— windres 走 gcc -E 预处理,
 *      而 gcc -E 把 '\' 当转义符:`C:\Users\x.rc` → `C:Usersx.rc`,
 *      报 "No such file or directory"。.rc 里那个 ICON 路径同样要正斜杠。
 *   ② .ico 要先拷到**纯 ASCII** 临时路径 —— mingw CRT 的 argv 走 CP_ACP,
 *      中文路径会变 mojibake(W-048 同款)。
 *   ③ SOURCE_DATE_EPOCH 必须在 windres **之前**设好 —— windres 会把 .o 的
 *      时间戳写进去,不固定就破坏 D26 逐字节可复现(同 gcc 那条一样)。
 *
 * 返回:0 = 成功(out_obj 里是 .ico.o 的路径 —— caller 负责在链接后 unlink)
 *      1 = 跳过(本布局没有图标资源 —— 不算错)
 *     -1 = 失败(caller 必须报错退出)
 */
__attribute__((used)) int jh_build_icon_obj(char *out_obj, int out_cap) {
#ifdef _WIN32
    const char *icon_path = jh_path_icon();
    if (!icon_path || icon_path[0] == '\0') {
        fprintf(stderr, "W-132: no icon source path (layout not detected) — 跳过嵌图标\n");
        return 1;
    }
    {
        struct stat st;
        if (stat(icon_path, &st) != 0 || st.st_size <= 0) {
            /* 不静默跳过:「为什么没图标」这件事必须看得见
               (v4.0.8 之后图标一路静到用户在 Explorer 里看见白板)。 */
            fprintf(stderr, "W-132: icon source not found at %s — 跳过嵌图标\n",
                    icon_path);
            return 1;
        }
    }

    char tmp_ico[1024], tmp_rc[1024], tmp_obj[1024];
    if (jh_mktemp_ascii("i", tmp_ico, (int)sizeof(tmp_ico)) != 0) return -1;
    if (jh_mktemp_ascii("r", tmp_rc, (int)sizeof(tmp_rc)) != 0) {
        DeleteFileA(tmp_ico); return -1;
    }
    if (jh_mktemp_ascii("o", tmp_obj, (int)sizeof(tmp_obj)) != 0) {
        DeleteFileA(tmp_ico); DeleteFileA(tmp_rc); return -1;
    }
    if (jh_set_tmp_suffix(tmp_ico, ".ico") != 0 ||
        jh_set_tmp_suffix(tmp_rc, ".rc") != 0 ||
        jh_set_tmp_suffix(tmp_obj, ".o") != 0) {
        DeleteFileA(tmp_ico); DeleteFileA(tmp_rc); DeleteFileA(tmp_obj);
        return -1;
    }
    /* ① windres 的路径必须是正斜杠(见上面的约束 ①) */
    jh_path_to_fwd(tmp_ico);
    jh_path_to_fwd(tmp_rc);
    jh_path_to_fwd(tmp_obj);

    /* ② .ico 拷到 ASCII 临时路径(约束 ②) */
    if (jh_file_copy(icon_path, tmp_ico) != 0) {
        DeleteFileA(tmp_ico); DeleteFileA(tmp_rc); DeleteFileA(tmp_obj);
        return -1;
    }

    /* .rc 现场生成 —— 不依赖仓库里的 compiler/src/jhyy.rc(那份用相对路径指向
       installer/assets/icons/,在 installer 布局下根本不存在)。 */
    char rcbuf[1024];
    int rn = snprintf(rcbuf, sizeof(rcbuf), "IDI_ICON1 ICON \"%s\"\n", tmp_ico);
    if (rn <= 0 || rn >= (int)sizeof(rcbuf)) {
        DeleteFileA(tmp_ico); DeleteFileA(tmp_rc); DeleteFileA(tmp_obj);
        return -1;
    }
    if (jh_write_file(tmp_rc, rcbuf, (long long)rn) != 0) {
        DeleteFileA(tmp_ico); DeleteFileA(tmp_rc); DeleteFileA(tmp_obj);
        return -1;
    }

    /* ③ SOURCE_DATE_EPOCH 必须在 windres 之前设好(约束 ③) */
    SetEnvironmentVariableA("SOURCE_DATE_EPOCH", "1234567890");

    char cmd[3072];
    snprintf(cmd, sizeof(cmd), "\"%s\" -i \"%s\" -O coff -o \"%s\"",
             jh_path_windres(), tmp_rc, tmp_obj);
    /* 用 jh_run(CreateProcessA)而不是 system():cmd.exe /c 遇到**以引号开头**的
       命令行会把外层引号吃掉(经典坑),报「文件名或目录名语法不正确」。
       CreateProcessA 自己解析 quoted path,路径带空格也安全(W-038 同款理由)。
       C 侧 main.c:522 用的是 system() —— 那边的 windres 是 PATH 解析的裸名
       (不以引号开头),所以没踩到这个坑;这里用的是绝对路径,必须走 jh_run。 */
    int rc = jh_run(cmd);
    DeleteFileA(tmp_ico);
    DeleteFileA(tmp_rc);
    if (rc != 0) {
        const char *out = jh_run_get_output();
        if (out && out[0]) {
            fprintf(stderr, "W-132: windres failed: %s\n", out);
        } else {
            fprintf(stderr, "W-132: windres failed (exit=%d)\n", rc);
        }
        DeleteFileA(tmp_obj);
        return -1;
    }
    if ((int)strlen(tmp_obj) >= out_cap) { DeleteFileA(tmp_obj); return -1; }
    snprintf(out_obj, (size_t)out_cap, "%s", tmp_obj);
    if (getenv("JHY_ICON_TRACE")) {
        /* 每进程打印一次:图标 .o 确实进了链接行(「加没加」必须看得见)。
           默认安静 —— 设 JHY_ICON_TRACE=1 才出声(排查用)。 */
        static int reported = 0;
        if (!reported) {
            reported = 1;
            fprintf(stderr, "W-132: icon resource object added to link line: %s\n",
                    tmp_obj);
        }
    }
    return 0;
#else
    /* POSIX: 没有 PE / DefaultIcon 这回事 —— 跳过(不算错) */
    (void)out_obj; (void)out_cap;
    return 1;
#endif
}
