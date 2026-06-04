#ifndef SEMA_H
#define SEMA_H

#include "ast.h"
#include "arena.h"

typedef struct {
    Arena    *arena;
    Node     *module;
    SymTable *global_scope;
    SymTable *current_scope;
    int       scope_depth;
    int       error_count;
} SemaContext;

void sema_init(SemaContext *ctx, Arena *arena);
int  sema_check(SemaContext *ctx, Node *module);

#endif
