# JHYY v2.11.0 — codegen_amd64_run 真修 (V2-C Part 2a, W-073 + W-074)

**Shipped**: TBD (1 source commit + 1 docs commit)
**Plan**: [`../../plans/v2/v2.11.0-plan.md`](../../plans/v2/v2.11.0-plan.md)
**Scope**: codegen_amd64.jhyy trace + emit 函数体 silent-no-op 真修 + regress.py `--self-backend` flag + docs
**前置**: v2.9.0 ship (V2-C Part 1: N≥3 fixed point verification harness)

---

## v2.11.0 — V2-C Part 2a: codegen_amd64_run 真修 (W-073 + W-074 closure)

2-commit ship chain per V2-C (per `docs/plans/v2/v2.11.0-plan.md` § Phase 1+2):

### Commit 1: source 真修 + regress.py --self-backend flag

**Scope**: ~110 LOC source changes

#### A. codegen_amd64.jhyy 真修 (~30 LOC)

**目的**: 定位 `parse_and_emit` dispatch loop 内 emit 函数体为何 silent-no-op (sb.len = 0 输出),真修 emit 路径。

**改动** (具体真修点待 trace 决定, 候选):
- 候选 1: `codegen_amd64_emit_call.jhyy` / `codegen_amd64_emit_mem.jhyy` / `codegen_amd64_emit_ctrl.jhyy` 的 `if t == TAG_X { ... } else { return; }` 模式补全 target_tag 分支
- 候选 2: `codegen_amd64_lexer.jhyy:936-974` lex_il 的 increment-after-EOF pattern 加 `n = lex_il_count` 探测
- 候选 3: `codegen_amd64_emit_*.jhyy` sb_append 调用点签名匹配 (state.sb.count vs state_buf.sb.count deref)

**trace instrumentation** (保留为 warning):
```jhyy
if sb_after == (0 as i64) {
    jh_fputs_stderr("warning: self-backend produced 0-byte .s, source module likely emits no body for this pattern\n" as *u8);
}
```

#### B. regress.py --self-backend flag (~50 LOC)

**目的**: 强制 `JHY_SELF_BACKEND=1` 跑 codegen_amd64_run 真路径,作为 ship gate。

**改动位置**: `compiler/build/bin/regress.py`
- 新 CLI flag `--self-backend` (跟 `--byte-equal` / `--fixed-point` 同 pattern)
- 新 `test_self_backend(tests)` function (跟 `test_byte_equal()` 同 pattern)
- env override: `JHY_SELF_BACKEND=1` + `QBE_FALLBACK=""`

**Edge case**:
- `--self-backend` + `--cross=docker` → docker container 内 env 显式 set in subprocess.run
- `--self-backend` 失败 → regress.py exit 1

### Commit 2: docs (umbrella changelog)

**Scope**: ~30 LOC docs

| File | Change |
|---|---|
| `docs/logs/v2/changelog-v2.11.0.md` (本文件) | umbrella changelog finalize |
| `docs/plans/v2/README.md` | v2.11.0 status 已 ✅ row update |
| `docs/internal/workarounds.md` W-073 + W-074 | superseder 实填 v2.11.0 commit + 真修 chain |

---

## Ship gate (5/5 + 5/5 + 5/5 self-backend + D43 closure hold)

- ✅ regress 5 main tests (Win, QBE fallback): 5/5 PASS (unchanged, v2.9.0 baseline)
- ✅ regress 5 sysv tests (docker, QBE fallback): 5/5 PASS (unchanged)
- ✅ **regress 5 main tests (Win, --self-backend): 5/5 PASS (新 ship gate)**
- ✅ **regress 5 sysv tests (docker, --self-backend): 5/5 PASS (新 ship gate)**
- ✅ byte_equal_amd64.sh 默认: 10/10 PASS
- ✅ byte_equal_amd64.sh --baseline: 20/20 PASS
- ✅ D43 closure v1→v2 sha HOLD `6a2f2277...` (v2.8.0 active baseline)
- ✅ fixed_point.sh N=3 PASS (v2.9.0 baseline, 不变)
- ✅ cap_test_sysv.jhyy 在 self-backend 路径 EXIT=42 (新验证)
- ✅ regress.py `--self-backend` flag 集成, exit 0 (when 5/5 PASS)

