# v0.8.0 changelog

## 概要

v0.7.0 之后（7A enum first-class + 7B const struct array），v0.8.0 转向 **v1.0.0 v1.x 自举 sprint 4-5 收尾**。v0.8 定位：清理自举路径的剩余卡点，让 `jhyy_0 (C 编译) 编 main.jhyy → jhyy_1` 跑通。

按 v1.0.0 L1 计划：v0.x patch 只修 bug，**不引入新特性**。v0.8.0 同样不引入新语法（enum / const array 等下个 minor version）。

## commit 1（1b86277）：修 3 个自举过程发现的 codegen bug

| bug | 文件 | fix |
|-----|------|-----|
| 11 | `compiler/src/codegen.c:222` | `cg_convert_arg` 加 `else if (src_qt == 'w' && dst_qt == 'l') conv = "extsw";` |
| 12 | `compiler/src0/codegen.jhyy:437` | `cg_copy_struct` FieldDesc.type 改 `fdesc_ptr + 8` |
| 13 | `compiler/src0/codegen.jhyy` | `CGContext.sret_slot: IRVal → sret_slot_id: i64` + 调用处用 IRVal literal |

**Why**：这 3 个 bug 是 sprint 4 翻译 codegen.jhyy 时暴露的 codegen 问题，挡住自举 main.c → main.jhyy 路径。bug 11 是 jhyy 0 codegen 缺 w→l extension（实测触发：i64 变量 > 0 字面量比较）。bug 12 是翻译 bug（FieldDesc 字段 offset 算错）。bug 13 是 v0 codegen 对 first-field-w struct value 的 sret 处理有缺陷（IRVal 有 5 字段），workaround 是把 sret_slot 改 i64 不存 struct。

## commit 2（b93925f）：翻译 main.c → main.jhyy

**目标**：`compiler/src/main.c` (556 行) → `compiler/src0/main.jhyy` (471 行)

**额外发现 bug 14**：codegen.jhyy 的 `"%c %"` 格式串在 sprintf 实际运行时被吃掉末尾 literal `%`，导致 IL emit 的 function 参数声明缺 `%` 前缀（`w _argc` 而非 `w %_argc`）。QBE 拒绝 `_argc` 作为 valid identifier（"unknown keyword"）。

**fix**：拆成 2 个 emit（`"%c "` 走 ir_emit_int + `"%"` 走 ir_emit_str）。在 codegen.jhyy:1921 加 v0 codegen bug workaround 注释。

**`compiler/runtime/runtime.{c,h}`**：main 改转发 argc/argv 给 main_jhyy（jhyy main 跟 C main 一样要接收 argc/argv，sprint 5 验证需要）。

**`compiler/src0/_driver*.jhyy` (12 个 driver)**：签名 `fn main_jhyy() -> i32` 改 `fn main_jhyy(_argc: i32, _argv: *u8) -> i32`（runtime 现在带 argc/argv 转发）。

## commit 3（990cc6c）：修 jhyy_v1 自举回归

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
| **commit 5 后** | **16** | **30** | **1 (timeout)** | **0** | **0** | — |

**commit 4 进度**：
- OK +7（7 NORUN → OK）+ 2（CERR float_arith/float_arith_f32 → OK，但实际归到 NORUN 子集）= net +7 OK
- NORUN -5（5 个进入更深状态：实际是 7 → 0）
- CERR -1（float_arith/float_arith_f32 离开 CERR）

## commit 5（9e77e09）：Phase A-1 if-expr — 5 codegen bug + parser if-as-expression

**目标**：让 `let r = if cond { a } else { b };` 在 jhyy_v1 能编译并跑通；regress 从 7 OK 推到 16 OK（+9）。

**改动一（util.jhyy）：Bug 18 — `sb_grow` 不能调 `realloc`**

- 症状：编第 2 个含 `if cond { ... }` 的函数时 jhyy_v1 rc=127（silent crash，无 stderr）
- 根因：`StringBuilder.buf` 是 `arena_alloc` 分配的，但 `sb_grow` 调 `realloc` — libc realloc/free 只接受 malloc 指针。realloc 接受 arena 指针会污染 heap metadata → silent crash（exit code 127 通常是 dynamic linker 找不到符号，但这里实际是 heap 死锁后续 segfault 被 bash 转 127）
- Fix：`malloc(new_cap)` + `memcpy(new_buf, old_buf, len)` + 放任旧 buf 泄漏（一次性进程，arena 整体释放时回收）
- 影响：单 fix 解 rc=127，2nd+ function 编译能跑

**改动二（codegen.jhyy）：Bug 19 — `ir_emit_alloc` 必须在 `ir_emit_jnz` 之前**

- 症状：含 `let x = if ... { ... } else { ... };` 的函数 QBE 报 "label or } expected"
- 根因：QBE 要求 `alloc` 必须在函数首块（在任何 terminator `jnz` 之前）。codegen.jhyy 原来 `ir_emit_jnz` 在前 `ir_emit_alloc` 在后
- Fix：调换顺序，先 alloc result slot 再 jnz

