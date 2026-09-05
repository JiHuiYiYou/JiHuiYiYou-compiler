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
              ├─ v2.0 阶段(串行,先 ship)*     │
              │   ├─ v2.0.0 (Sprint A Stage 1: target dispatcher)
              │   ├─ v2.1.0 (Sprint A Stage 2: ABI 抽离)
              │   ├─ v2.2.0 (Sprint A Stage 3: spec 锁定)
              │   ├─ v2.3.0 (Sprint B: hello-freestanding.efi + OVMF)
              │   └─ v2.4.0 (Sprint C: 多目标 dispatcher + byte-equal 三件套)
              ├─ v2.x 中期 ── ⟂ ────────────  ├─ v3.0 (3a-3f, v2.0 末启动)
              │                               │
              ├─ v2.x 末 ── ⟂ ──────────────  ├─ v3.1 (3g + 3g.5 + 3g.7)
              │                               │
              │                               ├─ v3.2+ (3h-3n)
              │                               └─ v3.x 末
              │                               │
              └───────────────┬───────────────┘
                              ▼
                          [OS M1]

* **v2.0 阶段串行(用户 2026-09-01 决定)**:v2.0 阶段 5 个版本(v2.0.0 → v2.1.0 →
  v2.2.0 → v2.3.0 → v2.4.0,粗粒度 Sprint A Stage 1/2/3 + Sprint B + Sprint C)顺序
  做完 ship,v3.0 3a-3f 等 v2.0 阶段 ship 后才启动 — 放弃原方案路径 A 的 wall-clock
  并行优化,换节奏更可控。
* **v2.x 中期/末 ‖ v3 全线异步并行(用户 2026-09-01 决定)**:v2.x M1/M2/末 跟 v3.0/v3.1/v3.2+
  各线独立推进,不强配对,各自 ship 后在 M1/M4/M11 launch 时做集成验证。
  但保留三个硬约束(per § 4):
  - v3.1 `3g → 3g.5 → 3g.7` 串行不可调换(D27)
  - v3.0 3c volatile 先 ship,再 v2.x 自写后端移植 volatile 语义
  - v3.0 3d `#[no_std]` 软 ship(M1 launch 不依赖 per D10)
