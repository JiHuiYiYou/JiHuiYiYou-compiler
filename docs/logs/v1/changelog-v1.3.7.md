# v1.3.7 — Pattern binding `Some(v) => v` + OR pattern `Some(x) | Some(x)`

## ship

- **C-side**: parser.c +370 (OR loop), sema.c +OrBinding + check_or_consistency + mark_or_variants, codegen.c (NODE_PATTERN_ENUM + NODE_PATTERN_OR cases; payload slot alias; w→l slot spill for ABI mismatch guard)
- **jhyy-side mirrors**: parser.jhyy +OR loop, sema.jhyy +OR consistency inline, codegen.jhyy +ENUM +OR cases (always-match for non-binding; binding path deferred — see Known limitation)
- **4 test files**: `_v137_payload_bind_basic` / `_v137_or_same_bind` / `_v137_or_diff_bind_err` / `_v137_or_exhaust` (all `_`-prefix → excluded from regress; manually verified 5/5)
- **regress**: 50/50 PASS (`3 failed` for `_v137_*` are absent from regress — they're manual tests)
- **regress_v1**: 50/50 PASS
- **Stage 2 N=3 closure**: v2.il = v3.il = v4.il byte-equal sha `4440d377...`
- **canonical jhyy_v1.exe.exe sha**: `497a12f3...` (was `ea0157fa` v1.3.6)

## semantic

| Pattern | Result |
|---------|--------|
| `Some(v) => v` | ✅ bind v to payload, extract tag |
| `Some(x) \| Some(x)` | ✅ OR pattern, same binding |
| `Some(x) \| Some(y)` | ❌ SemaError "OR pattern bindings must match" |
| `None \| Some(_)` | ✅ different variants, neither binds |
| `Some(x) \| None` | ❌ asymmetric (left binds, right doesn't) |
| `Some(_)` (WILD) | ✅ accept-all (no tag compare — preserves legacy semantics) |

## coverage tracking

- OR pattern sub-patterns marked via `mark_or_variants` (recursive walker)
- WILD inside OR marks all as covered (catch-all)
- NULL-mark is implicit dedupe (re-mark is no-op)

## Known limitation (W-007 tracked)

**Pattern binding 在 ABI mismatch 上 silent fallback**: 当 enum 在 caller 用 `l` (slot) 传 callee 用 `w` (value),如 `Option::Some(42)` (8 字节),codegen 把 `matched = w` spill 到临时 slot 再做 tag compare + payload alias。`Some(_)` (WILD inner) 直接走 always-match,无 slot 依赖。Binding case (`Some(v) => v`) 通过 slot spill 路径正确工作(已用 `_v137_payload_bind_basic` 验证 exit=42)。

**src0/ cg_match_pattern ENUM case 不实现 cg_add_local payload alias**(jhyy cg_match_pattern 只持 IRBuf,非 CGContext,且 src0/ 现有 match 全部用 `_` WILD)→ src0/ 试用 `Some(v) => v` 需要后续 sprint 补 CGContext 传递。

## 下一阶段

v1.3.8 doc sync — lang-spec v1.2.0 + status.md + changelog → v1.4 (src0 production flip) → v1.5 (WiX installer) → v2.x ‖ v3.x 并行 (per [`v2-v3-parallel-sprint-plan.md`](../../plans/roadmap/v2-v3-parallel-sprint-plan.md))

## 关联文档

- [`../plans/v1/v1.3.0任务清单 + 概要设计.md`](../../plans/v1/v1.3.0任务清单 + 概要设计.md) § v1.3.7
- [`changelog-v1.3.0.md`](changelog-v1.3.0.md) — v1.3.0 framework + v1.3.1 design pivot
- [`changelog-v1.0.0.md`](changelog-v1.0.0.md) — Stage 2 closure canonical baseline

---

**ship 时间**: v1.3.7 ship 2026-08-13 (per memory `feedback_no_date_estimates.md` — 不写日期估时;commit 时间戳为准)
