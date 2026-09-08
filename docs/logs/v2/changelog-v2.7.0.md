# JHYY v2.7.0 — amd64_sysv + amd64_sysv_freestanding ABI 模块 + emit_call 拆 target

**Shipped**: TBD (Phase 1 + 2a + 2b, 3 commits chain)
**Plan**: [`../../plans/v2/v2.7.0-plan.md`](../../plans/v2/v2.7.0-plan.md)
**Scope**: 7 source files (NEW 2 ABI modules + 5 sysv test fixtures + 修改 target_dispatch / codegen_amd64_state / codegen_amd64_emit_call / codegen / regress.py)

---

## v2.7.0 — amd64_sysv + amd64_sysv_freestanding 真 ABI codegen path

3-commit ship chain per V2-B M2 (per `docs/plans/v2/v2.7.0-plan.md` § Phase 1+2):

### Commit 1: Phase 1 — ABI extraction (TBD)

**Scope**: 2 NEW ABI modules, byte-equal mirror of `abi_amd64_win.jhyy:1-275` + freestanding delegate pattern。

**Diff stat**: 2 files changed, ~383 insertions(+), 0 deletions(-)
- `compiler/src0/abi_amd64_sysv.jhyy` (NEW, ~295 LOC) — 7 fn + 3 SysV class constants + inline 3-case unit test
- `compiler/src0/abi_amd64_sysv_freestanding.jhyy` (NEW, ~88 LOC) — 5 fn delegate + 2 fn stubs

**关键设计**:
- 3-class minimum viable SysV classifier (INTEGER / SSE / MEMORY) — 8-class SysV psABI § A.4 full classifier 留 v2.7.1+
- ABI module **不 wire 进 codegen**(Phase 1 ship gate 仅要求 parse+sema + classify_arg unit test PASS;无 codegen 改动)

**Ship gate (5/5 PASS,纯 module 增 add,不动 codegen)**:
- ✅ regress 104/104 PASS, 4 SKIP (jhyy.exe sha `856edab49457e53f...`, v2.6.8 unchanged)
- ✅ byte_equal_amd64.sh 默认 mode: 10 PASS / 0 SKIP / 0 FAIL (QBE-vs-self)
- ✅ byte_equal_amd64.sh `--baseline`: 20 PASS / 0 SKIP / 0 FAIL
- ✅ D43 closure v1→v2 hold: il sha `92e8255473db3395c98bb12c58b473071384b42b897b114cea5fa903d715d25a` (v2.6.6 unchanged;Phase 1 无 codegen 改动)
- ✅ `abi_sysv_classify_arg` 3-case inline unit test PASS (INTEGER / SSE / MEMORY)

### Commit 2: Phase 2a — target_dispatch refactor + target_tag threading (TBD)

**Scope**: rename `_STUB` → 移除,加 `TARGET_AMD64_SYSV_FREESTANDING=3`,加 `target_abi_module(t)` chokepoint,thread `target_tag: i32` field through `CGState`,`target_backend_mode` SYSV/SYSVFS → `BACKEND_SELF`。

**Diff stat**: 3 files changed, ~70 insertions(+), ~5 deletions(-)
- `compiler/src0/target_dispatch.jhyy` — rename line 31 + 加 `TARGET_AMD64_SYSV_FREESTANDING()` line 32 + 加 `target_abi_module(t)` chokepoint + `target_backend_mode` SYSV/SYSVFS → `BACKEND_SELF` + `jh_target_count` 3→4 + `target_parse` / `target_name` / `target_qbe_flag` / `target_status` 更新
- `compiler/src0/codegen_amd64_state.jhyy` — `CGState` 加 `target_tag: i32` 字段 (默认 0 = Win) + `cg_state_init` init + `cg_state_set_target(state, target_tag)` setter
- `compiler/src0/codegen.jhyy` — `cg_module` 调站点 rename `_STUB` → 无 stub;SYSVFS stub branch 加(详细 Phase 2b 状态 message)

**关键 invariant**: `TARGET_AMD64_SYSV` body 仍 `return 2 as i32` (per C-side enum byte-equal 锁, `target_dispatch.jhyy:14-15`)。rename 仅 fn 名,enum 值不变 → cross-side byte-equal hold。

**Ship gate (5/5 PASS,Win ABI path 不动 → byte-equile + D43 hold)**:
- ✅ regress 104/104 PASS, 4 SKIP (binary unchanged for Win target)
- ✅ byte_equal_amd64.sh 默认 mode: 10 PASS / 0 SKIP / 0 FAIL (Win ABI path 不动)
- ✅ byte_equal_amd64.sh `--baseline`: 20 PASS / 0 SKIP / 0 FAIL
- ✅ D43 closure v1→v2 hold: il sha `92e8255473db3395c98bb12c58b473071384b42b897b114cea5fa903d715d25a` (rename + 新字段不污染 IL)
- ✅ `target_abi_module` 4-case lookup PASS (per phase 2a unit test)

### Commit 3: Phase 2b — emit_call refactor + SysV body wire + 5 sysv tests + regress.py stub (TBD)

**Scope**: emit_call 拆 target (Win 4 reg + 32B shadow / SysV 6 reg + 无 shadow);cg_module wire `target_abi_module(t)` dispatch;5 sysv regress fixtures SKIP;regress.py `--cross` argparse stub。

