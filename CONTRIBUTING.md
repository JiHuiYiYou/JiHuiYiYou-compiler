# 贡献者指南

> JHYY 编译器项目的贡献者门槛 — 提交规则、PR 流程、AI agent 协作约定。
>
> **详细约定**:`docs/internal/conventions.md` (编码规范) + [`docs/internal/build.md`](docs/internal/build.md) (构建) + [`docs/internal/workarounds.md`](docs/internal/workarounds.md) (W-NNN workaround 登记)。
>
> **适用范围**:v2.x (QBE 重写) / v3.x (语言扩展) 并行 sprint 阶段。v1.x 已 ship + frozen。

## 入门

1. **读 [`README.md`](README.md) § What is JHYY + § Quick Start + § Status** — 项目是什么、怎么跑、当前在哪
2. **读 [`docs/plans/roadmap/v2-v3-parallel-sprint-plan.md`](docs/plans/roadmap/v2-v3-parallel-sprint-plan.md)** — 跨轴时间线 + OS 启动链路
3. **读 [`docs/plans/v2/v2.0.0-os-prep.md`](docs/plans/v2/v2.0.0-os-prep.md) § 1 + § 6** — OS 启动里程碑 + 关键决策点 (sprint 启动前必读)
4. **挑 sprint**:`docs/plans/v2/` / `docs/plans/v3/` L3 任务清单 → L4 详细方案 → 跟 user 启动

## 提交流程

### 1. 改前

- **从 main 拉新分支**:`git checkout main && git pull && git checkout -b feat/<short-name>` 或 `fix/<short-name>`
- **改动前 `git status` 看是否有 stale 文件** — 避免误提交上次的临时产物
- **新加 workaround 必须登记** — 见下文"Workaround 登记"
- **改 doc 前先 fact-check** — 限制是否仍存在 / 是否已 ship / 是否措辞过时(避免 doc-only 改动跟代码分离)

### 2. 改中

- **C 代码**:`-Wall -Wextra` 零警告,`gcc -std=c11`,路径用 `/`,统一 arena
- **JHYY 代码**(`compiler/src0/*.jhyy`):不可变优先(`let` 而非 `let mut`),避免嵌套表达式,`*T` 不用 `**T`
- **最小化改动范围**:不顺手 refactor,不加"将来可能有用"的代码
- **不改 ai 内部指令**:`CLAUDE.md` + `~/.claude/projects/.../memory/` 是给 AI agent 的本地指令,不属公共贡献范畴

### 3. 改后必跑

| 改的文件 | 必跑 |
|----------|------|
| `compiler/src/*.c` | `python compiler/build/bin/regress.py` (0 failed) |
| `compiler/src0/*.jhyy` | (1) `python compiler/build/bin/regress.py` (2) `python compiler/build/bin/regress.py --all --include-informational` |
| `compiler/tests/examples/*.jhyy` | `python compiler/build/bin/regress.py` |
| `docs/abis/*` | `python compiler/build/bin/regress.py` + 同步 v0.x / v1.x / v2.x 路线图引用 |
| `mcp-jhyy/*` | 重启 MCP server + `jhyy_run` tool 验证 hello.jhyy |

**5/5 PASS 是声称 fix 有效的硬门槛**(per `feedback_fix_evaluation_rule`)。非确定性 baseline 比 5/5 更严。

### 4. Commit message

格式(per [`docs/internal/conventions.md`](docs/internal/conventions.md) § 提交规则):

```
<type>(<scope>): <subject>

<body>

<footer>
```

- **type**:`feat` / `fix` / `refactor` / `chore` / `docs` / `test` / `perf`
- **scope**:改动区域,如 `compiler/codegen` / `installer` / `docs/plans/v3`
- **subject**:中文概述,≤ 50 字,无句号
- **body**:动机 + 关键决策点 + 跨文件影响(非琐碎改动必填)
- **footer**: `Co-Authored-By: MiniMax-M3 <noreply@MiniMax>` — 标记 AI 协作(per `feedback_commit_coauthor`)

