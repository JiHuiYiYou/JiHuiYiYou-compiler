# Phase 1: C 编译器实现

> 目标：用 C 语言实现 jhyy 的完整编译器，将 `.jhyy` 源码编译为可执行文件
> 预计：约 6-8 周
> 前置：Phase 0 完成
> 产出：`jhyy` 编译器可执行文件，能编译所有测试用例

---

## 模块依赖图

```
                    +----------+
                    |  main.c  |  CLI 参数解析, 驱动流水线
                    +----+-----+
                         |
          +--------------+---------------+
          |              |               |
          v              v               v
    +---------+    +---------+     +-----------+
    | lexer.c |--->| parser.c|---->|  sema.c   |  类型检查+推断
    +---------+    +----+----+     +-----------+
          |              |               |
          v              v               v
    +---------+    +---------+     +-----------+
    |  ast.c  |    | types.c |     |  symtab.c |  符号表
    +---------+    +---------+     +-----------+
          |              |               |
          v              v               v
    +---------+    +---------+     +-----------+
    |  ir.c   |--->|codegen.c|     |   util.c  |  StringBuilder, 哈希表
    +---------+    +---------+     +-----------+
          |
          v
    +----------+     +--------------+
    | arena.c  |     |diagnostics.c |  错误报告
    +----------+     +--------------+
```

---

## Sprint 1a: Lexer (词法分析器)

### 文件
- `compiler/src/lexer.h` — 接口
- `compiler/src/lexer.c` — 实现
- `compiler/tests/unit/test_lexer.c` — 测试

### Token 类型枚举

```c
typedef enum {
    // 字面量
    TOKEN_INT, TOKEN_FLOAT, TOKEN_STRING, TOKEN_CHAR, TOKEN_BOOL,

    // 标识符 (关键字在解析时通过字符串比较区分)
    TOKEN_IDENT,

    // 运算符和分隔符
    TOKEN_PLUS,       // +
    TOKEN_MINUS,      // -
    TOKEN_STAR,       // *
    TOKEN_SLASH,      // /
    TOKEN_PERCENT,    // %
    TOKEN_EQ,         // =
    TOKEN_EQEQ,       // ==
    TOKEN_BANGEQ,     // !=
    TOKEN_LT,         // <
    TOKEN_GT,         // >
    TOKEN_LTEQ,       // <=
    TOKEN_GTEQ,       // >=
    TOKEN_BANG,       // !
    TOKEN_AMP,        // &
    TOKEN_AMPAMP,     // &&
    TOKEN_PIPE,       // |
    TOKEN_PIPEPIPE,   // ||
    TOKEN_TILDE,      // ~
    TOKEN_CARET,      // ^
    TOKEN_LTLT,       // <<
    TOKEN_GTGT,       // >>
    TOKEN_PLUSEQ,     // +=
    TOKEN_MINUSEQ,    // -=
    TOKEN_STAREQ,     // *=
    TOKEN_SLASHEQ,    // /=
    TOKEN_PERCENTEQ,  // %=

    // 括号
    TOKEN_LPAREN, TOKEN_RPAREN,
    TOKEN_LBRACE, TOKEN_RBRACE,
    TOKEN_LBRACKET, TOKEN_RBRACKET,

    // 其他
    TOKEN_DOT, TOKEN_DOTDOT, TOKEN_COMMA, TOKEN_SEMICOLON,
    TOKEN_COLON, TOKEN_ARROW, TOKEN_FATARROW,

    TOKEN_EOF, TOKEN_ERROR,
} TokenKind;

// 关键字: fn let mut if else while for in match return type struct enum import extern as sizeof alignof
```

### 接口

```c
typedef struct {
    TokenKind kind;
    const char *start;
    size_t length;
    SourceLoc loc;   // { int line; int col; const char *filename; }
} Token;

typedef struct {
    const char *source;
    const char *current;
    const char *filename;
    int line, col;
    Token peek;
    int has_peek;
} Lexer;

void lexer_init(Lexer *l, const char *source, const char *filename);
Token lexer_next(Lexer *l);
Token lexer_peek(Lexer *l);
```

