# Sprint 1b — 数据结构 (AST + 类型系统 + 符号表 + Arena)

**日期**: 2026-06  
**状态**: 完成

## 成果

实现了编译器的核心数据结构：AST、类型系统、符号表、竞技场分配器。

### 文件

- `compiler/src/ast.h` / `ast.c` — AST 节点定义 (35 种节点类型)
- `compiler/src/types.h` / `types.c` — 类型表示与操作
- `compiler/src/symtab.h` / `symtab.c` — 符号表 (作用域链)
- `compiler/src/arena.h` / `arena.c` — Bump allocator

### AST 节点 (35 种)

Tagged union 设计，每种节点有对应数据 struct 和构造函数/访问器：

```
字面量: NODE_INT, NODE_FLOAT, NODE_STRING, NODE_CHAR, NODE_BOOL
表达式: NODE_IDENT, NODE_UNARY, NODE_BINARY, NODE_CALL, NODE_FIELD, NODE_INDEX
        NODE_CAST, NODE_SIZEOF, NODE_ALIGNOF, NODE_ADDR_OF, NODE_DEREF
语句:   NODE_BLOCK, NODE_IF, NODE_WHILE, NODE_FOR, NODE_LET, NODE_ASSIGN
        NODE_RETURN, NODE_EXPR_STMT
模式匹配: NODE_MATCH, NODE_MATCH_ARM, NODE_PATTERN_LIT, NODE_PATTERN_IDENT
          NODE_PATTERN_ENUM, NODE_PATTERN_RANGE, NODE_PATTERN_OR, NODE_PATTERN_WILD
结构体/枚举: NODE_STRUCT_LIT, NODE_ENUM_VARIANT, NODE_STRUCT_DEF, NODE_ENUM_DEF
声明:   NODE_FUNC_DECL, NODE_TYPE_DECL, NODE_EXTERN_DECL, NODE_IMPORT_DECL
顶层:   NODE_MODULE
```

### 类型系统

| 类型 | 大小 | 说明 |
|------|------|------|
| i8/i16/i32/i64 | 1/2/4/8B | 有符号整数 |
| u8/u16/u32/u64 | 1/2/4/8B | 无符号整数 |
| f32/f64 | 4/8B | 浮点 |
| bool | 1B | true/false |
| *T | 8B | 指针 |
| [*]T | 16B | 切片 (ptr+len) |
| [T; N] | N×sizeof(T) | 定长数组 |
| struct | 字段之和 | 结构体 (nominal equality) |
| enum | tag(4B)+payload | 带标签联合体 (nominal equality) |
| () | 0B | unit/void |

API: `type_size()`, `type_align()`, `type_eq()`, `type_to_string()`

### 符号表

- 链表式作用域 (parent 指针)
- FNV-1a hash, 256 桶
- 符号类型: `SYM_VAR`, `SYM_FN`, `SYM_TYPE`, `SYM_FIELD`, `SYM_VARIANT`, `SYM_MODULE`
- 支持递归查找 (`symtab_lookup`) 和遮蔽 (同深度拒绝重复)

### Arena Allocator

- Bump allocator, 默认 block 1MB
- Block chaining 处理大分配
- `arena_alloc()`, `arena_alloc_aligned()`, `arena_calloc()`, `arena_strdup()`, `arena_sprintf()`

### 已知问题 (P0)

- FNV-1a hash 表在 10+ 条目时查找不稳定，sema 使用线性 locals[] 数组规避

### 测试

- `compiler/tests/unit/test_sprint1b.c`: 50 项通过
