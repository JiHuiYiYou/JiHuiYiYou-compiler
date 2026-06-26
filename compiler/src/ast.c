#include "ast.h"
#include "arena.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ── Internal: allocate Node + variant data ── */
static Node *new_node(Arena *a, NodeKind kind, SourceLoc loc, size_t extra) {
    Node *n = arena_calloc(a, sizeof(Node) + extra);
    n->kind = kind;
    n->loc = loc;
    n->type = NULL;
    return n;
}

/* Returns pointer to variant data right after Node */
static void *node_extra(Node *n) {
    return (char *)n + sizeof(Node);
}

/* ── Accessor macros ── */
#define ACCESSOR(name, type) \
    type *name(Node *n) { return (type *)node_extra(n); }

ACCESSOR(node_int_data, NodeInt)
ACCESSOR(node_float_data, NodeFloat)
ACCESSOR(node_string_data, NodeString)
ACCESSOR(node_char_data, NodeChar)
ACCESSOR(node_bool_data, NodeBool)
ACCESSOR(node_ident_data, NodeIdent)
ACCESSOR(node_unary_data, NodeUnary)
ACCESSOR(node_binary_data, NodeBinary)
ACCESSOR(node_call_data, NodeCall)
ACCESSOR(node_qualified_call_data, NodeQualifiedCall)
ACCESSOR(node_field_data, NodeField)
ACCESSOR(node_index_data, NodeIndex)
ACCESSOR(node_cast_data, NodeCast)
ACCESSOR(node_array_type_data, NodeArrayType)
ACCESSOR(node_array_lit_data, NodeArrayLit)
ACCESSOR(node_slice_type_data, NodeSliceType)
ACCESSOR(node_slice_lit_data, NodeSliceLit)
ACCESSOR(node_slice_range_data, NodeSliceRange)
ACCESSOR(node_sizeof_data, NodeSizeof)
ACCESSOR(node_alignof_data, NodeAlignof)
ACCESSOR(node_addr_of_data, NodeAddrOf)
ACCESSOR(node_deref_data, NodeDeref)
ACCESSOR(node_block_data, NodeBlock)
ACCESSOR(node_if_data, NodeIf)
ACCESSOR(node_while_data, NodeWhile)
ACCESSOR(node_for_data, NodeFor)
ACCESSOR(node_let_data, NodeLet)
ACCESSOR(node_assign_data, NodeAssign)
ACCESSOR(node_return_data, NodeReturn)
ACCESSOR(node_expr_stmt_data, NodeExprStmt)
ACCESSOR(node_match_data, NodeMatch)
ACCESSOR(node_match_arm_data, NodeMatchArm)
ACCESSOR(node_pattern_lit_data, NodePatternLit)
ACCESSOR(node_pattern_ident_data, NodePatternIdent)
ACCESSOR(node_pattern_enum_data, NodePatternEnum)
ACCESSOR(node_pattern_range_data, NodePatternRange)
ACCESSOR(node_pattern_or_data, NodePatternOr)
ACCESSOR(node_struct_lit_data, NodeStructLit)
ACCESSOR(node_enum_variant_data, NodeEnumVariant)
ACCESSOR(node_struct_def_data, NodeStructDef)
ACCESSOR(node_enum_def_data, NodeEnumDef)
ACCESSOR(node_func_decl_data, NodeFuncDecl)
ACCESSOR(node_type_decl_data, NodeTypeDecl)
ACCESSOR(node_extern_decl_data, NodeExternDecl)
ACCESSOR(node_import_decl_data, NodeImportDecl)
ACCESSOR(node_const_decl_data, NodeConstDecl)
ACCESSOR(node_module_data, NodeModule)

/* ── Constructors ── */

Node *ast_new_int(Arena *a, SourceLoc loc, int64_t val, TypePrimitive prim) {
    Node *n = new_node(a, NODE_INT, loc, sizeof(NodeInt));
    NodeInt *d = node_int_data(n);
    d->value = val;
    d->prim = prim;
    return n;
}

Node *ast_new_float(Arena *a, SourceLoc loc, double val) {
    Node *n = new_node(a, NODE_FLOAT, loc, sizeof(NodeFloat));
    node_float_data(n)->value = val;
    return n;
}

Node *ast_new_string(Arena *a, SourceLoc loc, const char *chars, size_t len) {
    Node *n = new_node(a, NODE_STRING, loc, sizeof(NodeString));
    NodeString *d = node_string_data(n);
    d->chars = chars;
    d->len = len;
    return n;
}

Node *ast_new_char(Arena *a, SourceLoc loc, char ch) {
    Node *n = new_node(a, NODE_CHAR, loc, sizeof(NodeChar));
    node_char_data(n)->ch = ch;
    return n;
}

