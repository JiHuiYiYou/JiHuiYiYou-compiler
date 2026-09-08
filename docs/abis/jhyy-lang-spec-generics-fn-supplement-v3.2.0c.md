# jhyy-lang-spec — Generics (fn + turbofish) Supplement (v3.2.0c)

> **Supplement 状态**: ✅ locked (v3.2.0c shipped 2026-09-08, tag `v3.2.0c`)
> — generic fn `fn max<T>(...)` syntax + turbofish `max::<T>(args)` parse +
> monomorphize runtime ACTIVE;per-clone fresh sym isolation 保证 codegen
> type letter 正确 (i32 → `w`,f64 → `d`)。配合
> [`../jhyy-lang-spec-v1.3.0.md`](../jhyy-lang-spec-v1.3.0.md) +
> [v3.2.0 generics supplement](jhyy-lang-spec-generics-supplement-v3.2.0.md) +
> [v3.2.0b generics supplement](jhyy-lang-spec-generics-supplement-v3.2.0b.md) +
> [Cap<T> supplement v3.1.0](jhyy-lang-spec-cap-t-supplement-v3.1.0.md) +
> [PhantomData<T> supplement v3.1.1](jhyy-lang-spec-phantomdata-supplement-v3.1.1.md)
> 读。
> **作者**: JHYY <15901598712@163.com>
> **日期**: 2026-09-08
> **范围**: V3-C v3.2.0c sub-sprint — 3i fn path 阶段 2:fn syntax + turbofish +
> monomorphize + per-clone sym isolation。Call-site type inference (无 turbofish)
> 推 v3.2.0d。

---

## 1. 范围 / Scope

v3.2.0c 解锁 v3.2.0b § "Out of scope" 列表项 1+2:
- **`fn max<T, U>(...)` 语法 parse**:parse_func generic arm
- **`max::<T, U>(args)` turbofish parse**:parse_expr IDENT primary branch
  3-token lookahead (IDENT + `::` + `<`)
- **`mono_clone_func_decl`**:深 clone NodeFuncDecl + 11 字段全 copy
- **`mono_subst_block` / `mono_subst_stmt` / `mono_subst_expr`**:全 stmt/expr
  kind walk (覆盖所有 v1.x-subset statement/expression node)
- **`check_func_decl` body skip**:generic fn (ntype_params > 0) skip check
- **`infer_type` NODE_CALL turbofish handling**:mono_expand_fn_call + callee
  sym rewrite 到 mangled sym
- **`cg_func` skip gate**:mirror check_func_decl skip pattern
- **`mono_expand_fn_call`**:per-call-site mangled_name symtab dedupe + clone
  + append

**0 行 codegen.jhyy / abi_amd64_win.jhyy / types.jhyy / ir.jhyy / symtab.jhyy
/ codegen_amd64_emit_call.jhyy 改动** — monomorphized fn 走现有 emit path
(`abi_win_emit_function_header` 读 `p_sym.type_ptr` 自动获得正确 QBE type
letter)。

### Out of scope (本 sprint 不做)

- **Call-site type inference** `max(3, 5)` 推 T → **v3.2.0d**
  (需要 generic fn sym 有 type_ptr=`fn(T,T)->T` 模板类型;
   需要 infer_type NODE_CALL 在 no-turbofish 时 args 推断 T)
- 嵌套泛型 `Vec<Vec<T>>` (worklist-to-fixpoint) → v3.x 中
- PhantomData 嵌套 Cap 完整 codegen 路径 → v3.x 中
- 泛型 closures → v4.4.0 (per v3.2.1 plan)
- 泛型 bounds `<T: Ord>` → v3.x 末
- Lifetime 泛型 `<'a, T>` → v4.3.0
- const generic → v4.5.0
- Trait objects `dyn Trait` → v4.6.0

---

## 2. 语法 / Syntax

### 2.1 Generic fn 定义

```
fn <name><<T1, T2, ..., Tn>>(<params>) -> <ret_type> { <body> }
```

- 紧跟 fn name 的 `<` 是泛型参数 list 起始哨兵
- type-param 命名约定:大写字母起 (UpperCamelCase or single T),避免跟
  小写 value-param 混淆
- type-param 跟 type inst 路径一致(`fn parse<T>` + `Vec<i32>` 中 i32 是 type
  arg,不是 type-param)
- type-param 默认在 fn body 局部 scope(`push_scope` + `pop_scope`),不污染
  module-global scope
- type-param 注册为 SYM_TYPE type_ptr=0 sentinel(跟 struct path 一致)

