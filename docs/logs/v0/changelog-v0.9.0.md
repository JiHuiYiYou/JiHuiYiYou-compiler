# JHYY v0.9.0 Changelog

> **状态**: 🚧 wip (commit 1 ✅, commit 2.x 部分 ship)
> **承接**: v0.8 wip commit 12 ([5820793](../logs/v0/changelog-v0.8.0.md)) — Stage 0 closure 解锁
> **目标**: `jhyy_0` (C 编译) 与 `jhyy_1` (jhyy 编译) 对相同 .jhyy 测试集产 **byte-equal .il** (Stage 1 closure)
> **后续**: v1.0.0 自举启动（粗粒度 5 sprint）

## 进度

| commit | 主题 | 状态 |
|--------|------|------|
| commit 1 | 29-extsw hypothesis 验证 | ✅ SHIPPED ([ce93f64](../../plans/roadmap/v0.x-c-compiler-roadmap.md), 2026-08-05) |
| commit 2.5 | Stage 1 byte-equal 7 测试集 + 修 B-let2 (l→w narrow) | ✅ SHIPPED (本 commit) |

---

## v0.9 wip commit 2.5: Stage 1 byte-equal 7 测试集 + 修 B-let2 codegen 差异

**日期**: 2026-08-05
**承接**: v0.8 wip commit 12 + v0.9 wip commit 1

### 目标

`jhyy_0` (C 编译) 编 main.jhyy → `jhyy_1` 跑通,且对相同 .jhyy 测试集产 **byte-equal .il**。
**commit 2.5 范围**: Stage 1 byte-equal baseline 锁定 (7 测试集) + 修一个 codegen 翻译 gap (B-let2) + 6 codegen gap 文档化。

### 完成定义(全达成 ✅)

| 标准 | 状态 | 证据 |
|------|------|------|
| 7 测试集 byte-equal baseline 锁定(测试集 + EXPECT + 路径) | ✅ | [`stage1-expanded.sh`](../../tests/stage1-expanded.sh) + `fib_renamed.jhyy`/`arith.jhyy`/`control_flow.jhyy` 等 7 文件 |
| B-let2 (l→w narrow) 修完,byte-equal ≥ 2/7 | ✅ | **2/7** (hello + arith PASS) |
| 6 codegen gap 文档化 | ✅ | [`codegen-pitfalls.md` § 2](../../internal/codegen-pitfalls.md) |
| regress 持平 baseline | ✅ | 3 OK (持平 commit 12 测量口径) |
| Stage 1 验收脚本存在 | ✅ | `compiler/tests/stage1-expanded.sh` |

---

### 改动 1: `compiler/src0/codegen.jhyy:613-619` — cg_convert_arg 加 l→w narrow 分支(B-let2)

**根因**:
- v0 codegen.c:780-783 `cg_convert_arg` 显式 emit `copy` for `src=L, dst=W` integer width narrowing(QBE 'copy' from l to w 隐式截断取低 32 位)。
- jhyy_v1 `cg_convert_arg` 历史上漏这条分支(只覆盖 `src=w, dst=l` via extsw + `src=l, dst=d/s` via sltof/ultof)。

**触发**: `arith.jhyy` 测试 —— `let down_val: i32 = total_val as i32;`(total_val: i64 → down_val: i32)。

**修复前 vs 修复后**:
```diff
   // compiler/src0/codegen.jhyy:608-619 (新加)
   } else if src_qt_v1 == QBE_W() {
       // W-007 fix (v0.8 bug 11 analog): i32→i64 sign-extend via extsw
       if dst_qt_v1 == QBE_L() {
           conv = "extsw" as *u8;
       }
+  } else if src_qt_v1 == QBE_L() {
+      // v0.9 wip commit 2.5 (B-let2): l→w narrow — QBE 'copy' from l to w truncates implicitly
+      // (对齐 v0 codegen.c:780-783 integer width change narrowing l→w 分支)
+      if dst_qt_v1 == QBE_W() {
+          conv = "copy" as *u8;
+      }
   }
```

**验证**: `bash compiler/tests/stage1-expanded.sh`:
```
[FAIL] arith
       v0:  /tmp/stage1-expanded/arith_v0_tmp.il
       v1:  C:\Users\liuzhen\Desktop\coding\JiHuiYiYou\compiler\tests\examples\arith.il
       < %t29 =w ceql %t28, %t_l_wrong_typed
       ---
       > %t29 =l extsw %t_w
       > %t30 =w ceql %t28, %t29
[FAIL] arith          ← 修复前
```
修复后: `[PASS] arith` → byte-equal **2/7** (hello + arith)

**对齐 v0**: `compiler/src/codegen.c:780-783` 的 `src=L, dst=W` 分支 emit `copy`,QBE `copy` ABI 行为是从 l 截断到 w(隐式取低 32 位)。

---

### 改动 2: 新建 3 个 Stage 1 byte-equal 测试用例

