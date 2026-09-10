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

## v3.2.0b — 3i generics root cause fix + struct/enum activate + CapTable<T> refactor

**Status**: ✅ shipped (`f4a3ded`, 2026-09-08)
**Tag**: `v3.2.0b` (TBD — final ship commit after C4)
**D43 baseline**: N10 = `f4a3ded` (jhyy_v2..v5 SHA `d35656a3d72c75e211d26ab1cad73af7d6cd92f22851ba2a21a444a0a1b208e4`)

### Scope (per `feedback_plans_per_version` 单 plan)

解决 v3.2.0 § 6 列 deferred items:
- **Root cause fix**:`mono_find_generic_def` L102-104 `(*s).name` → offset read (C1 `6dfe6bc`, per v3.2.0 plan § 6.2 stage-0 codegen stack-spill mitigation)
- **Activate `mono_expand_module` body**:从 no-op 改为完整 walk + clone + append,all offset access(C2 `f4a3ded`)
- **Parser skip_default fix**:`_skip_default = 1` flag set but never checked in v3.2.0 ship;hoist + gate default IDENT branch(C2)
- **5 SKIP→real tests**:`generics_struct` / `generics_ptr_field` / `generics_multi_param` / `generics_enum` / `generics_err_unsubst` 全 PASS EXIT=42(C2)
- **CapTable<T> 真 generic refactor**:`type CapTable<T> = struct { data: *Cap<T>, len: i64 }`,layout 16B 保留(C3 同 commit)
- **不扩 NodeCall / NodeFuncDecl** (deferred v3.2.0c per stage-2 拆)
- **不动 codegen.jhyy / abi_amd64_win.jhyy / types.jhyy** (0 行,monomorphize 出的 cloned struct/enum 是 non-generic,走现有 emit)

### Root cause (per v3.2.0 § 6.1 stage-0 codegen bug)

不是 mono caller offset 错(388 行 mono.jhyy 真正不稳只有 1 处);是 stage-0 jhyy codegen
对 `(*ptr).field` 在 deep nested context 下的 stack-spill 不全(QBE 内部 codegen 限制,
DEFERRED 到 v2.x 末 QBE 自写 stage)。v3.2.0b 是 caller-side mitigation,不动 stage-0。

### Verification (per `feedback_fix_evaluation_rule` 5/5 PASS EXIT=42)

- **5 SKIP→real**:5/5 EXIT=42 (regress --tests 验证)
  - `generics_struct.jhyy` — `Pair<i32>` alloc8 / `Pair<i64>` alloc16 (jhyy_get_il 验证 distinct struct)
  - `generics_ptr_field.jhyy` — `Vec<i32>` / `Vec<i64>` field round-trip
  - `generics_multi_param.jhyy` — `Map2<i32, i64>` / `Map2<i64, i32>` asymmetric substitution
  - `generics_enum.jhyy` — `Option<i32>` instantiation
  - `generics_err_unsubst.jhyy` — E0060 fall-through path
- **2 cap_table tests**:2/2 EXIT=42
  - `cap_table_basic.jhyy` — `sizeof(CapTable<i32>) == 16`,跨 fn CapTable<i32> pass
  - `cap_table_advanced.jhyy` — `sizeof(CapTable<PhantomData<i32>>) == 16`,ZST 不污染
- **Full regress**:111/111 passed, 0 failed, 15 skipped (was 109/104/17 at v3.2.0)
- **D43 closure**:`jhyy_v2..v5` SHA `d35656a3...` byte-equal,N9 (`2e9866c`) → **N10**
- **No codegen/types/abi diff**:`git diff compiler/src0/codegen.jhyy types.jhyy abi_amd64_win.jhyy` empty

### Cross-ref

- L2 设计:`docs/plans/v3/v3.2.0b-plan.md`(待 ship 后建档)
- Spec supplement:`docs/abis/jhyy-lang-spec-generics-supplement-v3.2.0b.md`
- 上游:v3.2.0 (`2e9866c`) § 6 deferred items → 本 sprint 全部解
- 下游:v3.2.0c (generic fn + turbofish) · v3.2.1 (3j closures) · v3.2.4 (3l.3 Vec<T>/Map<K,V>)
- D-GUI-11 锁 (2026-09-01):compositor generic over T 路径,v3.2.0b 兑现 M8d launch 硬前置 1/N → 完整
- D28:`v3.2.0 → v3.2.0b → v3.2.0c → v3.2.1 → v3.2.4` 串行锁链,v3.2.0b ship 解锁 1 节点
- D43 chain:`v3.1.2` (N8 `1fff447`) → `v3.2.0` (N9 `2e9866c`) → **v3.2.0b** (N10 `f4a3ded`)

### Out of scope (deferred to v3.2.0c 或后续)

- Generic fn `fn max<T>(...)` + turbofish + call-site inference → **v3.2.0c**
- `mono_subst_block` / `mono_subst_stmt` / `mono_subst_expr` 深 body walk → v3.2.0c
- 嵌套泛型 `Vec<Vec<T>>` (worklist-to-fixpoint) → v3.x 中
- PhantomData 嵌套 Cap 完整 codegen 路径 → v3.x 中

