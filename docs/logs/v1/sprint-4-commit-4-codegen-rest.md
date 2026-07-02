# Sprint 4 commit 4 — codegen.jhyy: cg_func + cg_module + 3 v0 codegen bug workarounds

**日期**: 2026-07-02
**对应 plan**: [`../../plans/v1/v1.0.0详细实现方案.md`](../../plans/v1/v1.0.0详细实现方案.md) § 4.5（codegen 翻译策略）+ Stage 1 byte-equal
**状态**: ⚠️ **代码翻译完成 + 47/50 regress PASS（0 failed）；Stage 1 byte-equal BLOCKED，defer 到 v0.8**
**新增**: `compiler/src0/codegen.jhyy` +990 行（commit 3 是 ~1062 行，commit 4 是 ~2000 行）

## 目标

sprint 4 commit 3 已翻译 cg_expr stmt/binary/if/while 等核心 cases。
本 commit 增量翻译：

1. **cg_func 完整实现**（function header + sret + params + locals + body + return）
2. **cg_module 完整实现**（CGContext alloc + Pass B function dispatch；Pass A 占位）
3. **cg_find_local out_buf 重构**（workaround v0 codegen bug 8 — multi-field struct return）
4. **cg_convert_arg 重构**（消除 &&/|| 嵌套 → workaround bug 9）
5. **NODE_IF store/load 重构**（phi → load from result_slot → workaround bug 9 partial）
6. **`let extra = if ...` 重构**（mutable assignment 替代 → workaround bug 9）

## 实现要点

### 1. cg_func 完整实现

完整翻译 C 端 `cg_func`：header + sret 隐藏参数 + 形参列表 + locals 注册 + body 表达式 + return emit。

```jhyy
fn cg_func(cg_raw: *u8, n: *Node) -> i32 {
    // 跳过 extern
    // 解析 sym → ret_type → is_sret / ret_qt
    // emit "export function [qt] $mangled_name("
    // sret → 加隐藏 "l %ret" 第一个参数
    // 形参 loop → emit "[qt] %name"
    // emit " {" + "@start" label
    // 重置 cg, arena_alloc loop label arrays (3 * 32 * IRVAL_SIZE)
    // sret → alloc sret_slot = copy %ret
    // 每个形参 register as local
    // cg_expr(body)
    // cg_body_returns(body) → 检查是否以 return 结尾
    // 如果未 return → emit ret (sret / ret_qt / void 三分支)
    // emit "}\n\n"
}
```

### 2. cg_module 完整实现

```jhyy
fn cg_module(cg_raw: *u8, module_node: *Node) -> i32 {
    // alloc CGContext + locals arena block (MAX_LOCALS * LOCALENTRY_SIZE)
    // ir_init(ir, arena)
    // Pass B: 对每个 child FUNC_DECL 调 cg_func
    // (Pass A const data 占位：codegen.jhyy 当前不处理 const decl)
}
```

### 3. cg_find_local out_buf 重构（workaround bug 8）

**症状**：v0 codegen 处理 multi-field struct return（如 `IRVal` 5 字段 = 40 字节）时漏写 sret body，emit 出 `=l copy w` 或 loadw-on-loadw type mismatch。

**方案**：caller alloc IRVal 缓冲，pass `*u8` pointer 给 helper；helper 用 ptr arithmetic 写每个 IRVal 字段。

```jhyy
// Before:
fn cg_find_local(cg_raw: *u8, sym: *u8) -> IRVal { ... }  // BAD: returns struct

// After:
fn cg_find_local(cg_raw: *u8, sym: *u8, out_buf: *u8) -> i32 {
    // 写入 out_buf（IRVal fields: kind(0) id(4) ival(8) name(16) qbe_type(24)）
    let value_u8 = ptr_add_u8(entry_ptr as *u8, 8 as i64);
    let kind_p = value_u8 as *i32;
    let out_kind_p = out_buf as *i32;
    *out_kind_p = *kind_p;  // scalar deref, no struct field access
    // ... 同样的 pattern for id/ival/name/qbe_type
}

// Caller:
let loc_buf = IRVal { kind: 0, id: 0, ival: 0 as i64, name: 0 as *u8, qbe_type: 0 };
let _found = cg_find_local(cg_raw, sym, (loc_buf as *u8));
let loc = loc_buf;  // use loc.id, loc.qbe_type, etc.
```

中间方案 `let raw_val: IRVal = (*entry_ptr).value; let result = IRVal { kind: raw_val.kind, ... };` **失败**（同样 QBE 错误）— out_buf 模式是已知唯一 fix。

### 4. cg_convert_arg 重构（workaround bug 9）

