# JHYY 语言规范 — Generics Function Supplement (v3.2.0d)

> **Supplement** to [`jhyy-lang-spec-v1.3.0.md`](../abis/jhyy-lang-spec-v1.3.0.md) § 11
> (generics) + 附录 B 限制 + [`jhyy-lang-spec-generics-fn-supplement-v3.2.0c.md`](../abis/jhyy-lang-spec-generics-fn-supplement-v3.2.0c.md)
> (turbofish path, ship ✅ at v3.2.0c)。
>
> 本 supplement 锁定 v3.2.0d ship 的 **call-site type inference** 路径,与 v3.2.0c turbofish 路径互为补充。
> Tag: `v3.2.0d` (2026-09-08, commit `c7cf5b4` + C2)。

---

## 1. 背景

v3.2.0c ship 了 turbofish path:`max::<i32>(3, 5)` 显式 type args。但 Rust 风格
call-site inference `max(3, 5)` (编译器从 arg 推断 T=i32) v3.2.0c § Out of scope
推到 v3.2.0d。本次 ship 完整补完。

D28 链:`v3.2.0 → v3.2.0b → v3.2.0c → v3.2.0d → v3.2.1 → v3.2.4`。
v3.2.0d 是 3i generics fn path "runtime 完整" 的最后一块(M8d compositor generic
callback + M11 std lib `Vec<T>::push` ergonomic 写的硬前置)。

---

## 2. Call-Site Type Inference 规则

### 2.1 语法(与 turbofish 互斥)

```jhyy
fn max<T>(a: T, b: T) -> T {
    if a > b { return a; }
    return b;
}

fn main() -> i32 {
    // Turbofish path (v3.2.0c):
    let a: i32 = max::<i32>(3, 5);

    // Call-site inference path (v3.2.0d — 本 supplement):
    let b: i32 = max(3, 5);
    let c: f64 = max(3.0, 5.0);
}
```

两条 path 在 NODE_CALL 上互斥:
- `ntype_args > 0` ⇒ 走 turbofish path (v3.2.0c 已 ship)
- `ntype_args == 0` + generic fn 命中 ⇒ 走 call-site inference path (v3.2.0d 新)

### 2.2 算法(in sema.jhyy NODE_CALL turbofish `else` 分支)

入口条件:
1. `NODE_CALL.callee` 是 `NODE_IDENT`
2. `(*callee_sym).kind == SYM_FN`
3. `NODE_CALL.ntype_args == 0`
4. `mono_find_generic_def((*ctx).module, base_name) != 0` 命中 generic 声明

步骤:

1. **收集 fn decl 的 type_params**:`fn_decl.type_params` (offset 80) + `fn_decl.ntype_params` (offset 88)
   - 元素是 *Sym (per parser.jhyy L3150 — `*tpslot = _tpsym as *u8`)
2. **建立 param → type_param slot 映射**:walk `fn_decl.params` (offset 8) + `fn_decl.nparams` (offset 16)
   - 每个 param.type_annot 是 `NODE_IDENT` (单 T) 或 `NODE_UNARY` / `NODE_INDEX` 等
   - 对 NODE_IDENT:比对 sym.name 跟 type_params[i].name(strcmp 后 0-终止),记录 `param_slot[arg_idx] = i`
   - 对 NODE_UNARY (*T):递归处理 inner
3. **Walk call args**:`infer_type` 每个 arg 拿 *Type
4. **每个 *Type → *Node** via `mono_type_to_type_node`(见 § 3)
5. **写到 type_args[param_slot[arg_idx]]**
6. **T agreement 检查**:同一 type_param slot 被多次 set 时,`(*Type).kind` + 关键字段必须一致
   - 不一致 ⇒ E0062 "conflicting types for T: i32 vs f64"
7. **调 `mono_expand_fn_call`** → mangled sym (e.g. `max$i32`)
8. **Sym rewrite**:NODE_IDENT.sym = mangled_sym + NODE_CALL.type_args/ntype_args 防御性写
9. **Inline cloned fn type_ptr setup**(L2273 check_func_decl 定义晚于本处,jhyy 无 forward decl):
   - 设 mangled_sym.kind = SYM_FN + type_ptr = concrete func type
   - 每个 cloned param sym:type_ptr = param type + kind = SYM_VAR
10. **Inline cloned body IDENT type_ptr propagation**(helpers `mono_propagate_idents_in_expr` / `_to_cloned_body`):
    - cloned fn 是 Pass 3b 才 append 的,Pass 3a 已 finish,Pass 3b 跳过 mangled-$ → 不会 check_func_decl → body IDENT.type_ptr 不会自动 set,需要手动 propagate(否则 codegen 默认 `w` 而非 `d` 等导致 QBE type mismatch)

### 2.3 多 T 支持

```jhyy
fn pick<T, U>(a: T, b: U) -> T {
    return a;
}

fn main() -> i32 {
    let x: i32 = pick(3, 5.0);  // T=i32, U=f64
}
```

- param 0 (a:T) → type_params[0] (T)
- param 1 (b:U) → type_params[1] (U)
- arg 0 (3:i32) → type_args[0] = NODE_IDENT("i32")
- arg 1 (5.0:f64) → type_args[1] = NODE_IDENT("f64")
- mangled name: `pick$i32$f64`

### 2.4 Recursive Inference

```jhyy
fn main() -> i32 {
    let x: i32 = max(max(3, 5), 7);  // inner max(3,5) 先 → max$i32; outer max(max$i32, 7) → max$i32
}
```

`infer_type` 本来就是递归;inner call 完成时已 mono + sym rewrite,outer call 看到的
arg 是 concrete sym,不再触发 inference,直接走普通 path。

### 2.5 Dedupe

