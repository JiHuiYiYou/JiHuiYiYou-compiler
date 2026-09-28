# jhyy-lang-spec-floatsupplement-v3.3.0 — f32 / f64 spec 入口 (V3 ship 节点)

> **ship date**: 2026-09-28
> **branch**: `axis-v3`
> **D28 锁**: v3.3.0 ship = f32/f64 类型 + 算术 + ABI 全 ship
> **状态**: ✅ 已 ship (no-op verification,代码层面此前已在 v0.x / v1.7.0 / v3.0.7 / v3.1.0 各阶段 ship)
> **umbrella**: 本文件 = single-page 入口 (非 spec 修订)

---

## 1. 目的 / Purpose

v1.3.0 spec (主 spec 文件 `docs/abis/jhyy-lang-spec-v1.3.0.md`) 中 f32 / f64 相关 spec 内容**散落在多个章节**(跨 §2.6 / §4.2 / §5.6 / §11 / §16.6 / 附录 D + 附录 F 历史)。本补充 = **navigation aid**,给 v3.x 后续 sprint 设计和 v4.0.0 merge 提供 single-page 入口;**不修改主 spec**(per `feedback_doc_refactor_factcheck` 重构前 fact-check 原则)。

> **注意**:v1.7.0 Stage 5 changelog (commit `c04c546`) 引用 "spec §4.5 字面量族扩" 描述 Float suffix,但当前 v1.3.0 spec **§4.5 标题是"字符串字面量"**(L287);Float suffix 实际定义在 **§2.6 (L170-176)** + **§4.2 (L242-251)**。§4.5 引用是 v1.7.0 spec 版本的措辞,本 v1.3.0 spec 已重排 §4 为整数字面量 / 浮点字面量 / 布尔 / 字符 / 字符串 五节。

## 2. f32 / f64 spec 内容索引 (v1.3.0 spec 内 line refs)

| 主题 | v1.3.0 spec line | 内容摘要 |
|------|------------------|----------|
| 类型表 (f32 4B / f64 8B) | L111-112 | `f32` = 4 字节,`f64` = 8 字节,基础类型 (PRIM_F32 / PRIM_F64) |
| 类型推断 (默认 f64) | L156-157 | `let y = 3.14;` → `y: f64` (无后缀默认 f64) |
| 浮点字面量后缀 (§2.6) | L170-176 | `let a = 3.14;` → f64;`let c = 2.0e10f32;` → f32 |
| 浮点字面量 (§4.2) | L242-251 | `let pi = 3.14; let half = 0.5; let exp = 1.0e10; let tiny = 1e-5f32;` (L248 f32 suffix 例) |
| 类型转换 cast 表 (§5.6) | L374-381 | f32 ↔ f64 互转 + f32/f64 → i32/i64 行 + i32/i64 → f32/f64 列 |
| 类型转换 cast 例 (§5.6) | L386-403 | `let y: f64 = x as f64; let z: i64 = x as i64; let w: i32 = y as i32;` |
| 类型转换 cast 例 (§16.6) | L1064-1071 | `let f: f64 = 3.14; let i: i32 = f as i32; let big: i64 = i as i64; let back: f32 = big as f32;` |
| 浮点算术 codegen (§11, 附录 D v0.5.0) | L1372 | `+ - * /` 使用 `adds`/`subs`/`muls`/`divs` (f32) 和 `addd`/`subd`/`muld`/`divd` (f64) |
| Float suffix ship 历史 (附录 F v1.7.0 Stage 5) | L1695 | commit `c04c546` (2026-08-28) — `1.0f32` / `1.0f64` / `1.0f` 显式后缀 |

## 3. f32 / f64 codegen / ABI ship 锚点 (V3 self-backend)

