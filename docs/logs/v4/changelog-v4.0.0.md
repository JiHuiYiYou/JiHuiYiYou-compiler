# v4.0.0 umbrella changelog

**Ship date:** 2026-09-30 · **Branch:** `main` · **Tag:** `v4.0.0` · **Preconditions:** all ✅ (v1.8.3 / v2.16.0 / v3.4.2 all shipped)

---

## What is v4.0.0

v4.0.0 is the **convergence release** — first merge of the two parallel axes (`axis-v2` + `axis-v3`) into `main`, kicking off the v4.x minor-version series. Per user decision 2026-09-29, both v2.x and v3.x are declared FINAL; v4.0.0 unifies their state in a single tree and re-bases all version references, README, CLAUDE.md, and the roadmap.

**No new features in v4.0.0 itself** — the feature surface is the union of v2.16.0 (QBE-removed, in-mem self-backend pipeline, N≥10 fixed point, `.exe` byte-equal D26 stage0 coverage) + v3.4.2 (V3 self-backend closure, stdlib `std::*` modules, char_literal_3/4byte + fmod 真修).

v4.0.0 = the moment when JHYY stops being two parallel compilers and becomes one.

---

## Preconditions met

| Precondition | Status | Reference |
|---|---|---|
| v1.8.3 shipped (Stage 2 N=4 byte-equal closure + installer) | ✅ 2026-08-29 | tag `98c8272` |
| v2.16.0 shipped (QBE removed + bench.sh + .exe byte-equal) | ✅ 2026-09-22 | tag `v2.16.0` = `axis-v2` HEAD `0b4cde5` |
| v3.4.2 shipped (V3 self-backend closure + 3 minor 真修 W-085/088/089) | ✅ 2026-09-29 | tag `v3.4.2` = `axis-v3` HEAD `8cfcc1e` |
| v2/v3 ACTIVE workaround bucket cleared | ✅ at v3.4.2 | `workarounds.md` ACTIVE = 0 |

---

## Merge commit log

