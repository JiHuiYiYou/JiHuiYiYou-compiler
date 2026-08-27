# Changelog v1.0.0 (2026-08-10) — 🏆 **历史性一刻**

**Stage 2 N=3 byte-equal 闭环达成 — jhyy 自举编译器编译自己 (raw .il byte-equal, 4-hop 稳定)**

## 成就

| 项 | 值 |
|---|---|
| **v1.0.0 tag** | commit `eabee0d` (2026-08-10, 取代 v1.0.0-rc `3e19b64`) |
| **里程碑** | M4 (Stage 2 N=3 byte-equal) ✓ |
| jhyy_v1.exe.exe sha | `43c66665edebc6b21160610385b6ae49ddacc2379fc2bbb3f11b72a917da73df` (408 KB) |
| jhyy_v2.exe sha | `d3aeed095b7aaf69c9bc0a681e5989439dab641906491a5bdd2d974078dc59b1` (412 KB) |
| jhyy_v3.exe sha | `536ffcb2690b9f3739ca118b4e4aca468f6774364413444dc034957d026d98f4` (412 KB) |
| **jhyy_v2.il / v3.il / v4.il sha** | **`2445e97da75f0015857948f531b305f0d01bb0e77efa989f20412df7fcfbd983`** (1.378 MB, **3 份 byte-equal**) |
| 4-hop 自举稳定 | jhyy_v4.il = `2445e97d...` (同 sha) |
| jhyy_v2 编 src0/main.jhyy 自身 (jhyy_v2_self.exe) | sha `ce442129...` (binary 字节不同, **.il 仍 byte-equal**) |
| regress.py (C-side jhyy.exe) | **50/53 PASS, 0 failed, 3 skipped** |
| regress_v1.py (jhyy_v1.exe.exe) | **50/53 PASS, 0 failed, 3 skipped** |
| Stage 1 byte-equal | **7/7 PASS** (hello/fib_renamed/struct_val_pass/match_exhaustive/arith/const_array/control_flow) |
| Runtime smoke | jhyy_v2 编 _repro_t0.jhyy EXIT=100 (10+20+30+40) ✓ + fib(10) EXIT=55 ✓ |
| **fix_output_il.py 依赖** | **无** (Sprint 4.25 真修 supersede Sprint 4.19 escape hatch) |

## 闭环定义 (达成)

> **Stage 2 N=3 byte-equal**: jhyy_v1 编 src0/main.jhyy → jhyy_v2.il, jhyy_v2 编 src0/main.jhyy → jhyy_v3.il, jhyy_v3 编 src0/main.jhyy → jhyy_v4.il, **三份 raw .il sha 完全一致** (无 fix_output_il.py 后期处理)。
>
> jhyy_v4 编 src0/main.jhyy → jhyy_v5.il (4-hop 稳定) — fixed point 是 attractor, 不是 transient。
>
> jhyy_v2 编 src0/main.jhyy 自身 (jhyy_v2_self.exe), jhyy_v2_self 编 src0/main.jhyy → jhyy_v2_v3.il sha `2445e97d...` (self-build 路径仍 byte-equal)。

## 三门槛全过

```
✅ 门槛 1: regress.py (C-side jhyy.exe)              → 50/53 PASS, 0 failed
✅ 门槛 2: regress_v1.py (jhyy_v1.exe.exe)           → 50/53 PASS, 0 failed
✅ 门槛 3: Stage 1 byte-equal (jhyy_0 vs jhyy_v1)    → 7/7 PASS
✅ 门槛 4 (新增): Stage 2 N=3 byte-equal (raw .il)   → 4-hop 稳定
```

## 真修里程碑 — Sprint 4.25 A′ sentinel 守卫路径

**W-005 #2 (sentinel pollution) 真根因 (Plan agent 验证 2026-08-10)**:

1. `next_tmp = 1` (ir.c:38) → `kind=IRVAL_TEMP, id=0` 是 sentinel (永不被合法分配)
2. `cg_body_returns()` 纯语法检查 (只看最后 stmt)
3. 函数体 `if c { return A } else { return B }` → `body_returns() == false` → epilogue 跑
5. epilogue → `cg_copy_struct` → 逐字段 emit `copy %t0` → QBE reject
6. NODE_RETURN sret 分支同理

**Fix (8 处 irval_is_undef 守卫)**:

| # | 文件 | 守卫位置 |
|---|------|---------|
| 1 | `compiler/src/ir.h` | `static inline int irval_is_undef(IRVal v)` helper |
| 2 | `compiler/src/codegen.c:142-148` | `cg_copy_struct` 开头 early-return |
| 3 | `compiler/src/codegen.c:1481-1486` | NODE_RETURN sret 分支 |
| 4 | `compiler/src/codegen.c:1718-1728` | cg_func epilogue sret |
| 5 | `compiler/src0/ir.jhyy` | 镜像 `fn irval_is_undef(v: IRVal) -> i32` |
| 6-8 | `compiler/src0/codegen.jhyy` | 镜像 3 处守卫 |

**关键不变量**:
- 守卫只在 `id == 0` (sentinel) 时短路
- `next_tmp = 1` 让 sentinel 永不被 `ir_new_tmp` 分配
- 任何走 sentinel 路径的代码本来就会 emit 非法 IL — 守卫**不改正确程序输出**, 7/7 byte-equal 由构造保持

**撤 WIP** (Sprint 4.21–4.22 多轮 attempt 累积):
- WIP `irval_read(buf: *u8) -> IRVal` helper (按值返回 IRVal, 自相矛盾)
- WIP `NODE_RETURN has_sret` bare-`ret` 分支 (sret void 假设)
- A′ 守卫 supersede 两个 workaround

## 5+ attempts 历史 (Sprint 4.13 → 4.25)

| Sprint | 路径 | 结论 |
|--------|------|------|
| 4.13 (commit 2.45) | IRVal struct layout alignment (DEFINITION 层, 4→8 offset) | 部分修 (修 id@offset 4 vs 8), 但 sentinel 漏 emit 没修 |
| 4.21 Phases B+C+D+G | cg_find_local / cg_copy_struct / cg_expr 全改 `const IRVal*` 指针 | 假说错误 (C-side 已 out-param, 没动真根因) |
| 4.22 | cg_match_pattern `let mut + if/else` 改条件表达式 | 假说错误 (2 种写法 emit 同样污染) |
| 4.23 (commit 2.79) | jhyy-side MAX_LOCALS 512→1024 | 修 39+ `%t0` 污染但 W-005 #2 仍漏 |
| 4.21.21 partial B+C+D+G | 综合 | 修了 sret 但 cg_expr signature mismatch (jhyy-side never migrated) |
| 4.24 (commit 2.80) | `resolve_one_import_v1` in_progress push/pop (W-011) | 修 inline_imports dedup, 但留独立 sret emit bug |
| **4.25 (commit 2.81)** | **A′ sentinel 守卫 (8 处)** | **真修** ✓ |
| **4.26 (commit 2.80+2.81+eabee0d)** | **Stage 2 N=3 byte-equal 重测** | **✅ EMPTY diff** |

## Sprint 4.26 — Stage 2 N=3 byte-equal 重测

**步骤**:

1. C-side rebuild → `jhyy.exe` (新)
2. C-side 编 `src0/main.jhyy` → `jhyy_v1.exe` (sha `43c66665...`) → 复制为 `jhyy_v1.exe.exe`
3. `jhyy_v1.exe.exe` 编 `src0/main.jhyy` → `jhyy_v2.exe` (sha `d3aeed09...`)
4. `jhyy_v2.exe` 编 `src0/main.jhyy` → `jhyy_v3.exe` (sha `536ffcb2...`)
5. **Diff raw .il**: `jhyy_v1.il` / `jhyy_v2.il` / `jhyy_v3.il` 全部 sha `2445e97d...` ✅
6. 4-hop 稳定: `jhyy_v3.exe` 编 `src0/main.jhyy` → `jhyy_v4.il` sha `2445e97d...` ✅
7. self-build 稳定: `jhyy_v2.exe` 编 `src0/main.jhyy` → `jhyy_v2_self.exe` (sha `ce442129...`), `jhyy_v2_self.exe` 编 `src0/main.jhyy` → `jhyy_v2_v3.il` sha `2445e97d...` ✅
8. 三门槛验证: regress 50/53 + regress_v1 50/53 + Stage 1 7/7 ✅
9. Runtime smoke: `jhyy_v2.exe` 编 `_repro_t0.jhyy` EXIT=100, fib(10) EXIT=55 ✅
10. **tag v1.0.0** at commit `eabee0d` (取代 v1.0.0-rc `3e19b64`)

## 已知限制 (不算 blocker, v1.0.0 ship)

1. **覆盖率 50/53** — 47 真实测试 + 3 skipped, 规模小. 工业级通常 ≥1000+ + 第三方 benchmark.
2. **C vs jhyy emit 不 byte-equal** — C-side `jhyy_v1.il` sha `bccc452e...`, jhyy-side `2445e97d...`. v1↔v2↔v3 byte-equal (固定点稳定), 但**收敛到 C 端不达成**.
3. **仍有 ACTIVE workaround**: W-003/W-004/W-006/W-007 还在 workarounds.md 活跃列表 (跟 W-005/W-011 无关, 是 codegen 翻译层缺功能的 workaround).
4. **闭环保守性未测**: 改 src0/ 任何一行, N 代 .il 是否还能 byte-equal? 没 mutation testing 验证.
5. **单平台**: 只 Windows + MSVC + QBE `-t amd64_win`. 无 Linux/macOS/ARM.
6. **无 CI gate**: 不能"git push → 自动验证闭环", 任何 sprint 改动都可能悄悄打破 N=3.
7. **缺 OS 基础设施**: 无 GC, 无 struct exception handling, 无运行时/链接器分离 (PE 自己 emit).
8. **C 编译器最终丢弃** (v1.0 真自举启动门槛) 未达成.

## v1.0.0 = v1.0-self-hosting M4 完成

| 里程碑 | 状态 |
|--------|------|
| M1 — Stage 1 byte-equal (jhyy_0 vs jhyy_v1 emit 一致) | ✅ (Sprint 4.5 C step 4 commit 2.45) |
| M2 — regress_v1.py baseline ≥ 50/53 | ✅ (Sprint 4.5 B ship commit 2.40) |
| M3 — jhyy_v1 编 src0/main.jhyy 成功 | ✅ (Sprint 4.18 fix_il.py 完整化 commit 2.75) |
| **M4 — Stage 2 N=3 byte-equal (jhyy_v1↔v2↔v3 raw .il 一致)** | ✅ **(Sprint 4.25 真修 + 4.26 重测)** |
| M5 — boot-from-scratch (无 C 编译器启动) | ⏸️ backlog (v1.0 完成定义) |

## v1.x 收尾路线 (post-v1.0.0)

按 [`docs/plans/v1/v1.0-post-50-53-plan.md`](../../plans/v1/v1.0-post-50-53-plan.md) Phase 2+3:

- **Phase 2 (style cleanup, 不阻塞 release)**: Sprint 4.5+ 之前 deferred 的 cg_expr signature 重构 / W-003/W-004/W-006 + Bug 1-4 清理
- **Phase 3 (v1.x 完成)**: regress 50/53 → 60+/53 + 第三方 benchmark + Stage 3 更大规模闭环 + CI gate
- **Phase 4 (退出 C 编译器)**: jhyy 编 jhyy 出 jhyy,删 src/ (C 端) — M5 boot-from-scratch
- **Phase 5 (v2.x || v3.x 并行启动)**: QBE 完整重写 (amd64_sysv 多目标) + 语言扩展 (inline asm / naked / no_std / &mut lifetime) — OS M1-M11 硬前置

