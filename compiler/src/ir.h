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

typedef struct {
    IRValKind kind;
    union {
        int id;           /* IRVAL_TEMP: temp number */
        int64_t ival;     /* IRVAL_INT: immediate value */
    };
    const char *name;     /* IRVAL_BLOCK: label name, IRVAL_STR: $data name */
    char qbe_type;        /* 'w', 'l', 's', 'd' */
} IRVal;

/* ── Key: which QBE type character to use for a jhyy Type ── */
char qbe_type_of(Type *t);

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
void ir_emit_phi(IRBuf *ir, IRVal dst, int npairs, ...);

/* emit data (deferred until ir_flush_data) */
void ir_emit_data(IRBuf *ir, const char *fmt, ...);
void ir_emit_data_string(IRBuf *ir, IRVal id, const char *str, size_t len);
/* flush deferred data definitions to buf */
void ir_flush_data(IRBuf *ir);

/* convenience */
void ir_emit_func_header(IRBuf *ir, const char *name, char ret_type, /* params */ ...);

#endif
