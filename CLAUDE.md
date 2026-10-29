# CLAUDE.md — JHYY (机会翼游) 编译器项目

自研静态类型编程语言 + 自举编译器。
当前: **🟢 v4.1.2 发布**（2026-10-29，**`jhyy --version` 从来就不存在**（跑它 =
`unknown command` + exit 1）⇒ 全仓表述订正；**`jhyy --help` 里 compile/build 的
说明写反了**（要 exe 用 `jhyy compile`）；**版本号自动化** —— `VERSION` 文件做
唯一真相源 + `scripts/dev/bump_version.py`（set/check/finalize）+ 两道门
（CI 零漂移门 + release 的 `VERSION == tag` 断言）；顺带真修 `build.ps1 bundle`
静默复用陈旧 MSI ⇒ bundle 里嵌旧编译器）——
<https://github.com/JiHuiYiYou/JiHuiYiYou-compiler/releases/tag/v4.1.2>
（installer .exe 54.9 MB + compiler .msi 27.5 MB + vscode .vsix + SHA256.txt）。
**🟢 v4.1.0 发布**（2026-10-29，**installer 自带最小原生 ucrt64 工具链 ⇒
装机用户不再需要 MSYS2**）——
<https://github.com/JiHuiYiYou/JiHuiYiYou-compiler/releases/tag/v4.1.0>
（installer .exe 54.9 MB + compiler .msi 27.5 MB + vscode .vsix + SHA256.txt）。
**🟢 v4.0.22 发布**（2026-10-29）——lang-spec 覆盖审计：补 49 条回归门 + 14 个
真缺陷真修 + 台账 ACTIVE 桶第二次清空。
**🟢 v4.1.1 发布**（2026-10-29，**VSCode 终端 profile 改为探测真实 bash**（VSCode 自带的
`bash (MSYS2)` 路径写死且不回落）+ 新增 `jhyy-bash.cmd` 启动器；
**⚠️ 同时作废「打包 POSIX 层」这条计划** —— 实测 MSYS2 运行时**不做按树搬迁**
⇒ 详见 [`installer/toolchain/README.md`](installer/toolchain/README.md) § 二期结论）。
<https://github.com/JiHuiYiYou/JiHuiYiYou-compiler/releases/tag/v4.0.22>
**🟢 v4.0.19 发布**（2026-10-20，**台账 ACTIVE 桶首次清空(14 → 0)**）——
<https://github.com/JiHuiYiYou/JiHuiYiYou-compiler/releases/tag/v4.0.19>
（installer .exe + compiler .msi + vscode .vsix + SHA256.txt）。
**v4.1.0 的关键事实**（详见 [`installer/toolchain/README.md`](installer/toolchain/README.md)）：
解析顺序 `JHY_GCC → %JHYY_HOME%\env.txt → **内置** → C:\msys64 → PATH`；
新增 7 条工具链常驻门 + W-158..W-163 六条台账；**破坏性变更**（默认 gcc 换成内置那份）。
⚠️ **v4.1.0 最值得记住的一条**：gcc 16 把系统头路径**写死**成
`<prefix>/bin/../../ucrt64/include` ⇒ 工具链根下**必须保留 `ucrt64/` 这一层**
—— 本地(gcc 15.2.0)永远测不出来，是 CI(gcc 16.2.0)逼出来的。
⚠️ **发版链路上修掉的两个既有 bug**：
① MSI 的 Bal 扩展 DLL 路径**写死 WiX 版本** ⇒ WiX 一升级，发版就挂在最后一步；
② GitHub runner 镜像自带**旧 MSYS2 在 `C:\mingw64`**（gcc 15.2.0）且**排在 PATH 前面**
⇒ pwsh 步按 PATH 找 gcc 会挑中旧的 ⇒ 工具链版本 pin 失败 ⇒ 现在把
MSYS2 根目录**显式传下去**（`JHY_MSYS2_ROOT=$(cygpath -w /)`）。
⚠️ v4.0.22 第二轮最值得记住的一条：**自举闭环门验错了代**（W-147）—— 旧逻辑验的是
**锚点**的不动点、`mv` 装出去的却是**没被验过**的第 1 代 ⇒ 改后端时 src0 自己的 `.s`
编码一变就**硬卡死**，而且那一代恰恰是**常量错**的一代 ⇒ 门已改成**迭代到不动点**
（过渡期自动消化，且门从「验锚点」升级成「验装出去的那个产物」）。
⚠️ v4.0.22 最值得记住的一条：**6 个 std 模块的测试全是 inline 副本** ⇒ 改
`compiler/src0/std/*.jhyy` 真身**零回归覆盖**，而且副本里是**同样的错误代码**
⇒ 副本测试给错误实现背书。补的 6 个 `std_*_import.jhyy`(第一次 import 真身)
当场挖出三处真缺陷：**字节循环写穿 4n 字节**(12 处)、**`import string;` 编译失败**、
**arena 把分配互相踩 ⇒ AV**。详见
[`docs/logs/v4/changelog-v4.0.0.md`](docs/logs/v4/changelog-v4.0.0.md) § v4.0.22。
⚠️ v4.0.21 最值得记住的两条：
① **「链接失败」的三层掩护**（悬空注释吞掉 C 桥符号 → `$(CFLAGS_STAGE0)` 未定义
把 `-Wall -Wextra` 一起丢掉 → PATH 里 `/mingw64/bin` 抢在 ucrt64 前面导致 ld
加载错版本 DLL、**失败时零输出**）；
② **跨盘输出 100% 失败**（`MoveFileExW` 不带 `MOVEFILE_COPY_ALLOWED` ⇒ 不能跨卷
⇒ 输出到 D: 而 `%TEMP%` 在 C: 时**产物不落地**）—— 本地同盘 ⇒ 完全无感，
是 CI 第一次跑 MCP pytest 才暴露的**老** bug ⇒ 详见
[`docs/logs/v4/changelog-v4.0.0.md`](docs/logs/v4/changelog-v4.0.0.md) § v4.0.21。
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
| 知道下一步做什么 | [`version-schedule.md`](docs/plans/v4/version-schedule.md)(**版本轴排期,入口在这**)→ 当前主线 [`self-backend-perf-plan.md`](docs/plans/v4/self-backend-perf-plan.md)
| 起 v4.x 新 sprint | [`self-backend-perf-plan.md`](docs/plans/v4/self-backend-perf-plan.md)(v4.2 起的主线)→ 其余未启动工作看 [`backlog.md`](docs/plans/v4/backlog.md) |
| 改编译器 / 排 bug | [`architecture.md`](docs/internal/architecture.md) 看模块边界 → [`build.md`](docs/internal/build.md) 看构建 + 调试坑 |
| 改语言规范 / ABI | [`jhyy-lang-spec-v4.0.0.md`](docs/abis/jhyy-lang-spec-v4.0.0.md) / [`jhyy-abi-v4.0.0.md`](docs/abis/jhyy-abi-v4.0.0.md) |
| 查 v2/v3 历史决策 | [`docs/archive/v2-v3/`](docs/archive/v2-v3/) (v2-v3-parallel-sprint-plan.md + v2.0.0-os-prep.md 已归档,2026-09-29 user FINAL 决定作废) |

