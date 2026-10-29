# 自研后端运行时性能基线 —— 2026-10-29 实测

> 这份文档补上 [`JHYY自研后端pass查缺报告.md`](../plans/v4/JHYY自研后端pass查缺报告.md)
> §4.2 说的「**这个项目到目前为止没有做过一次运行时性能测量**」——
> 那句话**不准确**:`compiler/tests/bootstrap/bench.sh` 存在(v4.0.0),
> 但**它的计时器是坏的**,而且不在 CI ⇒ 等于没有测量。
> 本文档是**第一份可信的基线**。

**审计对象**:`JiHuiYiYou-compiler` main @ `ca4aaa3`(v4.1.2 发布 commit)
**测量机**:Windows 10 19045 · gcc 15.2.0(MSYS2 ucrt64)· MinGW 工具链
**测量工具**:`scripts/dev/bench/runtime_perf.py`(本轮新增)

---

## 一、为什么必须换掉 bench.sh 的计时器

| 问题 | 实测证据 |
|---|---|
| MSYS2 的 `date +%s.%N` 不可靠 | `sleep 1.0` 被量成 **1.445 ~ 1.756 秒**(误差 45%~76%) |
| `bench.sh` 的计时器正是用它 | `bench.sh:174-178` 的 fallback 路径 |
| `/usr/bin/time` 的输出被重定向吞掉 | `bench.sh:171`:`t=$(/usr/bin/time -f "%e" "$prog" > /dev/null 2>&1; ...)` —— `2>&1` 把 time 的 stderr 也丢了 ⇒ `t` 恒为空 ⇒ **每次都走那条坏路径** |
| MSYS2 bash 里 spawn Windows exe 开销巨大 | bench.sh 量 gcc -O2 的 fib = **197ms**;真实值 **55ms** |
| bench.sh **不验正确性** | 只计时;程序输出全错也算「跑成功」 |

⇒ `bench.sh` 的历史数字(v4.0.0-rc1 记的 fib 1.399x / ack 0.596x / nq 1.020x)
**不可信,不应作为基线引用**。

---

## 二、基线数字

`runtime_perf.py`(CPython `perf_counter` → Win32 QueryPerformanceCounter;
min-of-7;输出先逐字比对 gcc 产物,不一致直接 FAIL):

| 程序 | gcc -O0 | gcc -O1 | gcc -O2 | **jhyy** | jhyy/gcc-O0 | jhyy/gcc-O2 |
|---|---|---|---|---|---|---|
| **fib** | 89.7ms | 72.4ms | 55.5ms | **307.9ms** | **3.43x** | 5.55x |
| **ack** | 28.5ms | 25.4ms | 22.9ms | **134.7ms** | **4.73x** | 5.89x |
| **nq**  | 20.4ms | 19.9ms | 19.1ms | **32.0ms**  | 1.57x | 1.67x |

静态指标(从生成的 `.s` 统计):

| 程序 | 指令数 | 访存指令数 | 访存占比 | 函数数 | 帧最小/中位 | chkstk |
|---|---|---|---|---|---|---|
| fib | 74 | 36 | **49%** | 2 | 8368 / 8384 | 2 |
| ack | 99 | 52 | **53%** | 2 | 8352 / 8400 | 2 |
| nq  | 322 | 223 | **69%** | 3 | 8496 / 8528 | 3 |

### 参照系该用 gcc -O0,不是 gcc -O2

fib / ack / nq 这三个程序 **gcc -O0 ≈ gcc -O2**(89.7 vs 55.5 / 28.5 vs 22.9 /
20.4 vs 19.1)—— 它们的成本被**递归调用开销**主导,优化 pass 帮不上什么忙。

⇒ 差距(3.43x / 4.73x)**几乎全部来自 codegen 质量**,不是「缺优化 pass」。
⇒ `bench.sh` 的 `THRESHOLD=1.1` 对 gcc -O2 是个**不可达门槛**(gcc 自己都达不到),
对 gcc -O0 才是有意义的尺子。**v4.2.0 把参照系改成 gcc -O0。**

⚠️ 但这**不能**推广到「jhyy 只需要追平 gcc -O0」。用户写的真实程序(循环、
数组、浮点)上 gcc -O2 ≫ gcc -O0。**-O0 是「codegen 质量」的下限,
-O2 是「用户体感」的目标。** 两者都要,分阶段。

---

## 三、帧尺寸消融实验(本轮最重要的发现)

**问题**:`codegen_amd64_emit_ctrl.jhyy:565` 写死
`alloc_pool_size = (8192 as i64) + pfa_v` ⇒ **每个函数的帧至少 8352 字节**,
与该函数实际用几个 temp 无关。

**自举产物实测**(`compiler/src0/main.s`,v4.1.2,10.4 MB):

