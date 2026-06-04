#include "lexer.h"
#include <string.h>   /* strncmp */
#include <ctype.h>    /* isdigit, isalpha, isspace */
#include <stdlib.h>   /* strtoll, strtod */

/* ── keywords table ── */
typedef struct {
    const char *name;
    TokenKind kind;
} Keyword;

static const Keyword keywords[] = {
    {"fn",      TOKEN_FN},
    {"let",     TOKEN_LET},
    {"mut",     TOKEN_MUT},
    {"if",      TOKEN_IF},
    {"else",    TOKEN_ELSE},
    {"while",   TOKEN_WHILE},
    {"for",     TOKEN_FOR},
    {"in",      TOKEN_IN},
    {"match",   TOKEN_MATCH},
    {"return",  TOKEN_RETURN},
    {"type",    TOKEN_TYPE},
    {"struct",  TOKEN_STRUCT},
    {"enum",    TOKEN_ENUM},
    {"import",  TOKEN_IMPORT},
    {"extern",  TOKEN_EXTERN},
    {"as",      TOKEN_AS},
    {"sizeof",  TOKEN_SIZEOF},
    {"alignof", TOKEN_ALIGNOF},
    {"true",    TOKEN_BOOL},
    {"false",   TOKEN_BOOL},
};
#define NKEYWORDS (sizeof(keywords) / sizeof(keywords[0]))

/* ── helpers ── */

static char peek_char(Lexer *l) { return *l->current; }
static char next_char(Lexer *l) {
    char c = *l->current;
    if (c == '\0') return c;
    l->current++;
    if (c == '\n') { l->line++; l->col = 1; }
    else           { l->col++; }
    return c;
}

static int match_char(Lexer *l, char expected) {
    if (*l->current == expected) {
        l->current++;
        l->col++;
        return 1;
    }
    return 0;
}

static Token make_token(Lexer *l, TokenKind kind, const char *start, size_t len) {
    Token t;
    t.kind = kind;
    t.start = start;
    t.length = len;
    t.loc.filename = l->filename;
    t.loc.line = l->line;
    t.loc.col = l->col - (int)len;  /* column at start of token */
    return t;
}

static Token error_token(Lexer *l, const char *msg, size_t len) {
    Token t;
    t.kind = TOKEN_ERROR;
    t.start = msg;
    t.length = len;
    t.loc.filename = l->filename;
    t.loc.line = l->line;
    t.loc.col = l->col;
    return t;
}

/* ── skip whitespace and comments ── */

static void skip_line_comment(Lexer *l) {
    char c;
    while ((c = peek_char(l)) != '\0' && c != '\n')
        next_char(l);
}

static void skip_block_comment(Lexer *l) {
    int depth = 1;
    while (depth > 0) {
        char c = next_char(l);
        if (c == '\0') return;  /* unterminated comment */
        if (c == '/' && peek_char(l) == '*') { next_char(l); depth++; }
        if (c == '*' && peek_char(l) == '/') { next_char(l); depth--; }
    }
}

static void skip_whitespace(Lexer *l) {
    for (;;) {
        char c = peek_char(l);
        switch (c) {
        case ' ': case '\t': case '\r': case '\n':
            next_char(l);
            break;
        case '/':
            if (*(l->current + 1) == '/') {
                next_char(l); next_char(l);
                skip_line_comment(l);
            } else if (*(l->current + 1) == '*') {
                next_char(l); next_char(l);
                skip_block_comment(l);
            } else {
                return;
            }
            break;
        default:
            return;
        }
    }
}

/* ── number scanning ── */

static int is_hex_digit(int c) {
    return isdigit(c) || (c >= 'a' && c <= 'f') || (c >= 'A' && c <= 'F');
}

static int is_oct_digit(int c) {
    return c >= '0' && c <= '7';
}

static int is_bin_digit(int c) {
    return c == '0' || c == '1';
}

