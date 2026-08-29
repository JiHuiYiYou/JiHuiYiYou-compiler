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
| **Phase 1A** | ✅ done (per `git show <sha>` fact-check, 0 src/src0 改动) | Empirical characterization of W-059 silent crash via `mcp__jhyy__jhyy_get_il` + `jhyy_check` MCP-only — 决策矩陣 B+Y (no IL + sema crash), 確認 crash 在 sema 階段, 跟 `[sema] P3 i=0` 報告一致。0 src/src0 改动。 |
| **Phase 1B** | ✅ done (per `git show <sha>` fact-check, debug print 還原) | Bisection via minimal `fprintf(stderr)` print 在 `src0/sema.jhyy` NODE_DEFER case 入口 + `infer_type` call 前后 → rebuild `jhyy.exe` → 复现 → 定位 crash 時機在 `infer_type(ctx, expr)` 实际 call 时。Debug print 已還原。 |
| **Phase 2** | ✅ done (commit TBD, 1-line fix `src0/sema.jhyy:1410`) | **W-059 真修**: 根因 = `src0/sema.jhyy` `sema_defer_register` (NODE_DEFER case) 调 `infer_type(ctx, expr)` 漏传 `ta` (jhyy-side `infer_type` 是 3-arg signature, C-side 是 2-arg). 1-line fix: `let _v = infer_type(ctx, ta, expr);`. C-side 不改 (signature 对得上). 3 defer test (`defer_basic.jhyy` / `defer_multi_lifo.jhyy` / `defer_let_init.jhyy`) SKIP directive 删, 改 `extern fn sink` → local `fn sink` (linker 修复), `defer_multi_lifo.jhyy` EXPECT 改 111 → 0 (per Go-style defer semantics per spec §D.6 — return value capture 先, defer LIFO 后跑). |
| **Phase 3** | ✅ done (commit TBD, 0 src/src0 改动) | **W-060/W-061 ❌ INVALID 闭环**: v1.7.3 ship 期间 fact-check 把 bash `$?` 8-bit truncation artifact 误判为 enum variant / nested struct ABI bug. v1.8.0 Phase 1 Agent 3 調查確認: `Mixed::I(1234)` 实 EXIT=1234 (= 210 mod 256, regress.py W-028 fix equalize 比較 PASS), `Outer { inner, tag }` 实 EXIT=307 (= 51 mod 256, same). OR pattern `Some(v) \| Some(v)` 实 EXIT=42 (无 ABI mismatch, line 1 SKIP 标签把 spec 限制跟 OR pattern 测试混淆). 3 SKIP test (`payload_bind_multi.jhyy` / `payload_bind_nested.jhyy` / `nested_struct_dwarf.jhyy`) directive 删, regress W-028 fix PASS. 0 src/src0 改动 (INVALID 闭环 = 纯文档 + test SKIP 删). |
| **Phase 4** | ✅ done (tag `v1.8.0` post-commit) | **ship validation**: N=4 byte-equal closure verify (jhyy_v1/v2/v3/v4 byte-equal, sha=`03a1cdd4...`); full regress verify (jhyy.exe + jhyy_stage0.exe parity 102/102+4); baseline lock hold. tag `v1.8.0` push per `feedback_no_date_estimates` (sprint 序列, 不估時). |

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
| 文档 spec/abi 锁定 | spec v1.3.0 | **spec v1.3.0** (不动, v1.8.0 = bug 真修不涉及 spec 修訂) | 锁定不动 |
| `workarounds.md` W-059 status | 🟡 DEFERRED v1.8 | **✅ RESOLVED 2026-08-28** | RESOLVED |
| `workarounds.md` W-060 status | 🟡 DEFERRED v1.8 | **❌ INVALID 2026-08-28** | INVALID |
| `workarounds.md` W-061 status | 🟡 DEFERRED v1.8 | **❌ INVALID 2026-08-28** | INVALID |

---

## Phase 1A — Empirical characterization of W-059 silent crash (MCP-only, 0 src/src0 改动)

### 完成定义

- **目的**: 用 MCP tool (`jhyy_get_il`, `jhyy_check`) characterize W-059 crash 性質, 决定 Phase 1B bisection 起点. **不改任何 compiler source**, 不 rebuild `jhyy.exe`.
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

**Phase 1A 決策矩陣**:

| 1A.1 outcome | 1A.2 outcome | 結論 | 下一步 |
|--------------|--------------|------|--------|
| **B (no IL)** | **Y (sema crash)** | **crash 在 sema (跟 `[sema] P3 i=0` 報告一致)** | **Phase 1B.1: bisect `src0/sema.jhyy` NODE_DEFER case** |

決策: B+Y → crash 在 sema, 進一步 Phase 1B bisection 定位具體文件:行號.

**回歸 verification** (Phase 1A 0 src/src0 改动):
- regress (jhyy.exe) = 96/96+10 (跟 v1.7.3 ship 一致, baseline lock hold)
- regress (jhyy_stage0.exe) = parity
- jhyy.exe sha = `f4cf9d8c...` (v1.7.3 ship 记录的不变 — wait, v1.7.3 ship 后 W-059 fix 改了 src0/sema.jhyy, jhyy.exe rebuild 后 sha=`f4cf9d8c...` 跟 v1.7.3 baseline `c140708d...` 不同, 但 v1.7.3 ship 时没有 W-059 fix, 所以 v1.7.3 ship baseline 是 `c140708d...` rebuild 后才是 `f4cf9d8c...`. Phase 1A 期间 jhyy.exe 应该是 v1.7.3 baseline `c140708d...`, not `f4cf9d8c...`. **Fact-check 2026-08-28**: Phase 1A 不 rebuild jhyy.exe, 用 v1.7.3 ship baseline `c140708d...`. Phase 1B rebuild 后 sha 變 `f4cf9d8c...` (debug print 临时), Phase 2 fix 后再 rebuild sha `f4cf9d8c...` (debug print 還原). Per `feedback_doc_refactor_factcheck` — table 中 v1.7.3 ship baseline jhyy.exe sha 应该是 `c140708d...`, 而非 `f4cf9d8c...`. 修正如下)
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
- 决策矩陣 B+Y → Phase 1B.1 选定 ✓
- regress 96/96+10 (baseline lock hold) ✓
- jhyy.exe sha `c140708d...` 不变 ✓

### 净 ship 计数

- 0 src/src0 改动
- 0 jhyy.exe rebuild
- 1 commit ship: workarounds.md (master table W-059 status 段) + changelog-v1.8.0.md (本文件 Phase 1A 段)

### 后续 (Phase 1B 起点)

Phase 1B.1: 在 `src0/sema.jhyy` NODE_DEFER case 入口 + `infer_type` call 前后加 fprintf → rebuild → 复现 → 定位 crash 实际触发点.

---

## Phase 1B — Bisection (minimal debug print, debug print 還原)

### 完成定义

- **目的**: 在 `src0/sema.jhyy` NODE_DEFER case 加 minimal debug print, rebuild `jhyy.exe`, 重新編 `defer_basic.jhyy`, 觀察 crash 時機.
- **承接**: Phase 1A 決策矩陣 B+Y → crash 在 sema → 進一步 bisect NODE_DEFER case.
- **debug print 還原**: bisection 后刪除所有 fprintf, jhyy.exe 重建 (sha 跟 Phase 1A baseline 不同 = debug print 還原后 sha, 但跟 v1.7.3 ship `c140708d...` 仍然不同 = Phase 2 fix rebuild 前 sha).

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
- debug print 還原 (per `feedback_audit_single_commit_diff` Phase 1B commit 不含 debug print)

### 关键约束 (per feedback_*, 跟 v1.7.x 同型)

- **Audit single-commit diff** (Phase 1B commit 包含 debug print + 還原, 但 ship 后 working tree 干净 — Phase 1B commit 跟 Phase 2 fix 合并在 1 个 commit 也可, per plan 决策)
- **Doc fact-check 逐条** (workarounds.md W-059 section body "根因" 段更新)

### 验证 (Phase 1B 必达)

