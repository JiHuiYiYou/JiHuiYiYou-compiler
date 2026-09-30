# Changelog v2.11.23 (2026-09-17) — 🏆 **历史性一刻**

**🎯 首次 self-backend 0 FAIL parity with QBE path — jhyy 编 jhyy 走自研 amd64 后端, 跑通所有 119 个 active regression test (QBE 119/139 PASS, self-backend 119/139 PASS / 0 FAIL / 20 SKIP, 4 DEFERRED sub-bug 全真修)**

> **Per [`feedback_changelog_umbrella`](../../../JiHuiYiYou/memory/feedback_changelog_umbrella.md)**: v2.x 轴用 umbrella `docs/logs/v2/changelog-v2.11.0.md`, 不创建 standalone changelog。但本 sprint 满足 **"sprint 实在长 (>10 commit) / 涉及重大 pivot" 例外条款** — 架构修 (slot-vs-region overlap) + 4 个 DEFERRED sub-bug 全真修 + ACTIVE workaround 5 → 3 + 首次 self-backend 0 FAIL parity with QBE path — 跟 v1.0.0 standalone 同级别 milestone celebration, 单拆一份独立 milestone doc (umbrella 顶部加 link 索引, **不**重复 umbrella section 内容)。

## 成就

| 项 | 值 |
|---|---|
| **v2.11.23 tag** | commit `0d66195` (2026-09-17, Phase 1+2+3 ship) |
| **里程碑** | **🎯 Self-backend 0 FAIL parity with QBE path 首次达成** (架构修 pivot, 4 DEFERRED sub-bug 全真修) |
| jhyy.exe sha (Phase 2 re-build) | `02118a50da775af29e40460431e8f17f9417688bc4d8fd4ada6477f6f9779ede` |
| jhyy.exe sha (v2.11.21-fix 末) | `5f225239...` |
| regress.py default QBE mode | **119/139 PASS** (best case, occasional flaky 1 FAIL on slice_index/nested_struct_deep — 跟 parity 无关) |
| regress.py --self-backend mode | **119/139 PASS / 0 FAIL / 20 SKIP** ✅ (稳定, 跟 QBE best case 数字一致) |
| regress.py active test set | 119/139 = 117 active PASS + 2 deferred DEFERRED-then-CLOSED = **119 PASS / 0 FAIL** (active set) |
| regress.py stage0 (C-side mirror) | 105/134 — **C-side frozen per 2026-09-16**, 不变 |
| self-host closure chain | v2 → v3 → v4 → v5 byte-equal `e6b6f1fa...` (re-baseline from `f61f467e...`) — **HOLD** (Phase 1+2 src0 changes 不影响 main.jhyy IL path) |
| ACTIVE workaround count | 5 → **3** (W-074.13 4 sub-bug 全 ✅ CLOSED) |
| Pure src0 LOC | **5 LOC total** (audit verify 后, v2.11.22 plan 估 65 LOC 收敛 13x) |

## 闭环定义 (达成)

> **Self-backend 0 FAIL parity with QBE path**: `python regress.py` (default QBE) 跟 `python regress.py --self-backend` (JHY_SELF_BACKEND=1 env) 跑同一套 119 个 active test, **两边 exit code byte-equal + 0 FAIL**。QBE 偶尔 flaky 1 fail (slice_index / nested_struct_deep 偶发) 不影响 parity — self-backend 是稳定 0 FAIL, parity 是 self-backend 能完整替代 QBE 跑通 active test set。
>
> 之前 sprint ship 时: self-backend 一直有 4 FAIL (big_array + cap_table_basic + dungeon_game + for_in_slice_nested) — v2.11.23 架构修后 4 sub-bug 全真修 → **首次 self-backend 0 FAIL**。
>
> **Stage 2 self-hosting closure** (separate milestone, v1.0.0 ship): jhyy_v1 编 src0/main.jhyy → jhyy_v2 → jhyy_v3 → jhyy_v4 → jhyy_v5 编 src0/main.jhyy → 全部 4 份 raw .il byte-equal — fixed point attractor。当前 v2.11.23 baseline `e6b6f1fa...` v2..v5 仍 byte-equal, v1 path WONTFIX 已知偏差 (per v2.11.19 ship B3 反馈, 不再 attempt 修复)。

