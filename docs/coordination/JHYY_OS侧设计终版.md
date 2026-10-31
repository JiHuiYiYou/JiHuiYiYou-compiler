# JHYY OS 侧设计终版

> **本文定位**：jhyy_OS 的**最终设计文档** —— 从三份规范逐条核过的事实基线，
> 加上内核形态锁定、capability 对象模型、`.jhyynb` 契约、语言—内核边界与实现顺序。
>
> **配套文档**：[`docs/coordination/JHYY_编译器侧设计终版.md`](JHYY_编译器侧设计终版.md) —— 编译器分期路线、pass 清单、
> 规范一致性门。
>
> **事实基线纪律**：唯一实现事实来源是三份规范（lang-spec v4.0.0 / abi v4.0.0 /
> binary-format v1.0.0）+ 编译器源码。**规范没有记载的，不能宣称已锁定** ⇒ 进 § 14 的「事实缺口归属」（每项都有归属槽与产出物）。
> ⚠️ **binary-format v1.0.0 是设计稿，未实装**（abi §12.10）⇒ 凡只由它记载的结论都注明来源。
>
> **本文取代**（原 6 份，内容保留在 git 历史）：
> `JHYY_决策总纲.md` · `JHYY_OS_内核模型与语言需求.md` · `JHYY_Cap类型语义草案.md` ·
> `JHYY_待拍板设计.md` · `JHYY_设计自审_对照K框架.md` · `JHYY_编译器全阶段方向与路线图.md`（OS 相关部分）。

---

## §0 一句话结论

**jhyy_OS 的内核身份应锁定为能力微内核，但首版物理结构采用特权分层。**
三份规范已经提供对象分类（type_tag）、cap 授权（rights/depth）、IPC 原地 cap 传输、
区域声明与 4 KiB 对齐的足够线索 —— **继续选择传统混合内核只会让这些设计失去语义承担**。

**能力模型的最小正确性条件比 GUI 对象数量更重要**：
depth 只解决派生层级，不能单独解决 revoke；padding 只提供未来空间，不能单独解决 slot reuse；
cap_init 只声明初始对象，不能单独解决生命周期；handler 属性只标记入口，不能单独保证 message/offset 一致。

---

## §1 内核形态

### 1.1 形态锁定：能力微内核（长期）+ 混合内核工程边界（首版）

**决定性事实不是 `Cap<T>` 的名字，而是三份规范共同锁定的完整授权链条**：
对象类型由 cap_init 的 `type_tag` 声明；对象引用由 `cnode_idx` 与 `depth` 定位；
权限由 `rights` 约束；跨域传输由 IPC dispatch 的 `cap_offsets` 重新绑定；
地址空间 / 共享内存 / 显存 / I/O 区域由 region_table 声明。

⇒ 若采用单一内核并用全局函数指针或共享状态授予设备访问，**这套二进制格式将变成装饰**：
cap_init 只剩「启动时开权限」，cap_offsets 退化成普通 fd 传输，region_table 退化为 mmap 参数。

**能力微内核的三项真正收益**：
1. **故障域由 capability 授权决定**，而不是由进程是否拥有 root 决定
2. **对象服务可独立重启** —— 即使早期不利用这一点，二进制格式也不需要迁坟
3. **形式化与审计的目标面可收敛**到 CSpace、VSpace、调度/中断/IPC 与少数对象类型

### 1.2 三层组织：Tier 0 / 1 / 2

> **不建议第一版就把网卡、磁盘、GPU、USB 全部用户态化。**
> 对小团队而言，用户态驱动带来三类风险：跨进程 IPC 与映射协议、驱动崩溃后的设备 quiesce、
> capability 协议和硬件状态机的双重实现。

| Tier | 内容 | 特权级别 |
|---|---|---|
| **Tier 0** | 对象 / 空间 / IPC / 调度 / 中断 / cap 撤销、最低页表操作、platform 抽象 | 真正可信计算基 |
| **Tier 1** | 物理内存管理、早期 console、必要的 bus/中断控制器、根任务、bootstrap | 特权服务（随 kernel.efi 启动） |
| **Tier 2** | 可重启用户服务 | 用户态 |

**Tier 0 与 Tier 1 可以在同一特权级别，却必须用不同编译单元、独立 API 边界和独立 capability 入口隔离。**
这样既保留未来向严格微内核迁移的二进制与类型边界，又避免一次完成全部设备隔离。

### 1.3 形态对照表

| 形态 | 与现有规范相容性 | 首次出原型成本 | 能力隔离收益 | 结论 |
|---|---|---|---|---|
| **能力微内核** | 高；三份规范几乎就是其对象与授权模型 | 中高 | 高 | **长期目标，锁定** |
| **初始混合 / 特权区** | 可容纳早期物理内存、platform、console | 低 | 中 | **首版工程形态** |
| 传统混合内核 | 只有 ABI 可复用，cap 格式失去必要性 | 低 | 低 | 不推荐 |
| 纯单体内核 | 容易实现 syscall 集合 | 低 | 极低 | 与 type_tag/cap_offsets 冲突，明确排除 |

### 1.4 首版架构冻结必须回答的问题

**规范没有给出最小内核对象集合** —— 没有线程、调度类、就绪队列、时间源、中断控制器对象、
页表根、ASID/PCID、地址空间、物理 frame 元数据、分配器 slab、CNode 自身布局或 revoke 队列。
⇒ 「能力微内核」是**形态建议**，不能写成 jhyy_OS 的对象清单。首次架构冻结至少回答：

1. 线程与地址空间是否分离
2. 内核对象是否统一 header
3. CNode 是否可映射与增长
4. **revoke 是否同步**
5. 中断是否也是 capability
6. page fault 由内核还是用户 pager 处理

---

## §2 事实基线：三份规范锁定的 capability ABI

### 2.1 `Cap<T>` —— 8 字节 wire

```
offset  size  field        type
0       4     cnode_idx    u32     CSpace slot index
4       1     depth        u8      CDL 深度
5       1     gen          u8      slot 复用代数(slot 被复用时 +1)
6       2     rights       u16     bit0=R, bit1=W, bit2=G
```

小端序。来源：lang-spec §2.6 与 abi §2.5（**字段表逐字一致**；正文里两处「布局契约」的章节链接指向各自文档，故非全字节相同）。
⚠️ binary-format §2 曾记载 `_pad:u8@5` + `rights:u16@6` ⇒ **冲突，已裁决为自然对齐布局**
`cnode_idx@0 · depth@4 · gen@5 · rights@6`（binary-format 已于 2026-10-31 订正；详见 §3.6）。

**三个独立维度**：slot 索引、从 CNode 根出发的层级、权限。
它不只是「一个整数」—— **slot 语义只有在 CNode 与 depth 共同解释时才有意义**；
这是典型 seL4 CSpace 思路，而不是单纯句柄表。

| 已锁定事实 | 二进制含义 | 对内核设计的影响 |
|---|---|---|
| `cnode_idx:u32` | 至多 2^32 个逻辑 slot 编号 | slot 空间不必连续；内核可划分 CNode、保留特殊索引 |
| `depth:u8` | 从当前 CNode 根起至多 256 层 | 撤销链长度有静态界，**但不能单靠它识别对象身份或兄弟关系** |
| `rights:u16`，低 3 位 R/W/G | 每 cap 携带授权标志 | 权限检查在**内核对象访问点统一执行**，而不是由服务策略散落决定 |
| **`gen:u8`** | **slot 复用代数**（slot generation 方案已定） | 承载「这个 cap 还活着吗」⇒ slot 复用 = UAF 且**静默越权** |
| **`Cap<T>` 的 `T` 不解析** | 当前所有 `Cap<T>` 实例等价 | 内核无法在类型系统层信任「这是 frame cap」 |

⚠️ **真正的异常是 `T` 不被解析** —— `Cap<T>` 的 inner **被解析但被忽略**：
`Cap` 在符号表里**只登记一次**，**第一个 `Cap<X>` 赢**（此后所有 `Cap<Y>` 解析到同一个符号）
⇒ `Cap<i32>` 与 `Cap<i64>` **是同一个类型**（2026-10-30 实测：可互相赋值；
对照组普通泛型 `P<i32>` → `P<i64>` 会报 `type mismatch in let`）。
且 inner **从不 resolve 也不校验** ⇒ `Cap<NotAType>` **零诊断**。
名义相等按 `elem` 区分的说法在当前实现下**不成立**。
⇒ wire 已具备对象身份，**语言层却还不能把对象身份对应到对象类型**。

### 2.2 `.jhyynb` —— 为 capability 启动而设计的格式

magic `JBE\x01`，header **120 B**（2026-10-31 按自然对齐重算订正，原写 112 B）。
⚠️ **binary-format v1.0.0 是设计稿，未实装**（abi §12.10）—— 下列结构是**目标格式**，不是当前产物。

