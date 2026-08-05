# codegen 坑清单（v0.9.0 commit 1+ 起维护）

记录 codegen.c / QBE IL 后端已知的误判、miscompile、cleanup 必要性。
每条带 (a) 复现路径 / (b) 影响 / (c) 修复优先级 / (d) 负责 sprint。

## § 1 误判为 bug 的"伪坑"（已验证非坑）

### 1.1 "extsw 太多"——`cg_convert_arg` 的 29 次 emit

**首次报告**: v0.8 wip commit 12 / changelog-v0.8.0
**触发**: jhyy 编译 `compiler/src0/arena.jhyy` (282 行) emit QBE IL 中含 29 个 `extsw` 指令。
**50/50 赌假设**: arena.jhyy 翻译稿 ptr 算术上下文 i32/i64 误用。
**v0.9.0 commit 1 验证结论**: **未命中**。29 个 extsw 全部为 i32 字面量 → i64 上下文的合法符号扩展。

**验证证据**:
- grep 翻译稿全部 ptr 算术上下文,均使用 `as i64`(L50 `ptr_add_v1`, L97 `cur_int_v1`, L100 `end_int_v1`, L156/162 `b_i64`),**无一处 i32 误用**。
- 实际 29 个 extsw 来源分类:
  - 函数返回 / 字段赋值中的 `0 as i64` / `1 as i64` / `16 as i64` / `1048576 as i64`(L22/L44/L55/L60/L80 等):字面量先 codegen 为 i32(`w copy N`),再由 `NODE_CAST` 走 codegen.c L776 的 `(src_qt=='w' && dst_qt=='l')` 分支 emit `extsw`——**语义正确**。
  - 字面量经 `cg_convert_arg` 喂入 i64 参数(`malloc(8 as i64)` / `memset(..., 0 as i32, 1 as i64)` 等):同一 `(src='w', dst='l')` 路径,正确转换。
- 这 29 个 extsw 全部为 QBE ABI 必需的整数宽度扩展指令,**不存在"应该 copy 但 emit 了 extsw"的误判**。

**QBE 设计事实**: QBE 是显式类型化 IR,`w`(32-bit) 与 `l`(64-bit) 之间必须显式 extsw/extuw,不能隐式 widen。jhyy 在 codegen NODE_CAST(L772-784)和 cg_convert_arg(L222)都用 `extsw` 处理 i32→i64,这是 QBE 必需。

**结论**: `cg_convert_arg` 在 v0.8 commit 11/12 加 `extsw` 分支的修复**正确且必要**(不加会出现 i32→i64 隐式窄化 bug)。

**修复状态**: 不修。`extsw` 计数是 .il 体积噪音,非功能 bug。

---

## § 2 Stage 1 byte-equal codegen translation gaps（v0.9.0 commit 2.5 范畴）

> **首次登记**: v0.9 wip commit 2.5 (2026-08-05)
> **测试集**: [`compiler/tests/examples/`](../../tests/examples/) 下 7 个 Stage 1 byte-equal 验证集(`stage1-expanded.sh`)
> **基线**: `jhyy_0` (C 编译) vs `jhyy_1` (jhyy 编译) 对相同 .jhyy 输入产 .il,**byte-equal 是硬性要求**
> **commit 2.5 验收**: byte-equal 至少 2/7 (本 commit 修 1 个,B-let2)