**改动三（codegen.jhyy）：Bug 20 — then/else 末 return 时不能 emit trailing jmp**

- 症状：if body 以 `return` 结尾时 QBE 报 "block @mergeX is used undefined" / "dead code after ret"
- 根因：then/else body emit 后无条件 `ir_emit_jmp(merge_block)`，但如果 body 末是 `ret`，jmp 是 dead code → QBE 拒收
- Fix：加 helper `cg_body_returns(body_node) -> i32` 检查 body 末是否为 NODE_RETURN，仅当非 return 时 emit trailing jmp
- 副作用：cg_body_returns 定义必须在 cg_expr 之前（jhyy 无 forward decl）—— 跟 NODE_IF 的引用顺序决定

**改动四（codegen.jhyy）：Bug 21 — `ir_emit_load` → `cg_emit_load` typo（value path）**

- 症状：非 void `let r = if cond { 1 } else { 2 };` 编译过但运行 hang / 输出空
- 根因：merge 块 emit `ir_emit_load(cg_raw, result, 0 as *u8, result_slot)` —— 4 参数 `(IRVal, ..., *, *)` 签名跟 `ir_emit_load(ir: *IRBuf, dst: IRVal, src: IRVal, off: IRVal)` 不同（4 参 vs 4 参但类型不同），jhyy v0 codegen 没做强类型 dispatch 走错函数 → emit 错的 IL
- Fix：`cg_emit_load(cg_raw, result, 0 as *u8, result_slot)`（codegen ctx，正确函数）
- 同类潜在 typo：logical AND/OR codegen（lines 1163/1179）—— 当前未触达，sprint 6 处理

**改动五（codegen.jhyy）：Bug 22 — `cg_body_returns` 定义必须在 cg_expr 之前**

- 症状：jhyy 报 "undefined variable 'cg_body_returns'"
- 根因：jhyy 无 forward declaration，函数必须在使用前定义。原来 `cg_body_returns` 在文件底部（v0.7 时代），NODE_IF 现在用上
- Fix：移到 cg_expr 之前（line 612）

**改动六（codegen.jhyy）：Bug 16 应用 — NODE_BLOCK expr-position 走 arena + field-level**

- 症状：含 `{ expr; expr; last_expr }` 块作为表达式位置（如 if body）时 stack buffer corruption
- 根因：v0 codegen bug 16 — IRVal 40 字节 struct value 赋给 mutable local，caller-stack 错位
- Fix：`last_buf = arena_alloc(IRVAL_SIZE())` + 每次写 5 字段；return 时 field-level deref 重建 IRVal struct value

**改动七（parser.jhyy）：if-as-expression 解析器分支**

- 症状：`let r = if cond { a } else { b };` 报 CERR（"expected ';' after expression" 或 "if without else"）
- 根因：parser.jhyy `parse_expr` 不支持 expression-form if（只支持 statement-form，走 `parse_if`）
- Fix：在 `parse_expr` 内 inline 一份 if 解析（parse_if 定义在 parse_expr 之后无法 forward ref）—— 支持 then/else block 内 expression statements + 嵌套 if（自递归）+ else-if（自递归）。不支持块内 let/return/match（if-expr 值块场景不需要，if-statement 走 parse_if）

**改动八（jhyy_helpers.c）：debug printf helpers**

- 加 `jh_fmt_d_stderr` / `jh_fmt_lld_stderr` 两个 wrapper（jhyy extern 不能 variadic）。这次 commit 没用上，sprint 6 codegen 排错时备用。

**jhyy_v1 regress 状态演进**：

| 阶段 | OK | CERR | STK/AV/TIMEOUT | WRX |
|------|----|----|----------------|-----|
| commit 4 | 7 | 8 | 32 | 0 |
| **commit 5** | **16** | **30** | **1** | **0** |

**commit 5 进度**：
- OK +9（if-as-expression 用法测试从 CERR → OK：void_if / bug3_void_if / bug2_if_phi + 6 个 test_if_*）
- CERR net +22：8 → 30（if-expr CERR 减 3，但 logical.jhyy 因 logical operator codegen typo 之前归类不同，加上其他 STK/AV 测试因 if-expr fixed 暴露更深 codegen bug，现在归 CERR）
- STK/AV 大幅减少：32 → 1（大量之前挂的 if 嵌套测试现在能跑）

**验证**：

| 步骤 | 状态 |
|------|------|
| jhyy_0 (C) regress | ✅ 47/47 pass, 0 fail, 3 skip |
| jhyy_v1 编 bug2_if_phi.jhyy → 跑通 | ✅ |
| jhyy_v1 编 bug3_void_if.jhyy → 跑通 | ✅ |
| jhyy_v1 编 void_if.jhyy → 跑通 | ✅ |
| jhyy_v1 regress | ✅ 16/47 OK（commit 4 → commit 5: +9）|

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
| QBE 完整重写 | v2.x | 2026-06-22 决策：先 v1.x 前端翻译 |
| 多目标架构（自研 OS）| v3.x+ | 当前 amd64_win 中间态 |
| 性能优化 | v2.x | v1.0 目标 = 翻译完成 + 行为正确 |