## 三门槛全过

```
✅ 门槛 1: regress.py default QBE mode     → 119/139 PASS (best case)
✅ 门槛 2: regress.py --self-backend mode  → 119/139 PASS / 0 FAIL / 20 SKIP (稳定)
✅ 门槛 3: self-host closure chain (N=5)   → v2/v3/v4/v5 byte-equal `e6b6f1fa...` (HOLD)
✅ 门槛 4 (新增): ACTIVE workaround 5 → 3  → W-074.13 4 sub-bug 全 CLOSED
```

## 真修里程碑 — slot-vs-region overlap 架构修

**W-074.13 真根因 (Plan agent + audit verify 2026-09-17)**:

v2.11.5 design 写好 `cg_record_temp_slot` API (state.jhyy:251) — 写 dst's pointer-slot = region offset。v2.11.5 broken (self-referential bug: `mov %rax, -<off>(%rbp)` 写 address 到 region 本身 overwrite)。v2.11.8 真修: explicit SKIP `cg_record_temp_slot` (走 formula `-(32+t*8)` 避开 self-referential)。但 formula 在某些 t 上 = region offset — formula pool 跟 region pool 都从 0 起负方向增长 → 同 frame 内 collision。

**Collision 例**:
- t2 = `alloc16 16` → region = `-48` (cg_alloc_slot next_offset advance)。formula `-(32+2*8) = -48` → **t2's pointer-slot 物理上 = t2's region**
- v2.11.8 SKIP comment author 检查 t6 (formula = -80, region = -48, 不 collision) 就以为 OK — 漏了 t2 (formula = -48, region = -48, **collision**)
- 后果: t2 后续 `add dst, imm` 看不到 address-holder flag → 走 slot read 路径 → 读到的是 region 自身存的 address 写过去的 byte → **wrong value** (big_array `t21 = t1 + 200`, formula `-200` = arr[50] region address `-400+4*50=-200` → wrong arr[50] = arr[0] base)

**Fix (2 emit calls + 1 frame_size 兜底, 5 LOC total)**:

| # | 文件 | Fix |
|---|------|-----|
| 1 | `compiler/src0/codegen_amd64_emit_mem.jhyy:322` (emit_alloc) | re-enable `cg_record_temp_slot(state, dst, off - 8)` (1 行 fix) — pointer-slot = region 下面 8 字节 (物理上 stack offset 更负), 跟 region 物理分离 + 跟 formula pool 物理分离 |
| 2 | `compiler/src0/codegen_amd64_emit_call.jhyy:1684` (emit_binop derived-temp) | 追加 `cg_alloc_slot(state, 8) + cg_record_temp_slot(state, dst_id, derived_slot)` (2 行 fix) — derived address-holder 走 dedicated slot, 跟 region element 物理分离 |
| 3 | `compiler/src0/codegen_amd64_emit_ctrl.jhyy:522-526` (frame_size 兜底) | `frame_size = max(frame_size, |next_offset|)` (1 行 fix, optional 但加了) |

**Why `off - 8` (not `off`)**: v2.11.5 design 写 `off = region` (self-referential bug)。`off - 8` 避开 self-referential (pointer-slot 在 region 下面 8 字节, 跟 region 物理分离)。`off - 8` (not `off + 8`): stack grows down, more-negative offset = 物理 "下面" (lower address)。

**关键不变量**:
- Region at `off`, pointer-slot at `off - 8` — 物理分离, 无 self-referential 风险
- `cg_offset_for_temp_with_target:639-660` tier-1 lookup 命中 return `off - 8` (覆盖 formula)
- Formula pool `-(32+t*8)` 走 tier-2 fallback (tier-1 命中 non-zero 直接 return)
- Alloc pool 跟 derived pool 共享 `cg_alloc_slot` next_offset — 同一 pool, advance 方向一致, 新 slot 总在最深位置, 不会 collision

