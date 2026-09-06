# jhyy-lang-spec — PhantomData<T> Supplement (v3.1.1)

> **Supplement 状态**: 锁定 (v3.1.1 ship gate) — 配合 [`../jhyy-lang-spec-v1.3.0.md`](../jhyy-lang-spec-v1.3.0.md) + [Cap<T> supplement v3.1.0](jhyy-lang-spec-cap-t-supplement-v3.1.0.md) + [borrow-check supplement v3.1.0](jhyy-lang-spec-borrow-check-supplement-v3.1.0.md) 读
> **作者**: JHYY <15901598712@163.com>
> **日期**: 2026-09-06
> **范围**: V3-C v3.1.1 sub-sprint 2/3 (3g.5) — `PhantomData<T>` 0 字节 ZST type marker

---

## 1. 范围 / Scope

本文档定义 v3.1.1 新增的 `PhantomData<T>` 类型 — 0 字节 layout (ZST),只占 type 表项不占 struct layout slot,不允许实例化 (M0 简化)。为后续 v3.2.0 generics 类型参数推导做语法 + 类型层准备 (e.g. `Vec<T>` 等容器类型需要 PhantomData<T> 持有 T 但不存 T)。

**D27 锁**:本 sub-sprint 必须在 v3.1.0 (Cap<T>) ship 后启动。

完整 `CapTable<T>` + 跨函数 cap pass 留 **v3.1.2** (3g.7 sub-sprint)。`PhantomData<&T>` lifetime 参数留 **v4.3.0** (Polonius + lifetime 完整版)。

---

## 2. 语法 / Syntax

### 2.1 v3.1.1 完整语法

```jhyy
struct Wrapper {
    _marker: PhantomData<i32>,   // type-level marker, 不占 struct slot
    val: i32,
}
```

**规则**:
- `PhantomData<T>` 必须带 `<T>`,`PhantomData` 单独出现 → sema 报 unresolved type。
- inner T 可任意合法 type(primitive/struct/ptr/slice/ref/Cap 等)。
- 不允许嵌套 `PhantomData<PhantomData<X>>`(M0 简化),留 v3.x 中。

### 2.2 不允许的语法 (M0 简化)

```jhyy
let p = PhantomData<i32>();      // ❌ E0050: cannot instantiate PhantomData<T>
let q: PhantomData<i32> = PhantomData<i32> {};  // ❌ E0050: cannot instantiate PhantomData<T>
PhantomData<i32> { };            // ❌ E0050: cannot instantiate PhantomData<T>

let _m: PhantomData<i32>;        // ✅ 字段声明合法 (sema 不报错)
```

错误信息统一为 `E0050: cannot instantiate PhantomData<T> (use as type-level marker only)`。

---

## 3. 0 字节布局 / 0-byte ZST Layout

### 3.1 字段表

| Offset | Size | Field | Type | Description |
|--------|------|-------|------|-------------|
| (无) | 0 | — | — | ZST: 无字段,无 layout slot |

**`sizeof(PhantomData<T>) == 0`**(任意 inner T),`alignof(PhantomData<T>) == 1`。

### 3.2 内置表示 (Type struct)

```c
// types.jhyy (v3.1.1 新增)
type PhantomData<T> = KIND_PHANTOM (value = 12);
// 内部表示:
//   kind:  KIND_PHANTOM
//   elem:  *Type (inner T — 用于 type_eq 结构等比)
//   size:  0   (硬编码,ZST invariant)
//   align: 1   (硬编码,不影响 struct 对齐)
```

### 3.3 为什么 size=0/align=1 硬编码而非计算

ZST invariant 是 `PhantomData<T>` 类型的核心语义 — 不论 inner T 如何变化,PhantomData 必须保持 0 字节布局(否则"marker"语义失效)。硬编码 size=0/align=1 简洁且语义明确;若 inner 变化需更新 size,反而违背 marker 设计意图。

### 3.4 type_eq 行为

`PhantomData<i32>` ≠ `PhantomData<u64>`(结构等比,跟 KIND_CAP 同型)。便于:
```jhyy
struct Foo<T> {
    _marker: PhantomData<T>,
    val: T,
}
```

---

## 4. ABI 集成 / ABI Integration

### 4.1 codegen emit (ZST skip)

PhantomData 字段在 codegen 层**不 emit 任何 IR**(per codegen.jhyy:cg_copy_struct line 654 早期 continue)。理由:

- QBE 不支持 0-size `allocN 0`(per spec § 11)
- struct layout 阶段 (sema.jhyy:2166-2193) 天然支持 0-size 字段:offset 不推进,max_align 不变
- codegen 层 early continue 避免浪费 tmp 分配

### 4.2 Cap<PhantomData<X>> 组合

**v3.1.1 限制**:`Cap<T>` 泛型语法 parser 阶段不支持 (留 v3.1.2)。本 sprint 仅验证:
- `Cap` (非泛型) sizeof = 8 (v3.1.0 已 ship,本 sprint 不变)
- struct 中 `cap: Cap` 字段 + `_marker: PhantomData<i32>` 字段组合 layout 正确 (per `cap_phantom_combo.jhyy` 测试)

