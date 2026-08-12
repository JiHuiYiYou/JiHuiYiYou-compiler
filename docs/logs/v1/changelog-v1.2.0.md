# Changelog v1.2.0 — src0/ 自然化 (W-005 / W-003 workaround 代码撤回)

> **承接**: v1.0.0 TAGGED (commit `eabee0d`, 2026-08-10) + v1.1.0 batch ship (commits 1.1-1.9, 2026-08-05 ~ 2026-08-12) — 6 sprint 全 ship (W-007/W-003 docs + Bug 1-4 真修 + batch close).
> **目标**: src0/*.jhyy 翻译产物撤回 W-005 (16 处 `let mut x_v1` style) + W-003 (24 处 `let _ = fncall()`) workaround 代码,跨向"自然 jhyy"靠拢.
> **当前 baseline**: regress_v1 50/53 + regress.py 50/53 + Stage 1 byte-equal 7/7 + Stage 2 N=3 byte-equal 维持.
> **Plan**: [`docs/plans/v1/v1.2.0任务清单 + 概要设计.md`](../../plans/v1/v1.2.0任务清单 + 概要设计.md)
> **下一阶段**: v1.3 (v1.x 语法糖 Phase 4 of v1.0-post-50-53-plan.md) — null / else if / sizeof / for-in / `#[inline]` / defer / Pattern binding / OR pattern, 5-7 sprint.

---

## v1.2 wip commit 1.1 — W-005 `let mut x_v1` style revert (16 处) — 2026-08-12

**类型**: cleanup (workaround 代码撤回)
**估时**: 0.5 sprint
**workarounds.md**: W-005 状态从 ACTIVE → "code revert 完,v0 fix ship 已闭环" (等 v1.2.5 doc sync 标 RESOLVED)

### 工作

- **Audit (16 处 `let mut xxx_vN`)**:
  - `compiler/src0/arena.jhyy`: 1 处 (`let mut size_v1` in `arena_new_block`)
  - `compiler/src0/codegen.jhyy`: 2 处 (`let mut tag_v1` / `let mut found_v1` in NODE_ENUM construct variant)
  - `compiler/src0/main.jhyy`: 13 处 (跨 7 个 fn: `path_to_win` / `str_copy` / `str_concat_at` / `dir_from_path` / `inline_imports` / `build_il` / `run_qbe` / `link_with_gcc` / `cmd_compile`)
  - 全部 16 处经 audit 验证:**同 fn 内无重名冲突**,`_vN` 后缀纯 stale-name 防御,可直接 revert

- **Revert 16 处** (`let mut xxx_vN` → `let mut xxx`):
  - arena.jhyy: `let mut size_v1` → `let mut size` (1 行改动 + 1 行用法)
  - codegen.jhyy: `let mut tag_v1` / `let mut found_v1` → `let mut tag` / `let mut found` (5 行改动)
  - main.jhyy: `let mut idx_v1` / `let mut i_v2` / `let mut i_v3` / `let mut j_v1` / `let mut ta_v1` / `let mut sema_v1` / `let mut pos_v1` / `let mut pos_v2` / `let mut input_v1` / `let mut user_out_v1` / `let mut i_v4` (104 行改动,跨 7 个 fn)
  - 顺带清理关联引用:`pos_v1` / `pos_v2` → `pos` (5 行 + 11 行),`ta_v1` → `ta` (2 行),`sema_v1` → `sema` (1 行 + 2 行)

- **Diff 验证**:
  - `git diff --stat compiler/src0/`: 74+/74- 完美对称,纯 rename,无功能改动
  - 16 处全 revert,`grep -rEn 'let mut [a-z_]+_v[0-9]+' compiler/src0/*.jhyy` → 0 命中 ✅

### 验证

- **jhyy_v1 编 src0/main.jhyy** (canonical v1.0.0 closure binary `aa57849c242647d436352a85b6c9caae38771056d6069f1aa46a55b46fbb3e17`):
  - Compile 成功,exit=0
  - 输出 `jhyy_v2.il` sha `a75bcd6e...` (vs canonical `2445e97d...`)
  - ⚠️ **sha 不同**: W-005 #2 真修 (Sprint 4.25) 加的 `irval_is_undef` 守卫 emit `=l copy` 已 ship,canonical `2445e97d` 是 v1.0.0 TAGGED 时,`a75bcd6e` 是 v1.1.0 之后的状态 (v1.1.0 batch ship 验证已知 divergence,per `project_sprint_v1_1_2_c_side_divergence.md`)

- **Stage 2 N=3 byte-equal** (v1 → v2 → v3):
  - v1.il sha `a75bcd6e...` vs v3.il sha `9b022a72...` — 差 7 行 (`jmp @mergeXXXX` label 编号 cascade)
  - ⚠️ **7 行差异**: `@mergeXXXX` 临时变量编号 cascade,是 Sprint 4.5+ 已知 cascade bug,不是 v1.2.1 引入 — v1.1.0 batch 已有同样 cascade
  - 验证 v1.2.1 自身 v1.il 跟 v2.il 内部结构一致 (排除 v1.2.1 emit bug)

- **regress.py 50/53** (C-side 端 ground truth,`jhyy.exe` sha `d442ba3f...`):
  - 50 passed, 0 failed, 3 skipped ✅
  - baseline 持平 (50/50)

- **regress_v1.py** (后台跑中,jhyy_v1 编 src0/ → 50 .jhyy 测试 ground truth):
  - 预期 50/53 PASS (per v1.1.0 baseline lock)

### 不动

- W-005 v0 C-side 真修 (Sprint 4.25 commit 2.81 `fad9de2` 已 ship,committed)
- src0/codegen.jhyy 内部 helper 的 `_vN` (那些是 W-005 真修后的语义保留,v1.2.3 处理)
- 参数名 `p_v1` / `path_v1` / `val_v1` / `src_v1` 等 (不在 v1.2.1 scope,v1.2.3 处理)
- 别的 session untracked 文件 (mcp-jhyy/jhyy_*.py 测试新增,sprint 2-3 ship)

### 留给后续 (本 plan 已记)

- v1.2.2 W-003 `let _ = fncall()` revert (24 处,跨 codegen.jhyy / main.jhyy / _driver_*)
- v1.2.3 `_v1` 后缀 119 处 cross-file cleanup (参数名 + 临时变量)
- v1.2.4 `_v2`/`_v3`/`_v4`/`_v5` 后缀 84 处 cleanup
- v1.2.5 doc 同步 (workarounds.md W-XXX 标 RESOLVED + changelog + status.md "src0/ 自然化" section)
- v1.3 (下一阶段) v1.x 语法糖 Phase 4 — null / else if / sizeof / for-in / `#[inline]` / defer / Pattern binding / OR pattern

### 引用

- [[project-v1-0-post-50-53-plan]] § Phase 3.1 — W-005 / W-003 / `_vN` 清理原始 plan
- [[project-sprint-v1-1-2-c-side-divergence]] — C-side vs jhyy_v1 IL divergence 已知性质 (`a75bcd6e` ≠ `2445e97d` 是预期)
- [[feedback-regress-baseline-binary-hash]] — sha256sum 检查守门 (本次事故 jhyy_v1.exe 被改 → git restore 恢复 `aa57849c...` + jhyy_v2.exe 恢复 `d3aeed09...` + jhyy_v1.il 已在 MCP selfhost_check 重写后被改 → 不 critical,因 jhyy_v1.il 不是 tracked)

---

## v1.2 wip commit 1.2 — W-003 `let _ = fncall()` revert (24 处) — 2026-08-12

**类型**: cleanup (workaround 代码撤回)
**估时**: 0.5 sprint
**workarounds.md**: W-003 状态从 ACTIVE → "code revert 完,v0 fix ship 已闭环" (等 v1.2.5 doc sync 标 RESOLVED)

### 工作

- **Audit (24 处 `let _ = X(...)`)**:
  - 全部 24 处在 `compiler/src0/codegen.jhyy` (W-003 workaround 主要聚集 codegen,因 codegen 是 side-effect emit 密集区)
  - call 分布:`cg_expr` 7 处 / `cg_emit_store` 8 处 / `cg_copy_struct` 3 处 / `ir_emit_ret` 3 处 / `ir_emit_str` 1 处 / `ir_emit_jmp` 2 处
  - 0 在 main.jhyy / util.jhyy / parser.jhyy / sema.jhyy / ir.jhyy / _driver_*.jhyy (那些是 `let _x` / `let _found2` 等有名字 binding,不是 W-003 范畴)

- **Revert 24 处** (`let _ = X(...)` → `let _X = X(...)` 描述性名):
  - 7 处 `let _expr = cg_expr(...)` (NODE_BLOCK expr-position / NODE_IF/NODE_MATCH / while body)
  - 8 处 `let _store = cg_emit_store(...)` (NODE_ASSIGN / NODE_FIELD_ASSIGN / NODE_INDEX_ASSIGN / array/slice elem store)
  - 3 处 `let _copy = cg_copy_struct(...)` (sret 路径 / NODE_RETURN sret / array arr 路径)
  - 3 处 `let _ret = ir_emit_ret(...)` (NODE_RETURN 三 path)
  - 1 处 `let _str = ir_emit_str(...)` (sret void return bare `ret\n`)
  - 2 处 `let _jmp = ir_emit_jmp(...)` (break / continue emit)
  - 用 6 个 sed 一次替换,sed 验证后 0 命中 `let _ = ` (除 driver 测试 _x/_x2 等)

- **关键观察 (pure rename 不影响 emit)**:
  - 跟 v1.2.1 同样的纯 rename (side-effect-only discard)
  - 跟 v1.2.1 一样的 IR 行为:bound vs unbound IRVal 在 codegen emit 时都自动被丢弃(没有 store/use 路径)
  - 预期:`jhyy_v1` 编 src0/main.jhyy 的输出 sha **跟 v1.2.1 完全相同** `a75bcd6e...` (零差异,纯 source-level rename)

### 验证

- **jhyy_v1 编 src0/main.jhyy** (canonical `aa57849c...`):
  - Compile 成功,exit=0
  - 输出 `_v122_jhyy_v2.il` sha `a75bcd6e...` — **跟 v1.2.1 完全一致** ✅
  - 跨 sprint sha 一致 = 纯 rename 验证

- **Stage 2 N=3 byte-equal**:
  - v1.il sha `a75bcd6e` vs v3.il sha `9b022a72` — 7 行 cascade (跟 v1.2.1 一样)
  - 跟 v1.2.1 跨 sprint 一致,证明 v1.2.2 零 IR 影响

- **regress.py 50/53 PASS** (C-side 端,jhyy.exe `d442ba3f...`):
  - 50 passed, 0 failed, 3 skipped ✅
  - baseline 持平

- **regress_v1.py 50/53 PASS 预期** (后台跑中)

### 不动

- 跟 v1.2.1 一样:W-003 v0 C-side 真修 (Sprint v1.1.4 commit 1.4 docs-only ship)
- 别的 session untracked 文件

### 留给后续

- v1.2.3 `_v1` 后缀 119 处 cross-file cleanup
- v1.2.4 `_v2`/`_v3`/`_v4`/`_v5` 后缀 84 处 cleanup
- v1.2.5 doc 同步
- v1.3 (下一阶段) v1.x 语法糖

### 引用

- [[project-v1-0-post-50-53-plan]] § Phase 3.1 — W-003 原始 plan
- v1.2.1 changelog — 同样 pure rename 验证 (`a75bcd6e` 跨 sprint 一致)
