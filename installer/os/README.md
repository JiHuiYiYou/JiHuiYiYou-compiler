# jhyy_OS installer placeholder

本目录是 jhyy_OS MSI 的 placeholder, 当前 **空**. v1.5.0 ship 时不实际包含 OS installer, 只是给后续 OS sprint 留个目录 + README。

## 状态

- v1.5.0 (本 sprint): 占位, 仅 `.gitkeep` + 本 README
- v1.5.0+ (后续 OS sprint): 由 jhyy_OS 团队填实际 MSI 内容

## 为什么现在占位

v1.5.3 Burn bundle (per `docs/plans/v1/v1.5.0任务清单 + 概要设计.md` § Sprint v1.5.3) 设计成"一处 bundle, 多个 MSI chain" — Burn bundle 可以链 compiler MSI (本项目出) + 未来 OS MSI (OS 团队出)。`installer/os/` 目录结构预留, OS 团队后续 sprint 决定实际 OS MSI 内容怎么放, 直接 commit 进本目录即可, 不影响 compiler MSI 的 build path。

## 跨项目协调

参见 [`../../jhyy_OS/docs/coordination.md`](../../jhyy_OS/docs/coordination.md) § 0 Critical Path — OS 启动 M1-M11 里程碑里, installer 是 OS 启动前的依赖项 (OS 用户需要先装 JHYY 才能 build OS kernel)。

## 不在 v1.5 scope

- OS MSI 实际内容 (由 jhyy_OS 团队 sprint 设计)
- OS installer 测试 (需要 OS image, 不在本项目 CI 范围)
