# v4.x 版本轴排期 — 从 plan 到执行的桥

**状态:** 🔄 **2026-10-18 修订**。v4.0.8 的内容已在 CI 重构中提前完成,
本文档的排期随之重排;**未完成的「未完成事项」与决策点见下方 § 修订说明**。

**版本轴当前 HEAD = `v4.0.9-rc1`**(2026-10-18 打 tag,CI 重构后的首个真实发布;
此前最后一个真实 release 停在 2026-09-08 的 v3.2.0 —— 中间五次 tag 全部发布失败)。
本文档从 **v4.0.10** 起继续往后排。

⚠️ **v4.0.x 是 patch 序列,不是 minor 序列** —— 中间只出现过 `v4.0.2.1` /
`v4.0.2.5` 这样的第三段,说明历史上 v4.0.x 的粒度已经细到 patch 级。
如果一次 sprint 的内容超过一个 patch 的合理体量(比如 v4.0.13 的浮点一对
可能就不止一个 patch),**届时应该开 v4.1.0 而不是继续挤 v4.0.x**。
本文档目前按 patch 排是因为 v4.0.x 已有的先例如此,不是因为它适合。

plan 文件仍不以版本号命名(per [`README.md`](README.md) 的约定);
本文档是**排期表**,版本号在这份里是权威。

## 为什么需要这份

现在有两份文档,但都缺一环:

| 文档 | 有什么 | 缺什么 |
|---|---|---|
| [`active-workaround-clearance.md`](active-workaround-clearance.md) | 14 条 ACTIVE 的优先级 + 修法 + **未完成事项清单** | 没有版本归属 |
| [`backlog.md`](backlog.md) | 12 项未启动工作的依赖图 | 没有版本归属 |

两份都是「**按什么顺序**」,不是「**第几个版本做什么**」。中间缺的就是这份。

---

## 〇、2026-10-18 修订说明

CI 重构(`2c952e2`..`497868f`)顺带把这份排期里的几件事做掉了,排期因此重排。
**下表逐条核对的是事实,不是判断** —— 每条都回到源码/台账/门脚本核过。

| 原排期写的 | 现在的真实状态 |
|---|---|
| v4.0.8「B 组 4 条产物级门」待建 | ✅ `artifact_checks.sh` 四条全在,**各自造过红灯** |
| v4.0.8「`audit --strict` 接 CI」待接 | ✅ 已接 |
| v4.0.8「XFAIL / XPASS 语义接 CI」待接 | ✅ 随 regress 接上 |
| E 组「`sysv_full_regress.sh` 不在 CI」 | ✅ 换成两段式 `sysv` job(windows 编 `.s` → ubuntu 链+跑,不需要 Docker) |
| 浮点那一版「W-109 lexer 补 6 个助记符」 | ✅ **2026-10-17 已真修,W-109 → RESOLVED** |
| C 组「W-115 待做 RCA」 | ✅ **已完成**(台账有 depth 1/2/3/**4**/5/8/16/64 的实测表) |
| D 组「并发 flake 治根」 | ⚠️ **前提变了**,见下方 D3 |
| D 组「CI 上 regress 无实时进度」 | ✅ 早已有 `python -u` |
| D 组「超时只杀直接子进程」 | ✅ 已补回进程树清理(`_kill_process_tree`) |

**结论:v4.0.8 整版提前完成,v4.0.9 的 W-115 RCA 也完成。**
`active-workaround-clearance.md` 的「未完成事项清单」A/B/C/E 四组基本作废,
只剩 A 组的三分之一(见该文档修订)。

> **2026-10-20 增补:** 上表「修完没有任何门会响」里的 **W-104 已修完**
> (v4.0.11 的 ≤16B eightbyte 分类 + v4.0.12 的 >16B MEMORY class),
> **并且门是补上之后才修的** —— 补门这一步就是本节说的「给 W-104 加一个
> >4 参数的 SysV 用例」,顺带加的还有 >16B 的 MEMORY 用例与 gcc→jhyy 反向用例。
> 三方向跨实现对拍全绿(44 / 42 / 42),修复前分别是 171 / 139 SEGV / 20。
> 所以「W-104 修完没门会响」这个判断**在它被修的时候已经不成立了** ——
> 缺口 1 已闭合,剩 2(W-106 判定实验)与 3(W-110 RCA)。

### 修完有反馈 vs 修完没反馈

这是重排期的依据 —— **14 条 ACTIVE 里,只有一半修完会有门告诉你对不对**。

| 状态 | W-NNN | 门 |
|---|---|---|
| ✅ 修完立刻有红/绿(9 条) | W-116 | **两个**:`artifact_checks` + `sysv_link_run`,修完同时转绿 |
| | W-112 / W-113 / W-107 | `artifact_checks.sh` |
| | W-111 / W-114 / W-115 / W-105 / W-103 | regress 的 XFAIL→XPASS 语义 |
| ❌ 修完没有任何门会响(5 条) | **W-104** | sysv 门在跑,但现有 5 用例都 ≤4 参数,**碰不到 caller 侧分类** |
| | **W-106** | 无。需「删三行跑门」的判定实验 |
| | **W-110** | 无专用门。需 RCA |
| | **W-105.1** | 死代码(`sema.jhyy:2578` 有定义、**零调用点**),删或接线,不需要门 |
| | **W-118** | 无症状。修法需跨两文件铺长度字段 |

### 因此顺序要调整

原排期的隐含假设是「先花一版补门,再开始修」。现在门基本齐了,
**剩下 3 个缺口各自都已经很便宜**:

1. **给 W-104 加一个 >4 参数的 SysV 用例** —— 门已在 ubuntu 上每轮跑,只缺一个用例。全表性价比最高。
2. **做 W-106 的判定实验** —— 删 `symtab.jhyy:261-264` 那三行跑全部门。绿 = 已是冗余可直接删;红 = 需补最小复现。**这个实验今天才做得起,因为门是齐的。**
3. **W-110 的 RCA** —— 它两条假设里有一条依赖 W-109,而 W-109 是 2026-10-17 才修的。**前提今天才具备。**

