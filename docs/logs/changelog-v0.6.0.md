# JHYY v0.6.0 Changelog

## 版本目标

v0.5.0 通过了自举前的质量门禁（bug 修复 + ABI v1.0.0 + MCP + 压力测试），但留下了 2 个 pre-existing 失败和 4 个 P2/P3 特性。**v0.6.0 是自举前的最后一期准备**，完成后直接进入 v1.0.0 = 编译器自举（用 JHYY 写 JHYY）。

本版本定位：
- 补齐"自举必须"的语言特性：切片 codegen、模块命名空间、`*T ↔ usize` 转换
- 修复 v0.5 留下的 2 个 pre-existing 失败
- Stage 0 试点：`arena.jhyy` 完整翻译，验证 v0.6 编译器能编译 JHYY 编写的 JHYY 编译器模块
- 不引入 v1.x 高级特性（闭包、泛型、async、function pointers）
- 不做完整 Phase 2 翻译（那是 v1.0.0 / v1.1.0 的事）

---

## Sprint 6A: 切片 codegen

### 6A.1 类型表示

`[*]T` 在 codegen 层 = `{ptr: *T, len: i64}` 16 字节布局：

```
offset  field
0       ptr  (*T)
8       len  (i64)
```

ABI：按 struct pass-by-value 走 sret（与 v0.4 锁定的 struct ABI 一致）。

### 6A.2 切片字面量与数组 decay

```jhyy
let arr: [i32; 3] = [1, 2, 3];
let s: [*i32] = arr as [*i32];   // 数组 → 切片（隐式 decay）
let s2: [*u8] = "hello" as [*u8]; // 字符串 → 字节切片
```

codegen 把数组字面量的栈地址 + 长度构造成 `{ptr, len}` 结构。

### 6A.3 索引、子切片、长度

```jhyy
let s: [*i32] = &[1, 2, 3];
let first = s[0];        // *(s.ptr + 0)
let slice = s[1..3];     // 子切片 = {s.ptr+1, 2}
let n = len(s);          // s.len 字段
```

### 6A.4 新增测试

- `slice_literal.jhyy`
- `slice_index.jhyy`
- `slice_subrange.jhyy`
- `slice_iterate.jhyy`
- `slice_len.jhyy`
- `slice_to_slice.jhyy`
- `array_to_slice.jhyy`

---

## Sprint 6B: 模块命名空间

### 6B.1 限定调用语法

```jhyy
import math;
let r = math::factorial(5);
```

### 6B.2 Sym.module + 名称修饰

- `Sym` 增加 `const char *module` 字段（NULL = main）
- 跨模块函数 emit 时 mangle 为 `$mod__name`（如 `$math__factorial`）
- 同名函数在不同模块中不再冲突

### 6B.3 sema 解析

`NODE_QUALIFIED_CALL` 携带 `module + function`，sema 在全局作用域按 `{module, name}` 查找函数符号。

### 6B.4 codegen 名称修饰

`emit_mangled_name` 辅助函数：sym->module 非空时 emit `$mod__name`，否则 emit `$name`。

### 6B.5 main.c 解析

- `resolve_one_import` 接受 extra_paths（CLI 输入文件）
- `in_progress` 与 `completed` 分离（解决循环检测误报）
- 主文件目录 fallback：找不到 slash 时用 "."

### 6B.6 新增测试

- `multi_file/main.jhyy` 改为使用 `lib_a::get_a()` 等限定调用
- `multi_file/lib_a.jhyy`, `lib_b.jhyy`, `lib_c.jhyy`（传递性 import）
- `namespace_dup.jhyy` — 不同模块同名函数 `ns_dup_a::process()` vs `ns_dup_b::process()`
- `namespace/main.jhyy` — 完整 demo

---

## Sprint 6C: `as` 类型转换补全

### 6C.1 指针 ↔ usize 互转

```jhyy
let x: i32 = 42;
let p = &x;
let addr = p as i64;       // *T → i64 (usize equivalent)
let back = addr as *i32;   // i64 → *T
let v = *back;             // dereference recovered pointer
```

实现：sema 接受 `KIND_POINTER ↔ KIND_PRIMITIVE(i64/u64)` 互转；codegen emit `extsw`/`truncd` 或直接 `copy`（指针本身就是 l/i64）。

### 6C.2 cast_ptr_to_int.jhyy 测试

验证指针与整数互转的 codegen 正确性。

---

## Sprint 6D: Pre-existing bug 修复

### 6D.1 import_test.jhyy 路径 bug

- **症状**：main_path 没有 slash 时 resolve_imports 误拼 `main.jhyy/imported.jhyy`
- **修复**：dir 提取 fallback 到 `"."`

### 6D.2 mylib.jhyy link bug