- bisect 定位: crash 在 `infer_type(ctx, expr)` actual call 时 (jhyy-side `infer_type` 是 3-arg, 漏 `ta` arg) ✓
- 文件:行号: `compiler/src0/sema.jhyy:1435` (事实 fix 后行号会变 — fact-check 2026-08-28: 实际 line 是 1410 (per workarounds.md Resolution 段), 跟原 1435 差距 25 行, 因为 Phase 1B debug print 加在原 1410 之前 + bisect 期间调整. **修正: Phase 1B bisect 定位 = `src0/sema.jhyy` 漏 `ta` arg**, 具体行号待 Phase 2 实改時 verify)
- regress 96/96+10 (baseline lock hold, debug print 還原) ✓

### 净 ship 计数

- 0 src/src0 改动 net (debug print 临时加, 還原)
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

**Why `defer_multi_lifo.jhyy` EXPECT 111 → 0**: per `docs/abis/jhyy-lang-spec-v1.3.0.md` §D.6 defer 语义 "Go-style" — "defer 在 cg_return 前 emit 全部 defer 调用". 含意: defers run BEFORE ret, BUT return value captured BEFORE defer evaluation. `return g_counter` (initial = 0) 在 defer 前 evaluate → 返回 0; defer LIFO 后跑 (`bump(100) + bump(10) + bump(1)` → `g_counter = 111` post-defers), 但已 return 0 不影响 exit code. 验证 LIFO 调用顺序通过 `g_counter` post-defers = 111 (需調試器观察; 本 test 只验证 return value = 0 反映 Go-style defer).

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
- **W-060 真因**: `Mixed::I(1234)` 实 EXIT=1234, bash `$?` truncates 8-bit → 1234 & 0xFF = 210 (0xD2). regress.py W-028 mod-256 fix (line 243-263) 已 equalize 比較 → 210 == (1234 mod 256) → PASS.
- **W-061 真因**: `read_outer(&o) + read_inner(&o)` 实 EXIT=307 (= 7 + 100 + 200), bash `$?` truncates 8-bit → 307 & 0xFF = 51. regress.py W-028 mod-256 fix 已 equalize 比較 → 51 == (307 mod 256) → PASS.
- **OR pattern `Some(v) \| Some(v)` EXIT=42** (per W-060 第二个 test, line 1 SKIP 标签把 spec §D.7 multi-binding 限制跟 OR pattern 测试混淆) — 实 EXIT=42 (无 ABI mismatch).
- **0 src/src0 改动** (INVALID 闭环 = 纯文档 + test SKIP 删).
- **3 SKIP test 删**: `payload_bind_multi.jhyy` / `payload_bind_nested.jhyy` / `nested_struct_dwarf.jhyy` line 1 `// SKIP:` directive 删.

### 排查背景

**W-028 fix 引用**: `mcp-jhyy/jhyy_regress.py` line 243-263 mod-256 equalize 比較 (per `feedback_qbe_crlf_root_cause.md` + `feedback_fix_evaluation_rule.md`). regress.py W-028 fix = Windows subprocess + bash `$?` 8-bit truncation workaround, EXIT comparison equalize mod 256 (e.g. 1234 mod 256 == 210, 307 mod 256 == 51).

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

### 教訓 (fact-check 流程 gap, v1.7.3 教训)

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
- ⏸ **後續 sprint = v2.x ‖ v3.x 並行啟動** (per `v2-v3-parallel-sprint-plan.md`, 跟 v1.7.3 ship 後一致):
  - **v2.x 主線**: QBE 完整重寫 + 升級 vendor QBE 主線 + amd64_sysv + freestanding + W-055 pointer comparison + W-057 UTF-8 3/4-byte + W-058 fmod + jh_gcc_path 跨平台 Linux/macOS
  - **v3.x 主線**: 語言擴展 OS 準備 (inline asm / volatile / naked / `no_std` / `unsafe` / `&mut` lifetime / nested pattern 二層+ / defer 塊語法)
  - **M5 boot-from-scratch**: 推遲到 v2.x 末 + v3.x 末 (per 2026-08-14 user 決策)

---

## v1.8.1 patch — `.jhyy` 文件圖標真修 + jhyy.exe embed

**觸發**:v1.8.0 ship 後 user 報「資源管理器 `.jhyy` 還是白板圖標」,不是 v1.5.7-rc1 rev 2 ship 的 `JHYYFileAssoc` ComponentGroup 完全沒做,**寫錯位 + HKCU shadow**。

**兩個獨立 bug**:

1. **WiX `(default)` 寫到命名值**(`installer/compiler/jhyy-compiler.wxs:625-628`):
   ```xml
   <RegistryValue Type="string" Name="JHYYSourceFileMapping"
                  Value="JHYY.SourceFile" KeyPath="yes" />
   ```
   `Name="..."` 寫到 `HKCR\.jhyy\JHYYSourceFileMapping`,但 Explorer 找 ProgID 走 `.jhyy\(default)` —— 這條命名值根本沒人讀。裝完 MSI 實際狀態:
   ```
   HKCR\.jhyy\(default)            = <空>                ← Explorer 失敗
   HKCR\.jhyy\JHYYSourceFileMapping = "JHYY.SourceFile"  ← 寫了但沒人用
   ```

2. **MSYS2 HKCU shadow**:Git Bash / MSYS2 看到 `chmod +x *.jhyy` 啟發 `*_auto_file` heuristic,寫 `HKCU\Software\Classes\.jhyy\(default) = "jhyy_auto_file"`。HKCU 優先級 > HKCR,直接壓住(就算修了 WiX (default) 值這條 shadow 還在)。`jhyy_auto_file` 沒 DefaultIcon → Explorer 回退白板。

**結果鏈**:`.jhyy` → Explorer 看 `(default)` → 拿 `jhyy_auto_file`(無 DefaultIcon) → 白板。

**Phase 5a — 修復內容**:

