# 活跃 workaround 清零 — v4 发版前必须真修的 14 条

**状态:** ✅ **2026-10-20 完成 —— ACTIVE 桶清零(14 → 0)**,promote 条件全部满足

> 🎉 **本文档的目标已达成。** 台账 108 行:102 RESOLVED + 4 SUPERSEDED + 2 INVALID
> + **0 ACTIVE** + 0 DEFERRED。promote 条件的实测见
> [`version-schedule.md`](version-schedule.md) § v4.0.19。
>
> **下面保留整份文档作为审计轨迹** —— 每条 workaround 当时是怎么定位的、用了什么
> 修法、造了什么红灯,都在原处 ✓。**「怎么修」已经不重要了;重要的是「修了什么、
> 凭什么说修好了」** —— 而后者全在台账的 RCA 段里 ✓。
>
> **本文档最值钱的一段沉淀**(W-106 那条):「删掉 X ⇒ 偶发失败 ⇒ X 承重」这个
> 推理链**只在一个前提下成立** —— 那个偶发失败是**由 X 引起的**。W-106 那次不是
> (X 只改变了时序,让另一个 bug 撞上了)⇒ **「删掉试试」的实验必须配合「失败症状的
> 归因」**:症状是「**compile failed**」→ 指向「编译过程本身出了问题」(临时名 /
> 旁路文件 / 并发);症状是「算错」→ 指向「生成的代码有问题」⇒ 方向完全不一样 ✓。

**历史状态:** 🔄 2026-10-18 修订(2026-10-15 建,per user 2026-10-10 决定「所有 defer/active 的
workaround 必须在 v4 正式版中清零,大不了 v4 不发」)

> 📅 **版本归属见 [`version-schedule.md`](version-schedule.md)** —— 本文档给「怎么修」,
> 那份给「第几个版本修」。**下一次的入口已改为 v4.0.10(补三个缺口)**。

**修订摘要(2026-10-18,CI 重构期间顺带完成的部分):**
W-109 → **RESOLVED**(真修 `958c2b8`);W-118 新登记(B 组之外,
见台账);B 组 4 条产物级门 / E 组全部接线 / W-115 的 RCA **全部完成**;
并发 flake 的真根因(harness 产物命名冲突)已定位并修。ACTIVE 总数仍是 14
(一出一进),但**其中 9 条现在每次 CI 都有门在验** —— 详见下方优先级表的「门」列。

**基线:** `d2f5361`(2026-10-15)6 条首次进台账 → `93cdf3d` 补 W-109 → 补 W-110..W-116。
台账里的条目:`docs/internal/workarounds.md` W-103..W-107 / W-105.1 / **W-118** / W-109..W-116。

**优先级(高 → 低),并标出「现在有门吗」:**

> **2026-10-18 新增的列。** 判断一条 workaround 好不好修,不看它有多严重,
> 看**修完有没有门告诉你对不对** —— 没有门的话,修完只能靠「再跑一遍看看」,
> 而「再跑一遍」分不清是真修好了还是碰巧。而 10-15 写下这份表时,门几乎都没有。

