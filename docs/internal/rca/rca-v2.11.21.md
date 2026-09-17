# v2.11.21 — RCA: 4 self-backend fail root causes + silent-fail audit (5 sub-agent parallel investigation)

**Status**: 🔬 RCA-only sprint (docs-only, no source changes), 2026-09-17

**Why**: per `feedback_rca_first_root_cause`, RCA before fix — 4 fail at v2.11.20 ship had wrong/over-estimated root causes in initial W-074.13 entry. v2.11.21 fix sprint scope needs accurate LOC + concrete fix sketches before code.

**Method**: 5 sub-agents in parallel (4 RCA + 1 silent-fail audit), each given specific hypothesis to verify/refute with .s evidence.

---

## 1. big_array — slot alloc overlap (W-074.13 sub-bug 1)

### v2.11.20 RCA claim
2-pass slot allocation 重设计 (~80-120 LOC), cg_alloc_slot + cg_offset_for_temp_with_target 物理 overlap。

### v2.11.21 RCA finding
**CONFIRMED root cause**, but fix is **simpler than 2-pass**. **Hypothesis true at symptom level**; fix sketch different.

### Real root cause (file:line)
`compiler/src0/codegen_amd64_emit_mem.jhyy:284-297` (`emit_alloc`):
- `cg_alloc_slot(state, 400)` advances `next_offset` to -400 (region at -400..-1)
- `cg_offset_for_temp_with_target(1, win)` returns `-(32+1*8) = -40` (formula fallback, hardcoded)
- No coordination between region placement and pointer-slot placement
- Result: t1 pointer-slot at -40 collides with arr[90] at -400+4*90 = -40

### Evidence from .s (`/tmp/_rca_big_array.s`)
- Line 14: `subq $1816, %rsp` (1816 = region 400 + shadow 32 + many temp slots + frame padding)
- Line 16-17: `leaq -400(%rbp), %rax; movq %rax, -40(%rbp)  # → %t1`
- For copy 91: `addq $360, %rax; movl $91, (%r8)` → writes arr[90] at -40(%rbp), **overwriting t1's low 4 bytes**
- Subsequent binop reads t1 from -40(%rbp) → garbage → bogus address → SEGV

### Real fix sketch (~10-30 LOC, NOT 2-pass)
In `emit_alloc` after `cg_alloc_slot` returns `slot`, set pointer-slot **directly below region**:
```jhyy
let slot = cg_alloc_slot(state, aligned);
let pointer_slot_off = slot - 8;  // 8-byte pointer slot just below region
let _rec = cg_record_temp_slot(state, dst, pointer_slot_off);
(*s).next_offset = (*s).next_offset - 8;
(*s).total_alloc = (*s).total_alloc + 8;
let off = slot;
```
`mem_temp_offset` already queries `temp_slot_for_id[dst]` first (state.jhyy:644-650) and returns the recorded `pointer_slot_off` instead of falling back to formula.

The `cg_record_temp_slot` infrastructure **already exists** (state.jhyy:251-262) — v2.11.8 derived-address tracking fix made emit_alloc **skip** calling it (because region = pointer-slot was unsafe with indirect stores). The fix re-enables it with a **different value** (below region, not equal to region).

### Cross-test relevance
Only big_array impacted. cap_table_basic (16B struct), dungeon_game (link fail), for_in_slice_nested (load propagation bug, see § 4) are unrelated.

---

## 2. cap_table_basic — emit_copy FNARG misclassification (W-074.13 sub-bug 2)

### v2.11.20 RCA claim
fnarg ID (-3/-4/-5/-6) 在 cg_is_address_holder 查询 gap (~10-20 LOC)。

### v2.11.21 RCA finding
**Hypothesis REFUTED**. cg_is_address_holder works correctly; real bug is in `emit_copy` FNARG **detection** heuristic.

