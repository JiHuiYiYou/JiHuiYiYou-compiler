# v3.x 语言扩展 — 计划目录 (mirror v0/v1/v2)

**状态**: 🟢 **轴活跃** (V3-A + V3-B + V3-C v3.1.0 已 ship;V3-C v3.1.1 / v3.1.2 待 ship)

## 范围

v3.x 是语言特性扩展轴,服务于 [jhyy_OS](../../../jhyy_OS/) 的 OS-required 语言特性:

| Sprint | 特性 | 用途 | 状态 |
|--------|------|------|------|
| v3.0.0 (3d) | `#[no_std]` / `#![no_std]` | 切掉 runtime / panic_handler,写 freestanding kernel | ✅ **ship**(V3-A,feat commit `4fa06e2`)|
| v3.0.1 (3a) | inline asm | OS kernel 写汇编片段 (e.g. cpuid, msr, lgdt) | ✅ **ship**(V3-B,commit 89c9d34)|
| v3.0.2 (3b) | `#[naked]` fn | 不生成 prologue/epilogue (boot / interrupt entry) | ✅ **ship**(V3-B,commit 6f9c19b)|
| v3.0.3 (3c) | volatile load/store | 防止编译器 reorder (MMIO 设备寄存器) | ✅ **ship**(V3-B,commit 0bad962)|
| v3.0.4 (3e) | `#[link_section]` | 自定义目标 section (e.g. `.text.boot`) | ✅ **ship**(V3-B,commit 2058f1a)|
| v3.0.5 (3f) | memory barrier | compiler fence (e.g. `fence_seq_cst`) | ✅ **ship**(V3-B,commit 8f6e6fe)|
| **v3.1.0 (3g)** | `&T` / `&mut T` + NLL (stub) + `Cap<T>` 8 字节布局 | OS 模块间共享指针的 borrow check (per D11 决策) | ✅ **ship**(V3-C,commit d0b0f79)|
| v3.1.1 (3g.5) | PhantomData<T> ZST + Cap 组合 | `Cap<PhantomData<X>>` 8 字节布局保持 | ⏳ **待 ship**(D27 锁串行,v3.1.0 ship 后启动)|
| v3.1.2 (3g.7) | CapTable<T> + 跨函数 cap pass | jhyy_OS cap 表 byte-equal 联调 | ⏳ **待 ship**(D27 锁串行,v3.1.1 ship 后启动)|
| v3.1.3 patch | SysV abi_amd64_sysv.jhyy Cap<T> class backport | SysV target 跨函数 Cap<T> register 分配 | ⏳ **待 ship**(V2-B v2.7.0 ship 后启动)|
| v3.2.0 (3i) | generics(单态化)| 泛型函数 / struct / enum + 单态化 | ⏳ **未启动**(M8d + M11 硬前置,per D-GUI-11)|
| v3.2.1 (3j) | closures | `{fn_ptr, captured_env}` + 合成函数 | ⏳ **未启动**(M8d + M11 硬前置,3i ship 后启动)|
| v3.2.2 (3l.1) | std lib 基础(mem / fmt / string / arena)| jhyy 编译器自身用 | ⏳ **未启动**(M11 硬前置,3j ship 后)|
| v3.2.3 (3l.2) | std lib IO(io / os)| jhyy 编译器自身用 | ⏳ **未启动**(M11 硬前置,3l.1 ship 后)|
| v3.2.4 (3l.3) | std lib 泛型容器(vec / map)| jhyy 编译器自身用 `Vec<T>` | ⏳ **未启动**(M11 硬前置,3l.1 + 3i ship 后)|
| v3.2.5 (3l.4) | std lib 数学(math,FFI libm)| jhyy 编译器自身用 | ⏳ **未启动**(M11 硬前置,3l.1 + 3h ship 后)|
| 3h | 浮点类型 | f32 / f64 + 算术 | ⏳ **未启动**(MVP 不依赖,3l.4 前置)|
| 3k | 错误恢复 | 多错误同时报告 | ⏳ **未启动**(MVP 不依赖,UX 改进)|
| 3m | 基本优化 pass | 常量折叠 / 死代码消除 | ⏳ **未启动**(自举后性能,3l.4 后推)|
| 3n | 包管理器 | jhyy new / build / test | ⏳ **未启动**(M11 之后)|

完整 v3 未完成工作 → 9 个 per-version plan 文件(见下方"当前内容")。

完整 OS 启动链路 (`M1 → M11`) 见 [`../v2/v2.0.0-os-prep.md`](../v2/v2.0.0-os-prep.md)。

## 决策锁 (per `project_v2_v3_parallel_axes`)

- v2.x ‖ v3.x 并行推进 (semver 推论 v2.99 < v3.0 但实际 OS M1 启动前两轴各自达成即可)
- 每 sprint 设计前必读 [`../v2/v2.0.0-os-prep.md`](../v2/v2.0.0-os-prep.md) § 1 OS 启动里程碑表 + § 3 关键决策点 (D1-D11 / D18 / D27 / D42 / D43 / D-GUI-11 / D-GUI-12)
- 跨边界冲突走 [`../../../jhyy_OS/docs/coordination.md`](../../../jhyy_OS/docs/coordination.md) § 7 规则

