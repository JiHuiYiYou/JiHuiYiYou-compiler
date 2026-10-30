# JHYY `Cap<T, Rights>` 类型语义草案

> **本文定位**：`JHYY_OS_内核模型与语言需求.md`（B）与 `JHYY_编译器全阶段方向与路线图.md`（A）都把「`Cap<T>` 的 `T` 真实解析 + rights 进类型」列为最高优先级需求（B 需求清单第 1/2/3/5 项）。本文把这条需求展开成**可照着实现的语义草案**。
>
> **事实基线**：唯一实现事实来源是三份规范。凡规范未记载者标注「待确认」。本文不虚构现有实现结构。
>
> **本文与 A §4.1 的语法草案有实质分歧**，见 §7。

---

## §0 一句话结论

**rights 应当进类型参数，但必须走「内置有限集合类型」路线，不能走依赖类型路线。**

A §4.1 给的 `where new_rights <= src.rights`（`new_rights` 是运行时值却出现在类型约束里）在 JHYY 当前架构下**不可实现**——JHYY 没有 trait、没有 const 泛型、没有任何约束表达机制。本文给出**效果等价但只需增量最小**的替代方案：把 rights 做成 **8 个内置名义类型**，子集检查退化为**编译期常量位运算**，不需要引入任何约束系统。

---

## §1 rights 的类型级表示：三方案对比

### 1.1 三方案

| | 方案 A：const generic 位集 | 方案 B：内置有限集合类型 ✅ | 方案 C：phantom + where 约束 |
|---|---|---|---|
| 写法 | `Cap<Frame, 0b011>` | `Cap<Frame, Rw>` | `Cap<Frame, R> where R: SubsetOf<...>` |
| 需要的新机制 | const 泛型参数 + 常量表达式求值 | **仅需 8 个内置类型 + 一张 8 项表** | trait / bound / where 子句 |
| 与名义类型系统 | 冲突（常量不是声明名） | **相容**（仍是声明名比较，内部存掩码） | 冲突（需 bound 求解） |
| 与现有 mangling | 需新增常量编码规则 | **相容**（`<Base>$<T1>$<T2>` 直接多一段） | 需编码约束 |
| 类型等价判定 | 常量相等 | 名义比较 + 掩码相等 | 需约束求解 |
| 单态化上界 | 任意 2^16 种，失控 | **8 种/对象类型** | 失控 |
| 实现复杂度 | 中 | **低** | 高 |

### 1.2 推荐方案 B 的具体形态

R/W/G 三位 ⇒ **2³ = 8 种**，全量内置，不需要任何代数机制：

```jhyy
// 语言内置的 8 个 rights 集合类型（不是用户可定义的）
// 用户在源码里只能引用这 8 个名字，不能自定义新的集合
CapNone          // 0b000
CapR             // 0b001
CapW             // 0b010
CapG             // 0b100
CapRW            // 0b011
CapRG            // 0b101
CapWG            // 0b110
CapRWG           // 0b111
```

> 名字只是示意。**建议直接用 `R` `W` `G` `RW` `RG` `WG` `RWG` `None` 作保留标识符**——它们短、不会和用户类型撞名，且在错误信息里可读性最好。

用法：

```jhyy
let root:  Cap<Frame, RWG> = ...;
let ro:    Cap<Frame, R>   = root.derive::<R>();     // ✅ 减权，编译期通过
let bad:   Cap<Frame, RWG> = ro.derive::<RWG>();     // ❌ E0601：不能增权
let wrong: Cap<Endpoint, R> = ro.derive::<R>();      // ❌ E0602：对象类型不匹配
```

### 1.3 为什么这样最省

**类型等价只需一处改动**。JHYY 的名义类型按声明名比较；rights 集合类型的"声明名"就是那 8 个内置标识，内部各存一个 `u8` 掩码。sema 里加一张 8 项常量表即可，**不需要约束求解器、不需要 trait、不需要 const 泛型**。

**子集检查是编译期常量运算**：

