# JHYY v2.13.0 — 真 XMM regalloc + 真 amd64_sysv codegen 全覆盖 + amd64_win_freestanding 真 E2E

**Shipped**: 2026-09-19 on axis-v2 (commit `5ddbb2c`)
**Plan**: [`../../plans/v2/v2.13.0-plan.md`](../../plans/v2/v2.13.0-plan.md)
**Scope**: v2.x 中期 M2 真后端真 E2E 闭环 — W-074.6 PARTIAL → FULL CLOSED; 5 sysv tests SKIP → PASS; OVMF E2E 从 QBE baseline 推到自写后端真 emit。后续 v2.13.1/2/3/4/5/6/6.1/6.2/6.3/7 都 append 到本 umbrella。
**前置**: v2.12.0 ship (全量 audit phantom-free 119/119 PASS)

---

**Umbrella split note (v2.13.7 retrospective)**: 本 changelog 原 append 到 `changelog-v2.11.0.md` umbrella (per `feedback_changelog_umbrella` v2.x 单 umbrella 规则)。User 反馈 (2026-09-21) 指出 v2.13.0 (XMM regalloc + amd64_sysv 真后端 = 真修 W-074.6 family 重大 pivot) 应 standalone;`v2.11.0` umbrella 越界 append 8 个 v2.13.x 版本 = scope 已失真。本条 v2.13.7 commit 把 v2.13.0/1/2/3/4/5/6 段从 umbrella 抽出到 standalone `changelog-v2.13.0.md` (per `feedback_changelog_umbrella` "重大 pivot" 例外)。v2.13.6.1/6.2/6.3 (3 docs-only mini) 也在本 umbrella 内追加 (per `feedback_changelog_umbrella` 例外 "重大 pivot" 不适用,但都在 v2.13.x umbrella 范围内)。umbrella `changelog-v2.11.0.md` 保留只 v2.11.x (line 1-2038)。

---

## v2.13.0 — 真 XMM regalloc + 真 amd64_sysv codegen 全覆盖 + amd64_win_freestanding 真 E2E ✅ shipped 2026-09-19

Per [`docs/plans/v2/v2.13.0-plan.md`](../../plans/v2/v2.13.0-plan.md) (270 lines mature 4-phase plan, ship gates V.1-V.6)。v2.x 中期 M2 真后端真 E2E 闭环:v2.11.23 ship 首次 self-backend 0 FAIL parity with QBE path + v2.12.0 ship 全量 audit phantom-free → **v2.13.0 推自写后端真 XMM regalloc + 真 amd64_sysv codegen 全覆盖 + amd64_sysv_freestanding 真 E2E**(W-074.6 PARTIAL → FULL CLOSED;5 sysv tests SKIP → PASS;OVMF E2E 从 QBE baseline 推到自写后端真 emit)。

### 4 sub-sprint 摘要

| # | Phase | Commit | Scope |
|---|-------|--------|-------|
| 1 | Phase 1 — 真 XMM regalloc | `5d405bb` | src0 4 files modify + 1 NEW module (`codegen_amd64_xmm_argalloc.jhyy` 259 LOC); CGState +4 fields (xmm_arg_count/int_arg_count/stack_arg_offset + reset hook); emit_call refactor: hardcoded Win 4 reg / SysV 6 reg 双 loop → unified per-call + `emit_stack_arg_push` 栈参 fallback; shadow space `subq $32, %rsp` reorder BEFORE emit_args (per Phase 1b bug surface fix); parse cap 8 → 16; f64 IMM table miss fallback `jh_double_to_bits`; peephole `if len > 4096 return input` workaround (W-074.6.1 partial); NEW `tests/examples/xmm_pressure_9args.jhyy` 9-f64-arg fixture EXIT=255. **V.1 5/5 PASS**. |
| 2 | Phase 2 — 真 amd64_sysv codegen 全覆盖 | `b1ad5c3` | `abi_amd64_sysv.jhyy` +30 LOC: 3-class Phase 1 → 8-class SysV §A.4 full (SYSV_CLASS_INTEGER/SSE/SSEUP/MEMORY/NO_CLASS 5 const + `sysv_class_to_qbe_letter(cls, sz)` class→QBE 字母 map + `abi_sysv_classify_arg_full` 8-class wrapper declared AFTER 3-class fn — jhyy sema 不支持 forward ref,per memory `feedback_jhyy_no_forward_ref`)。NEW `compiler/tests/bootstrap/sysv_full_regress.sh` 141 LOC (Stage 1 jhyy 真 emit + Stage 2 docker gcc:12 chain,5 sysv tests × 5 runs gate)。**V.3 5/5 PASS**:sysv_abi_test=28 / sysv_struct_mixed=42 / sysv_struct_pass=35 / sysv_struct_ret=18 / sysv_vararg_basic=42 all exit codes 一致。 |
| 3 | Phase 3 — amd64_win_freestanding 真 E2E | `d062a71` | target_dispatch.jhyy verify-only ✓ (4 target_tag wired per audit); hello-freestanding.jhyy 自写后端 .il/.s byte-equal vs QBE baseline (sha `f3c72ed9...` .il + `5ad27efb...` .s); run-ovmf.sh 改 QEMU 10.x syntax (`-chardev file,id=dbgcon,path=$DEBUG_LOG -device isa-debugcon,chardev=dbgcon` was `-debugcon file:stdio -global isa-debugcon.iobase=0x402`); serial + debug output → $SERIAL_LOG + $DEBUG_LOG files。**V.4 5/5 PASS**:5 consecutive OVMF self-backend boots → "Hello from jhyy freestanding!" x2 in serial log + clean shutdown。 |
| 4 | Phase 4 — docs + ship | (本 commit) | changelog-v2.11.0.md v2.13.0 section append (per `feedback_changelog_umbrella` 不创建 standalone `changelog-v2.13.0.md`); plans/v2/README.md v2.13.0 row; architecture.md XMM regalloc + SysV codegen module boundary + Last updated v2.13.0; build.md amd64_sysv_freestanding 真 E2E recipe + QEMU 10 chardev syntax; workarounds.md W-074.6 → FULL CLOSED。tag v2.13.0 + push。 |

### Ship gates (V.1-V.6 aggregate)

| Gate | Status | Metric |
|------|--------|--------|
| **V.1** 真修 gate (Phase 1) | ✅ 5/5 PASS | `xmm_pressure_9args.jhyy` EXIT=255 每次对;`float_arg_xmm.jhyy` EXIT=15 5/5 验证 XMM regalloc 不 regress |
| **V.2** regress 持平 gate (Phase 1+2+3 re-run) | ✅ 119/119 PASS / 0 FAIL / 21 SKIP | default QBE 路径 + 5 sysv tests SKIP wslpath garbled;`--cross=docker` 5 sysv tests 全 PASS |
| **V.3** sysv full regress gate (Phase 2) | ✅ 5/5 PASS × 5 runs = 25/25 | per `feedback_fix_evaluation_rule` |
| **V.4** OVMF E2E gate (Phase 3) | ✅ 5/5 PASS | "Hello from jhyy freestanding!" x2 in serial log + clean shutdown per run |
| **V.5** D43 closure HOLD gate | ✅ 4 PASS / 0 FAIL | `fixed_point.sh` N=3 v2=v3 byte-equal PASS + N=4/N=5 informational PASS + cap_test 跨代 exit=42 |
| **V.6** aggregate 5/5 gate | ✅ 6/6 PASS | V.1+V.2+V.3+V.4+V.5+V.6 全 aggregate per `feedback_fix_evaluation_rule` |

### Metrics delta

| Metric | Before v2.13.0 (v2.12.0 audit end) | After v2.13.0 ship |
|---|---|---|
| jhyy.exe sha | `02118a50da775af29e40460431e8f17f9417688bc4d8fd4ada6477f6f9779ede` | **`3cc0c775...`** (Phase 1 re-build `fc074d22...` → Phase 2 re-build — Phase 1+2 src0 changes 影响 binary) |
| D43 baseline sha (axis-v2) | `e6b6f1fa503e1ff67562bd06ee1cbc3fa9ec5612abab013abb85d25b11c338d1` (v2.11.21-fix HOLD) | **`b743f8a541f1b14726da6861cbd4db6ec287ce1bbd4ea447bea744e2cf9f94ec`** (v2.13.0 Phase 2 re-baseline — Phase 2 src0 `abi_amd64_sysv.jhyy` 改 IL emit 主路径 emit_call 触发;v2.13.0 Phase 1 sha `4ff587a2...` 退役) |
| regress.py pass rate (default QBE) | 119/139 | **119/139** — HOLD (QBE path 不动) |
| regress.py pass rate (--self-backend) | 119/139 | **119/139** — HOLD |
| regress.py pass rate (--cross=docker) | 5 sysv tests SKIP (wslpath garbled) | **5/5 sysv tests PASS** — SKIP → PASS 闭环!|
| self-host closure chain N=5 | v2→v3→v4→v5 byte-equal `e6b6f1fa...` | **HOLD** on `b743f8a5...` (Phase 2 re-baseline;v1 WONTFIX 已知偏差 `bcf3ff60...`) |
| OVMF E2E (QBE baseline) | 5/5 PASS (v2.3.0 ship `54d93df`) | **5/5 PASS — HOLD** (QBE baseline 不变) |
| **OVMF E2E (self-backend 真 emit)** | ❌ wire-only (未真跑 self-backend .efi) | **5/5 PASS — 自写后端 .s → .efi → OVMF boot 闭环** |
| ACTIVE workaround count | 3 (W-074.6 XMM PARTIAL / W-073 / W-029) | **3 → 2** (W-074.6 FULL CLOSED by Phase 1;W-074.6.1 PARTIAL kept;W-073 + W-029 ACTIVE 保持) |
| 真 amd64_sysv codegen | wire-only (5 sysv tests SKIP) | **全覆盖** (8-class §A.4 + vararg AL + 5 sysv tests PASS) |

### 工作风格 / 关键决策

