# docs/logs/v2/ — v2.x 时代 changelog + sprint 实施日志

本目录放 **v2.x**(QBE 重写 + 多目标 + OS 准备)时代的版本日志和 sprint 实施日志。

**当前状态(2026-09-04)**:**v2.0 阶段 ship 完成** ✅ — v2.0.0 (`719ec25`, 2026-09-02) / v2.1.0 (`8ac3608`, 2026-09-03) / v2.2.0 (`896a329`, 2026-09-03) / v2.3.0 (tag `v2.3.0`, `54d93df`, 2026-09-04) / v2.4.0 (tag `v2.4.0`, `7fb735b`, 2026-09-04) 全 ship。`git tag -l "v2*"` = `v2.3.0` + `v2.4.0`(阶段收尾 tag,per 2026-09-04 user 决定: 阶段首批 ship 即可打 tag, 不再等阶段全部 ship)。

**v2.0 阶段 5 sprint 串行 ship**(2026-09-01 user 决定,放弃原"v2.0 跟 v3.0 sprint 3a-3f 同时推进"的 wall-clock 并行优化):
- `v2.0.0` Sprint A Stage 1: target dispatcher 起步 — ✅ shipped `719ec25` 2026-09-02
- `v2.1.0` Sprint A Stage 2: ABI 抽离 — ✅ shipped `8ac3608` 2026-09-03
- `v2.2.0` Sprint A Stage 3: spec 锁定 — ✅ shipped `896a329` 2026-09-03
- `v2.3.0` Sprint B: hello-freestanding.efi 跑 OVMF — ✅ shipped tag `v2.3.0` `54d93df` 2026-09-04
- `v2.4.0` Sprint C: 多目标 dispatcher + byte-equal 三件套 — ✅ shipped tag `v2.4.0` `7fb735b` 2026-09-04

**v3.0 3a-3f 启动前置全部解除** = **等 user 启动**:
- v3.0 3a = inline asm
- v3.0 3b = #[naked] fn
- v3.0 3c = volatile load/store
- v3.0 3e = #[link_section]
- v3.0 3f = memory barrier
- v3.0 3d = #[no_std] + core(**软 ship**, M1 launch 不依赖 per D10)

> **关键里程碑**:v2.0 阶段 ship = v2.0 OS 准备里程碑视图(`docs/plans/v2/v2.0.0-os-prep.md` § 1 M1 launch 链路)compiler 侧全部就位。M1 launch = jhyy_OS 编 `kernel.efi` 跑 OVMF + printk,等 v3.0 3a-3c/3e-3f 全 ship 后启动。

## 命名约定(per `docs/logs/v1/README.md` 镜像)

| 文件类型 | 命名 |
|---|---|
| 版本 changelog | `changelog-vX.Y.Z.md`(每个 vX.Y minor axis 一个 umbrella,patch 回填) |
| Sprint 实施日志 | `sprint-N-commit-M-*.md` |
| Sprint 末 codegen 坑 | `sprint-N-codegen-bugs.md`(参考 [`../v1/changelog-v1.8.0.md`](../v1/changelog-v1.8.0.md) 格式) |

**changelog umbrella 约定**(per `feedback_changelog_umbrella.md`):
- vX.Y axis 只 1 个 umbrella changelog(不创建 standalone `changelog-vX.Y.Z-wNNN.md`)
- Umbrella 包含:承接上版本 + 触发原因 + scope 决策 + sprint 状态总览表 + 关键数字表 + 决策点 + 跨 sprint 影响
- Patch 版本(vX.Y.Z where Z>0)— 内容回填到 vX.Y 的 umbrella changelog

## 关联

- v2.x sprint 计划 → [`../../plans/v2/`](../../plans/v2/)
- v2.x ‖ v3.x 并行 sprint 调度 → [`../../plans/roadmap/v2-v3-parallel-sprint-plan.md`](../../plans/roadmap/v2-v3-parallel-sprint-plan.md)
- v2.x QBE 自写长线路线图 → [`../../plans/roadmap/v2.x-qbe-rewrite.md`](../../plans/roadmap/v2.x-qbe-rewrite.md)
- v3.x 语言扩展长线路线图 → [`../../plans/roadmap/v3.x-language-expansion.md`](../../plans/roadmap/v3.x-language-expansion.md)
- 上代(v1.x jhyy 自举)→ [`../v1/`](../v1/)
- 跨项目 OS 时间线 → [`../../../../jhyy_OS/docs/coordination.md`](../../../../jhyy_OS/docs/coordination.md)
- v2.0 阶段 5 个 umbrella → [`changelog-v2.0.0.md`](changelog-v2.0.0.md) / [v2.1.0](changelog-v2.1.0.md) / [v2.2.0](changelog-v2.2.0.md) / [v2.3.0](changelog-v2.3.0.md) / [v2.4.0](changelog-v2.4.0.md)
