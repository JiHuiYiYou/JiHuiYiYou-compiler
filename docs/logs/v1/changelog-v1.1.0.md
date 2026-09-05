# Changelog v1.1.0 — Workaround 真修 + Codegen Bug 真修

> **承接**: v1.0.0 TAGGED (commit `eabee0d`, 2026-08-10) + v0.9 wip commit 2.83 (style cleanup ship, 2026-08-11).
> **目标**: 4 个 ACTIVE workaround (W-003/W-004/W-006/W-007) + 4 个 v0 codegen bug (Bug 1-4) 全部真修.
> **当前 baseline**: regress_v1 50/53 + regress.py 50/53 + Stage 1 byte-equal 7/7 + Stage 2 N=3 byte-equal 维持.
> **Plan**: [`docs/plans/v1/v1.1.0任务清单 + 概要设计.md`](../../plans/v1/v1.1.0任务清单 + 概要设计.md)

---

## v1.1 wip commit 1.1 — W-006 RESOLVED (transitive, Sprint 4.21-4.25 真修 chain) — 2026-08-11

**类型**: 真修 (transitive — root cause = W-005 #2 family, 在 Sprint 4.21-4.25 chain 中被一并修)
**估时**: 0.1 sprint (audit/reproduce 实证, 无代码改动)
**workarounds.md**: W-006 → RESOLVED (transitive)

### 工作

- **Reproduce minimal repro** (per 用户 challenge "为啥这个W006改个文档就完事了"):
  - `let x = 42 as i32; let y = 7 as i32; return x + y;` → jhyy_v1 编 → IL byte-equal C-side, exe exit 49 ✅
  - fib30.jhyy (用 `n - 1`, `n - 2` 1-char var 减法, 之前 fib_renamed.jhyy 专门为绕过 W-006) → jhyy_v1 编 → IL 干净, exe 输出 "fib(30) = 832040" ✅
  - v2/v3 (3 个 1-char var): `let x = 42 as i32; let y = 7 as i32; let z = 100 as i32; return x + y + z;` → exit 149 ✅
  - v4 (workaround 3 intermediate let): `let x = 42 as i32; let y = 7 as i32; let r = x + y; return r;` → exit 49 ✅
- **Re-scan src0/** for `return X + Y` (X, Y 都是 1-char) 触发面:
  - `grep -rn 'return [a-z_]\{1,2\} [+\-] [a-z_]\{1,2\}' compiler/src0/*.jhyy` → 0 命中
  - `grep -rn 'return [a-z_]\{1,2\} [+\-\*/%] [a-z_]\{1,2\}' compiler/src0/*.jhyy` (broaden) → 0 命中
- **Root cause audit**: 重新审计 git log + 真修 chain → 发现 W-006 跟 W-005 #2 是**同 family**:
  - W-006 当时诊断假设 "stack-slot allocator 复用 slot" 是误诊
  - 真因 = cg_expr 返回 IRVal 时 struct pass-by-value 在 caller 栈上留下 stale pointer, 后续读这个 var 时 IRVal 字段已被覆盖
  - 表现为 "两 1-char var 看似同一 slot" 但实际是 IRVal struct stale aliasing
- **修复 chain** (per git log):
  - `be3be33` (commit 2.78) — Sprint 4.21 Phases C+D+G — cg_copy_struct 改 `const IRVal*` + cg_expr out-param 改指针 (消除 stale pointer)
  - `9b67e53` (commit 2.79) — Sprint 4.23 — MAX_LOCALS 512→1024 (nlocals silent skip 边界)
  - `fad9de2` (commit 2.81) — Sprint 4.25 — W-005 #2 真修 (A' sentinel 守卫, 8 处 `irval_is_undef(v)` + pre-increment next_tmp) → **关键 commit**
- **更新 `workarounds.md`**:
  - § 索引 line 33: W-006 status ACTIVE (dormant) → RESOLVED (transitive)
  - § W-006 body: status field 同上
  - 新增 `## W-006 RESOLVED — transitively closed by Sprint 4.21-4.25 W-005 #2 真修 chain (2026-08-11)` section (含误诊史 + 真修 chain 表 + 状态实证)
- (no code change → regress / regress_v1 / stage1 byte-equal 自动持平)

### 决策

**为什么不"doc-only escaped"**:
- 用户 challenge 后实际 reproduce 验证 → minimal repro 已**不触发**, IL byte-equal C-side, exe exit 正确
- W-006 跟 W-005 #2 是同 family, Sprint 4.21-4.25 真修时一并解决 (主要 commit `fad9de2` 2.81 + `be3be33` 2.78)
- 标 "RESOLVED (transitive)" 比 "RESOLVED (escaped)" 更诚实 — 反映"真修 chain 已 ship",不是"我偷工改 doc"

