# docs/plans/v1/ — jhyy 自举 sprint 计划（jhyy 编译器编译自己）

本目录放 **v1.0.0 自举**（`compiler/src0/*.jhyy` 翻译 C 编译器到 jhyy）的 sprint 级计划。每个 sprint 一份任务清单 + 详细实现方案。

版本号对应 jhyy 编译器自身版本（目标 v1.0.0 = 真自举闭环，定义为 `.il byte-equal`）：
- `v1.0.0任务清单 + 概要设计.md` — v1.0.0 总览（粗粒度 5 sprint）
- `v1.0.0详细实现方案.md`
- `v1.0-sprint-3-launch.md` — v1.0 sprint 3 5 task 粗粒度合并 (v0.9 wip commit 2.18 视角, 部分过期)
- `v1.0-post-50-53-plan.md` — **当前活跃**: 50/53 → byte-equal Stage 2 → v2.x || v3.x 完整计划 (commit 2.47 视角)

C 端编译器 sprint 计划 → [`../v0/`](../v0/)

**vX.Y 轴后续**（已在 [`../roadmap/`](../roadmap/) 下）：
- v2.x = QBE 完整重写 + 多目标 / 自研 OS 准备 → [`../roadmap/v2.x-qbe-rewrite.md`](../roadmap/v2.x-qbe-rewrite.md)
- v3.x = 语言特性扩展（OS-required）→ [`../roadmap/v3.x-language-expansion.md`](../roadmap/v3.x-language-expansion.md)

**自举时的 C 端 patch**（v0.6.2 / v0.6.3 / v0.6.5 / v0.8 commit 1 等实测沉淀的 codegen / sema bug 修复）→ 改 `compiler/src/*.c` + `docs/logs/v0/changelog-v0.6.X.md`（属于 v0 时代）。