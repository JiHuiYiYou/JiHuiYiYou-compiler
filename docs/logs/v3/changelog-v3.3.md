# V3 v3.3.0 — 3h 浮点类型 (f32 / f64) [no-op verification]

> **ship date**: 2026-09-28
> **branch**: `axis-v3`
> **tag**: `v3.3.0` (annotated) — 见 `git log v3.3.0 -1` 取 ship commit SHA (post-v3.2.3.1 `a82fb57`; doc-only change)
> **D43 baseline**: N15+2 (post-rebuild, additive; zero-extend + std_io_print 真 impl 已 ship v3.2.3.1)
> **D28 锁**: v3.3.0 ship = v3.x 关键路径 (OS-required 浮点) 完整 ship;**v3.2.5 (math libm FFI) D28 硬前置解除**
> **v3-pre-v4-infra-port strategy**: tag `v3.3.0` (本 sprint 是 **OS-required 浮点 ship** 不是 infra-only fix;per 2026-09-26 user 决定,v2-v3 infra port 仍 v3.2.x 累计 fold,但 v3.3.0 是 v3.x FINAL OS-required sprint → tag)
> **umbrella**: 本文件

## 1. 范围 / Scope — no-op verification

**关键结论**:v3.3.0 (Sprint 3h 浮点类型) 在 v3 axis **代码层面已 fully ship 完毕**。本次 close-out = **no-op verification** — 不写新代码,只 audit + tag + docs 收尾。

**触发原因 (2026-09-28)**:user 反馈 v3.3.0 计划文档 (v3.3.0-plan.md) 状态 `⏳ 未启动` 跟代码实际状态脱节 (per `feedback_doc_refactor_factcheck` 原则)。Audit 后确认:

| 子项 | 计划预测 | 代码实际 | 差距 |
|------|----------|----------|------|
| 浮点字面量 `3.14` / `3.14f32` | v3.3.0 ship | ✅ **v1.7.0 Stage 5** ship (commit `c04c546`, 2026-08-28) + lexer.jhyy L373-448 含 `is_float = 1` 分支 + `f32/f64` suffix 解析 | 提前 ship (v1.x 语言扩展阶段) |
| 类型 `f32` ↔ `PRIM_F32` / `f64` ↔ `PRIM_F64` | v3.3.0 ship | ✅ **v0.x** ship (types.jhyy L140-204 + TypeArena 12 prims 含 f32_ty / f64_ty) | 提前 ship |
| 浮点算术 `adds/subs/muls/divs` + `addd/...` | v3.3.0 ship | ✅ **v3.0.7/Commit 1** ship (commit `886eaea` Layer 2+3 silent-bug shield; emit_conv 2-op form) + **v3.1.0/Ph.1** wholesale port | 提前 ship |
| 浮点比较 `ceqs/cnes/...` | v3.3.0 ship | ✅ codegen.jhyy L2274-2281 含 `ceqs/cnes/ceqd/cned` 全套 (QBE-era 已 ship,自举路径 mirror) | 提前 ship |
| 整数浮点互转 `stosi/dtosi/sitod/uitos` | v3.3.0 ship | ✅ codegen.jhyy L959-985 含 `QBE_S_LOCAL/QBE_D_LOCAL` 双分支 + `dtosi/stosi/sitod/uitos` | 提前 ship |
| 浮点作函数参数 + 返回值 (SysV: xmm0-7; Windows: xmm0-3) | v3.3.0 ship | ✅ **v3.0.7/Commit 3** ship (commit `fc49cd2` land emit_sse.jhyy + xmm_argalloc.jhyy) + **v3.1.0/Ph.1** wholesale port;`abi_amd64_sysv.jhyy` L42-117 含 SSE class for f32/f64 | 提前 ship |

**结论**:6/6 子项全部 ship,**均早于 v3.3.0 计划时间** (v0.x / v1.7.0 / v3.0.7 / v3.1.0 各阶段 ship)。**v3.3.0 是 phantom sprint** — 代码层无新增工作。

