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
