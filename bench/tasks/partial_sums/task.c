/* partial_sums — C 参考实现（基准任务的参照系）
 *
 * 算法:10 000 段 × 1 000 项 = 10 000 000 次迭代的整数部分和。
 * 每一段的和用 (j * 17 + 23) % 1000 生成 —— **纯确定性、无随机数**,
 * 所以两个 twin 不需要共享任何 PRNG 状态。
 *
 * 这道题测的是**纯整数代码生成**:不碰浮点、不碰堆、不碰 libc 之外的东西
 * ⇒ 是整套题里"最接近纯 jhyy 代码生成"的那一道(对照项)。
 *
 * ⚠️ 这份源码是 **参照系的参照系** —— 不要在这里做任何"优化":
 * 两个 twin 必须算法对等,否则比的是"手调过的 C" vs "朴素 jhyy"。
 */
#include <stdio.h>
int main(void) {
    long long total = 0;
    for (int i = 0; i < 20000; i++) {
        long long sum = 0;
        for (int j = 0; j < 1000; j++)
            sum += (long long)((j * 17 + 23) % 1000);
        total += sum;
    }
    printf("%lld\n", total);
    return 0;
}
