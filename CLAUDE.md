# CLAUDE.md — JHYY (机会翼游) 编译器项目

自研静态类型编程语言 + 自举编译器。
当前: **🟢 v4.0.19 发布**（2026-10-20，**台账 ACTIVE 桶首次清空(14 → 0)**）——
<https://github.com/JiHuiYiYou/JiHuiYiYou-compiler/releases/tag/v4.0.19>
（installer .exe + compiler .msi + vscode .vsix + SHA256.txt）。
**🟡 v4.0.20 进行中**（2026-10-24，**审计「skip test / 新增 test」的三处门修复**：
W-126 harness 的 `EXPECT-ERROR` 漏洞 / W-124 `#[no_std]` 零覆盖 / W-125 chained
`&&T` 死规则 ⇒ **200/200 PASS + 0 XFAIL + 19 SKIP**(219 total，本轮又真修 W-130 / W-133)；本机 Docker 起 daemon 后
6 个 sysv 用例本地也真跑）—— **未发布**，下一个动作 = 走发布链 + promote v4.0.0 final。
**v4.0.0 final 的 promote 条件全部满足**（184/184 生产+自举、closure v2==v3、
fixed_point 17 PASS、artifact 7 PASS、SysV 6+3、CI 全绿）。
此前 v3.4.2 / v4.0.0-rc1 / v4.0.1 / v4.0.2 / v4.0.6 五个 tag 全部发布失败，
最后一个真实 release 曾停在 2026-09-08 的 v3.2.0 —— 那段时间文档里的 "shipped"
指源码 commit，不指可安装产物；v4.0.9-rc1(2026-10-18)与 v4.0.19(2026-10-20)
先后把发布链接通。
- **v4.0.0-rc1 shipped** (2026-09-30, post-merge of `axis-v2` + `axis-v3` → main):
- **v4.0.0-rc1 shipped** (commits `a4ba8fa`..`675e7da`;tag `v4.0.0-rc1` 已打) — **v4.x 首发 RC** = v2.x FINAL (v2.16.0) + v3.x FINAL (v3.4.2) 合并入 main;QBE toolchain 完全移除 + bench.sh + .exe byte-equal D26 stage0 coverage + self-backend closure + stdlib (mem/fmt/io/math/string/vec) 落地。**🔴 2026-10-15 audit 后 blocker 未清零**(per 2026-10-10 user 决定 "所有defer/active的workaround必须在v4正式版中清零,大不了v4不发"):W-101 RESOLVED (v4.0.6 attempt #7) + W-097 RESOLVED (2026-10-15,六个 emit 根因,`closure_check.sh` PASS `v2.s == v3.s` byte-identical) + W-072 早已 RESOLVED (2026-09-09)。**索引表 ACTIVE = 14 / DEFERRED = 0**(2026-10-15 复核后修正 —— 此前写的「0」是索引重建脚本读不到 59/89 条目造成的假象,见 W-108;**2026-10-20 已降到 0 条**:W-104 / W-112 / W-114 / W-103 / W-107 / W-120 / W-105 / W-105.1 / W-118 / W-121 / W-122 / W-113 / W-115 / W-106 / W-123 先后闭合 ⇒ **ACTIVE = 0 / DEFERRED = 0** ✅),**下一个动作 = 走 v4.0.0 final 的 promote 流程**(排期见 [`version-schedule.md`](docs/plans/v4/version-schedule.md))([`active-workaround-clearance.md`](docs/plans/v4/active-workaround-clearance.md)),不是 tag final
- **v1.x 已 ship** (v1.8.3 tag `98c8272`, 2026-08-29) — Stage 2 N=4 byte-equal 闭环 + installer v1.8.3 WiX + UCPD.sys bypass。v1.x 终结。

**v4.0 阶段**:v2.x 中/末 items (QBE 自写 — 现已 in-mem self-backend 直接 x86-64 emit 完成 / amd64_sysv 实 impl — V2-B 5/5 + V2-C v2.8.0 已 ship / N 代 fixed point — v2.14.0 N≥10 已 ship) 跟 v3.x items (3a-3f OS-required: inline asm / `#[naked]` / volatile / `#[link_section]` / memory barrier / `#[no_std]` / `&mut` + lifetime) 全部走完 / dropped off-axis (per 2026-09-29 user FINAL 决定);v4.0.0-rc1 = convergence release candidate (RC 保持,不 promote final per 2026-10-10 user 决定),后续 v4.x 工作走 [`docs/plans/v4/`](docs/plans/v4/) 的当前计划 + backlog。**已 ship 实际状态**(2026-10-11 v4.0.4 plan 已 commit):v4.0.2 ACTIVE bucket → 0 (W-073 emit escape + W-074/076 arena rename + W-075 mem_set i64-store + GHA 修通);v4.0.2.1 W-074.6 sub-bug #3 partial 真修 (sema hash + 65536 + chkstk_ms);v4.0.2.2 W-096 frame blow-up;v4.0.2.3 W-098 i64 literal emit;v4.0.2.5 W-097 hoist 7-site + W-100 sret clobber 真修。**emit 类 blocker 已清零(2026-10-15)**:W-101 RESOLVED (v4.0.6 attempt #7)+ W-097 RESOLVED (2026-10-15 六个 emit 根因,`closure_check.sh` PASS,`fixed_point.sh N=5` 7 PASS / 0 FAIL / 0 INFO,N=2 起全代 byte-equal)+ W-072 早已 RESOLVED (2026-09-09)。**但 2026-10-15 audit 挖出 14 条此前从未登记的活 workaround**(W-103..W-107 / W-105.1 首批;补断言测试又挖出 W-109 浮点比较、W-110 比较串号、W-111 泛型 enum 构造器(当时记为崩溃,2026-10-18 复核不复现)、W-112 link_section no-op、W-113 asm 位置错、W-114 enum match 失效;启 Docker 跑 sysv 门再挖出 W-115 W-089 reproducer 仍崩、W-116 SysV callee 只 spill 4 个寄存器) —— 见下 §当前活跃 workarounds。**下一动作 = 走 v4.0.0 final 的 promote 流程**(2026-10-20:W-104 / W-112 / W-114 / W-103 / W-107 / W-120 / W-105 / W-105.1 / W-118 / W-121 / W-122 / W-113 / W-115 / W-106 / W-123 先后闭合 ⇒ **ACTIVE = 0**),不是 tag v4.0.0 final。OS M11 launch 路径需重新评估 (`v2.0.0-os-prep.md` + `v2-v3-parallel-sprint-plan.md` 中硬前置假设已作废并归档到 `docs/archive/v2-v3/`)。

## Reading order

按你打算做的事挑一个入口：

| 意图 | 先看 |
|------|------|
| 了解项目现在到哪、有什么限制 | 顶部 § 当前/目标 → [`workarounds.md`](docs/internal/workarounds.md)（当前限制）+ [`docs/logs/v4/changelog-v4.0.0.md`](docs/logs/v4/changelog-v4.0.0.md)（最新 ship） |
| 想看 v0.x（C 编译器）整体还有什么没完成 | [`v0.x-c-compiler-roadmap.md`](docs/plans/roadmap/v0.x-c-compiler-roadmap.md)（已 frozen） |
| 知道下一步做什么 | [`version-schedule.md`](docs/plans/v4/version-schedule.md)(**版本轴排期,入口在这**)
| 起 v4.x 新 sprint | [`active-workaround-clearance.md`](docs/plans/v4/active-workaround-clearance.md)(怎么修 + 未完成清单)→ 未启动的未来工作看 [`backlog.md`](docs/plans/v4/backlog.md) |
| 改编译器 / 排 bug | [`architecture.md`](docs/internal/architecture.md) 看模块边界 → [`build.md`](docs/internal/build.md) 看构建 + 调试坑 |
| 改语言规范 / ABI | [`jhyy-lang-spec-v1.3.0.md`](docs/abis/jhyy-lang-spec-v1.3.0.md) / [`jhyy-abi-v1.0.0.md`](docs/abis/jhyy-abi-v1.0.0.md) |
| 查 v2/v3 历史决策 | [`docs/archive/v2-v3/`](docs/archive/v2-v3/) (v2-v3-parallel-sprint-plan.md + v2.0.0-os-prep.md 已归档,2026-09-29 user FINAL 决定作废) |

## 权威文档（100% 权威）

| 文档 | 状态 | 用途 |
|------|------|------|
| [`jhyy-lang-spec-v1.3.0.md`](docs/abis/jhyy-lang-spec-v1.3.0.md) | 锁定（v1.3.0 = v1.1.0 + v1.3.x 增量）| 语言规范 + 附录 B 已知限制 + 附录 C/D/E v1.x 完整启动条件 + 历史 v1.0-v1.7 增量 |
| [`jhyy-abi-v1.0.0.md`](docs/abis/jhyy-abi-v1.0.0.md) | 锁定（v0.4/v0.5/v0.6/v0.7 实现已追更） | 类型布局 + 调用约定 + § 11.1 阻塞自举问题清单。**⚠️ 2026-10-15 修正:本文件此前称「已全部解锁」不成立** —— A3(struct 跨 FFI)从未实现,A5(浮点比较)是确证 bug(W-109),两者都没挡住自举(自举 v1.8.3 已达成),但也不能算「解锁」 |
| [`jhyy-lang-spec-floatsupplement-v3.3.0.md`](docs/abis/jhyy-lang-spec-floatsupplement-v3.3.0.md) | 锁定（v3.3.0 收编）| 浮点补充规范 — float `as` cast / fmod trunc / signed-zero semantics |

**所有 plan 文件以这两个为 100% 权威对齐**。其他 v*.* 计划文件措辞可能滞后或不准，遇到冲突以 lang-spec / abi 为准。

## 版本轴（单一 vX.Y 编号）

项目**只用版本号轴**，不再用 phase-X 两维编号。版本轴语义：

| 轴 | 范围 | 目标 |
|---|---|---|
| **v0.x** | C 编译器自身（C 端） | 编译器自举门槛达成（v0.6+）— **🟢 frozen at v1.0.0 baseline** |
| **v1.x** | jhyy 自举（`compiler/src0/*.jhyy`） | 真自举闭环（v1.0 = byte-equal `.il`）— **🟢 v1.8.3 shipped = v1.x 终结** |
| **v2.x** | QBE 完整重写 + 多目标 / 自研 OS 准备 | amd64_sysv / 多目标 / freestanding — **🟢 v2.16.0 shipped 2026-09-22 = v2.x 终结** (per 2026-09-29 user FINAL 决定;v2.x 中/末 items 全部 dropped off-axis,QBE 自写在 in-mem self-backend 里走完) |
| **v3.x** | 语言特性扩展（OS-required：inline asm / volatile / naked / no_std / `&mut` + lifetime）| 服务于 jhyy_OS — **🟢 v3.4.2 shipped 2026-09-29 = v3.x 终结** (per 2026-09-29 user FINAL 决定;v3.0 3a-3f 全部 dropped off-axis;3 个 minor v3.4.0/1/2 ship 走完 W-085/W-088/W-089 真修,ACTIVE workaround bucket 清空) |
| **v4.x** | 后合并 axis — stdlib / 0-C 闭环 / async / lifetime / trait / package manager / multi-arch / `.jhyynb` | 服务于编译器自身现代化 + jhyy_OS 重启评估 — **🟡 v4.0.0-rc1 shipped 2026-09-30 = v4.x 首发 RC** (axis-v2 + axis-v3 merge 入 main;**ACTIVE 已清零 → v4.0.0 final 可 promote**(余下 promote 条件见 `active-workaround-clearance.md` § 全局 ship gate);其余 12 项未启动,合并在 [`docs/plans/v4/backlog.md`](docs/plans/v4/backlog.md)) |

**轴之间的关系**（关键，避免误读 semver）：
- **v0.x → v1.x**：严格顺序（v1.0 强前置 v0.x 全部完成）✅
- **v1.x → v2.x / v3.x**：严格顺序（v2.0 / v3.0 sprint 3a 强前置 v1.0 真自举闭环）✅ v1.0.0 已 ship
- **v2.x + v3.x → v4.x**：v4.0 = v2.x + v3.x 合并入 main;v4.x 内部按依赖图决定串并行(强串行链 `lifetime → closure → dyn Trait → HKT`;M5 / async / 错误恢复 / 优化 / 包管理 / 并发 cap / `.jhyynb` 可并行)—— 详见 [`backlog.md`](docs/plans/v4/backlog.md) 依赖图
- **v4.x 中/末 items** (M5 0-C 闭环 / async / lifetime / trait / package manager / multi-arch / `.jhyynb`) 全部规划在 [`backlog.md`](docs/plans/v4/backlog.md),**一项都未启动**

> v1.x = jhyy-side production（v1.4.4 物理 flip `jhyy.exe` 为 jhyy-side binary）；v1.4.6 真修 3 个 ACTIVE workaround（W-017 codegen module-level `let mut` + W-019 codegen nested struct field chain + W-020 parser inline match-as-expression reorder）后，src0 production 无外部 C runtime helper 依赖（除 `jhyy_helpers.c` DEPRECATED 状态保留 1-2 sprint 观察期）+ parser / codegen 跨侧行为对齐。ACTIVE workaround 数 → 0。

历史 phase-X 措辞在新 sprint 文档里不再使用；如在旧 sprint / changelog / spec 里看到 phase-N 编号，按下表对应：phase-1 ≈ v0.x / phase-2 ≈ v1.x / phase-2.5 ≈ v2.x / phase-3 ≈ v3.x / phase-4 ≈ v4.x。

## v4.0.0-rc1 — sprint 详情(历史记录)

> 本节是 rc1 ship **当时**的门结果,数字以当时为准(如 158/158 是 rc1 的基线,
> 当前实测 162/162 + 23 SKIP)。当前状态看顶部 §v4.0 阶段 与 §当前活跃 workarounds。

**v4.0.0-rc1 任务清单**:[`docs/plans/v4/v4.0.0-plan.md`](docs/plans/v4/v4.0.0-plan.md) ✅ **shipped 2026-09-30 as RC** (Gate 3 self-host src0/main.jhyy deferred per 2026-09-30 user 决定;v4.0.0 final 待 v4.0.1 真修 multifn 后)

**v4.0.4 next-sprint plan**:[`docs/plans/v4/v4.0.4-plan.md`](docs/plans/v4/v4.0.4-plan.md) ✅ **已完成 2026-10-15**(W-101 attempt #7 成功 2026-10-12;W-097 六个 emit 根因 2026-10-15 真修,闭环达成)。本 plan 声明 fix scope = emit_call/emit_load dst temp record path —— **实际根因是 emit 层六个独立缺陷的组合**(alloc 池起点 / 助记符分派 or⊃xor / 比较宽度 / 指针返回 extern 识别 / emit_load / emit_store),plan 的 fix scope 判断有误,详见 `docs/internal/workarounds.md` W-097 RESOLVED section。

**核心动作**:
1. `git merge --no-ff axis-v2` → commit `a4ba8fa` (v2.16.0 axis final 整合)
2. `git merge --no-ff axis-v3` → commit `c13397d` (v3.4.2 axis final 整合;含 stdlib + 新 codegen arch)
3. `chore(version)` → commit `c473246` (22 文件 v2.16.0 → v4.0.0-rc1)
4. `docs(archive)` → commit `b1cf522` (`docs/plans/roadmap/v2-v3-parallel-sprint-plan.md` + `docs/plans/v2/v2.0.0-os-prep.md` → `docs/archive/v2-v3/`)
5. `docs(readme)` → commit `3a48fdd` (432 → 363 行 v4-aligned 重写)
6. `fix(regress)` → commit `3d41d03` (regress.py parents[2] → ROOT const post-repo-root relocation)
7. `fix(bench)` → commit `bc3a2cc` (bench.sh JHYY default path → git rev-parse post-axis-v2 drop)
8. `docs(changelog)` → commit `675e7da` (umbrella `docs/logs/v4/changelog-v4.0.0.md` 标 v4.0.0-rc1 + v4.0.1-plan.md NEW)
9. tag `v4.0.0-rc1` + branch cleanup (`axis-v2` / `axis-v3` 删除)

**验证门** (per v4.0.0-plan.md lines 62-67):
- ✅ regress.py (C-side `jhyy.exe`) 158/158 PASS + 22 SKIP (sha `4fd068d8...`)
- ✅ regress.py (`--binary=jhyy_v1.exe.exe`) 158/158 PASS + 22 SKIP parity (sha `766c96cc...`)
- ❌ `jhyy_selfhost_check` N≥3 byte-equal — **deferred to v4.0.1** (pre-existing W-074.6 multifn silent fail;non-regression)
- ❌ D43 final baseline freeze — **deferred to v4.0.1** (same root cause)
- ✅ `byte_equal_selfbackend.sh` 6/6 PASS (3 .s sha-mnemonic + 3 .exe exit)
- ✅ `bench.sh --report` first-time baseline (fib 1.399x / ack 0.596x / nq 1.020x;fib > 1.1x accepted per report-mode)
- ✅ ACTIVE workaround count = 0 (per v3.4.2 ship state)

**5/7 门 ✅ + 2/7 门 ❌ deferred** — 见 changelog 详细 RCA。

## 文档索引

### 路线图 + Sprint

| 层级 | 文档 | 状态 |
|------|------|------|
| L1 | [`v0.x-c-compiler-roadmap.md`](docs/plans/roadmap/v0.x-c-compiler-roadmap.md) | **已完成**（C 编译器演进到自举门槛，v0.9 wip commit 2.83 收尾）|
| L1 | [`v1.0-self-hosting.md`](docs/plans/roadmap/v1.0-self-hosting.md) | **v1.0.0 完成**（2026-08-10 tag `eabee0d` — Stage 2 N=3 byte-equal 闭环）|
| L1.5 | [`v2.x-qbe-rewrite.md`](docs/plans/roadmap/v2.x-qbe-rewrite.md) | **v2.16.0 完成**（2026-09-22 — QBE 移除 + bench.sh + .exe byte-equal）|
| L1 | [`v3.x-language-expansion.md`](docs/plans/roadmap/v3.x-language-expansion.md) | **v3.4.2 完成**（2026-09-29 — 3 个 minor v3.4.0/1/2 ship 走完 W-085/W-088/W-089 真修）|
| L1 | [`v4.x-post-merge.md`](docs/plans/roadmap/v4.x-post-merge.md) | **v4.0.0-rc1 完成**（2026-09-30 — axis-v2 + axis-v3 合并入 main;Gate 3 selfhost deferred → v4.0.1）|
| L1.5 | [`v2-v3-parallel-sprint-plan.md`](docs/archive/v2-v3/v2-v3-parallel-sprint-plan.md) | ⚠️ **SUPERSEDED** — 已归档到 [`docs/archive/v2-v3/`](docs/archive/v2-v3/) (per 2026-09-30 v4.0.0 archive step) |
| L3 | [`docs/plans/v4/active-workaround-clearance.md`](docs/plans/v4/active-workaround-clearance.md) | ✅ **已完成(2026-10-20)** —— ACTIVE 桶清零(14 → 0);文档保留作审计轨迹 |
| L3 | [`docs/plans/v4/backlog.md`](docs/plans/v4/backlog.md) | 12 项未启动的未来工作(原 v4.1.0 - v4.12.0 合并,2026-10-15) |

最近完成的 sprint: **v4.0.0-rc1 shipped 2026-09-30** — axis-v2 + axis-v3 merged into main。

下一阶段: **v4.0.0 final 的 promote + 发布**(见 [`active-workaround-clearance.md`](docs/plans/v4/active-workaround-clearance.md))→ 然后才谈 promote v4.0.0 final。backlog 那 12 项无优先级,不抢这条线。

**plan 命名约定(2026-10-15 修订)**:已 ship / 进行中的 sprint 保留 `v4.X.Y-plan.md`(审计轨迹,改名会破坏跟 changelog / commit 的对应);未启动的 backlog 与进行中的工作用描述性文件名,**不用版本号** —— 版本号在启动时才分配。
历史: changelog 见 `docs/logs/v0/changelog-v0.X.Y.md` (C 编译器) + `docs/logs/v1/changelog-v1.X.Y.md` (jhyy 自举) + `docs/logs/v2/changelog-v2.*.0.md` (QBE rewrite + freestanding) + `docs/logs/v3/changelog-v3.*.md` (language expansion + self-backend) + `docs/logs/v4/changelog-v4.0.0.md` (post-merge umbrella);早期 sprint（命名 `sprint-1*.md`）同目录。

### 项目内部（`docs/internal/`）

- [`build.md`](docs/internal/build.md) — 编译 / 运行 / **self-backend 坑（Windows 独有）**
- [`architecture.md`](docs/internal/architecture.md) — 流水线 / 模块 / 设计细节 / **self-backend codegen 速查** / Stage 0 自举
- [`conventions.md`](docs/internal/conventions.md) — 编码约定 / 文件命名 / 提交规则
- [`tests.md`](docs/internal/tests.md) — 集成测试清单 + 运行方法
- [`workarounds.md`](docs/internal/workarounds.md) — W-NNN workaround 台账（**ACTIVE = 0** ✅ 见下方 §当前活跃 workarounds）

### 语言规范 & ABI（`docs/abis/`，locked）

- [`jhyy-lang-spec-v1.3.0.md`](docs/abis/jhyy-lang-spec-v1.3.0.md) — 语言规范（v1.3.0 锁定 = v1.1.0 + v1.3.x 增量 + v3.3.0 float 补充合并）
- [`jhyy-abi-v1.0.0.md`](docs/abis/jhyy-abi-v1.0.0.md) — ABI 白皮书（struct pass-by-value / 多文件 / FFI / break-continue / 切片 / 命名空间）
- [`jhyy-lang-spec-floatsupplement-v3.3.0.md`](docs/abis/jhyy-lang-spec-floatsupplement-v3.3.0.md) — 浮点补充（已合并入 v1.3.0 spec 附录）

### 历史归档（`docs/archive/`，不再使用）

- [`v2-v3/v2-v3-parallel-sprint-plan.md`](docs/archive/v2-v3/v2-v3-parallel-sprint-plan.md) — **SUPERSEDED 2026-09-29** v2/v3 并行 sprint 调度（v4.0.0 archive 后保留）
- [`v2-v3/v2.0.0-os-prep.md`](docs/archive/v2-v3/v2.0.0-os-prep.md) — **SUPERSEDED 2026-09-29** OS × compiler 跨边界 M1-M11 硬前置（v4.0.0 archive 后保留）

## 工作风格

工具链与构建见 [`build.md`](docs/internal/build.md);编码约定、项目结构、改动后必跑基线见 [`conventions.md`](docs/internal/conventions.md)。

## 当前活跃 workarounds

**0 ACTIVE / 1 DEFERRED**(2026-10-25 —— ACTIVE 仍为 **0**;2026-10-20 曾清零 14 → 0,清零过程:**W-104 RESOLVED**(v4.0.12 —— ≤16B eightbyte 分类 + >16B MEMORY class 整体落栈,与 gcc 三方向对拍全绿);**W-114 RESOLVED**(v4.0.14 —— enum 的 ABI 两侧统一:参数按地址传、返回值走 sret、调用结果是 8 字节指针;顺带修了 **W-119**:SysV 帧布局把第 0 号局部变量放在 `0(%rbp)` = 覆盖旧 rbp);**W-112 RESOLVED**(v4.0.16 —— `#[link_section]` 的 `.section` 之前被插进 link 路径的副本,磁盘上的 .s 里没有);**W-103 RESOLVED**(v4.0.16 —— `std_os_*` 五个 mock 接真 libc bridge;顺带把 POSIX/Win 的 `O_*` flag 差异在桥这一层翻译掉 —— **Windows 的 `_O_CREAT`=0x100 不是 POSIX 的 0x40**,mock 从不调 `open(2)` 所以这错一直藏着;并让 std lib **第一次真的可被用户代码 import**(`import os;` 两级查找:main 文件旁边 → std lib 目录)),测试从 inline 副本改成 import 真身),**W-107 RESOLVED**(v4.0.17 —— 五张 per-fn 表改成**按实际函数数**分配,固定上限 4096 与「太多函数」的响亮守门一并删除,**没有上限了**;顺带挖出并修掉 **W-120**:temp 表的 65536 上限会让**越界静默算错值** —— 修 W-107 会暴露它,两者必须一起做),**W-105 + W-105.1 RESOLVED**(v4.0.18 —— (a)「`&mut` 真的能用」(v4.0.15)+ (b)**最小独占检查**(同作用域内双 `&mut` 互斥)落地;`check_borrow` / `check_cap_pass` 两个「恒 return 1 的假装会检查」函数都删掉了。**上一版 (b) 失败的真根因是 W-107**(per-fn 表的固定上限:那次尝试加了几个顶层函数把 main.jhyy 推过 1024 → 被丢弃的函数帧算成 8 字节 → 「帧偏移 ≈ -515KB 的写」),W-107 改成按实际函数数分配后阻塞自然消失),**W-118 RESOLVED**(v4.0.18 —— 语言 lexer 的 `lex_peek_char` 加 EOF 守卫;**防御性**修复:这条从来没观测到危害,只是把「EOF 是隐式的」变成显式的),顺带挖出并修掉 **W-121**(合成 closure 的符号名取自**节点堆地址** ⇒ ASLR ⇒ **同一编译器连编两次 `.s` 就不同**,产物不可复现;改用计数器)和 **W-122**(四个 side-file 用**固定路径** ⇒ 上一次编译的内容泄漏到下一次 —— `--no-link` 批量编译后紧接 `make` 会用 no_std 的链接行链一个正常程序 ⇒ 整个 build 挂掉),**W-113 RESOLVED**(v4.0.18 —— `asm!` / `fence_*` 的文本经 IL(`dbgasm <hex>`)**内联进函数体**;之前是 append 到 .s 末 = 落在所有函数之外 = **死字节** —— 连**内存屏障都从来没执行过**;`asm_before_ret` 从 KNOWN-FAIL 升级成真门),**W-115 RESOLVED**(v4.0.18 —— W-089 的 reproducer 之所以 STACK_OVERFLOW,根因**不是** W-089:是那个 8-subtest 里的**闭包捕获了外层变量** —— 闭包捕获在 v3.2.1 的 MVP 范围里明确不支持,但编译器**没有任何检查** ⇒ 给它生成坏代码(env 压根没传进合成 fn)⇒ 运行时炸。现在**编译期明确报错** ✓,reproducer 已转 PASS(EXIT=0)——「W-089 已 RESOLVED」这句话**现在有证据支撑**了),**W-106 RESOLVED**(v4.0.19 —— 那处「每次 symbol lookup 白造一个 StringBuilder」的
死存储删掉了:它注释里的理由(「逼 codegen 物化栈帧」)**早就被证伪**(删不删栈帧都
完整物化);而 2026-10-18 那次「删掉它 ⇒ 偶发失败 ⇒ 它承重」的对照实验**归错了因** ——
真凶是 **W-123**(`jh_mktemp_ascii` 的 seed = `pid ^ tid ^ ctr`,而 Windows 的 pid
与主线程 tid 来自**同一个全局计数器** ⇒ `N ^ (N+1) = 1` ⇒ **每两个并发进程就撞一次
同一个临时文件名** ⇒ 一个的 rename 失败 ⇒ **编译失败**。W-123 修好后:并发编译 32 个
→ **0 失败**(修复前 4 个)),**0 ACTIVE / 123 索引行**(DEFERRED 1 条 = W-134.1;2026-10-25 登记),per `docs/internal/workarounds.md` 索引表):

| W-NNN | 位置 | 性质 |
|-------|------|------|
| W-105 | — | ~~`&mut` 独占性完全不检查~~ ✅ **2026-10-20 已修**:(a)「`&mut` 真的能用」+ (b)**最小独占检查**(同作用域内双 `&mut` 互斥,新测试 `borrow_mut_conflict.jhyy` EXPECT-ERROR ✓)。词法作用域(borrow 提前结束会误报)—— 完整 NLL/Polonius 留 backlog v4.3.0 |
| W-103 | — | ~~`std_os_open/close/read/write` 全是 M0 mock,`std_os_exit` 不退出进程~~ ✅ **2026-10-20 已修**:5 个 libc bridge 进 `jhyy_helpers.c`;`import` 加 std lib 目录回落 → 测试改 import 真身(新增 `std_os_exit.jhyy` 验进程真退出) |
| W-107 | — | ~~五个 per-fn 表按固定上限分配~~ ✅ **2026-10-20 已修**:改成**按实际函数数**分配(`fn_count + 1`),`MAX_FN_ENTRIES` 常量删除、「太多函数」守门删除 —— **没有上限了**。之前那次动态分配被撤回,是因为「查表上界」那另一半真修还没落地(两者从未同时存在);这次两半齐了 |
| W-120 | — | ~~temp 表(65536)越界 → 静默算错值~~ ✅ **2026-10-20 已修**:两张按 temp id 索引的表改成按**实际最大 temp id** 分配 + 越界**响亮失败**。**HEAD 上本来就可复现**(一个 25000 语句的函数就够:算出 s=0,正确值 74994)。`main.jhyy` 自己的 max temp id 已到 64953 —— 离越界只剩 583 |
| W-106 | — | ~~死存储改栈布局~~ ✅ **2026-10-20 已修**:那处「每次 symbol lookup 白造一个 StringBuilder」删掉了。它注释里的理由**早就被证伪**;而当年「删掉它 ⇒ 偶发失败 ⇒ 它承重」的对照实验**归错了因** —— 真凶是 **W-123** |
| W-123 | — | ~~临时文件名 seed = `pid ^ tid ^ ctr` 会规律性碰撞~~ ✅ **2026-10-20 已修**:乘法混合 + 独占创建(CREATE_NEW)重试。并发编译 32 个 → **0 失败**(修复前 4 个) |
| W-112 | — | ~~`#[link_section]` 是 no-op~~ ✅ **2026-10-20 已修**:`.section` 之前被插进 link 路径的**副本**(`temp_asm`),磁盘上的 .s 和 `--no-link` 产物里都没有 → 现在 .s 产出后立刻对 `asm_path` 处理一次 |
| W-113 | — | ~~`asm!` / `fence_*` 的字节被 emit 到 `ret` 之后,永不执行~~ ✅ **2026-10-20 已修**:文本经 IL(`dbgasm <hex>`)内联进函数体;`asm_before_ret` 升级成真门 |
| W-115 | — | ~~W-089 的 reproducer 仍 STACK_OVERFLOW~~ ✅ **2026-10-20 已修**:根因是**闭包捕获外层变量**生成坏代码(不是 W-089)⇒ 现在编译期明确报错;reproducer EXIT=0 ✓ |
| W-105.1 | — | ~~`check_cap_pass` 同款 stub~~ ✅ **2026-10-20 已修**:它**连一个调用点都没有** → 函数 + 那 16 行「已知限制」注释一并删掉,原位置留「将来要做什么」的清单(零行为变化) |
| W-118 | — | ~~语言 lexer `lex_peek_char` 无 EOF 守卫~~ ✅ **2026-10-20 已修**:`Lexer` 加 `end` 字段 + 两个 peek 加守卫;A/B 证明 `.s` 逐字节不变(193/193)。**防御性**修复 —— 这条从来没观测到危害 |
| W-121 | — | ~~合成 closure 的符号名依赖堆地址 ⇒ 产物不可复现~~ ✅ **2026-10-20 已修**:改用每次编译单调递增的计数器(同一编译器连编三次 `.s` 现在逐字节相同) |
| W-122 | — | ~~四个 side-file 用固定路径 ⇒ 泄漏到下一次编译~~ ✅ **2026-10-20 已修**:每次编译开头先删干净(`version-schedule` § D3 记的「机制成立但未观测到发作」—— 今天发作了) |

**2026-10-24 追加(v4.0.20 —— 审计「skip test / 新增 test」挖出的三处;ACTIVE 仍是 0,
三条全是 RESOLVED)。** 三条都是**门**的问题 —— 门绿着,但它没在验它声称在验的东西:

| W-NNN | 性质 |
|-------|------|
| W-126 | ~~regress harness 的 `EXPECT-ERROR` 漏洞:编译**意外成功**时判 PASS~~ ✅ **2026-10-24 已修** —— `expect_error_kw` 只在「编译失败」分支被检查 ⇒ 编译成功时落到「只要进程没崩就算过」的分支。**8 个 expect-error 测试(含 `borrow_mut_conflict` / `closure_capture_unsupported` 两道最新门)全部不会变红**。修法:`rc == 0` 且有 EXPECT-ERROR ⇒ FAIL(探针当场由绿转红) |
| W-124 | ~~`#[no_std]` 零覆盖~~ ✅ **2026-10-24 已修** —— (a) 链接行写 `-Wl,--entry=main_jhyy`,而 codegen 按函数名原样发符号(用户的 `fn main` → `main`)⇒ **no_std 程序 100% 链不过**;(b) harness 只认 `fn main_jhyy` ⇒ `no_std_hello.jhyy` 被当「library」**静默跳过** ⇒ v3.0 的 ship gate 从没跑过。修法:链接行 = `-nostartfiles -nodefaultlibs -Wl,--entry=main -lgcc`(`-lgcc` 提供 `___chkstk_ms`,不含 C 运行时)+ harness/审计认 `#[no_std]` 的 `fn main` 入口 ⇒ **EXIT=42** ✓。⚠️ `#[no_std]` 用例**串行**跑(side-file 固定路径的并发互踩,根因见 W-122 余量) |
| W-125 | ~~chained `&&T` 的报错路径:sema 那条规则是死代码~~ ✅ **2026-10-24 已修** —— lexer 把 `&&` 切成一个 token,而 `parse_type` 只认单 `&` ⇒ 报「expected type name, got &&」(对用户毫无意义)⇒ sema 里那条「chained `&&T` not allowed」**永远走不到** ⇒ `borrow_check_err.jhyy` 长期挂 XFAIL,而那个 XFAIL **从未登记进台账** ⇒「台账 ACTIVE=0」与「套件自报 1 个已知失败」长期并存。修法:parser 显式拦 `&&` + 措辞对齐 sema ⇒ **套件 XFAIL 1 → 0** |

**2026-10-24 追加(v4.0.20 —— 修 v4 ABI / spec 时顺带挖出的五处;**W-130 与 W-133
是真修**,W-127 / W-128 / W-129 同期修完)。**

| W-NNN | 性质 |
|-------|------|
| W-127 | ~~Windows 目标整数 / 浮点实参寄存器编号不自洽~~ ✅ **2026-10-24 已修** —— MS x64 的整数与浮点实参**共用一个位置计数器**(RCX/RDX/R8/R9 ‖ XMM0-3),旧实现给浮点单独计数 ⇒ 浮点参在前时整数参读错寄存器。修法:`emit_amd64_arg_regs` 里 Windows 目标下整数位置按 `ri` 走、浮点走独立 XMM 计数 |
| W-128 | ~~`0o` / `0b` 字面量静默算成 0~~ ✅ **2026-10-24 已修** —— lexer 认前缀,但求值走 `strtoll(base=0)` ⇒ `0o17` / `0b101` 算成 0。修法:新增 `parse_int_literal` 按前缀分派(base 8 / base 2),base-0 路径不变 |
| W-129 | ~~`alignof(T)` 表达式无类型~~ ✅ **2026-10-24 已修** —— sema 里**只有** `NODE_SIZEOF` 分支、没有 `NODE_ALIGNOF` 分支 ⇒ `alignof` 走不到任何类型 ⇒ 报「type mismatch in let」。修法:两个分支**合并成一个**(data accessor 布局相同),值走 `type_align` |
| W-130 | ~~address-holder bitmap 的**容量**在 C 桥接层与 jhyy 侧脱节~~ ✅ **2026-10-24 已修** —— C 侧 `jh_cgstate_set/get_holds_flag` 把 `idx >= 65536` **硬编码**拒绝,而 jhyy 侧已把同一张 bitmap 动态扩到 `max_temp_id + 4096`(可 > 65536)⇒ temp id ≥ 65536 的 address-holder 标记写不进去 ⇒ `emit_loadsub` 退化成「读栈槽里指针的低字节」⇒ **编译器自己的 `--target=` 前缀判定失效**(9 字节前缀比较正好走字节读)。数字闭合:好产物里最高间接字节读 base temp = 65477(距悬崖 59);+W-127(+18)/+W-128(+50) 都还 OK,**+两者(+68)→ 65545 ≥ 65536 ⇒ 坏**。修法:C 侧加**容量通道**(`jh_cgstate_set_holds_table(bitmap, cap)` 原子装指针 + 容量,越界返 -1 哨兵)+ jhyy 侧**粘滞标志 + 编译末尾响亮失败** + 3 道常驻门(`artifact_checks.sh` 的 holds_cap_source / holds_bitmap / selfhost_target_flag) |
| W-133 | ~~`==` / `!=` 对 `struct` / `enum` / 数组是**身份比较**(比地址)不是值比较~~ ✅ **2026-10-24 已修** —— sema 对比较运算符**零类型约束** + `qbe_type_of` 对聚合无分支(默认 `'w'`)⇒ `ceqw` 比的是两个**槽地址的低 32 位** ⇒ 字段完全相同的两个 struct 判 `false`。修法:新增 `cg_value_eq`(struct 逐字段递归 / enum 比 tag + 按变体类型比 payload / 数组逐元素 / slice 比头)+ sema 拆两支(聚合必须同类型;大小比较编译期报错;调用结果报错)+ **顺带真修标量浮点 `==` 的 NaN 语义**(`ucomisd` + 纯 `setcc` 只读 ZF ⇒ unordered 时分不清「相等」⇒ `NaN == NaN` 恒为 true(错);现在加 `setnp`/`setp` 有序守卫) |
| W-133.1 | **SUPERSEDED** —— 聚合 `==` 不接受**函数调用结果**作为操作数(设计如此:编译期明确拒绝不安全形态,不是待修的 bug ⇒ 不占高优桶)(聚合返回值在 ABI 下不统一是地址:>16B 走 sret 是地址、≤16B 走寄存器 ⇒ 按地址比会读到寄存器里的头几个字节)。`let a = make_p(1); a == b` 里的 `a` 是变量 ⇒ 不报错 |
| W-133.2 | **SUPERSEDED** —— 聚合的**大小比较**(`<` `>` `<=` `>=`)未实装 ⇒ 编译期报错(聚合没有语言级的自然全序;修前静默比地址)—— 同上,设计如此不入高优桶 |
| W-133.3 | **SUPERSEDED** —— struct 字面量的字段值类型必须**精确匹配**字段类型(整数字面量默认推断为 `i32` ⇒ `u8` 字段配 `7` 报 `field type mismatch`;须先写 `let c: u8 = 7;`)—— 同上,设计如此不入高优桶 |
| W-134 | ~~MCP pytest 套件里有一个**恒红**的陈旧测试~~ ✅ **2026-10-25 已修** —— `test_regress_baseline_drift_detection` 断言「sha 漂移 ⇒ 报 binary drifted」,但那个行为已被上一轮 commit `f72cef4` 刻意换成「binary 比源旧」的新鲜度检查 ⇒ **从那次起套件就是红的**,而 CI 从不跑 pytest ⇒ 没人发现。修法:拆成两条 —— `test_regress_sha_drift_is_not_fatal`(漂移**不**误报)+ `test_regress_stale_binary_detected`(binary 比源旧 ⇒ early_abort `older than source`)。**套件 40 passed / 1 skipped / 0 failed** |
| W-134.1 | **DEFERRED** —— `mcp-jhyy/tests/`(41 个测试)在 CI 里**零覆盖**(`ci.yml` 没有 pytest step,也没有任何 `pip install`)⇒ 套件红绿都不影响 CI 结论。补 CI step 需要**第一个网络依赖**(fastmcp / pytest / pytest-asyncio),而本机 MSYS2 python 连 pip 都没有 ⇒ 命令**无法本地验证** ⇒ 建议单独一个 commit + 先在 PR 分支观察一轮 |

**回归现状(2026-10-24 实测,本轮真修后):200/200 PASS + 0 XFAIL + 19 SKIP(219 total)**
(本日早些时候 —— W-126 / W-124 / W-125 修完时 —— 是 186/186 + 0 XFAIL + 19 SKIP / 205 total;
再往前 184/184 + 2 XFAIL + 20 SKIP / 203 total)。本机 Docker Desktop 起 daemon 后
`regress.py --cross=auto` 解析成 **docker** ⇒ **7 个** sysv 用例本地也真跑
(exit=28/217/42/35/18/42/170 全对 —— 新增 `sysv_mixed_int_float`)。
`closure_check.sh` PASS(v2.s == v3.s 逐字节)、`fixed_point.sh` 17 PASS / 0 FAIL
(N=10 .il 与 .s 跨代 byte-equal)、`artifact_checks.sh` 12 PASS / 0 FAIL
(含 W-130 新增 3 道门)、`audit_test_assertions.py --strict` 0 违规。

**回归现状见下方「v4.0.20 真修批次」—— 数字已更新到 200/200 + 0 XFAIL / 219 total。**

2026-10-18 调整(**W-109 移出、W-118 移入,总数仍 14**):W-109(IL lexer 缺浮点比较
助记符)已于 2026-10-17 真修(`codegen_amd64_lexer.jhyy:1588` 的 `c*` gate 漏第二字符
`l`),台账状态 RESOLVED,但本表此前仍列着它 —— 这是既有陈旧,不是本次引入。
W-118 是同一天做 W-117 RCA 时发现的**另一处**同款缺陷(`lex_peek_char` 同样无守卫,
但 `lex_next_char` 读到非 0 垃圾会照常推进,所以是越界前进而不是空转)。
**计数以 `docs/internal/workarounds.md` 的脚本生成索引表为准**,不要数正文状态行
——104 个条目里只有 35 行是可解析的 `**状态:**` 格式(W-108 同源问题)。
索引本身也漏 2 条(W-025 / W-070,二者都是 RESOLVED 故不影响 ACTIVE 计数:
前者有 "follow-up" H3 打乱解析,后者的状态行还带 `✅` 前缀且日期格式不合 schema)。

排序、修法、验收 gate 见 [`active-workaround-clearance.md`](docs/plans/v4/active-workaround-clearance.md)。

**⚠️ 这几条为什么以前「看不见」:** 两个独立原因,都已修。

1. **索引重建脚本读不到**(W-108):`STATUS_RE` 不容忍状态行里的 `✅` 前缀
   (59 条被静默丢弃),且只匹配 H2 而 9 条挂在 H3 下 —— 索引 16 行 vs 台账 96 条。
   **「索引表 0 ACTIVE」从来不是「没有 ACTIVE」,是「读不到」。**
2. **回归测试本身不验证结果**:harness 只比退出码,stdout 从不参与判定。
   166 个可跑测试里 **53 个(32%)零信号** —— 6 个有 `// EXPECT:` 但数学上不可能
   失败,47 个只验「进程没崩」。W-109 就是这么活到今天的。详见
   [`docs/internal/tests.md`](docs/internal/tests.md) 与
   `scripts/dev/audit_test_assertions.py`。

查状态时回源码 `file:line` 复核,不要只信索引或「N/N PASS」。

**已 RESOLVED 的一批:**

- W-072 → RESOLVED (2026-09-09, v3.1.4)
- W-097 → RESOLVED (2026-10-15, v4.0.8,六个 emit 根因 → 自举闭环达成)
- W-098 / W-099 / W-100 / W-101 → RESOLVED (2026-10-09 ~ 2026-10-12)
- W-102 → RESOLVED (2026-10-15, address-holder 池与 alloc 池重叠 → self-hosted 编译器泛型 SEGV)
- W-074.6 → RESOLVED (2026-10-15,原 DEFERRED;所等的 W-096 / W-097 均已 RESOLVED)
- W-104 → RESOLVED (2026-10-20, v4.0.12 —— SysV struct 传参:≤16B eightbyte 分类 + >16B MEMORY class 整体落栈,与 gcc 三方向对拍一致)
- W-114 → RESOLVED (2026-10-20, v4.0.14 —— enum ABI 两侧统一:参数按地址、返回值 sret、调用结果 8 字节;顺带修了 W-119 的 SysV 帧布局)
- W-103 → RESOLVED (2026-10-20, v4.0.16 —— `std_os_*` 接真 libc bridge;POSIX/Win 的 `O_*` flag 差异在桥这层翻译;`import` 加 std lib 目录回落 → std lib 第一次真的可被用户代码 import)
- W-107 → RESOLVED (2026-10-20, v4.0.17 —— 五张 per-fn 表按实际函数数分配;新增常驻门 `artifact_checks.sh many_functions`:4100 个函数的合成文件求和必须 == 36900)
- W-120 → RESOLVED (2026-10-20, v4.0.17 —— temp 表按实际最大 temp id 分配 + 越界响亮失败;**同一道门**也抓它:关掉修复 → 求和 = 0(静默错值)被当场抓住)
- W-105 → RESOLVED (2026-10-20, v4.0.18 —— (a)「`&mut` 能用」+ (b) 最小独占检查(同作用域双 `&mut` 互斥);完整 NLL 留 backlog v4.3.0)
- W-105.1 → RESOLVED (2026-10-20, v4.0.18 —— `check_cap_pass` 死 stub 删除)
- W-118 → RESOLVED (2026-10-20, v4.0.18 —— 语言 lexer 的 EOF 守卫;A/B 193/193 逐字节不变)
- W-121 → RESOLVED (2026-10-20, v4.0.18 —— closure 符号名改用计数器 ⇒ 产物可复现)
- W-122 → RESOLVED (2026-10-20, v4.0.18 —— side-file 每次编译开头清干净 ⇒ 不再跨编译泄漏)
- W-113 → RESOLVED (2026-10-20, v4.0.18 —— `asm!` / `fence_*` 内联进函数体;之前是 .s 末的死字节)
- W-115 → RESOLVED (2026-10-20, v4.0.18 —— 根因是闭包捕获生成坏代码;现在编译期明确报错,W-089 的 reproducer 转 PASS)
- W-131 → RESOLVED (2026-10-24, v4.0.20 —— **v4.0.8 起 jhyy.exe 不再 embed 图标资源** ⇒ `.jhyy` 文件在 Explorer 里全是白板。安装器 `DefaultIcon` 改指独立 `jhyy-icon.ico`(本来就装着);已装机器写 HKCU 影子键即时恢复)
- W-132 → RESOLVED (2026-10-24, v4.0.20 —— 自举链接路径补 windres 步骤 ⇒ **用户编译出来的程序**也带 "J" 图标;**实现全在 C 侧**(`jh_gcc_invoke` 挂钩 + `jh_run` 收尾),`main.jhyy` 零改动 —— 给它加局部变量会移位 temp 编号 ⇒ 自举产物行为漂移;新增常驻门 `artifact_checks.sh compiler_icon` + `program_icon`,都用 Explorer 同一套 API(`shell32!ExtractIconExW`)问「exe 里到底有没有图标」)

历史 workaround 走 git history;`workarounds.md` 保留 RESOLVED/SUPERSEDED/INVALID 状态作 audit ledger。

## 与 jhyy_OS 项目的对齐（mirror stub）

> **本节给编译器侧 sprint 设计者** — 启动 session 打算做 v4.x / OS 相关 sprint 之前,**必读**本节指向的三份 OS 侧 doc (但 v4.x OS 启动路径需重新评估 — `v2.0.0-os-prep.md` 已作废)。

| 文档 | 用途 | 何时读 |
|------|------|--------|
| [`../jhyy_OS/docs/coordination.md` § 0 Critical Path](../jhyy_OS/docs/coordination.md) | OS × compiler 跨项目时间线权威视图 | **每个 v4.x sprint 启动前必读** (重新评估 M11 launch 路径) |
| [`../jhyy_OS/docs/v0.0.4-debug-abi.md`](../jhyy_OS/docs/v0.0.4-debug-abi.md) | **🔒 Locked**(2026-08-12,Q-Compiler-007 闭环 / D41)| Debug ABI + 尺寸定案 (D41 不动) |

**冲突解决规则**(从 OS 侧 coordination.md § 7 镜像):
- 任何 OS 镜像跟本 CLAUDE.md 冲突 → **以 compiler 为准** → OS 侧撤回 + 提交 Q-OS-XXX
- 任何 compiler doc 跟 OS 镜像冲突 → OS doc 为准(本地权威)→ compiler 提交 Q-Compiler-XXX
- 跨边界僵持 → 走 user 介入

**当前跨边界问题状态**(2026-08-12 校准,2026-09-30 v4.0.0 时 v2/v3 已 ship 但 OS M11 launch 路径需重新评估):
- ✅ **13 个 Q + 6 个 UD 决定 全部闭环/锁**
- ✅ Q-Compiler-007 (Debug ABI 所有权 + spec 锁) — 2026-08-12 闭环 (D41)
- ✅ D24-D29 6 个 UD 决定 — 全 ✅ 锁
- ⚠️ v2.0.0-os-prep.md 已归档 (2026-09-30);OS M11 launch 需重新评估路径,新 OS 计划待 v4.x sprint 设计时填