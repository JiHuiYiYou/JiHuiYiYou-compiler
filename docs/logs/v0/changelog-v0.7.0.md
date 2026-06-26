# JHYY v0.7.0 Changelog

## 版本目标

**v0.7 把语言本身再打磨一层**，为 v1.0.0 self-hosting 减少 workaround 数量。

本版本分三个 sprint：
- **7A enum first-class**：enum 现在是真正可用的语言特性（exhaustiveness + 短名 variant pattern）
- **7B const struct array**：（独立 sprint）
- **7C docs sync**：lang-spec / ABI 追更 + changelog 收尾

本文档只覆盖 7A。7B / 7C 见后续 changelog。

---

## Sprint 7B: const struct array

### 7B.1 lexer: TOKEN_CONST

**改动**：`compiler/src/lexer.h/c` 加 `TOKEN_CONST` + keyword `"const"`。

`const` 作为保留关键字，与 `let` / `type` / `fn` 并列。

### 7B.2 AST + symtab: NODE_CONST_DECL + SYM_CONST

**改动**：
- `compiler/src/ast.h/c` 新增 `NODE_CONST_DECL` + `NodeConstDecl { sym, type_annot, init }`
- `compiler/src/symtab.h` 新增 `SYM_CONST`（与 `SYM_VAR` / `SYM_FN` / `SYM_TYPE` 并列）

`SYM_CONST` 走 global scope，与 `const` 顶层声明一一对应。

### 7B.3 parser: parse_const_decl

**改动**：`compiler/src/parser.c` 新增 `parse_const_decl()`，`parse_decl` dispatch 加 `TOKEN_CONST → parse_const_decl`。

语法：`const NAME: [T; N] = [elem, elem, ...];`

只支持顶层 const（不支持函数体内 const）。元素必须是字面量 / struct-literal / 其他 const 引用（`is_const_expr()` 检查，sema 层）。

### 7B.4 sema: NODE_CONST_DECL case

**改动**：`compiler/src/sema.c` `case NODE_CONST_DECL`

- **Pass 1（register）**：parse 后立即注册 sym 进 global scope，让后续 decl 能引用
- **Pass 3（check bodies）**：解析 `[T; N]` 类型、validate init 是 `NODE_ARRAY_LIT` 且长度匹配、每个 elem 调 `is_const_expr(elem)`
  - 字面量（INT / FLOAT / BOOL / STR）→ 是 const
  - struct-literal → 是 const（前提是所有 field value 也是 const）
  - `SYM_CONST` 引用 → 是 const
  - 函数调用 / ident-ref-to-mutable / 等 → 报错
- 限制：elem 类型不能是 POINTER / SLICE / ENUM（指针常量 + 运行时 enum tag 需要 RTTI，超出 7B 范围）

**错误格式**：
```
const_non_literal.jhyy:15:31: error: const array element must be a const expression (literal, struct literal, or another const reference)
1 semantic error(s)
```

### 7B.5 codegen: data section emit + QBE DYNCONST load

**改动**：`compiler/src/codegen.c` `cg_module()` Pass A 新增 const decl 处理 + `cg_expr NODE_IDENT` SYM_CONST 分支。

**Emit 形式**（QBE IL）：
```qbe
data $ASCII_LOWER = { b 97, b 98, ..., b 122 }
export function w $main_jhyy() {
@start0
    %t0 =l copy $ASCII_LOWER
    %t1 =l copy 1
    %t2 =l add %t0, %t1
    %t3 =w loadub %t2
    ret %t3
}
```

**关键点**：
- `data $NAME = { ... }` —— QBE 把整个数组放到 .data 段（rodata，0-cost load）
- `$NAME` 是 QBE 的 DYNCONST（first-class value），用 `=l copy $NAME` 直接拿到数组地址，**不需要** `addr $NAME`（QBE 不支持）
- struct 数组平铺字段：`data $PALETTE = { w 1, w 2, w 3, w 4, w 5, w 6, w 7, w 8, w 9 }`（3 个 RGB × 3 个 i32 = 9 个 word）
- 元素类型 → QBE 类型映射：`u8 → b`、`u16 → h`、`i8 → b`、`i16 → h`、`i32 → w`、`i64 → l`、`f32 → s`、`f64 → d`
- 嵌套 array-of-array 在 7B 范围外（sema 拒绝）

**`ir.h/c`**：`ir_emit_data()` 公开（之前是 static），让 codegen 能 emit data section 到 `data_buf`（在 function emit 之前 flush）。

### 7B.6 codegen: 修 pre-existing arr_of_structs[i].field bug

**改动**：`compiler/src/codegen.c` `cg_expr NODE_INDEX` + `cg_emit_store`

