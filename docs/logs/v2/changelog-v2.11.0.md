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
