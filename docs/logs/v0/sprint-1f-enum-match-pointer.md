# Sprint 1f — Enum / Match / Pointer / Struct / For / Arena

**日期**: 2026-06-05  
**状态**: 完成

## 成果

完善了类型系统、语义分析和代码生成，实现了指针操作、结构体、枚举、match 表达式、for 循环等核心语言特性。

---

## 新增 AST 节点

| 节点 | 用途 |
|------|------|
| `NODE_STRUCT_DEF` | `struct { field: Type, ... }` — 类型定义体 |
| `NODE_ENUM_DEF` | `enum { Variant(Type), ... }` — 类型定义体 |

对应数据结构: `StructFieldDecl` (name + type_annot), `NodeStructDef`, `EnumVariantDecl` (name + payload_type), `NodeEnumDef`

---

## Parser 改进

### 1. `parse_type_decl` — 完整解析

**修改前**: 跳过 struct/enum 体，仅插入占位符。

**修改后**: 
- **struct**: 解析 `name: Type` 字段列表 (逗号分隔)
- **enum**: 解析 `VariantName` 或 `VariantName(Type)` 变体列表 (逗号分隔)
- **类型别名**: `type Name = OtherType`

### 2. `prefix_ident` — struct 字面量 & enum 构造

```jhyy
// struct 字面量 (仅当 sym->kind == SYM_TYPE 时触发)
let p = Point { x: 10, y: 20 };

// enum 变体构造 (仅当 sym->kind == SYM_TYPE 时触发)
let opt = Option::Some(42);
```

**关键**: 用 `sym->kind == SYM_TYPE` 守卫，避免将 while 条件中的 `{` 误判为 struct 字面量。

### 3. `parse_pattern` — 通配符 `_` 修正

`_` 在 lexer 中产生 `TOKEN_IDENT` (非 `TOKEN_STAR`)，需在 `TOKEN_IDENT` 分支中单独检测。

### 4. `parse_block` — 数组扩容 bug 修复

**Bug**: stmts 数组扩容时分配新内存但**未复制旧条目**。当 block 中超过 8 条语句时，前 8 条丢失，导致 SIGSEGV。

**修复**: 使用 `memcpy` 保留旧数据。

---

## Semantic Analysis 改进

### `SemaLocal` 改用 Sym 指针匹配

```c
typedef struct {
    Sym  *sym;   // 主匹配: 指针比较
    Type *type;
} SemaLocal;
```

查找顺序:
1. `d->sym->type` 直接检查 (函数类型提前设置)
2. locals[] Sym 指针匹配
3. locals[] name 字符串匹配 (P0 hash 表 bug 的 fallback)

### 新增类型推断

| 节点 | 推断逻辑 |
|------|---------|
| `NODE_STRUCT_LIT` | 查找类型符号 → 检查字段存在性与类型 → 返回 struct type |
| `NODE_ENUM_VARIANT` | 查找 enum 类型 → 检查变体存在性 → 检查 payload 类型 → 返回 enum type |
| `NODE_MATCH` | 推断被匹配表达式类型 → 检查所有 arm body 类型一致性 → 返回共同类型 |
| `NODE_FOR` | 推断 start/end 类型 → 注册循环变量到 locals → 推断 body |
| `NODE_FIELD` (pointer) | 自动解引用指针 → 查找 struct 字段偏移 → 返回字段类型 |

### `check_module` 三遍处理

```
Pass 1: 注册声明 (函数名 + 类型名)
Pass 2: 解析类型定义 (struct/enum → Type 对象，计算字段偏移、大小、对齐)
Pass 3: 检查函数体和顶层语句
```

**布局计算**:
- **struct**: 字段按对齐排列，自动计算 offset/size/align
- **enum**: tag (i32, 4 字节) + payload (最大变体对齐)，自动计算 total_size

---

## Codegen 改进

### 新增表达式代码生成

#### NODE_UNARY (`-`, `!`, `~`)

```
-x  →  sub 0, %x
!x  →  ceqw %x, 0
~x  →  xor %x, -1
```

**修复**: 此前缺失导致 `%t0` (id=0) 跨函数引用 QBE 报错。

#### NODE_ADDR_OF (`&x`)

