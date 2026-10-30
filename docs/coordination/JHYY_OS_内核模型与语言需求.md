# JHYY 操作系统内核模型与语言需求深度研究报告

## 摘要

本报告的唯一内部事实来源是用户提供的三份规范：语言规范 `jhyy-lang-spec-v4.0.0.md`、ABI 规范 `jhyy-abi-v4.0.0.md` 与二进制格式设计稿 `jhyy-binary-format-v1.0.0.md`。据此，JHYY 的能力路径已经不可逆：`Cap<T>` 的 8 字节 wire、cnode_idx/depth/rights、cap_init 表、IPC dispatch 表与 region_table 共同构成一个以 capability 为唯一授权货币、以 `.jhyynb` 为 capability 与区域声明载体的执行对象格式。因此，本报告明确建议 jhyy_OS 采用 **seL4 式能力微内核作为长期目标形态**，但不建议在第一阶段按教科书微内核拆分全部驱动；初始设备、页表演进和引导相关代码应集中在特权区，以混合内核的工程边界换取从 Windows 寄生到裸金属的能力闭环。

规范没有记载调度器、中断栈、物理内存模型、撤销树、锁语义或 D-lock 全集，因而这些都不能被宣称已经锁定。规范只给 `depth:u8`，这足以支持 256 层内的祖先证明和常数界撤销，却不足以独立表达 revoke-while-in-use、并发可撤销引用、跨版本对象身份及审计；撤销必须另有对象头/反向边/引用计数或 quiesce 机制。GUI 类型枚举已经具备 compositor/surface/seat/buffer 等对象骨架，但要支撑桌面，还需窗口对象、像素格式、显示 lease、事件聚焦与事务语义，其中 endpoint_focus 只是焦点授权的一枚 token，不是完整窗口状态机。

`.jhyynb` 最适合作为“capability/region/IPC 事实声明格式”，但其三个专属 section 尚不能表达栈上界、irq_ctx、锁序、分配点、WCET、handler 版本或 panic 可达性。建议新增 `contract` 或扩展 `debug_group`，并明确编译产物元数据与可加载模块的语义等级。CHERI 目前并非 amd64 的可用路线；在软件能力条件下，JHYY 必须把对象存在性、rights 单调性、派生链、跨地址空间映射与 wire 类型参数变成内核强制执行不变量，而把可证明无能力泄漏、region 内边界、栈上界与 handler/struct 一致性尽量上推至编译器。

## 一、事实基线：三份规范已经锁定的不是“想法”，而是一套 capability ABI

**`Cap<T>` 已经是对象引用，而不是文件描述符的整数别名。** 语言规范把 `Cap<T>` 定义为 8 字节 wire：`cnode_idx:u32` 位于第 0 字节，`depth:u8` 位于第 4 字节，`rights:u16` 位于第 5 字节，`padding:u8` 位于第 7 字节；rights 的 bit0=R、bit1=W、bit2=G[1]。这给出三个独立维度：slot 索引、从 CNode 根出发的层级和权限。它不只是“一个整数”，因为 slot 语义只有在 CNode 与 depth 共同解释时才有意义；这是典型 seL4 CSpace 思路，而不是单纯句柄表。真正异常的则是当前 `T` 不被解析，`Cap<i32>` 与 `Cap<i64>` 被当成同一类型[1]。因此 wire 已具备对象身份，语言层却还不能把对象身份对应到对象类型。

| 已锁定事实 | 二进制含义 | 对内核设计的影响 |
|---|---:|---|
| `cnode_idx:u32` | 至多 2^32 个逻辑 slot 编号 | slot 空间不必连续；内核可划分 CNode、保留特殊索引 |
| `depth:u8` | 从当前 CNode 根起至多 256 层 | 撤销链长度有静态界，但不能单靠它识别对象身份或兄弟关系 |
| `rights:u16`，低 3 位 R/W/G | 每 cap 携带授权标志 | 权限检查在内核对象访问点统一执行，而不是由服务策略散落决定 |
| `padding:u8` | 当前未解释 | 不可用作自由用途；建议保留给未来 flags/version |
| `Cap<T>` 的 `T` 不解析 | 当前所有 `Cap<T>` 实例等价 | 内核无法在类型系统层信任“这是 frame cap” |

**`.jhyynb` 已经不是通用 ELF 的复制品，而是为 capability 启动而设计。** magic 为 `JBE\x01`，header 112 B；cap_init 每表项 32 B，type_tag 定义 0=endpoint、1=page、2=framebuffer、3=console、4=file、5=shm、6=compositor、7=surface、8=seat、9=buffer、10=endpoint_focus[3]。type_tag 同时承担对象类别和权限类别：1=page 偏向地址空间映射，2=framebuffer 表示显存访问，4=file 与 5=shm 暗示两种不同的持久/共享数据模型。若内核只把它当成“启动时插入某个 slot 的数字”，就会浪费这份最昂贵的静态信息。

IPC dispatch 表每表项 16 B，包含 `msg_tag:u32`、`handler_fn_off:u32`、`cap_off_count:u16`、`cap_off_table_off:u32`；它引用 D16 wire `{n_caps:u16, _pad:u16, cap_offsets:[]u16}`，内核收到 IPC 后按 `cap_offsets` 原地改写 `cnode_idx` 以避免 deep-copy[3]。这说明 M3 ABI 不把 cap 当作可自由转储的载荷，而是在 message buffer 里保留“当前进程 slot 表中的偏移”，由内核在收发边界重新解析、重新证明。原地改写是有价值的性能决定，但它也意味着 message struct 与 cap_offsets 的布局错配会变成静默内存破坏。

region_table 每表项 24 B，region kind 为 0=anon_arena、1=mmap、2=raw_mmio、3=unsafe_share、4=cap_namespace、5=kernel_shared，rights 包括 R/W/X/share，并带 growable、cow、pinned、lazy_commit 等 flags[3]。这是一份“区域声明”，不是完整 VM 对象模型：它不规定页粒度、颜色、cache policy、NUMA 节点、映射计数、evict 顺序，也不携带 lifetime/borrow checker 数据。规范还明确声明 Region Table 不携带 borrow checker 数据，理由之一“Kernel 不解决语言问题”[3]。这一条不是拒绝语言了解内核，而是拒绝让运行时承担语言语义。

**ABI 的当前状态说明语言已经跨过“能表达能力”，但尚未跨过“能在内核中安全执行能力代码”。** 四个目标 amd64_win、amd64_win_freestanding、amd64_sysv、amd64_sysv_freestanding 均已在自托管后端覆盖[2]；`.jhyynb` 的 section 要求 4 KiB 对齐[3]，与 x86-64 页尺寸天然一致。但全 spill 策略只保存 RBP，自举编译器最大单函数帧达到 234080 B（约 229 KiB），目前依靠 `-Wl,--stack,67108864` 补偿[2]。这直接意味着内核栈模型不能按 C 风格的 8–16 KiB 默认值设计：229 KiB 已超经典 8 KiB 栈，未来最坏栈深度必须由编译器证明，而不能在 ABI 手册里继续作为 warning 存在。

