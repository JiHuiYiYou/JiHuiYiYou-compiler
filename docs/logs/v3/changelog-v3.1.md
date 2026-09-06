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

---

# V3-C v3.1.1 — `PhantomData<T>` ZST codegen (3g.5)

> **ship date**: 2026-09-06
> **branch**: `axis-v3` (per 2026-09-06 user "顺序做的后面不用开branch,就在v3主轴上修")
> **D27 锁**: 3g (v3.1.0) → 3g.5 (v3.1.1) → 3g.7 (v3.1.2) 串行不可调换
> **D43 baseline**: N7 (this sprint) — 上一条 N6 = `51376ce5721bccb0c81c7deabead1a6012fb76648c424238391018f1890b5761` (V3-B v3.0.5 final, v3.1.0 ship hold)
> **umbrella**: 本文件 v3.1.1 段 (与 v3.1.0 / v3.1.2 共用 changelog-v3.1.md, per `feedback_changelog_umbrella`)

---

## 1. 范围 / Scope

V3-C sub-sprint 2/3 — `PhantomData<T>` 0 字节 ZST type marker,只占 type 表项不占 struct layout slot,不允许实例化 (M0 简化)。

**D27 锁** v3.1.0 → v3.1.1 → v3.1.2 串行 (per [`../../plans/v3/batch-V3-C-plan.md`](../../plans/v3/batch-V3-C-plan.md) § 4.4 + [`../../plans/roadmap/v2-v3-parallel-sprint-plan.md`](../../plans/roadmap/v2-v3-parallel-sprint-plan.md))。

---

## 2. 改动 / Changes

### 2.1 types.jhyy

- 加 `KIND_PHANTOM = 12` (跟 v3.1.0 `KIND_CAP=11` 续号)
- `type_phantom(a, inner) -> *Type` ctor:复用 `Type.elem` slot 存 inner,`size=0`, `align=1` 硬编码 (ZST invariant)
- `type_size` 加 `KIND_PHANTOM` arm → `return 0`
- `type_align` 加 `KIND_PHANTOM` arm → `return 1`
- `type_eq` 加 `KIND_PHANTOM` arm → 结构等比 (跟 KIND_CAP 同型, `PhantomData<i32> ≠ PhantomData<u64>`)
- `type_to_string` 加 `KIND_PHANTOM` arm → `return "PhantomData"`

### 2.2 parser.jhyy

- `parse_type` IDENT 分支 (post-line 509) 加 `PhantomData<T>` 识别:
  - 匹配 `name == "PhantomData"` AND peek `<`
  - consume `<`, 递归 `parse_type(p)` 拿 inner T
  - expect `>`, 调 `type_phantom(arena, inner)`, 绑到 builtin ident sym
  - 不支持 `::` 限定 (M0 简化)
  - `PhantomData` 无 `<T>` → fall through 走 default ident → sema 报 unresolved

### 2.3 sema.jhyy

- 3 个禁实例化检查点 + `E0050: cannot instantiate PhantomData<T>` 错误:
  - `NODE_LET` (post-line 1305): `decl_type.kind == KIND_PHANTOM && init != null`
  - `NODE_CALL` (post-line 954): `callee_type.kind == KIND_PHANTOM`
  - `NODE_STRUCT_LIT` (post-line 1578): `t.kind == KIND_PHANTOM` (在 KIND_STRUCT 检查前)
- `let _m: PhantomData<T>;` (无 init) 合法 — 字段声明不受 E0050 拦

### 2.4 codegen.jhyy

- `cg_copy_struct` (line 654) 加早期 continue: `if (*ftype).kind == KIND_PHANTOM() { i = i + 1; continue; }`
- 字段迭代前跳过 PhantomData 字段, 不分配 src_off/dst_off tmp, 不 emit load/store IR

### 2.5 ir.jhyy

- `qbe_type_of` 加 `KIND_PHANTOM` arm → `return QBE_W` (防御, well-formed 程序不会触发)

### 2.6 codegen_amd64_emit_mem.jhyy

- **无修改**: `size <= 0` guard (line 263) 已存在; PhantomData 在 codegen.jhyy 阶段已 skip, 不进入 emit_mem 路径

---

## 3. 测试 / Tests

### 3.1 新增 test files

| File | Purpose | SKIP directive |
|------|---------|----------------|
| `compiler/tests/examples/phantom_zst.jhyy` | `sizeof(PhantomData<i32>) == 0` + `sizeof(Wrapper) == 4` | YES (V3-C 3g.5 jhyy-side only) |
| `compiler/tests/examples/cap_phantom_combo.jhyy` | `sizeof(Cap) == 8` + `sizeof(W) == 16` (Cap + PhantomData + u32) | YES |

### 3.2 测试结果