⚠️ **但缺口不是「排在所有真修之前」。**(2026-10-18 更正,详见 v4.0.10 节的说明)
这三条只被 **W-104 / W-106 / W-110** 三笔修复依赖;其余 9 条有门的**不必等**。

所以 **v4.0.10 把 W-111 放在这三条之前** —— 它是编译器崩溃(用户直接吃到),
而这三个缺口是纯基础设施(零用户可见价值)。按价值排,依赖只约束被依赖的那几笔。

---

## 一、硬约束:什么挡住了什么

### 政策约束(2026-10-10 user)

> 「所有 defer/active 的 workaround 必须在 v4 正式版中清零,大不了 v4 不发」

所以 **v4.0.0 final 的前置 = 14 条 ACTIVE 全部 RESOLVED**。这条政策把整个
v4.0.x 系列都占满了 —— v4.1 及以后的 backlog 在这条前提下**一个都动不了**。

### 待决事项(会改排期)

| # | 决策 | 影响 |
|---|------|------|
| **D1** | **W-105 走 A/B/C 哪条?** 见 [`active-workaround-clearance.md` § 决策点](active-workaround-clearance.md) | 选 A 就要先**实现 `&mut`**(功能缺失,不是检查缺失)→ 至少 2 个版本;选 C(判 DEFERRED)则政策实质放宽,v4.0.0 final 立刻解锁一大半 |
| **D2** | **v4.0.0 final 真的必须等 14 条全清?** | 若接受「先 promote RC 之外的部分」,整个排期前移 |
| **D3** | ~~并发 flake 治根(改编译器源码给旁路文件加 pid 隔离)算不算 v4.0.x 范围?~~ | ✅ **2026-10-18 关闭**:真根因是 harness 命名冲突,已修。旁路文件那条机制**未观测到发作**,降级为「先加并发压力探针,再决定改不改」—— 见 v4.0.17 |

**D2 的补充事实(2026-10-18):** 政策要求的前置条件数量**没松动**
(W-109 转 RESOLVED、W-118 新增,净数仍是 14),但**实际成本比 10-15 写下这份
计划时低** —— 14 条里已有 9 条在每次 CI 跑门验着,做完 v4.0.10 的三个缺口
就是 12 条。差别在于:现在每修一条都有即时反馈,而不是修完再回头找证据。

**本文档按 D1=A 排**(最保守)。若选 B/C,第三节直接缩短。

---

## 二、排序原则

1. **先写会红的测试,再修** —— 一个红测试比一次修复便宜,而且直接告诉你怎么修。
   今天已经验证:修 5 个测试挖出 6 条 ACTIVE。
2. **编译器崩溃优先于算错** —— 崩溃让用户拿不到诊断,算错只是结果不对。
3. **同族打包** —— W-109/W-110 是浮点一对,W-104/W-116 是 SysV 一对,
   W-112/W-113 是 emit 旁路一对。拆开做等于同一个根因查两次。
4. **RCA 先于修复** —— W-110 / W-115 在根因未定时动手会修错地方。

---

## 三、v4.0.x 排期

### v4.0.8 — 把「修之前缺的东西」补上(A 组 + B 组 + E 组接线)

✅ **已完成 —— 内容被 v4.0.9-rc1(CI 重构)吸收。**

不动编译器逻辑,只加测试与门。实际交付:

| 内容 | 状态 |
|---|---|
| B 组 4 条产物级门 | ✅ `artifact_checks.sh`,四条**全部当场翻红**并给出准确定位 |
| `audit_test_assertions.py --strict` 接 CI | ✅ |
| XFAIL / XPASS 语义接 CI | ✅ |
| `sysv_full_regress.sh` 接入 CI | ✅ 换成两段式 `sysv` job |
| A 组:W-104 红测试 | ❌ 未做(见 § 〇 缺口 1) |
| A 组:W-106 红测试 | ❌ 未做(见 § 〇 缺口 2) |
| A 组:W-107 红测试 | ✅ 由 `artifact_checks` 的 `per_fn_frame` 覆盖 |

**门现状(2026-10-18):**

| 检查 | 现在的输出 |
|---|---|
| W-112 link_section | `KNOWN-FAIL —— 生成的 .s 里 0 条 .section 指令` |
| W-113 asm_before_ret | `KNOWN-FAIL —— BAD main_jhyy (cpuid@333 ret@332)` |
| W-107 per_fn_frame | `KNOWN-FAIL —— f500 帧 8368B vs f1099 帧 96928B,11× 膨胀` |
| W-116 sysv_arg_spill | `KNOWN-FAIL —— callee 序言缺少: %r8d %r9d` |

> ⚠️ 这四条改成 **expected-FAIL 模型**(登记一致 = 绿),不再是无条件红 +
> `continue-on-error`。理由:恒红且被忽略的步骤会训练人忽略红色。
> 签名不符 / 未登记 / UNEXPECTED-PASS 仍然是红。workaround 转 RESOLVED 时
> 删掉 `KNOWN_FAIL` 里那一行即自动升级成真门,不需要动 CI 配置。

### v4.0.9 — ⚠️ 版本号已被发布消耗,内容分流到 v4.0.10

> **2026-10-18 更正。** 本节原本列三项(W-115 RCA / W-111 / W-106)。
> 现实是:**`v4.0.9-rc1` 这个 tag 已经把 v4.0.9 用掉了**,发的是 CI 重构。
> 于是「计划里的 v4.0.9」和「已发布的 v4.0.9」撞名 —— 写这份表时没处理,
> 导致 W-111 在修订后的排期里**没有归属**。
>
> **处置:** v4.0.9 作为计划版本作废,剩余项分流:
>
> | 原内容 | 去向 |
> |---|---|
> | W-115 栈溢出定位 | ✅ **已完成**,留在本节作审计轨迹 |
> | **W-111** 泛型 enum SEGV | → **v4.0.10** |
> | W-106 arena-touch 判定实验 | → **v4.0.10**(见 § 〇 缺口 2) |

