#ifndef IR_H
#define IR_H

#include "types.h"

/* ── Value types we track ── */
typedef enum {
    IRVAL_TEMP,    /* %N  — SSA temporary */
    IRVAL_INT,     /* 42  — integer constant */
    IRVAL_STR,     /* $str — string constant */
    IRVAL_BLOCK,   /* @name — block label */
} IRValKind;

/* IRVal layout MUST match jhyy-side type IRVal = struct { kind: i32, id: i32,
   ival: i64, name: *u8, qbe_type: i32 }. v0 emits jhyy struct literal field
   writes at jhyy-specified offsets but emits C struct field accesses using THIS
   struct's offsets. If they disagree (e.g. id @ offset 4 here vs union @ offset
   8), reads of fields filled by jhyy code return wrong values — W-005 systemic
   bug (3 cg_copy_struct call sites produce `copy %t0` because src_addr.id reads
   as 0 from ival instead of id).

   Removed union: id is independent of ival (no C-side code uses the union as a
   discriminator). Total struct size is unchanged (32 bytes, padded to 8-byte
   alignment for ival). */
typedef struct {
    IRValKind kind;       /* offset 0, 4 bytes (matches jhyy) */
    int id;               /* offset 4, 4 bytes (matches jhyy) */
    int64_t ival;         /* offset 8, 8 bytes (matches jhyy; overlaps with id logically but not physically) */
    const char *name;     /* offset 16, 8 bytes (matches jhyy) */
    char qbe_type;        /* offset 24, 1 byte (matches jhyy) */
} IRVal;

/* Sprint 4.25 W-005 #2 真修: `next_tmp` starts at 1 (ir.c:38), so id==0 is
   reserved as the "undefined / sentinel" IRVal. Callers initialize locals with
   `IRVal v = {0};` then never overwrite them when codegen decides to skip
   emission (e.g. NODE_IF when both arms terminate with return). Letting that
   sentinel reach cg_copy_struct / ir_emit_ret / ir_emit_store emits
   `copy %t0` / `\0 %t0` — QBE rejects with "invalid type for first operand".
   Guard each downstream consumer with irval_is_undef(v) BEFORE emitting. */
static inline int irval_is_undef(IRVal v) {
    return v.kind == IRVAL_TEMP && v.id == 0;
}

/* ── Key: which QBE type character to use for a jhyy Type ── */
char qbe_type_of(Type *t);
char qbe_data_type_of(Type *t);   /* data-section class (sub-word packs b/h) */

/* ── IR Buffer ── */
typedef struct {
    struct Arena *arena;
    char *buf;
    size_t len;
    size_t cap;
    int next_tmp;
    int next_block;
    int next_data;
    /* Current block for emission (most recently label-emitted block) */
    IRVal cur_block;
    /* Deferred data definitions (emitted before function code) */
    char *data_buf;
    size_t data_len;
    size_t data_cap;
} IRBuf;

void ir_init(IRBuf *ir, struct Arena *arena);

IRVal ir_new_tmp(IRBuf *ir, char qbe_type);
IRVal ir_new_block(IRBuf *ir, const char *hint);
IRVal ir_new_data_str(IRBuf *ir, const char *str, size_t len);
IRVal ir_current_block(IRBuf *ir);

/* emit instructions */
void ir_emit(IRBuf *ir, const char *fmt, ...);
void ir_emit_label(IRBuf *ir, IRVal block);
void ir_emit_ret(IRBuf *ir, IRVal val);
void ir_emit_jmp(IRBuf *ir, IRVal target);
void ir_emit_jnz(IRBuf *ir, IRVal cond, IRVal then_b, IRVal else_b);
void ir_emit_binary(IRBuf *ir, IRVal dst, const char *op, IRVal a, IRVal b);
void ir_emit_copy(IRBuf *ir, IRVal dst, int64_t val);
void ir_emit_call(IRBuf *ir, IRVal dst, const char *fn, IRVal *args, int n);
void ir_emit_call_void(IRBuf *ir, const char *fn, IRVal *args, int n);
void ir_emit_alloc(IRBuf *ir, IRVal dst, int size);
void ir_emit_store(IRBuf *ir, char qbe_type, IRVal val, IRVal addr);
void ir_emit_load(IRBuf *ir, IRVal dst, char qbe_type, IRVal addr);
/* v1.4.6 W-017: emit one operand with kind dispatch (mirror src0/ir.jhyy:310
   ir_emit_arg) — IRVAL_INT → " <ival>"; IRVAL_STR → " $name"; default → " %t<id>".
   Required for Stage 1 byte-equal (jhyy-side callers like ir_emit_store /
   ir_emit_load dispatch through this helper, not inline). */
void ir_emit_arg(IRBuf *ir, IRVal val);
void ir_emit_phi(IRBuf *ir, IRVal dst, int npairs, ...);

/* emit data (deferred until ir_flush_data) */
void ir_emit_data(IRBuf *ir, const char *fmt, ...);
void ir_emit_data_string(IRBuf *ir, IRVal id, const char *str, size_t len);
/* flush deferred data definitions to buf */
void ir_flush_data(IRBuf *ir);

/* convenience */
void ir_emit_func_header(IRBuf *ir, const char *name, char ret_type, /* params */ ...);

#endif
