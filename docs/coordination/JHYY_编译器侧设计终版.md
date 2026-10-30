# JHYY 编译器侧设计终版

> **本文定位**：JHYY 编译器侧的**最终设计文档** —— 从源码、规范、门脚本逐条核过的事实基线，
> 加上从「文档里写着」推到「编译不过」的完整分期路线。
>
> **配套文档**：[`docs/coordination/JHYY_OS侧设计终版.md`](JHYY_OS侧设计终版.md) —— 内核形态、capability 对象模型、
> `.jhyynb` 契约、语言—内核边界。
>
> **事实基线纪律**：唯一实现事实来源是三份规范（lang-spec v4.0.0 / abi v4.0.0 /
> binary-format v1.0.0）+ 源码 + 门脚本。凡三者均未记载者标「**待确认**」，不做推测性填充。
> 本文中所有 `file:line` 引用均可回查。
>
> **本文取代**（原 6 份，内容保留在 git 历史）：
> `JHYY_决策总纲.md` · `JHYY_编译器全阶段方向与路线图.md` · `JHYY_Cap类型语义草案.md` ·
> `JHYY_待拍板设计.md` · `JHYY_设计自审_对照K框架.md` · `JHYY_OS_内核模型与语言需求.md`（OS 部分）。
>
> **版本号是预留号** —— 每格启动时按实际状态复核；稳定身份是 `OS-N` 序号
> （见 [`docs/plans/v4/README.md`](../plans/v4/README.md) 的版本系列索引）。

---

## §0 一句话结论

**JHYY 编译器不应先成为一个「更完整的语言」，而应成为一个能把内核安全不变量变成「编译不过」的
能力程序验证与代码生成器。** 优先级是**确定性 > 执行反馈 > 表达力**：
先让自举成为可重复实验（P0），再让最小镜像真跑在裸金属（P1），再压栈（P2），
最后才动 capability 类型化（P4）。

**当前最大的风险不是缺特性，而是「静默错误」** —— 实参类型与个数**都不检查**、
bool 值未归一化、CLI 多余输入文件被静默忽略、整数隐式提升缺失且规范未记。

---

## §1 编译器在体系中的定位

### 1.1 分工公式

> **编译器证明 shape，内核强制执行 authority。**

编译器负责「类型与形状对不对」；内核负责「对象是否存在、权限够不够、并发与硬件状态」。
两者共享一份**可机器检查的契约**（`.jhyynb` 的 contract section）。

| 不变量 | 最佳检查阶段 |
|---|---|
| `Cap<T>` 的 T 与 type_tag 相容 | 编译期 |
| `Cap<T, R\|W>` 传入需要 W 的接口 | 编译期 |
| rights 单调收缩 | 编译期生成证明 + **运行期内核强制** |
| IPC `msg_tag` 唯一、handler 签名一致 | 编译期 |
| `cap_offsets` 合法性与位图 | 编译期布局验证 + **内核必须重查**（消息可能来自不可信进程） |
| message struct 字段 size/align 一致 | 编译期（D41 无 packed、显式 `_pad` 下可完整检查） |
| region 内访问不越界 | 运行期为主 |
| 跨进程 cap 派生 / 拷贝 / revoke | 运行期 |
| 页表 / TLB / ASID / 中断屏蔽 | 运行期 |
| 栈上界、irq_ctx、锁序 | 编译期分析 + 链接期断言 |

### 1.2 三个层级 + 一条事实链

```
语言层   capability / address space / rights / state token / error / 普通类型
签名层   effect row（may_sleep / irq_ctx / holds(L) / may_alloc / preempt_disabled）
事实层   layout / ABI / 栈 / 锁序 / WCET / panic / cap_offsets（分析生成）
```

**事实链**：AST/sema 附 source span → IL 保留 → codegen 约束 sret / 寄存器类 / naked 栈 / clobber
→ 链接期全程序断言 → `.jhyynb` 成为内核可验证契约。

> **纪律**：任何「不变量」必须落在三个层级之一，否则不得进入语言规范。

### 1.3 一等公民判定

「一等公民」不是语法漂亮，而是**编译器无需读注释即可推理**。六项测试：
参数化 / 类型检查 / 推导 / 拒绝 / 传递 / 事实输出。

| 对象 | 结论 | 承担角色 |
|---|---|---|
| `Cap<T>` | **一等** | 对象身份 + 权限 |
| rights 集合 | **一等** | 权限子集 |
| `ptr<space>`（user/kernel/phys/io） | **一等** | 解引用上下文 |
| 效果 `may_sleep`/`irq_ctx`/`preempt_disabled`/`may_alloc` | **一等（effect row）** | 执行上下文 |
| `holds(L)` | **一等（effect 参数）** | 锁序 |
| BootState | **一等，但封闭状态枚举** | 启动阶段不可倒退 |
| 错误类型 | 普通一等类型 | error as value |
| layout | **一等 metadata** | 生成期事实 |
| ABI 契约 | **一等编译对象，不是类型** | 编译器内部 |
| region | 运行时一等 + 类型轻量索引 | 内核对象 |
| WCET 上界 | **二等（分析结论，不是类型）** | contract |
| panic 可达性 | **二等事实** | contract |
| BootPhase 枚举值 | 普通类型即可 | — |
| IR 字母 `m`（MEMORY class） | 实现类型，不是语言一等 | 后端内部 |

### 1.4 明确不做（同等重要）

- **WCET 不参与泛型单态化** —— 只能是函数属性 + 常量上限
- **锁名不全量泛化**为 `Lock<order>` —— 用显式 `lock_class!` 编号，由 lockdep pass 消费
- **region 生命周期不复制为完整线性类型** —— 内核对象跨线程 / RCU / 引用计数，语言只持 token
- **运行时 ABI 细节不暴露为语言类型** —— 只提供 layout 查询
- **panic category 不是每层签名必写的类型参数**
- **不引入通用代数效应**（handler / CPS / 效应代数）—— 只做闭合效果格的单调传播与禁止规则

---

## §2 事实基线（2026-10-30 逐条回源码 / 规范 / 门脚本核过）

### 2.1 已实装（可直接依赖）

| 事实 | 证据 |
|---|---|
| 四个 amd64 目标全自托管，无 QBE 回退 | `amd64_win` / `amd64_win_freestanding` / `amd64_sysv` / `amd64_sysv_freestanding` |
| **IL 已经是 SSA** —— 前端产 `%tN = add %t2, %t3` | v4.4 寄存器分配器 `codegen_amd64_rcache.jhyy` 正是在 SSA temp 上做的 |
| 前端**已在源码层**算掉常量表达式、清掉死代码 | ⇒ IR 层优化三项合计只有语料 B 的 **1.8%** |
| `&&` / `\|\|` 短路（含嵌套） | `codegen.jhyy:3204-3245`；实测三种嵌套形状均短路 |
| 数字字面量 `0o` / `0b` 前缀 | W-128（v4.0.20） |
| side-file 路径加 pid 后缀 ⇒ 并发编译不互踩 | W-136（v4.0.21）；A/B 实测 12/12 逐字节相同 |
| `0o`/`0b`/`alignof` 等已在回归门内 | regress 279 total（2026-10-30 实测 259 PASS + 0 XFAIL + 20 SKIP） |

### 2.2 P0 待做（逐条 + 证据）

| 项 | 结论 | 证据 |
|---|---|---|
| 实参**类型**检查 | ❌ **未做** | `sema.jhyy:1773-1811`：期望形参类型只用于泛型 enum 变体解析（W-111 遗留），**从不与实参比对**。实测 `takes_i64(1 as i32)` / `takes_ptr(7 as i64)` 编译通过**并运行** |
| 实参**个数**检查 | ❌ **未做（规范里也没记）** | 实测 `takes_one(1, 2)` 编译通过并运行。lang-spec §118 与附录 B 只写了「类型不检查」 |
| `extern fn` 形状限制 | ❌ **未做** | `sema.jhyy:2984` 只跳过 body 检查，无任何形状约束 |
| CLI 多余输入文件报错 | ❌ **静默忽略** | `main.jhyy:1561-1563`：`if input == (0 as *u8) { input = arg; }` ⇒ 第二个输入文件被丢弃 |
| bool 归一化 | ⚠️ **宽度已一致，值未归一化** | 表达式层统一 `'w'`（`ir.jhyy:188`）、data 段用 `'b'`（`ir.jhyy:70`）；但 `codegen.jhyy:3212` 的 `jnz` 判「非 0」⇒ **值为 2 的 bool 仍算真** |
| 顶层非整数初始化 | ❌ **未做** | 实测 `const BAD: [i32; 2] = [1.5, 2.5];` 编译通过并运行。lang-spec §12 自陈「编译器不做 const 检查」⇒ **能力边界，不是 bug** |
| **整数隐式提升** | ❌ **缺失，且规范未记** ⚠️ | `i64 + 1` 报 "type mismatch in binary"；`i64 + (1 as i64)` 通过；`i64 < i64` 正常 ⇒ **不是比较运算符的问题**。而 `let x: i64 = 10` **通过**（字面量在 let/赋值处有 coerce，`sema.jhyy:2169-2175`）⇒ **同一套字面量在两个位置规则不同**。lang-spec §117 只写了「整数与浮点之间不允许隐式转换」，**整数之间没写** |
| UEFI EFIAPI wrapper | ❌ **未实装** | abi §12.8 —— `emit_entry_point` / `no_crt_init` 两个钩子都是空实现 |
| 交叉容器后端（PE/ELF 由 target 决定） | ❌ **未实装** | abi §12.9 —— 容器格式由宿主机 `ld` 决定 |
| Windows 控制台 UTF-8 | ❌ **运行时未设** | abi §12.14 —— `runtime.c` 的 `main` 不调 `SetConsoleOutputCP(65001)` |
| `emit_volatile` | ⚠️ **只发注释、什么都不做** | `codegen_amd64_emit_call.jhyy:2741`；后端**能**识别 volatile（`tok.qbe_type == QBE_VOLATILE_MARKER()`）却**无拒绝机制** |

