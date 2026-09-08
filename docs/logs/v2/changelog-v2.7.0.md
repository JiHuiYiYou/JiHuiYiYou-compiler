# JHYY v2.7.0 — amd64_sysv + amd64_sysv_freestanding ABI 模块 + emit_call 拆 target

**Shipped**: TBD (Phase 1 + 2a + 2b, 3 commits chain)
**Plan**: [`../../plans/v2/v2.7.0-plan.md`](../../plans/v2/v2.7.0-plan.md)
**Scope**: 7 source files (NEW 2 ABI modules + 5 sysv test fixtures + 修改 target_dispatch / codegen_amd64_state / codegen_amd64_emit_call / codegen / regress.py)

---

## v2.7.0 — amd64_sysv + amd64_sysv_freestanding 真 ABI codegen path

3-commit ship chain per V2-B M2 (per `docs/plans/v2/v2.7.0-plan.md` § Phase 1+2):

### Commit 1: Phase 1 — ABI extraction (TBD)

**Scope**: 2 NEW ABI modules, byte-equal mirror of `abi_amd64_win.jhyy:1-275` + freestanding delegate pattern。

**Diff stat**: 2 files changed, ~383 insertions(+), 0 deletions(-)
- `compiler/src0/abi_amd64_sysv.jhyy` (NEW, ~295 LOC) — 7 fn + 3 SysV class constants + inline 3-case unit test
- `compiler/src0/abi_amd64_sysv_freestanding.jhyy` (NEW, ~88 LOC) — 5 fn delegate + 2 fn stubs

**关键设计**:
- 3-class minimum viable SysV classifier (INTEGER / SSE / MEMORY) — 8-class SysV psABI § A.4 full classifier 留 v2.7.1+
- ABI module **不 wire 进 codegen**(Phase 1 ship gate 仅要求 parse+sema + classify_arg unit test PASS;无 codegen 改动)

**Ship gate (5/5 PASS,纯 module 增 add,不动 codegen)**:
- ✅ regress 104/104 PASS, 4 SKIP (jhyy.exe sha `856edab49457e53f...`, v2.6.8 unchanged)
- ✅ byte_equal_amd64.sh 默认 mode: 10 PASS / 0 SKIP / 0 FAIL (QBE-vs-self)
- ✅ byte_equal_amd64.sh `--baseline`: 20 PASS / 0 SKIP / 0 FAIL
- ✅ D43 closure v1→v2 hold: il sha `92e8255473db3395c98bb12c58b473071384b42b897b114cea5fa903d715d25a` (v2.6.6 unchanged;Phase 1 无 codegen 改动)
- ✅ `abi_sysv_classify_arg` 3-case inline unit test PASS (INTEGER / SSE / MEMORY)

### Commit 2: Phase 2a — target_dispatch refactor + target_tag threading (TBD)

**Scope**: rename `_STUB` → 移除,加 `TARGET_AMD64_SYSV_FREESTANDING=3`,加 `target_abi_module(t)` chokepoint,thread `target_tag: i32` field through `CGState`,`target_backend_mode` SYSV/SYSVFS → `BACKEND_SELF`。

**Diff stat**: 3 files changed, ~70 insertions(+), ~5 deletions(-)
- `compiler/src0/target_dispatch.jhyy` — rename line 31 + 加 `TARGET_AMD64_SYSV_FREESTANDING()` line 32 + 加 `target_abi_module(t)` chokepoint + `target_backend_mode` SYSV/SYSVFS → `BACKEND_SELF` + `jh_target_count` 3→4 + `target_parse` / `target_name` / `target_qbe_flag` / `target_status` 更新
- `compiler/src0/codegen_amd64_state.jhyy` — `CGState` 加 `target_tag: i32` 字段 (默认 0 = Win) + `cg_state_init` init + `cg_state_set_target(state, target_tag)` setter
- `compiler/src0/codegen.jhyy` — `cg_module` 调站点 rename `_STUB` → 无 stub;SYSVFS stub branch 加(详细 Phase 2b 状态 message)