**已完成的部分(留档):** W-115 的 RCA —— depth 1/2/3/**4**/5/8/16/64 实测,
64 层正常、4 层溢出,不是栈用量问题,是特定常量取值下被编出了坏代码。

**顺带查清的一件相关事:** 该测试此前**没有 EXPECT 标注**,harness 对无 EXPECT
的测试只要不是 NTSTATUS 崩溃就算 PASS —— 所以「本地崩 / CI 过」的差异
**不是跨环境差异,是它在两边都没在测东西**。补上 `// EXPECT: 0` 后两边都失败,
XFAIL 在两边都变成诚实描述。
**「A 环境失败、B 环境通过」最容易被读成环境差异,实际常常是它两边都没在测。**

> 📌 W-115 顺带查清了一件相关的事:该测试此前**没有 EXPECT 标注**,
> harness 对无 EXPECT 的测试只要不是 NTSTATUS 崩溃就算 PASS ——
> 所以「本地崩 / CI 过」的差异**不是跨环境差异,是它在两边都没在测东西**。
> 补上 `// EXPECT: 0` 后两边都失败,XFAIL 在两边都变成诚实描述。
> **「A 环境失败、B 环境通过」最容易被读成环境差异,实际常常是它两边都没在测。**

### v4.0.10 — 一笔真修(编译器崩溃)+ 补三个缺口

**这一版由四项组成,顺序按「用户可见价值」排,不按依赖排** —— 因为它们
彼此独立(见下方更正)。

| # | 内容 | 性质 | 为什么是现在 |
|---|------|------|------------|
| 1 | **W-111** 泛型 enum 的**关联构造器**在无类型上下文处报 `unknown enum type` | 功能未完成(干净的诊断,不是崩溃) | **设计决策已定**(2026-10-19,见台账):走「调用点期望类型」,因为 `Type` 里没有泛型实参字段(单态化已克隆出具体的 `Option<i32>`),期望类型本身就是充分信息。实现形态 = 新增局部 `infer_type_expected()` + 改三处调用点,**不动 `infer_type` 签名**(45 个调用点)。⚠️ **实施前必须先验**:`callee_type.params[i]` 在那一处是否已完成单态化 |
| 2 | **W-104 的探针** —— ✅ **2026-10-19 已完成,形态改了**(见下方更正) | 补门(不修 bug) | **任何纯 jhyy 测试都抓不到它** —— caller 与 callee 用同一套「struct 按指针」约定,彼此自洽。**最终形态 = 产物级探针**(`artifact_checks.sh` 的 `sysv_mixed_struct`,KNOWN-FAIL W-104),不是跨实现对拍:判据是「函数体内第一条 `movsd` 的源操作数必须是 xmm 寄存器」(SysV `{i32,f64}` = INTEGER(rdi) + SSE(xmm0)),对照组 `plain_f64` 保证不空转 |
| 3 | ~~**W-106 的判定实验**~~ | ⚠️ **2026-10-18 已跑三次,结论未定** | 注释的理由已被证伪、机制未知、删除的安全性未证实 → **不删,但也不能宣称承重**。见下 |
| 4 | **W-110 的 RCA** | ✅ **2026-10-19 完成,结论比预期好** | 它是 **W-109 的下游症状**,已随 W-109 修复闭合 → **这条根本不需要补门**,直接 RESOLVED(前后对照实测:修复前 6 次 `unknown QBE IL mnemonic` 且 `many(3,2)=1110`,修复后 0 次且 =10;参数网格 49 组 0 错) |

**gate:** W-111 修好后 `generics_enum.jhyy` 摘 XFAIL 且 PASS、`borrow`/`enum`
相关 XFAIL 减少、`regress` 不退步;W-104 的探针造过红灯;W-106 判定实验有明确
结论并记进台账;W-110 的 RCA 定位到语句级。

**当前状态(2026-10-19):✅ v4.0.10 全部四项完成。**

第 1 项 W-111 已落地实现并通过验收(`generics_enum.jhyy` 摘 XFAIL 且 PASS=106);
那句「实施前必须先验」的前置验证也做了 —— 依据是 NODE_PATTERN_ENUM 的
`match_type` 兜底(`sema.jhyy:527-545`)**今天就在工作**,证明形参类型已是
单态化后的具体 KIND_ENUM,同一个 Type 也正是 `callee_type.params[i]`。

顺带撞出并修掉一个 2024-11 就在的越界读:`main.jhyy` 构造 `SemaContext` 的
struct literal 漏列 `current_fn` / `ret_type_map` / `ret_type_map_n` 三字段
(jhyy 的 struct literal 按列出字段数决定分配大小),导致 `return` / `let` 位置
读越界 → **exit 139 SEGV**。这大概也是 W-111 当初被记成「编译器崩溃」的原因:
台账测的是 match 形态,而 match 不碰这三个字段。

验收:自举闭环 v2..v5 逐字节相同 · `closure_check.sh` PASS ·
全量回归 **177/177, 0 failed**(此前 176/176,多出来的那个是 generics_enum
从 XFAIL 转 PASS)· artifact 级门 0 PASS / 5 KNOWN-FAIL / 0 FAIL。
**ACTIVE 14 → 12**(W-109/W-110/W-111 三条出表)。

#### ⚠️ 一处更正(2026-10-18):原第 2 项的前提是错的

原写「给 W-104 加一个 >4 参数的 SysV 用例,现有 5 个都 ≤4 参数」。**不成立** ——
`sysv_abi_test.jhyy` 就是 7 参数用例(`seven_arg_fn`),而且已被
`sysv_link_run.sh` 验着(KNOWN-FAIL W-116)。