### 2.3 三处已订正的旧结论

| 旧结论 | 订正 | 影响 |
|---|---|---|
| 「最大单函数帧 229 KiB」 | ❌ **作废**。v4.2.1 后 **max 帧 237680 → 349232 B（341 KiB，反而变大）**，中位帧 **8368 → 288 B**，chkstk 调用 **1045 → 46** | 旧公式用 `max(...)`，在公式池主导时把 `per_fn_alloc` 丢掉了 ⇒ **降帧的真正杠杆是寄存器分配（v4.4 阶段二），不是再调公式** ⇒ P2 的「≤ 16 KiB」要按 341 KiB 重算 |
| 「目标 IL 不应直接升级为完整 SSA」 | ❌ **前提是错的** —— IL 已经是 SSA | 真正缺的是**寄存器分配 + dominance/phi**（后者是 v4.4.2） |
| 「u8 组合比较是 codegen 缺陷」 | ❌ **不成立**。2026-10-30 实测 `eq_u8(200,200)` / `ne_u8(200,201)` / `u8 == 255` / `bool && (…)` 全部正确（exit 0） | 真问题是 **bool 的值未归一化**（`jnz` 判「非 0」）⇒ 与 codegen 宽度无关 ⇒ 修法不同 |

> 📎 **动手前先写十行复现，确定是哪一类。别信任何人的转述，包括 AI 报告。**

### 2.4 一处陈旧的规范条目（本轮审核新发现）

**abi §12.13「旁路文件走固定路径」已经过时** —— W-136（v4.0.21）已给 side-file 加 pid 后缀，
实测 12 路并发逐字节相同。**该条应从偏离表移除**（表头已声明「已修复的偏离会从本表移除，编号随之前移」）。
⇒ 归入 v4.9(OS-5) 的 ABI 收敛一并订正。

---

## §3 分期路线图

### 3.1 总表

两条链：**稳定链**（P0 → P0.5 → P1 → P2 → P2.5）与**能力链**（P3 → P3.5 → P4 → P4.5），
在 P2.5/P3 与 P4 处汇合。版本轴对应见 §3.4。

| 阶段 | 目标 | 关键任务 | 前置 | 验收门（硬指标） | 不做会怎样 |
|---|---|---|---|---|---|
| **P0 止血** | 消除静默错误与不可重复编译 | 实参类型+个数检查；`extern fn` 参数形状限制；CLI 多余输入文件改报错；bool 值归一化；顶层非整数初始化；**整数上下文转换**（D12）；错误可定位（span） | 无 | ① 多余 `.jhyy` 输入报错（不静默忽略）② 并发 8 进程编译无旁路文件竞争 ③ `false && side()` 中 `side` 不执行 ④ 传 `i32` 给 struct 形参编译失败 ⑤ `takes_one(1,2)` 编译失败 | 后续自举无法区分真错误与旧 bug；Windows 上无法并行构建 |
| **P0.5 观测** | 编译器知道自己的最坏行为 | 输出 per-function `frame_local_max`；构建调用图算 `call_path_max`；递归/动态调用显式标记；链接器支持栈断言 | P0 | ① 所有函数两个上界可打印 ② CI 保存基线 CSV ③ 链接期可断言线程栈保留量 ≥ 最坏链 + redzone | 栈问题只能靠运行时溢出发现，内核栈大小无从配置 |
| **P1 反馈环** | 最小镜像真跑在裸金属 | UEFI entry 钩子实装；**按 `--target` 分支链接**（而非按源文件的 `#[no_std]`）；移除无条件 Windows 系统库；`SetConsoleOutputCP(65001)` | P0 | ① 最小 `kernel.efi` 在 QEMU/OVMF 输出 UTF-8 后停机 ② 编译期可选 8 KiB / 16 KiB 栈并触发断言 ③ `#[no_std]` 不再自动加 `-lkernel32 -luser32 -lshell32 -ladvapi32 -lm` | 编译器长期寄生 Windows；能力/IPC 是否可执行永远未知 |
| **P2 栈与分配** | 先证明栈，再压栈 | 栈深度全程序分析 + 链接断言；栈槽 16B 对齐；linear scan 寄存器分配；**禁 XMM 溢出 + 禁 red zone（上下文属性，同期）** | P0.5 | ① **最大单帧 ≤ 16 KiB**（基线 **341 KiB**）② `call_path_max` 受链接期断言 ③ SysV SIMD 参数不产生 8B 对齐 fault ④ 内核上下文 XMM 溢出点 = 0 ⑤ red zone 使用点 = 0 | 中断/IPC 破坏相邻栈；线程栈被迫无谓增大 |
| **P2.5 ABI 收敛** | 关闭已知偏离，形成兼容基线 | 修 sret 阈值/整数预算（§12.1/§12.4）、SysV eightbyte（§12.11）、16B 对齐（§12.6/§12.12）、`alignof(enum)`（§12.2）；PE/ELF 由 target 决定（§12.9）；`asm!`/fence 进 IL 节点；**订正 §12.13 陈旧条目** | P2 | ① 14 条已知偏离降至 **≤ 3 条**且均为显式兼容性例外 ② abi-hash CI 不回归 ③ hosted + freestanding 两套 smoke 全绿 | 新能力代码会在现有调用约定下悄悄错传 cap |
| **P2.75 效果最小集** | 先拦最高危上下文错误 | `with { irq_ctx }` / `with { may_sleep }` 语法 + **调用点直接禁止**（不做全推导、不做多态效果） | P2.5 | `irq_ctx` 内调用 `sleep()` / `alloc()` 编译失败 | 持锁睡眠、PF 路径分配继续靠 review |
| **P3 语言自洽** | 让内核 API 能用普通语言写 | 块表达式；`fn(...)` 类型位置；闭包捕获；`()` 类型位置；`defer` 覆盖末表达式；**结构化内联汇编**（类型化操作数、显式 clobber、效果签名） | P2.5 | ① BootState 迁移可写在块内 ② 函数指针可跨模块传递 ③ hot helper 可写成 1–5 行闭包并被 `#[inline]` 展开 ④ `asm!` 块未声明 clobber 即报错 | BootState、热路径内联、回调契约都无法自然表达 |
| **P3.5 效果骨架** | 完整效果格 | 效果传播；irq/preempt/sleep/alloc 禁止规则；lock class 与有序 acquire/release；`ptr<user>`/`ptr<kernel>` 与地址空间感知别名分析 | P3 + P2.75 | ① `irq_ctx` 内调用 `may_sleep`/`may_alloc` 被拒 ② 锁序图无环 ③ 误用给出确定错误码 ④ `ptr<user>` 直接解引用编译失败 | 持锁睡眠、PF 路径分配继续靠 review |
| **P4a 对象模型冻结** | 纸面冻结 capability 语义 | capability objects manifest：type_tag 白名单、初始 rights、生命周期 owner、cap init phase、version/provenance；**逐类决定 revoke 同步性** | P2.5 | ① 每个 type_tag 逐个有 owner 与 rights 初集 ② revoke 语义（是否同步、是否传播、是否需 quiesce）写明 ③ slot version 方案确定 | `Cap<T>` 改完还要再改一次（第二次 ABI break） |
| **P4b 能力类型化** | 授权链从 wire 提升为类型 | `Cap<T>` 真 T；8 个内置 rights 类型；`derive::<DstR>()` 子集检查；`ptr<phys>`/`ptr<io>`；derive API；`#[ipc_handler]` 全契约；cap_offsets 位图；contract section；`.jhyynb` 实装 | P4a、P3.5 | ① `Cap<i32>` ≠ `Cap<i64>` ② **整数不能 `as` 成 `ptr<phys>`** ③ IPC tag/layout/slot 全检查 ④ 最小 cap init + frame map + IPC demo 闭环 ⑤ contract 被 loader 校验 | 语言无法阻止 frame/endpoint/file 混用与物理地址越权 |
| **P4c 内核数据结构原语** | 内核能用这门语言表达出来 | `Rcu<T>`（grace period 类型）；`PerCpu<T>`（`gs:` 段寻址）；侵入式容器（list_head 等价） | P3（与 P4b **正交**，可并行） | 一个内核链表 + RCU 读侧能用 JHYY 自然表达，无需 unsafe | 内核只能靠反复 unsafe 包装 `list_head` / RCU 惯用法 |
| **P4.5 可信工具链** | 输出可审计事实 | 插桩 pass 族（KASAN / KMSAN / KCFI / shadow stack 对应物）；WCET class；panic 分类；layout 差分测试；per-function section / 冷热分离 / frame pointer 或 ORC unwind | P4b | ① 注入 ≥20 个 bug 被插桩捕获 ② KCFI 对类型不匹配的间接调用报错 ③ 所有契约有 schema + producer version | 无栈展开下故障与越界更难恢复 |

