# CLAUDE.md — JHYY (机会翼游) 编译器项目

自研静态类型编程语言 + 自举编译器。
当前: v0.8 wip / C 语言宿主编译器（v0.x 轴）
目标: v1.0.0 = jhyy 编译器编译自己（`.il` byte-equal 闭环）

## Reading order

按你打算做的事挑一个入口：

| 意图 | 先看 |
|------|------|
| 了解项目现在到哪、有什么限制 | [`status.md`](docs/internal/status.md) |
| 想看 v0.x（C 编译器）整体还有什么没完成 | [`v0.x-c-compiler-roadmap.md`](docs/plans/roadmap/v0.x-c-compiler-roadmap.md) |
| 起一个新 sprint | 下方"路线图 + Sprint"表的"当前 sprint"锚 → L3 任务清单 |
| 改编译器 / 排 bug | [`architecture.md`](docs/internal/architecture.md) 看模块边界 → [`build.md`](docs/internal/build.md) 看构建 + 调试坑 |
| 改语言规范 / ABI | [`jhyy-lang-spec-v1.0.0.md`](docs/abis/jhyy-lang-spec-v1.0.0.md) / [`jhyy-abi-v1.0.0.md`](docs/abis/jhyy-abi-v1.0.0.md) |
| **起 v2.0 / v3.0 / v3.1 / v3.2+ OS 相关 sprint** | [`docs/plans/v2/v2.0.0-os-prep.md`](docs/plans/v2/v2.0.0-os-prep.md) + [`../jhyy_OS/docs/coordination.md`](../jhyy_OS/docs/coordination.md) § 0 Critical Path → 下方"与 jhyy_OS 项目的对齐" |

## 项目布局

```
compiler/
  src/              *.c / *.h      C 端编译器实现（v0.x 主线）
  src0/             *.jhyy         jhyy 端编译器实现（v1.0 自举翻译产物；目标 = C 端弃用）
  runtime/                         JHYY 运行时（C 端链接）
  tests/examples/   *.jhyy         集成测试（regress.py 自动跑）
  build/bin/        regress.py     回归脚本 + jhyy.exe
mcp-jhyy/                          JHYY MCP 服务
docs/
  internal/         架构 / 构建 / 约定 / 状态 / 测试
  abis/             语言规范 + ABI（locked）
  plans/
    roadmap/        vX.Y 轴长线路线图（v0.x / v1.0 / v2.x / v3.x）
    v0/             C 编译器 sprint 计划（v0.4 / v0.5 / v0.6 / v0.7 / v0.8）
    v1/             jhyy 自举 sprint 计划（v1.0.0）
  logs/
    v0/             C 编译器 changelog + 早期 sprint
    v1/             jhyy 自举时代 changelog + sprint
```

## 一行构建 / 回归

```bash
/c/msys64/ucrt64/bin/gcc.exe -std=c11 -Wall -Wextra compiler/src/*.c -o compiler/build/bin/jhyy.exe -I compiler/src
python compiler/build/bin/regress.py
```

工具链: GCC 15.2.0 MSYS2 ucrt64 + QBE `-t amd64_win`（QBE 二进制在 `qbe/qbe.exe`，不是 PATH 里，靠 jhyy main.c 写绝对路径调用）。详细构建/调试见 `build.md`；测试方法见 `tests.md`。

## 权威文档（100% 权威）

| 文档 | 状态 | 用途 |
|------|------|------|
| [`jhyy-lang-spec-v1.0.0.md`](docs/abis/jhyy-lang-spec-v1.0.0.md) | 锁定（self-hosting 启动门槛） | 语言规范 + 附录 B 已知限制 + 附录 C v1.0.0 启动条件 |
| [`jhyy-abi-v1.0.0.md`](docs/abis/jhyy-abi-v1.0.0.md) | 锁定（v0.4/v0.5/v0.6 实现已追更） | 类型布局 + 调用约定 + § 11.1 阻塞自举问题清单 |

**所有 plan 文件以这两个为 100% 权威对齐**。其他 v*.* 计划文件措辞可能滞后或不准，遇到冲突以 lang-spec / abi 为准。

## 版本轴（单一 vX.Y 编号）

项目**只用版本号轴**，不再用 phase-X 两维编号。版本轴语义：

