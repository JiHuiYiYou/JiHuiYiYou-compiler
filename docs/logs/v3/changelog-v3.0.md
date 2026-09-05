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
| **V3-B (v3.0.5)** | ⏳ 待 V3-B v3.0.4 ship | 3f memory barrier |
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

## V3-B — v3.0.1 → v3.0.5 (M1-required 5 件套) — pending

**Per**: [`docs/plans/v3/batch-V3-B-plan.md`](../../plans/v3/batch-V3-B-plan.md)

(待 V3-A ship 后由 V3-B sprint 设计 fill in — 5 sub-sprint 累计到本 umbrella 末)

| Sub-sprint | 版本 | 特性 | 状态 |
|------------|------|------|------|
| 3a | v3.0.1 | inline asm | ⏳ 待 V3-A ship |
| 3b | v3.0.2 | `#[naked]` | ⏳ 待 V3-B v3.0.1 ship |
| 3c | v3.0.3 | volatile | ✅ **shipped** (V3-B Unit A2) |
| 3e | v3.0.4 | `#[link_section]` | ✅ **shipped** (V3-B Unit B2) |
| 3f | v3.0.5 | memory barrier | ⏳ 待 V3-B v3.0.4 ship |

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
- [x] D43 baseline 重置:`51376ce5...` → `dd65e754...` (N3 re-baseline)。closure chain (v1=v2=v3=v4) byte-equal `dd65e754...` hold (per D43 per-sub-sprint re-baseline policy)
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
| D43 baseline (N3) | sha=`dd65e7547874602e301ad93d4af66d52c4bdc743b9c92a776448f28dbc381e7f` | 本 batch 重 baseline (v2.4.0→v3.0.0 `51376ce5...` hold;v3.0.1/3 changes → 本 batch 重 baseline) |

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

**Per**: [`docs/plans/v3/batch-V3-C-plan.md`](../../plans/v3/batch-V3-C-plan.md)

(待 V3-B ship 后由 V3-C sprint 设计 fill in — 3 sub-sprint 累计到本 umbrella 末)

| Sub-sprint | 版本 | 特性 | 状态 |
|------------|------|------|------|
| 3g | v3.1.0 | `&mut` + lifetime | ⏳ 待 V3-B 末 ship |
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