### 3.2 依赖图

```
稳定链:  P0 ──▶ P0.5 ──▶ P1 ──▶ P2 ──▶ P2.5 ──┐
                                                    ├──▶ P3 ──▶ P3.5 ──┐
能力链:  P4a(纸面,可与 P2.5–P3.5 全并行) ─────────────────────────┤
                                                              ├──▶ P4b ──▶ P4.5
                                       P3 ──▶ P4c(与 P4b 正交,可并行) ┘
```

**并行项**：
- P0 内部各任务互不依赖，可全并行
- P0.5 与 P1 可并行（栈测量不阻塞 UEFI 钩子）
- P3 与 P2.5 部分并行（前端语法改造不依赖 ABI 收敛，但合流点需回归）
- **P4a 是纯纸面工作**，可与 P2.5–P3.5 完全并行 ⇒ 建议最早启动

### 3.3 三个硬接口（v4.4.0 阶段二）

> 这三条**必须在 v4.4.0 阶段二（emit 层消费寄存器）同期落地** ——
> 否则约束会晚一版落地，而那正是它开始发作的时刻。

| # | 接口 | 现状证据 | 处置 |
|---|---|---|---|
| **A** | **排除 volatile temp** | `emit_volatile`（`codegen_amd64_emit_call.jhyy:2741`）只发注释；后端能识别 volatile 标记却无拒绝机制；v4.4.0 阶段一资格判据（同基本块 + 无 call + 整数类型）**没有 volatile 这一维**（`codegen_amd64_rcache.jhyy` grep 零命中） | 显式排除 + 响亮失败（形状与阶段一安全网相同） |
| **B** | **禁 XMM 溢出 + 禁 red zone** | 后端全 spill、寄存器池只有 5 个 GPR、**没有省略帧优化**（grep 零命中）⇒ **当前恰好安全** | 持久断言，作为编译期上下文属性 |
| **C** | **16B 对齐** | abi §12.6（栈槽只保证 8B）+ §12.12（SysV 溢出 f64 栈参缺 16B） | **与寄存器分配正交 ⇒ 可提前单独做** |

> ⚠️ **A 的后果**：v4.4 阶段二一旦把 temp 放进寄存器，volatile load 会被缓存 ⇒ **MMIO 读静默失效**。
> ⇒ 「`ptr<io>` 默认 volatile、不合并、不推测读」的承诺在语言层写下来之前，后端必须先给得起。
> ⇒ **本条必须在 `ptr<io>` 落地之前完成。**

### 3.4 与版本轴的对应

每格落在哪个版本，见 [`docs/plans/v4/README.md`](../plans/v4/README.md) 的版本系列索引；
该格的详细 scope 在对应的 `v4.X.Y-plan.md` 里。
`OS-N` 是跨版本重排时**不变**的稳定身份。

| 阶段 | 版本（预留号） | 序号 | 主题 | 系列文档 |
|---|---|---|---|---|
| P0 | **v4.6** | OS-1 | 止血包 | [`docs/plans/v4/v4.6-plan.md`](../plans/v4/v4.6-plan.md) |
| P0.5 | **v4.7** | OS-2 | 观测（栈上界） | [`docs/plans/v4/v4.7-plan.md`](../plans/v4/v4.7-plan.md) |
| P1 | **v4.8** | OS-3 | 反馈环（最小 kernel.efi） | [`docs/plans/v4/v4.8-plan.md`](../plans/v4/v4.8-plan.md) |
| P2 | **v4.8.5** | OS-4 | 栈与分配 | [`docs/plans/v4/v4.8.5-plan.md`](../plans/v4/v4.8.5-plan.md) |
| P2.5 | **v4.9** | OS-5 | ABI 收敛 | [`docs/plans/v4/v4.9-plan.md`](../plans/v4/v4.9-plan.md) |
| P3 | **v4.10** | OS-6 | 语言自洽 | [`docs/plans/v4/v4.10-plan.md`](../plans/v4/v4.10-plan.md) |
| P2.75 | **v4.10.5** | OS-7 | 效果最小集 | [`docs/plans/v4/v4.10.5-plan.md`](../plans/v4/v4.10.5-plan.md) |
| — | v4.11 / v4.12 / v4.12.3 / v4.12.5 | OS-8..OS-11 | lifetime / trait / const generic / HKT | [`v4.11`](../plans/v4/v4.11-plan.md) / [`v4.12`](../plans/v4/v4.12-plan.md) / [`v4.12.3`](../plans/v4/v4.12.3-plan.md) / [`v4.12.5`](../plans/v4/v4.12.5-plan.md) |
| P3.5 | **v4.13** | OS-12 | 效果骨架 | [`docs/plans/v4/v4.13-plan.md`](../plans/v4/v4.13-plan.md) |
| P4a | **v4.13.5** | OS-13 | 对象模型冻结 | [`docs/plans/v4/v4.13.5-plan.md`](../plans/v4/v4.13.5-plan.md) |
| P4b | **v4.14** | OS-14 | 能力类型化 | [`docs/plans/v4/v4.14-plan.md`](../plans/v4/v4.14-plan.md) |
| P4c | **v4.14.5** | OS-15 | 内核数据结构 | [`docs/plans/v4/v4.14.5-plan.md`](../plans/v4/v4.14.5-plan.md) |
| P4.5 | **v4.15** | OS-16 | 可信工具链 | [`docs/plans/v4/v4.15-plan.md`](../plans/v4/v4.15-plan.md) |

**v4.6(OS-1) 有一条硬前置**：实参类型检查会让「整数实参传给指针形参」这类代码**编译失败**
⇒ 必须**先统计** `src0` 自身有多少处实参类型不符（自举是硬门），再决定报错口径
（全拒 / 只拒不安全形态）。**先统计，后改码。**

---

## §4 编译流水线：每一阶段保存可验证事实

### 4.1 Lexer / Parser

**现状**：数字 / 八进制 / 字符 / match 范围等行为有歧义；CLI 多余输入文件静默忽略。

**目标**：解析器只负责无歧义 CST，不替 sema 猜测语义。
- 错误必须带 span（file/source-id、start、end、token-kind）；恢复式解析在第一个错误后仍收集同类错误，
  但不超过每文件 20 个硬错误（避免单字符错误产生数千行派生报错）
- CLI 验收必须区分「未知参数」「多输入文件」「输入不存在」，**不得继续以静默忽略作为默认**
- 块表达式 / match arm 块 / `fn` 类型 / 闭包捕获在语法层预留，P3 再启用
- 「未来版本 token 黑名单」：旧语法保留原始解释，未闭合块和悬空 `=>` 报 E0xxx，不生成后续无意义诊断

**难点**：`1_000_000` / `1.0e10` / `077` 与字符 i32 语义需在兼容模式中冻结。

### 4.2 Sema / 类型系统

**现状**：实参不检查；bool 不归一化；顶层非整数初始化错误；borrow check 极弱（W-105 最小版，词法作用域）；
没有 effect row。

**目标**：两遍 + 约束求解（而非完全 Hindley–Milner）——
第一遍收集模块 / 类型 / 函数 / 泛型形参；第二遍检查签名 / 实参 / 泛型实例化 / 能力约束。

**建议的 IL 交接 schema**：

| Sema 输出 | 属性 | 消费者 |
|---|---|---|
| `ty` | 完整语言类型 | codegen、layout、诊断 |
| `cap_origin` | 来自哪枚源 cap / 哪次 derive | cap check、contract |
| `rights` | 常量位集 | rights subset、wire |
| `addr_space` | user/kernel/phys/io | codegen、codegen 验证 |
| `effects` | may_sleep/irq/preempt/alloc | effect pass、contract |
| `locks` | ordered lock classes | lock order pass |
| `state` | boot state | state pass |
| `layout_hash` | 字段顺序/size/align 的稳定 hash | IPC/ABI facts |
| `stack` | 本地帧上界 / 调用边 | stack analysis |
| `naked` | 手写栈预算、clobber、preserve | asm verifier |

