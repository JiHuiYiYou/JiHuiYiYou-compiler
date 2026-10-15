# 活跃 workaround 清零 — v4 发版前必须真修的 8 条

**状态:** 🔴 **进行中**(2026-10-15 建,per user 2026-10-10 决定「所有 defer/active 的 workaround
必须在 v4 正式版中清零,大不了 v4 不发」)

**基线:** `d2f5361`(2026-10-15)6 条首次进台账 → `93cdf3d` 补 W-109 → 补 W-110(8 条)。
台账里的条目:`docs/internal/workarounds.md` W-103..W-107 / W-105.1 / W-109 / W-110。

**优先级(高 → 低):**

| # | W-NNN | 一句话 | 性质 | 相对工作量 |
|---|-------|--------|------|-----------|
| 1 | **W-105** | `check_borrow` 恒 `return 1` → `&mut` 独占性完全不检查 | 语言层静默失效 | **见下方 ⚠️ 决策点** |
| 2 | **W-110** | 一个函数里多条浮点比较连续改同一 mutable 局部 → 结果串号 | 静默算错,**根因未 RCA** | **先做 RCA** |
| 3 | **W-109** | 自举 IL lexer 缺 6 个浮点比较助记符 → f32 比较按 f64 算,`f64 ==/!=` 硬失败 | **核心类型基本运算算错** | 小(补 6 个分支) |
| 4 | **W-103** | `std_os_open/read/write/exit` 全是 mock,`std_os_exit` 不退出 | stdlib 对用户撒谎 | 小(5 个 C bridge) |
| 5 | **W-104** | SysV ABI 参数分类调用 Win 分类器 | 错 ABI,目标路径平时不走 | 中(接线 + 新测试) |
| 6 | **W-107** | 五个 per-fn 表硬编码 1024,距触发只剩 33 个 fn | 静默降级(非溢出) | 中(改预分配) |
| 7 | **W-106** | `symtab_lookup_one` arena-touch 强制物化栈帧 | 冗余代码,后端依赖 | 小(需先构造复现) |
| 8 | **W-105.1** | `check_cap_pass` 同款 stub,**当前无调用点** | 死代码 | 最小(删或实现) |

排序依据:**① 现在就会让用户拿到错误结果** > ② 目标路径一旦启用就错 >
③ 距触发有明确余量的降级 > ④ 冗余/死代码。

> **W-109 与 W-110 是两回事,别当成一个 bug 一起「修好」。** W-109 是 lexer 缺
> 助记符;W-110 是 temp 槽位串号(属 W-096/097/101 家族)。W-110 排在前面是因为
> 它根因未确定,**RCA 本身就是第一步**。

> **⚠️ 一条比排序更重要的教训(2026-10-15 新增):** W-110 是**把 `float_cmp`
> 的 printf arity 修对之后**才暴露的。测试修好之前看不到真值,RCA 就是不完整的
> —— 第一版只抓到 lexer,第二个缺陷是被「真值」逼出来的。
> **`测试翻不了红的时候,RCA 也是不完整的`。**
> 现状:166 个可跑测试里 **53 个(32%)零信号**(6 个有 EXPECT 但数学上不可能
> 失败 + 47 个只验「进程没崩」)。见 `docs/internal/tests.md` 与
> `scripts/dev/audit_test_assertions.py`。修 W-109/W-110 的同时应该把比例压下去,
> 否则下一个 bug 还是这样活下来。

> **W-109 原本为什么至今没被发现:** 唯一覆盖它的测试 `float_cmp.jhyy` 第 48 行是
> **无条件 `return 42`**,比较结果只喂给一个 5 个 `%d` 却只声明 1 个参数的
> printf(正好撞上 B8)。所以 `regress.py --tests=float_cmp.jhyy` 报
> `PASS EXIT=42` —— 这个 PASS 不携带任何信息。`src0` 自身几乎不用浮点比较,
> 自举闭环因此一路绿灯。**又一次「闭环只证明自洽,不证明正确」。**

---

## ⚠️ 决策点:用户政策与既有计划冲突

W-105 的修复,[`backlog.md` § 3](backlog.md)(原 `v4.3.0-plan.md`)已经规划过了 ——
**Polonius borrow check,新模块 `compiler/src0/borrow_check.jhyy` 约 600 行**。
那不是一个 sprint 收尾,是一个完整算法实现。