**示例**:
```jhyy
fn max<T>(a: T, b: T) -> T {
    if a > b { return a; }
    return b;
}

fn map<T, U>(f: fn(T) -> U, x: T) -> U {
    return f(x);
}
```

### 2.2 Turbofish call-site

```
<expr>::<T1, T2, ..., Tn>(<args>)
```

- 3-token lookahead: IDENT + `::` + `<`
- turbofish 后必须紧跟 `(`(call),否则报错
- type-args 跟 type-param 位置 1:1 对应(arity check 在 `mono_expand_fn_call`:
  `ntype_args == fn.ntype_params`)
- turbofish type-args 存到 NODE_CALL.type_args/ntype_args(parser 在
  IDENT primary branch 解析,postfix `(` call wrap 时读走)
- LL(1) parser — `::` 后 commit(无 rollback);如果 `::` 后不是 `<`,报 syntax error

**示例**:
```jhyy
let mi: i32 = max::<i32>(3, 5);
let mf: f64 = max::<f64>(3.0, 5.0);
let r: U = map::<i32, f64>(int_to_f64, 42);
```

### 2.3 Call-site inference (v3.2.0d NOT in v3.2.0c)

`max(3, 5)` 无 turbofish → v3.2.0c 报 E0062 "undefined variable"(generic fn
sym 在 sema NODE_IDENT 路径走 type_ptr=0 分支,落到 "undefined variable")。
v3.2.0d 加 call-site inference(sema.infer_type NODE_CALL 检查 callee 是否
generic fn + 推断 T from args)。

---

## 3. Monomorphize 规则 / Monomorphize Rules

### 3.1 Mangled name

`<base_name>$<type_arg_1>$<type_arg_2>...$<type_arg_n>`

- 每个 type-arg 走 `type_to_string`(per v3.2.0 spec § 3.2)
- 多 type-arg 用 `$` 分隔
- type-param 不出现在 mangled name(只有 concrete type-arg)
- 跟 struct path 一致 — `Pair<i32, f64>` → `Pair$i32$f64`

**示例**:
```jhyy
fn max<T>(...)              → base_name = "max"
max::<i32>(...)             → mangled_name = "max$i32"
max::<f64>(...)             → mangled_name = "max$f64"
fn map<T, U>(...)
map::<i32, f64>(...)        → mangled_name = "map$i32$f64"
```

### 3.2 Clone 策略

`mono_clone_func_decl` 深克隆整个 NodeFuncDecl:
- 11 个 NodeFuncDecl 字段全 copy:
  - sym (cloned fn 用 mangled sym,原 `max` sym 由 mono_expand_fn_call 覆盖)
  - params (per-param deep clone + type_annot substitute)
  - nparams
  - ret_type (mono_subst_node 替换 T→concrete)
  - body (mono_subst_block 替换 T→concrete + 后续 IDENT sym rewrite)
  - is_extern / is_inline / is_naked / link_section / defers / ndefers
  - type_params → 0/NULL(cloned fn 是 non-generic)
  - ntype_params → 0
- **Per-clone fresh param sym** (C5 bug fix):
  - 不 share 旧 param_sym(避免 check_func_decl 跨 cloned fn 互相覆盖 type_ptr)
  - 每个 cloned param 调 symtab_alloc_sym,fresh allocation + name 复用
- **Body IDENT sym rewrite** (C5 bug fix):
  - mono_subst_block 不替换 non-type-param IDENT sym
  - 单独写 mono_rewrite_idents_in_stmt/expr walker,16B remap pair per param
  - 在 mono_subst_block 返回后调,rewrite IDENT sym `old_param_sym → cloned_p_sym`

### 3.3 Dedupe 策略

Per-call-site mangled_name 查 global_scope symtab:
- 命中 → skip(cloned fn 已存在,re-use)
- miss → 调 symtab_insert 注册 mangled sym as SYM_FN type_ptr=0 +
  调 mono_clone_func_decl + overwrite cloned.sym + append cloned to module.decls

注意:首次插入是 SYM_FN type_ptr=0,然后 check_func_decl(Pass 3a,优先于
non-mangled fn)跑 cloned fn → 升级 type_ptr=fn_type。

### 3.4 Codegen 路径

- **Original generic def** (`fn max<T>`):ntype_params=1 →
  `check_func_decl` skip (return 1) + `cg_func` skip (return 1)。
  0 codegen 输出。
