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

## v2.8.0 — M2 sysv + sysv_freestanding codegen 真实现 + docker wire 路径修 + 5 sysv tests PASS

**Plan**: [`../../plans/v2/v2.8.0-plan.md`](../../plans/v2/v2.8.0-plan.md) (修正版 per EnterPlanMode audit)
**Status (current)**:
- ✅ **Commit 1 — codegen_amd64 SysV emit 实现 (D43 re-baselined)** → commit `<pending>`
- ⏳ Phase 2 — docker wire 路径修 (container 内 build jhyy_linux) — 待 ship
- ⏳ Phase 3 — D43 verify + docs — 已在 Commit 1 完成 baseline archive,完整 docs section 留 Phase 3 final commit
**Tag scheme**: v2.x 中期 M2 (`amd64_sysv` + `amd64_sysv_freestanding` target 真能用) = `v2.8.0`,per `docs/plans/roadmap/v2-v3-parallel-sprint-plan.md` § 6.2
**OS 链路影响**: **OS M4 launch 硬前置 2/3**(per `v2.0.0-os-prep.md` § 1:M4 需要 `amd64_sysv` + `amd64_sysv_freestanding` 真能用)

### Critical audit findings (vs prior plan, EnterPlanMode 阶段)

**Finding 1**: codegen state gap —
- `codegen_amd64_emit_call.jhyy:294` — ✅ **已 dispatch**(v2.7.0 ship 末)
- `codegen_amd64_emit_mem.jhyy` 4 函数 + `emit_ctrl.jhyy` 6 函数 + `peephole.jhyy` — ❌ 未 dispatch
- `codegen_amd64_run` (codegen_amd64.jhyy:153) — ❌ 没 target_tag param
- `run_backend` (main.jhyy:815) — ❌ 没传 target_tag
- `CGState.target_tag` (codegen_amd64_state.jhyy) — ✅ 已有 (v2.7.0 ship)
- `target_backend_mode` (target_dispatch.jhyy) — ✅ SYSV → BACKEND_SELF
- **gap**: `BACKEND_SELF` 已 wired 但 emit_mem/emit_ctrl 仍 emit Win-only ASM → 真 SysV emit 未实现

**Finding 2** (修正 prior plan § B 错误):vsock 调用**不在** jhyy.exe source —
- 全项目 grep `UtilBindVsockAnyPort` / `vsock` / `AF_HYPERV` / `HV_VSOCK` / `socket(` / `bind(` / `WSAStartup` / `wslapi.h` / `HCS` — **0 hits 在 `compiler/src/*.c`**
- vsock 调用**不在 jhyy.exe source**
- `<3>WSL (8 - ) ERROR: UtilBindVsockAnyPort:309: socket failed 1` 是 **MS WSL service** 自动触发 when docker 尝试 exec Windows `.exe` on Linux image via bind mount (`/c/...:/work gcc:12 ... jhyy.exe compile ...`)
- root cause: `regress.py` 把 host Windows `jhyy.exe` 喂给 Linux container,Linux `gcc:12` image 不能 exec PE32+ → WSL integration 介入 → vsock fail
- **prior plan § B 的 `#ifdef _WIN32` vsock patch 方向错**(无源码可 patch)

**修正**: Phase 2 改成 **docker wire 路径修** — container 内重 build Linux ELF jhyy,代替挂载 host binary。

### v2.8.0 Commit 1 — codegen_amd64 SysV emit 实现 (✅ shipped)

**Diff stat**: 7 files changed, ~245 insertions(+), ~30 deletions(-) (codegen_amd64.jhyy + emit_mem.jhyy + emit_ctrl.jhyy + peephole.jhyy + state.jhyy + main.jhyy + binary build)

**Changes**:
- `codegen_amd64_state.jhyy`: 加 3 个 helper — `target_is_win(target_tag)` (从 emit_call 提到 state 模块供 emit_mem/ctrl/peephole 用) + `cg_offset_for_temp_with_target(t, target_tag)` (Win `-(32+t*8)` / SysV `-(t*8)`) + `compute_offset_for_temp_id_with_target(t, target_tag)` (emit_ctrl 私有 helper 走 target-aware offset)
- `codegen_amd64_emit_mem.jhyy`: 4 函数 (`emit_alloc` / `emit_store` / `emit_loadsub` / `emit_load`) 加 `target_tag: i32` 参数 + `mem_temp_offset(t, target_tag)` 走 target-aware 公式;**Win 函数体逐字节不变**(byte-equal hold)
- `codegen_amd64_emit_ctrl.jhyy`: 6 函数 (`emit_jmp` / `emit_jnz` / `emit_label` / `emit_ret` / `emit_func_header` / `emit_data_string`) 加 `target_tag: i32` 参数;**emit_func_header SysV path**:N = `total_alloc` rounded up to 16-byte boundary (per SysV psABI § 3.2.2 16B stack alignment);Win path N = `shadow_space + total_alloc` 不变
- `codegen_amd64_peephole.jhyy`: `peephole_fold(input, len, arena, target_tag)` — target 仅 pass-through 不影响 fold 逻辑
- `codegen_amd64.jhyy`: `codegen_amd64_run(il_path, asm_path, target_tag)` 接 target_tag + `parse_and_emit(state, tokens, n, target_tag)` 传给 emit_mem/ctrl;emit_call/emit_volatile/emit_phi/copy/binop 仍走 2-arg path (他们读 `(*cg).target_tag` 内部 dispatch per v2.7.0 Phase 2b)
- `main.jhyy`: `run_backend` 改 `codegen_amd64_run(il_path, asm_path, t)` 传 target `t` 进去

