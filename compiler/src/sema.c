#include "sema.h"
#include <stdio.h>
#include <string.h>
#include <stdarg.h>

/* ── helpers ── */
static void sema_error(SemaContext *ctx, SourceLoc loc, const char *fmt, ...) {
    fprintf(stderr, "%s:%d:%d: error: ", loc.filename, loc.line, loc.col);
    va_list ap;
    va_start(ap, fmt);
    vfprintf(stderr, fmt, ap);
    va_end(ap);
    fprintf(stderr, "\n");
    ctx->error_count++;
}

static void push_scope(SemaContext *ctx) {
    ctx->current_scope = symtab_new(ctx->arena, ctx->current_scope);
    ctx->scope_depth++;
}
static void pop_scope(SemaContext *ctx) {
    if (ctx->current_scope->parent)
        ctx->current_scope = ctx->current_scope->parent;
    ctx->scope_depth--;
}

/* ── forward ── */
static Type *infer_type(SemaContext *ctx, Node *n);
static Type *resolve_type_node(SemaContext *ctx, Node *tn);

/* ── resolve a type annotation node to a Type* ── */
static Type *resolve_type_node(SemaContext *ctx, Node *tn) {
    if (!tn) return NULL;

    switch (tn->kind) {
    case NODE_IDENT: {
        const char *name = node_ident_data(tn)->sym->name;
        Sym *sym = symtab_lookup(ctx->current_scope, name);
        if (sym && sym->kind == SYM_TYPE) {
            /* if the symbol already has a resolved type, use it */
            if (sym->type) return sym->type;
        }
        /* primitive types */
        if (strcmp(name, "i8") == 0)  return type_primitive(ctx->arena, PRIM_I8);
        if (strcmp(name, "i16") == 0) return type_primitive(ctx->arena, PRIM_I16);
        if (strcmp(name, "i32") == 0) return type_primitive(ctx->arena, PRIM_I32);
        if (strcmp(name, "i64") == 0) return type_primitive(ctx->arena, PRIM_I64);
        if (strcmp(name, "u8") == 0)  return type_primitive(ctx->arena, PRIM_U8);
        if (strcmp(name, "u16") == 0) return type_primitive(ctx->arena, PRIM_U16);
        if (strcmp(name, "u32") == 0) return type_primitive(ctx->arena, PRIM_U32);
        if (strcmp(name, "u64") == 0) return type_primitive(ctx->arena, PRIM_U64);
        if (strcmp(name, "f32") == 0) return type_primitive(ctx->arena, PRIM_F32);
        if (strcmp(name, "f64") == 0) return type_primitive(ctx->arena, PRIM_F64);
        if (strcmp(name, "bool") == 0) return type_primitive(ctx->arena, PRIM_BOOL);
        sema_error(ctx, tn->loc, "unknown type '%s'", name);
        return type_primitive(ctx->arena, PRIM_I32); /* error recovery */
    }

    case NODE_UNARY: {
        NodeUnary *ud = node_unary_data(tn);
        if (ud->op == TOKEN_STAR) {
            Type *inner = resolve_type_node(ctx, ud->expr);
            return type_pointer(ctx->arena, inner);
        }
        break;
    }
    default: break;
    }

    sema_error(ctx, tn->loc, "invalid type annotation");
    return type_primitive(ctx->arena, PRIM_I32);
}

