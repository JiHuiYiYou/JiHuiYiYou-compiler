/* mandelbrot — C 参考实现（基准任务的参照系）
 *
 * 算法:200×200 网格上跑曼德博集合迭代,输出**迭代计数**的
 * (总和, 异或) —— 而不是经典的 ASCII 图。
 *
 * ⚠️ 为什么输出校验和而不是 ASCII 图:
 *   jhyy 产物的 stdout 是**无缓冲**的(runtime.c 的 setvbuf(_IONBF))
 *   ⇒ 大量输出会退化成 syscall 瓶颈,测的就不是代码生成了。
 *   ⇒ 本套件所有题目一律"内部算完,只打印一个 checksum"。
 *
 * ⚠️ 浮点求值顺序必须与 jhyy 侧**逐句一致**(浮点加法不可交换)。
 *   gcc 默认目标 x86-64 **没有 FMA 指令** ⇒ 不会把 a*b+c 合成 FMA
 *   ⇒ -O0/-O1/-O2 三档的浮点结果逐位相同。
 *   (bench.py 另加 -ffp-contract=off 当护栏 —— jhyy 后端也发不出 FMA。)
 *
 * ⚠️ 这份源码是 **参照系的参照系** —— 不要在这里做任何"优化":
 * 两个 twin 必须算法对等,否则比的是"手调过的 C" vs "朴素 jhyy"。
 */
#include <stdio.h>
int main(void) {
    int w = 600, h = 600, max_iter = 100;
    long long sum = 0;
    int xacc = 0;
    for (int y = 0; y < h; y++) {
        double ci = ((double)y - (double)h / 2.0) * 2.0 / (double)h;
        for (int x = 0; x < w; x++) {
            double cr = ((double)x - (double)w / 2.0) * 2.0 / (double)w;
            double zr = 0.0, zi = 0.0;
            int i = 0;
            for (; i < max_iter; i++) {
                double x2 = zr * zr;
                double y2 = zi * zi;
                if (x2 + y2 > 4.0) break;
                zi = 2.0 * zr * zi + ci;
                zr = x2 - y2 + cr;
            }
            sum += i;
            xacc ^= i;
        }
    }
    printf("%lld %d\n", sum, xacc);
    return (int)(sum & 0xff);
}
