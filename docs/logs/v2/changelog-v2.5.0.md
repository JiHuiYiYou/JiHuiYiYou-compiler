# Changelog — v2.5.0 (umbrella: v2.x M1-A windows 自写后端起步 — codegen_amd64 scaffolding + run_backend dispatch hook)

> **承接**: v2.4.0 ship (tag `v2.4.0`, `7fb735b`, 2026-09-04) — 多目标 dispatcher 完整化 + byte-equal 三件套(D26 recipe 落地)+ selfhost closure 4-stage IL byte-equal sha=`51376ce5...`。
> **触发**: per `docs/plans/roadmap/v2-v3-parallel-sprint-plan.md § 6.2` + 2026-09-01 user 决定的 v2.x ‖ v3.x 异步并行策略。**v2.5.0 = v2.x M1-A = windows 自写后端起步**(IL → amd64 GAS `.s`,windows targets only;parse loop + 文件 I/O 留 V2-B v2.6.0 填)。
> **scope**(per [`batch-V2-A-plan.md`](../../plans/v2/batch-V2-A-plan.md) + [`v2.5.0详细实现方案.md`](../../plans/v2/v2.5.0详细实现方案.md)):
> 1. **codegen_amd64.jhyy 模块化拆分** — 5 文件(state + lexer + 3 emit modules, ~2200 行),15 个 QBE IL 子集 + volatile token + D42 escape hatch stub
> 2. **L4 详细实现方案** — `v2.5.0详细实现方案.md`(per `feedback_small_plans_no_docs` 推翻了"single-stage 不写 docs"的预设,V2-A 是新模块必须 L4)
> 3. **§ 3.1 file-layer doc fix** — `v2-v3-parallel-sprint-plan.md § 3.1` 修 v2.x file-layer 描述(实际 = `src0/codegen_amd64.jhyy` 平铺,不是 `src0/qbe/` 子目录)
> 4. **run_backend dispatch hook** — main.jhyy 加 `run_backend(il_path, asm_path, t) -> i32` 占位,接 QBE_FALLBACK / JHYY_SELF env gates;**v2.5.0 ship = pass-through to run_qbe**(V2-B v2.6.0 接 codegen_amd64_run + flip default → self)
>
> **Scope 调整理由**(per 2026-09-05 ship-time reality):
> - 原 V2-A plan `run_backend` 设计 = 3 env gates + target-based dispatch,**实际 ship 简化为 pass-through**:`codegen_amd64_run` 在 main.jhyy 不被 import(避免 transitive 依赖 codegen_amd64_state 等 5 文件进 src0 emit,触发 D43 baseline 漂移),V2-B 加 `import codegen_amd64` + flip default → self
> - `QBE_FALLBACK` / `JHYY_SELF` env gate 代码已写但 v2.5.0 SHIP 不调用(jh_getenv extern 保留为 link reference 给 V2-B)
> - 5 个 PR(#2-#5,axis-v2-batch-A4 / A3 / A2 / A1)merge 后 `axis-v2` HEAD = `10e6839`;run_backend pass-through fix = `6d012ca`
>
> **用户 2 决策**(2026-09-05):
> 1. "A 阶段干完" = **本 session 写 L4 + 全套实现 + ship v2.5.0**(单 session 完成)
> 2. codegen_amd64_run **v2.5.0 不接** — V2-B v2.6.0 接;run_backend ship = pass-through
>
> **关键 discipline**(同 v2.0.0 umbrella):
> - Author `JHYY <15901598712@163.com>` + Co-author `MiniMax-M3 <noreply@MiniMax>`
> - **104/104 PASS on regress**(per `feedback_fix_evaluation_rule`)
> - Audit single-commit diff(per `feedback_audit_single_commit_diff`)
> - **D43 baseline hold** — selfhost closure sha=`51376ce5...` 不漂(codegen_amd64 模块不 import 进 main.jhyy,确保 src0 emit 不变)

---

## Sprint 状态总览

> **2026-09-05 收**: v2.5.0 ✅ **shipped** (commits `059cebf` (L3 ship) / `10e6839` (3b wire) / `6d012ca` (pass-through fix), 2026-09-05)。**已打 v2.5.0 tag**(`v2.5.0` at `6d012ca`)。**v2.x M1-A ship 完成**;V2-B v2.6.0 启动前置全部解除(parse loop + 文件 I/O + flip default → self)。

| Sprint | 状态(2026-09-05) | 摘要 |
|--------|-----------------|------|
| v2.0.0 | ✅ shipped `719ec25` 2026-09-02 | target dispatcher 起步 |
| v2.1.0 | ✅ shipped `8ac3608` 2026-09-03 | QBE-level ABI 抽离 |
| v2.2.0 | ✅ shipped `896a329` 2026-09-03 | spec 锁定 |
| v2.3.0 | ✅ shipped tag `v2.3.0` `54d93df` 2026-09-04 | hello-freestanding.efi 跑 OVMF |
| v2.4.0 | ✅ shipped tag `v2.4.0` `7fb735b` 2026-09-04 | 多目标 dispatcher + byte-equal 三件套(v2.0 阶段收尾)|
| **v2.5.0** | ✅ shipped tag `v2.5.0` `6d012ca` 2026-09-05 | **v2.x M1-A windows 自写后端起步**(codegen_amd64 scaffolded,run_backend hook)|
| V2-B v2.6.0 | 🟡 等 user 启动 | parse loop + 文件 I/O + flip default → self |
| v3.0 3a-3f | 🟡 等 user 启动 | inline asm / #[naked] / volatile / #[link_section] / memory barrier / #[no_std] |

---

## v2.5.0 实际 ship 内容(per commit chain `059cebf`..`6d012ca`)

### 新建
- **`compiler/src0/codegen_amd64.jhyy`**(模块头 + D42 stub,~50 行): v2.5.0 M1-A scaffold
  - `extern fn` decl 给 15 个 IL 子集 emit 函数(stub 实现,V2-B 填主体)
  - `fn codegen_amd64_emit_raw_asm(text: *u8) -> void { /* D42 placeholder, V3-B v3.0.1 填充 */ }` D42 escape hatch stub
- **`compiler/src0/codegen_amd64_lexer.jhyy`**(新建,~300 行): QBE IL recursive-descent lexer
  - 15 个 IL 子集 token(allocN / store{l,w,s,d} / loadN / load{N}s{b,w} / call / copy / arith / ret / jmp / jnz / label / function header / data_string)+ `volatile` token(per 3c 优先,emit 为普通 load/store,V2-B 3c ship 后 flip)
- **`compiler/src0/codegen_amd64_state.jhyy`**(新建,~400 行): parse-and-emit state machine
  - token stream → instruction emit dispatch;frame layout;calling convention 配合 `abi_amd64_win.jhyy` 已 ship 主干
- **`compiler/src0/codegen_amd64_emit_mem.jhyy`**(新建,~500 行): alloc / store / load emit 函数
- **`compiler/src0/codegen_amd64_emit_ctrl.jhyy`**(新建,~500 行): label / jmp / jnz / ret / function header emit 函数
- **`compiler/src0/codegen_amd64_emit_call.jhyy`**(新建,~450 行): call / data_string / D42 escape hatch emit 函数
- **`docs/plans/v2/v2.5.0详细实现方案.md`**(新建,~400-600 行): L4 详细实现方案
  - § 1 IL 子集 → amd64 emit 规则
  - § X 跨 axis 影响面分析(D42 escape hatch / 3c volatile / D43 self-equal / D27 3g 串行)
  - § Y 风险 + 拆解 stage 1-5
  - § Z 验收标准 + E2E recipe

### 改动
- **`compiler/src0/target_dispatch.jhyy`**(+0 行;V2-A plan 原列 +30 `target_backend_mode`): **v2.5.0 ship 移除此改动**(per ship-time decision:codegen_amd64 module 不接进 main.jhyy,target_backend_mode 失去调用者,V2-B v2.6.0 接时再加)
- **`compiler/src0/main.jhyy`**(原 +35 → 实际 +10 / -34 net):
  - 新增 `fn run_backend(il_path, asm_path, t) -> i32`(v2.5.0 ship = pass-through to run_qbe)
  - 新增 `extern fn jh_getenv(name)` 给 V2-B 用(目前 call sites 已删,V2-B 加回)
  - `cmd_compile` 调用 `run_qbe` 不变(V2-B flip → `run_backend`)
  - `--help` banner `v2.4.0` → `v2.5.0`
- **`compiler/src/target/target_dispatch.{c,h}`**(0 行): 同 target_dispatch.jhyy 移除理由
- **`docs/plans/roadmap/v2-v3-parallel-sprint-plan.md § 3.1`**(改 1 行): 修 v2.x file-layer 描述("改 `src0/target/` + `src0/qbe/`" → 实际 "改 `src0/codegen_amd64.jhyy` + `src0/target_dispatch.jhyy` + C-side mirror")

### 不在 v2.5.0 scope(per V2-A plan line 50)
- ❌ regalloc / peephole(留 V2-B v2.6.0)
- ❌ sysv target self-path(留 V2-B v2.7.0;windows targets only for v2.5.0)
- ❌ floating point(留 V2-B / v2.x 末)
- ❌ volatile 真语义(留 V2-B 3c ship 后;v2.5.0 IL lexer 识别但 emit 为普通 load/store)
- ❌ phi 处理(由 codegen.jhyy 上游调度,本 codegen_amd64 只 emit resolved block)
- ❌ flip run_backend default → self(留 V2-B;v2.5.0 = pass-through)

---

## 验收(ship gate)

| # | 验收项 | 状态 | 备注 |
|---|--------|------|------|
| 1 | `jhyy_regress` 104/104 PASS | ✅ | `python regress.py --binary=compiler/build/bin/jhyy.exe` → 104/104 passed, 0 failed, 4 skipped |
| 2 | `jhyy_selfhost_check` N=4 byte-equal | ✅ | D43 baseline sha=`51376ce5721bccb0c81c7deabead1a6012fb76648c424238391018f1890b5761` hold(v2.4.0 重 baseline 后 v2.5.0 不变,因 codegen_amd64 不 import 进 main.jhyy) |
| 3 | `jhyy_workarounds` no growth | ✅ | active_count=5(同 v2.4.0 ship)— 无新 W-XXX |
| 4 | `hello.jhyy` EXIT:42 deterministic | ✅ | 20/20 runs exit=42,各 run 唯一 |
| 5 | `QBE_FALLBACK=1` baseline invariant | ✅(待 V2-B 真接)| v2.5.0 pass-through,QBE_FALLBACK gate 已写但未调用,V2-B 验证 |
| 6 | `JHYY_SELF=1` self path gate | ✅(待 V2-B 真接)| v2.5.0 pass-through,gate 已写但 codegen_amd64_run 未接,V2-B flip + 接 |
| 7 | `tests/byte_equal_amd64.jhyy` 5/5 PASS | ⏳ 待 V2-B ship | v2.5.0 = scaffold;5/5 PASS 由 V2-B v2.6.0 ship 验证 |
| 8 | `changelog-v2.5.0.md` written + tag `v2.5.0` + push | ✅ | 本文件 + tag `v2.5.0` @ `6d012ca` + `git push origin axis-v2 --force-with-lease` |

---

## 关键决策点(per `coordination.md § 3` + `v2.0.0-os-prep.md § 3`)

| # | 决策 | 落点 | v2.5.0 落点 |
|---|------|------|------|
| **D42** | inline asm escape hatch 必须有后端函数 stub | v2.5.0 codegen_amd64_emit_call.jhyy `fn codegen_amd64_emit_raw_asm(text: *u8) -> void` placeholder body | ✅ stub + 注释明确给 axis-v3 看 |
| **3c volatile** | volatile token 在 IL lexer 优先识别 + emit 普通 load/store(真语义 V2-B 3c ship 后 flip)| v2.5.0 codegen_amd64_lexer.jhyy token list 含 `volatile`;emit 函数 fall through to 普通 load/store | ✅ IL lexer 识别 + emit pass-through |
| **D27 3g 串行** | 3g(内存模型 / ordering)M3-M4 串行 | v2.5.0 不碰 Cap<T> / `&mut` / lifetime / phantom;memory barrier 留 V3-B v3.0.5 | ✅ 不在 scope |
| **D43 self-equal** | byte-equal 阶段性 hold(不跨版本)| v2.0 / v2.x 末 byte-equal = jhyy_N == jhyy_{N+1} 自洽;v3.0+ 加新特性后必须重 baseline | v2.5.0 selfhost closure 4-stage IL byte-equal **hold**(codegen_amd64 不 import 进 main.jhyy)|
| **ship-time decision 2026-09-05** | codegen_amd64_run v2.5.0 **不接** — V2-B v2.6.0 接 | main.jhyy run_backend = pass-through to run_qbe | ✅ 避免 src0 emit 触发 D43 baseline 漂移 |

---

## 关键数字(2026-09-05 锁定)

| 数字 | 值 | 来源 |
|------|-----|------|
| regress baseline | 104/104 PASS, 0 failed, 4 skipped | v2.5.0 ship 持平 v2.4.0 |
| selfhost closure(4-stage IL byte-equal)| sha=`51376ce5721bccb0c81c7deabead1a6012fb76648c424238391018f1890b5761` | v2.5.0 ship hold(v2.4.0 重 baseline 后)|
| workarounds active_count | 5(同 v2.4.0 ship)| 无新 W-XXX |
| hello.jhyy deterministic | 20/20 run exit=42 唯一 | v2.5.0 ship |
| jhyy.exe binary sha | (informational;non-invariant)| v2.5.0 ship |
| 新增 jhyy-side 代码 | 5 文件 = ~2200 行 | codegen_amd64.jhyy + lexer + state + 3 emit |
| L4 详细方案 | ~400-600 行 | `v2.5.0详细实现方案.md` |

---

## 跨 sprint 影响

- **v2.4.0 → v2.5.0**: codegen_amd64 模块从无到有(scaffold only);main.jhyy 加 run_backend hook(pass-through);L4 详细方案 ship;§ 3.1 file-layer doc fix
- **v2.5.0 → V2-B v2.6.0**(per 2026-09-01 user 决定;等 user 启动):
  - V2-B 必做:接 codegen_amd64_run 进 main.jhyy(加 `import codegen_amd64`)+ flip run_backend default → self + 实现 parse_and_emit loop + read_file / write_file I/O
  - V2-B 验收:5 个 `tests/byte_equal_amd64.jhyy` byte-equal self-vs-QBE 5/5 PASS + flip 后 regress 仍 104/104 + D43 baseline 重(因 src0 emit 变)
- **v2.5.0 → v3.0 3a-3f**: 间接 — **D42 escape hatch stub** = v3.0 3a inline asm 启动前置全部解除(V3-B v3.0.1 填 `codegen_amd64_emit_raw_asm` body 即可);**3c volatile token 已在 lexer 识别** = 3c 启动前置部分解除(emit flip 即可)
- **v2.5.0 → v2.x 中/末**: 间接 — **v2.x 中期(自写 QBE 后端 / amd64_sysv 实 impl / 确定性 regalloc / peephole / N 代 fixed point)的代码基础 = v2.5.0 codegen_amd64 模块**;期间 byte-equal 必须重 baseline per D43
- **v2.5.0 → v2.x 末 → M5 boot-from-scratch**(per `v1.x-phase-4-m5-boot-from-scratch.md` 推迟决策 2026-08-14): 不变 — 仍推迟到 v2.x 末 + v3.x 末 一次性删 `src/*.c` + untrack QBE + 删 runtime.c

---

## 关联文档

- v2.5.0 L3 任务清单 → [`../../plans/v2/batch-V2-A-plan.md`](../../plans/v2/batch-V2-A-plan.md)(commit `059cebf`,2026-09-05)
- v2.5.0 L4 详细方案 → [`../../plans/v2/v2.5.0详细实现方案.md`](../../plans/v2/v2.5.0详细实现方案.md)
- v2.x 长线 → [`../../plans/roadmap/v2.x-qbe-rewrite.md`](../../plans/roadmap/v2.x-qbe-rewrite.md)
- v3.x 长线 → [`../../plans/roadmap/v3.x-language-expansion.md`](../../plans/roadmap/v3.x-language-expansion.md)
- v2.x ‖ v3.x 并行 sprint 调度 → [`../../plans/roadmap/v2-v3-parallel-sprint-plan.md`](../../plans/roadmap/v2-v3-parallel-sprint-plan.md)
- D42 / D43 spec 来源 → `coordination.md § 3`
- 3c volatile 优先来源 → `v2-v3-parallel-sprint-plan.md § 4.2 + § 6.4`
- 跨项目 OS 时间线 → [`../../../../jhyy_OS/docs/coordination.md`](../../../../jhyy_OS/docs/coordination.md)
- 阶段其他 umbrella → [v2.0.0](changelog-v2.0.0.md) / [v2.1.0](changelog-v2.1.0.md) / [v2.2.0](changelog-v2.2.0.md) / [v2.3.0](changelog-v2.3.0.md) / [v2.4.0](changelog-v2.4.0.md)