**bug**：`let arr: [RGB; 3] = ...; arr[i].field` 之前会 codegen 出 `loadw` 在 struct 起始地址上，但 struct 是 12+ 字节，`loadw` 只读 4 字节，QBE 报"invalid type for first operand in add/loadsw"。

**根因**：
1. `NODE_INDEX` 不分 elem 类型，无脑 `loadw elem_size bytes` —— 对 struct elem 是错的（struct 大小 ≠ 4）
2. `cg_emit_store` 对 struct 走 `storew` 只存 4 字节（一个 word，恰好是 struct 的 stack-slot 地址），array slot 里存的根本不是 struct 值而是指针

**修法**：
1. `NODE_INDEX`：elem 是 struct 时直接返回 address（struct 值 = 地址，匹配 `NODE_DEREF` 语义）
2. `cg_emit_store`：elem 是 struct 时调 `cg_copy_struct(dst_addr, src_addr)` 字段级拷贝（QBE 没有 aggregate store 指令）

**附带修复**：`cg_emit_load` 之前 sub-word 类型返回 'b' / 'h'，但 QBE 的 `loadub` / `loadsb` / `loaduh` / `loadsh` 返回 word ('w')。改返回 'w' 匹配 sub-word → word cast。

**测试**：`tests/examples/struct.jhyy` / `struct_val_*.jhyy` / `big_test.jhyy` 全部 PASS（无回归）。

### 7B.7 测试

1. `tests/examples/const_array.jhyy`（positive）：`const ASCII_LOWER: [u8; 26] = [97..122]`，`ASCII_LOWER[25] as i32` → EXIT=122
2. `tests/examples/const_struct_array.jhyy`（positive）：`const PALETTE: [RGB; 3] = [...]`，`PALETTE[2].b` → EXIT=9
3. `tests/examples/_const_non_literal.jhyy`（negative，`_` 跳过 regress）：`const BAD: [i32; 1] = [compute()]` → 手动编译报"const array element must be a const expression" + exit=1

---

## Sprint 7C: docs sync

### 7C.1 lang-spec v1.0.0 → v1.1.0

**改动**：`docs/abis/jhyy-lang-spec-v1.0.0.md`

新增章节：
- **§11.3 enum match 穷尽性**（v0.7 7A）：enum match 必须覆盖所有 variant，否则编译错误。短名 variant pattern `Some(v)` / `None` 是语法糖，等价于 `Option::Some(v)` / `Option::None`
- **§13 顶层 const 数组**（v0.7 7B）：语法 `const NAME: [T; N] = [elem, ...];`，元素必须是 const 表达式（字面量 / struct-literal / 其他 const 引用）。codegen emit 到 QBE `.data` 段

版本号：v1.0.0 → **v1.1.0**（新增 §11.3 + §13，旧章节未改）

附录 B 状态更新：
- "enum match 无穷尽性检查" → 移到"已修复"列表
- "缺少 const 数组声明" → 移到"已修复"列表

### 7C.2 status.md v0.6.5 → v0.7.0

**改动**：`docs/internal/status.md`

- 当前版本：v0.6.5 → **v0.7.0**
- 已实现特性新增：
  - enum match 穷尽性检查（7A）
  - 短名 variant pattern（7A）
  - 顶层 const 数组声明（7B）
- 已知限制更新：
  - 移除 "enum match 无穷尽性检查" / "缺少 const 数组声明"
  - 新增 "Pattern binding codegen 提取 payload"（7A 后续 sprint）

### 7C.3 v1.0.0 plan 更新

**改动**：`docs/plans/v1/v1.0.0任务清单 + 概要设计.md`

"不在 v1.0 范围"表新增"Pattern binding codegen"（phase-2 启动后 patch）+ "嵌套 const array / const fn / 编译期求值"（phase-3+ 延后）。

---

## Sprint 7A: enum first-class

### 7A.1 sema: enum match 穷尽性检查

**改动**：`compiler/src/sema.c` `case NODE_MATCH`

之前 `match opt { Option::Some(v) => v }` 漏 `None` arm 也能编译过，运行时 `None` 落空 → UB 或静默错值。sema 现在对 enum match 做穷尽性检查：每条 enum variant 必须被某个 arm 覆盖，否则 `sema_error` 报 "non-exhaustive match: missing variant 'X'"。

**匹配覆盖规则**：
- `Option::Some(p)` / `Some(p)`：覆盖 `Some` variant
- `Option::None` / `None`：覆盖 `None` variant
- `_` 通配符：覆盖**所有**未覆盖的 variant（catch-all）
- `p1 | p2`（NODE_PATTERN_OR）：两侧都覆盖才算覆盖
- 字面量 / 范围 pattern：不算覆盖 enum variant（必须显式列）

**错误格式**：
```
match_nonexhaustive.jhyy:11:5: error: non-exhaustive match: missing variant 'None'
1 semantic error(s)
```