于是 2026-10-10 的政策(「ACTIVE 必须清零,大不了 v4 不发」)跟 backlog 里的
既有排期直接撞车。三个选项:

| 选项 | 做法 | 后果 |
|------|------|------|
| **A. 先做最小独占检查**(推荐) | 现在只做「同一作用域内 `&mut` 互斥 + `&mut`/`&` 互斥」的局部检查(~150 行),完整 Polonius 留 backlog | 双写这个**最危险的** case 当场堵住,政策可满足;Polonius 仍是 feature 项而非 blocker |
| B. 直接上 Polonius | 把 v4.3.0 提到 v4 final 之前 | v4 final 被一个 600 行算法实现无限期挂起 |
| C. W-105 降级为 DEFERRED | 台账改判,承认这是有意的 ship-gate 决策 | 政策实质上被自己放宽;但如实反映了 2026-08 当时的设计意图 |

**本文档按 A 写。** 若 user 选 B 或 C,只需改 W-105 一节与本决策点,其余 7 条不受影响。

---

## 1. W-105 — `check_borrow` 是硬编码 `return 1`

**台账:** W-105 | **触发面:** `compiler/src0/sema.jhyy:2558-2560`
**调用点:** `compiler/src0/sema.jhyy:2677`(`let _bc = check_borrow(ctx, ta, (*fd).body)`,
在函数声明检查路径上,**每个被 check 的函数都跑**)

**症状(全部静默放过):**
- `let y = &mut x; let z = &mut x;` —— 双 mutable 冲突
- `&mut` 与 `&` 共享/可变互斥
- reborrow `&mut *x`
- 跨函数 borrow、nested block 借用作用域
- lifetime 子类型 / variance

**根因:** v3.1.0 的 ship-gate 选择「先 ship 表面,语义分析留 v3.x 末」。
源码 `:2549-2557` 的注释诚实列出了不检查的项,但它从未进台账。

**影响面证据:** `&mut` 在 `compiler/src0/{ast, codegen_amd64_state, ir, mono, parser,
sema, std/string, types}.jhyy` 八个文件里都有使用,不是没人调的死代码。
`compiler/tests/examples/borrow_check_basic.jhyy` 存在,但它测的是 borrow 的
**表面可解析性**,不是冲突检测。

**修法(选项 A,最小独占检查):**
1. 在 `check_borrow` 里遍历 `body`,收集每个 `&T` / `&mut T` 表达式的
   (被借变量, 可变性, 作用域区间)
2. 同一区间内:两条 `&mut` 指向同一变量 → 报错;一条 `&mut` + 一条 `&` 同变量 → 报错
3. 区间用「所在 block 起止 token index」近似 —— **不做 NLL**,不做 reborrow,
   不做跨函数(这些留 Polonius)
4. 新增诊断沿用 v4.7 规划的 `Vec<Diag>` 形态,但**不等它** —— 先在
   `sema.jhyy` 内就地报错到 stderr

**验收 gate:**
- 新增 `tests/borrow_conflict_double_mut.jhyy` / `borrow_conflict_mut_shared.jhyy` ——
  两者必须**编译失败**且错误信息指向第二个冲突点
- `borrow_check_basic.jhyy`(现有)仍 PASS —— 不许把合法 borrow 也判死
- regress 全量不退步(基线 163/163 PASS + 22 SKIP)
- `closure_check.sh` PASS(v2.s == v3.s)
- `fixed_point.sh N=5` 7 PASS / 0 FAIL / 0 INFO

**风险:**
| 风险 | 缓解 |
|------|------|
| 近似作用域区间过宽 → 合法代码被误判 | 区间只用 block 边界,**不做**语句级收窄;误判案例进 regress 后收窄规则 |
| 误杀 src0 自身的 `&mut` 用法 | src0 本身必须能过编译 —— 跑 `closure_check.sh` 是硬门 |
| 范围失控长成 Polonius | 明确 out of scope:reborrow / 跨函数 / lifetime 子类型 |

---

## 2. W-110 — 一个函数里多条浮点比较连续改同一 mutable 局部 → 结果串号

**台账:** W-110 | **触发面:** 自举后端 temp 槽位管理(不是 lexer)

**症状(最小复现,已实测):**

```jhyy
fn one(a: f64, b: f64) -> i32 { if a < b { return 1; } return 0; }

fn many(a: f64, b: f64) -> i32 {
    let mut n: i32 = 0;
    if a == b { n = n + 1; }
    if a != b { n = n + 10; }
    if a <  b { n = n + 100; }
    if a <= b { n = n + 1000; }
    return n;
}
```

