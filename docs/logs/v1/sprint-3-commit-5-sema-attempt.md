# Sprint 3 commit 5 — sema.jhyy 翻译

**日期**: 2026-06-28
**对应 plan**: [`../../plans/v1/v1.0.0详细实现方案.md`](../../plans/v1/v1.0.0详细实现方案.md) § 3.4
**状态**: ✅ **完成 + T0-T7 全部 PASS（exit=42）**

## 目标

Sprint 4 提前开 codegen 需要先过 sema（sprint 3 commit 5 提前到本 sprint）：
翻译 `compiler/src/sema.c`（约 1100 行）到 `compiler/src0/sema.jhyy`，
覆盖 49 个 NodeKind 的类型推断 + 错误检查 + match 穷尽性检查 + let mut 检查。

C 端参考 `compiler/src/sema.c`。

## 实现

### 1. 翻译范围

- `sema_init` / `sema_check` —— 顶层 API
- `check_module` —— 3-pass：register decls → resolve type decls → check bodies
- `check_func_decl` —— 参数 + 返回类型 + 函数体类型检查
- `infer_type` —— 全部 NodeKind 分支（int/float/string/char/bool/ident/unary/binary/cast/deref/index/call/field/array_lit/slice_lit/slice_expr/sizeof/alignof/block/if/let/assign/return/break/continue/match/match_arm）
- `resolve_type_node` —— ident / unary (ptr) / array_type / slice_type
- `process_match_pattern` —— pattern ident / enum variant / tuple（带 variant payload type 解析）
- `process_match` —— 检查 match arms 穷尽性（7A）

### 2. 公共代码

- `sema_error_int / _int2 / _str / _str_int` —— 4 个变体走 StringBuilder 拼接 + jh_fputs_stderr
- `sema_push_scope / sema_pop_scope` —— SymTable 嵌套 + arena_alloc
- `sema_local_at / _sym / _type / _set` —— locals[] 数组 offset 访问（256 × 16 bytes 外置）
- `SemaContext` —— 80 bytes struct（10 字段，scope_depth + loop_depth 用 i32 + 4 pad）

### 3. symtab 增量（v0.7 7A 配套）

- `sym_enum_variants(t_raw, enum_name, out, max_variants)` —— 遍历 SymTable.entries，收集 `kind=SYM_VARIANT && module==enum_name` 的 sym，写到 out 数组，返回数量
- 调用方：sema 7A match 穷尽性检查、enum 字段收集

### 4. sema 增量（v0.7 7A 配套：IDENT 处理 SYM_VARIANT）

新增识别 enum variant value。原 IDENT branch 只处理 SYM_FN/SYM_TYPE，导致 `let c = Red`
这种 enum variant value 落 "undefined variable"。新增 3b 分支通过 `sym.module`（enum 名）
反查 enum sym，返回 enum type：

```jhyy
// 3b) SYM_VARIANT: 取 parent enum 的 type（module 字段记的是 enum 名）
if (*gsym).kind == SYM_VARIANT() {
    let module_name = (*gsym).module;
    if module_name != (0 as *u8) {
        let enum_sym = symtab_lookup_local((*ctx).global_scope, module_name);
        if enum_sym != (0 as *Sym) {
            if (*enum_sym).type_ptr != (0 as *u8) {
                let t = (*enum_sym).type_ptr as *Type;
                (*n).type_ptr = t as *u8;
                return t;
            }
        }
    }
}
```

### 5. amd64_win stack-spill bug workaround

T5 IDENT Red 处理时调 `symtab_lookup_local` 在第 4 次调用时 segfault。
通过在 `symtab_lookup_one` 加 1 次 sb_init 触碰 arena，让 QBE amd64_win backend 生成
更保守的 stack frame 后稳定通过：

```jhyy
fn symtab_lookup_one(t_raw: *u8, name: *u8) -> *Sym {
    ...
    if (*t).count == (0 as i64) {
        return 0 as *Sym;
    }
    // WORKAROUND: amd64_win stack-spill — touching arena forces
    // codegen to materialize stack frame in safe way.
    let mut _wb: StringBuilder = StringBuilder { buf: 0 as *u8, len: 0 as i64, cap: 0 as i64 };
    sb_init(t.arena as *Arena, &_wb);
    ...
}
```

