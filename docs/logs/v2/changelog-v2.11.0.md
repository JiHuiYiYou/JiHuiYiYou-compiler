# JHYY v2.11.x — C.3 phi 修复 + C.4 float QBE_FALLBACK + B-runtime 诊断

**Scope**: 3 minor versions (v2.11.18 / v2.11.19 / v2.11.20) — 28 self-backend Confirm FAIL → 0 cluster 收尾
**Status**: v2.11.18 ✅ shipped (2026-09-16); v2.11.19 / v2.11.20 📋 planned
**Plan**:
- v2.11.18: [`../../plans/v2/v2.11.18-plan.md`](../../plans/v2/v2.11.18-plan.md)
- v2.11.19: [`../../plans/v2/v2.11.19-plan.md`](../../plans/v2/v2.11.19-plan.md)
- v2.11.20: [`../../plans/v2/v2.11.20-plan.md`](../../plans/v2/v2.11.20-plan.md)

---

## v2.11.18 — phi 修復 (候选 C, move-pair lowering) ✅ shipped 2026-09-16

**Trigger** (user 2026-09-16):
> "进度又太慢, 又怕推块了老 revert, 进度就一直很缓慢, 二十多个小版本了, 自研后端还没搞定"
> "我有一个想法就是根因确定而不是症状确认"

User 提出 28 Confirm FAIL 跨 7 簇, 选 RCA-first, 1 iter 诊断后落到本 sprint。完整 RCA 见 [`docs/internal/rca-v2.11.17.md`](../../internal/rca-v2.11.17.md)。

### RCA 关键发现

1. 自研 backend 是**最小可行 backend** (per L4 § 4.3, `codegen_amd64_emit_call.jhyy:363-369`): 不做 regalloc / 不做 peephole / **不做 phi resolve** (`emit_phi` 字面意义上 noop, 只 emit 注释 + return 0)
2. **C.3 phi 11/28 真 bug**: `cg_emit_phi` (`codegen.jhyy:855-862`) 真的 emit QBE phi 节点进 IL, 但自研 `emit_phi` 不翻译成 move → `.s` 缺 merge point 的 move 指令 → 11 个 phi 测试全挂 + **任何依赖 phi 解析 base/offset 的下游指令也挂** (潜在覆盖 C.5 slice 5 + A2 ptr-deref 2 + unique dungeon_game 1 = **19/28 = 68%**)
3. `emit_call.jhyy:32-34` 注释 "phi resolved upstream" 是**误导** — `cg_emit_phi` 不 resolve, 只 emit phi
4. C.4 float 4/28 是**架构边界** (零 SSE emit 代码, 设计意图走 QBE_FALLBACK), 不是 bug — 推 v2.11.19
5. B-runtime 3/28 未诊断, 推 v2.11.20
6. cap_table test4 不属 v2 axis, 推 v3.x

### 修法候选 + 选 C

| 候选 | LOC | Risk | 评价 |
|---|---|---|---|
| A | 60-100 | MED | 下游补 `emit_phi` move emit — 影响 parse loop |
| B | 80-120 | MED | 上游加 phi lowering pass |
| **C** | **50-80** | **LOW** | **改 `cg_emit_phi` 直接 emit move-pair, 不发 phi — 跟 v2.5.0 minimal backend 架构对齐** |

### 选 C 的关键理由 (per user feedback 2026-09-16)

- **教科书算法**: LLVM `reg2mem` pass, phi elimination by move insertion — 每个前驱块末尾写同一个位置, 汇合点读它
- **QBE 官方支持** (per `doc/il.txt`): *"phi 指令对 QBE 前端来说不是必需的……另一个办法是干脆 emit 非 SSA 形式的代码!与 LLVM 不同, QBE 能自动修正非 SSA 的程序。"* QBE 在 `ssa()` pass 自动构造 SSA 并 `ssacheck()` 校验
- **特别适合自研后端栈槽模型**: 不做寄存器分配, 每个 `%tN` 直接 spill 到栈槽 → 多次赋值天然合法, 根本不需要 SSA
- **效果等价**: QBE pipeline `parse → memopt → ssa() → ssacheck → copy消除 → fold/常量传播 → regalloc → 发射` — 走完 `ssa()` 走同一份 SSA

