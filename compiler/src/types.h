#ifndef TYPES_H
#define TYPES_H

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

/* forward declaration */
struct Arena;

/* ── Primitive type enum ── */
typedef enum {
    PRIM_I8, PRIM_I16, PRIM_I32, PRIM_I64,
    PRIM_U8, PRIM_U16, PRIM_U32, PRIM_U64,
    PRIM_F32, PRIM_F64,
    PRIM_BOOL,
} TypePrimitive;

/* ── Type kind ── */
typedef enum {
    KIND_PRIMITIVE,
    KIND_POINTER,     /* *T       */
    KIND_SLICE,       /* [*]T     (ptr + length) */
    KIND_ARRAY,       /* [T; N]   (fixed-size array) */
    KIND_FUNC,        /* fn(T1, T2) -> Ret */
    KIND_STRUCT,      /* struct { fields } */
    KIND_ENUM,        /* enum { variants } */
    KIND_ALIAS,       /* type Name = T */
    KIND_VOID,        /* () unit type */
    KIND_UNRESOLVED,  /* name not yet resolved */
} TypeKind;

/* ── Forward declare Sym ── */
struct Sym;

/* ── Enum variant descriptor ── */
typedef struct VariantDesc {
    struct Sym *name;
    struct Type *payload;  /* NULL for nullary variant */
    int tag;
} VariantDesc;

/* ── Struct field descriptor ── */
typedef struct FieldDesc {
    struct Sym *name;
    struct Type *type;
    size_t offset;   /* byte offset within struct */
} FieldDesc;

/* ── Type ── */
typedef struct Type {
    TypeKind kind;
    union {
        TypePrimitive prim;  /* KIND_PRIMITIVE */

        struct {             /* KIND_POINTER */
            struct Type *elem;
        } pointer;

        struct {             /* KIND_SLICE */
            struct Type *elem;
        } slice;

        struct {             /* KIND_ARRAY */
            struct Type *elem;
            size_t count;
        } array;

        struct {             /* KIND_FUNC */
            struct Type **params;
            size_t nparams;
            struct Type *ret;
        } func;

        struct {             /* KIND_STRUCT */
            struct Sym *name;
            FieldDesc *fields;
            size_t nfields;
            size_t size;      /* total byte size */
            size_t align;     /* max alignment */
        } struct_type;

        struct {             /* KIND_ENUM */
            struct Sym *name;
            VariantDesc *variants;
            size_t nvariants;
            size_t tag_size;     /* sizeof(tag), usually 4 */
            size_t payload_size; /* max payload variant size */
            size_t total_size;   /* tag + payload, aligned */
        } enum_type;

        struct {             /* KIND_ALIAS */
            struct Sym *sym;
            struct Type *underlying;
        } alias;
    };
} Type;

/* ── API ── */
Type *type_primitive(struct Arena *a, TypePrimitive prim);
Type *type_pointer(struct Arena *a, Type *elem);
Type *type_slice(struct Arena *a, Type *elem);
Type *type_array(struct Arena *a, Type *elem, size_t count);
Type *type_func(struct Arena *a, Type **params, size_t nparams, Type *ret);
Type *type_struct(struct Arena *a, struct Sym *name, FieldDesc *fields, size_t nfields, size_t size, size_t align);
Type *type_enum(struct Arena *a, struct Sym *name, VariantDesc *variants, size_t nvariants, size_t tag_size, size_t payload_size, size_t total_size);
Type *type_alias(struct Arena *a, struct Sym *sym, Type *underlying);
Type *type_void(void);

size_t      type_size(Type *t);
size_t      type_align(Type *t);
bool        type_eq(Type *a, Type *b);
const char *type_to_string(Type *t);

#endif
