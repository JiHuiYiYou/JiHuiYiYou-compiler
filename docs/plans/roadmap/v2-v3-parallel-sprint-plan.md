# v2.x || v3.x 并行 Sprint 计划(L1.5 跨轴 sprint 调度)

> **状态**: 设计文档(L1.5 — 跨轴 sprint 调度,合并两轴视角)
> **生成原因**: v2.x-qbe-rewrite.md § 6 + v3.x-language-expansion.md § 0 + v2.0.0-os-prep.md § 2 已分别提到 v2 / v3 部分并行,但无**单一权威** sprint 级并行排程。本文件为 sprint 设计者提供:
> 1. v2.x / v3.x 并行关系总图(架构层 + sprint 层)
> 2. 共同前置
> 3. 独立性论证 + 风险触点
> 4. sprint 排程表(具体顺序)
> 5. OS M1 / M4 / M11 launch 路径映射 + 节点顺序
> **前置**: v1.0 真自举闭环(M4 hard)
> **不在 scope**: v0.x(已完成) / v1.x sprint 设计(→ [v1.0-self-hosting.md](v1.0-self-hosting.md)) / OS 端设计(→ `jhyy_OS/` repo)
> **权威源**: 本文件不替代 L1 长篇;v2.x 范围以 [v2.x-qbe-rewrite.md](v2.x-qbe-rewrite.md) 为准,v3.x 特性以 [v3.x-language-expansion.md](v3.x-language-expansion.md) 为准,OS 启动链路以 [v2.0.0-os-prep.md](../v2/v2.0.0-os-prep.md) 为准

---

## § 1 并行关系总图

### 1.1 架构层(per CLAUDE.md + v2.0.0-os-prep.md § 2)

```
                [v1.0 真闭环 (M4 hard)] ← 共同前置
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
          [v2.x 轴]                       [v3.x 轴]
    (QBE rewrite + 多 target)      (语言特性扩展)
              │                               │
              ├─ v2.0                         ├─ v3.0 (3a-3f)
              ├─ v2.x 中期                    ├─ v3.1 (3g + 3g.5 + 3g.7)
              └─ v2.x 末                      ├─ v3.2+ (3h-3n)
                                              └─ v3.x 末
              │                               │
              └───────────────┬───────────────┘
                              ▼
                          [OS M1]
```

### 1.2 sprint 层

| 阶段 | v2.x 轴 sprint | v3.x 轴 sprint | 并行关系 | 合流点 |
|------|---------------|---------------|---------|--------|
| v1.0 后 立即 | **v2.0 A**: amd64_win_freestanding target | **v3.0 3a**: inline asm | ⟂ 完全独立 | 各自 ship, M1 启动前完成 |
| v2.0 A 后 | **v2.0 B**: hello-freestanding.efi 跑 OVMF | **v3.0 3b**: #[naked] fn | ⟂ 完全独立 | 各自 ship |
| ... | ... | ... | ... | ... |
| v2.0 末 + v3.0 3a-3f 末 | v2.0 完成 | v3.0 完成 | ⟂ | **OS M1 launch** |
| v2.x 中期 | **v2.x M1**: 自写 IL → .s | **v3.1 3g**: &mut + lifetime + Cap<T> | ⟂ 部分独立(lifetime 暗示 escape analysis → 跟自写 regalloc 互动) | **OS M4 launch**(capability) |
| v2.x 中期 + v3.1 后 | **v2.x M2**: amd64_sysv | **v3.1 3g.5/3g.7**: phantom 0-byte + cap 表 byte-equal 联调 | ⟂ | M4 联调 |
| v2.x 末 + v3.2+ | **v2.x 末**: N 代 fixed point + QBE 移除 | **v3.2+ 3i/3j/3l**: generics / closures / std | ⟂ | **OS M11 launch**(自举 OS 真闭环) |

