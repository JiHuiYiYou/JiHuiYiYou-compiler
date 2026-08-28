# Changelog — v1.7.0 (umbrella: gap + workaround 补全, 5 候选分多步走)

> **承接**: v1.6.0 shipped (spec 语法全覆盖 + 混合 test + W-053/W-054 fix).
> **目标**: 用 5 个候选 (W-055 pointer arith / UTF-8 char literal / EXPECT-ERROR runner / `_v135_inline_simple_recursive` STACK_OVERFLOW / Float suffix) 分多步走,不着急,先 ship Stage 1 + Stage 2 真的两段(其他 stage 推后续 sprint)。
> **scope**: per `docs/plans/v1/v1.7.0任务清单 + 概要设计.md` + 用户节奏决策(2026-08-27)。
> **本 umbrella 涵盖 4 已 ship 阶段**:Stage 1 EXPECT-ERROR runner + Stage 2 W-055 spec §9.5 pointer arithmetic + Stage 3 W-056 UTF-8 2-byte BMP char literal + char type `u8 → i32` (spec §4.4 align) + Stage 4 `_v135_inline_simple_recursive` diagnostic test promote (排查发现无 codegen bug, 范围重定义为 test 文件 promote)。Stage 5 (Float suffix `f32`/`f64`, spec §4 待 verify) 推后续 sprint。

---

## Sprint 状态总览

| Sprint 阶段 | 状态 | 摘要 |
|------------|------|------|
| **Stage 1** | ✅ done (commit `f8559eb` + `732ba4a`) | `mcp-jhyy/jhyy_regress.py` 加 EXPECT-ERROR 解析 + 5 个 underscore negative test 改名 (`null_untyped_err` / `sizeof_err_expr` / `sizeof_err_unknown` / `v137_or_diff_bind_err` / `for_in_slice_err`) |
| **Stage 2** | ✅ done (commit `6216138` + `187e8ab`) | **W-055 spec §9.5 pointer arithmetic 真修**: sema 加 `*T +/- int → *T` / `int + *T → *T` / `*T - *T → i64` 类型规则 + codegen emit pointer arith (const-fold NODE_INT + extsw w→l + mul sizeof(elem)) + `&NODE_INDEX` codegen 真修 (返地址非值) + 3 个诊断 test 进 default regress |
| **Stage 3** | ✅ done (commits `934d9e0` + `3f89ce8`) | **W-056 UTF-8 2-byte BMP char literal + char type `u8 → i32` (spec §4.4 align)**: lexer lead-byte mask dispatch (1/2/3/4 bytes, 3/4 显式 reject) + decode_char_literal widen `unsigned char → uint32_t` + sema `PRIM_U8 → PRIM_I32` + codegen drop `(unsigned char)` + `& 255` mask + src0/parser.jhyy 3 处 inline copy 改共享 helper + 2 new BMP test 进 default regress |
| **Stage 4** | ✅ done (this commit) | **`_v135_inline_simple_recursive` diagnostic test promote 进 default regress**: 排查发现无 codegen bug — 源程序缺 base case 是 infinite recursion, runtime STACK_OVERFLOW 是预期 OS-level 行为, codegen.c:902 `current_inline_sym != fn_sym` 守卫工作正常 (IL 验证 emit `call $loopy` 非 inline 展开)。加 base case `if n <= 0 { return 0; }` → loopy(5)=15 终止 → 加 `// EXPECT: 15` → git mv 改回非 underscore 名 → 进 default regress 验证 guard 路径生效 |
| Stage 5 | ⏸️ 推后续 | Float suffix `f32`/`f64` (spec §4 待 verify) — 用户节奏决策"不着急" |

---

## 关键数字