### 4.3 IL / 中端

**现状**：进程内 IL 只有 `w/l/s/d/m`，足以描述宽度和 MEMORY class，却没有类型、效果、cap、layout 与调用图。

**⚠️ 订正**：IL **已经是 SSA**（前端一直产 SSA）。真正缺的是 **寄存器分配 + dominance/phi**
（后者是 v4.4.2）。⇒ 「缺 SSA」这个前提是错的。

**两阶段升级**（第一阶段的 SSA construction 已完成）：
1. **第一阶段剩余部分**：typed value、def/use、dominance、effect row、栈事实
2. **第二阶段**：机器无关优化框架

SSA 已有的前提下，允许 `Cap<T>`、效果与栈槽**不进入 SSA 值集**，仅作 instruction/block annotation ——
这样避免用 SSA phi 表达授权，也不会让效果集合成为每个 use 的显式数据。

**中端应增加的正确性 pass**（优化 pass 默认关闭，正确性 pass 默认开启；
每个优化必须声明它保留哪些 metadata）：

`ComputeStackBounds` · `EffectPropagation` · `LockOrderConstruction` · `CapDerivationCheck` ·
`LayoutFingerprinting` · `AsmContractCheck` · `PanicReachability` · `ContractEmission`

**cap derivation 应由 source cap 的「origin node」表达**：每次 derive / map / borrow 创建节点；
rights 是节点上的常量属性。代码生成把 8 字节 wire 写入位置或调用参数，但编译期分析只证明类型与子集关系。
**对象生命周期仍由内核强制** ⇒「分析图中存在派生路径」≠「对象仍然有效」。

**layout fingerprint 应是稳定 schema，不是原始结构体哈希**：
含类型 kind / size / align / 各字段 offset·size·align·`Cap<T,R>` 标记；
**不混入字段名**（重命名不改 ABI）。变更 layout 时 CI 生成 baseline 与 patch 两种 hash，
报错输出 first differing field。

**panic/termination reachability 应作为控制流事实**：
普通 error 走 `Result`；不可恢复路径分为 `unreachable` / `kernel_oops` / `thread_terminate` / `namespace_revoke`。
无栈展开意味着每条调用边都要显式处理或证明不可达。

### 4.4 后端 pass 全表

每个后端 pass 必须声明：输入 / 输出、读取哪些 IL 事实、是否改变 stack·effects·layout、是否允许增量、复杂度。
「可增量」指只对改动函数及其调用者/被调者重跑；跨过程全程序 pass 至少做到缓存未变输入的指纹。

| Pass | 输入 IR | 输出/动作 | 依赖前端信息 | 拦住哪类需求 | 复杂度 | 可增量 | 排期 |
|---|---|---|---|---:|---:|---|---|
| `ParamTypeChecker` | AST/HIR | 实参类型/个数 + extern 形状错误 | 完整签名 | 静默错误 | 中 | 是 | **OS-1 (v4.6)** |
| `BoolNormalization` | HIR/IL | 规范化 0/1 并报警来源 | 类型、控制流 | 静默错误 | 低 | 是 | **OS-1** |
| `IntContextCoerce` | HIR | 字面量按期望类型解释 | 期望类型 | 规范缺口 | 低 | 是 | **OS-1（D12）** |
| `TlsStageAllocator` | 驱动层 | 每编译唯一 temp path | 无 | 并发 | 低 | 是 | ✅ 已做（W-136） |
| `CapTypeResolver` | HIR | `Cap<T,R>` 节点与子集约束 | `T`、`rights` | 授权 | 中 | 是 | **OS-14** |
| `AddressSpaceChecker` | typed IR | `ptr<space>` 构造/解引用图 | cap origin、space kind | 授权 | 中 | 是 | **OS-12/OS-14** |
| `StackBoundsAnalysis` | CFG/IL | `frame_local_max`、`callee_max`、递归标记 | 调用图、asm budget | 栈 | 中 | 函数级 | **OS-2 (v4.7)** |
| `EffectPropagation` | CFG | `may_sleep/irq/preempt/alloc` | 函数效果、上下文 | 上下文 | 中 | 是 | **OS-7/OS-12** |
| `LockOrderBuilder` | CFG | 有序类、边、强依赖图 | `LockClass`、acquire/release | 死锁 | 高 | 调用图级 | **OS-12** |
| `IpcContractChecker` | HIR/IL | tag/handler/layout/cap_offsets | handler、message struct | IPC | 高 | 函数级 | **OS-14** |
| `NakedInterruptChecker` | IL/asm | 栈预算、clobber、preserve | `#[naked]` 契约 | 中断 | 高 | 是 | **OS-14** |
| `LayoutFingerprinter` | typed IL | size/align/hash/diff report | 字段与属性 | 布局 | 低 | 是 | **OS-5** |
| `CapOffsetsBitmap` | IL/asm emission | slot bitmap、type/rights allowlist | cap 字段、handler | IPC | 中 | 函数级 | **OS-14** |
| `LinearScanRegAlloc` | SSA/CFG | 分配、spill、callee-save | 栈上界、ABI class | 栈/访存 | 高 | 函数级 | **v4.4.0 阶段一已落地**（受限线性扫描：同基本块 + 无 call + 整数类型；5 个 callee-saved GPR；池满退化成栈槽）；**阶段二 = emit 层消费寄存器** |
| `AsmClosureInliner` | IL | inline 决策、带上下文 clone | `fn` 类型、块/捕获 | 热路径 | 中 | 是 | **OS-6** |
| `KasanShadow` | IL | load/store 插桩与红区 | address space、unsafe 边界 | 安全测试 | 高 | 函数级 | **OS-16** |
| `KmsanUninit` | SSA IL | 未初始化来源传播 | def/use | 安全测试 | 高 | 函数级 | **OS-16** |
| `KcfiTypeid` | IL/asm | 函数指针 type id 校验 | 函数类型 | 间接调用 | 高 | 是 | **OS-16** |
| `ShadowStack` | IR/asm | 返回地址备份/check | call graph、noreturn | ROP | 高 | 是 | **OS-16** |
| `PanicReachability` | CFG | termination category | noreturn/效果 | 故障 | 中 | 函数级 | **OS-16** |
| `WcetBoundEstimator` | CFG/loop | bounded class、局部上界 | loop bound、cache/ILP 模型 | 实时 | 高 | 函数级 | **OS-16** |
| `ContractEmitter` | 全程序 facts | `.jhyynb` 契约子节 | 全部 | 契约 | 中 | 缓存增量 | **OS-14** |
| `FactLinkVerifier` | object facts | 全程序上界、禁止环 | 调用图/lock 图 | 栈/锁 | 中 | 是 | **OS-2/OS-12** |

**栈深度 pass 应同时计算两个量**：
- `frame_local_max` = 固定槽 + alloca/地址池 + 对齐填充之和
- `call_path_max(f)` = 全调用图中从 `f` 到叶节点的最大路径深度

链接器验证 `thread_stack_reservation ≥ call_path_max(entry) + redzone`，
并对 `#[naked]`/interrupt 使用作者声明的 `handler_stack_budget`。
递归函数默认不可分析，应显式标 `#[unsafe(recursive, max_depth=N)]`；
动态调用形成未知上界，链接期拒绝进入中断路径。

**线性扫描的顺序是「先做保持栈槽、只分配普通值」**：
保留地址池语义，只为 formula/临时值建 interval，按起始位置排序，冲突则 spill，栈槽继续按固定偏移 ——
这样能在不改变 ABI 兼容性时先压低帧。**图着色只在前端热路径经基准证明尚有 ≥5% 访存收益时引入**
（最优寄存器分配是 NP 难，工业编译器普遍用近似算法）。

**`asm!` 与 fence 必须变成带 clobber 的 IL 节点**：
新版 IL 节点携带输入/输出/内存/clobber、volatile、stack 影响和 source span。
naked 函数必须有手写 prologue/epilogue，并声明使用的栈、是否允许调用、是否保留 callee-save。
interrupt 函数还须证明返回序列与 trap frame 形状匹配。

**插桩应形成可组合的 instrumentation group**：
KASAN（越界 + use-after-scope）→ KMSAN（未初始化传播）→ KCFI（函数指针 type id）→ shadow stack。
实现顺序如此，是因为前两者依赖更强的 def/use/SSA，后两者依赖函数类型与调用图。

### 4.5 汇编发射、链接与产物

**汇编发射不应再使用固定旁路文件**：改为基于 session ID、PID 和随机后缀的唯一临时文件；同一编译退出时清理。
（自举编译器若需跨进程共享，应改为传递 fd 或结构化 JSON 指令序列，而不是文件系统协议。）

**链接分支必须由显式 target 决定**：
target tuple `amd64_win` / `amd64_win_freestanding` / `amd64_sysv` / `amd64_sysv_freestanding` 应成为唯一判据；
`#[no_std]` 只控制运行时入口/依赖解析。PE/ELF 的选择由后端决定，不能继续依赖宿主机 `ld` 的偶然行为。

