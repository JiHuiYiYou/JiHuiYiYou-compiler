# v4.x 版本轴排期 — 从 plan 到执行的桥

**状态:** 📋 **排期草案**(2026-10-15 建)。**尚未承诺任何版本号** —— 下面写的
`v4.0.x` 是**目标顺序**,不是既定的里程碑。按 [`README.md`](README.md) 的命名约定,
版本号在启动时才分配,plan 文件也不以版本号命名;本文档是**排期表**,不是 plan。

## 为什么需要这份

现在有两份文档,但都缺一环:

| 文档 | 有什么 | 缺什么 |
|---|---|---|
| [`active-workaround-clearance.md`](active-workaround-clearance.md) | 14 条 ACTIVE 的优先级 + 修法 + **未完成事项清单** | 没有版本归属 |
| [`backlog.md`](backlog.md) | 12 项未启动工作的依赖图 | 没有版本归属 |

两份都是「**按什么顺序**」,不是「**第几个版本做什么**」。中间缺的就是这份。

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
| **D3** | 并发 flake 治根(改编译器源码给旁路文件加 pid 隔离)算不算 v4.0.x 范围? | 建议算 —— 它影响每次 ship 判断的可信度 |

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

### v4.0.1 — 把「修之前缺的东西」补上(A 组 + B 组 + E 组接线)

**不动编译器逻辑**,只加测试与门。这一版存在的意义是:它把后面 7 个版本的
「修好了怎么知道修好了」这个问题先解决掉。

| 内容 | 对应 |
|---|---|
| W-104 / W-106 / W-107 的红测试 | 未完成事项 A 组 |
| 4 条产物级门:`.text.boot` 存在性 / asm 相对 `ret` 的位置 / 高索引函数 `subq $N,%rsp` / SysV 逐位探针 | B 组 |
| `audit_test_assertions.py --strict` 接 CI | E 组 |
| XFAIL / XPASS 语义接 CI | E 组 |

**gate:** 新门**逐一造过红灯**(每条都要先证明它在 bug 存在时会 FAIL);
`regress` 全量 173/173 + 5 XFAIL + 19 SKIP 不退步;新增测试以 XFAIL 形式出现
而不是被 SKIP 掉。

**风险:** 四条产物级门都可能立刻翻红(它们本来就在验存在的 bug),所以这一版
**预期是红的** —— 红的部分用 XFAIL/已知失败登记,不是用「改判据让它绿」。

### v4.0.2 — 编译器崩溃 + 一个悬案

| 内容 | 说明 |
|---|---|
| **W-111** 泛型 enum 一 match 就 SEGV | sema 错误恢复路径:报完 `unknown enum type` 后应干净退出,而不是拿无效指针继续 |
| **W-115** `codegen_call_return_types` 栈溢出定位 | RCA;查清后判定 **W-089 的 ✅ RESOLVED 是否成立**,不成立就翻回 ACTIVE |
| **W-106** arena-touch | 有了 v4.0.1 的测试就能判:绿 = 直接删三行;红 = 补最小复现 |

**gate:** `borrow`/`enum` 相关 XFAIL 减少;`regress` 不退步。

### v4.0.3 — SysV ABI 一对

| 内容 | 说明 |
|---|---|
| **W-116** callee 参数溢出只做 4 个寄存器 | `%r8d`/`%r9d`/栈参数从未被读 |
| **W-104** caller 参数分类借 Win 分类器 | 正确的 `abi_sysv_classify_arg` 就在同文件 `:79`,没接线 |

**gate:** `sysv_full_regress.sh` 5/5(需 Docker);新增 >4 参数的逐位用例;
**Win 目标零回归**(两处改动物理隔离在各自 ABI 文件)。

**注意:** 这两条症状都是「SysV 多参数传错」但代码路径不同,**别当成一个 bug 修**。
修 W-116 不会自动修好 W-104。

### v4.0.4 — 浮点一对

| 内容 | 说明 |
|---|---|
| **W-110** RCA → 修 | 一个函数里多条浮点比较连续改同一 mutable 局部 → 串号 |
| **W-109** lexer 补 6 个助记符 | f32 变体 `cles`/`clts`/`cgts`/`cges` + `ceqd`/`cned`;`:1642` else 分支改兜底报错 |

**gate:** `float_cmp.jhyy` 删 XFAIL 后 PASS 且输出逐值正确
(`d=111110 d2=10 s=15 p=1 dem=1`);f32 四个序比较与 f64 `==`/`!=` 新增用例;
`closure_check.sh` PASS。