Node *ast_new_bool(Arena *a, SourceLoc loc, bool val) {
    Node *n = new_node(a, NODE_BOOL, loc, sizeof(NodeBool));
    node_bool_data(n)->value = val;
    return n;
}

Node *ast_new_ident(Arena *a, SourceLoc loc, Sym *sym) {
    Node *n = new_node(a, NODE_IDENT, loc, sizeof(NodeIdent));
    node_ident_data(n)->sym = sym;
    return n;
}

Node *ast_new_unary(Arena *a, SourceLoc loc, TokenKind op, Node *expr) {
    Node *n = new_node(a, NODE_UNARY, loc, sizeof(NodeUnary));
    NodeUnary *d = node_unary_data(n);
    d->op = op;
    d->expr = expr;
    return n;
}

Node *ast_new_binary(Arena *a, SourceLoc loc, TokenKind op, Node *left, Node *right) {
    Node *n = new_node(a, NODE_BINARY, loc, sizeof(NodeBinary));
    NodeBinary *d = node_binary_data(n);
    d->op = op;
    d->left = left;
    d->right = right;
    return n;
}

Node *ast_new_call(Arena *a, SourceLoc loc, Node *callee, Node **args, size_t nargs) {
    Node *n = new_node(a, NODE_CALL, loc, sizeof(NodeCall));
    NodeCall *d = node_call_data(n);
    d->callee = callee;
    d->args = args;
    d->nargs = nargs;
    return n;
}

Node *ast_new_qualified_call(Arena *a, SourceLoc loc, Node *module, Node *function, Node **args, size_t nargs) {
    Node *n = new_node(a, NODE_QUALIFIED_CALL, loc, sizeof(NodeQualifiedCall));
    NodeQualifiedCall *d = node_qualified_call_data(n);
    d->module = module;
    d->function = function;
    d->args = args;
    d->nargs = nargs;
    d->resolved = NULL;
    return n;
}

Node *ast_new_field(Arena *a, SourceLoc loc, Node *expr, const char *field) {
    Node *n = new_node(a, NODE_FIELD, loc, sizeof(NodeField));
    NodeField *d = node_field_data(n);
    d->expr = expr;
    d->field = field;
    return n;
}

Node *ast_new_index(Arena *a, SourceLoc loc, Node *expr, Node *index) {
    Node *n = new_node(a, NODE_INDEX, loc, sizeof(NodeIndex));
    NodeIndex *d = node_index_data(n);
    d->expr = expr;
    d->index = index;
    return n;
}

Node *ast_new_cast(Arena *a, SourceLoc loc, Node *expr, Node *target) {
    Node *n = new_node(a, NODE_CAST, loc, sizeof(NodeCast));
    NodeCast *d = node_cast_data(n);
    d->expr = expr;
    d->target_type = target;
    return n;
}

Node *ast_new_array_type(Arena *a, SourceLoc loc, Node *elem_type, Node *count_expr) {
    Node *n = new_node(a, NODE_ARRAY_TYPE, loc, sizeof(NodeArrayType));
    NodeArrayType *d = node_array_type_data(n);
    d->elem_type = elem_type;
    d->count_expr = count_expr;
    return n;
}

Node *ast_new_array_lit(Arena *a, SourceLoc loc, Node **elems, size_t nelems) {
    Node *n = new_node(a, NODE_ARRAY_LIT, loc, sizeof(NodeArrayLit));
    NodeArrayLit *d = node_array_lit_data(n);
    d->elems = elems;
    d->nelems = nelems;
    return n;
}

Node *ast_new_slice_type(Arena *a, SourceLoc loc, Node *elem_type) {
    Node *n = new_node(a, NODE_SLICE_TYPE, loc, sizeof(NodeSliceType));
    node_slice_type_data(n)->elem_type = elem_type;
    return n;
}

Node *ast_new_slice_lit(Arena *a, SourceLoc loc, Node *array) {
    Node *n = new_node(a, NODE_SLICE_LIT, loc, sizeof(NodeSliceLit));
    node_slice_lit_data(n)->array = array;
    return n;
}

Node *ast_new_slice_range(Arena *a, SourceLoc loc, Node *base, Node *start, Node *end) {
    Node *n = new_node(a, NODE_SLICE_RANGE, loc, sizeof(NodeSliceRange));
    NodeSliceRange *d = node_slice_range_data(n);
    d->base = base;
    d->start = start;
    d->end = end;
    return n;
}

