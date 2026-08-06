# Architecture Refactor — 整体路线图修订

> **状态**: 草案
> **目的**: 把所有 v*.* 计划文件跟当前真实状态对齐 + 整合 jhyy_OS 协调结果
> **关联**: 触发本次重构的源材料 — v0.8 wip commit 12 实测 + jhyy_OS 协调(`coordination.md` / `v0.0.2-foundation-revision.md` / `v0.0.1.5-M5b-prereqs.md`)
> **修改的文档**: 列出每条改动 + 改动依据 + 影响面

---

## § 0 为什么单独立这份文档

旧 plan 体系是分阶段逐步写的,几个关键事实在 v0.6 / v0.7 写计划时还没显现,导致多个文件出现:
- 范围重叠(v2.0.0-os-prep 的 P0 6 特 vs v3.x 3a-3f)
- 状态脱节(v0.8 任务清单"3 commit 收尾" vs 实际跑到 commit 12 + 9 workaround + Stage 0 closure)
- OS 错位(v2.x 写"ELF multi-target 优先" vs OS 实际走 UEFI + PE/COFF,不需要 ELF)

**本 doc 不重复内容**,只列**改动 + 依据 + 影响**。每条改动标一个 R-N 编号,跟实施 checklist 同步。

---

## § 1 真实状态盘点(本节是其他所有改动的 ground truth)

### 1.1 jhyy 编译器侧(本 repo)

