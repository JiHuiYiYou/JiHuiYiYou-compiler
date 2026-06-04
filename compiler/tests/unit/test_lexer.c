#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../../src/lexer.h"

static int passed = 0;
static int failed = 0;

#define ASSERT(cond, msg) do { \
    if (!(cond)) { \
        fprintf(stderr, "FAIL: %s (%s:%d)\n", msg, __FILE__, __LINE__); \
        failed++; \
    } else { passed++; } \
} while(0)

#define ASSERT_TOKEN(tok, exp_kind, exp_text) do { \
    ASSERT(tok.kind == exp_kind, "token kind mismatch: " exp_text); \
    if (tok.kind == exp_kind && strncmp(tok.start, exp_text, tok.length) != 0) { \
        fprintf(stderr, "  expected text '%s', got '%.*s'\n", exp_text, (int)tok.length, tok.start); \
        failed++; \
    } \
} while(0)

/* Helper: run lexer on source, return next token kind */
static TokenKind next_kind(Lexer *l) { return lexer_next(l).kind; }

/* ── Single-char tokens ── */
static void test_single_char_tokens(void) {
    Lexer l;
    lexer_init(&l, "()+ -*/%,;:.", "test");
    ASSERT(next_kind(&l) == TOKEN_LPAREN,    "(");
    ASSERT(next_kind(&l) == TOKEN_RPAREN,    ")");
    ASSERT(next_kind(&l) == TOKEN_PLUS,      "+");
    ASSERT(next_kind(&l) == TOKEN_MINUS,     "-");
    ASSERT(next_kind(&l) == TOKEN_STAR,      "*");
    ASSERT(next_kind(&l) == TOKEN_SLASH,     "/");
    ASSERT(next_kind(&l) == TOKEN_PERCENT,   "%");
    ASSERT(next_kind(&l) == TOKEN_COMMA,     ",");
    ASSERT(next_kind(&l) == TOKEN_SEMICOLON, ";");
    ASSERT(next_kind(&l) == TOKEN_COLON,     ":");
    ASSERT(next_kind(&l) == TOKEN_DOT,       ".");
    ASSERT(next_kind(&l) == TOKEN_EOF,       "EOF");
}

/* ── Double-char tokens ── */
static void test_double_char_tokens(void) {
    Lexer l;
    lexer_init(&l, "== != <= >= -> => && || .. += -= *= /= %= << >>", "test");

    Token t;

    t = lexer_next(&l); ASSERT(t.kind == TOKEN_EQEQ,       "==");
    t = lexer_next(&l); ASSERT(t.kind == TOKEN_BANGEQ,     "!=");
    t = lexer_next(&l); ASSERT(t.kind == TOKEN_LTEQ,       "<=");
    t = lexer_next(&l); ASSERT(t.kind == TOKEN_GTEQ,       ">=");
    t = lexer_next(&l); ASSERT(t.kind == TOKEN_ARROW,      "->");
    t = lexer_next(&l); ASSERT(t.kind == TOKEN_FATARROW,   "=>");
    t = lexer_next(&l); ASSERT(t.kind == TOKEN_AMPAMP,     "&&");
    t = lexer_next(&l); ASSERT(t.kind == TOKEN_PIPEPIPE,   "||");
    t = lexer_next(&l); ASSERT(t.kind == TOKEN_DOTDOT,     "..");
    t = lexer_next(&l); ASSERT(t.kind == TOKEN_PLUSEQ,     "+=");
    t = lexer_next(&l); ASSERT(t.kind == TOKEN_MINUSEQ,    "-=");
    t = lexer_next(&l); ASSERT(t.kind == TOKEN_STAREQ,     "*=");
    t = lexer_next(&l); ASSERT(t.kind == TOKEN_SLASHEQ,    "/=");
    t = lexer_next(&l); ASSERT(t.kind == TOKEN_PERCENTEQ,  "%=");
    t = lexer_next(&l); ASSERT(t.kind == TOKEN_LTLT,       "<<");
    t = lexer_next(&l); ASSERT(t.kind == TOKEN_GTGT,       ">>");
    ASSERT(next_kind(&l) == TOKEN_EOF, "EOF");
}

/* ── Brackets ── */
static void test_brackets(void) {
    Lexer l;
    lexer_init(&l, "(){}[]", "test");
    ASSERT(next_kind(&l) == TOKEN_LPAREN,   "(");
    ASSERT(next_kind(&l) == TOKEN_RPAREN,   ")");
    ASSERT(next_kind(&l) == TOKEN_LBRACE,   "{");
    ASSERT(next_kind(&l) == TOKEN_RBRACE,   "}");
    ASSERT(next_kind(&l) == TOKEN_LBRACKET, "[");
    ASSERT(next_kind(&l) == TOKEN_RBRACKET, "]");
    ASSERT(next_kind(&l) == TOKEN_EOF,      "EOF");
}

