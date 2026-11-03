/* binary_trees — C 参考实现（基准任务的参照系）
 *
 * 算法:建一棵深度 14 的满二叉树(2^15 - 1 = 32 767 个节点),
 * 算校验和(所有节点的 count 之和),再整棵释放掉。
 *
 * ⚠️ **节点布局必须与 jhyy 侧逐字节一致**:
 *   C:    struct { ptr, ptr, int }  ⇒ 偏移 0 / 8 / 16,sizeof = 24
 *   jhyy: type Node = struct { left: *u8, right: *u8, count: i32 }
 *         ⇒ jhyy 侧用 sizeof(Node) 分配、按硬编码偏移 0/8/16 写字段。
 *   ⇒ 若两边布局不一致,校验和就会不同 ⇒ **stdout 比对当场抓住**。
 *
 * ⚠️ 这道题**部分在测 libc**:malloc / free 是 ucrt64 的。
 *   ⇒ task.meta 的 libc 字段标 malloc;对外发布时逐题标注。
 *
 * ⚠️ 这份源码是 **参照系的参照系** —— 不要在这里做任何"优化":
 * 两个 twin 必须算法对等,否则比的是"手调过的 C" vs "朴素 jhyy"。
 */
#include <stdio.h>
#include <stdlib.h>

struct node { struct node *left, *right; int count; };

static struct node *build(int depth) {
    if (depth == 0) return NULL;
    struct node *n = (struct node *)malloc(sizeof(struct node));
    if (n == NULL) return NULL;
    n->count = 1;
    n->left = build(depth - 1);
    n->right = build(depth - 1);
    return n;
}
static int check(struct node *n) {
    if (n == NULL) return 0;
    int l = check(n->left);
    int r = check(n->right);
    return n->count + l + r;
}
static void free_tree(struct node *n) {
    if (n == NULL) return;
    free_tree(n->left);
    free_tree(n->right);
    free(n);
}
int main(void) {
    struct node *root = build(20);
    int sum = check(root);
    free_tree(root);
    printf("%d\n", sum);
    return sum & 0xff;
}
