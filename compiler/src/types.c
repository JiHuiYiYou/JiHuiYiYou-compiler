#include "types.h"
#include "symtab.h"
#include "arena.h"
#include <stdio.h>

/* ── cached primitive types ── */
static Type prim_i8, prim_i16, prim_i32, prim_i64;
static Type prim_u8, prim_u16, prim_u32, prim_u64;
static Type prim_f32, prim_f64;
static Type prim_bool;
static Type type_void_inst;
static int prims_inited = 0;

static void init_primitives(void) {
    if (prims_inited) return;
    prims_inited = 1;

    prim_i8      = (Type){ .kind = KIND_PRIMITIVE, .prim = PRIM_I8 };
    prim_i16     = (Type){ .kind = KIND_PRIMITIVE, .prim = PRIM_I16 };
    prim_i32     = (Type){ .kind = KIND_PRIMITIVE, .prim = PRIM_I32 };
    prim_i64     = (Type){ .kind = KIND_PRIMITIVE, .prim = PRIM_I64 };
    prim_u8      = (Type){ .kind = KIND_PRIMITIVE, .prim = PRIM_U8 };
    prim_u16     = (Type){ .kind = KIND_PRIMITIVE, .prim = PRIM_U16 };
    prim_u32     = (Type){ .kind = KIND_PRIMITIVE, .prim = PRIM_U32 };
    prim_u64     = (Type){ .kind = KIND_PRIMITIVE, .prim = PRIM_U64 };
    prim_f32     = (Type){ .kind = KIND_PRIMITIVE, .prim = PRIM_F32 };
    prim_f64     = (Type){ .kind = KIND_PRIMITIVE, .prim = PRIM_F64 };
    prim_bool    = (Type){ .kind = KIND_PRIMITIVE, .prim = PRIM_BOOL };
    type_void_inst = (Type){ .kind = KIND_VOID };
}

Type *type_primitive(Arena *a, TypePrimitive prim) {
    (void)a;
    init_primitives();
    switch (prim) {
    case PRIM_I8:   return &prim_i8;
    case PRIM_I16:  return &prim_i16;
    case PRIM_I32:  return &prim_i32;
    case PRIM_I64:  return &prim_i64;
    case PRIM_U8:   return &prim_u8;
    case PRIM_U16:  return &prim_u16;
    case PRIM_U32:  return &prim_u32;
    case PRIM_U64:  return &prim_u64;
    case PRIM_F32:  return &prim_f32;
    case PRIM_F64:  return &prim_f64;
    case PRIM_BOOL: return &prim_bool;
    default:        return NULL;
    }
}

Type *type_pointer(Arena *a, Type *elem) {
    Type *t = arena_alloc(a, sizeof(Type));
    t->kind = KIND_POINTER;
    t->pointer.elem = elem;
    return t;
}

Type *type_slice(Arena *a, Type *elem) {
    Type *t = arena_alloc(a, sizeof(Type));
    t->kind = KIND_SLICE;
    t->slice.elem = elem;
    return t;
}

Type *type_array(Arena *a, Type *elem, size_t count) {
    Type *t = arena_alloc(a, sizeof(Type));
    t->kind = KIND_ARRAY;
    t->array.elem = elem;
    t->array.count = count;
    return t;
}

Type *type_func(Arena *a, Type **params, size_t nparams, Type *ret) {
    Type *t = arena_alloc(a, sizeof(Type));
    t->kind = KIND_FUNC;
    t->func.params = params;
    t->func.nparams = nparams;
    t->func.ret = ret;
    return t;
}

Type *type_struct(Arena *a, Sym *name, FieldDesc *fields, size_t nfields, size_t size, size_t align) {
    Type *t = arena_alloc(a, sizeof(Type));
    t->kind = KIND_STRUCT;
    t->struct_type.name = name;
    t->struct_type.fields = fields;
    t->struct_type.nfields = nfields;
    t->struct_type.size = size;
    t->struct_type.align = align;
    return t;
}

Type *type_enum(Arena *a, Sym *name, VariantDesc *variants, size_t nvariants,
                size_t tag_size, size_t payload_offset, size_t payload_size, size_t total_size) {
    Type *t = arena_alloc(a, sizeof(Type));
    t->kind = KIND_ENUM;
    t->enum_type.name = name;
    t->enum_type.variants = variants;
    t->enum_type.nvariants = nvariants;
    t->enum_type.tag_size = tag_size;
    t->enum_type.payload_offset = payload_offset;
    t->enum_type.payload_size = payload_size;
    t->enum_type.total_size = total_size;
    return t;
}