### 7A.2 symtab: SYM_VARIANT 收集 API

**改动**：`compiler/src/symtab.h/c` 加 `sym_enum_variants()`

```c
int sym_enum_variants(SymTable *global_scope, const char *enum_name,
                      Sym **out, int max_variants);
```

遍历 global scope，收集所有 `kind == SYM_VARIANT && module == enum_name` 的 sym。sema 用这个 API 拿到 enum 的所有 variant，再跟 match arm 的 pattern 比对。

**SYM_VARIANT 早就存在**（v0.4 ABI 锁定期就有），只是之前没暴露收集 API。`Sym.module` 字段记的是 owning enum 名（不是真的 module 概念），是 `arena_strdup("Option")` 之类。

### 7A.3 parser: 短名 variant pattern

**改动**：`compiler/src/parser.c` `parse_pattern()`

之前只有 `Option::Some(v)` 显式限定能写 pattern。sprint 7A 加：
- `Some(v)` —— 短名 + `(`，自动查 global scope 找 `Some` 是否是已知 SYM_VARIANT，是就当 variant pattern
- `None` —— 短名无 `(`，同上逻辑。`None` 没 payload，所以 inner=NULL

```jhyy
match opt {
    Some(v) => v,     // OK
    None    => 0,     // OK
}
```

短名 variant pattern 走 `symtab_lookup(p->global_scope, name)`，locals 优先于 globals（用户写了 `let Some = ...;` 不会被误判成 variant）。

### 7A.4 codegen: 修 dangling next_check label

**改动**：`compiler/src/codegen.c` `case NODE_MATCH`

之前所有 arm 都不是 wildcard（只有 literal / range）时，最后一个 `next_check` block 的 label 从来没被 emit，QBE 报 "block @next5 is used undefined"。这个 bug 之前触发不到（`match.jhyy` 最后一个 arm 是 `_` wildcard），7A 加了 enum match 之后第一次暴露。

**修法**：循环结束后，如果 `next_check.id != 0`，emit 它的 label（sema 7A 已经保证 exhaustive，理论不可达）+ 给 phi 一个 dummy value。QBE 不报错了。

**次要修复**：emit 完 label 之后把 `next_check.id = 0`，避免被 wildcard 路径重复 emit（之前的 bug：emit label 后没清零，导致多 emit 一次"multiple definition"）。

### 7A.5 sema: match pattern binding 注册

**改动**：`compiler/src/sema.c` 加 `process_match_pattern()`

之前 `match opt { Some(v) => v }` 报 "undefined variable 'v'"——因为 sema 只查 pattern 的 kind 做覆盖检查，**没把 pattern 的变量 binding 加进 `ctx->locals` 和 `ctx->current_scope`**。

新加 `process_match_pattern(ctx, pat, match_type)`：
- `NODE_PATTERN_IDENT`：把 sym 加进 scope + locals，类型用 match_type
- `NODE_PATTERN_ENUM`：从 enum 类型里查 variant 的 payload 类型，递归处理 inner pattern
- `NODE_PATTERN_OR`：两侧都处理（同样的 binding 名会被覆盖——目前没做 "consistent binding" 检查，留给后续）
- 其它（LIT / WILD / RANGE）：no-op

**codegen 限制**：目前 codegen 还没把 pattern binding 接进 `cg->locals`，所以 `Some(v) => v` 写不出 payload 提取。配套测试 `match_exhaustive.jhyy` 暂时用 `Some(_) => 1` 占位（用通配符避开 binding）。payload binding 留到后续 sprint。

---

## 验证（7A 部分）

1. `python compiler/build/bin/regress.py` → **45/48 passed, 0 failed, 3 skipped**（v0.6.5 baseline 是 44/47，新增 1 个 positive test = match_exhaustive）
2. 新加 `compiler/tests/examples/match_exhaustive.jhyy`（positive）：`Option::Some` / `Option::None` / `Some(_)` / `None` 四种 pattern 都覆盖，EXIT=2
3. 新加 `compiler/tests/examples/_match_nonexhaustive.jhyy`（negative，`_` 前缀跳过 regress）：`Some(v) => v` 漏 `None` arm，手动编译报 "non-exhaustive match: missing variant 'None'" + exit=1
4. 旧的 `match.jhyy`（literal pattern + wildcard）继续 PASS（codegen 改动兼容 wildcard 路径）
5. 旧的 44 个非 match 测试继续 PASS

### 验证（7B 部分）

1. `python compiler/build/bin/regress.py` → **47/50 passed, 0 failed, 3 skipped**（v0.7 7A baseline 是 45/48，新增 2 个 positive test = const_array + const_struct_array）
2. `const_array.jhyy`：EXIT=122（`ASCII_LOWER[25]`）
3. `const_struct_array.jhyy`：EXIT=9（`PALETTE[2].b`）
4. `_const_non_literal.jhyy`：手动编译报 "const array element must be a const expression" + exit=1
5. 旧的 `struct.jhyy` / `struct_val_*.jhyy` / `big_test.jhyy` 继续 PASS（7B.6 修复 arr_of_structs[i].field 无回归）

