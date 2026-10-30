# 编码约定

> JHYY 编译器自身的开发规范。
>
> **Last updated**: v2.4.0 (2026-09-04) — **v2.0 阶段 (v2.0.0 → v2.4.0) 5 版本全 ship** baseline (tags `v2.3.0` / `v2.4.0`)。二进制命名(`jhyy.exe` / `jhyy_v1.exe.exe` / `jhyy-setuc.exe`)仍为当前真值;**v2.0 阶段未砍 C 端** (per M5 deferral 2026-08-14 — 仍等 v2.x 末 QBE 自写 + v3.x 末 runtime 重写后,一次性删 `src/*.c` + untrack `qbe/` + 删 `runtime.c`,完成 "jhyy 编 jhyy" 0 C 依赖闭环; v1.5 installer ship 不触发 M5)。

## 项目结构

```
compiler/
  src/              *.c / *.h      C 端编译器实现（v0.x 主线）
  src0/             *.jhyy         jhyy 端编译器实现（v1.0 自举翻译产物；目标 = C 端弃用）
  runtime/                         JHYY 运行时（C 端链接）
  tests/examples/   *.jhyy         集成测试（regress.py 自动跑）
  build/bin/        regress.py     回归脚本 + jhyy.exe
mcp-jhyy/                          JHYY MCP 服务
docs/
  internal/         架构 / 构建 / 约定 / 测试
  abis/             语言规范 + ABI（locked）
  plans/
    roadmap/        vX.Y 轴长线路线图（v0.x / v1.0 / v2.x / v3.x）
    v0/             C 编译器 sprint 计划（v0.4 / v0.5 / v0.6 / v0.7 / v0.8）
    v1/             jhyy 自举 sprint 计划（v1.0.0）
  logs/
    v0/             C 编译器 changelog + 早期 sprint
    v1/             jhyy 自举时代 changelog + sprint
```

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
6. **C-side vs jhyy_v1 closure chain binary 操作规则**（Sprint v1.1.2 调查结论, 2026-08-12;v1.3.7 commit `0f32977` 切到 `.exe.exe` 单 canonical,删 `jhyy_v1.exe`）：
   - ✅ C-side (`jhyy.exe`) 可写 `compiler/build/bin/jhyy.exe` + 派生 `.il`(开发态)
   - ❌ C-side **绝不可写** `jhyy_v1.exe.exe` / `jhyy_v2.exe` / `jhyy_v3.exe` / `jhyy_v4.exe` — closure 链 5 个 canonical binary,被污染后 Stage 2 byte-equal 验证失效
   - ✅ 验证 closure 时用 `jhyy_v1.exe.exe`(`jhyy_v1` 唯一变体) / `jhyy_v2.exe` / `jhyy_v3.exe` / `jhyy_v4.exe` 编 `src0/main.jhyy`,永远不写回 canonical
   - **v1.3.7 transition**: `jhyy_v1.exe`(旧 canonical 别名, v1.0.0 时期)已从 git 删除(commit `0f32977`),canonical 统一到 `jhyy_v1.exe.exe`(MCP `jhyy_regress` baseline 走这个)。v2/v3/v4 无变体。
   - **为什么需要这条规则**: C-side (`bccc452e...`) 跟 jhyy_v1 (`2445e97d...` → `7c035615...`) emit 的 `.il` 历史就不同(`Sprint 4.21-4.25 W-005 #2 真修 chain` 在 C-side 加 `irval_is_undef` 守卫导致多 emit 几个 `copy`,QBE no-op 但 sha 不同)。Stage 2 N=3 closure **不覆盖 C-side**,所以 C-side binary 跑出来 sha 跟 jhyy_v1 不同是预期行为。

### 改动后必跑（按层面）

