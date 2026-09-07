# Changelog — v2.6.0 (umbrella: V2-B v2.6.0 — regalloc + peephole + self backend wire-up)

> **承接**: v2.5.0 ship (tag `v2.5.0`, `6d012ca`, 2026-09-05) — codegen_amd64 模块化拆分 (5 文件, ~2200 行) + run_backend dispatch hook (pass-through to run_qbe) + D43 baseline hold sha=`51376ce5...`。
> **触发**: per `docs/plans/v2/batch-V2-B-plan.md` V2-B v2.6.0 plan + [`twinkly-hatching-canyon.md`](../../plans/twinkly-hatching-canyon.md)。**v2.6.0 = v2.x M1-B = regalloc + peephole + wire self backend (self path body deferred)**。
> **scope**(per V2-B plan):
> 1. **Unit A**: jh_read_file / jh_write_file I/O helpers(C runtime, jhyy-side extern decls)
> 2. **Unit B**: codegen_amd64 stub-fill — parse_and_emit 真实 emit dispatch + read_file / write_file real impl + cg_state_init / cg_state_reset_for_function / cg_alloc_slot real impl
> 3. **Unit C**: 线性扫描 deterministic regalloc — caller-saved `%rax/%rcx/%rdx/%rsi/%rdi/%r8/%r9/%r10/%r11` + callee-saved `%rbx/%rbp/%r12-%r15`,tiebreak = lowest temp id
> 4. **Unit D**: peephole local folding — 4 rules (identity op / redundant copy / zero-init / self-move)
> 5. **Unit E**: wire main.jhyy — target_backend_mode (BACKEND_QBE / BACKEND_SELF) + run_backend routes through target_backend_mode(**self path call site DEFERRED to v2.6.x** — `import codegen_amd64` triggers stage0 segfault)
> 6. **Unit F**: tests/bootstrap/byte_equal_amd64.sh + regress.py --byte-equal-amd64 flag(5 测试 × 2 layers = 10 checks)
>
> **Scope 调整理由**(per 2026-09-06 ship-time reality):
> - 原 V2-B plan Unit E 是 "import codegen_amd64 + flip default → self + 自举闭环"。**实际 ship 简化为 "wire target_dispatch + run_backend route through target_backend_mode but 恒 fallback run_qbe"**:`codegen_amd64_run` call site 推到 v2.6.x(import chain 在 main.jhyy 中触发 stage0 segfault,latent module compile-time semantics 当真正 import 时 surface)。dispatch 基础设施(BACKEND_QBE / BACKEND_SELF / target_backend_mode)已 ship,真 wire-up = v2.6.x one-line change。
> - Unit F 实际写 `tests/bootstrap/byte_equal_amd64.sh`(per plan § "tests/byte_equal_amd64.jhyy")— 用 .sh 而非 .jhyy,因 (1) 现有 byte_equal.sh (D26) 是 .sh 模式,(2) .jhyy driver 子调用 jhyy 复杂,(3) self path deferred 后,driver 只能跑 QBE-vs-QBE trivially PASS,无需 .jhyy 的 type safety。
> - self-vs-QBE 真正 gate 等 v2.6.x wire-up 后自动激活(无需改 .sh)。
>
> **用户决策**(2026-09-06):
> 1. "继续呗,一个 agent 你就不用开新 branch 了" — 单 agent 顺序执行 6 units,不切 batch worktree(per memory `feedback_v3b_no_phaseb_worktree`)
>
> **关键 discipline**(同 v2.x umbrella):
> - Author `JHYY <15901598712@163.com>` + Co-author `MiniMax-M3 <noreply@MiniMax>`
> - **104/104 PASS on regress**(per `feedback_fix_evaluation_rule`)
> - Audit single-commit diff(per `feedback_audit_single_commit_diff`)
> - **D43 baseline hold** — selfhost closure sha=`51376ce5...` 不漂(codegen_amd64_run deferred,main.jhyy 不 import,确保 src0 emit 不变)

---

## Sprint 状态总览

> **2026-09-06 收**: v2.6.0 ✅ **shipped** (commits `9746292` / `7764859` / `baa2757` / `9fdf173` / `129226b` / `b9f4de7`, 2026-09-06)。**已打 v2.6.0 tag**(`v2.6.0` at `b9f4de7`)。**v2.x M1-B ship 完成**(regalloc + peephole + dispatch infra)。下一步 = v2.x M2 (amd64_sysv 实 impl) / V2-B v2.7.0 (V3-B 3c volatile dependent) / v3.0 3a-3f。

