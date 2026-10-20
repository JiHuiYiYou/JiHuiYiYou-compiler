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