规范摘录数据（可下载：[规范摘录数据 CSV](/data/workspace/dr:JHYY_OS_内核模型与语言需求/规范摘录数据.csv)）将上述事实拆成可回溯单元格。表中所有数字均来自三份规范，不能外推为运行时性能或内存预算。

## 二、内核形态：建议采用能力微内核，但初始特权区按混合内核组织

**倾向性结论是能力微内核，不是骑墙的“微内核/宏内核折中”。** 决定性事实不是 `Cap<T>` 的名字，而是三份规范共同锁定的完整授权链条：对象类型由 cap_init 的 type_tag 声明，对象引用由 cnode_idx 与 depth 定位，权限由 rights 约束，跨域传输由 IPC dispatch 的 cap_offsets 重新绑定，地址空间/共享内存/显存/I/O 区域由 region_table 声明。若采用单一内核且用全局函数指针或共享状态授予设备访问，这套二进制格式将变成装饰：cap_init 只剩“启动时开权限”，cap_offsets 退化成普通 fd 传输，region_table 退化为 mmap 参数。若采用传统混合内核，超级用户态服务仍以 UID、root、iopl、全局地址空间或动态模块为中心，能力格式也无法成为统一授权货币。

能力微内核的真正收益有三项。第一，故障域由 capability 授权决定，而不是由进程是否拥有 root 决定。第二，对象服务可独立重启；即使早期 jhyy_OS 不利用这一点，二进制格式也不需要迁坟。第三，形式化与审计的目标面可收敛到 CSpace、VSpace、调度/中断/IPC 与少数对象类型。seL4 已通过完整函数正确性证明，后续工作又扩展到机密性、完整性、二进制证明与最坏执行时间分析[7]；南京大学对 seL4 证明库的近期工作同样将其实现级正确性与安全属性作为标杆[8]。这不是说 jhyy_OS 应复制 seL4 的证明规模，而是说明该形态的证明对象边界在工业界已有成熟先例。

**但建议的微内核不是“第一版就把网卡、磁盘、GPU、USB 全部用户态化”。** 对小团队而言，用户态驱动带来三类风险：跨进程 IPC 与映射协议，驱动崩溃后的设备 quiesce，以及 capability 协议和硬件状态机的双重实现。更合适的组织是三层。Tier 0 是真正可信计算基：对象/空间/IPC/调度/中断/cap 撤销、最低页表操作与 platform 抽象；Tier 1 是初始随 kernel.efi 启动的特权服务，包括物理内存管理、早期 console、必要的 bus/中断控制器、根任务与 bootstrap；Tier 2 才是可重启用户服务。Tier 0 与 Tier 1 可以在同一特权级别，却必须用不同编译单元、独立 API 边界和独立 capability 入口隔离。这样既保留未来向严格微内核迁移的二进制与类型边界，又避免一次完成全部设备隔离。

| 形态 | 与现有规范相容性 | 首次出原型成本 | 能力隔离收益 | 本报告结论 |
|---|---|---|---|---|
| 能力微内核 | 高；三份规范几乎就是其对象与授权模型 | 中高 | 高 | **长期目标，建议锁定** |
| 初始混合/特权区 | 可容纳早期物理内存、platform、console | 低 | 中 | **v0.0.1 工程形态** |
| 传统混合内核 | 只有 ABI 可复用，cap 格式失去必要性 | 低 | 低 | 不推荐 |
| 纯单体内核 | 容易实现 syscall 集合 | 低 | 极低 | 与 type_tag/cap_offsets 冲突，明确排除 |

**规范没有锁定的最小内核对象集合，是阻碍 Tier 0 冻结的第一项事实缺口。** 三份规范没有给出线程、调度类、就绪队列、时间源、中断控制器对象、页表根、ASID/PCID、地址空间、物理 frame 元数据、分配器 slab、CNode 自身布局或 revoke 队列。因此“能力微内核”只能是形态建议，不能写成 jhyy_OS 的对象清单。首次架构冻结应至少回答：线程与地址空间是否分离；内核对象是否统一 header；CNode 是否可映射与增长；revoke 是否同步；中断是否也是 capability；page fault 由内核还是用户 pager 处理。

## 三、CSpace 与 depth：256 层够证明祖先关系，不够表达完整撤销

**`depth` 的语义应是“当前 CNode 根到 slot 的层级数”，而不是对象生成次数。** 规范只记载 `depth:u8@4`[1]，没有给出名称解析算法。结合 cap 派生，最自然的解释是：深度为 0 表示直接挂在当前命名空间根的 slot；对 CNode cap 做 resolve 或 derive 时，新路径的层级增加。若如此，`depth` 允许内核在常数界内证明一条解析链不超过 255 次续接，并使撤销遍历的栈或队列深度受 256 上限约束。8 位还带来重要工程约束：深度不仅是能力证明，更是动态资源界。任何 derive 操作若不加检查，深度溢出既可能造成祖先关系失效，也可能被利用绕过 slot 归属。

**撤销树的核心不是树形索引，而是对象身份及“撤销时谁还持有引用”。** 规范没有提供 CDT/CROB/反向引用或 revoke 算法，所以这里必须区分事实与建议。在 seL4 中，CSpace 由 CNode 组成，派生出的 cap 若与父 cap 指向同一内核对象，撤销必须沿派生关系而非 CNode 索引树工作；简单从 CNode 根 DFS 会漏掉跨 CNode 别名。JHYY 至少应引入四种对象关系：

| 关系 | 表达内容 | 撤销时是否必须遍历 |
|---|---|---|
| parent → child derive | 派生来源与深度 | 是，用于寻找后代 |
| object → capability slot | 一个对象可被哪些有效 cap 引用 | 是，用于判定是否真正无引用 |
| mapping → page table entry | 一个 frame 当前映射在哪些页表 | 若支持 revoke/quiesce，必须 |
| cap slot → CNode | 当前 slot 的容器与索引 | 是，用于定位表项 |

单靠 `depth:u8` 只能证明“child 比 parent 更深”，不能证明 child 仍指向同一对象，不能证明没有兄弟 cap，也不能证明映射仍然存在。若撤销仅按 CNode 树遍历，跨 CNode 别名会造成遗漏；若按对象反向链表遍历，撤销是精确的，却需要每个对象维护反向边。建议以对象反向边作为语义真源，CNode depth 只作为派生证明与遍历界。

**rights 单调收缩应由 derive 系统保证，而不是由调用约定建议。** 规范的 R/W/G 只占 16 位中的 3 位[1]，还有 13 位 padding 空间。建议在未来 16 位布局中显式定义：derive 只能清位，不能置位；root 的 rights 是对象类型允许集的子集；派生 cap 的 rights 是父 rights 的子集；映射类操作可附加 VM rights，但不能产生新 capability rights。这是运行时不变量，必须由 `cap_derive(src, new_rights)` 系统调用强制。G 不应被允许由 R/W 派生得到，除非内核显式执行“升级需要授权对象”的协议。

**软件能力不能阻止用户态主动交出权限，只能保证权限不会凭空增加。** 这一点决定 capability 心理模型：权限缩小是可靠的，用户自愿 `share` 是服务层面的问题。若 compositor 将 full-framebuffer cap 交给应用，内核没有义务也不能阻止“用户态自己放弃了隔离”。因此内核应提供不可伪造的 token、最小权限派生和 revoke，策略层则负责焦点、剪贴板、屏幕录制与跨应用 share。episode_focus=10 是焦点 token 的起点，不是焦点策略本身。

