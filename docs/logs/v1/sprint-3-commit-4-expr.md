# Sprint 3 commit 4 — parser.jhyy parse_expr 完整 Pratt 翻译

**日期**: 2026-06-26
**对应 plan**: [`../../plans/v1/v1.0.0详细实现方案.md`](../../plans/v1/v1.0.0详细实现方案.md) § 3.3
**状态**: 完成 ✅

## 目标

Sprint 3 收官：替换 commit 3 的 parse_expr stub 为完整 Pratt 表达式解析。
完成后 parse_stmt arm bodies / let init / if cond / while cond / for start·end / return expr 全部有真实 expression node，不再 NULL。

C 端参考 `compiler/src/parser.c` L400-580（parse_expr + 12 prefix_* + 6 infix_* + ParseRule 表 + init_rules）。

## 实现

### 1. 设计约束（与 commit 3 一样）

jhyy 不支持 mutual recursion（forward reference = hard error）。
C 端 parse_expr ↔ prefix_* ↔ infix_* + parse_type ↔ parse_expr 形成 cycle。
**解决方案**：**monolithic parse_expr** —— 把 12 个 prefix_* + 6 个 infix_* 全部 inline 在 parse_expr 内部，按 token kind dispatch。

### 2. ParseRule 表（jhyy 版）

C 端用 struct array 存 12 行 infix rule。jhyy 没有 struct array literal，全部 inline 进 parse_expr 的 while 循环。
规则等价：
```
EQ/PLUSEQ/MINUSEQ/STAREQ/SLASHEQ/PERCENTEQ → PREC_ASSIGN
PIPEPIPE        → PREC_OR
AMPAMP          → PREC_AND
EQEQ/BANGEQ/LT/GT/LTEQ/GTEQ → PREC_COMPARE
PIPE            → PREC_BIT_OR
CARET           → PREC_BIT_XOR
AMP             → PREC_BIT_AND
LTLT/GTGT       → PREC_SHIFT
PLUS/MINUS      → PREC_TERM
STAR/SLASH/PERCENT → PREC_FACTOR
LPAREN/DOT/LBRACKET → PREC_PRIMARY（call action）
AS              → PREC_FACTOR（cast action）
```

stop token（终止 while loop）：EOF/SEMICOLON/RBRACE/RPAREN/RBRACKET/COMMA/COLON/FATARROW/IN/ELSE

### 3. prefix dispatch（12 类）

| token | 处理 |
|-------|------|
| TOKEN_INT | strtoll + jh_int_suffix_prim → ast_new_int(prim) |
| TOKEN_FLOAT | jh_f64_atof 走 store-mode → ast_new_float |
| TOKEN_STRING | 4-byte aligned read 字节进 arena → ast_new_string |
| TOKEN_CHAR | 4-byte aligned read + escape 解码 → ast_new_char |
| TOKEN_BOOL | 1=true / 0=false → ast_new_bool |
| TOKEN_IDENT | lookup symtab + 后续 optional `(` / `{` / `::` 区分 ident/struct lit/enum variant/qualified call |
| TOKEN_MINUS/BANG/TILDE | ast_new_unary |
| TOKEN_STAR | ast_new_deref |
| TOKEN_AMP | ast_new_addr_of；optional `[...]` → ast_new_slice_lit |
| TOKEN_LPAREN | 解析 internal expr → `)`（paren grouping）；empty `()` → unit ident "()" |
| TOKEN_SIZEOF/ALIGNOF | consume type ident → ast_new_sizeof / ast_new_alignof |
| TOKEN_LBRACKET | 解析 elements → `]` → ast_new_array_lit |

### 4. infix action（5 类）

| token | 处理 |
|-------|------|
| TOKEN_EQ | ast_new_assign(target=left, value=parse_expr(ASSIGN+1)) |
| TOKEN_PLUSEQ/MINUSEQ/... | ast_new_assign(target=left, value=ast_new_binary(op_token_minus_eq, left, right)) |
| TOKEN_LPAREN | 解析 args → `)` → ast_new_call(callee=left) |
| TOKEN_DOT | consume IDENT → ast_new_field(expr=left, field=name) |
| TOKEN_LBRACKET | 解析 index expr → `]`（或 `..` end expr → ast_new_slice_range） |
| TOKEN_AS | parse_type → ast_new_cast(expr=left, target=type) |
| 其他二元 op | ast_new_binary(op, left, parse_expr(prec+1)) |

### 5. 关键 bug 修复

#### Bug 1: forward reference parse_expr ↔ parse_type

`as` cast 的 RHS 调 parse_type，parse_type 的 array count 又调 parse_expr（曾经）→ cycle。
**修复**：
- **parse_type 上移**到 parse_expr 之前定义（jhyy 函数顺序决定能否编译）
- parse_type 的 array count 改为 inline int parse（consume `;` 之前必须是 TOKEN_INT，strtoll → ast_new_int，不调 parse_expr）

#### Bug 2: jhyy if-else 类型统一（type uniformity）

parse_expr 前缀 dispatch 错误分支调 `return 0 as *Node;` 但其他分支 `left = ...`（类型 `()`），if-else 要求两分支类型相同 → 编译错。
**修复**：错误分支也 `left = 0 as *Node;`，跳出 dispatch 后统一 `if left == (0 as *Node) { return 0 as *Node; }`。
infix dispatch 同模式：`is_infix = 0;` 替代 `return left;`，让 else 分支类型一致。

