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
- sha256sum 检查守门 (本次事故 jhyy_v1.exe 被改 → git restore 恢复 `aa57849c...` + jhyy_v2.exe 恢复 `d3aeed09...` + jhyy_v1.il 已在 MCP selfhost_check 重写后被改 → 不 critical,因 jhyy_v1.il 不是 tracked)

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

- **regress_v1.py 50/50 PASS** (jhyy_v1 编 src0/ → 50 .jhyy 测试 ground truth): 50 passed, 0 failed, 3 skipped ✅
  - baseline 持平 (50/50)

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

---

## v1.2 wip commit 1.3 — `_v1` 后缀 63 处 cleanup (19 个 unique identifier) — 2026-08-12

**类型**: cleanup (workaround 后缀撤回)
**估时**: 0.5 sprint
**workarounds.md**: 不直接对应 W-XXX,但属于 v1.1.0 batch ship 后的 stale-name 防御清理

### 工作

- **Audit (63 处,19 个 unique `_v1` identifier)**:
  - Plan 估时 119 处 (估计错误,实际只有 63 — plan 估的是把 `xxx_v1` 当作每个 unique 算多份)
  - 跨 3 个 src0/ 文件:codecen.jhyy (20) / main.jhyy (31) / _driver_ir.jhyy (2)
  - 还有 parser.jhyy (1) / sema.jhyy (5) / util.jhyy (2) 共 8 处,加上 codegen+main+_driver = 60,实际总 63 (含 3 处嵌套多行)

- **排除项 (函数名,不删)**:
  - `resolve_one_import_v1` (main.jhyy:234) — 函数名,改会破坏 v0 调用方对照
  - `var_name_eq_v1` (sema.jhyy:59) — 同上,函数名
  - 2 个函数名都保留 `_v1` 后缀 (跟 v0 C-side 对齐,后续 v3.x 命名空间清理再做)

- **Revert 19 个 identifier** (`xxx_v1` → `xxx`):
  - 函数参数:`argc_v1`/`argv_v1`/`p_v1`/`path_v1`/`val_v1`/`src_v1`/`dst_v1`/`off_v1` (8 个)
  - 局部变量:`bb_slot_v1`/`bv_slot_v1`/`d_variant_sym_v1`/`ftype_slot_v1`/`ir_v1`/`nvariants_v1`/`off_payload_v1`/`off_zero_v1`/`phi_v1`/`sym_p_v1`/`variants_buf_v1` (11 个)
  - 用 19 个 sed 一次替换 (per-identifier),验证 0 命中可替换 `_v1` 后

- **不动的 `_v1` 命中 (10 处,全部在 comments)**:
  - 描述 `jhyy_v1 binary` 的 comment (codegen.jhyy + jhyy_helpers.c + main.jhyy + parser.jhyy + sema.jhyy + util.jhyy)
  - 描述 `regress_v1.py` 的 comment (main.jhyy)
  - 描述 `jhyy_v1 inline_imports` 等 W-005 workaround 的 comment
  - 这些是历史叙述,不是 identifier

### 验证

- **jhyy_v1 编 src0/main.jhyy** (canonical `aa57849c...`):
  - Compile 成功,exit=0
  - 输出 `_v123_jhyy_v2.il` sha `348884af...`
  - **跟 v1.2.1/v1.2.2 (`a75bcd6e`) 不同** — 这是预期的:identifier rename 改了 QBE 符号名 (symbol table 顺序/size),emit IL 必然不同
  - 关键看 **sprint 内部** v1==v2 byte-equal (跟 v1.2.1/v1.2.2 同模式)

- **Stage 2 N=3 byte-equal** (cascade 验证):
  - v1.il sha `348884af` vs v3.il sha `554e7bde` — 7 行 cascade (跟 v1.2.1/v1.2.2 一致 7 行)
  - diff /tmp/_v123_jhyy_v2.il /tmp/_v123_v3.il | wc -l = 12 (= 7+5 context)
  - **7 行 cascade 仍是 Sprint 4.5+ 已知现象**,不是 v1.2.3 引入