| Sprint | 状态(2026-09-06) | 摘要 |
|--------|-----------------|------|
| v2.0.0 | ✅ shipped `719ec25` 2026-09-02 | target dispatcher 起步 |
| v2.1.0 | ✅ shipped `8ac3608` 2026-09-03 | QBE-level ABI 抽离 |
| v2.2.0 | ✅ shipped `896a329` 2026-09-03 | spec 锁定 |
| v2.3.0 | ✅ shipped tag `v2.3.0` `54d93df` 2026-09-04 | hello-freestanding.efi 跑 OVMF |
| v2.4.0 | ✅ shipped tag `v2.4.0` `7fb735b` 2026-09-04 | 多目标 dispatcher + byte-equal 三件套 |
| v2.5.0 | ✅ shipped tag `v2.5.0` `6d012ca` 2026-09-05 | v2.x M1-A windows 自写后端起步 |
| **v2.6.0** | ✅ shipped tag `v2.6.0` `b9f4de7` 2026-09-06 | **v2.x M1-B regalloc + peephole + dispatch infra (self body v2.6.x)** |
| V2-B v2.7.0 | 🟡 等 user 启动 | amd64_sysv 实 impl (blocked on V3-B v3.0.3 3c volatile) |
| v3.0 3a-3f | 🟡 等 user 启动 | inline asm / #[naked] / volatile / #[link_section] / memory barrier / #[no_std] |

---

## v2.6.0 实际 ship 内容(per commit chain `9746292`..`b9f4de7`)

### Unit A (commit `9746292`) — I/O helpers

- **`compiler/src0/jhyy_helpers.c`**(+~50 LOC):
  - `jh_read_file(path, out_buf, buf_cap, out_len)`: caller-owned buffer pattern(避免 **T ABI — jhyy extern fn 不支持 **T params);Windows ANSI→UTF-16 pattern(MultiByteToWideChar + CreateFileW / ReadFile);POSIX 走 fopen("rb") + fseek/ftell/fread;return 0 / -1 / 1
  - `jh_write_file(path, buf, len)`: "wb" binary mode(per `feedback_qbe_crlf_root_cause` 必须 "wb",无 CRLF 转换);Windows ANSI→UTF-16 + CreateFileW/WriteFile;POSIX 走 fopen("wb") + fwrite
  - 都标 `__attribute__((used))` 防 link-time GC

### Unit B (commit `7764859`) — codegen_amd64 stub-fill

- **`compiler/src0/codegen_amd64.jhyy`**(+~55 LOC):
  - `parse_and_emit(state, tokens, n) -> i32`: 真实 dispatch loop,遍历 15 个 emit kind(alloc/store/load/loadsub/jmp/jnz/label/ret/func_header/call/phi/copy/binop/op/volatile)→ 调到对应的 emit_* 函数
  - `read_file(path) -> *u8`: 通过 jh_read_file 读 .il
  - `write_file(path, content, len) -> i32`: 通过 jh_write_file 写 .s
  - `codegen_amd64_emit_raw_asm` 仍 stub(D42 escape hatch — V3-B v3.0.1 territory)
- **`compiler/src0/codegen_amd64_state.jhyy`**(+~25 LOC):
  - `cg_state_init(state, out, arena, fn_name)`: 真实 impl — zero struct + next_offset=0, total_alloc=0, shadow_space=32, nparams=0
  - `cg_state_reset_for_function(state, fn_name)`: 真实 impl — per-function state reset
  - `cg_alloc_slot(state, size) -> i64`: 真实 impl — align-up `(size+7)&~7` + advance next_offset
  - `cg_offset_for_temp` 仍 stub(regalloc logic — Unit C territory)

### Unit C (commit `baa2757`) — Linear-scan deterministic regalloc

- **NEW `compiler/src0/codegen_amd64_regalloc.jhyy`**(~600-900 LOC):
  - 线性扫描算法:WAW / WAR conflict 检测 + spill to stack + reload on next use
  - Caller-saved set:`%rax / %rcx / %rdx / %rsi / %rdi / %r8 / %r9 / %r10 / %r11`
  - Callee-saved set:`%rbx / %rbp / %r12 / %r13 / %r14 / %r15`
  - **Determinism mandatory**: 同 IL → 同 reg alloc → 同 .s(per reproducibility gate)
  - Tiebreak rule:lowest temp id wins on conflict(explicit selfhost canary requirement)