返回 mutable 变量的栈槽地址 (ptr type `l`)。仅支持栈分配变量。

#### NODE_DEREF (`*ptr`)

```
%result =w loadw %ptr
```

#### NODE_STRUCT_LIT

```
alloc8 <total_size>           // 分配栈空间
%addr =l add %slot, <offset>  // 计算字段地址
storew %field_val, %addr      // 存储字段值
```

#### NODE_ENUM_VARIANT

```
alloc8 <total_size>              // 分配栈空间
storew <tag>, %slot              // 存储 tag (i32)
%payload_addr =l add %slot, 4    // 计算 payload 地址
storew %payload_val, %payload_addr
```

#### NODE_MATCH

```
%val = cg_expr(expr)                        // 被匹配值

// arm 0: 字面量模式
%cmp0 =w ceqw %val, <lit0>
jnz %cmp0, @arm0, @next0

// arm 1: 字面量模式
@next0:
%cmp1 =w ceqw %val, <lit1>
jnz %cmp1, @arm1, @next1

// arm 2: 通配符
@next1:
jmp @arm2

// body blocks
@arm0: %r0 = ...; jmp @merge
@arm1: %r1 = ...; jmp @merge
@arm2: %r2 = ...; jmp @merge

// phi 汇合
@merge:
%result =w phi @arm0 %r0, @arm1 %r1, @arm2 %r2
```

支持模式: `NODE_PATTERN_LIT` (字面量), `NODE_PATTERN_WILD` (通配符 `_`), `NODE_PATTERN_RANGE` (范围 `lo..hi`)

#### NODE_FIELD (指针自动解引用 + 结构体值)

```
// 指针到结构体: ptr->field
%addr =l add %ptr, <offset>
%val =w loadw %addr

// 结构体值: struct.field
%addr =l add %base, <offset>
%val =w loadw %addr
```

#### NODE_FOR

```
alloc4 4                       // 循环变量栈槽
storew %start, %slot
jmp @loop_hdr

@loop_hdr:
%i =w loadw %slot              // 加载循环变量
%cond =w csltw %i, %end         // i < end
jnz %cond, @body, @exit

@body:
... body code ...

// 递增
%i2 =w loadw %slot
%next =w add %i2, 1
storew %next, %slot
jmp @loop_hdr

@exit:
```

### NODE_ASSIGN 支持解引用目标

```
*ptr = value  →  storew %value, %ptr
```

---

## 测试验证

### 端到端测试

| 测试文件 | 退出码 | 测试内容 |
|---------|-------|---------|
| `pointer.jhyy` | 100 | `&x`, `*p = 100` |
| `struct.jhyy` | 30 | struct 定义 + 字面量 + 字段访问 |
| `match.jhyy` | 20 | match 表达式 (字面量 + 通配符) |
| `forloop.jhyy` | 10 | for 循环 (0+0+1+2+3+4) |
| `demo.jhyy` | 0 | 全部 v0.0.1 特性回归测试 |
| `hello.jhyy` | 42 | 基础流水线 |

### 修复的 Bug (v0.0.1 → v0.0.2)

| Bug | 严重度 | 修复 |
|-----|--------|------|
| parse_block 数组扩容丢失数据 | P0 | memcpy 保留旧条目 |
| NODE_UNARY 返回空 IRVal 导致跨函数 temp 引用 | P0 | 添加 NODE_UNARY cg_expr |
| `_` 通配符未识别为 PATT_WILD | P1 | TOKEN_IDENT 中检测 `_` |
| body_returns 检测未穿透 NODE_BLOCK | P1 | 检查 NODE_BLOCK 最后一条语句 |
| struct/enum 关键字未按 TOKEN_STRUCT/TOKEN_ENUM 处理 | P1 | parse_type_decl 改用关键字 token |

### 已知遗留问题

- **P0**: 符号表 hash 查找不稳定 (sema 使用线性 locals[] 规避)
- **P1**: Windows `jhyy run` 的 system() 调用失败 (路径分隔符问题)
- **P2**: enum payload 在 codegen 中的偏移计算与 sema 布局可能不一致
- **P3**: struct 字段写入通过指针未完整测试
- **P4**: Arena API 作为 extern 函数可用但未完整集成测试
