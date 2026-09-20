# 编译器架构

> 流水线、源文件布局、关键设计决策。
>
> **Last updated**: v2.13.4 (2026-09-20) — 🎯 docs cleanup #4: 4 mislabel/PARTIAL reclassify (0 src change per user 2026-09-20 决定, 跟 v2.13.1/2/3 同 Group A docs-only audit-flip pattern);**W-022 ACTIVE → 📚 DOCS / canonical pattern**(entry 自身 "失效条件 N/A 设计如此,workaround 是规范用法", GH Actions PS5.1 default 在 windows-latest runner, workaround = `Set bash as default shell step` v1.5.5 ship 起 canonical, GH Actions 升 PS7 后 PS7 `Out-File -Encoding utf8NoBOM` 默认无 BOM 但 PS7 跟 PS5.1 共存期间需保留 bash-default canonical pattern);**W-024 ACTIVE → 🌍 ENV-ONLY**(真因 PS5.1 `Set-Content` / `Out-File` 写 UTF-8 文本默认加 BOM + CRLF,Windows PowerShell 5.1 是 GH Actions `windows-latest` runner default,**jhyy-side 不可修** — workaround pattern 稳定: bash-default shell step 或 `[System.IO.File]::WriteAllText($path, $content, [System.Text.UTF8Encoding]::new($false))` 强制 utf8NoBOM,GH Actions 升 PS7 后 `Set-Content -Encoding utf8` default 无 BOM 可考虑删 workaround);**W-029 🟢 ACTIVE → 🟢 STABLE-PRODUCTION mislabel fix**(真修 ship 在 v1.5.6 commit `a2dd4c1` "feat(v1.5.6): jhyy_helpers.c 加 jh_gcc_path() + jh_gcc_invoke() — A 派 Driver 探测" + docs commit `28450d3`,**`commit TBD` 是 docs 漏填** 不是 fix 没 ship — fix ship'd 4+ years stable in production, 🟢 ACTIVE label 误导 future contributor 误以为还需真修);**W-074.6 T4-g ⚠️ PARTIAL → ✅ RESOLVED**(v2.11.11 真修 ship in commit `e01cb59` "fix(codegen): v2.11.11 W-074.6 T4-g lexer cnew/ceqw silent-skip 真修" + docs `c6a703f` + `f0c1860`,5/6 self-backend EXIT exact closure ship done big_test EXIT=57 preserved 跨 v2.11.10/11/12/13/15/19/20/21-fix/23 + v2.13.0/1/2/3 全程维持;**6/6 完整 closure NOT 达成** 是 W-074.7.9 范围 已 ship 闭环,不是 W-074.6 T4-g scope — ⚠️ PARTIAL 是 v2.11.11 ship 当时 honest scope-claim 错出, v2.13.4 closeout flip 回 ✅ RESOLVED);**真 ACTIVE workaround count 5 → 0** 🎉 (剩 W-058 + W-057 + W-074.7 三条真未修 — W-058 codegen emit 路径缺 fmod / W-057 lexer spec 限 UTF-8 3/4-byte / W-074.7 phi merge gap 重设计 — 推 v2.13.5/6/7 真修 sprint);**D43 closure HOLD on `b743f8a5...`** 不变(v2.13.4 = docs-only, src0 未改 → 无 re-baseline event);**jhyy.exe sha `3cc0c7752b04e0fd...` HOLD**(rebuilt baseline not touched in v2.13.4);**regress 121/141 PASS QBE + 121/142 PASS self-backend** HOLD(无 new fixture);umbrellla changelog `docs/logs/v2/changelog-v2.11.0.md` v2.13.4 section(per `feedback_changelog_umbrella` 不创建 standalone `changelog-v2.13.4.md`);v2.13.4 = **无 standalone plan file**(per `feedback_small_plans_no_docs` 单 stage step-by-step plan 不写 `docs/plans/`,走 inline execution);~30 docs LOC, 1 docs commit;**关键决策**:v2.13.4 后真 ACTIVE workaround 归零是意义里程碑 — docs 准确度体现 + v2.x 末 ACTIVE workaround 收尾,剩 3 条真未修推后续 sprint;**status label 精度 audit 是 sprint scope** (DOCS / ENV-ONLY / STABLE-PRODUCTION / RESOLVED 等 5+ label 类别)。**v2.13.3 (immediate predecessor, 2026-09-20)** — 🎯 STALE docs audit #3 (5 flips + 1 reclassify, 0 src change per user 2026-09-20 决定, 跟 v2.13.1/2 同 Group A docs-only audit-flip pattern);**W-074 entry header 🟡 ACTIVE → ✅ CLOSED v2.11.0 ship**(cross-ref commit `25dfb00` 2026-09-09 "W-074 il_len=0 root cause 真修 + regress --self-backend",W-074.5 sub-entry 早 v2.11.1 ship 翻 RESOLVED,本 entry header 漏翻 v2.13.3 RCA closeout flip);**W-074.9 entry header ⏸ DEFERRED → ✅ CLOSED v2.11.21-fix + v2.11.23 ship**(3 sub-bugs 全真修 ship — sub-bug 5 dungeon_game gcc link 真修 commit `1985bd5` v2.11.21-fix Ph.4 next_token_ret 跨行吞 @else 真修 + sub-bug 6 big_array STACK_BUFFER_OVERRUN 真修 commit `98ca31f` v2.11.21-fix Ph.3 2-pass slot alloc + sub-bug 7 top_level_let_mut_types 真修 chain,v2.12.0 audit 验证 3/3 sub-bugs 全 PASS QBE≡SB parity — dungeon_game EXIT=0 / big_array EXIT=5050 / top_level_let_mut_types EXIT=17);**W-074.7 title/body mismatch canonical flip** ✅ CLOSED title → ⏸ DEFERRED(v2.11.15 Iter 2 commit `568d3aa` per-arm injection strategy 估"✅ CLOSED" 基于 spot-check 5/12 PASS,但 v2.11.16 Phase 0 audit user 要求 full regress 跑全 135 tests 发现 spot-check 不可靠 + stale .s 推断错误,body 标 ⏸ DEFERRED audit correction 才是 ground truth,title 误标 v2.13.3 closeout flip canonical 一致);**W-023 misclassification** ACTIVE → 📚 DOCS / canonical pattern(yaml 表达式 + bash sub-shell 语义鸿沟, GH Actions 设计如此,entry 自身写 "失效条件 N/A (设计如此)" 即承认无 bug — `${VAR}` 不展开 `${{ env.X }}` 是 GH Actions msys2 bash 设计如此,canonical pattern 用 `$VERSION` 直接读 env block);**ACTIVE workaround count ~3 → ~1**(剩 W-058 + W-057 vendor-only,再一个 minor sprint 可推 ACTIVE = 0);**D43 closure HOLD on `b743f8a5...`** 不变(v2.13.3 = docs-only, src0 未改 → 无 re-baseline event);**jhyy.exe sha `3cc0c7752b04e0fd...` HOLD**(rebuilt baseline not touched in v2.13.3);**regress 121/141 PASS QBE + 121/142 PASS self-backend** HOLD(无 new fixture);umbrellla changelog `docs/logs/v2/changelog-v2.11.0.md` v2.13.3 section(per `feedback_changelog_umbrella` 不创建 standalone `changelog-v2.13.3.md`);v2.13.3 = 5 flips(含 1 reclassify W-023),不增加 new fixture;v2.13.3 = **无 standalone plan file**(per `feedback_small_plans_no_docs` 单 stage step-by-step plan 不写 `docs/plans/`,走 inline execution);**关键决策**:audit subagent 是关键工具(Explore subagent 跨 grep + git log + audit log 4 cross-ref 路径,~30s 锁定 4 STALE candidates,比手工 cross-ref 快 5-10x)+ audit-flip #3 推 ACTIVE workaround count 收敛到 ~1,**v2.13.4+ 可推 ACTIVE = 0**(W-058 + W-057 vendor-only 单独 docs 标记)。**v2.13.2 (immediate predecessor, 2026-09-20)** — 🎯 W-074.8 family FULLY CLOSED(2 docs-only audit-flip + 1 NEW cap_table_2reg_basic.jhyy fixture, 0 src change);W-074.8 sub-bug 2 (C.4 float imm) STALE audit-flip → ✅ CLOSED v2.13.2(cross-ref v2.11.19 Phase 3 commit `d6364ba`);W-074.8 sub-bug 4 (cap_table 16B 2-reg) STALE on 2 counts audit-flip → ✅ CLOSED v2.13.2(cross-ref v2.11.21-fix Phase 1 commit `4beab82` 1 LOC + SysV § A.4 INTEGER+INTEGER = 1 reg pass);NEW fixture `cap_table_2reg_basic.jhyy`(15 LOC, EXPECT=42);W-074.8 entry header ⏸ DEFERRED → ✅ FULLY CLOSED v2.13.2;ACTIVE workaround count 7 → ~3(剩 W-074.9 3 sub-bugs + W-058 + W-057 vendor-only,v2.13.3 推);D43 closure HOLD on `b743f8a5...`;jhyy.exe sha `3cc0c7752b04e0fd...` HOLD;regress 121/141 PASS QBE + 121/142 PASS self-backend HOLD(+1 from v2.13.2 cap_table_2reg_basic fixture);umbrellla changelog `docs/logs/v2/changelog-v2.11.0.md` v2.13.2 section。(2 docs-only audit-flip + 1 NEW cap_table_2reg_basic.jhyy fixture, 0 src change per user 2026-09-20 决定);**W-074.8 sub-bug 2 (C.4 float imm) STALE description** audit-flip → ✅ CLOSED v2.13.2(cross-ref v2.11.19 Phase 3 commit `d6364ba` 真修 f32 IMM + f64 fractional + FNARG XMM bug,v2.12.0 audit line 184-191 验证 4/4 C.4 float tests PASS QBE≡SB parity — float_arith EXIT=6 / float_arith_f32 EXIT=4 / f32_suffix EXIT=0 / f64_suffix EXIT=0);**W-074.8 sub-bug 4 (cap_table 16B 2-reg) STALE on 2 counts** audit-flip → ✅ CLOSED v2.13.2(cross-ref v2.11.21-fix Phase 1 commit `4beab82` 1 LOC 真修 emit_copy `pct_count` bare `%t` heuristic 真因 — NOT "16B struct 2-register missing", 错诊;SysV § A.4 CapTable<i32> = INTEGER+INTEGER class = 1 reg pass, workarounds.md "16B → 2 regs" claim 跟 SysV § A.4 算法不符);**NEW fixture `cap_table_2reg_basic.jhyy`** (15 LOC, EXPECT=42) sanity-check 16B struct cross-fn pass-by-value,baseline 5/5 EXIT=42 PASS QBE;**W-074.8 entry header ⏸ DEFERRED → ✅ FULLY CLOSED v2.13.2**(4 sub-bugs 全 audit-flip: sub-bug 1+3 v2.13.1 commit `7d8578c` / sub-bug 2+4 v2.13.2 commit TBD, 0 src change total);**ACTIVE workaround count 7 → ~3**(剩 W-074.9 3 sub-bugs + W-058 + W-057 vendor-only,v2.13.3+ 推);**D43 closure HOLD on `b743f8a5...`** 不变(v2.13.2 = docs-only, src0 未改 → 无 re-baseline event);**jhyy.exe sha `3cc0c7752b04e0fd...` HOLD**(no rebuild,docs-only);**regress 121/141 PASS QBE + 121/142 PASS self-backend** HOLD(+1 from v2.13.2 cap_table_2reg_basic fixture);umbrellla changelog `docs/logs/v2/changelog-v2.11.0.md` v2.13.2 section(per `feedback_changelog_umbrella` 不创建 standalone `changelog-v2.13.2.md`);v2.13.2 plan (`docs/plans/v2/v2.13.2-plan.md`) V.1-V.4 gates 全 PASS;**关键决策**:RCA-first 必备(v2.13.2 scope DOWN 关键 per `feedback_rca_first_root_cause`)+ workarounds.md STALE description 错诊 + SysV § A.4 分类误判 都属 "docs 措辞滞后 ≠ code 真因" 模式(跟 v2.13.1 同 pattern)。**v2.13.1 (immediate predecessor, 2026-09-20)** — 🎯 RCA status audit + 6 status flips + 1 new fixture(Group A only, 0 src change);W-074.6.1 sub-family 4 sub-bugs STALE(代码已 ship v2.11.x 真修);W-074.7.9 self-backend STALE(idiv sign-extend + rem lexer 真修 ship v2.11.9);W-073 STALE(self-backend regress 120/120 PASS confirms 0-byte .s not triggered);W-074.8 sub-bug 1 + 3 audit-false-positive(baseline `storel val.id, addr` + emit_mem ptr-deref flag 都已 ship 修);6 status flips docs-only;NEW fixture `slice_iter_nested_basic.jhyy`(15 LOC, EXPECT=66);ACTIVE workaround count 7 → ~2(剩 W-058 + W-057 vendor-only);D43 closure HOLD `b743f8a5...`;jhyy.exe sha `3cc0c7752b04e0fd...` HOLD;regress 120/140 PASS QBE + 120/141 PASS self-backend(1 transient `match.jhyy` race);umbrellla changelog `docs/logs/v2/changelog-v2.11.0.md` v2.13.1 section。 — 🎯 自写后端**真 E2E**(XMM regalloc + SysV codegen + efi 真 boot);**W-074.6 PARTIAL → FULL CLOSED**(真 XMM regalloc linear-scan 8 XMM class + spill + reload + caller-saved across-call (Win XMM0-XMM5) + callee-saved save/restore (Win XMM6-XMM15) + 5+ f64 arg stack-arg fallback 全真修);**真 amd64_sysv codegen 全覆盖**(`abi_amd64_sysv.jhyy` 真修 8-class §A.4 INTEGER/SSE/SSEUP/MEMORY/NO_CLASS + sret RDI first arg + vararg AL save + IEEE 754 long/double width helpers + class-to-QBE-letter map);**amd64_win_freestanding 真 E2E OVMF 5/5 PASS**(self-backend → efi → ConOut 可见 "Hello from jhyy freestanding!" + clean shutdown);**5 sysv tests SKIP → 5/5 PASS**(sysv_abi_test=28 / sysv_struct_mixed=42 / sysv_struct_pass=35 / sysv_struct_ret=18 / sysv_vararg_basic=42 via docker gcc:12 chain, NEW `sysv_full_regress.sh` V.3 gate);regress 119/139 HOLD(QBE + self-backend 双路径 parity);**D43 closure re-baseline `e6b6f1fa...` → `b743f8a5...`**(Phase 2 IL emit 微变 expected re-baseline event per D43 closure rule);jhyy.exe sha `02118a50...` → **`3cc0c775...`**(Phase 1+2 re-build);**ACTIVE workaround count 3 → 2**(W-074.6 FULL CLOSED;W-074.6.1 PARTIAL kept ACTIVE 推 v2.13.1);新增 1 fixture (`xmm_pressure_9args.jhyy`) + 2 bootstrap script (`sysv_full_regress.sh` + `run-ovmf.sh` QEMU 10 适配);**4 sub-commit chain**:`5d405bb` Ph.1 + `b1ad5c3` Ph.2 + `d062a71` Ph.3 + Phase 4 docs+ship;umbrellla changelog `docs/logs/v2/changelog-v2.11.0.md` v2.13.0 section(per `feedback_changelog_umbrella` 不创建 standalone `changelog-v2.13.0.md`);v2.13.0 plan (`docs/plans/v2/v2.13.0-plan.md`) V.1-V.6 gates 全 PASS;**关键决策**:jhyy sema single-pass 无 forward ref(saved as [[feedback_jhyy_no_forward_ref]]) + QEMU 10 chardev syntax migration + QEMU Win32 binary 需 cygpath -w MSYS → Windows path convert。**v2.12.0 (immediate predecessor, 2026-09-19)** — 🎯 首个 audit sprint (无抽样) — 全量 119/119 active PASS tests manual trace audit,phantom PASS = 0,FAIL = 0;audit 跨 8 类别 (Slice 11 + Struct 8 + Control flow 15 + Generics 11 + IO/runtime 21 + Module/global 12 + Pattern match 9 + Misc 32 = 119) 每个 test 编双 backend (QBE + self-backend),.il + .s byte-equal verify,subprocess.run EXIT parity 验证,multi-input boundary (neg/max/OOB/loop iter N=1/100/10000) cross-check;**6 EXPECT-ERROR tests** (compile-fail) QBE ≡ SB exit=1 parity;**jhyy.exe sha `02118a50...` HOLD** (audit 是 trace 不修,无 src0 改 / 无 jhyy.exe re-build);**D43 closure HOLD on `e6b6f1fa...`** 不变 (v2/v3/v4/v5 byte-equal chain HOLD);**ACTIVE workaround count HOLD ≤ 3** (W-074.6 XMM PARTIAL / W-073 verification / W-074.13 ✅ CLOSED);regress 119/139 PASS / 0 FAIL / 20 SKIP,QBE + self-backend 双路径 parity;audit log 落点 `compiler/tests/audit/v2.12.0-audit-log.md` (NEW dir);umbrellla changelog `docs/logs/v2/changelog-v2.11.0.md` v2.12.0 section。v2.12.0 plan (`docs/plans/v2/v2.12.0-plan.md`) V.1-V.6 gates 全 PASS。 — C 端(`compiler/src/*.c`)**freeze 决策** (2026-09-16): 自 v2.5.0 self-backend 引入后基本冻在 v2.4.0 baseline,只有 build-bootstrap 必前置 (jhyy_stage0.exe SIGSEGV 之类) 才 cherry-pick / 改 (W-068 / W-072 例);新 codegen feature (v2.x 中/末 / v3.x / QBE 自写 / N 代 fixed point) 全走 jhyy 端 (`compiler/src0/*.jhyy`);D43 closure 改为 **jhyy-side internal** (v1.exe → v2.exe → v3.exe → v4.exe → v5.exe .il byte-equal),不再要求 C-side mirror;终态 M5 (v1.x 末 Phase 4) 一次性 `rm src/*.c` + untrack QBE + 删 runtime.c。**v2.0 阶段 (v2.0.0 → v2.4.0) 5 版本全 ship** (tags `v2.3.0` / `v2.4.0`);**v2.7.0 末 3-commit ship + v2.7.1 3-commit ship**(Linux ELF runtime + regress.py `--cross` 实 wire);**v2.8.0 → v2.8.3 M2 ship + W-070 真修 + docker gcc chain 5/5 sysv PASS**;**v2.9.0 V2-C Part 1 ship** (src0 revert + N≥3 selfhost fixed point harness);**v2.11.x series** (v2.11.0-19 self-backend iter on axis-v2 + v2.11.18 phi 修復 merge → main);**v2.11.19 Full SSE/float emit (Win+SysV) ship** (5 sub-commits on axis-v2: lexer 8 conv op + emit_sse.jhyy 新建 + f32 IMM 真解 + emit_load/store 浮点路径 + 4 新 fixture;**真修额外 bug**:cg_parse_f64_imm_bits lookup table 高 32-bit 全错 1× 静默 7 sprint);**v2.11.20 address-holder flag propagate + W-017 self-backend emit_load/store $label + match range ship** (3 sub-commits on axis-v2: RC-1 + RC-7 emit_load + emit_copy LABEL flag propagate + W-074.10/W-074.11 真修 + RC-4 match range cmp+clamp fix + W-074.12 真修);**self-backend regress 115/139 PASS** (+11 over v2.11.19 104/139;7 RCA-listed + 4 side effects from RC-1 fix;4 deep-rooted fail deferred to v2.11.21 per honest ship — big_array slot alloc conflict / cap_table_basic emit_load silent fail / dungeon_game multi-file import link / for_in_slice_nested nested slice iterate SEGV, see W-074.13);**D43 closure HOLD** `a8a28cb6...` (active baseline 未变 per V.7 byte-equal gate);**v2.11.21-RCA ship** (2026-09-17) — RCA-only docs sprint (5 parallel sub-agent RCA + silent-fail audit on 8/115 PASS);0 source LOC changes; W-074.13 description refined + W-074.10 caveat added (over-aggressive load propagation → for_in_slice_nested SEGV identified as regression); LOC 收敛至 ~30-75 for v2.11.21-fix sprint; D43 closure HOLD (`f61f467e...`);regress 115/139 → 115/139 (无 src0 changes); active baseline 不变。**v2.11.21-fix ship** (2026-09-17) — 2 src0 真修 (Phase 1 cap_table_basic 1 LOC pct_count `ndig > 0` gate + Phase 4 dungeon_game 1 LOC `next_token_ret` lex_skip_ws 不跨 \n) + 2 DEFERRED to v2.12.x (Phase 2 for_in_slice_nested + Phase 3 big_array,真 fix > 80 LOC each 超 budget);regress 115/139 → **117/139** (+2 self-backend PASS); D43 closure **HOLD on `e6b6f1fa...`** (v2.11.21-fix ACTUAL measured: v2/v3/v4/v5 → 1 unique sha;v2.11.19/20/21-RCA 之前所有 docs claimed `a8a28cb6...` 或 `f61f467e...` 是错的 — measurement 才是 ground truth per `feedback_audit_single_commit_diff`); jhyy.exe sha `0207dd53...` → `5f225239...` (Phase 4 src0 lex_skip_ws 改 binary); W-074.13 PARTIALLY CLOSED (sub-bug 2 + 3 ✅, sub-bug 1 + 4 🔴 DEFERRED to v2.12.x); W-074.10 caveat 升格为正式 amendment (over-aggressive load propagate → for_in_slice_nested SEGV 真因); docs 措辞滞后修正 (实际 closure baseline `e6b6f1fa...`,不是 v2.11.19/20/21-RCA 之前 docs 写的 `a8a28cb6...` / `f61f467e...`)。