## 四、type_tag 与 GUI：对象骨架已经出现，完整桌面尚未被规范定义

**type_tag 不是设备枚举，而是能力对象分类。** 11 个值中，endpoint、file、shm 偏 IPC/数据；page、framebuffer、compositor、surface、seat、buffer 偏图形与地址空间；console 是传统输出对象；endpoint_focus 是焦点授权。这说明内核至少要认识两类 region/page 对象与四类图形对象，而不是把所有图形资源压成“一块显存”。这优于把 drm/gpu 抽象泄漏进语言，也与“Kernel 不解决语言问题”相容：内核解决对象存在、授权、映射与生命周期，窗口管理器解决布局与策略。

**compositor/surface/seat/buffer 足以构建双缓冲显示管线，但不足以构成桌面。** compositor 可作为事务提交对象；surface 是应用可见绘制目标；buffer 是可共享像素内存；seat 聚合键盘、鼠标、触摸与焦点。表面上看，type_tag 已经具备交换缓冲所需的对象集合，但规范没有定义像素格式、平面/stride、modifier、损伤区域、原子提交、presentation feedback、VSync、hotplug、input 事件队列、scancode 映射、DPI、拖放或截图授权。framebuffer=2 与 buffer=9 也需要明确区分：前者更像连续显存区域，后者更像可共享、可变格式的图形缓冲区。若两者最终语义相同，应合并；若不同，应在 type_tag 之外补充对象专属数据结构。

| 桌面能力 | 规范是否已记载 | 建议对象或能力 | 若不实现的直接后果 |
|---|---|---|---|
| 应用绘制到离屏 buffer | 有 buffer/surface 线索 | buffer cap + surface attach | 无法区分图形资源与普通共享内存 |
| 双缓冲/提交 | 有 compositor/surface 线索 | transaction endpoint | 撕裂、跨客户端状态不一致 |
| 输入分发 | 有 seat | seat ep + focus cap | 任何 client 可读取全局输入 |
| 焦点切换 | 有 endpoint_focus=10 | focus token 与 lease | 无法可靠防止后台录屏或按键监听 |
| 多显示器/hotplug | 未记载 | display lease cap | compositor 与驱动强耦合 |
| 像素格式/modifier | 未记载 | 对象专属格式字段 | 应用可凭 framebuffer 误解释显存 |

**焦点应以 capability 授权，而不是以“前台窗口 id”授权。** seat 的键盘事件只应流向当前持有有效 focus cap 的 surface endpoint；切换焦点由 compositor 通过原子 derive/swap 完成。focus cap 应可撤销、可绑定到 surface 生命周期，并区分键盘、指针、触摸和全局快捷键。这里的规范未记载项会阻塞 D-GUI-12 的接口冻结：M3 ABI 使用 MS x64 函数指针与 `#[naked]` interrupt[3]，但规范没有给出 keyboard/mouse 事件的 message struct、focus revoke race、surface destruction 与 in-flight frame 的关系。

## 五、CHERI 缺失下，JHYY 的软件能力必须把“内存安全”与“授权安全”拆开

**amd64 没有 CHERI，JHYY 不能把 `Cap<T>` 宣传为硬件不可伪造指针。** 软件能力的可靠部分是“内核对象存在且调用者拥有 slot”，不可靠部分是“用户态数据没有被解释成另一种类型或伪造 slot”。slot 索引可以写入任意内存、被 memcpy、被序列化和反序列化；没有 type/version/provenance 元数据，无法区分合法 slot 和巧合整数。CHERI 的目标是让能力成为受硬件标签保护的指针式原语，并证明强封装；2025 年仍有针对 Arm Morello 强封装性的形式化工作[9]。这与 amd64 上“用户可自由复制 8 字节整数”的现实是根本不同。

**软件能力能做到的是 object capability，不是 fat-pointer 空间能力。** object capability 模型下，应用只能持有一个不可伪造的引用，并只能通过受控入口调用对象方法；这是 seL4 的强项，也是 `.jhyynb` 的 cap_init/IPC 设计自然对应的模型。空间能力则要求每次内存访问都携带边界与权限；没有 CHERI，普通指针解引用无法由硬件检查。JHYY 未来若有 `ptr<user>`/`ptr<kernel>`/`ptr<phys>`，它们应被定义为“经过类型/上下文证明的受限指针”，而不是“硬件保证越界 fault”的能力。这条边界直接影响语言承诺：编译器可以说“合法程序不会在内核上下文任意解引用用户指针”，但不能说“所有物理地址访问都受硬件 capability 约束”。

**CHERI 缺失对语言提出了四项额外要求。**

1. **CNode slot 必须版本化。** 建议在 8 字节 wire 中永久保留 `padding:u8`，后续以 1 字节 generation/version 加软件证明承载对象版本；在兼容前不应复用 slot 索引，或复用前必须清零并维护全局 epoch。否则 slot 释放后再分配会让旧 cap 继续访问新对象。
2. **`Cap<T>` 的 `T` 必须被解析。** 只有内核对象类型进入语言类型参数，编译器才能证明“frame cap 不会进入 endpoint 接口”。硬件边界缺失时，类型就是唯一廉价防线。
3. **rights 必须进入类型参数或 phantom 参数。** `Cap<T, Rights>` 让编译器区分只读映射与可写映射，避免所有 cap 退化成 `Cap<i32>`。
4. **provenance 必须成为语言与 ABI 的不变量。** cap_init 的 `provenance_seed_off`[3] 已有种子字段，但规范没有说明如何 hash、绑定、派生或验证。建议每枚派生 cap 携带版本、祖先 proof 或单向 chain token，且 user-space 不得自行构造 `Cap<T>`。

**对 amd64 的短期建议是“软件 capability + 可选 CHERI 后端”，而不是等待 CHERI。** Morello 是 Arm 原型平台，不能直接解决 amd64 硬件缺口[10]。如果未来支持 CHERI 架构，可将同一对象模型映射为硬件能力；在此之前，JHYY 的可靠性目标应是内核对象模型与协议安全，而不是声称达到 CHERI 的空间安全强度。

## 六、语言—内核边界：编译器证明 shape，内核强制执行 authority

**正确的分工不是“编译器懂 OS，或内核懂 Rust/JHYY”，而是两者共享一份可机器检查契约。** 编译器输入源码与 `cap_init`/`ipc_dispatch`/`region_table` 声明，输出 `.jhyynb`；内核只信任该文件的格式、签名（若引入）、cap slot 与对象。编译期应证明“类型与 shape”，运行期负责“对象存在、权限、原子性与跨地址空间状态”。这满足第 5 原则中“Kernel 不解决语言问题”的合理解释：内核不实现 JHYY 的完整类型论，但必须实现 capability authority 的真源。

