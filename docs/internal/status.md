# 当前状态

> 语言特性 / 已知限制 / 历史修复。版本进展详见 `docs/logs/`。

## 当前版本: v1.0.0 tagged (commit `eabee0d`, 2026-08-10)

> **v1.0.0** — Stage 2 N=3 byte-equal 闭环达成。`jhyy_v1 → jhyy_v2 → jhyy_v3 → jhyy_v4` 编译自身,产出 4 份 sha 完全一致的 raw `.il` 文件 (sha `2445e97d...`, 1.378 MB, 无 fix-up 后处理)。
>
> 详尽 ship 记录见 [`docs/logs/v1/changelog-v1.0.0.md`](../logs/v1/changelog-v1.0.0.md)。本文件专注当前功能状态 + 已知限制 + 历史修复索引。
>
> v0.9 wip 阶段（commit 2.1-2.83）作为 v0.x 收尾主线，主要里程碑：
> - **v0.9 commit 1** (ce93f64) — 29-extsw hypothesis 验证
> - **v0.9 wip commit 2.5-2.9** — Stage 1 byte-equal 7 测试集 + B-let2/B-φ1/B-data/B-struct/B-match 真修
> - **v0.9 wip commit 2.10-2.11** — W-005 真修 (CGContext C/jhyy 布局对齐)
> - **v0.9 wip commit 2.12a-2.12b** — match-expr 翻译补全 (byte-equal 5/7 → 6/7)
> - **v0.9 wip commit 2.13-2.17** — W-005 加固 / W-004 文档 / Task #60 真修 / AUDIT 5 struct / C' 确定性 audit
> - **v0.9 wip commit 2.42-2.43** (Sprint 4.5 C) — len() builtin 翻译层 bug 修 + cg_convert_arg D→S unreachable 分支修
> - **v0.9 wip commit 2.75-2.83** (Sprint 4.18-4.5 E+ style cleanup) — fix_il.py 完整化 / Sprint 4.25 W-005 #2 + sret 真修 / Stage 2 N=3 byte-equal 实证 / workarounds.md W-008 文档 / Phase 2 Style Cleanup
>
> v0.8 wip commit 12 是 v0.9 前一版（12 commits → Stage 0 closure 解锁）。v0.7.0 是更前版（7A enum first-class + 7B 顶层 const 数组）。

回归基线 (v1.0.0 锁定)：
- **jhyy_0 (C 编译) regress.py**: **50/53 passed, 0 failed, 3 skipped**（3 skipped 是库文件，无 `main_jhyy`）
- **jhyy_v1 (自举) regress_v1.py**: **50/53 passed, 0 failed, 3 skipped**（与 C 端 baseline 持平）
- **Stage 1 byte-equal**: **7/7 PASS**（jhyy_0 vs jhyy_v1 对 7 测试集产出 byte-equal `.il`）
- **Stage 2 N=3 byte-equal**: ✅ **sha `2445e97d...` 4-hop 稳定**（jhyy_v1/v2/v3/v4 四份 raw `.il` 字节相同, fixed point 是 attractor）

---

## 已实现的语言特性

