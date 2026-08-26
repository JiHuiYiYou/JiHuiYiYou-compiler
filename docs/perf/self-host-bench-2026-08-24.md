# Self-Hosting Compile Time Benchmark

**Date:** 2026-08-24
**Snapshot:** 当前 `jhyy.exe` (v1.5.6 era jhyy-side binary, SHA `d524b8d0…`) + `jhyy_v1.exe.exe` (v1.0.0 historical baseline, SHA `37ffc49c…`)
**Cross-reference:** [`v1.0.0-build-bench.md`](v1.0.0-build-bench.md)（单模块对比）;[`../plans/v2/v2.0.0-os-prep.md`](../plans/v2/v2.0.0-os-prep.md)（OS 准备清单里编译器自身构建基线）

## 动机

参考第三方编译器 **TPV** 的自举数据：

| 阶段 | TPV 时间 |
|---|---|
| TPV 自举（编译器编自己，仅 compile-to-IR） | **2 分钟** |
| TPV 自举 + llc + 链接（端到端产出 binary） | **2 分 50 秒** |

想知道 JHYY 在自举维度上的对应数字 —— 给 OS 准备 sprint 的编译器构建预算做参考。

## 测试方法

3 次取最小值（min 减 Windows 进程启动噪声），首次 warmup 不计。

**测量方式：** `/usr/bin/time -f "%e"` 包命令；bash 子壳隔离 `/usr/bin/time` 与命令自身 IO 重定向。

| 阶段 | 命令 | 测量什么 |
|---|---|---|
| **A. 自举（仅 compile-to-IL）** | `jhyy build src0/main.jhyy` | lex+parse+sema+codegen → 1.6 MB IL |
| **B. 自举 + QBE + gcc 链接（端到端）** | `jhyy compile src0/main.jhyy` | A + qbe + gcc + 链接 → 完整 .exe |
| **C. 仅 QBE** | `qbe -t amd64_win main.il > main.s` | 隔离 QBE 耗时 |

**没有单独测 gcc 链接：** `jhyy compile` 内部用绝对路径 + 自定义 flags（per v1.0.0 L1 § 134），手动复制会有 ld 错误；只能用 `B - A - C ≈ gcc + overhead` 推算。

## 系统

- OS: Windows 10 Home 10.0.19045
- MSYS2: 3.6.4 (x86_64)
- 编译器二进制:
  - `jhyy.exe`        (current jhyy-side production, 467 KB) `d524b8d05ef86df80dd1af53858e89db7bf9eb80384a0ee13684646c8a4a25e8`
  - `jhyy_v1.exe.exe` (v1.0.0 historical baseline, 452 KB)        `37ffc49c681c7016310b697f5f324484ebd0cc366653d3febd6b63c81add5f6f`
- QBE: `qbe/qbe.exe` (本地构建，target `amd64_win`)

## 工作量

| 模块 | 行数 |
|---|---:|
| codegen.jhyy   | 3807 |
| parser.jhyy    | 2523 |
| sema.jhyy      | 1987 |
| ast.jhyy       | 1401 |
| main.jhyy      | 1030 |
| lexer.jhyy     |  867 |
| ir.jhyy        |  863 |
| types.jhyy     |  424 |
| util.jhyy      |  354 |
| symtab.jhyy    |  336 |
| arena.jhyy     |  161 |
| ffi.jhyy       |   67 |
| **生产代码合计** | **~13820 行** |
| _driver_*.jhyy / _test_*.jhyy (不进 build) | 3890 |

`main.jhyy` 入口 → 传递闭包 12 个生产模块；不计 `_driver_*` / `_test_*`（driver 文件不进 import graph）。

**IL 输出：** `compiler/src0/main.il` = 1,683,356 B (~120 B/LOC)
**asm 输出：** `main.s` = 1,453,898 B，83,471 行 (~10 asm 行/LOC)

## 结果

| 阶段 | jhyy.exe | jhyy_v1.exe.exe | TPV 参考 |
|---|---:|---:|---:|
| **A. 自举（compile-to-IL）** | **0.32 s** | 0.33 s | 120 s |
| **B. 自举 + QBE + gcc 链接（端到端）** | **7.87 s** | 7.88 s | 170 s |
| **C. 仅 QBE** | **2.46 s** | — | — |
| **B − A − C ≈ gcc 链接 + 进程开销** | **≈ 5.09 s** | — | — |

3-run min；raw 数值见 § Raw timings。

## 解读

### 1. JHYY 自举远快于 TPV（数量级差距）

| 维度 | JHYY | TPV | 倍数 |
|---|---:|---:|---:|
| 自举（compile-to-IR） | 0.32 s | 120 s | **~375×** |
| 端到端（+ llc/QBE + 链接） | 7.87 s | 170 s | **~22×** |

主要来源（粗估）：
- **代码量差异**：JHYY 自举源 ~13.8k 行（生产模块合计），TPV 体量未公布但 MLIR/LLVM 系编译器通常 100k+ 行。
- **单遍 pass vs 多遍 IR 优化**：TPV 走 MLIR 多层 dialect × LLVM 多 pass → 时间主要在 IR 优化；JHYY 只 lex→parse→sema→codegen 一次直出 QBE IL。
- **QBE 单 pass**：2.46 s（1.6 MB IL → 1.45 MB asm），无 LLVM 那种 O(n²) 优化爆炸。