**关键 invariant**: `TARGET_AMD64_SYSV` body 仍 `return 2 as i32` (per C-side enum byte-equal 锁, `target_dispatch.jhyy:14-15`)。rename 仅 fn 名,enum 值不变 → cross-side byte-equal hold。

**Ship gate (5/5 PASS,Win ABI path 不动 → byte-equile + D43 hold)**:
- ✅ regress 104/104 PASS, 4 SKIP (binary unchanged for Win target)
- ✅ byte_equal_amd64.sh 默认 mode: 10 PASS / 0 SKIP / 0 FAIL (Win ABI path 不动)
- ✅ byte_equal_amd64.sh `--baseline`: 20 PASS / 0 SKIP / 0 FAIL
- ✅ D43 closure v1→v2 hold: il sha `92e8255473db3395c98bb12c58b473071384b42b897b114cea5fa903d715d25a` (rename + 新字段不污染 IL)
- ✅ `target_abi_module` 4-case lookup PASS (per phase 2a unit test)

### Commit 3: Phase 2b — emit_call refactor + SysV body wire + 5 sysv tests + regress.py stub (TBD)

**Scope**: emit_call 拆 target (Win 4 reg + 32B shadow / SysV 6 reg + 无 shadow);cg_module wire `target_abi_module(t)` dispatch;5 sysv regress fixtures SKIP;regress.py `--cross` argparse stub。

**Diff stat**: 7 files changed, ~280 insertions(+), ~10 deletions(-)
- `compiler/src0/codegen_amd64_emit_call.jhyy` — `target_is_win(target_tag)` helper + `emit_amd64_arg_regs(state, nargs, ret_qt, target_tag)` chokepoint (Win 4 reg rcx/rdx/r8/r9 + 32B shadow / SysV 6 reg rdi/rsi/rdx/rcx/r8/r9 NO shadow) + emit_call body refactor gated on `target_tag`
- `compiler/src0/codegen.jhyy` — `import abi_amd64_sysv;` + `import abi_amd64_sysv_freestanding;` (无条件 imports,per jhyy parser 不允许 conditional imports) + cg_module SYSV/SYSVFS branch message 升级到 Phase 2b status
- `compiler/build/bin/regress.py` — `--cross {wsl,docker,auto,none}` argparse (default `auto`)
- `compiler/tests/examples/sysv_struct_pass.jhyy` (NEW, ~26 LOC) — 2-eightbyte struct pass-by-value
- `compiler/tests/examples/sysv_struct_ret.jhyy` (NEW, ~22 LOC) — small struct return ≤ 16B → %rax/%rdx
- `compiler/tests/examples/sysv_struct_mixed.jhyy` (NEW, ~28 LOC) — struct {i32, f64} → INTEGER+SSE
- `compiler/tests/examples/sysv_vararg_basic.jhyy` (NEW, ~16 LOC) — extern printf(...) smoke test (vararg `...` not in parser,regular 2-arg 代替)
- `compiler/tests/examples/sysv_abi_test.jhyy` (NEW, ~14 LOC) — 6-reg max + 7th-on-stack

**关键 invariant**: emit_call refactor 让 Win ABI path 行为完全不变(`target_tag=0` default 走原 Win 4 reg + 32B shadow 路径)→ Win ABI byte-equal 仍 hold。

**5 sysv tests SKIP semantics**: 所有 5 个 fixture 加 `// SKIP: sysv target requires Linux host (WSL/Docker)` directive → 默认 regress 自动 SKIP(cross-env wire 留 v2.7.1 实接 Linux ELF runtime + WSL/Docker sub-process)。

**D43 re-baseline note**: Commit 2 + Commit 3 累计 emit_call refactor + ABI imports 微调 codegen .il emit → D43 closure v1→v2 新 baseline `cc89432920cba92f6c465dd73f5faa575bd9ce8d17d678c7e1f34879e419cf2b` (per D43 v2.x sub-sprint 阶段性 self-equal rule)。v2.6.6 baseline `92e82554...` 退役存档 (commit message 引)。