| 特性 | 状态 |
|------|------|
| 整数/浮点/字符串/字符/布尔字面量 | 完成 |
| 浮点字面量 codegen (f32/f64) | 完成 (v0.3) |
| 浮点算术 `+ - * /` (f32/f64) | 完成 (v0.5) |
| `let` / `let mut` 变量绑定 | 完成 |
| 定长数组 `[T; N]`：字面量/类型注解/下标读写 | 完成 (v0.3) |
| 切片 `[*]T`：字面量/index/subrange/len | 完成 (v0.6) |
| 顶层 const 数组 (`const NAME: [T; N] = [...]`) | 完成 (v0.7) |
| 二元运算 (算术/比较/位运算) | 完成 |
| `&&` / `\|\|` 短路求值 | 完成 |
| 一元运算 (`-`, `!`, `~`) | 完成 |
| 类型转换 `as` (整数/浮点互转, 扩宽/截断) | 完成 (v0.5) |
| `as` 指针↔整数 (`*T ↔ i64/u64`) | 完成 (v0.6) |
| `if`/`else` 表达式 (含嵌套 if/else if, void 分支) | 完成 |
| `while` 循环 (含 break/continue) | 完成 (v0.5) |
| `for i in start..end` 循环 (类型感知, break/continue) | 完成 |
| `break;` / `continue;` | 完成 (v0.5) |
| 函数 (参数/返回/递归/return 类型检查) | 完成 |
| `return` 提前返回 | 完成 |
| 块表达式 `{ ... }` | 完成 |
| 指针 `&x`, `*ptr`, `*ptr = val` | 完成 |
| struct 定义/字面量/字段访问 | 完成 |
| struct 按值传递/返回/赋值 | 完成 (v0.4) |
| struct 字段通过指针 (`ptr->field`) | 完成 |
| enum 定义/变体构造 (一致内存布局) | 完成 |
| `match` 表达式 (字面量/通配符/范围) | 完成 |
| enum match 穷尽性检查 (未覆盖 variant 报错) | 完成 (v0.7) |
| 短名 variant pattern (`Some(v)` / `None`) | 完成 (v0.7) |
| `extern fn` FFI 声明 (含 printf, 文件 I/O) | 完成 |
| FFI 多参数调用 (≥3 参数) | 完成 (v0.4) |
| 复合赋值 (`+=`, `-=`, `*=`, `/=`, `%=`) | 完成 |
| import 模块系统 (含传递性导入) | 完成 (v0.4) |
| 多文件 CLI 输入 | 完成 (v0.4) |
| 模块命名空间 `mod::fn()` | 完成 (v0.6) |
| Claude Code MCP 服务 (11 工具 + 4 资源) | 完成 (v0.5 + mcp-jhyy Sprint 1 2026-08-11) |
| Stage 0 自举试点 (`arena.jhyy` 翻译) | 完成 (v0.6) |
| **v1.0.0 真自举 byte-equal 闭环** | **完成 (2026-08-10 commit `eabee0d`)** |
| 控制台输出 (中文 UTF-8 + 数字 printf) | 完成 |
| Arena allocator (via FFI) | 完成 |

---

## 已知限制

| # | 严重度 | 描述 |
|---|--------|------|
| **P2** | 不完整 | 浮点比较 (`==`/`<`/...) 部分场景未完全类型化 |
| **P3** | 缺失 | 浮点 fmod (`%`) 未实现 |
| **P3** | 缺失 | struct/enum 跨 FFI 边界 (Windows x64 ABI 不兼容) |
| **P3** | 缺失 | 变参函数 (`printf` 的 `...`) 在 JHYY 侧需展开 |
| **P3** | 缺失 | 函数回调 (v1.x 考虑) |
| **P3** | 缺失 | Windows 下 `jhyy run` 子命令 `system()` 路径有 bug (P1) |
| **P3** | 缺失 | Pattern binding codegen（`Some(v) => v` 提取 payload）—— 7A 仅 sema 层注册 binding，codegen 用 `_` 通配符规避 |
| **P3** | 缺失 | 嵌套 const array（`[[i32; N]; M]`）、const pointer / const slice / const enum array —— sema 拒绝 |
| **P2** | 后端 bug | **jhyy 编译器 amd64_win 后端 stack-spill**（sprint 3 commit 5/6 实测）：`infer_type → IDENT → symtab_lookup_local → symtab_lookup_one` 在特定调用栈深度 + 大结构传参下崩溃。临时 workaround 在 `compiler/src0/symtab.jhyy:255-258`（`sb_init` 触发 arena_alloc 改变栈帧大小）。完整记录见 `docs/plans/v1/v1.0.0详细实现方案.md` § 3.6 和 `docs/logs/v1/sprint-3-commit-6-sema-cleanup.md`。修复路径：v2.x QBE rewrite |

