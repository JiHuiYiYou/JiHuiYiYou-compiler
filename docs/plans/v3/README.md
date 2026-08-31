# v3.x 语言扩展 — 计划目录 (mirror v0/v1/v2)

**状态**: 待启动 (与 v2.x 并行轴)

## 范围

v3.x 是语言特性扩展轴,服务于 [jhyy_OS](../../../jhyy_OS/) 的 OS-required 语言特性:

| Sprint | 特性 | 用途 |
|--------|------|------|
| v3.0 (3a) | inline asm | OS kernel 写汇编片段 (e.g. cpuid, msr, lgdt) |
| v3.0 (3b) | `#[naked]` fn | 不生成 prologue/epilogue (boot / interrupt entry) |
| v3.0 (3c) | volatile load/store | 防止编译器 reorder (MMIO 设备寄存器) |
| v3.0 (3d) | `#[no_std]` / `#![no_std]` | 切掉 runtime / panic_handler, 写 freestanding kernel |
| v3.0 (3e) | `#[link_section]` | 自定义目标 section (e.g. `.text.boot`) |
| v3.0 (3f) | memory barrier | compiler fence (e.g. `fence_seq_cst`) |
| v3.1 (3g+3g.5+3g.7) | `&mut` + lifetime + Cap<T> 8 规则 + phantom 0 字节 | OS 模块间共享指针的 borrow check (per D11 决策) |

完整 OS 启动链路 (`M1 → M11`) 见 [`../v2/v2.0.0-os-prep.md`](../v2/v2.0.0-os-prep.md)。

## 决策锁 (per `project_v2_v3_parallel_axes`)

- v2.x ‖ v3.x 并行推进 (semver 推论 v2.99 < v3.0 但实际 OS M1 启动前两轴各自达成即可)
- 每 sprint 设计前必读 [`../v2/v2.0.0-os-prep.md`](../v2/v2.0.0-os-prep.md) § 1 OS 启动里程碑表 + § 6 关键决策点
- 跨边界冲突走 [`../../../jhyy_OS/docs/coordination.md`](../../../jhyy_OS/docs/coordination.md) § 7 规则

## 当前内容

(暂无 — 待 sprint 启动时由 user + Claude 联合设计)

## 命名约定

每 sprint 一份:
- `v3.X.0任务清单 + 概要设计.md` — L3 任务清单 + 概要设计
- `v3.X.0详细实现方案.md` — L4 详细实现

(跟 v0/v1/v2 镜像)