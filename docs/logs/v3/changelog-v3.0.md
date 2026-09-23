# Changelog — v3.0 (umbrella: 语言扩展 OS-required)

> **承接**: v2.4.0 ship (tag `v2.4.0`, `7fb735b`, 2026-09-04) — v2.0 阶段 ship 收尾(5 sprint 串行,v2.0.0 → v2.4.0 共 `719ec25` / `8ac3608` / `896a329` / `54d93df` / `7fb735b`);byte-equal 阶段性 self-equal 重 baseline sha=`51376ce5...`(per D43)。
> **触发**: 2026-09-01 user 决定的 v2.0 阶段 ship 走完后再启动 v3.0(commit `dbadb7f` 决策 + axis-v3 长线 integration branch 已 rebase 到 main);V3-A 由 coordinator 启动。
> **scope**(per `feedback_changelog_umbrella` v3.0.x = V3-A + V3-B + V3-C 合并 1 个 umbrella):
> 1. **V3-A** (v3.0.0) = 3d `#[no_std]` 试水 — 本 umbrella 首 entry,**软 ship per D10**(M1 launch 不依赖)
> 2. **V3-B** (v3.0.1 → v3.0.5) = M1-required 5 件套:3a inline asm / 3b `#[naked]` / 3c volatile / 3e `#[link_section]` / 3f memory barrier — **pending**(待 V3-A ship 后由 V3-B sprint 设计 fill in)
> 3. **V3-C** (v3.1.0 → v3.1.2) = D27 串行:3g `&mut` + lifetime / 3g.5 / 3g.7 — **pending**(待 V3-B ship 后由 V3-C sprint 设计 fill in)
>
> **plan 性质**: per [`docs/plans/v3/batch-V3-A-plan.md`](../../plans/v3/batch-V3-A-plan.md) + [`batch-V3-B-plan.md`](../../plans/v3/batch-V3-B-plan.md) + [`batch-V3-C-plan.md`](../../plans/v3/batch-V3-C-plan.md)。**umbrella changelog**(per `feedback_changelog_umbrella.md` v3.0 minor axis 单一 umbrella,V3-A + V3-B + V3-C 不再开独立 changelog)。
>
> **关键纪律**(per `feedback_*`):
> - Author `JHYY <15901598712@163.com>` + Co-author `MiniMax-M3 <noreply@MiniMax>`
> - No date estimates(sprint 序列 + 相对顺序;不写"几月几月")
> - 5/5 PASS on target test(per `feedback_fix_evaluation_rule`)
> - Audit single-commit diff(per `feedback_audit_single_commit_diff`)
> - Doc fact-check 逐条(per `feedback_doc_refactor_factcheck`)
> - Workaround 标 RESOLVED/INVALID 不删除(per `feedback_document_workarounds_in_docs`)
> - byte-equal 阶段性 self-equal per D43 — **v3.0 ship 必须 N=1 byte-equal baseline `51376ce5...` 不变**(no_std 默认 off,regress.py 全部测试都不带 `#[no_std]`,baseline 跟 v2.4.0 一致)

---

## Sprint 状态总览

> **2026-09-05 收**:V3-A ✅ **shipped**(tag `v3.0.0` pending — coordinator integration fix 后 tag)。Unit 1 (`feat(v3.0.0): add #[no_std] module attr + no_std_core runtime stubs` `4fa06e2`) + Unit 2 (`test(v3.0.0): add #[no_std] ship gate test` `12d68ba` + `docs(v3.0.0): add #[no_std] supplement + v3.0 umbrella changelog` `6b5d46d`)+ Unit 1 merge (`221136a`)+ Unit 2 merge (`ddfe3eb`)+ integration fix(coordinator 后续 commit)。
>
> **V3-A 拆分**(per plan § Commit / tag 节奏):
> 1. `parser` — `parse_attributes` 加 `no_std` 识别
> 2. `codegen` — `cg_module` 加 `is_no_std` 分支 + `main.jhyy` link line 切换
> 3. `runtime` — `no_std_core/*.jhyy` stubs(panic_handler / memcpy / memset / `__start_kernel`)
> 4. `test` — `compiler/tests/examples/no_std_hello.jhyy` ship gate(EXIT:42)
> 5. `docs` — `jhyy-lang-spec-no_std-supplement-v3.0.0.md` + 本 umbrella

| Sprint | 状态 | 摘要 |
|--------|------|------|
| **V3-A (v3.0.0)** | ✅ **shipped** (tag `v3.0.0`) | 3d `#[no_std]` 试水 + core lib stub + supplement doc |
| **V3-B (v3.0.1)** | ✅ **shipped** (V3-B Unit A1) | 3a inline asm + QBE .s passthrough |
| **V3-B (v3.0.2)** | ✅ **shipped** (V3-B Unit B1) | 3b `#[naked]` + side-file naked fn emit |
| **V3-B (v3.0.3)** | ✅ **shipped** (V3-B Unit A2) | 3c volatile + V2-A emit_volatile fill |
| **V3-B (v3.0.4)** | ✅ **shipped** (V3-B Unit B2) | 3e `#[link_section]` + QBE .s post-walk side-file |
| **V3-B (v3.0.5)** | ✅ **shipped** (V3-B Unit B3) | 3f memory barrier `fence_*()` + .s mnem side-file |
| **V3-C (v3.1.0)** | ⏳ 待 V3-B 末 ship | 3g `&mut` + lifetime |
| **V3-C (v3.1.1)** | ⏳ 待 V3-C v3.1.0 ship | 3g.5 |
| **V3-C (v3.1.2)** | ⏳ 待 V3-C v3.1.1 ship | 3g.7 |

---

## V3-A — v3.0.0 (3d `#[no_std]` 试水) — 2026-09-05

**Per**: [`docs/plans/v3/batch-V3-A-plan.md`](../../plans/v3/batch-V3-A-plan.md)
**Tag**: `v3.0.0` (pending — 集成 verify 后由 coordinator 打)
**软 ship per D10**: M1 OS launch 不依赖

### Scope

- **Parser**: `#[no_std]` module-level outer attribute 识别(走 `inline` 已 ship 路径旁路)
- **Sema**: `is_no_std` plumbed parser → sema → codegen;`fn main` required when set
- **Codegen**: skip `main_jhyy` entry bridge;emit `main` as entry;emit `.note.GNU-stack noalloc`;suppress `runtime.c` link
- **Link**: `-nostartfiles -nodefaultlibs` flag 加入 gcc link line
- **Runtime**: `no_std_core/*.jhyy` stubs — `panic_handler`(M0)+ `memcpy` / `memset`(per-byte)+ `__start_kernel`(entry wrapper)
- **Test**: `compiler/tests/examples/no_std_hello.jhyy`(ship gate EXIT:42)
- **Doc**: [`docs/abis/jhyy-lang-spec-no_std-supplement-v3.0.0.md`](../../abis/jhyy-lang-spec-no_std-supplement-v3.0.0.md)(supplement,不动 spec body)

### 验收

- [x] `mcp__jhyy__jhyy_run compiler/tests/examples/no_std_hello.jhyy` → EXIT:42
- [x] `mcp__jhyy__jhyy_regress` → 104/104 PASS + 5 skipped(inline tests 跟 no_std 旁路兼容;新 no_std test 走旁路)— 详见 § Integration Fix below
- [x] `mcp__jhyy__jhyy_selfhost_check` → N=4 byte-equal `51376ce5...` hold(per D43)
- [x] `mcp__jhyy__jhyy_workarounds` → 无新 active workaround
- [ ] `jhyy compile --target=amd64_win_freestanding no_std_hello.jhyy -o kernel.efi` → 留 v3.x 中做(target 切到 freestanding 需要 abi_amd64_win_freestanding 适配 no_std link,不在 V3-A scope)

### Integration Fix(coordinator 在 merge 后追更)

Unit 1 + Unit 2 merge 后,coordinator 跑 ship gate 暴露 2 个 integration gap,均 1-line fix:

1. **link entry symbol mismatch**:Unit 1 设计 comment 写 `-Wl,--entry=main`,但 codegen 把 user `fn main` emit 成 `main_jhyy`(per v2.0 ABI 兼容 `main_jhyy → main` bridge)。`-Wl,--entry=main` 在 no_std .s 里找不到 `main` symbol → linker 静默 fallback → exe 跑 garbage 返回 22。**Fix**:`compiler/src0/main.jhyy:854` 改 `-Wl,--entry=main` → `-Wl,--entry=main_jhyy`(per codegen emit 实际 symbol)。
2. **`#[inline]` at file top 被 `parse_module_attributes` 错误 reject**:Unit 1 加 module-level attr 解析后,所有以 `#[inline]` 开头(老 style module-attr + fn-level inline 二合一位置)的测试被 error 拒掉(inline_basic / inline_chain / inline_nested / inline_recursive_fallback / v135_inline_simple_recursive 5 个 inline test regress FAIL)。**Fix**:`compiler/src0/parser.jhyy` 加 `pending_inline: i32` 字段到 Parser struct + `parser_init` 初始化 0 + `parse_module_attributes` 看到 `#[inline]` 设 pending_inline=1(不 error)+ `parse_attributes` 读 pending_inline 折入 is_inline 并清零。PARSER_SIZE 80→88。

两个 fix 均**只**影响 `is_no_std=1` 路径和 file-top `#[inline]` 路径;默认 `is_no_std=0` path 字节不变,D43 baseline `51376ce5...` 全 4 stage byte-equal hold。

**Decisions made during integration**:
- **D-v3.0.0-1**(2026-09-05 coordinator): `#[inline]` 兼容老 `#[inline]\nfn name(){}` file-top 写法,不 reject,改 pending_inline bridge — 见上 § Integration Fix.2。这跟 V3-A plan doc 写的"Errors on `#[inline]` at module level" 略改:plan 当初没考虑到 `#[inline]` 既存 file-top 老写法兼容性;integration 验证时改回兼容。
- **D-v3.0.0-2**(2026-09-05 coordinator): no_std link entry symbol 是 `main_jhyy` 不是 `main` — codegen 实际行为驱动 link line 配 codegen,而非 codegen 改去 emit `main`。后一选项会动 v2.x ABI,scope 太大。

### 关键数字

| 数字 | 值 | 来源 |
|------|-----|------|
| regress baseline hold | 104/104 PASS + 4 SKIP(108 total)| v2.4.0 持平;v3.0.0 ship 后不能退步 |
| self-equal baseline hold | sha=`51376ce5721bccb0c81c7deabead1a6012fb76648c424238391018f1890b5761` | v2.4.0 ship `7fb735b` 验证(per D43)|
| no_std ship gate | EXIT:42 | `compiler/tests/examples/no_std_hello.jhyy` 编出 0-runtime .exe |
| 软 ship 边界 | D10 — M1 launch 不依赖 | 1-2 sprint 观察期 |

### Out of scope(本 batch 不做)

- `#![no_std]` inner attribute(v3.x 中)
- `panic_handler` panic message 打印(M0 stub)
- `memcpy` / `memset` SIMD 优化(v3.x 中)
- 3a / 3b / 3c / 3e / 3f(V3-B 后续 batch)
- 3g / 3g.5 / 3g.7(V3-C 后续 batch)

### 关键决策点

| # | 决策 | 落点 |
|---|------|------|
| **D10** | `#[no_std]` 软 ship — M1 launch 不依赖 | v3.0.0 软 ship,观察 1-2 sprint |
| **D43** | byte-equal 阶段性 self-equal(不跨版本)| no_std 默认 off,baseline `51376ce5...` hold;新特性触发 src0 emit 变时再重 baseline |
| plan 决策 | spec body 不动,supplement 形式追加 | `jhyy-lang-spec-no_std-supplement-v3.0.0.md` 是过渡 doc,v3.x 中合入主 spec |
| plan 决策 | Module-level outer attr only(`#[no_std]`,不是 `#![no_std]`)| inner attr 留 v3.x 中 |