```
derive::<TargetR>(src: Cap<T, SrcR>) 合法  ⟺  TargetR.mask & !SrcR.mask == 0
```

两边都是类型级常量 ⇒ 在 sema 里一条位运算判完。

**单态化上界可控**：11 类 type_tag × 8 种 rights = 88 种组合的**理论**上界，实际用到的远少。对比方案 A（2^16 种）与方案 C（任意约束组合），这是唯一不会拖垮编译时间的选择——而 JHYY 自举编译器的单函数帧已经 229 KiB，编译时间预算本就紧张。

---

## §2 rights 运算的语义规则

### 2.1 四条核心规则

| # | 规则 | 编码 | 检查阶段 |
|---|---|---|---|
| R1 | **派生只能清位，不能置位** | `child.mask ⊆ parent.mask` | 编译期 |
| R2 | **root 的 rights 是对象类型允许集的子集** | `root.mask ⊆ allowed_mask(type_tag)` | 编译期（manifest 驱动） |
| R3 | **映射类操作可附加 VM rights，但不产生新 capability rights** | 分离两套位 | 编译期 |
| R4 | **G（grant）不能由 R/W 派生得到** | 需显式授权对象 | 编译期 + 运行期 |

R4 值得单独说：`grant` 意味着"可以把这个能力再转给别人"，是**权限的放大器**。若允许 `RW → RWG` 的派生，rights 单调收缩就形同虚设。建议：**G 位只能从同样带 G 的父 cap 继承，且内核侧额外要求授权对象**。

### 2.2 `depth` 与 rights 的关系

`depth: u8`（wire offset 4）。规范未记载其精确语义，按 B §3 的解释（当前 CNode 根到 slot 的层级数）：

- 深度上限 255 ⇒ **撤销遍历的栈/队列深度有静态界**，这是个好的工程性质
- **深度溢出必须显式处理**：`derive` 时若 `depth == 255`，建议**编译期无法判定（运行时值）→ 运行期返回错误**，而不是回绕
- **深度与 rights 正交**：深度是"解析链长度"，rights 是"权限位"，两者不互相推导

### 2.3 ⚠️ 一处规范间不一致（需要你确认）

| 来源 | rights 字段 |
|---|---|
| lang-spec v4.0.0 §2.6 / abi v4.0.0 §2.5 | **3 位**：bit0=R, bit1=W, bit2=G |
| binary-format v1.0.0 §7 cap_init | **4 位**：bit0=R, bit1=W, bit2=G, **bit3=revoke** |

**这不是小事**：如果 revoke 位是 wire 的一部分，那它就是第 4 个权限维度，方案 B 的 8 种集合要变成 16 种；如果 revoke 只是 cap_init 表项的元数据（不进 `Cap<T>` wire），那 8 种不变。

> **建议：revoke 不进 `Cap<T>` wire**。持有权与撤销权是不同性质的东西——撤销通常是"我能撤销我派发出去的"，这更适合由内核按派生关系判定，而不是在 cap 上带一个位。但这需要你拍板（见 §8）。

### 2.4 ⚠️⚠️ 另一处规范间不一致（2026-10-30 新发现，**比 2.3 更硬**）

**两份锁定规范对 `Cap<T>` 的 8 字节 wire 布局不一致 —— `rights` 的字节偏移差 1。**

| 来源 | 布局 |
|---|---|
| lang-spec v4.0.0 §2.6 + abi v4.0.0 §2.5 | `cnode_idx:u32@0` · `depth:u8@4` · **`rights:u16@5`** · `padding:u8@7` |
| binary-format v1.0.0 §2（引 D6 + D23） | `cnode_idx:u32@0` · `depth:u8@4` · **`_pad:u8@5`** · **`rights:u16@6`** |

