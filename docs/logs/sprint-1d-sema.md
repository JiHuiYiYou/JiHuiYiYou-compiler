# Sprint 1d — Semantic Analysis (语义分析)

**日期**: 2026-06  
**状态**: 完成

## 成果

实现了类型检查与推断，为 AST 节点标注类型。

### 文件

- `compiler/src/sema.h` — 接口定义
- `compiler/src/sema.c` (~500 行) — 实现

### 三遍遍历

```
Pass 1: 注册所有顶层声明 (函数名 → SYM_FN, 类型名 → SYM_TYPE)
Pass 2: 解析所有类型声明 (struct/enum → Type 对象)
Pass 3: 检查函数体和顶层语句
```

### 类型推断规则

| 表达式 | 推断类型 |
|--------|---------|
| `42` | `i32` (默认) |
| `42i64` | `i64` |
| `3.14` | `f64` |
| `true` / `false` | `bool` |
| `"hello"` | `[*]u8` |
| `&expr` | `*typeof(expr)` |
| `*ptr` | 解引用 ptr 指向的类型 |
| `a + b` | a 和 b 的共同类型 (需一致) |
| `a == b` | `bool` |
| `if cond { a } else { b }` | unify(typeof(a), typeof(b)) |
| `{ stmts... }` | 最后一条表达式的类型 |
| `match expr { arms }` | 所有 arm 的共同类型 |

### 错误检测

- 未定义变量引用
- 类型不匹配 (二元运算、赋值、函数体 vs 返回类型)
- 对非指针类型解引用
- 对非结构体类型做字段访问
- struct 字面量字段名/类型不匹配
- enum 变体的 payload 类型不匹配
- if 条件必须是 bool
- match arm 类型不统一

### 关键设计

1. **SemaLocal**: 使用 `Sym*` 指针匹配（主）+ name 字符串匹配（fallback），解决 P0 hash 表 bug 导致的重复 Sym 对象问题
2. **`resolve_type_node`**: 解析类型标注 → Type*，支持原始类型、指针、用户自定义 struct/enum/alias
3. **结构体字段布局**: 自动计算 offset、size、align
4. **枚举布局**: tag (i32) + payload，自动计算总大小和对齐
5. **参数**: 在函数作用域中注册，类型来自标注
6. **返回类型推断**: 若标注为 `()`, 体有返回值则自动推断

### 测试

- `compiler/tests/unit/test_sema.c`: 21 项通过
