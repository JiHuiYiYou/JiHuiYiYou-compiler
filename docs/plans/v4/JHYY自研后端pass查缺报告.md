# JHYY 自研后端 pass 查缺报告（基于实际源码审计）

审计对象：`JiHuiYiYou/JiHuiYiYou-compiler` main 分支快照
审计范围：`compiler/src0/codegen_amd64*.jhyy`、`codegen_amd64_regalloc.jhyy`、`codegen_amd64_peephole.jhyy`、`docs/plans/roadmap/v2.x-qbe-rewrite.md`
生成日期：2026-10-25

> ⚠️ **本报告的审计对象是 v2.x 时代的快照**（2026-10-25 按 v4.0.21 源码复核过）。
> **技术内容基本仍然成立**（pass 缺口清单、regalloc 未接、peephole 规则数、
> 行数等已逐条复核），但**下面 §〇 的流水线描述与 §4.1 的 benchmark 配方
> 描述的是旧架构** —— QBE 已于 **v3.1.0** 从运行期彻底移除，当前**没有**
> 「默认走 qbe.exe」这条路径。复核时改掉的地方都标了 `【复核修正】`。

---

## 〇、先纠正一个命名

`docs/logs/v2/retrospective-v2.11.23.md:273` 写得很清楚：

> 不是"自研后端替代 QBE" —— QBE 还在 path 里…**自研后端替代的是 codegen 那一段**（AST → QBE IL），不替代 QBE 后端 codegen。

但**当前代码状态已经超出了这句话**。真正的架构是：

```
.jhyy → (前端 lexer/parser/sema) → QBE IL (.il)
      → codegen_amd64_run: lex_il → parse_and_emit → peephole → .s → gcc
```

即 `codegen_amd64*.jhyy` 这一组是**直接吃 QBE IL、吐 x86-64 汇编的自写后端**，`codegen_amd64_lexer.jhyy`（2230 行）负责解析 QBE IL 文本。所以它确实是在重写 QBE 后端，而不是只重写前端。

**【复核修正】上面的流水线原图写的是「`JHY_SELF_BACKEND=1` 时走自研后端 /
默认走 `qbe.exe`」—— 这在当前代码上已不成立：**

- `main.jhyy:890-903` 的 `run_qbe` 是 **fatal stub**（「QBE backend removed in
  v3.1.0 — self-backend sole production path」），且**全仓零调用点**；
- `main.jhyy:915-927` 的 `run_backend`（唯一的生产分派）**无条件**调
  `codegen_amd64_run`；
- **`JHY_SELF_BACKEND` 编译器根本不读** —— 它只剩 `codegen_amd64.jhyy:271` 与
  `main.jhyy:55` 两处**注释**，以及几个把它当「跳过测试」开关的脚本
  （`mcp-jhyy/jhyy_regress.py:493` / `compiler/tests/bootstrap/byte_equal_selfbackend.sh:153`）。
  编译器真正读的环境变量只有 `JHY_WRITE_IL` 与 `QBE_FALLBACK`（后者已被忽略）。
- `qbe/qbe.exe` 仍在仓里，但只被开发用的 bench 脚本
  （`scripts/dev/bench/self_host_bench.sh:54`）调用。

**⇒ 「自研后端是唯一生产路径」这件事从 v3.1.0 起就成立**，不是 v4.x 才变的。

**流水线实际代码位置**：`codegen_amd64.jhyy:265` `codegen_amd64_run()`

```
1. jh_read_file(.il)         cap 4MB
2. arena_init(8MB) → lex_il() → lex_il_count()
3. malloc CGState(768B) + cg_state_init + cg_state_set_target
4. cg_compute_per_fn_max_temps()      ← 栈帧大小预扫
   （【复核修正】原清单漏了紧接着的 cg_compute_global_max_temp +
     cg_state_set_frame_max_temp,codegen_amd64.jhyy:368-369）
5. regalloc_clear_global()            ← 【实际是跳过 regalloc】
6. parse_and_emit()                   ← emit_* 分派
7. cg_state_get_temp_overflow() 检查   ← 越界即响亮失败
   （【复核修正】原清单漏了 W-130 的 holds 溢出响亮失败,
     codegen_amd64.jhyy:401-408）
8. peephole_fold_with_len()           ← 【>4096 字节直接返回原样】
   （【复核修正】阈值判断实际在 peephole_fold,peephole.jhyy:545-547;
     peephole_fold_with_len 只是转发,:737 → :751 —— 结论不变）
9. jh_write_file(.s)
```

