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
| `python regress.py` | **290 PASS + 0 XFAIL + 0 failed + 20 SKIP**（310 total） |
| 断言强度审计 | `python scripts/dev/audit_test_assertions.py --strict` —— 扫描 310 · 可跑 290 · 真断言 222 · literal-return-ok 8 · expect-error 60 · skipped 6 · library 14 · **零信号 0** |
| 产物级门数 | `artifact-checks` —— **23 道**（`check_*` 函数数） |
| 产物级门 KNOWN-FAIL | **0** 条（当前没有预期失败的门 —— 每道门都该自己绿） |

> **回归的结果有四类,不是三类** —— PASS / failed / SKIP 之外还有 **FLAKY**
> （「首次红、隔离重跑绿」）：它**既不是通过**（结果不可信）也**不是失败**
> （重跑确实过了）⇒ 不进 PASS、不进 failed，**但在 total 里有它**。
> ⇒ 对拍门（`regress-facts`）的不变式是 `passed + skipped + flaky == total`。
> ⇒ 某一轮有 FLAKY 时，`passed` **不与本节对拍**（它少的那几个就是 flaky）——
> 对拍了只会报「本节的数错了」，**方向是反的**（现实没变，是那一轮**不可信**）。
> 门此时报的是「间歇性失败 = 真 bug」并点名是哪些测试。
>
> ⚠️ **2026-11-15 事故**:这道门此前**看不见 FLAKY 桶**（`regress.py --summary-json`
> 的摘要里没有那个字段）⇒ 一次 FLAKY 会让它报「实测自相矛盾」并把矛头指向
> **本节** ⇒ 修法指向错方向（真问题在那个间歇性失败的测试里）。
> 真实病因：`w097_alloc_alias.jhyy` 把三次 store 写在 64 字节分配的**外面**
> （堆越界 ⇒ 退出时堆清理踩雷 ⇒ 间歇性 SIGSEGV，另有挂死），
> CI 上 12 轮里撞上 1 轮。已修（缓冲区 256 字节）。
> 顺带发现：那个测试**只断言退出码** ⇒ W-097 真复发时 stdout 变了而退出码没变
> ⇒ **它抓不住自己要抓的回归** ⇒ 已补 `EXPECT-OUT`。

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
| 回归事实对拍 | `regress-facts` | § 2.1 的数 == 本轮**实测**数（缺摘要即红）；有 FLAKY 时报「间歇性失败 = 真 bug」并点名，**不**报「数错了」 | ci.yml · build-and-test · `python scripts/dev/check_regress_facts.py tmp/regress-summary.json` |
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
| 文档事实 | `docs-facts` | 事实 / 链接 / 反引号裸路径 / `§ N.M` 章节引用 / 台账正文（**索引 ↔ 正文双向对拍**）/ `feedback_*` 代号索引 / **门清单 ⇄ CI 实况** | ci.yml · build-and-test · `python scripts/dev/docs_facts_check.py` |
| 知识包新鲜度 | `gen-knowledge` | 仓里的知识包 == **刚生成的**（重新生成到临时目录再逐字比对）⇒ 规范/标准库改了却没重生成 ⇒ 红。⚠️「反直觉点（编译器验证过）」那一节**自带第二道门** ⇒ 规则过时了**生成这一步就会红** | ci.yml · build-and-test · `python scripts/gen-knowledge.py --check` |
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
| 条目总数 | **234** |
| ACTIVE | **0** |
| DEFERRED | 1 |
| RESOLVED / SUPERSEDED / INVALID | 211 / 19 / 3 |

