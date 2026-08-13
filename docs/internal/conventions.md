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
| 长期 vX.Y 路线图 | `docs/plans/roadmap/vX.X-*.md` |

## 提交规则

1. **禁止提交构建产物**：`.exe`、`.il`、`.s`、`.o`（已在 `.gitignore`）
2. **禁止提交临时调试文件**：`test_*.c`、`test_*.jhyy`、`out.txt` 等（用 `tmp/` 目录）
3. **改动前先看 git status**：避免误提交上次的临时文件
4. **每个 sprint 一个 commit**：commit message 用中文概述 + Co-Authored-By: MiniMax-M3 <noreply@MiniMax>
5. **版本号用 git tag**：`git tag v0.X.Y`
6. **C-side vs jhyy_v1 closure chain binary 操作规则**（Sprint v1.1.2 调查结论, 2026-08-12）：
   - ✅ C-side (`jhyy.exe`) 可写 `compiler/build/bin/jhyy.exe` + 派生 `.il`(开发态)
   - ❌ C-side **绝不可写** `jhyy_v1.exe` / `jhyy_v2.exe` / `jhyy_v3.exe` / `jhyy_v4.exe` — 这些是 closure 链 canonical binary,被污染后 Stage 2 byte-equal 验证失效
   - ✅ C-side 写 `jhyy_v1.exe.exe` OK(每次 Stage 0 jhyy_v1 重建会被 MCP `jhyy_regress` baseline 校验保护)
   - ✅ 验证 closure 时用 `jhyy_vN.exe.exe` 编 `src0/main.jhyy`,永远不写回 `jhyy_v*.exe`
   - **为什么需要这条规则**: C-side (`bccc452e...`) 跟 jhyy_v1 (`2445e97d...` → `7c035615...`) emit 的 `.il` 历史就不同(`Sprint 4.21-4.25 W-005 #2 真修 chain` 在 C-side 加 `irval_is_undef` 守卫导致多 emit 几个 `copy`,QBE no-op 但 sha 不同)。Stage 2 N=3 closure **不覆盖 C-side**,所以 C-side binary 跑出来 sha 跟 jhyy_v1 不同是预期行为。

### 改动后必跑（按层面）

| 改的文件 | 必跑 | 备注 |
|----------|------|------|
| `compiler/src/*.c` (C 编译器源) | `python compiler/build/bin/regress.py` | 0 failed 才算完成 |
| `compiler/src0/*.jhyy` (jhyy 编译器源) | (1) `python compiler/build/bin/regress.py` (jhyy_0 编 regress)<br>(2) `python compiler/build/bin/regress_v1.py` (jhyy_v1 编 regress，持平 baseline) | v0.9 wip commit 2.83 + v1.0.0 阶段必跑 |
| `compiler/tests/examples/*.jhyy` | `python compiler/build/bin/regress.py` | 加新测试必跑 |
| `docs/abis/jhyy-lang-spec-*.md` / `docs/abis/jhyy-abi-*.md` | (1) 同步更新 v0.x / v1.x / v2.x 路线图引用<br>(2) `regress.py`（spec 改动可能影响 jhyy 端解析） | spec 改动 = 跨多 sprint 影响 |
| `docs/plans/v0/*` / `docs/plans/v1/*` / `docs/plans/v2/*` / `docs/plans/roadmap/*` | 至少 review 跨文件引用一致性 | doc-only 改动不强制 regress，但建议跑一次验证 jhyy 编译器仍编得出 hello.jhyy |
| `mcp-jhyy/*` | 重启 MCP server + 跑 `jhyy_run` tool 验证 hello.jhyy | — |

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

## Workaround 登记（强制）

**所有 workaround 必须登记到 `docs/internal/workarounds.md` 才能写入代码。** 详见该文件 § 登记格式。

登记时机：
- **执行前**：在 doc 写明 workaround 是什么、触发面、怎么改、影响范围、失效条件
- **执行后**：回填实际改动的清单（rename 表 / 行号 / commit hash）

不豁免：哪怕是 1 行 inline comment 的 workaround 也得登记。已存在的 inline comment（如 `util.jhyy` hash_string 处的 `// 绕过 v0.6 codegen bug`）补登记到 doc。

superseded 的 workaround 标记 `RESOLVED` 不删除（留作审计）。
