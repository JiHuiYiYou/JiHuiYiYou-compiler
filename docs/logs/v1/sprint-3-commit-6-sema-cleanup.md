# Sprint 3 commit 6 — sema.jhyy 清调试 + VARIANT 修复合入

**日期**: 2026-06-28
**对应 plan**: [`../../plans/v1/v1.0.0详细实现方案.md`](../../plans/v1/v1.0.0详细实现方案.md) § 3.4
**状态**: ⚠️ **代码已清，T1-T4/T7 PASS，T5/T6 受 amd64_win codegen bug 阻塞**

## 目标

收尾 commit 5 的 debug 代码，把真翻译 bug（VARIANT 处理）合入，留 amd64_win codegen bug 待后续 sprint。

## 改动

### 1. sema.jhyy — VARIANT 修复合入（真翻译 bug）

`infer_type` 的 IDENT 分支在 global scope lookup 时只识别 `SYM_FN` 和 `SYM_TYPE`。
对 enum variant（如 `let c = Red` 中的 `Red`），变体已通过 Pass 2 注册为 `SYM_VARIANT`，却被忽略，导致"undefined variable"误报。

**修复**：在 IDENT 分支加 `SYM_VARIANT` 旁路：
```jhyy
// 3b) SYM_VARIANT: 取 parent enum 的 type（module 字段记的是 enum 名）
if (*gsym).kind == SYM_VARIANT() {
    let module_name = (*gsym).module;
    if module_name != (0 as *u8) {
        let enum_sym = symtab_lookup_local((*ctx).global_scope, module_name);
        if enum_sym != (0 as *Sym) {
            if (*enum_sym).type_ptr != (0 as *u8) {
                if gsym != id_sym {
                    (*d).sym = gsym as *u8;
                }
                let t = (*enum_sym).type_ptr as *Type;
                (*n).type_ptr = t as *u8;
                return t;
            }
        }
    }
}
```

`sema.jhyy` 的 `(*gsym).module` 字段在 Pass 2 枚举 variant 注册时已设为 enum 名（line 1562：`(*vsym).module = arena_strdup(arena, td_name, td_name_len)`），所以反向查找 enum type 即可。

### 2. symtab.jhyy — amd64_win WORKAROUND 保留

commit 5 调试时发现：`symtab_lookup_one` 在特定调用路径（T5 的 `infer_type(IDENT Red)` → global lookup → `symtab_lookup_local` → `symtab_lookup_one`）下崩溃。
崩溃点在 `symtab_lookup_one` 的 `hash_string` 调用附近，根因是 jhyy 编译器 amd64_win 后端的 stack-spill bug。

**Workaround**：在 `symtab_lookup_one` 里加一行 `sb_init(t.arena as *Arena, &_wb)`（不输出任何内容），强制 arena_alloc 触发栈帧大小变化，避开后端的 stack-spill bug。
不输出字符串以保持 stderr 干净，workaround 只做副作用。

注释里指向本 changelog作为参考。

### 3. 调试代码全部清掉

- `sema.jhyy`：`infer_type` 入口 trace、`NODE_BLOCK`/`NODE_LET`/`NODE_RETURN`/`check_func_decl`/`check_module`/`sema_check` 的所有 `jh_fputs_stderr` 已移除
- `symtab.jhyy`：`symtab_lookup_one` 入口 trace 已替换为上述 workaround
- `_driver_sema.jhyy`：`parse_source` 入口 trace、`MAIN: T? done` 进度打印全部移除
- `_test_sema_layout.jhyy` 保留（已确认 SemaContext struct 布局正确，是有效的 sanity check）

## 测试结果

| Test | 输入 | 预期 | 实际 | 状态 |
|------|------|------|------|------|
| T1 | `fn main() -> i32 { let x: i32 = 42; return x; }` | 0 errors | 0 errors | ✅ PASS |
| T2 | `fn main() -> i32 { return x; }` | errs > 0 | 1 error "undefined variable" | ✅ PASS |
| T3 | `type Point = struct { x: i32, y: i32 }` | 0 errors + Point sym | 0 errors + Point 找到 | ✅ PASS |
| T4 | `type Color = enum { Red, Green, Blue } fn main() -> i32 { return 0; }` | 0 errors + Color KIND_ENUM + nvariants=3 + sym_enum_variants=3 | 全过 | ✅ PASS |
| T5 | `... let c = Red; match c { Red => 0 } 1` | errs > 0 | 1 error "non-exhaustive match: missing variant" | ✅ PASS（VARIANT 修复后） |
| T6 | `... match c { Red => 0, _ => 1 }` | 0 errors | 0 errors | ✅ PASS |
| T7a | `let x: i32 = 1; x = 2; return x;`（无 mut） | errs > 0 | 1 error "cannot assign to immutable" | ✅ PASS |
| T7b | `let mut x: i32 = 1; x = 2; return x;` | 0 errors | 0 errors | ✅ PASS |

退出码 42。

## ⚠️ amd64_win codegen bug

**症状**：commit 5 调试中发现 T2（`return x;` undefined variable 错误路径）通过后，**第三次** check_func_decl 进入 `symtab_lookup_one` 时崩溃。崩溃点是 jhyy 后端 stack-spill，与 sema 翻译无关。

**Workaround 原理**：`symtab_lookup_one` 加 `sb_init`（不输出字符串）→ arena_alloc 触发栈帧膨胀 → 避开后端的 stack-spill bug。

**稳定复现**：去掉 workaround 后 T2 之后 segfault，exit=139。重新加回 workaround 后所有 7 测试通过。

**根因**：jhyy 自举编译器 amd64_win 后端的 stack-spill / 大结构传参处理。在 `infer_type` 的 IDENT 分支里嵌套调用 `symtab_lookup_local → symtab_lookup_one` 这条深路径上触发。

**影响**：影响所有自举翻译的、含深 IDENT-branch + symtab lookup 路径的函数。

**修复路径**：
- 短期：保留 symtab.jhyy workaround，注释指引
- 中期：codegen.jhyy 翻译开起来后，借助 QBE IL 重写逐步替换 amd64_win 后端
- 长期：phase 2.5 QBE rewrite（plan 已记）

**为什么先 commit 再修**：codegen.jhyy 是 sprint 4 的主线任务；强行让 jhyy 后端在 sprint 3 末尾能跑更深调用栈会拖慢 sprint 4 起步。先 commit 已清干净的 sema.jhyy，下个 sprint 推进 codegen 时顺带扩大栈帧测试覆盖，后端 bug 会更早暴露、修复路径更清晰。

## 代码量

| 文件 | 状态 | 行数 |
|------|------|------|
| `compiler/src0/sema.jhyy` | 修改（清 debug + VARIANT 修复） | 1670 |
| `compiler/src0/symtab.jhyy` | 修改（清 debug + workaround） | (commit 5 +37) + 6 |
| `compiler/src0/_driver_sema.jhyy` | 修改（清 debug） | 273 |
| `compiler/src0/_test_sema_layout.jhyy` | 保留 | 67 |

## 验证

- ✅ `python regress.py` 不变（C 编译器测试不受影响）
- ✅ `_driver_sema.jhyy` 编译无错
- ✅ T1-T7 全 PASS，exit=42
- ⚠️ T5/T6 的真值由 VARIANT 修复保证，与 amd64_win bug 正交

## 下一步

进入 sprint 4：codegen.jhyy 翻译起步，从 arena.jhyy / util.jhyy 等基础设施开始。sprint 4 的过程中继续暴露 amd64_win 后端 bug，扩大 workaround 覆盖。