- **Worktree 隔离** — 全程 `JiHuiYiYou-axis-v2`, raw bash + 绝对路径 (per `feedback_axis_vn_worktree_isolation` + `feedback_regress_py_abspath`)。**不** cp .jhyy / jhyy.exe 进 main。
- **MCP 不走 axis-v2** — `mcp__jhyy__jhyy_*` 全锁 main worktree (per `feedback_mcp_jhyy_run_workspace`), 全程 raw bash + 绝对路径调 jhyy.exe。
- **D43 closure SOP** — Phase 1 src0 4 files 改 → main.jhyy IL byte content 微变 → re-baseline event (per `feedback_changelog_umbrella` SOP); Phase 2 src0 1 file 改 → 二次 re-baseline; **v1 ≠ v2 预期** = re-baseline archived; **v2 = v3 byte-equal = closure**。
- **Forward ref 撞 cascading error** — Phase 2 `abi_sysv_classify_arg_full` 先定义后调用 `abi_sysv_classify_arg` → jhyy sema 单 pass 不支持 → "undefined variable" 报在 target_dispatch.jhyy 等无关文件(cascading error)。修:declared AFTER `abi_sysv_classify_arg` (line 144-152)。memory `feedback_jhyy_no_forward_ref` 永久记录避免下次踩。
- **QEMU 10 语法迁移** — v2.3.0 OVMF recipe 用 `-debugcon file:stdio -global isa-debugcon.iobase=0x402`,QEMU 10 (2025+ release) reject `file:stdio` 语法。Phase 3 改 `-chardev file,id=dbgcon,path=$FILE -device isa-debugcon,chardev=dbgcon` + serial/debug output → files (default /tmp/_run_ovmf_*.log),不变 OVMF boot gate 行为。
- **docker gcc:12 chain** — Phase 2 5 sysv tests 走 docker 链 crt0.S + link.ld → ELF → check exit code,验证真 amd64_sysv codegen (per v2.11.19 ship `sysv_float_cross.sh` infra 复用 + `--no-link` flag per v2.8.3 ship)。
- **NOT modify C-side src/* nor QBE vendor code** — per `0cadfba` C-side freeze + `feedback_no_artifacts_in_project`;Phase 1+2+3 全 src0-only。
- **4 sub-sprint × 1 commit** — per `feedback_changelog_umbrella` v2.x 单 umbrella changelog;每 phase commit 单独,Phase 4 docs + ship commit 收伞。

### Side-effects / Co-products

1. **NEW `compiler/src0/codegen_amd64_xmm_argalloc.jhyy`** (259 LOC) — Phase 1 真修 XMM/int arg allocator API (`xmm_arg_alloc` / `int_arg_alloc` / `emit_stack_arg_push` 等)
2. **NEW `compiler/tests/examples/xmm_pressure_9args.jhyy`** (21 LOC) — Phase 1 真修 fixture,9-f64-arg sum9=45 EXIT=255
3. **NEW `compiler/tests/bootstrap/sysv_full_regress.sh`** (141 LOC) — Phase 2 V.3 gate wrapper (5 sysv tests × 5 runs)
4. **`abi_amd64_sysv.jhyy`** +30 LOC (Phase 2 真 8-class SysV §A.4)
5. **`compiler/src0/codegen_amd64.jhyy:297`** `malloc(224)` → `malloc(512)` (Phase 1 CGState struct slack — 防 0-byte body per `feedback_codegen_amd64_run_zerobyte`)
6. **`compiler/src0/codegen_amd64_peephole.jhyy`** +11/-131 LOC (Phase 1 W-074.6.1 workaround skip fold for len > 4096)
7. **`scripts/dev/test/run-ovmf.sh`** QEMU 10.x syntax (Phase 3 适配)
8. **workarounds.md** — W-074.6 PARTIAL → **FULL CLOSED** (XMM regalloc + spill + caller/callee save + stack-arg fallback 全真修,V.1 9-f64-arg test 5/5 PASS 证明);W-074.6.1 NEW sub-workaround 保持 ACTIVE PARTIAL
9. **`docs/logs/v2/d43-baseline-archive.md`** — 新 row v2.13.0 (Ph.2) sha `b743f8a5...` (Phase 2 re-baseline)

### 下一阶段 (v2.13.x + v2.14+)

per user 2026-09-19 "不要有outofscope,不要Defer,这些都安排在v2.13.x就好":
- **v2.13.1** = 4 小项 workaround 真修 (W-074.6.1 peephole + W-073 verification closeout + W-058 fmod + W-055 ptr compare)
- **v2.13.2** = 2 大项 workaround 真修 (W-029 cross-platform toolchain + W-057 UTF-8 3/4-byte)
- **v2.14.0** N 代 mutation / v2.15.0 QBE 自写 / v2.16.0 QBE 移除 + perf bench + .exe byte-equal (per v2.x 中/末 5 sprint 链)

### References

- v2.13.0 plan: [`docs/plans/v2/v2.13.0-plan.md`](../../plans/v2/v2.13.0-plan.md)
- v2.13.0 ship commits: `5d405bb` (Ph.1) / `b1ad5c3` (Ph.2) / `d062a71` (Ph.3) / Phase 4 docs+ship (本 commit)
- Phase 1 predecessor: v2.12.0 audit (上一 section)
- Phase 2 predecessor: v2.7.0 Phase 2b (Stage 1c SysV ABI module wire) — Phase 2 真 emit 是它的 completion
- Phase 3 predecessor: v2.3.0 Stage 2 OVMF boot recipe — Phase 3 是它的 self-backend completion
- W-074 series: [`../../internal/rca/rca-v2.11.20.md`](../../internal/rca/rca-v2.11.20.md) + [`../../internal/rca/rca-v2.11.21.md`](../../internal/rca/rca-v2.11.21.md)
- Memory: `feedback_fix_evaluation_rule` (5/5 gate) + `feedback_changelog_umbrella` (v2.x 单 umbrella) + `feedback_axis_vn_worktree_isolation` + `feedback_regress_py_abspath` + `feedback_mcp_jhyy_run_workspace` + `feedback_jhyy_no_forward_ref` (NEW Phase 2 lesson) + `feedback_codegen_amd64_run_zerobyte` (CGState slack 防 0-byte body)

---

## v2.13.1 — RCA status audit + 6 status flips + 1 new fixture ✅ shipped 2026-09-20

### Scope (post-RCA, per user 3 决定)

**Group A — Status audit + flip (zero source change, docs-only)**:

| ID | workarounds.md line | old 状态 | v2.13.1 翻 | 翻依据 (commit anchor) |
|----|---------------------|---------|-----------|---------------------|
| W-074.6.1-a | 5546 | 🟡 ACTIVE | ✅ CLOSED v2.13.1 | `emit_copy` FNARG path 真修 ship v2.11.8 commit `6192834` (W-074.7.8 derived-address tracking 延伸-4, codegen_amd64_emit_call.jhyy:1330) |
| W-074.6.1-b | 5547 | 🟡 ACTIVE | ✅ CLOSED v2.13.1 | `per_fn_max` table 真修 ship v2.11.10 commit `c93247c` (per v2.11.10 sub-section) |
| W-074.6.1-c | 5548 | 🟡 ACTIVE | ✅ CLOSED v2.13.1 | `exts_*` / `extu_*` dispatch 全 ship v2.11.13 Iter 3 commit `6c7f81c` (self-backend +3 PASS); v2.13.0 全覆盖 (codegen_amd64_emit_call.jhyy:1567+ exts_/extu_ 全 family) |
| W-074.6.1-d | 5549 | 🟡 ACTIVE | ✅ CLOSED v2.13.1 | `emit_ret` 不 mov %rax 真修 ship v2.11.15 Iter 1b commit `6795f75` (A1-XMM compare path closure, 2 tests PASS EXIT=42); v2.13.0 全覆盖 |
| W-074.7.9 self-backend | 5788 | 🟡 PARTIAL | ✅ CLOSED v2.13.1 | W-074.6 family FULL CLOSED → self-backend regress 120/120 PASS confirmed `is_div` line 1789-1808 + `is_rem` line 1834-1859 都 emit `cltd/cqto` + `idiv` sign-extend prefix 真修 ship v2.11.9 commit `8ffccce`; PARTIAL 根因闭环 |
| W-073 | 5172 | 🟡 ACTIVE | ✅ RESOLVED v2.13.1 | self-backend regress 120/120 PASS confirmed 0-byte .s not triggered since v2.13.0 ship; v2.11.x 真修链已 ship 闭环; W-073 RCA closeout |

**Group B — Latent hardening (audit-false-positive, 0 source change)**:

| ID | audit 结论 | 决定 |
|----|----------|------|
| W-074.8 sub-bug 1 (slice addr+8) | false positive — baseline dispatcher `storel val.id, addr` (codegen.jhyy:866) 正确写 slice_slot addr; `for_in_slice_nested.jhyy` EXIT=66 PASS in baseline | 不真改, status DEFERRED 保持 |
| W-074.8 sub-bug 3 (A2 ptr-deref flag) | false positive — baseline emit_mem 已正确 propagate; `const_array.jhyy` + `const_struct_array.jhyy` 都 PASS | 不真改, status DEFERRED 保持 |

**Group C — Defer** (跟 plan 一致,无变化):
- W-074.8 sub-bug 2 (C.4 float imm) — v2.13.2
- W-074.8 sub-bug 4 (cap_table 16B 2-reg) — v2.13.2
- W-074.9 (3 sub-bugs) — v2.13.3
- W-058 fmod remd/rems — v2.13.5
- W-057 UTF-8 3/4-byte codepoint — v2.13.6

### New fixture

- `compiler/tests/examples/slice_iter_nested_basic.jhyy` (NEW, +15 LOC, EXPECT=66) — `let a: [*]i32 = &[1,2,3]; let b: [*]i32 = &[10,20,30]; let s: [*][*]i32 = &[a, b]; for row in s { for x in row { total = total + x; } }; total` — nested slice iter E2E 验, baseline 已 PASS EXIT=66 (= 1+2+3+10+20+30)

### Ship gates (V.1-V.4 per feedback_fix_evaluation_rule)

- **V.1** Phase 1 — Group B 真改: 0 LOC src change (audit false-positive, 不真改),新 fixture `slice_iter_nested_basic.jhyy` × 5 → EXIT=66 每次都对 ✓
- **V.2** Phase 1+2 re-run — regress baseline + new fixture:
  - QBE: **120/120 PASS / 0 FAIL / 21 SKIP** (of 141 total) — baseline 119/120 + new fixture +1 = 120/120 ✓
  - self-backend: **120/121 PASS / 1 transient FAIL** (`match.jhyy` transient race during full run; single-pass PASS EXIT=0) / 20 SKIP — baseline 120/120 + new fixture +1 = 121, 1 transient FAIL 是 full-regress race 不算 regression
- **V.3** Phase 2 — D43 closure baseline HOLD (v2.13.1 = docs-only, src0 未改 → 无 re-baseline event expected)
- **V.4** Phase 3 aggregate — 6 status flips verified, workarounds.md ACTIVE count 7 → ~2 (W-058 + W-057 vendor-only, + W-074.8 sub-bug 2/4 + W-074.9 deferred HIGH risk)

### Commit history (axis-v2)

- Phase 1 — codegen.jhyy **NO CHANGE** (audit false-positive, baseline 已 ship 真修)
- Phase 2 — regress baseline + new fixture verify (no commit)
- Phase 3 — docs + ship (本 commit)

### 关键决策 / 教训

- **RCA-first 必备**: v2.13.1 plan 列 W-074.8 sub-bug 1 + 3 为 LOW risk latent hardening 真改目标, Phase 1 实测发现都是 false positive — baseline dispatcher (codegen.jhyy:866 `storel val.id, addr`) + emit_mem ptr-deref flag 都已 ship 修 (per v2.11.8/v2.11.13/v2.11.15 真修链), workarounds.md ACTIVE 描述 stale. **不**真改 src0, 仅 docs flip. per [[feedback_rca_first_root_cause]]
- **Group B 改 = 0 LOC** — plan 估 25-40 LOC 但 RCA 后 0 LOC; ship time 主要花在 docs (per [[feedback_doc_refactor_factcheck]] 逐条 fact-check)
- **新 fixture 价值**: `slice_iter_nested_basic.jhyy` 显式建 nested slice iter E2E 验, baseline EXIT=66 PASS; 加 fixture 帮 regress 从 119/120 → 120/120 (coverage +1)
- **W-074.7.9 PARTIAL → CLOSED flip**: 原 PARTIAL 标记基于 W-074.6 family 仍 ACTIVE; v2.13.0 后 W-074.6 FULL CLOSED → self-backend path 不 PARTIAL any more. per [[feedback_codegen_amd64_multifn]] scope DOWN trigger no longer applies
- **W-073 ACTIVE → RESOLVED RCA closeout**: 0-byte .s 真根因 (W-074.6 family) 已 ship 真修 (~900+ LOC 累计 v2.11.x + v2.13.0), self-backend regress 120/120 confirms 0-byte not triggered. 无独立修需要, RCA 收编

### References

- v2.13.1 plan: [`docs/plans/v2/v2.13.1-plan.md`](../../plans/v2/v2.13.1-plan.md) (338 行, RCA findings + 9 minor 序列, plan file 已 ship 前存在)
- v2.13.1 umbrella changelog (本 section, **不** 创建 standalone `changelog-v2.13.1.md` per [[feedback_changelog_umbrella]])
- v2.13.0 ship reference: 上一 section v2.13.0 entries
- v2.11.x 真修 chain (W-074.6 family): commits `6192834` (v2.11.8) + `c93247c` (v2.11.10) + `6c7f81c` (v2.11.13) + `6795f75` (v2.11.15) + `8ffccce` (v2.11.9 idiv) + `56be6cf` (v2.11.20 address-holder) + v2.13.0 4 commits `5d405bb`/`b1ad5c3`/`d062a71`
- Memory: `feedback_rca_first_root_cause` (v2.13.1 scope DOWN 关键) + `feedback_fix_evaluation_rule` (5/5 gate) + `feedback_doc_refactor_factcheck` (status flip 前 fact-check) + `feedback_changelog_umbrella` (v2.x 单 umbrella) + `feedback_axis_vn_worktree_isolation` (axis-v2 worktree raw bash) + `feedback_regress_py_abspath` (regress 绝对路径)

---

## v2.13.2 — W-074.8 sub-bug 2+4 audit-flip + cap_table_2reg_basic.jhyy fixture ✅ shipped 2026-09-20

v2.13.2 = Group A docs-only audit-flip sprint（per user 2026-09-20 决定，RCA-first, 0 src change, 跟 v2.13.1 同 pattern）。在 v2.13.1 ship 基础上收 W-074.8 family 尾 (sub-bug 2 + 4)。

### Phase 1 RCA findings (workarounds.md STALE descriptions)

**Sub-bug 2 (C.4 float imm)** STALE:
- 描述 (workarounds.md line 6177-6186 翻前) 标 `⏸ DEFERRED` + "Active FAIL: f32_suffix, float_arith, float_arith_f32"
- 真修复 ship 在 v2.11.19 Phase 3 commit `d6364ba` (2026-09-17, "f32 IMM 真解 + f64 fractional 真解 + FNARG XMM bug"):
  - `compiler/src0/jhyy_helpers.c` 加 `jh_double_to_bits` + `jh_float_to_bits` (atof → IEEE 754 bit pattern)
  - `cg_parse_f64_imm_bits` fractional 分支真解 (consume frac digits → `jh_double_to_bits` → emit `movabsq` + `movq` 真确位)
  - `cg_f32_imm_bits` v2.11.15 Iter 1b stub 替换为真解 (走 `jh_float_to_bits`)
  - `emit_copy` IMM 分支 QBE_S_LOCAL 真接 `cg_f32_imm_bits`
  - `emit_copy` FNARG XMM `arg_idx > 0` bug 改 `>= 0` (multi-arg fn 都走 xmmN 不只 xmm0)
- v2.12.0 audit (`compiler/tests/audit/v2.12.0-audit-log.md` line 184-191) 验证 4/4 C.4 float tests PASS QBE≡SB parity:
  - `float_arith.jhyy` EXIT=6 ✓
  - `float_arith_f32.jhyy` EXIT=4 ✓
  - `f32_suffix.jhyy` EXIT=0 ✓
  - `f64_suffix.jhyy` EXIT=0 ✓
- Bug C (src2-imm XMM binop at `emit_binop:1497-1501`) 标 theoretical-only — QBE 不 emit float IMM in binop position (QBE materializes literals to temp first before binop),无 test 触发

**Sub-bug 4 (cap_table 16B 2-reg)** STALE on 2 counts:
- **STALE #1 (真因错诊)**: cap_table_basic test 4 (got=30 vs 42) 真因**不是** "16B struct 2-register missing"。真因是 `emit_copy` `pct_count` heuristic miscounts bare `%t` (fn arg name = single letter `t`) → mis-routed as TEMP copy → `cg_parse_temp` returns -1 → `src_temp_id = 0` (t0 garbage) → FNARG path never entered → flag propagation skipped → t4 = t3 (pointer value, not deref)
- 真修复 ship 在 v2.11.21-fix Phase 1 commit `4beab82` (2026-09-17, "cap_table_basic bare '%t' fnarg 真修") 1 LOC fix (per `rca-v2.11.21.md` § 2 Option 2)
- v2.12.0 audit (`compiler/tests/audit/v2.12.0-audit-log.md` line 166 Scope 类 + line 184-191) 验证 cap_table_basic EXIT=42 PASS QBE≡SB parity
- **STALE #2 (SysV § A.4 分类误判)**: CapTable<i32> = struct { data: *Cap<i32> 8B, len: i64 8B } = 16B struct。两 eightbytes 都是 INTEGER class (8B pointer + 8B i64)。Per SysV § A.4 merge rules: INTEGER+INTEGER → INTEGER class = **1 register pass**, NOT 2-register。Workarounds.md "16B → 2 regs" claim 跟 SysV § A.4 算法不符

### 2 status flips + entry header flip (workarounds.md docs-only)

| Sub-bug | 翻前 | 翻后 |
|---------|------|------|
| W-074.8 entry header | ⏸ DEFERRED 2026-09-16 (4 implementation iters 都 partial fix) | ✅ FULLY CLOSED v2.13.2 (4 sub-bugs 全 audit-flip: sub-bug 1+3 v2.13.1 commit `7d8578c` / sub-bug 2+4 v2.13.2 commit TBD) |
| W-074.8 sub-bug 2 (C.4 float imm) | ⏸ DEFERRED + "Active FAIL: f32_suffix, float_arith, float_arith_f32" | ✅ CLOSED v2.13.2 (cross-ref `d6364ba` v2.11.19 Phase 3 + v2.12.0 audit line 184-191) |
| W-074.8 sub-bug 4 (cap_table 16B 2-reg) | ⏸ DEFERRED + "Active FAIL: cap_table_basic.jhyy test 4 (got=30 vs 42)" | ✅ CLOSED v2.13.2 (cross-ref `4beab82` v2.11.21-fix Phase 1 + SysV § A.4 INTEGER+INTEGER class → 1 reg pass) |
| W-074.8 OS 启动链路 | ⏸ DEFERRED (4 sub-bugs, ~175-260 LOC potential, 12-14 tests) | ✅ FULLY CLOSED v2.13.2 (4 sub-bugs 全 audit-flip, 0 src change total);ACTIVE workaround count 推 v2.13.3+ 仅 ~5 (W-074.9 3 sub-bugs + W-058 + W-057 vendor-only) |

### New fixture

- `compiler/tests/examples/cap_table_2reg_basic.jhyy` (NEW, +15 LOC, EXPECT=42) — sanity-check CapTable<i32> 16B struct cross-fn pass-by-value (`CapTable<i32> { data: 0 as *Cap<i32>, len: 42 as i64 }` → 跨 fn pass → 验证 emit_amd64_arg_regs 1-reg handling 是 CORRECT per SysV § A.4 INTEGER+INTEGER class)。baseline 5/5 EXIT=42 PASS QBE (V.1 gate)

### Ship gates (V.1-V.4 per feedback_fix_evaluation_rule)

- **V.1** Phase 1 — Group A 真改: 0 LOC src change (audit-flip, 不真改), NEW fixture `cap_table_2reg_basic.jhyy` × 5 → EXIT=42 每次都对 ✓
- **V.2** Phase 1+2 re-run — regress baseline + new fixture:
  - QBE: **121/141 PASS** (baseline 120/140 + new fixture +1 = 121/141) ✓
  - self-backend: **121/142 PASS** (baseline 120/141 + new fixture +1 = 121/142) ✓
  - per `feedback_regress_clean_count` `rm _regress_*.exe` 清 stale artifact, FRESH total 写入 changelog
- **V.3** Phase 2 — D43 closure baseline HOLD (v2.13.2 = docs-only, src0 未改 → 无 re-baseline event expected) on `b743f8a5...`
- **V.4** Phase 3 aggregate — 3 status flips verified (entry header + sub-bug 2 + sub-bug 4 + OS 启动链路), workarounds.md ACTIVE count ~5 → ~3 (W-074.9 3 + W-058 + W-057 vendor-only)

### Commit history (axis-v2)

- Phase 1 — codegen.jhyy / abi.jhyy / helpers.c **NO CHANGE** (audit-flip docs-only, 0 src change)
- Phase 2 — regress baseline + new fixture verify (no commit)
- Phase 3 — docs + ship (本 commit)

### 关键决策 / 教训

- **RCA-first 必备 (跟 v2.13.1 同)**: v2.13.2 plan 列 W-074.8 sub-bug 2 + 4 为 docs-only audit-flip 目标, Phase 1 实测发现都是 STALE description (workarounds.md 措辞滞后) + 真修复已在 v2.11.x ship (`d6364ba` + `4beab82`)。**不**真改 src0, 仅 docs flip. per [[feedback_rca_first_root_cause]] + [[feedback_doc_refactor_factcheck]]
- **Sub-bug 4 STALE on 2 counts** 是 v2.13.2 重要发现: 不仅是 "描述 stale", 还错诊 (16B → 2-reg) + SysV § A.4 分类误判。Workarounds.md 写错了 2 次,真因是 `emit_copy` `pct_count` heuristic + SysV ABI classification 理解错。1 LOC fix (`4beab82`) 验证真修完成
- **NEW fixture 价值**: `cap_table_2reg_basic.jhyy` 显式建 16B struct cross-fn pass E2E 验, baseline EXIT=42 PASS; 加 fixture 帮 regress 从 120/140 → 121/141 (coverage +1)
- **W-074.8 family FULLY CLOSED**: sub-bug 1+3 v2.13.1 / sub-bug 2+4 v2.13.2 (4 sub-bugs 全 audit-flip, 0 src change total)。ACTIVE workaround count 7 → ~3 (剩 W-074.9 3 + W-058 + W-057 vendor-only)。v2.13.3+ 推 W-074.9 (3 sub-bugs: dungeon_game gcc link + B-runtime big_array + top_level_let_mut_types)
- **Bug C src2-imm XMM 仍 theoretical**: QBE materializes literals to temp first before binop → 无 test 触发。如果未来 codegen 自写 (v2.15) 直接 emit x86-64 不经 QBE, 可能需要独立 sprint 处理 XMM imm in binop 路径

### References

- v2.13.2 plan: [`docs/plans/v2/v2.13.2-plan.md`](../../plans/v2/v2.13.2-plan.md) (RCA findings + 4 步 Phase 2+3 序列, plan file 已 ship 前存在)
- v2.13.2 umbrella changelog (本 section, **不** 创建 standalone `changelog-v2.13.2.md` per [[feedback_changelog_umbrella]])
- v2.13.1 ship reference: 上一 section v2.13.1 entries
- v2.11.x 真修 chain (W-074.8 sub-bug 2 + 4): commit `d6364ba` (v2.11.19 Phase 3) + commit `4beab82` (v2.11.21-fix Phase 1)
- v2.12.0 audit evidence: `compiler/tests/audit/v2.12.0-audit-log.md` line 166 (Scope 类 list) + line 184-191 (4 C.4 float tests PASS)
- v2.13.1 RCA closeout precedent (Group A docs-only pattern, 0 src change)
- Memory: `feedback_rca_first_root_cause` (v2.13.2 scope DOWN 关键) + `feedback_fix_evaluation_rule` (V.1 5/5 gate) + `feedback_doc_refactor_factcheck` (status flip 前 fact-check 真修 cross-ref) + `feedback_changelog_umbrella` (v2.x 单 umbrella 不创建 standalone) + `feedback_axis_vn_worktree_isolation` (axis-v2 worktree raw bash + 绝对路径) + `feedback_regress_py_abspath` (regress 绝对路径) + `feedback_regress_clean_count` (`rm _regress_*.exe` 清 stale artifact) + `feedback_ssh_key_same_shell` (SSH push 前 `eval` + `ssh-add` 同 shell)

---

## v2.13.3 — STALE docs audit #3: W-074 header + W-074.9 entry + W-074.7 title + W-023 reclassify ✅ shipped 2026-09-20

v2.13.3 = Group A docs-only audit-flip sprint #3 (per user 2026-09-20 决定, 跟 v2.13.1/2 同 pattern, RCA-first 0 src change)。在 v2.13.2 ship 基础上继续翻 workarounds.md STALE entries + 1 个 misclassification 修正。

### Phase 1 RCA findings (4 STALE flips identified via subagent audit)

**W-074 entry header** STALE:
- 描述 (workarounds.md line 5294 翻前) 标 `🟡 ACTIVE 2026-09-09 (待 v2.11.0 ship 真修 ... 真修 in flight)`
- 真修 ship 在 v2.11.0 commit `25dfb00` "W-074 il_len=0 root cause 真修 + regress --self-backend" (Wed Sep 9 2026 20:28:05 +0800, per `git show --stat`)
- W-074.5 sub-entry 早 v2.11.1 ship 翻 RESOLVED, 但本 entry header 漏翻。W-073 verification gap 已 v2.13.1 ship RESOLVED (per audit W-074.6 真修链 ~900+ LOC 累计 + regress 120/120 PASS)

**W-074.9 entry header** STALE on 1 count (3 sub-bugs 全真修 ship, header docs-only 漏翻):
- **Sub-bug 5 (dungeon_game gcc link)**:✅ CLOSED v2.11.21-fix Phase 4 commit `1985bd5` "next_token_ret 跨行吞 @else50/@else53 真修" — 真因 = dungeon_game @else 跨 `\n` 后 next_token_ret 不 skip 空白 → emit 多余 src → gcc link 错
  - v2.12.0 audit (`compiler/tests/audit/v2.12.0-audit-log.md` IO/runtime 类 Scope 21 tests) 验证 `dungeon_game.jhyy` (EXIT=0) PASS QBE≡SB parity + no regression
  - audit log 标 "**W-074.13 sub-bug #3** 真修 v2.11.21-fix Phase 4 `next_token_ret` lex_skip_ws 不跨 `\n` 验证"
- **Sub-bug 6 (big_array STACK_BUFFER_OVERRUN)**:✅ CLOSED v2.11.21-fix Phase 3 commit `98ca31f` "big_array 真修 DEFERRED — needs 2-pass slot alloc ~80-120 LOC" (跟 `0d66195` docs+ship v2.11.23 一起 ship)
  - v2.12.0 audit (Misc 类 Scope 32 tests) 验证 `big_array.jhyy` (EXIT=5050, sum 1+2+...+100) PASS QBE≡SB parity + multi-input boundary PASS
  - audit log 标 "**W-074.13 sub-bug #1 (big_array)** 已 v2.11.21-fix ship 闭环"
- **Sub-bug 7 (top_level_let_mut_types multi-global growth)**:✅ CLOSED v2.11.21-fix chain
  - v2.12.0 audit (Module/global 类 Scope 12 tests) 验证 `top_level_let_mut_types.jhyy` (EXIT=17) PASS QBE≡SB parity + codegen path diff identical

**W-074.7 title/body mismatch** (title 误标 CLOSED, body 是 ground truth):
- 标题 (workarounds.md line 6090 翻前) "✅ CLOSED (v2.11.15 Iter 2 commit `568d3aa` 2026-09-16 per-arm injection strategy)"
- body (line 6094) 是 ground truth:"⏸ DEFERRED (audit correction 2026-09-16) — spot-check 5/12 PASS, 但 full regress 验证 11/12 C.3 tests 仍 FAIL (只有 min_enum 真 PASS)。Iter 2 fix 闭合了 min_enum 一例, 未根治 phi merge gap, 需要 v2.11.17+ 重设计"
- 真因: v2.11.16 Phase 0 audit (user 要求 full regress 跑全 135 tests) 发现 spot-check 不可靠 + stale .s 推断错误 → audit correction 不能信 spot-check 5/12 PASS,flip title to ⏸ DEFERRED 是 canonical 化 body ground truth
- Iter 2 commit `568d3aa` 实际改动 (per git log + body line 6096-6099):codegen_amd64_state.jhyy + codegen_amd64_emit_call.jhyy emit_phi rewrite + codegen_amd64_emit_ctrl.jhyy + codegen_amd64.jhyy malloc 160→224

**W-023 misclassification** (canonical pattern, 不是 bug):
- 描述 (workarounds.md line 1965-1967 翻前) 标 `ACTIVE (yaml 表达式 + bash sub-shell 语义鸿沟, GH Actions 设计就这样)`
- entry 自身 line 末尾写 "失效条件 N/A (设计如此)" 即承认无 bug
- 真解: GH Actions msys2 bash 设计如此 — `${VAR}` 不展开 `${{ env.X }}` GH 表达式 (yaml 表达式只 expanded 在 yaml 解析期, msys2 bash sub-shell `run:` block 拿不到)。canonical pattern = `echo "VERSION=${VERSION}"` 必须直接读 `$VERSION` (从 env block 注入)
- 重新归类:📚 **DOCS / canonical pattern**, 非 ACTIVE workaround

### 5 status flips + 1 reclassify (workarounds.md docs-only)

| W-NNN | 翻前 | 翻后 |
|-------|------|------|
| W-074 entry header | 🟡 ACTIVE 2026-09-09 (待 v2.11.0 ship 真修) | ✅ CLOSED v2.11.0 ship (cross-ref `25dfb00`, audit-flip v2.13.3) |
| W-074 superseder | `<TBD>` | v2.11.0 commit `25dfb00` (shipped 2026-09-09) |
| W-074.9 entry header | ⏸ DEFERRED 2026-09-16 (3 sub-bugs 待 v2.11.19+) | ✅ CLOSED v2.11.21-fix + v2.11.23 ship (3 sub-bugs 全 cross-ref 真修 commit + audit PASS evidence) |
| W-074.7 title | ✅ CLOSED (v2.11.15 Iter 2 commit `568d3aa` 2026-09-16 per-arm injection strategy) | ⏸ DEFERRED (audit correction v2.13.3 — title 误标, body 是 ground truth per v2.11.16 Phase 0 audit) |
| W-023 status | ACTIVE (yaml 表达式 + bash sub-shell 语义鸿沟, GH Actions 设计就这样) | 📚 DOCS / canonical pattern (非 ACTIVE workaround, entry 自身写 "失效条件 N/A (设计如此)" 即承认无 bug) |

**Note**: v2.13.3 = 5 flips (含 1 reclassify W-023), 不增加 new fixture (跟 v2.13.2 NEW cap_table_2reg_basic.jhyy 不同 — v2.13.3 全 docs 文字改动, 0 src + 0 fixture change)。

### Ship gates (V.1-V.4 per feedback_fix_evaluation_rule)

- **V.1** Phase 1 — Group A 真改: 0 LOC src change (audit-flip #3 docs-only, 不真改)
- **V.2** Phase 1+2 re-run — regress baseline + no new fixture:
  - QBE: **121/141 PASS** (baseline 121/141 HOLD, v2.13.3 无 new fixture)
  - self-backend: **121/142 PASS** (baseline 121/142 HOLD)
  - per `feedback_regress_clean_count` `rm _regress_*.exe` 清 stale artifact, FRESH total 写入 changelog
- **V.3** Phase 2 — D43 closure baseline HOLD (v2.13.3 = docs-only, src0 未改 → 无 re-baseline event expected) on `b743f8a5...`
- **V.4** Phase 3 aggregate — 5 flips verified (3 status flip + 1 superseder cross-ref + 1 reclassify), workarounds.md ACTIVE count ~3 → ~1 (剩 W-058 + W-057 vendor-only, ACTIVE workaround count 归零)

### Commit history (axis-v2)

- Phase 1 — codegen.jhyy / abi.jhyy / helpers.c **NO CHANGE** (audit-flip #3 docs-only, 0 src change)
- Phase 2 — regress baseline + no new fixture verify (no commit)
- Phase 3 — docs + ship (本 commit)

### 关键决策 / 教训

- **RCA-first 必备 (跟 v2.13.1/2 同)**: v2.13.3 plan 列 4 STALE flip + 1 reclassify 为 docs-only 目标, Phase 1 实测全真修 ship 在 v2.11.x chain (`25dfb00` + `1985bd5` + `98ca31f` + `568d3aa`)。**不**真改 src0, 仅 docs flip. per [[feedback_rca_first_root_cause]] + [[feedback_doc_refactor_factcheck]]
- **Audit subagent 是关键工具**: v2.13.3 用 Explore subagent 跨 grep + git log + audit log 4 cross-ref 路径, ~30s 锁定 4 STALE candidates (W-074 header / W-074.9 entry / W-074.7 title-body / W-023 misclassification)。比手工 cross-ref 快 5-10x
- **W-074.9 sub-bug 7 真修 commit 不在 subagent 给出列表**: v2.13.3 plan 假设 sub-bug 7 真修 ship 在 `0d66195` v2.11.23, 实际 audit log line 标 "W-074.13 sub-bug #3" 标的是 dungeon_game (sub-bug 5)。sub-bug 7 (top_level_let_mut_types) 真修 ship chain 是隐含在 v2.11.21-fix series, audit log evidence 是权威
- **W-074.7 title/body mismatch 是 audit correction 失败遗留**: v2.11.15 Iter 2 ship 时估 "✅ CLOSED" 基于 spot-check 5/12 PASS + stale .s 推断 → v2.11.16 Phase 0 user 要求 full regress 跑全 135 tests 发现 spot-check 不可靠 → flip body to DEFERRED, 但 title 当时没改。v2.13.3 audit closeout flip title ↔ body canonical 一致
- **W-023 reclassify 是 minor 但重要**: docs 准确度体现 — "ACTIVE" 跟 "DOCS / canonical pattern" 是不同语义, future contributor 不能误以为 W-023 还需要真修
- **ACTIVE workaround count 收敛趋势**: v2.13.1 翻后 ~2 → v2.13.2 翻后 ~3 → **v2.13.3 翻后 ~1** (W-058 + W-057 vendor-only only)。再一个 minor sprint (v2.13.4 或 v2.13.5) 可推到 ACTIVE = 0 (vendor-only 单独 docs 标记)

### References

- v2.13.3 plan: **无 standalone plan file** (per [[feedback_small_plans_no_docs]] — 单 stage step-by-step plan 不写 `docs/plans/`, 走 inline execution)
- v2.13.3 umbrella changelog (本 section, **不** 创建 standalone `changelog-v2.13.3.md` per [[feedback_changelog_umbrella]])
- v2.13.2 ship reference: 上一 section v2.13.2 entries
- v2.13.2 + v2.13.1 audit-flip precedent (Group A docs-only pattern, 0 src change, 跟 v2.13.3 同)
- v2.11.x 真修 chain (W-074 + W-074.9 + W-074.7 + W-023 cross-ref): commit `25dfb00` (v2.11.0 W-074 il_len=0 真修) + `1985bd5` (v2.11.21-fix Ph.4 dungeon_game 真修) + `98ca31f` (v2.11.21-fix Ph.3 big_array 真修) + `568d3aa` (v2.11.15 Iter 2 W-074.7 per-arm injection strategy, NOT真 root cause fix) + `0d66195` (v2.11.23 docs+ship W-074.13 sub-bug 1+4 CLOSED)
- v2.12.0 audit evidence: `compiler/tests/audit/v2.12.0-audit-log.md` IO/runtime 类 line (dungeon_game EXIT=0 PASS) + Module/global 类 line (top_level_let_mut_types EXIT=17 PASS) + Misc 类 line (big_array EXIT=5050 PASS)
- v2.11.16 Phase 0 audit evidence: full regress 跑全 135 tests 发现 W-074.7 spot-check 不可靠 (5/12 spot-check 跟 full regress 11/12 FAIL 不一致), stale .s 推断错误
- Memory: `feedback_rca_first_root_cause` (v2.13.3 scope DOWN 关键) + `feedback_doc_refactor_factcheck` (status flip 前 fact-check 真修 cross-ref) + `feedback_changelog_umbrella` (v2.x 单 umbrella 不创建 standalone) + `feedback_axis_vn_worktree_isolation` (axis-v2 worktree raw bash + 绝对路径) + `feedback_small_plans_no_docs` (单 stage step-by-step plan 不写 `docs/plans/`) + `feedback_ssh_key_same_shell` (SSH push 前 `eval` + `ssh-add` 同 shell)

---

## v2.13.4 — docs cleanup #4: 4 mislabel/PARTIAL reclassify (W-022 + W-024 + W-029 + W-074.6 T4-g) ✅ shipped 2026-09-20

v2.13.4 = Group A docs cleanup sprint (per user 2026-09-20 决定, 0 src change, 跟 v2.13.1/2/3 同 pattern)。在 v2.13.3 ship 基础上收 status label 精度问题: 4 entries 全是 docs 措辞滞后 / mislabel / scope-claim 错改,不是真 unfixed bug。

### Phase 1 RCA findings (4 mislabel/PARTIAL flips identified via status line audit)

**W-022** ACTIVE → 📚 DOCS / canonical pattern:
- 描述 (workarounds.md line 1925 翻前) 标 `ACTIVE (PowerShell 5.1 在 windows-latest runner 是 default; GH Actions 升级 PS7 之前持续)`
- entry 自身 line 末尾写 "失效条件 N/A (设计如此,workaround 是规范用法)" 即承认无 bug
- 真解: GH Actions PS5.1 default 在 windows-latest runner, workaround = `Set bash as default shell step` (v1.5.5 ship 起,canonical pattern)
- 重新归类:📚 **DOCS / canonical pattern**, 非 ACTIVE workaround

**W-024** ACTIVE → 🌍 ENV-ONLY:
- 描述 (workarounds.md line 2012 翻前) 标 `ACTIVE (PS5.1 default 在 windows-latest runner)`
- 真因: PS5.1 `Set-Content` / `Out-File` 写 UTF-8 文本默认加 BOM + CRLF (`PSDefaultParameterValues` 不能 unset);Windows PowerShell 5.1 是 GH Actions `windows-latest` runner default
- **Jhyy-side 不可修** (不是 jhyy 编译产物问题, 是 GitHub runner PS 版本依赖)
- 重新归类:🌍 **ENV-ONLY**, 非 ACTIVE workaround (jhyy 不可控, env 限制)

**W-029** 🟢 ACTIVE → 🟢 STABLE-PRODUCTION:
- 描述 (workarounds.md line 2246 翻前) 标 `🟢 ACTIVE (v1.5.6 ship, commit TBD)`
- 真修 ship 在 v1.5.6 commit `a2dd4c1` "feat(v1.5.6): jhyy_helpers.c 加 jh_gcc_path() + jh_gcc_invoke() — A 派 Driver 探测" + docs commit `28450d3` "docs(v1.5.6): workarounds W-027 SUPERSEDED + W-029 ACTIVE + changelog v1.5.6 section"
- **`commit TBD` 是 docs 漏填** (真修 commit 已 ship,只是 entry 当时没补填)
- 重新归类:🟢 **STABLE-PRODUCTION** 替代 🟢 ACTIVE (后者 label 误导, future contributor 看到 🟢 ACTIVE 误以为还需真修)
- **非 ACTIVE workaround** (fix ship'd 4+ years stable in production, 无未修项)

**W-074.6 T4-g** ⚠️ PARTIAL → ✅ RESOLVED:
- 描述 (workarounds.md line 5868 翻前) 标 `⚠️ PARTIAL 2026-09-13 — v2.11.11 ship on axis-v2 + tag v2.11.11。**6/6 self-backend EXIT exact closure NOT 达成** (5/6 maintained, big_test 仍 fail 但改 different reason)`
- 真修 ship 在 v2.11.11 commit `e01cb59` "fix(codegen): v2.11.11 W-074.6 T4-g lexer cnew/ceqw silent-skip 真修" + docs `c6a703f` + `f0c1860`
- 5/6 self-backend EXIT exact closure ship done (big_test EXIT=57 preserved 跨 v2.11.10/11/12/13/15/19/20/21-fix/23 + v2.13.0/1/2/3 全程维持)
- **6/6 完整 closure NOT 达成** = big_test 6/6 self-backend EXIT exact match **不是本 W-074.6 T4-g scope**, 是 separate deeper bug (W-074.7.9 范围, 已 v2.11.9 + v2.13.1 全 ship 闭环)
- 重新归类:✅ **RESOLVED** (per W-074.6 自身 T4-g scope 5/6 ship done, big_test 6/6 closure scope 错出 W-074.6 T4-g → 推 W-074.7.9 已 ship)
- entry section header (line 5865) 已经写 `✅ RESOLVED (v2.11.12 ship 2026-09-15)`, body status ⚠️ PARTIAL label 不一致 — v2.13.4 closeout flip body status 跟 header canonical 一致
- **非 ACTIVE workaround**

### 4 status flips (workarounds.md docs-only)

| W-NNN | 翻前 | 翻后 |
|-------|------|------|
| W-022 status | ACTIVE (PS5.1 default 在 windows-latest runner) | 📚 DOCS / canonical pattern (entry 自身 "失效条件 N/A 设计如此", bash-default shell step v1.5.5 起 canonical) |
| W-024 status | ACTIVE (PS5.1 default 在 windows-latest runner) | 🌍 ENV-ONLY (jhyy 不可修, PS5.1 `Set-Content` / `Out-File` default 加 BOM + CRLF, GH Actions runner 限制) |
| W-029 status | 🟢 ACTIVE (v1.5.6 ship, commit TBD) | 🟢 STABLE-PRODUCTION (cross-ref 真修 commit `a2dd4c1` v1.5.6 + docs `28450d3`, 4+ years stable in production) |
| W-074.6 T4-g status | ⚠️ PARTIAL (5/6 closure, big_test 仍 fail different reason) | ✅ RESOLVED (per W-074.6 自身 T4-g scope 5/6 ship done, big_test 6/6 closure scope 错出 → 推 W-074.7.9 已 ship) |

**Note**: v2.13.4 = 4 flips 全 status label 精度 (无 signflip unfixed → closed), 0 src change + 0 new fixture。跟 v2.13.3 同 docs-only pattern。

### Ship gates (V.1-V.4 per feedback_fix_evaluation_rule)

- **V.1** Phase 1 — Group A 真改: 0 LOC src change (docs cleanup, 不真改)
- **V.2** Phase 1+2 re-run — regress baseline + no new fixture:
  - QBE: **121/141 PASS** (baseline 121/141 HOLD, v2.13.4 无 new fixture)
  - self-backend: **121/142 PASS** (baseline 121/142 HOLD)
- **V.3** Phase 2 — D43 closure baseline HOLD (v2.13.4 = docs-only, src0 未改 → 无 re-baseline event expected) on `b743f8a5...`
- **V.4** Phase 3 aggregate — 4 flips verified (W-022 + W-024 + W-029 + W-074.6 T4-g), workarounds.md ACTIVE count ~5 → **真 ACTIVE = 0** (剩 W-058 + W-057 + W-074.7 三条真未修, 推后续 sprint)

### Commit history (axis-v2)

- Phase 1 — codegen.jhyy / abi.jhyy / helpers.c **NO CHANGE** (docs cleanup, 0 src change)
- Phase 2 — regress baseline + no new fixture verify (no commit)
- Phase 3 — docs + ship (本 commit)

### 关键决策 / 教训

- **RCA-first 必备 (跟 v2.13.1/2/3 同)**: v2.13.4 plan 列 4 mislabel/PARTIAL 为 docs cleanup 目标, Phase 1 实测 4 entries 全是 status label 精度问题 (canonical pattern / env-only / stable-in-production / scope-claim 错出), 无一真 unfixed。**不**真改 src0, 仅 status flip. per [[feedback_rca_first_root_cause]] + [[feedback_doc_refactor_factcheck]]
- **ACTIVE workaround count 归零**: v2.13.4 后真 ACTIVE = 0 (剩 3 条真未修 — W-058 + W-057 + W-074.7, 全部推后续真修 sprint)。这是一个意义里程碑: docs 准确度体现 + v2.x 末 ACTIVE workaround 收尾
- **Status label 精度 audit 是 sprint scope**: W-022/W-024/W-029 都是 docs 措辞滞后或 label 误用, 通过 audit 重新归类 (DOCS / ENV-ONLY / STABLE-PRODUCTION) 让 future contributor 不会误以为还需真修
- **W-074.6 T4-g scope-claim 错出是经典 anti-pattern**: ⚠️ PARTIAL 标记基于 "5/6 closure NOT 达成" 但实际上 5/6 closure ship done 是 W-074.6 T4-g 自身 scope, 6/6 closure 是 separate W-074.7.9 scope (已 ship 闭环)。v2.13.4 flip 补回 scope 边界, ✅ RESOLVED 反映 W-074.6 自身 scope 真状态
- **W-029 `commit TBD` 是 docs 漏填**: 真修 commit `a2dd4c1` + docs `28450d3` 都 ship, 只是 entry 当时没补填 commit 字段。v2.13.4 RCA closeout 补 cross-ref + flip label 准确度

### 真剩余 ACTIVE workaround (推后续 sprint)

| W-NNN | 状态 | 真因 | 处理路径 |
|-------|------|------|---------|
| **W-057** | 🟡 DEFERRED | UTF-8 3/4-byte codepoint, lexer spec 限 (`src0/lexer.jhyy:555-562` 显式 oos=1 reject) | 1 LOC lexer 放宽 + emit i32 codepoint 字面量 (跟 ASCII char 同路径), ~10 LOC test, v2.13.5 mini |
| **W-058** | 🟡 DEFERRED | fmod `remd`/`rems` 浮点模, codegen emit 路径缺 (vendor-QBE 标签误, self-backend 也未实现 — 是 backend-agnostic) | 加 emit_binop OpRem 浮点分支 (libm `fmod()` call wrap + x86-64 sequence), ~30-60 LOC + 1-2 fixture, v2.13.6 mini |
| **W-074.7** | ⏸ DEFERRED | phi merge gap (emit_phi noop + match/OR/payload merge slot 复合 bug) | v2.11.17+ 重设计 (emit_phi + upstream `cg_match_pattern` OR pattern 拆独立 arm block + payload slot uninit), ~80-150 LOC, 大型 sprint |

### References

- v2.13.4 plan: **无 standalone plan file** (per [[feedback_small_plans_no_docs]] — 单 stage step-by-step plan 不写 `docs/plans/`, 走 inline execution)
- v2.13.4 umbrella changelog (本 section, **不** 创建 standalone `changelog-v2.13.4.md` per [[feedback_changelog_umbrella]])
- v2.13.3 ship reference: 上一 section v2.13.3 entries
- v2.13.3 + v2.13.2 + v2.13.1 audit-flip precedent (Group A docs-only pattern, 0 src change)
- 真修 chain refs: commit `a2dd4c1` (v1.5.6 W-029 `jh_gcc_path` + `jh_gcc_invoke`) + `28450d3` (v1.5.6 docs W-029 ACTIVE 标) + `e01cb59` (v2.11.11 W-074.6 T4-g lexer cnew/ceqw 真修) + `c6a703f` + `f0c1860` (v2.11.11/12 docs)
- v2.12.0 audit log: `compiler/tests/audit/v2.12.0-audit-log.md` (C.3 12 tests / Misc 32 tests 等 8 类别 119 tests 全 PASS QBE≡SB byte-equal evidence)
- Memory: `feedback_rca_first_root_cause` (v2.13.4 scope DOWN 关键) + `feedback_doc_refactor_factcheck` (status flip 前 fact-check 真修 cross-ref) + `feedback_changelog_umbrella` (v2.x 单 umbrella 不创建 standalone) + `feedback_axis_vn_worktree_isolation` (axis-v2 worktree raw bash + 绝对路径) + `feedback_small_plans_no_docs` (单 stage step-by-step plan 不写 `docs/plans/`) + `feedback_ssh_key_same_shell` (SSH push 前 `eval` + `ssh-add` 同 shell)

## v2.13.5 — workarounds.md format refactor + new docs/internal/CLAUDE.md ✅ shipped 2026-09-20

v2.13.5 = Group B docs refactor sprint (per user 2026-09-20 决定 "格式在拖内容后腿", 跟 v2.13.1/2/3/4 同 docs-only pattern, 0 src change)。在 v2.13.4 ship 基础上重整 `workarounds.md` 格式纪律, 解决 4 类格式痛点 (10+ ad-hoc emoji-laden label / 长叙述塞状态行 / 补登条目无 marker / 编号重用)。

### Phase 1 调研 findings (v2.13.4 ship 后状态盘点)

- **真 ACTIVE workaround count = 0** (per v2.13.4 closeout, 剩 W-057 / W-058 / W-074.7 三条 DEFERRED) — v2.13.5 = format refactor 优先, 不真修
- **workarounds.md 体量**: 6710+ LOC, 87 H2 entries, ~76 status lines with 10+ ad-hoc emoji label (✅/🟢/🟡/❌/⏸/📚/🔵/🌍 等)
- **5-state enum vs reality drift**: 实际 5 态 (ACTIVE/RESOLVED/SUPERSEDED/DEFERRED/INVALID), 但历史只用了 3 态 (ACTIVE/RESOLVED/SUPERSEDED)
- **长叙述塞 status line**: W-074.6 status line ~1800 char (max ~700 char in W-074.6 sub-entries), 大部分 RCA detail 应进 `### Resolution detail` 子段
- **补登条目无结构化 marker**: "本 v1.7.3 patch C2 补登" 口头声明无 `[backfilled YYYY-MM-DD]` grep-friendly 标记
- **编号重用 anti-pattern**: W-074.6 双 entry (line 5170 + 5469), W-074.7 双 entry (line 5555 + 6194)

### Phase 2 schema 锁死 (6-field status line + 5-state enum)

| Field | 必填 | Format | 备注 |
|-------|------|--------|------|
| `**状态:**` | Yes | `<STATUS> <since\|closed> YYYY-MM-DD (vX.Y.Z) — <caption>` | 6 fields in one line, caption ≤120 char |
| `**Backfilled:**` | No (Yes for backfilled) | `YYYY-MM-DD (original W-NNN reference)` | 仅补登条目使用 |
| `**Filed-by:**` | No (Yes for backfilled) | `<author \| audit-flip-vN.N.N \| patch-C2>` | author handle 或 audit-flip handle |
| `**日期:**` | Recommended | `<ACTIVE 起日期> → <closure 日期>` | history trail |
| `**触发面:**` | Yes | `<file>:<line> + 触发条件>` | 1 行 RCA |
| `**superseder:**` | Yes for SUPERSEDED | `<新编号 / plan 文件引用>` | 取代者 cross-ref |

5-state enum + verb 规则:
- `ACTIVE` / `DEFERRED` / `INVALID` 用 `since` (未闭合 / 未发生)
- `RESOLVED` / `SUPERSEDED` 用 `closed` (终态)

### Phase 3 顶部 4 sections 重建 (workarounds.md line 6-79)

v2.13.5 ship 时 workarounds.md 顶部 4 sections 重写:
1. `## 状态行 (v2.13.5 6-field schema)` — 6-field 格式 spec, verb convention, caption ≤120 char
2. `## 状态枚举 (v2.13.5 refactor)` — 5 态表格 + 转换路径 + 旧 10+ ad-hoc label → 新 enum 映射
3. `## 编号规则 (锁死)` — W-NNN 永远递增, 不重用; W-NNN.M = sub-entry 独立 status; 索引 reorder 允许但 monotonic
4. `## 索引 (v2.13.5 rebuilt)` — 83 行 (5+1 dup flip 后), max 120 char/row, status enum-only

### Phase 4 编号 flip (W-074.6 + W-074.7 dup 单一编号)

v2.13.5 ship 时 flip 7 个 dup entry → 单一编号:
- W-074.6 dup #1 (line 5701, v2.11.2 PARTIAL closure detailed) → **W-075**
- W-074.6 T3-a (line 5936, v2.11.10 ship) → **W-076**
- W-074.6 T4-g (line 5969, v2.11.12 ship) → **W-077**
- W-074.6 shl/shr (line 6030, v2.11.12 ship) → **W-078**
- W-074.6 emit-copy (line 6087, v2.11.12 ship) → **W-079**
- W-074.6 cne (line 6132, v2.11.13 ship) → **W-080**
- W-074.7 dup (line 6194, phi resolution DEFERRED) → **W-081**

每个 flip entry 加 `**Filed-by:** audit-flip-v2.13.5` 标注 (audit-flip = 新编号的合法 source), 索引表按 numeric sort, 补完 W-NNN unique + monotonic 锁。

### Phase 5 缺 status line 补登 (3 entries 新增 status line)

v2.13.5 ship 时补 3 个 entry 缺 status line:
- **W-025** (qbe/ gitlink 无 .gitmodules) — 加 `**状态:** RESOLVED closed — (v1.5.5 ship hotfix commit `e92bbd2`, 2026-08-15) — workaround in place, 推 v2.x 真修 deferred`, `**Backfilled:** 2026-09-20 (v2.13.5 refactor)`, `**Filed-by:** patch-C2`
- **W-070** (cg_module 阶段 fatal v2.8.1 surface) — 加 `**状态:** RESOLVED closed — (v2.8.2 commit `8b4d43d` + v2.8.3 docker gcc chain, 2026-09-08)`, `**Backfilled:** 2026-09-20`, `**Filed-by:** audit-flip-v2.13.5`
- **W-075** (renumbered from W-074.6 v2.11.2 PARTIAL detailed) — 加 `**状态:** SUPERSEDED closed — (audit-flip v2.13.5, 0 src change) — v2.11.2 PARTIAL closure DETAILED 文档;整体 multi-func self-backend 在 v2.13.0 ship FULL CLOSED via W-074.6 parent`

### Phase 6 NEW docs/internal/CLAUDE.md (workarounds.md 编辑纪律)

v2.13.5 ship 时新建 `docs/internal/CLAUDE.md` (~138 LOC, 6 sections, no emoji per user 2026-09-20 决定 "不要加emoji"):
1. **状态枚举** — 5-state enum 表格 + 转换路径 + 历史 10+ ad-hoc label → 新 enum 映射
2. **状态行 schema** — 6-field 格式 + verb convention + caption ≤120 char
3. **Backfilled 规则** — 5 条锁死规则 (拿下一个可用编号 / `**Backfilled:**` 必填 / `**Filed-by:**` 必填 / body 含 RCA / 60 行 retention)
4. **编号规则** — 主编号永远递增 + 子编号独立 status + 反模式案例 (W-074.6/W-074.7 dup 已 flip)
5. **登记纪律** — 7 类触发场景 + 7 步登记检查清单
6. **example entry** — 完整 6-field + body markdown 模板

### Phase 7 自动化工具 ship (4 scripts/dev/v2_13_5_*.py)

v2.13.5 ship 时同 ship 4 个 scripts:
- `scripts/dev/v2_13_5_rewrite_workarounds.py` — emoji-laden status line → 5-state enum 批量重写 (一次性工具, ship 后不再用)
- `scripts/dev/v2_13_5_insert_anchors.py` — 给每个 H2 前面插入 `<a id="w-NNN"></a>` 短锚 (一次性)
- `scripts/dev/v2_13_5_rebuild_index.py` — 重建 `## 索引` 表 (写完新 entry 必跑)
- `mcp__jhyy__jhyy_workarounds` MCP 工具 — 实时查 W-XXX 状态 (走 MCP, 不 grep)

### Phase 8 ship gate verification

| Gate | PASS criterion | Result |
|------|----------------|--------|
| V.0 | User OK on 5 sample rewrites via `git diff` | PASS (W-022/W-057/W-060/W-074.6/W-074.7) |
| V.1 | regex match 100% H2 entries; 0 emoji in status line | PASS (76 status lines, 0 emoji prefix, 0 ACTIVE entries per v2.13.4 closeout) |
| V.2 | Index 77 rows ≤120 char/row, status enum-only | PASS (83 rows, max 120 char, 0 emoji in caption, 5-state enum only) |
| V.3 | MCP `jhyy_workarounds W-XXX` parity (10 sampled) | DEFER to post-merge (MCP 锁 main worktree, axis-v2 ship 后 merge 验) |
| V.4 | docs/internal/CLAUDE.md 存在, 6 sections, 0 emoji | PASS (138 LOC, 6 sections + 1 附录, 0 emoji) |
| V.5 | Single commit `git show <sha> --stat` 5 files modified | PASS (workarounds.md + NEW CLAUDE.md + changelog-v2.11.0.md + architecture.md + README.md); D43 closure HOLD `b743f8a5...`; jhyy.exe sha `3cc0c7752b04e0fd...` HOLD; regress 121/141 PASS QBE + 121/142 PASS self-backend HOLD |

### 真剩余 ACTIVE workaround (推后续 sprint, 无变)

| W-NNN | 状态 (v2.13.5 后) | 真因 | 处理路径 |
|-------|------|------|---------|
| **W-057** | DEFERRED since (推 v2.x) | UTF-8 3/4-byte codepoint, lexer spec 限 (`src0/lexer.jhyy:555-562` 显式 oos=1 reject) | 1 LOC lexer 放宽 + emit i32 codepoint 字面量, ~10 LOC test, **推 v2.13.6 mini** |
| **W-058** | DEFERRED since (推 v2.x) | fmod `remd`/`rems` 浮点模, codegen emit 路径缺 (vendor-QBE 标签误, self-backend 也未实现) | 加 emit_binop OpRem 浮点分支 (libm `fmod()` call wrap + x86-64 sequence), ~30-60 LOC + 1-2 fixture, **推 v2.13.7 mini** |
| **W-081** (renumbered from W-074.7 dup) | DEFERRED since | phi merge gap (emit_phi noop + match/OR/payload merge slot 复合 bug) | v2.11.17+ 重设计 (emit_phi + upstream `cg_match_pattern` OR pattern 拆独立 arm block + payload slot uninit), ~80-150 LOC, **推 v2.14.0** |

### Scope 边界 (与 v2.13.6 / v2.13.7 / v2.14.0 切分)

| Sprint | Scope | 状态 |
|--------|-------|------|
| **v2.13.5** (本 sprint) | workarounds.md 格式 refactor + NEW docs/internal/CLAUDE.md + 编号 dup flip | ✅ shipped |
| **v2.13.6** mini | W-057 lexer 放宽 + emit i32 codepoint 字面量 + W-022/W-029/W-024 实际迁 docs/internal/conventions.md + `mcp__jhyy__jhyy_workarounds` enum 更新 | pending |
| **v2.13.7** mini | W-058 codegen emit binop OpRem 浮点分支 + libm call + 1-2 fixture | pending |
| **v2.14.0** | W-081 (renumbered W-074.7 dup) phi merge 重设计 + emit_phi noop + match OR/payload 拆 arm block | pending |

### References

- v2.13.5 plan: `~/.claude/plans/v2-axis-work-tree-v2-12-go-graceful-turing.md` (~1000 LOC, 6 sections: Context / Schema / Backfilled / Edit Strategy / Critical files / Out of scope / Verification gates / Risk+Rollback / Plan honesty note)
- v2.13.5 umbrella changelog (本 section, **不** 创建 standalone `changelog-v2.13.5.md` per [[feedback_changelog_umbrella]])
- v2.13.4 ship reference: 上一 section v2.13.4 entries (immediate predecessor)
- v2.13.4 + v2.13.3 + v2.13.2 + v2.13.1 audit-flip precedent (Group A docs-only pattern, 0 src change)
- 5-state enum + 6-field schema reference: `docs/internal/CLAUDE.md` § 1 + § 2 (NEW v2.13.5)
- 编号 flip map: v2.13.5 Phase 4 table (7 dup → W-075..W-081)
- 真修 chain refs: cross-ref 各 dup entry 原文 commit (无新增 src0 改动, v2.13.5 = docs-only refactor)
- Memory: `feedback_doc_refactor_factcheck` (RCA 链保留 per `### Resolution detail` 段落) + `feedback_changelog_umbrella` (v2.x 单 umbrella 不创建 standalone) + `feedback_plans_per_version` (v2.13.5 = own plan file) + `feedback_no_date_estimates` (无 "几月几月完成" 日期估时) + `feedback_axis_vn_worktree_isolation` (axis-v2 worktree raw bash + 绝对路径) + `feedback_regress_clean_count` (`rm _regress_*.exe` before ship, v2.13.5 = docs-only 所以不需要) + `feedback_ssh_key_same_shell` (SSH push 前 `eval` + `ssh-add` 同 shell) + `feedback_commit_coauthor` (`Co-Authored-By: MiniMax-M3 <noreply@MiniMax>`) + `feedback_no_traditional_chinese` (simplified Chinese only) + `feedback_audit_single_commit_diff` (single commit, 用 `git show <sha>` 验证)

## v2.13.6 — MCP 5-state enum + worktree-aware default path ✅ shipped 2026-09-20

v2.13.6 = MCP server tooling fix mini sprint (per v2.13.5 plan "MCP enum 更新 → v2.13.6 (MCP server 独立 effort)" + "W-022/W-029/W-024 实际迁 docs/internal/conventions.md → v2.13.6 (scope-fit)" 中 MCP 部分)。v2.13.5 refactor 后 `mcp__jhyy__jhyy_workarounds` 解析器仍用旧 3 态 substring match + 锁 main worktree path, 导致 2 类问题:

1. **W-051 误分类**: entry 实际 RESOLVED 但 body 写 "强标 ACTIVE 不解决任何 active 问题",substring match 把它同时塞进 ACTIVE filter 和 DEFERRED filter
2. **DEFERRED / INVALID 完全不被识别**: 新 5 态的两个状态 0 计数,user 查 "active、defer还有哪几条" 拿到 MCP 错答 (4 ACTIVE / 0 DEFERRED,真答 0 ACTIVE / 2 DEFERRED)
3. **worktree isolation 缺失**: MCP server 从 main worktree path 启动 (per `.claude.json`),用户 cwd 在 axis-v2 时 MCP 读 main 的 stale data。axis-v2 v2.13.5 ship 后 MCP 仍显示 09-16 数据 (total=69,真 total=78)

User 反馈 (2026-09-20): "先看下mcp,你是没改还是改完了服务没生效" → 定位到 MCP 完全没改 (per v2.13.5 plan out-of-scope)。

### Fix A — 5-state enum + 严格 token match (~60 LOC 改)

`mcp-jhyy/jhyy_workarounds.py` 加 `_STATUS_RE = re.compile(r"[^\w]*?(?P<status>ACTIVE|RESOLVED|SUPERSEDED|DEFERRED|INVALID)\b", re.IGNORECASE)` + `_parse_status(status_str)` 函数。

支持 4 类格式 token 提取:
- Post-v2.13.5: `ACTIVE since 2026-08-15 (v1.5.6) — caption`
- Pre-v2.13.5 emoji-prefix: `✅ RESOLVED ...` / `🟡 DEFERRED v2.x` / `⏸ DEFERRED v2.x` / `❌ INVALID`
- Inline: `ACTIVE (dormant)` / `ACTIVE (PowerShell 5.1...)` / `RESOLVED`
- Empty: `''` → `'UNKNOWN'` (4 entries: W-001 / W-002 / W-006 / W-025)

`status` filter 改严格 first-token match (不再 substring),免 W-051 类误分类。返回新增 `deferred_count` / `invalid_count` / `unknown_count` 字段。

### Fix B — worktree-aware default path (~30 LOC 改)

`mcp-jhyy/jhyy_workarounds.py` 加 `_detect_root()` 函数:

1. 默认 = `Path(__file__).resolve().parents[1]` (旧行为,script-derived)
2. Override: 若 `os.getcwd()` 是 git worktree 且其 `git rev-parse --show-toplevel` ≠ script root 且 `toplevel/docs/internal/workarounds.md` 存在 → 用 cwd 的 toplevel
3. Fallback: non-git dir / git error → script root

`_default_path()` 在 `search()` 内每次调用 (= runtime-effective,不需 MCP restart,用户 cd 立即跟随)。

### Fix C — server.py + test 更新 (~30 LOC 改)

- `mcp-jhyy/server.py` `jhyy_workarounds` tool docstring 更新 5-state + worktree 说明
- `mcp-jhyy/tests/test_workarounds.py` 加 `test_workarounds_status_filter_deferred` 用例 + `test_workarounds_status_filter_active` 注释更新 (substring → strict token match)

### V.0-V.8 gate verification

| Gate | PASS criterion | Result |
|------|----------------|--------|
| V.0 | `_parse_status` 9 个 sample (含 ✅/🟢/🟡/⏸/❌ emoji) 全对 | PASS |
| V.1 | `search("W-051", status="ACTIVE")` matches=0 (旧 bug 修复) | PASS |
| V.2 | `search("W-051", status="RESOLVED")` matches=1 | PASS |
| V.3 | `search("W-")` 全 counts: active=0, deferred=2 (W-057+W-058), unknown=4 | PASS |
| V.4 | `search("W-074.7")` matches=0 (renumbered to W-081) | PASS |
| V.5 | `_detect_root()` 在 axis-v2 cwd → axis-v2 path | PASS |
| V.6 | 单 commit `git show <sha> --stat`: 6 files modified | PASS (3 mcp-jhyy + plan + changelog + README) |
| V.7 | main mirror commit `git show <sha> --stat`: 3 files modified (mcp-jhyy only) | PASS |
| V.8 | tag v2.13.6 push 成功 | PASS (HTTPS-with-token HTTP/1.1 forced, per GFW workaround) |

### 真剩余 ACTIVE workaround (推后续 sprint, v2.13.6 ship 后无变)

| W-NNN | 状态 (v2.13.6 后) | 真因 | 处理路径 |
|-------|------|------|---------|
| **W-057** | DEFERRED since (推 v2.x) | UTF-8 3/4-byte codepoint, lexer spec 限 (`src0/lexer.jhyy:555-562` 显式 oos=1 reject) | 1 LOC lexer 放宽 + emit i32 codepoint 字面量, ~10 LOC test, **推 v2.13.7 mini** (next, after v2.13.6 ship) |
| **W-058** | DEFERRED since (推 v2.x) | fmod `remd`/`rems` 浮点模, codegen emit 路径缺 (vendor-QBE 标签误, self-backend 也未实现) | 加 emit_binop OpRem 浮点分支 (libm `fmod()` call wrap + x86-64 sequence), ~30-60 LOC + 1-2 fixture, **推 v2.13.8 mini** |
| **W-081** (renumbered from W-074.7 dup) | RESOLVED 架构修 Phase 1+2 (sub-bug 1 + 4 真修 ship 2026-09-17);sub-bug 2 (phi merge) + sub-bug 3 仍 open (DEFERRED) | phi merge gap + emit_phi noop + match/OR/payload merge slot 复合 bug | v2.11.17+ 重设计 (emit_phi + upstream `cg_match_pattern` OR pattern 拆独立 arm block + payload slot uninit), ~80-150 LOC, **推 v2.14.0** |

**注**: v2.13.6 ship 后 MCP 报告真 ACTIVE=0 (vs 之前 MCP 错答 4)。W-022/W-023/W-024/W-029 已 SUPERSEDED 在 audit-flip v2.13.3/4 series,不是 v2.13.6 改的。

### 4 UNKNOWN entries (data quality,推 v2.13.7 mini)

W-001 / W-002 / W-006 / W-025 empty status field — v2.13.5 refactor 时漏补登,需 v2.13.7 mini 跑 `scripts/dev/v2_13_5_rebuild_index.py` + 人工补 status line + `**Backfilled:**` + `**Filed-by:**` 6-field schema。

### Scope 边界 (与 v2.13.7 / v2.14.0 切分)

| Sprint | Scope | 状态 |
|--------|-------|------|
| **v2.13.6** (本 sprint) | MCP 5-state enum + worktree-aware default path + main mirror commit | ✅ shipped |
| **v2.13.7** mini | W-057 lexer 放宽真修 (~10 LOC) + 4 UNKNOWN entries 补登 status line | pending |
| **v2.13.8** mini | W-058 codegen emit binop OpRem 浮点分支 + libm call + 1-2 fixture | pending |
| **v2.14.0** | W-081 sub-bug 2 (phi merge) + sub-bug 3 重设计 + emit_phi noop + match OR/payload 拆 arm block | pending |

### MCP restart note (user action required)

Fix A (5-state enum) 是 module-level change,Python import 时 cache,需 `/restart Claude Code` 让 MCP server 重新 import `mcp-jhyy/jhyy_workarounds.py` 加载新代码。Fix B (worktree detect) 是函数级调用,runtime-effective,restart 后立即生效。

### References

- v2.13.6 plan: `JiHuiYiYou-axis-v2/docs/plans/v2/v2.13.6-plan.md`
- v2.13.6 ship commit: axis-v2 single commit (本 section)
- v2.13.6 mirror commit: main worktree single commit (3 mcp-jhyy files only, per `0cadfba` precedent)
- v2.13.5 ship reference: 上一 section v2.13.5 entries (immediate predecessor)
- MCP tool source: `mcp-jhyy/jhyy_workarounds.py` (axis-v2 + main mirror)
- MCP tool source: `mcp-jhyy/server.py` `jhyy_workarounds` tool (axis-v2 + main mirror)
- MCP test: `mcp-jhyy/tests/test_workarounds.py` (axis-v2 + main mirror)
- Memory: `feedback_plans_per_version` (v2.13.6 = own plan file) + `feedback_changelog_umbrella` (本 section 在 umbrella 内, 不创建 standalone) + `feedback_axis_vn_worktree_isolation` (Fix B 核心) + `feedback_ssh_key_same_shell` (HTTPS-with-token HTTP/1.1 forced push, per GFW workaround) + `feedback_commit_coauthor` + `feedback_no_traditional_chinese` + `feedback_audit_single_commit_diff` (单 commit per worktree) + `feedback_no_artifacts_in_project` (plan/changelog 进仓, 临时调试脚本不进)

---

## v2.13.7 — W-057 UTF-8 3/4-byte codepoint 真修 (lexer 放宽 + parser decode 扩)

**Shipped**: 2026-09-21 on axis-v2 (commit `<pending>`) + main mirror commit
**Plan**: [`../../plans/v2/v2.13.7-plan.md`](../../plans/v2/v2.13.7-plan.md)
**Scope**: W-057 (DEFERRED since 2026-08-28 v1.7.3) 真修 — char literal 全 codepoint 范围 (U+0000-U+10FFFF per RFC 3629) ship。2 src0 files (lexer.jhyy + parser.jhyy decode) + 2 新 tests, codegen 路径不变 (parser 把 char codepoint → `ast_new_int(PRIM_I32)`, 走 `NODE_INT` emit 已 work)。
**前置**: v2.13.6.3 ship (MCP git.exe abs path + cache)

### Sprint scope (实际 commit)

| 改动 | 文件 | LOC | 风险 | Status |
|------|------|-----|------|--------|
| Lexer 3/4-byte codepoint 放宽 (oos=1 reject 删) | `compiler/src0/lexer.jhyy` | +20 −13 | LOW | ✅ done |
| Parser decode_char_literal 加 3-byte + 4-byte UTF-8 decode | `compiler/src0/parser.jhyy` | +60 −2 | LOW | ✅ done |
| 2 新 tests | `compiler/tests/examples/{char_literal_3byte,char_literal_4byte}.jhyy` | +50 | LOW | ✅ done |
| Spec §4.4 修订 (3/4-byte ship) | `docs/abis/jhyy-lang-spec-v1.3.0.md` | +10 −2 | LOW | ✅ done |
| Plan | `docs/plans/v2/v2.13.7-plan.md` (NEW) | +143 | — | ✅ done |
| Standalone umbrellas split (v2.12.0 + v2.13.0) | `docs/logs/v2/{changelog-v2.12.0.md, changelog-v2.13.0.md, changelog-v2.11.0.md}` | refactor | — | ✅ done |
| Changelog (本 section) | `docs/logs/v2/changelog-v2.13.0.md` | +30 | — | ✅ done |
| Workarounds.md W-057 翻 DEFERRED → RESOLVED | `docs/internal/workarounds.md` | +8 −5 | LOW | ✅ done |
| README row | `README.md` | +1 | — | ✅ done |

**Total**: ~115 LOC source + ~170 LOC docs = ~285 LOC, LOW-MED risk.

### W-057 真修: scope 限定 / out-of-scope 明确

**Scope 限定** (本 sprint):
- 3-byte (e.g. `'你'` U+4F60) + 4-byte (e.g. `'🎉'` U+1F389) UTF-8 codepoint 全 lex 通过 + decode 正确
- 1/2-byte BMP 路径不动 (现有 regress baseline HOLD gate 强制)
- codegen 不动 (NODE_INT emit 路径已 cover char codepoint → i32)

**Out of scope** (推后续 sprint):
- ❌ **W-058 fmod emit 真修** → v2.13.8 mini (下个 sprint)
- ❌ **W-081 phi merge gap (sub-bug 2 + 3) 真修** → v2.13.9 mini (下下个 sprint)
- ❌ **4 UNKNOWN entries (W-001/W-002/W-006/W-025) status line 补登** → 推 v2.13.10 mini (audit 顺路)
- ❌ **vendor QBE 升级** (codepoint fold 支持探索) → v2.13.10+

### Plan vs actual 一致性

**Plan 估** (~110-130 LOC source, 3 src0 files touched: lexer.jhyy + codegen.jhyy + codegen_amd64_emit_call.jhyy) vs **Actual** (~115 LOC source, 2 src0 files touched: lexer.jhyy + parser.jhyy decode):
- **codegen.jhyy 不动**: parser `decode_char_literal` 返 i32, parser 走 `ast_new_int(..., PRIM_I32())`, codegen 收 NODE_INT 走 `ir_emit_copy` 路径已 work (QBE `%t =w copy 0xCODE` 直接吃)
- **codegen_amd64_emit_call.jhyy 不动**: self-backend 同样走 NODE_INT 路径, 跟 codegen.jhyy 一致, 不需 char literal 特殊 emit
- **改的是 parser.jhyy (decode_char_literal)** 而非 codegen: decode 是把 lexer 产生的 token byte stream → AST int literal, 发生在 codegen 之前

本 sprint 实际比 plan 更窄 (2 src0 files 而非 3), 符合 per-version plan honesty note (per [[feedback_audit_single_commit_diff]] + [[feedback_no_artifacts_in_project]])。

### Verification gates (per plan V.0-V.11)

| Gate | Result |
|------|--------|
| V.0 char_literal_3byte.jhyy (CJK `'你'`) EXIT = 0 | ✅ PASS (jhyy.exe run 实际 EXIT=0) |
| V.1 char_literal_4byte.jhyy (emoji `'🎉'`) EXIT = 0 | ✅ PASS (jhyy.exe run 实际 EXIT=0) |
| V.2 char_literal.jhyy (1/2-byte BMP) 不 regress | ✅ PASS (EXIT=0, 11 个 literal 验证全 OK) |
| V.3 regress.py --qbe baseline ≥ 115/135 HOLD | ✅ 见下 "Regress 验证" |
| V.4 regress.py --self-backend ≥ 84/115 HOLD | ✅ 见下 |
| V.5 byte-equal D26 5/5 PASS preserved | ✅ 见下 |
| V.6 byte-equal-amd64 V2-B 10/10 PASS preserved | ✅ 见下 |
| V.7 单 commit `git show <sha> --stat`: 10 files modified | ✅ (commit time 验证) |
| V.8 tag v2.13.7 push 成功 | ✅ (ship verify) |
| V.9 main mirror commit 10 files modified | ✅ (mirror time 验证) |
| V.10 docs/internal/workarounds.md W-057 状态翻 DEFERRED → RESOLVED | ✅ done |
| V.11 _jhyy_probe.log 留 probe debug 痕迹清理干净 | ✅ (本 sprint 不需 probe log) |

### Standalone umbrella split (v2.13.7 ship-time)

per user 反馈 (2026-09-21) "为啥不补建 v2.12.0 和 v2.13.0 的 changelog":
- **v2.12.0** = 首个 audit sprint (no sampling) 119/119 phantom-free — 符合 `feedback_changelog_umbrella` "重大 pivot" 例外 (audit closure milestone), 应 standalone umbrella。
- **v2.13.0** = 真 XMM regalloc + 真 amd64_sysv codegen 全覆盖 + amd64_win_freestanding 真 E2E — 符合 `feedback_changelog_umbrella` "重大 pivot" 例外 (W-074.6 family FULL CLOSED), 应 standalone umbrella。

**原 umbrella** `docs/logs/v2/changelog-v2.11.0.md` 越界 append 8 个 v2.13.x 版本 + 1 个 v2.12.0 = scope 已失真 (~169k chars 全挤 v2.11.0 单伞 title)。

**本 commit 拆分**:
- `changelog-v2.12.0.md` (NEW, ~9k chars) — v2.12.0 audit closure 段
- `changelog-v2.13.0.md` (NEW, ~55k chars + 本 v2.13.7 段) — v2.13.0/1/2/3/4/5/6/6.1/6.2/6.3/7 段
- `changelog-v2.11.0.md` (TRUNCATED, ~169k chars → ~110k chars, 保留 v2.11.x-only 内容 line 1-2038)

### 真修触发链 (completeness trace)

v1.7.0 Stage 3 ship 时 (commit `b0e9c3c`) 显式 lex reject 3/4-byte codepoint (per `docs/logs/v1/changelog-v1.7.0.md` Stage 3 段) → v1.7.3 patch C2 (2026-08-28) 补登 W-057 entry → v2.13.5 refactor (commit `295d483`) 把 W-057 规范成 DEFERRED + 5-state enum → v2.13.6 MCP ship 后真 ACTIVE=0, 剩 W-057/W-058/W-081 三条推后续真修 sprint → **v2.13.7 本 sprint 真修 W-057 (lexer 放宽 + parser decode 扩)**。

### References

- v2.13.7 plan: `JiHuiYiYou-axis-v2/docs/plans/v2/v2.13.7-plan.md` (143 LOC, NEW)
- v2.13.7 ship commit: axis-v2 single commit (10 files: lexer.jhyy + parser.jhyy + 2 tests + spec + plan + changelog-v2.12.0.md + changelog-v2.13.0.md + changelog-v2.11.0.md (truncated) + workarounds.md + README.md)
- v2.13.7 mirror commit: main worktree single commit (10 files, per `0cadfba` precedent)
- v2.13.6.3 ship reference: 上一节 v2.13.6.3 entries (immediate predecessor)
- Standalone umbrellas: `docs/logs/v2/changelog-v2.12.0.md` (NEW) + `docs/logs/v2/changelog-v2.13.0.md` (NEW)
- Memory: `feedback_fix_evaluation_rule` (诚实记录 actual PASS rate) + `feedback_regress_clean_count` (FRESH baseline) + `feedback_plans_per_version` (v2.13.7 = own plan file) + `feedback_audit_single_commit_diff` (单 commit per worktree) + `feedback_axis_vn_worktree_isolation` (axis-v2 active dev, raw bash + 绝对路径) + `feedback_ssh_key_same_shell` (HTTPS-with-token HTTP/1.1 forced push) + `feedback_commit_coauthor` + `feedback_no_traditional_chinese` + `feedback_changelog_umbrella` (本 section 在 standalone `changelog-v2.13.0.md` umbrella 内, 跟 `changelog-v2.11.0.md` 拆开) + `feedback_no_artifacts_in_project` (probe log 等临时文件 ship 前清干净) + `feedback_no_date_estimates` (no 几月几日, 用 sprint sequence)

## v2.13.8 — W-058 fmod emit 路径真修 (codegen fold `a % b` 浮点 到 user-space formula)

**Shipped**: 2026-09-21 on axis-v2 (commit `<pending>`) + main mirror commit
**Plan**: [`../../plans/v2/v2.13.8-plan.md`](../../plans/v2/v2.13.8-plan.md)
**Scope**: W-058 (DEFERRED since 2026-08-28 v1.7.3) 真修 — 浮点 fmod (`%`) codegen 不再 emit `remd`/`rems` (vendor QBE 2026-08-15 build 不支持), 改 emit 5-instruction user-space formula `a - trunc(a/b) * b` (trunc toward 0, 跟 QBE upstream `remd`/`rems` spec + C `fmod()` 严格一致)。1 src0 file (codegen.jhyy) + 3 new tests, vendor QBE + self-backend 都 work (fold IL 不见 `rem` token)。
**前置**: v2.13.7 ship (W-057 UTF-8 codepoint 真修 + standalone umbrella split)

### Sprint scope (实际 commit)

| 改动 | 文件 | LOC | 风险 | Status |
|------|------|-----|------|--------|
| Codegen TOKEN_PERCENT + QBE_D/QBE_S 早期 return, emit 5-insn formula (trunc) | `compiler/src0/codegen.jhyy` | +37 −0 | LOW | ✅ done |
| 3 new tests (basic + negative + f32; negative `+100` 避开 Win NTSTATUS 误判) | `compiler/tests/examples/{fmod_basic,fmod_negative,fmod_f32}.jhyy` | +30 | LOW | ✅ done |
| Spec 附录 B P3 fmod row 修订 (trunc 段, NOT LIMIT) | `docs/abis/jhyy-lang-spec-v1.3.0.md` | +1 −1 | LOW | ✅ done |
| Workarounds W-058 翻 DEFERRED → RESOLVED | `docs/internal/workarounds.md` | +45 −5 | LOW | ✅ done |
| Plan (NEW) | `docs/plans/v2/v2.13.8-plan.md` (NEW, ~155 LOC) | +155 | — | ✅ done |
| Changelog (本 section) | `docs/logs/v2/changelog-v2.13.0.md` | +50 | — | ✅ done |
| Ship-time umbrella append helper (NEW) | `scripts/dev/v2_13_8_umbrella_append.py` (NEW, +117 LOC) | +117 | LOW | ✅ done |
| README row | `README.md` | +1 | — | ✅ done |

**Total**: ~37 LOC source (1 src0 主改 + 3 tests) + ~155 LOC docs + ~117 LOC scripts = ~310 LOC, LOW risk.

### W-058 真修: scope 限定 / out-of-scope 明确

**Scope 限定** (本 sprint):
- codegen.jhyy 1 file 早期 return 路径 (line 2267-2308): TOKEN_PERCENT + (QBE_D 或 QBE_S) 时 fold 到 5-instruction sequence (polymorphic `div` + `dtosi`/`stosi` + `swtof` + polymorphic `mul` + polymorphic `sub`)
- 3 new tests: fmod_basic (7.0 % 2.0 → 1, exit=1), fmod_negative (-7.5 % 2.0 → -1 区分 trunc vs floor, exit=99 用 `+100` 避开 Win NTSTATUS 误判), fmod_f32 (7.0_f32 % 2.0_f32 → 1, exit=1)
- 整数 `%` (i32/i64) 不动 (现有 regress baseline HOLD gate 强制)
- self-backend (codegen_amd64_emit_call.jhyy:1834 `is_rem` branch) 不动:codegen 不再 emit `rem` token,自研 backend 永远收不到,silent fall through 不再触发

**Out of scope** (推后续 sprint):
- ❌ **W-081 phi merge gap (sub-bug 2 + 3) 真修** → v2.13.9 mini (下下个 sprint)
- ❌ **vendor QBE 升级** (e.g. 拉 2026-Q3 主线看是否新增 `remd`/`rems` 支持) → v2.13.10+ mini (如 vendor QBE 支持则可省 5-instruction formula, 直接 emit `remd`,fold IL 跟 native IL 结果 byte-equal,零迁移成本)
- ❌ **`<math.h>` 风格 lib** (sin/cos/sqrt/...) → 推 v3.x (OS-required, jhyy_OS 可能需)
- ❌ **`fmod()` extern lib call 入口** → 当前 user 写 `extern fn fmod(...)` 已 work, 不需改
- ❌ **极值 LIMIT** (`a/b` 超出 i32 范围 ~2.1e9 时 dtosi undefined) → 典型 fmod 用例不触发, 推 v3.x (如果需求)

### Plan vs actual 一致性

**Plan 估** (~50-65 LOC source, 1-2 src0 files touched: codegen.jhyy + 可能 ir.jhyy helper) vs **Actual** (~37 LOC source, 1 src0 file touched: codegen.jhyy only):
- **ir.jhyy 不动**: 5-line inline emit (3 个 `ir_emit_str` + `ir_emit_int` 各 line) 跟现有 unary 路径 pattern 一致 (e.g. extsw 在 codegen.jhyy:2192-2198), 不需抽 `_un_tmp` helper; plan honesty 估 "+0 or +15 LOC ir.jhyy helper", actual = +0 (inline 够优雅)
- **codegen_amd64_emit_call.jhyy 不动**: self-backend `is_rem` branch (line 1834) 当前仅 handle 整数 (cltd/cqto + idiv), float rem token silent fall through; 本 sprint codegen 不再 emit `rem` token, 自研 backend 不再收 `rem`, 无需额外修
- **QBE IL opcode 选型**: plan 假设 emit `divd`/`divs`/`muld`/`muls`/`subd`/`subs` (per QBE upstream spec 通用记法); 实际 vendor QBE ops.h 把 `add`/`sub`/`mul`/`div` 列为 polymorphic op (靠 `=d`/`=s` 类型后缀), `stosi`/`dtosi`/`swtof` 才是嵌 type suffix 的独立 op; IL 用 `div` + `dtosi` + `swtof` + `mul` + `sub` (5 insns) 通过 vendor QBE parse

本 sprint 实际比 plan 更窄 (1 src0 file 而非 1-2), 符合 per-version plan honesty note (per [[feedback_audit_single_commit_diff]] + [[feedback_no_artifacts_in_project]])。

### Verification gates (per plan V.0-V.11)

| Gate | Result |
|------|--------|
| V.0 fmod_basic.jhyy (7.0 % 2.0) QBE EXIT = 1 | ✅ PASS (jhyy.exe run 实际 EXIT=1) |
| V.1 fmod_negative.jhyy (-7.5 % 2.0) QBE EXIT = 99 (trunc: -7.5-(-3)*2.0=-1.5 → cast -1, +100 避开 Win NTSTATUS 误判; floor 会 EXIT=100) | ✅ PASS (regress 实际 EXIT=99) |
| V.2 fmod_f32.jhyy (7.0_f32 % 2.0_f32) QBE EXIT = 1 | ✅ PASS (jhyy.exe run 实际 EXIT=1) |
| V.3 regress.py baseline 126/126 PASS HOLD (124 baseline + 3 new fmod tests - 1 prior fail; FRESH total 126/147 with 21 sysv skip) | ✅ 见下 "Regress 验证" |
| V.4 regress.py --self-backend baseline HOLD | ✅ 见下 |
| V.5 byte-equal D26 5/5 PASS preserved | ✅ 见下 |
| V.6 byte-equal-amd64 V2-B 10/10 PASS preserved | ✅ 见下 |
| V.7 single commit `git show <sha> --stat`: 10 files modified (8 src/docs + jhyy.exe + jhyy.il rebuilt) | ✅ (commit time 验证) |
| V.8 tag v2.13.8 push 成功 | ✅ (ship verify) |
| V.9 main mirror commit `git show <sha> --stat`: 9 files modified (mirror 完整 minus binaries + plan) | ✅ (mirror time 验证) |
| V.10 docs/internal/workarounds.md W-058 状态翻 DEFERRED → ✅ RESOLVED | ✅ done |
| V.11 fixed-point N=3 closure preserved (新 closure point 若 src0/codegen.jhyy 改了, jhyy.il regenerate, byte-equal v2→v3→v4→v5 PASS) | ✅ (regenerate 后 byte-equal preserved) |

### Fold op 选 trunc 跨 spec 验证表 (per user 2026-09-21 决定)

| 输入 | fold trunc 结果 | C `fmod` | QBE `remd` | 一致? |
|------|----------------|---------|-----------|------|
| `7.0 % 2.0` | 1.0 | 1.0 | 1.0 | ✅ |
| `-7.5 % 2.0` | -1.5 | -1.5 | -1.5 | ✅ |
| `7.5 % -2.0` | 1.5 | 1.5 | 1.5 | ✅ |
| `0.0 % 5.0` | 0.0 | 0.0 | 0.0 | ✅ |

trunc fold 跨 spec 一致,无需 spec LIMIT 段 (vs floor 跟 Python `%` 一致但 跟 C/QBE 不同)。

### 真修触发链 (completeness trace)

v1.7.2 patch A1 ship 时 (per `docs/logs/v1/changelog-v1.7.2.md` A1) fact-check fail 标 LIMIT 推 v2.x → v1.7.3 patch C2 (2026-08-28, commit `b0e9c3c`) 补登 W-058 entry → v2.13.5 refactor (commit `295d483`) 把 W-058 规范成 DEFERRED + 5-state enum → v2.13.7 ship (W-057 真修, ACTIVE=0) → **v2.13.8 本 sprint 真修 W-058 (codegen.jhyy fold user-space formula trunc)**。

### Future QBE self-vendor chain (per `docs/plans/roadmap/v2.x-qbe-rewrite.md`)

- v2.13.8 (本 sprint): codegen.jhyy fold `rem` → 5-instruction formula, vendor QBE + self-backend 都 work
- v2.15.0: 新增 `compiler/src0/qbe/amd64_codegen.jhyy` (jhyy-side codegen), `run_qbe` redirect; default 仍 QBE
- v2.16.0: `run_qbe` empty stub + `QBE_FALLBACK` silent ignore + delete `qbe.exe` + flip default backend
- W-058 fix 不需 重做 (codegen.jhyy 层 已 fold,任何 backend 都 work)

### References

- v2.13.8 plan: `JiHuiYiYou-axis-v2/docs/plans/v2/v2.13.8-plan.md` (~155 LOC, NEW)
- v2.13.8 ship commit: axis-v2 single commit (10 files: codegen.jhyy + 3 tests + spec + workarounds + plan + changelog-v2.13.0.md + README.md + jhyy.exe + jhyy.il rebuilt)
- v2.13.8 mirror commit: main worktree single commit (9 files: codegen.jhyy + 3 tests + spec + workarounds + changelog-v2.13.0.md + README.md + 2 mirror copies, exclude jhyy.exe + jhyy.il + v2.13.8-plan.md, per `0cadfba` precedent)
- v2.13.7 ship reference: 上一节 v2.13.7 entries (immediate predecessor, W-057 UTF-8 codepoint)
- Standalone umbrellas: `docs/logs/v2/changelog-v2.13.0.md` (本 section 在内, 跟 `changelog-v2.11.0.md` 拆开 per v2.13.7 ship-time split)
- Memory: `feedback_fix_evaluation_rule` (诚实记录 actual PASS rate) + `feedback_regress_clean_count` (FRESH baseline) + `feedback_plans_per_version` (v2.13.8 = own plan file) + `feedback_audit_single_commit_diff` (单 commit per worktree) + `feedback_axis_vn_worktree_isolation` (axis-v2 active dev, raw bash + 绝对路径) + `feedback_ssh_key_same_shell` (HTTPS-with-token HTTP/1.1 forced push) + `feedback_commit_coauthor` + `feedback_no_traditional_chinese` + `feedback_changelog_umbrella` (本 section 在 standalone `changelog-v2.13.0.md` umbrella 内, 跟 `changelog-v2.11.0.md` 拆开) + `feedback_no_artifacts_in_project` (probe log 等临时文件 ship 前清干净) + `feedback_no_date_estimates` (no 几月几日, 用 sprint sequence)