```
one(3,2)=0        ← 单条 f64 比较:完全正确
many(3,2)=1110    ← 错误,应为 10
many(1,2)=1110    ← 正确
```

`many(3,2)` 与 `many(1,2)` **返回同一个值** —— 四条 `if` 读到了同一份比较
结果(看起来是最后一条 `a <= b` 的)。

**这条为什么单独登记、且排在 W-109 前面:** 它跟 W-109 根因不同(W-110 是 temp
槽位串号,属 W-096/097/101 家族),**当成一个 bug 一起「修好」会两边都修不对**。
排在前面是因为**根因未确定,RCA 本身就是第一步**。

**为什么第一版 RCA 没抓到它:** 它是**把 `float_cmp.jhyy` 的 printf arity 修对
之后**才暴露的 —— 此前输出全是垃圾,看不到真值就定不出真因。
**测试翻不了红的时候,RCA 也是不完整的。**

**RCA 两条假设(都未验证,别当结论):**
1. 四条比较的布尔结果落到同一 temp 槽位,后写覆盖先写
2. W-109 的 `ceqd`/`cned` unknown mnemonic 造成 IL 解析错位,后续 token 被错读
   —— 最小复现同样打了 `unknown QBE IL mnemonic`,与假设 2 一致但未证实因果

**第一步:** 跑 RCA 定因。建议从 `codegen_amd64_state.jhyy` 的 temp 记录路径
入手,对照 W-097 的七处 hoist site 与 W-101 的 record path。

**验收 gate:**
- 上面的最小复现进 `compiler/tests/examples/`,断言
  `many(3,2)==10` 且 `many(1,2)==1110` —— **两个不同实参必须给出不同结果,
  这才是能抓住串号的断言**(只断言一个值的话,串号恰好也能过)
- `float_cmp.jhyy` 删掉 `// SKIP:` 后输出为 `d=111110 d2=10 s=15 p=1 dem=1`
- `closure_check.sh` PASS + `fixed_point.sh` 7 PASS + regress 不退步

---

## 3. W-109 — 自举 IL lexer 缺 6 个浮点比较助记符

**台账:** W-109 | **触发面:** `compiler/src0/codegen_amd64_lexer.jhyy:1628-1647`

**症状(两类,已实测):** 后端 emit 出自己 lex 不回来的助记符。

| emit 出的 | 语义 | lexer 命中 | 后果 |
|---|---|---|---|
| `cles` / `clts` / `cgts` / `cges` | f32 `<=` / `<` / `>` / `>=` | `:1638-1641` 只判 `n3=='t'/'e'`,**不判 `s`** | 认成 f64 版本 → **按 f64 比较** |
| `ceqd` / `cned` | f64 `==` / `!=` | 落到 `:1642` else,无一命中 | **硬失败** `unknown QBE IL mnemonic` |

f64 的 `<` `<=` `>` `>=` **是好的**(那 4 个 `c*d` lexer 认识),整数比较也齐全
(`ceqw`/`cnew`/`cs*w`/`cu*w` 各 5 个)。

**根因:** v2.11.15「A1-XMM」补 f64 比较时只加了 `n3 == 'd'` 的四种形式。
更糟的是 `:1642` 的 else 分支会把未知助记符**默默映射成 `cs*w`** ——
`cles` 恰好落进 `:1641` 的 `cled` 分支,所以它不报错,只是算错。

**修法:**
1. `:1635-1641` 补齐 6 个助记符(`cgts`/`cges`/`clts`/`cles` 加 `s` 分支,
   另加 `ceqd`/`cned` 两个新分支)
2. **`:1642` else 分支改成兜底报错** —— 现在它会把未知助记符映射成 `cs*w`,
   下次再加助记符时同样的静默错类型会重演。这条比 1 更重要

**已完成的部分(2026-10-15,commit 见 CHANGELOG):**
- `float_cmp.jhyy` 已改成真断言:printf 按实际用到的 5 个参数逐个声明
  (此前声明 1 个却传 5 个 %d,输出全是垃圾)、退出码由比较结果推导、
  逐值 `EXPECT-OUT` 断言、加 `// SKIP: W-109`(修完删掉这行即验收)
- harness 新增 `// EXPECT-OUT:` 指令(只比 stdout 不比 stderr)
- **造红灯已验证**:临时去掉 SKIP → `FAIL expected=111137 got=112237`,
  并打出 `d=111110 d2=1110 s=15 p=1 dem=1`