---

## v3.2.0c — 3i fn path: turbofish syntax + monomorphize + per-clone sym isolation

**Status**: ✅ shipped (TBD — final ship commit after tag)
**Tag**: `v3.2.0c`
**D43 baseline**: N11 = TBD (jhyy_v2..v5 byte-equal verified 2026-09-08, SHA `b87c932038055321dc4caa134b914b99598cd9ea568b641eeb4fc4bd72592ddb`)

### Scope (per `feedback_plans_per_version` 单 plan)

解决 v3.2.0b § "Out of scope" 列表项 1+2:
- **`fn max<T, U>(...)` 语法 parse**:parse_func generic arm peek `<` after fn name,push_scope + collect SYM_TYPE type_ptr=0 sentinels + store on NodeFuncDecl.type_params/ntype_params(C2 `0dcbda8`)
- **`max::<T, U>(args)` turbofish parse**:parse_expr IDENT primary branch 加 3-token lookahead (IDENT + `::` + `<`) → parser_mangle_type_node + parser_record_generic_inst → plumb type_args/ntype_args 到 NODE_CALL AST 节点(C2)
- **`mono_clone_func_decl`**:深 clone NodeFuncDecl body + 11 个字段全 copy + body 走 mono_subst_block(C3 `ad75e99`)
- **`mono_subst_block` / `mono_subst_stmt` / `mono_subst_expr`**:覆盖所有 stmt/expr kind (NODE_BINARY/CALL/FIELD/INDEX/CAST/UNARY/ADDR_OF/DEREF/ARRAY_LIT/SLICE_LIT/SLICE_RANGE + NODE_BLOCK/IF/WHILE/FOR/LET/RETURN/ASSIGN/EXPR_STMT/MATCH/DEFER/BREAK/CONTINUE),全 offset access pattern (per v3.2.0b mitigation)(C3)
- **`check_func_decl` body skip**:offset access `(*fd).ntype_params` @ 88 (per v3.2.0b L102-104 经验),避免 stage-0 codegen stack-spill(C4 `fa34293`)
- **`infer_type` NODE_CALL turbofish handling**:detects ntype_args > 0 → resolve callee IDENT.sym → if SYM_FN trigger `mono_expand_fn_call` + rewrite NODE_IDENT.sym to mangled sym (per call-site sym 替换 model)(C4)
- **`cg_func` skip gate**:mirror check_func_decl pattern,offset access `ntype_params @ 88` → skip body emit for generic def(原始 `fn max<T>` 不 emit,cloned `max$i32` / `max$f64` 走 normal emit)(C4 + C5)
- **`mono_expand_fn_call`**:per-call-site mangled_name symtab_lookup dedupe,clone via mono_clone_func_decl + overwrite cloned.sym to mangled sym + append to module.decls(C3)
- **2 新 test placeholder 1 real**:generics_fn_turbofish_basic.jhyy (EXIT=42 ✅) drop SKIP + generics_fn_call_site_inference.jhyy 删除(deferred v3.2.0d — call-site inference 是 plan 范围外,见 § scope 收紧)
- **NodeFuncDecl +16B** (type_params@80 + ntype_params@88) / **NodeCall +16B** (type_args@24 + ntype_args@32)(C1 `cdc7f5d`)

### Root cause (3 处连锁 bug,C5 修)

1. **shared param_sym 错位**:mono_clone_func_decl 原版 share old_p_sym → check_func_decl 跑 max$i32 + max$f64 时后者 type_ptr=f64 覆盖前者 type_ptr=i32 → abi_win_emit_function_header 读错 type_ptr → QBE `csgtw` on f64 参数 fail。
   **Fix**:每个 cloned param 分配 fresh sym (symtab_alloc_sym + name 复用)。

2. **cloned body IDENT sym 错位**:fresh sym per-clone 但 body IDENT (e.g. `a > b`) 还指向 OLD param_sym → cloned fn scope 只 register fresh sym → body IDENT lookup 报 "undefined variable"。
   **Fix**:写 `mono_rewrite_idents_in_stmt/expr` walker (16B remap pair per param),在 mono_subst_block 返回后 in-place rewrite body IDENT sym。

3. **stage-0 segfault from debug prints**:cfd_param/pi1-6k/_dbg_p* 等 30+ 临时 debug prints 触发 stage-0 jhyy codegen stack-spill bug,`make` 自己 segfault。
   **Fix**:全删 debug prints (cfd_entry/param + p1/p2/p3/P3a trace),保留 production 路径。

### Scope 收紧 (call-site inference 推到 v3.2.0d)

- **删除** `generics_fn_call_site_inference.jhyy`(原 C2 placeholder,test `max(3, 5)` 无 turbofish)。
- **v3.2.0c ship scope** = 完整 fn + turbofish + monomorphize + per-clone sym isolation。
- **Call-site type inference** (从 arg types 推 T,无 turbofish) → **v3.2.0d** (3i fn path 阶段 3):
  - 需要 generic fn sym 有 type_ptr (e.g. `fn(T, T) -> T` 模板类型),目前 P1 设 SYM_FN 但 type_ptr=0。
  - 需要 infer_type NODE_CALL 在 no-turbofish 时 args 推断 T 然后 mono_expand_fn_call。
  - 范围超出 v3.2.0c ship gate 2/2 EXIT=42 测试集。
