# Changelog — v2.3.0 (umbrella: hello-freestanding.efi 跑 OVMF)

> **承接**: v2.2.0 ship (`896a329`, 2026-09-03) — spec 锁定(abi § 13/14 + lang-spec § 17-20 + build.md multi-target);jhyy.exe binary 仍 sha=`376084ba...`(frozen,纯文档不改 IL 输出)。
> **触发**: v2.2.0 ship 后立刻启动(per 2026-09-01 user 决定的 5 版本串行 sprint 计划)。**v2.0 阶段 Sprint B** = v2.0 阶段首个 **E2E 启动验证**:把 v2.1.0 编出的 freestanding .obj 经 lld-link 链成 .efi,跑 OVMF,验证 printk 到 framebuffer(ConOut)。**jhyy 编译 OS 类程序的第一例** = M1 launch 链路第一块就位(per `v2.0.0-os-prep.md § 1 M1 真 launch = jhyy_OS 编 `kernel.efi` 跑 OVMF,等 v3.0 3a-3c/3e-3f 全 ship 后)。
> **scope**(per [`v2.3.0任务清单 + 概要设计.md`](../../plans/v2/v2.3.0任务清单 + 概要设计.md)):
> 1. **EFI struct + protocol 定义** — `compiler/tests/examples/hello-freestanding/efi.jhyy` 新建(EfiSystemTable + EfiSimpleTextOutputProtocol per UEFI spec 2.10)
> 2. **hello-freestanding.jhyy + link.ld + build-efi.sh** — UEFI entry + printk stub
> 3. **run-ovmf.sh + OVMF.fd + E2E 验证** — QEMU + OVMF 启动 + printk 到 framebuffer + serial console
>
> **关键 discipline**(同 v2.0.0 umbrella):
> - Author `JHYY <15901598712@163.com>` + Co-author `MiniMax-M3 <noreply@MiniMax>`
> - 5/5 PASS on target test(per `feedback_fix_evaluation_rule`)— **E2E 启动验证:同一 hello-freestanding.efi 5 次启动 5/5 输出"ABCDEHello from jhyy freestanding!\nF\nHello from jhyy freestanding!\n"**
> - Audit single-commit diff(per `feedback_audit_single_commit_diff`)
> - **Plan doc audit-note fix**(per `feedback_doc_refactor_factcheck`)— 4 commits 中 1 commit 修 stale "v2.0 阶段尚未启动"

---

## Sprint 状态总览

> **2026-09-04 收**: v2.3.0 ✅ **shipped** (commits `b505b7a` / `5e0e70e` / `54d93df`, 2026-09-04,**3 commits ship**)。**已打 v2.3.0 tag**(v2.0 阶段 Sprint B 阶段首批 tag;per 2026-09-04 user 决定: 阶段首批 ship 即可打 tag, 不再等阶段全部 ship)。
>
> **多 commit 拆分**:
> 1. `b505b7a` Stage 1 — efi.jhyy UEFI struct/protocol + hello-freestanding/ carveout
> 2. `5e0e70e` Stage 2 — hello-freestanding.jhyy + build-efi.sh + efi_helpers.s
> 3. `54d93df` Stage 3 — run-ovmf.sh + E2E 验证 + plan doc audit-note fix
> + pre-Stage 0: `28c178f` build toolchain + OVMF .fd copy(per v2.3.0 计划,但独立 ship)

| Sprint | 状态(2026-09-04) | 摘要 |
|--------|-----------------|------|
| v2.0.0 | ✅ shipped `719ec25` 2026-09-02 | target dispatcher 起步 |
| v2.1.0 | ✅ shipped `8ac3608` 2026-09-03 | QBE-level ABI 抽离 |
| v2.2.0 | ✅ shipped `896a329` 2026-09-03 | spec 锁定 |
| **v2.3.0** | ✅ shipped tag `v2.3.0` `54d93df` 2026-09-04 | hello-freestanding.efi 跑 OVMF(首个 E2E 启动验证)|
| v2.4.0 | ✅ shipped tag `v2.4.0` `7fb735b` 2026-09-04 | 多目标 dispatcher + byte-equal 三件套 |
| v3.0 3a-3f | 🟡 等 user 启动 | **v2.0 阶段 ship ✅ = 启动前置全部解除** |

---

## v2.3.0 实际 ship 内容(per commit chain `b505b7a`..`54d93df` + pre-Stage 0 `28c178f`)

### 新建
- `compiler/tests/examples/hello-freestanding/efi.jhyy`(~150 行): UEFI struct + protocol 定义
  - EfiSystemTable / EfiSimpleTextOutputProtocol / EfiBootServices / EfiRuntimeServices per UEFI spec 2.10
  - `EFI_GRAPHICS_OUTPUT_PROTOCOL` / `EFI_LOADED_IMAGE_PROTOCOL` 等备用 protocol 占位
- `compiler/tests/examples/hello-freestanding/hello-freestanding.jhyy`(~80 行): UEFI entry + printk stub
  - `efi_main` entry(per `abi_amd64_win_freestanding.jhyy:abi_fs_emit_entry_point`)
  - `serial_puts` / `ConOut->OutputString` 间接调用
- `compiler/tests/examples/hello-freestanding/link.ld`(~30 行): PE32+ link script(.text / .data / .reloc + EFI subsys)
- `compiler/tests/examples/hello-freestanding/efi_main_asm.s`(~27 行): 入口汇编胶水(efi_main → efi_helpers → ConOut)
- `compiler/tests/examples/hello-freestanding/efi_helpers.s`(~40 行): ABI helpers(efi_call_via_ptr 等)
- `compiler/tests/examples/hello-freestanding/no-op.jhyy`(~13 行): minimal jhyy efi_main, debug fixture 隔离 codegen vs EFI 启动问题;保留作为未来 freestanding ABI regression test
- `scripts/dev/build/build-efi.sh`(~50 行): jhyy 编 → .obj → lld-link → .efi
- `scripts/dev/test/run-ovmf.sh`(~50 行): QEMU + OVMF 启动 + serial capture

### 改动
- `.gitignore`: 加 `tests/examples/hello-freestanding/` carve-out(v2.3.0 Stage 1 引入新目录)
- `docs/plans/v2/v2.3.0任务清单 + 概要设计.md`: stale "v2.0 阶段尚未启动" → 已 ship(v2.0.0 / v2.1.0 / v2.2.0 commit + 1 处日期 / 1 处 baseline)

### 工具链(`pre-Stage 0 commit 28c178f`)
- `scripts/dev/build/install-freestanding-toolchain.sh` 新建: 安装 lld + OVMF.fd(如果系统没装)
- OVMF.fd copy 到 `compiler/build/bin/OVMF.fd`(edk2 UDK2018 RELEASEX64_OVMF.fd,2018 release)

### 验收
- ✅ **hello-freestanding.efi 编出**(PE32+ format,`file` 报告 `PE32+ executable (EFI application) x86-64`)
- ✅ **QEMU + OVMF 启动** + printk 到 framebuffer(ConOut->OutputString)
- ✅ **UEFI struct 定义正确**: EfiSystemTable + EfiSimpleTextOutputProtocol per UEFI spec 2.10
- ✅ **E2E 5/5 PASS**: 同一 hello-freestanding.efi 5 次启动,5/5 输出
  ```
  ABCDEHello from jhyy freestanding!
  F
  Hello from jhyy freestanding!
  ```
  - A-F = efi_main 内 debug markers(`serial_puts`),验证 codegen 各阶段正确
  - "Hello" 来自 ConOut->OutputString 通过 `efi_call_via_ptr` 间接调用
- ✅ regress 持平 v2.2.0 actual baseline(104/104 PASS, 0 failed, 4 skipped)

### Binary 状态
- v2.3.0 期间 jhyy.exe binary 不变 = sha=`376084bacd70dab15b22f6cb11d024c2e2cab67d24ccca313b8a0fcd134f3205`(同 v2.0.0 → v2.2.0 frozen)
- selfhost closure 4-stage byte-equal sha=`312ee9ff`(per v2.1.0 baseline)— hello-freestanding.jhyy 不进 src0,不破坏 closure

---

## 关键决策点(per `coordination.md § 3` + `v2.0.0-os-prep.md § 3`)

| # | 决策 | 落点 | v2.3.0 落点 |
|---|------|------|------|
| **D25** | v2.0 freestanding target 走 QBE + GCC | v2.0 期间 codegen 仍用 QBE 工具链;v2.1.0 ABI 抽离 + v2.3.0 lld-link 链 freestanding .obj | E2E 验证 QBE + GCC 链 + lld-link 可行 ✅ |
| **D-GUI-12** | UEFI = EFIAPI = MS x64 | `abi_amd64_win_freestanding` 复用 `abi_amd64_win`;hello-freestanding.efi 经 MS x64 calling conv 调 UEFI ConOut protocol | E2E 验证 协议调用通过 efi_call_via_ptr 正确 ✅ |
| **D40** | wire-format ↔ jhyy-side 表达规则 | lang-spec § 20 锁(per v2.2.0)| v2.3.0 E2E 验证 EFI struct layout 跟 UEFI spec 一致 ✅ |
| **D41** | Debug ABI spec 🔒 锁 + 所有权 | lang-spec § 19 锁(per v2.2.0)| v2.3.0 E2E 不依赖 Debug ABI(forward-looking 给 jhyy_OS 编 kernel.efi 用)|

---

## 关键数字(2026-09-04 锁定)

| 数字 | 值 | 来源 |
|------|-----|------|
| regress baseline | 104/104 PASS, 0 failed, 4 skipped | v2.3.0 持平 v2.2.0 |
| selfhost closure | v1↔v2↔v3↔v4 .il byte-equal sha=`312ee9ff` | v2.1.0 baseline(commit `8ac3608` 显式 pin);v2.3.0 改动是 `hello-freestanding/` 测试 examples + scripts(均不在 src0/),src0 IL emit 不变,closure 链持续 hold |
| jhyy.exe binary sha | `376084bacd70dab15b22f6cb11d024c2e2cab67d24ccca313b8a0fcd134f3205` | v2.0.0 → v2.3.0 frozen |
| E2E 5/5 PASS | 同一 hello-freestanding.efi 5 次启动,5/5 输出 | `54d93df` commit message |
| OVMF.fd | edk2 UDK2018 RELEASEX64_OVMF.fd(2018 release)| v2.3.0 Stage 0 `28c178f` |
| QEMU 启动命令 | `qemu-system-x86_64 -drive if=pflash,format=raw,file=OVMF.fd -drive format=raw,file=hello-freestanding.efi` | `run-ovmf.sh` |
| ABI 抽离代码量 | ~1150 LOC(jhyy)+ ~660 LOC(C-side mirror)| v2.1.0 沉淀, v2.3.0 复用 |

---

## 跨 sprint 影响

- **v2.1.0 → v2.3.0**: 关键依赖(freestanding .obj 编出 = hello-freestanding.efi 跑 OVMF 前置)— **M1 launch 链路第一例** ✅
- **v2.2.0 → v2.3.0**: 严格顺序(spec 锁 = E2E 启动验证前置,lang-spec § 17 OS 启动前置 + § 18 freestanding 模式 = spec 端就位)✅
- **v2.3.0 → v2.4.0**: 间接(E2E 启动验证 = byte-equal 三件套 D26 复盘 sanity check,amd64_win 编 hosted + amd64_win_freestanding 编 freestanding 同时跑通)✅
- **v2.3.0 → M1 launch**: **关键里程碑**:v2.3.0 = compiler 侧能编 EFI 程序的 ground truth;M1 launch = jhyy_OS 编 `kernel.efi` 跑 OVMF,等 v3.0 3a inline asm(直接插汇编给 EFI protocol 调用用)+ 3b #[naked] / 3c volatile / 3e #[link_section] / 3f memory barrier 全 ship
- **v2.3.0 → v3.0 3a**: 间接(3a inline asm 走 QBE 工具链 .s 输出路径 = v2.3.0 efi_main_asm.s 模式复用;不依赖 v2.x 自写后端)
- **v2.3.0 → v3.0 3b/3c/3e/3f**: 间接(freestanding ABI 抽离 = OS kernel codegen 表面就位)

---

## 关联文档

- v2.3.0 任务清单 → [`../../plans/v2/v2.3.0任务清单 + 概要设计.md`](../../plans/v2/v2.3.0任务清单 + 概要设计.md)
- EFI E2E 测试 → [`../../tests/examples/hello-freestanding/`](../../tests/examples/hello-freestanding/)(efi.jhyy / hello-freestanding.jhyy / no-op.jhyy / link.ld / efi_main_asm.s / efi_helpers.s)
- build-efi.sh → [`../../../scripts/dev/build/build-efi.sh`](../../../scripts/dev/build/build-efi.sh)
- run-ovmf.sh → [`../../../scripts/dev/test/run-ovmf.sh`](../../../scripts/dev/test/run-ovmf.sh)
- freestanding toolchain install → [`../../../scripts/dev/build/install-freestanding-toolchain.sh`](../../../scripts/dev/build/install-freestanding-toolchain.sh)(`28c178f`)
- abi-v1.0.0 spec(§ 13/14 freestanding)| [`../../abis/jhyy-abi-v1.0.0.md`](../../abis/jhyy-abi-v1.0.0.md)
- lang-spec-v1.3.0(§ 17-20 OS 启动前置 + freestanding + Debug + Wire)| [`../../abis/jhyy-lang-spec-v1.3.0.md`](../../abis/jhyy-lang-spec-v1.3.0.md)
- 跨项目 OS 时间线 → [`../../../../jhyy_OS/docs/coordination.md`](../../../../jhyy_OS/docs/coordination.md)
- 阶段其他 umbrella → [v2.0.0](changelog-v2.0.0.md) / [v2.1.0](changelog-v2.1.0.md) / [v2.2.0](changelog-v2.2.0.md) / [v2.4.0](changelog-v2.4.0.md)
