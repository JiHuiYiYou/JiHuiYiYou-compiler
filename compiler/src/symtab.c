#include "symtab.h"
#include "arena.h"
#include <string.h>

/* Power-of-2 initial size: 256 slots, fine for most scopes */
#define SYMTAB_INITIAL_SIZE 256

/* FNV-1a hash (64-bit) */
static uint64_t hash_string(const char *s) {
    uint64_t hash = 14695981039346656037ULL;
    while (*s) {
        hash ^= (unsigned char)*s++;
        hash *= 1099511628211ULL;
    }
    return hash;
}

/* Grow table to 2x size, rehash all entries */
static void symtab_grow(SymTable *t) {
    size_t old_n = t->nentries;
    Sym **old_entries = t->entries;

    t->nentries = old_n * 2;
    t->mask = t->nentries - 1;
    t->entries = arena_calloc(t->arena, t->nentries * sizeof(Sym *));

    /* Rehash existing entries */
    for (size_t i = 0; i < old_n; i++) {
        Sym *sym = old_entries[i];
        if (!sym) continue;
        uint64_t h = hash_string(sym->name);
        size_t idx = (size_t)(h & t->mask);
        /* Linear probe to find empty slot */
        while (t->entries[idx] != NULL) {
            idx = (idx + 1) & t->mask;
        }
        t->entries[idx] = sym;
    }
    /* old_entries is arena memory, no need to free */
}

SymTable *symtab_new(Arena *a, SymTable *parent) {
    SymTable *t = arena_alloc(a, sizeof(SymTable));
    t->nentries = SYMTAB_INITIAL_SIZE;
    t->mask = SYMTAB_INITIAL_SIZE - 1;
    t->entries = arena_calloc(a, t->nentries * sizeof(Sym *));
    t->count = 0;
    t->parent = parent;
    t->arena = a;
    return t;
}

Sym *symtab_insert(SymTable *t, const char *name, SymKind kind,
                   Type *type, bool is_mutable, int depth) {
    /* Grow if load factor > 0.75 */
    if (t->count * 4 >= t->nentries * 3) {
        symtab_grow(t);
    }

    uint64_t h = hash_string(name);
    size_t idx = (size_t)(h & t->mask);
    size_t first_tombstone = (size_t)-1;

    for (;;) {
        Sym *entry = t->entries[idx];
        if (entry == NULL) {
            /* Empty slot — insert here (or at first tombstone) */
            size_t target = (first_tombstone != (size_t)-1) ? first_tombstone : idx;
            Sym *sym = arena_alloc(t->arena, sizeof(Sym));
            sym->name = name;
            sym->kind = kind;
            sym->type = type;
            sym->is_mutable = is_mutable;
            sym->depth = depth;
            t->entries[target] = sym;
            t->count++;
            return sym;
        }
        /* Check for duplicate in same scope */
        if (entry->depth == depth && strcmp(entry->name, name) == 0) {
            return NULL;  /* already defined at this depth */
        }
        idx = (idx + 1) & t->mask;
        /* Table is full (shouldn't happen with growth) */
        if (idx == (size_t)(h & t->mask)) break;
    }
    return NULL;  /* table full */
}

/* Insert an already-allocated Sym* into the table (no allocation).
   Used to register parser-created symbols into sema's scope tree. */
Sym *symtab_insert_sym(SymTable *t, Sym *sym) {
    if (t->count * 4 >= t->nentries * 3) {
        symtab_grow(t);
    }

    uint64_t h = hash_string(sym->name);
    size_t idx = (size_t)(h & t->mask);

    for (;;) {
        Sym *entry = t->entries[idx];
        if (entry == NULL) {
            t->entries[idx] = sym;
            t->count++;
            return sym;
        }
        /* Skip if same sym already present (import dedup) */
        if (entry == sym) return sym;
        idx = (idx + 1) & t->mask;
        if (idx == (size_t)(h & t->mask)) break;
    }
    return NULL;
}

/* Search one table level (no parent recursion) */
static Sym *symtab_lookup_one(SymTable *t, const char *name) {
    if (!t || t->count == 0) return NULL;

    uint64_t h = hash_string(name);
    size_t idx = (size_t)(h & t->mask);
    size_t start = idx;

    do {
        Sym *entry = t->entries[idx];
        if (entry == NULL) {
            /* Empty slot means the key is not in this table —
               but only if we haven't wrapped. Linear probing means
               entries can cluster, so an empty slot definitely means
               the key was never inserted (no deletions). */
            return NULL;
        }
        if (strcmp(entry->name, name) == 0) {
            return entry;
        }
        idx = (idx + 1) & t->mask;
    } while (idx != start);

    return NULL;
}

Sym *symtab_lookup(SymTable *t, const char *name) {
    while (t) {
        Sym *sym = symtab_lookup_one(t, name);
        if (sym) return sym;
        t = t->parent;
    }
    return NULL;
}

Sym *symtab_lookup_local(SymTable *t, const char *name) {
    return symtab_lookup_one(t, name);
}
