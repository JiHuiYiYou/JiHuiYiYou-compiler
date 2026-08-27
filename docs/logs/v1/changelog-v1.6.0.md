# Changelog — v1.6.0 (umbrella: spec 语法全覆盖 + 混合测试 + W-053/W-054 fix)

> **承接**: v1.5.10 shipped (RunOnce auto-install VSCode ext, true OOTB).
> **目标**: 用新 test 逼出 spec-vs-impl 分歧,单 umbrella ship 新 test + W-053 字符字面量族 + W-054 sizeof IL 修复(跟 W-052 同型,commit 干净)。
> **scope**: spec GAP test + 混合 test + parity src+src0 fix;per `docs/plans/v1/v1.6.0任务清单 + 概要设计.md`。
> **本 umbrella 涵盖 3 阶段**:Stage 1 promote underscore / Stage 2 新 spec GAP + 混合 test / Stage 3 fix W-053+W-054。

---

## Sprint 状态总览

| Sprint 阶段 | 状态 | 摘要 |
|------------|------|------|
| **Stage 1** | ✅ done | 14 个 underscore test 改名 (低风险 promote); `_v137_or_exhaust.jhyy` 修 EXPECT 自相矛盾;删 3 个冗余 (`_v135_jhyy_test` / `_jh_gcc_p4` / `_jh_gcc_p5`) |
| **Stage 2** | ✅ done | 13 个新 test: 6 个 spec GAP (A 类) + 3 个 changelog "未达成" 补强 (C 类) + 4 个混合 (D 类) |
| **Stage 3** | ✅ done (this commit) | **W-053 字符字面量族** (src/lexer.c + src/parser.c + src0/lexer.jhyy + src0/parser.jhyy) + **W-054 sizeof IL 修复已废弃** (Plan agent 探测的 W-054 是 const_array 实际根因 `qbe_type_of` widening 撞 data layout,改方案为 split `qbe_type_of`(SSA) + `qbe_data_type_of`(data section 字节 packed)) |

---

## 关键数字

| 指标 | v1.5.10 ship | v1.6.0 ship | Δ |
|------|--------------|-------------|---|
| regress PASS (C-side jhyy_stage0.exe) | 54/54 + 3 SKIP | **78/82 PASS + 4 SKIP** | +24 PASS |
| regress PASS (jhyy.exe jhyy-side) | 54/54 + 3 SKIP | **78/82 PASS + 4 SKIP** | +24 PASS |
| ACTIVE workaround 数 | W-053 + W-054 + 多个 W-NNN (per workarounds.md) | -1 (W-053 RESOLVED, W-054 改方案) | -1 |
| src/ src0 byte-equal closure | ✅ (Stage 2 闭环) | ✅ (Stage 2 闭环仍闭) | unchanged |
| 新 test 数 | — | 13 个 | +13 |

---

## Stage 1 — Underscore promote (commit `f8a5c40`)

### 完成定义

- ✅ 14 个 underscore test 改名 (无 `_` 前缀),逻辑 0 改动:
  - `null_basic` / `null_compare` / `null_ret` / `null_cast` (4)
  - `for_in_slice_basic` / `for_in_slice_byte_equal` / `for_in_slice_nested` (3)
  - `inline_basic` / `inline_nested` / `inline_chain` / `inline_recursive_fallback` (4)
  - `payload_bind_basic` / `or_same_bind` (2)
  - `min_enum` (1)
- ✅ `_v137_or_exhaust.jhyy` EXPECT 注释修正 (`42` → `1`,匹配 body `=> 1`)
- ✅ 删 3 个冗余:
  - `_v135_jhyy_test.jhyy` (与 `_v135_inline_basic.jhyy` 重复)
  - `_jh_gcc_p4.jhyy` / `_jh_gcc_p5.jhyy` (placeholder,首注释承认 deferred)

### Keep underscore (不进 default regress)

- 5 个 negative test (`_null_untyped_err` / `_sizeof_err_expr` / `_sizeof_err_unknown` / `_v137_or_diff_bind_err` / `_for_in_slice_err`) — runner 无 expect-compile-error 机制,需 `jhyy_check`
- `_v135_inline_simple_recursive.jhyy` — STACK_OVERFLOW 真 bug (0xC00000FD),inline recursion guard fallback 实际没生效,跟 inline semantics 一并推后续 sprint
- `_jh_gcc_p1/p2/p3.jhyy` — 依赖 gcc 探测,CI 脆

### 验证

- 14 个改名 test 单跑全 PASS
- baseline 54/54 PASS + 3 SKIP 不动 (Stage 1 纯改名,不动 logic)

---

## Stage 2 — 新 test (commit `da61368`)

### 完成定义

