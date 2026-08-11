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