| 轴 | 范围 | 目标 |
|---|---|---|
| **v0.x** | C 编译器自身（C 端） | 编译器自举门槛达成（v0.6+）|
| **v1.x** | jhyy 自举（`compiler/src0/*.jhyy`） | 真自举闭环（v1.0 = byte-equal `.il`）|
| **v2.x** | QBE 完整重写 + 多目标 / 自研 OS 准备 | amd64_sysv / 多目标 / freestanding（OS 准备清单 → [`docs/plans/v2/v2.0.0-os-prep.md`](docs/plans/v2/v2.0.0-os-prep.md)）|
| **v3.x** | 语言特性扩展（OS-required：inline asm / volatile / naked / no_std / `&mut` + lifetime）| 服务于 jhyy_OS |

**轴之间的关系**（关键，避免误读 semver）：
- **v0.x → v1.x**：严格顺序（v1.0 强前置 v0.x 全部完成）
- **v1.x → v2.x / v3.x**：严格顺序（v2.0 / v3.0 sprint 3a 强前置 v1.0 真自举闭环）
- **v2.x || v3.x**：**并行轴**（semver 会推论 "v2.99 < v3.0"，但项目实际是 v2.0 跟 v3.0 sprint 3a-3f 同时推进，OS M1 启动前两轴各自达成即可）。详情见 [`docs/plans/v2/v2.0.0-os-prep.md`](../JiHuiYiYou/docs/plans/v2/v2.0.0-os-prep.md) § 1 OS 启动里程碑表 + § 6 关键决策点。

历史 phase-X 措辞在新 sprint 文档里不再使用；如在旧 sprint / changelog / spec 里看到 phase-N 编号，按下表对应：phase-1 ≈ v0.x / phase-2 ≈ v1.x / phase-2.5 ≈ v2.x / phase-3 ≈ v3.x。

## 与 jhyy_OS 项目的对齐（mirror stub,2026-08-05 加）

> **本节给编译器侧 sprint 设计者** — 启动 session 打算做 v2.0 / v3.0 / v3.1 / v3.2+ sprint 之前,**必读**本节指向的三份 OS 侧 doc。

| 文档 | 用途 | 何时读 |
|------|------|--------|
| [`../jhyy_OS/docs/coordination.md` § 0 Critical Path](../jhyy_OS/docs/coordination.md) | OS × compiler 跨项目时间线权威视图(节点表 + 链式图)| **每个 sprint 启动前必读** |
| [`docs/plans/v2/v2.0.0-os-prep.md`](docs/plans/v2/v2.0.0-os-prep.md) | OS 启动链路编译器侧**唯一权威**(M1-M11 硬前置 + v2.0/v3.0/v3.1 节点)| 任何 OS 相关 sprint 设计必读 |
| [`../jhyy_OS/docs/v0.0.2-foundation-revision.md § 4`](../jhyy_OS/docs/v0.0.2-foundation-revision.md) | OS 端镜像(冲突时以 v2.0.0-os-prep 为准)| 跨边界决策 review |

**冲突解决规则**(从 OS 侧 coordination.md § 7 镜像):
- 任何 OS 镜像跟 `v2.0.0-os-prep § 1/2` 冲突 → **以 compiler 为准** → OS 侧撤回 + 提交 Q-OS-XXX
- 任何 compiler doc 跟 OS 镜像冲突 → OS doc 为准(本地权威)→ compiler 提交 Q-Compiler-XXX
- 跨边界僵持 → 走 user 介入

**当前跨边界问题状态**(2026-08-05 校准):
- ✅ **12 个 Q + 6 个 UD 决定 全部 2026-08-05 闭环/锁**(per coordination.md § 6 + § 8)
- Q-OS-001/002/003/004/005/006/007/008/009(9 条 OS → Compiler)— 全 ✅
- Q-Compiler-001/002/003/004/005/006(6 条 Compiler → OS)— 全 ✅
- D24-D29 6 个 UD 决定(per architecture-refactor § 15)— 全 ✅ 锁
- 详见 [`../jhyy_OS/docs/coordination.md § 2 + § 3 + § 6`](../jhyy_OS/docs/coordination.md)

**11 条跨边界决策**(2026-08-05 锁,详见 `coordination.md § 3`):
- D1 boot 路径 UEFI+PE/COFF / D2 region types primary / D3 M11 依赖图 / D4 缺 feature=设计输入
- D5 spec baseline 锁 / D6 Cap<T> 8 字节 / D7 v2.0 milestone 落盘
- D8 v2.0 = M1 target 硬前置 / D9 3g/3g.5/3g.7 在 M3-M4 / D10 `#[no_std]` 软 / D11 `&mut` 矩阵

## 文档索引

### 路线图 + Sprint