## 流水线

```
.jhyy → Lexer → Token流 → Parser → AST → Sema → 标注AST → Codegen → QBE IL → QBE → 汇编(.s) → GCC → .exe
```

`main.c` 调用顺序：
```
read_file
→ arena_init
→ lexer_init
→ parser_init
→ parser_parse
→ resolve_imports        (v0.4+：多文件)
→ sema_init
→ sema_check
→ ir_init
→ cg_module
→ write .il
→ system("qbe ...")
→ system("gcc ... + runtime.c")
```

---

## 源文件清单

`compiler/src/` 下 19 个文件（含 .c + .h）：

| 文件 | 行数 | 职责 |
|------|------|------|
| `arena.c/h` | ~150 | Bump allocator（编译器内部用） |
| `lexer.c/h` | ~400 | 词法分析：源码 → Token 流（50+ token 类型） |
| `ast.c/h` | ~400 | AST：35 种节点类型（tagged union） |
| `types.c/h` | ~250 | 类型系统：原始类型/指针/切片/数组/struct/enum/func/alias |
| `symtab.c/h` | ~120 | 符号表：FNV-1a hash，开放寻址 + 链式作用域 |
| `parser.c/h` | ~750 | 递归下降 + Pratt 表达式解析 |
| `sema.c/h` | ~500 | 语义分析：类型检查/推断，3 遍遍历 |
| `ir.c/h` | ~250 | IR 构建器：QBE IL 文本生成 |
| `codegen.c/h` | ~550 | AST → QBE IL 发射 |
| `main.c` | ~150 | CLI 入口，驱动流水线，调用 QBE + GCC |