- **Cloned concrete fn** (`fn max$i32`):ntype_params=0 →
  `check_func_decl` 走 normal 路径,设 `(*param_sym).type_ptr = pt` →
  `cg_func` 走 normal 路径,`abi_win_emit_function_header` 读
  `p_sym.type_ptr` → 正确 QBE type letter (`w` for i32, `d` for f64)。

### 3.5 多 cloned fn 共享原 def

原 generic def 本身不 emit,只作 AST template;所有 call-site 触发
mono_expand_fn_call 生成 cloned fns。Pass 3a (cloned fns first) 确保 cloned
fn 的 SYM_FN sym (with type_ptr=fn_type) 在 caller (e.g. main_jhyy) 的
NODE_CALL resolution 之前就位。

---

## 4. AST 扩展 / AST Layout

### 4.1 NodeFuncDecl 扩展

v3.2.0c 在 v3.2.0b 基础上 +16B (total 96B):
```
offset  field          size  type
0       sym            8     *Sym        (cloned: mangled sym from mono_expand_fn_call)
8       params         8     *u8         (NodeFuncDeclParam 数组,each 16B)
16      nparams        8     i64
24      ret_type       8     *Node
32      body           8     *Node
40      is_extern      4     i32
44      is_inline      4     i32
48      defers         8     *u8
56      ndefers        8     i64
64      is_naked       4     i32
68      pad            4     -
72      link_section   8     *u8
80      type_params    8     *u8         (NEW v3.2.0c — type-param sym 数组)
88      ntype_params   8     i64         (NEW v3.2.0c)
```

NODE_FUNC_DECL_SIZE: 80 (v3.2.0b) → 96 (v3.2.0c)

### 4.2 NodeCall 扩展

v3.2.0c +16B (total 40B):
```
offset  field          size  type
0       callee         8     *Node
8       args           8     *u8         (arg node 数组)
16      nargs          8     i64
24      type_args      8     *u8         (NEW v3.2.0c — turbofish type-arg 数组)
32      ntype_args     8     i64         (NEW v3.2.0c)
```

NODE_CALL_SIZE: 24 → 40

`ast_new_call` signature:
```
fn ast_new_call(arena, loc_filename, loc_line, loc_col,
                callee, args, nargs,
                type_args, ntype_args) -> *Node
```

### 4.3 NodeFuncDeclParam 不变

`sym @0 (8) + type_annot @8 (8) = 16B` — cloned 时 per-param fresh sym
(symtab_alloc_sym) + new_p_annot (mono_subst_node)。

---

## 5. Parser 路径 / Parser Pipeline

### 5.1 parse_func generic arm

触发:`fn NAME <`
- peek `<` after fn name → 上推 generic arm
- push_scope (per-fn type-param 局部)
- loop: parse IDENT + comma + insert SYM_TYPE type_ptr=0 到 current scope
- exit loop on `>`
- 后续 params / ret / body 走 normal path
- fn decl 解析完后 pop_scope

### 5.2 parse_expr turbofish arm

触发:IDENT primary branch 命中 `NAME :: <`
- peek IDENT + `::` + `<` 3-token lookahead
- commit `::`(LL(1) no rollback)
- parser_mangle_type_node:解析 `<T1, T2, ...>` 成 typed args 数组
- parser_record_generic_inst:记录 `{base_name, mangled_name, [type_arg_nodes]}`
  到 parser.generic_insts
- 设 `pending_targs = tfargs; pending_ntargs = ntfargs` (local in parse_expr)
- left = ast_new_ident(... turbofish_sym ...) (turbofish_sym 是 base_name 的 SYM_FN)
- postfix `(` 路径:读 pending_targs/pending_ntargs,传给 ast_new_call 作为
  type_args/ntype_args

注意:`::` 后必须是 `<` 才能 commit;否则 syntax error (qualified call `mod::fn(...)`
走 NODE_QUALIFIED_CALL 路径,不通过本 arm)。

---

## 6. Sema 路径 / Sema Pipeline

### 6.1 check_func_decl body skip (Pass 3)

```jhyy
let fd_off = fd as i64;
let ntp_off = (fd_off + (88 as i64)) as *i64;  // NodeFuncDecl.ntype_params @ 88
if *ntp_off > (0 as i64) {
    return 1 as i32;  // skip generic fn body
}
```

offset access(per v3.2.0b mitigation L102-104)避免 stage-0 jhyy codegen
stack-spill bug 在 `(*fd).ntype_params` deep nested deref 触发。

### 6.2 Pass 3a — cloned fns first

