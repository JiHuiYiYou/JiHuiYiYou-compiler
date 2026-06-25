# Sprint 3 commit 2 — parser.jhyy parse_decl 翻译

**日期**: 2026-06-25
**对应 plan**: [`../../plans/v1/v1.0.0详细实现方案.md`](../../plans/v1/v1.0.0详细实现方案.md) § 3.3
**状态**: 完成 ✅

## 目标

把 C 端 `compiler/src/parser.c` 982 行中的 parse_decl 翻译成 `compiler/src0/parser.jhyy` (~620 行)。
plan 拆分：commit 2 = parse_decl + parse_func + parse_type_decl + parse_type + parse_extern_decl + parse_import_decl + parse_block + parse_stmt stub + parse_expr stub。
commit 3 = parse_stmt 完整，commit 4 = parse_expr 完整 Pratt。

## 实现

### 1. parser.jhyy 翻译（~620 行）

**核心结构**：
- `type Parser` 平铺 6 字段 prev（避免 nested struct 触发 QBE 'w' load 不对齐，plan § 1.5 bug #5）
- Parser 字节数 80（2 ptr + 6 token 字段 + 2 scope + 2 i32 = 16+48+16+8 = 88 → 实际 80 因为 4-byte pad）

**API**：
- `parser_init(p, lex, a)` — 初始化 + symtab_new(a, 0)
- `parser_parse(p)` — 循环 parse_decl 到 EOF，ast_new_module 返回 *Node

**parse_decl 顶层 dispatch**：
- `TOKEN_FN` → `parse_func(p, 0)`
- `TOKEN_TYPE` → `parse_type_decl(p)`
- `TOKEN_EXTERN` → `parse_extern_decl(p)` → `parse_func(p, 1)`
- `TOKEN_IMPORT` → `parse_import_decl(p)`
- 其他 → `parse_stmt(p)` stub

**parse_func**：
- 注册到 `(*p).global_scope` (SYM_FN, depth=0)
- is_extern=1 时设 `(*sym).is_extern = 1`
- params 数组 growable（cap 4 → ×2）
- 可选 `-> RetType`
- is_extern → `;` ；否则 `parse_block`
- 返回 `ast_new_func_decl(... is_extern)`

**parse_type_decl**：
- 注册到 `(*p).global_scope` (SYM_TYPE)
- 3 种 body：struct / enum / alias（默认 else 分支）
- struct fields / enum variants 各自 growable

**parse_type**：
- `*T` → `ast_new_unary(STAR, inner)`
- `[*]T` → `ast_new_slice_type(elem)`
- `[T; N]` → `ast_new_array_type(base, count_expr_stub)`
- `fn(T1, T2) -> R` → `ast_new_int(0, PRIM_I32)` placeholder
- `Ident [:: Ident]*` → `ast_new_ident(sym)` 反复覆盖 base 到最右 ident
- 关键：`let mut sym / let mut qsym`（plan § 0 bug #2，let mut bug）

**parse_block**：循环 parse_stmt 到 `}`，push/pop scope，stmts growable

**parse_stmt / parse_expr / parse_pattern stub**：commit 3/4 实现，stub 至少 advance 一 token 防 parse_block / parse_let / parse_match 死循环

### 2. 翻译要点

1. **C Token by value → jhyy 平铺 6 字段 + caller 栈分配 + lexer 写 *t**（同 lexer.jhyy）
2. **C `bool` → jhyy i32 (0/1)**
3. **C nested Token in Parser.prev → jhyy Parser 平铺 6 字段**
4. **C `fprintf(stderr, ...)` 变参 → jhyy jh_print_loc_stderr + jh_fputs_stderr**
5. **C `size_t` → jhyy i64**
6. **C `bool match / check` → jhyy i32 (0/1)**
7. **jhyy 无 struct return value → caller 栈分配 + callee 写 *t**
8. **jhyy 无前向引用 → order matters**（parser_advance 必须在 parser_peek 之前）
9. **jhyy if/else 各分支返回类型必须一致 → 用 `body = 0 as *Node;` 统一 is_extern 路径**

### 3. _driver_parser.jhyy 单元测试（13 个 test + 退出码 42）