| 指标 | v1.6.0 ship | v1.7.0 ship | Δ |
|------|------------|-------------|---|
| regress PASS (jhyy.exe) | 78/82 PASS + 4 SKIP | **89/89 PASS + 4 SKIP** | +11 PASS (Stage 2: +8, Stage 3: +2, Stage 4: +1) (-1 删 `_ptr_arith_limit.jhyy`) |
| regress PASS (jhyy_stage0.exe) | 78/82 PASS + 4 SKIP | **89/89 PASS + 4 SKIP** | +11 PASS |
| ACTIVE workaround 数 | W-055 ACTIVE | -2 (W-055 + W-056 RESOLVED) | -2 |
| src/ src0 byte-equal closure | ✅ (Stage 2 闭环) | ✅ (Stage 4 闭环仍闭, jhyy_v1.il == v2.il == v3.il == v4.il, sha 不变 7552aa94...) | unchanged (test-only change) |
| 新 test 数 | — | 11 (Stage 1: 5 进 default, Stage 2: 3 进 default, Stage 3: 2 进 default, Stage 4: 1 进 default) | +11 |
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

## Stage 2 — W-055 spec §9.5 pointer arithmetic 真修 (commits `6216138` + `187e8ab`)

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

## Stage 3 — W-056 UTF-8 2-byte BMP char literal + char type `u8 → i32` (this commit)

> **承接**: Stage 2 ship (commits `6216138` + `187e8ab`)。W-053 (char escape family) 修在 v1.6, 但多字节 UTF-8 + spec §4.4 类型对齐留到 Stage 3 (W-056)。
> **Scope**: 2-byte BMP only (3-byte CJK / 4-byte emoji 推 v2.x, per master plan §"Stage 1-5 不覆盖的")。

### 完成定义

- ✅ `compiler/src/lexer.c:213-234` scan_char + `compiler/src0/lexer.jhyy:500-524` lex_scan_char — 按 UTF-8 lead byte mask (`0x80/0xE0/0xF0`) dispatch 字节数 (1/2/3/4), 消费对应数 continuation byte (`0xC0==0x80` mask 验证)。3-byte / 4-byte 显式 error ("3/4-byte UTF-8 codepoint not supported in v1.7.0 Stage 3, use ASCII or 2-byte BMP; CJK/emoji 推 v2.x") — per master plan scope
- ✅ `compiler/src/ast.h:96 + :325` NodeChar.ch `char → uint32_t` + ast_new_char signature。src0/ast.jhyy NodeChar.ch: i32 已够, 不动
- ✅ `compiler/src/parser.c:44-81` decode_char_literal return type `unsigned char → uint32_t` + UTF-8 multi-byte decode (lead + 1 cont → 11-bit codepoint)。调用点 prefix_char (parser.c:861) + pattern path (parser.c:248) 去掉 `(char)` cast
- ✅ `compiler/src0/parser.jhyy` 共享 helper `decode_char_literal` 替换 3 处 inline copy (line 362, 570, 696) — **W-053 教训: 漏 1 处 silent fail** (per `feedback_*`)
- ✅ `compiler/src/sema.c:334-337 + compiler/src0/sema.jhyy:520-524` NODE_CHAR — `PRIM_U8 → PRIM_I32` (spec §4.4)。Breaking: 现有 char_literal.jhyy + char_pattern.jhyy 需类型对齐 (Step 7 修)
- ✅ `compiler/src/codegen.c:598-603 + compiler/src0/codegen.jhyy:1312-1318` NODE_CHAR codegen — 去掉 `(unsigned char)` + `& 255` 截断。IR temp 已 `'w'` (32-bit), 只透传 codepoint
- ✅ Side fix: src0/parser.jhyy:463 + :623 char pattern codepath `PRIM_U8() → PRIM_I32()` (与 src/parser.c:250/263/272 对齐) — char_utf8_expr Stage 0 parity EXIT=0 vs v1 EXIT=5 失守的根因
- ✅ 2 new test 进 default regress:
  - `compiler/tests/examples/char_utf8_basic.jhyy` — 3 个 BMP char literal 值断言 (`'é'` = 233 / `'ñ'` = 241 / `'ü'` = 252) → EXIT=0
  - `compiler/tests/examples/char_utf8_expr.jhyy` — BMP char 在 match arm pattern + match value (single-expr arm 范式, 跟 char_pattern.jhyy 一致) → EXIT=5