static Token scan_number(Lexer *l) {
    const char *start = l->current - 1; /* first digit already consumed by next_char */
    int base = 10;
    int is_float = 0;
    int (*digit_fn)(int) = isdigit;

    /* check radix prefix */
    if (*start == '0') {
        char c = peek_char(l);
        if (c == 'x' || c == 'X') {
            base = 16; digit_fn = is_hex_digit;
            next_char(l);
        } else if (c == 'o' || c == 'O') {
            base = 8; digit_fn = is_oct_digit;
            next_char(l);
        } else if (c == 'b' || c == 'B') {
            base = 2; digit_fn = is_bin_digit;
            next_char(l);
        }
    }

    /* scan digits */
    while (digit_fn(peek_char(l)))
        next_char(l);

    /* check for decimal fraction */
    if (base == 10 && peek_char(l) == '.' && digit_fn(*(l->current + 1))) {
        is_float = 1;
        next_char(l);  /* skip '.' */
        while (digit_fn(peek_char(l)))
            next_char(l);
    }

    if (is_float) return make_token(l, TOKEN_FLOAT, start, l->current - start);

    /* scan type suffix for integers: i8, i16, i32, i64, u8, u16, u32, u64 */
    /* the suffix is part of the token text but parsed later */
    if (peek_char(l) == 'i' || peek_char(l) == 'u') {
        next_char(l);  /* skip i or u */
        while (isdigit(peek_char(l)))
            next_char(l);
    }

    return make_token(l, TOKEN_INT, start, l->current - start);
}

/* ── string and char scanning ── */

static Token scan_string(Lexer *l) {
    const char *start = l->current - 1; /* opening " */
    for (;;) {
        char c = next_char(l);
        if (c == '\0')
            return error_token(l, "unterminated string literal", l->current - start);
        if (c == '"') break;  /* closing quote */
        if (c == '\\') {
            /* skip escape sequence */
            char e = peek_char(l);
            switch (e) {
            case 'n': case 't': case 'r': case '\\': case '"': case '0':
                next_char(l); break;
            case 'x':
                next_char(l);
                if (is_hex_digit(peek_char(l))) next_char(l);
                if (is_hex_digit(peek_char(l))) next_char(l);
                break;
            default: break; /* unknown escape, keep the backslash */
            }
        }
    }
    return make_token(l, TOKEN_STRING, start, l->current - start);
}

static Token scan_char(Lexer *l) {
    const char *start = l->current - 1; /* opening ' */
    char c = next_char(l);
    if (c == '\\') {
        /* handle escape */
        char e = peek_char(l);
        switch (e) {
        case 'n': case 't': case 'r': case '\\': case '\'': case '0':
            next_char(l); break;
        case 'x':
            next_char(l);
            if (is_hex_digit(peek_char(l))) next_char(l);
            if (is_hex_digit(peek_char(l))) next_char(l);
            break;
        default: break;
        }
    }
    char closing = next_char(l);
    if (closing != '\'')
        return error_token(l, "unterminated character literal", l->current - start);
    return make_token(l, TOKEN_CHAR, start, l->current - start);
}

/* ── identifier / keyword scanning ── */

static TokenKind lookup_keyword(const char *name, size_t len) {
    for (size_t i = 0; i < NKEYWORDS; i++) {
        if (strlen(keywords[i].name) == len &&
            strncmp(keywords[i].name, name, len) == 0)
            return keywords[i].kind;
    }
    return TOKEN_IDENT;
}

static Token scan_ident_or_keyword(Lexer *l) {
    const char *start = l->current - 1; /* first char already consumed */
    char c;
    while ((c = peek_char(l)) != '\0') {
        if (isalnum(c) || c == '_') { next_char(l); continue; }
        break;
    }
    size_t len = l->current - start;
    TokenKind kind = lookup_keyword(start, len);
    return make_token(l, kind, start, len);
}

/* ── public API ── */

void lexer_init(Lexer *l, const char *source, const char *filename) {
    l->source = source;
    l->current = source;
    l->filename = filename;
    l->line = 1;
    l->col = 1;
    l->has_peek = 0;
}

