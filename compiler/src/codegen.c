#include "codegen.h"
#include "arena.h"
#include <stdio.h>
#include <string.h>

/* ── side table: map Sym* → IRVal for local vars ── */
#define MAX_LOCALS 512
typedef struct {
    Sym  *sym;
    IRVal value;        /* SSA temp for immutable, stack slot addr for mutable */
    int   is_stack;     /* 1 if value is a stack slot address */
} LocalEntry;

typedef struct {
    IRBuf      *ir;
    LocalEntry  locals[MAX_LOCALS];
    int         nlocals;
    Type       *current_ret_type;  /* function return type for checking */
} CGContext;

static void cg_add_local(CGContext *cg, Sym *sym, IRVal val, int is_stack) {
    if (cg->nlocals < MAX_LOCALS) {
        cg->locals[cg->nlocals].sym = sym;
        cg->locals[cg->nlocals].value = val;
        cg->locals[cg->nlocals].is_stack = is_stack;
        cg->nlocals++;
    }
}

static IRVal cg_find_local(CGContext *cg, Sym *sym, int *is_stack) {
    for (int i = 0; i < cg->nlocals; i++) {
        if (cg->locals[i].sym == sym) {
            if (is_stack) *is_stack = cg->locals[i].is_stack;
            return cg->locals[i].value;
        }
    }
    IRVal zero = {0};
    return zero;
}

/* ── forward ── */
static IRVal cg_expr(CGContext *cg, Node *n);
static void   cg_stmt(CGContext *cg, Node *n);

/* ── codegen for expressions ── */