/* ── type inference for expressions ── */
static Type *infer_type(SemaContext *ctx, Node *n) {
    if (!n) return type_void();
    if (n->type) return n->type;  /* already inferred */

    switch (n->kind) {
    /* ── literals ── */
    case NODE_INT: {
        NodeInt *d = node_int_data(n);
        n->type = type_primitive(ctx->arena, d->prim);
        return n->type;
    }
    case NODE_FLOAT: {
        n->type = type_primitive(ctx->arena, PRIM_F64);
        return n->type;
    }
    case NODE_STRING: {
        n->type = type_slice(ctx->arena, type_primitive(ctx->arena, PRIM_U8));
        return n->type;
    }
    case NODE_CHAR: {
        n->type = type_primitive(ctx->arena, PRIM_U8);
        return n->type;
    }
    case NODE_BOOL: {
        n->type = type_primitive(ctx->arena, PRIM_BOOL);
        return n->type;
    }

    /* ── identifier ── */
    case NODE_IDENT: {
        NodeIdent *d = node_ident_data(n);
        /* Check d->sym first (works for functions whose type was set early) */
        if (d->sym && d->sym->type) {
            n->type = d->sym->type;
            return n->type;
        }
        /* Search locals array (linear scan, reliable) */
        for (int i = ctx->nlocals - 1; i >= 0; i--) {
            if (strcmp(ctx->locals[i].name, d->sym->name) == 0) {
                n->type = ctx->locals[i].type;
                return n->type;
            }
        }
        sema_error(ctx, n->loc, "undefined variable '%s'", d->sym->name);
        n->type = type_primitive(ctx->arena, PRIM_I32);
        return n->type;
    }

    /* ── unary ── */
    case NODE_UNARY: {
        NodeUnary *d = node_unary_data(n);
        Type *inner = infer_type(ctx, d->expr);
        switch (d->op) {
        case TOKEN_MINUS: case TOKEN_TILDE:
            if (inner->kind != KIND_PRIMITIVE)
                sema_error(ctx, n->loc, "unary operator requires primitive type");
            n->type = inner;
            return n->type;
        case TOKEN_BANG:
            n->type = type_primitive(ctx->arena, PRIM_BOOL);
            return n->type;
        default:
            n->type = inner;
            return n->type;
        }
    }

    /* ── binary ── */
    case NODE_BINARY: {
        NodeBinary *d = node_binary_data(n);
        Type *lt = infer_type(ctx, d->left);
        Type *rt = infer_type(ctx, d->right);

        switch (d->op) {
        case TOKEN_PLUS:
        case TOKEN_MINUS:
        case TOKEN_STAR:
        case TOKEN_SLASH:
        case TOKEN_PERCENT:
        case TOKEN_PIPE:
        case TOKEN_AMP:
        case TOKEN_CARET:
        case TOKEN_LTLT:
        case TOKEN_GTGT:
            if (!type_eq(lt, rt))
                sema_error(ctx, n->loc, "type mismatch in binary: %s vs %s",
                           type_to_string(lt), type_to_string(rt));
            n->type = lt;
            return n->type;
        case TOKEN_EQEQ:
        case TOKEN_BANGEQ:
        case TOKEN_LT: case TOKEN_GT:
        case TOKEN_LTEQ: case TOKEN_GTEQ:
            n->type = type_primitive(ctx->arena, PRIM_BOOL);
            return n->type;
        case TOKEN_AMPAMP:
        case TOKEN_PIPEPIPE:
            n->type = type_primitive(ctx->arena, PRIM_BOOL);
            return n->type;
        default:
            n->type = lt;
            return n->type;
        }
    }

    /* ── dereference ── */
    case NODE_DEREF: {
        NodeDeref *d = node_deref_data(n);
        Type *inner = infer_type(ctx, d->expr);
        if (inner->kind != KIND_POINTER)
            sema_error(ctx, n->loc, "cannot dereference non-pointer type %s", type_to_string(inner));
        n->type = inner->kind == KIND_POINTER ? inner->pointer.elem : type_void();
        return n->type;
    }

    /* ── address-of ── */
    case NODE_ADDR_OF: {
        NodeAddrOf *d = node_addr_of_data(n);
        Type *inner = infer_type(ctx, d->expr);
        n->type = type_pointer(ctx->arena, inner);
        return n->type;
    }

    /* ── call ── */
    case NODE_CALL: {
        NodeCall *d = node_call_data(n);
        Type *callee_type = infer_type(ctx, d->callee);
        if (callee_type->kind == KIND_FUNC) {
            n->type = callee_type->func.ret ? callee_type->func.ret : type_void();
        } else {
            n->type = type_void(); /* unknown return */
        }
        return n->type;
    }

    /* ── field access ── */
    case NODE_FIELD: {
        NodeField *d = node_field_data(n);
        Type *struct_type = infer_type(ctx, d->expr);
        if (struct_type->kind == KIND_STRUCT) {
            for (size_t i = 0; i < struct_type->struct_type.nfields; i++) {
                if (strcmp(struct_type->struct_type.fields[i].name->name, d->field) == 0) {
                    n->type = struct_type->struct_type.fields[i].type;
                    return n->type;
                }
            }
            sema_error(ctx, n->loc, "struct '%s' has no field '%s'",
                       struct_type->struct_type.name->name, d->field);
        } else if (struct_type->kind == KIND_POINTER &&
                   struct_type->pointer.elem->kind == KIND_STRUCT) {
            /* auto-deref pointer to struct */
            Type *elem = struct_type->pointer.elem;
            for (size_t i = 0; i < elem->struct_type.nfields; i++) {
                if (strcmp(elem->struct_type.fields[i].name->name, d->field) == 0) {
                    n->type = elem->struct_type.fields[i].type;
                    return n->type;
                }
            }
            sema_error(ctx, n->loc, "struct '%s' has no field '%s'",
                       elem->struct_type.name->name, d->field);
        } else {
            sema_error(ctx, n->loc, "cannot access field on type %s", type_to_string(struct_type));
        }
        n->type = type_void();
        return n->type;
    }

    /* ── block ── */
    case NODE_BLOCK: {
        NodeBlock *d = node_block_data(n);
        Type *last_type = type_void();
        for (size_t i = 0; i < d->nstmts; i++) {
            last_type = infer_type(ctx, d->stmts[i]);
        }
        n->type = last_type;
        return n->type;
    }

    /* ── if ── */
    case NODE_IF: {
        NodeIf *d = node_if_data(n);
        Type *cond_type = infer_type(ctx, d->cond);
        if (!type_eq(cond_type, type_primitive(ctx->arena, PRIM_BOOL)))
            sema_error(ctx, n->loc, "if condition must be bool, got %s", type_to_string(cond_type));

        Type *then_type = infer_type(ctx, d->then_body);
        if (d->else_body) {
            Type *else_type = infer_type(ctx, d->else_body);
            if (!type_eq(then_type, else_type))
                sema_error(ctx, n->loc, "if/else branches must have same type: %s vs %s",
                           type_to_string(then_type), type_to_string(else_type));
            n->type = then_type;
        } else {
            n->type = type_void();
        }
        return n->type;
    }

    /* ── let ── */
    case NODE_LET: {
        NodeLet *d = node_let_data(n);
        Type *init_type = infer_type(ctx, d->init);
        Type *decl_type = init_type;

        if (d->type_annot) {
            decl_type = resolve_type_node(ctx, d->type_annot);
            if (!type_eq(decl_type, init_type))
                sema_error(ctx, n->loc, "type mismatch: expected %s, got %s",
                           type_to_string(decl_type), type_to_string(init_type));
        }

        d->sym->type = decl_type;
        d->sym->kind = SYM_VAR;
        if (ctx->nlocals < SEMA_MAX_LOCALS) {
            ctx->locals[ctx->nlocals].name = d->sym->name;
            ctx->locals[ctx->nlocals].type = decl_type;
            ctx->nlocals++;
        }
        n->type = type_void();
        return n->type;
    }

    /* ── assign ── */
    case NODE_ASSIGN: {
        NodeAssign *d = node_assign_data(n);
        Type *target_type = infer_type(ctx, d->target);
        Type *value_type = infer_type(ctx, d->value);
        if (!type_eq(target_type, value_type))
            sema_error(ctx, n->loc, "assignment type mismatch: %s = %s",
                       type_to_string(target_type), type_to_string(value_type));
        n->type = type_void();
        return n->type;
    }

    /* ── expr stmt ── */
    case NODE_EXPR_STMT: {
        NodeExprStmt *d = node_expr_stmt_data(n);
        n->type = infer_type(ctx, d->expr);
        return n->type;
    }

    /* ── return ── */
    case NODE_RETURN: {
        /* type will be checked against function return type later */
        n->type = type_void();
        return n->type;
    }

    /* ── while ── */
    case NODE_WHILE: {
        NodeWhile *d = node_while_data(n);
        infer_type(ctx, d->cond);
        infer_type(ctx, d->body);
        n->type = type_void();
        return n->type;
    }

    /* ── other: skip for now ── */
    default:
        n->type = type_void();
        return n->type;
    }
}

