#ifndef SEMA_H
#define SEMA_H

#include "ast.h"
#include "arena.h"

#define SEMA_MAX_LOCALS 256

typedef struct {
    const char *name;
    Type       *type;
} SemaLocal;

typedef struct {
    Arena    *arena;
    Node     *module;
    SymTable *global_scope;
    SymTable *current_scope;
    SemaLocal locals[SEMA_MAX_LOCALS];
    int       nlocals;
    int       scope_depth;
    int       error_count;
} SemaContext;

void sema_init(SemaContext *ctx, Arena *arena);
int  sema_check(SemaContext *ctx, Node *module);

#endif
