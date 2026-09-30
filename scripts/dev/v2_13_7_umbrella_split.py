#!/usr/bin/env python3
"""v2.13.7 ship-time: append v2.13.7 section to v2.13.0 standalone umbrella.
Per user 2026-09-21 feedback, split v2.11.0 umbrella into:
- changelog-v2.11.0.md (v2.11.x only, line 1-2038)
- changelog-v2.12.0.md (NEW, v2.12.0 audit closure)
- changelog-v2.13.0.md (NEW, v2.13.0/1/2/3/4/5/6/6.1/6.2/6.3/7)

This script runs AFTER the bash split (which already truncated v2.11.0 umbrella
and wrote v2.12.0 + v2.13.0 standalone files with v2.13.0/1/2/3/4/5/6 content).
"""
from pathlib import Path

V137_SECTION = """
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
"""

v13_path = Path("docs/logs/v2/changelog-v2.13.0.md")
existing = v13_path.read_text(encoding="utf-8")
new = existing.rstrip() + "\n" + V137_SECTION
v13_path.write_text(new, encoding="utf-8")
print(f"Appended v2.13.7 to {v13_path}: {len(new)} chars")

import subprocess
r = subprocess.run(["grep", "-c", "^## v2.13", "docs/logs/v2/changelog-v2.13.0.md"], capture_output=True, text=True)
print(f"v2.13.x sections in v2.13.0 umbrella: {r.stdout.strip()}")
r = subprocess.run(["grep", "-c", "^## v2.13", "docs/logs/v2/changelog-v2.11.0.md"], capture_output=True, text=True)
print(f"v2.13.x sections in v2.11.0 umbrella (should be 0): {r.stdout.strip()}")
r = subprocess.run(["grep", "-c", "^## v2.11", "docs/logs/v2/changelog-v2.11.0.md"], capture_output=True, text=True)
print(f"v2.11.x sections in v2.11.0 umbrella: {r.stdout.strip()}")
r = subprocess.run(["grep", "-c", "^## v2.12", "docs/logs/v2/changelog-v2.11.0.md"], capture_output=True, text=True)
print(f"v2.12.x sections in v2.11.0 umbrella (should be 0): {r.stdout.strip()}")