/* ── check function declaration ── */
static void check_func_decl(SemaContext *ctx, Node *n) {
    NodeFuncDecl *fd = node_func_decl_data(n);

    /* register in global scope if not yet done */
    if (!fd->sym->type) {
        /* create function type placeholder, then fill in */
    }

    push_scope(ctx);
    ctx->nlocals = 0;

    /* register parameters */
    Type **param_types = arena_alloc(ctx->arena, fd->nparams * sizeof(Type *));
    for (size_t i = 0; i < fd->nparams; i++) {
        Type *pt = resolve_type_node(ctx, fd->params[i].type_annot);
        param_types[i] = pt;
        fd->params[i].sym->type = pt;
        fd->params[i].sym->kind = SYM_VAR;
        symtab_insert(ctx->current_scope, fd->params[i].sym->name, SYM_VAR, pt, false, ctx->scope_depth);
    }

    /* determine return type */
    Type *ret_type;
    if (fd->ret_type) {
        ret_type = resolve_type_node(ctx, fd->ret_type);
    } else {
        ret_type = type_void(); /* will be inferred from body */
    }

    /* create full function type */
    Type *fn_type = type_func(ctx->arena, param_types, fd->nparams, ret_type);
    fd->sym->type = fn_type;
    fd->sym->kind = SYM_FN;

    /* check body */
    if (fd->body && !fd->is_extern) {
        Type *body_type = infer_type(ctx, fd->body);
        if (ret_type->kind != KIND_VOID && !type_eq(body_type, ret_type)) {
            sema_error(ctx, fd->body->loc, "function body type %s does not match return type %s",
                       type_to_string(body_type), type_to_string(ret_type));
        }
        /* if ret_type was void and body returns something, infer return type */
        if (ret_type->kind == KIND_VOID && body_type->kind != KIND_VOID) {
            fd->sym->type = type_func(ctx->arena, param_types, fd->nparams, body_type);
        }
    }

    pop_scope(ctx);
}

