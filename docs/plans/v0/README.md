# docs/plans/v0/ — C 编译器 sprint 计划（C 端编译器自身演进）

本目录放 **C 端编译器**（`compiler/src/*.c`）的 sprint 级计划。每个 sprint 一份任务清单 + 详细实现方案。

版本号对应 C 编译器版本（当前 v0.8 wip，最近发版 v0.6.3 + 多个 v0.6.x patch）：
- `v0.4.0任务清单 + 概要设计.md` — v0.4 sprint 计划（struct pass-by-value）
- `v0.4.0详细实现方案.md`
- `v0.5.0任务清单 + 概要设计.md` — v0.5 sprint 计划（浮点 + break/continue）
- `v0.5.0详细实现方案.md`
- `v0.6.0任务清单 + 概要设计.md` — v0.6 sprint 计划（自举前最后一期）
- `v0.6.0详细实现方案.md`
- `v0.7.0任务清单 + 概要设计.md` — v0.7 sprint 计划（enum first-class + 顶层 const 数组）
- `v0.7.0详细实现方案.md`
- `v0.8.0任务清单 + 概要设计.md` — v0.8 sprint 计划（自举路径清理）

**vX.Y 轴后续**（已在 [`../roadmap/`](../roadmap/) 下）：
- v2.x = QBE 完整重写 + 多目标 / 自研 OS 准备 → [`../roadmap/v2.x-qbe-rewrite.md`](../roadmap/v2.x-qbe-rewrite.md)
- v3.x = 语言特性扩展（OS-required：inline asm / volatile / naked / no_std / `&mut` + lifetime）→ [`../roadmap/v3.x-language-expansion.md`](../roadmap/v3.x-language-expansion.md)

v1.0.0 自举 sprint 计划 → [`../v1/`](../v1/)

**C 端编译器的 changelog** 在 [`../../logs/v0/`](../../logs/v0/)（v0.0.1 → v0.8 wip 全套 changelog）。