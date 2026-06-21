#include "parser.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

/* ── helpers ── */
static Token peek(Parser *p) { return lexer_peek(p->lexer); }
static int check(Parser *p, TokenKind k) { return peek(p).kind == k; }
static Token advance(Parser *p) { return p->prev = lexer_next(p->lexer); }
static int match(Parser *p, TokenKind k) {
    if (check(p, k)) { advance(p); return 1; }
    return 0;
}
static Token expect(Parser *p, TokenKind k, const char *what) {
    if (check(p, k)) return advance(p);
    Token t = peek(p);
    fprintf(stderr, "%s:%d:%d: error: expected %s, got %s\n",
            t.loc.filename, t.loc.line, t.loc.col, what, token_kind_name(t.kind));
    p->error_count++;
    return t;
}

/* ── forward declarations ── */
static Node *parse_expr(Parser *p, Precedence prec);
static Node *parse_stmt(Parser *p);
static Node *parse_decl(Parser *p);
static Node *parse_type(Parser *p);
static Node *parse_pattern(Parser *p);

/* ── scope ── */
static void push_scope(Parser *p) {
    p->current_scope = symtab_new(p->arena, p->current_scope);
    p->scope_depth++;
}
static void pop_scope(Parser *p) {
    if (p->current_scope && p->current_scope->parent)
        p->current_scope = p->current_scope->parent;
    p->scope_depth--;
}

/* ── get a local name string from token ── */
static const char *tok_name(Parser *p, Token t) {
    return arena_strdup(p->arena, t.start, t.length);
}

/* ══════════════════════════════════════════════
   TYPE PARSING
   ══════════════════════════════════════════════ */

static Node *parse_type(Parser *p) {
    Node *base = NULL;

    if (match(p, TOKEN_STAR)) {
        /* pointer type: *T */
        base = parse_type(p);
        /* represent as a type node — for now just return a placeholder */
        /* We'll resolve to Type* in sema */
        /* For parser, we use a special unary form to represent *T */
        Node *inner = base;
        return ast_new_unary(p->arena, p->prev.loc, TOKEN_STAR, inner);
    }

    if (match(p, TOKEN_LBRACKET)) {
        if (match(p, TOKEN_STAR)) {
            /* [*]T — slice type */
            expect(p, TOKEN_RBRACKET, "] after [*");
            Node *elem = parse_type(p);
            return ast_new_slice_type(p->arena, p->prev.loc, elem);
        }
        /* [T; N] — array type */
        base = parse_type(p);
        expect(p, TOKEN_SEMICOLON, "; in array type");
        Node *count_expr = parse_expr(p, PREC_PRIMARY); /* count */
        expect(p, TOKEN_RBRACKET, "] in array type");
        return ast_new_array_type(p->arena, p->prev.loc, base, count_expr);
    }

    if (match(p, TOKEN_FN)) {
        /* fn type: fn(T1, T2) -> Ret (simplified for now) */
        expect(p, TOKEN_LPAREN, "( in fn type");
        /* skip params for now */
        /* ... */
        return ast_new_int(p->arena, p->prev.loc, 0, PRIM_I32); /* placeholder */
    }

    /* named type: ident [::ident] */
    Token t = expect(p, TOKEN_IDENT, "type name");
    const char *name = tok_name(p, t);
    /* look up or create symbol */
    Sym *sym = symtab_lookup(p->current_scope, name);
    if (!sym) {
        sym = symtab_insert(p->current_scope, name, SYM_TYPE, NULL, false, p->scope_depth);
    }
    base = ast_new_ident(p->arena, t.loc, sym);

    /* possibly nested like std::module::Type */
    while (match(p, TOKEN_COLON) && match(p, TOKEN_COLON)) {
        t = expect(p, TOKEN_IDENT, "type name after ::");
        name = tok_name(p, t);
        sym = symtab_lookup(p->current_scope, name);
        if (!sym)
            sym = symtab_insert(p->current_scope, name, SYM_TYPE, NULL, false, p->scope_depth);
        base = ast_new_ident(p->arena, t.loc, sym);
    }

    return base;
}

/* ══════════════════════════════════════════════
   PATTERN PARSING
   ══════════════════════════════════════════════ */

