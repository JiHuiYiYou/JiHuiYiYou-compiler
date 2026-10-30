# JHYY 编译器全阶段方向与路线图

## 摘要

JHYY 编译器不应先成为一个“更完整的语言”，而应成为一个能证明内核安全不变量、并把这些证明写入可执行对象的**能力程序验证与代码生成器**。按 OS 需求清单的失效严重性，最需要优先关闭的不是泛型表达力，而是实参类型检查、唯一输出路径、可重复编译、布尔/初始化语义、最小 freestanding 反馈环，以及 `Cap<T,Rights>`、`ptr<phys>` 派生、IPC handler、栈深度、irq/preempt/alloc 效果和锁序分析。本文建议将 P1 上提到“完成 P0 基础语义止血后立即执行”，因为它决定后续所有内核接口是否真的被硬件和加载器执行；同时建议把 P3 的块表达式与 `fn` 类型位置前移，因为它们是 BootState 线性 typestate 与热路径内联的前置条件。P4 的 `Cap<T>` 真实类型化则应保留在 capability 对象模型最小冻结后实施，而不是先于“对象类型—权限—生命周期”语义确定。寄存器分配的正确顺序是先建立可重复的栈帧测量和编译期断言，再做线性扫描，最后才讨论图着色；229 KiB 单函数帧必须把“最大本地需求 + 被调者最坏路径”分开测量，并以 `max_frame ≤ 16 KiB`、`max_call_depth × max_frame + redzone ≤ stack_reservation` 等硬门槛验收。

## 一、设计总纲：JHYY 的价值是“把更多 OS 不变量变成编译不过”

**编译器应成为能力内核 TCB 的一部分，而不是与 OS 并列的工具。** 上游 OS 报告已锁定：`.jhyynb` 的 cap_init、ipc_dispatch、region_table 分别声明初始能力、IPC 入口和区域；`Cap<T>` 的 8 字节 wire 已包含 cnode_idx、depth、rights，而当前 `T` 却不解析，所有 `Cap<T>` 被视为同一类型[1]。这说明格式已经在记录授权事实，语言却没有让这些事实参与类型检查。后续编译器的核心职责因此应当统一为：把源码中的授权、资源、控制流与 ABI 事实转换成 IL 的机器检查属性，最终以对象代码和 `.jhyynb` 契约交付；运行期只负责无法静态知道的对象存在、并发、硬件状态和跨信任边界输入。

**编译器的首要产品不只是 `.s` 或 `.o`，而是“可执行对象 + 可验证契约”。** 现有流水线从 lexer 经 parser、sema、进程内 IL，进入自托管 amd64 后端，再经 GAS 与 ld 生成二进制[2]。这意味着目标文件是最终产物，却不是唯一的合理产物。栈上界、锁序、cap 类型、效果、ABI 布局与 panic 可达性都应成为辅助输出：可直接生成 JSON/Protobuf 供 IDE、CI 和静态分析消费，再按固定 schema 选择性写入 `.jhyynb` 的契约 section。Linux BPF 的 BTF 是先例：Clang 把类型和重定位事实输出到 `.btf`/`.btf.ext`，加载器据此做 CO-RE，而不是依赖每个程序手工匹配内核结构[12]；Google Kythe 则说明，编译器生成的声明、引用、定义和调用事实可以成为跨工具的语言无关交换层[13]。

**“JHYY 比 Rust/C 更有优势”只有在类型和授权链真正相连时才成立。** 上游报告建议 `ptr<phys>` 必须从 `Cap<frame>` 派生，而不是由整数转换而来[1]。这是一条高价值结构性约束：`Cap<Frame>` 证明调用者持有物理页授权，`ptr<phys>` 只是该授权在当前函数中的使用证据。Rust 中常见做法仍是 `PhysAddr` 或裸指针加文档约定，授权来源并不总在类型里。JHYY 若能让“能映射”“能解引用”“能 DMA”各自成为 cap rights 的证明，就会形成 Rust 不能零成本补回的边界。反之，如果 `Cap<T>` 仍只有 8 字节且 `T` 不解析，新增语法只是装饰。

## 二、一等公民模型：能被推理、拒绝非法组合，且不依赖注释

**一等公民不是“语法漂亮”，而是“编译器无需阅读注释即可完成推理”。** 建议采用六项可操作测试：

1. **参数化测试**：它能否作为类型参数、const 参数或属性参数出现，而不被编译器擦除？
2. **类型检查测试**：它是否参与类型等价、子类型/子集关系，并阻止不合法组合？
3. **推导测试**：不写注释时，编译器能否从合法来源推导，而不从注释或字符串名猜测？
4. **拒绝测试**：非法组合是否必然报错，而不是延迟到运行时或生成未定义行为？
5. **传递测试**：它能否跨越函数签名、IL、后端与二进制契约保持同一语义？
6. **事实输出测试**：它能否输出可被 loader/kernel 或外部工具独立验证的机器可读事实？

| 候选对象 | 参数化 | 类型检查 | 推导 | 拒绝非法 | 跨阶段传递 | 事实输出 | 结论 |
|---|---:|---:|---:|---:|---:|---:|---|
| `Cap<T>` | 已能写参数 | 当前 `T` 擦除 | 应从 wire/type_tag 推导 | 必须拒绝越权派生 | 需进 IL/ABI | 是 | **一等** |
| rights 集合 | 可作为 const/phantom | 可做子集检查 | 可从源 cap 推导 | 禁止增权 | 需进 wire/contract | 是 | **一等** |
| `ptr<space>` | 可作为类型参数 | 必须检查解引用上下文 | 可从 `Cap<frame>` 派生 | 禁止整数转物理指针 | 需进 IL/codegen | 部分 | **一等** |
| boot state | 可作为类型参数 | 必须检查状态迁移 | 可从 init API 推导 | 禁止倒退/跳步 | 需进 IL | 可选 | **一等，但封闭状态** |
| 错误类型 | 可作为普通类型 | 已有基本类型能力 | 可推导 `Result` 分支 | 不做运行时 panic 即报告可达性 | 可进 IL | 是 | **普通一等类型** |
| 效果 `may_sleep` 等 | 可作为签名注解 | 必须检查传播/禁止点 | 可局部推断 | 禁止 irq/preempt 上下文睡眠 | 进 IL/contract | 是 | **一等，但属 effect row** |
| `holds(L)` | 可作为能力参数 | 必须检查偏序 | 可从 acquire/release 推导 | 禁止反向/乱序 | 进 IL/contract | 是 | **一等 effect 参数** |
| layout | 可附类型/属性 | 可算 size/align/hash | 可从字段推导 | 拒绝未定义布局组合 | 进 ABI facts | 是 | **一等 metadata** |
| ABI 契约 | 不宜作为运行时类型参数 | 可检查调用者/被调者 | 可从签名和属性推导 | 拒绝不匹配 sret/寄存器类 | 进 asm/object/facts | 是 | **一等编译对象，不是类型** |
| region | 可作为对象类型与参数 | 需对象 header | 可从 region_table 推导 | 禁止越界/非法 owner | 需进 cap/region section | 是 | **运行时一等 + 类型轻量索引** |
| WCET 上界 | 可作为 const/属性 | 只能做算术和单调性检查 | 不宜自动推断 | 缺失/循环无界时报错 | 进 contract | 是 | **二等：分析结论，不是类型** |
| panic 可达性 | 可作为 enum/标签 | 可检查分类 | 可做控制流传播 | 无统一终止面时报错 | 进 contract | 是 | **二等事实** |
| BootPhase 枚举值 | 可作为普通类型 | 可穷尽匹配 | 不生成授权 | 仅靠穷尽无法防误用 | 无 ABI 必要 | 否 | **普通类型即可** |
| ABI class `m` | 应只是 IR/后端分类 | 不应成为语言类型 | 从语言类型映射 | 仅阻止非法 lowering | 进 ABI facts | 是 | **实现类型，不是语言一等** |