| 层级 | 文档 | 状态 |
|------|------|------|
| L1 | [`v0.x-c-compiler-roadmap.md`](docs/plans/roadmap/v0.x-c-compiler-roadmap.md) | **进行中**（C 编译器演进到自举门槛）|
| L1 | [`v1.0-self-hosting.md`](docs/plans/roadmap/v1.0-self-hosting.md) | 未启动（语言特性启动门槛已达成，见 lang-spec 附录 C）|
| L1.5 | [`v2.x-qbe-rewrite.md`](docs/plans/roadmap/v2.x-qbe-rewrite.md) | 未启动（中期方向，待 v1.0 后启动）|
| L1 | [`v3.x-language-expansion.md`](docs/plans/roadmap/v3.x-language-expansion.md) | 未启动（语言特性扩展；自举能力已在 v1.0 完成）|
| L1.5 | [`v2-v3-parallel-sprint-plan.md`](docs/plans/roadmap/v2-v3-parallel-sprint-plan.md) | **v2.x ⟂ v3.x 并行 sprint 调度**（M1-M4-M11 路径 + 风险触点 + 时间线）|
| L1 | [`v0.0-skeleton.md`](docs/plans/roadmap/v0.0-skeleton.md) | 已完成（早期骨架）|
| L3 | `docs/plans/v0/v0.X.0任务清单 + 概要设计.md` | 每个 C 编译器 sprint 一份 |
| L4 | `docs/plans/v0/v0.X.0详细实现方案.md` | 每个 C 编译器 sprint 一份 |
| L3 | `docs/plans/v1/v1.0.0任务清单 + 概要设计.md` | jhyy 自举 sprint（v1.0 = .il byte-equal 闭环）|
| L4 | `docs/plans/v1/v1.0.0详细实现方案.md` | 同上 |

最近完成的 sprint: **v0.6.0**（v0.6.2 / v0.6.3 已发，patch）→ `docs/plans/v0/v0.6.0任务清单 + 概要设计.md` / `docs/plans/v0/v0.6.0详细实现方案.md` / `docs/logs/v0/changelog-v0.6.3.md`
当前 sprint: **v0.8 wip**（自举路径清理 — bug 11-22 已修，regress 持平 **12 OK / 47 总**(持平 baseline,per commit 12 / changelog-v0.8.0);目标 = jhyy_v1 编所有 .jhyy 跑通）→ `docs/plans/v0/v0.8.0任务清单 + 概要设计.md` / `docs/logs/v0/changelog-v0.8.0.md`
下一阶段: **v1.0.0** 自举启动（粗粒度 5 sprint）→ `docs/plans/v1/v1.0.0任务清单 + 概要设计.md` / `docs/plans/v1/v1.0.0详细实现方案.md`
历史: changelog 见 `docs/logs/v0/changelog-v0.X.Y.md`；早期 sprint（命名 `sprint-1*.md`）同目录。

### 项目内部（`docs/internal/`）

- [`build.md`](docs/internal/build.md) — 编译 / 运行 / **QBE 后端坑（Windows 独有）**
- [`architecture.md`](docs/internal/architecture.md) — 流水线 / 模块 / 设计细节 / **QBE IL 速查** / Stage 0 自举
- [`conventions.md`](docs/internal/conventions.md) — 编码约定 / 文件命名 / 提交规则
- [`status.md`](docs/internal/status.md) — 当前版本 / 已实现特性 / 已知限制 / 历史修复
- [`tests.md`](docs/internal/tests.md) — 集成测试清单 + 运行方法

### 语言规范 & ABI（`docs/abis/`，locked）

- [`jhyy-lang-spec-v1.0.0.md`](docs/abis/jhyy-lang-spec-v1.0.0.md) — 语言规范（v0.6 锁定）
- [`jhyy-abi-v1.0.0.md`](docs/abis/jhyy-abi-v1.0.0.md) — ABI 白皮书（struct pass-by-value / 多文件 / FFI / break-continue / 切片 / 命名空间）

## 工作风格

只列 JHYY-specific 项；通用约定见根 `CLAUDE.md` § 跨项目工作风格。

- **工具链**：Windows + MSYS2 bash，Unix 路径语法（`/c/...` 而非 `C:\...`）
- **QBE IL 写盘**：必须 `fopen("wb")`，否则 Windows MSVCRT 把 `\n` 转 `\r\n` 污染 IL。详见 `build.md` § QBE 后端坑
- **改动后必跑**：`python compiler/build/bin/regress.py`，0 failed 才算完成