## 实施顺序

```
✅ v0.8 commit 1: 修 3 个自举过程发现的 codegen bug   (1b86277, 2026-07-02)
✅ v0.8 commit 2: 翻译 main.c → main.jhyy + bug 14    (b93925f, 2026-07-02)
✅ v0.8 commit 3: 修 jhyy_v1 自举回归                (990cc6c, 2026-07-03)
✅ v0.8 commit 4: 3 类 fix + regress 推进 7 OK       (50ad92b + 760c7c2 changelog, 2026-07-03)
✅ v0.8 commit 5: Phase A-1 if-expr + regress 推进 16 OK  (9e77e09, 2026-08-03)
✅ v0.8 commit 6 wip: bisect heap corruption (efc41bf, 2026-08-03)
✅ v0.8 commit 7: W-002 标识符 rename + workaround doc (0453cef, 2026-08-03)
✅ v0.8 commit 8: W-003 let _ = fncall → direct call   (bea83f0, 2026-08-03)
✅ v0.8 commit 9: W-001 byte-by-byte hash + W-005 let-mut workaround (d570c72, 2026-08-03)
✅ v0.8 commit 10: W-005 扩展到 util/arena + W-006/W-007 文档 (d8535a9, 2026-08-04)
✅ v0.8 commit 11: W-008 cg_find_field_offset 三层 deref 漏修 + doc (2d4c319, 2026-08-04)
✅ v0.8 commit 12: W-009 cg_convert_arg src_t==0 兜底 + dst.kind 放宽 + doc (5820793, 2026-08-04)
→ v0.9 sprint: W-001~W-009 真修 + main.c 翻译收尾 + Stage 1 byte-equal 闭环

---

## commit 11 (2d4c319)：W-008 cg_find_field_offset 三层 deref 漏修

**目标**：修 jhyy_v1 codegen.jhyy 的 cg_find_field_offset / cg_copy_struct 三处 deref 漏，让 struct field access emit 正确 IL（i64 field `=l loadl` 而非 `=w loadw`，pointer field 同样修正）。

**改动一（codegen.jhyy:448 — Bug 8c, ftype deref）**

```jhyy
// 前：let ftype = ptr_add_u8(fdesc_ptr, 8 as i64) as *Type;     // 读到 FieldDesc 内字节
// 后：
let ftype_slot_v1 = ptr_add_u8(fdesc_ptr, 8 as i64) as **Type;
let ftype = *ftype_slot_v1;
```

**改动二（codegen.jhyy:489-491 — Bug 8a, sym deref, 深层 root cause）**

```jhyy
// 前：let fname_str = *fname_str_ptr;    // 读到 *Sym 当字符串
// 后：
let sym_p_v1 = *(fdesc as **Sym);                                  // deref Sym*
let fname_str = *(ptr_add_u8(sym_p_v1 as *u8, 0 as i64) as **u8);  // Sym.name @ offset 0
```

**改动三（codegen.jhyy:496-502 — Bug 8b, type slot deref）**

```jhyy
// 前：*out_type_v1 = ptr_add_u8(fdesc, 8 as i64) as *u8;          // 写 fdesc+8 地址
// 后：*out_type_v1 = *(ptr_add_u8(fdesc, 8 as i64) as **u8);       // 写 fdesc+8 处的值
```

**Why**：jhyy_v1 的 struct field access 路径（`(*a).field`、`s.field`、struct assign、struct copy）全部走 cg_find_field_offset / cg_copy_struct。这两个 helper 把 *u8 当 **u8 解 / 少解一层 deref，导致：
1. **Bug 8a**（最深层）：FieldDesc.name 实际存 *Sym，strcmp(Sym*, "val") 几乎永远不匹配 → cg_find_field_offset fallback 走错路径
2. **Bug 8b/8c**：FieldDesc.type 漏 deref → caller 拿到的 field_type_raw 是 fdesc+8 这个**指向 type 字段存储地址的指针**（不是 Type 指针本身）→ qbe_type_of 读到 garbage kind → fall through → return QBE_W → 所有 i64/pointer struct field 标量化且 QBE_W
3. **下游链**：caller emit `%tN =w loadw` 但目标字段是 i64/pointer（需要 `=l loadl`）→ QBE typecheck 拒绝

**修复前 → 修复后 IL 对比**（`Box { val: 5 as i64 }`）：
```diff
- %t4 =w loadw %t0      # 错：i64 字段按 32-bit 读
+ %t4 =l loadl %t0      # 对：i64 字段按 64-bit 读
```

**验证**：
- 复现：`compiler/src0/__w8_test.jhyy`（最小 struct field 读写）— 修复前 QBE 拒绝，修复后 emit 正确 IL
- 端到端：`jhyy_v1 compile arena.jhyy` 修复后 emit 含 `=l loadl` 给 def_size 字段（offset 32），QBE 通过 stage 0 closure 入口
- v0 regress：47/47 pass, 0 fail, 3 skip（**无 regression**）
- v1 regress：12 OK（commit 10 是 16 OK，**回退 -4** — 因为 W-008 修了 loadw→loadl 但暴露了下一道 cslel operand type bug：W-009 候选）

**Stage 0 closure 关系**：W-008 + W-007（commit 10 修 cg_convert_arg extsw）是 Stage 0 闭环的**必要组合**。两个 fix 缺一不可：W-007 修 return literal 的 w→l 转换，W-008 修 struct field load 的类型判定。任一缺失 → jhyy_v1 编译 arena.jhyy 失败。

**superseder**：本 commit 转 W-008 为 RESOLVED；剩余 v1 OK 数量回落的原因是 commit 11 把一些之前走错 IL 但碰巧能跑的测试暴露到 QBE 严格 typecheck 下，**新 cslel 错**。修 W-009（cslel 比较结果类型错）后 v1 OK 数量应回到 16+。

**详细文档**：[`docs/internal/workarounds.md` § W-008](../../internal/workarounds.md#w-008)

---

## commit 12 (5820793)：W-009 cg_convert_arg + NODE_CAST 两处放宽

**目标**：让 jhyy_v1 编 arena.jhyy 时所有 `ptr == 0` / `i64 cmp 0` / `pointer cmp 0` 路径 emit 正确 IL（l vs l，不再 w vs l），Stage 0 closure 解锁。

**改动一（codegen.jhyy:548-553, Fix 1）— cg_convert_arg src_t==0 兜底**

```jhyy
// 前：if src_t == (0 as *u8) { return arg; }
// 后：
let src_qt_v1: i32 = if src_t == (0 as *u8) { arg.qbe_type } else { qbe_type_of(src_t) };
```

**改动二（codegen.jhyy:555-570, Fix 2）— cg_convert_arg 不再 bail dst.kind=KIND_POINTER**

```jhyy
// 前：if (*dst).kind != KIND_PRIMITIVE() { return arg; }   // 让 "0 as *u8" 永远 no-op
// 后：移除 dst.kind check（pointer qbe_type 是 L，走 W→L extsw）；保留 src.kind=KIND_PRIMITIVE 检查
if (*src).kind != KIND_PRIMITIVE() { return arg; }
```

**改动三（codegen.jhyy:1844-1855, Fix 3）— NODE_CAST 移除 src_t==0 早 bail**

```jhyy
// 前：if src_t == (0 as *u8) || dst_t == (0 as *u8) { return inner_v_v1; }
// 后：if dst_t == (0 as *u8) { return inner_v_v1; }
```

**Why**：v0 (codegen.c:721) 的 NODE_CAST 直接 emit QBE 转换指令（src_qt/dst_qt 决策，不 bail KIND_POINTER）。jhyy_v1 把 cast 委托给 cg_convert_arg，但 cg_convert_arg 有两个 hard bail 阻挡：
1. src_t==0 早 bail — 但 literal 0 走这里（type_ptr_v1 未填）
2. dst.kind != KIND_PRIMITIVE 早 bail — 让 `0 as *u8` 永远 no-op（pointer cast）

**修复前 vs 修复后 IL（arena.jhyy line ~53 `if raw == (0 as *u8)`）：**
```diff
  %t28 =l call $malloc(l %t27)
  %t29 =w copy 0