### v1.x 阻塞分析（2026-06-22 验证）

abi § 11.1 五个阻塞自举问题（A1-A5）中，A1/A2/A4 已 ✓。**A3 / A5 不阻塞 v1.x**：

**A3（struct/enum 跨 FFI by-value）** —— 编译器自身用不到：
- v1.x FFI 列表（malloc/free/fopen/fread/fwrite/fprintf/strlen/strcmp/system/exit）全 pointer/scalar
- 源码 grep 仅 `struct Arena *`（指针，非 by-value），无 `extern fn foo() -> struct X` 模式
- 可延后到 v3.x（用户代码要调 C 函数传 struct 时再处理）

**A5（浮点 NaN/Inf + 不完整运算）** —— 编译器自身不用 float 算术：
- `double` 实际用途只有 2 处：`atof()` 解析字面量、`NodeFloat { double value; }` AST 字段
- codegen 用 `%.17g` 把 double 格式化为 QBE IL `d_xxx` 文本，**不做算术**
- 无 `addd`/`muld`/`divd` 等浮点指令
- v0.5 sprint 5A 已实现 float 字面量 codegen + 基础算术。P3 的 NaN/Inf 是**算术语义**（`0.0/0.0`、`NaN == NaN`），编译器不跑 float 算术所以碰不到
- 可延后到 v3.xa（float stdlib），届时 NaN/Inf 规约与算术语义统一处理

**v0.6 已解决**：
- ✅ 切片 `[*]T` codegen
- ✅ 模块命名空间 (`mod::fn()`)
- ✅ `*T ↔ i64` 互转 (`as`)

---

## 已修复 — v0.7.0

- **enum match 穷尽性检查**（7A）：sema 强制每个 variant 必须被覆盖（literal/range pattern 不算），未覆盖报错
- **短名 variant pattern**（7A）：`Some(v)` / `None` 作为 `Option::Some(v)` / `Option::None` 的语法糖
- **match dangling next_check label 修复**（7A）：全 non-wildcard arm 时补 emit label
- **顶层 const 数组声明**（7B）：`const NAME: [T; N] = [elem, ...]`，emit 到 QBE `.data` 段（DYNCONST 0-cost load）
- **const array struct 平铺**：data section emit 时 struct 字段平铺成 `w`/`l` 等基本类型
- **arr_of_structs[i].field codegen 修复**（7B 附带）：NODE_INDEX struct elem 返回地址而非 load；cg_emit_store struct 走 cg_copy_struct 字段级拷贝
- **sub-word load 类型修正**（7B 附带）：loadub/loadsb/loaduh/loadsh 返回 word (`w`)
- **新增 2 个测试**：const_array, const_struct_array
- **47/50 回归通过**（3 skipped = 库文件）

## 已修复 — v0.6.0

- **切片 `[*]T` 完整 codegen**：字面量 / index / subrange / len / array decay
- **模块命名空间**：`mod::fn()` 限定调用 + `Sym.module` 字段 + `$mod__name` mangle
- **`as` 类型转换补全**：`*T ↔ i64` 互转
- **NODE_ADDR_OF 修复**：SSA temp 取址时 spill 到新栈 slot
- **NODE_DEREF 修复**：pointer-to-struct 返回指针本身（by-address）
- **NODE_FIELD 修复**：pointer-to-struct field access 用正确 qbe_type
- **NODE_ASSIGN 新增 NODE_FIELD**：`(*ptr).field = val` 现在生效
- **extern fn 不再 mangle**：`arena.jhyy` 的 `extern fn malloc` 直接 emit 原名
- **resolve_imports dir fallback**：主文件路径无 slash 时回退到 `"."`
- **regress.py 跳过库文件**：无 `main_jhyy` 的文件 SKIP，不算 failed
- **Stage 0 翻译**：`compiler/src0/arena.jhyy`（arena.c → JHYY），验证自举能力
- **新增 7 个测试**：slice_*, namespace_dup, cast_ptr_to_int
- **43/46 回归通过**（3 skipped = 库文件）