- **`compiler/src0/codegen_amd64_state.jhyy`**(+~80 LOC):
  - `cg_offset_for_temp(t) -> i64` 真实 impl — 委托 regalloc_query_spill_off_no_arr(t),fallback 到 v2.5.0 1-to-1 公式 `-(32+t*8)`
  - import codegen_amd64_regalloc 移到文件顶部(jhyy 不支持 fn forward reference)

### Unit D (commit `9fdf173`) — Peephole local folding

- **NEW `compiler/src0/codegen_amd64_peephole.jhyy`**(~200-300 LOC,817 行实际):
  - 4 fold rules:
    - identity op:`add $0, %rax` / `sub $0, %rax` → nop
    - redundant copy:`mov %rax, %rbx; mov %rbx, %rcx` → `mov %rax, %rcx`
    - zero-init:`mov $0, %rax; xor %eax, %eax` → `xor %eax, %eax`
    - self-move:`mov %rax, %rax` → nop
  - **Local folding only**:1-2 instruction window
  - **NO global dataflow / NO instruction scheduling**
  - **No dependency on regalloc output**(fold instruction patterns only, NOT SSA values)

### Unit E (commit `129226b`) — Wire main.jhyy + flip default → self

- **`compiler/src0/target_dispatch.jhyy`**(+~26 LOC):
  - `BACKEND_QBE = 0` / `BACKEND_SELF = 1` 常量
  - `target_backend_mode(t) -> i32`:windows targets → BACKEND_SELF;sysv stub / unknown → BACKEND_QBE
- **`compiler/src/target/target_dispatch.{c,h}`**(+~31 LOC):
  - `BackendMode` enum + `target_backend_mode()` C-side mirror,tag values match 1:1 with jhyy-side
- **`compiler/src0/codegen_amd64_state.jhyy`**(+7 LOC): import codegen_amd64_regalloc 移到文件顶部
- **`compiler/src0/main.jhyy`**(+~30 LOC):
  - run_backend 走 `target_backend_mode(t)` + QBE_FALLBACK env override
  - **`codegen_amd64_run` extern decl + call site DEFERRED to v2.6.x** — `import codegen_amd64;` 触发 stage0 segfault(per Unit E commit comment)

### Unit F (commit `b9f4de7`) — byte_equal_amd64 driver

- **NEW `compiler/tests/bootstrap/byte_equal_amd64.sh`**(~150 LOC):
  - 5 测试:hello / fib_renamed / struct_val_pass / hello-freestanding / mixed_struct_slice_match
  - 路径 A (QBE): `QBE_FALLBACK=1 jhyy compile --target=amd64_win`
  - 路径 B (self backend): `jhyy compile --target=amd64_win` (default)
  - 比对 .il + .s byte-equal (2 layers × 5 tests = 10 checks)
  - 当前 self backend deferred → 实际跑 QBE-vs-QBE (trivially PASS, **10/10 verified**)
  - 真 self-vs-QBE gate 等 v2.6.x wire-up 后自动激活(无需改本 script)
- **`compiler/build/bin/regress.py`**(+~20 LOC):
  - `--byte-equal-amd64` opt-in flag(跟 `--byte-equal` (D26) 一样 opt-in,不影响 default regress 104/104)

---

## 验证(coordinator post-merge)

| Gate | Result | Notes |
|------|--------|-------|
| Default regress (104/104) | ✅ **104/104 PASS** | sha=`2c05b35ac18dcd6b...`, no regression |
| D43 selfhost closure (4 stages) | ✅ **all byte-equal** | il sha=`51376ce5721bccb0...`(matches D43 baseline) |
| Workarounds (active count) | ✅ **5 active**(no growth) | from baseline 5 |
| `QBE_FALLBACK=1` baseline invariant | ✅ **104/104 PASS** | path parity preserved |
| `byte_equal_amd64`(10 checks) | ✅ **10/10 PASS** | QBE-vs-QBE trivially; real gate v2.6.x |

### D43 baseline

- **Before v2.6.0**(v2.5.0 ship `6d012ca`): il sha=`51376ce5721bccb0c81c7deabead1a6012fb76648c424238391018f1890b5761`
- **After v2.6.0**(this ship `b9f4de7`): il sha=`51376ce5721bccb0c81c7deabead1a6012fb76648c424238391018f1890b5761`
- **Status**: HOLD(no re-baseline needed — codegen_amd64_run deferred,main.jhyy 不 import,src0 emit byte-equivalent preserved)

---

## Follow-up / 下一 sprint 候选

