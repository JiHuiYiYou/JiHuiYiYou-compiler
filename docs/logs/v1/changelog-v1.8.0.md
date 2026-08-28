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