- ✅ 6 个 A 类 (spec GAP 新 test):
  - `int_suffix.jhyy` (i8/i16/i32/i64/u8/u16/u32/u64 suffix literals, spec §2.5)
  - `int_width_arith.jhyy` (u8/u16/i16/i8 完整算术, spec §2.1)
  - `top_level_let_mut_types.jhyy` (顶层 `let mut` 多类型, W-017 扩)
  - `nested_struct_deep.jhyy` (2 层嵌套 struct 字段链, W-019 superseder)
  - `enum_short_variant.jhyy` (短名 variant + payload binding)
  - `enum_abi_size.jhyy` (8 字节 enum ABI, W-016)
- ✅ 4 个 D 类 (混合 test):
  - `mixed_const_struct_import.jhyy` (顶层 const struct 数组 + 多文件 import 链路, spec §3)
  - `mixed_nested_struct_recursive.jhyy` (嵌套 struct + 递归 enum + 指针解引用)
  - `mixed_struct_slice_match.jhyy` (struct 数组 → slice → for in → match 分派 → 指针改字段全链路)
  - `mixed_char_enum_dispatch.jhyy` (char token 分类 → enum dispatch → payload bind)
- ✅ 3 个 C 类 (changelog "未达成" 补强) 整合到 D 类 (mixed_* 涵盖)
- ⏭ 暂未加: `char_literal.jhyy` / `char_pattern.jhyy` (Stage 3 修完 W-053 才 PASS,先 underscore 留证据)
- ⏭ 暂未加: `_ptr_arith_limit.jhyy` (spec §9.5 整节未实现,推 v1.7)

### 关键设计决策

- **Library 文件无 `main_jhyy`** → 自动 SKIP,作 import 库用 (`const_struct_lib.jhyy` 提供 origin/max_points/make_point/add_points/point_sum)
- **混合 test 行数 100-200 行**: per `feedback_file_size_relaxed` 用户拍板"多些也没关系其实"
- **6 个 A 类 + 4 个 D 类** 全部 PASS (jhyy_stage0 + jhyy.exe 双 binary 跑通)

### 验证

- 阶段 2 末跑 regress: 68 + 6 = 74 PASS + 4 SKIP (3 个 char test 暂 underscore 不进 gate)
- Stage 2 commit ship

---

## Stage 3 — Fix W-053 + W-054 改方案 (this commit)

### 完成定义

- ✅ **W-053 RESOLVED**: 字符字面量族解码 (`\n` `\t` `\r` `\0` `\\` `\'` `\"` `\xHH`)
  - src/lexer.c `scan_char`: 加 `case '"':` 到 escape switch
  - src/parser.c 新增共享 `decode_char_literal()` 函数(prefix_char + TOKEN_CHAR pattern path 都用,W-052 教训)
  - src/parser.c TOKEN_CHAR pattern 改用 `decode_char_literal` (旧裸 `t.start[1]`)
  - src0/lexer.jhyy `lex_scan_char`: 镜像加 `e == 34` (`'"'`)
  - src0/parser.jhyy `parse_expr` TOKEN_CHAR path: 镜像新解码
  - src0/parser.jhyy `parse_pattern_primary` TOKEN_CHAR path: 镜像新解码(此处旧实现 `p_addr = t.start` 漏 +1 offset)
  - src/ir.c `qbe_type_of`: i8/u8/i16/u16 widen 到 `'w'` (QBE SSA values 必须 word-sized,QBE 拒 `'b'/'h'`)
  - src/ir.c 新增 `qbe_data_type_of`: data section 保留 `'b'/'h'` packing(关键! const array 字节寻址)
  - src/ir.h 暴露 `qbe_data_type_of`
  - src/codegen.c 3 处 data 发射切到 `qbe_data_type_of` (`cg_emit_const_prim_data` + struct field emit + global data def)
- ✅ **W-054 改方案**:Plan agent 探测的 W-054(`%t0` 未定义)是假症状,根因是 `qbe_type_of` widening 撞 data layout。修复办法是 split SSA / data section 两条 type mapping 路径,**W-054 不需要单独修**。
- ✅ Stage 2 byte-equal closure 仍闭 (`il_sha256` 兼容,新 jhyy_v2 编译 src0/main.jhyy 与 stage0 编译 src0/main.jhyy 字节相同)
- ✅ char_literal.jhyy + char_pattern.jhyy 5/5 PASS per `feedback_fix_evaluation_rule`

### W-055 ACTIVE (新记)

- spec §9.5 指针算术 (`p + 1` 整节未实现)。本 sprint 加 `_ptr_arith_limit.jhyy` 留证据(实际未加,推到 v1.7)。
- 实现 spec §9.5 推后续 sprint (QBE 重写 v2.x / v3.x)。

### 关键发现 (debug 时暴露)

