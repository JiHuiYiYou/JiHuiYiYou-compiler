# JHYY 编译器 v0.0.1 修改记录

## 概述

本次工作基于 Phase 0 骨架代码，修复了编译器在 parser、sema、codegen 三个阶段的多个 bug，使编译器能够正确编译并运行包含函数定义、变量绑定、控制流等基础语言特性的 `.jhyy` 源文件。

---

## 修改清单

### 1. parser.c — 函数名注册时机修复

**文件**: `compiler/src/parser.c:370-371`

**问题**: `parse_func` 在解析完函数体**之后**才把函数名插入 global scope。导致递归调用时函数名找不到。

**修改前**:
```c
// 函数体解析完后才注册
pop_scope(p);
Sym *sym = symtab_insert(p->global_scope, fname, SYM_FN, NULL, false, 0);
```

**修改后**:
```c
// 解析体之前注册，支持递归
Sym *sym = symtab_insert(p->global_scope, fname, SYM_FN, NULL, false, 0);
push_scope(p);
// ...解析参数和体...
pop_scope(p);
// 用已有的 sym，不再重复 insert
```

**影响**: 递归函数（如 `fibonacci`）现在可以正常编译。

---

### 2. sema.c — NODE_IDENT 查找机制重写

**文件**: `compiler/src/sema.c:104-121`

**问题**: sema 在 `sema_init` 中创建了**自己的 scope 树**（`symtab_new`），与 parser 的 scope 树完全独立。`NODE_LET` 处理时只设置了 parser 的 `Sym->type`，但 `NODE_IDENT` 用 `symtab_lookup` 在 sema 自己的 scope 中查找，导致 "undefined variable"。

此外，parser 的 scope 树在插入较多条目后（约 10+），`symtab_lookup` 会随机失败（根因未定位，疑似 FNV-1a hash 冲突问题）。

**修改**: `NODE_IDENT` 改为两步查找：

1. **优先检查 `d->sym->type`**: parser 的 Sym 对象如果已有 type（如函数名由 `check_func_decl` 提前设置），直接使用
2. **线性数组兜底**: 在 sema 中维护 `SemaLocal locals[]` 数组，`NODE_LET` 处理时把 `(name, type)` 写入，`NODE_IDENT` 查找时线性扫描。完全绕过 hash 表

**新增字段** (`sema.h`):
```c
#define SEMA_MAX_LOCALS 256
typedef struct {
    const char *name;
    Type       *type;
} SemaLocal;
// SemaContext 中新增:
SemaLocal locals[SEMA_MAX_LOCALS];
int       nlocals;
```

**影响**: 变量查找稳定可靠，不再依赖 hash 表。

---

### 3. symtab.c — 桶数扩容

**文件**: `compiler/src/symtab.c:6`

**问题**: hash 桶数仅 64，在有一定规模（20+ 条目）的 scope 中碰撞概率偏高。

**修改**:
```c
// 修改前
#define SYMTAB_INITIAL_SIZE 64
// 修改后
#define SYMTAB_INITIAL_SIZE 256
```

**影响**: 降低碰撞概率，虽未根本解决 hash 查找问题，但提高了可靠性。

---

### 4. codegen.c — NODE_BLOCK 语句/表达式分流

**文件**: `compiler/src/codegen.c:163-175`

**问题**: `cg_expr` 的 `NODE_BLOCK` 分支对**所有**子语句调用 `cg_expr`，但 `NODE_LET`、`NODE_ASSIGN` 的代码生成逻辑在 `cg_stmt` 中。导致 `let` 绑定和赋值语句不生成任何代码。

**修改前**:
```c
case NODE_BLOCK: {
    for (size_t i = 0; i < d->nstmts; i++) {
        if (d->stmts[i]->kind == NODE_RETURN) { ... }
        last = cg_expr(cg, d->stmts[i]);  // 全走 cg_expr
    }
}
```

**修改后**: 区分语句类型：
- `NODE_RETURN` → `cg_stmt`
- `NODE_EXPR_STMT` → 取内部表达式走 `cg_expr`，结果作为 block 返回值
- 其余 (`NODE_LET`, `NODE_ASSIGN`, `NODE_WHILE` 等) → `cg_stmt`

**影响**: `let`、赋值、`while` 循环均能正确生成 QBE 指令。

---

### 5. codegen.c — 函数参数用 copy 映射

**文件**: `compiler/src/codegen.c:296-306`

