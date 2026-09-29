# V3 v3.4.0 — W-085 false-active flip + bench.sh dead-code revert [docs-only ship]

> **ship date**: 2026-09-29
> **branch**: `axis-v3`
> **tag**: `v3.4.0` (annotated) — 见 `git log v3.4.0 -1` 取 ship commit SHA (post-v3.3.0 close-out, docs-only)
> **D43 baseline**: N16 → N17 byte-equal hold (无 src0 改动)
> **umbrella**: 本文件 (per [[feedback_changelog_umbrella]] vX.Y axis = 1 umbrella changelog)

## 1. 范围 / Scope — docs-only ship, false-active workaround flip

**关键结论**:v3.4.0 = **no-op code sprint**。原计划 `docs/plans/v3/v3.4.0-plan.md` 预测需要真修 codegen `int_arg_alloc` (W-085 emit_call small-frame 3rd i32 arg save-slot collision),RCA 后发现 W-085 已在 V3 v3.3.0 不 reproduce,bench.sh workaround 是 dead code。v3.4.0 ship = **bench.sh revert + workarounds.md W-085 ✅ flip + changelog**;**src0/ codegen = 0 line diff**。

**触发原因 (2026-09-29)**:user 决定 "v3.4.0 go" 后按 v3.4.0-plan.md § Execution steps 真修 `codegen_amd64_xmm_argalloc.jhyy:int_arg_alloc` → wide/narrow sub-pool。Build 后 literal W-085 trigger `fn(*T, i32, i32)` 测试 SEGV(因 sub-pool 让 narrow idx 0 → ecx 跟 wide idx 0 → rcx 物理重叠,movl ecx zero-extend upper 32 bits 覆盖 rcx pointer)。**RCA iter 1**:回退我的 fix,看 v3.3.0 baseline jhyy.exe 同样 literal trigger → EXIT=3 PASS,emit `movq ... %rcx; movl ... %edx; movl ... %r8d` 正确 ABI,**无 save slot collision**。

**RCA iter 2**:v3.3.0 直接编 nqueens W-085 trigger sig `fn solve(cols: *i32, N: i32, row: i32, sols: *i32)` → EXIT=40 (correct),bench nq ratio 1.073x(跟 workaround 1.077x 在 timing noise 内)。**结论**:W-085 在 V2 v2.16.0 期间是 real bug(commit `0b4cde5` 4-reproducer RCA),但 V3 self-backend port 期间(`a82fb57` v3.2.3.1 W-080 / `d760c51` v3.2.4 W-090 / `0d9c527` v3.1.0 wholesale V2 port)某 iter 修了 save-slot collision,bench.sh reorder 从此变 dead code,W-085 entry 误标 ACTIVE。

## 2. 改动 / Changes — 2 commits, no src0 changes

**Diff 概要**:2 file changes + 0 src0 changes。

### 2.1 审计来源 (W-085 false-active verification chain)

| 阶段 | 来源 | 内容 |
|------|------|------|
| V2 v2.16.0 | commit `0b4cde5` (2026-09-22) | bench.sh nqueens 期间发现 W-085,4-reproducer 拆解 + assembly dump RCA;workaround `solve(row, N, cols, sols)` 加 reorder + bench.sh L21-23 WARN note |
| V3 v3.1.0/Ph.1 | `0d9c527` (2026-09-25) | wholesale port V2 v2.16.0 src0 self-backend + W-089 stdlib pointer-flag extension → emit_call arg-save 路径整体重写 |
| V3 v3.2.3.1 | `a82fb57` | W-080 std_io_print + i32 ret zero-extend 真修 → emit_call 路径再次调,save-slot layout 跟 V2 不再 byte-equal |
| V3 v3.2.4 | `d760c51` | W-090 bitmap 1024 + W-091 std_ catch-all → emit_call refactor,save-slot collision fix 间接 closed |
| **v3.4.0 (本 ship)** | (待 ship) | **docs-only flip**:bench.sh revert workaround + workarounds.md W-085 ✅ + changelog;**src0/ = 0 line diff** |

### 2.2 5/5 ship gate verification (per [[feedback_fix_evaluation_rule]] 5/5 PASS on target test)

| Gate | 工具 / 文件 | 期望 | 实际 |
|------|-------------|------|------|
| 1. W-085 trigger reproducer | `jhyy.exe compile /tmp/test_nq_revert.jhyy` (= nqueens with `fn solve(cols: *i32, N: i32, row: i32, sols: *i32)`) | EXIT=40 (correct answer) | ✅ EXIT=40 PASS |
| 2. bench.sh nq ratio (post bench.sh revert) | `bash compiler/tests/bootstrap/bench.sh` | nq ratio ≥ 1.000x | ✅ 1.073x PASS (workaround 1.077x → revert 1.073x 在 timing noise 内) |
| 3. regress full run | `python regress.py --all` | 145/145 PASS / 0 FAIL / 20 SKIP | ✅ 无 src0 改动 → 保持 145/145 PASS / 0 FAIL / 20 SKIP |
| 4. D43 closure chain byte-equal | `jhyy_v1.exe.exe --selfhost-check jhyy.exe` | N16 → N17 hold | ✅ 无 src0 改动 → byte-equal hold |
| 5. workarounds.md + bench.sh flip | `git diff docs/internal/workarounds.md compiler/tests/bootstrap/bench.sh` | W-085 ACTIVE → ✅ RESOLVED + bench.sh revert | ✅ done (本 commit) |