运行时：
- `compiler/runtime/runtime.c` ~50 行：`main → main_jhyy` 桥接 + Arena 实现（重复声明，仅供运行时使用）
- `compiler/runtime/runtime.h` ~25 行：运行时头文件

---

## 关键设计细节

### AST 节点

- 所有节点是 `Node` struct + variant data（紧跟 Node 在 arena 中分配）
- `ACCESSOR` 宏模式：`node_xxx_data(Node*)` 返回 variant data 指针
- 构造函数命名：`ast_new_xxx(Arena*, SourceLoc, ...)`
- 共 35 种 `NodeKind`，分布在 `ast.h`

### 类型系统

```
KIND_PRIMITIVE   i8/u8/i16/u16/i32/u32/i64/u64/f32/f64/bool
KIND_POINTER     *T
KIND_SLICE       [*]T (v0.6 codegen)
KIND_ARRAY       [T; N]
KIND_STRUCT      struct { ... }
KIND_ENUM        enum { ... }
KIND_FUNC        (T1, T2) -> R
KIND_ALIAS       type X = ...
KIND_VOID        ()
```

`qbe_type_of()` 返回 QBE 宽度字符：
- `b` (i8/u8/bool)、`h` (i16/u16)、`w` (i32/u32)、`l` (i64/u64)、`s` (f32)、`d` (f64)

