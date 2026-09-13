# Changelog

> **入口**:GitHub Release / 包管理器 / cache 层从这个文件读版本号。具体变更看 [`docs/CHANGELOG.md`](docs/CHANGELOG.md) (完整索引) → [`docs/logs/v*/changelog-vX.Y.{0,md}`](docs/logs/) (per-version umbrella)。

## 最新 release

### v2.11.9 — 2026-09-13 — **axis-v2 W-074.7.9 QBE side 真修 — QBE fallback 5/5 EXIT exact closure** (axis-v2 only; main 待 merge; self-backend 侧仍 ACTIVE W-074.6 family)

**Tag**: `v2.11.9` (axis-v2 branch)
**Status**: W-074.7.9 big_test runtime **QBE side ✅ CLOSURE**; self-backend side 仍 🟡 ACTIVE due to W-074.6 family (extsw silent-skip + multi-func body 0-byte + emit_ret 不 mov %t1 → %eax 等 pre-existing bugs, 已知范围 ~500+ LOC 多 sprint, 显式 deferred v2.x 中期 per W-074.6 ACTIVE state)

**Highlights**:

- **2 个独立 root cause 真修** (per v2.11.9 plan mode Explore agent 调研):
  - **`idiv` emit 无 sign-extend prefix** (emit_call.jhyy `is_div` branch): x86 `idivl` semantics dividend = `(%edx << 32) | %eax`; `%edx` 残留 → x86 #DE fault → Windows STATUS_INTEGER_DIVIDE_BY_ZERO 0xC000008C (wrapped 0xC0000095 per process config). **真修**: add `\tcltd\n` / `\tcqto\n` prefix (mirror `is_mod`).
  - **Lexer 不识 QBE `rem` keyword** (lexer.jhyy `next_token_binop` dispatcher + main `next_token` `'r'` → ret/rem disambiguate): QBE `%` operator emits `rem` (signed remainder, per QBE spec §6.3). Lexer 之前无 `rem` branch → `next_token` returns -1 → `lex_il` 静默 skip 1 byte/iteration → `rem` keyword + 2 operand temps ALL skipped → those `t24`/`t69`/`t109`/etc. SSA values never appear in `.s`. **真修**: add `rem` branch in `next_token_binop` (consume "em", op_name="rem"); add `'r'` → ret/rem dispatch in main `next_token` (跟 `'d'` → div pattern 一致).
- **`is_rem` flag + dispatch 真修** (emit_call.jhyy): new `is_rem` flag init + `cg_find_sub` check for "rem" 3-char substring + `is_rem` dispatch branch (cltd/cqto + idiv + movq %rdx, %rax — same path as is_mod).
- **QBE fallback 5/5 EXIT exact closure 真修达成** (per [[feedback_fix_evaluation_rule]]):
  - hello=42 ✅
  - big_test=**12345** ✅ (从 v2.11.8 STATUS_INTEGER_OVERFLOW 0xC0000095 → v2.11.9 EXIT=12345, 真修 closure) — 9 个 `rem` ops 正确 emit (cltd+idivl + movq %rdx, %rax)
  - struct_val_pass=35 ✅
  - fib_renamed=832040 ✅ (= 832040 mod 256 = 40, 跟 baseline 一致)
  - nested_struct_deep=22 ✅
  - struct_val_assign=30 ✅
- **QBE fallback 115/115 regress PASS preserved** + **self-backend 1/5 hello PASS preserved** (per W-074.6 baseline; multi-func closure deferred v2.x 中期)
- **D43 closure v1↔v2 .il sha HOLD** (v2/v3/v4/v5 sha `42580b87...` post-fix, re-baseline per D43 closure rule 因 rem emit 微变)
- **byte-equal-amd64 10/10 PASS preserved** + **fixed_point N≥3 PASS preserved**
- **NEW ship gate audit grep** (per [[feedback_codegen_amd64_run_zerobyte]]): self-backend big_test.s `cltd` = 14 (5 div + 9 rem) + `idivl` = 14 + `movq %rdx, %rax` = 9 (was 0 pre-fix) + `.s` 行数 8727 ≥ 100 bytes + `main_jhyy.s` non-empty
- **jhyy.exe.sha256 refresh**: `9ef7f49734ef99d7...`