---

## 一、确认缺失的 pass（对照 QBE 官方清单）

| # | Pass | QBE | JHYY 自研后端 | 证据 |
|---|---|---|---|---|
| 1 | SSA 构造 / phi 插入 | ✅ | ❌ 不构造 | ILTOK_PHI 存在（`state.jhyy:60`），但依赖上游 QBE IL 已是 SSA；自身不重建 |
| 2 | 稀疏条件常量传播 SCCP | ✅ | ❌ | 全仓无 sccp/const-prop 实现 |
| 3 | 常量折叠 / 代数化简 | ✅ | ❌ | 同上 |
| 4 | 简单 GVN | ✅ | ❌ | 无 |
| 5 | 复制传播 / 合并 | ✅ copy() | ❌ | peephole Rule 3 已删除（见 §二） |
| 6 | 死代码消除 | ✅ | ❌ | 只有 peephole 的 3 条局部规则 |
| 7 | 别名分析 | ✅（隐式） | ❌ | 无 |
| 8 | 死存储消除 / load 转发 | ✅ | ❌ | 无 |
| 9 | 小栈槽寄存器化 | ✅ | ❌ | 反过来：全部寄存器化到栈槽 |
| 10 | 活跃区间分析 | ✅ | ⚠️ 实现了但没接 | `regalloc.jhyy` 有 build interval 逻辑 |
| 11 | split spiller | ✅ | ❌ | 无 |
| 12 | 溢出启发式（循环分析） | ✅ | ❌ | 无循环分析 |
| 13 | **寄存器分配** | ✅ linear scan + hint | ❌ **完全未启用** | 见 §二，最严重的一条 |
| 14 | 指令选择 + 窥孔 | ✅ | ⚠️ 3 条规则，且大文件不跑 | 见 §二 |
| 15 | 尾调用优化 | — | ❌ | 无 |
| 16 | ABI lowering | ✅ | ✅ 较完整 | `abi_amd64_win.jhyy` 309 行 + `abi_amd64_sysv.jhyy` 584 行；v2.13.0 补齐 SysV 8-class 分类 |

peephole.jhyy 文件头自己写了不做哪些（第 5–7 行）：

> - **不**做 instruction scheduling（超标量 / OoO）— 留给 post-M5
> - **不**做 loop optimization / LICM / GVN — 留给 post-M5

**结论：16 项里 1 项完整（ABI），1 项半残（peephole），14 项缺失。**

---

## 二、三个"存在但等于没有"的关键项

### 2.1 寄存器分配：972 行实现，完全没接

`codegen_amd64.jhyy:369-381`：

```jhyy
// v2.11.2 (W-074.6 T3-b):regalloc_run SKIP — 走 cg_offset_for_temp_with_target
// 公式 fallback (v2.5.0 1-to-1 简化)。原因:regalloc_run 在 self path
// 还没 wire 完整,产出的 spill offset 跟 emit_mem/ctrl/call 不对齐会
// 静默错槽。skip 后所有 offset 走 identical `-(32 + t*8)` 公式
let _clear_rc = regalloc_clear_global();
// let reg_arr = regalloc_init(&arena);
// if reg_arr != (0 as *u8) {
//     let _ = regalloc_run(&arena, reg_arr, tokens, n);
// }
```

`codegen_amd64_regalloc.jhyy` 第 3–5 行也确认：

> emit 函数目前还是 v2.5.0 1-to-1 栈路径（per plan：regalloc 输出"可用但未消费"）

**后果**：每个 SSA 临时值 `%tN` 都落在 `-(32 + N*8)` 的栈槽上。每一次运算都是 load → 算 → store。

`MAX_TEMPS = 64`（`regalloc.jhyy:63`）。

### 2.2 peephole：4 条规则删到 3 条，且大文件整体跳过

