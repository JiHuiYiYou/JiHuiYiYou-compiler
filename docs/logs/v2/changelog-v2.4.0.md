# Changelog — v2.4.0 (umbrella: 多目标 dispatcher 完整化 + byte-equal 三件套)

> **承接**: v2.3.0 ship (tag `v2.3.0`, `54d93df`, 2026-09-04) — hello-freestanding.efi 跑 OVMF(首个 E2E 启动验证);regress 持平 104/104 PASS;selfhost closure 4-stage .il byte-equal sha=`312ee9ff`。
> **触发**: v2.3.0 ship 后立刻启动(per 2026-09-01 user 决定的 5 版本串行 sprint 计划)。**v2.0 阶段 Sprint C = 阶段收尾**:闭环 D26 byte-equal 三件套完成定义 + multi-target CLI 表面完整化。**ship v2.4.0 = v2.0 阶段 ship + v3.0 3a-3f 启动前置全部解除**。
> **scope**(per [`v2.4.0任务清单 + 概要设计.md`](../../plans/v2/v2.4.0任务清单 + 概要设计.md)):
> 1. **dispatcher CLI 完整化** — `target_dispatch.jhyy` 加 `target_help` / `target_status` / `jh_target_count`;C-side mirror 同步;`main.jhyy` 加 `--help` flag;**amd64_sysv stub 保留 fatal**(per user 2026-09-04 确认);**不加 -c flag**(per user 2026-09-04 确认:已被 `compile` 子命令覆盖)
> 2. **byte-equal 三件套脚本** — `byte_equal.sh` 新建(.il + .s + .exe byte-equal 跨 jhyy_v1 ↔ jhyy_v2)+ **D26 reproducibility recipe**(jhyy link line `-g0 -Wl,--build-id=none` + `SOURCE_DATE_EPOCH=1234567890` via `jh_setenv`)
> 3. **regress.py 集成** — `--byte-equal` opt-in flag + `test_byte_equal()` subprocess wrapper
> 4. **plan doc audit-note fix** — `v2.4.0任务清单 + 概要设计.md` 修 12 处 stale(路径 / baseline / drop list)
>
> **Scope 调整理由**(per Plan agent audit 2026-09-04 vs 原 plan doc):
> - 原 plan 列 4 stage 范围 = 450 行;audit 后实际只需 **~390 行**(drop 4 items:`-c` flag / `amd64_sysv` behavior 改 / IL emit 顺序稳定化 / `s_deterministic_test.sh`)
> - `-c` flag 已被 `jhyy compile <file>` 子命令覆盖
> - `amd64_sysv` 当前 fatal 已 OK(message 已指向 M2),改 warning+empty emit 触发 codegen 改动 + byte-equal baseline 重做
> - IL emit 顺序稳定化已被 `jhyy_selfhost_check` 4-stage closure chain 隐式覆盖
> - `s_deterministic_test.sh` 被 byte_equal.sh [2/3] .s byte-equal step 覆盖
> - 原 plan 路径 / baseline 措辞过时(实际 regress 104/104;实际路径 `compiler/src0/target_dispatch.jhyy` 无子目录)
>
> **用户 3 决策**(2026-09-04 AskUserQuestion):
> 1. `amd64_sysv` stub 保留 fatal(不动 `codegen.jhyy:3783-3786`)
> 2. byte_equal.sh 包含 `.exe` 三件套(完整 D26)
> 3. top-level `-c` flag 不加
>
> **关键 discipline**(同 v2.0.0 umbrella):
> - Author `JHYY <15901598712@163.com>` + Co-author `MiniMax-M3 <noreply@MiniMax>`
> - **5/5 PASS on target test**(per `feedback_fix_evaluation_rule`)— byte-equal 5/5 PASS(.il + .s)+ .exe INFORMATIONAL
> - Audit single-commit diff(per `feedback_audit_single_commit_diff`)
> - **Plan doc audit-note fix**(per `feedback_doc_refactor_factcheck`)— 4 commits 中 1 commit 修 12 处 stale

---

## Sprint 状态总览

