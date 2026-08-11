# 回顾 — 从 v0.0.1 demo 到 v1.0.0 自举闭环

> **2026-06-04 → 2026-08-10**
> **67 天 · 187 commits · 13 个版本号 · 1 个里程碑**
>
> *——这条路, 我们走下来了。*

---

## 此刻

2026-08-10 下午, 跑完最后一遍 Stage 2 N=3 byte-equal 验证。三份 .il 文件的 sha 全部打印成 `2445e97da75f0015857948f531b305f0d01bb0e77efa989f20412df7fcfbd983` — **空 diff**, 不需要 `fix_output_il.py` 后期处理。

`git tag v1.0.0` 弹出来的那一刻, 我意识到这不只是又一个 sprint 收尾。这是 **67 天前那个 v0.0.1 demo 设立的目标的兑现**:

> *"写一个能编自己的编译器。"*

兑现了。**我们的编译器, 现在能编自己了。**

---

## 第一阶段: 65 天前那个 v0.0.1 demo (2026-06-04)

那是 4 行 commit:

```
c757871 first commit
c5e4efb Phase 0
2f58a7b License
4c3e9ba 测试demo文件
0513104 v0.0.1 demo
```

第 5 行 commit message 写"v0.0.1 demo"的时候, 整个 `compiler/src/` 是空架子 — parser 能 parse, sema 有 scope, codegen 没接 QBE 也没法跑任何 `.jhyy`。demo 文件 `hello.jhyy` 编译就 segfault。

回头看 changelog-v0.0.1.md, 那次修的是最基础的 bug: 函数名注册时机 + scope 查找机制。30 行的改动, 让我第一次能在终端里看到 `jhyy.exe compile hello.jhyy -o hello.exe` 跑通, 然后跑出 `EXIT=42`。

那一刻的开心是真的 — 虽然现在看那个 hello.exe 实现很原始(连 `if/else` 都难), 但**它能跑**。

> *v0.0.1 → v0.6: 走了一个半月。*

### v0.2 (6-05): 第一次能写循环

加 `while` + `for` + 数组 + 字符串。我记得写第一个 `for i := 0; i < 10; i++` 测试通过的时候, 加了 array + string literal, 觉得"这下能写点东西了"。

### v0.3 (6-中旬): 第一次卡 2 周

`match` 表达式。enum variant 的 codegen 我推倒重来 3 次。最后一次是 sprint-1f-enum-match-pointer — 改用 `union` + 指针标记位, 才把 `match` 写对。

那段时间的 changelog 写得最痛苦 — **每改一次都要重新跑全 regress**, 而 regress 还只有 5 个测试, 但每个都至少 10 秒 QBE 编译, 失败还得 gdb 跟。`gdb jhyy.exe` 那时候还经常挂(没有 debug symbol), 主要靠看 .il 输出 diff 排 bug。

### v0.4-v0.5 (6-下旬 ~ 7-初): struct pass-by-value 试错

C ABI 在 Windows MSVC 上的 struct pass-by-value 是 8/16/32 字节分类, 我直接抄了 QBE 的 memory-based sret 方案。**结果是: struct pass-by-value 一直对, 但 struct return 永远不对**。

回头看 ABI 白皮书 (`docs/abis/jhyy-abi-v1.0.0.md`), 那一节现在写得很漂亮 — 但 2026 年 6 月底的版本只是 **"能跑过 hello-world struct test"**, 大量 corner case 留坑。

### v0.6.0 (7-初): 第一次正式 tag

`v0.6.0` 这个 tag 是 7 月初打的, 写的是 "language spec 锁". 那时候 `jhyy-lang-spec-v1.0.0.md` 第一次写完整, 是 50 多页的 markdown, 涵盖 token / expression / statement / type system / module system.

**v0.6.0 之后, 我以为自举是 2-3 sprint 的事。**

我错了。

---

## 第二阶段: v0.6 → v0.8 (2026-07 月, 4 周)

