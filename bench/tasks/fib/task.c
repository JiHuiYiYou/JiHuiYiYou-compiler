/* fib — C 参考实现（基准任务的参照系）
 *
 * 与 bench/tasks/fib/task.jhyy 语义等价,stdout 必须逐字相同。
 * 这份源码是 **参照系的参照系** —— 不要在这里做任何"优化" :
 * 两个 twin 必须算法对等,否则比的是"手调过的 C" vs "朴素 jhyy"。
 */
#include <stdio.h>
int fib(int n) { if (n < 2) return n; return fib(n-1) + fib(n-2); }
int main(void) { printf("fib(35) %% 1000000 = %d\n", fib(35) % 1000000); return 0; }
