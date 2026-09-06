# v4.x — post-merge serial axis (concept only)

**状态**: ⏳ **概念阶段**(per 2026-09-06 user:"v4 现在还没出文档，但是其实有这个概念")

## 范围

v4.x 是 v2.x + v3.x axes merge 后的主版本轴 — **串行**,不再有 v2 ‖ v3 并行。

**触发**:v2-C v2.8.0 ship + v3.x 全关键路径 ship + user 决定 merge 时机 → 推 v4.0.0(merge commit + 删 axis-v2/axis-v3 worktree/branch)。

## 当前内容(per-version plan,均 ⏳ 未启动)

### v4.0 — merge
- [`v4.0.0-plan.md`](v4.0.0-plan.md) — v2+v3 axes merge → main axis push(机械 merge,不开新 worktree)

### v4.1 — 工具链闭环
- [`v4.1.0-plan.md`](v4.1.0-plan.md) — M5 删 `src/*.c` + untrack QBE + 删 `runtime.c`(per 2026-09-06 决定从 v2/v3 后 → v4.x)

### v4.2-v4.6 — 语言成熟化(原本 v3.x 中/末)
- [`v4.2.0-plan.md`](v4.2.0-plan.md) — async/await + Future runtime
- [`v4.3.0-plan.md`](v4.3.0-plan.md) — lifetime 完整版 + Polonius borrow check
- [`v4.4.0-plan.md`](v4.4.0-plan.md) — closure 增强 (move / borrow capture / generic / trait object)
- [`v4.5.0-plan.md`](v4.5.0-plan.md) — const generic
- [`v4.6.0-plan.md`](v4.6.0-plan.md) — trait objects (dyn Trait)

### v4.7-v4.9 — UX/性能
- [`v4.7.0-plan.md`](v4.7.0-plan.md) — 3k 错误恢复
- [`v4.8.0-plan.md`](v4.8.0-plan.md) — 3m 基本优化 pass
- [`v4.9.0-plan.md`](v4.9.0-plan.md) — 3n 包管理器

### v4.10-v4.11 — 高级类型系统 / 多线程
- [`v4.10.0-plan.md`](v4.10.0-plan.md) — HKT + specialization
- [`v4.11.0-plan.md`](v4.11.0-plan.md) — 并发 cap + 完整 memory model + 多架构 ABI

## 决策锁

- **v2.x ‖ v3.x 并行结束**:v4.0.0 merge 后,主版本轴串行
- **M5 推到 v4.1.0**(per 2026-09-06 user)
- **非 OS-required 抽象 feature 全推到 v4.x**(per 2026-09-06 决定)— v3.x 只做 OS-required
- **跨边界冲突**走 [`../../../jhyy_OS/docs/coordination.md`](../../../jhyy_OS/docs/coordination.md) § 7 规则(同 v3.x)
- **D43 阶段性 self-equal** hold:v4.x 每 sub-sprint ship 重新 baseline

## 命名约定

### 待 ship(per-version)
- `v4.X.Y-plan.md` — 每个 minor version 一份(per `feedback_plans_per_version` 规则)
- 不写 `batch-V4-X-plan.md`(per-version 替代)
- 不写独立 L4 详细实现方案(per `feedback_small_plans_no_docs`)

### L1 长篇(未写,概念阶段)
- `roadmap/v4.x-post-merge.md`(待启动)— 完整 v4.x 长线设计、决策锁、跨边界问题

## Changelog(占位,实际 ship 后建)

- `docs/logs/v4/changelog-v4.0.0.md` — v4.0.0 merge umbrella(v4.0.0 ship 时建)
- `docs/logs/v4/changelog-v4.1.md` — v4.1.x umbrella(v4.1.0 ship 时建)
- 后续每个 v4.X.0 建对应 umbrella(per `feedback_changelog_umbrella`)
