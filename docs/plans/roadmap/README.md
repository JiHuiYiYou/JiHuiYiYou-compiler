# docs/plans/roadmap/ — vX.Y 轴长线路线图（L1）

本目录放项目 **vX.Y 轴** 长线方向的 L1 路线图。每份文件描述一个 vX.Y 轴的最终目标、当前进度、依赖、阻塞点。

## 文件清单

| 文件 | vX.Y 轴 | 状态 | 简介 |
|------|---------|------|------|
| [`v0.0-skeleton.md`](v0.0-skeleton.md) | v0.x | 已完成 | 早期骨架（v0.0 时代产物）|
| [`v0.2.x-to-v1.0-roadmap-original.md`](v0.2.x-to-v1.0-roadmap-original.md) | v0.x → v1.x | 历史保留 | v0.2 → v1.0 原始路线图（被 v0.x-c-compiler-roadmap.md + v1.0-self-hosting.md 取代）|
| [`v0.x-c-compiler-roadmap.md`](v0.x-c-compiler-roadmap.md) | **v0.x** | **进行中**（v0.8 wip）| C 端编译器演进到自举门槛 |
| [`v1.0-self-hosting.md`](v1.0-self-hosting.md) | **v1.x** | 未启动（启动门槛已达成）| jhyy 编译器编译自己（`.il` byte-equal 闭环）|
| [`v2.x-qbe-rewrite.md`](v2.x-qbe-rewrite.md) | **v2.x** | 未启动（中期，待 v1.0 后）| QBE 完整重写 + 多目标 / 自研 OS 准备（amd64_sysv / 多目标 / freestanding）|
| [`v3.x-language-expansion.md`](v3.x-language-expansion.md) | **v3.x** | 未启动（语言特性扩展）| OS-required 特性（inline asm / volatile / naked / no_std / `&mut` + lifetime）— 服务于 jhyy_OS |

## sprint 级计划（L3 / L4）

sprint 级任务清单和详细实现方案按版本号轴单独目录组织：

- **v0.x** sprint 计划（v0.4 / v0.5 / v0.6 / v0.7 / v0.8）→ [`../v0/`](../v0/)
- **v1.x** sprint 计划（v1.0.0 自举）→ [`../v1/`](../v1/)
- **v2.x / v3.x** sprint 计划待相应路线图启动后再建

## 版本轴语义

项目只用版本号轴，不用 phase-X 双轴。版本轴对应表：

| phase-X（旧） | vX.Y（新）|
|---|---|
| phase-0 | v0.0（已完成）|
| phase-1 | v0.x |
| phase-2 | v1.x |
| phase-2.5 | v2.x |
| phase-3 | v3.x |

历史 changelog / 早期 sprint / 已完成 sprint 计划 / 锁定 spec 里的 phase-N 措辞**不改**（保留历史叙述）；新文档一律用 vX.Y。