**`.jhyynb` 的 contract section（kind=9）**：

| Contract 子节 | 内容 | 消费者 |
|---|---|---|
| `stack_table` | per-function frame、call path、recursive flag | loader、线程创建 |
| `effect_table` | may_sleep/irq/preempt/alloc 的调用图结论 | loader、分析器 |
| `lock_order` | class 偏序、边、强依赖 | loader、lockdep |
| `cap_map` | handler 的 cap slot bitmap、type allowlist、rights lower bound | trusted IPC 校验 |
| `layout_table` | type id、size、align、field fingerprint | kernel、CO-RE 式匹配 |
| `naked_table` | handler stack budget、clobber、preserve | loader |
| `termination_table` | panic category、noreturn、recoverable set | fault handler |
| `wcet_table` | bounded class、假设、局部上界 | 实时分析器 |

`debug_group` 适合放可选 source map，**不能承担 loader 语义**。
若坚持扩展 `debug_group`，至少分 `debug` / `contract` 两级 flag，加载器只验证后者。
contract section 必须有 **version、producer ID、source hash、compatibility policy**，
否则旧 loader 可能忽略新增安全字段。

**编译事实应双轨输出**（同 schema 生成，避免双份漂移）：
主 JSON/protobuf 面向工具链（IDE / CI / 静态分析）；`.jhyynb` contract 面向 loader。

---

## §5 语言能力设计（OS 需要的语言特性）

### 5.1 `Cap<T, Rights>` —— 编译器侧实现要点

**为什么 rights 必须进类型参数**（而不只是 phantom 字段或注解）：
若 rights 只作注解，两个 `Cap<Frame>` 一个只读一个可写，**类型相同 ⇒ 可以互相赋值 ⇒ 检查失效**；
注解也无法进入函数签名做传播。⇒ 必须进类型参数。

**但只做 8 个内置有限集合类型，不做任意代数**：

```
R/W/G 三位 ⇒ 2³ = 8 种：None · R · W · G · RW · RG · WG · RWG
```

**为什么不用 const generic 位集 / 依赖类型**：
- const generic 位集：与名义类型系统冲突（常量不是声明名）；单态化上界 2^16 失控
- 依赖类型（`where new_rights <= src.rights`，`new_rights` 是**运行时值**）：JHYY 没有 trait、没有 const 泛型、
  没有任何约束表达机制 ⇒ **在当前架构下不可实现**

**8 个内置类型的代价与收益**：

| 维度 | 结论 |
|---|---|
| 类型等价判定 | 名义比较 + 掩码相等 ⇒ **sema 里加一张 8 项常量表即可**，不需约束求解器 |
| 子集检查 | `TargetR.mask & !SrcR.mask == 0` ⇒ **编译期一条位运算** |
| 单态化上界 | 11 类 type_tag × 8 种 rights = 88 种**理论上界**，实际远少 |
| mangling | `<Base>$<T1>$<T2>` 直接多一段 ⇒ 天然确定性、可复现 |

**派生 API**：

```jhyy
// 静态派生（首选）：编译期完成子集检查
fn derive<T, SrcR, DstR>(src: &Cap<T, SrcR>) -> Cap<T, DstR>

// 运行时派生（次选，用于动态策略）：返回最宽类型 + Option
fn derive_dynamic<T, SrcR>(src: &Cap<T, SrcR>, want: u16) -> Option<Cap<T, RWG>>

// 窄化：运行时子集检查，失败 None
fn narrow<DstR>(c: &Cap<T, RWG>) -> Option<Cap<T, DstR>>
```

**四条 rights 规则**：

| # | 规则 | 编码 | 检查阶段 |
|---|---|---|---|
| R1 | **派生只能清位，不能置位** | `child.mask ⊆ parent.mask` | 编译期 |
| R2 | **root 的 rights 是对象类型允许集的子集** | `root.mask ⊆ allowed_mask(type_tag)` | 编译期（manifest 驱动） |
| R3 | **映射类操作可附加 VM rights，但不产生新 capability rights** | 分离两套位 | 编译期 |
| R4 | **G（grant）不能由 R/W 派生得到** | 需显式授权对象 | 编译期 + 运行期 |

R4 单独说：`grant` 意味着「可以把这个能力再转给别人」，是**权限的放大器**。
若允许 `RW → RWG`，rights 单调收缩就形同虚设。

**编译器侧影响清单**：

| 阶段 | 改动 | 复杂度 |
|---|---|---|
| **Lexer** | 新增 8 个保留字（`R`/`W`/`G`/`RW`/…）；若引入 `unsafe` 概念需新关键字 | 低 |
| **Parser** | 解析 `Cap<T, R>` 双参数；`ptr<phys, R>`；`derive::<T>()` turbofish | 中 |
| **Sema** | ① 8 项 rights 常量表 ② 类型等价加 rights 掩码比较 ③ derive 子集检查（位运算）④ `as` 转换表加禁止规则（整数→`ptr<phys>`）⑤ unsafe 标注 | **中（核心工作量）** |
| **Mangling** | `<Base>$<T1>$<T2>` 直接扩展 | 低 |
| **IL** | `Cap<T,R>` 是 8 字节标量（与 `l` 同承载）⇒ **不新增 IR 概念**，只在类型侧保留标记供后续 pass 消费 | 低 |
| **后端** | 无特殊处理（8 字节标量走 `l`）；**`ptr<io>` 需要禁止重排/合并/投机的 codegen 标记** ⚠️ **与 v4.4 阶段二有硬接口** | 中 |
| **链接 / `.jhyynb`** | cap_init 由 `#[cap_constructor]` 或顶层声明生成；`provenance_seed_off` 填充；contract section 输出 capability facts | 中 |

### 5.2 `ptr<phys>` / `ptr<io>`

**`ptr<phys>` 的构造必须只有三类可信来源**：
① `Cap<Frame>` 的借用映射；② `Cap<Framebuffer>` 显式适配；③ loader 验证过的 `region_table` raw_mmio 条目。
构造函数必须接受原 cap 的借用或显式 lifetime，并产出相同或更小 rights。
**整数、`*mut u8` 和 `ptr<kernel>` 不得隐式转为 `ptr<phys>`。**

**强制机制（最小改动，性价比最高）**：在 sema 的 `as` 转换表里加一条禁止规则 ——
改动量是**一行**，收益是**物理地址越权路径被彻底堵死**。

```jhyy
// 物理指针的 rights 跟随源 cap
fn frame_phys(c: &Cap<Frame, R>)     -> ptr<phys, R>
fn frame_phys_mut(c: &Cap<Frame, RW>) -> ptr<phys, RW>
```

**`ptr<phys>` 与 `ptr<io>` 必须分开**（不是类型洁癖，是副作用与 ordering 不同）：

| 类型 | 语义 | 默认行为 |
|---|---|---|
| `ptr<phys, R>` | 普通 RAM 物理地址 | 可缓存 |
| `ptr<io, R>` | MMIO 设备寄存器 | **默认 volatile**、不合并访问、**禁止推测读** |

推测读（speculative load）对 device register 是致命的 —— 读一次可能就有副作用。
⚠️ **这条承诺在后端给得起之前不能落地**（见 §3.3 接口 A）。

### 5.3 效果系统

**三段式**：声明的上限 + 调用点自动收窄 + 禁止点。

```jhyy
fn schedule() with {};
fn wait_event() -> Event with { may_sleep };
fn slab_alloc(sz: usize) -> *mut u8 with { may_alloc };
fn handle_page_fault(ctx: &mut TrapCtx)
    with { irq_ctx = handler, preempt_disabled }
{
    let _g = page_table_lock.acquire();   // E0510: 可能 sleep/alloc 的路径
}
```

- 缺省时 Sema 从函数体自底向上计算效果格上确界
- 调用时，被调者的效果必须是当前允许效果的**子集**
- 进入 `irq_ctx`、持锁或 `preempt_disabled` 后，调用点只允许 `may_sleep = false`、`may_alloc = false`
- 锁效果不是锁名字的无限集合，而是 `(lock_class, direction, option<order_index>)` 的**有限事实**；
  普通锁只检查有序对，读/写锁才进入强依赖规则

**两阶段落地**（自审结论）：**P2.75 效果最小集**先做 `irq_ctx` + `may_sleep` 两个效果 +
调用点直接禁止（不做全推导、不做多态效果、不做效果变量）—— 这就足以拦住最高频的两类 bug，
成本极低，**不需要等块表达式或 `fn` 类型**。完整效果格仍留 P3.5。

### 5.4 BootState

**启动态应把不可逆步骤变成线性类型推进**：

```jhyy
struct BootState<Stage> { _token: PhantomData<Stage> }
struct NoAlloc; struct HeapReady;
struct PagingOff; struct PagingOn;
struct CpuLocalOff; struct CpuLocalReady;
struct InterruptsOff; struct ThreadingReady;

fn enable_paging(s: BootState<PagingOff>) -> BootState<PagingOn> { ... }
fn init_heap(s: BootState<PagingOn>) -> BootState<HeapReady> { ... }
```

