# jhyy-lang-spec — Generics (struct/enum) Supplement (v3.2.0b)

> **Supplement 状态**: ✅ locked (v3.2.0b shipped 2026-09-08, tag `v3.2.0b`)
> — runtime monomorphize ACTIVE;monomorphized struct/enum 是 non-generic,走现有
> codegen path。配合 [`../jhyy-lang-spec-v1.3.0.md`](../jhyy-lang-spec-v1.3.0.md) +
> [v3.2.0 generics supplement](jhyy-lang-spec-generics-supplement-v3.2.0.md) +
> [Cap<T> supplement v3.1.0](jhyy-lang-spec-cap-t-supplement-v3.1.0.md) +
> [PhantomData<T> supplement v3.1.1](jhyy-lang-spec-phantomdata-supplement-v3.1.1.md)
> 读。
> **作者**: JHYY <15901598712@163.com>
> **日期**: 2026-09-08
> **范围**: V3-C v3.2.0b sub-sprint — root cause fix + activate `mono_expand_module`
> body + 5 SKIP→real + CapTable<T> refactor。

---

## 1. 范围 / Scope

v3.2.0b 解锁 v3.2.0 § 6 列 deferred items。**0 fn 路径** — generic fn / turbofish /
call-site inference 推 v3.2.0c(per user 2026-09-08 决定)。

**ship 状态**:
- ✅ Root cause fix:`mono_find_generic_def` L102-104 `(*s).name` → offset read
  (commit `6dfe6bc`, stage-0 codegen stack-spill mitigation)
- ✅ `mono_expand_module` body activated:遍历 `(*md).generic_insts` →
  `symtab_lookup(global, mangled_name)` dedupe → `mono_clone_and_subst` 克隆 +
  substitute → `mono_decls_append` 加入 `(*md).decls`。**全 offset access**(28 sites),
  避免 `(*sym).*` / `(*mdd).*` / `(*sd).*` / `(*fld).*` / `(*vd).*` 模式
- ✅ Parser `skip_default` fix:`_skip_default = 1` flag hoisted + default IDENT
  branch gated with `if skip_default == 0 { ... }`(commit `f4a3ded`)
- ✅ 5 generics_* tests drop SKIP,真 instantiate PASS EXIT=42
- ✅ CapTable<T> 真 generic refactor:`type CapTable<T> = struct { data: *Cap<T>, len: i64 }`,
  layout 16B 保留(`*Cap<T>` 8B ptr + `i64` 8B)
- ❌ Generic fn / turbofish → v3.2.0c

---

## 2. Root cause + mitigation

### 2.1 现象

v3.2.0 ship 时 `mono_expand_module` body 写好但禁用。Stage-0 jhyy codegen 对
`(*ptr).field` 在 deep nested context(QBE 内部 codegen 限制)触发 stack-spill
不全,产生 wrong bytes。388 行 mono.jhyy 真正不稳只有 1 处(L102-104 `(*s).name`),
其他 28 处已 offset access。

### 2.2 Mitigation (caller-side, 不动 stage-0)

- L102-104 改 offset read:`*((s as i64 + 0) as **u8)`(沿用 `mono_subst_node` L152-153 pattern)
- `mono_expand_module` body 全 offset access,不复用 `(*sym).*` 模式
- **D43 byte-equal closure 保住**:stage-0 bug 是 deterministic 的(每代走错路径但走法一致)
  — workaround 注入的 offset access pattern 在 v1/v2/v3/v4/v5 都产生 identical IL

### 2.3 推到 v2.x 末的根除

QBE 自写 stage (per `v2-v3-parallel-sprint-plan.md`)后,stage-0 codegen 是 jhyy-self,
不再有 stack-spill 边界问题。本 sprint 不做。

---

## 3. Mono substitution 规则

### 3.1 触发

`parser_record_generic_inst` 在 parser 每次遇到 `Foo<T1, T2, ...>` 引用时调一次
(struct/enum instantiation;**不**对 fn call-site 触发 — 阶段 2 v3.2.0c 才扩)。

每条 inst 记 `{ mangled_name, arg_types, nargs, base_name }` 到 `(*p).generic_insts`。

### 3.2 Dedupe

`mono_expand_module` 对每条 inst:
1. `symtab_lookup(global_scope, mangled_name)` → 找到 ms(per-inst mangled sym)
2. 走 `(*md).decls`,找 existing `NODE_TYPE_DECL` with `sym == ms`(handles parser
   recording 1 inst per usage site)
