/* ack — C 参考实现（基准任务的参照系）
 *
 * 与 bench/tasks/ack/task.jhyy 语义等价,stdout 必须逐字相同。
 * 这份源码是 **参照系的参照系** —— 不要在这里做任何"优化" :
 * 两个 twin 必须算法对等,否则比的是"手调过的 C" vs "朴素 jhyy"。
 */
#include <stdio.h>
int A(int m, int n) {
    if (m == 0) return n + 1;
    if (n == 0) return A(m - 1, 1);
    return A(m - 1, A(m, n - 1));
}
int main(void) { printf("A(3, 8) = %d\n", A(3, 8)); return 0; }
