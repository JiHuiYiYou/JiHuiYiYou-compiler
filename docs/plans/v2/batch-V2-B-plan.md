# V2-B batch plan — v2.6.0 + v2.7.0 (M1-B regalloc + M2 sysv)

## Context

**Batch 范围**:V2-A 自写 amd64 windows 后端跑通,但缺 regalloc + peephole + sysv target。V2-B 加这两个 sub-sprint,出 amd64_sysv 跨 platform 联调,把"自写后端走 windows"扩成"自写后端走 windows + sysv"。

**在 v2 axis 内位置**:
- V2-A(V2-A 已 ship,v2.5.0 自写 amd64_win 后端起步)
- **V2-B = 本 batch**(v2.6.0 M1-B + v2.7.0 M2)
- 后接 V2-C(v2.8.0 N 代 fixed point + QBE 移除)

**上游依赖**:
- V2-A ✅ ship(`codegen_amd64.jhyy` 已跑通 amd64_win)
- v2.1.0 ✅ ship(ABI 抽离;`abi_amd64_win.jhyy` + `abi_amd64_win_freestanding.jhyy` 已有;sysv ABI 文件待建)
- v2.4.0 ✅ ship(多目标 dispatcher + byte-equal 三件套)
- Self-equal baseline `51376ce5...`(v2.5.0 re-baseline)

**跨 axis 硬前置**:**V3-B v3.0.3 (3c volatile) 必须 ship 在 V2-B 启动 v2.7.0 前**。v2.7.0 sysv target 移植 volatile 语义需要 3c spec 已定义。

## Sub-sprint 分解

### v2.6.0 (M1-B regalloc + peephole + 跨 target 联调)

**Scope**:
1. `compiler/src0/codegen_amd64.jhyy` 加 deterministic linear-scan regalloc
   - caller-saved:`%rax/%rcx/%rdx/%rsi/%rdi/%r8/%r9/%r10/%r11`
   - callee-saved:`%rbx/%rbp/%r12/%r13/%r14/%r15`
   - 算法:linear-scan(waw/war 冲突 + spill to stack + reload on next use)
   - **确定性**:同一 IL 输入 → 同一 reg 分配 → 同一 .s 输出(reproducibility gate)
2. `compiler/src0/codegen_amd64.jhyy` 加 peephole 优化(instruction folding):
   - `mov $0, %rax; xor %eax, %eax` → `xor %eax, %eax`
   - `mov %rax, %rbx; mov %rbx, %rcx` → `mov %rax, %rcx`(冗余 copy 折叠)
   - `add $0, %rax` / `sub $0, %rax` → nop(identity 折叠)
   - 简单模式:30-50 个 folding rule;**不**做 instruction scheduling
3. 跨 target 联调:amd64_win + amd64_win_freestanding 产出同等 .s(via regress;freestanding 跟 hosted 共 emit,差异在 link line)
4. `tests/byte_equal_amd64.jhyy` 扩展:跑 v2.5.0 QBE_FALLBACK baseline vs v2.6.0 自写 + regalloc + peephole 的 .s,**byte-equal**

**Key files**:
- 改 `compiler/src0/codegen_amd64.jhyy`(加 regalloc + peephole 模块,~600-900 行新增)
- 改 `compiler/src0/target_dispatch.jhyy`(无需大改)
- 改 `compiler/runtime/runtime.c`(无需大改;freestanding 仍走 UEFI ABI 入口)

**关键决策**:
- **Linear-scan 而非 graph coloring**:确定性 + 实现简单;per `v2-v3-parallel-sprint-plan.md § 4.1` v2.x 决策(graph coloring 在 3g 借用保留 + escape analysis 后做更合适,留 v2.x 末 / v3.x 末)
- **不**做 instruction scheduling(超标量 / OoO)— 性能优化留给 post-M5
- **不**做 loop optimization / LICM / GVN— 性能优化留给 post-M5
- **Peephole 仅 local folding**:1-2 条指令窗口;不做全局 dataflow