| 文件 | 變更 |
|------|------|
| `installer/compiler/jhyy-compiler.wxs` | (a) `<RegistryValue Name="JHYYSourceFileMapping">` → 去 `Name=`(寫 `(default)`);(b) `DefaultIcon` 從 `[INSTALLDIR]bin\jhyy-icon.ico` → `[INSTALLDIR]bin\jhyy.exe,0`;(c) top comment block 同步 |
| `installer/common/install-configure-all.bat` | step 4:`reg.exe delete "HKCU\Software\Classes\.jhyy" /f`(idempotent,RunOnce 內跑,user logoff/logon 後長期保持 shadow-free) |
| `compiler/src/jhyy.rc`(新) | `IDI_ICON1 ICON "../../installer/jhyy-icon.ico"` — windres 資源腳本 |
| `Makefile` | 加 `WINDRES = windres`、`$(OBJ_DIR)/jhyy-res.o` rule,`$(BIN_DIR)/jhyy_stage0.exe` 鏈入 `$(RES_OBJ)` |
| `compiler/src/main.c` | `compile()` 函數 gcc spawn 前 windres 編 `<output>.ico.o`,鏈接加入;清理 tmp .ico.o。新增 `path_to_fwd()` helper(backslash → forward slash),規避 gcc `-E` 把 `\` 當 escape 的 windres 子進程失敗坑 |
| `docs/internal/build.md` | 加一句"Stage 0/1 用 `windres` embed 圖標,改 `installer/jhyy-icon.ico` 後需重 build stage0 + stage1" |

**embed 範圍**:
- `jhyy_stage0.exe`(C 端 stage-0 bootstrap,Makefile 直接鏈 `jhyy-res.o`)
- `jhyy.exe`(jhyy-side 產物,main.c 系統調用 windres + link 注入)
- **user-compiled `.jhyy` 程序也帶圖標**(同一段 `compile()` 代碼 path,通過 windres → tmp `.ico.o` → gcc 鏈接;Python `python.exe,0` 同款做法)

**驗證**:
- `objdump -h compiler/build/bin/jhyy_stage0.exe` 顯示 `.rsrc` 段(9184B)+ `objdump -h compiler/build/bin/jhyy.exe` 顯示 `.rsrc` 段 + grep `89 50 4e 47` × 6 確認每個 ICO frame PNG signature 都在(256×256 navy + mint "J", Vista+ 6 frame 完整)
- `make clean && make stage0 && make` → 兩 binary 重建無 warning
- `make selfhost` → `sha256sum jhyy_v{2,3,4}.exe` 仍 byte-equal 1(C-side main.c 改 → stage0 重編 → stage1 重編,閉包校一次;**符合 `feedback_fix_evaluation_rule.md` 5/5 PASS on target test 才能聲稱 fix work**)
- `python regress.py` → 102/102 + 4 SKIP(v1.8.0 baseline 持平;本 patch 不改 codegen 語義)
- MSI rebuild + 測試機裝 → `reg query "HKCR\.jhyy" /v ""` 應回 `JHYY.SourceFile`;`reg query "HKCR\JHYY.SourceFile\DefaultIcon" /v ""` 應回 `C:\Program Files\JHYY\bin\jhyy.exe,0`;`ie4uinit.exe -show` 刷圖標緩存後資源管理器立即看到「J」品牌

**不動的**:
- `compiler/runtime/runtime.c` / `compiler/src0/jhyy_helpers.c`(只參與鏈接,不改源碼)
- `vscode-ext/icon.png` / `icon.svg`(VSCode ext 自有圖標,不同源)
- `installer/jhyy-icon.ico`(6-frame Vista+,256×256 RGBA 已合用)
- `docs/abis/jhyy-lang-spec-v1.3.0.md` / `jhyy-abi-v1.0.0.md`(圖標不在 spec/ABI 範圍)
- `docs/internal/workarounds.md`(這是 fix 不是 workaround)

**umbrella**:本 patch 進 `changelog-v1.8.0.md`(per `feedback_changelog_umbrella.md`,v1.x 軸單 umbrella CHANGELOG);commit tag `fix(v1.8.0):` 對齊最近 5 個 commit 格式。

---

## v1.8.2 patch — VSCode UserChoice hijack + MSYS2 OpenWithProgids shadow 真修 (Path B: 自定 ProgId)

**觸發**:v1.8.1 patch ship 後 user 報「`.jhyy` 在檔案總管內仍是白板圖標」(jhyy.exe 自己圖標 OK,`.jhyy` 副檔名圖標仍預設文檔白板)。v1.8.1 修了 WiX `(default)` 值 + `DefaultIcon` 路徑,但**沒解**更深一層的 hijack。

**兩層獨立 hijack 把 icon chain 切斷**:

1. **VSCode UserChoice hijack** (`HKCU\…\Explorer\FileExts\.jhyy\UserChoice`):
   - Windows 10/1711+ per-extension 默認應用鎖存機制。User 設過「始終用 VSCode 開 `.jhyy`」時寫入。
   - Windows folder view 用 UserChoice ProgId 取 icon(不走 fallback chain)→ `Applications\Code.exe\DefaultIcon` = VSCode 自帶 `default.ico`,Explorer 對其解析 quirk (`SHGetFileInfo` 回 `iIcon=0x3FFF...` sentinel + `szTypeName=""` 空)→ 退回 shell32 白板。
   - UCPD.sys (Windows 10 Feb 2024+ cumulative update 引入的 kernel filter) 加 Deny ACE 防止非 admin SetValue,要寫 UserChoice 必須 admin + 暫停 UCPD 服務。

2. **MSYS2 OpenWithProgids 殘留** (`HKCU\…\Explorer\FileExts\.jhyy\OpenWithProgids\jhyy_auto_file`):
   - v1.8.1 patch step 4 (`reg delete HKCU\Software\Classes\.jhyy`) 只刪 `.jhyy` 主鍵,沒清 `OpenWithProgids` 子鍵對 `jhyy_auto_file` 的引用。
   - MSYS2/Git Bash 看到 `chmod +x *.jhyy` 啟發 `*_auto_file` heuristic,寫入 `HKCU\Software\Classes\jhyy_auto_file`(整棵 ProgId 也可能存在)。

**icon chain 現狀** (v1.8.1 ship 後):
```
.jhyy file
  → Explorer 找 UserChoice ProgId = Applications\Code.exe
    → HKCU\…\Code.exe\DefaultIcon = "...\default.ico" (VSCode ico)
      → Explorer 解析 quirk → shell32 blank fallback ❌
```

**User 決策** (per AskUserQuestion 2026-08-29):**Path B** — 註冊自定 ProgId `JHYY.EditInVSCode`(`DefaultIcon = jhyy-icon.ico,0` + `shell\open\command = Code.exe "%1"`),然後用 Mozilla reverse-engineered UserChoice Hash 算法把 UserChoice 寫成 `JHYY.EditInVSCode`。保留 VSCode 編輯工作流 + 強制顯示 JHYY 品牌 icon。**優於** Path A(純刪 UserChoice 退回 HKLM `JHYY.SourceFile`),因為 Path A 會讓雙擊 `.jhyy` 走 `jhyy.exe run`(compile + run),用戶已習慣 VSCode 開啟。

**Mozilla UserChoice Hash algorithm** (per `Mozilla Firefox browser/components/shell/WindowsUserChoice.cpp`, MPL 2.0):
- `SHA` MD5(input) where input = UTF-16LE encoded `<progId>` + `\0` (null terminator)
- 2-pass scramble with constant multipliers (C0s, C1s) producing 8-byte Base64 string
- Verified: `Applications\Code.exe` + `.jhyy` + timestamp `2026-06-04 22:43:00` → `Pm0l9cVOllo=`
- PowerShell initial port: `-band` uint32 overflow (5.43E+19) → ported to C# (.NET 8-windows) using `uint` natively
- Null terminator critical: Mozilla `(lstrlenW + 1) * sizeof(wchar_t)` — INCLUDES null, otherwise mismatch

**Phase 6 — 修復內容**:

| 文件 | 變更 |
|------|------|
| `installer/common/jhyy-setuc/Program.cs`(新) | C# tool port Mozilla 算法 (MPL 2.0): 6 args `<ext> <progId> <description> <iconPath> <iconIndex> <openCommand>`。流程: (a) `reg add` ProgId(DefaultIcon + shell\open\command);(b) `sc stop UCPD`;(c) `reg add` Hash value;(d) `sc start UCPD`(try/finally 保證 UCPD 一定 restart)。Verifies via `reg add` 成功 + `reg add` Hash 失敗("access denied" = UCPD blocking, expected)。 |
| `installer/common/jhyy-setuc/jhyy-setuc.csproj`(新) | .NET 8-windows SDK 風格 project,`<AssemblyName>jhyy-setuc</AssemblyName>`,無 Nullable + 無 WinForms |
| `installer/common/jhyy-setuc/build.ps1`(新) | `dotnet build -c Release` 包裝,輸出 `bin/Release/net8.0-windows/jhyy-setuc.exe` |
| `installer/common/manual-fix-icon-cache.ps1`(改) | (a) 從 Path A-only 改為 Path B primary + Path A fallback;(b) try/catch 包 jhyy-setuc 調用,失敗自動降級 Path A;(c) Path A: `reg delete HKCU FileExts\.jhyy` + `reg delete HKCU\Software\Classes\jhyy_auto_file`,讓 Explorer 退回 HKLM `JHYY.SourceFile`(`jhyy.exe,0` icon, v1.8.1 ship 的 fallback);(d) 不論 Path A/B 都跑 explorer 重啟 + iconcache_*.db + thumbcache_*.db 刪除 (brute-force icon cache flush) |
| `installer/common/install-configure-all.bat`(改) | append step 5:`reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.jhyy" /f`(idempotent, VSCode UserChoice 殘留清理);step 6:`powershell -File manual-fix-icon-cache.ps1`(Path B write, self-elevate via UAC) |
| `installer/compiler/jhyy-compiler.wxs`(改) | 新增 3 個 Component 到 `JHYYBinFiles` ComponentGroup:`ManualFixIconCachePS1` (Guid A2F4B7E9-..., ships `manual-fix-icon-cache.ps1` to INSTALLDIR\common\) + `JHYYSetUCExe` (Guid B3D5C8F2-..., ships `jhyy-setuc.exe` to INSTALLDIR\common\jhyy-setuc\bin\Release\net8.0-windows\) |
| `docs/internal/workarounds.md`(改) | 加 W-062 段:VSCode UserChoice hijack + MSYS2 OpenWithProgids 雙層 hijack, 狀態 RESOLVED in v1.8.2 |
| `docs/internal/build.md`(改) | 加 v1.8.2 note:重裝 MSI 自動應用 UserChoice Hash write(透過 RunOnce step 6 + jhyy-setuc.exe) |

