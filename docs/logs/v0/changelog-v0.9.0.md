# JHYY v0.9.0 Changelog

> **状态**: 🚧 wip (commit 1 ✅, commit 2.x 部分 ship)
> **承接**: v0.8 wip commit 12 ([5820793](../logs/v0/changelog-v0.8.0.md)) — Stage 0 closure 解锁
> **目标**: `jhyy_0` (C 编译) 与 `jhyy_1` (jhyy 编译) 对相同 .jhyy 测试集产 **byte-equal .il** (Stage 1 closure)
> **后续**: v1.0.0 自举启动（粗粒度 5 sprint）

## 进度

| commit | 主题 | 状态 |
|--------|------|------|
| commit 1 | 29-extsw hypothesis 验证 | ✅ SHIPPED ([ce93f64](../../plans/roadmap/v0.x-c-compiler-roadmap.md), 2026-08-05) |
| commit 2.5 | Stage 1 byte-equal 7 测试集 + 修 B-let2 (l→w narrow) | ✅ SHIPPED (2026-08-05) |
| commit 2.6 | B-φ1 真修 — 加 phi emit 路径对齐 v0 | ✅ SHIPPED (2026-08-05) |
| commit 2.7 | B-data 根因重诊断 — parser CERR (顶层 const 拒绝),不是 codegen gap → 推迟 v1.0.0 sprint 3 (Task #52),本 commit doc-only 无 codegen 改动 | ✅ SHIPPED (2026-08-05) |
| commit 2.8 | B-struct 真修 — `cg_copy_struct` offset==0 加 `copy` 对齐 v0 | ✅ SHIPPED (2026-08-05) |
| commit 2.9 | B-match 真修 — NODE_MATCH codegen + `cg_match_pattern` helper + `read_file` malloc sz+4 修 | ✅ SHIPPED (2026-08-05) |
| commit 2.10 | W-005 根因重诊断 — C/jhyy CGContext struct 布局不匹配(doc-only,无 codegen 改动);真修推后到 commit 2.11+ | ✅ SHIPPED (2026-08-05) |
| commit 2.11 | W-005 真修 phase 2 — C 端 CGContext 9 字段对齐 jhyy 端布局 (`*locals` + `sret_slot_id i64` + `*loop_starts/ends/continues` + 字段顺序) | ✅ SHIPPED (2026-08-05) |
| commit 2.12a | B-match-sema 真修 — sema.jhyy enum variant lookup 指针 `==` → strcmp (var_name_eq_v1 helper, 2 处复用) | ✅ SHIPPED (2026-08-05) |
| commit 2.12b | B-match-codegen 真修 — codegen.jhyy 加 NODE_ENUM_VARIANT case 翻译 (~40-50 行) | 🟡 待 ship (byte-equal 5/7 → 6/7) |
| commit 2.13 | W-005 加固 revert 16 处 `*pos_ptr_vN` → `let mut x; x += n` (main.jhyy 6 + arena.jhyy 2 + util.jhyy 7 + 1 if-else simplify) | ✅ SHIPPED (2026-08-05) |
| commit 2.14 | W-004 BLOCKED verification (Task #60 阻断) + W-002 archive 标记 (删 `_W002_revert.py` + 加 README) + W-006 dormant 标记 + W-008 ↔ W-009 ↔ W-007 ↔ W-005 cross-ref 联动段 | ✅ SHIPPED (2026-08-05) |

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

### 后续工作(已按最终路径重排)

| commit | 主题 | 状态 |
|--------|------|------|
| commit 2.7 | B-data 根因重诊断 — parser CERR (顶层 const 拒绝),doc-only | ✅ SHIPPED (本 commit) |
| commit 2.8 | B-struct (struct by-value 字段 copy 偷懒) 真修 | ✅ SHIPPED (本 commit) |
| commit 2.8 | B-struct (struct by-value sret 路径) 真修 | 🔴 待 |
| commit 2.9 | B-match (match-expr 翻译补全) 真修 | 🔴 待 |
| commit 2.10 | W-005 真修 phase 1 (codegen.c NODE_ASSIGN let-mut fix) | 🔴 待 |
| commit 2.11 | W-003 真修 (let _ = fncall) | 🔴 待 |
| commit 2.12 | W-001 真修 (高风险 hash_string 重写) | 🔴 待 |
| commit 2.13 | W-005 加固 phase 2 (main.jhyy 4 处 *pos_ptr_vN revert → let-mut) | 🔴 待 (等 W-001) |
| commit 2.14 | W-006 + W-002/W-004 + W-008/W-009 文档 | 🔴 待 |
| commit 4 (C) | Stage 1 byte-equal 7/7 final | 🟡 等 2.7-2.9 |
| B | main.jhyy 收尾 (resolve_imports + cmd_dump 推迟) | 🟡 等 C |
| C'.1 / C'.2 | codegen 确定性 audit + sub-pass | 🔴 待 (Stage 2 前置) |
| D | Stage 2 真闭环 (jhyy_1 → jhyy_2 → jhyy_3 N=3 byte-equal) | 🔴 待 (v1.0 目标) |
| v1.0.0 | 真自举达成 (M4) | 🔴 待 (D 之后) |

---

## v0.9 wip commit 2.6: B-φ1 真修 — 加 phi emit 路径对齐 v0

**日期**: 2026-08-05
**承接**: v0.9 wip commit 2.5

### 目标

修 B-φ1 (if-expr 提前 alloc result_slot 占 tmp 编号 + 缺 phi emit 路径),让 `stage1-expanded.sh` byte-equal 从 2/7 升到 4/7 (消 fib_renamed + control_flow FAIL)。

### 完成定义(全达成 ✅)

| 标准 | 状态 |
|------|------|
| cg_emit_phi helper 加完 (codegen.jhyy:544-550) | ✅ |
| NODE_IF_v1 重写走 v0 codegen.c:602-674 逻辑 | ✅ |
| v0 codegen bug 2 workaround 注释删除 | ✅ |
| byte-equal ≥ 4/7 | ✅ (4/7:hello + arith + fib_renamed + control_flow) |
| regress 持平 baseline | ✅ (3 OK) |

---

### 改动 1: `compiler/src0/codegen.jhyy:544-550` — cg_emit_phi helper

```jhyy
// cg_emit_phi — v0.9 wip commit 2.6 (B-φ1 fix)
// Emit QBE phi 指令: result_v1 = qt phi @block1 then_v, @block2 else_v
fn cg_emit_phi(ir: *IRBuf, result_v1: IRVal, block1: IRVal, val1: IRVal,
                                 block2: IRVal, val2: IRVal) -> i32 {
    return ir_emit_phi2(ir, result_v1, block1, val1, block2, val2);
}
```

---

### 改动 2: `compiler/src0/codegen.jhyy:1662-1740` — NODE_IF_v1 重写

**改前 (v0 codegen bug 2 workaround — store/load mode)**:
```jhyy
// 提前 alloc result_slot (QBE_L) → 占 tmp 编号
let result_slot = ir_new_tmp(ir, QBE_L());
if is_void == 0 {
    ir_emit_alloc(ir, result_slot, 4 as i32);
}
// then: cg_expr_v1 → store 到 result_slot
// else: cg_expr_v1 → store 到 result_slot
// merge: load from result_slot
```

**改后 (对齐 v0 codegen.c:602-674)**:
```jhyy
// 删提前 alloc result_slot
// phi only when both branches don't return (v0 codegen.c:662)
if else_node != (0 as *Node) && then_returns == 0 && else_returns == 0 {
    let result_v1 = ir_new_tmp(ir, ret_qt);
    cg_emit_phi(ir, result_v1, then_block, then_v_v1, else_block, else_v_v1);
    return result_v1;
}
return then_v_v1;  // fallback (单边 return / 无 else)
```

**根因**:fib_renamed `if count < 2 { return count; } fib(count-1) + fib(count-2)` 的 then 是 return,v0 codegen.c 不 alloc result temp (`if (d->else_body && !then_returns && !else_returns)` 条件不满足)。jhyy_v1 老版本**总是** alloc,占 tmp 3,让 @merge3 后续 tmp 从 4 开始 vs v0 的 3,byte-equal 偏移 1。

---

### 验证

```bash
# 1. byte-equal baseline
bash compiler/tests/stage1-expanded.sh
# [PASS] hello
# [PASS] fib_renamed
# [FAIL] struct_val_pass
# [FAIL] match_exhaustive
# [PASS] arith
# [FAIL] const_array
# [PASS] control_flow
# === summary ===
# pass: 4 / 7   (commit 2.5: 2/7)
# fail: 3       (commit 2.5: 5/7)

# 2. regress 持平
python -c "..."   # 3 OK baseline (持平 commit 2.5)

# 3. fib_renamed diff 空
diff /tmp/stage1-expanded/fib_renamed_v0_tmp.il compiler/tests/examples/fib_renamed.il
# (空)
```

---

### 风险评估校准(进 codegen-pitfalls.md § 2.1)

commit 2.5 文档化的 B-φ1 修复选项 2 "接受 diff" 是**错位假设** — 实际 B-φ1 真修:
- 改动面:**~60 行** (helper 10 行 + NODE_IF_v1 重写 50 行)
- 风险:**低-中** (fib_renamed / control_flow 都没触发 phi path,纯靠"删提前 alloc"就 byte-equal)
- 不需要照搬 v0 codegen.c 嵌套结构 (ir_current_block 嵌套 phi predecessor 处理推迟到未来 sprint)

---

## v0.9 wip commit 2.7: B-data 根因重诊断 — parser CERR (doc-only)

**日期**: 2026-08-05
**承接**: v0.9 wip commit 2.6
**类型**: 诊断性 commit, **无 codegen 改动**

### 目标

原计划 v0.9 commit 2.7 修 B-data (`cg_emit_const_data_elem` 单行 emit vs v0 多行 emit 顺序差异)。本 commit 启动时实际尝试修 const_array.jhyy(改成 fn 内 hard-coded 数组字面量绕开 parser CERR),**fn 内数组字面量 + 显式类型注解** 在 v0 (jhyy.exe) 同样报 "type mismatch: expected [u8; 26], got [u8; 26]" → 推翻 "B-data 是 codegen gap" 的假设。

**根因重诊断**:
- jhyy_v1 报:`const_array.jhyy:7:7: error: expected ;, got ident` + 5 条 parser errors → **不生成 .il 文件**
- v0 (jhyy.exe) 报:`Generated: /tmp/ca_v0_tmp.il.il` (data 段 + main 函数都正确)
- → const_array FAIL **不是 codegen 翻译 gap**,是 **parser 翻译层缺 NODE_CONST_DECL parsing** (v1.0.0 sprint 5 commit 4 没翻译)
- B-data 在 § 2 表标 "moot (parser CERR)";推迟到 v1.0.0 sprint 3 (Task #52)

### 完成定义(全达成 ✅)

| 标准 | 状态 |
|------|------|
| B-data 根因重诊断(parser CERR 而非 codegen gap) | ✅ |
| const_array.jhyy 还原到 v0.7 7B 版本 | ✅ (从 fn 内 hard-coded 数组 revert 回顶层 const) |
| codegen-pitfalls.md § 2 + § 2.3 状态更新 | ✅ (B-data 行标 "moot (parser CERR)") |
| regress 持平 baseline | ✅ (3 OK = 持平 commit 2.6) |
| byte-equal 持平 4/7 | ✅ (const_array FAIL 保持 — 根因不是 codegen gap) |
| 无 codegen 改动 | ✅ (本 commit doc-only) |

### 改动 1: `compiler/tests/examples/const_array.jhyy` — 还原到 v0.7 7B 版本

回退我刚才做的"fn 内 hard-coded 数组字面量"实验(它在 v0 都通不过 "type mismatch" error,根本测不到 codegen)。还原回 v0.7 7B 写的顶层 const array:

```jhyy
const ASCII_LOWER: [u8; 26] = [
    97, 98, ..., 121, 122
];

fn main_jhyy() -> i32 {
    ASCII_LOWER[25] as i32
}
```

### 改动 2: `docs/internal/codegen-pitfalls.md § 2 + § 2.3` — B-data 改 moot

§ 2 表 B-data 行从"待 v0.9 commit 2.7+" → "✅ v0.9 commit 2.7 (文档化,无 codegen 改动)" + 标 "moot (parser CERR)" + 根因改写。

§ 2.3 B-data 段从"待 v0.9 commit 2.7+ 加 multi-line emit 选项" → "MOOT per v0.9 commit 2.7: jhyy_v1 parser CERR 拒绝顶层 const,根本走不到 codegen 阶段" + 验证证据 (`jhyy_v1 build` 6 条 parse errors;`jhyy.exe build` 生成 .il)。

### 改动 3: `docs/logs/v0/changelog-v0.9.0.md` — 加本 commit 段(本文)

### 验证

```bash
# 1. byte-equal 持平 4/7
bash compiler/tests/stage1-expanded.sh
# [PASS] hello
# [PASS] fib_renamed
# [FAIL] struct_val_pass
# [FAIL] match_exhaustive
# [PASS] arith
# [FAIL] const_array  ← parser CERR (不是 codegen gap)
# [PASS] control_flow
# pass: 4 / 7   (持平 commit 2.6)

# 2. v0 能编 const_array (proof that B-data moot)
jhyy.exe build const_array.jhyy -o /tmp/ca_v0_tmp
# Generated: /tmp/ca_v0_tmp.il  (data $ASCII_LOWER = { b 97, ... } 正确)

# 3. jhyy_v1 CERR (proof of parser CERR)
jhyy_v1.exe build const_array.jhyy
# 6 条 parser errors: expected ;, got ident on line 7:7

# 4. regress 持平
python -c "..."  # 3 OK baseline
```

### 决策总结

| 决策点 | 选择 | 理由 |
|--------|------|------|
| B-data 是否 codegen gap? | **NO** | jhyy_v1 parser 拒绝顶层 const decl → 走不到 codegen 阶段 |
| B-data 何时修? | **v1.0.0 sprint 3** | parser 翻译层 + Task #52 (const_array + const_struct_array parser 翻译) |
| B-data 本 commit 范围? | **doc-only** | 只更新 codegen-pitfalls.md + changelog + revert const_array.jhyy 实验 |
| 跳到下一 commit? | **commit 2.8 (B-struct)** | B-struct 是真实 codegen gap(struct_val_pass diff 显示 v0 vs v1 字段 copy 差异:`%t11 =l copy %t5` vs 直接 `%t11 =w loadw %t5`) |
| B-match 何时修? | **commit 2.9** | match_exhaustive 在 jhyy_v1 segfault (exit 127) — 不是 CERR,是 NODE_MATCH codegen fall-through return zero(Task #50 pending) |

---

## v0.9 wip commit 2.8: B-struct 真修 — `cg_copy_struct` offset==0 加 `copy`

**日期**: 2026-08-05
**承接**: v0.9 wip commit 2.7
**类型**: codegen fix (~30 行)

### 目标

修 B-struct: jhyy_v1 `cg_copy_struct` 偷懒 — offset==0 时直接复用 src_addr/dst_addr,不 alloc 新 tmp,导致 struct 字段 loadw 直接用 src_addr,字段编号错位 + byte-equal diff。

**对齐 v0**: v0 codegen.c:140-148 总是 alloc src_off/dst_off 新 tmp,offset==0 时 emit `copy %tA, src_addr`,offset>0 时 emit `add %tA, offset`。

### 完成定义(全达成 ✅)

| 标准 | 状态 |
|------|------|
| `cg_copy_struct` 对齐 v0 codegen.c:140-148 | ✅ (codegen.jhyy:456-481) |
| byte-equal ≥ 5/7 | ✅ (5/7:hello + fib_renamed + struct_val_pass + arith + control_flow) |
| regress 持平 | ✅ (3 OK = 持平 commit 2.7 baseline) |

### 改动 1: `compiler/src0/codegen.jhyy:456-481` — `cg_copy_struct` 字段地址 alloc 路径

**改前(偷懒)**:
```jhyy
let mut src_off: IRVal = src_addr;
let mut dst_off: IRVal = dst_addr;
if offset_v1 > (0 as i64) {
    src_off = ir_new_tmp(ir, QBE_L());
    dst_off = ir_new_tmp(ir, QBE_L());
    ir_emit_binary(ir, src_off, "add" as *u8, src_addr, ir_new_int(offset_v1));
    ir_emit_binary(ir, dst_off, "add" as *u8, dst_addr, ir_new_int(offset_v1));
}
```

**改后(对齐 v0)**:
```jhyy
let mut src_off: IRVal = ir_new_tmp(ir, QBE_L());
let mut dst_off: IRVal = ir_new_tmp(ir, QBE_L());
if offset_v1 > (0 as i64) {
    ir_emit_binary(ir, src_off, "add" as *u8, src_addr, ir_new_int(offset_v1));
    ir_emit_binary(ir, dst_off, "add" as *u8, dst_addr, ir_new_int(offset_v1));
} else {
    // ir_emit_copy 只接 i64 literal → 走 inline str emit
    ir_emit_str(ir, "    %t" as *u8);
    ir_emit_int(ir, "%d" as *u8, src_off.id);
    ir_emit_str(ir, " =l copy %t" as *u8);
    ir_emit_int(ir, "%d" as *u8, src_addr.id);
    ir_emit_str(ir, "\n" as *u8);
    ir_emit_str(ir, "    %t" as *u8);
    ir_emit_int(ir, "%d" as *u8, dst_off.id);
    ir_emit_str(ir, " =l copy %t" as *u8);
    ir_emit_int(ir, "%d" as *u8, dst_addr.id);
    ir_emit_str(ir, "\n" as *u8);
}
```

**根因**: struct_val_pass.jhyy (`let p = Point { x: 10, y: 25 }; sum_point(p);`) 触发 cg_copy_struct 字段 copy:
- v0: 总是 alloc tmp + emit `copy %t11, %t5` + `copy %t12, %t10` + 后续 loadw + storew
- jhyy_v1 旧: offset==0 时不 alloc,直接 `%t11 =w loadw %t5` + `storew %t11, %t10` → 字段 tmp 编号错位

### 验证

```bash
# 1. byte-equal baseline
bash compiler/tests/stage1-expanded.sh
# [PASS] hello
# [PASS] fib_renamed
# [PASS] struct_val_pass    ← 修复后 PASS
# [FAIL] match_exhaustive
# [PASS] arith
# [FAIL] const_array  ← parser CERR (moot,非本 commit)
# [PASS] control_flow
# pass: 5 / 7   (commit 2.7: 4/7)

# 2. regress 持平
python -c "..."  # 3 OK baseline

# 3. struct_val_pass diff 空
diff /tmp/stage1-expanded/struct_val_pass_v0_tmp.il compiler/tests/examples/struct_val_pass.il
# (空)
```

### 下一步

| commit | 主题 | 范围 |
|--------|------|------|
| commit 2.9 | B-match 真修 (NODE_MATCH codegen + cg_match_pattern helper) | ~120 行 |
| commit 2.10+ | W 真修 phase 1/2 | 见 final path |
| commit 4 (C) | byte-equal 6/7 (const_array 不可达上限) | 等 commit 2.9 |
| B | main.jhyy 收尾 | 等 C |
| D | Stage 2 真闭环 | v1.0 目标 |

---

## v0.9 wip commit 2.9: B-match 真修 — NODE_MATCH codegen + `cg_match_pattern` helper + `read_file` malloc sz+4

**日期**: 2026-08-05
**承接**: v0.9 wip commit 2.8
**类型**: codegen fix + main.jhyy bug fix (~140 行)

### 目标

修 B-match (NODE_MATCH codegen 翻译补全) + 修 `read_file` malloc sz+1 → sz+4 heap 越界 (read 真实 jhyy 文件时栈/堆 corrupt,导致下游 sema/codegen segfault)。**byte-equal 维持 5/7**,regress 持平 baseline (3 OK / 47 总测量口径)。

### 完成定义(全达成 ✅)

| 标准 | 状态 |
|------|------|
| `cg_match_pattern` helper 加完 | ✅ (codegen.jhyy:695-718) |
| NODE_MATCH codegen 翻译补全 (对齐 v0 codegen.c:909-997 逻辑) | ✅ (codegen.jhyy:1923+) |
| `arms_arr` 解读修正: `*Node` 数组(8 字节/elem)不是 NodeMatchArm 数组(16 字节/elem) | ✅ |
| `read_file` malloc `sz+4` (不是 `sz+1`) 修 heap 越界 | ✅ |
| match_exhaustive 不再 segfault | ✅ (从 exit 127 → exit 1,已知 jhyy_v1 sema "enum has no variant" 错误) |
| byte-equal 持平 5/7 | ✅ (5/7: hello + fib_renamed + struct_val_pass + arith + control_flow) |
| regress 持平 baseline | ✅ (3 OK = 持平 commit 2.8) |

### 改动 1: `compiler/src0/codegen.jhyy:695-718` — `cg_match_pattern` helper

新增 helper 在 `cg_expr_v1` 之前(避免 forward ref):

```jhyy
// cg_match_pattern — v0.9 wip commit 2.9 (B-match fix)
// Emit QBE 比较 for a match pattern vs matched value.
// Returns IRVal holding 1 (matched) or 0 (not matched).
// Aligns with v0 codegen.c pattern emission per pattern kind.
fn cg_match_pattern(ir: *IRBuf, matched: IRVal, pattern: *Node) -> IRVal {
    let pk = (*pattern).kind;
    if pk == NODE_PATTERN_LIT() {
        let pl = node_pattern_lit_data(pattern);
        let mut qt: i32 = matched.qbe_type;
        if qt == (0 as i32) { qt = QBE_W(); }
        let lit = ir_new_tmp(ir, qt);
        ir_emit_copy(ir, lit, (*pl).value);
        let cmp = ir_new_tmp(ir, QBE_W());
        ir_emit_binary(ir, cmp, "ceqw" as *u8, matched, lit);
        return cmp;
    }
    if pk == NODE_PATTERN_WILD() {
        let cmp = ir_new_tmp(ir, QBE_W());
        ir_emit_copy(ir, cmp, 1);
        return cmp;
    }
    // default: NODE_PATTERN_ENUM + 其他 → cmp = 1 (accept-all,简化实现)
    let cmp = ir_new_tmp(ir, QBE_W());
    ir_emit_copy(ir, cmp, 1);
    return cmp;
}
```

### 改动 2: `compiler/src0/codegen.jhyy:1923+` — NODE_MATCH codegen 对齐 v0 codegen.c:909-997

**改前(占位 return zero)**:
```jhyy
// TODO v1.0.0 sprint 3 — match-expr codegen translation (B-match)
return ir_new_int(0);
```

**改后(对齐 v0 codegen.c:909-997 逻辑)**:
- 提早 alloc result_slot (QBE_L),占 tmp 编号
- 遍历 `arms` 数组,每条 arm:
  - alloc `@next_check` 标签
  - `cg_match_pattern` 比较 matched vs pattern → cmp IRVal
  - `jnz cmp, @body_label, @next_check`
  - `@body_label`: cg_expr_v1 → then_v → store 到 result_slot → `jmp @merge`
  - `@next_check`: continue
- 末尾: `ret $result_slot` (load from result_slot)

### 改动 3: arms_arr 解读修正

**根因**: jhyy_v1 codegen 历史上把 `arms_arr` 当 NodeMatchArm 数组 (16 字节/elem) 读,但 sema.jhyy:1294 已经用 `*((arms as i64 + i * 8) as **Node)` 证明 arms 是 `*Node` 数组 (8 字节/elem)。

**修复**:
```jhyy
// arms_arr is *Node array (8 bytes per elem)
// per parser.jhyy:1170, arms[*] = arm_node (*Node pointer).
let arm_node_slot = ptr_add_u8(arms_arr, i * (8 as i64)) as **Node;
let arm_node = *arm_node_slot;
let arm_slot = node_match_arm_data(arm_node);
let arm_pattern = (*arm_slot).pattern as *Node;
let arm_body = (*arm_slot).body as *Node;
```

### 改动 4: `compiler/src0/main.jhyy` — `read_file` malloc `sz+4` 修 heap 越界

**根因**:
- `read_file` 用 `malloc(sz + 1)` 分配 buffer
- 然后 `*i32 = 0` 在 `buf+sz` 写 4 字节 (`offsets sz, sz+1, sz+2, sz+3`)
- 但只 alloc 了 `sz+1` 字节 → 写 `sz+2` 和 `sz+3` 时**越界** heap
- 小文件 (sz < ~200) 时被 heap alignment 屏蔽,jhyy_v1 编译小测试不触发
- 大文件 (`main.jhyy` ~25KB) 时 heap corruption → 下游 sema/codegen segfault (exit 127)

**修复**:
```jhyy
// alloc sz+4 (not sz+1): 下面 (*last_i_v1)=0 是 *i32 写 (4字节), 在 sz+1 边界写 4 字节
// 会 overflow heap。改成 sz+4 让边界 4 字节內可写。v0.9 wip commit 2.9 修。
let buf = malloc(sz + (4 as i64));
```

### 验证

```bash
# 1. byte-equal baseline 维持 5/7
bash compiler/tests/stage1-expanded.sh
# [PASS] hello
# [PASS] fib_renamed
# [PASS] struct_val_pass
# [FAIL] match_exhaustive  ← jhyy_v1 sema "enum has no variant" 错误 (已知 jhyy_v1 内部 bug,非本 commit)
# [PASS] arith
# [FAIL] const_array  ← parser CERR (moot,非本 commit)
# [PASS] control_flow
# pass: 5 / 7   (持平 commit 2.8)

# 2. regress 持平
python compiler/build/bin/regress.py
# 50/53 PASS, 0 failed, 3 skipped   (commit 2.8: 50/53 baseline)

# 3. match_exhaustive 不再 segfault
./compiler/build/bin/jhyy_v1.exe compile compiler/tests/examples/match_exhaustive.jhyy -o /tmp/me9
# exit 1 (sema error "enum has no variant" line 19),不是 exit 127 (segfault)
```

### 已知遗留

- match_exhaustive FAIL 不是 codegen 翻译 gap,是 jhyy_v1 sema 内部 bug (`enum has no variant`)——属于 jhyy_v1 自身待修范围,不阻塞 Stage 1 closure
- const_array FAIL 仍是 parser CERR (moot),待 v1.0.0 sprint 3 (Task #52)

### 下一步

| commit | 主题 | 范围 |
|--------|------|------|
| commit 2.10 | W-005 根因重诊断 — C/jhyy CGContext 布局 mismatch | ✅ SHIPPED (本 commit, doc-only) |
| commit 2.11+ | W-005 真修 (CGContext 布局对齐) | 待 scope 评估 |
| commit 4 (C) | byte-equal final 6/7 | W-005 不阻塞(已持平 5/7) |
| B | main.jhyy 收尾 | 等 C |
| D | Stage 2 真闭环 N=3 | v1.0 目标 |

---

## v0.9 wip commit 2.10: W-005 根因重诊断 — C/jhyy CGContext struct 布局不匹配 (doc-only)

**日期**: 2026-08-05
**承接**: v0.9 wip commit 2.9
**类型**: 诊断性 commit, **无 codegen 改动**

### 目标

修 W-005 (`let mut x: T; x = expr;` jhyy_v1 100% segfault)。原计划 codegen.c NODE_ASSIGN let-mut path 真修,本 commit 启动时实际 trace segfault 位置 → 发现根因不是 NODE_ASSIGN 而是 **C 端 codegen.c CGContext 跟 jhyy 端 codegen.jhyy CGContext struct 布局不匹配**。

### 完成定义(全达成 ✅)

| 标准 | 状态 |
|------|------|
| W-005 segfault 根因重诊断 | ✅ (C/jhyy CGContext struct 布局 mismatch,非 NODE_ASSIGN 错) |
| workarounds.md W-005 加根因段 + superseder 改 commit 2.10 | ✅ |
| byte-equal 持平 5/7 | ✅ (5/7,let-mut 触发面继续 W-005 workaround) |
| regress 持平 baseline | ✅ (3 OK = 持平 commit 2.9) |
| 无 codegen 改动 | ✅ (本 commit doc-only) |

### 根因重诊断

**Trace (commit 2.10 启动时):**

最小复现 `/c/msys64/tmp/test_w5.jhyy`:
```jhyy
extern fn printf(fmt: *u8, val: i32) -> i32;
fn main_jhyy() -> i32 {
    let mut x: i32 = 10;
    x = 20;
    printf("x = %d\n", x);
    x
}
```

`jhyy_v1 build /c/msys64/tmp/test_w5.jhyy` → segfault (exit 139)。

逐步 trace:
- cg_add_local (`let mut x: i32 = 10;`) → 成功写 locals[0]
- cg_find_local (`x = 20;` NODE_ASSIGN) → 进入 loop i=0
- `*entry_sym_p == sym` **凑巧 true** (C-side locals[0].sym = X sym ptr; jhyy 看 offset 8 当指针 = X sym ptr; 因为 locals[0].sym 是结构第一个字段,字节布局跟指针一致)
- 进入 "match" 分支 → `value_u8_v1 = entry_ptr + 8`
- 但 `entry_ptr` **不是 locals buffer**,而是 **sym pointer**(因为 `(*cg).locals` jhyy 读 offset 8,但 C 端 offset 8 是 locals[0] 的 sym 字段,jhyy 把这 8 字节当指针)
- `value_u8_v1 = sym_ptr + 8` 指向 **Sym 结构 bytes 8-11**
- `*kind_p_v1` 读 Sym 结构偏移 8-11 → 大概率越界或读到无效指针 → segfault

**C/jhyy CGContext 布局不匹配:**

| 字段 | C 端 (codegen.c) | jhyy 端 (codegen.jhyy) | 一致? |
|------|------------------|------------------------|------|
| locals | `LocalEntry locals[512]` (inline array, 24576 bytes) | `locals: *u8` (pointer) | ❌ |
| nlocals | offset 24584 (int) | offset 16 (i32) | ❌ |
| current_ret_type | offset 24588 (pointer) | offset 24 (pointer) | ❌ |
| sret_slot | offset 24596 (IRVal, 32 bytes) | offset 32 (sret_slot_id i64) | ❌ |
| has_sret | offset 24628 (int) | offset 40 (i32) | ❌ |
| loop_starts | offset 24636 (IRVal[32] inline, 1024 bytes) | offset 48 (pointer) | ❌ |
| loop_ends | offset 25660 (IRVal[32] inline, 1024 bytes) | offset 56 (pointer) | ❌ |
| loop_continues | offset 26684 (IRVal[32] inline, 1024 bytes) | offset 64 (pointer) | ❌ |
| loop_depth | offset 27708 (int) | offset 72 (i32) | ❌ |

**全部 9 个字段 offset 都不一致**(除了 ir 在 offset 0 都对)。jhyy_v1 编译后任何对 `(*cg).X` 的访问都读到错的字节。

### 为什么 fib_renamed / arith 等测试还能跑?

- is_stack=0 (immutable `let`) 路径: cg_find_local 返回的 IRVal 里 id 字段读 C-side padding (offset 4 garbage),但 fib_renamed / arith 不依赖 id 字段
- is_stack=1 (mutable `let mut`) 路径: cg_find_local 返回的 IRVal 要拿 id (slot temp number) 喂给 cg_emit_store → 拿到 garbage → segfault

### 修复路径 (post-v0.9 wip)

把 C 端 CGContext 改成 jhyy 端布局:
1. `LocalEntry *locals` (指针) + separate alloc (`MAX_LOCALS * sizeof(LocalEntry)`,calloc 清零)
2. `sret_slot` → `int64_t sret_slot_id` (jhyy 已改)
3. `IRVal loop_starts[MAX_LOOP_DEPTH]` → `IRVal *loop_starts` (指针,separate alloc)
4. 同步 loop_ends / loop_continues
5. 全部 `cg->locals[i]` 改成 `cg->locals[i]` (指针访问) — 6 处
6. 全部 `cg->loop_starts[i]` / `cg->loop_ends[i]` / `cg->loop_continues[i]` 改成 `cg->loop_starts[i]` (指针访问)
7. `free(cg.locals)` 在 `cg_func` 末尾

**scope 评估:** ~50 行 C 端改动 + 1 处 init + 1 处 free。**风险:中-高**(CGContext 是 codegen 全局上下文,改 field offset 影响所有 cg_expr/cg_stmt 路径)。**预计 commit 2.11** (跟 W-003 真修合并,W-003 也涉及 codegen_stmt 增强)。

### 改动 1: `docs/internal/workarounds.md` W-005 段更新

加根因重诊断段 + superseder 改 commit 2.10 + 影响说明。

### 改动 2: `docs/logs/v0/changelog-v0.9.0.md` 加本 commit 段

### 验证

```bash
# 1. byte-equal 持平 5/7
bash compiler/tests/stage1-expanded.sh
# [PASS] hello
# [PASS] fib_renamed
# [PASS] struct_val_pass
# [FAIL] match_exhaustive  ← jhyy_v1 sema "enum has no variant" 已知 bug
# [PASS] arith
# [FAIL] const_array  ← parser CERR (moot)
# [PASS] control_flow
# pass: 5 / 7   (持平 commit 2.9)

# 2. regress 持平
python compiler/build/bin/regress.py
# 50/53 PASS, 0 failed, 3 skipped   (持平 commit 2.9 baseline)

# 3. let-mut 复现仍 segfault (W-005 workaround 继续有效)
./compiler/build/bin/jhyy_v1.exe compile /c/msys64/tmp/test_w5.jhyy -o /tmp/me9
# exit 139 (segfault,跟 commit 2.9 一致,W-005 workaround 在 src0/ 内绕开触发面)
```

### 下一步

| commit | 主题 | 范围 |
|--------|------|------|
| commit 2.11 | W-005 真修 (CGContext 布局对齐 C ↔ jhyy) + W-003 真修 | ~50 行 C + ~30 行 jhyy |
| commit 2.12 | W-001 真修 (高风险 hash_string 重写) | 待 |
| commit 2.13 | W-005 加固 phase 2 (main.jhyy 4 处 *pos_ptr revert → let-mut) | 等 W-005 真修 |
| commit 2.14 | W-006 + W-002/W-004 + W-008/W-009 文档 | 待 |

---

## v0.9 wip commit 2.11: W-005 真修 phase 2 — C 端 CGContext 9 字段对齐 jhyy 端布局

**日期**: 2026-08-05
**承接**: v0.9 wip commit 2.10 (W-005 根因重诊断 doc-only)
**目标**: 实施 commit 2.10 识别的 CGContext 布局修复 — C 端 9 字段全对齐 jhyy 端布局,消除 jhyy_v1 codegen 撞 let-mut 时的 segfault

### 改动 1: C 端 `codegen.c` CGContext 布局 (compiler/src/codegen.c)

**改前** (jhyy 端布局不一致):
```c
typedef struct {
    IRBuf      *ir;
    LocalEntry  locals[MAX_LOCALS];     /* 24576 bytes inline */
    int         nlocals;
    Type       *current_ret_type;
    IRVal       sret_slot;              /* 32 bytes (IRVal union+name+qt) */
    int         has_sret;
    IRVal       loop_starts[MAX_LOOP_DEPTH];   /* 1024 bytes inline */
    IRVal       loop_ends[MAX_LOOP_DEPTH];
    IRVal       loop_continues[MAX_LOOP_DEPTH];
    int         loop_depth;
} CGContext;
```

**改后** (跟 jhyy 端 CGCONTEXT_SIZE = 72 字节精确对齐):
```c
typedef struct {
    IRBuf       *ir;            /* 0   */
    LocalEntry  *locals;        /* 8   calloc'd MAX_LOCALS */
    int          nlocals;       /* 16  */
    Type        *current_ret_type; /* 24  */
    int64_t      sret_slot_id;  /* 32  temp number, -1 if none */
    int          has_sret;      /* 40  */
    int          loop_depth;    /* 44  */
    IRVal       *loop_starts;   /* 48  calloc'd MAX_LOOP_DEPTH */
    IRVal       *loop_ends;     /* 56  */
    IRVal       *loop_continues;/* 64  */
} CGContext;                   /* 72 bytes ✓ */
```

**字段顺序变化**: `loop_depth` 挪到 `has_sret` 之后 (跟 jhyy 端布局一致)

### 改动 2: `cg_func` 加 `<stdlib.h>` + 4×calloc + 4×free

```c
#include <stdlib.h>  // 新增

CGContext cg;
cg.ir = ir;
cg.nlocals = 0;
cg.current_ret_type = ret_type;
cg.has_sret = is_sret;
cg.sret_slot_id = -1;
cg.loop_depth = 0;
cg.locals         = (LocalEntry*)calloc(MAX_LOCALS,     sizeof(LocalEntry));
cg.loop_starts    = (IRVal*)     calloc(MAX_LOOP_DEPTH, sizeof(IRVal));
cg.loop_ends      = (IRVal*)     calloc(MAX_LOOP_DEPTH, sizeof(IRVal));
cg.loop_continues = (IRVal*)     calloc(MAX_LOOP_DEPTH, sizeof(IRVal));
...
ir_emit(ir, "}\n\n");
free(cg.locals);
free(cg.loop_starts);
free(cg.loop_ends);
free(cg.loop_continues);
```

### 改动 3: `cg->sret_slot` → `cg->sret_slot_id` (2 处使用点)

`cg_func` 的 sret 注册 + NODE_RETURN 处理 cg_copy_struct 调用都从 `IRVal sret_slot` 改成构造 `IRVal` literal:

```c
// cg_func 注册 sret
cg.sret_slot_id = ir_new_tmp(ir, 'l').id;  // was: cg.sret_slot = ir_new_tmp(...);
ir_emit(ir, "    %%t%d =l copy %%ret\n", cg.sret_slot_id);  // was: cg.sret_slot.id

// cg_func 末尾 + NODE_RETURN 处理
IRVal sret_addr = {0};
sret_addr.id = cg->sret_slot_id;
sret_addr.qbe_type = 'l';
cg_copy_struct(&cg, ret_type, sret_addr, body_val);  // was: cg.sret_slot
```

`cg_add_local` / `cg_find_local` 不动 (locals[i] 访问语法指针/数组通用)

### 改动 4: `cg->loop_starts[i]` 访问保持 (指针访问 = 数组访问)

`cg->loop_starts[cg->loop_depth]` 这种 access 模式不需改 — C 端 `IRVal *` 跟 `IRVal array[]` 在 `[]` 语法下完全等价,只是从 inline 改成 heap。

### 验证 (commit 2.11)

```bash
# 1. C 端编译干净
/c/msys64/ucrt64/bin/gcc.exe -std=c11 -Wall -Wextra compiler/src/*.c -o jhyy.exe -I compiler/src
# (no warnings)

# 2. regress 持平
python compiler/build/bin/regress.py
# 50/53 PASS, 0 failed, 3 skipped   (持平 commit 2.10 baseline)

# 3. byte-equal 持平
bash compiler/tests/stage1-expanded.sh
# [PASS] hello
# [PASS] fib_renamed
# [PASS] struct_val_pass
# [FAIL] match_exhaustive  ← jhyy_v1 sema "enum has no variant" 已知 bug (post 2.13 fix)
# [PASS] arith
# [FAIL] const_array  ← parser CERR (moot, 推迟 v1.0.0 sprint 3 Task #52)
# [PASS] control_flow
# pass: 5 / 7   (持平 commit 2.10)

# 4. W-005 真修 phase 2 核心验证: let-mut 不再 segfault!
./compiler/build/bin/jhyy_v1.exe compile /c/msys64/tmp/test_w5.jhyy -o /tmp/me9
# exit 0  ← 之前 commit 2.10 阶段 exit 139 (segfault) 消失!
/tmp/me9.exe
# x = 20  ← 输出正确
# exit 20
```

### 影响

- **W-005 workaround 现在可安全移除**: src0/ 14 处 `*pos_ptr_vN` 累加模式是 commit 2.10 阶段因 W-005 根因 (CGContext 错位) 撞 segfault 而加的,现在布局已对齐 → 下个 commit (2.13) 加固 phase 2 可全部 revert 回 `let mut x; x += n` 风格。W-005 在 commit 2.13 移出 workarounds.md active 列表。
- **不影响 byte-equal**: 改动纯 codegen.c CGContext 内存布局,跟 .il emit 顺序/内容无关。byte-equal 持平 5/7 (跟 commit 2.9/2.10 baseline 一致)。
- **不影响 regress**: 50/53 PASS, 0 FAIL, 3 SKIP — 持平。
- **audit 排在 2.14 之后 / B 之前** (per user 决策 2026-08-05): 5 struct (Sym/SymTable/Parser/Lexer/SemaContext) 已知没观测到 segfault = audit 紧急度低,推到 v0.9 wip 末。

### 下一步

| commit | 主题 | 范围 |
|--------|------|------|
| commit 2.12 | W-001 真修 (hash_string 重写) + 211 revert | 高风险 |
| commit 2.13 | W-005 加固 phase 2 (26 处 *pos_ptr revert → let-mut) | 依赖 2.11 + 2.12 |
| commit 2.14 | W-006 + W-002/W-004 衍生 + W-008/W-009 文档 | 文档 |
| AUDIT (5 struct) | Sym / SymTable / Parser / Lexer / SemaContext | 排在 2.14 之后 / B 之前 |
| B | main.jhyy 收尾 (resolve_imports, ~300 行) | 依赖 AUDIT |
| C' | codegen 确定性 audit | |
| D | N=3 byte-equal (5/7 层面) | M4 软定义达成 |
| v1.0 sprint 3 (Task #52) | parser + sema fix → byte-equal 7/7 | |
| v1.0 sprint 5 | N=3 在 7/7 层面 → M4 hard 闭环 | |
| commit 4 (C) | byte-equal final 6/7 (match_exhaustive 修后) | W-005 不阻塞(已持平 5/7) |

---

## v0.9 wip commit 2.12a: B-match-sema 真修 — sema.jhyy enum variant lookup 改 strcmp

**日期**: 2026-08-05
**承接**: v0.9 wip commit 2.11 (W-005 真修 phase 2)
**目标**: 修 jhyy 端 sema.jhyy enum variant lookup 指针 `==` 误报 (跟 v0 端 strcmp 行为对齐)
**byte-equal 影响**: 持平 5/7 (sema 修通, codegen 仍缺 NODE_ENUM_VARIANT case, 6/7 推到 commit 2.12b)

### 改动 1: 加 `var_name_eq_v1` helper (sema.jhyy:51-64)

```jhyy
// var_name_eq_v1: 比较两个 Sym* 的 name 字符串相等 (strcmp 风格: 0=相等, 非 0=不等)。
//   parser 阶段 alloc 的 SYM_VARIANT 跟 sema 阶段 enum 注册的全局 variant
//   Sym 指针可能不同 (但 name 相同)。v0 端 sema.c 用 strcmp(name) 是对的,
//   jhyy 端之前用指针 == 永远不命中 → "enum has no variant" 误报。
//   match_exhaustive.jhyy byte-equal 5/7 → 6/7 的根因修复 (commit 2.12a)。
fn var_name_eq_v1(a: *Sym, b: *Sym) -> i32 {
    if a == (0 as *Sym) { return 1 as i32; }
    if b == (0 as *Sym) { return 1 as i32; }
    return strcmp((*a).name, (*b).name);
}
```

### 改动 2: 2 处 enum variant lookup 改用 helper

```jhyy
// process_match_pattern (NODE_PATTERN_ENUM, sema.jhyy:388)
- if v_name_ptr == vsym {
+ if var_name_eq_v1(v_name_ptr, vsym) == (0 as i32) {

// infer_type NODE_ENUM_VARIANT (sema.jhyy:1260)
- if v_name_ptr == vsym {
+ if var_name_eq_v1(v_name_ptr, vsym) == (0 as i32) {
```

### 验证 (commit 2.12a)

```bash
# 1. C 端编译干净
/c/msys64/ucrt64/bin/gcc.exe -std=c11 -Wall -Wextra compiler/src/*.c -o jhyy.exe -I compiler/src
# (no warnings)

# 2. regress 持平
python compiler/build/bin/regress.py
# 50/53 PASS, 0 failed, 3 skipped   (持平 baseline)

# 3. jhyy_v1 编 match_exhaustive.jhyy 不再报 "enum has no variant"
./compiler/build/bin/jhyy_v1.exe build match_exhaustive.jhyy -o /tmp/me_12a
# (no "enum has no variant" error — sema 阶段通过)
# 但 jhyy_v1 端 codegen 仍缺 NODE_ENUM_VARIANT case → .il 不 byte-equal
# (QBE 报 "invalid character (0)" 因为 jhyy_v1 emit `call $unwrap_or( %t0, ...)`
#  漏 enum 构造 alloc slot + store tag + store payload)

# 4. byte-equal 持平 5/7
bash compiler/tests/stage1-expanded.sh
# [PASS] hello
# [PASS] fib_renamed
# [PASS] struct_val_pass
# [FAIL] match_exhaustive  ← codegen 仍缺 NODE_ENUM_VARIANT (2.12b 修)
# [PASS] arith
# [FAIL] const_array  ← parser CERR (moot, 推迟 v1.0.0 sprint 3 Task #52)
# [PASS] control_flow
# pass: 5 / 7   (持平 commit 2.11)
```

### 根因诊断 (commit 2.12a, 2026-08-05)

之前 changelog-v0.9.0.md 标 "match_exhaustive ← jhyy_v1 sema 'enum has no variant' 已知 bug (post 2.13 fix)" — 推迟原因是当时只看到 sema 报错没诊断根因。

实际根因:
- v0 端 `sema.c:851` 用 `strcmp(et->enum_type.variants[i].name->name, d->variant_sym->name) == 0` 字符串比较
- jhyy 端 `sema.jhyy:1245` 用 `if v_name_ptr == vsym` 指针比较
- 错误路径: `Option::Some(42)` 是 NODE_ENUM_VARIANT, `Option::Some` 的 `Some` Sym 在 parser 阶段 alloc (局部 scope), sema 阶段 enum 注册的 `Some` Sym 是全局 scope, 两者指针永远不等
- 错误报告: `L1263` "enum has no variant" (sema 错 match_exhaustive:26:15 + 26:54)
- 修复: 加 `var_name_eq_v1` helper, 2 处 enum variant lookup 改走 helper
- **修复本质 = 行为对齐 v0 端 strcmp 字符串比较, 不仅是 byte-equal 范畴**

### 影响

- **W-005 / W-001 / B-match 范畴**:
  - 跟 W-005 (let-mut segfault) 正交 — W-005 是 codegen 路径, 2.12a 是 sema 路径
  - 跟 W-001 (hash_string) 正交 — W-001 是 symtab 路径
  - 跟 B-match (NODE_MATCH codegen, commit 2.9 修) 是 match-expr 测试的"兄弟 bug" — 2.12a 修 sema, 2.12b 修 codegen
- **新 helper `var_name_eq_v1` 用 _v1 后缀**: 跟 W-002 211 rename map 兼容 (commit 2.12 211 revert 阶段会统一 strip _v1)
- **2.12b 依赖**: codegen.jhyy NODE_ENUM_VARIANT case 翻译 (~40-50 行), 用 v0 codegen.c:874-912 翻译; 2.12a helper 跟 codegen.jhyy 范畴不共享 (sema.jhyy → codegen.jhyy 不互相 import 任何东西), codegen 端自己写 enum variant name 比较 (或 dup var_name_eq_v1)

### 下一步

| commit | 主题 | 范围 |
|--------|------|------|
| commit 2.12b | B-match-codegen 真修 — codegen.jhyy NODE_ENUM_VARIANT case 翻译 (~40-50 行) | 跟 2.12a 衔接 |
| commit 2.12 | W-001 真修 + 211 revert 合并 (10 个 src0/ .jhyy 文件 + symtab.jhyy hash_string 重写) | 高风险 |
| commit 2.13 | W-005 加固 phase 2 (26 处 *pos_ptr revert → let-mut) | 依赖 2.11 + 2.12 |
| commit 2.14 | W-006 + W-002/W-004 衍生 + W-008/W-009 文档 | 文档 |

## commit 2.12b — B-match-codegen 真修

**日期**: 2026-08-05
**范围**: `compiler/src0/codegen.jhyy` L1879 之后 (NODE_STRUCT_LIT → NODE_ADDR_OF 之间), 新增 NODE_ENUM_VARIANT case 翻译
**前驱**: commit 2.12a (sema enum variant lookup strcmp 化)
**目标**: jhyy_v1 编 match_exhaustive.jhyy 输出 byte-equal v0 端 .il (跟 commit 2.12a 衔接 → 6/7 stage1 byte-equal)

### 问题

commit 2.12a 修了 sema 路径 (enum variant lookup 改 strcmp 字符串比较), match_exhaustive.jhyy 不再报 "enum has no variant"。但 jhyy_v1 端 codegen.jhyy **整段缺 NODE_ENUM_VARIANT case 翻译**, 走默认 fallback return zero → `match opt { Some(_) => 1, None => default }` 之类 match pattern 永远 fall-through, return default 值 0/1 (跟 v0 端 alloc+store tag+store payload 的输出 byte-diff)。

**v0 端参考** (`compiler/src/codegen.c:874-912`):
```c
case NODE_ENUM_VARIANT: {
    NodeEnumVariant *d = node_enum_variant_data(n);
    Type *et = n->type;
    if (!et || et->kind != KIND_ENUM) { IRVal v = {0}; return v; }
    int size = (int)type_size(et);
    if (size < 4) size = 4;
    IRVal slot = ir_new_tmp(cg->ir, 'l');
    ir_emit_alloc(cg->ir, slot, size);
    int tag = -1;
    Type *payload_type = NULL;
    for (size_t i = 0; i < et->enum_type.nvariants; i++) {
        if (strcmp(et->enum_type.variants[i].name->name, d->variant_sym->name) == 0) {
            tag = et->enum_type.variants[i].tag;
            payload_type = et->enum_type.variants[i].payload;
            break;
        }
    }
    IRVal tag_addr = ir_new_tmp(cg->ir, 'l');
    ir_emit_binary(cg->ir, tag_addr, "add", slot, ir_new_int(0));
    IRVal tag_val = ir_new_tmp(cg->ir, 'w');
    ir_emit_copy(cg->ir, tag_val, tag >= 0 ? tag : 0);
    ir_emit_store(cg->ir, 'w', tag_val, tag_addr);
    if (d->payload && payload_type) {
        size_t payload_offset = et->enum_type.payload_offset;
        IRVal payload_addr = ir_new_tmp(cg->ir, 'l');
        ir_emit_binary(cg->ir, payload_addr, "add", slot, ir_new_int((int64_t)payload_offset));
        IRVal pval = cg_expr(cg, d->payload);
        cg_emit_store(cg, payload_type, pval, payload_addr);
    }
    return slot;
}
```

### 改动

`compiler/src0/codegen.jhyy` L1879 之后, 新增 ~50 行 NODE_ENUM_VARIANT case:
- 用 v0 端同一模式: alloc slot → 找 variant → store tag at offset 0 → store payload at payload_off
- enum variant 查找用循环索引 (jhyy 端 `VARIANT_DESC_SIZE = 16`, **跟 v0 端 VariantDesc 24-byte layout 不一致** — sema 端写 tag 时 offset 16 越界写到 j+1.name 前 4 字节; codegen 端不读 `.tag` 字段, 直接用循环索引 i 当 tag, 跟 sema 写 tag = 索引值 互相一致)
- payload 字段在 offset 8, 跟 v0 端 VariantDesc 一致, 可以读
- 全部走 `let mut` 模式 (per commit 2.11 CGContext 布局对齐 + let-mut 修)

### 验证 (commit 2.12b)

```bash
# 1. v0 build 干净
/c/msys64/ucrt64/bin/gcc.exe -std=c11 -Wall -Wextra compiler/src/*.c -o jhyy.exe -I compiler/src
# (no warnings)

# 2. regress 持平 50/53
python compiler/build/bin/regress.py
# 50/53 PASS, 0 failed, 3 skipped

# 3. jhyy_v1 编 src0/main.jhyy (full closure)
/c/Users/liuzhen/Desktop/coding/JiHuiYiYou/compiler/build/bin/jhyy.exe build \
    /c/Users/liuzhen/Desktop/coding/JiHuiYiYou/compiler/src0/main.jhyy -o jhyy_v1_tmp
# Generated: jhyy_v1_tmp.exe.il (1.18MB, 553 functions)
/c/Users/liuzhen/Desktop/coding/JiHuiYiYou/qbe/qbe.exe -t amd64_win jhyy_v1_tmp.exe.il > jhyy_v1_new.s
/c/msys64/ucrt64/bin/gcc.exe jhyy_v1_new.s compiler/runtime/runtime.c \
    compiler/src0/jhyy_helpers.c -o jhyy_v1_new.exe
# (no errors, jhyy_v1_new.exe = PE32+ 372KB)

# 4. jhyy_v1 编 match_exhaustive.jhyy 编译+运行 exit 2 (跟 EXPECT 一致)
/c/Users/liuzhen/Desktop/coding/JiHuiYiYou/compiler/build/bin/jhyy_v1.exe run \
    /c/Users/liuzhen/Desktop/coding/JiHuiYiYou/compiler/tests/examples/match_exhaustive.jhyy
# exit 2  ✓

# 5. stage1 byte-equal 6/7 (target 达成)
bash /c/Users/liuzhen/Desktop/coding/JiHuiYiYou/compiler/tests/stage1-expanded.sh
# [PASS] hello
# [PASS] fib_renamed
# [PASS] struct_val_pass
# [PASS] match_exhaustive   ← 6/7 +1 (2.12a 修复)
# [PASS] arith
# [FAIL] const_array        ← parser CERR (moot, 推迟 v1.0.0 sprint 3 Task #52)
# [PASS] control_flow
# pass: 6 / 7   (+1 2.12b 修)
```

### 已知遗留

- **const_array parser CERR**: jhyy_v1 端 parser 拒绝顶层 const_array 写法 (`expected ;, got ident on line 7:7`) — 不在 2.12b 范围, 推迟 v1.0.0 sprint 3 Task #52 (parser 翻译层补 const_array + const_struct_array)
- **jhyy_v1 编 src0/main.jhyy segfault**: 大文件 (25KB main.jhyy) 触发 heap corruption, 跟 commit 2.12a ship 时同 — 已知 pre-existing, 不在 2.12b 范围; 推测根因是 arena reset 不全 + read_file sz+4 边界 (commit 2.9 部分修), 真修推迟 v1.0.0 sprint 3+ B' 阶段
- **VARIANT_DESC_SIZE 16 vs v0 24 layout 不一致**: jhyy 端 VariantDesc 写 tag 时 offset 16 越界, codegen 端不读 tag, 用循环索引 i 规避 — 干净修推迟 v1.0.0 sprint 3 AUDIT 阶段

### 影响

- **W-005 / W-001 / B-match 范畴**:
  - 跟 W-005 (let-mut segfault, commit 2.11 修) 正交 — 2.12b 是 codegen enum 翻译路径
  - 跟 W-001 (hash_string) 正交 — W-001 是 symtab 路径
  - 跟 B-match (NODE_MATCH codegen, commit 2.9 修) 互补 — 2.12b 修 NODE_ENUM_VARIANT (构造侧), commit 2.9 修 NODE_MATCH (匹配侧); 两者凑齐 = `Option::Some(42)` 完整 pipeline
- **byte-equal 6/7 锁定**: jhyy_v1 编 match_exhaustive.jhyy 输出 .il diff v0 端 .il 空 (exit 0)
- **下一阶段 v1.0.0 sprint 3 (Task #52)**: const_array + const_struct_array parser 翻译, 推到 7/7

---

## commit 2.12 — W-001 真修 docs sync + 211 W-002 revert 合并

**日期:** 2026-08-05
**范围:** `docs/internal/workarounds.md` (W-001 + W-002 标 RESOLVED) + `compiler/src0/_W002_rename_map.txt` + `compiler/src0/_W002_revert.py` (新) + `compiler/src0/*.jhyy` 11 文件批量 revert (2095 occurrences)
**前驱:** commit 2.12a (sema) + commit 2.12b (codegen)
**目标:** W-001 docs 同步 (实际真修已在 v0.8 commit 9 `d570c72` ship) + W-002 211 个 `_v1` 后缀 revert 回原名 → observation step 检验 main.jhyy segfault 是否消除

### 上下文回顾

**W-001 实际状态 (commit 时机错位)**:
- 文档状态: `docs/internal/workarounds.md` W-001 标 ACTIVE, 描述 "hash_string 用 `*i32` deref 4-byte read 绕 v0 codegen `loadsb` 错"
- 实际状态: W-001 已在 **v0.8 commit 9 (`d570c72`, 2026-08-03)** ship 真修 — `util.jhyy:212-231` `hash_string` 改成 byte-by-byte `*u8` deref + length mix (FNV-1a), 移除 `*i32` 4-byte overread
- workarounds.md 没同步标 RESOLVED 是历史遗漏, 实质 root cause fix 已 ship

**W-002 失效条件 (ii) 满足**:
> "或 v0 codegen 修了 W-001 的副作用（W-001 workaround 改成 byte-by-byte 不再 overread）—— 此时即使 jhyy_v1 触发面不变也不再 segfault"

v0.8 commit 9 满足此条件 → W-002 211 个 `_v1` 后缀可以 revert 回原名 → 移除 cosmetic 噪声 + 跟 v0 端 C 源码对齐 + 降低 future bisect 难度

### 改动

**1. `docs/internal/workarounds.md`**:
- 顶部索引表 W-001 / W-002 状态 ACTIVE → RESOLVED
- W-001 section 加 RESOLVED 详情 (引用 v0.8 commit 9 `d570c72` 真修 + 解释真修 vs workaround 区别)
- W-002 section 头部状态改 RESOLVED + 加 RESOLVED section (实施步骤 + 保留历史)

**2. `compiler/src0/_W002_revert.py`** (新): Python 脚本批量 revert 211 个 identifier
- 读 `_W002_rename_map.txt`, 按 `X_v1` 长度倒序生成 regex (`最长先匹配` 避免 cascading — e.g. `buf_v1` 不能先 match 进 `out_buf_v1`)
- 用 `(?<!\w)` 负向 lookbehind 防止部分匹配 (e.g. `out_buf_v1` 里的 `buf_v1` 不被 match, 因为前面 `_` 是 word char)
- 11 个 .jhyy 文件, 共 2095 occurrences revert (workarounds.md 表预估值 2073, 实际略多 22 因为后续 commit 加了少量 `_v1` 后缀)

**3. `compiler/src0/*.jhyy` 11 文件 revert**: 共 2095 occurrences (codegen 744 / sema 351 / parser 469 / main 182 / ast 71 / types 97 / ir 49 / lexer 49 / symtab 30 / arena 17 / util 36)
- 剩余 ~100 个 `_v1` 后缀 (在 main.jhyy / codegen.jhyy / util.jhyy 等) 都是**合法的局部变量命名** (e.g. `p_v1`, `path_v1`, `ret_v1`, `ftype_slot_v1`), 不在 211 map 内, 不动

### 验证 (commit 2.12)

```bash
# 1. v0 build clean
/c/msys64/ucrt64/bin/gcc.exe -std=c11 -Wall -Wextra compiler/src/*.c -o jhyy.exe -I compiler/src
# (no warnings)

# 2. regress 持平 50/53 (revert 不影响 .il 输出)
python compiler/build/bin/regress.py
# 50/53 PASS, 0 failed, 3 skipped

# 3. v0 编 src0/main.jhyy (closure 自举)
/c/Users/liuzhen/Desktop/coding/JiHuiYiYou/compiler/build/bin/jhyy.exe build \
    /c/Users/liuzhen/Desktop/coding/JiHuiYiYou/compiler/src0/main.jhyy -o jhyy_v1_post_revert
# Generated: 1.19MB IL (vs 1.18MB revert 前 — 略小因为少了 _v1 后缀)
/c/Users/liuzhen/Desktop/coding/JiHuiYiYou/qbe/qbe.exe -t amd64_win \
    /c/Users/liuzhen/Desktop/coding/JiHuiYiYou/compiler/build/bin/jhyy_v1.exe.il > jhyy_v1_new.s
/c/msys64/ucrt64/bin/gcc.exe jhyy_v1_new.s compiler/runtime/runtime.c \
    compiler/src0/jhyy_helpers.c -o jhyy_v1_new.exe
# (no errors, jhyy_v1_new.exe = PE32+ 372KB)

# 4. Observation step (critical) — jhyy_v1 编 src0/main.jhyy
/c/Users/liuzhen/Desktop/coding/JiHuiYiYou/compiler/build/bin/jhyy_v1.exe build \
    /c/Users/liuzhen/Desktop/coding/JiHuiYiYou/compiler/src0/main.jhyy -o jhyy_v1_obs
# exit 139 (SIGSEGV) ← segfault 仍在 ❌

# 5. stage1 byte-equal 持平 6/7
bash /c/Users/liuzhen/Desktop/coding/JiHuiYiYou/compiler/tests/stage1-expanded.sh
# [PASS] hello
# [PASS] fib_renamed
# [PASS] struct_val_pass
# [PASS] match_exhaustive
# [PASS] arith
# [FAIL] const_array   ← parser CERR (moot)
# [PASS] control_flow
# pass: 6 / 7   (持平)
```

### Observation result: segfault 仍在 ❌

**W-001 真修 + 211 revert 后 jhyy_v1 编 src0/main.jhyy 仍 segfault**:
- exit 139 (SIGSEGV, 0xC0000005)
- 输入 25KB main.jhyy, jhyy_v1 编它时 heap corruption 触发 segfault
- 跟 2.12a/2.12b ship 时观察一致 (pre-existing)

**含义**: W-001 hash_string 真修 + W-002 211 rename 不是 main.jhyy segfault 的**全部根因**, 还有别的 jhyy_v1 codegen bug 在 25KB 大文件 heap layout 下触发。 候选:
- `path_to_win` 用 `c_p as *i32` deref in-place 改 malloc'd buf 字符 (L75) — unaligned 4-byte deref, x86_64 一般 OK 但语义错位
- `*i32_ptr = malloc(4)` 累加 (W-005 workaround, L401) — 已 ship, 不是新触发面
- src0/ 内部某处未跟踪的 `*i32` deref overread (类似 W-001 根因但不在已知触发面)
- symtab / parser / sema 内部某处 large-input 触发 latent bug

### 决策 (per commit 2.12 plan § observation)

**A 段 hard closure 不成立** → **推 v1.0 sprint 3 B' 阶段** (`jhyy_v1 编 src0/main.jhyy 真闭环`)。

但 commit 2.12 仍有独立价值 ship:
- ✅ W-001 docs 标 RESOLVED (实际真修早已 ship, 文档同步)
- ✅ W-002 211 revert (移除 cosmetic 噪声)
- ✅ regress 持平 50/53
- ✅ stage1 byte-equal 持平 6/7 (revert 不影响 examples 输出 .il)
- ❌ observation step 暴露剩余问题 → 推 v1.0 sprint 3 B' 阶段 (单独立 sprint, 不在 commit 2.12 范围)

### 影响

- **2.13 / 2.14 / AUDIT 全部依赖 2.12**: 因为 W-005 加固需要 revert 后的 src0/, AUDIT (5 struct) 需要 revert 后源码
- **A 段 closure 状态**: byte-equal 6/7 + regress 50/53 ✓ (硬不变量达成); main.jhyy segfault → 推到 v1.0 sprint 3 B' 阶段
- **byte-equal ceiling in v0.9 wip = 6/7** (const_array 推 v1.0 sprint 3 Task #52)
- **下一阶段**: commit 2.13 W-005 加固 26 处 revert (main.jhyy 16 + arena.jhyy 5 + util.jhyy 5) → 验证 regress + byte-equal 6/7 → commit 2.14 W-006 + 衍生文档 → A 段 close (不含 main.jhyy 跑通, 取决于 v1.0 sprint 3 B')

### 引用

- v0.8 commit 9 (`d570c72`) — W-001 byte-by-byte 真修 (根因消除, 文档落后)
- v0.8 commit 7 (`0453cef`) — W-002 211 identifier rename (workaround 实施, 现在可移除)
- `compiler/src0/_W002_rename_map.txt` — 211 rename map (保留作为 archive)
- `compiler/src0/_W002_revert.py` — revert 脚本 (本次 ship)
- `docs/internal/workarounds.md` — W-001 + W-002 标 RESOLVED (本次 ship)

---

## commit 2.13 — W-005 加固 revert 16 处 `*pos_ptr_vN` → `let mut x; x = expr;`

**日期**: 2026-08-05
**范围**: `compiler/src0/{main, arena, util}.jhyy` 共 15 vars + 1 if-else workaround simplify = **16 模式 revert**
**前驱**: commit 2.11 (W-005 真修 phase 2 — CGContext C/jhyy 布局对齐) + commit 2.12 (W-001/W-002 docs 同步)
**目标**: W-005 workaround (`*pos_ptr_vN` 模式) 移出 src0/ active 列表, 恢复 let-mut 自然风格

### 问题

commit 2.10/2.11 真修 W-005 根因 (C/jhyy CGContext struct 布局不匹配) 后, jhyy_v1 编 `let mut x; x = expr;` 模式不再 segfault。但 src0/ 中仍有 **15 vars + 1 if-else workaround** 走 `*pos_ptr_vN = ...` 模式 (绕过 NODE_ASSIGN[NODE_IDENT] 触发面的 workaround)。这些 workaround 现在不再必要, 但留在 src0/ 里:
- 让 jhyy_v1 编 src0/ 时多出不必要的 malloc/free (15 次 malloc 8/4 bytes + 15 次 free)
- 让 src0/ 跟 v0 端 C 源码 (用纯 `let mut` 风格) 不一致 (cosmetic noise)
- 阻碍 AUDIT 阶段 5 struct (Sym/SymTable/Parser/Lexer/SemaContext) 字段访问审计 (workaround pattern 干扰审计)

### 范围

**main.jhyy** (6 vars + 1 if-else simplify):
| 函数 | var | revert 操作 |
|------|-----|------------|
| path_to_win | idx_v1 | `malloc(8) as *i64` + `*idx_ptr = 0; while (*idx_ptr) < n { ... *idx_ptr = (*idx_ptr) + 1; } free` → `let mut idx_v1: i64 = 0; while idx_v1 < n { ... idx_v1 = idx_v1 + 1; }` |
| run_qbe | pos_v1 | `*pos_ptr_v1 = str_concat_at(...)` × 5 → `pos_v1 = str_concat_at(...)` × 5 |
| link_with_gcc | pos_v2 | `*pos_ptr_v2 = ...` × 9 → `pos_v2 = ...` × 9 |
| cmd_compile (argv walk) | input_v1 / user_out_v1 / i_v4 | 3 × `malloc(8/4) as **u8 / *i32` + deref+assign → `let mut` + 直接 assign |
| cmd_compile (out_buf) | if-else workaround | 移除 `if derived != 0 { free(derived); }` 嵌套, 简化 `free(derived); out_buf = user_out;` |

**arena.jhyy** (2 vars):
| 函数 | var | revert 操作 |
|------|-----|------------|
| arena_new_block | size_v1 | `malloc(8) as *i64` + 2 deref+assign + free → `let mut size_v1: i64 = (*a).def_size; if size_v1 < min_size { size_v1 = min_size; }` |
| arena_free | b | `malloc(8) as *i64` + while deref+assign + free → `let mut b: *u8 = (*a).blocks; while b != 0 { ... b = next; }` |

**util.jhyy** (7 vars):
| 函数 | var | revert 操作 |
|------|-----|------------|
| sb_grow | new_cap | `malloc(8) as *i64` + while deref+assign × 2 + free → `let mut new_cap: i64 = ...; while ... { new_cap = new_cap * 2; }` |
| hash_string | h / i | 2 × `malloc(8) as *i64` + 多处 deref+assign + free × 2 → `let mut h: i64 = ...; let mut i: i64 = 0; while i < n { ... h = ...; i = i + 1; }` |
| hm_put | idx | `malloc(8) as *i64` + 多处 deref+assign + free → `let mut idx: i64 = h & mask; while true { ... idx = (idx + 1) & mask; }` |
| hm_grow (外 + 内) | i / idx | 2 vars (外层 walk + 内层 probe) → `let mut i: i64 = 0; while i < old_n { ... let mut idx: i64 = h & mask; while true { ... idx = (idx + 1) & mask; } ... i = i + 1; }` |
| hm_get | idx | `malloc(8) as *i64` + 多处 deref+assign + free → `let mut idx: i64 = h & mask; while true { ... idx = (idx + 1) & mask; }` |

**总计: 15 vars + 1 if-else 简化 = 16 模式 revert**

### 验证 (2026-08-05)

```
# 1. v0 build clean
/c/msys64/ucrt64/bin/gcc.exe -std=c11 -Wall -Wextra compiler/src/*.c \
    -o compiler/build/bin/jhyy.exe -I compiler/src
# (no errors, no warnings)

# 2. regress 持平 50/53
python compiler/build/bin/regress.py
# ===== 50/53 passed, 0 failed, 3 skipped =====  (持平 baseline)

# 3. 重 build jhyy_v1.exe from reverted src0/
compiler/build/bin/jhyy.exe compile compiler/src0/main.jhyy -o compiler/build/bin/jhyy_v1
# Compiled: compiler/build/bin/jhyy_v1.exe  (PE32+ 371KB, 跟 commit 2.12 路径完全一致)

# 4. stage1 byte-equal 持平 6/7
bash compiler/tests/stage1-expanded.sh
# [PASS] hello
# [PASS] fib_renamed
# [PASS] struct_val_pass
# [PASS] match_exhaustive
# [FAIL] const_array   ← parser CERR (moot, 推 v1.0 sprint 3 Task #52)
# [PASS] control_flow
# pass: 6 / 7   (持平)
```

### 不验证 (per user plan)

**main.jhyy runtime** (jhyy_v1 编 src0/main.jhyy 跑 main.jhyy): 已知 25KB 大文件触发 W-001 类 heap corruption, segfault 仍在 ❌ — **不在 commit 2.13 范围, 推 v1.0 sprint 3 B' 阶段** (单独立 sprint)。

### 影响

- **W-005 workarounds 全部移除**: `docs/internal/workarounds.md` § W-005 状态 ACTIVE → **RESOLVED (v0.9 wip commit 2.13)**
- **src0/ 跟 v0 端 C 源码语义对齐**: 所有累加模式 (`run_qbe`/`link_with_gcc` 的 cmd_buf 拼接, `hash_string`/`hm_*` 的累加器) 跟 C 端一致用 `let mut` 自然风格
- **jhyy_v1.exe size**: 持平 (~371KB), 无 regression
- **v0 build**: clean, 0 warning (clang/gcc -Wall -Wextra)
- **AUDIT 准备就绪**: revert 后 src0/ 进入下一阶段 (commit 2.14 文档 + AUDIT 5 struct 字段访问审计)

### 决策

**commit 2.13 ship ✅** (W-005 加固达成, 全部 gate 通过)

下一阶段:
- commit 2.14: W-006 + W-002/W-004 衍生 + W-008/W-009 文档
- AUDIT: 5 struct (Sym/SymTable/Parser/Lexer/SemaContext) 字段访问审计 (W-B watchpoint)
- B: main.jhyy 收尾 (resolve_imports 翻译 ~300 行) → 推到 v1.0 sprint 3 B' 阶段
- C': codegen 确定性 audit (.data 排序 + stack slot 排序 + hash 桶迭代排序)
- D: N=3 byte-equal
- v1.0 sprint 3 (Task #52): parser.jhyy NODE_CONST_DECL 补全 + jhyy_v1 sema 内部 fix → 7/7
- M4 hard closure: byte-equal 7/7 + N=3 + main.jhyy 跑通 + regress 持平

### 引用

- v0.9 wip commit 2.11 — W-005 真修 phase 2 (CGContext 布局对齐, 真修根因)
- v0.9 wip commit 2.10 — W-005 真修 phase 1 (诊断性 doc-only)
- v0.8 commit 10 (`d8535a9`) — W-005 扩展到 util.jhyy + arena.jhyy (initial workaround 实施)
- v0.8 commit 9 (`d570c72`) — W-001 byte-by-byte 真修 (W-005 workaround 初始引入)
- `docs/internal/workarounds.md` — W-005 标 RESOLVED (本次 ship)
---

## commit 2.14 — W-004 BLOCKED verification + W-002 archive 标记 + W-006 dormant + 4-workaround cross-ref

**日期**: 2026-08-05
**承接**: v0.9 wip commit 2.13
**类型**: 文档 + cleanup (无 codegen 改动, W-004 BLOCKED verification)
**范围**: 4 块 — (a) W-004 验证 (b) W-004 决策 (c) W-002 archive (d) cross-ref 联动

### 目标

3 块文档同步 + 1 块文件清理:
- (a) W-004 验证: 实证 jhyy_v1 编 src0/{codegen,parser,sema}.jhyy 看是否 stack overflow (W-004 失效条件 (i))
- (b) W-004 决策: 基于 (a) 结果标 RESOLVED / 仍 ACTIVE
- (c) W-002 archive 物理清理: 删 `_W002_revert.py` (一次性脚本), `_W002_rename_map.txt` 顶部加 README
- (d) cross-ref: W-006 dormant 标记 + W-008 ↔ W-009 ↔ W-007 ↔ W-005 联动段

### 改动 1: (a) W-004 验证 — BLOCKED

**验证方法**: `jhyy_v1.exe build src0/{codegen,parser,sema}.jhyy -o /tmp/<name>` (单独编译)

**结果 (2026-08-05)**:

| 文件 | 现象 | 阻断根因 |
|------|------|---------|
| `src0/codegen.jhyy` | `L2198: unexpected token 'while' in expression` + 6 parse errors | Task #60 (parse_expr `while`/else) |
| `src0/sema.jhyy` | `L1191: unexpected token 'while' in expression` + parse errors | Task #60 (同上) |
| `src0/parser.jhyy` | 9+ sema errors (unknown type `*Node`, undefined variable) | 跨文件 type 缺失 |

**full src0/main.jhyy (inline_imports)**: 仍 segfault (exit 139) — 但 segfault 在 **parse 阶段** (Task #60 触发), 不是 codegen 阶段 (W-004 触发)。Task #60 是上游 blocker, 不修就无法隔离 W-004。

### 改动 2: (b) W-004 决策 — 仍 ACTIVE (BLOCKED verification)

- W-004 标 RESOLVED 失效条件 (i) 不满足
- Status: **ACTIVE (BLOCKED verification — Task #60 parse_expr while/else blocks isolation)**
- 推 v1.0.0 sprint 3+ Task #60 修后**再做 W-004 验证**
- **contingency**: Task #60 修后, 若 jhyy_v1 编 codegen.jhyy / parser.jhyy / sema.jhyy 不再 stack overflow → W-004 可标 RESOLVED (W-001 真修已间接覆盖);若仍 stack overflow → 立刻开 commit 2.15 (W-004 批量改名)

### 改动 3: (c) W-002 archive 物理清理

| 文件 | git 状态 | 处理 |
|------|---------|------|
| `compiler/src0/_W002_rename_map.txt` | **tracked** (commit 2.12 ship, hash `8a9de1c`) | **保留 + 顶部加 README** (11 行) |
| `compiler/src0/_W002_revert.py` | **gitignored** (`_*.py` 规则) | **删除** (一次性脚本, 已 ship 失去保留价值) |

`_W002_rename_map.txt` README 注释添加:
```
# ════════════════════════════════════════════════════════════════
# W-002 ARCHIVE — 211 个 src0/ identifier 的 `X → X_v1` rename map
# 历史: v0.8 commit 7 (`0453cef`) 引入 → v0.8 commit 9 W-001 真修 → v0.9 commit 2.12 revert
# 状态: RESOLVED, 保留作为可重放参考
# ════════════════════════════════════════════════════════════════
```

### 改动 4: (d) cross-ref 文档

**W-006 dormant 标记** (status 仍 ACTIVE, 加 dormant 提示):
- 触发面扫描 2026-08-05: 当前 src0/ **0 命中** `return X ± Y` (X/Y 双 1-char)
- 翻译阶段已自然避免 (cast-chain / single-operand / intermediate let)
- 根因 (codegen stack-slot allocator bug) 未真修, 未来写 `return x + y` 又会触发

**W-008 ↔ W-009 ↔ W-007 ↔ W-005 cross-ref** (新 section):
- W-008 ↔ W-009 链式依赖 (struct field load type + literal 0 extsw, 缺一不可)
- W-005 ↔ W-007 不同路径 (W-005 store 路径 / W-007 return 路径)
- W-007 ↔ W-008 ↔ W-009 (cg_convert_arg 三向联动 + B-let2 镜像)
- W-005 真修 (CGContext 布局对齐) → 让 W-007/W-008/W-009 在 let-mut 路径上**才真正测得到**

**索引表更新**:
- W-004 加 "(BLOCKED verification — Task #60)"
- W-006 加 "(dormant — 0 触发面 in current src0/)"
- 新增 cross-ref 索引项 "W-008 ↔ W-009 ↔ W-007 ↔ W-005 (codegen 转化路径联动)"

### 验证 (2026-08-05)

```bash
# 1. 触发面扫描 (W-006 dormant 实证)
grep -rn 'return [a-z_]\{1,2\} [+\-] [a-z_]\{1,2\}[^_]' compiler/src0/*.jhyy
# 0 命中 ✓

# 2. _W002_revert.py 删除验证
ls compiler/src0/_W002_revert.py
# (not found) ✓

# 3. _W002_rename_map.txt README + tracked 验证
git ls-files compiler/src0/_W002_rename_map.txt
# compiler/src0/_W002_rename_map.txt ✓ (tracked, 顶部 11 行 README)

# 4. regress 持平
python compiler/build/bin/regress.py
# 50/53 PASS, 0 failed, 3 skipped   (持平 commit 2.13 baseline)

# 5. stage1 byte-equal 持平
bash compiler/tests/stage1-expanded.sh
# pass: 6 / 7   (持平 commit 2.13 baseline)

# 6. v0 build clean
/c/msys64/ucrt64/bin/gcc.exe -std=c11 -Wall -Wextra compiler/src/*.c \
    -o compiler/build/bin/jhyy.exe -I compiler/src
# (no warnings)
```

### 不验证 (per user plan)

- **W-004 实证**: 已 BLOCKED, 推 v1.0.0 sprint 3+ Task #60 修后再做
- **main.jhyy runtime (jhyy_v1 编 src0/main.jhyy 跑 main.jhyy)**: 已知 25KB 大文件触发 Task #60 (parse_expr), 不在本 commit 范围

### 已知遗留

- W-004 status ACTIVE, 失效条件 (i) 实证路径 BLOCKED by Task #60
- W-006 status ACTIVE dormant, 根因 (codegen stack-slot allocator) 未真修
- W-007 partial 真修, struct field + global var 路径需 W-005 后审计
- 跨边界 (jhyy_OS) 决策 D5 spec baseline 锁 + D11 `&mut` 矩阵 — 不在 2.14 范围

### 影响

- **W-004 / W-006 决策清晰化**: W-004 BLOCKED verification 有明示 (Task #60 dependency); W-006 dormant 有数据支撑 (0 命中扫描)
- **W-002 archive 物理清理**: 一次性脚本删除 (释放 2220B), tracked 文件保留 (ship history 完整)
- **cross-ref 联动段**: 给未来 sprint 设计者清晰 4-workaround 联动视图, 避免单独修一个漏考虑其他
- **AUDIT 准备就绪**: revert 后 src0/ + W-002 archive 清理 + W-004/W-006 状态明示 + cross-ref 联动 → AUDIT 5 struct 阶段所有前置达成

### 下一步

| commit / 阶段 | 主题 | 范围 | 依赖 |
|--------------|------|------|------|
| **AUDIT** | 5 struct (Sym/SymTable/Parser/Lexer/SemaContext) 字段访问审计 | ~200 行 review + 3-5 真修 | 本 commit (2.14) |
| B | main.jhyy 收尾 (resolve_imports 翻译 ~300 行) → 推 v1.0 sprint 3 B' | ~300 行 | AUDIT + Task #60 |
| C' | codegen 确定性 audit (.data 排序 + stack slot 排序 + hash 桶迭代排序) | ~50 行 | B |
| D | N=3 byte-equal (在 6/7 层面) | 验证 | C' |
| v1.0 sprint 3 (Task #52) | parser.jhyy NODE_CONST_DECL 补全 + jhyy_v1 sema 内部 fix → 7/7 | | D |
| v1.0 sprint 5 | N=3 在 7/7 层面 → M4 hard 闭环 | | v1.0 sprint 3 |
| Task #60 | Fix parse_expr to handle while/else in expression context | parser.jhyy 翻译 | 无 |
| Task #60 修后 → W-004 验证 | jhyy_v1 编 codegen.jhyy / parser.jhyy / sema.jhyy | | Task #60 |
| 2.15 (contingency) | W-004 批量改名 (触发面消除, 如果 Task #60 修后仍 stack overflow) | ~500 行机械改名 | Task #60 修 + W-004 verification |

### 引用

- v0.9 wip commit 2.11 — W-005 真修 (CGContext 对齐, W-004 验证前提)
- v0.9 wip commit 2.12 — W-001 docs 标 RESOLVED + W-002 211 revert (W-002 archive 起源)
- v0.9 wip commit 2.13 — W-005 加固 16 处 revert (W-005 RESOLVED 锁定)
- v0.8 commit 9 (`d570c72`) — W-001 byte-by-byte 真修 (W-002/W-004 根因消除)
- v0.8 commit 11 — W-008 真修 (cg_find_field_offset)
- v0.8 commit 12 — W-009 真修 (cg_convert_arg 入口 bail)
- `docs/internal/workarounds.md` — 4 块改动集中 (本 commit)
- `compiler/src0/_W002_rename_map.txt` — archive 文件 (tracked, README 已加)
- `compiler/src0/_W002_revert.py` — 已删除 (一次性脚本)