> ⚠️ **2026-11-15**：ACTIVE 从 0 变成 4 —— 新登记的 4 条真实缺陷
> （W-229 函数名当值用会崩编译器 / W-230 栈位置实参传 `null` 字面量 ⇒ 指针带残渣 /
> W-231 struct 字面量里的 `null` 字段误报 field type mismatch /
> W-232 顶层 `const` 标量的诊断文案误导）。
> ⚠️ **2026-11-20**：ACTIVE 4 → **6** —— 两条都是**做「推理题」题库**时
> 真编译真跑撞出来的：**W-233**（字符串字面量 `as [*]u8` ⇒ **切片的 len 没填**
> ⇒ 读元素**越界 ⇒ 访问违例**）、**W-234**（顶层 `const` 数组的元素写成
> `1 as i32` ⇒ **静默读出 0**，不报错）。
> ⇒ 它们**不在回归套件里**（仓内「XFAIL 计数恒为 0」是硬约束：
> `docs_facts_check.py:105` 的正则把 XFAIL 写死成 0、`check_regress_facts.py:192`
> 要求审计的 xfail 桶为 0）⇒ 复现件放在 `compiler/tests/known-bugs/`。
> ⚠️ **2026-11-20**：ACTIVE 6 → **7** —— **W-235**（窄类型 `i8`/`u8`/`i16`/`u16`
> 的**局部变量**既不截断也不回绕 ⇒ 与规范 § 4.2 / § 4.3 冲突 ⇒ 根因在
> `compiler/src0/ir.jhyy:178-181`）—— 也是**做推理题题库**时撞出来的。
> ⚠️ **2026-11-20**：ACTIVE 7 → **8** —— **W-236**（调用**不检查实参个数**
> ⇒ 少传/多传 ⇒ 编译通过 ⇒ 参数**全是垃圾**；根因在
> `compiler/src0/sema.jhyy:1956-1961`：**只推实参类型、没比个数**
> ⇒ 而规范 § 2.4 **只提了「实参类型不检查」** ⇒ 「个数」连规范都没写）。
> ⚠️ **2026-11-21**：ACTIVE 8 → **0** —— 台账 2026-11 那批「静默缺陷」
> （**W-228 … W-236**，共 **9** 条）**一次性全清**：v4.6 任务 7
> 「静默缺陷清零」落地 ⇒ 每一条都变成「一条编译期报错」或「一个正确结果」。
> ⇒ 9 条复现件全部搬进 `compiler/tests/examples/`（**9 条新的回归用例**）。
> ⇒ 顺带抓出编译器**自身**的 2 个真缺陷（**W-237 / W-238** —— `mono.jhyy` 两处
> 调用的**实参个数**对不上）⇒ 同一批修好 ⇒ 条目总数 232 → **234**。

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
| JHYY | 37431 | 66.4% | 386 |
| Python | 12321 | 21.9% | 43 |
| Shell | 2566 | 4.6% | 20 |
| PowerShell | 1900 | 3.4% | 20 |
| C | 1315 | 2.3% | 13 |
| C# | 287 | 0.5% | 1 |
| Assembly | 225 | 0.4% | 6 |
| Batchfile | 137 | 0.2% | 4 |
| JavaScript | 125 | 0.2% | 1 |
| TypeScript | 65 | 0.1% | 1 |
| **合计** | **56372** | **100%** | **495** |

> 口径：**代码行数**（非空、非纯注释）；文件清单取自 `git ls-files`
> ⇒ 生成物与 vendored 代码自动被 `.gitignore` 排除（不维护第二份排除清单）。
> **`.jhyy` → JHYY 这条映射是 GitHub Linguist 没有的** —— Linguist 不认这门语言，
> 所以 GitHub 侧栏那个语言条里，编译器真正的实现**一行都不出现**。
<!-- langstat:end -->

## 8. IDE 知识包与「模型写 JHYY」评测

> **本节只记「现在是什么」** —— 知识包的结构、配套工具、评测的现状与当前结论。
> 评测**每一轮的实测**（含**已被后一轮推翻**的、含**整节作废**的）都在
> [`docs/archive/experiments/knowledge-pack-eval-2026-11.md`](../archive/experiments/knowledge-pack-eval-2026-11.md)
> ⇒ **要追溯「当初怎么测的、哪个结论被推翻了」去那里**。
>
> ⚠️ **本节曾经是一个实验日志**（2026-11-13 ~ 11-20，原 § 8.2~§ 8.24）⇒
> 每轮都往里追加 ⇒ **越积越大、而且旧结论留在原地**（例如原 § 8.7 的结论
> 后来**整节作废**）⇒ ⇒ **2026-11-21 整体搬进 archive**，本节只留现状。

### 8.1 知识包（常驻进 IDE 会话）

| 项 | 值 |
|---|---|
| 生成器 | `scripts/gen-knowledge.py`（改规范 / 标准库后重跑） |
| 产物 | `docs/generated/jhyy-knowledge.md`（+ 同名 `.json` + `jhyy-error-fix.json`） |
| **怎么到用户手里** | IDE 打包时**拷进安装包** ⇒ 运行时从 `process.resourcesPath` 找 ⇒ **装机用户才有常驻知识**（细节见 § 8.4） |
| **台账 ACTIVE / DEFERRED 条目** | **自动抽取**（生成器解析 `docs/internal/workarounds.md`）⇒ 包里有「⚠ **还没修的坑**」一节 ⇒ **台账一改、重新生成就没了** ⇒ **零人为维护** |