## 已修复 — v0.5.0

- **浮点算术 codegen**：f32/f64 `+ - * /` 使用 `adds`/`subs`/`muls`/`divs`/`addd`/`subd`/`muld`/`divd`
- **类型转换 `as`**：整数扩宽 (exts), 浮点↔整数 (dtosi/sltof), 浮点互转 (exts/truncd)
- **if/else void 分支修复**：无值分支时不发 phi
- **嵌套 if/else if phi 修复**：预分配 trampoline 块 `ep` 避免前驱块标签错
- **if-as-block-return-value 修复 (关键 bug)**：cg_block 对 NODE_IF/NODE_MATCH/NODE_BLOCK 也调用 cg_expr 捕获值
- **break/continue**：while/for 循环支持, for 循环单独 `incr_b` 块
- **i32 整数溢出**：定义为二补码环绕, 行为有测试覆盖
- **零警告构建**：main.c cmd buffer 2048 → 4096 修复 snprintf 截断 warning
- **新增 10 个专项测试**：break_continue, float_arith, fib30, big_array, overflow, nested_if, void_if, ptr_self_assign, big_test
- **Python 回归脚本**：`compiler/build/bin/regress.py` 自动运行所有 .jhyy 测试
- **ABI 白皮书 v1.0.0**：锁定 struct pass-by-value, 多文件, FFI, break/continue
- **MCP 服务**：11 工具 (compile/run/check/get_il/lang_ref/abi_info/format + regress/il_diff/selfhost_check/workarounds) + 4 资源

## 已修复 — v0.4.0

- **struct 按值传递**：调用方分配栈拷贝, `cg_copy_struct` 逐字段复制
- **struct 返回值 (sret)**：调用方分配返回槽, 隐式传递指针, 被调用方写入
- **struct 赋值**：`a = b` 逐字段复制 (含嵌套 struct)
- **NODE_IDENT struct 修复**：返回地址而非 load 值
- **NODE_LET struct 修复**：不 mutable struct 也使用栈分配
- **NODE_RETURN sret**：复制到返回槽后 emit bare ret
- **cg_func sret header**：sret 函数签名添加隐藏指针参数
- **传递性 import**：递归解析, 循环检测, 访问列表持久化
- **多文件 CLI**：`jhyy compile a.jhyy b.jhyy -o output`
- **cmd_build 修复**：增加 `resolve_imports` 调用
- **新增辅助函数**：`cg_copy_struct`, `ir_emit_call_void`, `resolve_one_import`
- **CGContext 扩展**：`sret_slot`, `has_sret` 字段

## 已修复 — v0.3.0

- **Bug 1** Pratt 解析器优先级: `-`/`*`/`&` 双角色 token 使用 PREC_TERM/FACTOR/BIT_AND 而非 PREC_UNARY
- **Bug 2** 嵌套 if/else if/else phi 前驱块标签错误 — 添加 trampoline 块
- **Bug 3** if/else void 分支 phi 类型错误 — 已通过 void 返回类型处理修复
- **Bug 4** 浮点字面量 codegen 硬编码 0.0 — 格式化为 QBE `d_`/`s_` 字面量
- **ir_emit_alloc**：QBE 对齐值修复 (仅支持 4/8/16)
- **sema NODE_CALL**：参数类型推断递归 (修复 `arr[i]` 直接作为函数参数)
- **定长数组 `[T; N]`**：完整 codegen (类型注解/字面量/下标读写/赋值)
- 新增 AST 节点：`NODE_ARRAY_TYPE`, `NODE_ARRAY_LIT`

## 已修复 — v0.2.1

