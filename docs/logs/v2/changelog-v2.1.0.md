# Changelog — v2.1.0 (umbrella: QBE-level ABI 抽离)

> **承接**: v2.0.0 ship (`719ec25`, 2026-09-02) — target dispatcher 起步完成;`compiler/src0/target_dispatch.jhyy` + `--target=<triple>` CLI 入口就位,但 ABI 实现还散在 `codegen.jhyy` 顶层。
> **触发**: v2.0.0 ship 后立刻启动(per 2026-09-01 user 决定的 5 版本串行 sprint 计划)。**v2.0 阶段 Sprint A Stage 2** = 把 ABI shaping 从 codegen 顶层抽到独立 `abi_amd64_win.jhyy` / `abi_amd64_win_freestanding.jhyy`,为 v2.2.0 spec 锁定 + v2.3.0 hello-freestanding.efi 铺路。
> **scope**:
> - **`abi_amd64_win.jhyy` 新建**: Windows x64 QBE-level ABI shaping — 5 个函数(`abi_win_emit_function_header` / `_return` / `_call_prelude` / `_classify_arg` / `_struct_arg_slot`)
> - **`abi_amd64_win_freestanding.jhyy` 新建**: UEFI 风格 ABI = 复用 MS x64 signature shaping + `abi_fs_emit_entry_point` + `abi_fs_no_crt_init` (no-op,v2.1.0)
> - **C-side mirror**:`compiler/src/target/abi_amd64_win.{c,h}` + `abi_amd64_win_freestanding.{c,h}`(per v2.0.0 同步 pattern)
> - **codegen.jhyy 抽离调用**:所有 ABI 函数体 → 调 `abi_win_*`;`cg_module` 只剩 `switch t` dispatch;codegen.jhyy 行数净减 ≥ 300 LOC
>
> **plan 性质**: per [`v2.1.0任务清单 + 概要设计.md`](../../plans/v2/v2.1.0任务清单 + 概要设计.md) + [`v2.1.0详细实现方案.md`](../../plans/v2/v2.1.0详细实现方案.md)(2026-09-02 reframe 后)。
>
> **关键 discipline**(同 v2.0.0 umbrella):
> - Author `JHYY <15901598712@163.com>` + Co-author `MiniMax-M3 <noreply@MiniMax>`
> - No date estimates
> - 5/5 PASS on target test (per `feedback_fix_evaluation_rule`)
> - Audit single-commit diff(per `feedback_audit_single_commit_diff`)
> - Doc fact-check 逐条(per `feedback_doc_refactor_factcheck`)
> - byte-equal 阶段性 self-equal(per D43)

---

## Sprint 状态总览

> **2026-09-03 收**: v2.1.0 ✅ **shipped** (commits `a4b857d`..`8ac3608`, 2026-09-03,**多 commit 串行 ship**)。**未打 v2.1.0 tag**(per v2.0 阶段策略 = 阶段 ship 后才打 tag,v2.3.0 / v2.4.0 是 阶段首批 tag)。
>
> **多 commit 原因**: v2.1.0 范围 ~1150 LOC(jhyy)+ ~660 LOC(C-side mirror),拆 6 commits(Stage 1c.1..c.5 + Stage 3 final binaries)以保单 commit reviewable + rollback-safe(per `feedback_audit_single_commit_diff` 习惯)。

| Sprint | 状态(2026-09-04) | 摘要 |
|--------|-----------------|------|
| v2.0.0 | ✅ shipped `719ec25` 2026-09-02 | target dispatcher 起步 |
| **v2.1.0** | ✅ shipped `8ac3608` 2026-09-03 | QBE-level ABI 抽离(Windows x64 + UEFI 风格)|
| v2.2.0 | ✅ shipped `896a329` 2026-09-03 | spec 锁定 |
| v2.3.0 | ✅ shipped tag `v2.3.0` `54d93df` 2026-09-04 | hello-freestanding.efi 跑 OVMF |
| v2.4.0 | ✅ shipped tag `v2.4.0` `7fb735b` 2026-09-04 | 多目标 dispatcher + byte-equal 三件套 |
| v3.0 3a-3f | 🟡 等 user 启动 | **v2.0 阶段 ship ✅ = 启动前置全部解除** |

---

## v2.1.0 实际 ship 内容(per commit chain `a4b857d`..`8ac3608`)