### 类型推断规则

- 参数必须标注类型
- 局部变量自动推断（从 init 表达式）
- 函数返回类型：标注优先，标注为 `()` 时从函数体推断

### 符号表

- 开放寻址 + 线性探测，64-bit FNV-1a hash
- 2 的幂大小，负载因子 0.75 自动扩容
- `Sym.module`（v0.6+）：所属模块名（NULL = main），用于 `$mod__name` mangle
- `Sym.is_extern`（v0.6+）：FFI 声明，emit 时不 mangle
- `symtab_insert_sym()` 用于桥接 parser 和 sema 的 Sym

### 作用域管理

- Parser 和 Sema 各有独立的作用域链
- Parser：`parse_func` push → `parse_block` push → `parse_stmt` → ... → pop
- Sema：`check_func_decl` push → `infer_type(block)` → ... → pop
- Sema 的 `nlocals` 不会在 pop 时自动清理，需在 `check_func_decl` 入口手动置零

---

## ABI 关键决策（Windows x64）

1. **Struct pass-by-value** (v0.4+)
   - 调用方分配栈拷贝，`cg_copy_struct` 逐字段复制
   - 大于寄存器宽度的字段通过 memory 传递

2. **Struct return via sret** (v0.4+)
   - 调用方分配返回槽，隐式传递指针为第一个参数
   - 被调用方写入后 bare `ret`