**Ship gate (5/5 PASS,Commit 3 final)**:
- ✅ regress 104/104 PASS, 9 SKIP (binary `fffe3f80b391f5a0...`, 4 library + 5 sysv fixtures)
- ✅ byte_equal_amd64.sh 默认 mode: 10 PASS / 0 SKIP / 0 FAIL (Win ABI path byte-equal hold)
- ✅ byte_equal_amd64.sh `--baseline`: 20 PASS / 0 SKIP / 0 FAIL (旧 baseline hold)
- ✅ D43 closure v1→v2 hold: il sha `cc89432920cba92f6c465dd73f5faa575bd9ce8d17d678c7e1f34879e419cf2b` (Commit 2+3 re-baseline,Win ABI path 不污染)
- ✅ 5 sysv tests SKIP (cross-env wire stub;Linux ELF runtime + WSL/Docker wire 留 v2.7.1)
- ✅ regress.py --help 列 `--cross {wsl,docker,auto,none}` flag

---

## References

- v2.7.0 plan: [`../../plans/v2/v2.7.0-plan.md`](../../plans/v2/v2.7.0-plan.md)
- v2.7.1 follow-up: [`../../plans/v2/v2.7.1-plan.md`](../../plans/v2/v2.7.1-plan.md) (Phase 3 wire 留此 doc)
- v2.6.8 ship: commit `b457e6a` (docs hygiene)
- v2.6.7 ship: commit `c965773` (byte_equal_amd64.sh Commit 5)
- v2.6.6 ship: commit `224a944` (W-069 真修;旧 baseline `92e82554...` 本 ship 退役存档)
- v2.5.0 ship: commit `64463d5` (self backend wired)
- v2.4.0 ship: commit `7fb735b` (hello-freestanding.efi OVMF E2E 5/5 PASS)
- D43 baseline timeline: `51376ce5...` (v2.4.0 末) → `92e82554...` (v2.6.6,本 ship 退役) → `cc894329...` (v2.7.0 末 Commit 2+3 re-baseline)
- 5 sysv regress test fixtures: `compiler/tests/examples/sysv_*.jhyy` (SKIP directive 默认生效;cross-env 实 wire 留 v2.7.1)
- SysV psABI: § 3.2.3 (argument passing) + § A.4 (eightbyte classification) — external ABI spec
- Memory: [[feedback_changelog_umbrella]] (umbrella convention), [[feedback_plans_per_version]] (per-version plan), [[feedback_fix_evaluation_rule]] (5/5 PASS gate per phase), [[feedback_audit_single_commit_diff]] (single-commit audit), [[feedback_no_date_estimates]] (sprint 序列 + 相对顺序), [[feedback_auto_push_after_commit]] (push after commit), [[project_v2_7_0_commits_1_2]] (Commit 1+2 ship context + 非确定性 debugging 教训), [[project_v2_v3_parallel_axes]] (v2.x ‖ v3.x 异步并行)

---

## v2.7.1 — Linux ELF runtime + regress.py --cross 实 wire + docs

**Shipped**: 2026-09-08 (3-commit chain: `8500999` Phase 1 + `911b8da` Phase 2 + Commit 3 docs)
**Plan**: [`../../plans/v2/v2.7.1-plan.md`](../../plans/v2/v2.7.1-plan.md)
**Scope**: 1 NEW runtime dir (3 files: crt0.S / link.ld / README.md) + 1 driver file (regress.py --cross 实 wire) + 1 doc (d43-baseline-archive.md)

### Commit 1 (Phase 1): Linux ELF runtime — `runtime/linux_elf/` NEW

**Commit**: `8500999`
**Diff stat**: 4 files changed, 221 insertions(+), 0 deletions(-)
- `.gitignore` (+3) — runtime/linux_elf/ carveout (asm + linker script + README tracked)
- `runtime/linux_elf/crt0.S` (NEW, ~50 LOC) — `_start` entry point per SysV psABI § 3.2.2 + Linux x86_64 syscall table
- `runtime/linux_elf/link.ld` (NEW, ~60 LOC) — linker script (elf64-x86-64, ENTRY(_start), 2 PT_LOAD)
- `runtime/linux_elf/README.md` (NEW, ~110 LOC) — build invocations + ABI compliance + cross-compile integration