**问题**: 函数参数被注册为 `IRVAL_TEMP` 且 `id = -1`，导致生成的 QBE IL 中出现 `%t-1`，QBE 无法解析。

**修改前**:
```c
param_val.kind = IRVAL_TEMP;
param_val.id = -1;  // 非法 temp ID
```

**修改后**: 为每个参数分配正式 temp ID，生成 `copy` 指令将 QBE 参数名映射到 temp：
```c
IRVal param_val = ir_new_tmp(ir, qt);
ir_emit(ir, "    %%t%d =%c copy %%%s\n",
        param_val.id, qt, fd->params[i].sym->name);
cg_add_local(&cg, fd->params[i].sym, param_val, 0);
```

生成的 IL 示例:
```
%t0 =w copy %a     # 参数 a 映射到 %t0
%t1 =w copy %b     # 参数 b 映射到 %t1
%t2 =w add %t0, %t1
```

**影响**: 函数参数可正确传递和使用。

---

### 6. codegen.c — NODE_EXPR_STMT 内嵌 NODE_ASSIGN 路由

**文件**: `compiler/src/codegen.c:249-255`

**问题**: 赋值语句（如 `counter = 10`）在 AST 中是 `NODE_EXPR_STMT(NODE_ASSIGN(...))`。`cg_stmt` 的 `NODE_EXPR_STMT` 分支直接调用 `cg_expr`，而 `cg_expr` 不处理 `NODE_ASSIGN`，导致赋值不生成任何代码。

**修改**: `cg_stmt` 的 `NODE_EXPR_STMT` 分支检查内部表达式类型：
```c
case NODE_EXPR_STMT: {
    Node *inner = node_expr_stmt_data(n)->expr;
    if (inner->kind == NODE_ASSIGN) {
        cg_stmt(cg, inner);   // 走赋值逻辑
    } else {
        cg_expr(cg, inner);   // 值表达式
    }
    break;
}
```

**影响**: 赋值语句（包括复合赋值 `+=`, `-=` 等）能正确生成 store 指令。

---

## 遗留问题

### P0 — Parser hash 表查找不稳定

- **现象**: 在同一 scope 中，当通过 `symtab_insert` 插入约 10+ 个符号后，`symtab_lookup` 对**早期插入**的符号偶尔返回 NULL
- **临时规避**: sema 中使用线性 `locals[]` 数组替代 hash 查找
- **根因**: 未明。FNV-1a hash + 链式处理逻辑看起来正确，但实际运行中复现。可能需要 dump hash 分布或检查 arena 内存是否存在隐式越界
- **影响范围**: parser 的 `prefix_ident` 可能为已存在的变量创建重复 Sym 对象；sema 已不受影响

### P1 — Windows 下 `jhyy run` 的 system() 调用失败

- **现象**: `cmd_run` 中 `system(exe)` 报 `'compiler' 不是内部或外部命令`，因为路径中的 `/` 不被 Windows cmd.exe 识别
- **修复方向**: 将路径中的 `/` 转换为 `\`，或使用 `CreateProcess` / `_spawnv` 替代 `system()`

### P2 — 函数体返回值类型检查

- **现象**: 函数体最后若以 `return expr` 结尾，body type 会变成 `void`（因为 `NODE_RETURN` 的 `n->type = type_void()`）。而 `check_func_decl` 期望 body type 匹配返回类型
- **当前规避**: jhyy 是表达式导向语言，函数体最后的表达式**不加 `return`**，直接写表达式即可
- **长期**: `NODE_BLOCK` 在处理 `return` 之后应标记为 unreachable 并忽略 void；或让 `NODE_RETURN` 设置 block 类型为返回值的类型

### P3 — for 循环 / match 表达式未实现 codegen

- for 循环和 match 表达式在 parser 和 sema 中有部分支持，但 codegen 中无对应逻辑
- 调用会走到 `default` 分支，不生成任何代码

### P4 — 指针 / struct / enum / cast 未完整实现

- 类型系统已定义相关 kind，parser 有骨架代码
- sema 和 codegen 基本空实现
- `extern fn` 声明可用但参数类型受限

---

## 测试验证

测试文件: `compiler/tests/examples/demo.jhyy`

```bash
# 编译
gcc compiler/src/*.c -o compiler/build/bin/jhyy.exe -I compiler/src

# 运行
.\compiler\build\bin\jhyy.exe run compiler\tests\examples\demo.jhyy
```

demo.jhyy 内容覆盖：函数定义、递归、while 循环、mut 变量、复合赋值、算术/比较/逻辑/位运算、函数调用、if-else。
