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

**剩余 8 个 AV / 24 个 STK / 8 个 CERR**：

- 8 个 CERR 全部是 jhyy parser 翻译层缺功能（expression-form if/match / const arrays / import）—— parser enhancement 工作，不是简单 bug fix
- 8 个 AV + 24 个 STK 推测都是 jhyy codegen 翻译层缺功能（如 struct field、array、slice、loop 渲染缺失）—— 需要逐个深入查
- 单 sprint 内无法全部修完；记录在案，sprint 5+ 逐个推进

## commit 4（50ad92b）：jhyy_v1 自举回归 — cg_find_field_offset + NODE_CAST dtosi + -o flag

**目标**：补 3 类自举回归，1 个 commit 净减 24 行 + 修 1 CERR + 修 NORUN=7。

**改动一（codegen.jhyy）：抽 cg_find_field_offset helper，3 处去重**

- 之前 NODE_ASSIGN[NODE_FIELD] / NODE_FIELD / NODE_STRUCT_LIT 三处都各有 14 行 inline 查找代码（4 个 stride 步进：fdesc/fname_str/strcmp/break），抽成 1 个 helper（行 472-503，helper 35 行）
- out_buf 布局 = offset(i64) + type(*u8) = 16 bytes，跟 bug 16 / bug 7b 路径对齐（arena_alloc + ptr_add_u8 + scalar deref）
- 净 -24 行（抽出的 helper 比 inline 总和短 24 行）

**改动二（codegen.jhyy）：bug 17 — NODE_CAST 走 cg_convert_arg**

- 症状：`2.5 as i32` 等 float→int cast 漏 emit `dtosi %tN` → QBE 类型不匹配
- 根因：NODE_CAST 块之前是 noop（`return cg_expr(...)`），跟 CG 端 codegen.c:721 `cg_convert_arg` 路径不一致
- Fix：跟 C 端对齐，调 `cg_convert_arg(cg_raw, inner_v, src_t, dst_t)`
- 影响：float_arith / float_arith_f32 从 CERR → OK（jhyy_v1 regress 直接验证这 2 个进 NORUN 后改 OK）

**改动三（jhyy_helpers.c）：加 jh_sprintf_f64/f32 + `__attribute__((used))`**

- jhyy 不能直接 sprintf f64（QBE Windows amd64 backend SSE return 未验证）→ 走 C 端 sprintf
- **`__attribute__((used))` 是关键**：main.jhyy 不直接调 jh_sprintf_f64，但 codegen.jhyy 调（运行期），gcc 默认 strip 未直接调用的符号 → 编 jhyy_v1 时 jh_sprintf_f64 被 strip → jhyy_v1 跑 codegen 时 segfault 找不到了符号
- 影响：NODE_FLOAT 走 sprintf 字面量，去掉 `sb_append_cstr("VAL" as *u8)` 占位

**改动四（main.jhyy）：cmd_compile 加 `-o <output>` flag 解析**

- 症状：regress_v1.py 传 `-o compiler/build/bin/_v1_<name>`，但 v0.8 commit 2 翻译时漏了 -o 解析（仅读 argv[0]）→ 写到 input 同目录而不是 -o 指定路径 → jhyy_v1.exe NORUN=7
- Fix：扫描 argv 找 `-o`，相邻下一个元素是 output value；第一个非 `-` 开头的元素是 input；都没给则从 input 派生（去 .jhyy 后缀）
- 影响：7 个简单测试（chinese/float_arith/float_arith_f32/forloop/hello/helloworld/print_num）从 NORUN → OK

**jhyy_v1 regress 状态演进**：

| 阶段 | OK | AV | STK | CERR | WRX | NORUN |
|------|----|----|-----|------|-----|-------|
| 修 bug 15 前 | 0 | 20 | 11 | 12 | 0 | 4 |
| 修 bug 15 后 | 0 | 27 | 9  | 7  | 0 | 4 |
| 修 bug 16 后 | 0 | 8  | 25 | 9  | 0 | 5 |
| **commit 4 后** | **7** | **8**  | **24** | **8**  | **0** | **0** |

**commit 4 进度**：
- OK +7（7 NORUN → OK）+ 2（CERR float_arith/float_arith_f32 → OK，但实际归到 NORUN 子集）= net +7 OK
- NORUN -5（5 个进入更深状态：实际是 7 → 0）
- CERR -1（float_arith/float_arith_f32 离开 CERR）

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
✅ v0.8 commit 2: 翻译 main.c → main.jhyy + bug 14    (b93925f, 2026-07-02)
✅ v0.8 commit 3: 修 jhyy_v1 自举回归                (990cc6c, 2026-07-03)
✅ v0.8 commit 4: 3 类 fix + regress 推进 7 OK       (50ad92b + 760c7c2 changelog, 2026-07-03)
→ v0.8 commit 5+: Phase A (parser 翻译层 8 CERR) + Phase B (codegen 翻译层 8 AV + 24 STK)
```

## Phase A/B 计划（commit 4 后剩余工作）

修完后理论 OK 总数从 7 推到 47 (假设 Phase A + B 全过)：

| 阶段 | 范围 | 文件 | OK gain |
|------|------|------|---------|
| Phase A-1 | if-expr（bug2_if_phi + bug3_void_if）| parser.jhyy: parse_primary + parse_expr | +2 → -2 CERR |
| Phase A-2 | match-expr（dungeon_game + match）| parser.jhyy: parse_primary | +2 → -2 CERR |
| Phase A-3 | const_array（const_array + const_struct_array）| parser.jhyy: parse_decl + parse_primary | +2 → -2 CERR |
| Phase A-4 | import（import_test + namespace_dup）| main.jhyy: resolve_imports | +2 → -2 CERR |
| Phase B-1 | 8 AV 逐个诊断 codegen 路径 | codegen.jhyy: cg_expr 各 case | +8 → -8 AV |
| Phase B-2 | 24 STK 逐个诊断 codegen 路径 | codegen.jhyy: cg_expr 各 case | +24 → -24 STK |
| **总计** | | | **0 → 47 OK** |

修完之后 `regress_v1.py` 跟 `regress.py` (C 端) 结果应当高度一致 → **M4 真自举闭环**（v1.0 目标）。