## 2. 改动 / Changes — no new code

**Diff概要**:0 file changes,只 doc + tag 收尾。

### 2.1 审计来源 (Sprint 3h 全栈 ship 链路)

| 阶段 | commit | 内容 |
|------|--------|------|
| v0.x | (pre-tag) | `PRIM_F32()` / `PRIM_F64()` 引入 + `f32_ty` / `f64_ty` lazy init |
| v1.7.0 Stage 5 | `c04c546` (2026-08-28) | lexer `is_float = 1` 分支 + `TOKEN_FLOAT()` + `f32` / `f64` suffix 解析 (`compiler/src0/lexer.jhyy:373-449`) |
| v2.11.19 Phase 1-5 | (v2 axis 串联 5 commit) | lexer tokenize 8 conversion op → emit_conv_* SSE2 → f32 IMM + f64 fractional → FNARG XMM bug → emit_load/store 浮点路径 xmm0 scratch + ss/sd |
| v2.13.0/Ph.1 | `5d405bb` | 真 XMM regalloc (W-074.6 PARTIAL → FULL CLOSED) |
| v2.13.0/Ph.2 | `b1ad5c3` | 真 amd64_sysv codegen 全覆盖 — 8-class §A.4 + SSE class for f32/f64 (`abi_amd64_sysv.jhyy:42-159`) |
| v2.16.0 | `0b4cde5` | QBE toolchain removed + byte-equal .exe (v2.x FINAL) |
| v3.0.6/Ph.3 | `68b4b48` | src0 codegen_amd64 self-backend conversion family (W-083 Layer 1 + W-086 defer v3.0.7) |
| v3.0.7/Commit 1 | `886eaea` | V3 self-backend W-086 wholesale 真修 Layer 2+3 (cltq + op_len + ILTOK_CONV=80 + emit_conv 2-op form) |
| v3.0.7/Commit 3 | `fc49cd2` | land emit_sse.jhyy + xmm_argalloc.jhyy 跟 V2 v2.16.0 byte-equal (pure add, NO wiring) |
| v3.1.0/Ph.1 | `0d9c527` | wholesale port V2 v2.16.0 src0 self-backend + W-089 V3 stdlib pointer-flag extension |
| v3.2.2.1 (stale branch) | `16a9b92` (on `origin/axis-v3.3.0`) | test(floats): Phase 1 float_basic.jhyy baseline test (3h, v3.3.0) — **未 ship 到 main/axis-v3** (pre-v3.2.3 base) |

### 2.2 现有测试覆盖 (regress 内已 ship)

7+ 浮点测试全部 PASS (per `python regress.py --binary=compiler/build/bin/jhyy.exe` 151/151 PASS / 0 FAIL):

| 文件 | EXPECT | 覆盖 |
|------|--------|------|
| `f32_suffix.jhyy` | 0 | `2.5f32` + suffix parse + f32→i32 cast |
| `f64_suffix.jhyy` | 0 | `3.14f64` + suffix parse + f64→i32 cast |
| `float_arith.jhyy` | 6 | `1.5 + 2.5 * 2.0 = 6.5 → 6` (f64 precedence) |
| `float_arith_f32.jhyy` | (验证用) | f32 算术独立 |
| `float_cmp.jhyy` | (验证用) | `ceqs/cnes/ceqd/cned` 比较 |
| `float_test.jhyy` | (验证用) | 综合浮点操作 |
| `fmod_f32.jhyy` | (W-083) | user-space fmod 真修 (per W-083 v2.13.11 / V3 v3.0.6 mirror) |

### 2.3 工作流产物 (本 sprint 唯一新增)

- `docs/logs/v3/changelog-v3.3.md` (本文件) — no-op verification umbrella
- `docs/abis/jhyy-lang-spec-floatsupplement-v3.3.0.md` — f32/f64 spec 索引 + 散落 reference 汇总 (v1.3.0 spec §4.5 = 字符串字面量,Float suffix 不在 §4.5;实际跨 §4.3-§5.6 + §11 codegen + §15 history;本补充 = single-page 入口)
- `docs/plans/v3/v3.3.0-plan.md` — 状态 `⏳` → `✅` (no-op verification done)