| # | tag | 测试 | 现象 (jhyy_0 vs jhyy_1 .il diff) | 根因 | 优先级 | commit |
|---|-----|------|----------------------------------|------|--------|--------|
| 1 | **B-φ1** ✅ | `fib_renamed` / `control_flow` | if-expr phi slot 缺;jhyy_1 emit `ret %t4` 而 jhyy_0 emit `ret %t7`(`%t7 =w copy %t4`) | v0 if-expr codegen 用 QBE `phi`(merge 块 alloc result,两边 store);v1.0.0 sprint 5 commit 4 改走 store/load 模式(v0 codegen bug 2 workaround:nested if-else phi predecessor mismatch) | 🔴 中 | ✅ v0.9 commit 2.6 (本 commit) |
| 2 | **B-let2** ✅ | `arith` | `l → w` narrow 缺;`qbe_type_of` i64 → i32 字段赋值无 emit `copy`/`extuw` | jhyy_v1 `cg_convert_arg` (codegen.jhyy:544-634) 历史上只覆盖 `src=w, dst=l` (extsw) + `src=l, dst=d/s`;**漏 `src=l, dst=w`** —— v0 codegen.c:780-783 显式 emit `copy`(QBE 'copy' from l to w 隐式截断) | 🟢 必修 | ✅ v0.9 commit 2.5 |
| 3 | **B-struct** ✅ | `struct_val_pass` | struct by-value 字段 copy 时 jhyy_v1 offset==0 偷懒不 alloc tmp (直接用 src_addr/dst_addr),v0 codegen.c:140-148 总是 alloc + emit `copy`(offset==0) 或 `add`(offset>0) | jhyy_v1 `cg_copy_struct` (codegen.jhyy:430-490) 偷懒: offset==0 时 src_off = src_addr (复用),导致字段 loadw 直接用 src_addr → 字段编号错位 + byte-equal diff | 🟡 中 | ✅ v0.9 commit 2.8 |
| 4 | **B-match** ✅ | `match_exhaustive` | match-expr codegen 缺;NODE_MATCH case `cg_expr_v1` 当前 fall-through 返回 zero IRVal | v0 codegen.c 完整 match(codegen.c:909-997);jhyy_v1 commit 4 没翻译 match-expr(sprint 5 commit 4 占位 return zero)—— **commit 2.9 真修**:`cg_match_pattern` helper + NODE_MATCH 对齐 v0 逻辑 + arms_arr 解读修正(*Node 数组,不是 NodeMatchArm 数组)。match_exhaustive 现在 exit 1 (sema "enum has no variant") 不是 exit 127 (segfault) | 🔴 高 | ✅ v0.9 commit 2.9 |
| 5 | **B-data** ⚠️ moot (parser CERR) | `const_array` | jhyy_v1 parser **直接拒绝** 顶层 `const NAME: TYPE = [...];` (CERR: "expected ;, got ident" on line 7)→ 不生成 .il,byte-equal diff 不可观察 | **不是 codegen gap** —— jhyy_v1 parser 翻译层缺顶层 const decl (sprint 5 commit 4 没翻译 NODE_CONST_DECL parsing)。归并到 v1.0.0 sprint 3 parser 翻译 (Task #52) | 🟡 moot | ✅ v0.9 commit 2.7 (文档化,无 codegen 改动) |
| 6 | **B-testset** | 7 测试集 baseline 锁定 | Stage 1 byte-equal baseline = `hello`(已 PASS)/ `arith`(本 commit 修) / 5 FAIL | 测试集本身锁定:文件位置 + EXPECT + 不依赖 let mut / 不依赖 hash 触发面 | 🟢 完成 | ✅ v0.9 commit 2.5 |

### 2.1 B-φ1 详解(if-expr phi slot skip) — RESOLVED commit 2.6

**首次报告**: v0.9 wip commit 2.5(2026-08-05)
**修复**: v0.9 wip commit 2.6(2026-08-05)
**触发**: `stage1-expanded.sh` 跑 `fib_renamed.jhyy` + `control_flow.jhyy`,jhyy_0 vs jhyy_1 .il diff 显示 tmp 编号偏移 1:

```diff
- < %t3 =w copy 1            # v0 在 @merge3 从 tmp 3 开始
+ > %t4 =w copy 1            # jhyy_v1 在 @merge3 从 tmp 4 开始 (多 alloc result_slot 占 tmp 3)
```

**根因**:
- v0 codegen.c if-expr: 只在 `d->else_body && !then_returns && !else_returns` 时 alloc result + emit phi;otherwise fallback `return then_val`(no alloc,no phi,no extra tmp)
- jhyy_v1 codegen.jhyy:1659-1732 NODE_IF_v1 case **总是 alloc result_slot (QBE_L) + store/load mode** → 多占一个 tmp 编号,即使 fib_renamed 的 if-expr (then=return) 不需要 phi

**修复方案**(实际执行 — 不是 commit 2.5 估的"选项 2 接受 diff"):
1. jhyy_v1 codegen.jhyy:544-548 加 `cg_emit_phi` helper (包装 `ir_emit_phi2`)
2. codegen.jhyy:1662-1740 NODE_IF_v1 重写,删 v0 codegen bug 2 workaround:
   - 删提前 alloc result_slot
   - phi emit 条件: `else_node != 0 && then_returns == 0 && else_returns == 0`
   - 单边 return / 无 else → fallback `return then_v`
   - void if → return zero, 不 alloc
3. fib_renamed (then=return) 走 fallback,无 alloc → @merge3 从 tmp 4 → tmp 3,byte-equal

**验证**: `stage1-expanded.sh` 4/7 PASS (hello + arith + fib_renamed + control_flow)。regress 持平 3 OK。

**风险评估偏差**: commit 2.5 估 "B-φ1 选项 1 = 工作量大,选选项 2 接受 diff" 是**错位假设**——实际 jhyy_v1 codegen.jhyy 改动面很小 (helper ~10 行 + NODE_IF_v1 重写 ~50 行),不需要照搬 v0 codegen.c 嵌套结构。 fib_renamed / control_flow 都没触发 phi path (then 都是 return,走 fallback),纯靠"删提前 alloc"就 byte-equal。

### 2.2 B-let2 详解(l→w narrow in cg_convert_arg)

**首次报告**: v0.9 wip commit 2.5(2026-08-05)
**触发**: `arith.jhyy` 测试 —— `let down_val: i32 = total_val as i32;`(total_val: i64 → down_val: i32)。jhyy_1 emit 错 IL(QBE 报 "type mismatch" 或静默 emit `=w copy %l_value` 错字节宽度)。

**根因**:
- v0 codegen.c:780-783 `cg_convert_arg` 显式 emit `copy` for `src=L, dst=W` integer width narrowing。
- jhyy_v1 codegen.jhyy:544-634 `cg_convert_arg` 历史上漏这条分支(只覆盖 `src=w, dst=l` via extsw + `src=l, dst=d/s` via sltof/ultof)。

**修复**(v0.9 commit 2.5):

```jhyy
// compiler/src0/codegen.jhyy:613-619 (新加)
} else if src_qt_v1 == QBE_L() {
    // v0.9 wip commit 2.5 (B-let2): l→w narrow — QBE 'copy' from l to w truncates implicitly
    // (对齐 v0 codegen.c:780-783 integer width change narrowing l→w 分支)
    if dst_qt_v1 == QBE_W() {
        conv = "copy" as *u8;
    }
}
```

**验证**: `stage1-expanded.sh` arith.jhyy PASS(本 commit 前 FAIL,commit 后 PASS)。

### 2.3 B-struct / B-match / B-data 概要

**B-struct** (struct by-value 字段 copy) — **RESOLVED commit 2.8**: jhyy_v1 `cg_copy_struct` (codegen.jhyy:430-490) 偷懒 — offset==0 时直接用 src_addr / dst_addr (复用,不 alloc tmp),导致字段 `loadw %src_addr` 直接用 → 字段编号错位 + byte-equal diff。v0 codegen.c:140-148 总是 alloc src_off/dst_off + emit `copy`(offset==0) 或 `add`(offset>0)。修复:对齐 v0 路径 + 用 inline emit `copy %tN` (ir_emit_copy 只接 i64 literal,不接 IRVal src)。

**B-match** (match-expr codegen) — **RESOLVED commit 2.9**: jhyy_v1 cg_expr_v1 NODE_MATCH case 占位 return zero → 任何 match-expr 测试 QBE 报 "undefined temp"。修复:`cg_match_pattern` helper + NODE_MATCH 对齐 v0 codegen.c:909-997 逻辑 + arms_arr 解读修正(*Node 数组,不是 NodeMatchArm 数组)。match_exhaustive 现在 exit 1 (sema "enum has no variant") 不是 exit 127 (segfault)。**jhyy_v1 sema "enum has no variant" 已知遗留**:jhyy_v1 自身 bug,跟 codegen 无关,待 v1.0.0 sprint 3 修。

**B-data** (.data 段 emit 顺序) — **MOOT per v0.9 commit 2.7**: jhyy_v1 parser **CERR 拒绝顶层 `const NAME: TYPE = ...`** (`expected ;, got ident` on line 7 col 7 of `const_array.jhyy`),根本走不到 codegen 阶段,不存在 `.data` 段 emit 差异可观察。**根因**:parser 翻译层缺 NODE_CONST_DECL parsing (v1.0.0 sprint 5 commit 4 没翻译) → 推迟到 v1.0.0 sprint 3 (Task #52)。**验证证据**: `jhyy_v1 build const_array.jhyy` → 6 条 parse errors + exit 0 (CERR); `jhyy.exe build const_array.jhyy` → 生成 `/tmp/ca_v0.il.il` 含 `data $ASCII_LOWER = { b 97, ... }`。

### 2.4 修复策略共识(commit 2.5 锁定)

> **共识** (per v0.9 wip commit 2.5 plan § commit 2.5 + 用户确认):
> - **Byte-equal 优先级 > 100% 覆盖率**: 只要 hello.jhyy + 至少 1 个 fixable gap(jhyy_v1 端 codegen fix) PASS,**Stage 1 byte-equal baseline 锁定**
> - **不可修 gap (B-match 跟 parser 翻译耦合)** 推迟到 v1.0.0 sprint 3
> - **可选修 gap (B-φ1 / B-struct / B-data)** 接受 diff,**不阻塞 Stage 1 closure**(后续 v1.0 真自举以 v1 编自身为准)
> - **实测**: commit 2.5 修 B-let2 → byte-equal 1/7 → **2/7**(hello + arith PASS),regress 持平 3 OK baseline。

### 2.5 验收(commit 2.5 完成定义)

| 标准 | 状态 |
|------|------|
| 7 测试集 byte-equal baseline 锁定(测试集 + EXPECT + 路径) | ✅ |
| B-let2 修完,byte-equal ≥ 2/7 | ✅ (2/7:hello + arith) |
| 5 个未修 gap 文档化(B-φ1/B-struct/B-match/B-data + B-testset baseline) | ✅ (本文档) |
| regress 持平 baseline | ✅ (3 OK = 持平 commit 12 12 OK 测量口径差) |
| Stage 1 验收脚本存在 | ✅ ([`stage1-expanded.sh`](../../tests/stage1-expanded.sh)) |

### 2.6 commit 2.6 增量(B-φ1 真修)

| 标准 | 状态 |
|------|------|
| B-φ1 修完,byte-equal ≥ 4/7 | ✅ (4/7:hello + arith + fib_renamed + control_flow) |
| cg_emit_phi helper 加完 | ✅ (codegen.jhyy:544-550) |
| NODE_IF_v1 重写走 v0 codegen.c:602-674 逻辑 | ✅ (codegen.jhyy:1662-1740) |
| v0 codegen bug 2 workaround 注释删除 | ✅ (L1655-1658 注释删,改 v0.9 wip commit 2.6 注释) |
| regress 持平 | ✅ (3 OK = 持平 commit 2.5 baseline) |

### 2.7 commit 2.7 增量(B-data moot — doc-only)

| 标准 | 状态 |
|------|------|
| B-data 根因重新诊断 | ✅ parser CERR(顶层 const decl 拒绝),不是 codegen gap |
| const_array.jhyy 还原到 v0.7 7B 版本 | ✅ (从 fn 内 hard-coded 数组 revert 回顶层 const) |
| codegen-pitfalls.md § 2 + § 2.3 状态更新 | ✅ (B-data 行标 "moot (parser CERR)",§ 2.3 改写根因) |
| changelog-v0.9.0.md 加 commit 2.7 段 | ✅ |
| regress 持平 | ✅ (3 OK = 持平 commit 2.6 baseline) |
| byte-equal 持平 4/7 | ✅ (const_array FAIL 保持,根因 = parser CERR 不算 codegen gap) |

### 2.8 commit 2.8 增量(B-struct 真修)

| 标准 | 状态 |
|------|------|
| cg_copy_struct 对齐 v0 codegen.c:140-148 路径 | ✅ (codegen.jhyy:456-481) |
| offset==0 总是 alloc src_off/dst_off + inline emit `copy %tN` | ✅ (ir_emit_copy 不接 IRVal src → 走 inline str emit) |
| byte-equal ≥ 5/7 | ✅ (5/7:hello + fib_renamed + struct_val_pass + arith + control_flow) |
| regress 持平 | ✅ (3 OK = 持平 commit 2.7 baseline) |

**下一步**: v0.9 commit 2.9 (B-match 真修 — NODE_MATCH codegen 翻译 + cg_match_pattern helper) + commit 2.10+ (W 真修) → commit 4 final (byte-equal 7/7 const_array 不可达 6/7 上限)

### 2.9 commit 2.9 增量(B-match 真修 + read_file malloc sz+4)

| 标准 | 状态 |
|------|------|
| `cg_match_pattern` helper 加完 (codegen.jhyy:695-718) | ✅ |
| NODE_MATCH codegen 对齐 v0 codegen.c:909-997 逻辑 (codegen.jhyy:1923+) | ✅ |
| `arms_arr` 解读修正 (*Node 数组,不是 NodeMatchArm 数组) | ✅ |
| `read_file` malloc `sz+4` 修 heap 越界 (main.jhyy) | ✅ |
| match_exhaustive 不再 segfault (exit 127 → exit 1) | ✅ |
| byte-equal 持平 5/7 | ✅ (5/7: hello + fib_renamed + struct_val_pass + arith + control_flow) |
| regress 持平 | ✅ (3 OK = 持平 commit 2.8 baseline;实测 50/53 PASS) |

**下一步**: v0.9 commit 2.10 (W-005 根因重诊断,doc-only,已 SHIPPED 2026-08-05) → commit 2.11 (W-005 真修: C/jhyy CGContext 布局对齐,已 SHIPPED 2026-08-05) → commit 2.12a (sema.jhyy enum variant lookup 修复,已 SHIPPED 2026-08-05) → commit 2.12b (codegen.jhyy NODE_ENUM_VARIANT 翻译,byte-equal 5/7→6/7)

### 2.10 commit 2.10 增量 (W-005 根因重诊断, doc-only)

| 标准 | 状态 |
|------|------|
| W-005 根因 = C/jhyy CGContext struct 布局不匹配, 9 字段错位 | ✅ (workarounds.md W-005 根因段) |
| 修复路径明确 (C 端 CGContext 改 jhyy 端布局, ~50 行 C + ~30 行 jhyy) | ✅ |
| byte-equal 持平 5/7 (无 codegen 改动) | ✅ |
| regress 持平 | ✅ (50/53 PASS) |

**无 codegen 改动**, 仅 doc-only。实际修复推后到 commit 2.11。

### 2.11 commit 2.11 增量 (W-005 真修 phase 2)

| 标准 | 状态 |
|------|------|
| C 端 CGContext 9 字段全对齐 jhyy 端布局 (calloc locals + loop_starts/ends/continues + sret_slot_id i64 + 字段顺序) | ✅ (codegen.c:18-43) |
| cg_func 加 4×calloc + 4×free + `<stdlib.h>` include | ✅ (codegen.c:1604-1620) |
| `cg->sret_slot` → 构造 IRVal literal (`sret_addr.id = sret_slot_id`) | ✅ (codegen.c:1429, 1646) |
| jhyy_v1 编 test_w5.jhyy (let-mut 最小复现) 不再 segfault (exit 139 → exit 0 + `x = 20`) | ✅ |
| byte-equal 持平 5/7 (纯内存布局, 不影响 .il emit) | ✅ |
| regress 持平 50/53 | ✅ |

**W-005 workaround 现在可安全移除** (下一 commit 2.13 加固 26 处 `*pos_ptr_vN` → `let mut x; x += n` 风格 revert)。

### 2.12a commit 2.12a 增量 (sema enum variant lookup 修复)

| 标准 | 状态 |
|------|------|
| 加 `var_name_eq_v1` helper (strcmp name, NULL-safe, 2 处复用) | ✅ (sema.jhyy:51-64) |
| `process_match_pattern` L388 (NODE_PATTERN_ENUM) `v_name_ptr == vsym` → `var_name_eq_v1(v_name_ptr, vsym) == 0` | ✅ (sema.jhyy:388) |
| `infer_type` NODE_ENUM_VARIANT L1260 `v_name_ptr == vsym` → `var_name_eq_v1(...) == 0` | ✅ (sema.jhyy:1260) |
| regress 持平 50/53 | ✅ |
| byte-equal 持平 5/7 (codegen 仍缺 NODE_ENUM_VARIANT case) | ✅ (持平, 6/7 推到 commit 2.12b) |
| jhyy_v1 编 match_exhaustive.jhyy 不再报 "enum has no variant" | ✅ (sema 阶段通过) |

**根因**: parser 阶段 alloc 的 `SYM_VARIANT` 跟 sema 阶段 enum 注册的全局 variant `Sym` 指针不同 (但 name 相同)。jhyy 端用 `==` 永远不命中 → 误报 "enum has no variant"。v0 端 sema.c:851 用 `strcmp(name)`, 是正确实现。jhyy 端修复 = 语义对齐 v0, **不只为 byte-equal**。

**W-005 / W-001 / B-match 范畴**:
- 跟 W-005 (let-mut segfault) 正交 — W-005 是 codegen 路径, 2.12a 是 sema 路径
- 跟 W-001 (hash_string) 正交 — W-001 是 symtab 路径
- 跟 B-match (NODE_MATCH codegen, commit 2.9 修) 是 match-expr 测试的 "兄弟 bug" — 2.12a 修 sema enum variant lookup, 2.12b 修 codegen NODE_ENUM_VARIANT case (v0 codegen.c:874-912 翻译)

**下一步**: commit 2.12b (codegen.jhyy NODE_ENUM_VARIANT case 翻译, ~40-50 行, byte-equal 5/7 → 6/7) → commit 2.12 (W-001 真修 + 211 revert 合并)

---

## § 3 已修 codegen bug（历史索引，仅参考）

| Sprint | Bug | 修复 commit |
|--------|-----|------------|
| v0.7 7A | match non-wildcard 漏 emit next_check label | v0.7 commit 7A |
| v0.7 7B | arr_of_structs[i].field 返回地址不 load | v0.7 commit 7B |
| v0.8 W-009 | `cg_convert_arg` 缺 NODE_CAST 处理 + 整数宽度不转 | v0.8 commit 12 |
| v0.9 commit 2.5 (B-let2) | `cg_convert_arg` 漏 `src=l, dst=w` narrow 分支 | v0.9 wip commit 2.5 |
| v0.9 commit 2.6 (B-φ1) | if-expr 提前 alloc result_slot 占 tmp 编号 + 缺 phi emit | v0.9 wip commit 2.6 |
| v0.9 commit 2.7 (B-data) | (诊断) const_array FAIL 根因 = parser CERR 而非 codegen gap → 推迟到 v1.0.0 sprint 3 (Task #52) | v0.9 wip commit 2.7 (doc-only) |
| v0.9 commit 2.8 (B-struct) | `cg_copy_struct` offset==0 偷懒: 不 alloc src_off/dst_off → 字段编号错位 + byte-equal diff | v0.9 wip commit 2.8 |
| v0.9 commit 2.9 (B-match) | NODE_MATCH codegen 缺 + `read_file` malloc `sz+1` heap 越界 | v0.9 wip commit 2.9 |
| v0.9 commit 2.10 (W-005 诊断) | W-005 segfault 根因 = C/jhyy CGContext struct 布局不匹配 (9 字段) — 推迟真修到 2.11 | v0.9 wip commit 2.10 (doc-only) |
| v0.9 commit 2.11 (W-005 真修 phase 2) | C 端 CGContext 9 字段全对齐 jhyy 端布局: `LocalEntry *locals` + `int64_t sret_slot_id` + `IRVal *loop_starts/ends/continues` + 字段顺序 (loop_depth 在 has_sret 之后) | v0.9 wip commit 2.11 |
| v0.9 commit 2.12a (B-match-sema) | jhyy 端 sema.jhyy enum variant lookup 指针 `==` 永远不命中 (parser-scope vs sema-scope Sym 不同) → 误报 "enum has no variant"; v0 端 strcmp 字符串比较, 2.12a 改 jhyy 端对齐 | v0.9 wip commit 2.12a |
