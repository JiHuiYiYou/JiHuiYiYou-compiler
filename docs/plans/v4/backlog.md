# v4.x Backlog — 未启动的 12 项(2026-10-15 合并)

> ## ⚠️ 优先级:低
>
> **本文档不是当前工作项。** 当前唯一进行中的计划是
> [`active-workaround-clearance.md`](active-workaround-clearance.md)
> (6 处活 workaround 真修,per 2026-10-10 user 决定「必须在 v4 正式版清零,
> 大不了 v4 不发」)。
>
> 下面这 12 项**全部未启动**,且没有一项在阻塞 v4.0.0 final tag。
> 它们的原版本号(`v4.1.0` … `v4.12.0`)已作废 —— 见文末「关于版本号」。

**合并来源(2026-10-15):** `v4.1.0-plan.md` … `v4.12.0-plan.md` 共 12 份。
每份的 Scope 表 / 关键决策 / 验收 gate / 风险 / Out of scope 内容已全部保留,
只压缩了逐份重复的样板(Worktree 约定、Commit 节奏模板)。

**统一约定(原 12 份逐份重复,现声明一次):**
- Worktree:v4.x 主轴在 `main` 上直接 commit + tag,**不开新 worktree**
  (per 2026-09-06 user)
- 依赖编排按依赖图决定并行 / 串行,**不预设「单线串行」元规则**
  (per `feedback_no_blind_serial_rule`)

---

## 总览

| # | 项 | Scope | 改动量估算 | 强前置 | D43 目标 | 能否并行 |
|---|-----|-------|-----------|--------|-----------|---------|
| 1 | **M5 工具链闭环** | 删 `src/*.c` + untrack QBE + 删 `runtime.c` | ~5000+ 行删除 | v4.0 | — | 串行起点 |
| 2 | **async/await + Future runtime** | 语法 + state machine codegen + executor | ~1130 行 | 1, 3i, 3j | N17 | 独立 |
| 3 | **lifetime + Polonius borrow check** | lifetime 语法 + 子类型 + Polonius | ~1050 行 | 1, 3g stub | N18 | 串行链起点 |
| 4 | **closure 增强** | move / borrow capture / generic / trait object | ~700 行 | 3, 3i, 3j | N19 | 串行 |
| 5 | **const generic** | `const N` 泛型 + 单态化求值 | ~320 行 | 3i | N20 | 独立 |
| 6 | **trait objects (dyn Trait)** | trait/impl + vtable + 动态分发 | ~730 行 | 4, 3i | N21 | 串行 |
| 7 | **错误恢复** | parser/sema 多错误 + diag 聚合 + caret | ~580 行 | v4.0 | N22 | 独立 |
| 8 | **基本优化 pass** | 常量折叠 / 代数化简 / DCE | ~500 行 | 1 | N23 | 独立 |
| 9 | **包管理器** | `jhyy new/build/test` + manifest + 依赖 | ~780 行 | 3l.1, 3l.2 | N24 | 独立 |
| 10 | **HKT + specialization** | 一阶 `F<*>` + 单层 impl 覆盖 | ~530 行 | 5, 6 | N25 | 串行 |
| 11 | **并发 cap + 完整 memory model** | C11/Rust memory model + 多架构 Cap ABI | ~1950 行 | 3g, 3c, 3f | N26 | 独立 |
| 12 | **`.jhyynb` binary format** | DWARF emitter + section builder + `jhyy-inspect` | ~1800 行 | 1 | N27 | 独立 |

**依赖图:**

```
M5 ──┬─→ async ────────────────────────────────┐
     ├─→ lifetime/Polonius ─→ closure ─→ dyn Trait ─→ HKT ─┐
     ├─→ 优化 pass ──────────────────────────────┤         │
     ├─→ .jhyynb ───────────────────────────────┤         │
     └──────────────────────────────────────────┴─────────┘
const generic ──────────────────────────────→ HKT
错误恢复   (独立,无 v4.x 内前置)
包管理器   (独立,无 v4.x 内前置)
并发 cap   (独立,无 v4.x 内前置,M11 launch 之后)
```

**强串行链:** `lifetime → closure → dyn Trait → HKT`(每一步都是下一步的输入)
**可并行:** async / 错误恢复 / 优化 / 包管理 / 并发 cap / .jhyynb

---

## 1. M5 工具链闭环(原 `v4.1.0-plan.md`)

