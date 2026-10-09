# Changelog v4.0.2.4 — W-098 i64 literal emit 真修 (3-tier: emit + IR + cast)

**Date:** 2026-10-09 · **Author:** MiniMax-M3 · **Status:** wip (single-commit ship pending)

## Summary

W-098 i64 literal emit bug 真修 ship (1 commit, 3-tier fix) — `i64 literal > 32-bit signed range` 静默丢高 32 位的根因族全清。W-075 mem_set b32|shift|OR workaround 现在变成 "可选 revert" (W-098 修后 b8 构造直接 emit `movabsq $0x0101010101010101, %rax` 正确)。

**W-098 真修前**:
- 用户写 `0x100000001 as i64` → jhyy-side codegen emit `movl $4294967297, -off(%rbp); movl -off, %eax; cltq; movq %rax, -off` 模式,高 32 位丢 (存的是 1,不是 0x100000001)
- mem_set b8 构造必须 workaround (b32 + shift + OR)
- silent fail, runtime 难发现

**W-098 真修后**:
- 3-tier 真修: emit-side (movabsq + movq) + IR-side (NODE_INT W→L promote) + cast-side (cg_convert_arg 尊重 IR-level promotion)
- `_audit_w098_*.jhyy` 5 个 discriminating repro 全 PASS (imm_mov + imm_shr + binop + no_cast + b8)
- `std_mem_set_aligned.jhyy` 仍 PASS (workaround back-compat 无需 revert)
- regress 160/161 PASS (1 pre-existing fail `std_math_basic` per baseline)

## 3-tier 真修 detail

### Tier 1 — emit-side (`compiler/src0/codegen_amd64_emit_call.jhyy:emit_mov_imm_to_offset`)

QBE_L + imm > 32-bit signed range 走 `movabsq $imm, %rax; movq %rax, mem`,小 imm 仍走 direct `movq $imm, mem` (无 perf regression)。

```jhyy
let needs_wide: i32 = if qt == QBE_L_LOCAL() {
    if imm > 2147483647 || imm < -2147483648 { 1 } else { 0 }
} else { 0 };
if needs_wide != 0 {
    sb_append "\tmovabsq $"; ...  // movabsq + movq 模式
} else {
    // 原 mov<size> 路径
}
```

### Tier 2 — IR-side (`compiler/src0/codegen.jhyy:cg_expr NODE_INT`)

`let x = 0x100000001;` (default int type = W) 时,若 value > 32-bit signed,自动 promote 到 L type,存 L 槽 (避免 W 槽 emit 截断)。后续 cast 走 no-op (same type)。

```jhyy
let mut qt: i32 = qbe_type_of((*n).type_ptr);
if qt == QBE_W() && ((*d).value > 2147483647 || (*d).value < -2147483648) {
    qt = QBE_L();  // value-driven promote
}
```

### Tier 3 — cast-side (`compiler/src0/codegen.jhyy:cg_convert_arg`)

`(0x100000001 as i64)` cast 路径:即使 IR 已 promote 到 L,AST 层 src_t 仍是 i32 type → 走 extsw → re-truncate promote 后的值。Fix:取 IR-层 arg.qbe_type 作 src_qt(若比 AST 层宽)。

```jhyy
let mut src_qt: i32 = if src_t == 0 { arg.qbe_type } else { qbe_type_of(src_t) };
if arg.qbe_type == QBE_L() && src_qt == QBE_W() {
    src_qt = QBE_L();  // 尊重 IR-level promotion
}
```

## Binop src2_is_imm path 分析

Per W-097 deep audit (`docs/audit/w-097-emit-audit-checklist.md`),12 binop sites 在 emit_binop (lines 1808-1812 sub, 1824-1828 mul, 1847-1850 div, 1870-1873 mod, 1896-1899 rem, 1912-1916 and, 1928-1932 or, 1944-1948 xor, 1971-1979 shl/shr, 2066-2070 cmp, 2137-2141 add fallback) 都用 `$imm, %reg` form。

**W-098 真修后分析**: 实际 all literals 走 TEMP first via cg_expr NODE_INT (Tier 2 promote),binop emit 永远见 src2=TEMP (src2_is_imm=0) → binop 路径不触发 W-098。**Audit checklist 中 12 binop sites 标记 dormant for W-098** (no code change needed)。

## Verification (5/5 PASS per `feedback_fix_evaluation_rule`)