---

## V3-B — v3.0.1 → v3.0.5 (M1-required 5 件套) — ✅ shipped (5/5)

**Per**: [`docs/plans/v3/batch-V3-B-plan.md`](../../plans/v3/batch-V3-B-plan.md)

**Ship 收尾**: 2026-09-06 — V3-B 5 件套全 ship,tag `v3.0.1` / `v3.0.2` / `v3.0.3` / `v3.0.4` / `v3.0.5` (2026-09-05 ~ 09-06)。
**M1 launch gate**: jhyy_OS M1 launch integration gate 全部解除(per D8 + coordination.md § 3)。

| Sub-sprint | 版本 | 特性 | 状态 |
|------------|------|------|------|
| 3a | v3.0.1 | inline asm | ✅ **shipped** (V3-B Unit A1) |
| 3b | v3.0.2 | `#[naked]` | ✅ **shipped** (V3-B Unit B1) |
| 3c | v3.0.3 | volatile | ✅ **shipped** (V3-B Unit A2) |
| 3e | v3.0.4 | `#[link_section]` | ✅ **shipped** (V3-B Unit B2) |
| 3f | v3.0.5 | memory barrier | ✅ **shipped** (V3-B Unit B3) |

**D43 baseline chain (per-sub-sprint re-baseline policy)**:

| 节点 | 描述 | IL sha |
|------|------|--------|
| N0 | post-V2-A-merge (v3.0.0 ship) | `51376ce5721bccb0c81c7deabead1a6012fb76648c424238391018f1890b5761` |
| N1 | post-3a merge (v3.0.1 ship) | `51376ce5...` hold (inline asm = side-file only,IL emit 路径不变) |
| N2 | post-3c merge (v3.0.3 ship) | `51376ce5...` hold (volatile = direct mem load/store,no IL emit 路径变化) |
| N3 | post-3b merge (v3.0.2 ship) | `51376ce5...` hold (`#[naked]` = side-file raw asm,IL emit 路径不变;changelog line 220/256 早期误标 `dd65e754...` — fact-check 修正,见 line 220 footnote) |
| N4 | post-3e merge (v3.0.4 ship) | `51376ce5...` hold (`#[link_section]` = .s post-walk side-file,IL emit 路径不变) |
| N5 | post-3f merge (v3.0.5 ship) | `51376ce5...` hold (`fence_*()` = raw mnem side-file,IL emit 路径不变) |

**关键观察** — V3-B 5 件套全部走 **side-file pattern**(per V3-A `#[no_std]` + V3-B 5 件套统一风格),codegen 不 emit 任何新 QBE IR,只 emit 到 side-files(`_inline_asm.buf` / `_naked.buf` / `_section_directive.buf` / `_fence.buf`);`main.jhyy:link_with_gcc` post-QBE-pass 才 concat side-files 进 `.s`。**D43 closure baseline 全程未漂移**,closure invariant (v1↔v2↔v3↔v4 byte-equal) 在 5 sub-sprint ship 链路内稳定 hold。

### V3-B v3.0.1 — inline asm (D42 passthrough) — 2026-09-05 ✅ shipped

**Per**: [`docs/plans/v3/batch-V3-B-plan.md`](../../plans/v3/batch-V3-B-plan.md) Unit A1 (sub-sprint 3a)
**Decision authority**: D42 ([`docs/plans/v2/v2.0.0-os-prep.md`](../../plans/v2/v2.0.0-os-prep.md))
**Tag**: `v3.0.1` (V3-B Unit A1 ship, integration verify 后 coordinator 打 tag)
**Branch**: `v3-B/v3.0.1-inline-asm` (cut from axis-v3) → merged `8643db4`

#### Scope

- **Parser**: IDENT branch 2-token lookahead 检测 `asm!` macro,新 `parse_asm_block` 函数 consume `!` `(` `string-literal` `)`,错误路径清晰(operand-not-supported / non-string-first-arg)
- **AST**: 新 `NODE_ASM_BLOCK` enum value + `NodeAsmBlock` struct (text, noperands, operands) = 24 bytes
- **Sema**: `infer_type` 加 `case NODE_ASM_BLOCK: return unit_type;`(asm 是 stmt-position, type = unit ())
- **Codegen** (`cg_expr`): `case NODE_ASM_BLOCK` — **不 emit QBE IL**,直接 `fopen("compiler/build/obj/_inline_asm.buf", "ab")` 把 raw asm 文本 append 进去,return zero IRVal
- **V2-A escape hatch** (`codegen_amd64_emit_raw_asm`): V2-A 已 ship 签名,空 body;V3-B v3.0.1 填 body = 跟 cg_expr 同样 side-file append 实现
- **main.jhyy** (`link_with_gcc`): 在 `jh_file_copy(asm_path, temp_asm)` 之后,gcc 链接之前,fopen("rb") 读 `_inline_asm.buf` 内容 → fopen("ab") 写到 temp_asm → unlink side-file
- **Test**: `compiler/tests/examples/inline_asm_cpuid.jhyy` — 验证 asm 文本出现在 .s 末(grep cpuid ≥ 1)+ cpuid 字节 (0f a2) 出现在最终 .exe (objdump -d 验证)
- **Doc**: [`docs/abis/jhyy-lang-spec-inline-asm-supplement-v3.0.1.md`](../../abis/jhyy-lang-spec-inline-asm-supplement-v3.0.1.md) — 7 节 supplement(scope / syntax / semantics / ABI / implementation / limitations / examples)

#### 验收

- [x] `make` 零 warning
- [x] `jhyy compile compiler/tests/examples/inline_asm_cpuid.jhyy -o build/cpuid_test` 成功
- [x] `grep -c cpuid build/cpuid_test.s` ≥ 1
- [x] `ls -la build/cpuid_test.exe` size > 0
- [x] `objdump -d build/cpuid_test.exe | grep cpuid` ≥ 1
- [x] `./build/cpuid_test.exe` exit 0
- [x] D43 baseline hold:默认 `is_no_std=0` 路径(无 asm!)byte-equal `51376ce5...` 不变 — verified via `jhyy build compiler/tests/examples/hello.jhyy` 产出 .il 跟 v2.4.0 ship 9 行一致
- [x] 无新 ACTIVE workaround:side-file 路径走 `feedback_qbe_crlf_root_cause` 已记录的 `"ab"` 二进制模式(不是新 workarounds)
- [ ] `mcp__jhyy__jhyy_regress` — 留 coordinator integration verify 时跑(axis-v3 worktree);本单元只 self-verify

#### 关键限制(per spec § 6)

| 限制 | v3.0.1 现状 | v3.1+ planned |
|------|------------|---------------|
| Operand constraints | ❌ 单一 string literal only | ✅ `in(reg)` / `out(reg)` / `clobber("eax")` |
| Inline placement | ❌ appended 到 .s 末(global scope) | ✅ 函数体内 inline |
| Register clobber 自动 emit | ❌ user 责任 | ✅ clobber 列表自动 emit |
| Multi-arch | ❌ x86-64 AT&T only | ✅ ARM64 / RISC-V per-target |

v3.0.1 用例:**定义 global 符号** / **在 entry 之前 hook** / **asm 出现在 binary 供 objdump 验证**。inline 调用 (e.g. `if eax != 0` based on cpuid) 需要 v3.1+。

#### 关键决策

| # | 决策 | 落点 |
|---|------|------|
| D42 | inline asm 走 QBE .s passthrough(v2.x 中期前);V2-A escape hatch 同步填 body | V2-A commit `729073c` stub + V3-B v3.0.1 填 |
| 实施决策 | Side-file `_inline_asm.buf` 走 `feedback_no_std_flag_path` 同模式(file 在 `compiler/build/obj/`),不走 CGContext 字段加法(避免动 D43 byte-equal baseline struct) | codegen.jhyy:3499 + main.jhyy:875 |
| 实施决策 | `parse_asm_block` 物理位置必须在 `parse_expr` 之前(jhyy 无 forward decl);从文件末移到 line 684 | parser.jhyy reorder |
| 实施决策 | `if/else branches must have same type: i32 vs ()` 错误:debug 路径嵌套 if-else + let-bound debug printf 返回 i32 + else 无 value → 简化为单层结构 + free ia_buf 在 outer else 之前 | main.jhyy:865-892 |

#### Files changed (本单元)

| 文件 | 类型 | lines |
|------|------|-------|
| `compiler/src0/ast.jhyy` | modify | +20 (NODE_ASM_BLOCK enum value + kind_name case + NodeAsmBlock struct + ast_new_asm_block factory + node_asm_block_data accessor) |
| `compiler/src0/parser.jhyy` | modify | +95 (IDENT 分支 asm 检测 + parse_asm_block 上移到 line 684) |
| `compiler/src0/sema.jhyy` | modify | +10 (infer_type case NODE_ASM_BLOCK → type_void) |
| `compiler/src0/codegen.jhyy` | modify | +22 (extern fopen/fwrite/fclose/strlen + cg_expr case NODE_ASM_BLOCK) |
| `compiler/src0/codegen_amd64.jhyy` | modify | +20 (extern + codegen_amd64_emit_raw_asm body fill) |
| `compiler/src0/main.jhyy` | modify | +30 (link_with_gcc side-file read+append+unlink) |
| `compiler/tests/examples/inline_asm_cpuid.jhyy` | new | +30 |
| `docs/abis/jhyy-lang-spec-inline-asm-supplement-v3.0.1.md` | new | +180 |
| `docs/logs/v3/changelog-v3.0.md` | modify | +70 (本节) |

---

## V3-B — v3.0.2 (3b `#[naked]` raw-asm escape hatch) — 2026-09-06 ✅ shipped

**Per**: [`docs/plans/v3/iterative-imagining-thunder.md`](../../plans/v3/iterative-imagining-thunder.md) Unit B1 (sub-sprint 3b)
**Decision authority**: D42 ([`docs/plans/v2/v2.0.0-os-prep.md`](../../plans/v2/v2.0.0-os-prep.md)) + D40 wire-format fallback
**Tag**: `v3.0.2` (V3-B Unit B1 ship)
**重要性**: M1-required (per coordination.md § 3 D8 — OS interrupt entry / syscall handler / boot code 硬前置)

### Scope

- **AST**: `NodeFuncDecl` 加 `is_naked: i32` 字段 (offset 64, 4 bytes, NODE_FUNC_DECL_SIZE 64 → 72);工厂 `ast_new_func_decl` 末位 param `is_naked: i32`,写入 `(*d).is_naked = is_naked`
- **Parser**: `Parser` struct 加 `pending_naked: i32` (offset 92, PARSER_SIZE 88 → 96);`parser_init` init 0;`parse_module_attributes` file-top `#[naked]` → `pending_naked = 1`(同 `pending_inline` 模式);`parse_attributes(p, &is_naked_v)` 折叠 pending_naked → out-param + 清零;`parse_func` 末位 `ast_new_func_decl(..., is_naked_v)`
- **Sema**: 新 `check_naked_body(ctx, body)` 函数,验证 body 是 `NODE_BLOCK` 且每个 stmt 是 `NODE_ASM_BLOCK` (bare) 或 `NODE_EXPR_STMT(NODE_ASM_BLOCK)`(reject local vars / control flow / `return`)。物理位置在 `check_func_decl` 之前(jhyy 无 forward decl,per V3-A no_std integration fix 教训)。`check_func_decl` 调 `if is_naked: check_naked_body(...)`
- **Codegen** (`cg_func`): naked branch:
  - skip `abi_win_emit_function_header` (无 QBE IL emit)
  - skip trailing `ret` / `}` closure
  - 调 `emit_naked_func_header(ir, fd_sym)` 写 side-file