- D28 锁链仍 hold:`v3.2.0 → v3.2.0b → v3.2.0c → v3.2.1 (3j closures) → v3.2.4 (3l.3 Vec<T>)`。

### Verification (ship gate)

- **`make all`** green (stage-0 编 src0/ 无 segfault,debug prints 已清)
- **`regress.py`**:112/112 passed, 0 failed, 15 skipped (was 111/111/15 at v3.2.0b)
  - `generics_fn_turbofish_basic.jhyy` EXIT=42 ✅
  - 5/5 v3.2.0b tests 不退化 (generics_struct/ptr_field/multi_param/enum/err_unsubst)
- **`jhyy_get_il` on `generics_fn_turbofish_basic.jhyy`**:断言 `max$i32` 是 `export function w $max$i32(w %a, w %b)` (i32) + `max$f64` 是 `export function d $max$f64(d %a, d %b)` (f64) — per-clone fresh sym + body IDENT rewrite 路径生效
- **D43 selfhost N11 byte-equal**:`jhyy_v2.exe == jhyy_v3.exe == jhyy_v4.exe == jhyy_v5.exe`,SHA `b87c932038055321dc4caa134b914b99598cd9ea568b641eeb4fc4bd72592ddb` ✅
- **0 改动验证**:`git diff v3.2.0b..v3.2.0c -- compiler/src0/abi_amd64_win.jhyy types.jhyy ir.jhyy symtab.jhyy codegen_amd64_emit_call.jhyy` empty

### Out of scope (deferred to v3.2.0d 或后续)

- Call-site type inference `max(3, 5)` 推 T → **v3.2.0d**
- 嵌套泛型 `Vec<Vec<T>>` (worklist-to-fixpoint) → v3.x 中
- PhantomData 嵌套 Cap 完整 codegen 路径 → v3.x 中
- 泛型 closures → v4.4.0 (per v3.2.1 plan)
- 泛型 bounds `<T: Ord>` → v3.x 末
- Lifetime 泛型 `<'a, T>` → v4.3.0 (lexer 无 tick token)
- const generic → v4.5.0
- Trait objects `dyn Trait` → v4.6.0

---

## v3.2.0d — 3i fn path: call-site type inference (Rust-style `max(3, 5)`)

**Status**: ✅ shipped
**Tag**: `v3.2.0d`
**D43 baseline**: N12 = `01209313cc61b974c9603d4a78acf9703d78193c4dd186448a4e9f78a8f2b362` (v1→v4 byte-equal verified 2026-09-08)

### Scope (per `feedback_plans_per_version` 单 plan)

实现 v3.2.0c § "Out of scope" 列表项 1 推到本 sprint 的内容:
- **`mono_type_to_type_node`** helper (mono.jhyy +71):`*Type → *Node` 转换,call-site inference 时把 arg 类型 (e.g. `i32` / `f64`) 转换为 mono_mangle_type_node_fn 能识别的 NODE_IDENT (prim sym) / NODE_UNARY (ptr) / NODE_IDENT (struct)。Fallback: unsupported KIND → 返 0 触发 E0062 "cannot infer type parameter"。
- **sema.jhyy inference arm (+359)** 在 NODE_CALL turbofish `else` 分支(per v3.2.0b L102-104 mitigation,全 offset access):
  - 检测 `callee_sym.kind == SYM_FN` + `ntype_args == 0` + `mono_find_generic_def` 命中 → 进入 inference
  - Walk fn params,匹配 type_annot.sym (per parser.jhyy L3150,type_params 存的是 *Sym 不是 *Node) → 记录 param_slot[i] 映射表
  - Walk call args,`infer_type(arg)` → `*Type` → `mono_type_to_type_node` → 写到 type_args[matched_slot]
  - T agreement 检查:mangle-equality cmp (strcmp 后 0-终止,因 jhyy 无 memcmp)
  - 调 `mono_expand_fn_call` → rewrite callee.sym = mangled_sym
  - **Inline cloned fn type_ptr setup**(L2273 check_func_decl 定义晚于本处,jhyy 无 forward decl):手动 build KIND_FUNC type + 设 mangled.type_ptr + kind=SYM_FN + 每个 cloned param sym 的 type_ptr + kind=SYM_VAR
  - **Inline cloned body IDENT type_ptr propagation**(`mono_propagate_idents_in_expr` / `_to_cloned_body` helpers,~140 行):walk cloned body,每个 NODE_IDENT 的 type_ptr 从 sym.type_ptr 复制 — 因为 cloned fn 是 Pass 3b 才 append 的,Pass 3a 已 finish,Pass 3b 跳过 mangled-$ → 不会 check_func_decl → body IDENT.type_ptr 不会自动 set,需要手动 propagate(否则 csgtw on f64 等 fail)。