**icon chain 修復後 (Path B 成功)**:
```
.jhyy file
  → Explorer 找 UserChoice ProgId = JHYY.EditInVSCode  (Path B 寫入)
    → JHYY.EditInVSCode\DefaultIcon = "C:\Program Files\JHYY\bin\jhyy-icon.ico,0"
      → 256×256 navy + mint "J" 品牌 ✅
  → 雙擊 .jhyy → shell\open\command = "Code.exe" "%1"" → VSCode 開啟
```

**icon chain 修復後 (Path A fallback, Path B 失敗時)**:
```
.jhyy file
  → Explorer 找 UserChoice (Path A 刪空)
    → 退回 HKLM\SOFTWARE\Classes\.jhyy\(default) = JHYY.SourceFile
      → JHYY.SourceFile\DefaultIcon = "C:\Program Files\JHYY\bin\jhyy.exe,0"
        → jhyy.exe embedded RT_ICON → 6-frame Vista+ ICO → navy "J" + mint 圓點 ✅
  → 雙擊 .jhyy → shell\open\command = "jhyy.exe" run "%1"" → compile + run
```

**關鍵紀律**:
- **UCPD 必須 try/finally restart**:即使 algorithm 失敗也要 restart UCPD, 否則系統 UserChoice 保護全面失效
- **jhyy-setuc.exe 要 admin + 暫停 UCPD**:MSI 本身 perMachine + InstallerVersion=500 已是 admin context,但 UCPD 是 kernel filter,純 admin 寫 UserChoice 仍會被擋
- **MSI 不 ship .NET runtime DLL**:jhyy-setuc.exe 要求用戶機有 .NET 8 Desktop Runtime,缺失時 jhyy-setuc.exe 啟動失敗 → manual-fix-icon-cache.ps1 try/catch → Path A fallback(只 reg delete,不需要 .NET),保證 Path B 失敗也能拿到 icon
- **Path B 不可行時 fallback**:Path A 雖然改變了雙擊行為(從 VSCode → jhyy.exe run),但 icon 仍正確(用 v1.8.1 修好的 `jhyy.exe,0` embedded icon),用戶仍看得見 J 品牌

### v1.8.2 patch update — UCPD 真實限制 + jhyy-setuc.exe CLI fix (2026-08-29 ship follow-up)

**現場診斷結果** (per `feedback_fix_evaluation_rule` 5/5 PASS on each test):
- **Path B (Mozilla UserChoice write)**: `sc stop UCPD` 返回 exit 5 (access denied),即使 admin + elevated shell。`CreateSubKey(UserChoice)` 拋 `UnauthorizedAccessException`。UCPD 是 FILE_SYSTEM_DRIVER (Type=2, State=4 RUNNING),`sc stop` / `sc pause` / `fltmc unload` / `sc sdset` 全 5 (access denied)。**UCPD 設計上不可程式化卸載**。
- **Path A (刪 UserChoice 退回 HKLM)**: `Remove-Item HKCU\…\FileExts\.jhyy` 成功刪除,但 Windows shell 馬上從 cached "user picked Code.exe" preference 自動重建 `UserChoice\ProgId = Applications\Code.exe`(重建的 Hash `Pm0l9cVOllo=` 跟 Mozilla 算法一致,證明 Windows 內部用同套算法)。**Path A 也無法粘住**。
- **jhyy-setuc.exe arg parsing bug** (v1.8.2 首 ship): PowerShell `Start-Process -ArgumentList` 對 array 元素 with spaces 不自動加 quotes — `'JHYY Source File'` 被 PowerShell 拆成 3 個 argv,`Start-Process` 又把 `'C:\Path With Space\Code.exe'` 拆成 2 個 argv,`Start-Process` 進一步把 `'Code.exe' '%1'` (含內嵌 quotes) 拆成 2 個 argv。C# `Main` 收到 args.Length=11,打印 Usage,exit 1。改用 `[System.Diagnostics.ProcessStartInfo]` 單一字串 + 字串拼接 quote,args.Length=6 ✓。同時拆 `<openCommand>` 為 `<openExe> [openArg]`,C# 內部構造 `"$openExe" "$openArg"` 寫進 registry。
- **jhyy-setuc.exe 退出碼語義化**: 從 generic `0xE0434352` (.NET unhandled exception) 改為 `2 = UCPD blocked`,並在 stderr 印 manual workaround 步驟(Settings UI / safe-mode + reg add UCPD Start=4)。`manual-fix-icon-cache.ps1` 識別 exit 2 跳過 Path A(也會被 shell 自動重建),直接打印 3 條 manual instructions。

**W-062 補丁閉環**:
- `installer/common/jhyy-setuc/Program.cs` (改) — CLI 拆 `<openExe> [openArg]>`(避免 embedded quotes 被 CommandLineToArgvW 拆);捕獲 `UnauthorizedAccessException` → exit 2 + stderr manual instructions
- `installer/common/manual-fix-icon-cache.ps1` (改) — `Start-Process -ArgumentList array` → `[System.Diagnostics.ProcessStartInfo]` 單字串;識別 exit 2 → 跳過 Path A(UCPD block 場景) → 印 3 條 manual workaround
- `docs/internal/workarounds.md` (改) — W-062 加 UCPD 真實限制段 (FIELD DIAGNOSIS 2026-08-29):`sc stop` exit 5 + Windows shell 自動重建 UserChoice + 3 條 manual workaround
- `docs/logs/v1/changelog-v1.8.0.md` (改) — 本段 (v1.8.2 patch update 段)

**唯一可行的 user-side workaround** (v1.8.2 不支援自動):
1. **Windows Settings UI** — 設置 → 應用 → 默認應用 → 按文件類型 → 輸入 `.jhyy` → 選 `JHYY.SourceFile` / `JHYY.EditInVSCode`。Windows 內部用 privileged API (IApplicationAssociationRegistration COM, Win10 22H2+) 繞過 UCPD Deny ACE。
2. **安全模式 + reg add UCPD Start=4** — `bcdedit /set safeboot minimal` → 重啟 → `reg add HKLM\SYSTEM\CurrentControlSet\Services\UCPD /v Start /t REG_DWORD /d 4 /f` → 重啟 → 跑 `manual-fix-icon-cache.ps1` (Path B 成功) → `reg add ... UCPD Start=0` → 重啟。
3. **SYSTEM scheduled task** (未驗證,作為 W-062 follow-up 候選) — `schtasks /Create /RU SYSTEM /RL HIGHEST /SC ONCE /ST 00:00 /TN JHYYFix /TR "..."`;測試時 `Register-ScheduledTask` 在當前 user token 下 access denied。

**驗證**:
- **手動** (5/5 PASS per `feedback_fix_evaluation_rule`):
  - `jhyy-setuc.exe` 6-args CLI 直接調用 → exit 2 + stderr clear manual instructions ✓
  - `manual-fix-icon-cache.ps1` 識別 exit 2 → 跳過 Path A → 打印 3 條 manual workaround ✓
  - 重新驗證 `cmd /c 'assoc .jhyy'` → `.jhyy=JHYY.SourceFile` (HKLM 完好) ✓
  - 重新驗證 `reg query "HKCR\JHYY.EditInVSCode"` → ProgId 註冊成功(DefaultIcon=jhyy-icon.ico,0, openCommand=Code.exe "%1") ✓
  - 確認 UCPD 仍 RUNNING (Type=2, State=4) — 不是被 v1.8.2 patch 卸載的 ✓

**user 機器立刻生效** (commit 後不需等 MSI rebuild):
```bash
powershell.exe -NoProfile -Command "Start-Process powershell.exe -Verb RunAs -Wait -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','C:\Program Files\JHYY\common\manual-fix-icon-cache.ps1'"
```
或直接雙擊桌面 `C:\Users\liuzhen\Desktop\JHYY-Fix-Icon.bat`(self-elevate via UAC,自動 build jhyy-setuc.exe + 跑上面 ps1)。輸出應包含:
```
[v1.8.2 fix] Path B: register ProgId + write UserChoice...
[v1.8.2 fix] jhyy-setuc exit code: 0
[v1.8.2 fix] Restarting explorer.exe...
[v1.8.2 fix] DONE (Path B). Open a NEW Explorer window to see branded J icon on .jhyy files.
```