顺着查下去得到一个更要紧的结论:**W-104 根本不可能被任何纯 jhyy 测试抓到。**

实测 `--target=amd64_sysv_freestanding`,`Mixed = {i32, f64}`:

```
export function w $process(l %m) {     ← 参数是一个 64 位值,当地址用
    %t3 =d loadd (%m + 8)
}
调用侧: movq -208(%rbp), %rdi ; call process     ← 只传一个指针
```

真实 SysV 要求 `{i32,f64}` = INTEGER(rdi) + SSE(xmm0) **按值**传。
caller 与 callee 都按**指针约定**处理 → 彼此自洽 → 所有现有测试都过。

而 `docs/abis/jhyy-abi-v1.0.0.md:872`(locked 规范)明确要求
`amd64_sysv` 的 struct pass-by-value 遵循 SysV ABI,`:881` 要求「所有 `extern fn`
遵循对应 ABI」。**所以这是违反项目自己锁定的规范,不是规范没写。**

`sysv_struct_mixed.jhyy` 是这件事的完美反例 —— 它 PASS,但
`let _ = m.d_field;` 读一下就丢、结果只依赖 `i_field`。**即使让 `d_field`
参与计算,它仍然会通过。** 这是本项目第三个同款「测试名字覆盖了功能、内容没有」。

所以本版第 2 项改为:**写一个手写 asm 的 SysV callee(按真实 SysV 从
rdi+xmm0 读),让 jhyy 去调它** —— 以 XFAIL 形式进 `sysv` job 并当场翻红。
这是 v4.0.11 修 W-104 时唯一能验的东西,不先建它,那一版的修无从验证。

#### ✅ 第 3 项判定实验已完成(2026-10-18):W-106 的 workaround **承重,不能删**

删除 `symtab.jhyy:260-264` 的三行死存储后:

| 构建 | 全量回归 |
|---|---|
| 基线(保留) | **3/3 全绿** |
| 删掉 | **3 次里失败 2 次** |

失败的**两个测试不同,且各自单跑都绿**:`cap_table_basic`(compile failed)、
`float_cmp`(stdout 空 + 退出码不对)。

**结论:那个 workaround 不是冗余代码,它掩盖着一个真实的 codegen 栈溢出缺陷。**
删掉它不是「少一层无用代码」,是**间歇性错代码** —— 症状正是台账 D 组描述的
「与内容无关的随机失败」。

⚠️ 所以 **W-106 不属于「收尾时删掉」那一类**。它的修法在 codegen(栈帧物化),
与 W-096 / W-097 同族。排期里原本把它放在「判定实验 → 绿就删」的框架下是错的,
已按实测结果更正(台账与 `CLAUDE.md` 同步)。

> ⚠️ 第 2-4 项**预期是红的** —— 缺口补上的那一刻,对应的三个 bug 会第一次
> 有门在验。红用 XFAIL / KNOWN-FAIL 登记,**不是用「改判据让它绿」**。

#### ⚠️ 一处更正(2026-10-18)

本节最初只含第 2-4 项,并写着「**排在所有真修之前 —— 之后每一笔修复都依赖它**」。
**那句话过强了。** 准确的说法是:只有 **W-104 / W-106 / W-110** 三笔修复依赖
这些缺口 —— 剩下 9 条有门的(含 W-111)**根本不需要等**。

所以 W-111 被提到本节第一位:**它是编译器崩溃(用户直接吃到),而那三个缺口
是纯基础设施(零用户可见价值)**。按价值排,不按依赖排 —— 依赖只约束
「被依赖的那几笔必须在缺口之后」,不约束别的。

### v4.0.11 — SysV ABI 一对(第一笔有双重反馈的真修)

| 内容 | 说明 |
|---|---|
| **W-116** callee 参数溢出 | ✅ **2026-10-19 已修**。根因:`codegen_amd64_emit_call.jhyy` 里 arg_idx → 寄存器的判别**缺了 SysV 的 `arg_idx >= 4` 分支**(只有 `idx 0..3 给寄存器` + `idx>=4 **且 Win** 给栈`),SysV 的 idx≥4 全落到 `%ecx` 兜底;同一段代码重复 3 处、3 处都错。`reg_rax_for_qt_idx` 的 SysV idx 4/5 本来就对,只是够不着。**两个门同时转绿**:`sysv_abi_test` EXIT 22 → **28**,artifact 级门 KNOWN-FAIL → **PASS**(这些门历史上第一个 PASS) |
| **W-104** SysV struct 传参 | ✅ **2026-10-20 已全部修完(v4.0.12)**。跨实现对拍实测:修复前 jhyy caller → gcc callee 退出码 **171**(应 44)——「struct 按指针传」不只是不符规范,而是**与 gcc 完全不能互操作**。≤16B 部分 2026-10-19 改为按 eightbyte 分类传值(IL 层拆分,self-backend 无需改动),**双向对拍都 44**;>16B 的 **MEMORY class**(整体落栈)2026-10-20 补齐 —— 三方向对拍全绿:small jhyy→gcc = 44、big jhyy→gcc = 42、big gcc→jhyy = 42(修复前分别是 139 SEGV / 20)。新增常驻门 `sysv_abi_cross.sh`(ubuntu job)—— 纯 jhyy 测试永远看不到「自洽但不兼容」这一类 |

**gate:** `sysv_link_run.sh` 5/5(**不需要 Docker** —— 两段式 job:windows 侧编
`.s`,ubuntu 侧链 `crt0.S` + `link.ld` 成 ELF 再跑);W-104 的 >4 参数逐位用例
(v4.0.10 补的那个);**Win 目标零回归**(两处改动物理隔离在各自 ABI 文件)。

