#ifndef AST_H
#define AST_H

#include "types.h"
#include "symtab.h"
#include "lexer.h"

/* ── AST Node kind ── */
typedef enum {
    /* literals */
    NODE_INT,            /* 42, 0xFF     */
    NODE_FLOAT,          /* 3.14         */
    NODE_STRING,         /* "hello"      */
    NODE_CHAR,           /* 'a'          */
    NODE_BOOL,           /* true / false */

    /* expressions */
    NODE_IDENT,          /* variable reference */
    NODE_UNARY,          /* -expr, !expr, ~expr, *expr, &expr */
    NODE_BINARY,         /* a + b, a == b, a && b ... */
    NODE_CALL,           /* fn(args...) */
    NODE_FIELD,          /* expr.field */
    NODE_INDEX,          /* expr[index] */
    NODE_CAST,           /* expr as Type */
    NODE_ARRAY_TYPE,     /* [T; N] type annotation */
    NODE_ARRAY_LIT,      /* [1, 2, 3] array literal */
    NODE_SLICE_TYPE,     /* [*]T type annotation */
    NODE_SLICE_LIT,      /* &[1, 2, 3] slice literal */
    NODE_SLICE_RANGE,    /* s[a..b] sub-slice */
    NODE_SIZEOF,         /* sizeof(Type) */
    NODE_ALIGNOF,        /* alignof(Type) */
    NODE_ADDR_OF,        /* &expr */
    NODE_DEREF,          /* *expr */

    /* statements / block */
    NODE_BLOCK,          /* { stmts... } */
    NODE_IF,             /* if cond { then } [else { else }] */
    NODE_WHILE,          /* while cond { body } */
    NODE_FOR,            /* for var in start..end { body } */
    NODE_LET,            /* let [mut] name [:Type] = expr ; */
    NODE_ASSIGN,         /* target = expr */
    NODE_RETURN,         /* return [expr] */
    NODE_BREAK,          /* break; */
    NODE_CONTINUE,       /* continue; */
    NODE_EXPR_STMT,      /* expr ; (expression as statement) */

    /* match */
    NODE_MATCH,          /* match expr { arms } */
    NODE_MATCH_ARM,      /* pattern => body */

    /* patterns */
    NODE_PATTERN_LIT,    /* 0, true, 'a'  — literal pattern */
    NODE_PATTERN_IDENT,  /* x             — bind variable */
    NODE_PATTERN_ENUM,   /* Enum::Var(p)  — enum destructor */
    NODE_PATTERN_RANGE,  /* lo..hi        — range pattern */
    NODE_PATTERN_OR,     /* p1 | p2       — or pattern */
    NODE_PATTERN_WILD,   /* _             — wildcard */

    /* struct / enum */
    NODE_STRUCT_LIT,     /* TypeName { field: val, ... } */
    NODE_ENUM_VARIANT,   /* TypeName::Variant(expr) */
    NODE_STRUCT_DEF,     /* struct { field: Type, ... } — type definition body */
    NODE_ENUM_DEF,       /* enum { Variant(Type), ... } — type definition body */

    /* declarations */
    NODE_FUNC_DECL,      /* fn name(params) [-> Type] { body } */
    NODE_TYPE_DECL,      /* type Name = struct/enum { ... } */
    NODE_EXTERN_DECL,    /* extern fn name(params) [-> Type] */
    NODE_IMPORT_DECL,    /* import module */

    /* top level */
    NODE_MODULE,         /* root: list of declarations */
} NodeKind;

/* ── Node ── */
typedef struct Node {
    NodeKind    kind;
    Type       *type;        /* resolved type, set by sema */
    SourceLoc   loc;         /* source location */
    /* variant-specific data follows in arena */
} Node;

/* ── Variant data structs (embedded after Node in arena) ── */

typedef struct {
    int64_t       value;
    TypePrimitive prim;       /* i32, u64, etc. */
} NodeInt;