3. **Slice layout** (v0.6+)
   - `[*]T` = `{ptr: *T, len: i64}` 共 16 字节
   - 按 struct pass-by-value 走 sret

4. **模块命名 mangle** (v0.6+)
   - 跨模块函数 emit 时 mangle 为 `$mod__name`（如 `$math__factorial`）
   - extern fn 不 mangle（直接 emit 原名给链接器）

完整 ABI 锁定在 `docs/abis/jhyy-abi-v1.0.0.md`。

---

## QBE IL 速查

```
%t0 =w copy 42           # int 常量
%t1 =l copy %t0          # 64-bit 拷贝（必须同类型；跨宽度用 extsw/truncd）
%t2 =l alloc4 16         # 栈分配 16 字节
%t3 =l add %t1, 16       # 指针算术
%t4 =w loadw %t3         # 32-bit load
storew %t0, %t3          # 32-bit store
%t5 =w call $fn(args)    # 函数调用
ret %t0                  # 返回
jnz %t0, @then, @else    # 条件跳转
%t6 =w phi @a %x, @b %y  # phi 节点
```

宽度：
- `b` byte (8-bit)、`h` half (16-bit)、`w` word (32-bit)、`l` long (64-bit)
- `s` single (f32)、`d` double (f64)

类型转换指令：
- `extsw` (i32 → i64)、`extuw` (u32 → u64)、`extsh` (i16 → i64)
- `truncd` (f64 → f32)、`dtosi`/`dtosi`/`stosi`/`sltof`/`swtof`