**能力、地址空间和效果必须一等，因为它们会进入 wire 和内核决策。** `Cap<T,Rights>` 的 `T` 将决定允许调用的内核对象方法，rights 会写入 8 字节 wire，`ptr<phys>` 的合法来源决定物理内存访问是否越权；三者都直接对应静默越权。boot state、错误、layout、ABI 契约与锁持有集也值得进入编译模型，但承担不同角色：前两者是普通类型，layout 是生成期事实，ABI 是编译器内部契约，锁持有集是函数效果参数。把它们混称为“类型”会模糊检查时机。

**效果系统应成为“受限制的能力类型系统”，而不是通用代数效应。** 通用代数效应追求 handler 可组合、可恢复与自由效应代数，会增加 CPS、异步表示、effect handler 与较多单态化；JHYY 现阶段只需拒绝五种高危组合：`may_sleep`、`irq_ctx`、`preempt_disabled`、`holds(L)`、`may_alloc`。Koka 的先例表明，行类型可以携带和推断效果，并把选择性 CPS 转换推迟到真正需要 handler 的位置[11]，但 JHYY 不应照搬完整行类型机制，而只做闭合效果格的单调传播与禁止规则。Rust 的 `Send/Sync` 也说明，稳定而可自动派生的标记可以让大多数代码不写注解，只有 unsafe 边界显式说明[9][10]。

**下列对象不应成为通用一等类型，以免编译时间和体积失控。** 第一，WCET 上界不应参与完整泛型单态化；它只能是函数属性、常量上限和单调运算。第二，锁名称不应全部泛化为依赖类型 `Lock<order>`，否则锁比较和调用签名会迅速膨胀；应允许显式 `lock_class!` 编号，再由 lockdep pass 使用。第三，region 生命周期不应复制为完整线性类型，因为内核对象常跨线程、RCU 和引用计数；语言只持 token，真销毁由内核负责。第四，运行时 ABI 细节不应暴露为语言类型；应提供 `#[repr]`/layout 查询与契约属性。第五，panic category 应是有限枚举或独立控制流事实，而不是每层函数签名都必须写的类型参数。

**最终总纲是“三个层级、一条事实链”。** 语言层只有 capability、address space、rights、state token、error 和普通类型；effect row 是函数签名的附属证明；layout、ABI、栈、锁序、WCET、panic 与 cap_offsets 是分析生成的 facts。facts 从 AST/sema 开始附 source span，在 IL 中保留，在 codegen 中约束 sret、寄存器类、naked stack 与 clobber，在链接期做全程序断言，在 `.jhyynb` 中成为内核可验证契约。任何“不变量”至少要落在三个层级之一，否则不得进入语言规范。

## 三、整体分期：P0 先止血，P1 早建反馈环，P3/P4 重构要并行

**现有 14 条已知 ABI 偏离说明，先修补自托管编译器的确定性比追求新语言特性更紧迫。** ABI 规范记录：当前四个 amd64 目标均自托管；全 spill 仅保存 RBP；自举编译器最大单函数帧 234080 B，靠 `-Wl,--stack,67108864` 补偿；两个旁路池合并只能消灭一类重叠；栈槽对齐无 4 字节下限；SysV eightbyte、MEMORY 与寄存器溢出参数混排、sret 预算等问题仍存在；`_inline_asm.buf` 等固定路径会令并发编译互扰；链接分支由源文件是否 `#[no_std]` 决定；UEFI 的两个 entry 钩子仍是空实现[2]。这些都是“能编译、能自举，但组合后不可信”的典型。

**P0 的目标是让自托管本身成为可重复实验。** 必须依次完成：实参类型检查、extern fn 的形状限制、多余输入文件报错、唯一临时旁路文件、布尔归一化、顶层非整数变量初始化、八进制/数字字面量规则，以及先十行复现再修的 `&&`/`||` 与 u8 codegen 缺陷。此时不应追求完整类型推断，只追求“坏程序不再静默通过”。

**P1 应在 P0 后能编译出最小 freestanding 镜像，但允许镜像只做 UEFI 文本输出后停机。** 上游担心 trivial 程序仍可能撞上 229 KiB；正确的反证是建立帧上界测量：trivial program 的函数与调用深度通常远小于自举编译器。先跑通 entry 钩子、移除无条件 Windows 库、增加 UTF-8 控制台输出，再用 8 KiB 或 16 KiB 栈做链接断言。若 trivial image 实际超限，说明测量比 freestanding 本身更早成为阻塞项，应临时禁止递归与动态调用，而不是悄悄加栈。

**P2 应把“知道最坏栈”放在“用好寄存器”之前。** 先记录每个 IL 函数的本地槽、地址池、调用边与 callee 最坏深度，输出 per-function CSV/JSON；链接器拒绝最大调用链超过线程栈保留量的对象。测量稳定后，再实现线性扫描寄存器分配。线性扫描足以利用当前 IL 的顺序生命期，并显著减少全 spill；图着色只在前端热路径经基准证明尚有 >=5% 访存收益时引入。这样能避免“分配器更快但栈仍不可知”的局部优化。

**P3 不是语法美化，而是 P4 与内核 API 的语义基础。** 块表达式使 boot state 成为一组带顺序的语句；`fn` 类型位置使函数指针、IPC stub 和中断回调能写成普通参数；闭包捕获使 small helper 能保留上下文；`()` 类型位置则消除当前“函数指针无类型、闭包不能捕获、函数体末表达式返回不触发 defer”的断裂。它们与 P4 有依赖，但实现风险和回归范围比 capability 语义小，适合作为 P4 前的编译器架构练习。

**P4 必须在对象模型冻结后实施。** `Cap<T>` 真实 T、rights 参数化、`ptr<phys>` 派生、`#[ipc_handler]` 全契约和 `.jhyynb` 实装共同决定二进制兼容性。若先实装类型语法、后改变对象生命周期或 wire 权限位，会产生两次迁移。验收方式不是“语法能写”，而是用一个最小内核完成 cap init、frame 映射、IPC、栈/锁/效果全检查，并让一个能力不足的程序无法编译。

## 四、前端语法与 OS 需求对应

### 4.1 `Cap<T, Rights>`：把 wire 权限变成可证明的子集

```jhyy
type Read   = #cap_r;
type Write  = #cap_w;
type Grant  = #cap_g;
type Rw     = #cap_r | #cap_w;
type All    = #cap_r | #cap_w | #cap_g;

fn derive_frame(src: &Cap<Frame, All>, new_rights: Rights)
    -> Option<Cap<Frame, new_rights>>
    where new_rights <= src.rights
{
    syscall_derive(src, new_rights)
}

fn map_frame(frame: Cap<Frame, Rw>,
             space: &mut Cap<AddressSpace, Write>)
    -> Result<Cap<Mapping, Write>, KernelError>
{
    /* ... */
}
```

**rights 应使用编译期位集，而不是字符串枚举。** `#cap_r|#cap_w` 表示一个 const row；`where R2 <= R1` 表示新权限是旧权限的子集。`<=` 不能由普通运行时比较实现，否则权限检查会延迟到 syscall。Sema 把 rights 视为无符号常量集合，计算交集、并集和下传；函数形参的 rights 参数在进入 syscall 边界后仍需内核验证，因为攻击者可以伪造用户态调用参数。编译期证明拒绝“来源没有 W 却声称有 W”，不能证明“用户没有篡改 syscall 参数”。