| # | Commit | Message | Notes |
|---|---|---|---|
| 1 | `a4ba8fa` | `chore(merge): merge axis-v2 into main (v2.16.0 axis final)` | `--no-ff`; 1 conflict on `compiler/tests/bootstrap/fixed_point.sh` (resolved by `--theirs`; v3 doesn't have this file) |
| 2 | `c13397d` | `chore(merge): merge axis-v3 into main (v3.4.2 axis final)` | `--no-ff`; 20 conflicts (src0/*.jhyy + workarounds.md + bench.sh + 6 new test files + 4 jhyy_v2..v5.exe + jhyy_stage0.exe); all resolved `--theirs` per user decision 2 (v3 slim workarounds + v3 stdlib + v3 new codegen arch wins) |
| 3 | `c473246` | `chore(version): bump v2.16.0 → v4.0.0 across active source/docs/installer (~22 files)` | 22 files / 81 hits; excluded: `docs/logs/v2/`, `docs/plans/v2/`, `docs/logs/v3/changelog-v3.*`, `docs/plans/v3/v3.0.6-port-...` + `v3.4.0-plan.md`, `scripts/dev/v2_13_8_*.py` + `v2_15_0_*.py`, `compiler/tests/bootstrap/baseline_v2_self/README.md`, `installer/assets/license.rtf` |
| 4 | `b1cf522` | `docs(archive): move invalidated v2/v3 plans to docs/archive/v2-v3/` | per user decision 1: archive (not delete); `v2-v3-parallel-sprint-plan.md` + `v2.0.0-os-prep.md` → `docs/archive/v2-v3/` with README explaining rationale |
| 5 | `3a48fdd` | `docs(readme): full rewrite for v4.0.0 (post-QBE self-backend + stdlib)` | per user decision 4: 432 → 363 lines; badges → v4.0.0 + self-hosted amd64 backend + Windows+Linux; status table reflects v4.0.0 state; roadmap points to v4.1.0..v4.12.0 |
| 6 | (this commit) | `docs: v4.0.0 umbrella changelog + CLAUDE.md version-axis update` | per `feedback_changelog_umbrella`: single umbrella per vX.Y, no standalone changelog-v4.X.Y.md |
| 7 | (later) | `chore(cleanup): remove axis-v2 + axis-v3 worktree/branch (post-v4.0.0 merge)` | per `feedback_batch_worktree_cleanup` triplet |

---

## Files changed summary

| Category | Count | Examples |
|---|---|---|
| Compiler source (jhyy-side authoritative) | 14 | `compiler/src0/*.jhyy` (codegen + new codegen_amd64_emit_sse + new codegen_amd64_xmm_argalloc + new codegen_amd64_inmem + new std/*.jhyy + jhyy_helpers.c) |
| Compiler source (C-side legacy) | 2 | `compiler/src/main.c`, `compiler/src/target/target_dispatch.c` |
| Compiler tests | ~12 | `compiler/tests/examples/{char_literal_3,4byte,fmod_basic,fmod_negative,fmod_f32,cap_table_2reg,cap_test_sysv,conv_test,float_arg_xmm,float_load_store,float_unsigned,slice_iter_nested,xmm_pressure_9args}.jhyy` |
| Bootstrap / verification infra | 4 | `compiler/tests/bootstrap/{fixed_point.sh, mutation-test-report.md, sysv_float_cross.sh, sysv_full_regress.sh}` |
| Installer | ~5 | `installer/{build.ps1, Bundle.wxs, jhyy-compiler.wxs, Locale.zh-CN.wxl, README.md}` |
| Internal docs | 3 | `docs/internal/{architecture.md, build.md, workarounds.md, NEW CLAUDE.md}` |
| ABI / spec | 2 | `docs/abis/{jhyy-lang-spec-v1.3.0.md, jhyy-lang-spec-floatsupplement-v3.3.0.md}` |
| Build infra | 1 | `Makefile` |
| New stdlib | 8 | `compiler/src0/std/{arena,fmt,io,math,mem,os,string,vec}.jhyy` |
| Binaries (tracked artifacts) | ~15 | `compiler/build/bin/{jhyy.exe, jhyy_stage0.exe, jhyy.exe.sha256, jhyy_v5.exe, regress.py, jhyy.il, jhyy_v{2,3,4,5}.il}` |
| Scripts | 6 | `scripts/dev/v2_{13_5_insert_anchors, 13_5_rebuild_index, 13_5_rewrite_workarounds, 13_7_umbrella_split, 13_8_umbrella_append, 15_0_insert_readme}.py` + `scripts/dev/test/run-ovmf.sh` |
| MCP server | 1 | `mcp-jhyy/jhyy_regress.py` |
| Tools | 1 | `tools/fixed_point_summary.py` |
| New archive | 3 | `docs/archive/v2-v3/{README.md, v2-v3-parallel-sprint-plan.md, v2.0.0-os-prep.md}` |
| Existing new (post-merge) | 2 | `README.md` (rewrite) + `CLAUDE.md` (workspace, untracked) + `docs/logs/v4/changelog-v4.0.0.md` (this file) |

---

## Verification gates

Per `v4.0.0-plan.md` lines 62-67:

| Gate | Expected | Actual (post-merge) |
|---|---|---|
| regress.py (C-side `jhyy.exe`) | 104/104 PASS + 4 SKIP | ⏳ (Step 8 post-merge) |
| regress.py (`--binary=jhyy_v1.exe.exe`) | 104/104 PASS + 4 SKIP parity | ⏳ (Step 8 post-merge) |
| `jhyy_selfhost_check` (MCP) | N≥3 byte-equal stable | ⏳ (Step 8 post-merge) |
| D43 final baseline freeze | SHA preserved from v2.16.0 → v4.0.0 closure | ⏳ (Step 8 post-merge) |
| `byte_equal_selfbackend.sh` | 3/3 PASS (fmod_basic / fmod_negative / fmod_f32) | ⏳ (Step 8 post-merge) |
| `bench.sh --report` | first-time baseline accept (--strict ≤ 1.7x FAIL) | ⏳ (Step 8 post-merge) |
| ACTIVE workaround count | 0 (workarounds.md index) | ✅ per v3.4.2 ship state |

If any gate fails → STOP before tag push. Diagnose root cause per `feedback_rca_first_root_cause`; do not bypass with `git commit --no-verify`.

---

## Breaking / notable changes (post-merge cleanup)

1. **Version references unified to v4.0.0** — 22 files had `v2.16.0` strings bumped to `v4.0.0`. Historical `docs/logs/v2/`, `docs/plans/v2/`, `docs/logs/v3/changelog-v3.*`, `docs/plans/v3/v3.0.6-port-...` retained as audit ledger.
2. **Stale plans archived** — `v2-v3-parallel-sprint-plan.md` + `v2.0.0-os-prep.md` moved to `docs/archive/v2-v3/` with README explaining per 2026-09-29 user FINAL decision. The OS M11 launch path predicted by these docs is invalidated and needs v4.x-era redesign.
3. **QBE references purged from user-facing docs** — README.md drops all QBE mentions (except as historical); build.md updates for in-mem self-backend; installer wxs/wxl no longer mention QBE.
4. **WORKAROUND bucket cleared** — v3.4.2 ACTIVE → 0 carries forward to v4.0.0 (per user FINAL 决定). New ACTIVE bucket work in v4.x goes through standard process.
5. **`axis-v2` + `axis-v3` branches + worktrees removed** — `feedback_batch_worktree_cleanup` triplet post-tag-push.

---

## v4.x follow-on plans (⏳)

Per [`docs/plans/v4/v4.X.Y-plan.md`](../../plans/v4/) (14 files: v4.0.0 → v4.12.0):

| Sprint | Intent |
|---|---|
| v4.0.0 | (this ship — axis-v2 + axis-v3 merge) |
| v4.1.0 | M5: delete `compiler/src/*.c` + untrack QBE + delete `runtime/runtime.c` — "jhyy 编 jhyy" 0-C 闭环 (deferred from v1.x) |
| v4.2.0 | async/await + Future runtime |
| v4.3.0 | full lifetime + Polonius borrow check (replaces v3.1.0 NLL stub) |
| v4.4.0 | closure enhance: move/borrow capture/generic/trait object |
| v4.5.0 | const generic `[T; N]` |
| v4.6.0 | trait objects (dyn Trait) + vtable dispatch |
| v4.7.0 | multi-error recovery (parser/sema diagnostic chain) |
| v4.8.0 | basic optimization pass (const fold / dead code / algebra) |
| v4.9.0 | package manager (`jhyy new/build/test` + `jhyy.toml`) |
| v4.10.0 | HKT 1阶 + specialization |
| v4.11.0 | C11/Rust memory model + multi-arch (aarch64/riscv64) Cap<T> ABI |
| v4.12.0 | `.jhyynb` native binary format实装 (DWARF emitter + `--target=jhyy-os` + `jhyy-inspect`) |

Sprint ordering may be re-parallelized (not strictly serial) per dep graph: v4.3 → v4.4 strict; v4.5/v4.6/v4.7/v4.8/v4.9 can open feature worktrees in parallel.

---

## References

- **Authoritative spec**: [`docs/plans/v4/v4.0.0-plan.md`](../../plans/v4/v4.0.0-plan.md) (lines 27-33 + 49 merge + 83-89 commit cadence)
- **Memory**: `project_v2_v3_final.md` (2026-09-29 user FINAL 决定 v2/v3 closure)
- **Self-backend RCA**: `feedback_v3_self_backend_diverges_v2.md` + `feedback_codegen_amd64_run_zerobyte.md` (V3 self-backend bugs真修 in v3.4.x chain)
- **D43 baseline**: `docs/logs/v2/d43-baseline-archive.md` (v2.14.0 N≥10 baseline `43fee332...` HOLD through v4.0.0)
- **Workaround history**: `docs/internal/workarounds.md` (77 RESOLVED + 5 SUPERSEDED + 2 INVALID + 1 permanently deferred)

---

<sub>v4.0.0 umbrella changelog · per `feedback_changelog_umbrella` (single umbrella per vX.Y, no standalone changelog-v4.X.Y.md)</sub>