**完整 changelog**: [`docs/logs/v2/changelog-v2.11.0.md`](docs/logs/v2/changelog-v2.11.0.md) § v2.11.9
**Plan**: [`docs/plans/v2/v2.11.9-plan.md`](docs/plans/v2/v2.11.9-plan.md)

---

### v2.11.10 — 2026-09-13 — **axis-v2 W-074.6 T3-a per-fn frame size + T4-c multi-arg FN_ARG 真修 — 5/6 self-backend EXIT exact closure** (axis-v2 only; main 待 merge; **5/5 self-backend NOT achieved — T4-g emit_binop cnew + emit_jnz silent-skip exposed**)

**Tag**: `v2.11.10` (axis-v2 branch)
**Status**: W-074.6 T3-a per-fn frame size **✅ CLOSURE** + W-074.6 T4-c multi-arg FN_ARG 真修 (scope UP 配套);self-backend 5/6 EXIT exact closure (跟 v2.11.9 baseline 一致但 different bug 真修);5/5 self-backend closure deferred v2.11.10a+ (T4-g emit_binop cnew + emit_jnz loop body entry silent-skip, pre-existing W-074.6 family bug)

**Highlights**:

- **T3-a per-fn frame size 真修** — 两阶段 pre-scan (`cg_compute_per_fn_max_temps` Phase 1 扫 fn_starts, Phase 2 per-fn max temp id) + CGState 加 fn_starts/per_fn_max/fn_count 3 字段 + emit_func_header 改读 `per_fn_max[cur_fn_idx]` 替换 v2.11.2 global-max variant (1 个 fn = 15488 bytes frame → 递归函数 SIGSEGV 真修)
  - big_test_run.s per-fn `subq $N, %rsp` 出现 多个 distinct frame sizes (gcd $600 / t_gcd $5920 / etc)
  - `subq $15488` 出现 0 次 (vs 30+ pre-fix)
  - gcd `subq $600, %rsp` vs 旧 `subq $15488, %rsp` (75 temps × 8 = 600 vs 1936 temps × 8 = 15488)
- **T4-c multi-arg FN_ARG 真修** (scope UP 配套 T3-a):
  - lexer `next_token_func_header` 改 dup 完整 header text (`function w $name(args)`) 替代 v2.11.0-2.11.9 只 dup name;hdr_start 跳过 ws 让 dup 起始就是 "function" 字符 (避免 `.globl  function...` 链接失败)
  - emit_func_header 加 `cg_state_set_fn_header` populate cur_fn_header_text + extract name from full header for `.globl` + label
  - emit_copy FNARG 路径替换 hardcode `reg_rcx_for_qt(dst_qt)` → `cg_find_arg_idx` + `reg_rax_for_qt_idx(dst_qt, idx, target_tag)`,Win x64 arg 0..3 = %rcx/%rdx/%r8/%r9 (SysV → rdi/rsi/rdx/rcx via target_tag)
  - big_test gcd body emit `movl %ecx, -504(%rbp)` (arg 0 = %a) + `movl %edx, -512(%rbp)` (arg 1 = %b) vs 旧硬编码 `movl %ecx` 都用第 1 arg
- **诚实记录 per [[feedback_fix_evaluation_rule]]**:**5/6 self-backend EXIT exact closure** ✅ (hello=42 / struct_val_pass=35 / fib_renamed=40 / nested_struct_deep=22 / struct_val_assign=30), 跟 v2.11.9 baseline 一致但 different bug 真修
- **5/5 self-backend closure NOT achieved** — gdb 取证 big_test 在 T3-a+T4-c 真修后 SIGFPE at `gcd+158 idivl -576(%rbp)` (T4-g:emit_binop cnew silent-skip + emit_jnz loop body entry silent-skip — pre-existing W-074.6 family bug, NOT in v2.11.10 plan scope)。v2.11.10 plan 文档 "5/5 100% 可达" 预测 wrong — per [[feedback_codegen_amd64_multifn]] scope UP trigger:T4-g 暴露后 scope DOWN 5/6 闭环 接受 (跟 v2.11.9 baseline 一致不触发 +5 FLIP trigger)。**T4-g 真修 deferred v2.11.10a+ (~30-50 LOC 估)**
- **Stage 2 N=4 jhyy 编 jhyy 闭环 (v2/v3/v4/v5 byte-equal) PASS** + **QBE fallback 115/115 PASS preserved** + **byte-equal-amd64 10/10 preserved** + **fixed-point N≥3 PASS preserved**
- **D43 closure v1↔v2 .il sha HOLD** (re-baseline 因 emit 微变;new sha record in build artifacts)
- **jhyy.exe.sha256 refresh**

