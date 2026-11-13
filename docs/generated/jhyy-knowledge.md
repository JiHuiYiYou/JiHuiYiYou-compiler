# JHYY 知识包 —— 给写 JHYY 的 AI 常驻的速查

> **本文件是生成的，别手改** —— 改规范或标准库源码后重新跑：
> `python scripts/gen-knowledge.py`
>
> 真相源是语言规范（`docs/abis/jhyy-lang-spec-v4.0.0.md`）与标准库源码。

## 怎么用这份知识包

- **写代码前**：不确定某个语法/规则，查下面的目录 → 用 `jhyy_lang_ref` 取那一节。
- **写完后**：用 `jhyy_check` 真编译一遍，按**真实报错**改 —— 别靠猜。
- **看到「未实装」清单**：那些是**编译器明确拒绝**的构造 ⇒ 别写。

### 工具速查（**直接用这些，不用先搜工具**）

| 工具 | 干什么 | 什么时候用 |
|---|---|---|
| `jhyy_check` | 编译检查，返回**全部**诊断（行:列 + 错误原文） | 改完代码 ⇒ 必调一次 |
| `jhyy_run` | 编译**并运行**，返回 stdout / 退出码 | 要看程序实际输出 ⇒ 才调 |
| `jhyy_lang_ref` | 查语言规范（传章节号最准，如 `"5.6"`） | 不确定语法/规则 ⇒ 查目录里那节 |
| `jhyy_workarounds` | 查已知坑台账（含「已修」和「设计如此」） | 报错看着像编译器 bug ⇒ 查 |
| `jhyy_abi_info` | 查 ABI（结构体布局 / 调用约定 / FFI） | 涉及 struct 传参 / FFI ⇒ 查 |
| `jhyy_get_il` | 看编译出来的 IL | 调试 codegen ⇒ 才用 |

⚠️ **`jhyy_check` 一次就返回全部诊断** ⇒ 不要一个错误查一次。
⚠️ **别顺手改注释、别做额外验证**（不用证明断言非空、不用探测别的边界）——
　　那些是**任务范围外**的事，做了只会浪费轮数。

## 规范章节目录

查某一节用 `jhyy_lang_ref`，参数传章节号（如 `"5.6"` / `"附录 B"`）。