```
prologue frames=1045   chkstk calls=1045
  min=8352  median=8368  p90=9440  max=237680
  over4096=1045 (100%)   >=8192=1045 (100%)
```

⇒ **100% 的函数帧 > 4096** ⇒ Windows ABI 规定必须探页 ⇒
**100% 的函数每次调用都走一次 `___chkstk_ms`**。

**消融**(手工改 `fib_jhyy.s` 后重链,Python `perf_counter` 计时):

| 变体 | fib | 相对现状 |
|---|---|---|
| A 现状:8384 帧 + chkstk | 335ms | — |
| B 128 帧 + chkstk 保留 | 277ms | **-17%** |
| C 128 帧 + 无 chkstk | **197ms** | **-41%** |
| (参照) gcc -O0 | 98ms | |
| (参照) gcc -O2 | 62ms | |

**结论**:
- **帧尺寸本身** 贡献 **~17%**(8KB 栈的 cache 污染)
- **`___chkstk_ms` 每次调用的探页** 贡献 **~24%**
- 合计 **~41%**,来自**一个公式常量**
- 修完后仍差 gcc -O0 **2.0x** —— 那一截是**栈槽模型**的
  load/store 流量(49% 的指令是访存),**只有寄存器分配器能动**。

> ⚠️ 早期用 shell 计时做的同一实验得出「帧尺寸无影响」的**错误结论** ——
> 那个测量的噪声(±300ms)完全淹没了信号。**perf 测量必须用可信时钟。**
> 这条已写进 `runtime_perf.py` 的文档串。

---

## 四、修法(交给 v4.2.1)

```
现状:  alloc_pool_size = 8192 + per_fn_alloc
应为:  alloc_pool_size = 32 + (local_max+1)*8 + per_fn_alloc
```

`local_max` 是**该函数精确已知**的 local temp 上限
(`emit_ctrl.jhyy:544`,由 `per_fn_max[cur] - per_fn_max[cur-1]` 得出),
而 8192 是「公式 temp 池最深到 -32792」的**旧 4096-temp 时代**遗留的固定预留
(`state.jhyy:1153` 的注释自陈)。

**风险与对策**:

| 风险 | 对策 |
|---|---|
| pre-scan `per_fn_alloc` 低估 ⇒ 池长出帧外 ⇒ 静默踩坏栈 | 该估算**自带余量**(`total_a + max(total_a/2, 8, 64-bit binop 数)*8`,`state.jhyy:2148`),不是裸和;**再加一条响亮失败**:函数体 emit 完检查池底没越过预留边界,越了直接编译失败(沿用 W-120 / W-130 的「响亮失败远好过静默错代码」规矩) |
| 帧变小后暴露原本被大帧意外撑住的越界 | 全量 regress + 自举闭环 + `artifact_checks.sh` 14 条门全绿才算过 |
| `artifact_checks.sh` 的 `per_fn_frame` 门断言 f500 vs f1099 帧比 < 4 | 帧变小后比值只会更稳;但**门要重新验一次**(造红灯) |

**新增常驻门**(建议):`artifact_checks.sh frame_bloat` ——
断言「真实函数帧的中位数 < 1KB」且「`___chkstk_ms` 调用数 == 0」。
这条门直接锁死本轮的收益,防止将来回退。

---

## 五、复现

```bash
# 报告模式(永远 exit 0)
python scripts/dev/bench/runtime_perf.py

# dev 门模式(墙钟 + 静态指标,超阈值 exit 1)
python scripts/dev/bench/runtime_perf.py --strict

# CI 门模式(**只**静态指标硬门;墙钟只报告)
python scripts/dev/bench/runtime_perf.py --ci

# 只跑 fib(冒烟)
python scripts/dev/bench/runtime_perf.py --quick

# 重写静态指标基线
python scripts/dev/bench/runtime_perf.py --update-baseline
```

**环境**:MSYS2 python 无 pip;`scripts/dev/bench/runtime_perf.py` 只用标准库,
但 **`time.perf_counter` 需要 CPython**(MSYS2 的 python 也行,只要是 CPython)。
本机推荐 `C:\Users\liuzhen\miniconda3\python.exe`
(per `env_python_with_pytest` 这条 memory 记录)。

---

## 六、CI 门(v4.2.0 已接)

**硬门 = 静态指标**,不是墙钟。

| 指标 | 为什么能当硬门 |
|---|---|
| 指令数 / 访存数 | 「源码 × 编译器」的**确定性函数** ⇒ 跨机器跨 runner 逐字节相同 |
| 帧大小(min/med/max) | 同上;且**变大就是变差**(帧越大 ⇒ 摸的栈越多 ⇒ 越慢) |
| `___chkstk_ms` 次数 | 同上;**归零后不允许再出现** |