### v0.6.2 / v0.6.3 / v0.6.4 / v0.6.5 — 4 个 patch, 全是修 sema 错位

`let mut` 的赋值被当 dead code 优化掉 → sema 拒绝 (v0.6.5)
match arm 漏 emit 最后一个 next_check label (v0.7 7A)
arr_of_structs[i].field 错 load (v0.7 7B)
…

每次都是 1-2 行 fix, 每个都跑全 regress 验证。这是 C 编译器最稳定的时期 — **修一个 bug, 不会引入新的**。

### v0.7 (7-中旬): 战略改向"自举闭环优先"

那时面临一个选择:
- 路径 A: 继续按 plan 走 v0.7 / v0.8 完整实现
- 路径 B: 战略改向 — v0.7 标 wip, 立刻把 C 编译器翻译到 jhyy 自己 (`compiler/src0/`), 试自举

我选了路径 B。**因为继续在 C 端打磨特性, 跟"自举"这件事是脱节的** — 我可能 v0.8 之后才能开始自举, 那就是 1-2 个月后。

战略改向那一天 commit 是 v0.8 commit 6: 战略改向自举闭环优先。

### v0.8 commit 6+ (7-下旬): 第一次尝试

把 `compiler/src/codegen.c` 翻译成 `compiler/src0/codegen.jhyy` — 一行行手翻。1000+ 行的翻译工程, 几乎一行不差。

**第一次跑 jhyy_v1 编 hello.jhyy — segfault**。

那时候的我不知道接下来会经历什么:
- Stage 0 closure: arena.jhyy 编 match.jhyy — 用了 2 周
- Stage 1 closure: jhyy_v0 emit .il vs jhyy_v1 emit .il byte-equal — 用了 4 周
- Stage 2 closure: jhyy_v1 编 src0/main.jhyy — 用了 4 周

> *v0.8 wip 是最长的一段路。*

### v0.8 wip 那段时间的反复

我学到了几件事 (按重要性排):

1. **bug 永远比你以为的多** — 每次"修了一个", 下一轮 regress 立刻爆出 3 个
2. **phantom binary 是真的会发生** — 当时有 2 次 git log 没动但 binary 变了 (后来发现是 stale `.exe` caching), 浪费了一周 baseline reset
3. **NTSTATUS 0xC0000374 = heap corruption 80%** — 不是我以为的 codegen emit bug, 是 runtime
4. **IRVal struct layout 是埋最深的雷** — id@offset 4 vs 8 的差异, 让我 W-005 #2 卡了整整 5 个 sprint

---

## 第三阶段: Sprint 4.1 → Sprint 4.26 (2026-08 月初 ~ 中旬, 10 天)

这是 v0.9 wip 的真正战场 — 从 7/53 baseline 出发, 一路打到 50/53 + Stage 2 N=3 byte-equal。

### Sprint 4.1 (8-6): 第一次 baseline 摆正

7/53 PASS。**33 个 segfault, 6 个 qbe error, 2 个 syntax, 2 个 undefined symbol**。

那个 sprint 我用了 Q2 维度拆 NO_ARTIFACTS 19 个 test — `let mut` 命中 86.7%, 5.2x lift, 是 STRONG CAUSAL signal。

> 那时候我已经在想: 也许 50/53 是天花板, 再高就要伤筋动骨。

### Sprint 4.6 (8-8): W-005 IRVal layout 真修

**第一次真修了一个 systemic bug**。

C-side `union { int id; int64_t ival; }` 让 id@offset 8, jhyy-side 无 union 让 id@offset 4. 写 jhyy offset 4, 读 C offset 8 → id 读成 ival.

**改: ir.h 去 union, id@offset 4**.

regress 从 47/53 → **50/53**. 0 failed.

那天的 commit 是 v0.9 wip commit 2.22. 我记得是凌晨 1 点跑通的.