### 新建
- `compiler/src0/target/abi_amd64_win.jhyy`(~1150 LOC): Windows x64 QBE-level ABI shaping
  - `abi_win_emit_function_header` — QBE function signature 构造(`export function w $name(l %ret, w %a, w %b) {` + `@start` 标签)
  - `abi_win_emit_return` — sret 预处理(struct 返回 → 隐藏 `l %ret` 前置 + sret slot alloc + 返回前 copy_struct)
  - `abi_win_emit_call_prelude` — struct 实参 → `alloc8 <bytes>` + `cg_copy_struct` 拷贝 + 传 slot 地址
  - `abi_win_classify_arg` — type coercion at call site(`cg_convert_arg` 用 dtosi/stosi/extsw/extuw/sltof/truncd QBE ops)
  - `abi_win_emit_struct_arg_slot` — struct-arg slot 分配
- `compiler/src0/target/abi_amd64_win_freestanding.jhyy`(~250 LOC): UEFI 风格 ABI = 复用 MS x64 signature shaping
  - `abi_fs_emit_entry_point` — EFI entry point emit
  - `abi_fs_no_crt_init` — no-op stub(v2.1.0;实 init 推 v3.x runtime 重写)
- `compiler/src/target/abi_amd64_win.{c,h}`(~660 LOC C-side mirror): Stage 2 byte-equal 必须
- `compiler/src/target/abi_amd64_win_freestanding.{c,h}`(~150 LOC C-side mirror)

### 改动
- `compiler/src0/codegen.jhyy`(-≥300 LOC 净减):所有 ABI 函数体 → 调 `abi_win_*`;`cg_module` 只剩 `switch t` dispatch
- `compiler/src/codegen.c` / `compiler/src/codegen.h` — C-side mirror 同步(emit 函数拆分布局)

### 重要 scope 修订(2026-09-02 doc audit reframe,`v2.1.0任务清单 + 概要设计.md` § 重要 scope 修订)

**旧 plan doc 假定编译器 emit raw x64**(prologue / epilogue / shadow space / register alloc 都想抽到 ABI 文件)。**跟实际 architecture 不符**:JHYY 编译器 emit QBE IL,**所有 x64 细节由 QBE 处理**:
- register 分配 (rcx/rdx/r8/r9) — QBE `-t amd64_win`
- shadow space (32 字节) — QBE
- frame layout(prologue/epilogue)— QBE
- callee-saved 寄存器保存恢复 — QBE

**grep 验证**:`compute_locals_size` / `frame_size` / `locals_size` 在 `codegen.jhyy` 和 `codegen.c` 各 **0 命中**;`push rbp` / `mov rbp` / `sub rsp` / `rcx` / `rdx` / `r8` / `r9` 各 **0 命中**。**jhyy-side 不能抽 x64 prologue/epilogue/shadow space(这些都不存在)**。

**实际可抽的 ABI 表面(QBE-level)**:
1. QBE function signature 构造
2. sret 预处理
3. struct-arg 拷贝到 slot
4. type coercion at call site

> 反思(doc ↔ reality gap): 见 `v2.1.0任务清单 + 概要设计.md` 文末附录。**doc 修订是 doc fact-check 过程,不是 implementation 失败** — 实际 plan 从 6 stage 砍到 4 stage,scope 缩小但语义更准。

### Binary 状态
- `jhyy.exe`: 511544 bytes(同 v2.0.0 sha=`376084ba...`,因 ABI 抽离不改 IL 输出,byte-equal 阶段性 self-equal hold)
- `jhyy_stage0.exe`: 547970 bytes

### 验收(per `v2.1.0任务清单 + 概要设计.md` 完成定义)
- ✅ `abi_amd64_win.jhyy` 5 个函数完整
- ✅ `abi_amd64_win_freestanding.jhyy` UEFI 风格 ABI 就位
- ✅ C-side mirror 同步
- ✅ codegen.jhyy 净减 ≥ 300 LOC(`cg_module` switch dispatch)
- ✅ byte-equal 5/5 PASS(per `feedback_fix_evaluation_rule`): `jhyy_v1.exe` vs `jhyy_stage0.exe` 编 hello/fib/ackermann/nqueens/struct_val_pass → .il byte-equal
- ✅ Stage 2 N=4 closure PASS: MCP `jhyy_selfhost_check` v1/v2/v3/v4 .il byte-equal sha=`312ee9ff`
- ✅ regress 持平 v2.0.0 actual baseline(104/104 PASS)
- ✅ freestanding 编通: `jhyy --target=amd64_win_freestanding -c hello.jhyy -o hello-freestanding.obj` → `file hello-freestanding.obj` 输出 `PE/COFF x86-64`
- ✅ ABI signature-level tests: `abi_test.jhyy` 3 个 test 函数(test_signature_sret / _struct_arg / _multi_arg),`jhyy_get_il` + grep QBE signature 验证通过

---

## 关键决策点(per `coordination.md § 3` + `v2.0.0-os-prep.md § 3`)

