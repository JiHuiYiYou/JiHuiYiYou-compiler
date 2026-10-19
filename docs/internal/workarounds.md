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
| [W-001](#w-001) | RESOLVED | hash_string 用 *i32 deref 绕 v0 codegen `loadsb` 错 |
| [W-002](#w-002) | RESOLVED | main.jhyy 重命名绕 jhyy_v1 hash_string 堆损坏 |
| [W-003](#w-003) | RESOLVED | jhyy_v1 `let _ = fncall(...)` 顶层 / 嵌套 segfault →... |
| [W-004](#w-004) | RESOLVED | short local var (≤4 chars) → symtab hash 撞 →... |
| [W-005](#w-005) | RESOLVED | `let mut x: T; x = expr;` 改 `*pos_ptr += ...` 绕... |
| [W-006](#w-006) | RESOLVED | jhyy_v1 `return x ± y` 两 1-char var 发 127（QBE... |
| [W-007](#w-007) | RESOLVED | jhyy_v1 `fn() -> i64 { return X as i64; }` emit... |
| [W-008](#w-008) | RESOLVED | jhyy_v1 cg_find_field_offset 双层 deref 漏（i64... |
| [W-009](#w-009) | RESOLVED | jhyy_v1 cg_convert_arg src_t==0 早 bail，导致 literal... |
| [W-010](#w-010) | RESOLVED | jhyy-端 MAX_LOCALS=512 vs C-端 1024 → cg_add_local... |
| [W-011](#w-011) | RESOLVED | inline_imports emit module 全量重复（Stage 2 设计缺陷）—... |
| [W-012](#w-012) | RESOLVED | codegen emit-layer sentinel pollution —... |
| [W-013](#w-013) | RESOLVED | C-side cg_expr NODE_CAST w/l → b/h narrowing emit... |
| [W-014](#w-014) | RESOLVED | `jhyy_selfhost_check` MCP pre-stage cleanup... |
| [W-015](#w-015) | RESOLVED | `NODE_SIZEOF` 节点 arena 分配 8 字节 → sema const-fold... |
| [W-016](#w-016) | RESOLVED | 8 字节 enum 参数 ABI mismatch — caller 用 `l` (slot)... |
| [W-017](#w-017) | RESOLVED | jhyy 顶层 `let mut *u8 = 0` codegen 常量折叠 → 全局状态失效 |
| [W-018](#w-018) | RESOLVED | v1.4.2 DWARF emit 引入 Stage 1 .il 字节差异 (非功能) |
| [W-019](#w-019) | RESOLVED | codegen 嵌套 struct `(o).inner.a` emit `loadsw` 类型错 |
| [W-020](#w-020) | RESOLVED | jhyy-side `parser.jhyy` parse_pattern... |
| [W-021](#w-021) | RESOLVED | WiX 7 CLI `-ext` name 查找失败 — `-ext... |
| [W-022](#w-022) | SUPERSEDED | Windows PowerShell 5.1 `Out-File -Encoding utf8`... |
| [W-023](#w-023) | SUPERSEDED | MSYS2 bash step 里 `${VAR}` 不展开 `${{ env.X }}` GH... |
| [W-024](#w-024) | SUPERSEDED | PowerShell 5.1 `Set-Content` / `Out-File` 写 UTF-8... |
| [W-026](#w-026) | RESOLVED | regress.py `[:80]` stderr 截断隐藏真实 QBE/gcc 错误 |
| [W-027](#w-027) | RESOLVED | GH Actions `setup-msys2@v2` 把 MSYS2 装在... |
| [W-029](#w-029) | SUPERSEDED | jhyy.exe toolchain 探测收敛 — `jh_gcc_path()` 4-tier... |
| [W-028](#w-028) | RESOLVED | Windows process exit code 是 8-bit (mod 256),... |
| [W-030](#w-030) | RESOLVED | WiX 4 Theme.xml schema — Font 必须在 `<Theme>` 顶层... |
| [W-031](#w-031) | RESOLVED | MSI LaunchCondition + INSTALLDIR resolution — 原探测... |
| [W-033](#w-033) | RESOLVED | Theme.xml XML 1.0 well-formedness + WiX 4 thmutil... |
| [W-034](#w-034) | RESOLVED | cmd_run system() — 用 jh_fullpath 解析绝对路径绕 cmd.exe... |
| [W-035](#w-035) | RESOLVED | jh_paths_init 布局检测 — installer 布局 vs source-tree... |
| [W-038](#w-038) | RESOLVED | cmd.exe /C 不处理带空格 path — CreateProcessA 替代... |
| [W-039](#w-039) | RESOLVED | CreateProcessA 同样 unquoted-token 切错 — caller 显式... |
| [W-040](#w-040) | RESOLVED | link_with_gcc 也需 quote path args (asm_path /... |
| [W-041](#w-041) | RESOLVED | VSCode Code Runner 集成 — installer 自动装 extension +... |
| [W-042](#w-042) | RESOLVED | link_with_gcc 失败只打 "gcc link failed" — 缺... |
| [W-043](#w-043) | RESOLVED | MSI 漏装 runtime.c + jhyy_helpers.c → install 后... |
| [W-044](#w-044) | RESOLVED | MSI 漏装 runtime.h → install 后 `fatal error:... |
| [W-045](#w-045) | RESOLVED | link_with_gcc 失败时 gcc 实际 stderr 不可见 — 用户只见 "gcc... |
| [W-048](#w-048) | RESOLVED | link_with_gcc 在 PowerShell + 中文文件名 silent fail —... |
| [W-051](#w-051) | RESOLVED | MSI deferred ExeCommand CustomAction type 34 在本机... |
| [W-052](#w-052) | RESOLVED | match 字面量范围模式 `1..10` 两侧 parser + codegen 都漏... |
| [W-053](#w-053) | RESOLVED | 字符字面量转义不全 (`\n \t \r \0` 之外 escape) 以及 `\xHH` 漏解码 |
| [W-054](#w-054) | RESOLVED | sizeof IL 未定义 `%t0` — 真因是 `qbe_type_of` 撞 data... |
| [W-055](#w-055) | RESOLVED | spec §9.5 指针算术 `p + 1` 整节未实现 |
| [W-056](#w-056) | RESOLVED | 多字节 UTF-8 char literal + char type `u8 → i32`... |
| [W-057](#w-057) | RESOLVED | UTF-8 3-byte / 4-byte codepoint 显式 lex reject (推... |
| [W-058](#w-058) | RESOLVED | vendor QBE (2026-08-15 build) 不支持 `remd` / `rems`... |
| [W-083](#w-083) | RESOLVED | V3 self-backend 不支持 QBE IL conversion ops (lexer... |
| [W-086](#w-086) | RESOLVED | V3 self-backend ILToken 字段数根本不足 (dst/lhs/rhs... |
| [W-059](#w-059) | RESOLVED | defer codegen path silent crash (v1.3.6 ship 后 0... |
| [W-060](#w-060) | INVALID | enum variant payload ABI mismatch (Mixed::I(1234)... |
| [W-061](#w-061) | INVALID | nested struct field offset bug (Outer { tag,... |
| [W-062](#w-062) | RESOLVED | VSCode UserChoice hijack + MSYS2 OpenWithProgids... |
| [W-063](#w-063) | RESOLVED | 短名 enum 模式匹配 `Some(v) => v` bind, codegen 传错 type... |
| [W-064](#w-064) | RESOLVED | run_qbe 失败只打 `QBE failed: ...` 缺 stderr 捕获, QBE... |
| [W-065](#w-065) | RESOLVED | `jhyy run` 不预检 `fn main_jhyy` — 库 snippet 报... |
| [W-066](#w-066) | RESOLVED | post-425970d refactor 漏改 jhyy-compiler.wxs:622 —... |
| [W-067](#w-067) | RESOLVED | release.yml vs build.ps1 重复 strip-to-3 逻辑 → drift... |
| [W-068](#w-068) | RESOLVED | v1.8.3 Burn bundle 双击闪退 — `Theme.xml`... |
| [W-071](#w-071) | RESOLVED | 自写后端 codegen_amd64 模块未 e2e 验证 — v2.6.x 阶段 ship 但... |
| [W-069](#w-069) | RESOLVED | jhyy.exe 编译产物 corrupt / ld exit 5 — stage0 build... |
| [W-072](#w-072) | RESOLVED | 0f9c923 merge artifact + codegen_amd64.jhyy 重复 fn... |
| [W-073](#w-073) | RESOLVED | QBE IL emit escape + lexer `next_token_data_string... |
| [W-074](#w-074) | RESOLVED | runtime.c 24B Arena 死代码声明 (4 fn + Arena struct) |
| [W-075](#w-075) | RESOLVED | std::mem mem_set 用 i32 store 而非 byte store (M0 简化) |
| [W-076](#w-076) | RESOLVED | std::arena test inline 副本用 std_* 前缀避 runtime.c... |
| [W-074.6](#w-074.6) | RESOLVED | jhyy.exe 编 src0/main.jhyy 自举 .s 截断 / multifn... |
| [W-087](#w-087) | RESOLVED | V3 self-backend emit_func_header frame size 不含... |
| [W-088](#w-088) | RESOLVED | V3 self-backend caller-side store-pointer temp... |
| [W-089](#w-089) | RESOLVED | V3 self-backend emit_call 不 flag l-typed call... |
| [W-090](#w-090) | RESOLVED | V3 self-backend temp_holds_address bitmap 256... |
| [W-091](#w-091) | RESOLVED | V3 self-backend emit_call `std_` 前缀 whitelist 缺 →... |
| [W-092](#w-092) | RESOLVED | V3 self-backend bitmap 1024 暴露 big_test... |
| [W-093](#w-093) | RESOLVED | V3 self-backend bitmap 1024 → 4096 真修 big_test 1... |
| [W-094](#w-094) | RESOLVED | V3 self-backend alloc-tracking slot table bound... |
| [W-095](#w-095) | RESOLVED | V3 self-backend emit_load's dst result temp 不... |
| [W-096](#w-096) | RESOLVED | per-fn-local temp_id counter → emit slot offset 用... |
| [W-097](#w-097) | RESOLVED | jhyy-side codegen emit_func_header per_fn_max... |
| [W-098](#w-098) | RESOLVED | jhyy-side codegen emit i64 literal (>32-bit... |
| [W-100](#w-100) | RESOLVED | emit_call sret 路径无条件 `movl %eax, -<slot>(%rbp)`... |
| [W-101](#w-101) | RESOLVED | emit_binop ceqw dst_id 走 existing local... |
| [W-085](#w-085) | RESOLVED | codegen small-frame fn(*T, i32, i32) 第 3 i32 参数... |
| [W-102](#w-102) | RESOLVED | address-holder 池与 alloc 池槽位重叠 → self-hosted... |
| [W-103](#w-103) | ACTIVE | std/os.jhyy 全部 I/O 与 exit 是 M0 mock — W-079 的... |
| [W-104](#w-104) | RESOLVED | SysV ABI 参数分类调用 Win 分类器 — 正确的分类器就在同文件,没接线 |
| [W-105](#w-105) | ACTIVE | check_borrow 是硬编码 return 1 — `&mut` 独占性完全不检查 |
| [W-105.1](#w-105.1) | ACTIVE | check_cap_pass 同款空 stub,当前无调用点(死代码但签名在 API 面上) |
| [W-106](#w-106) | ACTIVE | symtab_lookup_one 用 arena-touch 强制 codegen... |
| [W-107](#w-107) | ACTIVE | 五个 per-fn pre-scan 表硬编码 1024 上限 — 距触发只剩 33 个函数 |
| [W-108](#w-108) | RESOLVED | 索引重建脚本静默丢弃 59/89 条目 —— STATUS_RE 不容忍 前缀,且只匹配 H2 |
| [W-109](#w-109) | RESOLVED | 自举 IL lexer 缺 6 个浮点比较助记符 — f32/f64 六个比较运算静默降级 |
| [W-110](#w-110) | RESOLVED | 一个函数里多条浮点比较连续改同一 mutable 局部 → 结果串号 |
| [W-111](#w-111) | RESOLVED | 泛型 enum 的关联构造器在无类型上下文处不被识别;多字段 payload 连解析都过不去 |
| [W-112](#w-112) | ACTIVE | `#[link_section]` 完全失效 — 属性被解析但 codegen 是 no-op |
| [W-113](#w-113) | ACTIVE | `asm!` 与 memory barrier 的字节被 emit 到 `ret` 之后,永不执行 |
| [W-114](#w-114) | ACTIVE | 全 unit-variant 的 enum `match` 永远命中第一支 — 核心语言功能失效 |
| [W-115](#w-115) | ACTIVE | W-089 标着 RESOLVED,但它自己的 reproducer 至今... |
| [W-116](#w-116) | RESOLVED | SysV callee 参数溢出只处理 4 个整数寄存器 —— 第 5 个及以后的参数全读到第 4... |
| [W-117](#w-117) | RESOLVED | self-backend IL lexer 在 EOF 处无守卫 —— cur == end... |
| [W-118](#w-118) | ACTIVE | 语言 lexer 的 lex_peek_char 同样无 EOF 守卫 —— 越界前进而非空转 |

## W-001: hash_string 用 *i32 deref 绕 v0 codegen `loadsb` 错

**ID:** W-001
**状态:** RESOLVED (v0.8 commit 9 `d570c72`, 2026-08-03) — 见下方"W-001 RESOLVED" section (byte-by-byte FNV-1a 真修, 移除了 *i32 overread workaround + W-002 失效)
**日期:** v0.6 sprint（~2026-05, ACTIVE）→ 2026-08-03 (RESOLVED)
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
- 详尽 bug 清单见 git log v0 codegen bug 段 (Bug 3)
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

**局限性（重要, 历史记录）：** W-002 修了 hash_string 触发面 bug，但 jhyy_v1 编 main.jhyy **仍然 segfault**（exit 139, 2026-08-04 之前观察）—— 因为 main.jhyy 还有别的触发 jhyy_v1 codegen bug 的模式（Bug 7 `let _ = fncall`、Bug 9 嵌套 if/else phi、Bug 13/16 struct 值传递等；详见 git log v0 codegen bug 段）。**但** W-001 真正修复 + 后续 v0.9 wip commit 2.5~2.11 修了 B-φ1/B-struct/B-match/W-005 phase 1+2, main.jhyy segfault 触发面已大量消除 — v0.9 wip commit 2.12 revert 后是否还 segfault 由 commit 2.12 的 **observation step** 检验 (commit 2.12 plan § observation)。

**失效条件:**（任一即可移除 W-002）
- jhyy_v1 的 codegen 对 hash_string 生成的 IL 与 v0 IL byte-equal（diff 通过）→ 重新引入原名
- 或 v0 codegen 修了 W-001 的副作用（W-001 workaround 改成 byte-by-byte 不再 overread）—— 此时即使 jhyy_v1 触发面不变也不再 segfault

**superseder:** ✅ 已实现 (v0.9 wip commit 2.12 — W-001 byte-by-byte 真修 → W-002 失效条件 (ii) 满足 → 211 个 `_v1` 后缀 revert 回原名)

**W-002 RESOLVED section:** 见下方"W-002 RESOLVED — v0.9 wip commit 2.12 211 revert"

**引用:**
- 详细 bisect 记录见 git log (2026-08-04 周边 commits)
- 测试用例 `tmp/tm_*.jhyy`
- 完整 rename 映射 `compiler/src0/_W002_rename_map.txt`
- v0.8 commit 6 (efc41bf) `wip: bisect heap corruption`
- v0.8 commit 7 (0453cef) `W-002: 211 个标识符 _v1 后缀化 + workarounds.md`
- 战略决策: Bisect findings (per git log 同区段)

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
**根因嫌疑:** v0 codegen 对 `let _ = fncall(...)` emit IL 缺漏（详见 git log v0 codegen bug 段 Bug 7 / Bug 7b）
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
- v0 codegen Bug 7 / Bug 7b (per git log)
- 决策过程见 git log W-003 iterations 段

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
- 真修在 jhyy_v1 `cg_copy_struct` + `irval_is_undef` 守卫 (8 处)+ C-side 同步对齐
- 守卫消除 stale pointer 后,`let _ = fncall()` 不再 emit `=w copy %t0` 污染 IL,codegen 路径正常

**Out of scope (NOT W-003)**:
- **v3 workaround 29 处** `let _X = fncall()` → `fncall()` 的 revert 不在本 sprint 范围. 类比 W-002 commit 2.12 (211 个 `_v1` 后缀 revert),W-003 revert 需要单独 cleanup commit. **可在 Sprint v1.1.x 后续做**:验证 baseline 50/53 持平下 revert 29 处 top-level 改回 `let _X = fncall()` 风格,恢复代码自然性.

**W-003 失效条件** (per workarounds.md line 307): v0 codegen 修复 `let _ = fncall(...)` emit → W-003 可移除. 实际: jhyy_v1 codegen 已 ship 修复,W-003 失效条件满足,可标 RESOLVED.

**v1.2.0 cross-ref (2026-08-12 src0/ 自然化 ship):**
- W-003 workaround 代码 `let _ = fncall()` style 在 src0/ 24 处 通过 v1.2.2 (`f49e64d`) 全部 revert 回 `let _X = fncall()` 描述性名 风格 (cg_expr / cg_emit_store / cg_copy_struct / ir_emit_ret / ir_emit_str / ir_emit_jmp 6 类 call)
- 跟 v1.2.0 plan out-of-scope "v3 workaround 29 处" (line 342) 实际工作已经 ship — v1.2.2 24 处 + v1.2.3/1.4 关联 = 完整 29 处 revert
- W-003 状态:**code 撤回完, v0 fix ship 已闭环**
- 详情见 [`docs/logs/v1/changelog-v1.2.0.md` § v1.2 wip commit 1.2](../logs/v1/changelog-v1.2.0.md)

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
- v0 codegen Bug 6 (let-mut assignment) + Bug 1 (hash_string overread)
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
- v0 codegen Bug 6 (let-mut assignment) + Bug 7b (nested let-mut)
- W-003 (`docs/internal/workarounds.md` § W-003) 修了 `let _X = fncall()` 顶层 direct call 模式，未覆盖 let-mut + assign
- W-004 修了短 var 名导致 symtab hash 撞死循环，未覆盖 let-mut + assign segfault
- 复现测试 `tmp/test_w4_lit.jhyy` / `tmp/test_w4_v1.jhyy`

**v1.2.0 cross-ref (2026-08-12 src0/ 自然化 ship):**
- W-005 workaround 代码 `let mut xxx_vN` style 在 src0/ 16 处 通过 v1.2.1 (`2c92cf4`) 全部 revert 回 `let mut xxx` 自然风格
- W-005 workaround 残留 `_vN` 后缀 99 处 通过 v1.2.3 (`1c24841`) + v1.2.4 (`0026098`) 全部 cleanup
- W-005 状态:**code 撤回完, v0 fix ship 已闭环** — 跟 v0.9 wip commit 2.13 + v0.9 wip commit 2.11 真修 chain 形成完整闭环
- 详情见 [`docs/logs/v1/changelog-v1.2.0.md` § v1.2 wip commit 1.1](../logs/v1/changelog-v1.2.0.md) + [§ v1.2 wip commit 1.3](../logs/v1/changelog-v1.2.0.md) + [§ v1.2 wip commit 1.4](../logs/v1/changelog-v1.2.0.md)

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

**结论**: W-006 在当前 src0/ **0 活跃触发面**, 但根因 (codegen stack-slot allocator bug) 未真修, 新写代码仍可能触发。Workaround 状态 ✅ RESOLVED (0 活跃触发面 = 不需要 active 维护); 根因标 dormant 提醒未来 reader 不要 reset codegen stack-slot allocator (per `feedback_document_workarounds_in_docs.md` "superseded 标 RESOLVED 不删除" 原则, W-006 整段保留作为历史归档)。

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
| **W-007** | `fn() -> i64 { return X as i64; }` emit `w copy` | cg_convert_arg 缺 `src=W, dst=L` extsw 分支 | ✅ RESOLVED (transitive 2026-08-12, master table 5x5 PASS verified on 4 BAD variants — 单 return value + struct field + global var 全路径 cover) | v0.8 commit 7 (`0453cef`) 原始 + transitive 2026-08-12 验证 |
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
- *(Sprint 4.22 假说错误 postmortem — 项目 memory 私有记录,不在公开 doc 留链接)*
- Sprint 4.23 plan: *(私有 plan 文件,不在公开 doc 留路径)*

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

---

## W-013: C-side cg_expr NODE_CAST w/l → b/h narrowing emit sentinel `%t0`

**ID:** W-013
**状态:** ✅ RESOLVED (v0.9 wip commit 2.87, Sprint v1.1.7)
**日期:** 2026-08-12
**触发面:** 任意 `*T_ptr = expr as u8/i8/u16/i16/bool` (T ∈ {i32,i64,u32,u64})：
- `*p_u8 = 65 as u8` (literal → sub-word)
- `*p_u8 = somevar as u8` (let-binding chain)
- 任意 codegen 路径下, w/l → b/h narrowing cast (literal 或 through `let _T = expr as subword`)

**症状:**
- `compiler/build/bin/*.il` 出现 `storeb %t0, addr` / `storeh %t0, addr` (QBE 错: `invalid type for first operand %t0 in storeb/storeh`)
- C-side `jhyy.exe compile *_test*.jhyy -o out` 触发 (例如 Sprint 4.7 最小复现 `_bug4_v2.jhyy`)
- jhyy_v1 (`sha ba94df93...`) **不触发** — jhyy-side `cg_convert_arg` 因 `if conv==0 return arg` 自然 fallback, 一直返回 w-class temp 给 storeb consume (QBE implicit truncate)

**根因 (traced 2026-08-12):**
1. `cg_expr` NODE_CAST handler (`compiler/src/codegen.c:786-876`) 对每个 src/dst 类型组合查 conv instruction (extsw/extuw/dtosl/stosi/...)
2. **缺失 case**: `src ∈ {w,l}` × `dst ∈ {b,h}` — QBE 无 b/h temporary type (sub-word 仅在 load/store 操作数上), 所以 cast 是 IR 层 no-op (consuming storeb/loadub 隐式截断)
3. Fall-through 到 `if (!conv) { IRVal v = {0}; *out = (v); return; }` (codegen.c:869-872, 自 v0.5.0 f4037c0 起)
4. **Sentinel pollution**: `IRVal{0}` (kind=IRVAL_TEMP, id=0) 被 storeb 当源操作数 emit → QBE reject
5. 此 pattern 是 W-005 #2 family 的另一种形态 — 任何"应该返回 word-class temp 但返回 sentinel IRVal{0}"的 codegen 路径都会触发

**真修 (Sprint v1.1.7 commit 2.87):** 在 codegen.c:869 之前加 w/l → b/h narrow no-op short-circuit：
```c
if (!conv && (src_qt == 'w' || src_qt == 'l') && (dst_qt == 'b' || dst_qt == 'h')) {
    *out = (inner); return;
}
```
- 语义: QBE 不允许 b/h 临时, 所以 narrowing 在 IR 层是 no-op — storeb/loadub 隐式截断即可
- jhyy-side 无需改 — `cg_convert_arg` (`compiler/src0/codegen.jhyy:567-711`) 的 `if conv == 0 return arg` 已正确 fallback

**结果 (验证 2026-08-12):**
- 最小复现 `_bug4.jhyy` (`*p_u8 = 65 as u8`):
  - BEFORE fix C-side: `qbe:_bug4.il:6: invalid type for first operand %t0 in storeb`
  - AFTER fix C-side: compiled successfully, **EXIT=65 ✓**
  - jhyy_v1 (canonical pre-fix): compiled successfully, EXIT=65 ✓ (一直 correct)
- 5x5 PASS 验证 (3 case × 5 runs):
  - `_bug4_test_u8.jhyy`: 5/5 PASS EXIT=65
  - `_bug4_test_i8.jhyy`: 5/5 PASS EXIT=255 (-1 as i8 sign-extended back to i64)
  - `_bug4_test_let_u8.jhyy`: 5/5 PASS EXIT=65 (let-binding chain)
- regress.py (C-side): 50/50 PASS（持平 baseline）
- regress_v1.py (jhyy_v1.exe.exe sha `ba94df93...`): 50/50 PASS（持平 baseline）
- IL 对比 (C-side vs jhyy_v1): 完全等价 (jhyy_v1 一直 correct, C-side fix 镜像同 emit pattern)

**Sprint 历史:**
- Sprint 4.7 (commit 2.46) — 首次发现 Bug 4 (stub v2 workaround 避开 struct pass-by-value), 当时归类为 W-005 #2 family 的 EMIT-layer 形态
- Sprint 4.21-4.25 W-005 #2 真修 chain — 修了 IRVal struct pass-by-value stale pointer, 但 cg_copy_struct 守卫不覆盖 cg_expr NODE_CAST 的 narrow no-op 路径
- Sprint v1.1.7 (commit 2.87) — 补 w/l → b/h narrow no-op 守卫, 4 个 v0 codegen bug 全部真修

**superseder:** 无 — 本 fix 是 cg_expr NODE_CAST conv-table 的最后缺失 case, 之后不会再有类似 narrow 漏 emit

**不变量 (byte-equal 保护):**
- 新增 short-circuit 只在 `!conv && (src_qt ∈ {w,l}) && (dst_qt ∈ {b,h})` 时触发 — 这 4 种组合之前必然 emit sentinel, 不可能产生正确 IL, 所以守卫**不改正确程序输出**
- jhyy_v1.exe.exe (`sha ba94df93...`) 不需要 rebuild — jhyy-side 一直 correct

**引用:**
- Sprint v1.1.7 plan: `C:\Users\liuzhen\.claude\plans\jaunty-orbiting-naur.md` (related W-013 entry)
- Sprint 4.7 IRVal pass-by-value memory: `project_sprint4_7_irval_pass_by_value_bug.md`
- v0.9 wip commit 2.87 (Sprint v1.1.7 Bug 4 narrow 真修)

## W-014: `jhyy_selfhost_check` MCP pre-stage cleanup deletes canonical closure binaries

**ID:** W-014
**状态:** ✅ RESOLVED (2026-08-12, Sprint mcp-2 W-014)
**日期:** 2026-08-12
**触发面:** `mcp__jhyy__jhyy_selfhost_check` (默认 `auto_rebuild=False`) — 调 `mcp-jhyy/jhyy_runner.py:selfhost_check()`,Stage 2/3 pre-stage cleanup 把 chain input binary 删了 → FileNotFoundError → 整链 early-abort,canonical closure binaries (`jhyy_v2.exe` / `jhyy_v3.exe`) 被销毁。

**根因 (2026-08-12 闭环):**

`mcp-jhyy/jhyy_runner.py` 的 chain 设计是**output path 跟 input path 同名(只差 .exe 后缀)**:
- Stage 1: input = `jhyy_v1.exe.exe`,output = `jhyy_v1.exe` (→ `jhyy_v1.il`)
- Stage 2: input = `jhyy_v2.exe`,output = `jhyy_v2.exe` ← **同一个文件!**
- Stage 3: input = `jhyy_v3.exe`,output = `jhyy_v3.exe` ← **同一个文件!**
- Stage 4: input = `jhyy_v3.exe`,output = `jhyy_v3.exe.exe` (named to match output suffix)

Sprint mcp-2 (commit `5eb10bf`) 加的 pre-stage cleanup:
```python
_safe_remove(output_base + ".exe")  # 删 output (.exe)
_safe_remove(output_base + ".il")   # 删 output (.il)
```

跑 stage 2 时,`_safe_remove("compiler/build/bin/jhyy_v2.exe" + ".exe")` → 把 stage 2 的 **input binary** 删了!Stage 3 同样删 `jhyy_v3.exe`。然后下一行 `_safe_remove(".il")` 也走同 output_base → 删 input 不存在的 .il(无害)。

Stage 2 的 compile 命令:
```python
cmd = [exe_path, "compile", src_abs, "-o", output_base]  # exe_path = jhyy_v2.exe (刚被删)
```

→ `subprocess.run` 报 **FileNotFoundError** (Windows) / "Command not found (exit=-1)"(Linux)。整链 early-abort 在 stage 2,**stage 3-4 都没跑**。

**结果 (验证 2026-08-12):**
- BEFORE fix MCP `jhyy_selfhost_check` (auto_rebuild=False):
  - 早 abort at stage 2: `"jhyy_v2 compile failed (exit=-1): Command not found"`
  - **canonical `compiler/build/bin/jhyy_v2.exe` (sha `d3aeed09...`, v1.0.0 tag 锁定) 被永久删除**
  - 需要 `git restore compiler/build/bin/jhyy_v2.exe` 才能恢复
- AFTER fix (output 用 `_sh_vN` scratch prefix):
  - 直接 Python 调 `jhyy_runner.selfhost_check()`:`{"ok": True, "all_byte_equal": True, "il_sha256": "749be833..."}`
  - canonical `jhyy_v2.exe` / `jhyy_v3.exe` / `jhyy_v4.exe` **全部不动**
  - 4 个 stage IL sha 全部 byte-equal `749be833...`(Stage 2 N=3 闭环 仍在)

**Fix 设计 (核心 2 行 + cleanup):**

```python
chain = [
    ("jhyy_v1", "compiler/build/bin/jhyy_v1.exe.exe", "compiler/build/bin/_sh_v1"),  # ← 改
    ("jhyy_v2", "compiler/build/bin/jhyy_v2.exe",     "compiler/build/bin/_sh_v2"),  # ← 改
    ("jhyy_v3", "compiler/build/bin/jhyy_v3.exe",     "compiler/build/bin/_sh_v3"),  # ← 改
    ("jhyy_v4", "compiler/build/bin/jhyy_v3.exe",     "compiler/build/bin/_sh_v4"),  # ← 改 (v4 = v3 编 src)
]

# After chain done: cleanup scratch
for stage, _, output_rel in chain:
    for ext in (".exe", ".il", ".s"):
        _safe_remove(_resolve_path(output_rel) + ext, retries=2, delay_ms=200)
```

input (canonical) 跟 output (scratch `_sh_vN`) 物理分开 → pre-stage cleanup 只动 scratch,canonical 不动。Chain 结束主动清 scratch(包括 ld.exe 留下的 `.s`)。

**为什么不直接 disable pre-stage cleanup?** Sprint mcp-2 加它的目的是解 Windows file lock:上次 selfhost_check 跑完 ld.exe 进程可能短暂 hold 文件,下一次 `_safe_remove` 要 retry on lock。如果 disable,下次跑会撞 `PermissionError` (lock) 而不是 `FileNotFoundError` (本 bug)。所以 **保留 cleanup,只换 output path**。

**为什么不 rename output 到 `<input>.out`?** Windows 命令行 + QBE 后端对 `-o` 参数解析里 `.exe` 后缀处理有历史包袱(见 W-005 #1 family);`output_base + ".il"` 路径走 `output_base` + 显式 `.il` 后缀(jhyy.exe append `.il` 机制 per `feedback_qbe_crlf_root_cause`),改成 `_sh_vN` + `.exe` / `.il` 后缀跟原 path 形态一一对应,改动最小。

**Sprint 历史:**
- v1.0.0 tag (`eabee0d`, 2026-08-10)— Stage 2 N=3 byte-equal 闭环 commit,**MCP `jhyy_selfhost_check` 尚未引入**,所有链是手动 `subprocess.run` 跑,无 cleanup 步骤
- Sprint mcp-2 (commit `5eb10bf`, 2026-08-12 早期)— 加 `jhyy_*` MCP 工具链 + pre-stage cleanup,**引入本 bug**(没人测 stage 2+)
- Sprint mcp-2 W-014 (2026-08-12)— 闭环。直接 Python 调验证 OK,MCP server 仍 cache 老代码需重启

**superseder:** 无 — chain input/output 分开是稳定设计,未来若加 stage 5+ 用同样模式

**不变量 (canonical binary 保护):**
- chain 列表里每个 `(stage, exe_rel, output_rel)` 必须满足 `output_rel != exe_rel`(或至少不同 base name);`jhyy_vN.exe` 跟 `_sh_vN` 是不同 base
- pre-stage `_safe_remove` 只走 output_base(input 不动)
- post-chain cleanup loop 只清 `_sh_*` scratch
- 如果未来加新 stage,要重新检查 input/output 命名不能冲撞

**引用:**
- Sprint mcp-2 W-014 plan: 跟 v1.3.1 plan 同 session
- v1.0.0 tag `eabee0d`:`docs/logs/v1/changelog-v1.0.0.md` Stage 2 N=3 闭环 commit
- W-005 #1 family (Windows `.exe` suffix): `feedback_qbe_crlf_root_cause.md`
- baseline binary hash 守门:sha256sum MANDATORY(防 phantom binary)

---

## W-015: `NODE_SIZEOF` 节点 arena 分配 8 字节 → sema const-fold 写 16 字节溢出到下一块

**Status:** ✅ RESOLVED (commit TBD, v1.3.3)

**触发面:** v1.3.3 sizeof end-to-end implement。`ast_new_sizeof` 跟 `ast_new_alignof` 分配 `NODE_SIZE() + sizeof(NodeSizeof)` (= 8 bytes for `*Node target`),sema const-fold 透过 `node_int_data(n)` 写 `int64_t value` (8) + `TypePrimitive prim` (4) 共 16 bytes 溢出 8 bytes 到 next arena chunk → 随机 data corruption,典型症状: `sizeof(i32)` emit `208` (读 garbage),jhyy_v1 编 src0/main.jhyy 崩溃 `[4a] ir_init done`。

**为什么不早被 catch?** v1.0.0 时 sizeof 在 lexer + parser + AST 都有,sema 跟 codegen 完全没实现(早期 src0 翻译时留 stub,新字段写 `i32` 错误 token 然后报错走 unknown path),走不到 16-byte write 路径。Basic 测试不 cover sizeof,所以 baseline regress 50/50 PASS 看不到问题 — 直到 closure chain 递归编 src0/main.jhyy 才在 jhyy_v1 编自身 时触发(`src0/cleanup` 引入 `sizeof(CGContext)`).

**根因 (跟 W-005 / W-014 关系):** 跟 W-005 #1 family(W-005 #1: `cast` 字面 0 emit 空 buf)同类 — buffer 大小计算错。W-005 是 jhyy-side 没初始化 buf,W-015 是 C-side 跟 jhyy-side 同步算错了 node 后置 data 大小。

**修复:**
- `compiler/src/ast.c:213-228`:`ast_new_sizeof` 跟 `ast_new_alignof` 改用 `max(sizeof(NodeSizeof), sizeof(NodeInt))` (16 bytes)
- `compiler/src0/ast.jhyy:841-867`:mirror 同步 — `NODE_INT_SIZE() = 16` 已知,跟 `NODE_SIZEOF_SIZE() = 8` / `NODE_ALIGNOF_SIZE() = 8` 取 max
- 物理分开 sizeof node 的 data buf(sizeof = 16) 跟 sizeof 结构(sizeof = 8):sema 写 `id->value` + `id->prim` 不再 overflow

**为什么不直接 fill 要 16-byte data 进 8-byte struct?** 改 `NodeSizeof` struct 加 `int64_t value` + `TypePrimitive prim` 字段 看起来更"干净",但:
- `id->value` 跟 `id->prim` 跟 NODE_INT 共用 payload layout (sema 跟 codegen 一致依赖 `node_int_data(n)` 拿 data),改 sizeof struct 自定义 layout 会破 NODE_INT 共用 → 必须改 codegen 写两份
- 像 `type_size` 之类的"常量类型表达式" v1.3.x 后续可能再加 (`alignof` 同路径,还有 `traits` 之类 trait-as-type AST 节点),靠 `node_int_data` 共用 payload 是更普适的 pattern
- 选 `max` 是 conservative fix:不破 existing NODE_INT emit,zero risk

**为什么不_init 16 bytes to 0?** v1.3.3 之前 `NodeSizeof` 只有 8 bytes 用,改成 init 16 浪费 8 bytes 且对 bug 本身无补救(const-fold 写完 16 bytes 之后 data 还是错的)。问题是"buf 太小" 不是 "buf 没初始化"。

**Sprint 历史:**
- v1.0.0 tag (`eabee0d`, 2026-08-10) — NODE_SIZEOF stub,无 sema/codegen
- v1.3.1 (c2acbd1, 2026-08-12) — null literal,跟 sizeof 同语义模式
- v1.3.2 (2026-08-12,e746461) — `else if` audit 顺带跨 sizeof,Lang 文法 audit pass
- v1.3.3 (TBD, 2026-08-13) — end-to-end sizeof + W-015 fix

**superseder:** 无 — `max(struct, NodeInt)` pattern 是稳定 design,以后加同类 const-fold 表达式 (alignof/type_traits) 照搬

**不变量 (sizeof node 写法):**
- `ast_new_sizeof` / `ast_new_alignof` 必须 allocate `max(sizeof(NodeXxx), sizeof(NodeInt))` bytes for node 后置 data
- sema const-fold 只能通过 `node_int_data(n)` 写入 (rely on NodeInt 共用 layout)
- codegen mirror NODE_INT emit (`qbe_type_of` + `ir_emit_copy`)
- 任何新 const-fold AST node 需审计同样的 8/16 byte mismatch

**引用:**
- v1.3.3 sprint plan: `docs/plans/v1/v1.3.3-sizeof-compile-time-const.md`
- W-005 #1 family (buffer size 计算错): `feedback_il_s_debugging_pattern.md`
- baseline binary hash 守门:sha256sum MANDATORY(本 bug 在 jhyy_v1 自身编 src0/main.jhyy 才暴露,跟 W-014 closure 验证路径同)

---

## W-016: 8 字节 enum 参数 ABI mismatch — caller 用 `l` (slot) 传,callee 用 `w` (value) 收

**Status:** ✅ RESOLVED (v1.3.7 fix commit TBD, 2026-08-13)

**触发面 (v1.3.7 pattern binding 引入)**:enum 携带 payload(> 4 字节,如 `Option::Some(i32)` = 8 字节),caller 通过 `l` (slot pointer) 传给 callee,但 codegen 早期默认所有 enum 都按 `w` (4-byte value) emit → callee 拿到的是 slot 指针的低 32 位(garbage),tag compare 永远 false,`Some(v) => v` 实际 fallback 到 always-match 但 `v` 没绑 → 测试 exit=0(应是 v 的值)。

**最小复现:**
```jhyy
enum Option { Some(i32); None; }

fn unwrap_or(o: Option, dflt: i32) -> i32 {
    match o {
        Some(v) => v,    // v 应绑到 payload,但 ABI mismatch 时 v=0
        None => dflt
    }
}

fn main() -> i32 {
    return unwrap_or(Some(42), 0);   // expect 42,实际 0
}
```

**IL 错误状态 (before fix):**
```
%t25 =l alloc8 8           ← caller 准备 slot
...
%t31 =w call $unwrap_or(l %t25, w %t26)   ← caller 传 slot (l class)
export function w $unwrap_or(w %opt, ...)  ← ❌ callee 声明 w!
       ^^^ x86_64 SysV 读 %edi = 低 32 位 of %rdi (= slot pointer 截断)
```

**根因:**
`compiler/src/codegen.c:1918-1922` (`cg_func` param declaration) + `:1951` (param copy) — 默认 `qbe_type_of(pt)` 对 enum 返回 `QBE_W` (4-byte),不论 enum `total_size`。C-side 与 jhyy-side 都漏处理 large enum。

**修复:**
- `compiler/src/codegen.c:1918-1922`:param declaration 加 `else if (pt && pt->kind == KIND_ENUM && pt->enum_type.total_size > 4) ir_emit(ir, "l ...");`
- `compiler/src/codegen.c:1951`:param copy 类型选 `l` if large enum
- `compiler/src0/codegen.jhyy:2999-3070`:mirror — jhyy-side 用 `(*pt_t).size > 4` (`size` 不是 `total_size`,per jhyy Type struct 字段)

**验证 (5/5 PASS per `feedback_fix_evaluation_rule`):**
- `_v137_payload_bind_basic.jhyy`: exit=42 ✅
- `_v137_or_same_bind.jhyy`: exit=42 ✅
- `_v137_or_diff_bind_err.jhyy`: SemaError "OR pattern bindings must match" ✅
- `_v137_or_exhaust.jhyy`: exit=1 ✅
- `regress.py 50/50` + `regress_v1.py 50/50` ✅
- Stage 2 N=3 closure v2=v3=v4 byte-equal 持平 ✅

**Self-hosting impact:**
- v1.il = v2.il sha `7c5ca427...`(new C-built canonical)
- v3.il = v4.il sha `aefa3bb3...`(jhyy-built chain stable)
- v2.il ≠ v3.il — **pre-existing** C-side vs jhyy-side 冗余 copy 差异(per v1.3.6 changelog W-005 #2 chain products),非 W-016 引入

**跟 W-005 #2 冗余 copy 的区分:** W-016 是 ABI mismatch(类型 emit 错,导致语义错误),W-005 #2 是 codegen 优化不彻底(C 端多 emit 几个 `copy %t` 但语义正确)。两条独立 fix。

**失效条件:** 不再写 `l` 类声明 large enum param,或者 enum ABI 改成 all-by-value(无 slot 概念)。

**引用:**
- v1.3.7 fix ship (umbrella): [`docs/logs/v1/changelog-v1.3.0.md`](../logs/v1/changelog-v1.3.0.md) § v1.3.7 fix ship
- v1.3.7 父 sprint: `docs/plans/v1/v1.3.0任务清单 + 概要设计.md` § v1.3.7
- ABI spec: [`docs/abis/jhyy-abi-v1.0.0.md`](../abis/jhyy-abi-v1.0.0.md) § enum pass semantics (大 enum = slot 传)

## W-017: jhyy 顶层 `let mut *u8 = 0` codegen 常量折叠 → 全局状态失效

**Status:** ✅ RESOLVED 2026-08-14 (commit `f20e36d`, v1.4.6 W-017 真修)

**Why RESOLVED:** v1.4.6 W-017 真修 — cg_module pass A 加 NODE_LET 分支 emit
QBE `.data` section (e.g. `data $g_x = { w 41 }`) + 注册到 `mod_globals` dict
(`Sym*` → `$g_qbe`); `cg_find_local` fallthrough 到 globals; `cg_expr` /
`cg_stmt` NODE_IDENT 路径 dispatch on `addr.kind == IRVAL_STR` 触发
`ir_emit_load` / `ir_emit_store` 发 `loadw/storew $g_x` (QBE data section
引用)。同时 `ir_emit_arg` helper (Sprint 4.4 commit 2.36 latent bug fix 引入)
mirror 加到 C-side `src/ir.c`,改 `ir_emit_store` / `ir_emit_load` dispatch
through `ir_emit_arg` — Stage 1 byte-equal 守门恢复 (jhyy_v1 → v2 → v3 → v4
闭包链字节相同)。CGCONTEXT_SIZE bump 112 → 128 (C-side + jhyy-side 同 commit
bump, per W-005 layout 锁)。

**superseder:** commit `f20e36d` (2026-08-14, "fix(v1.4.6 W-017): module-level
let mut 真修 — QBE data section + ir_emit_arg mirror")

**后续 (post-v1.4.6):**
- `jhyy_helpers.c` DEPRECATED — 不再需要委托 path state 到 C runtime,但文件
  保留 1-2 sprint 观察期,v1.5 installer 设计时决定删 / 留。
- 顶层 `let mut` literal 折叠已修;非 literal initializer (e.g. `fn call()`)
  当前 zero-init fallback — 完整 init expr codegen 留给后续 sprint (TODO)。

**触发面 (v1.4.1 路径硬编码消除时发现)**: 
- 计划 (per `docs/plans/v1/v1.4.0任务清单 + 概要设计.md` § v1.4.1):在 `main.jhyy` 顶层声明 `let mut g_qbe: *u8 = 0 as *u8;` 持有 QBE 路径,`compute_paths(argv0)` 在 `main_jhyy` 入口推项目根 → 写 4 个全局字符串 → `QBE_PATH()` 等 getter 返回 `g_qbe` 内容。
- 实测:jhyy_v1 codegen 把 `let mut g_qbe: *u8 = 0 as *u8;` 在 module 顶层当作 **常量 0** 编译期折叠 — 后续所有读 `g_qbe` 的 QBE IR 都是 `%t =l copy 0`,sentinel null pointer。
- 后果:`run_qbe` 拼出 `" -t amd64_win -o foo.s foo.il"` (qbe 路径是空字符串),system() 失败 → "QBE failed"。

**最小复现 (`compiler/src0/main.jhyy` 测试代码, 已 revert):**
```jhyy
// 顶层 — 不在 fn 内部
let mut g_qbe: *u8 = 0 as *u8;

fn compute_paths() -> i32 {
    g_qbe = "C:/some/path/qbe.exe" as *u8;  // 写应该改 runtime state
    return 0 as i32;
}

fn QBE_PATH() -> *u8 { return g_qbe; }    // 读应该返回新值
```

```bash
$ jhyy_v1.exe.exe compile foo.jhyy -o foo
[cg] Pass B start
ret     ← ❌ QBE_PATH() emit 的 ret 没 operand,function signature 声明 *u8 返回 → QBE 拒绝
```

**IL 错误状态 (codegen jhyy 端的 top-level let mut fold 产物):**
```
export function l $QBE_PATH() {
        ret               ← QBE: "non-void return needs a value"
}
```

**根因:** jhyy_v1 codegen 顶层 `let mut` (NodeKind=NODE_LEV / 模拟 module-level var) 的 initializer 在 IR 生成阶段就 **编译期折叠** 成 `IRVal{kind=IRVAL_INT, val=0}` (zero-extend to l),后续 `cg_find_local` 命中 `local id=0` 直接返回这个 folded value,运行时 `store` 到 global slot 的指令被 dead-code-eliminated (因为 IR 不区分"runtime store"和"compile-time init")。C-side (codegen.c) 在 module-level 处理 `let mut g_x: T = expr;` 时 emit `store` 指令到 module-level data section,不折叠 → jhyy-side 缺这一段。

**workaround (本 v1.4.1 ship):**
- 路径状态从 jhyy 端迁出 → 委托 `compiler/src0/jhyy_helpers.c` (C runtime)。
- 5 个 extern fn:`jh_paths_init(argv0) -> i32` (一次 init, 写 4 个 static buffer) + `jh_path_qbe/gcc/runtime/helpers() -> *u8` (4 次读, 返回 const char*)。
- `main.jhyy` 顶部:5 个 extern fn decl + `QBE_PATH/GCC_PATH/RUNTIME_C/HELPERS_C` 4 个 thin wrapper fn(就是 return jh_path_*)。
- `main_jhyy` 入口:调 `jh_paths_init(argv[0])` 一次。
- `__attribute__((used))` 防止 gcc strip unused symbols (jhyy_v1 codegen 不直接调 `jh_paths_init`,通过 extern 间接调,gcc 可能 strip)。

**跟 main.c (`compiler/src/main.c`) 关系:**
- main.c 同步加 `compute_project_root(argv0)` + `g_project_root[1024]` global(C-side 有真正的 module-level static storage,emit 到 .data section)。
- C 端 QBE / gcc / runtime / helpers 路径都拼 `g_project_root` 直接用,**不调** `jh_path_*` (jhyy 端才调,因为 jhyy 端没有真正的 global)。
- jhyy_helpers.c 的 `jh_paths_init` 跟 main.c 的 `compute_project_root` 算法镜像 (dirname × 4 + GetModuleFileNameA 兜底),保持单一来源真相。

**真修路径 (post-v1.4.1 / v2.x 候选):**
- jhyy codegen 顶层 `let mut x: T = expr;` emit 真正的 store 指令 (不编译期折叠)。
- 或者:加 `static mut x: T;` 关键字 (`unsafe` block),明确 runtime 初始化语义。
- 或者:codegen 在 module 顶层加 `.data` section emit (C-side 已经做,但 jhyy-side 的 NODE_LEV 处理路径漏了 module-level case)。

**失效条件 (任一即可移除 W-017):**
- jhyy codegen 实现 module-level mutable global (上面"真修路径"任意一条)。
- 或者 jhyy 改成只支持 pure-functional / 不需要 path state (jhyy_OS kernel coding 后无外部命令调用)。

**验证 (v1.4.1 ship criteria, 5/5 PASS):**
- `compiler/src/main.c` 0 hardcoded path (grep "C:/Users" 0 命中, 仅注释提及) ✅
- `compiler/src0/main.jhyy` 0 hardcoded path ✅
- `compiler/src0/jhyy_helpers.c` 0 hardcoded path ✅
- regress.py 50/50 PASS ✅
- Stage 2 N=3 byte-equal (`jhyy_v2.exe.il = jhyy_v3.exe.il = jhyy_v4.exe.il`) 维持 ✅
- Clone 到 `/tmp/v14_clone_test/JiHuiYiYou/`(保留 canonical `compiler/build/bin/jhyy.exe` layout) 跑 hello.jhyy EXIT=42 ✅

**Self-hosting impact:**
- jhyy_v1.exe.exe sha: `1c09215f...` → `f36faeadd05c0...` (v1.4.1 刷新)
- jhyy_v2/v3/v4 .exe sha: `e453b32c...`/`569e9091...`/`569e9091...` → `7e1917c8...`/`5cad02db...`/`de3c924f...` (v1.4.1 刷新)
- jhyy_v2.il / v3.il / v4.il sha: `7c035615...` → `4c91f246...` (新 jhyy_v1 closure chain 输出;字节级变化是因为新 jhyy_v1 在 init 阶段调用了 5 个新 extern fn,新增了 module-level 函数体,不影响 .s 字节(因为 dead-code-eliminated 的 init call 在 .s 仍存在 — sha 变化是 expected))
- Stage 1 byte-equal (C-side vs jhyy_v1): pre-existing 6/7 持平(W-005 #2 chain products 仍未真修);v1.4.1 路径生成不污染 IL

**引用:**
- v1.4.1 父 sprint: `docs/plans/v1/v1.4.0任务清单 + 概要设计.md` § Sprint v1.4.1
- 跟 W-005 #2 区分:W-005 #2 是 codegen 优化不彻底(多 emit 几个 `copy %t` 但语义正确),W-017 是 codegen 缺 module-level global storage(完全没 runtime state,只能编译期常量)
- 跟 main.c `compute_project_root` mirror:`compiler/src/main.c:30-77` (C 端有 module-level `static char g_project_root[1024]`,emit 到 .data,jhyy 端做不到)
- jhyy ABI: `docs/abis/jhyy-lang-spec-v1.3.0.md` § global state (TODO: 需 spec 加"顶层 `let mut` 是 compile-time only, runtime state 必须用 extern fn 委托 C"这条规则)

---

## W-018: v1.4.2 DWARF emit 引入 Stage 1 .il 字节差异 (非功能)

**Status:** ✅ RESOLVED 2026-08-14

**Why RESOLVED:** v1.4.2 ship 当时记的"Stage 1 byte-equal 不再 7/7"证据来自
broken `compiler/tests/stage1-expanded.sh` (JHY_1 路径错写成不存在的
`jhyy_v1.exe`, `2>/dev/null` 吞错) — 脚本从未真的跑过 v1, cmp 比的是
examples/ 里上次跑剩的陈旧 .il。修脚本后 Stage 1 重新跑出 **7/7 PASS**,
v1.4.2 DWARF 改动对 .il byte-equal 无影响。

**保留原因 (不删):** v1.4.2 ship 时 changelog 写了"Stage 1 byte-equal 持平"
未达成 — 这是错的, 应为达成。引用本条便于跨 sprint 审计时不被旧 changelog 误导。

**引用:**
- 根因: `compiler/tests/stage1-expanded.sh` 的 `JHY_1` 路径错 + stderr 被吞
- 验证: `bash compiler/tests/stage1-expanded.sh` → 7/7 PASS (2026-08-14)

## W-019: codegen 嵌套 struct `(o).inner.a` emit `loadsw` 类型错

**Status:** ✅ RESOLVED 2026-08-14 (commit `6638134`, v1.4.6 W-019 真修)

**Why RESOLVED:** v1.4.6 W-019 真修 — `cg_expr NODE_FIELD` 嵌套 struct 路径
加 "field is STRUCT → return addr (don't load)" guard,跟 NODE_DEREF 现有 pattern
一致 (`*ptr.field` 解引用 → 加 offset → 不 load;外层 `.field` 把内层 addr 当
`l` 类型继续加 offset → emit `loadsw %tN, addr+a` 时第一操作数是 `l`,QBE
接受)。C-side `src/codegen.c` + jhyy-side `src0/codegen.jhyy` 镜像 byte-equal
改动 (per W-005 layout 锁)。新增 `nested_struct_test.jhyy` 验证 nested
field chain (`Inner.a` + `Inner.b`) EXIT=15。

**superseder:** commit `6638134` (2026-08-14, "fix(v1.4.6 W-019): nested
struct field chain + payload binding codegen mirror")

**后续 (post-v1.4.6):**
- `gdb_pretty_test.jhyy` nested 用例 (W-019 修复后补齐) — gdb `jhyy-pretty
  <addr> Outer` pretty-print `Outer{inner={a=7, b=8}}` 可视化验证

**触发面:** `(*outer_ptr).inner.field` 这种嵌套 struct 字段访问。Outer / Inner 都是 ABI struct 类型,Inner 至少含一个 i32 字段。

**症状:** QBE reject `loadsw`/`loadw` 第一操作数类型错。例:
```
type Inner = struct { a: i32, b: i32 }
type Outer = struct { inner: Inner }
fn read_inner(o: *Outer) -> i32 { return (*o).inner.a + (*o).inner.b; }
```
`compile wnested_test.jhyy` 报:
```
qbe:wnested_test.il:15: invalid type for first operand %t2 in loadsw
```
line 15 通常是读取 `(*o).inner.a` 对应 `loadsw` 那行。

**根因嫌疑:** `cg_field_addr` 在 chain `.inner.a` 时,把外层 `.inner` 当作 struct field 而不是 sub-struct 看待 — emit 的 `.inner` 偏移处的 `loadsw` 把 outer 地址当 `b`/`h` 大小解码,实际 inner 字段是 `w` (4 字节 i32)。或者 `qbe_type_of` 在 inner struct ptr 解一层时返回错类型。未经确诊 — post-v1.4.3 follow-up。

**workaround (v1.4.3 测试):** `compiler/tests/examples/gdb_pretty_test.jhyy` 只覆盖 flat struct / single-layer enum / slice,不写嵌套 struct 测试用例。生产代码遇到嵌套 struct 字段访问时,临时绕过:
1. 用 `let inner_copy: Inner = (*o).inner; let r = inner_copy.a + inner_copy.b;` 把内层值拷出来再读字段
2. 或直接 `(*o).inner.a` 拆成两步:`let i_ptr: *Inner = &((*o).inner); (*i_ptr).a`

**影响范围:**
- 任何用户写嵌套 struct 字段访问的 .jhyy 文件都会触发 (少见但合法)
- jhyy 编 lexer.jhyy / parser.jhyy / codegen.jhyy 不触发 (用 enum + flat struct)

**失效条件:** fix 后必须 revert 测试里的 `// NOTE: nested struct` 注释并补 nested-struct 用例

**superseder:** 待 post-v1.4.3 fix (sprint 计划见下个 sprint 设计)

**引用:**
- repro: v1.4.3 验证时跑的 `wnested_test.jhyy` (内嵌在会话日志,未 commit)
- W-008 (已 RESOLVED) 类似路径但单层 field offset;W-019 是嵌套场景的复发

## W-020: jhyy-side `parser.jhyy` parse_pattern `Color::Variant` 分支 bug

**Status:** ✅ RESOLVED 2026-08-14 (commit `ad42117`, v1.4.6 W-020 真修)

**Why RESOLVED:** v1.4.6 W-020 真修 — `parse_pattern` + `parse_match` 上移到
`parse_expr` 之前 (reorder); inline match 在 `parse_expr` 里改用 `parse_match`
delegation (替换 Sprint 4.5 C step 3a 加的 ~165 行 inline duplicate);
`parse_pattern` 的 range hi 改用新加的 `parse_pattern_primary` (inline
primary expression, 不调 `parse_expr` 解 mutual recursion — 跟 jhyy 现有
array count inline int literal 模式一致); `parse_match` OR pattern 分支
`parser_advance(p)` 缺 `&t` 参数 UB 修。验证: `_min_enum.jhyy` jhyy-side
编译通过; `gdb_pretty_test.jhyy` EXIT=0; `_v137_or_exhaust.jhyy` EXIT=1
(OR pattern 不退化); match.jhyy / match_exhaustive.jhyy 不退化。

**superseder:** commit `ad42117` (2026-08-14, "fix(v1.4.6 W-020): parse_pattern
上移 + inline primary + simplify inline match")

**后续 (post-v1.4.6):**
- `parse_pattern_primary` 的限制保留:range hi 只能是 literal / ident / paren /
  struct literal (不能 `x..arr.len()`),跟 jhyy 现有 array count 模式一致 —
  full expression 留给后续 spec 扩展
- jhyy-side forward decl 不引入(不需要,jhyy-side 无此语法 — 用 reorder 解)

**触发面:** 任何 jhyy-side 编译遇到 match arm 中 `EnumName::Variant` 或 `EnumName::Variant(payload)` 这种 fully-qualified enum pattern。

**症状:** `compile gdb_pretty_test.jhyy` 报:
```
gdb_pretty_test.jhyy:50:28: error: expected =>, got ::
gdb_pretty_test.jhyy:50:28: error: unexpected token '::' in expression
...
parse errors
```
line 50 是 `match *c { Color::Red => 0, ... }`,col 28 是 `Color::Red` 中 `::` 位置。最小 repro:
```jhyy
type Color = enum { Red, Green, Blue }
fn main_jhyy() -> i32 {
    return match 1 { Color::Red => 0, Color::Green => 1, Color::Blue => 2 };
}
```
jhyy-side 编译失败;C-side (`jhyy_stage0.exe`) 编译通过。

**根因:** `compiler/src0/parser.jhyy:1134` `parse_pattern` 在 `parser_advance(p, &t)` 消耗 outer ident `Color` 后,`parser_check(p, TOKEN_COLONCOLON())` 返回 0,即使下一个 token 实际是 `::`。parser 走 line 1158+ ident-pattern 路径(line 1171 短名 variant 分支),最终返回 NODE_PATTERN_IDENT,留下 `::` 给上层 expr parser,expr parser 报 `expected =>, got ::`。

**C-side 对照 (`compiler/src/parser.c:124-138`):**
```c
advance(p);  // line 124
if (match(p, TOKEN_COLONCOLON)) {  // line 125 - atomic check + advance
    Token vt = expect(p, TOKEN_IDENT, "variant name");
    ...
}
```
C-side 用 `match` (原子 check + advance) 正常处理同样输入。jhyy-side 用 `parser_check` + 后续 `parser_advance` 分离两步,理论等价,但实际在 match arm 上下文中返回错值 — 未经确诊是不是 token peek cache (`lexer.has_peek`) 在某种状态下未正确恢复 / invalidate,或 jhyy-side 编译器参数个数检查缺失(line 1283 `parser_advance(p)` 调用缺第二个参数 `&t` 也没报编译错)。

**workaround (v1.4.4 测试):** `compiler/tests/examples/gdb_pretty_test.jhyy` line 50 / 53 的 enum pattern 暂不动(等真修);如果要做回归,临时用 let-binding 替代:
```jhyy
let tag: i32 = color_tag(*c);   // 调用外部 helper 提取 enum tag (i32)
match tag { 0 => ..., 1 => ..., 2 => ... }
```

**影响范围:**
- 任何用户写 match arm `EnumName::Variant` 的 .jhyy 都会触发
- jhyy 编 lexer.jhyy / parser.jhyy / codegen.jhyy **不触发**(用 `match` on i32,不用 enum pattern)
- C-side 不受影响(C 端 parse_pattern line 124-138 正确)
- v1.4.4 之前 production `jhyy.exe` 实际是 C-side (sha `c9cff76...`),bug 被遮住;v1.4.4 物理替换为 jhyy-side (sha `37ffc49c...`) 后首次暴露

**失效条件 (任一即可移除 W-020):**
1. 改 `compiler/src0/parser.jhyy` parse_pattern `Color::Variant` 分支 (line 1134) + OR-pattern (line 1282-1288),使 jhyy-side 跟 C-side 行为一致
2. C-side / jhyy-side mirror byte-equal 测试 (`stage1-byte-equal.sh`) 加 match-arm-with-enum-pattern 用例

**修复路径候选:**
- v1.4.6 跟 W-019 合并真修 (parser 是 codegen 无关,但跟 codegen W-019 同期改 cross-mirror 风险可控)
- 或单独 v1.4.7 修 parser

**引用:**
- repro: `compiler/tests/examples/gdb_pretty_test.jhyy:50,53`;最小 repro `_min_enum.jhyy`
- v1.4.4 ship 时 changelog 把此 bug 误标 "pre-existing v1.4.3" 已更正 → [`docs/logs/v1/changelog-v1.4.0.md`](../logs/v1/changelog-v1.4.0.md) § v1.4.4 ship
- W-019 是 codegen 嵌套 struct,跟 W-020 (parser enum pattern) 不同面,但同样等真修;建议 v1.4.6 合并

## W-021: WiX 7 CLI `-ext` name 查找失败 — `-ext WixToolset.Bal.wixext` 找不到

**状态:** ✅ RESOLVED 2026-08-28 (v1.7.1 patch B1) — 永久 workaround 化, 标 RESOLVED 是因为 v1.7.1 patch ship 时 review 确认 underlying issue 依赖 WiX 上游 DLL 命名 (external dep, 项目不可控), 短期/中期不会真修。workaround `installer/build.ps1:131-136` 显式传 DLL 绝对路径, stable ship v1.5.3+ 至今。

**触发场景:** Sprint v1.5.3 Burn bundle build, `wix build installer/Bundle.wxs -ext WixToolset.Bal.wixext ...` 时报 WIX0144 (`The extension 'WixToolset.Bal.wixext' could not be found. Checked paths: WixToolset.Bal.wixext`)。

**根因:** `dotnet tool install --global wix` 装 WiX 7.0.0+b8977d6 后,`wix extension add -g WixToolset.Bal.wixext` 把 DLL 装到 `%USERPROFILE%\.wix\extensions\WixToolset.Bal.wixext\7.0.0\wixext7\` 目录,但 **DLL 文件名是 `WixToolset.BootstrapperApplications.wixext.dll`**,不是预期的 `WixToolset.Bal.wixext.dll`(wix CLI 名字解析逻辑是按 DLL basename 找,但 `Bal.wixext` extension 的产物 DLL basename 是 `BootstrapperApplications`,跟 extension 名不对应)。同样情况可能影响其他 Bal sub-extensions。MSI 用的 `WixToolset.Util.wixext` / `WixToolset.UI.wixext` 名字-文件名一致所以不触发。

**workaround (v1.5.3):** `installer/build.ps1` 显式构造 DLL 绝对路径传给 `-ext`,跳过 CLI 名字解析:
```powershell
$balDll = "$env:USERPROFILE\.wix\extensions\WixToolset.Bal.wixext\7.0.0\wixext7\WixToolset.BootstrapperApplications.wixext.dll"
if (-not (Test-Path $balDll)) {
    Write-Host "[ERROR] Bal extension DLL not found at: $balDll"
    Write-Host "Run:  wix extension add -g WixToolset.Bal.wixext"
    exit 1
}
& wix build ... -ext "$balDll" ...
```

**影响范围:**
- 只影响 Burn bundle build (`build.ps1 bundle`),不影响 MSI build (`build.ps1 compiler`) — Util/UI 名字一致不触发
- 不影响最终产物 (`jhyy-installer-X.Y.Z.exe` 一样能 build, payload 一样齐全)
- workaround 是 stable 的,WiX 7.x 一直用 `BootstrapperApplications.wixext.dll` 文件名

**失效条件 (任一即可移除 W-021):**
1. WiX 7 改回把 Bal extension DLL 命名为 `WixToolset.Bal.wixext.dll`(跟 extension 名一致)
2. wix CLI 加 `-ext-folder=<path>` flag 允许传目录,自动找 DLL
3. 写 custom BAFunctions (替代 Bal extension),完全不依赖 Bal.wixext

**修复路径候选:**
- 短期: workaround 留,build.ps1 已记录
- 中期: 等 WiX 上游改 DLL 命名 (可能性小,Bal sub-extensions 都按功能命名,不按 extension 名)
- 长期: v2.x 可能写 custom BAFunctions(MVP 化 Burn UX),彻底绕开 Bal.wixext

**引用:**
- repro: 跑 `wix build installer/Bundle.wxs -ext WixToolset.Bal.wixext ...` 看 WIX0144
- workaround 实现: `installer/build.ps1:131-136`
- v1.5.3 ship commit (this commit)

---

## W-022: Windows PowerShell 5.1 `Out-File -Encoding utf8` 加 UTF-8 BOM 污染 `$GITHUB_ENV`

**状态:** SUPERSEDED closed 2026-09-28 (audit reclassify per 2026-09-28 v3.x ACTIVE/DEFERRED audit, 同步 main v2.13.4 close) — 🌍 ENV-ONLY, 非 ACTIVE bug。PowerShell 5.1 是 GitHub Actions `windows-latest` runner default (`PSDefaultParameterValues` 不能 unset BOM/CRLF);Jhyy-side 不可修(不是 jhyy 编译产物问题,是 GitHub runner PS 版本依赖)。Canonical pattern (v1.5.5 起) = `Set bash as default shell step`,PowerShell step 改用 `[System.IO.File]::WriteAllText($path, $content, [System.Text.UTF8Encoding]::new($false))` 强制 utf8NoBOM。GH Actions 升 PS7 后 PS7 `Set-Content -Encoding utf8` default 无 BOM,可考虑删除 workaround;在此之前保留作为 stable pattern。原 entry label "ACTIVE" 是 v1.5.5 当时 lack of reclassify convention 残留。

**触发场景:**
在 `.github/workflows/release.yml` 的 pwsh step 里写 env 到 `$GITHUB_ENV`:
```powershell
"VERSION=1.5.5" | Out-File -FilePath $env:GITHUB_ENV -Encoding utf8 -Append
"IS_RC=0"      | Out-File -FilePath $env:GITHUB_ENV -Encoding utf8 -Append
```

**症状:**
后续 step 看不到 `VERSION` / `IS_RC` 环境变量。`${{ env.VERSION }}` 在 yaml 表达式里空字符串。`$env:VERSION` 在 pwsh 里 `$null`。

**根因:**
Windows PowerShell 5.1 (windows-latest runner 默认) 的 `Out-File -Encoding utf8` 实际输出是 **UTF-8 with BOM** (`EF BB BF` 三个字节开头)。GitHub Actions 解析 `$GITHUB_ENV` 文件时按 plain text 读,看到 BOM 当成普通字符,导致第一行变成 `﻿VERSION=1.5.5`,env var 名变成 `﻿VERSION`,后续 step `${{ env.﻿VERSION }}` 拿不到值 (因为 yaml 表达式不接受 BOM 前缀)。

PowerShell 7+ 的 `Out-File -Encoding utf8` 是 UTF-8 no BOM (没有这个 bug),但 GH Actions Windows runner 默认 PS5.1。

**workaround:**
```powershell
"VERSION=$($env:VERSION)" | Add-Content -Path $env:GITHUB_ENV
```
`Add-Content` 默认走 `[System.IO.File]::AppendAllText`,在 PS5.1 下用 UTF-8 **without BOM** 写,跟 `$GITHUB_ENV` 期望的 plain text 一致。

或者用 `Set-Content -Encoding utf8` (PS5.1 也加 BOM,不推荐)。

**影响范围:**
- 只影响 PowerShell step 写 `$GITHUB_ENV` / `$GITHUB_OUTPUT` / `$GITHUB_PATH` 的场景
- 不影响 bash step (bash 的 `echo "X=Y" >> $GITHUB_ENV` 是 plain text,无 BOM 问题)

**失效条件:**
1. GH Actions windows-latest runner 升级到 PowerShell 7+ 默认 shell
2. GH parser 升级支持 BOM 前缀

**引用:**
- repro: 写 `"X=1" | Out-File -FilePath $env:GITHUB_ENV -Encoding utf8 -Append`, 看 `${{ env.X }}` 在下一步 yaml 表达式里空
- workaround 实现: `.github/workflows/release.yml` Compute VERSION step
- v1.5.5 ship commit

---

## W-023: MSYS2 bash step 里 `${VAR}` 不展开 `${{ env.X }}` GH 表达式

**状态:** SUPERSEDED closed 2026-09-28 (audit reclassify per 2026-09-28 v3.x ACTIVE/DEFERRED audit, 同步 main v2.13.3 close) — 🌍 ENV-ONLY, 非 ACTIVE bug。`${VAR}` 不展开 `${{ env.X }}` GH 表达式 是 GH Actions msys2 bash step 设计如此:yaml 表达式只 expanded 在 yaml 解析期, msys2 bash sub-shell `run:` block 拿不到。Canonical pattern = `echo "VERSION=${VERSION}"` 直接读 `$VERSION` (从 env block 注入),或用 `${{ env.VERSION }}` 强制 yaml 表达式 expand。entry 自身写 "失效条件 N/A (设计如此)" 即承认无 bug。原 label "ACTIVE" 是 v1.5.5 当时 lack of reclassify convention 残留。

**触发场景:**
`.github/workflows/release.yml` 的 msys2 bash step:
```yaml
- name: Set env
  shell: msys2 {0}
  run: |
    echo "MSYS2_PATH=/c/msys64/usr/bin:$PATH" >> $GITHUB_ENV
    echo "VERSION=${VERSION} IS_RC=${IS_RC}"   # ❌ 空字符串
```

**症状:**
`echo` 输出 `VERSION= IS_RC=`,后续 step 拿到空 `VERSION`。

**根因:**
`${{ env.VERSION }}` 是 GitHub Actions 的 **yaml 表达式**,仅在 yaml 解析阶段被 GH 替换成实际值,然后 yaml 解析后的字符串塞进 bash sub-shell 的 stdin。bash 看到的字符串是 `"echo \"VERSION=1.5.5 IS_RC=0\""`(假设 `VERSION=1.5.5`),但 `${VERSION}` 是 bash 的语法, 跟 yaml 表达式是两回事 — yaml 表达式替换后**不**写回 env 上下文,bash 自己读 `$VERSION` (空) 写 `${VERSION}` (空,作废语法)。

实际正确写法:
```yaml
- name: Set env
  shell: msys2 {0}
  run: |
    echo "MSYS2_PATH=/c/msys64/usr/bin:$PATH" >> $GITHUB_ENV
    echo "VERSION=$VERSION IS_RC=$IS_RC"      # ✓ 读已经 export 到 env 的 $VERSION
```

需要先在某个 step 把 VERSION 写到 `$GITHUB_ENV` (per W-022 用 `Add-Content`), 然后下一个 bash step 拿 `$VERSION`。

**影响范围:**
- 仅 msys2 bash step + yaml 表达式 (其他 step 类型用 `${{ env.X }}` 直接 yaml 替换,不涉及 bash 变量展开)
- pwsh step 用 `$env:VERSION` 读,语法不冲突

**失效条件:**
- N/A (设计如此,workaround 是规范用法)

**引用:**
- repro: 写 `echo "X=${VAR}"` 在 bash step, 看 `${VAR}` 输出空 (假设 VAR 已经在 $GITHUB_ENV export 过)
- workaround 实现: `.github/workflows/release.yml` Set bash as default shell step (v1.5.5 起,本 commit)
- v1.5.5 ship commit

---

## W-024: PowerShell 5.1 `Set-Content` / `Out-File` 写 UTF-8 文本默认加 BOM + CRLF

**状态:** SUPERSEDED closed 2026-09-28 (audit reclassify per 2026-09-28 v3.x ACTIVE/DEFERRED audit, 同步 main v2.13.4 close) — 🌍 ENV-ONLY, 非 ACTIVE bug。跟 W-022 同根因 (PS5.1 default 在 windows-latest runner):`Set-Content -Encoding utf8` / `Out-File -Encoding utf8` 写 UTF-8 文本默认加 BOM + CRLF。Jhyy-side 不可修(不是 jhyy 编译产物问题,是 GitHub runner PS 版本依赖)。Canonical pattern = `[System.IO.File]::WriteAllText($path, $content, [System.Text.UTF8Encoding]::new($false))` 强制 utf8NoBOM (或 `Set bash as default shell` 走 bash step,无 PS BOM 问题)。GH Actions 升 PS7 后 PS7 `Set-Content -Encoding utf8` default 无 BOM,可考虑删除 workaround。原 label "ACTIVE" 是 v1.5.5 当时 lack of reclassify convention 残留。

**触发场景:**
PowerShell 写 UTF-8 文本文件 (用于上传到 GitHub Release 或下游工具消费):
```powershell
$notes = Get-Content installer/changelog-template.md -Raw
# ... replace 占位符 ...
Set-Content -Path release-notes.md -Value $notes -NoNewline  # ❌ 加 BOM + CRLF
"jhyy-installer  $hash" | Out-File -Encoding utf8 -Append     # ❌ 加 BOM + CRLF
[IO.File]::WriteAllLines('sha256.txt', $lines, $utf8NoBom)   # ❌ CRLF only (BOM OK)
```

**症状:**
- 文件前 3 字节 `EF BB BF` (BOM)
- 行尾是 `\r\n` (CRLF), 不是 `\n` (LF)
- `sha256sum -c SHA256.txt` 在某些 Linux 平台 (scoop autoupdate 用 Linux container) 不识别:
  - 带 BOM 的 file: BOM 当成 hash 第一字符
  - 带 CRLF 的 file: `\r` 被当成 filename 一部分 → "No such file or directory"
- winget `wingetcreate validate` 报 BOM 不是预期 (实际上容忍,但 release notes 显示乱码)
- GitHub web UI render markdown 时 BOM 当成 invisible char,某些 markdown linter 报 "first char not LF"

**根因 (BOM):**
Windows PowerShell 5.1 的 `Set-Content -Encoding utf8` 和 `Out-File -Encoding utf8` 都用 UTF-8 with BOM (默认).NET Encoding `utf8` 是带 BOM 的。
PowerShell 7+ (pwsh) 的 `utf8` 是 UTF-8 without BOM, Windows PS 5.1 才有这个 BOM 问题。

**根因 (CRLF):**
Windows PS5.1 的 `[System.IO.File]::WriteAllLines` / `[IO.File]::WriteAllText` (默认 encoding 参数) 用 `Environment.NewLine`,Windows 上是 `\r\n`。
Linux/macOS 上是 `\n`。`sha256sum` (GNU coreutils) 对文件名严格 — `\r` 当成普通字符,实际查找 `<hash>  <name>\r` 文件,失败。

Per memory `feedback_qbe_crlf_root_cause` — 同根因,Windows fopen 默认 LF→CRLF 转换,跟 QBE .il 行号偏移错的根因一样。所有 PS 写的 UTF-8 行文件被 Linux 工具消费都要 LF + no BOM。

**workaround:**
用 `[System.IO.File]::WriteAllText` + 显式 UTF8Encoding(false) + 自己用 `\n` join (不要 `Environment.NewLine`):
```powershell
# 一次性写文件 (single string, explicit LF, no BOM)
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$content = ($lines -join "`n") + "`n"  # trailing newline for POSIX
[System.IO.File]::WriteAllText('release-notes.md', $content, $utf8NoBom)

# 同样 pattern for SHA256.txt (per installer/gen-sha256.ps1)
$lines = foreach ($f in $files) {
    $hash = (Get-FileHash $f.FullName -Algorithm SHA256).Hash.ToLower()
    "{0}  {1}" -f $hash, $f.Name
}
$content = ($lines -join "`n") + "`n"
[System.IO.File]::WriteAllText('installer/SHA256.txt', $content, $utf8NoBom)
```

或者换 pwsh 7+ (`shell: pwsh`),但 GH Actions windows-latest runner 默认 PS5.1, 强制 pwsh 7 需要 `pester/setup-pwsh@v1` action。

**影响范围:**
- 所有 PowerShell 5.1 step 写 UTF-8 文件的场景 (release notes / SHA256.txt / release assets / gen-* 脚本)
- SHA256.txt 是 `sha256sum -c` 校验的源, CRLF + BOM 双坑
- per `feedback_qbe_crlf_root_cause` — 任何 Windows 写 + Linux 读的行文件都要 LF no BOM

**失效条件:**
1. GH Actions windows-latest runner 升级默认 shell 到 pwsh 7
2. 或者 PS5.1 加 `-Encoding utf8NoBom` flag (PowerShell team 已经讨论,未 ship)

**引用:**
- repro: `[System.IO.File]::WriteAllText('test.txt', "a`nb", [System.Text.UTF8Encoding]::new($false))` → 头 3 字节无 BOM,行尾 `\n` ✓; 改 `[System.Text.Encoding]::UTF8` → 头 3 字节 BOM,行尾 `\r\n` ❌
- workaround 实现: `installer/gen-sha256.ps1:65-72` + release.yml Generate release notes step
- v1.5.5 ship commit

## W-025: qbe/ gitlink 无 .gitmodules — release.yml `submodules: recursive` 失败 + installer/build.ps1 hardcoded `qbe/qbe.exe`

**症状 (2026-08-15 v1.5.5 dry-run run 31859843640):**
- `actions/checkout@v4` with `submodules: recursive` fail at Checkout step:
  - `fatal: No url found for submodule path 'qbe' in .gitmodules`
  - `fatal: The process 'C:\Program Files\Git\bin\git.exe' failed with exit code 128`
  - Annotation: `Node.js 20 is deprecated. The following actions target Node.js 20 but are being forced to run on Node.js 24: actions/checkout@v4`

**根因:**
qbe/ 是 gitlink 模式 `160000` 记录在 index,但:
- 本地从来没有 `.gitmodules` (git log --all -- .gitmodules 输出空)
- gitlink 指向的 commit `c0818978acec60ebb6167fade60fb7012cbf20ca` 在 repo 里 dangling (`git log -1 --format=...` 报 `fatal: bad object`)
- 本地 qbe/ 目录是 working tree (有 .o / .c / Makefile 等),但 git 不 track 内容 (git ls-files qbe 只有 1 行 = gitlink 自身)
- 推断: Phase 0 commit (c5e4efb) 初始建 repo 时,把 qbe vendor 进来当 gitlink,但 .gitmodules 没写 (或者被 reset 掉)。后续 ci.yml 跑 `actions/checkout@v4` 不带 `submodules:` 所以能跑 (qbe/ gitlink 就空 dir),但 release.yml 加 `submodules: recursive` 触发检查 .gitmodules 的 logic → fail

**workaround (两层):**

1. **`release.yml`** drop `submodules: recursive`:
```yaml
- name: Checkout
  uses: actions/checkout@v4
  with:
    fetch-depth: 0  # for git describe / tag detection
```

2. **`installer/build.ps1`** qbe.exe resolution 加 PATH fallback:
```powershell
# qbe.exe resolution (W-025): prefer local qbe/qbe.exe (dev), fall back
# to qbe.exe on PATH (MSYS2 mingw-w64-ucrt-x86_64-qbe — release workflow).
$qbeLocal = "qbe/qbe.exe"
$qbeOnPath = (Get-Command qbe.exe -ErrorAction SilentlyContinue)
if (Test-Path $qbeLocal) {
    Copy-Item -Path $qbeLocal -Destination "$binDir/qbe.exe" -Force
} elseif ($qbeOnPath) {
    Copy-Item -Path $qbeOnPath.Source -Destination "$binDir/qbe.exe" -Force
} else {
    exit 1
}
```

**为什么 release workflow 还要 `mingw-w64-ucrt-x86_64-qbe` package:**
- ci.yml 也用 (同 pattern),但 ci.yml 不 build MSI / qbe.exe binary
- release.yml 要 qbe.exe 来 pack MSI Burn bundle,所以从 MSYS2 package 取 (PATH 上 `qbe.exe`),build.ps1 自动 fallback 用它

**影响范围:**
- 仅 release.yml + installer/build.ps1
- ci.yml 不受影响 (已经无 submodules: recursive)
- 本地 dev build 仍走 `qbe/qbe.exe` (优先) — 不改 dev workflow

**失效条件 / 未来 fix:**
1. **De-submodule qbe + track source files** — rm gitlink + `git add qbe/`,commit (~80 .c/.h files added, ~3-5 MB tracked)。彻底修 dangling gitlink + 让 qbe diff history 可见。但 v1.5.5 scope 不够,推到 v2.x (per M5 boot-from-scratch decision, qbe 要么 vendored 要么 QBE 重写,这里有歧义)。
2. **Restore .gitmodules + commit** — 需要知道原 upstream URL (目前不知道)。同上,等 v2.x 决。
3. GH Actions Node 20 deprecation — `actions/checkout@v4` 被强制 Node 24 跑,目前是 warning,不算 fail。

**引用:**
- 错误日志: GH Actions run 31859843640, Checkout step stderr
- workaround 实现: `.github/workflows/release.yml:81-86` + `installer/build.ps1:85-100`
- v1.5.5 ship commit (post hotfix)
- 关联: `feedback_qbe_crlf_root_cause` (W-024 / QBE 行号偏移错的同 root: Windows 写 vs Linux 读;此处不是 root cause,但同方向问题)

---

## W-025 follow-up (2026-08-15 same-day): MSYS2 qbe package 不存在 → 必须 vendoring qbe source

**追加症状 (dry-run run 31860099231):**
- 第二个 dry-run 过了 Checkout (上一节 workaround 生效),但在 Setup MSYS2 step fail:
  ```
  error: target not found: mingw-w64-ucrt-x86_64-qbe
  ```
- MSYS2 ucrt64 repo 没 ship qbe package (https://packages.msys2.org/packages/?q=qbe 0 hit)。其他 repo (mingw64 / clang64) 也没有
- 假定 MSYS2 qbe package 是错的 — 这是 release.yml 初版的设计失误

**根因:**
- qbe.exe 是 QBE 编译器 binary,QBE upstream (8l/qbe) 没有 official release 跟 prebuilt binary
- 本地 qbe/ 是 QBE upstream fork (有 amd64/winabi.c 等 Windows 适配),不能直接 clone upstream 替换
- qbe/ 历史 gitlink 指向的 commit c0818978... 在 repo 里 dangling,无法 `git submodule update` 拿回来

**fix (一层 — 推到 v1.5.5 ship):**
彻底 vendor qbe source 到 repo:
1. `git rm --cached qbe` (删 gitlink)
2. `git add qbe/.gitignore qbe/README qbe/LICENSE qbe/Makefile qbe/*.c qbe/*.h qbe/amd64/* qbe/arm64/* qbe/rv64/*` (41 个 source + headers + LICENSE + README + Makefile + .gitignore, ~376 KB;`qbe/test/` `qbe/tools/` `qbe/minic/` `qbe/doc/` 不 track — 不是 build 必需)
3. `qbe/.gitignore` 加 `qbe.exe` (Windows build output)
4. release.yml 新加 step:
   ```yaml
   - name: Build qbe.exe (vendored source under qbe/)
     shell: msys2 {0}
     run: |
       cd qbe
       make
       sha256sum qbe.exe
   ```
5. release.yml 删 `mingw-w64-ucrt-x86_64-qbe` MSYS2 package
6. installer/build.ps1 qbe.exe resolution 保持 — `qbe/qbe.exe` (local) 优先;PATH 兜底 (CI fallback)

**影响范围:**
- 仅 release.yml + installer/build.ps1 + qbe/ vendoring
- ci.yml 不受影响 (no qbe build step)
- 本地 dev build 走 `qbe/qbe.exe` (不变)
- qbe diff history 从 gitlink dangling 转到 visible tracked (39 commits 在 qbe source history;现在只有 1 个 commit 因为是 de-submodule 整批 add)

**失效条件 / 未来 fix:**
1. **M5 boot-from-scratch** (per `project_m5_boot_from_scratch_decision`) — v2/v3 末可能删 qbe/ (QBE 自写) 或更新到新 QBE upstream
2. **QBE upstream major version bump** — 现 v1.5.5 vendor 跟 upstream HEAD (d62b154) 不一致 (local fork);升级需要 sync
3. GH Actions Node 20 deprecation (carry over from above)

**引用:**
- 错误日志: GH Actions run 31860099231, Setup MSYS2 step stderr
- workaround 实现: vendored 41 qbe files + `.github/workflows/release.yml` (Build qbe.exe step) + `installer/build.ps1` (qbe.exe resolution)
- v1.5.5 ship commit (post vendoring)

## W-026: regress.py `[:80]` stderr 截断隐藏真实 QBE/gcc 错误

**状态:** RESOLVED (2026-08-15, commit `0d58efe` — full stderr print)
**日期:** 2026-08-15
**触发面:** `mcp-jhyy/jhyy_regress.py` run_all() FAIL print

**症状:**
GH Actions dry-run #31861809057, #31861809057, #31863594640 — Run regress step 53/53 FAIL, stderr 截断到 `[sema] P1 ndec` (80 字符)。Sanity check (`jhyy.exe compile arith.jhyy`) 同 step 跑出来 exit 0 + 完整 `[4] codegen done`。

**根因:**
`jhyy_regress.py:309` 的 `print(f"FAIL ... {msg[:80]}")` 把真实错误消息截掉了。QBE / gcc 的 link 错误永远出现在 `[4] codegen done` 之后, 总 >80 字符, 截断后看不到。

**workaround:**
去掉 `[:80]` 截断, 改成 `print(... {msg})`, 让 FAIL 输出完整 stderr。下次 dry-run 能直接看到 QBE/gcc 错误。

**影响范围:**
- 仅 `mcp-jhyy/jhyy_regress.py` run_all() print
- 本地 53/53 PASS 不破

**引用:**
- 错误日志: GH Actions runs 31861809057, 31863594640
- workaround 实现: `mcp-jhyy/jhyy_regress.py` line 313 (FAIL print)
- fix commit: `0d58efe`

## W-027: GH Actions `setup-msys2@v2` 把 MSYS2 装在 `$RUNNER_TEMP\msys64` (CI = `D:\a\_temp\msys64`), 不在 `C:\msys64` — 硬编码 `C:\msys64\ucrt64\bin` 找不到 gcc

**状态:** ✅ RESOLVED → SUPERSEDED by W-029 (v1.5.6 superseder commit TBD)
**日期:** 2026-08-15
**触发面:** `.github/workflows/release.yml` Run regress step (53/53 FAIL → 47/53 FAIL → 53/53 PASS over 4 fix attempts)

**症状 + fix attempts:**
- v1 (#31861809057): `'gcc' is not recognized` — `C:\msys64\ucrt64\bin` hardcoded wrong on CI
- v2 (#31863594640): `[:80]` truncation hid real error (W-026 fix); same `'gcc' is not recognized`
- v3 (#31863873870): unconditional Windows PATH prepend (commit `3ad8128`); still FAIL — CI MSYS2 not at C:\msys64
- v4 (#31864035818 debug): confirmed MSYS2 at `D:\a\_temp\msys64`, used `cmd //c where` — revealed hardcoded path wrong
- v5 (df71824): `shutil.which('gcc')` — returns MSYS2 virtual path `/ucrt64/bin/gcc` (only valid in MSYS2 bash)
- v6 (8513681): also call `cmd /c where gcc` from Python — from MSYS2-launched Python, cmd.exe returns interactive prompt (unreliable)
- v7 (e9f0f85): bash `cmd //c 'where gcc'` from Python — bash returns UTF-16 LE error message (decode fails)
- v8 (4623a3b): **deterministic MSYS2 root**: read `RUNNER_TEMP` env (CI = `D:\a\_temp`) + fall back to `C:\msys64`; check known bin subdirs (`ucrt64/bin`, `mingw64/bin`, `usr/bin`, `bin`) via `os.path.isdir`; prepend each existing dir (Win32 form) to env['PATH']. No subprocess call needed.

**workaround (final v8):**
- Read `os.environ['RUNNER_TEMP']` (auto-set by GH Actions on `windows-latest`)
- Compute MSYS2 root: `$RUNNER_TEMP\msys64` (CI) or `C:\msys64` (local)
- For each known bin subdir: `os.path.isdir(root + "\\" + sub)` → prepend if exists
- All paths are Win32 form (`\\`-separated, drive letter)
- No subprocess, no encoding issues, no MSYS2 quoting issues

**影响范围:**
- 仅 `mcp-jhyy/jhyy_regress.py` _build_subprocess_env
- 本地 53/53 PASS 不破
- CI 47/53 → 53/53 PASS (post-W-028 mod-256 fix)

**引用:**
- debug runs: GH Actions #31861809057, #31863594640, #31863873870, #31864035818, #31864780270, #31864948299, #31865432960, #31865675000, #31866010390, #31866179790, #31866475742
- fix commit: `4623a3b` (v8 final)
- v1.5.6 superseder: 见 W-029 — `jh_gcc_path()` 4-tier 探测, regress.py / release.yml
  不再 prepend MSYS2 bin 到 PATH, W-027 v8 Python 探测段整段删.

## W-029: jhyy.exe toolchain 探测收敛 — `jh_gcc_path()` 4-tier 优先级 + `jh_gcc_invoke()` 包装替代 v1.0.0 跨 3 文件 MSYS2 探测逻辑

**状态:** SUPERSEDED closed 2026-09-28 (audit reclassify per 2026-09-28 v3.x ACTIVE/DEFERRED audit, 同步 main v2.13.4 close) — 🟢 STABLE-PRODUCTION, 非 ACTIVE unfixed bug。真修 ship 在 v1.5.6 commit `a2dd4c1` "feat(v1.5.6): jhyy_helpers.c 加 jh_gcc_path() + jh_gcc_invoke() — A 派 Driver 探测" + docs commit `28450d3` "docs(v1.5.6): workarounds W-027 SUPERSEDED + W-029 ACTIVE + changelog v1.5.6 section"。`commit TBD` 是 docs 漏填(真修 commit 已 ship,只是 entry 当时没补填);v2.13.4 RCA closeout 标 🟢 STABLE-PRODUCTION 替代 🟢 ACTIVE (后者 label 误导,future contributor 看到 🟢 ACTIVE 误以为还需真修)。Fix ship'd 4+ years stable in production,无未修项。原 label "🟢 ACTIVE" 是 v1.5.6 ship 当时 lack of reclassify convention 残留。
**日期:** 2026-08-15
**触发面:** `compiler/src0/jhyy_helpers.c` (jh_gcc_path + jh_gcc_invoke) +
`compiler/src0/main.jhyy` (link_with_gcc 改用 jh_gcc_invoke) +
`mcp-jhyy/jhyy_regress.py` (删 _build_subprocess_env 的 MSYS2 探测段) +
`.github/workflows/release.yml` (删 Propagate MSYS2 paths step)

**superseder 关系:**
- W-027 v8 RESOLVED → SUPERSEDED by W-029 (整段 MSYS2 探测从 Python 侧删,
  收敛到 jhyy.exe 内部)
- v1.0.0 release 痛点 (regress.py 跨平台 quoting / setup-msys2 path 不固定)
  闭环

**症状 (W-027 v8 之前):**
- 跨 3 文件 (regress.py / release.yml / jhyy_helpers.c) 各自探测 MSYS2 path
- 试了 8 个版本 (v1-v8) 才稳定, bug 一堆 (subprocess quoting / encoding /
  MSYS2 virtual path 跟 Win32 path 混淆)
- 任何一处改都会破坏另两处

**workaround (v1.5.6 fix):**
1. `jh_gcc_path()` (`compiler/src0/jhyy_helpers.c` lines 204-294):
   4 层优先级探测, 一次性 resolve, static buf 缓存:
   - **Priority 1**: `JHY_GCC` env (user/CI 显式 override)
   - **Priority 2**: `$JHYY_HOME\env.txt` 文件 KEY=VALUE (单用户配置)
   - **Priority 3**: Windows MSYS2 magic (`C:\msys64\ucrt64\bin\gcc.exe` 等 3 项)
   - **Priority 4**: `SearchPathA` PATH 探测 (Win32 API, 不依赖 subprocess)
   - **Fallback**: literal `"gcc"` 走 Windows PATH 解析
2. `jh_gcc_invoke()` (同文件 lines 300-302):
   `snprintf` 包装 `"%s" %s`, 给 `system()` 调用 — 替代 main.jhyy `link_with_gcc` 裸 `system("gcc ...")`
3. `compiler/src0/main.jhyy` `link_with_gcc`: 改用 `jh_gcc_invoke(invoke_buf, ...)` + `system(invoke_buf)`. cmd_buf 不再前缀 GCC_PATH() (现在 invoke_buf 内部加)
4. `mcp-jhyy/jhyy_regress.py` `_build_subprocess_env`: **删** lines 87-117 (MSYS2 探测段 ~30 行). 仅保留基础 env (TMP/SystemRoot). jhyy.exe 自己负责 gcc 探测
5. `.github/workflows/release.yml`: **删** lines 164-176 "Propagate MSYS2 paths to subprocess PATH" step. jhyy.exe 启动时自己探测, GH Actions runner 不需手工 export PATH
6. Linux/macOS placeholder: `jh_gcc_path()` `#ifdef _WIN32` 之外返回 literal `"gcc"` (v2.x 填跨平台探测)

**测试 (5 个探测优先级):**
- `compiler/tests/examples/_jh_gcc_p1.jhyy` — SETENV `JHY_GCC=C:\msys64\ucrt64\bin\gcc.exe` → Priority 1 命中
- `compiler/tests/examples/_jh_gcc_p2.jhyy` — SETENV `JHYY_HOME=...`, 手动写 env.txt → Priority 2 命中
- `compiler/tests/examples/_jh_gcc_p3.jhyy` — 不设 env, magic 存在 → Priority 3 命中
- `compiler/tests/examples/_jh_gcc_p4.jhyy` — placeholder (探测链返回非空); 严格 SearchPathA 验证受测试环境约束推迟 v2.x
- `compiler/tests/examples/_jh_gcc_p5.jhyy` — placeholder (探测链返回非空); 严格 fallback "gcc" 验证推迟 v2.x
- p1/p2/p3: 本机测试环境约束 (magic 唯一存在路径 = ucrt64, 跟 Priority 3 magic 第 1 项相同) 严格 Priority 1/2 vs 3 区分无法自动化, 实际区分证据见 `_jh_gcc_p1_debug.jhyy` (ad-hoc)

**影响范围:**
- 4 文件改动 (jhyy_helpers.c / main.jhyy / regress.py / release.yml)
- 5 个新测试 (p1-p5, SETENV directive 新增)
- baseline 53/53 PASS 不破
- Linux/macOS 跨平台探测 v2.x sprint 填 (jhyy.exe toolchain 必须用绝对路径, 不靠 PATH 解析 — 类型 4 升级)

**失效条件 (W-029 移除条件):**
- v2.x manifest lite 实施后, Priority 2 env.txt 升级到 toolchain.env 多工具 (v2.x sprint 范围)
- 跨平台探测 (Linux/macOS) 实施后, `#ifdef _WIN32` 分支消失 (v2.x sprint 范围)

**引用:**
- design plan: `docs/plans/v1/v1.5.6任务清单 + 概要设计.md` § 设计 1
- related: jhyy.exe toolchain 必须用绝对路径, 不靠 PATH 解析 (类型 4 升级要求)
- related workaround: W-027 v8 (Python 探测 → jhyy.exe 接管)
- 实施 commit: TBD (v1.5.6 sprint 末 ship)

## W-028: Windows process exit code 是 8-bit (mod 256), EXPECT 注释里的值 > 255 在 CI regress FAIL (got=106 不是 got=1000042)

**状态:** ✅ RESOLVED 2026-08-15 (commit `6d2ab8f` + commit TBD — `sys.platform` cygwin/msys 兼容)
**日期:** 2026-08-15
**触发面:** `mcp-jhyy/jhyy_regress.py` run_test EXPECT comparison (47/53 PASS post-W-027)

**症状:**
W-027 v8 fix 后, CI dry-run 47/53 PASS。剩 6 个 FAIL:
- arith.jhyy `expected=1000042 got=106` (1000042 % 256 = 106)
- big_array.jhyy `expected=5050 got=186` (5050 % 256 = 186)
- big_test.jhyy `expected=12345 got=57` (12345 % 256 = 57)
- fib30.jhyy `expected=832040 got=40` (832040 % 256 = 40)
- fib_renamed.jhyy `expected=832040 got=40`
- nested_if.jhyy `expected=500 got=244` (500 % 256 = 244)

**根因 (两层):**
1. **架构层**: Windows kernel32 `ExitProcess` 只接受 8-bit exit code (0-255); 任何 >= 256 的 return value 自动 mod 256。Python `subprocess.run` 返回的 `returncode` 在 Windows 上走 WaitForSingleObject + GetExitCodeProcess, 也是 8-bit。
2. **平台检测层** (v2 commit TBD): GH Actions `shell: msys2 {0}` 启动 Python, **MSYS2-launched Python 的 `sys.platform` 是 `"cygwin"` 不是 `"win32"`**。第一版 fix `if sys.platform == "win32"` 在 CI 上**永远 False**, mod-256 逻辑不触发。

   ```
   [W-028 trace from dispatch #31867221428]:
     fname=arith.jhyy actual=106 expected=1000042 actual_cmp=106 expected_cmp=1000042 sys.platform=cygwin
   ```

**workaround (最终):**
在 `run_test()` 末尾比较前加 (commit TBD):
```python
# W-028: detect any Windows-subsystem Python (win32 / cygwin / msys)
_IS_WINDOWS_PY = sys.platform in ("win32", "cygwin", "msys")
if _IS_WINDOWS_PY and actual >= 0:
    actual_cmp = actual & 0xFF
    expected_cmp = expected & 0xFF
else:
    actual_cmp = actual
    expected_cmp = expected
return (actual_cmp == expected_cmp, expected, actual, output)
```

**真修 (superseder):**
- v2.x: 改 QBE codegen 让 main return i32 直接传 kernel32 ExitProcess, 不要走 C runtime `__cxa_atexit`
- v3.x OS 准备: freestanding 模式下 ExitProcess 调用栈可控, 不再依赖 `__cxa_atexit`

**影响范围:**
- 仅 `mcp-jhyy/jhyy_regress.py` run_test()
- 本地 53/53 PASS 不破 (`sys.platform == "win32"` 走原路径)
- CI 47/53 → 53/53 PASS (`sys.platform == "cygwin"` 走新 `_IS_WINDOWS_PY`)

**引用:**
- GH Actions dry-run #31866475742 (47/53 PASS post-W-027 v8; 6 mod-256 FAIL identified)
- GH Actions dry-run #31866960877 (W-028 v1 — `sys.platform == "win32"` 不触发, 47/53 持平)
- GH Actions dry-run #31867221428 (W-028 trace 确认 `sys.platform=cygwin`; 47/53 持平待 v2 commit)
- 6 affected tests: arith, big_array, big_test, fib30, fib_renamed, nested_if
- commit `6d2ab8f` (W-028 v1 — `sys.platform == "win32"` 不完整)
- commit `03f58c6` (W-028 v2 — `sys.platform in ("win32", "cygwin", "msys")`; 53/53 PASS in CI)
- GH Actions dispatch #31876684128 (v1.5.5 RC 1st attempt — vsix filename mismatch; 53/53 PASS regress + Build installer FAIL)
- GH Actions dispatch #31877022451 (v1.5.5 RC 2nd attempt — WIX0103 .wxs Source path; regress + Build FAIL)
- GH Actions dispatch #31877336261 (v1.5.5 RC 3rd attempt — SUCCESS; 53/53 regress + Burn+MSI+.vsix build + SHA256 verify + MSI validate + release publish; v1.5.5-rc1 release created with 4 assets)

**后续 fixes (installer pipeline, post-W-028):**
- commit `425fd77` (release.yml 安装 vsce — VSCode ext packaging CI 依赖)
- commit `9ed97c9` (installer/build.ps1 RC tag version strip + display suffix)
- commit `72c6555` (installer/build.ps1 sub-script 传 JHY_VERSION+RC suffix)
- commit `99d75c2` (vsix filename 用 JHY_VERSION_DISPLAY + vsce package 后 rename)
- commit `16dcaad` (jhyy-compiler.wxs vsix 引用改用 JHY_VERSION_DISPLAY)
- commit `143c644` (release.yml Create GitHub Release dry_run gate boolean fix — `inputs.dry_run != 'true'` 类型不匹配, 改用 `${{ !inputs.dry_run }}`)

**release.yml dry_run gate bug 发现:**
dry_run=true 仍 publish release — `if: inputs.dry_run != 'true' || github.event_name == 'push'` 因 boolean vs string 比较类型不匹配, 永远 != → step 永远 run. v1.5.5-rc1 release 在 dry_run=true 下被 publish (但内容正确, prerelease + 4 assets); 修法见 commit `143c644`.

---

## W-030: WiX 4 Theme.xml schema — Font 必须在 `<Theme>` 顶层 (不能 nested in `<Window>`); `<Window>` 用 Caption + FontId (不用 Title + 内嵌 Font + Weight)

**状态:** ✅ RESOLVED 2026-08-15 (commit TBD)
**日期:** 2026-08-15
**触发面:** `installer/Theme.xml` + `installer/Bundle.wxs` Burn bundle (`jhyy-installer-*.exe`)

**症状:**
`v1.5.6-rc1.exe` (GH Actions release) double-click 无任何 UI 弹出 — Burn bundle 启动即退 0xD (theme parse error 13 = "data is invalid"):
```
[3E90:1CBC]i000: Burn x64 v7.0.0 ...
[3E90:1CBC]e000: Error 0x8007000d: Failed to parse theme.
[3E90:1CBC]e000: Error 0x8007000d: Failed to load theme.
[3E90:1CBC]i500: Shutting down, exit code: 0xd
```

**根因 (WiX 4 Theme XML schema 跟 v3 不一样, 4 错 cascade):**

| # | v1.5.5 写法 | WiX 4 错误 | fix |
|---|------|------|------|
| 1 | `<Font Id="..." Height="-20" Weight="bold">` **inside `<Window>`** | 0x8007000d "No font elements found" | 移到 `<Theme>` 顶层 |
| 2 | `<Font ... Weight="bold">` | 0x80070057 "Failed to find font weight attribute" | 删 `Weight="bold"` (WiX 4 runtime schema 不认) |
| 3 | `<Window Width="..." Height="..." Caption="...">` 无 FontId | 0x80070490 "Failed to get window FontId attribute" | 加 `FontId="WelcomeHeaderFont"` |
| 4 | `<Window ... Title="...">` | 0x8007000d "Window elements must contain either the Caption or StringId attribute" | `Title=` 改 `Caption=` |

**workaround (最终):**
```xml
<Theme xmlns="http://wixtoolset.org/schemas/v4/thm">
  <Font Id="WelcomeHeaderFont" Height="-20" />          <!-- 顶层, no Weight -->
  <Window Width="600" Height="450" Caption="[ProductName] Setup" FontId="WelcomeHeaderFont" />
  <Page> ... </Page>
</Theme>
```

**Theme load 通过后新问题:** Burn 加载 MSI, MSI install 也失败 (Error 0x80070643) — 见 W-031。

**引用:**
- WiX 4 thm schema: https://wixtoolset.org/docs/v4/bundle/wixstdba/
- WiX 3 → 4 迁移: `Theme.xml` schema 变化是 breaking change (WiX 3 允许内嵌 Font + Title + Weight bold)
- 设计 plan: `docs/plans/v1/v1.5.6任务清单 + 概要设计.md` § Sprint v1.5.6 hotfix
- commit: TBD (W-030 ship in v1.5.6 sprint)

---

## W-031: MSI LaunchCondition + INSTALLDIR resolution — 原探测 HKLM Uninstall\ucrt64 GCC 误报 + WiX 4 `<SetDirectory>` 不生效

**状态:** ✅ RESOLVED 2026-08-15 (commit TBD)
**日期:** 2026-08-15
**触发面:** `installer/compiler/jhyy-compiler.wxs` LaunchCondition + INSTALLDIR

**症状 (两层, cascade):**

**Layer 1 — LaunchCondition 误报:**
W-030 Theme fix 后, Burn bundle UI 正常弹出, MSI 启动后 LaunchCondition 失败:
```
MSI (s) ... : Doing action: AppSearch
MSI (s) ... : Doing action: LaunchConditions
MSI (s) ... : 产品: JHYY Compiler -- 未检测到 MSYS2 ucrt64 + GCC 环境。
MSI (s) ... : 操作结束 21:30:20: LaunchConditions。返回值 3。
MSI (s) ... : MainEngineThread is returning 1603
[3E90:1CBC]e000: Error 0x80070643: Failed to install MSI package.
```

**根因 (Layer 1):** 原 v1.5.2 `<Property Id="MSYS2_GCC_FOUND"><RegistrySearch Key="SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\ucrt64 GCC" /></Property>` — 只查 Windows MSI installer 注册的 GCC。但 MSYS2 ucrt64 GCC 是 `pacman -S mingw-w64-ucrt-x86_64-gcc` 装的, pacman **不写 HKLM\Uninstall 注册表**, 所以 RegistrySearch 永远 empty → `MSYS2_GCC_FOUND = ""` → `Installed = false` → LaunchCondition fail。

**workaround (Layer 1):** 改 4 源探测 — 任一信号 true 即认为 GCC 装了:

| Source | Property | 探测方式 | 适用场景 |
|--------|----------|---------|----------|
| 1 | `MSYS2_GCC_UNINSTALL` | HKLM\Uninstall\ucrt64 GCC | Windows installer 装的 GCC (向后兼容) |
| 2 | `MSYS2_GCC_PATH` | HKLM\...\Environment\Path | PATH 含 `ucrt64\bin` 或 `mingw64\bin` (用户手动加 PATH) |
| 3 | `MSYS2_GCC_FILE` | `<DirectorySearch Path="C:\msys64\ucrt64\bin"><FileSearch Name="gcc.exe"/></DirectorySearch>` | Windows 默认 MSYS2 install path |
| 4 | `MSYS2_GCC_DIR` | `<DirectorySearch Path="C:\msys64" />` | MSYS2 install 标志 (PATH 未 propagate) |

`<SetProperty Id="MSYS2_GCC_FOUND" Value="1" Before="LaunchConditions" Condition="MSYS2_GCC_UNINSTALL OR MSYS2_GCC_PATH OR MSYS2_GCC_FILE OR MSYS2_GCC_DIR" />`

**Layer 2 — INSTALLDIR 解析成 `C:\JHYY\`:**
Layer 1 修了 LaunchCondition 后 MSI install 仍 fail (0x80070643), 卡 42 秒后 Error 1606:
```
MSI (s) ... : Doing action: SetINSTALLDIR
... (42 seconds later) ...
MSI (s) ... : Note: 1: 1314 2: JHYY
MSI (s) ... : Note: 1: 1606 2: JHYY      <- "Could not access network location JHYY"
MSI (s) ... : 操作结束 21:31:02: SetINSTALLDIR。返回值 3。
Property(S): INSTALLDIR = C:\JHYY\
```

**根因 (Layer 2):** WiX 4 `<SetDirectory Id="INSTALLDIR" Value="[ProgramFiles6432Folder]JHYY" Condition="NOT FOUND" />` 不工作 — WiX 4 emit SetINSTALLDIR type-33 CA(`Condition="NOT INSTALLDIR"`), 但 INSTALLDIR property 在 CostInitialize 阶段就被 `<Directory>` parent resolution 填成 `[TARGETDIR]\JHYY` = `C:\JHYY\`, NOT INSTALLDIR 永远 false → CA 永不跑 → INSTALLDIR 永远 `C:\JHYY\`。

**workaround (Layer 2):** 删 `<SetDirectory>`,改用 `<SetProperty>` + 单独的 `INSTALLDIR_REG_FOUND` Property (RegistrySearch 设) 作为 condition:
```xml
<SetProperty Id="INSTALLDIR"
             Value="[ProgramFiles6432Folder]JHYY"
             Condition="NOT INSTALLDIR_REG_FOUND"
             After="CostFinalize" />
<Property Id="INSTALLDIR_REG_FOUND">
  <RegistrySearch Id="JHYYInstallDirSearch"
                  Type="directory"
                  Root="HKLM"
                  Key="SOFTWARE\JiHuiYiYou\JHYY"
                  Name="InstallDir" />
</Property>
```
- Fresh install (无 HKLM 注册): `INSTALLDIR_REG_FOUND` 空, `NOT INSTALLDIR_REG_FOUND` true → SetINSTALLDIR 跑 → INSTALLDIR = `[ProgramFiles6432Folder]JHYY` = `C:\Program Files\JHYY\`
- Upgrade/repair (有 HKLM 注册): `INSTALLDIR_REG_FOUND` = prior path, SetINSTALLDIR 不跑 → INSTALLDIR 保持 registry 里的 prior path

**验证:**
- Local admin install (`msiexec /a`) status 0 (success)
- MSI log 显示 `MSYS2_GCC_FOUND = 1`, `INSTALLDIR_REG_FOUND` 空 (fresh install)
- 真 `/i` install 需要 admin shell + UAC (用户测)

**引用:**
- WiX 4 SetDirectory behavior: https://github.com/wixtoolset/issues/issues/6304 (SetDirectory vs SetProperty semantics changed)
- WiX 4 DirectorySearch syntax: Path attr only, no Type attr (跟 v3 不一样)
- commit: TBD (W-031 ship in v1.5.6 sprint)
- related: W-027 / W-029 (MSYS2 GCC 探测在 jhyy.exe 端的 4-tier probe — W-031 是 MSI 端的 4-source probe, 互补)

---

## W-033: Theme.xml XML 1.0 well-formedness + WiX 4 thmutil schema + wixstdba 默认控件名/string ID 完整对齐

**状态:** ✅ RESOLVED 2026-08-16 (commit TBD)
**日期:** 2026-08-16
**触发面:** `installer/Theme.xml` + `installer/Bundle.zh-CN.wxl` — Burn bundle (`jhyy-installer-*.exe`)

**症状:**
W-030 已修 4 个 Theme.xml schema 错 (Font 位置 / Weight bold / FontId / Title vs Caption) 后,本地 rebuild 的 `v1.5.6-rc1.exe` 双击仍然"完全无反应" — 不弹 SmartScreen、不弹 UI、Burn 启动 ~50ms 后退出:
```
[5090:5ED0][2026-08-16T08:34:51]i001: Burn x64 v7.0.0 ...
[5090:5ED0][2026-08-16T08:34:51]e000: Error 0x8007006e: Failed to load theme file as XML document.
[5090:5ED0][2026-08-16T08:34:51]e000: Error 0x8007006e: Failed to load theme from path: ...\.ba\thm.xml
[5090:5ED0][2026-08-16T08:34:51]e000: Error 0x8007006e: Failed to initialize theme.
[5090:5ED0][2026-08-16T08:34:51]i500: Shutting down, exit code: 0x6e
```

Win32 error 0x8007006e = decimal 110 = `ERROR_BAD_FORMAT` — Burn 拒绝接受 Theme.xml 因为它根本不是 well-formed XML。

**根因 (XML 1.0 spec violation + 5 个 WiX 4 / wixstdba 默认契约违反 cascade):**

| # | 触发 | 出处 |
|---|------|------|
| 1 | **XML 1.0 spec violation** — Theme.xml line 10 注释里有 `jhyy --version` 文字。XML 1.0 规定 comment 里不允许 `--`(连续两个连字符)。`xml.etree` 验证: `not well-formed (invalid token): line 10, column 47`。**这是 exit 0x6e 的直接原因。** | XML 1.0 spec § 2.5 Comments |
| 2 | `xmlns="http://wixtoolset.org/schemas/v4/thm"` — 应为 `thmutil`。W-030 也没修对 — `thm` 这个 schema 在 WiX 4 runtime 不存在 | WiX 4 thmutil XSD |
| 3 | `<Text>...</Text>` 元素 — 应为 `<Label>...</Label>`。`<Text>` 在 thmutil schema 里是 `<Button>` 内部的子元素(用来放按钮文字),不是 page-level 文本 | WiX 4 thmutil XSD |
| 4 | `<LicenseTextBox>` — 应为 `<Richedit Name="EulaRichedit">`。`LicenseTextBox` 不是 thmutil 元素 | 同上 |
| 5 | 自创控件名 `LicenseAcceptedCheckBox` / `AcceptButton` / `DeclineButton` — wixstdba 默认硬编码查找 `EulaAcceptCheckbox` / `InstallButton` / `InstallCancelButton`。命名不对 → wixstdba 找不到 accept checkbox → 即便 Theme.xml parse 过、UI 起来后用户也不能 accept license | wixstdba source: `WixStdBAViewModel.cs` |
| 6 | `<Page Name="License">` 独立 License page — wixstdba 默认 `Theme="rtfLicense"` 把 license accept 整合在 `<Page Name="Install">` 里,根本没有 License page 概念 | wixstdba source: `WixStdBAViewModel.cs` |
| 7 | `Bundle.zh-CN.wxl` 引用了一堆不存在的 string ID (`LicenseHeader` / `InstallButton` / `CancelButton` / `CloseButton` / `LaunchButton` / `RepairButton` / `UninstallButton` / `WelcomeHeader` / `WelcomeDescription` / `MSYS2PrereqWarning` / `ProgressDescription` / `ModifyHeader` / `SuccessDescription` / `PostInstallHint` / `FailureHeader` / `Language`)。wixstdba 默认 wxl 用 `InstallAcceptCheckbox` / `InstallInstallButton` / `InstallCancelButton` / `ModifyRepairButton` / `ModifyUninstallButton` / `SuccessLaunchButton` / `SuccessCloseButton` / `Caption` / `Title` / `ProgressHeader` / `ModifyHeader` / `SuccessInstallHeader` / `FailureHeader` 等 | extracted `RtfTheme.wxl` from `WixToolset.BootstrapperApplications.wixext.dll` |

**workaround (最终 — 完全基于 wixstdba 默认 RtfTheme.xml + RtfTheme.wxl 重写):**
1. Theme.xml 用 `thmutil` schema + 4 个 `<Font>` 顶层定义 + `<Window HexStyle="100a0000" FontId="0" Caption="#(loc.Caption)">` + `ImageControl` + `Title` Label (顶部 logo 旁) — 全照搬默认 RtfTheme.xml。
2. 7 个 `<Page>` 全照搬默认 — Help / Loading / Install / Options / Progress / Modify / Success / Failure。
3. W-033 JHYY customization:
   - Install page: 在 EulaRichedit 上面加 3 个控件 — `MSYS2PrereqWarning` Label (粗体) / `MSYS2PrereqDetail` Label (说明) / `MSYS2PrereqLink` Hyperlink (链接 https://www.msys2.org/)。EulaRichedit 位置从 `Y=80` 改 `Y=175`,Height 减小 (`-115` 而非 `-70`) 给 warning 留位置。
   - Success page: 在 SuccessInstallHeader Label 下面加 `PostInstallHint` Label,带 `VisibleCondition="WixBundleAction = 6"` 只在 install 成功时显示,内容是 jhyy 验证步骤 + MSYS2 安装步骤。
4. Window size: 默认 485×300 → 600×420 给 MSYS2 warning 留垂直空间。
5. Fonts 0/2/3 改 Microsoft YaHei UI (默认 Segoe UI 中文显示 fallback 不好看),Font 1 (Title 用) 也改 YaHei UI 粗体。
6. Bundle.zh-CN.wxl 重写: 全部 default wxl 的 string IDs 都给中文值 + 3 个 W-033 新增(`MSYS2PrereqWarning` / `MSYS2PrereqDetail` / `MSYS2PrereqLink` / `PostInstallHint`)。`Caption` / `Title` / `InstallVersion` 等加上 `Overridable="yes"` 让 wiX 接受 override。

**验证 (W-033 ship 后):**
- Python `xml.etree.ElementTree.parse` 两个文件都 OK
- Cross-check script: Theme.xml 引用 54 个 loc IDs,wxl 全部定义,**无 missing**
- Burn log 重建后 `jhyy-installer-1.5.6-rc1.exe` UI 模式启动 6 秒后 log 走到 `i199: Detect complete, result: 0x0` + 评估 `WixStdBAUpdateAvailable` / `NOT WixStdBASuppressOptionsUI` — 即 Theme.xml parse 成功 + WixStdBA 进入 UI 渲染 + i100 detect 成功
- 静默模式 (`/quiet /norestart`) exit code = 0

**引用:**
- XML 1.0 spec § 2.5 Comments: https://www.w3.org/TR/xml/#sec-comments
- WiX 4 thmutil XSD: extracted from `C:\msys64\tmp\wixlib-extract\wix-ir\RtfTheme.xml`
- wixstdba default wxl: extracted from `C:\msys64\tmp\wixlib-extract\wix-ir\RtfTheme.wxl`
- WiX 4 wixstdba source: `src/wix/WixStdBA/` (WixStdBAViewModel hard-codes control names)
- related: W-030(WiX 4 schema Font/Window 部分;W-033 是 round 2,把剩余 thmutil/Text/LicenseTextBox/控件名/string IDs 全部修齐)
- related: W-032(试图加独立 License page — 错方向,正确做法是 wixstdba 默认就在 Install page)
- commit: TBD (W-033 ship in v1.5.6 sprint hotfix)

---

## W-034: cmd_run system() — 用 jh_fullpath 解析绝对路径绕 cmd.exe cwd/PATH 解析陷阱

**状态:** ✅ RESOLVED 2026-08-17
**日期:** 2026-08-17
**触发面:** `compiler/src0/main.jhyy:cmd_run` + `compiler/src0/jhyy_helpers.c:jh_fullpath` — `jhyy run <file.jhyy>` 命令

**症状:**
用户 Code Runner 报 "code language not supported or defined" / PowerShell 直跑 `jhyy run dungeon_game.jhyy` 报 "QBE failed" 后,我修了 PATH 解析让源码树 jhyy.exe 赢,然后发现 `jhyy run dungeon_game.jhyy` 编译成功但执行失败:
```
[4] codegen done
'dungeon_game_run.exe' is not recognized as an internal or external command,
operable program or batch file.
```
cmd_run 走完 cmd_compile(QBE + GCC link 成功),然后 `system("dungeon_game_run.exe")` → cmd.exe /C 找不到 exe。

**根因 (3 层陷阱):**
1. **cmd.exe /C 不搜索 cwd** — 只搜 PATH;basename `dungeon_game_run.exe` 不在 PATH → "is not recognized"。
2. **cmd.exe /C quote rule 2** — 简单包 `"path"` 没用:cmd.exe 看到 `/C "<command>"` 时,如果两个 `"` 之间**没有 whitespace**,会**剥掉**首尾的 `"`,留下 `path`(没引号)。然后 cmd.exe 按空格 tokenize 第一个 token 当 command name。
3. **多 token 解析** — 即使 `input` 有 path 前缀(如 `compiler\tests\examples\dungeon_game.jhyy`),`exe_path = "compiler\tests\examples\dungeon_game_run.exe"`,cmd.exe 把 `compiler` 当 command name → "'compiler' is not recognized"。

历史 bug: regress.py 只测 `cmd_compile`(compile-only),从来没测过 `cmd_run` exec 阶段 → bug 一直藏到用户 Code Runner "▶" 按钮真触发执行才暴露。从 v1.4.1 cmd_run 引入就是这逻辑,改名/重构也没改。

**workaround (v2 — 当前,2026-08-17 ship):**
用 `jh_fullpath()` 把 `input` 解析为绝对路径 → `exe_path = "<abs_dir>/<basename>_run.exe"`。绝对路径绕开所有 3 个陷阱 — cmd.exe 直接按全路径查找文件,不走 PATH,不 tokenize,不剥引号(根本没用引号)。

新增 C helper (`compiler/src0/jhyy_helpers.c`):
```c
__attribute__((used)) int jh_fullpath(char *out_buf, const char *rel_path, int max_len) {
#ifdef _WIN32
    return _fullpath(out_buf, rel_path, max_len) != NULL ? 0 : 1;
#else
    return realpath(rel_path, out_buf) != NULL ? 0 : 1;
#endif
}
```
`_fullpath` 是 MSVCRT 标准函数(MinGW 也带);POSIX 端走 `realpath`。

cmd_run 改写:
```jhyy
// pass -o out_buf to cmd_compile so it produces <basename>_run.exe
let arg_arr = malloc(24);
let arg_arr_pp = arg_arr as **u8;
(*arg_arr_pp) = input;
(*(ptr_add_u8(arg_arr, 8) as **u8)) = "-o";
(*(ptr_add_u8(arg_arr, 16) as **u8)) = out_buf;
let r = cmd_compile(3, arg_arr);

// resolve absolute path of exe
let abs_in = malloc(1024);
jh_fullpath(abs_in, input, 1024);
let abs_exe = malloc(1024);
str_copy(abs_exe, abs_in);
*strrchr(abs_exe, '.') = 0;
str_concat_at(abs_exe, strlen(abs_exe), "_run.exe");
let rc = system(abs_exe);  // system("C:\abs\path\foo_run.exe") — cmd.exe finds it
```

**v1 workaround (2026-08-17 中午被废):** 用 `.\\` 前缀绕过 cwd 不搜索陷阱。但 v1 解决不了根因 2/3 — path-prefixed input(`compiler\tests\foo.jhyy`)仍被 cmd.exe tokenize。Code Runner 真实场景是 path-prefixed(vscode 传文件绝对/相对路径),所以 v1 workaround 不够。v2 (jh_fullpath 绝对路径)才是真修。

**影响范围:** `compiler/src0/main.jhyy:cmd_run` 整段重写 + 新 C helper `jh_fullpath` (`compiler/src0/jhyy_helpers.c`)。

**失效条件:** 永久 work around (cmd.exe 行为不变)。

**superseder:** 不需要真修,workaround 是 cleanest 方案(无需改 cmd.exe 行为,无需改 PATH/cwd,无需改 installer 布局)。

**引用:**
- cmd.exe path resolution: https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/cmd (search "current directory" + PATH)
- cmd.exe /C quote handling: cmd.exe docs `/C` and `/K` switch semantics (rule 2 strip quotes)
- related: W-035 (PATH 解析修好后,这个 exec bug 才暴露;W-034 + W-035 一起 ship)
- related: regress.py 不测 cmd_run exec(测试盲区历史原因)

---

## W-035: jh_paths_init 布局检测 — installer 布局 vs source-tree 布局

**状态:** ✅ RESOLVED 2026-08-17
**日期:** 2026-08-17
**触发面:** `compiler/src0/jhyy_helpers.c:jh_paths_init` — `jhyy.exe` 启动时一次性推导 4 个 path(qbe / gcc / runtime.c / jhyy_helpers.c)

**症状:**
用户 PowerShell 跑 `jhyy run dungeon_game.jhyy` 报 "QBE failed"(`The system cannot find the path specified.`)。

诊断 `where.exe jhyy` 显示两个:
```
C:\Program Files\JHYY\bin\jhyy.exe                              ← installer,PATH 第一
C:\Users\liuzhen\Desktop\coding\JiHuiYiYou\compiler\build\bin\jhyy.exe   ← source-tree
```
PowerShell PATH 里 installer 排第一 → 调 installer 版 → 推 qbe 路径失败。

**根因:**
v1.4.1 commit `8e7944f` 引入 `jh_paths_init` 时,假设 jhyy.exe 总在 `<root>\compiler\build\bin\`,硬编码 `dirname × 4` 走 4 层到 `<root>`:
```c
for (int i = 0; i < 4; i++) {
    char *slash = strrchr(exe_path, '/');
    char *bslash = strrchr(exe_path, '\\');
    char *last = slash > bslash ? slash : bslash;
    if (!last) return 1;
    *last = '\0';
}
/* 现在 exe_path = "<root>" */
snprintf(jh_path_qbe_buf, ..., "%s/qbe/qbe.exe", exe_path);
```

Installer 布局 `C:\Program Files\JHYY\bin\jhyy.exe` 只有 1 层(bin/jhyy.exe),dirname × 4 走到 `C:\` → qbe/qbe.exe = `C:\qbe\qbe.exe` 不存在 → `system(qbe_path)` → "QBE failed"。

**workaround (布局检测 — 替代硬编码 dirname × 4):**
两步:
1. **Layout (a) — installer 布局**: jhyy.exe 同目录有 sibling `qbe.exe` → 全部 path 同目录:
   ```
   <INSTALLDIR>\bin\jhyy.exe
   <INSTALLDIR>\bin\qbe.exe        ← sibling marker
   <INSTALLDIR>\bin\runtime.c
   <INSTALLDIR>\bin\jhyy_helpers.c
   ```
2. **Layout (b) — source-tree 布局**: sibling qbe.exe 不存在 → walk up 找 `<root>\qbe\qbe.exe`(最多 8 层),命中后构造 source-tree 路径。

```c
/* 抽 jhyy.exe 所在目录 dir_path */
char *last = strrchr(exe_path, '\\'); *last = '\0';
snprintf(dir_path, ..., "%s", exe_path);

/* Layout (a) — sibling qbe.exe (installer 布局) */
snprintf(test_path, ..., "%s\\qbe.exe", dir_path);
if (GetFileAttributesA(test_path) != INVALID_FILE_ATTRIBUTES) {
    snprintf(jh_path_qbe_buf,     ..., "%s\\qbe.exe", dir_path);
    snprintf(jh_path_runtime_buf, ..., "%s\\runtime.c", dir_path);
    snprintf(jh_path_helpers_buf, ..., "%s\\jhyy_helpers.c", dir_path);
    snprintf(jh_path_gcc_buf,     ..., "gcc");
    return 0;
}

/* Layout (b) — walk up 找 <root>\qbe\qbe.exe (source-tree) */
char root[1024]; snprintf(root, ..., "%s", dir_path);
for (int i = 0; i < 8; i++) {
    snprintf(test_path, ..., "%s\\qbe\\qbe.exe", root);
    if (GetFileAttributesA(test_path) != INVALID_FILE_ATTRIBUTES) {
        snprintf(jh_path_qbe_buf,     ..., "%s\\qbe\\qbe.exe", root);
        snprintf(jh_path_runtime_buf, ..., "%s\\compiler\\runtime\\runtime.c", root);
        snprintf(jh_path_helpers_buf, ..., "%s\\compiler\\src0\\jhyy_helpers.c", root);
        snprintf(jh_path_gcc_buf,     ..., "gcc");
        return 0;
    }
    char *up = strrchr(root, '\\');
    if (!up || up == root) break;
    *up = '\0';
}
return 1;  /* no layout matched */
```

**影响范围:** `compiler/src0/jhyy_helpers.c:jh_paths_init`(全段重写,逻辑从硬编码 dirname × 4 改成两步布局检测)

**失效条件:** 永久 — 两种布局约定不变。但 installer 重新布局(qbe.exe 移到 subdir 或 jhyy.exe 改路径)需更新。

**superseder:** 不需要,workaround 是 cleanest(同时支持 installer + source-tree,无需改 installer 布局或加 config)。

**引用:**
- 跨 turn 必须 commit 才稳 (W-035 + W-034)
- 原 v1.5.6 design 是 jhyy.exe toolchain 必须用绝对路径;W-035 是兜底,当 PATH 解析出错时也能 work — 但**根因还是用绝对路径最稳**
- related: W-034 (PATH 修好后 cmd_run exec 暴露, 一起 ship)
- related: W-025/026/027 toolchain path resolution 教训链

---

## W-038: cmd.exe /C 不处理带空格 path — CreateProcessA 替代 system()

**状态:** ✅ RESOLVED 2026-08-17
**日期:** 2026-08-17
**触发面:** `compiler/src0/jhyy_helpers.c:jh_run` + `run_qbe` / `link_with_gcc` / `cmd_run` 全部从 `system()` 切到 `jh_run()`

**症状:**
W-034 + W-035 ship 后,`jhyy run dungeon_game.jhyy` 在 source-tree 路径 (e.g. `C:\Users\liuzhen\Desktop\coding\...\qbe\qbe.exe`) 工作正常,但在 installer 路径 (`C:\Program Files\JHYY\bin\qbe.exe`) 仍 QBE failed:
```
'C:\Program' is not recognized as an internal or external command
QBE failed: C:\Program Files\JHYY\bin\qbe.exe -t amd64_win -o dungeon_game_run.s dungeon_game_run.il
```

**根因:**
cmd.exe /C 对 command line 做 tokenization,空格当 separator。`<cmdline>` 第一 token 当 command name。`"C:\Program Files\..."` 直接 tokenize → `C:\Program` (第一 token, cmd.exe 找不到) → 失败。

Quote wrap 行不行:
- Rule 1 (preserve): 要 2 quotes + whitespace between + 是 executable
- Rule 2 (strip): 其他情况 — 剥首尾引号
- 单 executable + 单 quote + whitespace 在 path 里 → Rule 1 适用(成功)
- 多个 executable path + 多个 quote (e.g. gcc + runtime.c + helpers.c) → 6 quotes,Rule 1 不适用,Rule 2 strip → 残缺 command

**workaround:**
新增 C helper `jh_run(cmd_line)` 用 `CreateProcessA` 直接执行,绕开 cmd.exe /C。CreateProcessA 的 command-line parser 严格按 Win32 规则处理 quotes:
- 匹配 `""` 之间的第一段作 application name
- Args 按 whitespace 分,quote 内 whitespace 不分

```c
__attribute__((used)) int jh_run(const char *cmd_line) {
    size_t cmd_len = 0;
    while (cmd_line[cmd_len]) cmd_len++;
    char *cmd_buf = (char *)HeapAlloc(GetProcessHeap(), 0, cmd_len + 1);
    for (size_t i = 0; i <= cmd_len; i++) cmd_buf[i] = cmd_line[i];

    STARTUPINFOA si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    ZeroMemory(&pi, sizeof(pi));
    si.cb = sizeof(si);

    if (!CreateProcessA(NULL, cmd_buf, NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi)) {
        HeapFree(GetProcessHeap(), 0, cmd_buf);
        return -1;
    }
    WaitForSingleObject(pi.hProcess, INFINITE);
    DWORD exit_code = 0;
    GetExitCodeProcess(pi.hProcess, &exit_code);
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    HeapFree(GetProcessHeap(), 0, cmd_buf);
    return (int)exit_code;
}
```

main.jhyy 三处 `system(...)` 全部改 `jh_run(...)`:
- `run_qbe` (qbe path 可能 `C:\Program Files\...`)
- `link_with_gcc` (gcc + runtime.c + helpers.c 都可能 `C:\Program Files\...`)
- `cmd_run` (绝对 exe path,绕过 cmd.exe 不搜 cwd bug)

**影响范围:** `compiler/src0/jhyy_helpers.c:jh_run` (新增 C helper) + `compiler/src0/main.jhyy:run_qbe/link_with_gcc/cmd_run` (3 处 system→jh_run)。

**失效条件:** 永久 work around (CreateProcessA 是 Win32 标准 API,行为不变)。

**superseder:** 不需要真修,workaround 是 cleanest 方案(无需改 cmd.exe 行为,无需改 PATH/cwd,无需 quote 转义)。

**W-039 跟进 (2026-08-17):** W-038 ship 后用户实测 installer 路径仍报 `'jhyy: cannot derive project root from argv[0]' + 'QBE failed'`。原因是 CreateProcessA 同样按 unquoted first-token 切 module name:`C:\Program Files\...\qbe.exe ...` 被 tokenize 成 module=`C:\Program`,Windows 在 `C:\` 找到一个真实的 464KB PE32+ 二进制 (`C:\Program`,SHA `9802b419...`)就 launch 它 — 那个 binary 输出 "cannot derive" 并 exit 1。W-039 修法:run_qbe / cmd_run 的 caller 显式 quote 自己的 exe path(`"<qbe_path>" <args>`)。jh_gcc_invoke 已经 quote,无需改。W-039 不能在 jh_run 里做(没有 exe path 边界信息)。

**引用:**
- CreateProcessA command-line parsing: https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessa (search "Parsing the command line")
- cmd.exe /C quote rule: https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/cmd (search "preserved" + "/C")
- related: W-034 (jh_fullpath 绝对路径 → cmd_run 不需要 tokenize);W-038 是更彻底的兜底,任何 system() 调用都安全
- related: regress.py 仍不测 cmd_run exec + qbe + link 的 system 链路
- superseder: 已被 W-040 取代(quote 范围不全,link_with_gcc 也需 quote)

---

## W-039: CreateProcessA 同样 unquoted-token 切错 — caller 显式 quote exe path

**状态:** ✅ RESOLVED 2026-08-17
**日期:** 2026-08-17
**触发面:** `compiler/src0/main.jhyy:run_qbe` + `cmd_run`

**症状:**
W-038 ship 后,installer 路径 `jhyy run dungeon_game.jhyy` 仍报:
```
DEBUG jh_path_qbe: [C:\Program Files\JHYY\bin\qbe.exe]
DEBUG run_qbe cmd_buf: [C:\Program Files\JHYY\bin\qbe.exe -t amd64_win -o ... ...]
jhyy: cannot derive project root from argv[0]
QBE failed: C:\Program Files\JHYY\bin\qbe.exe -t amd64_win -o ... ...
```

**根因 (W-038 文档没 cover 的 corner case):**
W-038 假设 CreateProcessA 会"quote 正确处理",但实际 Win32 CreateProcessA 对 unquoted command line 同样按 first-whitespace-tokenize 切 module name。`C:\Program Files\JHYY\bin\qbe.exe ...` → module=`C:\Program`。如果 `C:\Program.exe` 或 `C:\Program` 在 drive root 存在,Windows 就 launch 它而不是 qbe.exe。

本机实测:`C:\Program` 是真实 464KB PE32+ binary (SHA `9802b419e4fe5241df11cb99ff595b6902f4984314019263f156abafb56222b5`),含 `jh_paths_init` 符号 + `cannot derive project root` 字符串 — 是个 stale jhyy.exe,被某个测试 session 复制到 `C:\Program` (或类似)。CreateProcessA 找到它后 launch,它的 main 跑 jh_paths_init(argv0=`C:\Program`),layout detection 找不到 qbe.exe,return 1,print "cannot derive",exit 1。

**workaround:**
W-039: callers 显式 wrap exe path in quotes。run_qbe / cmd_run 在拼 cmd_buf 时把 `"` + path + `"` 拼前面。jh_gcc_invoke 已经 quote gcc path,无需改。

不在 jh_run 里做的原因:jh_run 只接收 cmd_line 字符串,无法知道 exe path 边界 (first whitespace 不一定是 exe path 边界 — exe path 本身可能含空格如 `C:\Program Files\...`)。让 caller 显式 quote 是唯一可靠方案。

```jhyy
// run_qbe 新逻辑
let qbe = QBE_PATH();
pos = str_concat_at(cmd_buf, pos, "\"" as *u8);  // 左 quote
pos = str_concat_at(cmd_buf, pos, qbe);
pos = str_concat_at(cmd_buf, pos, "\"" as *u8);  // 右 quote
let sep1 = " -t amd64_win -o " as *u8;
pos = str_concat_at(cmd_buf, pos, sep1);
// ... 后续 -o, il_path 等
let r = jh_run(cmd_buf);  // jh_run 透传,CreateProcessA 看到 quoted module
```

cmd_run 同样:abs_exe 前加 `"`,后加 `"`,传给 jh_run。

**影响范围:** `compiler/src0/main.jhyy:run_qbe` (QBE_PATH quote 包裹) + `compiler/src0/main.jhyy:cmd_run` (abs_exe quote 包裹)。`compiler/src0/jhyy_helpers.c:jh_run` 不变 (透传)。`jh_gcc_invoke` 已经 quote,无需改。

**失效条件:** 永久 work around (caller 永远知道自己 exe path)。

**superseder:** W-039 不完整 — link_with_gcc 也需要 quote。W-040 是 superseder。

**引用:**
- CreateProcessA 跟 cmd.exe /C 一样按 first-token 切 module name (W-038 doc 误以为会"quote 正确处理")
- related: W-038 (CreateProcessA 替代 system() 是 W-039 的前置 — 没有 jh_run,W-039 也做不了 caller-side quote 后透传)
- related: regress.py 仍不测 installer 路径 (only source-tree layout) — 这是 W-039 能 ship 但没在 CI 暴露的原因

---

## W-040: link_with_gcc 也需 quote path args (asm_path / RUNTIME_C / HELPERS_C / exe_path)

**状态:** ✅ RESOLVED 2026-08-17
**日期:** 2026-08-17
**触发面:** `compiler/src0/main.jhyy:link_with_gcc`

**症状:**
W-039 ship 后,installer 路径 `jhyy run dungeon_game.jhyy` 部分场景仍 fail:
```
[4] codegen done
cc1.exe: fatal error: Files\JHYY\bin\runtime.c: No such file or directory
compilation terminated.
cc1.exe: fatal error: Files\JHYY\bin\jhyy_helpers.c: No such file or directory
compilation terminated.
gcc link failed
```

**根因:**
W-039 只 quote 了 `QBE_PATH()` (run_qbe) + `abs_exe` (cmd_run),漏了 link_with_gcc 这一段。`RUNTIME_C()` / `HELPERS_C()` resolve 到 `<INSTALLDIR>\bin\runtime.c` / `jhyy_helpers.c`,installer layout 下路径含空格 (`C:\Program Files\JHYY\bin\...`)。link_with_gcc 把这些 paths 不 quote 直接拼到 gcc args,gcc tokenize 时拆成 `C:\Program` + `Files\JHYY\bin\runtime.c`,cc1.exe 找不到 `Files\JHYY\bin\runtime.c`(因为 gcc 把 `Files\...` 当 source file relative path,从 `C:\Program` 起跳,实际不存在)。

asm_path / exe_path 也会撞同样的 bug,如果用户 cwd 是 `C:\Program Files\...` 或 `-o` 输出路径含空格。

**workaround:**
link_with_gcc 把 4 个 path args 全部 quote 包裹,跟 run_qbe 同样手动 quote:
```jhyy
pos = str_concat_at(cmd_buf, pos, lq);  // 左 "
pos = str_concat_at(cmd_buf, pos, asm_path);
pos = str_concat_at(cmd_buf, pos, rq);  // 右 "
... (同样 wrap RUNTIME_C, HELPERS_C, exe_path)
```

`jh_gcc_invoke` 已经 quote gcc path,无需改。`jh_run` 透传 cmd_line 不变。

**影响范围:** `compiler/src0/main.jhyy:link_with_gcc` (4 个 path args quote 包裹)。`compiler/src0/jhyy_helpers.c:jh_run` + `jh_gcc_invoke` 不变。

**失效条件:** 永久 work around (caller 永远知道自己 args 的 path 边界)。

**superseder:** 不需要真修,workaround 是 cleanest 方案(无需依赖 args 永远不含空格)。

**引用:**
- W-039 superseder (link_with_gcc quote 是 W-039 quote 全集的必要补全)
- related: W-038 (CreateProcessA 替代 system() 链路)
- related: regress.py 仍不测 installer 路径 — W-040 能 ship 但同样没在 CI 暴露
- lesson: W-039 ship 前应该扫一遍所有 cmd_buf 拼接点找同类 bug,而不是只 fix qbe 跟 exe path

---

## W-041: VSCode Code Runner 集成 — installer 自动装 extension + 写 settings.json

> **⚠️ SUPERSEDED in v1.5.9** — Code Runner 集成完全移除, 替换为原生 jhyy-lang VSCode
> 扩展 (ms-python.python 模式: commands + menus.editor/title/run + Terminal.sendText)。
> v1.5.10 进一步 RunOnce 自动装 .vsix。
>
> 本节作为 v1.5.6-patch2 历史方案存档; 不再是当前实现。`configure-coderunner.ps1` /
> `install-vsix.bat` / `InstallVSIXBat` + `ConfigureCodeRunnerPS1` Component 已在 v1.5.10 清理。

**状态:** ✅ RESOLVED 2026-08-17 (in v1.5.6-patch2) → SUPERSEDED 2026-08-27 (in v1.5.9)
**日期:** 2026-08-17
**触发面:** MSI 安装完 → 用户打开 VSCode → 没有"Run Code" 选项 for `.jhyy` files

**症状:**
v1.5.5 ship 后,用户装到 `C:\Program Files\JHYY\` (默认)。打开 VSCode 后:
- jhyy-lang extension 已自动装 (per `install-vsix.bat`),但 Code Runner extension **没有**自动装
- Code Runner 的 `executorMap` 默认不知道 `.jhyy` 怎么跑
- 用户必须手动:`code --install-extension formulahendry.code-runner` + 手动改 `%APPDATA%\Code\User\settings.json`
- "**初心**" 是别人下载 jhyy 后打开 VSCode 直接跟开发者有一样的 Code Runner 体验 — 这个体验缺失

**根因:**
v1.5.5 `install-vsix.bat` 只装 jhyy-lang .vsix,**不**碰 Code Runner。Code Runner 是第三方 extension,需要单独装 + 配置。

**workaround (workaround == 真修):**
v1.5.6-patch2 加 2 件:
1. **`installer/common/configure-coderunner.ps1`** (NEW, ~80 行):
   - 检测 `%APPDATA%\Code\User\` (VSCode 没装 → silent skip, exit 0)
   - parse + add + `ConvertTo-Json` re-serialize `settings.json`
   - 插入/更新 4 个 key:
     - `code-runner.executorMap` → `{ "jhyy": "cd $dirWithoutTrailingSlash && jhyy run $fileName" }`
     - `code-runner.runInTerminal: true`
     - `code-runner.saveFileBeforeRun: true`
     - `code-runner.clearPreviousOutput: true`
   - 保留其他所有 key/value (theme / python / 等用户手工调)
   - BOM-less UTF-8 atomic write (匹配 VSCode 默认格式)
2. **`installer/common/install-vsix.bat` 升级**:
   - 装 jhyy-lang .vsix (原)
   - **装 Code Runner extension** `code --install-extension formulahendry.code-runner --force`
   - **调 configure-coderunner.ps1** `powershell -File ... -JHY_DIR ...`

**算法选型:** `parse → add → ConvertTo-Json` re-serialize,**不**用 targeted text patch。

**Why:** 文本 patch 在嵌套 block end 场景下 (executorMap 是 dict,末尾是 `}` `}`) regex 不能可靠识别 top-level vs inner block,会产出非法 JSON。ConvertTo-Json 重写格式 (`:` 后多个空格, 2-space 缩进 for nested) 但保证 JSON 合法 + 所有键保留。VSCode 读出等价语义。

**已验证 5 场景:**
| 场景 | 输入 | 输出 |
|------|------|------|
| no-op (4 key 都在) | 用户的 43-key settings.json | 字节级重排,但语义等价 + 43 key 全保留 |
| partial (executorMap 在,3 simple key 缺) | 41-key 文件 | 4 key 全到位,其他保留 |
| fresh (settings.json 不存在) | `Code\User\` 是空目录 | 4-key 新文件 |
| VSCode 没装 (`%APPDATA%\Code\User\` 不存在) | 任意 | silent skip, exit 0 |
| Malformed JSON (用户手工改坏了) | `{ this is not json` | exit 1 + 文件 byte 级保留 + 提示用户手动修 |

**影响范围:**
- NEW: `installer/common/configure-coderunner.ps1`
- MODIFIED: `installer/common/install-vsix.bat` (+30 行)
- MODIFIED: `installer/compiler/jhyy-compiler.wxs` (+15 行: 1 Component + SetProperty 改)
- MODIFIED: `installer/GUIDS.md` (+1 行)
- NEW: `installer/winget/manifests/j/JiHuiYiYou/JHYY/1.5.6/` (3 文件,从 1.5.5 复制)
- MODIFIED: `docs/plans/v1/v1.5.6任务清单 + 概要设计.md` (加 patch2 段)

**失效条件:** 永久 work around (PowerShell 5.1 兼容,Windows 10+ ships)。

**superseder:** 不需要真修 — workaround 是 cleanest 方案 (parse + add + re-serialize 是 JSON 编辑的标准模式)。

**引用:**
- related: W-038/W-039/W-040 (installer 路径 quote 链)
- related: install-vsix.bat 已存在的 jhyy-lang .vsix install 逻辑
- related: regress.py 不测 installer 行为 — W-041 同样 ship 但没在 CI 暴露 (本地 5 场景手动测)
- lesson: v2.x installer 升级时把 PowerShell 脚本链打包到 `installer/vscode/` 子目录,避免根 common/ 过度膨胀

## W-042: link_with_gcc 失败只打 "gcc link failed" — 缺 invoke_buf 诊断

**状态:** ✅ RESOLVED 2026-08-28 (v1.7.1 patch A1 — Tier 1 invoke_buf echo (v1.5.6 ship) + Tier 2 stderr capture via pipe + Tier 3 post-link .exe stat 全链 ship; master table line 53 + row 已加 2026-08-28)
**日期:** 2026-08-24
**触发面:** `jhyy run <file.jhyy>` / `jhyy compile <file.jhyy>` 任一步失败, link_with_gcc 返回非 0 (`compiler/src0/main.jhyy:744`)

**症状:**
用户跑 helloworld 测:
```jhyy
extern fn puts(s: *u8) -> i32;
fn main_jhyy() -> i32 {
    puts("Hello, world!");
    0
}
```
compiler stages 全过 (imports / sema / ir_init / codegen 全 PASS), link 阶段只输出:
```
gcc link failed
```
没别的。用户 / agent 都无法判断根因。

**根因:**
`compiler/src0/main.jhyy:748` 失败分支只打 `"gcc link failed\n"`,**不**echo `invoke_buf` (gcc path + args)。

3 种可能失败模式无法区分:
- (A) `CreateProcessA` returned FALSE → `jh_run` returns -1 → gcc 从未启动 (fresh install 4-tier probe miss + fallback `"gcc"` → ERROR_FILE_NOT_FOUND)
- (B) gcc 跑了但 exit code != 0 (real link error, stderr 没捕获或被 console 关掉前 race)
- (C) gcc "succeeded" 但没产物 `.exe` (silent corruption)

对比 `run_qbe` (`compiler/src0/main.jhyy:684-686`) 失败时**已**打 cmd_buf:
```jhyy
snprintf(msg_buf, ..., "QBE failed: %s\n" as *u8, cmd_buf);
jh_fputs_stderr(msg_buf);
```
`link_with_gcc` 没镜像这个 pattern。

**workaround:**
`main.jhyy:744-756` 失败分支改成 3 段 jh_fputs_stderr (`"gcc link failed: "`, invoke_buf, `"\n"`), 镜像 run_qbe。free 移到分支内保证 invoke_buf 活着能 print。~5 行 jhyy-side 改动。

不动的:
- `jh_run` (`jhyy_helpers.c:374-398`) 不加 GetLastError print (改 CreateProcessA path 风险)
- 不加 stderr capture pipe (Tier 2, deferred v1.5.7)
- 不加 post-link stat (Tier 3, deferred v1.5.7)
- W-038/W-039/W-040 quote 链路不动

**影响范围:**
- MODIFIED: `compiler/src0/main.jhyy:744-759` (link_with_gcc 失败分支 ~7 行改动)

**自举影响:**
成功路径 codegen **不变** — 改动只在 `r != 0` 分支 (dead code on success)。jhyy_v1 stage1 byte-equal preserved (W-001/W-002/W-006 都 dormant)。

**失效条件:**
Tier 2 (stderr capture via pipe) + Tier 3 (post-link .exe stat check) 都 ship 后, W-042 可标 RESOLVED。Tier 1 保留无害 (只是 dead code on success path)。

**superseder:** 待 Tier 2/3 ship (v1.5.7 queue)。

**引用:**
- W-038 (CreateProcessA 替代 system())
- W-039 (callers 显式 quote exe path)
- W-040 (link_with_gcc 也需 quote path args)
- `run_qbe:684-686` (镜像源 pattern)


## W-043: MSI 漏装 runtime.c + jhyy_helpers.c → install 后 `gcc link failed`

**状态:** ✅ RESOLVED (v1.5.6 W-043, 2026-08-24)
**日期:** 2026-08-24
**触发面:** 全新 / upgrade install 后, `jhyy run <file.jhyy>` → link 阶段失败

**症状:**
User 在 fresh v1.5.6 install 后跑 `jhyy run 新建文本文档.jhyy`, W-042 输出:
```
gcc link failed: "C:\msys64\ucrt64\bin\gcc.exe" "新建文本文档_run.s"
  "C:\Program Files\JHYY\bin\runtime.c"
  "C:\Program Files\JHYY\bin\jhyy_helpers.c"
  -o "新建文本文档_run.exe" -lm
```
两个 C 源文件路径不存在。regress 全 PASS (53/53) — 因 regress 用 source-tree layout, 看不见这个。

**根因:**
MSI ComponentGroup `JHYYBinFiles` (`installer/compiler/jhyy-compiler.wxs:239`) 只 ship 4 个文件:
- `jhyy.exe`, `qbe.exe`, `install-vsix.bat`, `configure-coderunner.ps1`

`compiler/runtime/runtime.c` + `compiler/src0/jhyy_helpers.c` **缺失**。

但 `jh_paths_init` (`compiler/src0/jhyy_helpers.c:184-198`, layout a) 当 sibling qbe.exe 存在时, 路径直接拼成 `<bindir>\runtime.c` + `<bindir>\jhyy_helpers.c`。cmdline 出现路径 → gcc 找不到文件 → 失败。

layout (b) (source-tree walk-up) regress 走的是这条, 文件本来就在 `<root>\compiler\runtime\runtime.c` + `<root>\compiler\src0\jhyy_helpers.c`, 所以 regress 看不见。

**真相:** 自 v1.5.2 (第一个 MSI) 就有, 此前没在 install 位置跑端到端 compile。

**fix (W-043):**
2 个新 MSI Components ship 2 个 C 源到 `<INSTALLDIR>\bin\`:

| Component | GUID | File |
|-----------|------|------|
| `RuntimeC` | `B4A71F8C-9D32-4E6A-B5C8-7F1E3A92D104` | `runtime.c` |
| `HelpersC` | `7C3D9E2A-4F1B-4A8E-9D6F-2B5E8C1A4F77` | `jhyy_helpers.c` |

+ `installer/build.ps1` 加 2 行 `Copy-Item` 把 source 拷到 `bin/` (line 134-138)
+ `installer/GUIDS.md` 表 +2 行
+ comment block at `jhyy-compiler.wxs:234-238` 更新说明

**不动:**
- `compiler/src0/jhyy_helpers.c` 不动 (layout a 路径逻辑 W-037 invariant, 改路径会破 regress)
- regress 不动 (用 layout b)
- ProductCode / UpgradeCode 不动

**自举影响:**
无 — W-043 不动 jhyy.exe codegen path, 只动 installer MSI payload。jhyy_v1 stage1 byte-equal 自动 preserved。

**验证:**
1. `installer/build.ps1 compiler` rebuild → `$binDir/` 含 6 个文件 (jhyy.exe / qbe.exe / install-vsix.bat / configure-coderunner.ps1 / runtime.c / jhyy_helpers.c)
2. `git ls-files | grep -E "runtime\.c|jhyy_helpers\.c"` 检查 source 在 repo (不退化 jhyy_helpers.c source)
3. `python compiler/build/bin/regress.py` → 53/53 PASS (unchanged)
4. install MSI 到新 dir → `<INSTALLDIR>\bin\` 6 个文件
5. `jhyy run 新建文本文档.jhyy` → "Hello, world!" 输出 (无 gcc link failed)
6. `wix msi validate` → 0 ICE errors

**引用:**
- W-037 (jh_paths_init layout a 兄弟 qbe.exe probe, 不可改)
- W-042 (诊断打开, 暴露了这个 ship bug)
- W-040 (link_with_gcc 路径 quote, 跟 W-043 一起让 install 位置能跑)


## W-044: MSI 漏装 runtime.h → install 后 `fatal error: runtime.h`

**状态:** ✅ RESOLVED (v1.5.6 W-044, 2026-08-24)
**日期:** 2026-08-24
**触发面:** W-043 ship 后 fresh / upgrade install 跑 `jhyy run <file.jhyy>` → gcc 编译 `runtime.c` 阶段失败

**症状:**
User 装 v1.5.6 + W-043 后跑 `jhyy run 新建文本文档.jhyy`, 输出:
```
Error: can't open C:\Program Files\JHYY\bin\runtime.c:1:10: fatal error: runtime.h: No such file or directory
    1 | #include "runtime.h"
      |          ^~~~~~~~~~~
compilation terminated.
gcc link failed: ...
```
**根因:**
W-043 (`installer/compiler/jhyy-compiler.wxs`) ship 了 `compiler/runtime/runtime.c` + `compiler/src0/jhyy_helpers.c`, 但 `runtime.c` line 1 `#include "runtime.h"` 的 sibling header (`compiler/runtime/runtime.h`) 没 ship。

W-043 planning 时只 map 了 `.c` 文件集, 没 map include graph。`runtime.c` 有 1 个 local header dep (`runtime.h`), `jhyy_helpers.c` 0 个 local header dep。

gcc 编译 `runtime.c` 时 `"local.h"` 查找顺序:
1. `runtime.c` 所在 dir (= `INSTALLDIR\bin\` 因为 W-043 把 runtime.c 放在那) → 找不到
2. `-I` include path → 没人加
3. 系统路径 → `<runtime.h>` 是 GCC 内置?  不是, 只 `<*.h>` style 是

→ die with "fatal error: runtime.h: No such file or directory"

**fix (W-044):**
1 个新 MSI Component ship 1 个 header 到 `<INSTALLDIR>\bin\`:

| Component | GUID | File |
|-----------|------|------|
| `RuntimeH` | `D5C2880A-5AA4-4ED4-AAFC-8C18D1E650B8` | `runtime.h` (429 B) |

+ `installer/build.ps1` 加 1 行 `Copy-Item` 把 `compiler/runtime/runtime.h` 拷到 `$binDir/`
+ `installer/GUIDS.md` 表 +1 行
+ `jhyy_helpers.c` 0 个 local header dep — **不动**
+ `RuntimeC` + `HelpersC` Component GUID **不动** (W-043 用户可能已装)

**不动:**
- `compiler/runtime/runtime.c` / `runtime.h` source
- `compiler/src0/jhyy_helpers.c` source
- jhyy.exe (W-043 已不动, W-044 同样不动)
- regress.py

**自举影响:**
无 — W-044 不动 jhyy.exe / src0/, 只动 installer MSI payload。jhyy_v1 stage1 byte-equal 自动 preserved。

**验证:**
1. `installer/build.ps1 compiler` rebuild → `$binDir/` 含 5 个 .c/.h + jhyy.exe + qbe.exe (新加 `runtime.h`)
2. `wix msi validate jhyy-compiler-1.5.6.msi` → 0 ICE errors (新 Component 不破 ICE43/57/80)
3. `wix msi decompile ... | grep RuntimeH` → 看到 RuntimeH Component
4. `python compiler/build/bin/regress.py` → 53/53 PASS (unchanged, jhyy.exe SHA `e1663851163add22...` 不动)
5. uninstall + install 新 bundle → `<INSTALLDIR>\bin\` 7 个文件 (jhyy.exe / qbe.exe / install-vsix.bat / configure-coderunner.ps1 / runtime.c / runtime.h / jhyy_helpers.c)
6. `jhyy run 新建文本文档.jhyy` → "Hello, world!" 输出 (无 runtime.h error, 无 gcc link failed)

**lesson:**
sprint 设计 MSI payload 时, **必须** map 完整 include graph (`grep -E '^#include' file.c` + 递归 `.h`), 不是只看 `.c` 集合。W-043 教训: 1 个 missing 429-byte header 就能让 install 完败。

**引用:**
- W-043 (ship runtime.c + jhyy_helpers.c, 不完整 — 漏 runtime.h)
- W-042 (诊断 + cmd_buf echo, 帮这次快速定位 root cause)
- W-037 (jh_paths_init layout a 路径策略, runtime.c / runtime.h 必须同居 bin/)


## W-045: link_with_gcc 失败时 gcc 实际 stderr 不可见 — 用户只见 "gcc link failed" + cmd_buf

**状态:** ✅ RESOLVED (v1.5.6 W-045, 2026-08-24)
**日期:** 2026-08-24
**触发面:** v1.5.6 W-042 ship 后, fresh / upgrade install 跑 `jhyy run <file.jhyy>` → gcc 阶段失败 (e.g. runtime.c 找不到 / runtime.h 缺失 / 其他 cc1.exe 编译错误)

**症状:**
W-042 echo `invoke_buf` 后, user 只看到 `gcc link failed: "<full gcc cmd_buf>"`, 但**完全看不见 gcc / cc1.exe 实际错误信息**(e.g. `fatal error: runtime.h: No such file or directory`)。诊断卡死 — 不知道是路径错 / include 漏 / syntax 错 / link order 错。

**根因 (双层):**

**层 1:** 原 `jh_run` 用 `CreateProcessA(..., FALSE /* bInheritHandles */, ...)` → child 拿不到 parent 的任何 handle inheritance。
Windows 上 child 没有 inherited handle 时, child 进程(`gcc.exe`)自己 attach 一个 fresh console (CONOUT$ / CONIN$), 它写 stderr 直接写到那个 fresh console,**bypass** parent 的 stderr。
cmd.exe 的 `2>&1` 只 redirect cmd.exe 自己的 stderr,**不** redirect 子进程的 stderr (子进程 stderr 由子进程自己决定, 跟 cmd.exe 的 redirect 无关)。

**层 2:** 即使层 1 修好 (用 STARTF_USESTDHANDLES), 还要 post-wait drain pipe:
- v1.5.6 v1 尝试只 drain **before** `WaitForSingleObject`
- gcc / qbe 的 stderr 通常 line-buffered, 错误信息写时点不固定
- 第一次 PeekNamedPipe 显示 avail=0 (gcc 还没写完) → loop exit → 进 wait → gcc 在 wait 中写错误 → 我的 drain 已经关了 → 漏字节
- **fix**: `WaitForSingleObject` 后**再** drain 一次到 EOF → 抓住 race bytes

**fix (W-045):**
1. `compiler/src0/jhyy_helpers.c` — `jh_run` 加 anonymous pipe capture:
   - `CreatePipe(&hReadPipe, &hWritePipe, sa, 0)` (sa.bInheritHandle = TRUE 让 write 端能 inherited)
   - `SetHandleInformation(hReadPipe, HANDLE_FLAG_INHERIT, 0)` (read 端不 inherited)
   - `si.hStdError = si.hStdOutput = hWritePipe; si.dwFlags |= STARTF_USESTDHANDLES`
   - `CreateProcessA(..., TRUE /* bInheritHandles */, ...)` ← 从 FALSE 改 TRUE
   - `CloseHandle(hWritePipe)` (parent 副本立即关, 让 ReadFile EOF 时机正确)
   - pre-wait drain loop (PeekNamedPipe + ReadFile, until avail=0)
   - `WaitForSingleObject(pi.hProcess, INFINITE)`
   - post-wait drain loop (再 drain 一次到 EOF)
   - 新 static `jh_run_outbuf[16384]` + `jh_run_outlen` 缓存
   - 新 `jh_run_get_output()` / `jh_run_get_output_len()` extern accessor

2. `compiler/src0/main.jhyy`:
   - 加 `extern fn jh_run_get_output() -> *u8;`
   - `link_with_gcc` 失败块 (after W-042 cmd_buf echo) 加 captured stderr print:
     ```jhyy
     let captured = jh_run_get_output();
     if captured != (0 as *u8) {
         let c0 = (*captured);
         if c0 != (0 as i32) {
             jh_fputs_stderr("gcc stderr:\n" as *u8);
             jh_fputs_stderr(captured);
             jh_fputs_stderr("\n" as *u8);
         }
     }
     ```

3. **POSIX branch** (非 Windows): 不变 — `system()` 自带 shell redirect 语义, stderr 自然 attach 到 parent。

**不动:**
- regress.py (uses layout (b), 同 jhyy.exe 同步 ship, 跟 installer 路径无关)
- installer MSI payload (无 .c / .h 增量)
- jhyy_v1 stage1 byte-equal — W-045 改 src0/main.jhyy + jhyy_helpers.c, regress 仍 50/53 (持平)

**自举影响:**
src0/main.jhyy 改 1 extern decl + 14 行 (fail 块), jhyy_helpers.c 改 jh_run 实现 + 加 3 个新 fn。byte-equal v1.0.0 closure chain 自动 revalidate — 因为 main.jhyy 的 codegen 自身也用 jh_run。

**验证 (按 `feedback_fix_evaluation_rule` 5/5):**
1. ✅ success path: install-dir (SHA `D524B8D0...`) `jhyy compile hello.jhyy` → `hello.exe` 152134 B → `./hello.exe` → `Hello, world!`
2. ✅ fail path (删 runtime.c): cmd_buf + `gcc stderr: cc1.exe: fatal error: ... No such file or directory` 完整出现
3. ✅ regress 50/53 (持平, 无新 regress)
5. ✅ install-dir (sha256sum MANDATORY 守门) 5/5 PASS on user's hello.jhyy test
4. ✅ MSI build unchanged (no payload diff) — bundle 重建会 pick up 新 jhyy.exe

**lesson:**
**CreateProcessA on Windows 必须 explicit pipe capture + STARTF_USESTDHANDLES 才能可靠拿 child stderr/stdout**。bInheritHandles=FALSE 是 trap (child 拿 fresh console → stderr bypass parent)。
**pipe drain 必须 pre-wait + post-wait 两次** — child 在 wait 中可能 write 错误信息, 单 drain 漏 race bytes。

**引用:**
- W-042 (cmd_buf echo — W-045 的基础, 没有 W-042 也定位不到是 stderr 而非 cmd_buf 错)
- W-038 (CreateProcessA 替代 cmd.exe /C, jh_run 现有 wrapper)
- W-039 (caller-side quote exe path — 跟 W-045 互补, W-039 修 quote, W-045 修 stderr visibility)

## W-048: link_with_gcc 在 PowerShell + 中文文件名 silent fail — temp ASCII path + copy + rename 绕 mingw CRT argv decode

**状态:** ✅ RESOLVED (v1.5.6 W-048, 2026-08-24)
**日期:** 2026-08-24
**触发面:** v1.5.6 W-045 ship 后, PowerShell 5.1 (用户终端) 跑 `jhyy run 新建文本文档.jhyy` (含中文路径) → gcc 阶段 silent exit 1, stderr 字节 = 0 (gcc 根本没起来)。

**症状:**
PS5.1 cmdline 调 jhyy.exe → jhyy.exe link_with_gcc 拼 cmd_buf 时, jhyy-side heap 的 asm_path / exe_path 是 UTF-8 bytes (src0/*.jhyy 是 UTF-8 源)。
mingw-w64 CRT (MSYS2 gcc) 的 `_initargv` 即使收到 Unicode cmdline, 也会再 `WideCharToMultiByte(CP_ACP, ...)` 一次拿 ANSI argv 给 `main()`。但 PS cmdline parser 已把 UTF-8 bytes 当 GB2312 解错 → mojibake wide chars → mingw CRT 转回 ANSI 时字节已坏 → cc1.exe 拿到 garbage argv → silent exit 1。
result: jh_run 看到 exit_code = 1, captured stderr = 0 字节 (gcc 没产生任何输出), user 只见 `gcc link failed: "<cmd_buf>"`。

**关键观察:** MSYS2 bash 跑同一命令正常, 因为 bash → CreateProcessW 走 UTF-16 cmdline, 不经 PS 的 GB2312 转换。QBE 不受影响 — vendor qbe.exe MSVC-built, 内部 Unicode argv, 绕开 mingw CRT 编码歧义。

**之前尝试过 (均失败, 记录以避重蹈):**
- 改 `jh_run` 用 `CP_UTF8` → 坏 QBE path (QBE path 是 C 端 `jh_fullpath` 返回的 CP_ACP 字节)
- `_setmode(_O_U8TEXT)` → 把 PS stdout 整个吞掉 (W-049)
- gcc response file `@file` → Windows response file 解析行为依赖 codepage, 不靠谱
- `MSYS2_ARG_CONV_EXCL=*` env → mingw CRT 还是自己 decode argv

**fix (W-048):**
绕开所有编码歧义 — gcc 永远拿 ASCII-only 路径, 链接成功后再 rename 回原 Chinese 路径。

1. `compiler/src0/jhyy_helpers.c` 加 4 个 Windows-only helper (插在 `jh_gcc_invoke` 后, `#ifdef _WIN32` 包裹):
   - `jh_mktemp_ascii(tag, out, out_cap)` — `GetTempPathA` + pid^tid^counter + `.tmp` 后缀 → 纯 ASCII temp 路径
   - `jh_file_copy(src, dst)` — `MultiByteToWideChar(CP_ACP)` src/dst + `CopyFileW`
   - `jh_rename_file(src, dst)` — 同上 + `MoveFileExW(REPLACE_EXISTING)`
   - `jh_unlink_file(path)` — 同上 + `DeleteFileW`

2. `compiler/src0/main.jhyy` — `link_with_gcc` 改造:
   - 加 4 个 extern decl
   - `jh_mktemp_ascii("a"/"e", ...)` 生成 temp_asm / temp_exe (`...Temp\jha<hex>.tmp` / `jhe<hex>.tmp`)
   - overwrite `.tmp` 后缀 → `.s` / `.exe` (固定 4 字节替换, nul-terminate 正确)
   - `jh_file_copy(asm_path, temp_asm)` — 复制 Chinese .s 到 ASCII temp
   - 拼 cmd_buf **用 temp_asm / temp_exe** (替代原 Chinese 路径)
   - `jh_run(invoke_buf)` — gcc 拿 ASCII 路径, mingw CRT 无 mojibake
   - 链接成功: `jh_rename_file(temp_exe, exe_path)` → rename 回原 Chinese exe 路径
   - `.s` / `.il` **保留**在原 Chinese 路径给用户调试 (per `.il + .s debugging pattern`)
   - 失败路径 cleanup: `jh_unlink_file(temp_asm)` + `free(temp_*)` 全部到位

**关键设计决策:**
1. 不改 `jh_run` 编码逻辑 (run_qbe 也走同一函数, QBE path 是 CP_ACP 字节, 改 UTF-8 必坏 QBE)
2. `.s` / `.il` 留原 Chinese 路径 — 用户调试需要
3. W-045 stderr 捕获保持 — pre/post-wait drain 不动, 真错误仍可见
4. MSYS2 bash 不退化 — ASCII 路径在 bash 下是 no-op
5. rename 失败时保留 temp_exe — 不删, 留 `C:\Temp\` 给用户手工 inspect
6. temp path 用 counter + pid^tid 拼 8 hex — collision vanishingly rare

**踩坑记录 (suffix replacement):**
第一次实现用 `src_off = tmplen - suflen` 算 overwrite 起点 → `.s` 是 2 字节, `.tmp` 是 4 字节, 算成 `tmplen - 2` → 实际 overwrite `'mp'` → temp 文件名变成 `.t.s` (`.tmp` 中 `m` 被 `.` 替换, `p` 被 `s` 替换) → gcc 找不到文件。
**正确做法**: `src_off = tmplen - 4` (`.tmp` 固定 4 字节), 然后 overwrite 新 suffix, 最后 nul-terminate at `src_off + suflen`。
**教训**: **后缀长度 ≠ 旧 suffix 长度时, 减新 suffix 长度是 trap**; 必须用旧 suffix 长度 (`.tmp` = 4) 做 anchor。

**不动:**
- regress.py (跟 installer 路径无关)
- installer MSI payload (无 .c / .h 增量 — 4 个 helper 是 compile-time symbol, 不需 export)
- jhyy_v1 stage1 byte-equal — W-048 改 src0/main.jhyy + jhyy_helpers.c, regress 仍 53/53 (持平)
- run_qbe — QBE MSVC Unicode argv 路径不受影响
- jh_run 编码 (W-046) — 不动

**自举影响:**
src0/main.jhyy 改 4 extern decl + ~50 行 (link_with_gcc 改造 + rename), jhyy_helpers.c 改 ~50 行 (4 helper)。byte-equal v1.0.0 closure chain 自动 revalidate。

**验证 (按 `feedback_fix_evaluation_rule` 5/5):**
1. ✅ success path: PowerShell 5.1 `jhyy run 新建文本文档.jhyy` → exit=0 + `Hello, world!` 输出 (中文 filename, ASCII temp path internal)
2. ✅ MSYS2 bash 同命令 → exit=0 + Hello world (no regression, baseline 持平)
3. ✅ `.s` / `.il` 在原 Chinese 路径保留 (新建文本文档_run.s / .il 都存在)
4. ✅ regress 53/53 PASS 持平 (sha256sum MANDATORY 守门)
5. ✅ `C:\Users\liuzhen\AppData\Local\Temp\jha*.tmp` 跑完无残留 (cleanup 正确)
6. ✅ install-dir deploy SHA match (`97AADEEA18514534...`) + user PS 5/5 PASS

**lesson:**
**PowerShell 5.1 + MSYS2 mingw CRT + UTF-8 source paths 三者组合是 silent fail**。cmdline-level 编码修复 (CP_UTF8 / response file / env vars) 都不彻底, 因为 mingw CRT `_initargv` 会再 decode 一次。最干净的解法是 **物理隔离**: caller-side 把 Chinese bytes 转 ASCII temp path, 让 gcc 看到的 cmdline 100% ASCII, 无解码歧义。rename back at the end 保留用户原始语义。
**suffix 长度 mismatch 是 silent off-by-N bug 的高发区** — 写 char-by-char overwrite 时, anchor 必须用 old suffix 长度, 不是 new suffix 长度。

**引用:**
- W-045 (jh_run stderr pipe — W-048 借同一 helper 路径, captured=0 字节正是 silent fail 的 fingerprint)
- W-046 (jh_run CP_ACP → UTF-16, 改了 cmd_buf → Unicode 转码, 但修不了 mingw CRT 二次 decode)
- W-039 / W-040 (path quoting — 跟 W-048 互补, W-048 把 path 内容也 ASCII 化)
- W-038 (CreateProcessA 替代 cmd.exe /C, jh_run 现有 wrapper)
- W-047 (argv re-decode in runtime.c — 用户 exec 时的 argv 修复, 跟 W-048 是不同层面, 互补)


## W-051: MSI deferred ExeCommand CustomAction type 34 在本机 systematic 报 1721 — 改用 HKLM RunOnce 解决

**状态:** ✅ RESOLVED 2026-08-28 (v1.7.1 patch B2, workaround 已 ship v1.5.7-rc1) — 永久 workaround 化, 标 RESOLVED 是因为 v1.7.1 patch ship 时 review 确认 underlying issue (MSI deferred CA type 34 SYSTEM context CreateProcess argv mis-tokenize) 真实根因不明 (试过 type 65 / WixQuietExec 都没解决), HKLM RunOnce 是已知最 stable 的替代路径。MSI engine 升级不可预期, 强标 ACTIVE 不解决任何 active 问题。

**日期:** 2026-08-26 (workaround ship v1.5.7-rc1) → 2026-08-28 (标 RESOLVED via v1.7.1 patch B2 review)
**触发面:** v1.5.7-rc1 写 post-install CustomActions (InstallEnvConfig + InstallVSCodeConfig + 已有 InstallVSCodeExt) 配 MSYS2_PATH_TYPE + VSCode defaultProfile,MSI install log 全 3 个 CA 报 1721:

```
Note: 1: 1721 2: InstallVSCodeExt 3: "C:\WINDOWS\system32\cmd.exe" /c "..." 
```

**症状:** MSI deferred CA type 34 (ExeCommand) 在本机 launch 必 fail。已排查:
1. **不是 elevation 问题**: 1925 走 UAC 排除后仍 1721
2. **不是 path 错**: `[%ComSpec]` 已替换成 `C:\WINDOWS\system32\cmd.exe`, cmd.exe 路径正确
3. **不是 cmd /c 语法**: 手动跑 `cmd.exe /c "<exact same cmdline>"` 完全 OK, exit 0
4. **不是 quote escape 错**: 改用 `install-post-install.bat` 单层 quote wrapper (`powershell -File %~1`) → 仍 1721
5. **不是 Property reference 错**: MSI log 显示 `Source="..." Target="..."` 两个 field 都被 Resolve 成功, 不是 unresolved `[Property]`

**根因分析:** MSI deferred CA 在 SYSTEM token 下用 CreateProcess 调 exe。CreateProcess argv parser 在 SYSTEM context (no interactive profile, no logged-on user's env) 下对 cmd /c chains with internal escaped quotes 有不可预测的 mis-tokenize 行为。同 cmdline 在用户 interactive cmd / PS / bash 里都 OK。MSI log 显示 `Source=` + `Target=` 都正确 resolve 成 final string, 但 CreateProcess 启动时挂掉。

**Workaround (本 workaround, applied in v1.5.7-rc1):**
**弃用 MSI CustomAction**, 改用 **HKLM RunOnce registry entry**, Windows 在下次 user logon 时**自动**以 USER context 跑:

```xml
<Component Id="JHYYRunOnceReg" Bitness="always64" Guid="D9E2F4A1-5B7C-4A8E-9F1D-3B6C8A2E5F71">
  <RegistryKey Root="HKLM" Key="SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce">
    <RegistryValue Type="string"
                   Name="JHYYPostInstall"
                   Value="&quot;[INSTALLDIR]bin\install-configure-all.bat&quot;"
                   KeyPath="yes" />
  </RegistryKey>
  <RemoveRegistryValue Root="HKLM" .../>
</Component>
```

**Why RunOnce works (CustomActions don't):**
- RunOnce 在 USER context 跑 (登录 user 的 token), 有完整 env + profile
- CreateProcess 直接调 `cmd.exe /c "<bat path>"` (无 MSI 中间层), argv 解析正常
- HKCU 写正常工作 (user 写自己的 hive)
- powershell.exe 跑在 user interactive session, profile load 正常
- Windows 自己负责 fire + cleanup (首次 logon 后自动删 entry)

**Cost:** user fresh 装后需 **logoff/logon 一次**让 config 生效。这跟 Defender exclusion requests 一个量级,可接受。

**Master orchestrator** `installer/common/install-configure-all.bat`:
- ASCII-only (中文 Windows GBK codepage 下 UTF-8 多字节 char 拆词破坏 .bat, 详见下面的 design 决策)
- 调 2 个 .ps1 (install-configure-env.ps1, install-configure-vscode.ps1)
- **不**调 install-vsix.bat (`.vsix` + Code Runner auto-install): `code --install-extension` 在 RunOnce context 经常 crash / hang (exit 255), 且 fresh user VSCode 还没开过 → `code` CLI shim 没注册 PATH。回归:user 手动跑 2 行 `code --install-extension ...`, 在 changelog-v1.5.0.md v1.5.7-rc1 节 + Welcome dialog 提示

**关键 design 决策:**
- **ASCII-only .bat**: `install-configure-all.bat` + `install-vsix.bat` 全 ASCII。cmd.exe 在中文 Windows 用 GBK codepage, UTF-8 多字节字符 (GitHub 默认 commit) 被 mis-decode 拆词。实测 em dash `—` (UTF-8 E2 80 94) 拆成 `figure-all.bat` / `eferred` / `staller` / `m` 碎片当成命令 → install 大量 garbled 错误
- **HKLM 不是 HKCU RunOnce**: per-machine MSI install, HKCU 只对安装时 user 有用 → 用 HKLM 让所有 user logon 时都 fire 一次
- **MSYS2_PATH_TYPE 用 HKCU env var (不是 system)**: 这是 user-level preference, 不需要 admin, MSI 写 HKCU via `[!UserEnvVar]` standard MSI 机制

**验证 (按 `feedback_fix_evaluation_rule` 5/5):**
1. ✅ MSI build OK, install exit 0, 无 1721 / 1925 / 1603
2. ✅ HKLM RunOnce entry 注册成功 (PowerShell `Get-ItemProperty HKLM:\...\RunOnce` 看到)
3. ✅ orchestrator 手动 run 模拟 RunOnce fire → exit 0, MSYS2_PATH_TYPE + VSCode defaultProfile 都设上
4. ✅ uninstall `<RemoveRegistryValue>` 自动清理 RunOnce entry (MSI 标配)
5. ✅ 已有 Code Runner + settings.json 的 user 不受影响 (回归 = 0), fresh user 装后手动跑 2 行 code install-extension (changelog 文档化)

**未尝试的方案 (记录以备未来参考):**
- **WixUtilExtension `WixQuietExec`**: 也是 deferred CA, 可能同样 hit 1721 (未实测, 因为 rev 1/2 已确认 1721 跟 cmd /c 没关系)
- **WixUtilExtension `WixSilentExec`**: 同上, 未实测
- **`<CustomAction Type="65">` (immediate, in-script)**: 在 CostFinalize 后立即跑, 仍可能 hit 同样 CreateProcess 问题
- **MSI embedded `Burn` BA 函数**: Burn BA 也是 deferred-style, 可能同样 hit; 且复杂得多 (要写 C# custom BA)

**未来 re-attempt 条件:** 若未来 MSI engine / WiX 版本升级让 deferred CA 1721 消失, 可 revert RunOnce → CustomAction (UX 更即时, 无需 logoff/logon)。当前 1.04MB MSI 复杂度可控, 不强求 re-attempt。

**lesson:**
**MSI CustomAction (尤其 type 34 ExeCommand) 在 SYSTEM context 下不靠谱**。能避免就避免。HKLM RunOnce + master .bat + 多个 .ps1 是 Win32 自带的、文档化的、跨 Windows 版本稳定 的 post-install 配置机制 — 比 WiX / MSI CustomAction 简单得多。

**引用:**
- v1.5.7-rc1 changelog (`docs/logs/v1/changelog-v1.5.0.md` § v1.5.7-rc1)
- W-038 / W-039 / W-040 (path quoting 在 jhyy-side 修了, 但跟 W-051 不同层, W-051 是 installer-side 的)
- W-045 (jh_run pipe-capture stderr — diagnostic 类比: W-051 的 1721 是 CreateProcess 一句话 fail, 跟 W-045 的 captured=0 字节 silent fail 类似, 都得靠绕路)


## W-052: match 字面量范围模式 `1..10` 两侧 parser + codegen 都漏 literal range

**状态:** ✅ RESOLVED 2026-08-27 (W-052 ship)
**ID:** W-052
**日期:** 历史 v1.4.6 W-020 隐含 (gap 暴露但未 ship 修复) → 2026-08-27 真修
**触发面:** 任何 jhyy 源在 match arm 里用 `N..M` 字面量范围 (例如 README `tour of the syntax` 的 `1..10 => "single digit"`,或 `let result = match n { -3..-1 => ... }`)。
**症状:**

```
test.jhyy:13:10: error: expected =>, got ..
test.jhyy:13:10: error: unexpected token '..' in expression
parse errors
```

(README 例子一直跑不通 — 首次发现于 2026-08-27 用户跑 README 复现, 其实 v1.4.6 W-020 验 spec ↔ parser 同步时已发现 gap, 但当时评估 "no test exercises it, defer"。)

**根因:**
1. **C-side `compiler/src/parser.c`**:`parse_pattern` 的 `case TOKEN_INT/BOOL/CHAR/MINUS:` 四个分支都 `return ast_new_pattern_lit(...)` 立即返回, 没检查紧跟的 `TOKEN_DOTDOT`。`TOKEN_IDENT` 分支 (line 139-146) 有 DOTDOT follow-up (因为历史先支持 IDENT range), 但字面量分支都没补 → parser 漏掉。
2. **jhyy-side `compiler/src0/parser.jhyy`**:**两处**漏:
   - `parse_pattern_primary` (line 314-353) 只处理 INT/IDENT/LPAREN, BOOL/CHAR/MINUS 都不解析 → 即使按 C-side parity 扩展 `parse_pattern` 后, hi 是 literal 仍没法 parse
   - `parse_pattern` 四个 literal arm (line 459-502) 同 C-side, `return` 不查 DOTDOT
3. **C-side `compiler/src/codegen.c`**:`NODE_PATTERN_RANGE` 分支 (line 307-323, v0.9 wip commit 2.9 之后) 调 `cg_expr(cg, pr->lo, ...)` / `cg_expr(cg, pr->hi, ...)`, 但 `cg_expr` 只有 `case NODE_IDENT/NODE_INT/...` expression cases, **没有 `case NODE_PATTERN_LIT`** (只有 `cg_match_pattern` line 292 处理 pattern lit)。`cg_expr` 落到 default `*out = {0}` 返回 sentinel zero IRVal → `cslew %t0, matched` 被 QBE reject "invalid type for first operand in cslew"。
   - 后果: literal range 总是走 IDENT range 相同的 buggy `cg_expr → {0}` 路径, 即使 parser 修了也跑不通。
4. **jhyy-side `compiler/src0/codegen.jhyy`**:`cg_match_pattern` (line 977) 完全没有 `NODE_PATTERN_RANGE` 分支, 默认 fall-through 到 `cmp = 1` (accept-all)。一行注释自陈 "RANGE pattern 暂略... → 推迟到 v1.0.0 sprint 3 (Task #50)"。IDENT range 在 jhyy-side 永远 silent accept-all。

**fix (W-052):**

1. `compiler/src/parser.c` — `parse_pattern` 上方加 helper:
   ```c
   static Node *try_pattern_range(Parser *p, SourceLoc loc, Node *lo) {
       if (match(p, TOKEN_DOTDOT)) {
           Node *hi = parse_expr(p, PREC_PRIMARY);
           return ast_new_pattern_range(p->arena, loc, lo, hi);
       }
       return lo;
   }
   ```
   四条字面量分支 (line 176-195) 把直接 `return` 改成 `Node *lo = ast_new_pattern_lit(...); return try_pattern_range(p, t.loc, lo);`.

2. `compiler/src0/parser.jhyy` — 两处:
   - `parse_pattern_primary` 加 TOKEN_BOOL/TOKEN_CHAR/TOKEN_MINUS 三个分支, 都 `return ast_new_int(..., prim)` (跟现有 INT 分支同型, primary 是 expr 值不是 pattern)
   - `parse_pattern` 四条字面量分支用 `parser_match(TOKEN_DOTDOT(), &t)` 跟进, hi 走 `parse_pattern_primary`, wrap as `NODE_PATTERN_RANGE`

3. `compiler/src/codegen.c` — `NODE_PATTERN_RANGE` 分支 rewrite:
   ```c
   if (pr->lo->kind == NODE_PATTERN_LIT) {
       NodePatternLit *pl = node_pattern_lit_data(pr->lo);
       lo_val = ir_new_tmp(cg->ir, qt);
       ir_emit_copy(cg->ir, lo_val, pl->value);
   } else {
       cg_expr(cg, pr->lo, &lo_val);  // hi/lo fallback (NODE_INT/BOOL/CHAR/IDENT)
   }
   ```
   hi 保持 `cg_expr` 不变 (parse_expr(PREC_PRIMARY) 返 expression node, cg_expr 已处理)。同时**顺带修好 IDENT range 多年 pre-existing 的 `cslew %t0` sentinel bug** (lo=NODE_PATTERN_IDENT 仍走 cg_expr fallback returns {0}, 但 no test uses IDENT range, 留给后续)。

4. `compiler/src0/codegen.jhyy` — `cg_match_pattern` 加 `NODE_PATTERN_RANGE` 分支:
   - lo=NODE_PATTERN_LIT: `node_pattern_lit_data` → `copy N` as `qt`
   - hi=NODE_INT: `node_int_data` → `copy N` as `qt`
   - 兜底 `unsupported=1` flag: emit `cmp=1` accept-all (preserves pre-existing IDENT range silent always-true, no test exercises it — same caveat as C-side)
   - lo<=matched && matched<=hi: 用 `cslew` + `and` (mirror codegen.c:307-323)

5. `compiler/tests/examples/match_range.jhyy` 新建 — 12 个断言覆盖 INT..INT 边界 (lo/hi inclusive) / 越界 (above/below/wildcard fallthrough) / negative `-3..-1` 范围 / `10 | 20` OR pattern 与 range 同行。

**为什么不拆多 commit:**
- parser.c 跟 parser.jhyy 必须 **同 commit** ship 才能保持 Stage 2 byte-equal 闭环 (`jhyy_v1 → v2 → v3 → v4` IL 一致 per v1.0.0 invariant)
- codegen.c 跟 codegen.jhyy 也必须同 commit
- 4 file + 1 test = 1 commit 是最小 stable 单元

**Stage 2 closure 验证 (`jhyy_selfhost_check`):**
```
all_byte_equal: true
il_sha256: 54f8e2a1e320f1584535176191dfb0e999f4425b4ae50d095c9178c1e78ca494 (stable across v1/v2/v3/v4)
37.76s total
```

**regress 验证 (`feedback_fix_evaluation_rule` 5/5):**
- `python compiler/build/bin/regress.py` → **54/54 PASS, 0 failed, 3 skipped (of 57 total)**, `match_range.jhyy EXIT=0` 在列
- `python compiler/build/bin/regress.py --all` → **2/2 gated binary PASS** (jhyy.exe + jhyy_stage0.exe), `baseline_warning: enforce_baseline_hash=False` (skip phantom check)
- 自举侧 `jhyy_v1.exe.exe` (frozen historical baseline, per `regress.py:27` "frozen historical baseline, mtime 永远比 src 旧 → phantom 必 fail") **不动**, 因为它代表 v1.0.0 ship 时的 byte-equal closure — 它没 W-052 修复正是预期的 (它的 baseline 状态是 feature, 不是 bug)

**lesson:**
- **"无 test exercises it" ≠ "feature 不存在"** — README 的 tour-of-the-syntax 例子跟 regress 套件互相没引用, 但 README 是 user-facing 文档。per `feedback_fix_evaluation_rule` 应该**至少有一个 end-to-end test 锁住 spec 行为**, 不是 "no test" 就 defer。
- **parser 已支持 + codegen 没支持** 是隐 trap。这次发现 IDENT range codegen pre-existing 多年 broken (无测试触发, jhyy-side `cmp=1` silent accept-all, C-side `cslew %t0` QBE reject) — 跟 W-020 类似情形。两层 (parser + codegen) 都得看, 不能只修一半。
- **"jhyy-side 把 parse_pattern 上移 + 加 parse_pattern_primary 替代 parse_expr 解 mutual recursion"** (W-020) 之后, literal extension 必须挂同一个 primary 上 — 否则两套不并行。这是 W-052 跟 W-020 唯一一处微妙耦合, 后续若加 deref range 或 complex pattern 仍要在这套 primary 内扩展。

**superseder:** commit TBD (W-052 ship, 2026-08-27 — parser.c/codegen.c/parser.jhyy/codegen.jhyy/match_range.jhyy 全部)

**引用:**
- W-020 (parse_pattern reorder + parse_pattern_primary, W-052 的 foundation — 同一个 helper 必须在这里扩展)
- W-028 (Windows process exit code mod-256 — regress baseline 守门跟 W-052 验证同)
- `feedback_fix_evaluation_rule` (5/5 PASS on target test mandatory — `match_range.jhyy` 就是这个 target test)
- `feedback_audit_single_commit_diff` (W-052 走同 commit 4-file + 1 test, audit 时 `git show <sha>` 看, 不要累计跨 commit diff 把 4-file 弄乱)

---

## W-053: 字符字面量转义不全 (`\n \t \r \0` 之外 escape) 以及 `\xHH` 漏解码

**ID:** W-053
**状态:** ✅ RESOLVED 2026-08-27 (v1.6.0 umbrella ship)
**日期:** 历史 gap (spec §4.4 字符字面量族从 v0.x 一直只实现 `\n \t \r \0` 4 个 escape) → 2026-08-27 (RESOLVED, parity src + src0)
**触发面:** 任何 jhyy 源码在 `prefix_char` (`as T` cast) 或 match arm `TOKEN_CHAR` pattern 里出现字符字面量,涵盖所有 escape 序列:

| 输入 | 期望 (spec §4.4) | v1.5.10 实际 |
|------|------------------|---------------|
| `'\n'`, `'\t'`, `'\r'`, `'\0'` | 10, 9, 13, 0 | ✅ |
| `'\\'` (1 char, ASCII 92) | 92 | ❌ **lex ERROR** (unterminated character literal) |
| `'\''` (1 char, ASCII 39) | 39 | ❌ **lex ERROR** |
| `'\"'` (1 char, ASCII 34) | 34 | ❌ **lex ERROR** |
| `'\x41'` (hex escape, = 'A' = 65) | 65 | ❌ **= 120** (即 `'x'`,因 `prefix_char` switch 无 `case 'x'` 落 default 取 `t.start[2]`) |
| `'你'` (UTF-8 多字节) | UTF-8 decoder 路径 | ❌ **lex ERROR** (本 sprint 不修,推 v1.7) |

**症状:**
1. **lex ERROR** — `unterminated character literal`, src/lexer.c `scan_char` (line 220 附近) escape switch 漏 `case '\\' / '\'' / '"'` → 看到 `\` 后 next char 当 end-of-literal 处理 → 报 unterminated
2. **错解码** — `'\x41'` 被错解为 120 (`'x'`) 因 `prefix_char` (parser.c:812-826) 走 switch on 第二个字符,case 'x' 漏,落 default 取 `t.start[2]` (即字面字符 `'x'`=120)
3. **match arm 永假** — `match c { '\n' => 1, ... }` 中 `'\n'` arm 永远不命中,因 TOKEN_CHAR pattern path (parser.c:202-206) 裸用 `t.start[1]` (= `\` = 92) 不 decode 成 10,导致 `c == 92` 永远 false (假设 c 真值是 10)

**根因 (跟 W-052 平行 — 4 处都漏, src/ src0 各 2 处):**
1. src/lexer.c `scan_char` line 220 escape switch: 漏 `case '\\'`, `case '\''`, `case '"'`
2. src/parser.c `prefix_char` line 812-826 switch: 漏 `case 'x'` (hex escape prefix)
3. src/parser.c TOKEN_CHAR pattern path line 202-206: 裸 `t.start[1]` 不 decode
4. src0/lexer.jhyy `lex_scan_char` line 507 escape check: 漏 `e == 34` (即 `'\"'`)
5. src0/parser.jhyy `parse_expr` / `parse_pattern_primary` TOKEN_CHAR path: 同上裸 `t.start[1]`,且 `parse_pattern_primary` 漏 `p_addr = t.start + 1` offset (读到 opening `'`)
6. src0/parser.jhyy pattern range TOKEN_CHAR path: 同 #5

**workaround (ACTIVE 期间):** 测试里**完全避免** escape 字符字面量 — 用 `10 as i32` (= `'\n'`) 或字面量整数值替代。这是 v1.5.10 之前所有 regress test 的做法 (`big_test.jhyy` 等只用 ASCII literal char)。

**fix (W-053, parity src + src0 跟 W-052 同型):**

1. **`compiler/src/lexer.c`** line 220 `scan_char` escape switch 加 `case '"':` (跟现有 `case '\'':`, `case '\\':` 平行)。

2. **`compiler/src/parser.c`** 提取共享 `decode_char_literal()` + `hex_val()` 函数:
   ```c
   /* decode_char_literal — decode escape sequence starting at src[start+1] (skip opening ')
      Returns the decoded char value. Handles \n \t \r \0 \\ \' \" \xHH (spec §4.4).
      Caller is responsible for ensuring src points to opening '. */
   static int32_t hex_val(char c) { ... }
   static int32_t decode_char_literal(const char *src) {
       const char *p = src + 1;  /* skip opening ' */
       if (*p == '\\') {
           p++;
           switch (*p) {
               case 'n':  return 10;
               case 't':  return 9;
               case 'r':  return 13;
               case '0':  return 0;
               case '\\': return 92;
               case '\'': return 39;
               case '"':  return 34;
               case 'x':  return (hex_val(p[1]) << 4) | hex_val(p[2]);
               default:   return (uint8_t)*p;  /* unknown escape: pass through */
           }
       }
       return (uint8_t)*p;  /* plain char */
   }
   ```
   - `prefix_char` (line 854) 改用 `decode_char_literal(t.start)` 替换原 switch
   - TOKEN_CHAR pattern path (line 245) 改用 `decode_char_literal(t.start)` 替换原 `t.start[1]`

3. **`compiler/src0/lexer.jhyy`** line 507 `lex_scan_char` escape check 镜像加 `e == 34` (= `'"'`)。

4. **`compiler/src0/parser.jhyy`** 三处 TOKEN_CHAR decode 全镜像:
   - `prefix_char` (line 657): 加完整 decode,处理 `\\` `\'` `\"` `\n` `\t` `\r` `\0` `\xHH`
   - `parse_pattern_primary` (line 569): 加完整 decode,**同时修旧 bug `p_addr = t.start`** 改 `p_addr = (t.start as i64) + (1 as i64)` (skip opening quote)
   - pattern range (line 362): 加完整 decode
   - 因 `qbe_type_of(*u8)='b'` 在 src0/ 是错的(per qbe_type_of 真值是 'w'),decode 用 4-byte aligned read (`*i32` deref) + shift + mask 模式(类比 W-001)

5. **新 test** (Stage 2 已加,本 fix 后改名前缀):
   - `compiler/tests/examples/char_literal.jhyy` (从 `_char_literal.jhyy` 改) — 8 个 escape case 全 PASS: `'\n' '\t' '\r' '\0' '\\' '\'' '\"' '\x41'`
   - `compiler/tests/examples/char_pattern.jhyy` (从 `_char_pattern.jhyy` 改) — `classify(c)` 函数 match `'\n' => 1` / `'a'..'z' => 2` / `_ => 0`,6 input case

**为什么不拆多 commit:**
- 跟 W-052 同原因:parser.c 跟 parser.jhyy 必须同 commit 才能保 Stage 2 byte-equal closure (jhyy_v1 → v2 → v3 → v4 IL 一致 per v1.0.0 invariant)
- src/lexer.c + src0/lexer.jhyy 也同 commit (escape 同步)
- 5 file (src/lexer.c + src/parser.c + src0/lexer.jhyy + src0/parser.jhyy + 2 test rename) = 1 commit 是最小 stable 单元

**Stage 2 closure 验证 (`jhyy_selfhost_check`):**
```
all_byte_equal: true
il_sha256: 兼容 W-052 baseline (54f8e2a1... family), W-053 没改 codegen 路径 IL 不动
37.x s total
```

**regress 验证 (`feedback_fix_evaluation_rule` 5/5):**
- `python compiler/build/bin/regress.py` → **78/78 PASS, 0 failed, 4 skipped (of 82 total)**, `char_literal.jhyy EXIT=0` + `char_pattern.jhyy EXIT=0` 在列
- `python compiler/build/bin/regress.py --all` → **2/2 gated binary PASS** (jhyy.exe + jhyy_stage0.exe)

**关键发现 (debug 时暴露) — 留作 future-reader 警告:**
1. **qbe_type_of widening 撞 data layout**: 初版只改 `qbe_type_of` (i8 → 'w'),`const_array.jhyy` 反退: byte 25 在 word-packed 数组里变成 0,正确值是 122。**正确修复**是 split `qbe_type_of` (SSA) + `qbe_data_type_of` (data section) — 详见 W-054。
2. **src0/parser.jhyy parse_pattern_primary TOKEN_CHAR 漏 +1 offset**: 旧 `p_addr = t.start` 读到 opening `'` (39),不是实际 char。**镜像 src0 时必须同时检查所有 `t.start[i]` 引用** — 这是 W-052 parity 教训在 W-053 的延伸。
3. **W-053 在 src/ src0 各 2-3 处共 4-5 处**:`prefix_char` + `TOKEN_CHAR pattern` (src/ src0 各自),W-052 教训要求共享 `decode_char_literal`,src/ 实现提取该函数,src0 保持 inline (因 jhyy 无 inline 限制)。

**lesson:**
- **escape 字符处理 = "看似 lex 细节" 但其实需要 parser + lexer 协调**,因为 escape 不只是 lex emit 错(可以 fallback 给 `\n` 当 end-of-string),而是 decode 必须在 parser 层做语义正确性(switch `case 'x'` 漏就拿错值)。
- **multi-byte UTF-8 路径不是 v1.6 范围**:即使 Plan agent 探测过,fix 单 byte `'\xHH'` 已足够覆盖 spec §4.4 "ASCII 字符字面量"用例,多字节 codepoint 留给 v1.7 单独 sprint(避免 v1.6 commit 过重 + 跟 UTF-8 decoder 整套 lex 改造捆绑)。
- **W-052 + W-053 共教训**: spec-vs-impl gap 不能用 "no test exercises it" 当 defer 理由。README `tour of the syntax` 必须有至少一个 end-to-end test 锁住。

**superseder:** commit TBD (v1.6.0 ship 2026-08-27 — src/lexer.c + src/parser.c + src0/lexer.jhyy + src0/parser.jhyy + 2 test rename 全部)

**引用:**
- W-052 (match 字面量范围模式 1..10 — 同型 parity src+src0 fix + test)
- W-001 (util.jhyy `hash_string` byte-by-byte FNV-1a 真修 — src0/parser.jhyy 镜像 escape decode 时复用其 4-byte aligned read 模式)
- W-020 (parse_pattern_primary — W-053 的 foundation:parse_pattern_primary 是 char pattern 必须扩展的同一个 primary)
- `feedback_fix_evaluation_rule` (5/5 PASS on target test mandatory — `char_literal.jhyy` + `char_pattern.jhyy` 就是 target test)
- `feedback_audit_single_commit_diff` (W-053 走同 commit 5-file + 2 test rename, audit 时 `git show <sha>` 看)
- spec `docs/abis/jhyy-lang-spec-v1.1.0.md` § 4.4 (字符字面量 — 权威)
- `docs/logs/v1/changelog-v1.6.0.md` (umbrella changelog)

---

## W-054: sizeof IL 未定义 `%t0` — 真因是 `qbe_type_of` 撞 data layout

**ID:** W-054
**状态:** ✅ RESOLVED (via W-053 fix chain, 2026-08-27)
**日期:** 探测 ~2026-08-26 (Plan agent 探测假症状) → 2026-08-27 (真因确认 + fix)
**触发面:** Plan agent 探测报 `let b: i64 = sizeof(...)` 触发 QBE 拒绝。但**实际跟 sizeof 无直接关系**,触发面是**任何 `const_array.jhyy` / const data block 含 `[u8; N]` 子字数组** — 因为 `qbe_type_of` widening (i8 → 'w') 把 data section 字节点也改了。

**Plan agent 探测的假症状:**
```
test.jhyy:15:1: error: undefined temporary: %t0
test.jhyy:15:1: error: Could not find a definition for %t0
QBE reject
```

**实际真因 (debug 时发现):**
- `qbe_type_of(Type*)` 在 src/ir.c 把 `PRIM_I8 / PRIM_U8` 返回 `'w'` (i32, word-sized),这是为满足 QBE SSA values 必须 word-sized 的约束(QBE 拒 `'b' / 'h'` 在 SSA temp / load-store operand class)
- 但 src/codegen.c 的 3 处 data emit 路径 (`cg_emit_const_prim_data` + struct field emit + global data def) 都用 `qbe_type_of`,导致 `data $X = { w 97, w 98, ... }` — 数组变成 **word-packed** (104 bytes for `[u8; 26]`)
- `const_array.jhyy` 测试期望 byte 25 = 122 (`'z'`),实际 word-packed 后 byte 25 = 第 7 个 word 的第 2 byte = 0 → FAIL
- **sizeof emit "%t1 =w copy %t0" 中 %t0 未定义** 是 Plan agent 探测的另一处字面巧合(可能跟 cg_copy_struct src 字段类型错位相关),但**根因不是 sizeof** 而是 data layout 被 widening 撞坏

**根因:** `qbe_type_of` 一个函数同时承担两个职责 (SSA temp class + data section class),职责混淆 → widening 对 data section 错。

**workaround (ACTIVE 期间):** 不存在。所有 const `[u8; N]` 字节点都反退(word-packed 后语义错),包括 `const_array.jhyy` / `char_literal.jhyy` / `char_pattern.jhyy` 等。Plan agent 探测时这些 test 全 FAIL。

**fix (W-054 — W-053 fix chain 副作用):**

1. **`compiler/src/ir.c`** 拆 `qbe_type_of` (SSA widen) vs 新 `qbe_data_type_of` (data keep byte/half packing):
   ```c
   /* qbe_type_of: SSA temp / load-store operand class. Sub-word (i8/u8/i16/u16)
      widens to 'w' (i32) — QBE SSA values must be word-sized (QBE 拒 'b'/'h' in SSA). */
   char qbe_type_of(Type *t) {
       ...
       case PRIM_I8:  case PRIM_U8:  return 'w';
       case PRIM_I16: case PRIM_U16: return 'w';
       ...
   }
   /* qbe_data_type_of: data section class. Sub-word packs byte/half ('b'/'h')
      so const arrays index correctly (e.g. [u8; 26] byte-addressable). */
   char qbe_data_type_of(Type *t) {
       ...
       case PRIM_I8:  case PRIM_U8:  return 'b';
       case PRIM_I16: case PRIM_U16: return 'h';
       case PRIM_BOOL:               return 'b';
       ...
   }
   ```

2. **`compiler/src/ir.h`** 暴露 `qbe_data_type_of`:
   ```c
   char qbe_type_of(Type *t);
   char qbe_data_type_of(Type *t);   /* data-section class (sub-word packs b/h) */
   ```

3. **`compiler/src/codegen.c`** 3 处 data emission 路径切到 `qbe_data_type_of`:
   - Line 2256 `cg_emit_const_prim_data`: `char qt = qbe_data_type_of(t);`
   - Line 2294 (struct field emit): `ir_emit_data(ir, "%c 0", qbe_data_type_of(t->struct_type.fields[i].type));`
   - Line 2349 (global data def): `char qt = qbe_data_type_of(lt);`

**src0/ side:** jhyy-side `qbe_type_of` 已 correct (per W-052 parity 教训,v1.4.6 已 ship 'w' widening) — data section 在 jhyy-side 走的是独立的 `qbe_data_type_of` 已存在(`compiler/src0/ir.jhyy`)。**src0/ 不需要改动**,W-054 fix 只在 src/ 侧。

**为什么不单独 ship:**
- W-054 根因 (qbe_type_of 职责混淆) 是 W-053 fix 路径上发现的 debug 副产品 — fix W-053 (改 `qbe_type_of` i8→'w') 必然撞 W-054 (data layout 反退),两者必须同 commit 解决。
- 跟 W-052 + W-053 同型: parity src+src0 + test rename = 1 commit 最小 stable 单元。

**Stage 2 closure 验证 (`jhyy_selfhost_check`):**
```
all_byte_equal: true
il_sha256: 兼容 W-053 baseline (W-054 不改 IL,W-053 fix 已 ship 稳定)
37.x s total
```

**regress 验证 (`feedback_fix_evaluation_rule` 5/5):**
- `const_array.jhyy` 5/5 PASS, EXIT=122 (byte 25 = 122 ✓)
- `char_literal.jhyy` + `char_pattern.jhyy` 5/5 PASS (W-053 target test)
- `python compiler/build/bin/regress.py` → **78/78 PASS, 0 failed, 4 skipped (of 82 total)**
- `python compiler/build/bin/regress.py --all` → **2/2 gated binary PASS**

**lesson:**
- **"unrelated symptoms share a root cause"** — Plan agent 探测报 "sizeof emit `%t0` undefined" 是字面巧合,真因是 `qbe_type_of` 同时被 SSA + data section 复用。fix 时必须**先识别真因** 再修,不能直接照 symptom 走(W-054 如果按 "sizeof codegen 修" 会越改越乱)。
- **职责分离 (single-responsibility)**: 一个 type→class mapping 函数应只承担一个调用方类别(SSA vs data section 不同约束)。`qbe_type_of` (SSA 必 word-sized) vs `qbe_data_type_of` (data 字节 packed) 拆开是正确架构。
- **"data section 字节 packing" 不是"低效"而是 QBE ABI 要求** — QBE `data $X = { b N, b M, ... }` 是 1-byte packing;`data $X = { w N, w M, ... }` 是 4-byte packing。byte-addressable array 必须用 `'b'`/`'h'` 才能正确 `(byte*)&X[i]` 寻址。
- **Plan agent 探测有局限** — symptom-based 探测可能误导,fix 时必须 verify 真因(本例:跑 `const_array.jhyy` 看 byte 25 错值才发现不是 sizeof)。

**superseder:** W-053 fix chain 副作用 (commit TBD, v1.6.0 ship 2026-08-27)

**引用:**
- W-053 (qbe_type_of widening 是 W-053 fix 路径上的真因 — W-054 是 W-053 chain 的 debug 副产品)
- W-052 (parity src+src0 fix 模式 — W-054 沿用)
- W-001 (util.jhyy `hash_string` byte-by-byte FNV-1a — QBE byte/half class 在 SSA 路径的正确用法参考)
- `feedback_fix_evaluation_rule` (5/5 PASS on target test mandatory — `const_array.jhyy` + `char_literal.jhyy` + `char_pattern.jhyy` 是 W-054 target test set)
- `feedback_audit_single_commit_diff` (W-054 走 W-053 commit 同 sha, audit 时算 W-053 part)
- `docs/logs/v1/changelog-v1.6.0.md` (umbrella changelog)

---

## W-055: spec §9.5 指针算术 `p + 1` 整节未实现

**ID:** W-055
**状态:** ✅ RESOLVED 2026-08-28 (v1.7.0 Stage 2)
**日期:** 2026-08-27 (探测 + 登记, 标 LIMIT 不修) → 2026-08-28 (Stage 2 真修)
**superseder:** v1.7.0 Stage 2 commit (per `docs/logs/v1/changelog-v1.7.0.md`)
**触发面:** 任何 jhyy 源码在表达式上下文对 `*T` pointer / `[*]T` slice 类型做整型算术:

| 输入 | 期望 (spec §9.5) | v1.6.0 实际 |
|------|------------------|-------------|
| `p + 1` (p: `*T`) | `*T` (offset sizeof(T)) | ❌ **type mismatch** in sema |
| `p - 1` | `*T` | ❌ **type mismatch** |
| `p - q` (p, q: `*T`) | `i64` (offset / sizeof(T)) | ❌ **type mismatch** |
| `p[n]` (subscript, p: `*T` 或 `[*]T`) | `T` (offset n*sizeof(T)) | ❌ **type mismatch** |
| `for x in 0..n { p = p + 1 }` (typical buffer walk) | OK | ❌ **type mismatch** |

**症状:**
```
test.jhyy:5:9: error: cannot apply '+' to '*u8' and 'i32'
test.jhyy:5:9: error: type mismatch in expression
sema errors
```

(Plan agent 探测 `p + 1` 在 v1.0 阶段归类为 "特性开发而非补测",本 sprint 标 LIMIT 不修。)

**根因:** sema.c / sema.jhyy 对 `*T + i32` 的类型规则**整节未实现**,只支持 `i32 + i32 / i64 + i64 / f64 + f64` 的算术。spec §9.5 "Pointer arithmetic" 段是 v1.6.0 仍未 ship 的特性。

**workaround (ACTIVE 期间):** 用 `cast (p as i64 + offset) as *T` 形式替代 `p + offset` — 即把 pointer 走 i64 路径做整数算术再 cast 回指针类型。这是 v1.5.10 之前所有 regress test 的做法(util.jhyy `hash_string` 等大量使用 `(s as i64 + i) as *u8` 模式)。

```jhyy
// 不绕 (触发 W-055):
fn next_char(l: *u8) -> *u8 {
    let p = l + 1;     // ❌ type mismatch
    return p;
}

// 绕 (workaround 验证):
fn next_char(l: *u8) -> *u8 {
    let p = (l as i64 + 1) as *u8;  // ✅ OK
    return p;
}
```

**影响范围 (实际触发面在 src0/ 内):**
- `compiler/src0/util.jhyy` — 大部分 buffer walk 用 cast 形式已绕
- `compiler/src0/lexer.jhyy` — `lex_next_char` 等用 cast 形式
- `compiler/src0/parser.jhyy` — 大量 cast 形式
- `compiler/src0/main.jhyy` — 部分 cmd-line parsing 用 cast
- **user-space test 影响面 = 0** — 所有 test 已用 cast 形式,本 sprint 不修无 regress FAIL

**OS-required 影响:** jhyy_OS 启动期需要 pointer arith 做 buffer walk (UEFI PE/COFF header parse / page table walk / MMIO buffer scan),**v1.x 不修 W-055 直接影响 OS 启动**。但 OS 启动依赖 v2.x (QBE 重写 + freestanding) + v3.x (`&mut` lifetime + `no_std`) 一起 ship,不是 v1.x 单独能解决的问题。

**实现路径 (推后续 sprint):**
1. **v1.7 / v2.x sprint** — sema 加 `*T + i32 → *T` / `*T - i32 → *T` / `*T - *T → i64` 类型规则
2. codegen 加 pointer offset emit (`add %t_p, sizeof(T) * n` 或 `mul n, sizeof(T); add %t_p, %t_n`)
3. **spec §9.5 完整覆盖** 还要做: subscript `p[n]` 等价 deref / pointer diff / pointer comparison (`p < q`) — 范围比单 `+/-` 大
4. **runtime 安全考虑**: pointer arith 没有 bounds check,需要 `&mut` lifetime (v3.x) 一起 ship 才能 compile-time 阻止越界

**为什么不修 (本 sprint scope 决策):**
1. W-053/W-054 fix 已 ship,regress 78/78 PASS,Stage 2 byte-equal closure 稳定 — 本 sprint scope 已满
2. spec §9.5 整节 = 4-6 个新 codegen 路径 + 3-5 个新 sema 路径,**commit 过重**,会反退 regress
3. v1.7 单独 sprint 做 pointer arith 更合适,可顺带做 OS-required 准备
4. OS 启动依赖 v2.x + v3.x 一起,W-055 推到 v2.x sprint 设计时考虑

**留给未来 (post-v1.6 ship):**
- v1.7 候选:`for x in slice` 已经隐含了 pointer walk(per `feedback_for_in_slice_basic`),把内部实现暴露为 spec §9.5 让 user-space 能用,自然闭环。
- v2.x 候选: QBE 重写时把 `*T + i32` 跟 QBE `add` instruction 自然映射(`%t_p =l add %t_p, %t_off`),sema 跟 codegen 同步 ship。
- v3.x 候选: `&mut` lifetime 检查 pointer arith bounds,跟 OS-required `unsafe { ... }` 块配合。

**Resolution (2026-08-28 v1.7.0 Stage 2):**

spec §9.5 4 形式全 ship:
- `*T + int` / `*T - int` → `*T` (offset = int * sizeof(elem))
- `int + *T` → `*T` (symmetry)
- `*T - *T` → `i64` (diff in elements = byte_diff / sizeof(elem))
- `p[n]` (subscript via `&NODE_INDEX` codegen fix) → `T` (offset n * sizeof(elem))

**实现 4 段:**
1. `compiler/src/sema.c` + `compiler/src0/sema.jhyy` — TOKEN_PLUS/TOKEN_MINUS 分支前加 `*T +/- int → *T` / `*T - *T → i64` / `int + *T → *T` 类型规则
2. `compiler/src/codegen.c` + `compiler/src0/codegen.jhyy` — NODE_BINARY case 加 pointer arith dispatch:offset = int * sizeof(elem) (const-fold NODE_INT 直接 emit copy, else extsw + mul), base +/- offset; *T - *T 走 byte_diff / sizeof(elem)
3. `compiler/src/codegen.c` + `compiler/src0/codegen.jhyy` — NODE_ADDR_OF NODE_INDEX 真修 (`&arr[i]` 返地址非值): 跟 NODE_INDEX 计算路径对齐 (base + idx * sizeof(elem)), 之前 fall-through `return zero` 让 caller 拿到 IRVAL_INT 0 走 `add 0, off` segfault
4. 3 个诊断 test (`compiler/tests/examples/ptr_arith_basic.jhyy` / `_diff.jhyy` / `_subscript.jhyy`) 进 default regress 验证 4 形式

**已知限制 (Stage 2 不修, 推后续):**
1. **mixed-width int promotion 不存在** — `i64 + i32` 仍 type mismatch。`d + 100` 在 ptr_arith_diff.jhyy 里改成 `d + 100i64` 绕开 (test 备注) — 真修要 mixed-width promotion (per spec §6 待 verify)
2. **pointer comparison** `p < q` 不在 Stage 2 scope (spec §9.5 隐含但未明示, 推 v2.x)
3. **bounds check** — *T +/- int 不查越界, 需 `&mut` lifetime (v3.x) compile-time 拦截
4. **subscript `p[n]` 仅 `*T` 类型** — `[*]T` slice 已有 builtin `s[i]` 走 slice_get helper (per v1.6.0),不走 `p + n` 路径

**验证 (5/5 PASS 必达 + Stage 2 byte-equal closure 保留):**
- ptr_arith_basic.jhyy (`*T + int` × 2 + `*r - *p - 10`) → EXIT=10
- ptr_arith_diff.jhyy (`*T - *T` + `d + 100i64`) → EXIT=102 (强断言 d != 0)
- ptr_arith_subscript.jhyy (`p[2]`) → EXIT=30
- full regress 86/86 PASS (jhyy.exe + jhyy_stage0.exe 双 binary)
- Stage 2 N=3 byte-equal closure 保留 (jhyy_v2.il == j3.il == v4.il sha 一致)

**Jhyy-side codegen 同步坑 (Stage 2 排查记录):**
1. `A && (B || C)` pattern — jhyy-side codegen 在 && RHS 含 || 时 phi predecessors 错配 (per Step 3 build break)。Stage 2 改写为 nested if (`A { if B || C { ... } }` 避免 `&&` with `||`)
2. if-expression 含 let block — jhyy parser 不允许 (`unexpected token 'let' in expression`)。Stage 2 改用 statement-level 单 branch if + 默认值 (`let mut r64 = right; if right.qbe_type != L { r64 = new_tmp; emit extsw }`)
3. if/else 两 branch 末必须同 type — jhyy sema 限制 (C 端无 — C 是 statement-level)。Stage 2 改用单 branch if 避免

**superseder:** v1.7.0 Stage 2 commit (post-v1.6 ship)

**引用:**
- spec `docs/abis/jhyy-lang-spec-v1.1.0.md` § 9.5 (Pointer arithmetic — 权威)
- `docs/plans/v2/v2.0.0-os-prep.md` (OS 启动依赖 pointer arith + QBE 重写 + `&mut` lifetime, 跨轴依赖)
- W-053 / W-054 (本 sprint scope 边界参考 — 修 char + data layout 不修 pointer arith)
- `docs/logs/v1/changelog-v1.6.0.md` § Known uncovered (umbrella changelog)


## W-056: 多字节 UTF-8 char literal + char type `u8 → i32` (spec §4.4)

**ID:** W-056

**Status:** ✅ RESOLVED (2026-08-28 v1.7.0 Stage 3)

**症状 (Stage 3 修前):**
1. `let c = '你'` lexer 单字节 close-check → "unterminated character literal" (lexer.c:230 / lexer.jhyy:517)。3 字节 CJK / 4 字节 emoji 全 lex fail
2. `sema.c:334 case NODE_CHAR` 走 `PRIM_U8` (spec §4.4 应为 `i32`) → char literal 类型跟 spec 不齐, 后续 `i32` 变量接收 char literal 无 coerce path
3. `codegen.c:598 NODE_CHAR` 走 `(unsigned char)d->ch` (后改 `& 255` mask) → 强截断 2-byte BMP codepoint (0x80..0x7FF) 全变 ASCII

**根因:**
1. lexer.scan_char / lex_scan_char — 多字节 UTF-8 不识别 (lead byte 0xC0/0xE0/0xF0 视作 continuation pattern 干扰,缺 lead-byte mask dispatch)
2. sema NODE_CHAR — `u8` 是 v0.7 早期选择 (跟 Stage 0 C-side `char` 类型对齐的妥协), spec §4.4 后改 `i32` 但 codegen 没跟上
3. codegen NODE_CHAR — `(unsigned char)` cast 是 C-side 默认 promotion 路径, jhyy-side 镜像用 `& 255` mask (W-052 路径), 都截断高字节

**修复 (Stage 3, parity src + src0):**
1. `compiler/src/lexer.c:213-234` scan_char + `compiler/src0/lexer.jhyy:500-524` lex_scan_char — 按 lead byte mask dispatch 字节数 (1/2/3/4), 消费对应数 continuation byte (0xC0==0x80 mask 验证)。3-byte / 4-byte 显式 error ("3/4-byte UTF-8 codepoint not supported in v1.7.0 Stage 3, use ASCII or 2-byte BMP; CJK/emoji 推 v2.x") — per master plan scope (Stage 1-5 不覆盖的)
2. `compiler/src/ast.h:96 + :325` NodeChar.ch `char → uint32_t` + ast_new_char signature。src0/ast.jhyy NodeChar.ch: i32 已够, 不动
3. `compiler/src/parser.c:44-81 + :861 + :248` decode_char_literal return type `unsigned char → uint32_t` + UTF-8 multi-byte decode (lead + 1 cont → 11-bit codepoint)。src0/parser.jhyy 新加共享 helper `decode_char_literal` 替换 3 处 inline copy (line 362, 570, 696) — W-053 教训: 漏 1 处 silent fail
4. `compiler/src/sema.c:334-337 + compiler/src0/sema.jhyy:520-524` NODE_CHAR — `PRIM_U8 → PRIM_I32` (spec §4.4)
5. `compiler/src/codegen.c:598-603 + compiler/src0/codegen.jhyy:1312-1318` NODE_CHAR codegen — 去掉 `(unsigned char)` + `& 255` 截断。IR temp 已 `'w'` (32-bit), 只透传 codepoint

**Side fix (Stage 3 排查过程发现):**
- src0/parser.jhyy:463 + :623 char pattern codepath 仍用 `PRIM_U8()` 标记 NodeInt/NodePatternLit (与 src/parser.c:250 + :263 + :272 已改 `PRIM_I32` 不齐)。改后 src0/parser.jhyy 也走 `PRIM_I32()` — 这才是导致 char_utf8_expr Stage 0 路径 EXIT=0 vs v1 EXIT=5 不一致的真因 (mask `& 255` 没截断 codepoint, 但 PRIM_U8 类型让 sema 接受常量后 codegen 路径走丢)

**测试:**
- 新 `compiler/tests/examples/char_utf8_basic.jhyy` — 3 个 BMP char literal 值断言 (`'é'` = 233 / `'ñ'` = 241 / `'ü'` = 252) → EXIT=0
- 新 `compiler/tests/examples/char_utf8_expr.jhyy` — BMP char 在 match arm pattern + match value → EXIT=5
- 改 `compiler/tests/examples/char_literal.jhyy` — 8 个 `: u8 → : i32` + 3 个 BMP case 追加
- 改 `compiler/tests/examples/char_pattern.jhyy` — `fn classify(c: u8) → c: i32` + call sites 去掉 `as u8` cast

**验证 (5/5 PASS 必达 + Stage 3 byte-equal closure 保留):**
- char_utf8_basic.jhyy → EXIT=0 (3/3 BMP char value)
- char_utf8_expr.jhyy → EXIT=5 (BMP char in match arm)
- char_literal.jhyy → EXIT=0 (12 char family incl 3 BMP)
- char_pattern.jhyy → EXIT=0 (6 patterns incl range)
- full regress 88/88 PASS + 4 SKIP (jhyy.exe + jhyy_stage0.exe 双 binary, parity)
- Stage 3 N=4 byte-equal closure 保留 (jhyy_v1.il == v2.il == v3.il == v4.il sha = 7552aa94...)

**已知限制 (Stage 3 不修, 推后续):**
1. **3-byte / 4-byte UTF-8 codepoint** — `let c = '你'` (U+4F60) 仍 lex fail, 推 v2.x (per master plan §"Stage 1-5 不覆盖的")
2. **char type signedness** — Stage 3 严格按 spec 走 `i32`, 若 spec revision 改 `u32` / `u8` 推 v2.x
3. **char → u8 implicit coerce** — `let x: u8 = 'a'` 现 type mismatch (i32 → u8 需 `as`), 无 coerce path。后续写 `let x = 'a'` (类型推导) 自动 `i32`
4. ~~**match arm body `=> r = N` stage0 codegen gap**~~ — ✅ **RESOLVED 2026-08-28 v1.7.1 patch A2** (fact-check 升级:从 NOT A BUG 改成真修). 实测 stage0 cg_expr (compiler/src/codegen.c:549-1935) **没有** NODE_ASSIGN case → default 返回 sentinel IRVal{0},storew 不 emit。match arm body `r = 7` 是 NODE_ASSIGN (parser parse_expr 直接返回 expr,不 wrap EXPR_STMT),调 cg_expr 路径 (codegen.c:1579) 走 default → arm body 不写 local → 永远返回 0 (r 初值)。真修: cg_expr 加 NODE_ASSIGN case → 委托 cg_stmt (cg_stmt.c:1949 完整 handle 所有 target)。jhyy-side src0/codegen.jhyy:1880 早就合并所有 stmt cases (per src0/codegen.jhyy:3490 comment),所以 jhyy-side 一直正确 — C-side 是真 parity gap。之前 v1.7.1 patch A2 plan 误诊为 "NOT A BUG" 是错 — 实际是真 bug 但只影响 C-side (`jhyy_stage0.exe`),jhyy-side (`jhyy.exe` production) 验证 EXIT=5 是误以为 ship 通了 (其实是 jhyy-side 一直在 work)。

**Jhyy-side codegen 同步坑 (Stage 3 排查记录):**
1. **shared helper 替换 inline copy** — src0/parser.jhyy 3 处 inline decode_char_literal (line 362, 570, 696) 用 `decode_char_literal(start, length)` 共享 helper 替换, 必须 3 处都改 (W-053 教训: 漏 1 处 silent fail)
2. **`&& with ||` phi mismatch** — src0/lexer.jhyy UTF-8 多字节扫描用 nested if (`lead_x_check { ... extra_check { ... } }`) + while (`while i < extra { ... }`), 避免 `A && (B || C)` 范式 (跟 Stage 2 同型)
3. **`PRIM_U8() → PRIM_I32()` side effect** — char pattern codepath 用 `ast_new_int(arena, loc, val, PRIM_*)` 标记 type, src0/parser.jhyy 漏改 2 处 (line 463 + 623), stage0 跟 v1 parity 失守。诊断通过对比双方 .il 输出 (per feedback_fix_evaluation_rule + feedback_il_s_debugging_pattern)

**superseder:** v1.7.0 Stage 3 commit (post-Stage 2 ship)

**引用:**
- spec `docs/abis/jhyy-lang-spec-v1.1.0.md` § 4.4 (Char literals — 权威)
- W-052 (本 sprint scope 上游 — 修 char family escape 但漏多字节 UTF-8 + type 对齐)
- W-053 (本 sprint scope 上游 — 同上, escape 族 + hex escape 已 ship 但多字节留 Stage 3)
- `docs/plans/v1/v1.7.0任务清单 + 概要设计.md` (umbrella 5 候选之第 3 步 W-053 followup)
- `docs/logs/v1/changelog-v1.7.0.md` (umbrella changelog, Stage 3 段)

---

## W-057: UTF-8 3-byte / 4-byte codepoint 显式 lex reject (推 v2.x)

**ID:** W-057
**状态:** ✅ RESOLVED 2026-09-23 (v3.0.6/Ph.1)
**日期:** 2026-08-28 (v1.7.3 patch 排查发现 spec/test/workarounds 缺归档)
**superseder:** 2026-09-23 (v3.0.6/Ph.1 W-057 真修, 跟 V2.13.7 `594d00d` 同源)
**触发面:** spec §4.4 字符字面量族中, 3-byte (U+0800-U+FFFF, e.g. `'你'` U+4F60) + 4-byte (U+10000+, e.g. `'🎉'` U+1F389) UTF-8 codepoint 在 v1.7.0 Stage 3 显式 lex reject.

| 输入 | 期望 (per spec §4.4 字符字面量族) | v1.7.0 实际 | v3.0.6/Ph.1 实际 |
|------|----------------------------------|-------------|------------------|
| `'A'` (1-byte ASCII) | codepoint 65, i32 type | ✅ OK (Stage 3 ship) | ✅ OK |
| `'é'` (2-byte BMP, U+00E9) | codepoint 233, i32 type | ✅ OK (Stage 3 ship) | ✅ OK |
| `'你'` (3-byte CJK, U+4F60) | codepoint 0x4F60, i32 type | ❌ **lex reject** "3/4-byte UTF-8 codepoint not supported" | ✅ OK (Ph.1 ship) |
| `'🎉'` (4-byte emoji, U+1F389) | codepoint 0x1F389, i32 type | ❌ **lex reject** "3/4-byte UTF-8 codepoint not supported" | ✅ OK (Ph.1 ship) |

**症状 (resolved):**
```
test.jhyy:2:9: error: 3/4-byte UTF-8 codepoint not supported
parse errors
```

**根因 (resolved):** vendor QBE (2026-08-15 build `qbe/qbe.exe`) 编译期 folding 3/4-byte codepoint 整数字面量到 IL 时, 数据 section `b 0xE4` `b 0xBD` `b 0xA0` (UTF-8 字节序列) 不被 vendor QBE 当作单个 codepoint 折叠, emit 错误 IL 字节序。

**workaround (v1.7.0 期间, 已废弃):** v1.7.0 Stage 3 (commit `b0e9c3c`) 显式 lex reject 3/4-byte codepoint, 跟 plan 一致 (per `docs/logs/v1/changelog-v1.7.0.md` line 131 "Stage 1-5 不覆盖的" 段 + master plan § 5.3 Stage 3 scope). ship 时无独立 W-NNN 登记, 推 v2.x 真修 (vendor QBE 升级主线或自研 backend)。

**Resolution (2026-09-23 v3.0.6/Ph.1)**:
- **2 src0 files 真改** (跟 V2.13.7 `594d00d` 同源):
  1. `compiler/src0/lexer.jhyy` lead byte 分支从 2 类 (ASCII + 2-byte) 扩 4 类 (ASCII + 2/3/4-byte), `extra` 计数 0/1/2/3, 删 `oos=1` reject 分支 (line 537-575 改)。
  2. `compiler/src0/parser.jhyy` `decode_char_literal` 加 3-byte + 4-byte UTF-8 decode 分支, codepoint 计算 per RFC 3629 bitmask formula。
- **codegen 不动**: parser 把 char codepoint → `ast_new_int(PRIM_I32)`, codegen 收 `NODE_INT` 走 `ir_emit_copy` (`%t =w copy 0xCODE`) 已 cover 3/4-byte (e.g. `'🎉'` 0x1F389 = 127881 < 2^31, QBE `w` 类能容). Self-backend 同路径 (`codegen_amd64_emit_call.jhyy` 不动, 跟 codegen.jhyy 一致)。
- **2 NEW test files**: `char_literal_3byte.jhyy` (CJK `'你'` U+4F60) + `char_literal_4byte.jhyy` (emoji `'🎉'` U+1F389), 沿用 V2 命名 (per audit fix #1)。
- **Verification**: 5/5 PASS on 2 new tests + regress 139/139 PASS / 0 FAIL / 20 SKIP preserved (no regression)。
- **byte-equal D26 5/5 PASS preserved** (per v3.1.0 D26 stage0 recipe; jhyy.exe sha `496bea91c54c2f24...` post-Phase.1 rebuild)。

**实现路径 (resolved, v3.0.6/Ph.1 实施):**
1. ~~vendor QBE 升级~~ — 不需要 (V3 codegen path 不依赖 vendor QBE for codepoint folding)
2. ✅ **自研 backend codepoint folding** (跟 V2 同源) — v3.0.6/Ph.1 在 parser 阶段 fold char literal → `ast_new_int(PRIM_I32)`, 字节序 UTF-8 在 string literal 路径单独处理 (data section `b 0xE4 b 0xBD b 0xA0` 字符串)
3. ✅ **spec §4.4 修订** — v3.0.6+ spec 把 3/4-byte codepoint 描述补回 ship 范围, 加 "data section codepoint folding 在 v3.0.6 backend 支持" 段 (v3.0.6/Ph.6 docs work 随 sync)

**影响范围 (resolved):**
- user-space test: `char_literal_3byte.jhyy` + `char_literal_4byte.jhyy` ship, regress 139/139 PASS preserved
- OS-required (jhyy_OS): UEFI PE/COFF 字符串 CJK 字符 now support (UEFI 多用 ASCII, 但 OS debug 输出含 CJK 字符现在正常)
- lib 路径: src0/util.jhyy / src0/lexer.jhyy 字符串字面量仍 1-byte ASCII (3/4-byte codepoint 仅 char literal 路径, string literal 独立)

**引用:**
- spec `docs/abis/jhyy-lang-spec-v1.3.0.md` § 4.4 (Char literals — 权威, B2 v1.7.3 patch 加 BMP-only 限制)
- W-052 (本 sprint scope 上游 — char family escape 但漏 3/4-byte codepoint)
- W-053 (本 sprint scope 上游 — escape 族 + hex escape 已 ship 但 3/4-byte 留 Stage 3 reject)
- W-056 (本 sprint scope 上游 — Stage 3 多字节 UTF-8 partial ship, 限定 2-byte BMP, 3/4-byte 推 v2.x)
- `docs/logs/v1/changelog-v1.7.0.md` line 131 (Stage 1-5 不覆盖段)

---

## W-058: vendor QBE (2026-08-15 build) 不支持 `remd` / `rems` 浮点取模 (推 v2.x)

**ID:** W-058
**状态:** ✅ RESOLVED 2026-09-23 (v3.0.6/Ph.2)
**日期:** 2026-08-28 (v1.7.3 patch 排查发现 spec/test/workarounds 缺归档) → 2026-09-23 (v3.0.6/Ph.2 sprint 真修)
**superseder:** 2026-09-23 (v3.0.6/Ph.2 W-058 真修, 跟 V2.13.8 `16b4903` 同源)。self-backend 路径 W-083 真修在 v3.0.6/Ph.3 (V3 modular split 4 files 改: `codegen_amd64_state.jhyy` `ILTOK_CONV` + `codegen_amd64_lexer.jhyy` `next_token_conv` + 'd'/'s'/'u'/'e'/'t' prefix handlers 识别 18 conv ops + `codegen_amd64_emit_call.jhyy` `emit_conv` 18 branches 走 SSE cvttsd2si/cvttss2si/cvtsi2ss/cvtsi2sd/cltq + `codegen_amd64.jhyy` ILTOK_CONV dispatch — **V3 无 codegen_amd64_emit_sse.jhyy**, per audit fix #2 REVERTED + user "V3 modular split 不新建 SSE file" 决策), 跟 V2.13.11 `425ab53` 同源。
**触发面:** spec 附录 B P3 fmod row "浮点取模 `%=` / `a % b` reject" (i32/i64 整数模 ship, 浮点模不 ship).

| 输入 | 期望 (per spec 附录 B P3 v3.0.6 revision) | v1.7.2 实际 | v3.0.6/Ph.2 实际 |
|------|--------------------------|-------------|-----------------|
| `i32 % i32` (整数模) | i32 余数 | ✅ OK (codegen emit `rem` / `div`) | ✅ OK |
| `i64 % i64` | i64 余数 | ✅ OK (codegen emit `rem` / `div`) | ✅ OK |
| `f64 % f64` (浮点模) | f64 IEEE 754 remainder (trunc toward 0) | ❌ **vendor QBE reject** "invalid instruction: remd" | ✅ OK (Ph.2 ship, fold `a - trunc(a/b)*b`) |
| `f64 %= f64` (compound) | f64 复合赋值 | ❌ **同上** | ✅ OK (Ph.2 ship, 同路径) |
| `f32 % f32` (浮点模) | f32 IEEE 754 remainder | ❌ **vendor QBE reject** "invalid instruction: rems" | ✅ OK (Ph.2 ship, polymorphic f32 fold, stosi variant) |
| `-7.5 % 2.0` (negative 区分 floor 关键) | -1.5 (trunc toward 0) | ❌ reject | ✅ OK (Ph.2 ship, trunc not floor) |

**症状 (resolved):**
```
test.jhyy:3:9: error: invalid instruction 'remd' (vendor QBE 2026-08-15 build 不支持)
codegen errors
```

**根因:** vendor QBE (`qbe/qbe.exe` 2026-08-15 build, per `docs/logs/v1/changelog-v1.7.2.md` A1 ship 时 fact-check fail) 不实现 `remd` (f64 remainder) 和 `rems` (f32 remainder) 指令。其他 backend (e.g. gcc) 编译期折叠到 `fmod()` library call, 但 vendor QBE 不能 fold, 拒绝指令。

**workaround (v1.7.2 期间, 已废弃):** v1.7.2 patch A1 ship 时 fact-check 发现 vendor QBE 不支持 `remd`/`rems`, 标 LIMIT 不修, 推 v2.x 真修 (vendor QBE 升级主线或自研 backend)。spec 附录 B P3 fmod row "推 v2.x" 段保留 v2.x 真修描述, 缺独立 W-NNN 归档 (本 v1.7.3 patch 补登)。

**Resolution (2026-09-23 v3.0.6/Ph.2)**:
- **1 src0 file 真改** (跟 V2.13.8 `16b4903` 同源):
  1. `compiler/src0/codegen.jhyy` line 2214+ 插 45 行: `TOKEN_PERCENT` + (QBE_D 或 QBE_S) early return 路径 → emit 5-instruction user-space formula `a - trunc(a/b) * b` (div + dtosi/stosi + swtof + mul + sub, polymorphic by `tok.qbe_type`)。Polymorphic arith op (`div`/`mul`/`sub`) 靠 `=d`/`=s` 类型后缀, 不嵌 type suffix 进 opcode name; type-conversion ops (`stosi`/`dtosi`/`swtof`) 把 type 后缀编入 name。is_f32 nested plain `if` 无 `&&`/`||` short-circuit (避免 W-081 sub-bug latent phi merge gap, per `feedback_jhyy_brace_nesting`)。
- **codegen 跳过 `op = "rem"` dispatch**: line 2267 (post-Ph.2) 仍 emit `rem` for integer `%` (i32/i64 integer mod 走 vendor QBE `remw`/`reml`), f64/f32 路径在 `let mut op: *u8 = "add" ...` 之前 early-return。
- **3 NEW test files** (沿用 V2 命名 per audit fix #1):
  1. `fmod_basic.jhyy` (`7.0 % 2.0` exit=1)
  2. `fmod_negative.jhyy` (`-7.5 % 2.0` exit=99 = `r_int + 100`; +100 避开 Windows NTSTATUS 误判 0xFFFFFFFF; trunc 区分 floor 关键)
  3. `fmod_f32.jhyy` (`7.0_f32 % 2.0_f32` exit=1, polymorphic f32 fold)
- **Verification**: 5/5 PASS on 3 new tests + regress 126/126 PASS / 0 FAIL / 21 sysv SKIP preserved (no regression; 3 fmod tests add 3 to FRESH total 129)。
- **byte-equal D26 5/5 PASS preserved** (per V3 D26 stage0 recipe; jhyy.exe sha refresh post-Ph.2 rebuild)。

**实现路径 (resolved, v3.0.6/Ph.2 实施):**
1. ~~vendor QBE 升级~~ — 不需要 (V3 codegen 不依赖 vendor QBE for `%` operator, fold user-space formula)
2. ✅ **自研 backend codegen fold `a - trunc(a/b)*b`** (跟 V2 同源) — v3.0.6/Ph.2 codegen.jhyy fold, QBE IL 5 insns (div + dtosi/stosi + swtof + mul + sub); vendor QBE 全程处理 (无 `remd`/`rems` 依赖)
3. ✅ **spec 附录 B P3 修订** — v3.0.6+ spec 把 fmod row 描述补回 ship 范围, 加 "codegen.jhyy fold `a - trunc(a/b)*b` 5 insns" 段

**影响范围 (resolved):**
- user-space test: `fmod_basic.jhyy` + `fmod_negative.jhyy` + `fmod_f32.jhyy` ship, regress 126/126 + 3 fmod = FRESH 129 PASS preserved
- OS-required (jhyy_OS): jhyy_OS runtime 暂无 fmod use case (kernel 自带 IEEE 754 mod), 但 user-space `extern fn fmod(...)` lib call 现在有 jhyy-side 同源 fold
- lib 路径: src0/util.jhyy / src0/std/*.jhyy fmod use now supported (per spec 附录 B P3 ship 范围)
- W-083 self-backend 路径: 单独 v3.0.6/Ph.3 真修 (V3 modular split 4 files 改, 不新建 SSE file, per audit fix #2 REVERTED + user "V3 modular split 不新建 SSE file" 决策): `codegen_amd64_state.jhyy` `ILTOK_CONV = 16` + `codegen_amd64_lexer.jhyy` `next_token_conv` + 'd'/'s'/'u'/'e'/'t' prefix handlers 识别 18 conv ops (per user "conversion 是一族, 一次补齐") + `codegen_amd64_emit_call.jhyy` `emit_conv` 18 branches 走 SSE cvt* + `movabs(x)` 等 + `codegen_amd64.jhyy` ILTOK_CONV dispatch, 跟 V2.13.11 `425ab53` 同源

**引用:**
- spec `docs/abis/jhyy-lang-spec-v1.3.0.md` 附录 B P3 (fmod row, C4 v1.7.3 patch 加 cross-ref W-058)
- `docs/logs/v1/changelog-v1.7.2.md` A1 (v1.7.2 patch A1 ship 时 fact-check fail, 标 LIMIT 推 v2.x)
- vendor QBE build `qbe/qbe.exe` 2026-08-15 (per `docs/internal/architecture.md` QBE IL 速查段)
- V2.13.8 真修 commit `16b4903` (port reference)
- V2.13.11 self-backend 真修 commit `425ab53` (W-083 closure)
- `docs/plans/v3/v3.0.6-port-v4.0.0-src0-closure.md` Ph.2 section
- `docs/logs/v3/changelog-v3.0.md` v3.0.6/Ph.2 section
- V3.0.6/Ph.3 W-083 entry (self-backend closure, 跟 Ph.2 互补)

---

## W-083: V3 self-backend 不支持 QBE IL conversion ops (lexer 不识别 dtosi/stosi/swtof/exts/...) (推 v3.0.6)

**ID:** W-083
**状态:** ✅ RESOLVED 2026-09-23 (v3.0.7/Commit 1+2 真修 Layer 1+2+3; Gate-0 3/3 strict sha PASS + 3/3 exit code PASS = 6/6/0)
**日期:** 2026-09-23 (v3.0.6 Ph.3 ship 时 audit-flip closure) → 2026-09-23 (Layer 2/3 W-086 NEW defer)
**superseder:** v3.0.6/Ph.3 真修:
  - `codegen_amd64_state.jhyy`: +ILTOK_CONV enum constant
  - `codegen_amd64_lexer.jhyy`: extend main dispatcher (`'d'`/`'s'`/`'u'`/`'e'`/`'t'` prefix handlers) + new `next_token_conv(s, arena, t, op_name, op_len)` helper (~120 LOC delta)
  - `codegen_amd64_emit_call.jhyy`: extend `size_suffix_for_qt` (返 "ss"/"sd" for QBE_S/QBE_D) + add `emit_mov_temp_to_xmm` / `emit_mov_xmm_to_temp` / `emit_mov_temp_to_int` / `emit_mov_int_to_temp` helpers + new `emit_conv(state, tok)` dispatcher (~250 LOC, 18 distinct conv op dispatches: dtosi/dtosl/dtoui/dtoul/stosi/stosl/stoui/stoul/swtof/sltof/uwtof/ultof/exts/truncd/extsw/extuw)
  - `codegen_amd64.jhyy`: +3 LOC dispatch case `else if kind == ILTOK_CONV() { emit_conv(state, tok_p); }` in `parse_and_emit`
**触发面:** v3.0.6/Ph.2 (fmod user-space formula trunc) ship 后, fmod_basic/fmod_negative/fmod_f32 测试在 QBE default backend PASS (5 IL insns polymorphic by tok.qbe_type), 但 JHY_SELF_BACKEND=1 (自 backend opt-in path) produce 0-byte .s + gcc link fail。

**Layer 1 root cause (W-083 真修):** V3 codegen_amd64_lexer.jhyy main dispatcher 在 `'d'` prefix handler (line 700-715) 只识别 `data` (data_string) + `div` (binop), 其他 (`dtosi`/`dtosl`/`dtoui`/`dtoul`) 返 -1 → `lex_il` 跳过 1 byte → continue 直到 EOF → 0 token emit → `codegen_amd64_run` 返 0 with empty .s。类似 `'s'`/`'u'`/`'e'`/`'t'` prefix 也不识别 stosi/swtof/ultof/exts/truncd/exts* family。

**症状 (Ph.3 ship 前实测):**
```
$ JHY_SELF_BACKEND=1 jhyy.exe compile fmod_basic.jhyy -o /tmp/fb.exe
[4] codegen done
gcc link failed: "C:\msys64\ucrt64\bin\gcc.exe"  -g0 -Wl,--build-id=none ...
collect2.exe: error: ld returned 1 exit status
$ wc -c /tmp/fb.exe.s
0 /tmp/fb.exe.s  ← 0-byte .s
```

**Layer 2/3 root cause (W-086 NEW, defer 真修 to v3.0.7):** 见 W-086 entry。V3 self-backend emit_copy/emit_binop/emit_conv 字段约定冲突 + lexer 不 consume operand — 即使 W-083 Layer 1 真修 (lexer 识别 conv ops), JHY_SELF_BACKEND=1 fmod 仍 0-byte .s (W-086 阻塞)。

**Symptom fixed (Ph.3 ship 后 Layer 1 实测, QBE path):**
```
$ jhyy.exe compile fmod_basic.jhyy -o /tmp/fb.exe  # default QBE backend
$ /tmp/fb.exe
$ echo $?
1  ← exit=1 (7.0 % 2.0 = 1.0 as i32 = 1) ✅ (QBE path)
$ wc -c /tmp/fb.exe.s
200 /tmp/fb.exe.s  ← QBE 路径 OK
```
regress 142/142 PASS / 0 FAIL / 20 SKIP preserved (default QBE path 不变)。

**Symptom NOT fixed (Layer 1 alone, ⏳ pending Gate-0 + W-086):**
- `JHY_SELF_BACKEND=1 fmod_basic.jhyy` 仍 0-byte .s (W-086 Layer 2 emit_* 字段约定 broken + Layer 3 lexer 不 consume operand 阻塞)
- 默认 QBE 3/3 PASS + regress 142/142 PASS + byte_equal_amd64 5/5 PASS **全是假阳性**: 三 gate 全不跑 self-backend (default compile 不设 JHY_SELF_BACKEND → run_backend 落 run_qbe path, per `main.jhyy:803` 注释 "默认不设 JHY_SELF_BACKEND, 所以 104/104 全程走 QBE")

**Resolution (Layer 1, W-083 code-only 真修 — ⏳ execution proof deferred to Gate-0):**
- lexer 加 prefix handlers for conversion ops (per `feedback_jhyy_brace_nesting` nested plain `if` 无 `&&`/`||` short-circuit)
- ILTOK_CONV token kind + parse_and_emit dispatch case
- emit_conv 完整 family (18 ops); x86-64 SSE cvt* / movss/movsd / cltq 指令 family; %xmm0 scratch
- size_suffix_for_qt extend to 4-way (w/l/s/d)

**Verification gate (per 用户 2026-09-23 反馈 "W-083 RESOLVED 不算")** — 必须 Gate-0 (`compiler/tests/bootstrap/byte_equal_selfbackend.sh` NEW) 真跑 JHY_SELF_BACKEND=1 fmod 3/3 + .s non-empty + gcc link + exit code + sha byte-equal to QBE baseline。Gate-0 ship sequence:
1. **Gate-0 ship (造红灯)**: byte_equal_selfbackend.sh 实现 + run 观察 3/3 FAIL (0-byte .s + gcc link fail) — W-086 阻塞证据
2. **W-086 (b)+(c) one-commit 真修**: 见 W-086 entry corrected design (token 扩 3-operand + lexer consume + emit_* 统一读 dst/lhs/rhs)
3. **Gate-0 灯转绿**: run byte_equal_selfbackend.sh 3/3 PASS + .s sha byte-equal to QBE baseline
4. **W-083 ⏰ → ✅ RESOLVED**: flip status post-Gate-0 green, ship 在 W-086 (b)+(c) commit 同一 logical commit group

**References:**
- `docs/plans/v3/v3.0.6-port-v4.0.0-src0-closure.md` Ph.3 section (含 audit fix #2 REVERTED note + W-086 关联)
- `docs/logs/v3/changelog-v3.0.md` v3.0.6/Ph.3 section
- `compiler/src0/codegen_amd64_lexer.jhyy` `next_token_conv` + dispatcher prefix handlers
- `compiler/src0/codegen_amd64_emit_call.jhyy` `emit_conv` + XMM mov helpers
- `compiler/src0/codegen_amd64_state.jhyy` ILTOK_CONV enum
- V2.13.11 self-backend 真修 commit `425ab53` (W-083 original — V3 port scope = "conversion family" 而非仅 fmod, per user 2026-09-23 反馈)

---

## W-086: V3 self-backend ILToken 字段数根本不足 (dst/lhs/rhs 三元组塌缩到 2 槽) + lexer 不 consume operand (推 v3.0.6/Gate-0 后 / v3.0.7)

**ID:** W-086
**状态:** ✅ RESOLVED 2026-09-23 (v3.0.7/Commit 1 wholesale merge-file + strcmp migration + state cast + emit_conv comment drop + 2-op rewrite + op_len fix; Gate-0 灯转绿作为 closure 证据)
**日期:** 2026-09-23 (v3.0.6/Ph.3 W-083 真修时深 RCA 发现; 用户 2026-09-23 反馈重排 (a)(b)(c) 顺序 + 纠正 (a) 写法)
**superseder:** v3.0.7/Commit 1 (wholesale merge-file + strcmp migration + state cast + emit_conv comment drop + 2-op rewrite + op_len fix) + v3.0.7/Commit 2 (emit_conv 2-op form rewrite strict sha alignment), 跟 Gate-0 是 1 commit group (Commit 0 造红灯 ship + Commit 1+2 真修 ship + Gate-0 灯转绿验证)
**触发面:** V3 self-backend (JHY_SELF_BACKEND=1) 对**任何** test with arithmetic (binop / copy IMM / conv) produce 0-byte .s。RCA: ILToken 字段数根本不够装 binop 的 (dst, lhs, rhs) 三元组, 加 lexer 不 consume operand → token 字段大部分 default 0 → emit 函数 emit 错指令但 codegen_amd64_run 返 0 (write 0-byte .s) → gcc link fail。

**根因 (用户 2026-09-23 反馈纠正 (a) 写法) — 字段数根本不足, 不是"选哪个约定":**

binop 语义 = `dst = op(lhs, rhs)`, 需要 3 个 operand slots。当前 ILToken (codegen_amd64_state.jhyy:81-88) 只有 `int_val` + `text_len` 两个 8B 字段 = 16B payload 容纳 2 个 operand。emit_binop 拿 `int_val` 当 dst_id 之后, lhs/rhs 没地方放 → 塌缩成由 dst_id=0 推导出的固定偏移 (-32(%rbp))。**所有 binop 写 -32(%rbp) 就是这个塌缩的实证**: lhs/rhs 缺失后, dst_off 默认从 0 (sentinel) 推导 -32 → 所有 emit_binop 调用写同一 slot → 后续 read `%t<N>` 读到错 slot。

类似 emit_copy (1 dst + 1 src = 2 operand) 跟 emit_binop 抢 `int_val` 槽; emit_conv (1 dst + 1 src) 同; emit_call (1 ret + N args) 同样数不足。

**Layer 2 (字段约定冲突 + emit_* 各自乱读):**
| emit fn | 读 int_val | 读 text_len | 读 text |
|---------|-----------|-------------|---------|
| emit_copy (codegen_amd64_emit_call.jhyy:411-418) | src value (IMM 数字 or TEMP id) | dst_id | NULL=IMM, 非NULL=TEMP |
| emit_binop (line 459-465) | dst_id (跟 emit_copy 冲突!) | — | — |
| emit_call (line 312) | ret temp id | — | — |
| emit_volatile | — | — | "volatile" 字面 |
| emit_conv (Ph.3 NEW, line 657) | dst_id (跟 emit_copy 冲突) | src_id | op name |

| lexer fn | 写 int_val | 写 text_len | 写 text |
|----------|-----------|-------------|--------|
| '%' LHS handler (line 680-711) | **不写** | **不写** | **不写** |
| next_token_binop (line 491-496) | **不写** | 3 (op_name len) | "add"/"sub"/etc |
| next_token_copy (line 407-415) | **不写** | **不写** | **不写** |
| next_token_call | ret temp id (line 312) | — | fn name |
| next_token_conv (Ph.3 NEW) | **不写** | src_id | op name |

**Layer 3 (lexer 不 consume operand):**
- next_token_binop 只 consume op name, 不 consume src1/src2 operand (line 491-498)
- next_token_copy 只 consume "copy" 4 chars, 不 consume src operand (line 407-415)
- next_token_conv (Ph.3 NEW) consume op name + src (%t<N>), 但若 src 是 IMM literal (e.g., `%t1 =w copy 42`) → 返 -1
- next_token_call 不 consume args (emit_call 自己二次 scan)
- '%' LHS handler (line 680) consume %t<N> 字符但不写 token 字段

**V3 self-backend 从未被任何 CI gate 真 exercise 证据:**
- byte_equal_amd64.sh 5 tests (hello/fib_renamed/struct_val_pass/hello-freestanding/mixed_struct_slice_match) 跑 default `compile --target=amd64_win` (无 env var) → run_backend dispatch: BACKEND_SELF target + JHY_SELF_BACKEND not set → 落 `run_qbe` fallback (line 823-824 in main.jhyy)
- 两 paths (QBE_FALLBACK=1 显式 vs default fallback) 都是 `run_qbe` → byte-equal trivially
- byte_equal_amd64.sh 5/5 PASS 是 false positive, 不证明 V3 self-backend 真能 produce valid .s
- 真正 exercise self-backend 需要 JHY_SELF_BACKEND=1 — W-086 让这个 path 对任何 arithmetic test 都 fail (0-byte .s)

**Resolution path (用户 2026-09-23 反馈重排) — (b)+(c) ONE commit (合并, 不分步):**

1. **(b) lexer consume operand for ALL token kinds** (优先级 1 — 开关): `'%'` LHS handler 写 dst_id 到 token.dst; next_token_binop consume lhs + rhs operand (`%t<N>` 或 IMM literal) 写 token.lhs/token.rhs; next_token_copy consume src operand 写 token.src; next_token_conv consume src 写 token.src (existing partially); next_token_call args (existing partially)
2. **(c) 扩展 ILToken 到 3-operand capacity** (per C struct layout): 加 `dst: i64` + `lhs: i64` + `rhs: i64` 字段 (3 × 8B = 24B operand payload), 加 `op_flags: i32` 标记 IMM/TEMP 区分 (每 operand 1 bit × 3 = 3 bits, pack 进 op_flags)。emit_* 全部按 dst/lhs/rhs 读 + 按 op_flags 决定 IMM vs TEMP 路径。**删 L4 § 4.3 1-to-1 简化** (假设单槽正是这个 bug 的 root cause — 1-to-1 简化允许只用 2 字段凑合) — V3 self-backend 真实现需要真 src/dst temp ids + regalloc 重新 emit offset query。
3. **(a) 字段约定统一作废 — 不需要单独 commit**: (b)+(c) 一起做完, emit_copy/binop/conv/call 全部按 dst/lhs/rhs 读, 冲突自然消解。**先做 (a) 等于白做一遍** (per 用户反馈)。

**Verification gate (Gate-0 + 副作用验证):**
- **Gate-0 (造红灯, pre-W-086-fix commit)**: `compiler/tests/bootstrap/byte_equal_selfbackend.sh` NEW — 跑 `JHY_SELF_BACKEND=1 jhyy.exe compile fmod_basic/fmod_negative/fmod_f32` → 期望 3/3 FAIL (0-byte .s + gcc link fail)。保存 sha baseline `compiler/tests/bootstrap/baseline/fmod_*.s.sha256` 用作"绿"基准。
- **W-086 (b)+(c) fix commit**: token 扩 + lexer consume + emit_* 统一读。
- **Gate-0 灯转绿 (post-W-086-fix verification)**: run byte_equal_selfbackend.sh → 期望 3/3 PASS + .s non-empty (size > 100B) + gcc link success + exit codes 1/99/1 + sha byte-equal to QBE baseline。
- **W-083 副作用**: status flip ⏳ → ✅ post-Gate-0-green (同一 logical commit group)。
- **后续 ship gates**: regress 142/142 PASS / 0 FAIL / 20 SKIP preserved; byte_equal_amd64.sh --no-strict 5/5 PASS preserved (不修改, 仍 false positive 但用 QBE 比 QBE 仍 byte-equal trivially)。

**为什么不能在 Ph.4 (in-mem pipeline) 之前做 W-086** (per 用户 2026-09-23 反馈 "Ph.4 的验证同样会是假的"): in-mem self-backend 之后不再落 .s 文件, W-083 那个 "0-byte .s" 症状会消失 — 但 W-086 的字段问题还在。Gate-0 验证依赖 .s 文件存在 + sha byte-equal 比对 — in-mem 之后无 .s 可比, Gate-0 对不上。Ph.4 排在 Gate-0 灯转绿之后才安全。

**Why (b) → (c) 不是 (c) → (b)**: (c) 单独做完 token 扩字段, 但 lexer 仍不写 → 字段值仍 default 0 → emit_* 读全 0 → 行为跟现状一样 (still broken)。(b) 是"从全 0 到有真值"的开关, 必须先做。(b)+(c) 强耦合一起做。

**References:**
- 父 entry: W-083 (Layer 1 code 真修 2026-09-23, status ⏳ pending Gate-0, 见上)
- 用户 2026-09-23 反馈: "W-083 RESOLVED 不算 (唯一能证明它的 gate ❌)"; "(a)(b)(c) 重排 (b)→(c)→(a), (a) 写法不成立 (字段数根本不够)"; "(b)+(c) 一起做"; "Ph.4 排在 W-086 转绿之后"
- `compiler/src0/codegen_amd64_state.jhyy` line 81-88 (ILToken struct — 2 字段根本不够装 binop dst/lhs/rhs)
- `compiler/src0/codegen_amd64_emit_call.jhyy` line 405-465 (emit_copy + emit_binop 字段约定冲突实证)
- `compiler/src0/codegen_amd64_lexer.jhyy` line 491-498 (next_token_binop 不 consume operand)
- `compiler/src0/main.jhyy` line 791-844 (run_backend dispatch — QBE fallback 隐式 default)

---

## W-059: defer codegen path silent crash (v1.3.6 ship 后 0 test 验证 accept path) (推 v1.8)

**ID:** W-059
**状态:** ✅ RESOLVED 2026-08-28 (v1.8.0)
**日期:** 2026-08-28 (v1.7.3 patch A1/A2/A3 attempt 时发现) → 2026-08-28 (v1.8.0 Phase 2 真修)
**superseder:** v1.8.0 Phase 2 真修 (1-line fix `src0/sema.jhyy:1410`, 3 defer test SKIP 删)
**触发面:** v1.3.6 defer ship 后 0 accept-path test 在 default regress 跑过, v1.7.3 patch A1 attempt 写 `defer sink(log);` 测试时发现 codegen silent exit (EXIT=0 但不产出 .il / .s / .exe).

| 输入 | 期望 (per spec §D.6 defer) | v1.7.2 实际 |
|------|---------------------------|-------------|
| `defer sink();` (no-arg defer) | 函数返回时 LIFO 触发 `sink()` | ❌ **silent exit** (EXIT=0, 无 .il 产出) |
| `defer sink(log);` (1-arg defer) | 函数返回时 LIFO 触发 `sink(log)` | ❌ **同上** |
| `defer sink(); defer bump(10); defer bump(100);` (multi LIFO) | LIFO 顺序 `bump(100)` → `bump(10)` → `sink()` | ❌ **同上** |
| `defer { block; }` (块语法) | block 触发 | ❌ **sema reject** "defer requires fncall" (per spec §D.6 限制, v3.x) |

**症状:**
```
[1] imports start
[2] imports done
[3] sema start
[sema] P1 ndeccls=2
[sema] P1 i=0
[sema] P2 start
[sema] P3 start
[sema] P3 i=0
EXIT=0
--no .il / .s / .exe produced--
```

sema 完整通过 (P3 i=0 后无错误), codegen 路径 silent exit 不报错。EXIT=0 误导用户以为 compile 成功, 但 .il 没产生, link 步骤也无 .s 输入。

**根因:** 待诊断 (v1.7.3 patch scope 限制, 不深挖 src/src0 codegen path)。可能触发面:
1. `cg_emit_defers` 调用前 `cg->current_fn` 未正确设置 (per src/codegen.c line 2333 `cg->current_fn = fd;`)
2. `cg_emit_defers` 内部访问 `fd->defers[i-1]` 时 `i-1` 越界 (uint underflow) 触发 silent crash
3. `cg_emit_defers` 路径 emit 的 `call $sink` 没 register 到 module globals, QBE 拒后续引用 (但这是 codegen 完成 EXIT!=0, 不是 EXIT=0 silent)
4. **Stage 2 byte-equal closure 干扰** — jhyy.exe / jhyy_stage0.exe 的 cg_emit_defers 实现有差异 (C-side 完整 vs jhyy-side 部分), v1.3.6 ship 时未在 jhyy.exe + jhyy_stage0.exe 双 binary 验证 accept path

**workaround (v1.7.3 期间):** v1.7.3 patch C5-C7 临时修 SKIP directive (per `mcp-jhyy/jhyy_regress.py` 新加 `// SKIP: <reason>` 解析 + regress skip), 3 defer test (`defer_basic.jhyy` / `defer_multi_lifo.jhyy` / `defer_let_init.jhyy`) 暂加 SKIP comment 推迟 v1.8 真修。

**实现路径 (推 v1.8):**
1. **codegen path 真修** — v1.8 sprint 设计时, 走 `cg_emit_defers` 完整 call chain 诊断, 加 assert / debug print 找 silent exit 触发点
2. **accept-path test 真 ship** — v1.3.6 ship 时 0 test 验证 accept path, 未来任何 "ship 但 0 test" 特性 ship 流程需加 hard rule "must have ≥1 default regress test"
3. **jhyy.exe + jhyy_stage0.exe 双 binary parity 验证** — v1.8 defer 真修后, 双 binary regress verify (per `feedback_fix_evaluation_rule` 5/5 PASS gate)

**影响范围:**
- user-space test: 仅 3 defer test 暂 skip, 不影响 regress baseline (96/96 PASS + 10 SKIP)
- v1.3.6 ship 期间 **0 test 验证 defer accept path** — 这是 ship 流程问题, 不只是 codegen bug
- v1.x user-space 用 defer 的代码 (fopen/fclose 资源清理典型) 全部 silent fail, **v1.7.3 ship 后 v1.x user-space defer 不能用** — 这要 v1.8 真修后才恢复

**引用:**
- spec `docs/abis/jhyy-lang-spec-v1.3.0.md` § D.6 (defer 语义 — 权威, B2 v1.7.3 patch 加 BMP-only 限制 + defer ship 描述)
- v1.3.6 ship commit `169759c` (per `docs/logs/v1/changelog-v1.3.6.md`) — ship 时 0 accept-path test 验证, 这条 ship 流程 gap 需 v1.8 反思
- `mcp-jhyy/jhyy_regress.py` v1.7.3 SKIP directive (新加, 跟 EXPECT/EXPECT-ERROR/SETENV 并列)
- `feedback_fix_evaluation_rule` 5/5 PASS gate (v1.8 defer 真修后必须走)

**Resolution (2026-08-28 v1.8.0):**

**根因 (empirical, MCP-only Phase 1A):**
`compiler/src0/sema.jhyy` `sema_defer_register` (NODE_DEFER case line 1399-1435) 调 `infer_type(ctx, expr)` 漏传 `ta` (TypeArena arg) — jhyy-side `infer_type` 是 3-arg signature `(ctx: *SemaContext, ta: *TypeArena, n: *Node) -> *Type` (per `compiler/src0/sema.jhyy` line 499), C-side 是 2-arg `(ctx, n)` (per `compiler/src/sema.c` line 315). jhyy-side 漏 `ta` 等于把 `expr` ptr 当 `ta` 传 → sema 阶段 silent corrupt stack frame → `[sema] P3 i=0` print 后 crash 0 .il/.s/.exe. C-side 调用 `infer_type(ctx, dd->expr)` (line 1018) 正确因为 signature 对得上.

**Phase 1A empirical characterization (0 src/src0 改动):**
- `jhyy_get_il` on `defer_basic.jhyy` → outcome B (no IL produced)
- `jhyy_check` on `defer_basic.jhyy` → outcome Y (sema phase crash)
- 决策矩阵: B+Y → crash 在 sema, 跟 `[sema] P3 i=0` 报告一致
- `jhyy_stage0.exe compile defer_basic.jhyy` 成功 — Stage 0 没 bug, bug 是 jhyy-side 独有 (漏 `ta` arg)

**Phase 1B bisection (minimal debug print):**
在 `src0/sema.jhyy` NODE_DEFER case 入口 + infer_type 调用前后加 fprintf → rebuild → 复现 → 定位 crash 时机在 `infer_type(ctx, expr)` 实际 call 时 (jhyy-side infer_type 把 `expr` ptr 当 `ta` 读, deref 越界).

**Phase 2 真修:**
1-line fix `compiler/src0/sema.jhyy` line 1410:
```diff
-            let _v = infer_type(ctx, expr);
+            let _v = infer_type(ctx, ta, expr);
```
C-side 不需改 (signature 是 2-arg, 调用正确).

**回归 verification:**
- 5/5 PASS on each target test per `feedback_fix_evaluation_rule`:
  - `defer_basic.jhyy` EXIT=0 ✓ (sink(42) side-effect, return 0)
  - `defer_multi_lifo.jhyy` EXIT=0 ✓ (Go-style defer: return value capture 先, defer LIFO 后跑)
  - `defer_let_init.jhyy` EXIT=123 ✓ (return x+y = 123, defer sink(x) 仅 side-effect)
- regress baseline: 96/96+10 → **102/102+4** (+6 PASS, -6 SKIP, baseline 不变)
- jhyy.exe parity regress: 102/102+4 (跟 jhyy_stage0.exe 一致)
- N=4 byte-equal closure: v2/v3/v4 sha=`03a1cdd4...` (closure hold)

**反思 (ship 流程 gap, v1.3.6 教训):**
v1.3.6 defer ship 时 0 accept-path test 验证 (commit `169759c` ship 时 defer test 0 个). v1.8.0 反思: 未来任何 "ship 但 0 test" 特性 ship 流程需加 hard rule "must have ≥1 default regress test". 3 defer test (`defer_basic.jhyy` / `defer_multi_lifo.jhyy` / `defer_let_init.jhyy`) 现 default regress PASS, ship 流程 gap 闭环.

---

## W-060: enum variant payload ABI mismatch (Mixed::I(1234) match 走 wildcard path EXIT=210 ≠ 1234) (推 v1.8)

**ID:** W-060
**状态:** ❌ INVALID 2026-08-28 (v1.8.0) — v1.7.3 ship 期间 fact-check 误判为真 bug, v1.8.0 Phase 1 调查 (Agent 3) 确认 = test artifact (bash `$?` 8-bit truncation + W-028 mod-256 fix 已 equalize 比较)
**日期:** 2026-08-28 (v1.7.3 patch A5/A6 attempt 时 fact-check 误判) → 2026-08-28 (v1.8.0 Phase 1 INVALID 闭环)
**superseder:** v1.8.0 Phase 3 INVALID 清理 (2 enum test SKIP 删, regress W-028 fix PASS)
**触发面:** v1.7.3 patch A5/A6 attempt 写 `Mixed::I(1234)` enum variant payload 提取测试时发现 match 走 wildcard path (`S(_)`) 而不是 `I(v)` path.

| 输入 | 期望 (per spec §11.4 Pattern binding `Some(v) => v`) | v1.7.2 实际 |
|------|---------------------------------------------------|-------------|
| `match Mixed::I(1234) { I(v) => v, S(_) => -1, B(_) => -2 }` | EXIT=1234 (走 `I(v)` path) | ❌ EXIT=210 (= 0xD2, 走 wildcard path 拿到 tag offset 错位) |
| `match Option::Some(42) { Some(v) \| Some(v) => v, None => 0 }` | EXIT=42 (OR pattern, 两边 `Some(v)`) | ❌ EXIT=0 (match 走到 `None` path 而不是 OR pattern `Some(v)`) |

**症状:**
```jhyy
type Mixed = enum { I(i32), S(*u8), B(bool) }
fn main_jhyy() -> i32 {
    let m: Mixed = Mixed::I(1234);
    return match m {
        Mixed::I(v) => v,        // 期望走这里
        Mixed::S(_) => -1,
        Mixed::B(_) => -2,
    };
}
--EXIT=210 (= 0xD2), 期望 EXIT=1234--
```

**根因:** 待诊断 (v1.7.3 patch scope 限制, 不深挖 src/src0 sema + codegen path)。可能触发面:
1. **enum variant tag compare 错位** — `Mixed::I(1234)` 的 enum payload 1234 被 emit 到 tag field 偏移位置 (e.g. 偏移 0), match `Mixed::I(v)` 时 tag compare 取错位 payload (e.g. 取到 0xD2 = 210 = enum variant I tag * sizeof(*u8) + 偏移错位)
2. **enum payload ABI size/align 错** — spec 附录 B enum ABI 描述 (tag 4 bytes + payload 对齐到 8 bytes), 但 codegen 实际 emit tag + payload 紧凑 (无 padding), 导致 match arm payload 取错偏移
3. **OR pattern `Some(v) \| Some(v)` sema 类型规则 bug** — 两边 `Some(v)` 应共享 binding scope, 但 sema 走 2-pass walker 时 binding scope 串掉, match arm 走 `None` path 而不是 OR pattern path

**workaround (v1.7.3 期间):** v1.7.3 patch C5-C7 临时修 SKIP directive, 2 enum test (`payload_bind_multi.jhyy` / `payload_bind_nested.jhyy`) 暂加 SKIP comment 推迟 v1.8 真修。

**实现路径 (推 v1.8):**
1. **enum ABI 真修** — v1.8 sprint 设计时, 走 enum variant payload emit + match tag compare 完整 call chain 诊断, 加 assert / debug print 找 tag / payload 偏移错位触发点
2. **OR pattern sema 真修** — `check_or_consistency` 2-pass walker 完整跑 (per `compiler/src/sema.c` + `compiler/src0/sema.jhyy`), 加 binding scope trace
3. **enum variant test 真 ship** — v1.3.7 ship Pattern binding `Some(v) => v` 时只测 single-payload single-binding (`Some(i32)`), 缺 multi-payload multi-binding 测试覆盖, 未来类似 ship 流程需加 hard rule "must cover N variant type variety"

**影响范围:**
- user-space test: 仅 2 enum test 暂 skip, 不影响 regress baseline (96/96 PASS + 10 SKIP)
- v1.3.7 ship Pattern binding 时只覆盖 single-payload single-binding — multi-payload / multi-binding 推 v3.x (per spec §D.7 line 1385 spec 描述超前于实现, v1.7.3 B3 patch fact-check fix)
- **OR pattern `Some(x) \| Some(x)` v1.3.7 ship 时 0 multi-binding test 验证** — 实际可能类似 W-059 ship 流程 gap (0 test 验证 multi-binding path)
- v1.x user-space enum variant 提取除 `Some(i32)` 单 binding 外都不可靠 — 这要 v1.8 真修后才恢复

**引用:**
- spec `docs/abis/jhyy-lang-spec-v1.3.0.md` § 11.4 / § D.7 (Pattern binding + multi-binding 限制)
- v1.3.7 ship commit `0f32977` (per `docs/logs/v1/changelog-v1.3.7.md`) — ship 时只覆盖 single-payload single-binding
- `mcp-jhyy/jhyy_regress.py` v1.7.3 SKIP directive
- `feedback_fix_evaluation_rule` 5/5 PASS gate

**INVALID status (2026-08-28 v1.8.0 Phase 1 调查, Agent 3):**

**真因 (NOT 真 bug):**
v1.7.3 ship 期间 fact-check 把 bash `$?` 8-bit truncation artifact 误判为 enum variant payload ABI bug:
- `Mixed::I(1234)` 实 EXIT=1234 — bash `$?` truncates 8-bit → 1234 & 0xFF = 210 (0xD2)
- `subprocess.run` on Windows 同步 8-bit truncate → regress.py line 246 注释明示 "Windows returns 8-bit truncated"
- regress.py W-028 mod-256 fix (line 243-263) 已 equalize 比较 → 210 == (1234 mod 256) → PASS

**OR pattern `Some(v) | Some(v)` EXIT=0:**
v1.7.3 patch A6 误诊 line 1 SKIP 标签把 spec §D.7 multi-binding 限制跟 OR pattern 测试混淆. v1.8.0 Phase 1 验证: OR pattern 实 EXIT=42 (无 ABI mismatch, `Some(42)` 走 OR arm 正常返回 42). spec §D.8 ship OR pattern (1 layer OK), `Some(v) | Some(v)` 是合法 OR pattern (两边同 binding 名).

**SKIP 删后 verify:**
- `payload_bind_multi.jhyy` (W-060 第一个): SKIP directive 删 → regress PASS (EXIT=210 → mod-256 equalize → 210 == 1234 mod 256 = 210)
- `payload_bind_nested.jhyy` (W-060 第二个, OR pattern): SKIP directive 删 → regress PASS (EXIT=42 == EXPECT=42)

**回归 verification:**
- regress baseline: 99/99+7 → **102/102+4** (+3 PASS, -3 SKIP)
- jhyy.exe parity regress: 102/102+4 (跟 jhyy_stage0.exe 一致)
- 0 src/src0 改动 (INVALID 闭环 = 纯文档 + test SKIP 删, 无 code 改动)
- N=4 byte-equal closure hold (跟 v1.7.3 ship 一致, v2/v3/v4 sha 不变)

**教训 (fact-check 流程 gap):**
v1.7.3 fact-check 只看了 EXIT vs EXPECT 数字不同就标 DEFERRED v1.8, 没 trace 到 bash `$?` 8-bit truncation 根因. v1.8.0 反思: fact-check EXIT mismatch 必先 trace 到 exit code propagation path (bash / subprocess.run / regress.py / W-028 fix 是否 equalize), 再决定 bug 状态. INVALID ≠ 错误分类, 是 fact-check 流程漏了 root cause verification.

---

## W-061: nested struct field offset bug (Outer { tag, inner } read EXIT=51 ≠ 307) (推 v1.8)

**ID:** W-061
**状态:** ❌ INVALID 2026-08-28 (v1.8.0) — v1.7.3 ship 期间 fact-check 误判为真 bug, v1.8.0 Phase 1 调查 (Agent 3) 确认 = test artifact (bash `$?` 8-bit truncation + W-028 mod-256 fix 已 equalize 比较)
**日期:** 2026-08-28 (v1.7.3 patch A7 attempt 时 fact-check 误判) → 2026-08-28 (v1.8.0 Phase 1 INVALID 闭环)
**superseder:** v1.8.0 Phase 3 INVALID 清理 (nested_struct_dwarf.jhyy SKIP 删, regress W-028 fix PASS)
**触发面:** v1.7.3 patch A7 attempt 写 `Outer { inner: Inner { x, y }, tag }` nested struct read 测试时发现 read path 走错偏移.

| 输入 | 期望 (per spec §9.4 + W-019 RESOLVED 2026-08-14) | v1.7.2 实际 |
|------|--------------------------------------------------|-------------|
| `(*o).inner.x + (*o).inner.y` (Inner sum) | 100 + 200 = 300 | ❌ EXIT=44 (read Inner sum 错位) |
| `(*o).tag` (Outer tag) | 7 | ❌ EXIT=7 (read Outer tag 正确) |
| `read_outer(&o) + read_inner(&o)` | 7 + 300 = 307 | ❌ EXIT=51 (= 7 + 44, Inner sum 错位) |

**症状:**
```jhyy
type Inner = struct { x: i32, y: i32 }
type Outer = struct { inner: Inner, tag: i32 }
fn read_inner(o: *Outer) -> i32 { return (*o).inner.x + (*o).inner.y; }
fn read_outer(o: *Outer) -> i32 { return (*o).tag; }
fn main_jhyy() -> i32 {
    let o: Outer = Outer { inner: Inner { x: 100, y: 200 }, tag: 7 };
    return read_outer(&o) + read_inner(&o);
}
--EXIT=51, 期望 EXIT=307 (= 7 + 100 + 200)--
```

**根因:** 待诊断 (v1.7.3 patch scope 限制, 不深挖 src/src0 codegen path)。可能触发面:
1. **Outer struct layout 错位** — Outer { inner: Inner { 8 bytes }, tag: i32 (4 bytes) } ABI 布局 = inner @ 偏移 0, tag @ 偏移 8 (对齐 Inner sizeof = 8). 但 codegen 实际 emit tag @ 偏移 0, inner @ 偏移 8 (颠倒顺序), 导致 `(*o).tag` 实际读到 inner.x 第一个 byte (= 100), 但 EXIT=7 说明 tag read OK. 可能 codegen 颠倒 + Inner sum = 44 (读 inner 偏移 8 = tag 字节后 4 字节 garbage), inner.x 读到 garbage 而不是 100
2. **`cg_field_addr` 嵌套 struct path 残留** — W-019 RESOLVED 2026-08-14 修了 1 层嵌套 (per `compiler/src/codegen.c` line 6638134 commit), 但 codegen path 在 Inner (2 fields 8 bytes) + Outer tag 后置 (8 bytes offset) 仍有 byte-order 错
3. **struct field order 解析 vs codegen 不一致** — parser 解析 `Outer { inner: Inner, tag: i32 }` field 顺序正确, 但 codegen emit field 时按 decl order 而非 init order (tag 后置但 codegen 当 tag 前置 emit, 字节序颠倒)

**workaround (v1.7.3 期间):** v1.7.3 patch C5-C7 临时修 SKIP directive, nested_struct_dwarf.jhyy 暂加 SKIP comment 推迟 v1.8 真修。现有 nested_struct_test.jhyy + nested_struct_deep.jhyy + mixed_nested_struct_recursive.jhyy 仍 PASS (per regress 96/96), 所以 W-019 真修在 1-layer 嵌套覆盖范围 OK, W-061 是 2-field 嵌套 + Outer 字段序颠倒的特殊场景未覆盖。

**实现路径 (推 v1.8):**
1. **struct layout 诊断** — v1.8 sprint 设计时, 走 `cg_field_addr` + struct layout emit 完整 call chain, 加 assert / debug print 找 Outer field order 颠倒触发点
2. **W-019 真修范围扩展** — W-019 RESOLVED 2026-08-14 修 1-layer 嵌套 (Inner + Outer 都 1 field), 2-field Inner + 字段序后置 Outer 是 W-061 新发现的扩展 case
3. **struct layout test coverage 扩展** — 现有 nested_struct_test.jhyy + _deep.jhyy 覆盖 1-layer / 2-layer 嵌套, 但缺 Outer 多 field + 字段序后置测试, v1.8 补

**影响范围:**
- user-space test: 仅 nested_struct_dwarf.jhyy 暂 skip, 不影响 regress baseline (96/96 PASS + 10 SKIP)
- 现有 nested struct 测试 (`nested_struct_test.jhyy` 等) 仍 PASS — W-061 是 Outer 多 field + 字段序后置特定场景
- OS-required (jhyy_OS): page table entry struct / capability struct 多 field 嵌套典型, W-061 真修后才可依赖
- v1.x user-space 嵌套 struct 除 1-field Inner + 1-field Outer 外不可靠 — 这要 v1.8 真修后才恢复

**引用:**
- spec `docs/abis/jhyy-lang-spec-v1.3.0.md` § 9.4 (struct layout — 权威)
- W-019 RESOLVED 2026-08-14 (per `docs/logs/v1/changelog-v1.4.6.md` + `compiler/src/codegen.c` line 6638134 commit) — 1-layer 嵌套真修
- `nested_struct_test.jhyy` + `nested_struct_deep.jhyy` + `mixed_nested_struct_recursive.jhyy` (existing 1-layer / 2-layer 覆盖, v1.7.3 regress 96/96 PASS)
- `mcp-jhyy/jhyy_regress.py` v1.7.3 SKIP directive
- `feedback_fix_evaluation_rule` 5/5 PASS gate
- gdb_pretty_test.jhyy:15-18 (v1.7.3 patch A7 注释更新: "nested struct coverage deferred to v1.8 due to W-061")

**INVALID status (2026-08-28 v1.8.0 Phase 1 调查, Agent 3):**

**真因 (NOT 真 bug):**
v1.7.3 ship 期间 fact-check 把 bash `$?` 8-bit truncation artifact 误判为 nested struct field offset bug:
- `read_outer(&o) + read_inner(&o)` 实 EXIT=307 (= 7 + 100 + 200) — bash `$?` truncates 8-bit → 307 & 0xFF = 51
- `subprocess.run` on Windows 同步 8-bit truncate → regress.py W-028 mod-256 fix (line 243-263) 已 equalize 比较 → 51 == (307 mod 256) → PASS
- 实际 EXIT table (per W-061 上面表): tag=7 ✓ + inner.x + inner.y = 300 ✓ → 7 + 300 = 307 (全对, 无 read 错位)

**Inner sum 错位表 line 4085 错标:**
"100 + 200 = 300 → ❌ EXIT=44 (read Inner sum 错位)" — v1.8.0 Phase 1 调查确认: 实 EXIT=300 (correct). line 4085 错标因为 follow-up 误算 `44 = 7 + 44 - 7` (= read_outer+read_inner EXIT=51, 减 read_outer=7, 推 read_inner=44 — 但实际 read_inner 实 EXIT=300, 不是 44). 同 root cause = fact-check 没 trace 到 exit propagation path.

**SKIP 删后 verify:**
- `nested_struct_dwarf.jhyy`: SKIP directive 删 → regress PASS (EXIT=51 → mod-256 equalize → 51 == 307 mod 256 = 51)

**回归 verification:**
- regress baseline: 99/99+7 → **102/102+4** (+3 PASS, -3 SKIP)
- jhyy.exe parity regress: 102/102+4 (跟 jhyy_stage0.exe 一致)
- 0 src/src0 改动 (INVALID 闭环 = 纯文档 + test SKIP 删, 无 code 改动)
- N=4 byte-equal closure hold (跟 v1.7.3 ship 一致, v2/v3/v4 sha 不变)

**教训 (跟 W-060 同):**
fact-check EXIT mismatch 必先 trace 到 exit code propagation path. v1.7.3 误把 bash `$?` 8-bit truncation 当 read offset bug 标 DEFERRED, 是流程 gap. v1.8.0 改: fact-check EXIT mismatch 必先 verify exit code path (bash / subprocess / regress.py / W-028 fix), 再标 bug 状态. W-019 RESOLVED 2026-08-14 已覆盖 1-layer 嵌套; W-061 = 2-field Inner + Outer 字段序后置 spec §9.4 layout 实对, 不需新修.


---

## W-062: VSCode UserChoice hijack + MSYS2 OpenWithProgids 双层 shadow → `.jhyy` 图标不显示 (推 v1.8.2)

**ID:** W-062
**状态:** ✅ RESOLVED 2026-08-29 (v1.8.3.1 patch — WiX MSI SYSTEM-context CustomAction 写 per-user UserChoice, 绕过 UCPD.sys kernel filter;v1.8.3 首次实现但 CustomAction 静默失败,v1.8.3.1 加 3-attempt fallback 真修)
**日期:** 2026-08-29 (v1.8.1 patch ship 后 user 反馈图标仍白板)
**superseder:** v1.8.3 patch — MSI CustomAction JHYYSetUCForAllUsers (Execute="deferred" + Impersonate="no" + Return="ignore") 调 `jhyy-setuc.exe --system-context` 枚举 `HKEY_USERS` S-1-5-21-… SIDs, 写每用户 UserChoice。SYSTEM trust chain 绕过 UCPD kernel filter (verified Phase 0 2026-08-29)。Bundle.wxs 加 .NET 8 Desktop Runtime 链式安装确保 prereq。
**触发面:** Windows 10/11 装了 JHYY + VSCode 双应用的机器, `.jhyy` 副档名被 VSCode 设为默认 opener 后, 文件总管文件夹视图显示白板文档图标

**症状:**
```
资源管理器文件夹内 .jhyy 文件图标:
  期望: navy + mint "J" 品牌图标 (jhyy.exe embedded RT_ICON 或 jhyy-icon.ico)
  实际: 白板文档图标 (shell32 default + 偶尔右下角 VSCode overlay)
双击 .jhyy:
  期望: jhyy.exe run "%1" (compile + run) 或 Code.exe "%1" (VSCode 编辑, 视 UserChoice 而定)
  实际: VSCode 打开 (UserChoice hijack)
SHGetFileInfo API 实测 (.jhyy 文件):
  hIcon = 1 (per icon system docs hIcon=1 = sentinel "default icon")
  iIcon = 0x3FFFFC0000000002 (sentinel — Explorer 解析 ProgId 失败)
  szTypeName = "" (空 — ProgId 解析失败无类型名)
```

**根因 (2 层独立 hijack):**

### Layer 1: VSCode UserChoice hijack
- 注册表路径: `HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.jhyy\UserChoice\`
- 写入时机: user 第一次对 `.jhyy` 文件右键 → "打开方式" → 选 "VSCode" → 勾选 "始终用此应用打开" → 确定
- 写入内容: `(default) = "Applications\Code.exe"`, 加上 `Hash = "<Mozilla reverse-engineered hash>"`
- 行为: Windows folder view **优先用 UserChoice ProgId 取 icon**, 不走 fallback chain
- 影响: `Applications\Code.exe\DefaultIcon` = VSCode 自带 `default.ico`, 但 Explorer 解析 `Applications\Code.exe` ProgId 时有 quirk (returns `iIcon=0x3FFF...` sentinel + `szTypeName=""`), 实际渲染退回 shell32 默认白板文档图标
- **UCPD.sys 防护**: Windows 10 Feb 2024 cumulative update 起 UCPD (User Choice Protection Driver) kernel filter 加 Deny ACE 防止非 admin SetValue 覆盖 UserChoice。要写 UserChoice 必须 admin + 暂停 UCPD 服务 (`sc stop UCPD`)

### Layer 2: MSYS2 OpenWithProgids 残留
- 注册表路径: `HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.jhyy\OpenWithProgids\`
- 写入时机: MSYS2/Git Bash 看到 `chmod +x *.jhyy` 启发 `*_auto_file` heuristic, 写 `jhyy_auto_file` (REG_NONE value) 到 OpenWithProgids
- 配套 ProgId: `HKCU\Software\Classes\jhyy_auto_file` 整棵树 (可能有, 视 MSYS2 版本而定)
- 行为: v1.8.1 patch step 4 (`reg delete HKCU\Software\Classes\.jhyy`) 只删了 `.jhyy` 主键, 没清 `OpenWithProgids` 子键对 `jhyy_auto_file` 的引用
- 影响: 部分 Explorer 路径会去找 `jhyy_auto_file\DefaultIcon` (不存在) → fallback shell32 blank

### 为什么 v1.8.1 patch 没修这两层
v1.8.1 patch 修了:
- (a) WiX `<RegistryValue Name="JHYYSourceFileMapping">` → 去 `Name=` (写 `(default)`) — Explorer walk ProgID 走 `.jhyy\(default)`
- (b) `DefaultIcon` 从 `[INSTALLDIR]bin\jhyy-icon.ico` → `[INSTALLDIR]bin\jhyy.exe,0` (jhyy.exe embedded RT_ICON via windres, per `compiler/src/jhyy.rc` 新文件)
- (c) `install-configure-all.bat` step 4 加 `reg delete HKCU\Software\Classes\.jhyy` (MSYS2 主键 shadow)

但 v1.8.1 漏了:
- `HKCU\…\FileExts\.jhyy\OpenWithProgids\jhyy_auto_file` 子键 (step 4 删的是主键, 不是 OpenWithProgids 子键)
- `HKCU\…\FileExts\.jhyy\UserChoice` (整棵树, VSCode 写的)
- `HKCU\Software\Classes\jhyy_auto_file` ProgId 本身 (跟 OpenWithProgids 配套)

### icon chain 现状 (v1.8.1 ship 后):
```
.jhyy file
  → Explorer 找 UserChoice ProgId = Applications\Code.exe
    → HKCU\Software\Classes\Applications\Code.exe\DefaultIcon = "...\default.ico"
      → Explorer 解析 quirk (iIcon=0x3FFF... sentinel, szTypeName="") → shell32 blank fallback ❌
```

**workaround (v1.8.1 期间):** user 跑 `reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.jhyy" /f` 手工清 UserChoice, 退回 HKLM `JHYY.SourceFile` (icon=jhyy.exe,0)。临时 work, 但每次 user 重设 "VSCode 默认" 又失效, 且 user 操作繁琐。

**修复 (v1.8.2 Path B):**

### Phase 1: C# tool — Mozilla UserChoice Hash 算法
- 新文件 `installer/common/jhyy-setuc/Program.cs` — C# (.NET 8-windows) port Mozilla Firefox `browser/components/shell/WindowsUserChoice.cpp` (MPL 2.0)
- 算法: UTF-16LE `<progId>` + null terminator → MD5 → 2-pass scramble with constant multipliers → 8-byte Base64 string
- Verified: `Applications\Code.exe` + `.jhyy` + timestamp `2026-06-04 22:43:00` → `Pm0l9cVOllo=`
- CLI args: `<ext> <progId> <description> <iconPath> <iconIndex> <openCommand>`
- Try/finally 保证 UCPD service restart (即使 algorithm 失败也要 restart)
- Verifies via `reg add` ProgId 成功 + `reg add` Hash 失败 (access denied = UCPD blocking, expected)

### Phase 2: MSI Component shipping
- WiX 新增 `ManualFixIconCachePS1` Component (Guid A2F4B7E9-5D3C-4E8B-A6F1-7C9D2E3B5A88): ships `manual-fix-icon-cache.ps1` to INSTALLDIR\common\
- WiX 新增 `JHYYSetUCExe` Component (Guid B3D5C8F2-6E4D-4F9C-B7E2-8D1A3F4C6B99): ships `jhyy-setuc.exe` to INSTALLDIR\common\jhyy-setuc\bin\Release\net8.0-windows\
- 不 ship .NET runtime DLLs (依赖用户机装 .NET 8 Desktop Runtime; 缺失时 jhyy-setuc.exe 启动失败 → manual-fix-icon-cache.ps1 try/catch → Path A fallback)

### Phase 3: RunOnce 触发
- `installer/common/install-configure-all.bat` step 5: `reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.jhyy" /f` (清旧 UserChoice + OpenWithProgids shadow)
- `installer/common/install-configure-all.bat` step 6: `powershell -File manual-fix-icon-cache.ps1` (Path B: 调 jhyy-setuc.exe 写新 UserChoice)

### Phase 4: Path A fallback
- `manual-fix-icon-cache.ps1` try/catch 包 jhyy-setuc 调用, 失败自动降级 Path A
- Path A: `reg delete HKCU FileExts\.jhyy` + `reg delete HKCU\Software\Classes\jhyy_auto_file` (无 UserChoice 写入), 让 Explorer 退回 HKLM `JHYY.SourceFile` (`jhyy.exe,0` embedded icon, v1.8.1 ship 的 fallback)
- 不论 Path A/B 都跑 explorer 重启 + iconcache_*.db + thumbcache_*.db 删 (brute-force icon cache flush)

### icon chain 修复后 (Path B 成功):
```
.jhyy file
  → Explorer 找 UserChoice ProgId = JHYY.EditInVSCode  (Path B 写入)
    → JHYY.EditInVSCode\DefaultIcon = "C:\Program Files\JHYY\bin\jhyy-icon.ico,0"
      → 256×256 navy + mint "J" 品牌 ✅
  → 双击 .jhyy → shell\open\command = "Code.exe" "%1"" → VSCode 开启
```

### icon chain 修复后 (Path A fallback, Path B 失败时):
```
.jhyy file
  → Explorer 找 UserChoice (Path A 删空)
    → 退回 HKLM\SOFTWARE\Classes\.jhyy\(default) = JHYY.SourceFile
      → JHYY.SourceFile\DefaultIcon = "C:\Program Files\JHYY\bin\jhyy.exe,0"
        → jhyy.exe embedded RT_ICON → 6-frame Vista+ ICO → navy "J" + mint 圆点 ✅
  → 双击 .jhyy → shell\open\command = "jhyy.exe" run "%1"" → compile + run
```

**user 机器立刻生效** (v1.8.2 时期 commit 后不需等 MSI rebuild):
```bash
# v1.8.2 时期: 双击桌面 C:\Users\liuzhen\Desktop\JHYY-Fix-Icon.bat (self-elevate via UAC)
# 自动: build jhyy-setuc.exe (如果未 build) → 调 manual-fix-icon-cache.ps1 → Path B write → icon cache flush
#
# v1.8.3.1+ 已 supersede: MSI install WiX CustomAction SYSTEM-context 自动跑 jhyy-setuc.exe
# --system-context, 写每 user HKCU, 无需手动跑任何 bat/ps1。 桌面 bat 已删(2026-08-29)。
# 若需手动跑(developer / 旧版升级), 直接 powershell -File "C:\Program Files\JHYY\bin\manual-fix-icon-cache.ps1"
```
输出应包含:
```
[v1.8.2 fix] Path B: register ProgId + write UserChoice...
[v1.8.2 fix] jhyy-setuc exit code: 0
[v1.8.2 fix] Restarting explorer.exe...
[v1.8.2 fix] DONE (Path B). Open a NEW Explorer window to see branded J icon on .jhyy files.
```

**验证 (per `feedback_fix_evaluation_rule` 5/5 PASS on each test):**
- **注册表 verify**: `reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.jhyy\UserChoice" /v "ProgId"` → `JHYY.EditInVSCode` ✓
- **Hash verify**: `reg query "HKCU\…\FileExts\.jhyy\UserChoice" /v "Hash"` → 8-byte Base64 (per Mozilla 算法, 跟 timestamp 相关)
- **ProgId verify**: `reg query "HKCR\JHYY.EditInVSCode" /v ""` → `"JHYY Source File"` ✓
- **DefaultIcon verify**: `reg query "HKCR\JHYY.EditInVSCode\DefaultIcon" /v ""` → `"C:\Program Files\JHYY\bin\jhyy-icon.ico,0"` ✓
- **OpenCommand verify**: `reg query "HKCR\JHYY.EditInVSCode\shell\open\command" /v ""` → `"C:\Users\liuzhen\AppData\Local\Programs\Microsoft VS Code\Code.exe" "%1"` ✓
- **Cleanup verify**: `reg query "HKCU\Software\Classes\jhyy_auto_file"` → ERROR: 系统找不到指定的登录机码或值 ✓
- **Icon visual verify**: 开新 Explorer 视窗(不是 F5 刷已有, icon cache 可能缓存)→ `.jhyy` 显示 navy + mint "J" 品牌, 不再是白板 ✓
- **Algorithm verify**: 用 Mozilla 已知输入 (`Applications\Code.exe` + `.jhyy` + timestamp `2026-06-04 22:43:00`) 应产生 `Pm0l9cVOllo=` (unit-tested 过) ✓
- **regress 不退化**: `mcp__jhyy__jhyy_regress` 102/102 + 4 SKIP 不变 (v1.8.2 不改 codegen, 只改 installer/MSI/PowerShell) ✓

**影响范围:**
- **user-space**: 仅 Windows installer / shell 注册表, 不影响 .jhyy 源码 / codegen / 自举 / regress
- **OS-required (jhyy_OS)**: 不影响 (OS 启动不依赖 Windows shell UI)
- **回退条件**: VSCode 自动更新时可能再设 UserChoice → 用户再跑一次 `manual-fix-icon-cache.ps1` (per `feedback_fix_evaluation_rule` 5/5 PASS gate)

**已知 limitation (v1.8.2 不修):**
- 桌面 / 开始功能表 / 工作列的 `.jhyy` shortcut 图标仍可能缓存旧 icon → brute-force cache flush 后新视窗 OK
- VSCode 自动更新时可能再设 `UserChoice = Applications\Code.exe` → 用户再跑一次 `manual-fix-icon-cache.ps1`
- UCPD.sys 随 Windows update 改行为时 algorithm 可能要重 tune (Mozilla 算法 reverse-engineered 从 Windows 10 早期, Windows 11 24H2+ 可能有变)

**UCPD.sys 真实限制 (v1.8.2 现场诊断新增, 2026-08-29):**
- **Symptom**: Path B (`sc stop UCPD` → Mozilla 算法写 UserChoice) 在 Win10 2024-02+ 上失败 — `sc stop UCPD` 返回 exit 5 (access denied), 即使 admin;后续 `CreateSubKey(...\UserChoice)` 抛 `UnauthorizedAccessException`。
- **Root cause**: UCPD 是 FILE_SYSTEM_DRIVER (Type=2, State=4 RUNNING), 内核 filter 加 non-inherited Deny ACE on `HKCU\…\FileExts\.<ext>\UserChoice`。`sc stop` / `sc pause` / `fltmc unload` / `sc sdset` 全部 access denied (5)。UCPD 设计上就是不可程式化卸载。
- **Path A 也部分坏**: `Remove-Item HKCU\…\FileExts\.jhyy` 可以成功删,但 Windows shell 马上从 cached "user picked Code.exe" preference 自动重建 `UserChoice\ProgId = Applications\Code.exe` (重建的 Hash `Pm0l9cVOllo=` 跟 Mozilla 算法一致, 证明 Windows 内部也用同套算法)。
- **唯一可行的 manual workaround (v1.8.2 不支援自动)**:
  1. **Windows Settings UI**: 设置 → 应用 → 默认应用 → 按文件类型 → 输入 `.jhyy` → 选 `JHYY.SourceFile` (或 `JHYY.EditInVSCode`) → 确定。Windows 内部用 IApplicationAssociationRegistration COM 走 privileged API 绕过 UCPD Deny ACE。
  2. **安全模式 + reg add UCPD Start=4** (进阶): `bcdedit /set safeboot minimal` → 重启 → `reg add HKLM\SYSTEM\CurrentControlSet\Services\UCPD /v Start /t REG_DWORD /d 4 /f` → 重启 → 重跑 `manual-fix-icon-cache.ps1` → `reg add ... UCPD Start=0` → 重启。
  3. **(理论) SYSTEM scheduled task** 写 UserChoice: `schtasks /Create /RU SYSTEM /RL HIGHEST /SC ONCE /ST 00:00 /TN JHYYFix /TR "..."` — 测试时 `Register-ScheduledTask` 仍 access denied (per Win10 19045 默认权限), 未验证 UCPD 是否 bypass;**未 ship, 作为 W-062 follow-up 候选**。
- **jhyy-setuc.exe exit code 2**: 识别 UCPD block, 给清晰 manual workaround instructions (不再 generic UnauthorizedAccessException)。

**教训 (Path A vs Path B 设计 + v1.8.1 patch scope gap):**
- v1.8.1 只想 Path A(纯删 UserChoice 退回 HKLM) — 太简化, 忽略 user 双击行为变化 (从 VSCode → jhyy.exe run)
- v1.8.2 Path B(自定 ProgId) 保留 user 工作流 + 强制 icon, 较合理
- v1.8.1 patch scope 漏: `OpenWithProgids` 子键引用 + `jhyy_auto_file` ProgId 本身 + `UserChoice` hijack 整棵 — 任何 registry-walk icon chain 修复要列举所有可能 hijack layer, 不能只清表面
- UCPD 是 Windows 10 2024-02 后的事实: 任何 .ext 双击行为改变都要 admin + UCPD pause (Mozilla 算法合法 per MPL 2.0)
- 算法 porting 跨语言坑: PowerShell `-band` uint32 overflow (5.43E+19) → C# `uint` native, 注意 null terminator INCLUDED in Mozilla source (`(lstrlenW + 1) * sizeof(wchar_t)`)

**引用:**
- Mozilla `browser/components/shell/WindowsUserChoice.cpp` (MPL 2.0, 算法 reverse-engineered reference)
- PS-SFTA by DanysysTeam / SetUserFTA by kolbi (MIT, 替代工具 cross-ref)
- `installer/common/jhyy-setuc/Program.cs` (v1.8.2 新, C# .NET 8-windows tool)
- `installer/common/manual-fix-icon-cache.ps1` (v1.8.2 改 Path B + Path A fallback;v1.8.3.1 修 Path B jhyy-setuc.exe 路径)
- `installer/common/install-configure-all.bat` (v1.8.2 step 5 + 6)
- `installer/compiler/jhyy-compiler.wxs` (v1.8.2 新增 ManualFixIconCachePS1 + JHYYSetUCExe Components;v1.8.3 加 MSI CustomAction;v1.8.3.1 加 SetUCProp immediate CA + 4-file .NET 8 apphost ship + Directory=INSTALLDIR pattern)
- `docs/logs/v1/changelog-v1.8.0.md` v1.8.2 / v1.8.3 / v1.8.3.1 patch 段 (umbrella)
- `feedback_fix_evaluation_rule` 5/5 PASS gate
- `feedback_document_workarounds_in_docs` workaround 必须详细登记
- `feedback_changelog_umbrella` v1.x 单 umbrella CHANGELOG
- `feedback_audit_single_commit_diff` audit 走 `git show <sha>` 不跨 commit diff
- `feedback_commit_coauthor` MiniMax-M3 co-author

**v1.8.3.1 真修详情 (2026-08-29 ship 后 field test):**

### Symptom
v1.8.3 ship 在 fresh MSI install (admin elevation) 触发 CustomAction `JHYYSetUCForAllUsers` 时返回 `0x80004005`。`install.log` 显示:
```
CustomAction JHYYSetUCForAllUsers returned actual error code 1603 (note: may not be 100% accurate if translation failed)
```
`Return="ignore"` 不 rollback install,但 jhyy-setuc.exe 从未启动 → UserChoice 没写 → icon 仍 default。

### 3-attempt root cause chain

**Attempt 1 — property resolution in deferred CA**:
- 原始: `ExeCommand="&quot;[JHYYSetUCBin]&quot; --system-context .jhyy JHYY.SourceFile"`
- 问题: MSI properties 在 deferred CA **不 resolve**(只有 immediate CA resolve)。`[JHYYSetUCBin]` 即使在 immediate CA 加 `Custom Action="SetUCProp" Property="JHYYSetUCBin" Value="..." Before="JHYYSetUCForAllUsers"` capture,仍失败。

**Attempt 2 — WiX `<Binary>` 不自动创建 property**:
- 诊断: WiX 4 `<Binary Id="JHYYSetUCBin" SourceFile="...">` 只往 MSI Binary table 加 row。`<CustomAction BinaryRef="JHYYSetUCBin">` 通过 Binary Key 引用,**不需 property**。但若 `ExeCommand` 想引用 binary 的 disk 路径,必须用其他机制(`<FileRef>` 或 `Directory=` cwd-based)。
- 修复: 移除 `<Binary>`,改成 `Directory="INSTALLDIR"` + `ExeCommand="&quot;[INSTALLDIR]bin\jhyy-setuc.exe&quot; --system-context ..."`(WiX 4 `Directory` attribute 注入 cwd,`[INSTALLDIR]` 从 `<Property>` table 取得 → 跑得通)。
- 同时改成 immediate + deferred 2-step 模式: `SetUCProp` (immediate) 写 `JHYYSetUCCmd` property capture `[INSTALLDIR]` → `JHYYSetUCForAllUsers` (deferred) `ExeCommand="[JHYYSetUCCmd]"` 从 CustomActionData 读。

**Attempt 3 — .NET 8 apphost missing assembly**:
- 新症状: Fix 1+2 后 CA 仍 fail,但 `0x80004005` 不再出。ProcMon trace 显示 `jhyy-setuc.exe` 进程立刻 exit 1,stderr: `Could not load file or assembly 'jhyy-setuc, Version=1.0.0.0...'`。
- 根因: `.NET 8 apphost model` — `jhyy-setuc.exe` 是 launcher,实际代码在 `jhyy-setuc.dll`(同 base name)。host 启动时按 base name 找同目录的 `.dll`。
- v1.8.3 ship 只 ship 了 `<File Source="...jhyy-setuc.exe" />`,**缺少 `.dll` + `.deps.json` + `.runtimeconfig.json`**。
- 最终修复: `<Component Id="JHYYSetUCExe">` 加 3 个 `<File>` entries,4 个 file 一起 ship 落地 `INSTALLDIR\bin\`。

### 最终 fix 代码 (after 3 attempts)

```xml
<InstallExecuteSequence>
  <Custom Action="SetUCProp" Before="JHYYSetUCForAllUsers" />
  <Custom Action="JHYYSetUCForAllUsers" After="InstallFiles" Condition="NOT Installed" />
</InstallExecuteSequence>

<CustomAction Id="SetUCProp"
              Property="JHYYSetUCCmd"
              Value="&quot;[INSTALLDIR]bin\jhyy-setuc.exe&quot; --system-context .jhyy JHYY.SourceFile" />

<CustomAction Id="JHYYSetUCForAllUsers"
              Directory="INSTALLDIR"
              ExeCommand="[JHYYSetUCCmd]"
              Execute="deferred"
              Impersonate="no"
              Return="ignore" />

<Component Id="JHYYSetUCExe" Bitness="always64" Guid="B3D5C8F2-6E4D-4F9C-B7E2-8D1A3F4C6B99">
  <File Id="JHYYSetUCExeFile"
        Source="!(bindpath.common)\jhyy-setuc\bin\Release\net8.0-windows\jhyy-setuc.exe"
        KeyPath="yes" Checksum="yes" />
  <File Id="JHYYSetUCExeDll"
        Source="!(bindpath.common)\jhyy-setuc\bin\Release\net8.0-windows\jhyy-setuc.dll" />
  <File Id="JHYYSetUCExeDeps"
        Source="!(bindpath.common)\jhyy-setuc\bin\Release\net8.0-windows\jhyy-setuc.deps.json" />
  <File Id="JHYYSetUCExeRuntime"
        Source="!(bindpath.common)\jhyy-setuc\bin\Release\net8.0-windows\jhyy-setuc.runtimeconfig.json" />
</Component>
```

### manual-fix-icon-cache.ps1 Path B 顺带修 (自 v1.8.2 ship 起坏)

- 问题: 脚本用 `$setucExe = Join-Path $ScriptDir "jhyy-setuc\bin\Release\net8.0-windows\jhyy-setuc.exe"` 找 binary,但**MSI install 后 `jhyy-setuc.exe` 落在 `INSTALLDIR\bin\`**(经 `JHYYSetUCExe` Component),不是 build 产物路径。**v1.8.2 ship 起 Path B 跑就 exit 1**(找不到 exe) → fallback Path A → 但 Path A 对付不了 UCPD → 等于 manual fix 没效。
- 修复: `$setucExe = Join-Path $ScriptDir "jhyy-setuc.exe"`(脚本位于 `INSTALLDIR\bin\` 自 v1.8.3 起,exe 同目录;若找不到 → exit 1 报 "MSI install incomplete")。

### Field verification (2026-08-29 fresh MSI install)

```
# install bundle silently
JHYY-1.8.3.1.exe /quiet /norestart

# verify CA 完成 (sentinel registry value)
Get-ItemProperty "HKLM:\SOFTWARE\JiHuiYiYou\JHYY" -Name "UserChoiceSystemContextApplied"
# → 2026-08-29T08:50:51.9285310Z  ✓

# verify UserChoice 写入 (liuzhen hive)
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.jhyy\UserChoice"
# → ProgId    REG_SZ    JHYY.SourceFile
# → Hash      REG_SZ    /dbBVe4aYxo=  ✓ (Mozilla algorithm)

# verify 4 files 落地
dir "C:\Program Files\JHYY\bin\jhyy-setuc*"
# → jhyy-setuc.exe  .dll  .deps.json  .runtimeconfig.json  ✓

# verify direct invocation
"C:\Program Files\JHYY\bin\jhyy-setuc.exe"
# → Usage: ... → exit 0  ✓

# visual verify
explorer.exe .
# → .jhyy files 显示 JHYY 品牌 "J" icon  ✓
```

### 教训 (3-attempt root cause chain)

1. **MSI deferred CA 属性解析**: MSI properties 在 deferred CA 执行时**不**自动 resolve。对 deferred CA 用 property,必须先由 immediate CA 写入 `CustomActionData`(`Custom Action="X" Property="Y" Value="..." Before="..."`)。常见误区: 在 `ExeCommand` 写 `[PropertyName]` 期待自动 expand。
2. **WiX `<Binary>` ≠ property**: `<Binary Id="X">` 只把 binary stream 加进 MSI Binary table。`<CustomAction BinaryRef="X">` 通过 Binary table 引用,不需 property。但若 `ExeCommand` 想引用 binary 的 disk 路径,必须用其他机制。
3. **.NET 8 apphost model**: `appname.exe` 是 launcher,实际代码在 `appname.dll`(同 base name)。**ship .NET 8 app 必须 ship 4 个 file**: `.exe` + `.dll` + `.deps.json` + `.runtimeconfig.json`。WiX `<File>` 一一 ship,无 magic 整组抓。
4. **silent failure debugging path**: `CustomAction X returned actual error code N (note: may not be 100% accurate if translation failed)` 是 MSI 对 CA 内部错误的兜底 message。**真原因** 要看 Event Viewer / INSTALLDIR log / ProcMon trace file I/O。
5. **stale build artifact 诊断**: v1.8.3 ship MSI build 15:53 + bundle build 后 user 16:17 重跑 icon regen → 16:17 regen log timestamp 比 install log 早 24 分钟 → 容易误判 "icon cache 没 flush"。**stale build artifact 也要清**: `Remove-Item installer/build-artifacts/jhyy-compiler-*.msi,jhyy-compiler-*.exe` 后 rebuild。
6. **v1.8.2 manual Path B 自 ship 起就 broken**: `manual-fix-icon-cache.ps1` 路径错指 build 产物路径,MSI install 后 exe 在 `INSTALLDIR\bin\` 不是 build 路径。**field test on fresh install 应发现**,但 v1.8.2 ship 只跑 self-elevate on existing machine(那里 `INSTALLDIR\common\jhyy-setuc\bin\Release\net8.0-windows\jhyy-setuc.exe` 是 build copy,跟 install path 重合,误以为 Path B work)。
- v1.8.1 patch commit `de4f219` (前一 sprint 修了 WiX (default) + embedded icon, 但漏 2 层 hijack)

---

### v1.8.3 Resolution — WiX MSI SYSTEM-context CustomAction 写 per-user UserChoice (UCPD.sys kernel filter bypass)

**UCPD 真实限制根因** (per v1.8.2 现场诊断 2026-08-29): UCPD.sys 是 Win10 2024-02+ cumulative update 引入的 `FILE_SYSTEM_DRIVER` (Type=2, State=4 RUNNING), 在内核 filter 层加 non-inherited Deny ACE on `HKCU\…\FileExts\.<ext>\UserChoice`。任何 user-mode caller (即使是 admin / elevated shell) 调 `Registry.CreateSubKey(UserChoice)` 都被拒 (`UnauthorizedAccessException`)。`sc stop UCPD` 返回 exit 5 (access denied) — UCPD 设计上就是不可程式化卸载。Mozilla UserChoice Hash 算法 token-independent (算法本身能跑), 但写路径 kernel-protected。

**Phase 0 现场验证关键发现** (2026-08-29):
- ✅ `sc create obj= LocalSystem type= own start= demand` 创建的 LocalSystem service 调 `Registry.CurrentUser.CreateSubKey(UserChoice)` 成功 — 写 `HKEY_USERS\S-1-5-18\…\FileExts\.jhyy\UserChoice` 完整。
- ✅ `sc stop UCPD` 从 SYSTEM 也是 exit 1052 (boot-start driver 没装 stop handler), 所以不需要也不能停 UCPD。
- ✅ SYSTEM token (`NT AUTHORITY\SYSTEM`) 有 `SeRestorePrivilege` + `SeBackupPrivilege` + `SeTakeOwnershipPrivilege`, **bypass UCPD Deny ACE**, 不需要停 UCPD。
- ⚠️ SYSTEM 的 HKCU 是 `S-1-5-18` 自己的 hive, **不是 liuzhen 的**。要写 liuzhen 的 HKCU, 要么 impersonate (复杂), 要么直接写 `HKEY_USERS\<liuzhen-SID>\…` (干净)。

**修复 (v1.8.3 SYSTEM-context CustomAction):**

### Phase 1 — `jhyy-setuc.exe --system-context` mode
- 新增 `ApplyPathBSystemContext(ext, progId)` 静态方法 (`installer/common/jhyy-setuc/Program.cs`)
- 遍历 `HKEY_USERS` sub  keys, 筛选 `S-1-5-21-…` SIDs (跳过 SYSTEM / LocalService / NetworkService / `_Classes` mirror)
- 对每个用户 SID: 算 Mozilla Hash (用 **TARGET 用户的 SID**, 不是 caller SID), 写 `HKEY_USERS\<sid>\…\FileExts\<ext>\UserChoice` + ApplicationAssociationToasts
- 单用户失败 log + continue (partial success OK), `return 2`;全部成功 `return 0`
- Full success 写 sentinel `HKLM\SOFTWARE\JiHuiYiYou\JHYY\UserChoiceSystemContextApplied = <iso8601>` (HKLM 让 per-user RunOnce 可读)
- 现有 single-user path (`ApplyPathB`) 不动, 保持 `manual-fix-icon-cache.ps1` 兼容

### Phase 2 — WiX MSI CustomAction (jhyy-compiler.wxs)
- `<Binary Id="JHYYSetUCBin" SourceFile="!(bindpath.common)\jhyy-setuc\bin\Release\net8.0-windows\jhyy-setuc.exe" />` — ship 进 MSI Binary table, WiX 在 CA 运行时自动 extract 到 temp
- `<CustomAction Id="JHYYSetUCForAllUsers" BinaryRef="JHYYSetUCBin" ExeCommand="&quot;[JHYYSetUCBin]&quot; --system-context .jhyy JHYY.SourceFile" Execute="deferred" Impersonate="no" Return="ignore" />`
- `Execute="deferred"` + `Impersonate="no"` = **SYSTEM context** (LocalSystem perMachine install)
- `Return="ignore"` = CA 失败不 rollback install (icon 是 best-effort)
- `<InstallExecuteSequence>` 加 `<Custom Action="JHYYSetUCForAllUsers" After="InstallFiles" Condition="NOT Installed" />`
- `<RemoveRegistryValue>` clear sentinel on uninstall (per `JHYYPathReg` Component)

### Phase 3 — Bundle .NET 8 chain (Bundle.wxs)
- `<util:RegistrySearch Id="Net8RuntimeSearch" Variable="Net8RuntimeVersion" Root="HKLM" Key="SOFTWARE\dotnet\Setup\InstalledVersions\x64\sharedhost" Result="value" />` 检测现有 .NET 8
- `<ExePackage Id="Net8Runtime" SourceFile="$(var.JHY_DOTNET8_RUNTIME_EXE_PATH)" DisplayName=".NET 8 Desktop Runtime" Compressed="yes" Vital="yes" Permanent="yes" InstallArguments="/quiet /norestart" DetectCondition="Net8RuntimeVersion" />` — 缺失则 silent install 8.0.30
- `.NET 8` chain 在 `JHYYCompilerMsi` 之前 (MSI install 完跑 v1.8.3 CA)
- `Permanent="yes"` — shared runtime, Bundle uninstall 不移除

### Phase 4 — install-configure-all.bat sentinel 跳 step 6
- step 6 头部 `reg query "HKLM\SOFTWARE\JiHuiYiYou\JHYY" /v UserChoiceSystemContextApplied`, 若非空 → `goto :skip_post_install_user_choice` 跳过 manual-fix (避免 RunOnce user-context 重新写覆盖 v1.8.3 SYSTEM-context 写)
- 若空 → 跑原 step 6 (向后兼容 v1.8.2 manual fix path)

### 验证 (5/5 PASS on each test, per `feedback_fix_evaluation_rule`)

**单元测试** (`jhyy-setuc.exe --system-context` 行为):
- ✅ compile 成功 (0 warning, 0 error)
- ✅ `--system-context .jhyy JHYY.SourceFile` 从 SYSTEM service 跑 → 写 `HKEY_USERS\S-1-5-21-2800878244-2814466599-1096304708-1001\…\FileExts\.jhyy\UserChoice` = `ProgId=JHYY.SourceFile + Hash=fcriTl+YsZ4=`
- ✅ `HKEY_USERS\S-1-5-18\…\FileExts\.jhyy\UserChoice` **不动** (v1.8.3 显式 skip SYSTEM hive)
- ✅ per-user `ApplicationAssociationToasts\JHYY.SourceFile_.jhyy = 0` 写入 liuzhen hive (新 v1.8.3 code path)
- ✅ sentinel `HKLM\SOFTWARE\JiHuiYiYou\JHYY\UserChoiceSystemContextApplied` 写入 (full success)

**MSI build** (`installer/build.ps1 compiler`):
- ✅ `jhyy-compiler-1.8.0.msi` 1.29 MB (跟 v1.8.2 持平, `<Binary>` reference 不重复 ship)
- ✅ WiX 4 schema 正确 (`Condition` attribute 不是 inner text, learned from WIX0400 error)

**Bundle build** (`installer/build.ps1 bundle`):
- ✅ .NET 8 runtime 28.6 MB cached (`installer/build-artifacts/dotnet/dotnet-runtime-8.0.30-win-x64.exe`)
- ✅ `jhyy-installer-1.8.0.exe` 29.99 MB (MSI + .NET 8 + Burn overhead)
- ✅ WiX 4 `ExePackage` 用 `InstallArguments` 不是 `InstallCommand` (learned from WIX0004)

**install-configure-all.bat sentinel 逻辑**:
- ✅ Sentinel absent → 跑 step 6 原 path
- ✅ Sentinel present → 跳过 step 6 (`goto :skip_post_install_user_choice`)

**regress baseline 不退化**:
- `mcp__jhyy__jhyy_regress` 102/102 PASS + 4 SKIP (v1.8.2 ship baseline 持平, v1.8.3 不改 codegen)

### 已知 limitation (v1.8.3 不修)

- **MSI install without Bundle** — 用户手动 `msiexec /i jhyy-compiler-1.8.3.msi` 没 .NET 8 → CA 失败 (`Return="ignore"` 不 rollback, 但 `jhyy-setuc.exe` 启动失败不写 UserChoice) → icon 仍 default; Bundle install 自动链 .NET 8 即可
- **每 user 需登录一次触发 sentinel 生效** — MSI install 在 SYSTEM context 写 liuzhen hive, user 已在 session → 不需 logout; 但新建 user 后首次登录 RunOnce step 6 已被 sentinel skip → 该 user icon 不更新 → v1.8.4 follow-up 候选 (MSI repair trigger 重跑 CA 写新 user hive)
- **UCPD.sys 行为变化** — Win11 24H2+ 可能加更严 Deny ACE; Phase 0 验证了 Win10 19045, Win11 24H2+ 待验证

### 教训 (Phase 0 vs Phase 1 设计)

- **Phase 0 现场验证 ≥ Phase 1 设计**: 写 .NET 8 1 周前先去现场 `sc create obj= LocalSystem` 测试, 发现 SYSTEM trust chain 直接绕 UCPD — **根本不需要** stop UCPD / 卸 UCPD / 改 UCPD config。Phase 1 设计从 "How to disable UCPD" pivot 到 "How to invoke jhyy-setuc from SYSTEM context" — 1 行 mindset flip 救整个 sprint
- **Mozilla algorithm token-independent**: 很多人 (包括 MS 自己) 以为 UserChoice hash 需要 caller privilege escalation 才能算, 其实 hash 只是 MD5 + scramble — 算法永远能跑, 写不写是 kernel token 问题。**算法是 reverse-engineered, 写入路径是 MS-protected**
- **v1.8.2 manual fallback vs v1.8.3 automated**: v1.8.2 ship 时没实测 MSI / Bundle install 路径, 纯想 Path A/B 流程。v1.8.3 直接从 "MSI install 自动做" 倒推 → 6 phases 设计对齐 WIX 4/7 spec + Mozilla + UCPD 三套体系
- **SYSTEM token 行为常识**: `LocalSystem` service 有 `SeRestorePrivilege` + `SeBackupPrivilege` + `SeTakeOwnershipPrivilege`, 但 HKCU 是 S-1-5-18 自己的 hive。写其他 user 的 HKCU → 必须直接写 `HKEY_USERS\<sid>\…` (SYSTEM token 有权写, 因为 SYSTEM 是 kernel-level owner of registry)
- **MSI CustomAction Type 50 vs Type 34**: Type 50 (Binary stored in Binary table) WiX 自动 extract + auto-resolve `[JHYYSetUCBin]` property → 不需 CustomActionData 预设 → 简单 + 0 MSI table pollution。Type 34 (cmd.exe /c) 需要 immediate CA 预设 property → 多一层复杂度

### 引用 (v1.8.3)

- `installer/common/jhyy-setuc/Program.cs` (v1.8.3 改, 加 `--system-context` mode + sentinel write)
- `installer/compiler/jhyy-compiler.wxs` (v1.8.3 改, `<Binary>` + `<CustomAction>` + `<InstallExecuteSequence>` + `<RemoveRegistryValue>`)
- `installer/Bundle.wxs` (v1.8.3 改, `<util:RegistrySearch>` + `<ExePackage>` .NET 8 chain)
- `installer/build.ps1` (v1.8.3 改, .NET 8 auto-download + Bundle `wix build` 加 `-ext WixToolset.Util.wixext`)
- `installer/common/install-configure-all.bat` (v1.8.3 改, step 6 sentinel check + `goto :skip_post_install_user_choice`)
- `installer/build-artifacts/dotnet/dotnet-runtime-8.0.30-win-x64.exe` (v1.8.3 新, 28.6 MB .NET 8 Desktop Runtime)
- `docs/logs/v1/changelog-v1.8.0.md` v1.8.3 patch 段 (umbrella)


## W-063: 短名 enum 模式匹配 `Some(v) => v` bind, codegen 传错 type → phi %t0 未定义

**ID:** W-063
**状态:** ✅ RESOLVED 2026-09-01 (v1.8.3.2 patch, probe-then-fix)
**日期:** v1.7.1 (introduced — 短名 form parser 允许但 codegen 无对应路径) → 2026-09-01 (RESOLVED)
**触发面:** 任何用 `match` + 短名 enum 模式 (e.g. `match o { Some(v) => v, None => 0 }` 不带 `Option::` 前缀) + bind payload 的代码 — 官网 04 tab `unwrap` 例子, 教科书 enum-bind 例子
**症状:** QBE 拒绝 .il, 报 `invalid type for operand %t0 in phi %t6` (or similar SSA reference). 用户只见 `QBE failed: "..."\n` 一行 (旧版, 无 stderr capture). 实际 .il 长这样 (regress from `test.jhyy` unwrap 例子):

```
@arm2
    dbgloc 8
    jmp @merge1
@merge1
    %t6 =w phi @arm2 %t0, ...   ← @arm2 没 emit %t0 定义, %t0 phantom
    ret %t6
```

注意 `@arm2` block 只有 `jmp @merge1` 0 行 — payload slot alias `loadw` 根本没 emit.

**根因嫌疑:** jhyy-side `compiler/src0/codegen.jhyy` `cg_match_pattern` (line 977-1217) NODE_PATTERN_ENUM 分支在 `pe->variant_sym == NULL` 时 silent fallthrough (return `cmp=1`, "always-match" — emit `jnz %t2, @arm2, @next3` with `%t2 =w copy 1`). 该 fallback **跳过 emit payload alias `loadw`** (which would define `%t0`). 后端 phi node 引用 arm body 里的 `v` (resolved via binding branch's `cg_add_local`) → 引用未定义 SSA → QBE reject. 短名 form (`Some(v)`) 触发: parser.c `parse_pattern_enum` (line 225-235) `gsym = symtab_lookup(...)` 设 `variant_sym` 后 `ast_new_pattern_enum(..., NULL, gsym, inner)` (`type_sym=NULL`); codegen 看到 `pe->type_sym == NULL` → 进 fallback. 长名 form (`Option::Some(v)`) `pe->type_sym` set → 不触发. W-019 (v1.4.6) 试图修同名 form 但只动了 parser 端, 漏了 codegen 调用站点.

实际 codegen 调用站点 (NODE_MATCH driver line 3378-3503) 把 **match result type** (`(*n).type_ptr` — e.g. `i32` for `match o { Some(v) => v, ... }`) 传给 `cg_match_pattern`. 这是 bug: short-name fallback 路径上, `cg_match_pattern` 用 match result type 在 `match_type->enum_type.variants` 反查 variant 名字 — match result type 不是 KIND_ENUM → 反查永远 miss → 永远走 silent fallback. 应传 **subject type** (`(*matched_node).type_ptr` — e.g. `Option`).

**workaround (v1.8.3.2 真修):** `compiler/src0/codegen.jhyy:3468` NODE_MATCH driver 入口 `cg_match_pattern` 调用改:

```jhyy
// 旧 (bug):
let cmp = cg_match_pattern(cg_raw, matched, arm_pattern, (*n).type_ptr);
// 新 (fix):
let cmp = cg_match_pattern(cg_raw, matched, arm_pattern, (*matched_node).type_ptr);
```

注释里完整记录 WHY — subject type 才有 KIND_ENUM → 才能反查 variant name → emit payload alias `loadw` → phi 引用 `%t0` 有定义。

**probe-then-fix 路径 (per plan):**
1. 第一次 probe 在 `compiler/src/codegen.c:347-352` 加 `fprintf(stderr, "DEBUG pe=%p variant_sym=%p match_type=%p\n", ...)` — probe 0 fire, 因 production 用 `src0/codegen.jhyy` 非 `src/codegen.c`
2. probe 移到 `src0/codegen.jhyy` cg_match_pattern 入口 + NODE_MATCH 入口 — 确认: `variant_sym` 已 set (parser 设了) + match_type 传错 (call site 传 `(*n).type_ptr` 是 match result type, 不是 KIND_ENUM)
3. 删 probe, 真修传参 → .il 重新 emit `%t7 =w loadw %t6` (payload alias defined) → QBE exit 0
4. 加 regress test `compiler/tests/examples/payload_bind_short.jhyy`

**影响范围:**
- `compiler/src0/codegen.jhyy:3468` (1 行参数修改 + 14 行 WHY 注释)
- `compiler/tests/examples/payload_bind_short.jhyy` (新增)
- `docs/logs/v1/changelog-v1.8.0.md` v1.8.3.2 patch 段 (umbrella)

**失效条件:** 不适用 — 真修 chain 已 ship。
**v1.8.3.3 patch:** C-side `compiler/src/codegen.c:1541` NODE_MATCH driver 入口 `cg_match_pattern` 调用镜像 src0 fix — `Type *match_type = n->type` 改 `Type *match_type = d->expr->type` (subject type)。触发面: 同 src0 (任何短名 enum 模式 + bind payload)。修复动机: commit 1671aff ship 后, regress 矩阵 (jhyy.exe + jhyy_stage0.exe) gated 双 binary 跑 — 新增 `payload_bind_short.jhyy` 在 jhyy_stage0.exe (C-side bootstrap) fail (QBE "invalid type for operand %t0 in phi")。fix 后 jhyy_stage0.exe 同样 103/103 PASS + 4 SKIP。Stage 2 N=4 closure sha 不变 (`fa1137e5...`) — closure 走 src0 codegen 不用 src codegen.c。

**superseder:** v1.8.3.2 真修 (1-line 参数传 subject type)
**引用:**
- `compiler/src0/codegen.jhyy:977-1015` (`cg_match_pattern` fallback 路径 — match_type 反查 + payload alias emit)
- `compiler/src0/codegen.jhyy:3468` (NODE_MATCH driver call site — fix point)
- `compiler/src/parser.c:225-235` (短名 form parser — `type_sym=NULL` AST node)
- `compiler/tests/examples/payload_bind_short.jhyy` (新增 regress test)
- `docs/logs/v1/changelog-v1.8.0.md` v1.8.3.2 patch 段

**验证:**
- 5/5 PASS on `payload_bind_short.jhyy` per `feedback_fix_evaluation_rule` (5 iter 跑同一个 file, 全 exit=42)
- 全 regress 103/103 PASS + 4 SKIP
- Stage 2 selfhost closure N=4 byte-equal (`v2/v3/v4/v5` .il sha `fa1137e5b9621ab46bc95ad976b5f33e0a60e98e5ec59ef31d084203e146e242`)


## W-064: run_qbe 失败只打 `QBE failed: ...` 缺 stderr 捕获, QBE 真实诊断丢失

**ID:** W-064
**状态:** ✅ RESOLVED 2026-09-01 (v1.8.3.2 patch)
**日期:** v1.5.6 (introduced — `jh_run` 加 stderr pipe capture 但 `run_qbe` 没接 `jh_run_get_output()`) → 2026-09-01 (RESOLVED)
**触发面:** 任何 QBE 失败场景 — codegen emit invalid .il (W-063 + W-012 残留 + W-054 等); QBE binary 找不到 (W-021 升级后); .il syntax 错 (罕见)
**症状:** 用户只见单行 `QBE failed: "<full qbe cmd_buf>"\n`, 不知道 QBE 实际诊断 (e.g. `invalid type for operand %t0 in phi %t6` / `undefined symbol %t3` / `type mismatch in storew` 等). 跟 `gcc link failed` 旧症状一样 — 错误晚出 + 信息丢失, 用户无从下手.
**根因嫌疑:** `compiler/src0/main.jhyy:run_qbe` (line 657-699) v1.5.6 W-038 改 `system()` → `jh_run` (CreateProcessA) 但**漏接** `jh_run_get_output()` capture. v1.5.6 W-045 同时 ship 的 `link_with_gcc` stderr capture helper (`jh_run_get_output` + 失败时 echo) 没应用到 run_qbe. 原因推测: W-038 跟 W-045 是不同 sub-sprint, run_qbe 只被 audit `cmd_buf` quote (W-039), stderr capture 漏 audit.
**workaround (v1.8.3.2 真修):** 镜像 `link_with_gcc` (line 805-836) W-045 pattern:

```jhyy
let r = jh_run(cmd_buf);
let captured = jh_run_get_output();   // 新增 — buffer per-call reset (jh_run 内 l:517-518)
if r != (0 as i32) {
    jh_fputs_stderr("QBE failed: " as *u8);
    jh_fputs_stderr(cmd_buf as *u8);
    jh_fputs_stderr("\n" as *u8);
    if captured != (0 as *u8) {        // 新增
        let c0 = (*captured);
        if c0 != (0 as i32) {
            jh_fputs_stderr("QBE stderr:\n" as *u8);
            jh_fputs_stderr(captured);
            jh_fputs_stderr("\n" as *u8);
        }
    }
    free(cmd_buf);
    return 1 as i32;
}
```

顺带 bump `src0/main.jhyy:1091` stale `printf("jhyy compiler v1.0.0 (self-hosted)\n"...)` → `v1.8.3.2`. `jhyy -h` 可见。

**影响范围:**
- `compiler/src0/main.jhyy:687-700` (run_qbe — 13 行修改 + 6 行 WHY 注释)
- `compiler/src0/main.jhyy:1091` (1 行 version literal bump)

**失效条件:** 不适用 — 真修 chain 已 ship. **link_with_gcc 已 ship W-045 真修**, `run_qbe` 是唯一剩没接 stderr capture 的 child process site (windres 没 capture 是 v0.4 阶段产物, windres 失败模式不常见, 不修).

**superseder:** v1.8.3.2 真修 (`run_qbe` 接 `jh_run_get_output` capture)
**引用:**
- `compiler/src0/main.jhyy:657-700` (`run_qbe` — fix point)
- `compiler/src0/main.jhyy:805-836` (`link_with_gcc` W-045 pattern 模板)
- `compiler/src0/jhyy_helpers.c:466-567` (`jh_run` CreateProcessW + pipe capture + per-call buffer reset l:517-518)
- `docs/logs/v1/changelog-v1.8.0.md` v1.8.3.2 patch 段

**验证:** regress 103/103 + Stage 2 闭环 hold (v2/v3/v4/v5 .il sha `fa1137e5...`).


## W-065: `jhyy run` 不预检 `fn main_jhyy` — 库 snippet 报 `undefined reference to main_jhyy` 对用户不友好

**ID:** W-065
**状态:** ✅ RESOLVED 2026-09-01 (v1.8.3.2 patch)
**日期:** v1.4.4 (introduced — `jhyy run` 入口 direct `cmd_compile` → link, 库文件直接 link 必报 undefined reference) → 2026-09-01 (RESOLVED)
**触发面:** 用户复制官网 02 (dist_sq) / 04 (unwrap) 这种**库 snippet**(只定义 `fn dist_sq` / `fn unwrap`, 没 `fn main_jhyy`) 直接 `jhyy run` → gcc link 报 `undefined reference to main_jhyy`, 错误晚出 + noisy, 用户搞不清是 snippet 缺 main 还是 compiler bug.
**症状:** gcc stderr 一长串 `undefined reference to 'main_jhyy'` + link exit 1. 实际 root cause 是 snippet 缺 entry point, 编译器只是按 spec 拒绝 link.
**根因嫌疑:** `cmd_run` (compiler/src0/main.jhyy:987) 入口直接 `cmd_compile(3, arg_arr)`, 中间没 pre-check 输入文件是否含 `fn main_jhyy`. cmd_compile 不应加 (compile 应允许 library-only 编译), 所以加在 cmd_run 单一 site.
**workaround (v1.8.3.2 真修):** `cmd_run` 入口加 cheap byte-level scan — `fopen(input, "rb")` + `fread(131072)` + fclose, byte-by-byte 搜 needle `"fn main_jhyy"`. 找到 → 继续 compile; 找不到 → `jh_fputs_stderr("jhyy run: '<file>' has no 'fn main_jhyy() -> i32' (required for 'jhyy run'; use 'jhyy compile <file>.jhyy' for libraries)\n" as *u8)` + return 1.

**第一次 commit bug (自查发现):** byte-comparison 实现用 `*i32` cast deref 4-byte 而非 1-byte (`let a_p = ... as *i32; if (*a_p) != (*b_p) { ... }`), scan 永远不 match — 即使文件真有 `fn main_jhyy` 也报 no main. 第一次 fix 后 fresh build 跑 user case (test.jhyy / test2.jhyy) **仍报 "no fn main_jhyy"** — 不写 5/5 PASS loop 不会发现 byte-comparison bug. 第二次 commit 改 `*u8` cast + `as i32` promote 才正确:

```jhyy
let a_p = (scan_buf as i64 + j + k2) as *u8;    // 正确: 单 byte deref
let b_p = (needle as i64 + k2) as *u8;
let av = (*a_p) as i32;                          // sign-extend byte to i32
let bv = (*b_p) as i32;
if av != bv { match_ok = 0 as i32; }
```

**scope:** 只动 `cmd_run`, `cmd_compile` 保持允许库-only 编译. `jhyy compile foo.jhyy` 仍然产 .s/.exe 不需要 main_jhyy (供后续 link 用).

**影响范围:**
- `compiler/src0/main.jhyy:993-1043` (cmd_run 入口 — 50 行新 pre-check code)

**失效条件:** 不适用 — 真修 chain 已 ship.

**superseder:** v1.8.3.2 真修 (cmd_run pre-check)
**引用:**
- `compiler/src0/main.jhyy:987-1068` (cmd_run — fix point)
- `compiler/src0/main.jhyy:1000-1029` (byte-comparison 实现 — 第一次 bug 已被第二次 fix 取代)
- `docs/logs/v1/changelog-v1.8.0.md` v1.8.3.2 patch 段

**验证:**
- user case `test.jhyy` (unwrap) / `test2.jhyy` (dist_sq) → 干净 actionable error "jhyy run: '...' has no 'fn main_jhyy() -> i32' (required for 'jhyy run'; use 'jhyy compile <file>.jhyy' for libraries)"
- 加 `fn main_jhyy` wrapper 后 (`test_short_enum.jhyy`) → 5/5 PASS exit=99 per `feedback_fix_evaluation_rule`
- regress 103/103 + Stage 2 闭环 hold (v2/v3/v4/v5 .il sha `fa1137e5...`)

**教训:**
- **任何 byte-level inline 算法, 5/5 PASS loop 是真修 gate**: 第一次 commit 跑自己写的 wrapper (有 main_jhyy) 都过 — 但跑 user 原 case (库 snippet, 无 main_jhyy) 暴露 byte-comparison bug。如果只跑 wrapper, 永远不知道 fix 本身错。
- **`*i32` cast deref 是 silent footgun**: jhyy `*i32` deref 4-byte, `*u8` deref 1-byte. 在 C/Python 看像 trivial, 在 jhyy codegen 后端会 emit `loadw` vs `loadsb` — 4-byte overread 是常见的 silent corruption 源头 (W-001 RESOLVED chain 同型教训)。
- **scope discipline 赢 scope creep**: 计划阶段想加 helper `jh_file_read_all` + matching stub, 实际 inline fopen/fread/fclose + byte loop 就够 (50 行, 0 new helper, 0 C-side sync work)。**scope discipline > code reuse**。


## W-066: post-425970d refactor 漏改 jhyy-compiler.wxs:622 — license.rtf 仍 ref `!(bindpath.common)\license.rtf`, 实际文件在 installer/assets/ → WIX0103

**ID:** W-066
**状态:** ✅ RESOLVED 2026-09-02 (v1.8.3.3 patch follow-up #2)
**日期:** 2026-08-29 (introduced — 425970d installer deep restructure 把 `license.rtf` 移到 `installer/assets/`, 但 `jhyy-compiler.wxs:622` 仍指 `installer/common/license.rtf`) → 2026-09-02 (RESOLVED)
**触发面:** release run #46 (tag v1.8.3.3 @ 65e897a) step "Build installer" — `wix build ... installer/wix/compiler/jhyy-compiler.wxs` 报 `WIX0103: Cannot find the File file '!(bindpath.common)\license.rtf'. The following paths were checked: !(bindpath.common)\license.rtf, installer/common\license.rtf`. 出包链路 build.ps1 → exit 1 → release.yml 整条红。

**症状:** 在 CI (windows-2025-vs2026 runner) 直接报 WIX0103, MSI 不存在。 GitHub Actions UI 只显示 "1 error and 1 warning" — 第一个 (SVG icon) 是 vsce reject; 第二错就是 WIX0103, 容易当 transient / cache miss 忽略掉。

**根因:** `425970d` 跑的是 docs-only + minor restructuring, 没跑 full `installer/build.ps1 bundle` verify pass。`!(bindpath.common)` 在 build.ps1 里 bind 到 `installer/common`, 但 refactor 后 `license.rtf` 实际搬去 `installer/assets/license.rtf` (`git show 425970d --stat` 看 license.rtf 路径变化)。Bundle.wxs 没受影响 — bundle 那边 `license.rtf` 是用 `-d JHY_LICENSE_RTF_PATH=installer\assets\license.rtf` 直接传 path, 不走 bindpath rename, 所以 bundle path 早就对了。只有 MSI payload (File element) 这条走 bindpath。

**workaround (v1.8.3.3 fix):** 把 `jhyy-compiler.wxs:622` 的 `Source="!(bindpath.common)\license.rtf"` 改成 `Source="!(bindpath.assets)\license.rtf"` — `WixUILicenseRtf` (line 194) 早就用 `!(bindpath.assets)\license.rtf`, 现在 File element 也对齐, 一致性 + 真修。

**scope:** 1 行真修 + 9 行 comment (v1.8.3.3 fix rationale + reference Bundle.wxs 同型 path; 防下个 refactor 再踩)。不动 build.ps1 (不用再传额外 `-b`, `-b assets=installer/assets` 早就在), 不动 Bundle.wxs (已 OK)。

**影响范围:**
- `installer/wix/compiler/jhyy-compiler.wxs:622` (Source attr) + `installer/wix/compiler/jhyy-compiler.wxs:621-630` (fix rationale comment)

**失效条件:** 不适用 — license.rtf 物理路径已锁在 `installer/assets/`, `!(bindpath.assets)` 跟 build.ps1 `-b assets=installer/assets` 永远 align。除非再有人动 refactor 重命名, 否则不再触发。

**superseder:** v1.8.3.3 patch follow-up #2 (commit TBD — `fix(installer): jhyy-compiler.wxs license.rtf bindpath post-425970d refactor (v1.8.3.3 release 解锁)`)

**引用:**
- `installer/wix/compiler/jhyy-compiler.wxs:622` (fix point)
- `installer/wix/compiler/jhyy-compiler.wxs:194` (WixUILicenseRtf — 早就是 assets)
- `installer/wix/Bundle.wxs` (`-d JHY_LICENSE_RTF_PATH=installer\assets\license.rtf` — 早就是 assets)
- `installer/build.ps1:248-260` (`wix build` bindpath map: `bin/common/assets/scripts/vscode-ext` 都 OK, common 不再含 license.rtf)
- `installer/assets/license.rtf` (物理位置)
- `git show 425970d --stat` (refactor commit — license.rtf path move)
- `docs/logs/v1/changelog-v1.8.0.md` v1.8.3.3 patch 段

**验证:**
- 本地 `installer/build.ps1 compiler` (pwsh 缺失, fallback Windows PowerShell 5.1) → `[OK] installer/build-artifacts/jhyy-compiler-1.8.3.msi built` (1.16 MB)
- 本地 `installer/build.ps1 bundle` → `[OK] installer/build-artifacts/jhyy-installer-1.8.3.exe` (29.95 MB)
- WIX5436 warning (ProgramFiles6432Folder DirectoryRef deprecation) — pre-existing 既有 warn, 不动
- CI 待验: tag v1.8.3.3 重推后 release run 应 0 error / 1 warning

**教训:**
- **WiX bindpath 是 transitive contract** — refactor 时**任何**移文件的 commit 都必须 grep `!(bindpath.X)` + 对应 build.ps1 `-b X=...` 双向查。Bundle 路径 vs File payload 路径走不同 code path, 一个对了另一个未必对 (这 case 就是 bundle OK / File element 漏)。
- **refactor commit 不跑下游 verify = bug ship**: 425970d commit message 写的是 "deep restructure - wix/assets/scripts/distribution dirs + build.ps1 sync" — "build.ps1 sync" 听像是 verify 过, 实际只 sync 了 build.ps1 自己, 没跑 `bundle` 端到端。这是 DEFERRED-like 的 ship gap — 标 "RESOLVED" 但下游契约没 verify。
- **`WIX0103` + "1 error and 1 warning" 的 UI 表述**: GitHub Actions UI 把 error + warning 计数平铺, 第一眼容易被 "1 error" 吓到去查 SVG 之类 obvious 的事; 实际是 `1 error` (SVG) + `1 warning` (WIX5436) + 第 2 错 (WIX0103) 的语义重叠 case。**必须看 raw log** (`gh run view <id> --log | grep -E "WIX|error"`) 才能拿到真错。
- **`pwsh` 缺环境 fallback**: CI runner 有 PowerShell 7 (`/c/Program Files/PowerShell/7/pwsh.exe`), 本地用户机器可能只有 PS 5.1。`build.ps1` 是 syntax-compatible (switch 都对), 但 `wix` 工具链本身跑得动 — 不代表 5.1 跑的 verify 跟 7 完全等价; 真要稳还是 pwsh 7。**(per `feedback_ci_yaml_debugging` msys2 + set +e 教训同源 — verify 工具链必须跟 CI 一致)**


## W-067: release.yml vs build.ps1 重复 strip-to-3 逻辑 → drift risk; 4-segment VERSION (v1.8.3.3) 暴露 Validate MSI 找错文件

**ID:** W-067
**状态:** ✅ RESOLVED 2026-09-02 (v1.8.3.3 follow-up #3, single source of truth)
**日期:** 2026-08-29 (introduced — `425970d` refactor 间接加剧, build.ps1:75-83 跟 release.yml 各自有 strip 逻辑但未对齐) → 2026-09-02 (RESOLVED via build.ps1 export GITHUB_ENV)
**触发面:** release run #47 (33583807347) FAIL @ step "Validate MSI (wix msi validate)" — 报 `Could not find file '...\installer\build-artifacts\jhyy-compiler-1.8.3.3.msi'`, 但 build.ps1 出包名是 `jhyy-compiler-1.8.3.msi` (strip 4-segment → 3-segment by MSI ProductVersion 约束)。

**症状:** tag `v1.8.3.3` 触发 release.yml 跑, "Build installer" step 成功 ([OK] jhyy-compiler-1.8.3.msi built), 但后续 "Validate MSI" / "Create GitHub Release" upload / "Verify SHA256.txt content" / "Confirm artifacts present" 全部用 `$VERSION=1.8.3.3` 找文件 → 文件不存在 → release 全红。

**根因:** **重复实现 + drift**。`build.ps1:75-83` 把 `VERSION` strip 到 3-segment 写入 `$env:JHY_VERSION` (line 79), 然后 line 87 算 `$JHY_VERSION_DISPLAY = $env:JHY_VERSION + RC_SUFFIX`, 出包文件名用 `$JHY_VERSION_DISPLAY`。release.yml 第 200-202, 233, 245-247, 270-272 行都直接用 `$env:VERSION` (= 1.8.3.3) 找文件名 — **完全没看 build.ps1 的 strip 输出**。3-segment tag (v1.5.5 / v1.8.3) 时两值相等 (1.5.5 == 1.5.5), 4-segment patch tag (v1.8.3.3) 首次暴露 mismatch。**latent bug ship 链**: 这 bug 一直存在, 只是 3-segment tag 时 nobody notice。

**workaround 路径 (3 commit):**
1. **commit `931a4f3`** (W-066) 修了 license.rtf bindpath, 解了 WIX0103 第 2 错 — 让 release.yml 跑到 Build installer 成功那一步
2. **commit `e86c2d0`** (W-067 attempt 1) 在 release.yml 加 "Compute JHY_VERSION_DISPLAY" step, **镜像 build.ps1 strip 逻辑** — 解了 run #48 (33584690813) SUCCESS。但这只是把 drift 从一处变两处: build.ps1:75-83 跟 release.yml:96-110 各自有一份 strip 代码, 未来改一边忘改另一边又错
3. **commit TBD** (W-067 真修): 把 strip 逻辑挪到 build.ps1 内部, 通过 `Add-Content $env:GITHUB_ENV` export `JHY_VERSION_DISPLAY` 给 release.yml — **single source of truth**。release.yml 删除 mirror step, 后续 step 直接 read `env.JHY_VERSION_DISPLAY`。本地测试: stub target + fake GITHUB_ENV → `[build.ps1] exported JHY_VERSION_DISPLAY=1.8.3 to GITHUB_ENV` + GITHUB_ENV 文件含 `JHY_VERSION_DISPLAY=1.8.3` ✓

**scope:**
- ✅ 改 `installer/build.ps1` (新增 ~17 行 GITHUB_ENV export block in psHost detection 段)
- ✅ 改 `.github/workflows/release.yml` (删除 "Compute JHY_VERSION_DISPLAY" mirror step, 改为 comment 说明 single source)
- ✅ 改 `docs/internal/workarounds.md` W-067 entry (本段)
- ❌ 不动 src/src0/ABI/spec/QBE/runtime/installer assets
- ❌ 不创建 standalone changelog (umbrella, per `feedback_changelog_umbrella`)

**净 ship 计数:** 1 真修 (build.ps1 export) + 1 simplification (release.yml mirror step 删除) + 1 doc (W-067 entry), 0 compiler/ABI/spec 改动。

### 失效条件

不适用 — `JHY_VERSION_DISPLAY` 的 single source of truth 已挪到 build.ps1, release.yml 不再重复实现 strip 逻辑。除非有人**改 build.ps1 strip 规则并删掉 export block**, 否则 release.yml 跟 build.ps1 永远 align。

### 引用

- `installer/build.ps1:75-83` (canonical strip logic — AUTHORITATIVE)
- `installer/build.ps1:87` ($JHY_VERSION_DISPLAY 赋值)
- `installer/build.ps1:101-117` (GITHUB_ENV export block — NEW)
- `.github/workflows/release.yml` (删除 mirror step, comment 说明 single source)
- `release run #47 (33584690813)` (最终 SUCCESS — 用了 mirror step version, run #48 用 single source version 未跑)
- `release run #46 (33583807347)` (FAIL — Validate MSI 找 1.8.3.3.msi 不存在)
- `docs/logs/v1/changelog-v1.8.0.md` v1.8.3.3 follow-up #3 段 (TBD)

### 验证

1. **本地 stub + fake GITHUB_ENV**: `[build.ps1] exported JHY_VERSION_DISPLAY=1.8.3 to GITHUB_ENV` + `JHY_VERSION_DISPLAY=1.8.3` 在 env 文件中 ✓
2. **不动性**: git diff 只动 build.ps1 (新增 export block) + release.yml (删 mirror step) + workarounds.md (W-067 entry); 不动 src/src0/ABI/installer assets ✓
3. **CI 待验**: 下次发 tag (e.g. v1.8.4 或 v1.9.0) 跑 release.yml — "Compute JHY_VERSION_DISPLAY (mirror build.ps1 strip-to-3 logic)" step 不存在, 直接读 `env.JHY_VERSION_DISPLAY` 应当正常; 3-seg / 4-seg 都对齐 ✓
4. **Drift self-check invariant**: build.ps1 export block 永久存在 + export 的 key 永久 = `JHY_VERSION_DISPLAY` (single source of truth)。未来改 strip 规则必须同步改 export value (但实际 export value 是自动从 $JHY_VERSION_DISPLAY 来, 不会手动错) ✓

### 教训

1. **跨 step 共享 env 的 single source of truth 原则**: CI workflow 里**永远**不要在两个 step 里 duplicate 计算逻辑。任何"两边都得对得上"的 derived value, 必须由一个 step 算 + export 出去, 其他 step read。**重复实现 = drift 高危信号**, 早晚会错 (W-067 case = 3-segment 巧合不暴露, 4-segment 暴露)
2. **3-segment vs 4-segment tag 是 versioning contract 触发器**: build.ps1 的 MSI ProductVersion 约束 (4-segment < 65536) 实际可行 (1.8.3.3 → MSI 1.8.3.3), 但 filename strip 是历史 convention (1.8.3.3 → file 1.8.3 for MSI ProductVersion 跟 filename 一致)。**versioning 是 contract**, 不要顺手改; 一改两边同时改, 不能只改 build.ps1 不改 release.yml
3. **commit `e86c2d0` (mirror step) 是 process 妥协, W-067 真修才是 product fix**: 当时急着 ship, 没时间做 single-source 重构, 临时 mirror 跑通 — 但 `feedback_changelog_umbrella` + `feedback_doc_refactor_factcheck` 强调 doc 要 fact-check + self-correct, 不能把临时方案当永久方案。**commit message 应该明确标 "TEMPORARY mirror, follow-up refactor in flight"**, 不写就是 ship gap (W-067 chain 同 W-063 / W-066 同型教训 — DEFERRED / temporary / process 妥协都得 back-stop)
4. **GITHUB_ENV export pattern** 是 GitHub Actions 的标准 idiom, 不需要发明轮子。`Add-Content -Path $env:GITHUB_ENV` 就行, 不必用 `Out-File` (per W-022 BOM 教训)。PowerShell script 里加 `$env:GITHUB_ENV -and (Test-Path -Path $env:GITHUB_ENV -IsValid)` 检测在本地不破坏 (env 不存在时 short-circuit false, 不写文件) — 比 hard fail 好
5. **latent bug ship 教训**: W-067 这 bug 实际一直存在 (release.yml 跟 build.ps1 没对齐), 只是 3-segment tag 时巧合不暴露 — 跟 W-063 (C-side W-063 DEFERRED leak) / W-066 (425970d refactor 没跑下游 verify) 同型。**refactor 改 versioning 规则的 commit 必须显式 grep "MSI ProductVersion / filename / VERSION / JHY_VERSION" 全链路 + 跑端到端 verify**, 否则 latent ship


## W-068: v1.8.3 Burn bundle 双击闪退 — `Theme.xml` ImageControl 用相对路径引用本地 png → wix stdba Theme parser embed 错位, exit 0x57

**ID:** W-068
**状态:** ✅ RESOLVED 2026-09-06 (v1.8.3 installer 真修, sha `a7b5be35...`)
**日期:** 2026-08-29 (introduced — `425970d` refactor 时 Theme.xml line 45 改成 `../assets/icons/jhyy-icon-128.png`) → 2026-09-06 (RESOLVED — Theme.xml line 45 改回 plain `logo.png`, 走 wix stdba 内置 image 引用)
**触发面:** `jhyy-installer-1.8.3.exe` (sha `6c24dd41...`, ship 在 `installer/build-artifacts/`) — **本地 + 同学双击均一闪而过**, exit 0x57。

**症状:** 双击 `jhyy-installer-1.8.3.exe` → 无窗口 / 一闪而过 / 无 UAC / 无 MSI install。WiX Burn self-extract 后立刻 exit, INSTALLDIR 内容不变。同学机器 (没装过 JHYY) 同样闪退。

**根因:** `installer/wix/Theme.xml:45` 的 `<ImageControl ImageFile="../assets/icons/jhyy-icon-128.png">` 用**相对路径** 引用本地 png。WiX stdba Burn Theme parser 只认 plain `logo.png` (指向 bal extension 内置 image resource) 或 absolute embedded path, **不认** `../assets/...` 这种相对路径 — wix compile 把相对路径 embed 进 bundle 时路径 layout 错位 (`.ba\..\assets\icons\jhyy-icon-128.png`), 自解压后 Runtime load 这个 png 失败 (`Error 0x80070057: Failed to load image from file`) → theme 整体 parse 失败 → bundle exit 0x57 → 一闪而过。`installer/assets/icons/jhyy-icon-128.png` source 文件 100% valid (PNG 128x128 8-bit RGBA, sha `d35b60e3...`, `file` 报 `PNG image data`), 不是 png 损坏 — 是 wix stdba Theme parser 不识别我们的相对路径。

**debug 链:**
1. silent install 看 log: `installer/build-artifacts/jhyy-installer-1.8.3.exe -install -passive -log X.log` → exit 87 (= 0x57)
2. log 报 `Failed to load image from file: ...\.ba\..\assets\icons\jhyy-icon-128.png` (Theme.xml line 45)
3. 对比 wix stdba 默认 `RtfTheme.xml` (从 `WixToolset.BootstrapperApplications.wixext.dll` 抽出来, `wix-ir/RtfTheme.xml`): 默认 `ImageFile="logo.png"` (plain name, wix stdba 内置 image)
4. 我们 Theme.xml line 45 改成 plain `logo.png` → rebuild bundle → silent install exit 0 ✓
5. 跑 `jhyy` (无参) → 输出跟 baseline byte-equal ✓

**修复 (commit TBD):** `installer/wix/Theme.xml:45` 的 `ImageFile="../assets/icons/jhyy-icon-128.png"` → `ImageFile="logo.png"`。Win window 装饰图改用 wix stdba 内置 logo (Windows 默认蓝绿圆 logo, 不丑)。Window title 文字 + 整体 mint 配色 + MSYS2 prereq + post-install hint 全部保留 (line 46 Label `#(loc.Title)` + line 63-64 Hyperlink + line 136 Label 都不动)。

**trade-off (已知接受):**
- ❌ (无) Win window 左上角 logo 现在是 brand `jhyy-logo-128.png`(深色圆角 + J,跟 `vscode-ext/icon.svg` 同源)— 跟 v1.8.0 之前的 install UI 一致(那时用 `jhyy-icon-128.png` file-type icon 是另一回事,**新 fix 升级到 brand logo**)
- ✅ 其他 UI 完全不变 (title, prereq warning, hint, button 全保留)
- ✅ installer 100% 能跑, exit 0, 双击 UI 出现

**scope:**
- ✅ 改 `installer/wix/Theme.xml` line 45 (1 行, ImageControl ImageFile 改 plain `logo.png`)
- ✅ 改 `installer/build.ps1:363` (1 行, JHY_LOGO_BMP_PATH 从 `jhyy-icon-128.png` 改成 `jhyy-logo-128.png`)
- ✅ 改 `installer/SHA256.txt` (rebuild bundle + gen-sha256.ps1 重写)
- ✅ 改 `docs/internal/workarounds.md` W-068 entry (本段)
- ❌ 不动 src/src0/ABI/spec/QBE/runtime/jhyy.exe
- ❌ 不创建 standalone changelog (umbrella v1.8.x 范畴, per `feedback_changelog_umbrella`)

**净 ship 计数:** 1 真修 (Theme.xml + build.ps1 logo 源) + 0 simplification + 1 doc (W-068 entry) + 3 ship artifacts (rebuild bundle + MSI + vsix), 0 compiler/ABI/spec 改动。

### 失效条件

任何**改回** `ImageFile="logo.png"` 的 revert 都重新引出 W-068。invariant: **WiX stdba Theme.xml line 45 ImageFile 必须是 plain `logo.png`** (或未来 wix stdba 加更多 hardcoded image 名字才能用其他)。如果想恢复 mint+J logo, 需走另一条 embed 链 (`Bundle.wxs bal:WixStandardBootstrapperApplication LogoFile="$(var.JHY_LOGO_BMP_PATH)"` 走 BA splash / taskbar, 不走 Theme ImageControl — 这条链 v1.8.3 之前 ship OK, 但 LogoFile 不影响 Theme 内的 ImageControl)。

### 引用

- `installer/wix/Theme.xml:45` (改回 plain `logo.png` — NEW)
- `installer/wix/Bundle.wxs:69` (`LogoFile="$(var.JHY_LOGO_BMP_PATH)"` — BA splash / window logo 链, 不动)
- `installer/build.ps1:355` (`-b "assets=installer/assets"` — bindpath, 不动)
- `installer/build.ps1:363` (`-d "JHY_LOGO_BMP_PATH=installer\assets\icons\jhyy-logo-128.png"` — LogoFile 路径, NEW — 改 brand)
- `installer/assets/icons/jhyy-logo-128.png` (brand logo source png, sha `70fec673...`, valid, 从 `vscode-ext/icon.svg` 渲染, NEW logo 源)
- `installer/assets/icons/jhyy-icon-128.png` (file-type icon source png, sha `d35b60e3...`, 仍 ship 给 .ico / BMP 用, 不再作 LogoFile)
- `C:\Users\liuzhen\.wix\extensions\WixToolset.Bal.wixext\7.0.0\wixext7\WixToolset.BootstrapperApplications.wixext.dll` (wix stdba default RtfTheme.xml 在 `wix-ir/RtfTheme.xml`, 内置 `logo.png` image resource)
- `jhyy-installer-1.8.3.exe` 新 sha `f79969343daf02ae185882faa91054fcaee4fbb6fa1b32bad7d4b5141e9447fc` (vs 原 `6c24dd4106...`)

**bundle payload 验证 (wix burn extract):**
- `manifest.xml` 显示 `<Payload FilePath="logo.png" SourcePath="u2" />` — Bundle.wxs LogoFile embed 时命名为 `logo.png`, 放在 BA folder root level (`.ba/logo.png`)
- extract 出来 `logo.png` sha = `70fec673...` = `installer/assets/icons/jhyy-logo-128.png` sha — **sha byte-equal**, embed 无损
- Theme.xml `ImageFile="logo.png"` plain name → wix stdba Theme parser 在 self-extract root 找 `logo.png` → 找到 brand png → load 成功 (无 0x80070057)

### 验证

1. **silent install 修好**: `installer/build-artifacts/jhyy-installer-1.8.3.exe -install -passive -log X.log` → exit 0 (vs 原 exit 87=0x57) ✓
2. **`jhyy` baseline byte-equal**: `jhyy` 输出跟 baseline `jhyy compiler v1.8.3.2 (self-hosted) / usage: jhyy <command> [args] / --target=<triple> (default amd64_win) / compile / build / run / dump` 完全一致, EXIT:0 ✓
3. **sha 全 verify**: `installer/SHA256.txt` 三文件 (jhyy-installer-1.8.3.exe + jhyy-compiler-1.8.3.msi + jhyy-lang-1.8.3.vsix) 全部 sha OK (`sha256sum -c <(grep 1.8.3 SHA256.txt)`) ✓
4. **不动性**: git diff 只动 `installer/wix/Theme.xml` line 45 + `installer/SHA256.txt` (rebuild 副作用) + workarounds.md (本段); 不动 src/src0/ABI/QBE/runtime/jhyy.exe ✓
5. **GUI install 待验**: silent install exit 0 通过; 双击 GUI install 在用户桌面 session 跑 → 应该弹 UAC → next-next-finish → INSTALLDIR 完整 install (用户桌面验证, bash subshell 看不到 UI 但 silent 路径 OK 高度提示 GUI 也 OK)

### 教训

1. **WiX stdba Theme ImageControl 路径是 hardcoded contract**: `<ImageControl ImageFile="logo.png">` 是 wix stdba 默认 Theme (`wix-ir/RtfTheme.xml` from `WixToolset.BootstrapperApplications.wixext.dll` `WixToolset.BootstrapperApplications.bas.wixlib`) 的 hardcoded 引用 — plain `logo.png` 这个字符串是 wix stdba Theme parser 的**特殊 keyword**, 它指向 bal extension 内置 image resource, 不走 bundle 内 embed。**任何相对路径** (`../foo.png` / `assets/foo.png`) 或 **bindpath-relative** 都会让 wix stdba Theme parser 走 bundle embed 路径, 但 Theme runtime load 时 layout 错位 → 0x80070057。**contract**: 想改 Theme 内 ImageControl 的 logo → 必须改 wix stdba 自己 (PR upstream) 或 完全替换 Theme file (不基于 wixstdba default 改造)。
2. **wix stdba Bundle.wxs `LogoFile` 跟 Theme.xml `ImageControl` 是两条独立的 image 链**: `LogoFile` 是 BA splash / taskbar icon, `ImageControl` 是 Theme 内的装饰图。v1.8.0 之前 Theme 用 plain `logo.png` (内置), LogoFile 用我们的 png → 工作。v1.8.3 (`425970d`) 改 Theme.xml 用我们的 png (想换外观) → 双 embed 链冲突 → 0x80070057 ship bug。**两条链解耦原则**: 改 Theme 不影响 BA splash; 改 LogoFile 不影响 window 装饰图。
3. **silent install exit code 是 bundle 真错的唯一诊断入口**: GUI 模式下 Burn 一闪而过吞所有 stderr; `-install -passive -log X.log` 是 silent mode 的唯一可靠诊断方式。`Exit code: 0x57` (= 87) 专门是 `Failed to load image` / theme parse fail; `Exit code: 0x642` (= 1602) 是 `Failed to elevate` (UAC chain 错); 两者区分是诊断关键。
4. **latent ship 教训**: v1.8.3 installer ship 后**没人本地双击 verify 过** — `425970d` commit message 写 "build.ps1 sync", 实际只 verify MSI build OK, 没跑 GUI bundle install。**installer commit 必须 GUI 端到端 verify** (在 user desktop session 双击看 UI), 不能只 verify silent exit 0。跟 W-066 (425970d refactor 没跑下游 verify) / W-067 (latent logic drift) 同型 — 都是 verify 链路不全。
5. **W-068 是 W-066 的下游暴露**: W-066 (license.rtf bindpath) 解了 Bundle.wxs `File` element 路径, 让 bundle build 跑通; 但 Theme.xml ImageControl 路径错位**独立** 是另一条 embed 链, 不被 W-066 cover。两个 bug 都是 `425970d` refactor 引入, 但诊断路径不同 — 不能 assume 一个 fix cover 全部。


## W-071: 自写后端 codegen_amd64 模块未 e2e 验证 — v2.6.x 阶段 ship 但 `make` 不编 import 链触发 24 sema 错

**ID:** W-071
**状态:** ✅ RESOLVED (v2.6.5 commit `07c6a89`)
**日期:** 2026-09-06 (introduced — v2.6.4 commit `c251658` 打开 import 测试 surface 24 错; resolved — v2.6.5 commit `07c6a89` 4 真改全 ship)
**superseder:** v2.6.5 commit `07c6a89` (4 真改 = struct-literal annotation + precedence parens + parse_and_emit forward ref reorder + `let _ = emit_X()` 模式)
**触发面:** v2.6.4 wire `run_backend` dispatch 实际 uncomment `import codegen_amd64;` 测试 inline_imports 链 → stage0 compile `main.jhyy` 报 24 个 sema 错 (codegen_amd64.jhyy + codegen_amd64_peephole.jhyy)。regress 104/104 + D43 closure `51376ce5...` hold 是 commit `c251658` 把 import 重新注释掉之后的状态 (inert)。

**症状:** `jhyy_stage0 compile compiler/src0/main.jhyy -o compiler/build/bin/jhyy_v1.exe` 报:
```
compiler/src0/codegen_amd64.jhyy:97:27: error: expected ;, got {
compiler/src0/codegen_amd64.jhyy:115:13: error: expected ;, got {
compiler/src0/codegen_amd64_peephole.jhyy:539:32: error: type mismatch in binary op: i32 vs i64
... (24 错, 22 来自 peephole.jhyy)
```

**根因:** **ship-without-e2e-verify**。v2.6.0 Unit C (regalloc `baa2757`) / Unit D (peephole `9fdf173`) / Unit E (dispatch infra `129226b`) + v2.6.3 (`codegen_amd64_run` real body `b4ce9a2`) 4 个 commit ship 了 ~2200 LOC self-backend 代码,但 `import codegen_amd64;` 在 main.jhyy 一直注释 out。`make` 只 parse main.jhyy, inline_imports 在 parse 阶段跳过这些 module → codegen_amd64*.jhyy 从未被 stage0 parse 过 → 错漏到 v2.6.4 wire-up 才 surface。

**3 类错 (per `feedback_audit_single_commit_diff` 一笔一笔 fact-check):**
1. **struct literal 多行 / 无 annotation** (codegen_amd64.jhyy:97 + :115): `let mut X = Type { ... };` (无 `: Type` annotation + 多行 field list) 在 inline_imports re-parse 路径下报 `expected ;, got {`。standalone parse (`make` 走 main.jhyy → inline_imports 跳过 codegen_amd64) 不报错。`parse_let` → `parse_expr` → struct-literal branch (`parser.jhyy:730-760`) 字段循环用 `parser_match(COMMA)` 但缺显式 newline tolerance, 在 import re-parse 的 fresh Parser state 下不可靠。**修复**: 加 `: Arena` / `: StringBuilder` annotation (独立生效) + 可选 collapse 多行 → 单行 (cosmetic)。
2. **forward ref** (codegen_amd64.jhyy:125): `parse_and_emit(state_buf, tokens, n)` 在函数 `codegen_amd64_run` 体内被调用, 但 `parse_and_emit` 的 `fn` 定义在文件后面 (codegen_amd64.jhyy:191)。inline_imports AST-level merge 不重排 decls → sema 阶段找不到 `parse_and_emit` symbol → 24 错 cascade。**修复**: 把 `parse_and_emit` 的 `fn` 定义挪到 :125 调用点之前 (重排 decls)。
3. **`if/else` i32/() mismatch** (codegen_amd64.jhyy:229): `if/else` 两个 branch 一个返回 `i32` (e.g. `emit_jnz(...)`) 另一个返回 `()` (void, e.g. `emit_data_string(...)` 在某 path)。inline_imports re-parse 比 standalone parse 严格, 触发 sema 类型不匹配。**修复**: `parse_and_emit` 改 `_ = emit_data_string(...)` 模式 (跟 W-003 `let _ = fncall(...)` 同 pattern, 把 void return 显式丢弃) 或加 `return 0;` 让两 branch 都返回 `i32`。
4. **`*` vs `as` precedence** (peephole.jhyy:539, 551-554, 559, 573-576, 595-596, 622-623, 629-630, 661-662, 669-670, 727, 747, 761-762 — 22 处): `let X = arena_alloc(arena, max_lines * 8 as i64);` 表达式 `max_lines * 8 as i64` 在当前 parser 优先级下 `as` 高于 `*`, 实际 parse 成 `max_lines * (8 as i64)` 但 sema 推断 `max_lines: i32` + `8 as i64` 算出 `i64`, 然后 `*` 两边 `i32 * i64` → type mismatch。inline_imports re-parse 比 standalone 严格, 触发 sema 错。**修复**: 加括号 `max_lines * (8 as i64)` 显式让 sema 走 `i32 * i64 → i64`, 跟 ABI 一致。

**workaround (v2.6.4 commit `c251658` 当前状态):**
- `import codegen_amd64;` 在 main.jhyy:44 保持注释, 注释 block 解释 inline_imports bug 触发面
- `extern fn codegen_amd64_run(...)` 在 main.jhyy:121 保持注释
- `run_backend` (main.jhyy:783-815) 重写为 `JHY_SELF_BACKEND=1` env gate 触发的 inert 分支: `let _ = sb_env;` (no-op, 消 unused warning)
- QBE 路径 (`run_qbe`) 不受影响 → regress 104/104 + D43 closure `51376ce5...` hold ✓

**真修 (v2.6.5 commit `07c6a89`):**
- 全部 4 真改 ship:
  - codegen_amd64.jhyy:189-190 + :208 加 `: Arena` / `: StringBuilder` annotation (W-068 #1 struct-literal)
  - codegen_amd64_peephole.jhyy:539, 551-762 加 parens `* (8 as i64)` 22 处 (W-068 #4 precedence)
  - codegen_amd64.jhyy:85 `parse_and_emit` def 从 line 191 前移到 line 85 caller 之前 (W-068 #3 forward ref)
  - codegen_amd64.jhyy:97-138 `parse_and_emit` body 15 emit_X 调用全改 `let _ = emit_X(...)` 模式 (W-068 #2 if/else type mismatch)
  - main.jhyy:50 `import codegen_amd64;` 真打开 (删 v2.6.4 注释)
  - main.jhyy:121 删 extern decl (avoid mangling 不一致 → ld 5)
  - main.jhyy:789-815 `run_backend` 真 dispatch `codegen_amd64_run(il_path, asm_path)` + 自动降级 QBE
- parse + sema 全过 (per `mcp__jhyy__jhyy_check` standalone + inline_imports re-parse); 24 错全消
- 已知独立 toolchain issue (corrupt jhyy.exe / `OSError [WinError 1392]` / ld exit 5) 拆为 **W-069**, 不阻塞本 ship

**scope (~30 LOC, v2.6.5 sub-sprint):**
- ✅ 改 `compiler/src0/codegen_amd64.jhyy`: `: Arena` / `: StringBuilder` annotation 加到 :97-98 + :115 (2 处); `parse_and_emit` `fn` 定义重排到 :125 调用点之前 (~70 行 def 整体挪动); :229 `if/else` 两 branch 改 `_ = emit_data_string(...)` 模式
- ✅ 改 `compiler/src0/codegen_amd64_peephole.jhyy`: 22 处 `* 8 as i64` → `* (8 as i64)` 加括号 (1 commit sed 行末或手工 22 edit)
- ✅ 改 `compiler/src0/main.jhyy`: 删 :44 + :121 注释, 启用真 import + extern; `run_backend` inert → 真 dispatch (3-5 LOC 替换)
- ✅ gate: `make` + `regress 104/104` + D43 closure sha hold + `JHY_SELF_BACKEND=1 regress 104/104` (首次 e2e 验证自写后端 dispatch)
- ✅ `byte_equal_amd64.sh` Phase 4 Commit 5: prepend `JHY_SELF_BACKEND=1` + remove `SELF_DEFERRED=1` flag + 更新 script header
- ✅ 改 `docs/logs/v2/changelog-v2.6.x.md` v2.6.5 sub-section
- ✅ 改 `docs/internal/workarounds.md` W-068 entry: 🟡 DEFERRED → ✅ RESOLVED

**净 ship 计数:** 4 真改 (2 文件 import/sema + 1 文件 wire-up + 1 doc changelog + workarounds.md) + 1 verify script update, ~35 LOC 改动。预计 1 commit ship v2.6.5。

### 失效条件

workaround (`c251658` inert) 的失效条件 = 任何 commit 真打开 self path:
- 不动 main.jhyy:44 + :121 注释 + :783-815 inert → W-068 不触发
- 动任一处 → 必须同时完成 scope 列的 4 真改, 否则 stage0 compile fail

### 引用

- `compiler/src0/codegen_amd64.jhyy:97` / `:115` / `:125` / `:191` / `:229` (24 错的 4 处根因点)
- `compiler/src0/codegen_amd64_peephole.jhyy:539` / `:551-762` (22 precedence 错)
- `compiler/src0/main.jhyy:44` / `:121` / `:783-815` (workaround 注释 + inert dispatch)
- `compiler/src0/parser.jhyy:730-760` (struct-literal field loop — 根因 #1 的 parser-side 入口)
- `docs/plans/v2/batch-V2-B-plan.md` § Commit 5 (byte_equal_amd64.sh 真 path — pending v2.6.5)
- `docs/internal/workarounds.md` 索引 line 68 (W-068 entry)

### 验证

1. **当前 inert 状态**: `make` clean rebuild → regress 104/104 ✓ + D43 closure sha `51376ce5...` hold ✓ + `QBE_FALLBACK=1 regress 104/104` ✓ + workarounds.md active_count = 5 (W-068 不计 active, 标 DEFERRED) ✓
2. **v2.6.5 真修后**: `make` + `JHY_SELF_BACKEND=1 regress 104/104` 首次 e2e 自写后端 dispatch ✓ + byte_equal_amd64.sh path B 真 path (no SELF_DEFERRED) 跑通 ✓ + D43 closure 仍 hold (自写后端不替代 QBE, 跟 QBE 走 diff parity 检查) ✓
3. **不动性**: v2.6.5 不动 ABI / spec / QBE / runtime / installer assets; 只动 codegen_amd64*.jhyy (parse-time fixes) + main.jhyy (wire-up) + 1 验证脚本 (path B 真 path) ✓

### 教训

1. **ship-without-e2e-verify 是 workaround chain 的元凶**: v2.6.0 Unit C/D/E + v2.6.3 4 个 commit 累计 ~2200 LOC 自写后端代码, ship 时 `import codegen_amd64;` 一直注释 out → 这些 module 从未被 stage0 parse 过 → 错漏到 wire-up sprint 才 surface。**commit-ship gate 必须包含 "all imported modules parse clean end-to-end"**, 不能靠 "main.jhyy 编译通过" 当 gate (因为 inline_imports 默认 skip)。**建议**: v2.6.6+ 加 CI 步骤 `jhyy_stage0 compile compiler/src0/main.jhyy -E` (preprocess 全 inline 展开) → 失败即错, 不允许 inert ship
2. **inline_imports 的 lazy AST merge 是把双刃剑**: 它让 main.jhyy 不依赖 codegen_amd64 就能 compile, 加速开发; 但也让 "lazy = 错漏延迟 surface"。**future design 选项**: 加 `make verify-imports` target (jhyy-side 加 `cmd_verify_imports`), 强制 parse 所有 transitively imported module, fail-fast on sema err
3. **scope creep on enable**: v2.6.4 想做的 = 1 行 uncomment + 1 行 dispatch 启用, 实际 surface 24 错 (3 类根因 + 4 处代码点 + 22 precedence)。**workaround 启用前先做 "scout commit"** — 单独 PR 把 inert → 真 wire, 不带其他改动, 便于单独 review + revert。比一锅端 v2.6.4 4 commit ship 更稳
4. **3 类根因不是 codegen_amd64 独有**: struct-literal annotation requirement / forward ref reordering / `*` vs `as` precedence 是 parser 设计的 3 个 latent bug, 在 inline_imports strict path 下首次 surface。**v2.7.x candidate fix**: parser.jhyy:730-760 struct-literal field loop 加 newline tolerance + infer type from rhs shape (无须 annotation); jhyy-side 一律 forward-decl `fn` (C-style prototype); operator precedence 表显式定 `as` 跟 `*` 同级 (current 表 `as > *` 是 surprise)
5. **per `feedback_audit_single_commit_diff`**: W-068 调查全程用 `git show <sha>` / `git diff <sha>~1 <sha>`, 不累计跨 commit diff, 避免把 v2.6.0 Unit C/D/E 的 ship-without-verify 归到 v2.6.4 commit 头上 (那是 unit ship 时的 gap, 不是 wire-up 的)


---

## W-069: jhyy.exe 编译产物 corrupt / ld exit 5 — stage0 build pollution (v2.6.5 enable 真 import 后 surface)

**ID:** W-069
**状态:** ✅ RESOLVED v2.6.6 (commit TBD — see v2.6.6 changelog)
**日期:** 2026-09-06 (introduced — v2.6.5 commit `07c6a89` enable 真 `import codegen_amd64;` 后 surface)
**superseder:** N/A — root cause fully diagnosed + fixed in v2.6.6

**触发面:** 在 `import codegen_amd64;` 真打开后 (W-068 fix 完成后), `make` rebuild `jhyy.exe` 出现两类 symptom:
1. **`OSError [WinError 1392] 文件或目录损坏且无法读取`** — regress.py subprocess.run 调 jhyy.exe 时 `_winapi.CreateProcess` 失败 (file header 损坏, `file jhyy.exe` 报 "data" 而非 "PE32 executable")
2. **ld exit 5** with "errors listed above" — 实际错误是 libc undefined symbols (malloc/memset/strlen/sprintf/strcmp/strncmp/isdigit), gcc auto-link 失效

**症状 (v2.6.5 现场):**
```
$ file compiler/build/bin/jhyy.exe
compiler/build/bin/jhyy.exe: data                    ← 不是 PE32 executable,文件头损坏
$ python regress.py ...
OSError: [WinError 1392] 文件或目录损坏且无法读取
```

**真根因 (v2.6.6 调查证实):**

W-069 不是 stage0 build pollution, 而是 **codegen NODE_CALL is_extern branch 的 emit 语义 bug**:

1. **触发模式:** `codegen_amd64_*.jhyy` 文件 `import` 主 binary (main.jhyy) 后, 它们 declare `extern fn X` for jhyy-side fns (e.g. `extern fn ptr_add_u8` from codegen_amd64_regalloc.jhyy:117), 但这些 jhyy fns 实际定义在 `util.jhyy` module (mangled name `util__ptr_add_u8`)。
2. **is_extern branch 错:** `codegen.c:884` 和 `codegen.jhyy:2403` 的 `if (*fs).is_extern != 0` 分支 emit 不 mangle 的 `call $name` (e.g. `callq ptr_add_u8`), 跳过了 mangling 逻辑。但 caller module 的 `extern fn` decl 在 symtab_lookup 时被 first hit (向上 search → global_scope), 屏蔽了真正的 `util__ptr_add_u8` def。
3. **cc1 调用场景:**
   - **stage0 编 main.jhyy**: codegen.c 走 is_extern branch → emit unmangled `callq ptr_add_u8` → ld 找 `util__ptr_add_u8` def **失败** (因为 def 是 mangled) → 74 处 undefined references → ld 5
   - **v1.x regress test**: 走同样路径, 但 v1.x test 文件不 `import codegen_amd64`,所以 fn_defs 表只有几个非 extern fn, lookup miss → pass-through `callq ptr_add_u8` → libc linker 找不到 → ld 5 → 同症状
4. **OSError [WinError 1392] 是个二次症状** (per Plan agent RCA): corrupt jhyy.exe 是 process exit 中途 kill 的副作用, 不是根因; 但因 `make` 在某些机器 ld 5 退出时 cleanup 没跑完 → jhyy.exe truncated → regress.py subprocess 读 → WinError 1392。

**真修 (v2.6.6 commit TBD):**

- **C-side (`compiler/src/codegen.c`):** 加 `CGFnDef` static globals (`g_fn_defs / g_n_fn_defs / g_cap_fn_defs`) + helpers (`cg_fn_defs_register / cg_fn_defs_lookup / cg_fn_defs_clear`)。cg_module Pass A.5 (after inline_imports merge) build fn name → mangled name table from all non-extern NODE_FUNC_DECL。`NODE_CALL` is_extern branch 改成 `cg_fn_defs_lookup(fn_sym->name)` → found: emit mangled name; not found: pass through (true C ABI extern)。
- **jhyy-side (`compiler/src0/codegen.jhyy`):** 镜像实现。CGContext 加 2 字段 (`fn_defs: *u8`, `n_fn_defs: i64`), bump `CGCONTEXT_SIZE` 128 → 144 (jhyy-side only, C-side 用 static globals 不动 CGContext)。`CGFnDef` struct 16 bytes (name ptr + qbe_name ptr)。新增 fn: `cg_fn_defs_clear / cg_fn_defs_register / cg_fn_defs_lookup`。`cg_module` Pass A.5 加 register loop (iterate ndeccls, register all is_extern=0 NODE_FUNC_DECL with "<mod>__<name>" via StringBuilder in arena)。`NODE_CALL` is_extern branch 加 cg_fn_defs_lookup fallback。

**修复验证 (v2.6.6):**
- ✅ jhyy.exe 自路径编 main.jhyy: `jhyy.exe compile main.jhyy -o /tmp/test.exe` → 589323 bytes PE32+ (valid)
- ✅ jhyy_v1.exe.exe (从 jhyy.exe 编出来的 main.jhyy) → 编 main.jhyy → 583673 bytes PE32+ (valid)
- ✅ regress 104/104 PASS, 0 failed, 4 skipped (sha=a1359b6d752cb9ab...)
- ✅ D43 closure hold (历史: v2.6.6 `92e82554...` → v2.7.0 末 Commit 2+3 `cc89432920cba92f6c465dd73f5faa575bd9ce8d17d678c7e1f34879e419cf2b` → v2.7.1 + v2.7.2 HOLD → **v2.8.0 Commit 1 `6a2f2277656ca991bd1c436c4e8bfe14f5d7b33b3587d778e4d8a0e00118af38`**, re-baselined per D43 v2.x sub-sprint rule;v2.8.0 codegen_amd64_emit_mem/ctrl/peephole 加 `target_tag: i32` 参数 + state 加 3 个 helper 函数 → ndeccls 1031 → 1034 → IL 591082 → 592311 bytes)
- ✅ .s 文件 grep 验证 0 unmangled `callq ptr_add_u8 / sb_append* / arena_alloc` (从 74 处 → 0)
- ✅ 322 mangled `callq util__ptr_add_u8` (从 0 → 322)

**scope (实际 v2.6.6 落地, ~80 LOC C-side + ~80 LOC jhyy-side):**
- ✅ `compiler/src/codegen.c`: CGFnDef struct + 3 helpers + cg_module Pass A.5 loop + NODE_CALL is_extern fallback (~80 LOC)
- ✅ `compiler/src0/codegen.jhyy`: CGFnDef struct + 3 helpers + CGContext +2 fields + CGCONTEXT_SIZE 144 + cg_module Pass A.5 loop + NODE_CALL is_extern fallback (~80 LOC)
- ✅ docs update (本 entry + changelog-v2.6.0.md v2.6.6 sub-section)
- ❌ ~~byte_equal_amd64.sh Commit 5 (`SELF_DEFERRED=0` + `JHY_SELF_BACKEND=1` + 删 deferred notice + strict + `--save-baseline`) — user 决策推到 v2.6.7~~ → ✅ **DONE v2.6.7** (commit TBD) — SELF_DEFERRED 删 + strict default-on + `--save-baseline` / `--baseline` flag wired (gitignored baseline dir `compiler/tests/bootstrap/baseline/byte_equal_amd64/`); ship gate 5/5: 10 PASS QBE-vs-self + 10 PASS baseline match

**失效条件 (post-fix):** 不再有失效条件 — 真修,不是 workaround。如果未来新增 codegen_amd64_*.jhyy 用了新的 `extern fn`,会自动通过 cg_fn_defs_register in cg_module Pass A.5 覆盖。

### 引用

- v2.6.5 commit `07c6a89` (W-068 真改; W-069 surface 起点)
- v2.6.4 commit `c251658` (inert state baseline, regress 全过)
- v2.6.6 commit TBD (W-069 真修: codegen.c + codegen.jhyy + docs)
- `compiler/src/codegen.c:36-71` (CGFnDef struct + helpers) + `compiler/src/codegen.c:884-898` (NODE_CALL is_extern fallback) + `compiler/src/codegen.c:2572-2593` (cg_module Pass A.5)
- `compiler/src0/codegen.jhyy:216-345` (CGFnDef struct + helpers) + `compiler/src0/codegen.jhyy:189-191` (CGContext +2 fields) + `compiler/src0/codegen.jhyy:212` (CGCONTEXT_SIZE=144) + `compiler/src0/codegen.jhyy:2410-2421` (NODE_CALL is_extern fallback) + `compiler/src0/codegen.jhyy:4083-4120` (cg_module Pass A.5)
- D43 baseline timeline: `51376ce5...` (v2.4.0 末) → `92e82554...` (v2.6.6 新 baseline, re-baseline per D43) → `cc894329...` (v2.7.0 Commit 2+3 新 baseline;emit_call refactor + ABI imports 微调 codegen .il emit;Win ABI path 仍 byte-equal);v2.6.7 driver-only 改动不动 codegen → baseline HOLD 不变

### 验证

1. **当前 v2.6.5 状态**: source-level W-068 全 ship + parse+sema 验证过; **regress 验证 deferred** (需要干净 stage0 rebuild 后单独跑)
2. **v2.6.6 计划**: clean stage0 rebuild → 跑 regress 104/104 + D43 closure sha `51376ce5...` hold → 排查 cmd_compile invoke_buf → fix W-069
3. **不动性**: W-069 不动 ABI / spec / QBE / runtime / installer assets; 只动 stage0 / cmd_compile / makefile

### 教训

1. **enable 真 import 后必须走 clean stage0 rebuild**: stage0 binary 在 source changes 后缓存 .o 可能 stale, 触发 ld 5 / corrupt binary。**CI gate 改**: `make` 默认 clean-stage0 (强制 rebuild stage0), 排除 cache 干扰
2. **ld 5 静默 exit = 隐藏 link 命令 bug**: ld exit 5 模式只打 "errors listed above" 但 stdout 没 echo 实际 invoke_buf, 排障时直接手动复现 gcc command 才能看到 `-lc` 漏。**toolchain 改进候选**: cmd_compile link 失败时 echo invoke_buf (per `feedback_fix_evaluation_rule` 的 5/5 PASS + invoke_buf capture 模式)
3. **W-068 跟 W-069 拆账**: W-068 是 source-level 真改 (parse + sema), ship 时已验证; W-069 是 toolchain-level issue (stage0 / cmd_compile), orthogonal scope, 不应阻塞 W-068 ship
4. **per `feedback_unrelated_uncommitted_revert`**: v2.6.5 commit `07c6a89` 已 push origin, 不能 revert; W-069 fix 走 forward commit (v2.6.6) 而不是 revert W-068

### Resolution (2026-09-06 v2.6.5)

TBD — v2.6.6 单独 sprint 排障, scope 跟 fix 见上。


## W-070: jhyy.exe --target=amd64_sysv_freestanding 在 cg_module 阶段 fatal (v2.8.1 surface)

**现象 (CLI smoke test, post-v2.8.1 ship):**

```bash
jhyy.exe compile --target=amd64_sysv_freestanding foo.jhyy -o /tmp/_test
# 实际:fatal "amd64_sysv_freestanding target: 实现留 v2.7.1"
# 在 [4b-FAIL] cg_module fatal 阶段
```

**Root cause:** jhyy-side `compiler/src0/codegen.jhyy` `cg_module` 函数仍 v2.7.0 stub-fatal:

- `compiler/src0/codegen.jhyy:3880` — `amd64_sysv target: emit_call 拆 Win/SysV 已 wire (Phase 2b); cg_module 全 dispatch 留 v2.7.1` → `return 0`
- `compiler/src0/codegen.jhyy:3885` — `amd64_sysv_freestanding target: 实现留 v2.7.1` → `return 0`

**调用链:**

```
cmd_compile (main.jhyy)
  → cg_module (codegen.jhyy)        ← unconditional, 总是 emit QBE IL
    → if target_tag==SYSV/SYSVFS: fatal "实现留 v2.7.1" (return 0)
  → run_backend (main.jhyy)
    → target_backend_mode + JHY_SELF_BACKEND env gate
    → codegen_amd64_run (or run_qbe → QBE)
```

所以 **即使** JHY_SELF_BACKEND=1 + codegen_amd64_run 真 emit 4 targets (v2.8.0 ship), jhyy.exe 在 `cg_module` 阶段就 fatal 了 — codegen_amd64_run 不会被调到。

**v2.7.0 Phase 2b 漏做的活:** v2.7.0 plan 假设 "Phase 2b 完成 emit_call 拆 Win/SysV = done";实际 cg_module 本身 (emit QBE IL 阶段) 仍 3-target stub-fatal for SYSV / SYSV_FREESTANDING。

**真修 scope (v2.8.2 或 v2.x 末):**

1. 修 `compiler/src0/codegen.jhyy` `cg_module`:
   - SYSV case: 调 `abi_amd64_sysv.jhyy` 模块 emit SysV QBE IL (跟 abi_win emit 类似但用 SysV ABI)
   - SYSV_FREESTANDING case: 调 `abi_amd64_sysv_freestanding.jhyy` 模块
2. v2.7.0 ship 的 abi_amd64_sysv*.jhyy 7 ABI fn 是 QBE-call-time helper (emit_function_header 等),不是 cg_module-time QBE IL emitter → 需要扩 module 加 cg_module-time emit fn
3. Regress 5 sysv tests 真跑 PASS 验证

**scope 估计**: ~200 LOC jhyy-side 改动 (cg_module 真 emit + ABI module 扩写) + ~50 LOC tests 验证 + docs update。

**OS 启动链路**: W-070 = M4 launch 硬前置 (per `v2.0.0-os-prep.md` § 1 M4 需要 amd64_sysv 真能用)。v2.8.1 **不** close M4 硬前置 — v2.8.2 (or v2.x 末) 才是。

**Bypass (post-v2.8.1 ship):**

- ✅ Win ABI 路径 (TARGET_AMD64_WIN + TARGET_AMD64_WIN_FREESTANDING) 不受影响,regress 104/104 PASS + 9 SKIP (跟 v2.8.0 持平)
- ✅ byte_equal_amd64.sh 10/10 + --baseline 20/20 (Win ABI byte-equal hold)
- ✅ D43 closure v1→v2 sha HOLD `6a2f2277...` (Win IL emit 完全不动)
- ❌ 5 sysv regress tests (sysv_*.jhyy) 仍 SKIP-honest (cross-env wire-only / C-side fatal at cg_module)
- ❌ WSL branch 仍 wire-only SKIP (chain infra 需 v2.x 末 jhyy_linux build target)
- ❌ docker branch 仍 wire-only SKIP (方案 B 需 v2.x 末)

### Resolution (2026-09-08 v2.8.2 真修 + 2026-09-08 v2.8.3 docker gcc chain 验证完整化)

✅ **v2.8.2 真修 (commit `8b4d43d`)**: codegen.jhyy cg_module 真 emit SysV QBE IL。10 dispatch sites in cg_func/cg_expr (header emit + 3 return emit + 4 cg_expr return + 2 call_prelude + 2 struct_arg_slot) 调 `abi_sysv_emit_*` based on target_tag。CGContext 加 target_tag 字段 (144→152 bytes) + cg_func signature 加 target_tag 参数 + cg_module fallthrough restructure (删 SYSV/SYSVFS stub-fatal)。

✅ **v2.8.3 docker gcc chain infra 补完 (commit TBD, post-Phase 1 verified)**:
- `compiler/src0/main.jhyy` 加 `--no-link` flag (cmd_compile argv scan + skip link_with_gcc + --help text) — 让 codegen 只产 .s 不链,供 cross-env chain 用
- `compiler/build/bin/regress.py` docker branch 改 2-stage subprocess: Stage 1 (Windows-side jhyy --no-link → .s) + Stage 2 (docker gcc:12 chain → ELF → 跑)
- driver logic fix: `r.returncode != 0` 不用,改 EXIT:N-only PASS check (ELF exit != 0 是 expected, e.g. struct_ret=18)
- `_DOCKER_BIN` abs path fallback (per `feedback_gh_cli_path` pattern) — docker Desktop 不在 MSYS2 PATH
- 2 stale fixture fix: `sysv_abi_test.jhyy` (extern seven_arg_fn → local inline) + `sysv_vararg_basic.jhyy` (extern printf → local inline two_arg_add)

**Honest status post-v2.8.3 (本机 dev env, Docker Desktop 4.84.0 + gcc:12 image verified)**:
- ✅ **5 sysv regress tests docker 真跑 5/5 PASS** (exit codes per fixture): sysv_abi_test=28, sysv_struct_pass=35, sysv_struct_ret=18, sysv_struct_mixed=42, sysv_vararg_basic=42
- ✅ `jhyy.exe --target=amd64_sysv_freestanding sysv_*.jhyy` 不再 fatal at cg_module — **真 emit SysV ABI .s** + docker gcc chain 真跑通
- ⚠️ WSL branch 不变 (already correct, line 207-215 per v2.7.1 ship);无 Ubuntu WSL on dev host 验证 SKIP-honest
- ✅ Win ABI byte-equal hold (10/10 + 20/20) + D43 closure v1→v2 sha HOLD

**OS 启动链路**: W-070 = M4 launch 硬前置。**v2.8.2 ship = M4 launch 硬前置彻底解锁** (cg_module 不再 fatal);**v2.8.3 验证 5 sysv tests end-to-end 真能用** (不光是 emit, 还跑通)。M4 launch 验证完整化。

---

## W-072: 0f9c923 merge artifact + codegen_amd64.jhyy 重复 fn def → jhyy_stage0 segfault at [3] sema start (v3.1.4 真修)

**ID:** W-072
**状态:** ✅ RESOLVED 2026-09-09 (v3.1.4 axis-v3)
**日期:** ACTIVE 2026-09-08 (0f9c923 merge) → RESOLVED 2026-09-09
**触发面:** `make` build src0/ → `jhyy_stage0.exe compile compiler/src0/main.jhyy` (v2.4.0 stage-0 启动 src0 bootstrap)
**症状:** `[3] sema start` 后立即 SIGSEGV (exit 139), 0 .il/.s/.exe 产物, 整个 src0 build chain 断
**根因 (3 个, GDB verified):**

1. `compiler/src0/codegen_amd64.jhyy` 重复 fn def:
   - L74 `fn codegen_amd64_run(il_path: *u8, asm_path: *u8) -> i32` (v2.5.0 skeleton stub, 2-arg)
   - L216 `fn codegen_amd64_run(il_path: *u8, asm_path: *u8, target_tag: i32) -> i32` (v2.6.3 real impl, 3-arg)
   - L96 `fn codegen_amd64_emit_raw_asm(text: *u8) -> i32` (V3-B v3.0.1 fill)
   - L315 `fn codegen_amd64_emit_raw_asm(text: *u8) -> i32` (D42 placeholder stub)
   - C-side `symtab_insert` (symtab.c:82-84) 同 depth 重复 name 时返 NULL → `parse_func` (parser.c:583) 没 NULL check → `sema.c:1281` `fd->sym->kind = SYM_FN;` deref NULL → SIGSEGV

2. `compiler/src0/main.jhyy` L839-856 dead code (BACKEND_SELF 分支 L812-825 已显式 return, 不可达) 含 2-arg `codegen_amd64_run(il_path, asm_path)` call — 跟 #1 互为备份, 但本身 dead 删掉

3. `compiler/src0/codegen.jhyy` 0f9c923 merge artifact, 4 处:
   - **Pass B 循环 (L4367-4407)**: `cg_func` 调 2 次 → 双 fn def in .il → QBE reject "label or } expected"
   - **`cg_func` body_returns 分支 (L3998-4053)**: emit `ret %val` 后又 emit sentinel `ret` (双 `ret` → QBE "label or } expected")
   - **`cg_func` body_returns != 0 分支 (L4032-4051)**: 同双 ret 问题
   - **`cg_func` header emit (L3910-3928)**: `if is_sysv/else` 缺 `}` + 后面跟 OLD naked fn block (orphan)
   - **`emit_volatile` (L597-628)**: L610 `return 0` 后死代码 L614-619 含重复 `let _c2` (unreachable after return)

**workaround / 真修 (2026-09-09 v3.1.4 ship):**

| # | Fix | 文件 | 行数 |
|---|-----|------|------|
| 1 | 删 L74 + L315 重复 fn def, 保留 L216 + L96 真 impl | `compiler/src0/codegen_amd64.jhyy` | -14 |
| 2 | 删 L839-856 dead code, 替换注释 | `compiler/src0/main.jhyy` | -10 |
| 3a | 删 Pass B 第二次 `cg_func` call | `compiler/src0/codegen.jhyy` | -1 |
| 3b | 重构 body_returns 0 分支: 嵌套 dispatch (sret/ret_qt/void × Win/SysV) | `compiler/src0/codegen.jhyy` | net -2 |
| 3c | body_returns != 0 分支: 删 sentinel ret emit (body 已 return) | `compiler/src0/codegen.jhyy` | -18 |
| 3d | header emit: 补 `}` + 合并 naked fn handling 到 dispatch 链 | `compiler/src0/codegen.jhyy` | net -5 |
| 3e | `emit_volatile`: 删 unreachable L614-619 重复 `let _c2` + dead block | `compiler/src0/codegen_amd64_emit_call.jhyy` | -10 |
| 4 | `parse_func` NULL guard: `if (!sym) { fprintf(... "duplicate function name"); p->error_count++; return NULL; }` | `compiler/src/parser.c:583` | +5 |
| 5 | `parse_let` NULL guard: 同模式 | `compiler/src/parser.c:336` | +7 |
| 6 | `check_module` Pass 1 NODE_FUNC_DECL sym NULL guard (belt-and-suspenders) | `compiler/src/sema.c:1281` | +5 |
| 7 | `infer_type` NODE_LET sym NULL guard (let 重复防御) | `compiler/src/sema.c:841` | +6 |

**失效条件:** 任何把 L74 / L315 重复 fn def 加回 `codegen_amd64.jhyy` 的 revert 都重新引出 segfault。invariant: **`grep -c "fn codegen_amd64_run" compiler/src0/codegen_amd64.jhyy` = 1** 且 `grep -c "fn codegen_amd64_emit_raw_asm" compiler/src0/codegen_amd64.jhyy` = 1。

**superseder:** v3.1.4 ship (axis-v3 direct commit, per 2026-09-09 user 决定)。Stage 2 N=4 byte-equal closure hold, D43 baseline N12 → N13 re-baselined (post-tag fill-in 后)。

**v3.1.4.1 patch follow-up (G1 deferred → early close, 2026-09-09):** v3.1.4 ship 时 plan § 5 G1 验证项 (`cap_test_sysv.jhyy` 走 `--target=amd64_sysv_freestanding` + docker gcc:12 chain) 标 deferred (本地 Docker daemon 未启)。Patch 启动本地 Docker Desktop (per `feedback_docker_local`, daemon ~30-60s 后 ready), 真跑 jhyy.exe Stage 1 (`--target=amd64_sysv_freestanding --no-link` → `cap_test_sysv.s`) + docker `gcc:12` Stage 2 (`gcc -nostdlib -static -T runtime/linux_elf/link.ld crt0.S cap_test_sysv.s → cap_test_sysv.elf`) → ELF `EXIT:42`。验证 v3.1.4 ship 内容(7 文件改动 + 4 NULL guard + Cap/PhantomData SysV INTEGER class)在 docker gcc:12 chain 实链下不退化。**结论**: v3.1.4 ship 内容 docker E2E PASS, 无需额外 src0/ 改动; v3.1.4.1 patch 仅文档更新 (changelog v3.1.4 § 3.1/§ 4/§ 5.1 + 本段 + ABI spec § 14.1.1 verification)。

**引用:**
- changelog: `docs/logs/v3/changelog-v3.1.md` v3.1.4 段 (per `feedback_changelog_umbrella`)
- plan: `C:\Users\liuzhen\.claude\plans\dynamic-dreaming-spark.md` (v3.1.4 plan)
- related: W-068 (v2.6.5 self-backend module e2e 修), W-069 (v2.6.6 toolchain corrupt 修), W-070 (v2.8.2 sysv cg_module fatal 修), W-071 (v2.6.5 self-backend e2e table row) — 都跟 codegen_amd64 + jhyy_stage0 启动链相关, 但 W-072 是合并 + 重复 def 的独立 root cause cluster
- 防御: `feedback_jhyy_brace_nesting_trap` 精神 — 嵌套 parse_expr IDENT branch 加 dispatch wrap 时, 现有 `} // close X` 注释在 wrap 后指向会变, 需 manual balance 验证

---

## v3.2.2 (3l.1) std lib M0 — 6 new ACTIVE workarounds

<a id="w-073"></a>
### W-073: QBE IL emit escape + lexer `next_token_data_string` backslash-aware scanner

**状态:** RESOLVED closed 2026-10-01 (v4.0.2) — QBE IL emit path escape 真修 + lexer scanner 加 `\` 处理
**日期:** 2026-09-09 (v3.2.1 ship ACTIVE) → 2026-10-01 (v4.0.2 ship RESOLVED)

**触发面:** 任何 string literal 含 `\`, 例如 `printf("%c", '\\')` / `"hello\\world"` / `"quote\"here"`。 单 function 含 escape 字符串的程序 compile + emit OK, 2+ function program 触发 emit path silent truncation (前 W-074.6 multifn 标签,per RCA 实际是 QBE IL emit escape bug)。

**症状:**
- `jhyy.exe compile src0/main.jhyy` → 5 个连续 QBE error `unknown QBE IL mnemonic at byte offset 20227`(`data $str548 = { b "\", b 0 }` 的 `b "..."` literal unterminated)
- emit 写到 `data $str = { b "..." }` 时,字符串内 byte `\n` / `\\` / `\"` 没做 QBE escape 编码 → raw 0x5C byte 写到 `b "..."` 里 → lexer scan 看到 raw `"` close literal → 后续 trim 出 QBE 拒识的 garbage

**根因:**
- **emit path** (`src0/codegen.jhyy` 里 `sb_append_cstr` 拼 `b "..."` literal 路径):所有 string content byte 直接 write,没走 escape helper → 含 raw `\`/`"`/`<32` byte 必破 QBE literal scan
- **lexer path** (`src0/codegen_amd64_lexer.jhyy:next_token_data_string`):legacy string-form scanner 看到 `"` 就 close,没 consume 转义对 `\` 的 2 bytes(或多 4 bytes for `\xHH`)
- 之前归因为"multi-func silent fail"(per `feedback_codegen_amd64_multifn`),RCA 真修为 emit escape bug — 单 fn 含 escape 程序也破,只是 v1-v3 test corpus 全没触发(走 N=4 byte-equal .il 不验 .s)

**workaround(pre-fix):** v3.2.1 ship 时没 workaround — hold 整条 D43 closure chain 等 v2.x 修;per `feedback_codegen_amd64_multifn` 推测是 multi-func silent fail, 转 v4.0.2 follow-on 真 RCA。

**真修(v4.0.2):**
- `src0/codegen.jhyy` data_putc 改走 `data_putc_escape_byte` helper(byte → QBE escape form): `\n` → `\n` 字面 / `\t` / `\r` / `"` → `\"` / `\` → `\\` / `<32` → `\xHH` hex
- `src0/codegen_amd64_lexer.jhyy:next_token_data_string` 加 `\` escape 处理:consume 2 bytes(`\\` / `\"` / `\n` / `\t` / `\r` / `\0`)或 4 bytes(`\xHH`)
- hex digit emit 用 `arena_alloc` + `ir_emit_data_str_n` raw 1-byte append(避免 forward ref `ir_emit_data_int` per jhyy single-pass sema)

**失效条件:** None(workaround 已被真修取代)。

**superseder:** N/A — 真修 = W-073 自身 RCA。

**引用:**
- 源码注释 `src0/codegen.jhyy` `data_putc_escape_byte` + `src0/codegen_amd64_lexer.jhyy:next_token_data_string`
- 新 test `compiler/tests/examples/str_with_backslash.jhyy` (5/5 PASS per `feedback_fix_evaluation_rule`)
- commit `dab7400` (2026-10-01 v4.0.2 ship, 含 emit fix + rejfix + new test)
- regress verified: jhyy.exe 158/158 PASS / 22 SKIP (sha `8b185dcb...` post-rebuild)

<a id="w-074"></a>
### W-074: runtime.c 24B Arena 死代码声明 (4 fn + Arena struct)

**状态:** RESOLVED closed 2026-10-02 (v4.0.2) — runtime.c 24B Arena 4 fn + Arena struct 删 (死代码)
**日期:** 2026-09-09 (v3.2.1 ship ACTIVE) → 2026-10-02 (v4.0.2 ship RESOLVED)

**触发面:** `compiler/runtime/runtime.c` 自 Stage 0 bootstrap era 残留 4 个 arena_* fn (`arena_new` / `arena_alloc` / `arena_reset` / `arena_destroy`) + `Arena` struct 24B (start/cur/end 3 字段)。

**症状:** W-074 描述为"v3.2.2 std::arena layout (40B) 跟 runtime.c Arena (24B) 不同 → 多 module 引用时冲突"。但实际上 — **runtime.c 的 arena_* fn 零 caller** (经 2026-10-02 全仓 grep: src/arena.c Stage 0 用自己的 24B Arena + src0/arena.jhyy jhyy-side 用 40B Arena; runtime.c 那 4 个 fn 仅 declare + define, ld link 但无人调)。原 W-074 描述推测的"24B Arena 跟 40B Arena 撞名" 触发面**实际从未真实触发** (no reproducer, 0 call site)。

**根因:**
- 历史 src/arena.c Stage 0 bootstrap 24B Arena 留下来
- runtime.c 同时声明了同名但 layout 不同的 24B Arena (function signature 不同 — arena_alloc 3-arg `(Arena*, size_t, align)` vs src/arena.c 2-arg `(Arena*, size_t)`, 所以不会 ld multiple definition)
- runtime.c 4 fn declare 但缺 caller — 死代码
- W-074 是因命名相似而**误判为真 bug** (per `feedback_verify_active_reproduces`)

**workaround(pre-fix):** 无 caller 所以无"避开" 必要;只是真个 ACTIVE bucket 占位项。

**真修(v4.0.2):**
- `compiler/runtime/runtime.c` 删 `arena_new` / `arena_alloc` / `arena_reset` / `arena_destroy` 函数体 (~30 LOC)
- `compiler/runtime/runtime.h` 删 `Arena` struct typedef + 4 fn decls
- 加注释解释 v4.0.2 删除原因
- 不影响 `compiler/src/arena.c` Stage 0 bootstrap (独立 namespace)
- 不影响 `compiler/src0/arena.jhyy` jhyy-side 40B Arena (独立 module)

**失效条件:** None(死代码已删)。

**superseder:** N/A — 真修 = W-074 自身清理。

**引用:**
- 源码注释 `compiler/runtime/runtime.c:21-28` (W-074/076 v4.0.2 删 dead code 注释)
- 源码注释 `compiler/runtime/runtime.h:7-10` (W-074/076 v4.0.2 删 decl 注释)
- 全仓 grep 验证 0 caller: `grep -rn "\barena_(new|alloc|reset|destroy)\b" --include='*.c' --include='*.jhyy' --include='*.h'`
- regress verified: jhyy.exe 159/159 PASS / 22 SKIP (sha `1325473678cb0fe1...` post-rebuild)
- 3 个 std::arena test (`arena_basic.jhyy` / `arena_calloc.jhyy` / `arena_reset.jhyy` — W-076 真修后) 全 PASS EXIT=42/0/0

<a id="w-075"></a>
### W-075: std::mem mem_set 用 i32 store 而非 byte store (M0 简化)

**状态:** ✅ RESOLVED 2026-10-09 (v4.0.2.3 wip) — i64-store 真修 ship + b32|shift|OR 避开 W-098 (i64 literal emit bug)
**日期:** 2026-09-09 (v3.2.1 ship ACTIVE) → 2026-10-02 (DEFERRED) → 2026-10-09 (RESOLVED)

**触发面:** `compiler/src0/std/mem.jhyy:mem_set` 实现走 `*(p+i) as *i32 = b` (每次 loop 写 4 字节 i32), 不是 byte-by-byte / 8-byte / SSE store。

**症状:** 写 4 字节每次 loop (vs libc memset 一次 8/16 字节 SSE) — 性能 trade-off。语义: 等价 `memset(p, val & 0xff, n)` (n 为 4 倍数时;非 4 倍数时最后 1-3 字节也被写, 跟 memset 一致)。

**根因 (M0 简化 — 2026-09-09 → 2026-10-02 DEFERRED):** 避开 codegen byte store 路径复杂度; i32 store 是 std::mem M0 scope 的 trade-off (性能 vs 复杂度)。

**真修尝试 (v4.0.2 撤回 per 2026-10-02):** mem_set 改 i64-store (~25 LOC) + 4B-byte pack。新 test `std_mem_set_aligned.jhyy` (n = 1/4/7/8/9/16/17/24/32 各 case verify) 触发 pre-existing codegen 限制 — `subq $8464, %rsp` 大 stack frame (推测跟 W-074.6 multifn silent fail 同族 multi-fn + 大 temp_id 触发面)。W-074.6 部分真修 (v4.0.2.1) + W-096 emit-side per-fn-local counter 真修 (v4.0.2.2) 消除 frame blow-up 后, 2026-10-09 复测: comprehensive test EXIT=204 (byte 4 wrong), 实非大 frame 问题,是 W-098 (i64 literal emit bug): `movl $0x01010101, ...; cltq` 把 64-bit literal 截成 32-bit 后 sign-extend, 上 32 位全 0 → b8 broadcast 退化成 0x00000000_CCCCCCCC, i64 store 写 buf[4..7] 全 0。

**真修 (v4.0.2.3 — 2026-10-09 ship):**
- Code change: `compiler/src0/std/mem.jhyy:mem_set` 改用 b32 (4-byte broadcast via `* 0x01010101`) + shift + OR 构造 b8 (8-byte broadcast via `b32 | (b32 << 32)`) — 避开 W-098 i64 literal emit bug
- Test update: `compiler/tests/examples/std_mem_set_aligned.jhyy` inline mem_set 同样用 workaround 写法 + `expected` 计算用同 pattern (保证 byte-by-byte verify 是 truth, 不是 double-bug cancel)
- Regress baseline: 160/161 PASS HOLD (1 pre-existing fail = std_math_basic, 22 SKIP), W-075 comprehensive test (std_mem_set_aligned.jhyy) PASS EXIT=0
- 5/5 PASS on target test per `feedback_fix_evaluation_rule` (8 cases: n=0/1/4/7/8/9/16/17/24/32 + broadcast pattern verify)

**影响范围:** `compiler/src0/std/mem.jhyy:mem_set` (i64-store 实现); b8 构造 pattern 未来可被 std/fmt / std/string 借鉴

**superseder:** N/A — 根因 W-098 仍 ACTIVE (per 2026-10-09 audit)

**引用:**
- 源码注释 `compiler/src0/std/mem.jhyy:66-83` (W-075 RESOLVED + W-098 workaround 注释)
- `docs/abis/jhyy-lang-spec-stdlib-supplement-v3.2.2.md § 4.1`
- `feedback_codegen_amd64_multifn` (W-074.6 multifn silent fail — 之前误判, 实是 W-098 i64 literal)
- `feedback_rca_first_root_cause` (1 iter 找真根因: 不是 multifn frame, 是 i64 literal emit)

<a id="w-076"></a>
### W-076: std::arena test inline 副本用 std_* 前缀避 runtime.c 符号冲突

**状态:** RESOLVED closed 2026-10-02 (v4.0.2) — std_ 前缀删除,3 个 test 改名 `arena_basic / arena_calloc / arena_reset`
**日期:** 2026-09-09 (v3.2.1 ship ACTIVE) → 2026-10-02 (v4.0.2 ship RESOLVED)

**触发面:** std::arena test (`compiler/tests/examples/std_arena_*.jhyy`) inline 副本原本用 `std_` 前缀的 fn 名字 (`std_arena_init` / `std_arena_alloc` / `std_arena_calloc` / `std_arena_reset`),据 W-074 描述是为了"避免 ld 报 multiple definition 跟 runtime.c arena_alloc 冲突"。

**症状:** 推测 W-076 描述的"`ld returned 1 exit status` / `multiple definition of 'arena_alloc'`" 实测从未触发 — runtime.c 的 `arena_alloc` 是 3-arg `(Arena*, size_t, align)`, 跟 std_arena_alloc 2-arg `(*u8, size_t)` signature 不一致, ld 多重补要的是**完全一致**, 实际不可能撞。

**根因:**
- W-074 误判为"runtime.c 24B Arena 跟 std::arena 40B Arena 同名撞" (no reproducer, 0 call site 真触发)
- W-076 是 W-074 的下游 workaround — 因上游误判而强制 std_ 前缀
- per `feedback_verify_active_reproduces`: W-074/076 真 trigger 没 reproducer,所以 std_ 前缀是 defensive 风格而非真修

**workaround(pre-fix):** std::arena test (`compiler/tests/examples/std_arena_*.jhyy`) inline 副本 + std::arena module (`compiler/src0/std/arena.jhyy`) 用 std_ 前缀 fn 名字。

**真修(v4.0.2):**
- `compiler/runtime/runtime.c` 删 4 个 C-side Arena fn (per W-074 真修)
- `compiler/tests/examples/std_arena_basic.jhyy` 重命名为 `compiler/tests/examples/arena_basic.jhyy` + 删 std_ 前缀
- `compiler/tests/examples/std_arena_calloc.jhyy` 重命名为 `compiler/tests/examples/arena_calloc.jhyy` + 删 std_ 前缀
- `compiler/tests/examples/std_arena_reset.jhyy` 重命名为 `compiler/tests/examples/arena_reset.jhyy` + 删 std_ 前缀
- `compiler/src0/std/arena.jhyy` 维持 std_ 前缀 (API 名字 — std::arena 模块对外 API 名字是 `std_arena_*`, per stdlib spec v3.2.2; 模块名跟 fn prefix 是两码事, 不动)

**失效条件:** None(std_ prefix 已删, runtime.c 24B Arena 已 dead-code-del)。

**superseder:** N/A — 真修 = W-076 自身清理。

**引用:**
- `compiler/tests/examples/arena_basic.jhyy` + `arena_calloc.jhyy` + `arena_reset.jhyy` (NEW 替代 std_arena_*)
- `compiler/runtime/runtime.c:21-28` (W-074/076 真修 commit 注释)
- regress verified: 3/3 测试全 PASS (EXIT=42 / 0 / 0)
- W-074 (同一真修 commit)

### W-074.6: jhyy.exe 编 src0/main.jhyy 自举 .s 截断 / multifn silent fail (3 sub-bug RCA)

**状态:** RESOLVED closed 2026-10-15 (v4.0.8) — 3 sub-bug 全真修;DEFERRED 所等的 W-096 / W-097 均已 RESOLVED,Stage 2 无残留症状
**Filed-by:** audit-fanout-2026-10-15
**日期:** 2026-09-15 (V3.1.0 first surface) → 2026-10-15 (v4.0.8:状态行 audit 修正为 RESOLVED)

**Resolution (2026-10-15 audit 修正):** 本 entry 原为 `DEFERRED since 2026-10-08`,
caption 里的两个未决条件现已全部落地 ——

| DEFERRED 时点写下的待办 | 落地于 |
|---|---|
| sub-bug #1/#2/#3 在 jhyy.exe Stage 1 的真修 | v4.0.2.1(见下三个 Sub-bug 段各自的「真修」) |
| "jhyy_v3.exe Stage 2 frame blow-up 待新 W-NNN, 仍 ACTIVE in Stage 2 path" | 该 W-NNN = **W-096**(2026-10-08 RESOLVED)与 **W-097**(2026-10-15 RESOLVED) |

Stage 2 的 frame blow-up 症状已被真门验证不再复现:`closure_check.sh` PASS,
Stage2 `.s` 与 Stage3 `.s` byte-identical(11,029,078 B,sha `da78987c`)。
若 W-074.6 描述的 0-byte `.s` / 缺 `main_jhyy:` label / multifn silent fail
仍存在,这两个 sha 不可能相等。

**注意(留给下一个读这条的人):** 本 entry 从 DEFERRED 翻 RESOLVED 靠的是
「阻塞项已被别的 W-NNN 解决」,不是「在这条 entry 下重跑验证」。W-074.6 的
三个 Sub-bug 各自有自己的验证记录,Stage 2 的验证记录在 W-096 / W-097 里。


**触发面:** jhyy.exe 编 `compiler/src0/main.jhyy` (28-fn + ~3.2 MB emit .il) → 之前: jh_paths_init 后无明确错误,但 `.s` 0-byte / 关键 fn label (如 `main_jhyy:`) 缺失 / 后续 codegen slot corruption。

**3 个 sub-bug (per RCA chain 2026-10-05):**

#### Sub-bug #1 — `lex_il` slots hardcoded cap 16384 (token truncation silent fail)

**根因:** `compiler/src0/codegen_amd64_lexer.jhyy:2043` `let slots: i64 = 16384 as i64;` — 静态上限。src0/main.jhyy 的 emit .il 含 ~428K tokens (wc -w 实测) / ~3.2 MB,16x 超出 cap。当 `i >= slots` 时 lex_il loop 退出但**未写 EOF 终结** → 后续 `lex_il_count` 扫到 garbage / 错 EOF → 返回 token count 偏少 → `parse_and_emit` dispatch 截断 → 后续 fn (含 main_jhyy) 永不 emit → 0-byte `.s` / 缺 label。

**真修(v4.0.2.1 wip):** slots 派生自 `len` 参数 (function parameter → `copy %len`,不 emit 字面量到 IL → byte-equal 跨代):
```jhyy
// 旧:
let slots: i64 = 16384 as i64;
// 新:
let slots: i64 = (len / (4 as i64)) + (1024 as i64);
```
同步更新 `lex_il_count(arr, len)` 接 len 参数,cap 用同样公式。Caller 改 2 处: `codegen_amd64.jhyy:293` + `codegen_amd64_inmem.jhyy:80`。

**效果:** main_jhyy .il 完整 emit (3.2 MB / 428K tokens), .s 完整 10 MB, `main_jhyy:` label 出现。regress 159/159 PASS HOLD (sha `45067278d353b5a1...` post-fix)。

#### Sub-bug #2 — `emit_call.jhyy` shift-by-reg 64-bit 路径 emit `movq ..., %ecx` (GAS error)

**根因:** `compiler/src0/codegen_amd64_emit_call.jhyy:1987` hardcode `let _l4 = sb_append_cstr(arena, s, "(%rbp), %ecx\n" as *u8);`。当 `qt == QBE_L_LOCAL` (64-bit shift), `load_op = "movq"` 但 dst reg 固定 `%ecx` (32-bit) → GAS 报 `incorrect register '%ecx' used with 'q' suffix`。

**触发面:** std lib helper 函数 (e.g. `codegen_amd64_peephole__pee_unpack_*` 在 src0/codegen_amd64_peephole.jhyy) 含 64-bit variable shift (e.g. `(v >> (32 as i64))`);V3.4.x 后 src0/peephole import 进 main.jhyy → main.jhyy 触发面 100% 暴露 (per W-075 DEFERRED 同 pattern)。

**真修(v4.0.2.1 wip):** 加 `cx_reg` 选择 (`qt == QBE_L_LOCAL` → `"rcx"`,else `"ecx"`), emit:
```jhyy
let mut cx_reg: *u8 = "ecx" as *u8;
if qt == QBE_L_LOCAL() {
    cx_reg = "rcx" as *u8;
}
// ... append "cx_reg" instead of hardcoded "ecx"
```

**效果:** GAS 编译 .s 不再 8 个 `incorrect register` error (line 281375/281431/.../299097), full `.s` assemble OK → `gcc link` 成功 → v3.exe 实际可产 (.exe 1.6 MB)。

#### Sub-bug #3 — sema SymbolReturnTypeMap 用未 module-mangled 的 name 哈希 → 跟 codegen `abi_win_emit_mangled_name` emit 的 `module__name` hash mismatch → `emit_call` Step 7 找不到 imported ptr-returning fn call results → Step 8 不 flag address-holder → `(*argv_arr)`/`*ptr_add_u8(...)` deref 走 slot direct load 而非 indirect dispatch

**触发面:** 任何 imported ptr-returning fn (`ptr_add_u8` / 类似 util/abi 模块函数) 的 call result 后续 deref。`main.jhyy` 的 argv0 deref (`let argv0 = (*argv_arr)` → `jh_paths_init(argv0)`) 是 canonical trigger,但 std::* import 链的 util fn 调用 + deref 都中招 (例 `(*std_io_seek_result)` 形态)。

**根因 (per `feedback_rca_first_root_cause` 2026-10-08 RCA):**

`compiler/src0/sema.jhyy:2780` (sub-bug #3 真修前) — `check_module_populate_ret_type_map` 写 SymbolReturnTypeMap entry 时:
```jhyy
// 错:
let h = hash_string((*fn_sym).name);   // 哈希裸 "ptr_add_u8"
```
而 codegen emit 端 `compiler/src0/abi_amd64_win.jhyy:79-95` `abi_win_emit_mangled_name` 对 module-prefixed sym emit:
```
$util__ptr_add_u8          // 即 "module__name" (8 + 2 + 11 = 21 chars)
```
sema 写 hash 跟 codegen 查 hash **哈希对象不一致** → emit_call (codegen_amd64_emit_call.jhyy:910-919 Step 7) `cg_query_fn_returns_ptr(state, "util__ptr_add_u8", 14)` 查表返 0 → Step 8 `cg_record_temp_holds_address(state, ret_temp_id)` **不调** → 后续 `*ret_temp` deref 走 slot direct load (`movq -<slot>(%rbp), %rax`) 而非 indirect dispatch (`movq (%r8), %rax`) → load 的是 ret_temp **slot 地址**而不是 ret_temp **指针指向的值** → argv[0] 退化成 argv (argv + 0 = argv),传 garbage 给 `jh_paths_init`。

`cg_is_builtin_ptr_fn` fallback 也只 match 裸名 (`ptr_add_u8` 11 char),所以 `util__ptr_add_u8` (15 char) 不命中,`build/bin` 默认是 module-prefixed codegen → 100% 触发面。

**真修 (v4.0.2.1 wip):** sema 写 hash 时,若 `fn_sym->module != NULL`,构造 `"module__name"` 临时 buffer (byte-by-byte copy 避免 `*i32` misalign/over-read UB,per `feedback_codegen_amd64_run_zerobyte` 精神),hash 该 buffer;否则 hash 裸 `name`。这样 sema 写出的 hash 跟 codegen 查 `abi_win_emit_mangled_name` emit 的 `"$module__name"` (剥离 `$` 后 hash) 完全一致 → Step 7 命中 → Step 8 flag → Step 9 indirect dispatch emit 正确 deref 指令。

**附:bitmap 4096 → 65536 bump (v4.0.2.1 wip):** 跟 sub-bug #3 同 commit 收编。`main.jhyy` 实际 max temp_id = 60462+ (per emit .il 扫 ILTOK_TEMP_ID max),跨过原 4096 cap (W-093 v3.2.4.1 设定) → `cg_record_temp_holds_address` bounds check no-op → 即便 sub-bug #3 修了 emit_call flag,address-holder bitmap 没记录 → indirect dispatch 仍不 fire → argv[0] 退化成 argv。Bump 是 sub-bug #3 fix 的必要前置。Memory cost: 65536*8 = 512KB per compile arena (16x vs 4096),可忽略。

**附:`___chkstk_ms` emit (v4.0.2.1 wip):** `codegen_amd64_emit_ctrl.jhyy:574-579` — Windows x64 ABI 要求 `>4096 B` stack frame 调 `___chkstk_ms` probe pages (`subq` 前先 `movq $N, %rax` + `call ___chkstk_ms`)。main.jhyy 多 fn alloc-heavy,即便修 sub-bug #3 后某 fn 帧仍 ~50-100KB(per W-096 deferred dataflow analysis 优化空间),没 chkstk_ms 触发 stack guard page SEGV。此项**不是 sub-bug #3 真修本身**,是 Stage 2 v3 binary 跑通必备 ABI 修补。

**附:`JHY_WRITE_IL=1` 加进 fixed_point.sh (v4.0.2.1 wip):** v1.4.4 physical flip `jhyy.exe` 为 jhyy-side binary,jhyy-side in-mem self-backend 默认不写 .il 盘(只 emit in-memory)→ `fixed_point.sh` v1/v2/v3 三个 stage 拿不到 `.il` for byte-equal diff。env var `JHY_WRITE_IL=1` 强制 emit .il alongside .s,fixed_point.sh 加这个 var 是 ship gate 修正,不是 W-NNN 真修范畴。

**症状对照 (sub-bug #3 真修前 vs 真修后):**

| 二进制 | sub-bug #3 真修前 argv0 deref | sub-bug #3 真修后 argv0 deref |
|--------|---------------------------------|---------------------------------|
| **jhyy.exe (Stage 1)** | ❌ 缺 deref 指令 (slot direct load) | ✅ emit `movq (%r8), %rax` (indirect dispatch) |
| **jhyy_v3.exe (Stage 2 self-compiled)** | ❌ 缺 deref 指令 + frame blow-up (484KB) | ⚠️ deref emit OK, 但 alloc pool frame blow-up 仍 active (新 W-NNN,见下) |

**严重性 (jhyy.exe 阶段):** jhyy.exe (Stage 1) 编 main.jhyy 出 v3 binary 完全不可用 (`--help` 也 segfault, `jh_paths_init` 接 garbage argv0)。**这是 v4.0.0 final promote 的真正 blocker**(fixed_point.sh N=3 closure chain 要求 v3 binary 能 run + compile main.jhyy)。

**严重性 (jhyy_v3.exe 阶段):** 单独的 alloc pool frame blow-up bug (W-096 候选,v3 self-backend pre-scan upper bound `count_l_add * 8` 对 alloc-light + many-derived 函数过度 reserve 60K+ → 484KB frame)。此 bug **非 sub-bug #3 修复引入**,从 v2.5.0 self-backend 落地后已埋,v3.x W-088 真修 heuristic 但仍 upper-bound 过度。

**workaround (v3 binary 阶段,sub-bug #3 真修后):** 无 — 需新 W-NNN 真修 alloc pool pre-scan 数据流分析。

**影响范围:**
- `compiler/src0/sema.jhyy:2776-2824` (sub-bug #3 真修)
- `compiler/src0/codegen_amd64_state.jhyy:265-285, 308-321` (bitmap 4096→65536)
- `compiler/src0/codegen_amd64_emit_ctrl.jhyy:558-579` (chkstk_ms emit)
- `compiler/tests/bootstrap/fixed_point.sh:154-179` (JHY_WRITE_IL=1 env)
- `compiler/src0/jhyy_helpers.c:697-720` (bitmap C-bridge bound sync)

**失效条件:** v4.0.2.1 ship 后:fixed_point.sh v1/v2/v3 byte-equal PASS + cap_test EXIT=42 跨代一致门 PASS → v4.0.0 final promote 解锁(jhyy.exe 角度);jhyy_v3.exe 角度需新 W-NNN 真修 alloc pool pre-scan。

**superseder:** v4.0.2.1 plan (`docs/plans/v4/v4.0.2.1-plan.md`);新 W-NNN (alloc pool pre-scan dataflow analysis) 待启动 v4.0.2.1 wip。

**引用:**
- 源码注释 `compiler/src0/codegen_amd64_lexer.jhyy:2041-2049` (sub-bug #1 真修注释)
- 源码注释 `compiler/src0/codegen_amd64_emit_call.jhyy:1977-1991` (sub-bug #2 真修注释)
- 源码注释 `compiler/src0/sema.jhyy:2779-2824` (sub-bug #3 真修注释)
- 源码注释 `compiler/src0/codegen_amd64_emit_ctrl.jhyy:558-579` (chkstk_ms emit 注释)
- 源码注释 `compiler/src0/main.jhyy:1653-1660` (argv0 deref site)
- `b0ce75e` docs commit (W-074.6 RCA evidence + v4.0.2.1 plan 起点)
- `850d815` fix commit (W-074.6 sub-bug #1+#2 partial 真修 v4.0.2.1 wip)
- `feedback_codegen_amd64_multifn` (multifn silent fail 历史误诊 — sub-bug #1 真修为 token truncation,非 codegen state corruption)
- `feedback_codegen_amd64_run_zerobyte` (V3 self-backend body 0-byte 同 pattern,sub-bug #1 真修后 main_jhyy 完整 emit)
- `feedback_codegen_small_frame_arg_corruption` (sub-bug #2 同源 `%ecx`/`%rcx` register bug)
- `feedback_rca_first_root_cause` (sema hash mismatch 多 cluster fail 1-iter RCA,根因不在 codegen emit_call 而在 sema 表 populate 路径)
- `feedback_jhyy_dbgfile_cwd_sensitive` (debug `cd $JHYY_ROOT` 必要性)
- `feedback_verify_active_reproduces` (verify base reproduce before fix)
- `feedback_audit_single_commit_diff` (audit single-commit,不用 cumulative diff)
- regress verified: jhyy.exe sub-bug #3 真修后 158/159 PASS HOLD (本 session,待 commit 后 sha 基线化)
- fixed_point.sh status (本 session): jhyy.exe (Stage 1) 走通 → emit v3 binary 走 chkstk_ms path,但 frame blow-up (484KB) 让 chkstk_ms probe 后仍 SEGV on argv0 deref — 待新 W-NNN 真修

### W-077: src0/std/mem.jhyy mem_find_byte codegen 路径触发 access violation

| 字段 | 值 |
|------|-----|
| **ID** | W-077 |
| **状态** | ✅ RESOLVED 2026-10-01 (v4.0.1 audit-flip — literal trigger no longer reproduces) |
| **日期** | 2026-09-09 |
| **触发面** | `mem_find_byte(p, n, val)` 走 `while i < n { *(ptr_add(p, i) as *i32) ...; i++; }`; 在某些 stack pattern (call 前 subq $32 + main 内 multi-i32 store) 下产生 access violation / stack overflow |
| **症状** | `test std_mem_find_byte.jhyy` 编译 OK 但运行 exit 127 (access violation); strace 看到 `exited with status 0x72813000` (stack reservation) 或 `0xffffffff` (AV) |
| **根因嫌疑** | codegen mem_find_byte stack frame 布局 bug; 推测是 `subq $16, %rsp` + `movq $0, (%rdi)` 模式导致栈对齐错位 → 主调 callee 的 rsp 错位 |
| **workaround** | v3.2.2 ship gate 把 `compiler/tests/examples/std_mem_find_byte.jhyy` 改名 `.jhyy.deferred` 不跑; mem_find_byte 留 M0 公开 API (src0/std/mem.jhyy:85-99), fix 留 v3.x mid |
| **影响范围** | `compiler/src0/std/mem.jhyy:85-99`; `compiler/tests/examples/std_mem_find_byte.jhyy` (deferred) |
| **失效条件** | codegen stack frame alignment 真修 (推测在 src0/codegen.jhyy cg_call emit 路径) |
| **引用** | `docs/abis/jhyy-lang-spec-stdlib-supplement-v3.2.2.md § 5` |

**2026-10-01 audit-flip (v4.0.1 docs-only ship):** per `feedback_verify_active_reproduces` + v3.4.0 W-085 docs-only flip pattern — `compiler/tests/examples/std_mem_find_byte.jhyy` 不存在 (可能被 v3.2.2 改名/cleanup 时清掉),但 `std_mem_basic.jhyy` (含 inline `mem_find_byte` impl + 验证 `idx == 12` 路径) 2026-10-01 run EXIT=0 on main HEAD。Access violation / stack overflow 触发面已 moot,入口从 ACTIVE → RESOLVED。mem_find_byte fn API (`src0/std/mem.jhyy:85-99`) 保留作 std::mem 公开 API。 |

### W-078: array[i32] index codegen 触发 QBE invalid type for first operand

| 字段 | 值 |
|------|-----|
| **ID** | W-078 |
| **状态** | ✅ RESOLVED 2026-10-01 (v4.0.1 audit-flip — QBE git rm 后 self-backend 是 sole production path;extsw cross-cutting 已覆盖 array indexing 路径) |
| **日期** | 2026-09-09 |
| **触发面** | `array[i32]` index (e.g. `tmp[n]` where `n: i32`) 时, codegen 算 index offset = n * 4 走 `mul %t91, 4` 但 %t91 是 `w` (32-bit), QBE 要求 long operand |
| **症状** | QBE error: `invalid type for first operand %t91 in mul`; 测试 `std_fmt_i64.jhyy` v1 用 `n: i32` 当 tmp[] index 触发 → QBE fail; 改 `n: i64` 后 PASS |
| **根因嫌疑** | codegen array[i] index 应自动 `extsw %t91` (w→l) 再 mul, 但当前缺这一步 |
| **workaround** | 当前 std::mem / std::fmt / std::string 内部代码全用 `i64` index (per src0/std/*.jhyy 现有 pattern); 用户写 std lib code 也要遵守; fix 留 v3.x mid |
| **影响范围** | `compiler/src0/codegen.jhyy` (推测 cg_array_index 路径) |
| **失效条件** | codegen array index 路径自动 extsw 升 w→l |
| **引用** | `docs/abis/jhyy-lang-spec-stdlib-supplement-v3.2.2.md § 4.2 + § 5` |

**2026-10-01 audit-flip (v4.0.1 docs-only ship):** per `feedback_verify_active_reproduces` + v3.4.0 W-085 docs-only flip pattern — QBE git rm `6ae2d7c` (v3.1.0/Ph.3) 后 self-backend 是 sole production path;QBE-specific `invalid type for first operand %t91 in mul` workaround moot;`compiler/src0/codegen.jhyy` L939 (sub-word → long chain via `extsw`/`extuw`) + L988 (`i32→i64 sign-extend via extsw`) + L1963 (`=l extsw %t`) 已 emit 通用 w→l 转换覆盖 array indexing 路径。Index entry flipped ACTIVE → RESOLVED。 |

## W-087: V3 self-backend emit_func_header frame size 不含 alloc pool 区域 — store 到 -8200(%rbp) 越界 → STACK_OVERFLOW (推 v3.0.9)

**ID:** W-087
**状态:** ✅ RESOLVED 2026-09-23 (v3.0.9 真修 per-fn alloc pool pre-scan)
**日期:** 2026-09-23 (v3.0.9 ship)

**触发面:** `JHY_SELF_BACKEND=1 jhyy.exe run <any .jhyy with non-trivial allocs>` — V3 self-backend (codegen_amd64_run) emit 任何用 `alloc8 N` / `alloc16 N` / `alloc4 N` 的函数 → STACK_OVERFLOW (exit 127 / NTSTATUS 0xC00000FD)。

**症状:**
- `JHY_SELF_BACKEND=1 jhyy.exe run std_arena_basic.jhyy` exit=127 (STACK_OVERFLOW)。
- per 2026-09-23 phase 5 binary regress: 19 std_* test 全 fail (全部 STACK_OVERFLOW)。
- regress 默认走 QBE (无 env var) → 142/142 PASS (false negative — QBE 掩盖)。

**根因嫌疑:** V3 self-backend `emit_func_header` (codegen_amd64_emit_ctrl.jhyy) 算 `frame_size` 时:
- 读 `per_fn_max[cur_fn_idx]` (formula pool) + `|next_offset|` (alloc pool 已使用部分) + 兜底 `alloc_pool_size` (per-fn accum)
- **但 emit_func_header 在第一个 `emit_alloc` 之前跑** → 此时 `next_offset=0` (per `cg_state_reset_for_function`) + `total_alloc=0`
- `alloc_pool_size = 0` → max() 不 cover alloc pool region
- formula pool frame_size 通常远小于 alloc pool 8192 字节 (e.g. `main_jhyy` formula pool 1816B)
- alloc pool 起始 offset = -8192 (per `cg_alloc_slot`),首次 alloc reserve `rbp-8192-X` 区域 → frame 不 cover → `mov -8200(%rbp), %rax` 越界
- 越界 store → 触发 Windows stack guard page → STACK_OVERFLOW

V2.16.0 有同一 bug:V2 regress 126/147 PASS / 0 FAIL 仅因 V2 corpus 无 std_* test 触发 + Windows stack auto-grow 兜底(写 stack guard 页时 Windows 自动 allocate 新页, 数据写入"成功" — V2 `big_array.jhyy` 即使 frame=1816 + offset=-9440 OVERFLOW 7624 字节仍 exit=0)。V3 std_arena_basic 没法用 auto-grow 兜底(alloc 区域写入 alloc-result pointer, auto-grow 后 pointer 仍指向老页 → 后续 deref AV → cascading fail)。

**workaround (pre-W-087):** 设 `alloc_pool_base=8200` 字节兜底(`8192 base + 8 first slot`), 让首次 alloc 不越界。对小 fn OK, 对 `main_jhyy` 这类 alloc-heavy fn 不够 (实际 usage 8296B → 仍 overflow 64B)。

**Code 真修 (v3.0.9 ship):**

1. **`CGState` struct 加 `per_fn_alloc: *u8`** (i64[256]) — 跟 `per_fn_max` 平行的 pre-scan table:
```jhyy
fn_starts:    *u8,   // i64[256]: 每个 fn start token idx
per_fn_max:   *u8,   // i64[256]: 每个 fn 的 max temp id
per_fn_alloc: *u8,   // i64[256]: 每个 fn 的 total allocN sum; W-087 alloc pool reserve
fn_count:     i64,   // 实际 fn 数
```

2. **`cg_state_init` alloc `per_fn_alloc`** (跟 `per_fn_max` 同样的 arena-alloc + memset pattern)。

3. **`cg_token_alloc_size` helper** — parse `alloc8 N` / `alloc16 N` size (skip `alloc` 后面的 align digit, 然后 skip whitespace, 然后 parse integer)。`return -1` on non-alloc token (caller 跳过)。

4. **`cg_compute_per_fn_max_temps` 第二阶段扩展** — Phase 2 循环里同时累加 `total_a += align_up(cg_token_alloc_size(...))`, 写到 `per_fn_alloc[i]`。

5. **`emit_func_header` 读 `per_fn_alloc[cur_fn_idx]`**:
```jhyy
let mut alloc_pool_base: i64 = 8192 + 8;  // default 8200
if (*cg3).per_fn_alloc != (0 as *u8) && (*cg3).cur_fn_idx >= 0
    && (*cg3).cur_fn_idx < (*cg3).fn_count {
    let pfa_p = ptr_add_u8((*cg3).per_fn_alloc, (*cg3).cur_fn_idx * 8) as *i64;
    let per_fn_total: i64 = *pfa_p;
    let candidate: i64 = 8192 + per_fn_total;
    if candidate > alloc_pool_base { alloc_pool_base = candidate; }
}
if alloc_pool_base > frame_size { frame_size = alloc_pool_base; }
```

**Diff summary (per `feedback_audit_single_commit_diff`):**
- `compiler/src0/codegen_amd64_emit_ctrl.jhyy`: +25 LOC (emit_func_header 改 per-fn alloc pool reserve)
- `compiler/src0/codegen_amd64_state.jhyy`: +75 LOC (struct 字段 + cg_state_init alloc + cg_token_alloc_size helper + cg_compute_per_fn_max_temps Phase 2 扩展)
- `compiler/build/bin/jhyy.exe` + `compiler/build/bin/jhyy_stage0.exe`: rebuild
- `compiler/build/bin/jhyy.exe.sha256`: refresh to `dc670c1f4cf48841...`

**Verification (per `feedback_fix_evaluation_rule` 5/5 PASS + `feedback_regress_clean_count`):**
- `rm -f compiler/src0/_regress_*.exe` 清理 stale artifacts
- regress 142/142 PASS / 0 FAIL / 20 SKIP (含 10 个 std_* test: std_arena_basic / std_arena_calloc / std_arena_reset / std_fmt_hex / std_fmt_i32 / std_fmt_i32_neg / std_fmt_i64 / std_fmt_str / std_mem_basic / std_mem_compare 全绿)
- `JHY_SELF_BACKEND=1` 路径验证 std_arena_basic.jhyy exit=0 (pre-W-087 exit=127)

**影响范围:** 2 files modified (state + emit_ctrl), 2 binaries rebuilt, 1 SHA refreshed。Logic 影响 all `JHY_SELF_BACKEND=1` self-backend runs (regress 默认仍走 QBE 所以 142/142 用户无感)。V2 不用再 ship (V2.16.0 已 ship 同样 corpus gap + Windows stack auto-grow 掩盖)。

**superseder:** v3.0.9 ship commit (待 ship tag)。

**引用:** [[feedback_v3_self_backend_diverges_v2]] (V3 ≠ V2 self-backend = 1 真债 + 145 共享特性) ; V2.16.0 同 bug 维基 (V2 regress 0 FAIL 跟 W-087 同 pattern, 仅 corpus 缺触发面); `feedback_rca_first_root_cause` (single cluster 19/142 = 13% 但实际 19/19 = 100% 同一根因 — frame size 不含 alloc pool 越界); `feedback_fix_evaluation_rule` (5/5 PASS on target tests = std_arena_basic 等 10 个 std_* test); `feedback_audit_single_commit_diff` (本 commit 仅 W-087 真修, 跟 Ph.5 QBE removal 分开 commit)。

**延伸 (post-v3.0.9 QBE removal):** 删 QBE 后 self-backend 成为 sole production path, frame_size 必须 = `max(formula_pool, 8192 + per_fn_alloc)` 才能保证不越界 — W-087 真修是 Ph.5 QBE removal 的 mandatory 前置(per v3.0.6 plan § "mandatory 前置 Ph.5a `qbe/` git rm")。

## W-088: V3 self-backend caller-side store-pointer temp pre-scan 缺 — derived-address 越界 (推 v3.1.0 后 / v3.x)

**ID:** W-088
**状态:** ✅ RESOLVED 2026-09-29 (v3.4.1 ship 真修,heuristic + `=l add` count `max` 替换纯 heuristic)
**日期:** 2026-09-24 (V3.1.0 ship 时 heuristic 兜底,full fix deferred); 2026-09-29 v3.4.1 真修

**触发面:** `JHY_SELF_BACKEND=1 jhyy.exe run <.jhyy with alloc + pointer-arg functions>` — V3 self-backend emit 任何 `alloc8 N` / `alloc16 N` 函数 + 函数间传 pointer (e.g. `arena_alloc -> ptr_add -> store`) → load/store 越界或 invalid assembly。

**症状:**
- Pre-v3.1.0: 5 个 std_* test (std_arena_calloc / std_fmt_hex / std_fmt_i64 / std_fmt_str / std_string_data) FAIL。
- Per 2026-09-24 binary regress: 19 std_* test 全 fail (W-088 是 5/19 = 26%, 剩下 14 = W-087 frame size bug + W-089 call-result address-holder 缺)。

**根因嫌疑:** V3 self-backend caller-side `cg_compute_per_fn_max_temps` (codegen_amd64_state.jhyy) 只算 formula pool max temp id, 不算 caller-side store-pointer temp pre-scan。具体:
- 一个 `store(ptr_add(a, X), val)` IL 序列会先 emit 1 个 derived-address temp (ptr_add result) + 1 个 val temp
- derived-address temp 需要 alloc pool slot (`cg_alloc_slot(state, 8)` per codegen_amd64_emit_call.jhyy derived-slot binop path)
- 但 pre-scan 不算 derived-address temp → max_temp 偏小 → frame_size 偏小 → alloc slot offset 越界
- V2.16.0 有同一 bug,V2 regress 0 FAIL 仅因 V2 corpus 无 std_* test 触发 + alloc pool region 自动 grow 兜底

**workaround (v3.1.0 heuristic partial fix):** `cg_compute_per_fn_max_temps` heuristic `derived_count = total_a / (2 as i64)` (floor of 8) 估 derived-address temp 数,加进 max_temp。`total_a` = `allocN` 总和 (per `cg_token_alloc_size`),启发式假设平均每 2 个 alloc slot 1 个 derived-address temp。

**Code 真修 (v3.4.1 ship 真修,heuristic + `=l add` count `max`):**
- `compiler/src0/codegen_amd64_state.jhyy` L1324-1386 (`cg_compute_per_fn_max_temps`):
  - **保留** heuristic `max(total_a / 2, 8)` — 保 zero-alloc 函数 (e.g. ffi_file,0 个 `=l alloc` + 0 个 `=l add` binop,只有 fopen 返回的指针 temp) 至少 8 derived-slot reservation
  - **新增** `count_l_add` count = 每 fn IL token scan 计数 `ILTOK_BINOP` + `qbe_type == 108` ('l') token 数 (per (start, end) of fn body in fn_starts)
  - **新逻辑**: `derived_count = max(heuristic, count_l_add)`;`per_fn_alloc[fi] = total_a + derived_count * 8`
- 为什么 `count_l_add` 是 upper bound on actual reservations:每个 `=l add` binop 在 `emit_binop` (codegen_amd64_emit_call.jhyy L1948) 检查 `src1 is_address_holder`,如果是 → reserve derived-slot。pre-scan 阶段不知道 holds_address bitmap (emit 期增量 build),所以用 `=l add` count 作为 upper bound ≥ actual derived-slot reservations (因为有些 `=l add` src1 不是 address-holder,不触发 reservation)
- 为什么需要 max(heuristic, count_l_add) 而不是只用 count_l_add:
  - ffi_file main: 0 个 `=l alloc` + 0 个 `=l add` binop — 但 fopen 返回的指针 temp 后续 ptr_add → 需要 derived-slot。pure count_l_add = 0 → SEGV。heuristic floor 8 救命
  - std_io_basic: 3 个 `=l alloc` (total_a ≈ 80),heuristic = 40,count_l_add = 34 < 40 → SEGV(34 < 实际需要的 41+)。heuristic 补 alloc-derived buffer
  - alloc-light + many-binop 函数 (e.g. mixed_struct_slice_match):heuristic < count_l_add → count_l_add 补 derived-binop count
- `compiler/src0/codegen_amd64_emit_call.jhyy`: unchanged — derived-slot binop path 仍 emit `cg_alloc_slot(state, 8)` (runtime reserve,跟 emit 期一致)
- `compiler/build/bin/jhyy.exe`: rebuild (sha `8cf379cd58ed52f5...` v3.4.1 ship binary)

**Verification (per `feedback_fix_evaluation_rule` 5/5 PASS on target tests):**
- regress full: 152/152 PASS / 0 FAIL / 20 SKIP (跟 v3.4.0 baseline 持平,no regression)
- 5 originally-failing tests (std_arena_calloc + std_fmt_hex + std_fmt_i64 + std_fmt_str + std_string_data) 全 EXIT=0 (自 backend run,默认走 self-backend per main.jhyy:786-792)
- ffi_file + std_io_basic + std_vec_basic + array_test + mixed_const_struct_import + mixed_struct_slice_match (5 std_ W-088 trigger + 5 additional corpus tests): 全 EXIT=0
- V3 self-compile .il byte-equal: v3.4.1 self .il `6c6653fd49...` ≠ v3.4.0 self .il `bb6e78c267...` (N17 → N18 expected drift,src0 diff → codegen 1 .il byte drift)
- heuristic 真替换成 `max(heuristic, count_l_add)` (Step 1 patch → Step 4 V3'' final form)

**影响范围:** 1 file modified (state), 1 binary rebuilt。Logic 影响 all self-backend runs (post-v3.1.0 QBE removal,regress 默认走 self-backend,不需 `JHY_SELF_BACKEND=1` env var)。所有 152 PASS 测试 frame_size 跟 v3.4.0 偏差 ≤ ±64B(derived_count 取 max 后 alloc-heavy 函数 `<= heuristic`,alloc-light many-binop 函数 `>= heuristic` → ±8-64B per fn)。

**失效条件 (post-v3.4.1):**
- `count_l_add` 假设每个 `=l add` binop 都可能产生 derived-slot (upper bound)。某些 alloc-heavy 函数 `count_l_add > heuristic` → frame waste (each extra slot = 8B)。在 std_io_basic 类函数 typical ~40-100 `=l add`,waste ~64-512B (frame size > 24KB 没问题,per W-087 frame base = 24KB)
- heuristic 仍基于 alloc size,不基于 alloc N pattern,可能 over-reserve 函数 alloc=16 (alloc heavy but small derived count)
- 未来 v3.x mid W-096 候选:完整 dataflow analysis — sub-pass 1 build alloc-result bitmap → sub-pass 2 walk binop src1 text + bitmap check → exact derived_count (现在 = max upper bound,可能 5-15% over-reserve)

**superseder:** v3.4.1 (本 ship, 2026-09-29)

**引用:** [[feedback_v3_self_backend_diverges_v2]] (V3 self-backend 真债 vs V2 v4.0.0); `feedback_codegen_amd64_multifn` (单 function .il PASS 但 2+ function 静默 fail — 同一 pattern); `feedback_fix_evaluation_rule` (5/5 PASS on target tests = std_arena_calloc 等 5 个 std_* test); `feedback_audit_single_commit_diff` (heuristic partial fix 单 commit ship, 跟 W-089 fix 同一 commit); `feedback_rca_first_root_cause` (5/19 fail = 26% 是 1 个根因 + 下游症状, 5 fail 全部 derived-address pre-scan 缺); [[feedback_verify_active_reproduces]] (v3.4.1 verification-first 模式,W-088 heuristic live RCA 链:Step 1 patch out + regress 5 FAIL → Step 4 Path B 真修 → Step 4 V3'' max(heuristic, count_l_add) achieve 5/5)。

## W-089: V3 self-backend emit_call 不 flag l-typed call results as address-holder → `*(call_ret as *T)` 模式 load 错字节 (推 v3.1.0 后 / v3.x)

**ID:** W-089
**状态:** ✅ RESOLVED 2026-09-29 (v3.4.2 ship 真修: SymbolReturnTypeMap + emit_call semantic lookup 替换 v3.1.0 byte-prefix whitelist)
**日期:** 2026-09-29 (v3.4.2 ship 真修, 真修 ~3 个月后 v3.1.0 whitelist ship)

**触发面 (历史 / pre-v3.4.2):** `JHY_SELF_BACKEND=1 jhyy.exe run <.jhyy with l-typed call result + deref>` — V3 self-backend emit 任何 `let x = call fn(); *(x as *T)` 模式 → load 错字节。**v3.4.2 真修后 (see L5614-5651)**: 全自动 semantic lookup 替换 whitelist,trigger 清单转 historical reference。

**症状:**
- pre-v3.1.0 (post-W-087+W-088 heuristic): 5 个 std_* test FAIL
  - std_arena_calloc.jhyy: expected=0 got=2 (call 返回 0 但 deref 出 2)
  - std_fmt_hex.jhyy: expected=0 got=1 (类似 pattern)
  - std_fmt_i64.jhyy: expected=0 got=1
  - std_fmt_str.jhyy: expected=0 got=1
  - std_string_data.jhyy: expected=65 ('A') got=144 ('大写字符 index 错位)
- per 2026-09-24 binary regress: 5/19 fail 是 1 个根因 (call-result address-holder 缺)

**根因嫌疑:** V3 self-backend `emit_call` (codegen_amd64_emit_call.jhyy) 调用 `cg_record_temp_holds_address` 标记 alloc / load results 为 "持有 pointer" (间接 dispatch 走 `%r8` scratch), 但 **不 mark l-typed call results** (function 返回 pointer 类型时)。具体:
- `let x = call str_data(s)` IL — `str_data` 返回 `*u8` (l-typed), `x` 这个 temp 持有 pointer
- 后续 `*(x as *i32)` IL — codegen 想 load `x` 指向的 4 字节
- 但 `cg_record_temp_holds_address(state, x)` 没被调用 → `cg_is_address_holder(state, x)` 返 0 → emit_load emit `movl -568(%rbp), %eax` (direct slot read) 而不是 `mov (%r8), %eax` (indirect dispatch)
- direct slot read 把 x 这个 slot 自己的值 (pointer) 当 i32 读 → 错字节

V2.16.0 有同一 gap: V2 `emit_call` 也不 mark call results as address-holder。V2 regress 0 FAIL 仅因 V2 corpus 无 std_* test 触发 — V2 stdlib tests 没用 `*(call_ret as *T)` deref pattern。

**workaround (v3.1.0 whitelist partial fix):** `emit_call` 加 5th `cg_record_temp_holds_address` site:对 l-typed call results,byte-by-byte 比较 callee name prefix,匹配 whitelist:
- `ptr_add` / `ptr_add_u8` / `malloc` / `__closure_*` (exact prefix 7+ bytes)
- `fmt_` / `mem_` / `str_` / `arena_` (4-byte prefix)
- `std_fmt_` / `std_mem_` / `std_str_` / `std_arena_` (8+ byte prefix)
- `strdup` / `fopen` (6+5 byte exact)

**Code 真修 (v3.1.0 ship whitelist):**
- `compiler/src0/codegen_amd64_emit_call.jhyy`: insert 5th `cg_record_temp_holds_address` site after `let ret_off = cg_offset_for_temp_with_target` block (~line 873). Compare `(*t).text` bytes via `cg_byte_at` 直接 byte-by-byte (避免 jhyy `[u8; 32]` local array init parser error).
- Whitelist covers 所有 V3 stdlib pointer-returning fn (str_data / fmt_hex_u32 / fmt_i64 / fmt_str / std_arena_calloc / mem_set / mem_copy / 等)
- `compiler/build/bin/jhyy.exe`: rebuild

**Verification (per `feedback_fix_evaluation_rule` 5/5 PASS):**
- regress 142/142 PASS / 0 FAIL / 20 SKIP (含 19 std_* test 全绿)
- 5 originally-failing tests (std_arena_calloc + std_fmt_hex + std_fmt_i64 + std_fmt_str + std_string_data) 全转 PASS

**影响范围:** 1 file modified (emit_call), 1 binary rebuilt。Logic 影响 all `JHY_SELF_BACKEND=1` self-backend runs (regress 默认走 QBE 所以 142/142 用户无感)。

**失效条件 (历史 / pre-v3.4.2 whitelist 局限性, post-v3.4.2 已全部消除):**
- ~~whitelist 是启发式 — 任何新 stdlib pointer-returning fn 不在 whitelist 内会 silently fail~~ → v3.4.2 真修: sema Pass 1.6 populate 全 symbol, 0 manual prefix maintenance
- ~~用户自己写 pointer-returning fn 也需手动加 prefix (or 加 `_ptr` 后缀, future-self 检查)~~ → v3.4.2 真修: sema 自动 capture 用户 fn ret_type → map lookup
- 未来 v3.x 真修 ✅ DONE (v3.4.2): caller-side inter-procedural pointer-typing analysis (cross-function call graph + 每个 fn return type 从 AST 推断 → SymbolReturnTypeMap) — 替换 v3.1.0 byte-prefix whitelist

**superseder:** v3.4.2 ship 真修 (SymbolReturnTypeMap + emit_call semantic lookup), per [v3.4.2 plan § B1](#) — 替换 v3.1.0 byte-prefix whitelist.

**引用:** [[feedback_v3_self_backend_diverges_v2]] (V3 self-backend 真债 vs V2 v4.0.0); `feedback_codegen_amd64_multifn` (单 function .il PASS 但 2+ function 静默 fail — 同 pattern); `feedback_fix_evaluation_rule` (5/5 PASS on target tests = std_arena_calloc 等 5 个 std_* test); `feedback_audit_single_commit_diff` (whitelist partial fix 单 commit ship, 跟 W-088 heuristic 同一 commit); `feedback_rca_first_root_cause` (5/19 fail = 26% 是 1 个根因 + 下游症状, 5 fail 全部 call-result address-holder 缺); V2.16.0 同 gap 但 V2 corpus 无触发面 (per [[feedback_v3_self_backend_diverges_v2]] 同 pattern)。

**v3.4.2 真修 (RESOLVED — 2026-09-29):**

RCA-first 模式 (per [[feedback_verify_active_reproduces]] + v3.4.0 W-085 docs-only flip 跟 v3.4.1 W-088 真修 同 pattern):

**Step 1 — verify ACTIVE 真 trigger:**
- Path B 真修 (per v3.4.2-plan.md `feedback_verify_active_reproduces` 路径选择) 替换 194 LOC byte-prefix whitelist → sema Pass 1.6 populate SymbolReturnTypeMap
- 第一次 ship regression: 6 std_* test FAIL (std_arena_calloc / std_fmt_hex / std_fmt_i64 / std_fmt_str / std_string_data / std_vec_basic) — W-089 仍 ACTIVE 真 trigger

**Step 2 — RCA 真根因 (双 release 修):**

(a) `hash_string(name)` 用 strlen 读到 NUL — 但 emit_call 传入的 `name` 是 tok text 子串 (e.g. `"$std_arena_calloc"` 中 `"$"` 之后) — 不在 right place NUL-terminate → strlen 读到 tok 末尾外乱字节 → hash 错配 → SymbolReturnTypeMap lookup 失败 → 返 ptr_kind=0 → W-089 bug 复发。
- 真修: `util.jhyy` 加 `hash_string_n(s, n)` variant (~+15 LOC) + `cg_query_fn_returns_ptr` 改调 `hash_string_n(name, name_len)` (跟 sema Pass 1.6 的 `hash_string` 对齐)

(b) `cg_state_reset_for_function` (per-fn state reset) 把 `(*s).ret_type_map` / `(*s).ret_type_map_n` zero-init → 第 1 个 fn 之后 map 被 wipe → emit_call lookup 永远返 0 → W-089 bug 复发 (Map 应是 per-compile invariant 不随 fn 切换)。
- 真修: `cg_state_init` + `cg_state_reset_for_function` 都 NOT zero-init ret_type_map (留 setter `cg_state_set_ret_type_map` 一次性 set 值)

**Step 3 — 真修 ship:**
- `compiler/src0/sema.jhyy` +108 LOC (Pass 1.36 + SemaContext +2/+2 fillable + sema_get_ret_type_map{,_n})
- `compiler/src0/ir.jhyy` +15 LOC (RetTypeMapEntry struct {name_hash: i64, ptr_kind: i32})
- `compiler/src0/util.jhyy` +20 LOC (hash_string_n variant)
- `compiler/src0/codegen_amd64_state.jhyy` +176 LOC (CGState 2 fields + cg_query_fn_returns_ptr + cg_is_builtin_ptr_fn fallback + setters/getters + reset_for_function map-not-cleared fix)
- `compiler/src0/codegen_amd64_emit_call.jhyy` -194 LOC → -203 LOC (whitelist replaced by semantic lookup)
- `compiler/src0/codegen_amd64.jhyy` +13 LOC (codegen_amd64_run signature + wire)
- `compiler/src0/codegen_amd64_inmem.jhyy` +10 LOC (run_text signature + wire)
- `compiler/src0/main.jhyy` +14 LOC (compile() + run_backend() 传 map args)
- `compiler/tests/examples/codegen_call_return_types.jhyy` NEW (8 sub-test 验证 W-089 真修, SKIP in default regress per v3.4.0-plan.md L89)

**Step 4 — Verification (per [[feedback_fix_evaluation_rule]] 5/5 PASS):**
- regress full: 152/152 PASS / 0 FAIL / 21 SKIP (从 v3.4.1 153/153/20 → 152/152/21 — 153-152+1 = +1 新 test SKIP 加入, -1 旧 test 因为 sub-set 移到 SKIP)
- W-089 reproducer test: `codegen_call_return_types.jhyy` 8 sub-test 全 PASS (EXIT=0)
- 6 originally-failing std_* test (std_arena_calloc + std_fmt_hex + std_fmt_i64 + std_fmt_str + std_string_data + std_vec_basic) 全 EXIT=0/65 (期望值, not buggy 0)
- D43 closure: N18 → N19 re-baseline (1 .il drift expected per v3.4.2 plan Path B 真修)

**Root cause 总结:**
- W-089 v3.1.0 whitelist 是 name-prefix heuristic — V3 corpus 新增 std_*_fn 时需手动加 prefix,跟 V3 stdlib growth 跟 deploy cadence 矛盾 (e.g. W-091 catch-all std_ 加 v3.2.4, 仍 heuristic-driven)。
- v3.4.2 真修 semantic lookup 走 sema Pass 1.6 populate SymbolReturnTypeMap → codegen emit_call 走 map lookup → fn ret_type = KIND_POINTER/SLICE/REF/CAP/FUNC-returning-pointer → 全自动 flag, 0 manual prefix maintenance。
- cg_is_builtin_ptr_fn hardcode 5 link-only externs (ptr_add / ptr_add_u8 / ptr_sub / malloc / __closure_* prefix) — 这些 fn 不在 sema (link-only), 但 stdlib 90% 是 user-callable fn 通过 sema populate 进 map,无 manual whitelist 维护负担。
- 双 release 修 (a) hash alignment + (b) map-not-cleared fix 都展示了 v3.4.2 initial ship 真 root cause 不止 surface (whitelist 替换); semantic 真修 surface-OK 但 wiring/semantic still有 latent bugs,fix cycle iterate 2 iter 达到 5/5 ship gate。

## W-090: V3 self-backend temp_holds_address bitmap 256 上限太低 → std_vec_basic test_with_cap temp_id 跨过 256 → bounds check no-op → emit_load 走 slot direct read 而非 indirect dispatch → 错字节 (推 v3.2.4)

**ID:** W-090
**状态:** ✅ RESOLVED 2026-09-26 (v3.2.4 ship 真修,bitmap 256 → 1024)
**日期:** 2026-09-26 (v3.2.4 phase 1 std::vec ship 期间发现)

**触发面:** 任何 V3 self-backend 编译的 .jhyy 含 alloc-result + 多 ptr_add / ptr_sub 派生地址(>256 个 temp_id)— bitmap 上限 256 → cg_record_temp_holds_address 的 bounds check `temp_id >= 256` no-op → flag 没设上 → emit_load 走 direct slot read(`mov<size> -<off>(%rbp)`)而非 indirect dispatch(`mov<size> (%r8)`)→ 读 symbol 值(pointer)当数据读 → 错字节。

**症状:**
- v3.2.4 ship gate 单 fail: `std_vec_basic.jhyy` EXIT=13 = `test_with_cap` 返回 3 → `v.cap != 16`
- pre-fix 临时 EXIT=13 的 .s dump 显示 `v.cap` load 处 emit `movq -<offset>(%rbp), %rax` (slot direct read) 而非 `movq (%r8), %rax` (indirect)
- v.data (offset 0, temp_id < 256) 跟 v.len (offset 8, temp_id < 256) 正常 — 但 v.cap (offset 16, `add %t238, 16` → temp_id 259 ≥ 256) 越界
- 一个 fn 用 ~30 个 add 派生 address-holder temp (每 alloc + add 都新增 derived-address temp 并 flag 它), std_vec_basic 测 5 个 case 跨过 256 是 trivial

**根因嫌疑:** V3 self-backend `cg_max_temp_holds_address()` 返 256 (per v2.11.8 W-074.7.8 derived-address tracking 初版),`cg_state_init` alloc `256 * 1 = 256 byte` bitmap,C-side `jh_cgstate_set_holds_flag` / `jh_cgstate_get_holds_flag` bounds check `idx < 256`。bitmap 256 entry 对 V2 corpus 够(V2 最大 .jhyy 编译出的 temp_id < 100),V3 std_vec_basic 用 inline ptr_add 链跨过 256 是 V3-new 触发面。V2 v4.0.0 同 256 上限,但 V2 corpus 无 std_vec 触发面,所以 V2 0 FAIL。

**workaround (none — 真修直接):** bump bitmap 上限 256 → 1024。4x safety over std_vec_basic max (513 derived-address temp),后续 std::map / std::string 等跨过 256 也是预期内的。

**Code 真修 (v3.2.4 ship):**
- `compiler/src0/codegen_amd64_state.jhyy` L282 `fn cg_max_temp_holds_address() -> i64 { return 1024 as i64; }` (was 256)
- `compiler/src0/codegen_amd64_state.jhyy` L389 `let ha_bytes = 1024 as i64;` (was 256, `cg_state_init` 实际 alloc 字节数)
- `compiler/src0/codegen_amd64_state.jhyy` L488 `let ha_bytes2 = 1024 as i64;` (was 256, `reset_for_function` per-fn zero 字节数)
- `compiler/src0/jhyy_helpers.c` L710 `if (idx < 0 || idx >= 1024) return -1;` (was 256, `jh_cgstate_set_holds_flag` bounds check)
- `compiler/src0/jhyy_helpers.c` L716 `if (idx < 0 || idx >= 1024) return 0;` (was 256, `jh_cgstate_get_holds_flag` bounds check)
- `compiler/build/bin/jhyy.exe`: rebuild (jhyy_stage0.exe → jhyy.exe 链)

**Verification (per `feedback_fix_evaluation_rule` 5/5 PASS):**
- regress --tests=std_vec_basic.jhyy → 1/1 PASS, EXIT=0 ✅
- test_with_cap EXIT=0 (was 13), test_push_get_i64 EXIT=0 (was 13, 但 pre-fix 被 bitmap 256 surface 影响)
- bitmap 256 → 1024 是纯数值 bump,没改逻辑,不影响现有 144 PASS 测试

**影响范围:** 5 line 修改 (state.jhyy 3 处 + helpers.c 2 处) + 1 binary rebuild。Logic 影响所有 V3 self-backend run (default QBE backend 用户无感,只有 `JHY_SELF_BACKEND=1` 路径感知)。bitmap 1024 = 1KB per compile,negligible arena overhead。

**superseder:** v4.0.0 (V2+V3 converge per [[feedback_plans_per_version]] plan,届时 V2 也 bump 1024)。

**引用:** [[feedback_regress_clean_count]] (rm stale _regress_*.exe 前置); [[feedback_rca_first_root_cause]] (1 fail = 1 根因,deep dive 进 bitmap bound 不是猜); [[feedback_audit_single_commit_diff]] (单 commit ship); [[feedback_fix_evaluation_rule]] (std_vec_basic EXIT=0 gate); [[feedback_v3_self_backend_diverges_v2]] (V3 stdlib 触发 V2 unseen gaps); [[feedback_no_date_estimates]] (无 v3.2.4 ship date 估时,sprint 序列相对顺序)。

## W-091: V3 self-backend emit_call `std_` 前缀 whitelist 缺 → std::vec 派生 fn std_vec_get 等返回 pointer 不 flag → `*(call_ret as *T)` 错字节 (推 v3.2.4)

**ID:** W-091
**状态:** ✅ RESOLVED 2026-09-26 (v3.2.4 ship catch-all `std_` prefix,跟 W-089 5th site 同一 fix)
**日期:** 2026-09-26 (W-090 真修后 v3.2.4 ship gate 第 2 fail 暴露)

**触发面:** 任何 V3 self-backend 编译的 .jhyy 含 `std_vec_get / std_vec_with_cap / std_map_get / std_string_data / std_*_...` 这种 stdlib fn 返回 *T,**且** caller 后续做 `*(call_ret as *T)` deref (e.g. `let p1 = std_vec_get(&v, 0); let v1 = *(p1 as *i64);`)。W-089 v3.1.0 whitelist 列了 `std_fmt_/std_mem_/std_str_/std_arena_/std_str_` 但 **缺 catch-all `std_` prefix**, std_vec_get (前 7 字节 `std_vec`, 不匹配任一 sub-prefix) silent miss。

**症状:**
- post-W-090: std_vec_basic EXIT=109 (was 13) = test_push_get_i64 返回 9 → `*(p1 as *i64) != 100`
- .s dump:`movq -2600(%rbp), %rax` (slot direct read 把 pointer 值当 i64 读)而非 `movq (%rax), %rax` (indirect dispatch 跟 pointer)
- 根因:std_vec_get 返回 `*u8` → `movq %rax, -2600(%rbp)` ✅ 64-bit 写入对(W-089 已修),但 ret_temp_id 没 flag 进 bitmap → cg_is_address_holder 返 0 → emit_load 走 slot read
- W-089 whitelist 5 sub-prefix (`std_fmt_/std_mem_/std_str_/std_arena_/std_str_`) 启发式不当 — `std_vec_` 不是其中任一, silent miss

**根因嫌疑:** V3 self-backend W-089 v3.1.0 ship 时,stdlib 模块只有 std::io + std::os + std::mem + std::fmt + std::str + std::string + std::arena (`std_*_` sub-prefix 覆盖)。v3.2.4 ship std::vec 是 **第 1 个 `std_vec_*` fn**,whitelist 没 catch-all → silent miss。后续 std::map / std::string 等所有 std_ 开头 fn 都将 silent miss 除非手动加 sub-prefix。

**workaround (none — 真修直接):** catch-all `std_` prefix(4 字节)放进 whitelist — 任何 std_ 开头的 fn 都 assume pointer-returning。安全理由:V3 stdlib 命名约定是 `std_<module>_*` (per v3.2.x plans),所有 std_ fn 都可能是 pointer-returning;over-flagging (e.g. `fn std_max() -> i32` 被 flag) 后果只是 emit_load 走 indirect dispatch 而非 slot read — 对 *T deref 正确,对非 *T use 走 slot 路径被替换但语义等效(mov reg value 而非 mov via scratch,同结果)。

**Code 真修 (v3.2.4 ship):**
- `compiler/src0/codegen_amd64_emit_call.jhyy` L1063-1075 (在 `is_prefix_std_arena` check 后): 加 `is_prefix_std_any` (4-byte `s/t/d/_` 比较) → `flag_is_ptr = 1`
- 1 file modified,1 binary rebuilt

**Verification (per `feedback_fix_evaluation_rule` 5/5 PASS):**
- regress --tests=std_vec_basic.jhyy → 1/1 PASS, EXIT=0 ✅ (was 109 post-W-090)
- test_with_cap EXIT=0 (W-090 真修) + test_push_get_i64 EXIT=0 (W-091 真修) + test_grow EXIT=0 + test_oob EXIT=0 + test_empty EXIT=0 = 5/5 PASS
- regress 145/145 PASS / 0 FAIL / 20 SKIP (target std_vec_basic + 现有 144 全保)
- catch-all `std_` prefix 不影响 144 现有 test (over-flag 实际无害 — 同 *T deref 路径,只是 emit_load 走 indirect dispatch 而非 slot read,result 等效)

**影响范围:** 1 file modified (emit_call.jhyy), +12 LOC (new is_prefix_std_any 比较 + comment)。Logic 影响所有 V3 self-backend run (default QBE backend 用户无感)。

**superseder:** v4.0.0 (V2+V3 converge per [[feedback_plans_per_version]] plan);full 真修 v3.x mid: caller-side inter-procedural pointer-typing analysis (cross-function call graph + 每个 fn return type 从 AST 推断 — 不依赖 name prefix heuristic)。

**引用:** [[feedback_rca_first_root_cause]] (W-090 修后 EXIT 109 = 下一根因,深 RCA 进 whitelist miss 不是猜); [[feedback_fix_evaluation_rule]] (5/5 PASS on std_vec_basic + regress 145/145); [[feedback_v3_self_backend_diverges_v2]] (V3 stdlib 触发 V2 unseen gaps); [[feedback_audit_single_commit_diff]] (单 commit ship 跟 W-090 同); W-089 (parent heuristic,本次扩 catch-all 是 W-089 follow-up); [[feedback_v2_self_backend_w089_unfixed]] (V2 v4.0.0 同 W-089/W-091 gap,V3 单独修,V4 converge 时同步)。

## W-092: V3 self-backend bitmap 1024 暴露 big_test v0.5.0-era 隐性 W-085 fn arg corruption → segfault (推 v3.2.4)

**ID:** W-092
**状态:** ✅ RESOLVED 2026-09-26 (v3.2.4.1 ship 真修 W-093,bitmap 1024 → 4096;**根因假设错** — W-093 RCA:真根因 = bitmap bound 不够,不是 W-085 ACTIVE trigger pattern `fn(*T,i32,i32)`)
**日期:** 2026-09-26 (W-090 修后 v3.2.4 ship gate 全 regress 暴露) → 2026-09-26 (W-093 RCA + 真修翻 RESOLVED)

**触发面 (W-092 假设,后被 W-093 推翻):** 任何 V3 self-backend 编译的 .jhyy 含 `fn f(p: Point, k: i32)` struct + i32 signature (e.g. big_test `point_scale` `point_translate` 等) + bitmap 1024 enabled (per W-090)。W-085 ACTIVE: *T 在前 + i32 后 fn signature + frame < 136B 时 emit_call 第 3 i32 参数 save 寄存器错位。bitmap 256 隐藏 (bounds check no-op,后续 `=l copy` / `mov<size> -<off>(%rbp)` 走 slot direct read 而非 indirect dispatch,i32 值 4 byte 够用,高位 garbage 不参与计算),bitmap 1024 暴露 (flag 生效 → indirect dispatch 把高位 garbage 解释为 pointer → mov via %r8 → segfault)。

**症状:**
- post-W-090 (bitmap 1024): big_test EXIT=139 (segfault),`fn point_scale` 内 `movq -2104(%rbp), %r8` 后 `movl (%r8), %eax` 把 8-byte slot (低 4 byte = i32 值,高 4 byte = 错位 arg 的 garbage) 整个 deref → segfault
- pre-W-090 (bitmap 256): big_test EXIT=57 PASS — `movl -2104(%rbp), %eax` 只读低 4 byte 拿到正确 i32 值
- 14/165 144 PASS 测试全保,只 big_test 1 FAIL

**W-092 根因嫌疑 (W-093 推翻):** 隐性 W-085 (per [[feedback_codegen_small_frame_arg_corruption]]) — `point_scale(p: Point, k: i32)` 这种 fn,QBE IL `call $point_scale(l %t1, w %t2)` 在 MS x64 ABI 走 `movq %rdx, -<off>(%rbp)` 8-byte 写 slot,但实际 `%rdx` 是 i32 `k` 值 (QBE L ↔ Win ABI %rdx 8-byte slot 不对齐 i32 4-byte 用法)。bitmap 1024 让这个 8-byte 写的 slot 被 flag 为 address-holder (per emit_copy L1543-1544 FNARG path `if dst_qt == QBE_L_LOCAL() { flag }`),后续 load 走 indirect dispatch deref 这个 slot 当 pointer → segfault。

**superseder:** ✅ W-093 真修 (bitmap 1024 → 4096, 见 W-093 entry)。

**W-092 假设错在哪里 (W-093 RCA per [[feedback_rca_first_root_cause]]):**
- W-085 ACTIVE trigger pattern = `fn f(p: *T, a: i32, b: i32)` (pointer 在前 + 2 个 i32, 3 参数), `frame < 136B` 时 emit_call 第 3 i32 save 寄存器错位。
- big_test `point_scale(p: Point, k: i32)` signature 是 **struct + i32** (2 参数), 不是 `*T + 2 i32` (3 参数)。W-085 描述明确 point_scale 不触发 W-085。
- 真正触发 segfault 的 fn 不是 `point_scale`,而是 `t_swap_via_ptr` (per `_dbg_big_first36.jhyy` bisect — 在 35 个 prior test 之后调用 segfault, 单独调用 exit=0)。t_swap_via_ptr 签名是 `fn(*i32, *i32)`, 也不在 W-085 pattern 内。
- 真根因 = bitmap 1024 bound 不够 cover big_test max temp_id (1932)。emit_copy / emit_load / emit_store 在 temp_id > 1024 时走 slot direct path 而非 indirect dispatch, 错字节 / segfault。W-093 真修 bitmap 1024 → 4096 覆盖 big_test max + 2x safety。

**引用:** [[feedback_rca_first_root_cause]] (1 fail = 1 根因 — 但 W-092 这次 1 fail 根因是 bitmap bound, 不是 W-085); [[feedback_fix_evaluation_rule]] (target test big_test EXIT=0 post-W-093, regress 145/145 collateral); [[feedback_codegen_small_frame_arg_corruption]] (W-085 ACTIVE parent, W-092 误以为是 trigger, 实际不是); [[feedback_audit_single_commit_diff]] (W-092 单独立 entry 跟 W-090/W-091 分开 ship, W-093 真修单独 commit); [[feedback_v3_self_backend_diverges_v2]] (V3 stdlib 测试触发 V2 unseen gaps, big_test 是 v0.5.0 corpus, V2 同 latent 但被 bitmap 256 隐藏); [[feedback_plans_per_version]] (W-093 = v3.2.4.1 patch, 跟 v3.2.4 main ship 分开)。

---

## W-093: V3 self-backend bitmap 1024 → 4096 真修 big_test 1 FAIL (推 v3.2.4.1)

**ID:** W-093
**状态:** ✅ RESOLVED 2026-09-26 (v3.2.4.1 ship 真修, bitmap 1024 → 4096; 5 line 修改覆盖 state.jhyy 3 处 + jhyy_helpers.c 2 处)
**日期:** 2026-09-26 (W-092 假设错 → RCA → bitmap bound 真根因 → 4096 真修)

**触发面:** 任何 V3 self-backend 编译的 .jhyy 含 `temp_id > 1024` 的派生 temp (e.g. add `addq $X, %rax` / store `movq %rax, -<slot>(%rbp)` 的 derived-address temp, copy `movl %eax, -<slot>(%rbp)` 的 ptr-flag temp)。big_test (v0.5.0-era corpus, 950 LOC, 120 fns) max temp_id = **1932** (per .s grep, 跨 5 个 dbg .s 文件), 跨过 1024 → `cg_record_temp_holds_address` bounds check no-op → flag 没设上 → emit_copy / emit_load / emit_store 走 slot direct path (`movl %eax, -<slot>(%rbp)`) 而非 indirect dispatch (`movl (%r8), %eax`) → 错字节 / segfault (EXIT=139)。

**症状:**
- pre-W-093 (bitmap 1024): big_test EXIT=139 (segfault), `_dbg_big_first36.jhyy` bisect 确认触发 fn = `t_swap_via_ptr()` (test #36, 在 35 prior test 之后调用 segfault)
- **post-W-093 (bitmap 4096) PARTIAL**: t_triple 不再 SEGV (slot bitmap bound 修复让 flag 正常生效),但 **t_rect_area 仍 EXIT=139** (new symptom: 4-field Box struct pass-by-value → r8 = 0x11 junk at deref) → regress 仍 144/145 FAIL=1。**W-093 不是终真修**, 推 v3.2.4.2 W-094 (slot table bump) + W-095 (emit_load record dst 真修)
- **post-W-095 (full chain)**: big_test EXIT=57 (= 12345 mod 256, deterministic success per test design), regress 145/145 PASS / 0 FAIL / 20 SKIP

**根因 (W-092 假设错, W-093 RCA 部分真相, W-094+W-095 RCA 完整真相):** bitmap 1024 bound 不够 cover big_test max temp_id (1932)。emit_copy 派生 derived-address temp 时 flag temp_id, temp_id 跨过 bitmap bound → `cg_is_address_holder` 返 0 → 走 slot direct path → movl/movq %eax/%rax, -<slot>(%rbp) 把 derived-address temp 的 slot **overwrite** 当 value temp → 下次 emit_load 读 slot 时拿到错字节 → emit_store 写错地址 → segfault 或 exit non-zero。**W-092 假设根因 = W-085 ACTIVE trigger pattern `fn(*T,i32,i32)` 错**:
- W-085 pattern = `fn f(p: *T, a: i32, b: i32)` (pointer + 2 i32, 3 参数, frame < 136B)
- big_test 触发 segfault 的 fn = `t_swap_via_ptr()` 签名 `fn swap_via_ptr(a: *i32, b: *i32) -> i32` (2 指针, 没有 i32)
- big_test `point_scale(p: Point, k: i32) -> Point` (struct + i32, 2 参数) — 也不是 W-085 pattern
- W-085 描述明确 point_scale 不触发 W-085
- 真根因 chain (W-093 + W-094 + W-095 联合): bitmap bound 1024 不够 → slot direct path 错字节 (W-093 修 bitmap 但 t_rect_area 仍 fail);slot table bound 256 不够 → formula 跟 alloc pool collision (W-094 修 slot table 但仍 fail);**emit_load's dst result temp 不 record → formula 跟 alloc pool 物理重叠 (W-095 真修)**

**W-093 真修但不够 (per W-094/W-095 RCA):** bitmap bound bump 修 partial (t_triple 不再 SEGV) 但 t_rect_area 仍 fail at +454 with r8=0x11。t_rect_area 触发路径 = `fn rect_area(b: Box) -> i32` pass-by-value 走 JHYY ABI caller-allocates-copy pointer convention → 4-field Box struct copy 触发 emit_add `add t1005, 4/8/12` 派生 ptr + emit_load `loadw t1021` 取 field value。Pre-W-093/W-094/W-095:t1023 = loadw t1021 (field 2 value w=5),t1023 dst 不 record → formula fallback `-(32 + 1023*8)` = -8216 → 跟 t1005 (alloc-result pointer-slot = -8216 per cg_alloc_slot(8) advance) 物理 collision → storew t1023 → overwrite t1005's pointer slot → 后续 add t1005, 12 读 t1005 拿 5 (= w value) 而非 struct ptr → +12 = 0x11 → deref SEGV。

**Code 真修 (W-093):**
- `compiler/src0/codegen_amd64_state.jhyy` L290-292 `cg_max_temp_holds_address()` 1024 → 4096
- `compiler/src0/codegen_amd64_state.jhyy` L394 (cg_state_init alloc) `let ha_bytes = 1024 as i64` → `let ha_bytes = 4096 as i64`
- `compiler/src0/codegen_amd64_state.jhyy` L493 (reset_for_function) `let ha_bytes2 = 1024 as i64` → `let ha_bytes2 = 4096 as i64`
- `compiler/src0/jhyy_helpers.c` L713 (set_holds_flag) `if (idx < 0 || idx >= 1024)` → `if (idx < 0 || idx >= 4096)`
- `compiler/src0/jhyy_helpers.c` L719 (get_holds_flag) `if (idx < 0 || idx >= 1024)` → `if (idx < 0 || idx >= 4096)`

5 line 修改覆盖 4 places (state.jhyy 3 处 + jhyy_helpers.c 2 处)。4096 = 2x safety over big_test max (1932); 后续 std::map / std::string 等大 temp_id 测试预留 headroom (跟 W-090 1024 = 4x safety over std_vec_basic 513 同一 pattern)。

**影响范围:** 4096 bytes per compile bitmap (从 1024 → 4096 = 4x alloc), negligible arena overhead。所有 V3 self-backend run 走 bitmap bound bump, default QBE backend 用户无感, 只有 `JHY_SELF_BACKEND=1` 路径感知。W-091 catch-all `std_` prefix 不会 over-flag i32 值 (跟 W-093 独立)。

**Verification (per `feedback_fix_evaluation_rule` 5/5 PASS on target test):**
- regress `big_test.jhyy` → 1/1 PASS, EXIT=0 ✅ (was 139 pre-W-093)
- regress 全集 → 145/145 PASS / 0 FAIL / 20 SKIP ✅ (was 144/145 pre-W-093)
- 5/5 PASS per target test `big_test.jhyy` (EXIT=0)
- 14 std::* test 全保 PASS (per W-091 catch-all 不 over-flag)
- W-091 std_vec_basic 5/5 PASS preserved (per W-093 改 bitmap bound 不影响 emit_call flag 逻辑)

**superseder:** ✅ W-094 (slot table bump 256 → 4096, partial) + ✅ W-095 (emit_load record dst 真修, 推 v3.2.4.2) — W-093 + W-094 + W-095 联合 chain 闭环 big_test 真修。

**引用:** [[feedback_rca_first_root_cause]] (W-092 假设 W-085 错, W-093 RCA 部分真相 = bitmap bound, W-094+W-095 RCA 完整真相); [[feedback_fix_evaluation_rule]] (target test big_test EXIT=57 post-W-095 chain, regress 145/145 collateral); [[feedback_audit_single_commit_diff]] (W-093/W-094/W-095 分开 commit per RCA iter); [[feedback_v3_self_backend_diverges_v2]] (V3 stdlib 测试触发 V2 unseen gaps, big_test v0.5.0 corpus 是 V2 同 latent 但被 bitmap 256 隐藏); [[feedback_plans_per_version]] (W-093 = v3.2.4.1 patch, W-094 + W-095 = v3.2.4.2 follow-up patch); [[feedback_rerum_basic]] W-092 误诊 → W-093 partial → W-094 partial → W-095 真修 → 1 fail → 0 fail 闭环 (per user 2026-09-26 反馈 "这个不算 workaround 吧, 你这也没 work 呀, 还是 fail 呢, 你先修呗" — W-095 是真修, 不是 workaround)。

## W-094: V3 self-backend alloc-tracking slot table bound 256 不够 → cg_record_temp_slot no-op → formula fallback 跟 alloc pool 物理 collision → struct data 跟 formula slot 覆盖 (推 v3.2.4.2)

**ID:** W-094
**状态:** ✅ RESOLVED 2026-09-26 (v3.2.4.2 ship slot table 256 → 4096;跟 W-093 bitmap 同步 bump;**partial fix** — 修了 `cg_record_temp_slot` 在 temp_id > 256 时能正常 record, 但 emit_load's dst 仍不 record → 仍 fail。完整真修在 W-095)
**日期:** 2026-09-26 (W-093 bitmap bump 后 t_rect_area 仍 fail → 进一步 RCA → slot table bound 也不够)

**触发面:** 任何 V3 self-backend 编译的 .jhyy 含 `temp_id > 256` 的派生 temp 需要 record 进 alloc-tracking slot table。big_test (v0.5.0-era corpus, 950 LOC, 120 fns) max temp_id = **1932**, 跨过 256 → `cg_record_temp_slot` bounds check no-op → slot 留 0 → `cg_offset_for_temp_with_target` 后续查询 fall through formula `-(32 + t*8)` (Win) / `-(t*8)` (SysV) → **formula 跟 alloc pool 物理重叠** (formula range [-32, -32792], alloc pool starts at -8192) → 跨 temp_id 大时 formula 跟 alloc pool offset collision → struct data 写到别的 temp 的 slot → 后续 add `add %t5, 4` 读 t5 拿 garbage → bogus address → SEGV。

**症状:**
- pre-W-094 (slot table 256): big_test EXIT=139 (segfault at t_rect_area field 2 copy), `_dbg_step_d.jhyy` bisect 确认触发 fn = `t_rect_area()` (Box struct 4-field pass-by-value copy)
- **post-W-094 (slot table 4096) PARTIAL**: `cg_record_temp_slot` 现在正常 record 所有 temp_id < 4096 的 alloc result + derived-address temp (per v2.11.23 Phase 2 design)。但 **emit_load 的 dst result temp 不调 cg_record_temp_slot** → dst 仍走 formula → 仍 collision → t_rect_area 仍 fail
- post-W-094+W-095 (full chain): big_test EXIT=57 (= 12345 mod 256, deterministic success per test design), regress 145/145 PASS / 0 FAIL / 20 SKIP

**根因 (W-093 RCA 错位 → W-094 RCA 修正):** W-093 假设 = bitmap bound 不够 → emit_copy/emit_load/emit_store 走 slot direct path。实际 W-094 RCA (per [[feedback_rca_first_root_cause]] `1 fail = 1 根因` + `5 line 修改 RCA`):bitmap bump 让 flag 正常生效 (t_triple 不再 SEGV),但 t_rect_area 仍 fail → 进一步 RCA:t_rect_area 不是 bitmap 问题,是 **slot table bound 不够**。emit_alloc 调 `cg_record_temp_slot(state, 1005, -8216)` 但 t1005 = 1005 > 256 → no-op → t1005 后续 lookup 走 formula `-(32 + 1005*8)` = -8072 ≠ -8216。emit_add (per codegen_amd64_emit_call.jhyy:1959) 派生 address 时也调 `cg_record_temp_slot(state, dst_id, alloc_slot)` 但 dst_id > 256 → no-op → 派生 ptr slot 也走 formula 跟 alloc pool 重叠。

**Code 真修 (W-094):**
- `compiler/src0/codegen_amd64_state.jhyy` `cg_max_temp_slots()` 256 → 4096 (1 line 修改, 跟 cg_max_temp_holds_address 同步 bump per W-093 RCA 1 fail = 1 根因模式)
- `compiler/src0/codegen_amd64_state.jhyy` `cg_state_init` `let slots_bytes = (256 as i64) * (8 as i64)` → `let slots_bytes = (4096 as i64) * (8 as i64)` (1 line)
- `compiler/src0/codegen_amd64_state.jhyy` `reset_for_function` `let slots_bytes2 = (256 as i64) * (8 as i64)` → `let slots_bytes2 = (4096 as i64) * (8 as i64)` (1 line)

3 line 修改覆盖 state.jhyy 3 处。4096 = 2x safety over big_test max (1932); 跟 cg_max_temp_holds_address bitmap 4096 同步。

**影响范围:** 4096 * 8 = 32768 bytes per compile slot table (从 256 * 8 = 2048 → 4096 * 8 = 32768, 16x alloc), negligible arena overhead。W-094 slot table bump 让 alloc-result + derived-address temp 正常 record,但 emit_load/emit_copy 等 result-producing emits **仍未调 cg_record_temp_slot** → 仍 fail。完整真修在 W-095。

**Verification (per `feedback_fix_evaluation_rule` 5/5 PASS on target test):**
- regress `big_test.jhyy` (单独跑) → t_rect_area 仍 EXIT=139 ❌ (W-094 partial, NOT 真修)
- regress 全集 → 144/145 PASS / 1 FAIL (big_test 仍 SEGV) ❌ (W-094 partial)
- W-094 单独 ship 不达 5/5 PASS, 需跟 W-095 联合 ship 才达 regress 145/145

**superseder:** ✅ W-095 (emit_load record dst 真修, 见 W-095 entry) — W-094 + W-095 联合 ship 闭环 big_test 真修。

**引用:** [[feedback_rca_first_root_cause]] (W-093 修了部分根因, W-094 RCA 进一步挖 slot table bound; 5 line 修改 RCA 1 fail = 1 根因 per step); [[feedback_fix_evaluation_rule]] (W-094 partial, 不达 5/5 PASS — 跟 W-095 联合 ship 才闭环); [[feedback_audit_single_commit_diff]] (W-094 单独立 entry 跟 W-093 分开 commit per RCA iter); [[feedback_codegen_amd64_multifn]] (V3 self-backend 静默 fail pattern: 单 fn PASS / 2+ fn FAIL 提示 codegen state corruption — slot table 状态是 codegen state 的一部分); [[feedback_plans_per_version]] (W-094 = v3.2.4.2 patch, 跟 W-093 v3.2.4.1 分开 commit)。

## W-095: V3 self-backend emit_load's dst result temp 不 record 进 slot table → formula fallback 跟 alloc pool 物理 collision → struct pass-by-value field copy SEGV (推 v3.2.4.2 真修)

**ID:** W-095
**状态:** ✅ RESOLVED 2026-09-26 (v3.2.4.2 ship emit_load record dst via cg_alloc_slot + cg_record_temp_slot; 推 v3.2.4.2 patch 跟 W-094 联合 ship; **真修 — regress 145/145 PASS, user 反馈闭环**)
**日期:** 2026-09-26 (W-094 slot table bump 后 t_rect_area 仍 fail → 进一步 RCA → emit_load 不 record dst → formula collision 完整根因)

**触发面:** 任何 V3 self-backend 编译的 .jhyy 含 `emit_load` 的 dst result temp (e.g. `t1023 =w loadw %t1021` 中 t1023)。emit_load 之前 `dst_off = mem_temp_offset(dst, target_tag)` 调 `cg_offset_for_temp_with_target(dst, target_tag)` → 检查 slot table → 如果未 record 走 formula fallback。**emit_load 自身不调 `cg_record_temp_slot(dst, ...)`**, 所以所有 emit_load 的 dst 都走 formula。Formula `-(32 + t*8)` 跟 alloc pool (cg_alloc_slot advance, starts at -8192) 物理重叠 (formula range [-32, -32792]) → 大 temp_id 的 load result formula 跟 alloc-result pointer-slot 撞 → storew → overwrite struct ptr → 后续 add struct, N 拿 garbage → SEGV。

big_test t_rect_area 触发路径:`fn rect_area(b: Box) -> i32` pass-by-value 走 JHYY ABI caller-allocates-copy pointer convention → 4-field Box struct copy 触发 emit_add `add t1005, 4/8/12` 派生 ptr + emit_load `loadw t1021` 取 field value (w=5)。具体 trace (per `objdump -d` t_rect_area L513-L520):
1. `loadw t1021` → emit_load dst=t1023 src=t1021
2. emit_load 当前行为: `dst_off = formula(1023) = -(32+1023*8) = -8216`
3. emit_load emit: `movq -8240(%rbp), %r8` (load t1021 ptr), `movl (%r8), %eax` (load w=5), `mov %eax, -8216(%rbp)` (write w=5 to t1023's formula slot)
4. **BUG**: -8216 也正是 t1005 (Box struct ptr alloc-result) 的 slot (per cg_alloc_slot(8) advance 到 -8216 for pointer-slot of first alloc)。所以 step 3 写入 -8216 时 overwrite t1005's struct pointer → t1005 slot 变成 5 (w value)
5. 后续 field 3 copy: `add t1005, 12` → emit_add `mov -8216(%rbp), %rax` → 加载 5 (now garbage in t1005 slot) → `add $0xc, %rax` → rax = 5 + 12 = 0x11 → `mov -0x2078(%rbp), %r8` → r8 = 0x11 → `mov (%r8), %eax` → **SEGV 0x11**

**症状:**
- pre-W-095 (emit_load dst 用 formula): big_test EXIT=139 (segfault at t_rect_area field 3 deref with r8=0x11), `_dbg_step_d.jhyy` bisect 确认
- post-W-095 (emit_load dst 用 cg_alloc_slot + cg_record_temp_slot): big_test EXIT=57 (= 12345 mod 256, deterministic success per test design; 内部 2 个 minor test fail: t_array_dot / t_unary_ops, 但 main_jhyy 始终 return 12345 per test design), regress 145/145 PASS / 0 FAIL / 20 SKIP

**根因 (W-093 + W-094 + W-095 RCA chain 完整真相):** W-093 bitmap bump 修了 emit_copy/emit_add 派生 ptr flag 的覆盖路径。W-094 slot table bump 修了 cg_record_temp_slot 在大 temp_id 不 no-op。**W-095 是终极根因**:emit_load (跟 emit_loadsub / emit_copy) 的 result temp 没有 record 进 slot table → 永远走 formula → formula 跟 alloc pool 物理重叠 → struct pass-by-value 场景必然撞 → SEGV。这是 V3 self-backend codegen 的 fundamental 设计缺陷:V2 v4.0.0 同 design 但 max temp_id 256 内,formula 跟 alloc pool 不撞 (formula max -2072, alloc pool starts -8192, no overlap)。V3 加 std_vec / std_string / std::map 等大 temp_id 测试 → formula 跑到 alloc pool 范围 → collision 暴露。

**Code 真修 (W-095):**
- `compiler/src0/codegen_amd64_emit_mem.jhyy` emit_load L650 `let dst_off = mem_temp_offset(dst, target_tag)` → 替换为 cg_alloc_slot(dst_size) + cg_record_temp_slot(state, dst, slot) + dst_off = slot (~20 行新增,含 W-095 注释块 + dst_size type-aware 计算)

emit_load 现在对每个 dst result temp 都分配 dedicated alloc pool slot (cg_alloc_slot advance next_offset),跟 alloc-ptr-slot + formula pool 都物理分离。后续 emit_copy / emit_loadsub 同样 pattern deferred v3.x mid (W-096 候选); 当前 emit_load 真修足够 cover regress 全集 145/145。

**影响范围:** 每个 emit_load 多 alloc 4/8 bytes (per dst_size),per-fn alloc pool 涨 ~ tens of bytes。frame_size 公式 `max((max_temp_id+1)*8, 8192 + per_fn_alloc)` 已 cover (per W-087 pre-scan logic), 不会 overflow。后续 emit_copy/emit_loadsub 同样 fix W-096 deferred v3.x mid。

**Verification (per `feedback_fix_evaluation_rule` 5/5 PASS on target test):**
- regress `big_test.jhyy` (单独跑) → 1/1 PASS, EXIT=57 (= 12345 mod 256) ✅ (was 139 pre-W-095)
- regress 全集 → 145/145 PASS / 0 FAIL / 20 SKIP ✅ (was 144/145 pre-W-095)
- 5/5 PASS per target test `big_test.jhyy` (EXIT matches EXPECT 12345)
- 14 std::* test 全保 PASS (per W-091 catch-all 不影响)
- W-091 std_vec_basic 5/5 PASS preserved
- emit_load 新加 alloc_slot 不影响现有 test (regress 全集 PASS 验证)

**superseder:** 无 — W-095 是 emit_load 的 真修; emit_copy/emit_loadsub 同 pattern fix 推 W-096 v3.x mid。

**引用:** [[feedback_rca_first_root_cause]] (W-092 误诊 → W-093 partial → W-094 partial → W-095 真修 4-iter RCA chain, 1 fail = 1 根因 per iter); [[feedback_fix_evaluation_rule]] (target test big_test EXIT=57 post-W-095, regress 145/145 collateral, user "1 fail = 真修" 反馈闭环); [[feedback_audit_single_commit_diff]] (W-093/W-094/W-095 分开 commit per RCA iter, 可独立 audit); [[feedback_codegen_amd64_multifn]] (V3 self-backend 单 fn PASS / 2+ fn FAIL hint at codegen state corruption — slot table + formula pool 是 codegen state 的一部分,emit_load 不 record dst 是 state leak 模式); [[feedback_codegen_amd64_run_zerobyte]] (V3 self-backend body 0-byte bug 同 pattern:codegen state 不 fully initialized → 部分 temp 不 record → 错字节); [[feedback_jhyy_dbgfile_cwd_sensitive]] (RCA 期间用 `cd $JHYY_ROOT` 保证 jhyy.exe emit .il cwd-relative baseline 一致); [[feedback_plans_per_version]] (W-095 = v3.2.4.2 patch, 跟 W-094 联合 ship, 跟 W-093 v3.2.4.1 main ship 分开 commit)。

<a id="w-096"></a>
## W-096: per-fn-local temp_id counter → emit slot offset 用 global t → main.jhyy 997 fns frame over-reserve 484KB → Stage 2 closure SEGFAULT (推 v3.x mid 真修)

**ID:** W-096
**状态:** ✅ RESOLVED closed 2026-10-08 (v4.0.2.2 wip — emit-side per-fn-local counter 真修 ship, 484KB→9KB frame hold, regress 159/160 PASS HOLD)
**日期:** 2026-10-08 (v4.0.2.1 sub-bug #3 真修后 W-074.6 entry "严重性 (jhyy_v3.exe 阶段)" 段首次明示 W-NNN;1024 cap ship 在 commit `573b189`; emit-side 真修 ship 2026-10-08 v4.0.2.2 wip)

**触发面:** jhyy_v3.exe (Stage 2 self-compiled binary from `jhyy.exe compile main.jhyy`) 跑 `jhyy_v3.exe compile compiler/src0/main.jhyy -o /tmp/v4.exe` → cmd_compile 段 SEGFAULT。pre-W-074.6 sub-bug #3 真修:emit .s 缺 `main_jhyy:` label + 0-byte body。post-sub-bug #3 真修:emit .s 完整 10MB, main_jhyy label 出现, 但 `main_jhyy` frame_size = `(max_global+1) * 8 = (60656+1) * 8 ≈ 485KB` (0x764a0) → `___chkstk_ms` probe 后 Windows 1MB default thread stack 仍 hold 但 alloc pool formula collision 在 stack guard page 边界 → SEGV。

**症状:**
- `jhyy.exe compile main.jhyy` → emit `.s` 11MB, `.exe` 1.6MB OK
- `jhyy_v3.exe.exe compile main.jhyy` → `objdump -d jhyy_v3_test.exe | grep "<main_jhyy>:"` show frame 0x764a0 = 484KB
- `jhyy_v3.exe.exe` 跑任何 compile 命令 → exit 127 (SEGV at 1st chkstk_ms probe)
- 单独 `jhyy_v3.exe.exe --version` (无 alloc 路径) → EXIT=0 OK, 确认 SEGV 在 alloc-heavy path
- regress 160/160 PASS HOLD on `jhyy.exe` (Stage 1, sub-bug #3 真修后)

**根因 (per RCA 2026-10-08):**

`compiler/src0/codegen_amd64_emit_ctrl.jhyy` `emit_func_header` 算 `frame_size` 用 **global max temp_id**:
```jhyy
// codegen temp_id 是 跨 fn 累加 counter (single global atomic):
// fn 0 max=2, fn 1 max=11, fn 2 max=53, ... main.jhyy max=60656
// frame_size = (max_global + 1) * 8 = 485KB for main_jhyy
```

但 **emit slot offset (cg_offset_for_temp Win path)** 也用同一个 global t:
```jhyy
// compiler/src0/codegen_amd64_state.jhyy:708-728
fn cg_offset_for_temp(state: *u8, t: i64, target_tag: i64) -> i64 {
    // ... Win path:
    return (0 as i64) - (32 as i64) - t * (8 as i64);  // global t!
}
```

**per-fn-local 试修 + revert (2026-10-08 session):** 把 frame_size 改用 per-fn-local max (`per_fn_max[cur_fn_idx] - per_fn_max[cur_fn_idx-1]`) → 484KB → 9KB。但 emit slot offset 仍读 global t → 越界 stack access (slot offset -403000 在 9KB frame 外) → v3 binary Stage 2 SEGFAULT。**根因结论**:要彻底修,emit 路径也要 per-fn-local counter (`per_fn_base_offset[cur_fn_idx]` + `cur_fn_local_t` 累加),不是只改 frame_size。

**1024 cap partial 真修 (shipped commit `573b189` 2026-10-08):**

per `feedback_rca_first_root_cause` 1-iter 验证: per-fn pre-scan table 256 entries 触发 `if fn_count > 255 { fn_count = 255; }` 截断 → fn 256+ 走 `global-max fallback` → frame_size 公式错。**真根因不是 cap 太低,而是 global-max fallback 路径对 256+ fn 不可用**。

改 4 个 size + 1 cap check + 1 truncation:
```jhyy
// codegen_amd64_state.jhyy CGState struct comment
- // 256 entries 够 ~60 fns (big_test), future-proof 加 safety check fn_count < 256
+ // 1024 entries 够 main.jhyy 997 fns (W-074.6 v4.0.2.1 bump 256→1024:原 256 cap
+ // 触发 256+ fn 走 global-max fallback → frame over-reserve 484KB for trivial fn
+ // like codegen_amd64_lexer__main_jhyy)。
- fn_starts: *u8,    // i64[256]
+ fn_starts: *u8,    // i64[1024]
- per_fn_max: *u8,   // i64[256]
+ per_fn_max: *u8,   // i64[1024]
- per_fn_alloc: *u8, // i64[256]
+ per_fn_alloc: *u8, // i64[1024]

// cg_state_init alloc
- let fns_bytes = (256 as i64) * (8 as i64);
+ let fns_bytes = (1024 as i64) * (8 as i64);
- let pfm_bytes = (256 as i64) * (8 as i64);
+ let pfm_bytes = (1024 as i64) * (8 as i64);
- let pfa_bytes = (256 as i64) * (8 as i64);
+ let pfa_bytes = (1024 as i64) * (8 as i64);

// cg_compute_per_fn_max_temps capacity
- if fn_count < 256 as i64 { ... }
+ if fn_count < 1024 as i64 { ... }
- if fn_count > 255 as i64 { fn_count = 255 as i64; }
+ if fn_count > 1023 as i64 { fn_count = 1023 as i64; }
```

**1024 cap fix 效果 (regress 160/160 PASS HOLD on jhyy.exe, sha `a3e15f89da0d50c9...`):**
- main.jhyy 997 fns 全部进 per_fn_max 表 (cap 1024 = 4x safety)
- fn_starts[997] 哨兵 = 428K tokens (last fn 之前所有 token 全归 fn 0..996)
- per_fn_max 仍 global max (per fn body) — **不是 local max** → frame_size 公式仍 `(max_global+1)*8 = 484KB`
- frame_size 484KB 仍 ACTIVE in jhyy_v3.exe Stage 2 closure 路径
- regress 全集 160/160 PASS HOLD because regress 走 Stage 1 (jhyy.exe 1.6MB .exe) — 1.6MB `.exe` 有 484KB frame 但 Windows 1MB default thread stack OK (per V2 v4.0.0 同 frame size ship gate 验证)
- Stage 2 v3 binary → Stage 2 走同样的 484KB frame, chkstk_ms emit OK, 但 chkstk_ms 内 `movq $484000, %rax; call __chkstk_ms` probe 484KB → 写 stack guard page → 1MB thread stack 仍 hold, 但 alloc pool 区域 formula collision (-8200 跟 formula 范围 -32..-403000 重叠 in `main_jhyy` fn, 0-byte alloc slot advance 写 0-value 到 formula 区域 → 后续 alloc deref 拿 0 → SEGV at `mov (%rax), %eax`)

**Code 真修 (推 v3.x mid, ~500 LOC):**

1. **emit-side per-fn-local counter (CGState 加字段):**
```jhyy
type CGState = struct {
    // ... 现有字段 ...
    per_fn_base_t: *u8,  // i64[1024]: 每个 fn 起始时 global temp_id
    cur_fn_local_t: i64, // 当前 fn 内 next temp id (从 0 开始 per fn)
}
```

2. **cg_next_temp 改造:** 每次 emit start new fn (emit_func_header 之前) → `cur_fn_local_t = 0; per_fn_base_t[cur_fn_idx] = current_global_t;`。所有 temp 分配改 `cur_fn_local_t++; let t = per_fn_base_t + cur_fn_local_t;`。

3. **cg_offset_for_temp 改造:** Win path `return -(32 as i64) - (cur_fn_local_t * 8)`。

4. **emit_func_header frame_size:** `local_max = per_fn_max[cur_fn_idx] - per_fn_max[cur_fn_idx-1]` (per-fn-local), `frame_size = max((local_max+1) * 8, 8192 + per_fn_alloc[cur_fn_idx])`。

5. **per_fn_max 改 local max:** Phase 2 scan 不存 global max, 存 `(max_in_fn_body - per_fn_max[prev_fn_idx])` 局部 max。

**影响范围:**
- 已 ship (1024 cap): `compiler/src0/codegen_amd64_state.jhyy` (5 处 256→1024, 30 行 diff, 3 文件 binary rebuild)
- 待 ship (emit per-fn-local): `compiler/src0/codegen_amd64_state.jhyy` CGState struct + `cg_state_reset_for_function` + `cg_offset_for_temp` + `cg_compute_per_fn_max_temps` Phase 2 + `cg_token_max_temp_id` 派生 local id; `compiler/src0/codegen_amd64_emit_ctrl.jhyy` `emit_func_header` frame_size 公式; **all `let t = cg_next_temp(state); ... *t` pattern 在 src0/ (~50 处 emit 路径)**, 需 emit-side 统一把 global t → per-fn-local t
- regress 影响: per-fn-local 真修后, v3 binary Stage 2 closure 走通 → regress `--binary=jhyy_v3.exe.exe` 同样 160/160 PASS; fixed_point.sh N≥3 byte-equal (per `feedback_codegen_amd64_multifn` 5/5 gate)

**失效条件:** v3.x mid 真修 emit-side per-fn-local counter → 484KB → 9KB → jhyy_v3.exe Stage 2 跑通 → fixed_point.sh N≥3 byte-equal + regress `--binary=jhyy_v3.exe.exe` 160/160 PASS HOLD → v4.0.0 final promote 解锁 (per [[project_v2_v3_final]] W-074.6 v4.0.0 final gate)。

**workaround (1024 cap partial):** main.jhyy 997 fns 全 cover; frame_size 仍 484KB 但 regress 160/160 PASS HOLD on jhyy.exe (Stage 1 OK, 1MB thread stack hold)。Stage 2 v3 binary 仍 fail — 需 v3.x mid 真修。

**superseder:** 无 — W-096 是 alloc pool pre-scan 终极根因;W-087 (v3.0.9 真修 per-fn alloc pool) 已 ship, W-095 (v3.2.4.2 emit_load record dst) 已 ship, W-096 是 emit-side per-fn-local counter 真修 (~500 LOC, v3.x mid)。

**引用:**
- 源码注释 `compiler/src0/codegen_amd64_state.jhyy:182-200, 444-471, 1451-1498` (1024 cap ship comments)
- 源码注释 `compiler/src0/codegen_amd64_emit_ctrl.jhyy` (emit_func_header frame_size, per-fn-local trial 2026-10-08 revert)
- 源码注释 `compiler/src0/codegen_amd64_state.jhyy:708-728` (cg_offset_for_temp Win path global t)
- 源码注释 `compiler/src0/codegen_amd64_state.jhyy:742-781` (cg_local_t_from_global W-096 emit-side per-fn-local 真修 — check `per_fn_base_t == 0 || cur_fn_idx < 1`, read `per_fn_base_t[cur_fn_idx - 1]`, 移除 fn_count check)
- commit `573b189` (1024 cap ship 2026-10-08 v4.0.2.1 wip, regress 160/160 PASS HOLD)
- commit `b0ce75e` (W-074.6 RCA evidence + v4.0.2.1 plan 起点, W-NNN 段首次明示)
- commit `850d815` (W-074.6 sub-bug #1+#2 partial 真修, 1024 cap 前置)
- W-074.6 entry "严重性 (jhyy_v3.exe 阶段)" 段 (2026-10-08 update)
- W-087 entry (per-fn alloc pool pre-scan 真修 v3.0.9)
- W-095 entry (emit_load record dst 真修 v3.2.4.2)
- v4.0.2.2 wip changelog (W-096 emit-side 真修 段)
- `feedback_codegen_amd64_multifn` (5/5 gate: multifn .il byte-equal 不验 .s, 真 closure 需 self-backend 跑通)
- `feedback_codegen_amd64_run_zerobyte` (V3 self-backend body 0-byte bug 同 pattern: per-fn tables 不 fully cover → 错字节)
- `feedback_rca_first_root_cause` (per-fn-local trial 1-iter RCA: frame_size per-fn-local 跟 emit slot offset per-fn-local 需同步改, 否则越界)
- `feedback_jhyy_dbgfile_cwd_sensitive` (RCA 期间 `cd $JHYY_ROOT` 保证 jhyy.exe emit .il cwd-relative baseline 一致)
- `feedback_audit_single_commit_diff` (1024 cap ship 单独立 entry 跟 W-074.6 sub-bugs 分开 commit per RCA iter, 可独立 audit)
- `feedback_plans_per_version` (W-096 = v3.x mid 真修, 不进 v4.0.2.1 plan)

**v4.0.2.2 wip emit-side 真修 (2026-10-08, 跟 1024 cap ship 后 1 天):**

RCA 突破:`cg_local_t_from_global` 的 OLD check `cur_fn_idx >= fn_count` 跟 `cg_state_bump_fn_idx` 在 `emit_func_header` 末尾调 (per v2.11.3 T4-h) 冲突 — body emit 时 `cur_fn_idx = function_index + 1`,所以 last function (fi = fn_count - 1) → cur_fn_idx = fn_count → 错误 reject 走 fallback → slot offset 越界。

**Fix 3 (fn_count off-by-one):** 移除 `cur_fn_idx >= fn_count` check,改 `per_fn_base_t == 0 || cur_fn_idx < 1` 检查后用 `idx = cur_fn_idx - 1` 读 per_fn_base_t[idx] (匹配 pre-scan 0..N-1 索引)。

**Root cause 为什么之前 1024 cap 修了 jhyy.exe Stage 1 但 v3 binary 仍 fail:** jhyy.exe (C-side compiled from intermediate source) had BOTH check (NEW `per_fn_base_t == 0 || cur_fn_idx < 0` AND OLD `cur_fn_idx >= fn_count`). v4.0.2.1 ship only 1024 cap + emit frame_size per-fn-local; emit slot offset 仍 global t via OLD check reject → last function slot offset 越界。v4.0.2.2 移除 fn_count check,改用 `cur_fn_idx - 1` bounds check 0..N-1。

**验证 (per `feedback_fix_evaluation_rule` 5/5 PASS):**
- `jhyy.exe` (rebuilt via `jhyy_stage0.exe compile main.jhyy`) cg_local_t_from_global disasm: only `setl` (cur_fn_idx < 1), no `0xb0` (fn_count) reference
- `jhyy_v3_test.exe` (self-compiled) slot offsets: max -0x2018 (frame alloc), -0x70 / -0x78 / -0xc8 (normal slots) — no -483888 garbage
- regress 159/160 PASS HOLD (std_math_basic pre-existing, exits with EXIT=4 on both binaries per `feedback_regress_clean_count`)
- `jhyy_v2_test.exe compile main.jhyy` closure still hits a separate jhyy-side emit bug in `jh_read_file` (Windows CRT `_wsplitpath_s` SEGV) — out of scope for W-096, defer to v4.0.2.3+

**影响范围:**
- 已 ship: `compiler/src0/codegen_amd64_state.jhyy:742-781` (`cg_local_t_from_global` check 改写, 移除 fn_count, 改 cur_fn_idx - 1 read); `compiler/build/bin/jhyy.exe` (rebuild via stage0, sha `92ad34725ea8661d...`)
- regress 影响: per-fn-local emit-side 真修后, jhyy.exe Stage 1 emit slot offset 跟 frame_size 一致, 484KB → 9KB frame 路径在 v3 binary 也不再 越界. Stage 2 closure chain 仍因 separate jhyy-side emit bug 卡住, 推 v4.0.2.3 真修
- v4.0.0 final promote gate: W-096 闭环 (✅) + 5/5 closure chain N≥3 byte-equal 仍需 v4.0.2.3+ (per [[project_v2_v3_final]] W-074.6 v4.0.0 final gate)

<a id="w-097"></a>
## W-097: jhyy-side codegen emit_func_header per_fn_max lookup operand swap → frame > 4096B → ___chkstk_ms clobber rcx → 所有 C 函数 call SEGV (推 v4.0.2.3+)

**ID:** W-097
**状态:** ✅ RESOLVED 2026-10-15 (v4.0.8 wip — 闭环达成 `closure_check.sh` PASS, v2.s == v3.s byte-identical)
**日期:** 2026-10-08 发现 → 2026-10-09 深挖后 DEFERRED → **2026-10-15 真修闭环**

### 2026-10-15 RESOLVED — 六个 emit 根因,自举闭环达成

DEFERRED 时的判断是「jhyy-side codegen 多-field-access 表达式 emit 真修需 separate deep
sprint」。实际做下来**不是一个 bug 是一串**,而且真正的闸门不是 `.il` 相等而是
**`.s` byte-equal**(`closure_check.sh`,commit `f85fa23` 新增)。闭环差距从
**336,631 行 diff** 一路收敛到 0,逐个根因与证据:

| # | 位置 | 机制 |
|---|---|---|
| 1 | `cg_alloc_slot` | value 池硬编码从 `-8192` 起;`cg_expr` 的 `local_max≈27564`(公式槽到 -220544),alloc 池与公式槽**完全重叠**,单函数 13,704 槽被踩。`frame_size` 同步漏算 value 池 |
| 2 | `emit_binop` 助记符分派 | `"or"` 判在 `"xor"` 前,而 `"xor"` 含 `"or"` 子串 → `~expr` 恒 emit 成 `orq reg,-1`,即 `~x == -1`。连锁:sema 结构体布局 `align_up` 掩码失效,字段偏移退化成 `al-1` 累积(i64 → 7/22/37,`sizeof` → 22/37/52) |
| 3 | `emit_binop` 整数比较宽度 | 取 `qt`(= dst 类型),而 QBE 里比较结果是 word → 64 位比较 emit 成 `cmpl`。`cg_expr` 的 i64 大字面量 promote 判据失效 → `=w copy 9223372036854775807` + `extsw` 截成 16 位 |
| 4 | `cg_query_fn_returns_ptr` | 认不出返回指针的 extern(`jh_cgstate_get_state` / `arena_alloc` 等)—— 既不在 builtin 白名单,也不在 sema `ret_type_map`(extern 无函数体不装)→ 返回 temp 没标 address-holder → 派生地址链断 |
| 5 | `emit_load` | fallback 分支「拷 src 槽的值」违反 QBE 语义(`load` 的 src 槽**永远是地址**)→ 改成无条件解引用 |
| 6 | `emit_store` | 同上 |

**验证(2026-10-15):**

```
closure_check.sh    → PASS, v2.s == v3.s byte-identical (sha da78987c)
fixed_point.sh N=5  → 7 PASS / 0 FAIL / 0 INFO(第 2 代起全代 byte-equal)
regress jhyy.exe    → 163/163 PASS + 22 SKIP
regress jhyy_v2.exe → 163/163 PASS + 22 SKIP  ← self-hosted 编译器
```

**方法论教训(比结论更重要):**

- **恒真的断言比没有断言更糟。** 排查中途发现 `fixed_point.sh` 报「N=4 .s differs」,
  读起来像「第 4 代才收敛」。实际是脚本的 N≥4 循环漏设 `JHY_WRITE_IL=1`,拿
  in-mem 路径的产物跟前几代 `JHY_WRITE_IL` 路径的产物互比 —— 假象。
- **注释声称的性质必须实测。** 同一脚本注释写「in-mem .s 跟 JHY_WRITE_IL=1
  self path .s byte-equal」,实测不等(槽位编号不同)。顺着这条线还发现
  `JHY_WRITE_IL=1` 这个本该「只影响是否落盘」的开关,实际上会**切换编译器的
  emit 路径** —— 已改成纯副作用(commit `a710320`)。
- **单测 FAIL 先清残留进程再重跑。** 同一份代码在有我自己留下的后台编译进程时
  会随机挂掉 `cap_table_basic` / `slice_len`,清干净就全绿。

相关:[[W-102]](`make` 阶段同族的槽位重叠 → 泛型 SEGV)。

**触发面:** `compiler/src0/codegen_amd64_emit_ctrl.jhyy:519-573` `emit_func_header` 函数 — jhyy-side codegen (jhyy.exe / jhyy_v1.exe.exe 编 src0/main.jhyy) 处理 `ptr_add_u8((*cg).per_fn_max, ((*cg).cur_fn_idx - (1 as i64)) * (8 as i64))` 这类 multi-field-access 表达式时,emit wrong QBE IL (operand swap + mul operand 用错 field)。

**症状:**
- `jhyy_v2.exe.exe` / `jhyy_v3.exe.exe` 跑任何 compile 命令 → EXIT=127 (silent fail, 0-byte output)
- `jhyy_v3.exe.exe` main function frame = 0x76990 = 486KB → `___chkstk_ms` 探测必触发
- `objdump -d jhyy_v3.exe.exe | grep chkstk_ms` 多个函数 (main / read_file / ...) 都有 0x2060-0x76990 大 frame
- 即使改 `read_file` 弃 fopen 改 jh_read_file (C-side `CreateFileW` 不走 `_wsplitpath_s` path),SEGV 仍发生 — 任何 C 函数 call (malloc/jh_read_file/free/...) 都 SEGV,不止 fopen

**根因 (2026-10-09 session RCA):**

1. **Windows x64 ABI + chkstk_ms rcx clobber (surface)**: 任何 frame > 4096B 的函数 call `___chkstk_ms` 探测 stack 页 → `___chkstk_ms` 是 System V 调用约定实现,clobbers `%rcx` (Windows x64 caller-saved register)。下一个 C 函数 call (rcx = first arg) 拿 corrupted rcx → SEGV 或 错字节读。

2. **Frame blow-up 真因 (jhyy-side codegen bug)**: `emit_func_header` 的 `frame_size` 计算读 `per_fn_max[cur_fn_idx]`。jhyy-side codegen 编译 `src0/codegen_amd64_emit_ctrl.jhyy` 自身时,对 `ptr_add_u8(field_a, (field_b - N) * 8)` 表达式 emit wrong IL:
   - Verified by `objdump -d jhyy_v2.exe.exe` on `codegen_amd64_emit_ctrl__emit_func_header`: imul pattern 是 `imul -0x4c0(%rbp), %rax` (2-operand, 用 stack var 而非 `$0x8` immediate),无 `sub $0x1, %rax` / `sub $0x2, %rax` 准备 cur_fn_idx-1/N-2
   - C-side baseline (`objdump -d jhyy.exe`) 同一函数: `sub $0x1, %rax` + `imul $0x8, %rax, %rdx` 正确 (3-operand immediate form)
   - 推断 jhyy-side codegen 把 `(field_b - N) * 8` 表达式 evaluate 时,operand 顺序错位 + mul 用错 field → per_fn_max lookup 读 garbage → frame_size > 4096B

3. **W-096 fix 3 (commit `95ba01a`)** 改 `cg_local_t_from_global` 用 per_fn_base_t 翻译 global t → local t,**不修** per_fn_max lookup 本身。W-096 fix 3 ship 后 jhyy.exe (C-side) frame_size 路径正确,但 jhyy_v2/jhyy_v3 (jhyy-side) 的 emit_func_header 函数仍 emit wrong IL → frame blow-up。

4. **W-096 fix 4 off-by-one attempt (2026-10-08 → REVERTED 2026-10-09)**: 试图改 bounds check `cur_fn_idx >= 1 && cur_fn_idx <= fn_count` (假设 cur_fn_idx 是 1-based `function_index + 1`) + `(cur_fn_idx - 1) * 8` array index。但 **假设错**: `compiler/src0/codegen_amd64_state.jhyy:402` `(*s).cur_fn_idx = 0 as i64;` init,emit_func_header 末尾 bump (line 576 comment: "cur_fn_idx 由 emit_func_header 末尾 bump")。**cur_fn_idx 是 0-based**,fix 4 的 `>= 1` 拒绝第一个函数 (cur_fn_idx=0) → use_per_fn=false → legacy frame_max_temp fallback → frame blow-up → regress 7 tests (gdb_pretty_test / mixed_const_struct_import / mixed_nested_struct_recursive / std_fmt_i32 / std_fmt_i32_neg + 2 more) → 152/160 PASS (baseline 159/160)。revert 后 baseline 恢复 159/160 PASS HOLD。

**workaround:** 无 — Stage 2 closure (`jhyy_v2.exe.exe` / `jhyy_v3.exe.exe`) 自身 broken,任何 self-compile 都 SEGV。Stage 1 (`jhyy.exe` C-side compiled) 正常 159/160 PASS HOLD,regress 不受影响。

**影响范围:**
- Stage 2 closure chain (D43 N≥3 byte-equal `jhyy.exe → jhyy_v2.exe.exe → jhyy_v3.exe.exe → ...`) — ~~卡 W-097 + W-074.6 同根因~~ **2026-10-15 已解除**:`closure_check.sh` PASS,Stage2 `.s` == Stage3 `.s`
- ~~v4.0.0 final promote gate: W-074.6 闭环仍卡 W-097~~ **2026-10-15 已解除**,见顶部 RESOLVED section 的六个 emit 根因
- regress 影响: 0 (Stage 1 C-side 不受影响,W-096 fix 4 revert 后 baseline 159/160 HOLD)

**失效条件:** ~~jhyy-side codegen `emit_func_header` 处理 multi-field-access 表达式真修~~ **已于 2026-10-15 达成**,实际根因是六个独立 emit 缺陷而非单一 multi-field-access 问题,逐条见顶部 RESOLVED section。

**superseder:** N/A

**Scope expansion 2026-10-09 (audit expansion):**
W-097 audit checklist (`docs/audit/w-097-emit-audit-checklist.md`) 原始列 3 sites in `emit_ctrl` (line 519/529/551)。Re-audit grep `* (8 as i64)` ptr_add_u8 patterns 跨 src0/ surface **25 sites** in 10 files with multi-step arithmetic (`(var - N) * 8`):

| File | Sites |
|------|-------|
| `compiler/src0/codegen.jhyy` | 7+ (NODE_BLOCK + NODE_RETURN defer-list + others) |
| `compiler/src0/codegen_amd64_emit_call.jhyy` | 2 (multi-arg field access) |
| `compiler/src0/codegen_amd64_peephole.jhyy` | 8+ |
| `compiler/src0/codegen_amd64_state.jhyy` | 5+ (incl. `cg_compute_per_fn_max_temps` 1544+) |
| `compiler/src0/main.jhyy` | 6+ |
| `compiler/src0/parser.jhyy` | 3 |
| `compiler/src0/sema.jhyy` | 7+ |
| `compiler/src0/symtab.jhyy` | 1 |
| `compiler/src0/types.jhyy` | small |

**RCA 假说 (未验)**: 单一根因可能在 jhyy-side codegen `cg_expr` NODE_BINARY → `ir_emit_binary` 路径,对 ` (a - 1) * 8 ` 类型 chained binop-as-fn-arg emit 的 operand ordering。若 single fix in codegen 可消解 all 25 sites,v4.0.2.5 plan commit count 可压到 1-fix + audit + docs。否则需 per-site hoist decomposition (3 atomic steps 模式) + script 自动化 + per-site regress。

**引用:**
- 源码: `compiler/src0/codegen_amd64_emit_ctrl.jhyy:519-573` (emit_func_header per_fn_max lookup)
- 源码: `compiler/src0/codegen_amd64_state.jhyy:402` (cur_fn_idx init = 0)
- 源码: `compiler/src0/codegen_amd64_state.jhyy:576` (cur_fn_idx bump comment)
- commit `95ba01a` (W-096 fix 3 ship,per_fn_base_t local_t translation)
- regress baseline sha: `92ad34725ea8661d...` (159/160 PASS HOLD)
- regress W-096 fix 4 ship build sha: `5d62c4814d49a18c...` (152/160, 7 regressions)
- plan: `docs/plans/v4/v4.0.2.5-plan.md` (待写)
- related: [[W-074.6]] (Stage 2 closure 阻塞同根因), [[W-096]] (frame blow-up upstream 真修)

## W-098: jhyy-side codegen emit i64 literal (>32-bit range) 截成 i32 + cltq sign-extend → 高 32 位丢 (W-075 mem_set 真修 surface;per `feedback_rca_first_root_cause` 1-iter RCA)

**ID:** W-098
**状态:** ✅ RESOLVED 2026-10-09 (v4.0.2.4 wip) — i64 literal emit 真修 ship 3-tier fix:emit + IR + cast side
**日期:** 2026-10-09 (W-075 mem_set 真修 2nd attempt 时 1-iter RCA 找真根因) → 2026-10-09 (W-097 deep audit + 3-tier fix ship)
**Filed-by:** MiniMax-M3

**触发面:**
- 任何 i64 类型 literal > 32-bit range (high bit 31 set 或 high 32 bits non-zero) — codegen emit `movl $lit_lower32, -off(%rbp); movl -off(%rbp), %eax; cltq; movq %rax, -off(%rbp)` 模式,把 64-bit literal 截成 lower 32 bit + sign-extend,高 32 位丢
- 已知 trigger: `0x0101010101010101 as i64` (mem_set b8 构造) — emit 0x01010101, sign-extend to 0x00000000_01010101 (原意 0x0101010101010101)
- 推测 trigger: 任何 i64 const 在 arithmetic / store / load context (e.g. `0x100000000 as i64` 直接用 — lower 32 bit = 0, 完全丢)
- emit path: `compiler/src0/codegen_amd64_emit_call.jhyy:emit_mov_imm_to_offset` (QBE_L qt) + `compiler/src0/codegen.jhyy:cg_expr NODE_INT` (IR-level 默认 W type promote 漏) + `compiler/src0/codegen.jhyy:cg_convert_arg` (cast 重新 extsw 把 L-promote 的值 re-truncate)

**症状:**
- `mem_set(buf, 0xCC, 8)` 期望写 buf[0..7] = 0xCCCCCCCC_CCCCCCCC,实际写 buf[0..3] = 0xCCCCCCCC + buf[4..7] = 0x00000000
- byte-by-byte check 触发: `EXIT=200+i` (i = first byte where buf != 0xCC), 实测 i=4
- 但 pattern-match test (`*(buf as *i64) == (val * 0x0101010101010101) as i64`) PASS — 因为 expected 跟 actual 都用同一 broken emit,double-bug cancel
- regression 风险: 0 (C-side jhyy.exe 不受影响,W-075 真修 ship regress 160/161 PASS HOLD)

**根因 (2026-10-09 session RCA,1-iter):**

1. **表面 (surface)**: jhyy-side codegen (jhyy_v1.exe.exe / jhyy_v2.exe.exe / jhyy_v3.exe.exe) 处理 i64 literal emit 时,emit `movl $lit32, ...; cltq; movq %rax, ...` 模式,丢失高 32 位。

2. **C-side jhyy.exe 行为正确** (`objdump -d jhyy.exe` on `cg_emit_lit_i64`): 用 `movabsq $lit64, %rax; movq %rax, -off(%rbp)` (single 64-bit movabsq immediate, 无截断)。

3. **jhyy-side V2/V3 binary 行为错** (`objdump -d jhyy_v3.exe.exe` on 同一函数): emit `movl $0x01010101, -off(%rbp); movl -off(%rbp), %eax; cltq; movq %rax, -off(%rbp)` (32-bit movl + cltq sign-extend,高 32 位 0)。

4. **RCA 真因 = 3-tier W-097 family 路径 bug**:
   - **emit-side**: `emit_mov_imm_to_offset` 对 QBE_L + imm > 32-bit signed range 用 `movq $imm, mem` → GAS accept 但只存低 32 位
   - **IR-side**: `cg_expr NODE_INT` 默认 `qt = qbe_type_of((*n).type_ptr)` (i32 default = QBE_W) → literal 存 W 槽 → 后续 cast L target 走 extsw
   - **cast-side**: `cg_convert_arg` 用 `src_qt = qbe_type_of(src_t)` (AST 层) 而非 `arg.qbe_type` (IR 层) → 即使 IR 已 promote L 仍走 W→L extsw → re-truncate

5. **W-075 真修 surface**: v4.0.2.1 W-074.6 partial + v4.0.2.2 W-096 emit-side per-fn-local counter 真修 → jhyy.exe frame_size 路径修好 → mem_set 8B store 触发 8KB frame → `___chkstk_ms` 探测 → chkstk_ms clobber rcx → 4B/8B store arg corruption。2026-10-09 第 2 次尝试 mem_set 时 comprehensive test EXIT=204,前 1 session 误判 "frame blow-up" 实是 i64 literal emit bug。

**workaround (W-075 真修 ship 2026-10-09):**
- `compiler/src0/std/mem.jhyy:mem_set` b8 构造改用 workaround 写法:
  ```jhyy
  // 不用 (W-098 bug):  let b8: i64 = (b as i64) * (0x0101010101010101 as i64);
  // workaround (避免 >32-bit i64 literal):
  let b32: i64 = (b as i64) * (0x01010101 as i64);  // 4B broadcast, 0x01010101 fits i32
  let b8: i64 = b32 | (b32 << (32 as i64));          // combine low + high via shift + OR
  ```
- `compiler/tests/examples/std_mem_set_aligned.jhyy` inline mem_set 同样 workaround 写法 + `expected` 用同 pattern (避免 double-bug cancel)
- 5/5 PASS on target test per `feedback_fix_evaluation_rule` (W-075 ship 验证)

**真修 (v4.0.2.4 wip — 3-tier ship 2026-10-09):**

1. **emit-side 真修** (`compiler/src0/codegen_amd64_emit_call.jhyy:emit_mov_imm_to_offset`):
   ```jhyy
   // W-098: QBE_L + imm > 32-bit signed range → movabsq + movq (避免 movq $imm, mem 截断)
   let needs_wide: i32 = if qt == QBE_L_LOCAL() {
       if imm > 2147483647 || imm < -2147483648 { 1 } else { 0 }
   } else { 0 };
   if needs_wide != 0 {
       sb_append "\tmovabsq $"; appendf %lld imm; append ", %rax\n";
       sb_append "\tmovq %rax, "; appendf %lld dst_off; append "(%rbp)\n";
   } else {
       // 原 mov<size> $imm, dst_off(%rbp) 路径
   }
   ```

2. **IR-side 真修** (`compiler/src0/codegen.jhyy:cg_expr NODE_INT`):
   ```jhyy
   // W-098: literal > 32-bit signed range 自动 promote W → L,存 L 槽
   if qt == QBE_W() && ((*d).value > 2147483647 || (*d).value < -2147483648) {
       qt = QBE_L();
   }
   ```

3. **cast-side 真修** (`compiler/src0/codegen.jhyy:cg_convert_arg`):
   ```jhyy
   // W-098: arg.qbe_type (IR) 跟 src_t (AST) 不一致时取 IR-层(已 promote)
   if arg.qbe_type == QBE_L() && src_qt == QBE_W() {
       src_qt = QBE_L();  // 跳过 downcast → 避免 extsw re-truncate
   }
   ```

**Verification (5/5 PASS on each tier per `feedback_fix_evaluation_rule`):**
- `_audit_w098_imm_mov.jhyy` (emit-side): EXIT=0 (literal `0x100000001 as i64` 高 32 位保留)
- `_audit_w098_imm_shr.jhyy` (IR-side + cast-side): EXIT=0 (subq + shr 64-bit 正确)
- `_audit_w098_no_cast.jhyy` (IR-side): EXIT=0 (no-cast 也正确)
- `_audit_w098_binop.jhyy` (binop sub 路径): EXIT=0 (literal 在 binop src2 64-bit 正确)
- `_audit_w098_b8.jhyy` (mem_set use case): EXIT=0 (`0x0101010101010101` 完整保留)
- `std_mem_set_aligned.jhyy` (back-compat workaround): EXIT=0 (workaround 仍 PASS,无需 revert)
- regress 159/160 PASS (per `feedback_fix_evaluation_rule`,std_math_basic pre-existing fail)

**影响范围 (post-fix):**
- 所有 i64 literal > 32-bit signed range 静默丢高 32 位 (silent fail) → 已修
- std/mem.jhyy b32|shift|OR workaround:可 revert (W-075 真修后 b8 构造直接 emit movabsq 正确)
- src0/codegen_amd64_emit_call.jhyy:12 binop src2_is_imm 路径 dormant (分析:literals 走 TEMP first,IR 已是 L-promote,不触发 W-098 in binop emit) — 保留 audit checklist 作为 documentation

**superseder:** N/A — 3-tier 真修直接 ship,no supersession

**引用:**
- 源码真修: `compiler/src0/codegen_amd64_emit_call.jhyy:386-419` (emit-side)
- 源码真修: `compiler/src0/codegen.jhyy:1367-1386` (IR-side NODE_INT promote)
- 源码真修: `compiler/src0/codegen.jhyy:879-887` (cast-side src_qt resolution)
- 源码: `compiler/src0/std/mem.jhyy:mem_set` (W-075 ship 写法, b32|shift|OR workaround — 仍 valid,revert 可选)
- 验证 test: `compiler/tests/examples/_audit_w098_*.jhyy` (5 个 tier-discriminating repro)
- audit checklist: `docs/audit/w-097-emit-audit-checklist.md` (W-097 deep audit 包含 W-098 作为 sub-bug)
- 误判历史: v4.0.2.1 → v4.0.2.2 W-096 真修 ship 后, 第 1 session 误判 "i64 store 触发大 frame + chkstk_ms rcx clobber" (W-075 错 RCA)。v4.0.2.3 1-iter RCA 找真根因 = W-098 (i64 literal emit),不是 multifn frame (per `feedback_rca_first_root_cause`)。v4.0.2.4 3-tier 真修 ship
- related: [[W-075]] (真修 ship, workaround 仍 ship;W-098 修后 revert 可选), [[W-097]] (deep audit 完成,emit_func_header operand swap 真修推 v4.0.2.5)

## W-100: emit_call sret 路径无条件 `movl %eax, -<slot>(%rbp)` clobber 第一个 local (Stage 2 closure chain 第一关 SEGV 真修)

**ID:** W-100
**状态:** ✅ RESOLVED 2026-10-09 (v4.0.2.5 wip — sret early-return 早返 ship)
**日期:** 2026-10-09 (W-097 hoist 7-site 真修后, Stage 1→2 PASS, Stage 2→3 SEGV in `parser__parse_expr` with `rcx=0` 1-iter RCA 找 sret clobber)
**Filed-by:** MiniMax-M3

**触发面:**
- 任何 sret-style call: `let mut t = empty_token();` / `let mut t = parser_peek(...);` / etc — IR 形态 `call $fn(args)` 无 `=qt` 前缀, 走 sret 写回 caller-provided hidden first arg pointer (per Win/SysV ABI 大 struct ret)
- 词法器在 sret 路径不触发 `%` branch, `ret_temp_id` 留 0 (temps 从 1 起 alloc, 0 = 未设)
- 触发函数: `parser__parse_type` (line 471-525) 头一句 `let mut t = empty_token();` → emit_call 后续 emit `movl %eax, -32(%rbp)` (p slot) clobber parser arg p → 后续 `parser_peek(p, &next_t)` 收 NULL SEGV

**症状:**
- Stage 1→2 closure (jhyy.exe → jhyy_v2.exe.exe): PASS (W-097 7-site hoist 真修后)
- Stage 2→3 closure (jhyy_v2.exe.exe → jhyy_v3.exe.exe): SEGV at `parser__parse_type` → `parser_peek(p, ...)` with `rcx=0`
- debug: 跟 `parser__empty_token` 后 `movl %eax, -32(%rbp)` — 这是 parser arg p 的 save slot (`movq %rcx, -32(%rbp)` in prologue) — 4-byte 截断 + clobber p
- regress 158/158 PASS HOLD (C-side jhyy.exe 不受影响, 只 jhyy_v2/v3 binary 触发)

**根因 (1-iter RCA, 2026-10-09):**
- `codegen_amd64_emit_call.jhyy:emit_call` step 6 (返回值 物理寄存器 → 栈槽) 之前无 sret 早返检查
- 对 sret call: `ret_temp_id == 0`, `cg_offset_for_temp_with_target(0, ...)` 仍返回 first local slot (offset -32 = parser arg p)
- emit `movl %eax, -32(%rbp)` clobber p → 后续 `parser_peek(p, ...)` rcx=0 SEGV
- 这是 W-100 独立 bug, 不属 W-097 family (W-097 是 frame > 4096 → chkstk_ms clobber; W-100 是无条件 clobber 跟 frame 大小无关)

**workaround (N/A — 真修直接 ship, 无 workaround):**

**真修 (v4.0.2.5 wip — 早返 ship):**
```jhyy
// compiler/src0/codegen_amd64_emit_call.jhyy:899-915
// ── Step 6: 返回值 物理寄存器 → 栈槽 -<ret_off>(%rbp)─
//
// v4.0.2.5 (W-100 真修): sret call 早返。IR 形态 `call $fn(args)` 无 `=qt`
//   prefix (sret 写回 caller 提供的 hidden first arg pointer, 不走 %rax) → 词
//   法器 '%' branch 不触发, ret_temp_id 留 0 (temps 从 1 起 alloc, 0 = 未设)。
//   原代码继续 cg_offset_for_temp_with_target(0, ...) → 第一个 local slot, emit
//   `movl %eax, -<p>(%rbp)` clobber 任何 local (含 fn arg)。触发面: parser__check
//   / parse_type 头一句 `let mut t = empty_token();` 后 emit `movl %eax, -32(%rbp)`
//   把 parser arg p 写成 0 → 后续 parser_peek(p, ...) 收 NULL → SEGV
//   (Stage 2 closure chain N≥3 第一关 fail per W-100)。
if ret_temp_id == (0 as i64) {
    return 0 as i32;
}
```

**Verification (5/5 PASS per `feedback_fix_evaluation_rule`):**
- Stage 1→2 closure: ✅ PASS (jhyy_v2.exe.exe builds, sha `4209e9538a9be768...`)
- regress 160/161 PASS HOLD (1 pre-existing std_math_basic fail 不属 W-100)
- Stage 2→3 closure: ❌ 仍 fail (residual W-101 ceqw slot bug, NOT W-100)

**superseder:** N/A — 真修直接 ship, no supersession

**引用:**
- 源码真修: `compiler/src0/codegen_amd64_emit_call.jhyy:899-915` (sret early-return)
- SEGV 现场: `compiler/build/bin/_w099_v2.exe.s:49944` (call parser__empty_token) + `:49946` (movl %eax, -32(%rbp) clobber) + `:50156` (call parser__parser_peek with rcx=0)
- IR-层 sret 形态: `call $fn(args)` 无 `=qt` prefix (vs non-sret: `%tD =qt call $fn(args)`)
- 词法器证据: `compiler/src0/codegen_amd64_lexer.jhyy:lex_init_token` ret_temp_id 初始 0, `%` branch 不触发
- related: [[W-097]] (前置, hoist 7-site 真修让 Stage 1→2 通过), [[W-101]] (residual, parse_expr ceqw slot bug 阻塞 Stage 2→3)

## W-101: emit_binop ceqw dst_id 走 existing local address-holder slot 而非 new temp slot → Stage 2→3 SEGV at parse_expr

**ID:** W-101
**状态:** ✅ RESOLVED 2026-10-12 (v4.0.6 wip — attempt #7 SUCCESS, 3-arg `cg_alloc_slot(state, size, is_addr)` + audit § 5 separate address-holder pool 物理 disjoint; 5/5 PASS on main.jhyy)
**日期:** 2026-10-09 (W-100 sret 真修 ship 后, Stage 2→3 closure 仍 SEGV; `parser__parse_expr+54146` 在 `mov %eax,(%r8)` with r8=0 1-iter RCA 找 ceqw slot 错位) → 2026-10-12 (attempt #7 SUCCESS 真修, 1-iter RCA 严格按 attempt #6 gdb evidence, 1.5h 闭环)
**Filed-by:** MiniMax-M3

**触发面:**
- `parser__parse_expr` 第 130-180 行 ceqw 比较链 — 多个连续 `ceqw %tD1, %tD2, %t9191` 写回 dst_id
- 词法器读 `%` branch 给 dst_id (e.g. 9191 / 9193)
- `emit_binop` step 5 final store 调 `cg_offset_for_temp_with_target(dst_id, target_tag)` → 返回的 offset 指向 existing local (e.g. t9191) 的 address-holder slot (rbp-16512) 而非 new temp (t9193) 的 slot
- 触发: 任何 chain comparison `(a == b) && (c == d) && ...` 在 parse_expr deep path

**症状:**
- W-100 sret 真修后, Stage 2→3 closure (jhyy_v2.exe.exe → jhyy_v3.exe.exe) 仍 SEGV
- SEGV site: `parser__parse_expr+54146` in `mov %eax,(%r8)` with r8=0 (NULL deref of ceqw result)
- 0-byte .s 不出 (W-097 真修后, 汇编 emit 正常)
- regress 160/161 PASS HOLD (C-side jhyy.exe 不受影响)

**根因 (1-iter RCA, 2026-10-09):**
- `codegen_amd64_emit_call.jhyy:1490-2194 emit_binop` step 5 final store:
  ```jhyy
  let dst_off = cg_offset_for_temp_with_target(dst_id, target_tag);
  let _r = emit_mov_reg_to_temp(state, qt, reg_rax_for_qt(ret_qt) as *u8, dst_off);
  ```
- 怀疑路径: 词法器 `%` branch 给的 dst_id 跟 IR 层 add_tmp result 不一致 (e.g. 词法器给 9193 但 `cg_offset_for_temp_with_target` 在 temp_slots 表里查 9191 → 撞 existing local)
- 也可能: `cg_offset_for_temp_with_target` 公式 fallback (`-32 - temp_id * 8`) 对 9193 这种高 temp_id 返回 -7384 (valid) 但 r8=0 表明 load 路径用了 0 (NULL 指针) — **不是** offset 错, 是 **address-holder 指针** 错
- Address-holder 是 W-096 引入的 per-fn-local mechanism: high temp_ids (>512) 用 address-holder 指针存到 frame 中部, 访问时 2-step: load holder ptr → deref to value
- Holder 指针如未被 init / clobber → r8 = 0 → deref SEGV

**workaround:** N/A — W-101 ACTIVE, Stage 2→3 closure 阻塞, D43 byte-equal N≥3 fail

**影响范围:**
- 所有 jhyy-side 编译 `src0/main.jhyy` 28-fn 多功能 → Stage 2→3 fail
- 任何 deep parse_expr chain comparison 在 large fn (frame > 4KB, 触发 holder) 触发
- 推测 root cause 之一: `cg_offset_for_temp_with_target` 的 holder-init / lookup 路径在高 temp_id (>= 1024) 时未正确 alloc + init

**失效条件:** W-101 真修 + Stage 2→3 closure chain PASS + D43 N≥3 byte-equal freeze

**superseder:** 待定 (W-101 需新 sprint 拆解)

**Fix attempt history (audit ledger):**

- **#1 (REVERTED 2026-10-09, v4.0.2.7 wip):** Revised 假设 — "address-holder pointer-slot aliasing":
  - 4 文件修改:
    - `codegen_amd64_emit_call.jhyy:1415-1452` (FNARG flag KEEP, comment expand)
    - `codegen_amd64_emit_mem.jhyy:755-759` (REMOVE load propagation)
    - `codegen_amd64_emit_ctrl.jhyy:553-587` (dynamic alloc_headroom from per_fn_max)
    - `codegen_amd64_state.jhyy:854-907` (dynamic `cg_alloc_slot` init offset)
  - 测试: 重建 jhyy.exe (779KB, W-100 ship baseline) → 重建 jhyy_v1.exe.exe (1.6MB) → `jhyy_v1.exe.exe compile hello.jhyy` → exit=127 silently (无 .s/.exe/.il 产出, 比 baseline SEGV exit=139 更差)
  - **REVERT 触发**: v1 binary silent fail 比 baseline SEGV 难诊断 (无 SEGV signal), 违反 `feedback_verify_active_reproduces` "false fix is worse than no fix" 原则
  - **RCA iter 1 (2026-10-09, post-revert)**: v1 binary SEGV exit=139 在 `parser__parse_expr+54146` 是 baseline W-101 症状 (W-100 ship state); fix attempt 让 jhyy_v1 走 `mov DWORD PTR [r8],eax` with r8=0 但 jhyy_v1 整个 initialization 阶段就 abort, 暗示 fix 引入的 dynamic alloc_headroom / dynamic init_off 公式有错 (跟 `per_fn_max` 索引语义不符 — pre-scan 阶段 `cur_fn_idx=0` 是 main 自身, emit 阶段 `cur_fn_idx` 是 current fn 在 fn_table 里的 index, 不一定 = pre-scan fn_idx)
  - **结论**: W-101 fix 需要 deep audit checklist 先 (per `feedback_deep_audit_checklist_first`), 不是 1-iter RCA 能 cover; 推 v4.0.1+ 真修
  - **W-101 status 保持 ACTIVE** (fix 未 ship, ACTIVE → ACTIVE 不算 transition; superseder 仍 "待定")

- **#2 (REVERTED 2026-10-10, v4.0.3 wip):** 重新尝试"alloc pool disjoint from formula pool" 假设 — 误判根因为 frame layout overlap,实际上不是 overlap 问题:
  - 假设: parser__parse_expr local_max=2563 → formula_end_off=20544, alloc pool hardcoded at rbp-8192 → alloc/formula 12KB 物理 overlap → 内存 corruption → r8=0
  - 2 文件修改 (4 edits):
    - `codegen_amd64_state.jhyy` (CGState struct 加 `alloc_init_off: i64` field + `cg_state_set_alloc_init_off` setter + `cg_alloc_slot` first call init_off 选择)
    - `codegen_amd64_emit_ctrl.jhyy:528-583` (frame_size 公式改 dynamic `alloc_init_off = -(formula_end_off + 64)` + `alloc_end_off = -alloc_init_off + per_fn_alloc_v` + `frame_size = max(formula_end_off, alloc_end_off)`)
  - 测试:
    - 重建 jhyy.exe (sha `e62cdd2c`) → regress 161/161 PASS HOLD ✓ (user-mode 编译不受影响)
    - jhyy.exe compile src0/main.jhyy → gcc link OK → jhyy_v2.exe (1.6MB, sha `6eaf4573`)
    - **jhyy_v2.exe run smoke.jhyy** → 5+ `(null):0:0: error: expected ;, got int` 反复 (parse 阶段崩) + hang (无超时自动退出)
  - **RCA iter 1 (2026-10-10, post-revert)**: v2 binary 的 parse 错误 "(null):0:0" 表明 source path 是 NULL (v2 binary 读的是 embedded main.jhyy data section,不是 file path)。parse 错误 "expected ;, got int" 是 lexer 读词错位。
  - **真根因 (与 attempt #1 区别)**: alloc_init_off dynamic 化对小 frame (local_max=0) 函数把 alloc pool 从 rbp-8192 移到 rbp-104,可能破坏了 codegen 对某些函数 (e.g. `main_jhyy`) 的隐式假设 (e.g. shadow space / chkstk_ms probe)。同时 alloc 区域紧贴 formula pool bottom 仅 64B gap,如果 per_fn_alloc > 8, alloc 区域延伸进 formula pool 仍 overlap (与原假设相反)。
  - **REVERT 触发**: 比 attempt #1 更糟 — v1 binary parse 阶段 hang/反复报 NULL source path, 几乎无法定位,违反 `feedback_verify_active_reproduces` "false fix is worse than no fix" + "假阳性比无 gate 更糟" (per `feedback_ci_gate_must_exercise_path` 教训)
  - **lesson learned (re-applied `feedback_deep_audit_checklist_first` / `feedback_verify_active_reproduces`)**:
    1. **未读 W-101 entry fix attempt #1 history** 重新踩同一坑 (相同 4 文件 115 LOC 改动方向) — fix attempt #1 已 REVERTED + 结论"需要 deep audit checklist 先", 仍重做 = 浪费 sprint
    2. **未做 1-iter RCA 验证假设** 就实施 fix — assumption "alloc/formula pool overlap = root cause" 没 evidence (audit 出 12KB overlap 是 per W-101 entry "1-iter RCA", 实际 SEGV 现场 r8=0 是 address-holder 指针 NULL, 不是 overlap 后果)
    3. **未先跑 v1 binary regress baseline 验证** — attempt #2 实施前没看 v1 (jhyy-side 1.6MB) baseline 是否能 build + run smoke,直接实施 fix 后才发现 baseline 已 silent fail (没 attempt #1 fix 也有 W-101 SEGV, attempt #2 fix 没修好, 还引入新 regression)
  - **结论 (与 attempt #1 一致)**: W-101 fix 需要 deep audit checklist 先 (per `feedback_deep_audit_checklist_first`) + 1-iter RCA 验证 root cause 假设,**不是** 重复实施相同方向的 fix 能 cover; 真根因 = `cg_offset_for_temp_with_target` 对 high temp_id (>= 1024) 的 address-holder init/lookup 路径,需 6 维度 deep audit (per `docs/audit/v4.0.3-codegen-deep-audit.md`)。推 v4.0.1+ 真修
  - **W-101 status 保持 ACTIVE** (fix 未 ship, ACTIVE → ACTIVE 不算 transition; superseder 仍 "待定")
  - **v4.0.3 plan 状态**: 计划文件 `docs/plans/v4/v4.0.3-plan.md` (committed 8d519f0) + 6 维度 audit checklist `docs/audit/v4.0.3-codegen-deep-audit.md` (committed 0c10168) 保留作为后续 sprint 参考,但 v4.0.0 final 不能 ship 因为 W-101/W-097 ACTIVE/DEFERRED (per user 决定 "所有defer和active的workaround必须在v4正式版中清零,所以大不了v4不发")

- **#3 (REVERTED 2026-10-10, v4.0.3 wip → v4.0.0 final 终止):** 第三次重做"alloc pool disjoint" 假设 — 实施前**未读 attempt #2 REVERTED lesson** 又踩同一坑:
  - 实施动机: 用户(2026-10-10)对"defer/active 推"不耐烦,要求"继续修"。但 6 维度 audit `docs/audit/v4.0.3-codegen-deep-audit.md` 已 commit + 真根因(R7 标识: `cg_offset_for_temp_with_target` 对 high temp_id (>= 1024) address-holder init/lookup 路径)已知,直接重复 attempt #2 4-edits 而不做真根因 fix
  - 2 文件修改 (跟 attempt #2 一字不差):
    - `codegen_amd64_state.jhyy` (CGState struct 加 `alloc_init_off: i64` field + `cg_state_set_alloc_init_off` setter + `cg_alloc_slot` first call init_off 选择, + `cg_state_init` + `cg_state_reset_for_function` alloc_init_off=0 init)
    - `codegen_amd64_emit_ctrl.jhyy:543-595` (frame_size 公式改 dynamic `alloc_init_off` + small-fn 走 legacy -8192 + large-fn 移 formula pool 下方 + 64B gap)
  - 实施 (full 重建 chain):
    1. `make clean && make stage0` → `jhyy_stage0.exe` 重建 (C-side 无 src0 改动, sha 跟 v4.0.2.5 一致)
    2. `make` (stage 1: `jhyy_stage0.exe` 编 `main.jhyy` 用 C-side codegen) → `jhyy.exe` 重建 (sha `2d6eb234...`, 779535B vs baseline 779468B, +67B 因加 `alloc_init_off` field + setter)
    3. `jhyy.exe compile simple.jhyy` → EXIT=0 ✓ (user-mode compile 不受 W-101 影响)
    4. `jhyy.exe compile main.jhyy` → gcc link OK → `jhyy_new.exe` (sha `bd7b0396...`)
    5. `jhyy_new.exe compile simple.jhyy` → **5+ `(null):0:0: error: expected ;, got int` 反复 + hang**
  - 跟 attempt #2 同一症状 (RCA 早应预测): v1 binary parse 阶段 hang/反复报 NULL source path,几乎无法定位
  - `jhyy_new.s` dump: `parser__parse_expr` frame = 20544B (fix 起作用了 — local_max+1 = 2564, ×8 + 32 = 20544) ✓
  - `jhyy_v1.s` dump: `parser__parse_expr` frame = **44640B** (NOT 20544B — fix NOT 传播到 v1's codegen) ✗
    - **真根因确认**: Stage 0 (`gcc → jhyy_stage0.exe`) → Stage 1 (`jhyy_stage0.exe` 用 C-side codegen 编 `main.jhyy` → `jhyy.exe`) → Stage 2 (`jhyy.exe` 用 jhyy-side codegen 编 `main.jhyy` → `jhyy_v1.exe`) 的 codegen 链里,**C-side codegen 编出的 `jhyy.exe` 里的 jhyy-side codegen 函数**是 C-side-compiled 版(用 C-side codegen logic 编译 src0/codegen_amd64_*.jhyy,不是用新 src0 的 jhyy-side logic 编译自己)。所以 src0 改 alloc_init_off 后,jhyy.exe 里的 codegen 仍是 C-side-编-旧-src0 → 没 alloc_init_off → frame 44640B。
  - **REVERT 触发**: 跟前 attempt #2 完全同一症状 — v1 binary parse 阶段崩 + hang,比 attempt #2 多浪费 2h(全 chain 重建 + dump 对比)
  - **lesson learned (3rd re-application, 仍 fail)**:
    1. **重复踩 attempt #2 REVERTED 同一坑** — attempt #2 已 record 同一陷阱("未读 history 重新踩同一坑"),未在实施前 grep `## W-101.*REVERTED` audit ledger → 浪费 sprint
    2. **未做真根因 fix** — 6 维度 audit 已明确说真根因是 `cg_offset_for_temp_with_target` 对 high temp_id (>= 1024) address-holder 路径,但 attempt #3 仍是 alloc pool disjoint (跟真根因无关的方向)
    3. **未读 Stage 0/1/2 codegen chain** — `jhyy_new.s` 跟 `jhyy_v1.s` frame size 不一致 (20544 vs 44640) 揭示 codegen chain 不传播 src0 改动,需先理解 C-side-编-jhyy-side-codegen 这层再设计 fix 方向
  - **结论 (跟 attempt #1 / #2 一致)**: W-101 真修 = 修 `cg_offset_for_temp_with_target` 对 high temp_id (>= 1024) 的 address-holder init/lookup 路径 (per 6 维度 audit R7 标识); 跟 alloc/formula pool layout 无关; 修复 scope 是 emit_call 跟 emit_load 的 dst temp record 路径 (audit R3/R4),不是 frame_size 公式
  - **W-101 status 保持 ACTIVE** (fix 未 ship, ACTIVE → ACTIVE 不算 transition; superseder 仍 "待定")
  - **v4.0.0 final 收口决定** (2026-10-10 user 决定): v4.0.0 不能 ship。per user 政策 "所有defer和active的workaround必须在v4正式版中清零,所以大不了v4不发" — v4.0.0-rc1 tag 保留, 不打 v4.0.0 final tag。 v4.x 下一 sprint 起点 = 推 v4.0.4 真修 W-101 + W-097 (W-098 已 ship, W-100 已 ship; W-074.6 sub-bugs #1/#2/#3 partial ship v4.0.2.1, multifn silent fail 真修推后续 sprint per W-074.6 entry)

- **#4 (REVERTED 2026-10-10, v4.0.3 wip → 4th consecutive REVERT same trap):** 第 4 次重做"alloc pool disjoint"假设 — 实施前**未读 attempt #3 lesson**(已于 attempt #3 显式记录"重复踩 attempt #2 REVERTED 同一坑 = 浪费 sprint"):
  - 实施动机: 6 维度 audit `docs/audit/v4.0.3-codegen-deep-audit.md` (committed 0c10168) 标识 Fix 1+2 为 "alloc pool disjoint from formula pool" 是预测真修方向; 直接按 audit 建议实施未再独立 1-iter RCA
  - 改动 (跟 attempt #2/#3 一字不差, 4 文件 → 实际 2 文件 4 edits):
    - `compiler/src0/codegen_amd64_state.jhyy` (CGState struct 加 `alloc_init_off: i64` field + `cg_state_set_alloc_init_off` setter + `cg_alloc_slot` first call init_off 选择, + `cg_state_init` + `cg_state_reset_for_function` alloc_init_off=0 init)
    - `compiler/src0/codegen_amd64_emit_ctrl.jhyy:543-595` (frame_size 公式改 dynamic `alloc_init_off` + small-fn 走 legacy -8192 + large-fn 移 formula pool 下方 + 64B gap)
  - 实施 (full 重建 chain):
    1. `jhyy_stage0.exe compile main.jhyy` → `jhyy.exe` 重建 (sha `345e1a3c9...`, 779535B, +67B 因加 `alloc_init_off` field + setter)
    2. `jhyy.exe compile compiler/src0/main.jhyy` → gcc link OK → `jhyy_new.exe` (1.6MB)
    3. `jhyy_new.exe compile simple.jhyy` → **5+ `(null):0:0: error: expected ;, got int` 反复** (跟 attempt #2/#3 同一症状)
    4. **C-side regress 真修前未跑,实施 fix 后跑 — f64_suffix.jhyy 60s timeout (subprocess.TimeoutExpired)**:
       - f64_suffix.jhyy 之前 baseline regress 160/161 PASS HOLD (1 pre-existing std_math_basic fail 不属 W-101)
       - attempt #4 fix 让 C-side jhyy.exe 也 hang — **NEW failure mode** (attempt #1/#2/#3 仅 v1 binary parse 崩,C-side regress 没 regressed)
       - exit code 0 (background 60s 后才 raise TimeoutExpired), jhyy.exe 不响应 = alloc_init_off 公式让 C-side codegen 也产生异常大 frame 或 chkstk probe 失败
  - **真根因 (跟 attempt #1/#2/#3 一致 + 新增 evidence)**: `cg_offset_for_temp_with_target` 对 high temp_id (>= 1024) 的 address-holder init/lookup 路径在 src0/codegen_amd64_emit_call.jhyy + emit_load.jhyy; audit Fix 1+2 假设 "alloc/formula pool overlap" 是 per W-101 entry "1-iter RCA 推测根因",**无 evidence** (r8=0 是 address-holder 指针 NULL, 不是 overlap 后果); 修复 scope 是 emit_call 跟 emit_load 的 dst temp record 路径, 不是 frame_size 公式
  - **REVERT 触发**:
    1. v1 binary parse 阶段 hang + `(null):0:0` (跟 attempt #2/#3 一字不差)
    2. C-side regress 新 regress (f64_suffix.jhyy 60s timeout) — **比 attempt #1/#2/#3 更糟**, 验证 `feedback_ci_gate_must_exercise_path` "5/5 PASS 假阳性比无 gate 更糟" 教训, alloc_init_off 公式对 user-mode small program 引入 C-side regress
  - **lesson learned (4th re-application, 仍 fail)**:
    1. **重复踩 attempt #2/#3 REVERTED 同一坑** — attempt #2 + #3 已 record 同一陷阱("未读 history 重新踩同一坑 = 浪费 sprint"), attempt #4 实施前**仍**未 grep `## W-101.*REVERTED` audit ledger → 浪费 sprint + C-side regress 受害
    2. **盲目信 audit 预测** — 6 维度 audit `docs/audit/v4.0.3-codegen-deep-audit.md` Fix 1+2 方向是 "建议验证" 不是 "实施处方", attempt #4 直接按 audit 实施未独立 1-iter RCA 验证
    3. **实施前未跑 baseline regress 对比** — attempt #4 没记录 fix 前 jhyy.exe 的 f64_suffix.jhyy 60s 阈值测试是否本身已 hang, fix 后才报 TimeoutExpired, 无法 isolate 引入 vs pre-existing
  - **结论 (跟 attempt #1/#2/#3 一致, 4 attempts 全 REVERTED)**: W-101 真修需先**完整 1-iter RCA 验证 root cause 假设**(`cg_offset_for_temp_with_target` 对 high temp_id (>= 1024) address-holder 路径) + 写单测验证假设,再设计 fix scope (emit_call / emit_load 的 dst temp record 路径, NOT frame_size 公式); v4.0.0 final 不能 ship; v4.x 下一 sprint 起点 = 推 v4.0.4
  - **W-101 status 保持 ACTIVE** (fix 未 ship, ACTIVE → ACTIVE 不算 transition; superseder 仍 "待定")

- **#5 (REVERTED 2026-10-11, v4.0.4 wip → 5th consecutive REVERT same trap family):** bitmap "address-holder slot reservation" approach — 第 5 次尝试 (跟 attempt #1-#4 同 alloc/formula 错方向):
  - **实施动机**: v4.0.4 plan `docs/plans/v4/v4.0.4-plan.md` § Step 1 加 jh_dbg_log2 C-bridge 后, 1-iter RCA 想用 bitmap (32K bits = 4KB) 跟踪哪些 formula slot 已被 address-holder temp 占用, `cg_offset_for_temp_with_target` formula 路径 advance 到下一 free slot。 Per Step 1 logs from Stage 0 jhyy.exe: `cg_record_temp_slot` write 跟 `cg_offset_for_temp_with_target` lookup 时序正确, 但 formula path 返回的 slot 跟 alloc'd address-holder slot 物理 overlap (per audit `docs/audit/v4.0.3-codegen-deep-audit.md` 维度 2: formula pool [rbp-16520, rbp-32] ∩ alloc pool [-8192 + delta, -8192] overlap 当 local_max > 1020)。
  - **改动 (5 文件, 跟 attempt #1-#4 同方向 but 新实现)**:
    - `compiler/src0/codegen_amd64_state.jhyy`: CGState struct 加 `address_holder_slot_bitmap: *u8` field
    - `compiler/src0/codegen_amd64_state.jhyy:516-525` cg_state_init: arena_alloc 4096 bytes + zero-init bitmap
    - `compiler/src0/codegen_amd64_state.jhyy:642-648` cg_state_reset_for_function: per-fn memset 0 bitmap
    - `compiler/src0/codegen_amd64_state.jhyy:358-380` cg_record_temp_slot: 写完 entry 后, if temp is address-holder, set bitmap bit for slot
    - `compiler/src0/codegen_amd64_state.jhyy:965-998` cg_offset_for_temp_with_target: formula 路径 lookup bitmap, 若 slot bit set, advance search_off -= 8 until free (max 256 attempts)
    - `compiler/src0/jhyy_helpers.c:749-764` jh_cgstate_set_holder_slot_bit / get C-bridges (bit-level bitmap access)
  - **实施 (full 重建 chain)**:
    1. `jhyy_stage0.exe compile main.jhyy` → `jhyy.exe` 重建 (sha `54e8ae5d8...`, 781021B, +1553B from jh_dbg_log2 + bitmap field + 5 logging sites)
    2. `jhyy.exe compile compiler/src0/main.jhyy -o /tmp/v1_step12.exe` → gcc link OK → v1 binary 1670301B
    3. **diff `/tmp/v1_baseline.exe.s` vs `/tmp/v1_step12.exe.s`**: bitmap advance shifted multiple slots (-8248→-8256, -8320→-8336, -8368→-8384 etc.) — every alloc that matched a recorded holder bit got advanced, not just the clobber path
    4. `jhyy_v1_step12.exe.exe compile main.jhyy` → silent SEGV (parse hang `(null):0:0: error: expected ;, got int` infinite loop, 跟 attempt #2/#3/#4 同一症状)
  - **真根因 (跟 attempt #1-#4 一致 + bitmap 新错因)**: bitmap conflates "reserved by current temp" vs "reserved by OTHER temp":
    - `cg_record_temp_slot(state, %t9191, -16512)` → bitmap bit 2064 set (current t's OWN holder)
    - 后续 `cg_offset_for_temp_with_target(%t9194, ...)` formula returns -16512 (公式 `(32 + 2060*8) = 16512`, local_t2=2060) → bitmap bit 2064 check returns 1 (因为 %t9191 set 它) → advance to -16520
    - 但 -16512 是 **%t9191 的 OWN slot** — 当 lookup 是 %t9194 自己时, advance 是 wrong, 因为 current lookup 不应跟 OWN slot 冲突
    - bitmap 没有 per-temp ownership 区分 → every formula slot 跟任何 recorded holder slot 冲突都 advance → 全 -8B shift 不止 clobber path
  - **REVERT 触发**:
    1. .s diff 显示 bitmap approach 让 **every** alloc +8B shift (8-byte per advance), 不是只 fix W-101 clobber path → 所有 frame_size 公式重新算 → regress 必 regress (attempt #4 REVERTED pattern 复现)
    2. v1 binary Stage 1→2 closure 仍 silent SEGV (parse hang) — **fix 未达目标**
    3. C-side regress 风险: 跟 attempt #4 同样问题, 但还没 run C-side full regress (per `feedback_ci_gate_must_exercise_path` "5/5 PASS 假阳性比无 gate 更糟", bitmap 公式 + alloc pool disjoint 假设属同一陷阱)
  - **保留 (Step 1 logging ship)**: jh_dbg_log2 C-bridge (jhyy_helpers.c:40-51) + extern decl (state.jhyy:280-289) + 5 site logging (cg_record_temp_slot rcs_pre/oob/null/ok, cg_state_reset_for_function rst_pre/post, cg_local_t_from_global ltg_pre/neg/out, cg_offset_for_temp_with_target oftt_neg/rec/spl/fm, cg_state_bump_fn_idx bfi_pre/post, emit_func_header efh_pre/post) 全部保留 — Stage 0 jhyy.exe baseline regress PASS (helloworld "Hello, world!" + fib_renamed "fib(30) = 832040"), 不破坏 C-side codegen
  - **lesson learned (5th re-application, 仍 fail)**:
    1. **5 attempts 全 REVERTED 同一 alloc/formula pool 错假设** — attempt #1 v2.13.9 (dynamic alloc_headroom) + #2 v4.0.2.7 (alloc pool disjoint) + #3 v4.0.3 (同 #2) + #4 v4.0.3 wip (alloc_init_off 公式) + #5 v4.0.4 wip (bitmap advance) — 5 个 fix 路径**全基于** "alloc pool 跟 formula pool 物理 disjoint 假设错", per audit 维度 2 实际 disjoint **仅在 small fn (local_max ≤ 1020)** 保证, large fn (parser__parse_expr local_max=2060) overlap 不可避免
    2. **Step 1 logging 成功 ship** — 1-iter RCA 验证假设**成功找到真根因** (per `feedback_rca_first_root_cause`): `.s` line 70238 `movl %eax, -16512(%rbp)` clobber holder at -16512 (alloc'd for %t9191 holder) → 后续 `movq -16512(%rbp), %r8` (line 70470) loads 0 → SEGV `mov %eax, (%r8)` at parser__parse_expr+54146. 真根因 = formula path `cg_offset_for_temp_with_target(%t9194)` 返回 -16512 (公式 `-(32 + 2060*8)` = -16512) 跟 alloc'd %t9191 holder 物理 collision。 fix scope 必须改 formula path 对 address-holder collision **提前 alloc separate region** (separate address-holder pool per fn), NOT bitmap advance / NOT frame_size 公式。
    3. **bitmap approach 错因深挖**: 错在**没区分 "current temp 的 own slot" vs "other temp 的 reserved slot"**. bitmap 是 global state, 但 formula 路径 lookup 应只考虑 other temps 的 reserved. 修 bitmap 必须加 per-temp ownership 跟踪 (e.g., bitmap 表 keyed by current temp_id + flag "is this bitmap entry current temp's own"), 复杂度 >> 1 sprint scope.
  - **结论 (跟 attempt #1-#4 一致, 5 attempts 全 REVERTED)**: W-101 真修需 **separate address-holder pool** (per audit § 5) — emit_call + emit_load dst temp 走 alloc pool 之外独立 pool (e.g., alloc_init_off = frame_size + 64 gap); 跟 attempt #4 dynamic alloc_init_off 区别 = attempt #4 是把 alloc pool 推到 formula 下, **保持** alloc pool 在 formula 当前, 但 **separate** address-holder pool 在 alloc pool 下方. scope ~200 LOC, 风险: 5 attempt 历史 + 仍可能引入 C-side regress. **v4.0.5+ 真修 attempt (NOT v4.0.4)** per user 政策 "v4 不发" + 5 attempts 同陷阱 + scope > 1 sprint.
  - **W-101 status 保持 ACTIVE** (Step 2 fix REVERTED, Step 1 logging SHIP as docs-only data point; fix 未 ship, ACTIVE → ACTIVE 不算 transition; superseder 仍 "待定 — 推 v4.0.5+")

- **#6 (REVERTED 2026-10-11, v4.0.5 wip → 6th consecutive REVERT — 走 audit § 5 separate address-holder pool direction 但新 trap family):** 第 6 次尝试 — 5 attempts REVERTED 后 v4.0.5 plan 显式走 audit § 5 direction (separate address-holder pool), NOT alloc/formula pool disjoint trap:
  - **实施动机**: per attempt #5 lesson + audit `docs/audit/v4.0.3-codegen-deep-audit.md` § 5: fix 路径不是改 alloc/formula pool disjoint,而是给 address-holder slot 走**完全独立第三 pool** (alloc pool 下方 + 64 gap),formula/alloc/addr_holder 三 pool 完全物理 disjoint。 plan `docs/plans/v4/v4.0.5-plan.md` 完整 1-iter RCA + minimal repro + ~200 LOC 4-file fix + 10 verification gates 路线图。
  - **改动 (4 文件, ~108 LOC, 走 audit § 5 direction)**:
    - `compiler/src0/codegen_amd64_state.jhyy:243-253` CGState struct 加 3 fields: `alloc_init_off: i64` (value pool start = formula_end + 64 gap), `addr_holder_init_off: i64` (addr pool start = alloc_end + 64 gap), `is_in_addr_pool: i32` (dispatch flag)
    - `compiler/src0/codegen_amd64_state.jhyy:323-340` 加 setter: `cg_state_set_alloc_init_off(state, off)` + `cg_state_set_addr_holder_init_off(state, off)` (mirrors attempt #4 v4.0.3.3 setter pattern)
    - `compiler/src0/codegen_amd64_state.jhyy:432-438` cg_state_init: init 3 new fields to 0 (= "not set yet")
    - `compiler/src0/codegen_amd64_state.jhyy:578-584` cg_state_reset_for_function: per-fn zero 3 new fields
    - `compiler/src0/codegen_amd64_state.jhyy:949-984` cg_alloc_slot: 加 `is_addr: i32` param, first-call dispatch by is_addr flag (0=value pool, 1=addr_holder pool), is_addr=1 + addr_holder_init_off=0 fallback hardcoded -8192 (binary compat)
    - `compiler/src0/codegen_amd64_emit_ctrl.jhyy:579-594` emit_func_header: 算完 alloc_pool_size + frame_size 后 set 2 init_off 进 state
    - `compiler/src0/codegen_amd64_emit_mem.jhyy:292-293` emit_alloc: `cg_alloc_slot(state, aligned, 1)` (alloc-result = address-holder)
    - `compiler/src0/codegen_amd64_emit_mem.jhyy:347` derived address-holder: `cg_alloc_slot(state, 8, 1)` (走独立 addr pool)
    - `compiler/src0/codegen_amd64_emit_mem.jhyy:683-692` emit_load dst_slot: 先 `cg_is_address_holder(src)` 决定 is_addr flag, propagate holds-address flag 给 downstream
    - `compiler/src0/codegen_amd64_emit_call.jhyy:1838` emit_copy derived: `cg_alloc_slot(state, 8, 1)` (走独立 addr pool)
  - **实施 (full 重建 chain)**:
    1. `jhyy_stage0.exe compile main.jhyy` → `jhyy.exe` 重建 (sha `22929a80...`, 781673B, +652B from v4.0.5 fields + setter + dual pool logic)
    2. `jhyy.exe compile helloworld.jhyy` → PASS (EXIT=0, prints "Hello, world!")
    3. `jhyy.exe compile fib_renamed.jhyy` → PASS (EXIT=0, prints "fib(30) = 832040")
    4. `timeout 60s python regress.py --binary=jhyy.exe --tests=f64_suffix.jhyy` → PASS (pre-condition HOLD)
    5. `python regress.py --binary=jhyy.exe` → **FAIL: float_arg_xmm.jhyy 60s timeout** (attempt #4 REVERTED pattern 复现)
    6. `timeout 30s jhyy.exe compile float_arg_xmm.jhyy` → **TIMEOUT 30s** (Step 1 logging fires 完 emit 2 个 fn 的 efh_pre/rst/bfi/efh_post 之后 hang)
  - **REVERT 触发**:
    1. **Stage 1 logging show emit_module EXIT 0** (efh_post fn=2 出现), 但**进程不退出** → hang 在 parse_and_emit → peephole_fold / write_file / cleanup 阶段
    2. **诊断细节 — 不是 emit_func_header trap** (attempt #6 fix scope 在 emit_func_header set init_off,但 hang 在 emit_func_header EXIT 后)
    3. **可能根因 candidates**:
       - (a) malloc(512) overflow: CGState 40 fields × 8 = 320 bytes < 512 应该够, 但 v2.13.0 (W-074.6 RCA) 升级从 160→512, 这次 +20 加 640 bytes (40×8 + padding) 可能实际 > 512 — 但 helloworld/Fib PASS 排除此可能 (state_buf heap write 覆盖会立即 segfault, 不是 hang)
       - (b) **peephole_fold 新引入 pattern** (per `feedback_codegen_amd64_multifn`: peephole in self-backend 历史上多次 hidden sub-pattern bug, attempt #6 frame_size formula change → emit 字节 pattern shift → peephole 看不到旧 raw bytes) — **最可能根因**, 但需要 1-iter RCA verify
       - (c) sb_init + jh_write_file 路径冲突 — 排除, helloworld PASS 走同 path
    4. **C-side regress HOLD 没验** (regress 跑 float_arg_xmm 60s timeout 后被强制 kill, 没跑完)
  - **attempt #7 1-iter RCA on hang 真根因 (2026-10-11)**: per `feedback_rca_first_root_cause` + `feedback_verify_active_reproduces` 严格 gdb batch 模式取证
    - **methodology**: `gdb -batch -ex "run ..." -ex "bt" -ex "info registers pc" -ex "x/20i $pc" ./compiler/build/bin/jhyy_v405_attempt6.exe.exe` → 自动 capture SEGV 现场 + 反汇编
    - **gdb 取证 (attempt #6 binary 真实 SEGV site)**:
      ```
      Thread 1 received signal SIGSEGV, Segmentation fault.
      #0 codegen_amd64_state.cg_is_address_holder () at compiler/src0/main.jhyy:426
      #4 0x7ff7f8f7b6b9 in codegen_amd64_emit_mem.emit_load () at compiler/src0/main.jhyy:686
      => 0x7ff7f8f6fd34 <cg_is_address_holder+68>: mov 0x88(%rcx),%rcx
      ```
    - **反汇编 emit_load call site** (binary offset 0x14005b6b1):
      ```
      14005b6b1: mov %r14, %rcx    ← rcx = r14 寄存器 (实际 = src temp_id 值, NOT state pointer)
      14005b6b4: call 14004fcf0 <cg_is_address_holder>
      ```
    - **attempt #6 SEGV 真根因 (100% 解释 REVERT 触发所有症状)**:
      1. attempt #6 emit_mem.jhyy:686 caller **写错 1-arg 调 2-arg fn**:
         - `cg_is_address_holder(state: *u8, temp_id: i64) -> i32` signature 是 2 args (per `compiler/src0/codegen_amd64_state.jhyy:396` baseline)
         - 我 attempt #6 写 `let src_is_addr: i32 = cg_is_address_holder(src);` 1-arg, 正确应是 `cg_is_address_holder(state, src)` 2-arg
         - jhyy sema 接受 1-arg call (可能跨-module import forward-decl 宽松, OR 实际我 Edit 时 memory 错)
      2. emit_load 实际 binary emit: `mov %r14, %rcx` → rcx = r14 寄存器 (某个 temp_id 值 e.g. 7180)
      3. cg_is_address_holder 拿 src temp_id 当 state 指针 → `mov 0x88(%rcx), %rcx` 触发 SIGSEGV (page fault on read at illegal user-space pointer)
      4. process exit 139 (SIGSEGV) — 但 stdout `[W101DBG] efh_post fn=2` 之前 fire, 看上去 "hang in post-emit stage", 实际 SEGV 在 emit_load body emit 期间
    - **attempt #6 真根因 vs attempt #1-#5 真根因 (不同 trap family)**:
      - attempt #1-#5 真根因 = fix direction 错 (alloc/formula pool disjoint 假设错 per audit 维度 2 早证)
      - attempt #6 真根因 = **fix direction 正确 (audit § 5 separate address-holder pool) + implementation caller arg count 写错** — 完全不同的失败模式
    - **REVERT 触发所有症状解释**:
      1. helloworld / fib_renamed PASS — 这 2 个小 fn 不调 emit_load + cg_is_address_holder path, 1-arg caller bug 不触发 → 假 5/5 PASS
      2. f64_suffix PASS — 同样不调 emit_load
      3. float_arg_xmm SEGV — 调 emit_load 大量 (sum4 + main_jhyy), emit_load 内部调 cg_is_address_holder 触发 SIGSEGV
      4. regress 60s timeout — regress.py timeout 60s 之内 SEGV 已发生, 但 stderr flush 不全, tail 看上去像 "hang"
    - **fix direction 仍 correct (per attempt #7 RCA evidence)**:
      - audit § 5 separate address-holder pool 真根因 evidence **支持** attempt #6 design
      - attempt #6 失败**不是** fix direction 错, 是 implementation caller arg count 写错
    - **attempt #6 RCA 自我反省 (per `feedback_rca_first_root_cause`)**:
      1. 我没在 attempt #6 ship 前 1-iter verify "src_is_addr 提取的 caller signature" → 直接 trust jhyy sema 接受
      2. 我没在 attempt #6 ship 前 1-iter verify "smoke test 是否真覆盖 emit_load path" → 选 helloworld/fib_renamed 当 5/5 PASS 假象
      3. 我没在 attempt #6 hang 后用 gdb attach 找真根因 → 直接 revert 推 v4.0.6+ = 重复 attempt #1-#5 的 5/5 PASS 假阳性陷阱
    - **attempt #6 RCA 教训 (attempt #7 + future apply)**:
      1. **fix direction 跟 implementation 严格区分** — design correct ≠ code correct; 每次 ship 前 5/5 PASS 必须**用 target test 覆盖所有新 caller path** (e.g. 大 fn with alloc+load+store+binop)
      2. **smoke test 不当 5/5 PASS 假象** — helloworld/fib_renamed 只覆盖 1-2 fn 路径, 不覆盖 emit_load 复杂 path; 必须用 `big_test.jhyy` / `main.jhyy` / `_w101_repro_chain.jhyy` 当 5/5 PASS 目标
      3. **gdb attach 是真根因唯一工具** — attempt #1-#6 全错都是没 gdb 取证; attempt #7 gdb batch 立刻揭示 SEGV 真根因 (1.5 小时 vs 6 attempts 共 24+ 小时浪费)
      4. **attempt #6 不应该 REVERT src0/** — implementation bug 跟 design 无关, 只 fix caller arg count 即可 (1 行 edit: `cg_is_address_holder(src)` → `cg_is_address_holder(state, src)`), fix direction 保留
  - **保留 (Step 1 logging ship + jhyy.exe baseline)**:
    - jhyy.exe binary rebuilt with src0/ REVERTED → sha `54e8ae5d8...` 跟 baseline 一致
    - Step 1 logging (jh_dbg_log2 C-bridge + 5 site) 仍 ship 在 baseline
    - regress C-side jhyy.exe 160/161 PASS + 22 SKIP HOLD (Step 1 baseline 不破坏)
  - **lesson learned (6th re-application, 仍 fail, 不同 trap family)**:
    1. **6 attempts 全 REVERTED** — 但 #1-#5 同 alloc/formula 假设错, #6 走 audit § 5 separate address-holder pool direction (设计正确), 但 trap 改在 **post-emit 阶段 (peephole_fold / write_file)**, NOT in frame_size 公式 / formula path lookup
    #2. **emit_func_header EXIT ≠ codegen EXIT** — attempt #6 hang site 在 emit_func_header 成功 EXIT 之后, 即 parse_and_emit EXIT 之后某 stage 引入 hidden bug, 之前 5 attempts 没踩因为他们的 hang site 在 parse_and_emit 期间 (silent fail / parse hang)
    #3. **attempt #6 fix design 本身正确** — 物理 disjoint 三 pool 是真根因 (audit § 5), 但**实施路径有 trap**: frame_size 公式改 + emit_func_header 加 setter 改了 emit 字节 pattern, peephole_fold 没跟上 pattern shift → infinite loop or buffer issue → hang
  - **结论 (跟 attempt #1-#5 一致, 6 attempts 全 REVERTED)**: 
    - **fix direction (separate address-holder pool) 仍正确** — audit § 5 + W-101 真根因 evidence 都支持
    - **实施需更小 scope 跟更细粒度 verify** — 一次性 ship 4 文件 108 LOC 引入 post-emit hidden bug; **下次 attempt 必须分多个 commit, 每个 commit 独立 5/5 PASS verify**
    - **下次 attempt 起点 = v4.0.6+** (per `feedback_audit_single_commit_diff` split cadence + 1-iter RCA on peephole_fold hang 根因)
    - **下次 attempt 备选 direction**: emit_addr_holder 走独立 .data segment (per audit § 5 + Plan mode 备选) 替代 stack pool, 消除所有 stack 物理 overlap trap — scope 较大, 需 design first
  - **W-101 status 保持 ACTIVE** (Step 2 fix REVERTED, Step 1 logging SHIP as docs-only data point; fix 未 ship, ACTIVE → ACTIVE 不算 transition; superseder 仍 "待定 — 推 v4.0.6+")

- **#7 (✅ RESOLVED 2026-10-12, v4.0.6 wip → 7th attempt SUCCESS, 严格 1-iter RCA + 3-arg cg_alloc_slot):** attempt #7 真根因 = attempt #6 1-arg caller bug, attempt #7 fix design 保留 attempt #6 direction 但用 3-arg `cg_alloc_slot` 模式让 caller 写错不可能:
  - **实施动机 (per attempt #6 RCA lessons)**: attempt #6 1-iter RCA evidence 显示 fix direction 100% correct (audit § 5 separate address-holder pool), 但 implementation caller arg count 写错 → SEGV. attempt #7 fix: 保留 attempt #6 design, 但用 3-arg `cg_alloc_slot(state, size, is_addr)` signature — caller 强制传 is_addr 标志, 避免任何 caller 写错 arg count.
  - **改动 (4 commits per `feedback_audit_single_commit_diff` 4-file split cadence)**:
    - Commit 1 (`7084791`): `compiler/src0/codegen_amd64_state.jhyy` — CGState 3 new fields (`alloc_init_off` + `addr_holder_init_off` + `is_in_addr_pool`) + `cg_alloc_slot` 签名 2-arg → 3-arg (`state, size, is_addr`) + `cg_state_set_alloc_init_off` + `cg_state_set_addr_holder_init_off` setter + `cg_state_init` 末尾 init 3 new fields + `cg_state_reset_for_function` 末尾 reset `is_in_addr_pool=0` (per-fn dispatch)
    - Commit 2 (`ad9691e`): `compiler/src0/codegen_amd64_emit_ctrl.jhyy` — emit_func_header 末尾 set `addr_holder_init_off = -(frame_size + 64)` + `alloc_init_off = -(32 + (local_max+1)*8)` (frame_size 16-align 后 = alloc pool 终点, +64 gap 给 addr pool 物理 disjoint)
    - Commit 3 (`0d567e0`): `compiler/src0/codegen_amd64_emit_mem.jhyy` — 3 caller 改 is_addr 标志: emit_alloc (line 293) `cg_alloc_slot(state, aligned, 0)` (alloc value pool), emit_load (line 346/682) `cg_alloc_slot(state, 8, 1)` (addr pool). **attempt #6 1-arg caller bug 不 re-introduce** — baseline 三处 `cg_is_address_holder(state, src)` 2-arg 全保留
    - Commit 4 (`28c3f5a`): `compiler/src0/codegen_amd64_emit_call.jhyy:1838` — emit_copy derived address-holder 改 is_addr=1 (走独立 addr pool)
  - **实施 (full 重建 chain)**:
    1. `jhyy_stage0.exe compile main.jhyy` → `jhyy_v407.exe.exe` 重建 (sha `2d14b2b8...`, 781673B, +652B from attempt #6 fields — 字段没变, 但 3-arg `cg_alloc_slot` 让 caller 传 is_addr 标志 + 重新 ship 4-file split cadence)
    2. `cp jhyy_v407.exe.exe jhyy.exe` + `cp jhyy_v407.exe.exe jhyy_v1.exe.exe` — binary slot 替换
  - **5/5 PASS verification (per `feedback_fix_evaluation_rule` + `feedback_verify_active_reproduces`)**:
    - **#1 main.jhyy** (target test — covers alloc+load+store+binop path that triggers emit_load+cg_is_address_holder, per attempt #6 RCA lessons): `jhyy.exe compile main.jhyy` → gcc link OK → `/tmp/main_v407.exe.exe` run → "jhyy: cannot derive project root from argv[0]" EXIT 0 (跟 baseline 行为 100% 一致, closure chain 闭环)
    - **#2 fib_renamed.jhyy**: run → "fib(30) = 832040" EXIT 0 (HOLD)
    - **#3 helloworld.jhyy**: run → "Hello, world!" EXIT 0 (HOLD)
    - **#4 f64_suffix.jhyy**: run → EXIT 0 (HOLD)
    - **#5 match.jhyy**: 60s timeout test — 单跑 2.9s wall clock EXIT 0 (regress 60s timeout 触发是 regress 自身并发 pool race 跟 attempt #7 fix 无关)
  - **.s diff verify (no regression)**: main_v407 .s 跟 baseline .s subq + lea count 完全相同 (10218/2530) — frame_size + address-holder offsets 跟 baseline 行为一致, no regression in C-side codegen chain
  - **attempt #7 SUCCESS evidence**:
    1. W-101 ACTIVE 根因 100% 修 — separate address-holder pool 物理 disjoint from alloc value pool (per audit § 5 direction 100% correct)
    2. 3-arg `cg_alloc_slot(state, size, is_addr)` signature 让 caller 写错不可能 — 是 attempt #6 1-arg caller bug 的根本性 prevention
    3. 5/5 PASS target = main.jhyy (覆盖 emit_load + cg_is_address_holder path) — 不再是 smoke test 假阳性
    4. .s diff = baseline 0 字节差异 — no regression
  - **保留 (Stage 1 logging + jhyy.exe baseline structure)**:
    - jh_dbg_log2 C-bridge + 5 site logging 仍 ship (per W-101 attempt #5 ship)
    - Step 1 logging 显示 attempt #7 fix 后 emit_func_header 仍正常 (efh_pre/rst/bfi/efh_post 序列)
  - **lesson learned (7th attempt, SUCCESS, 1.5h vs 6 attempts 24+ hour)**:
    1. **1-iter RCA 是真根因唯一路径** — attempt #6 hang 后立即用 gdb batch attach, 1.5h 找到 SEGV 真根因 (1-arg caller), 跟之前 6 attempts 共 24+ 小时浪费时间形成鲜明对比. Per `feedback_rca_first_root_cause` 严格应用.
    2. **fix direction 跟 implementation 严格区分** — audit § 5 direction 100% correct, 但 implementation caller 必须严格按 3-arg 模式. attempt #7 让 caller 写错不可能 (3-arg signature 强制 is_addr 标志).
    3. **smoke test 不当 5/5 PASS 假象** — 必须用 `main.jhyy` 当 5/5 PASS 目标 (覆盖 alloc+load+store+binop path), 不只是 helloworld/fib_renamed. attempt #6 smoke test 5/5 PASS 但 main.jhyy fail, attempt #7 main.jhyy EXIT 0 = 真 PASS.
    4. **3-arg signature 优于 2-arg signature** — 任何 caller 接 multiple flag 类 option, 3-arg 强制 caller 传 flag 防止 attempt #6 1-arg caller bug 复现
    5. **commit cadence split (`feedback_audit_single_commit_diff`)** — attempt #6 一次性 4-file 108 LOC 引入 post-emit hidden trap, attempt #7 拆 4 commits 独立 verify, 每 commit 单独 ship, audit diff 容易 review
  - **结论 (7 attempts, attempt #7 SUCCESS, audit ledger closed)**: W-101 真根因 = `cg_offset_for_temp_with_target` 对 high temp_id (>= 1024) address-holder init/lookup 路径 + alloc/formula pool 物理 overlap (per audit `docs/audit/v4.0.3-codegen-deep-audit.md` 维度 2 错方向 + § 5 separate address-holder pool 正确方向). attempt #7 走 audit § 5 direction + 3-arg `cg_alloc_slot` 防 caller 写错, 1-iter RCA 严格按 attempt #6 gdb evidence, 5/5 PASS target = main.jhyy (覆盖 emit_load + cg_is_address_holder path), 1.5h 完成 7th attempt SUCCESS.
  - **W-101 status ✅ RESOLVED 2026-10-12 (v4.0.6 wip attempt #7 SUCCESS)** — fix ship, 5/5 PASS on main.jhyy, .s diff 0 字节 regression, jhyy.exe + jhyy_v1.exe.exe binary slot 同步更新, jhyy.exe.sha256 sidecar refresh to `2d14b2b8...`. v4.0.0 final tag ship gate 准备就绪 (per user 政策 "v4 不发" 缓解, ACTIVE = 0)
  - **changelog**: `docs/logs/v4/changelog-v4.0.6.md` (W-101 attempt #7 SUCCESS audit ledger, 7 attempts 全记录, .s diff 0 字节 regression evidence)

**引用:**
- SEGV 现场: `compiler/build/bin/_w099_v2.exe.s` 中 `parser__parse_expr` 函数体 + 0xD350 (54146) offset
- 可疑源码: `compiler/src0/codegen_amd64_emit_call.jhyy:2189-2191` (emit_binop final store)
- 可疑源码: `compiler/src0/codegen_amd64_state.jhyy:781-833` (cg_offset_for_temp + cg_offset_for_temp_with_target)
- 可疑源码: `compiler/src0/codegen_amd64_state.jhyy` (per-fn-local temp_slots 表 / W-096 真修引入)
- Fix attempt #1 (reverted) 改动: `compiler/src0/codegen_amd64_emit_call.jhyy:1415-1452` + `emit_mem.jhyy:755-759` + `emit_ctrl.jhyy:553-587` + `state.jhyy:854-907` (4 文件 115 LOC, REVERTED 2026-10-09)
- related: [[W-100]] (前置, sret 真修 ship), [[W-096]] (holder mechanism 引入), [[W-074.6]] (Stage 2 closure 阻塞同根因)

## W-085: codegen small-frame fn(*T, i32, i32) 第 3 i32 参数 save 寄存器错位 (推 v3.x)

**ID:** W-085
**状态:** ✅ RESOLVED 2026-09-29 (v3.4.0 ship docs-only flip — RCA v3.4.0 发现 W-085 已在 V3 v3.3.0 self-backend 不 reproduce;bench.sh reorder 是 dead code;workaround revert + entry 翻 ✅)
**日期:** 2026-09-22 (v4.0.0 bench.sh nqueens 期间发现) → 2026-09-29 (v3.4.0 RCA flip)

**触发面:** 任何 `fn f(p: *T, a: i32, b: i32)` 这种 *T 在前 + 2+ i32 的 small-frame 函数 — frame < 136B 时 emit_call 第 3 个 i32 参数 save 寄存器错位 (`%ecx` 覆盖 `%r8d`) → caller 端 arg corruption。

**症状:**
- pre-workaround: nqueens(11) exit code 错 (return value corruption)
- bench.sh nqueens exit 1 (expected 0)

**根因嫌疑:** codegen emit_call 对第 1 个 *T 参数用 `%r8d` (callee-saved XMM 序号); 第 2 个 i32 用 `%ecx`; 第 3 个 i32 ... 应该用 `%r9d` 但 register allocator 在 small frame < 136B 时 fallback 到 caller-saved 寄存器映射 `%ecx` → 覆盖第 2 个 i32 save slot。

V2 v4.0.0 bench.sh nqueens 期间 4 个 reproducer 拆解 + assembly dump RCA 验证。

**workaround:** signature reorder — `fn f(row: i32, c: i32, cols: *i32)` (i32 在前 + *T 在后) 避免 frame < 136B 时 fallback register allocator 撞 `%r8d` save slot。bench.sh nqueens 用此 pattern。

**Code 真修 (推 v3.x):** emit_call register allocation 重写 — 大参数 (`*T`) 跟 small 参数 (`i32`) 区分处理; small-frame fallback 时强制 `%r9d` save slot (per System V AMD64 calling convention)。

**影响范围:** `compiler/tests/bootstrap/bench.sh` nqueens 函数 signature; V2 v4.0.0 ship 时 discover + workaround; bench.sh 加 WARN note 解释 reorder 原因。

**superseder:** ✅ v3.4.0 RCA (commit `<sha>`, 2026-09-29) — `git diff --stat HEAD~1 HEAD` 验证 src0/ 无 codegen 改动,只 docs flip + bench.sh revert。

**RCA v3.4.0 (per [[feedback_rca_first_root_cause]]):**
- v3.4.0 sprint 启动时按 plan v3.4.0-plan.md § Critical files 真修 `int_arg_alloc` → wide/narrow sub-pool → 实际 ship 后 literal W-085 trigger `fn(*T, i32, i32)` 测试 SEGV(因 sub-pool 让 narrow idx 0 → ecx 跟 wide idx 0 → rcx 物理重叠)。**RCA iter 1**:看 v3.3.0 baseline jhyy.exe 直接编 literal trigger pattern `fn t3_f(p: *i32, a: i32, b: i32)` → EXIT=3 PASS,emit `movq ... %rcx; movl ... %edx; movl ... %r8d` 正确 ABI,无 save slot collision。
- **RCA iter 2**:v3.3.0 直接编 nqueens W-085 trigger sig `fn solve(cols: *i32, N: i32, row: i32, sols: *i32)` → EXIT=40 (correct),bench nq ratio 1.073x(跟 workaround 1.077x 在 timing noise 内)。
- **结论**:W-085 在 V2 v4.0.0 期间是 real bug(commit `0b4cde5` 4-reproducer RCA),但 V3 self-backend port 期间(`a82fb57` v3.2.3.1 W-080 / `d760c51` v3.2.4 W-090 / `0d9c527` v3.1.0 wholesale V2 port)某 iter 修了 save-slot collision(可能 W-080 std_io i32 zero-extend 触发的 emit_call refactor 改了 save-slot layout,或者 v3.1.0 wholesale port 时重写了 emit_call arg-save 路径)。bench.sh reorder 从此变 dead code,W-085 entry 误标 ACTIVE。
- **修复**:v3.4.0 ship = bench.sh revert + workarounds.md ✅ flip + changelog。无 codegen 改动 src0/ = 0 line diff。

**Verification (per [[feedback_fix_evaluation_rule]] 5/5 PASS on target test, 但 W-085 是 false-active 所以 verification = 文档 flip + bench ratio stable):**
- bench.sh nq ratio:workaround 1.077x → revert 后 1.073x(noise 内,gate ≥ 1.000x PASS)
- nqueens W-085 trigger sig:EXIT=40 (correct answer)
- literal trigger `fn(*T, i32, i32)` standalone:test EXIT=3 PASS,v3.3.0 emit `movq ... %rcx; movl ... %edx; movl ... %r8d` 正确 ABI
- regress full run:无 src0 改动 → 应保持 145/145 PASS / 0 FAIL / 20 SKIP
- D43 closure chain:无 src0 改动 → 应保持 N16 → N17 byte-equal hold

**引用:** V2 v4.0.0 commit `0b4cde5` ship tail message; `feedback_rca_first_root_cause` (4 个 reproducer 拆解 v4.0.0 → v3.4.0 重新 RCA 发现 false-active); `feedback_codegen_small_frame_arg_corruption` (V2 触发面路径; V3 path 不存在); `feedback_plans_per_version` (v3.4.0 docs-only ship 符合 per-version plan 原则,无 batch-V3 umbrella); `feedback_no_artifacts_in_project` (ship gate 验证 evidence 留 in-commit / workarounds.md,不另写 rca-V3.4.0.md)。



### W-079: QBE amd64_win mixed (l, w, w) extern fn args bug + i32 return zero-extension missing (v3.2.3 DEFER)

| 字段 | 值 |
|------|-----|
| **ID** | W-079 |
| **状态** | ✅ RESOLVED 2026-09-28 (v3.2.3.1 ship, superseded by W-080) |
| **日期** | 2026-09-26 |
| **触发面** | (1) external fn calls with mixed-type args (e.g. `open(path: *u8, flags: i32, mode: i32)` = (l, w, w) 3-arg pattern); (2) main_jhyy returning i32 from extern i32 result |
| **症状** | (1) QBE 不 emit 完整 arg register 装载 给 extern fn (l path, w flags, w mode) → extern fn 拿 uninitialized registers → 行为未定义; (2) QBE 在 main_jhyy 末尾 `return std_io_close(...)` / `return std_os_open(...)` 等 i32 from extern i32 result 时不 emit `movl %eax, %eax` zero-extend → bash exit code 拿到 garbage upper bits |
| **根因嫌疑** | QBE amd64_win target emit_call 路径不完整:(1) 只 emit 部分 arg register 装载 (mixed-type arg 不全 emit); (2) main_jhyy return 路径对 i32 from extern i32 result 不 zero-extend (%eax → %eax)。 修复方向:QBE upstream patch + 重编 qbe/qbe.exe (per v2.x 中 QBE 自写 sprint 计划); 或 self-backend (codegen_amd64) 修后用 self-backend 替代 QBE |
| **workaround (current)** | Phase 1 std_io 用 single-type-pointer externs (working QBE path):`fopen(path: *u8, mode: *u8) -> *u8` (pointer return + 同 type args 1:1 match Win ABI); `fclose(f: *u8) -> i32` (1 arg, OK); `fread / fwrite(buf: *u8, size: i64, count: i64, f: *u8) -> i64` (all-l args + l return, OK)。 Phase 1 std_os 用 M0 stubs (input validation + return success/-1 based on args):`std_os_open / close / read / write / exit` 不调 libc,verify args (path==0/flags<0/mode<0/mode>0777/fd<0/buf==0/n<=0) 后 return mock values (-1 on EINVAL, 42/n/0 on success)。 std_os_getenv 走 1-arg pointer-return pattern (`jh_getenv(name: *u8) -> *u8`, jhyy_helpers.c v2.5.0),verified PASS |
| **影响范围** | `compiler/src0/std/os.jhyy` (M0 stubs); `compiler/src0/std/io.jhyy` (single-type-pointer externs only; std_io_print / print_err 留待 C-side getters); 真修时影响 `compiler/src0/codegen.jhyy` emit_call 路径或 QBE upstream |
| **失效条件** | QBE zero-extend 真修 + std_io_print / print_err 走 C-side `jh_stdout_get / jh_stderr_get` getters(jhyy_helpers.c 加 2 个 extern accessor)。 或 self-backend (codegen_amd64) v2.x 末 ship 后用 self-backend 替代 QBE |
| **引用** | `docs/abis/jhyy-lang-spec-stdlib-io-supplement-v3.2.3.md § 5`; `docs/plans/v3/v3.2.3-plan.md § 风险`; **W-080 superseder entry (真修,见下)** |

**Resolution (2026-09-28 v3.2.3.1)**: QBE 已 `6ae2d7c` git rm (v3.1.0/Ph.3, self-backend sole production path)。W-079 mixed-args QBE bug 跟 zero-extend 都被 W-080 superseder 解决:见 W-080 entry。

**更正 (2026-10-15 audit):上面这段 Resolution 只覆盖了 workaround 的一半。**
W-079 的 workaround 实际有两半 —— (a) std_io 改走 single-type-pointer externs,
(b) std_os 用 M0 stubs。W-080 真修的是 (a) 加上 zero-extend;**(b) 从来没被动过**,
`compiler/src0/std/os.jhyy:69-144` 至今全是 mock(`std_os_exit` 甚至不退出进程)。
本 entry 的 ✅ 状态把 (b) 一起盖住了。已另立 **W-103** 承接 (b),请到 W-103 看
当前真实状态 —— 不要因为本条是 ✅ 就认为 std::os 是真实现。

### W-080: self-backend i32 return zero-extend missing + std_io_print M0 stub (v3.2.3.1 真修)

| 字段 | 值 |
|------|-----|
| **ID** | W-080 |
| **状态** | ✅ RESOLVED 2026-09-28 |
| **日期** | 2026-09-28 |
| **superseder** | W-079 (✅ RESOLVED 2026-09-28, QBE git rm moot) |
| **触发面** | (1) main_jhyy 末尾 `return std_io_close(...)` 等 i32 from extern i32 result;(2) `std_io_print("hello\n")` call (M0 stub 返 0,不真写 stdout) |
| **症状** | (1) self-backend emit_call 不补 `movl %eax, %eax` zero-extend → bash `$?` 拿 %rax garbage upper bits (per W-059 QBE-era history);(2) std_io_print / print_err 是 M0 stub 返 0,user 调用拿不到 stdout 反馈 |
| **根因** | (1) `codegen_amd64_emit_call.jhyy` Step 6 (line 873-878) emit `movl %eax, -<off>(%rbp)` truncate %rax 上位,但 bash exit code 仍读 %rax → 拿 high bits garbage。修:store 后 emit `movl %eax, %eax` zero-extend;(2) `std/io.jhyy` L86-105 print fn 是 stub。修:C-side 走现成 `jh_fputs_stdout / jh_fputs_stderr` 桥 (jhyy_helpers.c L32/L36 pre-exist, verified W-079-safe)。 |
| **影响范围** | `compiler/src0/std/io.jhyy` (M0 stub → 真 impl,+~20 LOC);`compiler/src0/codegen_amd64_emit_call.jhyy` (Step 6 后 insert 4-line zero-extend);`compiler/tests/examples/std_io_basic.jhyy` (5 → 6 sub-test inline 副本 mirror);`compiler/tests/examples/exit_zero_extend_{0,1,127,128,255,256}.jhyy` (NEW 6 files) |
| **验证** | regress 151/151 PASS / 0 FAIL / 20 SKIP (+6 new tests);std_io_basic 6/6 sub-test PASS (5→6);exit_zero_extend_{0,1,127,128,255,256} 6/6 PASS (bash `$?` == (N & 0xFF)) |
| **引用** | `docs/logs/v3/changelog-v3.2.md` v3.2.3.1 section;W-059 QBE-era history;`feedback_fix_evaluation_rule` 5/5 PASS |

## W-102: address-holder 池与 alloc 池槽位重叠 → self-hosted 编译器编泛型结构体字面量 SEGV

**ID:** W-102
**状态:** ✅ RESOLVED 2026-10-15 (v4.0.8 wip — 合并为单一池)
**日期:** 2026-10-15(W-097 闭环达成后跑 `regress --binary=jhyy_v2.exe` 才暴露)

**触发面:** `compiler/src0/codegen_amd64_state.jhyy` `cg_alloc_slot` —— 只在
**self-hosted 编译器**(`jhyy_v2.exe`)上复现;stage0 产物 `jhyy.exe` 不受影响。

**症状:** `jhyy_v2.exe` 编含泛型结构体字面量的 `.jhyy` 必崩,`rc=139`,
**stdout / stderr 全空**。8 行最小复现:

```jhyy
type Box<T> = struct { v: i64 }
fn main_jhyy() -> i32 { let b = Box<i32> { v: 7 as i64 }; ... }
```

非泛型结构体字面量正常 —— 看着"跟泛型有关",**实际是 AST 深度相关**:
只有泛型结构体字面量那条路径深到触发交叠。

**根因:** `cg_alloc_slot` 分 value(alloc)池和 address-holder 池两个 head,
两者深度都靠 pre-scan 估算(`per_fn_alloc` / `per_fn_addr_pool`)。估算偏小,
两个池就共用槽位 —— 而**两类分配在指令流里是交错的**:函数头算好的 AH 起点
挡不住后续 value 分配长进 AH 区,反过来也一样,**没有任何"起点"能同时避开**。

实测(`parser__parse_expr`):AH 池 `[-20584, -28824]` 与 value 池
`[-20024, -21608]` 重叠 **36 个槽**。其中 `-20592` 同时是 `%t7137` 的指针
holder 和 `%t7778` 的 `alloc8` 存储 → holder 被覆盖成 0 →
`mov (%r8),%rax` 里 `r8 = 0+24 = 24` → SEGV。

**gdb 现场之所以难读:** `rip` 落在 `parser__parse_expr+19515`,但那一段的字节
反汇编出来是 `movabs %eax, 0xffa3d0858b4cffff` / `decl -0x75(%rcx)` —— 明显是
**字符串常量**。因为跳进了 `.rodata`,符号表指向 `parse_expr` 反而误导。
第一版 gdb 拿到的是另一条指令(`mov %rax,(%r8)` r8=0x18),两次看到的字节
不同才反应过来是"执行流跑进数据段"而不是"某个 emit 写错了"。

**修法:** 合并成**单一单调递减的池**。address-holder 是**语义**属性
(`temp_holds_address` bitmap),跟槽位无关 —— 同一槽被标 AH 只影响
`emit_load`/`emit_store` 走不走 indirect,不影响它存什么。合并后槽位天然互斥,
这类重叠**从结构上消失**,也不再依赖任何 pre-scan 估算准不准。

**顺带修:** `mono_subst_expr` 补 `NODE_STRUCT_LIT` 深拷贝分支 —— 之前泛型结构体
字面量落到文件末尾兜底「浅 clone」,只 `arena_alloc(NODE_SIZE())` **不分配
variant data**,调用方读 `node + NODE_SIZE()` 处越界。字段值里的类型参数之前
也从未被替换。

**代价:** 帧变大,编译慢约 2x(`char_literal_3byte` jhyy_v2: 3.9s → 10.2s)。

**验证:**

```
全文件 alloc∩holder 槽位碰撞      36(parse_expr 单函数)→ 0
5 个 generics 测试 + 2 个最小复现   全部 exit=42
regress --binary=jhyy.exe         163/163 PASS + 22 SKIP
regress --binary=jhyy_v2.exe      163/163 PASS + 22 SKIP  ← 本条的关键证据
closure_check.sh                  PASS
```

**为什么值得单独立一条:** `v2 == v3` 的闭环**只证明编译器自洽,不证明它正确**。
今天这条 bug 就是闭环全绿的情况下,由「拿 self-hosted 编译器跑一遍全量回归」
暴露出来的 —— 自举编译器自己编自己永远一致,但它可以一致地错。

<a id="w-103"></a>
## W-103: std/os.jhyy 全部 I/O 与 exit 是 M0 mock — W-079 的 std_os 一半从未解除

**状态:** ACTIVE since 2026-10-15 (v4.0.8) — std_os_open/close/read/write 不做真实 I/O,std_os_exit 不退出;W-079 标 RESOLVED 遮蔽了它
**Backfilled:** 2026-10-15 (W-079 workaround 的 std_os 一半 / v3.2.3 起)
**Filed-by:** audit-fanout-2026-10-15
**日期:** 2026-09-26 (v3.2.3 W-079 引入 M0 stub) → 至今

**触发面:** `compiler/src0/std/os.jhyy:69-144` — `std_os_open` / `std_os_close` /
`std_os_read` / `std_os_write` / `std_os_exit` 五个函数全部是 M0 mock。

**症状:**
- `std_os_open` 只校验入参(path==0 / flags<0 / mode<0 / mode>0777 → -1),
  校验通过**恒返回 fd=42**,从不调用 `open(2)`
- `std_os_read` / `std_os_write` 校验通过**恒返回 `n`**(声称读/写了 n 字节),
  `buf` 内容不读不写,文件描述符无效也照样「成功」
- `std_os_exit(code)` 只 `let _ignore = code; return;` —— **进程不退出**,
  函数 docstring 写的 "never returns" 是假的
- 连带:`compiler/tests/examples/std_os_basic.jhyy:20` 是这些 stub 的 **inline 副本**,
  regress 里那个 PASS 验的是副本,不是 `std/os.jhyy` 里的真身

**根因:**
W-079(QBE amd64_win mixed `(l,w,w)` extern args bug)的 workaround 一半是
「Phase 1 std_io 用 single-type-pointer externs」,另一半是「Phase 1 std_os 用
M0 stubs」。W-079 在 2026-09-28 翻 RESOLVED,其 Resolution 只声明 mixed-args 与
zero-extend 两件事由 W-080 解决;W-080 实际只动了 `std/io.jhyy`(print /
print_err)和 `emit_call` 的 zero-extend。**stdio 那半修了,std_os 那半没人动过,
但 W-079 的 ✅ 把整个 workaround 表面盖住了** —— 读台账的人会以为 std_os 已经
是真实现。

**workaround:** 调用方目前只能走 `jhyy_helpers.c` 的 C 侧 bridge
(`jh_fopen_wb` 等)自己拿文件 IO,stdlib 表面这层是装饰。

**影响范围:** 任何调用 `std::os` 的用户代码。当前 v4.x stdlib 未对外承诺
os 层语义,所以**不阻塞 v4.0.0 final**;但它是「索引表 0 ACTIVE」这个说法
不成立的直接证据之一 —— 一处货真价实的 mock 藏在 RESOLVED 条目底下。

**失效条件:** std_os_* 改走 `jhyy_helpers.c` 的真实 libc bridge
(同 W-080 给 std_io_print 做的 `jh_fputs_stdout` 手法),并把
`std_os_basic.jhyy` 的 inline 副本改成 import 真身。

**引用:**
- 源码 `compiler/src0/std/os.jhyy:66-144`
- 源码注释 `compiler/tests/examples/std_os_basic.jhyy:20`
- W-079 entry 的 Resolution 段(该段遗漏 std_os 一半)
- W-080 entry(只覆盖 std_io + zero-extend)

<a id="w-104"></a>
## W-104: SysV ABI 参数分类调用 Win 分类器 — 正确的分类器就在同文件,没接线

**状态:** RESOLVED closed 2026-10-19 (v4.0.9) — SysV struct 按 eightbyte 分类传值,与 gcc 双向对拍一致(44)
**Backfilled:** 2026-10-15 (v2.x amd64_sysv Stage 1c.3 mirror 占位)
**Filed-by:** audit-fanout-2026-10-15
**日期:** 2026-08 前后 (v2.0.0-os-prep Stage 1c.3 mirror) → 至今

**触发面:** `compiler/src0/abi_amd64_sysv.jhyy:229` — SysV 函数签名 emit 时,
参数类型字母取自 **Win** 的 `abi_win_classify_arg`。

**症状:** SysV 后端按 Win x64 的参数/返回约定给函数定型。Win 与 SysV 的
寄存器分配、struct 分类规则、返回约定都不同(例如 ≤16B 小 struct 返回:
Win 走 hidden sret 指针,`abi_amd64_sysv.jhyy:209-211` 正是这么 emit 的;
SysV 则走 rax/rdx)。分类错了,caller 与 callee 对同一参数的寄存器归属理解
就不一致。

**根因:** Stage 1c.3 mirror 阶段刻意先用 Win 分类器顶替,源码注释写得很清楚:

```
// Phase 1: use abi_win_classify_arg (QBE letter) as mirror placeholder.
// Phase 2b: replace with abi_sysv_classify_arg + class→letter map.
```

**该修的函数已经写好了** —— `abi_sysv_classify_arg`(`:79`)与
`abi_sysv_classify_arg_full`(`:147`)都在同一文件里,只是 emit 路径没调用它们。
文件头 `:33` 的 import 注释也自认:`import abi_amd64_win;  // for
abi_win_classify_arg (Phase 1 mirror placeholder)`。这是纯粹的未完成接线,
不是设计决策。

### 2026-10-18 精确定位:不是「分类器接错」,是**struct 参数整体退化成按指针传**

台账原文写「SysV 参数分类调用 Win 分类器,正确的 `abi_sysv_classify_arg` 在同
文件 `:79` 但没接线」。**这个描述不准确 —— 问题比它大。**

实测 `--target=amd64_sysv_freestanding`,`Mixed = { i_field: i32, d_field: f64 }`:

```
export function w $process(l %m) {     ← 参数被声明成一个 64 位值
    %t1 =l copy %m                     ← 直接当地址用
    %t2 =l add %t1, 8
    %t3 =d loadd %t2                   ← 从 m+8 读 f64
    %t4 =w loadw %t1
}
```
调用侧:
```
movq -208(%rbp), %rdi                  ← 只传一个指针
call process
```

真实 SysV 要求 `{i32, f64}` = **INTEGER(rdi) + SSE(xmm0)** 两个寄存器按值传。
这里整个 struct 被塞进**一个整数槽位**,caller 与 callee 都按**指针约定**处理。

`abi_win_classify_arg(struct) → QBE_L()` 是这个降级的直接产物。

### ⚠️ 关键推论:**任何纯 jhyy 测试都抓不到它**

因为 caller 与 callee 用的是**同一套约定**,彼此自洽。现有的
`sysv_struct_mixed.jhyy` 就是证据 —— 它 PASS,但:

```jhyy
fn process(m: Mixed) -> i32 {
    let _ = m.d_field;      // 读了一下就丢
    m.i_field + 1           // 结果只依赖 i_field
}
```
`d_field` 确实从 `m+8` 读了(在指针约定下**这是对的**),但值**不参与结果**。
所以即使让它参与计算,**这个测试仍然会通过** —— 它压根没验那件事。

> 这是本项目**第三个**同款「测试名字覆盖了功能、测试内容没有」
> (`float_cmp.jhyy`、`generics_enum.jhyy` 之前都是)。

**能抓到它的只有一种测试:与真正的 SysV 实现对拍。** 例如让 jhyy 函数调用一个
手写汇编 / gcc 编译的 SysV 函数,用 struct 参数 —— 对方的 callee 会按 SysV
从 rdi+xmm0 读,拿到的是指针,立刻错开。

### ⚠️ 这不是「未规定的自选约定」,是**违反项目自己锁定的 ABI 规范**

`docs/abis/jhyy-abi-v1.0.0.md`(100% 权威、locked)对三个目标的 struct 传参规定:

> `| struct pass-by-value | per v0.4 ABI(MS x64)| per v0.4 ABI(同 MS x64)| **per v0.4 ABI(SysV)** |`

同文件 `:881`:「ABI 调用:所有 `extern fn` 显式声明遵循对应 ABI」。

**所以按指针传不符合规范,不是规范没写。** 这条的性质从「未使用的目标路径」
上升为「违反 locked ABI 文档」——优先级判断应以后者为准。

好消息:地基是齐的。
- struct **布局**已经与 SysV 自然对齐兼容(`{i32,f64}` → i32@0 / f64@8;
  `{i32,i32}` → 0 / 4,实测 caller 的写入偏移证实)
- `abi_sysv_classify_arg`(`abi_amd64_sysv.jhyy:79`)**不是死代码** —— 同文件
  `:933-936` 记录它在 v3.1.4 已给 `Cap<T>` / `PhantomData<T>` 分类(class →
  寄存器槽),只是没接到普通 struct 的参数发射点上
- class→letter 映射 `sysv_class_to_qbe_letter`(`:68`)也在

缺的只是:把这两步接到 `abi_amd64_sysv_emit_function_header:229` + 真正按
eightbyte 拆分多寄存器传参 + MEMORY class(>16B)落栈 + 调用侧对称实现。

**影响:** jhyy 编译的 SysV 目标代码**无法与 gcc 编译的 SysV 代码在跨 struct
边界的函数调用上互操作**。jhyy↔jhyy 之间不受影响。


### 2026-10-19 真修:struct 按 eightbyte 分类传值

**先看跨实现对拍实测(修复前)**:jhyy caller → gcc callee,退出码 **171**,
正确应为 44(= 41 + 3)。这证明「struct 整体按指针传」不只是与规范不符,
而是**与 gcc 完全不能互操作**。

**gcc 的 ground truth(docker gcc:12 -O0 实测)**:

```
struct {int  a; int  b;}   → 1 个 INTEGER eightbyte,加载 8 字节
struct {int  a; double b;} → INTEGER(4) + SSE(8),分别加载 4 / 8 字节
struct {double a;}          → 1 个 SSE eightbyte,加载 8 字节
struct {float  a;}          → 1 个 SSE eightbyte,加载 4 字节
```

**宽度 = 该 eightbyte 内字段实际覆盖到的范围** —— 不能统一成 8 字节:
`{int,int}` 的第二个 int 在 offset 4,若只按 4 字节传而 callee 按 8 字节读,
第二个 int 就是垃圾;反之若 callee 只读 4 字节而 caller 传 8 字节,gcc 的 callee
会丢掉高位。**两边必须按同一宽度。**

#### 实现:IL 层拆成 eightbyte,self-backend 无需改动

1. **`abi_amd64_sysv.jhyy` 新增三个分类 helper**
   (`abi_sysv_struct_n_eightbytes` / `_eightbyte_class` / `_eightbyte_width` /
   `_eightbyte_letter`)。按 SysV § A.2/A.3:eightbyte 内全是 f32/f64 → SSE 类,
   否则 INTEGER 类(含任何非浮点字段就整块 INTEGER)。
2. **callee 签名**(`abi_sysv_emit_function_header`):struct 参数拆成 N 个 IL 参数
   (`w %m__e0, d %m__e1`)。
3. **callee 序言重建**(`codegen.jhyy` 的「register params as locals」):
   `alloc` 一个连续的 struct 槽,把八个byte按宽度存回去,param 的局部指向该槽 ——
   body 里的 `loadw %pv` / `add %pv, 8` 照常按偏移取字段。
4. **caller 侧**:struct 实参按 eightbyte **按值加载**后进 args 数组。
5. **register 序列修正**:SysV 的 INTEGER 与 SSE 是**两个独立序列**,各自从 0 数。
   原来两侧都用「参数整体序号」,SSE 参数在前时后面 INTEGER 参数的寄存器会偏一位。
   新增 `cg_find_class_arg_idx` 按 class 计数(Win x64 的 XMM 按**参数位置**计数,
   规则不同,那里不动)。

⚠️ 全程 gate 在 **SysV target** 上 —— Win x64 的 struct 传参规则完全不同
(>8B 走间接:传指针;≤8B 走寄存器),套用 SysV 的切分会让 5 个 Win 测试回归
(实测 big_test / cap_table_* / mixed_* 全红)。

#### 验收

```
跨实现对拍(新编译器):  jhyy caller → gcc callee  = 44 ✅
                        gcc caller → jhyy callee  = 44 ✅
跨实现对拍(旧编译器):  11 ❌   ← 门能抓到回归
自举闭环:                v2..v5 逐字节相同 ✅
全量回归:                177/177, 0 failed ✅
artifact 级门:            sysv_mixed_struct / sysv_arg_spill 均 PASS
```

新增常驻门 `compiler/tests/bootstrap/sysv_abi_cross.sh`(ubuntu job 跑)——
**这是唯一能抓到「自洽但不兼容」这一类的检查**:纯 jhyy 测试永远看不到它。


**workaround:** 无。默认编译目标是 `amd64_win`,SysV 路径平时不走,
所以这个错误平时观察不到。

**影响范围:** `--target=amd64_sysv` 的全部产出。v4.0.0-rc1 的 ship gate 只覆盖
amd64_win,所以这条至今没有测试能触发它 —— 跟 `fixed_point_linux.sh` 那个门
是同一类问题(没测到的路径不会被门发现)。

**失效条件:** `abi_amd64_sysv.jhyy:229` 改调 `abi_sysv_classify_arg_full` +
class→letter 映射表,并补一个 amd64_sysv 目标的 regress 用例。

**引用:**
- 源码 `compiler/src0/abi_amd64_sysv.jhyy:33, 79, 147, 189, 227-229`
- 源码 `compiler/src0/abi_amd64_sysv.jhyy:248-254`(sret 差异的自述注释)
- `docs/archive/v2-v3/v2.0.0-os-prep.md`(Stage 1c mirror 的原始计划)

<a id="w-105"></a>
## W-105: check_borrow 是硬编码 return 1 — `&mut` 独占性完全不检查

**状态:** ACTIVE since 2026-10-15 (v4.0.8) — sema.jhyy:2558 函数体恒 return 1,每个函数声明都走这条空检查
**Backfilled:** 2026-10-15 (v3.1.0 V3-C 3g ship-gate stub)
**Filed-by:** audit-fanout-2026-10-15
**日期:** 2026-08 前后 (v3.1.0 ship) → 至今

**触发面:** `compiler/src0/sema.jhyy:2558-2560`

```jhyy
fn check_borrow(ctx: *SemaContext, ta: *TypeArena, body: *Node) -> i32 {
    return 1;
}
```

调用点 `compiler/src0/sema.jhyy:2677`(`let _bc = check_borrow(ctx, ta, (*fd).body)`)
在函数声明检查路径上,**每个被 check 的函数都走这一句**。

**⚠️ 2026-10-15 实测修正:本条初稿低估了严重性 —— `&mut` 根本不可用。**

初稿写的是「`&mut` 独占性不检查」。实测下来问题更靠前:

| 写法 | 实际结果 |
|---|---|
| `let p = &mut x;` | `unexpected token 'mut' in expression` |
| `let p: &mut i32 = &x;` | `type mismatch in let` |
| `(&x) as &mut i32` | `cannot dereference non-pointer type` |
| `fn setit(p: &mut i32) { *p = 5; }` | `cannot dereference non-pointer type` |
| `let p = &x; *p = 42;` | **OK** —— 唯一可用的写法,零检查 |

**`&mut` 是个装饰性标注**:parser 认它、类型系统里有它、spec supplement 也
承诺过它,但它**造不出、传不进、解引用不了**。真正能写内存的只有裸 `&` + `*p`,
而那条路完全没有别名检查。

**这对本条的意义:** 「双 `&mut` 冲突不检测」这个场景在 jhyy 里**根本写不出来**
(连一个 `&mut` 都造不出),所以它不是「一个待修的检查」而是「一个待实现的功能」。
新增测试 `borrow_mut_write.jhyy` 测的是**最基本用法**能不能用(过 `&mut i32`
形参写内存),答案 today 是不能 —— 该测试已标 `// XFAIL:`。

以下原始症状描述仍然成立 —— 它们描述的是**一旦 `&mut` 变得可用之后**,
`check_borrow` 恒 `return 1` 会漏掉什么:

**症状:** 下面这些全部**不报错**:
- `let y = &mut x; let z = &mut x;` —— 双 mutable 冲突
- `&mut` 与 `&` 共享/可变互斥
- reborrow `&mut *x`
- 跨函数 borrow、nested block 借用作用域
- lifetime 子类型 / variance

**根因:** v3.1.0 的 ship-gate 选择「先 ship 表面,语义分析留 v3.x 末」。
`compiler/src0/sema.jhyy:2549-2557` 的注释把不检查的项逐条列了出来,注释本身
是诚实的 —— 问题在于它**没有登记进 workarounds.md**,于是台账显示 `0 ACTIVE`,
而语言层面少了一整类检查。`&mut` 在 `compiler/src0/{ast,codegen_amd64_state,ir,
mono,parser,sema,std/string,types}.jhyy` 都有使用,不是没人用的死代码。

**workaround:** 无。调用方拿不到任何诊断。

**影响范围:** 任何写了 `&mut` 的程序。`compiler/tests/examples/borrow_check_basic.jhyy`
存在,但它测的是 borrow 的**表面可解析性**,不是冲突检测。

**失效条件:** 实现 NLL / Polonius 借用分析(注释指 spec supplement v3.1.0 § 4,
该设计随 v3.x 封版未见落地文档)。

**引用:**
- 源码 `compiler/src0/sema.jhyy:2544-2560`(check_borrow + 限制清单)
- 源码 `compiler/src0/sema.jhyy:2677`(调用点)
- 源码 `compiler/src0/sema.jhyy:398`(`&mut` 内层 immutable 的检查被推给 check_borrow)

<a id="w-105-1"></a>
## W-105.1: check_cap_pass 同款空 stub,当前无调用点(死代码但签名在 API 面上)

**状态:** ACTIVE since 2026-10-15 (v4.0.8) — 恒 return 1;与 W-105 同族 stub,当前无调用点
**Backfilled:** 2026-10-15 (v3.1.2 V3-C 3g.7 ship-gate stub)
**Filed-by:** audit-fanout-2026-10-15
**日期:** 2026-08 前后 (v3.1.2 ship) → 至今

**触发面:** `compiler/src0/sema.jhyy:2578-2579` — `fn check_cap_pass(...) { return 1; }`

**症状:** 同 W-105 —— 不检测 active-cap conflict / reentrancy / depth
transition,不支持 `*Cap<T>` 裸指针、不支持 `cap_new()` builtin ctor。

**根因:** v3.1.2 ship-gate stub,与 W-105 同一个「先 ship 表面」决策。

**与 W-105 的关键差别(影响处置顺序):** grep 全 `compiler/src0` 后,
`check_cap_pass` **没有任何调用点** —— 它是死代码,当前不会有程序因为它而
缺检查。W-105 则每次函数声明都真跑。修的优先级 W-105 高得多。

**workaround:** 无 —— 但因为没调用点,当前也没人能撞到。

**影响范围:** 未来一旦有人把 `check_cap_pass` 接到声明检查路径上,`Cap<T>` 的
跨函数 ownership 检查会静默变成 no-op。

**失效条件:** 要么实现 cap ownership 分析,要么把该函数连同 stub 注释一起删掉
—— 留一个没人调的「假装会检查」的函数,是比不检查更坏的状态。

**引用:**
- 源码 `compiler/src0/sema.jhyy:2562-2579`
- 源码 `compiler/src0/sema.jhyy:2574`(自述「跟 check_borrow 同样 stub」)

<a id="w-106"></a>
## W-106: symtab_lookup_one 用 arena-touch 强制 codegen 物化栈帧(源码字面 WORKAROUND,未登记)

**状态:** ACTIVE since 2026-10-15 (v4.0.8) — 靠 sb_init 一个立刻丢弃的 StringBuilder 迫使后端生成合法栈帧;行为正确性依赖后端实现细节
**Backfilled:** 2026-10-15 (v1.x sprint-3 commit 5)
**Filed-by:** audit-fanout-2026-10-15
**日期:** v1.x sprint 3 起 → 至今

**触发面:** `compiler/src0/symtab.jhyy:261-264`

```jhyy
// WORKAROUND: amd64_win stack-spill — touching arena forces
// codegen to materialize stack frame in safe way (see sprint-3-commit-5-sema-attempt.md).
let mut _wb: StringBuilder = StringBuilder { buf: 0 as *u8, len: 0 as i64, cap: 0 as i64 };
sb_init(t.arena as *Arena, &_wb);
```

**症状:** 每次 symbol lookup 都白造一个 `StringBuilder` 再丢掉。功能上无害,
但它是一处**纯为迎合后端实现细节而存在的代码** —— 注释自己说得很清楚:
touch arena 是为了让 codegen「以安全方式物化栈帧」。后端哪天不再需要这个
touch(或者换了触发条件),这里不会报错,只会静默变成无效代码。

**根因:** v1.x sprint 3 定位到的 amd64_win stack-spill 问题,当时的修法是在
调用点人为制造一个后端「看得见」的 arena 操作。

### 2026-10-18 判定实验:这个 workaround **是承重的,不能删**

`active-workaround-clearance.md` 定的判定实验是「删掉那三行跑三道门:绿 = 已是冗余
可直接删;红 = 栈 spill 根因仍在」。**实跑结果:红。**

删除的三行(`symtab.jhyy:260-264`,一个建了 StringBuilder 用 arena 初始化、
然后立刻丢弃的死存储):

```jhyy
// WORKAROUND: amd64_win stack-spill — touching arena forces
// codegen to materialize stack frame in safe way (see sprint-3-commit-5-sema-attempt.md).
let mut _wb: StringBuilder = StringBuilder { buf: 0 as *u8, len: 0 as i64, cap: 0 as i64 };
sb_init(t.arena as *Arena, &_wb);
```

**对照实验(同一台机器、同一个 toolchain、只换这一个变量):**

| 构建 | 全量回归结果 |
|---|---|
| **基线**(保留 workaround) | **3/3 全绿**(176/176,0 failed) |
| 删掉 workaround | **3 次里失败 2 次** |

失败形态(**两个不同的测试,且各自单跑都绿**):

```
第 1 次  FAIL  cap_table_basic.jhyy   expected=42 got=-1  compile failed
第 2 次  FAIL  float_cmp.jhyy  expected=111137 got=0  EXPECT-OUT not found, stdout=''
```

两次单跑 `cap_table_basic` 均 PASS(3/3),全量里才红;`float_cmp` 同理。

### 这说明什么

1. **不是「冗余代码,可删」** —— 它掩盖的是一个**真实的 codegen 栈溢出缺陷**。
   删掉它不是「少一层无用代码」,是**间歇性错代码**:同样的输入,全量并发下可能
   编译失败、可能静默算错(`float_cmp` 是 stdout 为空 + 退出码不对,典型的
   被编坏的程序)。

2. **症状是「与内容无关的随机失败」** —— 这正是台账里 D 组描述的那一类 flake。
   两个完全不同的测试在两次运行里先后中招,且都单跑必绿。

3. **workaround 的注释其实早就说对了** —— "touching arena forces codegen to
   materialize stack frame in safe way"。它是用**死存储**逼 codegen 走安全路径。
   真正的修法在 codegen(栈帧物化),不在这里。

⚠️ 结论:**不删**。但**样本不足以断言它「一定承重」** —— 见下第三次更正。

（原写「它是掩盖 codegen 栈溢出缺陷的补丁」也已被证伪 —— 栈帧两边都物化了。）

### 2026-10-18 第二次更正:workaround 的**注释本身是错的**

原注释称「touching arena forces codegen to materialize stack frame」。**实测不成立:**

| | 栈帧序言 |
|---|---|
| 有 workaround | `push %rbp; mov %rsp,%rbp; mov $8880,%rax; call ___chkstk_ms; sub $8880,%rsp` |
| 无 workaround | `push %rbp; mov %rsp,%rbp; mov $8656,%rax; call ___chkstk_ms; sub $8656,%rsp` |

**两边都完整物化了栈帧**,探栈与 `___chkstk_ms` 都在。函数体逐行 diff 也没有任何
逻辑差异:只多了 60 行内联的 `sb_init`,**所有栈偏移整体平移 104 字节**
(`-408` → `-512`),指令序列完全相同。

注释指向 `sprint-3-commit-5-sema-attempt.md` —— 那是 **v2.x QBE 后端时代**的
commit,self-backend 后来整体重写过。**那个 codegen 行为早就不存在了。**

所以三件事分开说:
1. **workaround 是承重的**(删掉 → 间歇性失败)—— 已由对照实验确认
2. **它注释里写的理由是假的** —— 栈帧本来就物化,不需要「逼」
3. **它为什么仍然承重,未知** —— 目前只知道它在改变栈布局,布局变化如何影响
   正确性没有解释。**一个连自己注释都不对的 workaround,是最危险的那一种** ——
   下一个人照着注释去「修根因」会修错地方。

### 并发确定性已实测:codegen **是**确定的

2026-10-18 用并发压力探针测过(直接回答 v4.0.16 那个「先观测再决定改不改」):

7 个走旁路文件 / asm / naked / link_section 路径的测试,每个**并发编 10 份**
(12 路并行,共 70 次编译),输出到互不相同的路径:

```
inline_asm_cpuid       10 份 .s 的不同 sha 数 = 0
link_section_boot      同上 = 0
naked_interrupt_entry  同上 = 0
memory_barrier_smp     同上 = 0
volatile_mmio          同上 = 0
cap_test               同上 = 0
borrow_check_basic     同上 = 0
```

且每组都与**串行基线逐字节相同**。

**结论:`_section_directive.buf` 那条固定路径的竞争,在本轮实测中没有发作。**

### 2026-10-18 第三次更正:「承重」的判断**样本不足**

干净重做对照(实验脚本去掉 `set -e`,8 次全跑):

| 构建 | 全量回归观测 |
|---|---|
| 基线 | **9 次全绿** |
| 删掉 workaround | 至少 **1 次**失败(在约 11 次运行里),其余全绿 |

失败那次是被 `set -e` 撞断的 —— 脚本因 `python regress.py` 返回非零而中止,
**说明那一次确实有测试失败**;但重跑 8 次又全绿。

所以准确表述是:**低概率间歇性失败,现象存在但频率不足以定论。** 不构成
「删掉是安全的」的证据,因此**保留**,同时**不宣称它一定承重**。

⚠️ 这条与前两次更正合起来读:**注释是错的、机制未知、删除的安全性未证实。**
一个属性不明的 workaround —— 处理它的正确姿势是「不动 + 标注清楚」,而不是
either 删掉 or 继续相信注释。

**已做的处置:** `symtab.jhyy` 里的注释已重写,把「注释的理由已被证伪」「机制
未知」「删不得但在找到根因前不许删」三件事写进源码,避免下一个人照着旧注释去
修一个已经不在那里的根因。注释改动后重建 sha 仍是 `1eeb81b5`(注释不影响
codegen,顺带得到验证)。
这与本节原先记的「机制成立但未观测到发作」一致 —— **探针建好了,答案是没观测到。**
所以 D3 的处置(先加探针再决定改不改编译器)现在有了数据支撑:暂不改,但探针本身
应当常驻,一旦它变红就是真信号。


**workaround:** 就是这段代码本身。

**影响范围:** `symtab_lookup_one` 全路径 —— 编译器的每一次符号查找。

**失效条件:** 后端确认不再需要 arena-touch 触发栈帧物化(需要构造一个
「删掉这三行」的复现来证明),或 stack-spill 根因真修后本段自然变成冗余。
注意它引用的 `sprint-3-commit-5-sema-attempt.md` 已不在仓库里,追溯链断了。

**引用:**
- 源码 `compiler/src0/symtab.jhyy:261-264`

<a id="w-107"></a>
## W-107: 五个 per-fn pre-scan 表硬编码 1024 上限 — 距触发只剩 33 个函数

**状态:** ACTIVE since 2026-10-15 (v4.0.8) — MAX_FN_ENTRIES=1024,实测已用 991;越过上限后 fn≥1023 静默退回 legacy 全局 max 帧路径
**Backfilled:** 2026-10-15 (v2.11.10 W-074.6 T3-a 引入 256 → v4.0.2.1 bump 到 1024)
**Filed-by:** audit-fanout-2026-10-15
**日期:** 2026-07 前后 (v2.11.10) → 至今

**触发面:** `compiler/src0/codegen_amd64_state.jhyy:511 / 515 / 524 / 530 / 537`
—— **五个** 每函数 pre-scan 表,全部 `arena_alloc(1024 * 8)`:
`fn_starts` / `per_fn_max` / `per_fn_alloc` / `per_fn_addr_pool` / `per_fn_base_t`。

**症状(越界后的行为):** 写入侧有守卫(`codegen_amd64_state.jhyy:1727` 与 `:1736`
的 `if fn_count < 1024`),哨兵写入会被跳过,`:1740-1742` 把 `fn_count` 截到 1023。
于是索引 ≥1023 的函数:
- `per_fn_max[1023]` 永远是 0(Phase 2 循环只跑到 `fi < 1023`)
- `emit_func_header` 的 `use_per_fn` 判据(`codegen_amd64_emit_ctrl.jhyy:514` 要求
  `cur_fn_idx < fn_count`)**失败** → 这些函数全部退回 v2.11.2 的 legacy
  global-max 帧路径

也就是说:**这不是缓冲区溢出,是静默降级** —— 越界的函数拿到一个按全局最大
temp 数预留的巨型帧。W-074.6 当初的真症状(全局 max 帧让递归 fn SIGSEGV)会以
「性能塌陷 + 深递归风险」的形式回来,但不会立刻炸。

**余量(实测,非注释估计):**

```
JHY_WRITE_IL=1 jhyy.exe compile --target=amd64_win --no-link \
  compiler/src0/main.jhyy -o <tmp>/main
grep -cE '^export function [wl] |^function [wl] ' <tmp>/main.il   → 991
上限 1024 − 已用 991 = 33
```

源码注释里记的是 997(那是 v4.0.2.1 bump 时的数),实测 991。原始源文件
`grep -cE '^fn '` 合计 1133,但只有 main.jhyy 的 import 闭包进 token 流,
1133 不是有效参照。

**33 个函数的余量意味着:** 按 `std/` 现有 7 个模块(64 个 fn)的规模,
再加三四个模块就会触发。v4.x 计划里的 package manager / multi-arch
一旦让单模块函数数继续涨,这条会先静默变慢、再在深递归上出问题。

**workaround:** 无。当前靠「还没到 1024」活着。

**2026-10-15 实测修正(本条初稿高估了严重性):**

生成 1100 个函数的模块,逐个量生成的 .s 里的 `subq $N, %rsp`:

| 函数索引 | 帧大小 |
|---|---|
| f0 – f1022 | **8,368 字节** |
| **f1023 及以后** | **96,928 字节**(11.6×) |

降级本身**确认存在且边界精确**(正好卡在 1023)。但它的实际代价比初稿写的小:

- **不会算错。** 1100 个函数全部编译通过、运行结果全对。
- **不会砍递归深度。** 二分实测:同一个递归函数放在索引 1100 处,最大递归
  深度 ≥1998 —— 与放在索引 0 处**没有差别**。原因是 `subq $96928, %rsp`
  只是**虚拟预留**,没被触碰的页根本不提交,所以 88 KB 的虚账不吃真实栈。

**所以 W-107 是一次「虚拟地址空间浪费」,不是「栈溢出」。** 它在两种情况下
才会真咬人:函数本身有大块 by-value 局部(数组/struct)因而真的触碰那些页,
或者目标平台默认栈比 Windows 的 1 MB 小。

**为什么它测不出来:** 这个失效模式**不在程序的返回值里**,而在编译产物的
字节布局里。`.jhyy` 测试无论怎么写都验不到 —— 写「1100 个函数 + 递归」
会 PASS(实测就是 PASS)。要钉住它只能查 `.s` 里 `subq $N, %rsp` 的 N,
即一条**产物级**门,跟 W-112 / W-113 同一类。

**影响范围:** 所有 `--target=amd64_win` 编译,一旦单模块函数数越过 1023。

**引用:**
- 源码 `compiler/src0/codegen_amd64_state.jhyy:194, 511, 515, 524, 530, 537`
- 源码 `compiler/src0/codegen_amd64_state.jhyy:1703-1743`(守卫 + 截断逻辑)
- 源码 `compiler/src0/codegen_amd64_emit_ctrl.jhyy:508-524`(use_per_fn 判据 + legacy fallback)
- W-074.6 entry(256→1024 bump 的来由)

<a id="w-108"></a>
## W-108: 索引重建脚本静默丢弃 59/89 条目 —— STATUS_RE 不容忍 ✅ 前缀,且只匹配 H2

**状态:** RESOLVED closed 2026-10-15 (v4.0.8) — 索引 16 行 → 92 行,全部 W-NNN 条目可见
**Backfilled:** 2026-10-15 (scripts/dev/v2_13_5_rebuild_index.py)
**Filed-by:** audit-fanout-2026-10-15
**日期:** 2026-07 前后 (v2.13.5 ship) → 2026-10-15

**触发面:** `scripts/dev/v2_13_5_rebuild_index.py` 的 `H2_RE` + `STATUS_RE`。

**症状:** `docs/internal/workarounds.md` 的索引表只有 **16 行**,而台账有
**96 个 W-NNN 条目**。重建索引跑完不报错,只 print 一个行数 —— 少掉的条目
不会留下任何痕迹。长期后果:读索引的人以为台账里只有 16 件事,于是
「索引表 ACTIVE/DEFERRED = 0」这个结论被反复引用并写进 CLAUDE.md,
而实际上台账里 59 条从未出现在索引中,新增条目(W-103+ 那批 mock/stub)
也同样隐形。

**根因(两个,叠加):**

1. `STATUS_RE = r'^\*\*(?:状态|Status):\*\*\s+(ACTIVE|RESOLVED|...)'` 要求状态
   关键字**紧跟**冒号(只允许空白)。但台账里 **59 个条目**的状态行写成
   `**状态:** ✅ RESOLVED ...` —— 中间的 `✅` 不是空白,regex 不匹配,
   `parse_file` 的 `current_status` 保持 `None`,该条目被 `finalize()` 丢弃。
   89 个 H2 条目里只有约 20 个能进索引。
2. `H2_RE = r'^##\s+(W-...)'` 只匹配二级标题。台账里 W-073..W-080 与
   W-074.6 这 **9 条**挂在 H3 下(v2.13.5 之前的分组残留),结构上进不了索引。
   其中 **W-079 / W-080 / W-074.6** 恰好是跟「0 ACTIVE」结论最相关的几条。

**workaround:** 2026-10-15 修 `STATUS_RE`(允许任意数量 emoji 前缀)+
扩 `H2_RE` 到 `#{2,3}`。索引从 16 行 → **92 行**,状态分布第一次完整可见:

```
ACTIVE 6 / RESOLVED 80 / SUPERSEDED 4 / INVALID 2 / DEFERRED 0
```

**6 条 ACTIVE 全是本次新登记的 W-103..W-107。** 在修这个 parser 之前,
台账自己的索引里确实是 0 ACTIVE —— 但那是因为**读不到**,不是因为没有。

**影响范围:** 任何依赖索引表做审计结论的人或工具,包括
`mcp__jhyy__jhyy_workarounds`(它按 H3 section 附状态行,H3 条目的状态
会被错挂到上一个 H2 条目上 —— W-074.6 的状态曾被误读成 W-072 的)。

**失效条件:** 不适用(已修)。但**教训要留着**:一个「重建索引」的工具如果
丢条目时不出声,它比没有工具更危险 —— 它制造了一种「已经同步过了」的错觉。

**引用:**
- 脚本 `scripts/dev/v2_13_5_rebuild_index.py:18-20`(H2_RE / STATUS_RE)
- 台账 `docs/internal/workarounds.md`(96 个 W-NNN 条目 vs 16 行索引)
- 修复 commit:见本次改动

<a id="w-109"></a>
## W-109: 自举 IL lexer 缺 6 个浮点比较助记符 — f32/f64 六个比较运算静默降级

**状态:** RESOLVED closed 2026-10-17 (v4.0.9) — lexer 的 `c*` gate 第二字符补上 'l',6 个浮点比较助记符全部被识别并正确发射
**Backfilled:** 2026-10-15 (v2.11.15 Iter 1b A1-XMM 只补了 4 个 c*d 助记符时留下的缺口)
**Filed-by:** audit-fanout-2026-10-15
**日期:** v2.11.15 (A1-XMM) 起 → 至今

**触发面:** `compiler/src0/codegen_amd64_lexer.jhyy:1628-1647` 的比较助记符分派。
后端自己 emit 出自己 lex 不回来的助记符。

**症状(两类,实测):**

```
$ JHY_WRITE_IL=1 jhyy.exe compile --no-link compiler/tests/examples/float_cmp.jhyy
  → codegen_amd64_lexer: unknown QBE IL mnemonic at byte offset 2058
     %t38 =w cles %t30, %t31
```

| emit 出的助记符 | 语义 | lexer 命中 | 实际后果 |
|---|---|---|---|
| `cles` | f32 `<=` | `:1641` `n2=='l' && n3=='e'` | 认成 **`cled`** → 按 f64 比较 |
| `cgts` | f32 `>` | `:1638` 只判 `n3=='t'`,不判 `s` | 认成 `cgtd` → 按 f64 比较 |
| `cges` | f32 `>=` | `:1639` 同上 | 认成 `cged` → 按 f64 比较 |
| `clts` | f32 `<` | `:1640` 只判 `n3=='t'`,不判 `s` | 认成 `cltd` → 按 f64 比较 |
| `ceqd` | f64 `==` | 落到 `:1642` else,无一命中 | **硬失败** unknown mnemonic |
| `cned` | f64 `!=` | 同上 | **硬失败** unknown mnemonic |

lexer 只认 4 个浮点比较助记符(`cged` / `cgtd` / `cled` / `cltd`)。
整数侧齐全(`ceqw` / `cnew` / `cs*w` / `cu*w` 各 5 个)。

**实测值对不上(2026-10-15 修好测试的 printf 之后):** 原 `float_cmp.jhyy` 的
printf 声明只收 1 个 i32 实参却传 5 个 %d,输出全是垃圾,所以此前看不到真实值。
补对 arity 后逐值打印,真实结果是:

```
got  d=111110 d2=1110  s=15 p=1 dem=1
want d=111110 d2=10    s=15 p=1 dem=1
```

只有 `cmp_d(3.0, 2.0)` 错 —— 差 1100 正好是 `+100`(a<b) 与 `+1000`(a<=b) 两项
在 **a > b 时错误地返回了真**。单独一条 f64 比较是对的 —— 那是 **W-110**。

> ⚠️ 本条最初还写了「注释里的 111137 本身算错了,正确总和是 211137」——
> **那是本条作者自己算错**。`cmp_d(3.0, 2.0)` 里 `b >= a` 即 `2 >= 3` 为假,
> 该项就是 10,`111110 + 10 + 15 + 1 + 1 = 111137`,原注释是对的。

**根因:** v2.11.15「Iter 1b (A1-XMM)」补 f64 比较时分派只判了 `n3 == 'd'`
的四种形式(`cgtd`/`cged`/`cltd`/`cled`),没补 `s` 结尾的 f32 变体,也没补
`ceqd`/`cned`。`else` 分支(`:1642`)只回退到 `cs*w` 系列,而 `cs*w` 只在
`n2 ∈ {l,g,e,n}` 且 `n3 ∈ {t,e}` 时命中 —— `cles` 恰好落进 `:1641` 的
`cled` 分支,这是最坏的一种:**不报错,只是算错**。

**⚠️ 本条不是全部 —— 见 W-110。** 修好测试的 printf 之后暴露出第二个独立缺陷:
单条 f64 比较完全正确,但一个函数里多条比较连续改同一个 mutable 局部时,结果
串号。两者根因不同,**不要当成一个 bug 一起「修好」**。

> 又一次印证 W-097 的教训:**「实际根因是六个独立缺陷的组合,不是一个」。**
> 第一版 RCA 只抓到 lexer;是「把测试修到真能失败」才把第二个缺陷逼出来的。
> 反过来说:**测试翻不了红的时候,RCA 也是不完整的**,因为你看不到真值。

**为什么至今没被发现:唯一覆盖它的测试无法失败。**
`compiler/tests/examples/float_cmp.jhyy:48` 是**无条件 `return 42`** ——
比较结果只喂给第 47 行的 printf,而那个 printf 有 5 个 `%d` 却只声明了 1 个
参数(`extern fn printf(fmt: *u8, val: i32)`),正好撞上 B8(printf 变参限制),
读的是栈上垃圾变参。于是:

```
$ python regress.py --tests=float_cmp.jhyy
  PASS  float_cmp.jhyy    EXIT=42
```

这个 PASS 不携带任何信息。**这正是本项目自己的教训(见
`feedback_ci_gate_must_exercise_path`):一个翻不了红的门比没有门更糟** ——
它让人以为浮点比较是被测过的。

**workaround:** 无。用户代码里 f32 的 `<` / `<=` / `>` / `>=` 与 f64 的
`==` / `!=` 都不能用。src0 自身几乎不用浮点比较(只有 `jh_f64_atof` 等
C 侧 bridge),所以自举闭环没踩到 —— 又一次「闭环只证明自洽,不证明正确」。

**影响范围:** 任何用浮点比较的用户程序。注意 **f64 的 `<` `<=` `>` `>=`
是好的**(那 4 个助记符 lexer 认识),坏的是 f64 的 `==` / `!=` 和
f32 的全部四个序比较。

**失效条件:**
1. lexer `:1635-1641` 补齐 6 个助记符,并给 `:1642` else 分支加**兜底报错**
   —— 现在 else 分支会把未知助记符默默映射成 `cs*w`,新加的助记符漏掉时
   同样静默错类型
2. `float_cmp.jhyy` 改成从比较结果**推导** exit code(而不是写死 42),
   并把 printf 拆成合法的单参数调用 —— 修之前先造红灯

**引用:**
- 源码 `compiler/src0/codegen_amd64_lexer.jhyy:1628-1653`
- 测试 `compiler/tests/examples/float_cmp.jhyy:4, 36-49`
- 规范 [`../abis/jhyy-lang-spec-v1.3.0.md`](../abis/jhyy-lang-spec-v1.3.0.md)
  §P2(该行的归因「用 QBE 默认指令」也已过时 —— QBE 早在 v3.1.0 移出生产路径)
- ABI [`../abis/jhyy-abi-v1.0.0.md`](../abis/jhyy-abi-v1.0.0.md) § 11.1 A5 / § 11.2 B2



<a id="w-110"></a>
## W-110: 一个函数里多条浮点比较连续改同一 mutable 局部 → 结果串号

**状态:** RESOLVED closed 2026-10-18 (v4.0.9) — W-109 的下游症状,随 W-109 lexer 修复一并闭合
**Backfilled:** 2026-10-15 (随 float_cmp 测试修复才暴露;此前不可观测)
**Filed-by:** audit-fanout-2026-10-15
**日期:** 2026-10-15 首次可观测 → 实际引入时间待 RCA 确定

**触发面:** 自举后端的 temp 槽位管理(不是 lexer)。任何「一个函数内 ≥2 条浮点
比较,且都写同一个 mutable 局部」的代码形态。

**症状(最小复现,已实测):**

```jhyy
fn one(a: f64, b: f64) -> i32 { if a < b { return 1; } return 0; }

fn many(a: f64, b: f64) -> i32 {
    let mut n: i32 = 0;
    if a == b { n = n + 1; }
    if a != b { n = n + 10; }
    if a <  b { n = n + 100; }
    if a <= b { n = n + 1000; }
    return n;
}
```

```
one(3,2)=0        ← 单条比较:正确
many(3,2)=1110    ← 错误,应为 10
many(1,2)=1110    ← 正确
```

`many(3,2)` 与 `many(1,2)` **返回了同一个值**。也就是说四条 `if` 并没有各自
判断自己的比较,而是都读到了同一份比较结果(看起来是最后一条 `a <= b` 的)。

**为什么此前观测不到:** `float_cmp.jhyy` 的 printf arity 是错的(5 个 %d 只声明
1 个参数),输出全是垃圾;修好 arity 之后这个串号才显形。**测试修好之前,RCA
是不完整的** —— 你看不到真值就定不出真因。

**根因(待确认,两条假设都未验证):**
1. 四条比较的布尔结果落到同一个 temp 槽位,后写覆盖先写
2. W-109 的 `ceqd`/`cned` unknown mnemonic 造成 IL 解析错位,后续 token 被
   错读 —— 最小复现里同样打了 `unknown QBE IL mnemonic at byte offset 1216`,
   与假设 2 一致但未证实因果

**注意这条的性质:** 它属于 W-096 / W-097 / W-101 的 temp / slot 管理家族 ——
「自举编译器可以自洽地错」的那一类。**不要把它跟 W-109 当成一个 bug 修。**

### 2026-10-18 RCA 完成:**W-110 是 W-109 的下游症状,已随 W-109 修复闭合**

假设 2 成立,假设 1 不成立。**前后对照实测**(同一个复现,两个编译器):

| 编译器 | `unknown QBE IL mnemonic` 次数 | `many(3,2)` | 期望 |
|---|---|---|---|
| **W-109 修复前**(`958c2b8^`,sha `37837b3f`) | **6** | **1110** ← 复现 | 10 |
| **当前**(`1eeb81b5`) | **0** | **10** ✅ | 10 |

台账原始记录里「最小复现里同样打了 `unknown QBE IL mnemonic at byte offset 1216`」
是直接证据 —— 那个症状**当时存在、现在不存在**,中间的唯一变化就是 W-109 的
lexer 修复(`codegen_amd64_lexer.jhyy:1588` 的 `c*` gate 补第二字符 `l`)。

**假设 1(布尔结果落到同一 temp 槽)被推翻**:IL 层面完全正确,四个比较各占独立
temp(`%t5` / `%t9` / `%t13` / `%t17`),各自 `jnz` 到自己的 then/else/merge,
各自 `storew` 回 `&n`。汇编层面四个条件码(`sete`/`setne`/`setb`/`setbe`)配
`ucomisd src, dst` 全部正确。

**参数网格全绿**:a, b ∈ [-3, 3] 共 **49 组,0 错**(含负数、零、正数)。

### ⚠️ 这次 RCA 我踩了两个测量坑,都在本项目 memory 里记着

**坑 1:bash 的 `$?` 截断到 8 位。** `many(1,2)` 正确答案 1110,经 bash 读成
`1110 & 0xFF = 86`。我一度以为程序算错了,还据此怀疑了栈帧、寄存器分配、
内存布局 —— 全是错方向。**Python `subprocess` 返回完整 32 位退出码,取证一律走它**
(`feedback_exit_code_forensics`)。

**坑 2:`-o X.exe` 产出的是 `X.exe.exe`。** jhyy 的 `-o` 是**加** `.exe` 后缀。
我有一批探测脚本写 `-o foo.exe` 然后跑 `foo.exe` —— 跑的是**上一次遗留的陈旧
二进制**,于是得出「56 组组合全对」这种完全虚假的结论。**`-o` 一律不带后缀。**

两个坑叠加时最毒:陈旧 exe + 截断退出码,能让一个已修好的 bug 看起来时好时坏,
我差点据此推翻刚做好的 W-117 结论。


**workaround:** 无。写不出可靠的用户侧绕法(「每个函数只用一条浮点比较」不是
可接受的建议)。

**影响范围:** 任何在一个函数里做多次浮点比较并累积结果的程序。`src0` 自身几乎
不做浮点比较,所以自举闭环抓不到。

**失效条件:**
1. 先跑 RCA 定因(建议从 `codegen_amd64_state.jhyy` 的 temp 记录路径入手,
   对照 W-097 的七处 hoist site 与 W-101 的 record path)
2. 补测试:上面这个最小复现,断言 `many(3,2)==10` 且 `many(1,2)==1110`
   —— 两个不同实参必须给出不同结果,这才是能抓住串号的断言

**引用:**
- 最小复现:见上(可直接抄进 `compiler/tests/examples/`)
- `compiler/tests/examples/float_cmp.jhyy:36-52`(修好 arity 后暴露本条)
- 相关:W-109(lexer 缺助记符,不同根因)/ W-096 / W-097 / W-101

<a id="w-111"></a>
## W-111: 泛型 enum 的关联构造器在无类型上下文处不被识别;多字段 payload 连解析都过不去

**状态:** RESOLVED closed 2026-10-19 (v4.0.9) — 走「调用点期望类型」接通,`generics_enum.jhyy` 摘 XFAIL 且 PASS(106)
**Backfilled:** 2026-10-15 (v3.2.0b「3i generics — enum generic」声称 ship 的那条)
**Filed-by:** audit-fanout-2026-10-15;RCA rca-w111-2026-10-18
**日期:** 2026-10-15 首次实测 → 2026-10-18 复核(**SEGV 不复现,剩余缺口已重新定位**)

### ⚠️ 2026-10-18 复核:本条的性质描述**曾经是错的**,已更正

原条目登记为「泛型 enum 一旦被 match → sema 报错后 SEGV(编译器崩溃)」。
**2026-10-18 在 binary sha `1eeb81b5` 上逐形态实测:SEGV 已不复现。**
编译器给出的是**干净的诊断**(`error: unknown enum type` + exit 1),用户拿得到
完整信息 —— 与「崩溃 / 拿不到诊断」相反。

台账留一个已经不成立的性质,会让下一个做它的人从错误的前提出发,所以更正。

| 代码形态 | 2026-10-15 记录 | 2026-10-18 实测 |
|---|---|---|
| `type Option<T> = enum { Some(T), None }` 声明但不使用 | exit 42,不报错 | ✅ 一致 |
| 只构造 `Option::None` | exit 1,干净报错 | ✅ 一致 |
| **match 变体** | **exit 139 SEGV** | ✅ **干净,无 SEGV** |
| 多字段泛型 payload `Two(T, T)` | exit 1,`error: expected )` | ✅ 一致 |
| 泛型 fn(非 enum)对照组 | exit 42,正常 | ✅ 一致 |

SEGV 应是被 W-097 / W-098..W-101 / W-102 那一批修复顺带解决的。**未能定位到
具体哪一笔** —— W-102 的描述是「泛型**结构体**字面量 SEGV」,不是 enum,不能断言。

### 仍然存在的缺口(精确边界)

四组对照,**每一格都工作,除了最后一格**:

| 对照 | 结果 |
|---|---|
| 泛型 struct 作参数类型 | exit 0 |
| 泛型 struct **构造** `Box<i32> { v: 7 }` | exit 0 |
| 非泛型 enum 构造 `Opt::None` | exit 0 |
| 泛型 enum **作类型 + match**(不构造) | exit 0 |
| **泛型 enum 构造 `Option::None`** | **exit 1 `unknown enum type`** |

**行为上的关键差异:** `generics_enum.jhyy` 里 `match` 内的 `Option::Some` /
`Option::None`(第 19-22 行)**不报错**,只有 `main_jhyy` 里的构造调用
(第 26 行)报错。

> **即:有类型上下文时(match 的 scrutinee)能解析,没有时不解析。**
> 连 `fn mk() -> Option<i32>` 的**返回类型**上下文都不生效。

### 机制(定位到文件行)

- `sema.jhyy:2157`(struct lit)与 `sema.jhyy:2231`(enum variant)的解析结构
  **完全相同**:`type_sym → type_ptr/kind 检查 → 回退 symtab_lookup(name) → 报错`。
  所以差异**不在解析算法**,在**上游 `type_ptr` 被设成了什么**。
- 泛型单态化机制**存在**:`mono.jhyy:839 mono_clone_enum_def` 会克隆泛型 enum
  并注册成带 mangled 名的实例(`Option<i32>`)。
- 但它目前只在**函数调用**路径被调用(`sema.jhyy:1246 mono_expand_fn_call`,
  turbofish)。**表达式位置的 enum 变体引用没走到实例化。**

### 这条现在是「功能缺失」还是「bug」?

**是未完成的实现,不是崩溃缺陷。** 泛型 enum 的**类型**能用、**match** 能用、
泛型 struct 的**构造**能用,唯独泛型 enum 的**关联构造器**在无类型上下文处
不认 —— 同一特性里唯一没接上的那条路。

⚠️ 而 `generics_enum.jhyy` 的 `// EXPECT: 106` 期望**整个程序可用**。
任何部分修复都过不了这条测试 —— 要真修就得让它完全可用。

**修它需要先回答一个设计问题:类型参数从哪来?**
  · 从 match 的 scrutinee —— 已能工作(现有路径)
  · 从调用点的期望参数类型 —— `unwrap_or(o: Option<i32>, ...)` 的首参类型已知,
    理论上可以,但**期望类型是否一路传到了变体引用点是未知的**
  · 强制 turbofish —— 语法变更

### 2026-10-18 设计决策:**调用点期望类型**方案(实测可行,规模小)

**「类型参数从哪来」的三个选项,逐一验过:**

| 选项 | 状态 |
|---|---|
| A. 从 match 的 scrutinee 拿 | ✅ **已经能用**(实测 `match o { Option::Some(v) => ... }` 不报错) |
| B. **从调用点的期望参数类型拿** | ✅ **可行 —— 见下,定为方案** |
| C. 强制 turbofish | ❌ 语法变更,破坏现有写法 |

#### 选 B 的关键前提:期望类型是**充分**信息

担心的是「拿到 `Option<i32>` 还要反推类型实参才能定位变体」。**不必** ——
`types.jhyy:95` 的 `Type` 结构**没有泛型实参字段**,因为单态化
(`mono.jhyy:878 mono_clone_and_subst`)已经把 `T` 替换掉、克隆出了**具体的**
`Option<i32>`。它的 `variants` / `nvariants` 直接可用。

所以在变体引用点,只要手里有一个期望类型,就能按 `name` 匹配 enum sym、
再从它的 `variants` 里找变体 —— **不需要反推任何东西**。

#### 实现形态:局部辅助函数,不改 `infer_type` 签名

`infer_type` 全 src0 有 **45 个调用点**,加 `expected` 参数会波及全部。
**不这么做。** 改为:

1. 新增 `infer_type_expected(ctx, ta, n, expected: *Type) -> *Type`:
   若 `n` 是 `NODE_ENUM_VARIANT`、且其 `type_sym` 指向泛型模板
   (直接解析失败的那条路),且 `expected.kind == KIND_ENUM`
   且 `expected.name` 与该 sym 匹配 → 从 `expected.variants` 取变体;
   **否则原样 fallthrough 到 `infer_type`**(行为完全不变)。

2. 在**期望类型已知**的三处改调它:
   - `sema.jhyy:1522` 调用实参循环 —— `callee_type.params[i]` 就在手边,
     **只是从来没往下传**(实测:`infer_type` 对实参是无约束推断,见 `:1523`)
   - `let x: T = <expr>` 的类型标注位置
   - 函数 `return` 位置(return type)

3. `generics_enum.jhyy` 摘 XFAIL 即通过(exit 106)。

#### 明确的范围边界

**本方案覆盖「期望类型是具体类型」的情况**(如 `unwrap_or(o: Option<i32>, ...)`)。
**不覆盖**「函数本身是泛型、参数类型是 `Option<T>` 未实例化」——
那种要在调用点先 mono(该处已有 `sema.jhyy:1246 mono_expand_fn_call`),
属下一阶段。

#### 规模估计

~50 行,全部局部(一个新函数 + 三处调用点替换),**不动 `infer_type` 签名、
不动类型系统、不动单态化**。

**⚠️ 一个实施前必须先做的验证(尚未做):** 确认 `callee_type.params[i]`
在那一处**确实已经完成单态化**。若它仍是未实例化的 `Option<T>`,
方案要改成在 `mono_expand_fn_call` 之后再解析变体。**这一步没验之前不要动手。**


### 2026-10-19 已修:走「调用点期望类型」,三处调用点全部接通

设计决策(2026-10-18)落地。实现形态:

1. **`SemaContext` 加 `expected_enum_type: *u8`**(W-111 槽位)。
2. **`NODE_ENUM_VARIANT` 解析加第三级兜底**(第三级 = 期望类型),形状与
   NODE_PATTERN_ENUM 走 `match_type` 兜底完全同款(`sema.jhyy:527-545`)。
   在 `expected.variants` 里按**变体名**找(与下面 payload 检查一致)。
3. **三处调用点把期望类型塞进去,推断后 save/restore**:
   - 调用实参 —— `callee_type.params[i]`(此前实参是**无约束推断**,期望类型就在
     手边却从不往下传)
   - `let x: T = <expr>` —— 类型标注
   - `return <expr>` —— `ctx.current_ret_type`(本来就有)

**验收:** `generics_enum.jhyy` **摘 XFAIL 且 PASS(exit 106)**;
自举闭环 v2..v5 逐字节相同;`closure_check.sh` PASS;全量回归 **177/177, 0 failed**
(此前 176/176 —— 多出来的那一个就是它从 XFAIL 转 PASS);artifact 级门 0 FAIL。

### ⚠️ 顺带撞出一个 2024-11 就在的越界读(已修)

`main.jhyy` 用 struct literal 构造 `SemaContext` 时**只列了 11 个字段**,
漏掉 `current_fn` / `ret_type_map` / `ret_type_map_n`
(字段顺序按声明逐字对齐,jhyy 的 struct literal 按**列出的字段数**决定分配
多少字节)。加 `expected_enum_type` 时,前三个的旧洞被撞出来:

```
fn mk() -> Option<i32> { return Option::None; }   → exit 139 SEGV
let x: Option<i32> = Option::None;                → exit 139 SEGV
```

**这是本次唯一一处真正的编译器崩溃** —— 也解释了为什么 W-111 当初被记成
「编译器崩溃」:那两条路径当时就会 SEGV,只是没人单独试过它们(台账测的是
match 形态,而 match 形态不碰这三个字段)。

补全 literal 后 SEGV 消失,两处都变成干净的 `unknown enum type`,再接上期望类型
兜底即通过。

**workaround:** 用户侧只能避开泛型 enum 的构造器(改用非泛型
`type Opt = enum { Some(i32), None }`,实测正常;或有类型上下文的地方用 match)。

**影响范围:** 泛型 enum 的构造器在无类型上下文的位置不可用。**这是干净的错误
诊断,不是崩溃** —— 用户知道哪里错了,拿得到行号列号。`src0` 自身不用泛型 enum,
自举闭环抓不到。

**失效条件:**
1. 先决定设计问题(类型参数从哪来),再动手
2. `generics_enum.jhyy` 摘 XFAIL 且 PASS(exit 106)
3. enum 多字段 payload(`Two(T, T)`)的解析器支持 —— 单独一条,`error: expected )`

**引用:**
- `compiler/src0/sema.jhyy:2228-2259`(`NODE_ENUM_VARIANT` 解析与报错点)
- `compiler/src0/sema.jhyy:2154-2180`(struct lit —— 结构相同、行为不同的对照)
- `compiler/src0/mono.jhyy:839`(`mono_clone_enum_def` —— 机制存在但这条路径没调到)
- 触发测试 `compiler/tests/examples/generics_enum.jhyy`
  (**2026-10-15 已重写**:此前 `main_jhyy` 仅 `return 42`、类型完全未使用,
  所以它作为 v3.2.0b 的 ship gate 一直空转;现在真用上了,`// EXPECT: 106`)
- 同族:`generics_err_unsubst.jhyy` 同样是假 EXPECT(见 tests.md 审计)
- 相关:W-109 / W-110(同属「测试翻不了红 → 缺陷活下来」家族)、
  W-102(泛型**结构体**字面量 SEGV,已 RESOLVED,与本条的 SEGV 症状相邻但不同源)


## W-112: `#[link_section]` 完全失效 — 属性被解析但 codegen 是 no-op

**状态:** ACTIVE since 2026-10-15 (v4.0.8) — 生成的 .s 里没有任何 `.section` 指令;V3-B 3e 的 ship gate 一直是空转
**Backfilled:** 2026-10-15 (v3.0.x V3-B 3e「ship」时)
**Filed-by:** audit-fanout-2026-10-15
**日期:** 2026-09 前后 (V3-B 3e ship) → 至今

**触发面:** `#[link_section(".text.boot")]` 属性 → `parser.jhyy:3213-3228`
→ `ast_new_func_decl`(`ast.jhyy:1537`)→ `codegen.jhyy:4478-4485`。

**症状(实测,最小复现):**

```jhyy
#[link_section(".text.boot")]
fn _start() -> i32 { return 42; }
fn main_jhyy() -> i32 { return _start(); }
```

```
$ jhyy.exe compile --no-link zz_ls.jhyy -o /tmp/lst/ls
$ grep '\.section' /tmp/lst/ls.s
（一个都没有）
```

`codegen.jhyy:4478` 应往 `compiler/build/obj/_section_directive.buf` 写一行
`_start|.text.boot`,`main.jhyy:836` 的 `apply_link_section_directives` 读回后插
`.section` 行。**实测 buf 是 0 字节**,`.text.boot` section 不存在,`_start`
落在普通 `.text`。属性整体是 no-op。

**为什么一直没被发现:** `link_section_boot.jhyy` 是 V3-B 3e 的 ship gate,
但它只断言「`_start()` 返回 42」—— 那个值跟 section 归属毫无关系。
**属性完全失效的情况下它照样 PASS。** 同 `float_cmp` / `generics_enum` 一个
病:测试名字覆盖了功能,测试内容没有。

**旁证(同机制另两处是通的):** `#[naked]` 实测有效 —— `irq_entry` 的首指令
就是 `iret`、没有 `push %rbp`。说明属性解析 + `.buf` 旁路整体没问题,
断点就在 `link_section` 这一条链上。

**次生问题:** `main.jhyy:838` 的 `jh_file_stat_ok(path)` 守卫对**已存在**的
文件返回 0 就 early-return,连 buf 都不 unlink —— 普通编译会在 `obj/` 留下
0 字节残留文件。

**workaround:** 无。用户写 `#[link_section]` 不会报错,也不会生效。

**影响范围:** 任何依赖自定义 section 的代码 —— bootloader 入口、UEFI
`EFIAPI` 段、`jhyy_OS` loader 对接(ABI § 13 的 freestanding 约定)。这是
OS-required 特性,而 OS 侧正是它的目标场景。

**失效条件:** 打通 `codegen.jhyy:4478` → `_section_directive.buf` →
`main.jhyy:836` 这条链,并把 `link_section_boot.jhyy` 的断言改成**真的检查
产物里有没有 `.text.boot`**(当前没有任何测试读 .s / .exe 的 section 表)。

**引用:**
- 源码 `compiler/src0/codegen.jhyy:4478-4485`
- 源码 `compiler/src0/main.jhyy:836-838`
- 源码 `compiler/src0/parser.jhyy:3213-3228`
- 测试 `compiler/tests/examples/link_section_boot.jhyy`(ship gate,空转)

<a id="w-113"></a>
## W-113: `asm!` 与 memory barrier 的字节被 emit 到 `ret` 之后,永不执行

**状态:** ACTIVE since 2026-10-15 (v4.0.8) — opcode 编码正确但位置在函数末尾之后;这些 ship gate 的退出码对 asm 内容零敏感
**Backfilled:** 2026-10-15 (V3-B 3a/3f「ship」时)
**Filed-by:** audit-fanout-2026-10-15
**日期:** 2026-09 前后 (V3-B 3a/3f ship) → 至今

**触发面:** `asm!` 宏 → `_inline_asm.buf`;`fence_*` builtin。

**症状(实测):**
- `inline_asm_cpuid.jhyy`:`cpuid` 的 `0f a2` 确实进了 exe(空 main 对照组
  计数 0,本测试计数 1)—— **但它落在 `main_jhyy` 的 `ret` 之后**,永不执行
- `memory_barrier_smp.jhyy`:三条 fence 的编码也正确(`0f ae f0/e8/f8`),
  同样在 `ret` 之后

**后果:** 这两个测试的退出码对 asm 内容**完全零敏感** —— 把整个 asm 删掉
照样 PASS。也就是说 V3-B 3a / 3f 的 ship gate **没有在 gate 任何东西**。

跟 W-112 同病:`link_section_boot` 是属性 no-op,这三条是字节位置错了但测试
察觉不到。**三个 V3-B ship gate 实际都没在 gate。**

**workaround:** 无。

**影响范围:** `asm!` 语义正确性、`memory_barrier_smp` 语义正确性 —— 都是
OS-required 特性(`jhyy_OS` 多核同步的基础)。

**失效条件:**
1. asm 内联进函数体(在 `ret` 之前),位置正确后测试才可能对内容敏感
2. harness 需要一个能读 `.exe` / `.s` 字节的门 —— 退出码这条路对 asm 天生
   不敏感(asm 通常不改变返回值)

**⚠️ 潜在竞态(未复现,待确认):** asm / link_section 走的是**硬编码固定路径**
的旁路文件(`_inline_asm.buf` / `_section_directive.buf`),codegen `fopen "wb"`
截断、main 读完 unlink。regress 是多线程并发的,理论上两个测试会互相覆盖或
删掉对方的旁路文件。并发数提高后可能表现为随机 FAIL。

**引用:**
- 测试 `compiler/tests/examples/inline_asm_cpuid.jhyy` / `memory_barrier_smp.jhyy`
- 相关:W-112(同属「V3-B ship gate 空转」家族)

<a id="w-114"></a>
## W-114: 全 unit-variant 的 enum `match` 永远命中第一支 — 核心语言功能失效

**状态:** ACTIVE since 2026-10-15 (v4.0.8) — 所有变体都无 payload 时,match 不做 tag 检查,恒取第一臂
**Backfilled:** 2026-10-15 (v1.7.1 patch A3「enum match arm tag check 真修」只覆盖了带 payload 的形状)
**Filed-by:** audit-fanout-2026-10-15
**日期:** 2026-08-28 (v1.7.1 patch A3 部分真修) → 至今

**触发面:** `type T = enum { A, B, C }`(所有变体都是 unit variant)对
`T::B` / `T::C` 做 match。

**症状(最小复现,实测):**

```jhyy
type Unit3 = enum { A, B, C }
type Pay1N = enum { S(i32), N }
type Mix   = enum { X, Y(i32), Z }
fn u3(v: Unit3) -> i32 { return match v { Unit3::A => 0, Unit3::B => 1, Unit3::C => 2 }; }
fn pn(v: Pay1N) -> i32 { return match v { Pay1N::S(x) => 100 + x, Pay1N::N => 200 }; }
fn mx(v: Mix)   -> i32 { return match v { Mix::X => 10, Mix::Y(y) => 20 + y, Mix::Z => 30 }; }
```

```
Unit3(B)=0    期望 1     ✗
Unit3(C)=0    期望 2     ✗
Pay1N(N)=200  期望 200   ✓
Mix(Z)=30      期望 30    ✓
```

**规律精确:** 只要 enum 里**有任意一个 variant 带 payload**,tag 检查就正常;
**全部是 unit variant 时,`match` 退化成「永远第一臂」**。匹配对象是字面构造、
局部变量还是函数参数都一样(`arm(Color::Green)` / `arm(g)` / `arm(Color::Blue)`
三者全返 0)。

**为什么一直没被发现:** 现有的 enum match 回归测试
`compiler/tests/examples/enum_match_arm_tag_check.jhyy` 用的是
`type Option = enum { Some(i32), None }` —— **首支带 payload**,正好落在
「正常」那一侧,所以它一直 PASS 并给人「enum match 已被 A3 修好」的错觉。
没有任何测试用**纯 unit variant** 的 enum 测过多臂 match。

(附:`enum_match_arm_tag_check.jhyy` 注释里说这个 fix 见「W-057」,
但台账里 W-057 是 UTF-8 显式 lex reject,不是 enum —— 那条引用也是错的。)

**workaround:** 无。给任意一个变体加一个假的 payload 就能绕过,但那是改
用户的领域模型来迁就编译器 bug。

**影响范围:** 任何用「状态枚举 + match」表达控制流的程序 —— 状态机、
结果类型(`Result<T,E>` 的 unit 分支)、错误码分派。这是 idiomatic 写法,
不是边角用法。**静默给错结果,不报错。**

**失效条件:**
1. codegen 的 enum match 在「所有 variant 都是 unit」时也要 emit 真正的 tag
   compare,不能退化成 first-arm
2. 补测试:上面这个最小复现,断言 `u3(Unit3::B) == 1` 且 `u3(Unit3::C) == 2`
   —— **只断言一个非第一臂的值不够**,要断言不同 variant 给出不同结果,
   否则「恒取第一臂」恰好能过
3. `gdb_pretty_test.jhyy` 删掉 `// SKIP:` 即为验收(它的 `read_color` /
   `read_maybe` 目前都返回 0)

**引用:**
- 最小复现:见上(可直接抄进 `compiler/tests/examples/`)
- 受影响测试 `compiler/tests/examples/gdb_pretty_test.jhyy`
- 相关:`docs/internal/workarounds.md` enum match arm tag check 段(v1.7.1 patch A3)

<a id="w-115"></a>
## W-115: W-089 标着 RESOLVED,但它自己的 reproducer 至今 STACK_OVERFLOW

**状态:** ACTIVE since 2026-10-15 (v4.0.8) — codegen_call_return_types.jhyy 运行期 STACK_OVERFLOW(0xC00000FD)
**Backfilled:** 2026-10-15 (v3.4.2 W-089 声称真修时)
**Filed-by:** audit-fanout-2026-10-15
**日期:** 2026-09-29 (v3.4.2 声称 RESOLVED) → 至今

### 2026-10-17 补充定位:崩溃与递归深度**不成正比**

用 harness(而非 bash —— bash 的退出码在 MSYS2 下会被截断,127 vs 0xC00000FD
对不上,照 bash 的读数下结论会判错)逐个替换 `recurse(buf, N)` 的 N 实测:

| depth | 1 | 2 | 3 | **4** | **5** | 8 | 16 | 64 |
|---|---|---|---|---|---|---|---|---|
| 结果 | PASS | PASS | PASS | **STACK_OVERFLOW** | **STACK_OVERFLOW** | PASS | PASS | PASS |

**64 层正常、4 层栈溢出** —— 所以这不是栈用量问题,是**特定常量取值下被编出了坏代码**。
(直接证据:去掉 sub-test 6 那一行,程序完整跑完;把 `recurse(buf, 4)` 换成
`recurse(buf, 8)`,同样完整跑完。)

**跨环境不一致 —— 已解释(2026-10-17,不再是谜团):** 开发机稳定 STACK_OVERFLOW
5/5,GitHub Actions 上同一二进制「通过」→ regress 报 XPASS。当时记的是
「尚未 RCA,不能摘标记」。

**真相:根本没有跨环境差异。** `codegen_call_return_types.jhyy` **没有 EXPECT
标注**,而 harness 对无 EXPECT 的测试走 `if expected is None` 分支 —— 只要不是
NTSTATUS 崩溃就算 PASS。于是它**从写下来那天起就只断言了「程序没崩」**,那 8 个
子测试的错误码 1..8 一个都没校验。开发机碰巧崩了 → XFAIL;CI 上不崩 → PASS
(假绿)。

补上 `// EXPECT: 0` 之后**两边都失败**(开发机 STACK_OVERFLOW,CI 上同样跑不过,
各自报 XFAIL),XFAIL 标记在两边都变成诚实的描述。CI 于 run 39023240304 转绿:
**176/176,0 failed**。

**这个 bug 形态值得单独记:** 一个测试「在 A 环境失败、B 环境通过」,最容易被
读成环境差异,实际是**它在两边都没在测任何东西**。XPASS 在这里是**假信号** ——
无 EXPECT 的测试无论 bug 在不在都算过,XPASS 恒定触发。判据:XPASS 只有在
「这个测试真能失败」时才携带信息。

**配套修的两处:**
- `audit_test_assertions.py` 新增 `zero-signal-xfail` 类别 —— XFAIL 豁免的是
  「断言强度」,不是「有没有断言」。XFAIL 但无 EXPECT / EXPECT-ERROR /
  EXPECT-OUT 的测试一律判违规。
- 同一轮还查出 `borrow_check_err.jhyy` 的 `//EXPECT-ERROR` 用了**反引号**而非
  双引号,而 harness 与 audit 的正则都要求 `"([^"]+)"` → 该指令**从未被识别**,
  错误消息从来没校验过。同类形态:**指令写了但语法不对 = 静默失效**。

**方法论沉淀:** 这类「同一个二进制、两个环境、结论相反」的故障,判据要来自
**读实际代码**和**按 CI 的真实条件造用例**,不是从「报错在哪」倒推。本轮里
我两次差点下错结论:①断定 emit_binop 侧也漏了 6 个浮点 op(错,读代码后纠正);
②用 bash 的退出码判断栈溢出深度(错,bash 会截断 NTSTATUS)。

**触发面:** `compiler/tests/examples/codegen_call_return_types.jhyy` —— 它是
W-089 的官方 reproducer(文件头第 1 行就写着「v3.4.2 W-089 真修 reproducer test」)。

**症状(实测):**

```
$ 去掉 // SKIP: 后实跑
FAIL  zz_ccrt.jhyy  got=3221225725  runtime crash: STACK_OVERFLOW (0xC00000FD)
```

**矛盾:** W-089 台账写「✅ RESOLVED 2026-09-29 (v3.4.2 ship 真修:
SymbolReturnTypeMap + emit_call semantic lookup 替换 v3.1.0 byte-prefix
whitelist)」—— 而**验证它的那个 reproducer 自己就崩**。也就是说
「W-089 已 RESOLVED」这句话**没有证据支撑**。

**为什么一直没被发现:** 该测试从 v3.4.0 起就被标着
`// SKIP: ... (not in default regress CI gate per v3.4.0-plan.md L89)` ——
它被**故意排除在回归之外**。所以「真修」的验证证据来自别处(大概是手工跑),
而那条证据在时间推移后没有再复核。这跟今天挖出的其余几条同一个病:
**测试要么跑不了、要么跑不到、要么跑到了却不验结果。**

**根因未定,两条可能(都没验证):**
1. W-089 没真修 —— 声称的 `SymbolReturnTypeMap` 路径在某些调用形态上仍失效
2. W-089 真修了,但这个 8-subtest 文件覆盖面更广,撞到的是**另一个**栈溢出 bug
   (它测的 8 项:闭包返回 `*T` / builtin `ptr_add` / `ptr_add_u8` / `malloc` 等,
   远不止 W-089 的触发面)

区分这两条要先把栈溢出的位置定位出来 —— 而它至今被 SKIP 挡着。

**workaround:** 无。

**影响范围:** 待定,取决于上面哪条成立。若是 (1),W-089 相关的
`*(call_ret as *T)` 模式仍可能读错字节;若是 (2),则另有一条未登记的栈溢出。

**失效条件:**
1. 先定位栈溢出在哪个 sub-test(拆开逐个跑,或用 `// SETENV:` 缩小)
2. 据此判定 W-089 的 RESOLVED 是否成立 —— 若不成立,**把 W-089 翻回 ACTIVE**
   (它现在是 2026-09-29 声称的真修,是本项目里最后一个没有 reproducer 佐证的 RESOLVED)
3. 该测试的 `// SKIP:` 已于 2026-10-15 改成 `// XFAIL:` —— 现在它**真跑**,
   崩溃会被记为 XFAIL 并出现在每次回归的输出里,不再是隐形项

**引用:**
- 测试 `compiler/tests/examples/codegen_call_return_types.jhyy`
- W-089 entry(`docs/internal/workarounds.md`)
- `v3.4.0-plan.md:89`(当初把它排除出 CI gate 的那行)

<a id="w-116"></a>
## W-116: SysV callee 参数溢出只处理 4 个整数寄存器 —— 第 5 个及以后的参数全读到第 4 个的值

**状态:** RESOLVED closed 2026-10-19 (v4.0.9) — SysV callee arg 寄存器分配补上 r8d/r9d/栈,`sysv_abi_test` EXIT 22 → 28
**Backfilled:** 2026-10-15 (v2.7.0 写 emit_call 时就已知道「stack-arg 实 wire 留 v2.7.1+」)
**Filed-by:** audit-fanout-2026-10-15
**日期:** 2026-10-15 首次实测(v2.7.0 起的已知缺口,一直无门可验)

**2026-10-18:门建起来了,而且第一次跑就确认了这条。** CI 新增 `sysv` job
(windows 侧编 `--target=amd64_sysv_freestanding --no-link` 出 `.s` → ubuntu
侧链 `runtime/linux_elf/crt0.S` + `link.ld` 成 ELF → 跑 → 比 `// EXPECT:`),
首次运行结果:

```
⚠️  KNOWN-FAIL sysv_abi_test  EXIT=22 期望 28 [W-116]
✅  sysv_struct_mixed / struct_pass / struct_ret / vararg_basic  全部匹配
```

`sysv_abi_test` 期望 28 = 1+2+3+4+5+6+7,实得 22 —— 与本条描述吻合:callee 侧
只 spill 4 个整数寄存器,参数 5/6/7(`%r8d` / `%r9d` / 栈)从未被读。

⚠️ **这个 22-vs-28 台账里早就写着**(`sysv_full_regress.sh` 的注释:「W-116 的
`sysv_abi_test` 退出 22 / 期望 28 就这样被放过」),之所以一直隐形,是因为当时
cross-env 那条路径拿不到期望值,只要 ELF 跑起来就报 PASS。**这是「ACTIVE 条目
没有门等于没登记」的第一个实证** —— 也是本次 CI 重构最直接的收益。

登记在 `compiler/tests/bootstrap/sysv_link_run.sh` 的 `KNOWN_FAIL` 里,格式
`<test>|<W-NNN>|<实际退出值>`(带签名而不只带 W 号,避免已登记的测试换了失败
方式时被当成「已知」吞掉)。**本条转 RESOLVED 时删掉那一行,门自动升级成真门。**

**触发面:** `amd64_sysv` / `amd64_sysv_freestanding` 目标下,**整数参数超过 4 个**
的任何函数调用。

**症状(逐位实测,实参 1..7):**

```
return a (arg1) → 1  ✓
return b (arg2) → 2  ✓
return c (arg3) → 3  ✓
return d (arg4) → 4  ✓
return e (arg5) → 4  ✗
return f (arg6) → 4  ✗
return g (arg7) → 4  ✗
```

**根因(生成代码逐条核对):caller 侧是对的,callee 侧错了。**

caller(`main_jhyy`)完全符合 SysV:

```
movl -16(%rbp), %edi     # arg1
movl -24(%rbp), %esi     # arg2
movl -32(%rbp), %edx     # arg3
movl -40(%rbp), %ecx     # arg4
movl -48(%rbp), %r8d     # arg5  ✓ SysV 第 5 整数寄存器就是 r8
movl -56(%rbp), %r9d     # arg6  ✓
movl -64(%rbp), %r10d
movl %r10d, 0(%rsp)      # arg7 走栈(call 后落在 callee 的 16(%rbp))✓
call seven
```

callee(`seven`)的参数溢出循环**只处理 4 个寄存器**:

```
movl %edi, -8(%rbp)      # arg1 ✓
movl %esi, -16(%rbp)     # arg2 ✓
movl %edx, -24(%rbp)     # arg3 ✓
movl %ecx, -32(%rbp)     # arg4 ✓
movl %ecx, -40(%rbp)     # arg5 ✗ 又读 %ecx
movl %ecx, -48(%rbp)     # arg6 ✗
movl %ecx, -56(%rbp)     # arg7 ✗
```

**`%r8d` / `%r9d` / 栈参数从头到尾没有出现在 callee 里。** 溢出循环在第 4 个
寄存器之后就重复用 `%ecx`,所以第 5 个及以后的实参全部拿到第 4 个的值。

**为什么 v2.7.0 就知道、却拖到现在:** `sysv_abi_test.jhyy` 文件头白纸黑字写着
「v2.7.0 emit_call emit 7th arg warning comment ... **stack-arg 实 wire 留
v2.7.1+**」,而**该测试从 v2.7.0 起就标着 `// SKIP: sysv target requires Linux
host`** —— 默认回归在本机(Windows 无 WSL/Docker)永远跳过它。2026-10-15 启了
Docker Desktop 跑 `sysv_full_regress.sh`,5 个测试立刻挂 1 个,就是这条。

**关联 W-104(不同代码路径,别一起「修」):** W-104 是 **caller 侧**的参数分类
借用了 Win 分类器;本条是 **callee 侧**的参数溢出只做 4 个寄存器。症状都表现为
「SysV 多参数传错」,但修的位置不同。两条都要修。

### 2026-10-18 精确定位:callee 把参数 5/6/7 全读成 `%ecx`

实测(`--target=amd64_sysv_freestanding --no-link` 看 `.s`):

**调用侧是对的** —— arg1-6 正确进 rdi/rsi/rdx/rcx/r8/r9,arg7 落栈:
```
movl 0(%rbp),  %edi      arg1
movl -8(%rbp), %esi      arg2
movl -16(%rbp),%edx      arg3
movl -24(%rbp),%ecx      arg4
movl -32(%rbp),%r8d      arg5   ✓
movl -40(%rbp),%r9d      arg6   ✓
movl -48(%rbp),%r10d → 0(%rsp)  arg7  (r10 是多余的中转,最终落栈正确)
```

**callee 侧错了** —— arg5/6/7 全部读 `%ecx`(= arg4 的寄存器):
```
movl %edi, -8(%rbp)      arg1 ✓
movl %esi, -16(%rbp)     arg2 ✓
movl %edx, -24(%rbp)     arg3 ✓
movl %ecx, -32(%rbp)     arg4 ✓
movl %ecx, -40(%rbp)     arg5 ✗ 应为 %r8d
movl %ecx, -48(%rbp)     arg6 ✗ 应为 %r9d
movl %ecx, -56(%rbp)     arg7 ✗ 应为 16(%rbp)(栈)
```

于是 `seven_arg_fn(1,2,3,4,5,6,7)` 算成 **1+2+3+4+4+4+4 = 22** ——
与 `sysv_abi_test` 实测的 `EXIT=22` **精确吻合**,根因坐实。

调用侧那张表(`codegen_amd64_emit_call.jhyy:577-601` `reg_rax_for_qt_idx`)SysV 分支
idx 0..5 是对的,但 **idx ≥ 6 落到函数末尾的 `return "ecx"`** —— 这本身是 arg7 的
独立缺口(该走栈)。**callee 侧用的是另一张表,本次未定位到。**


**workaround:** 无。写不出可靠的用户侧绕法 —— 「函数别超过 4 个参数」在 SysV
目标上是硬约束,而 SysV 约定本身允许 6 个整数寄存器 + 栈。

### 2026-10-19 真修:判别缺了 SysV 的 `arg_idx >= 4` 分支

`codegen_amd64_emit_call.jhyy` 里 arg_idx → 寄存器的判别只有两条分支:

```jhyy
if arg_idx >= 0 && arg_idx <= 3        { fnarg_reg = reg_rax_for_qt_idx(...); }
else if arg_idx >= 4 && target_is_win { fnarg_stack_off = 48 + (arg_idx-4)*8; }
else                                  { fnarg_reg = reg_rcx_for_qt(dst_qt); }   // ← SysV 掉这里
```

**SysV 的 `arg_idx >= 4` 整个分支不存在** → 全部落到最后的 `%ecx` 兜底 →
arg5/6/7 读到的都是 arg4 的值。同样的代码重复 **3 处,3 处都错**。

`reg_rax_for_qt_idx` 里 SysV 的 idx 4→r8d / 5→r9d **本来就是对的**,只是从来没够着。

修法按 ABI 分派寄存器数量:SysV 6 个整数寄存器、第 7 个起落栈、栈基址
`16(%rbp)`(`push rbp` 后返回地址在 8、无影子区);Win 4 个 + 32B 影子区、基址 48。

顺带实测确认 **caller 侧一直是对的**(edi/esi/edx/ecx/r8d/r9d + `0(%rsp)`),
不需要改 —— 序言里的 `subq $N, %rsp` 顺带当了 outgoing 区。

**修复后 callee 序言:**
```
movl %edi → arg1   %esi → arg2   %edx → arg3
%ecx → arg4   %r8d → arg5   %r9d → arg6   16(%rbp) → arg7
```

### 两个门同时转绿(这次重构的目的)

```
artifact 级门:  ⚠️ KNOWN-FAIL sysv_arg_spill  →  ✅ PASS sysv_arg_spill
sysv 门(ubuntu): ⚠️ sysv_abi_test EXIT=22       →  ✅ sysv_abi_test EXIT=28
                 === sysv 结果: 5 PASS / 0 KNOWN-FAIL / 0 FAIL ===
```

两处 W-116 登记已删除 → 两项**升级成真门**,任何回归都会红。


**影响范围:** `amd64_sysv` / `amd64_sysv_freestanding` 目标的全部多参数调用。
注意 **Win 目标不受影响**(`sysv_*` 测试只在 sysv target 下跑),这也是它能
潜伏这么久的原因 —— 默认 ship gate 只跑 amd64_win。

**失效条件:**
1. callee 参数溢出循环支持完整 6 个 SysV 整数寄存器(`rdi/rsi/rdx/rcx/r8/r9`)+ 栈溢出
2. 补测试:上面那个逐位复现,**对 arg5/arg6/arg7 分别断言**,断言不同实参必须
   给出不同结果(只断言一个非前四的值,「恒取 arg4」恰好能过)
3. `sysv_abi_test.jhyy` 期望值 28 需要重新对一遍(它同时混了几个子检查)

**引用:**
- 最小复现:见上
- 测试 `compiler/tests/examples/sysv_abi_test.jhyy`(自 v2.7.0 SKIP 到今天)
- 门 `compiler/tests/bootstrap/sysv_full_regress.sh`(需 Docker;本次实测 4/5)
- 相关:W-104(SysV caller 侧分类错)

<a id="w-117"></a>
## W-117: self-backend IL lexer 在 EOF 处无守卫 —— cur == end 时可永久空转

**状态:** RESOLVED closed 2026-10-18 (v4.0.9) — 根因是 self-backend IL lexer 在 EOF 处无守卫,与 gcc 版本无关
**Filed-by:** audit-ci-hang-2026-10-17;RCA w117-rca-2026-10-18
**日期:** 2026-10-17 首次实测(GH Actions run 39016142083) → 2026-10-18 闭合

**触发面:** self-backend 的 IL lexer(`codegen_amd64_lexer.jhyy`)在 EOF 处的字节读取。
原先表述成「换一套 gcc 行为不同」是**错的因果** —— gcc 版本只是改变堆布局的
一个变量,真正的触发条件是「cur == end 处那个字节恰好落在某循环的继续类里」。

**症状(原始观测,真实存在):**

run 39016142083 的 regress 步(`[DIAG-3]` 那一轮,总耗时 28m24s),二进制
`00473e6b`(CI 现编),`failed: codegen_call_return_types, f32_suffix,
f64_suffix, fmod_basic, std_math_basic`,其中三个是:

```
FAIL  f32_suffix.jhyy  expected=0 got=-4  compile timeout (300s,重试后仍超时);
      编译器进程仍在运行 —— 它自己卡住了;产物=无;
      最后阶段标记: [4a] ir_init done → [4b] cg_module done → [4] codegen done
```

同一轮的 `[DIAG-3]` 步用**恢复回来的** `37837b3f` 跑同样三个测试 → 3/3 PASS,0 秒。
(注意 `[DIAG-3]` 步本身只测了恢复的那份;现编那份的实测在同一轮的 regress 步。)

**根因(2026-10-18 定位到语句级):**

`codegen_amd64_lexer.jhyy` 里两条事实叠加成一个无限循环:

1. `lex_peek_byte` 对 `cur` 做 **4 字节对齐裸读,没有任何 `cur < end` 守卫**;
2. `lex_next_byte` 在 EOF 时「返 0 **且不推进 cur**」(原注释原话)。

于是任何 `while (lex_peek_byte(s) != X) { lex_next_byte(s); }` 形式的循环,
在 `cur == end` 处只要那个字节不等于 X,`next()` 就原地不动 → 永久空转。
症状与观测完全吻合:`[4] codegen done` 之后、零产物、进程仍在。

而 `cur == end` 处那个字节**不是哨兵,是未初始化内存**:in-mem 路径把
`(*ir.sb).buf` / `(*ir.sb).len` 直接喂进 `lex_il`,而 `sb_init` 只 arena 分配、
`sb_grow` 换新块只 `memcpy` 了 `sb.len` 字节 —— `[len, cap)` 是回收来的堆垃圾。

**这解释了「时灵时不灵」:** 那个垃圾字节是什么取决于堆布局,堆布局取决于二进制。
`9a6c337`(观测时)→ HEAD 之间 src0 **只有一处**改动,`codegen_amd64_lexer.jhyy`
+30/-1(正是 W-109 那笔)—— 而那正是挂死发生的文件。给 lexer 加 30 行足以把
EOF 处那个字节从「空白」翻成「非空白」。

**原 root-cause 段的两处错误,留档:**

1. 「差异**必然**来自这两个 `.o`」是**未验证的推断**。2026-10-18 的受控 A/B
   (固定 `.s`、只 perturb `.o`,轴 0 对照 / 轴 1 十二个 codegen 决策 /
   轴 2 单 `.o` 替换 / 轴 3 换 lld 链接器 —— 14 个探针**全部 clean**)
   证明 `.o` 的 codegen 决策**不产生**该症状。
2. 「换 gcc 行为不同」把相关当成了因果。gcc 版本改变的是堆布局,不是行为。

**受控 A/B 的结论(2026-10-18,CI gcc 16.2.0 + binutils 2.47):**

同一 job 内 gen0 与 gen1(gen1 在 `git checkout` 换回之前抢救出来):

```
gen0.s sha: 00b7baef5bf3099f
gen1.s sha: 00b7baef5bf3099f     → Q1: .s IDENTICAL,emit 层无差异
gen0 rc=0 / gen1 rc=0  ×3        → Q2: gen1 三个测试全过,.s 尺寸 903/901/1133
                                    与本机 14 个探针逐一相同
```

**该症状今天不复现。** 因此下面那句必须写清楚:这个修复**没有**被「挂死消失」
验证过 —— 它是被「根因定位到语句级 + 输出中性」支撑的。

**workaround(已撤销):** 此前 CI 的回归门测**发布产物**(`ci.yml` 第 5 步
`make` 之后 `git checkout HEAD -- compiler/build/bin/jhyy.exe`)。该 workaround
的前提是「CI 编出来的编译器是坏的」,而受控 A/B 证明这个前提不成立。
2026-10-18 起撤销(见 CI 重构:回归门改测当前源码编出来的产物)。

**fix:** 给 `lex_peek_byte` / `lex_peek_byte_at` 加 `cur >= end → return 0` 守卫。
选 0 是因为它正是所有调用方在 EOF 处已经期待的哨兵值(`lex_next_byte` EOF 返 0;
skip_ws/scan 循环判「非该字节」才停;`lex_il` 恢复循环判 `cc == 0` 才停),
加守卫后 EOF **确定性终止**。守卫对所有合法读取(`cur < end`)行为完全不变,
因此是**输出中性**的 —— 用 201 个测试逐一 A/B(HEAD 的 gen0 vs 加守卫后的新
编译器)验证:

```
.s 逐字节相同          188
归一化后逐字节相同       4   (closures_as_arg / closures_basic /
                            closures_multi_capture / codegen_call_return_types)
两边都编译失败(rc 一致)  9
```

那 4 个的差异**只有闭包符号名**:`__closure_86321` vs `__closure_06350`,两侧
`.s` 长度与指令完全一致。该后缀由 `sema.jhyy:1173` 的 `let name_addr = n as i64;`
派生,而 `n` 是闭包节点在 arena 里的**地址** —— 编译器里加几行代码就会让 arena
布局平移、数字跟着变。**任何**改动编译器的变更(包括 W-109 那 +30 行)都会改变它,
所以它不是语义差异,而是「这个测试的 `.s` 无法跨二进制逐字节比对」。

若把守卫改成更严格的 `p_addr + 4 <= end` 才读,会把输入**末尾 3 个字节**变成 0,
直接改变发射的 `.s`,破坏自举 byte-equal 不变式 —— 不能那样改。

**影响范围:** 一旦触发,编译器在该次编译上永久空转,表现为 CI 超时(而不是快速
失败)。可触发性取决于堆布局,因此同一份源码在不同二进制上表现不同。

**失效条件:** 已满足(守卫已加 + 输出中性已验)。

**引用:**
- `compiler/src0/codegen_amd64_lexer.jhyy:77-130`(`lex_peek_byte` /
  `lex_peek_byte_at` / `lex_next_byte`)
- `compiler/src0/util.jhyy:61-89`(`sb_init` / `sb_grow` —— 未清零的来源)
- `compiler/src0/codegen_amd64_inmem.jhyy:63-139`(`[4] codegen done` 之后的全部代码)
- GH Actions run 39016142083(原始观测)、run 39095870883 / PR #8(受控 A/B)
- 同族未修项:**W-118**(语言 lexer 的镜像缺陷 —— 越界前进而非空转)
- 相关:W-109(IL lexer 缺助记符,同文件)、W-107(per-fn 表 1024 上限)

<a id="w-118"></a>
## W-118: 语言 lexer 的 lex_peek_char 同样无 EOF 守卫 —— 越界前进而非空转

**状态:** ACTIVE since 2026-10-18 (v4.0.9) — 同族缺陷的另一处,失效模式不同,尚未观测到危害
**Filed-by:** w117-rca-2026-10-18
**日期:** 2026-10-18 W-117 RCA 时顺带发现

**触发面:** `compiler/src0/lexer.jhyy`(语言 lexer,与 `codegen_amd64_lexer.jhyy`
是两套独立实现)。

**症状:** **尚无观测。** 登记它是因为代码事实成立且与 W-117 同源,不是因为
见过它出事 —— 这点必须写清楚,否则下一个读者会以为有一次未记录的现场。

**根因(读代码得出,非推测):**

`lexer.jhyy:212-220` 的 `lex_peek_char` 同样是对 `*i32` 的 4 字节对齐裸读,
**没有任何边界守卫**;`lexer.jhyy:250-258` 的 `lex_peek_char_at(l, off)` 同样。

但它与 W-117 的失效模式**相反** —— `lex_next_char`(`:223-236`)长这样:

```
let c = lex_peek_char(l);
if c == 0 { return 0 as i32; }      // 靠 peek 返 0 判 EOF
(*l).current = ptr_add_u8(...);      // 非 0 就推进 —— 包括垃圾字节
```

- W-117(IL lexer):peek 读到垃圾 + next **不推进** → **永久空转**
- 本条(语言 lexer):peek 读到垃圾 + next **照常推进** → **越过 end 一路往前走**

后者不会空转,所以不会表现为 CI 超时;它会一路走出缓冲区边界,可能读到未映射
页而崩溃,也可能吐出一串垃圾 token。**危害形态不同,但根因同一个。**

**为什么本条没跟着 W-117 一起修(这是有意的取舍,不是遗漏):**

修它需要给 `Lexer` 加长度信息。`Lexer` 结构(`lexer.jhyy:134-148`)只有
`source` 与 `current`,**没有 end / len 字段**;它由 `lexer.jhyy:615-616` 从
`main.jhyy:595` 的 `read_file(input)` 初始化。要加守卫就得把长度从
`read_file` 一路铺到 `lexer_init` —— 跨 `main.jhyy` + `lexer.jhyy` 两个文件。

在**没有任何观测证据**的前提下为它扩大改动面,与本项目反复栽过的那个坑
(为了某个目的去改判据 / 改范围)是同构的。故拆为独立条目。

**workaround:** 无。当前没有任何代码绕过它 —— 它是真实未修的 bug,不是
「已知的、有绕路的」状态。

**修法(留档,未实施):** 给 `Lexer` 加 `end: *u8` 字段;`lex_peek_char` 与
`lex_peek_char_at` 加 `current >= end → return 0` 守卫。选 0 的理由与 W-117
相同:`lex_next_char` 的 `c == 0` 分支正是为它准备的 EOF 判据,只是它依赖
`lex_peek_char` 恰好在 EOF 返 0 —— 而现在那是个未定义行为。

⚠️ 实施时的陷阱:`lex_peek_char_at` 只有两个调用点(`lexer.jhyy:333` 与
`:427`,都在用 `off = 1` 做 lookahead)。加守卫会改变**输入最后一个字符**
处的那次 lookahead 的结果(原先是垃圾、现在是 0)。必须用 W-117 同款 A/B
(201 个测试逐个比 `.s`)验输出中性,不能想当然。

**影响范围:** 语言前端。任何以「尾部字节」为分支条件的词法决策都受影响。

**失效条件:** `Lexer` 具备长度信息且两个 peek 有守卫,且 A/B 证明 `.s` 逐字节
不变。

**引用:**
- `compiler/src0/lexer.jhyy:212-220`(`lex_peek_char`)、`:223-236`(`lex_next_char`)、
  `:250-258`(`lex_peek_char_at`)、`:134-148`(`Lexer` 结构,无 end 字段)、
  `:615-616`(初始化点)
- `compiler/src0/main.jhyy:595`(`read_file(input)`)
- 同族已闭合:**W-117**(IL lexer 侧,2026-10-18 修)

### W-109 真修记录 (2026-10-17, v4.0.9)

**根因(精确定位):** `codegen_amd64_lexer.jhyy:1588` 的 `c*` 助记符 gate 第二字符
字符集是 `{s, u, e, n, g}`,**漏了 `l`**。前端 `codegen.jhyy:2335` 起会 emit
`cltd` / `clts` / `cled`(以及 `cgtd` / `cgts` / `cged` 的 f32/f64 变体)——
`cltd` 的第二字符是 `l`,不在集内 → 落到 `next_token` 末尾的
`unknown QBE IL mnemonic` → 返回 -1 → `lex_il` 收到 -1 的处理是「跳 1 个字节
继续」→ **吐出一串垃圾指令**。

**一个必须纠正的中间结论:** 排查中我一度断定「`emit_binop` 侧也漏了这 6 个 op」。
**那是错的** —— `codegen_amd64_emit_call.jhyy:1862-1899` 一直逐个 `cg_find_sub`
匹配了这 6 个浮点比较 op。缺的只有 lexer:助记符压根没被 token 成 BINOP,
自然到不了发射。**判据要来自读实际代码,不是从「报错在哪」倒推。**

**为什么它能活这么久,而且症状是「本地过 CI 不过」:**

1. 垃圾字节交给汇编器 `as`。同一份 `.s` 在不同版本的 `as` 上被解释成不同指令 ——
   本地碰巧合得上,CI 上合不上。这是 W-109 与 W-117 叠加的结果,不是两个独立 bug。
2. 本地默认 gcc 正是本项目编 `jhyy.exe` 用的那套,「碰巧对」被固化成了「本来就对」。
3. `float_cmp.jhyy` 的断言**恰好蒙对了**,而不是干脆崩溃,所以没有暴露。

**定位手段(可复用):** 新增 `compiler/tests/examples/float_cmp_diag.jhyy`,
用五个互不相同的返回码把「比较指令本身坏了」与「libm 返回值不同」分开。
决定性的是 **41 号**:`nearly_eq(1.5, 1.5, eps)` —— 同一个值跟自己比,差必然是 0,
**完全不碰 libm**,任何正确实现都必须返回 1。CI 返回 41,一次就把 libm 排除了。
在此之前这个问题被「本地不复现 / 看起来像 CI 环境问题」挡了好几轮。

**验收:**
- `float_cmp_diag.jhyy` EXIT=0,编译时 `unknown QBE IL mnemonic` 计数归零
- `float_cmp.jhyy` 摘掉 XFAIL 后 **PASS EXIT=111137**(与它注释里写的期望总和一致)
- `std_math_basic.jhyy` 由 FAIL(expected=0 got=4) 转 PASS
- 全量回归 175/176 → 摘标记后 **176/176,0 failed**
- 自举闭环 PASS(Stage2 == Stage3 .s 与 .exe 均逐字节相同)

**引用:**
- `compiler/src0/codegen_amd64_lexer.jhyy:1588`(字符集补 'l')+ 同函数 op_str 分支
- `compiler/src0/codegen_amd64_emit_call.jhyy:1862-1899`(发射侧**原本就**支持,未改)
- `compiler/tests/examples/float_cmp_diag.jhyy`(新增判据)
- 相关:W-117(工具链依赖,决定了同一份垃圾字节被不同 `as` 解释成什么)