Node *ast_new_sizeof(Arena *a, SourceLoc loc, Type *target) {
    Node *n = new_node(a, NODE_SIZEOF, loc, sizeof(NodeSizeof));
    node_sizeof_data(n)->target = target;
    return n;
}

Node *ast_new_alignof(Arena *a, SourceLoc loc, Type *target) {
    Node *n = new_node(a, NODE_ALIGNOF, loc, sizeof(NodeAlignof));
    node_alignof_data(n)->target = target;
    return n;
}

Node *ast_new_addr_of(Arena *a, SourceLoc loc, Node *expr) {
    Node *n = new_node(a, NODE_ADDR_OF, loc, sizeof(NodeAddrOf));
    node_addr_of_data(n)->expr = expr;
    return n;
}

Node *ast_new_deref(Arena *a, SourceLoc loc, Node *expr) {
    Node *n = new_node(a, NODE_DEREF, loc, sizeof(NodeDeref));
    node_deref_data(n)->expr = expr;
    return n;
}

Node *ast_new_block(Arena *a, SourceLoc loc, Node **stmts, size_t nstmts) {
    Node *n = new_node(a, NODE_BLOCK, loc, sizeof(NodeBlock));
    NodeBlock *d = node_block_data(n);
    d->stmts = stmts;
    d->nstmts = nstmts;
    return n;
}

Node *ast_new_if(Arena *a, SourceLoc loc, Node *cond, Node *then_body, Node *else_body) {
    Node *n = new_node(a, NODE_IF, loc, sizeof(NodeIf));
    NodeIf *d = node_if_data(n);
    d->cond = cond;
    d->then_body = then_body;
    d->else_body = else_body;
    return n;
}

Node *ast_new_while(Arena *a, SourceLoc loc, Node *cond, Node *body) {
    Node *n = new_node(a, NODE_WHILE, loc, sizeof(NodeWhile));
    NodeWhile *d = node_while_data(n);
    d->cond = cond;
    d->body = body;
    return n;
}

Node *ast_new_for(Arena *a, SourceLoc loc, Sym *var, Node *start, Node *end, Node *body) {
    Node *n = new_node(a, NODE_FOR, loc, sizeof(NodeFor));
    NodeFor *d = node_for_data(n);
    d->var = var;
    d->start = start;
    d->end = end;
    d->body = body;
    return n;
}

Node *ast_new_let(Arena *a, SourceLoc loc, bool is_mut, Sym *sym, Node *type_annot, Node *init) {
    Node *n = new_node(a, NODE_LET, loc, sizeof(NodeLet));
    NodeLet *d = node_let_data(n);
    d->is_mutable = is_mut;
    d->sym = sym;
    d->type_annot = type_annot;
    d->init = init;
    return n;
}

Node *ast_new_assign(Arena *a, SourceLoc loc, Node *target, Node *value) {
    Node *n = new_node(a, NODE_ASSIGN, loc, sizeof(NodeAssign));
    NodeAssign *d = node_assign_data(n);
    d->target = target;
    d->value = value;
    return n;
}

Node *ast_new_return(Arena *a, SourceLoc loc, Node *expr) {
    Node *n = new_node(a, NODE_RETURN, loc, sizeof(NodeReturn));
    node_return_data(n)->expr = expr;
    return n;
}

Node *ast_new_break(Arena *a, SourceLoc loc) {
    return new_node(a, NODE_BREAK, loc, 0);
}

Node *ast_new_continue(Arena *a, SourceLoc loc) {
    return new_node(a, NODE_CONTINUE, loc, 0);
}

Node *ast_new_expr_stmt(Arena *a, SourceLoc loc, Node *expr) {
    Node *n = new_node(a, NODE_EXPR_STMT, loc, sizeof(NodeExprStmt));
    node_expr_stmt_data(n)->expr = expr;
    return n;
}

Node *ast_new_match(Arena *a, SourceLoc loc, Node *expr, Node **arms, size_t narms) {
    Node *n = new_node(a, NODE_MATCH, loc, sizeof(NodeMatch));
    NodeMatch *d = node_match_data(n);
    d->expr = expr;
    d->arms = arms;
    d->narms = narms;
    return n;
}

Node *ast_new_match_arm(Arena *a, SourceLoc loc, Node *pattern, Node *body) {
    Node *n = new_node(a, NODE_MATCH_ARM, loc, sizeof(NodeMatchArm));
    NodeMatchArm *d = node_match_arm_data(n);
    d->pattern = pattern;
    d->body = body;
    return n;
}

Node *ast_new_pattern_lit(Arena *a, SourceLoc loc, int64_t val, TypePrimitive prim) {
    Node *n = new_node(a, NODE_PATTERN_LIT, loc, sizeof(NodePatternLit));
    NodePatternLit *d = node_pattern_lit_data(n);
    d->value = val;
    d->prim = prim;
    return n;
}