### Real root cause (file:line)
`compiler/src0/codegen_amd64_emit_call.jhyy:1057-1071` (emit_copy TEMP-vs-FNARG heuristic):
- `pct_count` counting loop increments for ANY `%t` prefix (regardless of digits)
- For IL `%t3 =l copy %t`, pct_count = 2 → misclassified as TEMP copy
- TEMP branch calls `cg_parse_temp(..., idx=1)` which requires DIGITS after `t` (state.jhyy:825 `if ndig > 0`)
- For `%t` (no digits), returns -1 → falls back to `src_temp_id = 0` (t0's garbage)
- FNARG detection branch (lines 1089-1123) never entered because `pct_count >= 2`

The flag propagation IS correct when called; the issue is `emit_copy` never reaches the FNARG path that calls `cg_record_temp_holds_address` (line 1238).

### Evidence from .s (`/tmp/_rca_cap_table.s` cross_fn_sum_table)
```asm
cross_fn_sum_table:
  movq -32(%rbp), %rax      # EMIT_COPY: src_off = -32 = t0 slot (WRONG)
  movq %rax, -56(%rbp)      # → t3 slot. Should be "movq %rcx, -56(%rbp)" (FNARG path)
  movq -56(%rbp), %rax      # EMIT_LOAD %t3 — direct slot read (no indirect dispatch)
  movq %rax, -64(%rbp)      # → t4 = t3's value (pointer), NOT *t3
```
Expected: `movq %rcx, -56(%rbp); movq -56(%rbp), %r8; movq (%r8), %rax; movq %rax, -64(%rbp)`.

### Real fix sketch (~5-10 LOC)
Change heuristic to count only `%tN` with DIGITS, not bare `%t`. Two options:
1. Replace `pct_count` loop with `cg_count_valid_temps(text, len)` helper that uses same `ndig > 0` check as cg_parse_temp.
2. In TEMP branch (line 1067-1071), validate `src_temp_id` returned by cg_parse_temp — if -1, fall through to FNARG detection instead of defaulting to 0.

Recommended option 2 (smaller, defensive — preserves existing TEMP path semantics).

### Cross-test relevance
Only triggers when fn arg name starts with `t` (e.g. `%t`, `%table`, `%target`, `%temp`). Rare edge case; only cap_table_basic in regress uses `%t` as fn arg.

---

## 3. dungeon_game — missing label definitions (W-074.13 sub-bug 3)

### v2.11.20 RCA claim
multi-file import + gcc link path missing piece (~30-50 LOC), W-074.6 PARTIAL 主项子集。

### v2.11.21 RCA finding
**Hypothesis REFUTED on major claim**: dungeon_game is **single-file** (grep `import` = 0 lines). Not a multi-file bug.

### Real root cause
Self-backend emits `jmp .Lelse50_b0_fn6` and `jmp .Lelse53_b0_fn6` but **never emits the corresponding `.Lelse50:` / `.Lelse53:` label definitions**:
```
$ nm -u _rca_dg_self.o
                 U .Lelse50_b0_fn6
                 U .Lelse53_b0_fn6
                 U printf / puts / scanf   (these 3 are C runtime — OK)
```
QBE baseline has only 3 C runtime undefineds. Self adds 2 missing labels → `ld returned 5 exit status`.

### Control flow pattern triggering it
`then`-branch is `ret`-only, so `@else50`/`@else53` are unreachable in practice, but IL still tokenizes them as labels. Pattern:
```
@then49 → ret → @else50 → jmp @merge51 → @merge51 → jmp @merge45 → @else44 → jmp @merge45 → @merge45
```
`.s` has `.Lthen49 → Lmerge51 → .Lelse44 → Lmerge45` — **`.Lelse50` and `.Lelse53` are completely missing**.

### Suspect causes
Either `next_token_label` is being skipped past these labels, or `emit_label` silently fails. Most likely given W-074.6/W-074.7 bug history: arena-allocated `(*t).text` reuse bug where two consecutive label tokens share the same `text` pointer, and `emit_label` for the first one happens correctly while the second one's `text` pointer got reallocated for a different token before emit. Could also be `cg_record_block_name` table-full failure silently falling back to `b_count = 0` for a different name slot.

### Fix sketch (LOC: 10-30 trivial / 30-80 if lexer arena reuse)
Add assertion in `emit_label` after writing the def: emit `# EMIT_LABEL <name>\n` comment marker and verify post-emit that the label name appears in `sb`. More directly, investigate `lex_skip_ws_and_comments` between `next_token_ret` and the next `next_token_label` call for a bug that consumes past the `\n` into the `@else50` line.

Bisection: insert `jh_fputs_stderr("token kind=%d\n", tok.kind)` debug in `parse_and_emit` to confirm whether `ILTOK_LABEL` for `@else50`/`@else53` ever reach the dispatch.

### Cross-test relevance
**None**. This specific control flow pattern (ret-only-then + forward-jmp + immediate-merge) is unique to dungeon_game's `$battle` `if state == 0` block in entire regress.

---

## 4. for_in_slice_nested — v2.11.20 RC-1 fix over-aggressive (W-074.13 sub-bug 4) ⚠️ REGRESSION IDENTIFIED

### v2.11.20 RCA claim
Nested slice iterate 是 RC-1 fix 修了 5/6 slice test 但 nested case 仍 SEGV;deeper indirect dispatch chain (~20-40 LOC)。

### v2.11.21 RCA finding
**Hypothesis REFUTED on root cause**. Real bug is **v2.11.20 RC-1 fix itself was wrong direction** — flag propagation in `emit_load` over-aggressive.

### Real root cause (file:line)
`compiler/src0/codegen_amd64_emit_mem.jhyy:704-710` (v2.11.20 RC-1 Phase 1 block):
```jhyy
if (*t).qbe_type == QBE_L_LOCAL() {
    let _lp = cg_record_temp_holds_address(state, dst);
}
```
When `t42 = loadl t41` runs (where `t41 = data_ptr + i*16` is a real runtime address-holder), this marks `t42` as address-holder. But `t42`'s slot stores the **value** loaded from `*t41` (the row's `data_ptr` VALUE) — NOT a stack-slot address. Then `t49 = loadl t42` in the inner loop emits indirect dispatch (`movq -368(%rbp), %r8; movq (%r8), %rax` at `/tmp/_rca_fisn.s:229-230`), dereferencing the row's `data_ptr` as a slot address → SEGV.