v3.2.0c 引入 2-pass Pass 3:
- **Pass 3a**:遍历 `(*md).decls`,对每个 NODE_FUNC_DECL whose sym name contains
  `$`(mangled) → 调 check_func_decl(cloned fn 此时 ntype_params=0,不 skip,
  升级 SYM_TYPE → SYM_FN + 设 type_ptr=fn_type)
- **Pass 3b**:其他 fns(regular + non-mangled generic)

为何需要 2-pass:Pass 1.5 (mono_expand_module) 把 cloned fn 的 sym 插入
global_scope as SYM_TYPE type_ptr=0(check `if (*gsym).type_ptr != 0` 会
fail);Pass 3a 在 caller (main_jhyy) NODE_CALL resolution 之前先把 cloned
fn 升级到 SYM_FN + fn_type,caller 找 mangled sym 时命中。

### 6.3 infer_type NODE_CALL turbofish

```jhyy
let d_off = d as i64;
let nta_off = (d_off + (32 as i64)) as *i64;  // NodeCall.ntype_args @ 32
let nta_val = *nta_off;
if nta_val > (0 as i64) {
    let callee_ptr = *((d_off as i64) as **u8);  // callee @ 0
    if callee_ptr != (0 as *u8) {
        if *((callee_ptr as i64) as *i32) == NODE_IDENT() {  // callee kind
            let callee_id_pre = node_ident_data(callee_ptr as *Node);
            let callee_sym_pre = *((callee_id_pre as i64) as **Sym);
            if (*callee_sym_pre).kind == SYM_FN() {
                let ta_ptr = *((d_off + (24 as i64)) as **u8);  // type_args @ 24
                let mangled_sym = mono_expand_fn_call(
                    (*ctx).global_scope, (*ctx).arena,
                    (*ctx).module as *Node,
                    callee_sym_pre,
                    ta_ptr, nta_val);
                if mangled_sym != (0 as *Sym) {
                    *((callee_id_pre as i64) as **Sym) = mangled_sym;  // rewrite IDENT.sym
                }
            }
        }
    }
}
```

全 offset access(per v3.2.0b mitigation)。

### 6.4 mono_expand_fn_call

```jhyy
fn mono_expand_fn_call(global, arena, module_node, def, type_args, ntype_args) -> *Sym
```

步骤:
1. dedupe:symtab_lookup(global, mangled_name) 命中 → return existing sym
2. 否则:symtab_insert(global, mangled_name_buf, SYM_FN(), type_ptr=0, ...) →
   返回 fresh sym `ms`
3. 克隆 def:mono_clone_func_decl(arena, def, type_params_of_def,
   type_args, ntype_args)
4. overwrite cloned.sym → ms(NodeFuncDecl.sym @ offset 0 in Node data area)
5. append cloned 到 module_node.decls (mono_decls_append)
6. return ms

注意:def 是 *Node(NodeFuncDecl 节点本身),def_tp = def + NODE_SIZE() + 80
读 type_params 字段(避开 Node header 32B)。

---

## 7. Codegen 路径 / Codegen Pipeline

### 7.1 cg_func skip gate

```jhyy
let fd_off2 = fd as i64;
let ntp_off2 = (fd_off2 + (88 as i64)) as *i64;  // NodeFuncDecl.ntype_params @ 88
if *ntp_off2 > (0 as i64) {
    return 1;  // skip generic fn body emit
}
```

mirror check_func_decl pattern。

### 7.2 Cloned fn emit

cloned `max$i32` (ntype_params=0) 走 normal cg_func 路径:
1. 读 cloned.fn_sym (mangled `max$i32`) → abi_win_emit_function_header
2. abi_win_emit_function_header 遍历 params,每个 param:
   - `param_slot = ptr_add_u8(params, i * 16) as *NodeFuncDeclParam`
   - `p_sym = param_slot.sym as *Sym` (per-clone fresh sym from mono_clone_func_decl)
   - `pt = p_sym.type_ptr` (set by check_func_decl Pass 3a)
   - `pqt = abi_win_classify_arg(pt)` → QBE type letter
   - emit `<pqt> %<name>`
3. cloned body 走 normal cg_expr emit(T→concrete 已替换 + IDENT sym 已 rewrite)

---

## 8. 错误 / Errors

| Error | 触发 | 修复 |
|-------|------|------|
| `parse error: expected '<' after turbofish '::'` | `f::(args)` 无 `<` | 加 `<T, ...>` 或用 qualified call `mod::fn(args)` |
| `parse error: expected '>' after turbofish args` | `f::<T(` 不闭合 | 闭合 `>` |
| `E0062: undefined variable` | `max(3, 5)` 无 turbofish (call-site inference 未实现) | v3.2.0c 用 turbofish;v3.2.0d 加 call-site inference |
| `QBE: invalid type for first operand ... in csgtw` | generic fn codegen 路径 bug | **已在 v3.2.0c 修**(per-clone fresh sym isolation + body IDENT sym rewrite) |

