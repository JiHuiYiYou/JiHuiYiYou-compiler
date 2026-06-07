#include "ir.h"
#include "arena.h"
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <stdlib.h>

/* ── jhyy → QBE type mapping ── */
char qbe_type_of(Type *t) {
    if (!t) return 'w';
    switch (t->kind) {
    case KIND_PRIMITIVE:
        switch (t->prim) {
        case PRIM_I8:  case PRIM_U8:  return 'b';
        case PRIM_I16: case PRIM_U16: return 'h';
        case PRIM_I32: case PRIM_U32: return 'w';
        case PRIM_I64: case PRIM_U64: return 'l';
        case PRIM_F32:                return 's';
        case PRIM_F64:                return 'd';
        case PRIM_BOOL:               return 'w';
        default: return 'w';
        }
    case KIND_POINTER: return 'l';
    case KIND_SLICE:   return 'l';
    case KIND_FUNC:    return 'l';
    case KIND_VOID:    return 0;
    default: return 'w';
    }
}

/* ── IR buffer ── */
void ir_init(IRBuf *ir, Arena *arena) {
    ir->arena = arena;
    ir->cap = 4096;
    ir->buf = arena_alloc(arena, ir->cap);
    ir->buf[0] = '\0';
    ir->len = 0;
    ir->next_tmp = 0;
    ir->next_block = 0;
    ir->next_data = 0;
    ir->data_buf = NULL;
    ir->data_len = 0;
    ir->data_cap = 0;
}

/* emit to data buffer (deferred definitions) */
static void ir_emit_data(IRBuf *ir, const char *fmt, ...) {
    if (!ir->data_buf) {
        ir->data_cap = 1024;
        ir->data_buf = arena_alloc(ir->arena, ir->data_cap);
        ir->data_buf[0] = '\0';
    }
    va_list ap; va_start(ap, fmt);
    size_t avail = ir->data_cap - ir->data_len;
    int n = vsnprintf(ir->data_buf + ir->data_len, avail, fmt, ap);
    va_end(ap);
    if (n < 0) return;
    if ((size_t)n >= avail) {
        size_t new_cap = ir->data_cap * 2;
        while ((size_t)n >= new_cap - ir->data_len) new_cap *= 2;
        char *new_buf = arena_alloc(ir->arena, new_cap);
        memcpy(new_buf, ir->data_buf, ir->data_len);
        ir->data_buf = new_buf; ir->data_cap = new_cap;
        va_start(ap, fmt);
        vsnprintf(ir->data_buf + ir->data_len, ir->data_cap - ir->data_len, fmt, ap);
        va_end(ap);
    }
    ir->data_len += n;
}

void ir_flush_data(IRBuf *ir) {
    if (!ir->data_buf || ir->data_len == 0) return;
    /* Prepend data definitions to main buffer */
    size_t total = ir->data_len + ir->len;
    while (total >= ir->cap) ir->cap *= 2;
    char *new_buf = arena_alloc(ir->arena, ir->cap);
    memcpy(new_buf, ir->data_buf, ir->data_len);
    memcpy(new_buf + ir->data_len, ir->buf, ir->len);
    ir->buf = new_buf;
    ir->len = total;
    ir->data_len = 0;
}

IRVal ir_new_tmp(IRBuf *ir, char qbe_type) {
    IRVal v; v.kind = IRVAL_TEMP; v.id = ir->next_tmp++; v.qbe_type = qbe_type; return v;
}
IRVal ir_new_block(IRBuf *ir, const char *hint) {
    IRVal v; v.kind = IRVAL_BLOCK; v.id = ir->next_block++;
    v.name = arena_sprintf(ir->arena, "%s%d", hint ? hint : "b", v.id); return v;
}
IRVal ir_new_data_str(IRBuf *ir, const char *str, size_t len) {
    IRVal v; v.kind = IRVAL_STR; v.id = ir->next_data++;
    v.name = arena_sprintf(ir->arena, "$str%d", v.id);
    v.qbe_type = 'l';  /* data labels are pointers (64-bit addresses) */
    ir_emit_data_string(ir, v, str, len); return v;
}

