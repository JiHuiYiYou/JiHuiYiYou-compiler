# Changelog — v2.0.0 (umbrella: target dispatcher 起步,v2.0 阶段首个 sprint)

> **承接**: v1.8.3 ship (`98c8272`, 2026-08-29, tag `v1.8.3` = v1.x FINAL marker) — installer v1.8.3 WiX + UCPD.sys bypass,v1.x 终结。
> **触发**: 用户 2026-09-01 "v2.0 阶段 5 版本 sprint 计划" 决策(commit `dbadb7f`)— v2.0 阶段串行 ship(放弃原方案 wall-clock 并行优化),v3.0 3a-3f 等 v2.0 阶段 ship 后启动。
> **scope**:
> - **v2.0.0** = Sprint A Stage 1: target dispatcher 起步(`compiler/src0/target/target_dispatch.jhyy` 新建 + `codegen.jhyy` target switch + `main.jhyy` 加 `--target=<triple>` CLI + 默认 `Amd64Win`)
> - 后续 patch(v2.0.1 / v2.0.2 等)— 内容回填到本 umbrella
>
> **plan 性质**: per [`v2.0.0任务清单 + 概要设计.md`](../../plans/v2/v2.0.0任务清单 + 概要设计.md)。**新 umbrella changelog**(per `feedback_changelog_umbrella.md` vX.Y axis 单 umbrella;v2.0 minor axis 单一 umbrella)。
>
> **关键纪律**:
> - **Author 必须 `JHYY <15901598712@163.com>`** per `feedback_git_identity_canonical` + Co-author `MiniMax-M3 <noreply@MiniMax>` per `feedback_commit_coauthor`
> - **No date estimates** per `feedback_no_date_estimates.md`
> - **5/5 PASS on target test** per `feedback_fix_evaluation_rule`
> - **Audit single-commit diff** per `feedback_audit_single_commit_diff` (per sprint 单 commit ship)
> - **Doc fact-check 逐条** per `feedback_doc_refactor_factcheck`
> - **workaround 标 RESOLVED/INVALID 不删除** per `feedback_document_workarounds_in_docs.md`
> - **byte-equal 阶段性 self-equal** per coordination.md § 3 D43(v2.0 期间 byte-equal = jhyy_N == jhyy_{N+1} 自洽;v3.0 / v3.1 落地后必须重新 baseline)

---

## Sprint 状态总览

> **2026-09-01**:v2.0 阶段**未启动**。下表为规划状态。

| Sprint | 状态(2026-09-01) | 摘要 |
|--------|-----------------|------|
| **v2.0.0** | 🟡 待启动 | target dispatcher 起步: `target_dispatch.jhyy` 新建 + `codegen.jhyy` target switch + `main.jhyy` `--target=` CLI;regress 持平 v1.0 baseline(50/53 PASS,0 failed,3 skipped);byte-equal 5/5 PASS(per `feedback_fix_evaluation_rule`)|
| **v2.1.0** | 🟡 待启动(前置:v2.0.0) | ABI 抽离:`abi_amd64_win.jhyy` 新建(Windows x64 ABI 抽离:4 参数寄存器 + shadow space + struct sret)+ `abi_amd64_win_freestanding.jhyy` 新建(UEFI 风格 ABI:复用 MS x64 + no_crt_init + entry emit)+ codegen.jhyy 抽离调用 + ABI 单元测试 |
| **v2.2.0** | 🟡 待启动(前置:v2.1.0) | spec 锁定:`jhyy-abi-v1.0.0.md` 增 § 13(多 target ABI + freestanding 约定 + Cap<T> wire format 草案 + Debug ABI)+ `jhyy-lang-spec-v1.3.0.md` 增 § 18-21(OS-related 语法预留位 + freestanding 模式 + Debug ABI + Wire Format)+ `build.md` multi-target dispatch 说明 + jhyy_OS 端 cross-check |
| **v2.3.0** | 🟡 待启动(前置:v2.2.0) | hello-freestanding.efi 跑 OVMF: `efi.jhyy` 新建(UEFI struct + protocol 定义)+ `hello-freestanding.jhyy` + `link.ld` + `build_efi.sh`(lld-link → .efi)+ `run_ovmf.sh`(QEMU + OVMF 启动 + printk 到 framebuffer)|
| **v2.4.0** | 🟡 待启动(前置:v2.3.0) | 多目标 dispatcher + byte-equal 三件套: `target_dispatch.jhyy` 完整化 + CLI flag 完善(`--help` / `-c` / `-o` / `--target=`)+ `byte_equal.sh`(per D26 三件套验证: `.il + .s + .exe` byte-equal,`.exe` 兜底 `gcc -g0 + strip + SOURCE_DATE_EPOCH + --build-id=none`)+ `regress.py` 集成 byte-equal 检查 + .s deterministic output 前置 |

---

## 关键决策点(per `coordination.md § 3` + `v2.0.0-os-prep.md § 3`)

