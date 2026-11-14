# FACTS — 事实单一真相源

> **本文件是仓内唯一记录「会变的数字」的地方。**
> 其它文档**引用**这里的值，**不复述**。
> 复述 = 下一个漂移源（本仓 2026-10-30 审计实测：一个回归数被写在 31 份文档里，
> 结果两份 README 徽章落后 8 个 release 而 CI 全绿）。
>
> **维护**：数字变了先改这里，再改引用它的地方。
> **自动校验**：`python scripts/dev/docs_facts_check.py`（CI 会跑）—— 它把这里的值
> 与 `VERSION` / 台账索引 / 门脚本 / 实际回归输出对拍，不一致就红。

---

## 1. 版本与发行产物

| 项 | 值 |
|---|---|
| 当前版本 | **4.1.5**（真相源 = 仓库根 `VERSION` 文件） |
| **怎么刷版本** | [`docs/internal/build.md` § 版本号自动化](build.md#版本号自动化) —— `bump_version.py set` → `make` → bundle → `finalize` → `check`，**顺序不能反** |
| 最新 release | `v4.1.5`（2026-11-09） |
| 版本轴 | v0.x(C 编译器，冻结于 v1.0.0) · v1.x(自举，终结于 v1.8.3) · v2.x(QBE 重写，终结于 v2.16.0) · v3.x(语言扩展，终结于 v3.4.2) · **v4.x(当前)** |
| 编译器二进制 | `compiler/build/bin/jhyy.exe`（~2 MB） |

| 产物 | 体积 |
|---|---|
| `jhyy-installer-4.1.5.exe` | ~54 MB（GUI 安装器；含 .NET 8 Desktop Runtime + **内置 ucrt64 工具链**） |
| `jhyy-compiler-4.1.5.msi` | ~27 MB（企业 / SCCM 分发；含 `jhyy-setuc.exe` + 内置工具链） |
| `jhyy-lang-4.1.5.vsix` | VS Code 扩展 |

> ℹ️ **体积是实测的** —— `bump_version.py finalize` 量 `installer/build-artifacts/`
> 里的产物后回填（见 [build.md § 版本号自动化](build.md#版本号自动化)）
> ⇒ **别手改这几行**，手改了下次 finalize 会覆盖掉。
> 门 `check_artifact_sizes` 只保证「FACTS 与两份 README 一致」，**不保证为真**
> ⇒ 「为真」由那次实测保证。

> 自 **v4.1.0** 起 installer 自带最小原生 ucrt64 工具链 ⇒ **最终用户不需要 MSYS2**。

---

## 2. 回归与门

### 2.1 事实（会变的数字）

> **本节是这些数字的唯一定义处** —— 下面两节只列「门」,不复述数字。
> 「跨文档一致」由门 `docs-facts` 管;「**为真**」由门 `regress-facts` 管
> （它拿 `regress.py` 的实测计数对拍本节）⇒ 两者合起来才是「事实单一真相源」。

| 项 | 值 |
|---|---|
| `python regress.py` | **281 PASS + 0 XFAIL + 0 failed + 20 SKIP**（301 total） |
| 断言强度审计 | `python scripts/dev/audit_test_assertions.py --strict` —— 扫描 301 · 可跑 281 · 真断言 217 · literal-return-ok 8 · expect-error 56 · skipped 6 · library 14 · **零信号 0** |
| 产物级门数 | `artifact-checks` —— **23 道**（`check_*` 函数数） |
| 产物级门 KNOWN-FAIL | **0** 条（当前没有预期失败的门 —— 每道门都该自己绿） |

### 2.2 CI 门（完整清单）

> **本表是仓内「门」的完整清单** —— [`CONTRIBUTING.md`](../../CONTRIBUTING.md) 让读者来这里找。
>
> **每道 CI 门在 workflow 里都带一个 `# gate: <id>` 标记** —— 门 `docs-facts` 的第 J 项
> 按它**双向**对拍:workflow 里跑了却没登记 ⇒ 红;登记了却没在 workflow 里跑 ⇒ 红;
> workflow 里新加一个带 run 块的步骤却没分类（既不是门也没登记为非门）⇒ 红。
> **每道门跑的是哪些脚本**也要与「在哪跑 · 跑什么」那一列对得上 ⇒
> 「在别的门的步骤里偷偷加一道新门」是看不见的。
>
> ⚠️ **改 workflow 或这张表时,两边一起改** —— 否则 J 项会红。

| 门 | id | 查什么 | 在哪跑 · 跑什么 |
|---|---|---|---|
| 自举闭环（构建期） | `selfhost` | jhyy.exe 能把自己编成同一个东西（迭代到不动点）；产物与提交进仓的那份逐字节对照（发布者视角） | ci.yml · build-and-test · `make` |
| 提交产物同步 | `artifact-fresh` | 提交进仓的那份 jhyy.exe 对当前源码的**行为** == 现编产物（比 `.s`，不比 `.exe`） | ci.yml · build-and-test · `bash compiler/tests/bootstrap/artifact_fresh_check.sh` |
| 全量回归 | `regress` | 每个用例的退出码 / stdout 断言 | ci.yml · build-and-test · `python regress.py --all` |
| 回归事实对拍 | `regress-facts` | § 2.1 的数 == 本轮**实测**数（缺摘要即红） | ci.yml · build-and-test · `python scripts/dev/check_regress_facts.py tmp/regress-summary.json` |
| 断言强度 | `assert-strength` | 每个用例都有能失败的断言（零信号即红）**＋ 指令 ⇄ 读点对照**（测试里用到的每条指令都必须在 harness 里有读点；harness 里解析了却没登记的指令 ⇒ 死指令，红） | ci.yml · build-and-test · `python scripts/dev/audit_test_assertions.py --strict` |
| 产物级门 | `artifact-checks` | **23 道**产物级断言（expected-FAIL 模型） | ci.yml · build-and-test · `bash compiler/tests/bootstrap/artifact_checks.sh` |
| 交叉环境准备 | `sysv-emit` | 交叉环境那几份 `.s` 一份都不能少 | ci.yml · build-and-test · 内联 shell |
| 运行时性能 | `perf` | 静态指标硬门（指令数 / 访存 / 帧大小 / chkstk；墙钟只报告） | ci.yml · build-and-test · `python scripts/dev/bench/runtime_perf.py --ci` |
| 基准套件 | `bench-perf` | 每道基准题的 stdout 与 gcc 逐字相同 + 二进制体积不回归 + 静态指标不回归（墙钟只报告） | ci.yml · build-and-test · `python bench/bench.py --ci` |
| 差分对拍 | `bench-diff` | 随机程序 · C 与 jhyy 的 stdout 逐字节相同 + 行为不回退（金标准）；只红在输出不一致 / 运行时崩溃 | ci.yml · build-and-test · `python bench/difftest.py --seeds bench/seeds/ci.txt --ci` |
| 内置工具链 | `toolchain` | 可重定位 / 头闭包 / poisoned PATH / windres | ci.yml · build-and-test · `powershell -File installer/scripts/collect-toolchain.ps1` + `powershell -File installer/scripts/verify-toolchain.ps1` |
| VSCode bash 探测 | `vscode-bash` | 扩展的 terminal profile 指向一个真实存在的 bash | ci.yml · build-and-test · `powershell -File installer/scripts/verify-vscode-bash-detect.ps1` |
| MCP 套件 | `mcp-pytest` | MCP 工具坏了 ⇒ CI 红 | ci.yml · build-and-test · `python -m pytest mcp-jhyy/tests` |
| 版本零漂移 | `version` | `VERSION` == 全仓每一处版本串（含两份 README 的徽章） | ci.yml · build-and-test · `python scripts/dev/bump_version.py check` |
| 文档事实 | `docs-facts` | 事实 / 链接 / 反引号裸路径 / `§ N.M` 章节引用 / 台账正文 / `feedback_*` 代号索引 / **门清单 ⇄ CI 实况** | ci.yml · build-and-test · `python scripts/dev/docs_facts_check.py` |
| 事实链变异测试 | `docs-mutation` | 给事实链注入**故意的错误**，逐个确认它会红 ⇒ 证明门看得见 | ci.yml · build-and-test · `python scripts/dev/test_docs_gate_mutations.py` |
| 三规范一致性 | `spec-consistency` | 三份规范的 `Cap<T>` wire 布局一致 | ci.yml · build-and-test · `python scripts/dev/check_spec_consistency.py` |
| `.jhyynb` 布局算术 | `binary-layout` | 每个 struct 的声明尺寸 == 自然对齐算出来的尺寸，无隐式 padding | ci.yml · build-and-test · `python scripts/dev/check_binary_format_layout.py` |
| 架构断言 | `arch-claims` | `architecture.md` 的结构性断言与源码一致 | ci.yml · build-and-test · `python scripts/dev/check_arch_claims.py` |
| 寄存器分配对拍 | `regalloc-parity` | Python 参考实现与编译器侧的分配数**逐项相同**（两套独立实现） | ci.yml · build-and-test · `python scripts/dev/check_regalloc_parity.py` |
| VSCode grammar | `vscode-grammar` | grammar == 语言真实规则 | ci.yml · vscode-ext · `node vscode-ext/scripts/check-grammar.mjs` |
| 语言构成 | `langstat` | 语言构成的产物（图表 + 本文件 § 7 + 两份 README 的数）与**当前源码树**一致 | ci.yml · build-and-test · `python scripts/dev/langstat.py --check` |
| SysV ABI | `sysv-abi` | 链 + 跑 + 比 `// EXPECT:` | ci.yml · sysv · `bash compiler/tests/bootstrap/sysv_link_run.sh` |
| SysV 跨实现对拍 | `sysv-cross` | jhyy ↔ gcc 能否互调（W-104） | ci.yml · sysv · `bash compiler/tests/bootstrap/sysv_abi_cross.sh` |
| 发布：版本 == tag | `release-version` | `VERSION` 文件与 tag 不符 ⇒ 拒发 | release.yml · 内联 pwsh |
| 发布：CI 绿 | `release-ci-green` | **手动发布**路径下，对应 tag 的 CI run 必须是 success（tag 路径由 ci.yml 的 `needs:` 保证；手动路径此前完全绕开 CI ⇒「门没跑就发」在机制上可行） | release.yml · 内联 pwsh（GitHub API） |
| 发布：产物与提交版同源 | `release-anchor` | release 自己那次 make 编出的 jhyy.exe 与**提交进仓的那份**对同一份 src0 产出的 `.s` 逐字节相同（比 `.s` 不比 `.exe` ⇒ 跨 toolchain 不假阳性） | release.yml · `bash compiler/tests/bootstrap/artifact_fresh_check.sh` |
| 发布：构建产物 | `release-build` | Burn bundle + MSI + `.vsix` 构建成功 | release.yml · `pwsh -File installer/build.ps1 bundle` |
| 发布：SHA256 | `release-sha256` | `SHA256.txt` 与产物逐一对得上 | release.yml · 内联 pwsh |
| 发布：release notes | `release-notes` | 没填的占位符 ⇒ 拒发 | release.yml · 内联 pwsh |
| 发布：MSI 校验 | `release-msi` | `wix msi validate` | release.yml · 内联 pwsh |
| 发布：产物齐全 | `release-artifacts` | 该有的产物一个不能少（dry-run 门） | release.yml · 内联 pwsh |

### 2.3 本地门（opt-in，需手工跑）

> 这些门**不接 CI** —— 要么太慢、要么需要特定环境。
> 触发时机写在最后一列。**接进 CI 前先把它移到 § 2.2**（门会查）。

| 门 | id | 查什么 | 怎么跑 / 何时跑 |
|---|---|---|---|
| 跨代闭环 | `closure-check` | Stage2 的 `.s` == Stage3 的 `.s`（`compiler/tests/bootstrap/closure_check.sh`，带非空守卫） | `bash compiler/tests/bootstrap/closure_check.sh` · 改 `src0` 之后 |
| 跨代 fixed-point | `fixed-point` | N=10 跨代 `.il` + `.s` byte-equal（`compiler/tests/bootstrap/fixed_point.sh`） | `python regress.py --fixed-point` · 改 `src0` 之后（发版级流程） |
| 字节三件套 | `byte-equal` | `.il` / `.s` / `.exe` 三层 byte-equal | `python regress.py --byte-equal` · 跨版本对拍时 |
| 差分全量 | `bench-diff-full` | 32 个种子的**全量模式** —— W-185 / W-186 修好后**已知缺陷清单已清空** ⇒ 全量模式 ≡ 规避模式,只剩「有没有新缺陷」这一问 | `python bench/difftest.py --seeds bench/seeds/all.txt --mode full --ci` · 定期跑 |

> **为什么「跨代闭环」是本地门而不是 CI 门**(2026-11-03 审计):
> CI 里那道闭环由 `make` 自己兜 —— `$(BIN_DIR)/jhyy.exe` 规则**迭代到不动点**,
> 收敛的那一代就是装出去的那一代 ⇒ 「装出去的那个产物在不动点上」当场被证过。
> 再单独跑一遍 `closure_check.sh` 只是**复述同一个结论**(恒绿 ⇒ 是噪音不是门)。
> ⚠️ 2026-11-03 同时给 `make` 的那段循环**补了非空守卫** ——
> 此前 `cmp -s` 比两个**空文件**也判「相同」⇒ 编译器「静默 exit 0 但不产 .s」
> 时会假绿(`closure_check.sh` 一直有守卫,只有构建期那段没有)。


---

## 3. workaround 台账

| 项 | 值 |
|---|---|
| 台账 | [`docs/internal/workarounds.md`](workarounds.md) —— **永不归档** |
| 条目总数 | **223** |
| ACTIVE | **0** |
| DEFERRED | 1 |
| RESOLVED / SUPERSEDED / INVALID | 200 / 19 / 3 |

---

## 4. v4.x 排期

> 版本号是**预留号** —— 启动那一格时按当时的实际状态复核（每份 plan 自带「启动时复核清单」）。
> 稳定身份是 **OS-N** 序号。

### 4.1 性能线（自研后端 —— 当前主线）

| 版本 | 内容 | 状态 |
|---|---|---|
| **v4.4.0** | **寄存器分配 ①**：位置映射 + 前瞻窗口缓存（**阶段二 = emit 层消费寄存器**） | 🔄 下一版 |
| v4.4.1 | 寄存器分配 ②：call-clobber + 寄存器类 | 🔴 预留号 |
| v4.4.2 | 寄存器分配 ③：跨基本块 + phi 并行移动 | 🔴 预留号 |
| v4.4.3 | 寄存器分配 ④：门 + perf 验证 + 去文本耦合 | 🔴 预留号 |
| v4.4.5 | peephole 4096 真修 + IR 优化框架（v4.2.2 / v4.3.0 降级而来） | 🔴 预留号 |
| v4.5 | M5 Part 3（0-C 闭环 —— 最后一项）· **阶段 0：std API 收口 + 缺口补齐**（2026-11-02 新增；**阶段 0 不依赖 v4.4** ⇒ 可与性能线并行） | 🔴 预留号 |

> v4.4.0 **阶段一**（寄存器分配器 + 安全网，产物逐字节不变）已于 2026-10-30 完成。
> 已 ship 的 v4 sprint 计划（v4.0.0 … v4.0.7）见 [`docs/archive/plans/v4/`](../archive/plans/v4/)
> —— v4.1.x / v4.2.x **没有**独立的 `-plan.md`（内容记在 [`CHANGELOG.md`](../../CHANGELOG.md)
> 的 release / change slot 表，以及性能线总纲里）。

### 4.2 测评线（v4.3.x —— 发版前）

| 版本 | 内容 | 状态 |
|---|---|---|
| **v4.3.0** | **测评套件地基**：`bench/` 目录 + 基准门 + 口径（METHODOLOGY.md） | ✅ 已完成 2026-11-03 |
| v4.3.1 | 3 道新题（partial_sums / mandelbrot / binary_trees）+ 测量地板口径 + 附录 B 剩余覆盖缺口 | ✅ 已完成 2026-11-03 |
| v4.3.2 | 3 道浮点 / 字节变换新题（revcomp / nbody / spectral）+ 浮点位模式探针 | ✅ 已完成 2026-11-03 |
| v4.3.3 | 随机程序差分测试器 + 差分门 `bench-diff` + 金标准 | ✅ 已完成 2026-11-03 |
| v4.3.4 | 对外基线快照 + 两份 README 同步 + release notes | ✅ 已完成 2026-11-04（随 release `v4.1.3` 发布） |
| v4.3.5 | `fmt_i64` 的 i64::MIN 缺陷（动 src0 ⇒ 走发版级流程） | ✅ 已完成 2026-11-04（W-195） |

> **为什么排在 v4.4 之前**：测评线要在**发版前**完成 ⇒ 编号在 v4.4 之前。
> v4.3.0 原本是「IR 优化框架 + `-O` 开关」，2026-10-29 因实测价值 ≈ 1.8% 而
> **降级到 v4.4 之后**（IR 优化框架已并入 v4.4.5）⇒ 号码空出。
> ⚠️ **静态指标基线绑定编译器版本** ⇒ v4.4.x 的寄存器分配落地后必须重取一次。
>
> **测评线整格随 release `v4.1.3`（2026-11-04）收口** —— v4.3.4 的「对外基线快照 + 两份
> README 同步 + release notes」是那次发布本身的收尾动作 ⇒ 它没有独立的 tag / 产物
> （release 记录见 [`CHANGELOG.md`](../../CHANGELOG.md) 的 v4.1.3 行）。
> ⇒ **下一格 = 性能线 v4.4.0**（寄存器分配①阶段二 —— emit 层消费寄存器）。

### 4.3 OS 线（v4.6 → v4.15）

| 版本 | OS-N | 内容 |
|---|---|---|
| v4.6 | OS-1 | 止血包 |
| v4.7 | OS-2 | 观测（栈上界） |
| v4.8 | OS-3 | 反馈环（最小 kernel.efi） |
| v4.8.5 | OS-4 | 栈与分配 |
| v4.9 | OS-5 | ABI 收敛 |
| v4.10 | OS-6 | 语言自洽（块表达式 / `fn` 类型位置 / 闭包捕获 / `()` 类型位置 / defer 覆盖末表达式 / 结构化内联汇编 / **编译期格式化宏 `println!`** —— 2026-11-02 新增） |
| v4.10.5 | OS-7 | 效果最小集 |
| v4.11 | OS-8 | lifetime |
| v4.12 | OS-9 | trait + `dyn Trait` |
| v4.12.3 | OS-10 | const generic |
| v4.12.5 | OS-11 | HKT（一阶） |
| v4.13 | OS-12 | 效果骨架 + 锁序 |
| v4.13.5 | OS-13 | 对象模型冻结（manifest） |
| v4.14 | OS-14 | 能力类型化（`Cap<T>` 真 T） |
| v4.14.5 | OS-15 | 内核数据结构（RCU / PerCpu） |
| v4.15 | OS-16 | 可信工具链（KASAN / KCFI） |

### 4.4 未排期（v4.16 起）

async/await · 包管理器 · 并发 cap + 完整 memory model · 多架构 ABI
—— **不预先落文档**，启动时再领版本号。

### 4.5 第三方包管理上游发布（**2026-11-07 随 v4.1.4 发出去 · 2026-11-09 随 v4.1.5 跟上**）

| 渠道 | 状态（2026-11-09） |
|---|---|
| winget-pkgs | **PR 已提交**（**#475435**，`JiHuiYiYou/winget-pkgs` 的 `jh-4.1.5` 分支）—— 4.1.4 的 #473726 **已关闭**（被 4.1.5 取代）。`InstallerSha256` 按**已发布**的资产回填（本地构建那个不算数：MSI 含时间戳，两边差一整个）。本机 `winget validate` **验证成功** ✓。**CLA 已签**（2026-11-07 在 #473726 上回 `agree`，账号级 ⇒ 覆盖之后所有 PR）⇒ 现在只差**社区版主审批**（`mergeStateStatus: BLOCKED`，检查全绿）。**上游合并前 `winget install` 还装不上** |
| scoop | **个人 bucket 已上线**（`JiHuiYiYou/scoop-bucket` 的 `bucket/jhyy.json`）—— 按本仓 2026-11-05 的决定：**先走个人 bucket**，Main bucket 另议（装法：`scoop bucket add jhyy https://github.com/JiHuiYiYou/scoop-bucket`）。4.1.5 已回填（版本 + 已发布资产的 sha256）✓ |
| 仓内 manifest | **已修好 + 已随版发布** —— 4.1.5 的三件套 + scoop 的 `checkver` / `autoupdate` 正则对着线上 tags 页与 SHA256.txt **实测命中**（autoupdate 的正则从已发布的 SHA256.txt 里取出的 hash 与 bucket 里写的**逐字相同** ✓）。**1.5.5 / 1.5.6 是历史占位符**（那两次 release 的资产已 404 ⇒ sha256 填不上 ⇒ 天生不可发布，保留原样） |

> ⚠️ 别把这一格跟 § 4.4 的「包管理器」混为一谈 —— § 4.4 说的是**语言层面**的
> 包管理器（`jhyy new/build/test` + `jhyy.toml`），这一格说的是**发行渠道**。
>
> 背景：v1.5.5 的决策是「**写 manifest，实际 publish 推到 v2.x**」—— 而 **v2.x 轴
> 早已终结**（v2.16.0）⇒ 这个决定**从来没被执行**，manifest 就一直躺在仓里当
> reference；而且它们**还是坏的**（version/installer 装反、scoop 脚本用 `//`
> 注释）⇒ 台账 **W-203 / W-204**。
> ⇒ **2026-11-07 补上这一格**：manifest 修好（2026-11-05）→「什么时候提」
> 等了两个月 → 随 **v4.1.4** 一起把 PR 提了、bucket 建了。
> ⇒ 顺带挖出并修掉**发版工具自己的三个缺陷**（W-218 / W-219 / W-221）——
> **都是「提 PR 前最后一次跑发版流程」才暴露的**。

---

## 5. 目标三元组

| 三元组 | 含义 |
|---|---|
| `amd64_win` | x86-64-w64-mingw32（默认，hosted Windows） |
| `amd64_win_freestanding` | x86-64-w64-none（UEFI） |
| `amd64_sysv` | x86-64-linux-none |
| `amd64_sysv_freestanding` | x86-64-linux-none-freestanding |

---

## 6. 引用本文件的方式

**正确**（从 `docs/` 下的子目录引用）：

```markdown
回归基线见 [`../internal/FACTS.md`](../internal/FACTS.md) § 2。
```

**错误**（复述 = 下一个漂移源）—— ⚠️ 下面这段是**故意写错**的示范,不要照抄：

```markdown
（反面例子 —— 故意写错,不要照抄）
回归 259 PASS + 0 XFAIL + 0 failed + 20 SKIP（279 total）。
```

例外：**仓库门面**（`README.md` / `README.zh-CN.md`）可以在「Status」段直接给数字 ——
但那里的数字由 `docs_facts_check.py` 一并对拍。

---

## 7. 语言构成

<!-- langstat:begin —— 这一节由 `scripts/dev/langstat.py` 生成，别手改 -->

| 语言 | 代码行 | 占比 | 文件数 |
|---|---|---|---|
| JHYY | 37045 | 67.8% | 377 |
| Python | 10995 | 20.1% | 42 |
| Shell | 2566 | 4.7% | 20 |
| PowerShell | 1900 | 3.5% | 20 |
| C | 1315 | 2.4% | 13 |
| C# | 287 | 0.5% | 1 |
| Assembly | 225 | 0.4% | 6 |
| Batchfile | 137 | 0.3% | 4 |
| JavaScript | 125 | 0.2% | 1 |
| TypeScript | 65 | 0.1% | 1 |
| **合计** | **54660** | **100%** | **485** |

> 口径：**代码行数**（非空、非纯注释）；文件清单取自 `git ls-files`
> ⇒ 生成物与 vendored 代码自动被 `.gitignore` 排除（不维护第二份排除清单）。
> **`.jhyy` → JHYY 这条映射是 GitHub Linguist 没有的** —— Linguist 不认这门语言，
> 所以 GitHub 侧栏那个语言条里，编译器真正的实现**一行都不出现**。
<!-- langstat:end -->


## 8. IDE 知识包与「模型写 JHYY」评测

> **这是 IDE 仓（`JiHuiYiYou-IDE`）内嵌的 Claude Code 会话用的两样东西**：
> 一份**常驻知识包**（从本仓的规范 + 标准库源码生成），和一套**评测**
> （把「模型写 JHYY 代码」变成可测量的数字）。数字只写在这里。

### 8.1 知识包（常驻进 IDE 会话）

| 项 | 值 |
|---|---|
| 生成器 | `scripts/gen-knowledge.py`（改规范/标准库后重跑） |
| 产物 | `docs/generated/jhyy-knowledge.md`（+ 同名 `.json`） |
| 规范章节目录 | **25** 章 |
| 反直觉点（规范里带 ⚠ 标记的行） | **58** 条 |
| 附录 B「未实装」 | **15** 项 |
| 附录 B「已实装但受限」 | **19** 行 |
| 标准库公开 API | **8** 模块 / **45** 个函数（**含各模块 `// API:` 块里的用法注**） |
| **常用用法（能编译）** | **2** 段 —— **每个都真编译过**（编译不过 ⇒ 生成器报错） |
| 知识包体积 | 约 **19.4k** 字符 |

> ⚠️ **标准库 API 表以源码的 `// API:` 块为准**，**不抄规范 § 15 那张表** ——
> 实测那张表把 fmt 的内部 helper（`digit_char` / `hex_char`）和一个根本不是
> stdlib 函数的 `ptr_add` 也列成了「公开 API」（它们确实能编过，不是 bug，
> 但会误导用户去调内部实现）。

### 8.2 评测

> ⚠️⚠️ **口径订正（2026-11-13）** —— **本节此前报出的轮数 / 正确率
> 混进了基础设施故障**，凡是引用它们的结论都要打折看。
>
> | 故障 | 症状 | 影响 |
> |---|---|---|
> | **超时太短** | harness 默认超时 **300 秒** ⇒ 每个臂都有 **6~8/29 题**被掐断（答案停在半路） | 那些题的 `finalPass=False` 是「**被掐断**」，不是「模型没写对」 |
> | **API 500** | `API Error: Internal server error. Please retry (500)` ⇒ 模型根本没机会做完 | 同上 |
>
> ⇒ **具体后果**：「**hook 让正确率掉 10%**」这个结论**完全是超时造成的假象** ——
> hook 臂退步的 5 题里 **3 题是被掐断的**（另 2 题是最难的 `mask-change`）。
> ⇒ **轮数 / 成本**的数字受影响较小（掐断的题轮数偏**少** ⇒ 实测的 hook 优势
> **被低估**了）。
>
> ⇒ **现在**：
> - 默认超时 **900 秒**
> - 超时 / API 错误 / usage 缺失 ⇒ **自动重试**（默认 2 次，即最多跑 3 遍）
> - JSONL 里记 `timedOut` / `apiError` / `attempts`
> - 汇总**多打一行**「只算跑完的 N 题」⇒ **基础设施故障不再算模型的锅**
> - 逐题对比工具：IDE 仓 `JiHuiYiYou-IDE/scripts/eval/diff-arms.py`（**掐断的题单列**）

**⚠️ 轮数不是「改代码」多，是「调工具」多** —— 这是评测测出来的最重要的一件事：

| run | 首过 | **改代码版数** | 通过后还在改 | **平均轮数** | **总工具调用** |
|---|---|---|---|---|---|
| 旧（无错误索引 / 无检索改造 / 无知识包） | 21/29 | **1.8** | 0.0 | 17.7 | 391 |
| + 错误索引 + 检索改造 | 24/29 | 1.9 | 0.0 | 12.6 | 436 |
| + 知识包 | 23/29 | 2.0 | 0.0 | 12.2 | 434 |

⇒ **每题只改 1.8~2.0 版代码，却花了 12~17 轮** ⇒ 轮数的 85%+ 是**工具调用**。

**工具调用分布**（29 题）：

| 类别 | 旧 | +错误索引 | +知识包 |
|---|---|---|---|
| **探索**（ls/grep/find） | 55 | 67 | 69 |
| **跑程序**（`jhyy_run`） | 56 | 70 | 67 |
| **读文件** | 42 | 47 | 55 |
| 查规范（`jhyy_lang_ref`） | 53 | 32 | **32** |
| 查台账（`jhyy_workarounds`） | 35 | 36 | **20** |
| 改代码 | 45 | 58 | 58 |
| 找工具（ToolSearch） | 34 | 35 | 37 |

⇒ **知识包确实让模型少查资料**（查规范 −40%、查台账 −43%）⇒ 这是它的真实价值；
但它多花了别的轮次（探索 +25%、读文件 +31%）⇒ **净轮数没降**。
⇒ **最大的单点优化不是知识包，是「让模型少跑、少探索」** ——
「探索 + 读 + 跑」= **178 次**，这正是 **PostToolUse hook 能自动化的**
（模型写完 ⇒ IDE 自动编译 ⇒ 诊断直接进上下文 ⇒ 不用自己跑、自己看）。

⚠️ **以上都是 n=1** ⇒ 是**方向**不是结论（同一个任务跑两次轮数差 25% 完全可能）
⇒ 要下结论得 n≥3（harness 支持 `--repeat N`，取中位数）。

| 项 | 值 |
|---|---|
| harness | IDE 仓 `JiHuiYiYou-IDE/scripts/eval/run-eval.ts`（`npm run eval`） |
| 任务集 | IDE 仓 `JiHuiYiYou-IDE/eval/tasks.json` —— **32** 道 |
| 变异种类 | **8** 种（其中速查表**没覆盖**的 3 种 + 1 种行为变异） |
| 破坏方式 | **2** 种：`compile-break`（编译不过）/ `behavior-break`（能编但行为变了） |
| 判据 | 编译通过 **且** 退出码一致 **且** stdout **逐字**一致 |
| 基线臂 | `baseline` = IDE 现状（12 条速查 + jhyy MCP） |

**基线数字**（32 道题 × 1 次；模型 = 本机 provider 的 MiniMax-M3.1-Flash）：

| 臂 | 配置 | 首次写对 | 总轮数 | 中位轮数 | 总成本 | 调编译器 |
|---|---|---|---|---|---|---|
| **A** | 现状：12 条速查 + MCP | 32/32 | **527** | 15.0 | $16.56 | 17/32 |
| **B** | 知识包（无工具速查） | 32/32 | 462（−12%） | 10.5 | $15.50（−6%） | 13/32 |
| **C** | 知识包 + 工具速查 | 32/32 | 434（−18%） | 11.0 | $16.52（−0%） | 12/32 |
| **D** | C + 收紧范围的题目措辞 | 32/32 | **368（−30%）** | **9.0** | **$14.78（−11%）** | **6/32** |

⇒ **D 最优**：轮数 −30%、成本 −11%、**「模型自己去编译」的次数 17 → 6**。

**轮数花在哪（轨迹归因，IDE 仓 `scripts/eval/analyze-turns.ts`）**：

| 大类 | A（495 次调用） | D（324 次调用） |
|---|---|---|
| 验证（编译 + 跑程序） | 155（31%） | 95（29%） |
| 查资料（规范 + 台账） | 109（22%） | **39（12%）** |
| 读/探索 | 109（22%） | 78（24%） |
| 改代码 | 78（16%） | 52（16%） |
| **找工具（ToolSearch）** | 40（8%） | **60（19%）** |

⇒ **三条结论**：

1. **正确率没有提升空间** —— 基线在规则级题目上已经 100%。
2. **知识包的价值在「少查资料」**（109 → 39），**不在正确率**。
3. **ToolSearch 是「机制开销」不是「知识开销」** —— 臂 A 的 40 次是**空查询**（盲搜），
   臂 D 的 60 次是**精确的 `select:mcp__jhyy__jhyy_check`**（模型知道要哪个，但工具没被装载）
   ⇒ **知识包里的工具速查治不了它**；写全 `--allowedTools` 的工具名也只从 1.25/题降到 1/题
   ⇒ **要消掉它只能靠 IDE 侧的 PostToolUse hook**（模型压根不用调 MCP 工具 ⇒ 装载也不需要）。

### 8.3 语言对照组 —— **同样的实现，大众语言 vs 小众语言**

语料：语言仓 `bench/difftest.py` 的随机程序生成器 ⇒ **同一个 AST** 发出
C（`emit_c`）和 JHYY（`emit_jhyy`）**两个实现**，再对两者施加**平行变异**
（入口名写错 / 少声明 / 格式符错 / 掩码改了）。
⇒ **同一个算法、同一批数、同一类错、同一份期望输出，只有语言不同**。

**29 对**（IDE 仓 `eval/tasks-paired.json`）：

| 指标 | C | JHYY | 差 |
|---|---|---|---|
| 平均轮数 | **9.8** | **10.1** | +2% |
| 平均工具调用 | 13.0 | 13.5 | +4% |
| 总成本 | $11.7 | $12.3 | +5% |
| 最终写对 | 21/29 | 21/29 | 0 |
| 逐对方向 | — | — | JHYY 更费 11 · 更省 11 · 持平 7 |
| **调编译器** | **28/29** | **11/29** | **−17** |

**按变异分组（平均轮数）**：

| 变异 | C | JHYY | 差 | 说明 |
|---|---|---|---|---|
| `entry-name` | 13.5 | **8.5** | **−5.0** | 入口名这条规则 **JHYY 反而更省** —— IDE 有 jhyy MCP + 速查表 + 知识包 ⇒ 模型**直接知道**，不用编译验证 |
| `missing-decl` | 11.9 | **17.3** | **+5.4** | 少声明：gcc 直接说 `implicit declaration of function 'printf'` ⇒ 一轮够；JHYY 只说「undefined variable printf」⇒ **模型得自己查规范** |
| `wrong-format` | 9.4 | **17.2** | **+7.8** | printf 的格式符：gcc 会警告类型不匹配；JHYY 要先知道 `printf` 的签名是 `val: i64` |
| `mask-change` | 4.4 | — | — | JHYY 侧数据不全（多次中断） |

⇒ **结论**：

1. **JHYY 的「多绕」不是语法难** —— 总体只比 C 多 2% 轮数，正确率完全一样。
2. **是「API 语义不熟 + 编译器报错不自带修复线索」** ⇒
   知识包该做的**不是教语法**（模型已经会），而是
   **把 API 语义（stdlib 签名/用法）和「编译器报错 → 该改哪」直接给出来**。
3. **JHYY 侧「调编译器」只有 C 侧的一半（11/29 vs 28/29）** ⇒
   模型**凭知识直接改**了（知识包给了它自信）⇒ **效率更高，但少了编译器兜底**。
   ⇒ ⇒ **这正是 PostToolUse hook 的最佳论证**：
   让模型既保留「凭知识直接改」的效率，又**自动有编译器兜底**（不用自己花轮次去编译）。

⚠️ **n=1**，且 `mask-change` 那组 JHYY 侧数据不全（多次中断）⇒ 方向，不是结论。

> ⚠️ **单次结果不可信** —— Claude Code CLI **没有 seed flag** ⇒ A/B 必须
> **n≥3 次重复取中位数 + 报离散度**。任何「提升 X%」的说法不带离散度都是噪音。
>
> ⚠️ 成本数字是**本机实测**（provider 走 MiniMax-M3.1-Flash）⇒
> 换模型/换供应商要重测；报告里必须写明当时的模型 id。

### 8.4 「编译器报错 → 该改哪」索引（MCP 工具 `jhyy_error_lookup`）

| 项 | 值 |
|---|---|
| 工具 | `jhyy_error_lookup`（MCP 侧 `mcp-jhyy/jhyy_errors.py`） |
| 索引条数 | **169** 条（编译器源码 + 规范 § 18 + 附录 B + 语料实测 + 台账 + **人工校订层**） |
| 数据来源 | 全部**只读**：静态扫描 `compiler/src0/*.jhyy`、规范 § 18 / 附录 B、56 个 `EXPECT-ERROR` 用例的实测报错、台账 |
| 回归门 | `mcp-jhyy/tests/test_error_lookup.py`（10 个测试，含**走 server 层**的那条） |
| 单条查询 | `jhyy_errors.lookup(msg)` —— 比 `search()` 严格（**只认高置信匹配**，无关查询返回 `None`） |
| 校订层 | `CURATED_FIXES`（12 条）—— **手写**「怎么改」，覆盖自动条目 |

⚠️ **为什么要加「人工校订层」** —— 自动扫出来的 169 条里
**`fix` 只有 20 条、`meaning` 只有 77 条** ⇒ 模型拿到诊断**大概率还是不知道该改哪儿**。
而评测量出来的诊断面**极小**（29 道配对任务里只有 **1 种**结构化诊断
+ **1 种**链接期失败）⇒ ⇒ **为最高频的那几条手写「怎么改」是划算的**。

⚠️ **校订层只覆盖**评测里真出现过的（`undefined variable` / `type mismatch in let` /
`unexpected token ';'`）+ 速查表里的铁律（入口名 / `as` / `import` / 闭包捕获 / 类型标注 …）
⇒ **它是补丁不是主体** —— 主体仍是那 169 条自动条目。

**为什么有它** —— 语言对照（29 对）测出来的：「少声明」「格式符错」这两类在 JHYY 上
**多 5~8 轮** ⇒ 根因是 **C 的编译器报错自带修复线索**
（`implicit declaration of function 'printf'`），而 JHYY 只说
「undefined variable printf」⇒ 模型得自己查规范才知道怎么改
⇒ 这个索引做的就是那一步翻译。

**⚠️ 不改编译器** —— 改 `compiler/src0/*.jhyy` 的逻辑会移位模块级 temp 编号
⇒ 自举产物漂移 ⇒ 要走全量 regress + `make` 刷锚点 + 三个 closure 门
⇒ 索引**只读**编译器源码。

**顺带修的三处**（`jhyy_workarounds.py`）：
- `根因` alias 缺失 ⇒ 台账里 134 条用 `**根因:**` ⇒ 它们的 root_cause 解析成空串
  ⇒ 修完**有 root_cause 的条目从 17 条涨到 150 条**、failure_condition 124 条
  （错误索引靠台账关联 ⇒ 关联面直接变大）
- `search()` 只透出 9 个字段（丢了 `fix`/`verify`/`failure_condition`/`reference`）
  ⇒ 补到 14 个
- 每次调用重读 1 MB markdown ⇒ 加 **mtime 缓存**（实测 0.107s → 0.0006s）

### 8.7 hook 的净效果 —— **轮数可靠，正确率 n=1 测不出**

**两个臂**（同一批 29 道配对 JHYY 任务、`knowledge` 臂、只差「装不装 PostToolUse hook」）：
A = IDE 现状（知识包 + MCP），B = A + hook。

**两次独立测量**（同一配置、同一批题，各自跑一遍）：

| | 测量① | 测量② |
|---|---|---|
| **正确率**（A → B） | 26/29 → 27/29（**+1**） | 27/29 → 22/29（**−5**） |
| **总轮数**（A → B） | **−73（−20%）** | **−53（−10%）** |
| **总成本**（A → B） | **−25%** | **−7%** |
| 跑挂（超时 / API 错误） | 0/29 | **0/29**（重试机制生效） |

⇒ ⇒ **两条结论，置信度完全不同**：

1. **轮数：hook 实打实省 10~20%** —— 两次独立测量**方向一致、量级相近**
   ⇒ 这条**可以拿来决策**。
2. **正确率：测不出来** —— 一次 +1、一次 −5 ⇒ **n=1 的噪声就是 ±5 题**
   ⇒ ⇒ **此前报出去的「hook 让正确率掉 10%」这种结论一律作废**
   （它同时被超时截断**和**噪声污染过）。

⇒ ⇒ **⚠️ 最刺眼的一条**：**同一个配置（同一个臂、同一批题）跑两次，
正确率差 5 题**（22/29 vs 27/29）⇒ ⇒ **⇒ 任何 n=1 的正确率对比都不可信**
⇒ 要下正确率的结论得 **n≥3 取中位数**（一次臂 ≈ $32 ⇒ n=3 两臂 ≈ $190）。

**hook 省下来的到底是什么**（测量②的工具调用分布）：

| 类别 | A | B | 差 |
|---|---|---|---|
| **探索**（ls/grep/find） | 88 | 58 | **−30** |
| **跑程序**（`jhyy_run`） | 96 | 73 | **−23** |
| 改代码 | 86 | 70 | **−16** |
| 读文件 | 57 | 49 | −8 |
| 查台账（`jhyy_workarounds`） | 14 | 25 | **+11** |
| 查规范（`jhyy_lang_ref`） | 12 | 22 | **+10** |
| **总调用** | 482 | 429 | **−53** |

⇒ ⇒ **hook 把「自己摸索 + 自己跑」（−77 次）换成了「查规范 + 查台账」（+29 次）**
⇒ ⇒ 这**正是**它该干的事（模型写完 ⇒ 系统直接给诊断 ⇒ 不用自己摸索）
⇒ ⇒ 但换来的**正确率**测不出来 ⇒ ⇒ **别把它宣传成「提升正确率」**。

**⇒⇒ 决策建议**：**该上**（轮数省 10~20% 是两次实测一致的；没有证据说它有害），
但**只当「省轮次」卖**，**不要当「提升正确率」卖**。

### 8.8 第三类题：**「把 C 程序翻译成 JHYY」**（不饱和 + 代表性）

| 项 | 值 |
|---|---|
| 题目 | 工作目录给一份 **C 程序**（`main.c`），模型**从零写**一个行为一致的 `main.jhyy` |
| 地面真相 | 配对语料的 **JHYY 侧**（`bench/difftest.py` 的 `random.Random(seed)` ⇒ 同种子同程序） |
| 判据 | 编译通过 **且** 退出码一致 **且** stdout **逐字**一致 |
| 题数 | **8** 道（16 个种子里挑 stdout 两侧相同的） |
| 良定义性 | **29 对的 C 侧与 JHYY 侧参考 stdout 逐字相同** ⇒ 「翻译成行为一致的程序」成立 |

**为什么要有这一类** —— 规则类题目（`entry-name` / `missing-decl` / `wrong-format`）
已经 **95%+ 饱和** ⇒ 那把尺子只能测「**有没有变差**」，**测不出「有没有变好」**
⇒ 再加 n=3 也只是把「变差」测得更准而已。

⇒ ⇒ 「翻译」是**不饱和**的（要摸清 stdlib API 语义 + 整数宽度）
且**正是 IDE 的真实用法**（写新代码，不是修代码）⇒ 而且它**精准打在实测缺口上**：
C 侧编译器报错自带修复线索（`implicit declaration of function 'printf'`），
JHYY 侧只说「undefined variable」⇒ **多 5~8 轮**。

**冒烟实测（2026-11-14）**：模型**没有作弊**（真写了一份翻译），
但**花了 34 轮**——它自己摸出了 stdlib 的打印 API
（`import io; import fmt;` + `fmt_i64` + `std_io_print`）
⇒ **这 34 轮全花在「API 语义不熟」上** ⇒ 正是要测的缺口。

⇒ ⇒ **⇒ 由此定出下一个干预**：知识包加「**常用用法（能编译）**」
（打印一个数 / 打印一个字符串）⇒ **每段都真编译过** ⇒ 不会漂。

⚠️ **这类题绝对不能把期望输出给模型** ⇒ 否则它把答案直接打印出来就过
⇒ **只判分**。

⚠️ **踩过的坑**：`--pack <相对路径>` ⇒ claude CLI 是在**临时工作目录**里起的
⇒ 相对路径在那里**不存在** ⇒ 每次立刻失败 ⇒ **8/8「usage 缺失」、总花费 $0**
⇒ 看着像「全错」。⇒ **症状很好认：成本为 0 + 全部 usage 缺失 = 命令没起来**。

### 8.4b MCP 的诊断解析 —— **Windows 盘符会让行号列号全丢**

`jhyy_check` 回来的诊断曾经长这样：

```
{"file":"","line":0,"col":0,"message":"C:\\Users\\...\\main.jhyy:5:11: error: undefined variable"}
```

⇒ **行号列号全没了** ⇒ 模型只拿到一坨原始文本 ⇒ 「定位到具体哪一行」这件事
在 MCP 这条路上**从来没发生过**。

**根因** —— 正则 `^([^:]+):(\d+):(\d+):\s*(.+)$` 用 `[^:]+` 匹配文件名
⇒ **`[^:]` 跨不过 Windows 盘符的冒号** ⇒ 整条匹配失败 ⇒ 落进兜底分支。

⚠️ **IDE 侧早就是对的**（`src/main/compiler/diagnostics.ts` 用**贪婪**的 `(.*)`）
⇒ 而且那份文件的注释**点名道姓**说了 MCP 这份是错的 ⇒ **一直没修**。

⇒ 现在跟 IDE 对齐：贪婪 `(.*)` + 剥掉 `error:` / `warning:` 前缀 + 补 `severity`
（噪声行标成 `severity: "note"` ⇒ **不让模型以为每行都是一条错误**）。

回归门：`mcp-jhyy/tests/test_error_lookup.py` 里那条
`test_parse_diagnostics_handles_windows_drive_letters`。

### 8.5 检索改造（`jhyy_lang_ref`）

| 项 | 值 |
|---|---|
| 章节号精确查 | `"18"` / `"10.4"` / `"附录 B"` / `"B"` ⇒ 直接取那一节**连它的子节** |
| 整节返回 | matches 带 `body`（整节正文，上限 4000 字符，**只给 top 3**） |
| 中文提问 | 中文连续串切 **bigram** ⇒ `search("怎么写命名空间")` 从 **0 命中**变成命中 § 13 |
| CN→EN 反向别名 | 从 `_ALIASES` 自动反查（不用手写第二张表 ⇒ 不会漂移）⇒ `search("命名空间")` 的 top 分 6 → 9 |
| 回归门 | `mcp-jhyy/tests/test_lang_ref_recall.py`（7 个测试） |

**为什么必须做章节号精确查** —— 它是 `jhyy_error_lookup` **指路的前提**：
错误索引告诉模型「去查 § 18」，那 `jhyy_lang_ref("18")` 就必须取得到那一节
⇒ 否则**链条断在中间**（错误索引指了路，检索却取不到）。

**⚠️ 不是每一章都有子节** —— § 13 / § 15 / § 18 的内容直接写在章下；
§ 1 / § 2 / § 5 才有（§ 5 → 5.1~5.7）。

### 8.6 IDE 侧的「编译回灌」（PostToolUse hook）

模型写完 `.jhyy` ⇒ **IDE 立刻编译 ⇒ 真实诊断回灌上下文**（不是靠模型自觉去调工具）。

| 项 | 值 |
|---|---|
| 钩子脚本 | IDE 仓 `scripts/jhyy-check-hook.mjs` |
| settings 生成 | IDE 仓 `src/main/claude/hooks.ts`（`buildHookSettings`） |
| 打包 | `package.json` 的 `extraResources`（**必须放 asar 外面** —— asar 里的文件没法被外部 node 执行） |
| 端到端验证 | IDE 仓 `scripts/claude-hook-e2e.ts`（真 CLI + **marker 铁证**：模型复述出注入的标记 ⇒ 进了上下文） |

⚠️ **端到端验证挖出三个真 bug**（没验证就上线全是空话）：

1. **hook 命令里的路径不能用反斜杠** —— CLI 跑 hook 命令**经过 shell** ⇒
   sh 把反斜杠当转义符 ⇒ `C:\Users\...` → `C:Users...` ⇒ 找不到文件 ⇒ hook 静默死掉
   ⇒ 统一转**正斜杠**。
2. **hook 里必须用 `bash -lc` 跑编译器** —— hook 继承 CLI 的 env ⇒ PATH 带着
   **错的 `C:\msys\usr\bin`** ⇒ `windres`（嵌 exe 图标）预处理失败 ⇒
   编译器改用占位对象 `__jhyy_icon_obj_missing__` 链接 ⇒ **链接必挂且与代码无关**
   ⇒ 模型拿到**假错误**，连编译正确的代码也被判失败。
3. **PostToolUse 的输出要带 `tool_response: {success: true}`** —— CLI 的 hook 文档明写。

⚠️ **顺带修了一个 IDE 侧的真问题**：Claude 会话原来用 `env: { ...process.env }` 起
⇒ **不带 MSYS2 的 login shell env** ⇒ **IDE 里 Claude 自己编译 JHYY 代码也会撞上
「windres 失败 ⇒ 链接必挂」的假错误** ⇒ 现在会话带上了 `mergeShellEnv(...)`
（终端那条路早就走了，见 `src/main/ptyNode.ts`）。

⚠️⚠️ **2026-11-14 CI 抓到的第二个真 bug：hook 在 CI 上**一次编译都没跑过****

CI 红了：hook 回来的 `additionalContext` 是**空串**。

**根因** —— hook 硬依赖 `CLAUDE_CODE_GIT_BASH_PATH`（或 `C:\msys64\usr\bin\bash.exe`）：
- CI 上 `CLAUDE_CODE_GIT_BASH_PATH` **不存在**（那是 Claude Code 自己设的）
- CI 上 `msys2/setup-msys2` 把 MSYS2 装在 **`$RUNNER_TEMP\msys64`** ⇒ 也不是 `C:\msys64`

⇒ **bash 找不到** ⇒ 编译压根没跑 ⇒ 没有任何诊断。

⚠️⚠️ **老版为什么「绿」** —— 老版用「**有没有结构化诊断**」判断成功
⇒ 没编译 ⇒ 没诊断 ⇒ 走「✓ 编译通过了」分支 ⇒ **测试看着是绿的，其实什么都没验**
⇒ ⇒ 这正是改成**退出码**判据之后 CI 才红的原因 —— **门变诚实了**。

⚠️⚠️ **第二轮 CI 又红 ⇒ 「bash 优先」这个设计本身是错的** —— 它在**两个环境里
各坏一次**：
- **没有 bash** 的环境 ⇒ 编译压根没跑
- **有 bash 但 `-lc` 的 PATH 不对** 的环境（CI 上 setup-msys2 的 bash 就是）
  ⇒ 编译跑了但**找不到 gcc**

⇒ ⇒ **CI 连续三轮的结果**：

| 轮次 | 结果 |
|---|---|
| ① 只有 bash | 红 —— 没有 bash ⇒ **一次编译都没跑过** |
| ② bash 优先 + 直接 spawn 兜底 | 红 —— 红的是 bash 那条 ⇒ **直接 spawn 那条过了** |
| ③ 直接 spawn 默认 + bash 兜底 | 红 —— 还是 bash 那条 ⇒ **直接 spawn 那条全过** |

⇒ ⇒ **bash 兜底没有任何可证明的用处** ⇒ **砍掉** ⇒ hook **只有一条路**
⇒ 行为可预测、门好写。

⇒ **最终形态**：**直接 spawn** + env 照抄 `src/main/compiler/env.ts`
（MSYS 风格 PATH 转 Windows 风格 + **ucrt64 的 bin 排最前**
+ 补 TMP/TEMP/SystemRoot + **只追加不替换**继承来的 PATH）。

⚠️ **顺带的好处**：直接 spawn + 修好的 env ⇒ gcc 的**真实**链接错误
（`undefined reference to 'main_jhyy'`）**透出来了** ⇒ 不再只有
「ld returned N exit status」⇒ 模型不用猜入口名。

⚠️ **两条路都要被测到** ⇒ 加 `JHY_HOOK_FORCE_DIRECT=1` ⇒ 单测**两条都跑**
（**CI 走的是「直接 spawn」那条** ⇒ 只测 bash 那条 ⇒ CI 那条路上出问题没人抓）。

⚠️ **一个设计改动**：hook 在**编译成功时也注入一句**「✓ 现在编译通过了」——
① 「注入进了上下文」这件事**每次**都可观测（否则模型一次就改对时注入路径根本测不到）；
② **省一轮**（模型改完就知道过了 ⇒ 不用自己再编译一次确认）。

⚠️⚠️ **2026-11-13 挖到的真 bug：hook 把「链接不过」说成「编译通过了」**

入口写成 `fn main`（该是 `fn main_jhyy`）⇒ **链接期**才失败 ⇒ 编译器 stderr 里
**没有** `file:line:col: error:` 形态的诊断 ⇒ 老版 hook 用
「**有没有结构化诊断**」判断成功 ⇒ **注入「✓ 编译通过了」** ——
而程序**根本链接不过** ⇒ **模型以为做完了 ⇒ 交了一份链接不过的代码**。

⇒ **修法**：成功判据改成**退出码 == 0**（不看诊断条数）。
⇒ **回归门**：IDE 仓 `tests/claude/hook.test.ts` 有一条专门的断言 ——
**链接不过时上下文里绝不能出现「编译通过」四个字**。
⚠️ 老版的断言太弱（只查 `ctx` 含「编译」）⇒ **抓不住这个 bug** ⇒ 门必须够具体。

⚠️ **另外两处同源改动**（都是「只说哪里错、不说怎么改」⇒ 把模型从
「去查规范」拽到「照诊断改」）：

| 改动 | 原来 | 现在 |
|---|---|---|
| **诊断带修法** | `- 12:5 undefined variable` | `- 12:5 undefined variable` + `→ 怎么改：…；见 规范 § 2.3`（修法来自语言仓生成的 `docs/generated/jhyy-error-fix.json`，**169 条**） |
| **成功提示加免责** | 「✓ 现在编译通过了。」 | 「✓ 现在编译通过了（**只说明语法/语义没问题，不代表输出对**）。」⇒ 针对 `mask-change`（**能编译、但输出不对**）那类题 |
| **结尾指回工具** | 「按这些诊断改，别靠猜。」 | 「按这些诊断改；**不确定某个错是什么意思时**，用 MCP 工具 `jhyy_error_lookup` 查它的修法。」