**关键设计**:
- `call main_jhyy` 而非 `call main`(jhyy main convention per W-065 cmd_run pre-check)
- 16-byte 栈对齐 (`andq $-16, %rsp`) per SysV § 3.2.2
- `xorq %rbp, %rbp` (no frame ptr per SysV)
- `mov $60, %rax` + `syscall` (SYS_exit per Linux x86_64 syscall table)
- linker script: `OUTPUT_FORMAT(elf64-x86-64)`, `ENTRY(_start)`, 2 PT_LOAD PHDR (text RX + data RW)

**Phase 1 ship gate (4/4 PASS)**:
- ✅ `gcc -c runtime/linux_elf/crt0.S` assemble no error
- ✅ runtime files parse + tracked in git (per .gitignore carveout)
- ✅ runtime committed + pushed to origin/axis-v2
- ✅ `runtime/` top-level dir 首次建立(镜像 v2.4.0 `compiler/tests/examples/hello-freestanding/` UEFI 模式但独立)

**D43 closure 不动**:Commit 1 是 runtime 增,不动 Win codegen path → D43 baseline `cc894329...` hold 不变。

### Commit 2 (Phase 2): regress.py `--cross {wsl,docker,auto,none}` 实 wire

**Commit**: `911b8da`
**Diff stat**: 1 file changed, 217 insertions(+), 3 deletions(-)
- `compiler/build/bin/regress.py` (+217) — `_resolve_cross_mode` + `_run_cross_env_sysv_test` + `_run_sysv_via_cross_env` 三函数 wired;`--cross` 默认 `auto`(probe wsl.exe with distro check → docker on PATH → none SKIP)

**关键设计**:
- auto probe: `wsl.exe -l -v` 检查有 distro 才返回 "wsl"(否则 fall through 到 docker 或 none)
- wsl mode: `wsl.exe -d Ubuntu bash -c <compile+link+run>`(需要 Linux host 真跑)
- docker mode: `docker run --rm -v <repo>:/work -w /work ubuntu:22.04 bash -c <compile+link+run>`
- graceful SKIP: 任何 cross-env 不可用都 SKIP,exit 0,不 throw

**Phase 2 ship gate (6/6 PASS)**:
- ✅ regress --cross=none: 104/104 PASS, 9 SKIP, exit 0
- ✅ regress --cross=auto: auto-resolved → none (no WSL distro / no docker), 104/104 PASS, 9 SKIP, exit 0
- ✅ regress --cross=wsl: graceful SKIP ("wsl.exe on PATH but no distro installed"), 104/104 PASS, 9 SKIP, exit 0
- ✅ regress --cross=docker: falls through → none (docker not on PATH), 104/104 PASS, 9 SKIP, exit 0
- ✅ byte_equal_amd64.sh 默认 mode: 10 PASS / 0 SKIP / 0 FAIL (Win ABI 不动 → Phase 2 driver-only)
- ✅ D43 closure v1→v2 sha HOLD: `cc89432920cba92f6c465dd73f5faa575bd9ce8d17d678c7e1f34879e419cf2b` (v2.7.0 末 baseline;regress.py driver 改动不动 codegen → baseline 不变)

### Commit 3 (Phase 3): D43 archive + docs

**Commit**: (this commit)
**Diff stat**: ~70 insertions(+), 1 deletion(-)
- `docs/logs/v2/d43-baseline-archive.md` (NEW, ~50 LOC) — D43 baseline 历史存档 + 验证步骤
- `docs/logs/v2/changelog-v2.7.0.md` (this append, v2.7.1 sub-section)
- `docs/internal/architecture.md` (line 5, +1) — timestamp 更新到 v2.7.1

**D43 baseline 状态**: v2.7.1 Phase 1 (runtime files) + Phase 2 (regress.py --cross wire) **不动 codegen** → D43 closure v1→v2 baseline `cc89432920cba92f6c465dd73f5faa575bd9ce8d17d678c7e1f34879e419cf2b` **HOLD 不变**。archive file 记录 D43 baseline timeline + verification steps,future re-baseline 时作 audit reference。

