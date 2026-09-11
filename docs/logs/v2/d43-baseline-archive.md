# D43 closure baseline — historical archive

D43 closure invariant (per [`../plans/v2/v2.0.0-os-prep.md`](../plans/v2/v2.0.0-os-prep.md) § 3 row 10 + [`../../internal/architecture.md`](../../internal/architecture.md) D43 lock):
**v1 编 main.jhyy .il sha == v2 编 main.jhyy .il sha**(阶段性 self-equal;v2.x sub-sprint 改 codegen → 阶段性 break → re-baseline + archive 旧 baseline)。

此文件存 v2.x 期间所有 D43 baseline 阶段值 + 退役旧值 + 验证步骤。

## Timeline

| Sprint | Baseline sha (full) | Status | Note |
|---|---|---|---|
| v2.4.0 末 | `51376ce5721bccb0c81c7deabead1a6012fb76648c424238391018f1890b5761` | **退役**(被 v2.6.6 re-baseline 替代)| hello-freestanding.efi OVMF E2E 5/5 PASS ship 后 stable |
| v2.6.6 | `92e8255473db3395c98bb12c58b473071384b42b897b114cea5fa903d715d25a` | **退役**(被 v2.7.0 末 Commit 2+3 re-baseline 替代)| W-069 真修(NODE_CALL is_extern mangling)后 codegen 微调 |
| v2.7.0 末 | `cc89432920cba92f6c465dd73f5faa575bd9ce8d17d678c7e1f34879e419cf2b` | **退役**(被 v2.8.0 Commit 1 re-baseline 替代)| Commit 2+3 emit_call refactor + ABI imports 微调 codegen .il emit |
| v2.7.1 | (同 v2.7.0 末) | **HOLD 不变**| Phase 1 (runtime files) + Phase 2 (regress.py --cross wire) 不动 codegen |
| v2.7.2 | (同 v2.7.0 末) | **HOLD 不变**| regress.py false-positive 修,driver-only patch,不动 codegen |
| **v2.8.0** | `6a2f2277656ca991bd1c436c4e8bfe14f5d7b33b3587d778e4d8a0e00118af38` | **退役**(被 v2.9.0 src0 revert re-baseline 替代)| Commit 1 codegen_amd64_emit_mem/ctrl/peephole 加 `target_tag: i32` 参数 + state 加 `target_is_win`/`cg_offset_for_temp_with_target`/`compute_offset_for_temp_id_with_target` → ndeccls 1031 → 1034 → IL 大小 591082 → 592311 |
| v2.8.1 | (同 v2.8.0) | **HOLD 不变**| C-side target_dispatch mirror update,不动 codegen |
| v2.8.2 | (同 v2.8.0) | **HOLD 不变**| W-070 真修(jhyy-side cg_module 真 emit SysV QBE IL),但 Commit 1 没动 src0/codegen.jhyy 主体 → IL 大小不变 → D43 hold |
| v2.8.3 | (同 v2.8.0) | **HOLD 不变**| `--no-link` flag + regress.py docker gcc chain infra 补完,driver-only patch,不动 codegen |
| **v2.9.0** | `7aebc1b62ad8b1398d42bff30bdd56b25679ccfc1fb66fc9355be0bd6a43a6a3` | **退役**(被 v2.11.0 + v2.11.1 + v2.11.2 cumulative re-baseline 替代)| Commit 1 src0 revert to `archive/axis-v2-pre-merge`(per 2026-09-08 user decision:v2,v3 merge first, re-branch for v2-C + v3.1.3)→ axis-v3 的 V3-C 3g + 3g.5 + 3g.7 + 3i call-site inference + V3-B 3b naked + 3c volatile 等增量从 src0 撤 → ndeccls 1034 → 1034(保持)+ codegen 主路径微调 → IL 重算 |
| v2.11.0 | (同 v2.9.0) | **HOLD 不变**| W-074 il_len=0 真修 (heap-allocate `il_len_box`) + regress.py `--self-backend` flag,不动 codegen 主路径 IL emit |
| v2.11.1 | (同 v2.9.0) | **HOLD 不变**| W-074.5 lexer gap closure + 7 真修延伸 (dbgfile/dbgloc/{/} + ILTOK_DIRECTIVE + parse_and_emit noop + csltw lexer + next_token_call args consume + struct offset 真修 + emit cast 真修),driver-side patch,不动 codegen 主路径 IL emit |
| **v2.11.2** | `86a0103c34f1bc68e2a1e421cbbf88d72e8b2e31482b4c3dfe7c9101af9d0c0e` | **当前 active baseline**| W-074.6 multi-func self-backend crash/hang closure + IL field contract (int_val = dst temp id 统一) + 2 个新 lexer helpers (`lex_finish_instr` + `lex_consume_to_eol`) + shared parse helpers (5 个 cg_* in state.jhyy) + 7 个 codegen_amd64_*.jhyy 子模块 (lexer/state/emit_ctrl/emit_call/emit_mem/peephole/codegen_amd64) 微调 → ndeccls + IL emit 微量偏移 → IL 重算 |

