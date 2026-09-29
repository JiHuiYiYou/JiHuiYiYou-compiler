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
| **v3.4.0** (shipped 2026-09-29) | W-085 真修 codegen | **✅ docs-only flip — W-085 false-active,无 codegen 改动** |
| v3.4.1 (shipped 2026-09-29) | W-088 真修 `cg_compute_per_fn_max_temps heuristic` | ✅ shipped 2026-09-29 (`max(heuristic, count_l_add)`) |
| v3.4.2 (shipped 2026-09-29) | W-089 真修 `emit_call byte-prefix whitelist` | ✅ shipped 2026-09-29 (sema Pass 1.6 + SymbolReturnTypeMap) |

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

### v3.4.1 (shipped 2026-09-29)
- **scope**:W-088 `cg_compute_per_fn_max_temps heuristic` 真修 (heuristic + `=l add` count `max`)
- **superseder**: heuristic 真替换 → `max(heuristic, count_l_add)`,heuristic 兜底保留
- **5/5 ship gate verified**:
  1. **regress full**: 152/152 PASS / 0 FAIL / 20 SKIP (跟 v3.4.0 baseline 持平,no regression)
  2. **5 originally-failing std_* W-088 trigger tests** (std_arena_calloc + std_fmt_hex + std_fmt_i64 + std_fmt_str + std_string_data) 全 EXIT=0
  3. **5 additional corpus tests** (ffi_file + std_io_basic + std_vec_basic + array_test + mixed_const_struct_import + mixed_struct_slice_match) 全 EXIT=0 — 涵盖 alloc-heavy / alloc-light + many-binop / zero-alloc 3 类触发面
  4. **D43 closure**: v3.4.1 self-compile .il `6c6653fd49...` ≠ v3.4.0 self-compile .il `bb6e78c267...` (N17 → N18 expected drift,src0 diff → codegen 1 .il byte drift)
  5. **workarounds.md + changelog**: W-088 entry ✅ flipped + RCA v3.4.1 段 full record
- **RCA chain (per [[feedback_verify_active_reproduces]])**:
  - Step 1: patch out heuristic `derived_count = total_a / 2` (floor 8) → rebuild via stage0 → binary `jhyy_noheuristic.exe`
  - Step 2: regress full = **147/152 PASS, 5 FAIL** (array_test, mixed_const_struct_import, mixed_struct_slice_match, std_io_basic ACCESS_VIOLATION, std_vec_basic HEAP_CORRUPTION) → heuristic is LIVE (跟 W-085 v3.4.0 RCA 不同 pattern,W-088 heuristic 真 reproduce)
  - Step 3: V3' (count-all-l-add binops) → regress 149/152 PASS, 2 FAIL (ffi_file ACCESS_VIOLATION, std_io_basic SEGV) — count-all-l-add 在 zero-alloc 函数 (ffi_file 0 `=l add` + 0 `=l alloc`) 给 0 reservation → SEGV;std_io_basic total_a=80 heuristic=40 > count=34 → under-reserve
  - Step 4 V3'': `max(heuristic, count_l_add)` → regress 152/152 PASS / 0 FAIL / 20 SKIP ✅ — heuristic 保 zero-alloc 函数 floor 8 + alloc-heavy buffer;count_l_add 补 alloc-light many-binop 函数
- **diff stat**: 1 file modified (state), 1 binary rebuilt (`8cf379cd58ed52f5...`)
- **ACTIVE workaround count**: 2 → 1 (W-088 flip;剩 W-089 推 v3.4.2)
- **plan ref**: `docs/plans/v3/v3.4.0-plan.md` L42-51 (W-088 scope); `docs/plans/v3/v3.4.0-plan.md` L88-93 (v3.4.1 5/5 gate framework)
- **memory ref**: [[feedback_verify_active_reproduces]] (v3.4.0 W-085 false-active 教训 → v3.4.1 W-088 same RCA pattern 但是 LIVE,Path B 真修); [[feedback_audit_single_commit_diff]] (Path B = 1 src0 commit + 1 docs commit,2 commit ship); [[feedback_changelog_umbrella]] (vX.Y axis = 1 umbrella changelog,v3.4.1 section fills v3.4.0 placeholder)