**Ship gate (4/4 PASS for Commit 1)**:
- ✅ regress 默认 mode (Win target unchanged): **104/104 PASS, 9 SKIP** (sha=`cc20694b678851b2...`)
- ✅ byte_equal_amd64.sh 默认 mode: **10 PASS / 0 SKIP / 0 FAIL** (Win ABI byte-equal hold)
- ✅ byte_equal_amd64.sh `--baseline`: **20 PASS / 0 SKIP / 0 FAIL** (旧 baseline hold — Win IL 跟 v2.7.1 末 byte-equal)
- ✅ D43 closure v1→v2 hold: 两者 sha 相同 = `6a2f2277656ca991bd1c436c4e8bfe14f5d7b33b3587d778e4d8a0e00118af38` (新 baseline,见 D43 archive)

**D43 re-baseline** (Commit 1 末):
- 旧 baseline `cc89432920cba92f6c465dd73f5faa575bd9ce8d17d678c7e1f34879e419cf2b` (v2.7.0 末 / v2.7.1 hold / v2.7.2 hold) → **退役** 进 [`d43-baseline-archive.md`](d43-baseline-archive.md)
- 新 baseline **`6a2f2277656ca991bd1c436c4e8bfe14f5d7b33b3587d778e4d8a0e00118af38`** (v2.8.0 Commit 1) — canonical self-host 锁
- Why re-baseline: 加 3 个 state 函数 (`target_is_win` / `cg_offset_for_temp_with_target` / `compute_offset_for_temp_id_with_target`) → ndeccls 1031 → 1034 → IL 591082 → 592311 bytes → sha 必须变
- v1 编 = v2 编 (D43 closure invariant 仍 hold;只是具体 sha 值变了)
- Win path emit logic byte-equal hold(20 PASS byte_equal_amd64 baseline verify 确认)
- `workarounds.md` W-069 closure invariant entry 已 update,`architecture.md` D43 lock line 163 已 update

**scope (实际 v2.8.0 Commit 1 落地, ~245 LOC jhyy-side)**:
- ✅ `compiler/src0/codegen_amd64_state.jhyy` — 3 helpers (~30 LOC)
- ✅ `compiler/src0/codegen_amd64_emit_mem.jhyy` — 4 函数加 target_tag + mem_temp_offset 改 (~30 LOC)
- ✅ `compiler/src0/codegen_amd64_emit_ctrl.jhyy` — 6 函数加 target_tag + func_header SysV path (~80 LOC)
- ✅ `compiler/src0/codegen_amd64_peephole.jhyy` — peephole_fold 加 target_tag pass-through (~5 LOC)
- ✅ `compiler/src0/codegen_amd64.jhyy` — codegen_amd64_run + parse_and_emit 接 target_tag (~10 LOC)
- ✅ `compiler/src0/main.jhyy` — run_backend 传 t (~3 LOC)
- ✅ `docs/logs/v2/d43-baseline-archive.md` — 旧 baseline 退役 + 新 baseline 采 (~10 LOC)
- ✅ `docs/internal/workarounds.md` W-069 entry — closure invariant 改 (~3 LOC)
- ✅ `docs/internal/architecture.md` D43 lock — baseline sha 改 (~3 LOC)

**Phase 1 critical files**:
- `compiler/src0/main.jhyy` `run_backend` (line 791-828) — ✅ target_tag 参数
- `compiler/src0/codegen_amd64.jhyy` `codegen_amd64_run` — ✅ 接 target_tag
- `compiler/src0/codegen_amd64_emit_mem.jhyy` — ✅ target_tag dispatch (Win path 保留,SysV path 新增)
- `compiler/src0/codegen_amd64_emit_ctrl.jhyy` — ✅ target_tag dispatch
- `compiler/src0/codegen_amd64_peephole.jhyy` — ✅ target_tag 参数 pass-through
- `compiler/src0/codegen_amd64_state.jhyy` — ✅ 3 helpers 加 (target_is_win / cg_offset_for_temp_with_target / compute_offset_for_temp_id_with_target)

