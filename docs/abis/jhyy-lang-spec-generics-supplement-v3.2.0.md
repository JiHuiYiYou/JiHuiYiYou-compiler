# jhyy-lang-spec — Generics (struct/enum) Supplement (v3.2.0)

> **Supplement 状态**: 部分锁定 (v3.2.0 ship gate — parser + AST scaffolding only;
> runtime monomorphize deferred to v3.2.0b per `docs/logs/v3/changelog-v3.2.md` § 6)
> — 配合 [`../jhyy-lang-spec-v1.3.0.md`](../jhyy-lang-spec-v1.3.0.md) +
> [Cap<T> supplement v3.1.0](jhyy-lang-spec-cap-t-supplement-v3.1.0.md) +
> [PhantomData<T> supplement v3.1.1](jhyy-lang-spec-phantomdata-supplement-v3.1.1.md) +
> [borrow-check supplement v3.1.0](jhyy-lang-spec-borrow-check-supplement-v3.1.0.md) 读
> **作者**: JHYY <15901598712@163.com>
> **日期**: 2026-09-08
> **范围**: V3-C v3.2.0 sub-sprint — `type Foo<T>` 语法 + `Foo<i32>` 引用语法

---

## 1. 范围 / Scope

本文档定义 v3.2.0 新增的 **generic struct/enum 语法 + AST/sema scaffolding** —
runtime monomorphize 推到 **v3.2.0b**(per `docs/logs/v3/changelog-v3.2.md` § 6)。

**当前 ship 状态**:
- ✅ Parser 接受 `type Foo<T>` 声明 + `Foo<i32, i64>` 引用语法
- ✅ AST 节点 `NodeTypeDecl` 加 `type_params` / `ntype_params` 字段
- ✅ Sema Pass 1.5 hook 就位(Pass 1 → Pass 2 之间)
- ✅ Sema Pass 2/3 skip generic def(`ntype_params > 0`)
- ✅ E0060:bare `T` in non-generic scope 报错路径
- ❌ Runtime monomorphize(无 per-inst 类型实例化)— 推到 v3.2.0b

**触发**:
- M8d launch 硬前置 1/N 满足(compositor generic over T)
- M11 launch 硬前置解锁(`Vec<T>` / `Map<K,V>` std lib 依赖)
- v3.2.0b (fn + turbofish) 启动前置
- V2-C v2.8.0 N 代 fixed point 跨 axis 验算前置

---

## 2. 语法 / Syntax

### 2.1 v3.2.0 完整语法

```jhyy
// Generic struct
type Pair<T> = struct {
    a: T,
    b: T,
}

// Generic struct with pointer field (generic-on-pointer)
type Vec<T> = struct {
    data: *T,
    len: i32,
    cap: i32,
}

// Multi type-param
type Map2<K, V> = struct {
    key: K,
    val: V,
}

// Generic enum
type Option<T> = enum {
    Some(T),
    None,
}

// Reference syntax (must use uppercase A-Z name by convention)
let p: Pair<i32> = Pair<i32> { a: 1, b: 2 };
let v: Vec<i64> = Vec<i64> { data: 0 as *i64, len: 0, cap: 0 };
let m: Map2<i32, i64> = Map2<i32, i64> { key: 1, val: 2 as i64 };
```

### 2.2 语法规则

1. **type-param 列表**:`<T>` 或 `<T, U, V>` — 0+ 个 type-param
2. **type-param 名**:大写 A-Z 起始(PascalCase by convention);小写首字母当 IDENT
   parse 时优先走变量查找,不进 generic arm(避免 `n < 2` 跟 `Vec<n>` 冲突)
3. **引用语法**:`<T1, T2, ...>` — type 位置出现于 `let x: Foo<i32>` / 字段类型 /
   函数参数类型 / 函数返回类型
4. **mangled name 规则**:`Name$arg1$arg2$...`,`$` 分隔符,跟现有 `mod__name`
   不冲突(per [`jhyy-abi-v1.0.0.md`](../jhyy-abi-v1.0.0.md) § name mangling)
5. **不能嵌套 v3.2.0**:`Vec<Vec<T>>` → 报 E0061 nested generic not supported
   (留 v3.x 中)
6. **不能 bounds v3.2.0**:`<T: Ord>` → 不识别 (留 v3.x 末)

### 2.3 不允许的语法 (M0 简化)