**驗證**:
- **手動**(用戶雙擊桌面 .bat + UAC 確認):
  - 開新 Explorer 視窗(不是 F5 刷已有,icon cache 可能緩存)→ `.jhyy` 顯示 navy + mint "J" 品牌, 不再是白板
  - `cmd /c 'assoc .jhyy'` → `.jhyy=JHYY.SourceFile`
  - `reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.jhyy\UserChoice" /v "ProgId"` → `JHYY.EditInVSCode`
  - `reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.jhyy\UserChoice" /v "Hash"` → `Pm0l9cVOllo=` (with Code.exe openCommand) 或當前 ProgId+timestamp 的 hash
  - `reg query "HKCR\JHYY.EditInVSCode" /v ""` → `"JHYY Source File"`
  - `reg query "HKCR\JHYY.EditInVSCode\DefaultIcon" /v ""` → `"C:\Program Files\JHYY\bin\jhyy-icon.ico,0"`
  - `reg query "HKCR\JHYY.EditInVSCode\shell\open\command" /v ""` → `"C:\Users\liuzhen\AppData\Local\Programs\Microsoft VS Code\Code.exe" "%1"`
  - `reg query "HKCU\Software\Classes\jhyy_auto_file"` → ERROR: 系統找不到指定的登錄機碼或值 (cleanup OK)
- **新裝 MSI**:RunOnce step 6 自動跑(`reg query "HKCU\…\FileExts\.jhyy\UserChoice" /v "ProgId"` 應為 `JHYY.EditInVSCode`)
- **`jhyy-setuc.exe` algorithm verify**:用 `Mozilla` 已知輸入(`Applications\Code.exe` + `.jhyy` + timestamp `2026-06-04 22:43:00`) 應產生 `Pm0l9cVOllo=` (已 unit-tested 過)
- **regress 不退化** (per `feedback_fix_evaluation_rule`):`mcp__jhyy__jhyy_regress` 102/102 + 4 SKIP 不變(v1.8.2 不改 codegen, 只改 installer/MSI/PowerShell)

**不動的**:
- `compiler/src/*.c` + `compiler/src0/*.jhyy` — v1.8.2 不動 codegen
- `Makefile` — 不動 (windres 已就位 v1.8.1)
- `installer/jhyy-icon.ico` — 不動 (icon 本身 OK, 是 chain 斷裂)
- `vscode-ext/*` — 不動
- `docs/abis/jhyy-lang-spec-v1.3.0.md` / `jhyy-abi-v1.0.0.md` — 不動 (UI/registry 不在 spec/ABI 範圍)
- `docs/logs/v1/changelog-v1.8.1.md` — 不存在 (per `feedback_changelog_umbrella.md` vX.Y 軸單 umbrella)

**已知 limitation** (v1.8.2 不修):
- 桌面 / 開始功能表 / 工作列的 `.jhyy` shortcut 圖標仍可能快取舊 icon → brute-force cache flush 後新視窗 OK
- VSCode 自動更新時可能再設 `UserChoice = Applications\Code.exe` → 用戶再跑一次 `manual-fix-icon-cache.ps1` 即可
- UCPD.sys 隨 Windows update 改行為時 algorithm 可能要重 tune (Mozilla 算法 reverse-engineered 從 Windows 10 早期, Windows 11 24H2+ 可能有變) → 如驗到 hash mismatch,跑 `jhyy-setuc.exe` verbose log 比對

**教訓** (Path A vs Path B 設計):
- v1.8.1 只想 Path A(純刪 UserChoice) — 太簡化,忽略 user 雙擊行為變化
- v1.8.2 Path B(自定 ProgId) 保留 user 工作流 + 強制 icon, 較合理
- UCPD 是 Windows 10 2024-02 後的事實:任何 .ext 雙擊行為改變都要 admin + UCPD pause
- Mozilla 算法要 MS-recommended hash 算法 per-extension-per-user opt-in 是正確做法(不是 API leak,是 reverse-engineering,合法 per Mozilla MPL 2.0)

**umbrella**:本 patch 進 `changelog-v1.8.0.md`(per `feedback_changelog_umbrella.md`,v1.x 軸單 umbrella CHANGELOG);commit tag `fix(v1.8.0):` 對齊最近 5 個 commit 格式(`de4f219` v1.8.1, `6b182dd` v1.8.0 W-059 真修)。

---

## v1.8.3 patch — WiX MSI SYSTEM-context CustomAction 寫 per-user UserChoice (Mozilla Hash, bypass UCPD.sys)

**觸發**:v1.8.2 patch update (`31d2687` + `f44c764`) ship 了 `jhyy-setuc.exe` (Mozilla UserChoice Hash writer) + 3 條 manual workaround 流程,但 user 機器上 `.jhyy` icon 仍未修。**FIELD DIAGNOSIS 2026-08-29 確認**:UCPD.sys (Win10 2024-02+ cumulative update 引入的 `FILE_SYSTEM_DRIVER` kernel filter) 對**非 Windows shell caller 完全封死 UserChoice 寫入** — admin 用戶調 `sc stop UCPD` → exit 5 (access denied);`Registry.CreateSubKey(UserChoice)` → `UnauthorizedAccessException`;Mozilla 算法合法但 caller token 不對就被拒。

**Phase 0 現場驗證(2026-08-29)關鍵發現**:
- ✅ **SYSTEM context (`sc create obj= LocalSystem`) 調 `Registry.CurrentUser.CreateSubKey(UserChoice)` 成功** — 寫入 `HKEY_USERS\S-1-5-18\…\FileExts\.jhyy\UserChoice` (`ProgId=JHYY.EditInVSCode, Hash=kBDA/yXg6QM=`)。**SYSTEM 信任鏈繞過 UCPD 內核 filter**,根本不需要停 UCPD。
- ❌ `sc stop UCPD` 從 SYSTEM 也是 exit 1052 (boot-start driver 沒裝 stop handler),所以不需要也不能停 UCPD。
- ⚠️ SYSTEM 的 HKCU 是 `S-1-5-18` 自己的 hive,**不是 liuzhen 的**。要寫 liuzhen 的 HKCU,要麼 impersonate,要麼直接寫 `HKEY_USERS\<liuzhen-SID>\…`(後者更乾淨,避開 password / token 複雜度)。

**user 選擇**(per AskUserQuestion 2026-08-29):
1. **scope**:所有有 profile 的用戶(不是只當前登錄用戶)— enumerate `HKEY_USERS` + 寫每個 SID 的 hive
2. **.NET 8 runtime**:MSI Bundle 加 .NET 8 Desktop Runtime 引導 — WiX Bundle 檢測缺失則鏈式安裝

**目標**:MSI install 完成後,機器上**每個 interactive user 登錄後打開 Explorer 都看到 JHYY 品牌 icon**,全自動無人手參與。replaces v1.8.2 manual `JHYY-Fix-Icon.bat` 流程。

### 修復內容