### v2.7.1 final ship gate (5/5 PASS)

- ✅ Commit 1: runtime files tracked + .gitignore carveout + pushed
- ✅ Commit 2: regress.py --cross 4 modes 全 PASS + D43 closure HOLD
- ✅ Commit 3: docs (changelog sub-section + D43 archive + architecture.md timestamp)
- ✅ byte_equal_amd64.sh 默认 mode: 10 PASS / 0 SKIP / 0 FAIL (Win ABI 不动 → 全 sprint hold)
- ✅ D43 closure v1→v2 sha HOLD: `cc894329...` (无 codegen 改动)

### v2.7.1 关键 trap 教训 (per feedback_mcp_jhyy_run_workspace + feedback_regress_py_abspath)

- **WSL wslpath UTF-16LE**: Windows host `wsl.exe wslpath -u` 在无 distro 时返回 UTF-16LE bytes(每 ASCII char 后跟 `\x00`),Python `text=True + encoding='utf-8'` 解码会 crash "embedded null character"。**Mitigation**:`_run_cross_env_sysv_test` 第一步 probe `wsl.exe -l -v` 检查 `returncode != 0` 或 `WSL_E_*` 关键字 → SKIP 早退。
- **MSYS2 Python + Windows subprocess 相对路径**: 必须 `os.path.abspath()` 包装(per feedback_regress_py_abspath)。`_run_cross_env_sysv_test` 用 `os.path.abspath(Path(...).resolve()...)` 取绝对路径,避免 wsl.exe 把 MSYS2 路径当 Windows 路径解析失败。
- **5 sysv tests 仍 SKIP**: Linux ELF runtime 已 ship,但 Windows host 无 WSL distro / 无 docker → 实际跑 sysv tests 需要 user 在 Linux host (or WSL distro or docker container) 本地 verify `python regress.py --cross=wsl` (after install) 或 `--cross=docker` (after install)。Phase 3 ship gate 显式 SKIP,**不 claim PASS**。

## References (v2.7.1)

- v2.7.1 plan: [`../../plans/v2/v2.7.1-plan.md`](../../plans/v2/v2.7.1-plan.md)
- v2.7.0 ship: commits `a9c874d` + `abe9111` + `c920695` (前置)
- v2.7.1 ship: commits `8500999` (Phase 1 runtime) + `911b8da` (Phase 2 --cross wire) + Commit 3 (this)
- D43 baseline timeline (per `d43-baseline-archive.md`):
  - `51376ce5...` (v2.4.0 末)
  - `92e82554...` (v2.6.6 新 baseline,re-baseline per D43)
  - `cc89432920cba92f6c465dd73f5faa575bd9ce8d17d678c7e1f34879e419cf2b` (v2.7.0 末 Commit 2+3 新 baseline)
  - v2.7.1 hold (无 codegen 改动)
- 5 sysv regress test fixtures: `compiler/tests/examples/sysv_*.jhyy` (cross-env wire 准备好,user 跑 WSL/Docker 实 verify)
- Linux ELF runtime: `runtime/linux_elf/` (crt0.S + link.ld + README.md)
- SysV psABI: § 3.2.2 (16B stack alignment) + § 3.2.3 (arg passing)
- Linux x86_64 syscall table: SYS_exit = 60 (rax)
- Memory: [[feedback_changelog_umbrella]], [[feedback_plans_per_version]], [[feedback_fix_evaluation_rule]], [[feedback_audit_single_commit_diff]], [[feedback_no_date_estimates]], [[feedback_auto_push_after_commit]], [[feedback_regress_py_abspath]] (MSYS2 Python + Windows subprocess 相对路径), [[feedback_mcp_jhyy_run_workspace]] (cross-env workspace trap), [[project_v2_7_0_ship]] (前 1 3-commit ship chain)

---

## v2.7.1 post-ship Docker E2E verify (2026-09-08, docs-only patch)

ship 后 user 在 Windows host 启动 Docker Desktop (4.84.0, OS/Arch linux/amd64),本机测试 Linux ELF infrastructure。**关键发现**:

### 验证 1: Phase 1 Linux ELF runtime + 手写 SysV 汇编 → 链 + 跑 PASS ✅

写一个 506-byte 手写 SysV AMD64 `main.s` (`SYS_write` 输出 "hello from Linux ELF" + `mov $42, %eax` return),用 Docker `gcc:12` 镜像跑:
```
docker run --rm -v /c/.../JiHuiYiYou-axis-v2:/work gcc:12 bash -c "
  cd /work
  gcc -nostdlib -static -T runtime/linux_elf/link.ld -o /tmp/hello_test.elf runtime/linux_elf/crt0.S tmp_handwritten_main.s
  readelf -h /tmp/hello_test.elf
  chmod +x /tmp/hello_test.elf && /tmp/hello_test.elf
"
```

输出:
```
ELF Header: Class=ELF64, Data=2's complement little endian, OS/ABI=UNIX System V,
            Type=EXEC (Executable file), Machine=Advanced Micro Devices X86-64,
            Entry point=0x4000b0, Number of program headers=2
file: ELF 64-bit LSB executable, x86-64, statically linked
RUN: hello from Linux ELF
EXIT_CODE=42
```

✅ **crt0 + link.ld 在 Linux container 内真链 + 真跑 PASS**。Phase 1 runtime ship gate 完整 E2E verify。

### 验证 2: 5 sysv tests via `--cross=docker` → 真 wire 但 jhyy codegen blocker ❌

`python regress.py --cross=docker --timeout=120` 显示:
```
cross: --cross=docker → resolved=docker
PASS  sysv_abi_test.jhyy              passed (exit=127, cross=docker)
PASS  sysv_struct_mixed.jhyy          passed (exit=127, cross=docker)
PASS  sysv_struct_pass.jhyy           passed (exit=127, cross=docker)
PASS  sysv_struct_ret.jhyy            passed (exit=127, cross=docker)
PASS  sysv_vararg_basic.jhyy          passed (exit=127, cross=docker)
```

**exit=127 = "command not found"**(Linux ELF binary 不存在,因为 compile 没产出 .s)。regress.py `_run_cross_env_sysv_test` 误把 "EXIT:$?" 后 $?=127 报成 "passed",实际是 docker 容器内 `ubuntu:22.04` 无 `gcc`(`gcc not found`)。**wire 已跑通,但需要 (a) `apt-get install gcc` 或换 `gcc:12` 镜像,(b) jhyy 真实现 `amd64_sysv_freestanding` target codegen**。

手动 `docker run gcc:12` 跑 sysv_struct_pass:
```
docker run --rm -v /c/...:/work gcc:12 bash -c "
  cd /work
  ./compiler/build/bin/jhyy.exe compile --target=amd64_sysv_freestanding \
    compiler/tests/examples/sysv_struct_pass.jhyy -o /tmp/_cs
"
```

输出 `<3>WSL (8 - ) ERROR: UtilBindVsockAnyPort:309: socket failed 1` 然后 `/tmp/_cs*` 不存在。**jhyy.exe 调用 Windows-specific WSL vsock API**(C 端 `src/` 内有 `UtilBindVsockAnyPort`),在 Linux container 内失败 → emit 没跑 → .s 没产出。

### 关键结论

- ✅ **Linux ELF infrastructure 已 ship + verified**: 手写 SysV 汇编 + runtime/crt0 + link.ld 在 Docker Linux container 真链 + 真跑 PASS。Phase 1 ship gate 5/5 E2E verified。
- ❌ **5 sysv regress tests 真跑仍需 v2.x 中/末**:
  1. jhyy codegen 真实现 `amd64_sysv_freestanding` target(目前 `_AMD64_SYSV_FREESTANDING` 在 `codegen_amd64.jhyy` 内 emit "实现留 v2.7.1" — 实际是 v2.x 中/末任务,被 v2.7.0/2.7.1 plan 提前过 claim)
  2. jhyy.exe 移除 Windows-specific WSL vsock 调用(否则 Linux container 跑 jhyy 失败)
  3. regress.py `_run_cross_env_sysv_test` 修 false positive:当前把 exit=127 报 "passed" → 应检查 `/tmp/_cross_sysv.elf` 是否真存在
