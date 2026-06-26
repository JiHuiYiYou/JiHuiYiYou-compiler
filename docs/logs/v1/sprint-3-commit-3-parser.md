# Sprint 3 commit 3 — parser.jhyy parse_stmt + parse_pattern 翻译

**日期**: 2026-06-26
**对应 plan**: [`../../plans/v1/v1.0.0详细实现方案.md`](../../plans/v1/v1.0.0详细实现方案.md) § 3.3
**状态**: 完成 ✅

## 目标

commit 2 翻译了 parse_decl + parse_func + parse_type_decl + parse_type + parse_extern_decl + parse_import_decl + parse_block + parse_stmt stub + parse_expr stub。
commit 3 完成 parse_stmt 完整版（9 个子分支配器）+ parse_pattern 完整版。

C 端 parser.c 中相关行号：
- parse_let L238, parse_if L261, parse_while L280, parse_for L290, parse_match L311
- parse_return L341, parse_break L354, parse_continue L361, parse_expr_stmt L368
- parse_stmt L376-387（dispatcher）
- parse_pattern L113-204

## 实现

### 1. 翻译要点

**核心设计约束**：jhyy 不支持 mutual recursion（forward reference = hard error，已实测 2026-06-26）。
C 端 `parse_stmt → parse_block → parse_stmt` 是 mutual recursion cycle，直接翻译 jhyy 会编译失败。

**解决方案**：**inline block parser**。
- 删掉共享的 `parse_block` 函数
- parse_if / parse_while / parse_for / parse_func 的 body 各自 inline 一份 block parser（含 push/pop scope + dispatcher loop + expect RBRACE）
- inlined dispatcher 调 "sub-stmt 函数集 + self-recursion + 必要 cross control flow"
- nested LBRACE（`{ { ... } }`）暂不支持（commit 3 limitation，测试无此用例）

**Order 约束**（jhyy 函数定义顺序决定能否编译）：
```
parse_type      → parse_let 用
parse_let, parse_return, parse_break, parse_continue, parse_expr_stmt  (共享 5)
parse_pattern   (self-recursive)
parse_match     → 用 parse_pattern
parse_if        → inlined block 调 self + 共享 5
parse_for       → inlined block 调 self + parse_if
parse_while     → inlined block 调 self + parse_for + parse_if
parse_stmt      → top-level dispatcher
parse_func      → inlined block 调 parse_if/while/for + 共享 5
parse_type_decl, parse_extern_decl, parse_import_decl
parse_decl
parser_init, parser_parse
```

**已知限制**（v0.7 测试集覆盖，phase-2 编译 jhyy 不需要）：
- while-inside-if（测试无此模式）
- while-inside-for（测试无此模式）
- nested LBRACE（`{ { stmt; } }`）
- parse_expr 仍为 stub（commit 4）→ match arm body / let init / if cond 等临时 NULL

### 2. parse_stmt 9 子分支配器

| 函数 | 对应 C 行 | jhyy 翻译 |
|------|----------|----------|
| parse_let | L238 | loc save + consume let + optional mut + ident + optional `: type` (parse_type) + `=` + parse_expr + `;` + symtab_insert SYM_VAR + ast_new_let |
| parse_if | L261 | loc save + consume if + parse_expr cond + inlined block + optional `else` (parse_if 或 inlined block) + ast_new_if |
| parse_while | L280 | loc save + consume while + parse_expr cond + inlined block + ast_new_while |
| parse_for | L290 | loc save + consume for + expect IDENT loop var + expect in + parse_expr start + expect `..` + parse_expr end + push_scope + symtab_insert + inlined block + pop_scope + ast_new_for |
| parse_match | L311 | loc save + consume match + parse_expr subj + expect `{` + 循环 parse_pattern + expect `=>` + parse_expr body + match_arm growable + expect `}` + ast_new_match |
| parse_return | L341 | loc save + consume return + optional parse_expr (无 `;`/`}` 时) + expect `;` + ast_new_return |
| parse_break | L354 | loc save + consume break + expect `;` + ast_new_break |
| parse_continue | L361 | loc save + consume continue + expect `;` + ast_new_continue |
| parse_expr_stmt | L368 | parse_expr + optional `;` (RBRACE/EOF 前省略) + ast_new_expr_stmt |