| 文件 | 锚点 | 内容 |
|------|------|------|
| `compiler/src0/types.jhyy` | L140-204 | `f32_ty` / `f64_ty` (TypeArena 12 prims) + `PRIM_F32()` / `PRIM_F64()` |
| `compiler/src0/lexer.jhyy` | L373-449 | `lex_scan_number` 内 `is_float = 1` 分支 + `f32` / `f64` suffix 解析 (`1.0f32` / `1.0f64` / `1.0f`) |
| `compiler/src0/codegen.jhyy` | L959-985 | `QBE_S_LOCAL` / `QBE_D_LOCAL` 双分支 + `dtosi` / `stosi` / `sitod` / `uitos` 整数↔浮点转换 |
| `compiler/src0/codegen.jhyy` | L1422-1448 | f32 / f64 字面量 (`s_<val>` / `d_<val>`) QBE emit |
| `compiler/src0/codegen.jhyy` | L2274-2281 | `ceqs` / `cnes` / `ceqd` / `cned` 浮点比较 emit |
| `compiler/src0/abi_amd64_sysv.jhyy` | L42-159 | `SYSV_CLASS_SSE` for f32 / f64 (SysV § A.4 8-class) |
| `compiler/src0/codegen_amd64_emit_call.jhyy` | L71-72 | `import codegen_amd64_emit_sse` + `import codegen_amd64_xmm_argalloc` (XMM reg alloc) |
| `compiler/src0/codegen_amd64_emit_call.jhyy` | L503-504 | "f32 / f64 (QBE_S / QBE_D) return 用 %xmm0 + movss / movsd" |
| `compiler/src0/codegen_amd64_emit_call.jhyy` | L672-674 | `xmm_arg_reset` (XMM arg alloc reset per call) |

## 4. f32 / f64 测试覆盖 (V3 regress 内)

7+ 浮点测试全部 PASS (per `python regress.py --binary=compiler/build/bin/jhyy.exe` 151/151 PASS / 0 FAIL / 20 SKIP):

| 文件 | 内容 | 验证 |
|------|------|------|
| `compiler/tests/examples/f32_suffix.jhyy` | `2.5f32` + suffix parse + f32 → i32 cast | EXIT=0 |
| `compiler/tests/examples/f64_suffix.jhyy` | `3.14f64` + suffix parse + f64 → i32 cast | EXIT=0 |
| `compiler/tests/examples/float_arith.jhyy` | `1.5 + 2.5 * 2.0 = 6.5 → 6` (f64 precedence) | EXIT=6 |
| `compiler/tests/examples/float_arith_f32.jhyy` | f32 算术独立 (1.5f32 + 2.5f32 * 2.0f32) | EXIT=6 |
| `compiler/tests/examples/float_cmp.jhyy` | `ceqs` / `cnes` / `ceqd` / `cned` 比较 | EXIT=... |
| `compiler/tests/examples/float_test.jhyy` | 综合浮点操作 (let / cast / arith / cmp) | EXIT=... |
| `compiler/tests/examples/fmod_f32.jhyy` | user-space fmod 真修 (W-083 v2.13.11 / V3 v3.0.6 mirror) | EXIT=... |

## 5. Ship 历史 (V3 axis)

f32/f64 **不是 v3.3.0 一次性 ship**;是**逐阶段 ship**:

| 阶段 | commit | 内容 |
|------|--------|------|
| v0.x (pre-tag) | (历史) | `PRIM_F32()` / `PRIM_F64()` 引入 + `f32_ty` / `f64_ty` lazy init |
| v1.7.0 Stage 5 | `c04c546` (2026-08-28) | lexer `is_float = 1` 分支 + `f32` / `f64` suffix 解析 (`compiler/src0/lexer.jhyy:373-449`) |
| v2.11.19 Phase 1-5 | (v2 axis 5 commit) | lexer tokenize 8 conversion op → emit_conv_* SSE2 → f32 IMM + f64 fractional → FNARG XMM bug → emit_load/store 浮点路径 xmm0 scratch + ss/sd |
| v2.13.0/Ph.1 | `5d405bb` | 真 XMM regalloc (W-074.6 PARTIAL → FULL CLOSED) |
| v2.13.0/Ph.2 | `b1ad5c3` | 真 amd64_sysv codegen 全覆盖 — 8-class §A.4 + SSE class for f32/f64 (`abi_amd64_sysv.jhyy:42-159`) |
| v2.16.0 | `0b4cde5` | QBE toolchain removed + byte-equal .exe (v2.x FINAL) |
| v3.0.6/Ph.3 | `68b4b48` | src0 codegen_amd64 self-backend conversion family (W-083 Layer 1 + W-086 defer v3.0.7) |
| v3.0.7/Commit 1 | `886eaea` | V3 self-backend W-086 wholesale 真修 Layer 2+3 (cltq + op_len + ILTOK_CONV=80 + emit_conv 2-op form) |
| v3.0.7/Commit 3 | `fc49cd2` | land emit_sse.jhyy + xmm_argalloc.jhyy 跟 V2 v2.16.0 byte-equal (pure add, NO wiring) |
| v3.1.0/Ph.1 | `0d9c527` | wholesale port V2 v2.16.0 src0 self-backend + W-089 V3 stdlib pointer-flag extension |
| **v3.3.0** (本次 close-out) | **`a82fb57`** (current HEAD, +doc only) | **no-op verification + tag `v3.3.0`** (代码层无新增) |

