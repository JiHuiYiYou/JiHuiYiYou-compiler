# jhyy_OS installer placeholder

> **Last updated**: v1.8.3 (2026-08-29) — v1.x 已终结。OS installer scope **仍 deferred**,由 jhyy_OS 团队在后续 OS sprint 启动时填具体 WXS / Bundle / ProgId / CustomAction。详见 [`docs/plans/v2/v2.0.0-os-prep.md`](../../docs/plans/v2/v2.0.0-os-prep.md) § OS 启动链路 + [`../../../jhyy_OS/docs/coordination.md`](../../../jhyy_OS/docs/coordination.md) § 0 Critical Path。

本目录是 jhyy_OS MSI 的 placeholder,当前**仅** `.gitkeep` + 本 README,无任何 WXS / Bundle / MSI 产物。

## 状态

- ✅ v1.5.0: 占位 ship(仅 `.gitkeep` + README)
- ✅ v1.8.3: 仍占位,**v1.x 终结** — 无 OS installer scope
- ⏳ OS sprint 启动后:由 jhyy_OS 团队填实际 MSI 内容(预计跟 compiler MSI 走 Burn bundle chain,per `docs/plans/v2/v2.0.0-os-prep.md` § OS MSI chain)

## 为什么本目录仍占位

v1.5.3 Burn bundle (per `docs/plans/v1/v1.5.0任务清单 + 概要设计.md` § Sprint v1.5.3) 设计成"一处 bundle,多个 MSI chain" — Burn bundle 链 compiler MSI(本项目出)+ 未来 OS MSI(OS 团队出)。`installer/os/` 目录结构预留,OS 团队后续 sprint 决定实际 OS MSI 内容怎么放,直接 commit 进本目录即可,不影响 compiler MSI 的 build path。

**v1.5 → v1.8 期间**:Burn bundle chain 设计未变,directory 保留;OS MSI scope 推到 v2.x 末 / v3.x 末 OS sprint(per `docs/plans/roadmap/v2-v3-parallel-sprint-plan.md` M1-M11 节点表)。

## 跨项目协调

参见 [`../../../jhyy_OS/docs/coordination.md`](../../../jhyy_OS/docs/coordination.md) § 0 Critical Path — OS 启动 M1-M11 里程碑里, installer 是 OS 启动前的依赖项(OS 用户需要先装 JHYY 才能 build OS kernel)。**当前 13 个 Q + 6 个 UD 决定 全部闭环/锁**(per coordination.md § 6 + § 8),无 open 跨边界问题阻塞 OS sprint 设计。

跨边界决策涉及 OS installer 的部分(per v2.0.0-os-prep § 3):
- **D6**: `Cap<T>` 8 字节 — OS 侧 cap node 内存布局,直接影响 OS kernel ABI(不影响 OS MSI installer 范围)
- **D41**: Debug ABI spec 锁 — DebugEvent / ErrChain / ProvenanceInfo 三级标记(同样不直接影响 OS MSI)
- OS MSI installer 本身**未单列**跨边界决策 — 由 OS sprint 设计时新增

## 不在 v1.x scope

- OS MSI 实际内容(WXS / Bundle / CustomAction)— 由 jhyy_OS 团队 sprint 设计
- OS installer 测试(需要 OS image,不在本项目 CI 范围)
- OS installer publish(winget / scoop)— 跟 compiler installer 一起推到 v2.x

## 不在本目录范围

- `installer/compiler/` — compiler MSI(WiX 主文件)
- `installer/common/jhyy-setuc/` — UserChoice hash 写入 CLI(.NET 8,per v1.8.3 ship)
- `installer/build.ps1` — Burn bundle build script

## v2.x 启动后待办

v2.x OS sprint 启动后,本目录需新增:
- `installer/os/OsMsi.wxs`(或类似)— OS MSI 主 WiX 文件
- `installer/os/Bundle.wxs`(或修改 compiler `Bundle.wxs` 加 OS MSI chain)
- `installer/os/CLAUDE.md`(局部项目指令,跟 `installer/CLAUDE.md` 对齐)
- `installer/os/build.ps1`(可选,或统一在 `installer/build.ps1` 加 `os` target)
- `installer/os/README.md`(本文件)— 更新成 v?.? OS MSI shipped 版本

具体设计由 jhyy_OS 团队 sprint plan 决定,**不在 compiler 侧 sprint 设计 scope**。