**错误码与报错必须指出迁移路径，而不是只说“不匹配”。**

```text
E0421: capability rights 不是前驱的子集
  --> kernel/src/frame.jhyy:42:12
   |
42 |     let rw = derive_ro_as_rw(ro_cap);
   |            ^^^^^^^^^^^^^^^^^^^^^^^^
   |
   = 源权限：{#cap_r}
   = 目标权限：{#cap_r, #cap_w}
   = 建议：使用 `derive(frame, rights & #cap_r)`，或要求源 cap 至少包含 #cap_w
```

```text
E0422: capability 对象类型不匹配
  --> kernel/src/ipc.jhyy:88:20
   |
88 |     send_cap::<Frame>(ep, cap);
   |                    ^^^^^ 期望 Cap<Endpoint, _>
   |
   = 实参类型：Cap<Frame, {#cap_r}>
   = 建议：该接口要求 type_tag 兼容 Endpoint；Frame cap 不可作为 endpoint 能力传输
```

### 4.2 `ptr<phys>`：授权必须先于地址

```jhyy
fn frame_ptr<'f, R>(cap: &'f Cap<Frame, R>, range: Range<usize>)
    -> Result<ptr<'f, phys, R>, PhysError>
    where R: Contains<#cap_r>
{
    require(range.end <= frame_size(cap));
    unsafe { Ok(transmute_borrow(cap, range.start)) }
}

fn dma_buffer(cap: &Cap<Frame, Read|Write>, offset: usize) -> ptr<phys, Read|Write> {
    /* 只能从 frame cap 派生；不能由 usize 构造 */
}
```

**`ptr<phys>` 的构造必须只有三类可信来源。** 一是 `Cap<Frame>` 的借用映射；二是 `Cap<Framebuffer>` 显式适配；三是 loader 验证过的 `region_table` raw_mmio 条目。构造函数必须接受原 cap 的借用或显式 lifetime，并产出相同或更小 rights。整数、`*mut u8` 和 `ptr<kernel>` 不得隐式转为 `ptr<phys>`。device MMIO 还应与可缓存 RAM 分离：`ptr<phys, Cache>` 默认可缓存，`ptr<io, Device>` 默认 volatile、不合并访问、不推测读取。

```text
E0431: 非法构造物理地址指针
  --> kernel/src/mm.jhyy:15:9
   |
15 |     let p = ptr<phys>(0xdeadbeef as usize);
   |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   |
   = ptr<phys> 必须由 Cap<Frame>、Cap<Framebuffer> 或已验证 region 派生
   = 建议：使用 `frame_ptr(&cap, range)`，并让生命周期与 cap 借用绑定
```

```text
E0432: 物理指针的权限超出其来源能力
  --> kernel/src/mm.jhyy:30:20
   |
30 |     let w = frame_ptr(&ro_frame, 0..4096);
   |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   |
   = `frame_ptr` 要求来源至少包含 #cap_r
   = 建议：将签名限制为 `where R: Contains<#cap_r>`，或派生只读 cap
```

### 4.3 效果系统：用签名拒绝上下文误用

```jhyy
fn schedule() with {};

fn wait_event() -> Event
    with { may_sleep };

fn spin_acquire(lock: &Lock) -> Guard<'_>
    with { preempt_disabled, irq_ctx? = any };

fn slab_alloc(sz: usize) -> *mut u8
    with { may_alloc };

fn handle_page_fault(ctx: &mut TrapCtx)
    with { irq_ctx = handler, preempt_disabled }
{
    let _g = page_table_lock.acquire(); // E0510: 可能 sleep/alloc 的路径
}
```

**效果采用“声明的上限 + 调用点自动收窄 + 禁止点”三段式。** 每个函数签名可写 `with { ... }`；缺省时 Sema 从函数体自底向上计算效果格上确界。调用时，被调者的效果必须是当前允许效果的子集；进入 `irq_ctx`、持锁或 `preempt_disabled` 后，调用点只能允许 `may_sleep = false`、`may_alloc = false`。锁效果不是锁名字的无限集合，而是 `(lock_class, direction, option<order_index>)` 的有限事实；普通锁只检查有序对，读/写锁才进入强依赖规则。

```text
E0510: 在禁止睡眠的上下文中调用可能睡眠的函数
  --> kernel/src/fault.jhyy:60:13
   |
60 |         wait_event();
   |         ^^^^^^^^^^^
   |
   = 当前上下文：irq_ctx = handler, preempt_disabled
   = 被调函数声明：{ may_sleep }
   = 建议：把等待移到可睡眠上下文，或使用非阻塞 try 路径
```

```text
E0511: 锁序违反已验证的偏序
  --> kernel/src/vfs.jhyy:102:9
   |
102 |     acquire(&lock_b);
    |     ^^^^^^^^^^^^^^^
    |
    = 已有持有集：{ lock_class=7(A), order_index=0 }
    = 新加锁边：A(7) -> B(9)
    = 全程序已存在强路径：B(9) -> ... -> A(7)
    = 建议：统一按 LOCK_ORDER 声明，或将 A/B 改为同层嵌套锁
```

### 4.4 BootState：用状态 token 表达不可倒退的启动顺序

```jhyy
struct BootState<Stage> { _token: PhantomData<Stage> }

struct NoAlloc; struct HeapReady;
struct PagingOff; struct PagingOn;
struct CpuLocalOff; struct CpuLocalReady;
struct InterruptsOff; struct ThreadingReady;

fn enable_paging(s: BootState<PagingOff>) -> BootState<PagingOn> { ... }
fn init_heap(s: BootState<PagingOn>) -> BootState<HeapReady> { ... }
fn start_threading(s: BootState<InterruptsOff>) -> BootState<ThreadingReady> { ... }

fn kernel_main() -> ! {
    let s0 = BootState::<PagingOff> { _token: PhantomData };
    let s1 = enable_paging(s0);
    let s2 = init_heap(s1); // 若传 s0 则编译失败
    enter_kernel(s2)
}
```

**状态迁移必须消费旧 token。** `enable_paging(s)` 的 `s` 按值取得，旧状态不能复用；返回值创建新状态。这样既不需要完整 trait，也不需要借用检查器理解硬件。接口仍可标 `#[unsafe]` 并写明“调用者证明当前 CPU/页表状态”，但状态类型让误调用从文档升级为类型错误。状态的 number 可用普通泛型参数或新类型实现，P3 有块表达式后再允许临时状态作用域。

```text
E0610: 启动状态顺序错误
  --> kernel/src/init.jhyy:74:19
   |
74 |     let heap = init_heap(s0);
   |                   ^^^^^^^^ 期望 BootState<PagingOn>
   |
   = 实参：BootState<PagingOff>
   = 要求：先调用 enable_paging 并取得 BootState<PagingOn>
```

### 4.5 `#[ipc_handler]`：编译期生成整张 dispatch 契约

```jhyy
#[ipc_handler(tag = 0x1001, version = 1, cap_slots = 1)]
fn handle_map_frame(msg: &MapFrameMsg) -> MapFrameReply {
    /* msg 和 reply 由编译器计算 layout；cap slot 自动记录 */
}

#[repr(c, align = 8)]
struct MapFrameMsg {
    frame: Cap<Frame, Read|Write>,
    vaddr: u64,
    _pad: [u8; 4],
}
```

**handler 不应只是属性标记，而应成为全程序契约。** 编译器在一个 `.jhyynb` 内检查：tag 唯一或由 `service_version+tag` 组成的复合 key 不冲突；handler 签名与 message/reply struct 双向一致；每个 `Cap<T>` 字段落在合法对齐槽；`cap_offsets` 不重叠、不越界；handler 所需的 rights 不超过调用 ABI 可携带范围；调用前后栈与效果合法。D16 wire 仍由内核解析，因此内核必须检查 offset、slot 存在性和 rights，但 trusted sender 的布局不一致被前移到编译期[1]。

```text
E0710: IPC tag 冲突
  --> kernel/src/ipc.jhyy:12:1
   |
12 | #[ipc_handler(tag = 0x1001, version = 1)]
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   |
   = 同 version 内已有 handler 使用 tag 0x1001，位于 kernel/src/fs.jhyy:40
   = 建议：更改 tag，或在跨服务接口中明确 service_version
```

```text
E0711: cap_offsets 与 message layout 不一致
  --> kernel/src/ipc.jhyy:48:5
   |
48 |     frame: Cap<Frame, Read|Write>,
   |     ^^^^^ 该字段未出现在生成的 cap_offsets 位图
   |
   = 位图覆盖：0..24
   = 期望覆盖完整 Cap<T> 槽；发现普通字段覆盖 8..16
   = 建议：确认字段类型确为 Cap<T>，或显式标 #[ipc_skip]
```

### 4.6 块表达式、函数类型与闭包：不是奢侈语法

```jhyy
fn enable_paging(s: BootState<PagingOff>) -> BootState<PagingOn> {
    configure_cr3();
    if ready() { mark_on() } else { try_fallback() };
    BootState { _token: PhantomData }
}

fn register_handler(cb: fn(ctx: &TrapCtx) -> u64) { ... }

let base = frame_base;
let write_byte = |off: usize, b: u8| unsafe {
    *frame_ptr(cap, off..off+1).as_mut() = b
};
```

**块表达式是 BootState 的硬前置。** BootState 本质是有序状态迁移；若块不能产生值、函数末表达式不形成连续控制流，状态推进就只能在函数边界完成，临时状态与错误恢复会退回全局可变变量。闭包不能捕获外层变量当前是更严重的问题：它阻止 hot helper 携带本地 token，也迫使开发者把大量两行函数写成顶层名字。再加上 `#[inline]` 只在函数体为单条 `return expr;` 时展开，内核热路径会因“函数无法写全类型/无法捕获上下文”而失去内联。

**`fn(...)` 类型位置是 IPC/中断回调契约的最低要求。** 当前没有函数指针类型语法，而 `#[naked]` interrupt、MS x64 函数指针和 IPC stub 都要求编译器知道参数/返回值的 lowering。最小方案不必先实现高阶类型，只要允许函数类型出现在参数、变量和返回值位置，并强制其 ABI/效果/是否 `#[naked]` 匹配。

```text
E0801: 函数指针类型不兼容
  --> kernel/src/irq.jhyy:50:30
   |
50 |     register_handler(handler_addr as fn());
   |                              ^^^^^^^^^^^^
   |
   = 目标期望：extern "sysv" fn(ctx: &TrapCtx) -> u64
   = 实际签名：fn()
   = 建议：使用完整函数类型，不要将裸地址转为不透明函数指针
```

## 五、编译流水线：每一阶段保存可验证事实

### 5.1 Lexer/Parser：错误必须可定位、可恢复

**现状**：数字、八进制、字符和 match 范围等行为有歧义；CLI 多余输入文件静默忽略。Parser 阶段应输出带 file/source-id、start、end、token-kind 的 span；恢复式解析在第一个错误后仍收集同类错误，但不超过每文件 20 个硬错误，避免单字符错误产生数千行派生报错。新增“未来版本 token 黑名单”：当引入块表达式、函数类型时，旧语法保留原始解释，未闭合块和悬空 `=>` 报 E0xxx，而不生成后续无意义诊断。

**目标**：解析器只负责无歧义 concrete syntax tree（CST），不替 sema 猜测语义。块表达式、match arm 块、`fn` 类型和闭包捕获在语法层预留，P3 再启用。与 OS 的对应主要是可维护性和后续能力语法稳定性：如果 lexer/parser 不能恢复，连续修改 capability API 的编辑反馈会迅速退化。

**难点**：现有 `1_000_000`、`1.0e10`、`077` 与字符 i32 语义需要在兼容模式中冻结。CLI 验收必须区分“未知参数”“多输入文件”“输入不存在”，不得继续以静默忽略作为默认。

### 5.2 Sema/类型系统：把 OS 需求变成 type row 和传播规则

**现状**：实参不检查；bool 不归一化；顶层非整数初始化错误；borrow check 极弱；没有 effect row。Sema 应采用“两遍 + 约束求解”而不是完全 Hindley–Milner：第一遍收集模块、类型、函数与泛型形参；第二遍检查签名、实参、泛型实例化和能力约束。capability、address space、rights、boot state 作为类型/phantom 参数；effect 作为函数属性；layout 作为生成期查询。

**建议的 IL 交接 schema（不声称当前 IL 已是 SSA）**：

| Sema 输出 | 属性 | 消费者 |
|---|---|---|
| `ty` | 完整语言类型 | codegen、layout、诊断 |
| `cap_origin` | 来自哪枚源 cap/哪次 derive | cap check、contract |
| `rights` | 常量位集 | rights subset、wire |
| `addr_space` | user/kernel/phys/io | codegen、codegen 验证 |
| `effects` | may_sleep/irq/preempt/alloc | effect pass、contract |
| `locks` | ordered lock classes | lock order pass |
| `state` | boot state | state pass |
| `layout_hash` | 字段顺序/size/align 的稳定 hash | IPC/ABI facts |
| `stack` | 本地帧上界/调用边 | stack analysis |
| `naked` | 手写栈预算、clobber、preserve | asm verifier |

**目标 IL 应先成为“带类型的控制流图 + 显式 effect/region metadata”。** SSA 利于全局 value numbering、GVN、LICM、PRE，但要求精确的 dominance、phi、内存模型和寄存器压力模型；当前全 spill、池化栈槽与多目标 ABI 尚未稳定。Koka 的 IR 包含类型、效果、堆与谓词注释，显示高层信息不必被完全擦除[11]；JHYY 可借鉴“保留类型与效果”。

> ⚠️ **2026-10-30 订正（前半句基于过时前提）**：本段原文写「**目标 IL 不应直接升级为完整 SSA**」
> —— 但事实是 **IL 已经是 SSA**：前端产出的就是 `%tN = add %t2, %t3` 形式，
> 且 `v4.4.0` 的寄存器分配器（`codegen_amd64_rcache.jhyy`）正是在 SSA temp 上做的。
> 另一条独立证据：前端**已在源码层算掉常量表达式、已清掉死代码** ⇒ IR 层优化三项
> （常量折叠 / 代数化简 / DCE）加起来只有语料 B 的 **1.8%**。
> ⇒ **「缺 SSA」这个前提是错的**。真正缺的是 **寄存器分配 + dominance/phi**
> （后者是 `v4.4.2` 的内容）。

**两阶段升级更合适** —— ⚠️ **2026-10-30 订正:第一阶段的 SSA construction 已经完成**（前端一直产 SSA）。
当前真正要补的是第一阶段的其余部分:typed value、def/use、dominance、effect row 和栈事实，
以及第二阶段的机器无关优化框架。SSA 已有的前提下，允许 `Cap<T>`、效果与栈槽不进入 SSA 值集，
仅作为 instruction/block annotation —— 这样避免用 SSA phi 表达授权，也不会让效果集合成为每个 use 的显式数据。

### 5.3 IL/中端：先分析正确性，再谈优化

**现状**：进程内 IL 只有 `w/l/s/d/m`，足以描述宽度和 MEMORY class，却没有类型、效果、cap、layout 与调用图[2]。中端至少应增加：`ComputeStackBounds`、`EffectPropagation`、`LockOrderConstruction`、`CapDerivationCheck`、`LayoutFingerprinting`、`AsmContractCheck`、`PanicReachability`、`ContractEmission`。优化 pass 默认关闭，正确性 pass 默认开启；每个优化必须声明它保留哪些 metadata。

**cap derivation 应由 source cap 的“origin node”表达。** 每次 derive、map、borrow 创建节点；rights 是节点上的常量属性。代码生成把 8 字节 wire 写入位置或调用参数，但编译期分析只证明类型与子集关系。对象生命周期仍由内核强制，因此“分析图中存在派生路径”不等于对象仍然有效。

**layout fingerprint 应是稳定 schema，而不是原始结构体哈希。** schema 包含：类型 kind、size、align、各字段 offset/size/align/`Cap<T,R>` 标记；不混入字段名，以保证重命名不改变 ABI。变更 layout 时，CI 可生成 baseline 与 patch 两种 hash，报错输出 first differing field。

**panic/termination reachability 应作为控制流事实，而不是把每种错误塞进返回类型。** 编译器把普通 error 作为 `Result` 要求处理；把不可恢复路径分为 `unreachable`、`kernel_oops`、`thread_terminate` 与 `namespace_revoke`。无栈展开意味着每条调用边都要显式处理或证明不可达。规范当前没有 panic/unwind[1]，因此终止分类必须由内核与编译器共同冻结，不能由本编译器单方面新增。

### 5.4 后端 pass：从“能生成汇编”升级为“能证明汇编契约”

**现状后端的核心问题不是指令选择，而是 ABI 假设全局且不可观测。** 每个后端 pass 必须声明输入/输出、读取哪些 IL 事实、是否改变 stack/effects/layout、是否允许增量和复杂度。增量指只对改动函数及其调用者/被调用者重跑；跨过程全程序 pass 至少做到缓存未变输入的指纹，而非每次全量。

| Pass | 输入 IR | 输出/动作 | 依赖前端信息 | 拦住 OS 需求 | 复杂度 | 可增量 |
|---|---|---|---|---|---:|---|
| `ParamTypeChecker` | AST/HIR | 实参/extern 形状错误 | 完整签名 | 2 | 中 | 是 | **📋 已排 v4.6(OS-1)** —— 2026-10-30 实测:实参**类型与个数**均不检查 |
| `BoolNormalization` | HIR/IL | 规范化 0/1 并报警来源 | 类型、控制流 | 已知 u8/&& 风险 | 低 | 是 |
| `TlsStageAllocator` | 驱动层 | 每编译唯一 temp path | 无 | P0 并发 | 低 | 是 |
| `CapTypeResolver` | HIR | `Cap<T,R>` 节点与子集约束 | `T`、`rights` 参数 | 1,2,3 | 中 | 是 |
| `AddressSpaceChecker` | typed IR | `ptr<space>` 构造/解引用图 | cap origin、space kind | 4,5 | 中 | 是 |
| `StackBoundsAnalysis` | CFG/IL | `local_max`、`callee_max`、递归标记 | 调用图、asm budget | 8 | 中 | 函数级 | **📋 已排 v4.7(OS-2)** —— 依赖 v4.4 把帧压下来才量得准 |
| `EffectPropagation` | CFG | `may_sleep/irq/preempt/alloc` | 函数效果、上下文 | 9,10 | 中 | 是 |
| `LockOrderBuilder` | CFG | 有序类、边、强依赖图 | `LockClass`、acquire/release | 19 | 高 | 调用图级 |
| `IpcContractChecker` | HIR/IL | tag/handler/layout/cap_offsets | handler、message struct | 6,16 | 高 | 函数级 |
| `NakedInterruptChecker` | IL/asm | 栈预算、clobber、preserve | `#[naked]` 契约 | 14,22 | 高 | 是 |
| `LayoutFingerprinter` | typed IL | size/align/hash/diff report | 字段与属性 | 15 | 低 | 是 |
| `CapOffsetsBitmap` | IL/asm emission | slot bitmap、type/rights allowlist | cap 字段、handler | 6,16 | 中 | 函数级 |
| `LinearScanRegAlloc` | SSA/CFG | 分配、spill、callee-save | 栈上界、ABI class | 8 | 高 | 函数级 | **🔄 v4.4.0 阶段一已落地**(受限线性扫描:同基本块 + 无 call + 整数类型;5 个 callee-saved GPR;池满退化成栈槽);**阶段二 = emit 层消费寄存器** |
| `AsmClosureInliner` | IL | inline 决策、带上下文 clone | `fn` 类型、块/捕获 | 热路径 | 中 | 是 |
| `KasanShadow` | IL | load/store 插桩与红区 | address space、unsafe 边界 | 安全测试 | 高 | 函数级 |
| `KmsanUninit` | SSA IL | 未初始化来源传播 | def/use | 安全测试 | 高 | 函数级 |
| `KcfiTypeid` | IL/asm | 函数指针 type id 校验 | 函数类型 | 22 | 高 | 是 |
| `ShadowStack` | IR/asm | 返回地址备份/check | call graph、noreturn | 内核 ROP 缓解 | 高 | 是 |
| `PanicReachability` | CFG | termination category | noreturn/效果 | 18 | 中 | 函数级 |
| `WcetBoundEstimator` | CFG/loop | bounded class、局部上界 | loop bound、cache/ILP 模型 | 20 | 高 | 函数级 |
| `ContractEmitter` | 全程序 facts | `.jhyynb` 契约子节 | 全部 | 7,17,20,21 | 中 | 缓存增量 |
| `FactLinkVerifier` | object facts | 全程序上界、禁止环 | 调用图/lock 图 | 8,19 | 中 | 是 |

**栈深度 pass 应同时计算两个量。** `frame_local_max` 是固定槽、alloca/地址池与对齐填充之和；`call_path_max(f)` 是全调用图中从 `f` 到叶节点的最大路径深度。链接器验证 `thread_stack_reservation ≥ call_path_max(entry) + redzone`，并对 `#[naked]`/interrupt 使用作者声明的 `handler_stack_budget`。递归函数默认不可分析，应显式标 `#[unsafe(recursive, max_depth=N)]`；动态调用则形成未知上界，链接期拒绝进入中断路径。

**线性扫描应先做“保持栈槽、只分配普通值”。** 当前两个池已合并以减少重叠[2]，但全 spill 只保存 RBP。第一版 linear scan 可保留地址池语义，只为 formula/临时值建 interval，按起始位置排序，遇到冲突 spill；栈槽继续按固定偏移。这样能在不改变 ABI 兼容性时先压低 229 KiB。真正的图着色应比较真实热点，不应因为“现代编译器都用”而提前引入。

**`asm!` 与 fence 必须变成带 clobber 的 IL 节点。** 当前 hex 被内联进 `dbgasm`，但历史实现曾 append 到 `.s` 末尾[2]；新版 IL 节点应携带输入/输出/内存/clobber、volatile、stack 影响和 source span。naked 函数必须有手写 prologue/epilogue，并声明使用的栈、是否允许调用、是否保留 callee-save。interrupt 函数还须证明返回序列与 trap frame 形状匹配。

**插桩应形成可组合的 instrumentation group。** `KASAN` 处理越界与 use-after-scope；`KMSAN` 传播未初始化；`KCFI` 验证函数指针目标 type id；shadow stack 备份返回地址。它们都应在 IL 插入、保留 source mapping，并在汇编发射时生成符号。规范未记载这些工具是否已存在，故列为新增；实现顺序应是 KASAN → KMSAN → KCFI → shadow stack，因为前两者依赖更强的 def/use/SSA，后两者依赖函数类型和调用图。

### 5.5 汇编发射、链接与产物：输出对象和可加载契约

**汇编发射不应再使用固定旁路文件。** P0 就把 `_inline_asm.buf`、`_section_directive.buf`、`_fence.buf`、`_no_std.flag` 改为基于 session ID、PID 和随机后缀的唯一临时文件；同一编译退出时清理。若自托管编译器需要跨进程共享，可改为传递 fd 或结构化 JSON 指令序列，而不是文件系统协议。

**链接分支必须由显式 target 决定。** 当前根据 `#[no_std]` 而非 `--target` 分支，并仍无条件加 Windows 库[2]，这会让 freestanding 镜像错误地依赖宿主库。target tuple `amd64_win`/`amd64_win_freestanding`/`amd64_sysv`/`amd64_sysv_freestanding` 应成为唯一判据；`#[no_std]` 只控制运行时入口/依赖解析。PE/ELF 的选择由后端决定，不能继续依赖宿主机 ld 的偶然行为。

**`.jhyynb` 需要一个独立且版本化的 `contract` section。** 上游已建议增加栈、sleep、中断、锁、分配、panic 与 WCET 元数据[1]。它应包含：

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

`debug_group` 适合放可选 source map，不能承担 loader 语义。若坚持扩展 `debug_group`，应至少分为 `debug/contract` 两种 flag，加载器只验证后者。contract section 必须有 version、producer ID、source hash 和 compatibility policy，否则旧 loader 可能忽略新增安全字段。

## 六、外部对标：借架构，不借完整语言

**MLIR 最值得借的是“多层 IR + dialect + pass manager”，不是其具体 operation set。** MLIR 允许高层语言信息与低层硬件表示共存，并保留 source location、type 与 traceable IR construction[8]。JHYY 不需要完整 MLIR，但应按 dialect 思想分区：语言类型 dialect、capability/address-space dialect、效果 dialect、machine-independent CFG dialect、amd64 ABI dialect。每个 lowering pass 声明保留/丢失哪些 properties。

**Rust MIR/THIR 与 Swift SIL 的启示是：高级检查必须在降级前完成，但降级后的 IR 仍要有类型。** Swift 在 SILGen 与 LLVM IRGen 之间插入 SIL，集中做语言检查并简化代码生成[7]；Rust MIR 也是类型解析后的核心优化层。JHYY 应避免“HIR 一无所知地 dump 到 4 字母 IL”，至少保留 typed value、function/block ID、call edge 与 effect metadata。

**效果系统的最优起点是 Koka 的选择性行类型，而不是完整代数效应。** Koka 用行多态表示效果，并能把不需要 handler 的调用直接编译，只对有真正效果处理的路径做 CPS 转换[11]。JHYY 的 `with { ... }` 可以先只支持闭合效果集和子集传播；row 多态只在内核 API 出现大量“多数效果相同、少数不同”的签名时引入。Rust 的 `Send/Sync` 也说明，可自动派生的 marker 能显著降低日常注解负担，但 unsafe 边界仍须显式证明[9][10]。

**寄存器分配应按“编译代价/收益”演进。** 线性扫描基于生命期起止排序，实现和调试成本低，适合当前顺序 IL；图着色处理全局干涉与合并，理论上能进一步降低 spill，但实现复杂度高。学术资料显示，多基本块、多数据类型和存储层次会让最优寄存器分配成为 NP 难问题，因此工业编译器通常使用近似算法[5][6]。JHYY 应先 linear scan，再 benchmark；只有当热点真实受寄存器压力限制时才做图着色，不应预设 graph coloring 必然优于 linear scan。

**栈分析应以 GCC `-fstack-usage` 和 Linux objtool 的最小组合建模。** `-fstack-usage` 输出每函数栈量及 static/dynamic/bounded 分类，动态调用和递归仍需链接期/运行时约束[4]。objtool 则从目标文件检查控制流、栈状态和入口契约。JHYY 可把 per-function facts 与全程序调用图分开：函数内静态边界由 IL pass 计算，递归/动态调用由链接器拒绝或要求显式边界。Linux lockdep 当前主要在运行时构建依赖链，但清华公开材料已经把强依赖链和循环检测做成编译期算法[14]；JHYY 应先覆盖显式 lock class，再处理读/写锁的强边。

**BTF 与 Kythe 表明，编译事实应双轨输出。** BTF 将内核与 BPF 程序所需类型、成员偏移和重定位写入可执行文件，使 Clang 生成的 BPF 程序能跨内核版本做 CO-RE[12]；Kythe 提供语言无关的构建、编译器、分析器之间的事实交换[13]。JHYY 的主 JSON/protobuf 面向工具链，`.jhyynb` contract 面向 loader；二者用同一 schema 生成，避免双份漂移。

**CHERI 可作为长期物理指针模型参考，但不进入 amd64 v0.0.1。** Morello 的硬件能力由元数据和权限标签保护，只能缩小边界或权限，不能扩大[15]。JHYY 当前只能做到软件 object capability：类型证明授权 shape，内核证明对象存在与 authority。不能声称 `ptr<phys>` 拥有 CHERI 式硬件边界。

## 七、分期路线图与可测量验收门

| 阶段 | 目标 | 具体任务 | 前置依赖 | 验收门（可测量） | 不做会怎样 |
|---|---|---|---|---|---|
| P0 止血 | 消除静默错误与不可重复编译 | 实参检查；extern 参数形状；CLI 报错；唯一旁路路径；bool 归一化；顶层初始化；数字字面量冻结；先十行复现再修 `&&`/u8；错误恢复与 span | 现有 parser/sema/后端可编译 | 100% 覆盖 `game.jhyy` 复现样本；多余输入报错 E0001；并发 8 进程无旁路文件竞争；`false && side()` 中 side 不执行；布尔比较只用 0/1 | 后续自举结果无法区分真错误与旧 bug；Windows 上无法并行构建 |
| P0.5 观测 | 编译器知道自己的最坏行为 | 测量本地槽、地址池、align、callee depth；输出 per-function CSV；链接器支持栈断言 | P0 | 所有单函数 `frame_local_max` 可打印；递归/动态调用显式标记；CI 保存基线 | 栈问题仍靠运行时溢出发现，无法给内核配置线程栈 |
| P1 反馈环 | 让最小内核真正跑在裸金属 | UEFI entry 钩子；按 target 分支链接；移除无条件 Windows 库；`SetConsoleOutputCP(65001)`；trivial image 链接期栈断言 | P0、现有四个目标后端 | 最小 `kernel.efi` 能在 QEMU/OVMF 输出 UTF-8 并停机；栈保留 8 KiB/16 KiB 任一目标可在编译期选；`#[no_std]` 不再自动加 Windows 库 | 编译器长期寄生 Windows，能力/IPC 是否可执行未知 |
| P2 栈与分配 | 先证明栈，再减少栈和 spill | 栈深度全程序分析；链接断言；栈槽 16B 对齐；线性扫描；可选 shadow slot；benchmark 套件 | P0.5 | `max_frame ≤ 16 KiB`；自举编译器最大路径相对当前 229 KiB 下降 ≥ 90%；SysV SIMD 参数不产生 8B 对齐 fault；所有改动函数增量重跑 | 内核中断/IPC 可能破坏相邻栈；229 KiB 迫使线程栈无谓增大 |
| P2.5 ABI 收敛 | 关闭已知偏离，形成兼容基线 | 修复 sret/整数预算、SysV eightbyte、MEMORY+参数混排；统一 alignof(enum)；asm/fence IL 节点；目标决定 PE/ELF | P2 | 14 条偏离降至 ≤3 条且均为显式兼容性例外；abi-hash CI 不回归；trivial + freestanding 两套 smoke 全绿 | 新能力代码会在现有调用约定下悄悄错传 cap 或 SIMD |
| P3 语言自洽 | 让 API 能用普通语言写 | 块表达式；`fn` 类型位置；闭包捕获；`()` 类型位置；defer 覆盖末表达式；类型别名/属性小修 | P2.5 | 100 个内核 helper 可写成 1–5 行闭包；boot state 迁移可在块内完成；函数指针可跨模块传递；P3 前后端测试全绿 | BootState、hot path inline 与 callback 契约都无法自然表达 |
| P3.5 效果骨架 | 先拦最高危上下文错误 | `with { ... }`、效果传播、irq/preempt/sleep/alloc 禁止规则；锁类与有序 acquire/release | P3 | 所有 `irq_ctx` 内 `may_sleep/may_alloc` 调用被拒；无反向锁边；误用给出 E0510/E0511 | 持锁睡眠、PF 路径分配仍靠 review |
| P4 OS 差异化 | 把授权链从 wire 提升为类型 | `Cap<T>` 真 T；rights 参数化与子集；`ptr<phys/io>`；cap derive API；`#[ipc_handler]`；cap_offsets；contract section | P2.5、P3.5、对象模型冻结 | `Cap<i32>`≠`Cap<i64>`；整数不能转 `ptr<phys>`；IPC tag/layout/slot 全检查；contract 被 loader 校验；最小 cap init/frame map/IPC demo 闭环 | 语言无法阻止 frame/endpoint/file 混用与物理地址越权 |
| P4.5 内核可信工具链 | 输出可审计事实 | KASAN/KMSAN/KCFI/shadow stack；WCET bounded class；panic category；layout diff | P4 | 插桩前后行为语义一致；至少 20 个注入 bug 被 KASAN/KMSAN 捕获；KCFI 对类型不匹配指针调用报错；所有契约有 schema 与 producer version | 无栈展开下故障与越界更难点恢复，无法审计对象边界 |

**总体依赖可压缩成两条链。** 稳定链为 P0 → P0.5 → P1 → P2 → P2.5；能力链为 P3 → P3.5 → P4 → P4.5。两条链只在 P2.5/P3 和 P4 处汇合。也就是说，实参检查、最小镜像、栈分析和 ABI 修复不应等待效果系统；而 capability 语法不应提前到 boot state/函数类型/闭包尚未稳定时。

## 八、与既有判断的分歧

**P1 应该上移，但不是把 P1 与 P0 完全互换。** 我的判断是：P0 中“可能让旧 bug 被新代码放大”的项目完成后，立即进入 P1。原因不是“能跑更重要”，而是 P1 提供最小实证平台：只有真实 PE/EFI 加载、目标分支链接和栈断言开始工作，才知道 P2 的 16 KiB 目标是否适配 trivial program，P4 的 IPC/cap 是否真的能被 loader 解释。若先花几个阶段完善语言，仍寄生在 Windows，能力语法可能从一开始就在没有执行路径的环境里演进。反方风险是过早写 UEFI 代码会把 ABI 偏离固化；因此验收应是“最小停机镜像 + 所有 P0 检查通过”，而不是立即做完整 boot。

**P3 与 P4 应部分交错，而不是严格串行。** OS 报告第十四节建议第一阶段冻结 `.jhyynb` 静态表、为 `Cap<T>` 增加真实 T 与 rights 参数[1]，这与把 capability 类型化放到 P4 并不冲突。真正属于 P4 的是 capability 的语义、ABI 与二进制兼容性；P3 只需先完成块表达式、`fn` 类型、闭包捕获和 `()` 类型。建议把 P3.5 效果骨架插入 P3 之后，把 `Cap<T>` 真实 T 与 rights 留在 P4。理由：效果与锁依赖依赖函数签名和 CFG，而这些又依赖函数类型与闭包；如果 P4 一次性引入所有 capability，一次回归可能横跨类型、效果、IPC 和二进制，难以二分。

**栈测量应先于寄存器分配，这方向正确，但要明确“两个上界”。** 同意“先测量/断言，再优化”；不同意把“栈帧”只看成单函数本地需求。229 KiB 是单函数 `frame_local_max` 的现实值，但链接器真正需要的是入口到叶节点的 `call_path_max × frame + redzone`。因此 P0.5 就要输出两个量，P2 才同时降低单帧和缩短最坏路径。若只做线性扫描，函数内 spill 减少，但递归/深调用图可能仍超限。

**P4 不应在对象生命周期和 revoke 未冻结时先落地真实 T。** `Cap<T>` 的 `T` 只有 8 字节 wire 且当前不解析[1]；这不能阻止前端类型化，但 wire 外的对象关系尚未确定。应先用 capability objects manifest（type_tag 白名单、rights 初始集、生命周期 owner、cap init phase）冻结语义，再改 `Cap<T>`。否则未来增加 version/provenance 会迫使第二次 ABI break。

**`Cap<T>` 的 rights 可以进类型参数，但不必支持任意 effect algebra。** 上游报告提出 `Cap<T,Rights>`[1]，我同意。JHYY 的 rights 是 R/W/G 的常量集合，适合子集约束；若引入完整代数效应，会把 syscall、handler、恢复和 CPS 一起引入，远超当前无栈展开模型。建议 `rights` 为 const generic 集合，编译器只实现交集、并集、子集和 `where` 约束。

**不把 `.jhyynb` 所有新事实都塞进 debug_group。** 上游建议扩展 `debug_group`[1]，我部分反对。可调试 source facts 与 loader-必须验证的 contract facts 应共享编码基础设施，但 security bit 必须不同。推荐新增 `contract` section，或至少用 `debug/contract` 两级 flag。否则旧 loader 可能把 capability 栈预算当成可选调试信息忽略。

**KCFI、shadow stack 和 WCET 不应与 P2 栈分析同权。** 它们重要，却依赖函数类型、调用图、ABI 稳定和实时模型。P2 必须先保证最坏栈不会溢出；插桩工具是“发现更多错误”，不是“避免静默越权”。所以把它们放在 P4.5，而非 P1/P2。

**外部对标应以机制而非项目品牌为依据。** MLIR 值得学的是分层 IR，不是必须引入 MLIR；Koka 值得学的是选择性 CPS，不是完整代数效应；Linux lockdep 值得学的是依赖链，但运行时动态锁依赖仍不能替代编译期 lock class；BTF 值得学的是编译事实供内核消费，不是照搬 BPF 类型语义。

## 九、规范未记载，待确认

以下项目没有三份规范支持，不能作为已实装事实：

1. 编译器源码结构、现有 pass 清单、HIR/AST 表示、单态化实现、错误码总表、增量编译缓存和测试框架均未提供。
2. 是否存在真正的 u8/boolean codegen bug，以及 `game.jhyy` 注释所述根因，尚未用十行复现程序验证；可能是 `&&` 的 32 位比较、u8 扩展、指令选择或 SSA 之前的中间表示问题。
3. `Cap<T>` 的 `T` 重新解析是否影响现有 wire 与二进制兼容性，规范没有 ABI versioning 或迁移方案。
4. capability objects、CNode、slot version、撤销树、反向边、revoke 同步性、depth 溢出处理和 provenance 规则均未记载。
5. `ptr<phys>` 是否消耗 `Cap<Frame>`、map/unmap 与 TLB quiesce 语义、frame metadata 所有者均未记载。
6. 锁类命名、偏序声明语法、读写锁强依赖、跨模块 lock order、中断锁与 try-lock 语义均未记载。
7. `may_sleep/irq_ctx/preempt_disabled/may_alloc` 的精确格、默认签名、禁止集与 unsafe escape hatch 未记载。
8. `.jhyynb` 的 contract section kind、版本、producer ID、签名、加载顺序、未知字段策略和 loader TCB 均未记载。
9. WCET 的目标架构 timing model、cache/流水线参数、循环边界注释和测量预算未记载。
10. panic/oops、fault handler、thread termination、namespace revoke 及 continuation 分类未记载。
11. KASAN/KMSAN/KCFI/shadow stack 的 shadow region、元数据结构、编译开关和内核协作接口未记载。
12. UEFI 的 console protocol、image handle、memory map、SMP 启动协议和退出/停机语义未记载。
13. 现有自托管后端是否有 SSA、dominance、def/use、CFG、寄存器压力模型、ABI verifier 和汇编 emission tests，未记载。
14. 现有 `_inline_asm.buf` 等旁路文件的读写协议、并发模式、跨后端共享方式和生命周期未记载。
15. 后续是否支持 aarch64、riscv64、PE/ELF 交叉容器后端，以及能力模型是否兼容 CHERI，未记载。
16. P3 新增语法是否破坏现有 `match` 闭包、`#[inline]`、defer 与块表达式，未给出完整兼容程序测试集。

## 十、最终判断

**JHYY 的第一优先级应是确定性，第二优先级是执行反馈，第三优先级才是表达力。** P0 把“传 i32 给 struct 形参也能通过”等静默错误变为编译失败，P0.5 让编译器第一次知道自己的最坏栈，P1 让最小镜像第一次真实执行。这个组合能在最小改动面内验证现有四个自托管后端和 ABI 是否适合内核。

**寄存器分配的正确顺序是测量 → 断言 → 线性扫描 → 按基准升级。** 229 KiB 单函数帧说明当前最大问题不是指令选择慢，而是最坏资源需求未知。线性扫描能复用顺序生命期、快速降低 spill；图着色只在热点分析和真实访存收益支持时实施。与此同时，栈分析必须同时报告 `frame_local_max` 与 `call_path_max`，链接器用线程栈保留量约束后者。

**能力模型必须贯穿类型、签名、IR、codegen 和 `.jhyynb`。** `Cap<T,Rights>` 的 T 应被解析，rights 只做子集收缩，`ptr<phys>` 只能从 `Cap<Frame>` 等可信来源派生，IPC handler 应由编译器生成 tag/layout/cap_offsets 契约。效果是函数签名的事实，而不是注释；boot state 是状态迁移 token；layout/ABI/栈/锁序/WCET/panic 是编译期生成的 facts。它们共同构成一条从源码到加载器的可审计链。

**P3 与 P4 应部分交错：先完成块表达式、`fn` 类型、闭包捕获和效果骨架，再冻结 capability 二进制语义。** 块表达式是 BootState 顺序迁移的前置条件；`fn` 类型是中断/IPC 回调的前置条件；闭包捕获是内核 hot helper 内联的前置条件。当前 `#[inline]` 只在单条 `return` 时展开，且闭包不能捕获，已实质阻塞小函数内联。capability 对象模型、生命周期与 wire 兼容性稳定后再引入 `Cap<T,Rights>` 和 IPC 全契约，可避免一次同时改变语言、ABI、二进制格式与内核接口。

**最终交付标准不是“能写更漂亮的内核”，而是“错误程序无法通过”。** 若完成 P0–P4.5，至少应达到：实参和 extern 形状错误被静态拒绝；最大栈可测量并受链接器断言；irq/preempt/alloc 上下文误用被拒绝；锁序环被拒绝；`ptr<phys>` 只能从 frame cap 派生；IPC tag、layout 与 cap slot 全检查；所有关键契约写入 `.jhyynb` 并由 loader 验证。反之，若 capability 类型、效果、栈和契约继续依赖运行时或人工 review，JHYY 虽然有自托管后端，仍只是“能编译的 OS 语言”，尚未成为能力微内核的编译器基础设施。

## 引用来源

[1] ../abis/jhyy-abi-v4.0.0.md
> 四目标：amd64_win / amd64_win_freestanding / amd64_sysv / amd64_sysv_freestanding，全自托管后端，无 QBE 回退。

[2] ../abis/jhyy-abi-v4.0.0.md
> 自举编译器最大单函数帧实测 234080 B ≈ 229 KiB，靠 `-Wl,--stack,67108864` 补偿。
>
> ⚠️ **2026-10-30 更正**:取数自 v4.2.1 **之前**。v4.2.1(2026-10-29)后 **max 帧
> 237680 → 349232 B(341 KiB,反而变大)**,中位帧 8368 → 288 B,chkstk 调用 1045 → 46。
> ⇒ **降帧杠杆已从「调公式」转移到「寄存器分配」(v4.4 阶段二)**,P2 验收目标需按
> 341 KiB 重算。详见 `docs/plans/v4/self-backend-perf-plan.md` § 三之二。

[3] ../abis/jhyy-binary-format-v1.0.0.md
> `.jhyynb`，header 112B，jhyy 专属 section：cap_init(kind=4) / ipc_dispatch(kind=5) / region_table(kind=7) / debug_group(kind=6)。

[4] https://news.qq.com/rain/a/20240813A07XK700
> GCC 提供 -fstack-usage 选项，能输出每个函数栈的最大使用量，并为每行添加 static/dynamic/bounded 修饰符。

[5] http://cs.nju.edu.cn/_upload/tpl/01/55/341/template341/2_compiler/projects/Project_4.pdf
> 几乎添加任何假设都会使寻找最优寄存器分配方案变成 NP 难问题，现代编译器多使用近似最优方案。

[6] https://soft.cs.tsinghua.edu.cn/~dongyuan/docs/compcert-2010.pdf
> 寄存器分配开始于采用逆向数据流分析的标准活跃分析，并基于伪寄存器构建冲突图。

[7] https://www.sohu.com/a/141073674_470093
> 在 IRGen 之前执行代码的监测和优化，生成高级中间表达 SIL，最后将 SIL 转换成 LLVM IR。

[8] https://www.sohu.com/a/307133340_670669
> MLIR 的核心是一种灵活的基础设施，适用于现代优化编译器，其中包含适用于中介码（IR）的规范与转换此中介码的代码工具包。

[9] https://new.qq.com/rain/a/20230330A01ER200
> Send 表明类型的所有权可以跨线程传递；Sync 表明类型允许多个线程共享。

[10] https://www.sohu.com/a/460215780_473282
> Rust 巧妙地使用了类型系统帮助构建完整的并发安全体系，Send/Sync 是与 ownership 模型配合的特殊标记。

[11] https://koka-lang.github.io/koka/doc/book.html
> Koka 类型语法包含 `with (predicates)` 限定符，以及 value、effect、effect row、heap、predicate 与 scope 等种类。

[12] https://www.sohu.com/a/570000417_612370
> Clang 通过 `--target bpf` 生成 BTF，`.btf` 记录类型信息，`.btf.ext` 记录 BPF 程序内数据类型使用情况。

[13] https://www.sohu.com/a/119835948_355142
> Kythe 提供一个语言无关的交换机制，供构建系统、编译器、解释器、静态分析、编辑器与代码审查程序共享信息。

[14] https://soft.cs.tsinghua.edu.cn/os2atc2018/ppt/osd4.pdf
> A strong dependency chain/path forms a circle 即为死锁条件；实现扩展 __bfs 在强依赖路径上遍历。

[15] https://m.thepaper.cn/baijiahao_19666964
> 一般无法在能力内添加边界，指令只能减少能力边界或权限、由原始对象创建子对象，无法扩大权限边界。