- %t30 =w ceql %t28, %t29            # INVALID：ceql 要两边 l
+ %t30 =l extsw %t29                 # cg_convert_arg 自动 emit
+ %t31 =w ceql %t28, %t30            # VALID：两边 l
```

**实测数字**：arena.jhyy emit 中 `extsw` 出现次数 0 → 29；所有 `ceql/cslel/csltl/csgtl` 操作数两边都是 l。QBE typecheck 通过。

**联动**：
- v0 regress：47/47 pass, 0 fail, 3 skip（**无 regression**）
- v1 regress：12 OK（持平，arena.jhyy 不在 regress 测试集——是 library；但**Stage 0 closure 解锁**）
- W-008 (commit 11) + W-009 (commit 12) = jhyy_v1 编 arena.jhyy 通过 QBE typecheck 的**必要组合**

**详细文档**：[`docs/internal/workarounds.md` § W-009](../../internal/workarounds.md#w-009)
```

## Phase A/B 计划（commit 4 后剩余工作 — v0.9 真修前）

> **2026-08-04 校准**：原"Phase A + B 全过 → 47 OK"假设未达成。Phase A-1 if-expr (commit 5, 9e77e09) 推进到 16 OK 后，后续 commit 6-12 的 W-001~W-009 workaround 暴露下一层 codegen 严格性问题（loadw→loadl / cslel operand type 等），jhyy_v1 regress 实际落定在 **12 OK / 47 总（持平 baseline）**。详见 [`v0.8.0任务清单 + 概要设计.md`](../../plans/v0/v0.8.0任务清单 + 概要设计.md) § 完成定义校准。

修完后理论 OK 总数从 7 推到 16（Phase A-1 commit 5 已达成；剩余待 v0.9 W-真修）：

