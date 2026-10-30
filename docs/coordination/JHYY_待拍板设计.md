# JHYY 待拍板设计 —— 12 条未决的设计

> **本文定位**:`docs/coordination/` 的五份基线文档在末尾各留了一张「需要你拍板」的表
> (`决策总纲 §6.1` 六条、`Cap类型语义草案 §8` 六条)。那些表只列了**问题**和**阻塞**,
> 没给**可选项**、**推荐**和**产物** ⇒ 拍板时无从下手。
>
> **本文给出 12 条决策的设计稿**:每条含①可核实的**事实基线**②**选项**③**建议 + 理由**
> ④**影响面**⑤**具体产物**(规范条文 / 类型签名 / wire 布局 / 门)。
>
> **本文不代替拍板** —— 每条的建议都可被否决;被否决时该条的「产物」一栏作废。
>
> **核实口径**:2026-10-30,所有「事实基线」逐条回**源码 / 规范 / 门脚本**核过,
> 引用位置写明 `file:line`。**不引用任何文档里的转述当事实。**

---

## §0 一页速查

| # | 决策 | 我的建议 | 阻塞什么 | 紧迫度 |
|---|---|---|---|---|
| **D1** | `Cap` wire 里 `rights` 在第 5 还是第 6 字节? | **以 lang-spec + abi 为准(rights@5)**,修订 binary-format;**并加规范一致性门** | `Cap<T>` 真 T 的第一步 | 🔴 **最硬** |
| **D2** | revoke 位是否进 `Cap` wire? | **不进**;cap_init 的第 4 位另作元数据 | rights 集合是 8 种还是 16 种 | 🔴 |
| **D3** | `Page` 与 `Frame` 是不是两个对象? | **统一为 `Frame`**,`Page` 不存在;**另发现缺 2 个 type_tag** | `frame_phys` 签名 | 🔴 |
| **D4** | slot version 方案? | **用 `padding:u8` 做 slot generation** | slot 复用 = UAF + 静默越权 | 🔴 |
| **D5** | 引入 `unsafe` 关键字? | **不引入**;用属性(`#[trusted]` / `#[unsafe_cap_ctor]`) | `as Cap` 后门怎么收敛 | 🟡 |
| **D6** | `derive_dyn` 是否允许? | **允许**,重命名 `derive_dynamic`,返回最宽类型 + `Option` | 动态策略写不写得出来 | 🟡 |
| **D7** | revoke 同步还是异步?传播吗? | **默认同步 + 分级**;区分 `retract_cap` / `revoke_object` | ⚠️ **其实不阻塞 Cap 真 T**(见 §7) | 🟡 |
| **D8** | `ptr<phys>` 消耗 `Cap<Frame>` 吗? | **不消耗**;派生新 cap,原 cap 保留 | derive API 形态 + TLB 协议 | 🟡 |
| **D9** | `as Cap` 逃生舱保留吗? | **保留但收敛**:唯一入口 `from_raw`,只在 `#[trusted]` 内可用 | 与 D5 同批 | 🟡 |
| **D10** | M3 message 的 cap 策略? | **移动语义**;发送即撤销 sender slot;**第一版不做 timeout** | `#[ipc_handler]` 契约 | 🟢 |
| **D11** | 内核栈策略? | **栈大小由 loader 选**;硬门改成「自举编译器 64 KiB 内跑完」;中断栈 4 KiB | P2 的 16 KiB 目标可不可达 | 🟡 |
| **D12** | 整数之间要不要隐式提升? | **只在字面量位置**(`i64 + 1` ✅,`i64 + i32_var` ❌),并写进规范 | OS-1 的报错口径 | 🟡 |

**依赖关系**:
```
D1 ──┬─→ D2(定下 rights 集合大小)
     ├─→ D4(定下 padding 字节的用途)
     └─→ D3(定下 type_tag 词汇)
D5 + D9 ──→ (as Cap 收敛方案)
D7 ──→ D8 ──→ D10(unmap 语义 → IPC 语义)
D12 ──→ OS-1 的实参检查口径
D11 ──→ OS-4 的验收门数字
```

---

## §1 D1 —— `Cap` wire 里 `rights` 在第 5 还是第 6 字节?

### 事实基线

| 来源 | 布局 |
|---|---|
| lang-spec §2.6 | `cnode_idx:u32@0` · `depth:u8@4` · **`rights:u16@5`** · `padding:u8@7` |
| abi §2.5 | 同上(**逐字一致**) |
| binary-format §2(D6+D23) | `cnode_idx:u32@0` · `depth:u8@4` · `_pad:u8@5` · **`rights:u16@6`** |

