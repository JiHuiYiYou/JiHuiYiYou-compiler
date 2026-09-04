# Changelog — v2.2.0 (umbrella: spec 锁定 — ABI § 13 + lang-spec § 17-20)

> **承接**: v2.1.0 ship (`8ac3608`, 2026-09-03) — QBE-level ABI 抽离完成;`abi_amd64_win.jhyy` / `abi_amd64_win_freestanding.jhyy` / C-side mirror 同步就位,byte-equal 5/5 PASS + selfhost closure 4-stage .il byte-equal sha=`312ee9ff`。
> **触发**: v2.1.0 ship 后立刻启动(per 2026-09-01 user 决定的 5 版本串行 sprint 计划)。**v2.0 阶段 Sprint A Stage 3** = 把已 ship 的 ABI + freestanding 约定**写进 spec**(之前只在 plan doc + 散在 C 端),让 v2.3.0 hello-freestanding.efi + v2.4.0 byte-equal + v3.x M1 联调有 100% 权威 spec 可对。
> **scope**(per [`v2.2.0任务清单 + 概要设计.md`](../../plans/v2/v2.2.0任务清单 + 概要设计.md)):
> - `docs/abis/jhyy-abi-v1.0.0.md` 增 § 13(多 target ABI + freestanding 约定 + UEFI 跟 MS x64 对齐)
> - `docs/abis/jhyy-lang-spec-v1.3.0.md` 增 § 17-20(OS 启动前置 + freestanding 模式 + Debug ABI + Wire Format)
> - `docs/internal/build.md` 更新(multi-target dispatch 说明)
> - 跟 jhyy_OS 端 cross-check(per `coordination.md § 0` Critical Path)
>
> **重要**: v2.2.0 是 v2.0 阶段 Sprint A 收尾,**纯文档改动**,不涉及代码逻辑变更。**spec 是 100% 权威文档**(per CLAUDE.md),改动必须 lock-in review。
>
> **关键 discipline**(同 v2.0.0 umbrella):
> - Author `JHYY <15901598712@163.com>` + Co-author `MiniMax-M3 <noreply@MiniMax>`
> - Doc fact-check 逐条(per `feedback_doc_refactor_factcheck`)— spec 改动 review 必严
> - lock-in review 必严:spec 改错一个数字 → OS 端 codegen 联动全错

---

## Sprint 状态总览

> **2026-09-03 收**: v2.2.0 ✅ **shipped** (commits `262b83a` / `c743ed5` / `eb710de` / `896a329`, 2026-09-03,**4 commits 串行 ship**)。**未打 v2.2.0 tag**(per v2.0 阶段策略 = 阶段 ship 后才打 tag,v2.3.0 / v2.4.0 是 阶段首批 tag)。
>
> **多 commit 原因**: v2.2.0 是纯文档改动,拆 4 commits 以保单 doc 单 commit reviewable:
> 1. `262b83a` Stage 1 — abi-v1.0.0 § 13/§ 14 restructure + 删重复 § 12
> 2. `c743ed5` Stage 2 — lang-spec § 17-20
> 3. `eb710de` Stage 3a — build.md multi-target dispatch
> 4. `896a329` Stage 3b — plan doc audit-note fix

| Sprint | 状态(2026-09-04) | 摘要 |
|--------|-----------------|------|
| v2.0.0 | ✅ shipped `719ec25` 2026-09-02 | target dispatcher 起步 |
| v2.1.0 | ✅ shipped `8ac3608` 2026-09-03 | QBE-level ABI 抽离 |
| **v2.2.0** | ✅ shipped `896a329` 2026-09-03 | spec 锁定(ABI § 13 + lang-spec § 17-20 + build.md)|
| v2.3.0 | ✅ shipped tag `v2.3.0` `54d93df` 2026-09-04 | hello-freestanding.efi 跑 OVMF |
| v2.4.0 | ✅ shipped tag `v2.4.0` `7fb735b` 2026-09-04 | 多目标 dispatcher + byte-equal 三件套 |
| v3.0 3a-3f | 🟡 等 user 启动 | **v2.0 阶段 ship ✅ = 启动前置全部解除** |

---

## v2.2.0 实际 ship 内容(per commit chain `262b83a`..`896a329`)

