# V3-B batch plan — v3.0.1 → v3.0.5 (M1-required 5 件套)

## Context

**Batch 范围**:5 个 sub-sprint 串行 ship(v3.0.1 → v3.0.5),覆盖 OS kernel 启动硬前置的 5 个语言特性:3a inline asm / 3b `#[naked]` / 3c volatile / 3e `#[link_section]` / 3f memory barrier。**3c volatile 必须最早 ship**(v2.x V2-B v2.7.0 sysv target 移植 volatile 语义依赖 3c spec 定义)。

**在 v3 axis 内位置**:
- V3-A(v3.0.0 no_std)✅ ship 在前
- **V3-B = 本 batch**(v3.0.1 → v3.0.5 = 5 个 sub-sprint)
- 后接 V3-C(v3.1.0 → v3.1.2 = D27 串行 3g/3g.5/3g.7)

**M1 launch 硬前置**(per `v2.0.0-os-prep.md § 1`):
- v3.0 3a-3c/3e-3f(V3-B 5 sub-sprints)
- v2.x 多 target 后端(V2-A + V2-B)
- 3d `#[no_std]` 软 ship per D10,不依赖

**上游依赖**:
- V3-A ✅ ship(v3.0.0 no_std 跑通 v3 axis dev workflow)
- V2-A ✅ ship(codegen_amd64.jhyy 自写后端起步;3a inline asm 走 QBE 路径初期不依赖 V2-A,但 codegen_amd64 后续移植 ASM escape hatch 时回归测试不变)
- v2.1.0 ✅ ship(ABI 抽离)

**跨 axis 硬约束(本 batch 内 sub-sprint 顺序锁定 + 跨 axis 触发)**:

| Sub-sprint | 跨 axis 触发 / 依赖 |
|------------|----------------------|
| v3.0.1 (3a) | D42:走 QBE `.s` 路径(初期);V2-A codegen_amd64.jhyy ASM escape hatch 移植时回归测试不变 |
| v3.0.2 (3b) | 跟 V2-A codegen_amd64.jhyy 无 file 冲突;3b 是 codegen.jhyy:cg_module 内 fn prologue/epilogue 切换 |
| **v3.0.3 (3c)** | **最早 ship;V2-B v2.7.0 sysv target 启动前置(否则 sysv backend volatile 移植没 spec)** |
| v3.0.4 (3e) | 跟 V2-B v2.7.0 sysv target ELF section 验证强相关 |
| v3.0.5 (3f) | 跟 V2-B v2.7.0 sysv target SMP 内存模型测试强相关 |

## Sub-sprint 分解

### v3.0.1 (3a inline asm)

**Scope**:
1. parser.jhyy:解析 `asm!(...)` 块语法(syntax: `asm!("cpuid" : "={eax}"(eax) : "{eax}"(1) : "ebx", "ecx", "edx" : "volatile")`)
2. codegen.jhyy:cg_module 加 asm emit 路径(走 .s 直接插入汇编)
3. sema.jhyy:asm 字符串解析 + operand 校验(in / out / clobber / options)
4. `mcp__jhyy__jhyy_lang_ref` 加 inline asm 文档条目

**Key files**:
- 改 `compiler/src0/parser.jhyy`(asm block parser,~80 行)
- 改 `compiler/src0/sema.jhyy`(asm operand validation,~50 行)
- 改 `compiler/src0/codegen.jhyy`(asm emit path,~60 行)
- 改 `compiler/src/target/asm_emit.{c,h}`(C-side mirror,~30 行)
- 新建 `tests/inline_asm_cpuid.jhyy`(验证 cpuid 返回,~30 行)
- 新建 `docs/abis/jhyy-lang-spec-inline-asm-supplement-v3.0.1.md`(~120 行 supplement)

**关键决策**:
- **D42** 锁:初期走 QBE `.s` 输出路径直接插入汇编(QBE 接 asm text 走 passthrough)
- **V2-A `codegen_amd64.jhyy` 后续移植 ASM escape hatch**(V2-A 已预留 `codegen_amd64_emit_raw_asm` 占位)— 移植时回归 test 走 `tests/inline_asm_cpuid.jhyy` byte-equal .s

### v3.0.2 (3b `#[naked]` fn)