| # | W-NNN | 一句话 | 性质 | 门 | 相对工作量 |
|---|-------|--------|------|----|-----------|
| 1 | **W-105** | `check_borrow` 恒 `return 1` → `&mut` 独占性完全不检查 | 语言层静默失效 | ✅ XFAIL 测试 | **见下方 ⚠️ 决策点** |
| 2 | **W-111** | 泛型 enum 一旦被 match → sema 报错后 **SEGV** | **编译器崩溃** | ✅ XFAIL 测试 | 中(先修错误恢复) |
| 3 | ~~W-110~~ | 一个函数里多条浮点比较连续改同一 mutable 局部 → 结果串号 | 静默算错 | ❌ 无 | ✅ **2026-10-17 已随 W-109 一并真修,RESOLVED** |
| 4 | ~~W-109~~ | 自举 IL lexer 缺 6 个浮点比较助记符 | — | — | ✅ **2026-10-17 真修,RESOLVED** |
| 5 | **W-103** | `std_os_open/read/write/exit` 全是 mock,`std_os_exit` 不退出 | stdlib 对用户撒谎 | ✅ XFAIL 测试 | 小(5 个 C bridge) | ✅ **2026-10-20 已修(v4.0.16)** |
| 6 | ~~W-104~~ | SysV ABI 参数分类调用 Win 分类器 | 错 ABI,目标路径平时不走 | ❌ 门在跑但**覆盖不到** | ✅ **2026-10-20 真修,RESOLVED**(v4.0.12) |
| 7 | **W-107** | 五个 per-fn 表硬编码 1024,距触发只剩 33 个 fn | 静默降级(非溢出) | ✅ 产物级门 | 中(改预分配) |
| 8 | **W-106** | `symtab_lookup_one` arena-touch 强制物化栈帧 | 冗余代码,后端依赖 | ❌ 无 | 小(判定实验,v4.0.10) |
| 9 | **W-105.1** | `check_cap_pass` 同款 stub,**当前无调用点** | 死代码 | — 不需要门 | 最小(删或实现) |
| 10 | ~~W-114~~ | 全 unit-variant 的 enum `match` 永远命中第一支 | **核心语言功能失效** | ✅ XFAIL 测试 | ✅ **2026-10-20 真修,RESOLVED**(v4.0.14 —— enum 的 ABI 两侧统一;顺带修了 W-119 的 SysV 帧布局) |
| 11 | **W-112** | `#[link_section]` 是 no-op | OS-required 特性失效 | ✅ 产物级门 | 中 |
| 12 | **W-113** | `asm!` / fence 字节 emit 到 `ret` 之后 | ship gate 空转 | ✅ 产物级门 | 中(先修 W-112 同链) |
| 13 | **W-115** | W-089 的 reproducer 仍 STACK_OVERFLOW | **深度 4/5 溢出、64 层正常** | ✅ XFAIL 测试 | RCA 已完成,剩真修 |
| 14 | **W-116** | SysV callee 参数溢出只处理 4 个寄存器 | **多参数调用传错** | ✅ **两个门** | 中 |
| 15 | **W-118** | 语言 lexer `lex_peek_char` 无 EOF 守卫 → 越过 end 前进 | 同 W-117 家族,**无观测症状** | ❌ 无 | 中(需跨两文件铺长度字段) |

**门的分布(2026-10-18 实测):** 9 条有门(W-103 / W-105 / W-107 / W-111 /
W-112 / W-113 / W-114 / W-115 / W-116),**5 条没有**(W-104 / W-106 / W-110 /
W-105.1 / W-118)。补掉前三条的排期见
[`version-schedule.md` § v4.0.10](version-schedule.md)。

排序依据:**① 现在就会让用户拿到错误结果** > ② 目标路径一旦启用就错 >
③ 距触发有明确余量的降级 > ④ 冗余/死代码。

> **W-109 与 W-110 是两回事,别当成一个 bug 一起「修好」。** W-109 是 lexer 缺
> 助记符;W-110 是 temp 槽位串号(属 W-096/097/101 家族)。W-110 排在前面是因为
> 它根因未确定,**RCA 本身就是第一步**。

> **⚠️ 一条比排序更重要的教训(2026-10-15 新增):** W-110 是**把 `float_cmp`
> 的 printf arity 修对之后**才暴露的。测试修好之前看不到真值,RCA 就是不完整的
> —— 第一版只抓到 lexer,第二个缺陷是被「真值」逼出来的。
> **`测试翻不了红的时候,RCA 也是不完整的`。**
> 现状(2026-10-15 终值):**零信号已清零** —— regress 173/173 全部有断言,
> NOASSERT 0 / VACUOUS 0(此前 53 个)。真断言 102 → **160**。
> 补断言的过程又挖出 W-112 / W-113 / W-114 三条真 bug。见 `docs/internal/tests.md` 与
> `scripts/dev/audit_test_assertions.py`。修 W-109/W-110 的同时应该把比例压下去,
> 否则下一个 bug 还是这样活下来。

> **W-109 原本为什么至今没被发现:** 唯一覆盖它的测试 `float_cmp.jhyy` 第 48 行是
> **无条件 `return 42`**,比较结果只喂给一个 5 个 `%d` 却只声明 1 个参数的
> printf(正好撞上 B8)。所以 `regress.py --tests=float_cmp.jhyy` 报
> `PASS EXIT=42` —— 这个 PASS 不携带任何信息。`src0` 自身几乎不用浮点比较,
> 自举闭环因此一路绿灯。**又一次「闭环只证明自洽,不证明正确」。**