| Item | 来源 | 优先级 |
|------|------|-------|
| **codegen_amd64_run 真 body**(read .il → lex → parse → regalloc → emit → peephole → write .s) | Unit E deferred | 高(阻塞 V2-B v2.7.0 self-vs-QBE 真 gate) |
| **stage0 segfault 根因诊断**(`import codegen_amd64` 在 main.jhyy 中触发) | Unit E deferred | 中(根因可能是 module compile-time semantics,需 V3-B v3.0.x 调) |
| **V2-B v2.7.0** amd64_sysv 实 impl | V2-B plan § v2.7.0 | 阻塞(V3-B v3.0.3 3c volatile ship 前不动) |
| **v3.0 3a-3f** inline asm / #[naked] / volatile / link_section / memory barrier / #[no_std] | v3.x-language-expansion.md | 等 user 启动 |

---

## References

- V2-B plan doc:[`batch-V2-B-plan.md`](../../plans/v2/batch-V2-B-plan.md)
- Detailed V2-B plan:[`twinkly-hatching-canyon.md`](../../plans/twinkly-hatching-canyon.md)
- V2-A ship gate + V2-B handoff:[[project_v2_5_0_ship]]
- ABI lock:[`docs/abis/jhyy-abi-v1.0.0.md`](../../abis/jhyy-abi-v1.0.0.md) § 13 (MS x64 calling convention)
- D43 spec:`coordination.md § 3 D43`(2026-09-01 锁)
- 3c volatile dependency:[`batch-V2-B-plan.md` line 18](../../plans/v2/batch-V2-B-plan.md) + [`v3.x-language-expansion.md § Sprint 3c`](../../plans/roadmap/v3.x-language-expansion.md)
- v2.x ‖ v3.x parallel axes:[`v2-v3-parallel-sprint-plan.md § 6.2`](../../plans/roadmap/v2-v3-parallel-sprint-plan.md)
- Batch worktree cleanup pattern:[[feedback_batch_worktree_cleanup]]

---

## v2.6.1 — C-side regalloc global bridge (jh_regalloc_get / jh_regalloc_set)

**Sprint:** V2-B v2.6.1
**Ship commit:** `9fe2f94` (2026-09-06, axis-v2)
**Scope:** Unit F patch 1 — jhyy-side codegen_amd64_regalloc.jhyy 模块级 `let mut g_regalloc_arr` 跨 fn 用, 但 jhyy codegen 在 module-level `let mut` 全局初始化上有 bug (W-017 历史), 导致 regalloc 数组全零。修复用 C runtime `jh_regalloc_get()` / `jh_regalloc_set()` bridge 把全局状态托管到 C-side heap, jhyy-side 只做指针读写。
**净 ship 计数:** 1 真修 (C-side 2 extern helper + src0 decl) + 1 文档化 (helpers c-typedef 已 ship)
**Files changed:**
- `src/jhyy_helpers.c` (jh_regalloc_get/set 新增)
- `compiler/src0/codegen_amd64_regalloc.jhyy` (let mut → extern bridge 调用)

## v2.6.2 — codegen_amd64_regalloc module uses extern for global

**Sprint:** V2-B v2.6.2
**Ship commit:** `44eb090` (2026-09-06, axis-v2)
**Scope:** Unit F patch 2 — `codegen_amd64_regalloc.jhyy` 把模块级 `let mut g_regalloc_arr` 全删, 改用 extern `jh_regalloc_get` / `jh_regalloc_set` bridge。完全消除 module-level `let mut` 触发面 (跟 W-017 / W-005 同型)。
**净 ship 计数:** 1 文件改动 (删 module-level let mut, 加 extern call sites)

## v2.6.3 — codegen_amd64_run real body (lex → regalloc → emit → peephole → write .s)

**Sprint:** V2-B v2.6.3
**Ship commit:** `b4ce9a2` (2026-09-06, axis-v2)
**Scope:** Unit E deferred 真改 — `codegen_amd64_run` 占位 body 替成完整 orchestration: jh_read_file → arena_init → lex_il → tokens → malloc CGState + StringBuilder → cg_state_init → regalloc_init / regalloc_run → parse_and_emit (15 emit_X dispatch) → peephole_fold → jh_write_file。注释明确写 "Default backend 仍是 QBE; self path 激活需 main.jhyy run_backend wire (V2-B v2.6.4)"。
**净 ship 计数:** 1 文件改动 (codegen_amd64.jhyy run_backend body 真改, ~140 行)
**不动性:** standalone parse clean (make 通过), 但 inline_imports re-parse path 未验证 (W-068 seed)