**关于期望值 —— 之前这里算错过,现已更正:** 总和是 **111137**
(`cmp_d(3.0,2.0)` 里 `b >= a` 即 `2 >= 3` 为假,该项就是 10)。原注释是对的,
第一版 RCA 写的「211137 / 注释算错了」是本计划作者自己的算术错误,已删。

**验收 gate:**
- `float_cmp.jhyy` 删掉 `// SKIP:` 后必须 PASS,且输出是
  `d=111110 d2=10 s=15 p=1 dem=1`
- ⚠️ 注意:**当前实测 `d2=1110`(应为 10)** —— 修 W-109 本身**未必能让它变绿**,
  因为 `d2` 的错来自 **W-110**(多条比较串号)。两条都要修
- 新增用例覆盖 f64 的 `==` / `!=` 与 f32 的四个序比较
- `closure_check.sh` PASS + `fixed_point.sh` 7 PASS + regress 不退步

**风险:**
| 风险 | 缓解 |
|------|------|
| else 分支改报错后,某些原本被静默映射的路径开始报错 | 那说明本来就在算错;逐个查清是真 bug 还是该加助记符 |
| src0 自身若有依赖静默映射的比较 | `closure_check.sh` 是硬门,红了就说明踩到了 |
| 修完 W-109 以为 W-110 也好了 | `float_cmp` 的 `d2` 就是反例 —— 验收必须看**逐值输出**,不能只看总 PASS |

---

## 4. W-103 — `std/os.jhyy` 全是 mock

**台账:** W-103 | **触发面:** `compiler/src0/std/os.jhyy:69-144`

**症状:**
- `std_os_open` 校验入参后**恒返回 fd=42**,从不调 `open(2)`
- `std_os_read` / `std_os_write` 校验后**恒返回 `n`**,`buf` 不读不写,
  无效 fd 也照样「成功」
- `std_os_exit(code)` 只 `let _ignore = code; return;` —— **进程不退出**,
  docstring 写的 "never returns" 是假的
- `compiler/tests/examples/std_os_basic.jhyy:20` 是这些 stub 的 **inline 副本**,
  regress 里那个 PASS 验的是副本,不是真身

**根因:** W-079 的 workaround 有两半 —— (a) std_io 改 single-type-pointer externs,
(b) std_os 用 M0 stubs。W-079 翻 ✅ 时 Resolution 只声明 (a) 由 W-080 解决;
W-080 实际只动了 `std/io.jhyy` 和 `emit_call`。**(b) 从来没人动过。**

**修法(照 W-080 给 `jh_fputs_stdout` 做的那个模式):**
1. `compiler/src0/jhyy_helpers.c` 补 5 个 C bridge ——
   `jh_open` / `jh_close` / `jh_read` / `jh_write` / `jh_exit`
   (现有 `jh_fopen_wb` 覆盖的是「按 wb 模式打开文件」,不是 fd 级 API)
2. `std/os.jhyy` 五个函数改成调对应 bridge,保留现有入参校验
   (EINVAL 语义不变,只是把「恒返 mock 值」换成真 syscall)
3. `std_os_basic.jhyy` 的 inline 副本改成 `import std::os` 用真身
4. `std_os_exit` 调 `jh_exit` 后补 `unreachable`(jhyy codegen 需要)

**验收 gate:**
- `std_os_basic.jhyy` 改成 import 真身后仍 PASS,且**新增**「写文件 → 读回 →
  内容 byte-equal」的真实 I/O 断言(mock 版恒过,真版才验得住)
- 新增 `std_os_exit_code.jhyy`:进程退出码 == 传入 code(当前不可能通过)
- regress 不退步;`closure_check.sh` PASS

**风险:**
| 风险 | 缓解 |
|------|------|
| 真 `std_os_exit` 生效后,自举编译器内部某处误调 → 编译中途退出 | src0 自身 grep 确认无人调 `std_os_exit`;若有人调,那是真 bug 一起修 |
| C bridge 增加 stage0 依赖面 | 与 v4.1.0 的 M5「删 C runtime」方向相反 —— **登记为已知张力**,M5 那份计划本来也还没启动 |

---

## 5. W-104 — SysV 参数分类借用 Win 分类器

**台账:** W-104 | **触发面:** `compiler/src0/abi_amd64_sysv.jhyy:229`