完整 `Cap<PhantomData<u32>>` 嵌套组合测试留 v3.1.2 (3g.7) 引入 `Cap<T>` generic syntax 后。

### 4.3 qbe_type_of

```c
qbe_type_of(t) {
    ...
    if (t.kind == KIND_PHANTOM) return QBE_W;  // 防御 arm,well-formed 程序不会触发
    ...
}
```

---

## 5. codegen 集成

### 5.1 cg_copy_struct 跳过 PhantomData 字段

```c
while i < nfields {
    ...
    if (*ftype).kind == KIND_PHANTOM() {
        i = i + (1 as i64);
        continue;   // v3.1.1: ZST 字段不 emit IR
    }
    // 否则走正常 src_off/dst_off + load/store 路径
    ...
}
```

### 5.2 sema 禁实例化 (3 个检查点)

| 检查点 | sema.jhyy 位置 | 触发条件 |
|--------|----------------|----------|
| `NODE_LET` | post-line 1305 | `decl_type.kind == KIND_PHANTOM && init != null` |
| `NODE_CALL` | post-line 954 | `callee_type.kind == KIND_PHANTOM` |
| `NODE_STRUCT_LIT` | post-line 1578 | `t.kind == KIND_PHANTOM`(在 `t.kind == KIND_STRUCT` 检查前)|

### 5.3 parser PhantomData<T> 识别

```c
parser.jhyy parse_type (post-line 509):
if strcmp(name, "PhantomData") == 0 {
    if peek.kind == TOKEN_LT {
        consume `<`;
        let inner = parse_type(p);  // 递归解析 inner T
        expect `>`;
        return type_phantom(arena, inner);  // 绑到 builtin ident sym
    }
    // 缺 `<T>` → fall through 走 default ident → sema 报 unresolved
}
```

---

## 6. 实测 / Tests

### 6.1 sizeof 测试

```jhyy
// compiler/tests/examples/phantom_zst.jhyy
// SKIP: V3-C 3g.5 feature — jhyy-side only
struct Wrapper {
    _marker: PhantomData<i32>,
    val: i32,
}

fn main_jhyy() -> i32 {
    let s_pd: i64 = sizeof(PhantomData<i32>);
    if s_pd != 0 { return 10; }
    let s_pd64: i64 = sizeof(PhantomData<u64>);
    if s_pd64 != 0 { return 11; }
    let s_w: i64 = sizeof(Wrapper);
    if s_w == 4 { return 42; }   // PhantomData 不占 → sizeof = i32 = 4
    return s_w as i32;
}
// EXPECT: 42
```

### 6.2 Cap + PhantomData 组合测试

```jhyy
// compiler/tests/examples/cap_phantom_combo.jhyy
// SKIP: V3-C 3g.5 feature — jhyy-side only
struct W {
    cap: Cap,
    _marker: PhantomData<i32>,
    other: u32,
}

fn main_jhyy() -> i32 {
    let s_cap: i64 = sizeof(Cap);
    if s_cap != 8 { return 20; }
    let s_w: i64 = sizeof(W);
    if s_w == 16 { return 42; }  // 8 cap + 0 phantom + 4 u32 + 4 tail pad = 16
    return s_w as i32;
}
// EXPECT: 42
```

### 6.3 E0050 报错测试 (parser-level)

不在 regress 内 (parser 报错预期失败 EXIT != 0),留 v3.1.2 / v4.x 错误恢复 (3k) sub-sprint 加 positive error-recovery test。

---

## 7. 跨 sprint 对齐

- **V3-C v3.1.2** (3g.7) — CapTable<T> + 跨函数 cap pass,引入 `Cap<T>` generic syntax
- **V3-C v3.2.0** — generics monomorphize (3i), `Vec<T>` 等容器类型用 PhantomData<T> 持类型参数
- **V2-C v2.8.0** (N 代 fixed point) — V3-C 全 ship 后启动,验算 `phantom_zst.jhyy` + `cap_phantom_combo.jhyy`
- **V2-B v2.7.0** (amd64_sysv) — `abi_amd64_sysv.jhyy` PhantomData class backport 留 v3.1.3 / v4.x

---

## 8. 已知限制 / Known Limitations

| 限制 | 留到 |
|------|------|
| `PhantomData<PhantomData<X>>` 嵌套 | v3.x 中 |
| `PhantomData<&T>` lifetime 参数 | v4.3.0 Polonius |
| PhantomData 与 `#[no_std]` 组合测试 | v3.x 中 |
| E0050 parser-level positive test (错误恢复) | v4.7.0 (3k) |
| 完整 `Cap<PhantomData<X>>` 嵌套组合测试 | v3.1.2 (Cap<T> generic syntax) |
| PhantomData 字段访问 `.phantom` (无用,M0 不需要) | 不做 |
| PhantomData 作为函数参数/返回值 (ZST,无运行时影响) | v3.x 中 |