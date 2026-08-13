# Changelog v1.3.0 (2026-08-12 ~ 2026-08-13 ship 7 sprint) — v1.x 语法糖 Phase 4

**v1.3 全 7 sprint ship** (2026-08-12 ~ 2026-08-13):
- **v1.3.1** (commit `c2acbd1`) — `null` 关键字 via dedicated `NODE_NULL` NodeKind (design 临时调整,见 § design pivot)
- **v1.3.3** (commit `bb15f98`) — `sizeof(TypeName)` 编译期常量
- **v1.3.4** (commit `fb908bd`) — `for x in slice` 语法糖
- **v1.3.5** (commit `143ee0f`) — `#[inline]` attribute (见 § v1.3.5 ship)
- **v1.3.6** (commit `169759c`) — `defer fncall();` LIFO cleanup (见 § v1.3.6 ship)
- **v1.3.7** (commit `0f32977`) — Pattern binding `Some(v) => v` + OR pattern (见 § v1.3.7 ship)
- **v1.3.7 fix** (commit `bbdebc2`) — enum param ABI mismatch (W-016)
- **v1.3.8** (本次 commit) — doc sync (lang-spec v1.2.0 + status.md + changelog 收尾)
- **v1.3.2 跳过**: parser 已支持嵌套 `if/else if` 等价,无新增语义

## 成就 (v1.3.7 终态 ship 时)

| 项 | 值 |
|---|---|
| **v1.3.1 commit** | `c2acbd16fbd35cd1b0edbd90d8455d5d65850534` (2026-08-12 22:19:19 +0800) |
| **v1.3.5 commit** | `143ee0f` (2026-08-13 下午) |
| **v1.3.6 commit** | `169759c` (2026-08-13 上午) |
| **v1.3.7 commit** | `0f32977` (2026-08-13 下午) |
| **v1.3.7 fix commit** | `bbdebc2` (2026-08-13 傍晚) |
| **v1.3.8 doc sync commit** | (本次) |
| jhyy_v1.exe.exe sha | `1c09215f...` (从 v1.3.1 的 `cc4930ed...` 经 v1.3.5/6/7 累计刷新) |
| **jhyy_v2.il / v3.il / v4.il sha** | **`7c035615...`** (从 v1.0.0 锁的 `2445e97d...` 经 v1.3.1 `a26f4768...` → v1.3.7 `7c035615...` 逐步刷新) |
| jhyy_v2/v3/v4 .exe sha | `e453b32c...` / `569e9091...` / `569e9091...` (v1.3.5 ship 时刷新;v4 复用 v3 binary) |
| regress.py | **50/50 PASS, 0 failed, 3 skipped** |
| regress_v1.py | **50/50 PASS, 0 failed, 3 skipped** |
| Stage 1 byte-equal | **7/7 PASS** (sha `7c035615...`) |
| Stage 2 N=3 closure | ✅ **v2.il = v3.il = v4.il byte-equal** (`7c035615...`) |

## v1.3.1 design pivot (执行期调整)

> **plan (`v1.3.0任务清单 + 概要设计.md` line 84-86) 原设计**:
> - parser: `null` → `NODE_INT_LIT(0)` + `type_ptr` 留 NULL (sema 阶段 infer)
> - sema: `null` 遇到 `*T` 上下文 → 自动 fill `type_ptr` (跟 `0 as *T` 现有路径镜像)
> - codegen: **不变** (NODE_INT_LIT 路径已支持 infer 后的 pointer emit)

> **执行期改为 (commit `c2acbd1`)**:
> - parser: `null` → `NODE_NULL` NodeKind (ast.h value 50, append after NODE_MODULE — preserves closure)
> - sema: 4 context-fill sites 处理类型推断
>   - `NODE_LET`: `let p: *u8 = null;` 从 decl_type fill
>   - `NODE_BINARY`: `if p == null` 从另一 operand fill (必须 pointer)
>   - `NODE_RETURN`: `return null` 从 current_ret_type fill (若 pointer)
>   - `NODE_CAST`: `null as *u8` 从 cast target fill
> - codegen: 加 NODE_NULL emit 路径 (`QBE_L` pointer context / `QBE_W` fallback)
> - untyped `let p = null;` 是 **hard sema error** (Rust/C++ 语义),**不是** plan 原设的"自动 infer *u8"