**M5 deferral 历史:** 2026-08-14 user 决定 v1.5 installer ship 不触发 M5;
原计划「v2/v3 后 sprint」于 2026-09-06 升级为 v4.x sprint。

| Part | 内容 | 文件 |
|------|------|------|
| 1 | 删 `compiler/src/*.c`(C 端编译器,~5000+ 行) | `git rm -r compiler/src/` |
| 2 | Untrack QBE 源码 + binary | `compiler/qbe/` + `compiler/build/bin/qbe.exe` |
| 3 | 删 `compiler/runtime/runtime.c` + C runtime helpers | 替换为 `std/*.jhyy` + `unsafe` + FFI |
| 4 | 工具链自含闭环验证 | `build-jhyy.sh` / `build.md` / `architecture.md` |

**关键决策:** M5 是「删除」而非「重写」—— 实现代码已迁到 jhyy(std lib)或自写后端,
M5 只删遗留 C。工具链仍依赖 MinGW `as` + `gcc`,**不**重打包 MSYS2。

**验收 gate:** `compiler/` 下 `\.c$` grep 0 hit · `jhyy 编 jhyy` 全闭环 byte-equal ·
`tools/check_dangling.py` 0 dangling · procmon 验证不 spawn `qbe.exe` + 不 link `runtime.c`

**风险:** 删 `compiler/src/*.c` 触发 build 崩溃 → 先 `make -n` dry-run + 保留 1 commit 恢复能力 ·
删 `runtime.c` 触发 std lib 漏覆盖 → regress + std lib test 全过,fail 时 hotfix 进 patch ·
byte-equal fail → revert 删 C action,逐文件删逐步验算

> ⚠️ **本文档修正(2026-10-15):** Part 2「untrack QBE」已经过时 —— QBE 已
> `6ae2d7c` git rm(v3.1.0)。Part 1/Part 3 仍有效。
> ⚠️ Part 3 与 [`active-workaround-clearance.md` W-103](active-workaround-clearance.md)
> 存在方向张力:W-103 要往 `jhyy_helpers.c` 加 5 个 C bridge,而 M5 Part 3 要删 C runtime。
> 两者的取舍需要 user 拍板。

---

## 2. async/await + Future runtime(原 `v4.2.0-plan.md`)

| 改动 | 文件 | 估算 |
|------|------|------|
| async fn 语法 + `.await` 表达式 | `parser.jhyy` | ~80 行 |
| Future trait + Pin/Unpin | `sema.jhyy` + `types.jhyy` | ~150 行 |
| state machine codegen(async fn → enum) | `codegen.jhyy` | ~300 行 |
| `.await` 表达式 codegen(轮询 + 状态恢复) | `codegen.jhyy` | ~200 行 |
| executor runtime(单线程 + 多线程 worker) | `std/async.jhyy` + `std/executor.jhyy` | ~400 行 |

**关键决策:** 单线程 + 可选 worker pool(不做完整 tokio 风格)· 不做 async closure ·
不做 async trait · state machine 编码走 Rust async 路径(无 stackless coroutine 复杂性)

**验收 gate:** 3+ async 测试 5/5 PASS · D43 → **N17** · async executor 跑通
1000 个并发 task 不死锁 · `jhyy_selfhost_check` byte-equal hold

**风险:** state machine codegen 复杂度 → 复用已有 enum codegen 路径 ·
leak/deadlock → leak detector + 1000 task 并发测试 ·
self-referential future → M0 不做(Pin 强制)

**Out of scope:** async closure · async trait · self-referential future / 完整 Pin ·
tokio 风格多线程 runtime · async + 借用检查复杂 case · 多线程 cap 集成(见第 11 项)

---

## 3. lifetime 完整版 + Polonius borrow check(原 `v4.3.0-plan.md`)

> ⚠️ **这一项跟当前计划直接冲突。** Polonius 正是
> [`active-workaround-clearance.md`](active-workaround-clearance.md) 里 **W-105**
> 的完整修法(~600 行 `borrow_check.jhyy` 新模块)。当前计划走的是「最小独占检查」
> 路线,把完整 Polonius 留在本文档。两者是**同一条路的短版与长版**,不是两件事 ——
> 做第 3 项时,W-105 可以顺势从 ACTIVE 翻 RESOLVED。