---

## 不在 v0.7 范围（明确延后）

| 项 | 状态 | 备注 |
|---|---|---|
| Pattern binding codegen（`Some(v) => v` 提取 payload） | 7A 后续 sprint | 当前 `cg->locals` 不知道怎么 inject pattern binding；7A 只做 sema 层 binding 可见性，codegen 用 `_` 通配符规避 |
| OR pattern 一致性检查（`Some(x) \| Some(y)` 两边必须绑同名） | 7A 后续 | 当前 silently 覆盖 binding |
| 嵌套 const array（`[[i32; N]; M]`） | 7B 后续 | sema 拒绝；自举需要时再开 |
| const pointer / const slice / const enum array | 7B 后续 | sema 拒绝；需要 RTTI |
| const fn / 编译期函数求值 | 后续 phase | 大特性，单独 sprint |
| #5 nested struct QBE 'w' load 对齐 | open | jhyy 端继续 workaround |
| #6 `qbe_type_of(i8)` 返回 'b' | open | jhyy 端继续 workaround |

---

## 兼容性

- **行为严格化**：
  - 7A：enum match 漏 arm 现在报错（之前静默错值）
  - 7B：const 数组元素必须 const 表达式；非 const 报错（之前无 const 语法）
- **ABI 兼容**：
  - 7A：codegen 改动只补 label 发射，不改 .exe 行为
  - 7B：新增 `data $NAME = { ... }` emit 是新语法，无现有代码受影响；7B.6 修 pre-existing arr_of_structs[i].field bug 是修正而非改动
- **lang-spec 兼容**：v0.7 是 spec v1.0.0 的实现补强。新发 spec v1.1.0，新增 §11.3 enum match 穷尽性 + §13 const 数组。旧 v1.0.0 文件保留作为 phase-2 启动前的快照。
- **短名 variant pattern 不会与 ident pattern 冲突**：parser 走 `symtab_lookup(p->global_scope, name)`，只对 global SYM_VARIANT 生效；用户写 `let Some = ...; match x { Some(y) => ... }` 时，parser 找到的 `Some` 是 local SYM_VAR 不是 SYM_VARIANT，会走老路径当 ident pattern。

---

## 改动文件

### 7A
- `compiler/src/symtab.h`（sym_enum_variants 声明）
- `compiler/src/symtab.c`（sym_enum_variants 实现）
- `compiler/src/parser.c`（parse_pattern 短名 variant 路径）
- `compiler/src/sema.c`（NODE_MATCH 穷尽性检查 + process_match_pattern 绑定注册）
- `compiler/src/codegen.c`（NODE_MATCH dangling next_check label 修复）
- `compiler/tests/examples/match_exhaustive.jhyy`（新，positive test）
- `compiler/tests/examples/_match_nonexhaustive.jhyy`（新，negative test 文档）

### 7B
- `compiler/src/lexer.h`（TOKEN_CONST）
- `compiler/src/lexer.c`（`"const"` keyword entry + token_kind_name）
- `compiler/src/ast.h`（NODE_CONST_DECL + NodeConstDecl + accessor）
- `compiler/src/ast.c`（ast_new_const_decl + node_const_decl_data + dump + kind_name）
- `compiler/src/symtab.h`（SYM_CONST）
- `compiler/src/parser.c`（parse_const_decl + dispatch in parse_decl）
- `compiler/src/sema.c`（NODE_CONST_DECL + is_const_expr helper）
- `compiler/src/ir.h/c`（ir_emit_data 公开）
- `compiler/src/codegen.c`（NODE_IDENT SYM_CONST + NODE_INDEX struct elem + cg_module Pass A + cg_emit_load + cg_emit_store struct copy + NODE_CAST sub-word → word）
- `compiler/tests/examples/const_array.jhyy`（新，positive test）
- `compiler/tests/examples/const_struct_array.jhyy`（新，positive test）
- `compiler/tests/examples/_const_non_literal.jhyy`（新，negative test 文档）

### 7C
- `docs/abis/jhyy-lang-spec-v1.1.0.md`（新文件 = v1.0.0 + §11.3 enum match 穷尽性 + §13 const 数组）
- `docs/internal/status.md`（v0.6.5 → v0.7.0）
- `docs/logs/v0/changelog-v0.7.0.md`（本文档：新增 7B / 7C sections）
- `docs/plans/v1/v1.0.0任务清单 + 概要设计.md`（"不在 v1.0 范围"表新增 pattern binding + 嵌套 const）
- `compiler/build/bin/jhyy.exe`（重新编译）
