# 编码约定

> JHYY 编译器自身的开发规范。

## C 代码

1. **C11 标准**：`gcc -std=c11 -Wall -Wextra`，**零警告**
2. **路径用 `/`**：不用 `\`（即使在 Windows 上）
3. **Arena 分配**：编译器内部统一用 arena，不直接 `malloc`（除非 arena 自己需要 grow）
4. **修改范围最小化**：不顺手 refactor，不加"将来可能有用"的代码
5. **改动后跑完整回归**：`python compiler/build/bin/regress.py` 必须 0 failed

## 文件命名

| 类型 | 命名 |
|------|------|
| C 源文件 | `snake_case.c/h` |
| JHYY 源文件 | `snake_case.jhyy` |
| 文档 | `kebab-case.md` |
| Sprint 日志 | `docs/logs/v0/changelog-v0.X.Y.md` |
| C 编译器 sprint 设计 | `docs/plans/v0/v0.X.Y详细实现方案.md` |
| C 编译器 sprint 概要 | `docs/plans/v0/v0.X.Y任务清单 + 概要设计.md` |
| jhyy 自举 sprint 设计 | `docs/plans/v1/vX.Y.Z详细实现方案.md` |
| jhyy 自举 sprint 概要 | `docs/plans/v1/vX.Y.Z任务清单 + 概要设计.md` |
| 长期 phase 路线图 | `docs/plans/phase/phase-N-*.md` |

## 提交规则

1. **禁止提交构建产物**：`.exe`、`.il`、`.s`、`.o`（已在 `.gitignore`）
2. **禁止提交临时调试文件**：`test_*.c`、`test_*.jhyy`、`out.txt` 等
3. **改动前先看 git status**：避免误提交上次的临时文件
4. **每个 sprint 一个 commit**：commit message 用中文概述 + Co-Authored-By
5. **版本号用 git tag**：`git tag v0.X.Y`

## 测试命名

- 集成测试：`compiler/tests/examples/<feature>.jhyy`
- 单元测试：`compiler/tests/unit/test_<feature>.c`
- 回归脚本：`compiler/build/bin/regress.py`（自动跑所有 .jhyy）

## gitignore 例外

默认 `compiler/tests/examples/` 只跟踪 `.jhyy`。新加子目录时需要在 `.gitignore` 加例外：

```
!compiler/tests/examples/<subdir>/
!compiler/tests/examples/<subdir>/*.jhyy
```

## JHYY 代码（自举后）

1. **路径用 `/`**
2. **避免嵌套表达式**：复杂表达式拆 `let mut x = ...`
3. **不可变优先**：默认 `let`，需要时再 `let mut`
4. **指针用 `*T` 不用 `**T`**（自举后建议）