void ir_emit(IRBuf *ir, const char *fmt, ...) {
    va_list ap; va_start(ap, fmt);
    size_t avail = ir->cap - ir->len;
    int n = vsnprintf(ir->buf + ir->len, avail, fmt, ap);
    va_end(ap);
    if (n < 0) return;
    if ((size_t)n >= avail) {
        size_t new_cap = ir->cap * 2;
        while ((size_t)n >= new_cap - ir->len) new_cap *= 2;
        char *new_buf = arena_alloc(ir->arena, new_cap);
        memcpy(new_buf, ir->buf, ir->len);
        ir->buf = new_buf; ir->cap = new_cap;
        va_start(ap, fmt);
        vsnprintf(ir->buf + ir->len, ir->cap - ir->len, fmt, ap);
        va_end(ap);
    }
    ir->len += n;
}

/* ── emit helpers (using %tN for temps to avoid QBE numeric issues) ── */

void ir_emit_label(IRBuf *ir, IRVal block) {
    ir_emit(ir, "@%s\n", block.name);
}

void ir_emit_ret(IRBuf *ir, IRVal val) {
    if (val.qbe_type)
        ir_emit(ir, "    ret %%t%d\n", val.id);
    else
        ir_emit(ir, "    ret\n");
}

void ir_emit_jmp(IRBuf *ir, IRVal target) {
    ir_emit(ir, "    jmp @%s\n", target.name);
}

void ir_emit_jnz(IRBuf *ir, IRVal cond, IRVal then_b, IRVal else_b) {
    ir_emit(ir, "    jnz %%t%d, @%s, @%s\n", cond.id, then_b.name, else_b.name);
}

void ir_emit_binary(IRBuf *ir, IRVal dst, const char *op, IRVal a, IRVal b) {
    char qt = dst.qbe_type;
    if (a.kind == IRVAL_INT && b.kind == IRVAL_INT) {
        ir_emit(ir, "    %%t%d =%c copy %lld\n", dst.id, qt, (long long)a.ival);
    } else if (a.kind == IRVAL_INT) {
        ir_emit(ir, "    %%t%d =%c %s %lld, %%t%d\n", dst.id, qt, op, (long long)a.ival, b.id);
    } else if (b.kind == IRVAL_INT) {
        ir_emit(ir, "    %%t%d =%c %s %%t%d, %lld\n", dst.id, qt, op, a.id, (long long)b.ival);
    } else {
        ir_emit(ir, "    %%t%d =%c %s %%t%d, %%t%d\n", dst.id, qt, op, a.id, b.id);
    }
}

void ir_emit_copy(IRBuf *ir, IRVal dst, int64_t val) {
    ir_emit(ir, "    %%t%d =%c copy %lld\n", dst.id, dst.qbe_type, (long long)val);
}

void ir_emit_call(IRBuf *ir, IRVal dst, const char *fn, IRVal *args, int n) {
    char qt = dst.qbe_type ? dst.qbe_type : 'w';
    ir_emit(ir, "    %%t%d =%c call $%s(", dst.id, qt, fn);
    for (int i = 0; i < n; i++) {
        if (i > 0) ir_emit(ir, ", ");
        if (args[i].kind == IRVAL_STR) {
            ir_emit(ir, "%c %s", args[i].qbe_type, args[i].name);
        } else {
            ir_emit(ir, "%c %%t%d", args[i].qbe_type, args[i].id);
        }
    }
    ir_emit(ir, ")\n");
}

void ir_emit_alloc(IRBuf *ir, IRVal dst, int size) {
    /* QBE only supports alignment 4, 8, or 16. Round up size to alignment. */
    int align;
    if (size <= 4) align = 4;
    else if (size <= 8) align = 8;
    else align = 16;
    /* Round size up to alignment boundary */
    int aligned_size = (size + align - 1) & ~(align - 1);
    ir_emit(ir, "    %%t%d =l alloc%d %d\n", dst.id, align, aligned_size);
}