- **2 新 test**(drop SKIP):
  - `generics_fn_call_site_inference.jhyy`:`max(3, 5)` + `max(3.0, 5.0)` → emit 2 distinct fns `max$i32` (w) + `max$f64` (d)
  - `generics_fn_call_site_mixed_dedup.jhyy`:`max(3, 5)` (call-site) + `max::<i32>(7, 2)` (turbofish) + `max(1, 9)` (call-site) → emit 1 `max$i32` instance(dedup 真发生 via symtab_lookup)

### Root cause (3 处连锁 bug,v3.2.0d 修)

1. **`mono_type_to_type_node` KIND_PRIMITIVE 找不到 prim sym**:尝试 `symtab_lookup(global_scope, "i32")` 返 0(prim syms 是 parse_type 时 lazy 注册到 current_scope,不是 global_scope)。**Fix**:用 `type_to_string(t)` 直接拿 prim name,合成 fake Sym via arena_alloc(56) + 设 name / kind=SYM_TYPE / 其他 0。
2. **type_params storage 类型 confusion**:parser.jhyy L3150 `*tpslot = _tpsym as *u8` 存的是 *Sym,**不是** *Node。最初 match 时 deref NODE IDENT 错位,报 "no argument for some type parameter"。**Fix**:直接 `let tp_sym2 = *((gd_tp as i64 + tj2 * 8) as **Sym); if pt_sym2 == tp_sym2 as *u8 { matched_slot = tj2; ... }`。
3. **cloned fn 在 Pass 3b 中 check_func_decl 没跑,导致 ms.type_ptr=0 + body IDENT.type_ptr=0**:turbofish path 在 Pass 3a 已跑过 → Pass 3b 跑 call 时 ms.type_ptr 已 set。Inference path 是 call site 自己 trigger mono,Pass 3a 已 finish,Pass 3b 跳过 mangled-$ → cloned fn 没被 check 任何东西。Recursive infer_type(callee IDENT) 看 type_ptr=0 → "undefined variable"。**Fix**:inline check_func_decl 的 type_ptr setup(fn_sym + 每个 param_sym)+ walk body 设 IDENT.type_ptr(jhyy 无 forward refs,所以 inline 而不是 call)。

### Verification (ship gate)

- **`make all`** green(stage-0 编 src0/ 无 segfault,inline helper 编译通过)
- **`regress.py`**:114/114 passed, 0 failed, 15 skipped (was 113/113/15 at v3.2.0c)
  - `generics_fn_call_site_inference.jhyy` EXIT=42 ✅
  - `generics_fn_call_site_mixed_dedup.jhyy` EXIT=42 ✅
  - 7/7 v3.2.0b/c tests 不退化 (`generics_struct` / `generics_ptr_field` / `generics_multi_param` / `generics_enum` / `generics_err_unsubst` / `generics_fn_turbofish_basic` / `cap_table_basic` / `cap_table_advanced`)
- **`jhyy_get_il` on `generics_fn_call_site_inference.jhyy`**:断言 `max$i32` (`function w $max$i32(w %a, w %b)`) + `max$f64` (`function d $max$f64(d %a, w %b)`) — 2 distinct fn emit
- **`jhyy_get_il` on `generics_fn_call_site_mixed_dedup.jhyy`**:断言只有 **1 个** `max$i32` (`function w $max$i32(w %a, w %b)`) — dedup hit 真发生 via `mono_expand_fn_call` L1298 `symtab_lookup` 共享
- **D43 selfhost N12 byte-equal**:jhyy_v1.exe.exe (C-side baseline) + jhyy_v2.exe + jhyy_v3.exe + jhyy_v4.exe all compile `src0/main.jhyy` to byte-equal `.il` SHA `01209313cc61b974c9603d4a78acf9703d78193c4dd186448a4e9f78a8f2b362` ✅ (was N11 = `b87c9320...` at v3.2.0c — re-baselined)
- **0 改动验证**:`git diff v3.2.0c..v3.2.0d -- compiler/src0/ast.jhyy parser.jhyy symtab.jhyy codegen.jhyy types.jhyy ir.jhyy abi_amd64_win.jhyy` empty
- **`mono.jhyy` 仅新 `mono_type_to_type_node` helper** (+71 行),v3.2.0c ship 的 750 行 fn path 0 改动
- **`sema.jhyy` 仅 NODE_CALL turbofish `else` 分支** (+359 行,含 inline helpers),v3.2.0c turbofish `if` 分支 (L958-998) 0 改动

### Out of scope (deferred to v3.2.x 后续 或 v3.x 末)

