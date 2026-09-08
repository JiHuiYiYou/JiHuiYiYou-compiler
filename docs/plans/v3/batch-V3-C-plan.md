# V3-C batch plan — v3.1.0 → v3.1.2 (D27 串行 3g → 3g.5 → 3g.7)

## Context

**Batch 范围**:3 个 sub-sprint 串行 ship(v3.1.0 → v3.1.1 → v3.1.2),覆盖 v3.1 三大 OS 内存安全特性:`&mut` + lifetime(3g)+ phantom 0-byte codegen 路径(3g.5)+ cap table 联调(3g.7)。**D27 锁串行不可调换**:3g codegen 必须先于 3g.5 phantom 0-byte codegen 路径,3g.5 必须先于 3g.7 cap table 联调。

**在 v3 axis 内位置**:
- V3-A ✅ ship(v3.0.0 no_std)
- V3-B ✅ ship(v3.0.1 → v3.0.5 = 3a/3b/3c/3e/3f)
- **V3-C = 本 batch**(v3.1.0 → v3.1.2 = D27 串行)
- 后接:v3.x 中(M4 launch / 后续)

**M4 launch 硬前置**(per `v2.0.0-os-prep.md § 1`):
- v3.1 3g + 3g.5 + 3g.7(V3-C 整个 batch)
- v2.x 全 target 自写后端(V2-A + V2-B + V2-C)
- 借用检查 + 8 字节 Cap<T> layout + cap table 联调

**上游依赖**:
- V3-A ✅ ship(no_std 提供 kernel base)
- V3-B ✅ ship(3a inline asm 提供 raw 内存访问;3c volatile 提供 MMIO 语义)
- V2-A + V2-B ✅ ship(自写后端 + regalloc + peephole + sysv target)
- Self-equal baseline sha(V3-B v3.0.5 ship 时锁定)

**跨 axis 硬前置**:
- **V2-C v2.8.0 N 代 fixed point 验算时跑 `cap_test.jhyy` 需要 3g borrow check + 8 字节 layout**;否则 fail
- V3-C 整个 batch 必须 ship 在 V2-C 启动**前**(per `batch-V2-C-plan.md` 跨 axis 硬约束)
- **3c volatile 必须已 ship**(V3-B v3.0.3)— cap pass 跨 volatile 引用需 volatile 语义

## Sub-sprint 分解

### v3.1.0 (3g `&mut` + lifetime + Cap<T> 8 规则)

**Scope**:

#### Part 1: parser `&mut T` 类型 + lifetime 标注

1. `compiler/src0/parser.jhyy`(改):
   - 类型解析加 `&T`(共享借用)+ `&mut T`(可变借用)
   - let binding 加 lifetime 标注:`let x: &'a mut T = ...`(省略时按 NLL 自动推断)
   - 函数参数 + 返回类型支持借用类型
   - Lifetime elision 规则(NLL 简化版;不实现完整 Lexical lifetimes)

#### Part 2: sema 借用检查(NLL 简化版)

1. `compiler/src0/sema.jhyy`(改,~500 行新增):
   - 借用检查(NLL — Non-Lexical Lifetimes;`Polonius` 完整版留 v3.x 末)
   - 规则:
     - 同一 scope 内 `&mut` 借用独占(无其他 `&` 或 `&mut` 活跃)
     - 借用生命周期 = NLL 推断(scope 结束 = 借用结束)
     - 不支持 reborrow(`&mut *x` 留 v3.x 中)— 简化为 `&mut *x` 等价 `&mut x`
     - 不支持 lifetime 子类型(subtype / variance)— 留 v3.x 中
2. 错误信息:借用冲突时指向具体 line + column + 冲突变量名
3. W-069 NLL borrow check workaround 文档登(if any edge case)

#### Part 3: codegen 借用保留 → 寄存器分配时不动借用变量

1. `compiler/src0/codegen.jhyy`(改,~200 行):
   - 借用变量标记 `is_borrowed: i32` 传到 CGContext
   - 简化 escape analysis:被借用的变量在借用生命周期内不分配到寄存器(走 stack slot)
2. V2-A `codegen_amd64.jhyy`:跟 regalloc 集成 — 借用变量强制 stack slot(per § 4.3 regalloc vs 借用)

#### Part 4: Cap<T> 8 字节布局

