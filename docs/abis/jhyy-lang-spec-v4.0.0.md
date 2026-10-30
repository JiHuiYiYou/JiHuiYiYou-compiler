# JHYY 语言规范 v4.0.0

**状态**：v4.0.0 —— v4 世代的规范基线，随 `v4.0.0 final` promote 一同锁版
**取代**：`jhyy-lang-spec-v1.3.0.md` 及其 17 份 v3.x supplement（2026-10-24 归档至 git 历史）
**事实基线**：正文只写**当前代码确实已实装**的行为；未实装 / 已实装但受限的，统一收进[附录 B](#附录-b未实装--已实装但受限)
**配套**：[`jhyy-abi-v4.0.0.md`](./jhyy-abi-v4.0.0.md)

> **本版相对 v1.3.0 的写法变化**：v1.3.0 把 v3.x 的特性散在 17 份 supplement 里，本体与 supplement 之间大量交叉引用、且互相矛盾（例：v1.3.0 § 6.1 文档化了从未实装的块表达式；§ 4.1 文档化了会静默算错的 `1_000_000`）。本版把**已实装部分一次性收进正文**，supplement 全部作废；**未实装的部分明确写进附录 B**，不再混在正文里冒充特性。

> **读法**：正文的每一条都对应编译器源码中可复现的行为。凡带 ⚠️ 的行是「与直觉/与旧规范不同」的点，已在附录 B 有对应条目。

---

## 1. 程序结构

### 1.1 入口点

普通（hosted）程序必须定义 `main_jhyy`：

```jhyy
fn main_jhyy() -> i32 {
    0
}
```

- 入口的真实签名是 `main_jhyy(argc: i32, argv: *u8) -> i32`；`argc` / `argv` 是可选的（写 `fn main_jhyy() -> i32` 也合法）。
- ⚠️ **`argv` 的类型写作 `*u8`，实际却是「指向指针数组的指针」**（C 的 `char **`）。
  写 `*argv` 只会 **load 1 个字节**（生成的 IL 是 `loadub`）—— 那是 `argv[0]` **指针的最低字节**，不是指针本身。
  ⇒ 要读 `argv[i]` 必须先 cast 成 `**u8`：

  ```jhyy
  fn main_jhyy(argc: i32, argv: *u8) -> i32 {
      let p = argv as **u8;   // 指针数组
      let a0 = p[0];          // argv[0]
      let a1 = *(p + 1);      // argv[1]
      0
  }
  ```

  见[附录 B](#附录-b未实装--已实装但受限)。
- 返回值作为进程退出码。
- `#[no_std]` 程序改为 `fn main`（见 [§ 17.4](#174-link_section-与-no_std)）。

### 1.2 源文件与多文件

- 后缀 `.jhyy`，UTF-8 编码。
- **多文件通过 `import` 组合，不是靠命令行列多个文件。**
  ⚠️ 命令行**只接受一个**输入文件；多余的 `.jhyy` 参数会被**静默忽略**（不报错、不警告）。`jhyy compile a.jhyy b.jhyy` 实际只编 `a.jhyy`。
  → 正确做法是 `a.jhyy` 里写 `import b;`，由编译器沿 import 图把 `b.jhyy` 一起编进来。

### 1.3 注释与语句分隔

```jhyy
// 单行注释
/* 块注释 */
```

语句以换行或 `;` 分隔。

### 1.4 顶层声明

| 声明 | 语法 | 备注 |
|---|---|---|
| 函数 | `fn name(...) -> T { ... }` | |
| 外部函数 | `extern fn name(...) -> T;` | 只声明，不生成函数体 |
| 类型别名 / struct / enum | `type Name = ...` | ⚠️ **结尾不能带 `;`** |
| 导入 | `import module;` | 模块名**不带 `std::` 前缀**，见 [§ 13](#13-模块与导入) |
| 顶层可变变量 | `let mut name: T = expr;` | 真正的**运行时全局变量**，见 § 3 |
| 顶层 const 数组 | `const NAME: [T; N] = [...];` | 元素应当是字面量（编译器不做 const 检查，见 § 12） |

---

## 2. 类型系统

### 2.1 基础类型

`i8` `i16` `i32` `i64` `u8` `u16` `u32` `u64` `f32` `f64` `bool` `()`

大小与对齐见 [ABI § 2.1](./jhyy-abi-v4.0.0.md#21-基础类型)。

- **没有独立的 `char` 类型**。字符字面量的类型是 `i32`，值是 Unicode codepoint。
- 字符字面量支持**全码点范围 U+0000–U+10FFFF**（含 4 字节 emoji / 辅助平面），按 UTF-8 解码。
- ⚠️ `()` 是零大小类型（sizeof 0 / alignof 1），但**类型位置不认它** —— `let x: () = ();` 与 `fn f() -> ()` 都是解析错误（函数**省略**返回类型是支持的）。见[附录 B](#附录-b未实装--已实装但受限)。
- `bool` 占 1 字节，字面量只有 `true` / `false`（0 / 1）；⚠️ 编译器**不做归一化**，非字面量来源的值可能是任意字节（见附录 B）。

### 2.2 复合类型

| 类型 | 说明 |
|---|---|
| `*T` | 指针，8 字节 |
| `fn(...)` | 函数指针，8 字节 —— ⚠️ **类型位置不认这个语法**（`fn(i32)` / `fn(i32) -> i32` 都被拒）。见[附录 B](#附录-b未实装--已实装但受限) |
| `[T; N]` | 定长数组 |
| `[*]T` | 切片 `{ data: *T, len: i64 }`，16 字节 |
| `struct { ... }` | 结构体，名义类型 |
| `enum { ... }` | 带标签联合体，名义类型 |
| `&T` / `&mut T` | 借用，8 字节单指针 |
| `Cap<T>` | capability，8 字节，见 [§ 2.6](#26-capt) |
| `PhantomData<T>` | 零大小类型标记，见 [§ 2.7](#27-phantomdatat) |
| `volatile T` | 仅修饰基础类型，见 [§ 17.1](#171-volatile) |

### 2.3 类型别名

```jhyy
type Age = i32
type Point = struct { x: i32, y: i32 }
```

- ⚠️ **`type` 声明结尾不带分号**。带 `;` 会得到 `error: unexpected token ';' in expression`。
- 别名是**透明**的 —— `Age` 与 `i32` 完全等价。
- `struct` / `enum` 定义是**名义类型**：字段布局相同而名字不同即为不同类型（按声明名比较，不是按布局）。

### 2.4 类型推断

- **参数必须显式标注类型**。
- 局部变量从初始化表达式推断。
- 无后缀整数字面量默认 `i32`；无后缀浮点字面量默认 `f64`。
- 整数与浮点之间**不允许隐式转换**，必须 `as`。
- ⚠️ **函数实参类型不做检查**。把 `i32` 传给 `struct` 形参能编译通过，运行时按 struct 布局读寄存器 → 访问违例崩溃（见附录 B）。

### 2.5 字面量

#### 整数字面量

| 形式 | 支持 | 说明 |
|---|---|---|
| 十进制 `42` | ✅ | |
| 十六进制 `0xFF` / `0Xff` | ✅ | |
| 前导零 `077` | ✅ | **按八进制解释**（= 63） |
| 八进制 `0o77` / `0O77` | ✅ | 显式 base 8 |
| 二进制 `0b1010` / `0B1010` | ✅ | 显式 base 2 |
| 下划线分隔 `1_000_000` | ❌ | 解析错误（`expected ;, got ident`） |

类型后缀：`42i8` `42i16` `42i32` `42i64` `42u8` `42u16` `42u32` `42u64`。

#### 浮点字面量

```jhyy
let pi: f64 = 3.14;
let half: f64 = 0.5;
let f: f32 = 2.5f32;
```

- 形式限定为 `N.M`（或 `N.M` + 后缀）。⚠️ **不支持指数写法** —— `1.0e10` / `1e-9` 解析失败（`expected ;, got ident`）。
- 无后缀默认 `f64`。后缀：`f32` / `f64` / `f`（= f64）。
- 文本转换交给 C 侧 `atof()`（`jh_f64_atof`）做；`atof` 本身支持指数，但**词法层先一步把指数挡掉了**。

#### 布尔字面量

`true` / `false`，类型 `bool`。

#### 字符字面量

```jhyy
let a: i32 = 'a';
let nl: i32 = '\n';
let emoji: i32 = '🎉';   // 127881
```

类型 `i32`，值为 codepoint。转义：

| 转义 | 含义 |
|---|---|
| `\n` | 换行 (0x0A) |
| `\t` | 制表 (0x09) |
| `\r` | 回车 (0x0D) |
| `\0` | 空字节 (0x00) |
| `\\` | 反斜杠 |
| `\'` | 单引号 |
| `\"` | 双引号 |
| `\xHH` | 十六进制字节（1–2 位） |

其他转义序列（如 `\q`）是词法错误。

#### 字符串字面量

```jhyy
let s: *u8 = "hello";
```

- 类型是 `*u8`（指向 NUL 结尾的 UTF-8 字节串），不是切片、不是数组。
- 落 **`.data`** 段（GAS 默认数据段），不是只读段。
- ⚠️ **没有隐式 decay**：`let s: [*]u8 = "hello";` 会得到 `type mismatch in let`。要显式 `as [*]u8`。

### 2.6 `Cap<T>`

8 字节内建类型：

```
offset  size  field        type
0       4     cnode_idx    u32     CSpace slot index
4       1     depth        u8      CDL 深度
5       2     rights       u16     bit0=R, bit1=W, bit2=G
7       1     padding      u8      零
```

- 小端序。
- ⚠️ **`T` 当前不被解析** —— `Cap` 的 inner 被硬编码成 `i32`，所以 `Cap<i32>` 与 `Cap<i64>` **是同一个类型**（实测 `let b: Cap<i64> = a;`（`a: Cap<i32>`）编译通过）。名义相等按 `elem` 区分的说法在当前实现下不成立。
- 不提供 `.cnode_idx` / `.depth` / `.rights` 字段访问语法。构造走 8 字节整型字面量 + `as Cap`：

```jhyy
let c: Cap = 0x0000030200000007 as Cap;   // cnode=7, depth=2, rights=R|W
```

### 2.7 `PhantomData<T>`

零大小类型（`sizeof == 0`，`alignof == 1`），用作类型标记：

```jhyy
struct Wrapper {
    _marker: PhantomData<i32>,   // 合法：不占 struct 槽位
    val: i32,
}
```

- 允许作 struct 字段（不推进 offset、不影响对齐）。
- ⚠️ **不允许实例化**，报 `E0050`。触发写法是**带 init 的 `let`**：

```jhyy
let p: PhantomData<i32> = 0;   // error: E0050: cannot instantiate PhantomData<T> ...
```

（写成 `let p = PhantomData<i32>();` 得到的不是 E0050，而是 `undefined variable` —— 表达式位置不认这个写法。）

### 2.8 `sizeof` / `alignof`

```jhyy
let s: i64 = sizeof(i32);      // 4
let p: i64 = sizeof(*u8);      // 8
let a: i64 = alignof(i64);     // 8
let b: i64 = alignof(i32);     // 4
```

- 两者都接受**类型**（不是表达式）。`sizeof(some_var)` 会得到 `unknown type`。
- 返回类型都是 `i64`。
- ⚠️ **`alignof(enum)` 恒为 4** —— 与 enum 布局算出的自然对齐（`max(4, max_payload_align)`）不一致，见 [ABI § 12.2](./jhyy-abi-v4.0.0.md#abi-12-2)。

---

## 3. 变量与绑定

```jhyy
let x = 42;              // 不可变
let mut counter = 0;     // 可变
counter = 10;
```

- 不可变绑定编译为 SSA 临时量；**不可重新赋值** —— `x = 1;` 报 `cannot assign to immutable variable (use let mut)`。
- 可变绑定在栈上分配，可重新赋值、可取地址。
- ⚠️ **可以给不可变绑定取地址，编译器不检查**（旧规范说「不可取地址」是错的）。而且通过这样的指针写入**不报错也不生效**（`x` 保持原值）—— 写保护未实装，见附录 B。
- 支持 **shadowing**：同名 `let` 建立新绑定覆盖旧的（**同作用域与嵌套作用域都成立**；可以改变可变性 —— `let mut y = 1; let y = 2;` 之后 `y` 是**不可变**的，给它赋值报 `cannot assign to immutable variable (use let mut)`）。⇒ 同作用域重名 `let` **不是**错误（与 Rust 的 E0428 不同）。
- ⚠️ **同名 `fn` / `type` / `const` / 函数参数是错误** —— 编译期报 `the name \`x\` is defined multiple times`（与 Rust 的 E0428 一致）。**只有 `let` 走 shadowing**。
- 复合赋值：`+=` `-=` `*=` `/=` `%=`，仅适用于可变变量。
- 顶层允许 `let mut name: T = expr;`。顶层变量是**运行时全局变量** —— 赋值在函数之间可见（实测：在 `bump()` 里改 `g`，`main` 里读到的是改后的值）。
- 顶层 `let mut` / `let` 的类型标注**不是强制的**(实测 `let mut g = 5;` 编译通过且取值正确)。
- ⚠️ **只有整数类型的顶层变量初始化正确**：`let mut f: f64 = 3.5;` 读到 **0**（初始化器被丢弃）；指针 / struct 类型的顶层变量是**未定义读**（读到垃圾值）。见附录 B。

---

## 4. 运算符

### 4.1 优先级（低 → 高）

| 优先级 | 运算符 | 源码常量 |
|---|---|---|
| 1 | `=` `+=` `-=` `*=` `/=` `%=` | `PREC_ASSIGN` |
| 2 | `\|\|` | `PREC_OR` |
| 3 | `&&` | `PREC_AND` |
| 4 | `==` `!=` `<` `>` `<=` `>=` | `PREC_COMPARE` |
| 5 | `\|` | `PREC_BIT_OR` |
| 6 | `^` | `PREC_BIT_XOR` |
| 7 | `&` | `PREC_BIT_AND` |
| 8 | `<<` `>>` | `PREC_SHIFT` |
| 9 | `+` `-` | `PREC_TERM` |
| 10 | `*` `/` `%` **`as`** | `PREC_FACTOR` |
| 11 | `-` `!` `~` `&` `*`（一元前缀） | `PREC_UNARY` |
| 12 | `.` `->` `()` `[]` | `PREC_PRIMARY` |

⚠️ 三处与直觉/旧规范不同：

- **`||` 比 `&&` 松**（两者不同级，`&&` 更紧）。
- **复合赋值与 `=` 同级**（都是 `PREC_ASSIGN`）。
- **`as` 与 `*` `/` `%` 同级**，不是最低。

### 4.2 语义要点

- **整数溢出是定义行为**：二进制补码环绕，无运行时检查。
- **`&&` / `||` 是短路求值**（分支跳转 + phi），不是逐位运算。
- `!` 是逻辑非；`~` 是按位取反。
- 有符号 / 无符号、32 / 64 位、浮点的比较指令按操作数类型分别选择。
- **`==` / `!=` 对聚合类型按值比较**（`struct` / `enum` / 数组 / 切片），规则见 [§ 4.2.1](#421-聚合类型的相等比较)。
- **浮点 `==` / `!=` 遵循 IEEE 754 的 ordered 语义**：有 NaN 参与时 `==` 为 `false`、`!=` 为 `true`（即 `NaN != NaN` 成立）。`struct` 的浮点字段同样遵循该语义。
- 浮点 `%`（fmod）**已实装**，走 user-space 公式 `a - trunc(a/b) * b`，语义与 C `fmod()` 一致（向 0 截断）。

#### 4.2.1 聚合类型的相等比较

`struct` / `enum` / 数组 / 切片的相等比较**按值**进行 —— 不是身份（地址）比较。

| 聚合 | 比较方式 |
|---|---|
| `struct` | **逐字段递归**比较；`PhantomData`（ZST）字段跳过；指针字段比**指针值本身**（浅比较，不解引用）；`bool` / `u8` 字段按原值比（1 字节读取后零扩展）；浮点字段按 IEEE 754 ordered 语义（见上）；**数组字段按值逐元素比**（数组在 struct 里是内联字节） |
| `enum` | 先比 **tag**；tag 相同时按**该变体**的 payload 类型比 payload（**不按字节比** —— 变体的 padding 是未初始化垃圾）；不同变体的 payload 类型不一致时**逐变体分派**（每个变体按自己的 payload 类型比） |
| 数组 | **逐元素**比较（元素是 `struct` 时递归） |
| 切片 | 比**头**（数据指针 + 长度），**不逐元素** |

约束（**编译期报错**，不静默产出错值）：

| 情形 | 诊断 |
|---|---|
| 两个操作数不是同一类型（`struct A == struct B`、`[i32;2] == [i32;3]`） | `type mismatch in binary` |
| 聚合类型的大小比较（`a < b`、`a >= b`） | `ordering comparison is not supported for struct/enum/array/slice types` |
| 操作数是**函数调用结果**（`make_p(1) == make_p(2)`） | `equality comparison of a function call result is not supported for aggregate types` |

关于最后一条：聚合返回值在 ABI 下**不统一是地址** —— > 16 B 的聚合走 sret（是地址），≤ 16 B 的走寄存器（不是地址）⇒ 按地址比会读到寄存器里的头几个字节 ⇒ 静默错值。注意形态差别：`let a = make_p(1); a == b` 里的 `a` 是**变量**（值在栈槽里）⇒ 按值比较安全 ⇒ **不报错**。

类型别名（`type Q = P`）会被**解包**后按底层类型的规则比较。

### 4.3 类型转换 `as`

| 转换 | 支持 |
|---|---|
| 整数 ↔ 整数（扩宽 / 截断） | ✅ |
| 浮点 ↔ 浮点（`f32` ↔ `f64`） | ✅ |
| 整数 ↔ 浮点 | ✅ |
| 指针 ↔ `i64` / `u64` | ✅ |
| 指针 ↔ 指针 | ✅ |
| 整数 → 指针 | ✅ |
| 布尔 ↔ 整数 | ✅ |
| 浮点 ↔ 指针 | ✅ **数值转换**（**不是**按位重解释、**不是**解引用）—— 浮点→指针：**饱和**转成 64 位无符号整数后当地址（NaN → 0；x < 0 → 0；x ≥ 2^64 → `u64::MAX`；区间内向 0 截断）；指针→浮点：地址当 64 位**无符号**整数做数值转换（整数→浮点是 roundTiesToEven，只可能丢精度，**不涉及饱和** ⇒ 与反向不对称） |

```jhyy
let addr: i64 = p as i64;
let back: *i32 = addr as *i32;
let y: f64 = x as f64;
let w: i32 = y as i32;      // 区间内截断；越界饱和到 i32::MIN/MAX；NaN → 0
```

⚠️ 浮点 → 整数采用**饱和**语义（Rust 风格）：区间内按 IEEE 754 **向 0 截断**；**越界饱和**到目标类型的 `MIN` / `MAX`；**NaN → 0**（不是 `integer indefinite`）。

⚠️ 负零（`-0.0`）向 0 截断得 `0`。浮点 ↔ 浮点（`f32` ↔ `f64`）是**值转换**（`f32 → f64` 精确无损；`f64 → f32` 收窄到单精度，x86 `cvtsd2ss` 按默认的 round-to-nearest-even 舍入），**不是**位重解释。

---

## 5. 控制流

### 5.1 if / else

```jhyy
let max = if a > b { a } else { b };
```

- 有 `else` → 表达式，类型是两个分支的统一类型。
- 无 `else` → 语句，类型为 `()`。
- 嵌套 `if / else if` 链合法。
- 分支体是**表达式**，不能写 `{ stmt; }` 块。

### 5.2 while

```jhyy
while i < 10 {
    i = i + 1;
}
```

类型为 `()`。

### 5.3 for

```jhyy
for i in 0..10 { ... }
```

- 区间 `start..end` 是**半开区间**（不含 `end`），步长 1。
- 循环变量类型从 `start` / `end` 推断。
- 支持对切片迭代（`for x in slice`）。
- 类型为 `()`。
- ⚠️ **match 里的区间是闭区间**，与 for 相反 —— 见 [§ 5.6](#56-match)。

### 5.4 break / continue

```jhyy
for i in 0..100 {
    if i > 10 { break; }
    if i % 2 == 0 { continue; }
    sum += i;
}
```

| 循环 | `break` 目标 | `continue` 目标 |
|---|---|---|
| `while` | 循环出口 | 重新测试条件 |
| `for` | 循环出口 | `i++` |

只能在循环体内使用，编译期校验。

### 5.5 return

```jhyy
fn foo(n: i32) -> i32 {
    if n < 0 { return 0; }
    n * 2
}
```

函数体最后一个表达式不加 `return` 即为返回值；`return expr;` 用于提前返回。

### 5.6 match

```jhyy
let desc = match x {
    0 => "zero",
    1 | 2 => "one or two",
    3..10 => "three to nine",
    _ => "many",
};
```

| 模式 | 语法 | 备注 |
|---|---|---|
| 字面量 | `0`、`true`、`'a'` | |
| 通配符 | `_` | |
| 多值 | `pat1 \| pat2` | 仅 enum variant；两侧必须**绑定同名同类型**的变量 |
| 范围 | `start..end` | ⚠️ **闭区间**（含两端） |
| 枚举绑定 | `Enum::Variant(x)` 或短名 `Variant(x)` | |

- 所有 arm 返回类型必须一致。
- ⚠️ **arm 的 body 只能是单个表达式** —— 不能写 `return`，也不能写成语句块（`{ ... }`）。与闭包体同款限制（§5.7）。
- **每个 match arm 是独立作用域**：arm 的模式绑定（`Some(x)` 的 `x`）是**新绑定** —— 它**遮住**外层同名变量（arm 里读到的是 payload，不是外层的旧值），arm 结束后**不外泄**。与 Rust 一致。
- **穷尽性检查已实装**：match 作用在 enum 上时，每个变体必须被显式覆盖或由 `_` 兜底，否则编译错误 `non-exhaustive match: missing variant`。
- ⚠️ **范围的端点语义与 `for` 循环不同**：`0..10` 在 match 里**同时匹配 0 和 10**（闭区间），在 `for` 里不含 10（半开）。写范围 pattern 时按闭区间理解。
- ⚠️ 不支持 **guard pattern**（`Some(x) if x > 0` → 解析错误）。
- ⚠️ 不支持嵌套 OR（`A | B | C`）与二层以上的嵌套 pattern。

### 5.7 闭包

```jhyy
let f = |x: i32| { x + 1 };
let r: i32 = f(41);        // 42
```

- 语法：`|param: T, ...| { expr }`。参数类型**必须**显式标注。
- 函数体是**一个块，块里只放单个表达式**（`|x: i32| { x + 1 }`）：里面不能写 `let` / `return` / `match` / 任何语句 —— 块只起括号作用。
- **不能捕获外层变量**。闭包体内引用外层局部变量会编译期报错：
  `closure cannot capture outer variables (not supported yet): the closure body may only use its own parameters and literals`
- ⚠️ 闭包值**可直接调用**；但「当函数值**传递**」做不到 —— 没有 `fn(...)` 类型语法（见 [§ 2.2](#22-复合类型) 与[附录 B](#附录-b未实装--已实装但受限)）。

---

## 6. 函数

```jhyy
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

- 参数**必须**显式标注类型。
- 返回类型可省略（`-> ()`），或从函数体推断。
- 递归可用（函数名在解析函数体之前注册）。
- **不支持嵌套函数** —— 所有函数必须在顶层声明（函数体里写 `fn` 是解析错误）。
- 不支持默认参数与变参。
- 函数体最后一个表达式即返回值。

### 6.1 defer

```jhyy
fn f() -> i32 {
    defer cleanup();
    return 0;
}
```

- `defer` 语句在**显式 `return`** 路径上按 **LIFO** 顺序执行（sret 路径同样覆盖）。
- ⚠️ **函数体末表达式的隐式返回不触发 defer**。`fn f() -> i32 { defer g(); 0 }` 不会调用 `g`；写成 `fn f() -> i32 { defer g(); return 0; }` 才会（见附录 B）。
- 只接受函数调用（`defer fncall();`），不支持 `defer { block; }` 块语法。
- 只允许出现在函数体顶层，不允许嵌套作用域。

### 6.2 属性

| 属性 | 作用 |
|---|---|
| `#[inline]` | 提示内联。当前实现只在**函数体是单条 `return <expr>;`** 时真正展开；struct 返回 / 多语句 / if-else / 循环体 / 递归调用都回退成普通 `call` |
| `#[naked]` | 见 [§ 17.3](#173-naked) |
| `#[link_section("...")]` | 见 [§ 17.4](#174-link_section-与-no_std) |
| `#[no_std]` | 见 [§ 17.4](#174-link_section-与-no_std) |

---

### 6.3 实参传递的寄存器规则（两个目标**相反**）

同一个「实参落在哪个寄存器」在两个目标下规则**正好相反** —— 写混合 int/float 参数时
（尤其跨目标移植、或手写汇编对接时）要注意：

| 目标 | 规则 | 例 |
|---|---|---|
| `amd64_win`（MS x64） | 整数与浮点**共享同一个位置计数器**：槽 1 → `RCX`/`XMM0`，槽 2 → `RDX`/`XMM1`，槽 3 → `R8`/`XMM2`，槽 4 → `R9`/`XMM3`，槽 ≥ 5 落栈 | `fn f(a: f64, b: i32)` ⇒ `a` 在 XMM0、`b` 在 **EDX**（**不是** ECX） |
| `amd64_sysv` | 整数与浮点是**两个独立 bank**：整数按出现顺序占 `rdi`/`rsi`/…，浮点按出现顺序占 `xmm0`/`xmm1`/…，互不影响 | `fn f(a: f64, b: i32)` ⇒ `a` 在 XMM0、`b` 在 **RDI** |

两种规则下函数的**返回值**都相同，所以纯 jhyy 代码跨目标行为一致。
完整规则见 [ABI § 3.1 / § 3.2](./jhyy-abi-v4.0.0.md#31-ms-x64amd64_win--amd64_win_freestanding)。

---

## 7. 指针与借用

### 7.1 指针

```jhyy
let mut x = 42;
let p = &x;        // *i32
let v = *p;
*p = 100;
```

- `&x` 的类型是 `*i32`。⚠️ 编译器**不检查** `x` 是否可变 —— 不可变绑定也能取地址。
- 指针算术 `p + n` / `p - n` 是**按元素**缩放的：`p + 1` 在 `*i32` 上前进 `sizeof(i32)` = 4 字节。`p - q` 的结果是**元素个数**（`i64`）。
- `null` 关键字可用。
- ⚠️ **`->` 不是成员访问运算符**（它只用于函数返回类型）。通过指针访问字段写 `(*p).field`；`p->field` 是解析错误。

### 7.2 借用 `&T` / `&mut T`

类型位置与表达式位置均可用：

```jhyy
let x: &i32 = ...;
let mut y: &mut i32 = ...;

let mut v = 42;
let r = &mut v;
```

- `sizeof(&T) == sizeof(&mut T) == 8`；`is_mut` 是编译期标记，不占内存。
- `&T`（共享）在表达式位置的**类型表示仍是 KIND_POINTER** —— `&mut expr` 才是 `KIND_REF(is_mut=1)`。
- 不支持链式 `&&T`；不支持生命周期标注 `'a`。
- **借用检查只做到最小程度**：同一作用域内重复 `&mut` 同一变量会被编译期拒绝（`cannot borrow this variable as mutable more than once at the same time`）。**完整的 NLL / Polonius 借用检查未实装** —— 见附录 B。

---

## 8. 结构体

```jhyy
type Point = struct {
    x: i32,
    y: i32,
}

let p = Point { x: 10, y: 20 };
let px = p.x;
```

- 字段按声明顺序排列、按自然边界对齐（算法见 [ABI § 2.3](./jhyy-abi-v4.0.0.md#23-struct-布局)）。
- ⚠️ **构造时允许省略字段**，编译器**不报「缺字段」错误**。
  但缺失字段的值是**未初始化读（栈上的垃圾）**，**不是 0** —— 见[附录 B](#附录-b未实装--已实装但受限)。
- 支持嵌套 struct；按值传递时递归复制。
- 按值传参与返回走 [ABI § 3.3 / § 3.5](./jhyy-abi-v4.0.0.md#33-聚合类型传参win)。

---

## 9. 枚举

```jhyy
type Option = enum {
    Some(i32),
    None,
}

let some_val = Option::Some(42);
let none_val = Option::None;
```

- tag 为 `i32`，从 0 起按声明顺序分配。
- 变体可带 payload，也可为 nullary。
- 布局算法见 [ABI § 2.4](./jhyy-abi-v4.0.0.md#24-enum-布局)。
- 配合 `match` 做穷尽性检查（[§ 5.6](#56-match)）。

---

## 10. 数组与切片

### 10.1 定长数组

```jhyy
let arr: [i32; 5] = [1, 2, 3, 4, 5];
let first = arr[0];
arr[2] = 100;
```

- 下标**不做**运行时边界检查。
- 数组 → 切片需要显式 `as [*]i32`。
- 按值传参时调用者建副本、传地址（见 ABI § 3.3）。

### 10.2 切片

```jhyy
let s: [*]u8 = "hello" as [*]u8;   // 无隐式 decay
let n = len(s);
let sub = s[1..3];
let b = s[0];
```

- 布局 `{ data: *T, len: i64 }`，16 字节。
- 支持字面量、索引、子切片、长度查询、`for x in slice` 迭代。
- 可作为函数参数传递。
- `len()` 是内建，**只接受切片 / 数组**；对字符串字面量（`*u8`）不适用。

---

## 11. 泛型

### 11.1 泛型 struct / enum

```jhyy
type Pair<T> = struct { a: T, b: T }
type Option<T> = enum { Some(T), None }

let p: Pair<i32> = Pair<i32> { a: 1, b: 2 };
```

- **单态化已激活**：每个实例是一份独立的克隆 AST + 独立的 `*Sym`。
- type-param 名**约定**大写起始（**未强制**；大写检查只用于区分泛型类型实参与 `<` 运算符）。
- mangling：`<Base>$<T1>$<T2>...`（例如 `Pair$i32`）。

### 11.2 泛型函数

```jhyy
fn max<T>(a: T, b: T) -> T {
    if a > b { return a; }
    return b;
}

let mi: i32 = max::<i32>(3, 5);   // turbofish
let mf: f64 = max(3.0, 5.0);      // 调用点推断
```

- **turbofish `name::<T>(...)` 已实装**。
- **调用点类型推断已实装**（从实参推断 `T`，支持多 type-param、递归推断、按 mangled name 去重）。
- 泛型定义本身不生成代码，只有实例化的克隆版本生成代码。
- 推断失败时报错 `E0062`。

### 11.3 不支持

- 泛型约束 `<T: Ord>`
- 生命周期泛型 `<'a, T>`
- const generic
- trait objects
- HKT

---

## 12. 顶层 const 数组

```jhyy
const ASCII_LOWER: [u8; 26] = [97, 98, 99, /* ... */ 122];

fn main_jhyy() -> i32 {
    ASCII_LOWER[25] as i32   // 122
}
```

- 仅支持**顶层** `const`；函数体内不允许。
- 元素应当是 const 表达式（字面量、struct 字面量）。
- ⚠️ **编译器不做 const 表达式检查**：元素位置放函数调用能编译通过，但**不会被求值**，运行时取到 0。
- 不允许 `const` 指针、`const` 切片。⚠️ **`const` enum 数组实际是允许的**（无报错）。
- 落到 **`.data`** 段（当前不是只读段），以 `leaq SYMBOL(%rip)` 形式零成本寻址。

---

## 13. 模块与导入

```jhyy
import mylib;
import vec;          // 标准库模块,不带 std:: 前缀
```

- 语法是**单个标识符**。⚠️ `import std::vec;` 是**解析错误**（`expected ;, got ::`）。
- 查找顺序：**main 文件旁边 → 标准库目录**两级回落。因此 `import vec;` 会找到标准库的 `vec` 模块。
- `import` 惯例写在文件顶部，但 ⚠️ 编译器**不强制位置**（写在其他声明之后也能编译）。
- **传递性**：`import` 是递归的（`main → a → b` 时 `main` 可用 `b` 的声明）。
- **循环检测**：成环时编译报错 `circular import '...'`（不崩溃）。
- **模块命名空间**：不同模块可定义同名函数，用 `mod::fn()` 限定调用（符号 mangle 见 ABI § 3.6）。
- **不支持嵌套 import 路径**（无 `import utils::io`）。

```jhyy
// lib_a.jhyy
fn process() -> i32 { 100 }

// main.jhyy
import lib_a;
fn main_jhyy() -> i32 {
    lib_a::process()
}
```

---

## 14. FFI

```jhyy
extern fn puts(s: *u8) -> i32;
extern fn fopen(path: *u8, mode: *u8) -> *u8;
```

- `extern fn` 只声明、不生成函数体，链接期由 `ld` 解析符号。
- 汇编符号**不加修饰**（[ABI § 3.6](./jhyy-abi-v4.0.0.md#36-名称修饰)）。
- **不支持变参**：`printf` 的每个参数必须在 JHYY 侧逐个列出。
- ⚠️ **参数 / 返回类型不做限制**：声明 `extern fn takes(s: MyStruct) -> i32;` 能编译通过（且**不会**按值跨 FFI 传 struct —— 实际按地址传，与 C ABI 不符）。

---

## 15. 标准库

8 个模块，随编译器一同安装。**导入时写模块名本身，不带 `std::` 前缀**：

```jhyy
import mem;
import fmt;
import string;
import arena;
import io;
import os;
import vec;
import math;
```

| 模块 | 公开 API |
|---|---|
| `mem` | `ptr_add`、`mem_copy`、`mem_compare`、`mem_set`、`mem_find_byte`、`mem_zero` |
| `fmt` | `ptr_add`、`digit_char`、`hex_char`、`fmt_i32`、`fmt_i64`、`fmt_str`、`fmt_hex_u32` |
| `string` | `str_from_cstr`、`str_from_bytes`、`str_len`、`str_data`、`str_concat`、`str_equals`、`str_compare`、`str_find`、`strlen_local` |
| `arena` | `arena_init`、`arena_alloc`、`arena_alloc_aligned`、`arena_calloc`、`arena_reset`、`arena_free`、`arena_new_block`、`align_up`、`ptr_add` |
| `io` | `std_io_open`、`std_io_close`、`std_io_read`、`std_io_write`、`std_io_print`、`std_io_print_err`、`std_io_eprint` |
| `os` | `std_os_open`、`std_os_close`、`std_os_read`、`std_os_write`、`std_os_exit`、`std_os_getenv`、`OS_O_RDONLY()`、`OS_O_WRONLY()`、`OS_O_RDWR()`、`OS_O_CREAT()`、`OS_O_TRUNC()`、`OS_O_APPEND()`、`OS_MODE_RW_R()` |
| `vec` | `std_vec_new`、`std_vec_with_cap`、`std_vec_push`、`std_vec_get`、`std_vec_len`、`std_vec_cap`、`std_vec_free`、`std_vec_grow`、`std_vec_byte_copy` |
| `math` | `std_math_sin`、`std_math_cos`、`std_math_sqrt`、`std_math_pow`（**仅 f64**） |

- ⚠️ `std::os` 的 `OS_O_*` / `OS_MODE_RW_R` 是**零参函数**，不是常量 —— 用法是 `os::OS_O_CREAT()`。不带括号会得到 `expected (, got ;`。
- `std::os` 的文件描述符 API 通过 C bridge 接真实 POSIX / Win32 调用；`std_os_exit` 会真正终止进程。POSIX / Win 的 `O_*` flag 差异在桥这一层翻译掉。
- `std::math` 只有 f64 版本，无 f32 版本，也无 `tan` / `log` / `exp` / `floor` / `ceil`。

---

## 16. 命令行

```
jhyy [--target=<triple>] [--help] <command> [args]
```

| 命令 | 作用 |
|---|---|
| `compile <file.jhyy> [-o output]` | 编译为目标文件（Windows 上链接为 `.exe`） |
| `build <file.jhyy> [-o output]` | 编译 + 链接 |
| `run <file.jhyy>` | 编译 + 链接 + 执行 |
| `dump <file.jhyy>` | 打印 AST / 定型 IR 供调试 |

| 标志 | 作用 |
|---|---|
| `--target=<triple>` | 选择目标（默认 `amd64_win`）。可选值见 [ABI § 1](./jhyy-abi-v4.0.0.md#1-目标平台) |
| `--no-link` | 只产出 `.s`，跳过 gcc 链接 |
| `--help` | 打印完整帮助 |

⚠️ **命令行只接受一个输入文件**，多余的文件参数被静默忽略（见 [§ 1.2](#12-源文件与多文件)）。

---

## 17. 底层与 OS 扩展

### 17.1 `volatile`

```jhyy
let mut mmio: volatile i32 = 0 as i32;
let a: i32 = mmio;   // volatile load
mmio = 42;           // volatile store
```

- 只修饰**基础类型**；修饰 struct / 指针 / 数组 / 切片是编译错误；`volatile volatile T` 是编译错误（`chained 'volatile volatile' is not allowed`）。
- 布局与 `T` 完全相同，不改变 ABI。
- 保证单线程内每次访问命中内存、不重排、不做寄存器缓存。**跨线程序需配合 `fence_*`**。

### 17.2 `asm!`

```jhyy
asm!("nop");
asm!("cpuid");
```

- 语句位置专用，不能作表达式值使用。
- 单字符串参数；**不支持操作数约束**、模板占位符、clobber 声明（`asm!(...) operands are not supported ... single-string-literal only`）。
- AT&T 语法，x86-64 only。
- **内联在函数体当前位置**（文本 hex 编码进 IL，后端在该位置解回原文写入 `.s`）。这一点是正确性问题：早期实现把它 append 到 `.s` 末尾，落在所有函数之外成为**死字节**。

### 17.3 `#[naked]`

```jhyy
#[naked]
fn irq_entry() {
    asm!("pushq %r15");
    asm!("iret");
}
```

- 无 prologue / epilogue，完全控制寄存器与栈。
- 函数体**只能**含 `asm!(...)` 语句（`naked function body may only contain asm!(...) statements`）；局部变量 / 控制流 / `return` 是编译错误。
- 不参与 sret；被调用方需自行保存 callee-saved 寄存器。

### 17.4 `#[link_section]` 与 `#[no_std]`

```jhyy
#[link_section(".text.boot")]
fn _start() -> i32 { return 42 as i32; }
```

```jhyy
#[no_std]
fn main() -> i32 { return 42 as i32; }
```

- `#[link_section("name")]` 只作用于函数声明，改变符号落入的 section，不改变调用约定。section 名必须是可打印 ASCII（否则 `link_section name contains non-ASCII byte`）。
- `#[no_std]` 是**模块级**属性，不链接 C 运行时启动文件，入口符号改为 `main`；没有 `fn main` 会得到 `error: #[no_std] module must define 'fn main()'`。

### 17.5 内存屏障

```jhyy
fence_seq_cst();   // mfence
fence_acquire();   // lfence
fence_release();   // sfence
```

- 三个内建函数，无参数，语句位置，返回 `()`。
- **内联在调用点**（与 `asm!` 同一条 `dbgasm` 通道）。
- 只覆盖 x86-64；没有 ARM / RISC-V 版本。

### 17.6 freestanding 目标与 entry 符号

`--target=amd64_win_freestanding` / `amd64_sysv_freestanding` 选择的是**调用约定归属**（见 [ABI § 1](./jhyy-abi-v4.0.0.md#1-目标平台)），**不改变链接方式**。

- **entry 符号由用户自行提供**，编译器不提供默认 entry：

  | 场景 | entry 符号 | 签名 |
  |---|---|---|
  | UEFI | `efi_main` | `fn efi_main(ImageHandle: *u8, SystemTable: *u8) -> Status` |
  | 裸机 / Linux ELF | `_start` | `fn _start() -> ()` |

- ⚠️ **要得到纯 freestanding 产物，源文件还必须带 `#[no_std]`** —— 链接行是按 `#[no_std]` 属性分支的，**不是按 `--target`**：
  - 带 `#[no_std]` → 不链 C 运行时（runtime.o / helpers.o），加 `-nostartfiles -nodefaultlibs -Wl,--entry=main -lgcc`
  - 不带 → 照常链 runtime + helpers + Windows 系统库
- ⚠️ freestanding 的两个编译期钩子（`emit_entry_point` / `no_crt_init`）**当前都是空实现** —— 编译器**不**生成 UEFI EFIAPI wrapper，**也不**自动抑制 CRT 链接。
- ⚠️ 即使带 `#[no_std]`，链接行仍会无条件追加 `-lm -lkernel32 -luser32 -lshell32 -ladvapi32`。真正的 UEFI / 裸机镜像需要**自行**用 lld-link（`/SUBSYSTEM:EFI_APPLICATION /ENTRY:efi_main`）或自定义链接行完成。
- freestanding 模式下 `extern fn` 必须显式声明，并按该目标的调用约定调用。

---

## 18. 错误码与诊断

| 码 | 触发 |
|---|---|
| `E0050` | 实例化 `PhantomData<T>`（带 init 的 `let`） |
| `E0060` | 在非泛型作用域出现未实例化的裸 type-param `T`（`unresolved type parameter; generic must be instantiated`） |
| `E0062` | 泛型 type-param 无法从实参推断 / 推断冲突 |

其余诊断以文本形式给出，无编号。高频文本：

| 文本 | 场景 |
|---|---|
| `non-exhaustive match: missing variant` | enum match 未覆盖全变体 |
| `closure cannot capture outer variables (not supported yet): the closure body may only use its own parameters and literals` | 闭包捕获外层变量 |
| `cannot assign to immutable variable (use let mut)` | 给不可变绑定赋值 |
| `cannot borrow this variable as mutable more than once at the same time` | 同作用域双 `&mut` |
| `circular import '<path>'` | import 成环 |
| `unexpected token ';' in expression` | `type` 声明后多写了 `;` |
| `expected ;, got ::` | `import std::xxx;`（应为 `import xxx;`） |

---

## 19. Debug ABI（🔒 per D41）

> **状态**：🔒 v2.2.0 锁定 Debug ABI 跨项目契约，随本规范 v4.0.0 一并继承。
> **权威位置**：**本节即权威**（编译器侧）。原 OS 端镜像 `jhyy_OS/docs/v0.0.4-debug-abi.md`（🔒 Locked 2026-08-12，Q-Compiler-007 闭环 / D41）已随 OS 侧文档整体清理于 2026-10-30（commit `f98d83d`）⇒ **OS 侧重写时从本节镜像，不得反向**。
> **doc version pinning**：本节锁定时引用 OS doc 的 commit/tag；OS 端后续更新走 Q-Compiler-007 流程同步。

### 19.1 尺寸定案（per D41）

| 类型 | 尺寸 | 说明 |
|------|------|------|
| `DebugEvent`（定长 header + nested payload） | **56B** | OS 端 kernel introspection 输出 |
| `ErrChain`（含 `SourceLoc` 24B 内嵌） | **64B** | 错误链，NULL-ended |
| `ProvenanceInfo`（DAG parents/children K=8） | **136B** | `Cap<T>` runtime trace metadata |

**布局总原则**（per D41 R1/R2）：jhyy **无 `packed` / `repr(...)`**；所有跨边界 struct 一律自然对齐；padding 显式写成 `_pad*` 字段。

### 19.2 jhyy 侧类型表达

jhyy 侧类型表达**严格遵循 [§ 20](#20-wire-format--jhyy-侧表达规则-per-d40) 的 wire-format 规则**（per D40）：

| wire 字段 | jhyy 表达 | 说明 |
|----------|----------|------|
| `ProvenanceInfo.grant_chain` / `revoke_chain` | `*ProvenanceInfo`（裸指针） | NULL 结尾单向链 |
| `ErrChain.prev` | `*ErrChain`（裸指针） | NULL 结尾单向链 |
| `ErrChain.trace` / `ErrChain.context` | `[*]TraceEntry` / `[*]u8` 切片 | 显式 `*_len` 字段 |
| `DebugEvent.payload` | `*u8` + `payload_len` | 跨 FFI 用指针，长度由显式字段提供 |

### 19.3 jhyy 编译器不生成 DWARF debug info（per D41 R3）

- jhyy 编译器 emit `dbgfile` + `dbgloc` 指令，**仅 line table**。
- **不**生成 DWARF `.debug_info` / `.debug_abbrev` / `.debug_line` 完整 section。
- debug 数据由 OS 端 runtime side table 承载；release build 可 strip runtime debug info。

### 19.4 FFI 边界提醒（per D41 R4）

本节全部 struct 都是**内存布局契约**（指针传递），**不得按值跨 FFI 边界**。集成 `SysError.chain` 时必须以指针传 `ErrChain`。

---

## 20. Wire Format ↔ jhyy 侧表达规则（🔒 per D40）

> **状态**：🔒 v2.2.0 锁定跨 FFI 边界时 wire-format C struct 字段到 jhyy 类型表达的系统规则（per D40，2026-08-12 锁，修订 D14 字段类型部分，D14 主体不变）。

### 20.1 两条核心映射

| wire 字段特征 | jhyy 表达 | 尺寸 | 说明 |
|--------------|----------|------|------|
| wire 有显式 `*_len: usize` 字段 | `[*]T` 切片 | 16B（ptr + len） | 长度由字段提供 |
| wire 是 NULL-terminated 单向链 | `*T` 裸指针 | 8B | NULL 表示 chain 末尾 |

### 20.2 wire `*_len` → `[*]T` 切片

```c
typedef struct { uint8_t* data; uint64_t data_len; } Buffer;
```

```jhyy
type Buffer = struct {
    data: [*]u8   // 切片 = ptr(8B) + len(8B)
}
```

`data` 是 wire `uint8_t*` + `data_len` 合并表达；**jhyy 类型层不区分**（wire 两字段是同一语义）。

### 20.3 wire NULL-ended chain → `*T` 裸指针

```c
typedef struct ErrChain { struct ErrChain* prev; SourceLoc loc; uint32_t code; } ErrChain;
```

```jhyy
type ErrChain = struct {
    prev: *ErrChain    // NULL-ended 单向链
    loc: SourceLoc
    code: u32
}
```

`*ErrChain` 裸指针 = wire `ErrChain*`（NULL = chain root）。

### 20.4 跟 D14（FFI 边界）的关系

- D14 主体规则不变；本节是 D14 在 wire-format 字段类型层的具体扩展。
- 任何与 D40 锁的偏差走 Q-Compiler-XXX 流程。
- 本节跟 freestanding 的 MS x64 约定、[§ 19](#19-debug-abi-per-d41) 的 Debug ABI、`Cap<T>` runtime 链用例一致 —— `Cap<T>` runtime `*T` 链 + `ProvenanceInfo.grant_chain` `*T` 链全部用 `*T` 裸指针。

---

## 附录 A：与 v1.3.0 的差异

| v1.3.0 | v4.0.0 |
|---|---|
| 本体不含 v3.x 特性，靠 17 份 supplement 补充 | 已实装特性全部收进正文，supplement 作废 |
| 后端是 QBE | 自托管 amd64 后端，QBE 已移除 |
| 仅 `amd64_win` | 四个目标（见 ABI § 1） |
| `&mut` 仅有类型解析，检查是 stub | 最小独占检查已实装（同作用域双 `&mut` 编译期拒绝） |
| `asm!` / fence append 到 `.s` 末尾（实际不执行） | 内联在函数体当前位置 |
| `#[link_section]` 是 no-op | 已打通 |
| `std_os_*` 是 mock | 接真实 libc / Win32 |
| 泛型只有 struct/enum，fn 路径待定 | struct / enum / fn / turbofish / 调用点推断全实装 |
| 无 std lib | 8 个模块（§ 15） |
| 文档化了从未实装的块表达式 | 已删除（未实装 → 附录 B） |
| 文档化了会静默算错的 `1_000_000` | 已删除（未实装 → 附录 B） |
| `import std::xxx;` | `import xxx;`（模块名不带 `std::` 前缀） |
| `type X = ...;` 带分号 | `type X = ...` 不带分号 |
| match 范围标为「半开」 | match 范围是**闭区间**（与 for 相反） |
| defer 声称「覆盖所有返回路径」 | 只覆盖**显式 `return`** 路径 |
| 多文件靠命令行列文件 | 多文件靠 `import`；命令行只接受一个输入文件 |

---

## 附录 B：未实装 / 已实装但受限

> 这里列出的项**都不在本规范正文的承诺范围内**。

### 未实装

- **单元类型 `()`** —— `()` 在类型位置不被接受（`let x: () = ();` / `fn f() -> ()` 都是解析错误）
- **`fn(...)` 函数指针类型语法** —— 类型位置不认 `fn(i32)` / `fn(i32) -> i32` ⇒ 闭包值**无法作为函数值传递**
- 完整 NLL / Polonius 借用检查、生命周期标注 `'a`、reborrow、跨函数借用
- 闭包捕获外层变量 —— **编译期明确报错**，不静默生成错误代码
- **match arm 的 body 不能是语句块** —— 只能是单个表达式（不能写 `return` / `{ ... }`；与闭包体同款限制）
- 块表达式（`let v = { ... };`）—— 表达式位置不认 `{`
- 泛型约束 `<T: Ord>`、生命周期泛型、const generic、trait objects、HKT
- 变参函数、回调函数、struct/enum 按值跨 FFI 边界
- `Cap<T>` 的字段访问（`.cnode_idx` / `.depth` / `.rights`）；`Cap<T>` 的 `T` 不被解析
- `std::math` 的 f32 版本与 `tan` / `log` / `exp` / `floor` / `ceil`
- async / await、`std::map`
- aarch64 / riscv64 目标、`.jhyynb` 原生二进制格式
- `asm!` 的操作数约束、clobber 声明、Intel 语法
- match 的 **guard pattern**（`Some(x) if x > 0`）
- 浮点字面量的**指数写法**（`1.0e10`）

### 已实装但受限（附台账编号）

| 项 | 现象 | 台账 |
|---|---|---|
| **`argv` 的类型写作 `*u8`，实际是 `char **`** | 入口签名里的 `argv` 是「指向指针数组的指针」，但类型写作 `*u8` ⇒ `*argv` 只 load **1 字节**（IL `loadub`）—— 那是 `argv[0]` **指针的最低字节**，不是指针本身 ⇒ 拿它跟 `0` 比等于断言「堆地址最低字节 ≠ 0」（跟堆布局绑定的假信号）。读 `argv[i]` 必须先 `argv as **u8`（见 §1.1） | **W-157** |
| **聚合 `==` 不接受函数调用结果** | `make_p(1) == make_p(2)` 编译期报错(`equality comparison of a function call result is not supported for aggregate types`)。聚合返回值在 ABI 下**不统一是地址**(>16B 走 sret 是地址;≤16B 走寄存器)⇒ 按地址比会读到寄存器里的头几个字节。**形态差别**:`let a = make_p(1); a == b` 里的 `a` 是**变量**(值在栈槽里)⇒ 安全 ⇒ 不报错 | **W-133.1** |
| **聚合的大小比较未实装** | `a < b` / `a >= b`(struct / enum / 数组 / 切片)编译期报错(`ordering comparison is not supported for struct/enum/array/slice types`)—— 聚合的大小比较无定义 | **W-133.2** |
| **struct 字面量的字段值类型必须精确匹配字段类型** | `type P = struct { c: u8 }` 写 `P { c: 7 }` 报 `field type mismatch` —— 整数字面量默认推断为 `i32`,与 `u8` 不相等。须写成 `let c: u8 = 7;` 再 `P { c: c }` | **W-133.3** |
| **struct 字面量省略的字段未初始化** | 编译器不报「缺字段」错误，但缺失字段的值是**栈上的未初始化垃圾**，**不是 0**（毒化栈后实测 y=0 / z=garbage，每次可能不同） | — |
| **不可变性的写保护未实装** | 编译器不检查取地址对象是否可变；`&x` 对不可变绑定合法，`*p = v` 不报错也**不生效** | — |
| **函数实参类型不检查** | `f(5)` 传给 struct 形参能编译，运行时按 struct 布局读寄存器 → **访问违例崩溃** | — |
| 借用检查只覆盖「同作用域内双 `&mut`」 | 词法作用域会误报「借用提前结束」的情况尚未处理 | — |
| 嵌套泛型 `Vec<Vec<T>>` | 未被测试套件覆盖，行为不应依赖 | — |
| `const` 元素不做 const 检查 | 元素位置放函数调用能编译，但不会被求值，运行时取到 0 | — |
| **顶层全局变量只有整数类型初始化正确** | `let mut f: f64 = 3.5;` 读到 **0**（初始化器被丢弃）；`let mut p: Point = ...` 读到**垃圾**（未定义读）。整数类型（含跨函数读写链）正确 | — |
| `match` 范围是闭区间 | 与 `for` 的半开区间语义相反，容易踩 | — |
| `defer` 不覆盖隐式返回 | 函数体末表达式返回时 defer 不执行 | — |
| `std_io_print` / `std_io_print_err` | 依赖 libc 的 `stdout` / `stderr` 句柄获取 | — |
| SysV 下 MEMORY class 参数与寄存器溢出参数混排 | 编译报错（[ABI § 12.4](./jhyy-abi-v4.0.0.md#abi-12-4)） | — |
| 无交叉编译容器后端 | `--target` 不切换 PE / ELF 产出 | — |

---

## 附录 C：自举兼容性

**自举（self-hosting）= 用 JHYY 写 JHYY 编译器**。

- v1.0.0 已达成真自举闭环（commit `eabee0d`，2026-08-10）。
- v4.0.x 世代的闭环形态是「`jhyy.exe` 自己编 src0，产出与自身 byte-equal」—— 见 `docs/internal/build.md` 与 `compiler/tests/bootstrap/fixed_point.sh`。
- **自举编译器本身是本规范的最大消费者**：规范里每条关于「已实装」的断言，在 `compiler/src0/*.jhyy` 里都能找到对应实现。
- 规范改动对自举的影响面：`docs/internal/conventions.md` 要求 `docs/abis/*` 变更后跑一遍 `regress.py`（spec 改动可能影响 jhyy 端解析）。

---

## 附录 D：完整示例

```jhyy
// 完全可编译的一个程序：入口 + 泛型 + struct + enum + match + 闭包 + defer
import vec;

type Shape = enum {
    Circle(i32),
    Rect(i32, i32),
    Empty,
}

type Point = struct {
    x: i32,
    y: i32,
}

fn area(s: Shape) -> i32 {
    match s {
        Shape::Circle(r) => 3 * r * r,
        Shape::Rect(w, h) => w * h,
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
    let s = Shape::Rect(p.x, p.y);
    let a = area(s);

    let f = |n: i32| { n * 2 };
    let d = f(a);

    let m: i32 = max::<i32>(d, 100);

    return m;   // 100
}
```

---

## Cross-ref

- ABI：[`jhyy-abi-v4.0.0.md`](./jhyy-abi-v4.0.0.md)
- 二进制格式（设计稿，未实装）：[`jhyy-binary-format-v1.0.0.md`](./jhyy-binary-format-v1.0.0.md)
- 历史档案：v1.3.0 及其 17 份 v3.x supplement、v1.1.0、v1.0.0、v0.2.1、v0.0.1 —— 均已归档至 git 历史（`git show <sha>:docs/abis/<name>`）
- 已知限制台账：[`docs/internal/workarounds.md`](../internal/workarounds.md)
