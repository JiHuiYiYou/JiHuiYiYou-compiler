# jhyy-lang-spec-stdlib-math-supplement-v3.2.5 — std::math FFI libm (M0, f64-only)

> **ship date**: 2026-09-28
> **branch**: `axis-v3`
> **D28 锁**: v3.2.5 ship = v3.x 关键路径 (OS-required) 完整 ship;M11 launch 硬前置解锁条件之一
> **umbrella**: 本文件 = std::math 模块 spec 补充 (跟 main `docs/abis/jhyy-lang-spec-v1.3.0.md` 不修改)

---

## 1. 模块清单 / Module Inventory

| 模块 | 文件 | LOC | 内容 |
|------|------|-----|------|
| `std/math.jhyy` | `compiler/src0/std/math.jhyy` | ~75 | 4 extern decls (sin/cos/sqrt/pow) + 4 `std_math_*` wrappers + module doc |

## 2. 设计约束 / Design Constraints

- **M0 f64-only**: f32 variants 推 v3.x 中;f64 covers default literal type (`2.5` not `2.5f32`)。
- **Option A direct extern**: 不走 C-side bridge;V3 self-backend 已 verified f64 ret codegen (`compiler/src0/codegen_amd64_emit_call.jhyy:502-506` + L873-886,f32/f64 ret 用 %xmm0 + movss/movsd,SysV/Win ABI 一致)。QBE-era `jh_f64_store / jh_double_to_bits` bridge pattern post-QBE moot (per `git rm qbe/` commit `6ae2d7c` v3.1.0/Ph.3)。
- **No cross-module imports**: `std/math.jhyy` 独立 module,不 import `std/io.jhyy` 等 (per W-077 root cause 跨模块 import 不稳)。
- **`std_math_*` 前缀**: W-076 命名约定 + W-091 catch-all `std_` prefix 覆盖 std_math_* returns(但本模块 fn 全返 f64 不返 pointer,W-091 over-flag 无副作用)。
- **libm linkage**: `-lm` 已 in link line (per `main.jhyy:1201` + `jhyy_helpers.c:424` comment);MSVCRT (Windows) 把 `sin/cos/sqrt/pow` 编译为 gcc 内置;POSIX `gcc` 走 `-lm` 链 `libm.so`。两个平台 bit-pattern agreement 在 1e-9 tolerance 内。

## 3. API Detail

| 签名 | 语义 | libm 调用 |
|------|------|-----------|
| `fn std_math_sin(x: f64) -> f64` | sin(x) (radian) | `sin` |
| `fn std_math_cos(x: f64) -> f64` | cos(x) (radian) | `cos` |
| `fn std_math_sqrt(x: f64) -> f64` | √x ≥ 0;NaN if x < 0 | `sqrt` |
| `fn std_math_pow(base: f64, exp: f64) -> f64` | base^exp (general exponentiation) | `pow` |

### 边界行为 / Edge Behavior (libm IEEE 754 标准)

| 输入 | std_math_sin | std_math_cos | std_math_sqrt | std_math_pow |
|------|--------------|--------------|---------------|--------------|
| 0 | +0 | 1 | 0 | base^0 = 1 (any base) |
| +∞ | NaN | NaN | +∞ | +∞ (exp > 0) / 0 (exp < 0) / 1 (exp = 0) |
| -∞ | NaN | NaN | NaN | (-∞)^exp = NaN / +∞ (exp < 0 + odd int) |
| NaN | NaN | NaN | NaN | NaN |
| sqrt(-1) | — | — | NaN (no exception) | — |

**注意**: libm 无 exception 机制;`errno` 不置 (per C99 + POSIX)。User 需自己处理 NaN/Inf (用 f64 bit pattern cast 或 `f64 > X` 比较)。

## 4. Known Limits

- ❌ **No f32 versions**: 推 v3.x 中 (实际 user case 出现再加);f32 variant 用 `%xmm0` + `movss` 路径,V3 self-backend 已 verified clean (`emit_call.jhyy:502-506`) 但 regress 缺位覆盖。
- ❌ **No tan / log / exp / floor / ceil / fabs / atan2 / asin / acos / atan**: 推 v3.x 中;上述都是 libm 标准函数,加 fn = 加 4-8 LOC wrapper,但 regress 需 +sub-test。
- ❌ **No NaN / Inf explicit handling**: libm 返回 NaN/Inf 是 IEEE 754 标准行为;wrapper-level 拦截会改语义 (跟 libm 默认行为冲突)。
- ❌ **No domain error reporting**: `sqrt(-1)` → NaN (no exception), `pow(0, 0)` → 1 (C99 libm behavior);errno 不置。
- ❌ **No SIMD math**: SIMD intrinsic (`_mm_sin_ps` 等) 推 v3.x 末,需要 codegen 新增 path。
- ❌ **No high-precision math**: libm 是 IEEE 754 double precision (≈15-17 位有效数字);extended precision (`long double` 80-bit) 推 v4.x。

## 5. Tests

| 测试 | 覆盖 |
|------|------|
| `compiler/tests/examples/std_math_basic.jhyy` | 6 sub-test (sin(0)/cos(0)/sqrt(4) bit-exact + sqrt(2)/pow(3,0.5) delta 1e-9 + pow(2,10) bit-exact) |

### 测试策略

- **Bit-exact** (sub-test 1/2/3/5): cast f64 → i64 比较位 pattern;verify libm 输出跟 IEEE 754 spec 一致 (`sin(0) = +0`、`cos(0) = 1`、`sqrt(4) = 2.0`、`pow(2,10) = 1024`)。
- **Delta 1e-9** (sub-test 4/6): MSVCRT ↔ glibc libm agreement 在 1e-9 tolerance 内,无 false-positive。

### Caveat: parser literals

V3 self-backend parser (`compiler/src0/parser.jhyy`) **不支持 `1e-9` scientific notation 数字字面量 inline in fn arg position**(per `lexer.jhyy` lex_scan_number 分支;经验证 `let eps: f64 = 1e-9;` 单独 statement 可解析但 `nearly_eq(a, b, 1e-9)` arg 位置触发 `unexpected token`)。Workaround: extract 到 local var `let eps: f64 = 0.000000001;` 再传入 fn arg。

## 6. Cross-ref

- L2 设计: `docs/plans/v3/v3.2.5-plan.md`
- Umbrella: `docs/logs/v3/changelog-v3.2.md` v3.2.5 section (append)
- D28 锁链前置: `docs/plans/v3/v3.3.0-plan.md` (✅ ship 2026-09-28, 解锁 math)
- f32/f64 type ship: `docs/abis/jhyy-lang-spec-floatsupplement-v3.3.0.md`
- M11 launch gate: `docs/plans/v2/v2.0.0-os-prep.md § 1 M11`
- v4.0.0 fold-in: `docs/plans/roadmap/v2-v3-parallel-sprint-plan.md § 5.1`
- Workarounds: 无新 W-NNN (W-080 covers i32 ret;W-089 ACTIVE 但 std_math_* 不触发 — 全 f64 ret 不返 pointer;W-091 catch-all `std_` prefix 已覆盖 std_math_* returns)
- Codegen 锚点: `compiler/src0/codegen_amd64_emit_call.jhyy:502-506` (f32/f64 ret) + `compiler/src0/codegen_amd64_emit_sse.jhyy` (SSE helpers) + `compiler/src0/abi_amd64_sysv.jhyy:42-159` (SysV SSE class)