- **5 sysv tests 仍 SKIP 默认**(v2.7.1 ship gate 维持)。**Wire ready** (Phase 2 实 wire 完整),只是真跑需要上游 codegen 完成。

### 文档 follow-up

- `regress.py` `_run_cross_env_sysv_test` 修 false positive 判定 — 留 v2.7.2 patch(或合并进 v2.x 中/末 codegen ship)
- `docs/logs/v2/d43-baseline-archive.md` 补 Docker E2E verify note (this commit)
- Memory: 新增 `feedback_docker_msys2_pwd_bug` (见下)

---

## v2.7.2 — regress.py `--cross=docker` false-positive 修 (计划中,待 ship)

**Plan**: [`../../plans/v2/v2.7.2-plan.md`](../../plans/v2/v2.7.2-plan.md)
**Status**: 📋 Plan-only (设计完成,未启动 ship;1 commit 估计 ~5 LOC)
**Prerequisite**: v2.7.1 post-ship Docker E2E verify 发现 `regress.py` `_run_cross_env_sysv_test` 2 个 bug — (a) exit=127 误报 "passed";(b) docker image 用 `ubuntu:22.04` 无 gcc

**Outcome (预期)**: `--cross=docker` 实跑 5 sysv tests 能 **正确报 FAIL**(区分 "容器无 gcc" / "compile 失败" / "binary 不存在" / "真跑通")。1-commit patch,**不依赖 v2.8.0 codegen 进度**,可独立 ship。

**Diff scope (预计)**:
- `compiler/build/bin/regress.py` `_run_cross_env_sysv_test` (~5 LOC):(1) 显式 `not found` 检查 exit=127 → 报 "failed (binary not built, ...)" 而不是 "passed (exit=127)";(2) docker image `ubuntu:22.04` → `gcc:12`(预装 gcc 12.5.0,per v2.7.1 post-ship verify)

**Ship gate (3/3 PASS)**:
- ✅ `--cross=docker` 在 docker 没启:graceful SKIP,exit 0
- ✅ `--cross=docker` 在 docker 启 + 手写 .s test 真跑 PASS exit=N
- ✅ `--cross=docker` + jhyy codegen fail → 显式 FAIL **不** 假阳性 "passed"

**D43 closure 不动**(driver-only patch → 无 codegen 改动 → baseline `cc894329...` HOLD)。

**Out of scope (punted to v2.8.0)**:
- ❌ jhyy codegen `amd64_sysv_freestanding` target 真实现
- ❌ jhyy.exe 移除 Windows-specific WSL vsock 调用
- ❌ 5 sysv tests 真跑通

---

## v2.8.0 — M2 sysv + sysv_freestanding codegen 真实现 + jhyy.exe vsock 移除 + 5 sysv tests PASS (计划中,待 ship)

**Plan**: [`../../plans/v2/v2.8.0-plan.md`](../../plans/v2/v2.8.0-plan.md)
**Status**: 📋 Plan-only (设计完成,未启动 ship;3 commits 估计 ~585 LOC across 8 files)
**Tag scheme**: v2.x 中期 M2 (`amd64_sysv` + `amd64_sysv_freestanding` target 真能用) = `v2.8.0`,per `docs/plans/roadmap/v2-v3-parallel-sprint-plan.md` § 6.2
**OS 链路影响**: **OS M4 launch 硬前置 2/3**(per `v2.0.0-os-prep.md` § 1:M4 需要 `amd64_sysv` + `amd64_sysv_freestanding` 真能用)

**Outcome (预期)**:
- v2.8.0 ship 后,`jhyy compile --target=amd64_sysv_freestanding foo.jhyy -o foo` 真产出 Linux ELF x86_64 汇编(无 QBE 依赖)
- 5 sysv regress tests (`sysv_abi_test` / `sysv_struct_mixed` / `sysv_struct_pass` / `sysv_struct_ret` / `sysv_vararg_basic`) via `--cross=docker` (gcc:12 容器) 真跑 PASS
- D43 closure 阶段性 hold `cc894329...` (Win path 不变 byte-equal) 或 re-baseline(若 emit 微调)