| Test | Tier | Result |
|------|------|--------|
| `_audit_w098_imm_mov.jhyy` (emit-mov) | Tier 1 | EXIT=0 |
| `_audit_w098_imm_shr.jhyy` (IR-side + cast-side, subq path) | Tier 2+3 | EXIT=0 |
| `_audit_w098_no_cast.jhyy` (no explicit cast) | Tier 2 | EXIT=0 |
| `_audit_w098_binop.jhyy` (binop sub path) | dormant | EXIT=0 |
| `_audit_w098_b8.jhyy` (mem_set use case, `0x0101010101010101`) | Tier 1+2 | EXIT=0 |
| `std_mem_set_aligned.jhyy` (back-compat workaround) | — | EXIT=0 |

regress 160/161 PASS (1 pre-existing `std_math_basic` per baseline, per `feedback_regress_clean_count` FRESH count).

## What changed

### 1. `compiler/src0/codegen_amd64_emit_call.jhyy:386-419` — emit-side (Tier 1)

`emit_mov_imm_to_offset` 加 QBE_L_LOCAL + imm > 32-bit signed range 分支,emit `movabsq $imm, %rax; movq %rax, mem`。小 imm 走原 direct path 无 perf regression。

### 2. `compiler/src0/codegen.jhyy:1367-1386` — IR-side (Tier 2)

`cg_expr NODE_INT` 加 value-driven W→L promote:`if qt == QBE_W() && value > 32-bit signed range, qt = QBE_L()`。

### 3. `compiler/src0/codegen.jhyy:879-887` — cast-side (Tier 3)

`cg_convert_arg` 加 IR-level promotion respect:`if arg.qbe_type == QBE_L() && src_qt == QBE_W(), src_qt = QBE_L()`。

### 4. `compiler/tests/examples/_audit_w098_*.jhyy` (5 NEW) — discriminating repros

- `_audit_w098_imm_mov.jhyy` — Tier 1 (emit-mov 路径)
- `_audit_w098_imm_shr.jhyy` — Tier 2+3 (subq + shr 64-bit 正确)
- `_audit_w098_no_cast.jhyy` — Tier 2 (no explicit cast, value-driven promote)
- `_audit_w098_binop.jhyy` — binop sub path 验证
- `_audit_w098_b8.jhyy` — mem_set use case (`0x0101010101010101`)

### 5. `docs/internal/workarounds.md` — W-098 ACTIVE → ✅ RESOLVED

flip 状态 + 补 "真修" 段 (3-tier detail) + 更新 "影响范围" (post-fix silent fail 消除) + 更新 "引用" (加 source file:line refs)。

## Workaround back-compat

W-075 mem_set b32|shift|OR workaround 仍 valid (back-compat 测试 PASS)。Revert 可选,但建议保留 1-2 sprint 观察期,跟 v1.4.6 修 W-017/W-019/W-020 保留 `jhyy_helpers.c` DEPRECATED 状态 1-2 sprint 观察期同 pattern。

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Tier 2 NODE_INT promote W→L 改变 AST type → 影响后续 cast dispatch | minor — 同一 type cast 是 no-op | 验证 5 audit tests + regress 160/161 PASS |
| Tier 3 cg_convert_arg 取 arg.qbe_type vs src_t 优先级 | minor — arg.qbe_type 是 IR-actual, src_t 是 AST-declared | IR-actual 更接近 codegen 实际, 优先级对 |
| `mem.jhyy:mem_set` b32|shift|OR workaround revert 风险 | low — workaround 仍 PASS, 无需立即 revert | 观察 1-2 sprint |

## Related

- [[W-075]]: mem_set i64-store 真修 (shipped v4.0.2.3, workaround ship 走 b32|shift|OR 避 W-098)
- [[W-096]]: emit-side per-fn-local counter 真修 (v4.0.2.2) — prerequisite 暴露 W-098 真正面
- [[W-097]]: deep audit 启动,sprint 内 emit_func_header 真修 (推 v4.0.2.5,本次未 ship)
- `feedback_rca_first_root_cause` (2026-10-09 1-iter RCA 找真根因,不是 multifn frame)
- `feedback_fix_evaluation_rule` (5/5 PASS on each tier mandatory)
- `feedback_audit_single_commit_diff` (本次 1 commit,3-tier + audit tests + workarounds flip)
- `feedback_regress_clean_count` (160/161 fresh count,1 pre-existing fail per baseline)
