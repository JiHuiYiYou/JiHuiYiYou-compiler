#include "runtime.h"
#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>

#ifdef _WIN32
#include <windows.h>
#endif

void arena_new(Arena *a, size_t size) {
    a->start = (char *)malloc(size);
    if (!a->start) {
        a->cur = a->end = 0;
        return;
    }
    a->cur = a->start;
    a->end = a->start + size;
}

void *arena_alloc(Arena *a, size_t size, size_t align) {
    uintptr_t mask = align - 1;
    char *p = (char *)(((uintptr_t)a->cur + mask) & ~mask);
    if (p + size > a->end) return 0;
    a->cur = p + size;
    return p;
}

void arena_reset(Arena *a) {
    a->cur = a->start;
}

void arena_destroy(Arena *a) {
    free(a->start);
    a->start = a->cur = a->end = 0;
}

int main(int argc, char **argv) {
#ifdef _WIN32
    SetConsoleOutputCP(65001); /* UTF-8 console output */
#endif
    return main_jhyy(argc, argv);
}