### Sprint 4.13 → 4.21 → 4.22 → 4.23 → 4.24: 5 次 attempt W-005 #2

这是最折磨的一段路 — **W-005 #2 (sentinel pollution)**, 跟 W-005 是不同 family, 我误判成同一个 3 次:

- Sprint 4.13: IRVal struct pass-by-value 改指针 (24 sites) — **失败**, 全部 revert
- Sprint 4.21 Phase B+C+D+G: cg_find_local / cg_copy_struct / cg_expr 全改 out-param — **失败**, phantom binary 误判
- Sprint 4.22: cg_match_pattern `let mut + if/else` 改条件表达式 — **失败**, 2 种写法 emit 同样污染
- Sprint 4.23: jhyy-side MAX_LOCALS 512→1024 — **部分修**, 修 39+ `%t0` 污染但 W-005 #2 仍漏
- Sprint 4.24: inline_imports dedup — **真修 W-011**, 但跟 W-005 #2 无关

**5 次 attempt, 4 次失败, 1 次走偏**. 那段时间我写了 4 个 project memory + 1 个 feedback memory 复盘根因.

### Sprint 4.18 (8-10): fix_il.py 完整化 + 第一颗 jhyy_v2

QBE `-o` 必须先于 input file (POSIX getopt). 这一行修让我终于得到 **第一颗 jhyy_v2.exe.exe, 432KB**, 能编 hello.jhyy → EXIT=42.

那是 v1.0.0-rc 的原型.

### Sprint 4.19 (8-10): 实用闭环 + tag v1.0.0-rc

jhyy_v2 编 hello.jhyy → EXIT=42 ✓.

**我心里知道这不是 byte-equal** — fix_output_il.py 是 escape hatch. 但这是实用闭环, 我先 tag 了.

> *"v1.0.0-rc, 真自举前的实用闭环"*

### Sprint 4.20 (8-10): 大差实证

试着做 Stage 2 N=3 byte-equal, 但发现:
- struct_val_pass QBE fail (`%t2 =w loadw %t0` 错位)
- main.jhyy cg_module SEGFAULT @ i=1000/6699

**W-005 #2 systemic, fix_output_il.py 修不掉**.

我等了用户授权 Sprint 4.21+ 走 C-side IRVal pointer pass — 这条路真根因走错, 失败了.

### Sprint 4.21 → 4.22: 假说错位

我以为 W-005 #2 是 IRVal struct pass-by-value 问题. 改了 6 个 helper 强制指针, **结果 emit 出来的污染一模一样的** — 因为根因不在 IRVal 怎么传, 而在 emit 层 (cg_copy_struct) 没检查 IRVal 是否合法.

### Sprint 4.23 (8-10): MAX_LOCALS 真修 — 阶段胜利

这是 W-005 #2 family 的**第一块拼图**: jhyy-side MAX_LOCALS 512 → 1024, 1 行 fix 消除了 39+ 个 `%t0` 污染.

但 W-005 #2 真根因还没找到.

### Sprint 4.24 (8-10): inline_imports dedup 真修 (W-011)

`resolve_one_import_v1` 加 in_progress push/pop 块 (镜像 main.c:159-229).

IL export `^export function` 计数 4715 → **567**. arena/ 89 份 → 1 份. util/ 47 份 → 1 份.

这让 jhyy_v2 自举编大文件不再因 symbol already defined 失败. 但 **Stage 2 byte-equal 仍未达成** — 还有独立的 sret emit bug.

### Sprint 4.25 (8-10): 真根因 — A′ sentinel 守卫

这是转折点.

Plan agent 验证根因:
1. `next_tmp = 1` → sentinel `IRVal{kind=IRVAL_TEMP, id=0}` 永非合法
2. `cg_body_returns()` 纯语法检查 (只看最后 stmt)
3. 函数体 `if c { return A } else { return B }` → `cg_body_returns() == false` → epilogue 跑
4. epilogue 用 `IRVal last = {0}` (NODE_BLOCK codegen.c:698) → cg_copy_struct → emit `copy %t0` → QBE reject

