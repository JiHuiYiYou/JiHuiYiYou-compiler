# CLAUDE.md — JHYY (机会翼游) 编译器项目

自研静态类型编程语言 + 自举编译器。
当前: **🟡 v4.0.9-rc1 发布**（2026-10-18，**6 周来第一个真实可安装产物**）——
在 CI 重构把发布链修通之后打的 tag:
<https://github.com/JiHuiYiYou/JiHuiYiYou-compiler/releases/tag/v4.0.9-rc1>
（installer .exe 28.5 MB + compiler .msi + vscode .vsix + SHA256.txt）。
**v4.0.0 final 仍被 4 条 ACTIVE workaround 挡着**，按既定决策清零前不 promote；
4.0.9-rc1 是 RC，`make_latest` 为 false，v3.2.0 仍是 Latest。
此前 v3.4.2 / v4.0.0-rc1 / v4.0.1 / v4.0.2 / v4.0.6 五个 tag 全部发布失败，
最后一个真实 release 停在 2026-09-08 的 v3.2.0 —— 那段时间文档里的 "shipped"
指源码 commit，不指可安装产物。
- **v4.0.0-rc1 shipped** (2026-09-30, post-merge of `axis-v2` + `axis-v3` → main):
- **v4.0.0-rc1 shipped** (commits `a4ba8fa`..`675e7da`;tag `v4.0.0-rc1` 已打) — **v4.x 首发 RC** = v2.x FINAL (v2.16.0) + v3.x FINAL (v3.4.2) 合并入 main;QBE toolchain 完全移除 + bench.sh + .exe byte-equal D26 stage0 coverage + self-backend closure + stdlib (mem/fmt/io/math/string/vec) 落地。**🔴 2026-10-15 audit 后 blocker 未清零**(per 2026-10-10 user 决定 "所有defer/active的workaround必须在v4正式版中清零,大不了v4不发"):W-101 RESOLVED (v4.0.6 attempt #7) + W-097 RESOLVED (2026-10-15,六个 emit 根因,`closure_check.sh` PASS `v2.s == v3.s` byte-identical) + W-072 早已 RESOLVED (2026-09-09)。**索引表 ACTIVE = 14 / DEFERRED = 0**(2026-10-15 复核后修正 —— 此前写的「0」是索引重建脚本读不到 59/89 条目造成的假象,见 W-108;**2026-10-20 已降到 4 条**:W-104 / W-112 / W-114 / W-103 / W-107 / W-120 / W-105 / W-105.1 先后闭合),**下一个动作 = 清零剩下的 4 条活 workaround**(排期见 [`version-schedule.md`](docs/plans/v4/version-schedule.md))([`active-workaround-clearance.md`](docs/plans/v4/active-workaround-clearance.md)),不是 tag final
- **v1.x 已 ship** (v1.8.3 tag `98c8272`, 2026-08-29) — Stage 2 N=4 byte-equal 闭环 + installer v1.8.3 WiX + UCPD.sys bypass。v1.x 终结。

**v4.0 阶段**:v2.x 中/末 items (QBE 自写 — 现已 in-mem self-backend 直接 x86-64 emit 完成 / amd64_sysv 实 impl — V2-B 5/5 + V2-C v2.8.0 已 ship / N 代 fixed point — v2.14.0 N≥10 已 ship) 跟 v3.x items (3a-3f OS-required: inline asm / `#[naked]` / volatile / `#[link_section]` / memory barrier / `#[no_std]` / `&mut` + lifetime) 全部走完 / dropped off-axis (per 2026-09-29 user FINAL 决定);v4.0.0-rc1 = convergence release candidate (RC 保持,不 promote final per 2026-10-10 user 决定),后续 v4.x 工作走 [`docs/plans/v4/`](docs/plans/v4/) 的当前计划 + backlog。**已 ship 实际状态**(2026-10-11 v4.0.4 plan 已 commit):v4.0.2 ACTIVE bucket → 0 (W-073 emit escape + W-074/076 arena rename + W-075 mem_set i64-store + GHA 修通);v4.0.2.1 W-074.6 sub-bug #3 partial 真修 (sema hash + 65536 + chkstk_ms);v4.0.2.2 W-096 frame blow-up;v4.0.2.3 W-098 i64 literal emit;v4.0.2.5 W-097 hoist 7-site + W-100 sret clobber 真修。**emit 类 blocker 已清零(2026-10-15)**:W-101 RESOLVED (v4.0.6 attempt #7)+ W-097 RESOLVED (2026-10-15 六个 emit 根因,`closure_check.sh` PASS,`fixed_point.sh N=5` 7 PASS / 0 FAIL / 0 INFO,N=2 起全代 byte-equal)+ W-072 早已 RESOLVED (2026-09-09)。**但 2026-10-15 audit 挖出 14 条此前从未登记的活 workaround**(W-103..W-107 / W-105.1 首批;补断言测试又挖出 W-109 浮点比较、W-110 比较串号、W-111 泛型 enum 构造器(当时记为崩溃,2026-10-18 复核不复现)、W-112 link_section no-op、W-113 asm 位置错、W-114 enum match 失效;启 Docker 跑 sysv 门再挖出 W-115 W-089 reproducer 仍崩、W-116 SysV callee 只 spill 4 个寄存器) —— 见下 §当前活跃 workarounds。**下一动作 = 清零剩下的 4 条**(2026-10-20:W-104 / W-112 / W-114 / W-103 / W-107 / W-120 / W-105 / W-105.1 已先后闭合),不是 tag v4.0.0 final。OS M11 launch 路径需重新评估 (`v2.0.0-os-prep.md` + `v2-v3-parallel-sprint-plan.md` 中硬前置假设已作废并归档到 `docs/archive/v2-v3/`)。

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
| **v4.x** | 后合并 axis — stdlib / 0-C 闭环 / async / lifetime / trait / package manager / multi-arch / `.jhyynb` | 服务于编译器自身现代化 + jhyy_OS 重启评估 — **🟡 v4.0.0-rc1 shipped 2026-09-30 = v4.x 首发 RC** (axis-v2 + axis-v3 merge 入 main;**剩 4 条活 workaround 清零 → v4.0.0 final promote**;其余 12 项未启动,合并在 [`docs/plans/v4/backlog.md`](docs/plans/v4/backlog.md)) |

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
| L3 | [`docs/plans/v4/active-workaround-clearance.md`](docs/plans/v4/active-workaround-clearance.md) | **当前唯一进行中** — 剩 4 条活 workaround 真修(W-106 / W-113 / W-115 / W-118) |
| L3 | [`docs/plans/v4/backlog.md`](docs/plans/v4/backlog.md) | 12 项未启动的未来工作(原 v4.1.0 - v4.12.0 合并,2026-10-15) |

最近完成的 sprint: **v4.0.0-rc1 shipped 2026-09-30** — axis-v2 + axis-v3 merged into main。

下一阶段: **清零剩 4 条活 workaround**(见 [`active-workaround-clearance.md`](docs/plans/v4/active-workaround-clearance.md))→ 然后才谈 promote v4.0.0 final。backlog 那 12 项无优先级,不抢这条线。

**plan 命名约定(2026-10-15 修订)**:已 ship / 进行中的 sprint 保留 `v4.X.Y-plan.md`(审计轨迹,改名会破坏跟 changelog / commit 的对应);未启动的 backlog 与进行中的工作用描述性文件名,**不用版本号** —— 版本号在启动时才分配。
历史: changelog 见 `docs/logs/v0/changelog-v0.X.Y.md` (C 编译器) + `docs/logs/v1/changelog-v1.X.Y.md` (jhyy 自举) + `docs/logs/v2/changelog-v2.*.0.md` (QBE rewrite + freestanding) + `docs/logs/v3/changelog-v3.*.md` (language expansion + self-backend) + `docs/logs/v4/changelog-v4.0.0.md` (post-merge umbrella);早期 sprint（命名 `sprint-1*.md`）同目录。

### 项目内部（`docs/internal/`）

- [`build.md`](docs/internal/build.md) — 编译 / 运行 / **self-backend 坑（Windows 独有）**
- [`architecture.md`](docs/internal/architecture.md) — 流水线 / 模块 / 设计细节 / **self-backend codegen 速查** / Stage 0 自举
- [`conventions.md`](docs/internal/conventions.md) — 编码约定 / 文件命名 / 提交规则
- [`tests.md`](docs/internal/tests.md) — 集成测试清单 + 运行方法
- [`workarounds.md`](docs/internal/workarounds.md) — W-NNN workaround 台账（**ACTIVE = 4**,见下方 §当前活跃 workarounds）

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

**4 ACTIVE / 0 DEFERRED**(2026-10-20 复核:**W-104 RESOLVED**(v4.0.12 —— ≤16B eightbyte 分类 + >16B MEMORY class 整体落栈,与 gcc 三方向对拍全绿);**W-114 RESOLVED**(v4.0.14 —— enum 的 ABI 两侧统一:参数按地址传、返回值走 sret、调用结果是 8 字节指针;顺带修了 **W-119**:SysV 帧布局把第 0 号局部变量放在 `0(%rbp)` = 覆盖旧 rbp);**W-112 RESOLVED**(v4.0.16 —— `#[link_section]` 的 `.section` 之前被插进 link 路径的副本,磁盘上的 .s 里没有);**W-103 RESOLVED**(v4.0.16 —— `std_os_*` 五个 mock 接真 libc bridge;顺带把 POSIX/Win 的 `O_*` flag 差异在桥这一层翻译掉 —— **Windows 的 `_O_CREAT`=0x100 不是 POSIX 的 0x40**,mock 从不调 `open(2)` 所以这错一直藏着;并让 std lib **第一次真的可被用户代码 import**(`import os;` 两级查找:main 文件旁边 → std lib 目录)),测试从 inline 副本改成 import 真身),**W-107 RESOLVED**(v4.0.17 —— 五张 per-fn 表改成**按实际函数数**分配,固定上限 4096 与「太多函数」的响亮守门一并删除,**没有上限了**;顺带挖出并修掉 **W-120**:temp 表的 65536 上限会让**越界静默算错值** —— 修 W-107 会暴露它,两者必须一起做),**W-105 + W-105.1 RESOLVED**(v4.0.18 —— (a)「`&mut` 真的能用」(v4.0.15)+ (b)**最小独占检查**(同作用域内双 `&mut` 互斥)落地;`check_borrow` / `check_cap_pass` 两个「恒 return 1 的假装会检查」函数都删掉了。**上一版 (b) 失败的真根因是 W-107**(per-fn 表的固定上限:那次尝试加了几个顶层函数把 main.jhyy 推过 1024 → 被丢弃的函数帧算成 8 字节 → 「帧偏移 ≈ -515KB 的写」),W-107 改成按实际函数数分配后阻塞自然消失),**4 ACTIVE / 105 索引行**,per `docs/internal/workarounds.md` 索引表):