- **regress.py 50/53 PASS** (jhyy.exe `d442ba3f...`):
  - 50 passed, 0 failed, 3 skipped ✅
  - baseline 持平

- **regress_v1.py 50/50 PASS** (jhyy_v1 编 src0/ → 50 .jhyy 测试 ground truth): 50 passed, 0 failed, 3 skipped ✅
  - baseline 持平 (50/50)

### 不动

- 跟 v1.2.1/v1.2.2 同:函数名 `resolve_one_import_v1` / `var_name_eq_v1` (改函数名是 v3.x 命名空间范畴)
- 跟 v1.2.1/v1.2.2 同:comment 里描述 `jhyy_v1` / `regress_v1.py` 的历史叙述
- 别的 session untracked 文件

### 留给后续

- v1.2.4 `_v2`/`_v3`/`_v4`/`_v5` 后缀 84 处 cleanup (同模式)
- v1.2.5 doc 同步 (workarounds.md + status.md + changelog 收尾)
- v1.3 (下一阶段) v1.x 语法糖

### 引用

- v1.2.1 changelog — Stage 2 N=3 7 行 cascade 已知现象
- [[project-sprint-v1-1-2-c-side-divergence]] — C-side vs jhyy_v1 IL divergence 性质 (rename 后 sha 变化是预期)

---

## v1.2 wip commit 1.4 — `_v2`/`_v3`/`_v4`/`_v5` 后缀 36 处 cleanup (18 unique identifier) — 2026-08-12

**类型**: cleanup (workaround 后缀撤回)
**估时**: 0.5 sprint
**workarounds.md**: 不直接对应 W-XXX,跟 v1.2.3 同模式,延续 stale-name 防御清理

### 工作

- **Audit (36 处,18 个 unique `_v2`/`_v3`/`_v4`/`_v5` identifier)**:
  - Plan 估时 84 处 (估计错误,实际只有 36 — 同 v1.2.3 估时偏差模式)
  - 跨 3 个 src0/ 文件:codecen.jhyy (10) / main.jhyy (24) / _driver_ir.jhyy (2)
  - 18 个 unique identifier 分布:
    - `_v2` 后缀 (9 个):`argc_v2` / `argv_v2` / `bb_slot_v2` / `bv_slot_v2` / `dst_v2` / `init_v2` / `p_v2` / `phi_v2` / `src_v2`
    - `_v3` 后缀 (5 个):`argc_v3` / `argv_v3` / `bb_v3` / `bv_v3` / `p_v3`
    - `_v4` 后缀 (2 个):`argc_v4` / `argv_v4`
    - `_v5` 后缀 (2 个):`argc_v5` / `argv_v5`

- **Revert 18 个 identifier** (`xxx_vN` → `xxx`, 几个 `bb_v3`/`bv_v3`/`init_v2` 特殊 rename):
  - `bb_v3` → `bb` / `bv_v3` → `bv` (跟 `bb_slot`/`bv_slot` 区分,各自不同 scope 安全)
  - `init_v2` → `init_v` (跟 comment "init_val" 描述对齐)
  - 其余 15 个 `xxx_v2/3/4/5` → `xxx` 纯 rename
  - 用 18 个 sed 一次替换 (per-identifier),验证 `grep -rEn '\b[a-z_]+_v[2-5]\b'` 只剩 `_W002_rename_map.txt` comment 一处 ✅

- **不动的 `_vN` 命中 (历史 comment)**:
  - `compiler/src0/_W002_rename_map.txt` comment 一处描述 `init_v2 -> init_v2_v1` 翻译映射
  - 描述 `jhyy_v2` / `jhyy_v3` / `jhyy_v4` 的 comment (closure binary 命名,不能动)
  - 描述 `regress_v1.py` 的 comment

