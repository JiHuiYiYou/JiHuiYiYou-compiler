# JHYY v2.9.0 — N≥3 selfhost fixed point 验算 + verification harness (V2-C Part 1)

**Shipped**: TBD (1 source commit + 1 docs commit)
**Plan**: [`../../plans/v2/v2.9.0-plan.md`](../../plans/v2/v2.9.0-plan.md)
**Scope**: 1 NEW shell script + 1 NEW python tool + regress.py opt-in flag + docs
**前置**: v2.8.3 ship (`--no-link` flag + docker gcc chain 5/5 sysv PASS + W-070 真修)

---

## v2.9.0 — V2-C Part 1: N≥3 closure 验算 harness (加能力,不动 codegen)

2-commit ship chain per V2-C (per `docs/plans/v2/v2.9.0-plan.md` § Phase 1+2):

### Commit 1: src0 revert to axis-v2-pre-merge baseline (per 2026-09-08 user decision)

**Scope**: 14 src0 files restored from `archive/axis-v2-pre-merge` after additive axis-v3 merge (commit `0f9c923`) broke jhyy_stage0.exe binary compatibility:
- jhyy-side added NodeFuncDecl.is_naked (V3-B v3.0.2 3b naked) + NodeFuncDecl +16B type_params (V3-C v3.1.0 3g) + NodeCall +16B type_args (V3-C 3i call-site inference)
- C-side `sema.c:1281` 仍按旧 NodeFuncDecl offset 解 `fd->sym->kind` → segfault on src0/main.jhyy compile

**Diff stat**: 14 files changed, ~4400 insertions(+), ~140 deletions(-) (revert to v2.8.3-baseline content)
- `compiler/src0/abi_amd64_win.jhyy`
- `compiler/src0/ast.jhyy`
- `compiler/src0/bootstrap/v1.0/_driver_ast_3c.jhyy`
- `compiler/src0/codegen.jhyy`
- `compiler/src0/codegen_amd64.jhyy`
- `compiler/src0/codegen_amd64_emit_call.jhyy`
- `compiler/src0/codegen_amd64_state.jhyy`
- `compiler/src0/ir.jhyy`
- `compiler/src0/jhyy_helpers.c`
- `compiler/src0/lexer.jhyy`
- `compiler/src0/main.jhyy`
- `compiler/src0/parser.jhyy`
- `compiler/src0/sema.jhyy`
- `compiler/src0/types.jhyy`

**关键决策**:
- axis-v3 content (V3-C 3g borrow check + V3-C 3g.5 CapTable<T> + V3-C 3g.7 NLL + V3-B 3c volatile + V3-B 3b naked + V3-B 3i call-site inference) 由 v3 axis owner 在 split 时重 apply — 不在本 batch 范围
- v2.9.0 ship 时 src0 = `archive/axis-v2-pre-merge` 内容 (v2.8.3 baseline)
- jhyy.exe.sha256 refresh: `780eb55e...` → `580030a8...` (新 stage0 build 后)

**Ship gate (5/5 PASS,纯 unmerge 不动 codegen 行为)**:
- ✅ regress 5 main tests (Win): 5/5 PASS (`hello.jhyy` EXIT=42, `struct_val_pass.jhyy` EXIT=35, `fib_renamed.jhyy` EXIT=832040, `nested_struct_deep.jhyy` EXIT=22, `big_test.jhyy` EXIT=12345)
- ✅ byte_equal_amd64.sh 默认: 10/10 PASS (5 tests × 2 files = 10 PASS)
- ✅ D43 closure v1→v2 sha HOLD `7aebc1b62ad8b139...` (v2.9.0 新 baseline,per Commit 1 src0 改 → D43 re-baseline; archive per `d43-baseline-archive.md`)
- ✅ `make` rebuild 成功 (jhyy.exe 596973 bytes → sha `580030a8...`)
- ✅ `jhyy.exe.sha256` sha256sum -c OK (phantom-binary hazard 消除)

### Commit 2: Phase 1+2 — fixed_point.sh + regress.py --fixed-point + summary + docs

**Scope**: 1 NEW shell script (~210 LOC) + 1 NEW python tool (~110 LOC) + regress.py opt-in flag (~30 LOC) + docs (~150 LOC across 4 files)

**Diff stat**: 4 files changed, ~300 insertions(+), ~5 deletions(-)
- `compiler/tests/bootstrap/fixed_point.sh` (NEW, ~210 LOC) — N≥3 selfhost closure 验算 harness
- `tools/fixed_point_summary.py` (NEW, ~110 LOC) — human-readable markdown summary
- `compiler/build/bin/regress.py` (~30 LOC) — `--fixed-point` flag + `test_fixed_point()` function 跟 `test_byte_equal()` 同 pattern
- `docs/logs/v2/d43-baseline-archive.md` (~5 LOC) — append v2.9.0 re-baseline row