typedef struct { double value; } NodeFloat;
typedef struct { const char *chars; size_t len; } NodeString;
typedef struct { char ch; } NodeChar;
typedef struct { bool value; } NodeBool;
typedef struct { Sym *sym; } NodeIdent;

typedef struct {
    TokenKind op;
    Node     *expr;
} NodeUnary;

typedef struct {
    TokenKind op;
    Node     *left;
    Node     *right;
} NodeBinary;

typedef struct {
    Node   *callee;
    Node  **args;
    size_t  nargs;
} NodeCall;

typedef struct { Node *expr; const char *field; } NodeField;
typedef struct { Node *expr; Node *index; } NodeIndex;
typedef struct { Node *expr; Node *target_type; } NodeCast;
typedef struct { Node *elem_type; Node *count_expr; } NodeArrayType;
typedef struct { Node **elems; size_t nelems; } NodeArrayLit;
typedef struct { Node *elem_type; } NodeSliceType;
typedef struct { Node *array; } NodeSliceLit;
typedef struct { Node *base; Node *start; Node *end; } NodeSliceRange;
typedef struct { Type *target; } NodeSizeof;
typedef struct { Type *target; } NodeAlignof;
typedef struct { Node *expr; } NodeAddrOf;
typedef struct { Node *expr; } NodeDeref;

/* ── Sub-structs used by AST nodes ── */
typedef struct {
    const char *name;
    Node       *value;
} NodeFieldInit;

typedef struct {
    Sym  *sym;
    Node *type_annot;
} NodeFuncDeclParam;

typedef struct {
    Node  **stmts;
    size_t  nstmts;
} NodeBlock;

typedef struct {
    Node *cond;
    Node *then_body;
    Node *else_body;  /* NULL if no else */
} NodeIf;

typedef struct { Node *cond; Node *body; } NodeWhile;
typedef struct { Sym *var; Node *start; Node *end; Node *body; } NodeFor;

typedef struct {
    bool  is_mutable;
    Sym  *sym;
    Node *type_annot;  /* explicit type, NULL if inferred */
    Node *init;
} NodeLet;

typedef struct { Node *target; Node *value; } NodeAssign;
typedef struct { Node *expr; } NodeReturn;
typedef struct { Node *expr; } NodeExprStmt;

/* break / continue: no variant data needed */

typedef struct { Node *expr; struct Node **arms; size_t narms; } NodeMatch;

typedef struct {
    Node *pattern;
    Node *body;
} NodeMatchArm;

typedef struct { int64_t value; TypePrimitive prim; } NodePatternLit;
typedef struct { Sym *sym; } NodePatternIdent;
typedef struct { Sym *type_sym; Sym *variant_sym; Node *inner; } NodePatternEnum;
typedef struct { Node *lo; Node *hi; } NodePatternRange;
typedef struct { Node *left; Node *right; } NodePatternOr;

typedef struct {
    Sym            *type_sym;
    NodeFieldInit  *fields;
    size_t          nfields;
} NodeStructLit;

typedef struct {
    Sym  *type_sym;
    Sym  *variant_sym;
    Node *payload;  /* NULL for nullary variant */
} NodeEnumVariant;

/* Struct field declaration (for type definitions) */
typedef struct {
    const char *name;
    Node       *type_annot;
} StructFieldDecl;

typedef struct {
    StructFieldDecl *fields;
    size_t           nfields;
} NodeStructDef;

/* Enum variant declaration (for type definitions) */
typedef struct {
    const char *name;
    Node       *payload_type;  /* NULL for nullary variant */
} EnumVariantDecl;

typedef struct {
    EnumVariantDecl *variants;
    size_t           nvariants;
} NodeEnumDef;

typedef struct {
    Sym               *sym;
    NodeFuncDeclParam *params;
    size_t             nparams;
    Node              *ret_type;
    Node              *body;
    bool               is_extern;
} NodeFuncDecl;

typedef struct {
    Sym  *sym;
    Node *body;   /* struct/enum definition */
} NodeTypeDecl;

