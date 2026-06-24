# JHYY v0.6.3 Changelog

## 版本目标

v0.6.2 patch 修完 sprint 1 实测沉淀的 3 个 codegen / sema bug。sprint 2 commit 3a 实测又暴露 **2 个 codegen bug**（#8 QBE Windows d-type spill + #9 f64/f32 比较 emit 错 + 混合类型比较 + call site 隐式 f64↔f32 转换），均属 sprint 1 计划文件 `v1.0.0详细实现方案.md` § 0 绕开清单内。**v0.6.3 是真正的 phase-2 自举前 C 端编译器最后一期 patch**，把这 2 个修掉（#8 维持 bridge 已 work around + #9 真修）。

本版本定位：
- 修 #9（codegen 真修：4 处）+ 加 call-site f64↔f32 隐式转换 + 加 binary mixed-type float compare coercion
- 维持 #8 workaround（`jh_f64_store` 桥函数已存在，无新工作）
- 不引入新特性
- 不做架构改动

---

## 修复清单

### 1. codegen: f64 / f32 比较 emit 错（#9 plan 坑）

**问题**：`if a == b { ... }` 其中 a/b 是 f64，codegen emit `%t =w ceqw %a, %b`，QBE 报 "invalid type for first operand in ceqw"（%a/%b 是 d type，不能用 word compare op）。

**根因**：`cg_emit_compare` 路径只 switch on `op_qt == 'l'` vs `default`，把 'd' / 's' 都 fall through 到 `ceqw` / `csltw` / `csgtw` 等 word 类 op。QBE 实际 float compare 名字是 `ceqd` / `ceqs` / `cltd` / `cled` / `cgtd` / `cged` / `clts` / `cles` / `cgts` / `cges`（int 是 `csltl` / `csgtl` 等），并且 float **没有** signed/unsigned 区分（所以 `cultd` / `cugtd` 等不存在 —— 第一次改时误写，QBE 报 unknown instruction）。

**修复**：`compiler/src/codegen.c` `cg_emit_compare` 完整 switch：
```c
case TOKEN_EQEQ:
    if (op_qt == 'l') op = "ceql";
    else if (op_qt == 'd') op = "ceqd";
    else if (op_qt == 's') op = "ceqs";
    else op = "ceqw";
    break;
```
6 个比较 op（EQEQ/BANGEQ/LT/LTEQ/GT/GTEQ）全部按 width + signedness 分发。float 不查 `is_unsigned`（QBE 不区分）。

**额外发现**：mixed-type `f32 var > 1.0f64` 也会触发 "invalid type for second operand"（cgts(s, d) 混类型）。修复：在 NODE_BINARY 比较分支前加 `if (left.qbe_type != right.qbe_type) right = cg_convert_arg(right, d->right->type, d->left->type);` 强制 right 跟 left 同 qbe_type。

### 2. codegen: call site f64↔f32 隐式转换缺失

**问题**：`cmp_s(1.0, 2.0)`（cmp_s 接 f32），caller emit `movsd $Lfp1, %xmm1; movsd $Lfp0, %xmm0`（8 byte mov），callee `ucomiss %xmm0, %xmm1` 只读低 4 byte。结果：两个 1.0/2.0 的 f64 表示低 32 bit 全 0，当 f32 读出来是 0.0，函数返回错误值。

**根因**：NODE_CALL / NODE_QUALIFIED_CALL 直接把 `cg_expr(arg)` 写到 args[]，没检查参数表达式 type vs 参数 type 的 qbe_type 是否一致。

**修复**：抽出 `cg_convert_arg(cg, arg, src_t, dst_t)` helper（call site + binary mixed-type + cast 共用），NODE_CALL / NODE_QUALIFIED_CALL 拿到 `fn_sym->type->func.params[i]` 后：
```c
if (param_ts && i < nparams && param_ts[i]) {
    arg = cg_convert_arg(cg, arg, d->args[i]->type, param_ts[i]);
}
```
支持 f64↔f32 的 `truncd` / `exts` 双向。其他 width 转换（f64↔i32 等）也在表里但目前 sema 拒，绝对到不了 codegen。