---

## ⚠️ 未完成事项清单(2026-10-15 收尾时写下)

台账现有 **14 条 ACTIVE**。它们的**修法**都在下面各节,但**修之前缺的东西**
不在 —— 这一节记的是「还没有做的事」。每条都是可独立领走的。

### A. 有 bug 但**根本没有测试**

> ✅ **2026-10-18:3 条里 1 条已覆盖。** W-107 由 `artifact_checks.sh` 的
> `per_fn_frame` 覆盖(`.jhyy` 测试验不到它的失效模式,产物级门可以)。
> W-104 / W-106 仍缺 —— 已排进 `version-schedule.md` § v4.0.10。

写一个红测试往往比修 bug 便宜,而且会直接告诉你该怎么修。


| W-NNN | 缺什么 | 备注 |
|---|---|---|
| **W-104** | SysV **caller 侧**参数分类借 Win 分类器,没有任何用例 | docker 门已能跑,但现有 5 个用例都是 ≤4 参数,**碰不到 W-104**(需 >4 才暴露分类差异)。见 B |
| **W-106** | `symtab_lookup_one` arena-touch,零覆盖 | 先删那三行跑三道门:绿 = 已是冗余可直接删;红 = 栈 spill 根因仍在,需补最小复现 |
| **W-107** | per-fn 表 1024 上限,零覆盖 | **`.jhyy` 测试验不到**(失效模式不在返回值里)。已实测:1100 函数全对、递归深度无变化,只有 `.s` 里 `subq $N, %rsp` 从 8368 跳到 96928。需产物级检查,见 B |

### B. 需要**产物级门**(`.jhyy` 测试表达不了的,4 条)

> ✅ **2026-10-18:4 条全部已建** —— `compiler/tests/bootstrap/artifact_checks.sh`,
> 每条都造过红灯。现为 **expected-FAIL 模型**:登记一致 = 绿,签名不吻合 /
> 未登记 / UNEXPECTED-PASS = 红。workaround 转 RESOLVED 时删掉 `KNOWN_FAIL`
> 里那一行即自动升级成真门。W-116 另有第二个门(`sysv_link_run.sh`)。


这四条共同点:**失效模式在编译产物的字节里,不在程序的返回值里**。任何 `.jhyy`
测试都验不到 —— 写出来会 PASS。需要一条读 `.s` / `.exe` 的 shell 门。

| W-NNN | 门要断言什么 |
|---|---|
| **W-112** | 编译带 `#[link_section(".text.boot")]` 的文件后,`.exe` 的 section 表里**必须有 `.text.boot`**(现在只有 `.text`) |
| **W-113** | `asm!` 产生的字节必须出现在 `ret` **之前**。现测法是数 exe 里 `0f a2`(cpuid)出现次数(对照组 0 / 本测试 1),但这只证明「emit 了」不证明「执行了」 —— 要看指令相对 `ret` 的位置 |
| **W-107** | 生成 >1023 函数的模块,断言高索引函数的 `subq $N, %rsp` **不显著大于**低索引函数的 |
| **W-116** | 逐位探针:实参 1..7,分别 return 第 n 个,断言**每个都不同**。只断言一个非前四的值会被「恒取 arg4」骗过 |

新门必须遵守 `feedback_ci_gate_must_exercise_path`:**ship 前造红灯**,先证明它
在 bug 存在时会 FAIL。

### C. 要先做 RCA 才能动手

> ✅ **2026-10-18:W-115 的 RCA 已完成**(台账有 depth 1/2/3/**4**/5/8/16/64 的
> 实测表:64 层正常、4 层溢出,不是栈用量问题)。剩余的是真修本身。
> **W-110 的 RCA 仍未做**,但前提刚刚具备 —— 它两条假设里依赖 W-109 的那条,
> 而 W-109 是 2026-10-17 才修的。已排进 `version-schedule.md` § v4.0.10。


| W-NNN | 待做的 RCA |
|---|---|
| **W-110** | 浮点比较 temp 串号,两条假设都没验证:(1) 四条比较的布尔结果落到同一 temp 槽;(2) W-109 的 unknown mnemonic 造成 IL 解析错位。建议从 `codegen_amd64_state.jhyy` 的 temp 记录路径入手,对照 W-097 七处 hoist + W-101 record path |
| **W-115** | `codegen_call_return_types.jhyy` 栈溢出的**位置未知**。先拆开逐个 sub-test 跑,定位是哪个;再判定 W-089 的 ✅ RESOLVED 是否成立 —— **若不成立要把 W-089 翻回 ACTIVE**(它现在是最后一个没有 reproducer 佐证的 RESOLVED) |