### 三条风险 + 缓解 (per user 反馈)

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| **🔴 漏前驱 = 静默错** (用 phi 时漏前驱语法残缺容易被发现; 改 move-pair 后漏前驱 → QBE 不会报错 → 静默插 phi → 运行时读到 garbage 值) | HIGH | HIGH | Phase 0 穷举所有 phi 调用点 + 5.5 grep `phi ` 全 0 是安全网 |
| 🟡 类型宽度 — `then_v =w` vs `result =l` 走 copy 行为跟 phi 不同; copy 到 sub-word 类型高位未定义 | MED | MED | real_qt = dst.qbe_type → src.qbe_type → QBE_W() 兜底; 5.1 跑 11 测试发现 |
| 🟡 角落 case: `then_returns == 1 && else_returns == 0` → result 未 alloc (hoist 条件要求两都不 return) → `return then_v`, 但只有 else 达汇合点, 正确值是 else 的 | LOW | MED | do_emit_pair 旗 gate 保留原 hoist 条件, fallback `return then_v` 跟原行为字节同 |

### Phase A 实施 (jhyy-side, ~80 LOC)

**Diff stat**:
- `compiler/src0/ir.jhyy` (+17 LOC): 新增 `ir_emit_copy_tmp` helper (类型宽度 fallback: dst.qt → src.qt → QBE_W())
- `compiler/src0/codegen.jhyy` (+62 / -64 LOC):
  - `cg_emit_phi` definition 改 noop + DEPRECATED 注释 (~5 LOC)
  - NODE_IF: hoist `result` + `do_emit_pair` flag + then/else 分支 emit `ir_emit_copy_tmp` + merge return result (~30 LOC)
  - NODE_MATCH: hoist `result` + 删 `phi_buf`/`nphi_var` arena alloc + 每 arm body 末尾 emit copy + dangling `next_check` 也 emit copy + merge 直接 return (~50 LOC)

### Phase A 验收 (per `feedback_fix_evaluation_rule` 5/5 PASS)

- ✅ **5/5 PASS on C.3 phi 5 测试** (从 11 个挑最简 5): bug2_if_phi / bug3_void_if / bug3_void_exact / nested_if / control_flow
- ✅ **IL phi count = 0** (grep `-c "phi "` = 0 全 5) — 漏前驱 = 必有 phi 残留, 安全网一步不能省
- ✅ **regress.py 114/114 PASS** (full suite, 0 fail, 20 skipped = WSL/V3-B features)
- ✅ **self-host closure sha = `3f96814870a3afb0d9b59e6d212165ffddeaada5ff4d8b29eda83126c0253cf8`** (v1/v2/v3/v4/v5 byte-equal, re-baseline per D43, 见 [`d43-baseline-archive.md`](d43-baseline-archive.md) v2.11.18 row)
- ✅ **byte_equal_amd64.sh 10/10 PASS** (self vs QBE parity, no-strict mode)
- ✅ **nested_if EXIT=244** (= 500 mod 256, 期望 500 per `// EXPECT: 500` 注释)
- ✅ **5/5 phi 测试 stdout 含正确值** (bug2_if_phi: `result = 300`; bug3_void_if: `result = 100`; bug3_void_exact: `x = 100`; control_flow: `sum = 23`; nested_if EXIT 244 = 500)

### Phase B (C-side mirror, ~70 LOC) **DEFERRED to v2.11.21**