| W-NNN | 位置 | 性质 |
|-------|------|------|
| W-105 | — | ~~`&mut` 独占性完全不检查~~ ✅ **2026-10-20 已修**:(a)「`&mut` 真的能用」+ (b)**最小独占检查**(同作用域内双 `&mut` 互斥,新测试 `borrow_mut_conflict.jhyy` EXPECT-ERROR ✓)。词法作用域(borrow 提前结束会误报)—— 完整 NLL/Polonius 留 backlog v4.3.0 |
| W-103 | — | ~~`std_os_open/close/read/write` 全是 M0 mock,`std_os_exit` 不退出进程~~ ✅ **2026-10-20 已修**:5 个 libc bridge 进 `jhyy_helpers.c`;`import` 加 std lib 目录回落 → 测试改 import 真身(新增 `std_os_exit.jhyy` 验进程真退出) |
| W-107 | — | ~~五个 per-fn 表按固定上限分配~~ ✅ **2026-10-20 已修**:改成**按实际函数数**分配(`fn_count + 1`),`MAX_FN_ENTRIES` 常量删除、「太多函数」守门删除 —— **没有上限了**。之前那次动态分配被撤回,是因为「查表上界」那另一半真修还没落地(两者从未同时存在);这次两半齐了 |
| W-120 | — | ~~temp 表(65536)越界 → 静默算错值~~ ✅ **2026-10-20 已修**:两张按 temp id 索引的表改成按**实际最大 temp id** 分配 + 越界**响亮失败**。**HEAD 上本来就可复现**(一个 25000 语句的函数就够:算出 s=0,正确值 74994)。`main.jhyy` 自己的 max temp id 已到 64953 —— 离越界只剩 583 |
| W-106 | `compiler/src0/symtab.jhyy:260-264` | 死存储改栈布局。**2026-10-18 三次实测:原注释的理由已被证伪(栈帧两边都物化)、机制未知、删除的安全性未证实(约 11 次运行里 1 次间歇失败 vs 基线 9 次全绿)。不删,但别信旧注释** |
| W-112 | — | ~~`#[link_section]` 是 no-op~~ ✅ **2026-10-20 已修**:`.section` 之前被插进 link 路径的**副本**(`temp_asm`),磁盘上的 .s 和 `--no-link` 产物里都没有 → 现在 .s 产出后立刻对 `asm_path` 处理一次 |
| W-113 | `asm!` / `fence_*` emit 路径 | 字节被 emit 到 `ret` 之后,永不执行;ship gate 零敏感 |
| W-115 | `codegen_call_return_types.jhyy` | W-089 标 ✅ RESOLVED,但它自己的 reproducer 仍 STACK_OVERFLOW |
| W-105.1 | — | ~~`check_cap_pass` 同款 stub~~ ✅ **2026-10-20 已修**:它**连一个调用点都没有** → 函数 + 那 16 行「已知限制」注释一并删掉,原位置留「将来要做什么」的清单(零行为变化) |
| W-118 | `compiler/src0/lexer.jhyy:212-258` | 语言 lexer `lex_peek_char` 无 EOF 守卫 → 越过 end 前进(W-117 的同族另一处,尚未观测到危害) |

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