| Test | 验证 |
|------|------|
| T0 | main_jhyy 启动 |
| T1 | extern fn decl（C 端是 NODE_FUNC_DECL + is_extern=1，不是 NODE_EXTERN_DECL） |
| T2 | import decl（NODE_IMPORT_DECL + SYM_MODULE） |
| T3 | type alias（body = NODE_IDENT） |
| T4 | type struct（NODE_STRUCT_DEF，nfields=2，name="x"） |
| T5 | type enum（NODE_ENUM_DEF，nvariants=3，Blue(i32) 有 payload） |
| T6 | fn 空 body（NODE_BLOCK，nstmts=0） |
| T7 | fn params + ret type |
| T8 | module 多 decl（3 个：import / extern fn / type） |
| T9 | pointer type `*T`（NODE_UNARY，op=TOKEN_STAR） |
| T10 | slice type `[*]T`（NODE_SLICE_TYPE） |
| T11 | array type `[T; N]`（NODE_ARRAY_TYPE，count expr stubbed 走 0） |
| T12 | qualified type `std::io::Buffer`（body = NODE_IDENT "Buffer"） |
| T13 | error detection（缺 `)` → error_count 增加） |

## 关键 bug 修复

### Bug A: arena_strdup 多复制 1 byte 污染 NUL 终止

**症状**：T1 测试 `strcmp((*sym).name, "printf")` 失败，sym name 不是 "printf" 而是 "printf(" 之类的

**根因**（v0.6 sprint 1 arena.jhyy 翻译 bug）：`arena_strdup` 用 `memcpy(p, s, len + 1)` 而不是 `memcpy(p, s, len); p[len] = '\0'`。多复制 1 byte 把 `s[len]`（紧跟 token 后的 byte，通常非 0 如 `(`, ` `, `\n`）当 NUL 终止符

**修复**（compiler/src0/arena.jhyy:122-135）：
```c
fn arena_strdup(a: *Arena, s: *u8, len: i64) -> *u8 {
    let p = arena_alloc(a, len + 1 as i64);
    if p == (0 as *u8) { return 0 as *u8; }
    memcpy(p, s, len);                          // 只复制 len byte
    memset(ptr_add(p, len), 0 as i32, 1 as i64); // 显式 NUL
    return p;
}
```

**影响**：所有 token name / sym name / ident / type name 全部能正确 strdup

### Bug B: let mut 缺失导致 qualified ident sym 变 null

**症状**：T12 测试 `std::io::Buffer` qualified type，body 节点 `(*id).sym` 是 0（NULL），导致 deref segfault

**根因**：parse_type 写 `let qsym = symtab_lookup(...)` 后 `qsym = symtab_insert(...)`。`qsym` 不可变，codegen 把这次"重新赋值"当 dead code 优化掉。后续 `ast_new_ident(..., qsym)` 用的还是 lookup 的 0 结果

**修复**（compiler/src0/parser.jhyy:243, 255）：`let mut sym` / `let mut qsym`（参考 memory `feedback_let_mut_assignment_bug.md`）

**这是 v0.6 codegen 已知 bug**：let x = ... 后的 if-block 里 x = Y 会被优化掉；必须 `let mut x`

## 已知差异 / 绕开

1. **parse_stmt / parse_expr / parse_pattern stub**：commit 3/4 完整实现
2. **parse_type 的 `[T; N]` count expr**：stub 走 `parse_expr(p, 0)` 返回 0；commit 4 接入完整 Pratt 后修复
3. **parse_type 的 `fn(...) -> R` 函数字面量类型**：返回 `ast_new_int(0, PRIM_I32)` placeholder；C 端亦同
4. **C 端 `parse_type_def` 一并处理 `type Name = struct {...}`** → jhyy 拆分到 parse_type_decl
5. **parse_type_decl 不消费末尾 `;`**（C 端 parser 用 `parse_stmt` 兜底吃掉）—— 但 jhyy parse_block / parser_parse 的 EOF 检查会 loop 兜底，行为一致

## 验证

- ✅ `jhyy.exe build _driver_parser.jhyy` 无错
- ✅ QBE `-t amd64_win` 无错
- ✅ gcc link + run：T0-T13 + PASS，exit=42
- ✅ `python regress.py` 44/47 passed, 0 failed（parser.jhyy 是新模块，未影响 C 端编译）

## 下一步

按 plan 接下来是 **sprint 3 commit 3: parser.jhyy parse_stmt 完整**（parse_let / parse_if / parse_while / parse_for / parse_match / parse_return / parse_break / parse_continue / parse_pattern）。预计 ~300-500 行 jhyy。
