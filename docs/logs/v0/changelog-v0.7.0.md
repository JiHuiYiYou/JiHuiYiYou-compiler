# JHYY v0.7.0 Changelog

## 版本目标

**v0.7 把语言本身再打磨一层**，为 v1.0.0 self-hosting 减少 workaround 数量。

本版本分三个 sprint：
- **7A enum first-class**：enum 现在是真正可用的语言特性（exhaustiveness + 短名 variant pattern）
- **7B const struct array**：（独立 sprint）
- **7C docs sync**：lang-spec / ABI 追更 + changelog 收尾

本文档只覆盖 7A。7B / 7C 见后续 changelog。

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

## 验证

1. `python compiler/build/bin/regress.py` → **45/48 passed, 0 failed, 3 skipped**（v0.6.5 baseline 是 44/47，新增 1 个 positive test = match_exhaustive）
2. 新加 `compiler/tests/examples/match_exhaustive.jhyy`（positive）：`Option::Some` / `Option::None` / `Some(_)` / `None` 四种 pattern 都覆盖，EXIT=2
3. 新加 `compiler/tests/examples/_match_nonexhaustive.jhyy`（negative，`_` 前缀跳过 regress）：`Some(v) => v` 漏 `None` arm，手动编译报 "non-exhaustive match: missing variant 'None'" + exit=1
4. 旧的 `match.jhyy`（literal pattern + wildcard）继续 PASS（codegen 改动兼容 wildcard 路径）
5. 旧的 44 个非 match 测试继续 PASS

---

## 不在 v0.7 范围（明确延后）

| 项 | 状态 | 备注 |
|---|---|---|
| Pattern binding codegen（`Some(v) => v` 提取 payload） | 7A 后续 sprint | 当前 `cg->locals` 不知道怎么 inject pattern binding；7A 只做 sema 层 binding 可见性，codegen 用 `_` 通配符规避 |
| OR pattern 一致性检查（`Some(x) \| Some(y)` 两边必须绑同名） | 7A 后续 | 当前 silently 覆盖 binding |
| 7B const struct array | v0.7 7B sprint | 独立 changelog |
| 7C docs sync | v0.7 7C sprint | lang-spec / ABI 追更 #2 已修复 + enum first-class 状态 |
| #5 nested struct QBE 'w' load 对齐 | open | jhyy 端继续 workaround |
| #6 `qbe_type_of(i8)` 返回 'b' | open | jhyy 端继续 workaround |

---

## 兼容性

- **行为严格化**：enum match 漏 arm 现在报错（之前静默错值）。用户代码如有命中必须补 arm 或加 `_` wildcard。
- **ABI 兼容**：不改 emit 形式（codegen 改动只是补 label 发射，不改语义），.exe 行为不变。
- **lang-spec 兼容**：v0.7 7A 是 spec v1.0.0 的实现补强。spec 附录 B 可把"enum match 无穷尽性检查"移到"已修复"，新增"短名 variant pattern"作为可选语法糖。
- **短名 variant pattern 不会与 ident pattern 冲突**：parser 走 `symtab_lookup(p->global_scope, name)`，只对 global SYM_VARIANT 生效；用户写 `let Some = ...; match x { Some(y) => ... }` 时，parser 找到的 `Some` 是 local SYM_VAR 不是 SYM_VARIANT，会走老路径当 ident pattern。

---

## 改动文件

- `compiler/src/symtab.h`（sym_enum_variants 声明）
- `compiler/src/symtab.c`（sym_enum_variants 实现）
- `compiler/src/parser.c`（parse_pattern 短名 variant 路径）
- `compiler/src/sema.c`（NODE_MATCH 穷尽性检查 + process_match_pattern 绑定注册）
- `compiler/src/codegen.c`（NODE_MATCH dangling next_check label 修复）
- `compiler/tests/examples/match_exhaustive.jhyy`（新，positive test）
- `compiler/tests/examples/_match_nonexhaustive.jhyy`（新，negative test 文档）
- `docs/logs/v0/changelog-v0.7.0.md`（本文档）
- `compiler/build/bin/jhyy.exe`（重新编译）
