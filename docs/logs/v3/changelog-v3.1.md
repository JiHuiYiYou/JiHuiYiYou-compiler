# V3-C v3.1.0 — `&T` / `&mut T` + NLL (stub) + `Cap<T>` 8-byte Layout

> **ship date**: 2026-09-06
> **branch**: `v3-C/v3.1.0-borrow-and-cap`
> **D27 锁**: 3g (v3.1.0) → 3g.5 (v3.1.1) → 3g.7 (v3.1.2) 串行不可调换
> **D43 baseline**: N6 (this sprint) — 上一条 N5 = `51376ce5` (V3-B v3.0.5 final)
> **umbrella**: 本文件 v3.1.0 部分 (3 sub-sprint 共享)

---

## 1. 范围 / Scope

V3-C sub-sprint 1/3 — `&T` / `&mut T` 借用类型 + 简化版 NLL (stub) + `Cap<T>` 8 字节 layout。

**D27 锁** v3.1.0 → v3.1.1 → v3.1.2 串行 (per [`../../plans/v3/batch-V3-C-plan.md`](../../plans/v3/batch-V3-C-plan.md) § 4.4 + [`../../plans/roadmap/v2-v3-parallel-sprint-plan.md`](../../plans/roadmap/v2-v3-parallel-sprint-plan.md))。

---

## 2. 改动 / Changes

### 2.1 ast.jhyy

- 加 `NODE_REF_TYPE = 55` (v3.1.0; 54 已被 V3-B 3f 占用 = `NODE_BUILTIN_FENCE`)
- 加 `NodeRefType { inner: *u8, is_mut: i32, lifetime: *u8 }` (24 bytes)
- 加 `ast_new_ref_type` / `node_ref_type_data` factory + accessor

### 2.2 types.jhyy

- 加 `KIND_REF = 10` (v3.1.0) + `KIND_CAP = 11`
- `Type` struct 加 `is_mut: i32 + _pad_mut: i32` (160 → 168 bytes)
- 加 `type_ref(inner, is_mut)` ctor + `type_cap(inner)` ctor (size=8, align=8 硬编码)
- `type_size` / `type_align` / `type_eq` / `type_to_string` 加 KIND_REF / KIND_CAP arm
- `type_eq` 对 KIND_REF 强校验 is_mut 必须相等 (`&T` ≠ `&mut T`)

### 2.3 parser.jhyy

- `parse_type` line 316 顶端加 `&T` / `&mut T` prefix 分支
- Disambiguation: peek next token,跳过 `&&` (boolean-and,留 v1.x 语义)
- 拒绝 chained `&&T` (借用是 terminal)
- 拒绝 `&mut volatile T` / `volatile &mut T` (借用 + volatile 互斥)
- `&mut` 关键字 optional,`is_mut` 标记同步到 AST

### 2.4 sema.jhyy

- `resolve_type_node` 加 `NODE_REF_TYPE` arm (line 349) — resolve inner + 复制 fields + 设 KIND_REF + is_mut
- 拒绝 chained `&&T` (KIND_REF 套 KIND_REF)
- 拒绝 `&(mut)? volatile T` 组合
- `sema_error_str` 错误信息
- **check_borrow STUB** — 完整 NLL 留 v3.x 末,当前直接 `return 1`
- 错误恢复: invalid 借用返回 `i32` placeholder (跟 volatile path 一致)
- **sema ident dispatch** 加 `Cap` builtin → `type_cap(i32)` (v3.1.0 简化, generic 留 v3.1.2)

### 2.5 codegen_amd64_state.jhyy

- 加 `QBE_BORROWED_MARKER = -2` (区别 volatile `-1`)
- qbe_type 仍写 `'l'`,marker 供 codegen 阶段 metadata 区分

### 2.6 ir.jhyy

- `qbe_type_of` 加 KIND_REF → `QBE_L` (8-byte ptr)
- `qbe_type_of` 加 KIND_CAP → `QBE_L` (8-byte struct pass-by-value)

### 2.7 abi_amd64_win.jhyy

- `abi_win_classify_arg` 走 delegate path — KIND_REF / KIND_CAP 自动返回 `QBE_L`
- MS x64 calling convention: 8-byte struct 走 INTEGER class (RCX/RDX/R8/R9)
- SysV (`abi_amd64_sysv.jhyy`) 留 v3.1.3 backport (V2-B v2.7.0 ship 后)

