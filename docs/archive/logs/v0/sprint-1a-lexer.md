# Sprint 1a — Lexer (词法分析器)

**日期**: 2026-06  
**状态**: 完成

## 成果

实现了完整的词法分析器，将 `.jhyy` 源码转换为 Token 流。

### 文件

- `compiler/src/lexer.h` (~80 行) — 接口定义
- `compiler/src/lexer.c` (~320 行) — 实现

### Token 类型 (50+)

- **字面量**: `TOKEN_INT`, `TOKEN_FLOAT`, `TOKEN_STRING`, `TOKEN_CHAR`, `TOKEN_BOOL`
- **关键字** (18 个): `fn`, `let`, `mut`, `if`, `else`, `while`, `for`, `in`, `match`, `return`, `type`, `struct`, `enum`, `import`, `extern`, `as`, `sizeof`, `alignof`
- **特殊值**: `true`/`false` → `TOKEN_BOOL`
- **运算符**: 算术 (`+`, `-`, `*`, `/`, `%`), 比较 (`==`, `!=`, `<`, `>`, `<=`, `>=`), 逻辑 (`&&`, `||`, `!`), 位运算 (`&`, `|`, `^`, `<<`, `>>`, `~`), 复合赋值 (`+=`, `-=`, `*=`, `/=`, `%=`)
- **分隔符**: 括号 `()`, `{}`, `[]`, `;`, `,`, `.`, `..`, `:`, `->`, `=>`

### 核心功能

1. `skip_whitespace_and_comments()`: 跳过空格/制表符、`//` 行注释、`/* */` 嵌套块注释
2. `scan_number()`: 十进制/十六进制(`0x`)/八进制(`0o`)/二进制(`0b`)，整数后缀 (`i8`-`i64`, `u8`-`u64`)
3. `scan_string()` / `scan_char()`: 处理转义序列 `\n`, `\t`, `\r`, `\\`, `\"`, `\0`, `\xNN`
4. `scan_ident()`: 标识符 → 查关键字表决定 token 类型
5. 双字符 token: `match(c)` 辅助函数做 lookahead

### 测试

- `compiler/tests/unit/test_lexer.c`: 17 个测试函数，153 项通过

### 注意事项

- `true`/`false` 初始遗漏，后续补充进关键字表
- `isdigit` 等函数签名修正为 `int (*)(int)`