/* ── Integers ── */
static void test_integers(void) {
    Lexer l;
    lexer_init(&l, "0 42 0xFF 0o77 0b1010 100i64 255u8 1u16", "test");
    Token t;

    t = lexer_next(&l);
    ASSERT(t.kind == TOKEN_INT, "0");
    ASSERT(strncmp(t.start, "0", t.length) == 0, "zero");

    t = lexer_next(&l);
    ASSERT(t.kind == TOKEN_INT, "42");
    ASSERT(strncmp(t.start, "42", t.length) == 0, "42");

    t = lexer_next(&l);
    ASSERT(t.kind == TOKEN_INT, "0xFF");
    ASSERT(strncmp(t.start, "0xFF", t.length) == 0, "0xFF");

    t = lexer_next(&l);
    ASSERT(t.kind == TOKEN_INT, "0o77");
    ASSERT(strncmp(t.start, "0o77", t.length) == 0, "0o77");

    t = lexer_next(&l);
    ASSERT(t.kind == TOKEN_INT, "0b1010");
    ASSERT(strncmp(t.start, "0b1010", t.length) == 0, "0b1010");

    t = lexer_next(&l);
    ASSERT(t.kind == TOKEN_INT, "100i64");
    ASSERT(strncmp(t.start, "100i64", t.length) == 0, "100i64");

    t = lexer_next(&l);
    ASSERT(t.kind == TOKEN_INT, "255u8");
    ASSERT(strncmp(t.start, "255u8", t.length) == 0, "255u8");

    t = lexer_next(&l);
    ASSERT(t.kind == TOKEN_INT, "1u16");
    ASSERT(strncmp(t.start, "1u16", t.length) == 0, "1u16");

    ASSERT(next_kind(&l) == TOKEN_EOF, "EOF");
}

/* ── Floats ── */
static void test_floats(void) {
    Lexer l;
    lexer_init(&l, "3.14 0.5 10.0", "test");
    Token t;

    t = lexer_next(&l);
    ASSERT(t.kind == TOKEN_FLOAT, "3.14");
    ASSERT(strncmp(t.start, "3.14", t.length) == 0, "3.14");

    t = lexer_next(&l);
    ASSERT(t.kind == TOKEN_FLOAT, "0.5");
    ASSERT(strncmp(t.start, "0.5", t.length) == 0, "0.5");

    t = lexer_next(&l);
    ASSERT(t.kind == TOKEN_FLOAT, "10.0");
    ASSERT(strncmp(t.start, "10.0", t.length) == 0, "10.0");

    ASSERT(next_kind(&l) == TOKEN_EOF, "EOF");
}

/* ── Keywords ── */
static void test_keywords(void) {
    Lexer l;
    lexer_init(&l, "fn let mut if else while for in match return type struct enum import extern as sizeof alignof",
               "test");

    ASSERT(next_kind(&l) == TOKEN_FN,      "fn");
    ASSERT(next_kind(&l) == TOKEN_LET,     "let");
    ASSERT(next_kind(&l) == TOKEN_MUT,     "mut");
    ASSERT(next_kind(&l) == TOKEN_IF,      "if");
    ASSERT(next_kind(&l) == TOKEN_ELSE,    "else");
    ASSERT(next_kind(&l) == TOKEN_WHILE,   "while");
    ASSERT(next_kind(&l) == TOKEN_FOR,     "for");
    ASSERT(next_kind(&l) == TOKEN_IN,      "in");
    ASSERT(next_kind(&l) == TOKEN_MATCH,   "match");
    ASSERT(next_kind(&l) == TOKEN_RETURN,  "return");
    ASSERT(next_kind(&l) == TOKEN_TYPE,    "type");
    ASSERT(next_kind(&l) == TOKEN_STRUCT,  "struct");
    ASSERT(next_kind(&l) == TOKEN_ENUM,    "enum");
    ASSERT(next_kind(&l) == TOKEN_IMPORT,  "import");
    ASSERT(next_kind(&l) == TOKEN_EXTERN,  "extern");
    ASSERT(next_kind(&l) == TOKEN_AS,      "as");
    ASSERT(next_kind(&l) == TOKEN_SIZEOF,  "sizeof");
    ASSERT(next_kind(&l) == TOKEN_ALIGNOF, "alignof");
    ASSERT(next_kind(&l) == TOKEN_EOF,     "EOF");
}