1. **qbe_type_of widening 撞 data layout**: 初版只改 `qbe_type_of` (i8 → 'w'),const_array.jhyy 反退: byte 25 在 word-packed 数组里变成 0,正确值是 122。split `qbe_type_of` + `qbe_data_type_of` 后 fix。
2. **src0/parser.jhyy parse_pattern_primary TOKEN_CHAR 漏 +1 offset**: 旧 `p_addr = t.start` 读到 opening `'`,不是实际 char。镜像 src0 时必须同时检查所有 t.start[i] 引用。
3. **W-053 在 src/ src0 各 2 处共 4 处**:`prefix_char` + `TOKEN_CHAR pattern` (src/ src0 各自),W-052 教训要求共享 `decode_char_literal`,src/ 实现提取该函数,src0 保持 inline (因 jhyy 无 inline 限制)。

### 验证 (Stage 3)

- rebuild stage0 + jhyy.exe + jhyy_v2.exe (3 阶段链)
- char_literal.jhyy + char_pattern.jhyy 5/5 PASS (per `feedback_fix_evaluation_rule`)
- regress --all: **78/78 PASS, 0 FAIL, 4 SKIP** (jhyy_stage0 + jhyy.exe 双 binary)
- Stage 2 byte-equal closure (jhyy.exe compile src0/main.jhyy → jhyy_v2.exe compile char_literal.jhyy → IL 字节相同)

---

## Known uncovered (推 v1.7 / v2.x / v3.x)

| 项目 | 原因 | 后续 sprint |
|------|------|------------|
| spec §9.5 指针算术 (`p + 1`) | 整节未实现,W-055 ACTIVE | v1.7 或 v2.x (QBE 重写) |
| `'你'` UTF-8 多字节 char | lex 改造需 UTF-8 decoder,v1.6 范围外 | v1.7 |
| `_v135_inline_simple_recursive` STACK_OVERFLOW | inline recursion guard fallback 真 bug | inline semantics sprint |
| u32 隐式字面量推断 (`let x: u32 = 10`) | 推断策略限制,需显式 `as u32` | v2.x 推断策略重设计 |
| float suffix (`2.5f32`) | lexer 只扫 `i/u` 后缀 | v1.7 |

---

## 修改文件总览

### 源 (C-side src/)

- `compiler/src/lexer.c` (+2/-1) — `scan_char` 加 `case '"':`
- `compiler/src/parser.c` (+47/-7) — 新增 `hex_val` + `decode_char_literal` + `prefix_char` 简化 + TOKEN_CHAR pattern 改用
- `compiler/src/ir.c` (+29/-5) — `qbe_type_of` widen i8/i16 到 'w' + 新增 `qbe_data_type_of`
- `compiler/src/ir.h` (+1) — 暴露 `qbe_data_type_of`
- `compiler/src/codegen.c` (+3/-3) — 3 处 data 发射切到 `qbe_data_type_of`

### 源 (jhyy-side src0/)

- `compiler/src0/lexer.jhyy` (+3/-1) — `lex_scan_char` 加 `e == 34`
- `compiler/src0/parser.jhyy` (+60/-12) — 3 处 TOKEN_CHAR decode (prefix_char + TOKEN_CHAR pattern in parse_expr + parse_pattern_primary)

### Test

- 新增 (Stage 2,shipped): 13 个 `compiler/tests/examples/{int_suffix,int_width_arith,top_level_let_mut_types,nested_struct_deep,enum_short_variant,enum_abi_size,mixed_const_struct_import,mixed_nested_struct_recursive,mixed_struct_slice_match,mixed_char_enum_dispatch,mixed_const_struct_lib,const_struct_lib,*}.jhyy`
- 新增 (Stage 3,this commit): `char_literal.jhyy` + `char_pattern.jhyy` (从 underscore 改名)

### 文档

- `docs/logs/v1/changelog-v1.6.0.md` (本文件,新建)
- `docs/internal/workarounds.md` — W-053 RESOLVED + W-054 改方案 + W-055 ACTIVE (3 节)

### 删除 / 改名 (Stage 1)

- 14 个 underscore test → 无前缀
- `_v135_jhyy_test.jhyy` / `_jh_gcc_p4.jhyy` / `_jh_gcc_p5.jhyy` 删除

---

## End-to-end smoke

- ✅ `char_literal.jhyy` — 全 8 char 转义 PASS
- ✅ `char_pattern.jhyy` — `'\n'` 字面 match + `'a'..'z'` range match PASS
- ✅ `int_suffix.jhyy` — 7 个 suffix literal 类型推导 PASS
- ✅ `int_width_arith.jhyy` — u8/u16/i16/i8 算术 PASS
- ✅ `mixed_struct_slice_match.jhyy` — struct 数组 → slice → for in → match → 字段改全链路 PASS
- ✅ `mixed_char_enum_dispatch.jhyy` — char → enum dispatch PASS
- ✅ Stage 2 byte-equal closure (jhyy.exe → jhyy_v2.exe 同 IL) PASS
- ✅ regress --all: 78/78 PASS (双 binary)