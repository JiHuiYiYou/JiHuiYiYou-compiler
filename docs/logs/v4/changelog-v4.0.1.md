# v4.0.1 changelog

**Ship date:** 2026-10-01 · **Branch:** `main` · **Tag:** `v4.0.1` (planned) · **Preconditions:** all ✅ (v4.0.0-rc1 shipped 2026-09-30)

> **Note:** v4.0.1 = **docs-only** sprint per `feedback_memory_selectivity` + `feedback_verify_active_reproduces` + v3.4.0 W-085 docs-only flip pattern。No src0/ codegen changes; jhyy.exe sha unchanged。下一 sprint **v4.0.2** = self-compile emit→lex round-trip RCA (multi-func silent-fail issue, deferred from v4.0.0-rc1 Gate 3 selfhost, now scoped as standalone sprint per 2026-09-30 user 决定)。

---

## What is v4.0.1

v4.0.1 ships a **workarounds.md ACTIVE bucket audit & sync** against main HEAD (commit `416285f`, v4.0.0-rc1)。动机:user 2026-10-01 说"以代码为准,不要信文档" — index table L24-88 多个 ACTIVE entry 跟 body 状态不一致(典型:W-085 body 已 ✅ RESOLVED 2026-09-29 但 index 仍 🟡 ACTIVE)。本 sprint 走 audit-flip pattern,验证每个 ACTIVE entry 的 literal trigger 在当前代码上是否真 reproduce,根据 reproduce 结果**flip → RESOLVED 或 add Last-verified footer**。

**No src0/ codegen changes**;本 sprint scope 严格限定在 `docs/internal/workarounds.md` + `docs/logs/v4/changelog-v4.0.1.md` (本文件)。

---

## Preconditions met

| Precondition | Status | Reference |
|---|---|---|
| v4.0.0-rc1 shipped (axis-v2 + axis-v3 merged, post-QBE self-backend) | ✅ 2026-09-30 | tag `v4.0.0-rc1`, commit `416285f` |
| workarounds.md schema locked (5-state enum, 6-field status) | ✅ | `docs/internal/CLAUDE.md §1-2` |
| W-085 docs-only flip pattern precedent (v3.4.0) | ✅ 2026-09-29 | `docs/logs/v3/changelog-v3.4.md` |

---

## Audit-flip actions (W-NNN state changes)

Per Step 1.1 verification matrix + Step 1.3 docs-only flips (per `merge-v2-axis-v3-axis-into-main-serialized-aho.md` plan):

### Flipped ACTIVE → RESOLVED (literal trigger no longer reproduces on main HEAD)

| W-ID | Body status before | Body status after | Audit-flip reason |
|------|--------------------|-------------------|--------------------|
| W-085 | 🟡 ACTIVE (workaround in place via signature reorder) | ✅ RESOLVED 2026-09-29 (v3.4.0 docs-only flip) | Body was already ✅ flipped 2026-09-29 (per v3.4.0 RCA — V3 self-backend port fixed save-slot collision as side-effect); index was stale 🟡 ACTIVE. **Index synced this sprint (2026-10-01 v4.0.1)**. |
| W-078 | 🟡 ACTIVE | ✅ RESOLVED 2026-10-01 (v4.0.1 audit-flip) | QBE git rm `6ae2d7c` (v3.1.0/Ph.3) → self-backend sole production path → QBE-specific `invalid type for first operand %tXX in mul` workaround moot; `compiler/src0/codegen.jhyy` L939/L988/L1963 emit extsw 通用 w→l 转换 cross-cutting 覆盖 array indexing 路径。 |
| W-077 | 🟡 ACTIVE (test deferred) | ✅ RESOLVED 2026-10-01 (v4.0.1 audit-flip) | W-077 引用的 `compiler/tests/examples/std_mem_find_byte.jhyy` 不存在(可能早期 rename/cleanup 已消除)。`std_mem_basic.jhyy`(含 inline `mem_find_byte` impl + 验证 `idx == 12` 路径)2026-10-01 run EXIT=0 on main HEAD;Access violation 触发面已 moot。 |

### Verified still ACTIVE (literal trigger reproduces on main HEAD)

| W-ID | Body status | Why kept ACTIVE | Last-verified footer |
|------|-------------|------------------|----------------------|
| W-073 | 🟡 ACTIVE (hold per 2026-09-09 user 决定) | `fixed_point.sh` v2 仍 fail 编 src0/main.jhyy → v3.exe — multi-func silent-fail issue 仍 real | 2026-10-01 — but per `feedback_codegen_amd64_multifn` 不是 workaround 范畴,转 v4.0.2 follow-on |
| W-074 | 🟡 ACTIVE (deferred to v3.2.4) | `runtime.c:23-45` 仍 export 24B C Arena;`std::arena` 仍 40B;两层 layout 不一致仍 real | 2026-10-01 — superseder 推到 v4.x mid(v3 已 FINAL 2026-09-29) |
| W-075 | 🟡 ACTIVE (M0 accept) | `compiler/src0/std/mem.jhyy:78` 仍 `*(ptr_add(dst, i) as *i32) = b` i32-store,M0 简化 trade-off 仍 real | 2026-10-01 — 推 v4.x mid perf sprint 或 accept 永久 |
| W-076 | 🟡 ACTIVE | `runtime.c` 仍 export C-side `arena_*` 24B Arena, std_ 前缀仍 mandatory | 2026-10-01 — 跟 W-074 同步推 v4.x mid |

