# 自研后端性能线 —— v4.2 及以后的排期

**状态:** 🔄 **2026-10-29 立线**。v4.2 起的主线 = **自研后端性能线**
(2026-10-29 user 拍板:「自研后端性能线为主线」,语言特性链整体后移)。

**定位:** 自研后端**就是编译器本身** —— `compiler/src/*.c` 已于 v4.0.21 删光,
`jhyy.exe` 由它自己编 `src0/main.jhyy`(自举)。所以后端性能不是「锦上添花」,
它直接乘在两件事上:① 项目自己的迭代速度(自举编译 **12.5s**);
② 用户写的每一个 jhyy 程序。

**起点:** [`docs/perf/self-backend-baseline-2026-10-29.md`](../../perf/self-backend-baseline-2026-10-29.md)
—— 第一份**可信**的运行时基线(旧 `bench.sh` 的计时器是坏的)。

---

## 〇、复核:旧报告哪些结论还站得住

[`JHYY自研后端pass查缺报告.md`](JHYY自研后端pass查缺报告.md)(2026-10-25 审计 v2.x 快照)
**仍然成立**:

- regalloc 实现**未接线**(`codegen_amd64.jhyy:380-383` 仍是注释掉的)
- peephole 的 4096 字节跳过仍在(`codegen_amd64_peephole.jhyy:545`)
- peephole 只剩 3 条 no-op 级规则(Rule 3 已删)
- 16 个 QBE pass 里 14 个缺失
- 自研后端自 v3.1.0 起是**唯一生产路径**

**已被本轮复核推翻 / 订正**:

| 旧报告的说法 | 本轮实测结论 |
|---|---|
| §5 P1「接上 regalloc 是最高杠杆的一改」 | **推翻**。它是 prototype 不是「差一根线」:无 CFG、无函数边界、无 call-clobber 处理、无寄存器类、无 spill/reload 插入;`MAX_TEMPS=64` 对真实 60656 个 temp;寄存器侧 API **零调用点**。成本被低估约一个数量级 |
| §4.2「从没做过运行时性能测量」 | `bench.sh` 存在但**计时器是坏的**且不在 CI ⇒ 等于没测。基线见上文 |
| §4.3「IL buffer 4MB cap」 | 那是已废弃的文件读路径;生产走 in-mem + 8MB arena |
| §3「byte-equal 与优化互斥,必须先决策」 | **假两难**。没有任何门拿硬编码 sha 比对 —— 全是运行时算 sha 比「同一编译器的两次运行」。**不需要先决策** |
| §4.1 估算「当前落在 QBE 的 30–50%」 | 无数据支撑,且参照系选错(见下) |

**旧报告漏掉的、本轮新增的两条**:

1. **每个函数的帧至少 8352 字节**(`emit_ctrl.jhyy:565` 的写死常量 8192)
   ⇒ **100% 的函数每次调用都走 `___chkstk_ms` 探页** ⇒ **实测 ~41% 的运行时**
2. **CLI 根本没有 `-O` 开关**(只有 `-o` / `--target=`)

---

## 一、基线(2026-10-29 实测)

| 程序 | gcc -O0 | gcc -O2 | **jhyy** | jhyy/gcc-O0 | 访存指令占比 |
|---|---|---|---|---|---|
| fib | 89.7ms | 55.5ms | **307.9ms** | **3.43x** | 49% |
| ack | 28.5ms | 22.9ms | **134.7ms** | **4.73x** | 53% |
| nq  | 20.4ms | 19.1ms | **32.0ms**  | 1.57x | 69% |

**参照系 = gcc -O0**,不是 gcc -O2 —— 这三个程序 gcc -O0 ≈ gcc -O2
(递归调用开销主导),所以差距几乎全在 codegen 质量而非优化 pass。
`bench.sh` 那个 `1.1x` 对 gcc -O2 的门槛**不可达**(gcc 自己都达不到)。

⚠️ 但 **-O0 只是下限**:真实用户程序(循环/数组/浮点)上 gcc -O2 ≫ gcc -O0。
**v4.2 的目标是把 3.4x 拉到 2x 以内;v4.4 的目标是让 1x 成为可达的长期目标。**

---

## 二、版本序列