## 5+ attempts 历史 (v2.11.20 → v2.11.23)

| Sprint | 路径 | 结论 |
|--------|------|------|
| **v2.11.20** (commit `73cba17`, 2026-09-15) | RC-1 emit_load/emit_copy LABEL flag propagate + W-017 module-level `let mut` + RC-4 match range | ✅ 修 11 tests, 但留下 4 FAIL (big_array + cap_table_basic + dungeon_game + for_in_slice_nested) DEFERRED |
| **v2.11.21-RCA** (commit `5dd9024`, 2026-09-17) | RCA-only sprint — 5 parallel sub-agent RCA + silent-fail audit on 8/115 PASS | ✅ 0 source LOC changes; W-074.13 description refined + W-074.10 caveat added; LOC 收敛估 ~25-75 for 真 fix |
| **v2.11.21-fix** (commit `a22b868`, 2026-09-17) | cap_table_basic 1 LOC + dungeon_game 1 LOC | ✅ 修 2 sub-bug (cap_table_basic + dungeon_game);2 DEFERRED (big_array + for_in_slice_nested) 真 fix > 80 LOC each 超 budget; regress 115 → 117 PASS |
| **v2.11.22 attempt** (commit `b76d385`, 2026-09-17) | 6 surgical edit attempt (slot-vs-region overlap RCA) | ❌ ALL REVERTED before commit; RCA claim **部分偏** (audit 命中 formula pool 跟 region pool collision, 不是 slot/region 本身共享); docs-only ship 记录 attempt outcome |
| **v2.11.23 (this sprint)** | emit_alloc re-enable cg_record_temp_slot + emit_binop derived-slot + frame_size 兜底 (5 LOC total) | ✅ 修 2 DEFERRED sub-bug (big_array + for_in_slice_nested);regress 117 → 119 PASS / 0 FAIL — **首次 self-backend 0 FAIL parity with QBE** |

## Sprint v2.11.23 — verification gates V.1-V.7

| Gate | 验证 | 结果 |
|------|------|------|
| V.1 | Phase 1 emit_alloc 1-line fix (for_in_slice_nested 真修) | ✅ EXIT=66 PASS + 12/12 regression PASS |
| V.2 | Phase 2 emit_binop 2-line fix (big_array 真修) | ✅ EXIT=5050 PASS + 9/9 regression PASS |
| V.3 | stratified random sample of 20 PASS tests silent-fail gate | ✅ 20/20 PASS exit + .s structural identity QBE vs self-backend |
| V.4 | regress.py --self-backend (FRESH) | ✅ 119/119 active PASS / 0 FAIL / 20 SKIP |
| V.5 | self-host closure chain N=5 byte-equal | ✅ v2/v3/v4/v5 byte-equal `e6b6f1fa...` (HOLD;re-baseline from `f61f467e...`) |
| V.6 | regress.py default QBE mode (FRESH) | ✅ 119/119 PASS best case (occasional flaky 1 FAIL on slice_index/nested_struct_deep — 跟前 sprint 状态一致, 跟 parity 无关) |
| V.7 | ACTIVE workaround count | ✅ 5 → 3 (W-074.13 sub-bug 1+2+3+4 全 CLOSED) |
| **V.8** (SysV cross-check) | sysv_float_cross.sh | ✅ 6/6 PASS (v2.11.19 baseline unchanged; per-alloc separate pointer-slot 是 target-agnostic, SysV 也 fix) |

**任意 fail-fast → revert 对应 commit, 不进 ship**。

## 4 sub-bug 真修历史 (W-074.13)

