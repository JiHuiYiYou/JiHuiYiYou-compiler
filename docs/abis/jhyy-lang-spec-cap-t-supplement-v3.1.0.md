# jhyy-lang-spec — Cap<T> Supplement (v3.1.0)

> **Supplement 状态**: 锁定 (v3.1.0 ship gate) — 配合 [`../jhyy-lang-spec-v1.3.0.md`](../jhyy-lang-spec-v1.3.0.md) + [borrow-check supplement](jhyy-lang-spec-borrow-check-supplement-v3.1.0.md) 读
> **作者**: JHYY <15901598712@163.com>
> **日期**: 2026-09-06
> **范围**: V3-C v3.1.0 sub-sprint 1/3 (3g) — `Cap<T>` 8 字节 layout

---

## 1. 范围 / Scope

本文档定义 v3.1.0 新增的 `Cap<T>` capability builtin type — 8 字节 layout (cnode_idx + depth + rights + padding)。

完整 CapTable + 跨函数 cap pass 留 **v3.1.2** (3g.7 sub-sprint)。PhantomData<T> ZST 组合留 **v3.1.1** (3g.5)。

---

## 2. 语法 / Syntax

### 2.1 v3.1.0 简化

```jhyy
let c: Cap = make_cap();   // 简化: default inner = i32
```

**v3.1.0 不支持** `Cap<T>` 泛型语法 (parser 阶段不接受 `<T>` in type-position)。`Cap` 视为 builtin ident,`elem` 默认为 `i32`。完整 `Cap<T>` generic 留 v3.1.2。

### 2.2 字段构造 (cnode_idx + depth + rights)

```jhyy
// v3.1.2+ 计划: literal ctor
let c: Cap = cap_new(7 as u32, 2 as u8, 0b11 as u16);  // cnode=7, depth=2, rights=R|W
```

**v3.1.0** 不实现 `cap_new` builtin — 用户用 raw 8-byte integer literal + cast:

```jhyy
// 8-byte integer literal, layout 跟 Cap<T> 一致
let c: Cap = 0x00070002_00000003 as Cap;
```

`cap_new` builtin 留 v3.1.2 (per V3-C plan doc § 6 out-of-scope of v3.1.0)。

---

## 3. 8 字节布局 / 8-byte Layout

### 3.1 字段表

| Offset | Size | Field | Type | Description |
|--------|------|-------|------|-------------|
| 0 | 4 | `cnode_idx` | `u32` | CSpace slot index (e.g. 7) |
| 4 | 1 | `depth` | `u8` | CDL (Capability Distribution Layer) depth |
| 5 | 2 | `rights` | `u16` | Bitmask: 0x1=R, 0x2=W, 0x4=G (grant) |
| 7 | 1 | `padding` | `u8` | Alignment to 8 bytes (zero-initialized) |
| **Total** | **8** | | | **`sizeof(Cap<T>) == 8`** |

### 3.2 内置表示 (Type struct)

```c
// types.jhyy
type Cap = KIND_CAP (value = 11, 新增);
// 内部表示:
//   kind:  KIND_CAP
//   elem:  *Type (inner T — v3.1.0 default i32)
//   size:  8  (硬编码)
//   align: 8  (硬编码)
```

### 3.3 C-side memory representation

```c
// Cap layout in memory (8 bytes, little-endian):
// byte 0: cnode_idx[7:0]
// byte 1: cnode_idx[15:8]
// byte 2: cnode_idx[23:16]
// byte 3: cnode_idx[31:24]
// byte 4: depth (u8)
// byte 5: rights[7:0]
// byte 6: rights[15:8]
// byte 7: padding (u8, 0)
```

### 3.4 字节序

**小端 (little-endian) only**。x86_64 / aarch64 / riscv64 全是小端,大端架构 (s390x / ppc64le 是小端) 留 v3.x 末 swap 处理。

---

## 4. ABI 集成 / ABI Integration

### 4.1 qbe_type_of

```c
qbe_type_of(t) {
    ...
    if (t.kind == KIND_CAP) return QBE_L;  // 8-byte struct pass-by-value
    ...
}
```