**状态迁移必须消费旧 token**：`enable_paging(s)` 的 `s` 按值取得，旧状态不能复用。
这样既不需要完整 trait，也不需要借用检查器理解硬件。
接口仍可标 `#[unsafe]` 并写明「调用者证明当前 CPU/页表状态」，但状态类型让误调用**从文档升级为类型错误**。

> **块表达式是 BootState 的硬前置** —— typestate 本质是带顺序的语句序列；
> 若块不能产生值、函数末表达式不形成连续控制流，状态推进就只能停在函数边界，
> 临时状态与错误恢复会退回全局可变变量。

### 5.5 `#[ipc_handler]`

**handler 不应只是属性标记，而应成为全程序契约**。编译器在一个 `.jhyynb` 内检查：
tag 唯一（或 `service_version+tag` 复合 key 不冲突）；handler 签名与 message/reply struct **双向一致**；
每个 `Cap<T>` 字段落在合法对齐槽；`cap_offsets` 不重叠、不越界；
handler 所需的 rights 不超过调用 ABI 可携带范围；调用前后栈与效果合法。

```jhyy
#[ipc_handler(tag = 0x1001, version = 1, cap_slots = 1)]
fn handle_map_frame(msg: &MapFrameMsg) -> MapFrameReply { ... }

#[repr(c, align = 8)]
struct MapFrameMsg {
    frame: Cap<Frame, Read|Write>,
    vaddr: u64,
    _pad: [u8; 4],
}
```

**D16 wire 仍由内核解析** ⇒ 内核必须检查 offset、slot 存在性和 rights，
但 **trusted sender 的布局不一致被前移到编译期**。

**错误信息必须指出迁移路径**，不能只说「不匹配」：

```text
E0601: capability rights escalation
  --> src/main.jhyy:12:28
   |
12 |     let bad: Cap<Frame, RWG> = ro.derive::<RWG>();
   |                                ^^^^^^^^^^^^^^^^^^
   |
   = note: source capability has rights `R` (0b001)
   = note: requested rights `RWG` (0b111)
   = note: rights may only be reduced on derive, never increased
   = help: derived rights must satisfy `DstR ⊆ SrcR`
```

### 5.6 块表达式、函数类型、闭包、结构化内联汇编

**这不是奢侈语法**：

- **块表达式**是 BootState 的硬前置（§5.4）
- **`fn(...)` 类型位置**是 IPC / 中断回调契约的最低要求 ——
  当前没有函数指针类型语法，而 `#[naked]` interrupt、MS x64 函数指针和 IPC stub 都要求编译器知道参数/返回值的 lowering。
  最小方案不必先实现高阶类型，只要允许函数类型出现在参数、变量和返回值位置，
  并强制其 ABI / 效果 / 是否 `#[naked]` 匹配。
- **闭包捕获**目前**被编译器明确报错**（捕获外层变量在 MVP 范围外）。
  它阻止 hot helper 携带本地 token，迫使开发者把大量两行函数写成顶层名字。
- **`#[inline]` 只在函数体为单条 `return expr;` 时展开** ⇒ 内核热路径**一个 helper 都内联不了**。
- **结构化内联汇编**（自审新增）：`asm!` 仍是字符串（abi §8）——
  W-113 只修了「内联位置」这个正确性 bug（此前字节被 append 到 `.s` 末尾 = 落在所有函数之外 = 死字节），
  **没做结构化改造**。目标：类型化操作数、显式 clobber、效果签名；
  `asm!` 块未声明 clobber 即报错。

---

## §6 自审发现的编译器侧缺口

> 审计方法：对六份基线文档做关键词出现统计 + 语境确认，不凭记忆断言。
> 统计结果：`FPU / 浮点寄存器 / XMM` = 0 · `register block / 位域` = 0 · `别名分析` = 0 ·
> `frame pointer / ORC` = 0 · `冷热分离` = 0 · `RCU` 只在需求清单、路线图无排期 ·
> `PerCpu` 同上 · `侵入式容器` 同上。

### 6.1 真遗漏（普适内核约束，不因「从零开始」而消失）

| # | 缺口 | 为什么是真遗漏 | 落点 |
|---|---|---|---|
| 1 | **禁 FPU/SIMD 溢出 + 禁 red zone** | 硬件/内核惯用法的硬约束。当前**恰好安全**（全 spill + 显式帧 + 无省略帧优化），**但正因如此**问题会在 P2 那一刻诞生 | **§3.3 接口 B —— v4.4.0 阶段二同期** |
| 2 | **register block / 位域语法** | 硬件描述一等语法。Cap 草案只给了 `ptr<io>`，没有寄存器块声明 | P4b |
| 3 | **地址空间感知别名分析（优化侧）** | 只做了安全侧（`ptr<phys>` 派生），**优化侧零覆盖** | P3.5 |
| 4 | **per-function section / 冷热分离 / frame pointer 或 ORC unwind** | 只有「能出 EFI」；段级布局与 unwind 表全缺 | P4.5 |
| 5 | **`Rcu<T>` / `PerCpu<T>` / 侵入式容器** | **最严重遗漏** —— 决定「内核能不能用这门语言表达出来」。所有 P 阶段都在解决「内核安不安全」，**没有一个阶段在解决「内核能不能写出来」** | **P4c** |
| 6 | **`ptr<user>` / `ptr<kernel>` / `ptr<percpu>`** | 只有 `ptr<phys>`/`ptr<io>` | P3.5 |
| 7 | **ABI 单一真源** | 能力微内核下价值极高：endpoint 一处声明应同时生成内核侧 + client stub + IPC dispatch 表 + 契约元数据 | P4b |
| 8 | **结构化内联汇编** | 见 §5.6 | P3 |
| 9 | **`&Allocator` 无全局隐式分配器** | 显式分配器是 Zig 的核心特性之一 | P3.5 |
| 10 | **别名分析 / 冷热分离** | 同 #3 / #4 | P3.5 / P4.5 |

**额外**：**「有经验的 C 程序员两周内能上手吗」**这条验收门此前**零讨论**。
设计上目前符合（8 个内置 rights 类型、无借用检查、无生命周期标注，学习曲线远低于 Rust），
但**必须写成验收门**，否则会随着特性堆叠悄悄失守。

### 6.2 框架错配（明确不做 + 理由）

审计第一轮的框架是以 **Linux 为隐含参照系**写的。JHYY 不是 Linux，没有那些历史包袱 ——
**有些「缺失」是优势而非缺陷**。

| 条目 | 为什么不适用 | 处置 |
|---|---|---|
| **Kconfig 配置空间** | JHYY 无 Kconfig，无 3000 万行历史配置 | 降级为「target × 属性 × flag 组合矩阵可达性」，放入 P2.5 而非独立项 |
| **static keys / alternatives（代码自修改）** | Linux 应对多硬件变体的历史包袱 | **明确推迟到 P5+**，写进「不做」清单 |
| **Coccinelle 语义补丁** | 用于批量改写历史代码，JHYY 没有历史代码 | **明确不移植**，写进「不做」清单并说明理由 |
| 一等 C 互操作的「逐文件增量迁移」 | jhyy_OS 不从 C 迁移 | 降级：只需 FFI 边界可用，不需要大规模迁移工具 |
| **重度单态化** | Cap 草案算 88 种组合上界，但**无全局编译时间预算** | 需要时再加预算机制 |

### 6.3 外挂工具内化表（可度量形式）

> **每完成一期，对着这张表数。**

| 外挂工具 | 它守的规则 | JHYY 内化形态 | 阶段 | 状态 |
|---|---|---|---|---|
| **objtool** | 栈帧校验、入口契约、noinstr | 栈深度双上界 pass + `#[naked]`/interrupt 契约检查 | OS-2 / OS-4 | ✅ 有排期 |
| **lockdep** | 运行时锁序环检测 | 编译期锁序图 + 环检测 | OS-12 | ✅ 有排期 |
| **sparse** | `__user` 地址空间注解 | `ptr<user>`/`ptr<kernel>` 类型 | OS-12 | 📋 |
| **pahole** | 结构体布局检查 | ABI 布局哈希 + 布局差分测试 | OS-5 | ✅ 有排期 |
| **`-fstack-usage`** | 事后栈用量报告 | per-function facts → contract section | OS-2 | ✅ 有排期 |
| **`-mgeneral-regs-only`** | 禁浮点寄存器 | 上下文属性（禁 XMM 溢出 + 禁 red zone） | **v4.4.0 阶段二 + OS-4** | 📋 |
| **Coccinelle** | 语义补丁批量改写 | **不移植**（无历史代码） | — | ✅ 有理由地不做 |

**当前 7 项中 5 项有排期，2 项需补。**

---

## §7 规范一致性与 ABI 收敛

### 7.1 三处规范冲突：`Cap` wire 布局（**编译器侧动作**）