```
v4.2 ── 性能基线可信化 + 帧尺寸修复 + peephole 解封
  ├─ v4.2.0  可信性能门(脚本已落地,待接 CI)
  ├─ v4.2.1  帧尺寸公式修复          ← ~41% 运行时,单点改动
  └─ v4.2.2  peephole 4096 限制真修   ← 不修,后面所有 .s 级 pass 都无从验证
v4.3 ── IR 层优化框架 + -O 开关
  ├─ v4.3.0  -O0/-O1 开关 + IR pass 框架(常量折叠/代数化简/DCE/不可达消除)
  └─ v4.3.1  artifact_checks.sh 去文本耦合(为 v4.4 的 codegen 大改铺路)
v4.4 ── 真寄存器分配器(4 个子版本,多 sprint 工程)
  ├─ v4.4.0  per-fn 作用域 + CFG + 真活跃区间
  ├─ v4.4.1  call-clobber + 寄存器类(GPR/XMM)+ MAX_TEMPS 动态化
  ├─ v4.4.2  spill/reload 插入 + 帧布局重算
  └─ v4.4.3  emit_mem/emit_ctrl/emit_call 改造 + phi 改并行移动(含环打破)
v4.5 ── M5 Part 3(0-C 闭环)  ← 前置 = v4.2 + v4.4
v4.6+ ─ 语言特性链(lifetime → closure → dyn Trait → HKT)
```

---

## 三、逐版范围

### v4.2.0 —— 可信性能门

**为什么先做**:后面每一版都要用「性能有没有变好」当验收判据。
判据不可信 ⇒ 后面全是盲改。

| 交付 | 状态 |
|---|---|
| `scripts/dev/bench/runtime_perf.py` | ✅ **已落地并验证**(输出逐字比对 gcc 产物;min-of-7;附静态指标:指令数/访存数/帧尺寸/chkstk 次数) |
| `compiler/tests/bootstrap/bench.sh` 的计时器 | ✅ **已改成入口别名** —— 不再自己实现计时(它的计时器是坏的:MSYS2 的 `date +%s.%N` 把 `sleep 1.0` 量成 1.45~1.76 秒),全部委托 `runtime_perf.py`;旧的 `--report`/`--strict` 调用方式与退出码不变 |
| CI 接线 | ✅ **已接**(`ci.yml` 的 `build-and-test` job,排在 `artifact_checks.sh` 之后) |
| 静态指标进门 | ✅ **已是硬门** —— 基线 `scripts/dev/bench/runtime_perf.baseline.json`,容差 2%;墙钟**只报告**(共享 runner 噪声大:同一个 fib 连续几轮量出 2.27x/3.46x/4.42x/4.65x) |

**gate**: 门**造过红灯**才算门(per `feedback_ci_gate_must_exercise_path`)
—— ✅ 已做:基线的 `fib.insn` 74 → 70 ⇒ `--ci` 当场 exit 1 并报
`fib.insn: 74 > 基线 70 的 102% 上限 71.4`;还原 ⇒ exit 0。

**不改编译器** ⇒ 零回归风险。

**⚠️ 为什么墙钟不进硬门**:GitHub 共享 runner 的宿主负载不可控,墙钟噪声比信号大
一个数量级 ⇒ 拿它当硬门只会制造假红,而「恒红且被忽略的步骤比没有门更糟」
(本项目栽过这个坑,见 `artifact_checks.sh` 步的注释)。
**静态指标是「源码 × 编译器」的确定性函数** ⇒ 跨机器不漂 ⇒ 才是能当硬门的东西。

### v4.2.1 —— 帧尺寸公式修复 ⭐

**改动**(`codegen_amd64_emit_ctrl.jhyy:565`):

```
现状:  alloc_pool_size = 8192 + per_fn_alloc
改为:  alloc_pool_size = 32 + (local_max+1)*8 + per_fn_alloc
```

`local_max` 是该函数**精确已知**的 local temp 上限(`emit_ctrl.jhyy:544`);
8192 是「公式池最深 -32792」的**旧 4096-temp 时代**遗留常量
(`codegen_amd64_state.jhyy:1153` 自陈)。

**预期收益**:fib **-41%**(实测消融:8384 帧 + chkstk = 335ms → 128 帧无 chkstk = 197ms);
自举产物 **1045 个函数全部**从 ≥8352 字节降到几百字节 ⇒ **`___chkstk_ms` 归零**。

**风险与对策**:

| 风险 | 对策 |
|---|---|
| pre-scan `per_fn_alloc` 低估 ⇒ 池长出帧外 ⇒ 静默踩坏栈 | 该估算**自带余量**(`total_a + max(total_a/2, 8, 64-bit binop 数)*8`,`state.jhyy:2148`);**再加响亮失败**:函数体 emit 完检查池底未越过预留边界,越了直接编译失败(沿用 W-120 / W-130 的规矩) |
| 帧变小后暴露原本被大帧意外撑住的越界 | 全量 regress + 自举闭环 + `artifact_checks.sh` 14 条门全绿 |
| `per_fn_frame` 门(f500 vs f1099 帧比 < 4)语义变化 | 重新验 + 造红灯 |

**新增常驻门** `artifact_checks.sh frame_bloat`:断言「真实函数帧中位数 < 1KB」
且「`___chkstk_ms` 调用数 == 0」—— **直接锁死本轮收益,防回退**。

**gate**: 全量 regress 绿 + 自举闭环绿 + `artifact_checks` 绿 + **perf 数字改善 ≥ 30%**
+ `make` 后 `git add compiler/build/bin/jhyy.exe`(CI 的 artifact-fresh 步会比对它)。

#### ✅ 完成记录(2026-10-29,台账 W-167)

**改法**(`codegen_amd64_emit_ctrl.jhyy`):
```
alloc_pool_size = 8192 + per_fn_alloc
⇒ alloc_pool_size = 32 + (local_max+1)*8 + per_fn_alloc
```
`local_max` 是**该函数精确已知**的 local temp 上限(`per_fn_max[cur] - per_fn_max[cur-1]`)
⇒ 帧终于按函数实际需要算。

**实测(自举产物 1045 个真实函数)**:

| | 修前 | 修后 |
|---|---|---|
| 帧 min / 中位 | 8352 / 8368 | **208 / 288** |
| 总预留栈 | 9.1 MB | **1.5 MB** (-84%) |
| 帧 >4096 / chkstk 调用 | 1045 / 1045(100%) | **46 / 46(4.4%)** |
| 最紧函数的余量 | 2664 B | **14584 B** |
| fib / ack jhyy/gcc-O0 | 3.46x / 4.65x | **2.14x / 2.13x** |
| 自举编译耗时 | 6676ms | **5605ms** (-16%) |

⚠️ **帧 max 变大(237680 → 349232)但不是变紧** —— 旧公式用 `max(...)`,
在公式池主导时**把 `per_fn_alloc` 丢掉了** ⇒ 值池向下生长不受帧保护
(`parser__parse_expr` 只剩 2664 字节余量)。新公式把两项**相加**
⇒ **顺手修掉一个潜在下溢**,大函数现在余量更足。

**门(新增两条,都验过红灯)**:
- `artifact_checks.sh frame_bloat` —— 修之前**必然红**(报「小函数的帧 8384B > 1024B」)
- `artifact_checks.sh frame_slots` —— 每个 rbp 相对槽位必须落在该函数的帧内
  (修之前就该是绿的 —— 已验;它是「帧算小的安全网」)

**验收(全绿)**:

| 门 | 结果 |
|---|---|
| `regress jhyy.exe` | ✅ **257 PASS + 0 XFAIL + 0 failed + 20 SKIP**(277 total,与修前基线一致) |
| `artifact_checks.sh` | ✅ **16 PASS / 0 KNOWN-FAIL / 0 FAIL / 0 SKIP**(14 → 16,多的两条是本版新增) |
| `closure_check.sh` | ✅ PASS(v2.s == v3.s,sha `8f706fe76d5fc0b7`) |
| `fixed_point.sh` | ✅ **17 PASS / 0 FAIL / 0 INFO**(N=10) |
| `make`(自举闭环门) | ✅ 第 2 代收敛(**过渡期自动消化** —— W-147 的「迭代到不动点」) |
| perf 静态基线 | ✅ 已更新并锁住收益(insn 74→70 / frame_med 8384→320 / chkstk 2→0) |

> ⚠️ **自举闭环的过渡期**:第 1 代(旧公式编新源码)与第 2 代(新公式编新源码)
> 产物必然不同 ⇒ 门**推进锚点一代**后收敛 —— 这正是 W-147 把门从「验锚点」
> 改成「迭代到不动点」的意义,不需要任何 escape hatch。

### v4.2.2 —— peephole 4096 限制真修

**为什么**:`.s` 超过 4096 字节就整段跳过 peephole(`peephole.jhyy:545`)。
真实程序(自举产物 10.4MB)永远跳过 ⇒ **peephole 只在 hello-world 级输入上跑过**。
不修这条,v4.4 之后任何 .s 级 pass 的验证都缺一个可信的 .s 级工具。

