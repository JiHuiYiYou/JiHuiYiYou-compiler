#include <stdio.h>
#include <string.h>
#include "../../src/lexer.h"
#include "../../src/parser.h"
#include "../../src/arena.h"
#include "../../src/ast.h"

static int passed = 0, failed = 0;
#define ASSERT(cond, msg) do { if(!(cond)) { fprintf(stderr,"FAIL: %s\n",msg); failed++; } else passed++; } while(0)

static Arena arena;
static Lexer lexer;
static Parser parser;

static Node *parse(const char *src) {
    arena_init(&arena, 1024 * 1024);
    lexer_init(&lexer, src, "test");
    parser_init(&parser, &lexer, &arena);
    return parser_parse(&parser);
}

/* ── Literals ── */
static void test_int_literal(void) {
    Node *mod = parse("42;");
    ASSERT(mod->kind == NODE_MODULE, "module node");
    NodeModule *md = node_module_data(mod);
    ASSERT(md->ndeccls == 1, "one decl");
    Node *decl = md->decls[0];
    ASSERT(decl->kind == NODE_EXPR_STMT, "expr stmt");
    /* the expr inside the expr_stmt */
    Node *expr = node_expr_stmt_data(decl)->expr;
    ASSERT(expr->kind == NODE_INT, "int literal");
    ASSERT(node_int_data(expr)->value == 42, "value 42");
}

static void test_float_literal(void) {
    Node *mod = parse("3.14;");
    NodeModule *md = node_module_data(mod);
    Node *decl = md->decls[0];
    Node *expr = node_expr_stmt_data(decl)->expr;
    ASSERT(expr->kind == NODE_FLOAT, "float literal");
}

static void test_bool_literal(void) {
    Node *mod = parse("true;");
    NodeModule *md = node_module_data(mod);
    Node *decl = md->decls[0];
    Node *expr = node_expr_stmt_data(decl)->expr;
    ASSERT(expr->kind == NODE_BOOL, "bool literal true");
    ASSERT(node_bool_data(expr)->value == true, "true value");

    arena_free(&arena);
    mod = parse("false;");
    md = node_module_data(mod);
    decl = md->decls[0];
    expr = node_expr_stmt_data(decl)->expr;
    ASSERT(expr->kind == NODE_BOOL, "bool literal false");
    ASSERT(node_bool_data(expr)->value == false, "false value");
}

static void test_string_literal(void) {
    Node *mod = parse("\"hello\";");
    NodeModule *md = node_module_data(mod);
    Node *decl = md->decls[0];
    Node *expr = node_expr_stmt_data(decl)->expr;
    ASSERT(expr->kind == NODE_STRING, "string literal");
    NodeString *s = node_string_data(expr);
    ASSERT(s->len == 5, "string len = 5");
    ASSERT(strncmp(s->chars, "hello", 5) == 0, "string content");
}

/* ── Binary expressions ── */
static void test_binary_arithmetic(void) {
    Node *mod = parse("1 + 2 * 3;");
    Node *expr = node_expr_stmt_data(node_module_data(mod)->decls[0])->expr;
    ASSERT(expr->kind == NODE_BINARY, "binary");
    ASSERT(node_binary_data(expr)->op == TOKEN_PLUS, "top op +");
    /* right child should be 2 * 3 (higher precedence) */
    Node *right = node_binary_data(expr)->right;
    ASSERT(right->kind == NODE_BINARY, "right is binary");
    ASSERT(node_binary_data(right)->op == TOKEN_STAR, "right op *");
}

static void test_comparison(void) {
    Node *mod = parse("a == b;");
    Node *expr = node_expr_stmt_data(node_module_data(mod)->decls[0])->expr;
    ASSERT(expr->kind == NODE_BINARY, "binary == ");
    ASSERT(node_binary_data(expr)->op == TOKEN_EQEQ, "op ==");
}

static void test_logical(void) {
    Node *mod = parse("a && b || c;");
    Node *expr = node_expr_stmt_data(node_module_data(mod)->decls[0])->expr;
    ASSERT(expr->kind == NODE_BINARY, "binary logical");
    ASSERT(node_binary_data(expr)->op == TOKEN_PIPEPIPE, "top is ||");
}

static void test_field_access(void) {
    Node *mod = parse("point.x;");
    Node *expr = node_expr_stmt_data(node_module_data(mod)->decls[0])->expr;
    ASSERT(expr->kind == NODE_FIELD, "field access");
    ASSERT(strcmp(node_field_data(expr)->field, "x") == 0, "field name x");
}

static void test_call(void) {
    Node *mod = parse("f(1, 2);");
    Node *expr = node_expr_stmt_data(node_module_data(mod)->decls[0])->expr;
    ASSERT(expr->kind == NODE_CALL, "call");
    ASSERT(node_call_data(expr)->nargs == 2, "2 args");
}

static void test_deref_and_addr(void) {
    Node *mod = parse("*p;");
    Node *expr = node_expr_stmt_data(node_module_data(mod)->decls[0])->expr;
    ASSERT(expr->kind == NODE_DEREF, "deref");

    arena_free(&arena);
    mod = parse("&x;");
    expr = node_expr_stmt_data(node_module_data(mod)->decls[0])->expr;
    ASSERT(expr->kind == NODE_ADDR_OF, "addr of");
}

/* ── Let bindings ── */
static void test_let_simple(void) {
    Node *mod = parse("let x = 42;\n");
    Node *decl = node_module_data(mod)->decls[0];
    ASSERT(decl->kind == NODE_LET, "let");
    NodeLet *ld = node_let_data(decl);
    ASSERT(!ld->is_mutable, "not mutable");
    ASSERT(ld->init->kind == NODE_INT, "init int");
}