1. `compiler/src0/codegen.jhyy`(改,~80 行):
   - 内置类型 `Cap<T>`(per D6 + `project_cap_abi_layout`)
   - 布局:`cnode_idx: u32` + `depth: u8` + `rights: u16` + `padding: u8`(显式 padding 到 8 字节)
   - `sizeof(Cap<i32>) == 8` 验证
2. ABI:`Cap<T>` pass-by-value 走单个 64-bit register / stack slot(per SysV + MS x64 8-byte class)
3. V2-A `codegen_amd64.jhyy`:Cap<T> 布局集成
4. `tests/cap_test.jhyy`:`sizeof(Cap<i32>) == 8` 验证

**Key files**:
- 改 `compiler/src0/parser.jhyy`(借用类型 + lifetime,~250 行)
- 改 `compiler/src0/sema.jhyy`(NLL 借用检查,~500 行)
- 改 `compiler/src0/codegen.jhyy`(借用保留 + Cap<T> 布局,~280 行)
- 改 `compiler/src0/codegen_amd64.jhyy`(V2-A 集成 + Cap<T> 布局,~50 行)
- 新建 `tests/cap_test.jhyy`(~30 行)
- 新建 `tests/borrow_check_basic.jhyy`(~50 行,基本借用冲突验证)
- 新建 `docs/abis/jhyy-lang-spec-borrow-check-supplement-v3.1.0.md`(~200 行 supplement)
- 新建 `docs/abis/jhyy-lang-spec-cap-t-supplement-v3.1.0.md`(~150 行 supplement)

**关键决策**:
- **NLL 而非 full Lexical**(per `v2-v3-parallel-sprint-plan.md § 4.4`):简化 + 确定性;Lexical 全功能留 v3.x 末
- **不**支持 reborrow(留 v3.x 中)— 简化为 `&mut *x` 等价 `&mut x`(可能不严谨但 ship gate 不阻塞)
- **不**支持 lifetime 子类型 / variance(留 v3.x 中)
- **借用保留 escape analysis 简化**:只 mark "借用变量不分配寄存器";不做精确数据流分析;留 v3.x 中
- **Cap<T> 显式 padding**:不依赖 ABI 自然对齐,显式 padding 保证 8 字节布局(per `project_cap_abi_layout`)
- **不**支持 Cap<T> 内嵌套 Cap<T>(`Cap<Cap<T>>` 留 v3.x 中)— 简单 8 字节布局

### v3.1.1 (3g.5 phantom 0-byte codegen)

**Scope**:

#### Part 1: PhantomData<T> 类型

1. `compiler/src0/parser.jhyy`(改,~30 行):
   - 内置类型 `PhantomData<T>`
2. `compiler/src0/sema.jhyy`(改,~20 行):
   - `PhantomData<T>` 类型识别
   - 不允许实例化(只能 `let x: PhantomData<T>;`)
3. `compiler/src0/codegen.jhyy`(改,~80 行):
   - `PhantomData<T>` 0 字节布局(ZST — Zero-Sized Type)
   - codegen 不 emit 布局字段,只占 type 表项
   - `sizeof(PhantomData<i32>) == 0` 验证

#### Part 2: 跟 Cap<T> 组合

1. `compiler/src0/codegen.jhyy`(改,~40 行):
   - `Cap<PhantomData<X>>` 组合:Cap 仍 8 字节,PhantomData 0 字节,组合仍 8 字节
   - `struct Wrapper<T> { cap: Cap<T>, _phantom: PhantomData<T> }`:sizeof == 8
2. V2-A `codegen_amd64.jhyy`:ZST 字段在 struct 内不 emit layout

#### Part 3: 验证

1. `tests/phantom_zst.jhyy`:`sizeof(PhantomData<i32>) == 0` + `sizeof(Wrapper<i32>) == 8` 验证
2. `tests/cap_phantom_combo.jhyy`:`Cap<PhantomData<X>>` 8 字节验证

**Key files**:
- 改 `compiler/src0/parser.jhyy`(PhantomData 类型 parser,~30 行)
- 改 `compiler/src0/sema.jhyy`(PhantomData 识别 + 不允许实例化,~20 行)
- 改 `compiler/src0/codegen.jhyy`(ZST codegen 路径 + 跟 Cap 组合,~120 行)
- 改 `compiler/src0/codegen_amd64.jhyy`(V2-A 移植 ZST 不 emit layout,~20 行)
- 新建 `tests/phantom_zst.jhyy`(~30 行)
- 新建 `tests/cap_phantom_combo.jhyy`(~30 行)
- 新建 `docs/abis/jhyy-lang-spec-phantomdata-supplement-v3.1.1.md`(~80 行 supplement)

