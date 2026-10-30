# archive — 历史归档

> **这里放「已经发生过的」东西。**
> **不要在这里找现状** —— 当前状态在 [`docs/FACTS.md`](../FACTS.md)，当前计划在
> [`docs/plans/v4/`](../plans/v4/)，规范在 [`docs/abis/`](../abis/)。
>
> 归档的内容**不改**（那是审计轨迹）。它描述的是当时的世界，可能与现在矛盾 —— 那正是
> 归档的意义。

---

## 分类

| 目录 | 内容 | 份数 |
|---|---|---|
| [`logs/`](logs/) | 各版本轴的 changelog + sprint 实施日志 + D43 基线台账 | 62 |
| [`plans/`](plans/) | v0–v4 各轴的 sprint 计划与路线图 | 115 |
| [`perf/`](perf/) | 已被取代的性能测量数据 | 2 |
| [`audit/`](audit/) | codegen 深审报告 + RCA | 5 |

### `logs/` — 按版本轴分

| 轴 | umbrella changelog | 覆盖 |
|---|---|---|
| v0 | `logs/v0/changelog-v0.0.1.md` … `logs/v0/changelog-v0.9.0.md`（13 份） | C 编译器自身，冻结于 v1.0.0 baseline |
| v1 | `logs/v1/changelog-v1.0.0.md` … `logs/v1/changelog-v1.8.0.md`（10 份） | jhyy 自举，终结于 v1.8.3 |
| v2 | `logs/v2/changelog-v2.0.0.md` … `logs/v2/changelog-v2.13.0.md`（13 份） | QBE 重写 + 多目标，终结于 v2.16.0 |
| v3 | `logs/v3/changelog-v3.0.md` … `logs/v3/changelog-v3.4.md`（5 份） | 语言特性扩展，终结于 v3.4.2 |
| v4 | `logs/v4/changelog-v4.0.0.md`（**1 份 umbrella**，3212 行） | 当前轴 —— v4.0.0 → v4.1.2 全部版本 |

**umbrella 约定**（现行）：**一条版本轴只有一个 umbrella changelog**，patch 版本回填进
它。v4 轴已按此收敛（2026-10-30）；**v0 / v1 轴是历史遗留**（一个轴 10–13 份
standalone），当时约定尚未立 ⇒ 不追溯重写。

### `plans/` — 按版本轴分

`plans/v0|v1|v2|v3/`（历史轴的 sprint 计划与「任务清单 + 概要设计」）·
`plans/roadmap/`（L1 长线路线图，含 v0.2.x-to-v1.0-roadmap-original 这类明确标注
「已被取代」的历史稿）· `plans/v2-v3/`（已作废的跨轴并行计划 + OS 准备计划，
**SUPERSEDED 2026-09-29**）· `plans/v4/`（**已 ship 的 v4 sprint 记录** ——
v4.0.0 … v4.0.7，以及已完结的排期轴与清零审计）· `plans/bootstrap-v1.0-README.md`
（v1.0 自举驱动说明）。

> ⚠️ `plans/v2-v3/` 两份的前提（v2.x 中/末 + v3.0 3a-3f ship）**从未成立**。
> 跨项目设计基线现单点在 [`docs/coordination/`](../coordination/)。

---

## 命名约定

| 文件名 | 含义 |
|---|---|
| `changelog-vX.Y.Z.md` | 版本 changelog（现行：每轴一个 umbrella，文件名取该轴最早的 minor） |
| `sprint-N-commit-M-*.md` | sprint 实施日志 |
| `retrospective-vX.Y.Z.md` | 版本复盘 |
| `logs/v2/d43-baseline-archive.md` | D43 字节相等基线台账 |
| `vX.Y.Z-plan.md` | sprint 计划（已 ship 或预留号） |
| `vX.Y.Z任务清单 + 概要设计.md` | v0–v2 早期的 sprint 文档 |
| `batch-VN-X-plan.md` | 某条轴的批量 sprint 计划 |

---

## `[[feedback_*]]` 代号说明

本目录（以及仓内其它文档）里出现的 `[[feedback_xxx]]` / `feedback_xxx` 是**旧
memory 文件的代号**。那批 memory 已于 2026-10-30 合并进仓库根
[`CONTRIBUTING.md`](../../CONTRIBUTING.md) § 工作规约 —— 通用规约（提交身份 /
验证纪律 / Git 破坏性操作 / 文档与措辞 / 台账纪律 / jhyy 编译器特有规则）现在在那里，
按代号可查。

> 本目录的这些代号是**历史脚注**，保留原文不改。

---

## 相关

- 当前事实：[`docs/FACTS.md`](../FACTS.md) · 当前计划：[`docs/plans/v4/`](../plans/v4/)
- 全仓文档索引：[`docs/internal/README.md`](../internal/README.md)
- 台账（永不归档）：[`docs/workarounds.md`](../workarounds.md)