parse_stmt dispatcher (C L376-387)：
- 9 个 if 分支调对应函数

### 3. parse_pattern 翻译

C 端 parse_pattern L113-204 = wildcard / ident / `Name::Variant` / 短名 variant / range / int / bool / char / minus / default error。

| 模式 | jhyy 翻译 |
|------|----------|
| `_` (wildcard) | 4-byte aligned read t.start[0]（绕开 qbe_type_of(*u8)='b' bug，参照 lexer.jhyy lex_peek_char），compare ASCII 95 |
| `Name::Variant` | check COLONCOLON, save outer_name **BEFORE** consume `::`（关键：parser_advance 会覆盖 prev_*），expect IDENT variant, lookup/insert type_sym + variant_sym, optional `(inner)` |
| `lo..hi` range | check DOTDOT, parse_expr hi (stub → NULL), ast_new_pattern_range |
| 短名 variant `Some(v)` / `None` | lookup ident in global_scope as SYM_VARIANT（**前提：parse_type_decl 注册 variant**），optional `(inner)` |
| 普通 ident binding | lookup/insert SYM_VAR + ast_new_pattern_ident |
| int literal | consume, strtoll(t.start, 0, 0), ast_new_pattern_lit PRIM_I32 |
| bool literal | consume, strncmp "true", ast_new_pattern_lit PRIM_BOOL |
| char literal | consume, 4-byte aligned read + shift + mask, ast_new_pattern_lit PRIM_U8 |
| `-int` | consume `-`, expect INT, strtoll, negate, ast_new_pattern_lit PRIM_I32 |
| default | error + advance 1 token + return NULL |

### 4. parse_type_decl 注册 variants

C 端 parser.c:526-530 关键 5 行：parse_type_decl 解析 `enum { ... }` 后**循环 symtab_insert 每个 variant 名为 SYM_VARIANT in global_scope**。
jhyy commit 2 漏了这段，commit 3 补上：解析完 enum body 后，遍历 variants 数组，逐个 `symtab_insert(global_scope, name, SYM_VARIANT, ...)`。

不补会导致：短名 variant pattern（`Some(_) => ...`）找不到 variant 符号，回退到 ident binding，AST 错误。

## 关键 bug 修复

### Bug 1: forward reference (C parse_stmt ↔ parse_block cycle)

jhyy 实测 2026-06-26 不允许 mutual recursion（forward reference = hard error）。
C 端 parse_stmt L385 → parse_block → parse_stmt 循环编译失败。
**解决**：inline block parser，删共享 parse_block。
plan § 1.5 没明确写 inline 是 jhyy 唯一可行路径，commit 3 实施时才发现。

### Bug 2: tokenizer keyword len bucket 错位

lexer.jhyy lookup_keyword 把 `in`（2 字符）放进了 `len == 3` 分支，导致 `in` 被识别为 IDENT 而非 TOKEN_IN。
**修复**：搬到 `len == 2` 分支。`for i in 0..10` 才能正常 parse。

### Bug 3: parse_pattern 短名 variant 找不到 SYM_VARIANT

parse_type_decl 没注册 variant 名为 SYM_VARIANT。
**修复**：解析完 enum body 后循环 symtab_insert。

### Bug 4: parse_pattern outer ident 覆盖

`Name::Variant` 解析时，parser_match(COLONCOLON) 和 parser_expect(IDENT) 各调一次 parser_advance，覆盖 prev_* 两次。
原代码读 `(*p).prev_start / prev_length` 取 outer ident 名字，但拿到的已经是 variant 名字。
**修复**：parser_check(COLONCOLON) 之前先从 t.start/t.length 存 outer_name（此时 t 还指向刚 consume 的 outer ident）。