```

### 1.2 sprint 层

| 阶段 | v2.x 轴 sprint | v3.x 轴 sprint | 关系 | 合流点 |
|------|---------------|---------------|------|--------|
| v1.0 后 立即 | **v2.0.0**: Sprint A Stage 1 — target dispatcher 起步(Amd64Win 完整路径 + 其他 stub + `--target` CLI) | (等待 v2.0 阶段 ship) | 串行 | — |
| v2.0.0 末 | **v2.1.0**: Sprint A Stage 2 — ABI 抽离(abi_amd64_win + abi_amd64_win_freestanding + codegen 抽离调用 + ABI 单元测试) | (等待 v2.0 阶段 ship) | 串行 | — |
| v2.1.0 末 | **v2.2.0**: Sprint A Stage 3 — spec 锁定(abi § 13 + lang-spec § 18-21 + build.md + jhyy_OS cross-check) | (等待 v2.0 阶段 ship) | 串行 | — |
| v2.2.0 末 | **v2.3.0**: Sprint B — hello-freestanding.efi 跑 OVMF(EFI struct + lld-link 链 + QEMU 启动 + printk) | (等待 v2.0 阶段 ship) | 串行 | — |
| v2.3.0 末 | **v2.4.0**: Sprint C — 多目标 dispatcher 完整化 + byte-equal 三件套(per `coordination.md § 3 D26`) | (等待 v2.0 阶段 ship) | 串行 | — |
| **v2.0 阶段 ship 后** | (v2.0 阶段完成,freestanding target + 多目标 + byte-equal 三件套就位) | **v3.0 3a-3f** 启动(inline asm / #[naked] / volatile / #[link_section] / memory barrier / 3d #[no_std] 软) | ⟂ 异步并行 | **OS M1 launch**(各自 ship 后联调)|
| v2.x 中期 | **v2.x M1-A/B + M2**: 自写 IL → .s + 确定性 regalloc + peephole + 多 target 联调 + amd64_sysv(_freestanding) | **v3.1 3g/3g.5/3g.7**(&mut + lifetime + Cap<T> + phantom 0-byte + cap 表联调) | ⟂ 异步并行(3g → 3g.5 → 3g.7 内部串行 per D27)| **OS M4 launch**(各自 ship 后联调)|
| v2.x 末 | **v2.x 末**: N 代 fixed point(N≥3)+ QBE 工具链完全移除 | **v3.2+ 3i/3j/3l**: generics(单态化)/ closures / std lib(9 模块)| ⟂ 异步并行 | **OS M11 launch**(各自 ship 后联调,真自举 OS 闭环)|

> **⟂ 符号说明**(per CLAUDE.md + `project_v2_v3_parallel_axes.md`):表示两轴**无 semver 顺序**,M1 启动前两轴各自达成即可。sprint 启动者必须显式查 v2 / v3 是否并行或顺序,不要按 semver 推论。
>
> **2026-09-01 user 决定**(本文件主要更新):
> - **v2.0 阶段串行**(v2.0.0 → v2.1.0 → v2.2.0 → v2.3.0 → v2.4.0,粗粒度 Sprint A Stage 1/2/3 + Sprint B + Sprint C):v3.0 3a-3f 等 v2.0 阶段 ship 后才启动 — 放弃原方案路径 A 的 wall-clock 并行优化
> - **v2.x 中期/末 ‖ v3 全线异步并行**:v2.x M1/M2/末 跟 v3.0/v3.1/v3.2+ 各线独立推进,不强配对 — 各自 ship 后在 M1/M4/M11 launch 时做集成验证;但**保留 § 4 三个硬约束**(3g 串行 / 3c volatile 顺序 / 3d 软 ship)

---

## § 2 共同前置

| 项 | 当前状态 | 完成定义 |
|----|---------|---------|
| v0.9 末(Stage 1 单层 byte-equal) | ✅ shipped 2026-08-11 (wip commit 2.83) | C 版 jhyy 编 src0/main.jhyy → jhyy_0 → 编 src0/main.jhyy → jhyy_1;`diff jhyy_0.il jhyy_1.il` byte-equal;regress.py 持平 baseline |
| v1.0 末(M4 hard,Stage 2 三层 N=3 fixed point) | ✅ TAGGED 2026-08-10 (commit `eabee0d`) | jhyy_1 编 src0/main.jhyy → jhyy_2;jhyy_2 编 → jhyy_3;`diff jhyy_2.il jhyy_3.il` byte-equal (sha `2445e97d...`);regress 持平 50/53 baseline;main.jhyy runtime 跑通 |

> **⚠️ 术语澄清**:`v0.9 末` ≠ `v1.0 末(M4 hard)`。v0.9 是 Stage 1 单层(jhyy_0 vs jhyy_1 byte-equal);v1.0 是 Stage 2 三层 N=3(jhyy_1/2/3 fixed point)。**v2.0/v3.0 真正硬前置是 v1.0 末(M4 hard),不是 v0.9 末** — 后者只到 Stage 1,后者进度不影响 v2.0/v3.0 启动时点。**两者皆 ✅ ship**(2026-08-10 / 2026-08-11),v2.0/v3.0 sprint 启动无编译器侧前置阻塞。

**v1.0 距 v0.9 末 plan 回顾**(per `v1.0.0 任务清单` 5 sprint 框架,2026-08-10 已 ship):
- sprint 1-2: 翻译 codegen.c / jhyy_helpers.c 主体 → jhyy_0 / jhyy_1 ✅
- sprint 3-4: 全 src0/*.jhyy 翻译 + Stage 2 三层验证(N=3 byte-equal) ✅
- sprint 5: regress.py jhyy_1 跑通 + v1.0.0 changelog 收尾 ✅

**v2.0/v3.0 总前置**:**v0.9 末 + v1.0 末(M4 hard) — 两者 ✅ ship**,sprint 启动无编译器侧前置阻塞。

---

## § 3 独立性论证

### 3.1 改动文件不重叠

| 维度 | v2.x | v3.x |
|------|------|------|
| **主改** | codegen 后端(QBE → 自写)/ target dispatcher | lang-spec + sema + codegen 单点 emit |
| **路径** | `compiler/src0/target/` + `compiler/src0/qbe/`(v2.0 启动) | `compiler/src0/sema.jhyy` + `compiler/src0/codegen.jhyy` 单点 |
| **依赖** | v0 C 端 `codegen.c` + QBE 工具链 | `jhyy-lang-spec-v1.3.0.md` + `jhyy-abi-v1.0.0.md` |

### 3.2 ABI 影响隔离

| 改动 | v2.x 影响 | v3.x 影响 |
|------|---------|-----------|
| spec 增补 | § 13(多 target ABI) | 各特性节(§ 14 / § 15 / § 16) |
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

### 5.1 路径 A: v2.0 阶段串行 + v3.0 3a-3f 异步 → OS M1

> **2026-09-01 user 决定**:v2.0 阶段 5 个版本(v2.0.0 → v2.1.0 → v2.2.0 → v2.3.0 → v2.4.0)**顺序做完 ship**,v3.0 3a-3f 等 v2.0 阶段 ship 后异步启动(不强配对,各自 ship 后在 M1 launch 做端到端联调)。

| Sprint | 内容 | 依赖 |
|--------|------|------|
| **v0.9 末** | W-001~W-009 真修 + main.c 翻译 + Stage 1 byte-equal | ✅ shipped (commit 2.83, 2026-08-11) |
| **v1.0**(5 sprint 框架) ✅ shipped (2026-08-10 tag `eabee0d`) | codegen.c / jhyy_helpers.c 翻译 + 全 src0/ 翻译 + Stage 2 三层 N=3 fixed point | v0.9 末 |
| **v1.1.0** ⟂ **v2.0.0** ✅ shipped (2026-09-02 commit `719ec25`)| lang-spec § 18-21 + abi § 13 草案(.md)/ amd64_win_freestanding target 起步(.jhyy + QBE + GCC)| v0.9 末 / v1.0 末(spec 改 .md,codegen 改 .jhyy,无冲突,可并行)|
| **v2.1.0** ✅ shipped (2026-09-03 commit `8ac3608`) | ABI 抽离(abi_amd64_win + abi_amd64_win_freestanding + codegen 抽离调用 + ABI 单元测试) | v2.0.0 |
| **v2.2.0** ✅ shipped (2026-09-03 commit `896a329`) | spec 锁定(abi § 13 + lang-spec § 18-21 + build.md + jhyy_OS cross-check) | v2.1.0 |
| **v2.3.0** ✅ shipped (2026-09-04 tag `v2.3.0` commit `54d93df`) | hello-freestanding.efi 跑 OVMF(UEFI + PE/COFF 链路验证)| v2.2.0 |
| **v2.4.0** ✅ shipped (2026-09-04 tag `v2.4.0` commit `7fb735b`) | 多目标 dispatcher + **byte-equal 三件套**(per `coordination.md § 3 D26`:`jhyy_v1.il == jhyy_v2.il` + `.s == .s` + `.exe byte-equal` 兜底 recipe per [`v2.4.0 § 2.1.1 byte_equal.sh`](../v2/v2.4.0任务清单 + 概要设计.md))| v2.3.0 |
| **v3.0 3a-3f**(⟂ 异步)⏳ 待启动 | v2.0 阶段 ship 后启动:3a inline asm / 3b #[naked] fn / 3c volatile load/store / 3e #[link_section] / 3f memory barrier / 3d #[no_std](软,任何时点做 per D10)| v2.4.0(6 特性独立,内部不强依赖;**3c 硬约束**:v2.x 自写后端在 3c ship 后才移植 volatile 语义,per § 4.2)|
| **M1 launch** | OS 编 kernel.efi + QEMU + OVMF + printk(端到端联调)| v2.0 阶段 + v3.0 3a-3c/3e-3f 全 ship(3d 软,M1 不依赖)|

**关键**:
- **v1.1.0 spec drafting 跟 v2.0.0 并行**(改 .md vs .jhyy 无冲突)— 但这是 spec 草案,不是 v3.0 特性,不算 v3 启动
- **v3.0 3a-3f 启动时点 = v2.4.0 ship 后**(不是 v1.0 末)— 节奏比原方案保守,放弃 wall-clock 并行优化,换取 v2.0 阶段节奏可控
- **v3.0 6 特性内部独立**,user 可按个人节奏穿插(双 sprint 设计者参考 § 7 实操建议)
- **保留硬约束**:v3.0 3c volatile 先 ship,再 v2.x 自写后端移植 volatile 语义(per § 4.2)

> **2026-09-04 状态更新**:v2.0 阶段 5 版本全 ship (v2.0.0 → v2.4.0, 2026-09-02 ~ 09-04, tags `v2.3.0` / `v2.4.0`, commits 719ec25 / 8ac3608 / 896a329 / 54d93df / 7fb735b);Stage 2 N=4 byte-equal closure sha `51376ce5...` re-baselined per D43;regress 104/104 PASS + 4 SKIP;hello-freestanding.efi E2E 5/5 PASS on OVMF。**v3.0 3a-3f 下一步启动**(等 user 决定);v2.x 中/末 ‖ v3 全线 异步并行(per § 5.2 / § 5.3)。

### 5.2 路径 B: v2.x 中期 ‖ v3.1 3g/3g.5/3g.7 异步并行 → OS M4

> **2026-09-01 user 决定**:v2.x 中期(M1-A/M1-B/M2)跟 v3.1 3g + 3g.5 + 3g.7 **异步并行**,各线独立推进不强配对,各自 ship 后在 M4 launch 做端到端联调。
>
> **硬约束保留**(per `coordination.md § 3 D27`):**3g → 3g.5 → 3g.7 顺序不可调换** — 3g.5 phantom 0-byte codegen 路径依赖 3g 的 codegen;3g.7 cap table 联调依赖 3g.5 锁定的 8 字节布局。**v2.x 中期内部仍串行**:M1-A → M1-B → M2(v2.x 自写后端的 windows → 多 target 联调 → sysv targets 顺序依赖)。

| Sprint | 内容 | 依赖 |
|--------|------|------|
| **v3.1 3g**(⟂ 异步)| &mut + lifetime + Cap<T> 8 规则(借用检查 + QBE 后端 emit 路径)| v2.0 末 |
| **v2.x M1-A**(⟂ 异步)| amd64_codegen.jhyy(IL → amd64 .s 主体,windows target)| v2.0 末 |
| **v2.x M1-B** | 确定性 regalloc + peephole + 跨 target(windows + sysv + freestanding)联调 | v2.x M1-A(内部串行)|
| **v2.x M2** | amd64_sysv + amd64_sysv_freestanding target | v2.x M1-B(内部串行)|
| **v3.1 3g.5** | phantom 0-byte codegen | **3g(D27 硬约束:串行不可调换)** |
| **v3.1 3g.7** | jhyy_OS cap 表 byte-equal 联调 | **3g.5(D27 硬约束)** |
| **OS M4 launch** | OS 端 Cap<T> 程序跑通(端到端联调)| v3.1 3g + 3g.5 + 3g.7 + v2.x M1-B + M2 全 ship |

**v2.x M1 拆 sprint 建议**:
- amd64_codegen.jhyy 从零写 + 指令集覆盖盘点(整数 / 内存 / 控制流 / syscall / struct sret,浮点延后 per `v2.x-qbe-rewrite § 5 挑战 2`)+ 确定性 regalloc + peephole + 多 target 联调。**历史经验**:QBE 1.0 用了 1-2 年,LLVM -g0 模式是后期才稳定;即便 jhyy 复用 QBE IL 层有优势,M1 是大特性,需分阶段 ship
- **拆法 A**(推荐):中-A 写 windows IL → .s 主体(目标 = `jhyy --target=amd64_win hello.jhyy` 产 .s 跟 C 版 QBE 字节相同)+ 中-B 加 sysv + freestanding + regalloc + peephole(目标 = 多 target 跨编 jhyy 字节相同)
- **拆法 B**(保守):中-A = windows 主体 + 中-B = sysv 主体 + 中-C = regalloc + peephole 优化
- user 后续在 v2.x 启动 L3 任务清单时定

**关键**(2026-09-01 更新):
- **v3.1 3g 跟 v2.x M1-A 异步并行**:不锁 v3.1 3g 必须先 ship;user 可双线穿插推进
- **3g.5 / 3g.7 仍串行跟随 3g**(per D27)
- **v2.x 中期内部仍串行**(M1-A → M1-B → M2):windows 主体 → 多 target 联调 → sysv targets 是技术依赖,不可异步
- **汇合点 = M4 launch**:所有 ship 后做端到端联调

### 5.3 路径 C: v2.x 末 ‖ v3.2+ 异步并行 → OS M11

> **2026-09-01 user 决定**:v2.x 末(N 代 fixed point + QBE 移除)跟 v3.2+(3i/3j/3l)**异步并行**,各线独立推进不强配对,各自 ship 后在 M11 launch 做端到端联调。

| Sprint | 内容 | 依赖 |
|--------|------|------|
| **v3.2 3i**(⟂ 异步)| generics(单态化)| v3.1 3g.7 末 |
| **v3.2 3j**(⟂ 异步)| closures | 3i(内部串行,3j 依赖 3i generics)|
| **v3.2 3l**(⟂ 异步)| std lib(9 模块)| 3i, 3j(内部串行,std lib 依赖 generics + closures)|
| **v2.x 末**(⟂ 异步)| N 代 fixed point(N=3) + QBE 工具链完全移除 | v2.x M1-B + M2 |
| **OS M11 launch** | jhyy_OS 跑 jhyy 编译器 + 编 jhyy_OS(真自举 OS 闭环,端到端联调)| v3.2 3i + 3j + 3l + v2.x 末 全 ship |

**关键**(2026-09-01 更新):
- **v3.2 内部串行**(3i → 3j → 3l,技术依赖)
- **v2.x 末 跟 v3.2+ 各线独立推进**,不强配对
- **汇合点 = M11 launch**:所有 ship 后做端到端联调

### 5.4 总里程碑节点(顺序链,无时间)

| 里程碑 | 关键节点 |
|--------|---------|
| **v0.9 末**(Stage 1 单层 byte-equal) | ✅ shipped (commits 2.22-2.83, 2026-08-11 完成) |
| **v1.0 末**(M4 hard,Stage 2 三层 N=3) | ✅ TAGGED (commit `eabee0d`, 2026-08-10) |
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
当前 (2026-09-01)
  │
  ↓ (commits 2.22-2.83)
v0.9 末(Stage 1 单层 byte-equal)✅ (2026-08-11)
  │
  ├──> OS 端可立刻开始 prep + 用 raw pointer (`*mut T` per D5) 写 kernel 源码
  │    (注:写完不编,要等 v1.0 末 + v2.0 + v3.0 3a-3c/3e-3f 全部 ship 后才能跑)
  │
  ↓ (v1.0 5 sprint 框架)
v1.0 末(M4 hard,Stage 2 三层 N=3)✅ (2026-08-10 tag `eabee0d`)
  │
  ├──> OS 端继续 prep(已写源码 + 单元测试)
  ├──> [v1.1.0 spec drafting] (跟 v2.0 A 并行,改 .md 不冲突 — 是 spec 草案非 v3.0 启动)
  │
  ↓ v2.0 阶段串行(2026-09-01 user 决定,放弃原方案路径 A 的 wall-clock 并行)
  │
  [v2.0.0 ✅] - Sprint A Stage 1: target dispatcher 起步(Amd64Win 完整路径 + 其他 stub + `--target` CLI) — 2026-09-02 commit `719ec25`
  │
  [v2.1.0 ✅] - Sprint A Stage 2: ABI 抽离(abi_amd64_win + abi_amd64_win_freestanding + codegen 抽离调用 + ABI 单元测试) — 2026-09-03 commit `8ac3608`
  │
  [v2.2.0 ✅] - Sprint A Stage 3: spec 锁定(abi § 13 + lang-spec § 18-21 + build.md + jhyy_OS cross-check) — 2026-09-03 commit `896a329`
  │
  [v2.3.0 ✅] - Sprint B: hello-freestanding.efi 跑 OVMF(UEFI + PE/COFF 链路验证) — 2026-09-04 tag `v2.3.0` commit `54d93df`
  │
  [v2.4.0 ✅] - Sprint C: 多目标 dispatcher 完整化 + byte-equal 三件套(per D26) — 2026-09-04 tag `v2.4.0` commit `7fb735b`
  │
  ↓ v2.0 阶段全 ship (2026-09-04),v3.0 3a-3f 启动(⟂ 异步并行,不强配对,等 user 决定)
  │
  [v3.0 3a-3f] (6 个 sprint, 关键路径 = 3a-3c/3e-3f;3d 软可推迟)
        - 3a inline asm
        - 3b naked fn
        - 3c volatile(硬约束:v2.x 自写后端需 3c ship 后移植 volatile 语义,per § 4.2)
        - 3e link_section
        - 3f memory barrier
        - 3d no_std(软,M1 启动不依赖 per D10,M1 后再 ship 也行)
  │
  ↓ 联调
M1 launch (OS 编 kernel.efi + QEMU + OVMF + printk)
  │
  ↓ v2.x 中期 ‖ v3.1 异步并行 → M4 launch(per § 5.2)
  ↓ v2.x 末 ‖ v3.2+ 异步并行 → M11 launch(per § 5.3)
```