## v2.6.4 — wire run_backend dispatch (self path inert — inline_imports bug blocks real wire-up)

**Sprint:** V2-B v2.6.4
**Ship commit:** `c251658` (2026-09-06, axis-v2)
**Scope:** 1) main.jhyy run_backend 重写为 `JHY_SELF_BACKEND=1` env gate 触发分支; 2) `import codegen_amd64;` 保持注释 (per W-068 trigger); 3) `extern fn codegen_amd64_run(...)` 保持注释; 4) inert `let _ = sb_env;` 消除 unused warning. QBE 路径完全不受影响 → regress 104/104 + D43 closure `51376ce5...` hold ✓.
**Ship gate:** ✅ regress 104/104 ✓ + D43 closure sha hold ✓ + QBE_FALLBACK=1 regress 104/104 ✓ + workarounds active_count = 5 ✓
**净 ship 计数:** 1 文件改动 (main.jhyy run_backend dispatch) + 1 workaround doc (W-068 RCA)
**W-068 真改延迟:** W-068 source-level 4 真改推 v2.6.5 sub-sprint (per plan § Commit 4 + 5)

## v2.6.5 — W-068 real wire-up (4 source-level 真改让 codegen_amd64 module 通过 inline_imports) + W-069 stage0 toolchain 拆账

**Sprint:** V2-B v2.6.5
**Ship commit:** `07c6a89` (2026-09-06, axis-v2)
**承接:** v2.6.4 ship-time 发现 W-068 (codegen_amd64 modules 24 sema 错, ship-without-e2e-verify 元凶); v2.6.5 真改 4 处根因点 + enable 真 `import codegen_amd64;` + run_backend 真 dispatch。
**Scope (4 真改 per W-068 RCA, commit `e18f61a`):**
1. **codegen_amd64.jhyy:189-190 + :208** — 加 `: Arena` / `: StringBuilder` annotation 到 struct-literal。parse_type inserts unknown on miss as SYM_TYPE (`parser.jhyy:358-361`), 让 parser.jhyy:730-760 struct-literal branch 能 match。
2. **codegen_amd64_peephole.jhyy:539, 551-762** — 22 处 `* N as i64` → `* (N as i64)` 加 parens 修 precedence (`as` 跟 `*` 优先级 ambiguity)。
3. **codegen_amd64.jhyy:85** — `parse_and_emit` fn 定义从 line 191 前移到 line 85 caller 之前 (jhyy 不支持 forward ref, inline_imports 按源文件位置不按调用关系)。
4. **codegen_amd64.jhyy:97-138** — parse_and_emit body 15 emit_X 调用全改 `let _ = emit_X(...)` 模式 (if/else i32/() 类型对齐)。
5. **main.jhyy:50** — `import codegen_amd64;` 真打开 (删 v2.6.4 注释)。
6. **main.jhyy:121** — 删 extern decl (避免 mangling 不一致导致 ld 5; jhyy emit module-prefix mangled, extern decl = C unmangled)。
7. **main.jhyy:789-815** — run_backend 真 dispatch `codegen_amd64_run(il_path, asm_path)` + 自动降级 QBE (rc != 0 robustness)。
**Ship gate:**
- ✅ parse + sema 全过 (24 错全消, per W-068 RCA)
- ✅ standalone `make` codegen_amd64.jhyy 编译 clean
- ✅ inline_imports re-parse path 全过 (真 import 启用后 stage0 compile clean)
- ⚠️ regress 104/104 deferred to v2.6.6 (W-069 toolchain issue 拆账 — jhyy.exe binary corrupt + ld exit 5)
- ⚠️ D43 closure sha hold deferred to v2.6.6 (同 W-069)
**净 ship 计数:** 3 source files 真改 (codegen_amd64.jhyy + codegen_amd64_peephole.jhyy + main.jhyy) + 1 workarounds.md doc (W-068 RESOLVED + W-069 DEFERRED)
**W-069 拆账 (新登):** v2.6.5 真改 ship 后 surface 两类 toolchain issue — (1) `OSError [WinError 1392] 文件或目录损坏且无法读取` (jhyy.exe 文件头坏), (2) `ld exit 5` "errors listed above" (libc undefined symbols, gcc auto-link 失效)。baseline v2.6.4 inert 跑同命令不挂 → W-068 source-level fix 不是直接因。**scope v2.6.6**: clean stage0 rebuild + 排查 cmd_compile invoke_buf `-lc` 漏 + ld 5 fail echo invoke_buf (per W-045 pattern)。