static Node *parse_pattern(Parser *p) {
    Token t = peek(p);

    switch (t.kind) {
    case TOKEN_IDENT: {
        /* check for wildcard _ first */
        if (t.length == 1 && *t.start == '_') {
            advance(p);
            return ast_new_pattern_wild(p->arena, t.loc);
        }
        /* else: identifier pattern, Enum::Variant, or range */
        advance(p);
        if (match(p, TOKEN_COLON) && match(p, TOKEN_COLON)) {
            Token vt = expect(p, TOKEN_IDENT, "variant name");
            const char *tname = tok_name(p, t);
            const char *vname = tok_name(p, vt);
            Sym *tsym = symtab_lookup(p->current_scope, tname);
            Sym *vsym = symtab_lookup(p->current_scope, vname);
            Node *inner = NULL;
            if (check(p, TOKEN_LPAREN)) {
                advance(p);
                inner = parse_pattern(p);
                expect(p, TOKEN_RPAREN, ") after enum pattern");
            }
            return ast_new_pattern_enum(p->arena, t.loc, tsym, vsym, inner);
        }
        if (match(p, TOKEN_DOTDOT)) {
            Node *hi = parse_expr(p, PREC_PRIMARY);
            const char *name = tok_name(p, t);
            Sym *sym = symtab_lookup(p->current_scope, name);
            if (!sym) sym = symtab_insert(p->current_scope, name, SYM_VAR, NULL, false, p->scope_depth);
            Node *lo = ast_new_pattern_ident(p->arena, t.loc, sym);
            return ast_new_pattern_range(p->arena, t.loc, lo, hi);
        }
        const char *name = tok_name(p, t);
        Sym *sym = symtab_lookup(p->current_scope, name);
        if (!sym) sym = symtab_insert(p->current_scope, name, SYM_VAR, NULL, false, p->scope_depth);
        return ast_new_pattern_ident(p->arena, t.loc, sym);
    }

    case TOKEN_STAR:
        goto default_case;

    case TOKEN_INT: {
        advance(p);
        int64_t val = strtoll(t.start, NULL, 0);
        return ast_new_pattern_lit(p->arena, t.loc, val, PRIM_I32);
    }
    case TOKEN_BOOL: {
        advance(p);
        bool val = (t.length == 4 && strncmp(t.start, "true", 4) == 0);
        return ast_new_pattern_lit(p->arena, t.loc, val ? 1 : 0, PRIM_BOOL);
    }
    case TOKEN_CHAR: {
        advance(p);
        return ast_new_pattern_lit(p->arena, t.loc, (unsigned char)t.start[1], PRIM_U8);
    }
    case TOKEN_MINUS: {
        advance(p);
        Token n = expect(p, TOKEN_INT, "integer after - in pattern");
        int64_t val = -strtoll(n.start, NULL, 0);
        return ast_new_pattern_lit(p->arena, t.loc, val, PRIM_I32);
    }
    default:
    default_case:
        fprintf(stderr, "%s:%d:%d: error: unexpected token '%s' in pattern\n",
                t.loc.filename, t.loc.line, t.loc.col, token_kind_name(t.kind));
        p->error_count++;
        advance(p);
        return NULL;
    }
}

/* ══════════════════════════════════════════════
   STATEMENT PARSING
   ══════════════════════════════════════════════ */

static Node *parse_block(Parser *p) {
    SourceLoc loc = peek(p).loc;
    expect(p, TOKEN_LBRACE, "{");
    push_scope(p);

    Node **stmts = NULL;
    size_t nstmts = 0;
    size_t cap = 0;

    while (!check(p, TOKEN_RBRACE) && !check(p, TOKEN_EOF)) {
        Node *stmt = parse_stmt(p);
        if (stmt) {
            if (nstmts >= cap) {
                cap = cap ? cap * 2 : 8;
                Node **new_stmts = arena_alloc(p->arena, cap * sizeof(Node *));
                if (stmts && nstmts > 0)
                    memcpy(new_stmts, stmts, nstmts * sizeof(Node *));
                stmts = new_stmts;
            }
            stmts[nstmts++] = stmt;
        }
    }

    expect(p, TOKEN_RBRACE, "}");
    pop_scope(p);
    return ast_new_block(p->arena, loc, stmts, nstmts);
}

static Node *parse_let(Parser *p) {
    SourceLoc loc = peek(p).loc;
    advance(p); /* consume 'let' */

    bool is_mut = match(p, TOKEN_MUT);

    Token name = expect(p, TOKEN_IDENT, "variable name");
    const char *vname = tok_name(p, name);

    /* optional type annotation */
    Node *type_annot = NULL;
    if (match(p, TOKEN_COLON)) {
        type_annot = parse_type(p);
    }

    expect(p, TOKEN_EQ, "=");
    Node *init = parse_expr(p, PREC_NONE);
    expect(p, TOKEN_SEMICOLON, ";");

    Sym *sym = symtab_insert(p->current_scope, vname, SYM_VAR, NULL, is_mut, p->scope_depth);
    return ast_new_let(p->arena, loc, is_mut, sym, type_annot, init);
}

static Node *parse_if(Parser *p) {
    SourceLoc loc = peek(p).loc;
    advance(p); /* consume 'if' */

    Node *cond = parse_expr(p, PREC_NONE);
    Node *then_body = parse_block(p);
    Node *else_body = NULL;

    if (match(p, TOKEN_ELSE)) {
        if (check(p, TOKEN_IF)) {
            else_body = parse_if(p);
        } else {
            else_body = parse_block(p);
        }
    }

    return ast_new_if(p->arena, loc, cond, then_body, else_body);
}

static Node *parse_while(Parser *p) {
    SourceLoc loc = peek(p).loc;
    advance(p); /* consume 'while' */

    Node *cond = parse_expr(p, PREC_NONE);
    Node *body = parse_block(p);

    return ast_new_while(p->arena, loc, cond, body);
}