### D. 测试基础设施缺口

> **2026-10-18 更新 —— 本组四条里三条已闭环:**
>
> | 项 | 状态 |
> |---|---|
> | 1. 并发 flake | ✅ **根因已找到并修**:不是编译器,是 harness 自己的产物命名冲突(`multi_file/main` 与 `namespace/main` 都写 `_regress_main.*`,并发互踩)。全量回归 175/176 → **176/176**。超时孤儿进程也已清理。**但第三层假设(旁路文件)未观测到发作** —— 见下面 1.c) 与 `version-schedule.md` v4.0.16 |
> | 2. freestanding / UEFI 无测试 | ❌ 未动 |
> | 3. 负向行为未观测 | ❌ 未动 |
> | 4. CI 上 regress 无实时进度 | ✅ 早已用 `python -u` |

1. **并发 flake —— ✅ 已定位并修(2026-10-18)**

   **根因(与本节原先的三个假设都不同):** harness 的 `_regress_*` 产物名只用
   `basename`,于是 `multi_file/main.jhyy` 与 `namespace/main.jhyy` **都**映射到
   `_regress_main.{il,s,exe}`。两者自 2026-10-15 改用 rglob 后进了同一个并发
   suite,互相删对方产物、覆盖 `-o`,甚至可能执行**另一个测试**编出来的 `.exe`。
   两个测试期望不同(EXIT=60 vs EXIT=0),撞上就是红的那个输。

   修复:`artifact_slug()` 带相对路径。全量回归从 175/176 变 **176/176**;
   清理数 340 → 346,差的 6 正好是 3 个子目录测试 × 2 个产物。

   ⚠️ **下面 1.a)–1.c) 的复盘仍然有效** —— 它们解释的是「为什么 CI 上会 hang」,
   而 hang 的真因(W-117,IL lexer 在 EOF 处无守卫)已于 2026-10-18 定位并修。
   但 1.c) 的**旁路文件机制仍未观测到发作**,处置见 `version-schedule.md` v4.0.16。


   **2026-10-17 复盘 —— 受害者不是随机的,是固定的三个,而且与代码内容无关。**
   早先「每次受害者都不同」的观察只说明*谁先撞上*在变;真正稳定的性质是:
   `f32_suffix` / `f64_suffix` / `fmod_basic` **恒定**在 CI 上 compile 超时,
   单跑全过,本地恒过。已排除的解释(都实测过,不是靠推理排除的):

   | 假设 | 排除方式 |
   |---|---|
   | CRLF(`core.autocrlf` 差异) | `.gitattributes` 有 `*.jhyy text eol=lf`,CI 上也是 LF;本地三个文件 CR 数 = 0 |
   | 内容分组(浮点 / `as i32` / 类型标注) | `float_test` / `float_arith` / `fmod_f32` / `fmod_negative` 形态完全相同却全部通过;字母序上三个受害者还**不相邻**(中间隔着 7 个通过的 float 测试) |
   | 编译器二进制不同(CI 现编 vs 提交进仓的) | 本地 `touch src0/main.jhyy && make` 重建出**逐字节相同**的 `37837b3f`;CI 报的 `00473e6b` 差异可由 CI 的 gcc 版本解释(`.comment` 段记版本号),不改变行为 |
   | 编译器本身挂 | CI 上 `[DIAG]` 步**直接命令行调用**,整步耗时 30 秒 = 3 × 10s sleep,即三个测试**全部 10 秒内编译完成** |

   所以挂的是 **harness**,不是编译器、不是输入。

   **已确认的机制(代码级,非推测):**

   a) **编译阶段没关 stdin。** 运行阶段有 `stdin=subprocess.DEVNULL`(注释:
      「MCP server 无有效 stdin → 子进程阻塞」),编译阶段漏了。jhyy.exe 用
      `system()` 拉 gcc,整条链继承 harness 的 stdin,而 GitHub Actions 给每个
      step 的 stdin 是**一根永远不送数据、也永远不关闭**的管道。链上任何一环
      (常见 `cmd.exe /c`)去读它就永久阻塞。本地 stdin 已关闭,复现不了。
      → 已修(`a25d03c`)

   b) **超时只杀直接子进程。** `subprocess.run(timeout=)` 到点只
      TerminateProcess jhyy.exe,它 `system()` 拉起的 gcc → cc1/as 留下继续满核跑。
      runner 只有 2 核,几个孤儿就占死;后续测试越跑越慢、超时越来越多 ——
      故障因此表现得**与内容无关**,实际是前一次超时的残骸在拖垮后面所有测试。
      → 已修(`a25d03c`,`_kill_tree`)

   c) **旁路文件确实是固定路径且无条件读。** `codegen.jhyy:4463` 每次编译都用
      `"wb"` 打开 `_section_directive.buf`;`main.jhyy:1154/1179/854` 在**任何**
      编译结束时都无条件读它、拼进自己的 `.s`、然后 unlink。「文件里只有我自己
      写的内容」这个不变量在并发下直接不成立。**治根 = 旁路文件按 pid 隔离。**

      ⚠️ 但 2026-10-17 复现**失败**:9 个用 asm/naked 的测试交错 4 轮并发
      (36 次编译)逐个与串行基线比对,**0 处差异**;旁路文件也被正常 unlink、
      没有累积。所以 c 是**机制成立但未观测到发作**的隐患,不能算本次 CI 挂死的
      已确认根因 —— 记在这里是为了别把它当成已经排除。

