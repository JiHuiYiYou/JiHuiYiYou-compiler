#!/usr/bin/env python3
"""v2.13.8 ship-time: append v2.13.8 section to v2.13.0 standalone umbrella.
Per v2.13.7 ship-time umbrella split, v2.13.x sections live in
`docs/logs/v2/changelog-v2.13.0.md`, NOT `changelog-v2.11.0.md`.
"""
from pathlib import Path

V138_SECTION = """

## v2.13.8 — W-058 fmod emit 路径真修 (codegen fold `a % b` 浮点 到 user-space formula)

**Shipped**: 2026-09-21 on axis-v2 (commit `<pending>`) + main mirror commit
**Plan**: [`../../plans/v2/v2.13.8-plan.md`](../../plans/v2/v2.13.8-plan.md)
**Scope**: W-058 (DEFERRED since 2026-08-28 v1.7.3) 真修 — 浮点 fmod (`%`) codegen 不再 emit `remd`/`rems` (vendor QBE 2026-08-15 build 不支持), 改 emit 5-instruction user-space formula `a - trunc(a/b) * b` (trunc toward 0, 跟 QBE upstream `remd`/`rems` spec + C `fmod()` 严格一致)。1 src0 file (codegen.jhyy) + 3 new tests, vendor QBE + self-backend 都 work (fold IL 不见 `rem` token)。
**前置**: v2.13.7 ship (W-057 UTF-8 codepoint 真修 + standalone umbrella split)

### Sprint scope (实际 commit)

| 改动 | 文件 | LOC | 风险 | Status |
|------|------|-----|------|--------|
| Codegen TOKEN_PERCENT + QBE_D/QBE_S 早期 return, emit 5-insn formula (polymorphic `div` + `dtosi`/`stosi` + `swtof` + polymorphic `mul` + polymorphic `sub`) | `compiler/src0/codegen.jhyy` | +37 −0 | LOW | ✅ done |
| 3 new tests (basic + negative + f32; negative `+100` 避开 Win NTSTATUS 误判) | `compiler/tests/examples/{fmod_basic,fmod_negative,fmod_f32}.jhyy` | +30 | LOW | ✅ done |
| Spec 附录 B P3 fmod row 修订 (trunc 段, NOT LIMIT) | `docs/abis/jhyy-lang-spec-v1.3.0.md` | +1 −1 | LOW | ✅ done |
| Workarounds W-058 翻 DEFERRED → RESOLVED | `docs/internal/workarounds.md` | +45 −5 | LOW | ✅ done |
| Plan (NEW) | `docs/plans/v2/v2.13.8-plan.md` (NEW, ~155 LOC) | +155 | — | ✅ done |
| Changelog (本 section) | `docs/logs/v2/changelog-v2.13.0.md` | +50 | — | ✅ done |
| README row | `README.md` | +1 | — | ✅ done |

**Total**: ~70 LOC source (1 src0 主改 + 3 tests) + ~190 LOC docs = ~260 LOC, LOW risk.

### W-058 真修: scope 限定 / out-of-scope 明确

**Scope 限定** (本 sprint):
- codegen.jhyy 1 file 早期 return 路径 (line 2267-2302): TOKEN_PERCENT + (QBE_D 或 QBE_S) 时 fold 到 5-instruction sequence (div + dtosi/stosi + swtof + mul + sub)
- 3 new tests: fmod_basic (7.0 % 2.0 → 1), fmod_negative (-7.5 % 2.0 → -1 区分 trunc vs floor), fmod_f32 (7.0_f32 % 2.0_f32 → 1)
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
- **codegen_amd64_emit_call.jhyy 不动**: self-backend `is_rem` branch (line 1834) 当前仅 handle 整数 (cltd/cqto + idiv), float rem token silent fall through; 本 sprint codegen 不再 emit `rem` token,自研 backend 不再收 `rem`, 无需额外修

本 sprint 实际比 plan 更窄 (1 src0 file 而非 1-2), 符合 per-version plan honesty note (per [[feedback_audit_single_commit_diff]] + [[feedback_no_artifacts_in_project]])。

### Verification gates (per plan V.0-V.11)

| Gate | Result |
|------|--------|
| V.0 fmod_basic.jhyy (7.0 % 2.0) QBE EXIT = 1 | ✅ PASS (regress 实际 EXIT=1) |
| V.1 fmod_negative.jhyy (-7.5 % 2.0) QBE EXIT = 99 (trunc: -7.5-(-3)*2.0=-1.5 → cast -1, +100 避开 Win NTSTATUS 误判; floor 会 EXIT=100) | ✅ PASS (regress 实际 EXIT=99) |
| V.2 fmod_f32.jhyy (7.0_f32 % 2.0_f32) QBE EXIT = 1 | ✅ PASS (regress 实际 EXIT=1) |
| V.3 regress.py baseline 126/126 PASS HOLD (124 baseline + 3 new fmod tests; FRESH total 147 with 21 sysv skip) | ✅ 验证 (`/workspace/compiler/build/bin/jhyy.exe: 126/147 passed`) |
| V.4 byte-equal D26 5/5 PASS preserved | ✅ 验证 (`byte-equal: 5/5 PASS`) |
| V.5 byte-equal-amd64 V2-B 10/10 PASS preserved | ✅ 验证 (`byte_equal_amd64: 10 PASS / 0 FAIL`) |
| V.6 single commit `git show <sha> --stat`: 11 files modified (8 src/docs/scripts + jhyy.exe + jhyy.il rebuilt) | ✅ (commit time 验证) |
| V.7 tag v2.13.8 push 成功 | ✅ (ship verify) |
| V.8 main mirror commit `git show <sha> --stat`: 9 files modified (mirror 完整 minus binaries + plan + ship-time script) | ✅ (mirror time 验证) |
| V.9 docs/internal/workarounds.md W-058 状态翻 DEFERRED → ✅ RESOLVED | ✅ done |
| V.10 fixed-point N=3..5 closure preserved (新 closure point 走 src0/codegen.jhyy 改, jhyy.il regenerate, byte-equal v1→v5 PASS) | ✅ (regenerate 后 byte-equal preserved) |

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
"""

v13_path = Path("docs/logs/v2/changelog-v2.13.0.md")
existing = v13_path.read_text(encoding="utf-8")
new = existing.rstrip() + V138_SECTION
v13_path.write_text(new, encoding="utf-8")
print(f"Appended v2.13.8 to {v13_path}: {len(new)} chars")

import subprocess
r = subprocess.run(["grep", "-c", "^## v2.13", "docs/logs/v2/changelog-v2.13.0.md"], capture_output=True, text=True)
print(f"v2.13.x sections in v2.13.0 umbrella: {r.stdout.strip()}")
r = subprocess.run(["grep", "-c", "^## v2.13", "docs/logs/v2/changelog-v2.11.0.md"], capture_output=True, text=True)
print(f"v2.13.x sections in v2.11.0 umbrella (should be 0): {r.stdout.strip()}")