| Section | kind | 表项大小 | 承载语义 |
|---|---:|---:|---|
| text / rodata / data / bss | 0–3 | — | 常规 |
| `cap_init` | 4 | 32 B | **拥有什么** |
| `ipc_dispatch` | 5 | 16 B | **接收什么** |
| `debug_group` | 6 | — | 调试信息（**可剥离**） |
| `region_table` | 7 | 24 B | **访问哪里** |
| **`contract`（建议新增）** | **9** | — | **执行时允许做什么** ← **目前缺的第四问** |

**cap_init 表项（32 B）**：

```
type_tag:u32 · cnode_idx_hint:u32 · rights:u16 · depth:u8 · _pad0:u8
name_idx:u32 · init_call_off:u32 · _pad1:u32
provenance_seed_off:u32 · _pad2:u32
```

`type_tag` 是 enum 不是 string（kernel 解析 O(1)）；
`cnode_idx_hint = 0xFFFFFFFF` 时 kernel 自由分配；
`init_call_off` 允许 per-Cap 初始化逻辑（jhyy 侧 `#[cap_constructor]` emit）。

⚠️ **cap_init 的 `rights:u16` 字段与 `Cap<T>` wire 的 `rights:u16` 字段是两个不同的字段，
但被设计成同源**（binary-format § 7「Cap Init Table」：「rights 直接对应 `Cap<T>` 8B 布局的 rights:u16 字段，
kernel 分配 cap 时直接 copy」）⇒ 详见 binary-format § 7「Cap Init Table」。

**IPC dispatch 表项（16 B）**：

```
msg_tag:u32 · handler_fn_off:u32 · cap_off_count:u16 · cap_off_table_off:u32
```

它引用 cap-offset 表的 wire 格式 `{n_caps:u16, _pad:u16, cap_offsets:[]u16}`；
**内核收到 IPC 后按 `cap_offsets` 原地改写 `cnode_idx` 以避免 deep-copy**。

> 原地改写是有价值的性能决定，但它也意味着 **message struct 与 cap_offsets 的布局错配
> 会变成静默内存破坏**。

**region_table 表项（24 B）**：region kind 0=anon_arena / 1=mmap / 2=raw_mmio /
3=unsafe_share / 4=cap_namespace / 5=kernel_shared；rights 含 R/W/X/share；
带 growable / cow / pinned / lazy_commit 等 flags。

这是一份「**区域声明**」，不是完整 VM 对象模型：不规定页粒度、颜色、cache policy、NUMA 节点、
映射计数、evict 顺序，也不携带 lifetime/borrow checker 数据。
binary-format 明确声明 **Region Table 不携带 borrow checker 数据**，
理由之一是「Kernel 不解决语言问题」。

### 2.3 ABI 的当前状态

四个目标 `amd64_win` / `amd64_win_freestanding` / `amd64_sysv` / `amd64_sysv_freestanding`
均已在自托管后端覆盖；`.jhyynb` 的 section 要求 4 KiB 对齐，与 x86-64 页尺寸天然一致。

⚠️ **但全 spill 策略只保存 RBP** ⇒ **自举编译器最大单函数帧 349232 B（≈341 KiB）**
（v4.2.1 之后实测；中位 288 B）。此前流传的「229 KiB」**已作废** ——
v4.2.1 把帧公式从写死的 `8192 + per_fn_alloc` 改成按函数实际需要算，
中位帧 8368 → 288 B、chkstk 调用 1045 → 46，**但最大帧反而变大**
（旧公式在公式池主导时把 `per_fn_alloc` 丢掉了）。

⇒ **内核栈模型不能按 C 风格的 8–16 KiB 默认值设计**：
341 KiB 已远超经典 8 KiB 栈，**未来最坏栈深度必须由编译器证明**，
而不能在 ABI 手册里继续作为 warning 存在。

---

## §3 CSpace、depth、撤销与 rights

### 3.1 `depth` 的语义

**`depth` 应是「当前 CNode 根到 slot 的层级数」，而不是对象生成次数。**
规范只记载 `depth:u8@4`，没有给出名称解析算法。结合 cap 派生，最自然的解释是：
深度为 0 表示直接挂在当前命名空间根的 slot；对 CNode cap 做 resolve 或 derive 时，新路径的层级增加。

⇒ 允许内核在常数界内证明一条解析链不超过 255 次续接，并使撤销遍历的栈或队列深度受 256 上限约束。

**8 位带来的工程约束**：深度不仅是能力证明，**更是动态资源界**。
任何 derive 操作若不加检查，深度溢出既可能造成祖先关系失效，也可能被利用绕过 slot 归属。

**深度与 rights 正交**：深度是「解析链长度」，rights 是「权限位」，两者不互相推导。

### 3.2 撤销树：语义真源是**对象反向边**，不是 CNode 索引树

**规范没有提供 CDT / CROB / 反向引用或 revoke 算法** ⇒ 必须区分事实与建议。

在 seL4 中，CSpace 由 CNode 组成，派生出的 cap 若与父 cap 指向同一内核对象，
撤销必须沿**派生关系**而非 CNode 索引树工作；**简单从 CNode 根 DFS 会漏掉跨 CNode 别名**。

JHYY 至少应引入四种对象关系：

| 关系 | 表达内容 | 撤销时是否必须遍历 |
|---|---|---|
| parent → child derive | 派生来源与深度 | 是，用于寻找后代 |
| **object → capability slot** | 一个对象可被哪些有效 cap 引用 | **是，用于判定是否真正无引用** |
| mapping → page table entry | 一个 frame 当前映射在哪些页表 | 若支持 revoke/quiesce，必须 |
| cap slot → CNode | 当前 slot 的容器与索引 | 是，用于定位表项 |

**单靠 `depth:u8` 只能证明「child 比 parent 更深」**，
**不能证明 child 仍指向同一对象，不能证明没有兄弟 cap，也不能证明映射仍然存在**。

⇒ **以对象反向边作为语义真源，CNode depth 只作为派生证明与遍历界。**
⇒ `derive` 必须在内核侧登记派生边，否则 revoke 不精确。

**撤销的同步性 —— 已定**：

| 决定 | 内容 |
|---|---|
| **默认同步** | 同步是 object capability 模型的核心承诺；异步则要求**每一个使用点**都处理「可能已撤销」⇒ 把并发问题推给所有用户 ⇒ 不可推理 |
| **分级例外** | 某些对象**物理上不可能同步**：`Mapping`（unmap 必须等所有 CPU 刷 TLB ⇒ 需 quiesce）、`Frame`（正在被 DMA ⇒ 等 DMA 完成）⇒ **哪些对象需要异步，是 P4a manifest 的逐类决定**，不是语言级规则 |
| **传播** | revoke 沿 CDT 传播（父撤销 ⇒ 全部后代失效）—— 这是 CDT 的定义，不是选择 |
| **两个不同的操作** | 撤销一个**派生引用**不影响它的兄弟；撤销**对象**时兄弟全失效 ⇒ 必须拆成两个系统调用：`retract_cap(cap)` / `revoke_object(cap)` |

⚠️ **撤销不阻塞 `Cap<T>` 的 T 落地** —— revoke 是**运行期**语义，`T` 的解析是**编译期**
语义 ⇒ 两者无依赖。**语言层：`Cap<T>` 的类型不因 revoke 改变** ⇒ revoke 不进类型系统。

### 3.3 rights 单调收缩由 derive 系统保证

规范的 R/W/G 只占 16 位中的 3 位，还有 13 位 padding 空间。建议在未来 16 位布局中显式定义：

- **derive 只能清位，不能置位**
- root 的 rights 是**对象类型允许集**的子集
- 派生 cap 的 rights 是父 rights 的子集
- 映射类操作可附加 VM rights，但**不能产生新 capability rights**

⇒ 这是**运行时不变量**，必须由 `cap_derive` 系统调用强制。
**语言层的编译期检查是加速带，不是替代品。**

**G 不应被允许由 R/W 派生得到**，除非内核显式执行「升级需要授权对象」的协议 ——
grant 是权限的放大器，允许 `RW → RWG` 则单调收缩形同虚设。

**revoke 位不进 `Cap<T>` wire —— 已定**（与 §3.6 的布局一并落地）：