**判定依据**：lang-spec §2.6 给的构造示例
`let c: Cap = 0x0000030200000007 as Cap;   // cnode=7, depth=2, rights=R|W`
按小端展开 = `07 00 00 00 | 02 | 03 00 | 00`
⇒ 只有在 **rights@5** 的布局下才解出 `cnode=7, depth=2, rights=0b011(R|W)`;
按 binary-format 的 **rights@6** 解出来是 `rights=0x0000`、`_pad=0x03` ⇒ **示例自相矛盾**。

**为什么这条比 §2.3 更硬**：
§2.3 是「rights 有几位」（多一位不影响 8 字节总长，只是语义集合变大）；
**这条是「rights 在第几字节」** —— 凡是按字节读写 cap 的地方（IPC 原地改写
`cnode_idx`、cap_init 复制 rights 字段、`.jhyynb` 序列化）**两种布局算出的
字节位置不同** ⇒ **同一份程序用不同规范实现会静默读写错位 1 字节**。

**现状**：`Cap<T>` 的 `T` 不被解析、`.cnode_idx`/`.depth`/`.rights` 无字段访问
（lang-spec §2.6 明示）⇒ **当前没有任何代码按字节拆 cap** ⇒ 这条不一致
**目前不发作**，是纯纸面冲突。但它**必须在动 `Cap<T>` 之前裁决** ——
因为 `Cap<T>` 真 T + rights 参数化的第一步就是"按类型把 8 字节拆成字段"。

> **建议：以 lang-spec / abi 的 `rights@5` 为准**（理由：① 它是两份规范里
> 自带可验证示例的那份；② binary-format 那份是 2026-09-04 从 D6/D23 反向
> 整理的**设计稿**（未实装），lang-spec/abi 是 2026-10-24 锁定的**当前实现事实**）。
> 但**必须写进 binary-format 修订**，否则两份锁定的规范继续互相矛盾。
> ⚠️ **这需要你拍板**（见 §8）。

---

## §3 派生 API 形态

### 3.1 静态派生（首选路径）

```jhyy
// 编译期已知目标 rights ⇒ 编译期完成子集检查
fn derive<T, SrcR, DstR>(src: &Cap<T, SrcR>) -> Cap<T, DstR>
    where DstR ⊆ SrcR        // 这不是运行时约束，是编译期常量判定
```

**注意**：这里的 `where DstR ⊆ SrcR` 里的 `DstR` 是**类型参数**，不是运行时值。这与 A §4.1 的 `where new_rights <= src.rights`（`new_rights: Rights` 是运行时值）**有本质区别**，见 §7.1。

报错形态：

```
error[E0601]: capability rights escalation
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

### 3.2 运行时派生（次选，用于动态策略）

有些场景目标 rights 确实是运行时值（比如按用户输入的策略派生）。此时**无法**编译期判定：

```jhyy
// 返回最宽类型 + Option，实际权限由内核在运行时决定并由运行时查询
fn derive_dyn<T, SrcR>(src: &Cap<T, SrcR>, want: u16) -> Option<Cap<T, RWG>>

// 窄化：运行时检查 + 断言
fn narrow<DstR>(c: &Cap<T, RWG>) -> Option<Cap<T, DstR>>
```

**设计要点**：运行时派生返回**最宽**类型（`RWG`），这是"诚实的"——编译器确实不知道。之后调用方必须显式 `narrow::<R>()` 才能拿回静态保证。

> 这条路径的存在是必要的，但**必须是显式的、名字丑的**（`derive_dyn`），让读代码的人一眼看出"这里放弃了编译期保证"。

### 3.3 `ptr<phys>` 从 `Cap<frame>` 派生 ⭐

**这是 JHYY 相对 Rust 的结构优势**：Rust 加地址空间类型是从零凭空造（任何整数都能变成 `PhysAddr`），JHYY 已有 capability 底座，可以让物理指针**天然带授权溯源**。

```jhyy
// 物理指针的 rights 跟随源 cap
fn frame_phys(c: &Cap<Frame, R>)   -> ptr<phys, R>
fn frame_phys_mut(c: &Cap<Frame, RW>) -> ptr<phys, RW>

