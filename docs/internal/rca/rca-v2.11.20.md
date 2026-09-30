# RCA — v2.11.20 B-runtime cluster 15 FAIL

**Date**: 2026-09-17
**Author**: RCA session (per `feedback_rca_first_root_cause`)
**Scope**: 15 FAIL in self-backend regress 104/139, target = 全部变绿 (15/15 fix)
**Status**: ✅ RCA complete → v2.11.20 sprint 设计 ready

---

## 0. Regress baseline

`JHY_SELF_BACKEND=1 python compiler/build/bin/regress.py --self-backend` (clean `_regress_*.exe` first):

```
===== 104/119 passed, 15 failed, 20 skipped (of 139 total) =====
  (cleaned 297 _regress_* artifacts; failed tests preserved)
compiler/build/bin/jhyy.exe: FAIL — passed=104/139 failed=15 skipped=20
  failed: big_array, cap_table_basic, const_array, const_struct_array, defer_multi_lifo
```

完整 15 FAIL (按 cluster 分组):

| Cluster | 测试 | 期望 | 实际 | Failure mode |
|---------|------|------|------|--------------|
| **C1: 大 alloc** | big_array | 5050 | 3221226505 | STACK_BUFFER_OVERRUN |
| **C2: slice** (5) | slice_index | 80 | 44 | wrong value |
| | slice_iterate | 60 | 42 | wrong value |
| | slice_literal | 60 | 42 | wrong value |
| | slice_subrange | 60 | 36 | wrong value |
| | for_in_slice_nested | (None) | 3221225477 | ACCESS_VIOLATION |
| **C3: const data** (2) | const_array | 122 | 25 | wrong value |
| | const_struct_array | 9 | 2902347808 | wrong value |
| **C4: 其余 6** | cap_table_basic | 42 | 30 | wrong value |
| | defer_multi_lifo | 0 | 1 | wrong value |
| | dungeon_game | (None) | -1 | compile fail: imports start |
| | match_range | 0 | 3 | wrong value |
| | mixed_struct_slice_match | 131 | 5 | wrong value |
| | top_level_let_mut_test | 42 | 106 | wrong value |
| | top_level_let_mut_types | 17 | 2881485552 | wrong value |

> 注: STACK_BUFFER_OVERRUN (0xC0000409) + ACCESS_VIOLATION (0xC0000005) 都是 NTSTATUS,Windows 进程 exit code 截断 mod 256 → 看起来是垃圾数 (3221226505 = 0xC0000409,3221225477 = 0xC0000005)。

---

## 1. Cluster 分析

### 1.1 Cluster C2: slice (5/5 FAIL — 同一根因)

**Root cause**: `W-074.7.8` derived-address tracking **incomplete** — 只 flag 直接 `alloc` 的 result 为 address-holder,**不 propagate** 给 (a) `loadl <address-holder-temp>` 的 result 或 (b) `add/sub` 在 non-pointer 上的 result。

**证据 — slice_index** (`compiler/tests/examples/slice_index.jhyy`):

IL (正确):
```
%t1 =l alloc16 32      ; array storage [10,20,30,40,50]
...
%t12 =l alloc16 16     ; slice struct {ptr, len}
storel %t1, %t13       ; slice.ptr = &array
storel %t15, %t14      ; slice.len = 5
%t16 =l loadl %t12     ; t16 = slice.ptr (slot read, but slot holds ptr)
%t18 =l copy 8         ; offset for s[2]
%t19 =l add %t16, %t18 ; t19 = ptr + 8 = &s[2]
%t20 =w loadw %t19     ; load int from &s[2]
```

self-backend .s 实际 emit (BUG):
```
movq -160(%rbp), %rax       # rax = %t16 (slot value = ptr)
addq -176(%rbp), %rax       # rax = ptr + 8 = %t19 (computed addr)
movq %rax, -184(%rbp)       # store %t19 (a pointer) at -184 slot
movl -184(%rbp), %eax       ; ★★★ loadw slot read, NOT [rax] deref!
movl %eax, -192(%rbp)       ; -> %t20 = slot value (= address-as-int, not int)
```