typedef struct { Sym *sym; } NodeExternDecl;
typedef struct { Sym *sym; } NodeImportDecl;

typedef struct {
    Node  **decls;
    size_t  ndeccls;
} NodeModule;

/* ── Node data accessors ── */

NodeInt          *node_int_data(Node *n);
NodeFloat        *node_float_data(Node *n);
NodeString       *node_string_data(Node *n);
NodeChar         *node_char_data(Node *n);
NodeBool         *node_bool_data(Node *n);
NodeIdent        *node_ident_data(Node *n);
NodeUnary        *node_unary_data(Node *n);
NodeBinary       *node_binary_data(Node *n);
NodeCall         *node_call_data(Node *n);
NodeField        *node_field_data(Node *n);
NodeIndex        *node_index_data(Node *n);
NodeCast         *node_cast_data(Node *n);
NodeArrayType    *node_array_type_data(Node *n);
NodeArrayLit     *node_array_lit_data(Node *n);
NodeSliceType    *node_slice_type_data(Node *n);
NodeSliceLit     *node_slice_lit_data(Node *n);
NodeSliceRange   *node_slice_range_data(Node *n);
NodeSizeof       *node_sizeof_data(Node *n);
NodeAlignof      *node_alignof_data(Node *n);
NodeAddrOf       *node_addr_of_data(Node *n);
NodeDeref        *node_deref_data(Node *n);
NodeBlock        *node_block_data(Node *n);
NodeIf           *node_if_data(Node *n);
NodeWhile        *node_while_data(Node *n);
NodeFor          *node_for_data(Node *n);
NodeLet          *node_let_data(Node *n);
NodeAssign       *node_assign_data(Node *n);
NodeReturn       *node_return_data(Node *n);
NodeExprStmt     *node_expr_stmt_data(Node *n);
NodeMatch        *node_match_data(Node *n);
NodeMatchArm     *node_match_arm_data(Node *n);
NodePatternLit   *node_pattern_lit_data(Node *n);
NodePatternIdent *node_pattern_ident_data(Node *n);
NodePatternEnum  *node_pattern_enum_data(Node *n);
NodePatternRange *node_pattern_range_data(Node *n);
NodePatternOr    *node_pattern_or_data(Node *n);
NodeStructLit    *node_struct_lit_data(Node *n);
NodeEnumVariant  *node_enum_variant_data(Node *n);
NodeStructDef    *node_struct_def_data(Node *n);
NodeEnumDef      *node_enum_def_data(Node *n);
NodeFuncDecl     *node_func_decl_data(Node *n);
NodeTypeDecl     *node_type_decl_data(Node *n);
NodeExternDecl   *node_extern_decl_data(Node *n);
NodeImportDecl   *node_import_decl_data(Node *n);
NodeModule       *node_module_data(Node *n);

/* ── Node constructors ── */
struct Arena;

