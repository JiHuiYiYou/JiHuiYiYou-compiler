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
    ir_emit(ir, "    %%t%d =%c call $%s(", dst.id, dst.qbe_type, fn);
    for (int i = 0; i < n; i++) {
        if (i > 0) ir_emit(ir, ", ");
        ir_emit(ir, "%c %%t%d", args[i].qbe_type, args[i].id);
    }
    ir_emit(ir, ")\n");
}

void ir_emit_alloc(IRBuf *ir, IRVal dst, int size) {
    ir_emit(ir, "    %%t%d =l alloc%d %d\n", dst.id, size, size);
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
    ir_emit(ir, "    %%t%d =%c phi ", dst.id, dst.qbe_type);
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
    ir_emit(ir, "data %s = { b \"", id.name);
    for (size_t i = 0; i < len; i++) {
        char c = str[i];
        if (c == '\\') ir_emit(ir, "\\\\");
        else if (c == '"') ir_emit(ir, "\\\"");
        else if (c == '\n') ir_emit(ir, "\\\\n");
        else ir_emit(ir, "%c", c);
    }
    ir_emit(ir, "\", b 0 }\n");
}

void ir_emit_func_header(IRBuf *ir, const char *name, char ret_type, ...) {
    ir_emit(ir, "export function %c $%s(", ret_type, name);
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