**关键决策**:
- **PhantomData 不允许实例化**:M0 简化;用户只能声明字段,不能 `let p = PhantomData<i32> {}`(防止误用)
- **PhantomData 在 struct 内不占 layout**:per Rust ZST 语义;用户需要 type-level 标记时使用
- **不**支持 `PhantomData<&T>` 等复杂 lifetime 参数(留 v3.x 中)
- **D27 锁:本 sub-sprint 必须在 v3.1.0 ship 后启动**(per D27 串行规则)

### v3.1.2 (3g.7 cap table 联调)

**Scope**:

#### Part 1: cap table 类型

1. `compiler/src0/parser.jhyy`(改,~30 行):
   - 内置类型 `CapTable<T>`(`struct CapTable<T> { caps: [*]Cap<T>, len: i64 }`)
   - `*Cap<T>` 裸指针类型(无借用)
2. `compiler/src0/sema.jhyy`(改,~50 行):
   - `CapTable<T>` 类型识别 + 字段访问
3. `compiler/src0/codegen.jhyy`(改,~80 行):
   - `CapTable<T>` 布局:`*Cap<T>`(8-byte 指针)+ `len: i64`(8 字节),总 16 字节
   - `[*]Cap<T>` 切片类型(per lang-spec v1.3.0 § 已有切片;Cap<T> 8 字节 → 切片元素 8 字节)

#### Part 2: 跨函数 cap pass

1. `compiler/src0/sema.jhyy`(改,~80 行):
   - `Cap<T>` 参数 / 返回值的 cap pass 校验(per ABI § 5 c-typedef)
   - 不允许 Cap<T> 跨越 volatile 引用(per V3-B 3c 语义)
2. `compiler/src0/codegen.jhyy`(改,~60 行):
   - `Cap<T>` 跨函数 call 走 64-bit register(同 Cap<T> pass-by-value)
3. V2-A `codegen_amd64.jhyy`:跨函数 Cap<T> register 分配
4. V2-B `abi_amd64_sysv.jhyy`:`Cap<T>` class = INTEGER(SysV 8-byte,占一个 reg)

#### Part 3: 联调验证

1. `tests/cap_table_basic.jhyy`:`CapTable<i32>` 创建 + 访问 + pass 跨函数
2. `tests/cap_test_advanced.jhyy`:跟 V3-C 3g + 3g.5 联合验证
3. V2-C v2.8.0 N 代 fixed point 验算脚本跑 `tests/cap_test.jhyy` 自动通过

**Key files**:
- 改 `compiler/src0/parser.jhyy`(CapTable + 裸指针 Cap<T>,~30 行)
- 改 `compiler/src0/sema.jhyy`(CapTable + cap pass + 跨函数,~130 行)
- 改 `compiler/src0/codegen.jhyy`(CapTable 布局 + 跨函数 emit,~140 行)
- 改 `compiler/src0/codegen_amd64.jhyy`(V2-A 跨函数 Cap<T> reg,~30 行)
- 改 `compiler/src0/abi_amd64_sysv.jhyy`(V2-B Cap<T> class,~10 行)
- 新建 `tests/cap_table_basic.jhyy`(~50 行)
- 新建 `tests/cap_test_advanced.jhyy`(~80 行)
- 新建 `docs/abis/jhyy-lang-spec-cap-table-supplement-v3.1.2.md`(~120 行 supplement)

**关键决策**:
- **Cap<T> 跨函数 cap pass 校验**:不允许跨越 volatile 引用(借用 + volatile 互斥语义复杂;留 v3.x 中)
- **CapTable<T> 用裸指针 + 长度**:per c-typedef 不借用(slice 借用由 user 自管;Cap<T> 本身不可变)
- **D27 锁:本 sub-sprint 必须在 v3.1.1 ship 后启动**(per D27 串行规则)
- **V2-C N 代 fixed point 验算触发**:v3.1.2 ship 后 V2-C v2.8.0 才可启动(否则 N 代 fixed point 跑 cap_test fail)

## 跨 axis 硬约束

