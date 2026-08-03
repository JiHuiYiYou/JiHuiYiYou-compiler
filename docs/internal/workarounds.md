# Workarounds

> JHYY 项目所有 workaround 的唯一权威登记处。
> 每个 workaround 必须在此登记后才能应用到代码里。

## 登记格式

每个 workaround 必须包含：

| 字段 | 含义 |
|------|------|
| **ID** | `W-NNN`，自增 |
| **状态** | `ACTIVE` / `RESOLVED` / `SUPERSEDED` |
| **日期** | 引入日期 (YYYY-MM-DD) |
| **触发面** | 什么模式/输入会触发底层问题 |
| **症状** | 触发后看到什么（编译报错/segfault/QBE 错/IL 错） |
| **根因嫌疑** | 当前最好的解释（不要求 100% 证实） |
| **workaround** | 怎么绕 |
| **影响范围** | 在哪些文件/位置应用了 |
| **失效条件** | 何时不能绕（比如 fix 后必须 revert） |
| **superseder** | 解决后引用哪个 fix / commit |
| **引用** | 相关 issue / 文档 / commit hash |

## 索引

| ID | 状态 | 简介 |
|----|------|------|
| [W-001](#w-001-hash_string-用-i32-deref-绕-v0-codegen-loadsb-错) | ACTIVE | hash_string 用 *i32 deref 绕 v0 codegen `loadsb` 错 |
| [W-002](#w-002-mainjhyy-重命名绕-jhyy_v1-hash_string-堆损坏) | ACTIVE | main.jhyy 重命名绕 jhyy_v1 hash_string 堆损坏 |

---

## W-001: hash_string 用 *i32 deref 绕 v0 codegen `loadsb` 错

**ID:** W-001
**状态:** ACTIVE
**日期:** v0.6 sprint（~2026-05）
**触发面:** `hash_string` 函数里需要 deref `*u8` 一次读 1 byte
**症状:**
- v0 codegen 对 `*((p) as *u8)` deref emit `%=b loadsb p`（destination 是 `b` class）
- QBE 不允许 `b` class 作 destination（loadsb 是 source-side narrow）
- QBE 报错：`invalid type for first operand in loadsb` 或类似

**根因嫌疑:** v0 codegen 误把 deref result 标 `b` class，应该是 `w`。

**workaround:** 改用 `*((p) as *i32)` deref 一次读 4 byte（`loadw` 合法），再 shift+mask 取目标 byte。

```jhyy
// 不绕 (v0 codegen 错):
let c = (*((p as i64 + i) as *u8)) as i64;

// 绕 (util.jhyy:199 hash_string):
let w = *((s as i64 + aligned) as *i32);
let sh = rem * (8 as i32);
let c = ((w >> sh) & (255 as i32)) as i64;
```

**影响范围:** `compiler/src0/util.jhyy:199-213` (`hash_string` 内部 4-byte aligned read 循环)

**失效条件:** v0 codegen 修了对 `*u8` deref 的类型推导（按 spec 应出 `w` destination），W-001 可移除。

**superseder:** TBD（v0 codegen bug fix sprint，post v1.0.0）

**引用:**
- 源码注释 `util.jhyy:195-198`
- 详尽 bug 清单见 `memory/feedback_v0_codegen_bug_workarounds.md` Bug 3
- 见 `docs/plans/v0/v0.6.0任务清单 + 概要设计.md`

---

## W-002: main.jhyy 重命名绕 jhyy_v1 hash_string 堆损坏

**ID:** W-002
**状态:** ACTIVE
**日期:** 2026-08-03
**触发面:**（任一即可）
1. 源码标识符长度 ∈ {6, 7, 8} 字符（如 `out_buf`、`in_buf`、`cmd_buf`）
2. 源码标识符后缀 = `_buf`（任意长度）
3. nlocals=1 + `return` 局部 var，或 nlocals=2 + `return binop(2 局部 var)`

**症状:**
- jhyy_v1（自举编译器）编 main.jhyy 或类似模式时 0xC0000005 segfault
- 即便触发名变量在 return 中完全不用也触发（`let out_buf: *u8 = "x"; return 0;`）
- v0 jhyy.exe 编同一源码完全正确
- `tmp/tm_*.jhyy` 151 个 bisect 用例保留作回归

**根因嫌疑:**
- W-001 的 `*i32` deref 4-byte read 在 jhyy_v1 编出来的 IL 里行为微妙
- arena 分配字符串后存在未初始化 slack 字节
- jhyy_v1 的 codegen 对 hash_string 的 IL emit 与 v0 有未定位差异，导致 4-byte read 在某些条件下把 slack 字节吸进 hash 值
- hash 错位 → SymTab lookup 误路由 → 错 sym 进 CGContext.locals → 后续 codegen 引用错 local → segfault
- 6-8 字符 + `_buf` 后缀触发面**尚未完全解释**——长度为什么是 6-8 而不是 5 或 9？

**workaround:** 把 main.jhyy 里所有触发面标识符重命名到 9+ 字符（机械前缀 `ptr_` / 后缀 `_data` / `_storage`），绕开触发面。

**改名规则:**
- 长度 ∈ {6, 7, 8} 字符的标识符一律改名到 ≥ 9 字符
- `_buf` 后缀的标识符一律改名（不论长度），`_buf` → `_buf_storage` 或 `_buffer_data`
- 改名一律**机械化**（加 `ptr_` 前缀 / `_data` 后缀），不手工取语义名，避免再撞新触发面
- 同时检查新名是否落在 6-8 字符范围，确保改名后**不引入新触发**

**影响范围:**
- `compiler/src0/main.jhyy`（本次应用目标，534 行）
- 其他 jhyy_v1 编译目标的源文件待评估（codegen.jhyy / parser.jhyy 等）

**改名规则（已实施 2026-08-03）：** 所有触发面标识符统一加 `_v1` 后缀：
- 长度 6 → 9 字符（safe）
- 长度 7 → 10 字符（safe）
- 长度 8 → 11 字符（safe）
- `_buf` 后缀 → `_buf_v1`（仍以 `_v1` 结尾，不再以 `_buf` 结尾；safe）

实施：见 `compiler/src0/_W002_rename_map.txt`（211 个标识符 → X_v1 形式）

**验证（2026-08-03）：**
- 重命名前：jhyy_v1 编 `tmp/tm_nm_out_buf.jhyy`（含 `let out_buf: *u8 = "x"; return 0;`）→ 失败（exit 127 / heap corruption）
- 重命名后：jhyy_v1 编同样输入但把 `out_buf` 改成 `output_buffer`（手测，临时文件）→ **成功**（exit 0，exe 产出）
- v0 jhyy.exe 编改名后的 main.jhyy → 成功（exit 0，输出的编译器也能再编 hello.jhyy）

**改名清单（211 个）：** 完整见 `compiler/src0/_W002_rename_map.txt`。按文件分布：

| 文件 | 替换数 |
|------|-------|
| codegen.jhyy | 724 |
| parser.jhyy | 469 |
| sema.jhyy | 351 |
| main.jhyy | 177 |
| types.jhyy | 97 |
| ast.jhyy | 71 |
| ir.jhyy | 49 |
| lexer.jhyy | 49 |
| util.jhyy | 39 |
| symtab.jhyy | 30 |
| arena.jhyy | 17 |
| **总计** | **2073** |

**局限性（重要）：** W-002 修了 hash_string 触发面 bug，但 jhyy_v1 编 main.jhyy **仍然 segfault**（exit 139）—— 因为 main.jhyy 还有别的触发 jhyy_v1 codegen bug 的模式（Bug 7 `let _ = fncall`、Bug 9 嵌套 if/else phi、Bug 13/16 struct 值传递等；详见 `memory/feedback_v0_codegen_bug_workarounds.md`）。要达到 closure 还得逐一修这些 bug。

**失效条件:**（任一即可移除 W-002）
- jhyy_v1 的 codegen 对 hash_string 生成的 IL 与 v0 IL byte-equal（diff 通过）→ 重新引入原名
- 或 v0 codegen 修了 W-001 的副作用（W-001 workaround 改成 byte-by-byte 不再 overread）—— 此时即使 jhyy_v1 触发面不变也不再 segfault

**superseder:** TBD（v0 codegen fix 或 jhyy_v1 IL diff 修复后）

**引用:**
- 详细 bisect 记录见 `memory/project_bootstrap_closure_state.md`
- 测试用例 `tmp/tm_*.jhyy`
- 完整 rename 映射 `compiler/src0/_W002_rename_map.txt`
- v0.8 commit 6 (efc41bf) `wip: bisect heap corruption`
- v0.8 commit 7 (待) `W-002: 211 个标识符 _v1 后缀化 + workarounds.md`
- 战略决策 `memory/project_bootstrap_closure_state.md` § Bisect findings