### v2.7.0 (M2 amd64_sysv + amd64_sysv_freestanding)

**Scope**:
1. 新建 `compiler/src0/abi_amd64_sysv.jhyy`(~280-300 行):
   - arg 顺序:rdi / rsi / rdx / rcx / r8 / r9(SysV AMD64 ABI § 3.2.3,**不**同 MS x64 的 rcx / rdx / r8 / r9)
   - **无** 32-byte shadow space(SysV 不像 MS x64 要求 caller reserve 32 bytes)
   - struct in regs by eightbyte:aggregate ≤ 16B 分两 regs(分规则见 SysV § 3.2.3);>16B 走 mem(指针 hidden arg)
   - callee-saved:`%rbx/%rbp/%r12-%r15`(同 MS x64);caller-saved:**无** `%rdi` 的 MS 特殊(SysV caller-saved 全是 rax/rcx/rdx/rsi/rdi/r8/r9/r10/r11)
   - 返回值:`%rax`(+ `%rdx` for 128-bit),struct by mem(隐式 sret arg)
2. 新建 `compiler/src0/abi_amd64_sysv_freestanding.jhyy`(~110 行):freestanding variant(无 libc,无 crt0;entry 用 `_start` 或自定义 ELF entry)
3. `compiler/src0/target_dispatch.jhyy`:
   - 加 `TARGET_AMD64_SYSV = 2` + `TARGET_AMD64_SYSV_FREESTANDING = 3`(v2.4.0 已预留 slot,改为真值)
   - `target_qbe_flag(t)`:amd64_sysv → "amd64_sysv"(QBE SysV target name;v2.5.0 之前 fatal,改为真 flag)
   - `target_backend_mode(t)`:amd64_sysv → self(V2-A 已默认 self,无需改)
   - `target_abi_module(t)`:windows → "abi_amd64_win";sysv → "abi_amd64_sysv"
4. Linux ELF 链接脚本(`linker_scripts/amd64_sysv.ld` 或 inline `gcc -nostdlib -e _start`):
   - hosted:`gcc -dynamic-linker /lib64/ld-linux-x86-64.so.2 <crt1.c> <crti.c> <crtbegin.o> -lc <obj>`
   - freestanding:`gcc -nostdlib -e _start -static <obj>`(entry 自己写;无 libc)
5. Cross-compile test:Windows 上 jhyy 跑 `--target=amd64_sysv hello.jhyy` → 编 ELF binary
   - regress.py 加 `--cross` 模式:Windows 编 → copy ELF 到 WSL/Docker → 跑 → EXIT:42
   - 单元测试:amd64_sysv → 走 WSL ubuntu docker image 验证(per `feedback_no_artifacts_in_project` 不放本地 dockerfile,跑时 docker pull 即可)
6. W-066 sysv workaround 文档登:SysV eightbyte 分配在 struct 嵌套时的 edge case + cross-compile setup

**Key files**:
- 新建 `compiler/src0/abi_amd64_sysv.jhyy`(~280-300 行)
- 新建 `compiler/src0/abi_amd64_sysv_freestanding.jhyy`(~110 行)
- 新建 `compiler/src/target/abi_amd64_sysv.{c,h}`(C-side mirror,~280 行)
- 改 `compiler/src0/target_dispatch.jhyy`(加 target 常量 + dispatch,~30 行)
- 改 `compiler/src/target/target_dispatch.{c,h}`(C-side mirror,~30 行)
- 改 `compiler/src0/main.jhyy`(cross-compile ELF 链接 cmd line,~50 行)
- 新建 `compiler/runtime/amd64_sysv/crt0.S`(~50 行,SysV freestanding entry)
- 新建 `compiler/runtime/amd64_sysv_freestanding/entry.S`(~30 行)
- 改 `compiler/build/bin/regress.py`(加 `--cross` 模式,`--target=amd64_sysv` 调用 docker,~40 行)
- 改 `docs/internal/build.md`(cross-compile 步骤 + docker pull 命令)