static IRVal cg_expr(CGContext *cg, Node *n) {
    if (!n) { IRVal v = {0}; return v; }

    switch (n->kind) {
    case NODE_INT: {
        NodeInt *d = node_int_data(n);
        IRVal v = ir_new_tmp(cg->ir, qbe_type_of(n->type));
        ir_emit_copy(cg->ir, v, d->value);
        return v;
    }
    case NODE_BOOL: {
        NodeBool *d = node_bool_data(n);
        IRVal v = ir_new_tmp(cg->ir, 'w');
        ir_emit_copy(cg->ir, v, d->value ? 1 : 0);
        return v;
    }
    case NODE_IDENT: {
        NodeIdent *d = node_ident_data(n);
        int is_stack = 0;
        IRVal loc = cg_find_local(cg, d->sym, &is_stack);
        if (is_stack) {
            /* load from stack */
            IRVal v = ir_new_tmp(cg->ir, qbe_type_of(n->type));
            ir_emit_load(cg->ir, v, qbe_type_of(n->type), loc);
            return v;
        }
        return loc; /* SSA value */
    }
    case NODE_BINARY: {
        NodeBinary *d = node_binary_data(n);
        IRVal left = cg_expr(cg, d->left);
        IRVal right = cg_expr(cg, d->right);

        IRVal result = ir_new_tmp(cg->ir, qbe_type_of(n->type));

        const char *op = NULL;
        switch (d->op) {
        case TOKEN_PLUS:  op = "add"; break;
        case TOKEN_MINUS: op = "sub"; break;
        case TOKEN_STAR:  op = "mul"; break;
        case TOKEN_SLASH: op = "div"; break;
        case TOKEN_PERCENT: op = "rem"; break;
        case TOKEN_EQEQ:   op = "ceqw"; break;
        case TOKEN_BANGEQ: op = "cnew"; break;
        case TOKEN_LT:     op = "csltw"; break;
        case TOKEN_LTEQ:   op = "cslew"; break;
        case TOKEN_GT:     op = "csgtw"; break;
        case TOKEN_GTEQ:   op = "csgew"; break;
        case TOKEN_AMPAMP: op = "and"; break;
        case TOKEN_PIPEPIPE: op = "or"; break;
        case TOKEN_AMP:    op = "and"; break;
        case TOKEN_PIPE:   op = "or"; break;
        case TOKEN_CARET:  op = "xor"; break;
        case TOKEN_LTLT:   op = "shl"; break;
        case TOKEN_GTGT:   op = "shr"; break;
        default: op = "add"; break;
        }
        ir_emit_binary(cg->ir, result, op, left, right);
        return result;
    }
    case NODE_CALL: {
        NodeCall *d = node_call_data(n);
        const char *fn_name = node_ident_data(d->callee)->sym->name;

        /* evaluate args */
        IRVal *args = NULL;
        if (d->nargs > 0)
            args = arena_alloc(cg->ir->arena, d->nargs * sizeof(IRVal));
        for (size_t i = 0; i < d->nargs; i++)
            args[i] = cg_expr(cg, d->args[i]);

        char qt = n->type ? qbe_type_of(n->type) : 'w';
        IRVal result = ir_new_tmp(cg->ir, qt);
        ir_emit_call(cg->ir, result, fn_name, args, (int)d->nargs);
        return result;
    }
    case NODE_IF: {
        NodeIf *d = node_if_data(n);
        IRVal cond = cg_expr(cg, d->cond);

        IRVal then_block = ir_new_block(cg->ir, "then");
        IRVal else_block = ir_new_block(cg->ir, "else");
        IRVal merge_block = ir_new_block(cg->ir, "merge");

        ir_emit_jnz(cg->ir, cond, then_block, else_block);

        /* then */
        ir_emit_label(cg->ir, then_block);
        IRVal then_val = cg_expr(cg, d->then_body);
        int then_returns = (d->then_body && d->then_body->kind == NODE_RETURN);
        if (!then_returns) ir_emit_jmp(cg->ir, merge_block);

        /* else */
        ir_emit_label(cg->ir, else_block);
        if (d->else_body) {
            IRVal else_val = cg_expr(cg, d->else_body);
            int else_returns = (d->else_body->kind == NODE_RETURN);
            if (!else_returns) ir_emit_jmp(cg->ir, merge_block);
            /* phi */
            ir_emit_label(cg->ir, merge_block);
            if (!then_returns && !else_returns) {
                IRVal result = ir_new_tmp(cg->ir, then_val.qbe_type);
                ir_emit_phi(cg->ir, result, 2, then_block, then_val, else_block, else_val);
                return result;
            }
        } else {
            ir_emit_jmp(cg->ir, merge_block);
            ir_emit_label(cg->ir, merge_block);
        }

        if (n->type && n->type->kind == KIND_VOID) {
            IRVal v = {0};
            return v;
        }
        return then_val; /* fallback */
    }
    case NODE_BLOCK: {
        NodeBlock *d = node_block_data(n);
        IRVal last = {0};
        for (size_t i = 0; i < d->nstmts; i++) {
            Node *stmt = d->stmts[i];
            if (stmt->kind == NODE_RETURN) {
                cg_stmt(cg, stmt);
                return last;
            }
            if (stmt->kind == NODE_EXPR_STMT) {
                NodeExprStmt *es = node_expr_stmt_data(stmt);
                if (es->expr->kind == NODE_ASSIGN) {
                    cg_stmt(cg, es->expr);
                } else {
                    /* capture value as potential block return value */
                    last = cg_expr(cg, es->expr);
                }
            } else {
                cg_stmt(cg, stmt);
            }
        }
        return last;
    }
    case NODE_RETURN: {
        NodeReturn *d = node_return_data(n);
        if (d->expr) {
            IRVal val = cg_expr(cg, d->expr);
            ir_emit_ret(cg->ir, val);
        } else {
            IRVal v = {0};
            ir_emit_ret(cg->ir, v);
        }
        IRVal v = {0};
        return v;
    }
    case NODE_EXPR_STMT: {
        NodeExprStmt *d = node_expr_stmt_data(n);
        return cg_expr(cg, d->expr);
    }
    default: {
        IRVal v = {0};
        return v;
    }
    }
}

