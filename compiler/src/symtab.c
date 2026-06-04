#include "symtab.h"
#include "arena.h"
#include <string.h>
#include <stdlib.h>

#define SYMTAB_INITIAL_SIZE 256

/* FNV-1a hash */
static uint32_t hash_string(const char *s) {
    uint32_t hash = 2166136261u;
    while (*s) {
        hash ^= (unsigned char)*s++;
        hash *= 16777619u;
    }
    return hash;
}

SymTable *symtab_new(Arena *a, SymTable *parent) {
    SymTable *t = arena_alloc(a, sizeof(SymTable));
    t->nbuckets = SYMTAB_INITIAL_SIZE;
    t->buckets = arena_calloc(a, t->nbuckets * sizeof(Sym *));
    t->count = 0;
    t->parent = parent;
    t->arena = a;
    return t;
}

Sym *symtab_insert(SymTable *t, const char *name, SymKind kind,
                   Type *type, bool is_mutable, int depth) {
    uint32_t h = hash_string(name) % t->nbuckets;
    Sym *sym = t->buckets[h];

    /* check if already exists in current scope */
    while (sym) {
        if (sym->depth == depth && strcmp(sym->name, name) == 0)
            return NULL;  /* already defined */
        sym = sym->next;
    }

    sym = arena_alloc(t->arena, sizeof(Sym));
    sym->name = name;
    sym->kind = kind;
    sym->type = type;
    sym->is_mutable = is_mutable;
    sym->depth = depth;
    sym->next = t->buckets[h];
    t->buckets[h] = sym;
    t->count++;
    return sym;
}

Sym *symtab_lookup(SymTable *t, const char *name) {
    while (t) {
        uint32_t h = hash_string(name) % t->nbuckets;
        Sym *sym = t->buckets[h];
        while (sym) {
            if (strcmp(sym->name, name) == 0)
                return sym;
            sym = sym->next;
        }
        t = t->parent;
    }
    return NULL;
}

Sym *symtab_lookup_local(SymTable *t, const char *name) {
    if (!t) return NULL;
    uint32_t h = hash_string(name) % t->nbuckets;
    Sym *sym = t->buckets[h];
    while (sym) {
        if (strcmp(sym->name, name) == 0)
            return sym;
        sym = sym->next;
    }
    return NULL;
}