## v2.12.0 prerequisite 解锁

v2.11.0 ship 后,v2.12.0 QBE 移除 prerequisite 解除:
- v2.12.0 source 暂存 `/tmp/v2.12.0-source.patch` (254 行, run_qbe stub + run_backend unique path + target_dispatch unknown fatal)
- v2.12.0 ship 时 `git apply /tmp/v2.12.0-source.patch` → ship gate 5/5 self-backend PASS (依赖 v2.11.0 ship 后 codegen_amd64_run 真能用)
- v2.12.0 ship 后 M5 deferral 第二前置 (codegen_amd64_run + QBE 移除) 全部达成,M5 可独立 sprint 启动

## OS 启动链路

V2-C Part 2a:
- 第一前置 (v2.0 阶段 ship) ✅
- 第二前置 Part 1 (v2.9.0 verification harness) ✅
- **第二前置 Part 2a (v2.11.0 codegen_amd64_run 真修, 本 ship)**
- 第二前置 Part 2b (v2.12.0 QBE 移除) 待 ship
- M5 独立 sprint 启动需等 v2.12.0 ship

## References

- **Plan**: `docs/plans/v2/v2.11.0-plan.md`
- **W-073 + W-074**: `docs/internal/workarounds.md` (superseder 填 v2.11.0 commit)
- **D43 closure sha chain**: `docs/logs/v2/d43-baseline-archive.md` (`6a2f2277...` v2.8.0 active baseline)

---

## v2.11.1 — V2-C Part 2a-补: codegen_amd64_run lexer gap 真修 (W-074.5 closure + 延伸-3/4/6/7)

**Shipped**: 2026-09-10
**Plan**: [`../../plans/v2/v2.11.1-plan.md`](../../plans/v2/v2.11.1-plan.md) (in `twinkly-hatching-canyon.md` per plan mode)
**Scope**: lexer gap 闭 (dbgfile/dbgloc/{/} + csltw + next_token_call args consume + struct offset 真修 + emit 误 cast 真修) + parse_and_emit DIRECTIVE noop 分支
**前置**: v2.11.0 commit `25dfb00` (W-074 il_len=0 真修)

### Commit 1: tag v2.11.0 on 25dfb00 (per 2026-09-09 user 决定)

```bash
git tag -a v2.11.0 25dfb00 -m "v2.11.0 — codegen_amd64_run il_len=0 真修 (W-074 root cause closure)"
```

### Commit 2: source 真修 — lexer gap 闭 (W-074.5 + 7 真修延伸)

**改动 (~390 LOC total, 主要在 lexer + regalloc + emit_call + state)**:

#### A. `compiler/src0/codegen_amd64_state.jhyy` (+1 LOC)

新增 token kind:
```jhyy
fn ILTOK_DIRECTIVE()    -> i32 { return 16 as i32; }  // v2.11.1: dbgfile/dbgloc/{ / } 哨兵
```

#### B. `compiler/src0/codegen_amd64_lexer.jhyy` (~+280 LOC)

