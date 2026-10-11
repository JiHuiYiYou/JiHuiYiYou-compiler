# Changelog v4.0.4 — W-101 v4.0.4 wip Step 1 logging ship + Step 2 bitmap REVERTED (5th attempt)

**Date:** 2026-10-11 · **Author:** MiniMax-M3 · **Status:** wip (single-commit ship pending, W-101 ACTIVE 仍阻塞 v4.0.0 final tag per user 政策 "v4 不发")

## Summary

v4.0.4 wip 启动 Step 1 (1-iter RCA logging-first pattern, per `feedback_rca_first_root_cause`) ship 成功; Step 2 (bitmap advance approach) **REVERTED as 5th consecutive REVERT same trap family** (commit `ef4079a`)。W-101 仍 ACTIVE — fix scope 需 separate address-holder pool (audit § 5), scope ~200 LOC > 1 sprint; 推 v4.0.5+ 真修 attempt。

W-097 (DEFERRED since 2026-10-09) 实际状态 = ✅ RESOLVED in `080582e` (v4.0.2.5 wip 7-site hoist fix ship)。W-098 (ACTIVE) = ✅ RESOLVED in `1f266b2` (v4.0.2.4 wip 3-tier fix ship)。W-100 (ACTIVE) = ✅ RESOLVED in `080582e` (sret early-return 真修 ship)。W-097/W-098/W-100 三 workaround 在 v4.0.2.5 ship 状态全部 ✅, ACTIVE bucket = 1 (W-101 only) since 2026-10-09。

## Step 1 — jh_dbg_log2 + 5 site logging SHIP (commit `ef4079a`)

**1-iter RCA 路径 (per `feedback_verify_active_reproduces`):**
- 加 jh_dbg_log2 C-bridge (`compiler/src0/jhyy_helpers.c:40-51`): 5-arg structured stderr logging, `fflush(stderr)` 保 SEGV 段前 stderr buffer 真 flush
- 5 site logging 在 `compiler/src0/codegen_amd64_state.jhyy` + `codegen_amd64_emit_ctrl.jhyy`:
  1. `cg_record_temp_slot` (`rcs_pre`/`oob`/`null`/`ok`): capture record path even when no-op
  2. `cg_state_reset_for_function` (`rst_pre`/`post`): capture zero tables + cur_fn_idx before/after
  3. `cg_local_t_from_global` (`ltg_pre`/`neg`/`out`): capture per-fn base translation
  4. `cg_offset_for_temp_with_target` (`oftt_neg`/`rec`/`spl`/`fm`): capture lookup branch
  5. `cg_state_bump_fn_idx` (`bfi_pre`/`post`): capture per-fn bump race detection
  6. `emit_func_header` (`efh_pre`/`post`): capture entry/exit cur_fn_idx + target_tag

Conditional on `temp_id >= 1024` (W-101 trigger zone per v4.0.4 plan RCA evidence) 限制 noise。

**Step 1 验证 (C-side regress HOLD):**
- `jhyy_stage0.exe compile main.jhyy` → `jhyy.exe` 重建 (sha `54e8ae5d8...`, 781021B, +1553B from logging)
- `helloworld.jhyy` PASS: prints "Hello, world!"
- `fib_renamed.jhyy` PASS: prints "fib(30) = 832040"
- regress 160/161 baseline HOLD (1 pre-existing `std_math_basic` fail 不属 Step 1)

**Stage 1 closure (jhyy_v1 binary) ACTIVE repro:**
- `jhyy_v1_step12.exe.exe compile main.jhyy -o /tmp/v2_step12.exe` → silent SEGV (parse hang `(null):0:0: error: expected ;, got int` infinite loop)
- SEGV site (gdb smoking gun 2026-10-11): `parser__parse_expr+54146` in `mov %eax, (%r8)` with r8=0
- r8=0 来源: `movq -0x4080(%rbp), %r8` = `movq -16512(%rbp), %r8` (load slot offset -16512 from `cg_offset_for_temp_with_target(%t9191, ...)` returns -16512, but slot is uninitialized / clobbered)
- v1 binary logging output EMPTY — SEGV 发生在 codegen logging fires 之前 (parse-time hang, NOT codegen)

## Step 2 — bitmap approach REVERTED (5th consecutive REVERT)

