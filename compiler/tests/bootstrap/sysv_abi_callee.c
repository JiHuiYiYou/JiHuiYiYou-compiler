/* sysv_abi_callee.c — W-104 跨实现 ABI 对拍的 gcc 侧
 *
 * 按**真正的 SysV ABI** 接收一个 `{int, double}` struct:
 *   SysV § A.2/A.3:struct 按 eightbyte 切分 —— INTEGER(rdi) + SSE(xmm0)。
 *   gcc 生成的代码实测:
 *       movl %edi, %eax        ; i_field ← rdi
 *       movq %xmm0, %rdx       ; d_field ← xmm0
 *
 * W-104 存在时 jhyy 传的是**一个指针**(rdi=struct 地址),这里读到的是
 * 地址的低 32 位当 i_field、xmm0 是垃圾 —— 结果错开,退出码不是 44。
 *
 * 期望:44 = 41 + 3。
 */

struct Mixed {
    int i_field;
    double d_field;
};

int gcc_take(struct Mixed m) { return m.i_field + (int)m.d_field; }
