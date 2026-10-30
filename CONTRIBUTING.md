# Contributing to JHYY

Thanks for your interest in improving JHYY (机会翼游). This document explains how to
report issues, propose changes, and get them merged.

> **本仓的通用工作规约在 [§ 工作规约](#工作规约)** —— 那是从项目历史里沉淀下来的
> 硬性要求（提交身份、验证纪律、Git 安全、文档纪律、台账纪律、jhyy 编译器特有规则）。
> 旧代号 `feedback_*` 仍可检索：那 70 条规约当年是独立的 memory 文件，已于 2026-10-30
> 合并进本节。

---

## Code of Conduct

Be respectful. Assume good faith. Technical disagreement is not personal conflict.

## I Have a Question

- **语言怎么用** ⇒ [语言规范](docs/abis/jhyy-lang-spec-v4.0.0.md)
- **ABI / FFI / struct 传参** ⇒ [ABI 白皮书](docs/abis/jhyy-abi-v4.0.0.md)
- **编译器现在什么状态 / 已知有哪些坑** ⇒ [`docs/FACTS.md`](docs/FACTS.md) 与
  [`docs/workarounds.md`](docs/workarounds.md)
- **本机环境问题（路径 / 工具不在 PATH / 两套 python / MCP 超时）** ⇒ 仓库根
  `CLAUDE.md`（本地文件，不入仓）

## I Want To Contribute

### Reporting Bugs

请开 issue，并尽量给出：

1. **最小复现程序**（`.jhyy` 全文）
2. **实际输出** vs **期望输出**（含退出码）
3. **版本**（`jhyy --help` 首行那一行）
4. 编译器来源：`compiler/build/bin/jhyy.exe` 还是自举产物？

> ⚠️ 退出码请用 **harness / Python `subprocess`** 取证，**不要信 bash 读到的**
> —— MSYS2 bash 会把退出码截成 8 位（`真值 & 0xFF`），期望值 ≥ 256 时**先算
> `期望 & 0xFF` 再对读数**（827→59、501→245、300→44、1000→232）。

### Suggesting Enhancements

先看 [`docs/plans/v4/`](docs/plans/v4/) —— 计划线是公开的；挑一格开工前先看那份
plan 的「启动时复核清单」。性能线与 OS 线的关系见 [`docs/FACTS.md`](docs/FACTS.md) § 4。

### Your First Code Pull Request

见下面的 [Development Setup](#development-setup)。改动**编译器源码**（`compiler/src0/*.jhyy`）
比改动文档贵得多 —— 见 [§ 工作规约](#工作规约) 的「jhyy 编译器本身的特殊规则」。

### Pull Request Process

1. 一个 PR 一件事。
2. 跑完门（见下）。**没跑的门 = 没跑的**。
3. commit message 用中文概述 + `Co-Authored-By: MiniMax-M3 <noreply@MiniMax>`。
4. 文档改动要同步事实（见 § 工作规约「文档与措辞」）。

---

## Development Setup

**宿主**：Windows 10 + MSYS2（`C:\msys64\mingw64\bin\bash.exe`）。

```bash
# 1. 依赖:MSYS2 + mingw-w64-ucrt-x86_64-gcc
pacman -S --needed mingw-w64-ucrt-x86_64-gcc mingw-w64-ucrt-x86_64-binutils

# 2. 编编译器(jhyy 自己编自己)
make all           # → compiler/build/bin/jhyy.exe

# 3. 跑回归
python regress.py  # 仓库根的 regress.py(不在 compiler/build/bin/ 里)
```

> ⚠️ 别用 Git Bash 自带的 MinGW `gcc`（`/c/Program\ Files/Git/mingw64/bin/gcc.exe`）——
> 它不支持 PE+ 链接，会在链接阶段失败。

细节（工具链查找顺序、手动验证流水线、版本号自动化、多 target 编译、Linux ELF 交叉链）
⇒ [`docs/internal/build.md`](docs/internal/build.md)。

### 运行测试

```bash
python regress.py                       # 全量
python regress.py --tests=hello.jhyy    # 单个
python scripts/dev/audit_test_assertions.py --strict   # 断言强度审计(挂 CI)
```

**回归数与门清单见 [`docs/FACTS.md`](docs/FACTS.md) § 2** —— 不要在别处复述那些数字。

### 开发脚本

`scripts/dev/` 下：`bench/`（性能测量，`runtime_perf.py` 是唯一可信的测量工具）·
`test/` · `build/` · `install/`。

---

## 工作规约

> 下面这些是**跨 sprint / 跨会话都成立**的硬性要求。一次性协调结果、单次决策、
> 调试过程**不写这里**：workaround 写 [`docs/workarounds.md`](docs/workarounds.md)，
> 其余进 commit message。

### 提交与推送

| 项 | 规约 |
|---|---|
| **commit 身份** | 必须 `JHYY <15901598712@163.com>` —— `JHYY@local` / host 派生值**不算**主页绿格子，永不接受。新仓首次 commit 前 `git config --local user.name "JHYY" && git config --local user.email "15901598712@163.com"`；commit 后 `git show <sha> --no-patch` 复核 `Author:` |
| **Co-Authored-By** | `Co-Authored-By: MiniMax-M3 <noreply@MiniMax>` —— **不要**保留系统默认的 Claude/Opus trailer |
| **push** | commit 成功**直接 push**，不二次确认。例外：`--force` / 新分支 / tag / 多 agent 并发抢同一 branch ⇒ 先确认 |
| **SSH** | push 到 `git@github.com:` 前**必须在同一次 Bash 调用里** `eval "$(ssh-agent -s)" && ssh-add /c/Users/liuzhen/.ssh/id_ed25519 && git push …`（Bash 工具每次新 subshell，agent 不持久 ⇒ 失败症状固定是 `Permission denied (publickey)`） |
| **作者** | 项目作者 = GitHub `JiHuiYiYou`（机会翼游）；提到本人时不要猜真名 |

### 验证纪律

- **改任何东西之前先确认基线绿**：把工作树恢复到 HEAD，**跑一遍完整构建 + 门**。基线不绿 ⇒ 先修基线。「基线也失败」这句话在**当场重建过基线**之前不许说 —— 只换源码不重建 = 比的是两个不同状态（2026-10-25 W-136 那轮因此绕了整整一轮）。〔`feedback_baseline_before_change`〕
- **多 cluster fail 先做 1 轮 RCA 找根因**，别逐个症状修；单个 cluster > 30% 通常 = 1 个根因 + 下游症状。深挖型 audit **先出 checklist**（逐行列出可疑点）再动手，别边看边改；挖出的新 sub-bug 单独开 W-NNN 条目。〔`feedback_rca_first_root_cause`〕〔`feedback_deep_audit_checklist_first`〕
- **声称修好之前，先用 baseline binary 验证它真能复现**；复现不了 = 该 workaround 已死 ⇒ docs-only 翻状态，不要硬 ship 假修。〔`feedback_verify_active_reproduces`〕
- **门必须真走到它声称验的那条路径**：opt-in flag / env var（如 `JHY_SELF_BACKEND=1`）必须真设；每道新门 ship 前**造一次红灯**（把被守的代码弄坏，确认门会红）。没走 opt-in 分支的「5/5 PASS」是假阳性，比没门更糟。〔`feedback_ci_gate_must_exercise_path`〕
  另外「**门看了哪些位置**」也是门的一部分：覆盖面 < 现实覆盖面 ⇒ 安全感是负的（版本门只扫 6 处 ⇒ 两份 README 徽章落后 8 个 release 而 CI 全绿）。一个门至少覆盖两种语法形式（markdown 链接 + 反引号代码跨度）。
- **自查工具报「0 问题」时，先造一条已知坏项证明它看得见**；反过来它报的问题也要复核 —— 假阳性跟假阴性同罪。
- **XPASS 只在测试真能失败时携带信息**：无 `EXPECT` / `EXPECT-ERROR` / `EXPECT-OUT` 的测试恒过，XPASS 是假信号；指令语法写错（该用双引号写成反引号）= 静默失效。
  **给测试补断言本身就是最高效的找 bug 手段**（2026-10-15 那轮补断言挖出 6 条 ACTIVE）；派 agent 补断言时必须写明「推导期望值 → 写判据 → 跑 → 不符就报告，**绝不让 observed 反向定义 expected**」。
- **regress 报 FAIL 先清残留进程 + 重跑两次**，两次一致之前不要改代码；message 是 `expected=X got=-1` + 编译器进度行 = 异常退出 / 环境问题，不是语义错。跑全量回归时**别在同一台机器上并发跑 make / 自举编译**（那会造出假 FLAKY）。〔`feedback_regress_flaky_rerun`〕
- **报数只报 fresh 数**：ship 前清掉 `_regress_*.exe` 等陈旧产物再跑，别沿用上一 session 的数字。〔`feedback_regress_clean_count`〕
- **子 agent 的 finding 动手前自己复现一次**（实测 5 条高优发现里 1 条纯误报）。
- **变异测试的 catch rate 必须迭代**：至少两种检测模式（`compile_fail` + `compile_il_diff`），只用 value-changing 的变异；find 串必须单次出现。

### Git 破坏性操作

- `git stash pop` 后必 `git diff --stat` 确认改动回来了才 drop；**优先 `git stash apply`**。
- **绝不**擅自跑 `git reflog expire --expire=now --all`（静默清掉 stash + reflog，不可逆）；清理默认只用 `git gc --prune=now`。
- `git checkout HEAD -- <files>` 不可逆（working tree 改动不进 reflog）—— discard 前必先 `git diff` 通读，确认它**真的无关**；不确定就 `git stash`，别凭「感觉无关」全丢。
- `git clean -Xdf` 的 pathspec 按**目录前缀**匹配（`dir/*.ext` 会连整个目录删掉）⇒ **先 `git clean -Xdn` 干跑**，并逐条显式传文件路径。
- `make clean` 现在只删 `build/bin/` 下的**未跟踪**产物（`.gitkeep` 与自举锚点 `jhyy.exe` 有白名单）—— 改 clean 目标时别把这个白名单弄丢。
- 「VSCode 说 N 个未提交改动」与 `git status` 对不上时，用 `git ls-files --others --exclude-standard | wc -l` 对齐（`git status` 折叠未跟踪目录且隐藏 ignored）。
- audit 某个 commit 的改动**只用单 commit diff**（`git show <sha>` / `git diff <sha>~1 <sha>`），不要用累计 diff —— 否则会把前几个 commit 的改动算到当前 commit 头上。〔`feedback_audit_single_commit_diff`〕

### 文档与措辞

- **只用简体中文，禁止繁体**（对话 / 文档 / commit message 都算）。zhconv `zh-cn` 转换有 1 处 edge case（`份量→分量`）要 post-fix；`zh-tw` config 绝对不用。
- **计划里不写日期估时**：只用 sprint 序列 + 相对顺序（「v4.4 → v4.5」），milestone 用 sprint 端点表达。〔`feedback_no_date_estimates`〕
- **plan 命名**：已 ship / 进行中的 sprint 逐版本一份 `vX.Y.Z-plan.md`（审计轨迹，改名会破坏跟 changelog / commit 的对应）；未启动的 backlog 不占版本号，用描述性文件名。**单 stage 内的 step-by-step 小规划不写 `docs/plans/`**（走 plan mode 或直接开干）。〔`feedback_plans_per_version`〕〔`feedback_small_plans_no_docs`〕
- **changelog 每条版本轴只有一个 umbrella**（`docs/archive/logs/vX/changelog-vX.Y.0.md`），不另起 `changelog-vX.Y.Z.md`。〔`feedback_changelog_umbrella`〕
- **一次性材料（宣讲稿 / 课程作业 / 外部分享）放桌面**，不进项目仓或 `docs/plans/`。〔`feedback_no_artifacts_in_project`〕
- **≤ 200 行 / sprint 是软指标**：超了先看是不是真有重复代码，没有就 ship，别为凑数牺牲可读性。〔`feedback_file_size_relaxed`〕
- **重构 docs 要逐条 fact-check**：这条限制还存在吗？对应 sprint 已经 ship 了吗？措辞过时吗？换实现路径（换 backend / 换算法）后，**旧文档里关于该路径的「已修复 / 已支持」全部要重新核一遍**（2026-10-15 复核 v1.3 的「浮点比较已支持」就是漏网）。docs-only commit 不用跑 regress，但**必须核对内容** —— 内容错的 doc 比 stale doc 更糟。〔`feedback_doc_refactor_factcheck`〕
- **会变的数字只写在 `docs/FACTS.md`**，其它文档引用、不复述 —— 复述就是下一个漂移源。〔`feedback_facts_single_source`〕
- **两份 README 必须同步改**（`README.md` / `README.zh-CN.md`）—— 门面分叉比内容旧更糟。

### 台账（docs/workarounds.md）纪律

- 每个 workaround 都要进 [`docs/workarounds.md`](docs/workarounds.md)（不只是代码注释）：**动手前**先写条目（是什么 / 触发条件 / 怎么绕 / 绕在哪 / 什么修法能取代它），**动手后**回填真实 file:line。根因修好后标 `RESOLVED` + 日期 + commit，**不要删**（审计轨迹）。〔`feedback_document_workarounds_in_docs`〕
- **桶语义**：`ACTIVE` = 真 bug，高优待办；`DEFERRED` = 真 bug、将来会修、只是不在本轮；`SUPERSEDED` = **不是待修的 bug**（设计如此 / 编译期明确拒绝 / canonical pattern）。「以后不修的」**不进 DEFERRED** —— 往高优桶灌水会让「0 ACTIVE / 0 DEFERRED」失去信号。
- **状态 / 计数不要信二手汇总**：索引表和 MCP `jhyy_workarounds` 都已实证会错报。任何「状态是 X / 计数是 N」的结论都要回源码 `file:line` 复核。

### jhyy 编译器本身的特殊规则

- **改 `compiler/src0/*.jhyy` 前先想清楚代价**：加局部变量会移位模块级 temp 编号 ⇒ 自举产物行为漂移 ⇒ 要走「刷新锚点 + D43 re-pin + 全量回归」一整套发版级流程。但**纯注释改动是免费的**（lexer 在 codegen 前剥掉注释 ⇒ `jhyy.exe` 逐字节不变，不用刷锚点、不用重跑回归）—— 订正过期注释别夹带逻辑改动。
- **jhyy sema 是 single-pass**：函数定义必须 precede 所有 uses，**不支持 forward reference**；报「undefined variable」却指向明显无关的文件 ⇒ 先怀疑新加函数的定义顺序。〔`feedback_jhyy_no_forward_ref`〕
- **`.il` 里写的路径是 cwd-relative** ⇒ `fixed_point` / `d43` / 变异测试一律先 `cd $JHYY_ROOT`（否则 baseline sha 漂移）。〔`feedback_jhyy_dbgfile_cwd_sensitive`〕
- **`JHY_WRITE_IL=1` 不只是「落盘 .il」，它会换编译路径** ⇒ 不能拿它产出的 .il 做「改动前后是否漂移」的对拍，要对拍就比 `.s`；且二进制必须放在**仓内**（jhyy 用 `argv[0]` 推导 project root）。〔`feedback_jhyy_write_il_switches_path`〕
- **没有符号表时直接读 `.il` + `.s`**，比 gdb 快也更准（`movl` vs `movq` 的宽度错一眼可见）；别静态扫几千行 codegen 找假设。〔`feedback_il_s_debugging_pattern`〕
- **`make` 报 `ld returned 1` 且 stderr 全空** ⇒ 多半是输出文件被孤儿 `jhyy.exe` 占着（Windows 上 exe 被 map 后 gcc 无法覆写）：`tasklist //FI "IMAGENAME eq jhyy.exe"`（MSYS2 里要 `//`）→ `taskkill //PID <pid> //F`；先**换输出路径复跑一次**做二分，别一上来读 .s。〔`feedback_jhyy_exe_lock_blocks_build`〕
- **改构建脚本后必须 `make clean && make` 从干净状态重建**：陈旧的中间产物（锚点 / 临时 .s / side-file）能让坏掉的构建脚本照样「绿」（2026-10-27 近失手：删掉拷锚点那行，`make` 照样过，CI 当场红）。**CI 的 fresh checkout 才是「从零能不能建出来」的地标**。〔`feedback_stale_build_artifacts_mask_broken_build`〕
- **`.ps1` 一律 ASCII-only**：PS 5.1 按 ANSI（GBK）读无 BOM 的 .ps1 ⇒ 中文注释变乱码甚至解析错误（CI 用 pwsh/UTF-8 ⇒ 只在本地炸）。中文说明放同名 `.md`。含反斜杠的批量改写**不要走 bash heredoc + python**（反斜杠会被吃掉成 `\b`），用 Edit 工具。〔`feedback_ps1_ascii_only`〕
- **写文本用 `open(path, "w", encoding="utf-8", newline="")`**（`Path.write_text` 等价于 `newline=None` ⇒ Windows 上会把 `\n` 转成 `\r\n`）；**批量行尾归一化前先滤掉二进制**（`git ls-files --eol` 看 `attr/-text`）。改完用 `git ls-files --eol <file>` 核查（**别用** MSYS2 的 `grep -c $'\r'` —— 它匹配每一行，给出假数字）。所有 IL / 二进制派生文件一律 `fopen(..., "wb")`。〔`feedback_edit_tool_crlf_trap`〕
- **CI workflow 的 YAML**：PyYAML `safe_load` 报错**一律当真**（GitHub 用更严的 YAML 1.1，parse 失败 ⇒ 整个 workflow 不跑，报错长得跟 step 内错误一样）⇒ 改完 fetch 真实 run 的 annotation 验证；`shell: msys2 {0}` 默认 `set -e`，probe 第一行要 `set +e`；不要写 `cd ${{ github.workspace }}`（checkout 已默认）。〔`feedback_ci_yaml_debugging`〕

### 工作方式

- **别拿「context 快满了」当停止调查的借口** —— 先看真实的剩余量。遇岔路**自己选一条走**，把依据说清就动手；只有「不可逆的破坏性操作」和「方向性产品决策」才停下来问。〔`feedback_no_false_context_excuse`〕
- **并行 / 串行按真实依赖图判断**，别把某个 sprint 的局部决策泛化成整条轴的元规则。〔`feedback_no_blind_serial_rule`〕
- **一次只改一个变量**：对照实验要**同时重建产物**；不要拿单次 FAIL 就改代码。〔`feedback_fix_evaluation_rule`〕

### 旧代号索引

那 70 条规约当年是独立的 memory 文件（`feedback_<slug>.md`），2026-10-30 合并进本节。
下面这些代号仍被仓内文档引用 —— **按代号可查**：

| 代号 | 规约在哪 |
|---|---|
| `feedback_baseline_before_change` | 改任何东西之前先确认基线绿 |
| `feedback_rca_first_root_cause` | 多 cluster fail 先做 1 轮 RCA |
| `feedback_deep_audit_checklist_first` | 深挖型 audit 先出 checklist |
| `feedback_verify_active_reproduces` | 声称修好之前先复现 |
| `feedback_ci_gate_must_exercise_path` | 门必须真走到它声称验的那条路径 |
| `feedback_codegen_amd64_run_zerobyte` | 同上 —— self-backend 0-byte `.s` 藏在 QBE 默认路径后面 |
| `feedback_codegen_amd64_multifn` | 同上 —— 多函数 `.il` 静默 0 输出，单函数测试 PASS 不可信 |
| `feedback_fix_evaluation_rule` | 一次只改一个变量；对照实验要同时重建产物 |
| `feedback_regress_flaky_rerun` | regress 报 FAIL 先清残留进程 + 重跑两次 |
| `feedback_regress_clean_count` | 报数只报 fresh 数 |
| `feedback_audit_single_commit_diff` | audit 某个 commit 只用单 commit diff |
| `feedback_unrelated_uncommitted_revert` | `git checkout HEAD -- <files>` 不可逆 —— discard 前必先 diff |
| `feedback_doc_refactor_factcheck` | 重构 docs 要逐条 fact-check |
| `feedback_no_artifacts_in_project` | 一次性材料放桌面，不进项目仓 |
| `feedback_file_size_relaxed` | ≤ 200 行 / sprint 是软指标 |
| `feedback_no_date_estimates` | 计划里不写日期估时 |
| `feedback_plans_per_version` / `feedback_small_plans_no_docs` | plan 命名与「小规划不写 docs/plans」 |
| `feedback_changelog_umbrella` | 每条版本轴只有一个 umbrella changelog |
| `feedback_document_workarounds_in_docs` | 每个 workaround 都要进台账 |
| `feedback_commit_coauthor` | Co-Authored-By trailer |
| `feedback_git_identity_canonical` | commit 身份（表里已写） |
| `feedback_jhyy_no_forward_ref` | jhyy sema 是 single-pass，不支持 forward reference |
| `feedback_jhyy_dbgfile_cwd_sensitive` | `.il` 里的路径是 cwd-relative ⇒ 一律先 `cd $JHYY_ROOT` |
| `feedback_jhyy_write_il_switches_path` | `JHY_WRITE_IL=1` 会换编译路径 ⇒ 对拍要比 `.s` |
| `feedback_jhyy_brace_nesting` / `feedback_jhyy_brace_nesting_trap` | jhyy 花括号嵌套陷阱（改 `parse_expr` 的 IDENT 分支时，`} // close X` 注释会指错） |
| `feedback_il_s_debugging_pattern` | 没有符号表时直接读 `.il` + `.s` |
| `feedback_jhyy_exe_lock_blocks_build` | `make` 报 `ld returned 1` 且 stderr 全空 ⇒ exe 被占 |
| `feedback_stale_build_artifacts_mask_broken_build` | 改构建脚本后必须 `make clean && make` |
| `feedback_ps1_ascii_only` | `.ps1` 一律 ASCII-only |
| `feedback_edit_tool_crlf_trap` | 写文本用 `newline=""`；行尾归一化前先滤掉二进制 |
| `feedback_ci_yaml_debugging` | CI workflow 的 YAML 报错一律当真 |
| `feedback_qbe_crlf_root_cause` | 同上 —— Windows 上 `fopen("w")` 会把 `\n` 转成 `\r\n` |
| `feedback_exit_code_forensics` | 退出码取证走 harness / Python `subprocess`，不信 bash |
| `feedback_docker_local` / `feedback_gh_cli_path` | **本机路径**（docker / gh 不在 MSYS2 PATH）⇒ 仓库根 `CLAUDE.md`（本地，不入仓） |
| `feedback_codegen_small_frame_arg_corruption` | 小帧下 `emit_call` 第 3 个参数寄存器被覆盖（workaround：改参数顺序或加 `_pad`） |
| `feedback_for_in_slice_basic` | `for i in slice` 的基础行为（回归基线之一） |
| `feedback_rerum_basic` | 早期重命名相关的实现细节 ⇒ 已不适用 |
| `feedback_v2_self_backend_w089_unfixed` / `feedback_v3_self_backend_diverges_v2` | V2/V3 自举后端的差异（V3 的 parity DIFF 是 V3 的债，不是 V2 的 bug） |