Node *ast_new_pattern_ident(Arena *a, SourceLoc loc, Sym *sym) {
    Node *n = new_node(a, NODE_PATTERN_IDENT, loc, sizeof(NodePatternIdent));
    node_pattern_ident_data(n)->sym = sym;
    return n;
}

Node *ast_new_pattern_enum(Arena *a, SourceLoc loc, Sym *type_sym, Sym *variant_sym, Node *inner) {
    Node *n = new_node(a, NODE_PATTERN_ENUM, loc, sizeof(NodePatternEnum));
    NodePatternEnum *d = node_pattern_enum_data(n);
    d->type_sym = type_sym;
    d->variant_sym = variant_sym;
    d->inner = inner;
    return n;
}

Node *ast_new_pattern_range(Arena *a, SourceLoc loc, Node *lo, Node *hi) {
    Node *n = new_node(a, NODE_PATTERN_RANGE, loc, sizeof(NodePatternRange));
    NodePatternRange *d = node_pattern_range_data(n);
    d->lo = lo;
    d->hi = hi;
    return n;
}

Node *ast_new_pattern_or(Arena *a, SourceLoc loc, Node *left, Node *right) {
    Node *n = new_node(a, NODE_PATTERN_OR, loc, sizeof(NodePatternOr));
    NodePatternOr *d = node_pattern_or_data(n);
    d->left = left;
    d->right = right;
    return n;
}

Node *ast_new_pattern_wild(Arena *a, SourceLoc loc) {
    return new_node(a, NODE_PATTERN_WILD, loc, 0);
}

Node *ast_new_struct_lit(Arena *a, SourceLoc loc, Sym *type_sym, NodeFieldInit *fields, size_t nfields) {
    Node *n = new_node(a, NODE_STRUCT_LIT, loc, sizeof(NodeStructLit));
    NodeStructLit *d = node_struct_lit_data(n);
    d->type_sym = type_sym;
    d->fields = fields;
    d->nfields = nfields;
    return n;
}

Node *ast_new_enum_variant(Arena *a, SourceLoc loc, Sym *type_sym, Sym *variant_sym, Node *payload) {
    Node *n = new_node(a, NODE_ENUM_VARIANT, loc, sizeof(NodeEnumVariant));
    NodeEnumVariant *d = node_enum_variant_data(n);
    d->type_sym = type_sym;
    d->variant_sym = variant_sym;
    d->payload = payload;
    return n;
}

Node *ast_new_struct_def(Arena *a, SourceLoc loc, StructFieldDecl *fields, size_t nfields) {
    Node *n = new_node(a, NODE_STRUCT_DEF, loc, sizeof(NodeStructDef));
    NodeStructDef *d = node_struct_def_data(n);
    d->fields = fields;
    d->nfields = nfields;
    return n;
}

Node *ast_new_enum_def(Arena *a, SourceLoc loc, EnumVariantDecl *variants, size_t nvariants) {
    Node *n = new_node(a, NODE_ENUM_DEF, loc, sizeof(NodeEnumDef));
    NodeEnumDef *d = node_enum_def_data(n);
    d->variants = variants;
    d->nvariants = nvariants;
    return n;
}

Node *ast_new_func_decl(Arena *a, SourceLoc loc, Sym *sym, NodeFuncDeclParam *params,
                         size_t nparams, Node *ret_type, Node *body, bool is_extern) {
    Node *n = new_node(a, NODE_FUNC_DECL, loc, sizeof(NodeFuncDecl));
    NodeFuncDecl *d = node_func_decl_data(n);
    d->sym = sym;
    d->params = params;
    d->nparams = nparams;
    d->ret_type = ret_type;
    d->body = body;
    d->is_extern = is_extern;
    return n;
}

Node *ast_new_type_decl(Arena *a, SourceLoc loc, Sym *sym, Node *body) {
    Node *n = new_node(a, NODE_TYPE_DECL, loc, sizeof(NodeTypeDecl));
    NodeTypeDecl *d = node_type_decl_data(n);
    d->sym = sym;
    d->body = body;
    return n;
}

Node *ast_new_extern_decl(Arena *a, SourceLoc loc, Sym *sym) {
    Node *n = new_node(a, NODE_EXTERN_DECL, loc, sizeof(NodeExternDecl));
    node_extern_decl_data(n)->sym = sym;
    return n;
}