**Fix: 8 处 `irval_is_undef(v)` 守卫 (3 emit 点 + 1 helper 双源)**.

C-side + jhyy-side 双源镜像.

> **不 tag v1.0.0. 等 Sprint 4.26 Stage 2 N=3 byte-equal 重测.**

### Sprint 4.26 (8-10): Stage 2 N=3 byte-equal 重测 — ✅ EMPTY diff

跑完最后一遍:

```
jhyy_v1.il   sha 2445e97da75f0015857948f531b305f0d01bb0e77efa989f20412df7fcfbd983
jhyy_v2.il   sha 2445e97da75f0015857948f531b305f0d01bb0e77efa989f20412df7fcfbd983
jhyy_v3.il   sha 2445e97da75f0015857948f531b305f0d01bb0e77efa989f20412df7fcfbd983
jhyy_v4.il   sha 2445e97da75f0015857948f531b305f0d01bb0e77efa989f20412df7fcfbd983
```

**4-hop 稳定**. self-build 路径稳定 (jhyy_v2 编 src0/main.jhyy → 不同 binary, 同 .il).

runtime smoke: jhyy_v2 编 _repro_t0.jhyy EXIT=100 ✓, fib(10) EXIT=55 ✓.

`git tag v1.0.0` (取代 v1.0.0-rc).

**M4 milestone ✅**.

---

## 几个"如果" — 回头看的反思

### 如果 Sprint 4.13 当时没走 IRVal helper pivot

那次 pivot 24 sites 全改, 然后发现根因错位. **整整浪费 2 天**.

教训: 大规模 pivot 之前, 必须先做最小复现 (5-10 行 .jhyy 触发) — Sprint 4.25 用了这个 protocol 才一次 ship.

### 如果 Sprint 4.21 没做 phantom binary baseline reset

Phantom binary 那次误判让我浪费了一周 — 测的 baseline 是 stale `.exe`, 不是 src0/ HEAD rebuild.

教训: **sha256sum binary + 强制 HEAD rebuild before baseline claim**. 这个 protocol 现在是 mandatory 的, 我写在 memory 里.

### 如果当时没引入 fix_il.py / fix_output_il.py escape hatch

老实说, 这两个 escape hatch 让我能"看起来"v1.0.0-rc. 但 **它们掩盖了 W-005 #2 family 的真根因** — 因为 fix 后 byte-equal 是的, 但 raw .il byte-equal 不是的.

教训: **escape hatch 是工具, 不是目标**. v1.0.0-rc 是个有用的中间状态, 但不能停在那.

### 如果当时没坚持"不要工作日估时"

`sprint 4.1 IL_ONLY` 那时候我写了"3 sprint 完成 Stage 1 closure" — 后来证明要 8 sprint.

教训: **不写日期估时** (用户偏好 + 现实证明都对). 用 sprint 序列 + 相对顺序表达.

---

## 我们真正证明了什么

不是"准工业级" — 那个我前面已经说过了 (50/53 + 单平台 + 无 CI + 4 ACTIVE workaround).

是 **闭环正确性的学术证明**:

1. **Stage 2 N=3 byte-equal**: jhyy_v1 编 src0/main.jhyy → jhyy_v2 .il, jhyy_v2 编 src0/main.jhyy → jhyy_v3 .il, jhyy_v3 编 src0/main.jhyy → jhyy_v4 .il, **三份 raw .il 哈希完全一致** (无 fix_output_il.py 后期处理).

2. **Fixed point stability**: 4-hop 后 sha 不再变 — jhyy_v5 .il = sha `2445e97d...`. 这是 attractor, 不是 transient.