2. **freestanding / UEFI 路径没有任何可跑测试**
   `hello-freestanding/` 三个文件全是 library(无 `main_jhyy`)。
   而那正是 `#[link_section]`(W-112)的目标场景 —— OS loader 对接的入口。

3. **一批负向行为从未观测过**,「越界会怎样 / 除零会怎样」目前无记录:
   数组下标越界、字符串越界、`i32::MIN / -1`、除零、深递归(现最深 30,
   而 W-116 那条实测能到 1998 —— 说明现在的递归测试根本没探到边界)。

4. **CI 上 regress 全程无实时进度。** Python 在非 TTY 下块缓冲,整轮 20 分钟的
   `[progress]` 心跳全部在退出时一次性刷出,时间戳全落在同一秒 —— 拿不到执行
   时序,也就看不出「谁和谁同时在跑」。诊断依赖时序时这是硬障碍。
   → `python -u regress.py` 或在 harness 里对 progress 用 `flush=True`。

### E. 门的接线缺口(测试存在但 CI 跑不到)

> ✅ **2026-10-18:本组 4 项全部完成。** `audit --strict` 已接 CI;XFAIL/XPASS
> 语义随 regress 接上;产物级门已建;`sysv_full_regress.sh` 改由两段式 `sysv`
> job 覆盖(windows 编 `.s` → ubuntu 链+跑,**不需要 Docker**)。本组作废。


| 门 / 检查 | 状态 |
|---|---|
| `sysv_full_regress.sh` | **不在 CI**。CI runner 没有 Docker,5 个 sysv 测试默认全 SKIP —— 静默降级、零提示。需决定:CI 加 Docker service,还是明确接受「sysv 只在本地有 Docker 时验」 |
| `audit_test_assertions.py --strict` | 已实现、已造红灯(零信号=0 时 EXIT 0、有违规 EXIT 1),**未接 CI**。接上才能防止「新增一个零信号测试」复发 |
| XFAIL / XPASS 语义 | 已实现并验证(XPASS 当场抓到 `generics_enum` 假标记),**未接 CI** |
| 产物级门(B 组) | 不存在,需新建 |

### F. 文档债(从最初 audit 起一直没碰)

- lang-spec § 17 语法描述与实现不符(首轮 audit 提出,未复核是否仍成立)
- `Option sizeof = 12` 应为 8(首轮 audit 提出)
- **16 处裸偏移指针访问**(ast / codegen / mono / sema)—— 首轮 audit 提到,
  至今**没有一条复核过**。这类写法正是 W-102(address-holder 池重叠)的同族形态,
  优先级可能被低估
- `docs/internal/workarounds.md` 索引 **103** 行 vs 台账 **104** 个条目 —— 漏的是
  W-025 / W-070(两条都是 RESOLVED,故不影响 ACTIVE 计数)。成因:W-025 有
  follow-up H3 打乱解析,W-070 状态行带 `✅` 前缀且日期不合 schema

