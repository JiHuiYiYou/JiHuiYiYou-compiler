# 编译器架构

> 流水线、源文件布局、关键设计决策。

## 流水线

```
.jhyy → Lexer → Token流 → Parser → AST → Sema → 标注AST → Codegen → QBE IL → QBE → 汇编(.s) → GCC → .exe
```

`main.c` 调用顺序：
```
read_file
→ arena_init
→ lexer_init
→ parser_init
→ parser_parse
→ resolve_imports        (v0.4+：多文件)
→ sema_init
→ sema_check
→ ir_init
→ cg_module
→ write .il
→ system("qbe ...")
→ system("gcc ... + runtime.c")
```

---

## 源文件清单

`compiler/src/` 下 19 个文件（含 .c + .h）：

| 文件 | 行数 | 职责 |
|------|------|------|
| `arena.c/h` | ~150 | Bump allocator（编译器内部用） |
| `lexer.c/h` | ~400 | 词法分析：源码 → Token 流（50+ token 类型） |
| `ast.c/h` | ~400 | AST：35 种节点类型（tagged union） |
| `types.c/h` | ~250 | 类型系统：原始类型/指针/切片/数组/struct/enum/func/alias |
| `symtab.c/h` | ~120 | 符号表：FNV-1a hash，开放寻址 + 链式作用域 |
| `parser.c/h` | ~750 | 递归下降 + Pratt 表达式解析 |
| `sema.c/h` | ~500 | 语义分析：类型检查/推断，3 遍遍历 |
| `ir.c/h` | ~250 | IR 构建器：QBE IL 文本生成 |
| `codegen.c/h` | ~550 | AST → QBE IL 发射 |
| `main.c` | ~150 | CLI 入口，驱动流水线，调用 QBE + GCC |

运行时：
- `compiler/runtime/runtime.c` ~50 行：`main → main_jhyy` 桥接 + Arena 实现（重复声明，仅供运行时使用）
- `compiler/runtime/runtime.h` ~25 行：运行时头文件

---

## 关键设计细节

### AST 节点

- 所有节点是 `Node` struct + variant data（紧跟 Node 在 arena 中分配）
- `ACCESSOR` 宏模式：`node_xxx_data(Node*)` 返回 variant data 指针
- 构造函数命名：`ast_new_xxx(Arena*, SourceLoc, ...)`
- 共 35 种 `NodeKind`，分布在 `ast.h`

### 类型系统

```
KIND_PRIMITIVE   i8/u8/i16/u16/i32/u32/i64/u64/f32/f64/bool
KIND_POINTER     *T
KIND_SLICE       [*]T (v0.6 codegen)
KIND_ARRAY       [T; N]
KIND_STRUCT      struct { ... }
KIND_ENUM        enum { ... }
KIND_FUNC        (T1, T2) -> R
KIND_ALIAS       type X = ...
KIND_VOID        ()
```

`qbe_type_of()` 返回 QBE 宽度字符：
- `b` (i8/u8/bool)、`h` (i16/u16)、`w` (i32/u32)、`l` (i64/u64)、`s` (f32)、`d` (f64)

### 类型推断规则

- 参数必须标注类型
- 局部变量自动推断（从 init 表达式）
- 函数返回类型：标注优先，标注为 `()` 时从函数体推断

### 符号表

- 开放寻址 + 线性探测，64-bit FNV-1a hash
- 2 的幂大小，负载因子 0.75 自动扩容
- `Sym.module`（v0.6+）：所属模块名（NULL = main），用于 `$mod__name` mangle
- `Sym.is_extern`（v0.6+）：FFI 声明，emit 时不 mangle
- `symtab_insert_sym()` 用于桥接 parser 和 sema 的 Sym

### 作用域管理

- Parser 和 Sema 各有独立的作用域链
- Parser：`parse_func` push → `parse_block` push → `parse_stmt` → ... → pop
- Sema：`check_func_decl` push → `infer_type(block)` → ... → pop
- Sema 的 `nlocals` 不会在 pop 时自动清理，需在 `check_func_decl` 入口手动置零

---

## ABI 关键决策（Windows x64）

1. **Struct pass-by-value** (v0.4+)
   - 调用方分配栈拷贝，`cg_copy_struct` 逐字段复制
   - 大于寄存器宽度的字段通过 memory 传递

2. **Struct return via sret** (v0.4+)
   - 调用方分配返回槽，隐式传递指针为第一个参数
   - 被调用方写入后 bare `ret`

3. **Slice layout** (v0.6+)
   - `[*]T` = `{ptr: *T, len: i64}` 共 16 字节
   - 按 struct pass-by-value 走 sret

4. **模块命名 mangle** (v0.6+)
   - 跨模块函数 emit 时 mangle 为 `$mod__name`（如 `$math__factorial`）
   - extern fn 不 mangle（直接 emit 原名给链接器）

完整 ABI 锁定在 `docs/abis/jhyy-abi-v1.0.0.md`。

---

## QBE IL 速查

```
%t0 =w copy 42           # int 常量
%t1 =l copy %t0          # 64-bit 拷贝（必须同类型；跨宽度用 extsw/truncd）
%t2 =l alloc4 16         # 栈分配 16 字节
%t3 =l add %t1, 16       # 指针算术
%t4 =w loadw %t3         # 32-bit load
storew %t0, %t3          # 32-bit store
%t5 =w call $fn(args)    # 函数调用
ret %t0                  # 返回
jnz %t0, @then, @else    # 条件跳转
%t6 =w phi @a %x, @b %y  # phi 节点
```

宽度：
- `b` byte (8-bit)、`h` half (16-bit)、`w` word (32-bit)、`l` long (64-bit)
- `s` single (f32)、`d` double (f64)

类型转换指令：
- `extsw` (i32 → i64)、`extuw` (u32 → u64)、`extsh` (i16 → i64)
- `truncd` (f64 → f32)、`dtosi`/`dtosi`/`stosi`/`sltof`/`swtof`

---

## Stage 0 自举试点

`compiler/jhyy-src/arena.jhyy` 是 `compiler/src/arena.c` 的 JHYY 翻译（v0.6）。

**翻译要点**：
- `size_t → i64`、`void* → *u8`
- varargs (arena_sprintf) 暂不支持
- 自引用 struct 指针用 `*u8 + as *ArenaBlock` 转换
- 指针算术通过 `(ptr as i64 + off) as *u8` 显式表达

测试 driver：`compiler/tests/examples/arena_test/arena_test.jhyy`

验证了 v0.6 编译器对编译自身模块的能力。下一期 v1.0.0 启动完整自举。