#### Bug 3: 函数体类型 () 不匹配 return *Node

jhyy type checker 不识别 while true 内的 `return left;` 覆盖所有路径 → 报"function body type () does not match return type *Node"。
**修复**：while 循环后加 `return 0 as *Node; // sentinel`（unreachable but satisfies type checker）。

#### Bug 4: jhyy operator precedence on `as`

`t.start as i64 + 1` 解析为 `t.start as (i64 + 1)`。
**修复**：`(t.start as i64) + (1 as i64)` 显式括号。

#### Bug 5: implicit declaration of `atof`（link 错）

jhyy_helpers.c 加 `jh_f64_atof` 用了 `atof` 但未 include stdlib.h。
**修复**：jhyy_helpers.c 顶部 `#include <stdlib.h>`。

#### Bug 6: T19/T20 字面量 `\n` 不是 newline

测试驱动 `let src = "...\n\nfn ..."` 里 `\n` 是 jhyy 字符串字面量中 lex 识别的 escape 转义，但 lex_scan_string 只是跳过 escape，**不写 newline byte 到内存**——resulting char 仍是 `\n`（backslash + n）。
测试驱动然后 lexer_init on this byte sequence，lexer 遇 `\` → "unexpected character" → error_count++。
**修复**：把 T19 / T20 的 src 改成单行（去掉 `\n\n` 间隔）。

#### Bug 7: T22 nstmts expected 实际 got 2

T22 用 commit 3 假设 nstmts=1（parse_expr 是 stub 时 trailing `0` 不能 form expr_stmt）。
**修复**：T22 改成 nstmts=2，验证 `return 42;` 后跟 `0` expr_stmt 真实存在。

#### Bug 8: NodeBool 字段名

T30 用 `(*bd3).val` 但 ast.jhyy 里 NodeBool 字段名是 `value`（跟 NodeInt 保持一致）。
**修复**：T30 改 `(*bd3).value`。

### 6. jhyy_helpers.c 新增 2 个 extern 桥

```c
int jh_f64_atof(const char *s, long long len, void *dst);  // store-mode atof
int jh_int_suffix_prim(const char *s, long long len);       // parse `42i32` 后缀
```

ffi.jhyy 同步加 extern 声明。

### 7. 主代码量

| 文件 | 行数 | 增量 |
|------|------|------|
| compiler/src0/parser.jhyy | 1748 | +500（parse_expr inline） |
| compiler/src0/_driver_parser.jhyy | 1288 | +240（T25-T34 新增 10 个测试 + T14/T22 修正） |
| compiler/src0/ffi.jhyy | 62 | +2 |
| compiler/src0/jhyy_helpers.c | 89 | +30 |

## 验证

- ✅ `jhyy.exe compile _driver_parser.jhyy` 无错
- ✅ `jhyy.exe compile _driver_parser.jhyy` 链接 + 运行无错
- ✅ **T0-T34 全部 PASS，exit=42**（commit 3 = 24 个，commit 4 新增 10 个）
- ✅ `python regress.py` **47/50 passed, 0 failed, 3 skipped**（未引入新失败）
- ✅ AST oracle 46/47 byte-equal（dungeon_game 1 个 diff 是不相关 let mut 已知差异）

新增 10 个 commit 4 专项测试：
| Test | 验证 |
|------|------|
| T25 | int + 二元加法（1+2 → NODE_BINARY TOKEN_PLUS） |
| T26 | 一元负号（-42 → NODE_UNARY TOKEN_MINUS） |
| T27 | 函数调用（foo(1,2) → NODE_CALL 2 args） |
| T28 | 字段访问（a.b → NODE_FIELD "b"） |
| T29 | 数组下标（a[0] → NODE_INDEX） |
| T30 | 4 种字面量（int/float/string/bool） |
| T31 | 优先级（1+2*3 → 顶层 PLUS，右孩子 STAR） |
| T32 | 赋值（x=42 → NODE_ASSIGN + NODE_EXPR_STMT） |
| T33 | 数组字面量（[1,2,3] → NODE_ARRAY_LIT nelems=3） |
| T34 | 字符串字面量（含引号剥离，"hello world" len=11） |

更新 2 个 commit 3 测试：
| Test | 变更 |
|------|------|
| T14 | nstmts 1→2（let + expr_stmt trailing 0）；新增 init=NODE_INT / s1=NODE_EXPR_STMT 验证 |
| T22 | nstmts 1→2（return + expr_stmt trailing 0） |

## Sprint 3 总结

| Commit | 内容 | 测试 |
|--------|------|------|
| 1 | parser.jhyy 骨架 + token kind 常量 + lexer 协作 | smoke |
| 2 | parse_decl / parse_func / parse_type / parse_extern / parse_import + stub parse_stmt/parse_expr | 13 tests |
| 3 | parse_stmt 9 子分支配器 + parse_pattern + inline block | +11 tests (24 total) |
| 4 | parse_expr 完整 Pratt（monolithic） | +10 tests (34 total) |

**Sprint 3 整体**: parser.jhyy 完成全部 3.3 节翻译，从零到 34 个测试全 PASS。
下个 sprint（sprint 4）应该是 codegen.jhyy 起步：把 AST → QBE IL，从 arena.jhyy / util.jhyy 等基础设施翻译开始。