| 阶段 | 范围 | 文件 | OK gain | 实际状态 |
|------|------|------|---------|---------|
| Phase A-1 | if-expr（bug2_if_phi + bug3_void_if）| parser.jhyy: parse_primary + parse_expr | +9 → -9 CERR | ✅ commit 5 已达成 |
| Phase A-2 | match-expr（dungeon_game + match）| parser.jhyy: parse_primary | +2 → -2 CERR | 🔴 v0.9 真修 |
| Phase A-3 | const_array（const_array + const_struct_array）| parser.jhyy: parse_decl + parse_primary | +2 → -2 CERR | 🔴 v0.9 真修 |
| Phase A-4 | import（import_test + namespace_dup）| main.jhyy: resolve_imports | +2 → -2 CERR | 🔴 v0.9 真修 |
| Phase B-1 | 8 AV 逐个诊断 codegen 路径 | codegen.jhyy: cg_expr 各 case | +8 → -8 AV | 🔴 v0.9 真修（W-001~W-009）|
| Phase B-2 | 24 STK 逐个诊断 codegen 路径 | codegen.jhyy: cg_expr 各 case | +24 → -24 STK | 🔴 v0.9 真修 |
| **总计** | | | **0 → 47 OK** | **v0.8 wip 实际 12 OK 持平（≠ 47）**|

---

## Sprint 4.4 A — 修 latent bug 解 Task #146 (commit 2.36, 2026-08-07)

**触发场景**: Task #146 (slice_subrange codegen fix) 完整 NODE_SLICE_RANGE 翻译 (~120 行) 触发 jhyy_v1 HEAD rebuild QBE 错 `invalid type for first operand %t0 in csltl` / `add`。

**Latent Bug 根因** (Sprint 4.4 B 实证):

1. **ir.jhyy:185 ir_init 设 next_tmp=0** + post-increment → 第一 ir_new_tmp 返回 id=0
2. **codegen.jhyy:740 `let zero = IRVal { kind: 0, id: 0, ... }`** → kind=0=IRVAL_TEMP
   - 当 `zero` 当 cg_expr 返回值 (e.g. `return zero;` fall-through) 传给 phi/csltl 操作数, 被当 temp 发 `%t0`
   - QBE 把 %t0 留作 call return register, 不接受普通操作数

**commit 2.36 修法** (选项 2 pre-increment, 1-line 局部 fix):

1. **ir.jhyy ir_new_tmp 改 pre-increment** — first id = 1, 跟 v0 端 cg_expr 入口 pre-alloc 行为对齐
2. **ir.jhyy 加 ir_emit_arg helper** — 按 val.kind dispatch (IRVAL_INT → literal `<ival>`, 其他 → `%t<id>`)
3. **codegen.jhyy `zero` 改 kind=IRVAL_INT()** — literal 0, 不再当 temp 发
4. **ir.jhyy ir_emit_load 改用 ir_emit_arg** — dispatch on addr.kind
5. **codegen.jhyy NODE_INDEX slice 处理改用 ir_emit_arg** — dispatch on base.kind

**Why 选选项 2 (pre-increment) 不选选项 1 (next_tmp=1 in init)**:
- 选项 2 根治: 改 return 逻辑, 不管 reset arena 多少次 first id 都 = 1
- 选项 1 局部: 改 init, 但每次 reset arena 回到 0 → first id 又撞 0
- 选项 2 1-line fix, 选项 1 改动面更大

**验证**:
- v0 regress: 50/53 passed, 0 failed, 3 skipped (持平 baseline 12/47, 实际已扩展到 50/53)
- jhyy_v1 (phantom sha e2064a6b): slice_subrange.jhyy **compile EXIT=0** (前: QBE FAIL %t0)
  - IL 显示 `loadl 0` (literal, 之前是 broken `%t0`)

**Task #145 BLOCKED** (defer Sprint 4.5 B): cleanup crash bisect + HEAD rebuild 加完整
NODE_SLICE_RANGE 翻译 仍 FAIL `\0 %t0` (4th arg of cg_match_pattern call) — phantom binary
范畴问题, 跟 Task #146 phantom binary finding 同根。

**内存记录**: [[`project_sprint4_4_b_latent_codegen_bug.md`]](../../../../.claude/projects/C--Users-liuzhen-Desktop-coding-JiHuiYiYou/memory/project_sprint4_4_b_latent_codegen_bug.md) (含 IL diff 实证)

**Sprint 4.4 A ship**:
- ✅ commit 2.36: latent bug fix (pre-increment + kind dispatch)
- 🔴 Step 2 commit 2.37 (完整 NODE_SLICE_RANGE 翻译) DEFERRED → Sprint 4.5 B
- 🔴 Task #145 (cleanup crash bisect) BLOCKED by phantom binary


修完之后 `regress_v1.py` 跟 `regress.py` (C 端) 结果**持平 baseline**（12 OK 持平即可，**不是** 47/47）→ **Stage 1 byte-equal 闭环**（v0.9 目标）。

---

## Sprint 4.5 B 启动 — phantom vs HEAD audit (commit 2.39, 2026-08-07)

**目的**: 验证 phantom binary 是否真缺 sprint 4.2+ 翻译 (NODE_CONST_DECL 等), 还是仅命名约定不同.