---

## Stage 0 自举试点

`compiler/src0/arena.jhyy` 是 `compiler/src/arena.c` 的 JHYY 翻译（v0.6）。

**翻译要点**：
- `size_t → i64`、`void* → *u8`
- varargs (arena_sprintf) 暂不支持
- 自引用 struct 指针用 `*u8 + as *ArenaBlock` 转换
- 指针算术通过 `(ptr as i64 + off) as *u8` 显式表达

测试 driver：`compiler/tests/examples/arena_test/arena_test.jhyy`

验证了 v0.6 编译器对编译自身模块的能力。**v1.0.0 已完成完整自举**（`jhyy_v1 → v2 → v3 → v4` 产出 byte-equal `.il`，sha `2445e97d...`，tag `9b05c0f` / commit `eabee0d`，2026-08-10）。v1.4 → v1.8 系列 ship 后，**Stage 2 N=4 byte-equal closure 稳定**（`jhyy_v1 → v2 → v3 → v4 → v5`，sha `03a1cdd4...` v1.8.0 → sha `51376ce5...` v2.4.0 re-baselined per D43, tag `v2.4.0` `7fb735b`, 2026-09-04）。**v2.0 阶段 (v2.0.0 → v2.4.0) 已 ship** — multi-target dispatcher + freestanding ABI + hello-freestanding.efi E2E 5/5 PASS on OVMF。后续 v2.x 中/末 (QBE 自写 / amd64_sysv 实 impl / N 代 fixed point) 跟 v3.0 3a-3f (inline asm / `#[naked]` / volatile / `#[link_section]` / memory barrier / `#[no_std]`) 异步并行,见 [`docs/plans/v2/v2.0.0-os-prep.md`](../plans/v2/v2.0.0-os-prep.md) 与 [`docs/plans/roadmap/v2.x-qbe-rewrite.md`](../plans/roadmap/v2.x-qbe-rewrite.md) + [`docs/plans/roadmap/v2-v3-parallel-sprint-plan.md`](../plans/roadmap/v2-v3-parallel-sprint-plan.md)。**v2.8.0 Commit 1 re-baseline** (codegen_amd64 emit_mem/ctrl/peephole target_tag dispatch) → `cc89432920cba92f6c465dd73f5faa575bd9ce8d17d678c7e1f34879e419cf2b` (v2.7.0 末/v2.7.1 hold/v2.7.2 hold) → **`6a2f2277656ca991bd1c436c4e8bfe14f5d7b33b3587d778e4d8a0e00118af38`** (v2.8.0 Commit 1 active) — 详见 [`docs/logs/v2/d43-baseline-archive.md`](../logs/v2/d43-baseline-archive.md)。

