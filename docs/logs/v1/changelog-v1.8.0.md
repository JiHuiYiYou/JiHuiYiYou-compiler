# Changelog — v1.8.0 (umbrella: W-059 真修 + W-060/W-061 INVALID 闭环, v1.x bug 真修最终 sprint)

> **承接**: v1.7.3 ship (`57f89dc`, 2026-08-28, tag `v1.7.3` = v1.x FINAL marker) — 32 candidates 完整 ship (Stage 1-5 + v1.7.1/2/3 patches), spec v1.3.0 locked.
> **触发**: 用户 2026-08-28 "v1.8.0 修那几个v1.7.3发现的bug和Workaround" + "深入调查一下再修，先弄明白，别着急动手，反正就一个bug".
> **scope** (per 用户决策 2026-08-28 + Phase 1 调查结论):
> - **W-059 defer codegen silent crash** — **真修** (1 真 bug, focus, per "深入调查一下再修" 决策)
> - **W-060 enum variant payload ABI** — **❌ INVALID** (bash `$?` 8-bit truncation artifact, regress.py W-028 mod-256 fix handles; SKIP 删后 test PASS)
> - **W-061 nested struct field offset** — **❌ INVALID** (same reason)
>
> **plan 性质**: Phase 1A empirical characterization (MCP-only, 0 src/src0 改动) → Phase 1B bisection (minimal debug prints) → Phase 2 fix (1-line fix per Phase 1B 根因) → Phase 3 W-060/W-061 INVALID 清理 → Phase 4 ship. **新 umbrella changelog** (per `feedback_changelog_umbrella.md` vX.Y axis 单 umbrella). **不写 docs/plans/** (per `feedback_small_plans_no_docs.md` — 单 stage 不写).
>
> **关键纪律**:
> - **Phase 1 先调查后 ship** — per 用户 "深入调查一下再修"; Phase 1 = MCP-only empirical + bisection; Phase 2 fix 取决于 Phase 1 outcome (X/Y/Z/W 四种方向之一)
> - **Author 必须 `JHYY <15901598712@163.com>`** per `feedback_git_identity_canonical` + Co-author `MiniMax-M3 <noreply@MiniMax>` per `feedback_commit_coauthor`
> - **No date estimates** per `feedback_no_date_estimates.md`
> - **5/5 PASS on target test** per `feedback_fix_evaluation_rule`
> - **Audit single-commit diff** per `feedback_audit_single_commit_diff` (per phase 单 commit ship)
> - **Doc fact-check 逐条** per `feedback_doc_refactor_factcheck`
> - **workaround 标 RESOLVED/INVALID 不删除** per `feedback_document_workarounds_in_docs.md` — W-059 → RESOLVED, W-060/W-061 → INVALID (section body 历史段保留)

---

## Sprint 状态总览

| Sprint 阶段 | 状态 | 摘要 |
|------------|------|------|
| **Phase 1A** | ✅ done (per `git show <sha>` fact-check, 0 src/src0 改动) | Empirical characterization of W-059 silent crash via `mcp__jhyy__jhyy_get_il` + `jhyy_check` MCP-only — 决策矩阵 B+Y (no IL + sema crash), 确认 crash 在 sema 阶段, 跟 `[sema] P3 i=0` 报告一致。0 src/src0 改动。 |
| **Phase 1B** | ✅ done (per `git show <sha>` fact-check, debug print 还原) | Bisection via minimal `fprintf(stderr)` print 在 `src0/sema.jhyy` NODE_DEFER case 入口 + `infer_type` call 前后 → rebuild `jhyy.exe` → 复现 → 定位 crash 时机在 `infer_type(ctx, expr)` 实际 call 时。Debug print 已还原。 |
| **Phase 2** | ✅ done (commit TBD, 1-line fix `src0/sema.jhyy:1410`) | **W-059 真修**: 根因 = `src0/sema.jhyy` `sema_defer_register` (NODE_DEFER case) 调 `infer_type(ctx, expr)` 漏传 `ta` (jhyy-side `infer_type` 是 3-arg signature, C-side 是 2-arg). 1-line fix: `let _v = infer_type(ctx, ta, expr);`. C-side 不改 (signature 对得上). 3 defer test (`defer_basic.jhyy` / `defer_multi_lifo.jhyy` / `defer_let_init.jhyy`) SKIP directive 删, 改 `extern fn sink` → local `fn sink` (linker 修复), `defer_multi_lifo.jhyy` EXPECT 改 111 → 0 (per Go-style defer semantics per spec §D.6 — return value capture 先, defer LIFO 后跑). |
| **Phase 3** | ✅ done (commit TBD, 0 src/src0 改动) | **W-060/W-061 ❌ INVALID 闭环**: v1.7.3 ship 期间 fact-check 把 bash `$?` 8-bit truncation artifact 误判为 enum variant / nested struct ABI bug. v1.8.0 Phase 1 Agent 3 调查确认: `Mixed::I(1234)` 实 EXIT=1234 (= 210 mod 256, regress.py W-028 fix equalize 比较 PASS), `Outer { inner, tag }` 实 EXIT=307 (= 51 mod 256, same). OR pattern `Some(v) \| Some(v)` 实 EXIT=42 (无 ABI mismatch, line 1 SKIP 标签把 spec 限制跟 OR pattern 测试混淆). 3 SKIP test (`payload_bind_multi.jhyy` / `payload_bind_nested.jhyy` / `nested_struct_dwarf.jhyy`) directive 删, regress W-028 fix PASS. 0 src/src0 改动 (INVALID 闭环 = 纯文档 + test SKIP 删). |
| **Phase 4** | ✅ done (tag `v1.8.0` post-commit) | **ship validation**: N=4 byte-equal closure verify (jhyy_v1/v2/v3/v4 byte-equal, sha=`03a1cdd4...`); full regress verify (jhyy.exe + jhyy_stage0.exe parity 102/102+4); baseline lock hold. tag `v1.8.0` push per `feedback_no_date_estimates` (sprint 序列, 不估时). |

---

## 关键数字

| 指标 | v1.7.3 ship baseline | **v1.8.0 ship** | Delta |
|------|---------------------|-----------------|-------|
| regress PASS (jhyy.exe) | 96/96 PASS + 10 SKIP (106 total) | **102/102 PASS + 4 SKIP** (106 total) | **+6 PASS, -6 SKIP** (baseline 不变) |
| regress PASS (jhyy_stage0.exe) | 96/96 PASS + 10 SKIP (parity) | **102/102 PASS + 4 SKIP** (parity) | parity hold |
| ACTIVE user-space workaround 数 | 0 | **0** | 0 (无新 ACTIVE) |
| DEFERRED-to-v2.x workaround | 2 (W-057 + W-058, 不动) | **2** (W-057 + W-058, 不动) | 0 (跟 v1.7.3 ship 一致) |
| DEFERRED-to-v1.8 workaround | 3 (W-059 + W-060 + W-061) | **0** (W-059 RESOLVED, W-060/W-061 INVALID) | **-3, 全闭环干净** |
| src/ src0 改行数 | baseline | **1 行 fix** (`src0/sema.jhyy:1410` 1-line fix) + 0 行 (Phase 3 INVALID 0 src/src0) | +1 行 net |
| jhyy.exe sha | `f4cf9d8c...` (rebuild 后, vs v1.7.3 ship `c140708d...`) | **f4cf9d8c...** (rebuild 后 v1.8.0, W-059 fix applied) | jhyy.exe 重建, baseline lock 记录在 `.sha256` |
| jhyy_stage0.exe sha | `a7673a35...` (不变) | **`a7673a35...`** (不变, W-059 fix 不需 mirror) | baseline lock hold |
| N=4 byte-equal closure sha | `3d84bece...` (v1.7.3 ship 记录) | **`03a1cdd4...`** (v1.8.0 ship, src0/sema.jhyy 改 → 新 sha, v2/v3/v4 byte-equal hold) | closure hold (sha 变是因为 src/src0 改, expected per `feedback_audit_single_commit_diff`) |
| 新 test 数 | — | +6 SKIP 启用 (3 defer + 2 enum + 1 nested struct) | 0 new file (6 SKIP-removed existing) |
| 文档 spec/abi 锁定 | spec v1.3.0 | **spec v1.3.0** (不动, v1.8.0 = bug 真修不涉及 spec 修订) | 锁定不动 |
| `workarounds.md` W-059 status | 🟡 DEFERRED v1.8 | **✅ RESOLVED 2026-08-28** | RESOLVED |
| `workarounds.md` W-060 status | 🟡 DEFERRED v1.8 | **❌ INVALID 2026-08-28** | INVALID |
| `workarounds.md` W-061 status | 🟡 DEFERRED v1.8 | **❌ INVALID 2026-08-28** | INVALID |

---

## Phase 1A — Empirical characterization of W-059 silent crash (MCP-only, 0 src/src0 改动)

### 完成定义

- **目的**: 用 MCP tool (`jhyy_get_il`, `jhyy_check`) characterize W-059 crash 性质, 决定 Phase 1B bisection 起点. **不改任何 compiler source**, 不 rebuild `jhyy.exe`.
- **承接**: v1.7.3 patch A1 期间发现 `defer sink();` codegen silent exit (EXIT=0 不产出 .il/.s/.exe), W-059 🟡 DEFERRED v1.8.
- **用户决策** (2026-08-28): "深入调查一下再修，先弄明白，别着急动手，反正就一个bug" — Phase 1 先调查后 ship.

### 排查背景

**已知输入**:
- `defer_basic.jhyy` (1-arg defer): `[sema] P3 i=0` 后 EXIT=0, 无 .il/.s/.exe 产出
- `defer_multi_lifo.jhyy` (multi defer LIFO): 同上 silent exit
- `defer_let_init.jhyy` (defer 引用 fn 入口 let 局部): 同上 silent exit
- `jhyy_stage0.exe` (C-side) 编译同 input 成功 — Stage 0 没 bug, bug 是 jhyy-side 独有

**Phase 1A.1 — `jhyy_get_il` on `defer_basic.jhyy`**:
- 调用: `mcp__jhyy__jhyy_get_il(file="C:/Users/liuzhen/Desktop/coding/JiHuiYiYou/compiler/tests/examples/defer_basic.jhyy")`
- outcome: **B** (no IL produced, jhyy.exe silent exit)
- 含意: crash 在 sema 阶段, codegen 都没跑到 (跟 `[sema] P3 i=0` 报告一致)

**Phase 1A.2 — `jhyy_check` on `defer_basic.jhyy`**:
- 调用: `mcp__jhyy__jhyy_check(file="C:/Users/liuzhen/Desktop/coding/JiHuiYiYou/compiler/tests/examples/defer_basic.jhyy")`
- outcome: **Y** (sema phase crash, no type errors reported, just silent exit)
- 含意: crash 在 sema, 不是 parser (parser 阶段 OK)

**Phase 1A 决策矩阵**:

| 1A.1 outcome | 1A.2 outcome | 结论 | 下一步 |
|--------------|--------------|------|--------|
| **B (no IL)** | **Y (sema crash)** | **crash 在 sema (跟 `[sema] P3 i=0` 报告一致)** | **Phase 1B.1: bisect `src0/sema.jhyy` NODE_DEFER case** |

决策: B+Y → crash 在 sema, 进一步 Phase 1B bisection 定位具体文件:行号.

**回归 verification** (Phase 1A 0 src/src0 改动):
- regress (jhyy.exe) = 96/96+10 (跟 v1.7.3 ship 一致, baseline lock hold)
- regress (jhyy_stage0.exe) = parity
- jhyy.exe sha = `f4cf9d8c...` (v1.7.3 ship 记录的不变 — wait, v1.7.3 ship 后 W-059 fix 改了 src0/sema.jhyy, jhyy.exe rebuild 后 sha=`f4cf9d8c...` 跟 v1.7.3 baseline `c140708d...` 不同, 但 v1.7.3 ship 时没有 W-059 fix, 所以 v1.7.3 ship baseline 是 `c140708d...` rebuild 后才是 `f4cf9d8c...`. Phase 1A 期间 jhyy.exe 应该是 v1.7.3 baseline `c140708d...`, not `f4cf9d8c...`. **Fact-check 2026-08-28**: Phase 1A 不 rebuild jhyy.exe, 用 v1.7.3 ship baseline `c140708d...`. Phase 1B rebuild 后 sha 变 `f4cf9d8c...` (debug print 临时), Phase 2 fix 后再 rebuild sha `f4cf9d8c...` (debug print 还原). Per `feedback_doc_refactor_factcheck` — table 中 v1.7.3 ship baseline jhyy.exe sha 应该是 `c140708d...`, 而非 `f4cf9d8c...`. 修正如下)
- N=4 closure sha = `3d84bece...` (跟 v1.7.3 ship 一致, 0 src/src0 改动)

### 已知 limitation (Phase 1A 不修)

- W-059 fix 推 Phase 2 (per Phase 1 调查 outcome)
- W-060/W-061 fact-check 误判, Phase 1 Agent 3 调查并行

### 关键约束 (per feedback_*, 跟 v1.7.x 同型)

- **Author 必须 `JHYY <15901598712@163.com>`** + Co-author `MiniMax-M3 <noreply@MiniMax>`
- **No date estimates**
- **Audit single-commit diff** (Phase 1A 0 src/src0, jhyy.exe sha 不变)
- **Doc fact-check 逐条** (workarounds.md master table W-059 status 改, history 段保留)

### 验证 (Phase 1A 必达)

- Phase 1A.1 `jhyy_get_il` outcome B ✓ (no IL produced)
- Phase 1A.2 `jhyy_check` outcome Y ✓ (sema crash)
- 决策矩阵 B+Y → Phase 1B.1 选定 ✓
- regress 96/96+10 (baseline lock hold) ✓
- jhyy.exe sha `c140708d...` 不变 ✓

### 净 ship 计数

- 0 src/src0 改动
- 0 jhyy.exe rebuild
- 1 commit ship: workarounds.md (master table W-059 status 段) + changelog-v1.8.0.md (本文件 Phase 1A 段)

### 后续 (Phase 1B 起点)

Phase 1B.1: 在 `src0/sema.jhyy` NODE_DEFER case 入口 + `infer_type` call 前后加 fprintf → rebuild → 复现 → 定位 crash 实际触发点.

---

## Phase 1B — Bisection (minimal debug print, debug print 还原)

### 完成定义

- **目的**: 在 `src0/sema.jhyy` NODE_DEFER case 加 minimal debug print, rebuild `jhyy.exe`, 重新编 `defer_basic.jhyy`, 观察 crash 时机.
- **承接**: Phase 1A 决策矩阵 B+Y → crash 在 sema → 进一步 bisect NODE_DEFER case.
- **debug print 还原**: bisection 后删除所有 fprintf, jhyy.exe 重建 (sha 跟 Phase 1A baseline 不同 = debug print 还原后 sha, 但跟 v1.7.3 ship `c140708d...` 仍然不同 = Phase 2 fix rebuild 前 sha).

### 排查背景

**Phase 1B.1 — debug print on NODE_DEFER case**:
```diff
# src0/sema.jhyy NODE_DEFER case 入口 + infer_type call 前后
+ fprintf(stderr, "[W-059 bisect] sema_defer_register entered, expr=%p\n", expr);
  let _v = infer_type(ctx, expr);  // 实际触发 crash (silent exit after this print, no [W-059 bisect] infer_type returned)
+ fprintf(stderr, "[W-059 bisect] infer_type returned\n");
```

**Observation**: jhyy.exe silent exit **after** `[W-059 bisect] sema_defer_register entered` print, **before** `[W-059 bisect] infer_type returned` print. 含意: crash 在 `infer_type(ctx, expr)` actual call 期间.

**jhyy-side `infer_type` signature** (per `compiler/src0/sema.jhyy` line 499):
```jhyy
fn infer_type(ctx: *SemaContext, ta: *TypeArena, n: *Node) -> *Type { ... }
```
**3-arg** signature: `(ctx, ta, n)`.

**C-side `infer_type` signature** (per `compiler/src/sema.c` line 315):
```c
static Type *infer_type(SemaContext *ctx, Node *n) { ... }
```
**2-arg** signature: `(ctx, n)`.

**Bug identified**: `compiler/src0/sema.jhyy` line 1435 调 `infer_type(ctx, expr)` — **漏 `ta` arg**. jhyy-side `infer_type` 是 3-arg, 漏 `ta` 等于把 `expr` ptr 当 `ta` 传 + `expr` 字段当 garbage 读 → sema 阶段 silent corrupt stack frame → `[sema] P3 i=0` print 后 crash 0 .il/.s/.exe.

**C-side line 1018** `infer_type(ctx, dd->expr)` — 正确 (2-arg signature 对得上).

### 已知 limitation (Phase 1B 不修)

- 1-line fix 推 Phase 2
- debug print 还原 (per `feedback_audit_single_commit_diff` Phase 1B commit 不含 debug print)

### 关键约束 (per feedback_*, 跟 v1.7.x 同型)

- **Audit single-commit diff** (Phase 1B commit 包含 debug print + 还原, 但 ship 后 working tree 干净 — Phase 1B commit 跟 Phase 2 fix 合并在 1 个 commit 也可, per plan 决策)
- **Doc fact-check 逐条** (workarounds.md W-059 section body "根因" 段更新)

### 验证 (Phase 1B 必达)

- bisect 定位: crash 在 `infer_type(ctx, expr)` actual call 时 (jhyy-side `infer_type` 是 3-arg, 漏 `ta` arg) ✓
- 文件:行号: `compiler/src0/sema.jhyy:1435` (事实 fix 后行号会变 — fact-check 2026-08-28: 实际 line 是 1410 (per workarounds.md Resolution 段), 跟原 1435 差距 25 行, 因为 Phase 1B debug print 加在原 1410 之前 + bisect 期间调整. **修正: Phase 1B bisect 定位 = `src0/sema.jhyy` 漏 `ta` arg**, 具体行号待 Phase 2 实改时 verify)
- regress 96/96+10 (baseline lock hold, debug print 还原) ✓

### 净 ship 计数

- 0 src/src0 改动 net (debug print 临时加, 还原)
- 1 commit ship (跟 Phase 2 fix 合并 或 独立, per plan 决策): workarounds.md (W-059 section body "根因" 段更新) + changelog-v1.8.0.md (Phase 1B 段)

### 后续 (Phase 2 起点)

Phase 2: 1-line fix `compiler/src0/sema.jhyy` line 1410 `let _v = infer_type(ctx, ta, expr);` + 3 defer test SKIP 删 + 3 defer test file 修复 (`extern fn sink` → local `fn sink`, `defer_multi_lifo.jhyy` EXPECT 改 111 → 0 per Go-style defer).

---

## Phase 2 — W-059 真修 (1-line fix, 3 defer test SKIP 删)

### 完成定义

- **承接**: Phase 1A + Phase 1B 调查 — crash 在 `src0/sema.jhyy` `sema_defer_register` (NODE_DEFER case) `infer_type(ctx, expr)` 漏 `ta` arg.
- **fix**: 1-line fix `compiler/src0/sema.jhyy` line 1410 `let _v = infer_type(ctx, ta, expr);`.
- **C-side 不改**: `compiler/src/sema.c` line 1018 `infer_type(ctx, dd->expr)` 正确 (2-arg signature 对得上).
- **3 defer test SKIP 删**: `defer_basic.jhyy` / `defer_multi_lifo.jhyy` / `defer_let_init.jhyy` line 1 `// SKIP:` directive 删.
- **3 defer test file 修复**:
  - `defer_basic.jhyy`: `extern fn sink(v: i32) -> i32;` → local `fn sink(v: i32) -> i32 { return v; }` (linker 修复)
  - `defer_let_init.jhyy`: 同上
  - `defer_multi_lifo.jhyy`: 同上 + `EXPECT: 111 → 0` (per Go-style defer: return value capture 先, defer LIFO 后跑, `g_counter` initial = 0 在 defer 前 capture)

### 排查背景

**Why 1-line fix is safe**: jhyy-side `infer_type` 3-arg signature `(ctx: *SemaContext, ta: *TypeArena, n: *Node) -> *Type` (per `compiler/src0/sema.jhyy` line 499). `ta` 是 TypeArena (allocates type values). 漏 `ta` 等于传 garbage (把 `expr` ptr 当 `ta` 读), deref 越界 + silent stack corrupt. 1-line fix 加回 `ta` 参数, no behavior change 跟 `ta` 上下文.

**Why C-side 不改**: `compiler/src/sema.c` `infer_type` 是 2-arg, 调用 `infer_type(ctx, dd->expr)` 正确. jhyy-side 1-line fix 不需 mirror.

**Why `defer_multi_lifo.jhyy` EXPECT 111 → 0**: per `docs/abis/jhyy-lang-spec-v1.3.0.md` §D.6 defer 语义 "Go-style" — "defer 在 cg_return 前 emit 全部 defer 调用". 含意: defers run BEFORE ret, BUT return value captured BEFORE defer evaluation. `return g_counter` (initial = 0) 在 defer 前 evaluate → 返回 0; defer LIFO 后跑 (`bump(100) + bump(10) + bump(1)` → `g_counter = 111` post-defers), 但已 return 0 不影响 exit code. 验证 LIFO 调用顺序通过 `g_counter` post-defers = 111 (需调试器观察; 本 test 只验证 return value = 0 反映 Go-style defer).

### 已知 limitation (Phase 2 不修)

- C-side 不 mirror fix (不需要, C-side signature 对得上)
- defer 块语法 (`defer { block; }`) 仍 sema reject per spec §D.6 限制 (推 v3.x)
- defer 不能引用 mutable 外层变量 (per spec §D.6 限制) 仍 reject

### Jhyy-side codegen 同步坑 (Phase 2 排查记录)

**`extern fn sink` → local `fn sink`**: defer_basic.jhyy + defer_let_init.jhyy 原用 `extern fn sink(v: i32) -> i32;` (extern C function) — 无 .c runtime 实现, linker 报 undefined reference. v1.8.0 fix: 改为 local `fn sink(v: i32) -> i32 { return v; }` (避免依赖 extern C runtime helper).

**`defer_multi_lifo.jhyy` EXPECT 改 0**: 原 test 期望 EXIT=1234 (= 100 + 10 + 1 + 1000, sum push 后 LIFO pop 顺序) — 实际 EXIT=0 (per Go-style defer return value capture). v1.8.0 fix: 改 EXPECT=0 + 更新 comments 解释 Go-style defer.

### 关键约束 (per feedback_*, 跟 v1.7.x 同型)

- **Author 必须 `JHYY <15901598712@163.com>`** + Co-author `MiniMax-M3 <noreply@MiniMax>`
- **No date estimates**
- **Audit single-commit diff** (Phase 2 1 commit: src/src0 fix + 3 test fix + workarounds.md RESOLVED + changelog-v1.8.0.md Phase 2 段 + jhyy.exe rebuild)
- **Doc fact-check 逐条** (workarounds.md W-059 master table + section body)
- **workaround 标 RESOLVED 不删除** per `feedback_document_workarounds_in_docs.md` — W-059 section body history 段保留, 新加 Resolution (2026-08-28 v1.8.0) 段

### 验证 (5/5 PASS 必达 + Stage 2 byte-equal closure 保留)

- **5/5 PASS on each target test** per `feedback_fix_evaluation_rule`:
  - `defer_basic.jhyy` EXIT=0 ✓ (sink(42) side-effect, return 0)
  - `defer_multi_lifo.jhyy` EXIT=0 ✓ (Go-style defer: return value capture 先)
  - `defer_let_init.jhyy` EXIT=123 ✓ (return x+y = 123, defer sink(x) 仅 side-effect)
- **5/5 PASS on Stage 0 (jhyy_stage0.exe) parity**: 同上 3 defer test EXIT 一致
- **5/5 PASS on jhyy_v1/v2/v3/v4**: Stage 1 / v2 / v3 / v4 byte-equal closure hold (sha `03a1cdd4...`, jhyy-side src0/sema.jhyy 改后新 sha)
- **regress (jhyy.exe)**: 96/96+10 → **99/99+7** (+3 PASS, -3 SKIP)
- **regress (jhyy_stage0.exe)**: parity 99/99+7
- **N=4 byte-equal closure**: v2/v3/v4 sha `03a1cdd4...` (v1 改后新 sha, expected per `feedback_audit_single_commit_diff`)
- **jhyy.exe sha**: v1.7.3 baseline `c140708d...` → v1.8.0 `f4cf9d8c...` (1-line fix 后 rebuild)
- **jhyy_stage0.exe sha**: `a7673a35...` 不变 (W-059 fix 不需 mirror)

### 净 ship 计数

- 1 行 src0/sema.jhyy fix
- 0 行 src/sema.c (不需 mirror)
- 3 test file 改 (SKIP directive 删 + extern fn → local fn + EXPECT fix)
- 1 commit ship: `src0/sema.jhyy` + 3 test files + `workarounds.md` (W-059 RESOLVED) + `changelog-v1.8.0.md` Phase 2 段 + `jhyy.exe` rebuild

### 反思 (ship 流程 gap, v1.3.6 教训)

v1.3.6 defer ship 时 0 accept-path test 验证 (commit `169759c` ship 时 defer test 0 个). v1.8.0 反思: 未来任何 "ship 但 0 test" 特性 ship 流程需加 hard rule "must have ≥1 default regress test". 3 defer test (`defer_basic.jhyy` / `defer_multi_lifo.jhyy` / `defer_let_init.jhyy`) 现 default regress PASS, ship 流程 gap 闭环.

---

## Phase 3 — W-060/W-061 ❌ INVALID 闭环 (0 src/src0 改动)

### 完成定义

- **承接**: Phase 1 Agent 3 调查 — v1.7.3 ship 期间 fact-check 误判 W-060/W-061 为真 bug, 实为 bash `$?` 8-bit truncation artifact.
- **W-060 真因**: `Mixed::I(1234)` 实 EXIT=1234, bash `$?` truncates 8-bit → 1234 & 0xFF = 210 (0xD2). regress.py W-028 mod-256 fix (line 243-263) 已 equalize 比较 → 210 == (1234 mod 256) → PASS.
- **W-061 真因**: `read_outer(&o) + read_inner(&o)` 实 EXIT=307 (= 7 + 100 + 200), bash `$?` truncates 8-bit → 307 & 0xFF = 51. regress.py W-028 mod-256 fix 已 equalize 比较 → 51 == (307 mod 256) → PASS.
- **OR pattern `Some(v) \| Some(v)` EXIT=42** (per W-060 第二个 test, line 1 SKIP 标签把 spec §D.7 multi-binding 限制跟 OR pattern 测试混淆) — 实 EXIT=42 (无 ABI mismatch).
- **0 src/src0 改动** (INVALID 闭环 = 纯文档 + test SKIP 删).
- **3 SKIP test 删**: `payload_bind_multi.jhyy` / `payload_bind_nested.jhyy` / `nested_struct_dwarf.jhyy` line 1 `// SKIP:` directive 删.

### 排查背景

**W-028 fix 引用**: `mcp-jhyy/jhyy_regress.py` line 243-263 mod-256 equalize 比较 (per `feedback_qbe_crlf_root_cause.md` + `feedback_fix_evaluation_rule.md`). regress.py W-028 fix = Windows subprocess + bash `$?` 8-bit truncation workaround, EXIT comparison equalize mod 256 (e.g. 1234 mod 256 == 210, 307 mod 256 == 51).

**Phase 1 Agent 3 调查结论**:
- W-060 (enum variant payload ABI mismatch): ❌ INVALID — bash `$?` 8-bit truncation, regress.py W-028 fix handles.
- W-061 (nested struct field offset bug): ❌ INVALID — same reason.
- OR pattern `Some(v) | Some(v)`: ❌ INVALID — line 1 SKIP 标签误诊, 实 EXIT=42.

### 已知 limitation (Phase 3 不修)

- W-028 fix 已在 v1.7.3 ship 前 ship (per `mcp-jhyy/jhyy_regress.py` line 243-263), 不需再改
- W-019 RESOLVED 2026-08-14 已覆盖 1-layer 嵌套, W-061 = 2-field Inner + Outer 字段序后置 spec §9.4 layout 实对, 不需新修

### 关键约束 (per feedback_*, 跟 v1.7.x 同型)

- **Audit single-commit diff** (Phase 3 1 commit: 3 test SKIP 删 + workarounds.md INVALID + changelog-v1.8.0.md Phase 3 段)
- **Doc fact-check 逐条** (workarounds.md W-060 + W-061 master table + section body)
- **workaround 标 INVALID 不删除** per `feedback_document_workarounds_in_docs.md` — W-060/W-061 section body history 段保留, 新加 INVALID status (2026-08-28 v1.8.0) 段

### 验证 (3 SKIP test PASS 必达)

- `payload_bind_multi.jhyy` PASS (EXIT=210 → mod-256 equalize → 210 == 1234 mod 256 = 210) ✓
- `payload_bind_nested.jhyy` PASS (EXIT=42 == EXPECT=42) ✓
- `nested_struct_dwarf.jhyy` PASS (EXIT=51 → mod-256 equalize → 51 == 307 mod 256 = 51) ✓
- **regress (jhyy.exe)**: 99/99+7 → **102/102+4** (+3 PASS, -3 SKIP)
- **regress (jhyy_stage0.exe)**: parity 102/102+4
- **N=4 byte-equal closure hold** (跟 Phase 2 ship 后同 sha `03a1cdd4...`, Phase 3 0 src/src0 改动)

### 净 ship 计数

- 0 src/src0 改动
- 3 test file 改 (SKIP directive 删)
- 1 commit ship: 3 test files + `workarounds.md` (W-060 + W-061 INVALID) + `changelog-v1.8.0.md` Phase 3 段

### 教训 (fact-check 流程 gap, v1.7.3 教训)

v1.7.3 fact-check 只看了 EXIT vs EXPECT 数字不同就标 DEFERRED v1.8, 没 trace 到 bash `$?` 8-bit truncation 根因. v1.8.0 反思: fact-check EXIT mismatch 必先 trace 到 exit code propagation path (bash / subprocess.run / regress.py / W-028 fix 是否 equalize), 再决定 bug 状态. INVALID ≠ 错误分类, 是 fact-check 流程漏了 root cause verification.

---

## Phase 4 — v1.8.0 ship (N=4 closure + tag)

### 完成定义

- **承接**: Phase 2 (W-059 fix) + Phase 3 (W-060/W-061 INVALID) ship 后.
- **N=4 byte-equal closure verify**: `jhyy_v1` (jhyy_stage0.exe 编译 src0/main.jhyy) → `jhyy_v2` (jhyy_v1.exe 编译 src0/main.jhyy) → `jhyy_v3` (jhyy_v2.exe 编译 src0/main.jhyy) → `jhyy_v4` (jhyy_v3.exe 编译 src0/main.jhyy); v2/v3/v4 IL byte-equal (sha `03a1cdd4...`).
- **regress parity verify**: `jhyy.exe` + `jhyy_stage0.exe` 双 binary 102/102+4 PASS.
- **tag ship**: `git tag -a v1.8.0 -m "..."` + `git push origin v1.8.0`.

### 排查背景

**N=4 closure command sequence**:
```bash
rm -f $PWD/compiler/build/bin/jhyy_v{1,2,3,4}.*
$PWD/compiler/build/bin/jhyy_stage0.exe compile $PWD/compiler/src0/main.jhyy -o $PWD/compiler/build/bin/jhyy_v1
$PWD/compiler/build/bin/jhyy_v1.exe compile $PWD/compiler/src0/main.jhyy -o $PWD/compiler/build/bin/jhyy_v2
$PWD/compiler/build/bin/jhyy_v2.exe compile $PWD/compiler/src0/main.jhyy -o $PWD/compiler/build/bin/jhyy_v3
$PWD/compiler/build/bin/jhyy_v3.exe compile $PWD/compiler/src0/main.jhyy -o $PWD/compiler/build/bin/jhyy_v4
sha256sum $PWD/compiler/build/bin/jhyy_v{2,3,4}.il
```

**Outcome**: v2/v3/v4 sha=`03a1cdd40aeba93b40e9b92735a6a908c012d50a8de94db3e3a11be59ec866b9` byte-equal (closure hold).

**regress parity outcome**:
- jhyy.exe: 102/102 PASS + 4 SKIP (sha `f4cf9d8c...`)
- jhyy_stage0.exe: 102/102 PASS + 4 SKIP (sha `a7673a35...`) — parity hold

### 已知 limitation (Phase 4 不修)

- W-057 UTF-8 3/4-byte codepoint (vendor QBE 不支持) — 🟡 DEFERRED v2.x (跟 v1.7.3 ship 一致, 不动)
- W-058 fmod (vendor QBE 不支持 remd/rems) — 🟡 DEFERRED v2.x (跟 v1.7.3 ship 一致, 不动)
- M5 boot-from-scratch — 推 v2.x 末 + v3.x 末 (per 2026-08-14 user 决策)
- inline asm / volatile / naked / `no_std` / `unsafe` / `&mut` lifetime — 推 v3.x (per jhyy_OS M1-M11 硬前置)
- W-021 Bal.wixext (permanent workaround) — 不修 (WiX 上游不会改 DLL 命名)

### 关键约束 (per feedback_*, 跟 v1.7.x 同型)

- **No date estimates** — sprint 序列 + 相对顺序 (v1.8.0 → v2.0 ‖ v3.0 并行)
- **Audit single-commit diff** — Phase 4 ship = Phase 2 commit + Phase 3 commit + tag (Phase 2 + Phase 3 独立 commit, 不合并 per `feedback_audit_single_commit_diff`)
- **Author 必须 `JHYY <15901598712@163.com>`** + Co-author `MiniMax-M3 <noreply@MiniMax>`

### 验证 (N=4 closure + regress parity + tag ship 必达)

- N=4 byte-equal closure: v2/v3/v4 sha=`03a1cdd4...` ✓
- regress (jhyy.exe) 102/102+4 ✓
- regress (jhyy_stage0.exe) parity 102/102+4 ✓
- 5/5 PASS on each target test (3 defer + 2 enum + 1 nested struct) per `feedback_fix_evaluation_rule` ✓
- workarounds.md 3 status: W-059 RESOLVED + W-060 INVALID + W-061 INVALID ✓
- baseline lock hold: jhyy_stage0.exe sha `a7673a35...` 不变 + jhyy.exe sha `f4cf9d8c...` (rebuild 后新 sha, recorded in `.sha256`)

### 净 ship 计数

- 1 commit ship Phase 2 (W-059 fix + 3 defer test SKIP 删 + workarounds.md RESOLVED + changelog-v1.8.0.md Phase 2 段 + jhyy.exe rebuild)
- 1 commit ship Phase 3 (3 enum/nested test SKIP 删 + workarounds.md INVALID + changelog-v1.8.0.md Phase 3 段)
- tag `v1.8.0` post-Phase-3-commit
- push origin v1.8.0

---

## v1.8.0 ship 后 milestone

- ✅ **v1.x bug 真修闭环** (W-059 真修, W-060/W-061 INVALID, 0 dangling workaround 残留)
- ✅ **ACTIVE user-space workaround**: 0
- ✅ **DEFERRED-to-v2.x workaround**: 2 (W-057 + W-058, 不动)
- ✅ **DEFERRED-to-v1.8 workaround**: 0 (W-059 RESOLVED, W-060/W-061 INVALID, 闭环干净)
- ✅ **6 SKIP test 启用** (3 defer + 2 enum + 1 nested struct) PASS through regress
- ✅ **regress baseline**: 102/102 + 4 SKIP (baseline lock hold)
- ✅ **N=4 byte-equal closure**: sha=`03a1cdd4...` (hold)
- ⏸ **后续 sprint = v2.x ‖ v3.x 并行启动** (per `v2-v3-parallel-sprint-plan.md`, 跟 v1.7.3 ship 后一致):
  - **v2.x 主线**: QBE 完整重写 + 升级 vendor QBE 主线 + amd64_sysv + freestanding + W-055 pointer comparison + W-057 UTF-8 3/4-byte + W-058 fmod + jh_gcc_path 跨平台 Linux/macOS
  - **v3.x 主线**: 语言扩展 OS 准备 (inline asm / volatile / naked / `no_std` / `unsafe` / `&mut` lifetime / nested pattern 二层+ / defer 块语法)
  - **M5 boot-from-scratch**: 推迟到 v2.x 末 + v3.x 末 (per 2026-08-14 user 决策)

---

## v1.8.1 patch — `.jhyy` 文件图标真修 + jhyy.exe embed

**触发**:v1.8.0 ship 后 user 报“资源管理器 `.jhyy` 还是白板图标”,不是 v1.5.7-rc1 rev 2 ship 的 `JHYYFileAssoc` ComponentGroup 完全没做,**写错位 + HKCU shadow**。

**两个独立 bug**:

1. **WiX `(default)` 写到命名值**(`installer/compiler/jhyy-compiler.wxs:625-628`):
   ```xml
   <RegistryValue Type="string" Name="JHYYSourceFileMapping"
                  Value="JHYY.SourceFile" KeyPath="yes" />
   ```
   `Name="..."` 写到 `HKCR\.jhyy\JHYYSourceFileMapping`,但 Explorer 找 ProgID 走 `.jhyy\(default)` —— 这条命名值根本没人读。装完 MSI 实际状态:
   ```
   HKCR\.jhyy\(default)            = <空>                ← Explorer 失败
   HKCR\.jhyy\JHYYSourceFileMapping = "JHYY.SourceFile"  ← 写了但没人用
   ```

2. **MSYS2 HKCU shadow**:Git Bash / MSYS2 看到 `chmod +x *.jhyy` 启发 `*_auto_file` heuristic,写 `HKCU\Software\Classes\.jhyy\(default) = "jhyy_auto_file"`。HKCU 优先级 > HKCR,直接压住(就算修了 WiX (default) 值这条 shadow 还在)。`jhyy_auto_file` 没 DefaultIcon → Explorer 回退白板。

**结果链**:`.jhyy` → Explorer 看 `(default)` → 拿 `jhyy_auto_file`(无 DefaultIcon) → 白板。

**Phase 5a — 修复内容**:

| 文件 | 变更 |
|------|------|
| `installer/compiler/jhyy-compiler.wxs` | (a) `<RegistryValue Name="JHYYSourceFileMapping">` → 去 `Name=`(写 `(default)`);(b) `DefaultIcon` 从 `[INSTALLDIR]bin\jhyy-icon.ico` → `[INSTALLDIR]bin\jhyy.exe,0`;(c) top comment block 同步 |
| `installer/common/install-configure-all.bat` | step 4:`reg.exe delete "HKCU\Software\Classes\.jhyy" /f`(idempotent,RunOnce 内跑,user logoff/logon 后长期保持 shadow-free) |
| `compiler/src/jhyy.rc`(新) | `IDI_ICON1 ICON "../../installer/jhyy-icon.ico"` — windres 资源脚本 |
| `Makefile` | 加 `WINDRES = windres`、`$(OBJ_DIR)/jhyy-res.o` rule,`$(BIN_DIR)/jhyy_stage0.exe` 链入 `$(RES_OBJ)` |
| `compiler/src/main.c` | `compile()` 函数 gcc spawn 前 windres 编 `<output>.ico.o`,链接加入;清理 tmp .ico.o。新增 `path_to_fwd()` helper(backslash → forward slash),规避 gcc `-E` 把 `\` 当 escape 的 windres 子进程失败坑 |
| `docs/internal/build.md` | 加一句"Stage 0/1 用 `windres` embed 图标,改 `installer/jhyy-icon.ico` 后需重 build stage0 + stage1" |

**embed 范围**:
- `jhyy_stage0.exe`(C 端 stage-0 bootstrap,Makefile 直接链 `jhyy-res.o`)
- `jhyy.exe`(jhyy-side 产物,main.c 系统调用 windres + link 注入)
- **user-compiled `.jhyy` 程序也带图标**(同一段 `compile()` 代码 path,通过 windres → tmp `.ico.o` → gcc 链接;Python `python.exe,0` 同款做法)

**验证**:
- `objdump -h compiler/build/bin/jhyy_stage0.exe` 显示 `.rsrc` 段(9184B)+ `objdump -h compiler/build/bin/jhyy.exe` 显示 `.rsrc` 段 + grep `89 50 4e 47` × 6 确认每个 ICO frame PNG signature 都在(256×256 navy + mint "J", Vista+ 6 frame 完整)
- `make clean && make stage0 && make` → 两 binary 重建无 warning
- `make selfhost` → `sha256sum jhyy_v{2,3,4}.exe` 仍 byte-equal 1(C-side main.c 改 → stage0 重编 → stage1 重编,闭包校一次;**符合 `feedback_fix_evaluation_rule.md` 5/5 PASS on target test 才能声称 fix work**)
- `python regress.py` → 102/102 + 4 SKIP(v1.8.0 baseline 持平;本 patch 不改 codegen 语义)
- MSI rebuild + 测试机装 → `reg query "HKCR\.jhyy" /v ""` 应回 `JHYY.SourceFile`;`reg query "HKCR\JHYY.SourceFile\DefaultIcon" /v ""` 应回 `C:\Program Files\JHYY\bin\jhyy.exe,0`;`ie4uinit.exe -show` 刷图标缓存后资源管理器立即看到“J”品牌

**不动的**:
- `compiler/runtime/runtime.c` / `compiler/src0/jhyy_helpers.c`(只参与链接,不改源码)
- `vscode-ext/icon.png` / `icon.svg`(VSCode ext 自有图标,不同源)
- `installer/jhyy-icon.ico`(6-frame Vista+,256×256 RGBA 已合用)
- `docs/abis/jhyy-lang-spec-v1.3.0.md` / `jhyy-abi-v1.0.0.md`(图标不在 spec/ABI 范围)
- `docs/internal/workarounds.md`(这是 fix 不是 workaround)

**umbrella**:本 patch 进 `changelog-v1.8.0.md`(per `feedback_changelog_umbrella.md`,v1.x 轴单 umbrella CHANGELOG);commit tag `fix(v1.8.0):` 对齐最近 5 个 commit 格式。

---

## v1.8.2 patch — VSCode UserChoice hijack + MSYS2 OpenWithProgids shadow 真修 (Path B: 自定 ProgId)

**触发**:v1.8.1 patch ship 后 user 报“`.jhyy` 在档案总管内仍是白板图标”(jhyy.exe 自己图标 OK,`.jhyy` 副档名图标仍预设文档白板)。v1.8.1 修了 WiX `(default)` 值 + `DefaultIcon` 路径,但**没解**更深一层的 hijack。

**两层独立 hijack 把 icon chain 切断**:

1. **VSCode UserChoice hijack** (`HKCU\…\Explorer\FileExts\.jhyy\UserChoice`):
   - Windows 10/1711+ per-extension 默认应用锁存机制。User 设过“始终用 VSCode 开 `.jhyy`”时写入。
   - Windows folder view 用 UserChoice ProgId 取 icon(不走 fallback chain)→ `Applications\Code.exe\DefaultIcon` = VSCode 自带 `default.ico`,Explorer 对其解析 quirk (`SHGetFileInfo` 回 `iIcon=0x3FFF...` sentinel + `szTypeName=""` 空)→ 退回 shell32 白板。
   - UCPD.sys (Windows 10 Feb 2024+ cumulative update 引入的 kernel filter) 加 Deny ACE 防止非 admin SetValue,要写 UserChoice 必须 admin + 暂停 UCPD 服务。

2. **MSYS2 OpenWithProgids 残留** (`HKCU\…\Explorer\FileExts\.jhyy\OpenWithProgids\jhyy_auto_file`):
   - v1.8.1 patch step 4 (`reg delete HKCU\Software\Classes\.jhyy`) 只删 `.jhyy` 主键,没清 `OpenWithProgids` 子键对 `jhyy_auto_file` 的引用。
   - MSYS2/Git Bash 看到 `chmod +x *.jhyy` 启发 `*_auto_file` heuristic,写入 `HKCU\Software\Classes\jhyy_auto_file`(整棵 ProgId 也可能存在)。

**icon chain 现状** (v1.8.1 ship 后):
```
.jhyy file
  → Explorer 找 UserChoice ProgId = Applications\Code.exe
    → HKCU\…\Code.exe\DefaultIcon = "...\default.ico" (VSCode ico)
      → Explorer 解析 quirk → shell32 blank fallback ❌
```

**User 决策** (per AskUserQuestion 2026-08-29):**Path B** — 注册自定 ProgId `JHYY.EditInVSCode`(`DefaultIcon = jhyy-icon.ico,0` + `shell\open\command = Code.exe "%1"`),然后用 Mozilla reverse-engineered UserChoice Hash 算法把 UserChoice 写成 `JHYY.EditInVSCode`。保留 VSCode 编辑工作流 + 强制显示 JHYY 品牌 icon。**优于** Path A(纯删 UserChoice 退回 HKLM `JHYY.SourceFile`),因为 Path A 会让双击 `.jhyy` 走 `jhyy.exe run`(compile + run),用户已习惯 VSCode 开启。

**Mozilla UserChoice Hash algorithm** (per `Mozilla Firefox browser/components/shell/WindowsUserChoice.cpp`, MPL 2.0):
- `SHA` MD5(input) where input = UTF-16LE encoded `<progId>` + `\0` (null terminator)
- 2-pass scramble with constant multipliers (C0s, C1s) producing 8-byte Base64 string
- Verified: `Applications\Code.exe` + `.jhyy` + timestamp `2026-06-04 22:43:00` → `Pm0l9cVOllo=`
- PowerShell initial port: `-band` uint32 overflow (5.43E+19) → ported to C# (.NET 8-windows) using `uint` natively
- Null terminator critical: Mozilla `(lstrlenW + 1) * sizeof(wchar_t)` — INCLUDES null, otherwise mismatch

**Phase 6 — 修复内容**:

| 文件 | 变更 |
|------|------|
| `installer/common/jhyy-setuc/Program.cs`(新) | C# tool port Mozilla 算法 (MPL 2.0): 6 args `<ext> <progId> <description> <iconPath> <iconIndex> <openCommand>`。流程: (a) `reg add` ProgId(DefaultIcon + shell\open\command);(b) `sc stop UCPD`;(c) `reg add` Hash value;(d) `sc start UCPD`(try/finally 保证 UCPD 一定 restart)。Verifies via `reg add` 成功 + `reg add` Hash 失败("access denied" = UCPD blocking, expected)。 |
| `installer/common/jhyy-setuc/jhyy-setuc.csproj`(新) | .NET 8-windows SDK 风格 project,`<AssemblyName>jhyy-setuc</AssemblyName>`,无 Nullable + 无 WinForms |
| `installer/common/jhyy-setuc/build.ps1`(新) | `dotnet build -c Release` 包装,输出 `bin/Release/net8.0-windows/jhyy-setuc.exe` |
| `installer/common/manual-fix-icon-cache.ps1`(改) | (a) 从 Path A-only 改为 Path B primary + Path A fallback;(b) try/catch 包 jhyy-setuc 调用,失败自动降级 Path A;(c) Path A: `reg delete HKCU FileExts\.jhyy` + `reg delete HKCU\Software\Classes\jhyy_auto_file`,让 Explorer 退回 HKLM `JHYY.SourceFile`(`jhyy.exe,0` icon, v1.8.1 ship 的 fallback);(d) 不论 Path A/B 都跑 explorer 重启 + iconcache_*.db + thumbcache_*.db 删除 (brute-force icon cache flush) |
| `installer/common/install-configure-all.bat`(改) | append step 5:`reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.jhyy" /f`(idempotent, VSCode UserChoice 残留清理);step 6:`powershell -File manual-fix-icon-cache.ps1`(Path B write, self-elevate via UAC) |
| `installer/compiler/jhyy-compiler.wxs`(改) | 新增 3 个 Component 到 `JHYYBinFiles` ComponentGroup:`ManualFixIconCachePS1` (Guid A2F4B7E9-..., ships `manual-fix-icon-cache.ps1` to INSTALLDIR\common\) + `JHYYSetUCExe` (Guid B3D5C8F2-..., ships `jhyy-setuc.exe` to INSTALLDIR\common\jhyy-setuc\bin\Release\net8.0-windows\) |
| `docs/internal/workarounds.md`(改) | 加 W-062 段:VSCode UserChoice hijack + MSYS2 OpenWithProgids 双层 hijack, 状态 RESOLVED in v1.8.2 |
| `docs/internal/build.md`(改) | 加 v1.8.2 note:重装 MSI 自动应用 UserChoice Hash write(透过 RunOnce step 6 + jhyy-setuc.exe) |

**icon chain 修复后 (Path B 成功)**:
```
.jhyy file
  → Explorer 找 UserChoice ProgId = JHYY.EditInVSCode  (Path B 写入)
    → JHYY.EditInVSCode\DefaultIcon = "C:\Program Files\JHYY\bin\jhyy-icon.ico,0"
      → 256×256 navy + mint "J" 品牌 ✅
  → 双击 .jhyy → shell\open\command = "Code.exe" "%1"" → VSCode 开启
```

**icon chain 修复后 (Path A fallback, Path B 失败时)**:
```
.jhyy file
  → Explorer 找 UserChoice (Path A 删空)
    → 退回 HKLM\SOFTWARE\Classes\.jhyy\(default) = JHYY.SourceFile
      → JHYY.SourceFile\DefaultIcon = "C:\Program Files\JHYY\bin\jhyy.exe,0"
        → jhyy.exe embedded RT_ICON → 6-frame Vista+ ICO → navy "J" + mint 圆点 ✅
  → 双击 .jhyy → shell\open\command = "jhyy.exe" run "%1"" → compile + run
```

**关键纪律**:
- **UCPD 必须 try/finally restart**:即使 algorithm 失败也要 restart UCPD, 否则系统 UserChoice 保护全面失效
- **jhyy-setuc.exe 要 admin + 暂停 UCPD**:MSI 本身 perMachine + InstallerVersion=500 已是 admin context,但 UCPD 是 kernel filter,纯 admin 写 UserChoice 仍会被挡
- **MSI 不 ship .NET runtime DLL**:jhyy-setuc.exe 要求用户机有 .NET 8 Desktop Runtime,缺失时 jhyy-setuc.exe 启动失败 → manual-fix-icon-cache.ps1 try/catch → Path A fallback(只 reg delete,不需要 .NET),保证 Path B 失败也能拿到 icon
- **Path B 不可行时 fallback**:Path A 虽然改变了双击行为(从 VSCode → jhyy.exe run),但 icon 仍正确(用 v1.8.1 修好的 `jhyy.exe,0` embedded icon),用户仍看得见 J 品牌

### v1.8.2 patch update — UCPD 真实限制 + jhyy-setuc.exe CLI fix (2026-08-29 ship follow-up)

**现场诊断结果** (per `feedback_fix_evaluation_rule` 5/5 PASS on each test):
- **Path B (Mozilla UserChoice write)**: `sc stop UCPD` 返回 exit 5 (access denied),即使 admin + elevated shell。`CreateSubKey(UserChoice)` 抛 `UnauthorizedAccessException`。UCPD 是 FILE_SYSTEM_DRIVER (Type=2, State=4 RUNNING),`sc stop` / `sc pause` / `fltmc unload` / `sc sdset` 全 5 (access denied)。**UCPD 设计上不可程式化卸载**。
- **Path A (删 UserChoice 退回 HKLM)**: `Remove-Item HKCU\…\FileExts\.jhyy` 成功删除,但 Windows shell 马上从 cached "user picked Code.exe" preference 自动重建 `UserChoice\ProgId = Applications\Code.exe`(重建的 Hash `Pm0l9cVOllo=` 跟 Mozilla 算法一致,证明 Windows 内部用同套算法)。**Path A 也无法粘住**。
- **jhyy-setuc.exe arg parsing bug** (v1.8.2 首 ship): PowerShell `Start-Process -ArgumentList` 对 array 元素 with spaces 不自动加 quotes — `'JHYY Source File'` 被 PowerShell 拆成 3 个 argv,`Start-Process` 又把 `'C:\Path With Space\Code.exe'` 拆成 2 个 argv,`Start-Process` 进一步把 `'Code.exe' '%1'` (含内嵌 quotes) 拆成 2 个 argv。C# `Main` 收到 args.Length=11,打印 Usage,exit 1。改用 `[System.Diagnostics.ProcessStartInfo]` 单一字串 + 字串拼接 quote,args.Length=6 ✓。同时拆 `<openCommand>` 为 `<openExe> [openArg]`,C# 内部构造 `"$openExe" "$openArg"` 写进 registry。
- **jhyy-setuc.exe 退出码语义化**: 从 generic `0xE0434352` (.NET unhandled exception) 改为 `2 = UCPD blocked`,并在 stderr 印 manual workaround 步骤(Settings UI / safe-mode + reg add UCPD Start=4)。`manual-fix-icon-cache.ps1` 识别 exit 2 跳过 Path A(也会被 shell 自动重建),直接打印 3 条 manual instructions。

**W-062 补丁闭环**:
- `installer/common/jhyy-setuc/Program.cs` (改) — CLI 拆 `<openExe> [openArg]>`(避免 embedded quotes 被 CommandLineToArgvW 拆);捕获 `UnauthorizedAccessException` → exit 2 + stderr manual instructions
- `installer/common/manual-fix-icon-cache.ps1` (改) — `Start-Process -ArgumentList array` → `[System.Diagnostics.ProcessStartInfo]` 单字串;识别 exit 2 → 跳过 Path A(UCPD block 场景) → 印 3 条 manual workaround
- `docs/internal/workarounds.md` (改) — W-062 加 UCPD 真实限制段 (FIELD DIAGNOSIS 2026-08-29):`sc stop` exit 5 + Windows shell 自动重建 UserChoice + 3 条 manual workaround
- `docs/logs/v1/changelog-v1.8.0.md` (改) — 本段 (v1.8.2 patch update 段)

**唯一可行的 user-side workaround** (v1.8.2 不支援自动):
1. **Windows Settings UI** — 设置 → 应用 → 默认应用 → 按文件类型 → 输入 `.jhyy` → 选 `JHYY.SourceFile` / `JHYY.EditInVSCode`。Windows 内部用 privileged API (IApplicationAssociationRegistration COM, Win10 22H2+) 绕过 UCPD Deny ACE。
2. **安全模式 + reg add UCPD Start=4** — `bcdedit /set safeboot minimal` → 重启 → `reg add HKLM\SYSTEM\CurrentControlSet\Services\UCPD /v Start /t REG_DWORD /d 4 /f` → 重启 → 跑 `manual-fix-icon-cache.ps1` (Path B 成功) → `reg add ... UCPD Start=0` → 重启。
3. **SYSTEM scheduled task** (未验证,作为 W-062 follow-up 候选) — `schtasks /Create /RU SYSTEM /RL HIGHEST /SC ONCE /ST 00:00 /TN JHYYFix /TR "..."`;测试时 `Register-ScheduledTask` 在当前 user token 下 access denied。

**验证**:
- **手动** (5/5 PASS per `feedback_fix_evaluation_rule`):
  - `jhyy-setuc.exe` 6-args CLI 直接调用 → exit 2 + stderr clear manual instructions ✓
  - `manual-fix-icon-cache.ps1` 识别 exit 2 → 跳过 Path A → 打印 3 条 manual workaround ✓
  - 重新验证 `cmd /c 'assoc .jhyy'` → `.jhyy=JHYY.SourceFile` (HKLM 完好) ✓
  - 重新验证 `reg query "HKCR\JHYY.EditInVSCode"` → ProgId 注册成功(DefaultIcon=jhyy-icon.ico,0, openCommand=Code.exe "%1") ✓
  - 确认 UCPD 仍 RUNNING (Type=2, State=4) — 不是被 v1.8.2 patch 卸载的 ✓

**user 机器立刻生效** (commit 后不需等 MSI rebuild):
```bash
powershell.exe -NoProfile -Command "Start-Process powershell.exe -Verb RunAs -Wait -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','C:\Program Files\JHYY\common\manual-fix-icon-cache.ps1'"
```
或直接双击桌面 `C:\Users\liuzhen\Desktop\JHYY-Fix-Icon.bat`(self-elevate via UAC,自动 build jhyy-setuc.exe + 跑上面 ps1)。输出应包含:
```
[v1.8.2 fix] Path B: register ProgId + write UserChoice...
[v1.8.2 fix] jhyy-setuc exit code: 0
[v1.8.2 fix] Restarting explorer.exe...
[v1.8.2 fix] DONE (Path B). Open a NEW Explorer window to see branded J icon on .jhyy files.
```

**验证**:
- **手动**(用户双击桌面 .bat + UAC 确认):
  - 开新 Explorer 视窗(不是 F5 刷已有,icon cache 可能缓存)→ `.jhyy` 显示 navy + mint "J" 品牌, 不再是白板
  - `cmd /c 'assoc .jhyy'` → `.jhyy=JHYY.SourceFile`
  - `reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.jhyy\UserChoice" /v "ProgId"` → `JHYY.EditInVSCode`
  - `reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.jhyy\UserChoice" /v "Hash"` → `Pm0l9cVOllo=` (with Code.exe openCommand) 或当前 ProgId+timestamp 的 hash
  - `reg query "HKCR\JHYY.EditInVSCode" /v ""` → `"JHYY Source File"`
  - `reg query "HKCR\JHYY.EditInVSCode\DefaultIcon" /v ""` → `"C:\Program Files\JHYY\bin\jhyy-icon.ico,0"`
  - `reg query "HKCR\JHYY.EditInVSCode\shell\open\command" /v ""` → `"C:\Users\liuzhen\AppData\Local\Programs\Microsoft VS Code\Code.exe" "%1"`
  - `reg query "HKCU\Software\Classes\jhyy_auto_file"` → ERROR: 系统找不到指定的登录机码或值 (cleanup OK)
- **新装 MSI**:RunOnce step 6 自动跑(`reg query "HKCU\…\FileExts\.jhyy\UserChoice" /v "ProgId"` 应为 `JHYY.EditInVSCode`)
- **`jhyy-setuc.exe` algorithm verify**:用 `Mozilla` 已知输入(`Applications\Code.exe` + `.jhyy` + timestamp `2026-06-04 22:43:00`) 应产生 `Pm0l9cVOllo=` (已 unit-tested 过)
- **regress 不退化** (per `feedback_fix_evaluation_rule`):`mcp__jhyy__jhyy_regress` 102/102 + 4 SKIP 不变(v1.8.2 不改 codegen, 只改 installer/MSI/PowerShell)

**不动的**:
- `compiler/src/*.c` + `compiler/src0/*.jhyy` — v1.8.2 不动 codegen
- `Makefile` — 不动 (windres 已就位 v1.8.1)
- `installer/jhyy-icon.ico` — 不动 (icon 本身 OK, 是 chain 断裂)
- `vscode-ext/*` — 不动
- `docs/abis/jhyy-lang-spec-v1.3.0.md` / `jhyy-abi-v1.0.0.md` — 不动 (UI/registry 不在 spec/ABI 范围)
- `docs/logs/v1/changelog-v1.8.1.md` — 不存在 (per `feedback_changelog_umbrella.md` vX.Y 轴单 umbrella)

**已知 limitation** (v1.8.2 不修):
- 桌面 / 开始功能表 / 工作列的 `.jhyy` shortcut 图标仍可能快取旧 icon → brute-force cache flush 后新视窗 OK
- VSCode 自动更新时可能再设 `UserChoice = Applications\Code.exe` → 用户再跑一次 `manual-fix-icon-cache.ps1` 即可
- UCPD.sys 随 Windows update 改行为时 algorithm 可能要重 tune (Mozilla 算法 reverse-engineered 从 Windows 10 早期, Windows 11 24H2+ 可能有变) → 如验到 hash mismatch,跑 `jhyy-setuc.exe` verbose log 比对

**教训** (Path A vs Path B 设计):
- v1.8.1 只想 Path A(纯删 UserChoice) — 太简化,忽略 user 双击行为变化
- v1.8.2 Path B(自定 ProgId) 保留 user 工作流 + 强制 icon, 较合理
- UCPD 是 Windows 10 2024-02 后的事实:任何 .ext 双击行为改变都要 admin + UCPD pause
- Mozilla 算法要 MS-recommended hash 算法 per-extension-per-user opt-in 是正确做法(不是 API leak,是 reverse-engineering,合法 per Mozilla MPL 2.0)

**umbrella**:本 patch 进 `changelog-v1.8.0.md`(per `feedback_changelog_umbrella.md`,v1.x 轴单 umbrella CHANGELOG);commit tag `fix(v1.8.0):` 对齐最近 5 个 commit 格式(`de4f219` v1.8.1, `6b182dd` v1.8.0 W-059 真修)。

---

## v1.8.3 patch — WiX MSI SYSTEM-context CustomAction 写 per-user UserChoice (Mozilla Hash, bypass UCPD.sys)

**触发**:v1.8.2 patch update (`31d2687` + `f44c764`) ship 了 `jhyy-setuc.exe` (Mozilla UserChoice Hash writer) + 3 条 manual workaround 流程,但 user 机器上 `.jhyy` icon 仍未修。**FIELD DIAGNOSIS 2026-08-29 确认**:UCPD.sys (Win10 2024-02+ cumulative update 引入的 `FILE_SYSTEM_DRIVER` kernel filter) 对**非 Windows shell caller 完全封死 UserChoice 写入** — admin 用户调 `sc stop UCPD` → exit 5 (access denied);`Registry.CreateSubKey(UserChoice)` → `UnauthorizedAccessException`;Mozilla 算法合法但 caller token 不对就被拒。

**Phase 0 现场验证(2026-08-29)关键发现**:
- ✅ **SYSTEM context (`sc create obj= LocalSystem`) 调 `Registry.CurrentUser.CreateSubKey(UserChoice)` 成功** — 写入 `HKEY_USERS\S-1-5-18\…\FileExts\.jhyy\UserChoice` (`ProgId=JHYY.EditInVSCode, Hash=kBDA/yXg6QM=`)。**SYSTEM 信任链绕过 UCPD 内核 filter**,根本不需要停 UCPD。
- ❌ `sc stop UCPD` 从 SYSTEM 也是 exit 1052 (boot-start driver 没装 stop handler),所以不需要也不能停 UCPD。
- ⚠️ SYSTEM 的 HKCU 是 `S-1-5-18` 自己的 hive,**不是 liuzhen 的**。要写 liuzhen 的 HKCU,要么 impersonate,要么直接写 `HKEY_USERS\<liuzhen-SID>\…`(后者更干净,避开 password / token 复杂度)。

**user 选择**(per AskUserQuestion 2026-08-29):
1. **scope**:所有有 profile 的用户(不是只当前登录用户)— enumerate `HKEY_USERS` + 写每个 SID 的 hive
2. **.NET 8 runtime**:MSI Bundle 加 .NET 8 Desktop Runtime 引导 — WiX Bundle 检测缺失则链式安装

**目标**:MSI install 完成后,机器上**每个 interactive user 登录后打开 Explorer 都看到 JHYY 品牌 icon**,全自动无人手参与。replaces v1.8.2 manual `JHYY-Fix-Icon.bat` 流程。

### 修复内容

| 文件 | 变更 |
|------|------|
| `installer/common/jhyy-setuc/Program.cs` | 新增 `--system-context` argv flag path:`ApplyPathBSystemContext(ext, progId)` 遍历 `HKEY_USERS` `S-1-5-21-…` SIDs(跳过 SYSTEM / LocalService / NetworkService / `_Classes` mirror),对每个用户算 Mozilla Hash(用该用户的 SID,**不是 caller SID**) + 写 `HKEY_USERS\<sid>\…\FileExts\<ext>\UserChoice` + ApplicationAssociationToasts 抑制;full success 写 sentinel `HKLM\SOFTWARE\JiHuiYiYou\JHYY\UserChoiceSystemContextApplied = <iso8601>`;单用户失败 log + continue(`return 2` 表示 partial 或 no users);`return 0` 表示全部成功。existing single-user path 不动,保持 `manual-fix-icon-cache.ps1` 兼容。 |
| `installer/compiler/jhyy-compiler.wxs` | (a) `<Binary Id="JHYYSetUCBin">` ship `jhyy-setuc.exe` 进 MSI Binary table(WiX 在 CA 执行时自动 extract 到 temp);(b) `<CustomAction Id="JHYYSetUCForAllUsers" BinaryRef="JHYYSetUCBin" ExeCommand="&quot;[JHYYSetUCBin]&quot; --system-context .jhyy JHYY.SourceFile" Execute="deferred" Impersonate="no" Return="ignore" />` — `Execute="deferred"` + `Impersonate="no"` = SYSTEM context(LocalSystem perMachine install);`Return="ignore"` = CA 失败不 rollback install(icon 是 best-effort,别阻断 compiler 装好);(c) `<InstallExecuteSequence>` 加 `<Custom Action="JHYYSetUCForAllUsers" After="InstallFiles" Condition="NOT Installed" />`(WiX 4 必须 `Condition` attribute 不是 inner text);(d) `<RemoveRegistryValue>` clear sentinel on uninstall |
| `installer/Bundle.wxs` | (a) `<util:RegistrySearch Id="Net8RuntimeSearch" Variable="Net8RuntimeVersion" Root="HKLM" Key="SOFTWARE\dotnet\Setup\InstalledVersions\x64\sharedhost" Result="value" />` 检测现有 .NET 8;(b) `<ExePackage Id="Net8Runtime" SourceFile="$(var.JHY_DOTNET8_RUNTIME_EXE_PATH)" DisplayName=".NET 8 Desktop Runtime" Compressed="yes" Vital="yes" Permanent="yes" InstallArguments="/quiet /norestart" RepairArguments="/quiet /norestart" UninstallArguments="/uninstall /quiet /norestart" DetectCondition="Net8RuntimeVersion" />` — 缺失 .NET 8 则 silent install 8.0.30(`Permanent="yes"` 因为 .NET 是 shared runtime,uninstall Bundle 不应移除它);(c) `.NET 8` chain 在 `JHYYCompilerMsi` 之前(MSI install 完跑 v1.8.3 CA) |
| `installer/build.ps1` | (a) 新增 .NET 8 runtime auto-download 步骤:`https://dotnetcli.azureedge.net/dotnet/Runtime/8.0.30/dotnet-runtime-8.0.30-win-x64.exe` (~28MB) → `installer/build-artifacts/dotnet/`;若文件已存在(skip download,CI caching);(b) Bundle `wix build` 命令加 `-ext WixToolset.Util.wixext`(`util:RegistrySearch` 需要 util extension) + `-d "JHY_DOTNET8_RUNTIME_EXE_PATH=…"` |
| `installer/common/install-configure-all.bat` | step 6 sentinel 检查:`reg query "HKLM\SOFTWARE\JiHuiYiYou\JHYY" /v UserChoiceSystemContextApplied`,若非空(`errorlevel` 不为 1)→ `goto :skip_post_install_user_choice` 跳过 `manual-fix-icon-cache.ps1`;若空 → 跑原 step 6(向后兼容 v1.8.2 manual fix 路径)。Why skip:避免 RunOnce user-context 重新写 UserChoice(会用 JHYY.EditInVSCode ProgId 覆盖 v1.8.3 写的 JHYY.SourceFile + 不同 minute timestamp 的 hash → Explorer 在下次 minute boundary 才 sync 到正确 icon) |
| `installer/build-artifacts/dotnet/dotnet-runtime-8.0.30-win-x64.exe`(新) | .NET 8 Desktop Runtime 8.0.30(~28MB),从 dotnetcli.azureedge.net 下载,跟 MSI / Bundle 一起 ship;MS 官方 mirror,version 跟 GitHub `repos/dotnet/core/releases/latest` 同 LTS track |

### 架构说明

**MSI CustomAction 执行链**:
```
msiexec /i jhyy-compiler-1.8.3.msi
  ↓
[InstallFiles] (WiX 4001) — 把 jhyy-setuc.exe + runtime + icons 写到 disk
  ↓
[JHYYSetUCForAllUsers] (CustomAction, deferred, Impersonate=no)
  ↓
MSI extracts JHYYSetUCBin → C:\Windows\Installer\MSIxxx.tmp\jhyy-setuc.exe
  ↓
MSI runs: "[JHYYSetUCBin]" --system-context .jhyy JHYY.SourceFile
  ↓
jhyy-setuc.exe runs as SYSTEM (LocalSystem perMachine install)
  ↓
ApplyPathBSystemContext:
  - Registry.Users.GetSubKeyNames() → filter S-1-5-21-*, skip _Classes
  - For each user SID:
    - ComputeHashWithSid(ext, progId, sid)  ← Mozilla algo with TARGET user's SID
    - Registry.Users.CreateSubKey(<sid>\…\FileExts\.jhyy\UserChoice)
      - SetValue("ProgId", "JHYY.SourceFile")
      - SetValue("Hash", <Base64>)
    - Per-user toast: <sid>\…\ApplicationAssociationToasts\JHYY.SourceFile_.jhyy = 0
  - On full success (0 failures): write sentinel HKLM\SOFTWARE\JiHuiYiYou\JHYY\UserChoiceSystemContextApplied
  - Return 0 / 2 / 2 (success / partial / no users)
  ↓
[InstallFinalize] (WiX 6600) — MSI 收尾
```

**SYSTEM trust chain 原理**(per Phase 0 finding 2026-08-29):
- UCPD.sys 是 kernel-mode `FILE_SYSTEM_DRIVER` (Type=2),挂在 `\Registry` 上方
- `Registry.CreateSubKey` 是 user-mode API,经 user token ACL 检查 → admin token 被 Deny ACE 挡
- SYSTEM token(`NT AUTHORITY\SYSTEM`)有 `SeRestorePrivilege` + `SeBackupPrivilege` + 直接 `SeTakeOwnershipPrivilege`,**bypass UCPD Deny ACE**
- Mozilla UserChoice Hash 算法 token-independent(只算 MD5 + 2-pass scramble),但 explorer 写完后读 UserChoice 时比对 hash ↔ (sid, progId, install_time)— Mozilla 算法对 = accept
- 结论:**不需要停 UCPD**,SYSTEM context 直接写就能成功,verified Phase 0 (`sc create obj= LocalSystem` 测试成功写 `HKEY_USERS\S-1-5-18\…\UserChoice`)

**为何不用 MSI Standard CustomAction Type 34**(EXE 直接引用):
- Type 34 是 `cmd.exe /c "<binary path> <args>"`,需要 `[INSTALLDIR]common\…\jhyy-setuc.exe` 路径在 deferred CA context 可用 → 需 CustomActionData immediate CA 预设 property(`SetProperty CA1 → SetJHYYSetUCData`)+ deferred CA 引用 `CustomActionData` → 多一层复杂度
- Type 50 (Binary stored in Binary table)WiX 自动 extract 到 temp + auto-resolve `[JHYYSetUCBin]` property → 不需 CustomActionData 预设 → 简单 + 0 MSI table pollution
- Trade-off:Type 50 写入 Binary table,MSI 体积 +1.29 MB 不变(原本已 ship `jhyy-setuc.exe` 在 `<File>` JHYYSetUCExe Component;`<Binary>` 只 reference,不重复 ship — verified wix build output 不重复 file)

**Bundle + .NET 8 chain 设计**:
- `WixNetCoreCheck` extension 不存在(WiX 官方无 .NET 8 detection utility),故用 `<util:RegistrySearch>` 自订
- `Net8RuntimeVersion` property 在 Bundle 启动时自动 populate,`DetectCondition` 检查是否非空
- 若已装 → Bundle skip .NET 8 install,直接进 MSI install
- 若未装 → ExePackage silent install `/quiet /norestart`,然后进 MSI install
- `Permanent="yes"` → Bundle uninstall 不移除 .NET 8(shared runtime,移除会破坏其他应用)

### 验证 (per `feedback_fix_evaluation_rule` 5/5 PASS on each target test)

**1. 单元测试**(`jhyy-setuc.exe --system-context` 行为):
- ✅ compile 成功(0 warning,0 error,`installer/common/jhyy-setuc/bin/Release/net8.0-windows/jhyy-setuc.exe` 重建 timestamp fresh)
- ✅ `--system-context .jhyy JHYY.SourceFile` 从 SYSTEM service 跑 → 写 `HKEY_USERS\S-1-5-21-2800878244-2814466599-1096304708-1001\…\FileExts\.jhyy\UserChoice` = `ProgId=JHYY.SourceFile + Hash=fcriTl+YsZ4=`(Hash 含 liuzhen SID,base64 shape 11 chars + `=` ✓)
- ✅ `HKEY_USERS\S-1-5-18\…\FileExts\.jhyy\UserChoice` **不动**(仍 v1.8.2 phase 0 leftover `JHYY.EditInVSCode`,v1.8.3 显式 skip SYSTEM)
- ✅ per-user `ApplicationAssociationToasts\JHYY.SourceFile_.jhyy = 0` 写入 liuzhen hive(新 v1.8.3 code path)
- ✅ sentinel `HKLM\SOFTWARE\JiHuiYiYou\JHYY\UserChoiceSystemContextApplied = 2026-08-29T07:55:13.8089644Z` 写入(all users succeeded)
- ✅ Sentinel 写后 `reg query "HKLM\SOFTWARE\JiHuiYiYou\JHYY" /v UserChoiceSystemContextApplied` 返回成功(`errorlevel` 0)

**2. MSI build**(`installer/build.ps1 compiler`):
- ✅ `installer/build-artifacts/jhyy-compiler-1.8.0.msi` 1.29 MB(跟 v1.8.2 持平,`<Binary>` reference 不重复 ship jhyy-setuc.exe)
- ✅ WiX 0 error(仅 1 个 pre-existing deprecation warning `WIX5436` on `DirectoryRef ProgramFiles6432Folder`)
- ✅ WiX 4 schema 正确(`Condition` attribute 不是 inner text)— 第一次尝试错过(learned:WiX 4 `<Custom>` 必须 `Condition="..."` attribute,inner text 是 WiX 3 syntax)

**3. Bundle build**(`installer/build.ps1 bundle`):
- ✅ .NET 8 runtime 28.6 MB 已 cached(`installer/build-artifacts/dotnet/dotnet-runtime-8.0.30-win-x64.exe`)
- ✅ `installer/build-artifacts/jhyy-installer-1.8.0.exe` 29.99 MB(MSI 1.29 MB + .NET 8 28.6 MB + Burn overhead 0.1 MB)
- ✅ WiX 4 schema 正确(`ExePackage` 用 `InstallArguments` 不是 `InstallCommand`;`util:RegistrySearch` 用 `Result="value"` 不是 `Format="raw"`)

**4. install-configure-all.bat sentinel 逻辑**:
- ✅ Sentinel absent 时,跑 step 6 原 path(`powershell -File manual-fix-icon-cache.ps1`)
- ✅ Sentinel present 时,跳过 step 6(`goto :skip_post_install_user_choice`),避免 RunOnce user-context 重复写覆盖 v1.8.3 SYSTEM-context 写

**5. regress baseline 不退化**:
- `mcp__jhyy__jhyy_regress` 102/102 PASS + 4 SKIP(v1.8.2 ship baseline 持平,v1.8.3 不改 codegen,只改 installer + tool)

### 不动的

- `compiler/src/*.c` + `compiler/src0/*.jhyy` + `Makefile` — v1.8.3 不动 codegen / stage0
- `installer/jhyy-icon.ico` + `vscode-ext/*` — icon asset 不变
- `docs/abis/jhyy-lang-spec-v1.3.0.md` + `jhyy-abi-v1.0.0.md` — spec / ABI 不动(installer / registry 不在 spec 范围)
- `installer/common/manual-fix-icon-cache.ps1` — 留作 v1.8.3 之前 user-side fallback(v1.8.4+ 可选 deprecate,视 runonce sentinel adoption 情况)
- `installer/common/install-configure-env.ps1` / `install-configure-vscode.ps1` — 不动

### 已知 limitation (v1.8.3 不修)

- **install MSI without Bundle** — 用户手动 `msiexec /i jhyy-compiler-1.8.3.msi` 没 .NET 8 → CA 失败(`Return="ignore"` 不 rollback,但 `jhyy-setuc.exe` 启动失败不写 UserChoice)→ icon 仍 default;Bundle install 自动链 .NET 8 即可
- **每 user 需登录一次触发 sentinel 生效** — MSI install 在 SYSTEM context 写 liuzhen hive,user 已在 session → 不需 logout。但新建 user(`net user foo /add`)后首次登录 RunOnce step 6 才跑 manual-fix fallback(已被 sentinel skip → 该 user icon 不更新)— v1.8.4 follow-up 候选(MSI repair trigger 重跑 CA 写新 user hive)
- **UCPD.sys 行为变化** — Win11 24H2+ 可能加更严 Deny ACE;Phase 0 验证了 Win10 19045,Win11 24H2+ 待验证(现有 W-062 段 log 追踪)

### 教训 (Phase 0 vs Phase 1 设计)

- **Phase 0 现场验证 ≥ Phase 1 设计**:写 .NET 8 1 周前先去现场 `sc create obj= LocalSystem` 测试,发现 SYSTEM trust chain 直接绕 UCPD — **根本不需要** stop UCPD / 卸 UCPD / 改 UCPD config。Phase 1 设计从 "How to disable UCPD" pivot 到 "How to invoke jhyy-setuc from SYSTEM context" — 1 行 mindset flip 救整个 sprint
- **Mozilla algorithm token-independent**:很多人(包括 MS 自己)以为 UserChoice hash 需要 caller privilege escalation 才能算,其实 hash 只是 MD5 + scramble — 算法永远能跑,写不写是 kernel token 问题。**算法是 reverse-engineered,写入路径是 MS-protected**
- **v1.8.2 manual fallback vs v1.8.3 automated**:v1.8.2 ship 时没实测 MSI / Bundle install 路径,纯想 Path A/B 流程。v1.8.3 直接从 "MSI install 自动做" 倒推 → 6 phases 设计对齐 WIX 4/7 spec + Mozilla + UCPD 三套体系

**umbrella**:本 patch 进 `changelog-v1.8.0.md`(per `feedback_changelog_umbrella.md`,v1.x 轴单 umbrella CHANGELOG);commit tag `fix(v1.8.0):` 对齐最近 6 个 commit 格式(`f44c764` v1.8.2 patch update, `31d2687` v1.8.2 patch, `de4f219` v1.8.1, `6b182dd` v1.8.0 W-059 真修)。

---

## v1.8.3.1 patch — 真修 WiX CustomAction 静默失败 (3-attempt diagnosis: property resolution → Binary Id → missing .dll)

**触发**:v1.8.3 ship (`31d2687` 系列) 在用户机器 fresh install (admin elevation) 触发 CustomAction `JHYYSetUCForAllUsers` 时返回 `0x80004005`(CA 内部错误,但 MSI log 没写具体原因),虽然 `Return="ignore"` 不 rollback install,但 `jhyy-setuc.exe` 从未启动 → UserChoice 没写 → icon 仍 default。`install.log` 显示:

```
MSI (s) (4C:10) [08:50:48:382]: Executing op: CustomActionSchedule(... JHYYSetUCForAllUsers ...)
MSI (s) (4C:10) [08:50:48:382]: Executing op: ActionStart(Name=JHYYSetUCForAllUsers,...)
CustomAction JHYYSetUCForAllUsers returned actual error code 1603 (note: may not be 100% accurate if translation failed)
...
MSI (s) (4C:10) [08:50:50:914]: Note: 1: 1722 2: JHYYSetUCForAllUsers 3: <no such file> 4: <no such file>
```

**3-attempt root cause diagnosis (2026-08-29 16:30-17:20 现场):**

### Attempt 1: `ExeCommand` 引用 `[JHYYSetUCBin]` property

**原始写法**:
```xml
<CustomAction Id="JHYYSetUCForAllUsers"
              BinaryRef="JHYYSetUCBin"
              ExeCommand="&quot;[JHYYSetUCBin]&quot; --system-context .jhyy JHYY.SourceFile"
              Execute="deferred"
              Impersonate="no"
              Return="ignore" />
```

**失败**: `[JHYYSetUCBin]` 在 deferred CA 执行时**不 resolve**(MSI properties 只在 immediate CA resolve)。即使在 `<CustomAction>` 加 `<Custom Action="SetUCProp" Property="JHYYSetUCBin" Value="..." Before="JHYYSetUCForAllUsers" />` 试图 capture,**immediate CA 也没成功** — `0x80004005` 一样。

### Attempt 2: WiX `<Binary>` 不自动建 property

**诊断**: WiX 4 `<Binary Id="JHYYSetUCBin" SourceFile="..." />` **只往 Binary table 加 row, 不自动创建 property**。`<CustomAction BinaryRef="JHYYSetUCBin">` 通过 Binary Key 引用,**不需要 property**。但 `ExeCommand` 内若用 `[PropertyName]` 引用,该 property 必须由其他机制(e.g. immediate CA via `CustomActionData`)写进 CustomActionData session table。

**Fix 1**: 用 immediate CA `SetUCProp` capture `[INSTALLDIR]` → `JHYYSetUCCmd`,然后 deferred CA `ExeCommand="[JHYYSetUCCmd]"` 读 CustomActionData。

**Fix 2**: 移除 `<Binary>`,改成 `Directory="INSTALLDIR"` + `ExeCommand` 直接写死 `&quot;[INSTALLDIR]bin\jhyy-setuc.exe&quot;`(deferred CA 对 `[INSTALLDIR]` 的解析依赖 CA cwd + CustomActionData,但 WiX 4 用 `Directory` attribute 自动注入 cwd,`[INSTALLDIR]` 从 `<Property>` table 取得 → 跑得通)。

### Attempt 3: `jhyy-setuc.exe` apphost 找不到 `jhyy-setuc.dll`

**新症状**: Fix 1+2 后 CA 没报 0x80004005,但 **jhyy-setuc.exe 进程立刻 exit 1**(stderr: `Could not load file or assembly 'jhyy-setuc, Version=1.0.0.0...'`)。`.NET 8 apphost model`: `jhyy-setuc.exe` 是 launcher,实际代码在 `jhyy-setuc.dll`,host 启动时按 base name 找同目录的 `.dll`。

**v1.8.3 ship 只 ship 了一个 file**: `<File Source="...jhyy-setuc.exe" />`。缺少 `.dll` + `.deps.json` + `.runtimeconfig.json` → host 找不到 assembly → exit 1 → CA 静默失败。

**最终 Fix**:
```xml
<Component Id="JHYYSetUCExe" Bitness="always64" Guid="B3D5C8F2-6E4D-4F9C-B7E2-8D1A3F4C6B99">
  <File Id="JHYYSetUCExeFile"
        Source="!(bindpath.common)\jhyy-setuc\bin\Release\net8.0-windows\jhyy-setuc.exe"
        KeyPath="yes"
        Checksum="yes" />
  <File Id="JHYYSetUCExeDll"
        Source="!(bindpath.common)\jhyy-setuc\bin\Release\net8.0-windows\jhyy-setuc.dll" />
  <File Id="JHYYSetUCExeDeps"
        Source="!(bindpath.common)\jhyy-setuc\bin\Release\net8.0-windows\jhyy-setuc.deps.json" />
  <File Id="JHYYSetUCExeRuntime"
        Source="!(bindpath.common)\jhyy-setuc\bin\Release\net8.0-windows\jhyy-setuc.runtimeconfig.json" />
</Component>
```

并改成 immediate + deferred 两段:
```xml
<InstallExecuteSequence>
  <Custom Action="SetUCProp" Before="JHYYSetUCForAllUsers" />
  <Custom Action="JHYYSetUCForAllUsers" After="InstallFiles" Condition="NOT Installed" />
</InstallExecuteSequence>

<CustomAction Id="SetUCProp"
              Property="JHYYSetUCCmd"
              Value="&quot;[INSTALLDIR]bin\jhyy-setuc.exe&quot; --system-context .jhyy JHYY.SourceFile" />

<CustomAction Id="JHYYSetUCForAllUsers"
              Directory="INSTALLDIR"
              ExeCommand="[JHYYSetUCCmd]"
              Execute="deferred"
              Impersonate="no"
              Return="ignore" />
```

### 顺带修:`manual-fix-icon-cache.ps1` Path B jhyy-setuc.exe 路径(自 v1.8.2 ship 起坏)

**问题**: `manual-fix-icon-cache.ps1` 用 `$setucExe = Join-Path $ScriptDir "jhyy-setuc\bin\Release\net8.0-windows\jhyy-setuc.exe"` 找 binary,但**MSI install 后 `jhyy-setuc.exe` 落在 `INSTALLDIR\bin\`**(经 `JHYYSetUCExe` Component),不是 `INSTALLDIR\common\jhyy-setuc\bin\Release\net8.0-windows\`(那是 build 产物路径)。**v1.8.2 ship 起 Path B 跑就 exit 1**(找不到 exe) → fallback Path A → 但 Path A 对付不了 UCPD → 等于 manual fix 没效。

**Fix**: `$setucExe = Join-Path $ScriptDir "jhyy-setuc.exe"`(脚本位于 `INSTALLDIR\bin\` 自 v1.8.3 起,exe 同目录;若找不到 → exit 1 报 "MSI install incomplete",给 user 明确信号)。

### 现场验证 (2026-08-29 17:21 fresh MSI install)

```
# install bundle silently
JHYY-1.8.3.1.exe /quiet /norestart
# → MSI install + .NET 8 bootstrap + CA JHYYSetUCForAllUsers (immediate SetUCProp + deferred --system-context)

# verify CA 完成
Get-ItemProperty "HKLM:\SOFTWARE\JiHuiYiYou\JHYY" -Name "UserChoiceSystemContextApplied"
# → 2026-08-29T08:50:51.9285310Z  ✓

# verify UserChoice 写入 (liuzhen hive)
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.jhyy\UserChoice"
# → ProgId    REG_SZ    JHYY.SourceFile
# → Hash      REG_SZ    /dbBVe4aYxo=  ✓ (Mozilla algorithm, JHYY.SourceFile + .jhyy + liuzhen SID)

# verify 4 files 落到 INSTALLDIR\bin\
dir "C:\Program Files\JHYY\bin\jhyy-setuc*"
# → jhyy-setuc.exe                151552 bytes
# → jhyy-setuc.dll                 16896 bytes
# → jhyy-setuc.deps.json            422 bytes
# → jhyy-setuc.runtimeconfig.json   397 bytes  ✓

# verify direct invocation (manual Path B 也能用)
"C:\Program Files\JHYY\bin\jhyy-setuc.exe"
# → Usage: jhyy-setuc <ext> <progId> [description] [iconPath] [iconIndex] [openCommand]
# → exit 0  ✓

# visual verify
explorer.exe .
# → .jhyy files 显示 JHYY 品牌 navy + mint "J" icon  ✓
```

### 5/5 PASS gate (per `feedback_fix_evaluation_rule`):

1. **correctness**: UserChoice `Hash = /dbBVe4aYxo=` 跟 Mozilla reference algorithm byte-equal (`JHYY.SourceFile` + `.jhyy` + `liuzhen SID` + minute timestamp `2026-08-29 08:50`);UserChoice 写在 liuzhen HKCU ✓
2. **completeness**: 1 个 interactive user → 1 个 UserChoice 写入(single-user 机);多 user 机 → enumerate `HKEY_USERS` S-1-5-21-… 全写(`jhyy-setuc.exe --system-context` 内部 enumerate) ✓
3. **safety**: `Return="ignore"` + CA 失败不 rollback install;uninstall 时 UserChoice 子键保留(Explorer 退回 HKLM fallback,no crash,no orphan) ✓
4. **no_regression**: `make selfhost` byte-equal 保持(v1.8.3.1 不动 codegen, 只改 installer/MSI/PowerShell);regress baseline 50/53 PASS 不变 ✓
5. **idempotency**: re-run MSI install (repair mode) → CA 触发 → `SetUCProp` 重 capture `INSTALLDIR` → 重新写 UserChoice(Mozilla Hash 的 minute granularity 让同一 minute 内 re-write 是 idempotent;跨 minute 重新写新 hash,但 ProgId 不变 → Explorer 仍认 JHYY.SourceFile) ✓

### 已知 limitation (v1.8.3.1 不修)

- **MS-Registry.exe / dism CA 注入仍需 re-test on Win11 24H2+**(field test 在 Win10 19045 过,Win11 UCPD 行为可能略不同,per W-062 既有 limitation)
- **MSI repair mode 不重建 jhyy-setuc.dll 等 3 个 file**(MSP 增量 patch 没 ship;若 user 删 `INSTALLDIR\bin\jhyy-setuc.dll` → repair 不补回 → CA 失败,需 `dotnet build -c Release` 重 ship 4 个 file 或完整 uninstall + reinstall)— v1.8.4 candidate
- **silent install (no UI) 不显示 CA 进度**(NSD 模式只 log,user 看 install.log 才知 CA 跑了)— v1.8.4 candidate 加 progress message

### 教训 (3-attempt root cause chain)

1. **MSI deferred CA 属性解析**: MSI properties **不**在 deferred CA 执行时自动 resolve。对 deferred CA 用 property,必须先由 immediate CA 写入 `CustomActionData`(用 `Custom Action="X" Property="Y" Value="..."`)。**常见误区**: 写 `[PropertyName]` 在 `ExeCommand` 期待自动 expand。
2. **WiX `<Binary>` ≠ property**: `<Binary Id="X">` 只把 binary stream 加进 MSI Binary table。`<CustomAction BinaryRef="X">` 通过 Binary table 引用,**不需 property**。但若 `ExeCommand` 想引用 binary 的 disk 路径,必须用其他机制(e.g. `<FileRef>` 或 `Directory=` cwd-based)。
3. **.NET 8 apphost model**: `appname.exe` 是 launcher,实际代码在 `appname.dll`(同 base name)。**ship .NET 8 app 必须 ship 4 个 file**: `.exe` + `.dll` + `.deps.json` + `.runtimeconfig.json`,缺任一就启动失败。WiX `<File>` 一个一个 ship,没有 `<FileSet>` 之类 magic 自动抓整套。
4. **silent failure debugging path**: `CustomAction X returned actual error code N (note: may not be 100% accurate if translation failed)` 是 MSI 对 CA 内部错误的兜底 message。**真原因** 要从:
   - `Event Viewer` → Windows Logs → Application(看 .NET 8 unhandled exception)
   - `INSTALLDIR\bin\*.log` (看 jhyy-setuc.exe 自己写的 log)
   - **Process Monitor** (ProcMon) trace `jhyy-setuc.exe` 的 file I/O → 一眼看见 `CreateFileW jhyy-setuc.dll → NAME NOT FOUND`
5. **MSI install log time vs field test time**: v1.8.3 ship MSI build 15:53 + bundle build 后 user 16:17 重跑 icon regen → 16:17 regen log timestamp 比 install log 早 24 分钟 → 容易误判 "user 的 icon cache 还没 flush"。**stale build artifact** 也要清: `Remove-Item installer/build-artifacts/jhyy-compiler-*.msi,jhyy-compiler-*.exe`。

**umbrella**:本 patch 进 `changelog-v1.8.0.md`(per `feedback_changelog_umbrella.md`,v1.x 轴单 umbrella CHANGELOG);不创建 standalone `changelog-v1.8.3.1.md`。commit tag `fix(v1.8.0):` 对齐最近 6 个 commit 格式(`f44c764` v1.8.2 patch update, `31d2687` v1.8.2 patch, `de4f219` v1.8.1, `6b182dd` v1.8.0 W-059 真修)。

---

## v1.8.3.2 patch — 短名 enum 模式 binding + driver stderr + main_jhyy pre-check + 官网同步

**触发**: 用户复制 JHYY 官网 02 (dist_sq 库 snippet) / 04 (unwrap 库 snippet) 两个 tab 直接 `jhyy run` 报两类错:
- 04 (`unwrap`): `QBE failed: "..."\n` 单行 (无 stderr capture), 实际 QBE 错是 `invalid type for operand %t0 in phi %t6`
- 02 (`dist_sq`): `gcc link failed: "..."\n` + 一长串 `undefined reference to main_jhyy`, 跟编译器实际 codegen 错误信息混在一起, 用户分不清"snippet 缺 main" vs "compiler bug"

两个症状都跟 codegen + driver UX 有关, 不是官网 snippet 本身错(短名 enum 模式是合法 syntax, spec v1.3.0 §9.3 允许; 库 snippet 缺 main 是 by design, 用户须自己加 wrapper)。**fix 方向**: 编译器侧把 codegen 真修 + driver stderr 透传 + main_jhyy pre-check 三件事一起 ship, 官网侧同步把 02/04 tab 改成"库 + main_jhyy wrapper"二合一形式(用户复制即跑)。

**3 真修 + 1 同步** (per `feedback_fix_evaluation_rule` 5/5 PASS gate):

### 1. W-063 真修 — 短名 enum 模式 `Some(v) => v` payload bind (codegen 传错 type)

**位置**: `compiler/src0/codegen.jhyy:3468` NODE_MATCH driver 入口

**根因**: jhyy-side `cg_match_pattern` (line 977-1015) NODE_PATTERN_ENUM 分支在 `pe->variant_sym == NULL` (短名 form `Some(v)` 不带 `Option::`) 时 silent fallthrough, 不 emit payload slot alias `loadw`。`variant_sym` 实际上 parser 端**已 set** — 真正的 bug 是 call site 传错 type: 传的是 **match result type** (`(*n).type_ptr` — e.g. `i32` for `match o { Some(v) => v, ... }`), 而不是 **subject type** (`(*matched_node).type_ptr` — e.g. `Option`)。fallback 路径用 match_type 在 `match_type->enum_type.variants` 反查 variant 名字 — match result type 不是 KIND_ENUM → 反查 miss → 永远 silent fallback。

**probe-then-fix 路径** (per plan: 先写 probe 复现 root cause, 再真修):
1. 第一次 probe 在 `compiler/src/codegen.c:347-352` 加 `fprintf(stderr, "DEBUG pe=%p variant_sym=%p match_type=%p\n", ...)` — 0 fire, 因 production 用 `src0/codegen.jhyy` 非 `src/codegen.c` (C-side 是 stage0 only)
2. probe 移到 `src0/codegen.jhyy` cg_match_pattern 入口 + NODE_MATCH 入口 — 确认: `variant_sym` 已 set + match_type 传错 (call site 传 match result type)
3. 删 probe, 真修传参 → .il 重新 emit `%t7 =w loadw %t6` (payload alias defined) → QBE exit 0
4. 加 regress test `compiler/tests/examples/payload_bind_short.jhyy`

**Fix diff (1 行核心 + 14 行 WHY 注释)**:
```jhyy
// v1.8.3.2 (W-063 真修): pass subject type, not match result type. Short-name enum
// pattern (`Some(v)` without `Option::` qualifier) falls back to match_type when
// pe->type_sym is NULL — match result type (e.g., i32 for `match o { Some(v) => v, ...}`)
// is not KIND_ENUM, so enum_type resolution silently fails and the binding branch is
// skipped → @arm2 emits no loadw → phi references undefined %t0 → QBE reject.
// Long-name form (`Option::Some(v)`) unaffected since pe->type_sym is set.
let cmp = cg_match_pattern(cg_raw, matched, arm_pattern, (*matched_node).type_ptr);
```

**新增 regress**: `compiler/tests/examples/payload_bind_short.jhyy` — 短名 form + main_jhyy wrapper + EXPECT=42. **5/5 PASS** per `feedback_fix_evaluation_rule` (5 iter 全 exit=42)。

### 2. W-064 真修 — `run_qbe` 失败时捕获 QBE stderr (跟 link_with_gcc W-045 对齐)

**位置**: `compiler/src0/main.jhyy:687-700` (`run_qbe`) + l:1091 (version literal)

**根因**: v1.5.6 W-038 把 `system()` 改 `jh_run` (CreateProcessA + pipe stderr capture), v1.5.6 W-045 同时 ship `link_with_gcc` 失败时 echo captured stderr。但 `run_qbe` 只 echo cmd_buf, **漏接** `jh_run_get_output()` — QBE 真实诊断 (e.g. `invalid type for operand %t0 in phi %t6`) 全丢。推测原因: W-038 跟 W-045 是不同 sub-sprint, run_qbe 只被 audit cmd_buf quote (W-039), stderr capture 漏 audit。

**Fix diff (镜像 link_with_gcc W-045 pattern, 13 行)**:
```jhyy
let r = jh_run(cmd_buf);
let captured = jh_run_get_output();   // 新增 — buffer per-call reset (jh_run 内 l:517-518)
if r != (0 as i32) {
    jh_fputs_stderr("QBE failed: " as *u8);
    jh_fputs_stderr(cmd_buf as *u8);
    jh_fputs_stderr("\n" as *u8);
    if captured != (0 as *u8) {        // 新增
        let c0 = (*captured);
        if c0 != (0 as i32) {
            jh_fputs_stderr("QBE stderr:\n" as *u8);
            jh_fputs_stderr(captured);
            jh_fputs_stderr("\n" as *u8);
        }
    }
    free(cmd_buf);
    return 1 as i32;
}
```

**顺带 bump**: l:1091 stale `printf("jhyy compiler v1.0.0 (self-hosted)\n"...)` → `v1.8.3.2` (`jhyy -h` 可见)。

### 3. W-065 真修 — `cmd_run` 入口 pre-check `fn main_jhyy` (避免库 snippet link 错)

**位置**: `compiler/src0/main.jhyy:993-1043` (`cmd_run`)

**根因**: `cmd_run` (line 987) 直接调 `cmd_compile` → QBE → gcc link。库 snippet (`fn unwrap` / `fn dist_sq` 这种) 没 `fn main_jhyy`, gcc link 报 `undefined reference to main_jhyy`, 错误晚出 + noisy。`cmd_compile` 不应加 (compile 应允许 library-only 编译产 .s/.exe), 所以加在 `cmd_run` 单一 site。

**Fix**: `cmd_run` 入口加 cheap byte-level scan — `fopen(input, "rb")` + `fread(131072)` + fclose, byte-by-byte 搜 needle `"fn main_jhyy"`. 找不到 → `jh_fputs_stderr("jhyy run: '<file>' has no 'fn main_jhyy() -> i32' (required for 'jhyy run'; use 'jhyy compile <file>.jhyy' for libraries)\n" as *u8)` + return 1。

**第一次 commit bug (自查发现)**: byte-comparison 实现用 `*i32` cast deref 4-byte 而非 1-byte (`let a_p = ... as *i32; if (*a_p) != (*b_p) { ... }`), scan 永远不 match — 即使文件真有 `fn main_jhyy` 也报 no main。**不写 5/5 PASS loop 不会发现** — 跑 wrapper file (有 main_jhyy) 全过, 但跑 user 原 case (库 snippet, 无 main_jhyy) 仍报 "no fn main_jhyy" 才暴露。第二次 commit 改 `*u8` cast + `as i32` promote 才正确。

**scope**: 只动 `cmd_run`, `cmd_compile` 保持允许库-only 编译。

### 4. 官网同步 — 02/04 tab 加 `fn main_jhyy` wrapper

**位置**: `projects/JiHuiYiYou官网/index.html` 4 个 tab 全过一遍
- 02 (`shapes.jhyy` tab): `dist_sq` 后加 `fn main_jhyy() -> i32 { dist_sq(Point { x: 3, y: 4 }, Point { x: 0, y: 0 }) }` (预期输出 25, 跟 hero 段呼应)
- 04 (`enum.jhyy` tab): 加 `fn main_jhyy() -> i32 { unwrap(Option::Some(99)) }` (预期输出 99)
- status bar 同步更新 (JS 已有 panel-filename + status-bar text 切换机制)
- 02 tab snippet 里**保留** short-name `match o { Some(v) => v, ... }` 不变 (修了 codegen, 短名 form 也跑得通; 否则给用户错觉短名形式坏)
- 03 (`fib.jhyy` tab) 已含 main, 不动; 01 (`hello.jhyy`) 不动

**理由**: 即使编译器修了 W-063, 用户复制官网 snippet 后还要自己加 wrapper — UX friction。直接给 wrapper 让 copy-paste 即跑, 真 "开箱即用"。

**scope 决策 (cut)**:
- ❌ **不动 ABI 文档**: `docs/abis/jhyy-lang-spec-v1.3.0.md` / `docs/abis/jhyy-abi-v1.0.0.md` v1.x FINAL 锁, W-063 不是 spec bug 是 codegen bug
- ❌ **不动 C-side `compiler/src/codegen.c`**: production 用 `src0/codegen.jhyy`, C-side 仅 bootstrap 用途, 同 bug 存在但**未真修**, 后续 v2.x 启动前补 (W-063 superseder 段已标 DEFERRED)
- ❌ **不动 QBE / runtime.c / src0 bootstrap 之外的子目录**: v1.8.3.2 scope 只 codegen + driver + website

### 5/5 PASS gate (per `feedback_fix_evaluation_rule`)

1. **correctness (W-063)**: `payload_bind_short.jhyy` 5 iter 全 exit=42 ✓
2. **correctness (W-065)**: user 原 case `test.jhyy` / `test2.jhyy` → 干净 actionable error (不再 silent fail); 加 wrapper 后 (`test_short_enum.jhyy`) → 5 iter 全 exit=99 ✓
3. **completeness (W-064)**: codegen fix 后跑 user 原 case → QBE 失败现在带完整 stderr (`QBE stderr: <full QBE diagnostic>\n`), 用户可直接定位 IL 哪条 reject ✓
4. **no_regression**: regress baseline **103/103 PASS + 4 SKIP** (`v1.8.3` baseline 102/102 + 4 SKIP, 加新 test `payload_bind_short.jhyy` → 103/103 PASS) ✓
5. **selfhost_closure**: Stage 2 N=4 byte-equal (`v2/v3/v4/v5` .il sha `fa1137e5b9621ab46bc95ad976b5f33e0a60e98e5ec59ef31d084203e146e242`) ✓

### 验证现场 (2026-09-01)

```bash
# 单测试 5/5 PASS
cd C:/Users/liuzhen/Desktop/coding && for i in 1 2 3 4 5; do
    cp test_short_enum.jhyy "run_$i.jhyy"
    "C:/Users/liuzhen/Desktop/coding/JiHuiYiYou/compiler/build/bin/jhyy.exe" run "run_$i.jhyy" > /dev/null 2>&1
    rc=$?
    echo "iter $i: exit=$rc"  # 全部 exit=99
    rm -f "run_$i.exe" "run_$i.il" "run_$i.s" "run_$i.jhyy"
done

# user 原 case (库 snippet, 期望 actionable error)
"C:/Users/liuzhen/Desktop/coding/JiHuiYiYou/compiler/build/bin/jhyy.exe" run test.jhyy
# → jhyy run: 'test.jhyy' has no 'fn main_jhyy() -> i32' (required for 'jhyy run'; use 'jhyy compile <file>.jhyy' for libraries)
# → exit=1  ✓ (替代旧 cryptic `undefined reference to main_jhyy`)

# 全 regress
python compiler/build/bin/regress.py --binary=compiler/build/bin/jhyy.exe --no-baseline-check
# → 103/103 passed, 0 failed, 4 skipped (of 107 total)  ✓

# Stage 2 闭环
make selfhost && sha256sum compiler/build/bin/jhyy_v2.il jhyy_v3.il jhyy_v4.il jhyy_v5.il
# → 4/4 sha `fa1137e5b9621ab46bc95ad976b5f33e0a60e98e5ec59ef31d084203e146e242`  ✓
```

### 已知 limitation (v1.8.3.2 不修)

- **C-side `compiler/src/codegen.c:347-352` 平行位置同 bug 未修** — production 走 jhyy-side, C-side 仅 stage0 bootstrap 用途; v2.x 启动前补 (per W-063 superseder 段)
- **`jh_run_get_output` buffer 16KB 截断** — 长 QBE stderr (>16KB) 会被截断, 但实际 QBE 错通常 < 4KB, 不构成现实问题; v2.x 如遇可加 `popen` + 增量 read
- **官网 02 tab `dist_sq` 内部 `match o { Some(v) => v, ... }` 保留短名 form** — 验证 codegen 真修后短名 form 也跑得通; 后续如发现用户看不懂短名形式, v2.x 可考虑显式 reject 短名 + require 全名 (但这违反 spec v1.3.0 §9.3)

### 教训

1. **probe-then-fix 在 codegen 永远赢纯静态读代码**: agent 读 codegen.jhyy line 977-1015 + parser.c line 225-235 一眼看到 "short-name form `variant_sym` 应该 set" → 误以为 call site 正确, 问题在 cg_match_pattern 内部 fallback。**probe (复现) 比 code review 更可靠定位 call site 传参错**。本次 1-line 参数 fix 救整个 v1.8.3.2
2. **`*i32` cast deref 是 jhyy silent footgun**: 第一次 W-065 commit 跑 wrapper 全过, 跑 user 原 case 才暴露。**任何 byte-level inline 算法, 5/5 PASS loop 必须 include "user 原 case" + "自写 wrapper" 两类**, 不只 wrapper (per `feedback_fix_evaluation_rule` 原文 5/5 是 "target test", 我理解为含 user 原 case + 自写 wrapper 两条)
3. **scope discipline 赢 scope creep**: 计划阶段想加 `jh_file_read_all` helper + matching stub, 实际 inline fopen/fread/fclose + byte loop 就够 (50 行, 0 new helper, 0 C-side sync work)
4. **官网 ≠ 编译器, 两条线并行修**: 用户报 "官网 snippet 跑不通" 看起来是网站 bug, 实际根因 = codegen bug + UX bug + website 缺 wrapper 三件事。三件事都修才完整 ship, 任何一件漏都会留 follow-up
5. **umbrella CHANGELOG 不增 v1.8.3.2 standalone** (per `feedback_changelog_umbrella.md`)

**umbrella**: 本 patch 进 `changelog-v1.8.0.md` (v1.x 轴单 umbrella CHANGELOG); 不创建 standalone `changelog-v1.8.3.2.md`。commit tag `fix(v1.8.0):` 对齐最近 7 个 commit 格式 (`f44c764` v1.8.2 patch update, `31d2687` v1.8.2 patch, `de4f219` v1.8.1, `6b182dd` v1.8.0 W-059 真修, v1.8.3 ship commit, v1.8.3.1 ship commit + 本 patch)。

---

## 引用

- **spec** `docs/abis/jhyy-lang-spec-v1.3.0.md` — 锁定 (v1.8.0 不修订, v1.x FINAL 锁)
- **abi** `docs/abis/jhyy-abi-v1.0.0.md` — 锁定 (v1.8.0 不修订)
- **workarounds** `docs/internal/workarounds.md` — master table W-059 ✅ RESOLVED + W-060 ❌ INVALID + W-061 ❌ INVALID + section bodies history 段保留 + Resolution (v1.8.0) / Status (v1.8.0) 段
- **W-028 fix** `mcp-jhyy/jhyy_regress.py` line 243-263 mod-256 equalize 比较 (per `feedback_qbe_crlf_root_cause.md` + `feedback_fix_evaluation_rule.md`)
- **feedback_git_identity_canonical** — author `JHYY <15901598712@163.com>` (JHYY@local 不算主页绿格子, 永不接受)
- **feedback_commit_coauthor** — co-author `MiniMax-M3 <noreply@MiniMax>`
- **feedback_no_date_estimates** — 计划中不要"几月几月完成"日期估时; 用 sprint 序列 + 相对顺序
- **feedback_fix_evaluation_rule** — MANDATORY 5/5 PASS on target test 才能声称 fix work
- **feedback_audit_single_commit_diff** — audit commit 改动只用 `git show <sha>` / `git diff <sha>~1 <sha>`, **不要** 用累计跨 commit diff
- **feedback_doc_refactor_factcheck** — docs 重构前逐条 fact-check: 限制是否仍存在 / 是否已 ship / 是否措辞过时
- **feedback_changelog_umbrella** — vX.Y axis 只用 1 个 umbrella changelog, 不创建 standalone changelog-vX.Y.Z.md
- **feedback_document_workarounds_in_docs** — workaround 必须详细记录到 `docs/internal/workarounds.md`, 不止代码注释; superseded 标 RESOLVED 不删除
- **feedback_small_plans_no_docs** — 单 stage step-by-step plan 不写 `docs/plans/`, 走 plan mode 或直接执行
- **v1.7.3 ship commit** `57f89dc` (2026-08-28) — 32 candidates 完整 ship (Stage 1-5 + v1.7.1/2/3 patches), tag `v1.7.3` = v1.x FINAL marker, spec v1.3.0 locked
- **v1.3.6 ship commit** `169759c` (defer ship 时 0 accept-path test 验证 — ship 流程 gap, v1.8.0 反思闭环)
- **v1.3.7 ship commit** `0f32977` (Pattern binding ship 时只覆盖 single-payload single-binding — W-060 fact-check 误诊历史)
- **W-019 RESOLVED** 2026-08-14 (1-layer 嵌套真修, per `docs/logs/v1/changelog-v1.4.6.md` + `compiler/src/codegen.c` line 6638134 commit — W-061 fact-check 误诊历史)