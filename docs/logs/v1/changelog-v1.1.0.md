# Changelog v1.1.0 — Workaround 真修 + Codegen Bug 真修

> **承接**: v1.0.0 TAGGED (commit `eabee0d`, 2026-08-10) + v0.9 wip commit 2.83 (style cleanup ship, 2026-08-11).
> **目标**: 4 个 ACTIVE workaround (W-003/W-004/W-006/W-007) + 4 个 v0 codegen bug (Bug 1-4) 全部真修.
> **当前 baseline**: regress_v1 50/53 + regress.py 50/53 + Stage 1 byte-equal 7/7 + Stage 2 N=3 byte-equal 维持.
> **Plan**: [`docs/plans/v1/v1.1.0任务清单 + 概要设计.md`](../../plans/v1/v1.1.0任务清单 + 概要设计.md)

---

## v1.1 wip commit 1.1 — W-006 RESOLVED (escaped) — 2026-08-11

**类型**: doc-only escaped (codegen fix deferred to v2.x)
**估时**: 0.1 sprint
**workarounds.md**: W-006 → RESOLVED

### 工作

- Re-scan `compiler/src0/*.jhyy` for `return X + Y` (X, Y 都是 1-char) 触发面:
  - `grep -rn 'return [a-z_]\{1,2\} [+\-] [a-z_]\{1,2\}' compiler/src0/*.jhyy` → 0 命中
  - `grep -rn 'return [a-z_]\{1,2\} [+\-\*/%] [a-z_]\{1,2\}' compiler/src0/*.jhyy` (broaden) → 0 命中
  - `grep -rn 'return \([a-z_]\{1,2\}\) [+\-] \([a-z_]\{1,2\}\)' compiler/src0/*.jhyy` (paren) → 0 命中
- 更新 `workarounds.md`:
  - § 索引 line 33: W-006 status ACTIVE (dormant) → RESOLVED (escaped)
  - § W-006 body: status field 同上
  - 新增 `## W-006 RESOLVED — v1.1 wip commit 1.1 doc-only escaped (2026-08-11)` section
- (no code change → regress / regress_v1 / stage1 byte-equal 自动持平)

### 决策

**为什么不真修就标 RESOLVED**:
- 当前 src0/ 触发面 = 0 命中 (2026-08-05 scan + 2026-08-11 re-scan 双重确认)
- 翻译风格已自然避免 — cast-chain / 单 operand / intermediate let 已是规范
- 根因 (codegen.c stack-slot allocator for ≤1-char vars) 修复涉及 stack frame 分配算法重写, scope 比 W-005/W-010 都大
- v1.1.x sprint 1-7 scope 聚焦 W-003/W-004/W-007 + Bug 1-4; W-006 根因修复留给 v2.x (QBE 重写时 stack frame 重设计一起做)

### 验证

- regress.py: 50/53 PASS (持平 baseline)
- regress_v1.py: 50/53 PASS (持平 baseline)
- Stage 1 byte-equal: 7/7 PASS (持平 baseline)
- 14 mcp-jhyy smoke test: PASS (持平 baseline)

### 不动

- `compiler/src/codegen.c` (无改动 — escape 策略)
- `compiler/src0/codegen.jhyy` (无改动)
- `compiler/src0/*.jhyy` (无改动 — src0/ 已自然避免)
- `compiler/tests/` (无改动)
- baseline (持平)

### 引用

- [`docs/internal/workarounds.md` § W-006](../../internal/workarounds.md) — 完整 W-006 entry + RESOLVED section
- [`docs/plans/v1/v1.1.0任务清单 + 概要设计.md` § Sprint v1.1.1](../../plans/v1/v1.1.0任务清单 + 概要设计.md) — 计划详情
- `memory/project_w006_dormant_scan_2026_08_05.md` — 2026-08-05 首次 dormant scan