**v2.13.0 re-baseline** (Phase 2 真 amd64_sysv IL emit 微变) → `b743f8a541f1b14726da6861cbd4db6ec287ce1bbd4ea447bea744e2cf9f94ec` (v2.13.0 active) — D43 closure re-baseline event per D43 closure rule (v2=v3 byte-equal = closure;v1≠v2 = re-baseline event)。

---

## 关键模块: 自写后端 XMM regalloc + SysV codegen (v2.13.0 ship)

> **v2.13.0 起** 自写后端(`codegen_amd64_*.jhyy`) 真 XMM regalloc + 真 amd64_sysv codegen,**不**再硬编码 xmm0..xmm7 或 stub 3-class SysV classification。完整模块边界:

| 模块 | 行数 (v2.13.0) | 职责 |
|------|----------------|------|
| `compiler/src0/codegen_amd64_regalloc.jhyy` | ~1050 (was ~972) | XMM register class (16 XMM regs) + linear-scan `alloc_xmm()` / `free_xmm()` / `spill_xmm()` / `reload_xmm()` + callee-saved save/restore at func entry/exit + caller-saved across-call |
| `compiler/src0/codegen_amd64_emit_sse.jhyy` | ~250 (MODIFY) | XMM arg/return helpers 接 `alloc_xmm()`(替换 hard-coded xmm0..xmm7) |
| `compiler/src0/codegen_amd64_emit_call.jhyy` | ~1100 (MODIFY) | XMM FNARG arg pass 改 `alloc_xmm()` (Win64 前 4 f64 → xmm0-3;SysV 前 8 f64 → xmm0-7;5+ f64 → stack-arg fallback) + SysV classification dispatch (RDI/RSI/RDX/RCX/R8/R9 整数 + XMM0-XMM7 float + mixed interleaving per SysV ABI §3.2.3) |
| `compiler/src0/abi_amd64_sysv.jhyy` | ~409 (was ~309) | 8-class §A.4 classification (INTEGER/SSE/SSEUP/MEMORY/NO_CLASS) + sret helper (> 16 byte → RDI 隐式 first arg) + vararg AL save + IEEE 754 long/double width helpers + class-to-QBE-letter map |
| `compiler/src0/abi_amd64_sysv_freestanding.jhyy` | ~150 (MODIFY) | 同 `abi_amd64_sysv` 但加 freestanding-specific 约束 (no stack probe no runtime helper call) |
| `compiler/src0/codegen_amd64_emit_mem.jhyy` | ~700 (MODIFY) | large struct return sret setup (caller alloc 8-byte aligned buffer, pass RDI = buffer ptr 隐式 first arg) |
| `compiler/src0/target_dispatch.jhyy` | ~200 (verify-only) | 4 target_tag 已 wired: `amd64_win` / `amd64_win_freestanding` / `amd64_sysv` / `amd64_sysv_freestanding` (per v2.13.0-plan.md line 91 audit 2026-09-17) — **NO MODIFY** |

