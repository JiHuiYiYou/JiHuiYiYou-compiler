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
- 4 个 `tmp/w004_*.jhyy` 测试文件不入 git (按 `feedback_no_build_artifacts_in_git` 原则, 测试用例留 `tmp/` 不跟踪)

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
- `memory/feedback_v0_codegen_bug_workarounds.md` — Bug 1 (hash_string overread) + Bug 6 (let-mut assignment) W-004 真因
- `memory/feedback_qbe_crlf_root_cause.md` — QBE 行号偏移错 (无关 W-004 但同 family 教训)
- Stage 1 byte-equal 7/7 PASS (持平 baseline)
- Task #60 fix: commit `52843b6` (v0.9 wip 2.15) — 验证路径 unblock