## 权威文档（100% 权威）

| 文档 | 状态 | 用途 |
|------|------|------|
| [`jhyy-lang-spec-v4.0.0.md`](docs/abis/jhyy-lang-spec-v4.0.0.md) | 锁定（2026-10-24，**取代 v1.3.0 + 17 份 v3.x supplement**，后二者已归档至 git 历史）| 语言规范 + 附录 B 已知限制。**正文只写当前代码确实已实装的行为**;未实装/受限的收进附录 B,不再混在正文冒充特性 |
| [`jhyy-abi-v4.0.0.md`](docs/abis/jhyy-abi-v4.0.0.md) | 锁定（2026-10-24）| 类型布局 + 调用约定。**⚠️ 2026-10-15 修正(v1.0.0 时代遗留):此前称「已全部解锁」不成立** —— A3(struct 跨 FFI)从未实现,A5(浮点比较)是确证 bug(W-109),两者都没挡住自举(自举 v1.8.3 已达成),但也不能算「解锁」 |
| ~~`jhyy-lang-spec-floatsupplement-v3.3.0.md`~~ | **已作废**（v3.3.0 收编进 v1.3.0,v1.3.0 又被 v4.0.0 取代 ⇒ 浮点补充规范现由 `jhyy-lang-spec-v4.0.0.md` 正文承载）| 浮点补充规范 — float `as` cast / fmod trunc / signed-zero semantics |

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
| L3 | [`docs/plans/v4/self-backend-perf-plan.md`](docs/plans/v4/self-backend-perf-plan.md) | 🔄 **v4.2 起的主线**(2026-10-29 立线)—— 自研后端性能线 |
| L3 | [`docs/plans/v4/backlog.md`](docs/plans/v4/backlog.md) | 12 项未启动的未来工作(原 v4.1.0 - v4.12.0 合并,2026-10-15);M5 Part 1/2 已完成,Part 3 = v4.5 |

最近完成的 sprint: **v4.1.2 shipped 2026-10-29** — 版本号自动化 + 三处「表述与实现不符」真修。

下一阶段: **v4.4 = 寄存器分配**(自研后端性能线,2026-10-29 user 拍板)——
见 [`docs/plans/v4/self-backend-perf-plan.md`](docs/plans/v4/self-backend-perf-plan.md)
(版本号权威在 [`version-schedule.md`](docs/plans/v4/version-schedule.md))。
v4.2.0 / v4.2.1 ✅ 已完成;**v4.2.2 / v4.3.0 已降级**(实测性能价值 ≈0,见下);
下一个是 v4.4.0(后端加「temp → 寄存器/槽位」位置映射 + 前瞻窗口的寄存器缓存)。