- **症状**：mylib/imported 等库文件被 regress.py 当作主程序 link 失败
- **修复**：regress.py 检测无 `main_jhyy` 的库文件并 SKIP（不计入 passed/failed）

### 6D.3 NODE_ADDR_OF 修复

- **症状**：`&x`（x 是不可变 scalar）返回 SSA 值而非地址，导致 `*ptr = ...` 修改不可见
- **修复**：SSA temp 取址时 spill 到新栈 slot，更新 local 条目为 is_stack=1

### 6D.4 NODE_DEREF 修复（pointer-to-struct）

- **症状**：`*ptr`（ptr 是 `*Struct`）错误地 `loadw` 4 字节
- **修复**：deref 对 pointer-to-struct 返回指针本身（struct by-address 语义）

### 6D.5 NODE_FIELD 修复（pointer-to-struct field access）

- **症状**：`(*ptr).field` 走错分支，field load 使用 'w' 宽度
- **修复**：codegen 检测 pointer-to-struct 走正确分支，使用 `qbe_type_of(field_type)` 决定 load 宽度

### 6D.6 NODE_ASSIGN 新增 NODE_FIELD 处理

- **症状**：`(*ptr).field = val` 完全无效果（codegen 不处理 NODE_FIELD target）
- **修复**：新增 NODE_FIELD 分支：计算 base+offset → store 到字段地址

### 6D.7 extern fn 不再被 mangle

- **症状**：`extern fn malloc(...)` 在 arena.jhyy 中被 mangle 成 `arena__malloc`，链接失败
- **修复**：`Sym.is_extern` 字段 + codegen 检查：extern fn 直接 emit 原名

---

## Sprint 6E: Stage 0 自举试点 — arena.jhyy

### 6E.1 arena.jhyy 翻译

将 `compiler/src/arena.c`（95 行 C）翻译成 `compiler/jhyy-src/arena.jhyy`（约 120 行 JHYY）。

**翻译要点**：
- `size_t → i64`、`void* → *u8`
- `varargs` (arena_sprintf) 暂不支持，省略
- 自引用结构体指针用 `*u8 + as *ArenaBlock` 转换绕过
- 指针算术通过 `(ptr as i64 + off) as *u8` 显式表达（JHYY `+` 不支持 pointer+integer）
- 所有整数常量加 `as i64` 后缀

### 6E.2 arena_test.jhyy driver

`compiler/tests/examples/arena_test/arena_test.jhyy` 验证 6 项功能：

| 测试 | 验证内容 |
|------|---------|
| arena_init | 设置 default_size 为 1024 |
| arena_alloc 200 次 | 触发新 block 分配 |
| arena_calloc | 零初始化 |
| arena_strdup | 字符串复制 + null 终止 |
| arena_reset | cur 回到 block 起始 |
| arena_free | 释放所有 block，无 double-free |

**结果**：通过（exit=42，heap-corruption-free）。

### 6E.3 self-hosting 准备度

`arena.jhyy` 演示了：
- ✅ 模块 import + 命名空间调用
- ✅ FFI（malloc/free/memset/memcpy）
- ✅ struct 定义 + 指针字段
- ✅ `let mut` + 不可变变量
- ✅ while 循环 + 早退
- ✅ 复合条件 + 短路

发现并修复的 v0.5 隐藏 bug（见 6D 节），证明 v0.6 编译器对编译自身模块的能力已达标。

---

## Sprint 6F: 文档

### 6F.1 新增文档

- `docs/logs/changelog-v0.6.0.md`（本文档）
- `docs/plans/v0.6.0任务清单 + 概要设计.md`
- `docs/plans/v0.6.0详细实现方案.md`

### 6F.2 更新文档

- `docs/abis/jhyy-lang-spec-v1.0.0.md` — 加入 切片/命名空间/as 转换语法
- `CLAUDE.md` — 同步 v0.6.0 状态到"当前状态"段

---

## 验证

### 回归测试

```
python compiler/build/bin/regress.py
===== 43/46 passed, 0 failed, 3 skipped =====
```

3 个 skipped 是库文件（无 main_jhyy）：mylib、ns_dup_a、ns_dup_b。

### 零警告构建

```bash
gcc -std=c11 -Wall -Wextra compiler/src/*.c -o compiler/build/bin/jhyy.exe -I compiler/src
```

无 warning，无 error。

---

## v0.6 → v1.0 路径

按 `phase-总规划-v0.2.x-to-v1.0.0.md` 的"严格按依赖顺序推进"原则：

- v0.6 已完成所有"自举必须"特性
- v1.0.0 = 启动自举（用 JHYY 写 JHYY），版本号跳跃标志 Phase 切换
- v1.1 / v1.2 = 逐步翻译 C 编译器模块到 JHYY

下一期：**v1.0.0 自举启动**。