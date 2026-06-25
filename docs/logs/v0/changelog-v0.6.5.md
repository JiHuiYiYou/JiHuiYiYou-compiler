# JHYY v0.6.5 Changelog

## 版本目标

**单点修复**：sema 严格化 `let` 不可变 binding 不能再被赋值（plan § 0 #2 "let mut dead-code"）。

之前 codegen 在 `if`/`while`/`for` 等 block 内对 `let x = X;` 后 `x = Y;` **静默 emit 死代码**（store 被吞），运行期用的是原值 X。jhyy 编译器内表现为"代码像对的，行为错"——极难定位。sprint 1 arena.jhyy `arena_new_block` 命中过；sprint 2 commit 3c 命中过；每次翻译都得防御性写 `let mut`。

**修法**：sema `infer_type` 处理 `NODE_ASSIGN` 时，对 `target->kind == NODE_IDENT` 情况查 `id->sym->is_mutable` 字段。`is_mutable == false`（即 `let` 而非 `let mut`）时 `sema_error` 报 "cannot assign to immutable variable"。

**配套改动**：
- `compiler/tests/examples/dungeon_game.jhyy` 的 `randRange` 函数命中过这个 bug：`let s = *seed; s = ...; *seed = s;` 的中间赋值被静默吞掉，LCG 永远不前进（randRange 实际等价于 `min`）。改成 `let mut s`。
- 新加 `_immutable_assign.jhyy`（`_` 前缀 → regress.py 跳过）作为 negative test 文档。手动验证：`jhyy compile _immutable_assign.jhyy` 必须报 "cannot assign to immutable variable" + exit=1。

---

## 修复详情

### sema: 拒绝 immutable binding 赋值（plan § 0 #2）

**改动**：`compiler/src/sema.c` `case NODE_ASSIGN`

```c
if (d->target->kind == NODE_IDENT) {
    NodeIdent *id = node_ident_data(d->target);
    if (id->sym && id->sym->kind == SYM_VAR && !id->sym->is_mutable) {
        sema_error(ctx, n->loc,
                   "cannot assign to immutable variable '%s' (use `let mut` to declare)",
                   id->sym->name);
    }
}
```

**为什么放 sema 不放 codegen**：
- 不可变是**语义属性**，sema 是正确层（codegen 只管 emit）。
- 复用 `sema_error` + `ctx->error_count`，跟其他错误处理一致。
- plan § 0 #2 最初写的是 codegen 层，那是 sprint 1 早期判断；放 sema 更干净。

**为什么只查 NODE_IDENT**：
- `*p = Y`（deref target）：往 pointer 指向的内存写，不是 rebind——允许。
- `arr[i] = Y`（index target）：往 array element 写，不是 rebind——允许。
- `s.field = Y`（field target）：struct field write，不是 rebind——通过 field path 走，不经过 NODE_IDENT。
- 只有 `x = Y`（direct ident）是 rebind——必须 immutable 检查。

**for 循环变量**：`for i in 0..10 { ... }` 的 `i` 在 symtab 是 `SYM_VAR, is_mutable=false`（parser.c:284）。如果用户写 `for i in 0..10 { i = 5; }`，新检查会报错。这正是我们想要的——for 循环变量本就不该被改写（语义是迭代元素，不是 counter）。

**match pattern 变量**：`match x { Foo(a) => ... a ... }` 的 `a` 是 `SYM_VAR, is_mutable=false`（parser.c:149）。同样，新检查会捕获任何 `a = Y` 误用——也是想要的。

---

## 验证

1. `python compiler/build/bin/regress.py` → **44/47 passed, 0 failed, 3 skipped**（跟 v0.6.4 baseline 一致）
2. `dungeon_game.jhyy` 修复后重新编译通过，行为从"LCG 不前进"修正为"LCG 正常前进"
3. `_immutable_assign.jhyy` 手动编译：报 "cannot assign to immutable variable 'x' (use `let mut` to declare)"，exit=1
4. jhyy 端 `compiler/src0/_driver_lexer.jhyy`（34 tests）+ `_driver_parser.jhyy`（13 tests + exit=42）编译并通过——确认 `let mut` 路径仍然正常工作
5. `compiler/src0/arena.jhyy` 用 `let mut size` 等 workaround 编译通过——sprint 1 翻译时碰到的死代码问题现在被 sema 拦在更早阶段

---

## 不在 v0.6.5 范围（明确延后）

| 项 | 状态 | 备注 |
|---|---|---|
| `#5` nested struct QBE 'w' load 对齐 | v0.6.2 changelog 写过但**未实现** | 当前 jhyy 端所有嵌套 struct 平铺 6 字段 workaround；C 端 codegen 默认 `default: return 'w'` 仍存在 |
| `#6` `qbe_type_of(i8)` 返回 'b' | v0.6.2 changelog 写过但**未实现** | 当前 jhyy 端用 `*i32 + shift+mask` workaround；C 端 `case PRIM_I8: return 'b'` 仍存在 |
| `#9` f64/f32 比较 + coercion | **v0.6.3 已 fix** | 见 `git log -S "ceqw"` |
| `#10` imported string dangle | **v0.6.4 已 fix** | 见 `4ac1878` |

> ⚠️ docs/logs/v0/changelog-v0.6.2.md 描述了 v0.6.2 将一次性修复 #2/#5/#6，但实际只有 #2 在 v0.6.5 实现。**#5/#6 仍是已知 open bug**，jhyy 端继续用 workaround；如需真修请开 v0.6.6 / v0.7 sprint。

---

## 兼容性

- **行为严格化**：之前 `let x; x = Y` 静默运行（错的）。现在报错（对的）。**用户代码如有命中必须改 `let mut`**——已在 `dungeon_game.jhyy` 实测到 1 个 case，其他 codebase 待 audit。
- **ABI 兼容**：纯错误检查，不改 emit 形式，.exe 行为不变。
- **lang-spec 兼容**：v0.6.5 是 spec v1.0.0 的实现补强，不改 spec。spec 附录 B 可把 #2 移到"已修复"。

---

## 改动文件

- `compiler/src/sema.c`（NODE_ASSIGN case 加 immutable 检查）
- `compiler/tests/examples/dungeon_game.jhyy`（`let s` → `let mut s`）
- `compiler/tests/examples/_immutable_assign.jhyy`（新，negative test 文档）
- `docs/logs/v0/changelog-v0.6.5.md`（本文档）
- `compiler/build/bin/jhyy.exe`（重新编译）