---

## § 6 Branch 操作约定(axis-v2 / axis-v3 并行施工)

> **2026-09-05 校准**:v2.0 阶段全 ship 后,user 决定分 **axis-v2 + axis-v3** 两个 long-lived branch 并行施工;每轴内顺序推荐,两轴并行。Branch flow 跟 Path A(§ 5.1)对齐 — v2.0 阶段 ship 后 = Path A 的"v2.x 中/末 ‖ v3 全线异步并行"phase 启动点。

### § 6.1 Branch 命名 + Fork Point

| Branch | 用途 | Fork point |
|--------|------|-----------|
| `main` | umbrella + M1 launch 集成 | (持续存在) |
| `axis-v2` | v2 axis:v2.x M1-A → M1-B → M2 → 末(QBE 自写 / amd64_sysv / N 代 fixed point) | `main @ 7fb735b` (v2.4.0) |
| `axis-v3` | v3 axis:v3.0 3d 试水 → 3a → 3b → 3c → 3e → 3f → v3.1 3g → 3g.5 → 3g.7 | `main @ 7fb735b` (v2.4.0) |

**Branch 创建**(一次性,2026-09-05 done):
```bash
git checkout -b axis-v2 7fb735b
git checkout -b axis-v3 7fb735b
git push -u origin axis-v2
git push -u origin axis-v3
```

