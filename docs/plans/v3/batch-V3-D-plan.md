# V3-D batch plan — v3.x 未完成工作盘点 (post-v3.1.0 ship 总览, 2026-09-06)

## Context

> **本文件目的**:盘点 v3 axis **未完成** 工作,作为后续 sprint 启动的总览。
> **不在范围**:已 ship sub-sprint 详情(V3-A v3.0.0 / V3-B v3.0.1..0.5 / V3-C v3.1.0)→ 看对应 batch plan + changelog。
> **权威源**: [`../roadmap/v3.x-language-expansion.md`](../roadmap/v3.x-language-expansion.md) (特性 backlog 唯一权威)+ [`../v2/v2.0.0-os-prep.md`](../v2/v2.0.0-os-prep.md) (OS M1-M11 硬前置)+ [`../roadmap/v2-v3-parallel-sprint-plan.md`](../roadmap/v2-v3-parallel-sprint-plan.md) (跨轴调度)。
> **版本号串约定**:本文件只用 `vX.Y.Z` 版本号引用 ship 节点,**不**用 commit hash(版本号已经是 ship 节点的稳定标识)。

### 已 ship (2026-09-06)

| Sprint | Tag | 内容 |
|--------|-----|------|
| V3-A v3.0.0 | `v3.0.0` | 3d `#[no_std]` 试水 ✅ ship |
| V3-B v3.0.1 | `v3.0.1` | 3a inline asm (QBE `.s` passthrough) ✅ ship |
| V3-B v3.0.2 | `v3.0.2` | 3b `#[naked]` (raw-asm escape hatch) ✅ ship |
| V3-B v3.0.3 | `v3.0.3` | 3c volatile type qualifier + V2-A `emit_volatile` ✅ ship |
| V3-B v3.0.4 | `v3.0.4` | 3e `#[link_section("name")]` + QBE .s post-walk ✅ ship |
| V3-B v3.0.5 | `v3.0.5` | 3f memory barrier `fence_seq_cst/acquire/release` ✅ ship |
| **V3-C v3.1.0** | **`v3.1.0`** | **3g `&T` / `&mut T` + NLL (stub) + `Cap<T>` 8-byte layout** ✅ ship |

> **关键观察**:V3-A + V3-B + V3-C v3.1.0 = **6 特性已 ship + 1 大特性(3g 主体)ship + 借用检查 stub**。**M1 launch 硬前置 5/6 完成**(3d 软),**M4 launch 硬前置 1/3 完成**(只 3g,3g.5 / 3g.7 待 ship)。

### 未完成工作分类(本文件主体)

| 类别 | Sprint / 路径 | OS 触发 / 优先级 |
|------|---------------|-----------------|
| **v3.1.1 (3g.5)** | PhantomData<T> ZST + Cap 组合 | **M4 launch 硬前置**,D27 串行锁,v3.1.0 ship 后启动 |
| **v3.1.2 (3g.7)** | CapTable<T> + 跨函数 cap pass | **M4 launch 硬前置**,D27 串行锁,v3.1.1 ship 后启动 |
| **v3.1.3 patch** | SysV abi_amd64_sysv.jhyy Cap<T> class backport | M4 launch 副作用,**V2-B v2.7.0 ship 后** backport |
| **v3.0 3c 移植**(跨轴) | v2.x 自写后端移植 volatile 语义(per `v2-v3-parallel-sprint-plan.md § 4.2`)| V2-A 后端 escape hatch,V2-C v2.8.0 之前 |
| **v3.2+ 3i (generics 单态化)** | generics 函数 / struct / enum + 单态化 | **M8d + M11 硬前置**,per D-GUI-11 2026-09-01 锁 |
| **v3.2+ 3j (closures)** | 闭包 = `{fn_ptr, captured_env}` + 合成函数 | **M8d + M11 硬前置**,per D-GUI-11 2026-09-01 锁,3i ship 后 |
| **v3.2+ 3l (std lib 4 子项)** | mem / fmt / string / arena / io / os / vec / map / math | **M11 硬前置**,3j ship 后启动(4 子项拆 3l.1 ~ 3l.4) |
| **v3.x 中 features** | 完整 NLL / 跨函数 borrow / lifetime 子类型 / variance / 完整 reborrow / 精确 escape analysis / `Cap<Cap<T>>` / `PhantomData<&T>` / CapTable 借用 / Cap 跨 volatile 借用 / ARM/RISC-V Cap<T> ABI | MVP 不依赖,留 v3.x 中 |
| **v3.x 末 features** | Polonius 完整 NLL / 完整 Lexical lifetimes / nested block borrow / 大端架构 swap / 多线程 cap | MVP 不依赖,留 v3.x 末 |
| **M5 boot-from-scratch** | 删 `src/*.c` + untrack QBE + 删 `runtime.c`(per `v1.x-phase-4-m5-boot-from-scratch.md`) | **独立 sprint**,v2.x 末 + v3.x 末后,user 2026-08-14 决定推迟 |

