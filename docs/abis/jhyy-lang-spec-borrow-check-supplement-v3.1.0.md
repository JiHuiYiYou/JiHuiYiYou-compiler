# jhyy-lang-spec — Borrow Check Supplement (v3.1.0)

> **Supplement 状态**: 锁定 (v3.1.0 ship gate) — 配合 [`../jhyy-lang-spec-v1.3.0.md`](../jhyy-lang-spec-v1.3.0.md) 读
> **作者**: JHYY <15901598712@163.com>
> **日期**: 2026-09-06
> **范围**: V3-C v3.1.0 sub-sprint 1/3 (3g)

---

## 1. 范围 / Scope

本文档定义 v3.1.0 新增的 `&T` / `&mut T` 借用类型语法 + 类型系统集成 + NLL 借用检查(简化版)。

完整 NLL (Non-Lexical Lifetimes) / Polonius 留 **v3.x 末**(per V3-C plan doc § 6 out-of-scope)。当前 ship-gate 实现 **类型解析 + 8-byte layout + linear-scope simplification**,**不**检测 active-borrow 冲突(留 v3.x 末)。

---

## 2. 语法 / Syntax

### 2.1 类型位置 (type position)

`&` 是 **type qualifier prefix**,必须出现在 type-annotation 上下文:

```jhyy
let x: &i32 = ...;            // shared borrow of i32
let mut y: &mut i32 = ...;    // exclusive borrow of i32
fn foo(p: &Cap) -> &i32 { ... }  // function param + return
```

解析规则:

1. `&` 后面 **必须** 跟一个 type(`mut` 关键字 optional)
2. `&mut` 表示 **exclusive borrow** (`is_mut = 1`)
3. `&` 表示 **shared borrow** (`is_mut = 0`)
4. 不支持 chained `&&T` — 借用是 terminal type
5. **不支持** lifetime `'a` 标注 (tokenizer 阶段无 tick token; 留 v3.x 中)
6. **不支持** `&volatile T` / `volatile &T` 组合 (volatile 强制 fresh temp, 借用必须 persist)

### 2.2 表达式位置 (expression position)

`&expr` 在表达式上下文 **保留** v1.x 语义(产生 POINTER `*T`),**不**自动 coerce 为 borrow type。完整 borrow-expr semantics 留 v3.x 末。

```jhyy
let x: i32 = 42;
let p: *i32 = &x;  // v1.x 语义: &x 产生 *i32 (POINTER), 走 type_pointer
```

**Out of scope v3.1.0**: `let y: &i32 = &x` (rhs 必须是 borrow expr, 但 v3.1.0 不实现) — 此组合编译失败 (`type mismatch in let`)。完整 borrow-coercion 留 v3.x 末。

---

## 3. 类型系统 / Type System

### 3.1 KIND_REF

`Type.kind = KIND_REF` (值 = 10, 新增)。`is_mut` 字段标识 `&mut` vs `&`。

```c
// C-side struct 字段 (Type, 168 bytes):
//   kind:         i32   // = KIND_REF
//   elem:         *u8   // *Type (inner T)
//   is_mut:       i32   // v3.1.0: 1 = &mut, 0 = &
//   _pad_mut:     i32   // alignment pad
```

### 3.2 Layout

`sizeof(&T) == 8` on all targets (single pointer, same as POINTER).`is_mut` 不影响 size (编译器内部 metadata, 不进 QBE IL)。

### 3.3 type_eq

```c
type_eq(&T1, &T2) {
    if (a.is_mut != b.is_mut) return false;  // &T vs &mut T 是 distinct
    return type_eq(a.elem, b.elem);          // inner 类型递归
}
```

### 3.4 type_size / type_align

- `type_size(&T) == 8`
- `type_align(&T) == 8`

### 3.5 type_to_string

- `&T` (is_mut=0) → 返回 `"&"`
- `&mut T` (is_mut=1) → 返回 `"&mut"`
- 完整 `&T` 字符串(`&i32`, `&mut Foo`)留 v3.x 中 (需递归 elem 拼接)