// 映射：返回新的 mapping cap，而不是 bool
fn map_into(space: &mut Cap<AddressSpace, W>,
            frame: Cap<Frame, R>,
            at: ptr<kernel>) -> Cap<Mapping, R>
```

**强制机制（最小改动）**：在 sema 的 `as` 转换表里加一条禁止规则——

```
整数 / 任意指针  --as-->  ptr<phys>     ❌ E0603
```

即：**`ptr<phys>` 只能由内建派生函数产生，不能由 `as` 凭空构造**。这是整个方案里性价比最高的一条——改动量是 sema 表里加一行，收益是物理地址越权路径被彻底堵死。

```
error[E0603]: cannot construct `ptr<phys>` by cast
  --> src/main.jhyy:8:20
   |
 8 |     let p: ptr<phys, RW> = 0x1000 as ptr<phys>;
   |                            ^^^^^^^^^^^^^^^^^^^
   |
   = note: physical addresses carry capability provenance
   = help: obtain one from a frame capability: `frame_phys(&my_frame_cap)`
```

### 3.4 `ptr<phys>` 与 `ptr<io>` 必须分开

B §10 主张分开，**采纳**。理由不是类型洁癖，而是**副作用与 ordering 不同**：

| 类型 | 语义 | 默认行为 |
|---|---|---|
| `ptr<phys, R>` | 普通 RAM 物理地址 | 可缓存 |
| `ptr<io, R>` | MMIO 设备寄存器 | **默认 volatile**、不合并访问、**禁止推测读** |

推测读（speculative load）对 device register 是致命的——读一次可能就有副作用。`ptr<io>` 必须在类型层标记，让 codegen 知道不能重排、不能合并、不能投机。

```jhyy
// MMIO 寄存器块：volatile 是类型的一部分，不是字段修饰符
let uart: ptr<io, RW> = mmio_region(&uart_cap);
```

### 3.5 `T` 的取值域：与 type_tag 的映射

cap_init 有 11 个 type_tag。建议语言侧定义 11 个对应的**对象标记类型**（`PhantomData` 风格的 ZST 或纯标记）：

| type_tag | 值 | 语言侧类型 | 说明 |
|---|---|---|---|
| endpoint | 0 | `Endpoint` | IPC 端点 |
| page | 1 | `Page` | 地址空间映射页 |
| framebuffer | 2 | `Framebuffer` | 连续显存 |
| console | 3 | `Console` | 传统输出 |
| file | 4 | `File` | 持久数据 |
| shm | 5 | `Shm` | 共享内存 |
| compositor | 6 | `Compositor` | 事务提交 |
| surface | 7 | `Surface` | 绘制目标 |
| seat | 8 | `Seat` | 输入聚合 |
| buffer | 9 | `Buffer` | 可共享像素缓冲 |
| endpoint_focus | 10 | `Focus` | 焦点 token |

**待确认**：`Page` 与 `Frame` 的关系。规范里 type_tag=1 是 `page`，但 B 报告多处用 `Cap<Frame>` 讨论物理页派生。这两者是同一个东西还是"page=映射单元 / frame=物理页"？**必须明确**，否则 `frame_phys` 的签名写不出来。

---

## §4 与现有 `as Cap` 构造语法的兼容与迁移

### 4.1 现状

lang-spec §2.6：**唯一**构造方式是 8 字节整型字面量 + `as`：

```jhyy
let c: Cap = 0x0000030200000007 as Cap;   // cnode=7, depth=2, rights=R|W
```

### 4.2 问题

类型化之后，这个语法是**直通后门**：任何人都能凭空造出任意 `Cap<Frame, RWG>`。B §5 已经指出：amd64 上 slot 索引可自由复制、可序列化，没有 provenance 元数据时无法区分合法 slot 与巧合整数。

### 4.3 建议：保留，但必须显式 unsafe

**不要废弃**（会破坏现有代码，且内核 bootstrap 阶段确实需要手工构造 root cap），但要求显式标注：

```jhyy
// 方案：引入最小 unsafe 概念（JHYY 目前没有 unsafe）
let root: Cap<Frame, RWG> = unsafe {
    Cap::<Frame, RWG>::from_raw(0x0000030200000007)
};
```

三个配套要求：

1. **`from_raw` 是唯一入口**，`as Cap` 保留一个 deprecated 别名指向它（给迁移期用）
2. **`#[trusted]` 模块级标注**：允许整个模块豁免，供 kernel bootstrap 用
3. **编译器可输出"unsafe cap 构造点清单"**，进 `.jhyynb` contract section，让 loader 知道这个二进制有多少处绕过