**判定证据**:lang-spec §2.6 自带构造示例
`0x0000030200000007 as Cap  // cnode=7, depth=2, rights=R|W`
小端展开 = `07 00 00 00 | 02 | 03 00 | 00`
⇒ **只有在 `rights@5` 下才解出注释说的 cnode=7 / depth=2 / rights=R|W**;
按 `rights@6` 解出来是 `rights=0x0000`、`_pad=0x03` ⇒ **示例自相矛盾**。

**另一条独立事实**:`type_tag` / `cap_init` 词汇表**只存在于 binary-format**
(`grep -l type_tag docs/abis/*.md` 只有它)⇒ **lang-spec 与 abi 互相印证,
binary-format 是孤本异类**。且 binary-format §32 引用的 D6/D23 原件**不在本仓**。

**当前不发作的原因**:`Cap<T>` 的 `T` 不解析、无 `.cnode_idx`/`.depth`/`.rights`
字段访问 ⇒ **没有任何代码按字节拆 cap**。

### 选项

| | 方案 | 代价 |
|---|---|---|
| A | 以 lang-spec + abi 为准(rights@5),修订 binary-format | 改一份**未实装的设计稿** ⇒ 零代码成本 |
| B | 以 binary-format 为准(rights@6),改 lang-spec + abi + 换示例 | 改两份**已锁定**的规范 + 换一个自洽性已被使用的示例 ⇒ 高成本、高风险 |
| C | 两者都不改,只写「按 target 决定」 | **最坏** —— 同一份程序用不同规范实现会静默错位 1 字节 |

### 建议:**A + 一道规范一致性门**

**理由**:
1. 两份**锁定**规范(lang-spec / abi,2026-10-24)互证一致,且带**可验证示例**;
   binary-format 是 2026-09-04 的**设计稿**(未实装)⇒ **事实基线的一侧有两票,另一侧只有一票**
2. 两种布局都满足 D41 的「自然对齐 + 显式 `_pad`」⇒ **对齐推不出对错** ⇒ 只能靠「哪个是实现事实 + 哪个自带示例」判
3. **当前零代码成本**:没有代码按字节拆 cap ⇒ 现在改是零成本,等 `Cap<T>` 真 T 落地后再改就是 ABI break

**为什么要加门(C 的教训)**:这次冲突能活三个月(两份锁定规范互相矛盾),是因为
**没有一道门**。⇒ 加 `scripts/dev/check_spec_consistency.py`:从 lang-spec §2.6 /
abi §2.5 / binary-format §2 三处解析 Cap 布局的 `(offset, size, type)` 三元组
+ rights 位宽 ⇒ **不一致即红**,接进 CI。

### 产物

- binary-format §2 那行改为 `rights:u16@5`,并加一句「本字段与
  [lang-spec §2.6](../abis/jhyy-lang-spec-v4.0.0.md) / [abi §2.5](../abis/jhyy-abi-v4.0.0.md)
  同源;改动须三处同步」
- **单一真源 = lang-spec §2.6**;abi 与 binary-format 改为引用它
- 新门 `check_spec_consistency.py`(比对三处的 Cap 布局 + rights 位宽)

---

## §2 D2 —— revoke 位是否进 `Cap<T>` wire?

### 事实基线

| 来源 | rights 位 |
|---|---|
| lang-spec §2.6 / abi §2.5 | **3 位**:bit0=R, bit1=W, bit2=G |
| binary-format §7 cap_init | **4 位**:bit0=R, 1=W, 2=G, **3=revoke** |

⚠️ 注意:**cap_init 表项的 `rights:u16` 字段**与 **`Cap<T>` wire 的 `rights:u16` 字段**
是**两个不同的字段**。binary-format §239 说「rights 直接对应 `Cap<T>` 8B 布局的
`rights:u16` 字段(per D6),kernel 分配 cap 时直接 copy」⇒ 它们被**设计成同源**。

### 建议:**revoke 不进 `Cap<T>` wire**

**理由**:

1. **两个正交维度被塞进了一个字段**。cap 的 rights 描述「**持有者能对这个对象做什么**」;
   revoke 描述「**持有者能对这个引用做什么**」。⇒ 前者是对象的权限集,后者是引用的处置权
   ⇒ 若同占 16 位,rights 类型从 8 种变 16 种,其中一半是**不可达组合**
   (有 revoke 而无 R/W/G 毫无意义)
2. **撤销的正确语义是 CDT 上的操作,不是 cap 上的属性**。一个 cap 被 revoke 后,
   它在**别的进程**的副本也失效吗?若 revoke 在 wire 上,每个副本各带一位 ⇒ **语义分裂**
   ⇒ CDT(对象反向边)是全局真源 ⇒ revoke 必须是 **CDT 上的操作**
3. **真正需要「这个引用还活着吗」的载体是 slot 版本**(见 D4)⇒ 那才是 cap wire 上
   真正需要的额外位 —— 而它已经在 `padding:u8` 里了