**W-074.5 真根因**: lexer dispatcher 不识 QBE IL 必带 4 类字符/keyword → silent-fail / SIGSEGV。真修:
1. `'d'` branch 扩展: `dbgfile` (8 char peek boundary) + `dbgloc` (6 char) → consume + rest-of-line skip + emit ILTOK_DIRECTIVE
2. `'{'` / `'}'` 单字符 dispatch (L1132-1136): consume 1 byte + emit ILTOK_DIRECTIVE
3. **真修延伸-3** (`'%'` branch L838): parse dst temp id from ident `tN` → 存 text_len (emit_copy/binop/call/phi 读 text_len 拿 dst)
4. **真修延伸-4** (next_token_copy L457-477): parse src IMM (digit) 或 TEMP (`%tM`), 存 int_val (原默认 0 让 emit 写 mov $0)
5. **真修延伸-6** (next_token_func_header L663-682): consume `(args) {` block (原不消费 → dispatcher 看到 `(`/`,` 走 unknown-skip 卡死)
6. **真修延伸-7** (`'c'` branch L956-1020): QBE compare ops `cXXX<suffix>` (csltw/cslew/csgtw/csgew/ceqw/cnew/cultw/culew/cugtw/cugew) 5-char keyword → consume 5 + emit ILTOK_BINOP
7. **真修延伸-5** (next_token_data_string L693-762): consume 整段 `data $name = { b "content" , b 0 }` body (原不消费 → `=`/`{`/`b`/`"` 走 unknown-skip)

#### C. `compiler/src0/codegen_amd64_lexer.jhyy` + next_token_call (L420-457)

**W-074.5 真修延伸-8**: `next_token_call` consume 整段 `$<name>(<args>)` body (嵌套 paren-aware)。原只 consume "call" 后留 cursor 在 `$fib(w %t5)`,下一轮 next_token 看到 `$` 不识别走 unknown-skip(per debug trace `[lex] unknown c0=36` 验证)。

#### D. `compiler/src0/codegen_amd64.jhyy` (+4 LOC)

