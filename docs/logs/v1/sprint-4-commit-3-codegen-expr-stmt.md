# Sprint 4 commit 3 — codegen.jhyy: cg_expr BLOCK/LET/ASSIGN/RETURN/BREAK/CONTINUE/EXPR_STMT/BINARY + cg_stmt 薄包装

**日期**: 2026-06-30
**对应 plan**: [`../../plans/v1/v1.0.0详细实现方案.md`](../../plans/v1/v1.0.0详细实现方案.md) § 4.5（codegen 翻译策略）
**状态**: ✅ **代码合并 + 47/50 regress PASS（0 failed），剩余 3 SKIP（lib）**
**新增**: `compiler/src0/codegen.jhyy` +407 行（commit 2 是 462 行，commit 3 是 1062 行）

## 目标

sprint 4 commit 2 已翻译 cg_expr literal cases（INT/BOOL/FLOAT/STRING/CHAR/IDENT/UNARY）。
本 commit 增量翻译：

1. **cg_stmt → 合并入 cg_expr**（jhyy 无 forward decl → 必须单一定义）
2. **cg_expr BLOCK/LET/ASSIGN/RETURN/BREAK/CONTINUE/EXPR_STMT**（stmt-position cases）
3. **cg_expr NODE_BINARY 完整**（含 short-circuit &&/|| + eager eval + qbe_type dispatch + signed/unsigned）

## 实现要点

### 1. cg_stmt 合并入 cg_expr

jhyy 无 forward declaration，即便独立函数 `cg_stmt ↔ cg_expr` 互引用都会触发"undefined variable 'cg_stmt'"。
**解决**：把 `cg_stmt` 的 body 合并入 `cg_expr`（单函数），`cg_stmt` 留作薄包装。

```jhyy
fn cg_stmt(cg_raw: *u8, n: *Node) -> i32 {
    if n == (0 as *Node) {
        return 0;
    }
    let _ = cg_expr(cg_raw, n);  // IRVal 自动丢弃
    return 1;
}
```

cg_expr 内部用 if-else if chain 按 `(*n).kind` 分派，所以同一份代码同时处理 expr-position 和 stmt-position。
对 Node 类型查找 `node_X_data(n)` 时 cast `(*d).left as *Node` 解引用 `*u8` 字段（v0 codegen bug 1 workaround，sprint 1 引入）。

### 2. v0 codegen bug 6（NEW）发现 + workaround

**Bug**：两个 `if kind == NODE_RETURN() { ... return zero; }` 在 cg_expr 同层并存时，
jhyy.exe parse+sema 0 errors / QBE 阶段未触发，但 `jhyy.exe compile codegen.jhyy`
**100% 复现 segfault（exit=139, 0xC0000005）**。

**触发场景**：commit 2 末尾加 stmt-position NODE_RETURN case（line 864-881），含 `(*cg).has_sret`、`cg_copy_struct`、`(*cg).sret_slot` 访问 → 编译崩溃。

**Workaround**：删 duplicate stmt-RETURN case（line 864-881），单 NODE_RETURN case 处理 expr-position；
stmt-position 自动走同一分支（cg_stmt → cg_expr 合并）。sret 字段处理延迟到 commit 4（cg_func 配合）。

memory `feedback_v0_codegen_bug_workarounds.md` 已加 bug 6 条目。

### 3. NODE_BINARY 完整翻译（含 short-circuit + signed/unsigned 分派）

C 端 `cg_expr` 用 `switch (n->kind)` + 算符 nested switch — jhyy 端改 `if kind == X()` chain +
算符用 `let mut op: *u8 = "add"; if d_op == TOKEN_PLUS() { op = "add"; } else if ...`（jhyy 无 `?:`，三元改写为 if/else）。

short-circuit `&&` / `||` 翻译同 C 端：生成 `false_block` / `true_block` / `eval_b` / `merge_b` 四块 + phi2。

cmp 算符按 `op_qt` + `is_unsigned` 分派至 QBE cmp 指令集（csltl / cslew / cultl / culew 等）。

### 4. jhyy 限制下的 workaround 集

- **指针算术**：`ptr_add_u8(p, off) = (p as i64 + off) as *u8`（jhyy 无 `*u8 + i64`）
- **struct 字段访问**：`let x = *((*base) as *Type).field` 或通过 ptr_add_u8 字段 offset 计算
- **i32/i64 字面量**：`5 as i64` 显式 cast（jhyy 默认数字字面量 i32）
- **IRVal struct literal**：`let v = IRVal { kind: 0, id: 0, ival: 0 as i64, name: 0 as *u8, qbe_type: 0 };`
- **fn 返回值丢弃**：`let _ = cg_emit_store(...);`（避免 `if/else` 分支类型不匹配）

## 改动统计

```
 compiler/src0/codegen.jhyy | 412 ++++++++++++++++++++++++++++++++++++-
 1 file changed, 407 insertions(+), 5 deletions(-)
```

## 验证

```
$ python compiler/build/bin/regress.py
...
===== 47/50 passed, 0 failed, 3 skipped =====
```

- 47 cases PASS（含 ir.jhyy 单元测试 + arena + 所有现有 expr 级 sample program）
- 3 SKIP（lib 文件，无 main）
- 0 FAILED（jhyy.exe compile 不再 segfault，QBE 错误回到 commit 2 已知的 v0 bug，不影响自举 stage 1 byte-equal oracle）

## 不在本 commit（commit 4 处理）

按 plan § 4.5：

- cg_expr `CAST / ADDR_OF / DEREF / STRUCT_LIT / ENUM_VARIANT / MATCH / INDEX / ARRAY_LIT / SLICE_LIT / SLICE_RANGE / FIELD`
- cg_stmt `FOR / WHILE`（loop_depth + loop_ends / loop_continues 完整支持）
- cg_func（function header + locals + body wrap）
- cg_module（Pass A const data + Pass B function emit）
- `_driver_codegen.jhyy`（sprint 4 单元测试）
- Stage 1 .il byte-equal 验证（核心目标）

## 关键风险（commit 4 需解决）

1. **Stage 1 byte-equal**：cg_expr 实现与 C 端 emit 顺序 / tmp 单调编号必须 byte-equal。
   任何 jhyy 端引入的额外 tmp 都会改变编号 → diff 不为零 → 自举判定失败。
   缓解：strict emit 顺序（sprint 4 plan § 4.5）+ 用 `_driver_codegen.jhyy` 跑 small fixtures 验证。

2. **sret 字段未处理**：cg.sret_slot / has_sret / current_ret_type 字段类型已声明但 commit 4 才会用到。
   struct return 必须配 cg_func 的 call setup（abi § 4），单独 case 不够。

3. **QBE 类型默认值**：commit 2 留下已知 v0 bug 1（qbe_type_of(struct) 默认 w），
   commit 4 加 CAST / STRUCT_LIT 时可能再触发。memory 已记 workarounds，直接套。
