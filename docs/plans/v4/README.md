# docs/plans/v4/ — v4.x 计划线

> **本目录是索引。** 排期表、版本号、OS-N 映射在
> [`docs/internal/FACTS.md`](../../internal/FACTS.md) § 4 —— **不要在这里复述那些数字**。
>
> ⚠️ **版本号是「预留号」** —— 每份 plan 开头都标了「启动时按实际状态复核」，
> 启动那一格时要重新核对。**稳定身份是 `OS-N` 序号**（OS 线），跨版本重排时序号不变。

---

## 目录结构

| 文档 | 内容 | 状态 |
|---|---|---|
| [`self-backend-perf-plan.md`](self-backend-perf-plan.md) | **性能线总纲**（v4.2 / v4.4 / v4.5） | 🔄 当前主线 |
| `v4.4.0-plan.md` … `v4.4.5-plan.md` + `v4.5-plan.md` | 性能线各版本槽（6 份） | 🔴 预留号 |
| `v4.6-plan.md` … `v4.15-plan.md` | OS 线各版本槽（16 份，OS-1 … OS-16） | 🔴 预留号 |

> **已 ship 的 v4 sprint 计划**（v4.0.0 … v4.0.7）+ 已完结的排期轴 + 清零审计
> ⇒ [`docs/archive/plans/v4/`](../../archive/plans/v4/)。

---

## 每份 plan 的统一结构

Context（为什么是这一版）· Goal（可度量）· Scope（范围）· **验收门（硬指标）** ·
**启动时复核清单** · Critical files · Risks · Out of scope · References。

---

## 两条线的关系

| 线 | 版本段 | 内容 |
|---|---|---|
| **性能线**（当前主线） | v4.4.x + v4.5 | 自研后端的寄存器分配与 IR 优化 |
| **OS 线** | v4.6 … v4.15 | 从编译器侧看 OS 线：能力类型化 / 效果系统 / 内核数据结构 / 可信工具链 |

**不是「并行正交」，是被切成两段**：OS 线的前置（寄存器分配）就是性能线的 v4.4。

⇒ 两条线的完整映射表（含 OS-N 序号）见 [`docs/internal/FACTS.md`](../../internal/FACTS.md) § 4。

---

## 启动一格之前

1. 读 [`docs/internal/FACTS.md`](../../internal/FACTS.md) § 4 —— 确认这一格现在是什么状态
2. 读那份 plan 的 **「启动时复核清单」** —— 逐条核对（很多数字是写计划时的快照）
3. 确认前置是否满足（OS 线那几格有硬前置）
4. 确认**版本号**（预留号可能已被别的 sprint 占用 —— 启动时才分配）

---

## 相关

- 事实（版本 / 回归数 / 排期 / OS-N 映射）⇒ [`docs/internal/FACTS.md`](../../internal/FACTS.md)
- 历史计划 ⇒ [`docs/archive/plans/`](../../archive/plans/)
- 跨项目设计 ⇒ [`docs/coordination/`](../../coordination/)