**Scope**:
1. parser.jhyy:parse_attributes 加 `"naked"` 识别(已有 inline / no_std 旁路加 6 行)
2. AST:FunctionAttr 加 `is_naked: i32`(per src0 当前 fn attr 模式)
3. sema.jhyy:`is_naked == 1` 校验:无局部变量(全部走 arg + inline asm)— error clear message
4. codegen.jhyy:`is_naked == 1` → 跳过 fn prologue/epilogue emit;emit raw `ret`(user 自管 stack / 寄存器)
5. `tests/naked_interrupt_entry.jhyy`:模拟 interrupt entry(fn 收到 arg 直接返回,无 prologue)

**Key files**:
- 改 `compiler/src0/parser.jhyy:2170`(`parse_attributes` 加 naked 识别,~6 行)
- 改 `compiler/src0/sema.jhyy`(`is_naked` 校验,~40 行)
- 改 `compiler/src0/codegen.jhyy`(naked fn emit path,~30 行)
- 新建 `tests/naked_interrupt_entry.jhyy`(~20 行)

**关键决策**:
- **不**支持 naked fn 内的局部变量(`is_naked == 1 && has_local_var` → error)
- **不**支持 naked fn 调用非 naked fn(链接期风险;留 v3.x 中)

### v3.0.3 (3c volatile load/store) — **最早 ship,M1 硬前置**

**Scope**:
1. parser.jhyy:解析 `volatile` 关键字(类型位置;`let x: volatile i32 = ...`)
2. AST:加 `is_volatile: i32` 标记(Type / Expr level)
3. sema.jhyy:`volatile` 标记传递
4. codegen.jhyy:`volatile` load → emit `mov` 直接走内存,no regalloc;volatile store → 同上
5. V2-A `codegen_amd64.jhyy`:识别 IR 中 volatile 标记,emit 同上(V2-A 已预留识别位)
6. `tests/volatile_mmio.jhyy`:模拟 MMIO(volatile 写 + 读顺序不被 reordering)

**Key files**:
- 改 `compiler/src0/parser.jhyy`(volatile 关键字 parser,~40 行)
- 改 `compiler/src0/sema.jhyy`(volatile 标记传递,~20 行)
- 改 `compiler/src0/codegen.jhyy`(volatile load/store emit path,~30 行)
- 改 `compiler/src0/codegen_amd64.jhyy`(V2-A 已预留;填充识别 + emit,~20 行)
- 新建 `tests/volatile_mmio.jhyy`(~30 行)
- 新建 `docs/abis/jhyy-lang-spec-volatile-supplement-v3.0.3.md`(~100 行 supplement)

**关键决策**:
- **不**支持 volatile 复合类型(struct volatile)— 留 v3.x 中(volatile 字段级在 struct 内)
- **不**支持 volatile 位域(volatile bitfield)— 留 v3.x 中
- **emit 走直接 mov mem**:no regalloc(no spill / reload);简单 + 正确(per `feedback_il_s_debugging_pattern`)
- **v2.7.0 sysv target 移植**(V2-B):v3.0.3 ship 后 v2.7.0 才能写 sysv volatile backend

### v3.0.4 (3e `#[link_section]`)

**Scope**:
1. parser.jhyy:parse_attributes 加 `"link_section"` + 解析字符串参数 `("...")`
2. AST:FunctionAttr / GlobalVarAttr 加 `link_section: *u8`(per src0 当前 fn attr 模式)
3. sema.jhyy:`link_section` 字符串传递
4. codegen.jhyy:cg_module emit `.section <link_section>` 指令(在 fn / global var 前)
5. V2-A `codegen_amd64.jhyy`:识别 link_section 标记,emit 同上
6. `tests/link_section_boot.jhyy`:`#[link_section(".text.boot")] fn _start() -> i32 { return 42; }` 验证 `readelf -S` 看 `.text.boot` 段

**Key files**:
- 改 `compiler/src0/parser.jhyy:2170`(`parse_attributes` 加 link_section 解析,~15 行)
- 改 `compiler/src0/sema.jhyy`(`link_section` 字符串传递,~20 行)
- 改 `compiler/src0/codegen.jhyy`(`.section` emit,~20 行)
- 改 `compiler/src0/codegen_amd64.jhyy`(V2-A 移植,~20 行)
- 新建 `tests/link_section_boot.jhyy`(~20 行)
- 新建 `docs/abis/jhyy-lang-spec-link-section-supplement-v3.0.4.md`(~80 行 supplement)

**关键决策**:
- **字符串字面量 + 静态检查**:section name 必须是 ASCII 标识符(a-zA-Z0-9_.)+ `.text` / `.data` / `.bss` / 自定义段
- **不**支持 module 级 `link_section` for static var 数组(留 v3.x 中)— 当前只支持 fn + global var scalar
- **跟 V2-B v2.7.0 sysv ELF section 联调**:v3.0.4 ship 后 v2.7.0 sysv 跑通 `readelf -S` 验证