### Bug 5: parse_pattern wildcard deref

`((t.start as i64) as *i32) as i32` 看似读首个 byte，实际 jhyy 不会把 `as i32` 自动 deref pointer。
**修复**：4-byte aligned read + shift + mask（参照 lexer.jhyy lex_peek_char 实现）。

### Bug 6: main.c link 缺 jhyy_helpers.c

commit 2 测试通过是因为当时只用 parse_decl → parse_func（无 error path），不需要 jh_* externs。
commit 3 启用 parse_stmt 走 inlined block，遇到 syntax error → parser_expect 调 jh_print_loc_stderr + jh_fputs_stderr。
**修复**：main.c L445 link 命令加 `compiler/src0/jhyy_helpers.c`。
**这是 plan 修订遗漏**：plan § 1.3 M1 里程碑说"用 jhyy 测 arena + helpers"但没明示 main.c link 必须加 helpers.c。

### Bug 7: ffi.jhyy 缺 strtoll extern

parse_pattern int literal 需要 `strtoll(t.start, 0, 0)`。
**修复**：ffi.jhyy 加 `extern fn strtoll(s: *u8, endptr: *u8, base: i32) -> i64;`

## 已知差异（vs C 版）

- **inline block vs shared parse_block**：jhyy 4 份 inlined dispatcher，vs C 1 份共享函数。代码量 +200 行，但保留所有 v0.7 测试组合。
- **wildcard / 短名 variant 字节读取**绕过 qbe_type_of(*u8)='b' bug（plan § 0 bug #6）
- **range pattern 仅 ident-based**（`x..y`），C 端同。jhyy 不支持 `1..10` 字面量范围（T24 测试已验证）
- **parse_expr 仍 stub**：match arm body / let init / if cond / while cond / for start/end / return expr 全部 NULL。commit 4 实现完整 Pratt 后修正。

## 验证

- ✅ `jhyy.exe build _driver_parser.jhyy` 无错
- ✅ `jhyy.exe compile _driver_parser.jhyy` 链接 + 运行无错（main.c 加了 jhyy_helpers.c）
- ✅ T0-T24 + PASS，exit=42（commit 2 = 13 个，commit 3 新增 11 个）
- ✅ `python regress.py` **47/50 passed, 0 failed, 3 skipped**（未引入新失败）
- ✅ AST oracle：break_continue.jhyy dump 输出 vs golden/break_continue.ast.txt 结构一致（除 test 自带 extern printf 不在 golden 里）
- ✅ match_exhaustive.jhyy dump：pattern_enum / pattern_wild / kind=variant vs kind=type 全部正确
- ✅ if-inside-for（break_continue.jhyy）解析正确
- ✅ 短名 variant pattern（Some/None）解析正确

新增 11 个 commit 3 专项测试：
| Test | 验证 |
|------|------|
| T14 | parse_let（mut + type annotation） |
| T15 | parse_if 无 else |
| T16 | parse_if + else block |
| T17 | parse_while + inlined block + break |
| T18 | parse_for + inlined block + continue |
| T19 | parse_match 短名 variant `Some(_) / None` |
| T20 | parse_match 完整限定 `Option::Some(_) / Option::None` |
| T21 | parse_pattern int literal（多个 arm） |
| T22 | parse_return |
| T23 | nested if-inside-for（cross control flow） |
| T24 | parse_pattern range `x..y` + bool literal |

## 下一步（commit 4）

parse_expr 完整 Pratt 表达式解析（+ ParseRule 表 + init_rules）。Sprint 3 收官。
预计：parse_expr 还要 ~400 行（C 端 ~150 行 + jhyy 习惯膨胀）；新增 ~5 个测试。