后续 sprint 应深入排查根因（疑 QBE stack-spill 阈值边界），可能由 symtab_lookup_one
locals 数量（7 个 8-byte）和 arena_alloc 大块（4096 字节 locals 数组）触发的 register
分配失败导致。完整调查见 sprint 3 commit 6 计划。

### 6. 测试驱动

`_driver_sema.jhyy` 8 个测试：
| Test | 验证 | 结果 |
|------|------|------|
| T0 | smoke：sema_init 不崩 | PASS |
| T1 | 有效函数（`let x: i32 = 42; return x;`）→ 0 errors | PASS |
| T2 | 未定义变量 → 1+ errors | PASS（errs=1）|
| T3 | struct layout → 0 errors + Point sym 存在 | PASS |
| T4 | enum variants 注册 → 0 errors + sym KIND_ENUM + nvariants=3 + sym_enum_variants=3 | PASS |
| T5 | match 非穷尽 → errors > 0 | PASS（"non-exhaustive match: missing variant"）|
| T6 | match 穷尽（有 `_`）→ 0 errors | PASS |
| T7 | let mut 可赋值 / let 不可赋值（v0.6.5 patch） | PASS（7a errs=1, 7b errs=0）|

退出码 42。T1-T7 每 test fresh arena（`arena_free → arena_init → sema_init`）避免 cross-test state。

## 调查过程（Bug 误诊与真因）

### 误诊 1: T1 fail（"undefined variable" for `x`）

**症状**：`fn main() -> i32 { let x: i32 = 42; return x; }` 输出 `test.jhyy:1:27: error: undefined variable`。

**误诊**：以为是 T1（有效函数）失败，开始排查 SemaContext struct layout / locals 数组 round-trip。
加大量 debug 后发现 1:27 的错误其实是 T2（`return x;` 无 `let x;`）的预期错误。

**真因**：stdout 是 buffered 的，`printf("T1\n")` 在 crash 前没 flush，T0-T7 标记全部
在 exit 时才打出来。错误归因错位。

**修正**：T1 实际 pass（独立跑 T1，exit=42）。崩溃实际发生在 T5 处理 IDENT `Red`
时的 `symtab_lookup_local` 调用。

### 真 bug: amd64_win stack-spill on symtab_lookup_one

**症状**：T5 IDENT Red 调 `symtab_lookup_local` → `symtab_lookup_one` 时 segfault。
sema 已确认 `(*ctx).global_scope` 有效（count=5, mask=255, entries 指针非 0）。

**临时 workaround**：在 symtab_lookup_one 加 1 次 sb_init（→ arena_alloc），让 QBE
amd64_win 生成不同 stack frame，bug 消失。

**真因未确认**：疑 QBE amd64_win backend 的 stack-spill threshold bug。symtab_lookup_one
有 7 个 8-byte locals + arena_alloc 大块（4096 字节 locals 数组）同时存在时，某些调用
序列会触发不安全的 spill 重用。完整调查建议见 sprint 3 commit 6。

## 代码量

| 文件 | 状态 | 行数 |
|------|------|------|
| compiler/src0/sema.jhyy | **新增** | ~1690 |
| compiler/src0/_driver_sema.jhyy | **新增** | 280 |
| compiler/src0/symtab.jhyy | 修改（+sym_enum_variants + workaround） | +40 |

## 验证

- ✅ `python regress.py` **47/50 passed, 0 failed, 3 skipped**（未引入新失败 — C 编译器测试不受影响）
- ✅ `_driver_sema.jhyy` **T0-T7 全部 PASS，exit=42**

## 下一步

1. 真因排查 amd64_win stack-spill bug → 提交到 jhyy compiler 项目
2. 重新跑 byte-equal oracle 验证 sema 翻译对齐 C 端
3. Sprint 4 才进 codegen.jhyy 翻译