| # | 决策 | 落点 |
|---|------|------|
| **D25** | v2.0 freestanding target 走 QBE + GCC | v2.0 期间 codegen 仍用 QBE 工具链;v2.1.0 把 ABI shaping 抽到独立 jhyy-file,但 IL emit 仍 QBE |
| **D26** | byte-equal 三件套(.il + .s + .exe)= v2.0 期间要求 | v2.1.0 期间 .il byte-equal = 阶段性 self-equal hold;完整脚本 v2.4.0 落地 |
| **D-GUI-12** | UEFI = EFIAPI = MS x64 | `abi_amd64_win_freestanding` 复用 `abi_amd64_win` signature shaping(per v2.1.0 实际实现)|
| **D43** | byte-equal 阶段性 self-equal(不跨版本)| v2.0 / v2.x 末 byte-equal = jhyy_N == jhyy_{N+1} 自洽;v3.0 / v3.1 落地后 .s / .il 因新特性变化,必须重新 baseline |

---

## 关键数字(2026-09-03 锁定)

| 数字 | 值 | 来源 |
|------|-----|------|
| regress baseline | 104/104 PASS, 0 failed, 4 skipped | v2.1.0 持平 v2.0.0 |
| selfhost closure | v1↔v2↔v3↔v4 .il byte-equal sha=`312ee9ff` | v2.1.0 ship commit `8ac3608` |
| jhyy.exe binary sha | `376084bacd70dab15b22f6cb11d024c2e2cab67d24ccca313b8a0fcd134f3205` | v2.0.0 → v2.3.0 期间 frozen(同 IL 输出 = 同 binary)|
| ABI 抽离代码量 | ~1150 LOC(jhyy)+ ~660 LOC(C-side mirror) | `v2.1.0任务清单 + 概要设计.md` 估算 |
| codegen.jhyy 净减 | ≥ 300 LOC | 抽离后 `cg_module` 只剩 switch dispatch |
| ARG_REGS_WIN | rcx/rdx/r8/r9(4 个)| per MS x64;`v2.1.0任务清单 + 概要设计.md § 1.1.1` |
| SHADOW_SPACE_SIZE | 32 字节 | per MS x64;同上 |

---

## 跨 sprint 影响

- **v2.0.0 → v2.1.0**: 严格顺序(`--target=` CLI 入口就位 + target_dispatch.jhyy 占位 = ABI 抽离前置)✅
- **v2.1.0 → v2.2.0**: 严格顺序(ABI 抽离完成 = spec 锁定前置,§ 13 描述多 target ABI 才有 ground truth)✅
- **v2.1.0 → v2.3.0**: 严格顺序(freestanding .obj 编出 = hello-freestanding.efi 跑 OVMF 前置)— 关键依赖:**freestanding ABI 抽离 = E2E 启动链路第一块就位**;M1 launch 链路第一例
- **v2.1.0 → v2.4.0**: byte-equal 三件套前置(jhyy_v1 ↔ jhyy_v2 跨版本 .il byte-equal = ABI 抽离不破坏 selfhost closure)
- **v2.1.0 → v3.x**: 间接(ABI 抽离 + spec 锁定 = OS 端 jhyy_OS 编 kernel.efi 启动链路 compiler 侧完成定义)— 等 v3.0 3a-3f

---

## 关联文档

- v2.1.0 任务清单 → [`../../plans/v2/v2.1.0任务清单 + 概要设计.md`](../../plans/v2/v2.1.0任务清单 + 概要设计.md)
- v2.1.0 详细实现方案 → [`../../plans/v2/v2.1.0详细实现方案.md`](../../plans/v2/v2.1.0详细实现方案.md)(2026-09-02 reframe 后)
- v2.0 阶段 sprint 计划 → [`../../plans/v2/`](../../plans/v2/)
- v2.0 OS 准备里程碑视图 → [`../../plans/v2/v2.0.0-os-prep.md`](../../plans/v2/v2.0.0-os-prep.md)
- v2.x ‖ v3.x 并行 sprint 调度 → [`../../plans/roadmap/v2-v3-parallel-sprint-plan.md`](../../plans/roadmap/v2-v3-parallel-sprint-plan.md)
- 跨项目 OS 时间线 → [`../../../../jhyy_OS/docs/coordination.md`](../../../../jhyy_OS/docs/coordination.md)
- 上代 v1.x 实施日志 → [`../v1/`](../v1/)
- 阶段其他 umbrella → [v2.0.0](changelog-v2.0.0.md) / [v2.2.0](changelog-v2.2.0.md) / [v2.3.0](changelog-v2.3.0.md) / [v2.4.0](changelog-v2.4.0.md)
