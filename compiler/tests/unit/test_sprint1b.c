#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../../src/arena.h"
#include "../../src/types.h"
#include "../../src/symtab.h"
#include "../../src/ast.h"

static int passed = 0, failed = 0;
#define ASSERT(cond, msg) do { \
    if (!(cond)) { fprintf(stderr, "FAIL: %s (%s:%d)\n", msg, __FILE__, __LINE__); failed++; } \
    else passed++; \
} while(0)

/* ── Arena tests ── */
static void test_arena_basic(void) {
    Arena a;
    arena_init(&a, 1024);

    void *p1 = arena_alloc(&a, 100);
    ASSERT(p1 != NULL, "arena alloc 100 bytes");
    void *p2 = arena_alloc(&a, 200);
    ASSERT(p2 != NULL, "arena alloc 200 bytes");
    ASSERT((char *)p2 > (char *)p1, "allocations are sequential");

    arena_reset(&a);
    void *p3 = arena_alloc(&a, 50);
    ASSERT(p3 == p1, "after reset, alloc returns same start");

    arena_free(&a);
}

static void test_arena_aligned(void) {
    Arena a;
    arena_init(&a, 1024);

    void *p = arena_alloc_aligned(&a, 8, 16);
    ASSERT(p != NULL, "aligned alloc");
    ASSERT(((uintptr_t)p & 15) == 0, "16-byte alignment satisfied");

    arena_free(&a);
}

static void test_arena_strdup(void) {
    Arena a;
    arena_init(&a, 1024);

    char *s = arena_strdup(&a, "hello", 5);
    ASSERT(s != NULL, "strdup");
    ASSERT(strcmp(s, "hello") == 0, "strdup content");
    ASSERT(s[5] == '\0', "strdup null terminated");

    arena_free(&a);
}

static void test_arena_large_alloc(void) {
    Arena a;
    arena_init(&a, 64);  /* smaller than request */

    void *p = arena_alloc(&a, 1024);
    ASSERT(p != NULL, "large alloc creates new block");

    arena_free(&a);
}

/* ── Type tests ── */
static void test_primitive_types(void) {
    Arena a;
    arena_init(&a, 1024);

    Type *i32 = type_primitive(&a, PRIM_I32);
    ASSERT(i32 != NULL, "i32 type");
    ASSERT(i32->kind == KIND_PRIMITIVE, "i32 is primitive");
    ASSERT(type_size(i32) == 4, "i32 size = 4");
    ASSERT(type_align(i32) == 4, "i32 align = 4");

    Type *u8 = type_primitive(&a, PRIM_U8);
    ASSERT(type_size(u8) == 1, "u8 size = 1");

    Type *i64 = type_primitive(&a, PRIM_I64);
    ASSERT(type_size(i64) == 8, "i64 size = 8");

    Type *f64 = type_primitive(&a, PRIM_F64);
    ASSERT(type_size(f64) == 8, "f64 size = 8");

    Type *b = type_primitive(&a, PRIM_BOOL);
    ASSERT(type_size(b) == 1, "bool size = 1");

    arena_free(&a);
}

static void test_pointer_type(void) {
    Arena a;
    arena_init(&a, 1024);

    Type *i32 = type_primitive(&a, PRIM_I32);
    Type *ptr = type_pointer(&a, i32);
    ASSERT(ptr->kind == KIND_POINTER, "ptr kind");
    ASSERT(ptr->pointer.elem == i32, "ptr elem");
    ASSERT(type_size(ptr) == 8, "ptr size = 8");
    ASSERT(type_align(ptr) == 8, "ptr align = 8");

    arena_free(&a);
}

static void test_type_eq(void) {
    Arena a;
    arena_init(&a, 1024);

    Type *i32_a = type_primitive(&a, PRIM_I32);
    Type *i32_b = type_primitive(&a, PRIM_I32);
    Type *i64 = type_primitive(&a, PRIM_I64);

    ASSERT(type_eq(i32_a, i32_b), "i32 == i32");
    ASSERT(!type_eq(i32_a, i64), "i32 != i64");
    ASSERT(type_eq(type_void(), type_void()), "void == void");

    arena_free(&a);
}

/* ── Symbol table tests ── */
static void test_symtab_insert_lookup(void) {
    Arena a;
    arena_init(&a, 1024);
    SymTable *t = symtab_new(&a, NULL);

    Type *i32 = type_primitive(&a, PRIM_I32);
    Sym *s = symtab_insert(t, "x", SYM_VAR, i32, false, 0);
    ASSERT(s != NULL, "insert x");
    ASSERT(strcmp(s->name, "x") == 0, "x name");
    ASSERT(s->type == i32, "x type = i32");
    ASSERT(!s->is_mutable, "x immutable");

    Sym *found = symtab_lookup(t, "x");
    ASSERT(found == s, "lookup x returns same");

    Sym *notfound = symtab_lookup(t, "y");
    ASSERT(notfound == NULL, "lookup y returns NULL");

    arena_free(&a);
}