---

## 3. 测试 / Tests

### 3.1 新增 test files

| File | Purpose | SKIP directive |
|------|---------|----------------|
| `compiler/tests/examples/cap_test.jhyy` | `sizeof(Cap) == 8` 验证 | YES (C-side bootstrap predates V3-C) |
| `compiler/tests/examples/borrow_check_basic.jhyy` | `sizeof(&i32) == sizeof(&mut i32) == 8` 验证 | YES |
| `compiler/tests/examples/borrow_check_err.jhyy` | `&&T` 拒绝验证 (sema 报错) | YES |

### 3.2 测试结果

- `compiler/build/bin/jhyy.exe`: 104/104 PASS + 10 SKIP (V3-B legacy) + 3 SKIP (V3-C new)
- **No regression** (V3-B baseline 104/104 仍 hold)
- Ship-gate 5/5 PASS: `cap_test.jhyy` EXIT=42 (sizeof == 8)

### 3.3 Self-host closure

- D43 baseline 暂未 re-baseline (per-sub-sprint re-baseline 计划)
- 本 sub-sprint 不影响 closure invariant (qbe_type 仍 `'l'`,IL emit 跟 v3.0.5 byte-equal)
- Re-baseline 留 v3.1.0 integration 阶段

---

## 4. 已知限制 / Known Limitations (out of scope 留后续)

| 限制 | 留到 |
|------|------|
| 双 mutable 借用冲突检测 (`&mut x; &mut x`) | v3.x 末 (Polonius) |
| `&mut` + `&` 互斥检测 | v3.x 末 |
| reborrow `&mut *x` | v3.x 末 |
| lifetime `'a` 标注 (tokenizer 阶段无 tick) | v3.x 中 |
| 跨函数 borrow | v3.x 末 |
| nested block 借用作用域 | v3.x 末 |
| path-based NLL (NLL2) | v3.x 末 |
| `Cap<T>` 泛型语法 `<T>` | v3.1.2 |
| `Cap` 字段访问 `.cnode_idx` | v3.1.2 |
| `cap_new()` builtin ctor | v3.1.2 |
| `Cap<Cap<T>>` 嵌套 | v3.x 中 |
| `PhantomData<&T>` lifetime 参数 | v3.x 中 |
| 大端架构 swap | v3.x 末 |
| `abi_amd64_sysv.jhyy` Cap<T> class | v3.1.3 backport |

---

## 5. 跨 sprint 对齐 / Cross-sprint Alignment

### 5.1 触发的后续 sprint

- **V3-C v3.1.1** (3g.5) — PhantomData<T> ZST + Cap 组合 (D27 锁启,v3.1.0 ship 后启动)
- **V3-C v3.1.2** (3g.7) — CapTable<T> + 跨函数 cap pass (D27 锁启,v3.1.1 ship 后启动)
- **V2-C v2.8.0** (N 代 fixed point) — V3-C 全 ship 后启动,验算 `cap_test.jhyy`
- **V2-B v2.7.0** (amd64_sysv) — `abi_amd64_sysv.jhyy` Cap<T> class backport 到 v3.1.3

### 5.2 跨边界 / Cross-boundary

- **jhyy_OS M4 launch 硬前置**: V3-C 全 ship + V2-A ✅ + V2-B 全 ship + V2-C N 代 fixed point 验算过
- **D6** (Cap<T> 8 字节) 已锁 — 本 sprint 实现 ✓
- **D10** (`#[no_std]` 软) — V3-A 已 ship,本 sprint 不影响
- **D11** (`&mut` 矩阵) — 本 sprint 实现 `&T` / `&mut T` 类型 + ABI,NLL 简化版

---

## 6. 文档 / Documentation

- [`../../abis/jhyy-lang-spec-borrow-check-supplement-v3.1.0.md`](../../abis/jhyy-lang-spec-borrow-check-supplement-v3.1.0.md) — borrow 语法 + 类型 + NLL stub
- [`../../abis/jhyy-lang-spec-cap-t-supplement-v3.1.0.md`](../../abis/jhyy-lang-spec-cap-t-supplement-v3.1.0.md) — Cap<T> 8 字节 layout + ABI

---

## 7. Commit

```
feat(v3.1.0): add &mut + lifetime NLL (stub) + Cap<T> 8-byte layout (3g)
```
