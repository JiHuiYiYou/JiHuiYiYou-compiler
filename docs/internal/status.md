# 当前状态

> 语言特性 / 已知限制 / 历史修复。版本进展详见 `docs/logs/`。

## 当前版本: v0.6.3

> Phase 1 — C 语言宿主编译器。v1.0.0 启动完整自举。v0.6.3 是 phase-2 自举前最后一期 C 端 patch（修 sprint 2 commit 3a 实测沉淀的 #9 f64/f32 比较 + call-site f64↔f32 隐式转换；#8 维持 `jh_f64_store` 桥）。

回归基线：**44/47 passed, 0 failed, 3 skipped**（3 skipped 是库文件，无 `main_jhyy`）。

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
| `extern fn` FFI 声明 (含 printf, 文件 I/O) | 完成 |
| FFI 多参数调用 (≥3 参数) | 完成 (v0.4) |
| 复合赋值 (`+=`, `-=`, `*=`, `/=`, `%=`) | 完成 |
| import 模块系统 (含传递性导入) | 完成 (v0.4) |
| 多文件 CLI 输入 | 完成 (v0.4) |
| 模块命名空间 `mod::fn()` | 完成 (v0.6) |
| Claude Code MCP 服务 (7 工具 + 4 资源) | 完成 (v0.5) |
| Stage 0 自举试点 (`arena.jhyy` 翻译) | 完成 (v0.6) |
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
| **P3** | 缺失 | 函数回调 (Phase 2 考虑) |
| **P3** | 缺失 | Windows 下 `jhyy run` 子命令 `system()` 路径有 bug (P1) |

### Phase 2 阻塞分析（2026-06-22 验证）

abi § 11.1 五个阻塞自举问题（A1-A5）中，A1/A2/A4 已 ✓。**A3 / A5 不阻塞 phase-2**：

**A3（struct/enum 跨 FFI by-value）** —— 编译器自身用不到：
- phase-2 FFI 列表（malloc/free/fopen/fread/fwrite/fprintf/strlen/strcmp/system/exit）全 pointer/scalar
- 源码 grep 仅 `struct Arena *`（指针，非 by-value），无 `extern fn foo() -> struct X` 模式
- 可延后到 phase-3（用户代码要调 C 函数传 struct 时再处理）

**A5（浮点 NaN/Inf + 不完整运算）** —— 编译器自身不用 float 算术：
- `double` 实际用途只有 2 处：`atof()` 解析字面量、`NodeFloat { double value; }` AST 字段
- codegen 用 `%.17g` 把 double 格式化为 QBE IL `d_xxx` 文本，**不做算术**
- 无 `addd`/`muld`/`divd` 等浮点指令
- v0.5 sprint 5A 已实现 float 字面量 codegen + 基础算术。P3 的 NaN/Inf 是**算术语义**（`0.0/0.0`、`NaN == NaN`），编译器不跑 float 算术所以碰不到
- 可延后到 phase-3a（float stdlib），届时 NaN/Inf 规约与算术语义统一处理

**v0.6 已解决**：
- ✅ 切片 `[*]T` codegen
- ✅ 模块命名空间 (`mod::fn()`)
- ✅ `*T ↔ i64` 互转 (`as`)

---

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
- **Stage 0 翻译**：`compiler/jhyy-src/arena.jhyy`（arena.c → JHYY），验证自举能力
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
- **MCP 服务**：7 工具 (compile/run/check/get_il/lang_ref/abi_info/format) + 4 资源

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

**v0.6.0 已完成（tagged）**。v0.7+ 路线取决于 v0.6 自举试点的进一步成果。

v1.0.0 = 完整自举：编译器编译自己并跑同一组测试通过。