**完整 changelog**: [`docs/logs/v2/changelog-v2.11.0.md`](docs/logs/v2/changelog-v2.11.0.md) § v2.11.10
**Plan**: [`docs/plans/v2/v2.11.10-plan.md`](docs/plans/v2/v2.11.10-plan.md)

---

### v2.11.11 — 2026-09-13 — **axis-v2 W-074.6 T4-g lexer cnew/ceqw silent-skip 真修 — 5/6 self-backend EXIT exact closure maintained** (axis-v2 only; main 待 merge; **6/6 self-backend NOT achieved — 新 stack-slot-reuse sub-bug 暴露, deferred v2.11.11a+**)

**Tag**: `v2.11.11` (axis-v2 branch)
**Status**: W-074.6 T4-g lexer 真修 **⚠️ PARTIAL closure** (lexer 部分 CLOSED,big_test gcd SIGFPE 真修); 5/6 self-backend EXIT exact closure maintained (跟 v2.11.10 baseline 持平但 different bug 真修); big_test 通过 gcd 后 **hang at t_bit_pack** (5min+ timeout),**新 stack-slot-reuse sub-bug 暴露** (W-074.6 family 范围内, deferred v2.11.11a+ 真修).

**Highlights**:

- **T4-g lexer 4-char compare-op recognition 真修** (`codegen_amd64_lexer.jhyy` 3 处 ~5 LOC):
  - **stage 1 guard** 加 `n1 == (110 as i32)` 接受 `cnew` prefix
  - **stage 2 guard refactor flag pattern** (2 独立 if 设 `has_type_suffix` flag + 最终 if check) 接受 type suffix at idx 3 (4-char `ceqw`/`cnew`) OR idx 4 (5-char `csltw`/`cultw`/...),**绕开 codegen short-circuit OR workaround 的 nested-OR bug** (首次尝试 nested OR 触发 QBE "predecessors not matched in phi" → refactor flag pattern 替代)
  - **op_str table** 加 `n1 == 110 ('n') → "cnew"` branch consistency (dead store 但保持代码对称)
- **T4-g 真修 verified**:
  - `big_test.il` 65 个 4-char compare op 正确 emit (11 ceqw → 11 sete + 54 cnew → 54 setne in big_test_run.s)
  - gcd Euclid loop cond check 正确 emit (cmpl + setne + cmpl $0 + jne/jmp) → **不再 SIGFPE in gcd+158** (跟 v2.11.10 不同)
  - `.s` audit: `set(ne|e)\b` count ≥ 65 + `jne .Lloop_body` count > 100 + `jmp .Lloop_end` count > 100 + `grep subq \$15488` = 0 (T3-a closure preserved)