| 事实 | 来源 | 旧 plan 是否提到 |
|------|------|------------------|
| v0.6.0 已发 | git tag | v1.0-self-hosting.md 提"v0.6.0 通过" |
| v0.7.0(7A enum first-class + 7B const struct array)已发 | changelog | 是 |
| **v0.8 wip 跑到 commit 12(5820793)** | git log | ❌ 旧 v0.8 任务清单只画到 3 commit 收尾 |
| 9 个 codegen workaround(W-001 ~ W-009)| `docs/internal/workarounds.md` | ❌ 旧 plan 完全没提 |
| **Stage 0 closure 部分达成**(jhyy_v1 编 src0/arena.jhyy 通过 QBE typecheck;其余 13 个 src0/*.jhyy 大部分**还没编过**)| commit 12 自验 | ❌ 旧 v0.8 任务清单"Stage 1 = M4 闭环" |
| **v1 regress:12 OK / 47 总**(剩余 35 个 = **8 CERR + 8 AV + 25 STK + 0 NORUN**)| commit 12 自测 | ❌ |
| 29-extsw hypothesis 50/50 是 arena.jhyy 翻译稿问题,非 codegen 真 bug | memory `project_bootstrap_closure_state` | ❌ |
| 真闭环回归预期:**12 OK 持平即可**(不是 47/47);剩余 CERR 是 parser 翻译层缺 match-expr / const-array / import,属 sprint 5/6 范畴 | memory 同上 | ❌ |
| 编译器自身用 arena.jhyy(region-based),语言层原生支持 region types | `compiler/src0/arena.jhyy` 验证 | ❌(v0.x-c-compiler-roadmap.md 不提) |

#### 1.1.1 v1 regress 35 失败分类(本轮事实)

| 类别 | 数量 | 性质 | 估计归属 |
|------|------|------|---------|
| **CERR**(parser 翻译层缺功能)| 8 | match-expr / const-array / const_struct_array / import 翻译缺 | sprint 5/6 工作 |
| **AV**(codegen 翻译层缺功能)| 8 | 残缺或类型错 | 逐个修 |
| **STK**(codegen 翻译层缺功能)| 25 | slice / array 路径有 bug | 逐个修 |
| **Slice/array cslel 子集** | 5+ | `_v1_array_to_slice.il:21`、`slice_*.il:15` 这类 | 单独 W-010 候选 |

#### 1.1.2 W-001 ~ W-009 workaround 详情(本轮已修 + 待真修)

**Stage 0 入口解锁(本轮 W-007/8/9)**:
- **W-007 extsw**:`codegen.c:222` `cg_convert_arg` 缺 `w→l` extension 路径;同时 jhyy v1 codegen 对应处
- **W-008 cg_find_field_offset 三层 deref 漏修**:嵌套 struct field 偏移计算错(3 层 deref 漏一层)
- **W-009 cg_convert_arg + NODE_CAST 两处放宽**:`src_t==0` 兜底 + 移除早 bail

**Stage 0 内部解锁(更早期 W-001~W-006)**:
- **W-001 byte-by-byte hash**:symtab 长度相关 heap corruption(identifier 长度 6-8 + `_buf` 后缀触发)
- **W-002 identifier rename**:211 个触发标识符改名(到 9+ 字符避 6-8 长度触发)
- **W-003 let _ = fncall() workaround**:`let _ = fncall()` 顶层 → 直接调(避 codegen 把赋死当 dead code 优化掉)
- **W-005 let-mut workaround**:同 v0.6.5 let mut bug(已修 sema);本轮是 let-mut 在 src0/ 翻译稿里有未 let mut 的遗漏
- **W-006 1-char local var 触发面文档**:codegen 对 1 字符 local var 路径不稳,文档化触发面

**待 v0.9 真修的 9 个 workaround** — 全部在 v0.9 commit 2 集中修(逐个 + 删 jhyy 端 workaround 注释)

### 1.2 jhyy_OS 侧(独立 repo)

| 事实 | 来源 | OS plan 锁 |
|------|------|------------|
| 5 原则锁(可行且简单 / 双线作战 / 寄生 Windows / Debug 在语言里 / Kernel 不解决语言问题)| `v0.0.0-design.md` § 2 | 🔒 |
| 混合内存模型:region types primary + linear cap + raw MMIO + unsafe_share | `v0.0.2-foundation-revision.md` § 3.2 | 🔒 |
| **boot 路径 = UEFI + PE/COFF(走 OVMF)** | `v0.0.2-foundation-revision.md` § 5 | 🔒 |
| M1-M11 依赖图锁:M1-M10 不需 generics/closures/async,M11 才需(3i+3j+3l) | `v0.0.2-foundation-revision.md` § 4 | 🔒 |
| Cap<T> 8 字节布局(`{cnode_idx: u32, depth: u8, rights: u16}` + phantom 0-byte)| `coordination.md` § 3 | 🔒 |
| 缺 feature = 设计输入(非 blocker) | `coordination.md` § 3 | 🔒 |
| jhyy spec 当前能力 baseline 锁(v1.1.0 spec + v0.7 编译器)| `coordination.md` § 3 | 🔒 |
| MVP coding style:fixed array + 显式 fn + struct env + raw pointer | `v0.0.2-foundation-revision.md` § 6 | 🔒 |
| `&mut` 推迟到 sprint 3g,M1-M10 用 raw pointer | `v0.0.2-foundation-revision.md` § 6.1 | 🔒 |

### 1.3 跨项目错位(本次重构的触发条件)

| 错位 | 旧 plan 描述 | 真实状态 |
|------|-------------|---------|
| v2.x 范围 | 自写 QBE + ELF multi-target(v2.x-qbe-rewrite.md 旧文)| OS 不需要 ELF;真实需要 = `amd64_win_freestanding` target(走 OVMF)+ 移除 QBE 工具链 |
| v2.0.0-os-prep P0 6 特性 | 列为 backlog,配 v3.x sprint 1-6 编号 | 实际已被 v3.x 3a-3f 完整覆盖(已重排);os-prep 失去存在意义,改完成定义视图 |
| v0.8 范围 | 3 commit 收尾(commit 1 修 bug,commit 2 翻译 main.c,commit 3 Stage 1) | 实际 12 commit,9 workaround,Stage 0 已闭合;main.c 翻译延后到 v0.9(命名需重切分)|
| v1.0 任务清单"不在 v1.0 范围" | 写"性能优化" / "多目标" / "v4.x+ 优化" | 缺 v0 codegen workaround 真修时机(W-001~W-009 哪些进 v0.9 patch,哪些推迟到 v1.0 末)|
| v0.x-c-compiler-roadmap | 仍是 1a-1g 旧 sprint 描述(v0.0~v0.1 时期)| 跟当前 v0.6/v0.7 已发版本脱节;应改为"已完成 sprint 总览 + 跟 v0.6+ 状态对齐" |
| v3.x OS P0 编号 | 旧 plan 写"v3.x sprint 1-6" | 实际 v3.x 3a-3f;编号已重排 |
| Cap<T> 16 字节布局(v3.x-capability-spec 旧版)| 8 字节 phantom 0-byte + 8 字节 _phantom 总 16 字节 | OS 端锁 8 字节(cnode_idx+depth+rights)+ phantom 0 字节(总 8 字节) |

---

## § 2 重构总览

按文档逐条列。编号 R-N 供后续实施追踪。

| R-N | 文档 | 改动类别 | 优先级 |
|-----|------|---------|--------|
| R-1 | v0.8.0 任务清单 + 概要设计.md | 拆分 v0.8 / 新建 v0.9 | P0 |
| R-2 | v0.x-c-compiler-roadmap.md | 改写:已完成 sprint 总览 + 跟 v0.6+ 对齐 | P0 |
| R-3 | v1.0.0 任务清单 + 概要设计.md | "不在 v1.0 范围"段重写 + 真闭环预期下调 | P0 |
| R-4 | v1.0.0 详细实现方案.md | codegen 坑清单加 W-001~W-009 + 29-extsw 状态记录 | P0 |
| R-5 | v1.0-self-hosting.md | 自举定义段加"12 OK 持平"注释(已加 OS 联动,只补这一段) | P1 |
| R-6 | v2.x-qbe-rewrite.md | 范围重写:UEFI 优先,OS 不需 ELF | P0 |
| R-7 | v2.0.0-os-prep.md | 改完成定义视图,删 P0 6 特性 backlog(已迁 v3.x 3a-3f) | P0 |
| R-8 | v3.x-language-expansion.md | 不变(已按 OS 需求重排过)| — |
| R-9 | v3.x-capability-spec.md | 改 8 字节布局描述(已部分对,补 phantom 0 字节措辞)| P1 |
| R-10 | 新建 `docs/plans/roadmap/architecture-refactor.md`(本文件) | 完成 | ✅ |

**总实施 = 9 doc 改动 + 1 新建 = 10 步**。

---

## § 3 R-1: 拆分 v0.8 / 新建 v0.9

### 改动

**v0.8.0 任务清单**:
- § 当前状态(2026-07-02)段改成 § 当前状态(commit 12 收尾时点)
- § 范围:删 commit 2 / commit 3 段(已推迟)
- § 实施顺序:只留 v0.8 wip 实际跑过的 12 commit(W-001~W-009 + Stage 0 closure unlock)
- § 不在 v0.8.0 范围:加"W-001~W-009 workaround 推迟到 v0.9 修" + "main.c 翻译推迟到 v0.9"
- § 验收:改"Stage 0 closure 解锁 + jhyy_v1 跑 regress 16 OK / 47 总"为完成定义

**新建 v0.9.0 任务清单**(对齐旧 v0.8 § commit 2/3):
- § 范围:
  - **commit 1**: 29-extsw hypothesis 验证(grep arena.jhyy ptr 算术上下文,确认 i32 误用范围;若 50/50 命中则修 arena.jhyy 而非 codegen)
  - **commit 2**: codegen bug 真修(逐个 W-001~W-009 真修,删 jhyy 端 workaround 注释)
  - **commit 3**: 翻译 main.c → main.jhyy(从旧 v0.8 任务清单 § commit 2 拿过来)
  - **commit 4**: Stage 1 byte-equal 验证 + regress.py JHYY_CC 支持(从旧 v0.8 任务清单 § commit 3 拿过来)
- § 验收:`diff jhyy_0.il jhyy_1.il byte-equal` + `JHYY_CC=jhyy_1 python regress.py` 持平(v0.8 16 OK 持平)

### 依据

- **v0.8 任务清单 § 当前状态(2026-07-02)** 写"当前状态"在 commit 1 后;实际 commit 12 才到达 Stage 0 closure。计划跟现实差 11 个 commit
- **codegen workaround** 体系是 sprint 4 / 5 期间逐个挖出来的,旧 plan 完全没预测到;W-001~W-009 任何一个真修都涉及 codegen.jhyy 翻译稿 + C 端 codegen.c + jhyy_helpers.c 三处改动,**v0.9 集中修**比分散到 v1.0 末更可控
- **main.c 翻译**(523 行 C → jhyy)是 sprint 5 的核心工作,跟 codegen bug 真修**强耦合**(codegen bug 修完 main.jhyy 才能稳定跑);v0.9 一起做

### 影响

- v0.9.0 任务清单**新建**(`docs/plans/v0/v0.9.0任务清单 + 概要设计.md`)
- v0.8.0 changelog 收尾后单独发(`docs/logs/v0/changelog-v0.8.0.md` 已有,补末尾段)
- v1.0.0 任务清单不动(本来就画 v1.0 = v1.x 自举 sprint 5 + Stage 1 验证);但 § 实施顺序表里 v0.8 → v0.9 → v1.0 重新对齐

---

## § 4 R-2: 改写 v0.x-c-compiler-roadmap.md

### 改动

整文件**改写**为:
- § 标题:v0.x: C 编译器实现(自举门槛)— **历史总览**
- § 总览表:v0.0 → v0.1 → v0.2 → v0.3 → v0.4 → v0.5 → v0.6 → v0.7 → v0.8 各 sprint 一行(状态 / 关键交付)
- § 关键决策:5 条 — amd64_win only / QBE 工具链 / struct sret 约定 / arena allocator / QBE IL "wb" 写盘
- § 跟 v1.x / v2.x 边界:v0.x = "C 端编译器到自举门槛"(v0.6+ 达成);v1.x 接前端翻译;v2.x 接 QBE rewrite
- 删原文件所有 1a-1g 旧 sprint 描述(已发版本 changelog 写过的内容不重复)

### 依据

- 旧 v0.x-c-compiler-roadmap.md 是 v0.0/v0.1 时期写的"未来 sprint 计划",所有 1a-1g 描述已通过 v0.0~v0.7 changelog 落地;**作为"未来计划"它已过期**,作为"历史总览"它不存在
- 后续新人(或不熟悉 v0.x 历史的 user)需要一份"v0.x 已完成什么 / 关键决策是什么 / 跟 v1.x 边界在哪"的入口
- v0.6+ 已是"自举门槛"(lang-spec 附录 C),v0.x = "基础设施已就绪"

### 影响

- CLAUDE.md "路线图 + Sprint" 表格更新:把 v0.x-c-compiler-roadmap 标"已完成"或"历史总览",加 v0.9 / v0.8 wip 状态
- 读 v0.x-c-compiler-roadmap.md 的人不会再误以为"未启动"

---

## § 5 R-3: v1.0.0 任务清单"不在 v1.0 范围"重写

### 改动

v1.0.0 任务清单 § "不在 v1.0 范围(明确延后)" 整段重写。原表:

| 特性 | 延后到 | 理由 |
|---|---|---|
| QBE 完整重写 | v2.x(中期)/ v3.x+ | 2026-06-22 决策:先 v1.x 前端翻译,QBE 重写后做 |
| codegen 优化 | v2.x | v1.0 目标 = 翻译完成 + 行为正确,不优化 |
| 多目标架构(自研 OS)| v4.x+ | 当前 amd64_win 中间态(abi § 1 决策记录),自研 OS ABI 待定 |
| 字符串 stdlib | v1.0 sprint 1 util.jhyy 自带最小 slice API | codegen 翻译按需扩展 |
| 浮点 stdlib | v3.xa | v1.x codegen.jhyy 翻译时**保留**浮点路径(v0.5 sprint 5A 已就绪,删了就 broken) |
| Pattern binding codegen(`Some(v) => v` 提取 payload)| v1.0 patch(自举 codegen.jhyy 翻译时按需补)| v0.7 7A 仅 sema 层注册 binding,codegen 用 `_` 通配符规避 |
| 嵌套 const array / const fn / 编译期求值 | v3.x+ | 自举不需要(数据走 StringBuilder 直接 emit) |

**重写后**:

| 特性 | 延后到 | 理由 |
|---|---|---|
| v0 codegen bug 1/2/3/4 真修(LEA / phi / loadub / &local) | v0.9 patch(已拆分)| v0.8 期间 W-001~W-009 workaround 体系,逐个在 v0.9 真修 |
| W-005 util/arena 范围扩展 | v0.9 patch | v0.8 commit 10 workaround 范围 |
| W-006/W-007 文档同步 | v0.9 patch | v0.8 commit 10 文档 |
| 29-extsw 真修(若 50/50 命中) | v0.9 commit 1 | 经验性 hypothesis;v0.9 验证 |
| QBE 完整重写 | v2.0(v2.x 内) | OS 走 UEFI + PE/COFF,不需要 ELF 后端优先;v2.0 改 = `amd64_win_freestanding` target + 移除 QBE |
| codegen 优化 | v2.0+ | v1.0 目标 = 翻译完成 + 行为正确 |
| 多目标 | v2.x(v2.0 → v2.x)| v2.0 启动 amd64_win_freestanding;v2.x 加 amd64_sysv(Linux 引导 / 测试)|
| `&mut + lifetime` | v3.1 sprint 3g(OS P1-7)| OS 端 M4 capability 硬前置,跟 Cap<T> 联动实现 |
| 泛型(generics)| v3.2+ sprint 3i(OS M11 硬前置)| MVP M1-M10 用 fixed array 够,M11 编译器源需要 |
| 闭包(closures)| v3.2+ sprint 3j(OS M11 硬前置)| MVP M1-M10 用显式 fn + struct env,M11 编译器源需要 |
| std lib(9 模块)| v3.2+ sprint 3l(OS M11 硬前置)| M11 编译器编自己时需要 std 跟 runtime |
| Cap<T> 完整实现 | v3.1 sprint 3g + 3g.5 + 3g.7 | 跟 `&mut + lifetime` 联动;MVP M4 硬前置 |
| inline asm / naked / volatile / no_std / link_section / memory barrier | v3.0 sprint 3a-3f(OS P0 6 特)| MVP M1 启动硬前置 |

### 依据

- v0.8 wip 实际跑出 W-001~W-009,旧 v1.0 plan 完全没提 → 范围脱节
- 旧 "v4.x+ 多目标" 表述错:OS 走 UEFI + PE/COFF,v2.0 就该有 freestanding target
- 旧 "v3.xa" "v3.x+" 模糊编号 → 跟 v3.x-language-expansion.md 的 3a-3n 编号对齐
- MVP 路径(M1-M10)不需要的特性和 M11 需要的特性必须分清(OS 端锁了)

### 影响

- 跨文档一致性:v0.8 / v0.9 / v1.0 / v2.0 / v2.x / v3.0 / v3.1 / v3.2+ 关系图清晰
- sprint 计划**真的可执行**(不再"等 2026-06-22 决策"等空话)

---

## § 6 R-4: v1.0.0 详细实现方案 codegen 坑清单 + 29-extsw

### 改动

v1.0.0 详细实现方案 § "v0.6 codegen 已知坑" 表(7 条)扩展为 10 条:
- 保留原 7 条(部分编号调整)
- **新增 8 条**:W-001~W-009 翻译(从 `docs/internal/workarounds.md` 拿过来),每条标"v0.9 真修 / 延后 / 接受 workaround"状态
- **新增 9 条**:29-extsw hypothesis(50/50 arena.jhyy 翻译稿问题,非 codegen 真 bug;v0.9 验证)
- **新增 10 条**:jhyy_helpers.c 范围(sprint 1 末 + sprint 4 末 + sprint 5 末 三次扩展)

加一段 § "sprint 末 codegen 坑记录模板" 说明 `docs/logs/sprint-N-codegen-bugs.md` 怎么写。

### 依据

- 旧表是 v0.6.0 收尾时写的(7 条),v0.7/v0.8 sprint 4 / 5 期间又挖出 9+ workaround;不更新则**自举翻译时无依据**
- 29-extsw 50/50 hypothesis 在 `memory/project_bootstrap_closure_state.md`,**不进 plan 等于失忆**;写进 plan 跟 codegen 坑表同一张表
- codegen 坑表是 v1.0 sprint 翻译时**唯一**的"已知道路"清单,丢一项 = 踩坑

### 影响

- 自举翻译时**有完整 10 条清单可对照**
- v0.9 真修每条都对应到具体 codegen.c / codegen.jhyy / jhyy_helpers.c 文件

---

## § 7 R-5: v1.0-self-hosting.md 自举定义加"12 OK 持平"注释

### 改动

v1.0-self-hosting.md § "自举定义" 段加一行注释:
> **真闭环回归预期**:jhyy_v1 编 jhyy_v1 跑 regress 大概率 = **12 OK 持平**(剩余 CERR 是 parser 翻译层缺 match-expr / const-array / import,属 sprint 5+ 范畴);**不接受 "要求 47/47 全过" 作为 v1.0 闭环门槛**。验证时点:commit 13+ 跑 arena_test 端到端

### 依据

- memory `project_bootstrap_closure_state.md` 第 3 段已写"真闭环回归预期 = 12 OK 持平即可"
- 旧 v1.0-self-hosting.md 写"diff byte-equal = 自举成功" + "regress.py 全过" → 实际 47/47 全过不现实(parser 翻译层缺口)
- memory 写但 v1.0 plan 没引用,等于没引用

### 影响

- v1.0 验收标准从"regress.py 全过"软化为"diff byte-equal + regress.py 持平(driver 一档)"
- user 跟 reviewer 看到"12 OK"不会被吓到(不是 jhyy 编 jhyy 编不动,是 parser 翻译层缺口)

---

## § 8 R-6: v2.x-qbe-rewrite.md 范围重写

### 改动

v2.x-qbe-rewrite.md **整体重写**。原文件保留"OS 对齐增量"段(已加),但 "在 v2.x 内" / "不在 v2.x 内" / "关键技术挑战" 段需要重写。

**重写后 § 在 v2.x 内**:
- 自写 QBE 后端(IL → .s 汇编)
- 整个编译栈 jhyy 化,无外部 QBE 依赖
- N 代自举 fixed point 验证
- 运行时性能不退化(≤ 1.1x)
- **多目标支持**(调整优先级):
  - **v2.0**:`amd64_win_freestanding` 目标(M1 启动所需,UEFI + PE/COFF + 无 libc)
  - **v2.x 内**:`amd64_sysv`(Linux 引导 / 测试)+ `amd64_sysv_freestanding`(OS 备用)
  - host:`amd64_win` 保持兼容(已支持)
- **确定性二进制 byte-equal**(v2.0 硬要求,.il + .s + .exe 全 byte-equal;`.exe byte-equal` 用 `gcc -g0 + strip + SOURCE_DATE_EPOCH + --build-id=none` 达成)

**重写后 § 不在 v2.x 内**:
- aarch64 / riscv64(v0.x + 后再说;v0.0.0 § 4 已锁 amd64 only v0.x)
- 自写 gcc / ld / as(保留外部工具链)
- 重写 QBE IL 文本层(仍用 QBE IL 作 IR)
- 引入新 ABI(沿用 amd64 + freestanding 自定义)

**重写后 § 关键技术挑战**:
- 挑战 1(byte-equal):加 `.exe byte-equal` 段(SOURCE_DATE_EPOCH 等)
- 挑战 2(指令集覆盖):保留
- 挑战 3(自举栈全栈验证):保留
- 挑战 4(多目标 + freestanding):**重写**:
  - **freestanding target 实现路径**:`#[no_std]` 联动 v3.x sprint 3d(但 v2.0 实现 `amd64_win_freestanding` 不需要 `#[no_std]` crate attr,只需"不 link libc"——所以 v2.0 不依赖 v3.x)
  - **boot stub 集成**:v3.x 3a-3f 实现 asm/naked/volatile/link_section 后,v2.0 末才能编"完整 freestanding 程序"
  - **OS boot.efi 路径**:v3.0 完成后,OS 用 v2.0 末的 amd64_win_freestanding 编 kernel.efi → 走 OVMF

### 依据

- OS 锁 UEFI + PE/COFF + OVMF,**v2.x QBE ELF 后端不阻塞 OS**(原 § 范围边界 写 ELF multi-target 是过时的"v0.0 时期想象")
- v2.x 必须**先于 OS M1 启动可达**,否则 jhyy 编 jhyy_OS kernel.efi 仍要依赖外部 QBE
- v2.0 跟 v3.0(v3.x P0 6 特)**部分并行**:
  - v2.0 启动 `amd64_win_freestanding` 不需要 `#[no_std]`(只需"不 link libc")
  - v3.0 sprint 3d 实现 `#[no_std]` 后,v2.0 末的 freestanding target 跟 `#[no_std]` 集成
  - OS 真启动(M1)v2.0 + v3.0 都要完成

### 影响

- v2.x 跟 v3.x 顺序从"严格串行"改为"v2.0 启动 + v3.0 并行,末段集成"
- v2.x 完成定义加".exe byte-equal 用 SOURCE_DATE_EPOCH 兜底"
- v2.0 完成标准 = "jhyy 编 hello-freestanding.jhyy → kernel.efi → 跑 OVMF 启动(无 libc 链接)"

---

## § 9 R-7: v2.0.0-os-prep.md 改完成定义视图

### 改动

整文件**改写**为:
- § 标题:v2.0.0:OS 准备 — 跟 jhyy_OS 的 v2.0 启动要求对齐
- § 完成定义:跟 jhyy_OS 协调(`coordination.md` § 1.1 + `v0.0.0-design.md` § 6):
  - v2.0 milestone = OS M1 启动可达(jhyy 编 kernel.efi + OVMF 跑通 printk)
  - v2.x 完成 = OS M11 启动可达(jhyy_OS 编 jhyy 编译器 + 跑 jhyy 编译器 编 jhyy_OS)
- § 关键决策点(从 v3.x 引用):P0 6 特性 = v3.x 3a-3f,**不在本文件 backlog**(已迁);本文件只列 v2.0 milestone 跟 v3.0 sprint 3a-3f 的**接口**
- § 跨项目接口:
  - v2.0 给 OS 提供:amd64_win_freestanding target(可编 UEFI PE/COFF,无 libc)
  - v3.0 给 OS 提供:sprint 3a-3f 6 特性(asm/naked/volatile/no_std/link_section/memory barrier)
  - v3.1 给 OS 提供:sprint 3g `&mut` + Cap<T>(OS M4 capability 硬前置)
- § 验收标准:从 v2.0.0-os-prep.md 旧文 P0/P1/P2 清单 → 删,改"v2.0 / v2.x 完成时 OS 启动到哪一里程碑"
- 删所有"v3.x sprint 1-6 编号"措辞(已迁 v3.x 3a-3f)

### 依据

- v2.0.0-os-prep.md 旧文写的"OS 必需语言特性 P0 6 特性"完全跟 v3.x-language-expansion.md 3a-3f 重复(后写,已重排);**两份文件描述同一件事,违反 single source of truth**
- 旧文 P1 `freestanding target` 说"v2.x 末" → 跟 R-6 重写后的 v2.0 = `amd64_win_freestanding` 冲突
- 旧文 P1 `compile-time const eval` → 跟 v3.x sprint 3m 的"基本优化"部分重叠,需拆分

### 影响

- v3.x-language-expansion.md 成为 OS P0 6 特性**唯一权威**
- v2.0.0-os-prep.md 成为"OS 启动里程碑视图"**唯一权威**
- v2.x-qbe-rewrite.md 成为"v2.x QBE + 多目标"**唯一权威**
- 三份文件**职责清晰不重叠**

---

## § 10 R-8: v3.x-language-expansion.md 不变

### 依据

- 已按 OS 需求重排过(3a-3f = OS P0,3g = `&mut`+lifetime,3h-3n = 后续)
- 已加"重排说明"在 § 0
- 已 cross-link OS 端 docs

### 验证项

- 编号 3a-3n 跟 `coordination.md` § 4.2 "Compiler sprint ↔ OS milestone" 表一致
- 3g.5 / 3g.7 拆 sprint 跟 `v3.x-capability-spec.md` § "实施拆 sprint" 一致

### 影响

- 无

---

## § 11 R-9: v3.x-capability-spec.md phantom 0-byte 措辞补齐

### 改动

v3.x-capability-spec.md § "内存布局(abi § 12 草案)" 段:
- 旧:Cap<T> 16 字节({cnode_idx:u32 + depth:u8 + rights:u16 + _phantom:*T})
- **新**:Cap<T> **运行时 8 字节**({cnode_idx:u32 + depth:u8 + rights:u16} 7 字节 + 1 字节 padding)+ `_phantom: *T` 是**编译期 0 字节字段**(phantom type 惯用法)
- 加一行:跟 `coordination.md` § 3 "Cap<T> phantom type 8 字节布局锁" cross-link

### 依据

- 旧文写"Cap<T> = 8 字节(cnode_idx + depth + rights)+ _phantom(0 字节)"在 § 内存布局已经对了,但 § 验收标准 § "phantom layout test" 写"size_of::<Cap<Page>>() == 8"是对的,§ 实施 sprint 3g 任务列表却写"codegen:Cap<T> 布局 = { cnode_idx: u32, depth: u8, rights: u16 }(16 字节)" — 旧措辞前后矛盾
- 跟 OS 端 coordination § 3 锁的 8 字节对齐

### 影响

- 文档前后一致
- 跟 jhyy_OS 端 cap 表布局 byte-equal 验证口径清晰

---

## § 12 实施顺序

按依赖链:

```
R-2 (v0.x-c-compiler-roadmap 改写) — 无依赖,先做
  ↓
R-1 (v0.8 拆分 + v0.9 新建) — 依赖 R-2
  ↓
R-3 (v1.0 任务清单"不在 v1.0 范围"重写) — 依赖 R-1(用 v0.9 引用)
R-4 (v1.0 详细实现方案 codegen 坑清单 + 29-extsw) — 依赖 R-1
  ↓
R-5 (v1.0-self-hosting.md 加 12 OK 注释) — 依赖 R-3
  ↓
R-6 (v2.x 范围重写) — 无依赖,但需 OS coordination § 3 UEFI 锁确认
R-7 (v2.0.0-os-prep 改完成定义视图) — 依赖 R-6(v2.x 重写后才有 milestone 引用)
R-9 (v3.x-capability-spec 8 字节措辞) — 无依赖
  ↓
R-8 (v3.x-language-expansion 验证,不改) — 最后验证 cross-ref
```

**总估时**:R-2 / R-8 / R-9 各 5 分钟(改写少);R-1 / R-3 / R-4 / R-6 / R-7 各 15-30 分钟(改写多)。

---

## § 13 跨文档引用关系(改后)

```
CLAUDE.md (项目入口)
  ↓
docs/plans/roadmap/README.md (route map 入口)
  ├─ v0.0-skeleton.md (历史)
  ├─ v0.x-c-compiler-roadmap.md (R-2 改:已完成 sprint 总览)
  ├─ v1.0-self-hosting.md (R-5 改:加 12 OK 注释)
  ├─ v2.x-qbe-rewrite.md (R-6 改:UEFI 优先,范围重写)
  ├─ v3.x-language-expansion.md (R-8 不变:3a-3n 已重排)
  ├─ v3.x-capability-spec.md (R-9 改:8 字节措辞)
  └─ architecture-refactor.md (本文件)

docs/plans/v0/ (L3 sprint 任务清单)
  ├─ v0.0~v0.7 各 sprint 任务清单(已发版本)
  ├─ v0.8.0 任务清单(R-1 改:commit 12 收尾)
  └─ v0.9.0 任务清单(R-1 新建:codegen bug 真修 + main.c 翻译)

docs/plans/v1/
  ├─ v1.0.0 任务清单(R-3 改:不在 v1.0 范围段重写)
  └─ v1.0.0 详细实现方案(R-4 改:codegen 坑清单加 W-001~W-009)

docs/plans/v2/
  └─ v2.0.0-os-prep.md (R-7 改:完成定义视图)

docs/internal/
  ├─ status.md (当前版本 / 已实现 / 已知限制)
  ├─ architecture.md (流水线 / 模块 / QBE IL / Stage 0 自举)
  ├─ build.md (编译 / QBE 坑)
  ├─ conventions.md (编码约定)
  ├─ tests.md (集成测试)
  └─ workarounds.md (W-001~W-009 现状,R-4 引用)

[../../../../jhyy_OS/docs/](../../../../jhyy_OS/docs/) (OS 端,跟本 repo 同级)
  └─ coordination.md (跨项目对齐,本 repo 通过绝对路径引用)
```

---

## § 14 跟 jhyy_OS 协调的对接点

本次重构跟 jhyy_OS 端 4 个 🔒 决策对接:

| OS 决策 | 编译器侧响应 | 落点 |
|---------|------------|------|
| UEFI + PE/COFF(走 OVMF)| v2.0 优先 `amd64_win_freestanding` target | R-6 |
| 混合内存模型(region types primary)| v3.0 跳过 borrow checker as primary(尊重 v0.0.0 原则 1) | R-8 不变(已重排) |
| MVP M11 依赖图锁(3i+3j+3l 推迟到 M11)| v1.0 任务清单"不在 v1.0 范围"段标 M11 硬前置 | R-3 |
| Cap<T> 8 字节布局锁 | v3.x-capability-spec 措辞一致 | R-9 |
| 缺 feature = 设计输入(非 blocker) | v1.0 任务清单不列"等待 feature 实现才做"的项 | R-3 + R-4 |
| jhyy spec 当前能力 baseline 锁 | v1.0 sprint 5 main.c 翻译用 fixed array + 显式 fn + struct env + raw pointer | R-4 |

---

## § 15 待 user 后续决定(本次重构不锁,留 OS 端协调)

| # | 决定项 | 建议 | 等谁 |
|---|--------|------|------|
| 1 | v0.9 codegen bug 真修顺序(W-001~W-009 全修还是分批)| 全修,v0.9 一口气清干净 | 编译器 agent |
| 2 | v2.0 `amd64_win_freestanding` 实现路径(走 QBE 还是自写 IL → .s 阶段)| v2.0 仍用 QBE + GCC;QBE 自写推到 v2.x 中期 | 编译器 agent |
| 3 | v2.0 .exe byte-equal 必要性 | 推荐纳为完成定义(OS 镜像可重现)| 编译器 + OS 联合 |
| 4 | sprint 3g `&mut + lifetime` 跟 Cap<T> 联动实现顺序 | 3g 主体 + 3g.5 phantom + 3g.7 联调 三段 | 编译器 agent |
| 5 | v3.x 后续(3h-3n)启动时机 | 跟 OS 实际用上时间对齐;M1 启动后立刻推 3g,M11 启动前推 3i+3j+3l | 编译器 + OS 联合 |
| 6 | v0.8 / v0.9 changelog 撰写 | v0.8 收尾写(commit 1-12 全记),v0.9 启动前 | 编译器 agent |

---

## § 16 实施路线图 — v0.8 wip → OS M11

> **目的**:把本 refactor 的 R-1~R-9 改动 + 后续 sprint 工作串成一条**从当前到 OS 真闭环**的完整路线图。每阶段给:**目标 / 做法 / 事实依据 / 跟 OS 接口**。
>
> **结构**: 7 个阶段(从 v0.8 wip → v3.1+),每阶段标"OS 对接"那一栏=这一阶段**完成时**能给 OS 端什么。

### § 16.1 阶段一览

```
v0.8 wip → v0.9.0 → v1.0.0 → v1.1.0 → v2.0.0 → v2.x → v3.0.0 → v3.1.0 → M1 → M10 → M11
[当前]    [近期]    [中期]    [中期]    [中期]    [中长]  [长]      [长]     [OS]   [OS]   [OS]
```

| 阶段 | 状态 | 关键交付 | OS 启动链路 |
|------|------|---------|------------|
| **v0.8 wip** | 当前,commit 12 收尾 | Stage 0 部分达成 + W-001~W-009 | 0 |
| **v0.9.0** | 近期 | W 真修 + main.c 翻译 + Stage 1 | 0 |
| **v1.0.0** | 中期 | Stage 2 / M4 真闭环(jhyy_1 跑 regress 持平) | 0 |
| **v1.1.0** | 中期 | spec 增补 + jhyy_helpers 清理 | 0 |
| **v2.0.0** | 中期 | `amd64_win_freestanding` target + 移除 QBE 工具链 | **0(为 M1 解锁编译能力)** |
| **v2.x** | 中长 | `amd64_sysv` + 多目标 + N 代 fixed point | 0 |
| **v3.0.0** | 长 | OS P0 6 特性(3a-3f) | **M1 启动可达** |
| **v3.1.0** | 长 | `&mut + lifetime` + Cap<T>(3g + 3g.5 + 3g.7) | **M4 启动可达** |
| **M1 启动** | OS | jhyy 编 kernel.efi → OVMF → printk | OS boot 链路第一站 |
| **M4 启动** | OS | capability 落地 + IPC 协议 | OS 微内核骨架 |
| **M11 启动** | OS | jhyy_OS 跑 jhyy 编译器 + 编 jhyy_OS | **自举 OS 真闭环** |

---

### § 16.2 v0.8 wip(当前,commit 12 收尾)

| 项 | 内容 |
|---|------|
| **目标** | 收尾 v0.8 wip;锁定 changelog;启动 v0.9 准备 |
| **做法** | 1. 写 v0.8.0 changelog 完整版(commit 1-12 全记) 2. 跑最后一次 regress.py 锁定"12 OK / 47 总"为 v0.8 baseline 3. 跟 OS 端 alignment coordination:确认"v1.0 closure 达成前 M1 不可启动" 4. 准备 v0.9 任务清单 |
| **事实依据** | commit 12 自测数据(§ 1.1.1 失败分类 + § 1.1.2 W 详情) |
| **OS 对接** | 0 — 编译器没真闭环,OS 不可启动 |
| **R 链接** | R-1(v0.8 任务清单收尾) |
| **完成定义** | v0.8.0 changelog 写完 + v0.8 wip branch 收尾(不再 commit) |

---

### § 16.3 v0.9.0(近期)

| 项 | 内容 |
|---|------|
| **目标** | W-001~W-009 全部真修 + main.c 翻译 + Stage 1 byte-equal 验证 |
| **做法** | **commit 1**: 29-extsw hypothesis 验证(grep `compiler/src0/arena.jhyy` 找 ptr 算术上下文,确认 i32/i64 误用范围;若 50/50 命中则修 arena.jhyy 而非 codegen) <br> **commit 2**: codegen bug 真修(逐个 W-001~W-009 真修 + 删 jhyy 端 workaround 注释 + 3 处 C 端 codegen.c 真改 + 必要时 jhyy_helpers.c 改) <br> **commit 3**: 翻译 main.c → main.jhyy(从旧 v0.8 任务清单 § commit 2 拿过来,523 行 C → jhyy;不重翻译 jhyy_helpers.c) <br> **commit 4**: Stage 1 byte-equal 验证(diff `jhyy_0.il` vs `jhyy_1.il` byte-equal)+ regress.py JHYY_CC 支持改(sprint 5 已规划) |
| **事实依据** | W-001~W-009 全部已知,逐个有 workaround + 触发场景(§ 1.1.2);main.c 翻译工作量在旧 v0.8 plan 已估;regress.py 改 JHYY_CC 是 sprint 5 已锁 |
| **OS 对接** | 0 — v0.9 仍是 C 端编译器阶段(OS 不可启动) |
| **R 链接** | R-1(新建 v0.9 任务清单)+ R-4(codegen 坑清单 + W-001~W-009 进 v1.0 详细方案) |
| **完成定义** | diff `jhyy_0.il` `jhyy_1.il` byte-equal(全 regress 43 + src0/ 自验文件)+ `JHYY_CC=jhyy_1 python regress.py` 持平(v0.8 baseline 12 OK) |

---

### § 16.4 v1.0.0(中期)

| 项 | 内容 |
|---|------|
| **目标** | Stage 2 / M4 真闭环 = jhyy_1 编 jhyy_1 跑 regress 全过(持平 v0.8 baseline) |
| **做法** | 1. 跑 v0.9 末 Stage 1 验证通过(§ 16.3 完成) 2. jhyy_1 编 jhyy_1 → jhyy_2,3 层自举验证(N=3 fixed point 局部) 3. regress.py 用 jhyy_1 跑 4. 写 v1.0.0 changelog 5. 标 v1.0.0 闭环 = "C 端编译器退役 + jhyy 编译器自举" |
| **事实依据** | v0.9 已完成 Stage 1;v1.0.0 任务清单 5 sprint 框架已锁;sprint 5 末做 M4 闭环(已规划) |
| **OS 对接** | 0 — jhyy 编译器能编 jhyy,但 jhyy 编译器还**不能编 OS**(缺 3a-3f 6 特性) |
| **R 链接** | R-3(v1.0 任务清单"不在范围"段重写)+ R-5(自举定义加 12 OK 持平) |
| **完成定义** | jhyy_1 编 jhyy_1 跑 regress 持平 + 3 层自举 N=3 fixed point + v1.0.0 changelog |

---

### § 16.5 v1.1.0(中期)

| 项 | 内容 |
|---|------|
| **目标** | spec 增补 + jhyy_helpers.c 清理 + 文档同步 |
| **做法** | 1. **lang-spec 增补**:§ 18 Cap<T> + § 19 unsafe_cap + § 20 Type-driven IPC + § 21 provenance(spec drafting,不动实现) <br> 2. **abi 增补**:§ 12 Cap wire format + cnode 引用布局 <br> 3. **jhyy_helpers.c 清理**:v0.9 末 + v1.0 期间累积的 bridge fn 评估;能砍的砍,能内联的内联 <br> 4. **v0.x 历史 sprint 文档归档**:v0.0~v0.7 任务清单 → `docs/logs/v0/`,L3 表格里只留 v0.6+ 已发版 <br> 5. v1.1.0 changelog + spec patch |
| **事实依据** | OS 端 coordination § 5 已列 spec 增补 backlog;jhyy_helpers.c 范围扩了 3 次(v0.8 commit 10 + commit 11 + commit 12)需要清理 |
| **OS 对接** | 0.5 — spec 增补锁 = v3.1 sprint 3g 启动的硬前置(spec 锁定才能实现)|
| **R 链接** | R-3 + R-4(v1.0 任务清单 / 详细方案 spec drafting 项) |
| **完成定义** | lang-spec § 18-21 全部起草完(50 行/节级别) + abi § 12 起草完 + jhyy_helpers.c 评估报告 |

---

### § 16.6 v2.0.0(中期)

| 项 | 内容 |
|---|------|
| **目标** | `amd64_win_freestanding` target + 移除 QBE 工具链依赖 |
| **做法** | 1. **多目标 codegen dispatcher**:`jhyy --target=amd64_win` / `amd64_win_freestanding` / `amd64_sysv` 切换 <br> 2. **`amd64_win_freestanding` target**:不 link ucrt / vcruntime,user 自己写 `_start`(kernel entry) <br> 3. **QBE 依赖评估**:QBE 还在(为 hosted Windows + SysV 用),但 freestanding target 也走 QBE(只是不 link libc) <br> 4. **测试**:jhyy 编 hello-freestanding.jhyy → kernel.efi → OVMF 跑通 printk(用 v3.0 sprint 3a-3f 之前,只用 QBE IL 标准 emit + no libc link 即可) <br> 5. v2.0.0 changelog |
| **事实依据** | OS 端 coordination § 3 锁 UEFI + PE/COFF;v2.x-qbe-rewrite.md 旧文"ELF multi-target 优先"是 v0.0 时期想象,OS 真走 PE/COFF,不需要 ELF |
| **OS 对接** | **1** — 编译器能给 OS 提供"编 UEFI PE/COFF kernel.efi + 不 link libc"的能力。这是 OS 启动链路**第一项解锁**(没有 v2.0,jhyy 编 jhyy_OS kernel.efi 必须 link ucrt,ucrt 调 OS 入口) |
| **R 链接** | R-6(v2.x 范围重写) + R-7(v2.0.0-os-prep 改完成定义视图) |
| **完成定义** | `jhyy --target=amd64_win_freestanding hello.jhyy -o hello.efi` 成功 + hello.efi 在 OVMF 跑通 + 不依赖 QBE 二进制(已 self-host) |

---

### § 16.7 v2.x(中长)

| 项 | 内容 |
|---|------|
| **目标** | `amd64_sysv` + 多目标 + N 代自举 fixed point(jhyy_2 == jhyy_3) |
| **做法** | 1. **自写 QBE 后端**:`amd64_codegen.jhyy`(IL → amd64 汇编)+ `regalloc.jhyy`(确定性寄存器分配)+ `peephole.jhyy`(确定性优化) <br> 2. **N 代 fixed point 验证**:jhyy_0 → jhyy_1 → jhyy_2 → jhyy_3 → ... → jhyy_N == jhyy_{N+1}(3 代最低) <br> 3. **`.exe byte-equal`**:`gcc -g0 + strip + SOURCE_DATE_EPOCH + --build-id=none` 达成(OS 镜像可重现) <br> 4. **多目标扩展**:`amd64_sysv` (Linux 引导 / 测试)+ `amd64_sysv_freestanding` (备用) <br> 5. **移除 QBE 工具链**:build.md 改"自写后端";"qbe.exe"绝对路径不再硬编码 |
| **事实依据** | v1.0 真闭环已达成;QBE 自写是 v2.x 主目标;多目标扩展按 OS 需求 |
| **OS 对接** | **1+** — 编译器自写 IL → .s(无 QBE 依赖) = OS 编 jhyy_OS 完全 self-contained |
| **R 链接** | R-6(范围重写) |
| **完成定义** | jhyy_2 == jhyy_3 byte-equal + 不依赖 QBE 工具链 + `jhyy --target=amd64_sysv hello.jhyy` 成功 |

---

### § 16.8 v3.0.0(长)

| 项 | 内容 |
|---|------|
| **目标** | OS P0 6 特性实现(sprint 3a-3f)= OS M1 启动可达 |
| **做法** | 按 v3.x-language-expansion.md 已重排的 sprint 顺序: <br> **3a inline asm**(OS P0-1,内核必须) <br> **3b `#[naked]` fn**(OS P0-2,boot/interrupt 必须) <br> **3c volatile load/store**(OS P0-3,MMIO 必须) <br> **3d `#[no_std]` + core**(OS P0-4,freestanding 必须) <br> **3e `#[link_section]`**(OS P0-5,boot 段必须) <br> **3f memory barrier**(OS P0-6,多核同步必须) <br> 每 sprint 末跑 OS 端 demo:`fn outb(port: u16, val: u8) { asm { "out %al, %dx" : : "d"(port), "a"(val) } }` 之类 |
| **事实依据** | OS 端 v0.0.2-foundation-revision.md § 4 M1 依赖图锁 + v0.0.1.5-M5b-prereqs.md § 1 启动硬条件;v3.x-language-expansion.md 3a-3f 已重排 |
| **OS 对接** | **2** — M1 启动可达(jhyy 编 kernel.efi → OVMF → printk)。3a-3f 全 6 特性完成是 M1 的硬前置 |
| **R 链接** | R-8(不变,已重排) |
| **完成定义** | 6 特性全部 spec 增补 + 实现 + 集成测试;demo 程序在 jhyy 上跑通 |

---

### § 16.9 v3.1.0(长)

| 项 | 内容 |
|---|------|
| **目标** | `&mut + lifetime` + Cap<T>(sprint 3g + 3g.5 + 3g.7)= OS M4 capability 启动可达 |
| **做法** | **3g 主体**:`&mut + lifetime` + Cap<T> 8 条编译期规则 + sema 实现(per v3.x-capability-spec.md § 8 条规则) <br> **3g.5 phantom 0 字节布局保证**:codegen + abi 锁定(8 字节 = cnode_idx+depth+rights,phantom 0 字节) <br> **3g.7 联调**:跟 jhyy_OS 内核实际 cap 表布局 byte-equal 验证 <br> 每 sprint 末跑 OS 端 demo:`let c: Cap<Page> = kernel_alloc_page();` 编通 |
| **事实依据** | OS 端 v0.0.2-foundation-revision.md § 4 M4 依赖图锁(3g+3g.5+3g.7);v3.x-capability-spec.md 8 条规则已锁;coordination.md § 2.1 Q-OS-001 已问 sprint 拆法 |
| **OS 对接** | **3** — M4 capability 启动可达。Cap<T> 在 jhyy 编译期能验证 = OS 微内核骨架可用 |
| **R 链接** | R-9(8 字节措辞补齐) |
| **完成定义** | 8 条编译期规则全部实现 + phantom 0 字节布局 + 跟 jhyy_OS cap 表 byte-equal 验证 |

---

### § 16.10 M1 → M10 → M11(OS 启动链路)

| Milestone | 状态 | 编译器侧硬前置 | OS 侧启动 |
|-----------|------|--------------|---------|
| **M1** kernel 启动(printk)| 🔒 依赖 v3.0 3a-3f | jhyy 编 kernel.efi → OVMF → printk |
| **M2** cooperative scheduler(单核)| M1 基础上 | 无新编译器特性 |
| **M3** syscall ABI | M1 + 3a(asm syscall)| jhyy 编 syscall handler 走 inline asm |
| **M4** capability 落地 | M3 + 3g + 3g.5 | jhyy 编 Cap<T> 程序 + sema 8 规则验证 |
| **M5a** design doc 锁 | 设计阶段 | 无 |
| **M5b** IPC 实现 | M4 基础上 | jhyy 编 IPC handler,Type-driven IPC 验证 |
| **M6** driver 框架 | M5b + 3a + 3c | jhyy 编字符设备 driver |
| **M7** 自研文件协议 | M6 基础上 | jhyy 编 FS(用 fixed array [u8; N],**不**用泛型) |
| **M8a** 早期 UI | M1 + UEFI GOP(3c) | jhyy 编 framebuffer 渲染 |
| **M8b** PCI + AHCI | M8a 基础上 | jhyy 编 driver |
| **M9** SMP(rendezvous)| M2 + 3f(memory barrier)| jhyy 编 per-CPU 数据 + barrier |
| **M10** riscv64 port | M9 基础上 | 等 v2.x / v3.x 末 aarch64/riscv64 target 实现 |
| **M11** 自举 OS 跑 jhyy 编译器 | M1-M10 + **3i generics + 3j closures + 3l std lib** | jhyy_OS 跑 jhyy 编译器 + 编 jhyy_OS kernel.efi |

**M11 是真自举 OS 闭环** = "jhyy 编 jhyy 编 jhyy 编 OS 跑 jhyy 编译器 编 jhyy_OS 编 jhyy" 链 = 整个项目最终目标(per v0.0.0-design.md § 1 使命)。

---

### § 16.11 阶段间接口(关键交接点)

| 上游阶段 | 给下游什么 | 下游怎么用 |
|---------|----------|-----------|
| v0.8 wip | v1.0 baseline(12 OK 持平) | v1.0 跑 regress 对比基线 |
| v0.9.0 | Stage 1 闭环(`.il byte-equal`)| v1.0 跑 3 层自举 |
| v1.0.0 | jhyy_1 跑 regress 持平 + C 端编译器退役 | v1.1 启动 spec 增补;v2.0 启动多目标 |
| v1.1.0 | lang-spec § 18-21 + abi § 12 锁定 | v3.1 sprint 3g 启动按 spec 实现 |
| v2.0.0 | `amd64_win_freestanding` target + 编 kernel.efi | OS 端 M1 启动链路第一项 |
| v2.x | 自写 IL → .s + 多目标 + N 代 fixed point | OS 端 OS 完全 self-contained 编 |
| v3.0.0 | sprint 3a-3f 6 特性 | OS 端 M1 启动(jhyy 编 kernel.efi → OVMF → printk) |
| v3.1.0 | `&mut + lifetime` + Cap<T> 8 规则 | OS 端 M4 启动(capability 落地) |
| OS M11 | jhyy_OS 跑 jhyy 编译器 编 jhyy_OS | **真自举 OS 闭环** |

---

### § 16.12 关键依赖链(visual)

```
v0.8 wip(当前)                    OS M1
    │                              ↑
    ↓                              │
v0.9.0(Stage 1)                    │
    │                              │
    ↓                              │
v1.0.0(M4 真闭环)                  │
    │                              │
    ↓                              │
v1.1.0(spec 增补)                  │
    │                              │
    ↓                              │
v2.0.0(amd64_win_freestanding) ──→ │  OS 编 kernel.efi 能力
    │                              │
    ↓                              │
v2.x(自写 IL→.s + N 代)            │
    │                              │
    ↓                              │
v3.0.0(OS P0 6 特 3a-3f) ──────→ M1 启动可达
    │                              │
    ↓                              │
v3.1.0(3g &mut+Cap<T>) ────────→ M4 capability 启动
    │                              │
    ↓                              │
v3.2+(3i generics) ──────────────→ M11 硬前置 1
    ↓                              │
v3.2+(3j closures) ──────────────→ M11 硬前置 2
    ↓                              │
v3.2+(3l std lib) ───────────────→ M11 硬前置 3
                                   ↓
                                  M11 真自举 OS 闭环
```

---

## § 17 关联文档

- [v0.x-c-compiler-roadmap.md](v0.x-c-compiler-roadmap.md) — R-2 改
- [v1.0-self-hosting.md](v1.0-self-hosting.md) — R-5 改
- [v2.x-qbe-rewrite.md](v2.x-qbe-rewrite.md) — R-6 改
- [v2.0.0-os-prep.md](../v2/v2.0.0-os-prep.md) — R-7 改
- [v3.x-language-expansion.md](v3.x-language-expansion.md) — R-8 不变
- [v3.x-capability-spec.md](v3.x-capability-spec.md) — R-9 改
- [architecture.md](../../internal/architecture.md) — 内部架构(本重构不改,但 cross-ref)
- [status.md](../../internal/status.md) — 当前状态(本重构不改,但 cross-ref)
- [workarounds.md](../../internal/workarounds.md) — W-001~W-009 现状(R-4 引用)
- [../../../../jhyy_OS/docs/coordination.md](../../../../jhyy_OS/docs/coordination.md) — 跨项目对齐
- [../../../../jhyy_OS/docs/v0.0.2-foundation-revision.md](../../../../jhyy_OS/docs/v0.0.2-foundation-revision.md) — OS 端 5 决策
- [../../../../jhyy_OS/docs/v0.0.1.5-M5b-prereqs.md](../../../../jhyy_OS/docs/v0.0.1.5-M5b-prereqs.md) — M5b 启动硬条件