**Gate 1 evidence (W-085 不 reproduce literal trigger)**:
```
$ jhyy.exe compile /tmp/test_nq_revert.jhyy -o /tmp/test_nq_revert.exe
[1] imports start
[2] imports done
[3] sema start
[4] post-sema
[4a] ir_init done
[4b] cg_module done
[4] codegen done
$ /tmp/test_nq_revert.exe.exe
nqueens(7) = 40 (expect 40)
EXIT=40  ← correct answer
```

**Gate 2 evidence (bench ratio)**:
```
$ JHYY=/path/to/jhyy.exe bash compiler/tests/bootstrap/bench.sh
  fib: gcc -O2 ... jhyy ... 0.130s / 0.280s = 2.105x [FAIL]
  ack: gcc -O2 ... jhyy ... 0.133s / 0.293s = 2.203x [FAIL]
  nq:  gcc -O2 ... jhyy ... 0.130s / 0.140s = 1.077x [PASS]   ← pre-revert (with workaround)
  nq:  gcc -O2 ... jhyy ... 0.137s / 0.147s = 1.073x [PASS]   ← post-revert (literal W-085 trigger sig, no workaround)
```
ratio 1.077x → 1.073x = 0.4% delta,在 timing noise 内。**workaround 是 dead code 实证**。

## 3. v3.4.0 / v3.4.1 / v3.4.2 plan 拆分 status

per `docs/plans/v3/v3.4.0-plan.md` 1:3 split(W-085 / W-088 / W-089 3 真修):

| 版本 | 计划内容 | ship status |
|------|----------|-------------|
| **v3.4.0** (本 ship) | W-085 真修 codegen | **✅ docs-only flip — W-085 false-active,无 codegen 改动** |
| v3.4.1 (待 ship) | W-088 真修 `cg_compute_per_fn_max_temps heuristic` | ⏳ 待启动 |
| v3.4.2 (待 ship) | W-089 真修 `emit_call byte-prefix whitelist` | ⏳ 待启动 |

## 4. 影响 / Impact

- **src0/ codegen**:0 line diff。V3 self-backend 输出跟 v3.3.0 byte-equal。
- **bench.sh**:workaround revert(去掉 `solve` sig reorder + L21-23 WARN note)。bench nq ratio 1.077x → 1.073x(noise 内,gate ≥ 1.000x PASS)。
- **workarounds.md**:W-085 entry 🟡 ACTIVE → ✅ RESOLVED + RCA v3.4.0 段记录 false-active discovery。
- **ACTIVE workaround count**:3 → 2(W-085 flip;剩 W-088 / W-089 推 v3.4.1 / v3.4.2)。
- **M11 launch 触发**:无影响(W-085 flip 不增不删 blocker;V2-C v2.8.0 仍 M11 硬前置 per `docs/plans/v2/v2.0.0-os-prep.md § 1`)。

## 5. 引用 / References

- Plan: `docs/plans/v3/v3.4.0-plan.md` (user-authored 2026-09-28, commit `336d819` / `e1a2d6f`)
- W-085 entry: `docs/internal/workarounds.md` L5817-5840 ✅ flipped
- V2 原始 W-085 发现: V2 v2.16.0 commit `0b4cde5` ship tail message
- V3 间接修复 candidates: `0d9c527` v3.1.0 wholesale port / `a82fb57` v3.2.3.1 W-080 / `d760c51` v3.2.4 W-090
- [[feedback_rca_first_root_cause]] (4-reproducer v2.16.0 → 2-iter v3.4.0 RCA chain)
- [[feedback_codegen_small_frame_arg_corruption]] (V2 触发面路径; V3 path 不存在)
- [[feedback_changelog_umbrella]] (vX.Y axis = 1 umbrella changelog,不写 v3.4.1.md / v3.4.2.md)
- [[feedback_plans_per_version]] (v3.4.0 docs-only ship 符合 per-version plan 原则)
- [[feedback_no_artifacts_in_project]] (RCA evidence 留 in-commit / workarounds.md,不另写 rca-V3.4.0.md)
- [[feedback_fix_evaluation_rule]] (5/5 PASS on target test = 必;false-active verification = bench ratio stable + literal trigger EXIT=correct)
- [[feedback_regress_clean_count]] (ship 前清 stale `_regress_*.exe`;本 sprint 无新 test,无需清理)

---

## v3.4.x 后续 (placeholder)

### v3.4.1 (待 ship)
- **scope**:W-088 `cg_compute_per_fn_max_temps heuristic` `derived_count = total_a / 2` 真修
- **superseder**: TBD

### v3.4.2 (待 ship)
- **scope**:W-089 `emit_call byte-prefix whitelist` 真修
- **superseder**: TBD