**症状:** SysV 后端按 Win x64 约定给函数定型。Win 与 SysV 的寄存器分配、
struct 分类、返回约定都不同(≤16B 小 struct 返回:Win 走 hidden sret 指针
—— `:209-211` 正是这么 emit 的;SysV 走 rax/rdx)。分类错了,调用两侧对参数
寄存器归属的理解就不一致。

**根因:** Stage 1c.3 mirror 阶段的占位,注释自认:
`// Phase 2b: replace with abi_sysv_classify_arg + class→letter map.`
**正确的函数已经写好了** —— `abi_sysv_classify_arg`(`:79`)与
`abi_sysv_classify_arg_full`(`:147`)都在同一文件里,只是 emit 路径没调用。

**修法:**
1. `:229` 改调 `abi_sysv_classify_arg_full`,加 class → QBE letter 映射
2. `:209-211` 的 sret 判定按 SysV 规则改(≤16B 不发 hidden param)
3. 补 amd64_sysv 目标的 regress 用例 —— **当前 ship gate 只覆盖 amd64_win,
   这条至今没有任何测试能触发它**(跟 `fixed_point_linux.sh` 同一个病:
   没测到的路径不会被门发现)

**验收 gate:**
- 新增 `--target=amd64_sysv` regress 用例:struct 按值传参 / 返回、混合整浮点参数
- 上述用例在修复前**必须失败**(造红灯),修复后 PASS
- amd64_win 现有路径零回归(`regress` + `closure_check.sh`)

**风险:**
| 风险 | 缓解 |
|------|------|
| SysV 路径从无测试 → 修完仍不知道对不对 | 修之前先造红灯;没有红灯就不算修(per `feedback_fix_evaluation_rule`) |
| sret 规则改动波及 Win 路径 | 两个 ABI 文件物理隔离,`abi_amd64_win.jhyy` 不动 |

---

## 6. W-107 — per-fn 表 1024 上限

**台账:** W-107 | **触发面:** `compiler/src0/codegen_amd64_state.jhyy:511 / 515 / 524 / 530 / 537`
(五个表:`fn_starts` / `per_fn_max` / `per_fn_alloc` / `per_fn_addr_pool` / `per_fn_base_t`)

**余量(实测,非注释估计):**

```
JHY_WRITE_IL=1 jhyy.exe compile --target=amd64_win --no-link \
  compiler/src0/main.jhyy -o <tmp>/main
grep -cE '^export function [wl] |^function [wl] ' <tmp>/main.il   → 991
1024 − 991 = 33
```

**越界后的行为:** 写侧有守卫(`:1727` / `:1736`),`:1740` 把 `fn_count` 截到 1023。
所以**这不是缓冲区溢出** —— 索引 ≥1023 的函数其 `use_per_fn` 判据
(`codegen_amd64_emit_ctrl.jhyy:514`)失败,静默退回 legacy 全局 max 帧路径。
表现是性能塌陷 + 深递归风险(W-074.6 当初的症状以这个形式回来),不是立刻炸。
按实测行为定级,**不是紧急项**。

**修法:**
1. 表大小按 token 流里的实际函数数预分配 —— `cg_compute_per_fn_max_temps`
   已经是全量 pre-scan,函数总数是它的副产品,不需要两遍
2. 删掉 `:1740-1742` 的截断;真越界(预分配仍不够)时报错,不静默退回
3. 让 `use_per_fn` 失败时报错而非 fallback —— 静默退回正是当初让 W-074.6
   难以定位的原因

**验收 gate:**
- 造红灯:人为把上限调到 991,现路径应静默降级 PASS(证明门测不到),
  修后应报错
- 新增测试:单模块函数数 >1024,编译结果正确且无 frame 塌陷
- `fixed_point.sh` cap_test 三代 exit 一致;`closure_check.sh` PASS

**风险:**
| 风险 | 缓解 |
|------|------|
| 预分配大小依赖 pre-scan 正确性 | pre-scan 已经在填这些表,不是新增依赖;不一致时新加的报错会抓到 |
| arena 分配变大 | 五个表 ×8KB = 40KB 常驻,改成按需后反而更小 |

---

## 7. W-106 — `symtab_lookup_one` arena-touch

**台账:** W-106 | **触发面:** `compiler/src0/symtab.jhyy:261-264`