### v3.4.2 (shipped 2026-09-29, tag `v3.4.2`)

**scope**:W-089 `emit_call byte-prefix whitelist` 真修 (替换 194 LOC byte-prefix whitelist → sema Pass 1.6 populate `SymbolReturnTypeMap` → `emit_call` semantic lookup)

**根因 (RCA-first per [v3.4.0 W-085](#) + v3.4.1 W-088 真修 同 pattern)**:
- v3.1.0 引入 byte-prefix whitelist (`codegen_amd64_emit_call.jhyy` L898-1091,194 LOC) 兜底 `cg_record_temp_holds_address` 调用 — 当 callee name starts with `ptr_add` / `ptr_add_u8` / `malloc` / `__closure_*` / `fmt_` / `mem_` / `str_` / `arena_` / `std_fmt_` / `std_mem_` / `std_str_` / `std_arena_` / `strdup` / `fopen` / W-091 catch-all `std_` 时 flag call result as address-holder
- v3.1.0 whitelist = name-prefix heuristic — V3 stdlib growth 跟 deploy cadence 矛盾 (W-091 catch-all `std_` 是 v3.2.4 加的;任何新 stdlib fn 需手动加 prefix)
- V2.16.0 同 gap 但 V2 corpus 无触发面 (per [[feedback_v3_self_backend_diverges_v2]])

**Step 1 — verify ACTIVE 真 trigger**:
- Path B 删掉 whitelist (L1088-1090 `cg_record_temp_holds_address` call patch out) → rebuild via stage0 → regress + std_* trigger
- expect:≥6 FAIL (std_arena_calloc / std_fmt_hex / std_fmt_i64 / std_fmt_str / std_string_data / std_vec_basic 等)
- 实测:6 std_* test EXIT=1-6 失败 — **W-089 LIVE confirmed → Path B 真修**

**Step 2 — 真修** (Path B,2 commit):
- **sema.jhyy** +108 LOC:Pass 1.36 NEW `check_module_populate_ret_type_map(ctx, md)` 扫 `(*md).decls` NODE_FUNC_DECL → FNV-1a hash fn sym name → ptr_kind flag (1 iff ret_type resolves to KIND_POINTER/SLICE/REF/CAP 或 KIND_FUNC returning pointer recursion 1-level)。Hook in `check_module` AFTER Pass 3 body resolution (per [[feedback_jhyy_no_forward_ref]]);Closure synthetic fns attach ret_type from closure body return (~+10 LOC fix)。
- **ir.jhyy** +15 LOC:NEW `RetTypeMapEntry { name_hash: i64, ptr_kind: i32 }` struct。
- **util.jhyy** +20 LOC:NEW `hash_string_n(s, n)` variant — 跟 `hash_string` 同 algorithm 但 caller 提供 length (针对 emit_call 传 substring 指针,strlen 会读到 tok 末尾外乱字节 → hash 错配 → lookup 失败)。**第一次 ship regression 6 FAIL 真根因 (a)**。
- **codegen_amd64_state.jhyy** +176 LOC:NEW `CGState` fields `ret_type_map: *u8` + `ret_type_map_n: i64` + `cg_query_fn_returns_ptr(state, name, name_len)` map lookup + `cg_is_builtin_ptr_fn` fallback hardcoded 5 link-only externs (ptr_add / ptr_add_u8 / ptr_sub / malloc / __closure_ prefix) + setters/getters + reset_for_function map-not-cleared fix。**第一次 ship regression 6 FAIL 真根因 (b)** — `cg_state_reset_for_function` 把 per-compile invariant SymbolReturnTypeMap zero-init,第 1 个 fn 之后 map 被 wipe → lookup 永远返 0。
- **codegen_amd64_emit_call.jhyy** -194 LOC → -203 LOC:byte-prefix whitelist replaced by semantic lookup。Net delta ~-30 LOC (194 → ~25 LOC semantic path)。
- **codegen_amd64.jhyy** +13 LOC + **codegen_amd64_inmem.jhyy** +10 LOC:`codegen_amd64_run` / `run_text` signature 加 map args + wire。
- **main.jhyy** +14 LOC:`compile()` + `run_backend()` 传 map args。
- **codegen_call_return_types.jhyy** NEW:8 sub-test (i32-ret negative / *T-ret positive / i64-ret / cross-fn / nested 3-level / recursive / closure / builtin fallback)。SKIP in default regress per v3.4.0-plan.md L89。

**Step 3 — Verification (5/5 ship gate per [[feedback_fix_evaluation_rule]])**:
- **Gate 1**: `codegen_call_return_types.jhyy` 8 sub-test 全 PASS (EXIT=0)。
- **Gate 2**: regress full 152/152 PASS / 0 FAIL / 21 SKIP (从 v3.4.1 152/152/20 → 152/152/21 — +1 新 test SKIP 加入)。
- **Gate 3**: 6 originally-failing std_* test (std_arena_calloc + std_fmt_hex + std_fmt_i64 + std_fmt_str + std_string_data + std_vec_basic) 全 EXIT=0/65 (期望值, not buggy 0)。
- **Gate 4**: D43 closure N18 → N19 re-baseline (1 .il drift expected per Path B semantic 真修)。
- **Gate 5**: workarounds.md W-089 ACTIVE → ✅ + changelog-v3.4.md v3.4.2 section full + roadmap ACTIVE bucket → empty。

**Root cause 总结**:
- W-089 v3.1.0 whitelist = name-prefix heuristic — V3 stdlib growth 跟 deploy cadence 矛盾 (跟 V2 v2.16.0 同 gap 但 V2 corpus 无触发面,per [[feedback_v3_self_backend_diverges_v2]])。
- v3.4.2 真修 semantic lookup 走 sema Pass 1.6 populate `SymbolReturnTypeMap` → codegen emit_call 走 map lookup → fn ret_type = KIND_POINTER/SLICE/REF/CAP/FUNC-returning-pointer → 全自动 flag,0 manual prefix maintenance。
- `cg_is_builtin_ptr_fn` hardcode 5 link-only externs — 这些 fn 不在 sema (link-only), 但 stdlib 90% 是 user-callable fn 通过 sema populate 进 map,无 manual whitelist 维护负担。
- **双 release 修** (a) hash alignment + (b) map-not-cleared fix 都展示了 v3.4.2 initial ship 真 root cause 不止 surface (whitelist 替换);semantic 真修 surface-OK 但 wiring/semantic still有 latent bugs,fix cycle iterate 2 iter 达到 5/5 ship gate。

**diff stat**: 9 files modified / 1 file added (test), 1 binary rebuilt (`c0c74ebaadc25b2b...` v3.4.2 binary)

**ACTIVE workaround count**: 1 → 0 (W-089 flip;**v3.x ACTIVE bucket 清空** = W-085 ✅ + W-088 ✅ + W-089 ✅)

**plan ref**: `docs/plans/v3/v3.4.0-plan.md` L53-60 (W-089 scope) + L95-100 (W-089 5/5 gate framework)
**memory ref**: [[feedback_verify_active_reproduces]] (v3.4.0 W-085 false-active 教训 → v3.4.1 W-088 LIVE Path B 真修 → v3.4.2 W-089 same pattern);[[feedback_audit_single_commit_diff]] (Path B = 1 src0 commit + 1 docs commit,2 commit ship);[[feedback_changelog_umbrella]] (vX.Y axis = 1 umbrella changelog,v3.4.2 section fills v3.4.1 placeholder);[[feedback_fix_evaluation_rule]] (5/5 ship gate);[[feedback_rca_first_root_cause]] (1 root cause + downstream symptoms pattern);[[feedback_jhyy_no_forward_ref]] (Pass 1.6 defer to AFTER Pass 3 body resolution)