### 核心实现要点

1. `skip_whitespace_and_comments()`: 跳过空格、制表符、`//` 行注释、`/* */` 块注释
2. `scan_number()`: 十进制/十六进制(0x)/八进制(0o)/二进制(0b)，整数后缀(i8-i64, u8-u64)，浮点(含小数点)
3. `scan_string()` / `scan_char()`: 处理转义序列 `\n \t \r \\ \" \0 \xNN`
4. `scan_ident()`: 标识符 → 查关键字表决定 TOKEN_IDENT 还是关键字
5. 双字符 token: 使用 `match(c)` 辅助函数做 lookahead

### 关键字表

```c
static const struct { const char *name; TokenKind kind; } keywords[] = {
    {"fn", TOKEN_FN}, {"let", TOKEN_LET}, {"mut", TOKEN_MUT},
    {"if", TOKEN_IF}, {"else", TOKEN_ELSE}, {"while", TOKEN_WHILE},
    {"for", TOKEN_FOR}, {"in", TOKEN_IN}, {"match", TOKEN_MATCH},
    {"return", TOKEN_RETURN}, {"type", TOKEN_TYPE}, {"struct", TOKEN_STRUCT},
    {"enum", TOKEN_ENUM}, {"import", TOKEN_IMPORT}, {"extern", TOKEN_EXTERN},
    {"as", TOKEN_AS}, {"sizeof", TOKEN_SIZEOF}, {"alignof", TOKEN_ALIGNOF},
};
```

### 测试要点

- 单字符 token 全部识别
- 双字符 token (== != <= >= -> => && ||) 含 lookahead
- 十进制、十六进制、八进制、二进制整数 + 类型后缀
- 浮点数
- 字符串转义序列
- 行注释和块注释被正确跳过
- 行号列号追踪 (用于错误报告)
- `lexer_peek()` 不消耗 token

### 验收标准
- [ ] 所有 30+ token 类型正确识别
- [ ] 关键字作为独立 token 类型返回
- [ ] 数值字面量解析正确 (含各种进制和类型后缀)
- [ ] 注释被透明跳过
- [ ] 源码位置 (行号, 列号) 精确追踪
- [ ] `test_lexer.c` 全部通过

---

## Sprint 1b: 数据结构 (AST + 类型系统 + 符号表 + Arena)

### 文件
- `compiler/src/ast.h` — AST 节点定义
- `compiler/src/types.h` + `types.c` — 类型表示
- `compiler/src/symtab.h` + `symtab.c` — 符号表
- `compiler/src/arena.h` + `arena.c` — 编译器内部 arena allocator

### AST 节点 (ast.h)

Tagged union 设计:

```c
typedef enum {
    NODE_INT, NODE_FLOAT, NODE_STRING, NODE_CHAR, NODE_BOOL,
    NODE_IDENT, NODE_UNARY, NODE_BINARY, NODE_CALL,
    NODE_FIELD, NODE_INDEX, NODE_CAST,
    NODE_SIZEOF, NODE_ALIGNOF, NODE_ADDR_OF, NODE_DEREF,
    NODE_BLOCK, NODE_IF, NODE_WHILE, NODE_FOR,
    NODE_LET, NODE_ASSIGN, NODE_RETURN, NODE_EXPR_STMT,
    NODE_MATCH, NODE_MATCH_ARM,
    NODE_PATTERN_LIT, NODE_PATTERN_IDENT, NODE_PATTERN_ENUM,
    NODE_PATTERN_RANGE, NODE_PATTERN_OR, NODE_PATTERN_WILD,
    NODE_STRUCT_LIT, NODE_ENUM_VARIANT,
    NODE_FUNC_DECL, NODE_TYPE_DECL, NODE_EXTERN_DECL,
    NODE_IMPORT_DECL, NODE_MODULE,
} NodeKind;

typedef struct Node {
    NodeKind kind;
    Type *type;         // sema 阶段填入
    SourceLoc loc;
    // 具体数据紧跟 Node 在 arena 中分配
} Node;
```

每种 variant 有对应结构体 (NodeBinary, NodeCall, NodeIf, NodeLet, NodeFuncDecl 等) 和构造函数。