Node *ast_new_import_decl(Arena *a, SourceLoc loc, Sym *sym) {
    Node *n = new_node(a, NODE_IMPORT_DECL, loc, sizeof(NodeImportDecl));
    node_import_decl_data(n)->sym = sym;
    return n;
}

Node *ast_new_const_decl(Arena *a, SourceLoc loc, Sym *sym, Node *type_annot, Node *init) {
    Node *n = new_node(a, NODE_CONST_DECL, loc, sizeof(NodeConstDecl));
    NodeConstDecl *d = node_const_decl_data(n);
    d->sym = sym;
    d->type_annot = type_annot;
    d->init = init;
    return n;
}

Node *ast_new_module(Arena *a, SourceLoc loc, Node **decls, size_t ndeccls) {
    Node *n = new_node(a, NODE_MODULE, loc, sizeof(NodeModule));
    NodeModule *d = node_module_data(n);
    d->decls = decls;
    d->ndeccls = ndeccls;
    return n;
}

/* ── Debug name ── */

const char *node_kind_name(NodeKind kind) {
    switch (kind) {
    case NODE_INT:           return "int";
    case NODE_FLOAT:         return "float";
    case NODE_STRING:        return "string";
    case NODE_CHAR:          return "char";
    case NODE_BOOL:          return "bool";
    case NODE_IDENT:         return "ident";
    case NODE_UNARY:         return "unary";
    case NODE_BINARY:        return "binary";
    case NODE_CALL:          return "call";
    case NODE_QUALIFIED_CALL: return "qualified_call";
    case NODE_FIELD:         return "field";
    case NODE_INDEX:         return "index";
    case NODE_CAST:          return "cast";
    case NODE_ARRAY_TYPE:   return "array_type";
    case NODE_ARRAY_LIT:    return "array_lit";
    case NODE_SLICE_TYPE:   return "slice_type";
    case NODE_SLICE_LIT:    return "slice_lit";
    case NODE_SLICE_RANGE:  return "slice_range";
    case NODE_SIZEOF:        return "sizeof";
    case NODE_ALIGNOF:       return "alignof";
    case NODE_ADDR_OF:       return "addr_of";
    case NODE_DEREF:         return "deref";
    case NODE_BLOCK:         return "block";
    case NODE_IF:            return "if";
    case NODE_WHILE:         return "while";
    case NODE_FOR:           return "for";
    case NODE_LET:           return "let";
    case NODE_ASSIGN:        return "assign";
    case NODE_RETURN:        return "return";
    case NODE_BREAK:         return "break";
    case NODE_CONTINUE:      return "continue";
    case NODE_EXPR_STMT:     return "expr_stmt";
    case NODE_MATCH:         return "match";
    case NODE_MATCH_ARM:     return "match_arm";
    case NODE_PATTERN_LIT:   return "pattern_lit";
    case NODE_PATTERN_IDENT: return "pattern_ident";
    case NODE_PATTERN_ENUM:  return "pattern_enum";
    case NODE_PATTERN_RANGE: return "pattern_range";
    case NODE_PATTERN_OR:    return "pattern_or";
    case NODE_PATTERN_WILD:  return "pattern_wild";
    case NODE_STRUCT_LIT:    return "struct_lit";
    case NODE_ENUM_VARIANT:  return "enum_variant";
    case NODE_STRUCT_DEF:    return "struct_def";
    case NODE_ENUM_DEF:      return "enum_def";
    case NODE_FUNC_DECL:     return "func_decl";
    case NODE_TYPE_DECL:     return "type_decl";
    case NODE_EXTERN_DECL:   return "extern_decl";
    case NODE_IMPORT_DECL:   return "import_decl";
    case NODE_CONST_DECL:    return "const_decl";
    case NODE_MODULE:        return "module";
    default:                 return "?";
    }
}

/* ── AST dump (for byte-equal oracle / sprint 5 self-hosting verification) ── */

static void dump_indent(int depth) {
    for (int i = 0; i < depth; i++) fputs("  ", stdout);
}

static const char *dump_prim_name(TypePrimitive p) {
    switch (p) {
        case PRIM_I8: return "i8";   case PRIM_I16: return "i16";
        case PRIM_I32: return "i32"; case PRIM_I64: return "i64";
        case PRIM_U8: return "u8";   case PRIM_U16: return "u16";
        case PRIM_U32: return "u32"; case PRIM_U64: return "u64";
        case PRIM_F32: return "f32"; case PRIM_F64: return "f64";
        case PRIM_BOOL: return "bool";
        default: return "?";
    }
}

static const char *dump_sym_kind_name(SymKind k) {
    switch (k) {
        case SYM_VAR: return "var";
        case SYM_FN: return "fn";
        case SYM_TYPE: return "type";
        case SYM_FIELD: return "field";
        case SYM_VARIANT: return "variant";
        case SYM_MODULE: return "module";
        default: return "?";
    }
}

