# Changelog — v1.7.0 (umbrella: gap + workaround 补全, 5 候选分多步走)

> **承接**: v1.6.0 shipped (spec 语法全覆盖 + 混合 test + W-053/W-054 fix).
> **目标**: 用 5 个候选 (W-055 pointer arith / UTF-8 char literal / EXPECT-ERROR runner / `_v135_inline_simple_recursive` STACK_OVERFLOW / Float suffix) 分多步走,不着急,先 ship Stage 1 + Stage 2 真的两段(其他 stage 推后续 sprint)。
> **scope**: per `docs/plans/v1/v1.7.0任务清单 + 概要设计.md` + 用户节奏决策(2026-08-27)。
> **本 umbrella 涵盖 2 已 ship 阶段**:Stage 1 EXPECT-ERROR runner + Stage 2 W-055 spec §9.5 pointer arithmetic。Stage 3-5 (UTF-8 char / STACK_OVERFLOW 真修 / Float suffix) 推后续 sprint。

---

## Sprint 状态总览

| Sprint 阶段 | 状态 | 摘要 |
|------------|------|------|
| **Stage 1** | ✅ done (commit `f8559eb` + `732ba4a`) | `mcp-jhyy/jhyy_regress.py` 加 EXPECT-ERROR 解析 + 5 个 underscore negative test 改名 (`null_untyped_err` / `sizeof_err_expr` / `sizeof_err_unknown` / `v137_or_diff_bind_err` / `for_in_slice_err`) |
| **Stage 2** | ✅ done (this commit) | **W-055 spec §9.5 pointer arithmetic 真修**: sema 加 `*T +/- int → *T` / `int + *T → *T` / `*T - *T → i64` 类型规则 + codegen emit pointer arith (const-fold NODE_INT + extsw w→l + mul sizeof(elem)) + `&NODE_INDEX` codegen 真修 (返地址非值) + 3 个诊断 test 进 default regress |
| Stage 3-5 | ⏸️ 推后续 | UTF-8 char / `_v135_inline_simple_recursive` STACK_OVERFLOW / Float suffix — 用户节奏决策"不着急" |

---

## 关键数字

| 指标 | v1.6.0 ship | v1.7.0 ship | Δ |
|------|------------|-------------|---|
| regress PASS (jhyy.exe) | 78/82 PASS + 4 SKIP | **86/86 PASS + 4 SKIP** | +8 PASS (-1 删 `_ptr_arith_limit.jhyy`) |
| regress PASS (jhyy_stage0.exe) | 78/82 PASS + 4 SKIP | **86/86 PASS + 4 SKIP** | +8 PASS |
| ACTIVE workaround 数 | W-055 ACTIVE | -1 (W-055 RESOLVED) | -1 |
| src/ src0 byte-equal closure | ✅ (Stage 2 闭环) | ✅ (Stage 2 闭环仍闭, jhyy_v2.il == v3.il == v4.il) | unchanged |
| 新 test 数 | — | 8 (Stage 1: 5 进 default, Stage 2: 3 进 default) | +8 |
| 删 test 数 | — | 1 (`_ptr_arith_limit.jhyy` — W-055 LIMIT 标记, RESOLVED 后无用) | -1 |

---

## Stage 1 — EXPECT-ERROR runner + 5 negative test promote (commits `f8559eb` + `732ba4a`)

### 完成定义

- ✅ `mcp-jhyy/jhyy_regress.py:159` + `:184-192` 加 EXPECT-ERROR 解析:
  - 解析 `// EXPECT-ERROR: "<substring>"` 注释
  - compile fail 时验 `r.stderr` (full, not truncated 200) 含 substring → PASS, 否则 FAIL (kw not found)
  - 保持现有 expected 路径不变, 向后兼容 78 个原 test
- ✅ 5 个 underscore negative test git mv + 加 EXPECT-ERROR 注释:
  - `null_untyped_err.jhyy` (sema "cannot infer type of `null`" 期望)
  - `sizeof_err_expr.jhyy` (parser error 期望)
  - `sizeof_err_unknown.jhyy` (sema "unknown type" 期望)
  - `v137_or_diff_bind_err.jhyy` (OR pattern sema 错期望)
  - `for_in_slice_err.jhyy` (sema "not iterable" 期望)
- ✅ 不碰 `compiler/build/bin/regress.py` (shim) + `mcp-jhyy/server.py` (parity 自动 follow, 改 1 处生效 2 处)

### 排查坑

- **stderr 截断 200 字符 bug**: 5 个 test FAIL 因 `[sema] P* ndeccls=N` 启动 log 把 errors 推到 200 字符后。修: kw check 走 `r.stderr` (full), display msg 仍 truncated 200
- **git rename 50% 阈值**: 4/5 test 相似度 31-49%, rename detection 默认 50% 失败。修: 拆 2 commit — commit 1 = 100% rename (5/5 detected), commit 2 = EXPECT-ERROR annotations

---

## Stage 2 — W-055 spec §9.5 pointer arithmetic 真修 (this commit)

### 完成定义

- ✅ `compiler/src/sema.c:438-475` + `compiler/src0/sema.jhyy:664-700` 加 TOKEN_PLUS/TOKEN_MINUS 分支前 pointer arith 类型规则:
  - `*T + int` / `*T - int` → `*T`
  - `int + *T` → `*T` (symmetry)
  - `*T - *T` (same elem) → `i64`
- ✅ `compiler/src/codegen.c:722-` + `compiler/src0/codegen.jhyy:1911-` NODE_BINARY case 加 pointer arith dispatch:
  - `*T +/- int`: offset = int * sizeof(elem) (const-fold NODE_INT → `ir_emit_copy` 直 emit `=l copy N`; else `extsw w→l` + `mul by elem_size`)
  - `int + *T`: symmetric
  - `*T - *T`: `byte_diff = sub left, right; result = div byte_diff, elem_size`