### 改动(`docs/abis/jhyy-abi-v1.0.0.md`)
- 增 **§ 13 — 多 target ABI + freestanding 约定**:
  - amd64_win(Windows x64 hosted)— 4 参数寄存器 + shadow space + struct sret(per MS x64;`v2.1.0任务清单 + 概要设计.md § 1.1.1`)
  - amd64_win_freestanding(UEFI 风格)— 复用 MS x64 signature shaping + no_crt_init + EFI entry emit(per D-GUI-12, UEFI = MS x64)
  - amd64_sysv_stub(Linux x64,实 impl 推 v2.x M2)— 占位 + 错误信息明确指向 M2
- 增 **§ 14 — UEFI 跟 MS x64 对齐说明**(per D-GUI-12)
- 删重复 § 12(老 § 12 内容并入 § 13,避免双写)

### 改动(`docs/abis/jhyy-lang-spec-v1.3.0.md`)
- 增 **§ 17 — OS 启动前置**: 描述 M1 launch 链路对 jhyy-side 的硬前置(target dispatcher + ABI 抽离 + freestanding 编通)
- 增 **§ 18 — freestanding 模式**: 描述 `#[no_std]` 软 ship 边界(v3.0 3d 落地前)
- 增 **§ 19 — Debug ABI**(per D41 锁): DebugEvent 56B / ErrChain 64B / ProvenanceInfo 136B(per `jhyy_OS/docs/v0.0.4-debug-abi.md`)
- 增 **§ 20 — Wire Format**(per D40): wire-format ↔ jhyy-side 表达规则 — wire 有 `*_len` → `[*]T` 切片;NULL 结尾链 → `*T` 裸指针;Cap<T> wire format 草案 syntax-only(forward-looking,3g.5 落地前 layout 待锁)

### 改动(`docs/internal/build.md`)
- 增 multi-target dispatch 说明:--target=amd64_win / amd64_win_freestanding 调用流程 + amd64_sysv 报错信息

### Plan doc audit-note fix(`v2.2.0任务清单 + 概要设计.md`)
- L5: stale "v2.0 阶段尚未启动" → 实际 v2.0.0 / v2.1.0 ✅ shipped
- L7: "前置(v2.1.0 🟡 待 ship(前置))" → "前置(v2.1.0 ✅ shipped, commits a4b857d..8ac3608, 2026-09-03)"
- L65 Stage 1.1.2 ABI 差异表 column 修: "amd64_sysv (预留 v2.x M2)" → "amd64_sysv_stub (实 impl 推 v2.x M2)";函数 entry 行 `main (CRT 调)` → `main_jhyy (CRT 调)`;struct pass-by-value 行 amd64_win_freestanding 加 "(同 MS x64)";是否 link glibc/musl 行 amd64_sysv_stub 列加 "(hosted, post v2.x M2) / (freestanding, post v2.x M2)"

### jhyy_OS 端 cross-check
- 跨项目 spec 一致性 per `coordination.md § 0` Critical Path + `v2.0.0-os-prep.md § 3`
- v2.2.0 期间无 open 跨边界问题(13 Q + 6 UD 决定 全部闭环,per `coordination.md § 6`)

### Binary 状态
- v2.2.0 纯文档改动,**jhyy.exe binary 不变** = sha=`376084bacd70dab15b22f6cb11d024c2e2cab67d24ccca313b8a0fcd134f3205`(同 v2.0.0 → v2.1.0, frozen 持续)
- selfhost closure 4-stage byte-equal sha=`312ee9ff`(per v2.1.0 baseline,文档不改 IL 输出)

### 验收
- ✅ abi-v1.0.0 § 13 + § 14 锁
- ✅ lang-spec § 17-20 锁
- ✅ build.md multi-target dispatch 说明就位
- ✅ jhyy_OS 端 cross-check pass(per `coordination.md § 0` Critical Path)
- ✅ regress 持平 v2.1.0 actual baseline(104/104 PASS)— 文档改动不退步

---

## 关键决策点(per `coordination.md § 3` + `v2.0.0-os-prep.md § 3`)