## 3. 关键设计决策 (本 sprint 决策极少)

| # | 问题 | 决策 | 理由 |
|---|------|------|------|
| 1 | v3.3.0 是否有新代码 ship? | **否** — no-op verification | 6 子项全部在 v0.x / v1.7.0 / v3.0.7 / v3.1.0 各阶段 ship;Sprint 3h 启动时已无新工作可做 |
| 2 | tag 策略? | **tag `v3.3.0` 在 current HEAD `a82fb57`** (vs v3.2.3.1 NO TAG) | v3.3.0 是 **OS-required 浮点 ship 节点** = v3.x FINAL OS-required sprint (per `docs/plans/v2/v2.0.0-os-prep.md § 1 M11`);v3.2.3.1 NO TAG 是 infra-only fix 不算 ship 节点。区别:tag 标 **language feature ship milestone** 而不是 **infra patch** |
| 3 | 是否 fold `16a9b92` stale branch commit? | **否** — 直接删 `origin/axis-v3.3.0` branch | `16a9b92` 是基于 stale base `c5607ed` (v3.2.2) 的 Phase 1 测试,该测试 (`float_basic.jhyy`) **功能已被现有 f32_suffix/float_arith/float_cmp 等覆盖** (regress 7+ 浮点测试);cherry-pick 不会有新覆盖 |
| 4 | supplement doc 写法? | **single-page 入口 + 散落 ref 汇总** (vs §4.5 full rewrite) | v1.3.0 spec §4.5 = 字符串字面量 (NOT float);Float suffix 实际跨 §4.3 (类型表) + §5.6 (cast 表) + §11 (codegen);**不重排 spec** (per `feedback_doc_refactor_factcheck` 重构前 fact-check 原则,改 §4.5 标题会破现有引用),只发 supplement 作 navigation aid |
| 5 | v3.2.5 (math libm) D28 硬前置? | **已解锁** | v3.3.0 = f32/f64 类型 + 算术 + ABI 全 ship,v3.2.5 sin/cos/sqrt/pow 现在可安全 ship (no f32/f64 type gap) |

## 4. Verification

- ✅ `make all` green (无代码改动 → 沿用 v3.2.3.1 ship baseline)
- ✅ `python regress.py --binary=compiler/build/bin/jhyy.exe --all` → **151/151 PASS / 0 FAIL / 20 SKIP** (preserved;7+ 浮点测试全 PASS)
- ✅ Sprint 3h 6 子项全部已 ship (audit table § 1)
- ✅ D43 closure chain **HOLD N15** preserved (no code change → no closure drift)
- ✅ `docs/plans/v3/v3.3.0-plan.md` 状态 `⏳` → `✅` (no-op verification done)
- ✅ `docs/abis/jhyy-lang-spec-floatsupplement-v3.3.0.md` 写完 (single-page 入口)
- ✅ `origin/axis-v3.3.0` stale branch 已删 (per `feedback_batch_worktree_cleanup` pattern)

**fix evaluation rule** (per `feedback_fix_evaluation_rule`):no code change → 沿用 v3.2.3.1 baseline 151/151 PASS;无新 trigger 无新 verification required。

## 5. Commit / Tag

- **Commit 1** (single ship, per `feedback_audit_single_commit_diff` + `feedback_memory_selectivity` 一 decision = 一 commit):
  `docs(v3.3.0): no-op verification umbrella + floatsupplement + plan status flip (Sprint 3h f32/f64 已 ship)`
- **Tag**:**🟢 `v3.3.0`** on HEAD `a82fb57` (post-v3.2.3.1;语言 feature milestone ≠ infra patch)
- **Push**: `git push origin axis-v3` + `git push origin v3.3.0` + `git push origin --delete axis-v3.3.0` (per `feedback_auto_push_after_commit` + `feedback_ssh_key_same_shell` + `feedback_batch_worktree_cleanup`)