**为什么挑 W-116 作为第一笔真修:** 它是**唯一一条修完会让两个门同时变绿**的 ——
`artifact_checks` 的 `sysv_arg_spill` 与 `sysv_link_run.sh` 的
`sysv_abi_test` 都登记着它。一次改动就能证明这套门是真的在验东西,
这是给整套 CI 最好的验收。

**注意(2026-10-18 修正):** 原写「这两条症状都是『SysV 多参数传错』但代码路径不同,
**别当成一个 bug 修**」。前半句仍然成立,但**两条共享同一段未完成的 SysV 调用约定**,
耦合度比原先记的高:

- W-116 = **整数/浮点参数**在寄存器与栈之间的分配(callee 侧表缺失)
- W-104 = **struct 参数**的 eightbyte 分类(整体退化成指针)

修 W-116 **不会**自动修好 W-104(不同代码路径),但两者都要动
`codegen_amd64_emit_call.jhyy` / `abi_amd64_sysv.jhyy` 这一层的寄存器分配,
**排期上应视为相邻而非独立**。

⚠️ 反过来:**只修 W-116 可能不足以让 `sysv_abi_test` 转绿** —— 该测试的失败
目前完全归因于 W-116(22 = 1+2+3+4+4+4+4 精确吻合),但 W-104 也在同一 job 里
被同一批测试覆盖。真修时若 `sysv_abi_test` 仍红,先看是不是签名不吻合触发了
`sysv_link_run.sh` 的「签名不吻合 → 红」分支 —— 那说明还有第三个贡献者。

### v4.0.12 — SysV MEMORY class(>16B struct 走栈)

**背景:** W-104 的 ≤16B 部分已修(2026-10-19),>16B 仍未实现。本版做剩下的部分。

#### 已查清的机制(2026-10-19,不必重查)

| 事实 | 位置 |
|---|---|
| SysV 栈参数**已支持**:caller `subq $N,%rsp` 后写 `0(%rsp)` | `codegen_amd64_emit_call.jhyy:869` |
| 实测第 7 个整数参数:`movl -48(%rbp),%r10d; movl %r10d, 0(%rsp)` | — |
| temp 就是**固定 rbp 偏移的槽位** → `emit_stack_arg_push` 能直接推一个 load 出来的 temp | `codegen_amd64_xmm_argalloc.jhyy:217` |
| `frame_size = (max+1)*8` —— **帧大小只由 temp 数量决定,没有 outgoing area 概念** | `codegen_amd64_state.jhyy:195` |
| callee 侧读栈参数:`fnarg_stack_off` = Win `48+(idx-4)*8` / SysV `16+(idx-6)*8` | `codegen_amd64_emit_call.jhyy:1291` |

#### 真正的障碍

**self-backend 判定「某个实参落栈」的唯一依据是「寄存器池耗尽」**(`int_arg_alloc` /
`xmm_arg_alloc` 返回 -1 → `emit_stack_arg_push`)。

而 SysV 规定 MEMORY class 参数:**不消耗整数寄存器,却必须落栈**。这个语义
self-backend 表达不了 —— 现有 IL 里没有任何形式能表达「这个实参走栈」。

#### 实现需要动的四个层面

1. **IL 层(header 编码)**:MEMORY-class struct 参数在 header 里声明为 N 个 slot,
   名字带标记(如 `<name>__m<k>`,k = 全局 MEMORY slot 序号),让 self-backend
   能识别「这是栈参数」。
2. **self-backend(callee 侧)**:`emit_copy` 的 FNARG 路径遇到 `__m` 参数 →
   从 `16(%rbp) + off` 读,而不是从寄存器;`off` = 该参数在**内存参数序列**中的位置。
3. **self-backend(caller 侧)**:MEMORY struct 的每个 8 字节 slot 从 struct 副本
   load 成 temp → 推入 outgoing 区,且**不分配 GPR**。
4. **栈偏移协调**:caller 的 outgoing 区与 callee 的读区必须算出同一个位置。
   ⚠️ **整数溢出参数也在栈上**,与 MEMORY 参数混排时会打乱偏移 ——
   两者都按**声明顺序**排。**若整数参数 > 6 且同时有 MEMORY 参数,偏移计算需要
   完整遍历 header 的所有参数**,不能只数 MEMORY slot。

**建议的受限实现(先做这个):** 只支持「整数参数 ≤ 6(无溢出)+ 有 MEMORY 参数」。
此时栈上只有 MEMORY 参数,偏移 = `16 + MEMORY slot 全局序号*8`,不需要完整 header
遍历。**检测到「整数溢出 + MEMORY 混排」时明确报编译错误**(「暂不支持」),
而不是静默产出错误代码。

#### ✅ 完成记录(2026-10-20)

按上面的「受限实现」方案做完,四个层面都动了:

| 层 | 改动 |
|---|---|
| IL(header) | `abi_amd64_sysv.jhyy`:MEMORY 参数声明成 N 个 `__m<k>` slot(k 跨所有 MEMORY 参数累计) |
| IL(caller) | `codegen.jhyy`:每个 slot 从 struct 副本按值 load,作为独立实参进 args 数组,letter = `'m'`(109) |
| self-backend(caller) | `codegen_amd64_xmm_argalloc.jhyy`:`int_arg_alloc` 对 `'m'` 返 -1(落栈)且不占 INTEGER 序列;`codegen_amd64_emit_call.jhyy`:调用点 `subq $N, %rsp` 预留 outgoing 区,call 后对称 `addq` |
| self-backend(callee) | `codegen_amd64_emit_call.jhyy`:FNARG 识别 `__m<k>` → 从 `16(%rbp)+k*8` 读 |

**受限边界照做**:`cg_sysv_check_memory_scope`(`codegen.jhyy`)在「有 MEMORY 参数
且整数参数 > 6 或浮点参数 > 8」时**明确报错并退出**,不静默产错码。

**途中挖出的两个更早的 bug(不限于 MEMORY)**:

- `codegen.jhyy` 的 `out_idx` 写成 `= i`(原始下标)而不是跨实参累计 ——
  struct 展开后,后续实参会写回**已被占用**的槽位(`f(Mixed m, i32 x)` 的 %x
  落在 m 的第二个 eightbyte 上,call 文本多出一个空槽 `%t0`)。
  **单参数调用测不到**(只有一个实参时 i == out_idx)—— 这就是 ≤16B 的测试当初全绿的原因。
- `codegen_amd64_state.jhyy` 的 `cg_parse_mem_slot` 按 `_m_` 三字节比较 ——
  标记其实是 `__m<k>`(两个下划线)→ 永远匹配不上 → MEMORY 参数被当普通 INTEGER 参数从 %rdi 读。

**验收(全绿):**

- 跨实现对拍:small jhyy→gcc = **44**、big jhyy→gcc = **42**、big gcc→jhyy = **42**
  (修复前 big 两个方向分别是 **139 SEGV** 与 **20** —— 门确实能抓到)
- jhyy↔jhyy:big = **42**
- `sysv_abi_cross.sh` 扩成三方向,新 fixture `sysv_abi_mem_caller.jhyy` /
  `sysv_abi_mem_callee.jhyy`
- 新增 artifact 级门 `sysv_memory_class`(**只看 .s,不跑二进制 → Windows runner
  上就能跑,不依赖 docker**)
- Win 目标零回归:全量 **177/177**,0 failed(含 5 个 sysv 用例)
- 自举闭环 v2..v5 逐字节相同 + `closure_check.sh` v2==v3

#### 遗留(不在本版范围)

「整数溢出参数 + MEMORY 参数混排」仍是**报错**(不是静默错码),但没实现。
要支持它,callee 侧的溢出参数栈偏移也得改成从 header 完整遍历算出来
(`16 + 真实栈序号*8`),不再用「INTEGER 序列第 N 个」推。

### v4.0.13 — 浮点(W-110 单条)✅ **已完成**

| 内容 | 状态 |
|---|---|
| **W-110** RCA → 修 | ✅ **已修,RESOLVED** —— 根因是 W-109(IL lexer 缺浮点比较助记符),W-109 于 2026-10-17 真修后 W-110 一并消失 |
| ~~W-109~~ lexer 补 6 个助记符 | ✅ **2026-10-17 已真修,RESOLVED** —— 从这一版移除 |

**gate:** `float_cmp.jhyy` 删 XFAIL 后 PASS 且输出逐值正确
(`d=111110 d2=10 s=15 p=1 dem=1`);f32 四个序比较与 f64 `==`/`!=` 新增用例;
`closure_check.sh` PASS。

**RCA 前提已具备(2026-10-17 W-109 修复之后):** 原计划写「顺序不能反,因为
W-110 的两条假设里有一条是 W-109 造成的 IL 解析错位」。现在那条假设**可以直接
被验证或证伪** —— 这条不再是不确定性。

### v4.0.14 — enum match ✅ **2026-10-20 已完成**

**W-114**:全 unit-variant 的 enum `match` 永远命中第一支。有 variant 带 payload
就正常,所以现有测试全 PASS。

**gate:** `gdb_pretty_test.jhyy` 删 XFAIL 后 PASS;新增纯 unit-variant 三臂用例
(必须断言**不同变体给不同结果**,只断言一个非第一臂会被「恒取第一支」骗过)。

#### ✅ 完成记录(2026-10-20)

**RCA 推翻了原描述**:tag compare **一直都在 emit**(IL 里是
`%t8 =w ceqw %t6, %t7` + `jnz`),只是**比的东西不对**。

真根因是 **enum 的 ABI 两侧不一致**:jhyy 的 enum 值 = 「指向一个槽的地址」
(ABI § 2.6 布局 + § 4.1「enum 构造 → 栈槽」),而 `abi_win_classify_arg` 对
**size ≤ 4 的 enum 返回 QBE_W(按值传)** —— 与规范相反。

| 位置 | caller 给的 | callee 期望的 | 后果 |
|---|---|---|---|
| enum 参数(全 unit) | 地址(`l`) | 值(`w`) | 寄存器归属理解不一致 → **tag 比较永不成立** → 恒命中第一支 |
| enum 返回值 | callee 帧里那个槽的地址 | — | 函数一返回就**悬垂** |
| enum 调用结果 | 8 字节地址 | 只存 %rax 的**低 4 字节** | 地址被**截断** → 读 tag 读到垃圾 |

带 payload 的 enum(size > 4)恰好被分类成 QBE_L(地址)✓ —— 所以它一直正常,
这解释了「有任意一个 variant 带 payload 就正常」。

**实现(先定表示,再统一两侧):**

1. `abi_win_classify_arg` 对 enum 一律返回 QBE_L。它同时决定**参数**与**返回值**
   的字母(4 个调用点:Win header / SysV header / 返回类型 / callee 的 param 局部)
   —— enum 的值在两边都是地址,四处一次改齐。
2. **enum 的返回值改走 sret**(ABI § 3.3)。caller 出目标槽,callee 拷 **image**
   进去(新增 `cg_copy_enum`)。不能只拷地址 —— 那个地址指向 callee 自己帧里的槽。
3. enum 的**调用结果 / if 结果 / match 结果**用 `cg_value_type_of`(8 字节地址),
   不是 `qbe_type_of`(4 字节 tag)。
4. **「存储放 image,表达式求值为地址」**:局部变量槽 / struct 字段 / 数组元素 /
   循环变量 → 拷 image(新增 `cg_store_enum_image`);enum 变量 / 字段 / `*p` /
   `arr[i]` / `&e` → 给**地址**,不 load(load 出来的是 4 字节 image → tag 对、
   **payload 丢**)。

**途中挖出的两个更早的 bug:**