---

## 4. NLL 借用检查 (简化版)

**当前 v3.1.0 实现是 STUB**。完整 NLL 留 v3.x 末。

### 4.1 已知限制 (留 v3.x 末)

| 限制 | 留到 |
|------|------|
| `&mut x` + `&mut x` 双 mutable 冲突不检测 | v3.x 末 (Polonius) |
| `&mut` + `&` shared/mutable 互斥不检测 | v3.x 末 |
| reborrow `&mut *x` 路径 | v3.x 末 |
| lifetime 子类型 / variance | v3.x 末 |
| 跨函数 borrow | v3.x 末 |
| nested block 借用作用域 | v3.x 末 |
| path-based NLL (NLL2 算法) | v3.x 末 |
| escape analysis (借用是否 leak) | v3.x 中 |

### 4.2 check_borrow stub

`check_borrow()` 当前直接 `return 1`,不检测任何 active-borrow 冲突。**借用类型本身** (NODE_REF_TYPE arm in `resolve_type_node`) **已经正确解析** + 8-byte layout 已锁定,所以:

- ✅ `&T` / `&mut T` 编译通过
- ✅ `sizeof(&T) == 8`
- ✅ 跨函数 `&T` pass-by-value (8-byte ptr, 走 64-bit register)
- ❌ 双 mutable 借用不报错 (留 v3.x 末)
- ❌ shared/mutable 互斥不报错 (留 v3.x 末)

### 4.3 设计原则

v3.1.0 ship-gate 优先 **类型系统 + ABI 集成**,**借用检查延迟**到后续 sprint。理由:

- jhyy_OS M4 launch 强前置 `&mut T` (内核锁 mutable reference)
- 内核用 `&mut` 的场景:单线程 short-lived, NLL 检查不强需
- M4 launch 之后再补全 NLL 不阻塞 OS 启动
- v3.x 末 Polonius-style 全 NLL 是语言完整化的最后一步

---

## 5. codegen 集成

### 5.1 qbe_type_of

```c
qbe_type_of(t) {
    ...
    if (t.kind == KIND_REF) return QBE_L;  // 8-byte ptr
    if (t.kind == KIND_CAP) return QBE_L;  // 8-byte struct pass-by-value
    ...
}
```

### 5.2 QBE_BORROWED_MARKER

```c
// codegen_amd64_state.jhyy
fn QBE_BORROWED_MARKER() -> i32 { return -2 as i32; }
```

区别 volatile (`-1`): volatile 每次 load fresh temp; borrowed 是单 ptr 复用 (类似 POINTER)。`qbe_type` 仍写 `'l'` (8-byte ptr),marker 供 codegen 阶段 metadata 区分。

### 5.3 ABI classify (Windows x64)

`abi_win_classify_arg` 走 delegate path — `&T` / `Cap<T>` 都返回 `QBE_L` (8-byte INTEGER class per MS x64 calling convention)。

---

## 6. 实测

### 6.1 sizeof 测试

```jhyy
fn main_jhyy() -> i32 {
    let s_ref: i64 = sizeof(&i32);
    let s_cap: i64 = sizeof(Cap);
    if s_ref == 8 {
        if s_cap == 8 {
            return 42;
        }
    }
    return 0 as i32;
}
// EXPECT: 42
```

### 6.2 双 mutable 借用 (留 v3.x 末)

```jhyy
let mut x = 42;
let y = &mut x;
let z = &mut x;  // v3.1.0: NOT detected; v3.x 末: error
```

---

## 7. 跨 sprint 对齐

- **V3-C v3.1.1** (3g.5) — PhantomData<T> ZST,`Cap<PhantomData<T>>` 组合
- **V3-C v3.1.2** (3g.7) — CapTable<T> + 跨函数 cap pass
- **V2-C v2.8.0** (N 代 fixed point) — V3-C 全 ship 后启动,验算 `cap_test.jhyy`
- **V2-B v2.7.0** (amd64_sysv 实 impl) — `abi_amd64_sysv.jhyy` Cap<T> class backport 到 v3.1.3