- 计划 4 条：identity op / zero-init / redundant copy / self-move
- **Rule 3（redundant copy）整块删除**（`peephole.jhyy:668-680`）：会产生 `movq %rcx, %eax` 这类 size mismatch 非法 x86；v2.13.0 发现 jhyy 不识别常量 false gate，仍执行 body 导致 `n_lines` 被写坏、"整个 fold 失效"，于是真删除而非 gate
- **剩余 3 条：identity op / zero-init / self-move** —— 都是"删掉 no-op"级别，不是真正的优化

更致命的是 `peephole.jhyy:543-547`：

```jhyy
// Workaround: skip fold for len > 4096 (emit raw .s 直传)
if len > (4096 as i64) {
    return input;
}
```

原因：`.s` 超过 4096 字节时 peephole_concat_loop 静默崩溃（W-074.6.1 PARTIAL）。

**后果**：任何真实程序的 `.s` 都远超 4096 字节（自举那份 IL 有 1.378 MB），所以**peephole 在真实代码上从不运行**。它的 3 条规则只对 hello-world 级别的小文件生效。

### 2.3 XMM regalloc 是 ABI 层，不是通用 regalloc

`codegen_amd64_xmm_argalloc.jhyy`（267 行，v2.13.0 新增）解决的是**浮点参数按 SysV/Win ABI 分配到 xmm0-xmm7**，属于调用约定的一部分。它不等于通用寄存器分配——函数体内的临时值仍然全部落栈。

---

## 三、结构性矛盾：byte-equal 与优化直接冲突

这是这份审计里最重要的一条，也是你们自己已经在文档里承认的（`v2.x-qbe-rewrite.md § 5 挑战 1`）：

> 传统编译器优化（peephole / 指令调度 / 寄存器分配启发式）会破坏 byte-equal：
> - 不同 run 调度顺序不同 → .s 不一致
> - 哈希表迭代顺序不稳定 → 寄存器编号不同

而风险表（`§ 9`）写着：

| 风险 | 影响 | 缓解 |
|---|---|---|
| 自写 QBE 性能退化 > 1.1x | 运行时性能不达标 | peephole pass + 寄存器分配调优 |

**这两条是互斥的**：每调一次寄存器分配启发式 → `.s` 变 → D43 closure sha 变 → 必须 re-baseline。项目历史上已经 re-baseline 过多次（v2.4.0、v2.8.0、v2.11.9、v2.13.0 都触发过）。

**必须先决策**：性能目标和 byte-equal 目标，哪个优先？

建议的解耦方式——**把确定性约束在 pass 内部，而不是放弃 pass**：

- 寄存器分配用固定顺序启发式（你们 regalloc.jhyy 已经这么设计了：*"lowest temp_id wins on conflict"*，确定性 ✓）
- 所有遍历用排序而非哈希（symtab 已按名字 sorted ✓）
- peephole 规则按模式排序应用 ✓

这样每次调启发式仍会改 sha，但**只在调的时候改一次**，而不是每次运行都抖。所以真正的成本是 re-baseline 频次，不是不可兼得。

---

## 四、上基准测试前的现实评估

### 4.1 预期性能量级

全部临时值落栈（`-(32 + N*8)`）、零寄存器分配、零别名分析、peephole 不生效。对照 QBE 官方自我定位"约 LLVM -O2 的 73%"：

**粗估 JHYY 自研后端当前落在 QBE 的 30–50% 区间，即 LLVM -O2 的 20–35%。**

这个估算的依据是栈槽模型的固有代价：每个 SSA 值一次 store + 每次使用一次 load。对 temp 密集的数值代码（matmul、primes、fib）放大最明显。

**但这是估算，必须实测。** 建议立刻做一次：

> **【复核修正】** 原来的配方（`qbe -t amd64_win main.il` + `JHY_SELF_BACKEND=1
> jhyy compile`）**照抄跑不通** —— `JHY_SELF_BACKEND` 已不被编译器读取，
> 而 `qbe.exe` 也不再在生产路径上。当前可行的等价做法：

```bash
# ① 自研后端(唯一生产路径):写盘 .il,再单独跑后端
JHY_WRITE_IL=1 jhyy compile prog.jhyy -o prog     # → prog.il + prog.s
# ② QBE 对照臂:用仓里保留的 qbe/qbe.exe 手动跑同一个 .il
qbe/qbe.exe -t amd64_win prog.il > prog_qbe.s
# ③ 反汇编 diff,统计 insn 数 / mov 数 / 访存数
objdump -d prog.s > a.txt ; objdump -d prog_qbe.s > b.txt ; diff a.txt b.txt
```