> **⟂ 符号说明**(per CLAUDE.md + `project_v2_v3_parallel_axes.md`):表示两轴**无 semver 顺序**,M1 启动前两轴各自达成即可。sprint 启动者必须显式查 v2 / v3 是否并行或顺序,不要按 semver 推论。

---

## § 2 共同前置

| 项 | 当前状态 | 完成定义 |
|----|---------|---------|
| v0.9 末(Stage 1 单层 byte-equal) | 🚧 wip commit 2.21,Task #61 PARTIAL | C 版 jhyy 编 src0/main.jhyy → jhyy_0 → 编 src0/main.jhyy → jhyy_1;`diff jhyy_0.il jhyy_1.il` byte-equal;regress.py 持平 12 OK baseline |
| v1.0 末(M4 hard,Stage 2 三层 N=3 fixed point) | 未启动 | jhyy_1 编 src0/main.jhyy → jhyy_2;jhyy_2 编 → jhyy_3;`diff jhyy_2.il jhyy_3.il` byte-equal;regress 持平 baseline;main.jhyy runtime 跑通 |

> **⚠️ 术语澄清**:`v0.9 末` ≠ `v1.0 末(M4 hard)`。v0.9 是 Stage 1 单层(jhyy_0 vs jhyy_1 byte-equal);v1.0 是 Stage 2 三层 N=3(jhyy_1/2/3 fixed point)。**v2.0/v3.0 真正硬前置是 v1.0 末(M4 hard),不是 v0.9 末** — 后者只到 Stage 1,后者进度不影响 v2.0/v3.0 启动时点。

**v0.9 距 commit 2.21 待做**(per `architecture-refactor § 16.3`):
- commit 2.22: 29-extsw hypothesis 验证 + 修 arena.jhyy 翻译稿(若 50/50 命中)
- commit 2.23: W-001~W-009 全部真修 + 删 jhyy 端 workaround 注释 + 3 处 C 端 codegen.c 改
- commit 2.24: 翻译 main.c → main.jhyy(523 行)
- commit 2.25: Stage 1 byte-equal 验证 + regress.py `JHYY_CC` env var 改

