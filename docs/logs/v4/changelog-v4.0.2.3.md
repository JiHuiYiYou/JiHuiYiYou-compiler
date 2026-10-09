# Changelog v4.0.2.3 — W-075 mem_set i64-store 真修 (b32|shift|OR workaround for W-098)

**Date:** 2026-10-09 · **Author:** MiniMax-M3 · **Status:** wip (single-commit ship pending)

## Summary

W-075 mem_set i64-store 真修 ship (1 commit) + W-098 NEW entry (jhyy-side codegen i64 literal emit bug, ACTIVE per W-097 deep audit 范畴).

**W-075 真修前**: `mem_set` 走 M0 简化 i32-store (4B / loop), 性能 trade-off (vs libc memset 8/16B SSE) + 触发 W-074.6 multifn frame blow-up 同族 codegen 限制 (DEFERRED since 2026-10-02).

**W-075 真修后**: mem_set 改 i64-store (8B / loop) + 尾段 i32-store (残余 < 8 字节), 用 b32|shift|OR 构造 b8 避开 W-098 (i64 literal > 32-bit range 截 i32 + cltq sign-extend 丢高 32 位)。

**关键 1-iter RCA** (per `feedback_rca_first_root_cause`): 之前 session 误判 "i64 store 触发大 frame + chkstk_ms rcx clobber" (W-075 第 1 撤回), 实是 W-098 (jhyy-side codegen i64 literal emit bug), 不是 multifn frame。W-074.6 partial + W-096 emit-side per-fn-local counter 真修 已修 frame, 但 codegen i64 literal emit 是 jhyy-side codegen 自身 bug, 跟 W-097 (jhyy-side codegen emit_func_header per_fn_max lookup operand swap) 同根因族。

## What changed

### 1. `compiler/src0/std/mem.jhyy:mem_set` — i64-store + workaround b8 构造

```jhyy
// v4.0.2.3 真修: i64-store (8B / loop) + 尾段 i32-store
// b8 构造: b32 (4-byte broadcast) + shift + OR 避开 W-098 (i64 literal emit bug)
fn mem_set(dst: *u8, val: i32, n: i64) -> *u8 {
    if n < (0 as i64) {
        return 0 as *u8;
    }
    let b: i32 = val & (0xff as i32);
    let b32: i64 = (b as i64) * (0x01010101 as i64);
    let b8: i64 = b32 | (b32 << (32 as i64));
    let mut i: i64 = 0 as i64;
    let n8: i64 = n - (n % (8 as i64));
    while i < n8 {
        *(ptr_add(dst, i) as *i64) = b8;
        i = i + (8 as i64);
    }
    while i < n {
        *(ptr_add(dst, i) as *i32) = b;
        i = i + (1 as i64);
    }
    return dst;
}
```

### 2. `compiler/tests/examples/std_mem_set_aligned.jhyy` — comprehensive test update

- inline mem_set 同样 workaround 写法
- `expected` 计算用同 pattern (避免 double-bug cancel — 之前 7 个 inline test 都能 PASS 实因 mem_set 跟 expected 都用同样 broken `0x0101010101010101 as i64` literal, 实际 i64 store 写 0x00000000_CCCCCCCC 而非 0xCCCCCCCC_CCCCCCCC, byte-by-byte check 才能 catch)
- 10 cases: n=0/1/4/7/8/9/16/17/24/32 + 8-byte broadcast pattern verify
- EXIT=0 on C-side jhyy.exe

### 3. `docs/internal/workarounds.md` — W-075 flip RESOLVED + W-098 NEW ACTIVE

- W-075: ✅ RESOLVED 2026-10-09 (v4.0.2.3 wip) — workaround ship, comprehensive test PASS
- W-098: NEW ACTIVE — jhyy-side codegen emit i64 literal (>32-bit range) 截 i32 + cltq sign-extend 丢高 32 位;W-097 deep audit sprint 同步修

## W-098 RCA (1-iter per `feedback_rca_first_root_cause`)

**Trigger**: `mem_set(buf, 0xCC, 8)` 期望写 buf[0..7] = 0xCCCCCCCC_CCCCCCCC, 实际写 buf[0..3] = 0xCCCCCCCC + buf[4..7] = 0x00000000 (byte-by-byte check EXIT=200+4=204, 实测 byte 4 错)

