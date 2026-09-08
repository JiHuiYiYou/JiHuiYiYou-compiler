# D43 closure baseline — historical archive

D43 closure invariant (per [`../plans/v2/v2.0.0-os-prep.md`](../plans/v2/v2.0.0-os-prep.md) § 3 row 10 + [`../../internal/architecture.md`](../../internal/architecture.md) D43 lock):
**v1 编 main.jhyy .il sha == v2 编 main.jhyy .il sha**(阶段性 self-equal;v2.x sub-sprint 改 codegen → 阶段性 break → re-baseline + archive 旧 baseline)。

此文件存 v2.x 期间所有 D43 baseline 阶段值 + 退役旧值 + 验证步骤。

## Timeline

| Sprint | Baseline sha (full) | Status | Note |
|---|---|---|---|
| v2.4.0 末 | `51376ce5721bccb0c81c7deabead1a6012fb76648c424238391018f1890b5761` | **退役**(被 v2.6.6 re-baseline 替代)| hello-freestanding.efi OVMF E2E 5/5 PASS ship 后 stable |
| v2.6.6 | `92e8255473db3395c98bb12c58b473071384b42b897b114cea5fa903d715d25a` | **退役**(被 v2.7.0 末 Commit 2+3 re-baseline 替代)| W-069 真修(NODE_CALL is_extern mangling)后 codegen 微调 |
| v2.7.0 末 | `cc89432920cba92f6c465dd73f5faa575bd9ce8d17d678c7e1f34879e419cf2b` | **当前 active baseline**(v2.7.1 hold)| Commit 2+3 emit_call refactor + ABI imports 微调 codegen .il emit |
| v2.7.1 | (同 v2.7.0 末) | **HOLD 不变**| Phase 1 (runtime files) + Phase 2 (regress.py --cross wire) 不动 codegen |

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
# 期望: 两者 sha 相同 == 当前 baseline (v2.7.1 = cc89432920cba92f6c465dd73f5faa575bd9ce8d17d678c7e1f34879e419cf2b)

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
