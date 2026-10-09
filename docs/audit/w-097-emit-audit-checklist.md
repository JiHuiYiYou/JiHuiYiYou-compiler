# W-097 emit-path deep audit checklist

**Date:** 2026-10-09 · **Author:** MiniMax-M3 · **Status:** in-progress (Phase 2 of W-097 sprint, per v4.0.2.3 plan)
**Strategy:** per `feedback_deep_audit_checklist_first` — list all emit paths with operand-order / literal-emit / binop concerns BEFORE fixing, sub-bugs → fresh W-NNN entries

## Scope

W-097 (jhyy-side codegen emit_func_header per_fn_max lookup operand swap) was initially identified as a multifn frame blow-up bug. W-098 (jhyy-side codegen emit i64 literal > 32-bit range 截 i32 + cltq sign-extend) was found as a 1-iter RCA sub-bug (per `feedback_rca_first_root_cause`) while fixing W-075 mem_set.

This audit walks every emit path under `compiler/src0/codegen_amd64_*.jhyy` that has operand order / literal emit / binop concerns, looking for additional sub-bugs in the same family.

## Sub-bugs identified so far

### ✅ W-098 — jhyy-side codegen emit i64 literal > 32-bit range 截 i32 (ACT)

**Location:** `compiler/src0/codegen_amd64_emit_call.jhyy:383-395` (primary: `emit_mov_imm_to_offset`)

**Root cause:** GAS rejects `movq $imm64, mem` for imm64 > 32-bit signed range. The instruction silently truncates imm64 to imm32 and sign-extends, dropping high 32 bits. The correct sequence (used in `emit_mov_f64_imm_to_offset` at line 403-414) is `movabsq $imm64, %rax; movq %rax, mem`.

**Min repro:** `compiler/tests/examples/std_mem_set_aligned.jhyy` byte 4 check (EXIT=204 fails before workaround, EXIT=0 with b32|shift|OR workaround).

**Status:** workaround shipped in v4.0.2.3 (W-075 mem_set b8 构造走 b32|shift|OR). Real fix in W-097 deep audit sprint.

**Affected emit paths (full surface, all emit `<op>q $imm64, %<rax>` which has same root cause):**

| File:line | Function | Op | Risk |
|---|---|---|---|
| `emit_call.jhyy:383-395` | `emit_mov_imm_to_offset` | `mov<size> $imm64, mem` (i64 direct) | **W-098 primary** |
| `emit_call.jhyy:1808-1812` | `emit_binop` (sub, imm) | `subq $imm64, %rax` | same W-098 family |
| `emit_call.jhyy:1824-1828` | `emit_binop` (mul/imul, imm) | `imulq $imm64, %rax` | same W-098 family |
| `emit_call.jhyy:1847-1850` | `emit_binop` (div/idiv, imm) | `idivq $imm64, %rax` | same W-098 family |
| `emit_call.jhyy:1870-1873` | `emit_binop` (mod, imm) | `idivq $imm64, %rax` (then `movq %rdx, %rax`) | same W-098 family |
| `emit_call.jhyy:1896-1899` | `emit_binop` (rem, imm) | `idivq $imm64, %rax` (then `movq %rdx, %rax`) | same W-098 family |
| `emit_call.jhyy:1912-1916` | `emit_binop` (and, imm) | `andq $imm64, %rax` | same W-098 family |
| `emit_call.jhyy:1928-1932` | `emit_binop` (or, imm) | `orq $imm64, %rax` | same W-098 family |
| `emit_call.jhyy:1944-1948` | `emit_binop` (xor, imm) | `xorq $imm64, %rax` | same W-098 family |
| `emit_call.jhyy:1971-1979` | `emit_binop` (shl/shr, imm) | `shlq $imm64, %rax` / `shrq $imm64, %rax` | same W-098 family (shifts only use low 5/6 bits of imm, lower risk but still same emit pattern) |
| `emit_call.jhyy:2066-2070` | `emit_binop` (cmp, imm) | `cmpq $imm64, %rax` | same W-098 family |
| `emit_call.jhyy:2137-2141` | `emit_binop` (add fallback, imm) | `addq $imm64, %rax` | same W-098 family |

**Real fix design:** For QBE_L_LOCAL destination, replace `mov<size>q $imm64, mem` with `movabsq $imm64, %rax; movq %rax, mem` (mirror `emit_mov_f64_imm_to_offset` at line 403-414). For QBE_W_LOCAL destination, `movl $imm32, mem` is fine. For QBE_D_LOCAL/QBE_S_LOCAL, the `movabsq + movq` path is already in use (f64 IMM path).

### ⏳ W-097 — emit_func_header per_fn_max lookup operand swap (DEFERRED)

**Location:** `compiler/src0/codegen_amd64_emit_ctrl.jhyy:519,529,551` (multi-field-access pattern)

**Root cause (suspected):** jhyy-side codegen emits the `ptr_add_u8(field_a, (field_b - N) * 8)` pattern wrong — imul uses stack var instead of immediate `$8`, no sub for `cur_fn_idx-1`.