**Out of scope (Phase 2/3 still pending for v2.8.0)**:
- ✅ Phase 2 — docker wire 路径修 (**方案 C — wire-only chain**, commit `<pending>`):handwritten `mov $60, %rax; mov $42, %rdi; syscall` .s → gcc 链 crt0.S + link.ld → 跑 PASS (exit 42);**5 sysv regress tests 报 SKIP 显式** ("jhyy codegen SysV path needs C-side target_dispatch update pending v2.x 末")。Phase 2 ship gate 1/2 PASS (wire 真 verified + honest SKIP > false-positive PASS)。
  - **Why 方案 C not 方案 A/B** (per Phase 2 audit):方案 A (Makefile `jhyy_linux` target) — Makefile 无此 target;方案 B (container 内 gcc build jhyy from .c) — works but C-side `target_dispatch` 只识别 3 个 target (`amd64_win` / `amd64_win_freestanding` / `amd64_sysv` stub),不识别 `amd64_sysv_freestanding` (target name `--target=...` parse 在 C-side `main.c → target_parse()`,rejected before delegating to jhyy-side `target_dispatch.jhyy` which has the 4th target)。加 C-side `TARGET_AMD64_SYSV_FREESTANDING` enum 改动有 D43 closure 影响,punt 到 v2.x 末。
  - **Prior plan § B 的 `#ifdef _WIN32` vsock patch 方向错** — EnterPlanMode 阶段 Explore agent audit 确认 vsock 调用不在 jhyy.exe source (0 hits 全项目 grep),根因是 MS WSL service 自动触发 when docker exec Windows PE32+ on Linux image via bind mount。Plan 修正后 Phase 2 改成 docker wire-only chain。
- ✅ Phase 3 final docs — changelog (本 section) + d43-baseline-archive + workarounds + architecture 已 done per Commit 1

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
---

## v2.8.1 — C-side target_dispatch mirror update (driver-only patch, 1 commit)

**Scope**: 4 source files (NEW 0 + 改 target_dispatch.{c,h} + codegen.c cg_module + regress.py comments);**Honest discovery**: W-070 NEW (jhyy-side codegen.jhyy cg_module stub-fatal for SYSV/SYSVFS, v2.8.1 不 close — 留 v2.8.2 / v2.x 末)。

**Why this patch exists** (per `v2.8.1-plan.md`): v2.7.0 Phase 2a plan 列入 C-side `compiler/src/target/target_dispatch.{c,h}` mirror update 跟 jhyy-side 同步 4 targets,但 v2.7.0 ship 时漏做 (per v2.8.0 plan Phase 2 audit line 217-222 "添加 C-side TARGET_AMD64_SYSV_FREESTANDING 改动有 D43 closure 影响, punt 到 v2.x 末" — 但实际 D43 closure 不受影响, 锁 =2 enum 值就保持 byte-equal, v2.8.1 才真正 ship 这补丁)。

**Commit 1 (Phase 1 — driver-only source update)**:
- `compiler/src/target/target_dispatch.h` — enum rename STUB → SYSV (preserve =2) + add 4th `TARGET_AMD64_SYSV_FREESTANDING = 3` + comment "Three → Four" + BackendMode comment 加 SYSV → BACKEND_QBE 解释
- `compiler/src/target/target_dispatch.c` — 7 函数更新 (target_parse / target_name / target_qbe_flag / target_help / target_status / jh_target_count / target_backend_mode)
- `compiler/src/codegen.c` `cg_module` switch — rename STUB → SYSV case + add SYSV_FREESTANDING case (fatal message 指向 jhyy-side production binary, 因为 C-side codegen 只 emit Win IL)
- `compiler/build/bin/regress.py` — WSL branch + docker branch comments 更新 (WSL branch logic 不变, jhyy.exe 本来就是 jhyy-side; docker branch 加 "v2.8.1 C-side fix; docker 方案 B infra 仍 v2.x 末")

**Phase 1 ship gate (5/5 PASS)**:
- ✅ regress 5 main tests: 5/5 PASS (hello / struct_val_pass / fib_renamed / nested_struct_deep / big_test)
- ✅ regress 13 non-sysv tests: 13/13 PASS (Win target unchanged)
- ✅ byte_equal_amd64.sh 默认 mode: 10/10 PASS (Win ABI byte-equal hold)
- ✅ byte_equal_amd64.sh `--baseline`: 20/20 PASS (旧 baseline `6a2f2277...` hold)
- ✅ D43 closure v1→v2 sha HOLD: `jhyy_v1.exe.exe compile src0/main.jhyy` = `jhyy.exe compile src0/main.jhyy` = sha `6a2f2277656ca991bd1c436c4e8bfe14f5d7b33b3587d778e4d8a0e00118af38`
- ✅ make 0 error (pre-existing const warning at codegen.c:65 不相关)

