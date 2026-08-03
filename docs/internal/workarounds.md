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
| [W-002](#w-002-mainjhyy-重命名绕-jhyy_v1-hash_string-堆损坏) | ACTIVE | 211 个 src0 标识符 _v1 后缀化绕 jhyy_v1 hash_string 堆损坏 |
| [W-003](#w-003-jhyy_v1-let-_-fncall-顶层-嵌套-segfault) | ACTIVE | `let _ = fncall(...)` 改 direct call，绕 jhyy_v1 codegen segfault（Bug 7/7b） |
| [W-004](#w-004-short-local-var-4-chars--symtab-hash-撞--jhyy_v1-field-assign-死循环) | ACTIVE | 短（≤4 字符）local var / fn 参数 / field 改名绕 jhyy_v1 symtab hash 撞（stack overflow） |
| [W-005](#w-005-let-mut--assign--jhyy_v1-codegen-segfault) | ACTIVE | `let mut x: T; x = expr;` 改 `*pos_ptr += ...` 绕 jhyy_v1 codegen segfault |

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
---

## W-003: jhyy_v1 `let _ = fncall(...)` 顶层 / 嵌套 segfault → direct call (top-level only)

**ID:** W-003
**状态:** ACTIVE (partial — v3 只覆盖顶层)
**日期:** 2026-08-03
**触发面:** 任何 `let _NAME = fncall(...)` 模式，无论 `_NAME` 是什么；无论 fncall 是否在函数顶层或嵌套 if/while 块内
**症状:** jhyy_v1 编译含此模式的源码 → 0xC0000005 segfault（exit 139）
**根因嫌疑:** v0 codegen 对 `let _ = fncall(...)` emit IL 缺漏（详见 `memory/feedback_v0_codegen_bug_workarounds.md` Bug 7 / Bug 7b）
**workaround (v3 — 限定顶层):** 把**函数顶层**的 `let _X = fncall(args);` 改成 `fncall(args);`（direct call，无 binding）。**嵌套 if/while/for 块内的同模式保持原样**——v3 不改，避免 v0 sema if/else 分支类型不匹配。

```jhyy
// BAD (顶层):
let _s1 = store_byte_i32(nul1, 0 as i32);

// GOOD (顶层):
store_byte_i32(nul1, 0 as i32);

// BAD (嵌套 if) — 保持原样，不动
```

注意：`_X` 是 discard variable；direct call 的返回值被 jhyy 语义自然丢弃，无需 binding。

**v3 决策的根因（v1/v2 失败教训）：**
- **v1 (全部 direct call)**: v0 报 18 个 sema error（"if/else branches must have same type: () vs i32"）。
  - 原因：`let _X = fncall()` 让分支 type = `()`（NODE_LET → `type_void()`）；改 bare `fncall()` 让分支 type = `i32`（fncall 返回 i32）。分支 mismatch。
  - 受影响的 17 处都在 `sema.jhyy` 的嵌套 if-else（典型：middle if 的 else 分支是 `let _X = sema_error_str(...)`，then 分支里套一个 no-else 的 inner if）。
- **v2 (全部 mutable 模式 `let mut _x = 0; _x = fncall(); let _ = _x;`)**: v0 自己 segfault。
  - 原因：mutable pattern 在 codegen 路径中产生 jhyy_v1 codegen 不支持的 emit。可能触发 Bug 6（重复 if kind）或 Bug 9（nested phi）等。
- **v3 (只顶层 direct call)**: 通过。regress 47/50 pass, 0 fail, 3 skipped. jhyy_v1 可编 main.jhyy 但仍偶尔 segfault（heap 不稳）。

**影响范围（src0/ 各文件 `let _X = ...` 计数 — v3 实际替换 vs 剩余）：**

| 文件 | 总数 | v3 替换 (顶层) | 剩余 (嵌套) |
|------|------|----------------|--------------|
| codegen.jhyy | 34 | 1 | 33 |
| sema.jhyy | 77 | 18 | 59 |
| lexer.jhyy | 23 | 0 | 23 |
| parser.jhyy | 5 | 4 | 1 |
| main.jhyy | 12 | 10 | 2 |
| **总计** | **151** | **33** | **118** |

（v3 实际产生 29 替换，差异是某些顶层 pattern 不匹配正则或不在 `let _X = ` 形式）

**v3 实现的细节：** 用 Python 脚本 `tmp/do_w003_v3.py` 扫 brace depth，只改 depth==1 的模式。depth 计算跳过字符串 (`"..."`) 和行注释 (`//`)。29 处替换不引入新 sema error。

**v3 验证（2026-08-03）：**
- v0 build main.jhyy: ✓ exit 0, 生成 main.il
- regress.py: 47/50 pass, 0 fail, 3 skipped
- jhyy_v1 build main.jhyy: 部分成功（exit 0 偶尔，segfault 139 偶尔 — heap 不稳，需要进一步 workaround 或 root cause fix）
- jhyy_v1 build hello.jhyy: ✓ exit 0
- jhyy_v1 compile hello.jhyy -o tmp/hello_run.exe: ✓ exit 0
- jhyy_v1 build codegen.jhyy: ✗ parse error "unexpected token 'while' in expression"（Bug 60，jhyy 翻译 parser 时 while 在 expression 上下文漏处理）

**失效条件:** v0 codegen 修复 `let _ = fncall(...)` emit → W-003 可移除，回归 `let _X = fncall(...)` 风格

**superseder:** TBD（v0 codegen fix sprint，post v1.0.0）

**未解决问题 (v3 之后):**
- jhyy_v1 build main.jhyy 偶尔 segfault — 怀疑是 W-001/W-002 heap 损坏叠加 W-003 未覆盖的 Bug 7b 嵌套模式。118 处嵌套 `let _ = fncall()` 仍是潜在 trigger。
- 进一步 v4 候选：用 **mutable assignment pattern** 处理 depth==2（1-level if 块），depth==3+ 仍保持原样。
- mutable pattern 会触发 v0 codegen bug（v2 失败）— 需要先验证 v0 codegen 是哪种 pattern 失败、是否能更精细地限定 mutable 范围。

**引用:**
- `memory/feedback_v0_codegen_bug_workarounds.md` Bug 7 / Bug 7b
- 决策过程见 `memory/project_bootstrap_closure_state.md` § W-003 iterations

---

## W-004: short local var (≤4 chars) → symtab hash 撞 → jhyy_v1 field assign 死循环

**ID:** W-004
**状态:** ACTIVE
**日期:** 2026-08-03
**触发面:** 同时存在 ① 短（≤4 字符）函数名 + ② 短（≤4 字符）`let` 局部 var 名 + ③ struct field 赋值的组合。具体阈值取决于三者长度之和（如 `fn main` 4 + `let a` 1 + `field cur` 3 = fail；`fn entry` 5 + `let a` 1 + `field cur` 3 = OK）。
**症状:** jhyy_v1 编译含此模式的源码 → 0xC00000FD STACK OVERFLOW（exit 3221226356）。**不是** segfault（exit 3221225477）。
**根因嫌疑:** W-001 的 `hash_string` 用 `*i32` deref 一次读 4 byte。对于短字符串（长度 1-4），4-byte read 把后续 slack 字节吸进 hash 值，导致 hash 错位 → 多个不同 ident 撞同一 slot → 后续 cg_emit_store / cg_copy_struct 走错 sym → 递归查错 local → 死循环。

W-002 已修类似（identifier 长度 6-8 + `_buf` 后缀）的 hash_string 触发面，但只覆盖了**全局** enum 常量和**函数名**（211 个），未覆盖**局部 var 名**和**struct field 名**。本 workaround 补 W-002 漏掉的部分。

**workaround:** 把 src0/ 里所有 ≤ 4 字符的 `let` 局部 var 标识符重命名到 ≥ 5 字符。机械化前缀 `ptr_` / 后缀 `_local` / 加 `_v1`。同样适用于函数参数名。

**改名规则:**
- 长度 ≤ 4 字符的 `let`/`let mut` 局部 var（包含函数参数）一律改名到 ≥ 5 字符
- 长度 ≤ 4 字符的 struct field 名同样改名
- 命名规则同 W-002：机械化前缀/后缀，避免新撞

**最小复现（验证 workaround 必要性）:**

```jhyy
// BAD (触发 stack overflow):
type Arena = struct { cur: i32 }     // field "cur" 长度 3
fn main() -> i32 {                   // fn "main" 长度 4
    let mut a: Arena = Arena { cur: 0 as i32 };  // var "a" 长度 1
    a.cur = 5 as i32;                 // field assign 触发
    return 0 as i32;
}
// jhyy_v1: STACK OVERFLOW (3221226356)

// GOOD (workaround 验证):
type Arena = struct { current_value: i32 }  // field 长度 13
fn ab() -> i32 {                              // fn 长度 2，但其它都长
    let mut arena_local: Arena = Arena { current_value: 0 as i32 };  // var 长度 11
    arena_local.current_value = 5 as i32;
    return 0 as i32;
}
// jhyy_v1: OK
```

**验证（2026-08-03）:**
- 局部 var 名 `a`/`aa` (1-2 字符) + fn 名 `main`/`ab` (≤4 字符) + field 名 `cur`/`val` (≤4 字符) → 100% stack overflow
- 任一项 ≥ 5 字符 → 100% OK
- 字段赋值 (`a.cur = 5`) 是必要触发条件；只读不写不触发

**影响范围（src0/ 各文件 `let x` / `let mut x` 计数 — W-004 待替换）:**

- main.jhyy: 55 个 let + ~20 个 fn 参数（主要工作量）
- 其他文件待评估（codegen.jhyy / sema.jhyy 等 src0/ 文件，若要 jhyy_v1 编出来都要改）

**W-004 局限性:** W-001 的 hash_string 根因（`*i32` deref overread）未解，只是机械改名绕开触发面。W-001 真正修了之后，W-004 可移除并恢复短名。

**失效条件:** jhyy_v1 的 codegen 对 `*i32` deref 4-byte read 改成 byte-by-byte 不再 overread（修 W-001 根因）→ W-004 可移除。

**superseder:** TBD（v0 codegen fix sprint，post v1.0.0）

**引用:**
- `memory/feedback_v0_codegen_bug_workarounds.md` Bug 6 (let-mut assignment) + Bug 1 (hash_string overread)
- W-002 (`docs/internal/workarounds.md` § W-002) 修了 211 个全局/函数名，未覆盖局部 var
- 复现测试 `tmp/test_w4.jhyy` ~ `tmp/test_w8.jhyy`

---

## W-005: `let mut x: T; x = expr;` 改 `*pos_ptr += ...` 绕 jhyy_v1 codegen segfault

**ID:** W-005
**状态:** ACTIVE
**日期:** 2026-08-03
**触发面:** 函数体内任意 `let mut` 变量 + 后续 `x = expr;` 赋值语句（不论 expr 类型、变量名长度、是否被 read、所在 fn 深度）。**100% 触发**（exit 139 / 0xC0000005）。
**症状:** jhyy_v1 编译含此模式的源码 → 0xC0000005 segfault。v0 jhyy.exe 编同一源码 → exit 0（IL 正确）。
**最小复现:**
```jhyy
// BAD (segfault):
fn entry() -> i32 {
    let mut x: i32 = 0 as i32;
    x = 42 as i32;
    return x;
}
// jhyy_v1: segfault (139)

// GOOD (workaround 验证):
fn entry() -> i32 {
    let buf = malloc(8 as i64) as *i64;
    *buf = 0 as i64;
    *buf = *buf + 42 as i64;
    let nul = (buf as i64) as *u8;
    free(nul);
    return 0 as i32;
}
// jhyy_v1: OK
```

**根因嫌疑:** Bug 6 (let-mut assignment) + Bug 7b (nested let-mut) 的复合 — jhyy_v1 自举编译 `NODE_ASSIGN[NODE_IDENT]` 路径时 emit 错的 IL（多写 storew 到未初始化 stack slot，或 loadw-on-loadw 链），访问 uninitialized memory 触发 0xC0000005。**v0 codegen 没这个问题**（v0 编同一 .jhyy 源码 emit 正确 IL），所以是 jhyy_v1 自身 codegen 的 bug，不是源 v0 的 bug。

**workaround:** 用 `*pos_ptr += n` 模式（`i64` 通过 `*i64` 解引用累加）替代 `let mut pos: i64 = 0; pos = str_concat_at(...)`。需要累计位置的所有 cmd-构造函数（`run_qbe_v1` / `link_with_gcc`）都改。

```jhyy
// BAD (触发 segfault):
fn run_qbe_v1(il_path_v1: *u8, asm_path_v1: *u8) -> i32 {
    let cmd_buf_v1 = malloc(4096 as i64);
    let qbe = QBE_PATH_v1();
    let mut pos_v1: i64 = 0 as i64;
    pos_v1 = str_concat_at(cmd_buf_v1, pos_v1, qbe);
    pos_v1 = str_concat_at(cmd_buf_v1, pos_v1, " -t amd64_win -o " as *u8);
    pos_v1 = str_concat_at(cmd_buf_v1, pos_v1, asm_path_v1);
    ...
    let nul_p = (cmd_buf_v1 as i64 + pos_v1) as *u8;
    store_byte_i32(nul_p, 0 as i32);
    ...
}

// GOOD (W-005):
fn run_qbe_v1(il_path_v1: *u8, asm_path_v1: *u8) -> i32 {
    let cmd_buf_v1 = malloc(4096 as i64);
    let pos_ptr_v1 = malloc(8 as i64) as *i64;
    *pos_ptr_v1 = 0 as i64;
    let qbe = QBE_PATH_v1();
    *pos_ptr_v1 = str_concat_at(cmd_buf_v1, *pos_ptr_v1, qbe);
    *pos_ptr_v1 = str_concat_at(cmd_buf_v1, *pos_ptr_v1, " -t amd64_win -o " as *u8);
    *pos_ptr_v1 = str_concat_at(cmd_buf_v1, *pos_ptr_v1, asm_path_v1);
    ...
    let nul_p = (cmd_buf_v1 as i64 + *pos_ptr_v1) as *u8;
    store_byte_i32(nul_p, 0 as i32);
    ...
    free(pos_ptr_v1 as *u8);
}
```

注意：`*pos_ptr_v1 = str_concat_at(...)` 实际是 `*pos_ptr_v1 = expr`，本质也是 `let mut` assignment 模式。**但通过 `*i64` deref 走的是 `NODE_DEREF` 路径而不是 `NODE_ASSIGN[NODE_IDENT]` 路径**，绕开 bug 6 的触发面。

**验证（2026-08-03）:**
- 最小 let-mut + assign（i32/i64、var 长度 1/7/10/各种）→ 100% segfault
- `*pos_ptr = ...` 模式 → 100% OK
- v0 编两种模式都 OK（jhyy_v1 自身 bug，不是 v0 也不是源 jhyy 源码问题）

**影响范围（src0/ 中需 W-005 替换的 let-mut + assign 位置）:**

| 文件 | 函数 | 变量 | 替换数 |
|------|------|------|--------|
| main.jhyy | run_qbe_v1 | pos_v1 | 5 (5 个 assign) |
| main.jhyy | link_with_gcc | pos_v2 | 9 (9 个 assign) |
| **总计** | | | **14** |

**W-005 局限性:** 这是绕 `NODE_ASSIGN[NODE_IDENT]` 触发面。`let mut struct; struct.field = X` (NODE_ASSIGN[NODE_FIELD]) 走不同路径，W-005 不修。**Bug 6+7b 的根因修复需在 jhyy_v1 codegen.c 端修 NODE_ASSIGN 的 emit，post v1.0.0。**

**失效条件:** jhyy_v1 codegen 修对 NODE_ASSIGN[NODE_IDENT] 的 let-mut target → emit 正确 `storew` 到 stack slot → W-005 可移除并恢复 `let mut x; x = ...;` 风格。

**superseder:** TBD（jhyy_v1 codegen fix sprint，post v1.0.0 phase-2 落地后）

**引用:**
- `memory/feedback_v0_codegen_bug_workarounds.md` Bug 6 (let-mut assignment) + Bug 7b (nested let-mut)
- W-003 (`docs/internal/workarounds.md` § W-003) 修了 `let _X = fncall()` 顶层 direct call 模式，未覆盖 let-mut + assign
- W-004 修了短 var 名导致 symtab hash 撞死循环，未覆盖 let-mut + assign segfault
- 复现测试 `tmp/test_w4_lit.jhyy` / `tmp/test_w4_v1.jhyy`