> **2026-09-04 收**: v2.4.0 ✅ **shipped** (commits `ade0293` / `3babb19` / `b8aa7a9` / `7fb735b`, 2026-09-04,**4 commits ship**)。**已打 v2.4.0 tag**(`v2.4.0` at `7fb735b`)。**v2.0 阶段 5 sprint 全 ship ✅ + v3.0 3a-3f 启动前置全部解除**。
>
> **4 commits 拆分**:
> 1. `ade0293` Stage 1 — target_help/target_status + --help flag
> 2. `3babb19` Stage 2 — D26 byte-equal 三件套(gcc -g0 + SOURCE_DATE_EPOCH + jh_setenv)
> 3. `b8aa7a9` Stage 3 — regress.py 集成 --byte-equal flag
> 4. `7fb735b` Stage 4 — plan doc audit-note fix(12 处 stale)

| Sprint | 状态(2026-09-04) | 摘要 |
|--------|-----------------|------|
| v2.0.0 | ✅ shipped `719ec25` 2026-09-02 | target dispatcher 起步 |
| v2.1.0 | ✅ shipped `8ac3608` 2026-09-03 | QBE-level ABI 抽离 |
| v2.2.0 | ✅ shipped `896a329` 2026-09-03 | spec 锁定 |
| v2.3.0 | ✅ shipped tag `v2.3.0` `54d93df` 2026-09-04 | hello-freestanding.efi 跑 OVMF |
| **v2.4.0** | ✅ shipped tag `v2.4.0` `7fb735b` 2026-09-04 | 多目标 dispatcher + byte-equal 三件套(**v2.0 阶段收尾**)|
| v3.0 3a-3f | 🟡 等 user 启动 | **v2.0 阶段 ship ✅ = 启动前置全部解除** |

---

## v2.4.0 实际 ship 内容(per commit chain `ade0293`..`7fb735b`)

### 新建
- `compiler/tests/bootstrap/byte_equal.sh`(~181 行): D26 byte-equal 三件套验证
  - 三层 byte-equal:[1/3] .il / [2/3] .s / [3/3] .exe(兜底)
  - 用 `compile --target=amd64_win <file>` 形式(V1+V2 都支持)
  - 退出码:.il + .s PASS = 0;任一 FAIL = 1;.exe 状态不影响退出码(INFORMATIONAL)
  - 阶段性 self-equal per D43:跨 v2.0 → v2.x 末 有效;v3.0+ 加新特性后必须重 baseline

### 改动
- `compiler/src0/target_dispatch.jhyy`(+~30 行): 加 `jh_target_count` + `target_help` + `target_status`
- `compiler/src/target/target_dispatch.{c,h}`(+~30 行): C-side mirror 同步
- `compiler/src0/main.jhyy`(+~35 行):
  - `--help` flag argv scan + printf(commands + flags + target list + status)
  - `jh_setenv` extern decl + jh_setenv call(`SOURCE_DATE_EPOCH=1234567890` before `jh_run`)
  - `d26_flags` = `" -g0 -Wl,--build-id=none "` 前置到 gcc cmd line(link step)
- `compiler/src0/jhyy_helpers.c`(+~19 行):
  - 加 `jh_setenv(name, value)` helper: Win32 `SetEnvironmentVariableA`(env 进 Win32 env block, child 经 `CreateProcessW` 继承)+ POSIX `setenv` fallback
- `compiler/src/main.c`(仅注释更新,~7 行): 加注释说明 C-side `compile()` 只被 `jhyy_stage0.exe` 用(构建时 tool, 不需 byte-equal),D26 recipe 实现在 src0/main.jhyy
- `compiler/build/bin/regress.py`(+~90 行):
  - 加 `--byte-equal` argparse flag(opt-in;不影响默认 `regress.py` 104/104 baseline)
  - 加 `test_byte_equal(tests=None)`:subprocess 调 `bash byte_equal.sh` 跑 5 个 default tests
  - `shutil.which("bash")` 取 full path(Windows 上 bare "bash" 被 WSL installer alias 拦截,不是 MSYS2 bash)
  - `text=True, errors="replace"` 防 bash output 非 UTF-8 bytes crash reader thread
  - try/except 包 `subprocess.run`: timeout + generic exception → FAIL
- `docs/plans/v2/v2.4.0任务清单 + 概要设计.md`(修 12 处 stale,~270 行 net change):
  - L5 audit-note / L10 路径 / L40 路径 / L65 baseline / Stage 1.1.2 amd64_sysv 措辞 / Stage 2.1.2 + 2.1.3 drop / Stage 3.1.2 drop / Stage 2 验收测试名 / 总行数 / Risk 表