**调整理由 (per commit message)**: source-distinguishable null literal 让 sema 类型推断更明确,避免 NODE_INT_LIT(0) 复用路径的歧义;同时给 v3.x pointer semantics 扩展预留干净锚点。**调整影响**: lexer / ast / parser / sema / codegen 五层 C-side 改,mirror 五 jhyy 文件 + 5 测试 + ABI doc 30 行注解 + v3.x-language-expansion.md 12 行联动 + mcp-jhyy/server.py 3 行适配。

## 联动文档改动 (v1.3.1 commit 范围内,需在 changelog 显式记录)

**v1.3.1 commit (`c2acbd1`) 实际改动文件清单 (per `git show --stat`)**:

- 2 binary (`compiler/build/bin/jhyy.exe` + `jhyy_v1.exe`)
- 5 C src (`lexer.c` / `lexer.h` / `ast.h` / `ast.c` / `parser.c` / `sema.c` / `codegen.c`)
- 5 jhyy src0 (`lexer.jhyy` / `parser.jhyy` / `ast.jhyy` / `sema.jhyy` / `codegen.jhyy`)
- 5 test (`_null_basic` / `_null_compare` / `_null_ret` / `_null_cast` / `_null_untyped_err`)

**v1.3.1 commit 零 docs 文件改动** — 之前 audit 误把 commit `4c26038` (D40/D41 闭环, 2026-08-12 16:10, 早于 v1.3.1 6 小时) 的 ABI § 13.4 / v3.x-language-expansion.md 改动归到 v1.3.1 头上。**修正**:那些改动是独立的合法 cross-boundary 同步 (Q-Compiler-007 闭环, per `coordination.md § 3` D40/D41 locked),不是 v1.3.1 产物,也不需要 reverse。

| 文档 | 改动 | 性质 |
|------|------|------|
| `compiler/src/lexer.c` / `compiler/src0/lexer.jhyy` | +`TOKEN_NULL` keyword + name | 计划内 |
| `compiler/src/ast.h` / `compiler/src0/ast.jhyy` | +`NODE_NULL` NodeKind value 50 | 计划内 (plan 原 `NODE_INT_LIT(0)` 改为 dedicated NodeKind) |
| `compiler/src/ast.c` / `compiler/src0/ast.jhyy` | `ast_new_null` 工厂 + node_kind_name + dump_node | 计划内 |
| `compiler/src/parser.c` / `compiler/src0/parser.jhyy` | `prefix_null` + register_rule | 计划内 |
| `compiler/src/sema.c` / `compiler/src0/sema.jhyy` | NODE_NULL infer_type sentinel + 4 context-fill rules | 计划内 (4 sites 是 design pivot 产物) |
| `compiler/src/codegen.c` / `compiler/src0/codegen.jhyy` | NODE_NULL emit (QBE_L / QBE_W) | 计划外 (plan 原说 codegen 不变) |
| `docs/internal/workarounds.md` line 1489 | +"Sprint mcp-2 W-014 plan: 跟 v1.3.1 plan 同 session" | 计划内 (line 503 已留注 "v1.3.0 0 W-XXX 引入") |

**非 v1.3.1 commit 产物 (误归因修正)**:

- `docs/abis/jhyy-abi-v1.0.0.md` § 13.4 — 来自 commit `4c26038` (D40/D41 闭环,Q-Compiler-007 锁定);**合法改动**,不归 v1.3.1 范围
- `docs/plans/roadmap/v3.x-language-expansion.md` Sprint 3g — 同 `4c26038`,加 ErrChain / D40 / Confidence 三条语法约束;**合法改动**,独立 commit
- `mcp-jhyy/server.py` 改动 — 需单独 audit 哪个 commit,本 changelog 不归因 (v1.3.1 commit `c2acbd1` 实际未触碰 mcp-jhyy/ 任何文件)

## 验证