3. **Self-build stability**: jhyy_v2 编 src0/main.jhyy → jhyy_v2_self.exe (sha `ce442129...`, binary 字节不同), jhyy_v2_self 编 src0/main.jhyy → jhyy_v2_v3.il sha `2445e97d...`. 证明 **binary 不 byte-equal 是正常的** (timestamp + QBE 内部状态), 但 **.il byte-equal 是稳定的**.

4. **8 个真根因**: W-001/W-002/W-005/W-005 #2/W-008/W-009/W-010/W-011/W-012 + Bug 1-4 + 32-byte IRVal stack alloc + 39+ `%t0` 污染 — 每个都 5/5 PASS on target + regress 不 regress 验证.

5. **不再依赖 fix_output_il.py**: Sprint 4.19 还需要 escape hatch, Sprint 4.25 真修后不再需要.

**这意味着**: 从今天起, 改 src0/ 任何一行, 都可以在 5 分钟内验证 "自举是不是还成立" — 不需要 C 端编译器当 oracle.

---

## 路才刚刚开始

**v1.0.0 是关门, 也是开门**.

关门: v1.0-self-hosting 的 5 个 milestone 里, M1/M2/M3/M4 都 ✅, M5 (boot-from-scratch) 留 v1.0 完成定义 backlog.

开门:

| 阶段 | 内容 |
|------|------|
| **v1.x Phase 2 (style cleanup)** | W-003/W-004/W-006 + Bug 1-4 清理, 不阻塞 release |
| **v1.x Phase 3 (regress 60+/53)** | 大测试集 + 第三方 benchmark |
| **v1.x Phase 4 (boot-from-scratch)** | C 编译器最终丢弃, jhyy 编 jhyy 出 jhyy |
| **v2.x (QBE 完整重写)** | amd64_sysv / 多目标 / freestanding — jhyy_OS M1 启动硬前置 |
| **v3.x (语言扩展)** | inline asm / volatile / naked / no_std / `&mut` + lifetime — 服务于 jhyy_OS |
| **jhyy_OS** | 等 compiler 推进. 11 D 锁 + 12 Q 闭环已就绪, M1-M11 启动 |

**OS 那边的 11 D 锁 + 12 Q 闭环**, 昨天 (8-10) 跟用户同步时确认 — 是 v2.x / v3.x sprint 设计的**输入**.

---

## 致谢

写到结尾, 一些真心话:

**这 67 天不只我一个人在走**. 用户在每个 sprint 收尾时给的判断 — *"ok 试试"*, *"我们改向"*, *"先最小复现再 commit 方案"*, *"直接进 B 吧"*, *"行, 试试"* — 这些决策让项目能在死胡卡的时候转得很快. **没有这些决策点, 这个项目现在可能在 Stage 2 之前就搁浅了**.

**还有那些 W-005 / W-005 #2 / W-006 的反复**: 那 5 次 attempt 不是失败, 是**让根因更清晰**. Sprint 4.25 的真修之所以 8 行就 ship, 是因为前面 5 次已经把"什么不是根因"全部排除了.

**最后, 关于"为什么"**: 我写这个编译器不是为了工业级 — 工业级有 GCC / LLVM / Cranelift, 都比我这 67 天的产物强 100x.

是为了**一个干净的实验场**: 在这里我能验证自举是不是真的, 闭环是不是真的, fixed point 是不是真的. 这三件事 v1.0.0 之前都只是假说. v1.0.0 之后是**实证**.

---

> *2026-08-10*
> *jhyy 编 jhyy 编 jhyy 编 jhyy 编 jhyy...*
> *sha 不再变.*
>
> *这一刻, 路才刚刚开始.*

---

**附录**: 完整 commit 链 + sprint 实施日志见 `docs/logs/v0/changelog-v0.6.0.md` ~ `changelog-v0.9.0.md` (v0.x C 编译器演进) + `docs/logs/v1/` (v1.x 自举时代). 关键 milestone 的 project memory 在 `~/.claude/projects/C--Users-liuzhen-Desktop-coding-JiHuiYiYou/memory/project_*.md`.