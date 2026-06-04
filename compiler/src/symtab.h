#ifndef SYMTAB_H
#define SYMTAB_H

#include <stdbool.h>
#include <stddef.h>
#include "types.h"

/* ── Symbol kind ── */
typedef enum {
    SYM_VAR,       /* local / global variable */
    SYM_FN,        /* function */
    SYM_TYPE,      /* named type (struct/enum/alias) */
    SYM_FIELD,     /* struct field */
    SYM_VARIANT,   /* enum variant constructor */
    SYM_MODULE,    /* imported module */
} SymKind;

/* ── Symbol entry ── */
typedef struct Sym {
    const char *name;
    SymKind     kind;
    Type       *type;
    bool        is_mutable;
    int         depth;       /* scope depth, 0 = global */
    struct Sym *next;        /* hash chain */
} Sym;

/* ── Symbol table ── */
typedef struct SymTable {
    Sym            **buckets;
    size_t           nbuckets;
    size_t           count;
    struct SymTable *parent;     /* enclosing scope */
    struct Arena    *arena;
} SymTable;

SymTable *symtab_new(struct Arena *a, SymTable *parent);
Sym      *symtab_insert(SymTable *t, const char *name, SymKind kind, Type *type, bool is_mutable, int depth);
Sym      *symtab_lookup(SymTable *t, const char *name);        /* searches upward */
Sym      *symtab_lookup_local(SymTable *t, const char *name);  /* current scope only */

#endif
