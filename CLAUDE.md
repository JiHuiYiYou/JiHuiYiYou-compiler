# CLAUDE.md — JHYY (机会翼游) 编译器项目

自研静态类型编程语言 + 自举编译器。
当前: Phase 1 / v0.6.0 / C 语言宿主编译器
目标: v1.0.0 = 编译器编译自己（Phase 2）

## Reading order

按你打算做的事挑一个入口：

| 意图 | 先看 |
|------|------|
| 了解项目现在到哪、有什么限制 | [`status.md`](docs/internal/status.md) |
| 想看 Phase 1 整体还有什么没完成 | [`phase-1-c-compiler.md`](docs/plans/phase/phase-1-c-compiler.md) |
| 起一个新 sprint | 下方"阶段 + Sprint"表的"当前 sprint"锚 → L3 任务清单 |
| 改编译器 / 排 bug | [`architecture.md`](docs/internal/architecture.md) 看模块边界 → [`build.md`](docs/internal/build.md) 看构建 + 调试坑 |
| 改语言规范 / ABI | [`jhyy-lang-spec-v1.0.0.md`](docs/abis/jhyy-lang-spec-v1.0.0.md) / [`jhyy-abi-v1.0.0.md`](docs/abis/jhyy-abi-v1.0.0.md) |

## 项目布局

```
compiler/
  src/              *.c / *.h      编译器实现
  runtime/                         JHYY 运行时
  jhyy-src/                        自举翻译（当前 Stage 0 = arena.jhyy，见 architecture.md § Stage 0 自举试点）
  tests/examples/   *.jhyy         集成测试
  build/bin/        regress.py     回归脚本 + jhyy.exe
mcp-jhyy/                          JHYY MCP 服务
docs/
  internal/         架构 / 构建 / 约定 / 状态 / 测试
  abis/             语言规范 + ABI（locked）
  plans/
    phase/          长期 phase-N 顶层路线图
    v0/             C 编译器 sprint 计划
    v1/             jhyy 自举 sprint 计划
  logs/             changelog + 早期 sprint 记录
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
| [`jhyy-lang-spec-v1.0.0.md`](docs/abis/jhyy-lang-spec-v1.0.0.md) | 锁定（self-hosting 启动门槛） | 语言规范 + 附录 B 已知限制 + 附录 C phase-2 启动条件 |
| [`jhyy-abi-v1.0.0.md`](docs/abis/jhyy-abi-v1.0.0.md) | 锁定（v0.4/v0.5/v0.6 实现已追更） | 类型布局 + 调用约定 + § 11.1 阻塞自举问题清单 |

**所有 plan 文件以这两个为 100% 权威对齐**。其他 phase-* / v*.* 计划文件措辞可能滞后或不准，遇到冲突以 lang-spec / abi 为准。

## 文档索引

### 阶段 + Sprint

| 层级 | 文档 | 状态 |
|------|------|------|
| L1 | [`phase-0-skeleton.md`](docs/plans/phase/phase-0-skeleton.md) | 已完成 |
| L1 | [`phase-1-c-compiler.md`](docs/plans/phase/phase-1-c-compiler.md) | **进行中** |
| L1 | [`phase-2-self-hosting.md`](docs/plans/phase/phase-2-self-hosting.md) | 未启动（语言特性启动门槛已达成，见 lang-spec 附录 C） |
| L1.5 | [`phase-2.5-qbe-rewrite.md`](docs/plans/phase/phase-2.5-qbe-rewrite.md) | 未启动（中期方向，待 phase-2 后启动） |
| L1 | [`phase-3-expansion.md`](docs/plans/phase/phase-3-expansion.md) | 未启动（语言特性扩展；自举能力已在 phase-2 完成） |
| L3 | `docs/plans/v0/v0.X.0任务清单 + 概要设计.md` | 每个 C 编译器 sprint 一份 |
| L4 | `docs/plans/v0/v0.X.0详细实现方案.md` | 每个 C 编译器 sprint 一份 |
| L3 | `docs/plans/v1/v1.0.0任务清单 + 概要设计.md` | jhyy 自举 sprint（v1.0.0 phase-2） |
| L4 | `docs/plans/v1/v1.0.0详细实现方案.md` | 同上 |

最近完成的 sprint: **v0.6.0**（v0.6.2 / v0.6.3 已发，patch）→ `docs/plans/v0/v0.6.0任务清单 + 概要设计.md` / `docs/plans/v0/v0.6.0详细实现方案.md` / `docs/logs/v0/changelog-v0.6.3.md`
当前 sprint: **v1.0.0** phase-2 自举启动（粗粒度 5 sprint）→ `docs/plans/v1/v1.0.0任务清单 + 概要设计.md` / `docs/plans/v1/v1.0.0详细实现方案.md`
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
