# Sprint 3 commit 1 — lexer.jhyy 翻译

**日期**: 2026-06-25
**对应 plan**: [`../../plans/v1/v1.0.0详细实现方案.md`](../../plans/v1/v1.0.0详细实现方案.md) § 3.3
**状态**: 完成 ✅

## 目标

把 C 端 `compiler/src/lexer.c` (~468 行) 翻译成 `compiler/src0/lexer.jhyy` (~750 行)。这是 sprint 3 commit 1，计划 commit 顺序为 lexer → parser (3 commit) → sema。

## 实现

### 1. ffi.jhyy 新增 4 个 libc 函数声明

- `isdigit(c: i32) -> i32`
- `isalpha(c: i32) -> i32`
- `isalnum(c: i32) -> i32`
- `strncmp(a: *u8, b: *u8, n: i64) -> i32`

ctype.h 函数（`int __cdecl isdigit(int)`）走 UCRT 直接 FFI。strncmp 是 keyword 查找用。

### 2. lexer.jhyy 翻译

**TokenKind 常量**：75 个 i32 函数（C `enum` → jhyy 无 enum 原生），编号跟 C 端 lexer.h 完全一致。

**结构**：
- `type Token = struct { kind, start, length, loc_filename, loc_line, loc_col }`
- `type Lexer = struct { source, current, filename, line, col, peek_kind, peek_start, peek_len, peek_lf, peek_ll, peek_lc, has_peek, error_count }`

**API**：
- `lexer_init(l, source, filename)` 
- `lexer_next(l, *t)` — caller 栈分配 Token，lexer 填 *t
- `lexer_peek(l, *t)` — 1-token lookahead，caller 栈分配
- `token_kind_name(kind)` — debug 用

**私有 helper**：lex_peek_char / lex_next_char / lex_match_char / lex_peek_char_at / lex_make_token / lex_error_token / lex_skip_line_comment / lex_skip_block_comment / lex_skip_whitespace / is_hex_digit / is_oct_digit / is_bin_digit / lex_scan_number / lex_scan_string / lex_scan_char / lex_scan_ident_or_keyword / lookup_keyword

### 3. _driver_lexer.jhyy 单元测试

**测试覆盖**（34 个 token 验证 + 5 个 token_kind_name 验证）：
- L1: 基础 `let x = 42;` — 5 tokens + EOF
- L2: 关键字 + 带下划线 ident — `fn`, `if_while`, `return`
- L3: 12 个运算符 — `==`, `!=`, `<=`, `>=`, `&&`, `||`, `::`, `..`, `=>`, `->`, `<<`, `>>`
- L4: peek 不消耗 — 4 tokens
- L5: 字面量 + 类型后缀 — `true`, `false`, `3.14`, `0xFFi32`, `100u64`
- L6: 注释跳过 — `// line` + `/* block */` 混合
- L7: token_kind_name — 5 个 kind

退出码 42。

## 已知差异 / 绕开

1. **C `Token lexer_next(Lexer *)` 返回值 → jhyy 写 *Token**（caller 栈分配）。jhyy 无 struct 返回值（lang-spec v1.0.0 line 808: "struct 跨 FFI 见附录 B"）。所有 token 字段 6 个平铺，避免 nested struct。
2. **C `typedef struct { TokenKind kind; ... } Token` 内嵌 SourceLoc → jhyy 平铺 loc_filename/loc_line/loc_col 3 字段**（plan § 1.5 bug #5：nested struct 触发 QBE 'w' load 不对齐）。
3. **C `*u8 deref` → jhyy 用 4-byte aligned `*i32` + shift+mask**（plan § 0 bug #6）。lex_peek_char / lex_peek_char_at / lex_scan_number 的 `*(start)` 都走这模式。**注意**：每个 byte 读取走 4-byte aligned read + shift+mask；3 byte wasted bandwidth per char，但 lexer 是单线程顺序读，性能不敏感。
4. **C `static const Keyword keywords[24]` 数组 → jhyy 用链式 if/else + 按 len 分桶的 lookup_keyword**（jhyy 不能存 array of struct at compile time）。24 个 keyword → ~30 行 if/else，性能 O(1) by length bucket。
5. **C 函数指针 digit_fn → jhyy 用 digit_kind: i32 0/1/2/3 + if/else**（jhyy 无 fn pointer）。
6. **jhyy 无函数前向引用** → lexer_next 必须在 lexer_peek 之前定义（lexer_peek 调用 lexer_next）。
7. **jhyy if/else 各分支返回类型必须一致** → 函数调用作 statement 用 `let _x = func();` 模式丢弃返回值。

## 验证

- ✅ `compiler/build/bin/jhyy.exe build _driver_lexer.jhyy` 无错
- ✅ QBE `-t amd64_win` 无错（绕开 bug #6 后）
- ✅ gcc link + run：`PASS n_ok=34`, exit=42
- ✅ `python regress.py` 44/47 passed, 0 failed（lexer.jhyy 是新模块，未影响 C 端编译）

## 下一步

按 plan 接下来是 **sprint 3 commit 2: parser.jhyy 翻译 — parse_decl**（顶层 fn / type / extern / import 声明）。parser.c 982 行是 sprint 3 最大单模块，必拆 3 commit：
- commit 2: parse_decl
- commit 3: parse_stmt (let / if / while / for / match / return / block)
- commit 4: parse_expr (Pratt 解析：前缀/中缀/后缀)

预计每个 commit ~300-500 行 jhyy。