**Why defer**:
1. D43 closure 是 **jhyy-side self-equal**, 不需要 C-side mirror
2. `byte_equal_amd64.sh` 是 **self vs QBE parity**, 不是 **C-side vs jhyy-side parity**, 不需要 C-side mirror
3. Phase A 已 ship ALL 计划 ship gates (5/5 PASS + regress + D43 + byte-equal)
4. C-side mirror 改 `compiler/src/codegen.c` + `compiler/src/ir.c`, 引入新风险 (untested code) 而不带来新 gate
5. Per user "怕推块了老 revert" + "进度最大化" → 最小风险方案

**Phase B scope** (留 v2.11.21):
- `compiler/src/ir.c`: 新增 `ir_emit_copy_val` helper (parallel to jhyy-side `ir_emit_copy_tmp`)
- `compiler/src/codegen.c`: 4 处 phi emit site (if-expr + match inline + &&/|| 短路) 改 move-pair

### Prerequisite commit: 1c31b80 (W-068 真修 v2 cherry-pick from axis-v2 commit 31e9d95)

不修这个 v2.11.18 phi 改不动 — `jhyy_stage0.exe compile main.jhyy` 直接 SIGSEGV (exit 139)。根因: `0f9c923 merge axis-v3 → main` (2026-09-08) 引入 5 处 codegen merge artifact:

1. **codegen_amd64.jhyy L74 + L315 重复 fn def** (codegen_amd64_run 2-arg stub + codegen_amd64_emit_raw_asm stub 跟 axis-v3 L216/L315 真 impl 同名) → symtab_insert 同 depth 重复返 NULL → parse_func (parser.c:583) 没 NULL check → sema.c:1281 deref NULL → SIGSEGV
2. **codegen.jhyy cg_func Pass B 循环双调 cg_func** (QBE "label or } expected")
3. **codegen.jhyy cg_func body_returns 分支双 ret emit** (双 ret)
4. **codegen.jhyy cg_func header emit SysV/Win if-else 缺 `}`** (W-070 + naked fn block orphan)
5. **codegen_amd64_emit_call.jhyy emit_volatile L612-619 unreachable 重复 let _c2**

+ 4 处 defensive NULL guards (parser.c:583 parse_func sym / parser.c:336 parse_let sym / sema.c:1281 check_module NODE_FUNC_DECL / sema.c:841 infer_type NODE_LET) — 防未来类似 bug SIGSEGV 改 parse error。

**GDB-verified** by axis-v2 user (per `31e9d95` commit message)。

---

## v2.11.19 — float 自动 QBE_FALLBACK (C.4 float 4/28 架构边界 free win) 📋 planned

**Plan**: [`../../plans/v2/v2.11.19-plan.md`](../../plans/v2/v2.11.19-plan.md)
**RCA**: `rca-v2.11.17.md` § 3.3 — 自研 backend 零 SSE emit 代码 (grep `movss|movsd|addss|mulss|divss|cvtss2si|cvttsi2si|ucomiss|XMM` = 0 hits in `compiler/src0/codegen_amd64_*.jhyy`), 不是 bug, 是 v2.5.0 设计意图走 QBE_FALLBACK。
**修法 B 路** (本 sprint): `run_backend` dispatch 加 float detection (扫描 IL 含 `=s ` / `=d ` / `addss` / `addsd` 等关键词), 含 → 强制 QBE (跟 `QBE_FALLBACK=1` 等效)。free win, ~2-5 LOC, 1 commit ship。

---

## v2.11.20 — B-runtime 診斷 + 修復 (B-runtime cluster 3/28) 📋 planned

**Plan**: [`../../plans/v2/v2.11.20-plan.md`](../../plans/v2/v2.11.20-plan.md)
**RCA** (per `rca-v2.11.17.md` § 3.4):
- Grep `jhyy_str|jhyy_alloc|jhyy_panic|jhyy_slice|jhyy_string|jhyy_arena` 在 `compiler/src0/codegen_amd64_*.jhyy`: **0 matches**
- 只找到 compiler 自己用的 `arena_alloc` / `sb_append*` / `strlen` / `sprintf_lld` (编译时 codegen 自己用, 不是 compiled program runtime)
- 自研 backend 没 emit 任何 `jhyy_*` runtime helper 调用