static const char *dump_op_name(TokenKind k) {
    /* only operators that can appear in NODE_BINARY / NODE_UNARY */
    switch (k) {
        case TOKEN_PLUS: return "+";   case TOKEN_MINUS: return "-";
        case TOKEN_STAR: return "*";   case TOKEN_SLASH: return "/";
        case TOKEN_PERCENT: return "%";
        case TOKEN_EQ: return "=";     case TOKEN_EQEQ: return "==";
        case TOKEN_BANGEQ: return "!=";
        case TOKEN_LT: return "<";     case TOKEN_GT: return ">";
        case TOKEN_LTEQ: return "<=";  case TOKEN_GTEQ: return ">=";
        case TOKEN_BANG: return "!";   case TOKEN_TILDE: return "~";
        case TOKEN_AMP: return "&";    case TOKEN_PIPE: return "|";
        case TOKEN_AMPAMP: return "&&"; case TOKEN_PIPEPIPE: return "||";
        default: return "?";
    }
}

static void dump_node(Node *n, int depth);

static void dump_node_list(Node **arr, size_t n, int depth) {
    for (size_t i = 0; i < n; i++) dump_node(arr[i], depth);
}

static void dump_sym(Sym *s, int depth) {
    dump_indent(depth);
    if (!s) { fputs("SYM null\n", stdout); return; }
    fprintf(stdout, "SYM name=%s kind=%s\n", s->name, dump_sym_kind_name(s->kind));
}

static void dump_field_init(NodeFieldInit *fi, int depth) {
    dump_indent(depth);
    fprintf(stdout, "FIELD name=%s\n", fi->name);
    dump_node(fi->value, depth + 1);
}

static void dump_struct_field_decl(StructFieldDecl *fd, int depth) {
    dump_indent(depth);
    fprintf(stdout, "STRUCT_FIELD name=%s\n", fd->name);
    dump_node(fd->type_annot, depth + 1);
}

static void dump_enum_variant_decl(EnumVariantDecl *vd, int depth) {
    dump_indent(depth);
    fprintf(stdout, "ENUM_VARIANT_DECL name=%s\n", vd->name);
    dump_node(vd->payload_type, depth + 1);
}

static void dump_func_decl_param(NodeFuncDeclParam *p, int depth) {
    dump_indent(depth);
    if (p->sym)
        fprintf(stdout, "PARAM name=%s kind=%s\n", p->sym->name, dump_sym_kind_name(p->sym->kind));
    else
        fputs("PARAM name=null\n", stdout);
    dump_node(p->type_annot, depth + 1);
}