| 改动 | 文件 | 估算 |
|------|------|------|
| 完整 lifetime 标注语法 `'a` `'b` | `parser.jhyy` | ~50 行 |
| lifetime 子类型(协变 / 逆变 / 不变) | `sema.jhyy` | ~200 行 |
| **Polonius borrow check**(替换 v3.1.0 NLL stub = W-105) | `sema.jhyy` + `borrow_check.jhyy`(新) | ~600 行 |
| 完整 reborrow 规则 | `sema.jhyy` | ~150 行 |
| 借用 string view | `std/string.jhyy` | ~50 行 |

**关键决策:** Polonius 走 subset-based 算法(不做 full datafrog 优化)·
lifetime 子类型仅协变 + 不变(逆变留更后)· 不做 HRTB

**验收 gate:** 3+ lifetime 测试 5/5 PASS · D43 → **N18** ·
v3.1.0 stub 借用检查全部 case 仍过(regress 不退步)· `jhyy_selfhost_check` byte-equal hold

**风险:** Polonius 算法复杂度 → subset-based 简化 · lifetime 跟泛型交互 →
M0 仅在 generic fn 不带 lifetime 时完整 · reborrow 触发 regress 退步 → 完整版须跟 stub 兼容

**Out of scope:** 逆变 · HRTB · 完全 datafrog 版 Polonius · ghost / 幽灵借用 ·
Polonius + 闭包复杂 case · NLL→Polonius 迁移工具

---

## 4. closure 增强(原 `v4.4.0-plan.md`)

| 改动 | 文件 | 估算 |
|------|------|------|
| `move` 关键字(显式 move 捕获) | `parser.jhyy` + `sema.jhyy` | ~80 行 |
| 借用捕获(`&T` / `&mut T` 捕获) | `sema.jhyy` | ~120 行 |
| 泛型闭包 `\|x: T\| -> T` | `monomorphize.jhyy` | ~150 行 |
| 闭包 trait objects `Box<dyn Fn(i32) -> i32>` | `sema.jhyy` + `codegen.jhyy` | ~200 行 |
| Fn / FnMut / FnOnce 三 trait 区分 | `std/core.jhyy` + `sema.jhyy` | ~150 行 |

**关键决策:** `move` 仅强制 move 捕获 · 闭包 trait object 仅 `Box<dyn Fn>`(不做 `&dyn Fn`)

**验收 gate:** 4+ closure 增强测试 5/5 PASS · D43 → **N19** ·
v3.2.1 基础闭包测试仍过(regress 不退步)· `jhyy_selfhost_check` byte-equal hold

**风险:** borrow capture + lifetime 交互 → 复用第 3 项 Polonius ·
泛型闭包 + monomorphize → 失败时 fallback ·
闭包 trait object 跟 dyn Trait 集成 → 本项留 FnMut/FnOnce 接口,完整集成留第 6 项

**Out of scope:** async 闭包 · HRTB 闭包 · 闭包 + 高阶类型 · 闭包 + specialization(见第 10 项)

---

## 5. const generic(原 `v4.5.0-plan.md`)

| 改动 | 文件 | 估算 |
|------|------|------|
| 语法 `fn foo<const N: usize>(arr: [T; N])` | `parser.jhyy` | ~60 行 |
| const 泛型参数挂在 fn / struct 节点 | `ast.jhyy` | ~30 行 |
| 单态化时 const 参数求值 | `monomorphize.jhyy` | ~150 行 |
| `[T; N]` 数组类型用 const N 表达 | `types.jhyy` + `codegen.jhyy` | ~80 行 |

**关键决策:** const 参数仅支持整数 + bool + char · 不做 const 表达式求值

**验收 gate:** 3+ const generic 测试 5/5 PASS · D43 → **N20** · `jhyy_selfhost_check` byte-equal hold

**风险:** const 求值复杂度 → M0 简化仅常量 · `[T; N]` 交互 → v1.0 已有固定数组,
本项是参数化升级

**Out of scope:** string / struct const 参数 · 复杂 const 表达式 ·
const generic + specialization(见第 10 项)· const generic + HRTB

---

## 6. trait objects / dyn Trait(原 `v4.6.0-plan.md`)

| 改动 | 文件 | 估算 |
|------|------|------|
| trait 语法 + `impl Trait for Type` | `parser.jhyy` + `sema.jhyy` | ~150 行 |
| vtable emit(per type impl) | `codegen.jhyy` | ~200 行 |
| `dyn Trait` 类型 + vtable 动态分发 | `types.jhyy` + `sema.jhyy` | ~200 行 |
| `Box<dyn Trait>` heap-allocated | `std/core.jhyy` + `codegen.jhyy` | ~80 行 |
| Upcast(`as dyn SuperTrait`) | `sema.jhyy` | ~100 行 |

