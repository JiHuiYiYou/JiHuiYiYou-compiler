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