4. **seL4 的先例**:revoke 是 CDT 上的操作(CdtRevoke);cap 上没有 revoke 位

**代价与处置**:binary-format cap_init 的第 4 位需要重新定义。
⇒ **cap_init.rights 降回 3 位(R/W/G)**,与 Cap wire 一致;
若 cap_init 需要表达「该 cap 初始是否可撤销」⇒ 用**独立的表项字段**
(cap_init 表项 32B,`_pad0:u8` 有 1 字节可用)

### 产物

- binary-format §7:`rights: u16, // bit 0 = read, 1 = write, 2 = grant` +
  一行「revoke 语义由 CDT 承担,**不进 rights**;见 lang-spec §2.6」
- **rights 类型集合定为 8 种**(与 D1 合并生效)

---

## §3 D3 —— `Page` 与 `Frame` 是不是两个对象?

### 事实基线

**type_tag 词汇表只存在于 binary-format**(lang-spec / abi 里零命中):

```
0=endpoint  1=page  2=framebuffer  3=console  4=file  5=shm
6=compositor  7=surface  8=seat  9=buffer  10=endpoint_focus
```

⇒ **「Frame」这个词是 OS 报告自造的**,规范词汇表里只有 `page`。
而 lang-spec / abi 里连 capability 对象类型的词汇表都**没有**。

### 建议:**统一为 `Frame`;`Page` 不存在;并补两个缺失的 type_tag**

**理由**:

1. **`page` 在 OS/硬件语境里几乎总是「虚拟页」**。而这里要表达的是**物理页框**
   ⇒ 用 `page` 会持续引起歧义(页表映射单元 vs 物理页框)
2. **虚拟页根本不需要 cap** —— 它是地址空间的一个区域,由 `region_table` 声明
   (`anon_arena` / `mmap` / `raw_mmio` …)⇒ **cap 授权的对象是物理页框,不是虚拟页**
   ⇒ 二者**不该并列为两个 type_tag**
3. **type_tag 是数值,名字只是注释** ⇒ 改名字**零成本、零 ABI 影响**

**⚠️ 顺带发现:type_tag 表缺两个 OS 推导链必需的对象。**

`决策总纲 §4.1` 的示例代码用了 `Cap<AddressSpace, Write>`;
`OS 报告 §10` 的 `map_into` 返回 `Cap<Mapping, R>`。
⇒ **但 type_tag 表里既没有 address_space 也没有 mapping。**

⇒ **设计产出**:
- type_tag=1 的名字从 `page` 改为 **`Frame`**(语义:物理页框),binary-format 注释同步
- **不引入 `Cap<Page>`**;虚拟页/映射单元归 region_table
- **缺失的 type_tag 登记为 P4a(OS-13)的输入**,不在此刻临时加:
  - `AddressSpace`(cap 化的 VSpace)—— 总纲 §4.1 需要
  - `Mapping`(一次映射的结果)—— OS 报告 §10 的 `map_into` 需要
  ⇒ **P4a 的 manifest 必须先答「哪些对象类型存在」,否则 P4b 写签名时会再次缺类型**

---

## §4 D4 —— slot version 方案

### 事实基线

- `Cap<T>` wire 的 `padding:u8@7` —— lang-spec 明写「**零**」⇒ **1 字节空闲**
- 规范**完全没有** slot version / generation 的记载
- Cap 草案 §7.3 已把「slot 释放后被复用,旧 cap 指向新对象」列为**模型边界**(UAF 隐患)

### 选项

| | 方案 | 判定 |
|---|---|---|
| A | **`padding:u8` 改作 slot generation** | ✅ |
| B | 内核维护 `(slot, generation) → alive` 表,cap 不带 generation | ❌ **不可能** —— cap 只有 slot 索引,内核无从知道这个 cap 是哪个 generation 派发的 |
| C | 用 `provenance_seed` 哈希 | ❌ 同样需要 cap 带标识 |
| D | 不做,slot 永不复用 | ⚠️ 简单,但 2^32 槽会耗尽;且这等于**放弃**对一个已知 UAF 的防护 |

### 建议:**A —— `padding:u8` 改作 slot generation**

**理由**:
1. **`padding:u8` 已经存在且明文写「零」** ⇒ 重新定义它,**wire 长度不变、字段数不变、
   ABI 不破坏** ⇒ **零成本**
2. 这是**唯一能让内核判定「这个 cap 还活着吗」的机制** ⇒ 没有它,
   slot 复用 = UAF;更糟的是它**静默越权**(旧 cap 拿到了新对象的权限)
   ⇒ 这直接违反 object capability 模型的核心承诺
3. **seL4 用的是 CNode generation** ⇒ 成熟做法,不是发明