| 不变量 | 最佳检查阶段 | 理由 |
|---|---|---|
| `Cap<T>` 的 T 与对象 type_tag 相容 | 编译期 | shape 与类型参数可在链接前枚举 |
| rights 单调收缩 | 编译期生成证明，运行期内核强制 | 派生结果仍是运行时对象状态 |
| `Cap<T, R\|W>` 传入需要 W 的接口 | 编译期 | 纯类型权限 |
| IPC `msg_tag` 唯一及 handler 签名一致 | 编译期 | 同一 binary 的静态有限集合 |
| `cap_offsets` 指向合法 wire slot 且不越界 | 编译期布局验证；内核做边界检查 | offsets 属于 message shape，但可能被不可信进程构造 |
| message struct 内各字段 size/align 与 handler 期望一致 | 编译期 | 无 packed、显式 `_pad` 下可完整检查[1] |
| region 内访问不越页/对象 | 运行期为主，region 边界可静态检查 | 长度与映射在运行期变化 |
| 跨进程 cap 派生、拷贝与 revoke | 运行期 | 涉及全局对象图与并发 |
| 页表安装、TLB、ASID、中断屏蔽 | 运行期 | 硬件与全局状态 |
| 栈用量上限、irq_ctx、锁序 | 编译期分析 + 链接期断言 | 属于单个 binary 的控制流事实 |

**栈深度必须由“可关闭警告”升级为可验证属性。** 229 KiB 最坏帧已现实存在[2]，而规范规定栈槽只保证 8 字节对齐、没有 16 字节保证[2]。这会同时影响 SIMD 参数、IPC stub、汇编接口和内核 trap frame。建议每个函数输出 `max_frame`、`max_call_depth` 与 `requires_alignment`；每个线程创建点校验 `stack_reservation >= frame_of_callers + redzone`。对于 `#[naked]`、`asm!` 和 interrupt entry，汇编作者必须手工给出栈预算，编译器不得把它们视为零。否则 ABI 可以编译通过，却在内核递归 IPC、页错误路径或中断嵌套时破坏相邻栈。

**`.jhyynb` 缺少第四个契约 section。** cap_init、ipc_dispatch、region_table 回答“拥有什么、接收什么、访问哪里”；它们没有回答“执行时允许做什么”。建议增加 `contract` section，至少包含 `max_kernel_stack`、`may_sleep`、`irq_ctx`、`preempt_disabled`、`holds(L)`、`may_alloc`、IPC handler version、panic category 与 WCET class。若不想扩大正式加载格式，可把它放在 `debug_group` 的子节，但必须区分两类子节：一类是工具和内核必须验证的 contract metadata，另一类是可选调试信息。不能给调试信息内核加载语义，也不能给安全契约“debug”名称。

## 七、契约格式：`.jhyynb` 适合做事实载体，但表项必须版本化且禁止隐式默认值

**cap_init 的 32 B 表项已经足够丰富，但 name_idx 不是类型。** 表项包含 type_tag、cnode_idx_hint、rights、depth、name_idx、init_call_off、provenance_seed_off[3]。`name_idx` 适合诊断，不适合安全决策；安全决策必须用 type_tag、rights、目标 CNode 与对象身份。还缺少 target CNode、parent cap、init 阶段、生命周期 owner、quiesce callback offset 与是否允许进一步 derive。若只提供 cnode_idx_hint，加载器无法区分“建议放哪”与“必须放哪”，也无法证明没有 slot 冲突。

**IPC dispatch 的原地 cap 改写要求布局与权限双重校验。** 16 B 表项本身可以静态检查[3]；真正风险在 D16 wire 的 `cap_offsets`：每个 offset 必须落在 message buffer 的 `Cap<T>` 对齐槽，指向合法 slot，不重复指向同一 slot，且 handler 没有以非 cap 字节覆盖 cap。建议编译器为每条 handler 生成 `cap_offset_bitmap + type_tag_allowlist + rights_lower_bound`。内核仍必须检查 offset 边界、目标 slot 和 rights，因为 message 可能来自不可信进程；编译器负责保证 trusted sender 的布局一致性。

**region_table 应成为“由谁管理”的元数据，而不是页表格式。** 24 B 表项已经包含 region kind、rights、base_vaddr、size、flags[3]。但 anon_arena、mmap、raw_mmio、unsafe_share、cap_namespace、kernel_shared 六类的 owner 语义完全不同：raw_mmio 的 pinned/lazy_commit 很可能不适用；kernel_shared 不应允许普通 user process 任意 unmap；cap_namespace 不应参与 cow。建议内核根据 kind 的白名单解释 flags，而不是让 flags 成为通用位图。4 KiB 对齐[3]适合直接 mmap section data，却不应被误解为所有 region 必须按 4 KiB 粒度管理；huge page、cache attribute、device memory 与 sub-page 元数据仍需独立规则。

| 表 | 当前适合表达 | 必须补充，否则无法静态验证 |
|---|---|---|
| cap_init | 对象类别、初始 rights/depth、init call、provenance seed | 目标 CNode、parent、init phase、生命周期 owner |
| ipc_dispatch | msg_tag、handler offset、cap offset 表 | cap slot 位图、type/rights allowlist、handler 版本 |
| region_table | 区域类别、地址、长度、R/W/X/share、增长/复制/pin/lazy | cache/ordering、page size policy、owner、生命周期、WCET 属性 |
| contract（建议） | 栈、sleep、中断、锁、分配、panic | 编译器输出是否可信、是否签名、是否可被 loader 忽略 |

## 八、第 5 原则“Kernel 不解决语言问题”的正确边界

**原则本身成立，但“语言问题”必须被严格定义。** 本报告建议的定义是：内核不实现类型推导、trait 解析、借用区域、闭包捕获、泛型单态化、integer promotion 或源码诊断；这些是 JHYY 编译器的责任。内核还必须负责对象存在性、capability authority、页表、TLB、调度、中断、并发原语、设备状态与全局资源仲裁。若编译器试图让“持有 `&mut Frame`”直接操作物理页，就是越过边界；若内核仅验证 cap 的 cnode_idx/rights，却拒绝暴露对象类型，则会迫使每个服务用整数和 magic number 重建类型系统。

**边界条件一：当内存安全依赖全局内核状态时，内核必须破例提供安全抽象。** 页表、RCU grace period、PerCpu 偏移、中断屏蔽与锁都是全局硬件/运行时事实。编译器不能凭源码单线程推断“当前 CPU 的 PerCpu 引用是否仍然有效”。此时内核应输出稳定 unsafe primitive，并配合约化 safe wrapper；语言可检查 token 的持有，但无法凭类型创造原子可见性或禁止跨 CPU 重排。

**边界条件二：当错误语义必须由内核恢复时，语言不能独自定义 panic。** 内核 oops、double fault、page fault、cap fault、IPC timeout 涉及 trap frame、线程状态与调度决策。编译器可以提供 `#[panic_handler]`、错误分类、栈追踪元数据与 `no_unwind` 证明，但“线程 terminate / namespace revoke / kernel fault”必须由内核决定。规范当前无 panic、无栈展开[1]，因此需要先定义 fault 到达哪个 endpoint、是否捕获、是否撤销整个 CSpace。

**边界条件三：当 wire format 跨版本时，内核必须参与兼容性。** `.jhyynb` header、section kind、cap_init、ipc_dispatch、region_table 都有演进需求。内核可以拒绝未知 kind，却必须理解最低版本、cap wire 扩展与 contract 语义。若把格式升级完全交给编译器，loader 会在不知情状态下把新 section 当垃圾数据；若交给服务进程，则 boot 链又失去统一版本仲裁。