- **§ 1 程序结构**
- **§ 2 类型系统**
- **§ 3 变量与绑定** —— - 不可变绑定编译为 SSA 临时量；**不可重新赋值** —— `x = 1;` 报 `cannot assign to immutabl
- **§ 4 运算符**
- **§ 5 控制流**
- **§ 6 函数** —— - 参数**必须**显式标注类型。
- **§ 7 指针与借用**
- **§ 8 结构体** —— - 字段按声明顺序排列、按自然边界对齐（算法见 [ABI § 2.3](jhyy-abi-v4.0.0.md#23-struct-布局)）。
- **§ 9 枚举** —— - tag 为 `i32`，从 0 起按声明顺序分配。
- **§ 10 数组与切片**
- **§ 11 泛型**
- **§ 12 顶层 const 数组** —— - 仅支持**顶层** `const`；函数体内不允许。
- **§ 13 模块与导入** —— - 语法是**单个标识符**。⚠️ `import std::vec;` 是**解析错误**（`expected ;, got ::`）。
- **§ 14 FFI** —— - `extern fn` 只声明、不生成函数体，链接期由 `ld` 解析符号。
- **§ 15 标准库** —— 8 个模块，随编译器一同安装。**导入时写模块名本身，不带 `std::` 前缀**：
- **§ 16 命令行** —— ⚠️ **命令行只接受一个输入文件**，多余的文件参数被静默忽略（见 [§ 1.2](#12-源文件与多文件)）。
- **§ 17 底层与 OS 扩展**
- **§ 18 错误码与诊断** —— 其余诊断以文本形式给出，无编号。高频文本：
- **§ 19 Debug ABI（🔒 跨项目契约）**
- **§ 20 Wire Format ↔ jhyy 侧表达规则（🔒 跨项目契约）**
- **§ A 与 v1.3.0 的差异**
- **§ B 未实装 / 已实装但受限**
- **§ C 自举兼容性** —— **自举（self-hosting）= 用 JHYY 写 JHYY 编译器**。
- **§ D 完整示例**
- ** Cross-ref** —— - ABI：[`docs/abis/jhyy-abi-v4.0.0.md`](jhyy-abi-v4.0.0.md)

## 反直觉点（规范里标了 ⚠ 的行）

下面每条都是**规范原文标记**的「与直觉/与旧规范不同」之处。

- ⚠️ **`argv` 的类型写作 `*u8`，实际却是「指向指针数组的指针」**（C 的 `char **`）。  *（§ 1.1 入口点）*
- ⚠️ 命令行**只接受一个**输入文件；多余的 `.jhyy` 参数会被**静默忽略**（不报错、不警告）。`jhyy compile a.jhyy b.jhyy` 实际只编 `a.jhyy`。  *（§ 1.2 源文件与多文件）*
- | 类型别名 / struct / enum | `type Name = ...` | ⚠️ **结尾不能带 `;`** |  *（§ 1.4 顶层声明）*
- ⚠️ `()` 是零大小类型（sizeof 0 / alignof 1），但**类型位置不认它** —— `let x: () = ();` 与 `fn f() -> ()` 都是解析错误（函数**省略**返回类型是支持的）。见[附录 B](#附录-b未实装--已实装但受限)。  *（§ 2.1 基础类型）*
- `bool` 占 1 字节，字面量只有 `true` / `false`（0 / 1）；⚠️ 编译器**不做归一化**，非字面量来源的值可能是任意字节（见附录 B）。  *（§ 2.1 基础类型）*
- | `fn(...)` | 函数指针，8 字节 —— ⚠️ **类型位置不认这个语法**（`fn(i32)` / `fn(i32) -> i32` 都被拒）。见[附录 B](#附录-b未实装--已实装但受限) |  *（§ 2.2 复合类型）*
- ⚠️ **`type` 声明结尾不带分号**。带 `;` 会得到 `error: unexpected token ';' in expression`。  *（§ 2.3 类型别名）*
- ⚠️ **函数实参类型不做检查**。把 `i32` 传给 `struct` 形参能编译通过，运行时按 struct 布局读寄存器 → 访问违例崩溃（见附录 B）。  *（§ 2.4 类型推断）*
- ⚠️ **越界必须报错，不静默饱和**。饱和（把 2⁶³ 变成 2⁶³−1）会让「写错了」与「写对了」产出同一个值，用户无从察觉。  *（整数字面量的取值范围）*
- ⚠️ **32 位族当前不做范围检查**：无后缀字面量默认 `i32`，`0x100000000` 这类超 32 位的值今天仍按 `i32` 语义**静默截断**（不在上表的适用范围里）。  *（整数字面量的取值范围）*
- 形式限定为 `N.M`（或 `N.M` + 后缀）。⚠️ **不支持指数写法** —— `1.0e10` / `1e-9` 解析失败（`expected ;, got ident`）。  *（浮点字面量）*
- ⚠️ **没有隐式 decay**：`let s: [*]u8 = "hello";` 会得到 `type mismatch in let`。要显式 `as [*]u8`。  *（字符串字面量）*
- ⚠️ **字段顺序 = 自然对齐的结果（2026-10-31 订正）**：本布局**必须**是  *（§ 2.6 `Cap<T>`）*
- ⚠️ **`gen` 的语义（2026-10-30 定）**：slot 被复用时 +1；cap 派发时携带当时的代数。  *（§ 2.6 `Cap<T>`）*
- ⚠️ generation **只在同一个 CNode 槽内有意义** ⇒ 跨 CNode 派生时目标槽的代数由  *（§ 2.6 `Cap<T>`）*
- ⚠️ **`T` 当前不被解析** —— `Cap<T>` 的 inner **被解析但被忽略**：`Cap` 在符号表里  *（§ 2.6 `Cap<T>`）*
- ⚠️ **不允许实例化**，报 `E0050`。触发写法是**带 init 的 `let`**：  *（§ 2.7 `PhantomData<T>`）*
- ⚠️ **`alignof(enum)` 恒为 4** —— 与 enum 布局算出的自然对齐（`max(4, max_payload_align)`）不一致，见 [ABI § 12.2](jhyy-abi-v4.0.0.md#abi-12-2)。  *（§ 2.8 `sizeof` / `alignof`）*
- ⚠️ **可以给不可变绑定取地址，编译器不检查**（旧规范说「不可取地址」是错的）。而且通过这样的指针写入**不报错也不生效**（`x` 保持原值）—— 写保护未实装，见附录 B。  *（§ 3 变量与绑定）*
- ⚠️ **同名 `fn` / `type` / `const` / 函数参数是错误** —— 编译期报 `the name \`x\` is defined multiple times`（与 Rust 的 E0428 一致）。**只有 `let` 走 shadowing**。  *（§ 3 变量与绑定）*
- ⚠️ **顶层变量的初始化器必须是「整数常量表达式」**：顶层变量落在 **`.data` 段**（编译期常量），所以初始化器在**编译期**求值。  *（§ 3 变量与绑定）*
- ⚠️ 三处与直觉/旧规范不同：  *（§ 4.1 优先级（低 → 高））*
- ⚠️ 浮点 → 整数采用**饱和**语义（Rust 风格）：区间内按 IEEE 754 **向 0 截断**；**越界饱和**到目标类型的 `MIN` / `MAX`；**NaN → 0**（不是 `integer indefinite`）。  *（§ 4.3 类型转换 `as`）*
- ⚠️ 负零（`-0.0`）向 0 截断得 `0`。浮点 ↔ 浮点（`f32` ↔ `f64`）是**值转换**（`f32 → f64` 精确无损；`f64 → f32` 收窄到单精度，x86 `cvtsd2ss` 按默认的 round-to-nearest-even 舍入），**不是**位重解释。  *（§ 4.3 类型转换 `as`）*
- ⚠️ **分支块的类型 = 该块里最后一条语句的类型**：  *（§ 5.1 if / else）*
- ⚠️ **match 里的区间是闭区间**，与 for 相反 —— 见 [§ 5.6](#56-match)。  *（§ 5.3 for）*
- ⚠️ **`while` 的 `continue` 直接跳到条件重测 —— 循环体里 `continue` 之后的语句一律不执行。**  *（§ 5.4 break / continue）*
- | 范围 | `start..end` | ⚠️ **闭区间**（含两端） |  *（§ 5.6 match）*
- ⚠️ **arm 的 body 只能是单个表达式** —— 不能写 `return`，也不能写成语句块（`{ ... }`）。与闭包体同款限制（§5.7）。  *（§ 5.6 match）*
- ⚠️ **范围的端点语义与 `for` 循环不同**：`0..10` 在 match 里**同时匹配 0 和 10**（闭区间），在 `for` 里不含 10（半开）。写范围 pattern 时按闭区间理解。  *（§ 5.6 match）*
- ⚠️ 不支持 **guard pattern**（`Some(x) if x > 0` → 解析错误）。  *（§ 5.6 match）*
- ⚠️ **二层以上的嵌套 pattern 不支持** —— 编译期报错 `nested pattern is not supported`。  *（§ 5.6 match）*
- ⚠️ 闭包值**可直接调用**；但「当函数值**传递**」做不到 —— 没有 `fn(...)` 类型语法（见 [§ 2.2](#22-复合类型) 与[附录 B](#附录-b未实装--已实装但受限)）。  *（§ 5.7 闭包）*
- ⚠️ **函数体末表达式的隐式返回不触发 defer**。`fn f() -> i32 { defer g(); 0 }` 不会调用 `g`；写成 `fn f() -> i32 { defer g(); return 0; }` 才会（见附录 B）。  *（§ 6.1 defer）*
- `&x` 的类型是 `*i32`。⚠️ 编译器**不检查** `x` 是否可变 —— 不可变绑定也能取地址。  *（§ 7.1 指针）*
- ⚠️ **`->` 不是成员访问运算符**（它只用于函数返回类型）。通过指针访问字段写 `(*p).field`；`p->field` 是解析错误。  *（§ 7.1 指针）*
- ⚠️ **索引（`p[i]`）与解引用（`*p`）不是一回事** —— `p` 是引用时：  *（§ 7.2 借用 `&T` / `&mut T`）*
- ⚠️ **引用指向的是「那个变量」，不是「变量的内容」** ⇒ 引用到**指针**时要多解一层：  *（§ 7.2 借用 `&T` / `&mut T`）*
- ⚠️ **构造时允许省略字段**，编译器**不报「缺字段」错误**。  *（§ 8 结构体）*
- ⚠️ **一个变体最多带一个 payload** —— `Rect(i32, i32)` 是解析错误（`expected ), got ,`）。要装多个字段，把 payload 换成 struct —— 见[附录 B](#附录-b未实装--已实装但受限)。  *（§ 9 枚举）*
- ⚠️ **数组按值传参时，callee 拿到的是调用方数组的地址（实质按引用）** ——  *（§ 10.1 定长数组）*
- ⚠️ 这与 C / Rust 的「数组按值传参 = 复制」**不同** —— 想要副本得自己拷：  *（§ 10.1 定长数组）*
- ⚠️ 下标**不做**运行时边界检查（同 §10.1 定长数组）。  *（§ 10.2 切片）*
- ⚠️ **编译器不做 const 表达式检查**：元素位置放函数调用能编译通过，但**不会被求值**，运行时取到 0。  *（§ 12 顶层 const 数组）*
- 不允许 `const` 指针、`const` 切片。⚠️ **`const` enum 数组实际是允许的**（无报错）。  *（§ 12 顶层 const 数组）*
- 语法是**单个标识符**。⚠️ `import std::vec;` 是**解析错误**（`expected ;, got ::`）。  *（§ 13 模块与导入）*
- `import` 惯例写在文件顶部，但 ⚠️ 编译器**不强制位置**（写在其他声明之后也能编译）。  *（§ 13 模块与导入）*
- ⚠️ **参数 / 返回类型不做限制**：声明 `extern fn takes(s: MyStruct) -> i32;` 能编译通过（且**不会**按值跨 FFI 传 struct —— 实际按地址传，与 C ABI 不符）。  *（§ 14 FFI）*
- *⚠️ import 之后怎么调用 —— 规则（别猜，去翻模块源码）:**  *（§ 15 标准库）*
- ⚠️ 各模块的命名风格**历史上不统一**（下划线个数、是否带 `std_` 前缀都不同）：  *（§ 15 标准库）*
- ⚠️ 写错名字的报错是 `undefined variable`（**没有**「你是不是想写 …」的提示）⇒  *（§ 15 标准库）*
- ⚠️ `std::os` 的 `OS_O_*` / `OS_MODE_RW_R` 是**零参函数**，不是常量 —— 用法是 `os::OS_O_CREAT()`。不带括号会得到 `expected (, got ;`。  *（§ 15 标准库）*
- ⚠️ **命令行只接受一个输入文件**，多余的文件参数被静默忽略（见 [§ 1.2](#12-源文件与多文件)）。  *（§ 16 命令行）*
- ⚠️ **未识别的选项会被拒绝**，不会当成文件名 —— `jhyy compile --foo a.jhyy` 报  *（§ 16 命令行）*
- ⚠️ **除 `amd64_win` 外的目标链不了** —— `--target` 只决定**代码生成**的调用约定，  *（§ 16 命令行）*
- ⚠️ **要得到纯 freestanding 产物，源文件还必须带 `#[no_std]`** —— 链接行是按 `#[no_std]` 属性分支的，**不是按 `--target`**：  *（§ 17.6 freestanding 目标与 entry 符号）*
- ⚠️ freestanding 的两个编译期钩子（`emit_entry_point` / `no_crt_init`）**当前都是空实现** —— 编译器**不**生成 UEFI EFIAPI wrapper，**也不**自动抑制 CRT 链接。  *（§ 17.6 freestanding 目标与 entry 符号）*
- ⚠️ 即使带 `#[no_std]`，链接行仍会无条件追加 `-lm -lkernel32 -luser32 -lshell32 -ladvapi32`。真正的 UEFI / 裸机镜像需要**自行**用 lld-link（`/SUBSYSTEM:EFI_APPLICATION /ENTRY:efi_main`）或自定义链接行完成。  *（§ 17.6 freestanding 目标与 entry 符号）*

## 附录 B：未实装 —— 这些构造编译器会直接拒绝

- 单元类型 `()` —— `()` 在类型位置不被接受（`let x: () = ();` / `fn f() -> ()` 都是解析错误）
- `fn(...)` 函数指针类型语法 —— 类型位置不认 `fn(i32)` / `fn(i32) -> i32` ⇒ 闭包值无法作为函数值传递
- 完整 NLL / Polonius 借用检查、生命周期标注 `'a`、reborrow、跨函数借用
- 闭包捕获外层变量 —— 编译期明确报错，不静默生成错误代码
- match arm 的 body 不能是语句块 —— 只能是单个表达式（不能写 `return` / `{ ... }`；与闭包体同款限制）
- 块表达式（`let v = { ... };`）—— 表达式位置不认 `{`
- 泛型约束 `<T: Ord>`、生命周期泛型、const generic、trait objects、HKT
- 变参函数、回调函数、struct/enum 按值跨 FFI 边界
- `Cap<T>` 的字段访问（`.cnode_idx` / `.depth` / `.rights`）；`Cap<T>` 的 `T` 不被解析
- `std::math` 的 f32 版本与 `tan` / `log` / `exp` / `floor` / `ceil`
- async / await、`std::map`
- aarch64 / riscv64 目标、`.jhyynb` 原生二进制格式
- `asm!` 的操作数约束、clobber 声明、Intel 语法
- match 的 guard pattern（`Some(x) if x > 0`）
- 浮点字面量的指数写法（`1.0e10`）

## 附录 B：已实装但受限 —— 这些能写，但有坑

- **`argv` 的类型写作 `*u8`，实际是 `char `** —— 入口签名里的 `argv` 是「指向指针数组的指针」，但类型写作 `*u8` ⇒ `*argv` 只 load 1 字节（IL `loadub`）—— 那是 `argv[0]` 指针的最低字节，不是指针本身 ⇒ 拿它跟 `0` 比等于断言「堆地址最低字节 ≠ 0」（跟堆布局绑定的假信号）。读 `argv[i]` 必须先 `argv as u8`（见 §1.1） （台账 W-157）
- **聚合 `==` 不接受函数调用结果** —— `make_p(1) == make_p(2)` 编译期报错(`equality comparison of a function call result is not supported for aggregate types`)。聚合返回值在 ABI 下不统一是地址(>16B 走 sret 是地址;≤16B 走寄存器)⇒ 按地址比会读到寄存器里的头几个字节。形态差别:`let a = make_p(1); a == b` 里的 `a` 是变量(值在栈槽里)⇒ 安全 ⇒ 不报错 （台账 W-133.1）
- **聚合的大小比较未实装** —— `a < b` / `a >= b`(struct / enum / 数组 / 切片)编译期报错(`ordering comparison is not supported for struct/enum/array/slice types`)—— 聚合的大小比较无定义 （台账 W-133.2）
- **struct 字面量的字段值类型必须精确匹配字段类型** —— `type P = struct { c: u8 }` 写 `P { c: 7 }` 报 `field type mismatch` —— 整数字面量默认推断为 `i32`,与 `u8` 不相等。须写成 `let c: u8 = 7;` 再 `P { c: c }` （台账 W-133.3）
- **struct 字面量省略的字段未初始化** —— 编译器不报「缺字段」错误，但缺失字段的值是栈上的未初始化垃圾，不是 0（毒化栈后实测 y=0 / z=garbage，每次可能不同） 
- **enum 变体最多只能带一个 payload** —— `type S = enum { R(i32, i32) }` 编译期报错（`expected ), got ,`）—— 变体声明的括号里只能跟一个类型。要装多个字段，把 payload 换成 struct（`R(PRect)`；已由 `agg_eq_enum.jhyy` 覆盖）。门：`spec_err_enum_multi_payload.jhyy` 
- **不可变性的写保护未实装** —— 编译器不检查取地址对象是否可变；`&x` 对不可变绑定合法，`*p = v` 不报错也不生效 
- **函数实参类型不检查** —— `f(5)` 传给 struct 形参能编译，运行时按 struct 布局读寄存器 → 访问违例崩溃 
- **借用检查只覆盖「同作用域内双 `&mut`」** —— 词法作用域会误报「借用提前结束」的情况尚未处理 
- **嵌套泛型 `Vec<Vec<T>>`** —— 未被测试套件覆盖，行为不应依赖 
- **`const` 元素不做 const 检查** —— 元素位置放函数调用能编译，但不会被求值，运行时取到 0 
- **顶层全局变量只有整数类型初始化正确** —— `let mut f: f64 = 3.5;` 读到 0（初始化器被丢弃）；`let mut p: Point = ...` 读到垃圾（未定义读）。整数类型（含跨函数读写链）正确 
- **`match` 范围是闭区间** —— 与 `for` 的半开区间语义相反，容易踩 
- **`defer` 不覆盖隐式返回** —— 函数体末表达式返回时 defer 不执行 
- **二层以上的嵌套 pattern 不支持** —— pattern 树里不得有 enum pattern 是另一个 enum pattern 的后代（OR 包着的也算）⇒ 编译期报错 `nested pattern is not supported`。外层 tag 比较与内层 payload 提取都未实装 
- **命令行只接受一个输入文件** —— 多余的 `.jhyy` 参数被静默忽略（不报错、不警告）⇒ `jhyy compile a.jhyy b.jhyy` 实际只编 `a.jhyy`。多文件须用 `import` 组合（见 [§ 1.2](#12-源文件与多文件)） 
- **`std_io_print` / `std_io_print_err`** —— 依赖 libc 的 `stdout` / `stderr` 句柄获取 
- **SysV 下 MEMORY class 参数与寄存器溢出参数混排** —— 编译报错（[ABI § 12.4](jhyy-abi-v4.0.0.md#abi-12-4)） 
- **无交叉编译容器后端** —— `--target` 不切换 PE / ELF 产出 

## 标准库公开 API

导入时写模块名本身（**不带 `std::` 前缀**），调用时直接写完整函数名。

### `arena`

- `arena_init(a, default_size)` -> 1 / 0
- `arena_alloc(a, size)` -> *u8 (8-byte aligned) / 0 on fail
- `arena_calloc(a, size)` -> *u8 (zeroed) / 0 on fail
- `arena_reset(a)` -> 1 (重置 cur 到 start, 不释放 block)
- `arena_free(a)` -> 1 (释放所有 block)

### `fmt`

- `fmt_i32(out_buf, val)` -> 写入 i32 十进制到 out_buf (null-terminated);返回写入字节数 (不含 \0)
- `fmt_i64(out_buf, val)` -> 写入 i64 十进制;返回字节数
- `fmt_str(out_buf, s)` -> 复制 cstr 到 out_buf;返回字节数
- `fmt_hex_u32(out_buf, val, upper)` -> 写入 u32 十六进制;返回字节数

### `io`

- `std_io_open(path, mode)` -> FILE* (file handle) / 0 on fail
- `std_io_close(f)` -> 0 ok / -1 fail
- `std_io_read(f, buf, n)` -> 实际读字节数
- `std_io_write(f, buf, n)` -> 实际写字节数
- `std_io_print(s)` -> stdout 写 cstr(真 impl,W-080 v3.2.3.1)
- `std_io_print_err(s)` -> stderr 写 cstr(真 impl,W-080 v3.2.3.1)

### `math`

- `std_math_sin(x: f64)` -> f64 (sin(x), radian)
- `std_math_cos(x: f64)` -> f64 (cos(x), radian)
- `std_math_sqrt(x: f64)` -> f64 (sqrt(x) ≥ 0, NaN if x < 0)
- `std_math_pow(base: f64, exp: f64)` -> f64 (base^exp)

### `mem`

- `mem_copy(dst, src, n)` -> 复制 n 字节;返回 dst
- `mem_compare(a, b, n)` -> 比较 n 字节:0 equal / <0 a<b / >0 a>b
- `mem_set(dst, val, n)` -> n 字节设为 val (低 8 位);返回 dst
- `mem_find_byte(p, n, val)` -> 找第一个 == val 的字节;返回 index / -1
- `mem_zero(dst, n)` -> n 字节清零;返回 dst

### `os`

- `std_os_open(path, flags, mode)` -> fd (i64) / -1 on fail
- `std_os_close(fd)` -> 0 ok / -1 fail
- `std_os_read(fd, buf, n)` -> 实际读字节数 / -1 on fail
- `std_os_write(fd, buf, n)` -> 实际写字节数 / -1 on fail
- `std_os_exit(code)` -> 终止进程(never returns)
- `std_os_getenv(name)` -> env value cstr / 0 on miss

### `string`

- `str_from_cstr(a, s)` -> 复制 cstr 到 arena;返回 *StringHeader (16B)
- `str_from_bytes(a, p, n)` -> 复制 n 字节;返回 *StringHeader
- `str_len(s)` -> 长度
- `str_data(s)` -> *u8 (data pointer, NOT null-terminated)
- `str_concat(a, x, y)` -> 拼接 x + y 到新 arena buffer
- `str_compare(x, y)` -> 0 equal / <0 x<y / >0 x>y
- `str_find(s, needle)` -> 找 substring (needle = cstr);index / -1
- `str_equals(x, y)` -> 1 equal / 0

### `vec`

- `std_vec_new(elem_size)` -> Vec<i32> (24B uninit struct, data=0/len=0/cap=0)
- `std_vec_with_cap(elem_size, cap)` -> Vec<i32> (init with pre-allocated cap slots)
- `std_vec_push(v, elem_size, src: *u8)` -> i32 (auto-grow cap, copy elem from src into data)
- `std_vec_get(v, elem_size, idx)` -> *u8 (pointer to element at idx, NULL on OOB)
- `std_vec_len(v)` -> i64
- `std_vec_cap(v)` -> i64
- `std_vec_free(v)` -> i32 (free data buffer, reset to 0/0/0)

## 一段完整的 JHYY 程序（规范附录 D）

```jhyy
// 完全可编译的一个程序：入口 + 泛型 + struct + enum + match + 闭包 + defer
import vec;

type Shape = enum {
    Circle(i32),     // 半径
    Rect(i32),       // 面积（变体只带一个 payload —— 见附录 B）
    Empty,
}

type Point = struct {
    x: i32,
    y: i32,
}

fn area(s: Shape) -> i32 {
    match s {
        Shape::Circle(r) => 3 * r * r,
        Shape::Rect(a) => a,
        Shape::Empty => 0,
    }
}

fn max<T>(a: T, b: T) -> T {
    if a > b { return a; }
    return b;
}

fn cleanup() -> i32 {
    return 0;
}

fn main_jhyy() -> i32 {
    defer cleanup();

    let p = Point { x: 3, y: 4 };
    let s = Shape::Rect(p.x * p.y);
    let a = area(s);

    let f = |n: i32| { n * 2 };
    let d = f(a);

    let m: i32 = max::<i32>(d, 100);

    return m;   // 100
}
```

