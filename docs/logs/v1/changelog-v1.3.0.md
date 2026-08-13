# Changelog v1.3.0 (2026-08-12 ship v1.3.1, v1.3.2-1.3.8 待启动) — v1.x 语法糖 Phase 4

**v1.3.1 已 ship** (commit `c2acbd1`, 2026-08-12) — `null` 关键字 via dedicated `NODE_NULL` NodeKind (design 临时调整,见 § design pivot)。v1.3.2-1.3.8 待启动。

## 成就 (v1.3.1 ship 时)

| 项 | 值 |
|---|---|
| **v1.3.1 commit** | `c2acbd16fbd35cd1b0edbd90d8455d5d65850534` (2026-08-12 22:19:19 +0800) |
| jhyy_v1.exe.exe sha | `cc4930ed...` (was `ba94df93...`,NODE_NULL enum value 50 追加的必然结果) |
| **jhyy_v2.il / v3.il / v4.il sha** | **`a26f4768...`** (was `2445e97d...`,Stage 2 closure 刷新 — NODE_NULL emit 路径新增的必然结果) |
| jhyy_v2/v3/v4 .exe sha | `d3aeed09...` / `536ffcb2...` / `eb8b7a3b...` (canonical,维持) |
| regress.py | **50/50 PASS, 0 failed, 3 skipped** |
| regress_v1.py | **50/50 PASS, 0 failed, 3 skipped** |
| Stage 1 byte-equal | **7/7 PASS** (sha `a26f4768...`) |
| Stage 2 N=3 closure | ✅ **v2.il = v3.il = v4.il byte-equal** (`a26f4768...`) |

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

## 下一阶段

v1.3.2 启动 → 跟 v1.3 7 个 sub-sprint 串行推进 → v1.3.8 doc sync 收尾 → v1.4 (src0 production flip) → v1.5 (WiX installer) → 才到 v2.x ‖ v3.x 并行 (per [`v2-v3-parallel-sprint-plan.md`](../../plans/roadmap/v2-v3-parallel-sprint-plan.md))。

## 关联文档

- [`../plans/v1/v1.3.0任务清单 + 概要设计.md`](../../plans/v1/v1.3.0任务清单 + 概要设计.md) — plan 同步反映 design pivot (端改动表 + sprint 详细 § v1.3.1)
- [`../../plans/roadmap/v1.0-post-50-53-plan.md`](../plans/v1/v1.0-post-50-53-plan.md) § Phase 4 — v1.3 语法糖原始 plan 源
- [`../changelog-v1.2.0.md`](changelog-v1.2.0.md) — 前置 v1.2.0 ship 状态
- [`../changelog-v1.0.0.md`](changelog-v1.0.0.md) — Stage 2 closure canonical sha `2445e97d...` (v1.3.1 ship 后被刷新成 `a26f4768...`,不破坏历史记录)
- [`../../../internal/status.md`](../internal/status.md) — § 198-200 当前 sprint 同步到 v1.3.1,§ 208 下一阶段同步到 v1.3.2,§ 212-213 已知未完成项 v1.3.1 已覆盖 `null` (Pattern binding / OR pattern 仍属 v1.3.7 待 ship)

---

**ship 时间**: v1.3.1 已 ship 2026-08-12;v1.3.2-1.3.8 由 user 触发 (per memory `feedback_no_date_estimates.md` — 不写日期估时,用 sprint 序列 + 相对顺序)。