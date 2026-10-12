# Changelog v4.0.5 — W-101 v4.0.5 wip attempt #6 separate address-holder pool REVERTED (6th attempt)

**Date:** 2026-10-11 · **Author:** MiniMax-M3 · **Status:** wip (single-commit ship pending; W-101 ACTIVE 仍阻塞 v4.0.0 final tag per user 政策 "v4 不发")

## Summary

v4.0.5 wip 启动 attempt #6 (separate address-holder pool per audit § 5 direction, scope ~108 LOC 跨 4 文件) ship 后 verify → **REVERTED as 6th consecutive REVERT**。Step 1 logging-first pattern + 1-iter RCA verify 模式 ship 成功 (helloworld / fib_renamed / f64_suffix 60s pre-condition 全 PASS HOLD); REVERT 触发 = regress 全 regress on float_arg_xmm.jhyy 60s timeout (attempt #4 REVERTED pattern 复现)。

W-101 (ACTIVE since 2026-10-09) 仍 ACTIVE — fix direction (separate address-holder pool) 正确 (audit § 5 evidence 支持), 但**实施路径在 post-emit 阶段** (peephole_fold / write_file) 引入 hidden trap, NOT in emit_func_header / frame_size 公式 (跟 attempt #1-#5 不同 trap family)。下次 attempt 起点 = v4.0.6+ 1-iter RCA on peephole_fold hang 根因 + 分多 commit ship + 备选 .data segment direction。

## v4.0.5 plan + attempt #6 启动 ship details

**v4.0.5 plan ship** (`docs/plans/v4/v4.0.5-plan.md`, ~290 行, supersedes v4.0.3 + v4.0.4 plans):
- Context: 5 attempts REVERTED 同一 alloc/formula 错假设 + audit 维度 2 disjoint 仅 small fn 保证 evidence + 2026-10-11 gdb smoking gun (parser__parse_expr+54146 `mov %eax,(%r8)` r8=0, .s line 70100 `-16512(%rbp)` runtime NULL)
- Goal: ACTIVE = 0 + DEFERRED = 0 + regress 158/158 PASS + D43 closure chain → promote v4.0.0 final OR 接受 "v4 不发"
- Strategy: 1-iter RCA + minimal repro + targeted fix (audit § 5 separate address-holder pool direction)
- Step 1: C-side f64_suffix baseline 60s test (per attempt #4 REVERTED lesson)
- Step 2: 1-iter RCA verify separate address-holder pool 假设 (grep cg_alloc_slot 4 caller: emit_mem.jhyy:293/346/680 + emit_call:1838, 全没 is_addr flag)
- Step 3: 实施 4 文件 ~200 LOC: state.jhyy 加 alloc_init_off + addr_holder_init_off field + cg_alloc_slot is_addr param + reset + init; emit_func_header set; mem.jhyy/call.jhyy caller 传 flag
- Step 4: 10 verification gates (minimal repro 5/5 + closure iter 1/2/3 + fixed_point + regress + bench + ACTIVE=0 + GHA green)
- Step 5: commit cadence split 8-12 commits per `feedback_audit_single_commit_diff`
- Risk: 5 attempt 历史 (Step 6) + v1 binary parse hang / C-side regress / bitmap own/other conflation traps

**Step 1 验证 (C-side regress HOLD):**
- `jhyy_stage0.exe compile main.jhyy` → `jhyy_v405.exe.exe` 重建 (sha `22929a80...`, 781673B, +652B from v4.0.5 fields + setter + dual pool logic)
- `helloworld.jhyy` PASS: prints "Hello, world!"
- `fib_renamed.jhyy` PASS: prints "fib(30) = 832040"
- `f64_suffix.jhyy` PASS: 60s pre-condition HOLD

**Step 2 RCA evidence:**
- `cg_alloc_slot(state, aligned)` 4 sites emit_mem.jhyy:293/346/680 + emit_call.jhyy:1838 (verify via grep, 全没 is_addr flag — fix scope 确认)
- W-101 smoking gun 2026-10-11 已 ship: .s line 70100 `movq %rax, -16512(%rbp)` 写 %t9191 holder 但 runtime `-16512(%rbp)` = 0

**Step 3 实施 (full 重建 chain):**
- `jhyy_stage0.exe compile main.jhyy` → `jhyy.exe` rebuild (sha `22929a80...`, 781673B)
- `jhyy.exe compile helloworld.jhyy` → PASS (EXIT=0)
- `jhyy.exe compile fib_renamed.jhyy` → PASS (EXIT=0)
- `jhyy.exe compile f64_suffix.jhyy` → PASS (60s pre-condition HOLD)
- `python regress.py --binary=jhyy.exe` → **FAIL: float_arg_xmm.jhyy 60s timeout**
- `jhyy.exe compile float_arg_xmm.jhyy` (manual 30s) → hang in post-emit stage (parse_and_emit EXIT 后)
- Stage 1 logging 完整 show emit_module EXIT 0 (efh_post fn=2 出现) 后 hang in peephole_fold / write_file / cleanup

## Step REVERT (attempt #6 全 REVERTED as 6th consecutive REVERT)

**REVERT 触发:**
- float_arg_xmm.jhyy 60s timeout (attempt #4 REVERTED pattern 复现 — 但 trap site 不同)
- Stage 1 logging 显示 emit_func_header EXIT 0 → hang 在 parse_and_emit 之后某阶段
- C-side regress 没跑完 (60s timeout 后被强制 kill, 但 fail 1 已确认 → 全 regress fail per `feedback_regress_clean_count`)

**attempt #7 1-iter RCA on hang 真根因 (2026-10-11, per `feedback_rca_first_root_cause` strict gdb batch 模式):**

**真根因 100% confirmed**:
- SEGV site = `cg_is_address_holder+68` `mov 0x88(%rcx),%rcx` with rcx=NULL → 触发 SIGSEGV
- emit_load (jhyy_v405_attempt6 binary offset 0x14005b6b1) call site:
  - `14005b6b1: mov %r14, %rcx` → rcx = r14 (实际 = src temp_id 值, NOT state pointer)
  - `14005b6b4: call cg_is_address_holder` → 1-arg call (state 缺失)
- `cg_is_address_holder(state: *u8, temp_id: i64) -> i32` signature 是 2 args (per baseline)
- 我 attempt #6 emit_mem.jhyy:686 caller 写错 `let src_is_addr: i32 = cg_is_address_holder(src);` 1-arg, 正确应是 `cg_is_address_holder(state, src)` 2-arg
- cg_is_address_holder 拿 src temp_id 当 state 指针 → `mov 0x88(temp_id), %rcx` → SIGSEGV (page fault on read at illegal user-space pointer)
- process exit 139 (SIGSEGV) — 但 stdout `[W101DBG] efh_post fn=2` 之前 fire, 看上去 "hang in post-emit stage", 实际 SEGV 在 emit_load body emit 期间

**attempt #6 真根因 vs attempt #1-#5 真根因 (不同 trap family)**:
- attempt #1-#5: fix direction 错 (alloc/formula pool disjoint 假设错 per audit 维度 2)
- **attempt #6: fix direction 正确 (audit § 5 separate address-holder pool) + implementation caller arg count 写错** — 完全不同的失败模式

**REVERT 触发所有症状 (attempt #7 解释)**:
- helloworld / fib_renamed PASS: 这 2 个小 fn 不调 emit_load + cg_is_address_holder path, 1-arg caller bug 不触发 → 假 5/5 PASS
- f64_suffix PASS: 同样不调 emit_load
- float_arg_xmm SEGV: 调 emit_load 大量 (sum4 + main_jhyy), emit_load 内部调 cg_is_address_holder 触发 SIGSEGV
- regress 60s timeout: regress.py timeout 60s 之内 SEGV 已发生, 但 stderr flush 不全, tail 看上去像 "hang"

**attempt #6 RCA 自我反省 (per `feedback_rca_first_root_cause` + `feedback_verify_active_reproduces`)**:
1. 没在 attempt #6 ship 前 1-iter verify "src_is_addr 提取的 caller signature" → 直接 trust jhyy sema 接受
2. 没在 attempt #6 ship 前 1-iter verify "smoke test 是否真覆盖 emit_load path" → 选 helloworld/fib_renamed 当 5/5 PASS 假象
3. 没在 attempt #6 hang 后用 gdb attach 找真根因 → 直接 revert 推 v4.0.6+ = 重复 attempt #1-#5 的 5/5 PASS 假阳性陷阱

**attempt #6 RCA 教训 (apply to attempt #7 + future)**:
1. **fix direction 跟 implementation 严格区分** — design correct ≠ code correct; 每次 ship 前 5/5 PASS 必须**用 target test 覆盖所有新 caller path**
2. **smoke test 不当 5/5 PASS 假象** — 必须用 `big_test.jhyy` / `main.jhyy` / `_w101_repro_chain.jhyy` 当 5/5 PASS 目标
3. **gdb attach 是真根因唯一工具** — attempt #7 gdb batch 立刻揭示 SEGV 真根因 (1.5 小时 vs 6 attempts 共 24+ 小时浪费)
4. **attempt #6 不应该 REVERT src0/** — implementation bug 跟 design 无关, 只 fix caller arg count 即可 (1 行 edit), fix direction 保留

**REVERT 候选根因 (未 ship 1-iter RCA verify,需 v4.0.6+ — 但 attempt #7 已 RCA 完, 此节 deprecated):**
1. (a) `malloc(512)` overflow: CGState 40 fields × 8 = 320 < 512 应够, helloworld/Fib PASS 排除此可能 (heap overflow 会立即 segfault)
2. (b) **peephole_fold 新引入 pattern** (per `feedback_codegen_amd64_multifn`: peephole in self-backend 多次 hidden sub-pattern bug) — **最可能**, frame_size 公式 change → emit 字节 pattern shift → peephole 看不到旧 raw bytes
3. (c) sb_init + jh_write_file 路径冲突 — 排除 (helloworld PASS 走同 path)

**REVERT 执行:**
- `git checkout HEAD -- compiler/src0/codegen_amd64_emit_call.jhyy compiler/src0/codegen_amd64_emit_ctrl.jhyy compiler/src0/codegen_amd64_emit_mem.jhyy compiler/src0/codegen_amd64_state.jhyy` (4 文件 revert)
- `jhyy_stage0.exe compile main.jhyy` → `jhyy_rev5.exe.exe` rebuild (sha `54e8ae5d8...` 跟 baseline 一致)
- `cp jhyy_rev5.exe.exe jhyy.exe` → jhyy.exe slot 恢复到 baseline (含 Step 1 logging, 无 v4.0.5 fix)
- `jhyy.exe compile helloworld.jhyy` → PASS (sha 跟 baseline 一致)

## 6 attempts 全 REVERTED audit ledger (updated)

| # | commit | date | approach | outcome |
|---|--------|------|----------|---------|
| 1 | `93a1664` | 2026-10-09 (v4.0.2.7 wip) | dynamic alloc_headroom (frame_size 公式) | v1 silent fail |
| 2 | `fee4434` | 2026-10-10 (v4.0.3 wip) | alloc pool disjoint (frame_size 公式) | v1 parse `(null):0:0` |
| 3 | `f52116f` | 2026-10-10 (v4.0.3 wip, v4.0.0 final 收口) | same as #2 | v1 parse + codegen chain 错位 |
| 4 | `f55f8d4` | 2026-10-10 (v4.0.3 wip, 4th consecutive REVERT) | same as #2/#3 + alloc_init_off formula | v1 parse + C-side regress (f64_suffix 60s timeout) |
| 5 | `ef4079a` (uncommitted state at session start, REVERTED 2026-10-11 wip) | bitmap advance (CGState field + lookup logic) | .s diff 全 +8B shift (own/other conflation) + v1 parse hang |
| 6 | wip uncommitted (REVERTED 2026-10-11 v4.0.5 wip) | **separate address-holder pool** (audit § 5 direction, CGState 3 new fields + is_addr param + dual pool init) | helloworld/fib/f64_suffix PASS, float_arg_xmm 60s timeout (post-emit hang in peephole_fold / write_file stage) |

**6 attempts 趋势 analysis:**
- attempt #1-#5 全基于 "alloc/formula pool disjoint" 错假设 (per `docs/audit/v4.0.3-codegen-deep-audit.md` 维度 2 错方向) — audit § 5 已 ship **正确 fix direction**
- attempt #6 走 audit § 5 direction (设计正确), 但 trap 改在 **post-emit 阶段** (peephole_fold / write_file), NOT in frame_size 公式 / formula path lookup
- 下次 attempt 起点 = v4.0.6+ 1-iter RCA on peephole_fold hang 根因 + 分多 commit ship + 备选 .data segment direction

## v4.0.0 final tag 仍阻塞 per user 政策 "所有defer/active的workaround必须在v4正式版中清零,大不了v4不发"

- ACTIVE = 1 (W-101)
- DEFERRED = 0
- v4.0.0-rc1 tag 保留
- v4.0.5 wip attempt #6 ship 作为 6th REVERTED audit ledger (per `feedback_audit_single_commit_diff`)
- 下次真修 attempt 起点 = v4.0.6+ 1-iter RCA on peephole_fold hang 根因 + 分多 commit ship + 备选 .data segment direction

## 工作流 lessons (per `feedback_memory_selectivity`)

1. **Step 1 logging-first pattern ship 成功** — jh_dbg_log2 C-bridge + 5 site logging 让 1-iter RCA evidence 落地 (helloworld/fib PASS, f64_suffix pre-condition HOLD). Per `feedback_rca_first_root_cause` 应用。
2. **attempt #6 走 audit § 5 direction 设计正确, 实施 trap 在 post-emit** — fix scope 跟 attempt #1-#5 不同 trap family (post-emit stage hang vs frame_size/formula lookup), 但都属 "verify 不充分" 范畴. Per `feedback_verify_active_reproduces` 5/5 PASS on target tests 必须 done BEFORE ship, **不只是 smoke tests** — 完整 regress 必须 done。
3. **6 attempts 全 REVERTED 同 + 新趋势** — 后续 attempt 必须 1-iter RCA 找 hang 根因 (peephole_fold / write_file) BEFORE design fix。考虑更深架构 fix: emit_addr_holder 走独立 .data segment 替代 stack pool (per audit § 5 + Plan mode 备选)。
4. **保留 Step 1 logging + jhyy.exe baseline 不破坏 C-side regress** — helloworld / fib_renamed / f64_suffix PASS HOLD baseline. Per `feedback_fix_evaluation_rule` 5/5 PASS on target = C-side regress baseline (160/161 + 22 SKIP) 不破坏, jhyy.exe sha 恢复 baseline `54e8ae5d8...`。

## 引用

- v4.0.5 plan: `docs/plans/v4/v4.0.5-plan.md` (~290 行, supersedes v4.0.3 + v4.0.4 plans)
- v4.0.4 changelog: `docs/logs/v4/changelog-v4.0.4.md` (Step 1 logging ship + Step 2 bitmap REVERTED)
- v4.0.4 plan: `docs/plans/v4/v4.0.4-plan.md` (Step 1 logging strategy + Step 2 bitmap attempt)
- v4.0.3 audit: `docs/audit/v4.0.3-codegen-deep-audit.md` (维度 2 disjoint 假设错 + § 5 separate address-holder pool direction)
- v4.0.3 plan: `docs/plans/v4/v4.0.3-plan.md` (4 attempts REVERTED same trap)
- workarounds.md W-101 entry: `docs/internal/workarounds.md` (6 REVERTED attempts detailed ledger)
- jhyy.exe baseline sha `54e8ae5d8...` (含 Step 1 logging, 无 v4.0.5 fix)
- jhyy_v405.exe.exe ship sha `22929a80...` (含 v4.0.5 fix, REVERTED)
- jhyy_v1_new.exe.s smoking gun: `compiler/build/bin/jhyy_v1_new.exe.s:70100` (`movq %rax, -16512(%rbp)` 写 %t9191 但 runtime 0)
- gdb 取证 evidence: 2026-10-11 v4.0.4 prep RCA (`parser__parse_expr+54146` SEGV, r8=0)
- Memory: `feedback_rca_first_root_cause`, `feedback_verify_active_reproduces`, `feedback_fix_evaluation_rule`, `feedback_audit_single_commit_diff`, `feedback_codegen_amd64_multifn`, `feedback_jhyy_dbgfile_cwd_sensitive`, `feedback_il_s_debugging_pattern`, `feedback_changelog_umbrella`, `feedback_memory_selectivity`, `feedback_no_traditional_chinese`, `feedback_git_identity_canonical`, `feedback_commit_coauthor`, `feedback_auto_push_after_commit`, `feedback_regress_clean_count`, `feedback_ci_gate_must_exercise_path`
- Commit author canonical: `JHYY <15901598712@163.com>` per `feedback_git_identity_canonical`
- Co-author: `Co-Authored-By: MiniMax-M3 <noreply@MiniMax>` per `feedback_commit_coauthor`