**作者邮箱**:项目 owner 用 `JHYY <15901598712@163.com>` 才能上主页绿格子(per `feedback_git_identity_canonical`)。其他贡献者用自己的 git config。

### 5. 单 audit 范围

reviewer 看 commit 改动**只用**:

```bash
git show <sha>
git diff <sha>~1 <sha>
```

**不要**用累计跨 commit diff (`git diff <base>..<head>`) — 否则误把几小时前的 commit 改动归到当前 commit 头(per `feedback_audit_single_commit_diff`,2026-08-12 v1.3.1 audit 教训)。

### 6. PR

- **标题** = commit subject
- **描述** = commit body + 验证清单(改了哪些文件 → 跑了哪些测试 → 结果)
- **关联 issue / sprint 编号**(如有)
- **sprint 设计类 PR**:附 L3 任务清单 + L4 详细方案的更新 diff

## Workaround 登记(强制)

**所有 workaround 必须先在 [`docs/internal/workarounds.md`](docs/internal/workarounds.md) 登记,再写入代码**(per `feedback_document_workarounds_in_docs`)。登记内容:

1. **W-NNN 编号** + 一句话标题
2. **触发面**:哪个文件 / 哪个场景 / 哪种输入
3. **当前实现**:怎么改的,代码引用(file:line)
4. **影响范围**:波及哪些下游
5. **失效条件**:什么情况下这条 workaround 不再需要
6. **supersede 路径**:未来应该改成什么

不豁免:哪怕是 1 行 inline comment 的 workaround 也得登记。superseded 标 `RESOLVED` 不删除(留作审计)。

## Sprint 设计规则

- **计划中不写日期估时**(per `feedback_no_date_estimates`) — 用 sprint 序列 + 相对顺序,不写"几月几月完成"
- **跨项目边界**(跟 `../jhyy_OS/`)走 [`coordination.md`](../jhyy_OS/docs/coordination.md) § 7 冲突解决规则
- **sprint 设计前必读**:`docs/plans/v2/v2.0.0-os-prep.md` § 1 + § 6(OS 启动里程碑 + 关键决策点)
- **changelog 遵循 umbrella 约定**:vX.Y 轴只 1 个 umbrella changelog,不创建 `changelog-vX.Y.Z.md` 之类 standalone(per `feedback_changelog_umbrella`)

## AI 协作

本仓库用 Claude Code 作为开发协作 AI。改动 AI 代写的 commit 一律加 `Co-Authored-By: MiniMax-M3 <noreply@MiniMax>` 标记。

**AI agent 工作流**:

1. **session 启动前**:读取 `CLAUDE.md` (项目级 AI 指令) + `~/.claude/projects/.../memory/` (用户偏好)
2. **改动前**:查 `docs/internal/workarounds.md` 是否已有相关 W-NNN(避免重复登记)
3. **改动后**:跑 `regress.py` 验证(spec 改动必跑,代码改动必跑,doc-only 改动建议跑)
4. **commit 时**:遵循 § 4 格式,加 Co-author footer

**用户审查点**:AI 提议的 fix / refactor / 文档改动,user 审过才落地。`git push` / `git tag` / 多 agent race 时 user 显式确认。

## 详细参考

- **编码规范**:`docs/internal/conventions.md`
- **构建 / 调试**:`docs/internal/build.md`
- **架构**:`docs/internal/architecture.md`
- **测试**:`docs/internal/tests.md`
- **Workaround 索引**:`docs/internal/workarounds.md`
- **语言规范(锁定)**:`docs/abis/jhyy-lang-spec-v1.3.0.md`
- **ABI(锁定)**:`docs/abis/jhyy-abi-v1.0.0.md`
- **路线图**:`docs/plans/roadmap/`
- **Sprint 设计**:`docs/plans/v0/` / `docs/plans/v1/` / `docs/plans/v2/` / `docs/plans/v3/`
- **Changelog**:`docs/CHANGELOG.md` (索引) + `docs/logs/v{0,1}/changelog-vX.Y.{0,md}`