```jhyy
let x = foo::<i32>(3, 5);   // ❌ turbofish 留 v3.2.0b
let y = max(3, 5);          // ❌ generic fn 留 v3.2.0b
type Bad = Vec<Vec<T>>;     // ❌ E0061: nested generic not supported
type Bad2<T: Ord> = ...;    // ❌ bounds 留 v3.x 末
fn bad<T>() -> T { ... }    // ❌ generic fn 留 v3.2.0b
```

---

## 3. 错误码 / Error codes

| Code | 触发 | 行为 |
|------|------|------|
| **E0060** | bare type-param `T` in non-generic scope(出现在 non-generic type 位置) | error recovery:返回 `i32` 占位 type,继续 sema 跑后续检查 |
| **E0061** | nested generic `Vec<Vec<T>>` 或 `Vec<Pair<i32>>` | error recovery:inner generic 当 `i32` 处理,继续 |

---

## 4. ABI / Type layout

### 4.1 不动 Type struct

`Type` struct 在 v3.2.0 **完全不变** — 没有 `type_args` 字段:
- `Type` 字节数 168B → 168B(per `types.jhyy` v3.1.1)
- `KIND_*` 常量不变(per `types.jhyy`)
- `type_eq` / `type_size` / `qbe_type_of` 不变

**理由**:monomorphize 走 name-based source cloning(每条 instantiation 是
independent `*Sym` + 独立 cloned AST),不走 `Type` 的 `args` 字段。
加 `type_args` → TYPE_SIZE 变 → ABI 全 touch → D43 closure 必破。

### 4.2 AST 节点扩展

#### NodeTypeDecl(16 → 32 bytes)

```jhyy
type NodeTypeDecl = struct {
    sym:          *u8,    // *Sym (generic def 时是 base_name sym; cloned decl 是 mangled sym)
    body:         *u8,    // *Node (struct/enum 定义)
    type_params:  *u8,    // **Sym 数组 (NULL + ntype_params==0 表示 non-generic)
    ntype_params: i64,    // type-param 数
}
```

#### NodeModule(24 → 40 bytes)

