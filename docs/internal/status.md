# 当前状态

> **语言特性 / 已知限制 / 下一阶段**。详细 ship 记录见 `docs/logs/`,workarounds 见 `workarounds.md`,开发约定见 `conventions.md`。

## 当前版本

**v1.0.0 真自举闭环**（commit `eabee0d`, 2026-08-10）+ **v1.3.x 语法糖 Phase 4 ship**（6 sprint, 2026-08-12 ~ 2026-08-13）。

Stage 2 N=3 byte-equal closure IL sha `7c035615...`（v1.3.7 终态）。完整 ship 记录:
- [`docs/logs/v1/changelog-v1.0.0.md`](../logs/v1/changelog-v1.0.0.md) — Stage 2 closure 真闭环
- [`docs/logs/v1/changelog-v1.3.0.md`](../logs/v1/changelog-v1.3.0.md) — v1.3.x 语法糖 Phase 4 收尾
- [`docs/logs/v0/changelog-v0.9.0.md`](../logs/v0/changelog-v0.9.0.md) — v0.x 收尾主线（v0.9 wip commit 2.83）
- [`docs/logs/v0/`](../logs/v0/) + [`docs/logs/v1/`](../logs/v1/) — 全部历史 ship 报告

## 回归基线

| 指标 | 值 | 备注 |
|------|----|------|
| `jhyy.exe` (C 编译) `regress.py` | **50/50 PASS, 0 failed, 3 skipped** | 3 skipped = 库文件,无 `main_jhyy` |
| `jhyy_v1.exe.exe` (自举) `regress_v1.py` | **50/50 PASS, 0 failed, 3 skipped** | 持平 C-side baseline |
| Stage 1 byte-equal | **7/7 PASS** | `jhyy.exe` vs `jhyy_v1.exe.exe` 对 7 测试集产出 byte-equal `.il` |
| Stage 2 N=3 closure | ✅ **sha `7c035615...` 4-hop 稳定** | `jhyy_v1/v2/v3/v4` 四份 raw `.il` 字节相同 |

---

## 已实现的语言特性

### 字面量与基础类型

| 特性 | 状态 |
|------|------|
| 整数/浮点/字符串/字符/布尔字面量 | 完成 |
| 浮点字面量 codegen (f32/f64) | 完成 (v0.3) |
| 浮点算术 `+ - * /` (f32/f64) | 完成 (v0.5) |
| 类型转换 `as` (整数/浮点互转, 扩宽/截断) | 完成 (v0.5) |
| `null` 字面量 (typed pointer 上下文) | 完成 (v1.3.1) |
| `sizeof(TypeName)` 编译期常量 | 完成 (v1.3.3) |

### 类型与内存

| 特性 | 状态 |
|------|------|
| `let` / `let mut` 变量绑定 | 完成 |
| `as` 指针↔整数 (`*T ↔ i64/u64`) | 完成 (v0.6) |
| 定长数组 `[T; N]`（字面量/类型注解/下标读写） | 完成 (v0.3) |
| 切片 `[*]T`（字面量/index/subrange/len） | 完成 (v0.6) |
| 顶层 const 数组 (`const NAME: [T; N] = [...]`) | 完成 (v0.7) |
| struct 定义/字面量/字段访问 | 完成 |
| struct 按值传递/返回/赋值 | 完成 (v0.4) |
| struct 字段通过指针 (`ptr->field`) | 完成 |
| enum 定义/变体构造（一致内存布局） | 完成 |
| 指针 `&x`, `*ptr`, `*ptr = val` | 完成 |

### 控制流

| 特性 | 状态 |
|------|------|
| `if`/`else` 表达式（嵌套 `else if`, void 分支） | 完成 |
| `while` 循环（break/continue） | 完成 (v0.5) |
| `for i in start..end` 循环（类型感知, break/continue） | 完成 |
| `for x in slice` 语法糖 | 完成 (v1.3.4) |
| `break;` / `continue;` | 完成 (v0.5) |
| `return` 提前返回 | 完成 |
| 块表达式 `{ ... }` | 完成 |
| `defer fncall();` LIFO cleanup | 完成 (v1.3.6) |