/* ── top-level check ── */
static void check_module(SemaContext *ctx, Node *module) {
    NodeModule *md = node_module_data(module);

    /* Pass 1: register all declarations (function names, type names) */
    for (size_t i = 0; i < md->ndeccls; i++) {
        Node *decl = md->decls[i];
        switch (decl->kind) {
        case NODE_FUNC_DECL: {
            NodeFuncDecl *fd = node_func_decl_data(decl);
            symtab_insert(ctx->global_scope, fd->sym->name, SYM_FN, NULL, false, 0);
            break;
        }
        case NODE_TYPE_DECL: {
            NodeTypeDecl *td = node_type_decl_data(decl);
            symtab_insert(ctx->global_scope, td->sym->name, SYM_TYPE, NULL, false, 0);
            break;
        }
        case NODE_IMPORT_DECL:
        case NODE_EXTERN_DECL:
            break;
        default: break;
        }
    }

    /* Pass 2: check function bodies */
    for (size_t i = 0; i < md->ndeccls; i++) {
        Node *decl = md->decls[i];
        switch (decl->kind) {
        case NODE_FUNC_DECL:
            check_func_decl(ctx, decl);
            break;
        case NODE_LET:
            infer_type(ctx, decl);
            break;
        case NODE_EXPR_STMT:
            infer_type(ctx, decl);
            break;
        default:
            break;
        }
    }
}

/* ── public API ── */

void sema_init(SemaContext *ctx, Arena *arena) {
    ctx->arena = arena;
    ctx->module = NULL;
    ctx->global_scope = symtab_new(arena, NULL);
    ctx->current_scope = ctx->global_scope;
    ctx->nlocals = 0;
    ctx->scope_depth = 0;
    ctx->error_count = 0;
}

int sema_check(SemaContext *ctx, Node *module) {
    ctx->module = module;
    ctx->current_scope = ctx->global_scope;
    check_module(ctx, module);
    return ctx->error_count;
}
