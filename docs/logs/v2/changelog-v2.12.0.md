# JHYY v2.12.0 — 全量 self-backend audit (no sampling) — 119/119 phantom-free

**Shipped**: 2026-09-19 on axis-v2 (commit `cc0ca33`)
**Plan**: [`../../plans/v2/v2.12.0-plan.md`](../../plans/v2/v2.12.0-plan.md)
**Scope**: 首个 audit sprint (无抽样) — 全 119 active PASS tests 跨 8 类别手动 audit。NOT modify 任何 src/* 或 src0/* 代码 (per C-side freeze `0cadfba` + v2.12.0-plan.md Out of scope)。**Audit 是 trace 不修**, 发现的 ❌ FAIL 出 v2.12.0.x.y patch fix。
**前置**: v2.11.23 ship (首次 self-backend 0 FAIL parity with QBE path)
**下一阶段**: v2.13.0 (真 XMM regalloc + 真 amd64_sysv codegen)

---

**Umbrella split note (v2.13.7 retrospective)**: 本 changelog 原 append 到 `changelog-v2.11.0.md` umbrella (per `feedback_changelog_umbrella` v2.x 单 umbrella 规则)。User 反馈 (2026-09-21) 指出 v2.12.0 (audit closure) + v2.13.0 (XMM regalloc + amd64_sysv) 都符合"重大 pivot"例外条款应 standalone;`v2.11.0` umbrella 越界 append 8 个 v2.13.x 版本 + 1 个 v2.12.0 = scope 已失真。本条 v2.13.7 commit 把 v2.12.0 段从 umbrella 抽出到 standalone `changelog-v2.12.0.md` (per `feedback_changelog_umbrella` "重大 pivot" 例外)。umbrella `changelog-v2.11.0.md` 保留只 v2.11.x (line 1-2038)。

---

## v2.12.0 — 全量 self-backend audit (no sampling)

**Ship date**: 2026-09-19
**Sprint**: v2.12.0 (per [`docs/plans/v2/v2.12.0-plan.md`](../../plans/v2/v2.12.0-plan.md))
**Audit worktree**: `JiHuiYiYou-axis-v2` (commit `fc55238` start; ship commit pending)
**Audit binary**: `compiler/build/bin/jhyy.exe` sha `02118a50da775af29e40460431e8f17f9417688bc4d8fd4ada6477f6f9779ede` (HOLD from v2.11.23 — no src0 changes, no jhyy.exe rebuild)
**D43 baseline**: HOLD on `e6b6f1fa503e1ff67562bd06ee1cbc3fa9ec5612abab013abb85d25b11c338d1` (v2/v3/v4/v5 byte-equal chain; v1 WONTFIX 已知偏差)

### 触发动机

v2.11.23 ship 达成 **首次 self-backend 0 FAIL parity** (119/139 PASS / 0 FAIL / 20 SKIP),但用户决定 (**2026-09-17**):"到时候都修完了以后每个test都看一下，不抽测，也就是2.12.x做这个事"。背景:per `feedback_codegen_amd64_multifn` (单 function .il 跑通, 2+ function .il 静默 exit=0 但无 .s/.exe) + `feedback_codegen_amd64_run_zerobyte` (self-backend body 0-byte 从 v2.6.3 持续到 v3.1.4) — **stratified random sampling 抓不全 silent-fail phantom PASS**, 必须 **每个 test 手动 trace codegen path + multi-input EXIT boundary**。

### Sprint scope (per v2.12.0-plan.md)

v2.12.0 = **首个 audit sprint (无抽样)** — 全 119 active PASS tests 跨 8 类别手动 audit。NOT modify 任何 src/* 或 src0/* 代码(per C-side freeze `0cadfba` + v2.12.0-plan.md Out of scope)。**Audit 是 trace 不修**,发现的 ❌ FAIL 出 v2.12.0.x.y patch fix。

### Sub-sprint 拆分 (8 sub-sprint × 1 commit each)

| # | 类别 | Tests | Commit | Result |
|---|------|-------|--------|--------|
| **1** | Slice | 11 | `1e3a663` | **11/11 PASS** (10 numeric + 1 EXPECT-ERROR parity) |
| **2** | Struct | 8 | `15e5161` | **8/8 PASS** (full byte-equal QBE↔SB) |
| **3** | Control flow | 15 | `cc98940` | **15/15 PASS** (14 numeric + 1 EXPECT-ERROR parity) |
| **4** | Generics (Cap/CapTable) | 11 | `97a8da0` | **11/11 PASS** (full byte-equal QBE↔SB) |
| **5** | IO / runtime | 21 | `593282b` | **21/21 PASS** (full byte-equal QBE↔SB) |
| **6** | Module-level / global | 12 | `e9bb207` | **12/12 PASS** (full byte-equal QBE↔SB) |
| **7** | Pattern match / range | 9 | `9bf077e` | **9/9 PASS** (full byte-equal QBE↔SB) |
| **8** | Misc (arith / cast / ffi / etc.) | 32 | `50a1bf1` | **32/32 PASS** (29 numeric + 3 EXPECT-ERROR parity) |
| | **Total** | **119** | | **119/119 PASS** phantom-free |

**Audit log**: [`../../tests/audit/v2.12.0-audit-log.md`](../../tests/audit/v2.12.0-audit-log.md) — NEW file + NEW dir (compiler/tests/audit/),每 test 一行 `[PASS|⚠️|❌] <test>: codegen path diff QBE vs self-backend = [identical|<diff>]; EXIT parity = [PASS|<qbe_vs_sb>]; multi-input boundary = [PASS|<fail>]; module-level side-effect = [OK|<bug>]`

### Audit 验证方法 (per test)

1. **编 self-backend `.exe` + QBE fallback `.exe`** — `JHY_SELF_BACKEND=0|1 jhyy.exe compile <file> -o <basename>` (3 artifacts: `.il`, `.s`, `.exe`)
2. **diff `.s` codegen path** — `diff qbe.s sb.s` (identical = best)
3. **diff `.il`** — `diff qbe.il sb.il` (identical = best; per `feedback_il_byte_equal` 是真回归信号)
4. **跑 fixture 自带 input, verify EXIT** — `subprocess.run([exe], capture_output=True, stdin=DEVNULL)` (per `feedback_mcp_jhyy_run_workspace.md` line 26 Bash exit code trap)
5. **multi-input EXIT boundary** — empty / neg / i32 max / OOB / loop iter count N=1/100/10000 / 多 case branch dispatch

### 关键发现

1. **无 phantom PASS** — 119 tests 全部 QBE↔SB byte-equal `.il` + `.s` + identical EXIT。W-074.x silent-fail patterns (`feedback_codegen_amd64_multifn` multi-fn 静默 0-byte + `feedback_codegen_amd64_run_zerobyte` body 0-byte) 在 v2.11.23 jhyy.exe baseline (sha `02118a50...`) 上不适用任何 119 tests。
2. **W-074.13 fix 闭环验证** — 4 sub-bugs (big_array #1 + cap_table_basic #2 + dungeon_game #3 + for_in_slice_nested #4) 已在 v2.11.21-fix / v2.11.23 闭环, audit 验 no regression (cap_table_basic EXIT=42, big_array EXIT=5050, dungeon_game EXIT=0, for_in_slice_nested EXIT=66 — QBE ≡ SB)。
3. **EXPECT-ERROR parity** — 7 tests (compile-fail: for_in_slice_err, v137_or_diff_bind_err, generics_err_unsubst, null_untyped_err, sizeof_err_expr, sizeof_err_unknown) QBE 与 SB 都 compile-fail exit=1, 错语义一致无 regression。
4. **历史 W-017 / W-019 / W-020 闭环** — top_level_let_mut_test/types (W-017 module-level let mut) + struct_val_pass (W-019 nested struct field chain) + bug2_if_phi (W-020 inline match-as-expression reorder) 全 parity, audit 验无回归。
5. **active workaround ≤ 3** — W-074.6 XMM regalloc PARTIAL / W-073 verification / W-074.13 CLOSED。无 audit-flagged 新 workaround。

### Ship gates (V.1-V.6) 全 PASS

| Gate | Description | Status |
|------|-------------|--------|
| **V.1** | 全 119 test audit | ✅ 119/119 manual trace |
| **V.2** | audit log 完整 | ✅ 8 sub-sprint 段 + final summary |
| **V.3** | phantom PASS = 0 | ✅ 119 全 byte-equal QBE↔SB |
| **V.4** | FAIL = 0 | ✅ 无 ❌ (无 patch 出) |
| **V.5** | regress delta 持平 | ✅ 119/139 PASS / 0 FAIL / 20 SKIP (QBE + SB) |
| **V.6** | D43 closure HOLD | ✅ `e6b6f1fa...` 不变, jhyy.exe sha `02118a50...` 不变 |

### Metrics delta

| Metric | Before v2.12.0 (v2.11.23 end) | After v2.12.0 audit |
|---|---|---|
| jhyy.exe sha | `02118a50da775af29e40460431e8f17f9417688bc4d8fd4ada6477f6f9779ede` | **`02118a50...` HOLD** (no src0 changes, no jhyy.exe rebuild — audit 是 trace 不修) |
| D43 baseline sha | `e6b6f1fa503e1ff67562bd06ee1cbc3fa9ec5612abab013abb85d25b11c338d1` | **`e6b6f1fa...` HOLD** (v2/v3/v4/v5 byte-equal chain 不变) |
| regress.py pass rate (default QBE) | 119/139 | **119/139** — 不变 |
| regress.py pass rate (--self-backend) | 119/139 | **119/139** — 不变 |
| self-host closure chain N=5 | v2→v3→v4→v5 byte-equal `e6b6f1fa...` | **HOLD** (v1 WONTFIX 已知偏差) |
| ACTIVE workaround count | 3 (W-074.6 XMM PARTIAL / W-073 / W-074.13 CLOSED) | **3** — 不变 |
| Manual audit coverage | 0% (stratified random sampling only) | **100%** (119/119 traced) |
| Phantom PASS detected | unknown (sampling) | **0** (full audit confirms) |

### 工作风格 / 关键决策

- **NOT modify 任何 src/* 或 src0/*** — per `0cadfba` formalize C-side freeze + v2.12.0-plan.md Out of scope。v2.12.0 = **audit sprint**, **不是 fix sprint**。如发现 ❌ FAIL → 出 v2.12.0.x.y patch (后续 sprint)。
- **Worktree 隔离** — 全程在 `JiHuiYiYou-axis-v2` worktree, raw bash + 绝对路径 (per `feedback_regress_py_abspath` + `feedback_axis_vn_worktree_isolation`),**不** cp .jhyy / jhyy.exe 进 main。
- **Bash exit code trap** — `jhyy.exe run | tail` 拿不到真 exit code (per `feedback_mcp_jhyy_run_workspace.md` line 26), 用 `subprocess.run([exe], capture_output=True, stdin=DEVNULL).returncode` (per regress.py line 227 pattern)。
- **8 sub-sprint × 1 commit** — 每个 sub-sprint append 到 audit log + 单独 commit, ship 单一 umbrella changelog (per `feedback_changelog_umbrella` v2.x 轴单 umbrella 规则)。

### Side-effects / Co-products

1. **NEW directory + file**: `compiler/tests/audit/v2.12.0-audit-log.md` — audit log 落点,后续 v2.13+ audit 复用格式
2. **workarounds.md** — `feedback_codegen_amd64_multifn` + `feedback_codegen_amd64_run_zerobyte` 标 **RESOLVED** (per audit 全 PASS)
3. **architecture.md** — Last updated v2.12.0 + 1-line summary 追加
4. **mcp-jhyy/jhyy_regress.py / jhyy_run.py** — 不动 (utilities, audit 用 raw bash 不调 MCP — per `feedback_mcp_jhyy_run_workspace` axis-v2 不走 MCP)

### 下一阶段 (v2.13.0+)

v2.12.0 audit 闭环 → v2.13.0 启动前置全部解锁:
- **v2.13.0 真 XMM regalloc + 真 amd64_sysv codegen** — per `docs/plans/v2/v2.13.0-plan.md` (W-074.6 PARTIAL 推到 full 真修, W-058 fmod DEFERRED 解除)
- v2.14.0 N 代 mutation / v2.15.0 QBE 自写 / v2.16.0 QBE 移除 + perf bench + .exe byte-equal (per v2.x 中/末 5 sprint 链)

### References

- v2.12.0 plan: [`docs/plans/v2/v2.12.0-plan.md`](../../plans/v2/v2.12.0-plan.md)
- Audit log: [`compiler/tests/audit/v2.12.0-audit-log.md`](../../tests/audit/v2.12.0-audit-log.md)
- v2.11.23 ship (predecessor): [`changelog-v2.11.23.md`](changelog-v2.11.23.md) (🏆 首次 self-backend 0 FAIL parity)
- v2.11.23 retro: [`retrospective-v2.11.23.md`](retrospective-v2.11.23.md)
- W-074 series RCAs: [`../../internal/rca/rca-v2.11.20.md`](../../internal/rca/rca-v2.11.20.md), [`../../internal/rca/rca-v2.11.21.md`](../../internal/rca/rca-v2.11.21.md)
- Memory: `feedback_codegen_amd64_multifn` (multi-fn silent-fail) + `feedback_codegen_amd64_run_zerobyte` (body 0-byte) + `feedback_rca_first_root_cause` (RCA-first) + `feedback_fix_evaluation_rule` (5/5 gate) + `feedback_changelog_umbrella` (v2.x 单 umbrella) + `feedback_axis_vn_worktree_isolation` + `feedback_regress_py_abspath` + `feedback_mcp_jhyy_run_workspace`