---

## 1. v3.1.1 (3g.5) — PhantomData<T> ZST codegen

### 1.1 状态

**未 ship**。D27 锁:**v3.1.0 ship 后启动**(已完成,2026-09-06 tag `v3.1.0`)。下一 sub-sprint = v3.1.1。

### 1.2 Scope(per [`batch-V3-C-plan.md` § v3.1.1](batch-V3-C-plan.md))

| 改动 | 文件 | 估算 |
|------|------|------|
| `PhantomData<T>` 类型识别 | `compiler/src0/parser.jhyy` parse_type | +30 行 |
| `PhantomData<T>` 不允许实例化(只能声明) | `compiler/src0/sema.jhyy` | +20 行 |
| `PhantomData<T>` 0 字节 layout(ZST),只占 type 表项 | `compiler/src0/codegen.jhyy` | +80 行 |
| struct 内 PhantomData 字段不 emit layout | `compiler/src0/codegen_amd64_emit_mem.jhyy` (V2-A 移植) | +20 行 |
| `Cap<PhantomData<X>>` 8 字节组合 | `compiler/src0/codegen.jhyy` | +40 行 |
| 测试:`sizeof(PhantomData<i32>) == 0` + `sizeof(Wrapper<i32>) == 8` | `tests/phantom_zst.jhyy` | ~30 行 + SKIP directive |
| 测试:`Cap<PhantomData<X>>` 8 字节验证 | `tests/cap_phantom_combo.jhyy` | ~30 行 + SKIP directive |
| lang-spec 增补(7-section 模板) | `docs/abis/jhyy-lang-spec-phantomdata-supplement-v3.1.1.md` | ~80 行 |
| umbrella changelog 段 append | `docs/logs/v3/changelog-v3.1.md` | ~15 行 |

### 1.3 关键决策

- **PhantomData 不允许实例化**:M0 简化;user 只能 `let x: PhantomData<T>;` 声明字段,不能 `let p = PhantomData<i32> {}`(防止误用)
- **PhantomData 在 struct 内不占 layout**:per Rust ZST 语义
- **不**支持 `PhantomData<&T>` 等 lifetime 参数(留 v3.x 中,见 § 4)
- **D27 锁:本 sub-sprint 必须在 v3.1.0 ship 后启动**(已满足)
- **worktree?** per 2026-09-06 user:"顺序做的后面不用开branch,就在v3主轴上修就行" → **不开新 worktree**,直接在 `axis-v3` 上 commit + tag `v3.1.1`

### 1.4 验收 / 5/5 ship gate

- `tests/phantom_zst.jhyy` 5/5 PASS(`sizeof(PhantomData<i32>) == 0 && sizeof(Wrapper<i32>) == 8`)
- `tests/cap_phantom_combo.jhyy` 5/5 PASS(`sizeof(Cap<PhantomData<X>>) == 8`)
- D43 re-baseline → **N7**(post-v3.1.1 merge,ZST 改 layout,极可能 .il 漂移)
- `regress.py --all` → 2/2 gated PASS,jhyy.exe 107/107 + 17 SKIP(原 104 + 3g cap_test + borrow_check_basic + phantom_zst = 107;SKIP +4 = 17)
- `jhyy_selfhost_check` → N6 → N7 byte-equal hold(per D43 阶段性 self-equal)

---

## 2. v3.1.2 (3g.7) — CapTable<T> + 跨函数 cap pass

### 2.1 状态

**未 ship**。D27 锁:**v3.1.1 ship 后启动**。

### 2.2 Scope(per [`batch-V3-C-plan.md` § v3.1.2](batch-V3-C-plan.md))

| 改动 | 文件 | 估算 |
|------|------|------|
| `CapTable<T>` builtin + `*Cap<T>` 裸指针类型 | `compiler/src0/parser.jhyy` | +30 行 |
| `CapTable<T>` 类型识别 + 字段访问 | `compiler/src0/sema.jhyy` | +50 行 |
| `CapTable<T>` layout:`*Cap<T>`(8B ptr)+ `len: i64`(8B)= 16B | `compiler/src0/codegen.jhyy` | +80 行 |
| 跨函数 `Cap<T>` cap pass 校验 | `compiler/src0/sema.jhyy` | +80 行 |
| `Cap<T>` 跨函数 call emit 走 64-bit register | `compiler/src0/codegen_amd64_emit_call.jhyy` | +30 行 |
| 测试:`CapTable<i32>` 创建 + 访问 + 跨函数 | `tests/cap_table_basic.jhyy` | ~50 行 + SKIP |
| 测试:跟 3g + 3g.5 联合验证 | `tests/cap_test_advanced.jhyy` | ~80 行 + SKIP |
| lang-spec 增补 | `docs/abis/jhyy-lang-spec-cap-table-supplement-v3.1.2.md` | ~120 行 |
| umbrella changelog 段 append | `docs/logs/v3/changelog-v3.1.md` | ~15 行 |