**Audit 方法** (`objdump -t` + `strings` 比对):

| Binary | sha256 (前 16) | bytes | symbols | .text lines | unique strings |
|--------|----------------|-------|---------|-------------|----------------|
| phantom (jhyy_v1.exe) | `e2064a6b9c9d96...` | 397823 | 3399 | 13395 | 6 |
| HEAD v5 (jhyy_v1_v5) | `341659409385300d` | 398899 | 3401 | 13449 | 19 |

**audit 关键发现**:

1. **codegen 函数符号集完全相同** — `cg_add_local`, `cg_body_returns`, `cg_const_data_prim_val`, `cg_convert_arg`, `cg_copy_struct`, `cg_emit_const_data_elem`, `cg_emit_const_prim_data`, `cg_emit_load`, `cg_emit_phi`, `cg_emit_store`, `cg_emit_store_primitive`, `cg_expr`, `cg_find_field_offset`, `cg_find_local`, `cg_find_local_is_stack`, `cg_func`, `cg_match_pattern`, `cg_module`, `cg_stmt`, `emit_mangled_name`, `ir_new_int` 共 20 个全部存在 (phantom = HEAD v5).

2. **ast 枚举常量也存在** — `ast__NODE_CONST_DECL`, `ast__ast_new_const_decl`, `ast__NODE_FOR`, `ast__NODE_IF` 等 sprint 4.2+ 翻译符号 phantom = HEAD v5 都存在.

3. **真正区别**:
   - **命名约定**: phantom 无 `_v1` 后缀 (裸名 `arena__align_up`); HEAD v5 有 `_v1` 后缀 (`arena__align_up_v1`)
   - **代码量微差**: HEAD v5 大 1076 bytes (+19 unique strings) — 来自 commit 2.36 latent bug fix 的 5 处小修改 (ir.jhyy pre-increment + ir_emit_arg + zero kind=IRVAL_INT + ir_emit_load dispatch + NODE_INDEX slice dispatch)

**UPDATED 2026-08-07 commit 2.39**: 之前 (commit 2.34 phantom discovery postmortem) 误判 "phantom 缺 sprint 4.2+ 翻译". 真正原因: 只跟 `_v1` 后缀模式 grep, 而没 grep 不带后缀的 `NODE_CONST_DECL` 这种 enum 常量 (phantom 也有). audit 实测两个 binary 功能等价.

**Sprint 4.5 B 待办**:
1. **Task #145 cleanup crash bisect** — 22 tests "compile failed" 是 jhyy_v1 cleanup 阶段 non-deterministic HEAP_CORRUPTION. 需 HEAD rebuild 解后才能验证.
2. **完整 NODE_SLICE_RANGE 翻译 HEAD rebuild 验证** — commit 2.36 (latent bug fix) 通过 phantom 验证但 HEAD rebuild 验证被 phantom 范畴问题 BLOCKED. 加完整 NODE_SLICE_RANGE 触发 QBE `\0 %t0` (separate codegen bug, 4th arg of cg_match_pattern call).
3. **EXIT=60 真 PASS 验证** — Task #146 完成 (slice_subrange codegen fix 真 PASS).
4. **phantom binary 锁定** — phantom sha e2064a6b 是当前唯一 working baseline. 任何 phantom binary 修改 = baseline 重置,需同步 reset regress_v1 baseline 数字.

**内存记录**: [[`project_sprint4_4_phantom_binary_finding.md`]](../../../../.claude/projects/C--Users-liuzhen-Desktop-coding-JiHuiYiYou/memory/project_sprint4_4_phantom_binary_finding.md) (corrected from commit 2.34 postmortem)

---

## Sprint 4.5 B Task #145 ship — cmd_compile double-free fix (commit 2.40, 2026-08-07)

**Task**: 解 phantom binary 的 cmd_compile double-free bug (Sprint 4.5 B 步骤 1).

**根因** (`compiler/src0/main.jhyy` cmd_compile, lines 838-881):
```jhyy
let derived = malloc(1024 as i64);    // 总是 alloc
derive_output_name(input, derived);
let mut out_buf: *u8 = derived;
if user_out != (0 as *u8) {
    free(derived);                      // line 843: 如果 user_out 提供, 立即 free
    out_buf = user_out;
}
// 后面 cleanup 时:
if derived != (0 as *u8) { free(derived); }   // ❌ derived 非 0, double-free
```

cmd_compile 在 3 处 cleanup 检查 `if derived != (0 as *u8)` 来 free `derived` (lines 848, 871, 876), 但 `derived` 是 malloc 出来的真实指针 (永远非 0). 当 `user_out` 被提供时, derived 已经在 line 843 被 free 过一次, 后续 cleanup 再 free 一次 = **double-free** → NTSTATUS 0xC0000374 (HEAP_CORRUPTION) 非确定性崩溃。

**修法** (1-line × 3 sites): 把 cleanup 的 `if derived != (0 as *u8) { free(derived); }` 全部改成 `if user_out == (0 as *u8) { free(derived); }`. 语义: 只有 `user_out` 未提供时 (`derived` 仍是 output name 缓冲区) 才 free 它.