### v3.0.5 (3f memory barrier)

**Scope**:
1. parser.jhyy:解析 `fence_seq_cst` / `fence_acquire` / `fence_release` 内置函数调用(expr level)
2. sema.jhyy:识别 fence 内置函数(no 普通函数定义)
3. codegen.jhyy:emit `mfence` (seq_cst) / `lfence` (acquire) / `sfence` (release)
4. V2-A `codegen_amd64.jhyy`:移植 emit
5. `tests/memory_barrier_smp.jhyy`:`fence_seq_cst()` 测试(QEMU `-smp 2` 验证 SMP 场景)— 单核 x86 上等价 nop,只 sanity

**Key files**:
- 改 `compiler/src0/parser.jhyy`(fence expr parser,~30 行)
- 改 `compiler/src0/sema.jhyy`(fence 内置函数识别,~20 行)
- 改 `compiler/src0/codegen.jhyy`(fence emit,~15 行)
- 改 `compiler/src0/codegen_amd64.jhyy`(V2-A 移植,~10 行)
- 新建 `tests/memory_barrier_smp.jhyy`(~30 行)

**关键决策**:
- **x86 三种 fence 区分**:`mfence` 全序;`lfence` load 序;`sfence` store 序(per Intel SDM)
- **ARM / RISC-V fence 留 v3.x 中**(per OS M11 launch 计划):当前只 x86
- **不**实现完整 C11 / Rust memory model(cross-platform acquire/release)— 留 v3.x 中
- **SMP 测试需 QEMU `-smp 2`**:单核等价 nop → CI 仅做 emit 正确性 verify(读 .s 含 mfence / lfence / sfence);不实际跑多核(成本高)

## 跨 axis 硬约束(硬性顺序)

- **3c volatile 先 ship**(v3.0.3)→ V2-B v2.7.0 sysv volatile 移植可启动
- **D42** inline asm 路径:QBE `.s` 插入(初期)→ V2-A codegen_amd64 移植 ASM escape hatch(后续)
- **D43** 每 sub-sprint 重新 baseline(v3.0.0 → v3.0.1 → ... → v3.0.5 各 1 baseline sha)
- **本 batch 内 sub-sprint 串行不可调换**(v3.0.1 → v3.0.2 → ... → v3.0.5)— 顺序锁,任意一个失败 → batch 卡住 → 中途可暂停 + user 介入

## Batch ship gate

- 5 sub-sprints 全 ship,每 ship 1 段并入 `docs/logs/v3/changelog-v3.0.md`(umbrella,per `feedback_changelog_umbrella`)
- 每 ship `jhyy_regress` 104/104 PASS + `jhyy_selfhost_check` 4-stage byte-equal
- v3.0.3 ship 时通知 user:V2-B v2.7.0 sysv target 可启动 volatile 移植
- v3.0.4 + v3.0.5 ship 时通知 user:V2-B v2.7.0 sysv ELF section + SMP fence 测试可启动
- M1 launch 集成 gate 触发(per `v2.0.0-os-prep.md § 1`):v2 axis multi-target 全 ship + v3.0.0..v3.0.5 全 ship

## 风险 + 缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| 5 sub-sprints 串行 ship 中任何失败 → batch 卡住 | V3-B 阻塞 | 中途可暂停 + user 介入;每 sub-sprint ship 后做 sanity baseline 锁定,下次启动可恢复 |
| D42 inline asm 初期走 QBE 路径,跟 V2-A codegen_amd64.jhyy file 层**不冲突** | 安全 | 3a 改 parser + codegen 不动 codegen_amd64;V2-A ASM escape hatch 占位函数 v3.0.1 ship 后填充 |
| 3c volatile 跟 regalloc 冲突 | codegen 复杂度上升 | emit 直接 mov mem,no regalloc(no spill / reload);简单 + 正确 |
| memory barrier 在单核 x86 上等价 nop | SMP 测试难 | CI 仅做 emit 正确性 verify(读 .s 含 mfence / lfence / sfence);不实际跑多核 |
| QBE passthrough 路径(3a 初期)不被 QBE 本身支持 | inline asm 编译失败 | QBE 支持 `@asm {...}` 块 / 或 codegen.jhyy 在 QBE 调用**前**改写 .il(直接 emit .s)— 后者更可控 |
| naked fn 内调用非 naked fn 链接失败 | ship gate 阻塞 | 限制 naked fn 只能被 naked fn 调用 + assembly 入口;sema 加 warning(error?)引导 user |
| link_section 字符串静态检查不严 | 编过但 ELF 段错误 | 限制 ASCII 标识符 + 段名首字符 `.`;超过 → error |