### 2.3 关键决策

- **CapTable<T> 用裸指针 + 长度**:per c-typedef 不借用(slice 借用由 user 自管;`Cap<T>` 本身不可变)
- **Cap<T> 跨函数 cap pass 校验**:不允许跨越 volatile 引用(借用 + volatile 互斥语义复杂,留 v3.x 中)
- **D27 锁:本 sub-sprint 必须在 v3.1.1 ship 后启动**
- **worktree?** per 2026-09-06 user 决定 → **不开新 worktree**,axis-v3 direct commit + tag `v3.1.2`
- **V2-C v2.8.0 触发**:v3.1.2 ship 后 V2-C v2.8.0 N 代 fixed point 才可启动(否则 N 代验算跑 `cap_test.jhyy` fail)

### 2.4 验收 / 5/5 ship gate

- `tests/cap_table_basic.jhyy` 5/5 PASS
- `tests/cap_test_advanced.jhyy` 5/5 PASS
- D43 re-baseline → **N8**(post-v3.1.2 merge,CapTable 改 codegen,极可能 .il 漂移)
- `regress.py --all` → 2/2 gated PASS,jhyy.exe 109/109 + 17 SKIP
- `jhyy_selfhost_check` → N7 → N8 byte-equal hold

### 2.5 跨 axis 通知

**v3.1.2 ship 后通知 user:V2-C v2.8.0 N 代 fixed point 可启动**(per [`../v2/batch-V2-C-plan.md`](../v2/batch-V2-C-plan.md) 跨 axis 硬前置)。

---

## 3. v3.1.3 patch — SysV abi_amd64_sysv.jhyy Cap<T> class backport

### 3.1 状态

**未 ship**,scope-deferred(per 2026-09-06 决策:V3-C 整 batch scope **Windows target only**)。

### 3.2 Scope

| 改动 | 文件 | 估算 |
|------|------|------|
| `abi_amd64_sysv.jhyy`: `Cap<T>` class = INTEGER(SysV 8-byte,占一个 reg) | `compiler/src0/abi_amd64_sysv.jhyy`(v2.7.0 创建 / 当时未填 Cap class) | +10 行 |
| 跨函数 `Cap<T>` 在 sysv target 上的 register 分配验证 | `tests/cap_test_sysv.jhyy`(新) | ~30 行 + SKIP |
| lang-spec 增补(SysV Cap<T> class 章节)| `docs/abis/jhyy-abi-v1.0.0.md § 13.x` | ~30 行 |
| umbrella changelog 段 append | `docs/logs/v3/changelog-v3.1.md` | ~10 行 |

### 3.3 关键决策

- **触发前置**:V2-B v2.7.0 (`abi_amd64_sysv.jhyy`) ship 后 backport(目前 v2.7.0 未 ship,等 V2-B 启动)
- **不在 v3.1.2 scope**(per 2026-09-06 决策:Windows-only scope 优先 ship)
- **worktree?** per 2026-09-06 user → **不开新 worktree**,axis-v3 direct commit + tag `v3.1.3`
- **命名冲突**:本 patch 用 `v3.1.3` 而非 `v3.1.2-patch`,因 v3.1.2 已 ship tag;**不**遵循 feedback `feedback_changelog_umbrella` 的"vX.Y axis 只 1 个 umbrella changelog,无 standalone patch changelog"(本 patch 只往 `changelog-v3.1.md` append 段,**不**新建 standalone file)

### 3.4 验收 / 5/5 ship gate

- `tests/cap_test_sysv.jhyy` 5/5 PASS(走 `--target=amd64_sysv`)
- D43 re-baseline → **N9**(SysV Cap<T> 改 abi,可能漂移)
- `regress.py --all` → 2/2 gated PASS(109/109 + 17 SKIP 不变)
- `jhyy_selfhost_check` → N8 → N9 byte-equal hold

---

## 4. v3.x 中 features — 完整 lifetime / borrow / Cap 扩展

### 4.1 范围(per [`v3.x-language-expansion.md § 3g.5/3g.7`](../roadmap/v3.x-language-expansion.md) + batch-V3-C-plan.md "Out of scope")

