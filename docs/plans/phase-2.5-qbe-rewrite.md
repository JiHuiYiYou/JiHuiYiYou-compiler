# Phase 2.5: QBE 自写 + 全栈 jhyy 化 + N 代 fixed point

> **状态**：未启动（中期方向，待 phase-2 v1.0 完成后启动）
> **目标**：整个编译器（含 QBE 后端）全部 jhyy 化；能用 jhyy 编 jhyy；编译 N 代后结果分毫不差
> **前置**：phase-2 自举完成（v1.0 真自举闭环）
> **完成时间估计**：未定（v3.x+ 之后；不锁死）

---

## 为什么单独立 phase 文件

phase-2-self-hosting.md（前端翻译，v1.0）和 phase-3-expansion.md（语言特性扩展）**都不覆盖 QBE 后端重写**：

- phase-2 = 前端 jhyy 化（lexer/parser/sema/codegen emit IL），.il 仍交给 C 版 QBE 工具
- phase-3 = 语言扩展（浮点/泛型/闭包/标准库/优化/包管理），**不涉及后端汇编器**

但 user 2026-06-22 明确：**中期目标 = 整个编译器（含 QBE）全部 jhyy 化**。这条不在任何现有 phase 文件里，需要单独的 phase-2.5 占位。

跟原计划的关系：2026-06-22 决策"v3.x+ QBE 完整重写"被延后但**未给独立 phase**。phase-2.5 = 那个被延后的、缺独立 phase 文件的中期目标的具体化。

---

## 自举定义（强自举，N 代 fixed point）

```
C 版 jhyy      编译 src0/*.jhyy → jhyy_0
jhyy_0         编译 src0/*.jhyy → jhyy_1
jhyy_1         编译 src0/*.jhyy → jhyy_2
jhyy_2         编译 src0/*.jhyy → jhyy_3
...
jhyy_N == jhyy_{N+1}  (编译器自身 fixed point)
```

### 验证对象

| 层 | 验证 | 工具 |
|---|---|---|
| QBE .il | jhyy_N 和 jhyy_{N+1} 编 fib.jhyy 产 .il byte-equal | `diff` 空 |
| 汇编 .s | jhyy_N 和 jhyy_{N+1} 编 fib.jhyy 产 .s byte-equal | `diff` 空 |
| 行为 .exe | regress.py 全过（gcc timestamp 不可控，**不验证字节**） | regress.py |
| 性能 .exe | fib / ackermann / nqueens 等 benchmark 跑时间 ≤ 1.1x C 版 QBE 生成代码 | benchmark |

### 不验证

- 编译 wall time（自举编译慢可接受）
- .exe 字节 byte-equal（gcc ld 嵌 timestamp）

### "N 代" 的最低门槛

**jhyy_2 == jhyy_3**（编译器自身 fixed point，3 代内收敛）。**N ≥ 3** 是 phase-2.5 完成门槛。

> **N → ∞ 仍 fixed point** 是更强性质，目前**不要求**；是否纳入完成定义由 user 后续决定。

---

## 范围边界

### 在 phase-2.5 内

- 自写 QBE 后端（IL → .s 汇编）—— 整个 IL → .s 链 jhyy 化
- 整个编译栈（前端 + 后端 + main + 标准库）jhyy 化，**无外部 QBE 依赖**
- N 代自举 fixed point 验证
- 运行时性能不退化（≤ 1.1x C 版 QBE 生成代码）

### 不在 phase-2.5 内（明确延后）

- **不重写 QBE IL 文本层**：仍用 QBE IL 作为中间表示（jhyy 写 IL 文本 emit；不写 IL parser）
- **不写新 ABI / 多目标**：amd64_win 中间态不变
- **不重写 gcc / ld**：保留外部工具链（除非 user 后续要求自写 linker / 汇编器）
- **不做 phase-3 语言特性**：浮点/泛型/闭包等跟 phase-2.5 并行 / 之后

---

## 关键技术挑战

### 挑战 1：byte-equal .s + 速度不退化的矛盾

传统编译器优化（peephole / 指令调度 / 寄存器分配启发式）会破坏 byte-equal：
- 不同 run 调度顺序不同 → .s 不一致
- 哈希表迭代顺序不稳定 → 寄存器编号不同

**应对**：
- **Deterministic optimization**：所有优化 pass 必须保输出稳定（输入不变 → 输出不变）
- 排序：所有数据结构用排序遍历（symtab 按名字 sorted）
- 寄存器分配：固定顺序启发式（如 local-first → global）而非贪心
- peephole：rule 应用按模式排序
- **LLVM 有等价做法（带 -g0 模式 + stable hash），可参考**

### 挑战 2：x86_64 指令集覆盖

C 版 QBE 生成的 .s 用到多少 x86_64 指令？需要先 inventory：
- 整数算术（add/sub/mul/div/neg）
- 内存（mov/lea/push/pop）
- 控制流（jmp/jcc/call/ret）
- 系统调用（syscall）
- struct pass-by-value sret 处理（v0.4 ABI 锁定）
- 浮点（**phase-2.5 不做**，等 phase-3a）

