# v0.8.0 changelog

## 概要

v0.7.0 之后（7A enum first-class + 7B const struct array），v0.8.0 转向 **v1.0.0 phase-2 自举 sprint 4-5 收尾**。v0.8 定位：清理自举路径的剩余卡点，让 `jhyy_0 (C 编译) 编 main.jhyy → jhyy_1` 跑通。

按 v1.0.0 L1 计划：v0.x patch 只修 bug，**不引入新特性**。v0.8.0 同样不引入新语法（enum / const array 等下个 minor version）。

## commit 1（1b86277）：修 3 个自举过程发现的 codegen bug

| bug | 文件 | fix |
|-----|------|-----|
| 11 | `compiler/src/codegen.c:222` | `cg_convert_arg` 加 `else if (src_qt == 'w' && dst_qt == 'l') conv = "extsw";` |
| 12 | `compiler/src0/codegen.jhyy:437` | `cg_copy_struct` FieldDesc.type 改 `fdesc_ptr + 8` |
| 13 | `compiler/src0/codegen.jhyy` | `CGContext.sret_slot: IRVal → sret_slot_id: i64` + 调用处用 IRVal literal |

**Why**：这 3 个 bug 是 sprint 4 翻译 codegen.jhyy 时暴露的 codegen 问题，挡住自举 main.c → main.jhyy 路径。bug 11 是 jhyy 0 codegen 缺 w→l extension（实测触发：i64 变量 > 0 字面量比较）。bug 12 是翻译 bug（FieldDesc 字段 offset 算错）。bug 13 是 v0 codegen 对 first-field-w struct value 的 sret 处理有缺陷（IRVal 有 5 字段），workaround 是把 sret_slot 改 i64 不存 struct。

## commit 2（pending）：翻译 main.c → main.jhyy

**目标**：`compiler/src/main.c` (556 行) → `compiler/src0/main.jhyy` (471 行)

**额外发现 bug 14**：codegen.jhyy 的 `"%c %"` 格式串在 sprintf 实际运行时被吃掉末尾 literal `%`，导致 IL emit 的 function 参数声明缺 `%` 前缀（`w _argc` 而非 `w %_argc`）。QBE 拒绝 `_argc` 作为 valid identifier（"unknown keyword"）。

**fix**：拆成 2 个 emit（`"%c "` 走 ir_emit_int + `"%"` 走 ir_emit_str）。在 codegen.jhyy:1921 加 v0 codegen bug workaround 注释。

**`compiler/runtime/runtime.{c,h}`**：main 改转发 argc/argv 给 main_jhyy（jhyy main 跟 C main 一样要接收 argc/argv，sprint 5 验证需要）。

**`compiler/src0/_driver*.jhyy` (12 个 driver)**：签名 `fn main_jhyy() -> i32` 改 `fn main_jhyy(_argc: i32, _argv: *u8) -> i32`（runtime 现在带 argc/argv 转发）。

## commit 3（pending）：修 jhyy_v1 自举回归

**目标**：让 `jhyy_v1.exe`（自举版）能编译更多 tests，缩小与 `jhyy_0`（C 版）的差距。

**Bug 15（lexer.jhyy `lookup_keyword` length 错配）**：

- 症状：所有 `as` cast 编译报 CERR（"unexpected token ident"）— `as` 被识别为 ident 而非 TOKEN_AS
- 根因：`as`（2 字符）放在 `len == 3` 分支用 `strncmp(name, "as", 3)` —— strncmp 读越界不会匹配
- 同类 bug：`sizeof`（6 字符）放 `len == 5` 分支；`alignof`（7 字符）放 `len == 6` 分支
- Fix：把 `as` 移到 `len == 2` 分支用 strncmp length 2；新增 `len == 6` 分支给 `sizeof`；新增 `len == 7` 分支给 `alignof`
- 影响：单 fix 直接让 5 个 CERR 测试从 reject → 可能 pass

**Bug 16（codegen.jhyy `cg_find_local` out_buf cast segfault）**：

- 症状：所有 `let x = 42; x`（immutable scalar local + ident ref）触发 0xC0000005 segfault
- 根因：caller 模式 `let loc_buf = IRVal { ... }; cg_find_local(..., (loc_buf as *u8))` —— jhyy codegen 对 caller-stack IRVal struct value 做 `as *u8` 时 emit 错的 loadw 链，访问未初始化内存
- Fix：caller 改用 `arena_alloc(IRVAL_SIZE())` 拿到已知 buffer，函数内 write 进去，caller 端 field-level read 回 IRVal struct value
- 影响：单 fix 让 19 个 AV 测试从 segfault → 进展到下一阶段（但 18 个撞 STK 栈溢出）

**当前 jhyy_v1 regress 状态**：

| 阶段 | OK | AV | STK | CERR | WRX | NORUN |
|------|----|----|-----|------|-----|-------|
| 修 bug 15 前 | 0 | 20 | 11 | 12 | 0 | 4 |
| 修 bug 15 后 | 0 | 27 | 9  | 7  | 0 | 4 |
| 修 bug 16 后 | 0 | 8  | 25 | 9  | 0 | 5 |

**剩余 8 个 AV / 25 个 STK / 9 个 CERR**：

- 9 个 CERR 全部是 jhyy parser 翻译层缺功能（expression-form if/match / const arrays / import）—— parser enhancement 工作，不是简单 bug fix
- 8 个 AV + 25 个 STK 推测都是 jhyy codegen 翻译层缺功能（如 struct field、array、slice、loop 渲染缺失）—— 需要逐个深入查
- 单 sprint 内无法全部修完；记录在案，sprint 5+ 逐个推进

## 验证

| 步骤 | 状态 |
|------|------|
| jhyy_0 (C 编译) 编 main.jhyy → jhyy_v1.exe | ✅ exit 0 |
| jhyy_v1.exe build hello.jhyy | ✅ exit 0，生成 .il 合法 |
| jhyy_v1.exe compile hello.jhyy | ✅ exit 0，生成 .exe |
| /tmp/hello.exe 运行 | ✅ return 42（与 hello.jhyy `return 42` 一致）|
| regress.py | ✅ 47/50 pass, 0 failed, 3 skipped（无 regression）|

## 不在 v0.8.0 范围

| 项 | 延后到 | 理由 |
|----|-------|------|
| 修 v0 codegen bug 1/2/3/4（LEA/phi/loadub/&local）| v0.8.x patch 或 v1.0.0 后 | workaround 已在 jhyy 源码里 |
| QBE 完整重写 | phase-2.5 / v3.x+ | 2026-06-22 决策：先 phase-2 前端翻译 |
| 多目标架构（自研 OS）| phase-4+ | 当前 amd64_win 中间态 |
| 性能优化 | v2.x | v1.0 目标 = 翻译完成 + 行为正确 |

## 实施顺序

```
✅ v0.8 commit 1: 修 3 个自举过程发现的 codegen bug   (1b86277, 2026-07-02)
→ v0.8 commit 2: 翻译 main.c → main.jhyy + bug 14    (本文档)
→ v0.8 commit 3: Stage 1 byte-equal 验证              (后续 sprint)
```