static void test_let_mut(void) {
    Node *mod = parse("let mut y = 10;\n");
    Node *decl = node_module_data(mod)->decls[0];
    ASSERT(decl->kind == NODE_LET, "let mut");
    ASSERT(node_let_data(decl)->is_mutable, "is mutable");
}

/* ── Functions ── */
static void test_func_simple(void) {
    Node *mod = parse("fn add(a: i32, b: i32) -> i32 { a + b }\n");
    Node *decl = node_module_data(mod)->decls[0];
    ASSERT(decl->kind == NODE_FUNC_DECL, "func decl");
    NodeFuncDecl *fd = node_func_decl_data(decl);
    ASSERT(fd->nparams == 2, "2 params");
    ASSERT(fd->body != NULL, "has body");
}

static void test_func_no_params(void) {
    Node *mod = parse("fn main_jhyy() -> i32 { 42 }\n");
    Node *decl = node_module_data(mod)->decls[0];
    ASSERT(decl->kind == NODE_FUNC_DECL, "func no params");
    ASSERT(node_func_decl_data(decl)->nparams == 0, "0 params");
}

/* ── If / else ── */
static void test_if_expr(void) {
    Node *mod = parse("if x > 0 { 1 } else { -1 };");
    Node *decl = node_module_data(mod)->decls[0];
    ASSERT(decl->kind == NODE_IF, "if");
    NodeIf *id = node_if_data(decl);
    ASSERT(id->cond != NULL, "has cond");
    ASSERT(id->then_body != NULL, "has then");
    ASSERT(id->else_body != NULL, "has else");
}

/* ── While ── */
static void test_while_loop(void) {
    Node *mod = parse("while i < 10 { i = i + 1;\n }");
    Node *decl = node_module_data(mod)->decls[0];
    ASSERT(decl->kind == NODE_WHILE, "while");
}

/* ── For ── */
static void test_for_loop(void) {
    Node *mod = parse("for i in 0..10 { i }\n");
    Node *decl = node_module_data(mod)->decls[0];
    ASSERT(decl->kind == NODE_FOR, "for");
}

/* ── Match ── */
static void test_match_simple(void) {
    Node *mod = parse("match x { 0 => \"zero\", _ => \"other\" }\n");
    Node *decl = node_module_data(mod)->decls[0];
    ASSERT(decl->kind == NODE_MATCH, "match");
    ASSERT(node_match_data(decl)->narms == 2, "2 arms");
}

/* ── Return ── */
static void test_return_expr(void) {
    Node *mod = parse("return 42;\n");
    Node *decl = node_module_data(mod)->decls[0];
    ASSERT(decl->kind == NODE_RETURN, "return");
    ASSERT(node_return_data(decl)->expr != NULL, "has expr");
}

static void test_return_void(void) {
    Node *mod = parse("return;\n");
    Node *decl = node_module_data(mod)->decls[0];
    ASSERT(decl->kind == NODE_RETURN, "return void");
    ASSERT(node_return_data(decl)->expr == NULL, "no expr");
}

/* ── Block ── */
static void test_block_expr(void) {
    Node *mod = parse("{ let x = 1; x };");
    Node *decl = node_module_data(mod)->decls[0];
    ASSERT(decl->kind == NODE_BLOCK, "block");
    ASSERT(node_block_data(decl)->nstmts == 2, "2 stmts in block");
}

/* ── Extern ── */
static void test_extern_func(void) {
    Node *mod = parse("extern fn puts(s: i32) -> i32;\n");
    Node *decl = node_module_data(mod)->decls[0];
    ASSERT(decl->kind == NODE_FUNC_DECL, "extern func");
    ASSERT(node_func_decl_data(decl)->is_extern, "is extern");
}

/* ── Type declaration ── */
static void test_type_decl(void) {
    Node *mod = parse("type Point = struct { }\n");
    Node *decl = node_module_data(mod)->decls[0];
    ASSERT(decl->kind == NODE_TYPE_DECL, "type decl");
}

/* ── Import ── */
static void test_import(void) {
    Node *mod = parse("import os;\n");
    Node *decl = node_module_data(mod)->decls[0];
    ASSERT(decl->kind == NODE_IMPORT_DECL, "import");
}

/* ── Multiple declarations ── */
static void test_multiple_decls(void) {
    Node *mod = parse("let x = 1;\nlet y = 2;\n");
    ASSERT(node_module_data(mod)->ndeccls == 2, "2 decls");
}

/* ── Empty file ── */
static void test_empty_file(void) {
    Node *mod = parse("");
    ASSERT(mod->kind == NODE_MODULE, "empty module");
    ASSERT(node_module_data(mod)->ndeccls == 0, "0 decls");
}

int main(void) {
    printf("=== Parser Unit Tests ===\n\n");

    printf("[Literals]\n");
    test_int_literal();
    test_float_literal();
    test_bool_literal();
    test_string_literal();

    printf("[Expressions]\n");
    test_binary_arithmetic();
    test_comparison();
    test_logical();
    test_field_access();
    test_call();
    test_deref_and_addr();

    printf("[Statements]\n");
    test_let_simple();
    test_let_mut();
    test_if_expr();
    test_while_loop();
    test_for_loop();
    test_match_simple();
    test_return_expr();
    test_return_void();
    test_block_expr();

    printf("[Declarations]\n");
    test_func_simple();
    test_func_no_params();
    test_extern_func();
    test_type_decl();
    test_import();

    printf("[Other]\n");
    test_multiple_decls();
    test_empty_file();

    printf("\nResults: %d passed, %d failed\n", passed, failed);
    return failed > 0 ? 1 : 0;
}