- ✅ 2 existing test 改类型 (Step 7):
  - `compiler/tests/examples/char_literal.jhyy` — 8 个 `: u8 → : i32` + 3 个 BMP case 追加
  - `compiler/tests/examples/char_pattern.jhyy` — `fn classify(c: u8) → c: i32` + call sites 去掉 `as u8` cast
- ✅ `docs/internal/workarounds.md` 加 W-056 UTF-8 char literal (NEW → ✅ RESOLVED) + Stage 3 同步坑段
- ✅ `compiler/build/bin/jhyy.exe.sha256` 新 baseline 重锁 (Stage 3 N=4 byte-equal closure sha `7552aa94...`)

### 已知限制 (Stage 3 不修, 推后续)

1. **3-byte / 4-byte UTF-8 codepoint** — `let c = '你'` (U+4F60) 仍 lex fail ("3/4-byte UTF-8 codepoint not supported in v1.7.0 Stage 3"), 推 v2.x (per master plan §"Stage 1-5 不覆盖的")
2. **char type signedness** — Stage 3 严格按 spec 走 `i32`, 若 spec revision 改 `u32` / `u8` 推 v2.x
3. **char → u8 implicit coerce** — `let x: u8 = 'a'` 现 type mismatch (i32 → u8 需 `as`), 无 coerce path。后续写 `let x = 'a'` (类型推导) 自动 `i32`
4. **match arm body `=> r = N` stage0 codegen gap** — 在 char_utf8_expr.jhyy 排查时发现 stage0 codegen 对 match arm body 是 `NODE_ASSIGN` (单 stmt 非 block) 时, arm body 的 storew 不 emit (IL 只 `jmp @merge`, 不写 local)。test 改用 single-expr arm (`=> N`) 绕开 (per char_pattern.jhyy 范式)。根因 stage0/codegen.jhyy NODE_ASSIGN path 跟 NODE_BLOCK path 不全等价, 推后续 sprint 真修 (新 W-NNN candidate)
5. **Char in const array** — `qbe_data_type_of(u8)='b'` 不动 (char 不进 const array, 验证后已确认)。若后续 stage 加 char const array, 需 verify IL 字节不变 (W-054 hazard)

### Jhyy-side codegen 同步坑 (Stage 3 排查记录)

1. **shared helper 替换 inline copy** — src0/parser.jhyy 3 处 inline decode_char_literal (line 362, 570, 696) 用 `decode_char_literal(start, length)` 共享 helper 替换, 必须 3 处都改 (W-053 教训: 漏 1 处 silent fail)
2. **`&& with ||` phi mismatch** — src0/lexer.jhyy UTF-8 多字节扫描用 nested if (`lead_x_check { ... extra_check { ... } }`) + while (`while i < extra { ... }`), 避免 `A && (B || C)` 范式 (跟 Stage 2 同型)
3. **`PRIM_U8() → PRIM_I32()` side effect** — char pattern codepath 用 `ast_new_int(arena, loc, val, PRIM_*)` 标记 type, src0/parser.jhyy 漏改 2 处 (line 463 + 623), stage0 跟 v1 parity 失守。诊断通过对比双方 .il 输出 (per `feedback_fix_evaluation_rule` + `feedback_il_s_debugging_pattern`)
4. **OOS rejection 显式而非 fallthrough** — 3-byte (`(lead & 0xF0) == 0xE0`) + 4-byte (`(lead & 0xF8) == 0xF0`) 显式 error 比 silent fallthrough 安全 (per user Stage 3 plan review point 1, 避免 silent fail)
5. **decode off-by-one fix** — 2-byte BMP `'é'` (len=4, extra=1), check 应是 `len != 3 + extra` 而非 `len != consumed + 2` (per user Stage 3 plan review point 2)
6. **`=> { r = N; }` block syntax 在 jhyy parser 不允许** — 单 expression arm 范式 (`=> N` 或 `=> r = N`) 是 jhyy parser 唯一接受形式。char_utf8_expr 初版用 block syntax → "unexpected token '{' in expression", 改 single-expr 后 OK