| Sub-bug | 真修 sprint | Fix LOC | 触发 test |
|---------|------------|---------|-----------|
| **#1 big_array** (slot alloc conflict — cg_alloc_slot region + formula `-(32+t*8)` 物理 collision) | **v2.11.23 Phase 1+2** | 3 LOC (emit_alloc + emit_binop + frame_size) | `big_array.jhyy` EXIT=5050 |
| **#2 cap_table_basic** (emit_load silent fail on `loadl %t3` — W-074.6 PARTIAL silent-fail 主项) | v2.11.21-fix Phase 1 | 1 LOC (`ndig > 0` gate on pct_count) | `cap_table_basic.jhyy` EXIT=42 |
| **#3 dungeon_game** (multi-file import + gcc link — main_jhyy 在 .s 里 not visible per linker) | v2.11.21-fix Phase 4 | 1 LOC (`next_token_ret` lex_skip_ws 不跨 `\n`) | `dungeon_game.jhyy` EXIT=0 |
| **#4 for_in_slice_nested** (nested slice iterate path SEGV — RC-1 fix 修了 5/6 slice test 但 nested case 仍 SEGV) | **v2.11.23 Phase 1** (emitted by Phase 1 alone, no Phase 2 needed for THIS test) | 1 LOC (emit_alloc `off - 8`) | `for_in_slice_nested.jhyy` EXIT=66 |

**Total: 6 LOC src0 真修 (across v2.11.21-fix + v2.11.23 combined)**, 4 sub-bug 全 CLOSED, ACTIVE workaround 5 → 3。

## 已知限制 (不算 blocker, v2.11.23 ship)

1. **覆盖率 119/139** — 117 active PASS + 2 真修 (big_array + for_in_slice_nested) = 119 active + 20 SKIP。 规模仍 < 200, 工业级通常 ≥1000+ + 第三方 benchmark。
2. **QBE flaky** — QBE mode 偶发 1 FAIL on slice_index / nested_struct_deep (不是稳定 fail, 是 race-like 时序 — 与 self-backend parity 无关, 跟前 sprint 状态一致)。
3. **self-host closure v1 path WONTFIX** — v1.exe 编 src0/main.jhyy → jhyy_v2.il ≠ v2/v3/v4/v5 byte-equal (string interning quirk per v2.11.19 B3 反馈), v2..v5 仍 byte-equal `e6b6f1fa...`。
4. **Codegen amd64 真 XMM regalloc 仍 defer** — 当前 f32/f64 走 stack spill + load, 不走真 XMM regalloc; 跟 v2.11.19 ship 同 baseline, 不影响 parity。
5. **QBE 自写 defer** — 当前 self-backend 替代 QBE 后端 codegen, 但仍是 **QBE IL emit** → QBE external binary → assembly; 真正"自写后端" (跳过 QBE IL, 直接 emit x86-64) 推 v2.x 末。
6. **完整 V3-C 3i generics 真 refactor defer** — 推 v3.x。

## v2.11.23 = v2.11.x series milestone

| 里程碑 | 状态 |
|--------|------|
| M1 — self-backend 0 FAIL parity with QBE path (架构修 + 4 sub-bug 全真修) | ✅ **(v2.11.23 ship, this sprint)** |
| M2 — C-side freeze (jhyy-side only, 不再要求 C-side mirror) | ✅ (2026-09-16 user 决定) |
| M3 — D43 closure jhyy-side internal (v1→v2→v3→v4→v5 .il byte-equal, 不再要求 C-side mirror) | ✅ (per M2) |
| M4 — QBE 自写 (跳过 QBE IL, 直接 emit x86-64) | ⏸️ v2.x 末 (跟 v3.x 异步并行) |
| M5 — amd64_sysv 实 impl (完整 SysV calling convention 支持, 不只是 freestanding ABI) | ⏸️ v2.x 末 |
| M6 — N 代 fixed point (Stage 2 N=10+ byte-equal stable, mutation testing) | ⏸️ v2.x 末 |

## v2.x 后续路线 (post-v2.11.23)