**关键决策:** trait 不支持默认方法 · 不支持关联类型 · 仅 `Box<dyn>`(不做 `&dyn`)

**验收 gate:** 3+ trait / dyn 测试 5/5 PASS · D43 → **N21** · `jhyy_selfhost_check` byte-equal hold

**风险:** vtable 跟 codegen 主路径交互 → vtable 走独立 codegen 路径 ·
upcast/downcast 规则复杂 → M0 仅 upcast · trait bound on generic → 仅 `T: Trait` 形式

**Out of scope:** 默认方法 · 关联类型 · `&dyn Trait` · HRTB · trait + specialization ·
object-safe 完整规则 · async trait

---

## 7. 错误恢复(原 `v4.7.0-plan.md`)

| 改动 | 文件 | 估算 |
|------|------|------|
| Parser 同步点恢复(跳到下一个 `;` 或 `}`) | `parser.jhyy` | ~100 行 |
| Sema 多错误收集(不遇首个错就 bail) | `sema.jhyy` | ~150 行 |
| 错误聚合 `Vec<Diag>` | `diag.jhyy`(新) | ~150 行 |
| Source location + span 增强 | `lexer.jhyy` + `parser.jhyy` | ~80 行 |
| CLI 错误输出:彩色 + caret 指向 | `main.jhyy` | ~100 行 |

**关键决策:** 同步点仅 `;` 和 `}` · 不实现 LSP / IDE 集成

**验收 gate:** 2+ 错误恢复测试 5/5 PASS(单文件 5+ 错误全部报告)·
**不出现级联错误**(同一 bug 不报 5+ 次)· D43 → **N22** · `jhyy_selfhost_check` hold

**风险:** 恢复引入 false positive → 不恢复的 case 走原 bail,恢复路径保守 ·
span 与行/列不一致 → lexer 统一记录 byte offset → span mapping

**Out of scope:** 复杂 resync 策略 · LSP / IDE 集成 · 增量编译 · 错误代码(E0001)· fix-it hint

> 📌 **被当前计划引用:** W-105 的最小独占检查要报错,而
> [`active-workaround-clearance.md`](active-workaround-clearance.md) 里的方案是
> 「先在 `sema.jhyy` 内就地报错到 stderr,**不等**本项」。若本项先落地,W-105 应改接
> `Vec<Diag>` 而不是就地 stderr。

---

## 8. 基本优化 pass(原 `v4.8.0-plan.md`)

| 改动 | 文件 | 估算 |
|------|------|------|
| 统一优化 pass 框架 | `opt_pass.jhyy`(新) | ~150 行 |
| 常量折叠(`1 + 2 * 3` → `7`) | `opt_pass.jhyy` | ~100 行 |
| 代数化简(`x + 0` / `x * 1` / `x * 0`) | `opt_pass.jhyy` | ~80 行 |
| 死代码消除(`if false { X } else { Y }`) | `opt_pass.jhyy` | ~80 行 |
| 不可达代码消除 | `opt_pass.jhyy` | ~60 行 |
| 集成到主路径(sema 后 / codegen 前) | `main.jhyy` | ~30 行 |

**关键决策:** 不做循环优化 / LICM / GVN / instruction scheduling ·
仅 1 级优化(`-O1`)· pass 仅在 IR 层(v2 自写后端已有 peephole 兜底)

**验收 gate:** 3+ 优化测试 5/5 PASS · D43 → **N23**(优化改 .il)·
`-O1` 与 `-O0` 语义等价 · 优化后 .s 长度 ≤ 不优化 +5% ·
**`-O0` 必须仍 byte-equal**(D43 baseline 锁 `-O0`)

**风险:** 优化引入正确性 bug → 严格保持语义等价,sema 不跳过 ·
pass 跟 codegen 漂移 → 独立放置,失败时关 `-O1` fallback ·
闭环漂移 → `-O0` byte-equal 是硬约束

**Out of scope:** 循环优化 / LICM / GVN · instruction scheduling · 自动向量化 / SIMD ·
PGO · LTO · `-O2` / `-O3`

---

## 9. 包管理器(原 `v4.9.0-plan.md`)