## Out of scope

- `&mut` + lifetime(留 V3-C)
- Atomic 内置(CAS / fetch_add)— 留 v3.x 中(非 M1 必需)
- SysV volatile 后端移植(留 V2-B v2.7.0,本 batch 只 ship 3c spec)
- ARM / RISC-V fence(留 v3.x 中 / M11 launch 时)
- 完整 C11 / Rust memory model(留 v3.x 中)
- volatile struct / volatile bitfield(留 v3.x 中)
- module 级 `link_section` for static var 数组(留 v3.x 中)
- naked fn 调用非 naked fn(留 v3.x 中)
- 3d `#[no_std]`(留 V3-A)
- M5(留独立 sprint)

## 文件变更清单

### 新建(5 sub-sprints 累计)
- `tests/inline_asm_cpuid.jhyy`(~30 行)
- `tests/naked_interrupt_entry.jhyy`(~20 行)
- `tests/volatile_mmio.jhyy`(~30 行)
- `tests/link_section_boot.jhyy`(~20 行)
- `tests/memory_barrier_smp.jhyy`(~30 行)
- `docs/abis/jhyy-lang-spec-inline-asm-supplement-v3.0.1.md`(~120 行)
- `docs/abis/jhyy-lang-spec-volatile-supplement-v3.0.3.md`(~100 行)
- `docs/abis/jhyy-lang-spec-link-section-supplement-v3.0.4.md`(~80 行)
- `docs/logs/v3/changelog-v3.0.md`(umbrella,V3-A + V3-B 5 sub-sprint 合并)

### 改动(5 sub-sprints 累计)
- `compiler/src0/parser.jhyy`(`parse_attributes` 加 naked / link_section / volatile / asm,累计 ~150 行)
- `compiler/src0/sema.jhyy`(~150 行,asm operand + naked 校验 + volatile 传递 + link_section 字符串 + fence 识别)
- `compiler/src0/codegen.jhyy`(~155 行,asm emit + naked emit + volatile emit + section emit + fence emit)
- `compiler/src0/codegen_amd64.jhyy`(V2-A 移植 volatile / link_section / fence / ASM,~50 行;**不**移植 inline asm — 仍走 QBE 路径 per D42)
- `compiler/src/target/asm_emit.{c,h}`(~30 行 C-side mirror,3a 专用)
- `docs/logs/v3/changelog-v3.0.md`(5 段增量,每 sub-sprint ~10 行)

## Commit / tag 节奏

每 sub-sprint 1 个 commit + tag(5 sub-sprint × 1 commit = 5 commits):
- **Commit 1**:`feat(asm): add inline asm!() block (3a)` → tag `v3.0.1`
- **Commit 2**:`feat(naked): add #[naked] fn attribute (3b)` → tag `v3.0.2`
- **Commit 3**:`feat(volatile): add volatile load/store (3c)` → tag `v3.0.3`(**最早 ship,V2-B 前置通知**)
- **Commit 4**:`feat(link-section): add #[link_section] (3e)` → tag `v3.0.4`
- **Commit 5**:`feat(memory-barrier): add fence_* intrinsics (3f)` → tag `v3.0.5`
- 每 ship 重新 baseline sha → 写进 `changelog-v3.0.md` 对应段

## Cross-ref

- 上游:`docs/plans/v3/batch-V3-A-plan.md`(V3-A no_std 已 ship)
- 下游:`docs/plans/v3/batch-V3-C-plan.md`(3g/3g.5/3g.7 D27 串行)
- 跨 axis 触发 V2-B:`docs/plans/v2/batch-V2-B-plan.md`(v2.7.0 sysv volatile / section / fence 移植依赖 3c/3e/3f)
- 跨 axis V2-A codegen_amd64.jhyy:`docs/plans/v2/batch-V2-A-plan.md`(ASM escape hatch 占位 + volatile 标记位预留,V3-B 填充)
- D42 inline asm 路径锁:`docs/plans/roadmap/v2-v3-parallel-sprint-plan.md § 4.2`
- M1 launch gate:`docs/plans/v2/v2.0.0-os-prep.md § 1 M1`