static void cg_stmt(CGContext *cg, Node *n) {
    switch (n->kind) {
    case NODE_LET: {
        NodeLet *d = node_let_data(n);
        IRVal init_val = cg_expr(cg, d->init);

        if (d->is_mutable) {
            /* allocate stack slot */
            int size = (int)type_size(d->sym->type);
            if (size < 4) size = 4;
            IRVal slot = ir_new_tmp(cg->ir, 'l');
            ir_emit_alloc(cg->ir, slot, size);
            ir_emit_store(cg->ir, qbe_type_of(d->sym->type), init_val, slot);
            cg_add_local(cg, d->sym, slot, 1);
        } else {
            cg_add_local(cg, d->sym, init_val, 0);
        }
        break;
    }
    case NODE_ASSIGN: {
        NodeAssign *d = node_assign_data(n);
        /* find the target symbol */
        NodeIdent *id = node_ident_data(d->target);
        int is_stack = 0;
        IRVal slot = cg_find_local(cg, id->sym, &is_stack);
        if (is_stack) {
            IRVal val = cg_expr(cg, d->value);
            ir_emit_store(cg->ir, qbe_type_of(d->target->type), val, slot);
        }
        break;
    }
    case NODE_RETURN: {
        NodeReturn *dr = node_return_data(n);
        if (dr->expr) {
            IRVal val = cg_expr(cg, dr->expr);
            ir_emit_ret(cg->ir, val);
        } else {
            IRVal v = {0};
            ir_emit_ret(cg->ir, v);
        }
        break;
    }
    case NODE_EXPR_STMT: {
        Node *inner = node_expr_stmt_data(n)->expr;
        if (inner->kind == NODE_ASSIGN) {
            cg_stmt(cg, inner);
        } else {
            cg_expr(cg, inner);
        }
        break;
    }
    case NODE_WHILE: {
        NodeWhile *dw = node_while_data(n);
        IRVal loop_hdr = ir_new_block(cg->ir, "loop");
        IRVal body_b   = ir_new_block(cg->ir, "body");
        IRVal exit_b   = ir_new_block(cg->ir, "exit");

        ir_emit_jmp(cg->ir, loop_hdr);

        ir_emit_label(cg->ir, loop_hdr);
        IRVal cond = cg_expr(cg, dw->cond);
        ir_emit_jnz(cg->ir, cond, body_b, exit_b);

        ir_emit_label(cg->ir, body_b);
        cg_expr(cg, dw->body);
        ir_emit_jmp(cg->ir, loop_hdr);

        ir_emit_label(cg->ir, exit_b);
        break;
    }
    default:
        cg_expr(cg, n);
        break;
    }
}

/* ── function codegen ── */

static void cg_func(IRBuf *ir, Node *n) {
    NodeFuncDecl *fd = node_func_decl_data(n);
    if (fd->is_extern) return; /* no body to emit */

    char ret_qt = fd->sym->type && fd->sym->type->kind == KIND_FUNC && fd->sym->type->func.ret
                    ? qbe_type_of(fd->sym->type->func.ret) : 'w';

    /* emit header */
    ir_emit(ir, "export function %c $%s(", ret_qt, fd->sym->name);
    for (size_t i = 0; i < fd->nparams; i++) {
        if (i > 0) ir_emit(ir, ", ");
        Type *pt = fd->params[i].sym->type;
        ir_emit(ir, "%c %%%s", qbe_type_of(pt), fd->params[i].sym->name);
    }
    ir_emit(ir, ") {\n");
    ir_emit_label(ir, ir_new_block(ir, "start"));

    /* setup context */
    CGContext cg;
    cg.ir = ir;
    cg.nlocals = 0;
    cg.current_ret_type = fd->sym->type && fd->sym->type->kind == KIND_FUNC
                           ? fd->sym->type->func.ret : NULL;

    /* register params as locals (copy into SSA temps) */
    for (size_t i = 0; i < fd->nparams; i++) {
        char qt = qbe_type_of(fd->params[i].sym->type);
        IRVal param_val = ir_new_tmp(ir, qt);
        ir_emit(ir, "    %%t%d =%c copy %%%s\n",
                param_val.id, qt, fd->params[i].sym->name);
        cg_add_local(&cg, fd->params[i].sym, param_val, 0);
    }

    IRVal body_val = cg_expr(&cg, fd->body);

    /* emit ret if body ends with non-void expression and no explicit return */
    if (ret_qt != 0 && body_val.qbe_type != 0) {
        ir_emit_ret(ir, body_val);
    } else {
        IRVal v = {0};
        ir_emit_ret(ir, v);
    }

    ir_emit(ir, "}\n\n");
}

/* ── module codegen ── */

void cg_module(IRBuf *ir, Node *module) {
    NodeModule *md = node_module_data(module);
    for (size_t i = 0; i < md->ndeccls; i++) {
        Node *decl = md->decls[i];
        if (decl->kind == NODE_FUNC_DECL) {
            cg_func(ir, decl);
        }
    }
}
