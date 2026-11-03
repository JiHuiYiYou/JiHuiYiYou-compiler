# bench/ —— JHYY 基准套件

> **口径、方法学、已知偏差 ⇒ [`METHODOLOGY.md`](METHODOLOGY.md)。**
> 那一篇是"这些数字到底意味着什么"的唯一答案;本篇只讲"怎么跑"。

## 这是什么

一套**可复现**的基准测量:同一道题写两遍(一遍 C、一遍 jhyy),分别编译,
**逐字比对 stdout** 验正确性,然后比墙钟、比静态指标、比二进制体积。

参照系只有 **C**(gcc `-O0` 与 `-O2` 都报)。为什么只有 C、为什么不跟
Python/Node 比,见 [`METHODOLOGY.md` § 参照系](METHODOLOGY.md)。

## 怎么跑

```bash
# 报告模式 —— 永远 exit 0,只给人看
python bench/bench.py

# CI 门模式 —— 正确性 / 静态指标 / 二进制体积硬门;墙钟只报告
python bench/bench.py --ci

# dev 门模式 —— 墙钟也拦(本地用,共享 runner 上会假红)
python bench/bench.py --strict

# 只跑 fib(冒烟)
python bench/bench.py --quick

# 机器可读输出 / 可发布快照
python bench/bench.py --report --json tmp/bench.json
python bench/bench.py --publish --out bench/baseline/RESULTS-2026-11-03.md
#   ⚠️ 发布快照前**确认机器空闲** —— 墙钟的 run-to-run 波动可达 25%(实测),
#      有别的进程在跑时同一份代码能测出完全不同的比值。--publish 会自动多跑几轮。

# 断言这道门**看得见红**(且墙钟**不**让它红)
python bench/bench.py --selftest

# 重写静态指标基线(**必须写明理由**)
python bench/bench.py --update-baseline
```

环境变量:`JHY`(jhyy.exe 路径)· `GCC`(gcc 路径)· `RUNS`(每个程序跑几次,默认 7)
· `TOL`(静态指标容差,默认 0.02)。

## 目录

```
bench/
├── README.md              本篇 —— 怎么跑
├── METHODOLOGY.md         口径 / 参照系 / 维度定义 / 已知偏差 ⭐
├── bench.py               驱动:正确性 + 墙钟分布 + 静态指标 + 工程性指标 + 报告
├── difftest.py            随机程序差分测试器(v4.3.3 起)
├── tasks/<name>/          一道题一对源码 + 元数据
│   ├── task.c             C 参考实现
│   ├── task.jhyy          jhyy 实现
│   └── task.meta          key = value 元数据(规模 / libc 依赖 / checksum / 覆盖轴)
├── seeds/ci.txt           固定种子集(差分门的硬门用)
├── baseline/
│   ├── static.json        静态指标 + 二进制体积基线
│   └── RESULTS-<日期>.md  可发布的表格快照(带机器规格 + 提交 sha)
└── regress-cases/         已登记的差分反例
```

## 门

| 门 | id | 在哪 | 查什么 |
|---|---|---|---|
| 基准套件 | `bench-perf` | ci.yml · build-and-test | stdout 与 gcc 逐字相同 + 二进制体积不回归 + 静态指标不回归 |
| 运行时性能 | `perf` | ci.yml · build-and-test | fib/ack/nq 的静态指标不回归(墙钟只报告) |

**两份基线管的任务不重叠** ⇒ 没有"改了 A 忘了改 B"的漂移:

- `perf` 门拥有 **fib / ack / nq** 的静态指标基线
  (`scripts/dev/bench/runtime_perf.baseline.json`,v4.2.0 起就有)。
- `bench-perf` 门拥有**其余题目**的静态指标基线 + **全部题目**的二进制体积基线
  (`bench/baseline/static.json`)。
  ⇒ 体积是 `bench-perf` 带来的**新**约束 —— 此前没有任何门在管它。

**门清单的唯一真相源是 [`docs/internal/FACTS.md` § 2.2](../docs/internal/FACTS.md)**
—— 加门必须同时改那里和 `ci.yml`,漏一边 `docs-facts` 门就红。

## 加一道新题

1. 建 `bench/tasks/<name>/`,放 `task.c` + `task.jhyy` + `task.meta`。
2. **两个 twin 必须算法对等** —— 同样的算法、同样的数据结构、同样的求值顺序。
   否则比的是"手调过的 C" vs "朴素 jhyy",不是代码生成质量。
3. `task.meta` 至少写 `libc`(这道题有多少落在 libc 上)与 `checksum`
   (反死代码消除:优化器把计算吃掉 ⇒ checksum 消失 ⇒ 门红)。
4. ⚠️ **题目要够长**:测量地板约 20ms(见 [`METHODOLOGY.md` § 测量地板](METHODOLOGY.md))
   ⇒ 跑起来不到 ~150ms 的题,地板占比会超过 25% ⇒ 表里被标 `*` ⇒ **比值不可靠**。
   跑 `python bench/bench.py --report` 看 `floor%` 那一列,太高就加规模。
5. 跑 `python bench/bench.py --update-baseline` 把新题进基线,**并在 commit 里写明理由**。
6. ⚠️ 浮点题另有一条规矩:比对用 **IEEE-754 位模式**,且**只与 gcc `-O0` 的产物比**
   —— `-O2` 可能重排浮点运算。细节见 [`METHODOLOGY.md` § 浮点](METHODOLOGY.md)。

## 表里那些列是什么

| 列 | 是什么 |
|---|---|
| `jhyy/O0` `jhyy/O2` | **扣掉测量地板后**的比值 ⇒ 程序自身的工作之比(头条数字) |
| `raw O0` | 不扣地板的原始比值 ⇒ 含启动开销 ⇒ 用户体感 |
| `floor%` | 测量地板占这道题运行时间的比例 ⇒ **>25% 的题带 `*`,比值不可靠** |
| `min/med/p95` | jhyy 产物的墙钟分布(原始值,不扣地板) |
| `insn` `mem` `chk` | 静态指标(指令数 / 访存指令数 / `___chkstk_ms` 次数)—— **确定性 ⇒ 硬门** |
| `size` | 产物的字节数 |
| `libc` | 这道题有多少落在 libc 上(`none` / `malloc` / `libm`) |

## 不做什么

- **不做跨语言对比**(只对 C)。
- **不做 IO 题** —— jhyy 的 stdout 是无缓冲的,大量输出会退化成 syscall 瓶颈。
- **不测标准库** —— 本套件测的是**代码生成**。
- **不用 hyperfine / BenchExec** —— 本仓的计时路径在 MSYS2 下已被实测证明更可靠。

## 复现别人的数字

`bench/baseline/RESULTS-<日期>.md` 里带完整的机器规格(OS / CPU / gcc 版本 /
jhyy 版本 / 提交 sha)。在**同一台机器**上跑 `python bench/bench.py --report`,
应当得到同一量级的相对倍数。**跨机器的绝对数字不可比** —— 只比同环境内的相对倍数。