### 函数与模块

| 特性 | 状态 |
|------|------|
| 函数（参数/返回/递归/return 类型检查） | 完成 |
| FFI `extern fn` 声明（printf, 文件 I/O） | 完成 |
| FFI 多参数调用 (≥3 参数) | 完成 (v0.4) |
| import 模块系统（含传递性导入） | 完成 (v0.4) |
| 多文件 CLI 输入 | 完成 (v0.4) |
| 模块命名空间 `mod::fn()` | 完成 (v0.6) |
| `#[inline]` attribute（call-site 展开） | 完成 (v1.3.5) |

### 模式匹配

| 特性 | 状态 |
|------|------|
| `match` 表达式（字面量/通配符/范围） | 完成 |
| enum match 穷尽性检查 | 完成 (v0.7) |
| 短名 variant pattern (`Some(v)` / `None`) | 完成 (v0.7) |
| Pattern binding (`Some(v) => v` 提取 payload) | 完成 (v1.3.7) |
| OR pattern (`Some(x) \| Some(x)` 一致性检查) | 完成 (v1.3.7) |

### 自举 / 工具链

| 特性 | 状态 |
|------|------|
| Stage 0 自举试点 (`arena.jhyy` 翻译) | 完成 (v0.6) |
| **v1.0.0 真自举 byte-equal 闭环** | **完成 (2026-08-10 commit `eabee0d`)** |
| 控制台输出（中文 UTF-8 + 数字 printf） | 完成 |
| Arena allocator（via FFI） | 完成 |
| Claude Code MCP 服务（11 工具 + 4 资源） | 完成 (v0.5 + mcp-jhyy Sprint 1 2026-08-11) |
| 复合赋值 (`+=`, `-=`, `*=`, `/=`, `%=`) | 完成 |
| 二元运算（算术/比较/位运算） | 完成 |
| `&&` / `\|\|` 短路求值 | 完成 |
| 一元运算 (`-`, `!`, `~`) | 完成 |

---

## 已知限制

### MVP 边界（v1.3.x 限制）

| 严重度 | 描述 | 影响 / 计划 |
|--------|------|-------------|
| P3 | `#[inline]` 仅展开 body 是单条 `return <expr>;` 的 fn | struct return / 多 stmt / if-else / 循环 → fall back `call $name`（v3.x 候选扩展 inline 语义） |
| P3 | `#[inline]` 递归调用 → fall back `call $name` | 编译器行为正确,只是不展开 |
| P3 | `defer` 不支持 `defer { block; }` 块语法 | v3.x 候选 |
| P3 | `defer` 不跨循环 / 内联 / 嵌套 block 触发 | v3.x 候选 |
| P3 | OR pattern 仅支持 enum variant | tuple / struct pattern v3.x |
| P3 | OR pattern 两边必须绑同名 + 同类型 | `Some(x) \| Some(y)` 拒绝 |
| P3 | 嵌套 OR (`A \| B \| C`) 不支持 | v3.x 候选 |
| P3 | 嵌套 pattern 二层+ (`Some(Some(Some(x)))`) 不支持 | v3.x 候选 |
| P3 | guard pattern (`Some(x) if x > 0`) 不支持 | v3.x 候选 |

### 编译器自身限制（v1.x 不阻塞）

| 严重度 | 描述 | 影响 / 计划 |
|--------|------|-------------|
| P2 | **jhyy 编译器 amd64_win 后端 stack-spill**（`infer_type → IDENT → symtab_lookup_local → symtab_lookup_one` 在特定调用栈深度 + 大结构传参下崩溃） | 临时 workaround `compiler/src0/symtab.jhyy:255-258`（`sb_init` 触发 arena_alloc 改变栈帧大小）。完整记录 [`v1.0.0详细实现方案.md`](../plans/v1/v1.0.0详细实现方案.md) § 3.6 + [`sprint-3-commit-6-sema-cleanup.md`](../logs/v1/sprint-3-commit-6-sema-cleanup.md)。**修复路径: v2.x QBE rewrite** |