- `&e` 对 enum 取的是「指向一个装着地址的槽的地址」(通用 SSA 路径会先 alloc 一个
  temp 把地址存进去再取 temp 的地址)。enum 的值本身就是地址 → `&e` 应等于 `e`。
- **W-119**(单独登记):SysV 帧布局把第 0 号局部变量放在 `0(%rbp)` ——
  那是 `saveq %rbp` 存的**旧 rbp**。Win 侧靠 -32 的影子区避开,SysV 侧没有影子区
  就得靠 -8 的偏移避开(公式改成 `-(local_t+1)*8`)。**这条是活的**:
  `sysv_abi_test` 的 `main_jhyy` 里一直有 `movl $1, 0(%rbp)`;它自己没崩是因为
  它是最外层(caller 是 crt0,不关心 rbp)—— 同样的形状出现在**被别的 jhyy 函数
  调用**的函数里就直接 SEGV。

**验收(全绿):**

```
最小复现(Win):  u3(A)=0 u3(B)=1 u3(C)=2 ✅  pn(N)=200 pn(S(5))=105 ✅  mx(Z)=30 ✅
返回值:         arm(mk())=1 ✅  arm(passthru(U::C))=2 ✅  match mk(){..}=1 ✅
payload enum:   arm(P::N)=200 ✅  arm(P::S(5))=105 ✅  arm(mk())=200 ✅
局部变量:       let mut c: U = U::B → match=1 ✅  赋值后再 match=2 ✅
                let mut p: P = P::S(7) → arm(p)=107 ✅(payload 没丢)
struct 字段:    get_e(WithE{e:U::C})=2 ✅
gdb_pretty_test: read_color=1 + read_maybe=42 = 43 ✅(之前是垃圾)
SysV(同款):     同样的用例在 amd64_sysv 目标下 = 217 ✅
全量回归:       178/178, 0 failed ✅
自举闭环:       v2..v5 逐字节相同 ✅  closure_check v2==v3 ✅
5 个 SysV 回归:  5 PASS ✅   W-104 三方向对拍: 3 PASS ✅
```

新增常驻门:

- `compiler/tests/examples/enum_match_unit_variants.jhyy` —— XFAIL 标记已摘,
  并扩了三个用例(跨函数返回 / struct 字段 / payload enum 的返回)
- `compiler/tests/examples/sysv_enum_match.jhyy` —— **新增**:SysV 侧的 enum 回归
  (Win 与 SysV 两条路径都要验 —— 只验 Win 的话,「同一份 enum 语义在两个目标上
  不一致」这类缺陷会隐形)

### v4.0.15 — `&mut` 路线(D1=A)· 2026-10-20 部分完成

**(a) 让 `&mut` 真的可用** —— ✅ **2026-10-20 已真修**(见下)。
**(b) `check_borrow` 恒 return 1** —— ❌ **未做**:最小实现让自举编译器 SEGV(见下)。

**gate:** `borrow_mut_write.jhyy` 删 XFAIL 后 PASS;`borrow_check_basic.jhyy`
仍 PASS(不许把合法 borrow 判死);`closure_check.sh` PASS(src0 自己就用 `&mut`)。

#### (a) 完成记录(2026-10-20)

| 改动 | 内容 |
|---|---|
| `ast.jhyy` | `NodeAddrOf` 加 `is_mut`(记录大小 8 → 16) |
| `parser.jhyy` | 表达式位置接受 `&mut expr` |
| `sema.jhyy` | `&mut expr` 的类型 = KIND_REF(is_mut=1),与**类型**位置的 `&mut T` 同一表示(抽出 `sema_make_ref_type` 供两边共用) |
| `sema.jhyy` | 解引用接受 KIND_REF |
| `mono.jhyy` | 泛型实例化保留 is_mut |

**验收:** `borrow_mut_write.jhyy` 摘 XFAIL → EXIT=5 ✓;`borrow_check_basic.jhyy`
仍 EXIT=42 ✓;全量回归 **179/179** ✓;自举闭环 v2..v5 ✓。

**`&expr`(共享)的表示没动** —— 仍是 KIND_POINTER(v3.1.0 既定语义 ✓)。

#### (b) 未做 —— 原因记录在案

最小实现(在 sema 里记录每次借用,`check_borrow` 比对同一符号的借用集合)
**做出来了但让自举编译器 SEGV**:自举出来的 jhyy.exe 编任何文件都崩(确定性,
gdb 下不复现),崩溃点是一个**帧偏移 ≈ -515KB** 的写。

逐项二分(用不用 helper 调用 / 内联 / AST / parser / sema 各子集 / 加不加 dummy
函数)**都没定位到残留的那一处**,触发条件是「**在 `infer_type`(递归热路径)里加
代码**」这个动作本身 —— infer_type 的帧大小按 per-fn max temp 估(W-096)✗。

⇒ **下一步**:把借用记录**挪出 `infer_type`**(独立 pass,或 pattern/match 的窄
路径)✗,不要动递归热路径的帧布局 ✗。

**⚠️ 附带发现:W-107 的余量只剩 2 个函数**(main.jhyy 现在 1022 个 ✗)——
本仓库自己再加两个顶层函数就跨过 1024 ✗,而越过之后被丢弃的函数会拿到
**8 字节的帧** ✗ → 局部变量冲出帧 ✗。W-107 已升级为高优先 ✗(详见台账)。

**⚠️ 这是整条线上最大的一项,且性质存疑** —— 它是功能不是 bug。若 D1 选 C,
整条 v4.0.14 取消,政策实质放宽。

### v4.0.16 — stdlib 诚实 + emit 旁路

| 内容 | 说明 |
|---|---|
| **W-103** `std_os_*` 全部接真 libc | 往 `jhyy_helpers.c` 补 5 个 bridge;**方向与 M5(删 C runtime)相反**,需记张力 |
| **W-112** `#[link_section]` 打通 | `codegen.jhyy:4478` → `_section_directive.buf` → `main.jhyy:836` |
| **W-113** asm 字节内联进函数体 | 现在落在 `ret` 之后 |