**顺序不能反的理由:** W-110 的两条假设里有一条是「W-109 的 unknown mnemonic
造成 IL 解析错位」。先做 RCA 才知道 W-109 要不要连带修。

### v4.0.5 — enum match

**W-114**:全 unit-variant 的 enum `match` 永远命中第一支。有 variant 带 payload
就正常,所以现有测试全 PASS。

**gate:** `gdb_pretty_test.jhyy` 删 XFAIL 后 PASS;新增纯 unit-variant 三臂用例
(必须断言**不同变体给不同结果**,只断言一个非第一臂会被「恒取第一支」骗过)。

### v4.0.6 — `&mut` 路线(待 D1 确认)

**(a) 让 `&mut` 真的可用** —— parser 表达式位置拒 `&mut`、`&mut T` 产出的类型
不可解引用。这是**功能缺失**。
**(b) `check_borrow` 恒 return 1** —— 只在 (a) 之后有意义。

**gate:** `borrow_mut_write.jhyy` 删 XFAIL 后 PASS;`borrow_check_basic.jhyy`
仍 PASS(不许把合法 borrow 判死);`closure_check.sh` PASS(src0 自己就用 `&mut`)。

**⚠️ 这是整条线上最大的一项,且性质存疑** —— 它是功能不是 bug。若 D1 选 C,
整条 v4.0.6 取消,政策实质放宽。

### v4.0.7 — stdlib 诚实 + emit 旁路

| 内容 | 说明 |
|---|---|
| **W-103** `std_os_*` 全部接真 libc | 往 `jhyy_helpers.c` 补 5 个 bridge;**方向与 M5(删 C runtime)相反**,需记张力 |
| **W-112** `#[link_section]` 打通 | `codegen.jhyy:4478` → `_section_directive.buf` → `main.jhyy:836` |
| **W-113** asm 字节内联进函数体 | 现在落在 `ret` 之后 |

**gate:** `std_os_real_io.jhyy` 删 XFAIL 后 PASS(真文件读回 byte-equal);
产物级门「`.exe` 有 `.text.boot`」转绿;asm 相对 `ret` 的位置门转绿。

### v4.0.8 — 收尾

| 内容 |
|---|
| **W-107** per-fn 表按实际函数数预分配 + 删除截断 + `use_per_fn` 失败时报错 |
| **W-105.1** `check_cap_pass` —— 删(死代码)或实现(需 cap ownership 分析) |
| **D3** 并发 flake 治根:旁路文件按 pid 隔离 |
| 回归基线连续 3 次全绿(排除 flake) |

**gate:** v4.0.0 final 的四条 promote 条件全满足
(见 [`active-workaround-clearance.md` § 全局 ship gate](active-workaround-clearance.md))。

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

**注意 W-105(a) 与 backlog §3 的关系:** backlog §3(Polonius)是 v4.0.6(b) 的
完整版。v4.0.6 做完最小版之后,backlog §3 仍然该做 —— 两者的关系是「短版」与
「长版」,不是重复。

---

## 五、怎么用这份排期

1. **一次领一个版本**,不要并行做同一版本内的项(它们有依赖顺序)。
2. **每版开始时**:在对应 W-NNN 的台账条目上把状态从 ACTIVE 推进,或在 plan 里
   记录本版的实际内容。
3. **每版 ship 前**:造红灯 → 修 → 全量回归 → 更新本文档的「实际做完」列。
4. **排期变了就改这份**,别改记忆里的版本号 —— 版本号只有本文档一处权威。

**下一次的入口:** v4.0.1 的第一项是 **B 组的四条产物级门**(W-112 的
`.text.boot` 检查最直观,适合先做,能立刻看到红)。

---

## 六、这份排期本身的已知不确定性

| 项 | 不确定性 |
|---|---|
| 8 个小版本的数量 | 纯按依赖分组估的,没按工作量估。合并相邻版本很常见(比如 SysV 一对 + enum match 可能塞进同一版) |
| 不含日期 | per `feedback_no_date_estimates`,不给估时 |
| 不含「我最快多久做完」 | 上一轮已经证明:估时在这个项目上错得很离谱(并行 agent 挖出 6 条 bug 是计划外的) |
| W-110 / W-115 的工作量未知 | 它们要先 RCA,RCA 结果可能显著改变范围 |

**这份表的价值不在于它准,在于它让「下一个动作」没有歧义。**
