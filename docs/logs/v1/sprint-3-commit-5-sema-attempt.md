# Sprint 3 commit 5 — sema.jhyy 翻译（首次尝试 + 已知未通过）

**日期**: 2026-06-28
**对应 plan**: [`../../plans/v1/v1.0.0详细实现方案.md`](../../plans/v1/v1.0.0详细实现方案.md) § 3.4
**状态**: ⚠️ **部分完成 + 已知未通过测试**

## 目标

Sprint 4 提前开 codegen 需要先过 sema（sprint 3 commit 5 提前到本 sprint）：
翻译 `compiler/src/sema.c`（约 1100 行）到 `compiler/src0/sema.jhyy`，
覆盖 49 个 NodeKind 的类型推断 + 错误检查 + match 穷尽性检查 + let mut 检查。

C 端参考 `compiler/src/sema.c`。

## 实现

### 1. 翻译范围

- `sema_init` / `sema_check` —— 顶层 API
- `check_module` —— 3-pass：register decls → resolve type decls → check bodies
- `check_func_decl` —— 参数 + 返回类型 + 函数体类型检查
- `infer_type` —— 全部 NodeKind 分支（int/float/string/char/bool/ident/unary/binary/cast/deref/index/call/field/array_lit/slice_lit/slice_expr/sizeof/alignof/block/if/let/assign/return/break/continue/match/match_arm）
- `resolve_type_node` —— ident / unary (ptr) / array_type / slice_type
- `process_match_pattern` —— pattern ident / enum variant / tuple（带 variant payload type 解析）
- `process_match` —— 检查 match arms 穷尽性（7A）

### 2. 公共代码

- `sema_error_int / _int2 / _str / _str_int` —— 4 个变体走 StringBuilder 拼接 + jh_fputs_stderr
- `sema_push_scope / sema_pop_scope` —— SymTable 嵌套 + arena_alloc
- `sema_local_at / _sym / _type / _set` —— locals[] 数组 offset 访问（256 × 16 bytes 外置）
- `SemaContext` —— 80 bytes struct（10 字段，scope_depth + loop_depth 用 i32 + 4 pad）

### 3. symtab 增量（v0.7 7A 配套）

- `sym_enum_variants(t_raw, enum_name, out, max_variants)` —— 遍历 SymTable.entries，收集 `kind=SYM_VARIANT && module==enum_name` 的 sym，写到 out 数组，返回数量
- 调用方：sema 7A match 穷尽性检查、enum 字段收集

### 4. 测试驱动

`_driver_sema.jhyy` 8 个测试：
| Test | 验证 |
|------|------|
| T0 | smoke：sema_init 不崩 |
| T1 | 有效函数（`let x: i32 = 42; return x;`）→ 0 errors |
| T2 | 未定义变量 → 1+ errors |
| T3 | struct layout → 0 errors + Point sym 存在 |
| T4 | enum variants → 0 errors + Color sym KIND_ENUM + nvariants=3 + sym_enum_variants=3 |
| T5 | match 非穷尽 → errors > 0 |
| T6 | match 穷尽（有 `_`）→ 0 errors |
| T7 | let mut 可赋值 / let 不可赋值（v0.6.5 patch） |

退出码 42。T1-T7 每 test fresh arena（`arena_free → arena_init → sema_init`）避免 cross-test state。

## 已知未通过

### 🐛 Bug 1: T1 fail —— `return x;` 报 "undefined variable"

**症状**：T1 跑 `fn main() -> i32 { let x: i32 = 42; return x; }`，
sema 输出 `test.jhyy:1:27: error: undefined variable`，DBG 显示 name=x。

**预期**：NODE_LET 处理时应 `sema_local_set(locals, nlocals, x_sym, i32)` 然后 `nlocals++`，
返回语句 `infer_type(NODE_IDENT x)` 应在 locals 倒序搜索找到 x_sym。

**调查方向**：
- 已确认 `(*d).sym` 读到正确的 sym 指针（非 NULL）
- 已确认 type_annot/init 字段读到正确值
- 已确认 `(*ctx).nlocals` 字段读到的不是预期值（nlocals_before debug 输出后 segfault）
- 怀疑 `sema_local_set` 写入 `(*ctx).locals[i]` 触发的 segfault 在 arena 边界外

**可能根因**（待验证）：
1. SemaContext 80 bytes 字段对齐错了 —— jhyy struct 实际 layout vs C 端 layout 不一致
2. `(*ctx).locals` 指针被 arena_reset 后 sema_init 重新分配，但 jhyy codegen 把 locals 字段误读为 nlocals 或相邻字段
3. arena_alloc 大块（4096 bytes for 256 locals）触发了 jhyy 编译器在 amd64_win backend 的 stack spill bug

**建议下一个 sprint**：
- 写 `_test_sema_minimal.jhyy` 手动调 `sema_local_set` + `sema_local_sym` 验证 round-trip
- 验证 SemaContext 字节数：实际 `sizeof` vs 预期 80
- 怀疑是 arena 大块 spill，加 fallback 用 64 locals（1024 bytes）测

### 🐛 Bug 2: T4 间歇性 segfault（之前 session 修过）

**症状**：`fn main() -> i32 { type Color = enum { Red, Green, Blue } return 0; }`
单跑 T4 OK，但 T3 → T4 顺序跑会 segfault 在 post-Pass2 lookup。

**临时 workaround**（已撤回）：删 post-Pass2 lookup 诊断代码后 T4 errs=0。
但当前 T1 也 fail，所以 T3/T4 顺序下的稳定性无法验证。

## 代码量

| 文件 | 状态 | 行数 |
|------|------|------|
| compiler/src0/sema.jhyy | **新增**（带 bug） | ~1670 |
| compiler/src0/_driver_sema.jhyy | **新增** | 273 |
| compiler/src0/symtab.jhyy | 修改（+sym_enum_variants） | +37 |

## 验证

- ✅ `python regress.py` **47/50 passed, 0 failed, 3 skipped**（未引入新失败 — C 编译器测试不受影响）
- ❌ `_driver_sema.jhyy` T1 FAIL（"undefined variable" for `x`）
- ⏸ T2-T7 未独立验证（T1 fail 阻断后续 tests 顺序依赖）

## 下一步

1. 修 SemaContext struct layout / locals 数组 round-trip（Bug 1）
2. T1 pass 后独立验证 T2-T7
3. 重新跑 byte-equal oracle 验证 sema 翻译对齐 C 端
4. Sprint 4 才进 codegen.jhyy 翻译

## 提交策略

本次 commit 提交的是 **sprint 3 commit 5 首次尝试 + 已知未通过**。
目的：保存 translation progress + 文档化 bug，避免后续 sprint 从零开始。
后续 fix sprint 单独提交（不在本 commit 范围）。