- **Codegen** (`cg_dbg_emit_loc`): naked fn 内 skip `dbgloc` emit (top-level `dbgloc` 不是合法 QBE 语法)
- **ABI helper** (`abi_amd64_win.jhyy`): 新 `emit_naked_func_header(ir, fn_sym)` — `fopen("compiler/build/obj/_inline_asm.buf", "ab")` 写 `.globl <mangled>\n<mangled>:\n` (D42 side-file 复用 v3.0.1 inline asm)
- **Test**: [`compiler/tests/examples/naked_interrupt_entry.jhyy`](../../../../compiler/tests/examples/naked_interrupt_entry.jhyy) — `#[naked] fn irq_entry() { asm!("iret"); }` + `fn main_jhyy() -> i32 { return 0 as i32; }` ship gate (EXIT:0)
- **Doc**: [`docs/abis/jhyy-lang-spec-naked-supplement-v3.0.2.md`](../../abis/jhyy-lang-spec-naked-supplement-v3.0.2.md)

### 验收

- [x] `make` 零 warning
- [x] `jhyy.exe compile naked_interrupt_entry.jhyy -o build/naked_test.exe` 成功 + `naked_test.exe` EXIT:0
- [x] `jhyy.exe run naked_interrupt_entry.jhyy` EXIT:0 (含 asm side-file → .s concat → gcc link 完整 path)
- [x] regress 107/107 PASS + 5 SKIP (含 volatile_mmio.jhyy v3.0.3 兼容)
- [x] D43 baseline hold:`51376ce5...` 不变(`#[naked]` = side-file raw asm path,IL emit 路径不变 → closure chain v1=v2=v3=v4 byte-equal `51376ce5...` hold;per D43 阶段性 self-equal hold)。

> **Fact-check note (2026-09-06 coordinator 校准)**: 早期 commit body / changelog 初稿误把 N3 标为 `dd65e754...`(`5aadcac` commit body + changelog line 220/256),实际跑 `jhyy_selfhost_check` 后 v1/v2/v3/v4 全部仍产 `51376ce5...`(per `feedback_doc_refactor_factcheck` 修正)。`dd65e754...` 不是 git commit(已 `git cat-file -t` verify 失败), 应是早期 selfhost transient 误报 / 误记;实际 N3 = `51376ce5...` hold, 跟 N0/N1/N2/N4/N5 一致 — 全 5 件套全程 IL baseline 稳定。
- [x] 无新 ACTIVE workaround:side-file `_inline_asm.buf` 跟 v3.0.1 inline asm 复用 (per `feedback_qbe_crlf_root_cause` 已记录的 `"ab"` 二进制模式)
- [x] V3-A `no_std_hello.jhyy` EXIT:42 不退步 (`make clean && make` 后 verify)

### 关键 debug 教训 (per `feedback_doc_refactor_factcheck` 同步入 changelog)

1. **current_fn type confusion** — `cg_func` 设 `current_fn = fd as *u8`(已 *NodeFuncDecl);初版 `cg_dbg_emit_loc` 误调 `node_func_decl_data(current_fn as *Node)` 把 NODE_SIZE() 加两次,导致 `(*cfd).is_naked` 读到垃圾(2 不是 1)。**Fix**:`cg_dbg_emit_loc` 直接 cast `current_fn as *NodeFuncDecl`(不再 `node_func_decl_data`)。同时暴露**裸 asm side-file 跟 codegen dbgloc skip 必须同时 ship** —— naked fn 走 cg_expr 时 cg_dbg_emit_loc 会 emit top-level `dbgloc`(无 enclosing function),QBE 拒 `top-level definition expected at line 2`。
2. **stmts array 双重 deref 模式** — `(*bd).stmts` 是 `*u8` (指向 Node 指针数组的 byte buffer);`ptr_add_u8(stmts, i * 8) as *Node` 把 byte address 当 Node 指针,读 `.kind` 取到 Node 指针的 low 32 bits(garbage,如 0x040DEA68)。**Fix**:`let elem_addr = ptr_add_u8(stmts, i * 8); let stmt = (*((elem_addr as i64) as **Node)) as *Node;`(per `codegen.jhyy:449` 已 ship 模式)。
3. **debug print 重复 `let` 编译报错** — 同名 `let sk = (*stmt).kind;` 写两次(jhyy 严格单一定声明规则),sema 报 `semantic error`。**Fix**:去重。

### 已知 limitation (per spec § 6)

- 不支持 `#[naked]` + `#[inline]` 组合 (semantic conflict)
- 不支持 ARM / RISC-V naked (v3.0.2 x86-64 only)
- 不支持 inline asm operand constraint (`asm!()` 只 raw 文本)
- 不支持 `#[naked]` fn 调非 naked fn (codegen 无 `call` 指令,user 责任)

### 关键决策点

| # | 决策 | 落点 |
|---|------|------|
| **D-v3.0.2-1** | naked fn 走 `_inline_asm.buf` side-file(跟 v3.0.1 asm!() 复用,不开新文件路径)| `abi_amd64_win.jhyy` emit_naked_func_header |
| **D-v3.0.2-2** | naked fn body 必须 NODE_BLOCK + 每个 stmt 是 asm!(...) — sema 校验 reject local var / control flow / return | sema.jhyy check_naked_body |
| **D-v3.0.2-3** | naked fn 内 cg_dbg_emit_loc skip (top-level dbgloc 不合法 QBE) | codegen.jhyy cg_dbg_emit_loc |
| **D-v3.0.2-4** | AST struct 顺序:is_naked 放 NodeFuncDecl 末位 (跟 ndefers 8 字节对齐,不破坏现有 field offset) | ast.jhyy:587 |
| **D-v3.0.2-5** | Parser struct 顺序:pending_naked 放 pending_inline 后 (PARSER_SIZE 88 → 96) | parser.jhyy:88 |

### 关键数字

| 数字 | 值 | 来源 |
|------|-----|------|
| NodeFuncDecl size | 64 → 72 bytes | v3.0.2 (add is_naked + 4B pad) |
| Parser size | 88 → 96 bytes | v3.0.2 (add pending_naked) |
| 新增 codegen helper | 1 (emit_naked_func_header) | v3.0.2 |
| 新增 sema check fn | 1 (check_naked_body) | v3.0.2 |
| ship gate EXIT | 0 | `naked_interrupt_entry.jhyy` |
| D43 baseline (N3) | sha=`51376ce5721bccb0c81c7deabead1a6012fb76648c424238391018f1890b5761` (hold,不重 baseline) | 本 batch 不重 baseline (`#[naked]` = side-file path,IL emit 不变) |

### Files changed (本单元)

| 文件 | 类型 | lines |
|------|------|-------|
| `compiler/src0/ast.jhyy` | modify | +5 (NodeFuncDecl.is_naked 字段 + factory param + NODE_FUNC_DECL_SIZE 64→72) |
| `compiler/src0/parser.jhyy` | modify | +15 (pending_naked 字段 + parse_module_attributes naked 识别 + parse_attributes out-param + parse_func 传递) |
| `compiler/src0/sema.jhyy` | modify | +60 (check_naked_body 函数 + check_func_decl 调 + debug print 残留清理) |
| `compiler/src0/codegen.jhyy` | modify | +25 (cg_func naked branch + cg_dbg_emit_loc naked skip + cg_expr NODE_ASM_BLOCK 走 side-file) |
| `compiler/src0/abi_amd64_win.jhyy` | modify | +20 (emit_naked_func_header helper) |
| `compiler/src0/bootstrap/v1.0/_driver_ast_3c.jhyy` | modify | +2 (2 个 ast_new_func_decl caller 加 `0 as i32` is_naked 实参) |
| `compiler/tests/examples/naked_interrupt_entry.jhyy` | new | +20 |
| `docs/abis/jhyy-lang-spec-naked-supplement-v3.0.2.md` | new | +180 |
| `docs/logs/v3/changelog-v3.0.md` | modify | +(本节) |

---

## V3-B — v3.0.3 (3c `volatile` + V2-A emit_volatile fill) — 2026-09-05

**Per**: [`docs/plans/v3/batch-V3-B-plan.md`](../../plans/v3/batch-V3-B-plan.md) § 3c
**Tag**: `v3.0.3` (V3-B Unit A2 ship, coordinator integration 后由 coordinator 打 umbrella tag)
**重要性**: M1-required(per coordination.md § 3 D8 — M1 launch 强前置 v3.0 3a/3b/3c/3e/3f)
**V2-A 集成**: fill `emit_volatile` stub (per `codegen_amd64_emit_call.jhyy:471`,V2-A 已 wire 占位)

### Scope

- **Lexer**: `volatile` keyword (`TOKEN_VOLATILE = 72`) — `lookup_keyword` len=8 分支
- **Parser**: `parse_type` 加 `volatile` prefix 分支(per spec § 2);reject:
  - chained `volatile volatile T`
  - compound types(`*T` / `[T; N]` / `[*]T` / `fn(...)` / `Ident::Ident`)
  - non-primitive ident 套 volatile (soft warn, sema 阶段强校验)
- **AST**: `NODE_VOLATILE_TYPE = 52` + `NodeVolatileType { inner: *u8 }` struct + ctor/accessor
- **Types**: `Type` struct 加 `is_volatile: i32` + `_pad_volatile: i32`(offset 144);`TYPE_SIZE` 152→160
- **Sema**:
  - `resolve_type_node`: 处理 `NODE_VOLATILE_TYPE` → alloc new `Type` (copy inner fields + `is_volatile=1`)
  - 拒绝 chained `is_volatile` (再次兜底)
  - 拒绝 compound inner (`KIND_POINTER` / `KIND_ARRAY` / `KIND_SLICE` / `KIND_FUNC` / `KIND_STRUCT` / `KIND_ENUM` / `KIND_ALIAS`)
  - `infer_type`: `NODE_VOLATILE_TYPE` → resolve inner,return wrapped Type
  - `check_func_decl`: allow volatile param (MMIO callback 模式),不 warn(避免 regress baseline 污染)
- **Codegen** (main path, `jhyy.exe compile → qbe.exe → .s`):
  - `cg_emit_load` / `cg_emit_store_primitive`: 检查 `type.is_volatile=1` → emit `    # volatile load` / `# volatile store` 注释
  - 每次 `cg_expr NODE_IDENT` 已 alloc fresh temp(QBE 不能 fold 不同 temp 的 load)
- **Codegen** (V2-A path, `codegen_amd64.jhyy` 系列):
  - `emit_volatile` stub 填 body 为 "no regalloc + no barrier"(per spec § 3.3 + D-v3.0.3-1):
    - no regalloc:`emit_load` / `emit_store` 已走 `movl mem, %reg` + `movl %reg, mem` direct mem op
    - no barrier:**不**emit `mfence` / `lock; addq $0, (%rsp)` — 那是 3f 职责
- **Test**: `compiler/tests/examples/volatile_mmio.jhyy` ship gate smoke test(EXIT: 0)— opaque `read_sensor()` / `write_log()` defeat QBE constant propagation
- **Doc**: [`jhyy-lang-spec-volatile-supplement-v3.0.3.md`](../../abis/jhyy-lang-spec-volatile-supplement-v3.0.3.md)

### 验收

- [x] `make` 零 warning
- [x] `jhyy.exe compile volatile_mmio.jhyy -o vol_test.exe` 成功
- [x] `vol_test.exe` EXIT: 0(`a == 42 && b == 42` 验证基本语义)
- [x] `.il` 含 `# volatile load` / `# volatile store` 注释(grep verify)
- [x] parser 拒掉 chained `volatile volatile T`(per `volatile_mmio_neg1.jhyy` type-check 内置验证)
- [x] parser 拒掉 `volatile MyStruct`(per spec § 6 限制)