第 3 条是关键：**把后门变成可审计的事实**，而不是假装它不存在。这与本项目"事实基线"的文档哲学一致。

### 4.4 兼容性风险（待确认）

规范**没有 ABI versioning 方案**。改 `Cap<T>` 的语义是否破坏现有二进制？建议：

- 在 header 的 `abi_version: u8` 字段上 bump（binary-format §4 已有此字段，正好用上）
- **旧二进制不兼容**，但当前没有需要长期兼容的旧二进制存量，代价接近零

---

## §5 编译器各阶段影响清单

| 阶段 | 改动 | 复杂度 |
|---|---|---|
| **Lexer** | 新增保留字 `R`/`W`/`G`/`RW`/...（或 `CapR` 等）；若引入 `unsafe` 需新关键字 | 低 |
| **Parser** | 解析 `Cap<T, R>` 双参数；解析 `ptr<phys, R>`；`derive::<T>()` turbofish 语法 | 中 |
| **Sema** | ① 8 项 rights 常量表 ② 类型等价加入 rights 掩码比较 ③ `derive` 的子集检查（位运算）④ `as` 转换表加禁止规则（整数→`ptr<phys>`）⑤ unsafe 块标注 | **中（核心工作量）** |
| **Mangling** | `<Base>$<T1>$<T2>` 直接扩展——rights 作为第二个参数拼进去，天然确定性、可复现 | 低 |
| **IL** | `Cap<T,R>` 是 8 字节标量（与 `l` 同承载），**建议不新增 IR 概念**，只在类型侧保留标记供后续 pass 消费 | 低 |
| **后端** | 无特殊处理（8 字节标量走 `l`）；`ptr<io>` 需要**禁止重排/合并/投机**的 codegen 标记 | 中 |
| **链接 / `.jhyynb`** | cap_init 由 `#[cap_constructor]` 或顶层声明生成；`provenance_seed_off` 填充；contract section 输出 capability facts | 中 |

### 5.1 capability facts schema（写进 `.jhyynb` contract section）

```c
struct CapContract {
    cap_type_count:      u16,     // 该 binary 使用的 Cap<T,R> 组合数
    // 每种组合一条：
    //   { type_tag:u32, rights_mask:u16, monomorphic_count:u32 }
    unsafe_ctor_count:   u32,     // 【关键】unsafe 构造点数量
    unsafe_ctor_offs:    []u32,   // 各构造点的 .text 偏移，供审计
    derive_edges:        []u32,   // 静态派生边（src_type_tag → dst_type_tag）
    ptr_phys_sites:      []u32,   // ptr<phys> 派生点
}
```

**`unsafe_ctor_count` 是最有价值的一个字段**——它把一个"后门"变成可度量、可设阈值的指标。CI 里可以断言：`kernel.efi` 的 `unsafe_ctor_count ≤ N`，且只在 bootstrap 模块。

---

## §6 外部对标

### 6.1 Pony 的 reference capabilities —— 最值得抄的代数

Pony 的 `iso` / `trn` / `ref` / `val` / `box` / `act` 是**类型级权限**最成熟的工业实现。三个可借鉴点：

1. **deny 性质**：Pony 的能力是"拒绝什么"而不是"允许什么"——`val`（不可变）的语义是"谁都不能写"，这让组合规则自然单调
2. **viewpoint adaptation**：通过一个能力看另一个能力时，结果由两者的代数规则决定（如通过 `box` 看 `iso` 得到 `val`）——这正是 JHYY 需要的"派生后 rights 怎么算"
3. **单调收缩是内建的**：Pony 的 `iso → trn → ref → val` 方向不可逆

