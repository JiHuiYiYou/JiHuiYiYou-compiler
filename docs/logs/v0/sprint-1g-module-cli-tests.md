# Sprint 1g — 模块系统 + CLI + 测试套件 + Phase 1 完结

**日期**: 2026-06-05  
**状态**: 完成  
**版本**: v0.2.0

## 前置: P0 Bug 修复

在开始 1g 之前，集中修复了 4 个 P0 致命 bug：

### P0-A: Hash 表重写

- **问题**: FNV-1a 链式 hash 表在 10+ 条目后查找随机失败
- **修复**: 重写为开放寻址 (线性探测)，64-bit FNV-1a hash + power-of-2 表 + 0.75 负载因子自动扩容
- **影响**: symtab 查找稳定可靠

### P0-B: Sub-word 类型截断/扩展

- **问题**: i8/u8/i16/u16 使用 `loadw`/`storew`，无符号/零扩展
- **修复**: 添加 `cg_emit_load`/`cg_emit_store` helper，根据类型选择正确的 QBE 指令 (`loadsb`, `loadub`, `loadsh`, `loaduh`, `storeb`, `storeh`)

### P0-C/D: 比较/移位指令宽度

- **问题**: 所有比较硬编码为有符号 word (`csltw`)，u64/i64 比较和移位宽度错误
- **修复**: 比较指令根据操作数类型动态选择 (有符号/无符号 × w/l)，`ceql`/`cnel` 用于 64 位

---

## 1. CLI 完善

### `build` 子命令

```bash
jhyy build <file.jhyy> [-o output]  # 仅生成 .il, 不调用 QBE/GCC
```

### P1 修复: Windows `run` 路径

- **问题**: `system(exe)` 中 `/` 不被 cmd.exe 识别
- **修复**: `path_to_win()` 将 `/` 转换为 `\`

### 版本号

`jhyy compiler v0.2.0`

---

## 2. Import 系统

### 语法

```rust
// main.jhyy
import mylib;    // 加载同目录下的 mylib.jhyy

fn main_jhyy() -> i32 {
    mylib::function(args)
}
```

### 实现

1. **`resolve_imports()`** (main.c): 扫描 AST 中的 NODE_IMPORT_DECL，加载并解析被导入文件，将其顶层声明合并到主模块
2. **`symtab_insert_sym()`** (symtab.c): 将 parser 创建的 Sym* 直接插入 sema 的符号表，避免创建重复 Sym
3. **全局作用域 fallback** (sema.c): NODE_IDENT 在 locals 查找失败后，搜索 `ctx->global_scope` 查找导入的函数/类型

### 限制 (v0.2.0)

- 仅支持一级 import (不传递解析嵌套 import)
- 被导入模块中的 `import` 语句被跳过
- 路径相对于主文件所在目录
- 无命名空间隔离 (导入符号扁平放入全局作用域)

---

## 3. 测试套件

### 集成测试 (7 个 .jhyy 程序)

| 测试 | 预期 | 结果 | 验证特性 |
|------|------|------|---------|
| `hello.jhyy` | 42 | 42 | 基础流水线 |
| `demo.jhyy` | 0 | 0 | 全部 v0.0.1 特性 |
| `pointer.jhyy` | 100 | 100 | `&x`, `*p = val` |
| `struct.jhyy` | 30 | 30 | struct 定义/字面量/字段访问 |
| `match.jhyy` | 20 | 20 | match 表达式 |
| `forloop.jhyy` | 10 | 10 | for 循环 |
| `import_test.jhyy` | 72 | 72 | import 系统 |

---

## 4. Phase 1 完整变更汇总 (v0.0.1 → v0.2.0)

### 新增语言特性

- struct 定义和字面量、enum 定义和变体构造
- 指针 `&x`, `*ptr`, `*ptr = val`, struct 指针字段访问
- `match` 表达式 (字面量/通配符/范围模式)
- `for i in start..end` 循环
- `import` 模块系统
- `build` 子命令

### Bug 修复 (7 个)

| # | 严重度 | 描述 |
|---|--------|------|
| P0-A | 崩溃 | symtab hash 查找不稳定 |
| P0-B | 错误 | sub-word 类型无截断/扩展 |
| P0-C | 错误 | 比较指令硬编码为有符号 word |
| P0-D | 错误 | 64 位移位使用 w 宽度 |
| — | 崩溃 | parse_block stmts 数组扩容丢失数据 |
| — | 错误 | NODE_UNARY 未实现导致跨函数 temp 引用 |
| — | 错误 | `_` 通配符未识别为 PATT_WILD |
| P1 | 功能 | Windows `run` 命令路径错误 |

### 模块变更

| 文件 | 变更 |
|------|------|
| `symtab.h/c` | 重写: 链式 → 开放寻址; 新增 `symtab_insert_sym` |
| `ast.h/c` | 新增 NODE_STRUCT_DEF, NODE_ENUM_DEF |
| `parser.c` | 完整 struct/enum 定义解析; struct 字面量; enum 构造; `_` 修复; 数组扩容修复 |
| `sema.c` | struct/enum 布局计算; 三遍处理; Sym 指针匹配; 全局作用域 fallback |
| `codegen.c` | NODE_UNARY/NODE_ADDR_OF/NODE_DEREF/NODE_STRUCT_LIT/NODE_ENUM_VARIANT/NODE_MATCH/NODE_FOR/NODE_FIELD; sub-word load/store; 类型感知比较 |
| `main.c` | `build` 子命令; `resolve_imports`; 路径转换 |

### 文件统计

| 文件 | 行数 (约) |
|------|----------|
| `lexer.c` | 320 |
| `ast.c` | 450 |
| `types.c` | 220 |
| `symtab.c` | 140 |
| `parser.c` | 750 |
| `sema.c` | 560 |
| `ir.c` | 180 |
| `codegen.c` | 600 |
| `main.c` | 280 |
| `runtime/runtime.c` | 40 |
| **合计** | **~3540** |