### 验收
- ✅ `jhyy --help` 输出完整(commands + flags + target list + status)
- ✅ `jhyy --target=amd64_unknown` exit 1 + 列可用 target(已有 per `target_dispatch.jhyy:46`)
- ✅ multi-target 跑通:`--target=amd64_win` 编 hosted;`--target=amd64_win_freestanding` 编 PE/COFF .obj(per `scripts/dev/build/build-efi.sh`)
- ✅ **byte-equal 5/5 PASS**:`byte_equal.sh` 在 5 个 target test(`hello` / `struct_val_pass` / `fib_renamed` / `nested_struct_deep` / `big_test`)上 5/5 PASS(.il + .s 各 5/5 = 10/10, .exe 5/5 INFO)
- ✅ **same binary .exe byte-equal**:同一 jhyy.exe 跑 hello.jhyy 4 次 → byte-equal .exe(sha=`70f9667adb28d08e...`)
- ✅ `python regress.py --byte-equal` 5/5 PASS
- ✅ `python regress.py` 持平 104/104 PASS, 0 failed, 4 skipped
- ✅ selfhost closure 4-stage IL byte-equal sha=`51376ce5721bccb0c81c7deabead1a6012fb76648c424238391018f1890b5761`(v2.4.0 重新 baseline,因 Stage 1 `target_dispatch.jhyy` 加 `target_help` + `main.jhyy` 加 `--help` argv scan 触发 src0 emit 微变,per D43 阶段性 self-equal hold 需重 baseline)
- ✅ 4 commits pushed 到 main
- ✅ v2.4.0 tag 推送(per `feedback_auto_push_after_commit`)

### Binary 状态
- `jhyy.exe`: sha=`3f22a7a53d81c8a5cbef1a63a76c1d53074740df0f1467f90f7e6c21e2761343`(v2.4.0 D26 recipe 落地后 = 跟 src0 emit 同步变;per `feedback_make_clean_too_aggressive.md` IL byte-equal 是 closure invariant,binary sha 是 informational)
- selfhost closure 4-stage IL byte-equal sha=`51376ce5...`(v2.4.0 重新 baseline;v2.1.0 → v2.3.0 期间 frozen sha=`312ee9ff`;v2.4.0 Stage 1+2 触发 src0 emit 变 → 重 baseline;per D43 阶段性 self-equal hold)

---

## 关键决策点(per `coordination.md § 3` + `v2.0.0-os-prep.md § 3`)

| # | 决策 | 落点 | v2.4.0 落点 |
|---|------|------|------|
| **D26** | byte-equal 三件套(.il + .s + .exe)= v2.0 期间要求 | v2.4.0 完整脚本 + D26 reproducibility recipe | `byte_equal.sh` 5/5 PASS ✅ |
| **D43** | byte-equal 阶段性 self-equal(不跨版本)| v2.0 / v2.x 末 byte-equal = jhyy_N == jhyy_{N+1} 自洽;v3.0 / v3.1 落地后 .s / .il 因新特性变化,必须重新 baseline | v2.4.0 selfhost closure 4-stage IL byte-equal 重 baseline sha=`51376ce5...` ✅ |
| user 决策 2026-09-04 | `amd64_sysv` stub 保留 fatal(不动 `codegen.jhyy:3783-3786`)| v2.4.0 不动 codegen.jhyy;留 v2.x M2 实现时再做 | Stage 1.1.2 保留 fatal ✅ |
| user 决策 2026-09-04 | byte_equal.sh 包含 `.exe` 三件套(完整 D26) | v2.4.0 byte_equal.sh 包含 [3/3] .exe byte-equal(INFORMATIONAL)| Stage 2.1.1 ✅ |
| user 决策 2026-09-04 | top-level `-c` flag 不加 | v2.4.0 不加 `-c` flag(已被 `compile` 子命令覆盖) | Stage 1.1.3 ✅ |

---

## 关键数字(2026-09-04 锁定)