**关键决策**:
- **SysV struct in-regs 按 eightbyte 分**:参考 System V AMD64 ABI § 3.2.3(8 个 class:SSE / SSEUP / INTEGER / NO_CLASS / MEMORY);不实现完整分类器(只做 INTEGER + SSE + MEMORY 三类,NPO optimization)
- **Cross-compile test setup**:WSL / docker first run 需 user 协助;regress.py `--cross` 默认 fail-fast + 友好报错(不静默吞错,per `feedback_fix_evaluation_rule`);只 5/5 PASS 才标 success
- **freestanding SysV 入口**:`_start` entry 直接调 `main`(无 crt0.c);用户写 `fn main() -> i32`,linker 自动包 `_start`(`-nostartfiles` 关 crt0)

## 跨 axis 硬约束(per § 4.2 + § 4.3)

- **3c volatile 必须 ship 在 V2-B 启动 v2.7.0 前**:
  - V3-B v3.0.3 (3c volatile) ship → codegen.jhyy emit volatile 标记 → `codegen_amd64.jhyy` 解析 + emit mov mem(no regalloc)
  - v2.7.0 sysv target 移植 volatile 语义需要 3c spec 已定义;否则 sysv backend 写"volatile=不走寄存器缓存"代码跟 v3 spec 不一致
- **regalloc vs 借用检查**(per § 4.3):
  - v2.6.0 regalloc **不**考虑借用保留(3g 借用 escape analysis 尚未 ship,V3-C v3.1.0)
  - V2-C v2.8.0 末 fixed point 验算时如发现借用保留失败 → 退回 V2-B 修 regalloc(已知 risk,接受;V2-C ship gate 触发前如发现 fail,临时 hotfix 进 v2.7.x patch)
- **D43** 阶段性 self-equal hold:每 sub-sprint ship 重新 baseline(v2.5.0 → v2.6.0 → v2.7.0)

## Batch ship gate

- `jhyy_regress` 104/104 PASS on all 4 targets(amd64_win / amd64_win_fs / amd64_sysv / amd64_sysv_fs)
- v2.6.0 ship:
  - `--target=amd64_win` 编 .s byte-equal ↔ v2.5.0 baseline(regress byte-equal mode)
  - 加 regalloc + peephole 后 .s 长度 ≤ v2.5.0 +10%(性能不退步)
- v2.7.0 ship:
  - 新增 sysv targets 104/104 PASS(走 cross-compile docker)
  - `hello.jhyy` 在 Linux ELF binary 上 EXIT:42(WSL 或 docker 验证)
  - regress.py `--cross` 默认跑,5/5 PASS
- `mcp__jhyy__jhyy_selfhost_check` 4-stage byte-equal(N=4 per v2.4.0 D43 baseline)
- umbrella `docs/logs/v2/changelog-v2.6.0.md` + `changelog-v2.7.0.md`

## 风险 + 缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| Linear-scan regalloc 启发式跟实际 codegen 不符(per `feedback_il_s_debugging_pattern`) | 部分 regress fail | spill heavy functions 走 stack reload;emit `.loc` directive 方便调试 |
| SysV eightbyte 分类器不完整(只做 INTEGER+SSE+MEMORY 三类) | 嵌套 struct pass-by-value 不正确 | 写完整 8-class 分类器成本高;先做 happy path + 嵌套 mem fallback;复杂 case 留 v3.x 中 |
| Cross-compile 测试 setup(WSL / docker first run) | ship gate 阻塞 | user 协助;regress.py `--cross` 默认 fail-fast + 友好提示(WSL 安装 / docker 安装 / ubuntu:24.04 image pull) |
| Regalloc 跟 3g 借用保留冲突(已知) | V2-C v2.8.0 N 代 fixed point 验算 fail | 接受 risk;V2-C ship gate 触发前如发现 fail,临时 hotfix 进 v2.7.x patch;**不**重做 linear-scan(改成 graph coloring 更复杂,且跟 D43 阶段性 baseline 冲突) |
| v2.6.0 peephole folding 跟 QBE 产出 .s diff | byte-equal .s 失败(v2.6.0 自写后端 .s ≠ v2.5.0 QBE .s) | 接受:v2.6.0 ship 时 byte-equal baseline 重做(N=1+.il byte-equal,.s 可 diff;v2.6.0 起 .s 用自写后端新 baseline);回归到 IL byte-equal 闭包 + QBE_FALLBACK 校验 |
| Volatile 移植 spec 不一致 | sysv target volatile 行为跟 win target 不一致 | V2-B 启动 v2.7.0 前确认 V3-B v3.0.3 已 ship 且 spec 锁 |

