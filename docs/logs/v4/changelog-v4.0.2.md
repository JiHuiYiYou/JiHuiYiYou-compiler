# v4.0.2 changelog (DRAFT — partial ship)

**Ship date:** TBD · **Branch:** `main` · **Tag:** `v4.0.2` (planned) · **Preconditions:** all ✅ (v4.0.1 docs-only shipped 2026-10-01)

> **Note:** v4.0.2 = **ACTIVE bucket → 0 + GHA 修通 + promote v4.0.0 final prerequisite**。本 changelog 当前 **partial ship**:Step 2.4 GHA 修通 4 commits 已 land(`64871dc` `a19447e` `4a6ebd1` `448de0a`)。剩余:Step 2.1 W-073 emit escape 真修 + Step 2.2 W-074/076 runtime.c rename + (optional) Step 2.3 W-075 mem_set i64-store + 验证门 + tag v4.0.2。Promote v4.0.0 final = v4.0.3 (separate ship)。

---

## What is v4.0.2 (current scope)

v4.0.2 ships:
1. **GHA 修通** — ci.yml + release.yml 自 v4.0.0-rc1 (2026-09-30) 以来从未绿过,5 个 bug 全 fixed;本 step 已 ship ✓
2. **W-073 emit escape 真修** — self-compile `src0/main.jhyy` 失败根因 = QBE IL emit path 字符串 escape 编码 bug(不是 multi-func silent fail)
3. **W-074/076 runtime.c rename** — `arena_*` → `c_arena_*` namespace 隔离
4. **W-075 mem_set i64-store** (optional) — perf 优化

v4.0.2 是 **v4.0.0 final promote 的强前置**。Per 2026-10-01 user 决定:"v4.0.0 tag放在所有workaround清零和修复CI release之后"。

---

## Step 2.4 — GHA 修通 (✅ shipped 2026-10-02)

Per `merge-v2-axis-v3-axis-into-main-serialized-aho.md` GHA RCA,5 个 bug 全部 fixed in 4 commits:

| Bug | Severity | Fix commit | Detail |
|-----|----------|-----------|--------|
| **#1 qbe/ source untracked** | CRITICAL | `64871dc` | Track `qbe/qbe.exe` binary + sha baseline + .gitignore carveout |
| **#2 regress.py wrong path** | CRITICAL | `a19447e` | `python compiler/build/bin/regress.py` → `python regress.py` (3 places: ci.yml L84/99, release.yml L177) |
| **#3 jhyy_v1.exe.exe untracked** | HIGH | `4a6ebd1` | Restore from pre-`8aa2326` accidental deletion + sync content to current jhyy.exe (v1 = jhyy.exe copy convention per v1.4.4) |
| **#4 Build qbe.exe step** | (rolled into #1) | `448de0a` | Remove dead `cd qbe && make` step from both workflows (qbe.exe now tracked, no rebuild needed) |
| **#5 Stage 2 closure path** | OK | (audit only) | ci.yml L120-150 closure chain path matches fixed_point.sh pattern — no edit needed |
| **#6 installer/build.ps1** | OK | (dry-run) | Local `stub` dry-run PASS (wix 7.0.0); no stale assumptions found |

### Step 2.4 commits

```
64871dc chore(track): qbe/qbe.exe binary + sha baseline (GHA gate)
a19447e fix(ci): regress.py path in GHA workflows (v4.0.2 GHA gate)
4a6ebd1 fix(infra): restore jhyy_v1.exe.exe tracking (v4.0.2 GHA gate)
448de0a fix(ci): remove Build qbe.exe step from GHA (v4.0.2 GHA gate)
```

### GHA verification (post-push)

| Gate | Status |
|------|--------|
| `git push origin main` succeeds | ⏳ (next step) |
| GHA ci.yml latest run: PASS | ⏳ (next push triggers) |
| GHA release.yml dry_run PASS | ⏳ (manual trigger after ci green) |

---

## Step 2.1 — W-073 emit escape fix (⏳ TODO)

