/* nq — C 参考实现（基准任务的参照系）
 *
 * 与 bench/tasks/nq/task.jhyy 语义等价,stdout 必须逐字相同。
 * 这份源码是 **参照系的参照系** —— 不要在这里做任何"优化" :
 * 两个 twin 必须算法对等,否则比的是"手调过的 C" vs "朴素 jhyy"。
 */
#include <stdio.h>
static int sols = 0;
static int cols[8];
static int N = 7;
void solve(int row) {
    if (row == N) { sols++; return; }
    for (int c = 0; c < N; c++) {
        int ok = 1;
        for (int r2 = 0; r2 < row; r2++) {
            if (cols[r2] == c) { ok = 0; break; }
            if (cols[r2] - c == r2 - row) { ok = 0; break; }
            if (c - cols[r2] == r2 - row) { ok = 0; break; }
        }
        if (ok) { cols[row] = c; solve(row + 1); }
    }
}
int main(void) { solve(0); printf("nqueens(7) = %d (expect 40)\n", sols); return 0; }