**gate:** `std_os_real_io.jhyy` 删 XFAIL 后 PASS(真文件读回 byte-equal);
产物级门「`.exe` 有 `.text.boot`」转绿;asm 相对 `ret` 的位置门转绿。

### v4.0.17 — 收尾

| 内容 |
|---|
| **W-107** per-fn 表按实际函数数预分配 + 删除截断 + `use_per_fn` 失败时报错 |
| **W-105.1** `check_cap_pass` —— 删(死代码,已核实 `sema.jhyy:2578` 有定义、**零调用点**)或实现(需 cap ownership 分析) |
| 回归基线连续 3 次全绿(排除 flake) |

**gate:** v4.0.0 final 的四条 promote 条件全满足
(见 [`active-workaround-clearance.md` § 全局 ship gate](active-workaround-clearance.md))。

#### D3 的处置变更(2026-10-18):**先观测,再决定改不改编译器**

原计划把「并发 flake 治根 = 旁路文件按 pid 隔离」列为收尾工作。**该改。**

理由:那一轮 flake 的**真根因是 harness 的 `_regress_main` 命名冲突**
(`multi_file/main` 与 `namespace/main` 抢同一个产物名),已修且全量回归转绿。
而「旁路文件固定路径在并发下会互相踩」这条机制 —— 它自己的记录就写了
「机制成立但**未观测到发作**」:9 个用 asm/naked 的测试交错 4 轮并发
(36 次编译)逐个与串行基线比对,**0 处差异**。

为一个没观测到的机制改编译器源码,和「在还不知道有没有 flake 的时候先造
FLAKY 分类机制」是同一条理由。改成:

1. **先加并发压力探针**:跑 N 轮并发编译,逐字节比 `.s` 与串行基线。
2. **有差异** → 旁路文件确实会踩 → 按 pid 隔离(改 `codegen.jhyy:4462` 的
   `"compiler/build/obj/_section_directive.buf"` 为含 pid 的路径,并同步
   `main.jhyy:854` 的读侧)。
3. **无差异** → 不改编译器,把 `_section_directive.buf` 降级成登记在案的隐患,
   在 `workarounds.md` 留一条说明「机制成立、未观测到发作、暂不改」。

**探针本身成本极低**(复用现成的 `.s` 比对),且无论结论如何都留下一个
「并发下 codegen 是否确定」的常驻答案 —— 这比改完之后才知道有没有改对强。

---

## 四、v4.1 及以后

**在 v4.0.0 final 之前一个都动不了**(政策约束)。final 之后按
[`backlog.md`](backlog.md) 的依赖图推进:

```
M5 ──┬─→ async ────────────────────────────────┐
     ├─→ 优化 pass ───────────────────────────┤
     ├─→ .jhyynb ─────────────────────────────┤
     └────────────────────────────────────────┴──→ (M5 是很多项的前置)
const generic ──────────────────────────────→ HKT
错误恢复   (独立)
包管理器   (独立)
并发 cap   (独立,M11 launch 之后)
```

**强串行链:** `lifetime → closure → dyn Trait → HKT`

**注意 W-105(a) 与 backlog §3 的关系:** backlog §3(Polonius)是 v4.0.14(b) 的
完整版。v4.0.14 做完最小版之后,backlog §3 仍然该做 —— 两者的关系是「短版」与
「长版」,不是重复。

---

## 五、怎么用这份排期

1. **一次领一个版本**,不要并行做同一版本内的项(它们有依赖顺序)。
2. **每版开始时**:在对应 W-NNN 的台账条目上把状态从 ACTIVE 推进,或在 plan 里
   记录本版的实际内容。
3. **每版 ship 前**:造红灯 → 修 → 全量回归 → 更新本文档的「实际做完」列。
4. **排期变了就改这份**,别改记忆里的版本号 —— 版本号只有本文档一处权威。

**下一次的入口:** **v4.0.10 的三个缺口**,第一个是给 W-104 加一个 >4 参数的
SysV 用例 —— `sysv` job 已经在 ubuntu 上每轮跑那 5 个用例,只缺第 6 个,
加完当场能看见红。全表性价比最高的一项。

---

## 六、这份排期本身的已知不确定性

| 项 | 不确定性 |
|---|---|
| 9 个小版本的数量 | 纯按依赖分组估的,没按工作量估。合并相邻版本很常见(比如 SysV 一对 + enum match 可能塞进同一版) |
| 不含日期 | per `feedback_no_date_estimates`,不给估时 |
| 不含「我最快多久做完」 | 上一轮已经证明:估时在这个项目上错得很离谱(并行 agent 挖出 6 条 bug 是计划外的;CI 重构顺带做掉 v4.0.8 整版也是计划外的) |
| **W-115 的工作范围已大幅收窄** | ✅ RCA 已完成(2026-10-17),不再是不确定性。剩下的是真修本身 |
| **W-110 的工作范围仍未知** | 它要先做 RCA(v4.0.10 的第 3 项)。两条假设里依赖 W-109 的那条现在可验证,但结果仍可能改变范围 |

**这份表的价值不在于它准,在于它让「下一个动作」没有歧义。**

> ⚠️ **2026-10-18 的一条元教训:** 这份排期在 10-15 写下时,把「门」和「修」当成
> 严格前后两段。实际上门和修会互相暴露对方的问题 —— 补 SysV 门时当场抓到
> W-116,补断言时抓到 W-109/W-112/W-113/W-114,给 sanity check 加真退出码后
> 抓到两个发布链的陈年 bug。**「下一版做什么」这个问题的答案,有时是在做别的
> 版本时冒出来的。** 所以这份表的价值不在于它准,在于它让「下一个动作」没有歧义。
