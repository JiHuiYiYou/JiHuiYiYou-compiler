# docs/logs/v1/ — jhyy 自举时代 changelog + sprint 实施日志

本目录放 **jhyy 自举**（v1.x）时代的版本日志和 sprint 实施日志。

**当前内容**:v1.0.0 自举 ✅ **TAGGED 2026-08-10**(commit `eabee0d`,取代 v1.0.0-rc `3e19b64`)— Stage 2 三层 N=3 byte-equal 闭环(.il sha `2445e97d...` 1.378 MB, jhyy_v1/2/3/4 .il 全部同 sha)+ regress_v1 持平 50/53 baseline。目录里是:
- `changelog-v1.0.0.md` — v1.0.0 收尾 changelog(取代 v1.0.0-rc)
- `changelog-v1.0.0-rc.md` — v1.0.0-rc 实用闭环历史(2026-08-10 ship)
- `changelog-v1.1.0.md` — v1.1.0 wip(2026-08-11+,sprint 3h-3n 准备)
- `retrospective-v1.0.0.md` — v1.0.0 复盘(2026-08-10)
- sprint 2-4 commit 实施日志(per-commit 快照)

## 命名约定

| 文件类型 | 命名 |
|---|---|
| 版本 changelog | `changelog-vX.Y.Z.md`（v1.0.0 收尾时建）|
| Sprint 实施日志 | `sprint-N-commit-M-*.md` |
| Sprint 末 codegen 坑 | `sprint-N-codegen-bugs.md`（参考 [`../v0/changelog-v0.6.3.md`](../v0/changelog-v0.6.3.md) 格式）|

## 关联

- jhyy 自举 sprint 计划 → [`../../plans/v1/`](../../plans/v1/)
- vX.Y 轴路线图 → [`../../plans/roadmap/`](../../plans/roadmap/)
- C 端编译器 changelog → [`../v0/`](../v0/)