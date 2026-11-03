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
| 当前版本 | **4.1.2**（真相源 = 仓库根 `VERSION` 文件） |
| **怎么刷版本** | [`docs/internal/build.md` § 版本号自动化](build.md#版本号自动化) —— `bump_version.py set` → `make` → bundle → `finalize` → `check`，**顺序不能反** |
| 最新 release | `v4.1.2`（2026-10-29） |
| 版本轴 | v0.x(C 编译器，冻结于 v1.0.0) · v1.x(自举，终结于 v1.8.3) · v2.x(QBE 重写，终结于 v2.16.0) · v3.x(语言扩展，终结于 v3.4.2) · **v4.x(当前)** |
| 编译器二进制 | `compiler/build/bin/jhyy.exe`（~1.9 MB） |

| 产物 | 体积 |
|---|---|
| `jhyy-installer-4.1.2.exe` | ~55 MB（GUI 安装器；含 .NET 8 Desktop Runtime + **内置 ucrt64 工具链**） |
| `jhyy-compiler-4.1.2.msi` | ~28 MB（企业 / SCCM 分发；含 `jhyy-setuc.exe` + 内置工具链） |
| `jhyy-lang-4.1.2.vsix` | VS Code 扩展 |

> 自 **v4.1.0** 起 installer 自带最小原生 ucrt64 工具链 ⇒ **最终用户不需要 MSYS2**。

---

## 2. 回归与门

### 2.1 事实（会变的数字）

> **本节是这些数字的唯一定义处** —— 下面两节只列「门」,不复述数字。
> 「跨文档一致」由门 `docs-facts` 管;「**为真**」由门 `regress-facts` 管
> （它拿 `regress.py` 的实测计数对拍本节）⇒ 两者合起来才是「事实单一真相源」。

| 项 | 值 |
|---|---|
| `python regress.py` | **265 PASS + 0 XFAIL + 0 failed + 20 SKIP**（285 total） |
| 断言强度审计 | `python scripts/dev/audit_test_assertions.py --strict` —— 扫描 285 · 可跑 265 · 真断言 205 · literal-return-ok 8 · expect-error 52 · skipped 6 · library 14 · **零信号 0** |
| 产物级门数 | `artifact-checks` —— **18 道**（`check_*` 函数数） |

### 2.2 CI 门（完整清单）

> **本表是仓内「门」的完整清单** —— [`CONTRIBUTING.md`](../../CONTRIBUTING.md) 让读者来这里找。
>
> **每道 CI 门在 workflow 里都带一个 `# gate: <id>` 标记** —— 门 `docs-facts` 的第 J 项
> 按它**双向**对拍:workflow 里跑了却没登记 ⇒ 红;登记了却没在 workflow 里跑 ⇒ 红;
> workflow 里新加一个带 run 块的步骤却没分类（既不是门也没登记为非门）⇒ 红。
>
> ⚠️ **改 workflow 或这张表时,两边一起改** —— 否则 J 项会红。

| 门 | id | 查什么 | 在哪跑 · 跑什么 |
|---|---|---|---|
| 自举闭环（构建期） | `selfhost` | jhyy.exe 能把自己编成同一个东西（迭代到不动点）；产物与提交进仓的那份逐字节对照（发布者视角） | ci.yml · build-and-test · `make` |
| 提交产物同步 | `artifact-fresh` | 提交进仓的那份 jhyy.exe 对当前源码的**行为** == 现编产物（比 `.s`，不比 `.exe`） | ci.yml · build-and-test · 内联 shell |
| 全量回归 | `regress` | 每个用例的退出码 / stdout 断言 | ci.yml · build-and-test · `python regress.py --all` |
| 回归事实对拍 | `regress-facts` | § 2.1 的数 == 本轮**实测**数（缺摘要即红） | ci.yml · build-and-test · `python scripts/dev/check_regress_facts.py tmp/regress-summary.json` |
| 断言强度 | `assert-strength` | 每个用例都有能失败的断言（零信号即红） | ci.yml · build-and-test · `python scripts/dev/audit_test_assertions.py --strict` |
| 产物级门 | `artifact-checks` | **18 道**产物级断言（expected-FAIL 模型） | ci.yml · build-and-test · `bash compiler/tests/bootstrap/artifact_checks.sh` |
| 交叉环境准备 | `sysv-emit` | 交叉环境那几份 `.s` 一份都不能少 | ci.yml · build-and-test · 内联 shell |
| 运行时性能 | `perf` | 静态指标硬门（指令数 / 访存 / 帧大小 / chkstk；墙钟只报告） | ci.yml · build-and-test · `python scripts/dev/bench/runtime_perf.py --ci` |
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
| SysV ABI | `sysv-abi` | 链 + 跑 + 比 `// EXPECT:` | ci.yml · sysv · `bash compiler/tests/bootstrap/sysv_link_run.sh` |
| SysV 跨实现对拍 | `sysv-cross` | jhyy ↔ gcc 能否互调（W-104） | ci.yml · sysv · `bash compiler/tests/bootstrap/sysv_abi_cross.sh` |
| 发布：版本 == tag | `release-version` | `VERSION` 文件与 tag 不符 ⇒ 拒发 | release.yml · 内联 pwsh |
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
| 条目总数 | **179** |
| ACTIVE | **0** |
| DEFERRED | 1 |
| RESOLVED / SUPERSEDED / INVALID | 160 / 16 / 2 |

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
> 已 ship 的 v4.0.x / v4.1.x / v4.2.x sprint 计划见 `docs/archive/plans/v4/`。

### 4.2 OS 线（v4.6 → v4.15）

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

### 4.3 未排期（v4.16 起）

async/await · 包管理器 · 并发 cap + 完整 memory model · 多架构 ABI
—— **不预先落文档**，启动时再领版本号。

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
