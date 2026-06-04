#include "arena.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <stdarg.h>
#include <stdint.h>

void arena_init(Arena *a, size_t default_size) {
    a->def_size = default_size > 0 ? default_size : ARENA_DEFAULT_SIZE;
    a->blocks = NULL;
    a->start = NULL;
    a->cur = NULL;
    a->end = NULL;
}

static void arena_new_block(Arena *a, size_t min_size) {
    size_t size = a->def_size;
    if (size < min_size) size = min_size;
    /* ensure at least 8-byte alignment */
    ArenaBlock *b = (ArenaBlock *)malloc(sizeof(ArenaBlock) + size);
    if (!b) return;  /* OOM, leaves arena unchanged */
    b->next = a->blocks;
    a->blocks = b;
    a->start = (char *)(b + 1);
    a->cur = a->start;
    a->end = a->start + size;
}

void *arena_alloc(Arena *a, size_t size) {
    return arena_alloc_aligned(a, size, 8);
}

void *arena_alloc_aligned(Arena *a, size_t size, size_t align) {
    if (size == 0) return NULL;
    uintptr_t mask = align - 1;
    if (a->cur) {
        char *p = (char *)(((uintptr_t)a->cur + mask) & ~mask);
        if (p + size <= a->end) {
            a->cur = p + size;
            return p;
        }
    }
    /* need new block */
    arena_new_block(a, size + align);
    if (!a->cur) return NULL;  /* OOM */
    return arena_alloc_aligned(a, size, align);
}

void *arena_calloc(Arena *a, size_t size) {
    void *p = arena_alloc(a, size);
    if (p) memset(p, 0, size);
    return p;
}

char *arena_strdup(Arena *a, const char *s, size_t len) {
    char *p = arena_alloc(a, len + 1);
    if (!p) return NULL;
    memcpy(p, s, len);
    p[len] = '\0';
    return p;
}

char *arena_sprintf(Arena *a, const char *fmt, ...) {
    va_list args;
    va_start(args, fmt);
    int n = vsnprintf(NULL, 0, fmt, args);
    va_end(args);
    if (n < 0) return NULL;
    char *buf = arena_alloc(a, n + 1);
    if (!buf) return NULL;
    va_start(args, fmt);
    vsnprintf(buf, n + 1, fmt, args);
    va_end(args);
    return buf;
}

void arena_reset(Arena *a) {
    if (a->blocks) {
        a->start = (char *)(a->blocks + 1);
        a->cur = a->start;
        a->end = a->start + a->def_size;
    }
}

void arena_free(Arena *a) {
    ArenaBlock *b = a->blocks;
    while (b) {
        ArenaBlock *next = b->next;
        free(b);
        b = next;
    }
    a->blocks = NULL;
    a->start = a->cur = a->end = NULL;
}