| 特性 | 描述 | 优先级 | OS 触发 |
|------|------|--------|---------|
| **完整 NLL (Polonius)** | path-based NLL2,精确到 control flow graph | 低(MVP 不依赖)| 留 v3.x 末 |
| **跨函数 borrow** | 函数签名支持 lifetime 标注,跨调用边界推断 | 中(OS 复杂模块需要)| M11 launch 之后 |
| **lifetime 子类型 / variance** | `'a: 'b` 标注 + covariance/contravariance 规则 | 中 | M11 之后 |
| **完整 reborrow `&mut *x`** | expression 位置允许 `&mut *x` 创建 reborrow | 中(M4 后 OS 真实场景)| M4 后 |
| **精确 escape analysis** | 数据流分析 + 借用变量可走 register(不再 stack-only)| 中 | 性能优化 |
| **`Cap<Cap<T>>` 嵌套** | 嵌套 Cap 仍 8 字节 | 中 | OS 复杂 cap 场景 |
| **`PhantomData<&T>` lifetime 参数** | phantom 携带 lifetime | 中 | OS 复杂场景 |
| **CapTable 借用语义** | CapTable 切借用代替裸指针 | 低 | 优化 |
| **Cap<T> 跨 volatile 引用** | 借用 + volatile 互斥解锁 | 低 | OS 罕见 |
| **全 C11 / Rust memory model** | 完整内存顺序保证 | 低 | OS SMP 后 |
| **ARM / RISC-V Cap<T> ABI** | 多架构 Cap<T> layout 8 字节保证 | 中 | M11 launch 时(per `v2.0.0-os-prep.md § 1 M10 riscv64 port`)|

### 4.2 启动时机

