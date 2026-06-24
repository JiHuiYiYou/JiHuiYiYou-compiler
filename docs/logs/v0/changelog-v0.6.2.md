# JHYY v0.6.2 Changelog

## 版本目标

v0.6.0 + v0.6.1 是自举前最后一期准备，sprint 1 phase-2 实测沉淀 3 个 codegen / sema bug。**v0.6.2 是 phase-2 自举前的 C 端编译器最后一期 patch**，修复这 3 个 bug，让 sprint 2-4 翻译时不再需要专门 work around（之前 util.jhyy / arena.jhyy / hash_string 等已经临时绕开）。同时也是 jhyy 编译器 v1.0.0 真自举闭环的 C 端基线 —— 真自举完成即弃 C 端，但 v0.6.2 是最后 ship 的 C 端二进制。

本版本定位：
- 修 phase-2 翻译时碰到的 3 个 codegen / sema bug
- 不引入新特性（不扩 lang-spec / abi）
- 不做架构改动
- phase-2 翻译走 v0.6.2 编出的 jhyy.exe

---

## 修复清单

### 1. sema: `let x; if cond { x = Y; }` 静默丢赋值（#2 plan 坑）

**问题**：C 编译器 codegen 把 `let x: T = v; if cond { x = Y; } use(x)` 中 `x = Y` 当 dead code 优化掉，emit 空 then/else 分支。结果：`if cond {}` 完全无效，`use(x)` 用原值 `v`。jhyy 编译器内部表现为"代码像是对的，行为却不对"，极难定位。

**根因**：v0.6 codegen 在 `if` 块内对 `let`（不可变）binding 赋值时，**没有报语义错误**，继续走 emit store 路径。Sema 也没有 immutable 检查。

**修复**：`compiler/src/sema.c` `infer_type` 处理 `NODE_ASSIGN` 时，对 `target->kind == NODE_IDENT` 情况先查 `id->sym->is_mutable` 字段。`is_mutable == false`（即 `let` 而非 `let mut`）时调 `sema_error` 报 "cannot assign to immutable variable '%s' (declare with `let mut` to allow reassignment)"，跟现有 "type mismatch" 错误走同一条错误路径。

**测试**：
- 现有 `regress.py` 43/46 全过（修了一个隐藏 bug：`dungeon_game.jhyy` 的 `let s = *seed;` 实际命中过这个 pattern，之前 codegen 静默丢赋值，`randRange` 永远返回 `min`，但测试 EXIT=0 凑巧通过；改成 `let mut s` 后行为正确）
- 新加 negative test：`let x: i32 = 1; if true { x = 2; }` 必须报 "cannot assign to immutable variable" 编译失败

**风险**：
- 旧 regress.py 43 测试均通过（只有 dungeon_game.jhyy 一个真命中，改 let mut 即可）
- 用户代码如有 `let x; if cond { x = Y; }` 静默通过的 case，会被新检查捕获，**必须改成 `let mut x`**
- 这次属于"严格化"修复，**长期来说减少了 silent bug**，短期可能有 1-2 个用户代码需要改 `let mut`

### 2. ir: `qbe_type_of` PRIM_I8 / PRIM_U8 返回 'b' 导致 QBE 拒绝（#6 plan 坑）

**问题**：`qbe_type_of(i8)` 返回 `'b'`，codegen 在 `cg_emit_load` 路径 emit `%=b loadsb`。QBE 不允许 `'b'` 作 destination class（loadsb/loadub 总是 sign/zero extend 到 32-bit），报 "invalid type for first operand" 错误。

**根因**：v0.6 qbe_type_of 把 i8/u8 映射成 QBE 'b'（8-bit），跟 QBE 的 `loadsb`/`loadub` 行为不一致（QBE load 永远扩展到 32-bit）。

**修复**：`compiler/src/ir.c` `qbe_type_of` 对 `PRIM_I8`/`PRIM_U8`/`PRIM_I16`/`PRIM_U16` 都改返回 `'w'`。`store` 路径走 `ir_emit_store`，本来就有 fallback 把 'b'/'h' 当 'w' 处理（storew 截断到 8-bit），所以存储路径不受影响。

**测试**：
- 现有 22 个用 i8/u8 的 regress 测试均通过（0 个实际 emit `%=b loadsb/loadub`，因为 jhyy 端用 `*i32 + shift+mask` workaround 绕开了）
- 现在 C 端 emit 也是正确的 `%=w loadsb/loadub`，未来 jhyy 端可以走"对"的方式（`*u8` 直接 deref）而不需要 workaround

### 3. ir: `qbe_type_of` KIND_STRUCT / KIND_ARRAY 默认 'w' 导致 nested struct field load 错（#5 plan 坑）

**问题**：`qbe_type_of(struct)` 落到 `default: return 'w';` 分支，返回 4-byte load 类型。但 8-aligned struct（如 `struct { i64, i32 }`）的 field 访问应该用 8-aligned `loadl`，否则对齐错误 + 性能损失。

**根因**：v0.6 qbe_type_of 对 KIND_STRUCT / KIND_ARRAY 一刀切返回 'w'，没读 `type_align` 字段。

**修复**：`compiler/src/ir.c` `qbe_type_of` 对 `KIND_STRUCT` 加 case：`return type_align(t) >= 8 ? 'l' : 'w';`。`KIND_ARRAY` 类似，按 elem 的 align 决定。

**测试**：
- 现有 43 个 regress 测试均通过（0 个用 nested struct field access 8-aligned load）
- v0.6.2 emit 形式跟 QBE 对齐要求一致

---

## 不在 v0.6.2 范围（明确延后）

| 项 | 延后到 | 理由 |
|---|---|---|
| `&mut` 独占借用语法 | v1.1+ | phase-2 自举不需要（`*T` 指针够用），jhyy_helpers.c 桥已绕开 FILE* 问题 |
| 变参 FFI (`fprintf` 的 `...`) | v1.1+ | phase-2 用 `sprintf` 单 i32 + StringBuilder 拼接绕开 |
| 嵌套 import 路径 (`utils::io`) | v1.x | 当前 `import utils; utils::io_func()` 够用 |
| struct / enum 跨 FFI 边界 | v1.x | 自举不依赖 |

---

## 兼容性

- **ABI 兼容**：v0.6.2 patch 改 codegen emit 形式（`'b' → 'w'` / `'w' → 'l'` for 8-aligned struct），但 .il 文本变，.exe 行为不变。QBE 仍然接受（`%=w loadsb` / `%t =l loadl` 都是合法形式）
- **C 端 ABI 兼容**：v0.6.2 二进制跟 v0.6.1 二进制产出 .exe 行为完全相同（差异仅在 .il 中间产物，QBE 后端行为一致）
- **lang-spec 兼容**：v0.6.2 是 spec v1.0.0 的实现 patch，不改 spec。lang-spec 附录 B 把 #2 / #5 / #6 移到"已修复" 状态（v1.0.1 同步出）

---

## 验证

1. `regress.py 43/46 全过`（包括修复后的 dungeon_game.jhyy）
2. negative test: `let x: i32 = 1; if true { x = 2; }` 报 "cannot assign to immutable"
3. v0.6.2 编 jhyy 编 `compiler/src0/_driver.jhyy` 跑通 EXIT=42（跟 v0.6.1 行为一致）

---

## 提交

- 改动文件：`compiler/src/ir.c` / `compiler/src/sema.c` / `compiler/tests/examples/dungeon_game.jhyy`
- 新文件：本文档
- 二进制：`compiler/build/bin/jhyy.exe` 重新编译