- ✅ `compiler/src/codegen.c:1242-` + `compiler/src0/codegen.jhyy:3169-` NODE_ADDR_OF NODE_INDEX 真修 (`&arr[i]` 返地址非值):
  - 跟 NODE_INDEX 计算路径对齐 (base + idx * sizeof(elem))
  - 之前 fall-through `return zero` 让 caller 拿到 IRVAL_INT 0 → 走 `add 0, off` segfault
- ✅ 3 个 diagnostic test 进 default regress:
  - `compiler/tests/examples/ptr_arith_basic.jhyy` — `*T + int` × 2 + `*r - *p - 10` → EXIT=10
  - `compiler/tests/examples/ptr_arith_diff.jhyy` — `*T - *T` + `d + 100i64` → EXIT=102 (强断言 d != 0)
  - `compiler/tests/examples/ptr_arith_subscript.jhyy` — `p[2]` → EXIT=30
- ✅ 删 `_ptr_arith_limit.jhyy` — W-055 LIMIT 标记, RESOLVED 后无用 (git rm)
- ✅ `docs/internal/workarounds.md:3663-` W-055 状态 ACTIVE → RESOLVED + 加 Resolution 段

### 已知限制 (Stage 2 不修, 推后续)

1. **mixed-width int promotion 不存在** — `i64 + i32` 仍 type mismatch。`d + 100` 在 ptr_arith_diff.jhyy 改成 `d + 100i64` 绕开 (test 备注) — 真修要 mixed-width promotion (per spec §6 待 verify)
2. **pointer comparison** `p < q` 不在 Stage 2 scope (spec §9.5 隐含但未明示, 推 v2.x)
3. **bounds check** — `*T +/- int` 不查越界, 需 `&mut` lifetime (v3.x) compile-time 拦截
4. **subscript `p[n]` 仅 `*T` 类型** — `[*]T` slice 已有 builtin `s[i]` 走 slice_get helper (per v1.6.0),不走 `p + n` 路径

### Jhyy-side codegen 同步坑 (Stage 2 排查记录)

1. **`A && (B || C)` pattern** — jhyy-side codegen 在 && RHS 含 || 时 phi predecessors 错配 (per Step 3 build break)。Stage 2 改写为 nested if (`A { if B || C { ... } }` 避免 `&&` with `||`)
2. **if-expression 含 let block** — jhyy parser 不允许 (`unexpected token 'let' in expression`)。Stage 2 改用 statement-level 单 branch if + 默认值 (`let mut r64 = right; if right.qbe_type != L { r64 = new_tmp; emit extsw }`)
3. **if/else 两 branch 末必须同 type** — jhyy sema 限制 (C 端无 — C 是 statement-level)。Stage 2 改用单 branch if 避免

### 验证 (5/5 PASS 必达 + Stage 2 byte-equal closure 保留)

| 验证项 | 结果 |
|--------|------|
| ptr_arith_basic.jhyy (`*T + int` × 2 + `*r - *p - 10`) | ✅ EXIT=10 (jhyy.exe + jhyy_stage0.exe 双 binary) |
| ptr_arith_diff.jhyy (`*T - *T` + `d + 100i64`) | ✅ EXIT=102 (强断言 d != 0) |
| ptr_arith_subscript.jhyy (`p[2]`) | ✅ EXIT=30 |
| full regress (jhyy.exe) | ✅ 86/86 PASS + 4 SKIP |
| full regress (jhyy_stage0.exe) | ✅ 86/86 PASS + 4 SKIP |
| Stage 2 N=3 byte-equal closure | ✅ jhyy_v1.il == v2.il == v3.il == v4.il sha `84645fd88474d5865959adcb7b467f83243800ff115665aca34a8cffd81ef7c9` |

---

## Stage 3-5 推后续 sprint (per 用户节奏决策 "不着急")

| Stage | 简述 | 启动时机 |
|-------|------|---------|
| **Stage 3** | UTF-8 char literal `'你'` (W-053 followup, 2-byte BMP only) | Stage 2 ship 后, user 拍板 |
| **Stage 4** | `_v135_inline_simple_recursive` STACK_OVERFLOW 真修 (diagnostic → fix) | Stage 2 ship 后 |
| **Stage 5** | Float suffix `f32`/`f64` (spec §4 待 verify) | Stage 2-4 ship 后 |

---

## 用户节奏决策 (2026-08-27)

按用户决策:
1. **按 stage 走** — 不再 5 stage 一次性 plan, Stage 详细 plan + 后续 stage 一行索引 (master)
2. **小步走** — 每 stage 拆 6-8 小步, 每步独立可 ship
3. **不跑全量 regress** — 改用: 单 test → 受影响 subset → baseline 用 `--save-baseline` 锁定, 只在最后 ship 前跑一次 `--all`
4. **小规划不写 docs/plans/** — 单 stage step-by-step plan 走 plan mode 或直接执行 (per `feedback_small_plans_no_docs.md`)

---

## 引用

- spec `docs/abis/jhyy-lang-spec-v1.1.0.md` § 9.5 (Pointer arithmetic — 权威)
- `docs/plans/v1/v1.7.0任务清单 + 概要设计.md` (master)
- `docs/internal/workarounds.md` W-055 RESOLVED 段
- `docs/logs/v1/changelog-v1.6.0.md` (前 ship)
- `feedback_small_plans_no_docs.md` (用户 2026-08-27 节奏决策)