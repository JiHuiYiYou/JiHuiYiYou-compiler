/* revcomp — C 参考实现（基准任务的参照系）
 *
 * 算法:1 000 000 字节的确定性序列 → **反转** → **按位取反** → 两个校验和。
 *
 * ⚠️ 为什么不用 CLBG 的"读文件 / 互补碱基"那一套:
 *   jhyy 产物的 stdout 是**无缓冲**的 ⇒ 大量输出会退化成 syscall 瓶颈;
 *   文件 IO 又落在 libc 上 ⇒ 测的就不是代码生成。
 *   ⇒ 这里把输入改成**内部确定性生成**,输出改成**一个 checksum**。
 *
 * ⚠️ 随机数是**自带的 xorshift32** —— 不用 libc 的 rand(),
 *   否则两边的序列依赖各自 libc 的实现 ⇒ 输出不可比。
 *
 * ⚠️ 无符号溢出是**定义行为**(回绕)⇒ C 的 uint32_t/uint64_t 与 jhyy 的
 *   u32/u64 语义一致 ⇒ 两边逐位相同。
 *
 * ⚠️ 这份源码是 **参照系的参照系** —— 不要在这里做任何"优化":
 * 两个 twin 必须算法对等,否则比的是"手调过的 C" vs "朴素 jhyy"。
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

#define N 4000000

int main(void) {
    unsigned char *buf = (unsigned char *)malloc(N);
    if (buf == NULL) return 1;

    /* xorshift32 —— 确定性填充 */
    uint32_t s = 123456789u;
    for (int i = 0; i < N; i++) {
        s ^= s << 13;
        s ^= s >> 17;
        s ^= s << 5;
        buf[i] = (unsigned char)(s & 0xffu);
    }

    /* 反转 */
    for (int i = 0; i < N / 2; i++) {
        unsigned char t = buf[i];
        buf[i] = buf[N - 1 - i];
        buf[N - 1 - i] = t;
    }

    /* 取反 + 两个校验和(总和 + FNV-1a) */
    uint64_t sum = 0;
    uint64_t h = 1469598103934665603ull;
    for (int i = 0; i < N; i++) {
        buf[i] = (unsigned char)(255u - (unsigned)buf[i]);
        sum += (uint64_t)buf[i];
        h ^= (uint64_t)buf[i];
        h *= 1099511628211ull;
    }

    printf("%llu %016llx\n", sum, h);
    return 0;
}