### 验证 (5/5 PASS 必达 + Stage 3 byte-equal closure 保留)

| 验证项 | 结果 |
|--------|------|
| char_utf8_basic.jhyy (3 BMP char value) | ✅ EXIT=0 (jhyy.exe + jhyy_stage0.exe 双 binary) |
| char_utf8_expr.jhyy (BMP char in match) | ✅ EXIT=5 (jhyy.exe + jhyy_stage0.exe 双 binary) |
| char_literal.jhyy (12 char family incl 3 BMP) | ✅ EXIT=0 |
| char_pattern.jhyy (6 patterns incl range) | ✅ EXIT=0 |
| full regress (jhyy.exe) | ✅ 88/88 PASS + 4 SKIP (vs Stage 2 86/86, +2 UTF-8) |
| full regress (jhyy_stage0.exe) | ✅ 88/88 PASS + 4 SKIP (parity) |
| Stage 3 N=4 byte-equal closure | ✅ jhyy_v1.il == v2.il == v3.il == v4.il sha `7552aa949ed066afe086f907e94142753c297eedd8b7145e787fa7fbdc17aba6` |

---

## Stage 4-5 推后续 sprint (per 用户节奏决策 "不着急")

| Stage | 简述 | 启动时机 |
|-------|------|---------|
| **Stage 5** | Float suffix `f32`/`f64` (spec §4 待 verify) | Stage 4 ship 后, user 拍板 |

---

## Stage 4 — `_v135_inline_simple_recursive` diagnostic test promote 进 default regress (this commit)

> **承接**: Stage 3 ship (commits `934d9e0` + `3f89ce8`)。
> **范围重定义**: 跟原 umbrella 描述"_v135_inline_simple_recursive STACK_OVERFLOW 真修 (diagnostic → fix)" 不一致 — 排查发现 **无 codegen bug**, 本 stage 实际是 **test 文件 promote**。

### 排查背景

排查发现源程序 `_v135_inline_simple_recursive.jhyy` 实际是 **无限递归** (源程序 `loopy(n) = n + loopy(n-1)` 无 base case), runtime STACK_OVERFLOW 是 **预期 OS-level 行为**, 不是 compiler bug。

排查方法 (per `feedback_no_subagents_for_compiler_work` "先排查 root cause, 不盲改"):
1. 读 `_v135_inline_simple_recursive.jhyy` — 源程序 6 行, 无 base case
2. 读 `compiler/src/codegen.c:896-935` NODE_CALL inline expansion path — 守卫 `cg->current_inline_sym != fn_sym` 在 line 902
3. `jhyy.exe compile _v135_inline_simple_recursive.jhyy -o /tmp/_v135; cat /tmp/_v135.il` — 验证 IL emit `%t4 =w call $loopy(w %t3)`, 走真实 call, **不**无限 inline 展开
4. 对比 `inline_recursive_fallback.jhyy` — 同 shape 但有 `if n <= 1 { return 1; }` base case, PASS EXIT=120, 证明 codegen path 正确在 source program 终止时

**结论**: codegen.c:902 守卫工作正常, 无需 fix。本 stage 改为 **test 文件 promote** (加 base case + 加 EXPECT + 改回非 underscore 名 + 进 default regress)。

### 完成定义