`mono_expand_fn_call` 通过 `symtab_lookup` 检查 mangled name 是否已存在:
- 存在 ⇒ 复用现有 cloned decl
- 不存在 ⇒ 调 `mono_clone_func_decl` 克隆 + 注册

混合调用同 generic:
```jhyy
let a: i32 = max(3, 5);          // call-site inference → max$i32 (clone #1)
let b: i32 = max::<i32>(7, 2);   // turbofish → max$i32 (dedup hit, 复用 clone #1)
let c: i32 = max(1, 9);          // call-site inference → max$i32 (dedup hit, 复用 clone #1)
```

emitted .il 中只有 **1 个** `function w $max$i32(w %a, w %b)`。

---

## 3. `mono_type_to_type_node` Helper

文件:`compiler/src0/mono.jhyy` (+71 行,紧跟 `mono_mangle_type_node_fn` 后)

| Input KIND | Output NODE | 备注 |
|------|------|------|
| KIND_I32 / KIND_F64 / KIND_U8 / KIND_BOOL / KIND_U16 / KIND_U32 / KIND_U64 / KIND_I16 | NODE_IDENT (prim sym) | sym 合成:arena_alloc(56) + `type_to_string(t)` 作 name + kind=SYM_TYPE |
| KIND_PTR | NODE_UNARY (inner=NODE_IDENT) | `inner.sym = t.type_ptr as *Sym` |
| KIND_STRUCT | NODE_IDENT (struct sym) | `sym = t.type_ptr as *Sym`(struct sym 直接 = type_ptr) |
| KIND_CAP | NODE_IDENT (cap sym) | 同 KIND_STRUCT |
| KIND_FUNC / KIND_ARRAY / KIND_SLICE / KIND_VOID / 其他 | 返 0 | caller 报 E0062 "cannot infer type parameter" |

---

## 4. 错误消息 (E0062)

| 场景 | 消息 |
|------|------|
| mono_type_to_type_node 返 0 | `cannot infer type parameter T from arguments (unsupported type kind)` |
| type_param slot 无 arg | `type parameter T has no argument to infer from` |
| 同 slot 多次 set 不一致 | `conflicting types for T: i32 vs f64` |
| ntype_args > 0 + call-site inference 不能并存 | (不触发,turbofish 优先) |

---

## 5. Codegen 协同 (零改动)

`codegen.jhyy` 看到 NODE_CALL 时:
- NODE_IDENT.sym 已是 mangled_sym (e.g. `max$i32`)
- NODE_CALL.type_args 已 defensive write(ntype_args = fn 的 ntype_params)
- codegen 调 `type_func` lookup → KIND_FUNC with concrete param types → emit `call $max$i32(...)`

cloned fn body 的 IDENT.type_ptr 由 `mono_propagate_idents_to_cloned_body` 在 mono
阶段设置,确保 codegen 看到正确 prim width (`w` vs `d`)。

---

## 6. 范围与非范围 (v3.2.0d MVP)

### 6.1 支持 (本 ship)

- ✅ 单 T (`fn max<T>(a: T, b: T) -> T`)
- ✅ 多 T 不同位置 (`fn pick<T, U>(a: T, b: U)`)
- ✅ T agreement 检查
- ✅ Dedupe via symtab_lookup
- ✅ Recursive inference(inner call 先 infer 完成)
- ✅ KIND_PRIMITIVE + KIND_POINTER + KIND_STRUCT + KIND_CAP 推断
- ✅ 错误消息 E0062 + sema_error_str 报点

### 6.2 不支持 (Out of scope,推到后续)

- ❌ return-position T 推断 (无 arg 是 T) → v3.2.0e
- ❌ 嵌套 generic fn (`fn outer<T>(inner: fn(T) -> T)`) → v3.x 中
- ❌ 高阶 trait bound (`T: Ord`) → v3.x 末
- ❌ `*Cap<T>` / `*mut T` 推断边界 → v3.x 中
- ❌ KIND_FUNC / KIND_ARRAY / KIND_SLICE → *Node → v3.x 中
- ❌ Generic closures → v3.2.1 (D28 链下一节点)

---

## 7. 验证 (Ship Gate)

- ✅ `make all` green(stage-0 编 src0/ 无 segfault)
- ✅ 2/2 新 test PASS EXIT=42
- ✅ 7/7 v3.2.0b/c tests 不退化
- ✅ Full regress:114/114 passed, 0 failed, 15 skipped
- ✅ `jhyy_get_il` 断言 2 distinct fn (inference test) + 1 dedup fn (mixed test)
- ✅ D43 selfhost N11 (`b87c9320...`) → N12 (`01209313cc61b974c9603d4a78acf9703d78193c4dd186448a4e9f78a8f2b362`) byte-equal

---

## 8. Cross-ref

- 上游 spec:[`jhyy-lang-spec-generics-fn-supplement-v3.2.0c.md`](../abis/jhyy-lang-spec-generics-fn-supplement-v3.2.0c.md) (turbofish path)
- 上游 spec:[`jhyy-lang-spec-generics-supplement-v3.2.0.md`](../abis/jhyy-lang-spec-generics-supplement-v3.2.0.md) (generic decl)
- 上游 plan:`docs/plans/v3/v3.2.0d-plan.md` (本 sprint plan)
- 上游 ship record:`docs/logs/v3/changelog-v3.2.md` v3.2.0d 段
- D28 链:`v3.2.0 → v3.2.0b → v3.2.0c → v3.2.0d → v3.2.1 → v3.2.4`
- D43 N12 baseline: `01209313cc61b974c9603d4a78acf9703d78193c4dd186448a4e9f78a8f2b362`
- C1 commit: `c7cf5b4`
- M8d / M11 launch gates: `docs/plans/v2/v2.0.0-os-prep.md § 1`