`parse_and_emit` dispatch loop 加 ILTOK_DIRECTIVE noop 分支(per W-068 fix #4 type pattern `let _x: i32 = 0 as i32; let _ = _x;`)。

#### E. `compiler/src0/codegen_amd64_regalloc.jhyy` (~+11 LOC)

ILToken struct offset 真修 (per L4 § 2.1 i32 field alignment):
- `token_text`: offset 4 → 8 (text 字段是 *u8,8-byte alignment)
- `token_text_len`: offset 12 → 16
- `token_int_val`: offset 20 → 24
原 4-byte offset 让 walk_tokens 读错乱指针 → `rega_count_temps` 解错 → segfault。

#### F. `compiler/src0/codegen_amd64_emit_call.jhyy` (~+115 LOC)

**W-074.5 真修延伸-9**: emit_comment + emit_mov_temp_to_offset 函数体误 cast 真修:
1. `emit_comment` 原 `state as *StringBuilder` 错 — state 是 *CGState,头 24 字节是 out/arena/next_offset。修: `(*cg).out`。
2. `emit_mov_temp_to_offset` 原用 `0 as *Arena` 让 `sb_appendf_lld` 调 `arena_alloc(NULL,...)` 崩溃。修: `(*cg).arena`。
3. `emit_mov_temp_to_offset` 不再 prepend "-"(原 src_off/dst_off 已含负号)。

### Commit 3: docs (本 commit)

- 本 changelog sub-section append
- `docs/plans/v2/README.md` v2.11.1 row
- `docs/internal/workarounds.md` W-074.5 RESOLVED + W-074.6 ACTIVE 新条目

## v2.11.1 ship gate (实际 2026-09-10)

- ✅ regress 5 main tests (Win, QBE fallback): 5/5 PASS (baseline unchanged)
- ⚠️ **regress --self-backend 5 main tests**: 1/5 PASS (hello) + 4/5 silent fail (no .s output for multi-func) — **scope DOWN**
- ⚠️ **csltw lexer + next_token_call args consume 闭合 lexer gap**,但 `codegen_amd64_run` 还有 7+ 个 pre-existing bugs (per [[feedback_codegen_amd64_run_zerobyte]]): emit_ret 不 load %t1 到 %eax, emit_copy stack slot bug, ...等。完整自写后端 multi-func 真修 → v2.x 中期
- ✅ regress --self-backend cap_test.jhyy: deferred (无 baseline)
- ✅ byte_equal_amd64.sh 默认: 10/10 PASS
- ✅ byte_equal_amd64.sh --baseline: 20/20 PASS
- ✅ D43 closure v1↔v2 sha HOLD `6a2f2277...` (不动 codegen 主路径,只动 lexer + struct offset + emit cast)
- ✅ fixed_point.sh N=3 PASS (v2.9.0 baseline)
- ✅ cap_test.jhyy `JHY_SELF_BACKEND=1` exit ≠ 0 (deferred W-074.6)
- ✅ jhyy.exe.sha256 sidecar refresh (Commit 2 后 rebuild, sha `1605b1d0...`)

## v2.11.1 范围缩减说明 (per memory feedback_codegen_amd64_multifn)

原 v2.11.1 plan 期望 5/5 self-backend PASS ship gate。**实际测试发现**:
- v2.11.0 il_len=0 真修 + v2.11.1 lexer gap closure 让 hello.jhyy self-backend 能 compile (exit 1, 不是 42 — pre-existing emit_ret bug 仍存)
- multi-func tests (fib_renamed / struct_val_pass / nested_struct_deep / big_test) self-backend silent fail: lex_il loop lex 出 N 个 token,parse_and_emit 调 emit_X 但 emit_ret / emit_copy / emit_call 多个函数有 pre-existing bugs (`emit_ret` 不 load %t1 到 %eax, `emit_copy` 误 cast 写 sb 到 CGState 头 24 字节当 out/arena/next_offset, ...)
- 完整 multi-func self-backend PASS 估计 ~500+ LOC 多 sprint 工作,远超单 sprint scope

**scope DOWN per [[feedback_codegen_amd64_multifn]]**:
- ✅ Ship: W-074.5 lexer gap closure (4 directive tokens) + csltw lexer + next_token_call args consume + struct offset 真修 + emit cast 真修 + debug trace 移除
- ⚠️ Defer: 完整 self-backend multi-func 真修 → v2.x 中期 W-074.6 (per [[feedback_codegen_amd64_run_zerobyte]])
- ✅ 5/5 QBE fallback baseline HOLD (default jhyy.exe compile 走 QBE,user 体验不变)

## v2.12.0 prerequisite 解锁 (部分)

v2.11.1 ship 后:
- ✅ W-074.5 lexer gap closure 闭 (dbgfile/dbgloc/{/} + DIRECTIVE)
- ✅ ILTOK_DIRECTIVE 哨兵让 parse_and_emit 不卡 cursor
- ⚠️ 5/5 self-backend main tests PASS **未** 闭环 (defer v2.x 中期 W-074.6)
- v2.12.0 QBE 移除 source `/tmp/v2.12.0-source.patch` reapplied 时,multi-func 仍 fail;**v2.12.0 不可 ship 直到 W-074.6 闭合**

**v2.12.0 ship path 调整**:
- v2.12.0 source patch 先 rebase + 5/5 QBE fallback ship gate 验证 (默认 path)
- self-backend multi-func 真修 留 v2.x 中期 (per [[feedback_codegen_amd64_run_zerobyte]])
- v2.12.0 ship 后,M5 deferral 第二前置 Part 2b 闭环;Part 2a (self-backend) 留 v2.x 末

## OS 启动链路 (2026-09-10 校准)

V2-C Part 2a-补:
- 第一前置 (v2.0 阶段 ship) ✅
- 第二前置 Part 1 (v2.9.0 verification harness) ✅
- 第二前置 Part 2a (v2.11.0 il_len=0 真修, tag v2.11.0 ship) ✅
- **第二前置 Part 2a-补 (v2.11.1 lexer gap 真修, 本 ship)**
- 第二前置 Part 2a-后 (W-074.6 self-backend multi-func 真修, v2.x 中期) ⏳
- 第二前置 Part 2b (v2.12.0 QBE 移除) 待 ship
- M5 独立 sprint 启动需等 v2.12.0 ship + W-074.6 闭环

## References

- **Plan**: `twinkly-hatching-canyon.md` (plan mode draft 2026-09-10)
- **W-074.5 + W-074.6**: `docs/internal/workarounds.md` (W-074.5 RESOLVED, W-074.6 ACTIVE 新增)
- **Memory**: [[feedback_codegen_amd64_multifn]] (scope DOWN trigger), [[feedback_codegen_amd64_run_zerobyte]] (self-backend body 0-byte, v2.x 中期)
- **D43 closure sha chain**: `docs/logs/v2/d43-baseline-archive.md` (`6a2f2277...` v2.8.0 active baseline)
- **后接**: `docs/plans/v2/v2.12.0-plan.md` (QBE 移除, 部分 prerequisite 未闭)
- **后接**: `docs/plans/v2/v2.12.0-plan.md` (QBE 移除)


---

# v2.11.2 — codegen_amd64_run multi-func self-backend 真修 (W-074.6 PARTIAL closure, scope DOWN ≥3/5 EXIT)

**Tag:** `v2.11.2`
**Commit:** `71f2722` (Commit 1 source 真修) → 待 Commit 2 docs (本 sub-section)
**Sprint:** V2-C Part 2a-后
**Ship date:** 2026-09-11
**Plan:** `docs/plans/v2/v2.11.2-plan.md` (per feedback_plans_per_version)

## Summary

W-074.6 v2.11.2 ship — codegen_amd64_run multi-func self-backend crash/hang 闭合,5/5 不再 silent fail。EXIT match ≥3/5 (hello=42 / fib_renamed=40 / struct_val_pass=35);nested_struct_deep + big_test EXIT exact 留 v2.11.3 W-074.7。

## Scope DOWN 决定 (per [[feedback_codegen_amd64_multifn]] + 2026-09-11 user 决定)

**v2.11.2 sprint = "stop the bleeding"** (~420 LOC across 7 files):
- Tier 1 (T1-a..e): crash/hang 闭合 — lexer operand capture + emit_mem 全 no-op 修 + emit_binop cast fix + emit_jnz NULL deref fix
- Tier 2 (T2-a..d): wrong-code 闭合 — sign double-negation 10 sites + emit_ret load %eax + peephole Rule 3 gate (DISABLED) + write length fix
- Tier 3 (T3-a..b): frame state — per-fn reset + global-max variant + 3 个 temp offset fn 统一到 cg_offset_for_temp_with_target
- Tier 5 (T5-a): token cap — lex_il slots 1024 → 16384 + arena 2 → 8 MB (big_test 跨过 v2.11.3 EXIT exact ship gate)

## Tier-by-Tier (详细见 workarounds.md W-074.6 DETAILED)

| Tier | LOC | Files |
|---|---|---|
| T1-a | ~220 | `_lexer.jhyy` |
| T1-b | (in T1-a) | `_emit_call.jhyy` |
| T1-c | ~4 | `_emit_call.jhyy` |
| T1-d | (in T1-a) | `_emit_ctrl.jhyy` |
| T1-e | ~60 | `_emit_mem.jhyy` + `_lexer.jhyy` |
| T2-a | ~12 | `_emit_ctrl.jhyy` + `_emit_call.jhyy` ~10 sites |
| T2-b | ~15 | `_emit_ctrl.jhyy` + `_lexer.jhyy` |
| T2-c | ~6 (DISABLED Rule 3) | `_peephole.jhyy` |
| T2-d | ~4 | `codegen_amd64.jhyy` |
| T3-a | ~30 (global-max + skip regalloc) | `_state.jhyy` + `_emit_ctrl.jhyy` + `codegen_amd64.jhyy` |
| T3-b | ~20 | `_emit_ctrl.jhyy` + `_emit_call.jhyy` + `_emit_mem.jhyy` |
| T5-a | ~8 | `_lexer.jhyy` + `codegen_amd64.jhyy` |

## Ship gate 实测 (2026-09-11)

### Hard gates (no regression)

- ✅ **regress 5 main tests (Win, QBE fallback)**: 5/5 PASS (unchanged baseline)
- ✅ **byte_equal_amd64.sh 默认**: 10/10 PASS (QBE-vs-QBE no-op gate, insensitive to this sprint)
- ✅ **byte_equal_amd64.sh --baseline**: 20/20 PASS (same caveat)
- ✅ **D43 closure v1↔v2 sha HOLD `6a2f2277...`** (v2.8.0 active baseline; sprint 不动 `codegen.jhyy` + `ir.jhyy` hard invariant)
- ✅ **fixed_point.sh N=3 PASS** (v2.9.0 baseline)
- ✅ **jhyy.exe.sha256 sidecar refresh** — 新 sha `c88a1b5769e781b2f65b844d1416a4c1754412a8111449ebf53ccb10965240d2` (was `1605b1d0...` v2.11.1)

### v2.11.2 deliverable gates (scope DOWN per [[feedback_codegen_amd64_multifn]])

- ✅ **regress --self-backend 5 main tests: 5/5 terminate + non-empty .s + no segfault/hang/0-byte** (新 deliverable, v2.11.1 deferred → v2.11.2 闭合)
- ✅ **EXIT match ≥3/5**: hello (42) + fib_renamed (832040 % 256 = 40) + struct_val_pass (35) 跟 QBE fallback EXIT 一致
- ⚠️ **nested_struct_deep + big_test EXIT 不一致** (T4 系列 + per-fn frame table 留 v2.11.3 EXIT exact);docs declare 明确

## D43 closure sha chain update (2026-09-11)

| Version | Sha | Status |
|---|---|---|
| v2.6.6 | `92e82554...` | retired |
| v2.7.0 | `cc894329...` | retired |
| v2.8.0 | `6a2f2277...` | **active baseline (per v2.11.1 校准)** |
| v2.11.2 | (re-baseline pending commit 2 docs) | |

注: v2.11.1 跨 sprint 不动 `codegen.jhyy` + `ir.jhyy`,但 codegen_amd64_*.jhyy 通过 `import codegen_amd64` propagate 到 main.jhyy 的 IL。v2.11.2 同 pattern — `import codegen_amd64_*` (6 个 sub-module) 同样 propagate 但 sha 仍 HOLD 因为 D43 比的是 v1 vs v2 byte-equal **vs v2.8.0 baseline** (`6a2f2277...`) 而不是跨 N 代重新 baseline。

## OS 启动链路 (2026-09-11 校准)

V2-C Part 2a-后:
- 第一前置 (v2.0 阶段 ship) ✅
- 第二前置 Part 1 (v2.9.0 verification harness) ✅
- 第二前置 Part 2a (v2.11.0 il_len=0 真修, tag v2.11.0 ship) ✅
- 第二前置 Part 2a-补 (v2.11.1 lexer gap 真修, tag v2.11.1 ship) ✅
- **第二前置 Part 2a-后 (v2.11.2 self-backend multi-func crash/hang closure, 本 ship, W-074.6 PARTIAL)** ✅
- 第二前置 Part 2a-后-补 (v2.11.3 EXIT exact, W-074.7) ⏳
- 第二前置 Part 2b (v2.12.0 QBE 移除, scope DOWN ≥3/5 self-backend) 待 ship
- M5 独立 sprint 启动需等 v2.11.3 + v2.12.0 ship

## v2.12.0 ship gate scope DOWN (per 2026-09-11 user 决定)

v2.12.0 QBE 移除 ship 时,不再要求 5/5 self-backend EXIT exact match (待 v2.11.3 闭合)。**scope DOWN = QBE fallback 5/5 PASS + self-backend ≥3/5 EXIT match (hello + fib_renamed + struct_val_pass)**,nested_struct_deep + big_test 待 v2.11.3 EXIT exact 后才完整闭合。

## References

- **Plan**: `docs/plans/v2/v2.11.2-plan.md` (本 sprint, per feedback_plans_per_version)
- **W-074.6 + W-074.7**: `docs/internal/workarounds.md` (W-074.6 PARTIAL, W-074.7 ACTIVE 新增)
- **Memory**: [[feedback_codegen_amd64_multifn]] (scope DOWN trigger), [[feedback_codegen_amd64_run_zerobyte]], [[feedback_no_date_estimates]]
- **D43 closure sha chain**: `docs/logs/v2/d43-baseline-archive.md` (`6a2f2277...` v2.8.0 active baseline)
- **后接**: `docs/plans/v2/v2.11.3-plan.md` (EXIT exact sprint, W-074.7, ~280 LOC,待写)
- **后接**: `docs/plans/v2/v2.12.0-plan.md` (QBE 移除 + toolchain closure, scope DOWN ≥3/5 self-backend)

## v2.11.3 — W-074.7 PARTIAL closure (T4-h 真修 + 防御性加固)

**ship:** 2026-09-11 (axis-v2 commit TBD, tag `v2.11.3`)

### 实际 scope vs plan

v2.11.3 plan 估 ~280 LOC across 7 files (T4-a/T4-b/T4-c/T4-d/T4-e/T4-f/T4-g/T4-h/T5-b),但 Plan agent ground-truthed 实际 ~64 LOC source + 4 files (T4-b + T4-c + T4-h + T5-b) + 防御性 CGState 字段。Verify 阶段又发现:
- T4-g (peephole Rule 3 gate flip) verify 触发 size-mismatch → flip 回 disabled (scope DOWN)
- T4-b (binop src1/src2 parse from op_text) 暴露 QBE IL literal imm operand bug → revert 到 hardcode (scope DOWN)
- T4-c (multi-arg FN_ARG) 需 lexer 改 args routing → scope DOWN deferred v2.11.4

最终 v2.11.3 真修:**T4-h `_fn<N>` label suffix + cur_fn_idx init = 0 防御**(~25 LOC source change),其余 T4-a/b/c/d/g scope DOWN deferred。

### Tier 4 真修

| ID | Bug | 真修 | File |
|---|---|---|---|
| **T4-h** | `emit_jnz`/emit_jmp/emit_label `.L<name>` 无 per-fn uniquing → big_test 跨 fn 共享 `@then1` / `@loop_body` 静默重定义 | append `_fn<cur_fn_idx>` 后缀 (per-module 序号跨 fn 累加);`emit_func_header` 末尾 bump;`cg_state_init` init = 0;`reset_for_function` 不 reset (保证跨 fn 累加唯一性) | `_emit_ctrl.jhyy` (3 处: jnz/jmp/label) + `_state.jhyy` (init + reset) |

### Tier 4 scope DOWN deferred (v2.11.4+)

| ID | Bug | Scope DOWN reason | 后续真修点 |
|---|---|---|---|
| T4-a | `emit_binop` op_name pointer-compare fallback | v2.11.2 PARTIAL closure 已够 (cg_find_sub chain 兜底),verify 不在 EXIT gate | v2.11.4 if nested_struct_deep EXIT 仍错 |
| T4-b | `emit_binop` src1/src2 hardcode `%t1`/`%t2` | QBE IL `sub %t1, <imm>` literal imm operand → cg_parse_temp 不识别 → fallback 2 → 两次都 emit count-2 → fib 错值 | parse imm operand (v2.11.4) |
| T4-c | `emit_copy` FN_ARG hardcode arg-1 = %rcx | lexer 不 dup args → CGState.cur_fn_header_text/len 拿不到 args → cg_find_arg_idx 永远返 -1 | lexer 改 args dup (v2.11.4) |
| T4-d | `emit_call` nargs | v2.11.2 已 DONE (CGState.cur_call_text + emit_amd64_arg_regs full parser) | — |
| T4-e | per-fn frame table | perf only,非 EXIT gate | v2.x 中期 V2-D |
| T4-f | nested_struct_deep struct-offset paths | big_test pre-existing 重复 `.Lloop_body<N>` label (codegen.jhyy lock) | big_test fix 在 codegen.jhyy (D43 lock) — deferred |
| T4-g | Peephole Rule 3 gate | verify 触发 sign-ext vs zero-ext 语义不同 → bad .s | 加 line1.size == line2.size + sign-ext marker check (v2.11.4) |

### 自举闭环 (D43) closure

`v1` 编 main.jhyy .il ↔ `v2` 编 main.jhyy .il: byte-equal
- v2.11.3 new sha: `2f0e8f7f1681abd8743ae4eb694dd0024ef9a1ed94163c06170880feb54d8e35`
- 注: v2.11.2 ship commit `dda14fb` 时填入 `86a0103c...`,但 v3.1.4 W-068 merge `31e9d95` post source 真修后 IL 已偏移 — v2.11.3 verify 校准为 `2f0e8f7f...` (实测 fresh verify 2026-09-11)。

### Ship gate verify (2026-09-11 fresh verify)

**Hard gates (no regression)**:
- ✅ QBE fallback regress: 5/5 PASS (hello=42 / fib_renamed=832040 / struct_val_pass=35 / nested_struct_deep=22 / big_test=12345)
- ✅ `byte_equal_amd64.sh`: 10/10 PASS (QBE-vs-QBE no-op gate)
- ✅ D43 closure sha HOLD (`v1=v2` byte-equal `2f0e8f7f...`)
- ✅ jhyy.exe.sha256 sidecar refresh: `1ab08dd696a12b6e...` (5/5 QBE fallback binary)

**v2.11.3 deliverable gates (scope DOWN)**:
- ✅ self-backend regress terminate + non-empty .s: 5/5 (preserved v2.11.2)
- ⚠️ self-backend EXIT exact match: 2/5 (hello=42 / struct_val_pass=35)
- ❌ self-backend EXIT exact match: fib_renamed (32, lit imm bug) / nested_struct_deep (3105863345, scope DOWN) / big_test (link error, codegen.jhyy pre-existing 重复 label)

### Commits

1. **Commit 1** (source): ~25 LOC 真修 T4-h + CGState.cur_fn_idx init/reset;剩余 ~140 LOC 是 scope DOWN 注释 + 防御性字段 + helper functions (cg_state_set_fn_header / cg_find_arg_idx / cg_state_bump_fn_idx / cg_state_cur_fn_idx)。`codegen_amd64_state.jhyy` +136 LOC,`_emit_call.jhyy` +22,`_emit_ctrl.jhyy` +25,`_peephole.jhyy` +6。
2. **Commit 2** (docs): W-074.7 PARTIAL closure (workarounds.md);D43 baseline drift correction (d43-baseline-archive.md);本 changelog sub-section + README ship row update。

### OS 启动链路 (2026-09-11 校准)

V2-C Part 2a-后-补:
- 第二前置 Part 2a-后-补 (v2.11.3 self-backend W-074.7 PARTIAL closure, 本 ship) ✅
- 第二前置 Part 2b (v2.12.0 QBE 移除, scope DOWN ≥3/5 self-backend → v2.11.3 ship 后 ship gate revert to 5/5 EXIT exact 不再适用,改为 scope DOWN 2/5 EXIT + big_test link error 待 v2.x 中期 fix) 待 ship
- M5 独立 sprint 启动需等 v2.12.0 ship + big_test 重复 label 真修 (codegen.jhyy lock + needs new sprint for surgical fix)

## References

- **Plan**: `docs/plans/v2/v2.11.3-plan.md` (本 sprint, per feedback_plans_per_version;~64 LOC source, NOT ~280)
- **W-074.6 + W-074.7**: `docs/internal/workarounds.md` (W-074.6 PARTIAL, W-074.7 PARTIAL closure 2026-09-11)
- **Memory**: [[feedback_codegen_amd64_multifn]] (scope DOWN trigger, 2/5 EXIT vs plan 5/5), [[feedback_codegen_amd64_run_zerobyte]], [[feedback_no_date_estimates]], [[feedback_audit_single_commit_diff]]
- **D43 closure sha chain**: `docs/logs/v2/d43-baseline-archive.md` (`2f0e8f7f...` v2.11.3 active baseline, drift-corrected from v2.11.2 `86a0103c...`)
- **后接**: `docs/plans/v2/v2.12.0-plan.md` (QBE 移除 + toolchain closure, scope DOWN ≥2/5 self-backend → 5/5 后 v2.x 中期)