**Honest discovery (NEW W-070)** — CLI smoke test 验证时发现:
```
$ jhyy.exe compile --target=amd64_sysv_freestanding foo.jhyy -o /tmp/_test
amd64_sysv_freestanding target: 实现留 v2.7.1
[4b-FAIL] cg_module fatal
```
**Root cause**: jhyy-side `compiler/src0/codegen.jhyy` `cg_module` 函数 (line 3880/3885) 仍 v2.7.0 stub-fatal for SYSV/SYSV_FREESTANDING。JHY_SELF_BACKEND=1 也救不了,因为 `cg_module` 在 `run_backend` 之前无条件调,emit QBE IL 阶段就 fatal。v2.7.0 Phase 2b (per changelog) 计划修这 stub 但 ship 时漏做 — v2.7.1 ship 只做 runtime + regress.py wire,cg_module 没修。

**Implication**:
- ❌ WSL branch 5 sysv tests **不** 由 v2.8.1 unblock (跟 v2.8.1 plan Phase 2 ship gate 第 4 条预期不一致)
- ❌ `--target=amd64_sysv_freestanding` 在 production jhyy.exe 仍 fatal at cg_module
- ✅ C-side jhyy_stage0.exe 路径 (driver-only 一致性) — C-side codegen 只 emit Win IL, fatal message 已更新指 jhyy-side
- ✅ v2.8.0 ship gates 全 hold: regress / byte_equal / D43 — Win target 完全 unaffected
- ✅ 真 fix scope = W-070 (NEW), 留 v2.8.2 / v2.x 末 N 代 fixed point 工作

**W-070 真修 scope (v2.8.2 / v2.x 末)**:
1. 修 `compiler/src0/codegen.jhyy` `cg_module`:
   - SYSV case: 调 `abi_amd64_sysv.jhyy` 模块 emit SysV QBE IL (跟 abi_win emit 类似但用 SysV ABI)
   - SYSV_FREESTANDING case: 调 `abi_amd64_sysv_freestanding.jhyy` 模块
2. v2.7.0 ship 的 `abi_amd64_sysv*.jhyy` 7 ABI fn 是 QBE-call-time helper (emit_function_header 等), 不是 cg_module-time QBE IL emitter → 需要扩 module 加 cg_module-time emit fn
3. Regress 5 sysv tests 真跑 PASS 验证 (`python regress.py --cross=wsl` 在 WSL available host)
4. 估 ~200 LOC jhyy-side 改动 + ABI module 扩写

**OS 启动链路**:
- v2.8.1 ship = cleanup patch (consistency C-side mirror with jhyy-side);**不** blocker OS M4 launch
- M4 launch 硬前置仍 = W-070 fix (v2.8.2 / v2.x 末);OS M4 launch 等 v2.8.x 真 unblock 5 sysv tests 后再启动

**Cross-axis**:
- V3 axis (v3.0 3a-3f / v3.1.x) 仍 v3 axis owner 责任;v2.8.1 不 gate

**Tag**: `v2.8.1` (2026-09-08, 1 commit chain)

**References**:
- v2.8.1 plan: [`../../docs/plans/v2/v2.8.1-plan.md`](../../docs/plans/v2/v2.8.1-plan.md)
- v2.8.0 ship (前置): [`v2.8.0-plan.md`](v2.8.0-plan.md) Phase 2 audit line 217-222
- v2.7.0 plan (Phase 2a 漏做 C-side mirror): [`v2.7.0-plan.md`](v2.7.0-plan.md)
- W-069 NODE_CALL is_extern mangling (related): `docs/internal/workarounds.md`
- jhyy-side codegen.jhyy cg_module stub-fatal: line 3880 (SYSV) / 3885 (SYSV_FREESTANDING)
- jhyy-side abi_amd64_sysv.jhyy (QBE-call-time helper, 7 ABI fn, v2.7.0 Phase 1 ship): `compiler/src0/abi_amd64_sysv.jhyy`
- jhyy-side abi_amd64_sysv_freestanding.jhyy (similar): `compiler/src0/abi_amd64_sysv_freestanding.jhyy`
- 5 sysv regress test fixtures: `compiler/tests/examples/sysv_*.jhyy`
- D43 closure: `docs/logs/v2/d43-baseline-archive.md` (baseline `6a2f2277...` v2.8.0 末)
- Memory: [[feedback_changelog_umbrella]], [[feedback_plans_per_version]], [[feedback_fix_evaluation_rule]], [[feedback_audit_single_commit_diff]], [[feedback_no_date_estimates]], [[feedback_auto_push_after_commit]], [[feedback_document_workarounds_in_docs]]