**症状**：jhyy.exe 对 source-level `&&`/`||` 编译为 short-circuit（sc_false/sc_eval/sc_merge + phi）；嵌套时 phi predecessor 错配。

**方案**：把 `X && (Y || Z)` 链式条件拆为 nested `if/else`：

```jhyy
// Before:
if src_qt == QBE_D() && (dst_qt == QBE_W() || dst_qt == QBE_L()) { ... }
else if (src_qt == QBE_W() || src_qt == QBE_L()) && dst_qt == QBE_D() { ... }

// After:
if src_qt == QBE_D() {
    if dst_qt == QBE_W() { conv = "dtosi" as *u8; }
    else if dst_qt == QBE_L() { conv = "dtosl" as *u8; }
} else if dst_qt == QBE_D() {
    if src_qt == QBE_L() { conv = "sltof" as *u8; }
    else if src_qt == QBE_W() { conv = "swtof" as *u8; }
}
```

### 5. NODE_BINARY &&/|| 短路 → store/load

短路 &&/|| 也用 store/load 替代 phi：

```jhyy
// Before:
let result = ir_new_tmp(ir, QBE_W());
let eval_b = ir_new_block(ir, "sc_eval" as *u8);
let merge_b = ir_new_block(ir, "sc_merge" as *u8);
ir_emit_jnz(ir, left, eval_b, false_block);
ir_emit_label(ir, false_block);
let zero_v = ir_new_tmp(ir, QBE_W());
ir_emit_copy(ir, zero_v, 0);
ir_emit_jmp(ir, merge_b);
ir_emit_label(ir, eval_b);
let right_and = cg_expr(cg_raw, right_node);
let rb_and = ir_new_tmp(ir, QBE_W());
ir_emit_binary(ir, rb_and, "cnew" as *u8, right_and, ir_new_int(0));
ir_emit_jmp(ir, merge_b);
ir_emit_label(ir, merge_b);
ir_emit_phi2(ir, result, false_block, zero_v, eval_b, rb_and);

// After: alloc result_slot at outer scope; each branch store to slot, merge load
let result_slot = ir_new_tmp(ir, QBE_L());
ir_emit_alloc(ir, result_slot, 4 as i32);
// false branch: store zero_v to result_slot
// eval branch: store rb_and to result_slot
// merge: ir_emit_load(result, result_slot)
```

### 6. NODE_IF store/load 重构（partial workaround）

NODE_IF 也改 store/load 模式：alloc result_slot, then/else branch store, merge load。

## 已知 BLOCKED：Stage 1 byte-equal

`jhyy.exe compile codegen.jhyy` 仍 QBE 失败：

```
qbe:codegen_mcp_run.il:24942: predecessors not matched in phi %t8700
QBE failed
```

**根因**：jhyy.exe 对 source-level `if A { ... } else { ... }` 语句（无 return value）也 emit phi + ep_block trampoline。当 3+ 层嵌套时（典型场景：`if X { if (Y == A || Y == B) { if Z { ... } else { ... } } }`），phi predecessor 错配。

**已知 workaround 不完整**：上文的 store/load + &&/|| 重构只能消除部分嵌套场景。完全 workaround 需要把 cg_expr 全部重构为 1-level if/function — 不在 commit 4 scope 内。

**决策**：Stage 1 byte-equal 目标 defer 到 v0.8 sprint（先修 v0 codegen bug 9，再回来做 commit 4.1）。

## 已知 v0 codegen bug 增量

commit 4 期间发现 3 个新 v0 codegen bug（已记入 `feedback_v0_codegen_bug_workarounds.md`）：

- **bug 8**: multi-field struct return 漏写 sret body
  - Workaround: out_buf pattern（caller alloc 缓冲，helper 写）
- **bug 9**: source-level `&&`/`||` 嵌套 → phi predecessor mismatch
  - Workaround partial: 避免 &&/|| 嵌套；用 store/load 替代 phi
  - LIMITATION: jhyy.exe 对 source-level if/else 也 emit phi，3+ 层嵌套无法完全规避
- **bug 10**: nested struct field 32-bit LEA → loadw-on-loadw type mismatch
  - Workaround: ptr_add_u8 + cast + scalar deref（不用 `outer.inner.field`）

## regress.py 状态

```
47/50 passed, 0 failed, 3 skipped
```

未变。3 skipped：lib 测试（依赖未来 lib.jhyy）。

## 后续工作

1. **v0.8 sprint**: 修 v0 codegen bug 5-10（特别是 bug 9 — source-level if/else phi 嵌套）
2. **sprint 4 commit 4.1**: v0 修完后，重做 Stage 1 byte-equal
3. **sprint 4 commit 5**: codegen.jhyy 自我调用验证（jhyy 编出 codegen.jhyy 后再编 codegen.jhyy，结果 byte-equal）