```jhyy
type NodeModule = struct {
    decls:           *u8,    // **Node 数组(顶层 decls)
    ndeccls:         i64,
    is_no_std:       i32,    // 1 if file has `#[no_std]` module attr
    generic_insts:   *u8,    // *GenericInstRecord 数组(NULL + n==0 表示无 inst)
    ngeneric_insts:  i64,    // generic-inst record 数
}
```

#### GenericInstRecord(32 bytes,NEW)

```jhyy
type GenericInstRecord = struct {
    mangled_name: *u8,    // c 字符串,e.g. "Pair$i32"
    arg_types:    *u8,    // **Node 数组(parser 解析的 type-arg AST nodes)
    nargs:        i64,
    base_name:    *u8,    // 原始 generic name,e.g. "Pair"(Pass 1.5 反查 td_sym 用)
}
```

### 4.3 name mangling 规则

- **format**:`BaseName$arg1$arg2$...`,`$` 分隔符
- **arg encoding**:每个 type-arg 走 `parser_mangle_type_node`(递归 AST type node)
  - primitive `i32` → `i32`
  - IDENT `i64` → `i64`
  - UNARY `*T` → `*<inner>` (e.g. `*i32`)
  - nested generic 不支持 v3.2.0
- **确定性**:mangled_name 由 parser 用 source-order 拼,**无 pointer/hash
  顺序**(per D43 closure 要求)
- **dedupe**:Pass 1.5 按 mangled_name 查 symtab;已存在 + `type_ptr != 0` → skip
- **示例**:
  - `Pair<i32>` → `Pair$i32`
  - `Vec<i64>` → `Vec$i64`
  - `Map2<i32, i64>` → `Map2$i32$i64`

### 4.4 Symbol 表示

`Sym` struct 不变(56 bytes)。type-param 走 **`SYM_TYPE` + `type_ptr=0` 哨兵**:
- `Sym.name` = type-param 名(e.g. "T")
- `Sym.kind` = `SYM_TYPE`
- `Sym.type_ptr` = 0(sentinel)

scope chain(parent → global)让 parser 在 body parse 时能找到 type-param sym。

---

## 5. Sema 集成 / Sema integration

### 5.1 Pass 1 — register decls

- 遍历 `(*md).decls`,对每个 `NODE_TYPE_DECL`:
  - generic def (`ntype_params > 0`):insert sym `name = base_name`(e.g. "Pair")
  - cloned decl (`ntype_params == 0`):insert sym `name = mangled_name`(e.g. "Pair$i32")
  - 两 path 都走 `symtab_insert` 若 `symtab_lookup` 没找到

### 5.2 Pass 1.5 — monomorphize

调用 `mono_expand_module((*ctx).global_scope, (*ctx).arena, md)`:
- 遍历 `(*md).generic_insts`
- 对每条 inst:
  - dedupe by mangled_name → skip if already in symtab
  - 找到 base_name 对应的 generic def
  - 克隆 struct/enum body + 替换 type-param sym 为 arg nodes
  - 注册 mangled sym + 替换 cloned decl sym field
  - append cloned decl 到 `(*md).decls`
- **v3.2.0 ship 状态:NO-OP**(`return 0` per changelog § 6)

### 5.3 Pass 2 — layout type decls

```jhyy
if (*td).ntype_params > (0 as i64) {
    // v3.2.0: generic def 不 layout
    i2 = i2 + (1 as i64);
} else {
    // 正常 struct/enum layout 路径
    ...
}
```

### 5.4 Pass 3 — typecheck exprs

- 引用 `Foo<i32>` 的 IDENT sym 已经被 parser 设成 mangled name
- `resolve_type_node` 走 `symtab_lookup(current_scope, mangled_name)` → 命中
  cloned decl 的 sym(type_ptr 在 Pass 2 后已 set)

### 5.5 E0060 fall-through

`resolve_type_node` NODE_IDENT 分支:

```jhyy
if looked != (0 as *Sym) {
    if (*looked).kind == SYM_TYPE() {
        if (*looked).type_ptr == (0 as *u8) {
            // E0060: type-param 哨兵 — 用户写 unsubstituted `T` in non-generic scope
            let _x = sema_error_str(ctx, ...,
                "E0060: unresolved type parameter; generic must be instantiated");
            return type_primitive(ta, PRIM_I32());  // error recovery
        }
    }
}
```

---

## 6. Codegen 集成 / Codegen integration

### 6.1 不改 codegen

`codegen.jhyy` 4192 行 — **0 改动**。

理由:Pass 1.5 append 的 cloned decl 是 `ntype_params == 0` 的 normal struct/enum
decl,走 codegen 现有 struct/enum emit 路径。

### 6.2 不改 abi_amd64_win

`abi_amd64_win.jhyy` — **0 改动**。Cloned struct 的 layout 跟普通 struct
完全相同(size + alignment 走现有规则)。

---

## 7. 不允许的语义 / Disallowed semantics (M0 简化)

| 行为 | 状态 |
|------|------|
| `type Foo<T> = struct { ... }; let x: Foo = ...` (用 generic def 当 type) | ❌ Pass 2 skip,Pass 3 报 E0060(bare `Foo` 不存在 layout,only `Foo<i32>` 存在) |
| `type Foo<T> = struct { x: T }; let y: Foo<i32> = Foo { x: 1 }` (省略 `<i32>`) | ❌ parser 报 syntax error(struct literal `<>` 不能省) |
| `let x = foo::<i32>(3, 5)` turbofish | ❌ 留 v3.2.0b |
| `fn max<T>(...)` generic fn | ❌ 留 v3.2.0b |
| `Vec<Vec<T>>` nested | ❌ E0061 |
| `<T: Ord>` bounds | ❌ 不识别 |

---

## 8. Cross-ref

- 主规范:`docs/abis/jhyy-lang-spec-v1.3.0.md`
- ABI:`docs/abis/jhyy-abi-v1.0.0.md`
- Cap<T>:[`jhyy-lang-spec-cap-t-supplement-v3.1.0.md`](jhyy-lang-spec-cap-t-supplement-v3.1.0.md)
- PhantomData<T>:[`jhyy-lang-spec-phantomdata-supplement-v3.1.1.md`](jhyy-lang-spec-phantomdata-supplement-v3.1.1.md)
- Borrow:[`jhyy-lang-spec-borrow-check-supplement-v3.1.0.md`](jhyy-lang-spec-borrow-check-supplement-v3.1.0.md)
- Changelog:`docs/logs/v3/changelog-v3.2.md`
- Plan:`docs/plans/v3/v3.2.0-plan.md`

---

## 9. 历史 / History

| 版本 | 日期 | 改动 |
|------|------|------|
| v3.2.0 | 2026-09-08 | 本版(parser + AST + sema scaffolding;runtime defer v3.2.0b) |

---

## 10. 待 v3.2.0b 解锁 / Pending v3.2.0b

- `mono_expand_module` runtime 激活
- generic fn `fn max<T>(...)`
- turbofish `name::<T>(...)`
- 调用点 T 推断 `let x = max(3, 5)`
- `CapTable<T>` 真 generic 重构(`*Cap<T>` layout 实装)