**根因**: `peephole_concat_loop` 静默崩(W-074.6.1 PARTIAL)。
**gate**: 自举产物的 `.s` 上 peephole 真的跑了(可观测:fold 计数 > 0),且回归不退步。

### v4.3 —— IR 层优化框架 + `-O` 开关

**为什么是 IR 层而不是 .s 层**:IR 已经是 SSA(前端产的);在 IR 层做 pass
⇒ temp 数下降 ⇒ **帧进一步变小**(与 v4.2.1 叠加),而且是「少算」而不是
「算得更巧」—— 对一个 3.4x 的差距,少算比算巧更值钱。

**内容**:

- `-O0`(默认) / `-O1` 开关 —— **CLI 现在完全没有 `-O`**。
  默认保持 `-O0` ⇒ 现有 byte-equal 门全部保持绿,零风险。
- IR pass 框架 + 常量折叠 / 代数化简 / DCE / 不可达代码消除
  = backlog 第 8 项按新设计重做(原设计假设「后端已有 peephole 兜底」,已过时)

**gate**: `-O1` 与 `-O0` 语义等价(同一组用例输出逐字相同);
优化后 `.s` 长度 ≤ 不优化 +5%;**`-O0` 必须仍 byte-equal**。

### v4.3.1 —— `artifact_checks.sh` 去文本耦合

**为什么现在做**:这 14 条门里有 4 条是**汇编文本断言**
(`holds_bitmap` 认死 `%r8` + `%tN` 注释格式;`sysv_memory_class` 认死
`movq %r10, 0(%rsp)`;`sysv_arg_spill` 认死 `r8d`/`r9d`/`16(%rbp)`;
`per_fn_frame` 认死 `subq $N, %rsp` 的形状)。

v4.4 的寄存器分配器会**同时**改寄存器名、栈槽编号、帧布局 ⇒ 这 4 条会红
⇒ 需要手工改门 ⇒ 改门和改后端混在一起会掩盖真实回归。

**做法**:能改成语义判定的改语义判定(例如「base temp id > 65536」
而不是「某一行含 `, %r8`」);改不动的登记成 expected-FAIL 风格。

### v4.4 —— 真寄存器分配器

**这是本线的重头戏,也是旧报告估得最不准的一项。**
`regalloc.jhyy` 的 972 行里,真正可复用的是 **~375 行算法**
(区间构造 + 确定性贪心分配);另外 ~400 行是常量表 / 结构体访问器 / 寄存器名表。
**hard 90% 未实现**:

| 子版本 | 内容 |
|---|---|
| **v4.4.0** | per-fn 作用域(切 token 流 + 对齐 `per_fn_base_t`)+ **真 CFG** + 真活跃区间(现在只是「token 序号区间」,跨基本块、跨函数全乱)+ phi 边处理 |
| **v4.4.1** | **call-clobber**:调用点切区间,跨调用值只给 callee-saved(现在 caller-saved 寄存器随便发 —— `regalloc.jhyy:596-605`)+ 寄存器类(GPR vs XMM)+ `MAX_TEMPS=64` 动态化(真实 temp 空间到 60656) |
| **v4.4.2** | spill/reload **插入**(现在只记 `spill_off`,不生成 store/load 对)+ 帧布局重算(spill slot 与 home slot 共存) |
| **v4.4.3** | emit 改造:`emit_mem`/`emit_ctrl`/`emit_call` 消费寄存器(**每个 temp 仍需 home slot** —— 不是「从寄存器读代替从槽读」这么简单)+ **phi 解析改成并行移动**(现在是 slot-based 顺序 copy,`emit_call.jhyy:1167`,寄存器化后必须做并行赋值 + 环打破) |

**gate**: 每子版本独立可 ship;`artifact_checks` 的 4 条文本耦合门在 v4.3.1
之后不再拦路;全量 regress + 自举闭环 + perf 数字每版记录。

### v4.5 —— M5 Part 3(0-C 闭环)

**M5 的现状**:Part 1(删 `compiler/src/*.c`)✅ v4.0.21 已做;
Part 2(untrack QBE)✅ v3.1.0 已做;
**Part 3(删 `compiler/runtime/runtime.c` + `compiler/src0/jhyy_helpers.c` 的
用户侧 runtime)⬜ 唯一剩余**;Part 4(工具链自含闭环验证)部分。