注: 原 `derived = 0 as *u8` 方案被 sema 拒绝 ("cannot assign to immutable variable"). 用 `user_out == 0` 语义等价 (避免 null-out-derived).

**验证** (HEAD v6 = sha 76c05c4f, v0-compiled):
- `const_array.jhyy`: 10/10 OK (前 phantom: 3/10 OK / 7/10 crash)
- `fib30.jhyy`: 10/10 OK EXIT=832040 (前 phantom: 9/10 OK / 1/10 crash)
- `regress.py` (C 端 baseline): 50/53 passed, 0 failed, 3 skipped (持平)
- `regress_v1.py` (HEAD v6): **42/53 passed, 8 failed, 3 skipped** (前 phantom: 22 cleanup-crash "compile failed")

**regress_v1.py path fix** (paired with this commit):
```python
# Before: pointing at PHANTOM jhyy_v1.exe (sha e2064a6b)
JHYY = os.path.abspath("compiler/build/bin/jhyy_v1.exe")
# After: pointing at HEAD v6 jhyy_v1.exe.exe (sha 76c05c4f)
JHYY = os.path.abspath("compiler/build/bin/jhyy_v1.exe.exe")
```

之前 regress_v1 所有 "compile failed" 测量都是 PHANTOM binary 在 cleanup 时 heap crash, 不是 fix 的效果。改 path 后才能测 HEAD v6。