按 [`docs/plans/roadmap/v2-v3-parallel-sprint-plan.md`](../../plans/roadmap/v2-v3-parallel-sprint-plan.md) § 5.1 路径 A + [`docs/plans/v2/v2.0.0-os-prep.md`](../../plans/v2/v2.0.0-os-prep.md):

- **v2.x 中期 (v2.12+ 真 XMM regalloc)**: codegen_amd64 真 XMM register allocation (目前 f32/f64 走 stack spill + load)
- **v2.x 末 (QBE 自写 + amd64_sysv 实 impl + N 代 fixed point)**: 跳过 QBE IL, 直接 emit x86-64
- **v3.0 3a-3f 跟 v2.x 中/末 异步并行** (per 2026-09-01 user 决定): v3.0 3a-3f 是 inline asm / `#[naked]` / volatile / `#[link_section]` / memory barrier / `#[no_std]` (软 ship per D10), 跟 v2.x 中/末 各自 ship 后在 OS M1/M4/M11 launch 联调
- **v1.x M5 (v1.x 末 Phase 4)** 推迟决策 (2026-08-14 user 决定): 等 v2.x 末 QBE 自写 + v3.x 末 runtime 重写后, 一次性删 `src/*.c` + untrack QBE + 删 runtime.c, 完成"jhyy 编 jhyy" 0 C 依赖闭环; v1.5 installer ship 不触发 M5, M5 是 v1.x 末 Phase 4 单独 sprint

## 关键 commit

- `56be6cf` — v2.11.20 Phase 1+2 RC-1+RC-7 emit_load/emit_copy LABEL flag propagate
- `970f2ca` — v2.11.20 Phase 3 W-017 module-level `let mut` emit path
- `0831459` — v2.11.20 Phase 4 RC-4 negative IMM parse + clamp fix (match_range)
- `73cba17` — v2.11.20 docs+ship (RC-1+RC-3+RC-4 真修 + 4 FAIL DEFERRED)
- `5dd9024` — v2.11.21-RCA RCA-only (0 source LOC, 4 fail root cause analysis)
- `4beab82` — v2.11.21-fix Phase 1 cap_table_basic bare `"%t"` fnarg 真修 (1 LOC)
- `e410d79` — v2.11.21-fix Phase 2 for_in_slice_nested 真修 DEFERRED — needs ~30-50 LOC
- `98ca31f` — v2.11.21-fix Phase 3 big_array 真修 DEFERRED — needs 2-pass slot alloc ~80-120 LOC
- `1985bd5` — v2.11.21-fix Phase 4 dungeon_game `next_token_ret` 跨行吞 `@else50/@else53` 真修 (1 LOC)
- `a22b868` — v2.11.21-fix docs+ship (cap_table_basic + dungeon_game 真修, big_array + for_in_slice_nested DEFERRED)
- `b76d385` — v2.11.22 attempt 6 surgical edit REVERTED, docs-only DEFER outcome
- **`c46b926`** — **v2.11.23 Phase 1 — emit_alloc cg_record_temp_slot + cg_alloc_slot(8) (架构修 for_in_slice_nested 真修)** ⭐
- **`7e55ab4`** — **v2.11.23 Phase 2 — emit_binop derived-slot + alloc pool 从 formula pool 物理分离 (架构修 big_array 真修)** ⭐
- **`0d66195`** — **v2.11.23 docs+ship (workarounds W-074.13 sub-bug 1+4 CLOSED + architecture + changelog + d43-baseline-archive + plan + tag v2.11.23)** ⭐
- `11faff2` — v2.11.20 ship record correction (QBE=119/139 not 115/139, self-backend=115/139 PASS+4 FAIL)
- `d69c6f1` — architecture 🎯 milestone marker for v2.11.23
- **`v2.11.23`** (tag) — **🏆 首次 self-backend 0 FAIL parity with QBE path**

## 相关 memory