| # | 决策 | 落点 |
|---|------|------|
| **D25** | v2.0 freestanding target 走 QBE + GCC | v2.0 期间 codegen 仍用 QBE 工具链(实施快);v2.x 末自写 IL → .s |
| **D26** | byte-equal 三件套(.il + .s + .exe)= v2.0 期间要求 | v2.4.0 完整脚本;v2.0.0-v2.3.0 阶段性 self-equal(per D43)|
| **D-GUI-12** | UEFI = EFIAPI = MS x64 | abi_amd64_win_freestanding 复用 abi_amd64_win |
| **D40** | wire-format ↔ jhyy-side 表达规则 | v2.2.0 锁 lang-spec § 21;Cap<T> wire format 草案 syntax-only(forward-looking,3g 落地前 layout 待 3g.5 锁)|
| **D41** | Debug ABI spec 🔒 锁 + 所有权 | v2.2.0 锁 lang-spec § 20;尺寸 DebugEvent 56B / ErrChain 64B / ProvenanceInfo 136B(per `jhyy_OS/docs/v0.0.4-debug-abi.md`)|
| **D42** | 3a inline asm 启动不依赖 v2.x 完成 | v2.x 完成前 asm 走 QBE 工具链 .s 输出路径(直接插入汇编);v2.x 完成后 asm 走自写后端 escape hatch 路径 |
| **D43** | byte-equal 阶段性 self-equal(不跨版本)| v2.0 / v2.x 末 byte-equal = jhyy_N == jhyy_{N+1} 自洽;v3.0 / v3.1 落地后 .s / .il 因新特性(asm / volatile / link_section / Cap<T> layout)变化,必须重新 baseline |

---

## 关键数字(2026-09-01 锁定)

| 数字 | 值 | 来源 |
|------|-----|------|
| regress baseline | 50/53 PASS,0 failed,3 skipped | `v1.0.0详细实现方案 § 自举定义` + `v1.0-self-hosting.md` |
| byte-equal 5/5 PASS target test | hello / fib / ackermann / nqueens / struct_pass | `feedback_fix_evaluation_rule` |
| OVMF.fd | edk2 UDK2018 RELEASEX64_OVMF.fd(2018 release,需 v2.3.0 启动前 verify 现代 QEMU 兼容性)| `v2.3.0任务清单 + 概要设计.md § 3.1.2` |
| Debug ABI 尺寸 | DebugEvent 56B / ErrChain 64B / ProvenanceInfo 136B | `jhyy_OS/docs/v0.0.4-debug-abi.md`(D41 锁)|
| Cap<T> 8 字节布局 | `{cnode_idx: u32, depth: u8, rights: u16}` + phantom 0 字节 | `coordination.md § 3` D6 锁 |
| ARG_REGS_WIN | rcx/rdx/r8/r9(4 个)| per MS x64;`v2.1.0任务清单 + 概要设计.md § 1.1.1` |
| SHADOW_SPACE_SIZE | 32 字节 | per MS x64;`v2.1.0任务清单 + 概要设计.md § 1.1.1` |

---

## 跨 sprint 影响

- **v1.x → v2.0**:严格顺序(v2.0 sprint 强前置 v1.0 真自举闭环)✅ v1.0.0 已 ship
- **v2.0 阶段内部**:5 版本串行(放弃原 wall-clock 并行优化);byte-equal 阶段性 self-equal(per D43)
- **v2.0 → v3.0**:严格顺序(v3.0 3a-3f 等 v2.0 阶段 ship 后启动,2026-09-01 user 决定)— 放弃原方案"v2.0 跟 v3.0 sprint 3a-3f 同时推进"
- **v2.x 中/末 → v3.x 全线**:异步并行,不强配对,各自 ship 后在 OS M1/M4/M11 launch 联调
- **v2.x + v3.x → OS M1 launch**:OS 编 `kernel.efi` + QEMU + OVMF + printk = M1 真启动(需 v2.0 阶段 + v3.0 3a-3c/3e-3f 全 ship;v3.0 3d `#[no_std]` 软 ship,M1 launch 不依赖 per D10)
- **v2.x 末 + v3.x 末 → M5 boot-from-scratch**(per `v1.x-phase-4-m5-boot-from-scratch.md` 推迟决策 2026-08-14)— v2.x 末 QBE 自写 + v3.x 末 runtime 重写后,一次性删 `src/*.c` + untrack QBE + 删 runtime.c,完成"jhyy 编 jhyy" 0 C 依赖闭环

---

## 关联文档

- v2.0 阶段 sprint 计划 → [`../../plans/v2/`](../../plans/v2/)(v2.0.0 / v2.1.0 / v2.2.0 / v2.3.0 / v2.4.0 任务清单 + 概要设计)
- v2.x ‖ v3.x 并行 sprint 调度 → [`../../plans/roadmap/v2-v3-parallel-sprint-plan.md`](../../plans/roadmap/v2-v3-parallel-sprint-plan.md)
- v2.0 OS 准备里程碑视图 → [`../../plans/v2/v2.0.0-os-prep.md`](../../plans/v2/v2.0.0-os-prep.md)
- v2.x QBE 自写长线 → [`../../plans/roadmap/v2.x-qbe-rewrite.md`](../../plans/roadmap/v2.x-qbe-rewrite.md)
- v3.x 语言扩展长线 → [`../../plans/roadmap/v3.x-language-expansion.md`](../../plans/roadmap/v3.x-language-expansion.md)
- 跨项目 OS 时间线 → [`../../../../jhyy_OS/docs/coordination.md`](../../../../jhyy_OS/docs/coordination.md)
- 上代 v1.x 实施日志 → [`../v1/`](../v1/)