- **Codegen nested-OR workaround bug 取证 (NEW finding)**: `compiler/src0/codegen.jhyy:2060-2101` short-circuit OR workaround 不 track cur_block 当 right_node 含 nested OR → QBE "predecessors not matched in phi" → selfhost build break。**refactor 绕开**: flag pattern (2 独立 if + flag + 最终 if check) 替代 nested OR。真修 deferred v2.x 中期 V2-D。
- **诚实记录 per [[feedback_fix_evaluation_rule]]**:**5/6 self-backend EXIT exact closure maintained** ✅ (hello=42 / struct_val_pass=35 / fib_renamed=40 / nested_struct_deep=22 / struct_val_assign=30), 跟 v2.11.10 baseline 持平但 different bug 真修
- **6/6 self-backend closure NOT achieved** — big_test 通过 gcd 后 hang at t_bit_pack (5min+ timeout), **新 stack-slot-reuse sub-bug 暴露** (W-074.6 family 范围内, in `compiler/src0/codegen_amd64_emit_call.jhyy` emit_binop shift op 路径): bit_pack 函数 emit `(a & 0xFF) | ((b & 0xFF) << 8) | ((c & 0xFF) << 16) | ((d & 0xFF) << 24)` 时所有 shift amounts (8/16/24) 跟 0xFF masks 写**同一个** -32(%rbp) slot → 计算错值 → check_eq 不等 → hang。QBE 后端不受影响 (QBE 走自己 allocator, EXIT=57 PASS 维持)。v2.11.11 plan 文档 "6/6 100% 可达" 预测 wrong (跟 v2.11.10 plan "5/5 100% 可达" 一样 wrong, Risk 5 警告成真) — per user 2026-09-13 pre-confirmed scope DOWN ("仅 T4-g 真修 (推荐)"): scope 限定在 T4-g lexer 真修, 6/6 closure 留 v2.11.11a+ 真修 stack-slot-reuse (~30-50 LOC 估)
- **Self-backend regress**: **71/115 PASS** (vs v2.11.10 baseline 58/115, **+13 PASS** 改善, T4-g fix 暴露之前 crash 在 gcd 的 tests 现在通过, FLIP count = 13 PASS improvements 非 scope DOWN trigger per [[feedback_codegen_amd64_multifn]])
- **Stage 2 N=4 jhyy 编 jhyy closure PASS** + **QBE fallback 115/115 PASS preserved** + **byte-equal-amd64 10/10 preserved** + **fixed-point N≥3 PASS preserved**
- **D43 closure v1↔v2 .il sha HOLD** (re-baseline 因 lexer 微变; new sha `a4f32837...` recorded)
- **jhyy.exe.sha256 refresh**

**完整 changelog**: [`docs/logs/v2/changelog-v2.11.0.md`](docs/logs/v2/changelog-v2.11.0.md) § v2.11.11
**Plan**: [`docs/plans/v2/v2.11.11-plan.md`](docs/plans/v2/v2.11.11-plan.md)

---

### v2.11.8 — 2026-09-13 — **axis-v2 W-074.7.8 真修 — 4/5 EXIT exact closure** (axis-v2 only; main 待 merge)

**Tag**: `v2.11.8` (axis-v2 branch)
**Status**: W-074.7.8 derived-address tracking **PARTIAL closure** (4/5 EXIT exact); big_test runtime STATUS_INTEGER_OVERFLOW 0xC0000095 deferred v2.11.9+ (W-074.7.9 NEW)

**Highlights**:

- **Derived-address tracking 真修** — bitmap flag 任何 temp holding derived address (alloc-result + binop add/sub on pointer + copy of address-holder); emit_load/store/loadsub 改 full dispatch (slot vs indirect `mov<size> (%r8), %reg` via %r8 scratch); emit_binop 产生 derived-address 时 flag result; emit_copy propagate flag (TEMP + FNARG paths)
- **Self-referential slot bug 真修** — v2.11.5 design 让 pointer-slot == region offset, lea+mov 自我覆盖;真修 SKIP `cg_record_temp_slot`, pointer-slot 走 formula `-(32+t*8)` Win (formula 跟 region 物理分离)
- **FNARG flag propagate** — l-typed fnarg (struct param pointer) 走 FNARG path 不 flag propagate → struct_val_pass EXIT 6→35 flip 真修
- **byte-equal 五件套 4/5 EXIT exact closure**:
  - hello=42 ✅ (跟 baseline 一致)
  - fib_renamed=40 (= 832040 mod 256, 跟 baseline 一致) ✅
  - struct_val_pass=35 (从 v2.11.6 EXIT=6 → v2.11.8 EXIT=35, 真修 closure) ✅
  - nested_struct_deep=22 (从 v2.11.6 EXIT=35 → v2.11.8 EXIT=22, 真修 closure) ✅
  - struct_val_assign=30 ✅ (跟 baseline 一致)
  - big_test = STATUS_INTEGER_OVERFLOW 0xC0000095 ⚠️ (separate deeper bug, **deferred v2.11.9+ W-074.7.9 NEW**)