static Node *parse_for(Parser *p) {
    SourceLoc loc = peek(p).loc;
    advance(p); /* consume 'for' */

    Token var = expect(p, TOKEN_IDENT, "loop variable");
    const char *vname = tok_name(p, var);

    expect(p, TOKEN_IN, "in");

    Node *start = parse_expr(p, PREC_NONE);
    expect(p, TOKEN_DOTDOT, "..");
    Node *end = parse_expr(p, PREC_NONE);

    push_scope(p);
    Sym *sym = symtab_insert(p->current_scope, vname, SYM_VAR, NULL, false, p->scope_depth);
    Node *body = parse_block(p);
    pop_scope(p);

    return ast_new_for(p->arena, loc, sym, start, end, body);
}

static Node *parse_match(Parser *p) {
    SourceLoc loc = peek(p).loc;
    advance(p); /* consume 'match' */

    Node *expr = parse_expr(p, PREC_NONE);
    expect(p, TOKEN_LBRACE, "{");

    Node **arms = NULL;
    size_t narms = 0, cap = 0;

    while (!check(p, TOKEN_RBRACE) && !check(p, TOKEN_EOF)) {
        Node *pat = parse_pattern(p);
        expect(p, TOKEN_FATARROW, "=>");
        Node *body = parse_expr(p, PREC_NONE);
        if (check(p, TOKEN_COMMA)) advance(p);

        Node *arm = ast_new_match_arm(p->arena, loc, pat, body);
        if (narms >= cap) {
            cap = cap ? cap * 2 : 8;
            Node **new_arms = arena_alloc(p->arena, cap * sizeof(Node *));
            if (arms && narms > 0) memcpy(new_arms, arms, narms * sizeof(Node *));
            arms = new_arms;
        }
        arms[narms++] = arm;
    }

    expect(p, TOKEN_RBRACE, "}");
    return ast_new_match(p->arena, loc, expr, arms, narms);
}

static Node *parse_return(Parser *p) {
    SourceLoc loc = peek(p).loc;
    advance(p); /* consume 'return' */

    Node *expr = NULL;
    if (!check(p, TOKEN_SEMICOLON) && !check(p, TOKEN_RBRACE)) {
        expr = parse_expr(p, PREC_NONE);
    }
    expect(p, TOKEN_SEMICOLON, ";");

    return ast_new_return(p->arena, loc, expr);
}

static Node *parse_break(Parser *p) {
    SourceLoc loc = peek(p).loc;
    advance(p); /* consume 'break' */
    expect(p, TOKEN_SEMICOLON, ";");
    return ast_new_break(p->arena, loc);
}

static Node *parse_continue(Parser *p) {
    SourceLoc loc = peek(p).loc;
    advance(p); /* consume 'continue' */
    expect(p, TOKEN_SEMICOLON, ";");
    return ast_new_continue(p->arena, loc);
}

static Node *parse_expr_stmt(Parser *p) {
    Node *expr = parse_expr(p, PREC_NONE);
    /* allow omitting ; before } (expression as last statement in block) */
    if (!check(p, TOKEN_RBRACE) && !check(p, TOKEN_EOF))
        expect(p, TOKEN_SEMICOLON, ";");
    return expr ? ast_new_expr_stmt(p->arena, expr->loc, expr) : NULL;
}

static Node *parse_stmt(Parser *p) {
    if (check(p, TOKEN_LET))      return parse_let(p);
    if (check(p, TOKEN_IF))       return parse_if(p);
    if (check(p, TOKEN_WHILE))    return parse_while(p);
    if (check(p, TOKEN_FOR))      return parse_for(p);
    if (check(p, TOKEN_MATCH))    return parse_match(p);
    if (check(p, TOKEN_RETURN))   return parse_return(p);
    if (check(p, TOKEN_BREAK))    return parse_break(p);
    if (check(p, TOKEN_CONTINUE)) return parse_continue(p);
    if (check(p, TOKEN_LBRACE))   return parse_block(p);
    return parse_expr_stmt(p);
}

/* ══════════════════════════════════════════════
   DECLARATION PARSING
   ══════════════════════════════════════════════ */

static Node *parse_func(Parser *p, bool is_extern) {
    SourceLoc loc = peek(p).loc;
    advance(p); /* consume 'fn' */

    Token name = expect(p, TOKEN_IDENT, "function name");
    const char *fname = tok_name(p, name);

    /* Register function in global scope BEFORE parsing body so recursive calls work */
    Sym *sym = symtab_insert(p->global_scope, fname, SYM_FN, NULL, false, 0);
    if (is_extern && sym) sym->is_extern = true;

    push_scope(p);

    /* parameter list */
    expect(p, TOKEN_LPAREN, "(");
    NodeFuncDeclParam *params = NULL;
    size_t nparams = 0, pcap = 0;

    while (!check(p, TOKEN_RPAREN) && !check(p, TOKEN_EOF)) {
        Token pname = expect(p, TOKEN_IDENT, "parameter name");
        expect(p, TOKEN_COLON, ":");
        Node *ptype = parse_type(p);

        Sym *psym = symtab_insert(p->current_scope,
                                   tok_name(p, pname), SYM_VAR, NULL, false, p->scope_depth);

        if (nparams >= pcap) {
            pcap = pcap ? pcap * 2 : 4;
            NodeFuncDeclParam *np = arena_alloc(p->arena, pcap * sizeof(NodeFuncDeclParam));
            if (params && nparams > 0) memcpy(np, params, nparams * sizeof(NodeFuncDeclParam));
            params = np;
        }
        params[nparams].sym = psym;
        params[nparams].type_annot = ptype;
        nparams++;

        if (!match(p, TOKEN_COMMA)) break;
    }
    expect(p, TOKEN_RPAREN, ")");

    /* return type */
    Node *ret_type = NULL;
    if (match(p, TOKEN_ARROW)) {
        ret_type = parse_type(p);
    }

    /* body */
    Node *body;
    if (is_extern) {
        expect(p, TOKEN_SEMICOLON, ";");
        body = NULL;
    } else {
        body = parse_block(p);
    }

    pop_scope(p);

    return ast_new_func_decl(p->arena, loc, sym, params, nparams, ret_type, body, is_extern);
}