| 改动 | 文件 | 估算 |
|------|------|------|
| `jhyy new <name>` | `main.jhyy` | ~80 行 |
| `jhyy build`(读 `jhyy.toml`) | `main.jhyy` | ~150 行 |
| `jhyy test` | `main.jhyy` | ~100 行 |
| `jhyy.toml` TOML 解析 | `toml.jhyy`(新) | ~200 行 |
| 依赖管理(`[dependencies]` 解析) | `manifest.jhyy`(新) | ~200 行 |
| 项目骨架模板 | `compiler/templates/`(新) | ~50 行 |

**关键决策:** 依赖仅 git URL + 版本 tag(不做 registry)· 不做 lockfile ·
不做 virtual workspace / multi-package · 不做 publish

**验收 gate:** 4+ 包管理测试 5/5 PASS · D43 → **N24** · `jhyy_selfhost_check` hold

**风险:** TOML 解析复杂度 → 用 std lib 实现,不引第三方库 ·
git 依赖 clone 网络问题 → 支持 path 依赖,git 失败给清晰错误 ·
多版本冲突 → M0 仅支持单一版本(latest tag)

**Out of scope:** 自建 registry · lockfile · virtual workspace · publish ·
binary distribution · build profiles / dev-deps · workspace 级 CLI flags

---

## 10. HKT + specialization(原 `v4.10.0-plan.md`)

| 改动 | 文件 | 估算 |
|------|------|------|
| HKT 语法 `trait Functor<F<*>>` | `parser.jhyy` + `sema.jhyy` | ~200 行 |
| `*` = 类型构造器位置 | `types.jhyy` | ~80 行 |
| Specialization `impl` 覆盖默认 | `sema.jhyy` | ~150 行 |
| Specialization 解析规则(优先最具体) | `monomorphize.jhyy` | ~100 行 |

**关键决策:** HKT 仅 1 阶(不支持 `F<G<*>>`)· specialization 仅单层覆盖 ·
不做 associated type constructors

**验收 gate:** 3+ HKT/specialization 测试 5/5 PASS · D43 → **N25** · `jhyy_selfhost_check` hold

**风险:** HKT 推导复杂度 → M0 仅 1 阶 · specialization overlap 误判 → 仅单层覆盖,
overlap 报错清晰

**Out of scope:** 多阶 HKT · associated type constructors · negative reasoning ·
HKT + lifetime · HKT + const generic · type class coherence 完整规则

---

## 11. 并发 cap + 完整 memory model(原 `v4.11.0-plan.md`)

> **前置:OS M11 launch 之后。** M11 launch 路径本身需重新评估
> (per 2026-09-29 user FINAL 决定,`v2.0.0-os-prep.md` 已归档)。

| 改动 | 文件 | 估算 |
|------|------|------|
| 完整 C11 / Rust memory model(6 个 order) | `codegen.jhyy` + `std/atomic.jhyy` | ~300 行 |
| `atomic_load/store/rmw` 完整版 | `sema.jhyy` + `codegen.jhyy` | ~300 行 |
| 多线程 `Cap<T>` send / sync | `sema.jhyy` | ~150 行 |
| cap / fd table 集成 | `sema.jhyy` + `codegen_amd64_emit_call.jhyy` | ~200 行 |
| ARM / RISC-V `Cap<T>` ABI | `abi_aarch64_sysv.jhyy` + `abi_riscv64_sysv.jhyy`(新) | ~600 行 |
| Thread spawn + join + channel | `std/thread.jhyy` + `std/atomic.jhyy` | ~400 行 |

**关键决策:** 6 个 memory order 全支持 · 仅 OS thread(不做 green thread)·
多架构 Cap ABI 仅基本 INTEGER + 寄存器对齐(完整 8-class 分类器留更后)

**验收 gate:** 4+ atomic / thread / cap 测试 5/5 PASS · D43 → **N26** ·
多线程 producer/consumer 同步测试 1000 次不 fail ·
aarch64 / riscv64 跨架构 ABI 通过 cross-compile(WSL / docker)

**风险:** memory model 跟 codegen 交互 → atomic 走独立 codegen 路径 ·
多架构 ABI 复杂 → 复用 v2 自写后端模式,按架构逐个做 ·
cap race condition → OS 联调测试,失败时回退到 3g + 3c + 3f stub

**Out of scope:** Green thread / coroutine(见第 2 项 async)· 完整 8-class SysV 分类器 ·
async + 多线程完整集成 · 跨机器 capability delegation · 完整 `std::sync`

