#ifndef ARENA_H
#define ARENA_H

#include <stddef.h>

#define ARENA_DEFAULT_SIZE (1024 * 1024) /* 1 MB */

typedef struct ArenaBlock {
    struct ArenaBlock *next;
    /* data follows in allocation */
} ArenaBlock;

typedef struct Arena {
    char       *start;   /* current block start */
    char       *cur;     /* current allocation pointer */
    char       *end;     /* current block end */
    ArenaBlock *blocks;  /* linked list of blocks */
    size_t      def_size; /* default block size for new blocks */
} Arena;

void  arena_init(Arena *a, size_t default_size);
void *arena_alloc(Arena *a, size_t size);
void *arena_alloc_aligned(Arena *a, size_t size, size_t align);
void *arena_calloc(Arena *a, size_t size);
char *arena_strdup(Arena *a, const char *s, size_t len);
char *arena_sprintf(Arena *a, const char *fmt, ...);
void  arena_reset(Arena *a);  /* free all blocks, restart */
void  arena_free(Arena *a);   /* free everything */

#endif
