#include <stdio.h>
#include <string.h>
#include "../../src/arena.h"
#include "../../src/lexer.h"
#include "../../src/parser.h"
#include "../../src/sema.h"

static int passed = 0, failed = 0;
#define ASSERT(cond, msg) do { if(!(cond)){ fprintf(stderr,"FAIL: %s\n",msg); failed++; } else passed++; } while(0)

static Arena arena;
static Lexer lex;
static Parser p;
static SemaContext sema;

static Node *parse_and_check(const char *src) {
    arena_init(&arena, 256 * 1024);
    lexer_init(&lex, src, "test");
    parser_init(&p, &lex, &arena);
    Node *mod = parser_parse(&p);
    sema_init(&sema, &arena);
    sema_check(&sema, mod);
    return mod;
}

static Node *find_first_decl(Node *mod) {
    return node_module_data(mod)->decls[0];
}

/* ── Literal type inference ── */
static void test_infer_int(void) {
    Node *mod = parse_and_check("let x = 42;\n");
    Node *let = find_first_decl(mod);
    ASSERT(let->kind == NODE_LET, "let kind");
    NodeLet *ld = node_let_data(let);
    ASSERT(ld->sym->type != NULL, "sym has type");
    ASSERT(ld->sym->type->kind == KIND_PRIMITIVE, "int is primitive");
    ASSERT(ld->sym->type->prim == PRIM_I32, "i32 default");
}

static void test_infer_float(void) {
    Node *mod = parse_and_check("let x = 3.14;\n");
    NodeLet *ld = node_let_data(find_first_decl(mod));
    ASSERT(ld->sym->type->kind == KIND_PRIMITIVE, "float is primitive");
    ASSERT(ld->sym->type->prim == PRIM_F64, "f64 default");
}

static void test_infer_bool(void) {
    Node *mod = parse_and_check("let x = true;\n");
    NodeLet *ld = node_let_data(find_first_decl(mod));
    ASSERT(ld->sym->type->prim == PRIM_BOOL, "bool type");
}

static void test_infer_string(void) {
    Node *mod = parse_and_check("let s = \"hello\";\n");
    NodeLet *ld = node_let_data(find_first_decl(mod));
    ASSERT(ld->sym->type->kind == KIND_SLICE, "string is slice");
}

/* ── Type annotation ── */
static void test_explicit_type(void) {
    Node *mod = parse_and_check("let x: i64 = 100i64;\n");
    NodeLet *ld = node_let_data(find_first_decl(mod));
    ASSERT(ld->sym->type->kind == KIND_PRIMITIVE, "explicit type");
    ASSERT(ld->sym->type->prim == PRIM_I64, "i64 explicit");
}

/* ── Binary expression types ── */
static void test_binary_type(void) {
    Node *mod = parse_and_check("let x = 1 + 2;\n");
    NodeLet *ld = node_let_data(find_first_decl(mod));
    ASSERT(ld->sym->type->prim == PRIM_I32, "add yields i32");

    arena_free(&arena);
    mod = parse_and_check("let x = 1 + 2;\n"); /* reuse arena */
    (void)mod;
}

static void test_comparison_type(void) {
    Node *mod = parse_and_check("let x = a == b;\n");
    NodeLet *ld = node_let_data(find_first_decl(mod));
    ASSERT(ld->sym->type->prim == PRIM_BOOL, "== yields bool");
}

/* ── Pointer operations ── */
static void test_addr_of(void) {
    Node *mod = parse_and_check("let p = &x;\n");
    NodeLet *ld = node_let_data(find_first_decl(mod));
    ASSERT(ld->sym->type->kind == KIND_POINTER, "& yields pointer");
}

/* ── Function type inference ── */
static void test_func_type(void) {
    Node *mod = parse_and_check("fn add(a: i32, b: i32) -> i32 { a + b }\n");
    NodeFuncDecl *fd = node_func_decl_data(find_first_decl(mod));
    ASSERT(fd->sym->type != NULL, "func has type");
    ASSERT(fd->sym->type->kind == KIND_FUNC, "func type kind");
    ASSERT(fd->sym->type->func.nparams == 2, "2 params");
    ASSERT(fd->sym->type->func.ret->prim == PRIM_I32, "returns i32");
}

/* ── If expression type ── */
static void test_if_type(void) {
    Node *mod = parse_and_check("let x = if cond { 1 } else { 2 };\n");
    NodeLet *ld = node_let_data(find_first_decl(mod));
    ASSERT(ld->sym->type->kind == KIND_PRIMITIVE, "if yields type");
}

/* ── Block expression type ── */
static void test_block_type(void) {
    Node *mod = parse_and_check("let x = { let y = 1; y };\n");
    NodeLet *ld = node_let_data(find_first_decl(mod));
    ASSERT(ld->sym->type->kind == KIND_PRIMITIVE, "block yields last stmt type");
}

/* ── Error: undefined variable ── */
static void test_undefined_var(void) {
    Node *mod = parse_and_check("let x = y;\n");
    ASSERT(sema_check(&sema, mod) > 0, "undefined variable should produce error");
}

/* ── Error: type mismatch ── */
static void test_type_mismatch(void) {
    /* let x: i64 = "hello"; — cannot compile since string literal parser issue
       But we can test the concept */
    arena_free(&arena);
    arena_init(&arena, 256 * 1024);
    lexer_init(&lex, "fn f() -> i32 { \"hello\" }\n", "test");
    parser_init(&p, &lex, &arena);
    Node *mod = parser_parse(&p);
    sema_init(&sema, &arena);
    sema_check(&sema, mod);
    ASSERT(sema.error_count > 0, "type mismatch should produce error");
}

int main(void) {
    printf("=== Semantic Analysis Tests ===\n\n");

    printf("[Type Inference]\n");
    test_infer_int();
    test_infer_float();
    test_infer_bool();
    test_infer_string();

    printf("[Type Annotations]\n");
    test_explicit_type();

    printf("[Binary / Comparison]\n");
    test_binary_type();
    test_comparison_type();

    printf("[Pointer]\n");
    test_addr_of();

    printf("[Function]\n");
    test_func_type();

    printf("[Control Flow]\n");
    test_if_type();
    test_block_type();

    printf("[Errors]\n");
    test_undefined_var();
    test_type_mismatch();

    printf("\nResults: %d passed, %d failed\n", passed, failed);
    return failed > 0 ? 1 : 0;
}