应该 emit:
```
movq -160(%rbp), %r8        ; r8 = slot value (= ptr)
leaq 8(%r8), %r8            ; r8 = ptr + 8
movl (%r8), %eax            ; deref: read int from ptr+8
movl %eax, -192(%rbp)       ; -> %t20
```

**诊断**: `emit_load` line 608 (codegen_amd64_emit_mem.jhyy) 有 `if cg_is_address_holder(state, src) != 0` 分支 emit indirect。但 `%t19` (loadw target) **没被 flag 为 address-holder**,因为:
1. `emit_binop` 1602 行 flag propagate **只在 src1 是 address-holder 时**才 set dst
2. `%t19 = add %t16, %t18` 的 src1 = `%t16` = `loadl %t12`
3. `%t16` 是 `loadl <temp>` 的 result — **没被 flag** (emit_load 不 propagate)
4. 所以 chain 断了:%t19 不被 flag → loadw emit 直接 slot read → wrong value

**QBE reference (pass)**: 同样 IL,QBE 出 `subq $40, %rsp` + `movl 8(%rsp), %eax; movl 16(%rsp), %ecx; addl %ecx, %eax` 正确得到 80。

---

### 1.2 Cluster C3: const data (2/2 FAIL — 同一根因)

**Root cause**: `emit_copy` LABEL 分支 (`compiler/src0/codegen_amd64_emit_call.jhyy:1134-1168`) 不 flag dst 为 address-holder。`copy $PALETTE` / `copy $ASCII_LOWER` 的 result temp **从未被 flag**,后续 `add %t1, imm` + `loadw %t4` 走 slot read 路径 → wrong value。

**证据 — const_array**:

IL:
```
data $ASCII_LOWER = { b 97, ..., b 122 }
%t1 =l copy $ASCII_LOWER    ; t1 = &data[0]
%t2 =w copy 25
%t3 =l copy 25
%t4 =l add %t1, %t3         ; t4 = &data[25]
%t5 =w loadub %t4           ; load byte
```

.s emit (BUG):
```
leaq ASCII_LOWER(%rip), %rax
movq %rax, -40(%rbp)          ; t1 = &data[0] (CORRECT in instruction)
movq -40(%rbp), %rax
addq -56(%rbp), %rax
movq %rax, -64(%rbp)          ; t4 = addr stored at slot
movl -64(%rbp), %eax          ; ★★★ loadw slot read (low-32-bit of address)
movl %eax, ...                ; %t5 = 25 (low 32-bit of "ASCII_LOWER + 25" addr)
```

期望: ASCII_LOWER = 0x00401000 + 25 → 0x00401019, 低 32 位 = 0x00401019 = `4194329` ≠ 25。
实际 25 = 纯粹 imm slot 读出来。Slot 没初始化为 0 之前可能残留旧值,regress 看到 25 显然是 `cg_parse_int` 拿到 imm 直接 emit,没走 leaq 路径。

**fix 位置**: `emit_copy` LABEL 分支末尾 (line 1168 `return 0;` 之前) 加:
```jhyy
if dst_qt == QBE_L_LOCAL() {
    let _fna = cg_record_temp_holds_address(state, dst_id);
}
```
跟 FNARG path (line 1224-1226) + TEMP path (line 1259-1261) **完全同 pattern**,只缺 LABEL 这一处。

---

### 1.3 Cluster C1: big_array STACK_BUFFER_OVERRUN

**Root cause (推断)**: `emit_alloc` 单 function per-temp alloc-tracking 在某些大 alloc 模式下 stack frame 算错 / spill 溢出。Regress 报 0xC0000409 是 Windows STACK_BUFFER_OVERRUN。

**证据** (从 .s head):
```
subq $1816, %rsp             ; 大 frame
... addq $4..$396             ; init pattern (correct)
...访问 -1792(%rbp)            ; deepest access, 24B margin (OK)
```

Frame 1816B, deepest -1792,24B margin → frame size 算对。但 regress 报 STACK_BUFFER_OVERRUN。