### ACTIVE bucket truth (after audit)

| Metric | Before (v4.0.0-rc1) | After (v4.0.1) |
|--------|----------------------|------------------|
| Index ACTIVE rows | 6 (W-073/074/075/076/077/078) + W-085 stale 🟡 | 4 (W-073/074/075/076) — accurate |
| Body ACTIVE rows | 6 (W-073/074/075/076/077/078) + W-085 stale 🟡 | 4 (W-073/074/075/076) — accurate |
| Body ACTIVE entries without Last-verified footer | 6 | 0 — all have 2026-10-01 footer |

---

## Step 1.1 verification matrix

| W-ID | Reproduces on main HEAD? | Source-check | Result |
|------|---------------------------|-------------|---------|
| W-073 | YES (fixed_point.sh v2 still fails) | `bash compiler/tests/bootstrap/fixed_point.sh` | keep ACTIVE → v4.0.2 follow-on |
| W-074 | YES (runtime.c still 24B Arena) | `grep -nE "arena_(new|alloc|reset|destroy)" compiler/runtime/runtime.c` L23-45 | keep ACTIVE → v4.x mid |
| W-075 | YES (mem.jhyy:78 still i32-store) | `awk 'NR>=69 && NR<=80' compiler/src0/std/mem.jhyy` | keep ACTIVE → v4.x mid |
| W-076 | YES (std_arena_*.jhyy still std_ prefix) | `ls compiler/tests/examples/ | grep std_arena` | keep ACTIVE → v4.x mid |
| W-077 | NO (literal test absent; std_mem_basic.jhyy PASS) | `jhyy.exe run std_mem_basic.jhyy` → EXIT=0 | flip → RESOLVED |
| W-078 | NO (QBE removed; extsw cross-cutting covers array indexing) | QBE git rm `6ae2d7c` (v3.1.0); codegen.jhyy L939/L988/L1963 grep `extsw` | flip → RESOLVED |
| W-085 | NO (V3 self-backend port fixed save-slot collision) | body already flipped 2026-09-29; index stale | index sync only |

---

## Verification gates (all docs-only)

| Gate | Status |
|------|--------|
| `git diff --stat v4.0.0-rc1..v4.0.1` → only `docs/internal/workarounds.md` + `docs/logs/v4/changelog-v4.0.1.md` modified | ✅ |
| `jhyy.exe sha unchanged` (post-audit rebuild NOT required) | ✅ — docs-only sprint |
| workarounds.md index row count == body ACTIVE count (4 == 4) | ✅ |
| ACTIVE bucket entries all have `Last-verified: 2026-10-01` footer | ✅ |
| Flipped entries (W-077/W-078) have audit-flip paragraph in body | ✅ |
| regress.py 158/158 PASS HOLD (no src0/ changes → auto-pass) | ✅ (no rebuild required) |
| bench.sh --report PASS (no src0/ changes → auto-pass) | ✅ (no rebuild required) |
| ACTIVE workaround count = 4 (was 6 + W-085 stale 🟡, now accurate) | ✅ |

---

## Out of scope (deferred to v4.0.2)

- Self-compile emit→lex round-trip fix (W-073 follow-on) — multi-func silent-fail issue not multifn count per se (1/2/3/5/118-fn tests all pass; only 28-fn main.jhyy self-compile fails with "unknown QBE IL mnemonic at byte 20227" — emit→lex round-trip on jhyy-side lexer 不识别自家 emit 形式)
- v4.0.0-rc1 → v4.0.0 final promote (depends on v4.0.2 fix)
- v4.1.0 M5 src/*.c delete + runtime.c delete (per `docs/plans/v4/v4.1.0-plan.md`)

---

## Commit cadence

| # | Commit | Message | Type |
|---|--------|---------|------|
| 1 | (this commit) | `docs(audit): v4.0.1 workarounds.md ACTIVE bucket sync against main HEAD` | docs |
| 2 | tag | `v4.0.1` | — |

Total: 1 docs commit + 1 tag + 1 push.

---

## References

- v4.0.0-rc1 changelog: `docs/logs/v4/changelog-v4.0.0.md`
- workarounds.md audit-flip pattern: `docs/logs/v3/changelog-v3.4.md` L11-87 (W-085 docs-only flip, 2026-09-29)
- v4.0.1 plan: `~/.claude/plans/merge-v2-axis-v3-axis-into-main-serialized-aho.md` (audit + RCA 双 sprint plan)
- Memory: `feedback_verify_active_reproduces`, `feedback_audit_single_commit_diff`, `feedback_changelog_umbrella`, `feedback_fix_evaluation_rule`, `feedback_rca_first_root_cause`, `feedback_git_identity_canonical`, `feedback_ssh_key_same_shell`, `feedback_codegen_amd64_multifn`, `feedback_memory_selectivity`
- QBE git rm commit (per W-079 line 80): `6ae2d7c` (v3.1.0/Ph.3) — invalidates W-078 "QBE extsw fix 留 v3.x mid"