**Semantic distinction**: `load` dereferences its src (read memory); result is a VALUE not an address. Only `alloc` and `add/sub on pointer` produce slot/runtime addresses. RC-1's load-propagation collapses these cases.

### Real fix sketch (~5 LOC net)
**Edit 1**: Remove load propagation block (lines 704-710) in `codegen_amd64_emit_mem.jhyy`. The indirect-dispatch logic itself (lines 692-720) stays — needed when src is alloc-result (so `load t_alloc` correctly reads slot contents). Just don't mark dst.

**Edit 2**: Tighten `emit_binop` propagation at `codegen_amd64_emit_call.jhyy:1615`:
```jhyy
if qt == QBE_L_LOCAL() && (is_add_or_sub != (0 as i32) || cg_is_address_holder(state, src1_id) != (0 as i32)) {
```
Always propagate for `add/sub` on L_LOCAL regardless of src1 flag (QBE IL semantics: `add/sub` on `QBE_L_LOCAL` operands yields derived address regardless of bitmap).

### Verification trace (for_in_slice_nested with Edit 1+2)
- `t41 = add t38, t40` → with Edit 2: marked ✓
- `t42 = loadl t41` → with Edit 1: NOT marked (value) ✓ — was the bug
- `t44 = add t42, 8` → with Edit 2: marked (L_LOCAL add) ✓
- `t45 = loadl t44` → indirect dispatch: `movq (%r8), %rax` ✓
- `t49 = loadl t42` (inner) → direct slot read: `movq -368(%rbp), %rax` ✓ — fixes SEGV

### Bonus benefit
- `for_in_slice_byte_equal` — same `loadl %slice + loadw t_result` pattern, also benefits
- `mixed_struct_slice_match` — has `loadl` patterns + nested access; partial benefit (RC-1 already fixed the outer level)