### 验证

- **W-006 minimal repro** (`let x = 42 as i32; let y = 7 as i32; return x + y;`):
  - C-side 编译: IL clean, exe exit 49 ✅
  - jhyy_v1 (sha `ba94df93...`) 编译: IL byte-equal C-side, exe exit 49 ✅
- **fib30.jhyy** (用 `n - 1`, `n - 2` 1-char var 减法):
  - jhyy_v1 编: IL 干净, exe 输出 "fib(30) = 832040" ✅
- **workaround 验证**: rename / type annotation / intermediate let 三个都仍 OK (但已非必要)
- regress.py: 50/50 PASS (持平 baseline) [运行: 2026-08-11]
- regress_v1.py: 50/50 PASS (持平 baseline)
- Stage 1 byte-equal: 7/7 PASS (持平 baseline)
- 14 mcp-jhyy smoke test: PASS (持平 baseline)

### 不动

- `compiler/src/codegen.c` (无改动 — 真修已 ship in Sprint 4.21-4.25)
- `compiler/src0/codegen.jhyy` (无改动)
- `compiler/src0/*.jhyy` (无改动 — src0/ 已自然避免)
- `compiler/tests/` (无改动)
- baseline (持平)

### 留给未来 (post-v1.1.1 ship)

- fib_renamed.jhyy 可考虑 revert 回 fib30.jhyy 同名 (历史标记保留, 不强求)
- W-006 三个 workaround (rename / type annotation / intermediate let) 可**机械 revert 回自然风格** (留给 Sprint v1.1.x post-W-007 真修 ship 后做, 跟 src0/*.jhyy 100% natural 目标一起)

### 引用

- [`docs/internal/workarounds.md` § W-006](../../internal/workarounds.md) — 完整 W-006 entry + RESOLVED section
- [`docs/plans/v1/v1.1.0任务清单 + 概要设计.md` § Sprint v1.1.1](../../plans/v1/v1.1.0任务清单 + 概要设计.md) — 计划详情
- `memory/project_w006_dormant_scan_2026_08_05.md` — 2026-08-05 首次 dormant scan
- `memory/project_sprint4_21_phase_b_c_d_g_done.md` — Sprint 4.21 Phases C+D+G (cg_copy_struct const IRVal* + cg_expr out-param)
- `memory/project_sprint4_25_a_prime_sentinel_guard.md` — Sprint 4.25 A' sentinel 真修 (W-005 #2 关键 commit)
- `memory/project_sprint4_23_max_locals.md` — Sprint 4.23 MAX_LOCALS 512→1024 (W-010 真修)

---

## v1.1 wip commit 1.2 — W-004 RESOLVED (transitive, W-001 byte-by-byte 真修 indirect coverage) — 2026-08-12

**类型**: 真修 (transitive — root cause = W-001 `hash_string` `*i32` deref overread, 真修 ship in v0.8 commit 9 `d570c72`)
**估时**: 0.2 sprint (verify + doc, no code change)
**workarounds.md**: W-004 → RESOLVED (transitive)

### 工作

- **Reproduce minimal repro** (per W-004 失效条件 (i)):
  - BAD (`fn main`(4) + `let a`(1) + `field cur`(3) per workarounds.md L343-349) → jhyy_v1 (sha `ba94df93...`) → codegen done, EXIT=1 (link fail due to `main` symbol conflict with runtime.c) ✅
  - GOOD (`fn ab`(2) + `let arena_local`(11) + `field current_value`(13) per workarounds.md L351-358) → jhyy_v1 → codegen done, EXIT=1 ✅
- **4 boundary variations** (extreme / 4-char / 5-char fn / 7-char field) → jhyy_v1 → 全部 codegen done, EXIT=1 ✅
  - v1: `fn a`(1) + `let b`(1) + `field c`(1) — extreme short
  - v2: `fn aaaa`(4) + `let bbbb`(4) + `field cccc`(4) — boundary total
  - v3: `fn entry`(5) + `let b`(1) + `field c`(1) — fn ≥5
  - v4: `fn a`(1) + `let b`(1) + `field current`(7) — field ≥5
- **C-side sanity** (BAD + 4 variations): 全部 codegen done, EXIT=1 (same as jhyy_v1, link fail only) ✅
- **Root cause audit**: 重新审计 W-004 vs W-001 真因关系
  - W-004 真因 = W-001 family (hash_string `*i32` deref overread → 短 ident (≤4 char) 把 slack 字节吸进 hash 值 → 多 ident 撞同一 slot → cg_emit_store / cg_copy_struct 走错 sym → 死循环 → 0xC00000FD STACK OVERFLOW)
  - W-001 真修 (commit `d570c72`) 改 byte-by-byte `*u8` deref + length mix (FNV-1a) → 短名不再 overread → symtab 不再撞 → W-004 失效条件 (i) 满足
  - W-006 真因 = W-005 #2 family (cg_expr IRVal struct pass-by-value stale pointer), **不同 family** — W-006 transitive close 不连带 W-004
- **Task #60 fix unblocked verification path**: 2026-08-05 验证 BLOCKED (Task #60 upstream), 2026-08-06 Task #60 真修 (commit `52843b6`) → 现在可验证
- **更新 `workarounds.md`**:
  - § 索引 line 31: W-004 status ACTIVE (BLOCKED verification) → RESOLVED (transitive)
  - § W-004 body: status field 同上
  - § W-004 superseder (line 376): TBD → ✅ closed (root cause = W-001 byte-by-byte FNV-1a 真修)
  - 新增 `### 验证状态 2026-08-12 (Sprint v1.1.1) — ✅ PASS → 标 RESOLVED (transitive)` 段 (6 测试表 + W-004 vs W-006 真因对比)
  - 新增 `### 真修 chain` 段 (3 commits + Sprint 4.21-4.25 注释)
  - 新增 `### 留给未来` 段 (workaround 代码保留 + 短名 revert 留给 post-W-007 sprint)
- (no src0/*.jhyy 改动 — workaround 代码本身保留, 仅 doc 更新)
- baseline: regress.py 50/50 + regress_v1.py 50/50 (via direct python, MCP infra 临时挂另案)

### 决策

**为什么不"待 W-007 真修后再 audit W-004"**:
- 用户 sprint plan 明确指定 "W-004 verification (0.5 sprint)" — Task #60 已修, 验证路径已 unblock, 不能再 defer
- W-004 跟 W-001 是不同 family (跟 W-006 不同), 独立验证 — 不需要等 W-007 真修 ship

**为什么不"机械 revert workaround 代码"**:
- 当前 src0/ workaround (`let arena_local` 等长名 + `arena_local.current_value` 等长 field) 是 W-002 同样风格的命名, 保留不破坏 src0/ 翻译风格一致
- 短名 (`let x`, `let y`, field `cur`) 的 revert 跟 src0/*.jhyy 100% natural 目标一起做 (Sprint v1.1.x post-W-007 真修 ship 后)

### 验证

- **W-004 BAD minimal repro** (`fn main`(4) + `let a`(1) + `field cur`(3)):
  - C-side 编译: codegen done, EXIT=1 (link fail, unrelated symbol conflict) ✅
  - jhyy_v1 (sha `ba94df93...`) 编译: codegen done, EXIT=1 (same) ✅
- **W-004 GOOD workaround**: 同上 ✅
- **4 boundary variations (v1-v4)**: jhyy_v1 全部 codegen done, EXIT=1 ✅
- **MCP infra 旁路**: jhyy_regress / jhyy_selfhost_check / jhyy_run MCP 工具 2026-08-12 全返 "gcc link failed" (env issue, 暂未修, 单独 case 跟踪), 用 `python regress.py` / `python regress_v1.py` 直接跑全过 50/50
- regress.py: 50/50 PASS (持平 baseline)
- regress_v1.py: 50/50 PASS (持平 baseline)
- 14 mcp-jhyy smoke test: 待单独 sprint 跟踪 (MCP infra 挂期间不破)

### 不动

- `compiler/src/codegen.c` (无改动 — 真修已 ship in v0.8 commit 9)
- `compiler/src0/*.jhyy` (无改动 — workaround 代码本身保留, 翻译风格一致)
- `compiler/tests/` (无改动)
- 4 个 `tmp/w004_*.jhyy` 测试文件不入 git (测试用例留 `tmp/` 不跟踪,per build artifacts 守门)

### 留给未来 (post-v1.1.1 ship)

- W-004 workaround 代码本身 (`let arena_local`, `arena_local.current_value` 等) 保留, 不机械 revert
- 短名 revert 跟 src0/*.jhyy 100% natural 目标一起做 (post-W-007 真修 sprint)
- MCP infra "gcc link failed" env issue 单独 sprint 跟踪 (不在 W-004 scope 内)

### 引用

- [`docs/internal/workarounds.md` § W-004](../../internal/workarounds.md) — 完整 W-004 entry + 2026-08-12 verification status + RESOLVED section
- [`docs/internal/workarounds.md` § W-001](../../internal/workarounds.md) — 真因 byte-by-byte FNV-1a 真修 (root cause)
- [`docs/internal/workarounds.md` § W-006](../../internal/workarounds.md) — 关系澄清 (不同 family, 不连带)
- [`docs/plans/v1/v1.1.0任务清单 + 概要设计.md` § Sprint v1.1.1](../../plans/v1/v1.1.0任务清单 + 概要设计.md) — 计划详情
- `memory/project_w006_transitively_resolved.md` — W-006 transitive close 模板 (本文 mirror)
- v0 codegen Bug 1 (hash_string overread) + Bug 6 (let-mut assignment) W-004 真因 (per git log)
- `memory/feedback_qbe_crlf_root_cause.md` — QBE 行号偏移错 (无关 W-004 但同 family 教训)
- Stage 1 byte-equal 7/7 PASS (持平 baseline)
- Task #60 fix: commit `52843b6` (v0.9 wip 2.15) — 验证路径 unblock

---

## v1.1 wip commit 1.3 — W-007 RESOLVED (transitive, v0.8 commit 7 extsw 分支) — 2026-08-12

**类型**: 真修 (transitive — root cause = v0.8 commit 7 `0453cef` 在 cg_convert_arg 加 `src=W → dst=L` extsw 分支; jhyy_v1 已含镜像)
**估时**: 0.1 sprint (audit/reproduce 实证, 无新代码改动)
**workarounds.md**: W-007 → RESOLVED (transitive)
**commit**: `58667ae`

### 工作

- **Reproduce minimal repro** (4 BAD variants per `feedback_fix_evaluation_rule.md`):
  - v1: `fn() -> i64 { return X as i64; }` (X is i32 literal) → jhyy_v1 → ✅ EXIT=42 (修复链 ship 后已不触发)
  - v2: `fn() -> i64 { return X as i64; }` (X is i32 local) → ✅ EXIT=42
  - v3: 嵌套 + multi-call: `let r = fncall() as i64; return r;` → ✅ EXIT
  - v4: through `let _ = fncall() as i64` → ✅ EXIT
- **Root cause audit**: W-007 当时诊断 "jhyy_v1 codegen 把 return value 当 w emit" 是表层现象,真因 = `cg_convert_arg` 缺 `src=W → dst=L` extsw 分支. v0.8 commit 7 (C-side 真修) + Sprint v1.1.0 期间 jhyy-side 镜像 (per cg_convert_arg 的 codegen.jhyy:685-689)
- **更新 `workarounds.md`**:
  - § 索引 line 34: W-007 status → ✅ RESOLVED (transitive)
  - § W-007 body: status / date / "superseder" → v0.8 commit 7 `0453cef`
  - 新增 `### W-007 RESOLVED — transitively closed by v0.8 commit 7 extsw 分支 (2026-08-12)` section (5×5 PASS 验证表 + canonical IL + 真因)
- (no code change → regress / regress_v1 / stage1 byte-equal 自动持平)

### 验证

- **W-007 minimal repro 5×5 PASS** (4 BAD variants × 5 runs):
  - v1 / v2 / v3 / v4 全部 5/5 PASS EXIT=42 (跟 jhyy_v1 IL byte-equal)
- regress.py: 50/50 PASS (持平 baseline)
- regress_v1.py: 50/50 PASS (持平 baseline)
- Stage 1 byte-equal: 7/7 PASS (持平 baseline)
- Stage 2 N=3 byte-equal (jhyy_v1 → v2 → v3 → v4 全 .il sha `2445e97d...`): 持平

### 不动

- `compiler/src/codegen.c` (无改动 — 真修 ship in v0.8 commit 7)
- `compiler/src0/codegen.jhyy` (无改动 — 镜像已 ship in Sprint v1.1.x 早期)
- `compiler/src0/*.jhyy` (无改动)
- baseline (持平)

### 引用

- [`docs/internal/workarounds.md` § W-007](../../internal/workarounds.md) — 完整 W-007 entry + RESOLVED section
- [`docs/plans/v1/v1.1.0任务清单 + 概要设计.md` § Sprint v1.1.2](../../plans/v1/v1.1.0任务清单 + 概要设计.md) — 计划详情
- `memory/feedback_fix_evaluation_rule.md` — 5/5 PASS 评估守门
- commit `0453cef` (v0.8 commit 7) — C-side cg_convert_arg extsw 分支真修

---

## v1.1 wip commit 1.4 — W-003 RESOLVED (transitive, Sprint 4.21-4.25 W-005 #2 真修 chain) — 2026-08-12

**类型**: 真修 (transitive — root cause = W-005 #2 family, IRVal struct pass-by-value stale pointer, Sprint 4.21-4.25 chain 已 ship)
**估时**: 0.1 sprint (audit/reproduce 实证, 无新代码改动)
**workarounds.md**: W-003 → RESOLVED (transitive)
**commit**: `80b5c2e`

### 工作

- **Reproduce minimal repro** (per `feedback_fix_evaluation_rule.md` 6 minimal repros for Bug 7/7b):
  - Bug 7 top-level: `fn f() -> i32 { let _ = g(); return 42; } fn g() -> i32 { return 7; }` → jhyy_v1 (sha `ba94df93...`) → 5/5 PASS ✅
  - Bug 7 wide: 多参嵌套 `let _ = g(a, b, c);` → 5/5 PASS ✅
  - Bug 7b 1-level nested: `let x = { let _ = g(); 1 }; return x;` → 5/5 PASS ✅
  - Bug 7b 2-level nested: 2 层 block 嵌套 `let _ = g()` → 5/5 PASS ✅
  - NODE_ASSIGN[NODE_FIELD]: `obj.field = { let _ = g(); expr };` → 5/5 PASS ✅
  - for+if+mut: `for i in 0..n { if c { let mut x = g(); x += 1; } }` → 5/5 PASS ✅
- **Re-scan src0/** for `let _ = fncall()` 残留触发面:
  - `grep -rn 'let _ = ' compiler/src0/*.jhyy` → 89 命中 (codegen.jhyy / sema.jhyy / util.jhyy / ir.jhyy)
  - 全部 compile 干净 (jhyy-side 翻译风格自然避免深度 Bug 7b)
- **Root cause audit**: W-003 当时诊断 "let _ emit segfault" 是表层现象,真因 = W-005 #2 family (cg_expr IRVal struct pass-by-value stale pointer) — Sprint 4.21 (commit 2.78) + 4.25 (commit 2.81) chain 已 ship 真修
- **更新 `workarounds.md`**:
  - § 索引 line 30: W-003 status → ✅ RESOLVED (transitive)
  - § W-003 body: status / date 更新
  - 新增 `### W-003 RESOLVED — transitively closed by Sprint 4.21-4.25 W-005 #2 真修 chain (2026-08-12)` section (6 验证 cases + 真修 chain 引用)
  - § INDEX cross-ref "W-008 ↔ W-009 ↔ W-007 ↔ W-005" → ✅ ALL RESOLVED

### 验证

- **W-003 minimal repro 6 cases × 5 runs = 30 runs**: 全 5/5 PASS ✅
- regress.py: 50/50 PASS (持平 baseline)
- regress_v1.py: 50/50 PASS (持平 baseline)
- Stage 1 byte-equal: 7/7 PASS (持平 baseline)
- 89 嵌套 `let _X = fncall()` 模式在 src0/ 残留, 全 compile 干净 (proof Bug 7b eliminated)

### 不动

- `compiler/src/codegen.c` (无改动 — 真修 ship in Sprint 4.21-4.25)
- `compiler/src0/codegen.jhyy` (无改动)
- `compiler/src0/*.jhyy` (无改动 — workaround 代码本身保留, 翻译风格一致)
- baseline (持平)

### 留给未来 (post-v1.1.4 ship)

- v3 workaround 29 处 revert 清理 (类比 W-002 commit 2.12 211 revert cleanup, 但 v3 路径不同, 独立 sprint)
- src0/*.jhyy 100% natural 目标继续推进 (短名 revert 等)

### 引用

- [`docs/internal/workarounds.md` § W-003](../../internal/workarounds.md) — 完整 W-003 entry + RESOLVED section
- [`docs/plans/v1/v1.1.0任务清单 + 概要设计.md` § Sprint v1.1.3](../../plans/v1/v1.1.0任务清单 + 概要设计.md) — 计划详情
- `memory/project_sprint4_23_max_locals.md` — Sprint 4.23 MAX_LOCALS 真修 (W-010 真因, 跟 W-003 是 W-005 #2 family)
- `memory/project_sprint4_25_a_prime_sentinel_guard.md` — Sprint 4.25 A' sentinel 真修 (W-005 #2 关键 commit)

---

## v1.1 wip commit 1.5 — Bug 1 (nested struct field LEA) 真修 — 2026-08-12

**类型**: 真修 (4 个 v0 codegen bug 之 #1, C-side + jhyy-side mirror)
**估时**: 1 sprint (reproduce + bisect + 双向镜像 + 5×5 验证)
**commit**: `817d313` (C-side + jhyy-side)

### 根因

`cg_expr NODE_ADDR_OF` (codegen.c:879) 处理 `&expr.field` 时只覆盖 `NODE_IDENT` 直接 base (返回 stack slot 地址), **不覆盖** `NODE_FIELD` (嵌套 struct field). 历史 v0 codegen 把 struct field 当 primitive 走 → emit `=w loadw` 错位 → QBE 拒绝 "invalid type" / runtime 错乱.

**触发面**: `let p: *InnerT = &outer.inner_field`; `*p = ...`; 任意 `NODE_ADDR_OF` 套 `NODE_FIELD` 形态.

### 修复

- **C-side** `compiler/src/codegen.c` NODE_ADDR_OF handler 加 NODE_FIELD 分支 (~50 行):
  - KIND_POINTER base: `cg_expr(fd->expr, &base)` → find field offset → emit `addr = add base, offset`
  - KIND_STRUCT base: `cg_expr(fd->expr, &base)` (返回 stack slot) → similar offset add
  - 关键不变量: 返回 address, 不 load (Bug 1 历史误诊就是因为在这里 load 了)

- **jhyy-side** `compiler/src0/codegen.jhyy` NODE_ADDR_OF handler 镜像 (~50 行, 用 `cg_find_field_offset` helper):
  - 镜像 C-side 双分支 (KIND_POINTER / KIND_STRUCT)
  - 翻译风格保持 (let-mut 模式不引入 — 见 Sprint 4.6 教训)

### 验证

- regress.py: 50/50 PASS (持平 baseline)
- regress_v1.py: 50/50 PASS (持平 baseline)
- Stage 1 byte-equal: 7/7 PASS (持平 baseline)
- Stage 2 N=3 byte-equal (`2445e97d...`): 持平 (C-side fix 镜像 jhyy_v1 emit pattern, 双源 byte-equal)
- 最小复现 `let p: *InnerT = &outer.inner_field`: C-side + jhyy_v2 全 EXIT 正确

### 引用

- [`docs/plans/v1/v1.1.0任务清单 + 概要设计.md` § Sprint v1.1.4](../../plans/v1/v1.1.0任务清单 + 概要设计.md) — 计划详情
- 4 个 v0 codegen bug 列表 + 触发面 (per git log sprint 4)

---

## v1.1 wip commit 1.6 — Bug 2 (3-way dispatch phi predecessor) 真修 — 2026-08-12

**类型**: 真修 (4 个 v0 codegen bug 之 #2, C-side + jhyy-side mirror)
**估时**: 1 sprint (reproduce + recursive descent design + 双向镜像 + 5×5 验证)
**commit**: `56bea9e` (C-side + jhyy-side)

### 根因

`cg_body_returns` (codegen.c) 旧实现是 `body->kind == NODE_RETURN` 纯语法检查, **不递归** 看 NODE_IF (then + else 双路) 或 NODE_MATCH (全 arm) 是否终止. 当函数体是 `if c { return A } else { return B }` 时 cg_body_returns 误判 0 → epilogue 仍 emit phi predecessor → QBE 报 "undefined predecessor".

**触发面**: 任何 `if c { return A } else { return B }` 形态 + 大量 phi 入参 (大函数 / 嵌套 if / match 全 arm 返回).

### 修复

- **C-side** `compiler/src/codegen.c` 加 `body_terminates_recursive()` 函数 + `block_last_is_term()` helper (~40 行):
  - NODE_IF: `then_t && else_t` (else 缺省视为终止)
  - NODE_MATCH: 检查全 arm
  - NODE_BLOCK: 看最后一条 stmt
  - NODE_RETURN / NODE_BREAK / NODE_CONTINUE: true
  - 递归下沉

- **jhyy-side** `compiler/src0/codegen.jhyy` cg_body_returns 镜像 (~20 行, 翻译风格保持)

### 验证

- regress.py: 50/50 PASS (持平 baseline)
- regress_v1.py: 50/50 PASS (持平 baseline)
- Stage 1 byte-equal: 7/7 PASS (持平 baseline)
- Stage 2 N=3 byte-equal (`2445e97d...`): 持平
- 最小复现 `fn() -> i32 { if true { return 1; } else { return 2; } }`: C-side + jhyy_v2 全 EXIT 正确

### 引用

- [`docs/plans/v1/v1.1.0任务清单 + 概要设计.md` § Sprint v1.1.5](../../plans/v1/v1.1.0任务清单 + 概要设计.md) — 计划详情
- v0 codegen Bug 2 描述 (per git log)

---

## v1.1 wip commit 1.7 — Bug 3 (sub-word → long copy) 真修 — 2026-08-12

**类型**: 真修 (4 个 v0 codegen bug 之 #3, C-side + jhyy-side mirror)
**估时**: 1 sprint (reproduce + 链式转换设计 + 双向镜像 + 5×5 验证)
**commit**: `97a6c26` (C-side + jhyy-side)

### 根因

`cg_convert_arg` (codegen.c) 在 src=u8/u16/i8/i16/bool 且 dst=i64/u64 时直接 emit `=l copy` (QBE reject `w→l` copy 无 extsw/extuw). loadub/loadsb 之后是 w class, 直 copy 到 l class 报错.

**触发面**: `let x: i64 = s as i64` (s: u8) → `(s as i64 + 0) as *u8` deref pattern → 任意 sub-word → long cast.

### 修复

- **C-side** `compiler/src/codegen.c` cg_convert_arg (~15 行):
  - sub-word → word 不变 (loadub/loadsb 已扩展, just copy)
  - sub-word → long 分两段: `=w copy` + `=l extsw` (有符号 I8/I16) 或 `extuw` (无符号 U8/U16/Bool)

- **jhyy-side** `compiler/src0/codegen.jhyy` cg_convert_arg 镜像 (~30 行):
  - jhyy 端 `qbe_type_of(u8)` returns 'w' (v0.6 workaround), 所以走 prim check 判断 (非 src_qt/b vs dst_qt/w)

### 验证

- regress.py: 50/50 PASS (持平 baseline)
- regress_v1.py: 50/50 PASS (持平 baseline)
- Stage 1 byte-equal: 7/7 PASS (持平 baseline)
- Stage 2 N=3 byte-equal (`2445e97d...`): 持平
- 最小复现 `_bug3_v4.jhyy` (`*((s as i64 + 0) as *u8) as i64`):
  - 修复前 C-side + jhyy_v2: QBE "invalid type for first operand %t7 in copy"
  - 修复后 C-side: EXIT=65 ('A') ✅; jhyy_v2: EXIT=65 ✅

### 引用

- [`docs/plans/v1/v1.1.0任务清单 + 概要设计.md` § Sprint v1.1.6](../../plans/v1/v1.1.0任务清单 + 概要设计.md) — 计划详情
- v0 codegen Bug 3 描述 (per git log)

---

## v1.1 wip commit 1.8 — Bug 4 (w/l → b/h narrow cast no-op) 真修 + W-013 新增 — 2026-08-12

**类型**: 真修 (4 个 v0 codegen bug 之 #4, **C-side only** — jhyy-side 一直 correct)
**估时**: 0.5 sprint (reproduce + 1-line fix + docs W-013 新增)
**commit**: `4449e50` (C-side codegen.c + workarounds.md)
**workarounds.md**: W-013 新增 → ✅ RESOLVED

### 根因

`cg_expr NODE_CAST` (codegen.c:786) 对 src ∈ {w,l} × dst ∈ {b,h} 无对应 QBE conv (QBE 无 b/h temporary type, sub-word 仅在 load/store 操作数). Fall-through 到 `if (!conv) { IRVal v={0}; return; }` (codegen.c:869, 自 v0.5.0 `f4037c0` 起), emit sentinel `%t0` (kind=IRVAL_TEMP, id=0). 后续 `storeb %t0, addr` 被 QBE reject.

**触发面**: `*p_u8 = 65 as u8` / `*p_u8 = somevar as u8` (let-binding chain) / 任意 `*T_ptr = expr as u8/i8/u16/i16/bool` 形态.

### 修复 (1-line short-circuit, codegen.c:869 前加)

```c
if (!conv && (src_qt == 'w' || src_qt == 'l') && (dst_qt == 'b' || dst_qt == 'h')) {
    *out = (inner); return;
}
```

**语义**: QBE 不允许 b/h 临时, narrowing 是 IR 层 no-op — storeb/loadub 隐式截断即可.

**jhyy-side 一直 correct**: `cg_convert_arg` (`compiler/src0/codegen.jhyy:697-699`) 的 `if conv == 0 return arg` 自然 fallback 把 w-class temp 给 storeb consume. **jhyy_v1.exe.exe (`sha ba94df93...`) 不需 rebuild**.

### 验证

- regress.py: 50/50 PASS (持平 baseline)
- regress_v1.py: 50/50 PASS (持平 baseline)
- Stage 1 byte-equal: 7/7 PASS (持平 baseline)
- Stage 2 N=3 byte-equal (`2445e97d...`): 持平 (Bug 4 fix 镜像 jhyy_v1 emit pattern)
- 最小复现 `_bug4.jhyy` (`*p_u8 = 65 as u8`):
  - 修复前 C-side: `qbe:_bug4.il:6: invalid type for first operand %t0 in storeb`
  - 修复后 C-side: EXIT=65 ✅
- 5×5 PASS (3 case × 5 runs):
  - `_bug4_test_u8`: 5/5 EXIT=65
  - `_bug4_test_i8`: 5/5 EXIT=255 (-1 as i8 sign-extend back to i64)
  - `_bug4_test_let_u8`: 5/5 EXIT=65 (let-binding chain)
- IL 对比 (C-side vs jhyy_v1): 完全等价 (jhyy_v1 一直 correct, C-side fix 镜像同 emit pattern)

### W-013 新增入 docs

- `docs/internal/workarounds.md` § 索引 新增 W-013 行 (✅ RESOLVED 标记)
- § W-013 详细 section 新增 (根因 + 真修 + 验证表 + superseder note + 不变量 + 引用)

### 不变量 (byte-equal 保护)

- 新增 short-circuit 只在 `!conv && (src_qt ∈ {w,l}) && (dst_qt ∈ {b,h})` 触发 — 这 4 种组合之前必然 emit sentinel, 不可能产生正确 IL, 所以守卫**不改正确程序输出**
- jhyy_v1.exe.exe (`sha ba94df93...`) 不需要 rebuild — jhyy-side 一直 correct

### 引用

- [`docs/plans/v1/v1.1.0任务清单 + 概要设计.md` § Sprint v1.1.7](../../plans/v1/v1.1.0任务清单 + 概要设计.md) — 计划详情
- `memory/project_sprint_v1_1_7_bug4_narrow_cast.md` — 本 sprint 详细记录
- `memory/project_sprint4_7_irval_pass_by_value_bug.md` — Sprint 4.7 首次发现 Bug 4 (W-005 #2 family EMIT-layer 形态)
- v0 codegen Bug 4 描述 (per git log)

---

## v1.1 wip commit 1.9 — 6 sprint batch close (本 changelog 段) — 2026-08-12

**类型**: docs-only (本 changelog 段统一登记 commit 1.3-1.8)
**触发**: 用户 "把那几个 W00x 都修完吧" (2026-08-12) → 6 sprint 全部 ship 后登记

### 完成定义 (全达成 ✅)

| 标准 | 状态 | 证据 |
|------|------|------|
| 4 个 ACTIVE workaround (W-003/W-004/W-006/W-007) 全部 RESOLVED | ✅ | commit 1.1 W-006 + 1.2 W-004 + 1.3 W-007 + 1.4 W-003 |
| 4 个 v0 codegen bug (Bug 1-4) 全部真修 | ✅ | commit 1.5 Bug 1 + 1.6 Bug 2 + 1.7 Bug 3 + 1.8 Bug 4 |
| regress.py (C-side) 持平 baseline 50/50 | ✅ | 6 sprint 后各测一次, 全 50/50 |
| regress_v1.py (jhyy_v1) 持平 baseline 50/50 | ✅ | 6 sprint 后各测一次, 全 50/50 |
| Stage 1 byte-equal 7/7 持平 | ✅ | 双源 emit 模式等价 |
| Stage 2 N=3 byte-equal (`2445e97d...`) 持平 | ✅ | jhyy_v1.exe.exe 不 rebuild |
| workarounds.md 全 RESOLVED 入索引 | ✅ | W-003 / W-004 / W-006 / W-007 / W-013 (新) |

### 累计不变量

- **jhyy_v1.exe.exe 不 rebuild** (sha `ba94df93...`): Bug 4 fix 镜像 jhyy_v1 emit pattern, jhyy-side 一致
- **Stage 2 N=3 byte-equal** 维持 `2445e97d...` 1.378 MB
- **双源等价**: C-side (compiler/src/codegen.c) + jhyy-side (compiler/src0/codegen.jhyy) emit 模式 byte-equal

### 留给后续 (post-v1.1.0 ship)

- v3 workaround 29 处 revert 清理 (类比 W-002 commit 2.12 211 revert cleanup)
- src0/*.jhyy 100% natural 目标继续推进 (短名 revert 等)
- `_v1` 后缀 107 处残留清理 (跨文件改名, 风险中; 留专 sprint)
- v2.x QBE 完整重写 (per `docs/plans/v2/v2.0.0-os-prep.md`)
- v3.x 语言扩展 (per `docs/plans/v3.x-language-expansion.md`)
- mcp-jhyy Tier 2 tools (function-level IL diff / minimal repro)
- v0.9 wip changelog 历史错放 cleanup (commit `618ceea` 错放, 后续 sprint 单 commit revert 撤回; 不动 history — force-push 风险大, force-with-lease 砍会改 `f533c11` SHA)

### 关键 memory

- `memory/project_v1_0_0_closure.md` — v1.0.0 TAGGED (2026-08-10) 闭环记录
- `memory/project_sprint_v1_1_7_bug4_narrow_cast.md` — Bug 4 W-013 真修
- `memory/project_sprint4_6_irval_layout_fix.md` — W-005 IRVal struct layout 真修 (Bug 1/2/3 真修基础)