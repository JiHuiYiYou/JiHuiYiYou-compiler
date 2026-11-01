# `feedback_*` 代号索引

> 仓内文档（143 份、共 2221 处引用）用 `feedback_<slug>` 指向**一条工作规约**。
> 这些规约当年是独立的 memory 文件，2026-10-30 合并进工作规约，2026-10-31 随工作规约
> **整体搬出仓内**（对外门面 `CONTRIBUTING.md` 不放这些）。
> ⇒ 搬走之后，仓内只剩**代号**，**映射表也没进仓** —— 读者检索得到线索、解析不出含义。
>
> **本文件把那层映射补回仓内**：表一照工作规约的「旧代号索引」原样搬入；
> 表二是**仓内在用、但规约索引里没有**的 25 个 —— 释义据仓内用法反推（**待维护者确认**）。
>
> ⚠️ **这里只有索引，不是规约正文。** 完整规约仍属维护者的仓外笔记 ——
> 本文件回答「这个代号大概指什么」，不回答「这条规约到底怎么规定的」。

---

## 表一：通用工作规约（工作规约「旧代号索引」原样搬入）

| 代号 | 规约（摘要） |
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
| `feedback_plans_per_version` | plan 命名与「小规划不写 docs/plans」 |
| `feedback_small_plans_no_docs` | plan 命名与「小规划不写 docs/plans」 |
| `feedback_changelog_umbrella` | 每条版本轴只有一个 umbrella changelog |
| `feedback_document_workarounds_in_docs` | 每个 workaround 都要进台账 |
| `feedback_commit_coauthor` | Co-Authored-By trailer |
| `feedback_git_identity_canonical` | commit 身份（表里已写） |
| `feedback_jhyy_no_forward_ref` | jhyy sema 是 single-pass，不支持 forward reference |
| `feedback_jhyy_dbgfile_cwd_sensitive` | `.il` 里的路径是 cwd-relative ⇒ 一律先 `cd $JHYY_ROOT` |
| `feedback_jhyy_write_il_switches_path` | `JHY_WRITE_IL=1` 会换编译路径 ⇒ 对拍要比 `.s` |
| `feedback_jhyy_brace_nesting` | jhyy 花括号嵌套陷阱（改 `parse_expr` 的 IDENT 分支时，`} // close X` 注释会指错） |
| `feedback_jhyy_brace_nesting_trap` | jhyy 花括号嵌套陷阱（改 `parse_expr` 的 IDENT 分支时，`} // close X` 注释会指错） |
| `feedback_il_s_debugging_pattern` | 没有符号表时直接读 `.il` + `.s` |
| `feedback_jhyy_exe_lock_blocks_build` | `make` 报 `ld returned 1` 且 stderr 全空 ⇒ exe 被占 |
| `feedback_stale_build_artifacts_mask_broken_build` | 改构建脚本后必须 `make clean && make` |
| `feedback_ps1_ascii_only` | `.ps1` 一律 ASCII-only |
| `feedback_edit_tool_crlf_trap` | 写文本用 `newline=""`；行尾归一化前先滤掉二进制 |
| `feedback_ci_yaml_debugging` | CI workflow 的 YAML 报错一律当真 |
| `feedback_qbe_crlf_root_cause` | 同上 —— Windows 上 `fopen("w")` 会把 `\n` 转成 `\r\n` |
| `feedback_exit_code_forensics` | 退出码取证走 harness / Python `subprocess`，不信 bash |
| `feedback_docker_local` | **本机路径**（docker / gh 不在 MSYS2 PATH）⇒ 本地 `CLAUDE.md`（不入仓） |
| `feedback_gh_cli_path` | **本机路径**（docker / gh 不在 MSYS2 PATH）⇒ 本地 `CLAUDE.md`（不入仓） |
| `feedback_codegen_small_frame_arg_corruption` | 小帧下 `emit_call` 第 3 个参数寄存器被覆盖（workaround：改参数顺序或加 `_pad`） |
| `feedback_for_in_slice_basic` | `for i in slice` 的基础行为（回归基线之一） |
| `feedback_rerum_basic` | 早期重命名相关的实现细节 ⇒ 已不适用 |
| `feedback_v2_self_backend_w089_unfixed` | V2/V3 自举后端的差异（V3 的 parity DIFF 是 V3 的债，不是 V2 的 bug） |
| `feedback_v3_self_backend_diverges_v2` | V2/V3 自举后端的差异（V3 的 parity DIFF 是 V3 的债，不是 V2 的 bug） |

