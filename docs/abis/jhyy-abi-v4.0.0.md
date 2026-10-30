# JHYY ABI 规范 v4.0.0

**状态**：v4.0.0 —— v4 世代的 ABI 基线，随 `v4.0.0 final` promote 一同锁版
**取代**：`jhyy-abi-v1.0.0.md`（已归档至 git 历史）
**事实基线**：本文件只陈述**当前代码确实实现**的行为。凡未实装或与标准平台 ABI 不一致者，写入 [§ 12「已知偏离与未实装项」](#12-已知偏离与未实装项)，不写进正文。
**配套**：[`docs/abis/jhyy-lang-spec-v4.0.0.md`](./jhyy-lang-spec-v4.0.0.md)

> **本版相对 v1.0.0 的最大变化**：QBE 已从构建链移除（v3.1.0）。v1.0.0 里那套「QBE IL 映射表」全部作废 —— 规范改以**机器级术语**（寄存器、栈、section、指令）表述。

> **读法**：正文描述的是**实现**（含实现自身的缺陷），不是理想 ABI。与标准 SysV / MS x64 不一致的地方一律在 § 12 显式登记。

---

## 1. 目标平台

| 目标三元组 | 调用约定 | 运行时 | 输出容器 |
|---|---|---|---|
| `amd64_win`（默认） | MS x64 | hosted（链接 C 运行时） | ⚠️ 见下 |
| `amd64_win_freestanding` | MS x64 | freestanding（UEFI） | ⚠️ 见下 |
| `amd64_sysv` | SysV AMD64 | hosted | ⚠️ 见下 |
| `amd64_sysv_freestanding` | SysV AMD64 | freestanding | ⚠️ 见下 |

- ⚠️ **输出容器格式不由 `--target` 决定**，而由宿主机工具链的 `ld` 决定（`link_with_gcc` 没有 target 参数）。表中的 PE/ELF 只是各目标的**惯例**产出。见 [§ 12.9](#abi-12-9)。
- `amd64_win` 与 `amd64_win_freestanding` 的**调用约定逐字节相同** —— freestanding 只改变链接方式，不改变寄存器约定。`amd64_sysv` 与 `amd64_sysv_freestanding` 同理。
- 架构仅 x86-64。aarch64 / riscv64 未实装。
- 四个目标全部走自托管 amd64 后端（`target_backend_mode` 全部返回 `BACKEND_SELF`），没有 QBE 回退路径。
- ⚠️ **两个 freestanding 目标只切换「调用约定归属 + 入口钩子」，不切换链接方式。** 链接行是按源文件的 `#[no_std]` 属性分支的（见 § 7），跟 `--target` 无关。

### 1.1 编译流水线

```
.jhyy → lexer → parser → sema → IL（进程内）→ 自托管 amd64 后端 → .s（GAS / AT&T）→ gcc + ld → .exe / ELF
```

- **QBE 不在流水线中**。`run_qbe` 是 fatal-stub，被调用即报错退出。
- IL 到汇编是**进程内直传**（in-memory，不落盘），`.il` 仅在 `JHY_WRITE_IL=1` 时额外落一份供人检视。
  - `JHY_WRITE_IL` 只影响「要不要落一份 .il」，**不再影响走哪条 emit 路径**（v4.0.8 / W-097 统一，避免同一个 flag 悄悄换实现路径导致跨代比对出假差异）。
- 汇编器与链接器是外部 `gcc` / `ld`。
- ⚠️ **命令行只接受一个输入文件**；多余的 `.jhyy` 参数被静默忽略。多文件通过 `import` 组合（见语言规范 § 1.2）。

---

## 2. 类型布局

### 2.1 基础类型

| JHYY | sizeof | alignof | 机器宽度 | 备注 |
|---|---|---|---|---|
| `i8` / `u8` | 1 | 1 | byte | 加载到 32 位后符号/零扩展 |
| `i16` / `u16` | 2 | 2 | word(16) | 同上 |
| `i32` / `u32` | 4 | 4 | long(32) | |
| `i64` / `u64` | 8 | 8 | quad(64) | |
| `f32` | 4 | 4 | single | IEEE 754 binary32 |
| `f64` | 8 | 8 | double | IEEE 754 binary64 |
| `bool` | 1 | 1 | byte | ⚠️ 字面量只有 0 / 1，编译器**不做归一化** |
| `char` 字面量 | 4 | 4 | long(32) | **不是独立类型**，字面量的类型是 `i32`，值为 Unicode codepoint |
| `()` | 0 | 1 | — | 零大小类型 |

- 有符号整数溢出是**定义行为**：二进制补码环绕，无运行时检查。
- `i8/i16/u8/u16` 在寄存器中以 32/64 位承载，读写内存时做符号/零扩展。
- ⚠️ `bool` 存 1 字节，但来自算术 / 内存的值**不被归一化到 0/1**；只有字面量保证是 0/1。

### 2.2 复合类型

| 类型 | sizeof | alignof | 布局 |
|---|---|---|---|
| `*T` | 8 | 8 | 64 位平面地址；空指针为整数 0；指针算术步长为 `sizeof(T)` |
| `fn(...)` 函数指针 | 8 | 8 | |
| `[*]T` 切片 | 16 | 8 | `{ data: *T @0, len: i64 @8 }` |
| `[T; N]` 定长数组 | `N × sizeof(T)` | `alignof(T)` | 元素连续，无 padding |
| `struct` | 见 § 2.3 | | |
| `enum` | 见 § 2.4 | | |
| `&T` / `&mut T` | 8 | 8 | 单指针；`is_mut` 是编译期标记，不占内存 |
| `Cap<T>` | 8 | 8 | 见 § 2.5 |
| `PhantomData<T>` | 0 | 1 | ZST，不占 struct 槽位 |

### 2.3 struct 布局

```
offset = 0; max_align = 1
for each field（按声明顺序）:
    al = alignof(field_type)
    if al > max_align: max_align = al
    offset = align_up(offset, al)
    field.offset = offset
    offset += sizeof(field_type)
total_size = align_up(offset, max_align)
```

- **名义类型**：两个 struct 仅当是同一声明才视为同类型（按**声明名**比较，不是按布局）；字段布局相同但名字不同 = 不同类型。
- **嵌套 struct 内联展开**为单层布局（内联展开，占父结构体偏移，保留自身 padding）。
- `PhantomData<T>` 字段不推进 offset，不影响 `max_align`（靠 ZST 属性自然成立，无特判）。

### 2.4 enum 布局

```
tag_size = 4                                   // i32 tag，offset 0
total_align    = max(4, max_payload_align)
payload_offset = align_up(4, max_payload_align)
total_size     = align_up(payload_offset + max_payload_size, total_align)
```

```
+--------+-----------------+--------------------+
| tag    | padding         | payload            |
| i32 @0 | （可变）        | max_payload_size   |
+--------+-----------------+--------------------+
```

- 变体 tag 从 0 起按声明顺序递增。
- **名义类型**，同 struct。
- ⚠️ `alignof(enum)` 硬编码返回 **4**，与上面 `total_align` 的计算不一致 —— 见 [§ 12.2](#abi-12-2)。
  - 注：这是编译器内部 `type_align()` 的行为。**语言级的 `alignof(T)` 表达式当前未实装**（见语言规范 § 2.8 / 附录 B），所以这条不构成对外承诺。

### 2.5 `Cap<T>`

```
offset  size  field        type
0       4     cnode_idx    u32     CSpace slot index
4       1     depth        u8      CDL 深度
5       2     rights       u16     bit0=R, bit1=W, bit2=G
7       1     padding      u8      零
```

- 小端序。
- ⚠️ **`T` 当前不被解析** —— `Cap` 的 inner 被硬编码成 `i32`，所以 `Cap<i32>` 与 `Cap<i64>` 是同一个类型。语言规范里「名义相等按 `elem` 区分」的说法在当前实现下不成立。
- 不提供 `.cnode_idx` / `.depth` / `.rights` 字段访问语法；构造走 8 字节整型字面量 + `as Cap` 转换。

### 2.6 `volatile T`

- `volatile` 只修饰**基础类型**；修饰 struct / 指针 / 数组 / 切片是编译错误；`volatile volatile T` 是编译错误。
- **布局与 `T` 完全一致**，`volatile` 不改变大小、对齐、传参方式。
- 语义只保证**单线程内**每次 load 命中内存、每次 store 写回内存、不重排；**跨线程**序需配合 `fence_*`。

---

## 3. 调用约定

### 3.1 MS x64（`amd64_win` / `amd64_win_freestanding`）

| 规则 | 内容 |
|---|---|
| 整型/指针参数 | 前 4 个：`RCX`、`RDX`、`R8`、`R9`；其余走栈 |
| 浮点参数 | 前 4 个：`XMM0`–`XMM3`；其余走栈 |
| 返回值 | 整型/指针：`RAX`；浮点：`XMM0` |
| Shadow space | 调用者在栈上预留 32 字节（另有栈参时为 `32 + extra_args×8`，再 16 字节对齐） |
| 栈对齐 | `call` 前 16 字节对齐 |
| 栈探测 | 单帧 > 4096 字节时插入 `___chkstk_ms`（判据含 32 字节 shadow） |
| 栈预留 | 链接行 `-Wl,--stack,67108864`（64 MB） |

**整数与浮点实参共享同一个位置计数器**（MS x64 的核心规则）：

| 槽位（1-based） | 整数寄存器 | 浮点寄存器 |
|---|---|---|
| 1 | `RCX` | `XMM0` |
| 2 | `RDX` | `XMM1` |
| 3 | `R8` | `XMM2` |
| 4 | `R9` | `XMM3` |
| ≥ 5 | 栈 | 栈 |

第 n 个实参无论整数浮点都占**同一个槽位** —— `fn f(a: f64, b: i32)` ⇒ `a` 在 XMM0、`b` 在 **EDX**（不是 ECX）。

**Callee-saved 寄存器**（`RBX`、`RBP`、`RDI`、`RSI`、`RSP`、`R12`–`R15`、`XMM6`–`XMM15`）在**约定层面**由被调用方保存，但当前后端**只保存 `RBP`**，其余全部 spill 到栈帧（全 spill 策略）。约定的可观察行为成立，代价是栈帧显著偏大 —— 见 [§ 12.7](#abi-12-7)。

### 3.2 SysV AMD64（`amd64_sysv` / `amd64_sysv_freestanding`）

| 规则 | 内容 |
|---|---|
| 整型/指针参数 | 前 6 个：`RDI`、`RSI`、`RDX`、`RCX`、`R8`、`R9`；其余走栈 |
| 浮点参数 | 前 8 个：`XMM0`–`XMM7`；其余走栈 |
| 返回值 | 见 § 3.5 |
| Shadow space | **无** |
| 栈对齐 | `call` 前 16 字节对齐 |
| 栈探测 | 无 |

**整数与浮点是两个独立 bank** —— 整数实参按出现顺序占 `rdi`/`rsi`/`rdx`/`rcx`/`r8`/`r9`，浮点实参按出现顺序占 `xmm0`–`xmm7`，**两个 bank 各自编号、互不影响**。这与 MS x64 的共享位置计数器**正好相反**（见 § 3.1）。

**struct / 聚合类型参数分类**：

| 条件 | 传递方式 |
|---|---|
| `sizeof ≤ 16` | 按 eightbyte 切分分类（INTEGER / SSE），最多 2 个 eightbyte 进寄存器，其余进寄存器或栈 |
| `sizeof > 16` | **MEMORY class** —— 整体落在栈上 |

- eightbyte 宽度：第 0 个按该 eightbyte 内字段的实际覆盖取 4 或 8 字节；⚠️ **第 1 个及以后恒为 8 字节**（实现把字段的**绝对**结束偏移与字面量 4 比较，所以 12 字节 struct 的第二个 eightbyte 被当成 8 字节，与 gcc 的 INTEGER(4) 不符）—— 见 [§ 12.11](#abi-12-11)。
- **MEMORY class 参数与「寄存器溢出参数」混排时编译期报错**，不静默生成错误代码。这是 [§ 12.4](#abi-12-4) 记录的能力边界：一部分合法 SysV 用法当前无法编译。
- ⚠️ 溢出的 `f64` 栈参需要 16 字节对齐，caller 只按 8 递增 —— 见 [§ 12.12](#abi-12-12)。

### 3.3 聚合类型传参（Win）

| 参数类型 | 传递方式 |
|---|---|
| `struct` | 调用者在栈上建副本，逐字段复制（含嵌套 struct 递归），传副本地址（一个 `l` 参数） |
| `enum` | 传**一个 `l`**（enum 值自身槽的地址），**不建副本** |
| `[T; N]` | 传**一个 `l`**（数组自身地址），**不建副本**（实质按引用） |
| `[*]T` 切片 | 16 字节槽 `{data, len}`，但**只传一个 `l` 指针**指向该槽（Win 与 SysV 均如此） |

⚠️ 只有 `struct` 真正建副本。`enum` / `[T; N]` / 切片是按地址传递。

### 3.4 参数求值顺序

**未定义**，由编译器决定。当前实现为从左到右。

### 3.5 返回值

| 返回类型 | 约定 |
|---|---|
| 整型 / 指针 / `&T` | `RAX` |
| `f32` / `f64` | `XMM0` |
| `struct` / `enum` | **隐式 sret**：调用者分配返回槽，作为**隐藏的第 0 个参数**传入（**在寄存器里**：Win `%rcx` / SysV `%rdi`）；被调用方写入后裸 `ret` |
| `[T; N]` | ⚠️ **不走 sret**：callee 自建 16 字节槽，`RAX` 返回其地址 |
| `()` | 无返回值，函数尾部裸 `ret` |

- sret 槽大小 = `max(4, sizeof(T))`。
- ⚠️ **sret 在所有目标上无条件启用，无大小阈值**。这与 SysV ABI 不一致（SysV 应为 ≤16 字节的聚合类型用 `RAX:RDX` / `XMM0:XMM1` 返回）—— 见 [§ 12.1](#abi-12-1)。

### 3.6 名称修饰

| 情形 | 符号形式 |
|---|---|
| 普通函数 | `<name>`（IL 里写作 `$name`，落到汇编符号时去掉 `$`） |
| 模块内函数 | `<mod>__<name>`（跨模块限定调用 `mod::fn()`） |
| 泛型实例 | `<Base>$<T1>$<T2>...`（例如 `max$i32`、`Pair$i32$f64`） |
| 模块内泛型实例 | `<mod>__<Base>$<T1>$<T2>`（模块前缀优先） |
| 闭包 | `__closure_<N>`（合成函数名，N 为每次编译单调递增的计数器 ⇒ 产物可复现） |
| `extern fn` | **原样**，不加前缀、不加修饰 |

- 无重载支持。
- 泛型修饰名由 parser 按源码顺序拼出，**不含指针地址或哈希**，因此是确定性的。
- ⚠️ `extern fn` 有 **W-069 回落**：若同一编译单元里存在同名的非 extern 函数，改用预 mangled 名。

---

## 4. 栈帧与内存模型

### 4.1 栈帧

```
prologue:
    pushq %rbp
    movq  %rsp, %rbp
    [ movq $N, %rax ; call ___chkstk_ms ]   ; 仅 Win，且 N > 4096
    subq  $N, %rsp

epilogue:
    movq  %rbp, %rsp
    popq  %rbp
    ret
```

- 帧大小 `N`：
  - Win = `32 + align_up(stack_need, 16)`
  - SysV = `align_up(stack_need, 16)`
  - 其中 `stack_need` = `frame_size + addr_pool_reserve`（`addr_pool_reserve ≥ 64`）；`frame_size` = 该函数所有局部槽的总量。
- **只保存 `RBP`**。所有其他寄存器值 spill 到栈槽（全 spill）。
- 局部变量槽偏移 = `-(32 + t*8)`（Win，含 32 字节 shadow）；SysV 走 target-aware 变体。

### 4.2 栈槽分配

- 栈槽按 `(size + 7) & -8` 做 **8 字节对齐**。通用槽**没有 4 字节下限**（size=1 → 8）；4 / 8 / 16 字节的对齐分级只出现在 **alloc 池**（`ir_emit_alloc` 按 size 选）。
- ⚠️ **两个池，不是三个**：公式 / 临时槽池 + **合并后的 alloc + address-holder 单调池**。
  - v4.0.8（W-097 / W-098）把原本的 value(alloc) 池与 address-holder 池合并成**单一单调递减池**：两者的深度此前都靠 pre-scan 估算，估算偏小就会重叠，而 AH 分配与 value 分配在指令流里是交错的 —— 没有任何「起点」能同时避开两者。
  - address-holder 是**语义**属性（temp_holds_address bitmap），跟槽位无关；合并后槽位天然互斥，这类重叠从结构上消失，**也不再依赖任何 per-fn 上界估算准不准**。
- ⚠️ 无 16 字节对齐保证 —— 当前类型系统里没有要求 16 字节对齐的类型，故未触发（见 [§ 12.6](#abi-12-6)）。

### 4.3 堆

编译器自身不实现堆。用户通过 `std::arena`（malloc 分块 + bump 分配）或 `extern fn malloc` 管理。无 GC、无自动析构。

---

## 5. 浮点 ABI

- `f32` / `f64` 参数与返回值走 SSE 通道：`XMM0`–`XMM3`（Win）/ `XMM0`–`XMM7`（SysV），返回用 `XMM0`。
- 超出寄存器配额的参数回退到栈。
- XMM 寄存器分配器在每次调用前重置（同时清 `xmm_arg_count` / `int_arg_count` / `stack_arg_offset`）。
- ⚠️ **浮点立即数在 IL 里是十进制文本**（`d_1.0` / `s_2.5`），**不是** IEEE 754 位型；位型转换在后端 emit 时做，汇编层用 `movabsq $BITS,%rax ; movq %rax,mem`（f64）/ `movl $BITS,mem`（f32）落地。**不使用** `.long` / `.quad`（那两条只用于 `data` 字节数组）。
- 浮点比较按操作数宽度发射对应助记符（`ucomisd` / `ucomiss`）。
- **NaN 的 ordered 语义已实装**：比较走 `ucomis*` + `set<cc>`，并追加**有序守卫** —— `==` 用 `setnp`（PF=0 ⇒ 有序）与结果**取与**，`!=` 用 `setp`（PF=1 ⇒ unordered）与结果**取或**，序比较（`<` `>` `<=` `>=`）同样取与守卫。⇒ 有 NaN 参与时 `==` 为 `false`、`!=` 为 `true`，符合 IEEE 754。`struct` 的浮点字段比较走同一条 `ceqd` / `cned` 路径，语义一致。

---

## 6. FFI

| 方向 | 支持的参数类型 | 支持的返回类型 |
|---|---|---|
| JHYY → C | 全部基础类型、`*T`、`bool` | 同上 |
| C → JHYY | 同上 | 同上 |

- `extern fn` 只声明、不生成函数体，链接期由 `ld` 解析符号。
- **不支持**：struct / enum 按值跨 FFI 边界、变参函数（JHYY 侧需逐参数列出）、回调函数。
  - ⚠️ `extern fn` 的参数 / 返回类型**不做编译期限制**：声明 struct 参数能编译通过，但实际按地址传，与 C ABI 不符（静默不符，无报错）。
- 字符串字面量是 UTF-8 字节序列，存放在 **`.data`** 段（GAS 默认数据段；编译器从不发 `.section .rodata`），以 NUL 结尾（`.byte 0`），作为 `*u8` 传给 C，兼容 C `char*`。
- ⚠️ **Windows 控制台 UTF-8 输出不由运行时设置** —— `runtime.c` 的 `main` 只做 argv 重解码 + 调 `main_jhyy`，**没有** `SetConsoleOutputCP(65001)` 调用。需要 UTF-8 终端得自行 `chcp 65001`（见 [§ 12.14](#abi-12-14)）。

---

## 7. 程序入口与链接

| 模式 | 入口符号 | 说明 |
|---|---|---|
| hosted | `main_jhyy` | C 运行时 `main` 调用 `main_jhyy(argc, argv)`，其返回值作为进程退出码 |
| `#[no_std]` | `main` | 链接行 `-nostartfiles -nodefaultlibs -Wl,--entry=main -lgcc` |

- `#[no_std]` 不链接 C 运行时启动文件；`-lgcc` 仅提供 `___chkstk_ms` 等编译器内建，不含 C 运行时。
- `#[no_std]` 模式下 `fn main` 必须存在，否则编译错误（`error: #[no_std] module must define 'fn main()'`）。
- ⚠️ 链接行有两条分支，**判据是源文件里有没有 `#[no_std]`，不是 `--target`**：
  - 无 `#[no_std]` → 链 `runtime.o` + `helpers.o`（C 运行时 bridge）
  - 有 `#[no_std]` → **不链**上面两个，加 `-nostartfiles -nodefaultlibs -Wl,--entry=main -lgcc`
- ⚠️ 两条分支都带 `-g0 -Wl,--build-id=none -Wl,--stack,67108864 … -lm -lkernel32 -luser32 -lshell32 -ladvapi32`。**Windows 系统库与 `-lm` 是无条件加的**（`#[no_std]` 也加）—— 真正的 freestanding 镜像得自行用 lld-link / 自定义链接行完成。

### 7.1 中间产物与旁路文件

编译过程使用若干固定路径的旁路文件传递 codegen 到链接阶段的信息：

| 文件 | 用途 |
|---|---|
| `_inline_asm.buf` | `#[naked]` 函数的裸函数体（普通 `asm!` 走 IL `dbgasm` 通道，不落这里） |
| `_section_directive.buf` | `#[link_section]` 的 `.section` 指令 |
| `_fence.buf` | 内存屏障助记符（`fence_*` 现走 IL `dbgasm` 通道，此文件为历史路径） |
| `_no_std.flag` | `#[no_std]` 标记 |

- **每次编译开始时先删干净**（W-122）。
- ⚠️ 因此两个并发编译会互相干扰 —— 见 [§ 12.13](#abi-12-13)。

---

## 8. 底层扩展的 ABI 影响

| 特性 | 是否实装 | ABI 影响 |
|---|---|---|
| `#[naked]` | ✅ | 无 prologue / epilogue；函数体只能含 `asm!(...)`；不参与 sret；被调用方需自行保存 callee-saved 寄存器 |
| `#[link_section("...")]` | ✅ | 不改变调用约定，只改变符号落入的 section（在 `.s` 中该符号前插入 `.section` 指令） |
| `#[no_std]` | ✅ | 见 § 7 |
| `asm!("...")` | ✅ | **内联在函数体当前位置**（文本 hex 编码进 IL 的 `dbgasm <hex>` 指令，后端在该位置解回原文写入 `.s`） |
| `fence_seq_cst()` / `fence_acquire()` / `fence_release()` | ✅ | 分别发射 `mfence` / `lfence` / `sfence`，与 `asm!` 同通道内联在调用点 |
| `volatile T` | ✅ | 无（见 § 2.6） |

`asm!` 与 `fence_*` 的内联是正确性问题，不只是便利：早期实现把它们 append 到 `.s` 末尾（落在所有函数之外成为死字节），**内存屏障从未执行过**。

---

## 9. 稳定性承诺

**此版本锁定（不会因 minor/patch 改变）**：

- 基础类型的 sizeof / alignof
- 指针宽度（64 位）
- struct 字段对齐与排列算法
- enum 的 tag（i32，offset 0）布局
- 四个目标的调用约定归属（哪个目标用哪套约定）
- 名称修饰方案的基本形状（`<mod>__<name>` / `<Base>$<T>`）

**可能在后续版本改变**：

- struct / enum 返回值在 SysV 上的 sret 处理（应改为按大小分类返回）
- `alignof(enum)` 的取值
- 名称修饰方案（引入类型编码 / 重载编码）
- SysV 分类器对非 struct 标量的处理
- 栈槽对齐粒度

---

## 10. 内部 IR 字母表（非 QBE）

`.il` 是自托管后端的**进程内 IR 转储**，**不是标准 QBE 方言**，外部工具链无法消费。类型字母如下：

| 字母 | ASCII | 物理承载 |
|---|---|---|
| `w` | 119 | 32 位整数 |
| `l` | 108 | 64 位整数 / 指针 |
| `s` | 115 | `f32`，走 XMM 或 `movss` |
| `d` | 100 | `f64`，走 XMM 或 `movsd` |
| `m` | 109 | **MEMORY class**：只进栈，不占用整数寄存器 |

- 字母决定**承载宽度**，寄存器**序号**由发射期按目标选择（Win 与 SysV 各有独立寄存器名表）。
- ⚠️ `m` 是 JHYY 自有标记，**未进 `ir.jhyy` 的 `QBE_*` 常量集**（后端代码里硬编码 109）。

---

## 11. 与 v1.0.0 的差异速查

| v1.0.0 | v4.0.0 |
|---|---|
| 后端是 QBE（`-t amd64_win`） | QBE 已移除，自托管 amd64 后端 |
| 全文用 QBE IL 表述 | 全文用机器级表述（§ 10 的 IR 字母表仅作内部参考） |
| 仅 `amd64_win` 一个目标 | 四个目标（§ 1） |
| struct 按值传参 / sret 返回（Win 单目标） | 同上，且 SysV 另有 eightbyte 分类（§ 3.2） |
| extern fn 误加 `$` 前缀 | extern fn 原样发射（§ 3.6） |
| `asm!` / fence append 到 `.s` 末尾 | 内联在函数体当前位置（§ 8） |
| 切片布局已定义、codegen 未实装 | 切片完整可用，可作为参数传递 |
| 三个物理分离的栈池 | 两个池（alloc 与 address-holder 已合并，§ 4.2） |

---

## 12. 已知偏离与未实装项

> 本节是与标准平台 ABI 的**已知不一致**，以及当前能力的边界。它们都是有意记录、有门或已登记的事实，不是遗漏。
>
> **表内只列当前仍未闭合的项**；已修复的偏离会从本表移除（编号随之前移，故外部引用请以条目内容而非编号为准）。

| # | 项 | 性质 |
|---|---|---|
| <a id="abi-12-1"></a>12.1 | **struct / enum 返回值在所有目标无条件走 sret**，无大小阈值。SysV 标准应把 ≤16 字节聚合类型放进 `RAX:RDX` / `XMM0:XMM1`。跨语言互操作（jhyy 返回值给 gcc callee）会因此不符 | 偏离 SysV |
| <a id="abi-12-2"></a>12.2 | **`alignof(enum)` 硬编码返回 4**，而 enum 布局计算用的是 `max(4, max_payload_align)`。含大 payload 的 enum 作为 struct 字段时，对齐可能小于其自然对齐 | 内部不一致 |
| <a id="abi-12-3"></a>12.3 | **SysV 的非 struct 标量参数仍借 Win 分类器决定 IR 字母**。当前不出错（寄存器序号在发射期按 SysV 选），但这是隐式依赖，且无对拍测试覆盖 | 隐患 |
| <a id="abi-12-4"></a>12.4 | **SysV 下 MEMORY class 参数与寄存器溢出参数混排 → 编译期报错**。部分合法 SysV 用法（如大 struct 作第 7 个参数）当前无法编译。该守门**只数用户参数**，隐藏的 sret 指针会吃掉 INTEGER 0 ⇒ 实际整数预算为 5 而非 6 | 能力边界 |
| <a id="abi-12-5"></a>12.5 | **sret 槽大小 = `max(4, sizeof(T))`**，而 enum 拷贝按 `total_size` 写入。理论上二者可能不一致；但 enum 的 `total_align ≥ 4` ⇒ `total_size ≥ 4` ⇒ 实测恒等，属理论边界 | 理论边界 |
| <a id="abi-12-6"></a>12.6 | **栈槽只保证 8 字节对齐**。当前无 16 字节对齐类型，未触发；引入 SIMD 类型前需先改 | 能力边界 |
| <a id="abi-12-7"></a>12.7 | **全 spill，只保存 `RBP`**，栈帧显著偏大（自举编译器最大单函数帧：**v4.2.1 之后实测 349232 B ≈ 341 KiB**，中位 288 B；v4.2.1 之前是 234080 B ≈ 229 KiB —— 该数字**已作废**，v4.2.1 的帧公式按函数实际需要算，中位帧 8368 → 288 B，但**最大帧反而变大**（旧公式在公式池主导时把 `per_fn_alloc` 丢掉）⇒ 降帧的真正杠杆是**寄存器分配**（v4.4 阶段二），不是再调公式。随构建漂移），依赖 64 MB 栈预留补偿 | 实现特征 |
| <a id="abi-12-8"></a>12.8 | **UEFI EFIAPI wrapper 未实装**：freestanding 的两个钩子（`emit_entry_point` / `no_crt_init`）**都是空实现** —— 编译器不生成 EFIAPI wrapper，也不自动抑制 CRT / runtime 链接。entry 符号由用户自行提供（`efi_main` / `_start`，见语言规范 § 17.6） | 未实装 |
| <a id="abi-12-9"></a>12.9 | **无交叉编译容器后端**：`--target` 不切换 PE/ELF 产出，容器格式由宿主机 `ld` 决定 | 能力边界 |
| <a id="abi-12-10"></a>12.10 | **无 aarch64 / riscv64**。`.jhyynb` 原生二进制格式仍是设计稿，未实装 | 未实装 |
| <a id="abi-12-11"></a>12.11 | **SysV eightbyte 宽度规则只对第 0 个 eightbyte 成立**：第 1 个及以后恒为 8 字节（实现比较的是字段**绝对**结束偏移与字面量 4）。12 字节 struct 的第二个 eightbyte 因此被当作 8 字节，与 gcc 的 INTEGER(4) 不符 | 偏离 SysV |
| <a id="abi-12-12"></a>12.12 | **SysV 溢出的 f64 栈参缺 16 字节对齐**：caller 只按 8 递增 | 偏离 SysV |
| <a id="abi-12-13"></a>12.13 | **旁路文件走固定路径**，两个并发编译会互相干扰。`#[no_std]` 用例因此在测试 harness 中串行执行 | 能力边界 |
| <a id="abi-12-14"></a>12.14 | **Windows 控制台 UTF-8 不由运行时设置**：`runtime.c` 的 `main` 不调用 `SetConsoleOutputCP(65001)`，需自行 `chcp 65001` | 实现特征 |

---

## 13. Cross-ref

- 语言规范：[`docs/abis/jhyy-lang-spec-v4.0.0.md`](./jhyy-lang-spec-v4.0.0.md)
- 二进制格式（设计稿，未实装）：[`docs/abis/jhyy-binary-format-v1.0.0.md`](./jhyy-binary-format-v1.0.0.md)
- 历史档案（已归档至 git 历史）：`jhyy-abi-v1.0.0.md`、`jhyy-abi-v0.0.1.md`
- 已知限制台账：[`docs/internal/workarounds.md`](../internal/workarounds.md)
- 验证门：`compiler/tests/bootstrap/`（`closure_check.sh`、`fixed_point.sh`、`artifact_checks.sh`、`sysv_abi_cross.sh`、`sysv_full_regress.sh`）