<!-- knowledge:begin —— 这一节由 `scripts/gen-knowledge.py` 生成，别手改 -->

| 项 | 值 |
|---|---|
| 规范章节目录 | **25** 章 |
| 反直觉点（规范里带 ⚠ 标记的行） | **60** 条 |
| 附录 B「未实装」 | **16** 项 |
| 附录 B「已实装但受限」 | **20** 行 |
| 标准库公开 API | **8** 模块 / **45** 个函数 |
| 常见报错速查（诊断类别） | **9** 条 |
| 常用用法（**每个都真编译过**） | **5** 段 |
| **反直觉点（编译器逐条验证过）** | **29** 条 |
| 「报错 → 修法」表（`jhyy-error-fix.json`） | **182** 条（其中 **13** 条人工校订） |
| 知识包体积 | **41101** 字符 |

<!-- knowledge:end -->

> ⚠️ **标准库 API 表以源码的 `// API:` 块为准**，**不抄规范 § 15 那张表** ——
> 实测那张表把 fmt 的内部 helper（`digit_char` / `hex_char`）和一个根本不是
> stdlib 函数的 `ptr_add` 也列成了「公开 API」（它们确实能编过，不是 bug，
> 但会误导用户去调内部实现）。

> ⚠️ **「反直觉点（编译器逐条验证过）」那一节自带第二道门** —— 生成时每条都
> **真编译**：❌ **陷阱型**必须**编译不过**且报错含指定子串；
> ✅ **必须编译过**；**对照型**两种写法**并排实测**、输出不同就摆出来；
> **事实型**的输出**由生成器实测填进去**
> ⇒ ⇒ **规则过时了「生成这一步」就会红** ⇒ 根本产不出过时的包。

### 8.2 配套的 MCP 工具（IDE 会话里模型直接用的那几样）

| 工具 | 现状 |
|---|---|
| `jhyy_error_lookup` | 「编译器报错 → 该改哪」索引 —— 条目数见 § 8.1 的表（自动条目 + `CURATED_FIXES` 人工校订）⇒ 模型拿到诊断大概率知道该改哪儿；**只读**编译器源码（改 `compiler/src0/*.jhyy` 的逻辑会移位模块级 temp 编号 ⇒ 自举产物漂移 ⇒ 要走发版级流程） |
| `jhyy_lang_ref` | 章节号**精确查**（`"18"` / `"10.4"` / `"附录 B"` / `"B"` ⇒ 取那一节**连它的子节**）· 中文连续串切 **bigram**（`search("怎么写命名空间")` 从 0 命中变成命中 § 13）· CN→EN **反向别名**（从 `_ALIASES` 自动反查 ⇒ **不手写第二张表** ⇒ 不会漂） |
| `jhyy_check` 的诊断 | 带 `file` / `line` / `col` / `severity`；**Windows 盘符不再把行号列号吃掉**（原来正则的 `[^:]+` 跨不过盘符的冒号 ⇒ 整条匹配失败 ⇒ 落进兜底分支 ⇒ 模型只拿到一坨原始文本） |

### 8.3 评测（现状）

| 项 | 值 |
|---|---|
| harness | IDE 仓 `JiHuiYiYou-IDE/scripts/eval/run-eval.ts`（`npm run eval`） |
| 超时 / 重试 | **900 秒**；超时 / API 错误 / usage 缺失 ⇒ **自动重试 2 次**（最多跑 3 遍）；JSONL 记 `timedOut` / `apiError` / `attempts` ⇒ **基础设施故障不再算模型的锅** |
| 判分口径 | stdout **逐字** + 退出码一致；**行尾归一**（CRLF ≡ LF） |
| 题目 | 配对任务集（同一个 AST 发 C 与 JHYY 两份）· 手写翻译题 · **推理题**（「读代码说输出」，**不挂 MCP** ⇒ 反馈回路从工具层断开 ⇒ 才测得了正确率） |
| 指标 | **轮数**（每题中位 + P95 + 总轮数）· **工具调用数** · **正确率**（只有推理题测得了）· **错型频率**（比正确率灵敏得多 ⇒ n=1 就能判「某条规则消掉了它对应的那个坑」） |

**当前结论**（最新一轮；历史与**被推翻**的结论见归档）

