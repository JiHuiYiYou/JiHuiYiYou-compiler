# v4.0.0-rc1 changelog (deferred from v4.0.0)

**Ship date:** 2026-09-30 · **Branch:** `main` · **Tag:** `v4.0.0-rc1` · **Preconditions:** all ✅ (v1.8.3 / v2.16.0 / v3.4.2 all shipped)

> **Note:** v4.0.0 → v4.0.0-rc1 downgraded (per 2026-09-30 user 决定) — Gate 3 (jhyy_selfhost_check N≥3 src0/main.jhyy byte-equal) fails on pre-existing W-074.6 multifn silent fail bug. v4.0.0-rc1 ships the v2/v3-axis convergence with documented self-host main.jhyy known-limitation; v4.0.1+ closes the multifn bug per `feedback_codegen_amd64_multifn` (multi-func closure ~500+ LOC multi-sprint).

---

## What is v4.0.0-rc1

v4.0.0-rc1 is the **convergence release candidate** — first merge of the two parallel axes (`axis-v2` + `axis-v3`) into `main`, kicking off the v4.x minor-version series. Per user decision 2026-09-29, both v2.x and v3.x are declared FINAL; v4.0.0-rc1 unifies their state in a single tree and re-bases all version references, README, CLAUDE.md, and the roadmap.

**No new features in v4.0.0-rc1 itself** — the feature surface is the union of v2.16.0 (QBE-removed, in-mem self-backend pipeline, N≥10 fixed point, `.exe` byte-equal D26 stage0 coverage) + v3.4.2 (V3 self-backend closure, stdlib `std::*` modules, char_literal_3/4byte + fmod 真修).

v4.0.0-rc1 = the moment when JHYY stops being two parallel compilers and becomes one. The `rc1` suffix reflects one deferred gate (self-host `src0/main.jhyy` N≥3 closure — pre-existing W-074.6 multifn bug) being intentionally NOT promoted to `v4.0.0` final until the fix lands in a v4.0.x follow-on sprint.

---

## Preconditions met

| Precondition | Status | Reference |
|---|---|---|
| v1.8.3 shipped (Stage 2 N=4 byte-equal closure + installer) | ✅ 2026-08-29 | tag `98c8272` |
| v2.16.0 shipped (QBE removed + bench.sh + .exe byte-equal) | ✅ 2026-09-22 | tag `v2.16.0` = `axis-v2` HEAD `0b4cde5` |
| v3.4.2 shipped (V3 self-backend closure + 3 minor 真修 W-085/088/089) | ✅ 2026-09-29 | tag `v3.4.2` = `axis-v3` HEAD `8cfcc1e` |
| v2/v3 ACTIVE workaround bucket cleared | ✅ at v3.4.2 | `workarounds.md` ACTIVE = 0 |

---

## Merge commit log