L3 任务清单启动后第一步：grep `codegen.c` 列出 emit 的所有 QBE IL 指令类型，反推 .s 指令集范围。

### 挑战 3：自举栈全栈验证

phase-2 L1 计划只验证 `.il byte-equal`（单层）。phase-2.5 验证 `.il + .s` 双层 + 运行时性能：
- 验证脚本要重写：stage1.sh 加 .s diff 步骤 → 改名 stage2.sh
- benchmark 脚本：新写 `compiler/tests/bootstrap/bench.sh`，对比 jhyy_0 / jhyy_1 / C 版 QBE 三个编译器产 .exe 的运行时间

---

## 跟 phase-2 / phase-3 的关系

```
phase-2 (v1.0 前端翻译) ─┐
                        ├─ phase-2.5 (QBE 自写 + 全栈自举 + N 代 fixed point)
phase-3 (语言扩展) ─────┘
```

**执行顺序**（user 2026-06-22 未明示，**建议**串行）：
1. **先 phase-2**（v1.0）：前端 jhyy 化，但 .il 仍交给 C 版 QBE 工具
2. **后 phase-2.5**（v3.x+）：QBE 后端 IL → .s jhyy 化，移除 C 版 QBE 依赖
3. phase-3（语言扩展）跟 phase-2.5 关系待定（user 未说并行还是串行）

---

## 关键文件清单（待 phase-2.5 L3 任务清单细化）

### 新建
- `compiler/src0/qbe/`（待 phase-2 完成后从 C 版 QBE 翻译 / 自写）
  - `il_emit.jhyy`（IL 文本 emit，phase-2 已部分覆盖）
  - `amd64_codegen.jhyy`（IL → amd64 汇编）
  - `regalloc.jhyy`（确定性寄存器分配）
  - `peephole.jhyy`（确定性 peephole 优化）
- `compiler/tests/bootstrap/stage2.sh`（N 代 fixed point 验证）
- `compiler/tests/bootstrap/bench.sh`（运行时性能验证）

### 改动
- `compiler/build/bin/regress.py`：加 JHYY_CC 环境变量支持（phase-2 sprint 5 已规划）
- `docs/internal/build.md`：移除 QBE 工具链依赖（"QBE `-t amd64_win`" → 自写后端）

---

## 待 user 后续决定

1. **链接器 / 汇编器**：保留 gcc + as + ld，还是自写？（推荐：保留外部工具链）
2. **N 代 fixed point**：3 代收敛够，还是要求 N → ∞？（推荐：3 代最低 + 后续讨论无限）
3. **跟 phase-3 顺序**：phase-2 → 2.5 → 3 串行，还是 phase-3 部分跟 2.5 并行？
4. **指令集覆盖深度**：最小子集（add/sub/mul/mov/call/ret）先做，还是覆盖完整 x86_64？
5. **性能优化策略**：peephole + 确定性寄存器分配先做，还是等 v4.x 优化期统一做？

---

## 风险总表

| 风险 | 影响 | 缓解 |
|---|---|---|
| deterministic optimization 难做到 | 全部 .s byte-equal 要求 | 早期 inventory + 排序策略 |
| x86_64 指令集覆盖不全 | 部分 .jhyy 源编译失败 | L3 sprint 1 先 grep 现有 QBE IL 用例 |
| 自写 QBE 性能退化 > 1.1x | 运行时性能不达标 | peephole pass + 寄存器分配调优 |
| N 代 fixed point 收剑不到 | 完成定义不达标 | jhyy_N 和 jhyy_{N+1} diff；若发散回退定位 |
| phase-2 前端翻译有缺陷 | phase-2.5 起步基础不稳 | phase-2 完成后做严格 .il byte-equal 验证 |
| 自研 OS ABI 不兼容 | 多目标架构未来扩展 | 当前 amd64_win 中间态；多目标 phase-4+ 考虑 |

---

## Verification（phase-2.5 完成验证）

1. **编译验证**：C 版 jhyy 编译 src0/qbe/*.jhyy + src0/main.jhyy → jhyy_0
2. **自举验证**：
   - jhyy_0 编 src0/main.jhyy → jhyy_1
   - jhyy_1 编 src0/main.jhyy → jhyy_2
   - jhyy_2 编 src0/main.jhyy → jhyy_3
   - `diff jhyy_2 jhyy_3` 产 .il 字节相等（**编译器自身 fixed point**）
3. **.il byte-equal**：jhyy_0 / jhyy_1 / jhyy_2 对 fib.jhyy / ackermann.jhyy 产 .il 全部 byte-equal
4. **.s byte-equal**：jhyy_0 / jhyy_1 / jhyy_2 对 fib.jhyy 产 .s 全部 byte-equal
5. **regress.py**：jhyy_2 跑全过（行为覆盖）
6. **bench.sh**：jhyy_2 产 .exe 跑 fib / ackermann / nqueens ≤ 1.1x C 版 QBE 生成代码
7. **C 版 QBE 移除**：build.md 移除 QBE 工具链；jhyy_2 不依赖外部 qbe.exe
