# v4.x — post-merge integration axis

**状态**: 🔴 **当前唯一进行中的是** [`active-workaround-clearance.md`](active-workaround-clearance.md)
(6 处活 workaround 真修,per 2026-10-10 user 决定「必须在 v4 正式版清零,大不了 v4 不发」)

## 目录结构(2026-10-15 调整)

| 文档 | 内容 | 优先级 |
|------|------|--------|
| [`active-workaround-clearance.md`](active-workaround-clearance.md) | **当前工作项** — W-103..W-107 六处活 workaround 真修 | 🔴 最高 |
| [`backlog.md`](backlog.md) | 12 项未启动的未来工作(M5 / async / lifetime / closure / const generic / trait / 错误恢复 / 优化 / 包管理 / HKT / 并发 cap / `.jhyynb`) | 🟢 低 |
| `v4.0.0-plan.md` … `v4.0.7-plan.md` | 已 ship 的 sprint 记录,**保留为审计轨迹,不合并** | — |

**2026-10-15 变更:** 原 `v4.1.0-plan.md` … `v4.12.0-plan.md` 共 12 份合并为
单一 [`backlog.md`](backlog.md),**不再以版本号命名**。理由:这 12 项全部未启动,
版本号承诺了一个并不存在的排期,让「v4.12.0」听起来像既定里程碑。

版本号在**启动时**才分配,不预先占位。

## 范围

v4.x 是 v2.x + v3.x axes merge 后的主版本轴 — **integration axis**,不再有独立 v2 ‖ v3 axes。

**触发**:v2-C v2.8.0 ship + v3.x 全关键路径 ship + user 决定 merge 时机 → 推 v4.0.0。

**并行/串行**(per `feedback_no_blind_serial_rule`):v4.x 内部 sub-sprint **按依赖图决定
并行/串行**,**不**预设「single-line serial」元规则。依赖图见
[`backlog.md` 总览](backlog.md):

- 强串行链:`lifetime → closure → dyn Trait → HKT`
- 可并行:M5 / async / 错误恢复 / 优化 / 包管理 / 并发 cap / `.jhyynb`

## v4.0 阶段当前状态

- **v4.0.0-rc1 shipped 2026-09-30**(axis-v2 + axis-v3 merge 入 main;Gate 3 self-host deferred)
- **W-097 / W-101 / W-102 已 RESOLVED**(2026-10-15),自举闭环达成(`closure_check.sh` PASS)
- **索引表 6 ACTIVE / 0 DEFERRED**(2026-10-15)—— 6 条全是本次新登记的
  W-103..W-107,详情与优先级见 [`active-workaround-clearance.md`](active-workaround-clearance.md)
- **v4.0.0 final tag 未打** —— 按 user 2026-10-10 政策,须先清零 ACTIVE

## 决策锁

- **v2.x ‖ v3.x 并行结束**:v4.0.0 merge 后,无独立跨轴 parallel
- **M5 推到 v4.1**(per 2026-09-06 user)→ 现为 `backlog.md § 1`
- **非 OS-required 抽象 feature 全推到 v4.x**(per 2026-09-06 决定)— v3.x 只做 OS-required
- **跨边界冲突**走 [`../../../jhyy_OS/docs/coordination.md`](../../../jhyy_OS/docs/coordination.md) § 7 规则
- **D43 阶段性 self-equal** hold:v4.x 每 sub-sprint ship 重新 baseline
  (backlog 里的 N17…N27 是旧计划按序推演的编号,启动时按实际代数重定)

## 命名约定(2026-10-15 修订)

- **未启动的工作**:合并进单一 `backlog.md`,**不以版本号命名**
- **进行中的工作**:`active-*.md` 之类的描述性文件名,同样不用版本号
- **已 ship 的 sprint**:保留 `v4.X.Y-plan.md` 原名 —— 它们是审计轨迹,
  改名会破坏跟 changelog / commit 的对应关系
- 不写独立 L4 详细实现方案(per `feedback_small_plans_no_docs`)

> ⚠️ 本条**取代**了原「每个 minor version 一份 `v4.X.Y-plan.md`」的约定
> (原 per `feedback_plans_per_version`)。版本号在启动时分配,不预先占位。

## L1 长篇

- [`../roadmap/v4.x-post-merge.md`](../roadmap/v4.x-post-merge.md) — v4.x 长线设计 + 决策锁 + 跨边界问题 + 强/弱依赖图

## Changelog

- `docs/logs/v4/changelog-v4.0.0.md` — v4.0.x umbrella(v4 axis 唯一 changelog,
  per `feedback_changelog_umbrella`)
- backlog 中任何一项 ship 时,在该 umbrella 追加段落,不新建 standalone changelog