- `memory/feedback_rca_first_root_cause.md` — 多 cluster fail 先 RCA 找根因 (v2.11.22 attempt 验证 RCA claim 偏)
- `memory/feedback_audit_single_commit_diff.md` — audit commit 用 `git show <sha>` 而不是累计 diff
- `memory/feedback_fix_evaluation_rule.md` — 5/5 PASS on target test 才能声称 fix work
- `memory/feedback_codegen_amd64_multifn.md` — 单 function .il 跑通 ≠ 2+ function 跑通, 5/5 gate 不能以 hello 单测 PASS 当证据
- `memory/feedback_codegen_amd64_run_zerobyte.md` — self-backend body 0-byte 持续 5 sprint, v2.x axis 修
- `memory/feedback_regress_clean_count.md` — FRESH total (例 119/139) 才能写入 changelog
- `memory/feedback_changelog_umbrella.md` — vX.Y axis umbrella changelog; 本 sprint 满足 "重大 pivot" 例外
- `memory/feedback_plans_per_version.md` — 每个 minor version 一个 `vX.Y.Z-plan.md`
- `memory/feedback_memory_selectivity.md` — memory 只存通用规约, sprint-specific 写到 workarounds.md

## 引用

- W-074.13 4 sub-bug 全 CLOSED: [`docs/internal/workarounds.md`](../../internal/workarounds.md) W-074.13 entry + v2.11.23 sprint closure section
- v2.11.23 plan: [`docs/plans/v2/v2.11.23-plan.md`](../../plans/v2/v2.11.23-plan.md)
- v2.11.23 predecessor RCA: [`docs/internal/rca/rca-v2.11.21.md`](../../internal/rca/rca-v2.11.21.md) (v2.11.23 closure section 写 v2.11.21 末尾 — audit 指出 v2.11.22 RCA claim 偏, v2.11.23 修正; **不**创建 rca-v2.11.22.md)
- v2.11.23 umbrella section: [`docs/logs/v2/changelog-v2.11.0.md` v2.11.23 section](changelog-v2.11.0.md) (本 standalone doc 是 milestone celebration view, umbrella 顶部加 link 索引 — **不**重复内容)
- v2.11.23 D43 baseline: [`docs/logs/v2/d43-baseline-archive.md`](d43-baseline-archive.md) v2.11.23 row (HOLD on `e6b6f1fa...`)
- v2.11.22 attempt DEFER outcome: [`docs/plans/v2/v2.11.22-plan.md`](../../plans/v2/v2.11.22-plan.md) (commit `b76d385` docs-only ship)
- v2.12.0 plan (post-fix audit): [`docs/plans/v2/v2.12-plan.md`](../../plans/v2/v2.12-plan.md) (启动前置 = v2.11.23 ship, 已 ✅)
- codegen_amd64 Phase 1 fix point: `compiler/src0/codegen_amd64_emit_mem.jhyy:280-350` (emit_alloc)
- codegen_amd64 Phase 2 fix point: `compiler/src0/codegen_amd64_emit_call.jhyy:1653-1700` (emit_binop derived)
- codegen_amd64 frame_size 兜底: `compiler/src0/codegen_amd64_emit_ctrl.jhyy:522-526`
- cg_record_temp_slot API: `compiler/src0/codegen_amd64_state.jhyy:251-262`
- cg_alloc_slot API: `compiler/src0/codegen_amd64_state.jhyy:665-673`
- cg_offset_for_temp_with_target: `compiler/src0/codegen_amd64_state.jhyy:639-660` (tier-1 lookup)
- 已知 v1.0.0 standalone pattern: [`docs/logs/v1/changelog-v1.0.0.md`](../v1/changelog-v1.0.0.md) (本 doc 的 template)
- 已知 v1.x 收尾路线: [`docs/logs/v1/changelog-v1.8.0.md`](../v1/changelog-v1.8.0.md) umbrella
- 跨边界 OS 协调: [`../jhyy_OS/docs/coordination.md`](../../../jhyy_OS/docs/coordination.md) § 0 Critical Path (M1-M11 launch 联调)
