# CLAUDE.md — JHYY (机会翼游) 编译器项目

> 自研静态类型编程语言 + 自举编译器。Phase 1 = C 语言宿主编译器（当前）。
> v0.6.0 tagged。v1.0.0 目标 = 编译器编译自己。

## 速查

- **编译器源**：`compiler/src/*.c` `compiler/src/*.h`
- **运行时**：`compiler/runtime/`
- **自举翻译**：`compiler/jhyy-src/`（Stage 0：arena.jhyy）
- **集成测试**：`compiler/tests/examples/*.jhyy`
- **MCP 服务**：`mcp-jhyy/`
- **工具链**：GCC 15.2.0 MSYS2 ucrt64 + QBE `-t amd64_win`

### 一行构建
```bash
/c/msys64/ucrt64/bin/gcc.exe -std=c11 -Wall -Wextra compiler/src/*.c -o compiler/build/bin/jhyy.exe -I compiler/src
```

### 一行回归
```bash
python compiler/build/bin/regress.py    # 43/46 passed, 0 failed
```

详细构建/编译/排查：`docs/internal/build.md`。
手动编译/查看 IL/QBE 调用：`docs/internal/build.md` §手动验证流水线。

---

## 文档索引

### 项目内部（`docs/internal/`）
- [`build.md`](docs/internal/build.md) — 编译/运行/手动验证/QBE 坑
- [`architecture.md`](docs/internal/architecture.md) — 流水线 / 模块清单 / 设计细节 / ABI 决策 / QBE IL 速查
- [`conventions.md`](docs/internal/conventions.md) — 编码约定 / 文件命名 / 提交规则 / 测试命名
- [`status.md`](docs/internal/status.md) — 当前版本 / 已实现特性 / 已知限制 / 历史修复
- [`tests.md`](docs/internal/tests.md) — 集成测试清单 + 运行方法

### 语言规范 & ABI（`docs/abis/`）
- [`jhyy-lang-spec-v1.0.0.md`](docs/abis/jhyy-lang-spec-v1.0.0.md) — 语言规范（latest，锁定 v0.6）
- [`jhyy-abi-v1.0.0.md`](docs/abis/jhyy-abi-v1.0.0.md) — ABI 白皮书（locked：struct pass-by-value / 多文件 / FFI / break-continue / 切片 / 命名空间）

### 阶段规划（`docs/plans/phase-*.md`，L1 顶层）

| 文档 | 阶段 | 状态 |
|------|------|------|
| [`phase-0-skeleton.md`](docs/plans/phase-0-skeleton.md) | Phase 0 — 骨架 | 已完成 |
| [`phase-1-c-compiler.md`](docs/plans/phase-1-c-compiler.md) | **Phase 1 — C 宿主编译器（当前）** | 进行中（v0.6.0） |
| [`phase-2-self-hosting.md`](docs/plans/phase-2-self-hosting.md) | Phase 2 — 自举 | 未启动 |
| [`phase-3-expansion.md`](docs/plans/phase-3-expansion.md) | Phase 3 — 扩展期 | 未启动 |
| [`phase-总规划-v0.2.x-to-v1.0.0.md`](docs/plans/phase-总规划-v0.2.x-to-v1.0.0.md) | L2 战略路线 | v0.2 → v1.0 总览 |

### 计划（`docs/plans/`，Sprint L3/L4）
- 各 sprint：`v0.X.0任务清单 + 概要设计.md`（L3）/ `v0.X.0详细实现方案.md`（L4）

### Sprint 日志（`docs/logs/`）
- changelog：`changelog-v0.X.Y.md`
- 早期 sprint：`sprint-1*.md`

---

## 工作风格

- 改前先 `git status` 确认没有上次临时文件遗留
- C11 零警告（`gcc -std=c11 -Wall -Wextra`）
- 修改范围最小化：不顺手 refactor，不加"可能将来有用"的代码
- 改动后跑完整回归；`regress.py` 必须 0 failed
- Windows + MSYS2 bash。Unix 路径语法。
