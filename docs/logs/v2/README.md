# docs/logs/v2/ — v2.x 时代 changelog + sprint 实施日志

本目录放 **v2.x**（QBE 重写 + 多目标 + OS 准备）时代的版本日志和 sprint 实施日志。

**当前状态(2026-09-01)**:**v2.0 阶段未启动**(`git tag -l "v2*"` = 空;最新 tag = `v1.8.3` shipped 2026-08-29)。`v2.0.0` 是下一个待启动 sprint(Sprint A Stage 1: target dispatcher 起步,per [`v2-v3-parallel-sprint-plan.md § 5.1`](../../plans/roadmap/v2-v3-parallel-sprint-plan.md))。

**v2.0 阶段规划**(2026-09-01 user 决定,5 版本串行 ship):
- `v2.0.0` Sprint A Stage 1: target dispatcher 起步
- `v2.1.0` Sprint A Stage 2: ABI 抽离
- `v2.2.0` Sprint A Stage 3: spec 锁定
- `v2.3.0` Sprint B: hello-freestanding.efi 跑 OVMF
- `v2.4.0` Sprint C: 多目标 dispatcher + byte-equal 三件套

**v3.0 3a-3f 等 v2.0 阶段 ship 后才启动**(per 2026-09-01 user 决定,放弃原"v2.0 跟 v3.0 sprint 3a-3f 同时推进"的 wall-clock 并行优化)。

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