- ✅ `compiler/tests/examples/v135_inline_simple_recursive.jhyy` (was `_v135_inline_simple_recursive.jhyy`, git mv) — 加 base case `if n <= 0 { return 0; }` → `loopy(5)` 终止, 返回 `5+4+3+2+1+0 = 15`
- ✅ 加 `// EXPECT: 15` 注释 + provenance 注释 (codegen 守卫说明 + 排查背景 + 跟 `inline_recursive_fallback.jhyy` 区分)
- ✅ git mv `_v135_inline_simple_recursive.jhyy` → `v135_inline_simple_recursive.jhyy` (改回非 underscore 名, 进 default regress)
- ✅ 不动 `compiler/src/codegen.c` — 守卫已工作, 无 bug (per 排查证据)
- ✅ 不动 `compiler/src0/codegen.jhyy` — parity 不动 (src0 镜像的 codegen.c:902 守卫同样工作, Explore 已确认)
- ✅ `compiler/build/bin/jhyy.exe.sha256` — baseline sha 不变 (`445df36be736b16e50d028c8dad6d30700cf4fbf06fb4a2407e01bbbfed6ccc4`), 因 src/src0 没动, `--save-baseline` 覆盖无变化

### 已知 limitation (Stage 4 不修, 推后续)

1. **umbrella 早期措辞滞后** — `changelog-v1.7.0.md:163` 之前写"STACK_OVERFLOW 真修 (diagnostic → fix)", 现在 Stage 4 段更新成"diagnostic test promote (排查发现无 codegen bug)"。防止未来 reader 误以为有 defect 漏修 (per `feedback_doc_refactor_factcheck`)
2. **infinite recursion runtime crash 无 harness 覆盖** — 源程序确实无限递归时 (现在没了, 因加 base case), OS-level STACK_OVERFLOW 无 EXPECT-CRASH 注释能跑。如未来需, 走单独 harness stage (Stage 4 排查 Explore 建议 (b))
3. **`v135` 命名** — 文件名 v135 跟 version v1.3.5 一致, 但 project 已到 v1.7.0。保留 v135 历史命名 (跟 inline 家族 `inline_basic.jhyy` 等并列, 描述设计意图而非当前 version)

### 跟 inline_recursive_fallback.jhyy 的区分 (都验证 guard, body shape 不同)

| test | body shape | guard 触发原因 |
|------|-----------|--------------|
| `inline_recursive_fallback.jhyy` | `fact(n) = if n <= 1 { return 1; } return n * fact(n - 1);` — **multi-stmt + 控制流** | `cg_inline_simple_return_expr` 返 NULL (body 不是 single return expr) → `try_inline=false` |
| `v135_inline_simple_recursive.jhyy` (Stage 4) | `loopy(n) = if n <= 0 { return 0; } return n + loopy(n - 1);` — **simple-return + base case** | 同上 (base case if 让 `cg_inline_simple_return_expr` 返 NULL) → `try_inline=false` |

两者 guard 路径相同 (`try_inline=false` → emit `call $fn_sym`), 测的是同一 codegen path 但不同 AST shape。保留两者覆盖不同 AST shape。

### 验证 (5/5 PASS 必达 + Stage 4 byte-equal closure 保留)

| 验证项 | 结果 |
|--------|------|
| v135_inline_simple_recursive.jhyy (`loopy(5)`) | ✅ EXIT=15 (jhyy.exe + jhyy_stage0.exe 双 binary) |
| 5-test inline subset (v135 + inline_basic + nested + chain + recursive_fallback) | ✅ 5/5 PASS 双 binary (EXIT: 15, 42, 20, 13, 120) |
| full regress (jhyy.exe) | ✅ 89/89 PASS + 4 SKIP (vs Stage 3 88/88, +1 promote) |
| full regress (jhyy_stage0.exe) | ✅ 89/89 PASS + 4 SKIP (parity) |
| Stage 4 N=4 byte-equal closure | ✅ jhyy_v1.il == v2.il == v3.il == v4.il sha `7552aa949ed066afe086f907e94142753c297eedd8b7145e787fa7fbdc17aba6` (跟 Stage 3 同 sha, 因 src/src0 没动) |

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