Type *type_alias(Arena *a, Sym *sym, Type *underlying) {
    Type *t = arena_alloc(a, sizeof(Type));
    t->kind = KIND_ALIAS;
    t->alias.sym = sym;
    t->alias.underlying = underlying;
    return t;
}

Type *type_void(void) {
    init_primitives();
    return &type_void_inst;
}

/* ── size and alignment ── */

size_t type_size(Type *t) {
    if (!t) return 0;
    switch (t->kind) {
    case KIND_PRIMITIVE:
        switch (t->prim) {
        case PRIM_I8:  case PRIM_U8:   return 1;
        case PRIM_I16: case PRIM_U16:  return 2;
        case PRIM_I32: case PRIM_U32:  return 4;
        case PRIM_I64: case PRIM_U64:  return 8;
        case PRIM_F32:                 return 4;
        case PRIM_F64:                 return 8;
        case PRIM_BOOL:                return 1;
        default: return 0;
        }
    case KIND_POINTER: return 8;
    case KIND_SLICE:   return 16; /* ptr + len */
    case KIND_ARRAY:   return type_size(t->array.elem) * t->array.count;
    case KIND_FUNC:    return 8;  /* function pointer */
    case KIND_STRUCT:  return t->struct_type.size;
    case KIND_ENUM:    return t->enum_type.total_size;
    case KIND_VOID:    return 0;
    default: return 0;
    }
}

size_t type_align(Type *t) {
    if (!t) return 1;
    switch (t->kind) {
    case KIND_PRIMITIVE: return type_size(t); /* size == alignment for primitives */
    case KIND_POINTER:   return 8;
    case KIND_SLICE:     return 8;
    case KIND_ARRAY:     return type_align(t->array.elem);
    case KIND_FUNC:      return 8;
    case KIND_STRUCT:    return t->struct_type.align;
    case KIND_ENUM:      return 4; /* tag alignment */
    case KIND_VOID:      return 1;
    default: return 1;
    }
}

/* ── type equality ── */

bool type_eq(Type *a, Type *b) {
    if (a == b) return true;
    if (!a || !b) return false;
    if (a->kind != b->kind) return false;

    switch (a->kind) {
    case KIND_PRIMITIVE: return a->prim == b->prim;
    case KIND_POINTER:   return type_eq(a->pointer.elem, b->pointer.elem);
    case KIND_SLICE:     return type_eq(a->slice.elem, b->slice.elem);
    case KIND_ARRAY:     return type_eq(a->array.elem, b->array.elem) && a->array.count == b->array.count;
    case KIND_FUNC:
        if (a->func.nparams != b->func.nparams) return false;
        for (size_t i = 0; i < a->func.nparams; i++)
            if (!type_eq(a->func.params[i], b->func.params[i])) return false;
        return type_eq(a->func.ret, b->func.ret);
    case KIND_STRUCT:
        return a->struct_type.name == b->struct_type.name; /* nominal */
    case KIND_ENUM:
        return a->enum_type.name == b->enum_type.name;     /* nominal */
    case KIND_ALIAS:
        return type_eq(a->alias.underlying, b->alias.underlying);
    case KIND_VOID: return true;
    default: return false;
    }
}

/* ── type to string (for debugging) ── */

const char *type_to_string(Type *t) {
    static char buf[128];
    if (!t) return "(null)";
    switch (t->kind) {
    case KIND_PRIMITIVE:
        switch (t->prim) {
        case PRIM_I8:  return "i8";   case PRIM_I16: return "i16";
        case PRIM_I32: return "i32";  case PRIM_I64: return "i64";
        case PRIM_U8:  return "u8";   case PRIM_U16: return "u16";
        case PRIM_U32: return "u32";  case PRIM_U64: return "u64";
        case PRIM_F32: return "f32";  case PRIM_F64: return "f64";
        case PRIM_BOOL:return "bool";
        default: return "?prim";
        }
    case KIND_POINTER:
        snprintf(buf, sizeof(buf), "*%s", type_to_string(t->pointer.elem));
        return buf;
    case KIND_SLICE:
        snprintf(buf, sizeof(buf), "[*]%s", type_to_string(t->slice.elem));
        return buf;
    case KIND_ARRAY:
        snprintf(buf, sizeof(buf), "[%s; %zu]", type_to_string(t->array.elem), t->array.count);
        return buf;
    case KIND_FUNC:   return "fn(...)";
    case KIND_STRUCT: return t->struct_type.name ? t->struct_type.name->name : "(anon struct)";
    case KIND_ENUM:   return t->enum_type.name ? t->enum_type.name->name : "(anon enum)";
    case KIND_ALIAS:  return t->alias.sym ? t->alias.sym->name : "(alias)";
    case KIND_VOID:   return "()";
    default: return "?";
    }
}