**为什么排在性能线之后**(2026-10-29 论证):

1. **M5 Part 3 是把成熟的 C runtime 换成新写的 jhyy 代码。**
   `runtime.c` + `jhyy_helpers.c` 现在给每个用户程序提供 malloc / memcpy /
   printf / exit。删掉它们 ⇒ 这些改走 **jhyy 侧的实现**
   (`std/arena.jhyy`、`std/mem.jhyy`、`std/fmt.jhyy`、`std/os.jhyy` 已存在)。
   ⇒ **在一个已经比 gcc -O0 慢 3.4~4.7x 的后端上,再叠一层新写的、同样慢的代码。**
2. **先修后端,M5 Part 3 的成本才可控** —— 而且只有先有性能门,
   才能写出「0-C 闭环后程序不得比 0-C 前慢 > X%」这条真正有意义的门。
3. **寄存器分配器直接受益** —— std lib 的热路径(arena 分配、memcpy)
   拿到寄存器分配后,M5 Part 3 的性能代价会小得多。

**新增门**:「0-C 闭环后,同一组用例的运行时不得比 0-C 前慢 > 阈值」。

⚠️ **注意方向张力**:W-103 往 `jhyy_helpers.c` 加了 5 个 libc bridge,
M5 Part 3 要删 C runtime。**取舍**:真的 0-C 时换掉的是**bridge 的实现**
(改 syscall),`std/os.jhyy` 的 `std_os_*` 一行不动(台账 W-103 已记)。

### v4.6+ —— 语言特性链

`lifetime → closure → dyn Trait → HKT`(强串行链)+ async / const generic /
错误恢复 / 包管理器 / 并发 cap / `.jhyynb`。
**整体后移到性能线之后** —— 但注意它们与性能线**正交**,一旦性能线的主干
(v4.2 + v4.4)落地,两条线可以并行。

---

## 四、与 12 项 backlog 的关系

| backlog 项 | 处置 |
|---|---|
| 1 M5 工具链闭环 | Part 1/2 已完成;**Part 3 = v4.5**;Part 4 并入 v4.5 |
| 8 基本优化 pass | **重做** = v4.3(设计前提已过时:原方案假设「后端有 peephole 兜底」) |
| 2/3/4/5/6/7/9/10/11/12 | 保持 backlog 原范围,**排到 v4.6+** |

⇒ backlog 的依赖图(以 M5 为根)**已经过期**:M5 只剩 Part 3,且它是 v4.5。
`docs/plans/v4/backlog.md` 需同步。

---

## 五、明确不做的

- **不做向量化 / SIMD** —— 寄存器分配都没接上就加 SIMD 是「在漏水的船上刷漆」
- **不做 `-O2` / `-O3` / PGO / LTO** —— v4.3 只做 `-O1`
- **不重写 `regalloc.jhyy`** —— 复用它的贪心分配核心,重写的是它周围缺失的 90%
- **不改默认优化级别** —— 默认保持 `-O0`(现有 byte-equal 门全绿)
- **不碰 `artifact_checks.sh` 的判据语义**,直到 v4.3.1 专门处理

---

## 六、每版的 ship 动作(不变)

1. 改 → 全量 regress → 自举闭环 → `artifact_checks` → perf 数字
2. `make` 后 `git add compiler/build/bin/jhyy.exe`(CI 的 artifact-fresh 步会比对它)
3. 往 [`version-schedule.md`](version-schedule.md) 记实际做完的内容
4. 往 [`../internal/workarounds.md`](../../internal/workarounds.md) 登记新发现的 workaround

> ⚠️ **改 codegen 不会让任何 sha 基线变红** —— 所有门都是运行时算 sha 比两次运行。
> 真正会红的是 `artifact_checks.sh` 的 4 条汇编文本断言(v4.3.1 处理)和
> 需要重新提交 `jhyy.exe` 这件事。

## Cross-ref

- 基线数据:[`../perf/self-backend-baseline-2026-10-29.md`](../../perf/self-backend-baseline-2026-10-29.md)
- 测量脚本:`scripts/dev/bench/runtime_perf.py`
- 旧报告(部分结论已订正):[`JHYY自研后端pass查缺报告.md`](JHYY自研后端pass查缺报告.md)
- 排期表(版本号权威):[`version-schedule.md`](version-schedule.md)
- backlog:[`backlog.md`](backlog.md)