- **QBE fallback 115/115 PASS preserved** + **self-backend 5/5 link preserved** (v2.11.6 closure 不 regress)
- **self-backend regress +2 flips** (56/115 → 58/115, 远低于 +5 scope DOWN trigger per [[feedback_codegen_amd64_multifn]])
- **D43 closure v1↔v2 .il sha HOLD** (v2/v3/v4/v5 sha = `3f0bfb...` 一致) + **byte_equal_amd64 10/10 PASS preserved** + **fixed_point N≥3 PASS preserved**
- **NEW ship gate per [[feedback_codegen_amd64_run_zerobyte]]**: `main_jhyy.s` = 12 行 / 207 bytes (≥ 100 bytes 阈值, ≥ baseline, no truncation)
- **jhyy.exe.sha256 refresh**: `883680d966cc79a9bf4e7df851e2441fb8bd9fbfe1a0924cc9adaa38c1dca13a`

**完整 changelog**: [`docs/logs/v2/changelog-v2.11.0.md`](docs/logs/v2/changelog-v2.11.0.md) § v2.11.8
**Plan**: [`docs/plans/v2/v2.11.8-plan.md`](docs/plans/v2/v2.11.8-plan.md)

---

### v2.0 阶段 — 2026-09-04 — **v2.0 阶段全 ship ✅**

**Tags**: `v2.3.0` (commit `54d93df`) + `v2.4.0` (commit `7fb735b`); 阶段内 v2.0.0 / v2.1.0 / v2.2.0 未打 tag (per 2026-09-01 user 决定:阶段首批 ship 即可打 tag)
**Status**: v2.0 阶段 (v2.0.0 → v2.4.0) 全 ship;下一步 = **v3.0 3a-3f** (inline asm / `#[naked]` / volatile / `#[link_section]` / memory barrier / `#[no_std]` 软 ship) 等 user 启动;v2.x 中/末 ‖ v3.x 异步并行。

**Highlights**:

- **Multi-target dispatcher** — `jhyy compile --target=amd64_win` / `--target=amd64_win_freestanding` / `--target=amd64_sysv_stub`(stub fatal,推 v2.x 中/末)
- **hello-freestanding.efi 跑 OVMF 5/5 PASS** — QEMU + OVMF (q35 machine) 启动 + FAT12 image + serial capture;ConOut->OutputString 间接调用通过 efi_call_via_ptr
- **spec 锁定**: lang-spec § 17-20 (OS 启动前置 + freestanding + Debug + Wire); abi § 13/14 (Multi-target ABI + wire types)
- **byte-equal 三件套** — `.il + .s + .exe` 三层 byte-equal 跨 jhyy_v1 ↔ jhyy_v2;D26 reproducibility recipe (`gcc -g0 -Wl,--build-id=none` + `SOURCE_DATE_EPOCH=1234567890` via `jh_setenv`)
- **Stage 2 N=4 closure re-baselined** — sha `51376ce5...` (per D43 阶段性 self-equal hold,v2.4.0 Stage 1+2 触发 src0 emit 微变 → 重 baseline)
- regress baseline 104/104 PASS + 4 SKIP (108 total)
- ACTIVE workaround 数 → 0;W-057 / W-058 仍 DEFERRED-to-v2.x 中/末(QBE 自写时修)

**完整 changelog**: 5 个 umbrella = [`docs/logs/v2/changelog-v2.0.0.md`](docs/logs/v2/changelog-v2.0.0.md) / [v2.1.0](docs/logs/v2/changelog-v2.1.0.md) / [v2.2.0](docs/logs/v2/changelog-v2.2.0.md) / [v2.3.0](docs/logs/v2/changelog-v2.3.0.md) / [v2.4.0](docs/logs/v2/changelog-v2.4.0.md)

---

### v1.8.3 — 2026-08-29 — **v1.x FINAL** 🎯

**Tag**: `v1.8.3` `98c8272`
**Status**: v1.x 终结,v0.9 wip 冻结;v2.0 阶段 ship ✅ 走完 (2026-09-04),下一步 = v3.0 3a-3f 等 user 启动。

**Highlights**:

- **Stage 2 N=4 byte-equal 自举闭环稳定** — `jhyy_v1 → v2 → v3 → v4 → v5` 产出 byte-equal `.il` (sha `03a1cdd4...` v1.8.0 → `51376ce5...` v2.4.0 re-baseline)
- **Installer v1.8.3 WiX** — UCPD.sys Deny ACE bypass + Windows 文件关联 4 层清理 (HKCR + UserChoice + OpenWithProgids + jhyy_auto_file ProgId)
- **`jhyy-setuc.exe`** reverse-engineered Mozilla UCPD Hash 算法 (C# port),try/finally UCPD restart
- **v1.7.x 32 candidates 完整 ship**(Stage 1-5 + v1.7.1/2/3 patches)
- **spec v1.3.0 锁定** = v1.x FINAL marker; ACTIVE workaround 数 = 0

**完整 changelog**:[`docs/logs/v1/changelog-v1.8.0.md`](docs/logs/v1/changelog-v1.8.0.md) (umbrella)

## 版本轴速览

| 轴 | 范围 | 当前状态 |
|---|---|---|
| **v0.x** | C 编译器自身 (`compiler/src/*.c`) | 🟢 frozen at v1.0.0 baseline |
| **v1.x** | jhyy 自举 (`compiler/src0/*.jhyy`) | 🟢 **v1.8.3 shipped = v1.x FINAL** |
| **v2.x** | QBE 完整重写 + amd64_sysv / freestanding | ✅ **v2.0 阶段 ship** (2026-09-04, tags `v2.3.0` / `v2.4.0`); v2.x 中/末 ⏳ 未启动 (QBE 自写 / amd64_sysv 实 impl / N 代 fixed point) |
| **v3.x** | 语言特性扩展 (inline asm / `#[no_std]` / `&mut` + lifetime) | ⚪ next (v2.0 阶段 ✅ ship, 3a-3f 等 user 启动) |

## v1.x ship 时间线

| Version | Date | Tag / Commit | Highlights |
|---------|------|--------------|-----------|
| **v1.8.3** | 2026-08-29 | `98c8272` | installer v1.8.3 WiX + UCPD.sys bypass |
| v1.8.2 | 2026-08-28 | — | Win10 Feb 2024+ UCPD.sys Deny ACE bypass + 4-layer file assoc cleanup |
| v1.8.1 | 2026-08-28 | — | `jhyy-setuc.exe` reverse-engineered Mozilla 算法 |
| v1.8.0 | 2026-08-28 | — | W-059 defer codegen 真修 + W-060/W-061 INVALID 闭环 |
| v1.7.3 | 2026-08-28 | `57f89dc` | 32 candidates 完整 ship; spec v1.3.0 locked |
| v1.7.0 | 2026-08-15 | — | EXPECT-ERROR annotation + Stage 1-4 |
| v1.6.0 | 2026-08-13 | — | regress.py 收口 + baseline binary tracking |
| v1.5.10 | 2026-08-27 | `c057aa3` | RunOnce auto-install VSCode ext |
| v1.0.0 | 2026-08-10 | `eabee0d` | 真自举 byte-equal 闭环 (Stage 2 N=3) — jhyy 编 jhyy 里程碑 |

**完整时间线 + 每版本 patch 详情**:`docs/CHANGELOG.md` (索引) → `docs/logs/v1/` (per-version umbrella changelog)

## 下一阶段

**v3.0 3a-3f** (语言扩展 OS-required) 等 user 启动 — v2.0 阶段 ✅ ship 走完(2026-09-04);**v2.x 中/末 跟 v3.x 异步并行**(QBE 自写 / amd64_sysv 实 impl / N 代 fixed point 仍待 v2.x 中/末) — OS 准备:

- 路线图: [`docs/plans/roadmap/v2-v3-parallel-sprint-plan.md`](docs/plans/roadmap/v2-v3-parallel-sprint-plan.md)
- OS 启动链路: [`docs/plans/v2/v2.0.0-os-prep.md`](docs/plans/v2/v2.0.0-os-prep.md)
- 跨项目协调: [`../jhyy_OS/docs/coordination.md`](../jhyy_OS/docs/coordination.md)

## 编写约定

per `feedback_changelog_umbrella.md`:

1. **vX.Y 轴只 1 个 umbrella changelog** — 不创建 `changelog-vX.Y.Z.md` / `changelog-vX.Y.Z-wNNN.md` 之类 standalone
2. **Umbrella 包含**:承接上版本 + 触发原因 + scope 决策 + sprint 状态总览 + 关键数字 + 决策点 + 跨 sprint 影响
3. **Patch 版本**(vX.Y.Z where Z>0) 内容回填到 vX.Y 的 umbrella changelog
4. **本文件**(根 `CHANGELOG.md`) 是 GitHub Release / 包管理器入口,**不重复** `docs/CHANGELOG.md` 内容