**怀疑**: self-backend **silent fail** (per `feedback_codegen_amd64_multifn`) — `big_array_run.exe` 是 stale 残留 (Sep 17 13:27, prior session 编译产物,不是当前 src0 编译的)。fresh self-backend 编译可能没产出 .exe,regress 拿不到 .exe 退出 0 → 后续 cleanup 跑 stale binary crash。

**验证方法**: 在 fresh 状态下看 big_array 编译产出,若无 .exe → silent fail confirmed;若有 .exe 但 crash → 真正 frame issue。

**归属**: W-074.6 PARTIAL 主项 (silent fail family)。

---

### 1.4 Cluster C4: 剩余 6

| Test | Root cause (推断) |
|------|-------------------|
| cap_table_basic | Cap<T> + CapTable<T> generics codegen path 不全 (v3.2.0b 待 ship) |
| defer_multi_lifo | `let mut g_counter` global write-back emit 缺失 — 见 top_level_let_mut_*, 同根因 |
| dungeon_game | `compile failed: imports start` — 编译期 import resolution fail (per W-074.6 PARTIAL 已有,新暴露) |
| match_range | `0..10` 范围 match arm 翻译 cmp + jmp 多 case dispatch 不全 (可能 phi 在 jump table path) |
| mixed_struct_slice_match | 综合 = slice + struct + match range + for-in 4 feature 复合,多个 cluster bug 叠加 |
| top_level_let_mut_test/types | **W-017 ACTIVE** (workarounds.md 注册): module-level `let mut` global let mut 已被 文档化 ACTIVE,jhyy-side 不 implement,delegate 给 C-side jhyy_helpers.c runtime;self-backend 走 jhyy-side path 完全不写回 `$g_x` → 读永远 = init value (41) + 0/1 garbage = 106 等 |

---

## 2. 根因归纳 (去重)

| Root cause ID | 描述 | 影响 tests | 难度 | 优先级 |
|---|---|---|---|---|
| **RC-1: address-holder flag propagate incomplete** | (a) emit_load loadl <temp> 不 propagate flag to dst; (b) emit_binop add/sub 只 propagate 如果 src1 是 address-holder (chain break) | **slice 5 + const 2 + mixed_struct_slice_match 部分 = 7+** | LOW (改 emit_load + emit_binop + emit_copy LABEL 3 处 ~30 LOC) | **P0** |
| **RC-2: silent fail (W-074.6 PARTIAL 主项)** | self-backend 在某些 codegen path 静默 exit=0 但无 .exe 输出 (per `feedback_codegen_amd64_multifn`) | big_array + 5/5 regress silent fail 残余 | HIGH (debug codegen_amd64_run) | **P1** |
| **RC-3: W-017 module-level let mut ACTIVE** | jhyy-side 不 implement,delegate 给 C-side;self-backend 走 jhyy-side 不写回 global | top_level_let_mut_test + types + defer_multi_lifo = 3 | MEDIUM (实 impl) | **P2** |
| **RC-4: match range codegen** | range pattern codegen (1..10 / -3..-1) cmp + branch dispatch 不全 | match_range + mixed_struct_slice_match 部分 | MEDIUM | **P3** |
| **RC-5: Cap<T> / CapTable<T> generics codegen** | v3.2.0b 残,generics struct 字段 codegen 不全 | cap_table_basic | MEDIUM (per V3-C 3i) | **P3** |
| **RC-6: dungeon_game imports resolution** | compile fail,imports resolution path 缺 | dungeon_game | LOW (path 解) | **P3** |

**RC-1 + RC-2 fix 期望**: slice 5 + const 2 + mixed_struct_slice_match 大部分 + big_array = **8-9 fix** (per `feedback_fix_evaluation_rule` 5/5 PASS gate)
**RC-3 fix 期望**: 2-3 fix
**RC-4/5/6 fix 期望**: 2-4 fix (取决于 RC-1 是否连带修)
**累计**: 12-16 / 15 fix (= 全部或近全部)

---

## 3. v2.11.20 计划输入 (per RCA-first, RC-1 = P0)

### 3.1 Phase 1 — Address-holder flag propagate completeness (P0, RC-1)