### 类型系统 (types.h)

```c
typedef enum {
    TYPE_I8, TYPE_I16, TYPE_I32, TYPE_I64,
    TYPE_U8, TYPE_U16, TYPE_U32, TYPE_U64,
    TYPE_F32, TYPE_F64, TYPE_BOOL,
} TypePrimitive;

typedef enum {
    KIND_PRIMITIVE, KIND_POINTER, KIND_SLICE, KIND_ARRAY,
    KIND_FUNC, KIND_STRUCT, KIND_ENUM, KIND_ALIAS,
    KIND_VOID, KIND_UNRESOLVED,
} TypeKind;

typedef struct Type {
    TypeKind kind;
    union {
        TypePrimitive prim;       // KIND_PRIMITIVE
        struct { Type *elem; } pointer;            // KIND_POINTER
        struct { Type *elem; } slice;              // KIND_SLICE
        struct { Type *elem; size_t count; } array; // KIND_ARRAY
        struct { Type **params; size_t n; Type *ret; } func; // KIND_FUNC
        struct { Sym *name; Type **fields; size_t n; size_t size; size_t align; } struct_type;
        struct { Sym *name; struct Variant *vars; size_t n; size_t tag_size; size_t payload_size; } enum_type;
        struct { Sym *sym; Type *underlying; } alias;
    };
} Type;

// API
Type *type_primitive(Arena *a, TypePrimitive prim);
Type *type_pointer(Arena *a, Type *elem);
size_t type_size(Type *t);
size_t type_align(Type *t);
bool type_eq(Type *a, Type *b);
const char *type_to_string(Type *t);
```

### 符号表 (symtab.h)

```c
typedef enum { SYM_VAR, SYM_FN, SYM_TYPE, SYM_FIELD, SYM_VARIANT, SYM_MODULE } SymKind;

typedef struct Sym {
    const char *name;
    SymKind kind;
    Type *type;
    bool is_mutable;
    int depth;
    struct Sym *next;  // 链表 (同 bucket 冲突)
} Sym;

typedef struct SymTable {
    Sym **buckets;
    size_t nbuckets, count;
    struct SymTable *parent;  // 外层作用域
    Arena *arena;
} SymTable;

SymTable *symtab_new(Arena *a, SymTable *parent);
Sym *symtab_insert(SymTable *t, const char *name, SymKind kind, Type *type, bool mut, int depth);
Sym *symtab_lookup(SymTable *t, const char *name);       // 递归到 parent
Sym *symtab_lookup_local(SymTable *t, const char *name); // 仅当前层
```

### Arena (编译器用)

```c
#define ARENA_DEFAULT_SIZE (1024 * 1024)  // 1MB

typedef struct ArenaBlock { struct ArenaBlock *next; char data[]; } ArenaBlock;

typedef struct {
    char *start;    // 当前 block 起始
    char *cur;      // 当前分配指针
    char *end;      // 当前 block 结束
    ArenaBlock *blocks;
} Arena;

void arena_init(Arena *a, size_t size);
void *arena_alloc(Arena *a, size_t size);
void *arena_alloc_aligned(Arena *a, size_t size, size_t align);
char *arena_strdup(Arena *a, const char *s, size_t len);
void arena_reset(Arena *a);
void arena_free(Arena *a);
```

当单个 block 不够时，分配新的 block 加入链表。编译器可以处理任意大小的输入。

### 验收标准
- [ ] AST 节点枚举覆盖所有语法结构
- [ ] 每种 AST 节点有对应构造函数
- [ ] 类型系统能表示所有基础类型和复合类型
- [ ] `type_size()` / `type_align()` 正确计算
- [ ] `type_eq()` 正确比较类型等价性
- [ ] 符号表支持多层作用域和遮蔽
- [ ] Arena 通过 1000 次分配+reset 循环测试
- [ ] Arena 大分配 (>1MB) 正常扩展

---

## Sprint 1c: Parser (递归下降解析器)

### 文件
- `compiler/src/parser.h`
- `compiler/src/parser.c`
- `compiler/tests/unit/test_parser.c`