Token lexer_peek(Lexer *l) {
    if (!l->has_peek) {
        l->peek = lexer_next(l);
        l->has_peek = 1;
    }
    return l->peek;
}

Token lexer_next(Lexer *l) {
    /* return buffered peek if available */
    if (l->has_peek) {
        l->has_peek = 0;
        return l->peek;
    }

    skip_whitespace(l);

    const char *start = l->current;

    char c = next_char(l);

    switch (c) {
    case '\0': return make_token(l, TOKEN_EOF, start, 0);

    /* brackets */
    case '(': return make_token(l, TOKEN_LPAREN, start, 1);
    case ')': return make_token(l, TOKEN_RPAREN, start, 1);
    case '{': return make_token(l, TOKEN_LBRACE, start, 1);
    case '}': return make_token(l, TOKEN_RBRACE, start, 1);
    case '[': return make_token(l, TOKEN_LBRACKET, start, 1);
    case ']': return make_token(l, TOKEN_RBRACKET, start, 1);

    /* punctuation */
    case ',': return make_token(l, TOKEN_COMMA, start, 1);
    case ';': return make_token(l, TOKEN_SEMICOLON, start, 1);
    case ':': return make_token(l, TOKEN_COLON, start, 1);

    /* dot: ., .. */
    case '.':
        if (match_char(l, '.')) return make_token(l, TOKEN_DOTDOT, start, 2);
        return make_token(l, TOKEN_DOT, start, 1);

    /* +, += */
    case '+':
        if (match_char(l, '=')) return make_token(l, TOKEN_PLUSEQ, start, 2);
        return make_token(l, TOKEN_PLUS, start, 1);

    /* -, -=, -> */
    case '-':
        if (match_char(l, '=')) return make_token(l, TOKEN_MINUSEQ, start, 2);
        if (match_char(l, '>')) return make_token(l, TOKEN_ARROW, start, 2);
        return make_token(l, TOKEN_MINUS, start, 1);

    /* *, *= */
    case '*':
        if (match_char(l, '=')) return make_token(l, TOKEN_STAREQ, start, 2);
        return make_token(l, TOKEN_STAR, start, 1);

    /* /, /= */
    case '/':
        if (match_char(l, '=')) return make_token(l, TOKEN_SLASHEQ, start, 2);
        return make_token(l, TOKEN_SLASH, start, 1);

    /* %, %= */
    case '%':
        if (match_char(l, '=')) return make_token(l, TOKEN_PERCENTEQ, start, 2);
        return make_token(l, TOKEN_PERCENT, start, 1);

    /* =, == */
    case '=':
        if (match_char(l, '=')) return make_token(l, TOKEN_EQEQ, start, 2);
        if (match_char(l, '>')) return make_token(l, TOKEN_FATARROW, start, 2);
        return make_token(l, TOKEN_EQ, start, 1);

    /* !, != */
    case '!':
        if (match_char(l, '=')) return make_token(l, TOKEN_BANGEQ, start, 2);
        return make_token(l, TOKEN_BANG, start, 1);

    /* <, <=, << */
    case '<':
        if (match_char(l, '=')) return make_token(l, TOKEN_LTEQ, start, 2);
        if (match_char(l, '<')) return make_token(l, TOKEN_LTLT, start, 2);
        return make_token(l, TOKEN_LT, start, 1);

    /* >, >=, >> */
    case '>':
        if (match_char(l, '=')) return make_token(l, TOKEN_GTEQ, start, 2);
        if (match_char(l, '>')) return make_token(l, TOKEN_GTGT, start, 2);
        return make_token(l, TOKEN_GT, start, 1);

    /* &, && */
    case '&':
        if (match_char(l, '&')) return make_token(l, TOKEN_AMPAMP, start, 2);
        return make_token(l, TOKEN_AMP, start, 1);

    /* |, || */
    case '|':
        if (match_char(l, '|')) return make_token(l, TOKEN_PIPEPIPE, start, 2);
        return make_token(l, TOKEN_PIPE, start, 1);

    /* ~ */
    case '~': return make_token(l, TOKEN_TILDE, start, 1);

    /* ^ */
    case '^': return make_token(l, TOKEN_CARET, start, 1);

    /* number */
    case '0': case '1': case '2': case '3': case '4':
    case '5': case '6': case '7': case '8': case '9':
        return scan_number(l);

    /* string */
    case '"': return scan_string(l);

    /* char */
    case '\'': return scan_char(l);

    /* identifier or keyword */
    default:
        if (isalpha(c) || c == '_')
            return scan_ident_or_keyword(l);
        return error_token(l, "unexpected character", 1);
    }
}