**必须写明的约束(容易踩坑)**:
- generation **只在同一个 CNode 槽内有意义** ⇒ 跨 CNode 派生时,目标槽的 generation
  由**目标 CNode 的所有者**决定(内核分配),**不是继承** ⇒ 写错会让"跨 CNode 混淆"
  的防护看起来存在实则无效
- 因此 D3 的 `AddressSpace`/`Mapping` 若引入,**也要各自的 slot 空间与 generation 语义**

### 产物

- lang-spec §2.6 + abi §2.5:`padding:u8` 改名 `gen:u8`(或 `version:u8`),
  语义改为「**slot 复用代数**;slot 被复用时 +1;cap 派发时携带当时的代数」
- binary-format §2 同步
- `Cap<T>` 真 T 的实现里,`from_raw` 需要同时接受 slot 与 gen

---

## §5 D5 —— 是否引入 `unsafe` 关键字?

### 事实基线

`grep -rn unsafe compiler/src0/*.jhyy` ⇒ **零命中** ⇒ `unsafe` **完全不存在**。

### 选项

| | 方案 | 判定 |
|---|---|---|
| A | 引入 `unsafe` 关键字(`unsafe {}` / `unsafe fn`) | ❌ 成本远超收益 |
| B | **属性**(`#[trusted]` 模块级 / `#[unsafe_cap_ctor]` 语句级) | ✅ |
| C | 不收敛,`as Cap` 原样保留 | ❌ 留一个完全不受控的后门 |

### 建议:**B —— 不引入关键字,用属性**

**理由**:
1. **`unsafe` 是一整套语言级语义**(块 / fn / trait / impl / lint 生态 / 与 borrow 的交互),
   而 JHYY 连 `&mut` 的完整语义都还停在 W-105 的**最小版**(词法作用域)
   ⇒ 引入 `unsafe` 会立刻需要:块的作用域规则、fn 的调用点检查、`unsafe` 与借用检查的交互、
   unsafe trait 的对象安全… ⇒ **成本远超「让后门可标注」这一个需求**
2. **JHYY 要的只有一件事**:让「绕过 capability 构造」这件事**可标注、可统计、可审计**
   ⇒ **属性就够了**
3. **属性语法已经存在**(`#[naked]` / `#[no_std]` / `#[link_section]` / `#[ipc_handler]`)
   ⇒ **零新语法** —— 这是决定性理由
4. **模块级更贴合实际场景**:cap 构造只发生在 **kernel bootstrap**(整个模块都是特权)
   ⇒ 模块级标注一次即可,不必在每个构造点包块
   ⇒ 但**语句级也有价值**(用户模块里只有 3 处构造)⇒ **两级都要**

### 产物

```jhyy
// 文件 / 模块级:整个文件豁免(仅 kernel bootstrap 用)
#[trusted]
mod boot {
    fn root_cap() -> Cap<Frame, RWG> {
        return Cap::<Frame, RWG>::from_raw(0x0000030200000007);
    }
}
```

- 新属性 `#[trusted]`(模块/文件级)与 `#[unsafe_cap_ctor]`(函数/语句级)
- `from_raw` 是**唯一**构造入口;`as Cap` 保留为 **deprecated 别名**,
  且**只在 `#[trusted]` 范围内可用** ⇒ 在普通模块里写 `as Cap` ⇒ **编译期报错**
- 编译器输出 `unsafe_ctor_count` + `unsafe_ctor_offs` 进 contract section
  (schema 见 Cap 草案 §5.1)⇒ CI 可断言 `kernel.efi` 的 count ≤ N 且只在 bootstrap 模块
- **明确不做**:unsafe 关键字 / unsafe fn / unsafe trait / unsafe 块
  ⇒ 留到「需要 unsafe fn 时」再设计(那时的形态会不一样)

---

## §6 D6 —— `derive_dyn` 是否允许存在?

### 事实基线

Cap 草案 §3.2:运行时派生返回**最宽类型** `Cap<T, RWG>` + `Option`,
调用方须显式 `narrow::<D>()` 才能拿回静态保证。

### 建议:**允许,但重命名为 `derive_dynamic`**

**理由**:
1. **完全禁止会逼出更糟的写法**:用户会直接 `as Cap` 手搓 ⇒
   **把一个受控的降级变成一个完全不受控的后门** ⇒ 禁 `derive_dyn` 反而**更不安全**
2. **「名字丑」是对的**(Cap 草案 §3.2 原话)⇒ `derive_dynamic` 比 `derive_dyn` 更明显
3. **返回最宽类型是诚实的**:编译器确实不知道运行时 rights
4. **但 `narrow` 本身要过子集检查**:运行时检查 `TargetR ⊆ SrcR`,失败返回 `None`
   ⇒ 这是**运行时唯一一次权限检查** —— 且**内核侧还要再查一次**
   (用户态的检查只是加速带,Cap 草案 §6.3 已述)

### 产物