| 数字 | 值 | 来源 |
|------|-----|------|
| regress baseline | 104/104 PASS, 0 failed, 4 skipped | v2.4.0 持平 v2.3.0 |
| regress --byte-equal | 5/5 PASS | v2.4.0 Stage 3 |
| selfhost closure(4-stage IL byte-equal)| sha=`51376ce5721bccb0c81c7deabead1a6012fb76648c424238391018f1890b5761` | v2.4.0 ship `7fb735b` 验证(per `jhyy_selfhost_check` MCP tool 跑);v2.1.0 → v2.3.0 期间 frozen sha=`312ee9ff`(per v2.1.0 commit message),v2.4.0 Stage 1+2 触发 src0 emit 变 → 重 baseline(per D43 阶段性 self-equal hold 需重 baseline)|
| jhyy.exe binary sha | `3f22a7a53d81c8a5cbef1a63a76c1d53074740df0f1467f90f7e6c21e2761343` | v2.4.0 ship;v2.0.0 → v2.3.0 frozen sha=`376084ba...` |
| byte-equal 5/5 PASS target test | hello / struct_val_pass / fib_renamed / nested_struct_deep / big_test | v2.4.0 byte_equal.sh 验收 |
| same binary .exe byte-equal | 同一 jhyy.exe 跑 hello.jhyy 4 次 → byte-equal .exe sha=`70f9667adb28d08e...` | v2.4.0 Stage 2 D26 recipe 验证 |
| byte-equal 总改动量 | ~390 行新增(Stage 1+2+3 实际 diff)| `v2.4.0任务清单 + 概要设计.md` 总改动量 |

---

## 跨 sprint 影响

- **v2.0.0 → v2.4.0**: 完整闭环 — 阶段 5 sprint 全 ship;byte-equal 三件套 = D26 完成定义
- **v2.4.0 → v3.0 3a-3f**: **v2.0 阶段 ship ✅ = 启动前置全部解除**(per 2026-09-01 user 决定的 v2.0 阶段串行 ship 策略)— **等 user 启动 v3.0 sprint**:
  - v3.0 3a = inline asm
  - v3.0 3b = #[naked] fn
  - v3.0 3c = volatile load/store
  - v3.0 3e = #[link_section]
  - v3.0 3f = memory barrier
  - v3.0 3d = #[no_std] + core(**软 ship**, M1 launch 不依赖 per D10)
- **v2.4.0 → M1 launch**: 间接(M1 launch 启动条件 = v2.0 阶段 ship ✅ + v3.0 3a-3c/3e-3f 全 ship;3d 软 ship 例外)
- **v2.4.0 → v2.x 中/末**: 间接(byte-equal baseline sha=`51376ce5...` = v2.x 中期(自写 QBE 后端 / amd64_sysv 实 impl / 确定性 regalloc / peephole / N 代 fixed point)的起点;期间 byte-equal 必须重 baseline per D43)
- **v2.4.0 → v2.x 末 → M5 boot-from-scratch**(per `v1.x-phase-4-m5-boot-from-scratch.md` 推迟决策 2026-08-14)— v2.x 末 QBE 自写 + v3.x 末 runtime 重写后,一次性删 `src/*.c` + untrack QBE + 删 runtime.c,完成"jhyy 编 jhyy" 0 C 依赖闭环

---

## 关联文档

- v2.4.0 任务清单 → [`../../plans/v2/v2.4.0任务清单 + 概要设计.md`](../../plans/v2/v2.4.0任务清单 + 概要设计.md)(含 12 处 stale fix)
- v2.4.0 详细 scope 决策记录(per Plan agent audit 2026-09-04 vs 原 plan doc)| 见 `docs/plans/v2/v2.4.0任务清单 + 概要设计.md` § Summary of Changes 末段 + 4 commits commit message
- byte_equal.sh → [`../../../compiler/tests/bootstrap/byte_equal.sh`](../../../compiler/tests/bootstrap/byte_equal.sh)
- D26 spec 来源 → `coordination.md § 3 D26`(2026-08-05 锁)
- D43 spec 来源 → `coordination.md § 3 D43`(2026-09-01 锁)
- 跨项目 OS 时间线 → [`../../../../jhyy_OS/docs/coordination.md`](../../../../jhyy_OS/docs/coordination.md)
- v2.x ‖ v3.x 并行 sprint 调度 → [`../../plans/roadmap/v2-v3-parallel-sprint-plan.md`](../../plans/roadmap/v2-v3-parallel-sprint-plan.md)
- v2.x QBE 自写长线 → [`../../plans/roadmap/v2.x-qbe-rewrite.md`](../../plans/roadmap/v2.x-qbe-rewrite.md)
- v3.x 语言扩展长线 → [`../../plans/roadmap/v3.x-language-expansion.md`](../../plans/roadmap/v3.x-language-expansion.md)
- 阶段其他 umbrella → [v2.0.0](changelog-v2.0.0.md) / [v2.1.0](changelog-v2.1.0.md) / [v2.2.0](changelog-v2.2.0.md) / [v2.3.0](changelog-v2.3.0.md)