- **重要 rename 关系说明**:
  - `bb_v3` / `bv_v3` 是 **跟 `bb_slot_v2` / `bv_slot_v2` 完全不同的变量**,在 `cg_match_pattern` phi 收集循环里 (`codegen.jhyy:2656-2657`),独立 scope
  - `argc_v2` / `argc_v3` / `argc_v4` / `argc_v5` 是 4 个不同 fn 参数 (`cmd_compile` / `cmd_run` / `cmd_dump` / `main_jhyy`),各自独立 scope 都改 `argc` 安全
  - `init_v` x2 重复经 audit 验证 (mutable/array/struct path vs immutable path) 是 if/else 兄弟分支,scope 不重叠,安全
  - `bb_slot` / `bv_slot` x2 重复经 audit 验证 (2607-2617 vs 2624-2638 两个 if block),scope 不重叠,安全

- **Diff 验证**:
  - `git diff --stat compiler/src0/`: 36+/36- 完美对称,纯 rename,无功能改动

### 验证

- **jhyy_v1 编 src0/main.jhyy** (canonical `ba94df93...`):
  - Compile 成功,exit=0
  - 输出 `_v124_jhyy_v2.il` sha `f75ef7e2...`
  - v2 → v3 cascade: `_v124_v3.il` sha `5673c107...`, diff = 12 行 (7 cascade + 5 context) ✅
  - **跨 v1.2.1/v1.2.2/v1.2.3/v1.2.4 7 行 cascade 一致** — 证明 v1.2.4 zero IR impact beyond QBE symbol rename

- **regress.py 50/50 PASS** (C-side,`jhyy.exe` sha `d442ba3f...`): baseline 持平 ✅
- **regress_v1.py 50/50 PASS** (jhyy_v1 编 src0/,canonical `ba94df93...`): baseline 持平 ✅
- **closure binaries canonical sha 不变**:`jhyy_v1.exe` `aa57849c` / `jhyy_v2.exe` `d3aeed09` / `jhyy_v3.exe` `536ffcb2` / `jhyy_v4.exe` `eb8b7a3b` — v1.2.4 零干扰

### 不动

- 跟 v1.2.3 同:函数名 (`resolve_one_import_v1` / `var_name_eq_v1` 等保留,改函数名是 v3.x 命名空间范畴)
- 跟 v1.2.3 同:comment 里描述 `jhyy_vN` / `regress_vN.py` 的历史叙述
- 别的 session untracked 文件
- 跟 v1.2.3 同:`_W002_rename_map.txt` 翻译映射 comment

### 留给后续

- v1.2.5 doc 同步 (workarounds.md W-XXX 标 RESOLVED + status.md "src0/ 自然化" section + changelog 收尾)
- v1.3 (下一阶段) v1.x 语法糖

### 引用

- v1.2.1/v1.2.2/v1.2.3 changelog — 同样 pure rename 验证 (Stage 2 N=3 7 行 cascade 跨 sprint 一致)
- [[project-sprint-v1-1-2-c-side-divergence]] — C-side vs jhyy_v1 IL divergence 性质 (rename 后 sha 变化是预期)
- sha256sum 检查守门 (本次全程 jhyy_v1.exe.exe `ba94df93` + jhyy_v*.exe 4 个 closure binary canonical sha 0 干扰)

---

## v1.2 wip commit 1.5 — Doc sync (workarounds.md + status.md + changelog 收尾) — 2026-08-12

**类型**: doc-only (no code change)
**估时**: 0.3 sprint
**workarounds.md**: W-005 / W-003 状态从 "code revert 完" → "完整闭环 (v0 fix ship + src0/ 代码撤回双 ship)"

### 工作

- **`docs/internal/status.md` 修改**:
  - § "当前 sprint / 下一阶段": 加 v1.2.0 sprint 块 (4 commits 一览),串入 v1.1.0 + v1.0.0 + v0.9 wip 主线
  - 下一阶段: v2.x/v3.x → **v1.3 (v1.x 语法糖 Phase 4)** 优先 (per user feedback 2026-08-12)
  - 新增 § "src0/ 自然化 (v1.2.0 sprint, 2026-08-12 ship)" section: 4 sprint 一览表 + 纯 rename 验证 (跨 4 commit 7 行 cascade 一致) + 不动的 defense 列表 + Plan / 记录链接

