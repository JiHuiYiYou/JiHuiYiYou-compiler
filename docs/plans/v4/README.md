# v4.x — post-merge integration axis

**状态**: 🟢 **当前主线 = [`self-backend-perf-plan.md`](self-backend-perf-plan.md)**
(自研后端性能线,v4.2 起);**版本号权威 = [`version-schedule.md`](version-schedule.md)**。

## 目录结构(2026-10-30 调整)

| 文档 | 内容 | 状态 |
|------|------|------|
| [`self-backend-perf-plan.md`](self-backend-perf-plan.md) | **当前主线** —— 自研后端性能线(v4.2 / v4.4 / v4.5) | 🔴 进行中 |
| [`version-schedule.md`](version-schedule.md) | **版本号唯一权威** —— 「下一个版本做什么」在这里;**§ 五 = OS 线(P0–P4.5)接入版本轴** | 🔴 进行中 |
| `active-workaround-clearance.md` | ACTIVE 桶清零的审计轨迹(2026-10-20 已完成,ACTIVE=0) | ⚪ 留档 |
| `JHYY自研后端pass查缺报告.md` | 2026-10-25 的 pass 查缺报告(部分结论已被 2026-10-29 实测推翻) | ⚪ 留档 |
| `v4.0.0-plan.md` … `v4.0.7-plan.md` | 已 ship 的 sprint 记录,**保留为审计轨迹,不合并** | ⚪ 留档 |

### ⚠️ `backlog.md` 已删除(2026-10-30)

原 `backlog.md` 合并了 `v4.1.0-plan.md` … `v4.12.0-plan.md` 共 12 份未启动工作
(async / lifetime / closure / const generic / trait / 错误恢复 / 优化 / 包管理 /
HKT / 并发 cap / `.jhyynb` / M5 Part 3)。

**删除理由:** 那份文档的依赖图**已经被它自己标注为过期**(M5 只剩 Part 3 且
排到 v4.5;第 8 项优化 pass 被降级到 v4.4 之后),验收基线停在 163/163(现 257),
还挂着指向已删除的 `jhyy_OS/docs/coordination.md` 的链接 ⇒ **它是一份会误导
未来规划的僵尸排期表**。

**那 12 项没丢** —— 它们的清单与排序现由两处承担:

| 内容 | 现在在哪 |
|---|---|
| 版本归属 + 「下一个做什么」 | [`version-schedule.md`](version-schedule.md) § 四(v4.5 / v4.6+ 两行) |
| 详细 scope 与技术取舍 | git 历史(commit `98f4e4c` 之前)—— 启动某项时再翻,不预先占位 |

**未启动的工作不再预先排期** —— 版本号在**启动时**才分配。

## 范围

v4.x 是 v2.x + v3.x axes merge 后的主版本轴 — **integration axis**,不再有独立 v2 ‖ v3 axes。

**触发**:v2-C v2.8.0 ship + v3.x 全关键路径 ship + user 决定 merge 时机 → 推 v4.0.0。

**并行/串行**(per `feedback_no_blind_serial_rule`):v4.x 内部 sub-sprint **按依赖图决定
并行/串行**,**不**预设「single-line serial」元规则。当前依赖图见
[`version-schedule.md`](version-schedule.md) § 四:

- 强串行链:`lifetime → closure → dyn Trait → HKT`(v4.6+,与性能线正交,可并行)
- 当前串行主线:性能线 `v4.2(✅) → v4.4 → v4.5`,`v4.4.5+` 收降级下来的两版;
  OS 线从 `v4.6` 起接在后面(`version-schedule.md` § 五的 OS-1..OS-16)

## v4.0 阶段当前状态

- **v4.1.2 已发布**(2026-10-29)—— 当前最新 release
- **台账 ACTIVE = 0 / DEFERRED = 0**(2026-10-27 复核)
- **回归** 257 PASS + 0 XFAIL + 0 failed + 20 SKIP(277 total)
- **v4.2 已完成**:v4.2.0 可信性能门 · v4.2.1 帧尺寸按需(W-167)
- **v4.4.0 阶段一已完成**:寄存器分配器基础设施 + 安全网(默认关,产物逐字节不变)

## 决策锁

- **v2.x ‖ v3.x 并行结束**:v4.0.0 merge 后,无独立跨轴 parallel
- **跨边界冲突**走 [`../../coordination/JHYY_决策总纲.md`](../../coordination/JHYY_决策总纲.md)
  § 3 的裁决规则(编译器侧文档为本仓 `docs/coordination/` 5 份)
- **D43 阶段性 self-equal** hold:v4.x 每 sub-sprint ship 重新 baseline

## 命名约定(2026-10-30 修订)

- **进行中的工作**:`self-backend-perf-plan.md` 之类的描述性文件名,不用版本号
- **已 ship 的 sprint**:保留 `v4.X.Y-plan.md` 原名 —— 它们是审计轨迹,
  改名会破坏跟 changelog / commit 的对应关系
- **未启动的工作**:不预先落文档(2026-10-30 删 `backlog.md` 的决定);
  启动时新建描述性 plan 文件 + 在 `version-schedule.md` 领版本号
- 不写独立 L4 详细实现方案(per `feedback_small_plans_no_docs`)

> ⚠️ 本条取代了原「每个 minor version 一份 `v4.X.Y-plan.md`」的约定
> (原 per `feedback_plans_per_version`)。版本号在启动时分配,不预先占位。

## L1 长篇

- [`../roadmap/v4.x-post-merge.md`](../roadmap/v4.x-post-merge.md) — v4.x 长线设计 + 决策锁 + 跨边界问题 + 强/弱依赖图
- [`../../coordination/JHYY_决策总纲.md`](../../coordination/JHYY_决策总纲.md) — OS 线的 P0–P4.5 分期与硬门(与本轴正交)

## Changelog

- `docs/logs/v4/changelog-v4.0.0.md` — v4 axis 唯一 umbrella changelog,
  per `feedback_changelog_umbrella`
- 任何一项 ship 时,在该 umbrella 追加段落,不新建 standalone changelog