### 解析函数层次

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

  parse_expr(precedence) → 表达式 (Pratt 解析)
    parse_prefix()     → -expr, !expr, ~expr, *expr, &expr
    parse_infix()      → a + b, a == b, a && b ...
    parse_postfix()    → expr.field, expr[index], expr(args)
    parse_primary()    → 字面量, 标识符, (expr)
```

### Pratt Parser 核心

```c
// 运算符优先级
typedef enum {
    PREC_NONE, PREC_ASSIGN, PREC_OR, PREC_AND, PREC_COMPARE,
    PREC_BIT_OR, PREC_BIT_XOR, PREC_BIT_AND, PREC_SHIFT,
    PREC_TERM, PREC_FACTOR, PREC_UNARY, PREC_POSTFIX, PREC_PRIMARY
} Precedence;

typedef struct {
    Precedence prec;
    Node *(*prefix)(Parser *p);          // 前缀解析
    Node *(*infix)(Parser *p, Node *l);  // 中缀解析
} ParseRule;

// 主函数
static Node *parse_expr(Parser *p, Precedence min_prec) {
    Token t = lexer_peek(p->lexer);
    ParseRule *rule = &rules[t.kind];
    if (!rule->prefix) { error("expected expression"); return NULL; }

    lexer_next(p->lexer);
    Node *left = rule->prefix(p);

    while (min_prec <= rules[lexer_peek(p->lexer).kind].prec) {
        t = lexer_next(p->lexer);
        left = rules[t.kind].infix(p, left);
    }
    return left;
}
```

### 关键解析函数

**parse_let**:
```
let [mut] name [: Type] = expr ;
```
→ 创建 NODE_LET, 存储 is_mutable, sym, type_annot, init

**parse_func**:
```
fn name ( param : Type , ... ) [-> Type] { body }
```
→ 创建 NODE_FUNC_DECL, 存储 sym, params[], ret_type, body

**parse_match**:
```
match expr { pattern => body , ... }
```
pattern 可以是: 字面量、`_`、范围(`1..10`)、枚举变体(`Enum::Variant(v)`)、多模式(`1|2|3`)

### 测试要点

- 所有字面量: 整数、浮点、字符串、字符、bool
- 运算符优先级: `a + b * c` → `a + (b * c)`
- 结合性: `a - b - c` → `(a - b) - c`
- 所有语句: let(含/不含 mut/type), if/else, while, for, match, return, block
- 表达式: 函数调用、字段访问、索引、取地址、解引用
- 声明: fn, type struct, type enum, extern, import
- 嵌套结构: 函数内 let + if + while + block
- 错误处理: 语法错误时报告且不崩溃

### 验收标准
- [ ] 所有语法结构正确解析为 AST
- [ ] 运算符优先级严格按设计执行
- [ ] 语法错误产生有意义消息 (含行号)
- [ ] `test_parser.c` 全部通过

---

## Sprint 1d: Semantic Analysis (语义分析)

### 文件
- `compiler/src/sema.h`
- `compiler/src/sema.c`
- `compiler/tests/unit/test_sema.c`

### 两遍遍历

```c
void sema_check(Module *module) {
    // Pass 1: 注册所有顶层声明 (函数名、类型名)
    for each decl in module.decls:
        sema_declare_top_level(&ctx, decl);

    // Pass 2: 分析每个声明的函数体和类型定义
    for each decl in module.decls:
        sema_analyze_decl(&ctx, decl);
}
```

### 类型推断规则

| 表达式 | 推断类型 |
|--------|---------|
| `42` | `i32` |
| `42u64` | `u64` |
| `3.14` | `f64` |
| `true` / `false` | `bool` |
| `"hello"` | `[*]u8` |
| `&expr` | `*typeof(expr)` |
| `*ptr` | 解引用 ptr 指向的类型 |
| `a + b` | a 和 b 的算术类型 (需同类型) |
| `a == b` | `bool` |
| `if cond { a } else { b }` | unify(typeof(a), typeof(b)) |
| `{ stmts... }` | 最后一条语句的类型 (无最后语句 → `()`) |
| `return expr` | `()` (语句类型), 但检查 expr 与函数返回类型兼容 |

### 核心函数骨架

```c
Type *sema_infer_expr(SemaContext *ctx, Node *expr) {
    switch (expr->kind) {
        case NODE_INT:     return type_primitive(ctx->arena, expr->int_lit.prim);
        case NODE_BOOL:    return type_primitive(ctx->arena, TYPE_BOOL);
        case NODE_IDENT:   return sema_lookup_ident(ctx, expr);
        case NODE_BINARY:  return sema_check_binary(ctx, expr);
        case NODE_IF:      return sema_check_if(ctx, expr);
        case NODE_BLOCK:   return sema_check_block(ctx, expr);
        case NODE_LET:     return sema_check_let(ctx, expr);
        case NODE_CALL:    return sema_check_call(ctx, expr);
        // ...
    }
}
```

### 错误检测

- 未定义变量引用
- 类型不匹配 (如 `"hello" + 42`)
- 函数参数数量/类型不匹配
- 对非指针类型解引用
- 对非结构体类型做字段访问
- match 的 arm 类型不统一
- struct 字面量字段名不存在或类型不匹配

### 验收标准
- [ ] 字面量类型正确推断
- [ ] let 绑定: 类型推断和显式标注均正确
- [ ] 二元运算: 合法操作通过, 非法操作报错
- [ ] if/else: 分支类型统一, 无 else 返回 ()
- [ ] 函数: 参数类型解析, 返回类型推断
- [ ] 未定义变量、类型不匹配等均报错
- [ ] 作用域遮蔽正常工作
- [ ] `test_sema.c` 全部通过 (含错误测试)

---

## Sprint 1e: QBE Codegen

### 文件
- `compiler/src/ir.h` + `ir.c` — IR 构建器
- `compiler/src/codegen.h` + `codegen.c` — AST → QBE IL
- `compiler/tests/unit/test_codegen.c`

### IR 构建器

封装 QBE IL 的文本生成: 临时变量命名、基本块标签、指令格式。

```c
typedef struct {
    Arena *arena;
    char *buf;
    size_t len, cap;
    int next_tmp, next_block;
} IRBuf;