### § 6.2 Tag Scheme(sequential)

| Axis | Tag 序列 | 含义 |
|------|---------|------|
| **v2 axis** | `v2.5.0` → `v2.6.0` → `v2.7.0` → `v2.8.0` | M1-A (windows 后端) → M1-B (regalloc + peephole + 跨 target 联调) → M2 (sysv + sysv_freestanding) → 末 (N 代 fixed point + QBE 移除) |
| **v3 axis** | `v3.0.0` → `v3.0.1` → `v3.0.2` → `v3.0.3` → `v3.0.4` → `v3.0.5` → `v3.1.0` → `v3.1.1` → `v3.1.2` | 3d 试水 (#[no_std]) → 3a (inline asm) → 3b (#[naked]) → 3c (volatile load/store) → 3e (#[link_section]) → 3f (memory barrier) → 3g (&mut + lifetime + Cap<T> 8) → 3g.5 (phantom 0-byte) → 3g.7 (cap table) |

> **3d 试水原因**:`#[no_std]` 不动 `codegen.jhyy` 主干(只动 codegen 的 runtime emit + parser 的 `#![no_std]` attr),跟 v2 axis M1-A windows 后端起步 file 层冲突最小,branch 流程试水风险最低。
> **3d 软 ship per D10**:M1 launch 不依赖,M1 启动后合并跑集成测试即可。

### § 6.3 Rebase 节奏(每个 sub-sprint ship 前必做)

```bash
# 当前在 axis-vX 上
git fetch origin main
git rebase origin/main
# 解决冲突(罕见,因 axis 内 file 层跟 main 不重叠)
git push --force-with-lease
```

**Rebase 触发条件**(每 sub-sprint ship 前必做):
1. 另一个 axis ship 了新 tag → main HEAD 前进 → 当前 axis rebase
2. main 上有 M1 集成修复(罕见,v2.0 阶段 ship 后 main 锁) → 当前 axis rebase
3. **跨 axis 硬约束变化**(如协调 D42 / D43 / D-GUI-12 等) → 当前 axis review doc 后 rebase

**禁止**:`git rebase --force`(无 `--force-with-lease` 保护);在 axis branch 上 `git merge main`(会污染 linear history)。

### § 6.4 跨 Axis 硬约束(branch 隔离后仍要遵守)

| 约束 | 内容 | 来源 |
|------|------|------|
| **D42** | v3.0 3a inline asm 在 v2.x 自写后端完成**前**走 QBE .s 输出路径直接插入汇编(不依赖 `codegen_amd64.jhyy`);v2.x 末完成后才走自写后端 escape hatch | [coordination.md § 3 D42](../../../jhyy_OS/docs/coordination.md) |
| **3c volatile 优先** | v3.0 3c `volatile` load/store 必须**先 ship**,再 v2.x 自写后端移植 volatile 语义(避免双倍 baseline 漂移) | [v2-v3-parallel-sprint-plan.md § 4.2](#) |
| **D27** | v3.1 `3g → 3g.5 → 3g.7` 串行不可调换(phantom 0-byte 依赖 3g codegen;cap table 联调依赖 3g.5 锁定的 8 字节布局) | [coordination.md § 3 D27](../../../jhyy_OS/docs/coordination.md) |
| **D43** | 阶段性 self-equal hold:每轴内 Stage 2 N=4 byte-equal closure 是 `jhyy_N == jhyy_N+1` self-equal,**不**跨版本;v3 axis ship 改 codegen 特性 → v2 axis 后续 sub-sprint 重新 baseline | [coordination.md § 3 D43](../../../jhyy_OS/docs/coordination.md) |

### § 6.5 Self-equal Baseline(D43 阶段性 hold)

每 axis 独立维护自己的 byte-equal closure baseline:
- **v2 axis baseline** = `jhyy_N` 编 `src0/main.jhyy` 跟 `jhyy_N+1` 产出 byte-equal `.il`(自举 closure 不变,v2 axis 不依赖 v3 特性)
- **v3 axis baseline** = 每 ship 一个改 `codegen.jhyy` / `ir.jhyy` 的 sub-sprint(3a/3b/3c/3e/3f/3g 等),重新 baseline:
  - 当前 closure sha `51376ce5...`(v2.4.0 末)
  - 3d ship(不改 codegen 主干)→ closure hold ✅
  - 3a ship(改 .s emit 路径)→ 重新 baseline,新 sha X1
  - 3b ship(改 codegen fn prologue)→ 重新 baseline,新 sha X2
  - 3c ship(改 load/store emit)→ 重新 baseline,新 sha X3
  - 等等

**每 ship 必跑**:
```bash
python compiler/build/bin/regress.py                                    # 104/104 PASS 不变
python compiler/build/bin/regress.py --all --include-informational      # jhyy_v1/v2/v3/v4 byte-equal hold
./byte_equal.sh                                                         # per D26 三件套(改 .il/.s/.exe 时)
```

### § 6.6 M1 Launch 集成 Gate(双 axis ship 完毕才合并 main)

**集成 checklist**(M1 launch 前必全过):
- [ ] v2 axis:`v2.5.0` → `v2.6.0` → `v2.7.0` → `v2.8.0` 全 ship
- [ ] v3 axis:`v3.0.0` → `v3.0.1` → `v3.0.2` → `v3.0.3` → `v3.0.4` → `v3.0.5` 全 ship(`v3.1.0`+ 不要求)
- [ ] axis-v2 + axis-v3 都 rebase 到最新 main 无冲突
- [ ] 跨 axis 集成 PR:`axis-v2` → `main` + `axis-v3` → `main`(squash merge 顺序由 user 决定)
- [ ] `regress.py` 104/104 PASS + `regress.py --byte-equal` 5/5 PASS
- [ ] hello-freestanding.efi 跑 OVMF 5/5 PASS
- [ ] `jhyy_OS` 编 `kernel.efi` → QEMU + OVMF → printk 端到端联调(per `coordination.md § 0`)

### § 6.7 Batch 模式(双 axis 各开 batch,准备充分才施工)

**Batch 定义**:一个 axis 内多个 sub-sprint **串行连续** ship,中间不等待 user 中间确认(per `feedback_auto_push_after_commit`):
- L3 任务清单 + L4 详细实现方案 **批量预先铺好**(在第一波 batch 施工前)
- 每 sub-sprint ship 跑 self-equal 验证 + tag + push,无失败自动进入下一个
- 失败 / 阻塞 → 停下来报告 user,不静默跳过

**施工前准备清单**(必须全部 ready 才开 batch):
1. ✅ Branch flow setup(axis-v2 + axis-v3 都从 `7fb735b` fork 并 push)— 2026-09-05 done
2. ⏳ L3 任务清单(每 sub-sprint 一份):
   - `docs/plans/v2/v2.5.0任务清单 + 概要设计.md`(v2 axis 第一波)
   - `docs/plans/v3/v3.0.0任务清单 + 概要设计.md`(v3 axis 第一波 3d 试水)
3. ⏳ L4 详细实现方案(每 sub-sprint 一份,大 sprint 必做):
   - `docs/plans/v2/v2.5.0详细实现方案.md`(M1-A windows 后端)
   - `docs/plans/v3/v3.0.0详细实现方案.md`(3d #[no_std])
4. ⏳ § 6 Branch 操作约定(本节)— commit on main,2026-09-05 done
5. ⏳ 阶段性 byte-equal 三件套 自动化脚本就位(per D26)— `compiler/build/bin/byte_equal.sh` 已 ship v2.3.0
6. ⏳ 跨 axis 影响面分析(每个 L4 doc 必须含 § X 跨 axis 影响 + D42/3c/D27/D43 hard 约束 review)

**第一波 batch 内容**(待 user 说"开 batch"才启):
- **v2 axis batch** = `v2.5.0`(v2.x M1-A,amd64_codegen.jhyy windows 后端起步)
- **v3 axis batch** = `v3.0.0`(v3.0 3d `#[no_std]` 试水,软 ship per D10)

后续 wave(v2.6.0/v2.7.0/v2.8.0 + v3.0.1..v3.1.2)在第一波 ship 后,user 决定是否继续开 batch。

### § 6.8 Worktree 约定(per `feedback_no_subagents_for_compiler_work`)

- **sub-sprint 设计 / 实施在 axis branch 上**(不用 worktree 也行,branch checkout 即足够)
- **如果开 worktree**(如多 sub-sprint 同时筹备设计 doc),worktree 路径必须**显式指定项目内路径**(e.g. `git worktree add ../JiHuiYiYou-axis-v2-wt axis-v2`),不放在 `$TEMP` 等临时目录
- **不使用 sub-agent + worktree 自动施工**(v0.6 三个并行 worktree agent 被叫停的教训);手动 worktree OK
- **禁止** `git worktree add` 到 worktree 外的路径(branch 引用会乱)

### § 6.9 Sprint Doc 命名 + 提交规则

每 sub-sprint 必配 L3 + (大 sprint) L4 文档,在**对应 axis branch** 上提交:
- `docs/plans/v2/vX.Y.0任务清单 + 概要设计.md`(L3)
- `docs/plans/v2/vX.Y.0详细实现方案.md`(L4,大 sprint 必做)
- `docs/plans/v3/vX.Y.Z任务清单 + 概要设计.md`(L3)
- `docs/plans/v3/vX.Y.Z详细实现方案.md`(L4,大 sprint 必做)

**Commit message 风格**(沿用项目 convention):
```
feat(v2.X.0): <一句话标题>

<L3 摘要: 关键决策 + sprint 范围 + 验收标准>

Co-Authored-By: MiniMax-M3 <noreply@MiniMax>
```

**Changelog**(per `feedback_changelog_umbrella`):vX.Y axis 只 1 个 umbrella changelog,所有 patch + sub-sprint 回填到同一 changelog。

---

## § 7 实操建议(单/双 sprint 切换)

> **2026-09-01 user 决定更新**:v2.0 阶段单线串行(v2.0.0 → v2.1.0 → v2.2.0 → v2.3.0 → v2.4.0,粗粒度 Sprint A Stage 1/2/3 + Sprint B + Sprint C),不切 v3;v2.0 阶段 ship 后才进入 v2.x 中/末 ‖ v3 全线异步并行阶段(此时才有双线切换需求)。

**单人维护可考虑**:
- **v2.0 阶段**(5 个版本串行):纯 v2 单线,无 v3 并行压力;spec drafting (.md) 可跟 codegen (.jhyy) 并行穿插
- **v2.x 中/末 ‖ v3 全线异步并行阶段**:每周一半时间做 v2.x, 一半时间做 v3.x(避免 context switch 开销,具体分配按 sprint 设计者偏好);或 commit 交叉(每 v2 改 3 commit 后切 v3 改 3 commit)
- 关键: 两个轴都维持活跃, 避免一个轴停太久失活

> **⚠️ Context switch 开销**:每次切轴要重新加载 4-5 个文档(spec + abi + roadmap + 当前 sprint doc + coordination)到 LLM context。建议:每 sprint doc 加一行"本 sprint 关键文件清单"减少切换开销;**v2.0 阶段单线不切**(改后：原建议"把 v2.0.0 跟 v3.0 3a 严格串行"被本决定正式采纳,v2.0 阶段整体 ship 前不做 v3.0 3a)

**双 sprint 设计原则**:
- 每个 sprint ship 必须有独立验收标准(不互相阻塞)
- v2.x 中期 sprint ship 跟 v3.1 3g ship 验收独立(异步并行);**汇合点 = M4 launch**:v3.1 3g + 3g.5 + 3g.7 + v2.x M1-B + M2 全 ship 后做端到端联调(编 Cap<T> OS 程序 + 跑 capability 验证)
- v3.0 3d(#[no_std])集成测试单列,**可在 M1 launch 后合并跑**(软, M1 不依赖 per D10)

**节奏建议**(2026-09-01 更新):
1. v1.0 末(M4 hard)ship 后立即启动 **v2.0.0 + v1.1.0 spec drafting**(两个独立特性, 改不同文件层无冲突);v3.0 3a-3f 等 v2.0 阶段 ship 后才启动
2. v2.0 阶段 5 个版本顺序做完(v2.0.0 → v2.1.0 → v2.2.0 → v2.3.0 → v2.4.0,单线,不切 v3)
3. v2.0 ship 后, v3.0 3a-3f 启动(异步并行,不强配对;user 可按个人节奏穿插 6 特性)
4. v3.0 3d(#[no_std])放最后做, 集成测试可推迟到 M1 之后(软)
5. M1 launch 前停下 v2.0/v3.0 新 feature(3d 例外), 全员做端到端联调
6. v2.x 中/末 跟 v3.1/v3.2+ 异步并行阶段才进入 commit 切换节奏(避免一开始就并行切换)

---

## § 8 Cross-reference

| 文档 | 关系 |
|------|------|
| [v2.x-qbe-rewrite.md](v2.x-qbe-rewrite.md) | v2.x 轴权威 L1 文档(本文件是其 sprint 级细化 + 并行视角) |
| [v3.x-language-expansion.md](v3.x-language-expansion.md) | v3.x 轴权威 L1 文档(本文件是其 sprint 级细化 + 并行视角) |
| [v2.0.0-os-prep.md](../v2/v2.0.0-os-prep.md) | OS 启动链路 + 跨项目接口权威(本文件引用其 M1-M11) |
| [v1.0-self-hosting.md](v1.0-self-hosting.md) | v1.0 真闭环 L1 文档(本文件共同前置) |
| [v1.x-phase-4-m5-boot-from-scratch.md](v1.x-phase-4-m5-boot-from-scratch.md) | **M5 推迟决策**(2026-08-14) — v2.x 末 (QBE 移除) + v3.x 末 (runtime 重写) 都 ship 后, 一次性删 `src/*.c` + untrack QBE + 删 runtime.c; M5 是 v1.x 末 Phase 4 单独 sprint |
| [v1.0.0任务清单 + 概要设计.md](../v1/v1.0.0任务清单 + 概要设计.md) | v1.0 5 sprint 框架(M4 hard = sprint 3-4 末达成,本文件 § 2 + § 5.1 引用) |
| [architecture-refactor.md](architecture-refactor.md) | 整体重构 L1 文档(本文件是其 § R-6 细化) |
| [../../../jhyy_OS/docs/coordination.md](../../../jhyy_OS/docs/coordination.md) | 跨项目对齐(本文件 M1-M11 引用其决策) |

---

## § 9 Open Questions(sprint 启动前 user 决定)

> **2026-09-01 user 已决定**(本节更新):
> - **#1**(v2.0 阶段 + v3.0 是否并行):**v2.0 阶段串行**(5 个版本顺序 ship,放弃原方案 wall-clock 优化)
> - **#4**(v2.x 中期 vs v3.1 3g 优先):**异步并行无优先级**,各自 ship 后 M4 launch 汇合
> - **#5**(v1.1.0 spec drafting 并行启动):保留,**跟 v2.0.0 并行**(.md vs .jhyy 无冲突)

| # | 问题 | 建议 | 状态 |
|---|------|------|------|
| 1 | v2.0 阶段 + v3.0 是否真的并行(双 sprint 同时活跃)?还是先 v2.0 阶段全部 ship 再 v3.0? | **v2.0 阶段串行**(5 个版本顺序 ship);v3.0 3a-3f 等 v2.0 阶段 ship 后才启动(放弃 wall-clock 优化,换节奏可控)| ✅ 2026-09-01 user 决定 |
| 2 | 单人维护节奏(每天切 vs commit 切)? | **commit 切**(避免上下文切换开销);v2.0 阶段单线不切,异步并行阶段才切 | 🟡 待 v2.x 中期启动时定 |
| 3 | (2026-09-01 失效)v2.0.0 跟 v3.0 3a 不再并行,原"先 QBE → GCC 链验证"建议仍适用但**单线内**做 | v2.0.0 仍先 QBE → GCC 链验证再继续(单线内仍串行)| ✅ 仍适用 |
| 4 | M1 launch 后, v2.x 中期 vs v3.1 3g 哪个优先? | **异步并行无优先级**(2026-09-01 user 决定:两条线都疯狂往后修)| ✅ 2026-09-01 user 决定 |
| 5 | v1.1.0 spec drafting(§ 18-21)是否跟 v2.0.0 并行启动? | **并行**(spec 改 .md,codegen 改 .jhyy,无冲突);v3.0 3a 不在此并行范围(v3.0 等 v2.0 阶段 ship 后启动)| ✅ 2026-09-01 user 决定 |
| 6 | v2.x 中期"自写 IL → .s"按单 sprint 还是拆 2 sprint 估(中-A windows 主体 + 中-B sysv + regalloc + peephole)? | **拆 2 sprint**(单 sprint 范围过大;按拆 sprint 先 ship windows,后续加 target) | 🟡 待 v2.x 中期启动时定 |
| 7 | v3.0 3d `#[no_std]` 是否在 M1 launch 前必须 ship? | **否**(per `coordination.md § 3 D10` 软要求;M1 launch 不依赖;M1 启动后合并跑集成测试即可) | ✅ 已锁 |