```jhyy
// 运行时派生:显式放弃编译期保证
fn derive_dynamic<T, SrcR>(src: &Cap<T, SrcR>, want: u16) -> Option<Cap<T, RWG>>

// 窄化:运行时子集检查,失败 None
fn narrow<DstR>(c: &Cap<T, RWG>) -> Option<Cap<T, DstR>>
```

- 两条都**必须在函数名里暴露「放弃了编译期保证」** ⇒ 建议加 lint 级提示
- `narrow` 的运行时检查**必须在内核侧复核**

---

## §7 D7 —— revoke 同步还是异步?传播吗?

### 事实基线

- 规范只有 `depth:u8` ⇒ **无 CDT 结构、无反向边、无 revoke 算法**
- OS 报告 §3:「单靠 `depth:u8` 只能证明 child 比 parent 更深,**不能证明 child 仍指向
  同一对象,不能证明没有兄弟 cap,不能证明映射仍然存在**」
- seL4 的两个操作是**分开的**:`CdtRevoke`(撤销**对象**)vs `CdtRetract`(撤销**单个引用**)

### ⚠️ 先纠正一条阻塞判断

`决策总纲 §6.1` 第 1 条写「阻塞 `Cap<T>` 的 T 落地时机与 CDT 设计」。
**这条阻塞判断是错的**:revoke 是**运行期**语义,`T` 的解析是**编译期**语义
⇒ 两者无依赖。⇒ **D7 不阻塞 Cap 真 T**,可以从阻塞列表里降级。

### 建议:**默认同步 + 按对象类型分级;区分 retract 与 revoke**

**理由**:
1. **同步是 object capability 模型的核心承诺**:「撤销后不再有引用」是可推理的;
   异步则要求**每一个使用点**都处理「可能已撤销」⇒ 把并发问题推给所有用户 ⇒ 不可推理
2. 但**同步对某些对象物理上不可能**:
   - `Mapping`:unmap 物理映射必须等所有使用该映射的 CPU 刷 TLB ⇒ 必须 quiesce
   - `Frame`:正在被 DMA 的帧 ⇒ 等 DMA 完成
   ⇒ ⇒ **哪些对象需要异步,是 P4a manifest 的逐类决定**,不是语言级规则
3. **传播**:revoke **沿 CDT 传播**(父撤销 ⇒ 全部后代失效)—— 这是 CDT 的定义,不是选择
4. **兄弟 cap 不受影响**:撤销一个**派生引用**不影响它的兄弟(不同引用);
   但撤销**对象**时兄弟全失效 ⇒ ⇒ **必须是两个不同的操作**

### 产物

- 两个系统调用:`retract_cap(cap)`(撤销单个引用)/ `revoke_object(cap)`(撤销对象,传播)
- **默认同步**;需 quiesce 的对象类型在 P4a manifest 里标 `async_revoke: true`
  + 声明 quiesce 机制
- 语言层:**`Cap<T>` 的类型不因 revoke 改变** ⇒ revoke 不进类型系统
- `决策总纲 §6.1` 第 1 条的「阻塞」措辞订正

---

## §8 D8 —— `ptr<phys>` 消耗 `Cap<Frame>` 吗?unmap 等所有映射消失吗?

### 事实基线

- OS 报告 §10 明确列出**两个必须尽早决定的语义选择**:map 是否消耗 frame cap;
  frame unmap 时是否等待所有映射消失
- Cap 草案 §3.3 主张 `ptr<phys>` **只能**由内建派生函数产生(`as` 转换表加禁止规则)

### 建议:**不消耗 —— 派生新 cap,原 cap 保留**

**理由**:
1. **capability 模型的核心是「可并存的授权」**:映射一个 frame 不应该让 frame 消失
   ⇒ 用户可能想 map 两次(不同 vaddr),或 map 后仍持有 frame 用于 `unmap`
2. **消耗(by value)** 会让「map → unmap → 再 map」很别扭,且与「cap 是引用」的心智模型冲突
3. **借用(`&Cap<Frame, R>`)** 在借用检查下会让长生命周期的 mapping 借用短生命周期的 cap
   ⇒ 借用检查器会咬人(而 JHYY 的借用检查还在 W-105 最小版)
4. **派生新 cap** = `derive` + `map` 两步,与现有 8 种 rights 模型一致:
   **mapping 的 rights ⊆ frame 的 rights**(编译期常量判定)

**「转移所有权」怎么表达**:用现有能力即可 —— 用户想转移就自己 `derive` 后 `drop` 原件
⇒ **不需要语言级特例**。

**unmap 是否等待**:归 D7 的分级 ⇒ **`Mapping` 标 `async_revoke: true`**
(unmap 必须等所有映射消失,否则还有 CPU 在用那个物理页)⇒ **这是 manifest 的逐类决定**。

### 产物