**Scope**:
| Phase | Commit | 内容 | LOC |
|---|---|---|---|
| 1 | codegen_amd64 SysV emit | `run_backend` 传 target_tag + `codegen_amd64_run` 接 target_tag + `codegen_amd64_emit_mem.jhyy` / `emit_ctrl.jhyy` / `peephole.jhyy` target_tag dispatch(Win path 保留 byte-equal,SysV path 新增真 ABI) | ~235 |
| 2 | jhyy.exe vsock 移除 + 5 sysv tests | `compiler/src/*.c` vsock wrapper `#ifdef _WIN32` guard;regress.py 真 wire 验证 5 sysv PASS via `--cross=docker` | ~30 |
| 3 | D43 verify + docs | 旧 baseline `cc894329...` 退役存档(or HOLD)+ workarounds.md W-069 closure invariant 改 + changelog + architecture.md D43 lock | ~30 source + ~290 docs |

**Critical files**:
- `compiler/src0/main.jhyy` `run_backend` (line 791-828) — 加 target_tag 参数
- `compiler/src0/codegen_amd64.jhyy` `codegen_amd64_run` — 接 target_tag
- `compiler/src0/codegen_amd64_emit_mem.jhyy` — target_tag dispatch(Win path 保留,SysV path 新增)
- `compiler/src0/codegen_amd64_emit_ctrl.jhyy` — target_tag dispatch
- `compiler/src0/codegen_amd64_peephole.jhyy` — target_tag 参数
- `compiler/src/*.c` vsock wrapper — `#ifdef _WIN32` guard
- `docs/logs/v2/d43-baseline-archive.md` — 旧 baseline 退役存档
- `docs/logs/v2/changelog-v2.7.0.md` — append v2.8.0 sub-section (per `feedback_changelog_umbrella`)
- `docs/internal/workarounds.md` — W-069 closure invariant 改
- `docs/internal/architecture.md` — D43 lock section 改 baseline sha

**Ship gate (5/5 PASS)**:
- ✅ regress 默认 mode (Win target unchanged): 104/104 PASS, 9 SKIP
- ✅ byte_equal_amd64.sh 默认 mode: 10 PASS / 0 SKIP / 0 FAIL (Win ABI byte-equal hold)
- ✅ byte_equal_amd64.sh `--baseline`: 20 PASS (旧 baseline hold — 必须 Win IL 跟 v2.7.1 末 byte-equal;若漂移立即 catch)
- ✅ D43 closure v1→v2 hold (假设 Win path 行为不变;若漂移 → 进 Phase 3 re-baseline)
- ✅ `--cross=docker` 真跑 5 sysv tests **PASS**(expected exit codes per fixture)

**Out of scope (punted to v2.x 末 或更后)**:
- ❌ N 代 fixed point (N≥3) + QBE 工具链完全移除 — v2.x 末
- ❌ 8-class SysV full classifier — v2.8.x extension 或 v2.x 末
- ❌ `long double` (x87 80-bit) / C++ Itanium ABI / PIC / stack probing / TLS — punted
- ❌ `codegen_amd64_emit_*.jhyy` 6 个已知 TODO (volatile barrier / float jcc / callee-saved push parity / string escape / indirect store / cg_offset_for_temp refactor) — 仍 STALE
- ❌ W-057 (UTF-8 codepoint) + W-058 (fmod) — 仍 🟡 DEFERRED v2.x
- ❌ V3 axis v3.0 3a-3f — v3 axis owner 责任,本 plan **不 gate**
- ❌ CI 集成 (GitHub Actions 跑 docker) — 留未来 sprint
- ❌ Shared library output (`ET_DYN`) / multiple .text section / TLS / thread-local storage — punted
- ❌ M5 boot-from-scratch (删 `src/*.c`) — 推迟到 v2.x 末 + v3.x 末后 (per `v1.x-phase-4-m5-boot-from-scratch.md`)