/* ── Identifiers ── */
static void test_identifiers(void) {
    Lexer l;
    lexer_init(&l, "foo bar_baz _private x1 Point main_jhyy", "test");
    Token t;

    t = lexer_next(&l);
    ASSERT(t.kind == TOKEN_IDENT, "foo");
    ASSERT(strncmp(t.start, "foo", t.length) == 0, "foo");

    t = lexer_next(&l);
    ASSERT(t.kind == TOKEN_IDENT, "bar_baz");
    ASSERT(strncmp(t.start, "bar_baz", t.length) == 0, "bar_baz");

    t = lexer_next(&l);
    ASSERT(t.kind == TOKEN_IDENT, "_private");
    ASSERT(strncmp(t.start, "_private", t.length) == 0, "_private");

    t = lexer_next(&l);
    ASSERT(t.kind == TOKEN_IDENT, "x1");
    ASSERT(strncmp(t.start, "x1", t.length) == 0, "x1");

    t = lexer_next(&l);
    ASSERT(t.kind == TOKEN_IDENT, "Point");
    ASSERT(strncmp(t.start, "Point", t.length) == 0, "Point");

    t = lexer_next(&l);
    ASSERT(t.kind == TOKEN_IDENT, "main_jhyy");
    ASSERT(strncmp(t.start, "main_jhyy", t.length) == 0, "main_jhyy");

    ASSERT(next_kind(&l) == TOKEN_EOF, "EOF");
}

/* ── Strings ── */
static void test_strings(void) {
    Lexer l;
    lexer_init(&l, "\"hello\" \"world\\n\" \"escaped\\\\quote\"", "test");
    Token t;

    t = lexer_next(&l);
    ASSERT(t.kind == TOKEN_STRING, "\"hello\"");
    ASSERT(strncmp(t.start, "\"hello\"", t.length) == 0, "hello");

    t = lexer_next(&l);
    ASSERT(t.kind == TOKEN_STRING, "\"world\\n\"");
    /* includes the escape sequence */

    t = lexer_next(&l);
    ASSERT(t.kind == TOKEN_STRING, "\"escaped\\\\quote\"");
    ASSERT(next_kind(&l) == TOKEN_EOF, "EOF");
}

/* ── Chars ── */
static void test_chars(void) {
    Lexer l;
    lexer_init(&l, "'a' '\\n' '\\\\'", "test");
    Token t;

    t = lexer_next(&l);
    ASSERT(t.kind == TOKEN_CHAR, "'a'");

    t = lexer_next(&l);
    ASSERT(t.kind == TOKEN_CHAR, "'\\n'");

    t = lexer_next(&l);
    ASSERT(t.kind == TOKEN_CHAR, "'\\\\'");

    ASSERT(next_kind(&l) == TOKEN_EOF, "EOF");
}

/* ── Comments ── */
static void test_line_comment(void) {
    Lexer l;
    lexer_init(&l, "// this is a comment\n42", "test");
    /* comment should be skipped, next token is 42 */
    Token t = lexer_next(&l);
    ASSERT(t.kind == TOKEN_INT, "42 after line comment");
    ASSERT(strncmp(t.start, "42", t.length) == 0, "42 text");
    ASSERT(next_kind(&l) == TOKEN_EOF, "EOF");
}

static void test_block_comment(void) {
    Lexer l;
    lexer_init(&l, "/* block\ncomment */ 100", "test");
    Token t = lexer_next(&l);
    ASSERT(t.kind == TOKEN_INT, "100 after block comment");
    ASSERT(strncmp(t.start, "100", t.length) == 0, "100 text");
    ASSERT(next_kind(&l) == TOKEN_EOF, "EOF");
}

static void test_nested_block_comment(void) {
    Lexer l;
    lexer_init(&l, "/* outer /* inner */ still comment */ 7", "test");
    Token t = lexer_next(&l);
    ASSERT(t.kind == TOKEN_INT, "7 after nested comment");
    ASSERT(strncmp(t.start, "7", t.length) == 0, "7 text");
    ASSERT(next_kind(&l) == TOKEN_EOF, "EOF");
}

/* ── Source locations ── */
static void test_locations(void) {
    Lexer l;
    lexer_init(&l, "fn\nmain\n*\n", "test");
    Token t;

    t = lexer_next(&l);
    ASSERT(t.kind == TOKEN_FN, "fn");
    ASSERT(t.loc.line == 1, "fn on line 1");

    t = lexer_next(&l);
    ASSERT(t.kind == TOKEN_IDENT, "main");
    ASSERT(t.loc.line == 2, "main on line 2");

    t = lexer_next(&l);
    ASSERT(t.kind == TOKEN_STAR, "*");
    ASSERT(t.loc.line == 3, "* on line 3");
}