**不该抄**：Pony 的完整代数有 6 个能力 × 组合矩阵，是为 actor 并发设计的。JHYY 只需 8 种 rights 集合，**不要引入 viewpoint adaptation 的完整代数**——它的学习曲线会重演 Rust 借用检查的采用阻力。

### 6.2 Rust const generics —— 抄"最小可用"，不抄完整机制

Rust 的 const generics 走了很长的路（`min_const_generics` 先稳定最小子集，复杂常量表达式长期未稳）。教训是：**常量表达式在类型系统里是个坑**。

JHYY 应当**完全不引入 const 泛型**，而是把 rights 做成有限内置类型。这绕开了整个坑，代价只是失去"用户自定义 rights 组合"的能力——而 R/W/G 三位本来也不需要用户自定义。

### 6.3 seL4 CDT —— 抄"派生关系是真源"，不是 CNode 树

seL4 的撤销走 **CDT（Capability Derivation Tree）**而非 CNode 索引树：派生出的 cap 与父 cap 指向同一内核对象，从 CNode 根 DFS **会漏掉跨 CNode 别名**。

对 JHYY 的直接结论（与 B §3 一致）：

- **对象反向边是语义真源**，`depth` 只作为派生证明与遍历界
- `derive` 必须在内核侧登记派生边，否则 revoke 不精确
- rights 单调收缩由 `cap_derive` 系统调用强制——**语言层的编译期检查是加速带，不是替代品**

### 6.4 CHERI —— 明确不承诺

CHERI 的 capability 是硬件保护的指针式原语（带 tag bit、bounds、permissions、object type），Clang 用 `__capability` 限定符表达。

**amd64 上没有 CHERI**。因此：

- `Cap<T,R>` 是 **object capability**（内核对象存在 + 调用者拥有 slot），**不是** fat-pointer 空间能力
- 编译器可以说"合法程序不会在内核上下文任意解引用用户指针"，**不能**说"所有物理地址访问受硬件 capability 约束"
- 但**对象模型应当保持可映射到 CHERI**（预留 version/provenance 位），未来若有 CHERI 后端可直接落下

---

## §7 与既有判断的分歧

### 7.1 ⚠️ 反对 A §4.1 的依赖类型写法

A §4.1 给的是：

```jhyy
type Rw = #cap_r | #cap_w;
fn derive_frame(src: &Cap<Frame, All>, new_rights: Rights)
    -> Option<Cap<Frame, new_rights>>     // ← new_rights 是运行时值
    where new_rights <= src.rights        // ← 运行时值出现在类型位置
```

**这在 JHYY 当前架构下不可实现**，理由有三：

1. `new_rights` 是函数参数（运行时值），出现在返回类型 `Cap<Frame, new_rights>` 里 —— 这是**依赖类型**，需要 dependent type 或至少 const 泛型 + 复杂常量表达式。JHYY 连 trait 都没有。
2. `where new_rights <= src.rights` 需要**约束求解器**——同样需要一套 JHYY 没有的机制。
3. 更根本的：`src.rights` 里的 `src` 是运行时值，它的 rights 位来自内存，编译器根本无从静态读取。

**替代方案（§1–§3 的推荐）**效果等价且只需：

- 8 个内置类型 + 一张常量表
- `derive::<DstR>()` turbofish 语法
- sema 里一条位运算判定

**唯一失去的能力**：无法表达"运行时决定的 rights"。这个由 §3.2 的 `derive_dyn` 显式兜底——而且把"放弃了编译期保证"这件事**暴露在函数名里**，比隐式通过更有价值。

### 7.2 rights 是否真需要进类型参数？（有保留地支持）

**支持**，但理由要说准：不是"类型参数更高级"，而是**只有进类型参数才能参与名义类型比较**。