### 4.2 ABI classify (Windows x64 MS)

`abi_win_classify_arg`: `Cap<T>` 走 delegate path → `qbe_type_of` → `QBE_L`。MS x64 calling convention: 8-byte struct 走 INTEGER class (RCX/RDX/R8/R9)。

### 4.3 ABI classify (Linux x86_64 SysV) — 留 v3.1.3

**Out of scope v3.1.0**: V2-B v2.7.0 (`abi_amd64_sysv.jhyy`) NOT shipped,`Cap<T>` SysV classification 留 v3.1.3 backport (per V3-C plan doc § 5 + 2026-09-06 user 决定 Windows-only scope)。

---

## 5. codegen 集成

### 5.1 Stack slot

`Cap<T>` 走 8-byte stack slot (per V2-A v2.5.0 no-regalloc convention — `cg_offset_for_temp` 强制 stack-slot)。`Cap<T>` 8 字节刚好对齐到 8-byte slot boundary,无需特殊 padding 处理。

### 5.2 Pass-by-value

```jhyy
fn take_cap(c: Cap) -> i64 {  // c 走 RCX (Win) / RDI (SysV) 8-byte register
    return c.cnode_idx as i64;  // 访问字段
}
```

**v3.1.0 限制**: 不支持 `.cnode_idx` / `.depth` / `.rights` 字段访问 — `Cap` 不是 struct,fields 不可见。完整 field access 留 v3.1.2 (per V3-C plan doc § 6)。

### 5.3 Init / ctor

**v3.1.0 简化**: 用户用 raw 8-byte int literal + cast:

```jhyy
// cnode=7, depth=2, rights=0x3 (R|W), pad=0
//   7 << 0 = 0x07
//   2 << 32 = 0x0000000200000000
//   0x3 << 40 = 0x0000030000000000
//   total = 0x0000030200000007
let c: Cap = 0x0000030200000007 as Cap;
```

---

## 6. 实测 / Tests

### 6.1 sizeof 测试

```jhyy
// compiler/tests/examples/cap_test.jhyy
// SKIP: V3-C 3g feature — jhyy-side only
fn main_jhyy() -> i32 {
    let s_cap: i64 = sizeof(Cap);
    if s_cap == 8 {
        return 42;
    }
    return s_cap as i32;
}
// EXPECT: 42
```

### 6.2 跨函数 pass

```jhyy
// v3.1.2 计划 (out of scope v3.1.0)
fn pass_cap(c: Cap) -> Cap { return c; }
fn main_jhyy() -> i32 {
    let c: Cap = 0x0000030200000007 as Cap;
    let c2: Cap = pass_cap(c);
    return sizeof(Cap) as i32;
}
// EXPECT: 8
```

---

## 7. 跨 sprint 对齐

- **V3-C v3.1.1** (3g.5) — PhantomData<T> ZST (0-byte),`Cap<PhantomData<T>>` 8 字节不变
- **V3-C v3.1.2** (3g.7) — CapTable<T> = `[*]Cap<T>` + `i64 len` (16B),跨函数 cap pass
- **V2-C v2.8.0** (N 代 fixed point) — V3-C 全 ship 后启动,验算 `cap_test.jhyy`
- **V2-B v2.7.0** (amd64_sysv) — `abi_amd64_sysv.jhyy` Cap<T> class backport 到 v3.1.3

---

## 8. 已知限制 / Known Limitations

| 限制 | 留到 |
|------|------|
| `Cap<T>` 泛型语法 `<T>` 不支持 | v3.1.2 |
| `.cnode_idx` / `.depth` / `.rights` 字段访问 | v3.1.2 |
| `cap_new()` builtin ctor | v3.1.2 |
| `Cap<Cap<T>>` 嵌套 | v3.x 中 |
| `PhantomData<&T>` lifetime 参数 | v3.x 中 |
| 大端架构 swap | v3.x 末 |
| `abi_amd64_sysv.jhyy` Cap<T> class | v3.1.3 backport |
