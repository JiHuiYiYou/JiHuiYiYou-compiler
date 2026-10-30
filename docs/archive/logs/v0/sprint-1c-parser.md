# Sprint 1c — Parser (语法分析器)

**日期**: 2026-06  
**状态**: 完成

## 成果

实现了递归下降 + Pratt 表达式解析器，将 Token 流转换为 AST。

### 文件

- `compiler/src/parser.h` — 接口定义
- `compiler/src/parser.c` (~700 行) — 实现

### 解析架构

```
parser_parse() → Module
  parse_decl() → 顶层声明
    parse_func()       → fn ...
    parse_type_decl()  → type Name = struct/enum { ... }
    parse_extern()     → extern fn ...
    parse_import()     → import ...

  parse_stmt() → 语句
    parse_let()        → let [mut] name [:Type] = expr;
    parse_if()         → if cond { ... } [else { ... }]
    parse_while()      → while cond { ... }
    parse_for()        → for var in start..end { ... }
    parse_match()      → match expr { arms }
    parse_return()     → return [expr];
    parse_block()      → { stmts... }

  parse_expr(precedence) → 表达式 (Pratt)
    prefix: 字面量、标识符、一元运算符、括号
    infix:  二元运算符、赋值、调用、字段访问、索引
```

### Pratt 运算符优先级

```
NONE < ASSIGN(=, +=) < OR(||) < AND(&&) < COMPARE(==, !=, <, >, <=, >=)
< BIT_OR(|) < BIT_XOR(^) < BIT_AND(&) < SHIFT(<<, >>) < TERM(+, -)
< FACTOR(*, /, %) < UNARY(-, !, ~) < PRIMARY
```

### 关键修复

1. **函数名注册时机**: 必须在解析体**之前**把函数名插入 global scope，以支持递归调用
2. **`parse_expr_stmt`**: 允许在 `}` 和 EOF 前省略分号（块中最后一条表达式语句）
3. **`parse_type_decl`**: 改为使用 `TOKEN_STRUCT`/`TOKEN_ENUM` 关键字 token（而非 `TOKEN_IDENT`）
4. **struct 字面量 / enum 变体构造**: 在 `prefix_ident` 中，仅当符号为 `SYM_TYPE` 时才尝试解析 `TypeName { ... }` 或 `TypeName::Variant(...)`
5. **通配符 `_`**: 修正为按 `TOKEN_IDENT` 处理（lexer 中 `_` 不是 `TOKEN_STAR`）
6. **数组扩容 bug**: `parse_block` 中 `stmts` 数组扩容时使用 `memcpy` 保留旧条目（修复 >8 条语句时的崩溃）

### 测试

- `compiler/tests/unit/test_parser.c`: 58 项通过

### 已知限制

- `parse_type` 对 `[*]T` 切片和 `fn` 类型仅返回占位符
- struct 字面量构造函数在不完整作用域中有查找问题