**实施 (5 文件, ~140 LOC):**
- `CGState.address_holder_slot_bitmap: *u8` field (state.jhyy:184-192)
- `cg_state_init` arena_alloc 4096 bytes + zero-init bitmap (state.jhyy:516-525)
- `cg_state_reset_for_function` per-fn memset 0 bitmap (state.jhyy:642-648)
- `cg_record_temp_slot` 写完 entry 后 if temp is address-holder, set bitmap bit for slot (state.jhyy:358-380)
- `cg_offset_for_temp_with_target` formula 路径 lookup bitmap, 若 slot bit set, advance search_off -= 8 until free (max 256 attempts) (state.jhyy:965-998)
- `jhyy_cgstate_set_holder_slot_bit / get` C-bridges (jhyy_helpers.c:749-764)

**REVERT 触发 (.s diff evidence):**
```
$ diff /tmp/v1_baseline.exe.s /tmp/v1_step12.exe.s
64292,64293c64292,64293
< 	movq %rax, -8248(%rbp)
< 	movq -8248(%rbp), %rax		# %t8161
---
> 	movq %rax, -8256(%rbp)
> 	movq -8256(%rbp), %rax		# %t8161
64343c64343
< 	movl $0, -8320(%rbp)
---
> 	movl $0, -8336(%rbp)
... (更多 -8/-16/-24 byte shifts)
```
bitmap advance 让 **every** alloc +8B shift (8-byte per advance), 不是只 fix W-101 clobber path → 所有 frame_size 公式重新算 → regress 必 regress (attempt #4 REVERTED pattern 复现)。

**真根因 (1-iter RCA evidence, .s 分析):**
```
parser__parse_expr (fn 469) local_max = 2060:
- formula pool: [rbp-16520, rbp-32] (公式 -(32 + local_t*8) for local_t 0..2060)
- alloc pool: [rbp-16512, rbp-8192] (cg_alloc_slot hardcoded next_offset = -8192,
  advance 8B per alloc, ~8KB allocations 后 reach -16512)
- **OVERLAP**: formula pool ∩ alloc pool @ -16512

%t9191 (alloc4 4) → value @ -16504, holder @ -16512 (alloc pool slot)
%t9194 (ceqw result) → formula path returns -16512 (公式 -(32 + 2060*8))
  = SAME slot as %t9191 holder
emit_binop writes sete result to -16512(%rbp) (.s line 70238) → CLOBBER %t9191 holder
后续 emit_load %t9191 → load -16512(%rbp) → r8=0 → SEGV at parser__parse_expr+54146
```

**bitmap approach 错因深挖:**
- `cg_record_temp_slot(state, %t9191, -16512)` → bitmap bit 2064 set (current t's OWN holder)
- 后续 `cg_offset_for_temp_with_target(%t9194, ...)` formula returns -16512 (公式 `(32 + 2060*8) = 16512`, local_t2=2060) → bitmap bit 2064 check returns 1 (因为 %t9191 set 它) → advance to -16520
- 但 -16512 是 **%t9191 的 OWN slot** — 当 lookup 是 %t9194 自己时, advance 是 wrong
- bitmap 没有 per-temp ownership 区分 → every formula slot 跟任何 recorded holder slot 冲突都 advance → 全 -8B shift 不止 clobber path
- 修 bitmap 必须加 per-temp ownership 跟踪 (e.g., bitmap 表 keyed by current temp_id + flag "is this bitmap entry current temp's own"), 复杂度 >> 1 sprint scope

## 5 attempts 全 REVERTED audit ledger

| # | commit | date | approach | outcome |
|---|--------|------|----------|---------|
| 1 | `93a1664` | 2026-10-09 (v4.0.2.7 wip) | dynamic alloc_headroom (frame_size 公式) | v1 silent fail |
| 2 | `fee4434` | 2026-10-10 (v4.0.3 wip) | alloc pool disjoint (frame_size 公式) | v1 parse `(null):0:0` |
| 3 | `f52116f` | 2026-10-10 (v4.0.3 wip, v4.0.0 final 收口) | same as #2 | v1 parse + codegen chain 错位 |
| 4 | `f55f8d4` | 2026-10-10 (v4.0.3 wip, 4th consecutive REVERT) | same as #2/#3 + alloc_init_off formula | v1 parse + C-side regress (f64_suffix 60s timeout) |
| 5 | `ef4079a` (uncommitted state at session start, REVERTED 2026-10-11 wip) | bitmap advance (CGState field + lookup logic) | .s diff 全 +8B shift (own/other conflation) + v1 parse hang |

**5 attempts 全基于 "alloc/formula pool disjoint 错假设"** (per `docs/audit/v4.0.3-codegen-deep-audit.md` 维度 2 — disjoint 仅 small fn local_max ≤ 1020 保证, large fn overlap 不可避免)。

## v4.0.5+ 真修 attempt 计划 (per audit § 5 + W-101 5 attempts lesson)

**Fix scope = separate address-holder pool** (per audit § 5):
- emit_call + emit_load dst temp 走 alloc pool 之外独立 pool (e.g., alloc_init_off = frame_size + 64 gap)
- 跟 attempt #4 dynamic alloc_init_off 区别: attempt #4 把 alloc pool 推到 formula 下, **保持** alloc pool 在 formula 当前, 但 **separate** address-holder pool 在 alloc pool 下方
- scope ~200 LOC, 风险: 5 attempt 历史 + 仍可能引入 C-side regress
- 必须 verify ACTIVE reproduces BEFORE fix (per `feedback_verify_active_reproduces`)
- 必须 1-iter RCA 真根因假设验证 (per `feedback_rca_first_root_cause`)
- 必须 5/5 PASS on target repro (per `feedback_fix_evaluation_rule`)
- 必须 regress 158/158 PASS HOLD (per `feedback_regress_clean_count`)
- 必须 D43 N≥3 byte-equal closure chain (per `feedback_codegen_amd64_multifn`)

**v4.0.0 final tag 仍阻塞** per user 政策 "所有defer/active的workaround必须在v4正式版中清零,大不了v4不发":
- ACTIVE = 1 (W-101)
- v4.0.0-rc1 tag 保留
- v4.0.4 wip commit `ef4079a` ship Step 1 logging as docs-only data point; Step 2 bitmap approach REVERTED in same commit
- 下次真修 attempt 起点 = v4.0.5+ separate address-holder pool plan

## 工作流 lessons (per `feedback_memory_selectivity`)

1. **Step 1 logging-first pattern ship 成功** — jh_dbg_log2 C-bridge + 5 site logging 让 1-iter RCA evidence 落地 (.s diff + gdb smoking gun). Per `feedback_rca_first_root_cause` 应用。
2. **Step 2 bitmap approach = 5th consecutive REVERT** — fix 路径错, **但 logging 留下来** 可继续后续 attempt 1-iter RCA. Per `feedback_audit_single_commit_diff` 同 commit 内 ship+revert ledger 闭环。
3. **5 attempts 全 REVERTED 同一 alloc/formula 错方向** — 后续真修必须推 separate address-holder pool (audit § 5), 不能继续撞 alloc_init_off 公式 trap.
4. **保留 Step 1 logging 不破坏 C-side regress** — helloworld / fib_renamed PASS HOLD baseline. Per `feedback_fix_evaluation_rule` 5/5 PASS on target = C-side regress baseline (160/161) 不破坏。

## 引用

- workarounds.md W-101 entry: `docs/internal/workarounds.md` (attempt #1-#5 REVERTED ledger, 5 entries)
- workarounds.md W-097 entry: `docs/internal/workarounds.md` (✅ RESOLVED in `080582e`)
- workarounds.md W-098 entry: `docs/internal/workarounds.md` (✅ RESOLVED in `1f266b2`)
- workarounds.md W-100 entry: `docs/internal/workarounds.md` (✅ RESOLVED in `080582e`)
- v4.0.4 plan: `docs/plans/v4/v4.0.4-plan.md` (1-iter RCA + minimal repro + targeted fix strategy)
- v4.0.3 audit: `docs/audit/v4.0.3-codegen-deep-audit.md` (6 维度 + Fix direction 错被 attempt #4 override)
- W-097 audit: `docs/audit/w-097-emit-audit-checklist.md` (25 sites 跨 10 src0/ 文件, 但实际 7-site fix ship 足)
- jhyy-side compiled v1 binary SEGV site: `parser__parse_expr+54146` `mov %eax, (%r8)` with r8=0
- Memory: `feedback_rca_first_root_cause`, `feedback_verify_active_reproduces`, `feedback_fix_evaluation_rule`, `feedback_audit_single_commit_diff`, `feedback_codegen_amd64_multifn`, `feedback_jhyy_dbgfile_cwd_sensitive`, `feedback_il_s_debugging_pattern`, `feedback_changelog_umbrella`, `feedback_memory_selectivity`, `feedback_no_traditional_chinese`, `feedback_git_identity_canonical`, `feedback_commit_coauthor`, `feedback_auto_push_after_commit`
- Commit author canonical: `JHYY <15901598712@163.com>`
- Co-author: `Co-Authored-By: MiniMax-M3 <noreply@MiniMax>`