**Affected emit paths:**
- `emit_ctrl.jhyy:519` — `ptr_add_u8((*cg).per_fn_max, (*cg).cur_fn_idx * (8 as i64))` — simpler pattern (no `-1`)
- `emit_ctrl.jhyy:529` — `ptr_add_u8((*cg).per_fn_max, ((*cg).cur_fn_idx - (1 as i64)) * (8 as i64))` — **W-097 trigger** (has `-1`)
- `emit_ctrl.jhyy:551` — `ptr_add_u8((*cg2).per_fn_alloc, (*cg2).cur_fn_idx * (8 as i64))` — same family

**Verify baseline:** jhyy_v1.exe.exe (built with W-096 fix 3 = `95ba01a`) doesn't trigger this. jhyy_v2.exe.exe (jhyy-side compiled with v1) DOES trigger. The W-097 pattern only fires when jhyy-side codegen emits the binop sequence for `* 8` with multi-field access.

## Audit checklist — emit paths to walk

For each path, check: does it emit any immediate operand (i.e. `$imm`) for an instruction that has a 32-bit imm restriction? Does it use `ptr_add_u8(field_a, expression)` with multi-field-access expressions? Does it use binop ops with imm src2?

### `compiler/src0/codegen_amd64_emit_call.jhyy`

| Line | Function | Concern | Status |
|---|---|---|---|
| 97 | `emit_comment` | string emit (escape?) | OK — only ASCII text |
| 116 | `size_suffix_for_qt` | W/L/D/S → l/q/q/l | OK |
| 137 | `reg_rax_for_qt` | qt → eax/rax/rax/eax | OK |
| 148 | `reg_rcx_for_qt` | qt → ecx/rcx | OK |
| 159 | `reg_rdx_for_qt` | qt → edx/rdx | OK |
| 179 | `local_temp_offset` | `cg_local_t_from_global(t)` + `* 8` | verify: jhyy-side emit correct? |
| 189 | `emit_mov_temp_to_offset` | mem-to-mem mov | OK (no imm) |
| 214 | `cg_parse_f64_imm_bits` | f64 IMM parse | OK (uses `* 8` and `<< 32` — see W-098 trigger below) |
| 327 | `cg_f32_imm_bits` | f32 IMM parse | OK |
| **383** | **`emit_mov_imm_to_offset`** | **W-098 primary** | **待真修** |
| 403 | `emit_mov_f64_imm_to_offset` | correct movabsq pattern | OK (reference impl) |
| 420 | `emit_mov_temp_to_reg` | temp → reg | OK |
| 438 | `emit_mov_reg_to_temp` | reg → temp | OK |
| 456 | `emit_binop_rsp_to_rax` | mem op %rax | OK |
| 499 | `target_is_win` | target tag check | OK |
| 526 | `reg_rax_for_qt_idx` | arg reg by idx | OK |
| 586 | `emit_amd64_arg_regs` | arg setup | verify imm emit? — uses stack/mem, not imm |
| 736 | `parse_call_nargs` | parse text | OK |
| 777 | `parse_call_fnname` | parse text | OK |
| 796 | `emit_call` | full call sequence | OK (no imm emit for >32-bit values) |
| 944 | `emit_phi` | phi resolve | noop per upstream |
| **1062** | **`emit_copy`** | **IMM copy → calls W-098 fn** | **W-098 indirect** |
| **1451** | **`emit_binop`** | **all 11 ops + add fallback with src2_is_imm** | **W-098 indirect (12 paths listed above)** |
| 2204 | `emit_volatile` | marker only | OK |

### `compiler/src0/codegen_amd64_emit_ctrl.jhyy`

| Line | Function | Concern | Status |
|---|---|---|---|
| 61 | `SHADOW_SPACE()` | const 32 | OK |
| 62 | `TEMP_SLOT_BYTES()` | const 8 | OK |
| 70 | `compute_offset_for_temp_id` | `t * 8` simple | OK (only `* 8`, no `-1`) |
| 81 | `compute_offset_for_temp_id_with_target` | same + target | OK |
| 100 | `emit_jmp` | jmp + label | OK |
| 166 | `emit_jnz` | jnz + label | OK |
| 271 | `emit_label` | label: | OK |
| 321 | `emit_ret` | ret + zero-ext | OK |
| **444** | **`emit_func_header`** | **W-097 multi-field-access** | **待真修** |
| 645 | `emit_data_string` | .globl + .ascii/.byte | verify escape (W-073) |

### `compiler/src0/codegen_amd64_emit_mem.jhyy`