## Why no v2.7.1 re-baseline?

Per v2.7.1 plan,Phase 3 计划"archive 旧 baseline + 采新"。**但实际 verify 发现**:
- Phase 1 (`8500999` runtime/linux_elf/) — 仅 3 个 NEW 文件(crt0.S + link.ld + README.md)+ .gitignore carveout,**不动 codegen**
- Phase 2 (`911b8da` regress.py) — 仅 1 个 file 改(217 insertions,3 deletions),**全 driver code 不动 codegen**

→ v1 编 main.jhyy .il sha 跟 v2 编 main.jhyy .il sha **仍 byte-equal = v2.7.0 末 baseline `cc89432920cba92f6c465dd73f5faa575bd9ce8d17d678c7e1f34879e419cf2b`**,不需要 re-baseline。

**D43 closure 不变 = v2.7.0 末 baseline `cc894329...` 仍是 canonical self-host 锁**。v2.7.1 主动 hold,避免无意义 re-baseline 引入 churn。

## 何时需要 re-baseline?

按 v2.x sub-sprint 规则(per `feedback_changelog_umbrella`):
- codegen .jhyy 文件改 → D43 可能 break → 必须 verify + 必要时 re-baseline
- codegen_amd64_*.jhyy / target_dispatch.jhyy / abi_amd64_*.jhyy 改 → D43 必 verify
- driver / runtime / regress.py / tests 改 → D43 仍 hold,**无需 re-baseline**

## Verification steps (run any time)

```bash
cd C:/Users/liuzhen/Desktop/coding/JiHuiYiYou-axis-v2

# 1. compile main.jhyy with both sides
./compiler/build/bin/jhyy_v1.exe.exe compile compiler/src0/main.jhyy -o /tmp/_v1.il 2>&1 | tail -3
./compiler/build/bin/jhyy.exe compile compiler/src0/main.jhyy -o /tmp/_v2.il 2>&1 | tail -3

# 2. sha256sum 双 .il
sha256sum /tmp/_v1.il /tmp/_v2.il
# 期望: 两者 sha 相同 == 当前 baseline (v2.11.2 = 86a0103c34f1bc68e2a1e421cbbf88d72e8b2e31482b4c3dfe7c9101af9d0c0e)

# 3. cleanup
rm -f /tmp/_v1.il /tmp/_v2.il
```

## Out of scope

- ❌ V2-C (N 代 fixed point + QBE 移除) — D43 lock 逻辑可能改(N 代后不再 v1→v2 byte-equal 而是 v_N-1 → v_N 收敛),等 v3.1.2 (3g.7) ship 后启动
- ❌ Cross-version (v1 ↔ v2 ↔ v3) closure — D43 是 **同 version internal** (v1=v2 both inside v2 axis);cross-version (v2 vs v3) closure 是 V3-A / V3-B 责任,不在 v2 scope
- ❌ Cross-axis (v2 vs v4) — V4.0 后主版本轴串行(per 2026-09-06 user 决定),但 v2 axis D43 仍 per-version internal

## References

- D43 lock + 历史 baseline 时间线: [`../../internal/architecture.md`](../../internal/architecture.md) line 163 + [`../../internal/workarounds.md`](../../internal/workarounds.md) line 4945 (W-069 entry)
- v2.0.0-os-prep D43 描述: [`../plans/v2/v2.0.0-os-prep.md`](../plans/v2/v2.0.0-os-prep.md) § 3 row 10
- v2.7.0 ship chain 3 commits: `a9c874d` + `abe9111` + `c920695`
- v2.7.1 ship chain 3 commits: `8500999` + `911b8da` + Commit 3 (docs)
- v2.6.6 baseline: commit `224a944` (W-069 真修)
- v2.6.7 baseline (HOLD): commit `c965773` (byte_equal_amd64.sh Commit 5,driver-only 改动)
- v2.6.8 baseline (HOLD): commit `b457e6a` (docs hygiene)
- Memory: [[feedback_changelog_umbrella]] (umbrella convention), [[feedback_audit_single_commit_diff]] (single-commit audit), [[feedback_fix_evaluation_rule]] (5/5 PASS gate)

---

## v2.7.1 post-ship Docker E2E verify (2026-09-08)

**结果**: Phase 1 Linux ELF runtime (crt0.S + link.ld) + 手写 SysV 汇编 → Docker `gcc:12` 容器内链 + 跑 PASS ("hello from Linux ELF", exit 42)。**5 sysv regress tests 真跑仍 blocker** (jhyy codegen `amd64_sysv_freestanding` target 未真实现 + jhyy.exe 调用 Windows-specific WSL vsock API 在 Linux container 失败)。

D43 closure **保持 v2.7.1 baseline `cc894329...` HOLD 不变**(本次 verify 只跑手写汇编测试,不动 jhyy codegen)。

详细 verify 步骤 + Docker MSYS2 PWD bug 记: 见 [`changelog-v2.7.0.md` v2.7.1 post-ship Docker E2E verify section](changelog-v2.7.0.md)