⚠️ **2026-10-29 一次测量驱动的重排(不是拍脑袋)**:v4.2.1 落地后逐项量了
「还差多少」——
| 版本 | 声称价值 | **实测机会数** |
|---|---|---|
| v4.2.2 peephole | 折叠 no-op | 54 条 / 407386 行(0.002%) |
| v4.3.0 常量折叠 | `2+3` → `5` | 语料 A **0** / 语料 B **84** —— ⚠️ **前端本来就不折叠** |
| v4.3.0 代数化简 | `x+0` → `x` | 54 / 424 |
| v4.3.0 DCE | 删死指令 | 42(0.1%)/ 193 —— 前端产出的 SSA 本来就干净 |
| **v4.4 寄存器分配** | 消掉 load/store 往返 | **52% 的 temp 只用一次;30.5% 紧接着下一条就用;47.8% 在 4 条之内** |

**根因**:后端把**每个** SSA temp 物化成一个栈槽 ⇒ 每个值都是
「load 槽 → 算 → store 槽」⇒ 机器码里 **49% 的指令是访存**。
**这才是 2x 差距的所在**,IR 层优化动不了它。

**v4.2 主线为什么是自研后端性能**(2026-10-29 实测,不是判断):
`compiler/src/*.c` 已于 v4.0.21 删光 ⇒ **自研后端就是编译器本身**
(`jhyy.exe` 自己编 `src0/main.jhyy`)⇒ 后端性能直接乘在
项目迭代速度 + 用户写的每个 jhyy 程序上。可信基线(旧 `bench.sh` 的计时器是坏的):
修帧尺寸前 jhyy 比 gcc -O0 慢 **3.46x(fib)/ 4.65x(ack)**;
其中 **~41% 来自一个写死的常量**(`emit_ctrl.jhyy` 的 `8192` ⇒ 每函数帧
≥8352 字节 ⇒ 100% 的函数每次调用都走 `___chkstk_ms` 探页)。

**v4.2.1 已修(台账 W-167)**:帧中位 **8368 → 288 字节** · `___chkstk_ms` 调用
**1045 → 46 处** · 总预留栈 **9.1MB → 1.5MB** · fib/ack jhyy/gcc-O0
**3.46x/4.65x → 2.14x/2.13x** · 自举编译 **-16%** · 顺带修掉一个潜在下溢
(旧公式在公式池主导时把 `per_fn_alloc` 丢掉了 ⇒ 值池向下生长不受帧保护)。
新门 `artifact_checks.sh frame_bloat` + `frame_slots` 锁住这个收益。
数据见 [`docs/perf/self-backend-baseline-2026-10-29.md`](docs/perf/self-backend-baseline-2026-10-29.md),
测量脚本 `scripts/dev/bench/runtime_perf.py`(CPython `perf_counter`;MSYS2 的
`date +%s.%N` 不可信,别用它计时)。**CI 里的性能门是静态指标硬门**(指令数/
访存数/帧大小/chkstk 次数,确定性 ⇒ 跨机器逐字节相同),**墙钟只报告** ——
共享 runner 的宿主负载不可控。

**plan 命名约定(2026-10-15 修订)**:已 ship / 进行中的 sprint 保留 `v4.X.Y-plan.md`(审计轨迹,改名会破坏跟 changelog / commit 的对应);未启动的 backlog 与进行中的工作用描述性文件名,**不用版本号** —— 版本号在启动时才分配。
历史: changelog 见 `docs/logs/v0/changelog-v0.X.Y.md` (C 编译器) + `docs/logs/v1/changelog-v1.X.Y.md` (jhyy 自举) + `docs/logs/v2/changelog-v2.*.0.md` (QBE rewrite + freestanding) + `docs/logs/v3/changelog-v3.*.md` (language expansion + self-backend) + `docs/logs/v4/changelog-v4.0.0.md` (post-merge umbrella);早期 sprint（命名 `sprint-1*.md`）同目录。

### 项目内部（`docs/internal/`）

- [`build.md`](docs/internal/build.md) — 编译 / 运行 / **self-backend 坑（Windows 独有）**
- [`architecture.md`](docs/internal/architecture.md) — 流水线 / 模块 / 设计细节 / **self-backend codegen 速查** / Stage 0 自举
- [`conventions.md`](docs/internal/conventions.md) — 编码约定 / 文件命名 / 提交规则
- [`tests.md`](docs/internal/tests.md) — 集成测试清单 + 运行方法
- [`workarounds.md`](docs/internal/workarounds.md) — W-NNN workaround 台账（**ACTIVE = 0** ✅ 见下方 §当前活跃 workarounds）

