# V2-A batch plan — v2.5.0 (M1-A windows 后端起步)

## Context

**Batch 范围**:V2-A 是 v2 axis 第一 batch,只含 1 个 sub-sprint(v2.5.0)。把 v2.4.0 多目标 dispatcher 走的 QBE 后端(QBE IL → .s)换成自写 jhyy-side 后端,**windows 后端起步**(amd64_win + amd64_win_freestanding 走同一自写路径;sysv 留 V2-B v2.7.0)。

**在 v2 axis 内位置**:
- v2.0 阶段 5 版本已 ship(v2.0.0 → v2.4.0,2026-09-02 ~ 09-04,tags v2.3.0 / v2.4.0)
- V2-A = v2.x 中期 M1-A(v2.0.0-os-prep.md § 1 OS 启动里程碑表的 v2.5.0 节点)
- 后接 V2-B(v2.6.0 regalloc + v2.7.0 sysv)和 V2-C(v2.8.0 N 代 fixed point + QBE 移除)

**上游依赖(全已 ship)**:
- v2.4.0 多目标 dispatcher(`target_dispatch.jhyy` + `main.jhyy:671` `run_qbe` hook)
- v2.1.0 ABI 抽离(`abi_amd64_win.jhyy` + `abi_amd64_win_freestanding.jhyy`,windows + freestanding 两者 byte-identical 签名)
- v1.0 自举闭环(self-equal baseline `51376ce5...` v2.4.0 re-baselined per D43)

**跨 axis**:本 batch 启动时 v3 axis 任何 sub-sprint 尚未启动;无前置依赖。

## Sub-sprint 分解

### v2.5.0 (M1-A windows 自写 amd64 后端起步)

**Scope**:
1. 新建 `compiler/src0/codegen_amd64.jhyy`(~1500-2000 行):QBE IL → amd64 GAS `.s` 自写 emitter
   - QBE IL 子集(~15 instruction shapes):`alloc` / `store` / `load` / `call` / `phi` / `copy` / `binary` / `ret` / `jmp` / `jnz` / `label` / `func_header` / `data_string`(对齐 src0 实际 emit 的 IL 类型)
   - 跟 src0/codegen.jhyy 当前 emit 出的 IL 完全一致(同一份 .il 输入,自写后端产出 byte-equal .s ↔ QBE 产出)
2. `compiler/src0/target_dispatch.jhyy` 加 `target_backend_mode(t) -> i32`("qbe"=0 / "self"=1)
   - amd64_win + amd64_win_freestanding → mode=self(V2-A 默认)
   - amd64_sysv + amd64_sysv_freestanding → 暂 mode=qbe(V2-B v2.7.0 再迁)
3. `compiler/src0/main.jhyy:671` `run_qbe` 改名 `run_backend(il_path, asm_path, t)`
   - mode=self → 调 `codegen_amd64_emit(il_path, asm_path, t)` → `jh_run(as_cmd)`(`as` = MinGW assembler)
   - mode=qbe → 维持原 `run_qbe` body(V2-A 仅 debug fallback,不进 default path)
   - 新增 env var `QBE_FALLBACK=1` 强制走 QBE 路径(debug only;默认不挂)
4. regress.py 集成自写后端路径(`--backend=self|qbe|auto`,默认 auto = self for amd64_win*)
5. `tests/byte_equal_amd64.jhyy`(新):跑 `QBE_FALLBACK=0` 和 `QBE_FALLBACK=1` 两路径都 byte-equal .s ↔ baseline(自写后端正确性 sanity check)

**Key files**:
- 新建 `compiler/src0/codegen_amd64.jhyy`(主体,~1500-2000 行)
- 改 `compiler/src0/main.jhyy:671`(dispatch hook → `run_backend`)
- 改 `compiler/src0/target_dispatch.jhyy`(加 `target_backend_mode`)
- 改 `compiler/runtime/runtime.c`(无需大改;仅 link line 注释更新 — 自写后端同样调 `as` + `gcc`)
- 改 `compiler/build/bin/regress.py`(加 `--backend` flag + 默认 auto)
- 改 `compiler/src/target/target_dispatch.{c,h}`(C-side mirror 加 `target_backend_mode` 1:1 同步)

**关键决策**:
- **QBE IL 解析用 lexer + recursive descent**(参考 `parser.jhyy` 风格,跟 src0 既有 code style 一致)
- **amd64 emit 走 GAS 语法**(MinGW `as` 支持;不用 Intel 语法;每行 emit 加 `.att_syntax prefix` 明确)
- **保持 ABI 抽离(v2.1.0 已 ship)**:`abi_amd64_win.jhyy` 提供 arg 顺序 / shadow 规则 / struct pass;`codegen_amd64.jhyy` 只负责 IL → .s,**不**碰 ABI 调用约定细节
- **Self-equal 验证(N=1 minimum)**:v1.0 baseline(`51376ce5...`)→ jhyy_v2.5.0 跑 src0 → .il byte-equal(per D43);.s byte-equal ↔ QBE _FALLBACK 路径
- **不**做 regalloc / peephole / 性能优化(留 V2-B)

## 跨 axis 硬约束

- **D43**(阶段性 self-equal hold):v2.5.0 ship 必须 N≥1 代 self-equal baseline 不变;baseline 锁定 `51376ce5...`(v2.4.0 re-baselined)
- **D42**(inline asm QBE→自写后端路径):**预留** `codegen_amd64.jhyy` 的 ASM escape hatch(`codegen_amd64_emit_raw_asm(text: *u8)` 空函数,V3-B v3.0.1 启动时填充)— 这是 3a inline asm 启动前置;V2-A ship 时该函数可为空,仅占位
- **3c volatile**(V3-B v3.0.3):尚在 v3 axis,V2-A 不依赖;但 codegen_amd64.jhyy 设计需**预留** volatile load/store 标记位(IR 解析时识别 `volatile` token,无 → 0,V3-B 启动时填 1)
- **D10** `#[no_std]` 软 ship:V2-A 不依赖