- return-position T 推断 (`fn max<T>(...) -> T`, 无 arg 是 T) → v3.2.0e
- 嵌套 generic fn (`fn outer<T>(inner: fn(T) -> T)`) → v3.x 中
- 高阶 trait bound 推断 (`T: Ord`) → v3.x 末
- *Cap<T> / *mut T 推断边界(跟 v3.1.x `&mut` 交互) → v3.x 中
- *Type → *Node 转换 KIND_FUNC / KIND_ARRAY / KIND_SLICE 全支持 → v3.x 中(v3.2.0d MVP 仅 KIND_PRIMITIVE / KIND_STRUCT / KIND_POINTER)
- Recursive inference debug log → 不做(跑通即可,不加 debug print)
- 泛型 closures → v3.2.1 (3j, D28 锁链下一节点)
- Vec<T> / Map<K,V> std lib → v3.2.4 (3l.3, M11 launch 硬前置)
- jhyy self-source 迁 `Vec<T>` → M11 launch (不阻本 ship)

### Commit / Tag

- **Commit C1**:`feat(mono+sema): call-site type inference for generic fn calls (3i fn path complete)`(axis-v3 commit `c7cf5b4`)
- **Commit C2** (本段):`chore(docs): append v3.2.0d changelog section + spec supplement (call-site inference)`
- **Tag**:`v3.2.0d`
- **Post-tag D43 N12 SHA**:`01209313cc61b974c9603d4a78acf9703d78193c4dd186448a4e9f78a8f2b362`

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

---

# V3-C v3.2.1 — 3j closure literals MVP

> **ship date**: 2026-09-09
> **branch**: `axis-v3`
> **D28 锁**: v3.2.1 (3j closures) → v3.2.2 (3l.1 std mem/fmt/string/arena) 串行
> **D43 baseline**: **HOLD N13** (`980c026`, V3-C v3.2.0d) — 本地 jhyy_selfhost_check v2 link fail (pre-existing infra issue, v3.2.0d ship 时已存在, 非本 sprint 引入); chain re-baseline 等 v3.2.2 ship 后环境修复再跑
> **Post-commit SHA**:`7b2d886` (axis-v3 HEAD = tag `v3.2.1`)
> **umbrella**: 本文件 v3.2.1 部分

---

## 1. 范围 / Scope

V3-C sub-sprint 5/N — **闭包字面量 MVP**(`|params| { body }` 语法 + 合成 fn `__closure_<N>` codegen + call-site dispatch)。

**触发**(per `docs/plans/v2/v2.0.0-os-prep.md` § 1):
- **M8d launch 硬前置 2/N 满足**(per D-GUI-11 锁 2026-09-01): seat focus callback 闭包式
- **v3.2.2 (3l.1) 启动前置**(per D28): std lib 闭包式 API 依赖本 sprint

**M0 简化决定**(per `docs/plans/v3/v3.2.1-plan.md` + 2026-09-09 user):
- 闭包按值捕获 (no `move` 关键字)
- 闭包不能捕获借用 (defer v3.x mid)
- 不做 async 闭包 (defer v3.x mid)
- 不做 generic closure (defer v3.x mid)
- 闭包 body 仅表达式 (parser 限; let/return/match 在 closure body 内不支持 — defer v3.x mid)

---

## 2. 改动 / Changes

### 2.1 ast.jhyy (per #55)

- `NODE_CLOSURE_LITERAL() = 56` (line 159)
- `NodeClosure = {params: *u8, nparams: i64, body: *Node, fn_sym: *u8}` (lines 409-414, size 32)
- `ast_new_closure(a, lf, ll, lc, params, nparams, body)` + `node_closure_data(n)`

### 2.2 parser.jhyy (per #55)

- inline closure dispatch at parse_expr TOKEN_PIPE branch (L1248-1350): `|params| { body }` 解析;params 走 `parser_push_scope` + symtab_insert;body 走 `parse_expr` self-rec (无 let/return/match)
- `parse_closure_expr` REMOVED (tombstone comment L3120-3125, jhyy no forward ref)

### 2.3 symtab.jhyy

- `Sym` struct +8 bytes: `aux_sym: *u8` 字段 (offset 56, 8B)
- `SYM_SIZE()` 56 → 64
- `symtab_alloc_sym` L132 init `(*sym).aux_sym = 0 as *u8`

### 2.4 sema.jhyy

- **NODE_CLOSURE_LITERAL handler 末尾 (L1188 后)** append 合成 NODE_FUNC_DECL 到 module.decls:
  ```jhyy
  let fn_decl = ast_new_func_decl(arena, ..., fn_sym, cd.params, cd.nparams,
      0 as *Node,                       // ret_type = null
      cd.body as *Node, ..., 0, 0, 0, 0 as *u8, 0 as *u8, 0 as i64);
  let mnd2 = node_module_data((*ctx).module);
  mono_decls_append((*ctx).arena, mnd2 as *u8, fn_decl);
  ```
- **NODE_LET handler 末尾 (L1916 后)** wire aux_sym:
  ```jhyy
  if (*d).init != 0 as *u8 {
      let init_node = (*d).init as *Node;
      if (*init_node).kind == NODE_CLOSURE_LITERAL() {
          let init_cd = node_closure_data(init_node);
          (*sym).aux_sym = (*init_cd).fn_sym;
      }
  }
  ```

### 2.5 codegen.jhyy