| # | 决策 | 落点 | v2.2.0 落点 |
|---|------|------|------|
| **D40** | wire-format ↔ jhyy-side 表达规则 | lang-spec § 20 锁;Cap<T> wire format 草案 syntax-only | lang-spec § 20 ✅ |
| **D41** | Debug ABI spec 🔒 锁 + 所有权;DebugEvent 56B / ErrChain 64B / ProvenanceInfo 136B | lang-spec § 19 锁 | lang-spec § 19 ✅ |
| **D-GUI-12** | UEFI = EFIAPI = MS x64 | abi § 13/14 锁;`abi_amd64_win_freestanding` 复用 `abi_amd64_win` | abi § 13/14 ✅ |

---

## 关键数字(2026-09-03 锁定)

| 数字 | 值 | 来源 |
|------|-----|------|
| regress baseline | 104/104 PASS, 0 failed, 4 skipped | v2.2.0 持平 v2.1.0 |
| selfhost closure | v1↔v2↔v3↔v4 .il byte-equal sha=`312ee9ff` | v2.1.0 baseline(commit `8ac3608` 显式 pin);v2.2.0 纯文档改动,src0 IL emit 不变,closure 链持续 hold |
| jhyy.exe binary sha | `376084bacd70dab15b22f6cb11d024c2e2cab67d24ccca313b8a0fcd134f3205` | v2.0.0 → v2.3.0 frozen |
| abi-v1.0.0 § 13 范围 | ~200 行新增 | `v2.2.0任务清单 + 概要设计.md` Stage 1 估算 |
| lang-spec § 17-20 范围 | ~150 行新增 | 同上 Stage 2 估算 |
| build.md 更新 | ~50 行新增 | 同上 Stage 3 估算 |
| Debug ABI 尺寸 | DebugEvent 56B / ErrChain 64B / ProvenanceInfo 136B | `jhyy_OS/docs/v0.0.4-debug-abi.md`(D41 锁)|
| 跨边界 open 问题 | 0 | 13 Q + 6 UD 决定 全部闭环,per `coordination.md § 6` |

---

## 跨 sprint 影响

- **v2.1.0 → v2.2.0**: 严格顺序(ABI 抽离完成 = spec 锁定前置,§ 13 描述多 target ABI 才有 ground truth)✅
- **v2.2.0 → v2.3.0**: 严格顺序(spec 锁 = E2E 启动验证前置,lang-spec § 17 OS 启动前置 + § 18 freestanding 模式 = hello-freestanding.efi 跑 OVMF 的 spec 依据)✅
- **v2.2.0 → v2.4.0**: 严格顺序(spec § 13 multi-target = multi-target dispatcher CLI 完整化依据;spec § 19 Debug ABI + § 20 Wire Format = byte-equal 三件套 D26 复盘依据)✅
- **v2.2.0 → v3.x**: 间接(spec § 17-20 = v3.0 3a inline asm / 3b #[naked] / 3c volatile / 3d #[no_std] / 3e #[link_section] / 3f memory barrier 的 spec 锚点)— 等 v3.0 3a-3f 启动
- **v2.2.0 → M1 launch**: 间接(M1 launch 链路 compiler 侧 = v2.0 阶段 + v3.0 3a-3c/3e-3f;v2.2.0 锁 spec = 链路 spec 端就位)

---

## 关联文档

- v2.2.0 任务清单 → [`../../plans/v2/v2.2.0任务清单 + 概要设计.md`](../../plans/v2/v2.2.0任务清单 + 概要设计.md)
- abi-v1.0.0 spec → [`../../abis/jhyy-abi-v1.0.0.md`](../../abis/jhyy-abi-v1.0.0.md)(v2.2.0 加 § 13/14)
- lang-spec-v1.3.0 → [`../../abis/jhyy-lang-spec-v1.3.0.md`](../../abis/jhyy-lang-spec-v1.3.0.md)(v2.2.0 加 § 17-20)
- build.md → [`../../internal/build.md`](../../internal/build.md)(v2.2.0 multi-target dispatch)
- Debug ABI 锁来源 → [`../../../../jhyy_OS/docs/v0.0.4-debug-abi.md`](../../../../jhyy_OS/docs/v0.0.4-debug-abi.md)
- 跨项目 OS 端 spec mirror → [`../../../../jhyy_OS/docs/coordination.md`](../../../../jhyy_OS/docs/coordination.md)
- 阶段其他 umbrella → [v2.0.0](changelog-v2.0.0.md) / [v2.1.0](changelog-v2.1.0.md) / [v2.3.0](changelog-v2.3.0.md) / [v2.4.0](changelog-v2.4.0.md)