| Line | Function | Concern | Status |
|---|---|---|---|
| 47-129 | mem_* helpers | byte/parse helpers | OK |
| 153 | `mem_effective_qbe_type` | qt normalize | OK |
| 170 | `mem_mov_suffix` | b/h/w/l/s/d → b/w/l/q/ss/sd | OK (different from call.jhyy size_suffix_for_qt) |
| 182 | `mem_scratch_reg` | b/h/w/l/s/d → al/ax/eax/rax/xmm0 | OK |
| 196 | `mem_temp_offset` | `cg_offset_for_temp_with_target` + fallback `local_t3 * 8` | verify: jhyy-side emit correct? |
| 215-237 | mem_put/put_i64/put_slot | string builder wrapper | OK |
| 259 | `emit_alloc` | `subq $N, %rsp` | OK (imm = N, but N is small per-alloc, fits imm32) |
| **389** | **`emit_store`** | **label $str path + address-holder indirect** | **verify label emit** |
| **528** | **`emit_loadsub`** | **movsb/movzb/movsw/movzw + cltq** | **OK (no imm emit)** |
| **635** | **`emit_load`** | **mem → %<reg> + %<reg> → dst + zero-ext** | **OK (no imm emit)** |

### `compiler/src0/codegen_amd64_emit_sse.jhyy`

| Line | Function | Concern | Status |
|---|---|---|---|
| 45-87 | SSE helpers | xmm reg / suffix / mov | OK |
| 108 | `emit_conv_dtosi` | cvttsd2si + mov | OK |
| 143 | `emit_conv_stosi` | cvttss2si + movss + mov | OK |
| 177 | `emit_conv_truncd` | cvtsd2ss + movss | OK |
| 204 | `emit_conv_exts_f32_to_f64` | cvtss2sd + movsd | OK |
| 229 | `emit_conv_sltof` | movq + cvtsi2sd + movsd | OK |
| 260 | `emit_conv_swtof` | movl + cltq + cvtsi2ss/sd + movss/sd | OK |
| 306 | `emit_conv_ultof` | u64 → f64 half trick (7 insn) | OK |
| 336 | `emit_conv_uwtof` | u32 → f32/f64 (similar) | OK (verify: no imm emit) |

## Sub-bugs to file (W-099+)

If audit finds new sub-bugs (after W-098 fix is verified), file as fresh W-NNN entries per `feedback_deep_audit_checklist_first`. Currently expected to surface:

- **W-099 candidate:** `local_temp_offset` (line 179) — `cg_local_t_from_global(t) * 8` — verify jhyy-side emit
- **W-100 candidate:** `mem_temp_offset` (line 196) — fallback `local_t3 * 8` — same verify
- **W-101 candidate:** `emit_data_string` (line 645) — W-073 escape fix already in main, but verify W-097 family (operand order in escape handler)

If any other sub-bug surfaces during audit (e.g. src2_is_imm + qt mismatch), file immediately.

## Verification plan (per W-097 deep audit sprint)

1. **W-098 真修:** add `emit_mov_imm_to_offset` qt=L dispatch to mirror f64 path (movabsq + movq). Apply to all 12 binop paths with src2_is_imm. Verify 5/5 PASS on `std_mem_set_aligned.jhyy` (no longer needs b32|shift|OR workaround).
2. **W-097 真修:** audit `emit_func_header` line 519/529/551 multi-field-access. Likely fix: hoist `(cur_fn_idx - 1) * 8` to a local var first, then `ptr_add_u8(per_fn_max, local_var)`. Verify 5/5 PASS on jhyy-side compiled V2 binary.
3. **Sub-bugs 真修:** per W-NNN entry filed during audit.

## Commit cadence (W-097 deep audit sprint)

| # | Commit | Status |
|---|---|---|
| 1 | `docs(audit): W-097 deep audit checklist (this file)` | ⏳ wip |
| 2 | `fix(codegen): W-098 emit_mov_imm_to_offset qt=L → movabsq + movq` | ⏳ |
| 3 | `fix(codegen): W-098 binop src2_is_imm + qt=L → movabsq + movq (12 paths)` | ⏳ |
| 4 | `fix(codegen): W-097 emit_func_header multi-field-access hoist` | ⏳ |
| 5 | `test: std_mem_set_aligned no longer needs b32\|shift\|OR workaround` | ⏳ |
| 6 | `docs(workarounds): W-098 → RESOLVED + W-097 → RESOLVED + any W-NNN entries` | ⏳ |
| 7 | tag `v4.0.2.4` | ⏳ |

## References

- W-097 entry: `docs/internal/workarounds.md` (DEFERRED since 2026-10-09)
- W-098 entry: `docs/internal/workarounds.md` (ACTIVE since 2026-10-09)
- W-096 entry: `docs/internal/workarounds.md` (✅ RESOLVED 2026-10-08)
- Memory: `feedback_deep_audit_checklist_first` (this audit strategy)
- Memory: `feedback_rca_first_root_cause` (1-iter RCA before fix)
- Memory: `feedback_verify_active_reproduces` (verify ACTIVE repro before fix)
- Memory: `feedback_document_workarounds_in_docs` (W-NNN filing discipline)
- Memory: `feedback_fix_evaluation_rule` (5/5 PASS on target test)
- Related: W-074.6 (multifn silent fail upstream), W-075 (mem_set 真修 surface)
