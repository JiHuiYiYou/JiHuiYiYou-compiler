# v1.3.7 (W-007 fix) — Large enum param ABI mismatch

## ship

- **C-side**: codegen.c — `cg_func` param declaration + param copy use `l` (slot pointer) for enums with `total_size > 4`, mirroring `KIND_STRUCT` handling
- **jhyy-side mirror**: codegen.jhyy — same fix in `cg_func` param emit
- **regress**: 50/50 PASS
- **regress_v1**: 50/50 PASS

## before / after

**Before** (W-007 known limitation):
```
%t25 =l alloc8 8          (caller builds slot)
...
%t31 =w call $unwrap_or(l %t25, w %t26)   (caller passes slot)
export function w $unwrap_or(w %opt, ...)  (callee declares w!)
       ^^^ mismatch — x86_64 SysV reads %edi (low 32 bits of %rdi)
```

**After** (W-007 fixed):
```
%t25 =l alloc8 8          (caller builds slot)
...
%t31 =w call $unwrap_or(l %t25, w %t26)   (caller passes slot)
export function w $unwrap_or(l %opt, ...)  (callee declares l)
       ^^^ matched — both sides use slot pointer
```

## semantic

| Enum size | ABI | Use case |
|-----------|-----|---------|
| ≤ 4 bytes | `w` (value) | tag-only enum, no payload |
| > 4 bytes | `l` (slot pointer) | enum with payload (e.g. `Option::Some(i32)`) |

W-007 only affects the > 4 bytes case. Small enums (rare in practice) continue to use `w`.

## Self-hosting impact

- v1.il = v2.il = `7c5ca427...` (new C-built canonical)
- v3.il = v4.il = `aefa3bb3...` (jhyy-built chain stable)
- v2.il ≠ v3.il — pre-existing C-side vs jhyy-side divergence (redundant copies in C-side codegen). 已知 issue per v1.3.6 changelog (W-005 #2 chain products). Not caused by W-007 fix.

## 关闭 W-007

The `W-007` workaround (w→l spill in `cg_match_pattern` ENUM case) is now defensive — `matched` is always `l` for binding patterns (since binding requires payload, which requires `total_size > 4`). Kept the spill guard for safety but it's a no-op in practice.

Mark W-007 as RESOLVED in `docs/internal/workarounds.md`.

## 下一阶段

W-007 fix 完成。继续 v1.3.8 doc sync (lang-spec v1.2.0 + status.md + changelog) → v1.4 src0 production flip → v1.5 WiX installer → v2.x ‖ v3.x 并行 (per [`v2-v3-parallel-sprint-plan.md`](../../plans/roadmap/v2-v3-parallel-sprint-plan.md)).

## 关联文档

- [`changelog-v1.3.7.md`](changelog-v1.3.7.md) — v1.3.7 parent ship (pattern binding + OR pattern)
- [`changelog-v1.3.0.md`](changelog-v1.3.0.md) — v1.3.0 framework + v1.3.1 design pivot

---

**ship 时间**: 2026-08-13 (W-007 fix run, post v1.3.7 ship)