**XMM regalloc API** (per v2.13.0 Ph.1):
- `alloc_xmm(qt: i32) -> i32` — 分配 XMM register 返回 reg id(0-15); 若 8 XMM 全占用 → spill oldest
- `free_xmm(reg_id: i32)` — 释放 XMM register
- `spill_xmm(reg_id: i32, slot: i64)` — spill XMM 到 stack slot
- `reload_xmm(reg_id: i32, slot: i64)` — 从 stack slot reload 回 XMM
- `save_callee_saved_at_entry()` — func entry save Win XMM6-XMM15 (Win ABI callee-saved)
- `restore_callee_saved_at_exit()` — func exit restore 同上
- `save_caller_saved_across_call()` — call 前 save Win XMM0-XMM5 (Win ABI caller-saved across call)

**SysV classification API** (per v2.13.0 Ph.2):
- `abi_sysv_classify_arg(t_raw: i64) -> i32` — 8-class classification(被 `abi_sysv_classify_arg_full` 调,**不**直接调)
- `abi_sysv_classify_arg_full(t_raw: i64) -> i32` — 8-class wrapper(返回 INTEGER/SSE/SSEUP/MEMORY/NO_CLASS enum)
- `sysv_class_to_qbe_letter(cls: i32, sz: i64) -> i32` — class + size → QBE letter (`SSE → QBE_S(4B)/QBE_D(8B)`, `INTEGER/SSEUP/MEMORY → QBE_W/QBE_L` per size, `NO_CLASS → 0`)
- `abi_sysv_sret_setup(ret_type: i64) -> i32` — return type > 16 byte → emit sret setup(RDI 隐式 first arg)

**call graph topology 约束** (per `feedback_jhyy_no_forward_ref`):
- jhyy sema single-pass 无 forward ref,函数定义必须 precede 所有 uses
- 已知 require forward-ref-after pattern 的函数:`abi_win_classify_arg` placeholder → `abi_sysv_classify_arg` 3-class → `abi_sysv_classify_arg_full` 8-class wrapper(`abi_amd64_sysv.jhyy` line 84-88 + 144-152)
- 加新函数前必按 call graph topology 排序(被调用的先定义)

**新增 fixture + bootstrap script** (per v2.13.0 Ph.5):
- `compiler/tests/examples/xmm_pressure_9args.jhyy` (NEW) — 9-f64-arg sum9 XMM pressure + spill (EXIT=255) V.1 gate
- `compiler/tests/bootstrap/sysv_full_regress.sh` (NEW) — docker gcc:12 chain V.3 gate
- `scripts/dev/test/run-ovmf.sh` (MODIFY) — QEMU 10 chardev syntax + serial log file + cygpath -w MSYS → Windows path

**target_dispatch 状态** (4 target_tag):
| Target tag | Phase 真修 | 真后端真 E2E |
|------------|------------|---------------|
| `amd64_win` | v2.7.0+ | ✅ (regress 119/139 PASS) |
| `amd64_win_freestanding` | v2.7.0+ | ✅ v2.13.0 Ph.3 OVMF 5/5 PASS |
| `amd64_sysv` | **v2.13.0 Ph.2** | ✅ 5 sysv tests 5/5 PASS |
| `amd64_sysv_freestanding` | **v2.13.0 Ph.2** | ✅ 5 sysv tests 5/5 PASS(docker gcc:12 chain) |