**修改 1**: `compiler/src0/codegen_amd64_emit_mem.jhyy:580` emit_load line 651 末尾加:
```jhyy
// v2.11.20 RC-1: loadl/loadw/loadsw <address-holder-temp> → dst also flag
// (covers e.g. loadl %t12 where %t12 alloc'd: t16 = struct ptr read from
//  slot; subsequent add/sub/load on t16 need indirect dispatch)
if cg_is_address_holder(state, src) != (0 as i32) && (*t).qbe_type == QBE_L_LOCAL() {
    let _lp = cg_record_temp_holds_address(state, dst);
}
```

**修改 2**: `compiler/src0/codegen_amd64_emit_mem.jhyy` emit_store (line 392) + emit_loadsub (line 523) + emit_store (mirror) 同样 propagate flag if src/dst 是 address-holder 且 qbe_type=l。

**修改 3**: `compiler/src0/codegen_amd64_emit_call.jhyy:1134` LABEL 分支 `return 0;` 之前加:
```jhyy
if dst_qt == QBE_L_LOCAL() {
    let _la = cg_record_temp_holds_address(state, dst_id);
}
```

**修改 4**: `compiler/src0/codegen_amd64_emit_call.jhyy:1602` emit_binop add path (目前只 propagate sub via is_sub 路径) 同步 propagate:
- 如果 op = add 且 src1 是 address-holder → dst flag (sub 已经有同 pattern)
- 如果 src2 是 address-holder (immediate 不可能,但 src2 = TEMP 时) → 也 propagate

**预期 fix**: slice_index=80, slice_iterate=60, slice_literal=60, slice_subrange=60, const_array=122, const_struct_array=9, mixed_struct_slice_match 大部分

### 3.2 Phase 2 — 验证 big_array silent fail (P1, RC-2)

按 `feedback_codegen_amd64_multifn` debug 路径:
1. fresh clean `big_array.jhyy` → 找 `.exe` 是否产出
2. 若无 .exe → 真是 silent fail,需要 codegen_amd64_run main loop debug
3. 若有 .exe → 真 frame issue,Phase 4 路径

### 3.3 Phase 3 — W-017 module-level let mut 真修 (P2, RC-3)

实 impl jhyy-side `let mut <ident> = <expr>;` (top-level):
- emit data 段 (跟 const 同 pattern)
- emit codegen path: `loadw $g_x` → leaq + load,`storew $g_x` → leaq + store

### 3.4 Phase 4 — match range / generics / imports (P3, RC-4/5/6)

按 RC-4/5/6 单 Phase 一 fix per `feedback_rca_first_root_cause`:
- match_range: match cmp + jmp table for range patterns
- cap_table_basic: V3-C 3i 真 impl 残
- dungeon_game: imports resolution path debug

---

## 4. 风险 & Out of scope

| Risk | Mitigation |
|------|-----------|
| RC-1 fix cross-cluster 影响 (现有 28 PASS 用例可能是 bug 兼容) | regress delta 必须 ≥3 PASS 才 ship (per `feedback_fix_evaluation_rule`) |
| RC-2 silent fail 调试 难以复现 (per `feedback_codegen_amd64_multifn`) | fresh state 下 binary 验证;若不产 .exe 走 codegen_amd64_run debug (5/5 gate 不强制) |
| W-017 真修可能改 v1.4.6 已经过的 test | 严格 regress gate;若 regression → revert |
| dungeon_game 是 OS-related fixture | 推 v2.x 末 / v3.x |

---

## 5. References

- `docs/logs/v2/changelog-v2.11.0.md` v2.11.19 section + v2.11.20 ship section (per `feedback_changelog_umbrella` umbrella convention)
- `docs/internal/workarounds.md` W-074.6 PARTIAL + W-074.10 CLOSED + W-074.11 CLOSED + W-074.12 CLOSED + W-074.13 DEFERRED + W-017 ACTIVE (v1.4.6)
- `docs/internal/architecture.md` last updated v2.11.20
- `docs/plans/v2/v2.11.20-plan.md` (per `feedback_plans_per_version`)
- Memory: [[feedback_rca_first_root_cause]], [[feedback_codegen_amd64_multifn]], [[feedback_fix_evaluation_rule]], [[feedback_codegen_amd64_run_zerobyte]]
- Source: `compiler/src0/codegen_amd64_emit_mem.jhyy:580-720` (emit_load indirect + flag propagate + $label path)
- Source: `compiler/src0/codegen_amd64_emit_call.jhyy:1168` (emit_copy LABEL flag propagate)
- Source: `compiler/src0/codegen_amd64_emit_call.jhyy:1587-1620` (emit_binop flag propagate reference)
- Source: `compiler/src0/codegen_amd64_emit_ctrl.jhyy` (match range cmp+clamp fix)
- Source: `compiler/src0/codegen_amd64_state.jhyy:280-305` (cg_record_temp_holds_address / cg_is_address_holder APIs)

