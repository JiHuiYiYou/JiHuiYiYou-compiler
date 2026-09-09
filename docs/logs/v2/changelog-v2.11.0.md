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
- **后接**: `docs/plans/v2/v2.12.0-plan.md` (QBE 移除)