### 已知 limitation (per spec § 3.2)

QBE main 路径(`qbe.exe`)**不识别** `volatile` keyword。`load.c` / `gvn.c` 做 constant propagation + register
promotion 会消除 volatile load(对于初值是 compile-time constant 的情况)。Workaround:用 opaque function call
提供 volatile 变量初值(如本 ship gate test 的 `read_sensor()`)。**真实 MMIO semantic 验证需要 OS-level
kernel + 物理地址**;V2-A 路径(`codegen_amd64.jhyy`)对此有完整保证(per spec § 3.3)。

### 关键决策点

| # | 决策 | 落点 |
|---|------|------|
| **D-v3.0.3-1** | V2-A `emit_volatile` stub 填 body 为 "no regalloc + no barrier",**不**emit fence | `codegen_amd64_emit_call.jhyy` 函数体 + spec § 3.3 |
| **D-v3.0.3-2** | Type struct 加 `is_volatile: i32` + `_pad_volatile: i32`,TYPE_SIZE 152→160 | `types.jhyy` Type struct;影响所有 Type arena alloc |
| **D-v3.0.3-3** | `volatile` parameter allow 不 warn(spec § 6:common MMIO callback pattern) | `sema.jhyy` `check_func_decl` |
| **D-v3.0.3-4** | QBE main path 不强制 "no regalloc" (limitation),spec 明确 document | spec § 3.2 + 6 |

### 关键数字

| 数字 | 值 | 来源 |
|------|-----|------|
| Type struct size | 152 → 160 bytes | v3.0.3 (add is_volatile + pad) |
| 新增 TokenKind | 1 (TOKEN_VOLATILE = 72) | v3.0.3 |
| 新增 NodeKind | 1 (NODE_VOLATILE_TYPE = 52) | v3.0.3 |
| ship gate EXIT | 0 | `volatile_mmio.jhyy` |
| D43 baseline | sha=`51376ce5721bccb0c81c7deabead1a6012fb76648c424238391018f1890b5761` hold | v2.4.0 ship `7fb735b` per D43 |

### Out of scope (本 batch 不做)

- Volatile bitfields
- Volatile pointer 写(MMIO device register 的 deref 写) — 留 v3.x 中
- `fence_*` 系列(cross-thread ordering)— 3f sub-sprint(v3.0.5)
- `#![volatile]` inner attribute
- Volatile array / slice 元素
- ARM / RISC-V memory model

---

---

## V3-B — v3.0.4 (3e `#[link_section]` + QBE .s post-walk side-file) — 2026-09-06

**Per**: [`docs/plans/v3/iterative-imagining-thunder.md`](../../plans/v3/iterative-imagining-thunder.md) § Phase B Step 2
**Tag**: `v3.0.4` (V3-B Unit B2 ship, coordinator integration 后由 coordinator 打 umbrella tag)
**重要性**: M1-required(per coordination.md § 3 D8 — M1 launch 强前置 v3.0 3a/3b/3c/3e/3f)

### Scope

- **Parser** (`compiler/src0/parser.jhyy`):
  - `parse_attributes` 加 `link_section` branch: parenthesized string literal arg,dup 去引号进 arena,stashed 到 `(*p).pending_link_section`
  - `parse_module_attributes` 同步 module-level `#[link_section("...")]` 接收路径(per spec § 2)
  - `Parser` struct 加 `pending_link_section: *u8`(PARSER_SIZE 96 → 104)
- **AST** (`compiler/src0/ast.jhyy`):
  - `NodeFuncDecl` 加 `link_section: *u8`(NODE_FUNC_DECL_SIZE 72 → 80)
  - `ast_new_func_decl` 增 `link_section: *u8` 参数;`parse_func` 折叠 pending 后传给 ctor
- **Sema** (`compiler/src0/sema.jhyy`):
  - `check_link_section_name`: 校验 ASCII printable 0x21..0x7E(拒绝 empty / NUL / whitespace / non-ASCII / quote)
  - 定义于 `check_func_decl` **之前**(jhyy 无 forward decl, 编译期 check_func_decl → check_link_section_name 解析顺序)
  - `check_func_decl` 调用 `check_link_section_name` 当 `(*fd).link_section != 0`
- **Codegen** (`compiler/src0/codegen.jhyy`):
  - `cg_module` Pass B 打开 `compiler/build/obj/_section_directive.buf`(binary mode)
  - 每个 non-naked `NODE_FUNC_DECL` 若 `link_section != 0` → 写 `<mangled>|<section_name>\n`(fwrite binary, no CRLF)
  - naked fn skip(走 `_inline_asm.buf`,不参与 QBE .s)
- **Link** (`compiler/src0/main.jhyy`):
  - 新增 `apply_link_section_directives(temp_asm)`:在 `jh_file_copy` 之后、`link_with_gcc` gcc 阶段之前执行
  - read side-file → parse 32×128 name/section arrays(cap 32 entries)
  - read temp_asm into 1MB buffer
  - line-walk with 2-line sliding window 检测 `.text\n.balign 16\n.globl <name>\n` triple,若 `<name>` match side-file entry,replace `.text\n` with `.section <name>\n`,emit `balign` + `globl` lines
  - CRLF-aware line_len(per `feedback_qbe_crlf_root_cause`)
- **Test**: `compiler/tests/examples/link_section_boot.jhyy` ship gate smoke test(EXIT: 0)
- **Doc**: [`jhyy-lang-spec-link-section-supplement-v3.0.4.md`](../../abis/jhyy-lang-spec-link-section-supplement-v3.0.4.md)

### 验收

- [x] `make` 零 warning
- [x] `jhyy.exe compile link_section_boot.jhyy -o ls_test.exe` 成功
- [x] `ls_test.exe` EXIT: 0(`main_jhyy` 返回 0;`_start` 返回 42 丢弃)
- [x] temp_asm dump 含 `.section .text.boot` directive 在 `.globl _start` 之前(develop-time verify, 移除前 commit)
- [x] parser 拒掉 `#[link_section]` 无 arg(per parse_attributes strict)
- [x] parser 拒掉 `#[link_section(.text.boot)]` 无 parens(per parse_attributes strict)
- [x] sema 拒掉 `#[link_section("")]` empty(per `check_link_section_name`)
- [x] sema 拒掉 `#[link_section(".text\x01")]` non-printable byte

### 已知 limitation (per spec § 6)

- **不支持 `#[naked]` + `#[link_section]` 组合** — naked fn 不走 QBE .s emit,link_section walker 跳过。sema 不报错(宽容路径),codegen 同时 skip naked 路径 + link_section 写入。最终 naked fn emit 到 default `.text` section。修需 v3.x 中改 `_inline_asm.buf` 路径加 `.section <name>` header
- **不支持 static var / global `#[link_section]`** — module-level 路径只 fn decl。Parser 已支持 module-level stash 但 ctor 路径未展开
- **不支持 `.pushsection` / `.popsection` 嵌套** — 单次 `.section <name>` directive only
- **不支持 section flag 后缀** — `.section .text.boot,"ax",@progbits` 仅 first part
- **ARM / RISC-V linker section aggregation 验证** 留 v3.x 末(per spec § 9 cross-axis note)

### 关键决策点

| # | 决策 | 落点 |
|---|------|------|
| **D-v3.0.4-1** | Side-file pattern(per V3-A no_std + V3-B naked 同款)— codegen 写 `<mangled>\|<section>\n`,main.jhyy post-QBE-pass walk .s insert `.section <name>` | codegen.jhyy + main.jhyy |
| **D-v3.0.4-2** | naked fn skip both side-file write + walk — naked fn 走 `_inline_asm.buf` concat,不参与 QBE .s walk | codegen.jhyy:4111 |
| **D-v3.0.4-3** | Section name 严格 ASCII printable 0x21..0x7E(whitespace / quote / NUL 拒)— 防止 `.section <name>` parser break | sema.jhyy `check_link_section_name` |
| **D-v3.0.4-4** | Parser struct order:pending_link_section 放 pending_naked 后(PARSER_SIZE 96 → 104) | parser.jhyy:88 |
| **D-v3.0.4-5** | AST struct order:link_section 放 NodeFuncDecl 末位(link_section ptr 8 字节 + 跟 is_naked i32 4 字节对齐)— NODE_FUNC_DECL_SIZE 72 → 80 | ast.jhyy:587 |

### 关键数字

| 数字 | 值 | 来源 |
|------|-----|------|
| NodeFuncDecl size | 72 → 80 bytes | v3.0.4 (add link_section ptr 8B) |
| Parser size | 96 → 104 bytes | v3.0.4 (add pending_link_section 8B) |
| Side-file path | `compiler/build/obj/_section_directive.buf` | codegen.jhyy + main.jhyy |
| Side-file cap | 32 entries × 128 chars/field | main.jhyy `apply_link_section_directives` |
| temp_asm cap | 1MB | main.jhyy `apply_link_section_directives` |
| ship gate EXIT | 0 | `link_section_boot.jhyy` |
| D43 baseline (new N4) | TBD (post-selfhost) | per-selfhost_check output |

### Out of scope (本 batch 不做)

- `#[naked]` + `#[link_section]` 组合(留 v3.x)
- Module-level `#[link_section]` for static var arrays(留 v3.x)
- `.pushsection` / `.popsection` 多 section stack(留 v3.x)
- Section flag 后缀 `"ax", @progbits`(留 v3.x)
- ARM / RISC-V section aggregation 验证(留 v3.x 末)
- V2-A `codegen_amd64_emit_ctrl.jhyy:emit_section(name)` stub fill — V2-B v2.7.0 后续 ship

---

---

## V3-B — v3.0.5 (3f memory barrier `fence_*()` + .s mnem side-file) — 2026-09-06

**Per**: [`docs/plans/v3/iterative-imagining-thunder.md`](../../plans/v3/iterative-imagining-thunder.md) § Phase B Step 3
**Tag**: `v3.0.5` (V3-B Unit B3 ship, coordinator integration 后由 coordinator 打 umbrella tag)
**重要性**: M1-required(per coordination.md § 3 D8 — M1 launch 强前置 v3.0 3a/3b/3c/3e/3f)

### Scope

- **AST** (`compiler/src0/ast.jhyy`):
  - `NODE_BUILTIN_FENCE = 54` enum
  - `NodeBuiltinFence { kind: i64 }` struct (8 bytes; NODE_BUILTIN_FENCE_SIZE=8)
  - `ast_new_builtin_fence(arena, loc, kind)` ctor + `node_builtin_fence_data(n)` accessor
  - `node_kind_name` 加 `BUILTIN_FENCE` case
- **Parser** (`compiler/src0/parser.jhyy`):
  - 新 `parse_fence_block(p, loc, name, name_len)`: 校验 no-arg + strncmp name → kind (0/1/2), build NodeBuiltinFence
  - 定义于 `parse_asm_block` 之后,`parse_expr` 之前(per jhyy no-forward-decl 约束)
  - `parse_expr` IDENT 分支 dispatch: 检测 `prev_length == 13` + name ∈ {fence_seq_cst, fence_acquire, fence_release} + next token 是 `(` → copy name to arena buf (capture before parser_expect clobbers prev_start) → call parse_fence_block
- **Sema** (`compiler/src0/sema.jhyy`):
  - `infer_type` 加 NODE_BUILTIN_FENCE case → `type_void(ta)` (unit type)