- **MVP(M1-M10)不依赖**这些(per [`v2.0.0-os-prep.md § 1`](#) D28)
- **OS 真实场景驱动**:M4 launch 后 OS 端遇到 lifecycle 需求时回头补
- **本类不单独 batch**:作为 patch 进 `v3.1.x`(如 `v3.1.4` = 完整 reborrow + 精确 escape analysis)或 `v3.3.x`(大特性如 Polonius 完整 NLL)

---

## 5. v3.x 末 features — 长期 language maturity

### 5.1 范围

| 特性 | 描述 | 优先级 |
|------|------|--------|
| **Polonius 完整 NLL** | path-based NLL2,完整 Rust-style borrow checker | 留 v3.x 末(替代 NLL stub)|
| **完整 Lexical lifetimes** | 替代简化版 NLL | 同上 |
| **nested block 借用作用域** | 精细化借用 scope 嵌套 | 留 v3.x 末 |
| **大端架构 swap** | aarch64_be / riscv64 / ppc64 big-endian | 留 v3.x 末(per D10 末)|
| **多线程 cap (per-CPU)** | M9 SMP 后多线程 cap 安全 | 留 v4.x(per D28 表)|

### 5.2 启动时机

- **M11 launch 后**才有用(自举 OS 真闭环时 jhyy 编译器需要完整 borrow check + 跨函数 lifetime)
- **不是 MVP 硬前置**(per D28)
- **本类单独 batch**:留 `v3.5.0` 或 `v4.0.0` 大特性

---

## 6. v3.2+ 3i + 3j + 3l — M8d + M11 硬前置

> **D-GUI-11 锁**(2026-09-01):3i + 3j 从 "M11 硬前置" **升级** 为 "M8d + M11 硬前置"。compositor surface / buffer / seat interface 需 generic over T;seat focus callback 是闭包式 — M8d 早于 M11 启动。

### 6.1 v3.2 3i — generics (单态化)

#### 状态
**未 ship**。`v3.x-language-expansion.md § Sprint 3i` 已写设计草案,**未**写 L3 + L4 doc。

#### Scope(草案)
| 改动 | 文件 | 估算 |
|------|------|------|
| 语法:`fn name<T, U>(...)` + `name::<T>(args)` | `compiler/src0/parser.jhyy` | ~80 行 |
| 泛型参数挂在函数/struct/enum 节点 | `compiler/src0/ast.jhyy` | ~40 行 |
| 调用处收集具体类型 + 单态化 pass(sema 之后 / codegen 之前)| `compiler/src0/monomorphize.jhyy`(新)| ~300 行 |
| 单态化后类型检查 | `compiler/src0/sema.jhyy` (复跑) | ~150 行 |
| 测试:泛型函数 + struct + enum + 多类型参数 | `tests/generics_basic.jhyy` 等 | ~200 行 + SKIP |
| lang-spec 增补 | `docs/abis/jhyy-lang-spec-generics-supplement-v3.2.0.md` | ~250 行 |

#### 关键决策
- **M0 简化:不做 lifetime 泛型参数**(泛型 + lifetime 留 v3.x 中)
- **M0 简化:不做 const generic**(`const N: usize` 等,留 v4.x)
- **worktree?** per 2026-09-06 user → **不开新 worktree**(user "顺序做的后面不用开branch"),axis-v3 direct commit + tag `v3.2.0`
- **3j 紧随其后**:3j closures 内部依赖 3i generics(closure env 用 generic struct),per D28 顺序

#### 验收 / 5/5 ship gate
- 5+ 泛型测试 5/5 PASS
- `tests/std_lib_vec_pre.jhyy`(jhyy 自身源准备用 `Vec<T>`)跑通(集成)
- D43 re-baseline → **N10**(泛型改 codegen,极可能漂移)
- `regress.py --all` → 2/2 gated PASS

### 6.2 v3.2 3j — closures

#### 状态
**未 ship**。`v3.x-language-expansion.md § Sprint 3j` 已写设计草案。

#### Scope(草案)
| 改动 | 文件 | 估算 |
|------|------|------|
| 闭包语法 `|x: i32| { ... }` | `compiler/src0/parser.jhyy` | ~80 行 |
| 闭包 = `{fn_ptr, captured_env}` + 合成函数 `__closure_N(env, ...)` | `compiler/src0/codegen.jhyy` | ~250 行 |
| 按值捕获 + 多变量捕获 | `compiler/src0/sema.jhyy`(capture analysis)| ~150 行 |
| 测试:基本闭包 + 多变量捕获 + 闭包作参数/返回值 | `tests/closures_basic.jhyy` 等 | ~150 行 + SKIP |
| lang-spec 增补 | `docs/abis/jhyy-lang-spec-closures-supplement-v3.2.1.md` | ~200 行 |

#### 关键决策
- **M0 简化:闭包按值捕获**,不做 `move` 关键字
- **M0 简化:闭包不能捕获借用**(借用捕获留 v3.x 中)
- **worktree?** → axis-v3 direct commit + tag `v3.2.1`
- **3l 紧随其后**:std lib 依赖 generics + closures

#### 验收 / 5/5 ship gate
- 3+ 闭包测试 5/5 PASS
- D43 re-baseline → **N11**
- `regress.py --all` → 2/2 gated PASS

### 6.3 v3.2 3l — std lib (4 子项)

#### 状态
**未 ship**。`v3.x-language-expansion.md § Sprint 3l.1 ~ 3l.4` 已写设计草案(2026-09-01 拆分 4 子项)。

#### Scope(草案,4 子项拆 4 sprint)

**3l.1 标准库基础**(per design § 3l.1):

| 模块 | 功能 | 备注 |
|------|------|------|
| `mem.jhyy` | memcpy / memcmp / memset | 纯 jhyy,无泛型 |
| `fmt.jhyy` | 格式化字符串(自实现) | 替代 v1.0.0 编译器的 C 运行时 printf |
| `string.jhyy` | 字符串操作(拼接 / 查找 / 比较 / 切片)| 替代 v1.0.0 编译器的 C 运行时 string |
| `arena.jhyy` | Arena allocator(从 v0.x C 移植到纯 jhyy)| 编译器自身用 |

**3l.2 标准库 IO**:

| 模块 | 功能 |
|------|------|
| `io.jhyy` | 文件读写,stdin / stdout / stderr |
| `os.jhyy` | 系统调用包装(open / read / write / exit / getenv)|

**3l.3 标准库泛型容器**(需 3i generics):

| 模块 | 功能 |
|------|------|
| `vec.jhyy` | 泛型动态数组 `Vec<T>` |
| `map.jhyy` | 泛型哈希表 `Map<K, V>`(hash 函数用 `string.jhyy`)|

**3l.4 标准库数学**(需 3h 浮点):

| 模块 | 功能 |
|------|------|
| `math.jhyy` | 数学函数(sin / cos / sqrt / pow — FFI libm)|

#### 关键决策
- **4 子项 4 sprint**(per 2026-09-01 拆分):每个 sub-sprint 1 tag(v3.2.2 = 3l.1, v3.2.3 = 3l.2, v3.2.4 = 3l.3, v3.2.5 = 3l.4)
- **3l.3 依赖 3i generics ship**(已写 M11 硬前置)
- **3l.4 依赖 3h 浮点 ship**(未 ship,见 § 7)
- **3l.1 不依赖 generics / closures**(3l.1 基础 mem / fmt / string / arena 走 v3.2.1 closures 后即可)
- **jhyy 编译器自身迁移**:3l.3 ship 后 jhyy lexer/parser 用 `Vec<T>` 替代 `[T; N]` 固定数组(per `v3.x-language-expansion.md § 3l.3`)
- **worktree?** → axis-v3 direct commit(per user 2026-09-06 决定),4 sub-sprint 顺序 ship

#### 验收 / 5/5 ship gate
- 每个模块有源码 + 文档 + 单元测试
- `arena.jhyy` byte-equal 或接口兼容 v0.x C 版 arena(per D22)
- jhyy 编译器自身用 `string.jhyy` + `fmt.jhyy` 替换原 C FFI 字符串操作
- D43 阶段性 self-equal hold

### 6.4 v3.2 总览 — 汇合点 M8d + M11

```
v3.2.0 (3i generics) → v3.2.1 (3j closures) → v3.2.2 (3l.1 mem/fmt/string/arena)
                                                    ↓
                                                  v3.2.3 (3l.2 io/os) → v3.2.4 (3l.3 vec/map) → v3.2.5 (3l.4 math)
                                                                              ↑ 需 3i ship ↑
                                                                                            ↑ 需 3h 浮点 ↑
```

**M8d launch 触发**:v3.2.0 + v3.2.1 ship 后(per D-GUI-11)
**M11 launch 触发**:v3.2.0 + v3.2.1 + v3.2.2 + v3.2.3 + v3.2.4 + v3.2.5 + V2-A + V2-B + V2-C 全 ship(per D28)

---

## 7. v3.x 中 features — 语言成熟化(per `v3.x-language-expansion.md § 3h ~ 3n`)

### 7.1 状态

| Sprint | 状态 | 触发 |
|--------|------|------|
| **3h 浮点类型** | **未 ship**(MVP 不依赖,per D28)| 3l.4 浮点 math 需先 ship |
| 3k 错误恢复 | 未 ship | UX,MVP 不依赖 |
| 3m 基本优化 pass | 未 ship | 自举后性能,3l.4 后推 |
| 3n 包管理器 | 未 ship | UX,M11 之后 |

### 7.2 关键决策

- **3h 浮点**:**MVP 不依赖**,但 3l.4 math 需 3h ship → 建议 3l.4 ship 前先做 3h(避免 math 缺前置)
- **3k 错误恢复**:UX 改进,**不阻塞 MVP**;建议 M11 后做
- **3m 基本优化 pass**:自举后性能,常量化简 + 死代码消除;不破坏 byte-equal(per D43 阶段性 self-equal)
- **3n 包管理器**:M11 之后,跟 OS 启动无关

### 7.3 worktree?

**不开新 worktree**(per 2026-09-06 user 决定),axis-v3 direct commit。

---

## 8. v3.x 末 features — 长期 language maturity

### 8.1 范围

| 特性 | 描述 |
|------|------|
| **Polonius 完整 NLL** | path-based NLL2,完整 Rust-style borrow checker |
| **完整 Lexical lifetimes** | 替代 NLL stub |
| **nested block 借用作用域** | 精细化借用 scope 嵌套 |
| **大端架构 swap** | aarch64_be / riscv64_be / ppc64_be |
| **多线程 cap (per-CPU)** | M9 SMP 后多线程 cap 安全 |

### 8.2 启动时机

- **M11 launch 后**才有真实需求
- **不是 MVP 硬前置**
- **本类单独 batch**:留 `v3.5.0` 或 `v4.0.0` 大特性

---

## 9. M5 boot-from-scratch — 独立 sprint

### 9.1 状态

**未 ship**(per [`v1.x-phase-4-m5-boot-from-scratch.md`](../roadmap/v1.x-phase-4-m5-boot-from-scratch.md) 推迟决策,2026-08-14 user 决定)。

### 9.2 Scope

| 动作 | 文件 | 估算 |
|------|------|------|
| 删 `compiler/src/*.c` + `compiler/src/*.h` | git rm | (一次性 ~50 文件)|
| untrack QBE `compiler/qbe/`(去掉 submodule / git rm)| git rm | (一次性 ~30 文件)|
| 删 `compiler/runtime/runtime.c` | git rm | (1 文件)|
| v3.x 末 runtime 重写(`compiler/runtime/core.jhyy` etc.)| jhyy-side 重写 | 单独 sprint |
| 全栈迁移验证:`jhyy_v1.exe.exe`(v1 baseline frozen)→ 编 jhyy 自身 → 编 OS code → jhyy_OS 启动 | 集成测试 | (per `v1.x-phase-4-m5-boot-from-scratch.md`)|

### 9.3 关键决策

- **触发前置**:**v2.x 末**(QBE 完全移除,per `batch-V2-C-plan.md`)+ **v3.x 末**(runtime 重写,jhyy-side 替代 `runtime.c`)
- **不是 MVP 硬前置**;**M5 是 v1.x 末 Phase 4 单独 sprint**(per `v1.x-phase-4-m5-boot-from-scratch.md`)
- **不**在 v3 axis 内,留 axis-v3 末或独立 axis

### 9.4 worktree?

per 2026-09-06 user 决定 → **不开新 worktree**(顺序做的),axis-v3 末 direct commit。

---

## 10. 跨 axis 触发 / 通知

### 10.1 V3 axis → V2 axis 触发

| V3 ship | 触发 V2 |
|---------|---------|
| **v3.0.3 (3c volatile)** ✅ ship | V2-B v2.7.0 sysv target 启动(per `v2-v3-parallel-sprint-plan.md § 4.2` 硬约束:3c ship 后才能移植 volatile 语义)|
| **v3.1.0 (3g)** ✅ ship | V2-A `codegen_amd64.jhyy` 后续移植借用保留语义(regalloc 启发式需兼顾借用)|
| **v3.1.2 (3g.7)** 待 ship | **V2-C v2.8.0 N 代 fixed point 启动**(per `batch-V2-C-plan.md` 跨 axis 硬前置)|
| **v3.1.3 patch** 待 ship | V2-B v2.7.0 ship 后 backport(`abi_amd64_sysv.jhyy` Cap<T> class)|

### 10.2 V2 axis → V3 axis 触发

| V2 ship | 触发 V3 |
|---------|---------|
| V2-B v2.7.0 sysv target ship | V3 v3.1.3 patch backport(SysV Cap<T> class)|
| V2-C v2.8.0 N 代 fixed point ship | V3 v3.x 末 Polonius / 完整 NLL 启动 |

### 10.3 V3 axis → OS 端 触发

| V3 ship | 触发 OS |
|---------|---------|
| V3-A v3.0.0 (3d no_std) ✅ ship | M1 launch 不依赖(软,per D10)|
| V3-B v3.0.1..0.5 (3a/3b/3c/3e/3f) ✅ ship | **M1 launch 可启动**(per `v2.0.0-os-prep.md § 1`)|
| V3-C v3.1.0 (3g) ✅ ship | M4 launch 1/3 前置达成 |
| V3-C v3.1.1 (3g.5) 待 ship | M4 launch 2/3 前置达成 |
| V3-C v3.1.2 (3g.7) 待 ship | **M4 launch 可启动**(per `v2.0.0-os-prep.md § 1 M4`)|
| V3 v3.2.0..0.1 (3i + 3j) | **M8d launch 可启动**(per D-GUI-11)|
| V3 v3.2.2..0.5 (3l.1..3l.4) | **M11 launch 可启动**(per `v2.0.0-os-prep.md § 1 M11`)|

---

## 11. 节奏建议(per 2026-09-01 user 决定 + 2026-09-06 user 决定)

### 11.1 双 sprint 切换

- **V3 axis 内顺序推进**(per 2026-09-06 user:"顺序做的后面不用开branch,就在v3主轴上修就行"):
  - 后续 sub-sprint(v3.1.1 / v3.1.2 / v3.1.3 / v3.2.x / 3h)直接在 `axis-v3` commit,**不**开新 worktree
  - 不开 PR,axis-v3 long-lived integration branch 直接 merge
  - commit-on-axis-v3 → tag → push → 准备下一 sub-sprint
- **跨 axis 异步并行**:
  - V2 axis(V2-B v2.7.0 sysv + V2-C v2.8.0 N 代 fixed point)跟 V3 axis 各线独立推进
  - V2 axis V2-B v2.7.0 启动需要 V3-B v3.0.3 (3c) ship(已 ship) + V3 v3.1.3 patch backport(等 V2-B 启动)
  - V2-C v2.8.0 启动需要 V3 v3.1.2 ship(待 ship)

### 11.2 sub-sprint 启动顺序

```
当前 (2026-09-06)
  ↓
[v3.1.1 (3g.5) PhantomData] → tag v3.1.1
  ↓ D27 锁
[v3.1.2 (3g.7) CapTable + cap pass] → tag v3.1.2
  ↓ 通知 V2 axis: V2-C v2.8.0 可启动
[v3.1.3 patch (SysV Cap<T> class backport)] → 等 V2-B v2.7.0 ship 后启动 → tag v3.1.3
  ↓
[v3.2.0 (3i generics)] → tag v3.2.0
  ↓
[v3.2.1 (3j closures)] → tag v3.2.1
  ↓ 通知 M8d launch 可启动
[v3.2.2 (3l.1 mem/fmt/string/arena)] → tag v3.2.2
  ↓
[v3.2.3 (3l.2 io/os)] → tag v3.2.3
  ↓
[v3.2.4 (3l.3 vec/map)] → tag v3.2.4 (需 3i ship ✅)
  ↓
[v3.2.5 (3l.4 math)] → tag v3.2.5 (需 3h ship)
  ↓ 通知 M11 launch 可启动(等 V2 axis V2-C ship)
[v3.x 中 features] (完整 reborrow / 精确 escape analysis / Cap<Cap<T>> / PhantomData<&T> / CapTable 借用 / 多架构 Cap<T> ABI)
  ↓
[v3.x 末 features] (Polonius 完整 NLL / 完整 Lexical lifetimes / 大端架构)
  ↓
[M5 boot-from-scratch] 独立 sprint
```

### 11.3 worktree + branch 路径

```
C:\Users\liuzhen\Desktop\coding\JiHuiYiYou-axis-v3                              (parent, integration — 不开新 worktree)
```

per 2026-09-06 user:"顺序做的后面不用开branch,就在v3主轴上修就行" → **本批次不开新 worktree**;后续 v3.1.1 / v3.1.2 / v3.1.3 patch 直接在 axis-v3 commit + tag。

> **例外**:若 V3 跟 V2 axis 后续出现 file 层冲突(罕见,因 V2 改 codegen_amd64.jhyy,V3 改 parser/sema/codegen.jhyy 主体)+ V3 期间 OS 端需紧急 patch → 临时开 worktree,user 决定。

---

## 12. Out of scope(本文件不涉及)

- **已 ship 详情** → V3-A / V3-B / V3-C 各自 batch plan + changelog
- **v2 axis 未 ship 详情** → [`../v2/batch-V2-B-plan.md`](../v2/batch-V2-B-plan.md) + [`../v2/batch-V2-C-plan.md`](../v2/batch-V2-C-plan.md)
- **OS 端启动链路** → [`../../../jhyy_OS/docs/coordination.md`](../../../jhyy_OS/docs/coordination.md) § 0 Critical Path
- **跨边界 Q / UD / D 决策** → [`../../../jhyy_OS/docs/coordination.md`](../../../jhyy_OS/docs/coordination.md) § 2-3
- **M5 boot-from-scratch 详情** → [`../roadmap/v1.x-phase-4-m5-boot-from-scratch.md`](../roadmap/v1.x-phase-4-m5-boot-from-scratch.md)

---

## 13. Cross-reference

| 文档 | 关系 |
|------|------|
| [`v3.x-language-expansion.md`](../roadmap/v3.x-language-expansion.md) | v3.x 特性 backlog 唯一权威 |
| [`v2.0.0-os-prep.md`](../v2/v2.0.0-os-prep.md) | OS M1-M11 硬前置 |
| [`v2-v3-parallel-sprint-plan.md`](../roadmap/v2-v3-parallel-sprint-plan.md) | 跨轴调度 + § 4 硬约束(D42 / 3c / D27 / D43)+ § 6 Branch 操作约定(axis-v2 + axis-v3 并行)|
| [`batch-V3-A-plan.md`](batch-V3-A-plan.md) | V3-A v3.0.0 3d `#[no_std]` 试水 ✅ ship |
| [`batch-V3-B-plan.md`](batch-V3-B-plan.md) | V3-B v3.0.1..0.5 = 3a/3b/3c/3e/3f ✅ ship |
| [`batch-V3-C-plan.md`](batch-V3-C-plan.md) | V3-C v3.1.0..v3.1.2 = 3g + 3g.5 + 3g.7(v3.1.0 ✅ / v3.1.1 + v3.1.2 待 ship)|
| [`batch-V2-A-plan.md`](../v2/batch-V2-A-plan.md) | V2-A v2.5.0 amd64 自写后端起步 ✅ ship |
| [`batch-V2-B-plan.md`](../v2/batch-V2-B-plan.md) | V2-B v2.6.0 + v2.7.0 regalloc + peephole + sysv target(未 ship)|
| [`batch-V2-C-plan.md`](../v2/batch-V2-C-plan.md) | V2-C v2.8.0 N 代 fixed point + QBE 移除(未 ship;触发前置 = V3-C ship)|
| [`v1.x-phase-4-m5-boot-from-scratch.md`](../roadmap/v1.x-phase-4-m5-boot-from-scratch.md) | M5 推迟决策(2026-08-14)|
| [`../../../jhyy_OS/docs/coordination.md`](../../../jhyy_OS/docs/coordination.md) | 跨项目对齐(D-GUI-11 3i+3j 升级 / D-GUI-12 MS x64 syscall / D42 3a 路径 / D27 3g 串行 / D43 阶段性 self-equal)|

---

## 14. Open questions(等 user 决定启动顺序)

| # | 问题 | 建议 |
|---|------|------|
| 1 | v3.1.1 (3g.5) 启动时点 | 立即(2026-09-06 后 D27 锁已解锁,v3.1.0 ship 完成)|
| 2 | v3.1.2 (3g.7) 启动时点 | v3.1.1 ship 后立即(D27 锁) |
| 3 | v3.1.3 patch 启动时点 | 等 V2-B v2.7.0 ship 后(触发前置)|
| 4 | 3h 浮点启动时点 | 3l.4 math 启动前(避免 3l.4 缺前置) |
| 5 | 3i + 3j 启动时点 | D-GUI-11 M8d 硬前置;M8d 启动需求驱动(2026-09-01 OS 升)|
| 6 | 3l.1 ~ 3l.4 启动时点 | 3j ship 后顺序 ship;M11 硬前置 |
| 7 | v3.x 中 features 启动时点 | OS 真实场景驱动(M4 后 OS 端遇到 lifecycle 需求时回头补)|
| 8 | v3.x 末 features 启动时点 | M11 launch 后才有真实需求 |
| 9 | M5 boot-from-sprint 启动时点 | v2.x 末(V2-C v2.8.0 ship)+ v3.x 末 runtime 重写 ship 后 |