---

## ⚠️ 决策点:用户政策与既有计划冲突

W-105 的修复,v4.6+ 语言特性链的 lifetime 项(Polonius)已经规划过了 ——
**Polonius borrow check,新模块 `compiler/src0/borrow_check.jhyy` 约 600 行**。
那不是一个 sprint 收尾,是一个完整算法实现。

于是 2026-10-10 的政策(「ACTIVE 必须清零,大不了 v4 不发」)跟排期里的
既有排期直接撞车。三个选项:

| 选项 | 做法 | 后果 |
|------|------|------|
| **A. 先做最小独占检查**(推荐) | 现在只做「同一作用域内 `&mut` 互斥 + `&mut`/`&` 互斥」的局部检查(~150 行),完整 Polonius 留 v4.6+ 语言特性链 | 双写这个**最危险的** case 当场堵住,政策可满足;Polonius 仍是 feature 项而非 blocker |
| B. 直接上 Polonius | 把 v4.3.0 提到 v4 final 之前 | v4 final 被一个 600 行算法实现无限期挂起 |
| C. W-105 降级为 DEFERRED | 台账改判,承认这是有意的 ship-gate 决策 | 政策实质上被自己放宽;但如实反映了 2026-08 当时的设计意图 |

**本文档按 A 写。** 若 user 选 B 或 C,只需改 W-105 一节与本决策点,其余 11 条不受影响。

---

## 1. W-105 — `check_borrow` 是硬编码 `return 1`

**台账:** W-105 | **触发面:** `compiler/src0/sema.jhyy:2558-2560`
**调用点:** `compiler/src0/sema.jhyy:2677`(`let _bc = check_borrow(ctx, ta, (*fd).body)`,
在函数声明检查路径上,**每个被 check 的函数都跑**)

**⚠️ 2026-10-15 实测:本条的修法要整个重写 —— `&mut` 在 jhyy 里不可用。**

下面这份「修最小独占检查」的方案是照初稿写的,实测后发现**前提不成立**:

| 写法 | 实测结果 |
|---|---|
| `let p = &mut x;` | `unexpected token 'mut' in expression` |
| `let p: &mut i32 = &x;` | `type mismatch in let` |
| `(&x) as &mut i32` | `cannot dereference non-pointer type` |
| `fn setit(p: &mut i32) { *p = 5; }` | `cannot dereference non-pointer type` |
| `let p = &x; *p = 42;` | **OK** —— 唯一可用的写法,零检查 |

`&mut` 是个**装饰性标注**:parser 认、类型系统里有、spec supplement 承诺过,
但造不出、传不进、解引用不了。真正能写内存的只有裸 `&` + `*p`。

**所以本条其实是两个独立的工作项:**
- **(a) 让 `&mut` 真的能用** —— 这是功能缺失,不是检查缺失。在它能用之前,
  任何「独占性检查」都无从谈起(没有第二个 `&mut` 能产生冲突)。
- **(b) `check_borrow` 恒 `return 1`** —— 在 (a) 之后才需要做,否则它检查的是一个
  空集合。

新增测试 `borrow_mut_write.jhyy` 测的是最基本用法(过 `&mut i32` 形参写内存),
已标 `// XFAIL:` —— 修 (a) 时删掉这行即验收。

下列症状描述的是**一旦 (a) 完成之后**,`check_borrow` 恒 return 1 会漏掉什么:

**症状(全部静默放过 —— 前提是 `&mut` 先变得可用):**
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

**修法(选项 A —— 但要先做 (a),顺序不能反):**

**(a) 先让 `&mut` 可用**(当前完全不可用,是功能缺失):
- parser:`&mut` 在**表达式**位置被拒(`unexpected token 'mut'`),只能在类型
  标注位置用
- sema:`&mut T` 的类型解析产出的东西**不可解引用** —— `*p = 5` 报
  `cannot dereference non-pointer type`,连函数形参都不行
- 修法方向:让 `&mut T` 在表达式位置产出与 `*T` 同构的可解引用类型,`&x` 能
  初始化 `&mut i32` 绑定,形参 `&mut i32` 能被 `*p` 解引用
- 验收:`borrow_mut_write.jhyy` 删掉 XFAIL 后 PASS