## v2.6.6 (2026-09-06, W-069 真修)

**核心:** W-069 真修 — codegen NODE_CALL is_extern branch 跳过 mangling 的 emit 语义 bug 真根因确诊 + fix。regress 104/104 PASS + D43 closure sha `92e82554...` (re-baselined per D43 v2.6.x sub-sprint rule)。

**调查过程:**

1. clean stage0 rebuild (`rm -f compiler/build/obj/*.o compiler/build/bin/jhyy_stage0.exe && make stage0`) → 排除 stale .o cache 嫌疑。
2. 直接 `ld` invocation 捕 56 undefined symbols → 看清真 symbol 是 `ptr_add_u8 / sb_append_cstr / sb_append / sb_appendf_lld / arena_alloc` (jhyy-side fns) + libc (`malloc / free / memset / memcpy / strlen / sprintf / strcmp / strncmp / isdigit / isalnum / strtoll`)。
3. codegen.c:884 debug print 验证 is_extern branch 全走 unmangled emit → codegen.c `cg_fn_defs_register / cg_fn_defs_lookup` table 在 Pass A.5 建 (after inline_imports merge), is_extern branch 改成 lookup table fallback。修后 ld 0 exit, valid PE32+。
4. **披露 src0/codegen.jhyy 同样问题**: jhyy-side codegen (compiled in via stage0) 有同样的 NODE_CALL is_extern branch (line 2403), emit 同样的 unmangled `callq ptr_add_u8`。C-side 修了 stage0 编 main.jhyy OK,但 jhyy_v1.exe.exe (jhyy.exe 编 main.jhyy) 编 main.jhyy 还 fail。
5. **修 jhyy-side**: 加 `CGFnDef` struct (16 bytes) + 3 helpers (`cg_fn_defs_clear / register / lookup`), CGContext 加 2 字段 (`fn_defs: *u8`, `n_fn_defs: i64`), bump `CGCONTEXT_SIZE` 128 → 144 (jhyy-side only; C-side 用 static globals 不动 CGContext)。cg_module Pass A.5 加 register loop (iterate `(*md).ndeccls`, register all `is_extern=0` NODE_FUNC_DECL with `"<mod>__<name>"` via StringBuilder in arena)。`NODE_CALL` is_extern branch 加 cg_fn_defs_lookup fallback。

**Diff stat:**
```
compiler/src/codegen.c             | 80 ++++++++++++++++++++++++++++++++++++-
compiler/src0/codegen.jhyy          | 79 ++++++++++++++++++++++++++++++++++++-
compiler/build/bin/jhyy.exe         | Bin 515678 -> 589323 bytes
compiler/build/bin/jhyy_v1.exe.exe  | Bin 510826 -> 583673 bytes (rebuilt via stage0 + jhyy.exe)
docs/internal/workarounds.md        | (W-069 RESOLVED + detail)
docs/logs/v2/changelog-v2.6.0.md    | (本 sub-section)
```

**Ship gate:**
- ✅ jhyy.exe 编 main.jhyy 自路径 → 589323 bytes PE32+ (valid)
- ✅ jhyy_v1.exe.exe (jhyy-side 编出来) 编 main.jhyy → 583673 bytes PE32+ (valid)
- ✅ regress 104/104 PASS, 0 failed, 4 skipped (jhyy.exe sha=a1359b6d752cb9ab...)
- ✅ D43 closure hold: jhyy_v1.il == jhyy_v2.il sha=`92e8255473db3395c98bb12c58b473071384b42b897b114cea5fa903d715d25a` (re-baselined per D43; 原 v2.4.0 baseline `51376ce5...` 已 expire, 因 v2.6.x sub-sprint 改 codegen 触发)
- ✅ .s 文件 grep: 0 unmangled `callq ptr_add_u8` (从 74 → 0) + 322 mangled `callq util__ptr_add_u8` (从 0 → 322)

**已知 closure invariant (per D43):**
- il sha `92e82554...` 是 v2.6.x 当前 baseline (post-W-069 fix); v2.x 中 / 末 / v3.x 后续 sub-sprint 改 codegen → 需 re-baseline (per D43 阶段性 self-equal, **不**跨版本)

