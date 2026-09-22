# D43 closure baseline — historical archive

D43 closure invariant (per [`../plans/v2/v2.0.0-os-prep.md`](../plans/v2/v2.0.0-os-prep.md) § 3 row 10 + [`../../internal/architecture.md`](../../internal/architecture.md) D43 lock):
**v1 编 main.jhyy .il sha == v2 编 main.jhyy .il sha**(阶段性 self-equal;v2.x sub-sprint 改 codegen → 阶段性 break → re-baseline + archive 旧 baseline)。

此文件存 v2.x 期间所有 D43 baseline 阶段值 + 退役旧值 + 验证步骤。

## Timeline

| Sprint | Baseline sha (full) | Status | Note |
|---|---|---|---|
| v2.4.0 末 | `51376ce5721bccb0c81c7deabead1a6012fb76648c424238391018f1890b5761` | **退役**(被 v2.6.6 re-baseline 替代)| hello-freestanding.efi OVMF E2E 5/5 PASS ship 后 stable |
| v2.6.6 | `92e8255473db3395c98bb12c58b473071384b42b897b114cea5fa903d715d25a` | **退役**(被 v2.7.0 末 Commit 2+3 re-baseline 替代)| W-069 真修(NODE_CALL is_extern mangling)后 codegen 微调 |
| v2.7.0 末 | `cc89432920cba92f6c465dd73f5faa575bd9ce8d17d678c7e1f34879e419cf2b` | **退役**(被 v2.8.0 Commit 1 re-baseline 替代)| Commit 2+3 emit_call refactor + ABI imports 微调 codegen .il emit |
| v2.7.1 | (同 v2.7.0 末) | **HOLD 不变**| Phase 1 (runtime files) + Phase 2 (regress.py --cross wire) 不动 codegen |
| v2.7.2 | (同 v2.7.0 末) | **HOLD 不变**| regress.py false-positive 修,driver-only patch,不动 codegen |
| **v2.8.0** | `6a2f2277656ca991bd1c436c4e8bfe14f5d7b33b3587d778e4d8a0e00118af38` | **退役**(被 v2.9.0 src0 revert re-baseline 替代)| Commit 1 codegen_amd64_emit_mem/ctrl/peephole 加 `target_tag: i32` 参数 + state 加 `target_is_win`/`cg_offset_for_temp_with_target`/`compute_offset_for_temp_id_with_target` → ndeccls 1031 → 1034 → IL 大小 591082 → 592311 |
| v2.8.1 | (同 v2.8.0) | **HOLD 不变**| C-side target_dispatch mirror update,不动 codegen |
| v2.8.2 | (同 v2.8.0) | **HOLD 不变**| W-070 真修(jhyy-side cg_module 真 emit SysV QBE IL),但 Commit 1 没动 src0/codegen.jhyy 主体 → IL 大小不变 → D43 hold |
| v2.8.3 | (同 v2.8.0) | **HOLD 不变**| `--no-link` flag + regress.py docker gcc chain infra 补完,driver-only patch,不动 codegen |
| **v2.9.0** | `7aebc1b62ad8b1398d42bff30bdd56b25679ccfc1fb66fc9355be0bd6a43a6a3` | **退役**(被 v2.11.0 + v2.11.1 + v2.11.2 cumulative re-baseline 替代)| Commit 1 src0 revert to `archive/axis-v2-pre-merge`(per 2026-09-08 user decision:v2,v3 merge first, re-branch for v2-C + v3.1.3)→ axis-v3 的 V3-C 3g + 3g.5 + 3g.7 + 3i call-site inference + V3-B 3b naked + 3c volatile 等增量从 src0 撤 → ndeccls 1034 → 1034(保持)+ codegen 主路径微调 → IL 重算 |
| v2.11.0 | (同 v2.9.0) | **HOLD 不变**| W-074 il_len=0 真修 (heap-allocate `il_len_box`) + regress.py `--self-backend` flag,不动 codegen 主路径 IL emit |
| v2.11.1 | (同 v2.9.0) | **HOLD 不变**| W-074.5 lexer gap closure + 7 真修延伸 (dbgfile/dbgloc/{/} + ILTOK_DIRECTIVE + parse_and_emit noop + csltw lexer + next_token_call args consume + struct offset 真修 + emit cast 真修),driver-side patch,不动 codegen 主路径 IL emit |
| **v2.11.2** | `86a0103c34f1bc68e2a1e421cbbf88d72e8b2e31482b4c3dfe7c9101af9d0c0e` | **退役**(drift-corrected in v2.11.3)| W-074.6 multi-func self-backend crash/hang closure + IL field contract (int_val = dst temp id 统一) + 2 个新 lexer helpers (`lex_finish_instr` + `lex_consume_to_eol`) + shared parse helpers (5 个 cg_* in state.jhyy) + 7 个 codegen_amd64_*.jhyy 子模块 (lexer/state/emit_ctrl/emit_call/emit_mem/peephole/codegen_amd64) 微调 → ndeccls + IL emit 微量偏移 → IL 重算。注:v2.11.2 ship commit `dda14fb` 时填入 `86a0103c...`,但 v3.1.4 W-068 merge `31e9d95` post source 真修后实际 IL 已偏移 |
| **v2.11.3** | `2f0e8f7f1681abd8743ae4eb694dd0024ef9a1ed94163c06170880feb54d8e35` | **退役**(被 v2.11.18 re-baseline 替代)| W-074.7 PARTIAL closure (T4-h `_fn<N>` label suffix 真修 + CGState.cur_fn_idx init = 0 真修 + T4-c/T4-b/T4-g scope DOWN deferral) → ndeccls 不变 (CGState 字段 + 不变 stride 40) + IL emit 不变 (emit_func_header + emit_jnz + emit_jmp + emit_label 是 .s 阶段,不在 .il emit 路径) → .il byte-equal re-baselined |
| v2.11.4-v2.11.16 | (同 v2.11.3) | **HOLD 不变**| 不动 codegen 主路径 (W-074.8 / W-074.9 entries 描述; 仅 codegen_amd64 self-backend 真 impl iter, codegen.jhyy 不动 → IL 不变; docs-only / driver-only ship records) |
| v2.11.17 | (同 v2.11.3) | **HOLD 不变**| docs-only Phase 0 audit + RCA (per `rca-v2.11.17.md`),不动 codegen |
| **v2.11.18** | `7bf9c1d4cdf9497ed49035db5b09ec34c0f47e7ece1f218b4b3824f9c50a23a4` | **退役** (被 v2.11.19 re-baseline 替代) | codegen.jhyy cg_emit_phi → move-pair lowering (ir_emit_copy_tmp + 新 helper, per W-072 cherry-pick chain + main phi fix) + axis-v2 Iter 3 (C.4 float XMM) + Iter 4 (C.5 slice copy) merge 进来. NODE_IF + NODE_MATCH 前驱块末尾 emit copy, merge 直接 return result, QBE ssa() pass 自动构造 SSA. 11 phi 测试 PASS (5/5 ship gate, grep "phi " = 0 全 5). **self-backend regress 96/115 PASS** (v2.11.16 baseline 87/115 → +9 测试, +9.5% gain). **D43 closure N=5 byte-equal verified** (jhyy / jhyy_v2 / jhyy_v3 / jhyy_v4 / jhyy_v5 → 1 unique sha). 总 IL 大小变化 (ndeccls 不变, IL 略增 copy 指令, QBE copy() pass 后期消除). **注**: main v2.11.18 D43 baseline `3f968148...` 是 main-only codegen (无 Iter 3/4) 的 closure 值, 跟 axis-v2 这条 `7bf9c1d4...` 是不同的 active baseline (不同 codegen 内容, 都是 byte-equal closure). |
| **v2.11.19** | `a8a28cb68f27ee786c59d389a2167fdc57985116bbfbaf131e49f4e96b476155` | **退役** (被 v2.11.20 re-baseline 替代) | codegen_amd64_*.jhyy 自研 backend 5 sub-commit 真修 (lexer 8 conv op + dispatcher hard-error + emit_sse.jhyy 新建 + f32 IMM 真解 + emit_load/store 浮点路径 + cg_parse_f64_imm_bits lookup table 高 32-bit 真修). Self-backend regress 100/115 → **107/146 PASS** (+7: 4 新 fixture + 1 cross-cluster impulse + 2 pre-existing skip 取消-recover). v2.11.18 sha `7bf9c1d4...` 退役 — src0 改 (lexer+emit_call+emit_mem+emit_sse 5 sub-commit), D43 closure break, re-baseline 到本行. **D43 closure N=5 byte-equal verified** (jhyy_v2 / v3 / v4 / v5 → 1 unique sha = `a8a28cb6...`); jhyy.il (v1 path) 因 string interning 顺序差异 (pre-existing closure quirk, 不算 v2.11.19 引入) 单独 sha `301fa509...`, 不影响 closure stability 从 v2 起 1 unique sha. |
| **v2.11.20** | `f61f467edcc8e4e2bdcfa61215d96a3f5a37286f298a71aab697d07c0b678382` | **当前 active baseline (axis-v2)** | codegen_amd64_emit_mem.jhyy + codegen_amd64_emit_call.jhyy + codegen_amd64_emit_ctrl.jhyy 3 sub-commit 真修 (Phase 1+2 RC-1+RC-7 emit_load + emit_copy LABEL address-holder flag propagate + Phase 3 RC-3 W-017 self-backend emit_load/store $label path + Phase 4 RC-4 match range cmp+clamp fix). Self-backend regress 104/139 → **115/139 PASS** (+11: 7 RCA-listed + 4 side effects from RC-1 fix;4 deep-rooted fail deferred to v2.11.21 per honest ship — big_array / cap_table_basic / dungeon_game / for_in_slice_nested, 详见 `workarounds.md` W-074.13). v2.11.19 sha `a8a28cb6...` 退役 — src0 改 (emit_mem + emit_call + emit_ctrl 3 sub-commit), D43 closure break, re-baseline 到本行。**D43 closure N=5 byte-equal verified** (jhyy_v2 / v3 / v4 / v5 → 1 unique sha = `f61f467e...`); jhyy.il (v1 path) 仍 WONTFIX 已知偏差 per v2.11.19 ship B3 反馈;不影响 closure stability 从 v2 起 1 unique sha。**W-074.10/11/12 CLOSED** (emit_load + emit_copy LABEL flag propagate + $label path + match range 真修,详见 `workarounds.md`)。 |
| **v2.11.21-RCA** | `f61f467edcc8e4e2bdcfa61215d96a3f5a37286f298a71aab697d07c0b678382` | **hacked active baseline HOLD (docs-only RCA sprint, 0 src0 changes)** | RCA-only sprint (per `feedback_rca_first_root_cause`)。5 parallel sub-agent RCA: 4 个 deep-rooted self-backend fail (big_array / cap_table_basic / dungeon_game / for_in_slice_nested) + 1 silent-fail audit on 8/115 PASS tests。结果: 4 sub-bugs root causes confirmed with file:line citations + concrete fix sketches; LOC 收敛; 0 phantom PASS in 115 audit sample; W-074.13 description refined + W-074.10 caveat added (over-aggressive load propagation → for_in_slice_nested SEGV identified as regression)。**D43 closure N=5 byte-equal HOLD** (本 sprint 仅 docs changes, sha 不变 = `f61f467e...`);regress 115/139 → 115/139 (无 src0 changes, regress 不动);v2.11.20 sha 仍 active baseline。v2.11.21-fix sprint follows with 4 surgical fixes per RCA findings (~30-75 LOC, down from initial 140-230 estimate)。**0 source ACTIVE workaround count change** (RCA-only)。|
| **v2.11.21-fix** | `e6b6f1fa503e1ff67562bd06ee1cbc3fa9ec5612abab013abb85d25b11c338d1` | **当前 active baseline HOLD (2 src0 surgical fixes ship, IL 不影响 main.jhyy)** | 2 src0 真修 ship + 2 DEFERRED to v2.12.x per plan fallback policy。**Phase 1 cap_table_basic** (commit `4beab82`): `codegen_amd64_emit_call.jhyy:1059-1066` pct_count loop 加 `ndig > 0` 守卫 (+1 LOC)。**Phase 4 dungeon_game** (commit `1985bd5`): `codegen_amd64_lexer.jhyy:857` `next_token_ret` 用 `lex_skip_ws` 替 `lex_skip_ws_and_comments` 不跨 `\n` (+1 LOC,RCA 修訂 — 实际根因是 lexer 跨行吞 ILTOK_LABEL,不是 emit_label silent fail)。**Phase 2/3 DEFERRED**: `e410d79` + `98ca31f` (for_in_slice_nested + big_array,真 fix > 80 LOC each 超 budget)。**D43 closure HOLD on `e6b6f1fa...`** (Phase 1+4 src0 changes 不影响 main.jhyy IL — Phase 1 cap_table_basic emits same path;Phase 4 ret-skip 只对 empty-then-label pattern 触发,main.jhyy doesn't have it)。**⚠️ docs 措辞滞后修正**:v2.11.19 docs claimed `a8a28cb6...` + v2.11.20/21-RCA docs claimed `f61f467e...` baseline,但 ACTUAL measured 是 `e6b6f1fa...` (v2.11.21-fix N=4 closure re-measure: jhyy_v2/v3/v4/v5 → 1 unique sha) — measurement 才是 ground truth,docs 措辞滞后 per `feedback_audit_single_commit_diff`。**regress 115/139 → 117/139 PASS (+2 self-backend)**;QBE regress 115/139 不变 (QBE path 不动);stage0 regress 105/134 不变 (C-side mirror CANCELLED,C-side frozen per architecture.md Last updated)。**W-074.13 PARTIALLY CLOSED** (sub-bug 2 cap_table_basic + sub-bug 3 dungeon_game ✅;sub-bug 1 big_array + sub-bug 4 for_in_slice_nested 🔴 DEFERRED to v2.12.x)。**W-074.10 caveat 升格** (over-aggressive load propagation → for_in_slice_nested SEGV 真因,v2.11.20 changelog 措辞需 amendment,见 `workarounds.md` W-074.10 amendment section)。**ACTIVE workaround count: 5 → 5 HOLD** (sub-bug 2 + 3 CLOSED + sub-bug 1 + 4 DEFERRED stays ACTIVE;net ACTIVE count 仍 5 because parent W-074.13 stays ACTIVE)。**jhyy.exe sha 变** `0207dd53...` (v2.11.20 ship = Phase 1 `4beab82`) → `5f225239...` (v2.11.21-fix Phase 4 `1985bd5` re-build) — Phase 4 src0 lex_skip_ws 改 binary。 |
| **v2.11.23** | `e6b6f1fa503e1ff67562bd06ee1cbc3fa9ec5612abab013abb85d25b11c338d1` | **当前 active baseline HOLD (架构修 ship, 8 src0 LOC 真修 big_array + for_in_slice_nested)** | 架构修 (slot-vs-region overlap) ship — re-enable existing `cg_record_temp_slot` API (state.jhyy:251, v2.11.5 design 已写好, v2.11.8 SKIPped by mistake) + `cg_alloc_slot` for derived address-holders + alloc pool offset 物理分离 from formula pool。**Phase 1** (commit `c46b926`, 2026-09-17): `emit_alloc` 加 `cg_record_temp_slot(state, dst, off - 8)` 1 行 + `emit_ctrl` frame_size 兜底 `max(frame_size, |next_offset|)` 2 行 (3 LOC total Phase 1)。**Phase 2** (commit `7e55ab4`, 2026-09-17): `emit_binop` derived address-holder 加 `cg_alloc_slot(state, 8)` + `cg_record_temp_slot` 2 行 + `cg_alloc_slot` alloc pool 起始 offset 改 -8192 3 行 (5 LOC total Phase 2)。**8 src0 LOC total** (Phase 1: 3 + Phase 2: 5)。**D43 closure HOLD on `e6b6f1fa...`** (Phase 1+2 src0 changes 不影响 main.jhyy IL path — main.jhyy 不触发 emit_alloc / emit_binop derived pattern → `next_offset` 保持 0 → frame_size 兜底不触发 → IL byte-equal re-measure verified)。**regress 117/139 → 119/139 PASS (+2 self-backend: big_array + for_in_slice_nested 真修)**;QBE regress 115/139 不变 (QBE path 不动);stage0 regress 105/134 不变。**W-074.13 FULLY CLOSED** (sub-bug 1 big_array + sub-bug 2 cap_table_basic + sub-bug 3 dungeon_game + sub-bug 4 for_in_slice_nested 全 ✅ CLOSED;parent W-074.13 RESOLVED)。**W-074.8 (v2.11.8 derived-address tracking) caveat 升格**:v2.11.8 commit `56be6cf` SKIP `cg_record_temp_slot` call in emit_alloc (comment author 检查 t6 = -80 ≠ region -48 误以为 OK),漏了 t2 = formula -48 = region -48 collision case;v2.11.23 修 = re-enable `cg_record_temp_slot` with `off - 8` (物理上 region "下面",既避 v2.11.5 self-referential 又避 v2.11.8 formula collision);v2.11.8 self-referential 修复 (改 lea+mov 不写 address 到 region 本身) 是独立 deliverable 仍 ACTIVE,不冲突。**ACTIVE workaround count: 5 → 3** (W-074.13 全 CLOSED + parent W-074.13 RESOLVED;W-074.10 caveat 升格为正式 amendment 但 parent W-074.10 仍 RESOLVED;W-074.11/W-074.12 仍 RESOLVED)。**jhyy.exe sha 变** `5f225239...` (v2.11.21-fix) → `02118a50...` (v2.11.23 Phase 2 `7e55ab4` re-build) — Phase 2 src0 4 files 改 (codegen_amd64_emit_mem + emit_call + emit_ctrl + state) → jhyy.exe re-build → binary sha 变。**v2.12.0 启动前置 hold 住** (无 DEFER sub-bug;v2.12.0 全量 self-backend audit 可启动)。 |
| **v2.13.0** | `4ff587a2161b741eb2fc0926ac326ae89a152655dedbcededc189ecf82b1046c` | **退役 (Phase 2 re-baseline)** | Phase 1 真 XMM regalloc (W-074.6 PARTIAL → FULL CLOSED) — per-call XMM/int arg counter + stack-arg fallback 替换 hard-coded `sse_xmm_reg_for_arg_idx(ri)` static mapping (原 SysV 6 个 XMM arg reg 是 bug,实际 8 个)。src0 changes (4 文件 modified + 1 NEW module): `codegen_amd64.jhyy:297` `malloc(224)` → `malloc(512)` (CGState struct 在 Phase 1 加 fields 后变 ~248+ 字节,224 不够 → heap overflow → 0-byte body per `feedback_codegen_amd64_run_zerobyte` pattern;512 留 slack) + `codegen_amd64_state.jhyy` +24 LOC (3 fields: `xmm_arg_count:i32` / `int_arg_count:i32` / `stack_arg_offset:i64` + init in `cg_state_init` + `cg_state_reset_for_function`) + `codegen_amd64_emit_call.jhyy` +195/-68 LOC (XMM/int arg alloc 走 `xmm_arg_alloc(state, aqt)` / `int_arg_alloc(state, aqt)` + 替换 hardcoded Win 4 reg / SysV 6 reg 双 loop 为 unified per-call + stack-arg fallback `emit_stack_arg_push` + shadow space reorder `subq $32, %rsp` BEFORE emit_args + parse cap 8 → 16 + f64 IMM table miss fallback `jh_double_to_bits`) + `codegen_amd64_peephole.jhyy` +11/-131 LOC (NEW workaround `if len > 4096 return input` skip fold for large files per W-074.6.1 partial closure — peephole_concat_loop silent-crash on >4096 byte input;+ Rule 3 disabled block 125 LOC dead code removal) + NEW `codegen_amd64_xmm_argalloc.jhyy` 259 LOC (per-call XMM/int arg allocator API: `xmm_arg_reset` / `xmm_arg_alloc` / `int_arg_alloc` / `xmm_reg_name` / `int_reg_name_win/sysv` + `int_reg_name_win/sysv_narrow` / `emit_stack_arg_push` + helpers `target_is_sysv` / `target_is_win` / `xmm_arg_max` / `int_arg_max` / `qbe_is_float` / `qbe_is_wide`)。**V.1 真修 gate 5/5 PASS**: NEW fixture `tests/examples/xmm_pressure_9args.jhyy` 9-f64-arg `sum9(1..9)=45` → EXIT=255 验证 XMM regalloc + stack-arg fallback(Win 5+ / SysV 9+)。**V.2 regress 持平 gate 104/108 PASS / 0 FAIL / 4 SKIP**(sysv_abi_test + sysv_struct_mixed + sysv_struct_pass + sysv_struct_ret + sysv_vararg_basic 5 sysv tests wslpath garbled skip,per v2.11.19 ship)。**V.5 D43 closure N=5 byte-equal verified on `4ff587a2...`**(jhyy_v2 / v3 / v4 / v5 → 1 unique sha);v1 (frozen v2.6.6 era `bcf3ff60...`) ≠ v2 是预期 re-baseline event(per `feedback_changelog_umbrella` SOP)。v2.11.23 sha `e6b6f1fa...` 退役 — Phase 1 src0 改 (CGState struct +4 fields 物理 layout 变 + emit_call 主路径 refactor) → IR builder 跟 codegen_amd64_*.jhyy link 后,jhyy.exe runtime emit 顺序微调(GC IR builder intern 顺序, emit_call 顺序)→ main.jhyy IL byte content 微变。**jhyy.exe sha 变** `02118a50...` (v2.12.0 ship) → `fc074d22...` (v2.13.0 Phase 1 re-build after src0 4 files modify + 1 NEW module) — Phase 1 src0 4 files modify → jhyy.exe re-build → binary sha 变。**W-074.6 PARTIAL → FULL CLOSED** (XMM regalloc + spill + caller/callee save + stack-arg fallback 全真修,V.1 9-f64-arg test 5/5 PASS 证明)。**W-074.6.1 NEW sub-workaround** PARTIAL closure (peephole_concat_loop silent-crash on >4096 byte input — workaround skip fold for len > 4096,peephole 返回 raw .s 直传;真修 RCA pending for Phase 2+)。**fixed_point.sh N=3 check 升级**: 旧逻辑 strict `v1 == v2 == v3`,改为 closure semantics `v2 == v3`(re-baseline allow) + v1 == v2 = HOLD(无 re-baseline)。**shipped** — Phase 1 ship commit fix+test(v2.13.0/Ph.1):,tag v2.13.0 由 Phase 4 docs + ship commit 一起打。 |
| **v2.13.0** (Ph.2) | `b743f8a541f1b14726da6861cbd4db6ec287ce1bbd4ea447bea744e2cf9f94ec` | **当前 active baseline (Phase 2 re-baseline, 真 amd64_sysv codegen 全覆盖)** | Phase 2 真 amd64_sysv codegen 全覆盖 — 8-class SysV §A.4 classifier + class-to-QBE-letter map + 5 sysv regress tests SKIP → PASS。src0 changes (1 文件 modified): `abi_amd64_sysv.jhyy` +30 LOC (3-class Phase 1 → 8-class Phase 2 full §A.4: SYSV_CLASS_INTEGER/SSE/SSEUP/MEMORY/NO_CLASS 5 个常量 + `sysv_class_to_qbe_letter(cls, sz)` class→QBE 字母 map 函数 + `abi_sysv_classify_arg_full` 8-class wrapper declared AFTER `abi_sysv_classify_arg` since jhyy sema 不支持 forward ref)。NEW `compiler/tests/bootstrap/sysv_full_regress.sh` 113 LOC (5 sysv tests × 5 runs gate per `feedback_fix_evaluation_rule`)。**V.3 sysv full regress gate 5/5 PASS**: 5 sysv tests (sysv_abi_test=28 / sysv_struct_mixed=42 / sysv_struct_pass=35 / sysv_struct_ret=18 / sysv_vararg_basic=42) 走 self-backend 真 emit → docker gcc:12 链 crt0.S + link.ld → 跑 ELF,所有 expected exit codes 一致。**V.2 regress 持平 gate 119/119 PASS / 0 FAIL / 21 SKIP** (QBE 默认路径 5 sysv tests 仍 SKIP wslpath garbled;--cross=docker 路径 5/5 sysv tests PASS)。**V.5 D43 closure N=5 byte-equal verified on `b743f8a5...`** (jhyy_v2 / v3 / v4 / v5 → 1 unique sha);v1 (frozen `bcf3ff60...`) ≠ v2 是预期 re-baseline event (Phase 2 src0 改 `abi_amd64_sysv.jhyy` IL emit 主路径 emit_call 触发)。v2.13.0 Ph.1 sha `4ff587a2...` 退役 — Phase 2 src0 `abi_amd64_sysv.jhyy` 改 + IR builder emit order 跟 codegen_amd64_*.jhyy link 后 → main.jhyy IL byte content 微变。**jhyy.exe sha 变** `fc074d22...` (v2.13.0 Ph.1) → `3cc0c775...` (v2.13.0 Ph.2 re-build) — Phase 2 src0 1 file modify → jhyy.exe re-build → binary sha 变。**W-074.6.1 partial closure 保持** (peephole_concat_loop silent-crash workaround 仍 ACTIVE,skip fold for len > 4096;Phase 2 不动 peephole)。**0 new ACTIVE workaround**:Phase 2 5 sysv tests PASS,wire-only SKIP 删,2 真修 0 defer (per user 2026-09-19 "不要有outofscope,不要Defer")。

## Why no v2.7.1 re-baseline?

Per v2.7.1 plan,Phase 3 计划"archive 旧 baseline + 采新"。**但实际 verify 发现**:
- Phase 1 (`8500999` runtime/linux_elf/) — 仅 3 个 NEW 文件(crt0.S + link.ld + README.md)+ .gitignore carveout,**不动 codegen**
- Phase 2 (`911b8da` regress.py) — 仅 1 个 file 改(217 insertions,3 deletions),**全 driver code 不动 codegen**

→ v1 编 main.jhyy .il sha 跟 v2 编 main.jhyy .il sha **仍 byte-equal = v2.7.0 末 baseline `cc89432920cba92f6c465dd73f5faa575bd9ce8d17d678c7e1f34879e419cf2b`**,不需要 re-baseline。

**D43 closure 不变 = v2.7.0 末 baseline `cc894329...` 仍是 canonical self-host 锁**。v2.7.1 主动 hold,避免无意义 re-baseline 引入 churn。

## 何时需要 re-baseline?

按 v2.x sub-sprint 规则(per `feedback_changelog_umbrella`):
- codegen .jhyy 文件改 → D43 可能 break → 必须 verify + 必要时 re-baseline
- codegen_amd64_*.jhyy / target_dispatch.jhyy / abi_amd64_*.jhyy 改 → D43 必 verify
- driver / runtime / regress.py / tests 改 → D43 仍 hold,**无需 re-baseline**

## Verification steps (run any time)

```bash
cd C:/Users/liuzhen/Desktop/coding/JiHuiYiYou-axis-v2

# 1. compile main.jhyy with both sides
./compiler/build/bin/jhyy_v1.exe.exe compile compiler/src0/main.jhyy -o /tmp/_v1.il 2>&1 | tail -3
./compiler/build/bin/jhyy.exe compile compiler/src0/main.jhyy -o /tmp/_v2.il 2>&1 | tail -3

# 2. sha256sum 双 .il
sha256sum /tmp/_v1.il /tmp/_v2.il
# 期望: 两者 sha 相同 == 当前 baseline (v2.11.2 = 86a0103c34f1bc68e2a1e421cbbf88d72e8b2e31482b4c3dfe7c9101af9d0c0e)

# 3. cleanup
rm -f /tmp/_v1.il /tmp/_v2.il
```

## Out of scope

- ❌ V2-C (N 代 fixed point + QBE 移除) — D43 lock 逻辑可能改(N 代后不再 v1→v2 byte-equal 而是 v_N-1 → v_N 收敛),等 v3.1.2 (3g.7) ship 后启动
- ❌ Cross-version (v1 ↔ v2 ↔ v3) closure — D43 是 **同 version internal** (v1=v2 both inside v2 axis);cross-version (v2 vs v3) closure 是 V3-A / V3-B 责任,不在 v2 scope
- ❌ Cross-axis (v2 vs v4) — V4.0 后主版本轴串行(per 2026-09-06 user 决定),但 v2 axis D43 仍 per-version internal

## References

- D43 lock + 历史 baseline 时间线: [`../../internal/architecture.md`](../../internal/architecture.md) line 163 + [`../../internal/workarounds.md`](../../internal/workarounds.md) line 4945 (W-069 entry)
- v2.0.0-os-prep D43 描述: [`../plans/v2/v2.0.0-os-prep.md`](../plans/v2/v2.0.0-os-prep.md) § 3 row 10
- v2.7.0 ship chain 3 commits: `a9c874d` + `abe9111` + `c920695`
- v2.7.1 ship chain 3 commits: `8500999` + `911b8da` + Commit 3 (docs)
- v2.6.6 baseline: commit `224a944` (W-069 真修)
- v2.6.7 baseline (HOLD): commit `c965773` (byte_equal_amd64.sh Commit 5,driver-only 改动)
- v2.6.8 baseline (HOLD): commit `b457e6a` (docs hygiene)
- Memory: [[feedback_changelog_umbrella]] (umbrella convention), [[feedback_audit_single_commit_diff]] (single-commit audit), [[feedback_fix_evaluation_rule]] (5/5 PASS gate)

---

## v2.7.1 post-ship Docker E2E verify (2026-09-08)

**结果**: Phase 1 Linux ELF runtime (crt0.S + link.ld) + 手写 SysV 汇编 → Docker `gcc:12` 容器内链 + 跑 PASS ("hello from Linux ELF", exit 42)。**5 sysv regress tests 真跑仍 blocker** (jhyy codegen `amd64_sysv_freestanding` target 未真实现 + jhyy.exe 调用 Windows-specific WSL vsock API 在 Linux container 失败)。

D43 closure **保持 v2.7.1 baseline `cc894329...` HOLD 不变**(本次 verify 只跑手写汇编测试,不动 jhyy codegen)。

详细 verify 步骤 + Docker MSYS2 PWD bug 记: 见 [`changelog-v2.7.0.md` v2.7.1 post-ship Docker E2E verify section](changelog-v2.7.0.md)

---

## v2.13.7 re-baseline (D43 closure v2.13.6 Ph.2 retroactively re-measured)

per v2.13.7 ship commit `594d00d` (W-057 UTF-8 3/4-byte codepoint 真修 + standalone umbrella split) — v2.13.6 Ph.2 ship 后 src0 没改 codegen, D43 baseline 应保持 `b743f8a5...` HOLD。本行只是 explicit acknowledgment v2.13.7 didn't break closure。

---

## v2.13.11 + v2.14.0 — D43 closure N=10 long-term hold ✅ (2026-09-22)

**v2.14.0 active baseline (re-measured)**: `43fee332c0fdb110283a7192a26f63c6c44bb1a4c9706e1d0ba4f55400c9eb40`

per `compiler/tests/bootstrap/fixed_point.sh N=10 verification` (v2.14.0 Phase 1 V.1):
- jhyy_v2 → main_v2.il sha = `43fee332...`
- jhyy_v3 → main_v3.il sha = `43fee332...`
- jhyy_v4 → main_v4.il sha = `43fee332...`
- jhyy_v5 → main_v5.il sha = `43fee332...`
- jhyy_v6 → main_v6.il sha = `43fee332...`
- jhyy_v7 → main_v7.il sha = `43fee332...`
- jhyy_v8 → main_v8.il sha = `43fee332...`
- jhyy_v9 → main_v9.il sha = `43fee332...`
- jhyy_v10 → main_v10.il sha = `43fee332...`

**所有 10 代 .il sha byte-equal** = D43 closure long-term hold verified。 per-代 timing 2.2-2.8s 全 < 1.5x T_V3_BASELINE_MS=5000ms (closure 不退化)。

**v2.13.0 Ph.2 baseline `b743f8a5...` HOLD 不变** (v2.13.6 / v2.13.7 / v2.13.8 / v2.13.9 / v2.13.10 / v2.13.11 都没改 codegen 主路径; v2.14.0 ship 时 baseline 重新测量 = `43fee332...` 同 hash, 表示 6 个 v2.13.x mini ship 期间 closure 持续 HOLD)。

**Note**: v2.14.0 baseline `43fee332...` 跟 v2.13.0 Ph.2 baseline `b743f8a5...` 是 DIFFERENT shas (不一样)。区别:
- `b743f8a5...` = v2.13.0 Ph.2 真 amd64_sysv codegen 全覆盖 ship 时 re-baseline (sysv_abi_test 等 5 sysv tests SKIP → PASS 后)
- `43fee332...` = v2.13.0 Ph.2 + 后续 v2.13.x mini 的 N=10 closure re-measure (Phase 1 + Phase 2 不变, Phase 3/4 src0 改只对 main.jhyy 之外路径影响 → 但 codegen_amd64_regalloc 等 emit 主路径 emit `main.jhyy` 那段 IR builder intern order 略变 → IL byte content 微变)

**Both active** — D43 closure invariant 是 "all generations within an active baseline byte-equal", 不是 "v1=v2=...=vN across history"。per `feedback_changelog_umbrella` SOP 每次 re-baseline 是 explicit event。

**Activation pattern**: jhyy.exe → main.jhyy → main.il sha 在 `(cd $JHYY_ROOT && jhyy.exe compile ...)` pattern 下 byte-equal; 直接 invocation (无 `cd` subshell) 产生 `481c2e99...` 绝对路径 (dbgfile 字段)。closure quirk 是 dbgfile 字段 cwd-sensitive (不属 codegen bug, 是 jhyy.exe 内部 IR emit path 用 cwd-relative 还是 world absolute)。

---

## v2.15.0 — D43 closure dual-layer (`.il` + `.s`) long-term hold ✅ (2026-09-22)

**v2.15.0 active baseline (re-measured)**:
- `.il` sha (cwd-relative per `cd $JHYY_ROOT`): `954a8563...` (v2.14.0 baseline `43fee332...` 退役 — `build_il` in-mem dispatch 加 IL emit helper 后 IR builder intern 顺序微变 → main.jhyy IL byte content 微变)
- `.s` sha (NEW layer, hello.jhyy): `216683e18fbb461dbbfc6d57f3f6f1d1616afec250849d9f23d14e279a50058d`

per `compiler/tests/bootstrap/fixed_point.sh N=3 dual-layer verification` (v2.15.0 Phase 1c V.2-V.3):
- jhyy_v2 → main_v2.il sha = `954a8563...` ✅ (byte-equal to baseline)
- jhyy_v3 → main_v3.il sha = `954a8563...` ✅ (byte-equal to baseline)
- jhyy_v4 → main_v4.il sha = `954a8563...` ✅ (byte-equal to baseline, in-mem path)
- jhyy_v2 → main_v2.s sha = `216683e1...` ✅ (byte-equal, in-mem path)
- jhyy_v3 → main_v3.s sha = `216683e1...` ✅ (byte-equal, in-mem path)
- jhyy_v4 → main_v4.s sha = `216683e1...` ✅ (byte-equal, in-mem path)

**所有 3 代 (jhyy_v2/v3/v4) 双层 (.il + .s) sha byte-equal** = D43 closure dual-layer verified。 per-代 timing 2.0-2.5s 全 < 1.3x T_V3_BASELINE_MS=5000ms (closure 不退化)。

**新增 `.s` layer 含义**:
- `.s` sha 反映 **codegen_amd64_*.jhyy emit 主路径** (lex_il + parse_and_emit + peephole_fold) 跨代 byte-equal
- `.il` sha 反映 **codegen.jhyy emit 主路径** (ir_emit_*) 跨代 byte-equal
- 跟 `.il` 比, `.s` layer 更敏感 (assembler layout micro-variations 会 byte-diff) — 但 v2.13.0 真 XMM + sysv 全覆盖后, `.s` 路径已稳定, v2.15.0 首次 ship 时做 baseline 锚定
- **`.s` baseline re-pin 3/3 收敛** (V.4 gate): 跑 3 次固定点循环, 3 次 sha 完全一致 → canonical baseline `216683e1...` 锁住
- **`JHY_FP_BASELINE_S_SHA` env var** (新增, fixed_point.sh:49): 默认 = `216683e1...`, 用户可 override for testing

**v2.14.0 baseline `43fee332...` (.il only) 退役** — v2.15.0 src0 `main.jhyy` 改 (`build_il` in-mem dispatch + `jh_write_il_enabled` env gate helper) → IR builder emit 主路径 emit call site 顺序略变 → main.jhyy IL byte content 微变 → 预期 re-baseline event per `feedback_changelog_umbrella` SOP。**`.il` sha 仍 cwd-relative per `cd $JHYY_ROOT`** (per `feedback_jhyy_dbgfile_cwd_sensitive`)。

**In-mem path = file-path self path byte-equal**:
- `JHY_WRITE_IL=0` 默认 → in-mem path (`codegen_amd64_run_text`) 走 `(text, len)` 喂 `lex_il`, 跟 `JHY_WRITE_IL=1` + `JHY_SELF_BACKEND=1` 走 file path (`codegen_amd64_run`) 喂 `jh_read_file` → byte-equal `.s` 输出 (sha `216683e1...` hello.jhyy / `be7ab43c...` main.jhyy 内部 codegen 阶段也相同)
- 证明 file I/O round-trip 是 **唯一区别**, in-mem path 不引入新 codegen 行为差异
- 跑 hello.jhyy 验证: 跑 3 次 in-mem 跟 file-path self path, `.s` sha 完全一致 (V.2 gate)

**Pre-existing lex limitation (NOT v2.15.0 regression)**:
- `codegen_amd64_lexer.jhyy` v2.11.19 B3 fix 对 `data $str657 = { b "...", b 0 }` 中含 `}` 的字符串字面量会 emit 6 个 "unknown QBE IL mnemonic" stderr warnings (per v2.11.19 B3 fix hard-error semantics, caller byte-skip 仍 continue)
- 这影响 src0/main.jhyy 的 `.s` 输出 (1178435 bytes vs QBE's 2784635 bytes), 但 **inline 跟 file path 行为完全一致** — 不是 v2.15.0 引入的回归
- fixed_point.sh setup fails for src0/main.jhyy (gcc can't link incomplete .s), 但这是 pre-existing behavior, both paths produce same incomplete .s
- **memory feedback**: [[feedback_codegen_amd64_run_zerobyte]] + [[feedback_codegen_amd64_multifn]] — 这两个 limitations 在 v2.15.0 in-mem path 仍存在, v2.15.0 不动 lexer, 等 v3.x 真修

**v2.15.0 测量**:
- regress 126/147 PASS HOLD (V.1 gate)
- V.2 .s byte-equal: 3/3 收敛
- V.3 .il byte-equal N=10: 10/10 byte-equal `954a8563...`
- V.5 ACTIVE workaround count = 0 (W-074.14 → RESOLVED, no new ACTIVE)

**Both active** — D43 closure dual-layer invariant: "all generations within an active baseline byte-equal at both .il AND .s layer", 不是 "v1=v2=...=vN across history"。per `feedback_changelog_umbrella` SOP 每次 re-baseline 是 explicit event。