⚠️ **两份锁定规范对 `Cap<T>` 的 8 字节 wire 布局不一致 —— `rights` 的字节偏移差 1。**

| 来源 | 布局 |
|---|---|
| lang-spec v4.0.0 §2.6 | `cnode_idx:u32@0` · `depth:u8@4` · **`rights:u16@5`** · `padding:u8@7` |
| abi v4.0.0 §2.5 | 同上（**逐字一致**） |
| binary-format v1.0.0 §2（引 D6 + D23） | `cnode_idx:u32@0` · `depth:u8@4` · **`_pad:u8@5`** · **`rights:u16@6`** |

**判定证据**：lang-spec §2.6 自带构造示例
`let c: Cap = 0x0000030200000007 as Cap;   // cnode=7, depth=2, rights=R|W`
小端展开 = `07 00 00 00 | 02 | 03 00 | 00`
⇒ **只有在 `rights@5` 下才解出注释说的 cnode=7 / depth=2 / rights=R|W**；
按 `rights@6` 解出来是 `rights=0x0000`、`_pad=0x03` ⇒ **示例自相矛盾**。

**另一条独立事实**：`type_tag` / `cap_init` 词汇表**只存在于 binary-format**
（`grep -l type_tag docs/abis/*.md` 只有它）⇒ lang-spec 与 abi 互相印证，binary-format 是孤本异类。

**为什么这条比「rights 有几位」更硬**：
「有几位」只影响语义集合大小；
**「在第几字节」** —— 凡是按字节读写 cap 的地方（IPC 原地改写 `cnode_idx`、cap_init 复制 rights 字段、
`.jhyynb` 序列化）**两种布局算出的字节位置不同** ⇒ **同一份程序用不同规范实现会静默读写错位 1 字节**。

**当前不发作的原因**：`Cap<T>` 的 `T` 不被解析、无 `.cnode_idx`/`.depth`/`.rights` 字段访问
⇒ **没有任何代码按字节拆 cap**。⇒ **现在改是零成本，等 `Cap<T>` 真 T 落地后再改就是 ABI break。**

**编译器侧动作**：
1. **单一真源 = lang-spec §2.6**；abi §2.5 与 binary-format §2 改为引用它
2. binary-format §2 那行改为 `rights:u16@5` + 一句「本字段与 lang-spec §2.6 同源；改动须三处同步」
3. **加规范一致性门** `scripts/dev/check_spec_consistency.py`：
   从三处解析 Cap 布局的 `(offset, size, type)` 三元组 + rights 位宽 ⇒ **不一致即红**，接进 CI。
   （这次冲突能活三个月，就是因为**没有一道门**。）