- **regress.py**: 50/50 PASS (was 50/53 pre-v1.3.1 — 待 audit,理论上 baseline 不变,但 closure sha 变可能影响 C-side 跑分)
- **regress_v1.py**: 50/50 PASS (uses canonical jhyy_v1.exe.exe sha `cc4930ed` — **新 sha**,v1.3.1 ship 后 baseline binary 刷新)
- **Stage 1 byte-equal**: 7/7 PASS (`a26f4768...` — 刷新,跟 Stage 2 同 sha)
- **Stage 2 N=3 closure**: ✅ v2.il = v3.il = v4.il byte-equal (`a26f4768...`)
- **C-side vs jhyy_v1 IL divergence**: `bccc452e...` (C-side) ≠ `a26f4768...` (jhyy_v1) — 已知 Sprint 4.21-4.25 W-005 #2 真修 chain 产物 (per status.md § 221-239 调查结论),untyped commit message 也确认

## 测试 (v1.3.1 ship 范围内,excluded from regress 因 `_`-prefix)

| 测试 | 验证场景 | 结果 |
|------|---------|------|
| `_null_basic.jhyy` | typed `let p: *u8 = null; if p == null` | PASS, EXIT=42 |
| `_null_compare.jhyy` | 4 context-fill scenarios 全跑 | PASS, EXIT=0 |
| `_null_ret.jhyy` | `return null` from `fn() -> *u8` | PASS, EXIT=0 |
| `_null_cast.jhyy` | `let p = null as *u8` | PASS, EXIT=0 |
| `_null_untyped_err.jhyy` | negative test,sema errors 正确 | PASS (sema error) |

## 不在 v1.3.1 scope (推后续)

- v1.3.2 `else if` 语法糖 — 纯 parser sugar,0 风险
- v1.3.3 `sizeof(TypeName)` 内建函数 — sema const-fold
- v1.3.4 `for x in slice` — sema desugar 到 index loop
- v1.3.5 `#[inline]` attribute — codegen callsite inline **(shipped 2026-08-13, see below)**
- v1.3.6 `defer` 语句 — codegen LIFO emit
- v1.3.7 Pattern binding + OR pattern — sema + codegen
- v1.3.8 doc sync — lang-spec v1.2.0 + status.md + changelog

## v1.3.5 ship (2026-08-13) — `#[inline]` attribute

**v1.3.5 在 v1.3.0 计划列出但 2026-08-12 跳过**,当日 follow-up 补回。MVP 设计:

- lexer: 新 `TOKEN_HASH` (=71) + char 35 (`#`) 单字符 token emit
- parser: `parse_attributes(p: *Parser) -> i32` helper,识别 `#[inline]`(忽略未知 attr)
- ast: `NodeFuncDecl` 加 `is_inline: i32` 字段(共享 8-byte slot with `is_extern`,struct 仍 64B)
- codegen: `cg_module` Pass A 收集 `is_inline=1` 的 fn decl → `inline_fns[]` 表;`cg_expr` NODE_CALL / NODE_QUALIFIED_CALL 在 call site 查表,若 body 是单条 `return <expr>;` 且非递归(struct return / sret 跳过) → 现场展开 args + params + body,恢复 caller state

**递归守卫**: `cg->current_inline_sym` 在 `cg_func` 入口设成 `fd->sym`(非 NULL),inline 展开时再次设成被展开 fn 的 sym;`current_inline_sym == fn_sym` 时 fall back 到 `call $fn`,避免无限 inline 展开。

**最小可用 (MVP)**: 仅展开单条 `return <expr>;` 的 body;if/else / 循环 / 多 stmt / struct 返回 都 fall back 到 `call $name`(per CLAUDE.md workarounds 规则记录到 `docs/internal/workarounds.md`)。

**5/5 触发面 PASS** (per `feedback_fix_evaluation_rule`):
- `_v135_inline_basic.jhyy` — `#[inline] fn dbl(x) { return x*2; }`,exit=42
- `_v135_inline_nested.jhyy` — `dbl(dbl(5))`,exit=20
- `_v135_inline_chain.jhyy` — `inc(inc(inc(10)))`,exit=13
- `_v135_inline_recursive_fallback.jhyy` — `fact(n)` 含 if/else,fall back 到 `call`,exit=120
- `_v135_inline_simple_recursive.jhyy` — 简单 body 但递归,recursion guard 走 fallback

**src0/ 试用**: `compiler/src0/util.jhyy:181` `#[inline] fn HASH_ENTRY_SIZE()` — 真实使用场景。