**v1.0 距 v0.9 末待做**(per `v1.0.0 任务清单` 5 sprint 框架):
- sprint 1-2: 翻译 codegen.c / jhyy_helpers.c 主体 → jhyy_0 / jhyy_1
- sprint 3-4: 全 src0/*.jhyy 翻译 + Stage 2 三层验证(N=3 byte-equal)
- sprint 5: regress.py jhyy_1 跑通 + v1.0.0 changelog 收尾

**v2.0/v3.0 总前置**:**v0.9 末 + v1.0 末(M4 hard)**

---

## § 3 独立性论证

### 3.1 改动文件不重叠

| 维度 | v2.x | v3.x |
|------|------|------|
| **主改** | codegen 后端(QBE → 自写)/ target dispatcher | lang-spec + sema + codegen 单点 emit |
| **路径** | `compiler/src0/target/` + `compiler/src0/qbe/`(v2.0 启动) | `compiler/src0/sema.jhyy` + `compiler/src0/codegen.jhyy` 单点 |
| **依赖** | v0 C 端 `codegen.c` + QBE 工具链 | `jhyy-lang-spec-v1.0.0.md` + `jhyy-abi-v1.0.0.md` |

### 3.2 ABI 影响隔离

| 改动 | v2.x 影响 | v3.x 影响 |
|------|---------|-----------|
| spec 增补 | § 12(多 target ABI) | 各特性节(§ 14 / § 15 / § 16) |
| 不冲突 | ✓ | ✓ |

---

## § 4 风险触点(3 处交叉)

### 4.1 v2.0 freestanding ↔ v3.0 3d `#[no_std]` (per v2.0.0-os-prep § 3 D3)

- **关系**: v2.0 freestanding **不依赖** `#[no_std]` crate attr(只需"不 link libc"); `#[no_std]` 跟 v3.0 sprint 3d 联动
- **可并行**: ✓ 两者可独立 ship
- **3d 软 ship 关系**(per `coordination.md § 3 D10`):3d `#[no_std]` 是**软要求**,**M1 启动不依赖 3d**。v2.0 完成后 v2.0 freestanding 已能让 OS 编 `kernel.efi` 不 link libc;3d 仅是代码风格属性(给 OS 代码清晰度),M1 launch 后再 ship 也行
- **集成测试**: jhyy 编 `#[no_std] kernel.jhyy` 在 freestanding 环境下跑通(v2.0 + 3d 联调)— **可推迟到 M1 launch 之后**,非 M1 硬前置
- **建议顺序**: v3.0 3d 可在 v2.0 后任何时点做;3d 集成测试可在 M1 启动后合并跑(非 M1 启动前)

### 4.2 v2.x 自写 IL → .s ↔ v3.0 3c volatile

- **关系**: v2.x 自写后端要 emit volatile load/store; v3.0 3c volatile 在 QBE 后端先 ship
- **建议顺序**:
  - **v3.0 3c**(QBE 后端实现,验证 OK)
  - **v2.x 自写 IL → .s**(移植 volatile 语义到自写后端)
- **不阻 v3.0 3c 自身 ship**: v3.0 3c 完成后用户已可用 volatile

### 4.3 v3.1 3g lifetime ↔ v2.x 自写 regalloc

- **关系**: 3g lifetime 暗示 `&mut` 借用编译期校验; codegen 是 escape analysis → regalloc 要保留变量在借用期不被覆盖
- **建议顺序**:
  - **v3.1 3g 先 ship**(借用检查 + QBE 后端 emit 路径)
  - **v2.x 自写 regalloc 后做**(移植借用保留语义)
- **风险**: 中(regalloc 启发式要兼顾借用保留 + 确定性 byte-equal)
- **缓解**: v3.1 3g 期间先做 escape analysis pass,验证借用保留语义在 QBE 后端正确

---

## § 5 Sprint 排程

### 5.1 路径 A: v2.0 || v3.0 3a-3f → OS M1

| Sprint | 内容 | 依赖 |
|--------|------|------|
| **v0.9 末** | W-001~W-009 真修 + main.c 翻译 + Stage 1 byte-equal | (当前 wip commit 2.21) |
| **v1.0**(5 sprint 框架) | codegen.c / jhyy_helpers.c 翻译 + 全 src0/ 翻译 + Stage 2 三层 N=3 fixed point | v0.9 末 |
| **v1.1.0** ⟂ **v2.0 sprint A** 前段 | lang-spec § 18-21 + abi § 12 草案 / amd64_win_freestanding target 起步 | v0.9 末 / v1.0 末 |
| **v2.0 sprint A** ⟂ **v3.0 3a** | amd64_win_freestanding target + QBE + GCC / inline asm | v1.0 末 / v1.0 末 |
| **v2.0 sprint B** ⟂ **v3.0 3b** | hello-freestanding.efi 跑 OVMF / #[naked] fn | v2.0 A / v1.0 末 |
| **v2.0 sprint C** ⟂ **v3.0 3c** | 多目标 dispatcher + **byte-equal 三件套**(per `coordination.md § 3 D26`:`jhyy_v1.il == jhyy_v2.il` + `.s == .s` + `.exe byte-equal` 兜底 `gcc -g0 + strip + SOURCE_DATE_EPOCH + --build-id=none`) / volatile load/store | v2.0 A / v1.0 末 |
| **v3.0 3e** | #[link_section] | v1.0 末 |
| **v3.0 3f** | memory barrier | v1.0 末 |
| **v3.0 3d** | #[no_std] + core(**软**, M1 启动不依赖 per D10) | v1.0 末 |
| **M1 launch** | OS 编 kernel.efi + QEMU + OVMF + printk | v2.0 + v3.0 3a-3c/3e-3f 全 ship(3d 软,M1 不依赖) |

**关键**:v2.0 sprint A + v3.0 3a + v1.1.0 spec drafting **并行启动**是 wall-clock 关键,三者改不同文件层(.md vs .c/.jhyy vs .jhyy),无冲突。

### 5.2 路径 B: v2.x 中期 || v3.1 3g + 3g.5 + 3g.7 → OS M4

> **⚠️ 顺序强制**(per `coordination.md § 3 D27`):**3g → 3g.5 → 3g.7 顺序不可调换** — 3g.5 phantom 0-byte codegen 路径依赖 3g 的 codegen;3g.7 cap table 联调依赖 3g.5 锁定的 8 字节布局。

| Sprint | 内容 | 依赖 |
|--------|------|------|
| **v3.1 3g** ⟂ **v2.x M1** | &mut + lifetime + Cap<T> 8 规则 / 自写 IL → .s + 确定性 regalloc + peephole | M1 / v2.0 末 |
| **v2.x M1-A** | amd64_codegen.jhyy(IL → amd64 .s 主体,windows target) | v2.0 末 |
| **v2.x M1-B** | 确定性 regalloc + peephole + 跨 target(windows + sysv + freestanding)联调 | v2.x M1-A |
| **v3.1 3g.5** | phantom 0-byte codegen | 3g |
| **v3.1 3g.7** | jhyy_OS cap 表 byte-equal 联调 | 3g.5 |
| **OS M4 launch** | OS 端 Cap<T> 程序跑通 | v3.1 3g + 3g.5 + 3g.7 + v2.x M1-B |

**v2.x M1 拆 sprint 建议**:
- amd64_codegen.jhyy 从零写 + 指令集覆盖盘点(整数 / 内存 / 控制流 / syscall / struct sret,浮点延后 per `v2.x-qbe-rewrite § 5 挑战 2`)+ 确定性 regalloc + peephole + 多 target 联调。**历史经验**:QBE 1.0 用了 1-2 年,LLVM -g0 模式是后期才稳定;即便 jhyy 复用 QBE IL 层有优势,M1 是大特性,需分阶段 ship
- **拆法 A**(推荐):中-A 写 windows IL → .s 主体(目标 = `jhyy --target=amd64_win hello.jhyy` 产 .s 跟 C 版 QBE 字节相同)+ 中-B 加 sysv + freestanding + regalloc + peephole(目标 = 多 target 跨编 jhyy 字节相同)
- **拆法 B**(保守):中-A = windows 主体 + 中-B = sysv 主体 + 中-C = regalloc + peephole 优化
- user 后续在 v2.x 启动 L3 任务清单时定

**关键**: v3.1 3g 优先 ship(借用检查是 M4 硬前置,跟自写 regalloc 解耦 → 见 § 4.3);3g.5 / 3g.7 串行跟随 3g

### 5.3 路径 C: v2.x 末 || v3.2+ → OS M11

| Sprint | 内容 | 依赖 |
|--------|------|------|
| **v3.2 3i** ⟂ **v2.x M2** | generics(单态化)/ amd64_sysv + amd64_sysv_freestanding(在 M1-B 上加 target) | v3.1 3g 末 / v2.x M1-B |
| **v3.2 3j** | closures | 3i |
| **v3.2 3l** | std lib(9 模块) | 3i, 3j |
| **v2.x 末** | N 代 fixed point(N=3) + QBE 工具链完全移除 | v2.x M1-B + M2 |
| **OS M11 launch** | jhyy_OS 跑 jhyy 编译器 + 编 jhyy_OS(真自举 OS 闭环) | 全部 ship |

### 5.4 总里程碑节点(顺序链,无时间)

| 里程碑 | 关键节点 |
|--------|---------|
| **v0.9 末**(Stage 1 单层 byte-equal) | 当前 → 2.22(29-extsw 验证)→ 2.23(W 真修)→ 2.24(main.c 翻译)→ 2.25(Stage 1 + regress.py JHYY_CC) |
| **v1.0 末**(M4 hard,Stage 2 三层 N=3) | v0.9 末 → 5 sprint 框架 |
| **OS 端可设计 / prep** | v0.9 末起 — OS 团队写 kernel 源码(用 `*mut T` raw pointer per D5),不编 |
| **OS 端可编译 + 跑**(编 + OVMF 实际 M1 验证) | v1.0 末 + v2.0 + v3.0 3a-3c/3e-3f 全 ship |
| **OS M1 launch**(kernel boot, printk 到 framebuffer) | v2.0 + v3.0 3a-3c/3e-3f 全 ship(3d 软,M1 不依赖) |
| **OS M4 launch**(capability 落地) | M1 + v3.1 3g + 3g.5 + 3g.7 + v2.x M1-A + M1-B |
| **OS M5b + M8d 启动**(IPC + GUI 协议层,per `coordination.md § 3 D32`) | M4 + 3g.5/3g.7 后(Wayland-style compositor 单态 type 妥协 per D33) |
| **OS M11 launch**(自举 OS 闭环) | M4 + v3.2+ 3i/3j/3l + v2.x 末(N 代 fixed point + QBE 移除) |
| **OS M12 启动**(GUI 工具包,per `coordination.md § 3 D31` 候选 C) | M11 后(吃完整 3h 浮点 + 3i generics + 3j 闭包 + 3l std lib) |

---

## § 6 OS M1 launch 路径(详细顺序图)

```
当前 (2026-08-06)
  │
  ↓ (commits 2.22-2.25)
v0.9 末(Stage 1 单层 byte-equal)✅
  │
  ├──> OS 端可立刻开始 prep + 用 raw pointer (`*mut T` per D5) 写 kernel 源码
  │    (注:写完不编,要等 v1.0 末 + v2.0 + v3.0 3a-3c/3e-3f 全部 ship 后才能跑)
  │
  ↓ (v1.0 5 sprint 框架)
v1.0 末(M4 hard,Stage 2 三层 N=3)✅
  │
  ├──> OS 端继续 prep(已写源码 + 单元测试)
  ├──> [v1.1.0 spec drafting] (跟 v2.0 A / 3a 并行,改 .md 不冲突)
  │
  ↓ 并行启动 (v1.0 末后立刻)
  │
  ├──> [v2.0 sprint A-C] (3 个 sprint, 串行内部但可被 v3 sprint 交错)
  │     - A: amd64_win_freestanding target + QBE + GCC
  │     - B: hello-freestanding.efi 跑 OVMF
  │     - C: 多目标 dispatcher + byte-equal 三件套(per D26)
  │
  └──> [v3.0 3a-3f] (5-6 个 sprint, 关键路径 = 3a-3c/3e-3f;3d 软可推迟)
        - 3a inline asm
        - 3b naked fn
        - 3c volatile
        - 3e link_section
        - 3f memory barrier
        - 3d no_std(软,M1 启动不依赖 per D10,M1 后再 ship 也行)
  │
  ↓ 联调
M1 launch (OS 编 kernel.efi + QEMU + OVMF + printk)
```

---

## § 7 实操建议(单/双 sprint 切换)

**单人维护可考虑**:
- 每周一半时间做 v2.0 sprint, 一半时间做 v3.0 sprint(避免 context switch 开销,具体分配按 sprint 设计者偏好)
- 或 commit 交叉(每 v2 改 3 commit 后切 v3 改 3 commit)
- 关键: 两个轴都维持活跃, 避免一个轴停太久失活

> **⚠️ Context switch 开销**:每次切轴要重新加载 4-5 个文档(spec + abi + roadmap + 当前 sprint doc + coordination)到 LLM context。建议:每 sprint doc 加一行"本 sprint 关键文件清单"减少切换开销;或者把 v2.0 sprint A 跟 v3.0 3a 严格串行(避免一开始就并行切换),后续再切节奏。

**双 sprint 设计原则**:
- 每个 sprint ship 必须有独立验收标准(不互相阻塞)
- v2.0 集成测试 + v3.0 3a-3c/3e-3f 集成测试分别在各自 sprint 末做;**M1 launch 前停下新 feature, 做端到端联调**(编 OS kernel.efi + 跑 OVMF)
- v3.0 3d(#[no_std])集成测试单列,**可在 M1 launch 后合并跑**(软, M1 不依赖 per D10)

**节奏建议**:
1. v1.0 末(M4 hard)ship 后立即启动 v2.0 sprint A + v3.0 3a + v1.1.0 spec drafting(三个独立特性, 改不同文件层无冲突)
2. 之后按 commit 切换节奏穿插(避免 context switch 开销)
3. v3.0 3d(#[no_std])放最后做, 集成测试可推迟到 M1 之后(软)
4. M1 launch 前停下 v2.0/v3.0 新 feature(3d 例外), 全员做端到端联调

---

## § 8 Cross-reference

| 文档 | 关系 |
|------|------|
| [v2.x-qbe-rewrite.md](v2.x-qbe-rewrite.md) | v2.x 轴权威 L1 文档(本文件是其 sprint 级细化 + 并行视角) |
| [v3.x-language-expansion.md](v3.x-language-expansion.md) | v3.x 轴权威 L1 文档(本文件是其 sprint 级细化 + 并行视角) |
| [v2.0.0-os-prep.md](../v2/v2.0.0-os-prep.md) | OS 启动链路 + 跨项目接口权威(本文件引用其 M1-M11) |
| [v1.0-self-hosting.md](v1.0-self-hosting.md) | v1.0 真闭环 L1 文档(本文件共同前置) |
| [v1.0.0任务清单 + 概要设计.md](../v1/v1.0.0任务清单 + 概要设计.md) | v1.0 5 sprint 框架(M4 hard = sprint 3-4 末达成,本文件 § 2 + § 5.1 引用) |
| [architecture-refactor.md](architecture-refactor.md) | 整体重构 L1 文档(本文件是其 § R-6 细化) |
| [../../jhyy_OS/docs/coordination.md](../../../../jhyy_OS/docs/coordination.md) | 跨项目对齐(本文件 M1-M11 引用其决策) |

---

## § 9 Open Questions(sprint 启动前 user 决定)

| # | 问题 | 建议 |
|---|------|------|
| 1 | v2.0 + v3.0 是否真的并行(双 sprint 同时活跃)?还是先 v2.0 全部 ship 再 v3.0? | **并行**(wall-clock 短 ~50%) |
| 2 | 单人维护节奏(每天切 vs commit 切)? | **commit 切**(避免上下文切换开销) |
| 3 | v2.0 sprint A(freestanding target)是否要先做 QBE → GCC 链验证,再开始 v3.0 3a? | **是**(QBE 链不稳 → v3.0 3a 调试困难) |
| 4 | M1 launch 后, v2.x 中期 vs v3.1 3g 哪个优先? | **v3.1 3g 优先**(借用检查是 M4 硬前置,跟自写 regalloc 解耦) |
| 5 | v1.1.0 spec drafting(§ 18-21)是否跟 v2.0 sprint A + v3.0 3a 并行启动? | **并行**(spec 改 .md,codegen 改 .c/.jhyy,无冲突) |
| 6 | v2.x 中期"自写 IL → .s"按单 sprint 还是拆 2 sprint 估(中-A windows 主体 + 中-B sysv + regalloc + peephole)? | **拆 2 sprint**(单 sprint 范围过大;按拆 sprint 先 ship windows,后续加 target) |
| 7 | v3.0 3d `#[no_std]` 是否在 M1 launch 前必须 ship? | **否**(per `coordination.md § 3 D10` 软要求;M1 launch 不依赖;M1 启动后合并跑集成测试即可) |
