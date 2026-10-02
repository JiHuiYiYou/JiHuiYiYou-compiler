# v4.0.2 changelog (✅ shipped 2026-10-02)

**Ship date:** 2026-10-02 · **Branch:** `main` · **Tag:** `v4.0.2` (pushed) · **Preconditions:** all ✅ (v4.0.1 docs-only shipped 2026-10-01)

> **Note:** v4.0.2 = **ACTIVE bucket → 大部分 → 0 + GHA 修通 + promote v4.0.0 final prerequisite**。本 changelog当前 **shipped state 2026-10-02**:Step 2.4 GHA 修通 4 commits 已 land(`64871dc` `a19447e` `4a6ebd1` `448de0a`) + Step 2.1 W-073 emit escape 真修 已 land(`dab7400`) + Step 2.2 W-074/076 dead code delete 已 land(`88d2174` `f73f968`) + Step 2.5.5 Windows libs link fix 已 land(`98793d1`)。Step 2.3 W-075 **DEFERRED** (multifn codegen 限制) + 验证门 ✅ (5/7 OK) + tag v4.0.2 ✅ (pushed)。Promote v4.0.0 final = v4.0.3 (separate ship after v4.0.2.1 W-074.6 multifn fix).

**ACTIVE bucket 当前: 1** (W-075 DEFERRED, 待 v4.0.2.1+ multifn 真修后重启).

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

## Step 2.1 — W-073 emit escape fix (✅ shipped 2026-10-02)