若 rights 只作为 phantom 字段或注解：
- 两个 `Cap<Frame>` 一个只读一个可写，类型相同 ⇒ 可以互相赋值 ⇒ 检查失效
- 注解无法进入函数签名做传播

所以必须进类型参数。**但要克制**：只做 8 个内置集合，不做任意代数（§1.2）。这样既拿到了"只读 cap 传不进需要写的函数"，又避免了 Rust 借用检查式的学习曲线。

### 7.3 `ptr<phys>` 派生约束的强度上界（对 B §10 的补充）

B §10 主张 `ptr<phys>` 从 `Cap<frame>` 派生，**方向完全同意**，但要说清**它防住什么、防不住什么**：

**能防住**：
- 凭空造物理地址（`0x1000 as ptr<phys>` 编译失败）
- 用 endpoint cap 去访问物理内存（对象类型不匹配）
- 只读 frame 派生出可写 phys（rights 跟随）

**防不住**：
- 用户态把 8 字节 slot **复制**给另一个进程（软件 capability 可序列化——这是 object capability 模型的固有边界）
- slot 释放后被复用，旧 cap 指向新对象（**需要 slot version**，规范未记载）
- 内核本身的 bug（capability 模型不保护内核）

前两条不是缺陷，是**模型边界**：object capability 保证的是"授权不会凭空增加"，不是"用户不会自愿放弃隔离"。B §3 已指出这一点——compositor 把 full-framebuffer cap 交给应用，内核没有义务阻止。

> **因此在语言承诺里必须写清楚**：JHYY 保证「授权单调收缩 + 对象类型不匹配不可编译」，**不保证**「用户态不会主动泄露能力」。把这条写进规范，就不会出现"长得像 Rust 却不提供 Rust 保证"的虚假安全感（这是 A/B 共同指出的头号风险）。

---

## §8 需要你拍板的事

| # | 待决 | 影响 |
|---|---|---|
| 1 | **revoke 位是否进 `Cap<T>` wire？**（lang-spec 3 位 vs binary-format 4 位） | 决定是 8 种还是 16 种 rights 集合 |
| 2 | **`Page` 与 `Frame` 是否同一个对象？** | `frame_phys` 签名写不出来 |
| 3 | **是否引入 `unsafe` 关键字？** | 决定 `as Cap` 后门的收敛方式 |
| 4 | **slot version 方案** | 决定旧 cap 能否指向复用后的新对象（当前规范无记载，是 UAF 隐患） |
| 5 | **`derive_dyn` 是否允许存在？** | 允许 = 有逃生舱但也有效力缺口；禁止 = 某些动态策略写不出来 |
| **6** | **`Cap<T>` 8 字节 wire 里 `rights` 在第 5 还是第 6 字节？**（lang-spec/abi `rights@5` vs binary-format `rights@6`，见 §2.4） | **阻塞 `Cap<T>` 真 T 的第一步**（按类型拆字节）。建议以 lang-spec/abi 为准并修订 binary-format |

---

## §9 最小落地顺序（建议）

| 步 | 动作 | 产出 |
|---|---|---|
| 1 | **冻结 capability objects manifest**（11 个 type_tag 各自的允许 rights 集、owner、init phase） | 一份表，消除后续返工 |
| 2 | 引入 8 个内置 rights 类型 + sema 常量表 | `Cap<Frame, R>` 可写，且 `Cap<i32>` ≠ `Cap<i64>` |
| 3 | `derive::<DstR>()` + 子集检查 + E0601/E0602 | 增权不可编译 |
| 4 | `as` 转换表禁止整数→`ptr<phys>` + E0603 | 物理地址越权路径堵死 |
| 5 | `unsafe` + `from_raw` + `unsafe_ctor_count` 事实输出 | 后门可审计、可设阈值 |
| 6 | `#[ipc_handler]` 契约与 cap_offsets 位图 | IPC 静态检查闭环 |

第 4 步性价比最高：改动量是 sema 表里加一行，收益是堵死一整类越权。