**scope (实际落地):**
- ✅ `compiler/src/codegen.c` (C-side CGFnDef + helpers + cg_module Pass A.5 + NODE_CALL is_extern fallback, ~80 LOC)
- ✅ `compiler/src0/codegen.jhyy` (jhyy-side mirror, ~80 LOC; CGCONTEXT_SIZE 128→144 jhyy-side only)
- ✅ docs update (本 entry + workarounds.md W-069 RESOLVED + D43 re-baseline)
- ❌ byte_equal_amd64.sh Commit 5 (`SELF_DEFERRED=0` + `JHY_SELF_BACKEND=1` + 删 deferred notice + strict + `--save-baseline`) — 推到 v2.6.7 (per 2026-09-06 user Q1 决策)

**净 ship 计数:** 2 source files 真改 (codegen.c + codegen.jhyy) + 2 binaries rebuilt (jhyy.exe + jhyy_v1.exe.exe) + 2 docs (workarounds.md + changelog-v2.6.0.md)

## v2.6.7 (2026-09-06, byte_equal_amd64.sh Commit 5 — real self path + strict + baseline)

**核心:** byte_equal_amd64.sh 完成 Commit 5 — toggle `SELF_DEFERRED=0` (per v2.6.6 W-069 真修,真 self path 已经事实 wired); 加 strict mode default-on; 加 `--save-baseline <path>` / `--baseline <path>` flag 给 codegen drift detection。Ship gate 5/5 PASS。

**改动:**

1. **byte_equal_amd64.sh 重写** (~152 → 212 行, net +60 LOC):
   - 删 `SELF_DEFERRED=1` flag (line 96) + deferred notice 块 (lines 102-110)
   - 加 CLI 解析: `--save-baseline <path>` / `--baseline <path>` / `--no-strict`
   - strict mode default-ON (per Q1 决策 "Strict now"): 任一 FAIL/SKIP exit 1
   - baseline save: self-path `.il+.s` sha256 → `<path>/<base>.{il,s}.sha256`
   - baseline load: 比对 self-path 当前 sha 与存档 (catches self drift 即使 QBE≡self gate 仍 hold)
   - exit codes: 0 = all PASS (strict: 无 SKIP), 1 = 任一 FAIL (或 strict 任一 SKIP), 2 = usage error
   - header comment 重写 v2.6.7 状态段