static void test_symtab_duplicate(void) {
    Arena a;
    arena_init(&a, 1024);
    SymTable *t = symtab_new(&a, NULL);

    Type *i32 = type_primitive(&a, PRIM_I32);
    Sym *s1 = symtab_insert(t, "x", SYM_VAR, i32, false, 0);
    ASSERT(s1 != NULL, "insert x first time");
    Sym *s2 = symtab_insert(t, "x", SYM_VAR, i32, false, 0);
    ASSERT(s2 == NULL, "insert x second time returns NULL (duplicate)");

    arena_free(&a);
}

static void test_symtab_scoping(void) {
    Arena a;
    arena_init(&a, 1024);
    SymTable *global = symtab_new(&a, NULL);

    Type *i32 = type_primitive(&a, PRIM_I32);
    Sym *gx = symtab_insert(global, "x", SYM_VAR, i32, false, 0);
    ASSERT(gx != NULL, "global x");

    SymTable *local = symtab_new(&a, global);
    Type *i64 = type_primitive(&a, PRIM_I64);
    Sym *lx = symtab_insert(local, "x", SYM_VAR, i64, false, 1);
    ASSERT(lx != NULL, "local x shadows global");

    /* local lookup finds local first */
    Sym *found = symtab_lookup(local, "x");
    ASSERT(found == lx, "local lookup returns local x");

    /* local-only lookup doesn't find global */
    Sym *local_only = symtab_lookup_local(local, "x");
    ASSERT(local_only == lx, "local-only finds x");

    /* global lookup still sees its own x */
    Sym *global_found = symtab_lookup(global, "x");
    ASSERT(global_found == gx, "global lookup returns global x");

    arena_free(&a);
}

/* ── AST constructor tests ── */
static void test_ast_nodes(void) {
    Arena a;
    arena_init(&a, 1024);

    SourceLoc loc = { .line = 1, .col = 1, .filename = "test" };

    /* int literal */
    Node *n = ast_new_int(&a, loc, 42, PRIM_I32);
    ASSERT(n->kind == NODE_INT, "int node kind");
    ASSERT(node_int_data(n)->value == 42, "int value");
    ASSERT(n->loc.line == 1, "int loc line");

    /* binary */
    Node *left = ast_new_int(&a, loc, 1, PRIM_I32);
    Node *right = ast_new_int(&a, loc, 2, PRIM_I32);
    Node *add = ast_new_binary(&a, loc, TOKEN_PLUS, left, right);
    ASSERT(add->kind == NODE_BINARY, "binary kind");
    ASSERT(node_binary_data(add)->op == TOKEN_PLUS, "binary op");
    ASSERT(node_binary_data(add)->left == left, "binary left");
    ASSERT(node_binary_data(add)->right == right, "binary right");

    /* block */
    Node *stmts[] = { left, right };
    Node *block = ast_new_block(&a, loc, stmts, 2);
    ASSERT(block->kind == NODE_BLOCK, "block kind");
    ASSERT(node_block_data(block)->nstmts == 2, "block nstmts");

    /* let */
    Type *i32 = type_primitive(&a, PRIM_I32);
    SymTable *st = symtab_new(&a, NULL);
    Sym *sym = symtab_insert(st, "x", SYM_VAR, i32, false, 0);
    Node *let = ast_new_let(&a, loc, false, sym, NULL, left);
    ASSERT(let->kind == NODE_LET, "let kind");
    ASSERT(!node_let_data(let)->is_mutable, "let not mut");
    ASSERT(node_let_data(let)->sym == sym, "let sym");

    printf("  %s\n", node_kind_name(NODE_BINARY));
    printf("  %s\n", node_kind_name(NODE_FUNC_DECL));

    arena_free(&a);
}

int main(void) {
    printf("=== Sprint 1b: Data Structures Tests ===\n\n");

    printf("[Arena]\n");
    test_arena_basic();
    test_arena_aligned();
    test_arena_strdup();
    test_arena_large_alloc();

    printf("\n[Types]\n");
    test_primitive_types();
    test_pointer_type();
    test_type_eq();

    printf("\n[SymTab]\n");
    test_symtab_insert_lookup();
    test_symtab_duplicate();
    test_symtab_scoping();

    printf("\n[AST]\n");
    test_ast_nodes();

    printf("\nResults: %d passed, %d failed\n", passed, failed);
    return failed > 0 ? 1 : 0;
}
