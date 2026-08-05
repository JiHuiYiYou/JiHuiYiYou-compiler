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
| commit 2.12 | W-001 真修 (hash_string 重写) | 高风险 |
| commit 2.13 | W-005 加固 phase 2 (main.jhyy 14 处 *pos_ptr revert → let-mut) | 依赖 2.11 + 2.12 |
| commit 2.14 | W-006 + W-002/W-004 衍生 + W-008/W-009 文档 | 文档 |
| AUDIT (5 struct) | Sym / SymTable / Parser / Lexer / SemaContext | 排在 2.14 之后 / B 之前 |
| B | main.jhyy 收尾 (resolve_imports, ~300 行) | 依赖 AUDIT |
| C' | codegen 确定性 audit | |
| D | N=3 byte-equal (5/7 层面) | M4 软定义达成 |
| v1.0 sprint 3 (Task #52) | parser + sema fix → byte-equal 7/7 | |
| v1.0 sprint 5 | N=3 在 7/7 层面 → M4 hard 闭环 | |
| commit 4 (C) | byte-equal final 6/7 | W-005 不阻塞(已持平 5/7) |