#ifndef RUNTIME_H
#define RUNTIME_H

#include <stdint.h>
#include <stddef.h>

/* ── Arena Allocator ── */
typedef struct {
    char *start;
    char *cur;
    char *end;
} Arena;

void  arena_new(Arena *a, size_t size);
void *arena_alloc(Arena *a, size_t size, size_t align);
void  arena_reset(Arena *a);
void  arena_destroy(Arena *a);

/* user program entry point */
extern int main_jhyy(int argc, char **argv);

#endif
