/* nbody — C 参考实现（基准任务的参照系）
 *
 * 算法:5 个天体、500 000 步的引力推进,最后算总能量。
 * 输出**总能量的 IEEE-754 位模式**(16 位小写 hex)。
 *
 * ⚠️ 为什么输出位模式而不是十进制:
 *   jhyy 的 std::fmt **没有浮点格式化器** ⇒ 比不了十进制渲染。
 *   ⇒ 两边都把 f64 的 8 个字节当成 u64 打出来 ⇒ 逐字节可比。
 *   (C 侧用 memcpy + %016llx;jhyy 侧用 `&v as *u64` 指针别名 —— 实测一致。)
 *
 * ⚠️ 浮点求值顺序必须与 jhyy 侧**逐句一致**(浮点加法不可交换)。
 *   gcc 默认目标 x86-64 **没有 FMA 指令** ⇒ 不会把 a*b+c 合成 FMA
 *   ⇒ -O0/-O1/-O2 三档的浮点结果逐位相同。
 *
 * ⚠️ **sqrt 走的是 libm** ⇒ 这道题**部分在测 libc**(见 task.meta 的 libc 字段)。
 *
 * ⚠️ 这份源码是 **参照系的参照系** —— 不要在这里做任何"优化":
 * 两个 twin 必须算法对等,否则比的是"手调过的 C" vs "朴素 jhyy"。
 */
#include <stdio.h>
#include <string.h>
#include <math.h>

#define NB 5
#define NITER 500000

static const double init[NB][3] = {
    { 0.0, 0.0, 0.0 },
    { 4.84143144246472090, -1.16032004402742839, -0.103622044471123109 },
    { 8.34336671824457995,  4.12479856412430479, -0.403523417114321381 },
    { 13.0893263579460364, -10.0577350393348644, -0.301768379276131318 },
    { 16.9153415756894381, -8.79858571390527485,  0.651424232260967689 }
};

int main(void) {
    double b[NB][3];
    memcpy(b, init, sizeof(init));

    for (int it = 0; it < NITER; it++) {
        for (int i = 0; i < NB; i++) {
            for (int j = i + 1; j < NB; j++) {
                double dx = b[i][0] - b[j][0];
                double dy = b[i][1] - b[j][1];
                double dz = b[i][2] - b[j][2];
                double d2 = dx * dx + dy * dy + dz * dz;
                double mag = 0.01 / (d2 * sqrt(d2));
                b[i][0] -= dx * mag; b[i][1] -= dy * mag; b[i][2] -= dz * mag;
                b[j][0] += dx * mag; b[j][1] += dy * mag; b[j][2] += dz * mag;
            }
        }
    }

    double e = 0.0;
    for (int i = 0; i < NB; i++) {
        for (int j = i + 1; j < NB; j++) {
            double dx = b[i][0] - b[j][0];
            double dy = b[i][1] - b[j][1];
            double dz = b[i][2] - b[j][2];
            e += dx * dx + dy * dy + dz * dz;
        }
    }
    e *= 0.5;

    unsigned long long bits;
    memcpy(&bits, &e, 8);
    printf("%016llx\n", bits);
    return 0;
}