**(b) 再做独占检查**(仅在 (a) 完成后有意义):
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
- regress 全量不退步(基线 **173/173 PASS + 5 XFAIL + 19 SKIP**,含 XFAIL/XPASS 语义)
- `closure_check.sh` PASS(v2.s == v3.s)
- `fixed_point.sh N=5` 7 PASS / 0 FAIL / 0 INFO

**风险:**
| 风险 | 缓解 |
|------|------|
| 近似作用域区间过宽 → 合法代码被误判 | 区间只用 block 边界,**不做**语句级收窄;误判案例进 regress 后收窄规则 |
| 误杀 src0 自身的 `&mut` 用法 | src0 本身必须能过编译 —— 跑 `closure_check.sh` 是硬门 |
| 范围失控长成 Polonius | 明确 out of scope:reborrow / 跨函数 / lifetime 子类型 |

---

## 2. W-111 — 泛型 enum 一旦真被使用 → sema 报错后 SEGV

**台账:** W-111 | **触发面:** 用户写「泛型 enum」+「match 它的变体」

**症状(四个变体全实测):**

| 代码形态 | 结果 |
|---|---|
| `type Option<T> = enum { Some(T), None }` 声明但不使用 | exit 42,**不报错** |
| 只构造 `let x = Option::None;` | exit 1,`unknown enum type`(干净报错) |
| **match 变体** | **exit 139 SEGV** |
| `type Pair<T> = enum { Two(T, T), Empty }` | exit 1,`expected )`(解析阶段挂) |
| 泛型 fn(非 enum)对照组 | exit 42 正常 |

崩溃在 **sema 阶段**,且是**打完错误之后**:

```
[3] sema start
foo.jhyy:2:38: error: unknown enum type
<SEGV>
```

`generics_enum.jhyy` 声称测的就是「enum generic — Option\<T\>」,但
`main_jhyy` 只有 `return 42;`,**类型声明了却完全没被使用** —— 编译器走的是
「声明但不实例化」路径,什么都不触发。跟 `float_cmp` 同款:**测试名字覆盖了
功能,测试内容没有。**

**两条独立缺陷,修的优先级不同:**
1. **sema 错误恢复崩溃** —— 更该先修。泛型 enum 支不支持是另一个议题,但
   报完错就崩是明确的健壮性缺陷:用户拿不到完整诊断
2. **泛型 enum 实际未支持** —— 类型解析阶段就认不出 `Option<i32>`。泛型
   *函数*正常,问题局限在 enum 的泛型化路径

**验收 gate:**
- 补 `// EXPECT-ERROR: "unknown enum type"` 测试(现在连这条都没有)
- 修后**编译报错退出 1,不是 SEGV**
- enum 多字段 payload 的解析器支持单独一条

---

## 3. W-110 — 一个函数里多条浮点比较连续改同一 mutable 局部 → 结果串号

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

## 4. W-109 — 自举 IL lexer 缺 6 个浮点比较助记符

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

## 5. W-103 — `std/os.jhyy` 全是 mock

**✅ 2026-10-20 已修完(v4.0.16)—— 台账转 RESOLVED。**

实际落地比本节原先写的多两层,都是实测逼出来的:

1. **光接 bridge 不够 —— `O_*` flag 有平台差异。** 本节写的修法假设
   `std/os.jhyy` 里的 `O_CREAT`=64 能直接用;实测那是 **POSIX 值**,Windows 的
   `_O_CREAT`=**0x100**(而且 0x40 在 Windows 上是 `_O_NOINHERIT`)。第一次调用
   直接返 -1,从 C 侧复现同样 -1 才定位到是 flag 而不是 FFI。所以 bridge 里
   多了一层 `jh_os_translate_flags()`(POSIX ↔ 平台逐位翻译 + Windows 无条件
   OR `_O_BINARY`)。**这个错 mock 藏了很久 —— 因为 mock 从不调 `open(2)`。**