**边界条件四：当证明本身会改变系统状态时，运行期不能省略。** 编译器可证明某条路径不 sleep、不 alloc、不超过栈预算，但无法知道硬件是否真的发生中断、页表是否有效或另一 CPU 是否已释放 frame。运行期检查点是安全状态机的组成部分，而不是语言失败。反过来，运行期不应重新发明语言已经证明的 message 布局。

## 九、OS 对语言的需求清单：按“缺失后能否形成静默越权或无法启动”排序

下表将需求按失效严重性排序。“后果”采用可证伪标准：若没有该能力，能否在编译期被触发、是否只能依赖代码评审、是否会扩大 TCB。规范状态依据用户提供的三份规范；其中“无”不表示未来不能实现，只表示当前摘录未记载。

| 排序 | 需求 | 内核为何需要 | 不实现的后果 | 规范当前状态 | 阶段 |
|---:|---|---|---|---|---|
| 1 | `Cap<T>` 的 T 真实解析 | T 决定对象操作集；type_tag 必须与语言类型一致 | `Cap<i32>`=`Cap<i64>`，frame/endpoint/file 被混用，内核边界退回整数 | 当前 T 硬编码 i32[1] | 编译期/运行期 |
| 2 | `Cap<T, Rights>` 参数化 rights | R/W/G 是 16 位 wire 的一部分[1] | 只读对象可误传给 mut API；权限错误延后到运行时 | 仅存在 R/W/G bit | 编译期 |
| 3 | rights 派生单调收缩 | capability 模型必须禁止权限升级 | 派生子 cap 可绕过授权；CDL 无法表达 | 未记载 CDL 规则 | 编译期证明+运行期强制 |
| 4 | `ptr<user>`/`ptr<kernel>`/`ptr<phys>`/`ptr<io>` | trap/access 语义、cache/ordering 与可解引用上下文不同 | 用户指针在内核任意解引用；物理 I/O 与普通 RAM 混用 | 地址空间类型不存在[1] | 编译期 |
| 5 | `ptr<phys>` 从 `Cap<frame>` 派生 | frame cap 才是物理页的授权真源 | 物理地址可绕过 cap；DMA/显存缺少审计 | 有 frame/page/framebuffer tag，无派生规则 | 编译期 |
| 6 | `#[ipc_handler]` 全契约检查 | 内核原地改写 cap_offsets[3] | handler 与 message struct 错配会破坏 CNode | 仅有属性名 | 编译期 |
| 7 | capability 生命周期/销毁安全 | 撤销对象、CNode 与映射需要无悬挂 cap | slot reuse 导致 UAF；revoke 无法定位后代 | 未记载撤销结构 | 编译期+运行期 |
| 8 | 栈深度编译期断言 | 229 KiB 最大帧已是现实风险[2] | 内核递归、中断或 IPC 破坏栈 | 仅通过链接器补偿 | 编译期 |
| 9 | `may_sleep`/`irq_ctx`/`preempt_disabled` 效果 | sleep、调度与中断返回由内核控制 | 持锁 sleep、中断中非法 sleep | 效果系统不存在[1] | 编译期 |
| 10 | `holds(L)`/`may_alloc` | 锁序与内存分配会影响 deadlock/reclaim | 分配器递归持锁；PF 路径 OOM | 无锁序/分配效果 | 编译期分析 |
| 11 | RCU/PerCpu 语言原语 | 读侧必须关联 grace period 与 CPU 上下文 | 延后释放被提前回收；PerCpu 指针跨 context 失效 | 原语不存在[1] | 运行期+编译期 token |
| 12 | 侵入式容器与 pin 保证 | 内核对象常驻链表/队列，不能移动 | 容器指针悬空；list_head 需重复 unsafe 包装 | 无 list_head/trait/移动模型 | 编译期 |
| 13 | BootState 线性 typestate | paging/heap/alloc/interrupt 有严格顺序 | 未映射页表时使用 global alloc，或未初始化 CPU 时开中断 | 无启动状态系统[1] | 编译期 |
| 14 | `#[naked]` 与 interrupt 栈契约 | D-GUI-12 使用 `#[naked]` interrupt[3] | 入口使用错误栈、Callee-saved 或 redzone | 有 `#[naked]`，规则不足 | 编译期契约 |
| 15 | wire 结构稳定 repr 与布局测试 | D41 禁止 packed，要求自然对齐+显式 `_pad`[1] | section 解析发生 padding 相关 UB | D41 已锁定 | 编译期布局测试 |
| 16 | `cap_offsets` bitmap/handler 签名元数据 | 防止 IPC stub 把普通字节当 cap | 内核按错误 offset 改写 CNode | 仅有 offsets 数组 | 编译期输出+运行期检查 |
| 17 | region 边界与生命周期 metadata | region_table 只有 base/size/flags[3] | 越界映射或共享对象过早释放 | 部分存在 | 编译期/运行期 |
| 18 | panic/oops/继续可达性分析 | 内核无 panic、无 unwind[1] | 无法区分可恢复错误与内核 fault | 未定义 | 编译期+运行期 |
| 19 | lock-order/IRQ-safe 全程序分析 | 锁是可组合内核惯用法 | 组合两个子系统即产生死锁 | 无 | 编译期分析 |
| 20 | WCET/时间预算元数据 | GUI、驱动与中断有响应要求 | 无上界可验证实时路径 | 无 | 编译期元数据 |
| 21 | provenance/version 语义 | amd64 无 CHERI，软件 slot 可伪造 | slot reuse 与跨进程误解释 | 仅有 padding/seed 线索 | 运行期+编译期 |
| 22 | `asm!` 的寄存器/栈/clobber 契约 | ABI 全 spill 且栈槽仅 8 字节对齐[2] | 汇编破坏 ABI 假设却无法静态发现 | 有 `asm!`，语义不足 | 编译期 |

**前四项优先级高到足以阻塞任何 GUI 或用户服务原型。** 若 `T` 与 rights 不进类型，cap_init 的 11 类对象无法映射到类型系统；若 `ptr<phys>` 不从 `Cap<frame>` 派生，region_table 的 raw_mmio 与 framebuffer 也不能形成授权链；若 handler 契约不检查，IPC dispatch 的原地 cap 改写会直接破坏 CSpace。这四项缺失时，即使 kernel.efi 能启动，也无法证明 user-space 不是靠巧合工作。

**第 8 项栈深度与第 14 项 interrupt 契约是 ABI 正确性的前提。** 229 KiB 单函数帧意味着若内核仍按“每个函数很少分配大对象”的直觉实现，最坏路径将未知。编译器不应只警告，而应输出 per-function 帧上界、per-call-edge 深度和 `#[naked]` 手工预算；链接器拒绝不能满足保留栈的 binary。若暂时无法全程序分析，至少要先禁止递归、动态调用与巨型栈帧进入 `#[naked]`/interrupt path。

## 十、`ptr<phys>` 从 `Cap<frame>` 派生的具体形态