### ⚠️ REGRESSION IDENTIFIED
This bug is a clean illustration of "RCA stopped too early": original v2.11.20 RCA correctly identified that flag propagation was incomplete for slice_index/iterate patterns, but didn't verify the **direction** of propagation on the harder nested case. The fix that passed 5/6 slice tests in v2.11.20 actually introduced the SEGV in the 6th test. Per `feedback_codegen_amd64_multifn`, single-function PASS evidence is insufficient — multi-nested patterns require trace through every temp-id lifetime.

v2.11.20 changelog + workarounds.md W-074.10 description needs amendment (RC-1 description claimed it was "真修" but was actually over-aggressive for nested case).

---

## 5. silent-fail audit — 115 PASS sample (W-074.6 PARTIAL closure verification)

### Method
8 representative tests (covering W-074.10/11/12 fixed codepaths): slice_literal, slice_subrange, mixed_struct_slice_match, const_array, top_level_let_mut_test, match_range, nested_struct_deep, big_test.

For each: compile under QBE + self-backend, diff .s for fn/call/instruction structural identity + EXIT codes match.

### Result: **0 phantom PASS / 8 sampled**

| Test | QBE exit | SELF exit | .s verdict |
|---|---|---|---|
| slice_literal | 60 | 60 | PASS-confirmed (RC-1) |
| slice_subrange | 60 | 60 | PASS-confirmed (RC-1) |
| mixed_struct_slice_match | 131 | 131 | PASS-confirmed (RC-1; 3 fns match) |
| const_array | 122 | 122 | PASS-confirmed (RC-1 LABEL path; SELF adds `ASCII_LOWER` .globl — intentional) |
| top_level_let_mut_test | 42 | 42 | PASS-confirmed (W-074.11 $label path) |
| match_range | 0 | 0 | PASS-confirmed (W-074.12 clamp) |
| nested_struct_deep | 22 | 22 | PASS-confirmed (3 fns match) |
| big_test | 12345 | 12345 | PASS-confirmed (107 fns match) |

### Key findings
1. **Function set identical** for 6/8 tests. 2/8 with extra symbols (const_array: `ASCII_LOWER`, top_level_let_mut: `g_x`, big_test: 62x `str*`) are **intentional data-section emissions** — both backends place data, just different style.
2. **Call sites identical** — QBE uses `callq`, SELF uses `call`; counts match (match_range 12/12, nested_struct_deep 2/2, big_test 158/158).
3. **W-074.10/11/12 fixes confirmed working structurally** — RIP-relative, `%r8` indirect dispatch, sign-aware clamp all present.
4. **Instruction count divergence cosmetic** — SELF uses 1-to-1 stack slot allocation (5-7x more mov), not a semantic difference.

### Estimate
**115/139 PASS → ~108-115 true PASS, 0 phantom PASS detected in this sample.** The 24 fail cluster concentrated in W-074.13 deferred items, not scattered phantom PASSes.

### Caveat
8/8 not statistically conclusive for full 115. v2.11.21-fix sprint should add **stratified random sample of ~20 tests** (especially borderline ones with regress history) as belt-and-suspenders gate. This addresses `feedback_codegen_amd64_multifn` concern that single-function PASS evidence is insufficient.

---

## 6. v2.11.21-fix sprint scope (proposed)

### Code changes (~30-75 LOC, down from initial 140-230 estimate)

| Phase | Test | Fix file:line | LOC |
|---|---|---|---|
| 1 | cap_table_basic | `codegen_amd64_emit_call.jhyy:1067-1071` (validate src_temp_id, fall through to FNARG) | 5-10 |
| 2 | big_array | `codegen_amd64_emit_mem.jhyy:284-297` (emit_alloc record pointer-slot below region) | 10-30 |
| 3 | for_in_slice_nested | `codegen_amd64_emit_mem.jhyy:704-710` (delete block) + `codegen_amd64_emit_call.jhyy:1615` (tighten condition) | ~5 net |
| 4 | dungeon_game | `codegen_amd64_emit_ctrl.jhyy:266` (debug + fix label emit) — depends on RCA outcome | 10-80 |