**共 42 个代号。**

## 表二：仓内在用、但规约索引里没有的（据用法反推 · 待确认）

| 代号 | 释义（据仓内用法反推） |
|---|---|
| `feedback_auto_push_after_commit` | commit 成功后**直接 push**，不二次确认（CI 里明确写「不做 (per …)」） |
| `feedback_axis_vn_worktree_isolation` | 多轴并行时每条轴用**独立 worktree**（`JiHuiYiYou-axis-vN`），不共用工作树 |
| `feedback_batch_worktree_cleanup` | 批量任务结束后**清理临时 worktree / 删过期分支** |
| `feedback_compiler_toolchain_path_resolution` | 工具链路径解析的 4 层优先级：JHY_GCC env → JHYY_HOME\env.txt → MSYS2 magic → SearchPathA → fallback `gcc` |
| `feedback_createproc_unquoted_tokenize` | `CreateProcess` 的 cmd 行按**首个空白**切词 ⇒ 路径含空格必须自己加引号 |
| `feedback_d43_baseline_archive` | D43 基线 re-baseline 时**归档旧 sha + 新 sha**（历史 sha 失序的教训） |
| `feedback_destructive_shortcut` | 破坏性操作（删分支 / 清工作树）**不要图省事走捷径** |
| `feedback_diagnostic_emit` | 失败路径**要打诊断信息**，不要静默 |
| `feedback_docker_msys2_pwd_bug` | Docker 里 MSYS2 的 `pwd` 有 bug ⇒ 别拿它判路径 |
| `feedback_editorconfig_vendor_eol` | vendor 目录的**行尾**要与 `.editorconfig` 一致（别被自动改写） |
| `feedback_il_byte_equal` | `.il` 的**逐字节比对**才算真回归信号（行为近似不算） |
| `feedback_make_clean_too_aggressive` | `make clean` **别太激进**（会删掉不该删的产物） |
| `feedback_mcp_axis_v3_dont_copy` | MCP 侧 axis-v3 **不要复制**代码，直接用 |
| `feedback_mcp_jhyy_run_workspace` | MCP 的 `jhyy_run` **在 workspace 里跑** |
| `feedback_mcp_regress_timeout` | MCP 的 regress **要 600s 硬上限** |
| `feedback_memory_selectivity` | memory 只存**通用规约**；sprint 专属的写进台账 |
| `feedback_mutation_testing_iteration` | 变异测试的 catch rate **要迭代**到收敛 |
| `feedback_no_false_context_excuse` | **别拿「context 快满了」当停止调查的借口** |
| `feedback_no_std_flag_path` | `no_std` 的 flag 走 **side-file 路径**（`compiler/build/obj/`）而不是给 CGContext 加字段（避免动 D43 byte-equal baseline） |
| `feedback_no_traditional_chinese` | **不用繁体中文** |
| `feedback_regress_baseline_binary_hash` | regress 的 baseline **二进制 hash**（phantom binary 陷阱） |
| `feedback_regress_py_abspath` | `regress.py` 里路径**用绝对路径**（MSYS2 Python + Windows subprocess 兼容） |
| `feedback_regress_py_path_normalization` | `regress.py` 的**路径归一** |
| `feedback_save_baseline` | 保存 baseline（`--save-baseline`） |
| `feedback_ssh_key_same_shell` | ssh key / ssh-agent 要在**同一个 shell** 里 |
| `feedback_v3b_no_phaseb_worktree` | v3.b 阶段**不开新 worktree**，单 agent 顺序执行 |

**共 26 个代号。**

---

## 维护规则

1. **代号只增不改** —— 文档里已经引用的代号要永远能查到这里。
2. **新代号进表时**：先看表二有没有同义的（合并），没有才新增。
3. **表二的释义被规约正文确认后**，移到表一并注明出处。
4. **表一是规约正文的摘要**，不是正文 —— 两边冲突时以规约正文为准，并回来修这张表。

---

## 相关

- 工作规约正文：仓外（`.claude/working-rules.md`，不入仓）
- 台账：[`workarounds.md`](workarounds.md) —— 规约里与 workaround 纪律相关的部分
- 文档地图：[`README.md`](README.md)
- 为什么有「代号」这层间接：[`docs/archive/README.md`](../archive/README.md) 的「`[[feedback_*]]` 代号说明」