| # | Commit | Message | Notes |
|---|---|---|---|
| 1 | `a4ba8fa` | `chore(merge): merge axis-v2 into main (v2.16.0 axis final)` | `--no-ff`; 1 conflict on `compiler/tests/bootstrap/fixed_point.sh` (resolved by `--theirs`; v3 doesn't have this file) |
| 2 | `c13397d` | `chore(merge): merge axis-v3 into main (v3.4.2 axis final)` | `--no-ff`; 20 conflicts (src0/*.jhyy + workarounds.md + bench.sh + 6 new test files + 4 jhyy_v2..v5.exe + jhyy_stage0.exe); all resolved `--theirs` per user decision 2 (v3 slim workarounds + v3 stdlib + v3 new codegen arch wins) |
| 3 | `c473246` | `chore(version): bump v2.16.0 → v4.0.0-rc1 across active source/docs/installer (~22 files)` | 22 files / 81 hits; excluded: `docs/logs/v2/`, `docs/plans/v2/`, `docs/logs/v3/changelog-v3.*`, `docs/plans/v3/v3.0.6-port-...` + `v3.4.0-plan.md`, `scripts/dev/v2_13_8_*.py` + `v2_15_0_*.py`, `compiler/tests/bootstrap/baseline_v2_self/README.md`, `installer/assets/license.rtf` |
| 4 | `b1cf522` | `docs(archive): move invalidated v2/v3 plans to docs/archive/v2-v3/` | per user decision 1: archive (not delete); `v2-v3-parallel-sprint-plan.md` + `v2.0.0-os-prep.md` → `docs/archive/v2-v3/` with README explaining rationale |
| 5 | `3a48fdd` | `docs(readme): full rewrite for v4.0.0 (post-QBE self-backend + stdlib)` | per user decision 4: 432 → 363 lines; badges → v4.0.0 + self-hosted amd64 backend + Windows+Linux; status table reflects v4.0.0 state; roadmap points to v4.1.0..v4.12.0 |
| 6 | (this commit) | `docs: v4.0.0-rc1 umbrella changelog + CLAUDE.md version-axis update` | per `feedback_changelog_umbrella`: single umbrella per vX.Y, no standalone changelog-v4.X.Y.md; **v4.0 → v4.0.0-rc1 downgrade** per 2026-09-30 user 决定 (Gate 3 selfhost deferred) |
| 7 | (later) | `chore(cleanup): remove axis-v2 + axis-v3 worktree/branch (post-v4.0.0-rc1 merge)` | per `feedback_batch_worktree_cleanup` triplet |

---

## Files changed summary

| Category | Count | Examples |
|---|---|---|
| Compiler source (jhyy-side authoritative) | 14 | `compiler/src0/*.jhyy` (codegen + new codegen_amd64_emit_sse + new codegen_amd64_xmm_argalloc + new codegen_amd64_inmem + new std/*.jhyy + jhyy_helpers.c) |
| Compiler source (C-side legacy) | 2 | `compiler/src/main.c`, `compiler/src/target/target_dispatch.c` |
| Compiler tests | ~12 | `compiler/tests/examples/{char_literal_3,4byte,fmod_basic,fmod_negative,fmod_f32,cap_table_2reg,cap_test_sysv,conv_test,float_arg_xmm,float_load_store,float_unsigned,slice_iter_nested,xmm_pressure_9args}.jhyy` |
| Bootstrap / verification infra | 4 | `compiler/tests/bootstrap/{fixed_point.sh, mutation-test-report.md, sysv_float_cross.sh, sysv_full_regress.sh}` |
| Installer | ~5 | `installer/{build.ps1, Bundle.wxs, jhyy-compiler.wxs, Locale.zh-CN.wxl, README.md}` |
| Internal docs | 3 | `docs/internal/{architecture.md, build.md, workarounds.md, NEW CLAUDE.md}` |
| ABI / spec | 2 | `docs/abis/{jhyy-lang-spec-v1.3.0.md, jhyy-lang-spec-floatsupplement-v3.3.0.md}` |
| Build infra | 1 | `Makefile` |
| New stdlib | 8 | `compiler/src0/std/{arena,fmt,io,math,mem,os,string,vec}.jhyy` |
| Binaries (tracked artifacts) | ~15 | `compiler/build/bin/{jhyy.exe, jhyy_stage0.exe, jhyy.exe.sha256, jhyy_v5.exe, regress.py, jhyy.il, jhyy_v{2,3,4,5}.il}` |
| Scripts | 6 | `scripts/dev/v2_{13_5_insert_anchors, 13_5_rebuild_index, 13_5_rewrite_workarounds, 13_7_umbrella_split, 13_8_umbrella_append, 15_0_insert_readme}.py` + `scripts/dev/test/run-ovmf.sh` |
| MCP server | 1 | `mcp-jhyy/jhyy_regress.py` |
| Tools | 1 | `tools/fixed_point_summary.py` |
| New archive | 3 | `docs/archive/v2-v3/{README.md, v2-v3-parallel-sprint-plan.md, v2.0.0-os-prep.md}` |
| Existing new (post-merge) | 2 | `README.md` (rewrite) + `CLAUDE.md` (workspace, untracked) + `docs/logs/v4/changelog-v4.0.0.md` (this file) |

---

## Verification gates

Per `v4.0.0-plan.md` lines 62-67:

| Gate | Expected | Actual (post-merge) |
|---|---|---|
| regress.py (C-side `jhyy.exe`) | 104/104 PASS + 4 SKIP | ✅ **158/158 PASS + 22 SKIP** (sha `4fd068d8...`) |
| regress.py (`--binary=jhyy_v1.exe.exe`) | 104/104 PASS + 4 SKIP parity | ✅ **158/158 PASS + 22 SKIP** (sha `766c96cc...` — v1 frozen baseline parity preserved) |
| `jhyy_selfhost_check` (MCP) | N≥3 byte-equal stable | ❌ **FAIL** — pre-existing `feedback_codegen_amd64_multifn` (W-074.6 family) drops `main_jhyy` in self-compile of `src0/main.jhyy` (large multi-func file). Reproduces on **both** axis-v2 (v2.16.0 baseline `0b4cde5`) AND v4.0.0 main. NOT a merge regression. Per `feedback_verify_active_reproduces` + `feedback_rca_first_root_cause`: ship-deferred to v4.x per CHANGELOG note "self-backend 1/5 hello PASS preserved (per W-074.6 baseline; multi-func closure deferred v2.x 中期)". |
| D43 final baseline freeze | SHA preserved from v2.16.0 → v4.0.0 closure | ❌ **NOT APPLICABLE** — same root cause as selfhost. v2.14.0 baseline `43fee332...` was on **C-side QBE chain**, not self-host. Per D43 closure rule: re-baseline requires self-host closure working; if not, baseline is NOT preserved through the merge. New baseline = N/A until v4.x self-host 真修。 |
| `byte_equal_selfbackend.sh` | 3/3 PASS (fmod_basic / fmod_negative / fmod_f32) | ✅ **6/6 PASS** (3 .s sha-mnemonic gates + 3 .exe exit gates); wssa drift between V2 emit_conv and V3 emit_conv_* (1-byte size delta) noted as ⚠️ INFO (per script design — "预期若 V3 emit_conv != V2 emit_conv_*") |
| `bench.sh --report` | first-time baseline accept (--strict ≤ 1.7x FAIL) | ✅ **REPORT** mode PASS — fib 1.399x / ack 0.596x / nq 1.020x. fib > 1.1x accepted per first-time baseline rule; --strict gate deferred v4.x per `feedback_no_artifacts_in_project` |
| ACTIVE workaround count | 0 (workarounds.md index) | ✅ 0 ACTIVE per v3.4.2 ship state |

**Gate analysis** (per `feedback_rca_first_root_cause`):

- G1-G2 + G5-G7: **5 of 7 gates ✅** — production regress + byte-equal + bench + ACTIVE=0 all pass. v4.0.0 ships the **union of v2.16.0 + v3.4.2 closure surface** cleanly.
- G3 (self-host src0/main.jhyy) + G4 (D43 closure N≥10): **❌ pre-existing W-074.6 multifn silent fail**. Per v2.16.0 CHANGELOG "self-backend 1/5 hello PASS preserved ... multi-func closure deferred v2.x 中期". Per v3.4.x ship notes (W-085/W-088/W-089 ACTIVE bucket cleared for codegen SSE bugs but NOT multifn). v4.0.0 inherits this ACTIVE state.

**Decision (per 2026-09-30 user)**: ship v4.0.0-rc1 (NOT v4.0.0 final) with G3+G4 documented as KNOWN-LIMITATION. Self-host src0/main.jhyy fix scope: ~500+ LOC across emit_binop/emit_jnz/emit_call/multi-func state — multi-sprint, deferred to v4.0.1+. The `rc1` suffix is the canonical way to signal "ship-ready but not promotion-final due to documented deferred gate" per `feedback_changelog_umbrella`.

If any gate fails → STOP before tag push. Diagnose root cause per `feedback_rca_first_root_cause`; do not bypass with `git commit --no-verify`.

---

## Breaking / notable changes (post-merge cleanup)

1. **Version references unified to v4.0.0** — 22 files had `v2.16.0` strings bumped to `v4.0.0`. Historical `docs/logs/v2/`, `docs/plans/v2/`, `docs/logs/v3/changelog-v3.*`, `docs/plans/v3/v3.0.6-port-...` retained as audit ledger.
2. **Stale plans archived** — `v2-v3-parallel-sprint-plan.md` + `v2.0.0-os-prep.md` moved to `docs/archive/v2-v3/` with README explaining per 2026-09-29 user FINAL decision. The OS M11 launch path predicted by these docs is invalidated and needs v4.x-era redesign.
3. **QBE references purged from user-facing docs** — README.md drops all QBE mentions (except as historical); build.md updates for in-mem self-backend; installer wxs/wxl no longer mention QBE.
4. **WORKAROUND bucket cleared** — v3.4.2 ACTIVE → 0 carries forward to v4.0.0 (per user FINAL 决定). New ACTIVE bucket work in v4.x goes through standard process.
5. **`axis-v2` + `axis-v3` branches + worktrees removed** — `feedback_batch_worktree_cleanup` triplet post-tag-push.

---

## v4.0.0 final — ⛔ 未 promote,blocked

**这一节记录「为什么 v4.0.0 final 至今没有 tag」,而不是宣布 promote。**

按 2026-10-10 user 决定:「所有 defer/active 的 workaround 必须在 v4 正式版中
清零,大不了 v4 不发」。该门槛**当前未满足**。

### 曾经写过「已清零」,那是错的

`6d5eca4` 与 `1871cd7` 都写过「索引表 ACTIVE/DEFERRED = 0,blocker 清零,
下一动作 = tag v4.0.0 final」。2026-10-15 的 fan-out audit 推翻了这个结论,
两条独立的原因:

1. **用来证明清零的那个工具读不到数据。** `v2_13_5_rebuild_index.py` 的
   `STATUS_RE` 不容忍状态行里的 `✅` 前缀(59 条被静默丢弃),且只匹配 H2 而
   9 条挂在 H3 下 —— 索引 16 行 vs 台账 96 条。所以「索引表 0 ACTIVE」
   从来不是「没有 ACTIVE」,是「读不到」。已修(登记 **W-108**,索引 → 94 行)。

2. **验证闭环的那几个门自己翻不了红。** CI 里内联的 Stage2/Stage3 `.il` sha
   比对从没设 `JHY_WRITE_IL=1`,四个 sha 全是空串,`"$A" != "$B"` 对空串恒假,
   闭环与否都打 `PASS (sha=)`;`fixed_point.sh` 的 cap_test 层因为 `-o` 多写了
   `.exe` 三代全 SKIP 仍判 PASS;`fixed_point_linux.sh` 的终局判据
   `LINUX_PASS -ge 0` 对初值 0 恒真。真正的门 `closure_check.sh` 从未被 CI 调用过。
   已修(commit `4a117a1`,三个门逐一造过红灯)。

### 当前真实状态(2026-10-15 实测)

```
索引表        7 ACTIVE / 81 RESOLVED / 4 SUPERSEDED / 2 INVALID / 0 DEFERRED
regress       163/163 PASS + 22 SKIP (of 185)   ← 注意 PASS 的强度,见下
closure_check PASS, v2.s == v3.s byte-identical (sha da78987c)
fixed_point   7 PASS / 0 FAIL / 0 INFO (N=5)
```

**7 条 ACTIVE:** W-103(std_os 全 mock)/ W-104(SysV 借 Win 分类器)/
W-105(`check_borrow` 恒 return 1)/ W-105.1(同款死 stub)/
W-106(arena-touch)/ W-107(per-fn 表 1024 上限)/ W-109(浮点比较算错)。

修法、优先级、验收 gate 见
[`docs/plans/v4/active-workaround-clearance.md`](../../plans/v4/active-workaround-clearance.md)。

### ⚠️ 「163/163 PASS」不能当作正确性证据

`docs/internal/tests.md` 顶段有完整说明。一句话版本:185 个测试里约 108 个
有真断言,48 个只验「进程没崩」,stdout 从不被比较。浮点比较就是这么活到今天
的 —— `float_cmp.jhyy` 无判据指令且 `return 42` 写死,而 f32 比较实际按 f64 算、
`f64 ==/!=` 直接编译失败(W-109)。

**「PASS」证明的是「没崩」,不是「算对了」。**

### promote 条件

1. 上表 7 条 ACTIVE 全部 RESOLVED
2. 每条都有**能翻红**的测试(造过红灯),不是新增一个 `return 42`
3. `regress` 在 `jhyy.exe` 与 `jhyy_v2.exe` 两个 binary 上都不退步
4. `closure_check.sh` + `fixed_point.sh` 保持绿

---

## v4.0.12 — SysV MEMORY class(>16B struct 走栈)· W-104 闭合

**2026-10-20。** W-104 是最后一条「违反 locked ABI 规范」的 ACTIVE —— 现在
**RESOLVED**。台账:`docs/internal/workarounds.md` W-104。

### 修了什么

SysV 的 struct 传参有**两条**完全不同的路径,之前只实现了一条:

| struct 大小 | SysV 分类 | 传递方式 |
|---|---|---|
| ≤16B | INTEGER / SSE eightbyte | 按值分进 GPR / XMM |
| **>16B** | **MEMORY class** | **整份拷贝到栈上**,不占任何整数寄存器 |

≤16B 部分 2026-10-19 已修(v4.0.11)。本版补齐 >16B。

MEMORY class 的语义是「这个实参走栈」,而 self-backend 判定「实参落栈」的**唯一**
依据是「寄存器池耗尽」—— 表达不了「不占寄存器但必须落栈」。所以动了四个层面:

| 层 | 改动 |
|---|---|
| IL(header) | MEMORY 参数声明成 N 个 8 字节 slot,名字带 `__m<k>` 标记 |
| IL(caller) | 每个 slot 从 struct 副本按值 load,作为独立实参进 args 数组,letter `'m'`(109) |
| self-backend(caller) | `int_arg_alloc` 对 `'m'` 返 -1(落栈)且**不占 INTEGER 序列**;调用点 `subq $N,%rsp` 预留 outgoing 区,call 后对称 `addq` |
| self-backend(callee) | FNARG 识别 `__m<k>` → 从 `16(%rbp)+k*8` 读 |

**受限边界照做**:「有 MEMORY 参数」且「整数参数 > 6 或浮点参数 > 8」时
**明确报编译错误并退出**(`cg_sysv_check_memory_scope`),不静默产错码。

### 途中挖出的两个更早的 bug(不限于 MEMORY)

- `codegen.jhyy` 的 `out_idx` 写成 `= i`(原始下标)而不是跨实参累计 ——
  struct 展开后,后续实参会写回**已被占用**的槽位。`f(Mixed m, i32 x)` 的 %x
  落在 m 的第二个 eightbyte 上,call 文本多出一个空槽 `%t0`。
  **单参数调用测不到** —— 这就是 ≤16B 的测试当初全绿的原因。
- `codegen_amd64_state.jhyy` 的 `cg_parse_mem_slot` 按 `_m_` 三字节比较 ——
  标记其实是 `__m<k>`(两个下划线)→ 永远匹配不上。

### 验收

```
跨实现对拍(新):  small jhyy→gcc = 44 ✅   big jhyy→gcc = 42 ✅   big gcc→jhyy = 42 ✅
跨实现对拍(旧):  big jhyy→gcc = 139(SEGV) ❌   big gcc→jhyy = 20 ❌   ← 门能抓到
jhyy↔jhyy:       big = 42 ✅
全量回归:        177/177, 0 failed ✅(含 5 个 sysv 用例)
自举闭环:        v2..v5 逐字节相同 ✅   closure_check v2==v3 ✅
artifact 级门:    sysv_mixed_struct / sysv_memory_class / sysv_arg_spill 全 PASS
```

新增常驻门:

- `compiler/tests/bootstrap/sysv_abi_cross.sh` —— 扩成**三方向**
- `compiler/tests/bootstrap/artifact_checks.sh` 新增 `sysv_memory_class` ——
  **只看 .s 不跑二进制** → Windows runner 上就能跑,不依赖 docker
- fixture `sysv_abi_mem_caller.jhyy` / `sysv_abi_mem_callee.jhyy`

**ACTIVE 条数:11 → 10。**

---

## v4.0.14 — enum 的 ABI 两侧统一 · W-114 闭合(+ 顺带修 W-119)

**2026-10-20。** W-114(全 unit-variant 的 enum `match` 永远命中第一支)是最后
一条「核心语言功能静默失效」的 ACTIVE —— 现在 **RESOLVED**。台账:
`docs/internal/workarounds.md` W-114 / W-119。

### RCA 推翻了原描述

原台账写「match 不做 tag check」。**不对** —— tag compare **一直都在 emit**
(IL:`%t8 =w ceqw %t6, %t7` + `jnz`),只是**比的东西不对**。

真根因:**enum 的 ABI 两侧不一致**。jhyy 的 enum 值 = 「指向一个槽的地址」
(ABI § 2.6 布局 + § 4.1「enum 构造 → 栈槽」),而 `abi_win_classify_arg` 对
**size ≤ 4 的 enum 返回 QBE_W(按值传)** —— 与规范相反。

| 位置 | caller 给的 | callee 期望的 | 后果 |
|---|---|---|---|
| enum 参数(全 unit) | 地址(`l`) | 值(`w`) | 寄存器归属理解不一致 → **tag 比较永不成立** → 恒命中第一支 |
| enum 返回值 | callee 帧里那个槽的地址 | — | 函数一返回就**悬垂**(下一个函数的序言会盖掉它) |
| enum 调用结果 | 8 字节地址 | 只存 %rax 的**低 4 字节** | 地址被**截断** → 读 tag 读到垃圾 |

带 payload 的 enum(size > 4)恰好被分类成 QBE_L(地址)✓ —— 所以它一直正常。
这解释了「规律精确:有任意一个 variant 带 payload 就正常」。

### 实现:先定表示,再统一两侧

1. `abi_win_classify_arg` 对 enum 一律返回 QBE_L(地址)。它同时决定**参数**与
   **返回值**的字母(4 个调用点:Win header / SysV header / 返回类型 /
   callee 的 param 局部)—— enum 的值在两边都是地址,四处一次改齐。
2. **enum 的返回值改走 sret**(ABI § 3.3 明写「struct / enum → 隐式 sret 指针
   参数返回」)。caller 出目标槽,callee 把 **image** 拷进去(新增
   `cg_copy_enum`:按 8/4 字节分组拷 `sizeof(enum)` 字节)。不能只拷地址 ——
   那个地址指向 callee 自己帧里的槽,返回即悬垂。
3. enum 的**调用结果 / if 结果 / match 结果**用 `cg_value_type_of`(8 字节地址),
   不是 `qbe_type_of`(4 字节 tag)。
4. **「存储放 image,表达式求值为地址」**:局部变量槽 / struct 字段 / 数组元素 /
   循环变量 → 拷 image(新增 `cg_store_enum_image`);enum 变量 / 字段 / `*p` /
   `arr[i]` / `&e` → 给**地址**,不 load(load 出来的是 4 字节 image → tag 对、
   **payload 丢**)。

### 途中挖出的两个更早的 bug

- **`&e` 对 enum 取的是「指向一个装着地址的槽的地址」**:通用 SSA 路径会先 alloc
  一个 temp 把地址存进去、再取 temp 的地址。enum 的值本身就是地址 → `&e` 应
  等于 `e`。
- **W-119**(单独登记):**SysV 帧布局把第 0 号局部变量放在 `0(%rbp)`** ——
  那是 `saveq %rbp` 存的**旧 rbp**。Win 侧靠 -32 的影子区避开,SysV 侧没有
  影子区就得靠 -8 的偏移避开(公式改成 `-(local_t+1)*8`)。
  **这条是活的**:`sysv_abi_test` 的 `main_jhyy` 里一直有 `movl $1, 0(%rbp)`;
  它自己没崩是因为它是最外层(caller 是 crt0,不关心 rbp)—— 同样的形状出现在
  **被别的 jhyy 函数调用**的函数里就直接 SEGV。

### 验收

```
最小复现(Win):  u3(A)=0 u3(B)=1 u3(C)=2 ✅  pn(N)=200 pn(S(5))=105 ✅  mx(Z)=30 ✅
返回值:         arm(mk())=1 ✅  arm(passthru(U::C))=2 ✅  match mk(){..}=1 ✅
payload enum:   arm(P::N)=200 ✅  arm(P::S(5))=105 ✅  arm(mk())=200 ✅
局部变量:       let mut c: U = U::B → match=1 ✅  赋值后再 match=2 ✅
                let mut p: P = P::S(7) → arm(p)=107 ✅(payload 没丢)
struct 字段:    get_e(WithE{e:U::C})=2 ✅
gdb_pretty_test: read_color=1 + read_maybe=42 = 43 ✅(之前是垃圾)
SysV(同款):     同样的用例在 amd64_sysv 目标下 = 217 ✅
全量回归:       178/178, 0 failed ✅
自举闭环:       v2..v5 逐字节相同 ✅  closure_check v2==v3 ✅
5 个 SysV 回归:  5 PASS ✅   W-104 三方向对拍: 3 PASS ✅
```

新增常驻门:

- `compiler/tests/examples/enum_match_unit_variants.jhyy` —— XFAIL 标记已摘,并
  扩了三个用例(跨函数返回 / struct 字段 / payload enum 的返回)
- `compiler/tests/examples/sysv_enum_match.jhyy` —— **新增**:SysV 侧的 enum 回归
  (Win 与 SysV 两条路径都要验 —— 只验 Win 的话,「同一份 enum 语义在两个目标上
  不一致」这类缺陷会隐形)

**ACTIVE 条数:10 → 9。**

---

## v4.0.15 — W-105 (a):`&mut` 真的能用了(D1=A 路线的一半)

**2026-10-20。** 台账 W-105 的原描述是「`&mut` 是个装饰性标注:parser 认、
类型系统里有、spec supplement 也承诺过,但造不出、传不进、解引用不了」。
**这一半修好了** —— 另一半(独占性检查)仍未做,W-105 保持 ACTIVE。

| 改动 | 内容 |
|---|---|
| `ast.jhyy` | `NodeAddrOf` 加 `is_mut` 字段 |
| `parser.jhyy` | 表达式位置接受 `&mut expr`(之前报「unexpected token 'mut' in expression」) |
| `sema.jhyy` | `&mut expr` 的类型 = KIND_REF(is_mut=1),与**类型**位置的 `&mut T` 同一表示(抽出 `sema_make_ref_type` 供两边共用) |
| `sema.jhyy` | 解引用接受 KIND_REF(之前只认 KIND_POINTER) |
| `mono.jhyy` | 泛型实例化保留 is_mut |

**`&expr`(共享)仍是 KIND_POINTER** —— v3.1.0 既定语义 ✓,不动 ✓。

**验收:** `borrow_mut_write.jhyy` 摘 XFAIL → **EXIT=5** ✓;`borrow_check_basic.jhyy`
仍 EXIT=42 ✓;全量回归 **179/179** ✓;自举闭环 v2..v5 ✓。

**❌ 独占性检查(W-105 (b))没做**:最小实现让**自举编译器 SEGV** ——
自举出来的 jhyy.exe 编任何文件都崩(确定性,gdb 下不复现),崩溃点是一个
**帧偏移 ≈ -515KB** 的写(局部变量冲出帧)。逐项二分(调用 vs 内联 / AST /
parser / sema 各子集 / dummy 函数)都没定位到残留的那一处,触发条件是
「**在 `infer_type`(递归热路径)里加代码**」这个动作本身。⇒ 下一步:把借用
记录挪出 `infer_type`。详见台账 W-105。

**⚠️ 顺带发现:W-107 的余量只剩 2 个函数**(main.jhyy 现在 1022 个)。越过 1024
之后被丢弃的函数会拿到 **8 字节的帧** → 局部变量冲出帧。**W-107 升级为高优先**。

---

## v4.0.16 — std_os_* 接真 libc(W-103 闭合)+ `#[link_section]` 落到真的 .s(W-112 闭合)

**2026-10-20。** v4.0.16 计划里的三项:W-103 ✅ / W-112 ✅ / W-113 ⏳(未做)。

### W-103 —— `std_os_*` 的五个 mock 全是真实现了

**RCA 推翻了原描述的一半。** 台账写的是「W-079(QBE mixed-args bug)挡住了
std_os_*」。W-079 当年挡的是 **QBE**;QBE 随 v4.0.0 完全移除,self-backend
(codegen_amd64_*)不再经过 QBE。**实测 mixed-width extern 调用在 self-backend
下完全正常**(`jh_os_open(*u8, i32, i32) -> i64` 一次跑通)—— W-079 当年的
理由早已失效,W-079 的 RESOLVED 只是没覆盖 std_os 这一半。

**但 mock 还藏了第二个 bug,而且它比「不做事」严重。** `std/os.jhyy` 的
`O_*` 常量是 **POSIX 值**(`O_CREAT`=0x40),而 Windows 的 `_O_CREAT`=**0x100**。
mock 从不调 `open(2)`,所以这个错一直藏着;真接上 libc 之后第一次调用直接
返 -1。从 C 侧复现同样 -1 才定位到是 **flag 值**而不是 FFI:

```
Windows:  _O_CREAT  0x100   _O_EXCL 0x400   _O_APPEND 0x8   _O_TRUNC 0x200
POSIX:    O_CREAT   0x40    O_EXCL  0x80    O_APPEND  0x400 O_TRUNC  0x200
                                      ↑ 只有 TRUNC 两边同值
```

错法很隐蔽:POSIX 的 `O_CREAT`=0x40 落到 Windows 上是 `_O_NOINHERIT`,
于是「没带 O_CREAT」→ 文件不存在 → ENOENT → fd=-1,**看起来像「路径不对」**。

| 层 | 改动 |
|---|---|
| `jhyy_helpers.c` | 5 个 libc bridge:`jh_os_open/close/read/write/exit`。签名跟 `std_os_*` **1:1 对齐**(指针宽 / i32 / i64 各就各位)→ jhyy 侧零宽度转换。`read`/`write` 循环到读满/写满 n 或 EOF(POSIX 允许部分完成)。Windows 走 `_open/_close/_read/_write`,POSIX 走 `open/close/read/write` |
| `jhyy_helpers.c` | `jh_os_translate_flags()`:POSIX ↔ 平台 `O_*` 逐位翻译 + Windows 无条件 OR `_O_BINARY`(jhyy 的 `std_os_*` 是**字节**语义;不强制 binary 的话 CRT 会做 CRLF↔LF 转换,字节级往返就废了) |
| `std/os.jhyy` | 五个函数改调 bridge;入参校验(路径空 / flags<0 / mode 越界 → -1)保留 |
| `main.jhyy` | **import 两级查找**:main 文件旁边找不到 → 回落到 std lib 目录(`jh_path_stdlib()`)。这是 std lib **第一次真的可被用户代码 import** |
| `jhyy_helpers.c` | `jh_path_stdlib()`:源码树 layout (b) = `<root>\compiler\src0\std\`;installer layout (a) = `<bindir>\std\` |
| `installer/` | 8 个 std 模块进 MSI 的 `bin\std\`(WiX `StdDir` + 一个装 8 个 File 的 Component) |

**为什么 import 回落是这次修复的必需品(不是顺手加的)。** 之前 `import <mod>;`
**只在 main 文件旁边找**,于是 `compiler/src0/std/` 下的 8 个模块**任何用户程序
都够不着** —— 想测 `std/os.jhyy` 只能在测试文件里**抄一份 inline 副本**。
而副本是不受约束的:那份副本给「mock 契约」背书(`fd==42`、`write` 返 5),
于是一个**从不碰文件系统**的纯 mock 一直有个 PASS 撑着,而那个 PASS 不验证
任何真实行为。**mock 能活这么久,根因之一就是「测试验的是副本」。**

**测试改成 import 真身,断言全部对着真实行为重写:**

| 测试 | 验什么 | 造红灯 |
|---|---|---|
| `std_os_basic.jhyy`(改写) | import 真身 + 6 个 sub-test:真 fd(≥0)、写落盘、**读回的字节 == 文件里的字节**、getenv | `std_os_read` 退回 mock → **EXIT=9** 红 ✓ |
| `std_os_real_io.jhyy`(改写,XFAIL 已摘) | 用 **libc fopen/fread** 读回 std_os 写的文件 | `std_os_write` 退回 mock → **EXIT=4** 红 ✓ |
| `std_os_exit.jhyy`(**新增**) | 整个测试就是调 `std_os_exit(42)`;进程退出码必须 == 42 | `std_os_exit` 退回 no-op → **EXIT=99** 红 ✓ |

`std_os_real_io` 绕开 `std_os_read`、改用 libc fread 是**故意的**:两边都走
std_os 的话,「写进 A、读出 A」的闭环在 mock 下也自洽(mock 的 read 声称读了
n 字节,buf 里是上次残留)。只有**第三方读者**(libc)才能证明字节真的落盘。

**⚠️ 方向张力(有意识的取舍,不是疏忽):** 这 5 个 bridge 让 jhyy 程序**又依赖
C runtime**,与 M5「删 C runtime / 0-C 闭环」方向相反。取舍:std_os_* 是
**POSIX 语义层**,OS kernel M11 launch 之前由 host libc 兑现最省事。真要 0-C
时,**换掉的是这 5 个 bridge 的实现**(改成 syscall / kernel call),
`std/os.jhyy` 里的 `std_os_*` **一行都不用动** —— 张力被限制在
`jhyy_helpers.c` 一个文件里,不在语言语义层。同族先例:`std/io.jhyy` 的
`std_io_print` 走 `jh_fputs_stdout`(W-080),同一个手法。

**验收:**

```
全量回归:       181/181 PASS, 0 failed (203 total / 20 skip / 2 XFAIL 都是别的 bug)
自举闭环:       closure_check.sh v2.s == v3.s byte-identical ✅
产物级门:       artifact_checks.sh 5 PASS / 1 KNOWN-FAIL(W-113) / 0 FAIL
SysV 6 个回归:  6 PASS ✅    W-104 三方向 ABI 对拍: 3 PASS ✅
MSI:            wix build 成功,8 个 std 模块进 File 表 ✅
3 个新/改测试:  各自当场造过红灯 ✅
```

**ACTIVE 条数:8 → 7。**

### W-112 —— `#[link_section]` 的 `.section` 之前插进了**错误的文件**

台账记的是「`#[link_section]` 是 no-op,生成的 .s 里没有任何 `.section`」。
真因更具体:`.section` 指令被 apply 到 **link 路径的副本**(`temp_asm`),
而磁盘上的 `.s`(`--no-link` 的产物、也是所有 .s 级门的输入)**没有**。
修法:.s 产出后立刻对 `asm_path` 处理一次。产物级门
`artifact_checks.sh` 的 `link_section` check 从 KNOWN-FAIL 升成真门。

### W-113 —— ⏳ 本版未做

`asm!` / `fence_*` 的字节仍被 emit 到 `ret` 之后(永不执行)。这是 IL 层的
管道活(asm blob 要流过 IL 进 self-backend 才能落在函数体里),留在 v4.0.17。

---

## v4.0.17 — 两张「按固定上限分配」的表改成按实际需要分配(W-107 + W-120)

**2026-10-20。** 计划里的两项:**W-107** ✅ / **W-105.1** ⏳(留给下一版)。

### W-107 —— 五张 per-fn 表按实际函数数分配(没有上限了)

**这次为什么能成 —— 前一次为什么失败。** 台账记着「动态分配试过、实测仍有残留
缺陷、已撤回」(`a21c207` → `b7c4e6e`)。复盘发现:那次撤回的**同一个 commit**
里还带着另一条真修,而它恰好是动态分配的另一半:

| 缺陷 | 症状 | 修法 | 落地 |
|---|---|---|---|
| 表按固定长分配 | 超出部分被**丢弃** → 该函数没有 per_fn_max → local_max 被钳成 0 → 帧只有 8 字节 → 局部变量**冲出帧** | 按实际函数数分配 | **本次** |
| 查表按**表长**判界 | idx 越界时**跳过查表** → local_t 变成**全局 temp id** → 帧偏移 ≈ -518KB | 上界改用 `fn_count` 判 | `b7c4e6e`(早于本次) |

**只修一半时动态分配仍然 SEGV** —— 这就是第一次被撤回的原因:动态分配先落地,
上界真修后落地,**两者从未同时存在过**。本次两条同时在场,一次通过。

改法:`cg_state_init` 不再分配五张表(pre-scan 按 `fn_count + 1` 分配);
`MAX_FN_ENTRIES()` 常量**删除**;「太多函数」的响亮守门**删除**(不再有上限)。

### W-120 —— 同一个形状的**第二个**悬崖(HEAD 上本来就可复现)

修 W-107 的过程中挖出来的:**temp 表(temp_slot_for_id / temp_holds_address)
按固定 65536 分配**,而 temp id 是 IL emitter **全局**编号的。越界时:

```
temp id ≥ 65536 → 不记录 → 读时跳过查表 → 落到 formula 兜底
                → 同一个 temp 在「写」「读」两处解析成**不同的槽** → 值静默丢失
```

**症状:编译成功、链接成功、运行成功 —— 值是错的。** 实测一个 25000 语句的
函数:算出 `s = 0`(正确值 74994);4100 个函数的文件:求和 = 0(正确 36900)。

**⚠️ 余量有多小:`main.jhyy` 自己的 max temp id 已经到 64953** ——
离 65536 只剩 583。本仓库自己再加几十行就跨过去了。

**⇒ 所以修 W-107 会「暴露」W-120**:HEAD 上 W-107 的上限(4096 条)先撞上 →
**大声失败** → W-120 那条路径被完全挡住。两者必须一起做,否则就是把
「响亮的失败」换成「静默的错代码」(严格更坏)。

改法:两张表按**实际最大 temp id** 分配(pre-scan 的 `per_fn_max[fn_count-1]`
就是它);所有 bound check 改读实际容量;越界另有**响亮失败**兜底
(`temp_table_overflow` 粘滞标志 → 编译结束时 fail)。

### 新常驻门:`artifact_checks.sh` 的 `many_functions`

4100 个函数的合成文件(每个函数返回 9,main 求和)→ 期望 **36900**。
**这一个文件同时踩中两个悬崖**:4101 个函数 > 4032(旧 per-fn 上限),
且 max temp id = 65607 > 65536(旧 temp 上限)。

门里还断言「合成文件的 max temp id > 65536」—— temp id 只差 71 就越界,
合成文件一变就可能悄悄掉回去 → 那样门就变成**空门**而不报任何东西。

**造红灯(三种失效模式都被抓住):**

| 造红灯 | 结果 |
|---|---|
| 旧编译器(4096 硬上限) | ❌ 红(env:编译失败) |
| 禁掉 W-120 的 resize | ❌ 红(env:响亮守门触发) |
| 再禁掉守门 | ❌ 红(**求和 = 'MANYFUNC 0'** —— 静默错值被抓住) |

### 验收

```
全量回归:   181/181 PASS, 0 failed (203 total / 20 skip / 2 XFAIL)
自举闭环:   closure_check.sh v2.s == v3.s byte-identical ✅
产物级门:   6 PASS / 1 KNOWN-FAIL(W-113) / 0 FAIL ✅
SysV 回归:  6 PASS ✅   W-104 三方向 ABI 对拍: 3 PASS ✅
普通文件产物不变:hello / fib_renamed / struct_val_pass / nested_struct_deep /
                big_test 五个用例的 .s 与修复前**逐字节相同** ✅
```

**ACTIVE 条数:7 → 6。**

---

## v4.0.18 — W-105 (b):`&mut` 最小独占检查 · W-105.1:死 stub 删除

**2026-10-20。** ACTIVE 条数 6 → 4。

### 上一版 (b) 失败的真根因,是 W-107 —— 不是「infer_type 的帧布局」

台账记着:上一版最小实现(在 sema 的 `infer_type` 里记录借用)**做出来了,但让
自举编译器 SEGV** —— 崩溃点是「帧偏移 ≈ -515KB 的写」,当时的结论是
「infer_type 是递归热路径,加局部变量后帧布局位移,机制未定位」。

**2026-10-20 修 W-107 时,这个症状被认出来了** —— 「帧偏移 ≈ -515KB 的写」
正是 W-107 的签名:

```
local_t = global_t - base_t        ← 查表失败时退化成「全局 temp id」
帧偏移 = -(32 + local_t*8) ≈ -515KB
```

W-107 的机制:五张 per-fn 表按**固定上限 1024**分配 → 函数数超过 1024 的那些
函数**被丢弃** → per_fn_max 保持 0 → local_max 被钳成 0 → 帧算成 8 字节 →
局部变量冲出帧。

**上一版尝试恰好加了几个顶层函数**(把 main.jhyy 从 1022 推到 1025+)
⇒ **跨过了 1024 那道悬崖** ⇒ SEGV。**它撞的是 W-107,跟 infer_type 是什么
函数没关系。**

⇒ W-107 改成**按实际函数数分配**之后,这条阻塞**自然消失** ✓
⇒ 本次(b)在**同一个位置**(`infer_type` 的 NODE_ADDR_OF 分支)重做,**一次通过**。

### 做了什么(plan of record 的选项 A)

| 位置 | 内容 |
|---|---|
| `sema.jhyy` `SemaContext` | 加 3 个字段(`borrow_recs` / `borrow_rec_n` / `borrow_rec_cap`)—— **字段顺序必须与 struct literal 逐字一致**(漏字段 = 越界) |
| `sema.jhyy` `sema_record_borrow` | 记录一条借用 + 查冲突。**比名字不比指针** —— jhyy 的每个 IDENT 节点有**自己的** Sym(同名不同实例),比指针的话冲突检查恒不触发 |
| `sema.jhyy` `infer_type` | NODE_ADDR_OF:`&mut x`(x 是局部变量)→ 记录借用;NODE_BLOCK:进 block 记 mark、出 block 回卷 ⇒ **借用作用域 = 一个 block** |
| `sema_init` | 分配借用记录表(512 条);**满了响亮报错**,不静默丢 |

**检查规则:** `&mut x` 而 x 已有活的 `&mut` → 冲突。共享 `&x` 按 spec §2.2 是
POINTER(v1.x 语义)不是借用 ⇒ 不记录 ⇒「`&mut` 与 `&` 互斥」在 v3.1.0 根本
表达不出来(spec §4.1 也这么列)。reborrow / 字段 / 下标不记录(spec §4.1)。

**⚠️ 已知限制(诚实登记):** 词法作用域,不是 NLL —— borrow 提前结束的情况会
**误报**(`let y = &mut x; *y = 1; let z = &mut x;` 会被拒)。真正的
NLL/Polonius 在 backlog 的 **v4.3.0**。

### W-105.1 —— 死 stub 直接删

`check_cap_pass`(恒 return 1)grep 全 `compiler/src0` —— **零调用点**。
函数体 + 那 16 行「已知限制」注释一并删掉,原位置留一份「将来要做什么」的
清单。**零行为变化** ✓。

两个 stub 的处置不同,理由也记在台账里:`check_cap_pass` 没人调 → 删;
`check_borrow` 每个函数声明都调 → 走「实现最小检查」而不是删。

### 验收

```
新测试 borrow_mut_conflict.jhyy(EXPECT-ERROR):编译**失败** ✓
    「cannot borrow this variable as mutable more than once at the same time」
    (修复前:编译成功 —— 两个 &mut 真的指向同一个变量)
borrow_mut_write.jhyy(单个 &mut 写内存):仍 EXIT=5 ✓
borrow_check_basic.jhyy:特征化段使命完成,正向断言搬到新文件 ✓
全量回归:  182/182 PASS, 0 failed (204 total / 20 skip / 2 XFAIL)
自举闭环:  closure_check.sh v2.s == v3.s byte-identical ✅
产物级门:  6 PASS / 1 KNOWN-FAIL(W-113) / 0 FAIL ✅
断言审计:  零信号违规 0 ✅
```

**ACTIVE 条数:6 → 4。**

---

## v4.0.18(续)—— W-118 语言 lexer 的 EOF 守卫 · W-121 产物可复现 · W-122 side-file 泄漏

**2026-10-20。** ACTIVE 条数 4 → 3。

这一轮的起点是 W-118(语言 lexer 的 `lex_peek_char` 无 EOF 守卫),但它带出了
**两个新发现** —— 都是「门本来就在跑、只是没人从那个角度看过」。

### W-118 —— lexer 的 EOF 变成显式的(**防御性**修复)

`Lexer` 加 `end: *u8` 字段,`lex_peek_char` / `lex_peek_char_at` 加
`current >= end → return 0` 守卫(跟 IL lexer 的 W-117 同款结构)。

**⚠️ 这条从来没有观测到危害** —— 正常路径上 `read_file` 保证 NUL 终止,
lexer 到不了边界之外。所以这是**防御性**修复:把「EOF 是隐式的」变成显式的。
**它不是一次「修好了某个可见故障」** —— 别把它当成那种修复来读。

**A/B 实证(本 entry 早就写下的验收条件):** 修复前 vs 修复后的编译器,对
`compiler/tests/examples/*.jhyy` 逐个编译比 `.s`:

```
A/B(closure 名归一化后):逐字节相同 193 / 不同 0 / 编译失败 8
```

⇒ **输出中性 ✓**(8 个「失败」是两个编译器都失败的 expect-error 类用例 ✓)。

### W-121 —— 合成 closure 的符号名依赖堆地址 ⇒ 产物不可复现

A/B 报「4 个 .s 不同」,顺着查下去发现:**根因不是 W-118**,是 closure 的合成
符号名 `__closure_<N>` 的 `N` 取自 **closure 节点的堆地址** ⇒ ASLR ⇒
**同一个编译器连编两次,`.s` 就已经不同**:

```
<   call __closure_44756          >   call __closure_08251
```

**为什么以前没人发现:** 现有门比的是**两个不同代**的编译器(v2 vs v3),而它们
的布局恰好一致(同一份源码、同一套分配序列)⇒ 地址相同 ⇒ 名字相同 ⇒ 门是绿的。
只有「同一编译器跑两遍」才露馅。

修法:`N` 改用 SemaContext 里的**单调计数器** ⇒ 名字只跟「第几个 closure」有关,
与内存布局无关 ✓。验收:同一编译器连编三次 `.s` → 3 个**相同**的 sha ✓。

**这条值得单独强调:它破坏的是 D26 的 byte-equal 性质** —— 任何含 closure 的
源文件,「同一输入两次编译逐字节相同」这个假设**当时是不成立的**。

### W-122 —— 四个 side-file 用固定路径 ⇒ 上一次编译的内容泄漏到下一次

A/B 脚本用 `--no-link` 批量编译(freestanding / `#[no_std]` 用例会写
`_no_std.flag`)之后,紧接着的 `make` 拿 **no_std 的链接行**
(`-nostartfiles -nodefaultlibs`)去链一个**正常**程序 ⇒ **链接失败** ⇒
整个 build 挂掉。

根因是**生命周期错位**:那四个文件(`_no_std.flag` / `_inline_asm.buf` /
`_section_directive.buf` / `_fence.buf`)本意是「**本次**编译写 → **本次**编译读」,
但固定路径意味着一次编译**没走到读的那一步**(`--no-link` 不链)它们就留在盘上
⇒ 下一次编译把上一次的内容当自己的用。

**⚠️ 这正是 `version-schedule.md` § D3 记的那件事** —— 那一节写的是
「机制成立但**未观测到发作**」;今天它**发作了** ✓。

修法:每次编译**开头**先把这四个删干净(本次需要的话 codegen 会重新写 ✓)
——「陈旧」在物理上不再可能。**造过红灯:** 旧编译器两步 → 链接失败 ✗;
新编译器同样两步 → hello 正常链出 EXIT=42 ✓。

### 验收

```
全量回归:   182/182 PASS, 0 failed (204 total / 20 skip / 2 XFAIL)
自举闭环:   closure_check.sh v2.s == v3.s byte-identical ✅
产物级门:   6 PASS / 1 KNOWN-FAIL(W-113) / 0 FAIL ✅
SysV 回归:  6 PASS ✅   W-104 三方向 ABI 对拍: 3 PASS ✅
A/B:        193/193 逐字节相同 ✅
```

**ACTIVE 条数:4 → 3。**

---

## v4.0.18(续)—— W-113:`asm!` / memory barrier 内联进函数体(死字节变真指令)

**2026-10-20。** ACTIVE 条数 3 → 2。

### 症状:asm 字节落在**所有函数之外**

`asm!` 的文本之前由前端写进 side-file(`_inline_asm.buf`),`main.jhyy` 在链接前
把它拼接到 `.s` 的**末尾** ⇒ asm 字节落在**所有函数之外** ⇒ 是**死字节**,
永不执行(spec supplement v3.0.1 § 6 记的「appended 到 .s 末」)。

**⚠️ 顺带发现:`fence_*` 走的是同一个 side-file ⇒ `mfence` / `lfence` / `sfence`
也从来没执行过。** 对一个多核程序,这是**正确性**问题 —— 内存屏障不存在。

spec 的 § 6 roadmap 写明「要 inline 调用 asm,需要 v3.1+ 加 operand constraints
+ **placement tracking**」—— placement tracking 就是这一条。

### 做法

| 层 | 内容 |
|---|---|
| 前端 `codegen.jhyy` | `asm!` / `fence_*` 的文本**hex 编码**成一条 IL 指令 `dbgasm <hex>` 写进 IL(不再是写 side-file) |
| IL lexer | 认 `dbgasm` → ILTOK_DIRECTIVE(复用 dbgfile/dbgloc 的同款 token)。⚠️ **必须**调 `lex_finish_instr` —— dbgfile/dbgloc 不调它(它们不需要 token 文本),dbgasm 需要(后端要从 `tok.text` 取 hex) |
| 后端 | `emit_raw_asm_inline`:hex 解回原文,**原样写进 .s**(在函数体内部 ✓) |

**为什么 hex 而不是原样写进 IL:** IL 是**按行**的文本格式,而 asm 文本可能含
换行 / 引号 / 反斜杠 —— hex 一次性消掉这三个问题 ✓(跨平台也稳)。

### 验收

```
产物级门 artifact_checks.sh `asm_before_ret`(objdump 判位置):
    修复前:KNOWN-FAIL(「没有任何函数体包含它」)
    修复后:**PASS** ✓ ⇒ KNOWN_FAIL 里那行已删 ⇒ 升级成**真门** ✓
产物级门总计:7 PASS / 0 KNOWN-FAIL / 0 FAIL ✅(W-113 是最后一条 KNOWN-FAIL)
内存屏障:实测 .s 里 mfence/lfence/sfence 紧跟函数序言 ✅(之前在 .s 末尾)
全量回归:  182/182 PASS, 0 failed ✅
自举闭环:  closure_check.sh v2.s == v3.s byte-identical ✅
SysV 回归: 6 PASS ✅   W-104 三方向 ABI 对拍: 3 PASS ✅
```

**ACTIVE 条数:3 → 2。**

---

## v4.0.18(续)—— W-115:闭包捕获外层变量 → 编译期明确报错(W-089 的 reproducer 转 PASS)

**2026-10-20。** ACTIVE 条数 3 → 2 → **1**。

### 根因:不是 W-089,是**闭包捕获**

台账记的是「W-089 标着 RESOLVED,但它自己的 reproducer 至今 STACK_OVERFLOW」。

**逐 sub-test 二分定位**(每个中间版本都真编译 + 真跑):

```
N=1..6: exit=0                                     ← 前 6 个 sub-test 全绿
N=7:    exit=3221225725 (0xC00000FD = STACK_OVERFLOW)  ← 崩溃在第 7 个
```

第 7 个 sub-test 是闭包:`let f = |x: i32| { ptr_add(buf, x) };` —— 它
**捕获了外层的 `buf`**。生成的 .s 把坏在哪显示得很清楚:

```
make_closure:
    movl $8, -40(%rbp)
    movl -40(%rbp), %ecx     ← 只传了 x
    call __closure_00000     ← **没有传 env** ✗
__closure_00000:
    movl %ecx, -32(%rbp)     ← 32 位存 env 指针(截断)✗
    call ptr_add             ← **一个参数都没设** ✗
```

**⇒ 根因:闭包的 env 机制压根没实现** —— 合成 fn `__closure_N` 的调用约定里
**没有 env 参数**(sema 建的合成 fn 只有用户的参数),env 从来没被传进去 ⇒
闭包体读外层变量读到垃圾指针 ⇒ 运行时炸。

**而「闭包不能捕获外层变量」一直只是注释里的约定**(sema 的闭包分支写着
「M0: body 仅用 params + literals, 不引用 outer vars」)—— **没有任何检查**
⇒ 编译器给捕获了外层变量的闭包**生成坏代码** ✗。

### 修法:不实现捕获,改成**编译期明确报错**

闭包捕获在 v3.2.1 的 MVP 范围里**明确排除** ⇒ 实现它是 feature 工作
(backlog),不属于「清零 ACTIVE」。本轮做的是**把「静默生成坏代码」换成
「编译期明确报错」**:

- `SemaContext` 加 `in_closure` 标志(闭包体检查期间为 1)
- `NODE_CLOSURE_LITERAL` 分支:检查闭包体期间置位,结束后恢复
- `NODE_IDENT` 分支:在闭包里,若该 sym 是变量且**不在当前作用域**(闭包自己的
  作用域 = 参数 + 闭包体内局部变量)⇒ 它来自外层函数 ⇒ 一次**捕获** ⇒ 报错:
  `closure cannot capture outer variables (not supported yet)`

### 测试的处置

W-089 的 reproducer 里那个闭包 sub-test **移出**到新文件
`closure_capture_unsupported.jhyy`(EXPECT-ERROR)—— W-089 的 reproducer 验的
是「call 返回类型的 semantic lookup」,闭包不在它的射程里 ✓。

**⇒「W-089 已 RESOLVED」这句话现在有证据支撑** —— 它的官方 reproducer 跑通了 ✓。

### 验收

```
新测试 closure_capture_unsupported.jhyy(EXPECT-ERROR):编译**失败** ✓
    (修复前:编译**成功**,运行时 STACK_OVERFLOW)
W-089 的 reproducer codegen_call_return_types.jhyy:EXIT=0 ✅(XFAIL 摘掉)
不捕获外层变量的闭包:仍正常编 + 跑出正确值 ✅
全量回归:  184/184 PASS, 0 failed, 0 flaky ✅(XFAIL 从 2 条降到 1 条)
自举闭环:  closure_check.sh v2.s == v3.s byte-identical ✅
产物级门:  7 PASS / 0 KNOWN-FAIL / 0 FAIL ✅
```

**ACTIVE 条数:2 → 1。**

---

## v4.0.19 — 台账清零:ACTIVE 14 → **0** 🎉(W-106 + W-123)

**2026-10-20。** 这是本项目**第一次**把 ACTIVE 桶清空(台账 108 行:
102 RESOLVED + 4 SUPERSEDED + 2 INVALID + **0 ACTIVE** + 0 DEFERRED)。

### W-123 —— 临时文件名 seed 会**规律性**碰撞(并发编译随机失败的真凶)

`jh_mktemp_ascii` 的 seed = `GetCurrentProcessId() ^ GetCurrentThreadId() ^ ++ctr`,
注释写「collision vanishingly rare」—— **那个结构会规律性地撞**:

- Windows 的 **process id 与主线程 thread id 来自同一个全局计数器**
  ⇒ 一个新进程常见的 (pid, tid) 形态是 **(N, N+1)**
- ⇒ `N ^ (N+1) = 1`(N 为偶数时)⇒ **每两个并发进程就撞一次同一个临时文件名**
- ⇒ 两个并发编译抢同一个临时名 ⇒ 后一个的 rename 失败 ⇒ **编译失败**

「4 billion combos」那个论证把**输出空间的大小**当成了保证 ——
但**映射到输出空间的函数不是单射** ✗。

**复现:** 并发编译 32 个文件 → **4 个失败**,报「W-048: rename temp exe failed
(kept at ...\Temp\jhe0000000e.exe)」—— 两次失败的临时文件名**一字不差**
(`0000000e` = seed 14 = 1 ^ 15)。

**修法:** ① 换掉裸 XOR,用**乘法混合**(Knuth multiplicative hash)把
pid / tid / 计数器 / 时钟揉成一个 32 位值;② **真的独占创建一次**
(`CreateFileA` + `CREATE_NEW`),名字被占了就让内核拒绝、换 hash 重试 ⇒
**「唯一」由文件系统保证**。

修复后:同样的压力 → **0 失败** ✓。

### W-106 —— 那处「每次 symbol lookup 白造一个 StringBuilder」删掉了

**这一条的价值在于:它洗清了一个被误判了两年多的 workaround。**

2026-10-18 的对照实验:「删掉这三行 ⇒ 全量回归偶发失败(2/3,后来记为 1/11)
⇒ 它在承重 ⇒ 不能删」。**那个实验归错了因** —— 偶发失败的真凶是 **W-123**
(临时名碰撞 ✗),而那个 workaround 只是**改变了时序** ✗(让另一个 bug 撞上了
而已 ✗)。

⇒ **⇒ 那个 workaround 的「承重性」从来就不存在** ✓ —— 删掉它 ⇐ W-123 真修 ⇐
两个 bug 各自归位 ✓。

**方法论沉淀(比修复本身更值钱):** 「删掉 X ⇒ 偶发失败 ⇒ X 承重」这个推理链
**只在一个前提下成立**:那个偶发失败是**由 X 引起的**。本例里不是 —— X 只改变
了时序。**所以「删掉试试」的实验必须配合「失败症状的归因」** ✓:
本例的关键是症状是「**compile failed**」而不是「算错」——
**编译期失败**指向「编译过程本身出了问题」(临时名 / 旁路文件 / 并发),
而「算错」才指向「生成的代码有问题」⇒ 方向完全不一样 ✓。

**验收:**

```
并发压力:  32 个并发编译 → 0 失败 ✅(修复前 4 个)
全量回归:  184/184 PASS, 0 failed, 0 flaky ✅
自举闭环:  closure_check.sh v2.s == v3.s byte-identical ✅
产物级门:  7 PASS / 0 KNOWN-FAIL / 0 FAIL ✅
SysV 回归: 6 PASS ✅   W-104 三方向 ABI 对拍: 3 PASS ✅
```

### v4.0.18 那一轮清掉的(W-113 / W-115 / W-118 / W-121 / W-122 / W-105 / W-105.1)

见上文各节。**14 → 0** 的完整名单:
W-104 / W-112 / W-113 / W-114 / W-115 / W-118 / W-120 / W-121 / W-122 / W-123 /
W-103 / W-105 / W-105.1 / W-106 / W-107。

**⇒ ACTIVE 桶清空。** promote 条件的实测(2026-10-20):

| 门 | 结果 |
|---|---|
| `regress jhyy.exe` | ✅ 184/184 PASS + 20 SKIP |
| `regress jhyy_v2.exe`(**自举产物也跑**) | ✅ 184/184 PASS + 20 SKIP |
| `closure_check.sh` | ✅ v2.s == v3.s byte-identical |
| `fixed_point.sh` | ✅ 17 PASS / 0 FAIL / 0 INFO(跑到 N=10) |
| `make selfhost` | ✅ v2..v5 逐字节相同 |
| `artifact_checks.sh` | ✅ 7 PASS / 0 KNOWN-FAIL / 0 FAIL |
| SysV 回归 + W-104 三方向 ABI 对拍 | ✅ 6 PASS + 3 PASS |
| CI | ✅ 全绿 |

⇒ **v4.0.0 final 的 promote 条件已全部满足。**

---

## v4.0.19 — 已发布(2026-10-20)🎉

<https://github.com/JiHuiYiYou/JiHuiYiYou-compiler/releases/tag/v4.0.19>

**台账 ACTIVE 桶首次清空(14 → 0)** —— 102 RESOLVED + 4 SUPERSEDED + 2 INVALID +
0 ACTIVE + 0 DEFERRED(108 行)。

**promote 条件的实测:**

| 门 | 结果 |
|---|---|
| `regress jhyy.exe` | ✅ **184/184 PASS** + 20 SKIP |
| `regress jhyy_v2.exe`(**自举产物也跑**) | ✅ **184/184 PASS** + 20 SKIP |
| `closure_check.sh` | ✅ PASS,v2.s == v3.s byte-identical |
| `fixed_point.sh` | ✅ **17 PASS / 0 FAIL / 0 INFO**(跑到 N=10) |
| `make selfhost` | ✅ v2..v5 逐字节相同 |
| `artifact_checks.sh` | ✅ **7 PASS / 0 KNOWN-FAIL / 0 FAIL** |
| SysV 6 个回归 + W-104 三方向 ABI 对拍 | ✅ 6 PASS + 3 PASS |
| CI | ✅ 全绿 |

**发布链:** tag push → `ci.yml`(needs: build-and-test)→ `release.yml`
(reusable workflow)→ 出 installer .exe + compiler .msi + vscode .vsix + SHA256.txt
⇒ **门不绿就发不出去** ✓(这条链修好后 v4.0.9-rc1 与 v4.0.19 连续两次成功)。

---

## v4.0.20 — 审计「skip test / 新增 test」:三处**门**的问题(W-124 / W-125 / W-126)

**2026-10-24。** 起因是一次针对「SKIP 用例」与「新增用例」的审计。三个问题
**都是门的问题**,不是功能的问题 —— 门绿着,但它没在验它声称在验的东西。

### W-126 — regress harness 的 `EXPECT-ERROR` 漏洞:编译意外成功时判 PASS

`run_test` 只在「编译失败」(`rc != 0`)分支检查 `// EXPECT-ERROR:` 的关键词;
编译**意外成功**时一路落到 `if expected is None:` 分支 —— 那个分支只查
「进程是不是 NTSTATUS 崩溃」,不崩就算过 ⇒ 报 **PASS**,还进汇总行的「全部有断言」。

实测(探针,已删):
```
// EXPECT-ERROR: "zzz-this-keyword-never-appears-zzz"   ← 一个能正常编译的程序
→ PASS  _probe_expect_error.jhyy   EXIT=1
```
同形状的探针(把 `borrow_mut_conflict.jhyy` 的双 `&mut` 冲突去掉、指令原样不动)
→ 一样 PASS。

**危害:** 凡是「靠编译期报错兜住」的测试**都不会变红** —— 编译器哪天不再报那个错,
门照样绿。套件里 8 个 `expect-error` 测试全在射程内,其中 2 个是最新加的门:
`borrow_mut_conflict.jhyy`(W-105(b) 的 `&mut` 独占检查)与
`closure_capture_unsupported.jhyy`(W-115 的闭包捕获)。

**修法:** `rc == 0` 且 `expect_error_kw` 非空 ⇒ 直接 FAIL
(「编译失败但没有那个关键词」本来就 FAIL;补的是「编译成功」这一侧)。
**同一个探针当场由绿转红** ✓。

### W-124 — `#[no_std]` 从「零覆盖」变成「有门」

两个问题叠在一起,让 `#[no_std]` 这个 v3.0 ship gate **从来没有真正跑过**:

1. **链接行指向不存在的 entry 符号。** 链接行写的是 `-Wl,--entry=main_jhyy`,
   旁边的注释还宣称「codegen 把用户的 `fn main` 发成 `main_jhyy`」——
   **代码从来没这么做过**:codegen 按函数名原样发符号,用户的 `fn main` 就是 `main`。
   ⇒ no_std 程序 **100% 链不过**:
   ```
   ld: warning: cannot find entry symbol main_jhyy; defaulting to ...
   ld: undefined reference to `___chkstk_ms'
   ```
   第二个错是 `-nodefaultlibs` 的连带后果:self-backend 对 >4KB 的栈帧会发
   `call ___chkstk_ms`(W-074.6 sub-bug #3 修的),而那个符号在 CRT 里。
2. **没人跑它。** harness 只认 `fn main_jhyy` 当入口,而 `#[no_std]` 程序的入口
   按 sema 强制要求是 `fn main`(`sema.jhyy:3160`)⇒ `no_std_hello.jhyy` 被判成
   「library」→ **静默跳过**,从来没编过、更没跑过。

**修法:**
- 链接行 = `-nostartfiles -nodefaultlibs -Wl,--entry=main -lgcc`
  (`-lgcc` 提供 `___chkstk_ms`,且**不含** C 运行时 —— 这正是 freestanding 的
  标准做法:`-nostdlib` + 显式 `-lgcc`);
- 入口返回值语义:PE 入口函数返回的值**就是**进程退出码 ⇒ `fn main` 返回 42 ⇒
  退出码 42(**实测**,不是推测);
- harness + 审计脚本都改成认 `#[no_std]` 的 `fn main` 入口;
- 用例加 `// EXPECT: 42`,返回值改成推导式(`20 + 22`)而非字面量。

**⚠️ 附带规避(根因未根治):** `#[no_std]` 用例**串行**跑。编译器的 4 个 side-file
走**固定路径**通道(codegen 写 → link 读)+ 每次编译开头删干净 ⇒ 两个并发编译
会互相删对方的 side-file(根因见台账 W-122 的余量)。⇒ harness 把 `#[no_std]`
用例从并发池里拿出来,等并发池跑完再串行跑。

### W-125 — chained `&&T` 的报错路径:sema 那条规则是**死代码**

`let x: &&i32 = 0 as &&i32;` 此前报的是:
```
error: expected =, got &&
error: unexpected token '&&' in expression
error: expected ;, got ident
error: expected type name, got &&      ← 对用户毫无意义
```
**根因:** lexer 把 `&&` 切成**一个** `TOKEN_AMPAMP`,而 `parse_type` 的 borrow
分支只认 `TOKEN_AMP` ⇒ type 位置的 `&&i32` 压根不进 borrow 分支,落到
default ident 路径 ⇒ 报「expected type name」。

**连带后果(比症状本身更重要):**
1. `sema.jhyy:469` 那条真正的规则「chained `&&T` not allowed (borrow is terminal)」
   **永远走不到** —— 那条规则是**死代码**,从没被执行过,也就从没有被验证过;
2. `borrow_check_err.jhyy` 因此长期挂 XFAIL —— 而 **XFAIL 是已知 bug 的藏身处**:
   台账写着「ACTIVE = 0」,测试套件却自报「1 个已知失败」,两边**长期并存却没人
   对起来**。⇒ **「台账清零」不等于「没有已知 bug」**。

**修法:** parser 在 type 位置显式拦 `&&`,措辞与 sema 的规则对齐
(与既有的 `&mut &mut T` / `volatile volatile` 同一模式:parser 拦一道,
sema 兜底)。⇒ XFAIL 摘掉 → **PASS**,**套件 XFAIL 数 1 → 0**。

### 顺带修的

- `sysv_full_regress.sh` 的用例名单从 5 个补到 **6 个** —— CI 的 sysv job 早就在
  跑 6 个,本地脚本还停在 5 个 ⇒「本地绿、CI 红」的对不齐;
- CI 的 job 名 `SysV ABI (5 tests ...)` → `6 tests`;
- **本机 Docker:** Docker Desktop 起 daemon 后,`regress.py --cross=auto` 从 `none`
  解析成 **docker** ⇒ 6 个 sysv 用例**本地也真跑**(exit=28/217/42/35/18/42)。

### 门(2026-10-24 实测)

| 门 | 结果 |
|---|---|
| `regress jhyy.exe` | ✅ **186/186 PASS** + 0 XFAIL + 19 SKIP(205 total) |
| `regress jhyy_v2.exe`(自举产物也跑) | ✅ **186/186 PASS** + 0 XFAIL + 19 SKIP |
| `regress --cross=auto`(本机 docker) | ✅ 6 个 sysv 用例全 PASS |
| `sysv_full_regress.sh --runs=1` | ✅ **6/6 PASS** |
| `make selfhost` | ✅ v2.s == v3.s == v4.s == v5.s 逐字节相同 |
| `closure_check.sh` | ✅ PASS |
| `fixed_point.sh` | ✅ PASS |
| `artifact_checks.sh` | ✅ PASS |
| SysV ABI 三方向对拍 | ✅ 3 PASS |
| `audit_test_assertions.py --strict` | ✅ 0 违规 |
| 台账 | ✅ **0 ACTIVE / 0 DEFERRED** / 111 索引行(108 + W-124/125/126) |

**⇒ ACTIVE 桶仍然清空**(本轮三条全是 RESOLVED:一个门坏了(修门)、一个功能坏了
(修功能 + 补门)、一个规则是死代码(把规则接上 + 把门打开))。

### W-131 / W-132 —— 「图标全没了」:v4.0.8 起 jhyy.exe 不再带图标资源

**2026-10-24。** 用户报「我的文件图标没了」。查下来**不是** Explorer 设置、也
**不是**图标缓存坏了 —— 是 **`jhyy.exe` 这个二进制自己不带图标资源**,而 `.jhyy`
文件的图标恰恰是从它身上取的。

**取证(三条互相独立的证据):**
1. 注册表 `HKCR\JHYY.SourceFile\DefaultIcon` = `C:\Program Files\JHYY\bin\jhyy.exe,0`;
2. `shell32!ExtractIconEx(那个 exe, 0)` = **0**(取不到);同目录 2026-09-02 的
   备份 = **2**(32×32,有);
3. 该 exe 的 sha256 == HEAD 提交的 `compiler/build/bin/jhyy.exe`
   ⇒ **装出去的就是提交进仓的那份**,不是安装过程弄坏的。

**根因:** 嵌图标的 windres 步骤**只在 C 侧编译器**里
(`compiler/src/main.c:503-558`)。v4.0.8(commit `1dc6a23`,2026-10-16)把 jhyy.exe
的产出改到**自举编译器**,而自举侧一行 windres 逻辑都没有 ⇒ 从那以后每个
jhyy.exe 都不带图标资源。

历史扫描(30 个已提交版本逐个 `ExtractIconEx`)给出的分界线非常干净:
`a710320`(10-15)及之前 → 有图标;`1dc6a23`(10-16,v4.0.8)及之后 → 无图标。

**两个修法:**
- **W-131(文件图标)**:安装器的 FileAssoc `DefaultIcon` 改指**独立**的
  `[INSTALLDIR]bin\jhyy-icon.ico`(`JhyyIconFile` 组件本来就装它),不再依赖
  「exe 里有没有图标」这件事。已装机器的即时恢复:写 HKCU 影子键
  (`HKCU\Software\Classes\JHYY.SourceFile\DefaultIcon`)+ `ie4uinit` 刷图标缓存。
- **W-132(编译产物的图标)**:自举链接路径补 windres 步骤 ——
  `compiler/src0/jhyy_helpers.c` 新增 `jh_build_icon_obj()`(整个做在 C 侧),
  由 **`jh_gcc_invoke()`(链接命令的构造点)把 .o 插进链接行**,`jh_run()` 在链接
  结束后删掉它。**`main.jhyy` 一个字节都没动** —— 见下面那条教训。

**为什么 W-132 整个做在 C 侧、且 `main.jhyy` 一个字节都不动**:两条理由,第二条
更要命。

1. jhyy 语言**没有 1 字节标量类型** —— `*i32` 存是 **4 字节**(实测:写 0x41 之后
   按 i32 读回来是 0x414141),逐字节的活儿(路径转正斜杠、换临时文件后缀)在 `.jhyy`
   里做会把相邻 3 字节连带清成 NUL ⇒ 路径直接被截断;
2. **给 `main.jhyy` 新增任何局部变量都会移位模块级 temp 编号 ⇒ 自举产物的行为会
   漂移。** 实测:往 `link_with_gcc` 加 36 行 ⇒ 同一个编译器编出的 `main_jhyy` 里,
   那段 argv 扫描的 `movzbl (%r8)`(1 字节读)从 **2 处变成 0 处** ⇒ `--target=`
   不再被识别 ⇒ "cannot open file" ⇒ 6 个 sysv cross 用例全红 + artifact 门 7/9 红。
   ⇒ `main.jhyy` 是当前编译器里「加一行就可能自伤」的文件(用户代码注释里那条
   「自举产物行为漂移」说的就是它)⇒ **图标这条链全部落在 C 侧**。

三个**实测**出来的约束(都写进了代码注释):
1. **windres 的 `-i`/`-o` 路径必须用正斜杠** —— windres 走 gcc -E 预处理,gcc -E
   把 '\' 当转义符:`C:\Users\x.rc` → `C:Usersx.rc`;
2. **`.ico` 要先拷到纯 ASCII 临时路径** —— mingw CRT 的 argv 走 CP_ACP,中文路径
   会变 mojibake(W-048 同款);
3. **`SOURCE_DATE_EPOCH` 必须在 windres 之前设好** —— 否则 .o 的时间戳破坏 D26
   逐字节可复现。

还有一条:`system()` 不行 —— cmd.exe /c 遇到**以引号开头**的命令行会把外层引号
吃掉(报「文件名或目录名语法不正确」),必须走 `jh_run`(CreateProcessA)。

**新门:** `compiler/tests/bootstrap/artifact_checks.sh` 加两道常驻门 ——
`compiler_icon`(jhyy.exe 自己带图标)+ `program_icon`(编出来的程序带图标),
都用 **Explorer 同一套 API**(`shell32!ExtractIconExW`)问「这个 exe 里到底有没有
图标」,而不是猜 `.rsrc` 节在不在。

**验收:** jhyy.exe 与它编出来的 exe,`ExtractIconEx` 都从 0 变成 2 ✓;两道门都
PASS ✓;`.jhyy` 文件在 Explorer 里恢复显示 "J" 图标 ✓。

---

### W-127 / W-128 / W-129 / W-130 / W-133 —— 重写 v4 ABI / spec 时挖出的五个编译器缺陷

**2026-10-24。** 本轮的主线是**重写** `docs/abis/` 的 ABI 与语言规范(v4.0.0),
重写时逐条对照实现,**挖出五个编译器缺陷** —— 三个是编译器 bug,两个是
「编译器自身」的缺陷。全部**真修**(不是绕开)。

| W-NNN | 一句话 |
|---|---|
| W-127 | Windows 目标下整数 / 浮点实参**共用一个位置计数器**(MS x64 ABI),旧实现给浮点单独计数 ⇒ 浮点参在前时整数参**读错寄存器** |
| W-128 | `0o` / `0b` 字面量**静默算成 0**(lexer 认前缀,求值却走 `strtoll(base=0)`) |
| W-129 | `alignof(T)` 表达式**无类型**(sema 里只有 `NODE_SIZEOF` 分支)⇒ 报「type mismatch in let」 |
| W-130 | address-holder bitmap 的**容量**在 C 桥接层与 jhyy 侧脱节 ⇒ 编译器**自己的** `--target=` 前缀判定失效 |
| W-133 | `==` / `!=` 对 `struct` / `enum` / 数组是**身份比较**(比地址)不是值比较 ⇒ 字段完全相同的两个 struct 判 `false` |

**W-130 —— 数字闭合的根因链。** 这个最值得记,因为它**跨了两次改动**:

1. C 侧 `jh_cgstate_set/get_holds_flag` 把 `idx >= 65536` **硬编码**拒绝;
2. jhyy 侧 `cg_resize_temp_tables` 已把同一张 bitmap **动态扩到**
   `max_temp_id + 1 + 4096`(可以 > 65536)⇒ **两边脱节**;
3. ⇒ temp id ≥ 65536 的 address-holder 标记**写不进去**;
4. ⇒ `emit_loadsub`(**唯一**查这张 flag 的 load 路径)退化成「读栈槽里指针的
   **低字节**」⇒ 编译器**自己**那段 9 字节 `--target=` 前缀比较失效
   ⇒ "cannot open file" ⇒ 6 个 sysv cross 用例全红;
5. 数字:好产物里「最高间接字节读的 base temp」= **65477**(距悬崖 59);
   +W-127(+18 temp)→ 65495 OK;+W-128(+50)→ 65527 OK;
   **+两者(+68)→ 65545 ≥ 65536 ⇒ 坏**。

⇒ 也就是说:**W-127 / W-128 这两个「无害的修复」恰好把源码推过了悬崖** ——
修 bug 修出了新 bug。修法:C 侧加**容量通道**
(`jh_cgstate_set_holds_table(bitmap, cap)` 原子地装指针 + 容量,越界返 **-1 哨兵**)
+ jhyy 侧**粘滞标志 + 编译末尾响亮失败** + **3 道常驻门**。

> ⚠️ 记一笔:第一轮 `make` 报 **SELFFAIL** 是**预期内**的 —— 改了 codegen 行为,
> 锚点编译器编出来的产物与新编译器自己的产物必然不同 ⇒ 需要**两步自举**
> (把 `_boot_new.exe` 装成 `jhyy.exe` 再 `make`)。

**W-133 —— 规范本身的空白。** 两份旧规范**都没写**聚合类型 `==` 的语义:
旧 lang-spec 没写;旧 ABI 的「结构体相等性 / 枚举相等性」讲的是**名义类型相等性**
(两个 struct 类型是不是同一个类型),**不是** `==` 运算符。⇒ 这是**规范空白**,
不是回归。根因三处叠加:sema 对比较运算符**零类型约束** + `qbe_type_of` 对聚合
无分支(默认 `'w'`)⇒ `ceqw` 比的是两个**槽地址的低 32 位** + `KIND_ALIAS`
**全仓无人解包**。

修法:新增 `cg_value_eq`(struct 逐字段递归 / enum 比 tag + 按变体类型比 payload /
数组逐元素 / slice 比头)+ sema 拆两支 + **顺带真修标量浮点 `==` 的 NaN 语义**
(`ucomisd` + 纯 `setcc` 只读 ZF ⇒ unordered 时分不清「相等」⇒ **`NaN == NaN`
恒为 true(错)**;现在加 `setnp` / `setp` 有序守卫 ⇒ 有 NaN 参与时 `==` 为 `false`、
`!=` 为 `true`,符合 IEEE 754)。

**语义决策(用户拍板):** slice 的 `==` 比**头**;聚合的 `<` `>` `<=` `>=`
**编译期报错**;enum 各变体 payload 类型不一致 → per-variant 掩码 dispatch;
标量浮点 `==` 的 NaN 语义**本次一起修**。

**新门:** `artifact_checks.sh` 加 3 道(W-130 的 holds_cap_source / holds_bitmap /
selfhost_target_flag);`compiler/tests/examples/` 加 **14 个**用例
(W-127 / W-128 / W-129 各 1 + W-133 的 9 个聚合用例 + `float_nan_eq` +
1 个 sysv 交叉用例)。

**门(2026-10-24 实测):**

| 门 | 结果 |
|---|---|
| `regress jhyy.exe` | ✅ **200/200 PASS** + 0 XFAIL + 19 SKIP(219 total) |
| `regress --cross=auto`(本机 docker) | ✅ **7 个** sysv 用例全 PASS(exit=28/217/42/35/18/42/**170**) |
| `closure_check.sh` | ✅ PASS(v2.s == v3.s,byte-identical) |
| `fixed_point.sh` | ✅ 17 PASS / 0 FAIL / 0 INFO(N=10 .il 与 .s 跨代 byte-equal) |
| `artifact_checks.sh` | ✅ 12 PASS / 0 KNOWN-FAIL / 0 FAIL / 0 SKIP |
| `artifact_checks.sh --selftest` | ✅ 8/8 |
| `audit_test_assertions.py --strict` | ✅ 0 违规 |
| 台账 | ✅ **0 ACTIVE / 1 DEFERRED** / 123 索引行(DEFERRED 1 条 = W-134.1;W-133.1/.2/.3 是**设计边界** ⇒ 归 SUPERSEDED,不入高优桶) |

---

## v4.0.21 — W-136 side-file per-pid 唯一化 · W-137 Makefile 变量漏改 · 台账归零

**2026-10-25。** 起因:上一个 agent 提交了 M5 Part 1(删 C 端编译器)与
「MCP pytest 接进 CI」之后,在 **W-136** 上卡住 —— 它把「链接失败」的结论写成
「跟我的改动无关,是这台机器/这套 gcc 的独立问题」,代码留在工作树没提交。

**本节记录:那个结论是错的,以及为什么错成那样。**

### W-136 — side-file 用固定路径 ⇒ 并发编译互相截断/删除 ⇒ 静默错代码

编译器有三个「codegen 写 → link 步骤读」的跨阶段通道(side-file),全在
`compiler/build/obj/` 下、用**固定路径**:`_inline_asm.buf` /
`_section_directive.buf` / `_no_std.flag` / `_fence.buf`。
两个并发编译会互相踩:codegen 用 `fopen(path,"wb")` **截断**对方刚写的内容;
`main.jhyy` 编译开头「删干净」(W-122 的修法)又会把对方的文件删掉。
⇒ **静默错代码**:A 的 link 步骤读到 B 的空内容 ⇒ A 的 `.s` 少了
`#[link_section]` 的 `.section` 指令,不报任何错。

**A/B 实测(同一台机器,同一份 `#[link_section(".text.boot")]` 程序):**

| 编译器 | 8 路并发 | 12 路并发 |
|---|---|---|
| 旧(固定路径) | 6/8 保住 `.section`,**2 种不同产物** | 10/12 保住,**2 种不同产物** |
| 新(per-pid) | **8/8 保住,1 种产物** | **12/12 保住,1 种产物** |

⇒ 旧行为**静默丢掉 25% 的 `#[link_section]` 指令**。

**修法:** 路径加 **pid 后缀**(`jh_sidefile_path()`,C 侧实现)⇒ 每个进程用自己的
文件 ⇒ 结构上不可能互踩。写侧与读侧在同一进程 ⇒ 同 pid ⇒ 仍配对正确。

### 真正的根因:一行**未闭合的块注释**

W-136 的实现里,`compiler/src0/jhyy_helpers.c` 留下一行没闭合的块注释起始符,
把 `jh_cgstate_get_state` / `jh_cgstate_set_state` 两个 C 桥函数**整块吞进
注释**;同时把 `static void *g_jh_cgstate_state` 的定义删掉了。

⇒ C 文件**照样编译通过**(只有一条 `-Wcomment` 警告)⇒ 产物里**少了两个符号**
⇒ 链接期才炸 `undefined reference to 'jh_cgstate_get_state'`。

### W-137 — 为什么那条警告从没出现:`$(CFLAGS_STAGE0)` 未定义

`Makefile:26` 在 M5 Part 1(b6efe61)里把 `CFLAGS_STAGE0` 改名成 `CFLAGS_REPRO`,
**`:174` / `:178` 两条 `.o` 规则没跟着改** ⇒ 展开成空 ⇒ 两个 `.o` **不带**
`-std=c11 -Wall -Wextra -g0` ⇒ **`-Wall -Wextra` 正是会报 `-Wcomment` 的开关**,
它一丢,上一节那条警告就静默了。`CFLAGS_STAGE0` 是全 Makefile 里**唯一一个**
「用了但没定义」的变量。

**修法:** 两处改回 `$(CFLAGS_REPRO)`。顺带把 `jhyy_helpers.c` 里两处漏掉的
`-Wformat-truncation` 也按作者自己的做法包进 pragma(同一个函数里另外四处
`snprintf` 早就包了)⇒ `-Wall -Wextra` 下**零警告**。

### 第三层:链接器的错误输出被 DLL 冲突吞掉(纯环境,不是仓库缺陷)

本机 PATH 里 `/mingw64/bin` 抢在 `/c/msys64/ucrt64/bin` 前面,而前者带的
`libintl-8.dll` / `libiconv-2.dll` / `zlib1.dll` / `libwinpthread-1.dll`
**版本与 ucrt64 的不同** ⇒ ucrt64 的 `ld.exe` 加载到错版本的运行时 DLL
⇒ **链接失败时一个字都不打印**。

实测同一条链接命令:

| PATH | ld 的输出 |
|---|---|
| 当前 PATH(`/mingw64/bin` 在前) | **零字节** |
| ucrt64 优先 / 去掉 `/mingw64/bin` | `undefined reference to 'jh_cgstate_get_state'` ×5 |

⇒ **真错误被环境吞掉**,所以现场看到的是「ld 静默死 / flaky / plugin 开才有
exe」这类没法归因的现象。已记进 `docs/internal/build.md`(构建时把 ucrt64 提到
PATH 最前)。

### 新常驻门:`artifact_checks.sh` 的 `helpers_symbols`

「编译通过」不等于「符号齐全」—— 本次就是这样溜过去的。加一道**产物级**门:
把 `jhyy_helpers.c` **独立编译**一遍(不复用仓里那个可能陈旧的 `.o`),
取它真正导出的 `jh_*` 符号,与 src0 里 `extern fn jh_*` 的声明集合比对 ——
**少一个就红**,多了不红(新加 C 桥函数是正常演进)。

**已造红灯验证:** 还原成出事那版 ⇒ 门当场报出那两个符号(且 gcc 编译**零错误**,
说明「编译过了」确实不足以说明问题)。

### 台账:0 ACTIVE / 0 DEFERRED

- **W-135 的推理被改正**(结论不变):原写「block-name 表存的是 base 名 ⇒ 256 条
  用不满」是**错的** —— 它存的是**完整块名**(`then5`),**每个块一条**,
  `cg_expr` 一个函数就 ≈1492 块 ⇒ **上限可达**;无害的理由只有一条:
  名字带全局计数后缀 ⇒ 名字全局唯一 ⇒ `count` 恒为 0 ⇒ 满表回落发的标签与
  正常路径**逐字节相同**。另:超 256 块的函数在 **inline_import 进来的模块**
  里(`cg_expr` ≈1492 / `infer_type` ≈1212 / `next_token` ≈848),不在
  `main.jhyy` 自己的正文里(它自己最大 ≈126 块)。原文还写「曾尝试『响亮失败』
  改法并撤回」—— `git log --all` / stash / reflog 里**没有任何对应痕迹**,
  已改成明确的推演标注。
- **W-134.1 的 DEFERRED 是陈旧的**:commit `2ab0f24` 已经把 MCP pytest 接进
  CI(实测 40 passed / 1 skipped),台账却还写着 DEFERRED ⇒ 已翻成 RESOLVED。
  ⇒ **DEFERRED 桶归零**。

### 门(2026-10-25 实测)

| 门 | 结果 |
|---|---|
| `make`(自举闭环 + 漂移检查) | ✅ 通过(`_boot_new.s` == `_boot_new2.s` byte-equal) |
| `gcc -std=c11 -Wall -Wextra -c compiler/src0/jhyy_helpers.c` | ✅ **零警告**(rc=0) |
| `regress jhyy.exe` | ✅ **200/200 PASS** + 0 XFAIL + 19 SKIP(219 total) |
| `regress --cross=auto`(本机 docker) | ✅ **7 个** sysv 用例全 PASS(exit=28/217/42/35/18/42/**170**) |
| `closure_check.sh` | ✅ PASS(v2.s == v3.s,byte-identical) |
| `fixed_point.sh` | ✅ 17 PASS / 0 FAIL / 0 INFO(N=10 .il 与 .s 跨代 byte-equal) |
| `artifact_checks.sh` | ✅ **13 PASS** / 0 KNOWN-FAIL / 0 FAIL / 0 SKIP(+1 = 新门 `helpers_symbols`) |
| `artifact_checks.sh --only=helpers_symbols`(造红灯) | ✅ 出事那版 ⇒ **FAIL**,报出 `jh_cgstate_get_state` / `jh_cgstate_set_state` |
| `audit_test_assertions.py --strict` | ✅ 0 违规 |
| MCP pytest | ✅ **40 passed / 1 skipped**(miniconda python) |
| 台账 | ✅ **0 ACTIVE / 0 DEFERRED** / 126 索引行 |

**⇒ 另附一条漂移体检(手工,未进门):** 把新旧 `.s` 的 temp id / 字符串池下标 /
栈槽偏移全部归一化后 diff,12 MB 的 `.s` 只剩 **132 行**差异,且每一行要么是
路径字面量、要么是 `call jh_sidefile_path` ⇒ **零语义漂移**(W-132 记录的
「改 main.jhyy 会移位 temp 编号 ⇒ 自举产物行为漂移」这次没有发作;
`movzbl` 计数 HEAD 与新产物都是 5744)。

---

## v4.x follow-on plans (⏳)

> **2026-10-15 更新:** 原 12 份未启动计划(`v4.1.0` … `v4.12.0`)已合并为单一
> [`docs/plans/v4/backlog.md`](../../plans/v4/backlog.md),**不再以版本号命名**
> —— 版本号在启动时才分配。已 ship 的 `v4.0.x` 计划保留原名作审计轨迹。

Per [`docs/plans/v4/backlog.md`](../../plans/v4/backlog.md) (原 12 files: v4.1.0 → v4.12.0):

| Sprint | Intent |
|---|---|
| v4.0.0 | (this ship — axis-v2 + axis-v3 merge) |
| v4.1.0 | M5: delete `compiler/src/*.c` + untrack QBE + delete `runtime/runtime.c` — "jhyy 编 jhyy" 0-C 闭环 (deferred from v1.x) |
| v4.2.0 | async/await + Future runtime |
| v4.3.0 | full lifetime + Polonius borrow check (replaces v3.1.0 NLL stub) |
| v4.4.0 | closure enhance: move/borrow capture/generic/trait object |
| v4.5.0 | const generic `[T; N]` |
| v4.6.0 | trait objects (dyn Trait) + vtable dispatch |
| v4.7.0 | multi-error recovery (parser/sema diagnostic chain) |
| v4.8.0 | basic optimization pass (const fold / dead code / algebra) |
| v4.9.0 | package manager (`jhyy new/build/test` + `jhyy.toml`) |
| v4.10.0 | HKT 1阶 + specialization |
| v4.11.0 | C11/Rust memory model + multi-arch (aarch64/riscv64) Cap<T> ABI |
| v4.12.0 | `.jhyynb` native binary format实装 (DWARF emitter + `--target=jhyy-os` + `jhyy-inspect`) |

Sprint ordering may be re-parallelized (not strictly serial) per dep graph: v4.3 → v4.4 strict; v4.5/v4.6/v4.7/v4.8/v4.9 can open feature worktrees in parallel.

---

## References

- **Authoritative spec**: [`docs/plans/v4/v4.0.0-plan.md`](../../plans/v4/v4.0.0-plan.md) (lines 27-33 + 49 merge + 83-89 commit cadence)
- **Memory**: `project_v2_v3_final.md` (2026-09-29 user FINAL 决定 v2/v3 closure)
- **Self-backend RCA**: `feedback_v3_self_backend_diverges_v2.md` + `feedback_codegen_amd64_run_zerobyte.md` (V3 self-backend bugs真修 in v3.4.x chain)
- **D43 baseline**: `docs/logs/v2/d43-baseline-archive.md` (v2.14.0 N≥10 baseline `43fee332...` HOLD through v4.0.0)
- **Workaround history**: `docs/internal/workarounds.md` (77 RESOLVED + 5 SUPERSEDED + 2 INVALID + 1 permanently deferred)

---

<sub>v4.0.0 umbrella changelog · per `feedback_changelog_umbrella` (single umbrella per vX.Y, no standalone changelog-v4.X.Y.md)</sub>