static Node *parse_type_decl(Parser *p) {
    SourceLoc loc = peek(p).loc;
    advance(p); /* consume 'type' */

    Token name = expect(p, TOKEN_IDENT, "type name");
    const char *tname = tok_name(p, name);
    expect(p, TOKEN_EQ, "=");

    Node *body = NULL;

    if (match(p, TOKEN_STRUCT)) {
        /* type Name = struct { ... } */
        SourceLoc body_loc = p->prev.loc;
        expect(p, TOKEN_LBRACE, "{");

        StructFieldDecl *fields = NULL;
        size_t nfields = 0, fcap = 0;

        while (!check(p, TOKEN_RBRACE) && !check(p, TOKEN_EOF)) {
            Token fname = expect(p, TOKEN_IDENT, "field name");
            expect(p, TOKEN_COLON, ":");
            Node *ftype = parse_type(p);

            if (nfields >= fcap) {
                fcap = fcap ? fcap * 2 : 8;
                StructFieldDecl *nf = arena_alloc(p->arena, fcap * sizeof(StructFieldDecl));
                if (fields && nfields > 0) memcpy(nf, fields, nfields * sizeof(StructFieldDecl));
                fields = nf;
            }
            fields[nfields].name = tok_name(p, fname);
            fields[nfields].type_annot = ftype;
            nfields++;

            if (!match(p, TOKEN_COMMA)) break;
        }

        expect(p, TOKEN_RBRACE, "}");
        body = ast_new_struct_def(p->arena, body_loc, fields, nfields);
    } else if (match(p, TOKEN_ENUM)) {
        /* type Name = enum { ... } */
        SourceLoc body_loc = p->prev.loc;
        expect(p, TOKEN_LBRACE, "{");

        EnumVariantDecl *variants = NULL;
        size_t nvariants = 0, vcap = 0;

        while (!check(p, TOKEN_RBRACE) && !check(p, TOKEN_EOF)) {
            Token vname = expect(p, TOKEN_IDENT, "variant name");
            Node *payload_type = NULL;

            /* optional payload: Variant(Type) */
            if (match(p, TOKEN_LPAREN)) {
                payload_type = parse_type(p);
                expect(p, TOKEN_RPAREN, ")");
            }

            if (nvariants >= vcap) {
                vcap = vcap ? vcap * 2 : 8;
                EnumVariantDecl *nv = arena_alloc(p->arena, vcap * sizeof(EnumVariantDecl));
                if (variants && nvariants > 0) memcpy(nv, variants, nvariants * sizeof(EnumVariantDecl));
                variants = nv;
            }
            variants[nvariants].name = tok_name(p, vname);
            variants[nvariants].payload_type = payload_type;
            nvariants++;

            if (!match(p, TOKEN_COMMA)) break;
        }

        expect(p, TOKEN_RBRACE, "}");
        body = ast_new_enum_def(p->arena, body_loc, variants, nvariants);
    } else {
        /* type alias: type Name = OtherType */
        Node *alias_type = parse_type(p);
        body = alias_type;
    }

    Sym *sym = symtab_insert(p->global_scope, tname, SYM_TYPE, NULL, false, 0);
    return ast_new_type_decl(p->arena, loc, sym, body);
}

static Node *parse_extern_decl(Parser *p) {
    advance(p); /* consume 'extern' */
    return parse_func(p, true);
}

static Node *parse_import_decl(Parser *p) {
    SourceLoc loc = peek(p).loc;
    advance(p); /* consume 'import' */

    Token name = expect(p, TOKEN_IDENT, "module name");
    expect(p, TOKEN_SEMICOLON, ";");

    Sym *sym = symtab_insert(p->global_scope, tok_name(p, name), SYM_MODULE, NULL, false, 0);
    return ast_new_import_decl(p->arena, loc, sym);
}

static Node *parse_decl(Parser *p) {
    if (check(p, TOKEN_FN))     return parse_func(p, false);
    if (check(p, TOKEN_TYPE))   return parse_type_decl(p);
    if (check(p, TOKEN_EXTERN)) return parse_extern_decl(p);
    if (check(p, TOKEN_IMPORT)) return parse_import_decl(p);
    /* unknown at top level: try as statement */
    return parse_stmt(p);
}