- `compiler/build/bin/jhyy.exe`: **104/104 PASS + 15 SKIP** (V3-C v3.1.0 baseline 104/104 + 13 SKIP 仍 hold;新增 `phantom_zst.jhyy` + `cap_phantom_combo.jhyy` 进 SKIP 计数)
- **No regression** (V3-C v3.1.0 baseline 104/104 + 13 SKIP 仍 hold)
- Ship-gate 5/5 PASS: `phantom_zst.jhyy` + `cap_phantom_combo.jhyy` 各 EXIT=42 (MCP `jhyy_run` 验证 5 次连续 EXIT=42)
- Regress binary sha256: `ee38ebc3caa80872cf7d95c04246f0cb757906c2e8fb6274b2d927099715f16e`

### 3.3 Self-host closure (D43 baseline N6 → N7)

- **Stage 2 N=4 byte-equal closure PASS**: v2/v3/v4/v5 全部 sha256 = `40d51000c132cd8c538e196e695d89900acd14ec7c1f5225bba6a04e75851145`
- D43 baseline N6 (`51376ce5...`) → **N7** = 本 commit sha (ZST 改 codegen layout emit, IL 漂移预期)
- 本 sub-sprint ship 后 N7 冻结 (per `feedback_make_clean_too_aggressive` pattern)
- Re-baseline 流程: jhyy_selfhost_check 自动记录新 SHA, changelog v3.1.1 段写明 N7 baseline = 本 commit sha

---

## 4. 已知限制 / Known Limitations (out of scope 留后续)

| 限制 | 留到 |
|------|------|
| `PhantomData<PhantomData<X>>` 嵌套 | v3.x 中 |
| `PhantomData<&T>` lifetime 参数 | v4.3.0 Polonius |
| PhantomData 与 `#[no_std]` 组合 | v3.x 中 |
| PhantomData 作为函数参数/返回值 | v3.x 中 |
| 完整 `Cap<PhantomData<X>>` 嵌套测试 (需 `Cap<T>` generic syntax) | v3.1.2 |
| E0050 parser-level positive test (错误恢复) | v4.7.0 (3k) |
| PhantomData 字段访问 `.phantom` | 不做 (marker 无运行时影响) |
| SysV (`abi_amd64_sysv.jhyy`) PhantomData class | v3.1.3 / v4.x |

---

## 5. 跨 sprint 对齐 / Cross-sprint Alignment

### 5.1 触发的后续 sprint

- **V3-C v3.1.2** (3g.7) — CapTable<T> + 跨函数 cap pass, D27 锁启 (v3.1.1 ship 后启动)
- **V3-C v3.2.0** — generics monomorphize (3i), `Vec<T>` 等容器类型用 PhantomData<T> 持类型参数
- **V2-C v2.8.0** (N 代 fixed point) — V3-C 全 ship 后启动, 验算 `phantom_zst.jhyy` + `cap_phantom_combo.jhyy`

### 5.2 跨边界 / Cross-boundary

- **jhyy_OS M4 launch 硬前置**: V3-C 全 ship (v3.1.0/1.1/1.2) + V2-A ✅ + V2-B 全 ship + V2-C N 代 fixed point 验算过
- **D6** (Cap<T> 8 字节) 已锁 — 本 sprint 不变, PhantomData 不影响 Cap layout
- **D27** (3g → 3g.5 → 3g.7 串行) — 本 sprint ship 后解锁 v3.1.2

---

## 6. 文档 / Documentation

- [`../abis/jhyy-lang-spec-phantomdata-supplement-v3.1.1.md`](../abis/jhyy-lang-spec-phantomdata-supplement-v3.1.1.md) — PhantomData 语法 + 0 字节 layout + ABI + codegen + 测试
- (复用) [`../abis/jhyy-lang-spec-cap-t-supplement-v3.1.0.md`](../abis/jhyy-lang-spec-cap-t-supplement-v3.1.0.md) — Cap<T> 8 字节 layout + ABI
- (复用) [`../abis/jhyy-lang-spec-borrow-check-supplement-v3.1.0.md`](../abis/jhyy-lang-spec-borrow-check-supplement-v3.1.0.md) — `&T` / `&mut T` + NLL stub

---

## 7. Commit

```
feat(phantom): add PhantomData<T> ZST codegen + Cap combo (3g.5)
```

**D43 baseline update**: N6 (`51376ce5...`) → **N7 = `a8d55ac65315535b0d1c291b94f5b1c130a8cabc`** (single commit 包含全部 6 src0 改动 + 2 测试 + 1 spec + changelog;Stage 2 N=4 closure hold 在 `40d51000c132cd8c538e196e695d89900acd14ec7c1f5225bba6a04e75851145`;tagged `v3.1.1` on this commit)