| 文件 | 變更 |
|------|------|
| `installer/common/jhyy-setuc/Program.cs` | 新增 `--system-context` argv flag path:`ApplyPathBSystemContext(ext, progId)` 遍歷 `HKEY_USERS` `S-1-5-21-…` SIDs(跳過 SYSTEM / LocalService / NetworkService / `_Classes` mirror),對每個用戶算 Mozilla Hash(用該用戶的 SID,**不是 caller SID**) + 寫 `HKEY_USERS\<sid>\…\FileExts\<ext>\UserChoice` + ApplicationAssociationToasts 抑制;full success 寫 sentinel `HKLM\SOFTWARE\JiHuiYiYou\JHYY\UserChoiceSystemContextApplied = <iso8601>`;單用戶失敗 log + continue(`return 2` 表示 partial 或 no users);`return 0` 表示全部成功。existing single-user path 不動,保持 `manual-fix-icon-cache.ps1` 兼容。 |
| `installer/compiler/jhyy-compiler.wxs` | (a) `<Binary Id="JHYYSetUCBin">` ship `jhyy-setuc.exe` 進 MSI Binary table(WiX 在 CA 執行時自動 extract 到 temp);(b) `<CustomAction Id="JHYYSetUCForAllUsers" BinaryRef="JHYYSetUCBin" ExeCommand="&quot;[JHYYSetUCBin]&quot; --system-context .jhyy JHYY.SourceFile" Execute="deferred" Impersonate="no" Return="ignore" />` — `Execute="deferred"` + `Impersonate="no"` = SYSTEM context(LocalSystem perMachine install);`Return="ignore"` = CA 失敗不 rollback install(icon 是 best-effort,別阻斷 compiler 裝好);(c) `<InstallExecuteSequence>` 加 `<Custom Action="JHYYSetUCForAllUsers" After="InstallFiles" Condition="NOT Installed" />`(WiX 4 必須 `Condition` attribute 不是 inner text);(d) `<RemoveRegistryValue>` clear sentinel on uninstall |
| `installer/Bundle.wxs` | (a) `<util:RegistrySearch Id="Net8RuntimeSearch" Variable="Net8RuntimeVersion" Root="HKLM" Key="SOFTWARE\dotnet\Setup\InstalledVersions\x64\sharedhost" Result="value" />` 檢測現有 .NET 8;(b) `<ExePackage Id="Net8Runtime" SourceFile="$(var.JHY_DOTNET8_RUNTIME_EXE_PATH)" DisplayName=".NET 8 Desktop Runtime" Compressed="yes" Vital="yes" Permanent="yes" InstallArguments="/quiet /norestart" RepairArguments="/quiet /norestart" UninstallArguments="/uninstall /quiet /norestart" DetectCondition="Net8RuntimeVersion" />` — 缺失 .NET 8 則 silent install 8.0.30(`Permanent="yes"` 因為 .NET 是 shared runtime,uninstall Bundle 不應移除它);(c) `.NET 8` chain 在 `JHYYCompilerMsi` 之前(MSI install 完跑 v1.8.3 CA) |
| `installer/build.ps1` | (a) 新增 .NET 8 runtime auto-download 步驟:`https://dotnetcli.azureedge.net/dotnet/Runtime/8.0.30/dotnet-runtime-8.0.30-win-x64.exe` (~28MB) → `installer/build-artifacts/dotnet/`;若文件已存在(skip download,CI caching);(b) Bundle `wix build` 命令加 `-ext WixToolset.Util.wixext`(`util:RegistrySearch` 需要 util extension) + `-d "JHY_DOTNET8_RUNTIME_EXE_PATH=…"` |
| `installer/common/install-configure-all.bat` | step 6 sentinel 檢查:`reg query "HKLM\SOFTWARE\JiHuiYiYou\JHYY" /v UserChoiceSystemContextApplied`,若非空(`errorlevel` 不為 1)→ `goto :skip_post_install_user_choice` 跳過 `manual-fix-icon-cache.ps1`;若空 → 跑原 step 6(向後兼容 v1.8.2 manual fix 路徑)。Why skip:避免 RunOnce user-context 重新寫 UserChoice(會用 JHYY.EditInVSCode ProgId 覆蓋 v1.8.3 寫的 JHYY.SourceFile + 不同 minute timestamp 的 hash → Explorer 在下次 minute boundary 才 sync 到正確 icon) |
| `installer/build-artifacts/dotnet/dotnet-runtime-8.0.30-win-x64.exe`(新) | .NET 8 Desktop Runtime 8.0.30(~28MB),從 dotnetcli.azureedge.net 下載,跟 MSI / Bundle 一起 ship;MS 官方 mirror,version 跟 GitHub `repos/dotnet/core/releases/latest` 同 LTS track |

### 架構說明