/* ══════════════════════════════════════════════
   PRATT EXPRESSION PARSING
   ══════════════════════════════════════════════ */

static Node *parse_expr(Parser *p, Precedence min_prec) {
    /* handle expression-oriented statements inline */
    if (check(p, TOKEN_IF))      return parse_if(p);
    if (check(p, TOKEN_MATCH))   return parse_match(p);
    if (check(p, TOKEN_WHILE))   return parse_while(p);
    if (check(p, TOKEN_FOR))     return parse_for(p);
    if (check(p, TOKEN_LBRACE))  return parse_block(p);

    Token t = peek(p);

    ParseRule *rule = &p->rules[t.kind];
    if (!rule->prefix) {
        fprintf(stderr, "%s:%d:%d: error: unexpected token '%s' in expression\n",
                t.loc.filename, t.loc.line, t.loc.col, token_kind_name(t.kind));
        p->error_count++;
        advance(p);
        return NULL;
    }

    advance(p);
    Node *left = rule->prefix(p, p->prev);

    for (;;) {
        t = peek(p);
        /* stop conditions */
        switch (t.kind) {
        case TOKEN_EOF: case TOKEN_SEMICOLON: case TOKEN_RBRACE:
        case TOKEN_RPAREN: case TOKEN_RBRACKET: case TOKEN_COMMA:
        case TOKEN_COLON: case TOKEN_FATARROW: case TOKEN_IN:
        case TOKEN_ELSE:
            return left;
        default: break;
        }

        ParseRule *next = &p->rules[t.kind];
        if (!next->infix || next->prec < min_prec) return left;

        advance(p);
        left = next->infix(p, p->prev, left);
    }
}

/* ── Prefix functions ── */

static Node *prefix_int(Parser *p, Token token) {
    int64_t val = strtoll(token.start, NULL, 0);
    TypePrimitive prim = PRIM_I32;
    /* check suffix */
    for (size_t i = 0; i < token.length; i++) {
        if (token.start[i] == 'i' || token.start[i] == 'u') {
            const char *suf = token.start + i;
            char kind = *suf++;
            int bits = atoi(suf);
            if (kind == 'i') {
                switch (bits) { case 8: prim=PRIM_I8; break; case 16: prim=PRIM_I16; break; case 32: prim=PRIM_I32; break; case 64: prim=PRIM_I64; break; }
            } else {
                switch (bits) { case 8: prim=PRIM_U8; break; case 16: prim=PRIM_U16; break; case 32: prim=PRIM_U32; break; case 64: prim=PRIM_U64; break; }
            }
            break;
        }
    }
    return ast_new_int(p->arena, token.loc, val, prim);
}

static Node *prefix_float(Parser *p, Token token) {
    char buf[64];
    size_t n = token.length < 63 ? token.length : 63;
    memcpy(buf, token.start, n); buf[n] = '\0';
    double val = atof(buf);
    return ast_new_float(p->arena, token.loc, val);
}

static Node *prefix_string(Parser *p, Token token) {
    /* token includes quotes; extract content */
    const char *chars = token.start + 1;
    size_t len = token.length - 2;
    return ast_new_string(p->arena, token.loc, chars, len);
}

static Node *prefix_char(Parser *p, Token token) {
    char ch = 0;
    if (token.start[1] == '\\') {
        switch (token.start[2]) {
        case 'n': ch = '\n'; break;
        case 't': ch = '\t'; break;
        case 'r': ch = '\r'; break;
        case '0': ch = '\0'; break;
        default:  ch = token.start[2]; break;
        }
    } else {
        ch = token.start[1];
    }
    return ast_new_char(p->arena, token.loc, ch);
}

static Node *prefix_bool(Parser *p, Token token) {
    bool val = (token.length == 4 && strncmp(token.start, "true", 4) == 0);
    return ast_new_bool(p->arena, token.loc, val);
}