void ir_emit_store(IRBuf *ir, char qbe_type, IRVal val, IRVal addr) {
    const char *pref = (qbe_type == 'w') ? "storew" : (qbe_type == 'l') ? "storel" :
                       (qbe_type == 's') ? "stores" : (qbe_type == 'd') ? "stored" : "storew";
    ir_emit(ir, "    %s %%t%d, %%t%d\n", pref, val.id, addr.id);
}

void ir_emit_load(IRBuf *ir, IRVal dst, char qbe_type, IRVal addr) {
    const char *pref = (qbe_type == 'w') ? "loadw" : (qbe_type == 'l') ? "loadl" :
                       (qbe_type == 's') ? "loads" : (qbe_type == 'd') ? "loadd" : "loadw";
    ir_emit(ir, "    %%t%d =%c %s %%t%d\n", dst.id, dst.qbe_type, pref, addr.id);
}

void ir_emit_phi(IRBuf *ir, IRVal dst, int npairs, ...) {
    char qt = dst.qbe_type ? dst.qbe_type : 'w';
    ir_emit(ir, "    %%t%d =%c phi ", dst.id, qt);
    va_list ap; va_start(ap, npairs);
    for (int i = 0; i < npairs; i++) {
        if (i > 0) ir_emit(ir, ", ");
        IRVal block = va_arg(ap, IRVal);
        IRVal val = va_arg(ap, IRVal);
        ir_emit(ir, "@%s %%t%d", block.name, val.id);
    }
    va_end(ap);
    ir_emit(ir, "\n");
}

void ir_emit_data_string(IRBuf *ir, IRVal id, const char *str, size_t len) {
    ir_emit_data(ir, "data %s = { b \"", id.name);
    for (size_t i = 0; i < len; i++) {
        char c = str[i];
        if (c == '\\' && i + 1 < len) {
            /* JHYY escape sequence — emit the actual byte */
            char next = str[++i];
            switch (next) {
            case 'n':  ir_emit_data(ir, "\\n"); break;   /* QBE newline */
            case 't':  ir_emit_data(ir, "\\t"); break;   /* QBE tab */
            case 'r':  ir_emit_data(ir, "\\r"); break;   /* QBE carriage return */
            case '0':  ir_emit_data(ir, "\\0"); break;   /* QBE null byte */
            case '\\': ir_emit_data(ir, "\\\\"); break;  /* literal backslash */
            case '"':  ir_emit_data(ir, "\\\""); break;  /* literal double quote */
            case 'x': {
                /* \xHH hex escape — parse up to 2 hex digits */
                int val = 0;
                int digits = 0;
                while (digits < 2 && i + 1 < len) {
                    char hex = str[i + 1];
                    if (hex >= '0' && hex <= '9')      val = (val << 4) | (hex - '0');
                    else if (hex >= 'a' && hex <= 'f') val = (val << 4) | (hex - 'a' + 10);
                    else if (hex >= 'A' && hex <= 'F') val = (val << 4) | (hex - 'A' + 10);
                    else break;
                    i++; digits++;
                }
                ir_emit_data(ir, "\\x%02X", val & 0xFF);
                break;
            }
            default:
                /* unknown escape — emit literal backslash + char */
                ir_emit_data(ir, "\\\\%c", next);
                break;
            }
        } else if (c == '"') {
            ir_emit_data(ir, "\\\"");
        } else if (c == '\n') {
            ir_emit_data(ir, "\\n");
        } else {
            ir_emit_data(ir, "%c", c);
        }
    }
    ir_emit_data(ir, "\", b 0 }\n");
}

void ir_emit_func_header(IRBuf *ir, const char *name, char ret_type, ...) {
    if (ret_type)
        ir_emit(ir, "export function %c $%s(", ret_type, name);
    else
        ir_emit(ir, "export function $%s(", name);
    va_list ap; va_start(ap, ret_type);
    int first = 1;
    for (;;) {
        char *ptype = va_arg(ap, char *);
        if (!ptype) break;
        char *pname = va_arg(ap, char *);
        if (!pname) break;
        if (!first) ir_emit(ir, ", ");
        ir_emit(ir, "%c %%%s", *ptype, pname);
        first = 0;
    }
    va_end(ap);
    ir_emit(ir, ") {\n");
}