## Batch ship gate

- `jhyy_regress` 104/104 PASS(走自写 codegen_amd64.jhyy,非 QBE;默认 backend=auto)
- Self-equal baseline sha `51376ce5...` 不变(N=1+.il+.s 跨代 byte-equal)
- `QBE_FALLBACK=1` 跑同 104 tests 仍 PASS(QBE baseline 不变,fallback 可逆)
- `hello.jhyy` EXIT:42 跨 100 次 byte-equal .s(reproducibility sanity)
- `tests/byte_equal_amd64.jhyy` 5/5 PASS(self vs QBE .s 一致)
- `mcp__jhyy__jhyy_selfhost_check` 报 N=1 byte-equal
- `mcp__jhyy__jhyy_workarounds` 不引入新 W-XXX(V2-A 不留 workaround)
- umbrella `docs/logs/v2/changelog-v2.5.0.md` 写 baseline sha + 自写后端切换步骤

## 风险 + 缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| QBE IL 子集覆盖不全 | 部分 regress fail | QBE_FALLBACK=1 兜底;fail 的 test 拆 IL diff,补 codegen_amd64.jhyy emit path;**不**改 codegen.jhyy emit(保持 src0 IL 稳定) |
| IL 解析 bug 难定位 | v2.5.0 ship 阻塞 | per `feedback_il_s_debugging_pattern`:JHYY runtime 取证 fallback 直接读 `.il` + 自写后端产 `.s` 比对 QBE 产 `.s`,gdb 不行就走 file diff |
| Peephole 没做 | 性能退步 | 不阻塞 ship;V2-B v2.6.0 sub-sprint 做 |
| ASM escape hatch 预留不到位 | V3-B v3.0.1 启动卡住 | V2-A ship 前 review `codegen_amd64_emit_raw_asm` 签名;跟 V3-B 设计对齐(占位 = 空函数 + 注释 "filled by v3.0.1") |
| MinGW `as` 路径 / 版本差异 | ship 后用户机器 build fail | `scripts/dev/build/build-msys.sh` 加 `which as` 校验;README 注明 MinGW `as` 版本 ≥ 2.40 |
| `jhyy_helpers.c` C-side runtime bridge 改动 | self-equal closure fail | 走 `as` + `gcc` 链路,跟 QBE 路径一致;`runtime.c` 仅注释更新 |

## Out of scope

- amd64_sysv + amd64_sysv_freestanding 后端(留 V2-B v2.7.0)
- 确定性 regalloc / peephole(留 V2-B v2.6.0)
- N 代 fixed point 大验证(N≥3,留 V2-C v2.8.0)
- QBE 工具链完全移除(留 V2-C v2.8.0)
- `#[no_std]`(留 V3-A)
- inline asm / #[naked] / volatile / #[link_section] / memory barrier(V3-B 5 sub-sprints)
- `&mut` + lifetime + Cap<T>(留 V3-C)
- M5(删 src/*.c + runtime.c)— 留独立 sprint

## 文件变更清单

### 新建
- `compiler/src0/codegen_amd64.jhyy`(~1500-2000 行)
- `tests/byte_equal_amd64.jhyy`(sanity test,~30 行)

### 改动
- `compiler/src0/main.jhyy:671`(rename `run_qbe` → `run_backend` + branch on `target_backend_mode(t)`,~30 行)
- `compiler/src0/target_dispatch.jhyy`(加 `target_backend_mode(t)`,~10 行)
- `compiler/src/target/target_dispatch.{c,h}`(C-side mirror,~10 行)
- `compiler/runtime/runtime.c`(注释更新,不动逻辑)
- `compiler/build/bin/regress.py`(加 `--backend=self|qbe|auto`,~20 行)
- `docs/internal/build.md`(加自写后端 build 步骤 + `as` 版本要求)
- `docs/internal/architecture.md`(加 codegen_amd64.jhyy 模块边界描述)
- `docs/logs/v2/changelog-v2.5.0.md`(新 umbrella changelog)

## Commit / tag 节奏

- **Commit 1**:`feat(codegen_amd64): add self-written amd64 windows backend`(主体实现)
- **Commit 2**:`feat(dispatch): add target_backend_mode + run_backend hook`(dispatch 接入)
- **Commit 3**:`docs(plan): v2.5.0 batch V2-A ship`(umbrella + 自验证)
- **Tag**:`v2.5.0`(push 后建 tag,per `feedback_auto_push_after_commit` 但 tag 仍需 user 确认)
- **Baseline**:ship 时记 sha → 写进 `docs/logs/v2/changelog-v2.5.0.md`,作为 v2.6.0 / v2.7.0 / v2.8.0 阶段性 self-equal 起点

## Cross-ref(其他 batch / 文档)

- 后续 batch:`docs/plans/v2/batch-V2-B-plan.md`(v2.6.0 regalloc + v2.7.0 sysv 接收 V2-A 自写后端)
- 后续 batch:`docs/plans/v2/batch-V2-C-plan.md`(v2.8.0 N 代 fixed point 接 V2-A + V2-B 全 target)
- v3 axis:`docs/plans/v3/batch-V3-B-plan.md`(v3.0.1 inline asm 启动依赖 V2-A ASM escape hatch 占位)
- M1 launch gate:`docs/plans/v2/v2.0.0-os-prep.md § 1 M1 节点`