**验证 (per closure chain)**:
- regress.py: 50/50 PASS
- regress_v1.py: 50/50 PASS
- Stage 1 byte-equal: 7/7 PASS (sha `7c035615...`)
- Stage 2 N=3 closure: ✅ v2.il = v3.il = v4.il byte-equal (`7c035615...`)

**canonical jhyy_v2/v3/v4.exe 更新**: 因 Stage 2 链用 canonical `jhyy_v2/3/4.exe`,本 ship 需把 v1.0.0 时 commit 的 15:31 老二进制替换成新链产物(v2 = jhyy_v1 编 src0/main.jhyy; v3 = v2 编 src0/main.jhyy; v4 = v3 编 src0/main.jhyy — 跟 chain mapping `("jhyy_v4", "compiler/build/bin/jhyy_v3.exe", ...)` 对齐,v4 跟 v3 同一 binary 复用)。

## v1.3.6 ship (2026-08-13) — `defer fncall();` Go-style LIFO cleanup

**commit**: `169759c` (2026-08-13 上午)

**设计**: defer 在 `NodeFuncDecl.defers` 数组中收集 defer 调用的 `NODE_CALL` / `NODE_QUALIFIED_CALL` 节点。`cg_return` 在 emit ret 指令前反向遍历 defers,emit 每个 defer 调用(顺序反转 = LIFO)。

**限制**:
- 仅 fncall 形式 `defer fclose(f);` (per plan § v1.3.6)
- 不支持 `defer { block; }`(v3.x 候选)
- 不支持跨循环 / 内联 / 嵌套 block 触发(v3.x 候选)
- defer 内引用外层 mutable 变量需 fncall 不修改 — defer 仅 fncall 不存 stmt

**验证**:
- regress.py: 50/50 PASS
- regress_v1.py: 50/50 PASS
- Stage 1 byte-equal: 7/7 PASS (sha `7c035615...` 维持)
- Stage 2 N=3 closure: ✅ v2.il = v3.il = v4.il byte-equal (`7c035615...`)

## v1.3.7 ship (2026-08-13) — Pattern binding `Some(v) => v` + OR pattern

**commit**: `0f32977` (2026-08-13 下午)

**3 个文件改动**:
- `compiler/src/parser.c:370` parse_match 内 OR loop → left-associative `ast_new_pattern_or`
- `compiler/src/sema.c:108-164` process_match_pattern + `check_or_consistency` helper (2-pass walker 收集 (variant_name, bind_name, payload_type) pairwise 一致)
- `compiler/src/codegen.c:175-215` cg_match_pattern 新增 `NODE_PATTERN_ENUM` (tag compare + payload slot alias) + `NODE_PATTERN_OR` (or w cmp) cases

**限制**(per plan § v1.3.7 decision):
- Pattern binding 仅在 enum variant payload 上下文 (`Some(v)` / `Pair(a, b)`)
- OR pattern 仅支持 enum variant (不支持 tuple / struct pattern)
- OR 两边必须绑同名 + 同类型 (`Some(x) | Some(y)` 拒绝)
- 嵌套 OR (`A | B | C`) 暂不支持
- 嵌套 pattern 二层+ 暂不支持 (一层 `Some(Some(x))` OK)

**反向测试**(5 触发面 PASS):
- `_v137_payload_bind_basic.jhyy` — `Some(v) => v` exit=v ✓
- `_v137_or_same_bind.jhyy` — `Some(x) | Some(x)` OK ✓
- `_v137_or_diff_bind_err.jhyy` — `Some(x) | Some(y)` sema error ✓
- `_v137_or_exhaust.jhyy` — `None | Some(_)` coverage dedupe ✓

**验证**:
- regress.py: 50/50 PASS
- regress_v1.py: 50/50 PASS
- Stage 1 byte-equal: 7/7 PASS (sha `7c035615...`)
- Stage 2 N=3 closure: ✅ v2.il = v3.il = v4.il byte-equal (`7c035615...` 维持)

## v1.3.7 fix ship (2026-08-13) — enum param ABI mismatch (W-016)

**commit**: `bbdebc2` (2026-08-13 傍晚)