- **D27** 串行不可调换:3g → 3g.5 → 3g.7(per `v2-v3-parallel-sprint-plan.md § 4.4`)
- **V2-C v2.8.0 N 代 fixed point 验算触发**:V3-C ship 后 V2-C 可启动(否则 N 代验算跑 `cap_test.jhyy` fail)
- **3c volatile 必须已 ship**(V3-B v3.0.3)— cap pass 跨 volatile 引用需 volatile 语义
- **V2-B regalloc**(per § 4.3):v2.6.0 regalloc 不考虑借用保留 → v3.1.0 ship 后,V2-C v2.8.0 N 代 fixed point 验算时跑借用测试 → 如发现失败,退回 V2-B 修 regalloc(已知风险,接受)
- **D43** 每 sub-sprint 重新 baseline(v3.1.0 → v3.1.1 → v3.1.2 各 1 baseline sha)
- **本 batch 内 sub-sprint 串行不可调换**(v3.1.0 → v3.1.1 → v3.1.2)— 顺序锁,任意一个失败 → batch 卡住 → 中途可暂停 + user 介入

## Batch ship gate

- 3 sub-sprints 全 ship,合并 1 个 `docs/logs/v3/changelog-v3.1.md` umbrella(per `feedback_changelog_umbrella`)
- 每 ship `jhyy_regress` 104/104 PASS + `jhyy_selfhost_check` 4-stage byte-equal
- v3.1.0 ship 时:
  - `tests/cap_test.jhyy` 8-byte layout 验证(`sizeof(Cap<i32>) == 8`)
  - `tests/borrow_check_basic.jhyy` 借用冲突检测正确
- v3.1.1 ship 时:
  - `tests/phantom_zst.jhyy` ZST 验证
  - `tests/cap_phantom_combo.jhyy` 8 字节布局保持
- v3.1.2 ship 时:
  - `tests/cap_table_basic.jhyy` CapTable 跨函数验证
  - V2-C v2.8.0 N 代 fixed point 验算脚本**就绪**(等 V2-C 启动)
- M4 launch 集成 gate 触发(per `v2.0.0-os-prep.md § 1`):v2 axis N 代 fixed point ✅ + v3.1.0..v3.1.2 全 ship

## 风险 + 缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| 借用检查 + 8 字节布局 + cap table 联调复杂(3 个 sub-sprint 各自 ~500-800 行代码) | V3-C ship 阻塞 | 中途可暂停 + user 介入;每 sub-sprint ship 后 baseline 锁定,下次启动可恢复 |
| D27 不可调换 → 任一失败 batch 卡住 | V3-C 阻塞 | 中途可暂停 + user 介入 |
| Regalloc vs 借用保留(已知 V2-C v2.8.0 N 代验算时再验证) | V2-C ship 阻塞(退回 V2-B 修) | 接受 risk;V2-B regalloc 启发式已知不完善;V2-C ship gate 触发前如发现 fail,临时 hotfix 进 v2.7.x patch(不进 v2.8.0) |
| NLL 简化版 reborrow `&mut *x` 误用 → 编过但行为错误 | ship gate 阻塞 | 限制 `&mut *x` 在 expr 位置禁用,只允许 stmt-level `let y = &mut x` |
| Cap<T> 嵌套 Cap<T> 8 字节布局不保 | sizeof 错误 | M0 简单 8 字节布局(per `project_cap_abi_layout`);嵌套 case 留 v3.x 中 |
| PhantomData 实例化允许 → 误用 | type system 漏洞 | sema 显式禁用 instance + 错误信息;test 覆盖 |
| CapTable 跨函数 pass 借用 vs cap pass 冲突 | sema 复杂度 | M0 简化:CapTable pass-by-value 走 8-byte pointer + 8-byte len;不做借用 |
| 跨函数 Cap<T> 跟 3c volatile 互斥(cap pass 跨 volatile 引用) | ship gate 阻塞 | sema 显式禁用 + 错误信息;留 v3.x 中完整支持 |

## Out of scope