Node *ast_new_int(struct Arena *a, SourceLoc loc, int64_t val, TypePrimitive prim);
Node *ast_new_float(struct Arena *a, SourceLoc loc, double val);
Node *ast_new_string(struct Arena *a, SourceLoc loc, const char *chars, size_t len);
Node *ast_new_char(struct Arena *a, SourceLoc loc, char ch);
Node *ast_new_bool(struct Arena *a, SourceLoc loc, bool val);
Node *ast_new_ident(struct Arena *a, SourceLoc loc, Sym *sym);
Node *ast_new_unary(struct Arena *a, SourceLoc loc, TokenKind op, Node *expr);
Node *ast_new_binary(struct Arena *a, SourceLoc loc, TokenKind op, Node *left, Node *right);
Node *ast_new_call(struct Arena *a, SourceLoc loc, Node *callee, Node **args, size_t nargs);
Node *ast_new_field(struct Arena *a, SourceLoc loc, Node *expr, const char *field);
Node *ast_new_index(struct Arena *a, SourceLoc loc, Node *expr, Node *index);
Node *ast_new_cast(struct Arena *a, SourceLoc loc, Node *expr, Node *target);
Node *ast_new_array_type(struct Arena *a, SourceLoc loc, Node *elem_type, Node *count_expr);
Node *ast_new_array_lit(struct Arena *a, SourceLoc loc, Node **elems, size_t nelems);
Node *ast_new_slice_type(struct Arena *a, SourceLoc loc, Node *elem_type);
Node *ast_new_slice_lit(struct Arena *a, SourceLoc loc, Node *array);
Node *ast_new_slice_range(struct Arena *a, SourceLoc loc, Node *base, Node *start, Node *end);
Node *ast_new_sizeof(struct Arena *a, SourceLoc loc, Type *target);
Node *ast_new_alignof(struct Arena *a, SourceLoc loc, Type *target);
Node *ast_new_addr_of(struct Arena *a, SourceLoc loc, Node *expr);
Node *ast_new_deref(struct Arena *a, SourceLoc loc, Node *expr);
Node *ast_new_block(struct Arena *a, SourceLoc loc, Node **stmts, size_t nstmts);
Node *ast_new_if(struct Arena *a, SourceLoc loc, Node *cond, Node *then_body, Node *else_body);
Node *ast_new_while(struct Arena *a, SourceLoc loc, Node *cond, Node *body);
Node *ast_new_for(struct Arena *a, SourceLoc loc, Sym *var, Node *start, Node *end, Node *body);
Node *ast_new_let(struct Arena *a, SourceLoc loc, bool is_mut, Sym *sym, Node *type_annot, Node *init);
Node *ast_new_assign(struct Arena *a, SourceLoc loc, Node *target, Node *value);
Node *ast_new_return(struct Arena *a, SourceLoc loc, Node *expr);
Node *ast_new_break(struct Arena *a, SourceLoc loc);
Node *ast_new_continue(struct Arena *a, SourceLoc loc);
Node *ast_new_expr_stmt(struct Arena *a, SourceLoc loc, Node *expr);
Node *ast_new_match(struct Arena *a, SourceLoc loc, Node *expr, Node **arms, size_t narms);
Node *ast_new_match_arm(struct Arena *a, SourceLoc loc, Node *pattern, Node *body);
Node *ast_new_pattern_lit(struct Arena *a, SourceLoc loc, int64_t val, TypePrimitive prim);
Node *ast_new_pattern_ident(struct Arena *a, SourceLoc loc, Sym *sym);
Node *ast_new_pattern_enum(struct Arena *a, SourceLoc loc, Sym *type_sym, Sym *variant_sym, Node *inner);
Node *ast_new_pattern_range(struct Arena *a, SourceLoc loc, Node *lo, Node *hi);
Node *ast_new_pattern_or(struct Arena *a, SourceLoc loc, Node *left, Node *right);
Node *ast_new_pattern_wild(struct Arena *a, SourceLoc loc);
Node *ast_new_struct_lit(struct Arena *a, SourceLoc loc, Sym *type_sym, NodeFieldInit *fields, size_t nfields);
Node *ast_new_enum_variant(struct Arena *a, SourceLoc loc, Sym *type_sym, Sym *variant_sym, Node *payload);
Node *ast_new_struct_def(struct Arena *a, SourceLoc loc, StructFieldDecl *fields, size_t nfields);
Node *ast_new_enum_def(struct Arena *a, SourceLoc loc, EnumVariantDecl *variants, size_t nvariants);
Node *ast_new_func_decl(struct Arena *a, SourceLoc loc, Sym *sym, NodeFuncDeclParam *params, size_t nparams, Node *ret_type, Node *body, bool is_extern);
Node *ast_new_type_decl(struct Arena *a, SourceLoc loc, Sym *sym, Node *body);
Node *ast_new_extern_decl(struct Arena *a, SourceLoc loc, Sym *sym);
Node *ast_new_import_decl(struct Arena *a, SourceLoc loc, Sym *sym);
Node *ast_new_module(struct Arena *a, SourceLoc loc, Node **decls, size_t ndeccls);

const char *node_kind_name(NodeKind kind);

#endif