## 关键 commit

- `b2673b4` — Sprint 4.20 Step 2: Stage 2 N=3 byte-equal **大差实证** (cg_module SEGFAULT @ i=1000/6699)
- `d3242e4` — Sprint 4.21 Phase B: cg_find_local out-param (假说错误, partial ship)
- `be3be33` — Sprint 4.21 Phases C+D+G: IRVal struct pass-by-value 真修 (假说错误, partial ship)
- `9b67e53` — Sprint 4.23 commit 2.79: MAX_LOCALS 512→1024 (真修 W-010)
- `a70cb64` — Sprint 4.24 commit 2.80: inline_imports dedup (真修 W-011)
- `f6f8209` — docs: 合并 Sprint 4.25 (sret) + Sprint 4.26 (W-005 #2) → 单 sprint 4.25
- `6801821` — docs: W-005 #2 真修从 Phase 2 提到 Phase 1 (Stage 2 N=3 强前置)
- `fad9de2` — v0.9 wip commit 2.81: Sprint 4.25 W-005 #2 + sret 一并真修 (A′ sentinel 守卫)
- **`eabee0d`** — **docs: Sprint 4.26 Stage 2 N=3 byte-equal 重测结果 — ✅ EMPTY diff** ⭐
- **`v1.0.0`** (tag) — **取代 v1.0.0-rc (commit `3e19b64` Sprint 4.19 实用闭环)** 🏆

## 相关 memory

- `memory/project_v1_0_0_closure.md` — 本次 ship 完整记录
- `memory/project_sprint4_25_a_prime_sentinel_guard.md` — Sprint 4.25 真修详细
- `memory/project_sprint4_19_stage2_closure.md` — Sprint 4.19 v1.0.0-rc 实用闭环 (Stage 2 escape hatch fix_output_il.py)
- `memory/project_sprint4_24_inline_imports_dedup.md` — Sprint 4.24 W-011 真修
- `memory/project_sprint4_23_max_locals.md` — Sprint 4.23 W-010 真修
- `memory/project_sprint4_21_phase_b_c_d_g_done.md` — Sprint 4.21 partial ship (后被 4.25 覆盖)
- `memory/project_sprint4_13_pivot_failure.md` — Sprint 4.13 IRVal helper pivot 24 sites 失败
- `memory/project_v1_plan_phase_reorder.md` — W-005 #2 真修从 Phase 2 提到 Phase 1
- `memory/project_sprint4_25_merge_w005_sret.md` — Sprint 4.25 + 4.26 合并授权
- 自举路线图 (phase-2 翻译 C 前端 → QBE 完整重写) — per `memory/project_v2_v3_parallel_axes.md` 并行轴
- `memory/project_v2_v3_parallel_axes.md` — v2 ⟂ v3 并行轴
- `memory/project_os_wait_state.md` — OS 端等 compiler 推进 (11 D 锁 + 12 Q 闭环)

## 引用

- W-005 #2 + W-012 (新): `docs/internal/workarounds.md`
- 计划: `C:\Users\liuzhen\.claude\plans\jaunty-orbiting-naur.md`
- v1.0-post-50-53 plan: [`docs/plans/v1/v1.0-post-50-53-plan.md`](../../plans/v1/v1.0-post-50-53-plan.md)
- v1.0 自举路线图: [`docs/plans/roadmap/v1.0-self-hosting.md`](../../plans/roadmap/v1.0-self-hosting.md)
- C 端 changelog (Sprint 4.25 entry): [`docs/logs/v0/changelog-v0.9.0.md`](../v0/changelog-v0.9.0.md)
- v1.0.0-rc predecessor: [`changelog-v1.0.0-rc.md`](changelog-v1.0.0-rc.md)