void ir_init(IRBuf *ir, Arena *arena);
int  ir_new_tmp(IRBuf *ir);          // 返回临时变量 ID
int  ir_new_block(IRBuf *ir);        // 返回基本块 ID
void ir_emit(IRBuf *ir, const char *fmt, ...);
void ir_emit_ret(IRBuf *ir, int tmp, char qbe_type);
void ir_emit_jnz(IRBuf *ir, int cond, int then_b, int else_b);
void ir_emit_phi(IRBuf *ir, int dst, char qt, int n, /* pairs */...);
// ...
```

### QBE 类型映射

| jhyy | QBE |
|------|-----|
| i8/u8 | w (load 用 extub/extsb) |
| i16/u16 | w (load 用 extuh/extsh) |
| i32/u32 | w |
| i64/u64 | l |
| f32 | s |
| f64 | d |
| bool | w (0/1) |
| 指针 | l |
| () | 不生成 ret 值 |

### 核心 codegen 规则

**不可变 let (SSA)**:
```
let x = 42;  →  %x =w copy 42
```

**可变 let (栈槽)**:
```
let mut x = 0;  →  %x =l alloc4 4;  storew 0, %x
x = 5;          →  storew 5, %x_slot
```

**if/else 表达式**:
```
if cond { a } else { b }
→  jnz %cond, @then, @else
   @then: ... jmp @merge
   @else: ... jmp @merge
   @merge: %r =w phi @then %tv, @else %ev
```

**while 循环**:
```
→  @loop: %phi =w phi @entry %init, @body %next
   jnz %cmp, @body, @exit
   @body: ... jmp @loop
   @exit:
