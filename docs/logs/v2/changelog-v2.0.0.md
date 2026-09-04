# Changelog — v2.0.0 (umbrella: target dispatcher 起步,v2.0 阶段首个 sprint)

> **承接**: v1.8.3 ship (`98c8272`, 2026-08-29, tag `v1.8.3` = v1.x FINAL marker) — installer v1.8.3 WiX + UCPD.sys bypass,v1.x 终结。
> **触发**: 用户 2026-09-01 "v2.0 阶段 5 版本 sprint 计划" 决策(commit `dbadb7f`)— v2.0 阶段串行 ship(放弃原方案 wall-clock 并行优化),v3.0 3a-3f 等 v2.0 阶段 ship 后启动。
> **scope**:
> - **v2.0.0** = Sprint A Stage 1: target dispatcher 起步(`compiler/src0/target_dispatch.jhyy` 新建 + `codegen.jhyy` target switch + `main.jhyy` 加 `--target=<triple>` CLI + 默认 `Amd64Win`)
> - 后续 patch(v2.0.1 / v2.0.2 等)— 内容回填到本 umbrella
>
> **plan 性质**: per [`v2.0.0任务清单 + 概要设计.md`](../../plans/v2/v2.0.0任务清单 + 概要设计.md)。**umbrella changelog**(per `feedback_changelog_umbrella.md` vX.Y axis 单 umbrella;v2.0 minor axis 单一 umbrella)。
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

> **2026-09-02 收**:v2.0.0 ✅ **shipped** (commit `719ec25`, 2026-09-02, single-commit ship)。**未打 v2.0.0 tag**(per v2.0 阶段策略 = 阶段 ship 后才打 tag,v2.3.0 / v2.4.0 是 阶段首批 tag)。
>
> 下表 = 阶段 sprint 序列 + 实际 ship 状态。

| Sprint | 状态(2026-09-04) | 摘要 |
|--------|-----------------|------|
| **v2.0.0** | ✅ shipped `719ec25` 2026-09-02 | target dispatcher 起步: `target_dispatch.jhyy` 新建 + `codegen.jhyy` target switch + `main.jhyy` `--target=` CLI;regress 持平(jhyy_v1.exe ↔ jhyy.exe byte-equal)| |
| **v2.1.0** | ✅ shipped `8ac3608` 2026-09-03 | ABI 抽离: `abi_amd64_win.jhyy` + `abi_amd64_win_freestanding.jhyy` 新建;codegen.jhyy 抽离调用;freestanding .obj 编出 |
| **v2.2.0** | ✅ shipped `896a329` 2026-09-03 | spec 锁定: `jhyy-abi-v1.0.0.md` § 13 + `jhyy-lang-spec-v1.3.0.md` § 17-20 + `build.md` multi-target dispatch |
| **v2.3.0** | ✅ shipped tag `v2.3.0` `54d93df` 2026-09-04 | hello-freestanding.efi 跑 OVMF: `efi.jhyy` + `hello-freestanding.jhyy` + `link.ld` + `build-efi.sh` + `run-ovmf.sh`;QEMU + OVMF 启动验证通过 |
| **v2.4.0** | ✅ shipped tag `v2.4.0` `7fb735b` 2026-09-04 | 多目标 dispatcher + byte-equal 三件套: `target_help` + `--help` flag + `byte_equal.sh` 5/5 PASS + `regress.py --byte-equal` opt-in |
| v3.0 3a-3f | 🟡 等 user 启动 | inline asm / #[naked] / volatile / #[no_std] / #[link_section] / memory barrier — **v2.0 阶段 ship ✅ = 启动前置全部解除** |

> **v2.0 阶段 5 个 sprint 串行 ship,2026-09-02 → 2026-09-04 共 3 天**(per 2026-09-01 user 决定:放弃原方案 wall-clock 并行优化,换节奏可控)。**v3.0 3a-3f 启动前置全部解除**,等 user 启动。

---

## v2.0.0 实际 ship 内容(per commit `719ec25` diff)

### 新建
- `compiler/src/target/target_dispatch.{c,h}` (62 行): Target enum + 3 target 占位
- `compiler/src0/target_dispatch.jhyy` (69 行): jhyy-side mirror — `TARGET_AMD64_WIN()` / `TARGET_AMD64_WIN_FREESTANDING()` / `TARGET_AMD64_SYSV_STUB()` 常量 + `target_name(t)`

### 改动
- `compiler/src0/main.jhyy` (+130 行): `--target=<triple>` CLI flag 解析 + argv scan + 默认 `Amd64Win`
- `compiler/src0/codegen.jhyy` (+16 行): `cg_module` 内加 `switch t` dispatch + emit 函数拆分布局(Amd64Win 完整路径不变 + 其他 stub)
- `compiler/src/codegen.c` / `compiler/src/codegen.h` (+18 / +6 行): C-side mirror 同步
- `compiler/src/main.c` (+31 行): C-side `--target=` argv scan(供 jhyy_stage0.exe 用)
- `Makefile` / `.gitignore` (+7 / +8 行): build script 调整 + 新目录 ignore carve-out