### v1.0.0 已 ship 解除的旧限制（历史记录）

| 旧限制 | 解除 sprint |
|--------|-------------|
| Pattern binding codegen (`Some(v) => v` 提取 payload) | v1.3.7 (commit `0f32977`) |
| OR pattern 一致性检查 | v1.3.7 (commit `0f32977`) |
| 切片 `[*]T` codegen | v0.6.0 sprint 6A |
| 模块命名空间 (`mod::fn()`) | v0.6.0 sprint 6B |
| `*T ↔ i64` 互转 (`as`) | v0.6.0 sprint 6C |
| enum match 穷尽性检查 | v0.7 7A |
| 短名 variant pattern (`Some(v)` / `None`) | v0.7 7A |
| 顶层 const 数组 | v0.7 7B |
| v0 codegen bug 1-4（LEA / phi / loadub / &local） | v1.1.0 Bug 1-4 wip commits 1.5-1.8 |
| `null` 关键字 | v1.3.1 (commit `c2acbd1`) |
| `sizeof(TypeName)` | v1.3.3 (commit `bb15f98`) |
| `for x in slice` | v1.3.4 (commit `fb908bd`) |
| `#[inline]` | v1.3.5 (commit `143ee0f`) |
| `defer` | v1.3.6 (commit `169759c`) |
| enum param ABI mismatch (W-016) | v1.3.7 fix (commit `bbdebc2`) |

---

## 当前 sprint / 下一阶段

**v1.3.x 语法糖 Phase 4 全 6 sprint 已 ship**（v1.3.1 null / v1.3.3 sizeof / v1.3.4 for-in / v1.3.5 inline / v1.3.6 defer / v1.3.7 pattern binding + OR pattern;v1.3.2 `else if` 跳过 — parser 已支持嵌套 `if/else if` 等价）。v1.3.8 doc sync 收尾完成。

下一阶段:**v1.4** (src0 production flip) → **v1.5** (WiX installer) → **v2.x** (QBE 完整重写 + amd64_sysv / freestanding) ‖ **v3.x** (inline asm / `no_std` / `&mut` lifetime) 并行（OS 准备） → [`docs/plans/v2/v2.0.0-os-prep.md`](../plans/v2/v2.0.0-os-prep.md) + [`docs/plans/roadmap/v2-v3-parallel-sprint-plan.md`](../plans/roadmap/v2-v3-parallel-sprint-plan.md)。OS 端等编译器推进（per `memory/project_os_wait_state.md`,v1.0 闭环达成前不主动 prep OS）。

### v1.4+ 候选未完成项（明确延后, 非 blocker）

- 嵌套 const array (`[[i32; N]; M]`) — 自举需要时再开
- const pointer / const slice / const enum array — 需要 RTTI
- const fn / 编译期函数求值 — 大特性, 单独 sprint
- 浮点 fmod (`%` 操作符支持 f64/f32) — 当前 codegen.c:640 `TOKEN_PERCENT` 固定 emit `"rem"`(整数);自举不需要 float mod
- struct/enum 跨 FFI 边界(Windows x64 ABI 8-byte struct 重叠) — `compiler/src0/ffi.jhyy` 全 pointer/scalar,自举用不到;v3.x 处理
- JHYY 函数指针传给 C 函数(callback) — `src0/` 0 命中;v3.x 处理
- 变参函数 native syntax (`printf(fmt, ...)` 多参) — 当前稳定通过 single-val wrappers (`printf(fmt,val)` / `sprintf_lld(buf,fmt,val)` / `jh_fmt_lld_stderr(fmt,val)`,见 `compiler/src0/codegen.jhyy:9` "ir_emit 变参拆分");v3.x 候选 native variadic syntax