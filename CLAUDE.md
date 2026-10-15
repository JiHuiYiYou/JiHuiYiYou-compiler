# CLAUDE.md — JHYY (机会翼游) 编译器项目

自研静态类型编程语言 + 自举编译器。
当前: **🟡 v4.0.0-rc1 shipped** (2026-09-30, post-merge of `axis-v2` + `axis-v3` → main):
- **v4.0.0-rc1 shipped** (commits `a4ba8fa`..`675e7da`;tag `v4.0.0-rc1` 已打) — **v4.x 首发 RC** = v2.x FINAL (v2.16.0) + v3.x FINAL (v3.4.2) 合并入 main;QBE toolchain 完全移除 + bench.sh + .exe byte-equal D26 stage0 coverage + self-backend closure + stdlib (mem/fmt/io/math/string/vec) 落地。**🔴 2026-10-15 audit 后 blocker 未清零**(per 2026-10-10 user 决定 "所有defer/active的workaround必须在v4正式版中清零,大不了v4不发"):W-101 RESOLVED (v4.0.6 attempt #7) + W-097 RESOLVED (2026-10-15,六个 emit 根因,`closure_check.sh` PASS `v2.s == v3.s` byte-identical) + W-072 早已 RESOLVED (2026-09-09)。**索引表 ACTIVE = 9 / DEFERRED = 0**(2026-10-15 复核后修正 —— 此前写的「0」是索引重建脚本读不到 59/89 条目造成的假象,见 W-108),**下一个动作 = 清零 9 条活 workaround**([`active-workaround-clearance.md`](docs/plans/v4/active-workaround-clearance.md)),不是 tag final
- **v1.x 已 ship** (v1.8.3 tag `98c8272`, 2026-08-29) — Stage 2 N=4 byte-equal 闭环 + installer v1.8.3 WiX + UCPD.sys bypass。v1.x 终结。

**v4.0 阶段**:v2.x 中/末 items (QBE 自写 — 现已 in-mem self-backend 直接 x86-64 emit 完成 / amd64_sysv 实 impl — V2-B 5/5 + V2-C v2.8.0 已 ship / N 代 fixed point — v2.14.0 N≥10 已 ship) 跟 v3.x items (3a-3f OS-required: inline asm / `#[naked]` / volatile / `#[link_section]` / memory barrier / `#[no_std]` / `&mut` + lifetime) 全部走完 / dropped off-axis (per 2026-09-29 user FINAL 决定);v4.0.0-rc1 = convergence release candidate (RC 保持,不 promote final per 2026-10-10 user 决定),后续 v4.x 工作走 [`docs/plans/v4/`](docs/plans/v4/) 的当前计划 + backlog。**已 ship 实际状态**(2026-10-11 v4.0.4 plan 已 commit):v4.0.2 ACTIVE bucket → 0 (W-073 emit escape + W-074/076 arena rename + W-075 mem_set i64-store + GHA 修通);v4.0.2.1 W-074.6 sub-bug #3 partial 真修 (sema hash + 65536 + chkstk_ms);v4.0.2.2 W-096 frame blow-up;v4.0.2.3 W-098 i64 literal emit;v4.0.2.5 W-097 hoist 7-site + W-100 sret clobber 真修。**emit 类 blocker 已清零(2026-10-15)**:W-101 RESOLVED (v4.0.6 attempt #7)+ W-097 RESOLVED (2026-10-15 六个 emit 根因,`closure_check.sh` PASS,`fixed_point.sh N=5` 7 PASS / 0 FAIL / 0 INFO,N=2 起全代 byte-equal)+ W-072 早已 RESOLVED (2026-09-09)。**但 2026-10-15 audit 挖出 9 条此前从未登记的活 workaround**(W-103..W-107 / W-105.1 首批,后挖出 W-109 浮点比较、W-110 比较串号、W-111 泛型 enum 崩溃) —— 见下 §当前活跃 workarounds。**下一动作 = 清零这 9 条**,不是 tag v4.0.0 final。OS M11 launch 路径需重新评估 (`v2.0.0-os-prep.md` + `v2-v3-parallel-sprint-plan.md` 中硬前置假设已作废并归档到 `docs/archive/v2-v3/`)。

## Reading order

按你打算做的事挑一个入口：

| 意图 | 先看 |
|------|------|
| 了解项目现在到哪、有什么限制 | 顶部 § 当前/目标 → [`workarounds.md`](docs/internal/workarounds.md)（当前限制）+ [`docs/logs/v4/changelog-v4.0.0.md`](docs/logs/v4/changelog-v4.0.0.md)（最新 ship） |
| 想看 v0.x（C 编译器）整体还有什么没完成 | [`v0.x-c-compiler-roadmap.md`](docs/plans/roadmap/v0.x-c-compiler-roadmap.md)（已 frozen） |
| 起 v4.x 新 sprint | [`active-workaround-clearance.md`](docs/plans/v4/active-workaround-clearance.md)(**当前唯一进行中**)→ 未启动的未来工作看 [`backlog.md`](docs/plans/v4/backlog.md) |
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
| **v4.x** | 后合并 axis — stdlib / 0-C 闭环 / async / lifetime / trait / package manager / multi-arch / `.jhyynb` | 服务于编译器自身现代化 + jhyy_OS 重启评估 — **🟡 v4.0.0-rc1 shipped 2026-09-30 = v4.x 首发 RC** (axis-v2 + axis-v3 merge 入 main;**9 条活 workaround 清零 → v4.0.0 final promote**;其余 12 项未启动,合并在 [`docs/plans/v4/backlog.md`](docs/plans/v4/backlog.md)) |

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
| L3 | [`docs/plans/v4/active-workaround-clearance.md`](docs/plans/v4/active-workaround-clearance.md) | **当前唯一进行中** — W-103..W-107 六条活 workaround 真修 |
| L3 | [`docs/plans/v4/backlog.md`](docs/plans/v4/backlog.md) | 12 项未启动的未来工作(原 v4.1.0 - v4.12.0 合并,2026-10-15) |

最近完成的 sprint: **v4.0.0-rc1 shipped 2026-09-30** — axis-v2 + axis-v3 merged into main。

下一阶段: **清零 9 条活 workaround**(见 [`active-workaround-clearance.md`](docs/plans/v4/active-workaround-clearance.md))→ 然后才谈 promote v4.0.0 final。backlog 那 12 项无优先级,不抢这条线。

**plan 命名约定(2026-10-15 修订)**:已 ship / 进行中的 sprint 保留 `v4.X.Y-plan.md`(审计轨迹,改名会破坏跟 changelog / commit 的对应);未启动的 backlog 与进行中的工作用描述性文件名,**不用版本号** —— 版本号在启动时才分配。
历史: changelog 见 `docs/logs/v0/changelog-v0.X.Y.md` (C 编译器) + `docs/logs/v1/changelog-v1.X.Y.md` (jhyy 自举) + `docs/logs/v2/changelog-v2.*.0.md` (QBE rewrite + freestanding) + `docs/logs/v3/changelog-v3.*.md` (language expansion + self-backend) + `docs/logs/v4/changelog-v4.0.0.md` (post-merge umbrella);早期 sprint（命名 `sprint-1*.md`）同目录。

### 项目内部（`docs/internal/`）

- [`build.md`](docs/internal/build.md) — 编译 / 运行 / **self-backend 坑（Windows 独有）**
- [`architecture.md`](docs/internal/architecture.md) — 流水线 / 模块 / 设计细节 / **self-backend codegen 速查** / Stage 0 自举
- [`conventions.md`](docs/internal/conventions.md) — 编码约定 / 文件命名 / 提交规则
- [`tests.md`](docs/internal/tests.md) — 集成测试清单 + 运行方法
- [`workarounds.md`](docs/internal/workarounds.md) — W-NNN workaround 台账（**ACTIVE = 9**,见下方 §当前活跃 workarounds）

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

**9 ACTIVE / 0 DEFERRED**(2026-10-15 fan-out audit + 复核,per `docs/internal/workarounds.md` 索引表):

| W-NNN | 位置 | 性质 |
|-------|------|------|
| W-105 | `compiler/src0/sema.jhyy:2558-2560` | `check_borrow` 恒 `return 1`,`:2677` 每个函数声明都调 → `&mut` 独占性完全不检查 |
| W-111 | 泛型 enum 的 sema 错误恢复路径 | 泛型 enum 一旦被 match → 报完 `unknown enum type` 后 **SEGV**(编译器崩溃) |
| W-110 | 自举后端 temp 槽位(根因待 RCA) | 一个函数里多条浮点比较连续改同一 mutable 局部 → 结果串号 |
| W-109 | `compiler/src0/codegen_amd64_lexer.jhyy:1628-1647` | 自举 IL lexer 缺 6 个浮点比较助记符 → f32 比较按 f64 算,`f64 ==/!=` 硬失败 |
| W-103 | `compiler/src0/std/os.jhyy:69-144` | `std_os_open/close/read/write` 全是 M0 mock,`std_os_exit` 不退出进程 |
| W-104 | `compiler/src0/abi_amd64_sysv.jhyy:229` | SysV 参数分类调用 **Win** 分类器(`abi_sysv_classify_arg` 在同文件 `:79` 但没接线) |
| W-107 | `compiler/src0/codegen_amd64_state.jhyy:511-537` | 五个 per-fn 表硬编码 1024,实测已用 991 → 余量 33 个函数 |
| W-106 | `compiler/src0/symtab.jhyy:261-264` | arena-touch 强制后端物化栈帧(源码字面 `// WORKAROUND:`) |
| W-105.1 | `compiler/src0/sema.jhyy:2578-2579` | `check_cap_pass` 同款 stub,当前无调用点 |

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