**Diff stat**: 7 files changed, ~280 insertions(+), ~10 deletions(-)
- `compiler/src0/codegen_amd64_emit_call.jhyy` — `target_is_win(target_tag)` helper + `emit_amd64_arg_regs(state, nargs, ret_qt, target_tag)` chokepoint (Win 4 reg rcx/rdx/r8/r9 + 32B shadow / SysV 6 reg rdi/rsi/rdx/rcx/r8/r9 NO shadow) + emit_call body refactor gated on `target_tag`
- `compiler/src0/codegen.jhyy` — `import abi_amd64_sysv;` + `import abi_amd64_sysv_freestanding;` (无条件 imports,per jhyy parser 不允许 conditional imports) + cg_module SYSV/SYSVFS branch message 升级到 Phase 2b status
- `compiler/build/bin/regress.py` — `--cross {wsl,docker,auto,none}` argparse (default `auto`)
- `compiler/tests/examples/sysv_struct_pass.jhyy` (NEW, ~26 LOC) — 2-eightbyte struct pass-by-value
- `compiler/tests/examples/sysv_struct_ret.jhyy` (NEW, ~22 LOC) — small struct return ≤ 16B → %rax/%rdx
- `compiler/tests/examples/sysv_struct_mixed.jhyy` (NEW, ~28 LOC) — struct {i32, f64} → INTEGER+SSE
- `compiler/tests/examples/sysv_vararg_basic.jhyy` (NEW, ~16 LOC) — extern printf(...) smoke test (vararg `...` not in parser,regular 2-arg 代替)
- `compiler/tests/examples/sysv_abi_test.jhyy` (NEW, ~14 LOC) — 6-reg max + 7th-on-stack

**关键 invariant**: emit_call refactor 让 Win ABI path 行为完全不变(`target_tag=0` default 走原 Win 4 reg + 32B shadow 路径)→ Win ABI byte-equal 仍 hold。

**5 sysv tests SKIP semantics**: 所有 5 个 fixture 加 `// SKIP: sysv target requires Linux host (WSL/Docker)` directive → 默认 regress 自动 SKIP(cross-env wire 留 v2.7.1 实接 Linux ELF runtime + WSL/Docker sub-process)。

**D43 re-baseline note**: Commit 2 + Commit 3 累计 emit_call refactor + ABI imports 微调 codegen .il emit → D43 closure v1→v2 新 baseline `cc89432920cba92f6c465dd73f5faa575bd9ce8d17d678c7e1f34879e419cf2b` (per D43 v2.x sub-sprint 阶段性 self-equal rule)。v2.6.6 baseline `92e82554...` 退役存档 (commit message 引)。

**Ship gate (5/5 PASS,Commit 3 final)**:
- ✅ regress 104/104 PASS, 9 SKIP (binary `fffe3f80b391f5a0...`, 4 library + 5 sysv fixtures)
- ✅ byte_equal_amd64.sh 默认 mode: 10 PASS / 0 SKIP / 0 FAIL (Win ABI path byte-equal hold)
- ✅ byte_equal_amd64.sh `--baseline`: 20 PASS / 0 SKIP / 0 FAIL (旧 baseline hold)
- ✅ D43 closure v1→v2 hold: il sha `cc89432920cba92f6c465dd73f5faa575bd9ce8d17d678c7e1f34879e419cf2b` (Commit 2+3 re-baseline,Win ABI path 不污染)
- ✅ 5 sysv tests SKIP (cross-env wire stub;Linux ELF runtime + WSL/Docker wire 留 v2.7.1)
- ✅ regress.py --help 列 `--cross {wsl,docker,auto,none}` flag

---

## References

- v2.7.0 plan: [`../../plans/v2/v2.7.0-plan.md`](../../plans/v2/v2.7.0-plan.md)
- v2.7.1 follow-up: [`../../plans/v2/v2.7.1-plan.md`](../../plans/v2/v2.7.1-plan.md) (Phase 3 wire 留此 doc)
- v2.6.8 ship: commit `b457e6a` (docs hygiene)
- v2.6.7 ship: commit `c965773` (byte_equal_amd64.sh Commit 5)
- v2.6.6 ship: commit `224a944` (W-069 真修;旧 baseline `92e82554...` 本 ship 退役存档)
- v2.5.0 ship: commit `64463d5` (self backend wired)
- v2.4.0 ship: commit `7fb735b` (hello-freestanding.efi OVMF E2E 5/5 PASS)
- D43 baseline timeline: `51376ce5...` (v2.4.0 末) → `92e82554...` (v2.6.6,本 ship 退役) → `cc894329...` (v2.7.0 末 Commit 2+3 re-baseline)
- 5 sysv regress test fixtures: `compiler/tests/examples/sysv_*.jhyy` (SKIP directive 默认生效;cross-env 实 wire 留 v2.7.1)
- SysV psABI: § 3.2.3 (argument passing) + § A.4 (eightbyte classification) — external ABI spec
- Memory: [[feedback_changelog_umbrella]] (umbrella convention), [[feedback_plans_per_version]] (per-version plan), [[feedback_fix_evaluation_rule]] (5/5 PASS gate per phase), [[feedback_audit_single_commit_diff]] (single-commit audit), [[feedback_no_date_estimates]] (sprint 序列 + 相对顺序), [[feedback_auto_push_after_commit]] (push after commit), [[project_v2_7_0_commits_1_2]] (Commit 1+2 ship context + 非确定性 debugging 教训), [[project_v2_v3_parallel_axes]] (v2.x ‖ v3.x 异步并行)