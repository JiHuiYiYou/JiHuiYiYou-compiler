#ifndef RUNTIME_H
#define RUNTIME_H

#include <stdint.h>
#include <stddef.h>

/* v4.0.2 W-074/076: removed unused C-side Arena 24B struct + 4 fn
 * (`arena_new` / `arena_alloc` / `arena_reset` / `arena_destroy`).
 * Real arena paths go through compiler/src/arena.c (C-side bootstrap)
 * or compiler/src0/arena.jhyy (jhyy-side production 40B Arena). */

/* user program entry point */
extern int main_jhyy(int argc, char **argv);

#endif