**症状:** 每次符号查找都造一个 `StringBuilder` 再丢掉。功能无害,但它是
**纯为迎合后端实现细节而存在的代码** —— 注释自认:
`// WORKAROUND: amd64_win stack-spill — touching arena forces codegen to
materialize stack frame in safe way`。后端哪天不再需要这个 touch,
这里不会报错,只会静默变成无效代码。

**根因:** v1.x sprint 3 定位到的 amd64_win stack-spill,当时修法是在调用点
人为制造后端「看得见」的 arena 操作。它引用的 `sprint-3-commit-5-sema-attempt.md`
已不在仓库里,追溯链断了。

**修法:**
1. **先构造复现** —— 删掉这三行,跑 `closure_check.sh` + `fixed_point.sh`
   + regress。绿 = 已经是冗余,直接删;红 = stack-spill 根因仍存在,
   补一条最小复现记录再决定
2. 绿 → 删三行,`symtab_lookup_one` 直接进 hash 查找
3. 红 → 保留,但把失效条件写进台账,并补回缺失的复现文档

**验收 gate:**
- 三行删除后 `closure_check.sh` PASS + `fixed_point.sh` 7 PASS + regress 163/163
- 若删除后变红:新 W-NNN 登记根因,本条状态翻 ACTIVE 并写明复现

**风险:**
| 风险 | 缓解 |
|------|------|
| 删掉后某个特定 codegen 路径才炸 | 三道门全跑,且 991 个函数的覆盖面够宽 |

---

## 8. W-105.1 — `check_cap_pass` 同款 stub(无调用点)

**台账:** W-105.1 | **触发面:** `compiler/src0/sema.jhyy:2578-2579`

**症状:** 同 W-105 —— 不检测 active-cap conflict / reentrancy / depth
transition;不支持 `*Cap<T>` 裸指针、不支持 `cap_new()` builtin ctor。

**与 W-105 的关键差别:** grep 全 `compiler/src0` 后,**`check_cap_pass` 没有任何
调用点** —— 死代码,当前不会有程序因为它而缺检查。W-105 则每次函数声明都真跑。
**优先级最低。**

**修法(二选一,倾向删):**
- **删**:连同 stub 注释一起删掉。留一个没人调的「假装会检查」的函数,
  比不检查更坏 —— 下一个人接线时会以为检查存在
- **实现**:接进声明检查路径,则必须同时实现 cap ownership 分析

**验收 gate:**
- 删:`grep check_cap_pass compiler/src0` → 0 hit;三道门全绿
- 实现:`Cap<T>` 的 active-cap conflict 有测试覆盖,且**先造红灯**

---

## 全局 ship gate(6 条全修完)

```
regress jhyy.exe              → 不低于 163/163 PASS + 22 SKIP
regress jhyy_v2.exe           → 不低于 163/163 PASS + 22 SKIP   ← self-hosted 也跑
closure_check.sh              → PASS, v2.s == v3.s byte-identical
fixed_point.sh N=5            → 7 PASS / 0 FAIL / 0 INFO
workarounds.md 索引           → ACTIVE 0 / DEFERRED 0
```

**两条经验(2026-10-15 这轮学到的,别再踩):**

1. **每条修完都要造红灯。** W-104 那条尤其重要 —— `--target=amd64_sysv`
   至今没有任何测试能触发它,不造红灯就不知道修的是不是真问题。
2. **门要先验可信再用。** 本文档所有 gate 都依赖 `closure_check.sh` /
   `fixed_point.sh`,而这两个门在 `4a117a1` 之前**结构上无法翻红**
   (CI 内联拷贝的四个 SHA 全是空串;cap_test 三代全 SKIP 仍判 PASS)。
   门不可信时,「全绿」什么也不证明。

## Out of scope

- 完整 Polonius / NLL / lifetime 子类型 / reborrow(留 backlog 的 lifetime 项)
- 多架构 Cap<T> ABI(backlog 并发 cap 项)
- `.jhyynb` binary format(backlog)
- 其余 backlog 项 —— 见 [`backlog.md`](backlog.md)

## Cross-ref

- 台账:`docs/internal/workarounds.md` W-103..W-107
- 既有排期冲突:[`backlog.md` § 3](backlog.md)(Polonius)—— 本文档决策点 B/C 选项所指
- 门修复:commit `4a117a1`
- 台账登记 + 索引修复:commit `d2f5361`
- memory:`feedback_fix_evaluation_rule` / `feedback_ci_gate_must_exercise_path` /
  `feedback_verify_active_reproduces`