> 📌 **与 W-104 的关系:** 第 11 项的「完整 8-class SysV 分类器」正是
> [`active-workaround-clearance.md`](active-workaround-clearance.md) 里 **W-104**
> 的同族工作(当前 SysV 参数分类借用 Win 分类器)。做本项时应把 W-104 一并解决。

---

## 12. `.jhyynb` native binary format(原 `v4.12.0-plan.md`)

**Spec 锚点:** [`../../abis/jhyy-binary-format-v1.0.0.md`](../../abis/jhyy-binary-format-v1.0.0.md)
(2026-09-04 锁,设计完成,实装未排)

| Part | 内容 | 估算 |
|------|------|------|
| 1 | DWARF emitter(`dwarf_emit.jhyy` / `dwarf_expr.jhyy` / `jhyynb_sections.jhyy`) | ~900 行 |
| 2 | `--target=jhyy-os` 后端集成(`target_dispatch` + `codegen_amd64` + `emit_call` + `main`) | ~490 行 |
| 3 | `jhyy-inspect` CLI(section table / cap_init / ipc_dispatch dump) | ~200 行 |
| 4 | 5 个测试(smoke / dwarf / ipc / cap / selfhost) | — |
| 5 | 文档同步(spec 不动,实装后 § 18 验证打勾) | — |

**关键决策:** DWARF v5 子集 · `Cap<T>` phantom 字段不 emit ·
`#[ipc_handler]` 不进 spec(但 emit cap_offset 表)· wire-format per D40 ·
`--target=jhyy-os` 仅 64-bit · `.tls` section 留空占位

**验收 gate:** 5 个测试 5/5 PASS · D43 → **N27** · spec § 18 验证逐项打勾
(loader smoke / GDB attach 跨仓 / `jhyy-inspect` / CodeGraph 摄入 / jhyy 自举跨仓)·
`dwarf_emit.jhyy` 覆盖率 > 80%

> 跨仓项(GDB attach / OS 自举)本项 ship gate **不阻塞**,但 ship 后需通知
> jhyy_OS 仓 `.jhyynb` 实装就位。

**风险:** DWARF 字节级正确性 → 严格按 v5 spec,跟 GCC/LLVM emit cross-test ·
emit 字段偏移错 → 单元测试逐字段对 D-lock ·
ipc_dispatch 跟 OS cnode byte-equal fail → 跨仓 cross-test ·
GDB attach 联调失败 → OS 端 `jhyy-gdbstub` 需先 ship

**Out of scope:** jhyy_OS loader 实现(跨仓)· aarch64 / riscv64 字节序差异 ·
完整 DWARF · QBE `.s` post-process 包装路径 · 完整 8-class SysV 分类器 ·
`.tls` 实际内容 · `jhyy-gdbstub` daemon · `jhyy-inspect` 图形化 UI

---

## ⚠️ 已过时的验收基线(2026-10-15 核对)

原 12 份计划里的 gate 写着 `regress.py 104/104 PASS` 或
`regress.py --all → 2/2 gated PASS`。**当前实测基线是 163/163 PASS + 22 SKIP。**
启动任何一项时,gate 数字要按当时的实测基线重取,不要照抄本文档。

---

## 关于版本号

原 12 份计划各自绑定一个版本号(`v4.1.0` … `v4.12.0`),并约定「每个 minor
version 一份 plan」(per `feedback_plans_per_version`)。2026-10-15 user 决定改为
**合并成单一 backlog 文档、不以版本号命名** —— 理由是这 12 项全部未启动,
版本号承诺了一个并不存在的排期,反而让「v4.12.0」听起来像是既定里程碑。

版本号在**启动时**才分配,不预先占位。D43 目标(N17…N27)同理 —— 那是原计划里
按序推演的编号,启动时按当时的实际代数重新定。

## Cross-ref

- 当前进行中的计划:[`active-workaround-clearance.md`](active-workaround-clearance.md)
- 已 ship 的 v4.0.x 计划(保留为审计轨迹,不合并):`v4.0.0-plan.md` …
  `v4.0.7-plan.md`
- v4 概念与决策锁:[`README.md`](README.md)
- L1 长篇设计:[`../roadmap/v4.x-post-merge.md`](../roadmap/v4.x-post-merge.md)
- 跨仓(OS):[`../../../jhyy_OS/docs/coordination.md`](../../../jhyy_OS/docs/coordination.md)
- 台账:`docs/internal/workarounds.md`