### 语言规范 & ABI（`docs/abis/`，locked）

- [`jhyy-lang-spec-v4.0.0.md`](docs/abis/jhyy-lang-spec-v4.0.0.md) — 语言规范（v4.0.0 锁定，2026-10-24;**取代 v1.3.0 + 17 份 v3.x supplement**;浮点内容已收进正文）
- [`jhyy-abi-v4.0.0.md`](docs/abis/jhyy-abi-v4.0.0.md) — ABI 白皮书（struct pass-by-value / 多文件 / FFI / break-continue / 切片 / 命名空间）

### 历史归档（`docs/archive/`，不再使用）

- [`v2-v3/v2-v3-parallel-sprint-plan.md`](docs/archive/v2-v3/v2-v3-parallel-sprint-plan.md) — **SUPERSEDED 2026-09-29** v2/v3 并行 sprint 调度（v4.0.0 archive 后保留）
- [`v2-v3/v2.0.0-os-prep.md`](docs/archive/v2-v3/v2.0.0-os-prep.md) — **SUPERSEDED 2026-09-29** OS × compiler 跨边界 M1-M11 硬前置（v4.0.0 archive 后保留）

## 工作风格

工具链与构建见 [`build.md`](docs/internal/build.md);编码约定、项目结构、改动后必跑基线见 [`conventions.md`](docs/internal/conventions.md)。

**发版时的版本号不要手改** —— `VERSION` 文件是唯一真相源,一条命令刷全仓
(编译器横幅字面量 / license.rtf / scoop json / winget manifest 目录名 + 3 个 yaml /
changelog 段):
```bash
python scripts/dev/bump_version.py set 4.1.2   # 刷版本号
make                                            # 横幅字面量变了 -> 自举产物必须重编
pwsh -File installer/build.ps1 bundle           # 构建
python scripts/dev/bump_version.py finalize     # 回填 sha256
python scripts/dev/bump_version.py check        # 零漂移门(CI 也跑)
```
⚠️ **顺序不能反**:编译器的版本横幅只能是 `main.jhyy` 里的**字符串字面量** ——
改成运行时读文件/调 extern 需要新增局部变量,而**新增局部变量会移位模块级 temp
编号 ⇒ 自举产物行为漂移**(v4.0.20 实测 ⇒ 6 个 sysv 用例全红)。
详见 [`build.md`](docs/internal/build.md) § 版本号自动化。

## 当前活跃 workarounds