**这是 JHYY 相对 Rust 最值得固化的结构优势，但必须先解决 `T` 解析。** Rust 中 `PhysAddr` 通常只是一个整数，或 `NonNull`/`*mut` 加上文档约定；地址可以在不持有 frame 对象的情况下被构造。JHYY 若把 `ptr<phys>` 的合法来源限定为 `Cap<frame>::map`/`borrow_phys`、`Cap<framebuffer>` 的显示适配或 `region_table` 经 loader 验证的 raw_mmio 条目，就能在类型层保留“为何能访问该物理范围”的授权证据。

建议的 API 形状不是把 `Cap<T>` 直接转型，而是显式消耗或借用 cap 的权限：

```jhyy
// 示意：不代表规范已锁定
fn frame_phys<'cap, 'map>(cap: &'cap Cap<Frame, W>, range: Range<usize>)
    -> Result<ptr<phys, W>, PhysError>
{ ... }

fn map_into<'cap>(space: &mut Cap<AddressSpace, W>,
                  frame: Cap<Frame, R|W>,
                  vaddr: ptr<kernel>, rights: VmRights)
    -> Cap<Mapping, R|W>
{ ... }
```

`frame_phys` 返回的内存引用必须由 frame cap 的 lifetime 与 rights 约束；`map_into` 返回一个新 mapping cap，而不是“成功返回 bool”。mapping 应有自己的对象身份，以便 unmap、revoke 与 frame 生命周期分离。这里有两个语义选择必须尽早决定，规范均未记载：其一，map 是否消耗 frame cap；其二，frame unmap 时是否等待所有映射消失。前者影响 API 表达，后者影响 revoke 与 TLB 协议。

**`ptr<io>` 必须进一步拆分，而不是把所有 MMIO 合并为 `ptr<phys>`。** 普通 RAM、write-combining framebuffer、device register、uncacheable control register的副作用与 ordering 不同。建议 `ptr<phys, Cache>` 与 `ptr<io, Device>` 至少分开；device 指针默认 volatile、不合并访问、不推测读。若 `ptr<phys>` 可从 frame cap 派生，而 `ptr<io>` 可从 capability 加 object 证明派生，则 region_table 的 raw_mmio 不应被普通 frame API 直接访问。

## 十一、`#[ipc_handler]` 应成为全程序契约，而不是属性宏语法糖

**`msg_tag` 唯一性必须在单个 `.jhyynb` 内静态证明。** 若两个 handler 声明相同 tag，loader 无法稳定选择目标；若允许重载，则 wire tag 不再是完整 dispatch key。编译器应检查同一 binary 中 tag 不冲突，或明确定义“service interface version + tag”的复合 key。跨版本兼容不能靠允许冲突实现，而应由 IPC version capability 和协商协议实现。

**handler 签名必须与 message struct 双向一致。** 对 trusted binary，编译器可以从 `#[ipc_handler(fn(msg: &Msg) -> Reply)` 反向生成 IPC dispatch 表，而不是让开发者手写 `msg_tag`、函数 offset 与 cap_offsets。对 C/汇编或外部 ABI，可允许显式声明，但必须生成可导出的 contract JSON/section 并做双向校验。由于 ABI 目前 sret 无条件生效、alignof(enum) 硬编码 4，且 SysV 分类器有隐患[2]，message struct 的 ABI 规则必须成为 IPC contract 的一部分。

**cap_offsets 校验至少分四层。**

1. 编译器确认每个 `cap_offsets[i]` 位于 message struct 中一个完整 `Cap<T>` 槽。
2. 编译器生成 cap slot 位图，证明无重叠、无越界。
3. 发送端在可信编译前提下维护 wire 布局。
4. 内核因消息来自不可信进程，必须重新检查 offset、slot 存在性、rights 与 type_tag allowlist。

因此“编译器保证 layout”不能替代“内核检查 offset”。真正可避免的是 trusted sender 的 handler 参数和 IPC stub 之间的不一致，而不是跨信任边界的验证成本。

## 十二、启动态、栈与故障降级：让“不能调用”成为类型错误

**BootState 应把不可逆启动步骤变成线性类型推进。** 建议至少包括 `NoAlloc → HeapReady`、`PagingOff → PagingOn`、`CpuLocalOff → CpuLocalReady`、`InterruptsOff → ThreadingReady`。每一步要求前一状态被消费或显式证明。例如 `kernel_alloc()` 要求 `HeapReady`，`map_kernel()` 要求 `PagingOn`，`schedule()` 要求线程系统就绪。规范当前没有该机制[1]，但这一需求比引入完整 trait 更基础；它可以先用封闭状态 enum 与一组 unsafe 构造函数实现。

**中断与锁效果不能依赖文档约定。** 至少需要 `irq_ctx`：当前代码是否处于中断上下文；`preempt_disabled`：是否能 reschedule；`holds(L)`：持有哪些锁；`may_sleep`：是否允许 blocking。效果系统不必在 v0.0.1 实现完整交集/并集算法，但必须覆盖高频误用：`sleep` 在 `irq_ctx` 或 `preempt_disabled` 中禁止；`spin_lock` 在已持有不兼容锁序时禁止；`alloc` 在 PF/allocator 路径中禁止。若语言无法表达，应在 `#[naked]`/interrupt 函数接口中至少要求显式 `unsafe` capability 参数。

**无栈展开不是“没有错误处理”，而是必须定义错误终止面。** 规范当前无 GC、无栈展开、无 panic[1]。内核至少区分三类事件：普通错误通过返回值传播；可恢复 fault 投递到 capability endpoint；不可恢复 fault 触发当前线程终止、namespace revoke 或 kernel oops。必须明确“oops 之后能否继续运行”。若继续运行，哪些全局状态需要 quiesce；若不能，哪些子系统可以独立重启。没有这一层，无 panic 会退化为无限循环、双重 fault 或静默内存破坏。

## 十三、外部对标：值得抄的是能力/TCB 边界，不是具体 C 结构

**seL4 证明能力模型的价值，也证明验证成本不可轻视。** seL4 的 CSpace、CNode 与 capability 派生关系说明 JHYY 选的不是冷门模型；其实现级正确性、安全属性证明与二进制验证则显示，小内核在有限 TCB 下可做到工业级可信[7][8]。但南京大学材料把 seL4 证明工作量记录为 11+ 人年[8]。对单人/小团队，这不是“先写形式证明”，而是先把可验证的接口边界、对象不变式、撤销语义与测试 oracle 设计成可审查形式。seL4 用 C 写能力系统暴露的痛点主要是状态全局性、指针别名、宏与 unsafe cast 难以机械化；JHYY 不应把这些问题复制到 `Cap<i32>` + 手工 CNode 编码中。

**Rust for Linux 说明安全语言进入既有内核的最大阻力是惯用法边界，而不是语法。** 近期进展包括 2025 年维护者峰会认可 Rust 不再只是实验，已有生产驱动及超过 2 万行 Rust 代码[11]；但 DMA API 抽象、C/Rust 代码所有权与维护边界仍引发强烈冲突[12]。这说明 jhyy_OS 若能一开始就拥有统一语言，会避免 Rust-for-Linux 最大的一部分组织成本；但 Linux 的侵入式 list、RCU、设备引用与复杂锁序也会在 JHYY 中重现。Rust 并不能让“对象在多个链表、生命周期由 RCU grace period 管理”自然成为单所有权模型。JHYY 应直接设计侵入式容器与 RCU token，而不是先复制 Rust `Box/Arc` 再补 `ListLinks`。