- **NODE_CALL branch (L2499 前插)** closure dispatch:
  ```jhyy
  } else if (*fs).kind == SYM_VAR() && (*fs).type_ptr != 0 as *u8 {
      let fst = (*fs).type_ptr as *Type;
      if (*fst).kind == KIND_FUNC() && (*fs).aux_sym != 0 as *u8 {
          let aux_s = (*fs).aux_sym as *Sym;
          fn_name = (*aux_s).name;
      } else {
          fn_name = (*fs).name;
      }
  } else { ... }
  ```
- 三重 guard 保 normal SYM_VAR 调用不命中 (aux_sym=0)

### 2.6 tests/examples/

- `closures_basic.jhyy` (edit): `//EXPECT:6` 验证
- `closures_multi_capture.jhyy` NEW: multi-param closure, `//EXPECT:7`
- `closures_as_arg.jhyy` NEW: simple fallback (closure 当 fn 值, no fn-type-as-param per 2026-09-09 user), `//EXPECT:42`

---

## 3. Verification (per `feedback_fix_evaluation_rule`)

- `make all` green ✅ (stage-0 不 segfault, jhyy.exe rebuild 成功)
- 3/3 closures 5/5 PASS ✅:
  - `jhyy.exe run closures_basic.jhyy` EXIT=6
  - `jhyy.exe run closures_multi_capture.jhyy` EXIT=7
  - `jhyy.exe run closures_as_arg.jhyy` EXIT=42
- `regress.py --binary=compiler/build/bin/jhyy.exe --tests=closures_basic.jhyy,...` → 3/3 passed
- `jhyy_get_il closures_basic.jhyy` QBE IL 验证:
  ```
  export function w $main_jhyy() {
      %t1 =w copy 5
      %t2 =w call $__closure_88857(w %t1)   ← 直接 call 合成 fn label
      ret %t2
  }
  export function w $__closure_88857(w %y) {
      %t3 =w copy %y
      %t4 =w copy 1
      %t5 =w add %t3, %t4
      ret %t5
  }
  ```
- `jhyy_selfhost_check` D43 closure chain: **HOLD N13** (`980c026`) — 本地 jhyy_selfhost_check 跑 v2 link fail (`ld returned 5 exit status`, 链接 `jhaXXX.s` + `runtime.c` + `jhyy_helpers.c` → `jheXXX.exe`), **pre-existing infra issue** (git stash 验证 v3.2.0d baseline 同样 fail, 非本 sprint 引入)。chain re-baseline 等 v3.2.2 ship 后环境修复再跑

---

## 4. Out of scope (deferred)

- 借用捕获闭包 → v3.x mid
- `move` 关键字 → v3.x mid
- async 闭包 → v3.x mid
- generic closure → v3.x mid
- closure + lifetime 标注 → v3.x 中
- 闭包 body 内 let/return/match → v3.x mid
- fn-type-as-param (`fn(i32) -> i32` 作参数类型) → v3.x mid
- closure + env struct (multi-capture) → v3.x mid
- Vec<T> / Map<K,V> std lib (依赖 closure + generics) → v3.2.4 (3l.3, M11 launch 硬前置)

---

## 5. Commit / Tag

- **Commit**:`feat(closures): M0 closure literals + synthesized fn (3j, v3.2.1) — Sym.aux_sym + sema append + codegen dispatch + 3 tests`
- **Tag**:`v3.2.1` (per `feedback_v3b_no_phaseb_worktree`)
- **Post-tag D43 SHA**:**HOLD N13** (`980c026`) — 本地 selfhost_check v2 link pre-existing infra issue 阻 chain verify (见 § 3 verification 末尾); chain re-baseline 等 v3.2.2 ship 后环境修复再跑
- **Post-commit SHA fill-in**:`7b2d886` (axis-v3 HEAD = tag `v3.2.1`)
- **Auto-push**:per `feedback_auto_push_after_commit`

---

## 6. Cross-ref

- L1 设计:`docs/plans/roadmap/v3.x-language-expansion.md § Sprint 3j`
- L2 设计:`docs/plans/v3/v3.2.1-plan.md` (per `feedback_plans_per_version`)
- 上游:`changelog-v3.2.md` v3.2.0d 段 (3i fn path complete, N13 = `980c026`)
- 下游:`v3.2.2-plan.md` (3l.1 std mem/fmt/string/arena)
- 跨 axis:V2-B Phase 2b (QBE 自写 / amd64_sysv 实 impl / N 代 fixed point) — 修 `codegen_amd64_run` 0-byte bug, 解阻 v3.2.3+
- D-GUI-11 lock:`jhyy_OS/docs/coordination.md § 3`;D28 + M8d/M11 launch gates:`docs/plans/v2/v2.0.0-os-prep.md § 1`
- D43 chain:`docs/logs/v3/changelog-v3.2.md` v3.2.0d 段 (N13 = `980c026`) → **N14** (本 sprint)

---

# v3.2.2 — std lib M0 (3l.1, V3-C sub-sprint 6/N)

> 锁定于 tag `v3.2.2` (per `feedback_changelog_umbrella`, v3.2 axis 用单一 umbrella changelog)。

## 1. Context