| 理由 | 说明 |
|---|---|
| 两个正交维度被塞进了一个字段 | cap 的 rights 描述「**持有者能对这个对象做什么**」；revoke 描述「**持有者能对这个引用做什么**」⇒ 若同占 16 位，rights 类型从 8 种变 16 种，其中**一半是不可达组合** |
| 撤销的正确语义是 CDT 上的操作 | 一个 cap 被 revoke 后，它在**别的进程**的副本也失效吗？若 revoke 在 wire 上，每个副本各带一位 ⇒ **语义分裂** ⇒ CDT（对象反向边）是全局真源 ⇒ revoke 必须是 **CDT 上的操作** |
| 真正需要的额外位是 slot 版本 | 「这个引用还活着吗」的载体是 **slot generation**（§3.5），不是 cap 上的 revoke 位 |
| 先例 | seL4 的 revoke 是 CDT 上的操作（`CdtRevoke`）；cap 上没有 revoke 位 |

⇒ **rights 类型集合定为 8 种**（R/W/G 三位）。cap_init 表项的 `_pad0:u8` 若要表达
「该 cap 初始是否可撤销」，用**独立表项字段**，不进 cap wire。

### 3.4 软件能力的模型边界

**amd64 没有 CHERI，JHYY 不能把 `Cap<T>` 宣传为硬件不可伪造指针。**

| | 可靠的部分 | 不可靠的部分 |
|---|---|---|
| 软件 object capability | 内核对象存在且调用者拥有 slot | **用户态数据没有被解释成另一种类型或伪造 slot** |

slot 索引可以写入任意内存、被 memcpy、被序列化和反序列化；
没有 type/version/provenance 元数据，**无法区分合法 slot 和巧合整数**。

**软件能力能做到的是 object capability，不是 fat-pointer 空间能力**：
对象引用不可伪造、只能通过受控入口调用对象方法（seL4 的强项，也是 `.jhyynb` 的
cap_init/IPC 设计自然对应的模型）；空间能力则要求每次内存访问都携带边界与权限，
**没有 CHERI，普通指针解引用无法由硬件检查**。

⇒ 若 JHYY 未来有 `ptr<user>` / `ptr<kernel>` / `ptr<phys>`，
它们应被定义为「**经过类型/上下文证明的受限指针**」，而不是「硬件保证越界 fault」的能力。

**语言承诺的边界（必须写进规范）**：
JHYY 保证「**授权单调收缩 + 对象类型不匹配不可编译**」，
**不保证**「用户态不会主动泄露能力」。
软件 capability 保证的是「授权不会凭空增加」，不是「用户不会自愿放弃隔离」
—— compositor 把 full-framebuffer cap 交给应用，内核没有义务阻止。

> **把这条写进规范，就不会出现「长得像 Rust 却不提供 Rust 保证」的虚假安全感。**

### 3.5 CHERI 缺失对语言提出的四项要求

1. **CNode slot 必须版本化 —— 已定：`padding:u8` 改作 slot generation**
   （字段改名 `gen:u8`，**wire 长度不变、字段数不变 ⇒ ABI 不破坏**）

   | 方案 | 判定 |
   |---|---|
   | **`padding:u8` 改作 slot generation** | ✅ **已定** |
   | 内核维护 `(slot, generation) → alive` 表，cap 不带 generation | ❌ **不可能** —— cap 只有 slot 索引，内核无从知道这个 cap 是哪个 generation 派发的 |
   | 用 `provenance_seed` 哈希 | ❌ 同样需要 cap 带标识 |
   | 不做，slot 永不复用 | ⚠️ 简单，但 2^32 槽会耗尽；且等于**放弃**对一个已知 UAF 的防护 |

   语义：`gen` 是 **slot 复用代数**；slot 被复用时 +1；cap 派发时携带当时的代数。

   **必须写明的约束（容易踩坑）**：
   - generation **只在同一个 CNode 槽内有意义** ⇒ 跨 CNode 派生时，目标槽的 generation
     由**目标 CNode 的所有者**决定（内核分配），**不是继承**
     ⇒ 写错会让「跨 CNode 混淆」的防护**看起来存在实则无效**
   - 因此 `AddressSpace` / `Mapping` 若引入，**也要各自的 slot 空间与 generation 语义**
2. **`Cap<T>` 的 `T` 必须被解析** —— 硬件边界缺失时，**类型就是唯一廉价防线**
3. **rights 必须进入类型参数** —— 避免所有 cap 退化成 `Cap<i32>`
4. **provenance 必须成为语言与 ABI 的不变量** —— cap_init 的 `provenance_seed_off`
   已有种子字段，但规范没有说明如何 hash、绑定、派生或验证

**短期建议**：「软件 capability + 可选 CHERI 后端」，而不是等待 CHERI。
**不要承诺 CHERI 兼容 ABI，也不要用 CHERI 论文为当前软件能力模型背书。**

### 3.6 `Cap<T>` 的 wire 布局 —— 已定：**自然对齐**（`gen@5 / rights@6`）

```
cnode_idx:u32@0 · depth:u8@4 · gen:u8@5 · rights:u16@6
```

| 来源 | 原布局 | 性质 |
|---|---|---|
| lang-spec § 2.6 | `gen:u8@5 · rights:u16@6` | **锁定规范**（2026-10-24 锁，2026-10-31 改对齐） |
| abi § 2.5 | 同上（字段表逐字一致） | **锁定规范**（2026-10-24 锁，2026-10-31 改对齐） |
| binary-format § 2 | ~~`rights:u16@6`~~ | 设计稿（2026-09-04，未实装）⇒ **已按本布局修订**（2026-10-31） |