/* ── token name for debugging ── */

const char *token_kind_name(TokenKind kind) {
    switch (kind) {
    case TOKEN_INT:       return "int";
    case TOKEN_FLOAT:     return "float";
    case TOKEN_STRING:    return "string";
    case TOKEN_CHAR:      return "char";
    case TOKEN_BOOL:      return "bool";
    case TOKEN_IDENT:     return "ident";
    case TOKEN_FN:        return "fn";
    case TOKEN_LET:       return "let";
    case TOKEN_MUT:       return "mut";
    case TOKEN_IF:        return "if";
    case TOKEN_ELSE:      return "else";
    case TOKEN_WHILE:     return "while";
    case TOKEN_FOR:       return "for";
    case TOKEN_IN:        return "in";
    case TOKEN_MATCH:     return "match";
    case TOKEN_RETURN:    return "return";
    case TOKEN_TYPE:      return "type";
    case TOKEN_STRUCT:    return "struct";
    case TOKEN_ENUM:      return "enum";
    case TOKEN_IMPORT:    return "import";
    case TOKEN_EXTERN:    return "extern";
    case TOKEN_AS:        return "as";
    case TOKEN_SIZEOF:    return "sizeof";
    case TOKEN_ALIGNOF:   return "alignof";
    case TOKEN_PLUS:      return "+";
    case TOKEN_MINUS:     return "-";
    case TOKEN_STAR:      return "*";
    case TOKEN_SLASH:     return "/";
    case TOKEN_PERCENT:   return "%";
    case TOKEN_EQ:        return "=";
    case TOKEN_EQEQ:      return "==";
    case TOKEN_BANGEQ:    return "!=";
    case TOKEN_LT:        return "<";
    case TOKEN_GT:        return ">";
    case TOKEN_LTEQ:      return "<=";
    case TOKEN_GTEQ:      return ">=";
    case TOKEN_BANG:      return "!";
    case TOKEN_AMP:       return "&";
    case TOKEN_AMPAMP:    return "&&";
    case TOKEN_PIPE:      return "|";
    case TOKEN_PIPEPIPE:  return "||";
    case TOKEN_TILDE:     return "~";
    case TOKEN_CARET:     return "^";
    case TOKEN_LTLT:      return "<<";
    case TOKEN_GTGT:      return ">>";
    case TOKEN_PLUSEQ:    return "+=";
    case TOKEN_MINUSEQ:   return "-=";
    case TOKEN_STAREQ:    return "*=";
    case TOKEN_SLASHEQ:   return "/=";
    case TOKEN_PERCENTEQ: return "%=";
    case TOKEN_LPAREN:    return "(";
    case TOKEN_RPAREN:    return ")";
    case TOKEN_LBRACE:    return "{";
    case TOKEN_RBRACE:    return "}";
    case TOKEN_LBRACKET:  return "[";
    case TOKEN_RBRACKET:  return "]";
    case TOKEN_DOT:       return ".";
    case TOKEN_DOTDOT:    return "..";
    case TOKEN_COMMA:     return ",";
    case TOKEN_SEMICOLON: return ";";
    case TOKEN_COLON:     return ":";
    case TOKEN_ARROW:     return "->";
    case TOKEN_FATARROW:  return "=>";
    case TOKEN_EOF:       return "EOF";
    case TOKEN_ERROR:     return "ERROR";
    default:              return "?";
    }
}