```

**match 表达式**:
```
→  链式比较跳转到各 arm, 最后 phi 汇合
```

**函数定义**:
```
fn add(a: i32, b: i32) -> i32 { a + b }
→  export function w $add(w %a, w %b) { @entry: %r =w add %a, %b; ret %r }
```

**struct 构造和访问**:
```
let p = Point { x: 10, y: 20 };  →  alloc8 + storew 于偏移0 + storew 于偏移4
p.x                               →  loadw 于偏移0
```

**enum 构造和 match**:
```
Option::Some(42)  →  alloc8 + storew tag(0) + storew payload(42)
match opt { ... } →  loadw tag → cew/ceqw 比较 → jnz → extract payload
```

**Arena 操作**: 编译为对 runtime.c 中 C 函数的调用。

### Hello World 端到端

```rust
// hello.jhyy
fn main_jhyy() -> i32 { 42 }
```

预期 QBE IL:
```qbe
export function w $main_jhyy() {
@entry
    %0 =w copy 42
    ret %0
}
```

编译运行:
```bash
jhyy compile hello.jhyy -o hello
./hello
echo $?  # → 42
```

### 验收标准
- [ ] Hello World 端到端跑通
- [ ] 整数四则运算
- [ ] let 不可变 (SSA) 和可变 (栈槽)
- [ ] 函数调用 (参数传递、返回值)
- [ ] if/else 表达式
- [ ] while 循环
- [ ] 递归 (Fibonacci)
- [ ] 多函数模块
- [ ] 生成合法的 QBE IL (qbe 无报错)

---

## Sprint 1f: 枚举、Match、指针、Arena API

### 验收标准
- [ ] enum 构造 + match 端到端
- [ ] match 多 arm (通配符 `_`、多模式 `1|2`、范围 `1..10`)
- [ ] 指针 `&` 和 `*` 端到端
- [ ] Arena 分配/释放 在运行时正确
- [ ] struct 字段读写 + 通过指针访问字段

---

## Sprint 1g: 模块系统 + CLI + 测试套件

### CLI

```
jhyy compile <input> [-o output]   编译为可执行文件
jhyy build   <input>               编译不链接 (生成 .il)
jhyy run     <input>               编译并运行
jhyy --help / version
```

### 编译流程 (cmd_compile)

```c
1. read_file(input) → source
2. lexer_init → tokenize
3. parser_parse → AST
4. sema_check → 标注类型
5. cg_module → IRBuf (QBE IL 文本)
6. write_file(output.il, ir.buf)
7. system("qbe output.il -o output.s")
8. system("gcc output.s runtime/runtime.c -o executable")
```

### 测试套件 (20+ 程序)

| 文件 | 测试内容 |
|------|---------|
| `hello.jhyy` | 返回值 |
| `arithmetic.jhyy` | 加减乘除模 |
| `comparison.jhyy` | == != < > <= >= |
| `logical.jhyy` | && \|\| ! |
| `let_infer.jhyy` | 类型推断 |
| `let_mut.jhyy` | 可变变量 |
| `if_expr.jhyy` | if/else 表达式 |
| `fib_rec.jhyy` | 递归 Fibonacci |
| `fib_iter.jhyy` | 迭代 Fibonacci |
| `while_loop.jhyy` | while 循环 |
| `for_loop.jhyy` | for 循环 |
| `function.jhyy` | 多函数调用 |
| `struct.jhyy` | 结构体 |
| `enum.jhyy` | 枚举 + match |
| `match_int.jhyy` | 整数 match |
| `pointer.jhyy` | 指针操作 |
| `arena.jhyy` | Arena 分配 |
| `ffi.jhyy` | FFI 调用 C |
| `import_a.jhyy` + `import_b.jhyy` | 模块系统 |
| `shadow.jhyy` | 变量遮蔽 |
| `nested_block.jhyy` | 嵌套作用域 |

### 验收标准
- [ ] CLI 三个子命令正常工作
- [ ] import 系统正确加载模块
- [ ] 所有 20+ 测试编译运行通过
- [ ] 错误信息含文件名和行号

---

## Phase 1 完成标准

全部 Sprint 完成后：
1. jhyy 编译器能编译自身需要的所有语言特性
2. 20+ 测试用例全部通过
3. 错误信息有效帮助定位问题
4. 代码库结构清晰，每个模块职责明确
5. 可以进入 Phase 2: jhyy 自举
