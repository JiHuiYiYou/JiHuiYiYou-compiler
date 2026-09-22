#!/usr/bin/env python3
"""Insert v2.15.0 row in README.md after v2.14.0 row."""
import sys

V215_ROW = """

> **v2.15.0 ship 2026-09-22 on axis-v2 + tag `v2.15.0`** + **main mirror commit** (1 commit ship per worktree per [[feedback_audit_single_commit_diff]]): 🎯 **In-memory self-backend pipeline (skip `.il` file I/O) + `.s` byte-equal D43 closure dual-layer** — **Strategy B+** (per 2026-09-22 user 决定, NOT 原 plan 2026-09-17 "QBE 自写"), plan REWRITE per code reality per [[feedback_doc_refactor_factcheck]]. v2.14.0 ship 后 ACTIVE workaround count = 0;v2.x 末 5 sub-sprint chain 第 4 步 (per [[docs/plans/roadmap/v2-v3-parallel-sprint-plan.md § 5.1]] step 4)。**Phase 1 src0 in-mem entry** (~156 LOC net): `compiler/src0/codegen_amd64_inmem.jhyy` NEW (~131 LOC, `codegen_amd64_run_text(text, len, asm_path, target_tag) -> i32` 7-step orchestration, 复用现有 `lex_il` + `parse_and_emit` (24-way dispatch) + `peephole_fold_with_len` + `jh_write_file`, **0 修改** 9 个 `codegen_amd64_*.jhyy` 文件) + `compiler/src0/main.jhyy` MOD (+25 / -8 LOC: `import codegen_amd64_inmem` + `jh_write_il_enabled()` env gate 默认 0 + `build_il` in-mem dispatch 优先级链 in-mem self > write `.il` + `compile()` skip `run_backend` 当 `build_il` 返回 2) + **W-068 fix #4 unit-type alignment cascade** (if/else 分支都加显式 assignment 避 sema `()` vs `i32` 错) + **W-074.14 NEW → RESOLVED** (v2.15.0 `codegen_amd64_run_text` 直传 text 跳过 `jh_read_file` heap-boxed i64 兜底, supersede W-074.4 family)。**Phase 1c scripts `.s` byte-equal layer** (~55 LOC net): `compiler/tests/bootstrap/fixed_point.sh` MOD (+40 / -5 LOC, `.s` byte-equal 第二层 D43 closure loop + `JHY_FP_BASELINE_S_SHA` env var + warn 1.5x → 1.3x) + `compiler/tests/bootstrap/byte_equal.sh` MOD (+12 / -3 LOC, `.s` from INFO-only → primary closure gate per Strategy B+)。**Phase 2 docs + ship** (~290 LOC across 8 files per [[feedback_changelog_umbrella]] v2.x single umbrella): `docs/internal/build.md` (regress section v2.15.0 in-mem path 注释) + `docs/internal/architecture.md` (§"In-Mem Pipeline" 段) + `docs/internal/workarounds.md` (W-074.14 NEW entry + index line) + `docs/plans/v2/v2.15.0-plan.md` (REWRITE) + `docs/logs/v2/changelog-v2.13.0.md` (v2.15.0 section) + `docs/logs/v2/d43-baseline-archive.md` (v2.15.0 row) + `docs/plans/v2/README.md` (v2.15.0 status row) + `README.md` (本 row)。**6 verification gates V.1-V.6 全绿** per [[feedback_fix_evaluation_rule]]:**V.1 regress 126/147 PASS HOLD** (默认 in-mem path 不变) + **V.2 in-mem `.s` byte-equal to `JHY_WRITE_IL=1` self path** (`216683e18fbb461dbbfc6d57f3f6f1d1616afec250849d9f23d14e279a50058d` byte-equal 跑 hello.jhyy) + **V.3 V2↔V3 `.il` + `.s` 双层 byte-equal closure** (`954a8563...` `.il` + `216683e1...` `.s`) + **V.4 `.s` baseline re-pin 3/3 收敛** (3 次 deterministic `216683e1...`, 写 `JHY_FP_BASELINE_S_SHA` canonical baseline) + **V.5 ACTIVE workaround count = 0** (W-074.14 → RESOLVED, no new ACTIVE) + **V.6 single commit per worktree**。**Key insight 1 (in-mem path = byte-equal with file path)**: `codegen_amd64_run_text` 跟 `codegen_amd64_run` 跑 hello.jhyy + main.jhyy 都产生 byte-equal `.s` (sha `216683e1...` hello / sha `be7ab43c...` main 内部 codegen 阶段也相同) — 证明 file I/O round-trip 是 in-mem 路径 **唯一区别**, 不引入新 codegen 行为差异。**Key insight 2 (Pre-existing lex limitation NOT v2.15.0 regression)**: `codegen_amd64_lexer.jhyy` v2.11.19 B3 fix 对 `data $str657 = { b "...", b 0 }` 中含 `}` 的字符串字面量会 emit 6 个 "unknown QBE IL mnemonic" stderr warnings (per v2.11.19 B3 fix hard-error semantics, caller byte-skip 仍 continue). 这影响 src0/main.jhyy 的 `.s` 输出 (1178435 bytes vs QBE's 2784635 bytes), 但 **inline 跟 file path 行为完全一致** — 不是 v2.15.0 引入的回归; fixed_point.sh setup fails for src0/main.jhyy (gcc can't link incomplete `.s`) 是 pre-existing behavior per [[feedback_codegen_amd64_run_zerobyte]] + [[feedback_codegen_amd64_multifn]]。**scope minimisation per [[feedback_no_artifacts_in_project]] + [[feedback_auto_push_after_commit]]**: src0 改 2 files (`codegen_amd64_inmem.jhyy` NEW + `main.jhyy` MOD) + scripts 2 files + docs 7 files = 12 files touched, **1 commit ship per worktree** (per [[feedback_audit_single_commit_diff]] single-commit diff audit pattern); main mirror commit 同步 8 files (per `0cadfba` precedent; exclude `jhyy.exe` + `jhyy.il` binaries + `~/.claude/plans/` + `compiler/tests/bootstrap/mutation-test-report.md` auto-gen)。**next**: **v2.16.0** = QBE 工具链完全移除 + perf bench ≤ 1.1x C 版 + `.exe` byte-equal 兜底 recipe (`gcc -g0` + `strip` + `SOURCE_DATE_EPOCH` + `-Wl,--build-id=none`) — v2.x 末 第 5 步 ship 后 M5 独立 sprint 启动 (per [[docs/plans/roadmap/v1.x-phase-4-m5-boot-from-scratch.md]]) + v3.x OS-required 等 user 启动 (per [[docs/plans/roadmap/v2-v3-parallel-sprint-plan.md]])。详见 [[docs/plans/v2/v2.15.0-plan.md]] (REWRITE per code reality) + [[docs/logs/v2/changelog-v2.13.0.md]] § v2.15.0 + [[docs/logs/v2/d43-baseline-archive.md]] v2.15.0 row (新 `.s` baseline `216683e1...` pin)。
"""


def main():
    path = 'README.md'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    anchor = 'Linux D43 closure。'
    idx = content.find(anchor)
    if idx == -1:
        print('ERROR: anchor not found')
        sys.exit(1)

    search_from = idx + len(anchor)
    sep_idx = content.find('\n---\n', search_from)
    if sep_idx == -1:
        print('ERROR: section separator not found')
        sys.exit(1)

    new_content = content[:sep_idx] + V215_ROW + content[sep_idx:]

    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    delta = len(new_content) - len(content)
    print(f'Successfully inserted v2.15.0 row. New length: {len(new_content)} (was {len(content)}, +{delta} chars)')


if __name__ == '__main__':
    main()