⚠️ 两条臂的**来源不同**（① 是编译器自带的自举后端，② 是手工调 QBE），
所以对比时要注意 `prog.il` 必须由**同一份** `.jhyy` 产出（`JHY_WRITE_IL=1`
保证这一点）。

### 4.2 关于 v2.11.23 的"完全追平"

`retrospective-v2.11.23.md:21` 写的"自研后端第一次 — 完全追平：跟 QBE path 同数字"指的是**正确性 parity**（119 PASS / 0 FAIL，退出码一致），**不是性能 parity**。

`changelog-v2.13.0.md` 的 Metrics delta 表也印证：regress.py pass rate 是唯一 tracked 指标，**没有任何运行时性能数字**。

`docs/perf/` 下两份 bench 全部测的是**编译时间**（`jhyy build` 前端耗时，明确排除 QBE/gcc 阶段），不是生成代码的运行时间。

**所以：这个项目到目前为止没有做过一次"自研后端 vs QBE 生成代码运行速度"的测量。** 这是最大的空白，也是最低成本能拿到的信息。

### 4.3 两个硬阻塞（同前次清单）

| 阻塞 | 现状 | 解法 |
|---|---|---|
| 目标平台 | 当前主出 amd64_win / amd64_win_freestanding；`abi_amd64_sysv.jhyy` 已 584 行且 v2.13.0 跑通 5/5 SysV 测试 | Linux 目标基本就绪，接 benchLANG 的路径比预想的近 |
| 标准库 | `std/` 有 arena/fmt/io/math/mem/os/string/vec 8 个模块 | **无 JSON / CSV / 正则** → LangArena 的 8 道生态题无法用纯 JHYY 作答，需 FFI 调 C 库并明确标注 |

另外 `MAX_TEMPS=64`、`per_fn_max` 表上限、IL buffer 4MB cap 这三项，在 benchmark 规模的输入下可能先撞到。

---

## 五、整改优先级

### P0 — 先拿数据，别先写优化

1. **做一次 self-backend vs QBE 的运行时间对比**（1 天）
   同一批 benchmark，同一台机器，两组数字。没有这个基线，后面所有优化都是盲改。

2. **把 peephole 的 4096 限制修掉或明确降级**（W-074.6.1）
   现在的状况是：一个只作用于 hello-world 的优化 pass。要么修 concat loop 的崩溃根因，要么在文档里写死"peephole 当前不参与真实构建"，别让它继续占着一个"我们做了 peephole"的位置。

### P1 — 唯一能带来数量级变化的一项

3. **wire regalloc**
   实现已经在了（972 行 linear-scan，且已按确定性设计）。缺的是让 emit_mem / emit_ctrl / emit_call 消费 `regalloc_query_reg()` 的输出。
   
   这是**唯一一项能把性能从 30% 拉到 70% 的改动**。其余所有 pass 加起来都补不上寄存器分配的缺口。
   
   代价：触发 D43 re-baseline。但这是一次性的。

### P2 — 补齐 QBE parity 层

4. 复制传播 / 合并（peephole Rule 3 重做，加 size-aware check）
5. SCCP + 常量折叠
6. 局部 DCE

### P3 — 超过 QBE 的机会点

7. 块布局 / 分支排布（低难度，1–5%，QBE 基本不做）
8. 循环旋转（低难度，3–8%）
9. LICM（中难度，5–20%，QBE 不做）
10. 强度削弱（中难度，5–15%）

**不要现在做向量化。** 在寄存器分配都没接上的状态下加 SIMD，就像在漏水的船上刷漆。

---

## 六、一句话总结

当前自研后端是一个**功能正确、ABI 完整、但零优化的 IL→asm 直译器**：所有临时值落栈槽、寄存器分配实现完成但未接线、peephole 只剩 3 条 no-op 级别的规则且在真实规模输入上整体跳过。

最短路径不是补更多 pass，而是**把已经写完的那 972 行 regalloc 接上去**——它一个人能补的缺口，比剩下所有缺失 pass 加起来还多。