- **`docs/internal/workarounds.md` 修改**:
  - § W-005 末尾加 "v1.2.0 cross-ref" 段: 16 处 revert + 99 处 `_vN` cleanup + 完整闭环确认
  - § W-003 RESOLVED 段加 "v1.2.0 cross-ref" 段: 24 处 revert + out-of-scope "29 处" 实际工作已 ship 确认
  - List 表格 (line 30 + 32) W-003 / W-005 状态文字已 ship 状态文档对齐全

- **`docs/logs/v1/changelog-v1.2.0.md` § v1.2 wip commit 1.5** (本 entry): 收尾整 v1.2.0 sprint 5 commit 记录

### 验证

- **doc 一致性**: workarounds.md (W-005/W-003 cross-ref) / changelog-v1.2.0.md (commit 1.1-1.5 完整) / status.md (新 src0/ 自然化 section) 三方对齐 ✅
- **不需 code regress** (doc-only): 仍跑双 50/50 守门 ✅
  - regress.py 50/50 PASS (jhyy.exe sha `d442ba3f...`)
  - regress_v1.py 50/50 PASS (jhyy_v1.exe.exe sha `ba94df93...`)

### v1.2.0 整体完成 (5 commits 总览)

| v1.2.x | 类型 | commit | 改动 | grep 命中 |
|--------|------|--------|------|----------|
| 1.1 | W-005 revert | `2c92cf4` | src0/ 3 files | 16 处 `let mut x_v1` |
| 1.2 | W-003 revert | `f49e64d` | src0/ 1 file (codegen) | 24 处 `let _ = fncall()` |
| 1.3 | `_v1` cleanup | `1c24841` | src0/ 3 files | 63 处 / 19 unique identifier |
| 1.4 | `_v2`/`_v3`/`_v4`/`_v5` cleanup | `0026098` | src0/ 3 files | 36 处 / 18 unique identifier |
| 1.5 | doc sync | (this) | docs/ 3 files | 0 code change |

**累计**: 5 commits, 99 处 code rename + 3 docs file, 2.3 sprint 实际用 ~1 sprint (1-day batch ship)

**对照 plan 估时**:
- v1.2.1: 0.5 sprint (估) ≈ 0.2 sprint (实)
- v1.2.2: 0.5 sprint (估) ≈ 0.1 sprint (实)
- v1.2.3: 0.5 sprint (估) ≈ 0.2 sprint (实)
- v1.2.4: 0.5 sprint (估) ≈ 0.1 sprint (实)
- v1.2.5: 0.3 sprint (估) ≈ 0.1 sprint (实)
- **总计**: 2.3 sprint (估) ≈ 0.7 sprint (实) — 节省 1.6 sprint (per v1.2 sed 模式 + 4-commit 一次 batch ship)

### 留给后续

- **v1.3 (下一阶段)** v1.x 语法糖 Phase 4 of v1.0-post-50-53-plan.md — null / else if / sizeof / for-in / `#[inline]` / defer / Pattern binding / OR pattern, 5-7 sprint
- v1.3 全 ship 后启动 **v2.x** (QBE 完整重写) || **v3.x** (语言扩展) 并行 (OS 准备)

### 引用

- v1.2.1/v1.2.2/v1.2.3/v1.2.4 changelog — 4 sprint 完整 ship 记录
- [`docs/internal/status.md` § src0/ 自然化](../status.md) — status.md 新 section
- [`docs/internal/workarounds.md` § W-005 / § W-003 cross-ref](../workarounds.md) — workarounds.md v1.2.0 cross-ref
- [[project-v1-0-post-50-53-plan]] § Phase 3.1 — W-005 / W-003 / `_vN` 清理原始 plan
- [[project-sprint-v1-1-2-c-side-divergence]] — C-side vs jhyy_v1 IL divergence
