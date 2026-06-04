#ifndef PARSER_H
#define PARSER_H

#include "lexer.h"
#include "ast.h"
#include "arena.h"

/* ── Precedence levels for Pratt parsing ── */
typedef enum {
    PREC_NONE,
    PREC_ASSIGN,    /* = += -= *= /= %= */
    PREC_OR,        /* || */
    PREC_AND,       /* && */
    PREC_COMPARE,   /* == != < > <= >= */
    PREC_BIT_OR,    /* | */
    PREC_BIT_XOR,   /* ^ */
    PREC_BIT_AND,   /* & */
    PREC_SHIFT,     /* << >> */
    PREC_TERM,      /* + - */
    PREC_FACTOR,    /* * / % */
    PREC_UNARY,     /* -expr !expr ~expr *expr &expr */
    PREC_PRIMARY,
} Precedence;

/* ── Parse rule for Pratt parser ── */
struct Parser;

typedef Node *(*PrefixFn)(struct Parser *p, Token token);
typedef Node *(*InfixFn)(struct Parser *p, Token token, Node *left);

typedef struct {
    TokenKind  kind;
    Precedence prec;
    PrefixFn   prefix;
    InfixFn    infix;
} ParseRule;

/* ── Parser state ── */
typedef struct Parser {
    Lexer    *lexer;
    Arena    *arena;
    Token     prev;           /* last consumed token */
    SymTable *global_scope;
    SymTable *current_scope;
    int       scope_depth;
    int       error_count;
    ParseRule rules[128];
} Parser;

void parser_init(Parser *p, Lexer *lexer, Arena *arena);
Node *parser_parse(Parser *p);

#endif