static Node *prefix_ident(Parser *p, Token token) {
    const char *name = tok_name(p, token);
    Sym *sym = symtab_lookup(p->current_scope, name);
    if (!sym)
        sym = symtab_insert(p->current_scope, name, SYM_VAR, NULL, false, p->scope_depth);

    /* struct literal: TypeName { field: val, ... }
       Only when the identifier is a known type name (SYM_TYPE) */
    if (sym->kind == SYM_TYPE && check(p, TOKEN_LBRACE)) {
        SourceLoc loc = token.loc;
        advance(p); /* consume { */

        NodeFieldInit *fields = NULL;
        size_t nfields = 0, fcap = 0;

        while (!check(p, TOKEN_RBRACE) && !check(p, TOKEN_EOF)) {
            Token fname = expect(p, TOKEN_IDENT, "field name");
            expect(p, TOKEN_COLON, ":");
            Node *fval = parse_expr(p, PREC_NONE);

            if (nfields >= fcap) {
                fcap = fcap ? fcap * 2 : 8;
                NodeFieldInit *nf = arena_alloc(p->arena, fcap * sizeof(NodeFieldInit));
                if (fields && nfields > 0) memcpy(nf, fields, nfields * sizeof(NodeFieldInit));
                fields = nf;
            }
            fields[nfields].name = tok_name(p, fname);
            fields[nfields].value = fval;
            nfields++;

            if (!match(p, TOKEN_COMMA)) break;
        }

        expect(p, TOKEN_RBRACE, "}");
        return ast_new_struct_lit(p->arena, loc, sym, fields, nfields);
    }

    /* enum variant construction: TypeName::Variant(args)
       Only when the identifier is a known type name (SYM_TYPE) */
    if (sym->kind == SYM_TYPE && match(p, TOKEN_COLONCOLON)) {
        SourceLoc loc = token.loc;
        Token vt = expect(p, TOKEN_IDENT, "variant name");
        const char *vname = tok_name(p, vt);
        Sym *vsym = symtab_lookup(p->current_scope, vname);
        if (!vsym)
            vsym = symtab_insert(p->current_scope, vname, SYM_VARIANT, NULL, false, p->scope_depth);

        Node *payload = NULL;
        if (check(p, TOKEN_LPAREN)) {
            advance(p);
            payload = parse_expr(p, PREC_NONE);
            expect(p, TOKEN_RPAREN, ")");
        }

        return ast_new_enum_variant(p->arena, loc, sym, vsym, payload);
    }

    /* qualified call: mod::name(args)
       When IDENT is an imported module (SYM_MODULE), followed by :: */
    if (sym->kind == SYM_MODULE && match(p, TOKEN_COLONCOLON)) {
        SourceLoc loc = token.loc;
        Token fn_tok = expect(p, TOKEN_IDENT, "function name after '::'");
        const char *fn_name = tok_name(p, fn_tok);
        /* Create placeholder sym; sema resolves to actual function in module's namespace */
        Sym *fn_sym = symtab_lookup(p->current_scope, fn_name);
        if (!fn_sym)
            fn_sym = symtab_insert(p->current_scope, fn_name, SYM_FN, NULL, false, 0);

        /* Parse (args...) */
        Node **args = NULL;
        size_t nargs = 0, cap = 0;
        expect(p, TOKEN_LPAREN, "(");
        if (!check(p, TOKEN_RPAREN)) {
            do {
                Node *arg = parse_expr(p, PREC_NONE);
                if (nargs >= cap) {
                    cap = cap ? cap * 2 : 8;
                    Node **na = arena_alloc(p->arena, cap * sizeof(Node *));
                    if (args && nargs > 0) memcpy(na, args, nargs * sizeof(Node *));
                    args = na;
                }
                args[nargs++] = arg;
            } while (match(p, TOKEN_COMMA));
        }
        expect(p, TOKEN_RPAREN, ")");

        /* Module node is the SYM_MODULE itself; function node is IDENT */
        Node *mod_node = ast_new_ident(p->arena, loc, sym);
        Node *fn_node = ast_new_ident(p->arena, fn_tok.loc, fn_sym);
        return ast_new_qualified_call(p->arena, loc, mod_node, fn_node, args, nargs);
    }

    return ast_new_ident(p->arena, token.loc, sym);
}

static Node *prefix_unary(Parser *p, Token token) {
    TokenKind op = token.kind;

    /* special case: * is both prefix (deref) and infix (multiply) */
    if (op == TOKEN_STAR) {
        Node *expr = parse_expr(p, PREC_UNARY);
        return ast_new_deref(p->arena, token.loc, expr);
    }
    /* special case: & is both prefix (addr-of) and infix (bit-and) */
    if (op == TOKEN_AMP) {
        /* slice literal: &[1, 2, 3] */
        if (check(p, TOKEN_LBRACKET)) {
            SourceLoc loc = token.loc;
            advance(p); /* consume [ */
            Node **elems = NULL;
            size_t nelems = 0, cap = 0;
            if (!check(p, TOKEN_RBRACKET)) {
                do {
                    Node *elem = parse_expr(p, PREC_NONE);
                    if (nelems >= cap) {
                        cap = cap ? cap * 2 : 8;
                        Node **ne = arena_alloc(p->arena, cap * sizeof(Node *));
                        if (elems && nelems > 0) memcpy(ne, elems, nelems * sizeof(Node *));
                        elems = ne;
                    }
                    elems[nelems++] = elem;
                } while (match(p, TOKEN_COMMA));
            }
            expect(p, TOKEN_RBRACKET, "] in slice literal");
            Node *arr = ast_new_array_lit(p->arena, loc, elems, nelems);
            return ast_new_slice_lit(p->arena, loc, arr);
        }
        Node *expr = parse_expr(p, PREC_UNARY);
        return ast_new_addr_of(p->arena, token.loc, expr);
    }

    Node *expr = parse_expr(p, PREC_UNARY);
    return ast_new_unary(p->arena, token.loc, op, expr);
}

static Node *prefix_paren(Parser *p, Token token) {
    /* check for unit type () */
    if (match(p, TOKEN_RPAREN)) {
        /* unit literal */
        return ast_new_int(p->arena, token.loc, 0, PRIM_I32); /* placeholder for unit */
    }
    Node *expr = parse_expr(p, PREC_NONE);
    expect(p, TOKEN_RPAREN, ")");
    return expr;
}