---

## 9. 验证 / Verification

### 9.1 ship gate (v3.2.0c)

- ✅ `make all` green
- ✅ `regress.py` → 112/112 passed, 0 failed, 15 skipped
- ✅ `generics_fn_turbofish_basic.jhyy` EXIT=42
- ✅ 5/5 v3.2.0b tests 不退化
- ✅ `jhyy_get_il` 断言 `max$i32` → `export function w $max$i32(w %a, w %b)` +
  `max$f64` → `export function d $max$f64(d %a, d %b)`
- ✅ D43 selfhost N11 byte-equal(SHA `b87c932038055321dc4caa134b914b99598cd9ea568b641eeb4fc4bd72592ddb`)

### 9.2 0 改动验证

`git diff v3.2.0b..v3.2.0c -- compiler/src0/abi_amd64_win.jhyy types.jhyy ir.jhyy
symtab.jhyy codegen_amd64_emit_call.jhyy` empty

### 9.3 不动 stage-0

所有 src0/*.jhyy 改动都是 v1.x-subset dialect(per v3.2.0b stage-0 chain 要求)。
mono_rewrite_idents_in_stmt/expr walker 全 offset access pattern(per v3.2.0b
L102-104 mitigation),不动 stage-0 codegen。

---

## 10. Cross-ref

- L1 设计:`docs/plans/roadmap/v3.x-language-expansion.md § Sprint 3i`
- L2 设计:`docs/plans/v3/v3.2.0c-plan.md`(本 sprint plan)
- 上游:[v3.2.0b generics supplement](jhyy-lang-spec-generics-supplement-v3.2.0b.md)
- 下游:[v3.2.1 plan](docs/plans/v3/v3.2.1-plan.md) (3j closures — 用 generic fn 闭包)
  + [v3.2.4 plan](docs/plans/v3/v3.2.4-plan.md) (3l.3 Vec<T>/Map<K,V> — 用 generic fn std lib)
- D28 锁链:`v3.2.0 → v3.2.0b → v3.2.0c → v3.2.1 → v3.2.4`
- D43 chain:`N10 (a81b8ca / f4a3ded) → N11 (b87c932038055321dc4caa134b914b99598cd9ea568b641eeb4fc4bd72592ddb)`
- M8d launch gate:`docs/plans/v2/v2.0.0-os-prep.md § 1`(compositor generic over T — v3.2.0b 解 struct/enum,v3.2.0c 解 fn)
- M11 launch gate:`docs/plans/v2/v2.0.0-os-prep.md § 1`(3l.3 std lib Vec<T>/Map<K,V> 用 generic fn — v3.2.4 ship 后联调)
- 反馈:
  - `feedback_v3b_no_phaseb_worktree`(axis-v3 direct commit)
  - `feedback_plans_per_version`(per-version plan, 不 umbrella)
  - `feedback_commit_coauthor`(`Co-Authored-By: MiniMax-M3 <noreply@MiniMax>`)
  - `feedback_no_traditional_chinese`(简体输出)
  - `feedback_changelog_umbrella`(v3.2 axis 1 个 umbrella changelog)
  - `feedback_mcp_regress_timeout`(regress 走 raw python, MCP jhyy_regress 600s 硬超时)
  - `feedback_make_clean_too_aggressive`(`MCP jhyy_selfhost_check` 用 jhyy_v1.exe.exe 作 v1 baseline)

---

## 11. Commit / Tag

- **Commits**:
  - `cdc7f5d feat(ast): NodeFuncDecl +16B type_params + NodeCall +16B type_args (3i fn path AST)`
  - `0dcbda8 feat(parser): parse_func generic arm + parse_call turbofish arm (3i fn syntax)`
  - `ad75e99 feat(mono): mono_clone_func_decl + mono_subst_block/stmt/expr + expand generic def lookup (3i fn monomorphize)`
  - `fa34293 feat(sema): check_func_decl skip + infer_type turbofish + mono_expand_fn_call (3i call-site inference)`
  - `dd14381 fix(mono): clone fresh per-fn param syms + body IDENT sym rewrite (3i fn path bug)`
- **Tag**:`v3.2.0c`
- **Post-tag SHA fill-in**:本文件 § 9.1 N11 SHA
- **Auto-push**:per `feedback_auto_push_after_commit`