**墙钟为什么不能当硬门**:同一个 gcc -O2 的 fib 在本地连续几轮量出
2.27x / 3.46x / 4.42x / 4.65x —— 噪声比信号大一个数量级
(宿主负载 + MSYS2 里 spawn Windows exe 的开销)。
⇒ `--ci` 模式墙钟**只报告**,进 job summary 给人看趋势。

**基线文件**:`scripts/dev/bench/runtime_perf.baseline.json`
(容差 2% = `TOL`;基线为 0 的指标上限也是 0 ⇒ chkstk 归零后任何 >0 都红)。

⚠️ **更新基线必须写明理由** —— 它锁的是「**已经拿到的收益**」,不是「现状」。
v4.2.1 修完帧尺寸后基线会**大幅下降**(帧 8384 → 几百字节、chkstk 2 → 0),
那时更新基线 = 把收益锁进去。

**红光测试已做**(per `feedback_ci_gate_must_exercise_path`):
把基线的 `fib.insn` 从 74 改成 70 ⇒ `--ci` 当场 exit 1 并报
`fib.insn: 74 > 基线 70 的 102% 上限 71.4` ⇒ 还原 ⇒ exit 0。

**CI 接线**:`.github/workflows/ci.yml` 的 `build-and-test` job,
「运行时性能门(静态指标硬门 + 墙钟报告)」步,排在 `artifact_checks.sh` 之后。

**`compiler/tests/bootstrap/bench.sh` 现在的角色**:**入口别名** ——
不再自己实现计时(它的计时器是坏的,见 § 一),全部委托给 `runtime_perf.py`。
旧的 `bash bench.sh --report|--strict` 调用方式与退出码不变。

---

## 七、v4.2.1 已落地:帧尺寸修复后的实测

**改法**(`codegen_amd64_emit_ctrl.jhyy`):

```
alloc_pool_size = 8192 + per_fn_alloc
⇒ alloc_pool_size = 32 + (local_max+1)*8 + per_fn_alloc
```

`local_max` 是**该函数精确已知**的 local temp 上限(不是全局上限)⇒ 帧终于按需算。

### 静态指标(确定性 ⇒ 可直接比)

| 程序 | insn | mem | frame_med | chkstk |
|---|---|---|---|---|
| fib | 74 → **70** | 36 → 36 | 8384 → **320** | 2 → **0** |
| ack | 99 → **95** | 52 → 52 | 8400 → **400** | 2 → **0** |
| nq  | 322 → **316** | 223 → 223 | 8528 → **592** | 3 → **0** |

### 墙钟(只作参考,跨机器会漂)

| 程序 | 修前 jhyy/gcc-O0 | 修后 jhyy/gcc-O0 |
|---|---|---|
| fib | 3.46x | **2.14x** |
| ack | 4.65x | **2.13x** |
| nq  | 1.45x | 1.40x |

### 编译器自己的产物(1045 个真实函数)

| | 修前 | 修后 |
|---|---|---|
| 帧 min / 中位 | 8352 / 8368 | **208 / 288** |
| 帧 max | 237680 | 349232 ← 大函数**余量更足**(见下) |
| 总预留栈 | 9.1 MB | **1.5 MB** (-84%) |
| 帧 >4096 的函数 | 1045 (100%) | **46 (4.4%)** |
| `___chkstk_ms` 调用 | 1045 (100%) | **46 (4.4%)** |
| 最紧函数的余量 | 2664 B(`parser__parse_expr`) | 14584 B(同一个函数) |
| 自举编译耗时 | 6676ms | **5605ms** (-16%) |

⚠️ **帧 max 变大了,但不是变紧** —— 旧公式用 `max((local_max+1)*8, 8192+pfa_v)`,
在公式池主导时**把 `per_fn_alloc` 那一项丢掉了** ⇒ 值池向下生长不受帧保护
(旧产物里 `parser__parse_expr` 只剩 2664 字节余量)。新公式把两项**相加**
⇒ 大函数现在余量更足。这是**顺手修掉的一个潜在下溢**。

台账:**W-167**(RESOLVED 2026-10-29,v4.2.1)。

---

## Cross-ref

- 计划:[`../plans/v4/self-backend-perf-plan.md`](../plans/v4/self-backend-perf-plan.md)
- 旧报告(部分结论已过时):[`../plans/v4/JHYY自研后端pass查缺报告.md`](../plans/v4/JHYY自研后端pass查缺报告.md)
- 计时器已修的 bench(现在是入口别名):[`compiler/tests/bootstrap/bench.sh`](../../compiler/tests/bootstrap/bench.sh)
- 测量脚本:`scripts/dev/bench/runtime_perf.py`
- 静态指标基线:`scripts/dev/bench/runtime_perf.baseline.json`