## 6. v3.2.5 (math libm FFI) D28 硬前置解除

**v3.3.0 ship = v3.2.5 启动条件满足**:
- ✅ `f32` / `f64` 类型已 ship (types.jhyy L140-204)
- ✅ f32 / f64 字面量 + suffix 已 ship (lexer.jhyy L373-449)
- ✅ 浮点算术 / 比较 / cast 已 ship (codegen.jhyy L959-985 / L1422-1448 / L2274-2281)
- ✅ f32 / f64 作函数参数 + 返回值已 ship (abi_amd64_sysv.jhyy L42-159 + emit_call.jhyy L71-72 / L503-504)

**v3.2.5 内容**(per `docs/plans/v3/v3.2.5-plan.md`):`std::math::sin` / `cos` / `sqrt` / `pow` / `fmod` 等 libm FFI wrapper。**D28 硬前置 (f32/f64 类型) 已 ship** — v3.2.5 现在可启动,不再 block。

## 7. Cross-ref

- 主 spec: `docs/abis/jhyy-lang-spec-v1.3.0.md` (本文件不修改)
- V3 umbrella: `docs/logs/v3/changelog-v3.3.md` (本文件 ship umbrella)
- V3 plan: `docs/plans/v3/v3.3.0-plan.md` (status ⏳ → ✅)
- 下游 v3.2.5: `docs/plans/v3/v3.2.5-plan.md` (D28 硬前置解除)
- ABI: `docs/abis/jhyy-abi-v1.0.0.md` (struct pass-by-value / FFI / 多文件 / 切片 — float ABI 引用 jhyy-lang-spec-floatsupplement)
- M11 launch gate: `docs/plans/v2/v2.0.0-os-prep.md § 1 M11` (3h 浮点 ship 节点)
- v4.0.0 fold-in: `docs/plans/roadmap/v2-v3-parallel-sprint-plan.md § 5.1` (V2 + V3 converge)

## 8. 备注 (不修改主 spec 的理由)

1. **§4.5 标题 = "字符串字面量"** (v1.3.0 spec L287)。v1.7.0 Stage 5 changelog 引用 "§4.5 字面量族扩" 是 v1.7.0 spec 版本的措辞;v1.3.0 已重排 §4 为五节 (整数 / 浮点 / 布尔 / 字符 / 字符串)。Float suffix **在 §2.6 + §4.2**。
2. **Float suffix 定义跨多节**:§2.6 = 后缀语法 (L170-176);§4.2 = 完整字面量族 + 默认 f64 (L242-251)。两者并存,**修改任何一节都会破其他节引用** (per `feedback_doc_refactor_factcheck` 重构前 fact-check)。
3. **codegen / ABI 内容**在 §11 / 附录 D + abi.md,**跟 spec 主体分离**。本补充 = single-page 入口,**避免改 §4.5 标题 (会破 append-only changelog 引用)**。
4. **v4.0.0 merge 时**:如需彻底重排 §4 + §5 spec,推 v4.x scope (跟 jhyy_OS 跨项目 spec 整合一起改);v3.3.0 close-out 只做 navigation aid。