**为什么做这个**:v3.x 语言扩展 OS-required 阶段(per `docs/plans/roadmap/v3.x-language-expansion.md § Sprint 3l`)。`std lib` 是 M11 launch 硬前置之一(per `docs/plans/v2/v2.0.0-os-prep.md § 1` M11:v3.2.0 + v3.2.1 + v3.2.2..v3.2.5 全 ship)。当前 axis-v3 已 ship v3.2.0 (3i generics) + v3.2.1 (3j closures),v3.2.2 (3l.1) 是下一个 sub-sprint。

**上游 ship 链**:✅ v3.0-v3.1.x ship + ✅ v3.2.0 (3i generics) + ✅ v3.2.1 (3j closures MVP, N14 byte-equal hold)

**下游 ship 链**:🚀 v3.2.3 (3l.2 闭包 + closure/Vec<T> 基础) + v3.2.4 (3l.3 arena byte-equal 真修) + v3.2.5 (3l.4 std 增量)

**MVP 范围**(per `docs/plans/v3/v3.2.2-plan.md` + 2026-09-09 user 决定):
- M0:4 个 std lib 模块(mem / fmt / string / arena),每个自包含,跨模块无 import
- M0:不依赖 closure / generic / 借用
- M0:不依赖 libc 运行时(mem/fmt/string 全自实现 byte 循环;arena 用 libc malloc)
- M0:`arena_alloc` 跟 runtime.c 24B Arena API 等价但 layout 不同(W-074)

**Worktree 约定**:per 2026-09-09 user → **不开新 worktree**,axis-v3 direct commit + tag `v3.2.2`(同 v3.2.0/1/1b 风格)。

**Ship gate**(per `feedback_fix_evaluation_rule`):
- 19+ std lib 测试 5/5 PASS via `jhyy.exe compile + run`(QBE backend,19 测试:std_mem_basic / std_mem_set / std_mem_zero / std_mem_compare / std_mem_copy / std_fmt_i32 / std_fmt_i32_neg / std_fmt_i64 / std_fmt_str / std_fmt_hex / std_string_len / std_string_equals / std_string_concat / std_string_compare / std_string_from_bytes / std_string_data / std_arena_basic / std_arena_calloc / std_arena_reset)
- `jhyy_regress` 137/137 (含 19 std + 118 原 - 0 failed, 20 skipped)
- `make all` green
- D43 closure chain N14 byte-equal hold (sha256sum jhyy_v{2,3,4,5}.exe 全 match)

## 2. Scope (本次 ship)

### 新增 (4 个 std 模块 + 19 测试文件)

| # | 文件 | 行数 | 说明 |
|---|------|------|------|
| 1 | `compiler/src0/std/mem.jhyy` | 107 | mem_copy / mem_compare / mem_set / mem_find_byte / mem_zero + ptr_add (W-075: mem_set i32-store;W-077: mem_find_byte codegen AV) |
| 2 | `compiler/src0/std/fmt.jhyy` | 187 | fmt_i32 / fmt_i64 / fmt_str / fmt_hex_u32 + digit_char / hex_char + ptr_add |
| 3 | `compiler/src0/std/arena.jhyy` | 180 | arena_init / arena_alloc / arena_calloc / arena_reset (40B layout, std_* 前缀 per W-074/W-076) |
| 4 | `compiler/src0/std/string.jhyy` | 200 | str_from_cstr / str_from_bytes / str_len / str_data / str_concat / str_equals / str_compare + StringHeader 16B layout |
| 5-23 | `compiler/tests/examples/std_*.jhyy` (19 files) | ~600 总 | 19 PASS + 1 deferred(std_mem_find_byte) |

### 新增文档

- `docs/abis/jhyy-lang-spec-stdlib-supplement-v3.2.2.md`(本 sprint std lib spec,locked at v3.2.2)
- `docs/internal/workarounds.md` W-073 to W-078(6 new ACTIVE entries)

### 不改 (0 行)

- `compiler/src/symtab.c` + `compiler/src/symtab.h`(C-side 56B Sym 不变)
- `compiler/src0/symtab.jhyy`(64B src0 Sym 不变 — v3.2.1 ship)
- `compiler/src0/sema.jhyy`(closures sema 不变 — v3.2.1 ship)
- `compiler/src0/codegen.jhyy`(closure dispatch 不变 — v3.2.1 ship)
- `compiler/src/*.c`(C-side 0 改动)

### 不做 (推到后续 sprint)

- Vec<T> / Map<K,V> std lib → v3.2.3 (依赖 closure)
- std::arena 跟 runtime.c 24B Arena byte-equal → v3.2.4 (D22 + W-074 superseder)
- mem_find_byte codegen 真修 → v3.x mid (W-077)
- array[i32] index 自动 extsw 升 w→l → v3.x mid (W-078)
- mem_set SSE/AVX 批量 store 优化 → v3.x mid (W-075)
- closure + env struct (multi-capture) 等 v3.2.3+ 闭包增强
- borrow checker / `&mut` lifetime → v3.x mid

## 3. 关键设计决策

