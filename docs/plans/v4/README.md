# v4.x — post-merge integration axis

**状态**: 🟢 **当前主线 = [`self-backend-perf-plan.md`](self-backend-perf-plan.md)**
(自研后端性能线,v4.2 起);**版本号权威 = [`version-schedule.md`](version-schedule.md)**。

## 目录结构(2026-10-30 调整)

| 文档 | 内容 | 状态 |
|------|------|------|
| [`self-backend-perf-plan.md`](self-backend-perf-plan.md) | **当前主线** —— 自研后端性能线(v4.2 / v4.4 / v4.5) | 🔴 进行中 |
| [`version-schedule.md`](version-schedule.md) | 历史排期轴 —— v4.0.x 已 ship 的逐版记录(§ 三)+ 版本表(§ 四 / § 五.3);⚠️ **§ 一 / § 二是 2026-10-18 的旧快照**,读前先核对现状 | ⚪ 半归档 |
| `active-workaround-clearance.md` | ACTIVE 桶清零的审计轨迹(2026-10-20 已完成,ACTIVE=0) | ⚪ 留档 |
| `JHYY自研后端pass查缺报告.md` | 2026-10-25 的 pass 查缺报告(部分结论已被 2026-10-29 实测推翻) | ⚪ 留档 |
| `v4.0.0-plan.md` … `v4.0.7-plan.md` | 已 ship 的 sprint 记录,**保留为审计轨迹,不合并** | ⚪ 留档 |
| `v4.4.0-plan.md` … `v4.15-plan.md` | **v4.x 版本系列文档(22 份)** —— 每个版本槽一份,见下 | 🔴 预留号 |

## v4.x 版本系列文档(2026-10-30 新建)

**每个版本槽一份 `v4.X.Y-plan.md`**,内容:Context(为什么是这一版)· Goal(可度量)·
Scope(范围)· 验收门(硬指标)· **启动时复核清单** · Critical files · Risks · Out of scope · References。

⚠️ **版本号是「预留号」** —— per「版本号在启动时才分配,不预先占位」,
每份文档开头都标了 🔴 **预留号(未启动)**,**启动那一格时要按当时的实际状态复核**
(每份文档自带「启动时复核清单」)。
⇒ **稳定身份是 `OS-N` 序号**(OS 线)—— 跨版本重排时序号不变。

**性能线**(6 格):

| 版本 | 主题 | 文档 |
|---|---|---|
| v4.4.0 | 寄存器分配 ①:位置映射 + 前瞻窗口缓存(**下一个版本**) | [`v4.4.0-plan.md`](v4.4.0-plan.md) |
| v4.4.1 | 寄存器分配 ②:call-clobber + 寄存器类 | [`v4.4.1-plan.md`](v4.4.1-plan.md) |
| v4.4.2 | 寄存器分配 ③:跨基本块 + phi 并行移动 | [`v4.4.2-plan.md`](v4.4.2-plan.md) |
| v4.4.3 | 寄存器分配 ④:门 + perf 验证 + 去文本耦合 | [`v4.4.3-plan.md`](v4.4.3-plan.md) |
| v4.4.5 | peephole 4096 真修 + IR 优化框架(降级下来的两版) | [`v4.4.5-plan.md`](v4.4.5-plan.md) |
| v4.5 | M5 Part 3(0-C 闭环) | [`v4.5-plan.md`](v4.5-plan.md) |

**OS 线**(16 格,`OS-1`..`OS-16`):

| 版本 | 序号 | 主题 | 文档 |
|---|---|---|---|
| v4.6 | OS-1 | 止血包 | [`v4.6-plan.md`](v4.6-plan.md) |
| v4.7 | OS-2 | 观测(栈上界) | [`v4.7-plan.md`](v4.7-plan.md) |
| v4.8 | OS-3 | 反馈环(最小 kernel.efi) | [`v4.8-plan.md`](v4.8-plan.md) |
| v4.8.5 | OS-4 | 栈与分配 | [`v4.8.5-plan.md`](v4.8.5-plan.md) |
| v4.9 | OS-5 | ABI 收敛 | [`v4.9-plan.md`](v4.9-plan.md) |
| v4.10 | OS-6 | 语言自洽 | [`v4.10-plan.md`](v4.10-plan.md) |
| v4.10.5 | OS-7 | 效果最小集 | [`v4.10.5-plan.md`](v4.10.5-plan.md) |
| v4.11 | OS-8 | lifetime | [`v4.11-plan.md`](v4.11-plan.md) |
| v4.12 | OS-9 | trait + dyn Trait | [`v4.12-plan.md`](v4.12-plan.md) |
| v4.12.3 | OS-10 | const generic | [`v4.12.3-plan.md`](v4.12.3-plan.md) |
| v4.12.5 | OS-11 | HKT(一阶) | [`v4.12.5-plan.md`](v4.12.5-plan.md) |
| v4.13 | OS-12 | 效果骨架 + 锁序 | [`v4.13-plan.md`](v4.13-plan.md) |
| v4.13.5 | OS-13 | 对象模型冻结(manifest) | [`v4.13.5-plan.md`](v4.13.5-plan.md) |
| v4.14 | OS-14 | 能力类型化(`Cap<T>` 真 T) | [`v4.14-plan.md`](v4.14-plan.md) |
| v4.14.5 | OS-15 | 内核数据结构(RCU / PerCpu) | [`v4.14.5-plan.md`](v4.14.5-plan.md) |
| v4.15 | OS-16 | 可信工具链(KASAN / KCFI) | [`v4.15-plan.md`](v4.15-plan.md) |