2. **光接 bridge 也不够 —— std lib 之前**任何用户程序都 import 不到**。
   本节第 3 步写的是「改成 `import std::os` 用真身」,但当前 import 语法只认
   单个标识符(`import os;`),而且**只在 main 文件旁边找** `<mod>.jhyy` ——
   `compiler/src0/std/` 下的 8 个模块谁都够不着。所以额外加了 **import 的
   std lib 目录回落**(`jh_path_stdlib()`:源码树 `<root>\compiler\src0\std\`、
   installer `<bindir>\std\`),并把 8 个模块装进 MSI。
   **这一层不是顺手加的:** 没有它,测试只能继续抄 inline 副本,而副本给
   mock 契约背书(`fd==42`)—— 那正是这个 mock 能活这么久的根因之一。

另外,本节原文把根因归给「W-079 的 workaround 有两半」,**方向对但要补一句**:
W-079 当年挡的是 **QBE**;QBE 随 v4.0.0 完全移除,实测 mixed-width extern
调用在 self-backend 下**完全正常** —— W-079 当年的技术理由早已失效,
它的 RESOLVED 只是没覆盖 std_os 这一半。

修法与验收见 [`version-schedule.md`](version-schedule.md) § v4.0.16
与台账 `docs/internal/workarounds.md` 的 W-103 条目。下面保留本节原文作为
**审计轨迹**(桥的名字从 `jh_open/jh_close/...` 改成 `jh_os_open/jh_os_close/...`
—— 前缀跟已有 `jh_os_*` 家族对齐,避免跟 runtime.c 的 C 侧符号撞名)。

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

## 6. W-104 — SysV 参数分类借用 Win 分类器

**✅ 2026-10-20 已修完(v4.0.11 的 ≤16B + v4.0.12 的 >16B)—— 台账转 RESOLVED。**

实际根因比本节原先写的更大:不是「分类器接错」,是**整个 struct 参数退化成按指针传**。
修法与验收见 [`version-schedule.md`](version-schedule.md) § v4.0.11 / § v4.0.12
与台账 `docs/internal/workarounds.md` 的 W-104 条目。摘要:

- ≤16B → 按 eightbyte 分类(INTEGER→GPR,SSE→XMM);>16B → MEMORY class 整体落栈
- 常驻门 `sysv_abi_cross.sh` 扩成**三方向**(small jhyy→gcc / big jhyy→gcc /
  big gcc→jhyy),44 / 42 / 42 全绿;修复前 big 两个方向是 139 SEGV / 20
- 另加 artifact 级门 `sysv_memory_class`(**只看 .s,Windows runner 上就能跑**)

下面保留本节原文作为**审计轨迹**(修法描述已被实际实现取代 —— 实际不是
「改调 `abi_sysv_classify_arg_full`」那么简单,而是把 struct 拆成多个 IL 实参)。

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

## 7. W-107 — per-fn 表 1024 上限

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

## 8. W-106 — `symtab_lookup_one` arena-touch

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
- 三行删除后 `closure_check.sh` PASS + `fixed_point.sh` 7 PASS + regress 162/162
- 若删除后变红:新 W-NNN 登记根因,本条状态翻 ACTIVE 并写明复现

**风险:**
| 风险 | 缓解 |
|------|------|
| 删掉后某个特定 codegen 路径才炸 | 三道门全跑,且 991 个函数的覆盖面够宽 |

---

## 9. W-105.1 — `check_cap_pass` 同款 stub(无调用点)

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

## 全局 ship gate(全部修完)

> 修完之前先看上面 **§ 未完成事项清单** —— A 组(没测试)和 B 组(需产物级门)
> 是「修之前的前置」,不是可选工作。

```
regress jhyy.exe              → 不低于 162/162 PASS + 23 SKIP
regress jhyy_v2.exe           → 不低于 162/162 PASS + 23 SKIP   ← self-hosted 也跑
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

- 完整 Polonius / NLL / lifetime 子类型 / reborrow(留 v4.6+ 语言特性链的 lifetime 项)
- 多架构 Cap<T> ABI(留 v4.6+ 的并发 cap 项)
- `.jhyynb` binary format(留 v4.6+)
- 其余未启动项 —— 见 [`version-schedule.md`](version-schedule.md) § 四

## Cross-ref

- 台账:`docs/internal/workarounds.md` W-103..W-107
- 既有排期冲突:v4.6+ 语言特性链的 lifetime 项(Polonius)—— 本文档决策点 B/C 选项所指
- 门修复:commit `4a117a1`
- 台账登记 + 索引修复:commit `d2f5361`
- memory:`feedback_fix_evaluation_rule` / `feedback_ci_gate_must_exercise_path` /
  `feedback_verify_active_reproduces`