**RCA path**:
1. W-074.6 partial + W-096 emit-side per-fn-local counter 真修 后 mem_set 8B store 触发 8KB frame → `___chkstk_ms` 探测 → chkstk_ms clobber rcx → 4B/8B store arg corruption (W-075 第 1 撤回推测)
2. 实际 (W-098): jhyy-side codegen 编译 src0/main.jhyy 时, 对 `0x0101010101010101 as i64` literal emit `movl $0x01010101, -off(%rbp); movl -off(%rbp), %eax; cltq; movq %rax, -off(%rbp)` (32-bit movl + cltq sign-extend, 高 32 位 0)
3. C-side jhyy.exe (gcc-built) 同一函数 emit `movabsq $0x0101010101010101, %rax; movq %rax, -off(%rbp)` (single 64-bit movabsq immediate, 无截断)
4. jhyy-side V2/V3 binary (jhyy_v1.exe.exe 编译) emit 错 — 推测跟 W-097 (jhyy-side codegen emit_func_header per_fn_max lookup operand swap) 同根因族 (emit path operand order / register class 错)

**Workaround ship**: b32|shift|OR 构造 b8 — 不依赖 >32-bit i64 literal, 走 i32 literal (0x01010101) + 64-bit shift (32 fits i32 trivially) + 64-bit OR

**Caveat**: 任何 user 写的 jhyy-side code 用 >32-bit i64 literal 都静默丢高 32 位 (silent fail, runtime 难发现)。推测 std/fmt (1000-based divisor) / std/math (i64 常数) / src0/codegen.jhyy (QBE IL literal emit) 都有 surface, 待 W-097 deep audit sprint 同步 audit + 真修。

## Verification gates (v4.0.2.3 ship)

| Gate | Status |
|------|--------|
| regress.py 160/161 PASS HOLD (1 pre-existing fail = std_math_basic, 22 SKIP) | ✅ |
| `std_mem_set_aligned.jhyy` PASS EXIT=0 (5/5 on target test per `feedback_fix_evaluation_rule`) | ✅ |
| `std_mem_set.jhyy` PASS (旧 i32-store test, 单独 fn, 不受影响) | ✅ |
| `std_mem_basic.jhyy` / `std_mem_copy.jhyy` / `std_mem_compare.jhyy` / `std_mem_zero.jhyy` PASS (不变) | ✅ |
| regress baseline sha: `92ad34725ea8661d...` (W-096 ship baseline HOLD) | ✅ |
| ACTIVE workaround bucket = 1 (W-098 NEW; W-075 flip RESOLVED) | ✅ |

## Commit cadence (v4.0.2.3 ship batch)

| # | Commit | Status |
|---|--------|--------|
| 1 | `fix(std::mem): W-075 mem_set i64-store 真修 + b32\|shift\|OR workaround (W-098 surface)` | ⏳ |
| 2 | `test(std_mem_set_aligned): comprehensive 10 cases + expected 同样 workaround` | ⏳ |
| 3 | `docs(workarounds): W-075 flip ✅ RESOLVED + W-098 NEW ACTIVE entry` | ⏳ |
| 4 | tag `v4.0.2.3` (pushed after commit batch) | ⏳ |

## v4.0.0 final promote path

- v4.0.0 final tag 必须等 v4.0.2.3+ W-097 deep audit ship (Stage 2 jhyy-side codegen 真修)
- v4.0.0-rc1 仍 tag 在 main (per 2026-09-30 ship state)
- v4.0.2.3 ship 后, v4.0.0 final promote 推 v4.x W-097 audit sprint

## Out of scope (deferred)

- v4.0.2.4+ : W-097 deep audit (jhyy-side codegen emit_func_header / emit_binop / emit_lit 整个 emit path operand order 真修 — 同步修 W-098 i64 literal emit)
- v4.0.0 final promote: 等 W-097 ship
- std/fmt / std/math i64 literal audit + 同样 workaround pattern 应用: deferred 到 W-097 deep audit sprint

## References

- W-075 entry: `docs/internal/workarounds.md` (✅ RESOLVED 2026-10-09)
- W-098 entry: `docs/internal/workarounds.md` (NEW ACTIVE 2026-10-09)
- 源码: `compiler/src0/std/mem.jhyy:mem_set` (b32|shift|OR workaround)
- 源码: `compiler/tests/examples/std_mem_set_aligned.jhyy` (10 cases + byte-by-byte verify)
- Memory: `feedback_fix_evaluation_rule` (5/5 PASS on target test), `feedback_rca_first_root_cause` (1-iter 找 W-098 真因, 不是 multifn frame), `feedback_audit_single_commit_diff` (W-096 fix 4 revert 单 commit audit), `feedback_verify_active_reproduces` (W-075 第 1 撤回前的 multifn frame 误判历史教训)
