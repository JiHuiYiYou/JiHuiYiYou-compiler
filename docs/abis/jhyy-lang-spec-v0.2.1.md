# JHYY 语言规范 v0.2.1

**日期**: 2026-06-07
**状态**: 当前实现
**覆盖**: 编译器 v0.2.1 全部可用语法

---

## 目录

1. [程序结构](#1-程序结构)
2. [类型系统](#2-类型系统)
3. [变量与绑定](#3-变量与绑定)
4. [字面量](#4-字面量)
5. [运算符](#5-运算符)
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

后缀 `.jhyy`，UTF-8 编码。

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

---

## 2. 类型系统

### 2.1 基本类型

| 类型 | 大小 | 对齐 | 说明 |
|------|------|------|------|
| `i8` | 1 | 1 | 有符号 8 位整数 |
| `i16` | 2 | 2 | 有符号 16 位整数 |
| `i32` | 4 | 4 | 有符号 32 位整数 |
| `i64` | 8 | 8 | 有符号 64 位整数 |
| `u8` | 1 | 1 | 无符号 8 位整数 |
| `u16` | 2 | 2 | 无符号 16 位整数 |
| `u32` | 4 | 4 | 无符号 32 位整数 |
| `u64` | 8 | 8 | 无符号 64 位整数 |
| `f32` | 4 | 4 | 32 位浮点 (IEEE 754) |
| `f64` | 8 | 8 | 64 位浮点 (IEEE 754) |
| `bool` | 1 | 1 | 布尔值 (`true` / `false`) |
| `()` | 0 | 1 | unit 类型 (类似 void) |

### 2.2 复合类型

| 类型 | 大小 | 说明 |
|------|------|------|
| `*T` | 8 | 指针，64 位地址 |
| `struct { ... }` | 字段之和 (对齐) | 结构体 |
| `enum { ... }` | tag(4) + max_payload (对齐) | 带标签联合体 |

### 2.3 类型别名

```rust
type Age = i32;
type Point = struct { x: i32, y: i32 };
```

### 2.4 类型推断

- 参数**必须**显式标注类型
- 局部变量从初始化表达式自动推断
- 函数返回类型可从函数体推断（标注为 `()` 时）

### 2.5 整数字面量后缀

```
42i8, 42i16, 42i32, 42i64
42u8, 42u16, 42u32, 42u64
```

无后缀整数字面量默认为 `i32`。

---

## 3. 变量与绑定

### 3.1 不可变绑定 (let)

```rust
let x = 42;
let y = x + 1;
let z: i64 = 100;  // 带显式类型标注
```

- 不分配栈空间，直接作为 SSA 临时量
- 不可重新赋值
- 不可取地址

### 3.2 可变绑定 (let mut)

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

只适用于可变变量。

---

## 4. 字面量

### 4.1 整数字面量

```rust
let dec = 42;           // 十进制
let hex = 0xFF;         // 十六进制
let oct = 0o77;         // 八进制
let bin = 0b1010;       // 二进制
let with_suffix = 100i64;  // 带类型后缀
```

支持 `_` 分隔: `1_000_000`。

### 4.2 浮点字面量

```rust
let pi = 3.14;
let half = 0.5;
let exp = 1.0e10;
```

默认为 `f64`。浮点字面量 codegen 当前有限制（硬编码 0.0），端到端测试未完成。

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
```

类型为 `i32`。支持转义: `\n`, `\t`, `\r`, `\\`, `\'`, `\0`, `\xHH`。

### 4.5 字符串字面量

```rust
let greeting = "你好，世界！";
let with_escape = "第一行\n第二行";
```

类型为 `*u8`（指向 null 终止 UTF-8 字节串的指针）。

支持转义序列:
| 转义 | 含义 |
|------|------|
| `\n` | 换行 (0x0A) |
| `\t` | 制表 (0x09) |
| `\r` | 回车 (0x0D) |
| `\0` | 空字节 (0x00) |
| `\\` | 反斜杠 |
| `\"` | 双引号 |
| `\xHH` | 十六进制字节 |

---

## 5. 运算符

优先级从低到高:

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
| 12 (最高) | `.` `->` `()` `[]` |

### 5.1 算术运算

```rust
a + b    // 加法
a - b    // 减法
a * b    // 乘法
a / b    // 除法
a % b    // 取模
-a       // 取负
```

### 5.2 比较运算

```rust
a == b   // 等于
a != b   // 不等于
a < b    // 小于
a > b    // 大于
a <= b   // 小于等于
a >= b   // 大于等于
```

返回 `bool`。比较指令根据操作数类型自动选择:
- 有符号/无符号
- 32 位 (`w`) / 64 位 (`l`)

### 5.3 逻辑运算 (短路求值)

```rust
a && b   // 逻辑与: a 为 false 时不求值 b
a || b   // 逻辑或: a 为 true 时不求值 b
!a       // 逻辑非
```

**注意**: `&&` 和 `||` 是短路求值。右侧操作数只在必要时才求值。

### 5.4 位运算

```rust
a & b    // 按位与
a | b    // 按位或
a ^ b    // 按位异或
a << b   // 左移
a >> b   // 右移
~a       // 按位取反
```

移位宽度根据操作数类型自动选择 (`w` 或 `l`)。

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
- 无 else → 语句，类型为 `()`，分支值为 `void`
- 分支类型必须匹配

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

参数从左到右求值。

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
- 类型从 start/end 表达式推断 (支持 `i8`-`i64`, `u8`-`u64`)
- 步长为 1
- 类型为 `()`

### 7.3 return

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
- 支持所有整数类型、浮点、bool、指针

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

---

## 9. 指针

### 9.1 取地址

```rust
let mut x = 42;
let p = &x;        // p: *i32
```

只能对可变变量 (`let mut`) 取地址。

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
- 名义类型: `type A = struct { x: i32 }` 和 `type B = struct { x: i32 }` 是不同类型

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
```

- tag 为 `i32`，从 0 开始自动分配
- 变体可以有 payload (带类型参数) 或 nullary (无参数)
- payload 偏移对齐到最大 payload 对齐边界
- 名义类型

### 11.2 构造

```rust
let some_val = Option::Some(42);
let none_val = Option::None;
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

支持的模式:
| 模式 | 语法 | 示例 |
|------|------|------|
| 字面量 | `0`, `true`, `'a'` | `0 => ...` |
| 通配符 | `_` | `_ => ...` |
| 多值 | `pat1 \| pat2` | `1 \| 2 => ...` |
| 范围 | `start..end` | `3..10 => ...` |

- 所有 arm 的返回值类型必须一致
- match 是表达式，返回匹配 arm 的值

---

## 12. 模块与导入

### 12.1 import 声明

```rust
import mylib;       // 导入同目录下的 mylib.jhyy
```

### 12.2 被导入模块

`mylib.jhyy`:
```rust
fn helper() -> i32 {
    42
}
```

### 12.3 使用

导入后，被导入模块中的所有顶层声明（函数、类型）在主模块中可用:

```rust
import mylib;

fn main_jhyy() -> i32 {
    let result = helper();   // 来自 mylib.jhyy
    result
}
```

- 仅处理一级导入（不传递）
- 通过名称去重

---

## 13. FFI 与外部函数

### 13.1 extern fn 声明

```rust
extern fn puts(s: *u8) -> i32;
extern fn printf(fmt: *u8, val: i32) -> i32;
```

- 不生成函数体
- 链接时由 GCC 解析 C 符号
- 参数类型限于标量类型

### 13.2 常用 FFI

```rust
// 字符串输出
extern fn puts(s: *u8) -> i32;

// 格式化输出（单参数）
extern fn printf(fmt: *u8, val: i32) -> i32;
```

### 13.3 控制台输入

通过 FFI 调用 C 的 `scanf`。需要用 `&mut x` 传递指针：

```rust
extern fn scanf(fmt: *u8, ptr: *i32) -> i32;
extern fn printf(fmt: *u8, val: i32) -> i32;

fn main_jhyy() -> i32 {
    let mut x = 0;
    scanf("%d", &x);          // 读取整数到 x
    printf("你输入的是: %d\n", x);
    0
}
```

| C 函数 | JHYY extern 声明 | 用途 |
|--------|-----------------|------|
| `scanf` | `extern fn scanf(fmt: *u8, ptr: *i32) -> i32;` | 读取整数 |
| `getchar` | `extern fn getchar() -> i32;` | 读取单个字符 |

### 13.4 控制台 UTF-8

Runtime 在启动时自动调用 `SetConsoleOutputCP(65001)`，中文等 UTF-8 字符可直接输出和输入。

---

## 14. 编译器使用

### 14.1 命令行

```bash
jhyy compile <file.jhyy> [-o output]   # 编译为 .exe
jhyy build   <file.jhyy> [-o output]   # 编译为 .il (仅 QBE IR)
jhyy run     <file.jhyy>               # 编译并运行
jhyy                                    # 显示帮助
```

### 14.2 退出码

JHYY 程序的退出码是 `main_jhyy()` 的返回值。可以在命令行中用 `echo %ERRORLEVEL%` (Windows) 或 `echo $?` (Linux) 查看。

### 14.3 构建编译器

```bash
gcc -std=c11 -Wall -Wextra compiler/src/*.c -o compiler/build/bin/jhyy.exe -I compiler/src
```

---

## 15. 完整示例

### 15.1 阶乘 (迭代)

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

### 15.2 斐波那契 (递归)

```rust
fn fib(n: i32) -> i32 {
    if n <= 1 {
        return n;
    }
    fib(n - 1) + fib(n - 2)
}
```

### 15.3 结构体 + 指针

```rust
type Point = struct {
    x: i32,
    y: i32,
};

fn add_points(a: *Point, b: *Point) -> Point {
    Point {
        x: a->x + b->x,
        y: a->y + b->y,
    }
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

### 15.5 控制台输出

```rust
extern fn printf(fmt: *u8, val: i32) -> i32;

fn main_jhyy() -> i32 {
    let fib10 = fib(10);
    printf("fib(10) = %d\n", fib10);
    0
}
```

### 15.6 模块化

**main.jhyy**:
```rust
import math;

fn main_jhyy() -> i32 {
    math::factorial(5)
}
```

**math.jhyy**:
```rust
fn factorial(n: i32) -> i32 {
    if n <= 1 { return 1; }
    n * factorial(n - 1)
}
```

### 15.7 交互式输入

```rust
extern fn printf(fmt: *u8, val: i32) -> i32;
extern fn scanf(fmt: *u8, ptr: *i32) -> i32;

fn main_jhyy() -> i32 {
    printf("请输入一个数字: ", 0);

    let mut x = 0;
    scanf("%d", &x);

    let squared = x * x;
    printf("它的平方是: %d\n", squared);

    0
}
```
```

---

## 附录 A: 与 v0.0.1 的差异

| v0.0.1 | v0.2.1 |
|--------|--------|
| struct/enum 语法骨架 | 完整的 struct 字段 + enum 变体 + match |
| `&&`/`||` 逐位运算 | 短路求值 |
| for 循环硬编码 i32 | 类型感知 (i8-i64, u8-u64) |
| return 不检查类型 | return 类型检查 |
| 字符串类型 `[*]u8` | 字符串类型 `*u8` |
| 无转义序列 | 完整转义 `\n \t \r \0 \\ \" \xHH` |
| 无控制台输出 | puts + printf + UTF-8 |
| 无 import 系统 | import 模块导入 |
| `jhyy run` 路径问题 | Windows 路径修复 |
| symtab 不稳定 | 开放寻址 + FNV-1a 64-bit |

## 附录 B: 已知限制

| 限制 | 说明 |
|------|------|
| 切片 `[*]T` | 类型已定义，codegen 未实现 |
| 定长数组 `[T; N]` | 类型已定义，codegen 未实现 |
| 浮点字面量 | codegen 硬编码 0.0，端到端测试未完成 |
| 嵌套 import | 仅一级导入 |
| 结构体按值传递 | 不支持 |
| 变参 FFI | 不支持 |
