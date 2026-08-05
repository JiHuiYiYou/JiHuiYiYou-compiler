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

## § 2 待验证 / 未分类（v0.9.0 commit 2+ 范畴）

_（待后续 sprint 填充）_

---

## § 3 已修 codegen bug（历史索引，仅参考）

| Sprint | Bug | 修复 commit |
|--------|-----|------------|
| v0.7 7A | match non-wildcard 漏 emit next_check label | v0.7 commit 7A |
| v0.7 7B | arr_of_structs[i].field 返回地址不 load | v0.7 commit 7B |
| v0.8 W-009 | `cg_convert_arg` 缺 NODE_CAST 处理 + 整数宽度不转 | v0.8 commit 12 |
