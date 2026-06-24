# docs/plans/v1/ — jhyy 自举 sprint 计划（jhyy 编译器编译自己）

本目录放 **v1.0.0 phase-2 自举**（`compiler/src0/*.jhyy` 翻译 C 编译器到 jhyy）的 sprint 级计划。每个 sprint 一份任务清单 + 详细实现方案。

版本号对应 jhyy 编译器自身版本（目标 v1.0.0 = 自举闭环）：
- `v1.0.0任务清单 + 概要设计.md` — v1.0.0 phase-2 总览
- `v1.0.0详细实现方案.md`

C 端编译器 sprint 计划 → [`../v0/`](../v0/)

远期 phase-N 路线图 → [`../phase/`](../phase/)

**自举时的 C 端 patch**（v0.6.2 / v0.6.3 等 phase-2 实测沉淀的 codegen / sema bug 修复）→ 改 `compiler/src/*.c` + `docs/logs/v0/changelog-v0.6.X.md`，**不属于本目录**（属于 v0 时代）。