**0 ACTIVE / 0 DEFERRED**(2026-10-27 —— **ACTIVE 桶第二次清空**(第一次是 2026-10-20)。
v4.0.22 三轮下来把审计挖出的 6 条 ACTIVE 全闭了:W-143 / W-144(第二轮)、
W-145..W-149(第二轮)、**W-142(第三轮:同作用域 shadowing → 改成 shadowing)+ 兄弟
缺陷 W-150(重名 fn/type/const/参数 ⇒ 空指针写崩溃 → 改编译期报错)**;
第三轮晚又查出并修掉 **W-151**(match arm 不开作用域 ⇒ arm 的模式绑定复用外层同名
变量 ⇒ **payload 被静默丢弃**)与 **W-152**(重名 import ⇒ 编译器崩溃;重名类型参数 ⇒
误导性错误链)⇒ **「null sym 空指针写」这一整类收口**(13 类重名形态全扫:0 崩溃)。
⇒ 套件的 **XFAIL 也归零**。
**第四轮(同日)**:逐个 smoke-test MCP 工具 ⇒ 挖出 **W-154**(`jhyy_workarounds`
与索引脚本口径不一致 ⇒ 计数不可信)/ **W-155**(`jhyy_get_il` 从来没成功过)/
**W-156**(两份 env 构造器分叉 ⇒ MCP 的 regress 报 207/277 假失败)—— 三条都是
**工具自身**的沉默失效;外加 **W-157**:`spec_argc_argv` 门断言错宽度
(`*argv` 只 load 1 字节 ⇒ 它验的是「堆地址最低字节 ≠ 0」⇒ 跟堆布局绑定的假信号
⇒ CI 上因 PATH 形态变化而假红)。
⇒ 回归 **257 PASS + 0 XFAIL + 0 failed + 20 SKIP**(277 total);
MCP 套件 **46 passed / 1 skipped**。
(此前:2026-10-26 早些时候 —— ACTIVE 涨到 **3** —— **W-143** = 浮点↔指针**不是按位
重解释**(浮点→指针走数值截断;指针→浮点**静默给 0**);**W-144** = 数组类型的 struct
字段**没被拷贝**(字面量读到垃圾 + 按值赋值 ACCESS_VIOLATION))。
**W-139 / W-140 / W-141 三个 RESOLVED** 是同一轮挖出的 std lib 真缺陷(字节循环
写穿 4n 字节 / `import string;` 编译失败 / arena 分配互相踩)—— 根因都是
「**6 个 std 模块的测试全是 inline 副本**」⇒ 改真身零覆盖、副本给错误实现背书。
(此前:2026-10-25 —— ACTIVE 仍为 **0**;DEFERRED 也归零了:W-134.1
的 CI pytest step 已由 commit `2ab0f24` 落地,台账此前忘了翻状态 ⇒ 0/0;2026-10-20 曾清零 14 → 0,清零过程:**W-104 RESOLVED**(v4.0.12 —— ≤16B eightbyte 分类 + >16B MEMORY class 整体落栈,与 gcc 三方向对拍全绿);**W-114 RESOLVED**(v4.0.14 —— enum 的 ABI 两侧统一:参数按地址传、返回值走 sret、调用结果是 8 字节指针;顺带修了 **W-119**:SysV 帧布局把第 0 号局部变量放在 `0(%rbp)` = 覆盖旧 rbp);**W-112 RESOLVED**(v4.0.16 —— `#[link_section]` 的 `.section` 之前被插进 link 路径的副本,磁盘上的 .s 里没有);**W-103 RESOLVED**(v4.0.16 —— `std_os_*` 五个 mock 接真 libc bridge;顺带把 POSIX/Win 的 `O_*` flag 差异在桥这一层翻译掉 —— **Windows 的 `_O_CREAT`=0x100 不是 POSIX 的 0x40**,mock 从不调 `open(2)` 所以这错一直藏着;并让 std lib **第一次真的可被用户代码 import**(`import os;` 两级查找:main 文件旁边 → std lib 目录)),测试从 inline 副本改成 import 真身),**W-107 RESOLVED**(v4.0.17 —— 五张 per-fn 表改成**按实际函数数**分配,固定上限 4096 与「太多函数」的响亮守门一并删除,**没有上限了**;顺带挖出并修掉 **W-120**:temp 表的 65536 上限会让**越界静默算错值** —— 修 W-107 会暴露它,两者必须一起做),**W-105 + W-105.1 RESOLVED**(v4.0.18 —— (a)「`&mut` 真的能用」(v4.0.15)+ (b)**最小独占检查**(同作用域内双 `&mut` 互斥)落地;`check_borrow` / `check_cap_pass` 两个「恒 return 1 的假装会检查」函数都删掉了。**上一版 (b) 失败的真根因是 W-107**(per-fn 表的固定上限:那次尝试加了几个顶层函数把 main.jhyy 推过 1024 → 被丢弃的函数帧算成 8 字节 → 「帧偏移 ≈ -515KB 的写」),W-107 改成按实际函数数分配后阻塞自然消失),**W-118 RESOLVED**(v4.0.18 —— 语言 lexer 的 `lex_peek_char` 加 EOF 守卫;**防御性**修复:这条从来没观测到危害,只是把「EOF 是隐式的」变成显式的),顺带挖出并修掉 **W-121**(合成 closure 的符号名取自**节点堆地址** ⇒ ASLR ⇒ **同一编译器连编两次 `.s` 就不同**,产物不可复现;改用计数器)和 **W-122**(四个 side-file 用**固定路径** ⇒ 上一次编译的内容泄漏到下一次 —— `--no-link` 批量编译后紧接 `make` 会用 no_std 的链接行链一个正常程序 ⇒ 整个 build 挂掉),**W-113 RESOLVED**(v4.0.18 —— `asm!` / `fence_*` 的文本经 IL(`dbgasm <hex>`)**内联进函数体**;之前是 append 到 .s 末 = 落在所有函数之外 = **死字节** —— 连**内存屏障都从来没执行过**;`asm_before_ret` 从 KNOWN-FAIL 升级成真门),**W-115 RESOLVED**(v4.0.18 —— W-089 的 reproducer 之所以 STACK_OVERFLOW,根因**不是** W-089:是那个 8-subtest 里的**闭包捕获了外层变量** —— 闭包捕获在 v3.2.1 的 MVP 范围里明确不支持,但编译器**没有任何检查** ⇒ 给它生成坏代码(env 压根没传进合成 fn)⇒ 运行时炸。现在**编译期明确报错** ✓,reproducer 已转 PASS(EXIT=0)——「W-089 已 RESOLVED」这句话**现在有证据支撑**了),**W-106 RESOLVED**(v4.0.19 —— 那处「每次 symbol lookup 白造一个 StringBuilder」的
死存储删掉了:它注释里的理由(「逼 codegen 物化栈帧」)**早就被证伪**(删不删栈帧都
完整物化);而 2026-10-18 那次「删掉它 ⇒ 偶发失败 ⇒ 它承重」的对照实验**归错了因** ——
真凶是 **W-123**(`jh_mktemp_ascii` 的 seed = `pid ^ tid ^ ctr`,而 Windows 的 pid
与主线程 tid 来自**同一个全局计数器** ⇒ `N ^ (N+1) = 1` ⇒ **每两个并发进程就撞一次
同一个临时文件名** ⇒ 一个的 rename 失败 ⇒ **编译失败**。W-123 修好后:并发编译 32 个
→ **0 失败**(修复前 4 个)),**0 ACTIVE / 0 DEFERRED / 127 索引行**(W-134.1 的 CI step 已由 `2ab0f24` 落地,2026-10-25 补翻状态),per `docs/internal/workarounds.md` 索引表):

| W-NNN | 位置 | 性质 |
|-------|------|------|
| W-157 | — | ~~`spec_argc_argv` 门断言的不是它声称的东西 —— `*argv` 只 load **1 字节**~~ ✅ **2026-10-27 已修**:入口签名的 `argv` 实际是 C 的 `char **`(类型却写作 `*u8`)⇒ `*argv` 生成的 IL 是 `loadub` ⇒ 读到的是 **`argv[0]` 指针的最低字节** ⇒ 那条断言实际在验「**堆地址最低字节 ≠ 0**」⇒ **跟堆布局绑定的假信号**(PATH 形态一变 ⇒ 堆基址偏移 ⇒ 最低字节恰好为 0 ⇒ 假红;2026-10-27 CI 上就是这样炸的,本地用「MSYS 形式 PATH + `;` + Windows 形式」当场复现)。修法:门改 `*(argv as **u8)`(IL 变 `loadl`);spec §1.1 + 附录 B 写明 `argv` 的 cast 约定。门:`spec_argc_argv.jhyy` |
| W-152 | — | ~~重名 **import** ⇒ 编译器**崩溃**(0xC0000005);重名**类型参数** ⇒ 报一串指不到病根的错~~ ✅ **2026-10-27 已修**:同一个 null sym 的最后两条路径 —— import 的 sym 是 null ⇒ `main.jhyy` 的 `inline_imports` 直接 `(*id_sym_p).name` 解引用它 ⇒ 崩;类型参数的 null 进了 type_params 数组 ⇒ 声明与符号表对不上 ⇒ 后面报「E0062: cannot infer type parameter」这种误导性错误。两处都加 `parser_duplicate_name` 守卫。门:`spec_dup_import.jhyy` / `spec_dup_type_param.jhyy` |
| W-151 | — | ~~match arm 不开作用域 ⇒ arm 的模式绑定**复用外层同名变量** ⇒ **payload 被静默丢弃**(静默错值)~~ ✅ **2026-10-27 已修**:arm 的模式绑定落进**外层**作用域 + `parse_pattern` 的 ident 绑定走「先查后插」且查是 `symtab_lookup`(沿链往外找)⇒ 模式的「绑定」变成「引用」。修法:每个 arm 一个**独立作用域**(push/pop)—— ⚠ statement 形式(`parse_match`)与 expression 形式(inline match 在 `parse_expr` 里)是**两份**代码,**都要改**(实测踩过);模式里的 ident 只查**当前**作用域(`symtab_lookup_local`)。门:`spec_match_arm_scope.jhyy` |
| W-150 | — | ~~重名 **fn / type / const / 参数** ⇒ 编译器**空指针写崩溃**(0xC0000005)~~ ✅ **2026-10-27 已修**:与 W-142 同源(`symtab_insert` 对「同 scope 重名」返回 null ⇒ 调用方不检查 ⇒ null 进 AST ⇒ sema 无条件解引用)。user 拍板:这几类是**错误**(不像 `let` 那样 shadowing)⇒ 编译期报 `the name \`f\` is defined multiple times`。新增 `parser_duplicate_name`(报错 + 返回一个**可用**的 sym ⇒ 永不 null)+ 5 个直接插入点加守卫;parser 的 `error_count > 0` ⇒ 驱动直接 `parse errors` + exit 1 ⇒ sema 根本不跑。门:`spec_dup_fn_name.jhyy` / `spec_dup_type_name.jhyy` / `spec_dup_param.jhyy` |
| W-142 | — | ~~同作用域 shadowing 让编译器崩溃**(0xC0000005)~~ ✅ **2026-10-27 已修**:根因链 `parser.jhyy` 的 `parse_let` 调 `symtab_insert` → `symtab.jhyy` 的「重复检查(同 scope)」命中时 **`return 0`** ⇒ AST 的 sym 是 null → sema 无条件 `(*sym).type_ptr = ...` ⇒ **空指针写**。修法:同作用域同名 `let` ⇒ **shadowing**(spec §3 的原承诺已恢复)⇒ 新增 `symtab_insert_or_shadow`(**新建** Sym **原地替换**旧槽 —— 两个要点:复用旧指针 = 先绑定赢;新旧两条都留表里 = 按名查找拿到旧的)。语义与嵌套作用域的 shadowing 完全一致(可改可变性)。门:`spec_shadowing.jhyy`(**XFAIL 已摘**,转真门)+ `spec_shadowing_immutable.jhyy` |
| W-149 | — | ~~整数→浮点 conv 表丢**符号性** + f32 目标拿到 **f64** ⇒ 8 个组合里 5 个错~~ ✅ **2026-10-26 已修**:前端 conv 表(`cg_convert_arg`)对 `u64 → f64` 一律发**有符号**的 `sltof` ⇒ 值 ≥ 2^63 变负数(后端的 `ultof` 算法早就对、**W-146 还修过**,但前端从来没发过它 ⇒ 死代码);且给 f32 目标发 `ultof`/`uwtof` ⇒ 那几个 op 在本后端**恒产 f64** ⇒ f64 位模式塞进 f32 槽。修法:按源类型 prim 判符号性 + f32 目标统一「先转 f64,再 `truncd`」。门:`spec_int_to_float.jhyy`(8 组合矩阵;修前红 `got=234`) |
| W-148 | — | ~~后端 f64/f32 字面量解析**丢掉指数** ⇒ 任何 ≥1e16 的浮点常量都错~~ ✅ **2026-10-26 已修**:`cg_parse_f64_imm_bits` / `cg_f32_imm_bits` 只扫「数字+小数」⇒ 停在 'e' ⇒ `d_9.2233720368547758e+18` 被读成 `9.2233720368547758`(**差 1e18 倍**)。最狠的一处:W-143 的饱和阈值 2^63/2^64 变成 9.22/1.84 ⇒ `3.7 as u32` 饱和到 `u32::MAX`。修法:扫指数段后把整段交给 `atof` |
| W-147 | — | ~~自举闭环门**验错了代** —— 验锚点、装第 1 代 ⇒ 改后端时硬卡死 + 装出坏产物~~ ✅ **2026-10-26 已修**:旧逻辑比的是「锚点编的 .s」vs「锚点编出的 exe 再编的 .s」⇒ 验的是**锚点**的不动点,`mv` 装的却是**没验过**的第 1 代。改成**迭代到不动点**(每轮推进锚点,最多 3 轮;收敛即装 ⇒ 门从「验锚点」升级成「验装出去的产物」;3 轮不收敛 ⇒ 硬失败)。**过渡期自动消化,不需要 escape hatch** |
| W-146 | — | ~~`emit_conv_ultof` 算的是 `2*((x>>1)+(x>>63))` ⇒ **把最低位清零**~~ ✅ **2026-10-26 已修**:`1 → 0.0`、`3 → 2.0` ⇒ u64/指针 → f64 全错。修法:换成标准两分支(`< 2^63` 直接 `cvtsi2sd`;`≥ 2^63` 取低 63 位 + 2^63) |
| W-145 | — | ~~IL lexer 没有 `'u'` 分支 ⇒ `ultof` / `uwtof` 是**死 op**~~ ✅ **2026-10-26 已修**:两个 op 被**嵌套在 `c0 == 's'` 分支**里,而它们以 'u' 开头 ⇒ 永远进不去 ⇒ IL 里一出现就「unknown mnemonic」⇒ 跳 1 字节继续 ⇒ **吐出一串垃圾指令**。修法:`next_token` 加独立 `'u'` 分支 |
| W-144 | — | ~~数组类型的 struct 字段**没被拷贝**~~ ✅ **2026-10-26 已修**:`cg_emit_store` 有 KIND_STRUCT 分支但**没有 KIND_ARRAY 分支** ⇒ 数组字段落到「按标量存一个值」的兜底路径 ⇒ 存进去的是数组的**地址**(字面量读到垃圾 + 按值赋值 AV + `==` 退化成身份比较)。修法:`cg_copy_struct` 改名 **`cg_copy_agg`** 统一处理 struct 与 array(两者互相递归 ⇒ 不能拆)+ `cg_emit_store` 加 KIND_ARRAY 分支 + `NODE_FIELD`/`NODE_INDEX` 对数组返回地址。门:`spec_struct_array_field.jhyy`(**XFAIL 已摘**,转真门) |
| W-143 | — | ~~浮点 ↔ 指针**不是按位重解释**~~ ✅ **2026-10-26 已修**:按 user 拍板改成**数值转换**语义(浮点→指针 = 饱和转 u64 当地址;指针→浮点 = 地址当 u64 数值转浮点;浮点→整数 = **饱和**:区间内向 0 截断 / 越界饱和到 MIN/MAX / NaN → 0)。真根因不是「少发一条指令」:**指针→浮点一条指令都不发** ⇒ 结果 temp 的 qbe_type 仍是 `'l'` ⇒ 流进 f64 形参时 **caller 放整数寄存器 / callee 读 XMM** ⇒ ABI 寄存器类错配。门:`spec_ptr_float_cast.jhyy` + `spec_float_sat.jhyy`(**XFAIL 已摘**,转真门);spec §4.3 已同步 |
| W-139 | — | ~~std lib 的字节循环写 `*(p as *i32) = v` ⇒ store 宽度 4 字节 ⇒ 请求 n 字节实际写 4n 字节~~ ✅ **2026-10-26 已修**:jhyy 的 store 宽度跟 **cast 后的 pointee 类型**走(实测 `*(p as *i32) = 0x41424344` 写 4 字节、`*(p as *u8)` 写 1 字节)⇒ 12 处字节循环的读写统一改成 `*u8` 宽度(mem/fmt/string/vec)。`mem_set(b, 0x41424344, 4)` 修前写 7 字节(踩掉哨兵)修后写 4 字节 ✓ |
| W-140 | — | ~~`std/string.jhyy` 的 `str_find` 返回裸字面量 ⇒ `import string;` 编译失败~~ ✅ **2026-10-26 已修**:`-> i64` 的函数里 `return 0;` 推断成 i32 ⇒ 类型不匹配 ⇒ 改 `return 0 as i64;` |
| W-141 | — | ~~`std/string.jhyy` 的 arena 新建 block 时 payload 起点压在 next 指针上、且 bump 指针不推进 ⇒ 分配互相踩 ⇒ ACCESS_VIOLATION~~ ✅ **2026-10-26 已修**:block 布局改成 `[next(8B)][payload_size(8B)][payload...]`,payload 起点 = `raw+16`,`cur` 推进到 `data_start+size` |
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

**回归现状(2026-10-27 实测,W-142/W-150/W-151/W-152 真修后):257 PASS + 0 XFAIL + 0 failed + 20 SKIP(277 total)**
(新增 49 条门:6 个 std lib 真身覆盖 + 11 个 spec 正向行为 + 31 个错误诊断门 +
1 个聚合比较字段类型矩阵;第二轮再 +1 条 `spec_int_to_float.jhyy`(W-149 的 8 组合矩阵);
`spec_ptr_float_cast.jhyy`(W-143)/ `spec_struct_array_field.jhyy`(W-144)两个 XFAIL
**转真门** ⇒ 剩 1 个 XFAIL = `spec_shadowing.jhyy`(W-142))
(本日早些时候 —— W-126 / W-124 / W-125 修完时 —— 是 186/186 + 0 XFAIL + 19 SKIP / 205 total;
再往前 184/184 + 2 XFAIL + 20 SKIP / 203 total)。本机 Docker Desktop 起 daemon 后
`regress.py --cross=auto` 解析成 **docker** ⇒ **7 个** sysv 用例本地也真跑
(exit=28/217/42/35/18/42/170 全对 —— 新增 `sysv_mixed_int_float`)。
`closure_check.sh` PASS(v2.s == v3.s 逐字节)、`fixed_point.sh` 17 PASS / 0 FAIL
(N=10 .il 与 .s 跨代 byte-equal)、`artifact_checks.sh` **14 PASS** / 0 FAIL
(含 W-130 新增 3 道门)、`audit_test_assertions.py --strict` 0 违规、
`make`(自举闭环门)PASS —— 过渡期自动消化,**再跑一次产物逐字节不变**(幂等)。

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
- W-136 → RESOLVED (2026-10-25, v4.0.21 —— side-file 路径加 **pid 后缀** ⇒ 并发编译互不干扰。A/B 实测:旧编译器 12 路并发**静默丢掉 2/12 的 `#[link_section]` 指令**(2 种不同产物),新编译器 12/12 逐字节相同)
- W-137 → RESOLVED (2026-10-25, v4.0.21 —— `Makefile` 的 `$(CFLAGS_STAGE0)` 未定义(M5 Part 1 改名时漏改两处使用处)⇒ 两个 `.o` 丢掉 `-std=c11 -Wall -Wextra` ⇒ **`-Wcomment` 警告被静默** ⇒ 正是它掩护了 W-136 那次「悬空注释吞掉两个 C 桥符号」的编译期错误)
- W-138 → RESOLVED (2026-10-25, v4.0.21 —— `jh_rename_file` 的 `MoveFileExW` 不带 `MOVEFILE_COPY_ALLOWED` ⇒ **不能跨卷移动** ⇒ 输出路径与 `%TEMP%` 不同盘时**产物不落地**(`W-048: rename temp exe failed`)。本地同盘 ⇒ 一直无感;CI 第一次跑 MCP pytest(commit `2ab0f24` 刚接进 CI)才暴露 —— 那一步用 Git Bash ⇒ `%TEMP%` 在 C:,而工作区在 D:。加 flag ⇒ 跨卷退化成「复制+删除」;新门 `artifact_checks.sh crossvolume_rename`)
- W-134.1 → RESOLVED (2026-10-25, v4.0.21 —— CI 已接 MCP pytest 套件,commit `2ab0f24`;此前台账一直写着 DEFERRED ⇒ **DEFERRED 桶归零**)

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