Per RCA: `data $str548 = { b "\", b 0 }` QBE IL emit 没 double-escape `\` → unterminated `b "..."` literal → 5 个连续 "unknown QBE IL mnemonic" errors at byte 20227+。

Fix scope:
- `compiler/src0/codegen.jhyy` — emit path 在 data section 拼 `b "..."` literal 时加 escape handler (~30-80 LOC)
- `compiler/src0/codegen_amd64_lexer.jhyy:1043` — `next_token_data_string` robust escape scanner (~10-30 LOC)
- `compiler/tests/examples/str_with_backslash.jhyy` NEW
- `compiler/tests/examples/str_with_quote.jhyy` NEW

---

## Step 2.2 — W-074/076 runtime.c rename (⏳ TODO)

Per RCA: `runtime.c` `arena_*` 4 fn 跟 `std::arena` 40B jhyy-side Arena API 同名,namespace 冲突。

Fix scope:
- `compiler/runtime/runtime.c` — `arena_*` → `c_arena_*` rename (4 fn)
- `compiler/src0/abi_amd64_sysv.jhyy:291` + `abi_amd64_win.jhyy:21` + `arena.jhyy:88` — caller update
- `compiler/src0/std/arena.jhyy` — 删 `std_` 前缀
- `compiler/tests/examples/std_arena_*.jhyy` — 删 `std_` 前缀
- `compiler/tests/examples/arena_basic.jhyy` NEW

---

## Step 2.3 — W-075 mem_set i64-store (⏳ TODO optional)

Per RCA: `compiler/src0/std/mem.jhyy:78` 仍 `*(ptr_add(dst, i) as *i32) = b` i32-store,M0 简化 trade-off。

Skip criteria: scope creep risk on the emit path fix (W-073) — defer to v4.0.2.1 if W-073 surface unexpected changes。

---

## Step 2.5 — Verification gates (⏳ TODO before tag v4.0.2)

| Gate | Status |
|------|--------|
| regress.py 158/158 PASS | ⏳ |
| bench.sh --report 5/5 PASS | ⏳ |
| fixed_point.sh N≥3 byte-equal PASS | ⏳ (was fail pre-W-073 fix) |
| jhyy.exe compile main.jhyy → gcc link OK | ⏳ |
| ACTIVE bucket = 0 in workarounds.md | ⏳ |
| GHA ci.yml latest run: PASS | ⏳ (push triggers) |
| GHA release.yml latest dry_run: PASS | ⏳ (manual trigger) |

---

## Commit cadence (current state)

| # | Commit | Status |
|---|--------|--------|
| 1 | `64871dc` chore(track): qbe/qbe.exe binary + sha baseline | ✅ |
| 2 | `a19447e` fix(ci): regress.py path in GHA workflows | ✅ |
| 3 | `4a6ebd1` fix(infra): restore jhyy_v1.exe.exe tracking | ✅ |
| 4 | `448de0a` fix(ci): remove Build qbe.exe step from GHA | ✅ |
| 5+ | (Step 2.1/2.2/2.3 commits) | ⏳ |

---

## References

- v4.0.0-rc1 changelog: `docs/logs/v4/changelog-v4.0.0.md`
- v4.0.1 changelog: `docs/logs/v4/changelog-v4.0.1.md` (docs-only ship, ACTIVE bucket audit-flip)
- v4.0.2 plan: `~/.claude/plans/merge-v2-axis-v3-axis-into-main-serialized-aho.md`
- W-073 RCA evidence: byte 20227 in `data $str548 = { b "\", b 0 }` QBE IL emit output
- Memory: `feedback_verify_active_reproduces`, `feedback_rca_first_root_cause`, `feedback_codegen_amd64_multifn`, `feedback_jhyy_dbgfile_cwd_sensitive`, `feedback_changelog_umbrella`, `feedback_fix_evaluation_rule`, `feedback_ssh_key_same_shell`, `feedback_audit_single_commit_diff`, `feedback_git_identity_canonical`, `feedback_editorconfig_vendor_eol`, `feedback_make_clean_too_aggressive`, `feedback_ci_yaml_debugging`, `feedback_regress_py_path_normalization`