**Asterinas 的 framekernel 是比 Redox 更值得借鉴的边界模型。** Redox 是完整的 Rust 微内核操作系统，但其与 JHYY 最相关的部分仍是能力/IPC/服务拆分。Asterinas 公开材料称其将内核分为特权 OS 框架与去特权 OS 服务，前者把非安全 Rust 封装成安全 API，后者主要使用安全 Rust；这一架构的目标是缩小内存安全 TCB[13]。JHYY 应抄的是“把 unsafe 内核原语压缩到可审计边界”，而不是抄具体 Rust crate。JHYY 还应更彻底：以 capability 作为进入 OS 框架的唯一授权，而不是以模块/命名空间可见性替代授权。

**Theseus 类“语言化状态隔离”值得借鉴，但无法从现有检索可靠复现。** 由于搜索结果把同名 OS 项目与另一篇芯片论文混淆，本报告不引用未经核实的项目细节。可成立的通用结论是：语言能表达模块/状态边界，却不能替内核决定设备 quiesce、抢占和故障恢复。JHYY 应把 Theseus 式想法限定在“服务状态由类型与 capability 边界隔离”，不把它当作减少运行时机制的依据。

**Zig 值得抄的是显式控制流，不是“少做类型系统”。** 公开资料普遍把显式分配器、无隐藏控制流、comptime 与错误类型视为 Zig 的核心系统编程特性[14]。对 JHYY，这支持三条决定：函数签名显式体现 allocator 或 `may_alloc`；编译期计算 capability layout、section header 与 IPC stub；错误通过值返回并强制处理。不应照搬的是把大量属性推迟到运行期 assert。Zig 的可读性来自显式约定，JHYY 的安全来自把显式约定提升到类型与 contract。

**CHERI 与类型系统结合是长期方向，不应进入 amd64 的 v0.0.1 承诺。** Morello 的强封装证明与 CHERI 的不可伪造能力目标[9][10]说明，硬件能力能补上软件能力的 provenance 与空间边界缺口。但在 amd64 上没有该硬件时，JHYY 的能力上限是“内核对象存在、授权单调、映射可撤销、跨域调用受控”，不是“所有指针访问硬件可验证”。因此不要承诺 CHERI 兼容 ABI，也不要用 CHERI 论文为当前软件能力模型背书。

| 外部项目 | 已核实结论 | 对 JHYY 的建议 | 不应抄的部分 |
|---|---|---|---|
| seL4 | CSpace/能力模型、工业级验证先例 | 先冻结对象、CSpace、revoke 语义 | 复制 C 风格的全局状态与宏 |
| Rust for Linux | 安全抽象逐步进入既有内核 | 从一开始统一 unsafe 内核边界 | 把已有 Linux 惯用法当天然正确 |
| Asterinas | TCB 分层、safe service/framework 分层 | capability 成为进入 OS 框架的入口 | 只以 safe/unsafe 替代授权 |
| Redox | Rust 微内核工程实践 | 借鉴服务化与 IPC 测试 | 未经验证的具体服务结构 |
| Zig | 显式 alloc、comptime、错误值 | 让 alloc/sleep/irq 显式进入签名 | 放弃静态类型与布局证明 |
| CHERI/Morello | 硬件能力、强封装研究 | 预留 provenance 与版本扩展位 | 声称 amd64 已实现硬件能力 |

## 十四、推荐的最小实现顺序

**第一阶段只做“可信加载器能看懂、内核能强制执行”的最小格式。** 先冻结 `.jhyynb` 的 cap_init/region_table/IPC dispatch 静态表，为 `Cap<T>` 增加真实 T，为 rights 增加编译期参数。即便能力对象只有 endpoint、frame/page、address space 与 mapping 四类，也应足以验证 boot、loader、最小 IPC、frame 映射、user-space termination 与 revoke stub。GUI 对象先定义 buffer/surface/compositor/seat 的 layout，不实现完整 compositor。

**第二阶段把语言效果集中到五个最高危错误。** 按排序先实现 `Cap<T,Rights>`、`ptr<phys>` 从 frame cap 派生、`#[ipc_handler]` 契约、栈预算、irq/preempt/alloc 状态。侵入式容器、RCU、复杂锁序与 WCET 可以在 unsafe API 上先做，但不能永久停留在“开发者记得规则”。

**第三阶段才引入用户态驱动与完整 GUI。** 在第二阶段证明 type_tag、rights、handler、栈与启动态之后，file/shm/framebuffer/compositor/surface/seat/buffer 才能真正形成 capability 图形栈。这样每一次扩展都是给已有对象模型增加 type_tag 与 API，而不是重新设计授权机制。

**验证目标应按 TCB 分层，而不是一开始追求 seL4 级全证明。** 最低层用模型检查或属性测试验证 CNode 派生、rights 收缩、revoke 与 slot reuse；中层对 IPC stub 与 region metadata 做布局差分测试；上层对服务协议做 fuzz。待对象模型稳定后，再选择关键不变量进行机械化证明。seL4 的工程代价说明，验证对象边界必须先于验证实现细节[8]。

## 十五、规范未记载，待确认

**下列资料必须来自真实仓库、coordination.md、D-lock 全文或 v0.0.1-capability.md；本报告无法用三份规范补出。**

| 待确认项 | 已知线索 | 会阻塞的结论 |
|---|---|---|
| 真实 jhyy_OS 调度模型 | 规范没有线程、runqueue、时间片、优先级或 SMP 事实 | 能否确定内核是单核先跑、Tier 0 对象及 `#[ipc_handler]` 的抢占语义 |
| 中断与 trap 模型 | D-GUI-12 只提到 `#[naked] interrupt`[3] | interrupt entry 的栈、Callee-saved、redzone、IRQ 线程化与嵌套规则 |
| 内存管理模型 | 只有 region_table 与 frame/page/framebuffer tag | frame metadata、allocator、slab、page table、ASID/PCID、page fault handler 的位置 |
| CSpace 与 CNode 实际结构 | 只有 wire 的 cnode_idx/depth | slot version、CNode 增长、跨 CNode 解析与内核对象 header |
| CDT/撤销树 | 只有 depth 字段 | revoke 是否同步、是否支持 in-progress、反向边、RCU grace 与映射 unmap |
| D-lock 全集 | 仅知 D23、D40、D41、D-GUI-12、5 原则 | 哪些能力已锁定、哪些仍可变、与新增类型/效果系统是否冲突 |
| v0.0.1 capability 对象表 | 仅知道 11 个 type_tag 值 | page/frame/framebuffer/page 的语义区分、是否增加 kernel-internal 对象 |
| capability 版本与 provenance | cap_init 有 provenance_seed_off[3]，无规则 | slot reuse、派生 proof、跨进程与持久化是否安全 |
| region_table 的 owner/生命周期 | 只有 kind、rights、flags | kernel_shared/unsafe_share/cap_namespace 的引用与 revoke 语义 |
| 内核栈策略 | 只有用户态编译器 229 KiB 最大帧[2] | 内核栈大小、per-CPU 备份栈、中断栈、递归深度与栈溢出处理 |
| M3 message struct 与 cap policy | 只有 IPC dispatch 表与 D16 wire[3] | handler 版本、timeout、cap grant/return、in-flight 消息所有权 |
| panic/fault 模型 | 规范无 panic/unwind[1] | oops 分类、thread terminate、namespace revoke、是否支持 kernel continuation |
| GUI 完整对象模型 | 只有 compositor/surface/seat/buffer/focus 等 tag | 显示 lease、format/modifier、transaction、presentation feedback、input focus |
| boot/hardware 适配范围 | 只知 PE/COFF kernel.efi 与 UEFI 钩子空实现 | 第一版支持哪些主板、APIC、定时器、串口/显卡与 SMP 步骤 |
| `.jhyynb` 加载与签名语义 | 只有 section 格式 | 是否需要签名/测量、加载顺序、未知 section 处理、contract 是否强制 |
| 编译器 roadmap 与兼容性 | 只知四 ABI 目标与 14 条已知偏离[2] | `T` 重新解析是否会破坏 ABI、版本迁移与旧 binary 共存 |