## 跨轴 + branch 约定 (per `v2-v3-parallel-sprint-plan.md § 6`)

- **axis-v3** = v3 axis long-lived integration branch(fork 自 `main @ 7fb735b` v2.4.0)
- **顺序做的后面不开新 worktree**(per 2026-09-06 user 决定):v3.1.1 / v3.1.2 / v3.1.3 patch + 后续 3i/3j/3l/3h 直接 axis-v3 commit + tag,**不**开新 worktree
- **D43 阶段性 self-equal**:每 sub-sprint ship 重新 baseline sha(v3.0.0~0.5 + v3.1.0 ship 时已锁定 N0~N6)
- **D27 串行锁**:v3.1 3g → 3g.5 → 3g.7 不可调换
- **D42 锁**:3a inline asm 走 QBE .s 输出路径(已完成),v2.x 自写后端 escape hatch 后续移植
- **D-GUI-11 锁**:3i + 3j 升级为 M8d + M11 硬前置(compositor surface / buffer / seat interface 需 generic over T;seat focus callback 是闭包式)

## 当前内容

### 已 ship (batch plan)
- [`batch-V3-A-plan.md`](batch-V3-A-plan.md) — V3-A v3.0.0 3d `#[no_std]` 试水 ✅ ship
- [`batch-V3-B-plan.md`](batch-V3-B-plan.md) — V3-B v3.0.1..v3.0.5 = 3a/3b/3c/3e/3f M1-required 5 件套 ✅ ship
- [`batch-V3-C-plan.md`](batch-V3-C-plan.md) — V3-C v3.1.0 ✅ ship(v3.1.1 / v3.1.2 per-version plan 见下)

### 待 ship / 未启动 (per-version plan)
- [`v3.1.1-plan.md`](v3.1.1-plan.md) — 3g.5 PhantomData<T> ZST codegen(D27 锁:v3.1.0 ship 后启动)
- [`v3.1.2-plan.md`](v3.1.2-plan.md) — 3g.7 CapTable<T> + 跨函数 cap pass(D27 锁:v3.1.1 ship 后启动,M4 launch 触发前置)
- [`v3.1.3-plan.md`](v3.1.3-plan.md) — SysV abi_amd64_sysv.jhyy Cap<T> class backport patch(V2-B v2.7.0 ship 后启动)
- [`v3.2.0-plan.md`](v3.2.0-plan.md) — 3i generics(单态化,M8d + M11 硬前置,per D-GUI-11)
- [`v3.2.1-plan.md`](v3.2.1-plan.md) — 3j closures(M8d + M11 硬前置,3i ship 后启动)
- [`v3.2.2-plan.md`](v3.2.2-plan.md) — 3l.1 std lib 基础(mem / fmt / string / arena,M11 硬前置)
- [`v3.2.3-plan.md`](v3.2.3-plan.md) — 3l.2 std lib IO(io / os,M11 硬前置)
- [`v3.2.4-plan.md`](v3.2.4-plan.md) — 3l.3 std lib 泛型容器(vec / map,M11 硬前置)
- [`v3.2.5-plan.md`](v3.2.5-plan.md) — 3l.4 std lib 数学(math,FFI libm,M11 硬前置,3h ship 后启动)

### 抽象 feature / v3.x 中/末 / M5
(未编 version 号的 feature 仍走 [`../roadmap/v3.x-language-expansion.md`](../roadmap/v3.x-language-expansion.md) 的设计草案 — 3h 浮点 / 3k 错误恢复 / 3m 基本优化 / 3n 包管理器 / v3.x 中/末 features / M5 删 C runtime)

## 命名约定

### 已 ship (batch)
- `batch-V3-X-plan.md` — V3-A/B/C 用 batch-letter 命名(V3-A/B 全 ship 后冻结;V3-C v3.1.0 ship 后冻结,v3.1.1/v3.1.2 转 per-version)
- 详细:`batch-V3-X-详细实现方案.md`

### 待 ship (per-version,2026-09-06 user 决定)
- **`v3.X.Y-plan.md`** — 每个 minor version 一份(per user:每个小版本一个 plan 文件)
- 不写 `batch-V3-D-plan.md`(原"未完成工作盘点"伞型 doc 拆分为 9 个 per-version)
- L3 任务清单 + 概要设计 + 验收 + 风险 + Commit/tag 节奏 + Cross-ref 整合到一份 plan
- 不写独立 L4 详细实现方案(per `feedback_small_plans_no_docs` 单 stage 改动不写独立 L4)

## Changelog

- [`docs/logs/v3/changelog-v3.0.md`](../../logs/v3/changelog-v3.0.md) — V3-A + V3-B umbrella(6 特性 5 sub-sprint ship 链路)
- [`docs/logs/v3/changelog-v3.1.md`](../../logs/v3/changelog-v3.1.md) — V3-C umbrella(v3.1.0 段已写,v3.1.1 / v3.1.2 段待 append)