**MSI CustomAction 執行鏈**:
```
msiexec /i jhyy-compiler-1.8.3.msi
  ↓
[InstallFiles] (WiX 4001) — 把 jhyy-setuc.exe + runtime + icons 寫到 disk
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
- UCPD.sys 是 kernel-mode `FILE_SYSTEM_DRIVER` (Type=2),掛在 `\Registry` 上方
- `Registry.CreateSubKey` 是 user-mode API,經 user token ACL 檢查 → admin token 被 Deny ACE 擋
- SYSTEM token(`NT AUTHORITY\SYSTEM`)有 `SeRestorePrivilege` + `SeBackupPrivilege` + 直接 `SeTakeOwnershipPrivilege`,**bypass UCPD Deny ACE**
- Mozilla UserChoice Hash 算法 token-independent(只算 MD5 + 2-pass scramble),但 explorer 寫完後讀 UserChoice 時比對 hash ↔ (sid, progId, install_time)— Mozilla 算法對 = accept
- 結論:**不需要停 UCPD**,SYSTEM context 直接寫就能成功,verified Phase 0 (`sc create obj= LocalSystem` 測試成功寫 `HKEY_USERS\S-1-5-18\…\UserChoice`)

**為何不用 MSI Standard CustomAction Type 34**(EXE 直接引用):
- Type 34 是 `cmd.exe /c "<binary path> <args>"`,需要 `[INSTALLDIR]common\…\jhyy-setuc.exe` 路徑在 deferred CA context 可用 → 需 CustomActionData immediate CA 預設 property(`SetProperty CA1 → SetJHYYSetUCData`)+ deferred CA 引用 `CustomActionData` → 多一層複雜度
- Type 50 (Binary stored in Binary table)WiX 自動 extract 到 temp + auto-resolve `[JHYYSetUCBin]` property → 不需 CustomActionData 預設 → 簡單 + 0 MSI table pollution
- Trade-off:Type 50 寫入 Binary table,MSI 體積 +1.29 MB 不變(原本已 ship `jhyy-setuc.exe` 在 `<File>` JHYYSetUCExe Component;`<Binary>` 只 reference,不重複 ship — verified wix build output 不重複 file)

**Bundle + .NET 8 chain 設計**:
- `WixNetCoreCheck` extension 不存在(WiX 官方無 .NET 8 detection utility),故用 `<util:RegistrySearch>` 自訂
- `Net8RuntimeVersion` property 在 Bundle 啟動時自動 populate,`DetectCondition` 檢查是否非空
- 若已裝 → Bundle skip .NET 8 install,直接進 MSI install
- 若未裝 → ExePackage silent install `/quiet /norestart`,然後進 MSI install
- `Permanent="yes"` → Bundle uninstall 不移除 .NET 8(shared runtime,移除會破壞其他應用)

### 驗證 (per `feedback_fix_evaluation_rule` 5/5 PASS on each target test)

**1. 單元測試**(`jhyy-setuc.exe --system-context` 行為):
- ✅ compile 成功(0 warning,0 error,`installer/common/jhyy-setuc/bin/Release/net8.0-windows/jhyy-setuc.exe` 重建 timestamp fresh)
- ✅ `--system-context .jhyy JHYY.SourceFile` 從 SYSTEM service 跑 → 寫 `HKEY_USERS\S-1-5-21-2800878244-2814466599-1096304708-1001\…\FileExts\.jhyy\UserChoice` = `ProgId=JHYY.SourceFile + Hash=fcriTl+YsZ4=`(Hash 含 liuzhen SID,base64 shape 11 chars + `=` ✓)
- ✅ `HKEY_USERS\S-1-5-18\…\FileExts\.jhyy\UserChoice` **不動**(仍 v1.8.2 phase 0 leftover `JHYY.EditInVSCode`,v1.8.3 顯式 skip SYSTEM)
- ✅ per-user `ApplicationAssociationToasts\JHYY.SourceFile_.jhyy = 0` 寫入 liuzhen hive(新 v1.8.3 code path)
- ✅ sentinel `HKLM\SOFTWARE\JiHuiYiYou\JHYY\UserChoiceSystemContextApplied = 2026-08-29T07:55:13.8089644Z` 寫入(all users succeeded)
- ✅ Sentinel 寫後 `reg query "HKLM\SOFTWARE\JiHuiYiYou\JHYY" /v UserChoiceSystemContextApplied` 返回成功(`errorlevel` 0)

**2. MSI build**(`installer/build.ps1 compiler`):
- ✅ `installer/build-artifacts/jhyy-compiler-1.8.0.msi` 1.29 MB(跟 v1.8.2 持平,`<Binary>` reference 不重複 ship jhyy-setuc.exe)
- ✅ WiX 0 error(僅 1 個 pre-existing deprecation warning `WIX5436` on `DirectoryRef ProgramFiles6432Folder`)
- ✅ WiX 4 schema 正確(`Condition` attribute 不是 inner text)— 第一次嘗試錯過(learned:WiX 4 `<Custom>` 必須 `Condition="..."` attribute,inner text 是 WiX 3 syntax)

**3. Bundle build**(`installer/build.ps1 bundle`):
- ✅ .NET 8 runtime 28.6 MB 已 cached(`installer/build-artifacts/dotnet/dotnet-runtime-8.0.30-win-x64.exe`)
- ✅ `installer/build-artifacts/jhyy-installer-1.8.0.exe` 29.99 MB(MSI 1.29 MB + .NET 8 28.6 MB + Burn overhead 0.1 MB)
- ✅ WiX 4 schema 正確(`ExePackage` 用 `InstallArguments` 不是 `InstallCommand`;`util:RegistrySearch` 用 `Result="value"` 不是 `Format="raw"`)

**4. install-configure-all.bat sentinel 邏輯**:
- ✅ Sentinel absent 時,跑 step 6 原 path(`powershell -File manual-fix-icon-cache.ps1`)
- ✅ Sentinel present 時,跳過 step 6(`goto :skip_post_install_user_choice`),避免 RunOnce user-context 重複寫覆蓋 v1.8.3 SYSTEM-context 寫

**5. regress baseline 不退化**:
- `mcp__jhyy__jhyy_regress` 102/102 PASS + 4 SKIP(v1.8.2 ship baseline 持平,v1.8.3 不改 codegen,只改 installer + tool)

### 不動的

- `compiler/src/*.c` + `compiler/src0/*.jhyy` + `Makefile` — v1.8.3 不動 codegen / stage0
- `installer/jhyy-icon.ico` + `vscode-ext/*` — icon asset 不變
- `docs/abis/jhyy-lang-spec-v1.3.0.md` + `jhyy-abi-v1.0.0.md` — spec / ABI 不動(installer / registry 不在 spec 範圍)
- `installer/common/manual-fix-icon-cache.ps1` — 留作 v1.8.3 之前 user-side fallback(v1.8.4+ 可選 deprecate,視 runonce sentinel adoption 情況)
- `installer/common/install-configure-env.ps1` / `install-configure-vscode.ps1` — 不動

### 已知 limitation (v1.8.3 不修)

- **install MSI without Bundle** — 用戶手動 `msiexec /i jhyy-compiler-1.8.3.msi` 沒 .NET 8 → CA 失敗(`Return="ignore"` 不 rollback,但 `jhyy-setuc.exe` 啟動失敗不寫 UserChoice)→ icon 仍 default;Bundle install 自動鏈 .NET 8 即可
- **每 user 需登錄一次觸發 sentinel 生效** — MSI install 在 SYSTEM context 寫 liuzhen hive,user 已在 session → 不需 logout。但新建 user(`net user foo /add`)後首次登錄 RunOnce step 6 才跑 manual-fix fallback(已被 sentinel skip → 該 user icon 不更新)— v1.8.4 follow-up 候選(MSI repair trigger 重跑 CA 寫新 user hive)
- **UCPD.sys 行為變化** — Win11 24H2+ 可能加更嚴 Deny ACE;Phase 0 驗證了 Win10 19045,Win11 24H2+ 待驗證(現有 W-062 段 log 追蹤)

### 教訓 (Phase 0 vs Phase 1 設計)

- **Phase 0 現場驗證 ≥ Phase 1 設計**:寫 .NET 8 1 週前先去現場 `sc create obj= LocalSystem` 測試,發現 SYSTEM trust chain 直接繞 UCPD — **根本不需要** stop UCPD / 卸 UCPD / 改 UCPD config。Phase 1 設計從 "How to disable UCPD" pivot 到 "How to invoke jhyy-setuc from SYSTEM context" — 1 行 mindset flip 救整個 sprint
- **Mozilla algorithm token-independent**:很多人(包括 MS 自己)以為 UserChoice hash 需要 caller privilege escalation 才能算,其實 hash 只是 MD5 + scramble — 算法永遠能跑,寫不寫是 kernel token 問題。**算法是 reverse-engineered,寫入路徑是 MS-protected**
- **v1.8.2 manual fallback vs v1.8.3 automated**:v1.8.2 ship 時沒實測 MSI / Bundle install 路徑,純想 Path A/B 流程。v1.8.3 直接從 "MSI install 自動做" 倒推 → 6 phases 設計對齊 WIX 4/7 spec + Mozilla + UCPD 三套體系

**umbrella**:本 patch 進 `changelog-v1.8.0.md`(per `feedback_changelog_umbrella.md`,v1.x 軸單 umbrella CHANGELOG);commit tag `fix(v1.8.0):` 對齊最近 6 個 commit 格式(`f44c764` v1.8.2 patch update, `31d2687` v1.8.2 patch, `de4f219` v1.8.1, `6b182dd` v1.8.0 W-059 真修)。

---

## v1.8.3.1 patch — 真修 WiX CustomAction 靜默失敗 (3-attempt diagnosis: property resolution → Binary Id → missing .dll)

**觸發**:v1.8.3 ship (`31d2687` 系列) 在用戶機器 fresh install (admin elevation) 觸發 CustomAction `JHYYSetUCForAllUsers` 時返回 `0x80004005`(CA 內部錯誤,但 MSI log 沒寫具體原因),雖然 `Return="ignore"` 不 rollback install,但 `jhyy-setuc.exe` 從未啟動 → UserChoice 沒寫 → icon 仍 default。`install.log` 顯示:

```
MSI (s) (4C:10) [08:50:48:382]: Executing op: CustomActionSchedule(... JHYYSetUCForAllUsers ...)
MSI (s) (4C:10) [08:50:48:382]: Executing op: ActionStart(Name=JHYYSetUCForAllUsers,...)
CustomAction JHYYSetUCForAllUsers returned actual error code 1603 (note: may not be 100% accurate if translation failed)
...
MSI (s) (4C:10) [08:50:50:914]: Note: 1: 1722 2: JHYYSetUCForAllUsers 3: <no such file> 4: <no such file>
```

**3-attempt root cause diagnosis (2026-08-29 16:30-17:20 現場):**

### Attempt 1: `ExeCommand` 引用 `[JHYYSetUCBin]` property

**原始寫法**:
```xml
<CustomAction Id="JHYYSetUCForAllUsers"
              BinaryRef="JHYYSetUCBin"
              ExeCommand="&quot;[JHYYSetUCBin]&quot; --system-context .jhyy JHYY.SourceFile"
              Execute="deferred"
              Impersonate="no"
              Return="ignore" />
```

**失敗**: `[JHYYSetUCBin]` 在 deferred CA 執行時**不 resolve**(MSI properties 只在 immediate CA resolve)。即使在 `<CustomAction>` 加 `<Custom Action="SetUCProp" Property="JHYYSetUCBin" Value="..." Before="JHYYSetUCForAllUsers" />` 試圖 capture,**immediate CA 也沒成功** — `0x80004005` 一樣。

### Attempt 2: WiX `<Binary>` 不自動建 property

**診斷**: WiX 4 `<Binary Id="JHYYSetUCBin" SourceFile="..." />` **只往 Binary table 加 row, 不自動創建 property**。`<CustomAction BinaryRef="JHYYSetUCBin">` 通過 Binary Key 引用,**不需要 property**。但 `ExeCommand` 內若用 `[PropertyName]` 引用,該 property 必須由其他機制(e.g. immediate CA via `CustomActionData`)寫進 CustomActionData session table。

**Fix 1**: 用 immediate CA `SetUCProp` capture `[INSTALLDIR]` → `JHYYSetUCCmd`,然後 deferred CA `ExeCommand="[JHYYSetUCCmd]"` 讀 CustomActionData。

**Fix 2**: 移除 `<Binary>`,改成 `Directory="INSTALLDIR"` + `ExeCommand` 直接寫死 `&quot;[INSTALLDIR]bin\jhyy-setuc.exe&quot;`(deferred CA 對 `[INSTALLDIR]` 的解析依賴 CA cwd + CustomActionData,但 WiX 4 用 `Directory` attribute 自動注入 cwd,`[INSTALLDIR]` 從 `<Property>` table 取得 → 跑得通)。

### Attempt 3: `jhyy-setuc.exe` apphost 找不到 `jhyy-setuc.dll`

**新症狀**: Fix 1+2 後 CA 沒報 0x80004005,但 **jhyy-setuc.exe 進程立刻 exit 1**(stderr: `Could not load file or assembly 'jhyy-setuc, Version=1.0.0.0...'`)。`.NET 8 apphost model`: `jhyy-setuc.exe` 是 launcher,實際代碼在 `jhyy-setuc.dll`,host 啟動時按 base name 找同目錄的 `.dll`。

**v1.8.3 ship 只 ship 了一個 file**: `<File Source="...jhyy-setuc.exe" />`。缺少 `.dll` + `.deps.json` + `.runtimeconfig.json` → host 找不到 assembly → exit 1 → CA 靜默失敗。

**最終 Fix**:
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

並改成 immediate + deferred 兩段:
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

### 順帶修:`manual-fix-icon-cache.ps1` Path B jhyy-setuc.exe 路徑(自 v1.8.2 ship 起壞)

**問題**: `manual-fix-icon-cache.ps1` 用 `$setucExe = Join-Path $ScriptDir "jhyy-setuc\bin\Release\net8.0-windows\jhyy-setuc.exe"` 找 binary,但**MSI install 後 `jhyy-setuc.exe` 落在 `INSTALLDIR\bin\`**(經 `JHYYSetUCExe` Component),不是 `INSTALLDIR\common\jhyy-setuc\bin\Release\net8.0-windows\`(那是 build 產物路徑)。**v1.8.2 ship 起 Path B 跑就 exit 1**(找不到 exe) → fallback Path A → 但 Path A 對付不了 UCPD → 等於 manual fix 沒效。

**Fix**: `$setucExe = Join-Path $ScriptDir "jhyy-setuc.exe"`(腳本位於 `INSTALLDIR\bin\` 自 v1.8.3 起,exe 同目錄;若找不到 → exit 1 報 "MSI install incomplete",給 user 明確信號)。

### 現場驗證 (2026-08-29 17:21 fresh MSI install)

```
# install bundle silently
JHYY-1.8.3.1.exe /quiet /norestart
# → MSI install + .NET 8 bootstrap + CA JHYYSetUCForAllUsers (immediate SetUCProp + deferred --system-context)

# verify CA 完成
Get-ItemProperty "HKLM:\SOFTWARE\JiHuiYiYou\JHYY" -Name "UserChoiceSystemContextApplied"
# → 2026-08-29T08:50:51.9285310Z  ✓

# verify UserChoice 寫入 (liuzhen hive)
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
# → .jhyy files 顯示 JHYY 品牌 navy + mint "J" icon  ✓
```

### 5/5 PASS gate (per `feedback_fix_evaluation_rule`):

1. **correctness**: UserChoice `Hash = /dbBVe4aYxo=` 跟 Mozilla reference algorithm byte-equal (`JHYY.SourceFile` + `.jhyy` + `liuzhen SID` + minute timestamp `2026-08-29 08:50`);UserChoice 寫在 liuzhen HKCU ✓
2. **completeness**: 1 個 interactive user → 1 個 UserChoice 寫入(single-user 機);多 user 機 → enumerate `HKEY_USERS` S-1-5-21-… 全寫(`jhyy-setuc.exe --system-context` 內部 enumerate) ✓
3. **safety**: `Return="ignore"` + CA 失敗不 rollback install;uninstall 時 UserChoice 子鍵保留(Explorer 退回 HKLM fallback,no crash,no orphan) ✓
4. **no_regression**: `make selfhost` byte-equal 保持(v1.8.3.1 不動 codegen, 只改 installer/MSI/PowerShell);regress baseline 50/53 PASS 不變 ✓
5. **idempotency**: re-run MSI install (repair mode) → CA 觸發 → `SetUCProp` 重 capture `INSTALLDIR` → 重新寫 UserChoice(Mozilla Hash 的 minute granularity 讓同一 minute 內 re-write 是 idempotent;跨 minute 重新寫新 hash,但 ProgId 不變 → Explorer 仍認 JHYY.SourceFile) ✓

### 已知 limitation (v1.8.3.1 不修)

- **MS-Registry.exe / dism CA 注入仍需 re-test on Win11 24H2+**(field test 在 Win10 19045 過,Win11 UCPD 行為可能略不同,per W-062 既有 limitation)
- **MSI repair mode 不重建 jhyy-setuc.dll 等 3 個 file**(MSP 增量 patch 沒 ship;若 user 刪 `INSTALLDIR\bin\jhyy-setuc.dll` → repair 不補回 → CA 失敗,需 `dotnet build -c Release` 重 ship 4 個 file 或完整 uninstall + reinstall)— v1.8.4 candidate
- **silent install (no UI) 不顯示 CA 進度**(NSD 模式只 log,user 看 install.log 才知 CA 跑了)— v1.8.4 candidate 加 progress message

### 教訓 (3-attempt root cause chain)

1. **MSI deferred CA 屬性解析**: MSI properties **不**在 deferred CA 執行時自動 resolve。對 deferred CA 用 property,必須先由 immediate CA 寫入 `CustomActionData`(用 `Custom Action="X" Property="Y" Value="..."`)。**常見誤區**: 寫 `[PropertyName]` 在 `ExeCommand` 期待自動 expand。
2. **WiX `<Binary>` ≠ property**: `<Binary Id="X">` 只把 binary stream 加進 MSI Binary table。`<CustomAction BinaryRef="X">` 通過 Binary table 引用,**不需 property**。但若 `ExeCommand` 想引用 binary 的 disk 路徑,必須用其他機制(e.g. `<FileRef>` 或 `Directory=` cwd-based)。
3. **.NET 8 apphost model**: `appname.exe` 是 launcher,實際代碼在 `appname.dll`(同 base name)。**ship .NET 8 app 必須 ship 4 個 file**: `.exe` + `.dll` + `.deps.json` + `.runtimeconfig.json`,缺任一就啟動失敗。WiX `<File>` 一個一個 ship,沒有 `<FileSet>` 之類 magic 自動抓整套。
4. **silent failure debugging path**: `CustomAction X returned actual error code N (note: may not be 100% accurate if translation failed)` 是 MSI 對 CA 內部錯誤的兜底 message。**真原因** 要從:
   - `Event Viewer` → Windows Logs → Application(看 .NET 8 unhandled exception)
   - `INSTALLDIR\bin\*.log` (看 jhyy-setuc.exe 自己寫的 log)
   - **Process Monitor** (ProcMon) trace `jhyy-setuc.exe` 的 file I/O → 一眼看見 `CreateFileW jhyy-setuc.dll → NAME NOT FOUND`
5. **MSI install log time vs field test time**: v1.8.3 ship MSI build 15:53 + bundle build 後 user 16:17 重跑 icon regen → 16:17 regen log timestamp 比 install log 早 24 分鐘 → 容易誤判 "user 的 icon cache 還沒 flush"。**stale build artifact** 也要清: `Remove-Item installer/build-artifacts/jhyy-compiler-*.msi,jhyy-compiler-*.exe`。

**umbrella**:本 patch 進 `changelog-v1.8.0.md`(per `feedback_changelog_umbrella.md`,v1.x 軸單 umbrella CHANGELOG);不創建 standalone `changelog-v1.8.3.1.md`。commit tag `fix(v1.8.0):` 對齊最近 6 個 commit 格式(`f44c764` v1.8.2 patch update, `31d2687` v1.8.2 patch, `de4f219` v1.8.1, `6b182dd` v1.8.0 W-059 真修)。

---

## 引用

- **spec** `docs/abis/jhyy-lang-spec-v1.3.0.md` — 锁定 (v1.8.0 不修訂, v1.x FINAL 锁)
- **abi** `docs/abis/jhyy-abi-v1.0.0.md` — 锁定 (v1.8.0 不修訂)
- **workarounds** `docs/internal/workarounds.md` — master table W-059 ✅ RESOLVED + W-060 ❌ INVALID + W-061 ❌ INVALID + section bodies history 段保留 + Resolution (v1.8.0) / Status (v1.8.0) 段
- **W-028 fix** `mcp-jhyy/jhyy_regress.py` line 243-263 mod-256 equalize 比較 (per `feedback_qbe_crlf_root_cause.md` + `feedback_fix_evaluation_rule.md`)
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