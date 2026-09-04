# docs/plans/v2/ — v2.x sprint 计划（QBE 自写 + 多目标 + OS 准备）

本目录放 **v2.x**（QBE 自写 + 多目标 / 自研 OS 准备）的 sprint 级计划。

**当前状态**：v2.0 阶段 (v2.0.0 → v2.4.0) ✅ 全 ship (2026-09-02 ~ 09-04, tags `v2.3.0` / `v2.4.0`);v2.x 中/末 ⏳ 未启动,等 user 启动。

## 文件清单

| 文件 | 状态 | 简介 |
|------|------|------|
| [`v2.0.0-os-prep.md`](v2.0.0-os-prep.md) | 设计文档 | OS 编写前置的语言 / 编译基础设施清单（M1-M11 节点 + P0/P1/P2 优先级）|
| [`v2.0.0任务清单 + 概要设计.md`](v2.0.0任务清单 + 概要设计.md) | **sprint 计划**(2026-09-01 user 决定) | v2.0.0 = Sprint A Stage 1: target dispatcher 起步 |
| [`v2.1.0任务清单 + 概要设计.md`](v2.1.0任务清单 + 概要设计.md) | **sprint 计划** | v2.1.0 = Sprint A Stage 2: ABI 抽离（Windows x64 + UEFI 风格）|
| [`v2.1.0详细实现方案.md`](v2.1.0详细实现方案.md) | **sprint 计划**(详细实现) | v2.1.0 = 每个 ABI 函数的具体实现 + codegen 抽离调用细节 + byte-equal 验证脚本 |
| [`v2.2.0任务清单 + 概要设计.md`](v2.2.0任务清单 + 概要设计.md) | **sprint 计划** | v2.2.0 = Sprint A Stage 3: spec 锁定（abi § 13 + lang-spec § 18-21 + build.md）|
| [`v2.3.0任务清单 + 概要设计.md`](v2.3.0任务清单 + 概要设计.md) | **sprint 计划** | v2.3.0 = Sprint B: hello-freestanding.efi 跑 OVMF（EFI struct + lld-link + QEMU 启动 + printk）|
| [`v2.4.0任务清单 + 概要设计.md`](v2.4.0任务清单 + 概要设计.md) | **sprint 计划** | v2.4.0 = Sprint C: 多目标 dispatcher + byte-equal 三件套（cross-jhyy-version 验证）|

## 版本轴关系（关键）

**v2.0 阶段（v2.0.0 → v2.1.0 → v2.2.0 → v2.3.0 → v2.4.0）= 串行**（2026-09-01 user 决定）：
- 串行原因：每版在前版 baseline 上做，byte-equal 阶段性 self-equal 必须严格顺序（per D43）
- 跨版不能并行：v2.1.0 ABI 抽离依赖 v2.0.0 target dispatcher 起步；v2.2.0 spec 锁定依赖 v2.1.0 ABI 实现；v2.3.0 E2E 启动依赖 v2.2.0 spec 锁；v2.4.0 byte-equal 三件套依赖 v2.3.0 E2E 通
- v2.0 阶段 ship 后才启动 v2.x 中/末 + v3.0 3a-3f（per [`../roadmap/v2-v3-parallel-sprint-plan.md § 5.1` 路径 A](../roadmap/v2-v3-parallel-sprint-plan.md)）

**v2.x 中/末 ‖ v3.0+ = 异步并行**（2026-09-01 user 决定）：
- 不强配对：两条线各自推进，不要求 v3.0 启动跟 v2.x 中/末对齐
- 三条硬约束保留（per [`../roadmap/v2-v3-parallel-sprint-plan.md § 5.1-5.3`](../roadmap/v2-v3-parallel-sprint-plan.md)）：D27 v3.1 3g→3g.5→3g.7 串行 / v3.0 3c volatile 先 ship 再 v2.x 后端移植 volatile / v3.0 3d `#[no_std]` 软 ship（M1 launch 不依赖 per D10）

## 关联

- v2.x 长线路线图 → [`../roadmap/v2.x-qbe-rewrite.md`](../roadmap/v2.x-qbe-rewrite.md)
- v2.x ‖ v3.x 并行 sprint 调度 → [`../roadmap/v2-v3-parallel-sprint-plan.md`](../roadmap/v2-v3-parallel-sprint-plan.md)
- 上一代（v1.x 自举）→ [`../v1/`](../v1/)
- 自研 OS（独立 repo）→ `../../../jhyy_OS/`