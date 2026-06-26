#ifndef LEXER_H
#define LEXER_H

#include <stddef.h>

/* ── Token types ── */
typedef enum {
    /* literals */
    TOKEN_INT,
    TOKEN_FLOAT,
    TOKEN_STRING,
    TOKEN_CHAR,
    TOKEN_BOOL,

    /* identifier */
    TOKEN_IDENT,

    /* keywords */
    TOKEN_FN,
    TOKEN_LET,
    TOKEN_MUT,
    TOKEN_IF,
    TOKEN_ELSE,
    TOKEN_WHILE,
    TOKEN_FOR,
    TOKEN_IN,
    TOKEN_MATCH,
    TOKEN_RETURN,
    TOKEN_BREAK,
    TOKEN_CONTINUE,
    TOKEN_TYPE,
    TOKEN_STRUCT,
    TOKEN_ENUM,
    TOKEN_IMPORT,
    TOKEN_EXTERN,
    TOKEN_AS,
    TOKEN_SIZEOF,
    TOKEN_ALIGNOF,
    TOKEN_CONST,

    /* operators / punctuation */
    TOKEN_PLUS,        /* +  */
    TOKEN_MINUS,       /* -  */
    TOKEN_STAR,        /* *  */
    TOKEN_SLASH,       /* /  */
    TOKEN_PERCENT,     /* %  */
    TOKEN_EQ,          /* =  */
    TOKEN_EQEQ,        /* == */
    TOKEN_BANGEQ,      /* != */
    TOKEN_LT,          /* <  */
    TOKEN_GT,          /* >  */
    TOKEN_LTEQ,        /* <= */
    TOKEN_GTEQ,        /* >= */
    TOKEN_BANG,        /* !  */
    TOKEN_AMP,         /* &  */
    TOKEN_AMPAMP,      /* && */
    TOKEN_PIPE,        /* |  */
    TOKEN_PIPEPIPE,    /* || */
    TOKEN_TILDE,       /* ~  */
    TOKEN_CARET,       /* ^  */
    TOKEN_LTLT,        /* << */
    TOKEN_GTGT,        /* >> */
    TOKEN_PLUSEQ,      /* += */
    TOKEN_MINUSEQ,     /* -= */
    TOKEN_STAREQ,      /* *= */
    TOKEN_SLASHEQ,     /* /= */
    TOKEN_PERCENTEQ,   /* %= */

    /* brackets */
    TOKEN_LPAREN,      /* (  */
    TOKEN_RPAREN,      /* )  */
    TOKEN_LBRACE,      /* {  */
    TOKEN_RBRACE,      /* }  */
    TOKEN_LBRACKET,    /* [  */
    TOKEN_RBRACKET,    /* ]  */

    /* misc */
    TOKEN_DOT,         /* .  */
    TOKEN_DOTDOT,      /* .. */
    TOKEN_COMMA,       /* ,  */
    TOKEN_SEMICOLON,   /* ;  */
    TOKEN_COLON,       /* :  */
    TOKEN_COLONCOLON,  /* :: */
    TOKEN_ARROW,       /* -> */
    TOKEN_FATARROW,    /* => */

    TOKEN_EOF,
    TOKEN_ERROR,
} TokenKind;

/* ── Source location ── */
typedef struct {
    int line;
    int col;
    const char *filename;
} SourceLoc;

/* ── Token ── */
typedef struct {
    TokenKind kind;
    const char *start;    /* pointer into source */
    size_t length;        /* length of token text */
    SourceLoc loc;
} Token;

/* ── Lexer ── */
typedef struct {
    const char *source;   /* entire source string */
    const char *current;  /* current scan position */
    const char *filename;
    int line;
    int col;
    /* 1-token lookahead */
    Token peek;
    int has_peek;
} Lexer;

void  lexer_init(Lexer *l, const char *source, const char *filename);
Token lexer_next(Lexer *l);
Token lexer_peek(Lexer *l);
const char *token_kind_name(TokenKind kind);

#endif
