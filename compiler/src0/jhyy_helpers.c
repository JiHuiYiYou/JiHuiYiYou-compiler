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

#ifdef _WIN32
/* Forward-declare to avoid pulling windows.h (potential name conflicts) */
unsigned long __stdcall GetModuleFileNameA(void *hModule, char *lpFilename, unsigned long nSize);
#endif

/* sprintf_lld：i64 参数 sprintf wrapper（jhyy extern 不能 variadic）。
   Windows x64 ABI 下 i64 和 i32 都走 RCX/RDX/R8/R9 GPR，所以转发安全。
   ir.jhyy 用这个 emit %lld 整数字面量（struct 字段偏移等可能 > INT_MAX）。 */
int sprintf_lld(char *buf, const char *fmt, long long val) {
    return sprintf(buf, fmt, val);
}

/* stderr/stdout 流桥（jhyy 拿不到 FILE* 地址） */
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
    /* dirname × 4: .../compiler/build/bin/jhyy.exe → project root */
    for (int i = 0; i < 4; i++) {
        char *slash = strrchr(exe_path, '/');
        char *bslash = strrchr(exe_path, '\\');
        char *last = slash > bslash ? slash : bslash;
        if (!last) return 1;
        *last = '\0';
    }
    #pragma GCC diagnostic push
    #pragma GCC diagnostic ignored "-Wformat-truncation"
    snprintf(jh_path_qbe_buf,     sizeof(jh_path_qbe_buf),     "%s/qbe/qbe.exe", exe_path);
    snprintf(jh_path_gcc_buf,     sizeof(jh_path_gcc_buf),     "gcc");
    snprintf(jh_path_runtime_buf, sizeof(jh_path_runtime_buf), "%s/compiler/runtime/runtime.c", exe_path);
    snprintf(jh_path_helpers_buf, sizeof(jh_path_helpers_buf), "%s/compiler/src0/jhyy_helpers.c", exe_path);
    #pragma GCC diagnostic pop
    jh_paths_initialized = 1;
    return 0;
}

__attribute__((used)) const char *jh_path_qbe(void)     { return jh_path_qbe_buf; }
__attribute__((used)) const char *jh_path_gcc(void)     { return jh_path_gcc_buf; }
__attribute__((used)) const char *jh_path_runtime(void) { return jh_path_runtime_buf; }
__attribute__((used)) const char *jh_path_helpers(void) { return jh_path_helpers_buf; }