**测试**：
- 新加 `compiler/tests/examples/float_cmp.jhyy`：覆盖
  - `cmp_d(1.0, 2.0)` → 111110（f64 全 6 比较）
  - `cmp_d(3.0, 2.0)` → 10（f64 仅 != 真）
  - `cmp_s(1.0, 2.0)` → 15（f32 全 4 比较 + call-site 隐式 f64→f32 转换）
  - `take_d(2.5)` → 1（call-site f32→f64 via exts）
  - `take_s(3.5)` → 1（call-site f64→f32 via truncd + mixed-type `f32 > 1.0f64`）
- regress.py 44/47 passed, 0 failed, 3 skipped（float_cmp 自动被 regress.py 发现）

---

## 维持的 workaround（明确延后）

### #8: QBE Windows amd64 backend d-type spill bug

**状态**：维持 `jh_f64_store` C 桥函数（v0.6.2 / sprint 1 引入）。QBE Windows 后端 register allocator 把 d-type temp spill 到 GPR，emit `movsd %gpr, (%mem)` 触发 as "operand type mismatch"。

**QBE upstream**：未查（未跑 `mcp__fetch-mcp__search "QBE d-type spill XMM"`，按 plan 文件 § 0 #8 标记 P2 风险）。**v0.6.3 不处理**，bridge 已稳定 work around，phase-2 自举翻译所有 f64 字段 store 都走 `jh_f64_store(d as *u8, val)`。

**修复路径**（未来 v1.x+）：
- 查 QBE upstream 是否有 fix（`qbe/amd64/emit.c` 或 `rega.c`）
- 如果有，rebuild QBE 即可
- 如果没有，可能需要 fork QBE 或维持 bridge

---

## 不在 v0.6.3 范围（延后）

| 项 | 延后到 | 理由 |
|---|---|---|
| `&mut` 独占借用 | v1.1+ | phase-2 自举不需要（`*T` 指针够用） |
| 变参 FFI (`fprintf` 的 `...`) | v1.1+ | phase-2 用 `sprintf` 单 i32 + StringBuilder 拼接绕开 |
| 嵌套 import 路径 (`utils::io`) | v1.x | 当前 `import utils; utils::io_func()` 够用 |
| struct / enum 跨 FFI 边界 | v1.x | 自举不依赖 |
| QBE #8 d-type spill | v1.x | `jh_f64_store` 桥稳定 work around |

---

## 兼容性

- **ABI 兼容**：v0.6.3 patch 改 codegen emit 形式（多了 `truncd` / `exts` / `ceqd` / `cltd` ... 等指令），但 .il 文本变，.exe 行为不变。QBE 仍然接受
- **C 端 ABI 兼容**：v0.6.3 二进制跟 v0.6.2 二进制产出 .exe 行为完全相同（差异仅在 .il 中间产物 + f64↔f32 call-site 现在 emit 正确转换）
- **lang-spec 兼容**：v0.6.3 是 spec v1.0.0 的实现 patch，不改 spec。lang-spec 附录 B 把 #9 移到"已修复"状态（v1.0.1 同步出）

---

## 验证

- `python compiler/build/bin/regress.py` → **44/47 passed, 0 failed, 3 skipped**（之前 v0.6.2 是 43/46，新加 float_cmp.jhyy 自动被 regress.py 发现）
- 实际行为验证：`compiler/tests/examples/float_cmp.jhyy` 跑出来 EXIT=42，所有 cmp_d / cmp_s / take_d / take_s 返回值预期内
- `compiler/tests/examples/dungeon_game.jhyy` 仍 EXIT=0（修复 #2 时已加 `let mut`，不依赖这次 patch）