- NLL 完整版 / Polonius(留 v3.x 末)
- 全 Lexical lifetimes(留 v3.x 末)
- lifetime 子类型 / variance(留 v3.x 末)
- 完整 reborrow `&mut *x`(留 v3.x 中)
- 精确 escape analysis(留 v3.x 中)
- `Cap<Cap<T>>` 嵌套(留 v3.x 中)
- `PhantomData<&T>` lifetime 参数(留 v3.x 中)
- CapTable 借用语义(留 v3.x 中)— 当前 CapTable 用裸指针 + 长度
- Cap<T> 跨 volatile 引用借用(留 v3.x 中)
- 多线程 cap(M4 launch 之后;留 v4.x)
- 全 C11 / Rust memory model(留 v3.x 中)
- ARM / RISC-V Cap<T> ABI(留 v3.x 中 / M11 launch 时)
- 3a-3f(留 V3-B)
- 3d no_std(留 V3-A)
- M5(留独立 sprint)

## 文件变更清单

### 新建(3 sub-sprints 累计)
- `tests/cap_test.jhyy`(~30 行,v3.1.0)
- `tests/borrow_check_basic.jhyy`(~50 行,v3.1.0)
- `tests/phantom_zst.jhyy`(~30 行,v3.1.1)
- `tests/cap_phantom_combo.jhyy`(~30 行,v3.1.1)
- `tests/cap_table_basic.jhyy`(~50 行,v3.1.2)
- `tests/cap_test_advanced.jhyy`(~80 行,v3.1.2)
- `docs/abis/jhyy-lang-spec-borrow-check-supplement-v3.1.0.md`(~200 行)
- `docs/abis/jhyy-lang-spec-cap-t-supplement-v3.1.0.md`(~150 行)
- `docs/abis/jhyy-lang-spec-phantomdata-supplement-v3.1.1.md`(~80 行)
- `docs/abis/jhyy-lang-spec-cap-table-supplement-v3.1.2.md`(~120 行)
- `docs/logs/v3/changelog-v3.1.md`(umbrella,V3-C 3 sub-sprints 合并)

### 改动(3 sub-sprints 累计)
- `compiler/src0/parser.jhyy`(借用类型 + lifetime + PhantomData + CapTable + 裸指针 Cap<T>,累计 ~340 行)
- `compiler/src0/sema.jhyy`(NLL 借用检查 + PhantomData + CapTable + cap pass + 跨函数,~810 行)
- `compiler/src0/codegen.jhyy`(借用保留 + Cap<T> 布局 + ZST + CapTable + 跨函数 emit,累计 ~600 行)
- `compiler/src0/codegen_amd64.jhyy`(V2-A 集成 + Cap<T> + ZST + 跨函数 Cap<T>,~100 行)
- `compiler/src0/abi_amd64_sysv.jhyy`(Cap<T> class,~10 行)
- `docs/logs/v3/changelog-v3.1.md`(3 段增量,每 sub-sprint ~15 行)

## Commit / tag 节奏

每 sub-sprint 1 个 commit + tag(3 sub-sprint × 1 commit = 3 commits):
- **Commit 1**:`feat(borrow-check): add &mut + lifetime NLL + Cap<T> 8-byte layout (3g)` → tag `v3.1.0`
- **Commit 2**:`feat(phantom): add PhantomData<T> ZST codegen + Cap combo (3g.5)` → tag `v3.1.1`
- **Commit 3**:`feat(cap-table): add CapTable<T> + cross-function cap pass (3g.7)` → tag `v3.1.2`
- 每 ship 重新 baseline sha → 写进 `changelog-v3.1.md` 对应段
- **V2-C 启动通知**:V3-C ship 后通知 user V2-C v2.8.0 可启动(M5-bridge 触发)

## Cross-ref

- 上游:`docs/plans/v3/batch-V3-A-plan.md`(V3-A no_std 已 ship)+ `batch-V3-B-plan.md`(V3-B 3a-3f 已 ship)
- 下游:`docs/plans/v2/batch-V2-C-plan.md`(V2-C v2.8.0 N 代 fixed point 触发前置 = V3-C ship)
- 跨 axis V2-A codegen_amd64.jhyy:`docs/plans/v2/batch-V2-A-plan.md`(V2-A 预留借用保留 regalloc 接口,V3-C 填充)
- 跨 axis V2-B sysv Cap<T>:`docs/plans/v2/batch-V2-B-plan.md`(v2.7.0 abi_amd64_sysv.jhyy 加 Cap<T> class)
- D27 串行锁:`docs/plans/roadmap/v2-v3-parallel-sprint-plan.md § 4.4`
- M4 launch gate:`docs/plans/v2/v2.0.0-os-prep.md § 1 M4`
- 8 字节 Cap<T> layout:`memory/project_cap_abi_layout.md`