/* ── Peek ── */
static void test_peek(void) {
    Lexer l;
    lexer_init(&l, "42 hello", "test");

    Token p = lexer_peek(&l);
    ASSERT(p.kind == TOKEN_INT, "peek int");
    ASSERT(strncmp(p.start, "42", p.length) == 0, "peek 42");

    /* second peek should return same token */
    p = lexer_peek(&l);
    ASSERT(p.kind == TOKEN_INT, "peek again same");

    /* next should also be 42 */
    Token n = lexer_next(&l);
    ASSERT(n.kind == TOKEN_INT, "next after peek");

    /* now peek the next one */
    p = lexer_peek(&l);
    ASSERT(p.kind == TOKEN_IDENT, "peek ident");
    ASSERT(strncmp(p.start, "hello", p.length) == 0, "peek hello");

    n = lexer_next(&l);
    ASSERT(n.kind == TOKEN_IDENT, "next ident");
    ASSERT(strncmp(n.start, "hello", n.length) == 0, "next hello");

    ASSERT(next_kind(&l) == TOKEN_EOF, "EOF");
}

/* ── Token kind name ── */
static void test_token_kind_name(void) {
    ASSERT(strcmp(token_kind_name(TOKEN_FN), "fn") == 0, "name of fn");
    ASSERT(strcmp(token_kind_name(TOKEN_EOF), "EOF") == 0, "name of EOF");
    ASSERT(strcmp(token_kind_name(TOKEN_ERROR), "ERROR") == 0, "name of ERROR");
}

/* ── Bitwise operators ── */
static void test_bitwise_operators(void) {
    Lexer l;
    lexer_init(&l, "& | ~ ^ << >>", "test");
    ASSERT(next_kind(&l) == TOKEN_AMP,   "&");
    ASSERT(next_kind(&l) == TOKEN_PIPE,  "|");
    ASSERT(next_kind(&l) == TOKEN_TILDE, "~");
    ASSERT(next_kind(&l) == TOKEN_CARET, "^");
    ASSERT(next_kind(&l) == TOKEN_LTLT,  "<<");
    ASSERT(next_kind(&l) == TOKEN_GTGT,  ">>");
    ASSERT(next_kind(&l) == TOKEN_EOF,   "EOF");
}

/* ── Expression snippet ── */
static void test_expression(void) {
    Lexer l;
    lexer_init(&l, "let x = foo(a + b, c) * 2;\n", "test");

    ASSERT(next_kind(&l) == TOKEN_LET,      "let");
    Token ident = lexer_next(&l);
    ASSERT(ident.kind == TOKEN_IDENT,        "x");
    ASSERT(strncmp(ident.start, "x", 1) == 0, "x text");
    ASSERT(next_kind(&l) == TOKEN_EQ,        "=");
    ident = lexer_next(&l);
    ASSERT(ident.kind == TOKEN_IDENT,        "foo");
    ASSERT(strncmp(ident.start, "foo", 3) == 0, "foo text");
    ASSERT(next_kind(&l) == TOKEN_LPAREN,    "(");
    ident = lexer_next(&l);
    ASSERT(ident.kind == TOKEN_IDENT,        "a");
    ASSERT(next_kind(&l) == TOKEN_PLUS,      "+");
    ident = lexer_next(&l);
    ASSERT(ident.kind == TOKEN_IDENT,        "b");
    ASSERT(next_kind(&l) == TOKEN_COMMA,     ",");
    ident = lexer_next(&l);
    ASSERT(ident.kind == TOKEN_IDENT,        "c");
    ASSERT(next_kind(&l) == TOKEN_RPAREN,    ")");
    ASSERT(next_kind(&l) == TOKEN_STAR,      "*");
    Token num = lexer_next(&l);
    ASSERT(num.kind == TOKEN_INT,            "2");
    ASSERT(strncmp(num.start, "2", 1) == 0,  "2 text");
    ASSERT(next_kind(&l) == TOKEN_SEMICOLON, ";");
    ASSERT(next_kind(&l) == TOKEN_EOF,       "EOF");
}

/* ── Main ── */
int main(void) {
    printf("=== Lexer Unit Tests ===\n\n");

    test_single_char_tokens();
    test_double_char_tokens();
    test_brackets();
    test_integers();
    test_floats();
    test_keywords();
    test_identifiers();
    test_strings();
    test_chars();
    test_line_comment();
    test_block_comment();
    test_nested_block_comment();
    test_locations();
    test_peek();
    test_token_kind_name();
    test_bitwise_operators();
    test_expression();

    printf("\nResults: %d passed, %d failed\n", passed, failed);
    return failed > 0 ? 1 : 0;
}