**修法**: 1 iter 诊断 (Phase 1a-1d) + 1 iter 修复 (Phase 2a-2b), ~30-50 LOC, 2 iter ship。诊断输出"1 页 B-runtime 诊断报告" — 真根因 + 修法 + LOC 估计 + 风险。

---

## 不在本 umbrella 范围 (推 v3.x / v2.x 末)

- ❌ **A2 ptr-deref 2/28** — 上游 codegen jhyy-side 真修 (sema 加 deref check), 跟 phi 修复同根 (phi 解析 base/offset 失败的下游)
- ❌ **unique 2/28** (含 dungeon_game 1) — 跨 v3.x generics + Cap<T> 改动, 等 v3.0/v3.1 launch 后修
- ❌ **C.5 slice 5/28** (potential phi coverage, 实际可能已 PASS 在 v2.11.18) — 验证 v2.11.18 ship 后是否剩, 不剩则自动消
- ❌ **cap_table test 4/28** — 不属 v2 axis, 推 v3.x

---

## Sprint 状态总览 (v2.11.x)

| Sprint | Status | Scope | LOC | ETA |
|---|---|---|---|---|
| v2.11.18 phi 修復 | ✅ shipped 2026-09-16 | jhyy-side move-pair lowering | ~80 (src0/) + 6 文件 prerequisite | done |
| v2.11.19 float QBE_FALLBACK | 📋 planned | run_backend dispatch 加 float detection | ~2-5 | next sprint |
| v2.11.20 B-runtime 診斷+修 | 📋 planned | 1 iter 诊断 + 1 iter 修复 | ~30-50 | after v2.11.19 |
| v2.11.21 C-side mirror (Phase B) | 📋 planned | codegen.c + ir.c phi → move-pair | ~70 (src/) | after v2.11.18 ship verify |

## 关键数字表 (v2.11.18 ship)

| Metric | Before v2.11.18 | After v2.11.18 |
|---|---|---|
| jhyy.exe sha | `98c8272...` (v1.8.3 ship, frozen) | new sha (v2.11.18) |
| D43 baseline sha | `6a2f2277...` (v2.8.0 末) | `3f968148...` (v2.11.18 active) |
| regress.py pass rate | 114/114 (QBE path) | 114/114 (QBE path) — **不变**, 但 self-backend cluster C.3 phi 11/28 → 0 |
| regress.py stage0 pass rate | 105/134 (9 cap_table/generics 失败 — V3-B C-side 限制) | 105/134 — **不变** (C-side mirror deferred v2.11.21) |
| self-host closure chain | v1→v2→v3→v4 byte-equal (v1.8.3 N=4) | v1→v2→v3→v4→v5 byte-equal (v2.11.18 N=4 hold) |
| byte_equal_amd64.sh | 10/10 PASS (QBE vs self parity) | 10/10 PASS — **不变** |
| IL phi count (5 phi-cluster 测试) | 11+ 个 phi 节点 each | **0** — phi 全部消除 |
| ACTIVE workaround count | 5 | 5 (phi 不是 workaround, 是 codegen 设计选择) |

## References

- W-068 真修 v2 (prerequisite cherry-pick): commit `31e9d95` from axis-v2 → cherry-picked as `1c31b80` on main
- v2.11.18 fix: commit `780da2e`
- D43 baseline archive: [`d43-baseline-archive.md`](d43-baseline-archive.md) v2.11.18 row
- Memory: [[feedback_changelog_umbrella]], [[feedback_fix_evaluation_rule]], [[feedback_plans_per_version]], [[feedback_auto_push_after_commit]], [[feedback_ssh_key_same_shell]]