| 改的文件 | 必跑 | 备注 |
|----------|------|------|
| `compiler/src0/*.jhyy` (jhyy 编译器源) | (1) `python regress.py` (jhyy.exe 编 regress)<br>(2) `python regress.py --all --include-informational` (jhyy_v1 编 regress,持平 baseline)<br>(3) `make`（自举闭环:新 exe 编 src0 的产物必须与它自己编的逐字节相同）| **改了 src0 必须重跑 `make`** —— `compiler/build/bin/jhyy.exe` 是 git 跟踪的自举锚点,fresh clone 拿到的就是它;忘了重生成 = 提交了一份「源码与产物不同步」的仓 |
| `compiler/src0/jhyy_helpers.c` (C 桥) | 同上 + `bash compiler/tests/bootstrap/artifact_checks.sh --only=helpers_symbols` | C 桥少一个 `jh_*` 符号 ⇒ 编译照过、链接期才炸 ⇒ 有常驻门 |
| `compiler/tests/examples/*.jhyy` | `python regress.py` | 加新测试必跑 |
| `docs/abis/jhyy-lang-spec-*.md` / `docs/abis/jhyy-abi-*.md` | (1) 同步更新 v0.x / v1.x / v2.x 路线图引用<br>(2) `regress.py`（spec 改动可能影响 jhyy 端解析） | spec 改动 = 跨多 sprint 影响 |
| `docs/plans/v0/*` / `docs/plans/v1/*` / `docs/plans/v2/*` / `docs/plans/roadmap/*` | 至少 review 跨文件引用一致性 | doc-only 改动不强制 regress，但建议跑一次验证 jhyy 编译器仍编得出 hello.jhyy |
| `mcp-jhyy/*` | 重启 MCP server + 跑 `jhyy_run` tool 验证 hello.jhyy | — |

## 测试命名

- 集成测试：`compiler/tests/examples/<feature>.jhyy`
- ~~单元测试：`compiler/tests/unit/test_<feature>.c`~~ —— **v4.0.21 起已无 C 端单元测试**
  （M5 Part 1 删掉 `compiler/src/` 后它们编不出来、且要测的代码已不存在 ⇒ 一并删除）
- 回归脚本：`regress.py`（**仓库根目录**，自动跑所有 .jhyy）

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

### 短路语义（`&&` / `||`）

| 形状 | 右侧求值条件 |
|---|---|
| `A && B` | **A 为真时**才求值 B（A 假 ⇒ 结果假 ⇒ 跳过 B） |
| `A \|\| B` | **A 为假时**才求值 B（A 真 ⇒ 结果真 ⇒ 跳过 B） |

操作数**左到右**求值。

**嵌套是允许的** —— `A && (B || C)` / `(A || B) && C` / `A || (B && C)` 都正确短路。
v4.x 的 in-mem 后端在 `codegen.jhyy` 的短路实现里让**右侧只在 `sc_eval` 块求值**
（`&&` 走 `jnz left → sc_eval`，`||` 走 `jnz left → sc_true`），嵌套由递归自然覆盖。

⚠️ **「codegen 里禁嵌套短路」这条约束已退役**（**W-169**，2026-10-30）——
它是 **QBE IL 时代**的遗留（当时 nested phi predecessor 会 mismatch，故一律写成
nested plain `if`）。v4.x 换成 in-mem 后端后约束对象已不存在，且当年的静态检查脚本
**从未接进 CI**、当前也早已 FAIL（8 处「违规」全是正确代码）。

⇒ **门不是风格检查，是行为回归**：`compiler/tests/examples/logical_nested.jhyy`
（7 种嵌套形状 + 左到右顺序，用**调用计数器**区分「值对但副作用多执行」——
光看返回值抓不到短路失效）。

⚠️ 上面第 2 条「避免嵌套表达式」是**可读性**约定，仍然有效 ——
嵌套**可以写**（语义正确），但**不鼓励**（难读）。

## Workaround 登记（强制）

**所有 workaround 必须登记到 `docs/internal/workarounds.md` 才能写入代码。** 详见该文件 § 登记格式。

登记时机：
- **执行前**：在 doc 写明 workaround 是什么、触发面、怎么改、影响范围、失效条件
- **执行后**：回填实际改动的清单（rename 表 / 行号 / commit hash）

不豁免：哪怕是 1 行 inline comment 的 workaround 也得登记。已存在的 inline comment（如 `util.jhyy` hash_string 处的 `// 绕过 v0.6 codegen bug`）补登记到 doc。

superseded 的 workaround 标记 `RESOLVED` 不删除（留作审计）。