```jhyy
fn map_into<'f, R>(
    space: &mut Cap<AddressSpace, W>,
    frame: &Cap<Frame, R>,
    at: ptr<kernel>,
) -> Cap<Mapping, R>          // rights ⊆ frame.rights(编译期判定)
```

- `Mapping` 的 rights ⊆ `Frame` 的 rights ⇒ 编译期常量判定
- unmap 的等待语义进 P4a manifest(不进口语言)

---

## §9 D9 —— `as Cap` 逃生舱保留吗?

### 建议:**保留,但收敛**(与 D5 同批落地)

**理由**:
1. **完全禁掉是做不到的**:内核 bootstrap 阶段**确实需要**手工构造 root cap
   —— 没有更早的来源(先有鸡才有蛋)⇒ **后门在语义上不可消除,只能让它可审计**
2. ⇒ 目标不是「没有后门」,而是「**后门数量可度量、位置可审计、越权不可能**」
3. 收敛手段见 D5:`from_raw` 唯一入口 + `#[trusted]` 范围限定 +
   `unsafe_ctor_count` 进 contract section

### 产物

- 与 D5 共用产物;额外加一条:**`as Cap` 保留为 deprecated 别名**,
  迁移期给旧代码用,并在 compiler 侧发 deprecation 提示

---

## §10 D10 —— M3 message struct 的 cap 策略

### 事实基线

- IPC dispatch 表项 16B:`msg_tag:u32, handler_fn_off:u32, cap_off_count:u16, cap_off_table_off:u32`
- D16 wire:`{n_caps:u16, _pad:u16, cap_offsets:[]u16}`
- kernel 收到 IPC 后**按 cap_offsets 原地改写 `cnode_idx`**(避免 deep-copy)
- 编译器负责:tag 唯一性 / handler 签名与 message struct 双向一致 /
  cap_offsets 落在合法 `Cap<T>` 槽 / 无重叠无越界
- 内核负责:offset 边界 / slot 存在性 / rights / type_tag allowlist
  (消息可能来自**不可信**进程)

### 建议:三个子问题分别定

**子问题 1 —— grant / return:message 里的 cap 是移动还是复制?**
⇒ **移动(transfer)**。
理由:复制 ⇒ 一个 cap 两个持有者 ⇒ **revoke 语义立刻崩**(撤销谁?)⇒ 与 CDT 的对象身份模型冲突。
而 kernel 的「原地改写 `cnode_idx`」本身就是**移动**的实现
(把 sender 的 slot 索引改成 receiver 的 slot 索引 ⇒ sender 的那个 slot 被清空)。

**子问题 2 —— in-flight 消息所有权**
⇒ **发送即撤销 sender slot**。
⇒ 消息在 flight 期间持有的 cap 由 **kernel 托管**(receiver 侧的临时 slot 引用),
receiver 读走或丢弃才算最终转移。
⇒ **语言层后果:`send_cap` 按值消耗 cap** ⇒ **编译期保证 sender 之后不能再用**
(不需要运行期检查)。

**子问题 3 —— timeout**
⇒ **第一版不做**。
理由:seL4 用 notification + timeout,而 timeout 后 cap 归谁是经典的「泄漏」难题
⇒ 第一版同步阻塞 IPC **不带 timeout** ⇒ **不会产生泄漏** ⇒ 把这条登记为 ABI 已知限制。
⇒ timeout 归内核,不进语言。

### 产物

- IPC 里 cap = **移动**;`send_cap` 按值消耗
- **第一版不做借用/共享 cap**(`borrow_cap`)⇒ 需要「可共享引用」概念,第一版没有
- timeout:第一版不做,登记进 ABI §12 已知偏离

---

## §11 D11 —— 内核栈策略

### 事实基线

| 项 | 值 | 来源 |
|---|---|---|
| 自举编译器最大单函数帧 | **349232 B(341 KiB)** | v4.2.1 后实测(229 KiB 已作废) |
| 自举编译器中位帧 | **288 B** | 同上 |
| 栈预留 | 64 MB(`-Wl,--stack,67108864`) | ABI §12.7 |
| 栈槽对齐 | 只保证 8 字节 | ABI §12.6 |
| red zone / 省略帧 | 当前**不用** | grep 零命中 |
| P2 目标 | max_frame ≤ 16 KiB | 决策总纲 §4 |
| 寄存器分配理论上限 | 槽数 → ~24% ⇒ **~85 KiB** | v4.4 阶段一实测外推 |

### 建议

**① 栈大小不是编译器定的,是 loader / 内核定的。**
⇒ 编译器的作用是**把最坏情况算出来并让链接期断言** ⇒
「内核栈策略」这个决策**主要是内核侧的**(loader 选多大),编译器侧只提供事实。
⇒ 但**编译器的门需要数字** ⇒ 见 ②。

**② 把 P2 的门从「≤ 16 KiB」改成可判定的形式。**