static void dump_node(Node *n, int depth) {
    if (!n) { dump_indent(depth); fputs("null\n", stdout); return; }
    dump_indent(depth);
    fprintf(stdout, "%s\n", node_kind_name(n->kind));
    depth++;
    switch (n->kind) {
        case NODE_INT: {
            NodeInt *d = node_int_data(n);
            dump_indent(depth); fprintf(stdout, "value=%lld prim=%s\n", (long long)d->value, dump_prim_name(d->prim));
            break;
        }
        case NODE_FLOAT: {
            NodeFloat *d = node_float_data(n);
            dump_indent(depth); fprintf(stdout, "value=%g\n", d->value);
            break;
        }
        case NODE_STRING: {
            NodeString *d = node_string_data(n);
            dump_indent(depth); fprintf(stdout, "len=%zu chars=\"%.*s\"\n", d->len, (int)d->len, d->chars);
            break;
        }
        case NODE_CHAR: {
            NodeChar *d = node_char_data(n);
            dump_indent(depth); fprintf(stdout, "ch='%c'\n", d->ch);
            break;
        }
        case NODE_BOOL: {
            NodeBool *d = node_bool_data(n);
            dump_indent(depth); fprintf(stdout, "value=%s\n", d->value ? "true" : "false");
            break;
        }
        case NODE_IDENT: {
            NodeIdent *d = node_ident_data(n);
            dump_sym(d->sym, depth);
            break;
        }
        case NODE_UNARY: {
            NodeUnary *d = node_unary_data(n);
            dump_indent(depth); fprintf(stdout, "op=%s\n", dump_op_name(d->op));
            dump_node(d->expr, depth);
            break;
        }
        case NODE_BINARY: {
            NodeBinary *d = node_binary_data(n);
            dump_indent(depth); fprintf(stdout, "op=%s\n", dump_op_name(d->op));
            dump_node(d->left, depth);
            dump_node(d->right, depth);
            break;
        }
        case NODE_CALL: {
            NodeCall *d = node_call_data(n);
            dump_indent(depth); fprintf(stdout, "nargs=%zu\n", d->nargs);
            dump_node(d->callee, depth);
            dump_node_list(d->args, d->nargs, depth);
            break;
        }
        case NODE_QUALIFIED_CALL: {
            NodeQualifiedCall *d = node_qualified_call_data(n);
            dump_indent(depth); fprintf(stdout, "nargs=%zu\n", d->nargs);
            dump_node(d->module, depth);
            dump_node(d->function, depth);
            dump_node_list(d->args, d->nargs, depth);
            break;
        }
        case NODE_FIELD: {
            NodeField *d = node_field_data(n);
            dump_node(d->expr, depth);
            dump_indent(depth);
            fprintf(stdout, "field=\"%s\"\n", d->field);
            break;
        }
        case NODE_INDEX: {
            NodeIndex *d = node_index_data(n);
            dump_node(d->expr, depth);
            dump_node(d->index, depth);
            break;
        }
        case NODE_CAST: {
            NodeCast *d = node_cast_data(n);
            dump_node(d->expr, depth);
            dump_node(d->target_type, depth);
            break;
        }
        case NODE_ARRAY_TYPE: {
            NodeArrayType *d = node_array_type_data(n);
            dump_node(d->elem_type, depth);
            dump_node(d->count_expr, depth);
            break;
        }
        case NODE_ARRAY_LIT: {
            NodeArrayLit *d = node_array_lit_data(n);
            dump_indent(depth); fprintf(stdout, "nelems=%zu\n", d->nelems);
            dump_node_list(d->elems, d->nelems, depth);
            break;
        }
        case NODE_SLICE_TYPE: {
            NodeSliceType *d = node_slice_type_data(n);
            dump_node(d->elem_type, depth);
            break;
        }
        case NODE_SLICE_LIT: {
            NodeSliceLit *d = node_slice_lit_data(n);
            dump_node(d->array, depth);
            break;
        }
        case NODE_SLICE_RANGE: {
            NodeSliceRange *d = node_slice_range_data(n);
            dump_node(d->base, depth);
            dump_node(d->start, depth);
            dump_node(d->end, depth);
            break;
        }
        case NODE_SIZEOF:
        case NODE_ALIGNOF: {
            /* These hold a Type* resolved by sema; skipped in AST dump
               since types use a separate representation. */
            break;
        }
        case NODE_ADDR_OF:
        case NODE_DEREF: {
            NodeAddrOf *d = node_addr_of_data(n);
            dump_node(d->expr, depth);
            break;
        }
        case NODE_BLOCK: {
            NodeBlock *d = node_block_data(n);
            dump_indent(depth); fprintf(stdout, "nstmts=%zu\n", d->nstmts);
            dump_node_list(d->stmts, d->nstmts, depth);
            break;
        }
        case NODE_IF: {
            NodeIf *d = node_if_data(n);
            dump_node(d->cond, depth);
            dump_node(d->then_body, depth);
            if (d->else_body) dump_node(d->else_body, depth);
            break;
        }
        case NODE_WHILE: {
            NodeWhile *d = node_while_data(n);
            dump_node(d->cond, depth);
            dump_node(d->body, depth);
            break;
        }
        case NODE_FOR: {
            NodeFor *d = node_for_data(n);
            dump_sym(d->var, depth);
            dump_node(d->start, depth);
            dump_node(d->end, depth);
            dump_node(d->body, depth);
            break;
        }
        case NODE_LET: {
            NodeLet *d = node_let_data(n);
            dump_indent(depth); fprintf(stdout, "is_mutable=%s\n", d->is_mutable ? "true" : "false");
            dump_sym(d->sym, depth);
            if (d->type_annot) dump_node(d->type_annot, depth);
            if (d->init) dump_node(d->init, depth);
            break;
        }
        case NODE_ASSIGN: {
            NodeAssign *d = node_assign_data(n);
            dump_node(d->target, depth);
            dump_node(d->value, depth);
            break;
        }
        case NODE_RETURN: {
            NodeReturn *d = node_return_data(n);
            if (d->expr) dump_node(d->expr, depth);
            break;
        }
        case NODE_BREAK:
        case NODE_CONTINUE:
            break;  /* no variant data */
        case NODE_EXPR_STMT: {
            NodeExprStmt *d = node_expr_stmt_data(n);
            dump_node(d->expr, depth);
            break;
        }
        case NODE_MATCH: {
            NodeMatch *d = node_match_data(n);
            dump_node(d->expr, depth);
            dump_indent(depth); fprintf(stdout, "narms=%zu\n", d->narms);
            dump_node_list(d->arms, d->narms, depth);
            break;
        }
        case NODE_MATCH_ARM: {
            NodeMatchArm *d = node_match_arm_data(n);
            dump_node(d->pattern, depth);
            dump_node(d->body, depth);
            break;
        }
        case NODE_PATTERN_LIT: {
            NodePatternLit *d = node_pattern_lit_data(n);
            dump_indent(depth); fprintf(stdout, "value=%lld prim=%s\n", (long long)d->value, dump_prim_name(d->prim));
            break;
        }
        case NODE_PATTERN_IDENT: {
            NodePatternIdent *d = node_pattern_ident_data(n);
            dump_sym(d->sym, depth);
            break;
        }
        case NODE_PATTERN_ENUM: {
            NodePatternEnum *d = node_pattern_enum_data(n);
            dump_sym(d->type_sym, depth);
            dump_sym(d->variant_sym, depth);
            if (d->inner) dump_node(d->inner, depth);
            break;
        }
        case NODE_PATTERN_RANGE: {
            NodePatternRange *d = node_pattern_range_data(n);
            dump_node(d->lo, depth);
            dump_node(d->hi, depth);
            break;
        }
        case NODE_PATTERN_OR: {
            NodePatternOr *d = node_pattern_or_data(n);
            dump_node(d->left, depth);
            dump_node(d->right, depth);
            break;
        }
        case NODE_PATTERN_WILD:
            break;  /* no variant data */
        case NODE_STRUCT_LIT: {
            NodeStructLit *d = node_struct_lit_data(n);
            dump_sym(d->type_sym, depth);
            dump_indent(depth); fprintf(stdout, "nfields=%zu\n", d->nfields);
            for (size_t i = 0; i < d->nfields; i++)
                dump_field_init(&d->fields[i], depth);
            break;
        }
        case NODE_ENUM_VARIANT: {
            NodeEnumVariant *d = node_enum_variant_data(n);
            dump_sym(d->type_sym, depth);
            dump_sym(d->variant_sym, depth);
            if (d->payload) dump_node(d->payload, depth);
            break;
        }
        case NODE_STRUCT_DEF: {
            NodeStructDef *d = node_struct_def_data(n);
            dump_indent(depth); fprintf(stdout, "nfields=%zu\n", d->nfields);
            for (size_t i = 0; i < d->nfields; i++)
                dump_struct_field_decl(&d->fields[i], depth);
            break;
        }
        case NODE_ENUM_DEF: {
            NodeEnumDef *d = node_enum_def_data(n);
            dump_indent(depth); fprintf(stdout, "nvariants=%zu\n", d->nvariants);
            for (size_t i = 0; i < d->nvariants; i++)
                dump_enum_variant_decl(&d->variants[i], depth);
            break;
        }
        case NODE_FUNC_DECL: {
            NodeFuncDecl *d = node_func_decl_data(n);
            dump_sym(d->sym, depth);
            dump_indent(depth); fprintf(stdout, "nparams=%zu is_extern=%s\n", d->nparams, d->is_extern ? "true" : "false");
            for (size_t i = 0; i < d->nparams; i++)
                dump_func_decl_param(&d->params[i], depth);
            if (d->ret_type) dump_node(d->ret_type, depth);
            if (d->body) dump_node(d->body, depth);
            break;
        }
        case NODE_TYPE_DECL: {
            NodeTypeDecl *d = node_type_decl_data(n);
            dump_sym(d->sym, depth);
            dump_node(d->body, depth);
            break;
        }
        case NODE_EXTERN_DECL: {
            NodeExternDecl *d = node_extern_decl_data(n);
            dump_sym(d->sym, depth);
            break;
        }
        case NODE_IMPORT_DECL: {
            NodeImportDecl *d = node_import_decl_data(n);
            dump_sym(d->sym, depth);
            break;
        }
        case NODE_CONST_DECL: {
            NodeConstDecl *d = node_const_decl_data(n);
            dump_sym(d->sym, depth);
            if (d->type_annot) dump_node(d->type_annot, depth);
            if (d->init) dump_node(d->init, depth);
            break;
        }
        case NODE_MODULE: {
            NodeModule *d = node_module_data(n);
            dump_indent(depth); fprintf(stdout, "ndeccls=%zu\n", d->ndeccls);
            dump_node_list(d->decls, d->ndeccls, depth);
            break;
        }
        default:
            dump_indent(depth); fprintf(stdout, "<unknown kind %d>\n", n->kind);
            break;
    }
}

void ast_dump(Node *n) {
    dump_node(n, 0);
}