### 2. JHYY 自举的成本结构（端到端 7.87 s 拆分）

| 阶段 | 耗时 | 占比 |
|---|---:|---:|
| lex + parse + sema + codegen | 0.32 s | 4% |
| QBE IL → amd64 asm | 2.46 s | 31% |
| gcc link（含 runtime.c）+ 进程开销 | ~5.09 s | 65% |

**gcc 链接吃大头**：83k 行 asm + `runtime.c` 进 gcc → 单次冷链接 ~5 s。Windows gcc 启动本身 ~50-100 ms × 多个子进程（cc1/collect2/ld），加上 asm → object 编译 + 链接。**端到端优化空间主要在 gcc**：换 lld / mold / 自写 linker 在 Windows 下都没成熟替代。

### 3. Windows 进程启动噪声 ~50-100 ms 占比

- A. 自举 0.32 s：~150 ms 是 jhyy.exe 启动 + QBE 启动 ≈ 实际编译工作 < 200 ms
- C. QBE 2.46 s：~50 ms 进程 + 2.4 s 真实 QBE 工作

→ A 阶段"看似"比 codegen.jhyy 单文件（0.26-0.30 s）还慢一点（13.8k LOC vs 3.5k LOC），但实际**单行耗时反而更低**，因为 jhyy 启动是常数。

### 4. v1.0.0 baseline (`jhyy_v1.exe.exe`) 跟当前 (`jhyy.exe`) 性能同档

- A: 0.33 s vs 0.32 s (差 < 5% — 噪声)
- B: 7.88 s vs 7.87 s (差 < 1% — 噪声)

→ v1.0.0 → v1.5.6 自举性能无回退；新增 feature（inline asm / freestanding / runtime.h 包装等 W-XXX）没引入 codegen 性能墙。

## Caveats

1. **3-run min 抖动**：单 run ±30-100 ms；3-run min 覆盖大部分但极端值仍可能漏。要更高信噪比跑 5-10 runs。
2. **冷启动 vs 热启动**：OS file cache 命中后 read 全在内存；首次 cold start + Windows Defender 实时扫可能 +20-30%。
3. **gcc 拆分靠减法**：`B - A - C ≈ 5.09 s` 包含 jhyy.exe 二次启动 + QBE 二次启动 + gcc 启动 + 真实链接；真 gcc 链接 < 5 s，但精确数字无法独立测（手动调 gcc 复现 flag 会 ld error）。
4. **QBE 单线程**：83k 行单 pass 2.46 s；QBE 1.2 起原生单线程（不是并行优化器），多核机器也吃不满。
5. **未测并行 build**：`jhyy build/compile` 当前是单进程（jhyy 内部不并行）；未来 v2.x 如果引入模块并行编译可重新测。
6. **TPV 体量未公布**：375× / 22× 倍数依赖 TPV 代码量假设；纯数量级比较可信，精确倍数有 ±50% 误差。

## OS 准备 sprint 预算意义

OS 端 ([`../../jhyy_OS/docs/coordination.md`](../../jhyy_OS/docs/coordination.md) § 0 Critical Path) 在 M1 启动时会需要反复 build JHYY compiler。如果 sprint 设计里"build 编译器"出现频率高：

- **每轮冷构建 ~8 s**：可以接受 inline 在开发循环里（保存后即时 rebuild）
- **CI 跑全套（5 platform × 3 stage）~2 分钟**：在 Windows CI 上预算 1 分钟 + 编译 = 3-4 分钟，可行
- **自举 byte-equal 验证链**（v1 → v2 → v3 → v4）：4 × 8 s = **32 s**，可控

→ 自举构建**不是 OS 准备的瓶颈**。OS 端真瓶颈在 runtime.c 重写（OS kernel 用）+ 跨边界 ABI 验证（per D40/D41）。

## Raw timings (3 runs, s)

| 阶段 | 命令 | run1 | run2 | run3 | min |
|---|---|---:|---:|---:|---:|
| A1 | jhyy.exe build src0/main.jhyy          | 0.32 | 0.34 | 0.34 | 0.32 |
| A2 | jhyy_v1.exe.exe build src0/main.jhyy   | 0.33 | 0.33 | 0.34 | 0.33 |
| B1 | jhyy.exe compile src0/main.jhyy        | 8.16 | 8.14 | 7.87 | 7.87 |
| B2 | jhyy_v1.exe.exe compile src0/main.jhyy | 7.90 | 7.88 | 8.11 | 7.88 |
| C1 | qbe -t amd64_win main.il > main.s      | 2.46 | 2.56 | 2.54 | 2.46 |

## 复现

```bash
cd C:/Users/liuzhen/Desktop/coding/JiHuiYiYou
bash tmp/self_host_bench.sh
```

脚本做 warmup + 3 runs + min；输出格式：`runs=R1,R2,R3  min=MIN`。