| | 建议 |
|---|---|
| **硬门(可判定)** | **自举编译器自身(1045 个函数)的 `call_path_max × frame ≤ 64 KiB`** |
| **长期目标** | `max_frame ≤ 16 KiB` —— **保留但标注「可达性未证」** |

理由:自举编译器是本仓最坏情况(1045 函数 / 74k IL 指令 / 60k+ temp);
它的最坏调用路径若能在 64 KiB 内跑完 ⇒ **内核栈若跑得动自举编译器,就跑得动绝大多数内核代码**
⇒ 这是一个**有依据、可测、自指但可判定**的门,比「16 KiB」这种没有出处的数字强。
⚠️ 而按 341 KiB 基线,**16 KiB 单靠寄存器分配到不了** ⇒ 标注「待证」而不是假装可达。

**③ 中断栈**:独立于线程栈,**固定 4 KiB**,`#[naked]` interrupt handler 自报预算
(ABI §17.3 已有 `#[naked]`;OS 报告也要求「汇编作者必须手工给出栈预算」)。

**④ per-CPU 备份栈:不在栈策略里解决** ⇒ 归 P3.5 效果系统
(`preempt_disabled` 语义 + per-CPU 双缓冲)⇒ **从栈策略里划出去**。

**⑤ 递归深度**:递归函数**默认不允许进入内核栈路径**(链接期拒绝),
必须显式 `#[unsafe(recursive, max_depth=N)]` 声明上界
⇒ 与 P0.5 的「递归显式标记」一致。

### 产物

| 项 | 结论 | 落在哪 |
|---|---|---|
| 栈大小 | loader 选;编译器提供 `call_path_max` 事实 + 链接期断言 | OS-2(v4.7) |
| 硬门 | 自举编译器 `call_path_max × frame ≤ 64 KiB` | OS-4(v4.8.5) |
| 16 KiB | 长期目标,标注「可达性未证」 | OS-4 备注 |
| 中断栈 | 独立 4 KiB,handler 自报预算 | OS-3(v4.8) |
| per-CPU 备份栈 | 划出 → 效果系统 | OS-12(v4.13) |
| 递归 | 默认禁止进内核栈路径;`#[unsafe(recursive, max_depth=N)]` | OS-2(v4.7) |

---

## §12 D12 —— 整数之间要不要隐式提升?

### 事实基线(2026-10-30 实测)

| 写法 | 结果 |
|---|---|
| `i64 + (1 as i64)` | ✅ 通过 |
| `let x: i64 = 10;` | ✅ 通过(字面量在 let/赋值处有 coerce,`sema.jhyy:2169`) |
| **`i64 + 1`** | ❌ **报 "type mismatch in binary"** |
| `i64 < i64`(变量比变量) | ✅ 通过 ⇒ **不是比较运算符的问题** |

⇒ **同一套整数字面量,在 `let`/赋值处被 coerce,在二元运算处不。**
lang-spec §117 只写了「整数与浮点之间不允许隐式转换」,**整数之间既没写允许也没写禁止**
⇒ 这是一条**规范缺口**,不是实现 bug。

### 选项

| | 方案 | 判定 |
|---|---|---|
| F1 | 全面整数提升(C 风格) | ❌ `u32 + i32` ⇒ u64 ⇒ 引入 C 的经典溢出坑 |
| F2 | 保持现状,只把规则写进规范 | ⚠️ 不解决痛点 |
| F3 | **只在字面量位置提升** | ✅ |
| F4 | 连 `let x: i64 = 10` 也要写 `10 as i64` | ❌ 破坏现有代码,收益不成比例 |

### 建议:**F3 + 把规则写进规范**

**理由**:
1. **痛点是字面量,不是变量**:`i64 + 1` 极常见;`i64 + some_i32_var` 是**类型错误,应该报错**
   ⇒ F1 会把后者也放过 ⇒ 反而丢掉类型检查
2. **F3 是一处改动**:sema 里字面量 coerce 的逻辑**已经有**(let 位置),
   把它**复用到二元运算的操作数位置** ⇒ 而不是引入一整套提升规则
3. **F3 与现有一致性**:同一套字面量在同一处规则 ⇒ 消除「两处规则不同」的怪异

### 建议的规范条文

> 整数字面量在**期望类型已知**的位置(let / 赋值 / 函数实参 / 二元运算中另一侧为整型)
> 按期望类型解释;**两侧都是变量时不做隐式转换** ⇒ 类型不同即报错。
>
> `i64 + 1` ✅(1 按 i64 解释)· `let x: i64 = 10` ✅ · `takes_i64(1)` ✅
> `i64 + i32_var` ❌ · `i32_var + i64_var` ❌