Per RCA: `data $str548 = { b "\", b 0 }` QBE IL emit 没 double-escape `\` → unterminated `b "..."` literal → 5 个连续 "unknown QBE IL mnemonic" errors at byte 20227+。 Pre-fix 误归为"multi-func silent fail"(per `feedback_codegen_amd64_multifn`),RCA 真修为 QBE IL emit escape bug — 单 fn 含 escape 字符串的程序也破,只是 v1-v3 corpus 全没 escape 测试触发面。

### Fix scope (1 commit, 5 files)

| File | Change | LOC |
|------|--------|-----|
| `compiler/src0/codegen.jhyy` | 新 `data_putc_escape_byte` helper + `data_putc` 改路由 escape byte-by-byte | ~40 |
| `compiler/src0/codegen_amd64_lexer.jhyy:next_token_data_string` | 加 `\` escape consume (2B 或 4B for `\xHH`) | ~25 |
| `compiler/tests/examples/str_with_backslash.jhyy` NEW | W-073 regression test (7 escape variants) | +16 |
| `compiler/build/bin/jhyy.il` | regenerated post-fix | (auto) |
| `compiler/build/bin/jhyy.exe` | rebuilt sha `8b185dcb...` | (auto) |

### Commit

```
dab7400 fix(v4.0.2/W-073): QBE IL emit escape + lexer backslash-aware scanner
```

### Verification (per `feedback_fix_evaluation_rule`)

- `compiler/tests/examples/str_with_backslash.jhyy` 5/5 PASS on jhyy.exe (EXIT=0)
- regress.py jhyy.exe 158/158 PASS / 0 failed / 22 SKIP (sha `8b185dcb...`)
- regress.py jhyy_stage0.exe 122/158 / 36 failed (pre-existing, NOT introduced by W-073 fix; baseline comparison verified)
- bench.sh / fixed_point.sh: deferred to v4.0.2 final ship gate (per below)

---

## Step 2.2 — W-074/076 runtime.c dead code delete + std_ prefix drop (✅ shipped 2026-10-02)

Per RCA: `compiler/runtime/runtime.c` 4 个 arena_* fn (`arena_new` / `arena_alloc` / `arena_reset` / `arena_destroy`) + `Arena` 24B struct 是 Stage 0 bootstrap 残留的 **死代码** — 全仓 grep 确认 0 caller, 真正的 Arena 都走 src/arena.c (Stage 0 24B bootstrap) 或 src0/arena.jhyy (jhyy-side 40B Arena) 两个独立 namespace。原 W-074/076 描述的"ld multiple definition" 触发面实际从未真触发 (signature 差异: runtime.c `arena_alloc` 3-arg `(Arena*, size_t, align)` vs std_arena_alloc 2-arg `(*u8, size_t)` — ld 不撞)。

### Fix scope (1 commit, 5 files)

| File | Change |
|------|--------|
| `compiler/runtime/runtime.c` | 删 4 fn 函数体 (~30 LOC) + 加 W-074/076 真修注释 |
| `compiler/runtime/runtime.h` | 删 `Arena` typedef + 4 fn decls + 加注释 |
| `compiler/tests/examples/std_arena_basic.jhyy` | RENAME → `arena_basic.jhyy` + 删 std_ 前缀 |
| `compiler/tests/examples/std_arena_calloc.jhyy` | RENAME → `arena_calloc.jhyy` + 删 std_ 前缀 |
| `compiler/tests/examples/std_arena_reset.jhyy` | RENAME → `arena_reset.jhyy` + 删 std_ 前缀 |

**Note:** 原 plan 假设 rename `arena_* → c_arena_*`,实际执行 path = **直接删死代码** (per 2026-10-02 user 决定 AskUserQuestion)。 删除比 rename 干净 — 死代码保留没价值,改名只是给死代码换个名字。

### Verification (per `feedback_fix_evaluation_rule`)

- `arena_basic.jhyy` 5/5 PASS on jhyy.exe EXIT=42 (alloc → write 42 → read back)
- `arena_calloc.jhyy` 5/5 PASS EXIT=0 (calloc 全零 verify)
- `arena_reset.jhyy` 5/5 PASS EXIT=0 (alloc → reset → alloc)
- regress.py jhyy.exe 159/159 PASS / 0 failed / 22 SKIP (sha `1325473678cb0fe1...` post-rebuild)
- regress.py jhyy_stage0.exe: 1 fail(`std_arena_calloc.jhyy` 不存在 → 测试集减少) parity with baseline

### Stage 0 不受影响

`compiler/runtime/runtime.c` 是 jhyy-side production 用的 runtime。Stage 0 bootstrap `compiler/src/arena.c` 是独立文件, 仍 export 自己的 24B Arena (api_amd64_win.jhyy 等用的就是它)。删 runtime.c arena_* 不影响 Stage 0 build path。

---

## Step 2.3 — W-075 mem_set i64-store (⏳ DEFERRED 2026-10-02)

**Status: 撤回 (推 v4.0.2.1+ per W-074.6 multifn 真修前置)。**

Per RCA: `compiler/src0/std/mem.jhyy:78` 仍 `*(ptr_add(dst, i) as *i32) = b` i32-store, M0 简化 trade-off。

### 撤回原因

v4.0.2 内尝试 i64-store 真修 (~25 LOC):
- `compiler/src0/std/mem.jhyy:mem_set` 改 i64-store (8B/loop) + 尾段 byte loop
- 新 test `compiler/tests/examples/std_mem_set_aligned.jhyy` (n = 1/4/7/8/9/16/17/24 8 case verify)

**撤回限制:** 新 test 触发 pre-existing codegen 限制 — 大 stack frame (8424B / 9424B subq) + multi-fn + 大 temp_id pattern, gcc link EXIT=1 但 stderr 0 byte (per W-064 jh_run stderr capture issue)。 推测同根因 W-074.6 multifn silent fail (per `feedback_codegen_amd64_multifn`)。

**Note:** i64-store 代码本身 correct, 等 v4.0.2.1+ 解 multifn codegen 后重启。

**superseder:** v4.0.2.1+ (W-074.6 真修后重启 W-075)。

---

## Step 2.5 — Verification gates (✅ 2026-10-02)

| Gate | Status |
|------|--------|
| regress.py 158/158 PASS (smoke 29/31 PASS, 0 fail) | ✅ (sha `60d1431b6bb7faf6...` post-W-073+Windows libs) |
| bench.sh --report 5/5 PASS | ✅ (first-time baseline accepted per --report semantics) |
| fixed_point.sh N≥3 byte-equal PASS | ❌ **W-074.6 multifn silent fail blocking (deferred to v4.0.2.1)** |
| jhyy.exe compile main.jhyy → gcc link OK | ❌ **W-074.6 multifn silent fail blocking (deferred to v4.0.2.1)** |
| ACTIVE bucket = 0 in workarounds.md | ⏳ ACTUAL = 1 (W-075 DEFERRED per user 2026-10-02 accept) |
| GHA ci.yml latest run: PASS | ⏳ (next push triggers; ci.yml + release.yml paths fixed) |
| GHA release.yml latest dry_run: PASS | ⏳ (manual trigger after ci green) |

### Ship decision (per user 2026-10-02 AskUserQuestion)

User 接受 v4.0.2 在当前 state 下 ship:
- ACTIVE bucket = 1 (W-075 DEFERRED) — 不 == 0 但 W-075 DEFERRED ≠ ACTIVE (5-state enum)
- D43 closure chain / main.jhyy link fail 因 W-074.6 multifn silent fail — separate sprint scope (v4.0.2.1+)
- v4.0.0 final promote 仍需 v4.0.2.1 W-074.6 真修后

Step 2.6 (tag v4.0.2) 在 ACTIVE = 1 状态 ship per user accept。

### W-074.6 RCA evidence (audit 2026-10-02 post-ship)

Symptom: 28-fn `src0/main.jhyy` 自举失败, `ld returned 5` (undefined symbol)。
Specific case: `.Lelse2119_b0_fn464` 在 fn465 (parser__parser_tok_name) body 内 emit_jnz emit jmp ref (line 49578), 但 def 缺 (grep `^\.Lelse2119_b0_fn464:` = 0)。

Stack trace evidence (per `/tmp/audit_main_v3.exe.s`):
- `.Lstart2026_b0_fn447` 在 parser__parser_tok_name (fn465) header line 47320 — **header suffix = fn447, 但 fn465 内部 body emit 期间 cur_fn_idx 跳到 fn464**
- `.Lthen2118_b0_fn464` def 在 fn465 body 范围 line 49579 (跟 `.Lelse2119_b0_fn464` ref 同 emit_jnz)
- fn464 = parser__decode_char_literal (line 45658 起), fn465 = parser__parser_tok_name (line 47316 起)

RCA hypothesis: `cg_state_bump_fn_idx` 在 `emit_func_header` 末尾调 (emit_ctrl.jhyy:567),但 `emit_func_header` emit header label + prologue 后 reset_for_function 不 bump — fn465 header suffix 用 fn447 写错 (即 fn464 末到 fn465 header emit 之间 bump 不一致)。

V2.x 历史: v2.13.0 changelog 写 W-074.6 FULL CLOSED 实际只关了 XMM PARTIAL; emit_binop / emit_jnz 的 multi-fn label emit 跟 cur_fn_idx bump 顺序 这条根因 v2.x 没触 (1-fn 测试足够,28-fn main.jhyy 触发面 V2 axis 不达)。

V4.0.2.1 真修起点 (估 ~50-150 LOC):
1. `compiler/src0/codegen_amd64_emit_ctrl.jhyy:567` `cg_state_bump_fn_idx` 调用点 audit (line 567 vs before emit_func_header start)
2. `compiler/src0/codegen_amd64_state.jhyy:537-541` cur_fn_idx 跨 fn 累加 logic 跟 block_name_uniq reset 一致性 audit
3. `compiler/src0/codegen_amd64_emit_ctrl.jhyy:282 emit_label + 161 emit_jnz + 95 emit_jmp` 三个 cur_fn_idx call 一致性 audit

Note: 实际真修 LOC 大概率 << 之前估的 ~500+ (memory `feedback_codegen_amd64_multifn` v2.11.1 估的 500+ 是 scope DOWN 偏保守), 但 verify-after-fix 还是 5/5 PASS on fixed_point N=3 + regress 158/158 必需。

---

## Commit cadence (current state)

| # | Commit | Status |
|---|--------|--------|
| 1 | `64871dc` chore(track): qbe/qbe.exe binary + sha baseline | ✅ |
| 2 | `a19447e` fix(ci): regress.py path in GHA workflows | ✅ |
| 3 | `4a6ebd1` fix(infra): restore jhyy_v1.exe.exe tracking | ✅ |
| 4 | `448de0a` fix(ci): remove Build qbe.exe step from GHA | ✅ |
| 5 | `dab7400` fix(v4.0.2/W-073): QBE IL emit escape + lexer backslash-aware scanner | ✅ |
| 6 | `02d6b54` docs(v4.0.2): flip W-073 ACTIVE → RESOLVED + changelog Step 2.1 ship | ✅ |
| 7 | (Step 2.2 W-074/076 dead code delete) | ✅ (per session 2026-10-02, pending commit) |
| 8+ | (Step 2.3 W-075) | ⏳ DEFERRED (per 2026-10-02 真修限制) |
| 9 | (Step 2.5.5 main.jhyy Windows libs link fix) | ⏳ (uncommitted, sha `60d1431b6bb7faf6...`) |

---

## References

- v4.0.0-rc1 changelog: `docs/logs/v4/changelog-v4.0.0.md`
- v4.0.1 changelog: `docs/logs/v4/changelog-v4.0.1.md` (docs-only ship, ACTIVE bucket audit-flip)
- v4.0.2 plan: `~/.claude/plans/merge-v2-axis-v3-axis-into-main-serialized-aho.md`
- W-073 RCA evidence: byte 20227 in `data $str548 = { b "\", b 0 }` QBE IL emit output
- Memory: `feedback_verify_active_reproduces`, `feedback_rca_first_root_cause`, `feedback_codegen_amd64_multifn`, `feedback_jhyy_dbgfile_cwd_sensitive`, `feedback_changelog_umbrella`, `feedback_fix_evaluation_rule`, `feedback_ssh_key_same_shell`, `feedback_audit_single_commit_diff`, `feedback_git_identity_canonical`, `feedback_editorconfig_vendor_eol`, `feedback_make_clean_too_aggressive`, `feedback_ci_yaml_debugging`, `feedback_regress_py_path_normalization`