**关键设计**:
- **N=3 是 ship gate**(primary invariant per D43);N=4/N=5 是 informational (试更长链 closure)
- **v3 binary 自动 cp 到 project root 的 compiler/build/bin/jhyy_v3_fp.exe.exe**(jh_paths_init 走 dirname × 4 找 qbe.exe,放 /tmp/ 跑会 "cannot derive project root from argv[0]")
- **cap_test 跨代一致**(per V3-C v3.1.0 ship):exit 跨 v1/v2/v3 必须一致(隐含 borrow check + 8 字节 Cap<T> layout 决策一致)。axis-v2 branch 上 cap_test.jhyy 是 SKIP (V3-C only feature),v3 axis owner split 后 v3 才跑
- **--no-link flag** 仅 v2.8.3+ binary 支持,jhyy_v1.exe.exe (v2.5.0 frozen) 不支持 → script 默认 compile 拿 .il sidecar

**fixed_point.sh output** (verified 2026-09-08):
```
[setup] ✅ v3.exe built (596973 bytes)
[1/3] IL closure N=3 (D43 ship gate, primary):
  v1=7aebc1b62ad8b1398d42bff30bdd56b25679ccfc1fb66fc9355be0bd6a43a6a3
  v2=7aebc1b62ad8b1398d42bff30bdd56b25679ccfc1fb66fc9355be0bd6a43a6a3
  v3=7aebc1b62ad8b1398d42bff30bdd56b25679ccfc1fb66fc9355be0bd6a43a6a3
  ✅ PASS (N=3 .il byte-equal)
[4/5] IL closure N=4 (informational):
  v3=7aebc1b62ad8b1398d42bff30bdd56b25679ccfc1fb66fc9355be0bd6a43a6a3
  v4=7aebc1b62ad8b1398d42bff30bdd56b25679ccfc1fb66fc9355be0bd6a43a6a3
  ✅ PASS (N=4 .il byte-equal)
[5/5] IL closure N=5 (informational):
  v4=7aebc1b62ad8b1398d42bff30bdd56b25679ccfc1fb66fc9355be0bd6a43a6a3
  v5=7aebc1b62ad8b1398d42bff30bdd56b25679ccfc1fb66fc9355be0bd6a43a6a3
  ✅ PASS (N=5 .il byte-equal)
[cap_test] SKIP (V3-C only, axis-v2 branch 无 Cap<T> builtin)
=== fixed-point 结果: 4 PASS / 0 FAIL / 0 INFO ===
```

**Ship gate (5/5 PASS + 5/5 fixed_point)**:
- ✅ Commit 1 ship gate 持平 (5/5)
- ✅ **fixed_point.sh N=3 PASS** (新 ship gate, primary per D43)
- ✅ **fixed_point.sh N=4 PASS** (informational, 也 hold 说明 closure stable)
- ✅ **fixed_point.sh N=5 PASS** (informational, 5 代 closure 验证)
- ✅ fixed_point.sh cap_test 跨代 SKIP (V3-C gated, axis-v2 SKIP 正确)
- ✅ regress.py `--fixed-point` flag 集成,exit 0 on N=3 PASS
- ✅ fixed_point_summary.py 输出 markdown 表格 (进 changelog)
- ✅ D43 closure v1→v2 hold `7aebc1b62ad8b139...` (新 baseline 写进 d43-baseline-archive.md)
- ✅ docs 一致性: README status row + architecture N=3 closure re-verified + workarounds verification 注释

## 后续

**V2-C 后续 sub-sprint** (per `docs/plans/v2/v2.10.0-plan.md`):
- v2.10.0 = QBE 工具链完全移除 + toolchain self-contained closure (Part 2+3)
- v2.10.0 ship 后 → M5 deferral 第二前置全部达成 → M5 可独立 sprint 启动 (删 `src/*.c` + untrack QBE + 删 `runtime.c` 完成"jhyy 编 jhyy" 0 C 依赖闭环)

**v3 axis split**:
- axis-v3 owner 从 `archive/axis-v3-pre-merge` (tag `980c026`) 重分 axis-v3 branch
- axis-v3 owner 把 v3.0.0 3a-3f + V3-A + V3-B + V3-C 整个 batch 在 v3 branch 上 ship
- v3 owner 负责 cap_test.jhyy cross-gen 验证(本 changelog cap_test SKIP 由 axis-v2 owner 标注,v3 owner ship 时跑)

## References

- v2.9.0 plan: [`../../plans/v2/v2.9.0-plan.md`](../../plans/v2/v2.9.0-plan.md)
- v2.10.0 plan (后续): [`../../plans/v2/v2.10.0-plan.md`](../../plans/v2/v2.10.0-plan.md)
- v2.8.3 ship: tag `v2.8.3`, 2026-09-08 — `--no-link` flag + docker gcc chain
- v1.0.0 真自举 byte-equal: tag `9b05c0f` / commit `eabee0d`, sha `2445e97d...`
- D43 closure baseline archive: [`docs/logs/v2/d43-baseline-archive.md`](d43-baseline-archive.md)
- M5 deferral: [`../../plans/v1/v1.x-phase-4-m5-boot-from-scratch.md`](../../plans/v1/v1.x-phase-4-m5-boot-from-scratch.md)
- Memory: [[feedback_plans_per_version]], [[feedback_changelog_umbrella]], [[feedback_fix_evaluation_rule]], [[feedback_regress_baseline_binary_hash]], [[feedback_no_artifacts_in_project]], [[feedback_auto_push_after_commit]]