### Binary 状态
- `jhyy.exe`: 510826 bytes (sha=`376084ba...` — v2.0 期间 frozen baseline,v2.1.0 仍同 sha,v2.4.0 改 sha=3f22a7a5...)
- `jhyy_stage0.exe`: 534997 bytes
- `jhyy_v1.exe.exe`: 510826 bytes(同 v2.0.0 jhyy.exe,因 v1.4.4 ship 时已物理 flip;v2.0 期间 v1 ≡ v2 binary)

### 验收
- ✅ regress baseline 持平(`regress.py` 104/104 PASS, 0 failed, 4 skipped)
- ✅ multi-target 跑通:`--target=amd64_win` 编 hosted;`--target=amd64_win_freestanding` 编 stub(无 .efi link,v2.1.0 才接 freestanding)
- ✅ 未知 target 报错:`--target=amd64_unknown` exit 1 + 列可用 target
- ✅ selfhost closure 4-stage byte-equal(per v1.x baseline 继承)

---

## 关键决策点(per `coordination.md § 3` + `v2.0.0-os-prep.md § 3`)

| # | 决策 | 落点 |
|---|------|------|
| **D25** | v2.0 freestanding target 走 QBE + GCC | v2.0 期间 codegen 仍用 QBE 工具链(实施快);v2.x 末自写 IL → .s |
| **D26** | byte-equal 三件套(.il + .s + .exe)= v2.0 期间要求 | v2.4.0 完整脚本;v2.0.0-v2.3.0 阶段性 self-equal(per D43)|
| **D-GUI-12** | UEFI = EFIAPI = MS x64 | abi_amd64_win_freestanding 复用 abi_amd64_win(v2.1.0 落地)|
| **D40** | wire-format ↔ jhyy-side 表达规则 | v2.2.0 锁 lang-spec § 20;Cap<T> wire format 草案 syntax-only(forward-looking,3g 落地前 layout 待 3g.5 锁)|
| **D41** | Debug ABI spec 🔒 锁 + 所有权 | v2.2.0 锁 lang-spec § 19;尺寸 DebugEvent 56B / ErrChain 64B / ProvenanceInfo 136B(per `jhyy_OS/docs/v0.0.4-debug-abi.md`)|
| **D42** | 3a inline asm 启动不依赖 v2.x 完成 | v2.x 完成前 asm 走 QBE 工具链 .s 输出路径(直接插入汇编);v2.x 完成后 asm 走自写后端 escape hatch 路径 |
| **D43** | byte-equal 阶段性 self-equal(不跨版本)| v2.0 / v2.x 末 byte-equal = jhyy_N == jhyy_{N+1} 自洽;v3.0 / v3.1 落地后 .s / .il 因新特性(asm / volatile / link_section / Cap<T> layout)变化,必须重新 baseline |

---

## 关键数字(2026-09-04 锁定)

| 数字 | 值 | 来源 |
|------|-----|------|
| regress baseline | 104/104 PASS, 0 failed, 4 skipped | v2.0 期间各 sprint 持平 |
| selfhost closure(v2.0.0 ship 未显式 pin)| v1↔v2↔v3↔v4 .il byte-equal PASS per v2.0.0 commit message(无具体 sha) | v2.0.0 ship commit `719ec25` "MCP jhyy_selfhost_check 验证 PASS" |
| selfhost closure(v2.1.0 首次 pin)| v1↔v2↔v3↔v4 .il byte-equal sha=`312ee9ff` | v2.1.0 ship commit `8ac3608` commit message "Closure verified: il_sha256 312ee9ff" |
| selfhost closure(v2.4.0 重 baseline)| v1↔v2↔v3↔v4 .il byte-equal sha=`51376ce5721bccb0c81c7deabead1a6012fb76648c424238391018f1890b5761` | v2.4.0 ship commit `7fb735b`(per `jhyy_selfhost_check` MCP 验证) |
| jhyy.exe binary sha(v2.0 期间)| `376084bacd70dab15b22f6cb11d024c2e2cab67d24ccca313b8a0fcd134f3205` | v2.0.0 `719ec25` / v2.1.0 `8ac3608` / v2.2.0 `896a329` / v2.3.0 `v2.3.0` 全同 |
| jhyy.exe binary sha(v2.4.0)| `3f22a7a53d81c8a5cbef1a63a76c1d53074740df0f1467f90f7e6c21e2761343` | v2.4.0 D26 byte-equal recipe 落地后 |
| byte-equal 5/5 PASS target test | hello / struct_val_pass / fib_renamed / nested_struct_deep / big_test | v2.4.0 byte_equal.sh 验收 |
| OVMF.fd | edk2 UDK2018 RELEASEX64_OVMF.fd(2018 release) | v2.3.0 ship,QEMU 启动验证通过 |
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
- v2.0 阶段后续 umbrella → [`changelog-v2.1.0.md`](changelog-v2.1.0.md) / [v2.2.0](changelog-v2.2.0.md) / [v2.3.0](changelog-v2.3.0.md) / [v2.4.0](changelog-v2.4.0.md)