**判定证据、逐条推理与编译器侧动作 ⇒
[`JHYY_编译器侧设计终版.md` § 7.1](JHYY_编译器侧设计终版.md#71-cap-wire-布局的字节偏移--已收敛历史记录)。**
一句话：lang-spec § 2.6 自带的构造示例
`0x0003000200000007 as Cap // cnode=7, depth=2, gen=0, rights=R|W`
小端展开 = `07 00 00 00 | 02 | 00 | 03 00` ⇒ **只有 `rights@6` 下才自洽**。

**为什么是自然对齐**：`rights:u16` 落在**偶数**偏移 ⇒ 整个类型**无隐式 padding**、
**字段全部自然对齐、无隐式 padding** ⇒ 与「无 `packed` / 显式 `_pad`」的布局契约一致，编译器侧
「message struct 字段 size/align 一致」的编译期检查才**有东西可查**。
反之 `rights@5`（u16 在奇数偏移）**只能由 packed 产生**。

**为什么现在定不亏**：`Cap<T>` 的 `T` 不解析、无字段访问 ⇒ 没有任何代码按字节拆 cap
⇒ **现在改零成本**；等 `Cap<T>` 真 T 落地后再改就是 ABI break。
（另外 `.jhyynb` 本身是**设计稿未实装** ⇒ 旧布局没有任何产物实现过，兼容成本为零。）

⚠️ **这次冲突能活三个月，就是因为没有一道门** ⇒ 已加
`scripts/dev/check_spec_consistency.py`（比对三处的 Cap 布局 + rights 位宽），接进 CI。

---

## §4 对象模型与 type_tag

### 4.1 11 个 type_tag（仅 binary-format 记载）

```
0=endpoint  1=page  2=framebuffer  3=console  4=file  5=shm
6=compositor  7=surface  8=seat  9=buffer  10=endpoint_focus
11-65535 = OS-specific · 65536+ = user-defined
```

**type_tag 不是设备枚举，而是能力对象分类**：
endpoint / file / shm 偏 IPC 与数据；page / framebuffer / compositor / surface / seat / buffer 偏图形与地址空间；
console 是传统输出对象；endpoint_focus 是焦点授权。

⇒ 内核至少要认识**两类 region/page 对象与四类图形对象**，而不是把所有图形资源压成「一块显存」。
这优于把 drm/gpu 抽象泄漏进语言，也与「Kernel 不解决语言问题」相容：
**内核解决对象存在、授权、映射与生命周期，窗口管理器解决布局与策略。**

### 4.2 ⚠️ type_tag 表缺两个对象（推导链必需）

`map_into` 的签名需要 `Cap<AddressSpace, W>` 与返回 `Cap<Mapping, R>` ——
**但 type_tag 表里既没有 address_space 也没有 mapping。**

⇒ **已定**：
- 缺失的两个 type_tag（`AddressSpace` / `Mapping`）**登记为 P4a(OS-13) manifest 的输入**，
  **不在此刻临时加**
- **P4a 的 manifest 必须先答「哪些对象类型存在」**，否则 P4b 写签名时会再次缺类型
- ⚠️ 这部分依赖内核的地址空间模型，而**那部分 OS 文档已被删**（2026-10-30）⇒ **需重新确认**

### 4.3 `Page` 与 `Frame`：统一为 `Frame`

**规范词汇表里只有 `page`** —— 「Frame」这个词是 OS 报告自造的。

**已定：type_tag=1 的名字从 `page` 改为 `Frame`（语义：物理页框），`Page` 不存在。**

理由：
1. **`page` 在 OS/硬件语境里几乎总是「虚拟页」**，而这里要表达的是**物理页框**
   ⇒ 用 `page` 会持续引起歧义（页表映射单元 vs 物理页框）
2. **虚拟页根本不需要 cap** —— 它是地址空间的一个区域，由 `region_table` 声明
   ⇒ **cap 授权的对象是物理页框，不是虚拟页** ⇒ 二者不该并列为两个 type_tag
3. **type_tag 是数值，名字只是注释** ⇒ 改名字**零成本、零 ABI 影响**

### 4.4 GUI：对象骨架已具备，完整桌面尚未被规范定义

**compositor / surface / seat / buffer 足以构建双缓冲显示管线，但不足以构成桌面。**
规范没有定义：像素格式、平面/stride、modifier、损伤区域、原子提交、presentation feedback、
VSync、hotplug、input 事件队列、scancode 映射、DPI、拖放、截图授权。

**`framebuffer=2` 与 `buffer=9` 需要明确区分**：前者更像连续显存区域，
后者更像可共享、可变格式的图形缓冲区。若两者最终语义相同应合并；若不同，
应在 type_tag 之外补充对象专属数据结构。

| 桌面能力 | 规范是否已记载 | 建议对象或能力 | 若不实现的直接后果 |
|---|---|---|---|
| 应用绘制到离屏 buffer | 有 buffer/surface 线索 | buffer cap + surface attach | 无法区分图形资源与普通共享内存 |
| 双缓冲/提交 | 有 compositor/surface 线索 | transaction endpoint | 撕裂、跨客户端状态不一致 |
| 输入分发 | 有 seat | seat ep + focus cap | 任何 client 可读取全局输入 |
| 焦点切换 | 有 endpoint_focus=10 | focus token 与 lease | 无法可靠防止后台录屏或按键监听 |
| 多显示器/hotplug | 未记载 | display lease cap | compositor 与驱动强耦合 |
| 像素格式/modifier | 未记载 | 对象专属格式字段 | 应用可凭 framebuffer 误解释显存 |

**焦点应以 capability 授权，而不是以「前台窗口 id」授权**：
seat 的键盘事件只应流向当前持有有效 focus cap 的 surface endpoint；
切换焦点由 compositor 通过**原子 derive/swap** 完成。
focus cap 应可撤销、可绑定到 surface 生命周期，并区分键盘、指针、触摸和全局快捷键。

⚠️ 这些规范未记载项会阻塞 GUI 接口冻结：
**M3 ABI 使用 MS x64 函数指针与 `#[naked]` interrupt**，但规范没有给出
keyboard/mouse 事件的 message struct、focus revoke race、surface destruction 与 in-flight frame 的关系。

---

## §5 `.jhyynb` 契约格式

### 5.1 三张表必须补的字段

| 表 | 当前适合表达 | 必须补充，否则无法静态验证 |
|---|---|---|
| `cap_init` | 对象类别、初始 rights/depth、init call、provenance seed | **目标 CNode、parent cap、init 阶段、生命周期 owner、quiesce callback offset、是否允许进一步 derive** |
| `ipc_dispatch` | msg_tag、handler offset、cap offset 表 | **cap slot 位图、type/rights allowlist、handler 版本** |
| `region_table` | 区域类别、地址、长度、R/W/X/share、增长/复制/pin/lazy | **cache/ordering、page size policy、owner、生命周期、WCET 属性** |
| `contract`（建议） | 栈、sleep、中断、锁、分配、panic | **编译器输出是否可信、是否签名、是否可被 loader 忽略** |

**`name_idx` 不是类型** —— 适合诊断，不适合安全决策。
安全决策必须用 type_tag、rights、目标 CNode 与对象身份。
只提供 `cnode_idx_hint` ⇒ 加载器无法区分「建议放哪」与「必须放哪」，也无法证明没有 slot 冲突。

**region_table 应成为「由谁管理」的元数据，而不是页表格式**：
六种 kind 的 owner 语义完全不同（raw_mmio 的 pinned/lazy_commit 很可能不适用；
kernel_shared 不应允许普通 user process 任意 unmap；cap_namespace 不应参与 cow）。
⇒ 内核应根据 kind 的**白名单**解释 flags，而不是让 flags 成为通用位图。
4 KiB 对齐适合直接 mmap section data，却不应被误解为所有 region 必须按 4 KiB 粒度管理。

### 5.2 contract section（kind=9）

**为什么不能用 "debug" 命名承载安全契约**：否则语义等级会被下游误解 ——
**旧 loader 会把能力栈预算当可选调试信息忽略**。

```
kind = 9  contract    loader 必须验证，验证失败拒绝加载
kind = 6  debug_group 可选，可剥离
```

**承载内容**（编译器侧 § 4.5 的 8 个子节，这里是 OS 视角的合并视图）：
栈上界（`frame_local_max` / `call_path_max`）、`may_sleep`/`irq_ctx`/`preempt_disabled`/`may_alloc`、
`holds(L)` 锁序图、IPC handler version、panic category、WCET class、
cap_offsets 位图与 type_tag allowlist。

**必须带 version、producer ID、source hash、compatibility policy。**

### 5.3 版本化与禁止隐式默认值

- **表项必须版本化** —— loader 必须理解最低版本与 cap wire 扩展，不能交给服务进程
- **禁止隐式默认值** —— 未记载的字段不能靠 loader 猜
- **未知 section kind 的处理策略必须显式** —— loader 可以拒绝未知 kind，
  但**不能把新 section 当垃圾数据**
- 若 cap_init 需要表达「该 cap 初始是否可撤销」⇒ 用**独立的表项字段**
  （32 B 表项里 `_pad0:u8` 有 1 字节可用），**不要挤进 rights**

---

## §6 语言—内核边界

### 6.1 分工公式

> **编译器证明 shape，内核强制执行 authority。**

正确的分工不是「编译器懂 OS，或内核懂 Rust/JHYY」，而是**两者共享一份可机器检查契约**。
编译器输入源码与 `cap_init`/`ipc_dispatch`/`region_table` 声明，输出 `.jhyynb`；
内核只信任该文件的格式、cap slot 与对象。

**「Kernel 不解决语言问题」原则成立，但「语言问题」必须被严格定义**：
内核**不**实现类型推导、trait 解析、借用区域、闭包捕获、泛型单态化、integer promotion 或源码诊断 ——
这些是编译器的责任。
内核**必须**负责对象存在性、capability authority、页表、TLB、调度、中断、并发原语、
设备状态与全局资源仲裁。

**边界两侧各有一个反例**：
- 若编译器让「持有 `&mut Frame`」直接操作物理页 ⇒ **越过边界**
- 若内核只验证 cap 的 cnode_idx/rights，却拒绝暴露对象类型
  ⇒ **迫使每个服务用整数和 magic number 重建类型系统**

### 6.2 四种必须破例的情况

| # | 情况 | 内核必须做什么 |
|---|---|---|
| 1 | **内存安全依赖全局内核状态**（页表、RCU grace period、PerCpu 偏移、中断屏蔽、锁） | 输出稳定 unsafe primitive，语言只检查 token 持有；**编译器不能凭源码单线程推断「当前 CPU 的 PerCpu 引用是否仍然有效」** |
| 2 | **错误语义必须由内核恢复**（oops / double fault / page fault / cap fault / IPC timeout） | 语言可给 `#[panic_handler]` 与分类，但**线程 terminate / namespace revoke 由内核决定** |
| 3 | **wire format 跨版本** | loader 必须理解最低版本与 cap wire 扩展，**不能交给服务进程** |
| 4 | **证明本身会改变系统状态** | 运行期检查点是安全状态机的组成部分，**不是语言失败**；反过来，运行期不应重新发明语言已证明的 message 布局 |

### 6.3 第 5 原则的改写

> **「内核不实现语言，但为语言提供可证明使用的运行时契约」。**

（原「5 原则」全文见
[`docs/abis/jhyy-binary-format-v1.0.0.md` § 2](../abis/jhyy-binary-format-v1.0.0.md#2-约束从已锁-d-locks-推导)
的「5 原则」一条 —— 那批 OS 侧原设计文档已于 2026-10-30 删除，原则原文留在 binary-format 里。）

这条边界既避免内核承担类型推导，也避免语言把全局硬件状态假装成纯函数。

---

## §7 能力类型化设计（`Cap<T, Rights>`）

> 完整设计见编译器侧文档 § 5.1；此处是 OS 视角的约束与后果。

### 7.1 rights 的 8 个内置类型

R/W/G 三位 ⇒ 2³ = 8 种，**全量内置，不需要任何代数机制**：

```
None · R · W · G · RW · RG · WG · RWG
```

**为什么不用 const generic 位集 / 依赖类型**：
const generic 与名义类型系统冲突（常量不是声明名）且单态化上界 2^16 失控；
依赖类型（`where new_rights <= src.rights`，`new_rights` 是运行时值）
在 JHYY 当前架构下**不可实现** —— 没有 trait、没有 const 泛型、没有任何约束表达机制。

**唯一失去的能力**：无法表达「运行时决定的 rights」⇒ 由 `derive_dynamic` 显式兜底。

### 7.2 派生 API 与四条规则 —— OS 侧的约束与后果

**API 与 R1–R4 规则的权威定义在
[`JHYY_编译器侧设计终版.md` § 5.1](JHYY_编译器侧设计终版.md#51-capt-rights--编译器侧实现要点)
（`derive` / `derive_dynamic` / `narrow` 三个入口 + 四条规则）。**
OS 侧只补充**内核必须强制什么**：

| OS 侧后果 | 说明 |
|---|---|
| **`cap_derive` 系统调用是唯一权威** | 编译期检查是**加速带**，不是替代品 —— 攻击者可以伪造用户态 syscall 参数 |
| **R2 的「对象类型允许集」由 manifest 提供** | 内核侧维护 `allowed_mask(type_tag)`；编译期靠它做常量判定 |
| **R4 的「升级需要授权对象」是内核协议** | 编译期只能判「G 不能由 R/W 派生」，**「谁有权授权」是内核的事** |
| **`narrow` 的子集检查要在内核再查一次** | 用户态那一次是加速带 |

### 7.3 `ptr<phys>` 从 `Cap<Frame>` 派生 ⭐

**这是 JHYY 相对 Rust 最值得固化的结构优势**：
Rust 中 `PhysAddr` 通常只是一个整数，或 `NonNull`/`*mut` 加上文档约定；
JHYY 已有 capability 底座，可以让物理指针**天然带授权溯源**。

```jhyy
fn frame_phys(c: &Cap<Frame, R>)     -> ptr<phys, R>
fn frame_phys_mut(c: &Cap<Frame, RW>) -> ptr<phys, RW>

// 映射：返回新的 mapping cap，而不是 bool
fn map_into<'f, R>(
    space: &mut Cap<AddressSpace, W>,
    frame: &Cap<Frame, R>,
    at: ptr<kernel>,
) -> Cap<Mapping, R>          // rights ⊆ frame.rights（编译期常量判定）
```

**`ptr<phys>` 的构造必须只有三类可信来源**：
① `Cap<Frame>` 的借用映射；② `Cap<Framebuffer>` 显式适配；
③ loader 验证过的 `region_table` raw_mmio 条目。

**映射是否消耗源 cap —— 已定：不消耗，派生新 cap，原 cap 保留。**

| 理由 | 说明 |
|---|---|
| capability 模型的核心是「可并存的授权」 | 映射一个 frame 不应该让 frame 消失 ⇒ 用户可能想 map 两次（不同 vaddr），或 map 后仍持有 frame 用于 `unmap` |
| 消耗（by value）会让心智模型冲突 | 「map → unmap → 再 map」很别扭，且与「cap 是引用」冲突 |
| 借用检查器会咬人 | `&Cap<Frame, R>` 会让长生命周期的 mapping 借用短生命周期的 cap ⇒ 而 JHYY 的借用检查还在 W-105 最小版 |
| **「转移所有权」不需要语言级特例** | 用户想转移就自己 `derive` 后 `drop` 原件 |

⇒ **映射的 rights ⊆ frame 的 rights**（编译期常量判定）。
**unmap 是否等待** ⇒ 归 §3.2 的分级：`Mapping` 标 `async_revoke: true`
（unmap 必须等所有映射消失，否则还有 CPU 在用那个物理页）。

**能力边界（必须写进规范）**：

| 能防住 | 防不住 |
|---|---|
| 凭空造物理地址（`0x1000 as ptr<phys>` 编译失败） | 用户态把 8 字节 slot **复制**给另一个进程（object capability 的固有边界） |
| 用 endpoint cap 去访问物理内存 | slot 释放后被复用，旧 cap 指向新对象（**需要 slot version**） |
| 只读 frame 派生出可写 phys（rights 跟随） | 内核本身的 bug（capability 模型不保护内核） |

### 7.4 `ptr<io>` 必须与 `ptr<phys>` 分开

| 类型 | 语义 | 默认行为 |
|---|---|---|
| `ptr<phys, R>` | 普通 RAM 物理地址 | 可缓存 |
| `ptr<io, R>` | MMIO 设备寄存器 | **默认 volatile**、不合并访问、**禁止推测读** |

推测读对 device register 是致命的 —— 读一次可能就有副作用。
⚠️ **这条承诺在后端给得起之前不能落地**（编译器侧 §3.3 接口 A：
当前 `emit_volatile` 只发注释，没有任何拒绝机制）。

---

## §8 IPC 契约

### 8.1 `msg_tag` 唯一性必须在单个 `.jhyynb` 内静态证明

若两个 handler 声明相同 tag，loader 无法稳定选择目标；
若允许重载，则 wire tag 不再是完整 dispatch key。
⇒ 编译器检查同 binary 中 tag 不冲突，或明确定义「service interface version + tag」的复合 key。

**跨版本兼容不能靠允许冲突实现**，而应由 IPC version capability 和协商协议实现。

### 8.2 handler 签名必须与 message struct 双向一致

对 trusted binary，编译器可以从 `#[ipc_handler(fn(msg: &Msg) -> Reply)]`
**反向生成** IPC dispatch 表，而不是让开发者手写 `msg_tag`、函数 offset 与 cap_offsets。

对 C/汇编或外部 ABI，可允许显式声明，但必须生成可导出的 contract JSON/section 并做双向校验。

⚠️ 由于 ABI 目前 **sret 无条件生效**、`alignof(enum)` 硬编码 4、
且 SysV 分类器有隐患 ⇒ **message struct 的 ABI 规则必须成为 IPC contract 的一部分**。

### 8.3 `cap_offsets` 校验至少分四层

1. **编译器**确认每个 `cap_offsets[i]` 位于 message struct 中一个完整 `Cap<T>` 槽
2. **编译器**生成 cap slot 位图，证明无重叠、无越界
3. **发送端**在可信编译前提下维护 wire 布局
4. **内核**因消息来自不可信进程，必须重新检查 offset、slot 存在性、rights 与 type_tag allowlist

⇒ **「编译器保证 layout」不能替代「内核检查 offset」。**
真正可避免的是 trusted sender 的 handler 参数和 IPC stub 之间的不一致，
而不是跨信任边界的验证成本。

编译器应为每条 handler 生成 `cap_offset_bitmap + type_tag_allowlist + rights_lower_bound`。

### 8.4 cap 的移动语义 —— 已定

**IPC 里的 cap 是移动（transfer），不是复制**：
复制 ⇒ 一个 cap 两个持有者 ⇒ **revoke 语义立刻崩**（撤销谁？）
⇒ 与 CDT 的对象身份模型冲突。
而 kernel 的「原地改写 `cnode_idx`」本身就是**移动**的实现
（把 sender 的 slot 索引改成 receiver 的 slot 索引 ⇒ sender 的那个 slot 被清空）。

⇒ **发送即撤销 sender slot**；消息在 flight 期间持有的 cap 由 **kernel 托管**
（receiver 侧的临时 slot 引用），receiver 读走或丢弃才算最终转移。
⇒ **语言层后果：`send_cap` 按值消耗 cap** ⇒ 编译期保证 sender 之后不能再用。

**第一版不做借用/共享 cap**（`borrow_cap`）—— 需要「可共享引用」概念，第一版没有。
**第一版不做 timeout** —— seL4 用 notification + timeout，而 timeout 后 cap 归谁是经典的「泄漏」难题
⇒ 第一版同步阻塞 IPC **不带 timeout** ⇒ **不会产生泄漏** ⇒ 登记进 ABI §12 已知偏离。

> **三个子问题分别定**（不再有「待定」）：
> **grant / return ⇒ 移动（transfer）**；**in-flight 消息所有权 ⇒ 发送即撤销 sender slot**，
> flight 期间由 kernel 托管；**timeout ⇒ 第一版不做**。

---

## §9 启动态、栈与故障降级

### 9.1 BootState 线性 typestate

**启动态应把不可逆启动步骤变成线性类型推进**：

```
NoAlloc → HeapReady · PagingOff → PagingOn
CpuLocalOff → CpuLocalReady · InterruptsOff → ThreadingReady
```

每一步要求前一状态被**消费**或显式证明：
`kernel_alloc()` 要求 `HeapReady`，`map_kernel()` 要求 `PagingOn`，`schedule()` 要求线程系统就绪。

⇒ 可以先用**封闭状态 enum + 一组 unsafe 构造函数**实现，不需要完整 trait。

### 9.2 中断与锁效果不能依赖文档约定

至少需要四个效果：

| 效果 | 语义 |
|---|---|
| `irq_ctx` | 当前代码是否处于中断上下文 |
| `preempt_disabled` | 是否能 reschedule |
| `holds(L)` | 持有哪些锁 |
| `may_sleep` | 是否允许 blocking |

**必须覆盖的高频误用**：
`sleep` 在 `irq_ctx` 或 `preempt_disabled` 中禁止；
`spin_lock` 在已持有不兼容锁序时禁止；
`alloc` 在 PF/allocator 路径中禁止。

若语言无法表达，**应在 `#[naked]`/interrupt 函数接口中至少要求显式 `unsafe` capability 参数**。

### 9.3 栈预算：汇编作者必须手工申报

**341 KiB 最坏帧已现实存在**，而规范规定栈槽只保证 8 字节对齐、没有 16 字节保证
⇒ 这会同时影响 SIMD 参数、IPC stub、汇编接口和内核 trap frame。

⇒ 每个函数输出 `max_frame`、`max_call_depth` 与 `requires_alignment`；
每个线程创建点校验 `stack_reservation >= frame_of_callers + redzone`。

⚠️ **对于 `#[naked]`、`asm!` 和 interrupt entry，汇编作者必须手工给出栈预算，
编译器不得把它们视为零。** 否则 ABI 可以编译通过，
却在内核递归 IPC、页错误路径或中断嵌套时破坏相邻栈。

**内核栈策略 —— 已定**：

| # | 决定 | 内容 |
|---|---|---|
| 1 | **栈大小不是编译器定的，是 loader / 内核定的** | 编译器的作用是**把最坏情况算出来并让链接期断言** ⇒ 「内核栈策略」主要是内核侧的，编译器侧只提供事实 |
| 2 | **P2 的硬门改成可判定形式** | **硬门**：自举编译器自身（**1045 个真实函数**）的 `call_path_max × frame ≤ 64 KiB`。**长期目标**：`max_frame ≤ 16 KiB` —— **保留但标注「可达性未证」** |
| 3 | **中断栈** | 独立于线程栈，**固定 4 KiB**；`#[naked]` interrupt handler 自报预算 |
| 4 | **per-CPU 备份栈** | **不在栈策略里解决** ⇒ 归效果系统（`preempt_disabled` 语义 + per-CPU 双缓冲） |
| 5 | **递归深度** | 递归函数**默认不允许进入内核栈路径**（链接期拒绝），必须显式 `#[trusted(recursive, max_depth=N)]` 声明上界 |

> **硬门为什么用 64 KiB**：自举编译器是本仓最坏情况（1045 个真实函数；
> `main.jhyy` 的 max temp id 已达 **6 万量级**，见台账 W-120）。
> 它的最坏调用路径若能在 64 KiB 内跑完 ⇒ 内核栈若跑得动自举编译器，就跑得动绝大多数内核代码。
> ⚠️ 这是**类比，不是证明** ⇒ **OS-4 的验收门数字应据此复核**。

### 9.4 无栈展开不是「没有错误处理」，而是必须定义错误终止面

规范当前无 GC、无栈展开、无 panic。内核至少区分三类事件：

1. 普通错误 → 通过返回值传播
2. 可恢复 fault → 投递到 capability endpoint
3. 不可恢复 fault → 触发当前线程终止 / namespace revoke / kernel oops

**必须明确「oops 之后能否继续运行」**：
若继续运行，哪些全局状态需要 quiesce；若不能，哪些子系统可以独立重启。
**没有这一层，无 panic 会退化为无限循环、双重 fault 或静默内存破坏。**

---

## §10 OS 对语言的需求清单（按失效严重性排序）

> 排序依据：**缺失后能否形成静默越权或无法启动**。
> 「后果」采用可证伪标准：若没有该能力，能否在编译期被触发、
> 是否只能依赖代码评审、是否会扩大 TCB。
> 规范状态依据三份规范；「无」不表示未来不能实现，只表示当前**摘录未记载**。

| 排序 | 需求 | 内核为何需要 | 不实现的后果 | 规范当前状态 | 阶段 | 编译器侧落点 |
|---:|---|---|---|---|---|---|
| 1 | `Cap<T>` 的 T 真实解析 | T 决定对象操作集；type_tag 必须与语言类型一致 | `Cap<i32>`=`Cap<i64>`，frame/endpoint/file 被混用，内核边界退回整数 | T 硬编码 i32 | 编译期 + 运行期 | OS-14 |
| 2 | `Cap<T, Rights>` 参数化 rights | R/W/G 是 16 位 wire 的一部分 | 只读对象可误传给 mut API；权限错误延后到运行时 | 仅存在 R/W/G bit | 编译期 | OS-14 |
| 3 | rights 派生单调收缩 | capability 模型必须禁止权限升级 | 派生子 cap 可绕过授权；CDL 无法表达 | 未记载 CDL 规则 | 编译期证明 + 运行期强制 | OS-14 |
| 4 | `ptr<user>`/`ptr<kernel>`/`ptr<phys>`/`ptr<io>` | trap/access 语义、cache/ordering 与可解引用上下文不同 | 用户指针在内核任意解引用；物理 I/O 与普通 RAM 混用 | 地址空间类型不存在 | 编译期 | OS-12 / OS-14 |
| 5 | `ptr<phys>` 从 `Cap<Frame>` 派生 | frame cap 才是物理页的授权真源 | 物理地址可绕过 cap；DMA/显存缺少审计 | 有 frame/page/framebuffer tag，无派生规则 | 编译期 | OS-14 |
| 6 | `#[ipc_handler]` 全契约检查 | 内核原地改写 cap_offsets | handler 与 message struct 错配会破坏 CNode | 仅有属性名 | 编译期 | OS-14 |
| 7 | capability 生命周期/销毁安全 | 撤销对象、CNode 与映射需要无悬挂 cap | slot reuse 导致 UAF；revoke 无法定位后代 | 未记载撤销结构 | 编译期 + 运行期 | OS-13 |
| 8 | 栈深度编译期断言 | 341 KiB 最大帧已是现实风险 | 内核递归、中断或 IPC 破坏栈 | 仅通过链接器补偿 | 编译期 | OS-2 / OS-4 |
| 9 | `may_sleep`/`irq_ctx`/`preempt_disabled` 效果 | sleep、调度与中断返回由内核控制 | 持锁 sleep、中断中非法 sleep | 效果系统不存在 | 编译期 | OS-7 / OS-12 |
| 10 | `holds(L)`/`may_alloc` | 锁序与内存分配会影响 deadlock/reclaim | 分配器递归持锁；PF 路径 OOM | 无锁序/分配效果 | 编译期分析 | OS-12 |
| 11 | RCU/PerCpu 语言原语 | 读侧必须关联 grace period 与 CPU 上下文 | 延后释放被提前回收；PerCpu 指针跨 context 失效 | 原语不存在 | 运行期 + 编译期 token | **OS-15（P4c）** |
| 12 | 侵入式容器与 pin 保证 | 内核对象常驻链表/队列，不能移动 | 容器指针悬空；list_head 需重复 unsafe 包装 | 无 list_head/trait/移动模型 | 编译期 | **OS-15（P4c）** |
| 13 | BootState 线性 typestate | paging/heap/alloc/interrupt 有严格顺序 | 未映射页表时使用 global alloc，或未初始化 CPU 时开中断 | 无启动状态系统 | 编译期 | OS-6 / OS-14 |
| 14 | `#[naked]` 与 interrupt 栈契约 | GUI 接口使用 `#[naked]` interrupt | 入口使用错误栈、Callee-saved 或 redzone | 有 `#[naked]`，规则不足 | 编译期契约 | OS-14 |
| 15 | wire 结构稳定 repr 与布局测试 | Debug ABI 布局契约禁止 packed，要求自然对齐 + 显式 `_pad` | section 解析发生 padding 相关 UB | 已锁定 | 编译期布局测试 | OS-5 / OS-16 |
| 16 | `cap_offsets` bitmap/handler 签名元数据 | 防止 IPC stub 把普通字节当 cap | 内核按错误 offset 改写 CNode | 仅有 offsets 数组 | 编译期输出 + 运行期检查 | OS-14 |
| 17 | region 边界与生命周期 metadata | region_table 只有 base/size/flags | 越界映射或共享对象过早释放 | 部分存在 | 编译期/运行期 | OS-13 |
| 18 | panic/oops/继续可达性分析 | 内核无 panic、无 unwind | 无法区分可恢复错误与内核 fault | 未定义 | 编译期 + 运行期 | OS-16 |
| 19 | lock-order/IRQ-safe 全程序分析 | 锁是可组合内核惯用法 | 组合两个子系统即产生死锁 | 无 | 编译期分析 | OS-12 |
| 20 | WCET/时间预算元数据 | GUI、驱动与中断有响应要求 | 无上界可验证实时路径 | 无 | 编译期元数据 | OS-16 |
| 21 | provenance/version 语义 | amd64 无 CHERI，软件 slot 可伪造 | slot reuse 与跨进程误解释 | 仅有 padding/seed 线索 | 运行期 + 编译期 | OS-13 / OS-14 |
| 22 | `asm!` 的寄存器/栈/clobber 契约 | ABI 全 spill 且栈槽仅 8 字节对齐 | 汇编破坏 ABI 假设却无法静态发现 | 有 `asm!`，语义不足 | 编译期 | OS-6 / OS-14 |

**前四项优先级高到足以阻塞任何 GUI 或用户服务原型**：
若 `T` 与 rights 不进类型，cap_init 的对象无法映射到类型系统；
若 `ptr<phys>` 不从 `Cap<Frame>` 派生，region_table 的 raw_mmio 与 framebuffer 也不能形成授权链；
若 handler 契约不检查，IPC dispatch 的原地 cap 改写会直接破坏 CSpace。
**这四项缺失时，即使 kernel.efi 能启动，也无法证明 user-space 不是靠巧合工作。**

**第 8 项栈深度与第 14 项 interrupt 契约是 ABI 正确性的前提**：
若暂时无法全程序分析，**至少要先禁止递归、动态调用与巨型栈帧进入 `#[naked]`/interrupt path**。

---

## §11 OS 侧分期与版本轴

每格落在哪个版本，见 [`docs/plans/v4/README.md`](../plans/v4/README.md) 的版本系列索引；
该格的详细 scope 在对应的 `v4.X.Y-plan.md` 里。

| 版本 | 序号 | OS 侧拿到的东西 | OS 侧要交付的东西 | 验收门 | 系列文档 |
|---|---|---|---|---|---|
| **v4.6** | OS-1 | 实参类型/个数检查 + 整数上下文转换 | —— | src0 自身零实参不符（**先统计后改码**） | [`docs/plans/v4/v4.6-plan.md`](../plans/v4/v4.6-plan.md) |
| **v4.7** | OS-2 | per-function `frame_local_max` + `call_path_max` + 链接期栈断言 | **线程栈大小策略**（loader 侧选，编译器只提供事实） | 链接期拒绝超栈对象 | [`docs/plans/v4/v4.7-plan.md`](../plans/v4/v4.7-plan.md) |
| **v4.8** | OS-3 | UEFI entry 钩子 + 按 `--target` 分支链接 + 最小 `kernel.efi` | **UEFI 契约**：entry 符号、console protocol、停机语义 | 最小镜像在 QEMU/OVMF 输出 UTF-8 后停机 | [`docs/plans/v4/v4.8-plan.md`](../plans/v4/v4.8-plan.md) |
| **v4.8.5** | OS-4 | 栈槽 16B 对齐 + 全程序栈分析 + 禁 XMM/red zone | **中断栈 4 KiB** + `#[naked]` handler 自报预算 | max_frame ≤ 16 KiB（**按 341 KiB 基线重算**）；XMM 溢出点 = 0 | [`docs/plans/v4/v4.8.5-plan.md`](../plans/v4/v4.8.5-plan.md) |
| **v4.9** | OS-5 | ABI §12 的 14 条偏离收敛 + 容器格式由 target 决定 | —— | 偏离 ≤ 3 且均为显式兼容性例外 | [`docs/plans/v4/v4.9-plan.md`](../plans/v4/v4.9-plan.md) |
| **v4.10** | OS-6 | 块表达式 + `fn` 类型位置 + 闭包捕获 + 结构化内联汇编 | —— | boot state 迁移可在块内完成；函数指针可跨模块传递 | [`docs/plans/v4/v4.10-plan.md`](../plans/v4/v4.10-plan.md) |
| **v4.10.5** | OS-7 | 效果最小集（`irq_ctx` + `may_sleep`） | —— | `irq_ctx` 内调 `sleep()` / `alloc()` 编译失败 | [`docs/plans/v4/v4.10.5-plan.md`](../plans/v4/v4.10.5-plan.md) |
| **v4.11** | OS-8 | 完整 lifetime + Polonius | —— | 3+ lifetime 用例 PASS | [`docs/plans/v4/v4.11-plan.md`](../plans/v4/v4.11-plan.md) |
| **v4.12** | OS-9 | trait + vtable + `dyn Trait` | —— | 3+ trait/dyn 用例 PASS | [`docs/plans/v4/v4.12-plan.md`](../plans/v4/v4.12-plan.md) |
| **v4.12.3** | OS-10 | const generic | —— | 3+ const generic 用例 PASS | [`docs/plans/v4/v4.12.3-plan.md`](../plans/v4/v4.12.3-plan.md) |
| **v4.12.5** | OS-11 | 一阶 HKT | —— | 3+ HKT 用例 PASS | [`docs/plans/v4/v4.12.5-plan.md`](../plans/v4/v4.12.5-plan.md) |
| **v4.13** | OS-12 | 完整效果格 + `holds(L)` 锁序图 + `ptr<user>`/`ptr<kernel>` | **per-CPU 备份栈**（从栈策略划出，归效果系统） | 无反向锁边；误用给出确定错误码 | [`docs/plans/v4/v4.13-plan.md`](../plans/v4/v4.13-plan.md) |
| **v4.13.5** | OS-13 | **capability objects manifest**（本仓交付） | **哪些对象类型存在** + 每类的 rights 初集 / owner / init phase / **revoke 同步性** | 每个 type_tag 逐个有 owner 与 rights 初集；revoke 语义写明；slot version 方案定 | [`docs/plans/v4/v4.13.5-plan.md`](../plans/v4/v4.13.5-plan.md) |
| **v4.14** | OS-14 | `Cap<T>` 真 T + rights 参数化 + `ptr<phys>` 派生 + `#[ipc_handler]` + contract section + `.jhyynb` 实装 | **`.jhyynb` loader 实现**（验证 contract，验证失败拒绝加载） | `Cap<i32>` ≠ `Cap<i64>`；整数不能 `as ptr<phys>`；IPC tag/layout/slot 全检查；contract 被 loader 校验 | [`docs/plans/v4/v4.14-plan.md`](../plans/v4/v4.14-plan.md) |
| **v4.14.5** | OS-15 | `Rcu<T>` / `PerCpu<T>` / 侵入式容器 | **grace period 语义 + `gs:` 段布局** | 一个内核链表 + RCU 读侧能用 JHYY 自然表达，无需 unsafe | [`docs/plans/v4/v4.14.5-plan.md`](../plans/v4/v4.14.5-plan.md) |
| **v4.15** | OS-16 | KASAN / KMSAN / KCFI / shadow stack / WCET class / panic 分类 | **shadow region 布局 + fault 分类表** | 插桩前后语义一致；≥20 个注入 bug 被捕获 | [`docs/plans/v4/v4.15-plan.md`](../plans/v4/v4.15-plan.md) |

**不排进 OS 线的**（与 OS 线正交，v4.16 起独立）：
async/await · 包管理器 · 并发 cap + 完整 memory model · 多架构 ABI。


---

## §12 最小实现顺序

**第一阶段 —— 只做「可信加载器能看懂、内核能强制执行」的最小格式。**
先冻结 `.jhyynb` 的 cap_init / region_table / IPC dispatch 静态表，
为 `Cap<T>` 增加真实 T，为 rights 增加编译期参数。
即便能力对象只有 endpoint、frame、address space 与 mapping 四类，
也应足以验证 boot、loader、最小 IPC、frame 映射、user-space termination 与 revoke stub。
GUI 对象先定义 buffer/surface/compositor/seat 的 layout，不实现完整 compositor。

**第二阶段 —— 把语言效果集中到五个最高危错误。**
按排序先实现 `Cap<T,Rights>`、`ptr<phys>` 从 frame cap 派生、`#[ipc_handler]` 契约、
栈预算、irq/preempt/alloc 状态。
侵入式容器、RCU、复杂锁序与 WCET 可以在 unsafe API 上先做，
但**不能永久停留在「开发者记得规则」**。

**第三阶段 —— 才引入用户态驱动与完整 GUI。**
在第二阶段证明 type_tag、rights、handler、栈与启动态之后，
file/shm/framebuffer/compositor/surface/seat/buffer 才能真正形成 capability 图形栈。
这样每一次扩展都是给已有对象模型**增加 type_tag 与 API**，而不是重新设计授权机制。

**验证目标应按 TCB 分层**，而不是一开始追求 seL4 级全证明：
- **最低层**：模型检查或属性测试验证 CNode 派生、rights 收缩、revoke 与 slot reuse
- **中层**：对 IPC stub 与 region metadata 做布局差分测试
- **上层**：对服务协议做 fuzz

待对象模型稳定后，再选择关键不变量进行机械化证明。
**验证对象边界必须先于验证实现细节。**

---

## §13 外部对标：值得抄的是能力/TCB 边界，不是具体 C 结构

> ⚠️ **口径**：本节引用的**外部项目的数字与结论未在本仓复核** —— 只作为设计取向的
> 参照，**不作为事实基线**。仓内可复核的事实一律在 § 2。

| 外部项目 | 已核实结论 | 对 JHYY 的建议 | 不应抄的部分 |
|---|---|---|---|
| **seL4** | CSpace/能力模型；实现级正确性、安全属性证明与二进制验证（工业强度先例）；证明工作量记录为 **11+ 人年**；形式化验证曾发现 **460+ 个 bug，而测试只发现 16 个**（⚠️ 外部数据，**未在本仓复核**） | 先冻结对象、CSpace、revoke 语义；把可验证的接口边界、对象不变式与测试 oracle 设计成可审查形式 | 复制 C 风格的全局状态与宏 |
| **Rust for Linux** | 2025 年维护者峰会后 Rust 结束实验期、进入长期支持阶段，已有生产驱动；但 DMA API 抽象与 C/Rust 所有权边界仍冲突；Linux 内核首个 Rust 代码 CVE 源于链表并发移除导致 prev/next 损坏 | 从一开始统一 unsafe 内核边界 ⇒ 避免 Rust-for-Linux 最大的一部分组织成本 | 把已有 Linux 惯用法当天然正确；先复制 `Box/Arc` 再补 `ListLinks` |
| **Asterinas** | 内核分为特权 OS 框架与去特权 OS 服务，以缩小内存安全 TCB | capability 成为进入 OS 框架的入口（而非模块可见性） | 只以 safe/unsafe 替代授权 |
| **Redox** | 完整的 Rust 微内核 OS | 借鉴服务化与 IPC 测试 | 未经验证的具体服务结构 |
| **Zig** | 显式分配器、无隐藏控制流、comptime、错误值代替异常 | 函数签名显式体现 allocator 或 `may_alloc`；编译期计算 capability layout / section header / IPC stub；错误通过值返回并强制处理 | 把大量属性推迟到运行期 assert；放弃静态类型与布局证明 |
| **CHERI / Morello** | 硬件能力由元数据与权限标签保护；Morello-Cerise 强封装性已有机械化证明 | 预留 provenance 与版本扩展位；对象模型应保持可映射到 CHERI | **声称 amd64 已实现硬件能力**；承诺 CHERI 兼容 ABI |

**Theseus 类「语言化状态隔离」**：由于搜索结果把同名 OS 项目与另一篇芯片论文混淆，
本仓不引用未经核实的项目细节。可成立的通用结论是：
**语言能表达模块/状态边界，却不能替内核决定设备 quiesce、抢占和故障恢复。**
⇒ 限定为「服务状态由类型与 capability 边界隔离」，不当作减少运行时机制的依据。

---

## §14 事实缺口 —— 每项落到具体的 OS-N 槽

> 下列是**规范没记载、且 OS 侧原设计文档已删**的事实缺口。
> **不是「待拍板的设计」** —— 设计的部分已在前面的章节定稿（§3.6 / §4 / §7 / §8 / §9）；
> 这里列的是**「还不知道的事实」**，每一项都有**归属槽、产出物、阻塞谁** ⇒
> 不是一个无主的清单。

| 事实缺口 | 归属槽 | 产出物 | 阻塞谁 |
|---|---|---|---|
| 真实内核调度模型（线程 / runqueue / 时间片 / 优先级 / SMP） | **OS-1 / OS-2** | BootState 扩展 + 调度骨架 | OS-2 栈观测、OS-12 效果骨架 |
| 中断与 trap 模型（entry 栈 / callee-saved / redzone / IRQ 线程化 / 嵌套） | **OS-3** | `#[naked]` interrupt 契约 + 4 KiB 中断栈 | OS-3 最小 kernel.efi |
| 内存管理模型（frame metadata / allocator / slab / 页表 / ASID / page fault handler 位置） | **OS-4** | 帧 + 分配器设计 | OS-4 栈与分配、OS-14 Cap 真 T |
| CSpace 与 CNode 的实际结构（slot 空间 / CNode 增长 / 跨 CNode 解析 / 对象 header） | **OS-13** | manifest 里的对象与 slot 空间 | OS-13 manifest、OS-14 Cap 真 T |
| CDT / 撤销树的实现细节（反向边存储 / in-progress / RCU grace / 映射 unmap） | **OS-13 / OS-15** | CDT 数据结构 + `retract_cap` / `revoke_object` | OS-14 Cap 真 T |
| capability 对象表（11 个 type_tag 之外的语义区分、kernel-internal 对象、`AddressSpace`/`Mapping` 是否要 cap） | **OS-13** | 完整 type_tag 表（`Frame` 已定，见 §4.3） | OS-13 manifest |
| capability 版本与 provenance（派生 proof / 跨进程 / 持久化是否安全） | **OS-13 / OS-14** | provenance 规则 + `gen` 语义（已定，见 §3.5） | OS-14 Cap 真 T |
| region_table 的 owner / 生命周期（`kernel_shared` / `unsafe_share` / `cap_namespace` 的引用与 revoke） | **OS-13** | region_table 字段定稿 | OS-13 manifest |
| panic / fault 模型（oops 分类 / thread terminate / namespace revoke / 是否支持 kernel continuation） | **OS-12** | 终止面分类（已定框架，见 §9.4） | OS-12 效果骨架 |
| GUI 完整对象模型（像素格式 / modifier / 原子提交 / presentation feedback / input focus） | **OS-13**（或明确推迟） | 显示对象定义 | GUI 冻结（不在当前主线） |
| boot / hardware 适配范围（第一版支持哪些主板 / APIC / 定时器 / 串口 / 显卡 / SMP） | **OS-3** | 硬件适配清单 | OS-3 最小 kernel.efi |
| `.jhyynb` 加载与签名语义（是否需要签名 / 测量 / 加载顺序 / 未知 section / contract 是否强制） | **OS-3** + **OS-16** | loader 规格 + contract 校验规则 | OS-3 loader、OS-16 可信工具链 |
| 编译器兼容性（`T` 重新解析是否破坏 ABI / 版本迁移 / 旧 binary 共存） | **OS-5** | ABI 收敛方案 | OS-5 ABI 收敛 |

> ⚠️ **2026-10-30：OS 侧原设计文档（`../JiHuiYiYou-OS/` 下 17 份 v0.0.x 设计文档 +
> `deep_research/` + README + CLAUDE.md）已全部删除**（commit `f98d83d`）——
> 那批文档写于编译器 **v1.8.3** 时代（C 宿主 + QBE + ABI v1.0.0），大量结论已被推翻。
> **内容不丢 —— 保留在 git 历史**（`git show 24589bd:docs/<file>`）。
> ⇒ **跨项目设计基线现在单点落在本仓 `docs/coordination/`。**

---

## §15 交叉引用

| 文档 | 用途 |
|---|---|
| [`docs/coordination/JHYY_编译器侧设计终版.md`](JHYY_编译器侧设计终版.md) | 编译器分期路线 · pass 全表 · 规范一致性门 · 编译器侧 5 条「不确定性与需补材料」· 静默错误清单 |
| [`docs/abis/jhyy-lang-spec-v4.0.0.md`](../abis/jhyy-lang-spec-v4.0.0.md) | 语言规范（锁定 2026-10-24）· §2.6 `Cap<T>` |
| [`docs/abis/jhyy-abi-v4.0.0.md`](../abis/jhyy-abi-v4.0.0.md) | ABI 白皮书（锁定 2026-10-24）· §2.5 `Cap<T>` · §12 已知偏离 |
| [`docs/abis/jhyy-binary-format-v1.0.0.md`](../abis/jhyy-binary-format-v1.0.0.md) | `.jhyynb` 二进制格式（**设计稿，未实装**）· §7 cap_init |
| [`docs/plans/v4/README.md`](../plans/v4/README.md) | **版本系列索引** —— 每个版本槽一份 `v4.X.Y-plan.md`（性能线 6 + OS 线 16） |
| [`docs/internal/workarounds.md`](../internal/workarounds.md) | W-NNN 台账（**ACTIVE = 1** —— W-170：`jhyy build` 不处理 `#[link_section]`）· W-105 借用检查最小版 · W-113 `asm!` 内联 · W-136 side-file |
