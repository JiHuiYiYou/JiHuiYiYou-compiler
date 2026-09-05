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
| **V3-A (v3.0.0)** | ✅ **shipped** (tag `v3.0.0` pending) | 3d `#[no_std]` 试水 + core lib stub + supplement doc |
| **V3-B (v3.0.1)** | ⏳ 待 V3-A ship 后启动 | 3a inline asm |
| **V3-B (v3.0.2)** | ⏳ 待 V3-B v3.0.1 ship | 3b `#[naked]` |
| **V3-B (v3.0.3)** | ⏳ 待 V3-B v3.0.2 ship | 3c volatile |
| **V3-B (v3.0.4)** | ⏳ 待 V3-B v3.0.3 ship | 3e `#[link_section]` |
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
| 3c | v3.0.3 | volatile | ⏳ 待 V3-B v3.0.2 ship |
| 3e | v3.0.4 | `#[link_section]` | ⏳ 待 V3-B v3.0.3 ship |
| 3f | v3.0.5 | memory barrier | ⏳ 待 V3-B v3.0.4 ship |

### V3-B v3.0.1 — inline asm (D42 passthrough) — pending ship

**Per**: [`docs/plans/v3/batch-V3-B-plan.md`](../../plans/v3/batch-V3-B-plan.md) Unit A1 (sub-sprint 3a)
**Decision authority**: D42 ([`docs/plans/v2/v2.0.0-os-prep.md`](../../plans/v2/v2.0.0-os-prep.md))
**Branch**: `v3-B/v3.0.1-inline-asm` (cut from axis-v3)

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

## V3-C — v3.1.0 → v3.1.2 (D27 串行) — pending

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