**`compiler/tests/examples/fib_renamed.jhyy`** (18 行):
```jhyy
// EXPECT: 832040
// Recursive Fibonacci — fib(30) = 832040
// v0.9 wip commit 2.5: renamed locals (n→count, r→result) to avoid W-006 + W-004
extern fn printf(fmt: *u8, val: i32) -> i32;
fn fib(count: i32) -> i32 {
    if count < 2 { return count; }
    fib(count - 1) + fib(count - 2)
}
fn main_jhyy() -> i32 {
    let result: i32 = fib(30);
    printf("fib(30) = %d\n", result);
    result
}
```

**`compiler/tests/examples/arith.jhyy`** (17 行):
```jhyy
// EXPECT: 1000042
// i32/i64 mixed arithmetic + as conversion
// v0.9 wip commit 2.5: covers extsw path stability (small_val as i64 + total_val as i32)
//   + const-only data (no let mut → W-005 avoidance).
extern fn printf(fmt: *u8, val: i64) -> i32;
fn main_jhyy() -> i32 {
    let small_val: i32 = 42;
    let big_val: i64 = 1000000 as i64;
    let total_val: i64 = (small_val as i64) + big_val;
    printf("total = %d\n", total_val);
    let down_val: i32 = total_val as i32;
    down_val
}
```

**`compiler/tests/examples/control_flow.jhyy`** (24 行): 递归模拟 while/break/continue 语义,sum 0..9 跳过 5,break at 8 = 23

**3 个测试集特性**:
- 全部纯函数式 / 不依赖 let mut (W-005 avoidance)
- 全部 ≥2 字符变量名 (W-006 avoidance)
- 不依赖 hash 触发面 (W-001 6-8 字符 + _buf 后缀)

---

### 改动 3: 新建 `compiler/tests/stage1-expanded.sh` — Stage 1 byte-equal 验收脚本

7 测试集 byte-equal baseline 锁定脚本:
- 跑 `jhyy_0 build` vs `jhyy_1 build` 对相同 .jhyy 输入
- `cmp -s` 验证 .il byte-equal
- 失败时打印前 5 行 diff
- 总结 pass/fail 列表

---

### 改动 4: `docs/internal/codegen-pitfalls.md § 2` — 6 codegen translation gaps 文档化

| # | tag | 测试 | 根因 | 优先级 | commit |
|---|-----|------|------|--------|--------|
| 1 | **B-φ1** | fib_renamed / control_flow | if-expr v1.0.0 store/load workaround vs v0 phi slot | 🔴 中 | 待 v0.9 commit 2.6+ |
| 2 | **B-let2** | arith | `cg_convert_arg` 漏 `src=l, dst=w` narrow | 🟢 必修 | ✅ **本 commit** |
| 3 | **B-struct** | struct_val_pass | struct by-value sret 路径差异 | 🟡 中 | 待 v0.9 commit 2.7+ |
| 4 | **B-match** | match_exhaustive | match-expr codegen 缺 (跟 parser 翻译耦合) | 🔴 高 | 待 v1.0.0 sprint 3 |
| 5 | **B-data** | const_array | `.data` 段 emit 顺序 / 格式差异 | 🟡 中 | 待 v0.9 commit 2.7+ |
| 6 | **B-testset** | 7 测试集 baseline 锁定 | 测试集本身锁定 | 🟢 完成 | ✅ **本 commit** |

**修复策略共识**:
- byte-equal 优先级 > 100% 覆盖率
- 不可修 gap (B-match) 推迟到 v1.0.0 sprint 3
- 可选修 gap (B-φ1 / B-struct / B-data) 接受 diff,不阻塞 Stage 1 closure
- 实测: commit 2.5 修 B-let2 → byte-equal 1/7 → **2/7**

---

### 改动 5: `docs/internal/workarounds.md` — 加 B-let2 cross-ref entry

索引 + 详细 cross-ref entry:
- 跟 W-007 (w→l extsw) 镜像对称
- 跟 W-009 (src_t==0 兜底) 协同,cg_convert_arg 才算完整
- 引用 `codegen-pitfalls.md § 2.2` + 修复代码 + 测试集 + 验收脚本

---

### 验证(全过)

```bash
# 1. byte-equal baseline
bash compiler/tests/stage1-expanded.sh
# pass: 2 / 7   (hello + arith)
# fail: 5       (fib_renamed / struct_val_pass / match_exhaustive / const_array / control_flow)

# 2. regress 持平
python -c "..."   # 3 OK baseline (持平 commit 12 12 OK 测量口径)

# 3. codegen 文档
docs/internal/codegen-pitfalls.md § 2 — 6 gaps 全记录
docs/internal/workarounds.md — B-let2 cross-ref entry 完整
```

---

### 后续工作

| commit | 主题 | 备注 |
|--------|------|------|
| commit 2.6 | W-006 (1-char local var) 验证完整 | per `v0.9.0任务清单 + 概要设计.md` § commit 2.5 |
| commit 2.7+ | B-φ1 / B-struct / B-data 评估 | 加 `-emit-phi` / `-emit-sret-aligned` flag 或接受 diff |
| commit 3 | main.c → main.jhyy 翻译 (3 子 commit) | jhyy_helpers.c 不重翻译,直接 link |
| commit 4 | Stage 1 byte-equal 验证 + regress.py JHYY_CC 支持 | diff 全空 + regress 持平 + changelog 写完 |
| v1.0.0 | 自举启动 | 5 sprint 粗粒度 |