static Node *prefix_sizeof(Parser *p, Token token) {
    expect(p, TOKEN_LPAREN, "(");
    parse_type(p); /* target type */
    expect(p, TOKEN_RPAREN, ")");
    /* sema will resolve type */
    return ast_new_sizeof(p->arena, token.loc, NULL);
}

static Node *prefix_alignof(Parser *p, Token token) {
    expect(p, TOKEN_LPAREN, "(");
    parse_type(p); /* target type */
    expect(p, TOKEN_RPAREN, ")");
    return ast_new_alignof(p->arena, token.loc, NULL);
}

/* ── Infix functions ── */

static Node *infix_binary(Parser *p, Token token, Node *left) {
    TokenKind op = token.kind;
    ParseRule *rule = &p->rules[op];
    Node *right = parse_expr(p, (Precedence)(rule->prec + 1));
    return ast_new_binary(p->arena, token.loc, op, left, right);
}

static Node *infix_assign(Parser *p, Token token, Node *left) {
    TokenKind op = token.kind;
    Node *right = parse_expr(p, PREC_NONE);

    if (op == TOKEN_EQ) {
        return ast_new_assign(p->arena, token.loc, left, right);
    }

    /* compound: x += y → x = x + y */
    TokenKind binop;
    switch (op) {
    case TOKEN_PLUSEQ: binop = TOKEN_PLUS; break;
    case TOKEN_MINUSEQ:binop = TOKEN_MINUS; break;
    case TOKEN_STAREQ: binop = TOKEN_STAR; break;
    case TOKEN_SLASHEQ:binop = TOKEN_SLASH; break;
    case TOKEN_PERCENTEQ:binop=TOKEN_PERCENT; break;
    default: binop = op; break;
    }
    Node *bin = ast_new_binary(p->arena, token.loc, binop, left, right);
    return ast_new_assign(p->arena, token.loc, left, bin);
}

static Node *infix_call(Parser *p, Token token, Node *left) {
    Node **args = NULL;
    size_t nargs = 0, cap = 0;

    if (!check(p, TOKEN_RPAREN)) {
        do {
            Node *arg = parse_expr(p, PREC_NONE);
            if (nargs >= cap) {
                cap = cap ? cap * 2 : 8;
                Node **na = arena_alloc(p->arena, cap * sizeof(Node *));
                if (args && nargs > 0) memcpy(na, args, nargs * sizeof(Node *));
                args = na;
            }
            args[nargs++] = arg;
        } while (match(p, TOKEN_COMMA));
    }
    expect(p, TOKEN_RPAREN, ")");
    return ast_new_call(p->arena, token.loc, left, args, nargs);
}

static Node *infix_field(Parser *p, Token token, Node *left) {
    Token field = expect(p, TOKEN_IDENT, "field name");
    return ast_new_field(p->arena, token.loc, left, tok_name(p, field));
}

static Node *infix_index(Parser *p, Token token, Node *left) {
    SourceLoc loc = token.loc;
    Node *start = parse_expr(p, PREC_NONE);
    if (match(p, TOKEN_DOTDOT)) {
        Node *end = parse_expr(p, PREC_NONE);
        expect(p, TOKEN_RBRACKET, "]");
        return ast_new_slice_range(p->arena, loc, left, start, end);
    }
    expect(p, TOKEN_RBRACKET, "]");
    return ast_new_index(p->arena, loc, left, start);
}

static Node *infix_as(Parser *p, Token token, Node *left) {
    Node *target = parse_type(p); /* target type */
    return ast_new_cast(p->arena, token.loc, left, target); /* target resolved in sema */
}

/* ── array literal: [1, 2, 3] ── */
static Node *prefix_array_lit(Parser *p, Token token) {
    Node **elems = NULL;
    size_t nelems = 0, cap = 0;

    if (!check(p, TOKEN_RBRACKET)) {
        do {
            Node *elem = parse_expr(p, PREC_NONE);
            if (nelems >= cap) {
                cap = cap ? cap * 2 : 8;
                Node **ne = arena_alloc(p->arena, cap * sizeof(Node *));
                if (elems && nelems > 0) memcpy(ne, elems, nelems * sizeof(Node *));
                elems = ne;
            }
            elems[nelems++] = elem;
        } while (match(p, TOKEN_COMMA));
    }
    expect(p, TOKEN_RBRACKET, "]");
    return ast_new_array_lit(p->arena, token.loc, elems, nelems);
}

/* ══════════════════════════════════════════════
   INIT + TOP-LEVEL
   ══════════════════════════════════════════════ */

static void register_rule(Parser *p, TokenKind kind, Precedence prec, PrefixFn pre, InfixFn in) {
    p->rules[kind].kind = kind;
    p->rules[kind].prec = prec;
    p->rules[kind].prefix = pre;
    p->rules[kind].infix = in;
}