## Out of scope

- N 代 fixed point 全验证(N≥3,留 V2-C v2.8.0)
- QBE 工具链完全移除(留 V2-C v2.8.0)
- Volatile 后端移植语义**实现细节**(3c V3-B v3.0.3 ship 文档定义语义,v2.7.0 实现 load/store fence 即可)
- Instruction scheduling / loop optimization / LICM(留 post-M5)
- Graph coloring regalloc(留 post-M5)
- 8-class 完整 SysV 分类器(留 v3.x 中)
- `&mut` + lifetime(留 V3-C)
- `#[no_std]`(留 V3-A)

## 文件变更清单

### 新建
- `compiler/src0/abi_amd64_sysv.jhyy`(~280-300 行)
- `compiler/src0/abi_amd64_sysv_freestanding.jhyy`(~110 行)
- `compiler/src/target/abi_amd64_sysv.{c,h}`(~280 行 C-side mirror)
- `compiler/runtime/amd64_sysv/crt0.S`(~50 行)
- `compiler/runtime/amd64_sysv_freestanding/entry.S`(~30 行)
- `docs/logs/v2/changelog-v2.6.0.md` + `changelog-v2.7.0.md`

### 改动
- `compiler/src0/codegen_amd64.jhyy`(regalloc + peephole,~600-900 行)
- `compiler/src0/target_dispatch.jhyy`(加 SysV target + dispatch,~30 行)
- `compiler/src/target/target_dispatch.{c,h}`(C-side mirror,~30 行)
- `compiler/src0/main.jhyy`(cross-compile ELF link cmd,~50 行)
- `compiler/build/bin/regress.py`(加 `--cross` 模式,~40 行)
- `tests/byte_equal_amd64.jhyy`(扩展覆盖 regalloc + peephole 验证,~30 行)
- `docs/internal/build.md`(cross-compile + docker pull)
- `docs/internal/workarounds.md`(W-066 sysv 文档)

## Commit / tag 节奏

- **Commit 1**:`feat(regalloc): add deterministic linear-scan in codegen_amd64`(v2.6.0 主体)
- **Commit 2**:`feat(peephole): add local instruction folding`(v2.6.0)
- **Commit 3**:`feat(sysv): add amd64_sysv ABI + freestanding variant`(v2.7.0 主体)
- **Commit 4**:`feat(cross-compile): add regress --cross for sysv targets`(v2.7.0)
- **Tag**:`v2.6.0` ship 后 user 确认 → tag;`v2.7.0` ship 后 user 确认 → tag
- **Baseline**:每 ship 重新 baseline sha → 写进 `docs/logs/v2/changelog-v2.X.0.md`

## Cross-ref

- 上游:`docs/plans/v2/batch-V2-A-plan.md`(V2-A 自写后端起步 + ASM escape hatch 占位)
- 上游 axis:`docs/plans/v3/batch-V3-B-plan.md`(v3.0.3 3c volatile 必须在 v2.7.0 启动前 ship)
- 后续 batch:`docs/plans/v2/batch-V2-C-plan.md`(v2.8.0 N 代 fixed point 接 V2-A + V2-B 全 target)
- M2 节点:`docs/plans/v2/v2.0.0-os-prep.md § 1 M2`(sysv 后端启动 OS 用户态)
- § 4.1-4.3 regalloc 决策:`docs/plans/roadmap/v2-v3-parallel-sprint-plan.md`