> 完整的 12 条待拍板设计见 OS 侧文档 § 12 与 [`JHYY_待拍板设计.md` 的 git 历史](https://github.com/JiHuiYiYou)。

### 7.2 ABI §12 的 14 条已知偏离

| # | 项 | 性质 | 收敛于 |
|---|---|---|---|
| 12.1 | struct/enum 返回值在所有目标无条件走 sret，无大小阈值 | 偏离 SysV | OS-5 |
| 12.2 | `alignof(enum)` 硬编码 4 | 内部不一致 | OS-5 |
| 12.3 | SysV 的非 struct 标量参数借 Win 分类器决定 IR 字母 | 隐患 | OS-5 |
| 12.4 | SysV 下 MEMORY class 参数与寄存器溢出参数混排 → 编译期报错 | 能力边界 | OS-5 |
| 12.5 | sret 槽大小 `max(4, sizeof(T))` vs enum 按 `total_size` 拷贝 | 理论边界 | OS-5 |
| 12.6 | 栈槽只保证 8 字节对齐 | 能力边界 | OS-4（**可提前**） |
| 12.7 | 全 spill 只保存 RBP；max 帧 341 KiB / 中位 288 B | 实现特征 | OS-2 / v4.4 阶段二 |
| 12.8 | UEFI EFIAPI wrapper 未实装（两个钩子空实现） | 未实装 | OS-3 |
| 12.9 | 无交叉容器后端（PE/ELF 由宿主机 ld 决定） | 能力边界 | OS-5 |
| 12.10 | 无 aarch64 / riscv64；`.jhyynb` 仍是设计稿 | 未实装 | OS-14（`.jhyynb` 实装） |
| 12.11 | SysV eightbyte 宽度规则只对第 0 个成立 | 偏离 SysV | OS-5 |
| 12.12 | SysV 溢出的 f64 栈参缺 16 字节对齐 | 偏离 SysV | OS-4（**可提前**） |
| **12.13** | **旁路文件走固定路径** | ⚠️ **已过时 —— W-136 已修** ⇒ **应从表移除** | OS-5 顺带订正 |
| 12.14 | Windows 控制台 UTF-8 不由运行时设置 | 实现特征 | OS-3 |

**验收门**：14 条降至 **≤ 3 条**且均为显式兼容性例外；abi-hash CI 不回归；
hosted + freestanding 两套 smoke 全绿。

---

## §8 待拍板 —— 编译器侧 4 条

> 完整的 12 条（D1–D12）见 OS 侧文档 § 12 与 git 历史。
> 下列 4 条是**编译器侧直接落地**的；**它们都不阻塞任何后续版本 ⇒ 可先拍**。

### D12 —— 整数之间要不要隐式提升？【建议：只在字面量位置提升 + 写进规范】

**事实基线**（2026-10-30 实测）：

| 写法 | 结果 |
|---|---|
| `i64 + (1 as i64)` | ✅ 通过 |
| `let x: i64 = 10;` | ✅ 通过（字面量在 let/赋值处有 coerce，`sema.jhyy:2169`） |
| **`i64 + 1`** | ❌ **报 "type mismatch in binary"** |
| `i64 < i64`（变量比变量） | ✅ 通过 ⇒ **不是比较运算符的问题** |

⇒ 同一套整数字面量，在 `let`/赋值处被 coerce，在二元运算处不。
lang-spec §117 只写了「整数与浮点之间不允许隐式转换」，**整数之间既没写允许也没写禁止**
⇒ 这是一条**规范缺口**，不是实现 bug。

**选项**：F1 全面整数提升（C 风格）❌ / F2 保持现状只写规范 ⚠️ / **F3 只在字面量位置提升** ✅ /
F4 连 `let x: i64 = 10` 也要写 cast ❌（破坏现有代码，收益不成比例）

**建议：F3 + 把规则写进规范。**
- **痛点是字面量，不是变量**：`i64 + 1` 极常见；`i64 + some_i32_var` **是类型错误，应该报错**
  ⇒ F1 会把后者也放过 ⇒ **反而丢掉类型检查**
- **F3 是一处改动**：sema 里字面量 coerce 的逻辑**已经有**（let 位置），复用到二元运算与实参位置即可
- ⚠️ **与 OS-1 的实参检查有交互**：`takes_i64(1)` 会变合法 ⇒
  **OS-1 的报错口径必须区分「字面量可隐式转换」与「真的类型不符」** ⇒ 两者要**同批落地**，
  否则实参检查会把合法的字面量调用判死

**建议的规范条文**：

> 整数字面量在**期望类型已知**的位置（let / 赋值 / 函数实参 / 二元运算中另一侧为整型）按期望类型解释；
> **两侧都是变量时不做隐式转换** ⇒ 类型不同即报错。
>
> `i64 + 1` ✅（1 按 i64 解释）· `let x: i64 = 10` ✅ · `takes_i64(1)` ✅
> `i64 + i32_var` ❌ · `i32_var + i64_var` ❌

**产物**：lang-spec 补一节「整数上下文转换」；sema 复用 coerce；
**门**：新测试 `spec_int_ctx_coerce.jhyy`（正向三项 + 反向 `i64 + i32_var` 必须报错）。

### D5 —— 是否引入 `unsafe` 关键字？【建议：不引入，用属性】

**事实基线**：`grep -rn unsafe compiler/src0/*.jhyy` ⇒ **零命中** ⇒ `unsafe` 完全不存在。

**建议**：`#[trusted]`（模块/文件级）+ `#[unsafe_cap_ctor]`（函数/语句级）。
理由：
1. **`unsafe` 是一整套语言级语义**（块 / fn / trait / impl / lint 生态 / 与 borrow 的交互），
   而 JHYY 连 `&mut` 的完整语义都还停在 W-105 的**最小版**（词法作用域）⇒ 成本远超需求
2. JHYY 要的只有一件事：让「绕过 capability 构造」**可标注、可统计、可审计** ⇒ 属性就够了
3. **属性语法已经存在**（`#[naked]` / `#[no_std]` / `#[link_section]` / `#[ipc_handler]`）⇒ **零新语法** ——
   这是决定性理由
4. **模块级更贴合实际场景**：cap 构造只发生在 **kernel bootstrap**（整个模块都是特权）

**明确不做**：unsafe 关键字 / unsafe fn / unsafe trait / unsafe 块 ⇒ 留到「需要 unsafe fn 时」再设计。

### D9 —— `as Cap` 逃生舱保留吗？【建议：保留但收敛】（与 D5 同批）

- **完全禁掉是做不到的**：内核 bootstrap 阶段**确实需要**手工构造 root cap
  ⇒ **后门在语义上不可消除，只能让它可审计**
- ⇒ 目标不是「没有后门」，而是「**后门数量可度量、位置可审计、越权不可能**」
- 收敛手段：`from_raw` 是**唯一**构造入口；`as Cap` 保留为 **deprecated 别名**，
  且**只在 `#[trusted]` 范围内可用** ⇒ 在普通模块里写 `as Cap` ⇒ **编译期报错**
- 编译器输出 `unsafe_ctor_count` + `unsafe_ctor_offs` 进 contract section
  ⇒ CI 可断言 `kernel.efi` 的 count ≤ N 且只在 bootstrap 模块

**capability facts schema（写进 `.jhyynb` contract section）**：

```c
struct CapContract {
    cap_type_count:      u16,     // 该 binary 使用的 Cap<T,R> 组合数
    // 每种组合一条：{ type_tag:u32, rights_mask:u16, monomorphic_count:u32}
    unsafe_ctor_count:   u32,     // 【关键】unsafe 构造点数量
    unsafe_ctor_offs:    []u32,   // 各构造点的 .text 偏移，供审计
    derive_edges:        []u32,   // 静态派生边
    ptr_phys_sites:      []u32,   // ptr<phys> 派生点
}
```

> **`unsafe_ctor_count` 是最有价值的一个字段** —— 它把一个「后门」变成**可度量、可设阈值的指标**。

### D6 —— `derive_dyn` 是否允许存在？【建议：允许，重命名为 `derive_dynamic`】

1. **完全禁止会逼出更糟的写法**：用户会直接 `as Cap` 手搓
   ⇒ **把一个受控的降级变成一个完全不受控的后门** ⇒ 禁 `derive_dyn` 反而**更不安全**
2. **「名字丑」是对的** ⇒ `derive_dynamic` 比 `derive_dyn` 更明显
3. **返回最宽类型是诚实的**：编译器确实不知道运行时 rights
4. **但 `narrow` 本身要过子集检查**：运行时检查 `TargetR ⊆ SrcR`，失败返回 `None`
   ⇒ 这是**运行时唯一一次权限检查** —— 且**内核侧还要再查一次**（用户态的检查只是加速带）

---

## §9 验收计数器与度量

### 9.1 一句话判断标准

> **每完成一期，问：又有多少条规则从「文档里写着」变成了「编译不过」？**
> 这个数字不增长，就是在做工程优化而不是在做语言。

### 9.2 三类可测指标

| 类别 | 指标 | 当前值 |
|---|---|---|
| **规则转化率** | 「文档里写着」→「编译不过」的规则条数 | 逐期递增（见 §9.1） |
| **静默错误清零** | P0 六项中已闭合的项数 | **0 / 6**（P0 未启动） |
| **静默错误残余** | `spec_argc_argv` 式「验的不是它声称的东西」的门数 | 回归套件 **0 XFAIL**（2026-10-30：259 PASS + 0 XFAIL + 20 SKIP / 279 total） |

### 9.3 每个新特性的准入检查表

1. 它是**语言层 / 签名层 / 事实层**中的哪一层？（不属于任何一层 ⇒ 不得进规范）
2. 它把哪条规则从「文档」变成「编译不过」？
3. 它通过六项一等公民测试吗？哪几项不通过？
4. **有经验的 C 程序员两周内能上手吗？**（§6.1 末尾）
5. 它的产物能被 loader / 内核 / 外部工具**独立验证**吗？
6. 它引入了新的**逃逸舱**吗？逃逸舱可度量、可审计吗？

---

## §10 明确不做清单

| 不做 | 理由 |
|---|---|
| GC | 内核不用 |
| 异常栈展开 | 无 unwinding ⇒ 改为显式错误分类 + 终止面 |
| 默认 async | v4.16 起独立线，不进 OS 线 |
| **通用代数效应**（handler / CPS / 效应代数） | 只做闭合效果格的单调传播与禁止规则 |
| **const 泛型 + 依赖类型** | rights 走 8 个内置有限集合类型 |
| **unsafe 关键字 / unsafe fn / unsafe trait / unsafe 块** | 用 `#[trusted]` / `#[unsafe_cap_ctor]` 属性替代（D5） |
| **重度单态化** | 88 种 rights 组合上界可控；无全局编译时间预算 |
| **Kconfig 式配置空间** | 降级为「target × 属性 × flag 组合矩阵」 |
| **static keys / 代码自修改** | Linux 的历史包袱；推迟到 P5+ |
| **Coccinelle 语义补丁** | 无历史代码可批量改写 |
| **图着色寄存器分配**（当前） | 只在前端热路径经基准证明 ≥5% 访存收益后引入 |
| **CHERI 兼容 ABI 承诺** | amd64 无 CHERI；只预留 version/provenance 位 |

---

## §11 不确定性与需补材料

| 项 | 说明 |
|---|---|
| **「16 KiB 目标」是否可达** | 按 341 KiB 基线，v4.4 寄存器分配（槽数 → ~24%）理论给到 ~85 KiB ⇒ **单靠寄存器分配到不了 16 KiB** ⇒ OS-4 之后还需别的杠杆（帧布局 / 池分离 / 更多寄存器 / 降 temp 数）⇒ **16 KiB 应标注「可达性未证」** |
| **建议的可判定硬门** | **自举编译器自身（1045 个函数）的 `call_path_max × frame ≤ 64 KiB`** —— 自举编译器是本仓最坏情况（**1045 个真实函数**，per `docs/perf/self-backend-baseline-2026-10-29.md`；`main.jhyy` 的 max temp id 已达 **6 万量级**，见台账 W-120），它的最坏调用路径若能在 64 KiB 内跑完 ⇒ 内核栈若跑得动自举编译器，就跑得动绝大多数内核代码。⚠️ 这是**类比，不是证明** ⇒ **OS-4 的验收门数字应据此复核** |
| **编译器源码结构 / 现有 pass 清单 / 错误码总表** | 曾是「补材料」清单的 #1；本文已按源码补齐 P0 六项的 `file:line` 证据。**剩余缺口**：增量编译缓存、测试框架细节 |
| **jhyy_OS 的 coordination.md 与 D-lock 全集** | 目前只知道 D6/D16/D23/D40/D41/D42/D43/D44/D-GUI-2/D-GUI-12 ⇒ **OS 侧设计文档已于 2026-10-30 全部删除**（git 历史保留）⇒ **跨项目设计基线现单点落在本仓 `docs/coordination/`** |
| **v4.8(UEFI / kernel.efi) 本地不可完全验证** | 需 QEMU/OVMF；OS 仓设计文档已删 ⇒ 需重新确认 loader 侧的预期 |
| **12 条待拍板** | 已给设计稿（见 OS 侧文档 § 12）⇒ **拍板前 OS-13(P4a manifest) 与 OS-14(Cap 真 T) 不能启动** |

---

## §12 交叉引用

| 文档 | 用途 |
|---|---|
| [`docs/coordination/JHYY_OS侧设计终版.md`](JHYY_OS侧设计终版.md) | 内核形态 · capability 对象模型 · `.jhyynb` 契约 · 语言—内核边界 · OS 侧 22 条需求 · OS 侧 8 条待拍板 |
| [`docs/abis/jhyy-lang-spec-v4.0.0.md`](../abis/jhyy-lang-spec-v4.0.0.md) | 语言规范（锁定 2026-10-24） |
| [`docs/abis/jhyy-abi-v4.0.0.md`](../abis/jhyy-abi-v4.0.0.md) | ABI 白皮书（锁定 2026-10-24）· §12 已知偏离 |
| [`docs/abis/jhyy-binary-format-v1.0.0.md`](../abis/jhyy-binary-format-v1.0.0.md) | `.jhyynb` 二进制格式（**设计稿，未实装**） |
| [`docs/plans/v4/README.md`](../plans/v4/README.md) | **版本系列索引** —— 每个版本槽一份 `v4.X.Y-plan.md`（性能线 6 + OS 线 16） |
| [`docs/plans/v4/self-backend-perf-plan.md`](../plans/v4/self-backend-perf-plan.md) | v4.2+ 自研后端性能线（v4.4 寄存器分配） |
| [`docs/workarounds.md`](../workarounds.md) | W-NNN 台账（ACTIVE = 0） |
| [`docs/internal/build.md`](../internal/build.md) | 构建 / 调试 / self-backend 坑 |
| [`docs/FACTS.md`](../FACTS.md) | 回归套件清单与运行方法 |
| [`docs/perf/self-backend-baseline-2026-10-29.md`](../perf/self-backend-baseline-2026-10-29.md) | 帧/访存基线数据（341 KiB / 288 B 的来源） |