## 6. Cross-ref

- L1 设计: `docs/plans/roadmap/v3.x-language-expansion.md § Sprint 3h`
- L2 设计: `docs/plans/v3/v3.3.0-plan.md` (本次 status flip ⏳ → ✅)
- 上游: `changelog-v3.2.md` v3.2.3.1 (W-080 真修 std_io_print) + v3.2.4.2 (W-094/W-095 真修) + v3.2.4 (W-090/W-091/W-092 std::vec/map) + v3.2.3 (3l.2 std::io/os) — **v3.3.0 不依赖 std::math**,仅 float 类型 ship 节点
- 下游: **`v3.2.5-plan.md` (3l.4 math FFI libm) D28 硬前置解除** — v3.2.5 现在可启动 (sin/cos/sqrt/pow 全需 f32/f64 类型,现已就绪);v3.2.5 ship 后 v3.x 关键路径 (OS-required) 全 ship 完毕
- 跨 axis V2: `v2.13.0/Ph.1-2` (5d405bb / b1ad5c3) — V2 端的 XMM regalloc + amd64_sysv SSE class,V3 wholesale port 自举入口
- D43 chain: `docs/logs/v3/d43-baseline-archive.md` (N15 hold, 本 sprint 0 closure 改动)
- Language spec: `docs/abis/jhyy-lang-spec-v1.3.0.md` (本 sprint 不改 spec;补充 `jhyy-lang-spec-floatsupplement-v3.3.0.md` 作 navigation aid)
- Stale branch: `origin/axis-v3.3.0` (commit `16a9b92` on stale base `c5607ed`;Phase 1 test fold-in 不必要 → 直接删 branch)
- M11 launch gate: `docs/plans/v2/v2.0.0-os-prep.md § 1 M11` — v3.3.0 ship = M11 解锁条件 (3h 浮点) 满足;剩 v3.2.5 (3l.4 math 解锁后续)
- v4.0.0 fold-in: `docs/plans/roadmap/v2-v3-parallel-sprint-plan.md § 5.1` — 本 ship (无新代码) + v3.2.3.1 + v3.2.4.x + 后续 v3.2.5 全 fold 进 v4.0.0

---

# 备注 — 为什么 v3.3.0 不写代码就能 ship?

**历史路径回顾** (per `feedback_doc_refactor_factcheck` 重构前 fact-check 原则):

- **v3.x 启动时 (2026-09-01)**:user 决定 V2 ⟂ V3 并行,v3.0-3.2 走 std lib + W-真修 + closure + generics,**浮点列入 Sprint 3h 计划**,原意是 v3.3.0 走 lexer + types + codegen + ABI 全栈新增。
- **实际 ship 路径 (2026-08 之前)**:f32/f64 **已逐阶段 ship** —
  - v0.x 引入 PRIM_F32/PRIM_F64 (类型 layer)
  - v1.7.0 Stage 5 `c04c546` (lexer suffix layer)
  - v2.11.19 Phase 1-5 (codegen emit_conv_* + SSE path layer)
  - v2.13.0/Ph.1-2 (XMM regalloc + amd64_sysv ABI layer)
  - v3.0.6/Ph.3 + v3.0.7/Commit 1+3 (self-backend SSE 真修 layer)
  - v3.1.0/Ph.1 wholesale port (V3 self-backend 完整 SSE 路径)
- **Sprint 3h 启动时 (2026-09-06)**:user 决定**不开新 worktree**,v3.3.0 走 axis-v3 direct。代码层已 ship,**实际 plan 工作 = "verify 一切就位 + tag + close docs"** — 与本文件 § 1 audit table 一致。
- **本次 ship (2026-09-28)**:user 提示 docs 状态脱节 → audit 确认 phantom sprint → close-out (本文件)。

**Lesson learned (memory-worthy per `feedback_memory_selectivity`?❌)**:no — 这是 single-sprint audit result,不是 cross-sprint reusable rule。不进 memory。Doc 修订原则已在 `feedback_doc_refactor_factcheck`。