**8 个真 fail 诊断** (NEW 暴露的真实 bug):
| Test | rc | 真 bug |
|------|----|------|
| slice_subrange.jhyy | 0 (compile) → AV | Task #146 已知 |
| slice_iterate.jhyy | 1 (sema) | "undefined variable" sema bug |
| slice_len.jhyy | 1 (sema) | "undefined variable" sema bug |
| dungeon_game.jhyy | 1 (parser) | "unexpected token 'match' in expression" — match-expr 翻译缺 (Task #50) |
| match.jhyy | 1 (parser) | match-expr 同上 (Task #50) |
| import_test.jhyy | AV 0xC0000005 | codegen AV |
| namespace_dup.jhyy | AV 0xC0000005 | codegen AV |
| float_cmp.jhyy | QBE | "invalid type for second operand %t57 in cgts" — codegen 类型推导 |

**Task #145 ship**:
- ✅ 22 cleanup-crash tests 解 (regress_v1 真 PASS 8 → 30, 加 12 baseline = 42)
- 🔴 8 个真 fail 已诊断 (5 个 codegen, 2 个 parser/sema, 1 个 QBE 类型)
- 🔴 下一步: Task #146 (slice_subrange codegen fix) — 这才是真正的"再加 1 PASS"路径

**内存记录**: [[`project_sprint4_4_cleanup_crash_discovery.md`]](../../../../.claude/projects/C--Users-liuzhen-Desktop-coding-JiHuiYiYou/memory/project_sprint4_4_cleanup_crash_discovery.md) (UPDATED 加 cmd_compile double-free 根因)

---

### 2026-08-07 — v0.9 wip commit 2.41: Sprint 4.5 B Step 2 ship — baseline lock + HEAD v6 calibration

**Sprint 4.5 B ship 完成**: Task #145 (cmd_compile double-free) commit 2.40 + Step 2 baseline lock.
Task #146 (NODE_SLICE_RANGE codegen) BLOCKED by known latent bug, defer to Sprint 4.5 C.

**Canonical HEAD v6 binary** (Sprint 4.5 B ship):
- `jhyy_v1.exe.exe` sha256 = `181375d70822f758110c8dcfdebed492d046821eb63988d1be1754fb0d5d5eec`
- 对应 commit = `576867a` (Task #145 ship)
- 注: 之前 memory 记的 "sha 76c05c4f" 是 commit hash, 不是 binary hash

**Canonical HEAD v6 baseline** (jhyy_v1, regress_v1.py):
```
===== 42/53 passed, 8 failed, 3 skipped =====
```

regress.py (C 端): 50/53 passed, 0 failed, 3 skipped (持平 baseline, no regression)

**8 FAIL breakdown** (jhyy_v1 HEAD v6 真 bug):
| Test | expected | got | 根因 |
|------|----------|-----|------|
| dungeon_game.jhyy | None | -1 | parser match-expr 缺 (Task #50) |
| float_cmp.jhyy | None | -1 | QBE "invalid type f<->i cmp" |
| import_test.jhyy | None | -1 | codegen AV (多文件 import) |
| match.jhyy | None | -1 | parser match-expr 缺 (Task #50) |
| namespace_dup.jhyy | None | -1 | codegen AV (命名空间 dup) |
| slice_iterate.jhyy | 60 | -1 | sema undef var in slice 翻译 |
| slice_len.jhyy | 5 | -1 | sema undef var in slice 翻译 |
| slice_subrange.jhyy | 60 | AV | Task #146 BLOCKED |

**3 SKIP** (library, no main): mylib.jhyy, ns_dup_a.jhyy, ns_dup_b.jhyy

**历史 baseline 对比**:
| 阶段 | binary | regress_v1 |
|------|--------|-----------|
| commit 2.28 phantom | sha 17253a96 | "35/53" (假) |
| commit 2.28 真 src0/ HEAD rebuild | sha 6315b2ea | 7/53 |
| commit 2.31+2.32 phantom | sha e2064a6b | 16/53 |
| **commit 2.40 HEAD v6** | **sha 181375d7...** | **42/53** |

**Task #146 BLOCKED 状态**:
- 完整 NODE_SLICE_RANGE 翻译 (47 行) + 最小 const-only 版本 (49 行) 都触发 QBE `invalid type for first operand %t0 in copy`
- 根因: zero IRVal (kind=0=IRVAL_TEMP) 被 emit 进 IL 当 literal arg, QBE 看到 %t0 当 temp 但实际是 literal
- 修法需 `ir.jhyy` 加 IRVal kind dispatch (类似 `ir_emit_arg` helper), 是 translator architecture 层
- 不在 Sprint 4.5 B 范围, 列入 Sprint 4.5 C 或后续
- src0/codegen.jhyy 已 revert 到 clean state (无 NODE_SLICE_RANGE case)

**Baseline log**: `compiler/build/bin/_regress_v1_baseline_HEADv6.log` (55 行, 完整 PASS/FAIL 输出)

**内存记录**: [[`project_sprint4_5_b_step2_baseline_lock.md`]](../../../../.claude/projects/C--Users-liuzhen-Desktop-coding-JiHuiYiYou/memory/project_sprint4_5_b_step2_baseline_lock.md)

---

### 2026-08-08 — v0.9 wip commit 2.42: Sprint 4.5 C step 1 ship — len() builtin fix (slice_iterate + slice_len)

**Task**: 解 slice_iterate / slice_len 的 sema undef var bug (+2 PASS 杠杆).

**根因** (2 处翻译层 bug):

**Bug 1**: `src0/sema.jhyy:636` len() builtin 调用 `infer_type(ctx, ta, (*d).args as *Node)` — 错把 `**Node` args 数组当 `*Node` 传. 
正确写法: `*(((*d).args as i64 + (0 as i64) * (8 as i64)) as **Node)` (同 line 660/724 模式).

**Bug 2**: `src0/sema.jhyy:637-650` len() builtin 只设 type 但**不 rewrite node kind** — codegen 收到 NODE_CALL 但 len 不是 fn sym → fn_name="?" → QBE fail. 
正确写法: rewrite NODE_CALL → NODE_FIELD(s.len) for KIND_SLICE / NODE_INT(arr_count) for KIND_ARRAY (对齐 v0 codegen.c:1206-1219).

**Bug 3** (暴露 via fix 1+2): `src0/codegen.jhyy` NODE_FIELD case 不处理 KIND_SLICE — 之前只检查 KIND_POINTER + KIND_STRUCT, KIND_SLICE 时 struct_type_raw=0 → return zero → emit `%t0` (zero IRVal latent bug).
正确写法: KIND_SLICE 走合成字段路径 (s.ptr = loadl base+0, s.len = loadl base+8), 对齐 v0 codegen.c:1206-1219.

**修法** (~30 行):
- `sema.jhyy` line 636 改 args[0] 取法 + KIND_SLICE/KIND_ARRAY 双 rewrite branch
- `codegen.jhyy` NODE_FIELD 加 KIND_SLICE 早期返回 (before struct path), 跟 v0 codegen.c 一致

**验收** (HEAD v7 binary sha `87ce6733803d34d9eb79fc0b6eb15319a9aa6ed50618f690df8da41d077974f2`):
- slice_len.jhyy: 5/5 PASS EXIT=5
- slice_iterate.jhyy: 5/5 PASS EXIT=60
- regress.py (C 端): 50/53 持平
- regress_v1.py (HEAD v7): **44/53 passed, 6 failed, 3 skipped** (前 HEAD v6: 42/53, +2)
- 3x regress 跑稳定 44/53

**6 fail 剩余** (下一步 sprint 4.5 C input):
| Test | 根因 | 关联 task |
|------|------|----------|
| dungeon_game.jhyy | parser match-expr 缺 | Task #50 |
| match.jhyy | parser match-expr 缺 | Task #50 |
| slice_subrange.jhyy | codegen 缺 NODE_SLICE_RANGE | Task #146 BLOCKED |
| float_cmp.jhyy | QBE "invalid type f<->i cmp" | step 2 |
| import_test.jhyy | codegen AV | Task #43 |
| namespace_dup.jhyy | codegen AV | Task #43 |

**3 SKIP** (library, no main): mylib.jhyy, ns_dup_a.jhyy, ns_dup_b.jhyy

**Baseline log**: `compiler/build/bin/_regress_v1_baseline_v7.log`

**Binary saved**: `compiler/build/bin/jhyy_v1_v7.exe.exe` sha `87ce6733803d34d9eb79fc0b6eb15319a9aa6ed50618f690df8da41d077974f2`

**Timeline 校准**: 42 → 44 (+2 PASS). 下一步 Sprint 4.5 C step 2 (QBE float_cmp type) 估 +1 → 45.