- P0-A symtab FNV-1a → 开放寻址 + 线性探测
- P0-B sub-word 类型 (i8/u8/i16/u16) load/store 使用正确宽度
- P0-C 比较指令类型感知 (signed/unsigned × w/l)
- P0-D 64 位移位使用正确宽度
- P1 Windows `jhyy run` path_to_win() 修复（后来 v0.5 又冒出新变种）
- P1 return 语句类型正确传播，函数体类型检查修复
- P2 `&&`/`||` 短路求值 (分支跳转 + phi)
- P2 enum payload_offset 存储在 Type 中，sema/codegen 一致
- P2 for 循环变量类型感知 (使用 type_size + qbe_type_of)
- 控制台 UTF-8 输出 (SetConsoleOutputCP)
- 字符串转义序列 (\\n, \\t, \\r, \\0, \\\\, \\\", \\xHH)
- 函数体已有 return 时不再重复 emit ret

---

## 当前 sprint / 下一阶段

**v1.2.0 — src0/ 自然化**（4 commits ship, 2026-08-12 — commits `2c92cf4` / `f49e64d` / `1c24841` / `0026098`）：v1.0.0 闭环后第一个 v1.x 清理 sprint — 完成 W-005 (16 处 `let mut x_v1` style revert) + W-003 (24 处 `let _ = fncall()` revert) + `_v1`/`_v2`/`_v3`/`_v4`/`_v5` 后缀 99 处 cleanup 跨 src0/ 3 文件。Plan 见 [`docs/plans/v1/v1.2.0任务清单 + 概要设计.md`](../plans/v1/v1.2.0任务清单 + 概要设计.md);ship 记录见 [`docs/logs/v1/changelog-v1.2.0.md`](../logs/v1/changelog-v1.2.0.md)。

**v1.1.0 batch ship**（commits 1.1-1.9, 2026-08-05 ~ 2026-08-11）：6 sprint 全部 ship — W-007 docs / W-003 docs / Bug 1-4 真修 / batch close。详细 ship 记录见 [`docs/logs/v1/changelog-v1.1.0.md`](../logs/v1/changelog-v1.1.0.md)。

**v1.0.0 真自举闭环** ✅（2026-08-10 commit `eabee0d`）：Stage 2 N=3 byte-equal 达成 — 详尽 ship 记录见 [`docs/logs/v1/changelog-v1.0.0.md`](../logs/v1/changelog-v1.0.0.md)。

**v0.9 wip**（commit 2.83 ship, 2026-08-11）：v0.x 收尾主线 — Stage 1 byte-equal **7/7** + Stage 2 N=3 byte-equal 闭环 (sha `2445e97d...`) + 2 个 audit 全 PASS (AUDIT 修 VariantDesc heap overflow / C' 验证 5 维度 by-construction deterministic)。详细进度见 [`docs/logs/v0/changelog-v0.9.0.md`](../logs/v0/changelog-v0.9.0.md)。

下一阶段：**v1.3** (v1.x 语法糖 Phase 4 of v1.0-post-50-53-plan.md) — null / else if / sizeof / for-in / `#[inline]` / defer / Pattern binding / OR pattern, 5-7 sprint。**v1.3 全 ship 后**启动 **v2.x** (QBE 完整重写 + amd64_sysv / freestanding) || **v3.x** (inline asm / `no_std` / `&mut` lifetime) 并行（OS 准备）→ [`docs/plans/v2/v2.0.0-os-prep.md`](../plans/v2/v2.0.0-os-prep.md) + [`docs/plans/roadmap/v2-v3-parallel-sprint-plan.md`](../plans/roadmap/v2-v3-parallel-sprint-plan.md)。OS 端等编译器推进（per `memory/project_os_wait_state.md`，v1.0 闭环达成前不主动 prep OS）。

已知 v1.0.0 后续未完成项（明确延后，非 blocker）：
- Stage 1 byte-equal 6/7 → 7/7（const_array 因 parser 翻译层缺 NODE_CONST_DECL 推迟；v1.x post-50-53 plan 处理）
- Pattern binding codegen（`Some(v) => v` 提取 payload）—— v1.x post-50-53 patch
- OR pattern 一致性检查（`Some(x) | Some(y)` 两边必须绑同名）
- 嵌套 const array（`[[i32; N]; M]`）—— 自举需要时再开
- const pointer / const slice / const enum array —— 需要 RTTI
- const fn / 编译期函数求值 —— 大特性，单独 sprint
- v0 codegen bug 1/2/3/4（LEA / phi / loadub / &local）—— workaround 已在 jhyy 源码里，v1.x post-50-53 收尾

---

## C-side vs jhyy_v1 IL divergence (Sprint v1.1.2 调查结论, 2026-08-12)

**观察**: `compiler/build/bin/jhyy.exe compile compiler/src0/main.jhyy -o jhyy_v2` 产出 `.il` sha `bccc452e...` ≠ tracked `v1.il` sha `2445e97d...`。

**结论 (调查后)**: **这是历史/期望行为,不是回归**。Stage 2 N=3 byte-equal 闭环只覆盖 self-hosted chain (`jhyy_v1 → v2 → v3 → v4`),**不覆盖 C-side**。

| 编译器 | 产出 .il sha | 大小 | 用途 |
|--------|------------|------|------|
| `jhyy_v1.exe.exe` (tracked closure) | `2445e97d...` | 1.378 MB | Stage 2 闭环 canonical |
| `jhyy.exe` (C-side) | `bccc452e...` | 1.402 MB | 日常开发 / Stage 0 jhyy_v1 重建 |
| `jhyy_v2.exe` / `v3.exe` (closure chain) | `2445e97d...` | 1.378 MB | Stage 2 闭环 4-hop 稳定 |

**差异根因**: Sprint 4.21-4.25 W-005 #2 真修 chain (commits `be3be33` / `fad9de2`) 在 C-side `compiler/src/codegen.c` 加了 8 处 `irval_is_undef` 守卫 + IRVal struct pass-by-value 真修。jhyy-side (`compiler/src0/codegen.jhyy`) 镜像同样守卫但 emit 不需要额外 `=l copy`(arena IRVal 不存在 stale pointer 问题)。**C-side 多 emit 的 `copy` 是 QBE no-op**(defensive copy for stale pointer guard),程序语义等价。

**Bisect 验证** (`git checkout <commit> -- compiler/src/`, 10 个候选):
- `1b86277` (v0.8 commit 1) → C-side emit `bc2331b8...`(已不同于 closure canonical)
- `589b91f` / `7e7632f` / `69be7c9` / `57f9845` / `f3dc1b1` → 各自不同 sha
- `f3dc1b1` (Stage 1 closure) → `bccc452e...`(stable since)
- `d3242e4` / `be3be33` / `fad9de2` / `7af6b45` → 全部 `bccc452e...`(已 stable)
- **从未有 C-side commit 产出 `2445e97d`** — jhyy_v1 emit 跟 C-side emit **历史就不同**

**操作规则 (新, 加进 conventions)**:
- ✅ C-side (`jhyy.exe`) 可写 `compiler/build/bin/jhyy.exe` + `.il` 派生(开发态)
- ❌ C-side **绝不可写** `jhyy_v1.exe` / `jhyy_v2.exe` / `jhyy_v3.exe`(污染 closure 链)
- ✅ C-side 写 `jhyy_v1.exe` 仅在初始 bootstrap(jhyy.exe 编 src0/main.jhyy → jhyy_v1.exe 一次性,产出后 freeze sha)
- ✅ 验证 closure 时用 `jhyy_vN.exe.exe` 编 `src0/main.jhyy`,永远不写回 `jhyy_v*.exe`

**本次 session 修复** (commit 不在 v1.0.0 主线):
1. `jhyy_v2.il` 被 C-side overwrite 为 `bccc452e` → 从 canonical `jhyy_v1.exe.exe` 重新生成 → 现在 `2445e97d` byte-equal v1/v3
2. `jhyy_v1.exe` / `jhyy_v2.exe` / `jhyy_v3.exe` 三个 tracked binary 被 C-side overwrite → `git checkout 3fa0983 -- compiler/build/bin/jhyy_v{1,2,3}.exe` 恢复 tracked canonical shas (`aa57849c` / `d3aeed09` / `536ffcb2`)
3. 仅 `jhyy_v1.exe.exe` (sha `ba94df93`) 保持干净,因该文件被 MCP `jhyy_regress` 强制 baseline 校验保护

---

## src0/ 自然化 (v1.2.0 sprint, 2026-08-12 ship)

**背景**: v1.0.0 自举闭环 (`eabee0d`) 用的 src0/ `main.jhyy` 是 v0 C 端 codegen.c 的**翻译产物** — 翻译过程为防 W-005 / W-003 stale-name 触发面加了防御性 `_vN` 后缀 + 替代语法 (`let mut xxx_v1` / `let _ = fncall()`)。v0.9 wip + v1.1.0 batch ship 全部把 W-005 #2 + W-003 + Bug 1-4 都真修了,这些 defense 不再需要 — 但 src0/ 还残留 99 处 pure rename 翻译产物,影响可读性 / 可审计性 / 后续 v3.x 命名空间清理。

**目标**: 把 src0/ 翻译产物里的 defense 全部撤回,接近"自然 jhyy"代码风格,但**不改任何 IR emit** (pure rename,Stage 1 byte-equal 7/7 持+Stage 2 N=3 byte-equal 7 行 cascade 持)。

**实施 (4 commits, 2026-08-12)**:

| Sprint | Commit | 类型 | grep 命中 | 跨 sprint |
|--------|--------|------|----------|----------|
| v1.2.1 | `2c92cf4` | W-005 `let mut x_v1` revert | 16 处 | regress 50/50, v2.il `a75bcd6e` |
| v1.2.2 | `f49e64d` | W-003 `let _ = fncall()` revert | 24 处 | regress 50/50, v2.il `a75bcd6e` (同 v1.2.1) |
| v1.2.3 | `1c24841` | `_v1` 后缀 cleanup | 63 处 / 19 unique identifier | regress 50/50, v2.il `348884af` |
| v1.2.4 | `0026098` | `_v2`/`_v3`/`_v4`/`_v5` 后缀 cleanup | 36 处 / 18 unique identifier | regress 50/50, v2.il `f75ef7e2` |

**纯 rename 验证 (跨 4 commit 一致)**:
- Stage 2 N=3 7 行 cascade（`@mergeXXXX` label 编号）：跨 v1.2.1/2.2/2.3/2.4 一致,证明 rename 零 IR 行为影响
- v2.il sha 跨 sprint 变化 (rename 改 QBE 符号名) 是预期的,跟 [[project-sprint-v1-1-2-c-side-divergence]] 一致性质
- regress.py 50/50 + regress_v1.py 50/50 + jhyy_v1.exe.exe sha `ba94df93` 全程持平

**不动的 defense (按 plan out-of-scope)**:
- 函数名 `resolve_one_import_v1` / `var_name_eq_v1` (改函数名是 v3.x 命名空间范畴)
- 描述 `jhyy_vN` / `regress_vN.py` 的 comment (历史叙述)
- `_W002_rename_map.txt` 翻译映射 comment

**Plan / 记录**:
- Plan: [`docs/plans/v1/v1.2.0任务清单 + 概要设计.md`](../plans/v1/v1.2.0任务清单 + 概要设计.md)
- Ship: [`docs/logs/v1/changelog-v1.2.0.md`](../logs/v1/changelog-v1.2.0.md)
- v1.2.5 commit 5 = doc sync (workarounds.md + status.md + changelog 收尾)

**下一阶段**: v1.3 (v1.x 语法糖 Phase 4 of v1.0-post-50-53-plan.md) — null / else if / sizeof / for-in / `#[inline]` / defer / Pattern binding / OR pattern, 5-7 sprint。
