# JHYY 语言规范 v1.0.0

**日期**: 2026-06-21
**状态**: 锁定（self-hosting 启动门槛）
**覆盖**: 编译器 v0.6.0 全部可用语法
**不覆盖**: 已声明但 codegen 缺失的特性（见附录 B）

---

## 目录

1. [程序结构](#1-程序结构)
2. [类型系统](#2-类型系统)
3. [变量与绑定](#3-变量与绑定)
4. [字面量](#4-字面量)
5. [运算符与类型转换](#5-运算符与类型转换)
6. [表达式](#6-表达式)
7. [控制流](#7-控制流)
8. [函数](#8-函数)
9. [指针](#9-指针)
10. [结构体](#10-结构体)
11. [枚举与模式匹配](#11-枚举与模式匹配)
12. [模块与导入](#12-模块与导入)
13. [FFI 与外部函数](#13-ffi-与外部函数)
14. [编译器使用](#14-编译器使用)
15. [完整示例](#15-完整示例)
16. [附录 A：与 v0.2.1 的差异](#附录-av021-的差异)
17. [附录 B：已知限制](#附录-b已知限制)
18. [附录 C：自举兼容性](#附录-c自举兼容性)

---

## 1. 程序结构

### 1.1 入口点

每个 JHYY 程序必须定义 `main_jhyy` 函数，运行时调用它，返回值作为进程退出码。

```rust
fn main_jhyy() -> i32 {
    0
}
```

### 1.2 源文件

- 后缀 `.jhyy`，UTF-8 编码
- 可拆分为多个文件，通过 `import` 组合（见第 12 节）
- CLI: `jhyy compile main.jhyy lib.jhyy -o output`

### 1.3 注释

```rust
// 单行注释
/* 块注释 */
```

### 1.4 语句分隔

语句以换行或 `;` 分隔。`;` 主要用于同一行内写多条语句：

```rust
let x = 1;
let y = 2
let z = 3; let w = 4
```

### 1.5 顶层声明

每个源文件的顶层允许以下声明：

| 声明 | 语法 | 说明 |
|------|------|------|
| 函数 | `fn name(...) -> T { ... }` | 普通函数 |
| 外部函数 | `extern fn name(...) -> T;` | FFI 声明（无函数体） |
| 类型别名 | `type Name = ...;` | struct/enum/原语别名 |
| 导入 | `import module;` | 导入同目录下其他 .jhyy 文件 |
| 变量 | `let mut name: T = expr;` | 顶层可变变量（v0.5 起允许） |

---

## 2. 类型系统

### 2.1 基本类型

| 类型 | 大小 | 对齐 | 说明 |
|------|------|------|------|
| `i8`  | 1 | 1 | 有符号 8 位整数 |
| `i16` | 2 | 2 | 有符号 16 位整数 |
| `i32` | 4 | 4 | 有符号 32 位整数 |
| `i64` | 8 | 8 | 有符号 64 位整数 |
| `u8`  | 1 | 1 | 无符号 8 位整数 |
| `u16` | 2 | 2 | 无符号 16 位整数 |
| `u32` | 4 | 4 | 无符号 32 位整数 |
| `u64` | 8 | 8 | 无符号 64 位整数 |
| `f32` | 4 | 4 | 32 位浮点 (IEEE 754) |
| `f64` | 8 | 8 | 64 位浮点 (IEEE 754) |
| `bool` | 1 | 1 | 布尔值 (`true` / `false`) |
| `()`  | 0 | 1 | unit 类型（类似 void） |

### 2.2 复合类型

| 类型 | 大小 | 说明 |
|------|------|------|
| `*T` | 8 | 指针，64 位地址 |
| `[T; N]` | `sizeof(T) * N`（对齐） | 定长数组，N 是编译期常量 |
| `[*]T` | 16 | 切片：`{ptr: *T, len: i64}` (v0.6 完整 codegen) |
| `struct { ... }` | 字段之和（对齐） | 结构体 |
| `enum { ... }` | tag(4) + max_payload（对齐） | 带标签联合体 |

### 2.3 类型别名

```rust
type Age = i32;
type Point = struct { x: i32, y: i32 };
type Node = enum { Leaf, Branch(*Node, *Node) };
```

类型别名不创建新类型——`type Age = i32` 后 `Age` 和 `i32` 完全等价。但 `struct` / `enum` 定义是**名义类型**：

```rust
type A = struct { x: i32 };
type B = struct { x: i32 };
// A 和 B 是不同类型，不能互相赋值
```

### 2.4 类型推断

- 参数**必须**显式标注类型
- 局部变量从初始化表达式自动推断
- 函数返回类型可从函数体推断（标注为 `()` 时）
- 字面量与算术运算根据上下文自动推断

```rust
fn add(a: i32, b: i32) -> i32 {  // 参数必须标注
    a + b                         // 返回类型标注
}

fn infer() {                      // 无标注 → 从体推断
    let x = 42;                   // x: i32（默认）
    let y = 3.14;                 // y: f64
    let z = x + y;                // ❌ 错误：i32 + f64 类型不匹配
}
```

### 2.5 整数字面量后缀

```
42i8, 42i16, 42i32, 42i64
42u8, 42u16, 42u32, 42u64
```

无后缀整数字面量默认为 `i32`。

### 2.6 浮点字面量后缀

```rust
let a = 3.14;        // f64
let b: f32 = 1.5;    // f32（上下文推断）
let c = 2.0e10f32;   // 显式 f32 后缀
```

---

## 3. 变量与绑定

### 3.1 不可变绑定 (`let`)

```rust
let x = 42;
let y = x + 1;
let z: i64 = 100;  // 带显式类型标注
```

- 不分配栈空间（编译器优化为 SSA 临时量）
- 不可重新赋值
- 不可取地址

### 3.2 可变绑定 (`let mut`)

```rust
let mut counter = 0;
counter = 10;
counter += 5;
```

- 在栈上分配空间
- 可以重新赋值
- 可取地址 `&counter`

### 3.3 复合赋值

```rust
x += 1;   // x = x + 1
x -= 1;   // x = x - 1
x *= 2;   // x = x * 2
x /= 2;   // x = x / 2
x %= 3;   // x = x % 3
```

仅适用于可变变量。

### 3.4 shadowing

```rust
let x = 5;
let x = x + 1;   // 新绑定，覆盖旧的（不可变）
let mut x = x * 2;  // 覆盖为可变
```

---

## 4. 字面量

### 4.1 整数字面量

```rust
let dec = 42;                  // 十进制
let hex = 0xFF;                // 十六进制
let oct = 0o77;                // 八进制
let bin = 0b1010;              // 二进制
let with_suffix = 100i64;      // 带类型后缀
let big = 1_000_000;           // 下划线分隔
let neg = -42;                 // 负数（一元减）
```

### 4.2 浮点字面量

```rust
let pi = 3.14;           // f64
let half = 0.5;
let exp = 1.0e10;
let tiny = 1e-5f32;      // 显式 f32 后缀
```

浮点字面量在 codegen 中正确发射为 QBE `s_`/`d_` 字面量（v0.5 修复）。

### 4.3 布尔字面量

```rust
let yes = true;
let no = false;
```

类型为 `bool`，在 QBE 中表示为 `w`（0 或 1）。

### 4.4 字符字面量

```rust
let a = 'a';
let newline = '\n';
let tab = '\t';
let chinese = '你';
```

类型为 `i32`。支持转义：

| 转义 | 含义 |
|------|------|
| `\n` | 换行 (0x0A) |
| `\t` | 制表 (0x09) |
| `\r` | 回车 (0x0D) |
| `\0` | 空字节 (0x00) |
| `\\` | 反斜杠 |
| `\'` | 单引号 |
| `\"` | 双引号 |
| `\xHH` | 十六进制字节 |

### 4.5 字符串字面量

```rust
let greeting = "你好，世界！";
let with_escape = "第一行\n第二行";
```

类型为 `*u8`（指向 null 终止 UTF-8 字节串的指针）。

---

## 5. 运算符与类型转换

### 5.1 运算符优先级（从低到高）

| 优先级 | 运算符 |
|--------|--------|
| 1 (最低) | `=` |
| 2 | `+=` `-=` `*=` `/=` `%=` |
| 3 | `&&` `\|\|` |
| 4 | `==` `!=` `<` `>` `<=` `>=` |
| 5 | `\|` |
| 6 | `^` |
| 7 | `&` |
| 8 | `<<` `>>` |
| 9 | `+` `-` |
| 10 | `*` `/` `%` |
| 11 | `-` `!` `~` `&` `*` (一元前缀) |
| 12 | `as` (类型转换) |
| 13 (最高) | `.` `->` `()` `[]` |

### 5.2 算术运算

```rust
a + b    // 加法
a - b    // 减法
a * b    // 乘法
a / b    // 除法
a % b    // 取模（整数；浮点取模见附录 B）
-a       // 取负
```

整型溢出：二补码环绕（明确语义，不是 UB）。

### 5.3 比较运算

```rust
a == b   // 等于
a != b   // 不等于
a < b    // 小于
a > b    // 大于
a <= b   // 小于等于
a >= b   // 大于等于
```

返回 `bool`。比较指令根据操作数类型自动选择：
- 有符号 / 无符号
- 32 位 (`w`) / 64 位 (`l`)
- 浮点直接用 QBE 浮点比较

### 5.4 逻辑运算（短路求值）

```rust
a && b   // 逻辑与：a 为 false 时不求值 b
a || b   // 逻辑或：a 为 true 时不求值 b
!a       // 逻辑非
```

`&&` 和 `||` 是**短路求值**。右侧操作数只在必要时才求值（QBE 用分支跳转 + phi 实现）。

### 5.5 位运算

```rust
a & b    // 按位与
a | b    // 按位或
a ^ b    // 按位异或
a << b   // 左移
a >> b   // 右移
~a       // 按位取反
```

移位宽度根据操作数类型自动选择（`w` 或 `l`）。

### 5.6 类型转换 (`as`)

`as` 关键字做显式类型转换。允许的转换：

| 从 → 到 | i32 | i64 | f32 | f64 | *T |
|---------|-----|-----|-----|-----|-----|
| i8/i16/i32 | ✓ (扩宽) | ✓ (扩宽) | ✗ | ✗ | ✗ |
| i64 | ✓ (截断) | ✓ | ✗ | ✗ | ✗ |
| u8/u16/u32 | ✓ | ✓ | ✗ | ✗ | ✗ |
| u64 | ✓ | ✓ | ✗ | ✗ | ✗ |
| f32 | ✗ | ✗ | ✓ | ✓ (扩宽) | ✗ |
| f64 | ✗ | ✗ | ✓ (截断) | ✓ | ✗ |
| *T | ✗ | ✗ | ✗ | ✗ | ✓ (其他指针类型) |

整型 ↔ 浮点的转换通过 QBE 的 `dtosi` / `sltof` 等指令实现。

```rust
let x: i32 = 42;
let y: f64 = x as f64;     // i32 → f64
let z: i64 = x as i64;     // i32 → i64 (扩宽)
let w: i32 = y as i32;     // f64 → i32 (截断)
```

**整数 ↔ 整数、浮点 ↔ 浮点**：直接扩宽或截断。
**整数 ↔ 浮点**：用 `as` 显式转换，不允许隐式。
**指针 ↔ i64 (v0.6)**：用于 FFI 和底层模块。Windows x64 上指针即为 64 位值。

```rust
// v0.6: 指针 ↔ 整数互转 (用于 arena.jhyy 等底层模块)
let x: i32 = 42;
let p: *i32 = &x;
let addr: i64 = p as i64;      // *T → i64 (usize equivalent)
let back: *i32 = addr as *i32; // i64 → *T
```

---

## 6. 表达式

### 6.1 块表达式

```rust
let val = {
    let a = 10;
    let b = 20;
    a + b    // 最后一个表达式是块的值
};
// val = 30
```

块的类型是最后一个表达式的类型。无最后表达式时类型为 `()`。

### 6.2 if-else 表达式

```rust
let max = if a > b { a } else { b };
```

- 有 else → 表达式，类型是两个分支的统一类型
- 无 else → 语句，类型为 `()`，分支值为 void
- 分支类型必须匹配（无 else 时允许 void）

```rust
// 多分支
let grade = if score >= 90 {
    4
} else if score >= 80 {
    3
} else if score >= 70 {
    2
} else {
    0
};
```

### 6.3 函数调用

```rust
let result = function_name(arg1, arg2);
let sum = add(10, 20);
```

- 参数从左到右求值
- 实参类型必须匹配形参类型（必要时隐式 widening）
- struct 参数按值传递（拷贝整个 struct，见第 10.4 节）

### 6.4 数组下标

```rust
let arr: [i32; 5] = [1, 2, 3, 4, 5];
let first = arr[0];        // 读取
arr[2] = 100;               // 写入
```

下标必须是 `usize` 兼容的整数类型。运行时不做边界检查（QBE `load`/`store` 越界行为未定义，由调用方负责）。

---

## 7. 控制流

### 7.1 while 循环

```rust
let mut i = 0;
while i < 10 {
    i = i + 1;
}
```

类型为 `()`。循环体不能作为表达式返回值。

### 7.2 for 循环

```rust
for i in 0..10 {
    // i 从 0 到 9
}
```

- 循环变量 `i` 是可变栈分配
- 类型从 `start` / `end` 表达式推断（支持 `i8`-`i64`, `u8`-`u64`）
- 范围是 `start..end`（**半开区间**，不含 end）
- 步长为 1
- 类型为 `()`

### 7.3 break / continue

```rust
let mut sum = 0;
for i in 0..100 {
    if i > 10 { break; }       // 跳出整个循环
    if i % 2 == 0 { continue; } // 跳过本轮剩余，进入下一轮
    sum += i;
}
```

- `break` 跳出最近 `while` / `for`
- `continue` 跳到本轮开始（while: 跳回条件检查；for: 跳到 i++）
- 只能在循环体内使用，sema 验证 `loop_depth > 0`

### 7.4 return

```rust
fn foo(n: i32) -> i32 {
    if n < 0 {
        return 0;    // 提前返回
    }
    n * 2           // 正常返回（不加 return）
}
```

- `return expr;` — 提前返回，类型检查确保 expr 匹配函数返回类型
- `return;` — 无值返回，仅用于 `()` 返回类型的函数
- 函数体已有显式 `return` 时，不再生成尾部 ret

---

## 8. 函数

### 8.1 定义

```rust
fn name(param1: Type1, param2: Type2) -> ReturnType {
    // 函数体
    // 最后一个表达式是返回值
}
```

### 8.2 参数

- 参数必须显式标注类型
- 参数在函数体内是不可变的 SSA 临时量
- 支持所有基本类型、指针、struct（按值，见 10.4）
- 不支持默认值 / 变参（`...`）

### 8.3 返回类型

- 显式标注: `fn f() -> i32 { 42 }`
- 隐式推断: `fn f() { }` → 返回 `()`
- 标注为 `()` 时，从函数体推断实际返回类型
- 返回类型检查: `return expr` 的类型必须与声明一致

### 8.4 递归

```rust
fn fib(n: i32) -> i32 {
    if n <= 1 {
        return n;
    }
    fib(n - 1) + fib(n - 2)
}
```

函数名在解析函数体之前注册，递归调用正常工作。

### 8.5 嵌套函数

**当前不支持**。所有函数必须在顶层声明。

---

## 9. 指针

### 9.1 取地址

```rust
let mut x = 42;
let p = &x;        // p: *i32
```

只能对可变变量 (`let mut`) 或 `let` 字段可变访问取地址。

### 9.2 解引用

```rust
let v = *p;        // 读取指针指向的值
```

### 9.3 通过指针赋值

```rust
*p = 100;          // 修改指针指向的值
```

### 9.4 链式访问

```rust
ptr->field         // 通过指针访问结构体字段
(*ptr).field       // 等价写法
```

### 9.5 指针算术

```rust
let arr: [i32; 5] = [10, 20, 30, 40, 50];
let p: *i32 = &arr[0];
let q = p + 1;     // q 指向 arr[1]
let r = *(p + 3);  // r = arr[3]
```

指针 `+ n` 等于字节偏移 `n * sizeof(T)`。仅在数组 / 缓冲区场景有意义；普通变量取地址后做指针算术 UB。

---

## 10. 结构体

### 10.1 定义

```rust
type Point = struct {
    x: i32,
    y: i32,
};
```

- 字段按声明顺序排列
- 对齐到每个字段的自然边界
- 名义类型（与第 2.3 节一致）

### 10.2 构造

```rust
let p = Point { x: 10, y: 20 };
```

所有字段必须提供，顺序任意。

### 10.3 字段访问

```rust
let px = p.x;         // 通过值访问
let px = ptr->x;      // 通过指针访问
```

### 10.4 按值传递 / 返回（v0.4 ABI）

JHYY 的 struct ABI 是**调用方栈拷贝 + sret 返回**：

- **按值传参**：调用方分配临时栈槽 → 逐字段复制 → 把栈槽地址 (`*Struct`) 作为实参传递
- **按值返回**：调用方分配返回槽 → 隐式作为第一个参数 (`*Struct`) 传入 → 被调用方写入后 bare `ret`

具体见 [`jhyy-abi-v1.0.0.md`](jhyy-abi-v1.0.0.md) 第 3 节。

```rust
type Point = struct { x: i32, y: i32 };

fn shift(p: Point, dx: i32, dy: i32) -> Point {
    Point { x: p.x + dx, y: p.y + dy }
}

fn main_jhyy() -> i32 {
    let p = Point { x: 1, y: 2 };
    let q = shift(p, 10, 20);   // p 被拷贝到临时槽, q 通过 sret 写入
    q.x + q.y                   // 31
}
```

### 10.5 嵌套结构体

```rust
type Rect = struct {
    top_left: Point,
    bottom_right: Point,
};

let r = Rect {
    top_left: Point { x: 0, y: 0 },
    bottom_right: Point { x: 100, y: 100 },
};
```

按值传递时，`cg_copy_struct` 递归处理嵌套字段。

---

## 11. 枚举与模式匹配

### 11.1 枚举定义

```rust
type Option = enum {
    Some(i32),
    None,
};

type Result = enum {
    Ok(i64),
    Err(i32),
};

type Tree = enum {
    Leaf(i32),
    Branch(*Tree, *Tree),
};
```

- tag 为 `i32`，从 0 开始自动分配
- 变体可以有 payload (带类型参数) 或 nullary (无参数)
- payload 偏移对齐到最大 payload 对齐边界
- 名义类型

### 11.2 构造

```rust
let some_val = Option::Some(42);
let none_val = Option::None;
let leaf = Tree::Leaf(100);
```

### 11.3 match 表达式

```rust
let desc = match x {
    0 => "zero",
    1 | 2 => "one or two",
    3..10 => "three to nine",
    _ => "many",
};
```

支持的模式：

| 模式 | 语法 | 示例 |
|------|------|------|
| 字面量 | `0`, `true`, `'a'`, `"x"` | `0 => ...` |
| 通配符 | `_` | `_ => ...` |
| 多值 | `pat1 \| pat2` | `1 \| 2 => ...` |
| 范围 | `start..end` | `3..10 => ...`（半开区间） |
| 枚举绑定 | `Enum::Variant(x)` | `Option::Some(v) => v` |

- 所有 arm 的返回值类型必须一致
- match 是表达式，返回匹配 arm 的值

---

## 12. 模块与导入

### 12.1 单文件 import

```rust
// main.jhyy
import mylib;       // 导入同目录下的 mylib.jhyy

fn main_jhyy() -> i32 {
    helper()        // 来自 mylib.jhyy
}
```

```rust
// mylib.jhyy
fn helper() -> i32 {
    42
}
```

### 12.2 多文件 CLI（v0.4 起）

```bash
jhyy compile main.jhyy lib_a.jhyy lib_b.jhyy -o output
```

### 12.3 传递性 import（v0.4 起）

`import` 是**递归的**。如果 `main.jhyy` import `a.jhyy`，`a.jhyy` 又 import `b.jhyy`，则 `main` 可以直接使用 `a` 和 `b` 的声明。

**循环检测**：若 `a.jhyy → b.jhyy → a.jhyy`，编译器报错 `circular import: a.jhyy → b.jhyy → a.jhyy` 而不是崩溃。

### 12.4 模块命名空间（v0.6 起）

不同模块可定义同名函数，使用 `mod::fn()` 限定调用。编译器自动 mangle 为 `$mod__name`，避免符号冲突。

```rust
// lib_a.jhyy
fn process() -> i32 { 100 }

// lib_b.jhyy
fn process() -> i32 { 50 }

// main.jhyy
import lib_a;
import lib_b;

fn main_jhyy() -> i32 {
    let a = lib_a::process();   // 100
    let b = lib_b::process();   // 50
    a + b                       // 150
}
```

**实现**：
- `Sym.module` 字段记录所属模块（NULL = main）
- 跨模块函数 emit 时 mangle 为 `$mod__name`
- 同名函数在不同模块中互不干扰

### 12.5 限制

- **无嵌套 import 路径**：`import utils::io` 不支持；目前是 `import utils; utils::io_func()`

---

## 13. FFI 与外部函数

### 13.1 extern fn 声明

```rust
extern fn puts(s: *u8) -> i32;
extern fn printf(fmt: *u8, val: i32) -> i32;
extern fn scanf(fmt: *u8, ptr: *i32) -> i32;
extern fn fopen(path: *u8, mode: *u8) -> *u8;
extern fn fclose(file: *u8) -> i32;
```

- 不生成函数体
- 链接时由 GCC 解析 C 符号
- 参数类型限于基本类型和 `*T`
- **多参数**：v0.4 起支持 ≥3 参数（之前 codegen 限制 2 参数）
- **返回值**：标量或 `*T`；struct 跨 FFI 见附录 B

### 13.2 字符串输出

```rust
extern fn puts(s: *u8) -> i32;
extern fn printf(fmt: *u8, ...) -> i32;

fn main_jhyy() -> i32 {
    puts("Hello, world!");
    printf("数字: %d\n", 42);
    0
}
```

注：变参 `printf(...)` 在 JHYY 侧需要手动展开（见附录 B）。

### 13.3 控制台输入

```rust
extern fn scanf(fmt: *u8, ptr: *i32) -> i32;

fn main_jhyy() -> i32 {
    let mut x = 0;
    scanf("%d", &x);
    0
}
```

### 13.4 文件 I/O

```rust
extern fn fopen(path: *u8, mode: *u8) -> *u8;
extern fn fclose(file: *u8) -> i32;

fn main_jhyy() -> i32 {
    let f = fopen("test.txt", "w");
    if f == (0 as *u8) { return 1; }
    fclose(f);
    0
}
```

### 13.5 控制台 UTF-8

Runtime 在启动时自动调用 `SetConsoleOutputCP(65001)`，中文等 UTF-8 字符可直接输出和输入。

---

## 14. 编译器使用

### 14.1 命令行

```bash
jhyy compile <file.jhyy> [-o output]       # 编译为 .exe
jhyy compile a.jhyy b.jhyy -o output       # 多文件编译（v0.4）
jhyy build   <file.jhyy> [-o output]       # 仅生成 QBE IL (.il)
jhyy run     <file.jhyy>                   # 编译并运行（Windows path 修复见下）
jhyy check   <file.jhyy>                   # 仅语法/语义检查，不生成二进制（v0.5 MCP 用）
jhyy                                      # 显示帮助
```

### 14.2 退出码

JHYY 程序的退出码是 `main_jhyy()` 的返回值。Windows 用 `echo %ERRORLEVEL%` 查看，MSYS bash 用 `./a.exe; echo $?`。

### 14.3 构建编译器

```bash
/c/msys64/ucrt64/bin/gcc.exe -std=c11 -Wall -Wextra \
    compiler/src/*.c \
    -o compiler/build/bin/jhyy.exe \
    -I compiler/src
```

`-Wall -Wextra` 零警告（v0.5 修复）。

### 14.4 编译器流水线

```
.jhyy → Lexer → Token流 → Parser → AST → Sema → 标注AST → Codegen → QBE IL → QBE → .s → GCC → .exe
```

### 14.5 已知 `run` 子命令问题

Windows 下 `jhyy run` 在某些路径场景有 bug（P1，未修）。临时替代：

```bash
jhyy compile foo.jhyy -o foo
./foo.exe
```

---

## 15. 完整示例

### 15.1 阶乘（迭代）

```rust
fn factorial(n: i32) -> i32 {
    let mut result = 1;
    let mut i = 1;
    while i <= n {
        result = result * i;
        i = i + 1;
    }
    result
}
```

### 15.2 斐波那契（递归）

```rust
fn fib(n: i32) -> i32 {
    if n <= 1 { return n; }
    fib(n - 1) + fib(n - 2)
}
```

### 15.3 结构体 + 指针 + 按值传递

```rust
type Point = struct {
    x: i32,
    y: i32,
};

fn midpoint(a: Point, b: Point) -> Point {
    Point {
        x: (a.x + b.x) / 2,
        y: (a.y + b.y) / 2,
    }
}

fn main_jhyy() -> i32 {
    let p = Point { x: 0, y: 0 };
    let q = Point { x: 10, y: 20 };
    let m = midpoint(p, q);
    m.x + m.y       // 15
}
```

### 15.4 枚举 + match

```rust
type Option = enum { Some(i32), None };

fn unwrap_or(opt: Option, default: i32) -> i32 {
    match opt {
        Option::Some(val) => val,
        Option::None => default,
    }
}
```

### 15.5 break/continue + for

```rust
fn sum_odd_to_ten() -> i32 {
    let mut sum = 0;
    for i in 0..100 {
        if i > 10 { break; }
        if i % 2 == 0 { continue; }
        sum += i;
    }
    sum
}
```

### 15.6 类型转换

```rust
fn main_jhyy() -> i32 {
    let f: f64 = 3.14;
    let i: i32 = f as i32;        // 3 (截断)
    let big: i64 = i as i64;      // 3 (扩宽)
    let back: f32 = big as f32;   // 3.0 (i64 → f32)
    i
}
```

### 15.7 控制台输出

```rust
extern fn printf(fmt: *u8, val: i32) -> i32;

fn main_jhyy() -> i32 {
    printf("fib(10) = %d\n", fib(10));
    0
}
```

### 15.8 多文件模块

**main.jhyy**：
```rust
import math;

fn main_jhyy() -> i32 {
    math::factorial(5)     // 120
}
```

**math.jhyy**：
```rust
pub fn factorial(n: i32) -> i32 {
    if n <= 1 { return 1; }
    n * factorial(n - 1)
}
```

注：`pub` 关键字**当前不强制**，所有顶层声明默认公开。

### 15.9 递归枚举（Tree）

```rust
type Tree = enum {
    Leaf(i32),
    Branch(*Tree, *Tree),
};

fn sum_tree(t: *Tree) -> i32 {
    match *t {
        Tree::Leaf(v) => v,
        Tree::Branch(l, r) => sum_tree(l) + sum_tree(r),
    }
}
```

---

## 附录 A：与 v0.2.1 的差异

### v0.3.0 新增
- **定长数组 `[T; N]`**：类型 + 字面量 + 下标读写 + 赋值
- **Pratt 解析器优先级修复**：`-` / `*` / `&` 双角色 token 使用正确优先级
- **嵌套 if phi 前驱块 trampoline 修复**

### v0.4.0 新增
- **struct 按值传递**：调用方分配栈拷贝，`cg_copy_struct` 逐字段复制
- **struct 按值返回（sret）**：调用方分配返回槽 + 隐式第一参数
- **struct 嵌套**：按值传递递归处理嵌套字段
- **多文件 CLI**：`jhyy compile a.jhyy b.jhyy -o output`
- **传递性 import**：递归解析 + 循环检测
- **FFI 多参数**：≥3 参数支持

### v0.5.0 新增 / 修复
- **浮点算术 codegen**：`+ - * /` 使用 `adds`/`subs`/`muls`/`divs` (f32) 和 `addd`/`subd`/`muld`/`divd` (f64)
- **类型转换 `as`**：整数扩宽/截断、浮点↔整数、浮点互转
- **if/else void 分支**：无 else 时不发 phi
- **嵌套 if/else if phi trampoline 修复**
- **if-as-block-return-value 修复**：`cg_block` 对 NODE_IF/NODE_MATCH/NODE_BLOCK 也调 cg_expr
- **break / continue**：while/for 循环支持
- **for 循环单独 `incr_b` 块**：`continue` 正确跳到 i++
- **i32 整数溢出**：二补码环绕（明确语义）
- **零警告构建**：`main.c` cmd buffer 4096
- **Claude Code MCP 服务**：7 工具 + 4 资源
- **ABI v1.0.0 锁定**

### 状态变化（从"限制"移到"已实现"）
- 浮点字面量 codegen（v0.5 修复）
- 定长数组 `[T; N]`（v0.3 实现）
- 多文件模块（v0.4 实现）
- 传递性 import（v0.4 实现）
- struct 按值传递 / 返回（v0.4 实现）
- FFI 多参数（v0.4 实现）
- break / continue（v0.5 实现）

---

## 附录 B：已知限制

下列特性在 sema 中已部分接受，但 codegen 缺失或不可用。**Phase 1 不阻塞**，但影响 v0.6+ 候选。

| # | 严重度 | 描述 | 影响范围 |
|---|--------|------|---------|
| ~~**P2**~~ | ~~类型已定义，codegen 缺失~~ | ~~切片 `[*]T` — 编译器接受 `[*]i32` 但 codegen 无实现~~ | **v0.6.0 sprint 6A 已实现**：按 struct pass-by-value sret 处理 |
| **P2** | 不完整 | 浮点比较 (`==`/`<`/...) 部分场景未完全类型化（用 QBE 默认指令） | 大多数场景工作，极端 NaN/Inf 行为未规约（v0.5 sprint 5A 修了大部分） |
| **P3** | 缺失 | 浮点 fmod (`%`) — 整数 `%` 工作，浮点 `%` 拒绝 | 自举可绕过（用整数 mod） |
| **P3** | 缺失 | struct / enum 跨 FFI 边界（Windows x64 ABI 不兼容） | 需 C ABI 兼容 struct 传递（v0.6 候选） |
| **P3** | 缺失 | 变参函数 (`printf` 的 `...`) — JHYY 侧需手动展开为多个 extern | 自举可手写 wrapper |
| **P3** | 缺失 | 函数回调（把 JHYY 函数指针传给 C 调用） | Phase 2+ 考虑 |
| ~~**P3**~~ | ~~缺失~~ | ~~模块命名空间（v0.4 多文件后符号冲突）~~ | **v0.6.0 sprint 6B 已实现**：`Sym.module` 字段 + `$mod__name` mangle + `mod::fn()` 限定调用 |
| **P3** | 缺失 | 嵌套 import 路径 (`utils::io`) — 当前仅 `import utils; utils::io_func()` | v0.6+ 候选（v0.6 sprint 6B 未实现） |
| ~~**P2**~~ | ~~pre-existing~~ | ~~`import_test.jhyy` 找不到 `mylib.jhyy`（CLI 多文件参数路径 bug）~~ | **v0.6.0 sprint 6D.1 已修复**：dir 提取 fallback 到 `"."` |

---

## 附录 C：自举兼容性

**自举 (self-hosting) = 用 JHYY 写 JHYY 编译器**。Phase 2 启动门槛：本 spec v1.0.0 覆盖的子集必须能表达 JHYY 编译器源（C 版本）的全部语义。

### C 编译器架构 → JHYY 子集需求映射

| C 编译器模块 | 用到 C 特性 | JHYY v1.0.0 子集能力 | 状态 |
|------------|------------|---------------------|------|
| `arena.c` | bump allocator, ptr 算术 | `*u8` + 指针算术 | ✓ |
| `lexer.c` | 字符流扫描，状态机 | 字符串字面量 + `match` + char literal | ✓ |
| `parser.c` | 递归下降 + Pratt 表达式 | 递归函数 + 优先级编码在 token 序列里 | ✓ |
| `ast.c/h` | tagged union, variant data | `enum` + `*Node` | ✓ |
| `types.c` | 类型系统，递归 struct | `struct` + `enum` + `*Type` | ✓ |
| `symtab.c` | FNV-1a hash + 链地址 | `[u8; N]` 数组 + 链表 + 位运算 | ✓ |
| `sema.c` | 多次遍历 AST | 递归函数 + `*Node` | ✓ |
| `codegen.c` | SSA + phi + 控制流 | if-else + while + for + break/continue + 块表达式 | ✓ |
| `ir.c/h` | QBE IL 文本拼接 | 字符串拼接（`extern fn sprintf`）+ 数组 | ✓ |
| `main.c` | CLI 参数，文件 I/O | `extern fn getopt` + `fopen/fread/fclose` | ✓ |

### 不需要但有帮助的特性

| 特性 | 是否有助于自举 | 备注 |
|------|--------------|------|
| 切片 `[*]T` | 可选 | `(ptr, len)` pair 可替代；用于 token range 会更优雅 |
| 泛型 | 否 | C 编译器没用泛型，写 JHYY 版本时也不需要 |
| 闭包 | 否 | C 编译器是显式函数指针 + struct env |
| 异步 | 否 | C 编译器是同步的 |
| 异常 | 否 | C 编译器是 longjmp / setjmp 或错误码返回 |

### 推荐的 v0.6 优先项（为自举铺路）

1. ~~**切片 codegen** (P2)~~：**v0.6.0 sprint 6A 已实现** ✓
2. ~~**模块命名空间** (P3)~~：**v0.6.0 sprint 6B 已实现** ✓
3. **C ABI 兼容 struct 传递** (P3)：替换当前 stack-copy ABI，让自举的 JHYY 编译器能直接调用 C 标准库（**v0.6 sprint 6D 部分修 pointer-to-struct 语义，全 ABI 兼容仍待 phase-2**）
4. **`as` 支持指针 ↔ usize 互转** (P2)：方便做指针 ↔ 整数互转做 hash（**v0.6.0 sprint 6C 已实现** ✓）

### Phase 2 启动条件

✅ 本 spec 覆盖的全部特性在 v0.5.1 编译器中可用
✅ 已知限制（P2/P3）有 fallback 路径
⏳ 至少 5 个 sprint 验证（实际编译器源用 JHYY 写一遍，过回归）
⏳ Stage 0/1/2 自举验证（C 编译器编译 JHYY 编译器源码）

---

**规范版本**: v1.0.0（frozen）
**变更**: 此版本后任何破坏性语法/语义改动必须先走 RFC 流程
