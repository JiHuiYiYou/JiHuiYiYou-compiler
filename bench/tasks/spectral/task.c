/* spectral — C 参考实现（基准任务的参照系）
 *
 * 算法:500×500 稠密矩阵,反复做 y = A·v;t = Aᵀ·y;v = t,20 轮,
 * 最后算 ‖v‖₁。输出**结果的 IEEE-754 位模式**(16 位小写 hex)。
 *
 * ⚠️ 为什么不用 CLBG 的 sin(i*j) 填矩阵:
 *   那样两边都要调 libm 的 sin ⇒ 多一个 libc 依赖,且 sin 的结果在两边
 *   必须逐位相同才可比。改成**纯算术的确定性公式**
 *   ((i*7 + j*13) % 1000) / 7.0 ⇒ 两边建出完全相同的矩阵,
 *   而这道题测的仍然是**稠密矩阵乘向量**这条轴。
 *
 * ⚠️ 浮点求值顺序必须与 jhyy 侧**逐句一致**(浮点加法不可交换)。
 *
 * ⚠️ 这份源码是 **参照系的参照系** —— 不要在这里做任何"优化":
 * 两个 twin 必须算法对等,否则比的是"手调过的 C" vs "朴素 jhyy"。
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define N 500
#define ROUNDS 20

static double a[N * N];

int main(void) {
    /* 确定性填充 */
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            a[i * N + j] = (double)((i * 7 + j * 13) % 1000) / 7.0;
        }
    }

    double *v = (double *)malloc(sizeof(double) * N);
    double *y = (double *)malloc(sizeof(double) * N);
    double *t = (double *)malloc(sizeof(double) * N);
    if (!v || !y || !t) return 1;
    for (int i = 0; i < N; i++) v[i] = 1.0;

    for (int r = 0; r < ROUNDS; r++) {
        /* y = A · v */
        for (int i = 0; i < N; i++) {
            double s = 0.0;
            for (int j = 0; j < N; j++) s += a[i * N + j] * v[j];
            y[i] = s;
        }
        /* t = Aᵀ · y */
        for (int j = 0; j < N; j++) {
            double s = 0.0;
            for (int i = 0; i < N; i++) s += a[i * N + j] * y[i];
            t[j] = s;
        }
        memcpy(v, t, sizeof(double) * N);
    }

    double sum = 0.0;
    for (int i = 0; i < N; i++) sum += (v[i] < 0 ? -v[i] : v[i]);

    unsigned long long bits;
    memcpy(&bits, &sum, 8);
    printf("%016llx\n", bits);
    return 0;
}
