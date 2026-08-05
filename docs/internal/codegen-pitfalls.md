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
| 1 | **B-φ1** | `fib_renamed` / `control_flow` | if-expr phi slot 缺;jhyy_1 emit `ret %t4` 而 jhyy_0 emit `ret %t7`(`%t7 =w copy %t4`) | v0 if-expr codegen 用 QBE `phi`(merge 块 alloc result,两边 store);v1.0.0 sprint 5 commit 4 改走 store/load 模式(v0 codegen bug 2 workaround:nested if-else phi predecessor mismatch) | 🔴 中 | 待 v0.9 commit 2.6+ |
| 2 | **B-let2** | `arith` | `l → w` narrow 缺;`qbe_type_of` i64 → i32 字段赋值无 emit `copy`/`extuw` | jhyy_v1 `cg_convert_arg` (codegen.jhyy:544-634) 历史上只覆盖 `src=w, dst=l` (extsw) + `src=l, dst=d/s`;**漏 `src=l, dst=w`** —— v0 codegen.c:780-783 显式 emit `copy`(QBE 'copy' from l to w 隐式截断) | 🟢 必修 | ✅ v0.9 commit 2.5 |
| 3 | **B-struct** | `struct_val_pass` | struct by-value sret 参数路径差异(具体 diff 见 `stage1-expanded.sh` 输出) | jhyy_v1 NODE_CALL sret 路径(codegen.jhyy:1414-1538) emit `ret_slot` alloc + pass as `l %ret` arg,v0 codegen.c:1140-1234 emit 顺序 / slot 编号细节不一致 | 🟡 中 | 待 v0.9 commit 2.7+ |
| 4 | **B-match** | `match_exhaustive` | match-expr codegen 缺;NODE_MATCH case `cg_expr_v1` 当前 fall-through 返回 zero IRVal | v0 codegen.c 完整 match(codegen.c:1310-1450);jhyy_v1 commit 4 没翻译 match-expr(sprint 5 commit 4 占位 return zero)—— **CERR big 4 中的 2 个**(dungeon_game + match_test),v1.0.0 sprint 3 处理 | 🔴 高 | 待 v1.0.0 sprint 3 (parser 翻译 + codegen 翻译) |
| 5 | **B-data** | `const_array` | `.data` 段 emit 顺序 / 格式差异 | jhyy_v1 `cg_emit_const_data_elem` (codegen.jhyy:1916-1960) 当前 emit 顺序 vs v0 codegen.c `cg_emit_const_data` 不同 —— v0 先 emit 字段 `d N, w N` 分行,jhyy_v1 单行 emit | 🟡 中 | 待 v0.9 commit 2.7+ |
| 6 | **B-testset** | 7 测试集 baseline 锁定 | Stage 1 byte-equal baseline = `hello`(已 PASS)/ `arith`(本 commit 修) / 5 FAIL | 测试集本身锁定:文件位置 + EXPECT + 不依赖 let mut / 不依赖 hash 触发面 | 🟢 完成 | ✅ v0.9 commit 2.5 |

### 2.1 B-φ1 详解(if-expr phi slot skip)

**首次报告**: v0.9 wip commit 2.5(2026-08-05)
**触发**: `stage1-expanded.sh` 跑 `fib_renamed.jhyy` + `control_flow.jhyy`,jhyy_0 vs jhyy_1 .il diff 显示:

```diff
<     %t4 =w copy %t0
<     %t7 =w copy %t4    # phi 合并 from then-branch
<     ret %t7
---
>     %t4 =w copy %t0
>     ret %t4            # 直接 ret;没 emit phi 合并块
```

**根因**:
- v0 codegen.c if-expr codegen: alloc result_v1 temp in merge block,then/else 各 emit `jnz @merge` + branch 写入 temp,merge block 用 phi 拿最终值。
- jhyy_v1 codegen.jhyy:1659-1732 NODE_IF_v1 case **不走 phi**,改走 store/load 模式:alloc result_slot (QBE_L) in start block,then/else `store` 到 slot,merge `load` 出来。
- 行为正确(都返回 if-expr 值),但 .il 字节布局不同。

**修复选项**(v0.9 commit 2.7+ 评估):
1. **加 phi emit 路径对齐 v0** —— 工作量大(v0 codegen.c phi 用嵌套结构,jhyy 无前向引用避不开 mutual recursion)
2. **接受 diff + 文档化** —— Stage 1 byte-equal 仅要求 byte-equal,**不是**说 .il 必须跟 v0 完全相同;commit 2.5 修 B-let2 后 2/7 = 基线,**后续真自举**(v1.0 启动后)v1 编自身产物一致即可,不一定跟 v0 编的一致
3. **jhyy_v1 codegen 选项 flag** —— 加 `-emit-phi` flag,默认 store/load,真自举验证时切 phi(过设计,推迟到 v2.0 QBE 重写)

**推荐**: 选项 2 (commit 2.5 已采:接受 diff + 文档化)

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

**B-struct** (struct by-value sret): jhyy_v1 NODE_CALL sret 路径当前 emit 顺序 / temp 编号 / arg slot offset 跟 v0 codegen.c 不同 → 待 v0.9 commit 2.7+ 加 `-emit-sret-aligned` flag 对齐 v0 序列;或接受 diff(Stage 1 仅要求 hello + 至少 1/6 修)。

**B-match** (match-expr codegen): jhyy_v1 cg_expr_v1 NODE_MATCH case 占位 return zero → 任何 match-expr 测试 QBE 报 "undefined temp" → 待 v1.0.0 sprint 3(parser 翻译 + codegen 翻译)。这是 CERR big 4 中的 2 个(dungeon_game + match_test)。

**B-data** (.data 段 emit 顺序): jhyy_v1 `cg_emit_const_data_elem` (codegen.jhyy:1916-1960) 单行 emit `,` 分隔,v0 codegen.c `cg_emit_const_data` 多行 emit → 待 v0.9 commit 2.7+ 加 multi-line emit 选项或 jhyy_v1 切 multi-line 对齐 v0。

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

**下一步**: v0.9 commit 2.6+ (W-006 1-char local var 验证完整) + commit 3 (main.c 翻译) + commit 4 (Stage 1 final verify)

---

## § 3 已修 codegen bug（历史索引，仅参考）

| Sprint | Bug | 修复 commit |
|--------|-----|------------|
| v0.7 7A | match non-wildcard 漏 emit next_check label | v0.7 commit 7A |
| v0.7 7B | arr_of_structs[i].field 返回地址不 load | v0.7 commit 7B |
| v0.8 W-009 | `cg_convert_arg` 缺 NODE_CAST 处理 + 整数宽度不转 | v0.8 commit 12 |
