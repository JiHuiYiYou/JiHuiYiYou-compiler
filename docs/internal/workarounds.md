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
| [W-001](#w-001-hash_string-用-i32-deref-绕-v0-codegen-loadsb-错) | RESOLVED (v0.8 commit 9) | hash_string 改 byte-by-byte `*u8` deref + length mix (FNV-1a), 真修 W-001 副作用 |
| [W-002](#w-002-mainjhyy-重命名绕-jhyy_v1-hash_string-堆损坏) | RESOLVED (v0.9 wip commit 2.12) | 211 个 src0 标识符 `_v1` 后缀化 revert 回原名, W-001 真修后失效 |
| [W-003](#w-003-jhyy_v1-let-_-fncall-顶层-嵌套-segfault) | ✅ RESOLVED (transitive — jhyy_v1.exe.exe sha `ba94df93...` 已消除 Bug 7/7b 触发面; minimal repros for top-level + nested + NODE_ASSIGN[NODE_FIELD] all 5×5 PASS on canonical, 2026-08-12 verified) | `let _ = fncall(...)` 改 direct call，绕 jhyy_v1 codegen segfault（Bug 7/7b） |
| [W-004](#w-004-short-local-var-4-chars--symtab-hash-撞--jhyy_v1-field-assign-死循环) | RESOLVED (transitively closed by W-001 byte-by-byte FNV-1a 真修 — minimal repro + 4 boundary variations all pass codegen on jhyy_v1 (sha `ba94df93...`), 2026-08-12 verified) | 短（≤4 字符）local var / fn 参数 / field 改名绕 jhyy_v1 symtab hash 撞（stack overflow） |
| [W-005](#w-005-let-mut--assign--jhyy_v1-codegen-segfault) | RESOLVED (v0.9 wip commit 2.13) | `let mut x: T; x = expr;` 改 `*pos_ptr += ...` 绕 jhyy_v1 codegen segfault；commit 2.11 CGContext 布局对齐真修 + commit 2.13 revert 16 处回 `let mut` 风格 |
| [W-006](#w-006-jhyy_v1-return-x--y-两-1-char-var-发-127qbe-fail) | RESOLVED (transitively closed by Sprint 4.21-4.25 W-005 #2 真修 chain — minimal repro no longer triggers, 2026-08-11 verified) | jhyy_v1 codegen 让两个 1-char 局部变量在 `return x ± y` 共享同一 stack slot → QBE fail / exit 127；改名或加类型注解绕 |
| [W-007](#w-007-jhyy_v1-fn--i64--return--literal-as-i64-emit-w-copy) | ✅ RESOLVED (transitive — jhyy_v1.exe.exe sha `ba94df93...` 已含 cg_convert_arg `src=W → dst=L` extsw 分支镜像 v0.8 commit 7 `0453cef`, 2026-08-12 5x5 PASS verified on 4 BAD variants, IL byte-equal C-side) | jhyy_v1 codegen 把 `fn() -> i64 { return X as i64; }` 的 return value 当 w（32-bit）emit → QBE "invalid type for jump argument" 错 |
| [W-008](#w-008-jhyy_v1-cg_find_field_offset-漏一层-deref-i64-struct-field-emit-w-loadw) | RESOLVED | jhyy_v1 codegen NODE_FIELD 查 struct field type 时把 `*u8` 指针当 `**u8` 解了一层 → i64/pointer struct field 全 emit `=w loadw` 而非 `=l loadl` → QBE 拒绝 |
| [W-009](#w-009-jhyy_v1-cg_convert_arg-src_t--0-返回-arg-未-coerce-导致-literal-0-w-copy-0-在-ceql-被-reject) | RESOLVED | jhyy_v1 codegen cg_convert_arg 在 `src_t==0` 时直接 return arg，但 literal 0 实际 emit `=w copy 0`（因 qbe_type_of(NULL)=QBE_W）→ 比较 l 字段（pointer / i64 / u64）时 `ceql`/`csltl` 等操作码两边操作数类型不匹配 → QBE "invalid type for second operand" 错 |
| [B-let2 (cross-ref)](#cross-ref-b-let2-stage-1-byte-equal-codegen-gap) | RESOLVED (v0.9 commit 2.5) | jhyy_v1 `cg_convert_arg` 缺 `src=l, dst=w` narrow 分支 → `i64 → i32` 字段赋值 / `as` 转换 emit 错 IL。详见 [`codegen-pitfalls.md` § 2.2](codegen-pitfalls.md) |
| [W-008 ↔ W-009 ↔ W-007 ↔ W-005 (cross-ref)](#cross-ref-w-008--w-009--w-007--w-005-codegen-转化路径联动) | ✅ ALL RESOLVED (W-005 v0.9 wip 2.13 / W-008 v0.8 c11 / W-009 v0.8 c12 / W-007 transitive 2026-08-12) | 4 个 workaround 都在 jhyy_v1 `cg_convert_arg` + NODE_ASSIGN + NODE_FIELD codegen 路径, 全 RESOLVED |
| [W-010](#w-010-jhyy-端-max_locals--512-vs-c-端-1024--cg_add_local-静默溢出致-t0-污染) | RESOLVED (v0.9 wip commit 2.79) | jhyy-side `MAX_LOCALS=512` 比 C-side `1024` 小 2× → cg_expr 本地变量数溢出时 cg_add_local 静默返回 0 → cg_find_local miss → emit `%t0`(QBE temp 0,sentinel); align jhyy-side 到 1024 全消除 |
| [W-012](#w-012-codegen-emit-layer-sentinel-pollution-cg_copy_struct-emit-copy--t0-when-src_addrundef) | RESOLVED (v0.9 wip commit 2.81) | C/jhyy `cg_copy_struct` 在 src/dst 是 sentinel `IRVal{0}` (kind=IRVAL_TEMP, id=0) 时仍逐字段 emit `copy %t0`, QBE reject. 真修: `irval_is_undef(v)` sentinel 守卫 (3 emit 点 + 1 helper). |

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

## W-001 RESOLVED — v0.8 commit 9 (`d570c72`) byte-by-byte 真修

**日期:** 2026-08-03 (commit `d570c72`)
**修复:** `compiler/src0/util.jhyy` `hash_string` 改成 byte-by-byte `*u8` deref + length mix (FNV-1a)
- L222: `let c32 = *((s as i64 + (*i_ptr)) as *u8) as i32;` — `*u8` deref 1 byte (`loadsb` 仍可走, 不需 overread)
- 移除了 `*((s as i64 + aligned) as *i32)` 的 4-byte read 模式 (commit 之前 L199-213 整段)
- 移除了 `let w = ...` + `let sh = ...` + `(w >> sh) & 255` 的 shift+mask workaround

**为什么真修 (而不是简单 revert workaround):**
- W-001 根因不在 v0 codegen `loadsb` 错 (post-v0.6 sprint 实际已修复 destination 类型推导 — codegen L6+ 已正确处理 `*u8` deref 出 `w` class)
- 真正的"segfault 副作用" 来自 `*i32` 4-byte read overread slack 字节进 hash → hash 错位 → SymTab lookup 误路由 (W-002 根因)
- byte-by-byte 真修消除 overread → W-002 失效条件 (ii) 满足 → W-002 也可移除

**验证:**
- v0 编 src0/main.jhyy → 1.18MB IL, 553 functions
- jhyy_v1 编 hello.jhyy 等小测试 byte-equal PASS (stage1 6/7 持平)
- v0 + regress 持平 50/53

**引用:**
- commit `d570c72` (v0.8 commit 9: W-001 byte-by-byte hash + W-005 let-mut workaround)
- 源码注释 `util.jhyy:212-231`
- 配合 v0.9 wip commit 2.12 撤销 W-002 211 个 `_v1` 后缀 revert (见下)

---

## W-002: main.jhyy 重命名绕 jhyy_v1 hash_string 堆损坏

**ID:** W-002
**状态:** RESOLVED (v0.9 wip commit 2.12)
**日期:** 2026-08-03 (ACTIVE) → 2026-08-05 (RESOLVED)
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

**局限性（重要, 历史记录）：** W-002 修了 hash_string 触发面 bug，但 jhyy_v1 编 main.jhyy **仍然 segfault**（exit 139, 2026-08-04 之前观察）—— 因为 main.jhyy 还有别的触发 jhyy_v1 codegen bug 的模式（Bug 7 `let _ = fncall`、Bug 9 嵌套 if/else phi、Bug 13/16 struct 值传递等；详见 `memory/feedback_v0_codegen_bug_workarounds.md`）。**但** W-001 真正修复 + 后续 v0.9 wip commit 2.5~2.11 修了 B-φ1/B-struct/B-match/W-005 phase 1+2, main.jhyy segfault 触发面已大量消除 — v0.9 wip commit 2.12 revert 后是否还 segfault 由 commit 2.12 的 **observation step** 检验 (commit 2.12 plan § observation)。

**失效条件:**（任一即可移除 W-002）
- jhyy_v1 的 codegen 对 hash_string 生成的 IL 与 v0 IL byte-equal（diff 通过）→ 重新引入原名
- 或 v0 codegen 修了 W-001 的副作用（W-001 workaround 改成 byte-by-byte 不再 overread）—— 此时即使 jhyy_v1 触发面不变也不再 segfault

**superseder:** ✅ 已实现 (v0.9 wip commit 2.12 — W-001 byte-by-byte 真修 → W-002 失效条件 (ii) 满足 → 211 个 `_v1` 后缀 revert 回原名)

**W-002 RESOLVED section:** 见下方"W-002 RESOLVED — v0.9 wip commit 2.12 211 revert"

**引用:**
- 详细 bisect 记录见 `memory/project_bootstrap_closure_state.md`
- 测试用例 `tmp/tm_*.jhyy`
- 完整 rename 映射 `compiler/src0/_W002_rename_map.txt`
- v0.8 commit 6 (efc41bf) `wip: bisect heap corruption`
- v0.8 commit 7 (0453cef) `W-002: 211 个标识符 _v1 后缀化 + workarounds.md`
- 战略决策 `memory/project_bootstrap_closure_state.md` § Bisect findings

---

## W-002 RESOLVED — v0.9 wip commit 2.12 211 revert

**日期:** 2026-08-05 (commit pending ship)
**修复:** `compiler/src0/_W002_rename_map.txt` 211 个 `X -> X_v1` 反向 sed revert 回原名

**为什么 revert:**
- W-001 根因 (hash_string `*i32` overread slack 字节) 在 v0.8 commit 9 (`d570c72`) 已真修 → 改 byte-by-byte `*u8` deref
- byte-by-byte 真修后, hash_string 不再 overread → slack 字节不再污染 hash → W-002 触发面消失
- 211 个 `_v1` 后缀变成纯 cosmetic 噪声, 跟原 code base 分离, 增加 review burden + 阻碍 future bisect
- revert 后 src0/ 跟 v0 端 C 源码更接近 → 后续 v1.0.0 sprint 3+ 翻译难度降低

**实施步骤 (scripted, 见 commit 2.12 changelog):**
1. 读 `_W002_rename_map.txt` 生成反向 sed: `s/X_v1\b/X/g` per 211 identifier
2. 在 src0/ 11 个 .jhyy 文件批量 apply (1701 occurrences: codegen 600 / sema 309 / parser 282 / main 186 / types 87 / ast 57 / ir 47 / util 44 / lexer 43 / symtab 28 / arena 16)
3. v0 build + regress 持平 50/53
4. 新 jhyy_v1 编 src0/main.jhyy → **observation step** (per commit 2.12 plan):
   - segfault 消除 → A 段 hard closure 提前
   - segfault 还在 → 推 v1.0 sprint 3 B' 阶段
5. stage1 byte-equal 持平 6/7

**保留历史信息:**
- W-002 ACTIVE 期间的实施细节 (改名规则、影响范围、改名清单、局限性、引用) 保留在上方"W-002 ACTIVE 期间" 标题下, 作为 ACTIVE 历史归档
- `_W002_rename_map.txt` 保留作为可重放参考 (已不需要, 但 archive)

**引用:**
- v0.9 wip commit 2.12 (this commit) — 211 revert
- v0.8 commit 9 (`d570c72`) — W-001 byte-by-byte 真修 (根因消除)
- 配合 W-001 RESOLVED section (上方)

### Archive 文件 (v0.9 wip commit 2.14 标记)

W-002 revert 实施时产生的 archive 文件保留作为可重放参考:

| 文件 | git 状态 | 大小 | 用途 |
|------|---------|------|------|
| `compiler/src0/_W002_rename_map.txt` | **tracked** (commit 2.12 ship 时已 ship, hash `8a9de1c`) | 4982B | 211 个 `X → X_v1` rename mapping (反向应用即可 revert) |
| `compiler/src0/_W002_revert.py` | **gitignored** (`.gitignore` `_*.py` 规则) | 2220B | 一次性 revert 脚本 (2026-08-05 实施完成, 已 ship 后失去保留价值) |

**清理决策 (v0.9 wip commit 2.14)**:
- `_W002_revert.py`: **删除** (一次性工具, 已 ship, 不再需要; 占用磁盘 clutter)
- `_W002_rename_map.txt`: **保留 + 顶部加 README** (未来如果需要重新引入 W-002 rename 可直接当 input; 499 行 5KB 占用低; ship history 保留)

**README 注释 (添加在 `_W002_rename_map.txt` 顶部)**:
```
# ════════════════════════════════════════════════════════════════
# W-002 ARCHIVE — 211 个 src0/ identifier 的 `X → X_v1` rename map
# ════════════════════════════════════════════════════════════════
# 历史: v0.8 commit 7 (`0453cef`) 引入 W-002 (绕 hash_string *i32 overread)
#       v0.8 commit 9 (`d570c72`) W-001 真修后 W-002 失效
#       v0.9 wip commit 2.12 (`8a9de1c`) 211 revert 回原名
# 状态: RESOLVED (per docs/internal/workarounds.md § W-002)
# 用途: archive — 保留作为可重放参考; 未来若需重新引入 W-002 可直接当 input
# ════════════════════════════════════════════════════════════════
```

**引用**:
- `compiler/src0/_W002_rename_map.txt` (tracked, archive)
- `compiler/src0/_W002_revert.py` (gitignored, 已删 2026-08-05)
- v0.9 wip commit 2.14 — 标记 archive + 清理 + README 注释

---

## W-003: jhyy_v1 `let _ = fncall(...)` 顶层 / 嵌套 segfault → direct call (top-level only)

**ID:** W-003
**状态:** ✅ RESOLVED (transitive — jhyy_v1.exe.exe sha `ba94df93...` 已消除 Bug 7/7b 触发面,minimal repros for top-level + nested + NODE_ASSIGN[NODE_FIELD] all 5×5 PASS, 2026-08-12 verified)
**日期:** 2026-08-03 (ACTIVE) → 2026-08-12 (RESOLVED transitive)
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

### W-003 RESOLVED — transitively closed by Sprint 4.21-4.25 W-005 #2 真修 chain (2026-08-12)

**Sprint v1.1.3 verification (5×5 PASS on canonical jhyy_v1.exe.exe sha `ba94df93`)**:

| Trigger | Source | Expected | 5×5 |
|---------|--------|----------|------|
| **Bug 7 (top-level)** | `fn main_jhyy() -> i32 { let _x = noop(42); return 0; }` | EXIT=0 | ✅ 5/5 |
| **Bug 7 (top-level wide, 10 calls)** | 10 个连续 `let _X = store_byte(N, 0);` | EXIT=42 | ✅ 5/5 |
| **Bug 7b (1-level nested if)** | `if x==1 { if x==1 { let _d = noop(x); } }` | EXIT=0 | ✅ 5/5 |
| **Bug 7b (2-level nested if-if-if)** | `if x==1 { if y==2 { if z==3 { let _d = noop(x+y+z); ... } } }` | EXIT=5 | ✅ 5/5 |
| **Bug 7b + NODE_ASSIGN[NODE_FIELD]** | struct `Pair {a,b}` 嵌套 if + `let _s = sink(o.a); o.a = 99;` | EXIT=99 | ✅ 5/5 |
| **Bug 7b + for + if + mut** | `for i in 0..5 { if i>0 { let _d = noop(sum+i); sum = sum + i; } }` | EXIT=10 | ✅ 5/5 |

**关键证据 — 当前 src0/ 实际状态**:89 处 `let _X = fncall()` 仍存 (其中 **7** 在 codegen.jhyy,**54** 在 sema.jhyy,**17** lexer,**5** parser,**3** main,**2** _driver_sema,**1** ir.jhyy)。**所有 89 处都在嵌套 if/while 块内 (depth ≥ 2)** — 即正是 Bug 7b 的触发面,且全部正常 compile 通过 (regress_v1 50/50 PASS)。证明 Bug 7b 已自然消除,workaround v3 仅出于历史保险性保留。

**真因** (per Sprint 4.21-4.25 W-005 #2 真修 chain,commits `be3be33` / `fad9de2`):
- Bug 7/7b 根因 = IRVal struct pass-by-value stale pointer(per `project_sprint4_7_irval_pass_by_value_bug.md`)
- 真修在 jhyy_v1 `cg_copy_struct` + `irval_is_undef` 守卫 (8 处)+ C-side 同步对齐(per `feedback_codegen_workaround_linkage.md` 链路 1-3)
- 守卫消除 stale pointer 后,`let _ = fncall()` 不再 emit `=w copy %t0` 污染 IL,codegen 路径正常

**Out of scope (NOT W-003)**:
- **v3 workaround 29 处** `let _X = fncall()` → `fncall()` 的 revert 不在本 sprint 范围. 类比 W-002 commit 2.12 (211 个 `_v1` 后缀 revert),W-003 revert 需要单独 cleanup commit. **可在 Sprint v1.1.x 后续做**:验证 baseline 50/53 持平下 revert 29 处 top-level 改回 `let _X = fncall()` 风格,恢复代码自然性.

**W-003 失效条件** (per workarounds.md line 307): v0 codegen 修复 `let _ = fncall(...)` emit → W-003 可移除. 实际: jhyy_v1 codegen 已 ship 修复,W-003 失效条件满足,可标 RESOLVED.

---

## W-004: short local var (≤4 chars) → symtab hash 撞 → jhyy_v1 field assign 死循环

**ID:** W-004
**状态:** RESOLVED (transitive — W-001 byte-by-byte FNV-1a 真修 indirect coverage; minimal repro + 4 boundary variations all pass codegen on jhyy_v1 (sha `ba94df93...`) with EXIT=1 (link stage only), 2026-08-12 verified)
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

**superseder:** ✅ closed (root cause = W-001 byte-by-byte FNV-1a 真修 ship in v0.8 commit 9 `d570c72`, Task #60 真修 unblocked verification path in v0.9 wip commit 2.15 `52843b6`) — 详见下方"## W-004 RESOLVED — transitively closed by W-001 byte-by-byte 真修 (2026-08-12)" 段

**引用:**
- `memory/feedback_v0_codegen_bug_workarounds.md` Bug 6 (let-mut assignment) + Bug 1 (hash_string overread)
- W-002 (`docs/internal/workarounds.md` § W-002) 修了 211 个全局/函数名，未覆盖局部 var
- 复现测试 `tmp/test_w4.jhyy` ~ `tmp/test_w8.jhyy`

### 验证状态 2026-08-05 (v0.9 wip commit 2.14) — BLOCKED

**目标**: 验证 jhyy_v1 编 src0/{codegen,parser,sema}.jhyy 是否触发 stack overflow (W-004 失效条件 (i))。

**结果**: 验证 BLOCKED — 3 个目标文件**单独编译都跑不到 codegen 阶段**:

| 文件 | 现象 | 阻断根因 |
|------|------|---------|
| `src0/codegen.jhyy` | `L2198: unexpected token 'while' in expression` + 6 parse errors | Task #60 (parse_expr `while`/else) |
| `src0/sema.jhyy` | `L1191: unexpected token 'while' in expression` + parse errors | Task #60 (同上) |
| `src0/parser.jhyy` | 9+ sema errors (unknown type `*Node`, undefined variable, 不能 access field) | 跨文件 type (`*Node`, `Token`, `Sym` 等) 在 ast.jhyy / symtab.jhyy 等, 单独编 parser 拿不到 |

**full src0/main.jhyy (inline_imports 全拼接)**: 仍 segfault (exit 139) — 但 segfault 是在 parse 阶段 (Task #60 触发), 不是 codegen 阶段 (W-004 触发)。Task #60 是上游 blocker, 不修就无法隔离 W-004。

**结论**: W-004 标 RESOLVED 失效条件 (i) 无法满足, 推 v1.0.0 sprint 3+ Task #60 修后**再做 W-004 验证**。W-004 status 保持 ACTIVE (BLOCKED verification)。

**contingency**: 如果 Task #60 修后, jhyy_v1 编 src0/codegen.jhyy / parser.jhyy / sema.jhyy 不再 stack overflow → W-004 可标 RESOLVED (W-001 真修已间接覆盖);如果仍 stack overflow → 立刻开 commit 2.15 (W-004 批量改名, 触发面消除)。

### 验证状态 2026-08-12 (Sprint v1.1.1) — ✅ PASS → 标 RESOLVED (transitive)

**Task #60 真修 ship 2026-08-06** (commit `52843b6` v0.9 wip commit 2.15) → 验证路径 unblocked. Sprint v1.1.1 实际跑了 6 个最小 repro (BAD + GOOD + 4 boundary variations), jhyy_v1 (sha `ba94df93...`) 全部**通过 codegen 阶段** (不再触发 0xC00000FD STACK OVERFLOW):

| 测试 | 触发面 (fn / var / field) | C-side 行为 | jhyy_v1 行为 | 期望 (W-004 真修) |
|------|---------------------------|-------------|--------------|---------------------|
| BAD (workarounds.md L343-349) | `main`(4) / `a`(1) / `cur`(3) | EXIT=1 (link fail due to `main` symbol conflict with runtime.c) | EXIT=1 (same) | ✅ codegen OK |
| GOOD (workarounds.md L351-358) | `ab`(2) / `arena_local`(11) / `current_value`(13) | EXIT=1 (link fail) | EXIT=1 (same) | ✅ codegen OK |
| v1 (extreme short) | `a`(1) / `b`(1) / `c`(1) | EXIT=1 | EXIT=1 | ✅ codegen OK |
| v2 (all 4-char) | `aaaa`(4) / `bbbb`(4) / `cccc`(4) | EXIT=1 | EXIT=1 | ✅ codegen OK |
| v3 (5-char fn) | `entry`(5) / `b`(1) / `c`(1) | EXIT=1 | EXIT=1 | ✅ codegen OK |
| v4 (7-char field) | `a`(1) / `b`(1) / `current`(7) | EXIT=1 | EXIT=1 | ✅ codegen OK |

**关键观察**: jhyy_v1 在所有 6 个测试中, codegen 阶段日志 `Pass B start → B i=0 → cg_module done → codegen done` 完整, 后续 link 阶段失败只是因为 fn 名 (`main` / `a` / `ab` 等) 跟 runtime.c 的 `int main(int, char**)` 冲突 — **不是 W-004 触发**. 之前 W-004 触发是 exit 3221226356 (0xC00000FD STACK OVERFLOW), 现在 6/6 都是 EXIT=1 + "gcc link failed", 完全没有 stack overflow.

**W-004 vs W-006 真因 关系 (避免误诊)**:
- W-006 真因 = W-005 #2 family (cg_expr IRVal struct pass-by-value stale pointer) — Sprint 4.21-4.25 真修时一并解决
- W-004 真因 = W-001 family (hash_string `*i32` deref overread → symtab 撞 → cg_emit_store / cg_copy_struct 走错 sym → 死循环)
- **不同 family** — W-006 transitive close 不连带 W-004. W-004 独立被 W-001 byte-by-byte FNV-1a 真修覆盖.

**为什么之前 W-004 没识别成 W-001 family**:
- 当时 (2026-08-03) 诊断假设是 "stack-slot allocator for 短名复用 slot" (看到死循环 + 短名现象)
- 但实际根因是 `hash_string` 用 `*i32` deref 一次读 4 byte, 短字符串 (≤4 char) 把后续 slack 字节吸进 hash 值, 多个不同 ident 撞同一 slot
- W-002 当时 (2026-08-04) 修了 211 个全局/函数名, 但漏掉**局部 var + struct field** (per W-004 entry line 331)
- W-001 真修 (2026-08-04 commit `d570c72`) 改 byte-by-byte `*u8` deref + length mix (FNV-1a) → 短名不再 overread → symtab 不再撞 → W-004 失效条件 (i) 满足

### 真修 chain (按 commit 时间序, 仅列与 W-004 有关者)

| Commit | Sprint | 改动 | 跟 W-004 关系 |
|--------|--------|------|----------------|
| `d570c72` (v0.8 commit 9) | — | W-001 byte-by-byte FNV-1a 真修 (`hash_string` 改 `*u8` deref + length mix) | **关键 commit** — 短名不再 overread, symtab 不再撞 |
| `52843b6` (v0.9 wip 2.15) | — | Task #60 真修 (parse_if body inline parse_while 嵌套 TOKEN_WHILE 分支) | 验证路径 unblock — 不修则 src0/{codegen,sema}.jhyy 编不过 |
| Sprint 4.21-4.25 chain | 4.21-4.25 | W-005 #2 family 真修 (CGContext layout, IRVal const ptr, sentinel guard) | **非 W-004 直接根因** — W-006 跟 W-005 同 family 被一并修, 但 W-004 是 W-001 family 独立 |

### 留给未来 (post-v1.1.1 ship)

- W-004 workaround 代码本身 (`let arena_local` 等长名 + `arena_local.current_value` 等长 field) **不需 revert** — 当前不被触发, 保留不破坏 src0/ 自然性 (跟 W-002 同样风格的 211 改名为对照)
- 短名 (`let x`, `let y`, field `cur` 等) 的 revert 留给 Sprint v1.1.x post-W-007 真修 ship 后做, 跟 src0/*.jhyy 100% natural 目标一起
- 未来 reader: 若看到 src0/ 里有 `arena_local.current_value` 等"看起来不必要的长名", 不要误以为是 stale workaround — 是 W-004 历史 fallback, 当前 W-001 真修已使其非必要但保留以维持翻译风格一致

---

## W-005: `let mut x: T; x = expr;` 改 `*pos_ptr += ...` 绕 jhyy_v1 codegen segfault

**ID:** W-005
**状态:** RESOLVED (v0.9 wip commit 2.13)
**日期:** 2026-08-03 (workaround) → 2026-08-05 (commit 2.11 真修) → 2026-08-05 (commit 2.13 revert 加固)
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

**影响范围（src0/ 中需 W-005 替换的 let-mut + assign 位置）— commit 2.13 revert 后:**

| 文件 | 函数 | 变量 | revert 数 |
|------|------|------|-----------|
| main.jhyy | path_to_win | idx_ptr | 1 |
| main.jhyy | run_qbe | pos_v1 | 1 var / 5 assign |
| main.jhyy | link_with_gcc | pos_v2 | 1 var / 9 assign |
| main.jhyy | cmd_compile (argv walk) | input_v1 / user_out_v1 / i_v4 | 3 vars |
| main.jhyy | cmd_compile (out_buf) | out_buf if-else workaround | 1 简化 |
| arena.jhyy | arena_new_block | size_v1 | 1 |
| arena.jhyy | arena_free | b | 1 |
| util.jhyy | sb_grow | new_cap | 1 |
| util.jhyy | hash_string | h / i | 2 |
| util.jhyy | hm_put | idx | 1 |
| util.jhyy | hm_grow (outer + inner) | i / idx | 2 |
| util.jhyy | hm_get | idx | 1 |
| **总计** | | | **15 vars + 1 if-else 简化** (= 16 模式 revert) |

**commit 2.13 验证 (2026-08-05):** 所有 16 模式 revert 回 `let mut x; x = expr;` 风格后：
- v0 build clean (无 warning)
- regress 持平 50/53 PASS
- stage1 byte-equal 持平 6/7 PASS
- jhyy_v1.exe (built from reverted src0/) 可执行,跟 commit 2.12 路径完全一致
- main.jhyy runtime (jhyy_v1 编 src0/main.jhyy 跑 main.jhyy) **仍 segfault (exit 139)** —— 这是 main.jhyy 自身更大尺寸 (25KB) 引发的 W-001 类 heap corruption 问题,不在 commit 2.13 范围,推 v1.0 sprint 3 B' 阶段

**W-005 局限性:** 这是绕 `NODE_ASSIGN[NODE_IDENT]` 触发面。`let mut struct; struct.field = X` (NODE_ASSIGN[NODE_FIELD]) 走不同路径，W-005 不修。**Bug 6+7b 的根因修复需在 jhyy_v1 codegen.c 端修 NODE_ASSIGN 的 emit，post v1.0.0。**

**失效条件:** jhyy_v1 codegen 修对 NODE_ASSIGN[NODE_IDENT] 的 let-mut target → emit 正确 `storew` 到 stack slot → W-005 可移除并恢复 `let mut x; x = ...;` 风格。

**superseder:** v0.9 wip commit 2.10 (诊断性 doc-only,无 codegen 改动) — 真修推后到 v0.9 wip commit 2.11+ 或更晚。

**v0.9 wip commit 2.11 (2026-08-05) — W-005 真修 phase 2 实施完成:**
- C 端 `codegen.c` CGContext 布局改成 jhyy 端布局:
  - `LocalEntry locals[MAX_LOCALS]` (inline 24576 bytes) → `LocalEntry *locals` (calloc'd)
  - `IRVal sret_slot` (32 bytes) → `int64_t sret_slot_id` (8 bytes, = temp number)
  - `IRVal loop_starts/ends/continues[MAX_LOOP_DEPTH]` (3×1024 bytes) → `IRVal *loop_starts/ends/continues` (3×calloc'd)
  - 字段顺序: `loop_depth` 挪到 `has_sret` 之后 (跟 jhyy 端布局一致)
- C 端 `cg_func` 加 `calloc` ×4 + `free` ×4 (新 `<stdlib.h>` include)
- C 端所有 `cg->sret_slot` → 构造 `IRVal` literal (`{0}` + `sret_addr.id = sret_slot_id; sret_addr.qbe_type = 'l';`)
- 全部 9 字段 offset 现在跟 jhyy 端 CGCONTEXT_SIZE = 72 字节精确对齐
- **验证 (commit 2.11):**
  - regress 50/53 PASS, 0 FAIL, 3 SKIP — 持平 baseline
  - byte-equal 持平 5/7 (5 PASS / 2 FAIL: match_exhaustive + const_array)
  - **let-mut 最小复现 `tmp/test_w5.jhyy`:** jhyy_v1 编译 + 运行 → exit=20 (输出 `x = 20`) — **不再 segfault**! 之前 commit 2.10 阶段 jhyy_v1 编译同一文件 segfault (exit 139)
- 剩余影响: W-005 workaround (`*pos_ptr_vN` 模式) 在 src0/ 仍有 14 处使用。**W-005 现在可安全移除** — 下个 commit (2.13) 加固可 revert 14 处 `*pos_ptr_vN` 累加 → 改回 `let mut x; x += n` 风格。W-005 在 commit 2.13 移出 workarounds.md active 列表。

**根因重诊断(v0.9 wip commit 2.10,2026-08-05):** W-005 segfault **不是** "NODE_ASSIGN emit 错" 那么直接 —— 是 **C 端 codegen.c CGContext 跟 jhyy 端 codegen.jhyy CGContext struct 布局不匹配**:
- C 端: `LocalEntry locals[MAX_LOCALS]` (24576 bytes inline array),nlocals 在 offset 24584, has_sret 在 offset 24592+, loop_starts 在 offset 24600+ ...
- Jhyy 端: `locals: *u8` (指针,arena 单独 alloc),nlocals 在 offset 16, has_sret 在 offset 40, loop_starts 在 offset 48 ...
- Jhyy_v1 编译后,offset 错位 → `(*cg).locals` 实际读到 `locals[0].sym` (jhyy 当指针用) → cg_find_local 把 sym 指针当 locals buffer base → `ptr_add_u8(sym, 0)` 指向 Sym 结构 → `entry_sym_p == sym` 凑巧成立 → 后续读 `entry_ptr + 8` (kind 字段) 实际读 Sym 结构的非 sym 字节 → 越界读 → segfault
- **修复路径 (post-v0.9 wip):** 把 C 端 CGContext 改成 jhyy 端布局 (LocalEntry *locals + separate alloc) + 把 sret_slot 改成 sret_slot_id i64 + 把 loop_starts/ends/continues 改成 *u8 指针(单独 arena alloc)。涉及全部 codegen.c 字段访问路径 (~30 处)。**scope 超出 commit 2.10**,推迟到 commit 2.11+ 或独立 sprint。

**影响:** 不影响 commit 2.10 目标 (byte-equal 持平 5/7, regress 持平) —— 现状 byte-equal 5/7 已稳定,let-mut + assign 触发面继续走 W-005 workaround (`*pos_ptr_vN` 模式)。

**引用:**
- `memory/feedback_v0_codegen_bug_workarounds.md` Bug 6 (let-mut assignment) + Bug 7b (nested let-mut)
- W-003 (`docs/internal/workarounds.md` § W-003) 修了 `let _X = fncall()` 顶层 direct call 模式，未覆盖 let-mut + assign
- W-004 修了短 var 名导致 symtab hash 撞死循环，未覆盖 let-mut + assign segfault
- 复现测试 `tmp/test_w4_lit.jhyy` / `tmp/test_w4_v1.jhyy`

---

## W-006: jhyy_v1 `return x ± y` 两 1-char var 发 127（QBE fail）

**ID:** W-006
**状态:** RESOLVED (transitively closed by Sprint 4.21-4.25 W-005 #2 真修 chain — minimal repro no longer triggers, 2026-08-11 verified)
**日期:** 2026-08-04 (open) → 2026-08-11 (close, transitive)
**触发面:** 函数体末尾 `return X OP Y`（OP ∈ `+`, `-`），X 和 Y 都是 1-char 局部变量（任意 i32/i64 类型）。
**症状:** jhyy_v1 编译 → exit 127（无输出）→ 可能是 segfault 也可能是 QBE fail。QBE fail 时报 "invalid type for jump argument"。
**最小复现:**
```jhyy
// BAD (exit 127 / QBE fail):
fn main_jhyy() -> i32 {
    let x = 42 as i32;
    let y = 7 as i32;
    return x + y;
}
// jhyy_v1: exit 127

// GOOD (workaround 1 — rename):
fn main_jhyy() -> i32 {
    let xx = 42 as i32;
    let yy = 7 as i32;
    return xx + yy;
}
// jhyy_v1: OK (exit 0)

// GOOD (workaround 2 — type annotation):
fn main_jhyy() -> i32 {
    let x: i32 = 42 as i32;
    let y: i32 = 7 as i32;
    return x + y;
}
// jhyy_v1: OK

// GOOD (workaround 3 — intermediate let):
fn main_jhyy() -> i32 {
    let x = 42 as i32;
    let y = 7 as i32;
    let z = x + y;
    return z;
}
// jhyy_v1: OK
```

**根因嫌疑:** jhyy_v1 codegen 的 stack-slot allocator 给两个 1-char 局部 var 分配了**同一个 stack offset**（slot reuse bug）。当 `x + y` 在 return 表达式上下文被直接编译时，emit 的 IL 中两个 operand 指向同一临时，结果 QBE 拒绝（type mismatch 或 错位）→ 退化成 exit 127。v0 codegen 没这个问题。

**workaround:** 三个等价方案（任选一）：
1. **rename：** 把 X 或 Y 改成 ≥2 字符（`xx`、`yy` 等）
2. **type annotation：** `let x: i32 = 42 as i32;` 显式声明类型
3. **intermediate let：** `let z = x + y; return z;` 强制中间 stack slot

**影响范围:** 触发面在 src0/ 极常见：所有短局部变量（`x`/`y`/`n`/`i`/`p`/`h`/`c` 等）参与 `return X + Y` 或 `return X - Y` 时都中招。需要机械扫描：
- util.jhyy: 至少 12 个 1-char `let`（`n`、`p`、`h`、`c`、`e`、`i`），多个 `*i_ptr + 1` 累加模式
- arena.jhyy: `arena_free` 的 `b = next` 累加（已用 W-005 转 `*i64` 绕过）
- main.jhyy: `path_to_win` 索引累加（已用 W-005 转 `*i64` 绕过）
- lexer.jhyy / parser.jhyy / sema.jhyy / codegen.jhyy: 推测大量触发面（未审计）

**W-006 局限性:** 仅触发 `return X ± Y` 直接形式。中间 let / 比较 / 字段访问不触发。`*ptr_ptr += n` 累加（已 W-005 转过的）也不触发，因为 deref 走 NODE_DEREF 路径不同。

**失效条件:** jhyy_v1 codegen 修对 stack-slot allocator（按变量名长度 ≤1 时分配不同 slot）→ W-006 可移除并恢复 `let x = ...; return x + y;` 风格。

**superseder:** TBD（jhyy_v1 codegen fix sprint，post v1.0.0 落地后）

**引用:**
- 复现 `_test_e.jhyy` / `_test_y.jhyy`（x + y / a + b 都触发）
- v0 同源码编译 exit 0 → 是 jhyy_v1 自身 bug，不是源 jhyy 问题
- W-004 修了短名（≤4 char）symtab hash 撞死循环；W-006 是 codegen slot allocator bug，**不同 bug**

### 触发面扫描 2026-08-05 — dormant (0 活跃触发面)

**目标**: 扫当前 src0/ 看 `return X ± Y` (X, Y 都是 1-char) 触发面是否仍存在。

**扫描方法**: `grep -rn 'return [a-z_]\{1,2\} [+\-] [a-z_]\{1,2\}[^_]' compiler/src0/*.jhyy` (排除 2 字符含下划线的合法名)。

**结果**: **0 命中** — 当前 src0/ 内所有 `return X ± Y` 形式已自然避免 W-006 触发面:
- 翻译阶段已用 `(p as i64 + off) as *u8` cast-chain 形式替代直接 var+var (util.jhyy 11 处)
- 翻译阶段已用 `return n;` / `return 0 as *u8;` / `return (n as i64 + NODE_SIZE()) as *Type;` 单 operand 形式替代 (codegen / sema / ast)
- 翻译风格: `let z = x + y; return z;` intermediate let 已普遍 (避免直接 return sum)

**结论**: W-006 在当前 src0/ **0 活跃触发面**, 但根因 (codegen stack-slot allocator bug) 未真修, 新写代码仍可能触发。Status 保持 ACTIVE (dormant), 标记 "dormant" 提醒未来 reader。

**风险**: 如果未来写 `return x + y` (双 1-char) 又会触发 → 需机械改名 / 类型注解 / intermediate let。改动面在 codegen.jhyy stack-slot allocator 真修之前, 工作量随代码增长线性增加。

---

## W-006 RESOLVED — transitively closed by Sprint 4.21-4.25 W-005 #2 真修 chain (2026-08-11)

**日期**: 2026-08-11 (v1.1 wip commit 1.1, replaced earlier "doc-only escaped" framing)
**修复类型**: 真修 (transitive — 根因同 W-005 #2 family, 在 Sprint 4.21-4.25 真修过程中被一并解决)

### 误诊史 (为什么会写成 "escaped")

v1.1 wip commit 1.1 最初版本把 W-006 标 "RESOLVED (escaped — codegen fix deferred to v2.x)", 用户 challenge "为啥这个W006改个文档就完事了" 后立刻 reproduce 验证 → 发现 **minimal repro 已不触发** (IL 跟 C-side byte-equal, exe exit 正确). 重新审计 git log + 真修 chain 才知道 **W-006 跟 W-005 #2 是同 family, Sprint 4.21-4.25 真修 W-005 #2 时已经一并修了 W-006**.

### 真修 chain (按 commit 时间序, 仅列与 W-006 有关者)

| Commit | 改动 | 跟 W-006 的关系 |
|--------|------|----------------|
| `be3be33` (2.78) | Sprint 4.21 Phases C+D+G — cg_copy_struct 改 `const IRVal*` 入参 + cg_expr out-param 改指针 | 消除 IRVal struct pass-by-value 路径上 cg_expr 返回的临时 IRVal 在 caller 栈上 stale aliasing. **W-006 的 "两 1-char var 共享 stack slot" 实际不是 stack slot 复用, 而是 cg_expr 返回 IRVal 在 caller 栈上被后续调用覆盖** (后续 `x + y` 读 x 时实际读到 y 的 IRVal). |
| `fad9de2` (2.81) | Sprint 4.25 — W-005 #2 真修 (A' sentinel 守卫, 8 处 `irval_is_undef(v)` 守卫 + pre-increment next_tmp) | sentinel + pre-increment 确保每次 ir_new_tmp 都拿到唯一 ID, 杜绝 "两 var 指向同一个 `%t0`" 路径. 这一项是真修 W-006 的**关键 commit**. |
| `9b67e53` (2.79) | Sprint 4.23 — MAX_LOCALS 512→1024 | 边界相关: 之前 nlocals=512 在递归 / 长函数场景下 cg_add_local 返回 0 (silent skip) → 后续 cg_find_local 找不到返回 undef → undef IRVal 被 binop 当 operand 读 → 同样 cascade 出 W-006 的"两 var 共享栈帧"症状. |

### 为什么之前 W-006 没识别成 W-005 #2 family

- 当时的诊断假设是 "stack-slot allocator for ≤1-char vars 复用同一 slot" (看到两个 var 共享同一栈帧位置的现象, 推断是 allocator 在按 name 复用 slot).
- 但实际根因是 **cg_expr 返回 IRVal 时 struct pass-by-value 在 caller 栈上留下 stale pointer**, 后续读这个 var 时 IRVal 字段已被覆盖 — 表现为 "两 var 看似同一 slot".
- 当时 (2026-08-04) 没意识到 IRVal struct pass-by-value 是 systemic 问题, 把 W-006 当成独立 codegen 局点 bug 处理, 所以只记录 workaround + defer.

### 当前状态 (2026-08-11 实证)

- ✅ Minimal repro `let x = 42 as i32; let y = 7 as i32; return x + y;` → jhyy_v1 编 → IL byte-equal C-side, exe exit 49
- ✅ fib30.jhyy (用 `n - 1`, `n - 2` 1-char var 减法) → 直接 jhyy_v1 编 → IL 干净, exe 输出 "fib(30) = 832040"
- ✅ workarounds (rename / type annotation / intermediate let) 仍全部 OK (但已非必要)
- ✅ src0/ 扫描: `return X + Y` (X, Y ≤ 1 字符) 触发面 = 0 命中 — 当前翻译风格已不需要这些 workaround
- ✅ regress.py 50/50 + regress_v1.py 50/50 + stage1 byte-equal 7/7 持平

### 留给未来 (post-v1.1)

- W-006 三个 workaround 命名 (rename / type annotation / intermediate let) 可**机械 revert 回 `let x = ...; return x + y;` 风格** (Stage 2 N=3 闭环要求 jhyy_v1 编 jhyy_v1 编 src0/ 输出 byte-equal, 翻译风格应尽量少 workaround 噪声). 留给 Sprint v1.1.x post-W-007 真修 ship 后做.
- fib_renamed.jhyy 可考虑 revert 回 fib30.jhyy 同名 (历史标记保留, 不强求).

**superseder**: closed (root cause = W-005 #2 family)

**引用**:
- [`docs/plans/v1/v1.1.0任务清单 + 概要设计.md` § Sprint v1.1.1](../../plans/v1/v1.1.0任务清单%20+%20概要设计.md) — W-006 编排 (从 1st sprint 移到 "已真修" 状态)
- `memory/project_sprint4_21_phase_b_c_d_g_done.md` — Sprint 4.21 Phase C (cg_copy_struct const IRVal*)
- `memory/project_sprint4_25_a_prime_sentinel_guard.md` — Sprint 4.25 A' sentinel 真修
- Stage 1 byte-equal 7/7 PASS (持平 baseline)

**引用**:
- v1.1.0 plan [`docs/plans/v1/v1.1.0任务清单 + 概要设计.md`](../plans/v1/v1.1.0任务清单 + 概要设计.md) § Sprint v1.1.1
- 触发面扫描 2026-08-05: 见上方"### 触发面扫描 2026-08-05 — dormant (0 活跃触发面)" 段
- v1.1 wip commit 1.1 (this commit) — doc-only RESOLVED status flip

---

## W-007: jhyy_v1 `fn() -> i64 { return X as i64; }` emit `w copy`

**ID:** W-007
**状态:** ✅ RESOLVED (transitive — jhyy_v1.exe.exe sha `ba94df93...` 已含 type propagation fix per v0.8 commit 7 `0453cef` `cg_convert_arg src=W → dst=L extsw 分支补全`,2026-08-12 verified 5x5 PASS on 4 BAD variants, IL byte-equal C-side)
**日期:** 2026-08-04 (ACTIVE) → 2026-08-12 (RESOLVED transitive)
**触发面:** 函数体末尾 `return literal as i64;` 或 `let x = literal as i64; return x;`，且 literal 是字面整数常量。
**症状:** QBE 拒绝 → "invalid type for jump argument %t0 in block @start0"。jhyy_v1 编译 exit 1。
**最小复现:**
```jhyy
// BAD (QBE fail):
fn small_const() -> i64 { return 5 as i64; }
// jhyy_v1 emit:
//   export function l $small_const() {
//   @start0
//       %t0 =w copy 5      ← 函数返回 l (i64) 但 copy 是 w (32-bit)
//       ret %t0            ← QBE 拒绝
//   }
// QBE error: invalid type for jump argument %t0 in block @start0

// BAD 变体 2 (let + return):
fn small_const() -> i64 {
    let x = 5 as i64;
    return x;
}
// jhyy_v1: emit %t0 =w copy 5; ret %t0（同样错）

// BAD 变体 3 (arithmetic):
fn small_const() -> i64 {
    return (4 + 1) as i64;
}
// jhyy_v1: emit %t0 =w copy 4; %t1 =w copy 1; %t2 =w add %t0, %t1; ret %t2

// GOOD (workaround — 用 extern fn 包一层返回 i64):
extern fn some_64() -> i64;
fn small_const() -> i64 { return some_64(); }
// jhyy_v1: OK
```

**根因嫌疑:** jhyy_v1 codegen 的 const/copy emit 路径在类型推断时**丢失了 i64 类型信息**。NODE_INT_LIT 的默认 emit 类是 w (32-bit) — 看起来是 v0 早期版本的硬编码，jhyy_v1 翻译时没修。`as i64` cast 在 codegen 路径上没生效（虽然 sema 通过了）。

**workaround:**
- 暂时没有完全等价的 workaround（不能直接 emit i64 literal in codegen）
- **方法 1**：把 i64 返回函数改成返回 `*u8` 或 `i32`，调用方再做 cast（接口破坏大）
- **方法 2**：i64 常量函数（如 `FNV_OFFSET`、`FNV_PRIME`）改写成**两行 let + extern 调用链**（不实用）
- **方法 3**：在 jhyy_v1 codegen 端修 NODE_INT_LIT emit 的 type 推断（**根治，需 post v1.0.0**）

**影响范围:** util.jhyy 中所有 `fn XXX() -> i64 { return literal as i64; }`：
- `FNV_OFFSET() -> i64 { return 0xcbf29ce484222325 as i64; }`
- `FNV_PRIME() -> i64 { return 0x100000001b3 as i64; }`
- 以及 hash_string / strlen / sprintf_lld 等所有返回 i64 的内部函数

**W-007 局限性:** 仅触发字面整数常量。变量、函数调用返回 i64 不触发（caller 用 `l` 类型正确 emit）。所以 `let n: i64 = strlen(s);` 不受影响，`return n;` 也不受影响。

**失效条件:** jhyy_v1 codegen 在 NODE_INT_LIT 的 emit 路径上加 type propagation（看 return type / cast 类型决定 copy 的 class）→ W-007 可移除。

**superseder:** v0.8 commit 7 `0453cef` (cg_convert_arg src=W → dst=L extsw 分支补全) — 已 ship,镜像到 jhyy_v1 `compiler/src0/codegen.jhyy:657-661`

### W-007 RESOLVED — transitively closed by v0.8 commit 7 extsw 分支 (2026-08-12)

**Sprint v1.1.2 verification (5x5 PASS)**:

| Variant | Source | Expected | 5x5 PASS |
|---------|--------|----------|----------|
| V1 | `fn small_const() -> i64 { return 5 as i64; }` | EXIT=5 | ✅ 5/5 |
| V2 | `let x = 5 as i64; return x;` | EXIT=5 | ✅ 5/5 |
| V3 | `return (4 + 1) as i64;` | EXIT=5 | ✅ 5/5 |
| V4 | `return 0 as i64;` | EXIT=0 | ✅ 5/5 |

**canonical jhyy_v1 emit** (sha `ba94df93`, vs prior buggy `%t0 =w copy 5; ret %t0`):
```qbe
export function l $small_const() {
@start0
    %t1 =w copy 5
    %t2 =l extsw %t1     ← cg_convert_arg `src=W → dst=L` 分支补全生效
    ret %t2
}
```

**真因** (per v0.8 commit 7 + jhyy_v1 镜像 `codegen.jhyy:657-661`):
- NODE_INT_LIT 默认 emit 类是 `w` (QBE literal 不能 `l` class 直接 emit)
- 旧版 cg_convert_arg 缺 `src=W → dst=L` 分支 → emit `w copy; ret` → QBE fail
- v0.8 commit 7 加 `src=QBE_W && dst=QBE_L → emit extsw` 分支,jhyy_v1 翻译时已镜像 (codegen.jhyy:657-661 "W-007 fix (v0.8 bug 11 analog)" 注释)

**Out of scope (NOT W-007, separate shared bug)**:
- **大整数 literal (超出 INT32_MAX, 如 `0xcbf29ce484222325`)** → C-side AND jhyy_v1 都 emit `%t1 =w copy 9223372036854775807` (INT64_MAX 截断),后 `extsw`. 这是 NODE_INT_LIT parse 层 bug (lex 阶段把 hex literal 存为 i32 后溢出转 i64) — 双编译器共享,需要单独 sprint 修,不是 W-007
- **`-1 as i64`** → runtime crash (EXIT=127), C-side AND jhyy_v1 同样行为. IL 正确(`w copy 1; sub 0,1; extsw`),但运行时负数比较/QBE extsw 路径有 bug — 不是 W-007 触发面 (跟 W-007 literal-as-i64 emit type propagation 无关)

**W-007 失效条件** (per workarounds.md line 765): jhyy_v1 codegen NODE_INT_LIT emit path 加 type propagation → 失效条件已满足,标 RESOLVED.

**引用:**
- 复现 `_test_small.jhyy` / `_test_small4.jhyy` / `_test_small6.jhyy` / `_test_small8.jhyy` (4 BAD variants 全 PASS)
- v0 同源码 emit 正确 IL（`%t0 =l copy ...`），jhyy_v1 emit `w copy + extsw`，现在 byte-equal to v0
- 与 W-006 触发面不同（无 1-char var 介入），是独立 bug — W-006 也 RESOLVED (Sprint 4.21-4.25 W-005 #2 family transitive close)

---

## W-008: jhyy_v1 cg_find_field_offset 双层 deref 漏（i64 struct field emit `=w loadw` + 全 struct field 走 fallback）

**ID:** W-008
**状态:** RESOLVED（v0.8 commit 11，2d4c319 — codegen.jhyy 三处 deref 漏 + workarounds.md 文档同步；下游 cslel/ceql 错转为 W-009 候选）
**日期:** 2026-08-04
**触发面:** jhyy 源码里**任意 `(*ptr).field_X` 或 `s.field` 或 `field.assign()` 路径**走 cg_find_field_offset / cg_copy_struct — 包括 codegen 阶段任何按 struct 字段 emit 的代码：
- `(*a).def_size`（i64）— arena.jhyy 赋值/读取 def_size
- `(*a).blocks` 等所有 *u8 字段 — 写到 i64 变量也算
- v0.7 7B `arr_of_structs[i].field`（path 1/2 都用 cg_find_field_offset）
- 任何 user-defined struct 的 field 访问

**症状:** QBE 拒绝：`invalid type for store ... (w != l)` 或 `storel %t_w, %t_slot` type mismatch；jhyy_v1 编译 exit 1。**或者**编译过但运行时 segfault 0xC0000005（heap corruption）。
**根因（双层 deref 漏）：** jhyy_v1 `cg_find_field_offset`（codegen.jhyy）有**两个独立的 deref 漏**：

### Bug 8a：sym-p 解 deref（更深层 root cause）
```jhyy
// codegen.jhyy:489-491（fix 前）
let fdesc = ptr_add_u8((*st).fields_v1, j * FIELD_DESC_SIZE()) as *u8;
let fname_str_ptr = fdesc as **u8;
let fname_str = *fname_str_ptr;        // ← BUG：读到的是 *Sym，不是 const char *
if strcmp(fname_str, field_name) == 0 { ... }
```

sema.jhyy:1507 写入的是 `*fd_name_slot = fsym`（fsym 是 *Sym），所以 FieldDesc.name 字段存的是 *Sym 指针。strcmp(Sym*, "val") 把 Sym 内存字节当 C 字符串，但 Sym 字节是 8 字节堆指针（如 `0x0000_0020_4D_EF_12_34`，会有高位 0x00）→ strcmp 几乎永远不匹配 → cg_find_field_offset 直接走 fallback exit path 返回 0 → caller 拿到的 out_buf 是 uninitialized arena garbage → offset_v1=0、field_type_raw=garbage。

C 端 codegen.c:854 等价语句是 `strcmp(st->struct_type.fields[j].name->name, d->fields[i].name)` — **多一层 deref 读 `Sym->name`**，所以 v0 工作。

### Bug 8b：type slot deref（首次发现层）
```jhyy
// codegen.jhyy:493（fix 前）
let out_type_v1 = ptr_add_u8(out_buf_v1, 8 as i64) as **u8;
*out_type_v1 = ptr_add_u8(fdesc, 8 as i64) as *u8;   // ← BUG：写的是 fdesc+8 地址本身，不是 fdesc+8 处的值
```
对比 offset_v1 那行 `*out_off_v1 = *foff` 是正确 deref → 漏 symmetry。CGContext out_buf layout（i64 offset_v1 @ 0 + *Type @ 8）是 commit 4 抽 helper 定的，type slot 写漏 deref → caller 拿到 `field_type_raw` 实际是 fdesc+8 这个**指向 type 字段存储地址的指针**（不是 Type 指针本身）。

### Bug 8c：cg_copy_struct 同模式 (codegen.jhyy:448)
```jhyy
let ftype = ptr_add_u8(fdesc_ptr, 8 as i64) as *Type;   // ← BUG：ftype 实际指向 FieldDesc 内字节，不是 Type
```
后续 `(*ftype).kind` 读 4 字节 at fdesc_ptr+8 → Type* 指针的低 32 位 → 不等于任何 KIND_* → fall through → return QBE_W → 所有 struct field 标量化且 QBE_W。

### 联动错误链路
若只修 8b（type slot deref），但 8a（sym cmp）未修 → strcmp 仍然永不匹配 → fallback path → field_type_raw 仍然 garbage → 症状不变。所以**两个 bug 必须同时修**。最初 fix cycle 发现 8b 修完症状依旧，**进一步挖到 8a** 才是真 root cause。

### 下游链 (任意 fix 漏掉时)
1. `qbe_type_of(field_type_raw)` 读到非 valid Type* → garbage kind → 落到 `return QBE_W()` (ir.jhyy:127)
2. caller 拿到 `result_v1.qbe_type = QBE_W`
3. emit `%tN =w loadw %tA` 但目标是 i64/pointer 字段（需要 QBE_L → `=l loadl`）
4. QBE typecheck 拒绝 → jhyy_v1 退出 1

### 修复（commit 11 三处同步）
```jhyy
// codegen.jhyy:489-491（Bug 8a — sym deref）
let sym_p_v1 = *(fdesc as **Sym);                          // deref Sym*
let fname_str = *(ptr_add_u8(sym_p_v1 as *u8, 0 as i64) as **u8);  // Sym.name @ offset 0
if strcmp(fname_str, field_name) == 0 { ... }

// codegen.jhyy:448（Bug 8c — ftype deref in cg_copy_struct）
let ftype_slot_v1 = ptr_add_u8(fdesc_ptr, 8 as i64) as **Type;
let ftype = *ftype_slot_v1;

// codegen.jhyy:502（Bug 8b — type slot deref in cg_find_field_offset）
*out_type_v1 = *(ptr_add_u8(fdesc, 8 as i64) as **u8);    // 再 deref 一层
```

### 验证（v0.8 commit 11）
```jhyy
type Box = struct { val: i64, next: *u8 }
fn use_struct() -> i64 {
    let local_box: Box = Box { val: 5 as i64 };
    return local_box.val;
}
```
**jhyy_v1 emit (fix 后):**
```
%t4 =l loadl %t0
ret %t4
```
✅ QBE 通过，arena.jhyy 完整跑通 `step 1/2/3 ... rc=42` 输出（参见 arena_test.exe.exe 测试结果）。

**影响范围（仅在 jhyy_v1 codegen 翻译产物，v0 C 编译不受影响）:**
- src0/arena.jhyy: `arena_new_block/arena_alloc_aligned/arena_reset/arena_free` 全 struct field 访问
- src0/parser.jhyy: Lexer state struct, Parser state struct
- src0/sema.jhyy: SymTable entries, TypeArena fields
- src0/codegen.jhyy: LocalEntry.sym / IRVal.kind (但 cg_add_local / cg_find_local 不走 cg_find_field_offset，所以可能 OK)
- 任何 user-defined struct 的 field access

**Stage 0 closure 关系:** W-008 是 W-007 fix 完成后**下一道关卡** — W-007 extsw 让 `ARENA_DEFAULT_SIZE` 类型常函数 emit 正确；W-008 让所有 struct field load 类型正确。**两个 fix 缺一不可**才能 Stage 0 closure。

**失效条件:** 不再次变动 codegen.jhyy 的 cg_find_field_offset / cg_copy_struct 字段查找代码。或者把 sema 改成存 string 而非 *Sym（避开 deref 链）。

**superseder:** v0.8 commit 11（W-007 同 commit 应用）

**引用:**
- 复现：scratch src0/__w8_test.jhyy（最小 struct field 读写）
- arena.jhyy 验证：build/bin 多次重新 compile + run（rc=42 + 完整打印 step 1-3）
- 与 W-007：两层 root cause 都必须修。W-007 修 const/copy extsw，W-008 修 cg_find_field_offset deref
- 与 W-005：无直接关联，但 arena.jhyy 用 W-005 (*i64 指针累加) 才能让 W-008 fix 后的 struct field 访问真在 codegen 路径上跑通（W-005 解决 *p = ... 的赋值 segfault，W-008 解决 `*p = (*a).def_size` 的 i64 load 类型错）

---

## W-009: jhyy_v1 cg_convert_arg src_t==0 早 bail，导致 literal `0` 在 ceql/csltl 中以 w 操作数出现

**ID:** W-009
**状态:** RESOLVED（v0.8 commit 12, 5820793 — codegen.jhyy cg_convert_arg src_t==0 兜底 + dst.kind=KIND_POINTER 不再 bail + NODE_CAST 移除 src_t==0 早 bail；arena.jhyy Stage 0 closure 解锁）
**日期:** 2026-08-04
**触发面:** jhyy 源码里**任意 `l_field == 0` / `l_field != 0` / `i64_var cmp 0` / `pointer cmp 0` 路径**走 cg_expr → 比较操作 → cg_convert_arg：
- `if (*a).def_size > 0` — arena.jhyy: arena_new_block 的 fallback 路径
- `if malloc(...) == 0` — arena.jhyy: arena_new_block malloc 返回值 null check
- `if arena_alloc(...) == 0` — arena.jhyy: arena_strdup malloc null check
- 任何 user code 写的 `p == 0` 或 `p != 0`（p 是指针 / i64 / u64）

**症状:** QBE 拒绝：`invalid type for second operand %tX in ceql` 或 `invalid type for first operand %tX in csltl`。jhyy_v1 编译 exit 1。
**根因（cg_convert_arg 早 bail + literal 默认 w）：**

### Bug 9a：literal `0` 在 NODE_INT_v1 处 emit `=w copy 0`
```jhyy
// codegen.jhyy:671-676（fix 前）
if kind == NODE_INT_v1() {
    let d = node_int_data(n);
    let qt = qbe_type_of((*n).type_ptr_v1);   // type_ptr_v1=0 → qbe_type_of(NULL)=QBE_W
    let v = ir_new_tmp(ir, qt);               // qbe_type=W
    ir_emit_copy(ir, v, (*d).value);          // emit "    %tN =w copy 0"
    return v;
}
```

jhyy 的字面量 0 在 parser 阶段没填 type_ptr_v1（sema 也没补全 — 缺特性），所以 `qbe_type_of(NULL) = QBE_W`。NODE_INT_v1 直接 emit `w copy 0`。

### Bug 9b：cg_convert_arg src_t==0 时早 bail
```jhyy
// codegen.jhyy:548-550（fix 前）
fn cg_convert_arg(cg_raw_v1: *u8, arg: IRVal, src_t: *u8, dst_t: *u8) -> IRVal {
    let cg = cg_raw_v1 as *CGContext;
    let ir = (*cg).ir as *IRBuf;
    if src_t == (0 as *u8) {
        return arg;          // ← BUG：literal 走到这里不 coerce
    }
    if dst_t == (0 as *u8) {
        return arg;
    }
    ...
}
```

### 联动错误链路
比较操作 emit 块（codegen.jhyy:1291-1294）：
```jhyy
let mut right_coerced = right;
if d_op >= TOKEN_EQEQ() && d_op <= TOKEN_GTEQ() {
    if left.qbe_type != right.qbe_type {                    // L (l) != W (w) → 进 coerce
        right_coerced = cg_convert_arg(cg_raw_v1, right,
            (*right_node).type_ptr_v1,                       // 0
            (*left_node).type_ptr_v1);                      // l type
    }
}
```
`cg_convert_arg` 接 src_t=0 早 bail → `right_coerced = right`（仍是 `w copy 0`）→ emit `ceql %t_l, %t_w` → QBE "invalid type for second operand"。

### 修复（commit 12：cg_convert_arg + NODE_CAST 两处放宽条件）

实际实现包含 **三处放宽**，比原始 root cause 分析更深一层：

**Fix 1：cg_convert_arg src_t==0 时用 arg.qbe_type 兜底**
```jhyy
// codegen.jhyy:548-553（fix 后）
fn cg_convert_arg(cg_raw_v1: *u8, arg: IRVal, src_t: *u8, dst_t: *u8) -> IRVal {
    let cg = cg_raw_v1 as *CGContext;
    let ir = (*cg).ir as *IRBuf;
    if dst_t == (0 as *u8) {
        return arg;
    }
    // W-009 fix: src_t==NULL 时（literal 没 type info），用 arg.qbe_type 当 src_qt
    let src_qt_v1: i32 = if src_t == (0 as *u8) { arg.qbe_type } else { qbe_type_of(src_t) };
    ...
}
```

**Fix 2：cg_convert_arg dst.kind=KIND_POINTER 不再 bail（v0 行为对齐）**
```jhyy
// codegen.jhyy:555-570（fix 后）
if src_t != (0 as *u8) {
    let src = src_t as *Type;
    if (*src).kind != KIND_PRIMITIVE() {     // src 仍要求 primitive
        return arg;
    }
    // dst 不再硬要求 KIND_PRIMITIVE（pointer 是 qbe_type L，走 W→L extsw）
    if src_qt_v1 == dst_qt_v1 && (*src).kind == KIND_PRIMITIVE() {
        let dst2 = dst_t as *Type;
        if (*dst2).kind == KIND_PRIMITIVE() {
            if (*src).prim == (*dst2).prim { return arg; }
        }
    }
}
```
原版 hard-bail `dst.kind != KIND_PRIMITIVE` 让 `0 as *u8` 永远 no-op（C 端 codegen.c:721 也不 bail，所以 W-009 fix 让 jhyy_v1 行为对齐 v0）。

**Fix 3：NODE_CAST 不再因 src_t==0 早 bail**
```jhyy
// codegen.jhyy:1844-1855（fix 后）
if kind == NODE_CAST() {
    let ncd = node_cast_data(n);
    let inner_node = (*ncd).expr as *Node;
    let inner_v_v1 = cg_expr_v1(cg_raw_v1, inner_node);
    let src_t = (*inner_node).type_ptr_v1;
    let dst_t = (*n).type_ptr_v1;
    if dst_t == (0 as *u8) {                  // ← 移除了 src_t==0 的早 bail
        return inner_v_v1;
    }
    return cg_convert_arg(cg_raw_v1, inner_v_v1, src_t, dst_t);
}
```
原版 `if src_t == 0 || dst_t == 0 { return inner_v_v1; }` 在 literal 走到这里就 return，让 cast 失效。

### 验证（v0.8 commit 12）

**jhyy_v1 compile arena.jhyy emit (修复前)：**
```
%t28 =l call $malloc(l %t27)
%t29 =w copy 0                            ← 字面量 0 emit w
%t30 =w ceql %t28, %t29                   ← INVALID：ceql 要两边 l
```
QBE：`invalid type for second operand %t29 in ceql`

**jhyy_v1 compile arena.jhyy emit (修复后)：**
```
%t28 =l call $malloc(l %t27)
%t29 =w copy 0
%t30 =l extsw %t29                        ← 自动补 extsw
%t31 =w ceql %t28, %t30                   ← VALID：两边 l
```
实测：commit 12 后 arena.jhyy emit 中 `extsw` 出现 **29 次**（修复前是 0），所有 `ceql/cslel/csltl/csgtl` 操作数两边都是 l。QBE typecheck 通过。

**v0 regress：47/47 pass, 0 fail, 3 skip（**无 regression**）**

**v1 regress：12 OK（持平 — W-009 修了 arena.jhyy 这种**库文件**编译路径，regress 测试集是 47 个 main 程序不直接覆盖；但 Stage 0 closure 达成）**

### 影响范围（仅在 jhyy_v1 codegen 翻译产物，v0 C 编译不受影响）
- src0/arena.jhyy: `arena_new_block`/`arena_alloc_aligned`/`arena_strdup` 多个 `ptr == 0` null check
- src0/parser.jhyy: 任意 `let tok = ...; if tok == 0 { ... }` 类型 check（如果 parser 走 literal 0）
- src0/sema.jhyy: symbol table null check
- 任何 user code 里的 pointer / i64 / u64 字段 null-or-zero 比较

**Stage 0 closure 关系:** W-009 是 W-008 修完后**下一道关卡** — W-008 让 struct field load 类型正确（i64 field 出 `=l loadl`）；W-009 让比较 l 字段时 right operand (literal 0) 也走 `extsw` 升级到 l。**两个 fix 缺一不可**才能让 jhyy_v1 编 arena.jhyy 跑通 QBE 严格 typecheck。

**失效条件:** 不再次变动 cg_convert_arg 的 src_t==0 早 bail 逻辑。或者把 sema 改成给 NODE_INT 字面量填 type_ptr_v1（让 qbe_type_of 走 TYPE 路径而非 NULL fallback）。

**superseder:** v0.8 commit 12

**引用:**
- arena.jhyy: arena_new_block line ~50 `if malloc(8) == 0` + arena_strdup line ~190 `if arena_alloc(...) == 0`
- arena.il 反例：`_w008_arena.il:55` (`ceql %t28, %t29` mixed) 与 `:211` (`ceql %t112, %t113` mixed)
- 与 W-008：无直接关联。W-008 修 struct field load type，W-009 修 literal compare operand type
- 与 W-007：W-007 修 return literal 类型（extsw in cg_convert_arg w→l case），W-009 修 cg_convert_arg 入口 bail 条件让 extsw 路径真正走到

---

## Cross-ref: B-let2 (Stage 1 byte-equal codegen gap)

**ID:** B-let2
**状态:** RESOLVED (v0.9 wip commit 2.5)
**日期:** 2026-08-05
**触发面:** jhyy_v1 `cg_convert_arg` 函数 (`compiler/src0/codegen.jhyy:544-634`)
**症状:** Stage 1 byte-equal 验收 (`stage1-expanded.sh`) 跑 `arith.jhyy` 时 FAIL —— `let down_val: i32 = total_val as i32;` (total_val: i64 → down_val: i32) emit `=w copy %l_value`,QBE 报 "type mismatch"。

**根因:**
- v0 codegen.c:780-783 `cg_convert_arg` 显式 emit `copy` for `src=L, dst=W` integer width narrowing。
- jhyy_v1 codegen.jhyy:544-634 `cg_convert_arg` 历史上漏这条分支(只覆盖 `src=w, dst=l` via extsw + `src=l, dst=d/s` via sltof/ultof)。

**修复** (v0.9 wip commit 2.5):
- 在 `cg_convert_arg` 加 `src=L, dst=W` 分支:
```jhyy
} else if src_qt_v1 == QBE_L() {
    if dst_qt_v1 == QBE_W() {
        conv = "copy" as *u8;
    }
}
```
- 对齐 v0 codegen.c:780-783,QBE `copy` from l to w 隐式截断(lower 32 bits 取到 w,QBE ABI 行为)

**验证:** `bash compiler/tests/stage1-expanded.sh` arith.jhyy PASS,byte-equal baseline 1/7 → **2/7** (hello + arith)

**不是 workaround 而是真修:** B-let2 不需要 workarounds(非 user-facing 触发),直接修 codegen.jhyy 一处即解。

**与 W-007/W-009 关系:**
- W-007 修 `src=w, dst=l` (extsw) —— 跟 B-let2 镜像对称(B-let2 修 `src=l, dst=w` copy)
- W-009 修 src_t==0 兜底 —— 让 B-let2 / W-007 的转换路径走到(literal 0 → extsw → copy 链路)
- 三个 fix 缺一不可,jhyy_v1 cg_convert_arg 才算完整

**引用:**
- [`docs/internal/codegen-pitfalls.md` § 2.2](codegen-pitfalls.md) —— B-let2 详解(diff + 修复代码 + 验证)
- `compiler/src0/codegen.jhyy:613-619` —— 修复代码
- `compiler/tests/examples/arith.jhyy` —— 触发用例
- `compiler/tests/stage1-expanded.sh` —— 验收脚本
- v0 codegen.c:780-783 —— 对齐的 C 端 emit 路径

---

## Cross-ref: W-008 ↔ W-009 ↔ W-007 ↔ W-005 codegen 转化路径联动

**日期**: 2026-08-05 (v0.9 wip commit 2.14)
**目的**: 把 4 个 codegen 翻译层 workaround 集中梳理, 标清联动关系 + 真修路径, 避免未来 sprint 单独修一个时漏考虑其他 3 个。

### 4 workaround 摘要

| ID | 触发面 | 根因 | 真修状态 | commit |
|----|-------|------|---------|--------|
| **W-005** | `let mut x; x = expr;` (NODE_ASSIGN + NODE_IDENT) segfault | C/jhyy CGContext struct 布局不匹配 (9 字段 offset) | ✅ RESOLVED | v0.9 wip commit 2.11 (CGContext 对齐) + 2.13 (16 处 revert 回 `let mut`) |
| **W-007** | `fn() -> i64 { return X as i64; }` emit `w copy` | cg_convert_arg 缺 `src=W, dst=L` extsw 分支 | 🟡 ACTIVE (partial — 单 return value 路径修了, struct field + global var 路径仍漏) | v0.8 commit 7 (`0453cef`) partial |
| **W-008** | cg_find_field_offset 双层 deref 漏 → i64 struct field emit `=w loadw` | cg_find_field_offset helper 把 `*u8` 指针当 `**u8` 多解一层 | ✅ RESOLVED | v0.8 commit 11 |
| **W-009** | cg_convert_arg src_t==0 早 bail → literal 0 在 ceql/csltl 中以 w 操作数出现 | cg_convert_arg 入口 `if src_t == 0 { return arg; }` 跳过 extsw 路径 | ✅ RESOLVED | v0.8 commit 12 |

### 联动关系

**W-008 ↔ W-009 (链式依赖)**:
- W-008 修 struct field load 类型 (`=l loadl` for i64 field)
- W-009 修 literal 0 比较时升级到 l (`extsw` before compare)
- **缺一不可**: W-008 让 left operand 是 l; W-009 让 right operand (literal 0) 也是 l。任一不修, `ceql/csltl/csgtl` 操作数类型 mismatch → QBE 拒绝

**W-005 ↔ W-007 (NODE_ASSIGN 路径分支)**:
- W-005 修 `let mut x; x = expr;` 路径 (NODE_ASSIGN + NODE_IDENT + cg_add_local/cg_find_local/cg_emit_store)
- W-007 修 `return X as i64;` 路径 (NODE_RETURN + NODE_CAST → cg_convert_arg)
- **不同路径**: W-005 是 store 路径; W-007 是 return 路径。但 cg_emit_store 内部走 cg_convert_arg (类型转换) — W-005 真修后, W-007 partial 路径可能漏的 struct field + global var 路径**才**会被 W-005 真修路径触发

**W-007 ↔ W-008 ↔ W-009 (cg_convert_arg 三向联动)**:
- W-007 修 cg_convert_arg `src=W, dst=L` extsw 分支
- W-009 修 cg_convert_arg 入口 bail 条件, 让 extsw 路径走到
- W-008 修 cg_find_field_offset, 让 cg_emit_store 拿到的 struct field load 是正确类型 (`=l loadl` for i64 field), 喂给 cg_convert_arg 时 src_qt 是 L 而非 W (W-008 修了上游, W-007 才需 `src=L, dst=W` B-let2 copy 分支对应 `src=W, dst=L` extsw 分支)

**W-005 真修 (CGContext 布局对齐) → W-007/W-008/W-009 影响**:
- CGContext 布局对齐后, cg_add_local/cg_find_local/cg_emit_store 路径全 clean
- 之前 W-008/W-009 修的部分, 现在在 `let mut x; x = Y;` 路径上**才真正测得到**(之前因 W-005 segfault 在前面挡了)
- v0.9 wip commit 2.11 后跑 regress, 未观察到 W-007/W-008/W-009 在 src0/ 内的新触发面

### 真修路径共识 (per cross-ref)

| workaround | 真修 | commit | 备注 |
|-----------|------|--------|------|
| W-005 | ✅ 已真修 | v0.9 wip commit 2.11 + 2.13 | CGContext C/jhyy 9 字段对齐 |
| W-007 | 🟡 partial → 等 W-005 后审计 + B-let2 路径补全 | 待 v1.0 sprint 3+ | 单 return value 路径修了; struct field / global var 路径需审计 |
| W-008 | ✅ 已真修 | v0.8 commit 11 | cg_find_field_offset 单层 deref |
| W-009 | ✅ 已真修 | v0.8 commit 12 | cg_convert_arg 入口 bail 条件删 |

### 验证 (commit 2.14, 2026-08-05)

- regress 持平 50/53 (commit 2.13 baseline)
- stage1 byte-equal 持平 6/7 (commit 2.12 baseline)
- 4 workaround 联动关系: W-005 真修后, W-007 partial 路径在 src0/ 内的触发面待审计 (Task #60 修后 + W-004 verification 后再做)

### 引用

- v0.8 commit 7 (`0453cef`) — W-007 partial (单 return value path)
- v0.8 commit 9 (`d570c72`) — W-001 byte-by-byte 真修 (W-002/W-004 根因消除)
- v0.8 commit 10 (`d8535a9`) — W-005 workaround extension (util.jhyy + arena.jhyy)
- v0.8 commit 11 — W-008 真修 (cg_find_field_offset)
- v0.8 commit 12 — W-009 真修 (cg_convert_arg 入口)
- v0.9 wip commit 2.5 — B-let2 真修 (W-007 镜像)
- v0.9 wip commit 2.11 — W-005 真修 phase 2 (CGContext 对齐)
- v0.9 wip commit 2.13 — W-005 加固 16 处 revert 回 let mut
- v0.9 wip commit 2.14 (本 commit) — cross-ref 联动关系文档化

---

## W-010: jhyy-端 MAX_LOCALS=512 vs C-端 1024 → cg_add_local 静默溢出致 `%t0` 污染

**ID:** W-010
**状态:** RESOLVED (v0.9 wip commit 2.79)
**日期:** 2026-08-10（Sprint 4.21–4.23 triage 实证）
**触发面:** jhyy_v2 编译 `compiler/src0/main.jhyy`（cg_expr 内本地变量数 > 512）
**症状:**
- jhyy_v2.exe.il 末尾 ~470 行窗口内出现 ~39 处 `%t0` 引用
- 形式：`ceqw %t0, X`、`csltl %t0, X`、`=l call $ir__ir_new_tmp(l %t77637,  %t0)`（双空格是 qbe_type sigil 为空的物证）
- QBE reject：`invalid type for first operand %t0 in copy`（行 165792 类）
- 不在 regress 单文件测试中出现（单文件 cg_expr 本地变量数远低于 512）

**根因:**
1. `compiler/src0/codegen.jhyy:68` 定义 `fn MAX_LOCALS() -> i32 { return 512 as i32; }`
2. `compiler/src/codegen.c:17` 定义 `#define MAX_LOCALS 1024`
3. 两侧差 2×，**jhyy 端容量更小**
4. `cg_add_local` 在 `idx >= MAX_LOCALS` 时静默 return 0（codegen.jhyy:173），不报错
5. `cg_find_local` miss 返回零 sentinel `(IRVal){0}`（kind=IRVAL_TEMP, id=0）
6. `ir_init` next_tmp 从 1 开始，**temp 0 永不分配** → emit `%t0`（缺 qbe_type sigil）

**workaround:** 无（不报错 + 影响 jhyy_v2 自举构建）

**失效条件:**
- 单文件 regress 测试（cg_expr 本地变量数 < 512）不触发
- jhyy_v1 编 main.jhyy（C-side MAX_LOCALS=1024 够用）不触发
- **jhyy_v2 编 main.jhyy 才触发**（自举第二步 = 关键路径）

**superseder:** v0.9 wip commit 2.79 — jhyy-side `MAX_LOCALS` 512 → 1024，跟 C-side 对齐

**解决实证 (2026-08-10):**
- `compiler/build/bin/jhyy_v2.exe.il` 的 `grep "%t0,"` 计数从 39+ → **0**
- `grep " %t0," compiler/build/bin/jhyy_v2.exe.il` → **0 命中**
- regress.py 50/53 PASS（持平 baseline）
- regress_v1.py 50/53 PASS（持平 baseline）
- jhyy_v2 编 hello.jhyy 的 QBE 错（`invalid type for jump argument %t748`）跟本 bug **无关**——是 inline_imports 引发的函数重复 emit 问题（g_as 报 ~1500+ 处 `symbol X already defined`），属于 Stage 2 inline_imports 设计缺陷，跟 W-010 正交

**Sprint 历史:**
- Sprint 4.21 Phase B+C+D+G（IRVal struct pass-by-value → 指针）— **未触及根因**，4 workaround 站点仍 fail
- Sprint 4.22（cg_match_pattern `let mut + if/else` 改条件表达式）— **假说错误**，2 种写法 emit 同样的 `%t0` 污染（行号漂 2-12）
- Sprint 4.23 Explore agent（2026-08-10）— 找到 `%t0` 集中出现 + MAX_LOCALS 双源不一致 → 本 fix

**引用:**
- [`project_sprint4_22_cgexpr_signature_mismatch.md`](../../../../Users/liuzhen/.claude/projects/C--Users-liuzhen-Desktop-coding-JiHuiYiYou/memory/project_sprint4_22_cgexpr_signature_mismatch.md) — Sprint 4.22 假说错误 postmortem
- Sprint 4.23 plan: `C:\Users\liuzhen\.claude\plans\jaunty-orbiting-naur.md`

---

## W-011: inline_imports emit module 全量重复（Stage 2 设计缺陷）— RESOLVED

**ID:** W-011
**状态:** ✅ RESOLVED (Sprint 4.24 commit 2.80)
**日期:** 2026-08-10
**触发面:** `jhyy_v2` 编 `compiler/src0/main.jhyy` (12 个 module + transitive imports)，所有 module 函数在 IL 里 emit 多份（arena 89 份/util 47 份）
**症状:** QBE 通过，但 `as` 报 1500+ 处 `symbol 'X' is already defined`；jhyy_v2 self-build 在 link 阶段 fail
**根因:** `compiler/src0/main.jhyy` 的 `resolve_one_import_v1` 实现了 `completed[]` / `in_progress[]` 数组（64×512 byte slots）+ helper (`completed_match` / `in_progress_match`)，但**全文件零次写**这两个数组。C-side `compiler/src/main.c:159-229` 正确实现 push/pop 机制（push to in_progress BEFORE recursion, pop + push to completed AFTER recursion）。jhyy-side 缺这两段关键代码

**fix (Sprint 4.24 commit 2.80):** 在 `resolve_one_import_v1` 加两个 block：
1. **Step 1 (line ~280)**: parse 校验通过后、decl 迭代前 push mod_path 到 `in_progress[]`（cycle detection）
2. **Step 2 (line ~339)**: decl 迭代完后、free 前 pop mod_path from `in_progress[]` + push to `completed[]`（dedup）

字节复制用 `str_concat_at`（不能存指针，因为 mod_path 是父 frame 的临时 npath）；slot layout 用 `*u8` 指针 + 单独 `malloc(512)` heap buffer（与 C-side 64×512 byte 数组兼容）

**结果 (验证):**
- IL `^export function` 计数：**4715 → 567**（接近 plan 预期 ~560）
- `arena__*` 副本数：**89 → 1**
- `util__*` 副本数：**47 → 1**
- `regress.py` (C-side)：**50/53 PASS**（持平 baseline）
- `regress_v1.py` (jhyy_v1)：**50/53 PASS**（持平 baseline）
- `jhyy_v1.exe.exe` (sha `402b03e1...`) 编 `main.jhyy` 成功
- `jhyy_v2.exe.il` (sha `9b67e53...`) export 唯一计数达成

**Out of scope (Sprint 4.24):** jhyy_v2 self-build (jhyy_v2 → jhyy_v2.exe.exe) 仍 fail — QBE 在 line 10157 报 `newline expected, got ?? instead`，是独立 sret emit bug（`cg_expr` 的 `NODE_RETURN` 在 has_sret 时 emit `ret %tN` 而非 `ret`），跟 W-011 正交。修复需要 Sprint 4.25+ 走 cg_copy_struct inline rewrite 或 cmd_compile 自动调用 fix_il.py

**引用:**
- Sprint 4.24 plan: `C:\Users\liuzhen\.claude\plans\jaunty-orbiting-naur.md`
- v0.9 wip commit 2.80 (Sprint 4.24 dedup 真修)
- C-side reference: `compiler/src/main.c:159-229` (correct push/pop logic)

---

## W-012: codegen emit-layer sentinel pollution — cg_copy_struct emit `copy %t0` when src/dst undef

**ID:** W-012
**状态:** ✅ RESOLVED (v0.9 wip commit 2.81, Sprint 4.25)
**日期:** 2026-08-10
**触发面:** 函数体是 `if c { return A } else { return B }` 这种**两条 return 分支**的结构，其中：
- B = struct return 函数（has_sret = 1, 返回 aggregate type）
- A, B 都是非平凡表达式

**症状:**
- `compiler/build/bin/*.il` 出现 `copy %t0` / `\0 %t0`（QBE 错：`invalid type for first operand %t0 in copy` / `in csltl` 等）
- 单文件 regress 不触发（结构简单，return 直接 emit 不经过 cg_copy_struct）
- jhyy_v2 编 src0/main.jhyy 触发（大函数 + 多个 struct-return 模式）

**根因 (Plan agent 验证, 2026-08-10):**
1. `ir_init` (`compiler/src/ir.c:38`) 设 `next_tmp = 1`，所以 `%t0` 永不被合法分配 → IRVal `kind=IRVAL_TEMP, id=0` 是 sentinel
2. **Cg_func epilogue** (`compiler/src/codegen.c:1700-1710`) 用 `cg_body_returns()` 做**纯语法检查**（只看最后一条 stmt）
3. 但函数体是 `if c { return A } else { return B }` 时：`cg_body_returns() == false`（最后 stmt 不是 return）→ epilogue 跑 → `body_val` 来自 NODE_BLOCK 的 `IRVal last = {0}`（codegen.c:698，return 之前值未覆写）
4. epilogue → `cg_copy_struct(cg, ret_type, sret_addr, body_val)` → 逐字段 emit `=l copy %t0`
5. NODE_RETURN sret 分支 (`codegen.c:1474`) 同理：expr 是 unreachable 时仍 emit `cg_copy_struct` → 同 `copy %t0` 污染

**真修 (Sprint 4.25 commit 2.81):** 在 3 个 emit 点 + 1 个 helper 加 `irval_is_undef(v)` 守卫：
1. `compiler/src/ir.h:33-42`: 加 `static inline int irval_is_undef(IRVal v)` helper（`v.kind == IRVAL_TEMP && v.id == 0`）
2. `compiler/src/codegen.c:142-148`: `cg_copy_struct` 开头 early-return if src or dst undef
3. `compiler/src/codegen.c:1481-1486`: NODE_RETURN sret 分支，加 `if (!irval_is_undef(src)) cg_copy_struct(...)` 守卫
4. `compiler/src/codegen.c:1718-1728`: cg_func epilogue sret 分支，加 `if (!irval_is_undef(body_val)) cg_copy_struct(...)` 守卫
5. `compiler/src0/ir.jhyy:107-118`: 镜像 `fn irval_is_undef(v: IRVal) -> i32`
6. `compiler/src0/codegen.jhyy:412-422`: 镜像 cg_copy_struct 守卫
7. `compiler/src0/codegen.jhyy:931-960`: 镜像 NODE_RETURN sret 分支（has_sret 时走完整 copy，**非** bare `ret`）
8. `compiler/src0/codegen.jhyy:2780-2792`: 镜像 cg_func epilogue sret 守卫

**关键不变量（byte-equal 保护）:**
- 守卫只在 `kind=IRVAL_TEMP && id=0`（即 sentinel）时短路
- `next_tmp = 1` 让 sentinel 永不被 `ir_new_tmp` 分配
- 任何走 sentinel 路径的代码本来就会 emit 非法 IL（QBE 必 fail 或 runtime 错）
- 所以守卫**不改正确程序输出** — 7/7 byte-equal 由构造保持

**结果 (验证 2026-08-10):**
- 最小复现 `_repro_t0.jhyy`: 函数体 `if c { return A } else { return B }` + struct return
  - BEFORE fix: `qbe:_repro_t0.il.il:50: invalid type for first operand %t0 in copy`
  - AFTER fix: compiled successfully, **EXIT=30 ✓** (10+20)
- regress.py (C-side): 50/53 PASS（持平 baseline）
- regress_v1.py (jhyy_v1.exe.exe sha `43c66665...`): 50/53 PASS（持平 baseline）
- Stage 1 byte-equal: 7/7 PASS（持平 baseline, 由构造保证）

**Sprint 历史:**
- Sprint 4.13 IRVal layout alignment (commit 2.45) — 修 IRVal union layout（**DEFINITION 层**），但 `next_tmp=1` + `body_returns()` 纯语法检查仍漏 emit 层 sentinel
- Sprint 4.21 Phase C (`cg_copy_struct` 改 `const IRVal*`) — 试图用引用改签名，**没修 emit 层 sentinel 短路**
- Sprint 4.25 (commit 2.81) — Plan agent 找出真根因 (cg_body_returns 纯语法检查 + cg_copy_struct 不 short-circuit), 用 8 处 sentinel 守卫真修

**失效条件:**
- 任何 `cg_expr` emit IL 时假定 `kind=IRVAL_TEMP, id=0` 是合法值（违反 `next_tmp=1` 不变量）
- 新的 emit 点加入时忘记加 `irval_is_undef` 守卫

**superseder:** 长期看，`cg_body_returns()` 应该改成可达性分析（data-flow），但这是独立重构；本 fix 在 emit 层挡下游，已足够。

**不 tag v1.0.0:** Sprint 4.26 Stage 2 N=3 byte-equal 重测后再决定（已知仍可能有别的 Stage 2 差异）

**引用:**
- Sprint 4.25 plan: `C:\Users\liuzhen\.claude\plans\jaunty-orbiting-naur.md`
- v0.9 wip commit 2.81 (Sprint 4.25 sentinel 真修)