3. 如果已存在 → skip(alread done)
4. 否则 `mono_find_generic_def(md, base_name)` 找 generic def → `mono_clone_and_subst`
   克隆 + substitute → `mono_decls_append`

### 3.3 Substitution 规则 (`mono_subst_node`)

对 cloned body 内 NODE_IDENT:
- 若 sym.name 匹配 `type_params[k].name`(k ∈ [0, ntype_params)) → 替换为
  `arg_nodes[k]` (concrete type Node)
- 否则保留原 IDENT(non-type-param ident)

NODE_UNARY / NODE_ARRAY_TYPE / NODE_SLICE_TYPE / NODE_REF_TYPE → 递归 sub inner。
其他节点 → 保留原 kind + loc,不复 variant data。

---

## 4. CapTable<T> layout 锁

```
type CapTable<T> = struct {
    data: *Cap<T>,  // 8B ptr (Win x64 RCX class)
    len: i64,       // 8B
}
// sizeof(CapTable<T>) == 16, alignment 8
```

跟 v3.1.2 M0 简化 layout (`CapTable = struct { data: i64, len: i64 }`, 16B)**完全一致**
(都是 8B + 8B,ZST inner T 不污染,因为 `*Cap<T>` 是 ptr 不展开 inner)。

跨 fn `CapTable<T>` pass-by-value:走 Win x64 INTEGER class,2 × QBE_L slots
(RCX + RDX)。CapTable 16B 不会走 SSE class(per Win ABI 16B 整数走 stack)。

---

## 5. Verification gate (per `feedback_fix_evaluation_rule`)

ship 必须达到:
- [x] 5/5 PASS EXIT=42 on `generics_struct.jhyy` / `generics_ptr_field.jhyy` /
      `generics_multi_param.jhyy` / `generics_enum.jhyy` / `generics_err_unsubst.jhyy`
- [x] 2/2 PASS EXIT=42 on `cap_table_basic.jhyy` / `cap_table_advanced.jhyy`
- [x] Full regress 111/111 passed, 0 failed, 15 skipped (was 109/104/17)
- [x] D43 byte-equal:`jhyy_v2..v5` SHA `d35656a3d72c75e211d26ab1cad73af7d6cd92f22851ba2a21a444a0a1b208e4`
- [x] `jhyy_get_il` on `generics_struct.jhyy`:`Pair<i32>` alloc8 / `Pair<i64>` alloc16
      (2 distinct structs,monomorphize 真发生)
- [x] `git diff compiler/src0/codegen.jhyy types.jhyy abi_amd64_win.jhyy parser.jhyy`
      empty(0 改动)

---

## 6. Out of scope (deferred to v3.2.0c 或后续)

- Generic fn `fn max<T>(...)` — v3.2.0c
- Turbofish `name::<T>(...)` — v3.2.0c
- Call-site T inference `let x = max(3, 5)` — v3.2.0c
- `mono_subst_block` / `mono_subst_stmt` / `mono_subst_expr` 深 body walk — v3.2.0c
- 嵌套泛型 `Vec<Vec<T>>` (worklist-to-fixpoint) — v3.x 中
- `PhantomData<Cap<T>>` 嵌套 — v3.x 中(已从 v3.1.x 延)
- `*Cap<T>` raw ptr 完整 codegen 路径 — v3.x 中(阶段 1 只在 CapTable 内部用)

---

## 7. Cross-ref

- v3.2.0 changelog § 6 (deferred items driver):`docs/logs/v3/changelog-v3.2.md:162-204`
- v3.2.0 spec supplement(parser + AST surface 复用):`docs/abis/jhyy-lang-spec-generics-supplement-v3.2.0.md`
- v3.2.0 plan (L2 设计):`docs/plans/v3/v3.2.0-plan.md`
- D28 chain:`v3.2.0 → v3.2.0b → v3.2.0c → v3.2.1 → v3.2.4`
- D43 chain:N8 (`1fff447`) → N9 (`2e9866c`) → **N10** (v3.2.0b)
- D-GUI-11 (2026-09-01 锁):compositor generic over T 路径,v3.2.0b 兑现 M8d launch 硬前置
- 反馈:`feedback_fix_evaluation_rule`(5/5 PASS EXIT=42)
- 反馈:`feedback_plans_per_version`(per-version plan,不 umbrella)
- 反馈:`feedback_changelog_umbrella`(v3.2 axis 只用 1 个 umbrella changelog)