static void init_rules(Parser *p) {
    memset(p->rules, 0, sizeof(p->rules));

    register_rule(p, TOKEN_INT,    PREC_PRIMARY, prefix_int,    NULL);
    register_rule(p, TOKEN_FLOAT,  PREC_PRIMARY, prefix_float,  NULL);
    register_rule(p, TOKEN_STRING, PREC_PRIMARY, prefix_string, NULL);
    register_rule(p, TOKEN_CHAR,   PREC_PRIMARY, prefix_char,   NULL);
    register_rule(p, TOKEN_BOOL,   PREC_PRIMARY, prefix_bool,   NULL);
    register_rule(p, TOKEN_IDENT,  PREC_PRIMARY, prefix_ident,  NULL);
    register_rule(p, TOKEN_MINUS,  PREC_TERM,    prefix_unary,  infix_binary);
    register_rule(p, TOKEN_BANG,   PREC_UNARY,   prefix_unary,  NULL);
    register_rule(p, TOKEN_TILDE,  PREC_UNARY,   prefix_unary,  NULL);
    register_rule(p, TOKEN_STAR,   PREC_FACTOR,  prefix_unary,  infix_binary);
    register_rule(p, TOKEN_AMP,    PREC_BIT_AND, prefix_unary,  infix_binary);
    register_rule(p, TOKEN_LPAREN, PREC_PRIMARY, prefix_paren,  infix_call);
    register_rule(p, TOKEN_SIZEOF, PREC_PRIMARY, prefix_sizeof, NULL);
    register_rule(p, TOKEN_ALIGNOF,PREC_PRIMARY, prefix_alignof, NULL);
    register_rule(p, TOKEN_PLUS,   PREC_TERM,    NULL, infix_binary);
    register_rule(p, TOKEN_SLASH,  PREC_FACTOR,  NULL, infix_binary);
    register_rule(p, TOKEN_PERCENT,PREC_FACTOR,  NULL, infix_binary);
    register_rule(p, TOKEN_EQEQ,   PREC_COMPARE, NULL, infix_binary);
    register_rule(p, TOKEN_BANGEQ, PREC_COMPARE, NULL, infix_binary);
    register_rule(p, TOKEN_LT,     PREC_COMPARE, NULL, infix_binary);
    register_rule(p, TOKEN_GT,     PREC_COMPARE, NULL, infix_binary);
    register_rule(p, TOKEN_LTEQ,   PREC_COMPARE, NULL, infix_binary);
    register_rule(p, TOKEN_GTEQ,   PREC_COMPARE, NULL, infix_binary);
    register_rule(p, TOKEN_AMPAMP, PREC_AND,     NULL, infix_binary);
    register_rule(p, TOKEN_PIPEPIPE,PREC_OR,     NULL, infix_binary);
    register_rule(p, TOKEN_PIPE,   PREC_BIT_OR,  NULL, infix_binary);
    register_rule(p, TOKEN_CARET,  PREC_BIT_XOR, NULL, infix_binary);
    register_rule(p, TOKEN_LTLT,   PREC_SHIFT,   NULL, infix_binary);
    register_rule(p, TOKEN_GTGT,   PREC_SHIFT,   NULL, infix_binary);
    register_rule(p, TOKEN_EQ,     PREC_ASSIGN,  NULL, infix_assign);
    register_rule(p, TOKEN_PLUSEQ, PREC_ASSIGN,  NULL, infix_assign);
    register_rule(p, TOKEN_MINUSEQ,PREC_ASSIGN,  NULL, infix_assign);
    register_rule(p, TOKEN_STAREQ, PREC_ASSIGN,  NULL, infix_assign);
    register_rule(p, TOKEN_SLASHEQ,PREC_ASSIGN,  NULL, infix_assign);
    register_rule(p, TOKEN_PERCENTEQ,PREC_ASSIGN,NULL, infix_assign);
    register_rule(p, TOKEN_DOT,    PREC_PRIMARY, NULL, infix_field);
    register_rule(p, TOKEN_LBRACKET,PREC_PRIMARY,prefix_array_lit, infix_index);
    register_rule(p, TOKEN_AS,     PREC_FACTOR,  NULL, infix_as);
}

void parser_init(Parser *p, Lexer *lexer, Arena *arena) {
    p->lexer = lexer;
    p->arena = arena;
    p->error_count = 0;
    p->scope_depth = 0;
    p->global_scope = symtab_new(arena, NULL);
    p->current_scope = p->global_scope;
    init_rules(p);
}

Node *parser_parse(Parser *p) {
    SourceLoc loc = peek(p).loc;

    Node **decls = NULL;
    size_t ndeccls = 0, cap = 0;

    while (!check(p, TOKEN_EOF)) {
        Node *decl = parse_decl(p);
        if (decl) {
            if (ndeccls >= cap) {
                cap = cap ? cap * 2 : 16;
                Node **nd = arena_alloc(p->arena, cap * sizeof(Node *));
                if (decls && ndeccls > 0) memcpy(nd, decls, ndeccls * sizeof(Node *));
                decls = nd;
            }
            decls[ndeccls++] = decl;
        }
    }

    return ast_new_module(p->arena, loc, decls, ndeccls);
}