## 6. v2.11.20 closure (post-ship 2026-09-17)

**Sub-commits shipped** (axis-v2):
1. `56be6cf` Phase 1+2 RC-1 + RC-7 — emit_load + emit_copy LABEL flag propagate (W-074.10 CLOSED)
2. `970f2ca` Phase 3 RC-3 W-017 — module-level let mut emit path (W-074.11 CLOSED)
3. `0831459` Phase 4 RC-4 — negative IMM parse + clamp fix (W-074.12 CLOSED)
4. (this RCA closure) Phase 6 docs + changelog + workarounds + ship tag

**Regress delta**: 104/139 → 115/139 PASS (+11) under `--self-backend` mode (default QBE mode held 119/139 PASS, 不变)。**⚠️ docs 措辞滞后修正 (2026-09-17 v2.11.23 ship 复测 confirm)**: v2.11.20 ship record 当时写 "both default QBE + --self-backend modes 115/139 PASS" 是错的 — QBE path 实际是 119/139 PASS (跟 v2.11.23 today QBE 一致, 是 baseline), self-backend 是 115/139 PASS + 4 FAIL deferred (跟 v2.11.20 ship evidence 列的 4 deferred sub-bug match)。measurement 才是 ground truth per `feedback_audit_single_commit_diff`。

**D43 closure**: HOLD `a8a28cb6...` (per V.7 byte-equal gate,Phase 1+2+3+4 改 codegen_amd64_*.jhyy 但 D43 未动 — Phase 1+2/3/4 改 emit_load/emit_store/emit_copy LABEL/emit_ctrl match,不影响 jhyy_vN → jhyy_vN+1 .il 输出)。

**Workarounds closed**:
- W-074.10 (RC-1 + RC-7 emit_load + emit_copy LABEL flag propagate) ✅ CLOSED
- W-074.11 (RC-3 W-017 self-backend emit_load/store $label path) ✅ CLOSED
- W-074.12 (RC-4 match range cmp+clamp) ✅ CLOSED

**Workarounds deferred** (W-074.13 NEW):
- Sub-bug 1: big_array slot allocation conflict — 2-pass slot alloc 重设计 (~80-120 LOC)
- Sub-bug 2: cap_table_basic emit_load silent fail — fnarg ID 在 cg_is_address_holder 查询 gap (~10-20 LOC)
- Sub-bug 3: dungeon_game multi-file import link — W-074.6 PARTIAL 主项子集 (~30-50 LOC)
- Sub-bug 4: for_in_slice_nested nested slice iterate SEGV — RC-1 follow-up (~20-40 LOC)

**Honest scope**: 原始 plan 估 +15 fix (7 RCA-listed + 3 W-017 + 1 RC-4 + 4 side effects);实际 ship +11 (7 slice/const/mixed_struct + 3 W-017 + 1 RC-4)。4 deep-rooted fail 推 v2.11.21+ 真修,不为 +15 数字蒙混 ship (per `feedback_codegen_amd64_multifn` scope DOWN 原则)。

**SysV cross**: V.8 sysv_float_cross.sh 6/6 PASS (per v2.11.19 baseline)。
- Source: `compiler/src0/codegen_amd64_emit_call.jhyy:1587-1606` (emit_binop flag propagate)
- Source: `compiler/src0/codegen_amd64_state.jhyy:295-305` (cg_is_address_holder)
- Source: `compiler/src0/codegen_amd64_state.jhyy:280-291` (cg_record_temp_holds_address)