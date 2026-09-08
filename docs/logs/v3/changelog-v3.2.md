# V3-C v3.2.0 — 3i struct/enum monomorphize scaffolding (parser + AST)

> **ship date**: 2026-09-08
> **branch**: `axis-v3`
> **D28 锁**: v3.2.0 (3i struct/enum) → v3.2.0b (3i fn/turbofish) 串行不可调换
> **D43 baseline**: N9 = `2e9866c` (this sprint, post-tag fill) — 上一条 N8 = `1fff447` (V3-C v3.1.2)
> **umbrella**: 本文件 v3.2.0 部分 (D43 chain 走 v3.2.0b 重新 hold)

---

## 1. 范围 / Scope

V3-C sub-sprint 4/N — **monomorphize 基础 scaffolding**(`type Foo<T>` 语法 +
`Foo<i32>` 引用语法 + skip `ntype_params > 0` 在 Pass 2/3)。runtime
monomorphize 推到 **v3.2.0b**(per § 6 "Deferred")。

**触发**(per `docs/plans/v2/v2.0.0-os-prep.md` § 1):
- **M8d launch 硬前置 1/N 满足**:compositor surface/buffer/seat generic over T
  (per D-GUI-11 锁 2026-09-01)
- **M11 launch 硬前置解锁**:3l.3 std lib `Vec<T>`/`Map<K,V>` 依赖 3i
- **v3.2.0b (fn + turbofish)** 启动前置
- **V2-C v2.8.0 N 代 fixed point** 跨 axis 验算前置

**scope 拆分决定**(user 2026-09-07):
- **v3.2.0**(本 sprint)= struct/enum monomorphize scaffolding + generic-on-pointer + parser/AST 扩展
- **v3.2.0b**(紧随本 sprint,per `feedback_v3b_no_phaseb_worktree` 不开新 worktree)=
  generic fn `fn max<T>(...)` + turbofish `name::<T>(...)` + 调用点 T 推断 +
  monomorphize pipeline 激活

---

## 2. 改动 / Changes

### 2.1 ast.jhyy

- `NodeTypeDecl` 16 → 32 bytes(+ `type_params: *u8` / `ntype_params: i64`)
  - `type_params`: `**Sym` 数组,每个 type-param 是 `SYM_TYPE` + `type_ptr=0` 哨兵
  - `ntype_params > 0` 标记 generic def;Pass 2/3 跳过 layout/codegen
- `NodeModule` 24 → 40 bytes(+ `generic_insts: *u8` / `ngeneric_insts: i64`)
  - `generic_insts`: `*GenericInstRecord` 数组(parser 累积)