**v4.16 起**(不排进 OS 线,与之正交):async/await · 包管理器 ·
并发 cap + 完整 memory model · 多架构 ABI —— **不预先落文档**,启动时再领版本号。

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
| **每格的详细 scope** | **v4.x 版本系列文档**(见上)—— `v4.4.0-plan.md` … `v4.15-plan.md` |
| 技术取舍的原始论证 | git 历史(commit `98f4e4c` 之前)—— 启动某项时再翻 |

**未排期的工作不再预先排期** —— 版本号在**启动时**才分配。

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
- **跨边界冲突**走 [`../../coordination/JHYY_编译器侧设计终版.md`](../../coordination/JHYY_编译器侧设计终版.md)
  § 1 的分工公式 + [`../../coordination/JHYY_OS侧设计终版.md`](../../coordination/JHYY_OS侧设计终版.md) § 6 的语言—内核边界
- **D43 阶段性 self-equal** hold:v4.x 每 sub-sprint ship 重新 baseline

## 命名约定(2026-10-30 修订 + 2026-10-30 第二次修订)

- **进行中的工作**:`self-backend-perf-plan.md` 之类的描述性文件名,不用版本号
- **已 ship 的 sprint**:保留 `v4.X.Y-plan.md` 原名 —— 它们是审计轨迹,
  改名会破坏跟 changelog / commit 的对应关系
- **已排期的版本槽**:性能线与 OS 线的每一格**预先落一份 `v4.X.Y-plan.md`**(2026-10-30 新建 22 份)
  ⇒ 但**版本号仍是「预留号」**,启动那一格时按实际状态复核(每份自带「启动时复核清单」)
- **未排期的工作**(v4.16+ 那批:async / 包管理器 / 并发 cap / 多架构 ABI):
  **不预先落文档**(2026-10-30 删 `backlog.md` 的决定)——
  启动时新建描述性 plan 文件 + 在 `version-schedule.md` 领版本号
- 不写独立 L4 详细实现方案(per `feedback_small_plans_no_docs`)

> ⚠️ 本条取代了原「每个 minor version 一份 `v4.X.Y-plan.md`」的约定
> (原 per `feedback_plans_per_version`)。版本号在启动时分配,不预先占位。
>
> ⚠️ **2026-10-30 第二次修订**:本仓重新引入了「每版本一份 `v4.X.Y-plan.md`」,
> 但**限定在已排期的版本槽上**(性能线 v4.4.0–v4.5 + OS 线 v4.6–v4.15),
> 且**版本号是预留号** —— 稳定身份是 `OS-N` 序号,跨版本重排时序号不变。

## L1 长篇

- [`../roadmap/v4.x-post-merge.md`](../roadmap/v4.x-post-merge.md) — v4.x 长线设计 + 决策锁 + 跨边界问题 + 强/弱依赖图
- [`../../coordination/JHYY_编译器侧设计终版.md`](../../coordination/JHYY_编译器侧设计终版.md) — OS 线的 P0–P4.5 分期与硬门(与本轴正交)
- [`../../coordination/JHYY_OS侧设计终版.md`](../../coordination/JHYY_OS侧设计终版.md) — 内核形态 + capability 对象模型 + `.jhyynb` 契约 + 语言—内核边界

## Changelog

- `docs/logs/v4/changelog-v4.0.0.md` — v4 axis 唯一 umbrella changelog,
  per `feedback_changelog_umbrella`
- 任何一项 ship 时,在该 umbrella 追加段落,不新建 standalone changelog