⚠️ **与 OS-1 的实参检查有交互**:这条规则让 `takes_i64(1)` 合法 ⇒
**OS-1 的报错口径必须区分「字面量可隐式转换」与「真的类型不符」**
⇒ 两者要**同批落地**,否则实参检查会把合法的字面量调用判死。

### 产物

- lang-spec 补一节「整数上下文转换」(上述条文)
- sema:字面量 coerce 复用到二元运算 + 实参位置
- **门**:新测试 `spec_int_ctx_coerce.jhyy`
  (正向:`i64 + 1` / `let x: i64 = 10` / `takes_i64(1)`;反向:`i64 + i32_var` 必须报错)

---

## §13 拍板后的落地顺序

| 顺序 | 决策 | 依赖 | 落地位置 |
|---|---|---|---|
| 1 | **D1**(rights 偏移) | — | 改 binary-format + 加规范一致性门 |
| 2 | **D2**(revoke 位) | D1 | 改 binary-format;rights 集合定 8 种 |
| 3 | **D4**(slot generation) | D1 | 改 lang-spec §2.6 + abi §2.5 + binary-format |
| 4 | **D3**(Frame / 补 type_tag) | D1 | 改 binary-format 词汇;缺失 type_tag 登记进 P4a 清单 |
| 5 | **D12**(整数上下文转换) | — | lang-spec + sema + 新门(与 OS-1 同批) |
| 6 | **D5 + D9**(unsafe 收敛 + 逃生舱) | — | 属性 + `from_raw` + `unsafe_ctor_count` |
| 7 | **D11**(栈策略) | — | 改 OS-4 的验收门数字 |
| 8 | **D7 + D8 + D10**(revoke / map / IPC) | D4 | 语言签名 + P4a manifest 的逐类决定 |

**D5+D9 与 D12 都不阻塞任何后续版本** ⇒ 可先拍。

---

## §14 与版本轴的对应

| 决策 | 落在版本轴的哪一格 |
|---|---|
| D1 / D2 / D3 | **v4.9(OS-5,ABI 收敛)** —— 三处规范同步 + 规范一致性门 |
| D4 | **v4.14(OS-14,Cap 类型化)** —— wire 字段改名的时机在那里 |
| D5 / D9 | **v4.14(OS-14)** —— `from_raw` + `#[trusted]` 与 Cap 真 T 同批 |
| D6 | v4.14(OS-14) |
| D7 / D8 / D10 | **v4.13.5(OS-13,manifest)** 逐类决定 + **v4.14(OS-14)** 语言签名 |
| D11 | **v4.8.5(OS-4)** 的验收门数字 |
| D12 | **v4.6(OS-1)** —— 与实参检查同批 |

---

## §15 本文的不确定性

| 项 | 说明 |
|---|---|
| **D11 的 64 KiB 硬门** | 「自举编译器能跑 ⇒ 内核代码大概能跑」是**类比,不是证明**;内核可能有更深的递归或更大的帧 |
| **D4 的 generation 语义** | 跨 CNode 派生的 generation 归属是内核侧的实现细节,本文只定了「不继承」这条方向 |
| **D7 的同步性分级** | 哪些对象类型需要 async 是 manifest 的逐类决定,本文只给了判据(「需要 quiesce ⇒ async」) |
| **D3 的 type_tag 补充** | `AddressSpace` / `Mapping` 是否真的需要 cap 化的对象类型,要看内核的地址空间模型 —— 而**那部分 OS 文档已被删** ⇒ 需重新确认 |
| **D1 的门** | 「规范一致性门」只比对 Cap 布局;更广的规范一致性(其他字段)未覆盖 |

---

## Cross-ref

- [`JHYY_决策总纲.md`](JHYY_决策总纲.md) §6.1 —— 六条拍板项(本文 D7..D12)
- [`JHYY_Cap类型语义草案.md`](JHYY_Cap类型语义草案.md) §8 —— 六条拍板项(本文 D1..D6)
- [`JHYY_编译器全阶段方向与路线图.md`](JHYY_编译器全阶段方向与路线图.md) §7 —— P 阶段分期
- [`JHYY_OS_内核模型与语言需求.md`](JHYY_OS_内核模型与语言需求.md) §九 —— 22 条需求清单
- [`JHYY_设计自审_对照K框架.md`](JHYY_设计自审_对照K框架.md) —— 真遗漏 vs 框架错配
- 排期:[`../plans/v4/version-schedule.md`](../plans/v4/version-schedule.md) § 五(OS 线接入版本轴)
- 规范:[`../abis/jhyy-lang-spec-v4.0.0.md`](../abis/jhyy-lang-spec-v4.0.0.md) ·
  [`../abis/jhyy-abi-v4.0.0.md`](../abis/jhyy-abi-v4.0.0.md) ·
  [`../abis/jhyy-binary-format-v1.0.0.md`](../abis/jhyy-binary-format-v1.0.0.md)