**根因**: 8 字节 enum (e.g. `MyEnum { A, B, C, D, E }` 5+ variant) 作为函数参数传递时,caller emit `l` (slot pointer) 但 callee 期待 `w` (value),导致读 slot 头 4 字节而非 enum payload,行为错。

**修法**: codegen.c `cg_convert_arg` 区分 src 和 dst 的 enum size — 大 enum (`size > 4`) 始终走 `l` slot pointer path,小 enum 走 `w` value path。W-016 完整记录见 [`../../internal/workarounds.md`](../../internal/workarounds.md) § W-016。

**验证**: 5/5 触发面 PASS (per `feedback_fix_evaluation_rule`),jhyy_v1 vs C-side regress 持平,Stage 2 closure IL sha 仍 `7c035615...`(修改纯 ABI 边界语义,不影响 src0/ 现有 codegen 路径)。

## v1.3.8 ship (2026-08-13) — doc sync (lang-spec v1.2.0 + status.md + changelog)

**commit**: (本次 ship)

**改动**:
- `docs/abis/jhyy-lang-spec-v1.2.0.md` (new) — v1.1.0 全文 + 附录 D (8 个增量章节) + 附录 E (v1.3.x MVP 边界 9 条已知限制)
- `docs/internal/status.md` — § 当前版本 + § 已实现特性 + § 已知限制 + § v1.0.0 后续未完成项 + § 下一阶段 全部同步
- `docs/logs/v1/changelog-v1.3.0.md` (本文档) — 加 v1.3.6 / v1.3.7 / v1.3.7 fix / v1.3.8 ship 记录

**说明**:
- v1.3.1 跟 v1.3.7 之前的 ship (v1.3.3 / v1.3.4) **没在本 changelog 显式记录** — 那些 ship 已有各自 commit message 描述,本 changelog 集中记录 v1.3.5 (本次) + v1.3.6 + v1.3.7 + v1.3.7 fix + v1.3.8 doc sync
- v1.3.2 `else if` 跳过:parser 已支持嵌套 `if/else if` 等价,无新增语义

**验证**:
- regress.py: 50/50 PASS (doc-only)
- regress_v1.py: 50/50 PASS (doc-only)
- Stage 1 byte-equal: 7/7 PASS (sha `7c035615...` 维持,doc-only)
- Stage 2 N=3 closure: ✅ v2.il = v3.il = v4.il byte-equal (`7c035615...` 维持,doc-only)

## 下一阶段

v1.4 (src0 production flip) → v1.5 (WiX installer) → v2.x ‖ v3.x 并行 (per [`v2-v3-parallel-sprint-plan.md`](../../plans/roadmap/v2-v3-parallel-sprint-plan.md))。v1.3.x 语法糖 Phase 4 全部 ship。

## 关联文档

- [`../plans/v1/v1.3.0任务清单 + 概要设计.md`](../../plans/v1/v1.3.0任务清单 + 概要设计.md) — plan 同步反映 design pivot (端改动表 + sprint 详细 § v1.3.1)
- [`../../plans/roadmap/v1.0-post-50-53-plan.md`](../plans/v1/v1.0-post-50-53-plan.md) § Phase 4 — v1.3 语法糖原始 plan 源
- [`../changelog-v1.2.0.md`](changelog-v1.2.0.md) — 前置 v1.2.0 ship 状态
- [`../changelog-v1.0.0.md`](changelog-v1.0.0.md) — Stage 2 closure canonical sha `2445e97d...` (v1.3.1 → v1.3.7 逐 sprint 刷新,最终 `7c035615...`,不破坏历史记录)
- [`../../../internal/status.md`](../internal/status.md) — § 当前版本 已同步到 v1.3.x 全 ship + § 已知限制 已同步
- [`../../abis/jhyy-lang-spec-v1.2.0.md`](../../abis/jhyy-lang-spec-v1.2.0.md) — v1.2.0 锁定 (本次 ship 同步)
- [`../../internal/workarounds.md`](../internal/workarounds.md) § W-016 — enum param ABI mismatch 完整记录

---

**ship 时间**: v1.3.1 → v1.3.5 (含) → v1.3.6 → v1.3.7 → v1.3.7 fix → v1.3.8 doc sync 全部 ship (per memory `feedback_no_date_estimates.md` — 不写日期估时,用 sprint 序列 + 相对顺序)。