## 十六、最终判断

**jhyy_OS 的内核身份应明确锁定为能力微内核，但首版物理结构采用特权分层。** 三份规范已经提供对象分类、cap 授权、IPC 原地 cap 传输、区域声明与 4 KiB 对齐的足够线索，继续选择传统混合内核只会让这些设计失去语义承担。首版保留物理内存、platform、根任务与最低中断逻辑在特权区，可以显著降低从 Windows 寄生到裸金属的开发风险。

**能力模型的最小正确性条件比 GUI 对象数量更重要。** depth 只解决派生层级，不能单独解决 revoke；padding 只提供未来空间，不能单独解决 slot reuse；cap_init 只声明初始对象，不能单独解决生命周期；handler 属性只标记入口，不能单独保证 message/offset 一致。版本化 CNode、rights 单调收缩、capability 生命周期、栈预算与 `#[ipc_handler]` 全契约必须在大规模 service 前冻结。

**JHYY 的最大结构性机会是让授权从 wire 进入类型。** `Cap<T,Rights>`、`ptr<phys>` 从 `Cap<frame>` 派生、region 与启动态 typestate 共同构成了 Rust/C 难以低成本补回的边界。代价是语言必须接受 unsafe 内核原语，并承认 CHERI 缺失下软件能力不能达到硬件 provenance 的强度。

**第 5 原则应被改写为“内核不实现语言，但为语言提供可证明使用的运行时契约”。** 这条边界既避免内核承担类型推导，也避免语言把全局硬件状态假装成纯函数。以此为准，`.jhyynb` 的 cap_init/ipc_dispatch/region_table 负责事实声明，新增 contract section 负责控制流与资源不变量，kernel.efi 负责 authority 真源与全局状态。三者一致时，JHYY 才不只是“用自研语言写 OS”，而是拥有从 wire 到类型、从类型到 capability、从 capability 到对象生命周期的统一执行模型。

## 引用来源

[1] ../abis/jhyy-lang-spec-v4.0.0.md
> `Cap<T>` 是内建类型，8 字节 wire：`{cnode_idx:u32@0, depth:u8@4, rights:u16@5, padding:u8@7}`；rights bit0=R bit1=W bit2=G。

[2] ../abis/jhyy-abi-v4.0.0.md
> 自举编译器最大单函数帧 234080 B，靠 `-Wl,--stack,67108864` 补偿；栈槽只保证 8 字节对齐。
>
> ⚠️ **2026-10-30 更正**:此数字取自 v4.2.1 **之前**的产物。v4.2.1(2026-10-29)把帧
> 公式从写死的 `8192 + per_fn_alloc` 改成按函数实际需要算 ⇒ **中位帧 8368 → 288 字节**
> (1045 个函数里 chkstk 调用 1045 → 46),但 **max 帧 237680 → 349232 B(反而变大,
> 因为旧公式在公式池主导时把 `per_fn_alloc` 丢掉了)**。⇒ 「229 KiB 最大帧」这个
> 基线**已经过时**,P2 的验收目标要按 341 KiB 重算,且**降帧的真正杠杆是寄存器分配
> (v4.4 阶段二)而不是再调公式**。数据见 `docs/plans/v4/self-backend-perf-plan.md` § 三之二。

[3] ../abis/jhyy-binary-format-v1.0.0.md
> `.jhyynb` 的 cap_init、ipc_dispatch、region_table 分别承载能力初始化、IPC handler 与区域声明语义。

[4] https://news.qq.com/rain/a/LNK2025122006432400
> Linux 内核首个 Rust 代码 CVE 源于链表中并发移除导致的 prev/next 损坏。

[5] https://news.qq.com/rain/a/20250208A03OLY00
> Linux DMA API 的 Rust 抽象与既有 C 维护边界发生冲突，显示多语言内核的惯用法摩擦。

[6] https://finance.sina.com.cn/tech/digi/2026-02-09/doc-inhmfqci6266338.shtml
> Rust for Linux 进入长期支持阶段，相关抽象已进入生产内核代码。

[7] https://new.qq.com/rain/a/20230509A05H7600
> seL4 获得 2022 ACM 软件系统奖，表彰其工业强度、性能与机器检查证明。

[8] https://cs.nju.edu.cn/yuanyao/static/osdi2026.pdf
> seL4 实现在 Isabelle/HOL 中证明其函数正确性，并将证明扩展到机密性、完整性及二进制层。

[9] https://shz.nstl.gov.cn/paper_detail.html?id=598dd4c8f348e33db5e2ab37dd894a43
> Morello-Cerise 对 Arm Morello 的强封装性进行机械化证明。

[10] https://finance.sina.com.cn/tech/2022-01-21/doc-ikyakumy1717286.shtml
> Morello 原型板开始供合作伙伴测试，CHERI 提供硬件细粒度空间内存保护。

[11] https://news.qq.com/rain/a/20251215A06E9900
> 2025 年 Linux Kernel Maintainers Summit 后，Rust 结束实验期并成为长期组成部分。

[12] https://news.qq.com/rain/a/20250208A046QB00
> Rust 驱动调用 C DMA API 的补丁遭维护者反对，显示跨语言接口维护边界仍是阻力。

[13] https://news.qq.com/rain/a/20241022A09SYA00
> Asterinas 将内核分为特权 OS 框架与去特权 OS 服务，以缩小内存安全 TCB。

[14] https://news.qq.com/rain/a/20230714A088TD00
> Zig 要求显式分配器参数，并以错误值代替异常，避免隐藏控制流与隐式分配。

[15] https://www.docin.com/p-1924445485.html
> 北航 XServices 简介页面提及 seL4 约 8700 行 C 代码及形式化验证工作量。

[16] https://www.sohu.com/a/271144873_100204297
> 形式化验证 seL4 时共发现 460 多个 Bug，测试只发现 16 个 Bug。

[17] https://www.sohu.com/a/518132988_119709
> Arm 发布集成 CHERI 的 Morello SoC 原型，用于评估硬件增强设备安全性。

[18] https://m.thepaper.cn/baijiahao_19666964
> Morello 使用 128 位能力寄存器与元数据标签，使能力不可伪造。