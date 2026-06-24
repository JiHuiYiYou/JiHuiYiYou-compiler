# Sprint 1e — QBE Codegen (代码生成)

**日期**: 2026-06  
**状态**: 完成

## 成果

实现 AST → QBE IL 的代码生成，端到端连接 lexer→parser→sema→codegen→QBE→GCC 流水线。

### 文件

- `compiler/src/ir.h` / `ir.c` — IR 构建器 (QBE IL 文本生成)
- `compiler/src/codegen.h` / `codegen.c` — AST → QBE IL 发射
- `compiler/runtime/runtime.h` / `runtime.c` — C 运行时 (Arena + main 入口)

### IR 构建器

- `IRValKind`: `TEMP`, `INT`, `STR`, `BLOCK`
- `IRBuf`: arena-backed 增长缓冲区
- 关键命名规则:
  - **临时变量**: `%t0`, `%t1`... (前缀 `t` 是 QBE Windows 构建的要求)
  - **基本块**: `@start0`, `@loop1`... (hint + 序号)
  - **缩进**: 4 空格 (QBE Windows 构建不接受 tab)

#### IR 发射函数

| 函数 | QBE 输出 |
|------|---------|
| `ir_emit_copy` | `%tN =w copy 42` |
| `ir_emit_binary` | `%tN =w add %tA, %tB` |
| `ir_emit_call` | `%tN =w call $fn(w %tA, l %tB)` |
| `ir_emit_alloc` | `%tN =l alloc4 4` |
| `ir_emit_store` | `storew %tA, %tB` |
| `ir_emit_load` | `%tN =w loadw %tA` |
| `ir_emit_jnz` | `jnz %tC, @then, @else` |
| `ir_emit_phi` | `%tN =w phi @b1 %tA, @b2 %tB` |
| `ir_emit_ret` | `ret %tN` |

### QBE 类型映射

| jhyy | QBE |
|------|-----|
| i8/u8 | w (太小的用 word 承载) |
| i16/u16 | w |
| i32/u32 | w |
| i64/u64 | l |
| f32 | s |
| f64 | d |
| bool | w (0/1) |
| 指针 | l |
| () | 不生成 ret 值 |

### 代码生成规则

| jhyy 构造 | QBE 映射 |
|-----------|---------|
| `let x = 42` (不可变) | `%x =w copy 42` (纯 SSA) |
| `let mut x = 0` (可变) | `alloc4` + `storew`/`loadw` |
| 函数参数 | `%tN =w copy %param` (映射到 SSA) |
| `a + b` | `%tN =w add %tA, %tB` |
| `if cond { a } else { b }` | `jnz` + 分支 + `jmp` + `phi` |
| `while cond { body }` | loop 头 + `loadw` + `jnz` + 回边 |
| 函数调用 | `%tN =w call $fn(...)` |
| 函数定义 | `export function w $name(...) { ... }` |

### 关键修复

1. **参数映射**: 每个参数分配正式 temp ID，使用 `copy` 指令映射 `%param` → `%tN`
2. **NODE_BLOCK 语句/表达式分流**: 区分 `cg_stmt` 和 `cg_expr`，确保 `let`、`assign`、`while` 走正确路径
3. **NODE_EXPR_STMT 内嵌 NODE_ASSIGN 路由**: `cg_stmt` 检查内部表达式类型，正确路由赋值
4. **body_returns 检测**: 检查 body 块是否以 `return` 结尾 (NODE_BLOCK 包裹 NODE_RETURN 的情况)
5. **NODE_UNARY**: `-`, `!`, `~` 代码生成 (此前缺失，导致 `%t0` 跨函数引用)

### 运行时

- `main()` 调用用户定义的 `main_jhyy()`，将其返回值作为进程退出码
- Arena allocator: `arena_new`, `arena_alloc`, `arena_reset`, `arena_destroy`

### 工具链

- QBE: `qbe.exe -t amd64_win -o output.s input.il` (输出路径在前)
- GCC: `gcc.exe output.s runtime.c -o output.exe` (MSYS2 ucrt64)
- 编译器内使用绝对 Windows 路径调用 QBE 和 GCC

### Hello World 端到端验证

```jhyy
// hello.jhyy
fn main_jhyy() -> i32 { 42 }
```

生成 QBE IL:
```qbe
export function w $main_jhyy() {
@start0
    %t0 =w copy 42
    ret %t0
}
```

编译运行: `jhyy compile hello.jhyy` → `hello.exe` → EXIT:42

### 测试

- `compiler/tests/examples/hello.jhyy`: 端到端流水线验证
- `compiler/tests/examples/demo.jhyy`: 多函数、递归、while、mut、复合赋值、全部运算符