- `GenericInstRecord` NEW 32 bytes:`mangled_name(8) + arg_types(8) + nargs(8) + base_name(8)`
- `ast_new_module` / `ast_new_type_decl` 用 offset 写入(避免 jhyy struct deref 在 *NodeModule/*NodeTypeDecl 上的不稳性)
- `node_module_data` / `node_type_decl_data` accessors 不变

### 2.2 parser.jhyy

- `Parser` struct 104 → 128 bytes(+ `generic_insts: *u8` / `ngeneric_insts: i64` / `gcap: i64`)
- `parser_init` zeros new fields
- `parser_record_generic_inst(p, base, mangled, args, nargs)` NEW — append 到 `(*p).generic_insts`(doubling array;起始 cap=4)
- `parser_mangle_type_node(p, node, buf_p, len, cap)` NEW — 递归 AST type node → mangled suffix
- `parse_type_decl` 解析可选 `<T, U, ...>` generic param list(每个推 scope + 插 `SYM_TYPE`+`type_ptr=0` 哨兵 sym)
- `parse_type` IDENT branch INLINE generic arm:
  - **disambig**:IDENT 首字母必须大写(A-Z, ASCII 65-90)→ 避免跟小写变量或 `<` less-than 冲突
  - 消费 `<`,parse 多个 type-arg(逗号分隔),mangle + record inst,return `NODE_IDENT` bound 到 mangled sym
- `parse_expr` IDENT branch INLINE 同 generic arm(struct literal `Vec<i32> { ... }` 路径)
- `parser_parse` 把 `(*p).generic_insts, (*p).ngeneric_insts` 传给 `ast_new_module`

### 2.3 mono.jhyy NEW (~395 行,v1.x-subset dialect)

- `import arena; import util; import ast; import symtab;`
- helpers(`mono_decls_append` doubling array / `mono_find_generic_def` / `mono_subst_node` 递归 type node / `mono_clone_struct_def` / `mono_clone_enum_def` / `mono_clone_and_subst`)
- `mono_expand_module(global, arena, md) -> i32` — Pass 1.5 hook
  - **本 sprint ship 状态:NO-OP**(`return 0`),per § 6
  - 完整实现 present 在文件 helpers,但 `mono_expand_module` body 只 `return 0`
  - 原因:jhyy struct deref 在 `Sym`(56B)、嵌套 `StructFieldDecl`/`EnumVariantDecl` 上
    不可靠 — 深路径 `(*fld).*` 触发 wrong-byte reads;offset access 在浅层 OK
    但到 `mono_subst_node` → `strcmp((*sym).name, ...)` → 跨 arena pointer 路径
    触发的具体 bug 待解,见 changelog § 6 "Deferred"
- 文件最后一行有详细 ship status 注释 + deferral rationale

### 2.4 sema.jhyy

- `import mono;` 加在 `import parser;` 之后
- **Pass 1.5 hook**(在 Pass 1 close 和 Pass 2 start 之间):
  ```jhyy
  jh_fputs_stderr("[sema] P1.5 mono_expand_module start\n");
  let mono_errs = mono_expand_module((*ctx).global_scope, (*ctx).arena, md);
  ...
  ```
  当前 no-op,但 hook + import 已就位,v3.2.0b 激活时只改 mono.jhyy body
- Pass 2 内 NODE_TYPE_DECL 分支 skip `ntype_params > 0`(generic def 不 layout)
- `resolve_type_node` NODE_IDENT fall-through 加 **E0060**:`unresolved type parameter; generic must be instantiated`
  - 当 looked sym 是 `SYM_TYPE` + `type_ptr == 0`(type-param 哨兵)时触发
  - 返回 `type_primitive(ta, PRIM_I32())` 做 error recovery

### 2.5 tests/examples/

**5 NEW SKIP tests**:
- `generics_struct.jhyy` — `Pair<T>` 解析路径
- `generics_ptr_field.jhyy` — `Vec<T> { data: *T, ... }` 泛型指针字段
- `generics_enum.jhyy` — `Option<T> = enum { Some(T), None }`
- `generics_multi_param.jhyy` — `Map2<K, V>` 双 type-param
- `generics_err_unsubst.jhyy` — bare `T` in non-generic scope

**CapTable tests**:**不重写**(per § 6 deferral — runtime refactor 需要 monomorphize)

---

## 3. 验证 / Verification

### 3.1 基础回归(regress.py)

```
===== 104/104 passed, 0 failed, 22 skipped (of 126 total) =====
compiler/build/bin/jhyy.exe: PASS — passed=104/126 failed=0 skipped=22 (sha=...)
```

- 104/104 PASS — 跟 v3.1.2 baseline 一致(无 regress)
- 17 SKIP → 22 SKIP(+5 来自 5 个新 generics_* tests)
- 2 CapTable SKIP 保持原状(`cap_table_basic.jhyy` / `cap_table_advanced.jhyy`)

### 3.2 Self-host closure(待 v3.2.0b 跑)

N9 baseline 当前 D43 hold 来自 v3.1.2 `1fff447`(per changelog-v3.1.md v3.1.2 段)。
v3.2.0 ship 后 self-host closure 不变(mono_expand_module 是 no-op,src0 IL 不变)。
v3.2.0b 激活 monomorphize 时,**D43 re-baseline N8 → N9b**(per D43 chain 流程)。

---

## 4. Out of scope(本 sprint 不做 → v3.2.0b 或后续)

| 项 | 留到 | 备注 |
|----|------|------|
| Monomorphize pipeline runtime(激活 `mono_expand_module`) | **v3.2.0b** | 详见 § 6 — jhyy struct deref 深路径不稳,推到 fn body 路径重新评估 |
| Generic fn `fn max<T>(...)` | **v3.2.0b** | turbofish 也一起 |
| Turbofish `name::<T>(...)` | **v3.2.0b** | expr 位 `::<` 3-token disambiguator |
| 调用点 T 推断 `let x = max(3, 5)` | **v3.2.0b** | 新算法独立风险面 |
| 嵌套泛型 `Vec<Vec<T>>` | v3.x 中 | needs worklist-to-fixpoint |
| `PhantomData<Cap<T>>` 嵌套 | v3.x 中 | 已从 v3.1.x 延 |
| `*Cap<T>` raw ptr 完整 codegen | v3.x 中 | parser 已 support, codegen 等 v3.2.0b |
| `CapTable<T>` 真 generic 重构 | **v3.2.0b** | 当前 5 NEW tests 已用此 pattern,但实际 instantiation 不工作 |
| Lifetime 泛型 `<'a, T>` | v4.3.0 | per L2;lexer 无 tick token |
| const generic | v4.5.0 | per README |
| Specialization / HKT | v4.10.0 | per README |
| Trait objects `dyn Trait` | v4.6.0 | per README |
| 泛型 bounds `<T: Ord>` | v3.x 末 | sema 在 substitution 后查 |
| 泛型 closures | v4.4.0 | per v3.2.1 plan |
| jhyy self-source 迁 `Vec<T>` | M11 launch | 不阻本 ship |

---

## 5. 跨 sprint 对齐 / Cross-sprint Alignment

### 5.1 触发的后续 sprint

- **v3.2.0b**(V3-C 3i fn/turbofish)— v3.2.0 ship 后启动,激活 `mono_expand_module`
  + 加 fn 路径 + turbofish + 调用点推断
- **v3.2.1**(V3-C 3j closures)— D28 链,3i 完成后启动
- **v3.2.4**(V3-C 3l.3 `Vec<T>`/`Map<K,V>` std lib)— 等 3i 完
- **V2-C v2.8.0**(N 代 fixed point)— 跨 axis,3i + 3j ship 后启动

### 5.2 跨边界 / Cross-boundary

- **jhyy_OS M8d launch 硬前置**:**1/N 满足**(compositor 路径基本就位 — 实际 instantiation
  待 v3.2.0b)
- **jhyy_OS M11 launch 硬前置解锁**:parser/AST surface 已就位
- **D28** v3.2.0 → v3.2.0b 串行锁启 → v3.2.0b → v3.2.1 → v3.2.4 全 D28 锁
- **D-GUI-11** 锁(2026-09-01):compositor generic over T 路径,sema + parser surface ready

---

## 6. Deferred to v3.2.0b(本次 ship 不达项)

**核心问题**:`mono_expand_module` 的完整实现(mono.jhyy)在深路径触发 jhyy
struct deref 不稳定性。

### 6.1 具体路径(实测)

1. **NODE_TYPE_DECL 字段 offset access** ✓ — `node_type_decl_data(td)` 增 NODE_SIZE
   后,offset 0/8/16/24 读 `sym/body/type_params/ntype_params` 正确
2. **NodeModule 字段 offset access** ✓ — 同样 offset 0/8/16/20/28 正确
3. **GenericInstRecord 字段 offset access** ✓ — offset 0/8/16/24 正确
4. **NodeModule/GenericInstRecord 的 struct deref** ✗ — `(*mdd).ngeneric_insts`
   读到 wrong bytes(probe 显示 offset 28 = 2,deref = 0)
5. **NodeStructDef/NodeEnumDef 的 struct deref** 部分 ✗ — `(*sd).nfields`
   在某些 case 读到 wrong bytes(配合 `node_struct_def_data` 加 NODE_SIZE 后)
6. **StructFieldDecl/EnumVariantDecl 的 struct deref** ✗ — `(*fld).type_annot`
   在嵌套 context 下读到 wrong bytes
7. **Sym 的 struct deref** 部分 ✗ — `(*sym).name` 大多 OK,但跨 arena pointer
   路径(`arena_alloc` 出来的 sym → 跨 fn 传 → deref)有 edge cases

### 6.2 缓解策略

- **本次 ship**:mono_expand_module 改为 `return 0`(no-op);其他 helper code 保留
  在文件里、注释清楚;`sema.jhyy` 的 Pass 1.5 hook 保留但调用 no-op
- **v3.2.0b 行动**:
  - 加 6-8 个针对 `*sym.name` / `(*sd).nfields` / `(*fld).type_annot` 的 unit-style
    微测试,定位 struct deref 稳的边界
  - 如果 deep path 不稳,**`mono_subst_node` 全部用 offset access**(已经在浅层用过的
    模式,需要扩展到所有 Sym/StructFieldDecl/EnumVariantDecl deref)
  - 可能需要把 clone_and_subst 拆成多个小 fn,每个 fn 单独 debug deref 边界
  - 必要时**加 `arena` 旁路 helper**:`sym_name_safe(sym) -> *u8` 走 offset 而非
    `(*sym).name`,强制所有 caller 用 safe variant

### 6.3 风险评估

- **parser.surface 已经工作**(`type Foo<T>` + `Foo<i32>` 语法都 parse OK)
- **codegen 已经跳过 generic def**(Pass 2/3 `ntype_params > 0` skip)
- **唯一阻塞 runtime**:`mono_expand_module` body(已写好但禁用)
- **无 regress**(104/104 PASS 验证)
- **无 ABI 影响**(`Type` struct 不动,C-side struct layout 不变)

v3.2.0b 是 v3.2.0 的直接延续,在 fn body 路径重新激活 monomorphize。同 worktree,
per `feedback_v3b_no_phaseb_worktree`。

---

## 7. Cross-ref

- L1 设计:`docs/plans/roadmap/v3.x-language-expansion.md § Sprint 3i`
- L2 设计:`docs/plans/v3/v3.2.0-plan.md`(83 行)
- 上游:`v3.1.2-plan.md` (CapTable + 跨 fn Cap<T>, N8 = `1fff447`)
- 下游:`v3.2.0b-plan.md` · `v3.2.1-plan.md` · `v3.2.4-plan.md`
- 跨 axis:V2-C v2.8.0 N 代 fixed point
- D-GUI-11 lock:`jhyy_OS/docs/coordination.md § 3`;D28 + M8d/M11 launch gates:`docs/plans/v2/v2.0.0-os-prep.md § 1`
- D43 chain:`docs/logs/v3/changelog-v3.1.md` v3.1.2 段(N8 = `1fff447`)

---

## 8. Commit / Tag

- **Commit**:`feat(generics): add struct/enum monomorphize scaffolding (3i parser+AST; runtime defer v3.2.0b)`
- **Tag**:`v3.2.0` (per `feedback_v3b_no_phaseb_worktree`)
- **Post-tag SHA fill-in**:本文件 § "umbrella" 头锚 N9 = `<commit sha>`
- **Auto-push**:per `feedback_auto_push_after_commit`