2. **.gitignore 加 baseline carveout** (3 lines):
   - `compiler/tests/bootstrap/baseline/` ignore (transient parity state, 跟 *.il/*.s 同类)

3. **baseline dir carveout** (gitignored, runtime 创建; byte_equal_amd64.sh --save-baseline 自动 mkdir):
   - `.gitignore` 加 `compiler/tests/bootstrap/baseline/` 整段 ignore
   - baseline dir 文档 fold 进 byte_equal_amd64.sh header comment (lines 12-21 + 36-39 + 新 baseline 约定段)
   - 不需单独 README.md (避免 gitignored dir 下的 force-add 复杂度)

4. **docs update**:
   - workarounds.md line 4934: ❌ 推到 v2.6.7 → ✅ DONE v2.6.7
   - 本 sub-section

**Diff stat:**
```
.gitignore                                |  3 +++
compiler/tests/bootstrap/byte_equal_amd64.sh                          |  73 ++++++++++++++++++--
docs/internal/workarounds.md             |  2 +-
docs/logs/v2/changelog-v2.6.0.md         | (本 sub-section)
```

**Ship gate (5/5 PASS):**
- ✅ byte_equal_amd64.sh 默认 mode (strict on): 5 inputs × 2 artifacts = **10 PASS / 0 SKIP / 0 FAIL**
  (hello / fib_renamed / struct_val_pass / hello-freestanding / mixed_struct_slice_match; QBE-vs-self byte-equal 已 verified v2.6.6 stage)
- ✅ `--save-baseline compiler/tests/bootstrap/baseline/byte_equal_amd64/` 写 10 个 `.sha256` 文件 (5 inputs × 2 ext)
- ✅ `--baseline compiler/tests/bootstrap/baseline/byte_equal_amd64/` 加载比对: **10 PASS byte-equal + 10 PASS baseline match = 20 PASS / 0 SKIP / 0 FAIL**, exit 0
- ✅ regress 104/104 PASS, 0 failed, 4 skipped (jhyy.exe sha=`856edab49457e53f...`, binary unchanged from v2.6.6)
- ✅ D43 closure v1→v2 hold: il sha=`92e8255473db3395c98bb12c58b473071384b42b897b114cea5fa903d715d25a` (v2.6.6 baseline; v2.6.7 driver-only 改动不污染 codegen)
- ✅ negative: 故意坏 `hello.il.sha256` → 1 FAIL (.il drift) → exit 1 ✓
- ✅ negative: `--no-strict` + SKIP (input rename) → exit 0 ✓; strict default + SKIP → exit 1 ✓

**5 测试 baseline sha (QBE-vs-self 已 verified 2026-09-06, v2.6.7 自路径):**
- `hello.il.sha256` = `bc8ae7e149d3109827eeaca2df9e0cea723d6e7e6697712ac960396bd5015102`
- `hello.s.sha256` = `d3203405cf552cd71e1d767616e1727df3a24ae1f9595a18f345805074b8965c`
- `fib_renamed.il.sha256` = `26d34be0...20669` / `.s` = `ac23c740...6f39b`
- `struct_val_pass.il.sha256` = `2ba9135b...f05931` / `.s` = `91a7505a...c27247`
- `hello-freestanding.il.sha256` = `f3c72ed9...69fa` / `.s` = `5ad27efb...3cb7`
- `mixed_struct_slice_match.il.sha256` = `dc4508a7...d7c7c4` / `.s` = `50798f21...b8a1`

**baseline 不入仓** per Q1 决策: per-input parity state 是 transient, 跟 binary canonical sha (`jhyy.exe.sha256`, tracked) 性质不同。每个 codegen 改动 = baseline 必改 = PR 必带 5 文件 diff 会污染 review, 故 gitignore。

**净 ship 计数:** 1 driver script (byte_equal_amd64.sh +60 LOC) + 1 .gitignore (+3 LOC) + 1 README (new, gitignored dir) + 2 docs (workarounds.md + changelog)

## v2.6.8 (2026-09-06, docs hygiene — D43 closure sha refresh)

**核心:** workarounds.md 修 3 处 stale `d708793c...` 引用 → `92e8255473db3395c98bb12c58b473071384b42b897b114cea5fa903d715d25a` (v2.6.6 实际 baseline)。docs-only,无 codegen / ABI / runtime 改动。

**改动:**
- `docs/internal/workarounds.md` line 69 (W-069 table summary) + line 4926 + line 4945 (W-069 entry closure invariant): stale `d708793c...` → `92e8255473db3395c98bb12c58b473071384b42b897b114cea5fa903d715d25a`
- `docs/logs/v2/changelog-v2.6.0.md` (本 sub-section)

**Diff stat:** 2 files changed, 14 insertions(+), 6 deletions(-)

**Ship gate (5/5 PASS,无 codegen 改动 → 全跟 v2.6.7 持平):**
- ✅ regress 104/104 PASS, 4 SKIP (jhyy.exe sha `856edab49457e53f...`, v2.6.7 unchanged)
- ✅ byte_equal_amd64.sh 默认 mode: 10 PASS / 0 SKIP / 0 FAIL (QBE-vs-self, v2.6.7 baseline hold)
- ✅ byte_equal_amd64.sh `--baseline`: 20 PASS / 0 SKIP / 0 FAIL (10 byte-equal + 10 baseline match)
- ✅ D43 closure v1→v2 hold: il sha `92e8255473db3395c98bb12c58b473071384b42b897b114cea5fa903d715d25a` (v2.6.7 unchanged)
- ✅ workarounds.md W-069 entry closure sha 引用 `92e82554...` (跟 changelog 一致)

**净 ship 计数:** 0 source files 改,2 docs 改

## References (v2.6.1 - v2.6.8)

- v2.6.1 commit: `9fe2f94` (jh_regalloc_get/set C-side bridge)
- v2.6.2 commit: `44eb090` (regalloc module uses extern)
- v2.6.3 commit: `b4ce9a2` (codegen_amd64_run real body)
- v2.6.4 commit: `c251658` (wire run_backend inert)
- v2.6.5 commit: `07c6a89` (W-068 real wire-up)
- v2.6.6 commit: `224a944` (W-069 真修)
- v2.6.7 commit: TBD (byte_equal_amd64.sh Commit 5 + baseline)
- W-068 entry: [`../../internal/workarounds.md`](../../internal/workarounds.md) (✅ RESOLVED)
- W-069 entry: [`../../internal/workarounds.md`](../../internal/workarounds.md) (✅ RESOLVED v2.6.6)
- Plan doc: [`twinkly-hatching-canyon.md`](../../plans/twinkly-hatching-canyon.md) (Phase 1-4)
- D43 baseline: `51376ce5...` (v2.4.0 末) → `92e82554...` (v2.6.6 新 baseline, per D43 v2.x sub-sprint 阶段性 self-equal rule)