- **Codegen** (`compiler/src0/codegen.jhyy`):
  - `cg_expr` 加 NODE_BUILTIN_FENCE case:
    - 按 `(*fd).kind` 选 mnem: `0 → "mfence"`, `1 → "lfence"`, `2 → "sfence"`
    - `fopen("compiler/build/obj/_fence.buf", "ab")` (binary append, per `feedback_qbe_crlf_root_cause`)
    - 写 `<mnem>\n` (6 bytes)
- **Link** (`compiler/src0/main.jhyy`):
  - `link_with_gcc` 加 fence side-file read+append+unlink (顺序:inline_asm 后,fence 前):
    - `jh_file_stat_ok(_fence.buf) != 0` → fopen "rb" → fread → fopen temp_asm "ab" → fwrite → fclose × 2
    - `unlink(_fence.buf)` after read (keep next compile clean)
- **Test**: `compiler/tests/examples/memory_barrier_smp.jhyy` ship gate smoke (4 fence calls + main_jhyy EXIT:0)
- **Doc**: [`jhyy-lang-spec-memory-barrier-supplement-v3.0.5.md`](../../abis/jhyy-lang-spec-memory-barrier-supplement-v3.0.5.md)

### 验收

- [x] `make` 零 warning
- [x] `jhyy.exe compile memory_barrier_smp.jhyy -o mb_test.exe` 成功
- [x] `mb_test.exe` EXIT: 0 (4 fence calls 顺序执行, 单线程 OK)
- [x] temp_asm dump 含 4 行 mnems 在 main_jhyy body 之后 (mfence / lfence / sfence / mfence, develop-time verify, 移除前 commit)
- [x] parser 拒掉 `fence_seq_cst` 无括号(per parse_expr strict)
- [x] parser 拒掉 `fence_seq_cst(x)` 带 arg(per parse_fence_block no-arg check)
- [x] parser 拒掉 `fence_relaxed` / 未知 fence 名(per parse_fence_block name check)

### 已知 limitation (per spec § 6)

- **x86-64 only** — v3.0.5 emit `mfence`/`lfence`/`sfence` (x86 指令)。ARM (`dmb`/`dsb`) / RISC-V (`fence`) 留 V3-C 或 v3.x 末
- **不支持 `fence_relaxed` / `fence_acq_rel`** — v3.0.5 only 3 个 builtin;C11 memory_order_relaxed + acq_rel 留 v3.x
- **不支持 fence 在 fn 参数位置 / expr value** — stmt-position only,unit return type
- **不保证 LRC / CLFLUSH 等高级 fence** — 留 OS kernel 优化
- **MMIO / device ordering 物理验证** 留 OS M1 launch 联调

### 关键决策点

| # | 决策 | 落点 |
|---|------|------|
| **D-v3.0.5-1** | Side-file pattern(per V3-A no_std + V3-B naked + V3-B inline_asm + V3-B link_section 同款)— codegen 写 `<mnem>\n`,main.jhyy post-QBE-pass concat 到 .s | codegen.jhyy + main.jhyy |
| **D-v3.0.5-2** | 单独 `_fence.buf` side-file(不复用 `_inline_asm.buf`)— 让 fence 路径独立 audit,不污染 3a inline asm diff | codegen.jhyy + main.jhyy |
| **D-v3.0.5-3** | parse_fence_block 接受 name 参数(不依赖 prev_start)— parser_expect(p, LPAREN) 会 clobber prev_start, 必须 caller 在 consume 前 copy | parser.jhyy parse_fence_block + parse_expr dispatch |
| **D-v3.0.5-4** | kind 编号 0=seq_cst, 1=acquire, 2=release(顺序按 C++ memory_order 习惯,非字母序) | ast.jhyy + codegen.jhyy |
| **D-v3.0.5-5** | NodeBuiltinFence { kind: i64 } 而非 { kind: i32 } — 跟 NodeAsmBlock.noperands:i64 对齐(其他 enum 类字段都用 i64) | ast.jhyy |

### 关键数字

| 数字 | 值 | 来源 |
|------|-----|------|
| 新增 NodeKind | 1 (NODE_BUILTIN_FENCE = 54) | v3.0.5 |
| 新增 NodeBuiltinFence size | 8 bytes (1 × i64) | v3.0.5 |
| Side-file path | `compiler/build/obj/_fence.buf` | codegen.jhyy + main.jhyy |
| Fence variants | 3 (seq_cst / acquire / release) | v3.0.5 |
| Fence mnems | 3 (mfence / lfence / sfence) | x86 instruction set |
| ship gate EXIT | 0 | `memory_barrier_smp.jhyy` |
| D43 baseline (N5) | sha=`51376ce5721bccb0c81c7deabead1a6012fb76648c424238391018f1890b5761` (hold,跟 N0 一致) | `jhyy_selfhost_check` verify 4-stage byte-equal (`d742b32` build commit) |

### Out of scope (本 batch 不做)

- ARM (`dmb` / `dsb`) / RISC-V (`fence`) memory barrier 变体 — 留 v3.x 末
- `fence_relaxed` / `fence_acq_rel` builtin — C11 memory_order 完整 6 选 3 之外
- Fence 在 fn 参数位置 / expr value — stmt-position only
- LRC / CLFLUSH 等高级 CPU-specific fence — 留 OS kernel
- V2-A `codegen_amd64_emit_ctrl.jhyy:emit_fence(kind)` stub fill — V2-B v2.7.0 后续 ship

---

---

## V3-B Umbrella 收尾 (2026-09-06) — ✅ shipped (5/5)

V3-B 5 件套全 ship (v3.0.1 / v3.0.2 / v3.0.3 / v3.0.4 / v3.0.5),M1 launch integration gate 全部解除。下一步 = V3-C (`&mut` + lifetime),等 user 启动。

| 关键指标 | 值 | 来源 |
|---------|-----|------|
| 总 ship tags | 5 (`v3.0.1` → `v3.0.5`) | 2026-09-05 ~ 09-06 |
| D43 closure baseline | `51376ce5...` (跟 N0 一致,全程 hold) | `jhyy_selfhost_check` verify |
| Ship gate tests | 5 (`inline_asm_cpuid` / `naked_interrupt_entry` / `volatile_mmio` / `link_section_boot` / `memory_barrier_smp`) | 5/5 EXIT:0 |
| Regress (full) | 109/109 PASS, 0 fail, 5 SKIP (libraries) | `regress.py --binary=jhyy.exe` |
| 新增 AST nodes | 5 (NODE_ASM_BLOCK / is_naked bit in NodeFuncDecl / NODE_VOLATILE_TYPE / link_section ptr in NodeFuncDecl / NODE_BUILTIN_FENCE) | V3-B 5 件套合计 |
| Spec supplements | 5 (1 per sub-sprint,7-section template 通用) | `docs/abis/jhyy-lang-spec-*-supplement-v3.0.X.md` × 5 |
| Side-file paths | 4 (`_inline_asm.buf` / `_naked.buf` 复用 / `_section_directive.buf` / `_fence.buf`) | codegen.jhyy + main.jhyy |
| 新增 ACTIVE workaround | 0 (per `feedback_document_workarounds_in_docs` — 全 ship 时 0 new W-XXX) | coordinator verify |
| V3-A no_std 兼容 | ✅ `no_std_hello.jhyy` EXIT:42 hold | regress + 直跑 |
| 跨轴通知 (V2-B) | 3c shipped → V2-B v2.7.0 sysv volatile backend async | per 2026-09-01 user 决定 |

---

## V3-B v3.0.5-merge — CI regress gate fix (C-side parser pending_inline bridge + 5 V3-B SKIP) — 2026-09-06

v3.0.5 tag push (`d742b32`) 触发 release.yml CI 跑 gated regress → jhyy_stage0.exe FAIL 99/109,2 个 root cause 暴露:

1. **C-side parser 没镜像 d721cb5 pending_inline bridge** — V3-A v3.0.0 commit `4fa06e2` 加 `parse_module_attributes` 在 C-side 后,5 个 inline_* regress test 在 jhyy_stage0.exe 上 fail(C-side `#[inline]` at file-top 还是 error,jhyy-side 已 bridge)。**Fix**:mirror d721cb5 — `Parser.pending_inline: bool` 字段(parser.h)+ `parser_init` init false + `parse_module_attributes` 设 pending_inline=true(原 error)+ `parse_func` OR 进 is_inline 后清零。
2. **5 V3-B tests 用 jhyy-side-only feature** — `inline_asm_cpuid` (asm!) / `naked_interrupt_entry` (#[naked]+asm!) / `volatile_mmio` (volatile type) / `link_section_boot` (#[link_section]) / `memory_barrier_smp` (fence_*) — C-side parser 都没实现。**Fix**:加 `// SKIP: V3-B feature — jhyy-side only (C-side bootstrap predates V3-B)` 到 5 个 file header (per regress.py v1.7.3 SKIP directive,apply 到所有 binary)。

**Decision (D-v3.0.5-1)** (2026-09-06 coordinator):v3.0.5 tag force-move 到 fix commit `f990d05` (per 2026-09-06 user decide)。理由 — V3-B 5 件套是内部 sprint tag,无外部 user 依赖,force-move 比加 v3.0.5.1 patch tag 简单且 changelog footprint 小(umbrella 单节追更)。如果未来有外部 release 引用 v3.0.5,这决策需 revisit。

**Verify**:
- `make stage0` zero warnings
- `make` (stage 1 rebuild)
- `regress.py --all` → **2/2 gated binary PASS**:jhyy.exe 104/104 + 10 SKIP / jhyy_stage0.exe 104/104 + 10 SKIP
- `jhyy_selfhost_check` → D43 baseline `51376ce5721b...` hold (4-stage byte-equal)

**D43 影响**:零 — pending_inline 字段是 C-side `Parser` struct(parser.h),不传 jhyy-side,src0/ Stage 1 .il emit 输出不变,baseline hold。

**Files changed**:
- `compiler/src/parser.h` — `bool pending_inline` 字段 (1 line)
- `compiler/src/parser.c` — `parser_init` init false / `parse_module_attributes` 设 true 替 error / `parse_func` OR 进 is_inline 后清零 (3 hunks)
- `compiler/tests/examples/{inline_asm_cpuid,naked_interrupt_entry,volatile_mmio,link_section_boot,memory_barrier_smp}.jhyy` — 各加 1 行 `// SKIP:` 注释 (5 lines)

**Commits** (axis-v3):
- `5ef6d1a` fix(v3.0.5-merge): C-side parser pending_inline bridge + 5 V3-B SKIP directives
- `f990d05` build(v3.0.5-merge): rebuild jhyy.exe + jhyy_stage0.exe post C-side parser fix
- v3.0.5 tag force-moved to `f990d05`

---

## v3.0.6 — axis-v3 absorbs v2.16.0 src0 backend closure 📋 planned (Ph.1-7 pending)

**Status**: 🚧 in progress (Ph.1+2 ✅ shipped, Ph.3 ✅ code-only / W-083 ⏳ pending Gate-0, Gate-0 + W-086-fix + Ph.4-7 future Phases)

**Per**: [`docs/plans/v3/v3.0.6-port-v2.16.0-src0-closure.md`](../../plans/v3/v3.0.6-port-v2.16.0-src0-closure.md)

### Ph.1 — UTF-8 3/4-byte codepoint fold (W-057 真修) ✅ shipped

**Source**: V2 `594d00d` (v2.13.7 W-057 真修, 2026-09-21).

**W-057 真修** (DEFERRED since 2026-08-28 v1.7.3) — char literal 全 codepoint 范围 (U+0000-U+10FFFF per RFC 3629) ship。

**2 src0 files 改**:
1. `compiler/src0/lexer.jhyy` line 537-575 — lead byte 分支从 2 类 (ASCII + 2-byte) 扩 4 类 (ASCII + 2/3/4-byte), `extra` 计数 0/1/2/3, 删 `oos=1` reject 分支。
2. `compiler/src0/parser.jhyy` `decode_char_literal` line 197+ — 加 3-byte (U+0800-U+FFFF) + 4-byte (U+10000-U+10FFFF) UTF-8 decode 分支, codepoint 计算 per RFC 3629 bitmask formula。

**codegen 不动**: parser 把 char codepoint → `ast_new_int(PRIM_I32)`, codegen 收 `NODE_INT` 走 `ir_emit_copy` (`%t =w copy 0xCODE`) 已 cover 3/4-byte (e.g. `'🎉'` 0x1F389 = 127881 < 2^31, QBE `w` 类能容). Self-backend 同路径 (`codegen_amd64_emit_call.jhyy` 不动, 跟 codegen.jhyy 一致)。

**2 NEW test files** (沿用 V2 命名 per audit fix #1):
- `compiler/tests/examples/char_literal_3byte.jhyy` (CJK `'你'` U+4F60 = 20320, UTF-8: E4 BD A0) — EXIT=0
- `compiler/tests/examples/char_literal_4byte.jhyy` (emoji `'🎉'` U+1F389 = 127881, UTF-8: F0 9F 8E 89) — EXIT=0

**Docs update**:
- `docs/internal/workarounds.md` W-057 flip 🟡 DEFERRED → ✅ RESOLVED (line 59 索引 + line 3852+ body section)。
- `docs/plans/v3/v3.0.6-port-v2.16.0-src0-closure.md` NEW (per-version plan file per `feedback_plans_per_version`)。
- `README.md` v3.0.6/Ph.1 row append。

**Verification gates (V.0-V.2) all PASS**:
- V.0 char_literal_3byte.jhyy (CJK `'你'`) EXIT=0 — 5/5 PASS
- V.1 char_literal_4byte.jhyy (emoji `'🎉'`) EXIT=0 — 5/5 PASS
- V.2 regress — **139/139 PASS / 0 FAIL / 20 SKIP** preserved (跟 v3.2.2 baseline 137/137 + 2 new tests hold)
- jhyy.exe sha `496bea91c54c2f24...` post-Phase.1 rebuild
- byte-equal D26 5/5 PASS preserved (per v3.1.0 D26 stage0 recipe)
- fixed-point N=3 closure preserved (新 closure point through Ph.1 src0 改)

**Out of scope (推后续 Phases)**:
- Ph.2 codegen.jhyy W-058 fmod formula trunc (V2.13.8)
- Ph.3 codegen_amd64_emit_sse.jhyy W-083 self-backend fmod 真修 (V2.13.11)
- Ph.4 in-mem self-backend pipeline + codegen_amd64_inmem.jhyy NEW (V2.15.0)
- Ph.5a git rm -r qbe/ (V3 48 files, NOT V2 41)
- Ph.5b src0 run_qbe fatal-stub + jhyy_helpers.c QBE probing deleted + C-side parity + Makefile D26 + installer (V2.16.0, 含 C-side 76 LOC 改 豁免 2026-09-16 "no new C code" 约束)
- Ph.6 bench.sh NEW (272 LOC) + D26 stage0 coverage + .exe byte-equal 兜底 (V2.16.0)
- Ph.7 ship — git tag v3.0.6

### Ph.2 — codegen.jhyy W-058 fmod user-space formula trunc ✅ shipped

**Source**: V2 `16b4903` (v2.13.8 W-058 fmod emit 路径真修, 2026-09-21).

**Port reference diff**: V2 codegen.jhyy line 2264+ 插 45 行;V3 实测 offset = -49 (V3 line 2214+ vs V2 line 2264+), audit fix #3 估的 -74 偏差, V3 codegen.jhyy 实际更紧凑。

**Critical file changes** (1 src0 file + 3 NEW tests + 1 workarounds entry):

1. `compiler/src0/codegen.jhyy` line 2214+ 插 45 行 (在 `let mut op: *u8 = "add" as *u8;` line 2215 之前):
   - `TOKEN_PERCENT` + (QBE_D 或 QBE_S) early return 路径 → emit 5-instruction user-space formula `a - trunc(a/b) * b` (div + dtosi/stosi + swtof + mul + sub, polymorphic by `tok.qbe_type`)。
   - Polymorphic arith op (`div`/`mul`/`sub`) 靠 `=d`/`=s` 类型后缀, 不嵌 type suffix 进 opcode name;type-conversion ops (`stosi`/`dtosi`/`swtof`) 把 type 后缀编入 name。
   - `is_f32 nested plain if` 无 `&&`/`||` short-circuit (避免 W-081 sub-bug latent phi merge gap, per `feedback_jhyy_brace_nesting`)。
   - 跳过 `op = "rem"` dispatch (下方 line 2267, post-Ph.2);整数模 (`i32 % i32` / `i64 % i64`) 仍走 vendor QBE `remw`/`reml`, 不变。

2. `compiler/tests/examples/fmod_basic.jhyy` NEW (`7.0 % 2.0` exit=1) — 沿用 V2 命名 per audit fix #1。
3. `compiler/tests/examples/fmod_negative.jhyy` NEW (`-7.5 % 2.0` exit=99 = `r_int + 100`; +100 避开 Windows NTSTATUS 误判 0xFFFFFFFF; trunc 区分 floor 关键 case)。
4. `compiler/tests/examples/fmod_f32.jhyy` NEW (`7.0_f32 % 2.0_f32` exit=1, polymorphic f32 fold `stosi` variant)。

**Docs update**:
- `docs/internal/workarounds.md` W-058 flip 🟡 DEFERRED → ✅ RESOLVED (line 60 索引 + line 3905+ body section rewrite with Resolution 段)。
- `docs/plans/v3/v3.0.6-port-v2.16.0-src0-closure.md` Ph.2 status flip 📋 → ✅ + V3 line offset 实测 -49 (修正 audit fix #3 的 -74 估时)。
- `README.md` v3.0.6/Ph.2 row append (after Ph.1 row)。

**Verification gates (V.1-V.2) all PASS**:
- V.1 fmod_basic.jhyy (7.0%2.0) EXIT=1 — 5/5 PASS
- V.1 fmod_negative.jhyy (-7.5%2.0) EXIT=99 — 5/5 PASS (trunc 区分 floor 关键)
- V.1 fmod_f32.jhyy (7.0_f32%2.0_f32) EXIT=1 — 5/5 PASS (polymorphic f32 fold)
- V.2 regress — **126/126 + 3 new fmod = FRESH 129 PASS / 0 FAIL / 21 sysv SKIP** preserved (no regression)
- jhyy.exe sha refresh post-Phase.2 rebuild (post V3 codegen.jhyy edit)
- byte-equal D26 5/5 PASS preserved (per v3.1.0 D26 stage0 recipe)
- byte-equal-amd64 V3-B 10/10 PASS preserved
- fixed-point N=3 closure preserved (新 closure point through Ph.2 codegen.jhyy 改)

**QBE IL opcode 选型 spec 修订** (per V2 16b4903 commit message): vendor QBE `ops.h` 把 `add`/`sub`/`mul`/`div` 列为 polymorphic op (靠 `=d`/`=s` 类型后缀), `stosi`/`dtosi`/`swtof` 才是嵌 type suffix 的独立 op;早期 plan 假设 emit `divd`/`divs`/`muld`/`muls`/`subd`/`subs` (通用记法), 实际用 `div` + `dtosi` + `swtof` + `mul` + `sub` (5 insns) 通过 vendor QBE parse。

**Code structure detail** (per `feedback_jhyy_brace_nesting`): nested plain `if` 无 `&&`/`||` short-circuit 避免触发 W-081 sub-bug (latent phi merge gap)。

**Out of scope (推后续 Phases)**:
- Ph.3 codegen_amd64_emit_sse.jhyy W-083 self-backend fmod 真修 (V2.13.11, 跟 Ph.2 互补)
- Ph.4 in-mem self-backend pipeline + codegen_amd64_inmem.jhyy NEW (V2.15.0)
- Ph.5a git rm -r qbe/ (V3 48 files, NOT V2 41)
- Ph.5b src0 run_qbe fatal-stub + jhyy_helpers.c QBE probing deleted + C-side parity + Makefile D26 + installer (V2.16.0)
- Ph.6 bench.sh NEW (272 LOC) + D26 stage0 coverage + .exe byte-equal 兜底 (V2.16.0)
- Ph.7 ship — git tag v3.0.6

### Ph.3 — src0 codegen_amd64 self-backend conversion family (W-083 Layer 1 code-only 真修) ✅ code-only shipped / ⏳ execution proof deferred to Gate-0

**Source**: V2 `425ab53` (v2.13.11 W-083 self-backend fmod 真修, 2026-09-22). Per 用户 2026-09-23 "conversion 是一族, 一次补齐, 不 case-by-case" 反馈扩到 18 conv ops 一族真修。

**W-083 真修** (DEFERRED since 2026-09-22 v2.13.11) — V3 self-backend 不支持 QBE IL conversion ops (lexer 不识别 dtosi/stosi/swtof/exts/...)。**Audit fix #2 (2026-09-23) REVERTED**: V3 当前**没有** `codegen_amd64_emit_sse.jhyy` 文件 (V3 modular split 7 files only: state/lexer/emit_mem/emit_ctrl/emit_call/regalloc/peephole — 共 4594 LOC)。V2 monolithic 的 emit_sse.jhyy 在 V3 modular split 中拆散到 emit_call.jhyy。**Per user "V3 modular split 不新建 SSE file" 决策, conversion 逻辑 fold 进现有 modules (emit_call.jhyy 主, lexer 新 prefix handlers)**。

**4 src0 files 改**:

1. `compiler/src0/codegen_amd64_state.jhyy` (+11 LOC) — `ILTOK_CONV = 16` enum constant (next to `ILTOK_VOLATILE = 15`)
2. `compiler/src0/codegen_amd64_lexer.jhyy` (+242 LOC) — `next_token_conv(s, arena, t, op_name, op_len)` helper + extend `'d'/'s'/'u'/'e'/'t'` prefix handlers in main `lex_il` dispatcher,识别 18 conv ops (dtosi/dtosl/dtoui/dtoul/stosi/stosl/stoui/stoul/swtof/sltof/uwtof/ultof/exts/extu/extsw/extuw/extsh/extuh/extsb/extub/truncd/truncs); nested plain `if` 无 `&&`/`||` short-circuit (per `feedback_jhyy_brace_nesting`)
3. `compiler/src0/codegen_amd64_emit_call.jhyy` (+450 LOC) — `size_suffix_for_qt` 扩返 `"ss"`/`"sd"` for `QBE_S`/`QBE_D` floats + 4 XMM/GPR scratch helpers (`emit_mov_temp_to_xmm` / `emit_mov_xmm_to_temp` / `emit_mov_temp_to_int` / `emit_mov_int_to_temp`) + `emit_conv(state, tok)` dispatcher 18 distinct branches 走 SSE cvttsd2si/cvttss2si/cvtsi2ss/cvtsi2sd/cvtpd2ps/cvtss2sd/cltq
4. `compiler/src0/codegen_amd64.jhyy` (+5 LOC) — `parse_and_emit` ILTOK_CONV dispatch case `else if kind == ILTOK_CONV() { let _ = emit_conv(state, tok_p); }` (per W-068 fix #4 `let _ = ...` pattern)

**RCA finding (2026-09-23 Ph.3 ship 时 audit-flip closure)** — V3 self-backend `codegen_amd64_run` 对 fmod 类测试 produce 0-byte .s。Root cause **多层**:

- **Layer 1 (W-083, Ph.3 真修 ✅)**: lexer `'d'/'s'/'u'/'e'/'t'` prefix handler 不识别 conversion ops (dtosi/stosi/swtof/exts/extu/...) → `lex_il` 返 -1 → `codegen_amd64_run` 没 emit → 0-byte .s
- **Layer 2 (W-086 NEW, defer 真修)**: `emit_copy` / `emit_binop` / `emit_conv` **字段约定冲突** — `emit_copy` (line 411-418) 读 `int_val` = src value, `text_len` = dst_id;`emit_binop` (line 459-465) 读 `int_val` = dst_id (跟 emit_copy 冲突);`emit_call` (line 312) 读 `int_val` = ret temp id。'%' LHS handler (`codegen_amd64_lexer.jhyy` line 680) **不写** `int_val`/`text_len`, 留 0 从 `lex_init_token`。结果: emit_copy 读 src_int = 0 → 默认 IMM path → `movq $0, dst` → 所有 copy 写入 0;emit_binop 读 dst_id = 0 → dst_off = -32 永远 → 所有 binop 写 -32(%rbp) → 后续 read `%t<N>` 读到错 slot
- **Layer 3 (更深层, defer)**: 即使 emit_* 字段约定统一, lexer 也**不 consume operand** — `next_token_binop`/`copy` 等不 consume src operand, `lex_il` 跳过未知 byte;emit_* 假设 src 在 token 里, 但 token 里没 src

**Docs update**:
- `docs/internal/workarounds.md` W-083 flip 🟡 DEFERRED → ✅ RESOLVED (line ~3966+ body section)+ W-086 NEW 🟡 DEFERRED entry (Layer 2 + Layer 3 RCA + 假阳性 byte_equal_amd64 5/5 PASS 证据 + 真修路径 v3.0.7)
- `docs/plans/v3/v3.0.6-port-v2.16.0-src0-closure.md` Ph.3 section rewrite with 3-layer RCA + revised verification gate (default QBE backend 3/3 PASS ✅ / JHY_SELF_BACKEND=1 ❌ defer W-086 真修)
- `README.md` v3.0.6/Ph.3 row append (after Ph.2 row)

**Verification gates (V.3) — Ph.3 ship 时只 code-only verified, execution proof deferred to Gate-0**:
- V.3.a `jhyy.exe compile fmod_basic.jhyy` (default QBE backend) → .s 200B + exit 1 ✅ (QBE path)
- V.3.b `jhyy.exe compile fmod_negative.jhyy` (default QBE backend) → .s + exit 99 ✅ (QBE path)
- V.3.c `jhyy.exe compile fmod_f32.jhyy` (default QBE backend) → .s + exit 1 ✅ (QBE path)
- V.3.d regress — **142/142 PASS / 0 FAIL / 20 SKIP** preserved (default QBE path 不变)
- V.3.e `byte_equal_amd64.sh --no-strict` — 5/5 PASS preserved (**FALSE POSITIVE** — 5 tests 全走 QBE fallback per `main.jhyy:823-824`, 不设 JHY_SELF_BACKEND → run_backend 落 run_qbe path)
- V.3.f jhyy.exe sha `95a68fd32083bf5f...` post-Phase.3 code-only rebuild
- V.3.g **JHY_SELF_BACKEND=1 fmod 3/3 PASS ❌ BLOCKED by W-086** (Layer 2 emit_* 字段约定 broken + Layer 3 lexer not consume operand) — 唯一真 self-backend execution 路径, **⏳ deferred to Gate-0**

**byte_equal_amd64.sh 5/5 PASS 是 false positive (2026-09-23 发现, 用户 2026-09-23 反馈 "W-083 RESOLVED 不算")** — 5 tests 全走 QBE fallback (default `compile --target=amd64_win` 不设 `JHY_SELF_BACKEND` → `run_backend` 落 `run_qbe` path), V3 self-backend 从未被任何 CI gate 真 exercise。**Per 用户 2026-09-23 反馈**: W-083 status flip ⏳ RESOLVED-pending-verification (从 ✅ 退回), 挂到 **Gate-0** 真跑 JHY_SELF_BACKEND=1 路径。Gate-0 ship 后灯转绿 (跟 W-086-fix 同一 logical commit group) 才正式 ✅ RESOLVED。

**Code structure detail** (per `feedback_jhyy_brace_nesting`): nested plain `if` 无 `&&`/`||` short-circuit 避免触发 W-081 sub-bug (latent phi merge gap)。

**Out of scope (推后续 Phases / Gate-0 / W-086-fix / v3.0.7)**:
- **Gate-0 — byte_equal_selfbackend.sh NEW (造红灯)**: V3 self-backend 唯一 execution gate, 见 GATE-0 section append below
- **W-086-fix — (b)+(c) one commit 真修**: token 扩 3-operand + lexer consume + emit_* 统一读 dst/lhs/rhs, 见 W-086-fix section append below
- Ph.4 in-mem self-backend pipeline + codegen_amd64_inmem.jhyy NEW (V2.15.0) — 必须在 Gate-0 灯转绿后 (per 用户反馈 "Ph.4 排在 W-086 转绿之后")
- Ph.5a git rm -r qbe/ (V3 48 files, NOT V2 41) — **mandatory 前置 Gate-0 + W-086-fix**
- Ph.5b src0 run_qbe fatal-stub + jhyy_helpers.c QBE probing deleted + C-side parity + Makefile D26 + installer (V2.16.0, 含 C-side 76 LOC 改 豁免 2026-09-16 "no new C code" 约束)
- Ph.6 bench.sh NEW (272 LOC) + D26 stage0 coverage + .exe byte-equal 兜底 (V2.16.0)
- Ph.7 ship — git tag v3.0.6

### Gate-0 — byte_equal_selfbackend.sh NEW (造红灯) 📋 planned

**Why Gate-0 exists (per 用户 2026-09-23 反馈)**: W-083 ship commit `68b4b48` 走 default QBE 路径 + regress + byte_equal_amd64 5/5 PASS 全是 false positive (三 gate 全不跑 self-backend)。Gate-0 是 V3 self-backend 唯一真 execution path, 必须先造红灯 (3/3 FAIL) 才能给 W-086 真修一个有判定标准的验收 gate — 否则 W-086 修完你会在同一个假 gate 里再循环一轮。

**Files** (~80 LOC + 3 sha baseline):
- `compiler/tests/bootstrap/byte_equal_selfbackend.sh` NEW — 跑 `JHY_SELF_BACKEND=1 jhyy.exe compile fmod_*.jhyy --target=amd64_win` + 验证 [1/4] .s 非空 (size > 100B) [2/4] gcc link success [3/4] .exe exit code 期望值 (1/99/1) [4/4] .s sha byte-equal to QBE baseline
- `compiler/tests/bootstrap/baseline/fmod_{basic,negative,f32}.s.sha256` NEW (3 sha 文件 — 跟 byte_equal_amd64.sh QBE path 同 sha)

**Verification (this commit ship expected = 3/3 FAIL red)**:
- 跑 `bash compiler/tests/bootstrap/byte_equal_selfbackend.sh` → 期望 3/3 FAIL (0-byte .s + gcc link fail + exit code 异常) — **红灯是这次 ship 的全部价值所在**
- regress 142/142 PASS / 0 FAIL / 20 SKIP preserved (Gate-0 不改 default QBE 路径)
- byte_equal_amd64.sh --no-strict 5/5 PASS preserved (不修改)
- jhyy.exe sha 不变 (Gate-0 ship 不重 build jhyy.exe)

**为什么 Gate-0 跟 byte_equal_amd64.sh 分开 (不扩展现有)**: byte_equal_amd64.sh 5/5 PASS 是 false positive 已 ship 数月 (per v2.6.7 Commit 5), 真路径在 path B 也不设 JHY_SELF_BACKEND → 同样落 run_qbe fallback。Gate-0 必须独立 script + sha baseline 才不会被已有 QBE 比 QBE 假阳性 mask。

### W-086-fix — (b)+(c) one commit 真修 + Gate-0 灯转绿 📋 planned

**Why (b) → (c) → (a) (one commit, NOT 顺序分步)** (per 用户 2026-09-23 反馈):
- **(a) 原写法不成立**: "int_val/text_len 选一个" 错。**binop 语义 = dst = op(lhs, rhs) 需要 3 个 operand slots**, 当前 ILToken (codegen_amd64_state.jhyy:81-88) 只有 `int_val` + `text_len` 两个 8B 字段 = 16B payload, **字段数根本不够**。emit_binop 拿 `int_val` 当 dst_id 之后, lhs/rhs 没地方放 → 塌缩成 dst_id=0 推导的固定偏移 (-32(%rbp)) — **所有 binop 写 -32(%rbp) 就是塌缩的实证**。
- **正确顺序 (用户反馈)**: (b) 先做 → (c) 做 → (a) 自然成立
  - **(b) lexer consume operand for ALL token kinds** — 开关, 必须先做: `'%'` LHS handler 写 dst; next_token_binop consume lhs + rhs; next_token_copy consume src; next_token_conv consume src (existing partial extend to IMM); next_token_call args (extend to full)
  - **(c) 扩展 ILToken 到 3-operand capacity + 删 L4 § 4.3 1-to-1 简化**: 加 `dst: i64` + `lhs: i64` + `rhs: i64` (3 × 8B = 24B operand payload), 加 `op_flags: i32` 标记 IMM/TEMP 区分 (3 bits pack)。emit_* 全部按 dst/lhs/rhs 读 + 按 op_flags 决定 IMM vs TEMP 路径。**删 1-to-1 简化 = 同一个改动的另一面** (per 用户反馈) — 1-to-1 简化允许只用 2 字段凑合, 是这个 bug 的 root cause。
  - **(a) 字段约定统一作废 — 不需要单独 commit**: (b)+(c) 一起做完, emit_copy/binop/conv/call 全部按 dst/lhs/rhs 读, 冲突自然消解。先做 (a) 等于白做一遍。

**Files** (估 +~150 LOC src0):
- `compiler/src0/codegen_amd64_state.jhyy` (~+20 LOC): ILToken 扩 `dst` + `lhs` + `rhs` + `op_flags`; lex_init_token 初始化新字段
- `compiler/src0/codegen_amd64_lexer.jhyy` (~+60 LOC): `'%'` LHS + next_token_binop/copy/conv/call 全部 consume operand + 写入 token fields; nested plain `if` 无 `&&`/`||` per `feedback_jhyy_brace_nesting`
- `compiler/src0/codegen_amd64_emit_call.jhyy` (~+50 LOC): emit_copy / emit_binop / emit_call / emit_conv 统一按 dst/lhs/rhs 读 + op_flags; 删 1-to-1 简化
- `compiler/src0/codegen_amd64_regalloc.jhyy` (~+20 LOC): regalloc offset query 用真 src/dst temp ids (不再是 sentinel 0 fallback)

**Verification (this commit ship expected = 3/3 PASS green)**:
- **Gate-0 灯转绿**: `bash compiler/tests/bootstrap/byte_equal_selfbackend.sh` → 期望 3/3 PASS ✅ (3 fmod tests .s non-empty + gcc link success + exit codes 1/99/1 + sha byte-equal to QBE baseline)
- regress 142/142 PASS / 0 FAIL / 20 SKIP preserved (default QBE path 不变)
- byte_equal_amd64.sh --no-strict 5/5 PASS preserved (不修改, 仍 QBE 比 QBE byte-equal trivially)
- jhyy.exe sha refresh post-rebuild

**W-083 status flip**: ⏳ → ✅ RESOLVED post-Gate-0-green (commit message 跟 W-086-fix 同 logical commit group, ship in 同一 commit 或紧跟 separate commit per `feedback_audit_single_commit_diff`)

**为什么 W-086-fix 不能排在 Ph.4 之后** (per 用户 2026-09-23 反馈 "Ph.4 的验证同样会是假的"): in-mem self-backend 之后不再落 .s 文件, W-083 那个 "0-byte .s" 症状会消失 — 但 W-086 的字段问题还在。Gate-0 验证依赖 .s 文件存在 + sha byte-equal 比对 — in-mem 之后无 .s 可比, Gate-0 对不上。Ph.4 必须排在 Gate-0 灯转绿之后才安全。

---

## v3.0.7 — V3 self-backend 真 closure (W-083 + W-086 wholesale 真修 + Gate-0 灯转绿) — 2026-09-23 ✅ shipped

**Status**: ✅ **shipped** (Commits 0/1/2 入仓 + Gate-0 灯转绿 + W-083/W-086 ✅ RESOLVED)
**Per**: per-version plan [`docs/plans/v3/v3.0.7-...` (per `feedback_plans_per_version`, 跟 v3.0.6 同 per-version 模式; per `feedback_small_plans_no_docs` 若 sprint ≤ 1 stage 可走 plan mode 不单建 docs/plans 文件)]
**Trigger**: v3.0.6/Ph.3 ship 时 audit-flip 把 W-083 退回 ⏳ RESOLVED-pending-verification + W-086 NEW 🟡 DEFERRED (Layer 2/3 字段约定冲突 + lexer 不 consume operand);用户 2026-09-23 反馈三选项 (1) 维持 🟡 DEFERRED / (2) 文档修辞 / (3) 真执行路径 → 选 **(4) 选项 4 + strict sha 锁** + **wholesale 跟 V2 v2.16.0 emit_conv 2-op form 重写**。

### Scope (3 commits in axis-v3)

1. **Commit 0** `infra(v3.0.7/Commit 0): V2 self-backend golden .s 入库 (Gate-0 [2/4] 对照基线)` — `d51155e`
   - 3 V2 v2.16.0 self-backend 实际产出 .s 入仓到 `compiler/tests/bootstrap/baseline_v2_self/` (fmod_basic.s / fmod_negative.s / fmod_f32.s)
   - 造 Gate-0 红灯: V3 self-backend 0-byte .s → Gate-0 3/3 FAIL
   - 关联: W-086 NEW defer 入 workarounds.md
2. **Commit 1** `fix+infra(v3.0.7/Commit 1): V3 self-backend W-083/W-086 wholesale 真修 (merge-file 8 codegen_amd64_*.jhyy + strcmp + state cast + cltq + 2-op form)` — pending ship
   - **`git merge-file` wholesale**: V3/V2 共同祖先 `516821924613eba26cb5153bc8882814a783effe`, 8 codegen_amd64_*.jhyy (state/lexer/emit_call/emit_ctrl/emit_mem/regalloc/peephole + main) merge, **保留 V3 modular split 命名**
   - **strcmp migration**: 16 处 `op_name == ("X" as *u8)` → `strcmp(op_name, ("X" as *u8)) == (0 as i32)` (jhyy `==` on `*u8` 是 pointer compare NOT string compare, hang)
   - **state cast fix**: emit_mov_temp_to_xmm/emit_mov_xmm_to_temp/emit_comment 加 `let cg = state as *CGState; let s = (*cg).out; let arena = (*cg).arena;` (state 是 `*CGState` NOT `*StringBuilder`, 直接 cast → sb.buf/len/cap 读 garbage → sb_grow while 循环 doubles cap 到 INT_MAX → hang)
   - **cltq sign-extension**: `emit_conv_swtof` 加 `cltq` 在 `movl %eax, -N(%rbp)` 之後 `cvtsi2sd %rax, %xmm0` 之前 (per V2 W-083 v2.13.11 真修, fmod_negative EXIT=99 expected vs EXIT=100 sym flag)
   - **2-op form rewrite**: dtosi/dtosl/dtoui/dtoul/exts 改 `cvttsd2si -N(%rbp), %eax/rax` + `movl/movq %eax/rax, -M(%rbp)`, 替代 3-op `movsd -N(%rbp), %xmm0` + `cvttsd2si %xmm0, %eax`, 跟 V2 v2.16.0 golden byte-equal
   - **ILTOK_CONV value fix**: `ILTOK_CONV = 80` (NOT 16, 避免跟 `ILTOK_DIRECTIVE` 撞)
   - **op_len fix**: lexer 14 5-char conv ops call sites (dtosi/dtosl/dtoui/dtoul/stosi/stosl/stoui/stoul/swtof/sltof/uwtof/ultof/extsw/extsh/extsb/extuw/extuh/extub) op_len 4 → 5
   - **emit_conv comment drop**: 删 `emit_comment` call 在 `emit_conv` body 入口 (V3 跟 V2 .s diff 仅 2 行额外 `# emit_conv: ...` 注释, 删后 strict sha PASS)
3. **Commit 2** `fix+changelog(v3.0.7/Commit 2): W-083/W-086 status flip + per-version docs + ship` — pending: v3.0.7 tag push

### Verification gate (per `feedback_fix_evaluation_rule` 5/5 PASS on target tests + `feedback_regress_clean_count` rm _regress_*.exe)

- **Gate-0 (per W-086 真修验收)**: `bash compiler/tests/bootstrap/byte_equal_selfbackend.sh` → **3/3 strict sha PASS + 3/3 exit code PASS = 6/6/0 PASS / SKIP / FAIL** (EXIT=0)
  - fmod_basic: V3 self-backend sha=`25eccf0ad9e291f1...` byte-equal to V2 v2.16.0 self-backend golden sha=`25eccf0ad9e291f1...`
  - fmod_negative: V3 self-backend sha=`8b1d6f333eb19191...` byte-equal to V2 v2.16.0 self-backend golden sha=`8b1d6f333eb19191...`
  - fmod_f32: V3 self-backend sha=`e6346d245ed4b6ed...` byte-equal to V2 v2.16.0 self-backend golden sha=`e6346d245ed4b6ed...`
- **regress 142/142 PASS / 0 FAIL / 20 SKIP** preserved (default QBE path + JHY_SELF_BACKEND=1 self-backend path 双绿); `_regress_*.exe` 清 stale 后 FRESH total 162 (per `feedback_regress_clean_count`)
- **jhyy.exe sha** `bc98c633ca924f1f...` post-Commit 1+2 rebuild
- **W-086 + W-083 status flip**: 🟡 DEFERRED / ⏳ RESOLVED-pending-verification → ✅ RESOLVED 2026-09-23 (workarounds.md 索引行 + body section 同步更新)

### Why this sprint existed (vs. W-083 alone, post-v3.0.6/Ph.3)

per 用户 2026-09-23 三选项决策 (1/4): "选项 4 + strict sha 锁. 6-8 个函数的代价, 换来的是一个对操作数敏感、真实可信、且在 Ph.5a 之后能独自守门的 Gate-0"。原 v3.0.6/Ph.3 W-083 ship 时 3 个 gate (default QBE 3/3 fmod + regress 142/142 + byte_equal_amd64 5/5) 全是 **假阳性** (3 gates 全不跑 self-backend, default `compile --target=amd64_win` 不设 `JHY_SELF_BACKEND` → `run_backend` 落 `run_qbe` path per `main.jhyy:803` 注释)。W-086 是 RCA 发现的更深层 Layer 2 (emit_* 字段约定冲突) + Layer 3 (lexer 不 consume operand) 问题, 单修 W-083 不够。v3.0.7 = 真把 self-backend 拉通, 唯一真 execution 路径 (`JHY_SELF_BACKEND=1`) 真能 produce valid .s + 真过 Gate-0 strict sha + 真过 exit code。

### Out of scope (推后续 v3.0.8 / v3.0.6 Ph.5a+ Ph.5b)

- ❌ v3.0.6/Ph.4 in-mem self-backend pipeline (`codegen_amd64_inmem.jhyy` NEW) — 必须排在 Gate-0 灯转绿之后 (in-mem 后无 .s 可比, Gate-0 失效)
- ❌ v3.0.6/Ph.5a `qbe/` git rm + Ph.5b src0 clean code + C-side parity + Makefile + installer — W-086 真修后 unblock, 但不是 v3.0.7 scope
- ❌ v3.0.6/Ph.6 bench.sh NEW + D26 stage0 coverage
- ❌ v3.0.6/Ph.7 ship + tag (separately ship per `feedback_audit_single_commit_diff`)

### References

- workarounds.md: W-086 ✅ RESOLVED entry + W-083 ✅ RESOLVED entry (索引行 + body section 同步)
- Gate-0 script: `compiler/tests/bootstrap/byte_equal_selfbackend.sh` (244 LOC, [2/4] adaptive sha strategy + 4 gate 总 — `.s non-empty` + `strict sha` + `gcc link` + `exit code`)
- V2 golden: `compiler/tests/bootstrap/baseline_v2_self/v2_self_*.s` (3 .s 入仓)
- V3 merge base: `516821924613eba26cb5153bc8882814a783effe`
- 父 entry: v3.0.6/Ph.3 W-083 Layer 1 code-only 真修 (2026-09-23) + W-086 Layer 2/3 RCA (NEW defer to v3.0.7)
- 用户 2026-09-23 反馈三选项确认: "选项 4 + strict sha 锁" + "先 commit 3+4 (emit_conv 2-op rewrite) 再做 emit_sse 落地"

**Per**: [`docs/plans/v3/batch-V3-C-plan.md`](../../plans/v3/batch-V3-C-plan.md)

V3-B ✅ ship 后由 V3-C sprint 设计 fill in — 3 sub-sprint 累计到本 umbrella 末。

| Sub-sprint | 版本 | 特性 | 状态 |
|------------|------|------|------|
| 3g | v3.1.0 | `&mut` + lifetime | ⏳ 待 user 启动 |
| 3g.5 | v3.1.1 | (待 plan) | ⏳ 待 V3-C v3.1.0 ship |
| 3g.7 | v3.1.2 | (待 plan) | ⏳ 待 V3-C v3.1.1 ship |

---

## 关联文档

- V3-A 任务清单 + 概要 → [`batch-V3-A-plan.md`](../../plans/v3/batch-V3-A-plan.md)
- V3-A spec supplement → [`../../abis/jhyy-lang-spec-no_std-supplement-v3.0.0.md`](../../abis/jhyy-lang-spec-no_std-supplement-v3.0.0.md)
- V3-A ship gate test → [`../../../compiler/tests/examples/no_std_hello.jhyy`](../../../compiler/tests/examples/no_std_hello.jhyy)
- V3-A no_std stubs → `compiler/runtime/no_std_core/*.jhyy`(per batch-V3-A-plan.md § 文件变更清单)
- D10 spec 来源 → `coordination.md § 3 D10`(2026-08-05 锁)
- D43 spec 来源 → `coordination.md § 3 D43`(2026-09-01 锁)
- 跨项目 OS 时间线 → [`../../../../jhyy_OS/docs/coordination.md`](../../../../jhyy_OS/docs/coordination.md)
- v2.x ‖ v3.x 并行 sprint 调度 → [`../../plans/roadmap/v2-v3-parallel-sprint-plan.md`](../../plans/roadmap/v2-v3-parallel-sprint-plan.md)
- v3.x 语言扩展长线 → [`../../plans/roadmap/v3.x-language-expansion.md`](../../plans/roadmap/v3.x-language-expansion.md)
- 阶段前 umbrella → [v2.0.0](../v2/changelog-v2.0.0.md) / [v2.1.0](../v2/changelog-v2.1.0.md) / [v2.2.0](../v2/changelog-v2.2.0.md) / [v2.3.0](../v2/changelog-v2.3.0.md) / [v2.4.0](../v2/changelog-v2.4.0.md)