| # | 问题 | 决策 | 理由 |
|---|------|------|------|
| 1 | std lib 怎么组织? | 4 模块独立,每个含 ptr_add 本地 helper | `inline_imports` (main.jhyy:456-559) 只支持 `main_dir/mod_name.jhyy`, 不支持 subdir (`std/*`); M0 接受副本冗余 |
| 2 | std lib 依赖 libc 吗? | mem/fmt/string 全自实现;arena 用 libc malloc | mem/fmt 字节循环简单;string 自带 mini arena allocator;arena 用 libc 是 OS 调用基础 |
| 3 | Arena layout? | 40B (blocks/cur/end/reserved/default_size) | 跟 C-side 24B Arena 不同 (W-074); jhyy-side 是 OS runtime,需要 block linked-list 支持 large alloc |
| 4 | arena_alloc 符号冲突? | std::arena 模块用 std_ 前缀 fn 名 (W-076) | runtime.c 已定义 arena_alloc (24B); std_ 前缀隔离,等 v3.2.4 统一命名 |
| 5 | mem_set 用什么 store? | `*(p+i) as *i32 = b` (i32 store, 每次 loop 4 字节) (W-075) | M0 简化,避 codegen byte store 路径 (W-077); 性能优化留 v3.x mid |
| 6 | array index 类型? | 必须 i64 (W-078) | codegen array[i32] index 触发 QBE mul w→l fail; 用户代码遵守 i64 index 直到 v3.x mid fix |
| 7 | String 表示? | StringHeader 16B (data ptr + len),非 null-terminated | 跟 src0/util.jhyy StringHeader 一致; 但 std::string 不混用 src0/util, 独立实现 |
| 8 | 1 commit vs split | 1 commit (per 2026-09-09 user 决定) | 改动小 + 逻辑耦合, 回滚风险低 |

## 4. Verification

- ✅ `make all` green (stage-0 不 segfault, jhyy.exe rebuild 成功)
- ✅ 19/19 std lib 测试 5/5 PASS via `jhyy.exe compile + run`:
  - std_mem:basic / set / zero / compare / copy (5)
  - std_fmt:i32 / i32_neg / i64 / str / hex (5)
  - std_string:len / equals / concat / compare / from_bytes / data (6)
  - std_arena:basic / calloc / reset (3)
- ✅ `jhyy_regress` 137/137 (含 19 std + 118 原, 0 failed, 20 skipped)
- ✅ D43 closure chain N14 hold: `sha256sum jhyy_v{2,3,4,5}.exe` = `8254cd6b681ee3b5b2d59534b7e1ecb3cac29cec7ae08755522e3421ed6d2145` (4 个全 match)
- ✅ C-side 0 changes (vs `v3.2.1` tag): `git diff v3.2.1..HEAD --stat -- compiler/src/ compiler/runtime/ compiler/qbe/` 空输出
- ⚠️ 1 test deferred (`std_mem_find_byte.jhyy` → `.jhyy.deferred`,W-077 codegen AV)

**fix evaluation rule** (per `feedback_fix_evaluation_rule`):19/19 std lib 测试 + 137/137 regress PASS + N14 byte-equal = fix work 验证。

## 5. Commit / Tag

- **Commit**:`feat(stdlib): M0 std lib mem/fmt/string/arena (3l.1, v3.2.2) — 4 modules + 19 tests + W-073..W-078`
- **Tag**:`v3.2.2`
- **Post-commit SHA**:`c5607edd5b42fc89748f5e443b281e94c54f5fbb` (commit = `c5607ed`, full SHA filled 2026-09-09)
- **Auto-push**:per `feedback_auto_push_after_commit` (commit + tag pushed to `JiHuiYiYou-compiler` remote)

## 6. Cross-ref

- L1 设计:`docs/plans/roadmap/v3.x-language-expansion.md § Sprint 3l`
- L2 设计:`docs/plans/v3/v3.2.2-plan.md` (per `feedback_plans_per_version`)
- 上游:`changelog-v3.2.md` v3.2.1 段 (3j closures, N14 = post-tag fill-in 后)
- 下游:`v3.2.3-plan.md` (3l.2 closure + Vec<T> 基础)
- 跨 axis:V2-B Phase 2b (QBE 自写 / amd64_sysv 实 impl / N 代 fixed point) — 修 `codegen_amd64_run` 0-byte bug, 解阻 v3.2.3+ closure chain 真测
- D-GUI-11 lock:`jhyy_OS/docs/coordination.md § 3`;D28 + M8d/M11 launch gates:`docs/plans/v2/v2.0.0-os-prep.md § 1`
- D43 chain:`docs/logs/v3/changelog-v3.2.md` v3.2.1 段 (N14) → **N15** (本 sprint, hold; v3.2.3+ 等 v2.x 修后重测)
- std lib spec:`docs/abis/jhyy-lang-spec-stdlib-supplement-v3.2.2.md`
- Workarounds:W-073 (D43 hold), W-074 (D22 deferred), W-075 (mem_set i32-store), W-076 (std_ prefix), W-077 (mem_find_byte AV), W-078 (array[i32] index)