### Re-baseline impact
- W-074.10 (v2.11.20 emit_load flag propagate) needs amendment — over-aggressive for nested case; correct semantics is "load does NOT propagate, but add/sub on L_LOCAL always propagate". v2.11.20 changelog + workarounds.md W-074.10 description needs update.
- W-074.13 sub-bug 2 (cap_table_basic) description needs correction — not fnarg ID gap but emit_copy heuristic miscounts `%t`.
- W-074.13 sub-bug 3 (dungeon_game) description needs correction — not multi-file import link but missing label definitions.
- W-074.13 sub-bug 4 (for_in_slice_nested) description needs correction — not deeper indirect dispatch chain but v2.11.20 RC-1 over-aggressive.

### Verification gates (per `feedback_fix_evaluation_rule` 5/5 PASS)
- V.1 cap_table_basic: self-backend EXIT=42 ✓
- V.2 big_array: self-backend EXIT=5050 ✓
- V.3 for_in_slice_nested: self-backend EXIT=66 ✓
- V.4 for_in_slice_byte_equal: regression — should still PASS after fix ✓
- V.5 mixed_struct_slice_match: regression — should still PASS ✓
- V.6 dungeon_game: self-backend EXIT=0 (with stdin data) ✓
- V.7 regress delta: 115/139 → 119/139 PASS (+4)
- V.8 stratified sample of 20 random PASS tests (silent-fail gate)
- V.9 D43 closure HOLD (v2/v3/v4/v5 byte-equal) — likely re-baseline per V.7 history

### Doc updates
- `docs/internal/workarounds.md` W-074.10/11/12/13 + W-074.6 description amendments
- `docs/internal/rca/rca-v2.11.20.md` RC-1 amendment (over-aggressive)
- `docs/logs/v2/changelog-v2.11.0.md` v2.11.21 ship section
- `docs/plans/v2/v2.11.21-plan.md` NEW (per `feedback_plans_per_version`)
- `docs/internal/architecture.md` Last updated v2.11.21

### Out of scope (推后续)
- ❌ 完整 V3-C 3i generics refactor (推 v3.x — v2.11.21 RC-2 fix 是 surgical emit_alloc 不动 generics)
- ❌ QBE 自写 (推 v2.x 末)
- ❌ codegen_amd64 真 XMM regalloc (推 v2.x 中期)
- ❌ N 代 fixed point 大幅度扩展 (推 v2.x 末)

---

## 7. References

- `docs/internal/rca/rca-v2.11.20.md` (v2.11.20 RCA — 4 sub-bugs partially misdiagnosed)
- `docs/internal/workarounds.md` W-074.6 PARTIAL + W-074.10/11/12 CLOSED + W-074.13 DEFERRED (this RCA refines)
- `docs/logs/v2/changelog-v2.11.0.md` v2.11.20 ship section
- `docs/plans/v2/v2.11.20-plan.md` (predecessor plan)
- `docs/internal/architecture.md` Last updated v2.11.20
- Memory: [[feedback_rca_first_root_cause]], [[feedback_codegen_amd64_multifn]], [[feedback_fix_evaluation_rule]], [[feedback_codegen_amd64_run_zerobyte]]
- Source: `compiler/src0/codegen_amd64_emit_mem.jhyy:284-297, 613-720, 704-710`
- Source: `compiler/src0/codegen_amd64_emit_call.jhyy:1057-1071, 1089-1123, 1230-1265, 1615`
- Source: `compiler/src0/codegen_amd64_emit_ctrl.jhyy:248-253, 266-298`
- Source: `compiler/src0/codegen_amd64_lexer.jhyy:913-925`
- Source: `compiler/src0/codegen_amd64_state.jhyy:251-262, 280-330, 644-650, 717-760, 808-837`