| 结论 | 数 | 出处 |
|---|---|---|
| **知识包 = 每题少绕 ~9.5 轮** | 配对 Δ **−9.55**，bootstrap 95% CI **[−17.09, −4.55]**，11/11 同向 ⇒ 机制是**查规范 58 → 7** | [归档 § 8.22](../archive/experiments/knowledge-pack-eval-2026-11.md#s822) |
| **推理题上知识包臂全对** | 知识包臂**没有一道错**；速查表臂**有 14 道没过** ⇒ 配对符号检验 **14 : 0** ⇒ **p < 0.001** | [归档 § 8.24](../archive/experiments/knowledge-pack-eval-2026-11.md#s824) ⚠️ |
| **「反直觉语义」那几条，速查表补 2 行也能拿到同样正确率** | 48/54 → 53/54 → 54/54 ⇒ ⇒ 知识包在正确率上的优势 = **那 2 行**（一次性成本） | [归档 § 8.21](../archive/experiments/knowledge-pack-eval-2026-11.md#s821) |
| **JHYY 比 C 难的那点，不在语法** | 同一个 AST 发两份实现、29 对：**平均轮数只多 2%**、**正确率完全一样**；差的是「**API 语义不熟**」+「**编译器报错不带修复线索**」⇒ ⇒ **知识包该做的不是教语法**（模型已经会） | [归档 § 8.3](../archive/experiments/knowledge-pack-eval-2026-11.md#s83)（n=1） |

> ⚠️ **推理题那一行的计数口径有出入**（归档 § 8.24 自己的标题 / 表格 / 单元格
> 三处对不上）⇒ ⇒ **只取稳健的那条**：知识包臂全对、速查表臂 14 道没过、
> 配对 14:0 ⇒ p < 0.001。**别引用具体的「几比几」**。

**四条方法论**（比任何一轮的数都值钱）

1. **只有 n≥3 的数才是结论** —— n=1 只能给**方向**（同一个任务跑两次，轮数差 25% 完全可能）。
2. **报轮数必须同时报：每题中位 + P95 + 每题均值 + 总轮数** —— 单次离群值能把均值带偏 **17 个百分点**。
3. **尺子自己坏掉的时候，结论是假的** —— 每次改尺子先确认「**题面本身成立**」：模型看得到全部声明吗？期望值是「它打印的」还是「它返回的」？
4. **评测 harness 的任何开关，都必须能在启动日志里看见它「开没开」** —— 否则「两臂其实一样」永远没人发现 ⇒ 而结论照样漂亮（−38% / −14% 那种）⇒ ⇒ **越漂亮越危险**。

### 8.4 IDE 侧的「编译回灌」（PostToolUse hook）

模型写完 `.jhyy` ⇒ **IDE 立刻编译 ⇒ 真实诊断回灌上下文**（不是靠模型自觉去调工具）。

| 项 | 值 |
|---|---|
| 钩子脚本 | IDE 仓 `scripts/jhyy-check-hook.mjs` |
| settings 生成 | IDE 仓 `src/main/claude/hooks.ts`（`buildHookSettings`） |
| **最终形态** | **直接 spawn** 编译器（env 照抄 `src/main/compiler/env.ts`：MSYS 风格 PATH 转 Windows 风格 + **ucrt64 的 bin 排最前** + 补 TMP/TEMP/SystemRoot + **只追加不替换**继承来的 PATH）—— **bash 兜底已砍**（它在两个环境里各坏一次，且**无可证明的用处**）⇒ hook **只有一条路** ⇒ 行为可预测、门好写 |
| 成功判据 | **退出码 == 0**（不看诊断条数）—— 链接期失败**绝不能**报成「编译通过了」 |
| 打包 | `package.json` 的 `extraResources`（**必须放 asar 外面** —— asar 里的文件没法被外部 node 执行） |
| 端到端验证 | IDE 仓 `scripts/claude-hook-e2e.ts`（真 CLI + **marker 铁证**：模型复述出注入的标记 ⇒ 进了上下文） |
| **知识包怎么到用户手里** | IDE 打包时**拷进安装包** ⇒ 运行时从 `process.resourcesPath` 找 ⇒ **装机用户才有常驻知识**；**两道门不许静默跳过** —— CI 的 `knowledge-pack-sync`（拿不到 ⇒ 红）+ 本地 `npm run dist` 的第一步（拿不到 ⇒ 直接失败）⇒ **不打一个「只有 12 行速查表」的包出去** |

> ⚠️ **开发态优先用语言仓那份**（刚生成的最新）⇒ 评测读的 = 用户拿到的那份
> ⇒ ⇒ 「评测测的」和「用户拿到的」**永远是同一份**。
