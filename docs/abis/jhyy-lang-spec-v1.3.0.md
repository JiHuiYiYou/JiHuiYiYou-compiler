# JHYY 语言规范 v1.3.0

**日期**: 2026-08-13
**状态**: 锁定（v1.x 语法糖 Phase 4 收尾；v1.2.0 = v1.1.0 + v1.3.1-v1.3.7 ship 增量）
**覆盖**: 编译器 v1.3.7 全部可用语法
**不覆盖**: 已声明但 codegen 缺失的特性（见附录 B）

v1.2.0 增量（基于 v1.1.0）:
- §4.4 新增 `null` 关键字 (v1.3.1)
- §7.5 新增 `else if` 语法糖描述 (v1.3.2 计划 — 实际未 ship,parser 已支持嵌套 `if/else` 等价;本章保留作为未来正式语义)
- §8.5 新增 `#[inline]` attribute (v1.3.5)
- §9.4 新增 `for x in slice` 语法糖 (v1.3.4)
- §11.4 新增 Pattern binding `Some(v) => v` (v1.3.7)
- §11.5 新增 OR pattern `Some(x) | Some(x)` (v1.3.7)
- §13.1 新增 `sizeof(TypeName)` 编译期常量 (v1.3.3)
- §17.5 新增 `defer` 语句 (v1.3.6)

v1.1.0 增量（基于 v1.0.0）：
- §11.3 新增 enum match 穷尽性检查 + 短名 variant pattern
- §13 新增顶层 const 数组声明

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
13. [顶层 const 数组（v0.7+）](#13-顶层-const-数组v07)
14. [FFI 与外部函数](#14-ffi-与外部函数)
15. [编译器使用](#15-编译器使用)
16. [完整示例](#16-完整示例)
17. [附录 A：与 v0.2.1 的差异](#附录-av021-的差异)
18. [附录 B：已知限制](#附录-b已知限制)
19. [附录 C：自举兼容性](#附录-c自举兼容性)

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
let latin = 'é';   // 2-byte BMP, U+00E9
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

**限制 (v1.7.0 Stage 3 ship):** 仅 ASCII + 2-byte BMP (U+0000-U+007F + U+0080-U+07FF) codepoint ship。
3-byte (U+0800-U+FFFF, e.g. `'你'` = U+4F60) / 4-byte (U+10000+, e.g. `'🎉'` = U+1F389) UTF-8 codepoint 显式 lex reject (per `docs/logs/v1/changelog-v1.7.0.md` Stage 3 段 + `workarounds.md` W-056 RESOLVED 2026-08-27 + W-057 🟡 DEFERRED v2.x 真修)。v2.x 自研 backend codepoint folding 后开放 3/4-byte codepoint ship。

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
| 短名枚举绑定（v0.7+） | `Variant(x)` | `Some(v) => v` |

- 所有 arm 的返回值类型必须一致
- match 是表达式，返回匹配 arm 的值

**穷尽性检查（v0.7+）**：当 match 表达式作用在 enum 类型上时，每个 variant 必须被某个 arm 显式覆盖（枚举绑定 / 多值中的枚举绑定 / 通配符 `_`）。未覆盖的 variant 会导致编译错误：

```rust
let opt: Option = Some(5);
match opt {
    Some(v) => v,    // 漏 None → 编译错误
};
// error: non-exhaustive match: missing variant 'None'
```

覆盖规则：
- `Enum::Variant(...)` 或 `Variant(...)`（v0.7+ 短名语法糖）→ 覆盖该 variant
- `_` 通配符 → 覆盖所有未覆盖的 variant（catch-all）
- `pat1 | pat2` → 两侧都覆盖才算覆盖
- 字面量 / 范围 pattern → 不算覆盖 enum variant（必须显式列）

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

## 13. 顶层 const 数组（v0.7+）

```rust
const ASCII_LOWER: [u8; 26] = [
    97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109,
    110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122
];

fn main_jhyy() -> i32 {
    ASCII_LOWER[25] as i32   // 122 = 'z'
}
```

**语法**：`const NAME: [T; N] = [elem, elem, ...];`

- 仅支持**顶层 const**（不允许函数体内 const）
- 元素类型 `T` 可以是：基本类型（`i8/i16/i32/i64/u8/.../f32/f64/bool`）、结构体、嵌套 const 数组（v0.7 不允许，见附录 B）
- 不允许：`const` 指针、`const` 切片、`enum` 数组（需要 RTTI）
- 长度 `N` 必须是正整数

**元素必须是 const 表达式**：

| 表达式 | 是否 const |
|--------|----------|
| 字面量（`42`、`3.14`、`true`、`'a'`、`"hello"`） | ✓ |
| struct-literal（前提是 field value 都是 const） | ✓ |
| 其他 const 引用（`OTHER_CONST[0]`、`OTHER_CONST.field`） | ✓ |
| 函数调用（`compute()`） | ✗ 编译错误 |
| `let` 变量引用 | ✗ 编译错误 |

**codegen**：emit 到 QBE `.data` 段（rodata），运行时零成本加载：

```qbe
data $ASCII_LOWER = { b 97, b 98, ..., b 122 }
```

访问通过 QBE DYNCONST：`%t =l copy $NAME` 直接拿到数组地址，不需要 `addr` 指令。

**结构体数组**：字段平铺：

```rust
type RGB = struct { r: i32, g: i32, b: i32 }
const PALETTE: [RGB; 3] = [
    RGB { r: 1, g: 2, b: 3 },
    RGB { r: 4, g: 5, b: 6 },
    RGB { r: 7, g: 8, b: 9 }
];
```
```qbe
data $PALETTE = { w 1, w 2, w 3, w 4, w 5, w 6, w 7, w 8, w 9 }
```

---

## 14. FFI 与外部函数

### 14.1 extern fn 声明

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

### 14.2 字符串输出

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

### 14.3 控制台输入

```rust
extern fn scanf(fmt: *u8, ptr: *i32) -> i32;

fn main_jhyy() -> i32 {
    let mut x = 0;
    scanf("%d", &x);
    0
}
```

### 14.4 文件 I/O

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

### 14.5 控制台 UTF-8

Runtime 在启动时自动调用 `SetConsoleOutputCP(65001)`，中文等 UTF-8 字符可直接输出和输入。

---

## 15. 编译器使用

### 15.1 命令行

```bash
jhyy compile <file.jhyy> [-o output]       # 编译为 .exe
jhyy compile a.jhyy b.jhyy -o output       # 多文件编译（v0.4）
jhyy build   <file.jhyy> [-o output]       # 仅生成 QBE IL (.il)
jhyy run     <file.jhyy>                   # 编译并运行（Windows path 修复见下）
jhyy dump    <file.jhyy>                   # dump AST（debug 用）
jhyy                                      # 显示帮助
```

### 15.2 退出码

JHYY 程序的退出码是 `main_jhyy()` 的返回值。Windows 用 `echo %ERRORLEVEL%` 查看，MSYS bash 用 `./a.exe; echo $?`。

### 15.3 构建编译器

```bash
/c/msys64/ucrt64/bin/gcc.exe -std=c11 -Wall -Wextra \
    compiler/src/*.c \
    -o compiler/build/bin/jhyy.exe \
    -I compiler/src
```

`-Wall -Wextra` 零警告（v0.5 修复）。

### 15.4 编译器流水线

```
.jhyy → Lexer → Token流 → Parser → AST → Sema → 标注AST → Codegen → QBE IL → QBE → .s → GCC → .exe
```

### 15.5 已知 `run` 子命令问题

Windows 下 `jhyy run` 在某些路径场景有 bug — **v1.x 已修** (`main.c:591` `path_to_win(exe)` 已处理 MSYS ↔ Win32 路径转换)。如在更新版编译器中复发,以 `jhyy compile foo.jhyy -o foo && ./foo.exe` 作为 fallback。

---

## 16. 完整示例

### 16.1 阶乘（迭代）

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

### 16.2 斐波那契（递归）

```rust
fn fib(n: i32) -> i32 {
    if n <= 1 { return n; }
    fib(n - 1) + fib(n - 2)
}
```

### 16.3 结构体 + 指针 + 按值传递

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

### 16.4 枚举 + match

```rust
type Option = enum { Some(i32), None };

fn unwrap_or(opt: Option, default: i32) -> i32 {
    match opt {
        Option::Some(val) => val,
        Option::None => default,
    }
}
```

### 16.5 break/continue + for

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

### 16.6 类型转换

```rust
fn main_jhyy() -> i32 {
    let f: f64 = 3.14;
    let i: i32 = f as i32;        // 3 (截断)
    let big: i64 = i as i64;      // 3 (扩宽)
    let back: f32 = big as f32;   // 3.0 (i64 → f32)
    i
}
```

### 16.7 控制台输出

```rust
extern fn printf(fmt: *u8, val: i32) -> i32;

fn main_jhyy() -> i32 {
    printf("fib(10) = %d\n", fib(10));
    0
}
```

### 16.8 多文件模块

**main.jhyy**：
```rust
import math;

fn main_jhyy() -> i32 {
    math::factorial(5)     // 120
}
```

**math.jhyy**：
```rust
fn factorial(n: i32) -> i32 {
    if n <= 1 { return 1; }
    n * factorial(n - 1)
}
```

注：v1.x lexer 不识别 `pub` 关键字(顶层声明默认公开,无需 `pub` 标注)。复制本示例请保留 `fn factorial` 形式。

### 16.9 递归枚举（Tree）

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

## 17. OS 启动前置语言层准备 (v2.2.0 🔒 语法预留)

> **状态**:🔒 v2.2.0 锁定 v3.0 6 特性的**语法形式草案**。**v2.0 期间不实施** — 编译器当前拒绝所有 6 attribute 与内联 asm 字面量(sema 报错路径见 § 17.7)。实施时走 v3.0 sprint 3a-3f(per [`v2-v3-parallel-sprint-plan.md`](../../plans/roadmap/v2-v3-parallel-sprint-plan.md))。
>
> **§ 编号决策**:本 § 17-20 = v2.2.0 连续顺延 4 个新 sections(因 lang-spec doc 最高只到 § 16 + Appendix A-E)。同时避开 [`v3.x-language-expansion.md`](../../plans/roadmap/v3.x-language-expansion.md) § 19 / § 21 同号异义冲突(那里是 `unsafe cap { ... }` + `Cap::provenance()` 语法,v3.0 启动时整体重排)。

### 17.1 `inline asm` — 内联汇编(v3.0 sprint 3a)

```jhyy
asm {
    "mov %1, %0"
    : "=r"(result)             // outputs
    : "r"(input)                // inputs
    : "memory", "cc"            // clobbers
}
```

- 字符串字面量 + 冒号分隔 outputs / inputs / clobbers 4 段;约束符走 GCC extended asm 语法
- 仅在 `#[no_std]` + freestanding 模式下可启用(per § 17.4 + § 18)
- 类型推断:output 跟变量绑定类型一致,input 接受 `*T` / 整数 / 浮点

### 17.2 `#[naked]` — 无 prologue/epilogue 函数体(v3.0 sprint 3b)

```jhyy
#[naked]
fn efi_entry() -> () {
    // 编译器不插入任何 prologue/epilogue;函数体必须是 inline asm
    asm { "ret" }
}
```

- 编译器**不**插入 callee-saved 寄存器保存 / 栈帧分配 / `ret` 指令
- 函数体必须以 inline asm 结尾(否则 sema 拒绝);常用于中断处理 / entry stub
- ABI 仍按目标 target 走(per § 13)

### 17.3 `volatile *T` — volatile 指针(v3.0 sprint 3c)

```jhyy
let ptr: volatile *u8 = 0xFEE00000 as volatile *u8;
let val = *ptr;       // 读 — 不允许被优化掉
*ptr = 0x01;          // 写 — 不允许被合并 / 重排
```

- 解引用 `*` 强制产生 `load` / `store` 指令,不参与优化器 CSE / 死代码消除
- 仅对单次解引用有效;`*(ptr + 1)` 需重新标记 `volatile`

### 17.4 `#[no_std]` — 不依赖 jhyy runtime(v3.0 sprint 3d)

```jhyy
#[no_std]
fn kernel_entry() -> () {
    // 不能用 println! / malloc / vec! / 等依赖 jhyy runtime 的 std lib
    // extern fn 必须显式声明
    extern fn write_to_serial(c: *u8) -> i32;
}
```

- 编译器不链 `compiler/runtime/runtime.c`(per `Makefile` RUNTIME_OBJ)
- 配合 `target=amd64_win_freestanding` 使用(per § 13.3)
- 必须在文件 / module 级声明(不在函数级)

### 17.5 `#[link_section = "..."]` — 自定义链接段(v3.0 sprint 3e)

```jhyy
#[link_section = ".text.boot"]
fn _start() -> () {
    // 编译器 emit .text.boot 段(QBE `section` directive)
    efi_main(0 as *u8, 0 as *u8);
}
```

- 编译器在 emit QBE IL 时加 `section "name"` 指令
- 段名按 PE/COFF / ELF section 命名约定(`_start` 必须 `.text.boot`)

### 17.6 `fence()` — memory barrier(v3.0 sprint 3f)

```jhyy
fence();   // 全屏障,等价 GCC asm volatile("" ::: "memory")
```

- 编译器 emit `fence` QBE 指令(对应 QBE 0.2+ 支持)
- 不接受参数,全屏障语义(后续 v3.x 可能加 `fence(acquire)` / `fence(release)`)
- 用于 OS 端同步原语,freestanding / `#[no_std]` 模式下使用

### 17.7 v2.0 期间 sema 拒绝路径

编译器在 v2.0 期间对上述 6 个 attribute + `asm { ... }` 字面量 + `volatile` 类型修饰符**全部拒绝**:

- `asm { ... }` → sema error `"asm block not yet supported (v3.0 sprint 3a)"`
- `#[naked]` / `#[no_std]` / `#[link_section = "..."]` → sema error `"attribute X not yet supported (v3.0 sprint 3b-3e)"`
- `volatile *T` 类型 → sema error `"volatile qualifier not yet supported (v3.0 sprint 3c)"`
- `fence()` → sema error `"fence() not yet supported (v3.0 sprint 3f)"`

错误提示指向对应 v3.0 sprint,用户可参照本节语法草案准备代码。

---

## 18. freestanding 模式 (v2.2.0 🔒 约定)

> **状态**:🔒 v2.2.0 锁定 freestanding 模式约定。**v2.0 期间仅文档化,不引入新语法**;entry point 走用户 `extern fn` 模式(per § 18.1)+ 编译示例见 § 18.2。

### 18.1 entry 符号约定

freestanding 模式(仅 `amd64_win_freestanding` target 启用,per § 13.3)要求用户自行提供 entry point:

| 场景 | entry 符号 | 签名 |
|------|-----------|------|
| **UEFI** | `efi_main` | `fn efi_main(ImageHandle: *u8, SystemTable: *u8) -> Status` |
| **裸机** | `_start` | `fn _start() -> ()` |

- `efi_main`:跟 UEFI spec 第 2.1.2 节定义一致;`Status` 是 `usize` 别名,0 = EFI_SUCCESS
- `_start`:裸机 entry,无参数无返回值;退出走 `hlt` 或 `ret`(裸机场景下 `ret` 通常非法)
- 编译器**不**提供默认 entry(per § 13.3);未定义 entry 符号时链接期报错

### 18.2 freestanding 编译示例

```bash
# Step 1: 编 .obj
jhyy.exe compile hello_efi.jhyy --target=amd64_win_freestanding -o hello.obj

# Step 2: 链 .efi (v2.3.0 实际跑 OVMF 时验证;v2.2.0 仅编 .obj)
lld-link /SUBSYSTEM:EFI_APPLICATION /ENTRY:efi_main hello.obj /OUT:hello.efi
```

**约束**(per § 13.3):
- 不能引用 jhyy runtime helper(`memcpy` / `memset` / `malloc` 等)
- 不链 ucrt / vcruntime / libc / glibc / musl
- 外部 `extern fn` 必须显式声明并按 MS x64 ABI 调用

---

## 19. Debug ABI (v2.2.0 🔒 per D41)

> **状态**:🔒 v2.2.0 锁定 Debug ABI 跨项目契约。**OS 端镜像** 见 [`../../../jhyy_OS/docs/v0.0.4-debug-abi.md`](../../../jhyy_OS/docs/v0.0.4-debug-abi.md)(🔒 Locked 2026-08-12,Q-Compiler-007 闭环 / D41)。
>
> **doc version pinning**:本 § 19 锁定时引用 OS doc **commit/tag**;OS 端后续更新走 Q-Compiler-007 流程同步,v2.2.0 不引入新 cross-boundary 问题。

### 19.1 尺寸定案(per D41)

| 类型 | 尺寸 | 说明 |
|------|------|------|
| `DebugEvent`(定长 header + nested payload)| **56B** | OS 端 kernel introspection 输出 |
| `ErrChain`(含 `SourceLoc` 24B 内嵌)| **64B** | 错误链,NULL-ended |
| `ProvenanceInfo`(DAG parents/children K=8)| **136B** | `Cap<T>` runtime trace metadata |

**布局总原则**(per D41 R1/R2):jhyy **无 `packed` / `repr(...)`**;所有跨边界 struct 一律自然对齐;padding 显式写成 `_pad*` 字段。

### 19.2 jhyy 侧类型表达

jhyy 侧类型表达**严格遵循 § 20 wire-format 规则**(per D40):

| wire 字段 | jhyy 表达 | 说明 |
|----------|----------|------|
| `ProvenanceInfo.grant_chain` / `revoke_chain` | `*ProvenanceInfo`(裸指针)| NULL 结尾单向链 |
| `ErrChain.prev` | `*ErrChain`(裸指针)| NULL 结尾单向链 |
| `ErrChain.trace` / `ErrChain.context` | `[*]TraceEntry` / `[*]u8` 切片 | 显式 `*_len: usize` 字段 |
| `DebugEvent.payload` | `*u8` + `payload_len: usize` | 跨 FFI 用指针,长度由显式字段提供 |

### 19.3 jhyy 编译器不生成 DWARF debug info(per D41 R3)

- jhyy 当前 emit `dbgfile` + `dbgloc` 指令(QBE → .file N / .loc N in `.s`),**仅 line table**
- **不**生成 DWARF `.debug_info` / `.debug_abbrev` / `.debug_line` 完整 section
- debug 数据由 OS 端 runtime side table 承载(per `v0.0.1-capability.md § 5.2` "side table 可 strip")
- release build 可 strip runtime debug info,不污染 v1.0.0 locked baseline

### 19.4 FFI 边界提醒(per D41 R4)

§ 19 全部 struct 都是**内存布局契约**(指针传递),不得按值跨 FFI 边界;见 § 7.4(FFI 整体规则)。M3 集成 `SysError.chain` 时必须以指针传 `ErrChain`。

---

## 20. Wire Format ↔ jhyy-side 表达规则 (v2.2.0 🔒 per D40)

> **状态**:🔒 v2.2.0 锁定跨 FFI 边界时 wire-format C struct 字段到 jhyy 类型表达的系统规则(per D40,2026-08-12 锁,修订 D14 字段类型部分,D14 主体不变)。

### 20.1 两条核心映射

| wire 字段特征 | jhyy 表达 | 尺寸 | 说明 |
|--------------|----------|------|------|
| wire 有显式 `*_len: usize` 字段 | `[*]T` 切片 | 16B(ptr + len)| 长度由字段提供 |
| wire 是 NULL-terminated 单向链 | `*T` 裸指针 | 8B | NULL 表示 chain 末尾 |

### 20.2 wire `*_len` → `[*]T` 切片 示例

```c
// wire (C)
typedef struct {
    uint8_t*  data;
    uint64_t  data_len;   // 显式长度字段
} Buffer;
```

```jhyy
// jhyy 侧 (per § 20.1)
type Buffer = struct {
    data: [*]u8   // 切片 = ptr(8B) + len(8B)
}
```

- `data` 是 wire `uint8_t*` + `data_len` 合并表达,**jhyy 类型层不区分**(因为 wire 两字段是同一个语义)
- 跨 FFI 时 codegen 负责 wire ↔ jhyy 转换(走 `abi_amd64_win.*` 的结构体字段处理)

### 20.3 wire NULL-ended chain → `*T` 裸指针 示例

```c
// wire (C)
typedef struct ErrChain {
    struct ErrChain* prev;   // NULL = chain root
    SourceLoc        loc;
    uint32_t         code;
} ErrChain;
```

```jhyy
// jhyy 侧 (per § 20.1)
type ErrChain = struct {
    prev: *ErrChain    // NULL-ended 单向链
    loc: SourceLoc
    code: u32
}
```

- `*ErrChain` 裸指针 = wire `ErrChain*`(NULL = chain root)
- 跨 FFI 时 codegen 直接 emit 对应 QBE IL(指针字段即裸 `l` 类型)

### 20.4 跟 D14 (FFI 边界) 关系

- D14 主体规则不变;§ 20 是 D14 在 wire-format 字段类型层的具体扩展
- 任何与 D40 锁的偏差走 Q-Compiler-XXX 流程
- § 20 跟 § 13.4 (UEFI=MS x64) / § 19 (Debug ABI) / § 14.2 (Cap wire) 用例一致 — `Cap<T>` runtime `*T` 链 + `ProvenanceInfo.grant_chain` `*T` 链全部用 `*T` 裸指针

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
- **Claude Code MCP 服务**：7 工具 + 4 资源（v0.5 起；mcp-jhyy Sprint 1 2026-08-11 加 4 个生产级工具 → 11 工具，见 `mcp-jhyy/README.md`）
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

下列特性在 sema 中已部分接受，但 codegen 缺失或不可用。**v0.x 不阻塞**，但影响 v0.6+ 候选。

| # | 严重度 | 描述 | 影响范围 |
|---|--------|------|---------|
| ~~**P2**~~ | ~~类型已定义，codegen 缺失~~ | ~~切片 `[*]T` — 编译器接受 `[*]i32` 但 codegen 无实现~~ | **v0.6.0 sprint 6A 已实现**：按 struct pass-by-value sret 处理 |
| **P2** | 不完整 | 浮点比较 (`==`/`<`/...) 部分场景未完全类型化（用 QBE 默认指令） | 大多数场景工作，极端 NaN/Inf 行为未规约（v0.5 sprint 5A 修了大部分） |
| **P3** | 缺失 | 浮点 fmod (`%`) — 整数 `%` 工作，浮点 `%` 拒绝 | 自举可绕过（用整数 mod）。**v1.7.2 patch A1 fact-check**: vendor QBE (2026-08-15 build) 不支持 `remd`/`rems` 浮点 mod 指令, 推 v2.x 真修, 详见 `docs/internal/workarounds.md` W-058 🟡 DEFERRED v2.x |
| **P3** | 缺失 | struct / enum 跨 FFI 边界（Windows x64 ABI 不兼容） | 需 C ABI 兼容 struct 传递（v0.6 候选） |
| **P3** | 缺失 | 变参函数 (`printf` 的 `...`) — JHYY 侧需手动展开为多个 extern | 自举可手写 wrapper |
| **P3** | 缺失 | 函数回调（把 JHYY 函数指针传给 C 调用） | v1.x 考虑 |
| ~~**P3**~~ | ~~缺失~~ | ~~模块命名空间（v0.4 多文件后符号冲突）~~ | **v0.6.0 sprint 6B 已实现**：`Sym.module` 字段 + `$mod__name` mangle + `mod::fn()` 限定调用 |
| **P3** | 缺失 | 嵌套 import 路径 (`utils::io`) — 当前仅 `import utils; utils::io_func()` | v0.6+ 候选（v0.6 sprint 6B 未实现） |
| ~~**P2**~~ | ~~pre-existing~~ | ~~`import_test.jhyy` 找不到 `mylib.jhyy`（CLI 多文件参数路径 bug）~~ | **v0.6.0 sprint 6D.1 已修复**：dir 提取 fallback 到 `"."` |

---

## 附录 C：自举兼容性

**自举 (self-hosting) = 用 JHYY 写 JHYY 编译器**。v1.x 启动门槛：本 spec v1.1.0 覆盖的子集必须能表达 JHYY 编译器源（C 版本）的全部语义。**v1.0.0 已达成**（commit `eabee0d`, 2026-08-10）。

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
3. **C ABI 兼容 struct 传递** (P3)：替换当前 stack-copy ABI，让自举的 JHYY 编译器能直接调用 C 标准库（**v0.6 sprint 6D 部分修 pointer-to-struct 语义，全 ABI 兼容仍待 v1.x**）
4. **`as` 支持指针 ↔ usize 互转** (P2)：方便做指针 ↔ 整数互转做 hash（**v0.6.0 sprint 6C 已实现** ✓）

### v1.x 启动条件（v1.3.0 更新；v1.0.0 已 ✅ 达成, v1.3.x 全 ✅ 达成, v1.4-v1.7 全 ✅ 达成）

✅ 本 spec 覆盖的全部特性在 v0.7.0 编译器中可用
✅ 已知限制（P2/P3）有 fallback 路径
✅ enum match 穷尽性检查（v0.7 7A）——自举 codegen 不需要主动漏 match arm，但严格的 sema 防止 .il 输出错误
✅ 顶层 const 数组（v0.7 7B）——自举 codegen 需要 emit `data $NAME = { ... }` 字符串字面量表、关键字表等
✅ ~~Pattern binding codegen（`Some(v) => v` 提取 payload）~~ — **v1.3.7 已 ship** (commit `0f32977`,semantic 1.3.7 Pattern binding + OR pattern)
✅ 至少 5 个 sprint 验证（实际编译器源用 JHYY 写一遍，过回归）
✅ Stage 0/1/2 自举验证（C 编译器编译 JHYY 编译器源码）
✅ **v1.4 DWARF debug + gdb_pretty.py + jhyy.exe 物理 flip** (per `docs/logs/v1/changelog-v1.4.x.md`)
✅ **v1.5 installer Burn bundle + VSCode ext + RunOnce** (per `docs/logs/v1/changelog-v1.5.x.md`)
✅ **v1.6 W-053 char literal escape + W-054 sizeof data layout + 7A/7B 增量** (per `docs/logs/v1/changelog-v1.6.0.md`)
✅ **v1.7 W-055 pointer arith (Stage 2) + W-056 UTF-8 2-byte BMP + float suffix f32/f64 + W-042 + W-021/W-051 docs RESOLVED** (per `docs/logs/v1/changelog-v1.7.0.md` + `changelog-v1.7.1.md` + `changelog-v1.7.2.md`)
✅ **v1.7.3 v1.x FINAL ship** — 32 candidates 完整 ship, tag `v1.7.3` 标 v1.x final (per `docs/logs/v1/changelog-v1.7.0.md` v1.7.3 patch 段 + `changelog-v1.7.2.md` 已知 limitation)

### v1.3.x 启动条件（v1.3.0 更新；全 ✅ 达成）

✅ null literal (v1.3.1 commit `c2acbd1`)
✅ sizeof(TypeName) (v1.3.3 commit `bb15f98`)
✅ for x in slice (v1.3.4 commit `fb908bd`)
✅ #[inline] attribute (v1.3.5 commit `143ee0f`)
✅ defer statement (v1.3.6 commit `169759c`)
✅ Pattern binding + OR pattern (v1.3.7 commit `0f32977`)
✅ enum param ABI mismatch fix / W-016 (v1.3.7 fix commit `bbdebc2`)

---

## 附录 D：v1.3.x 增量章节

### D.1 `null` 关键字 (v1.3.1)

**语法**：`null` 作为关键字字面量,出现在 typed pointer 上下文时取值 `0 as *T`。

```rust
let p: *u8 = null;
if p == null { return 1; }
return null;  // fn() -> *u8
let q = null as *u8;
```

**类型推断规则**（4 sites）：
- `NODE_LET`: `let p: *u8 = null;` 从 decl_type 推断
- `NODE_BINARY`: `if p == null` 从另一 operand 推断 (必须 pointer)
- `NODE_RETURN`: `return null` 从 current_ret_type 推断 (若 pointer)
- `NODE_CAST`: `null as *u8` 从 cast target 推断

**限制**: untyped `let p = null;` 是 **hard sema error** (Rust/C++ 语义)。Sema 拒绝以避免歧义。

**AST**: dedicated `NODE_NULL` NodeKind (ast.h value 50) — 不是 `NODE_INT_LIT(0)` 复用路径,避免 v3.x pointer semantics 扩展时类型推断的歧义。

---

### D.2 `else if` 语法糖 (v1.3.2 — 跳过)

**状态**: v1.3.2 计划但**未 ship**。parser 已支持 `else { if cond { ... } }` 的嵌套写法,与 `else if` 语法糖语义等价。

**保留描述**(v1.3.2 plan)：
```rust
if a { ... } else if b { ... } else { ... }
// 等价于
if a { ... } else { if b { ... } else { ... } }
```

如果未来需要正式语义,需 parser 单行 token lookahead 重写。**v1.2.0 不强制**。

---

### D.3 `sizeof(TypeName)` 编译期常量 (v1.3.3)

**语法**：`sizeof(T)` 返回类型 `T` 的字节大小,作为 `i32` 字面量在编译期 const-fold。

```rust
let s = sizeof(i32);  // = 4
let n = sizeof(*u8);  // = 8 (pointer size on amd64)
let m = sizeof([i32; 10]);  // = 40
```

**实现**：sema `process_sizeof` 把 `sizeof(T)` 折叠为 `NODE_INT_LIT(<bytes>)`,跟 `1 + 2` 常量折叠机制一致。**不**支持运行时求值。

---

### D.4 `for x in slice` 语法糖 (v1.3.4)

**语法**：`for x in slice_expr { ... }` 遍历切片元素。

```rust
let s: [*]i32 = [1, 2, 3];
for x in s {
    // x: i32,依次取 s[0], s[1], s[2]
}
```

**Desugar**(sema 阶段)：等价于 index loop:
```rust
let mut i: i64 = 0;
while i < slice_len(s) {
    let x = slice_index(s, i);
    // body
    i = i + 1;
}
```

**限制**: 元素类型 `T` 必须是 `Copy`(sema 不强制,但 codegen 假设值类型)。

---

### D.5 `#[inline]` attribute (v1.3.5)

**语法**：在 `fn` 声明前加 `#[inline]`,提示编译器在 call site 展开函数体。

```rust
#[inline]
fn dbl(x: i32) -> i32 { return x * 2; }

fn main_jhyy() -> i32 {
    return dbl(21);  // call site 内联展开 = "return 21 * 2;"
}
```

**MVP 限制**(per changelog-v1.3.0.md § v1.3.5):
- 仅展开 body 是**单条 `return <expr>;`** 的 fn
- **struct 返回值** → fall back 到 `call $name`(sret ABI 不支持现场展开)
- **多语句 / if-else / 循环 body** → fall back 到 `call $name`
- **递归调用** → fall back 到 `call $name`(用 `current_inline_sym` Sym 指针守卫,避免无限展开)
- **未知 attribute** (e.g. `#[noreturn]`) → 解析并忽略,前向兼容

`#[inline]` 函数**仍**emit 为 QBE function(供非内联 call site / 外部调用 / 递归 fallback 使用)。

---

### D.6 `defer` 语句 (v1.3.6)

**语法**：`defer <expr>;` 把 expr 求值推迟到当前函数返回时按 LIFO 顺序执行(Go-style)。

```rust
fn main_jhyy() -> i32 {
    let f = fopen("data.txt");
    defer fclose(f);  // 函数返回前执行 fclose(f)

    // ... 函数体 ...
    return 0;  // 触发 fclose(f)
}
```

**LIFO 顺序**:多个 defer 按**反注册顺序**执行(最后注册的最先执行,跟栈行为一致)。

**Scope**:defer 在**当前 function body 退出时**触发(无论 `return` 早返还是 body 末尾 fall-through)。**不支持**:
- `defer { block; }`(v3.x 候选)
- 跨循环 / 内联 / 嵌套 block 触发(v3.x 候选)
- defer 内引用外层 mutable 变量(`defer x = x + 1` — defer fncall,不是 defer stmt)

**AST**: 复用 `NODE_CALL` / `NODE_QUALIFIED_CALL`,defer 标志在 `NodeFuncDecl.defers` 数组(codegen 在 `cg_return` 前 emit 全部 defer 调用)。

---

### D.7 Pattern binding `Some(v) => v` (v1.3.7)

**语法**: enum variant pattern 内可绑定 payload 字段名,body 内可直接引用 binding 名。

```rust
type Option = enum { Some(i32), None }

fn unwrap(o: Option) -> i32 {
    return match o {
        Some(v) => v,  // v: i32,从 Some 的 payload 提取
        None => 0,
    };
}
```

**限制**(per changelog-v1.3.0.md § v1.3.7):
- Pattern binding **只**在 enum variant payload 上下文 (`Some(v)` / `Pair(a, b)`)
- 多 binding 用逗号分隔: `Pair(a, b) => a + b`
- 嵌套 pattern `Some(Some(x))` 一层 OK,二层+ v3.x

---

### D.8 OR pattern `Some(x) | Some(x)` (v1.3.7)

**语法**: 用 `|` 把多个 pattern 组合,匹配任一即可。**两边必须绑同名 + 同类型**。

```rust
match opt {
    Some(x) | Some(x) => x,  // OK — 两边都是 x
    None => 0,
}

match opt {
    Some(x) | Some(y) => x + y,  // ERROR — OR pattern bindings must match: x != y
    None => 0,
}
```

**实现**: sema `check_or_consistency` 2-pass walker 收集 (variant_name, bind_name, payload_type) per branch,两边列表必须 pairwise 一致。WILD pattern (`_`) 视作 "no binding"。

**限制**:
- OR pattern 仅支持 enum variant (不支持 tuple / struct pattern)
- OR 两边必须绑同名 + 同类型
- 嵌套 OR (`A | B | C`) 暂不支持
- OR + WILD 混搭: `Some(x) | None` OK (None 无 binding)

---

### D.9 v1.4 DWARF debug + gdb_pretty.py + jhyy.exe 物理 flip

**v1.4 sprint 增量 (2026-08-13 ~ 2026-08-15):**

- **W-017 codegen 顶层 `let mut` 真修** (commit `f20e36d` 2026-08-14) — `compiler/src/codegen.c` + `compiler/src0/codegen.jhyy` 加 mod_globals dict registration + cg_find_local fallthrough to globals + cg_emit_load/store dispatch on IRVAL_STR addr. src0 production 无外部 C runtime helper `jhyy_helpers.c` 依赖.
- **W-018 DWARF emit Stage 1 IL 字节差异误报 RESOLVED** (2026-08-14) — `stage1-expanded.sh` 脚本错写路径吞错, 改后 7/7 PASS, W-018 是误报 RESOLVED.
- **W-019 codegen 嵌套 struct field chain 真修** (commit `6638134` 2026-08-14) — `cg_field_addr` 嵌套 struct 字段 (`(*o).inner.a`) `loadsw`/`loadw` 第一操作数类型错真修. 现有 `nested_struct_test.jhyy` 1-layer 嵌套覆盖 (regress PASS).
- **W-020 parser inline match-as-expression reorder 真修** (commit `ad42117` 2026-08-14) — jhyy-side `parser.jhyy` `parse_pattern` 在 match arm 上下文处理 `Color::Variant` 时 `parser_check(p, TOKEN_COLONCOLON())` 返 0 修复.
- **gdb_pretty.py + .gdbinit + DWARF debug info emit** (v1.4.2 ~ v1.4.3) — 验证 struct/enum/slice pretty-printer, 配套 `compiler/tests/examples/gdb_pretty_test.jhyy` 集成测试.
- **jhyy.exe 物理 flip v1.4.4** (2026-08-14) — Stage 0 链 C-side bootstrap → jhyy_stage0.exe → jhyy.exe production binary 切换, baseline lock 启动.

**限制**: nested struct 1-layer 覆盖, 2-layer / Outer 多 field 字段序后置 推后续 (per `workarounds.md` W-061 🟡 DEFERRED v1.8 新发现).

### D.10 v1.5 installer Burn bundle + VSCode ext + RunOnce

**v1.5 sprint 增量 (2026-08-15 ~ 2026-08-18):**

- **W-021 WiX 7 Bal.wixext 名字查找失败 → permanent workaround 化** (v1.5.7-rc1) — `-ext WixToolset.Bal.wixext` 名字查找 WIX0144 fail (装的 DLL 文件名是 `WixToolset.BootstrapperApplications.wixext.dll` 不是 `WixToolset.Bal.wixext.dll`), 改用 DLL 绝对路径永久 workaround (WiX 上游不会改 DLL 命名, 不再尝试 revert). v1.7.1 patch B1 RESOLVED 永久 workaround.
- **W-051 MSI deferred ExeCommand CustomAction type 34 → HKLM RunOnce 改写** (v1.5.7-rc1) — SYSTEM token 下 systematic 报 1721 (`CreateProcess` argv mis-tokenize cmd/c 链), 改用 HKLM RunOnce (USER context 跑 master .bat + 多个 .ps1), trade-off 是 fresh install 需 logoff/logon 一次. v1.7.1 patch B2 RESOLVED permanent workaround shipped.
- **W-022 / W-023 / W-024 CI infra** — PS5.1 + GH Actions runner 升级绑定, 不同 axis, 推 v2.x CI infra 重构时.
- **W-026 regress.py stderr 截断修复** (commit `0d58efe` 2026-08-15) — FAIL print `[:80]` 截断隐藏 QBE/gcc link 错误, 改成完整 stderr 输出.
- **W-027 GH Actions setup-msys2@v2 fix** (commit `4623a3b` 2026-08-15) — setup-msys2 装在 `$RUNNER_TEMP\msys64`, 改 deterministic MSYS2 root + known bin subdirs.
- **W-028 Windows ExitProcess 8-bit mod-256 fix** (commit `6d2ab8f` 2026-08-15) — mod 256 comparison in regress.py (`sys.platform in ("win32", "cygwin", "msys")`).
- **v1.5.10 RunOnce auto-install VSCode ext** (commit `c057aa3` 2026-08-27) — `install-configure-all.bat` step 3 inline `code --install-extension`, **真"开箱即用"闭环**; 废弃 install-vsix.bat (parser bug per `feedback_install_vsix_bat_parser_bug`).

**限制**: WiX Bal.wixext 永久 workaround 不解决, 推 v2.x 自写 BAFunctions; CI infra 三 workaround 推 v2.x CI 重构.

### D.11 v1.6 W-053 char literal escape + W-054 sizeof data layout + 7A/7B 增量

**v1.6 sprint 增量 (2026-08-26 ~ 2026-08-27):**

- **W-053 字符字面量转义不全 + hex escape 漏解码真修** — spec §4.4 字符字面量族 (`\n \t \r \0 \\ \' \" \xHH`) 全漏 decode; `'` 后的 char 走 `t.start[1]` 直接当 ASCII, 导致 pattern match 的 char arm 永假; `'\\'` `'\''` `'\"'` lex ERROR. 修复: `src/lexer.c scan_char` escape switch 加 `'"'` + `src/parser.c` 提取共享 `decode_char_literal()` (含 hex_val 子函数) + `src0/lexer.jhyy` 镜像加 `e == 34` + `src0/parser.jhyy` 3 处 TOKEN_CHAR decode 全镜像 (并修复 `parse_pattern_primary` `p_addr = t.start` 漏 +1 offset 的旧 bug). 新增 `char_literal.jhyy` (9 escape case) + `char_pattern.jhyy` (`'\n'` literal match + `'a'..'z'` range match) integration test. 5/5 PASS per `feedback_fix_evaluation_rule`. Stage 2 byte-equal 闭环 hold.
- **W-052 match literal range pattern `1..10` parser + codegen 真修** — 两边都漏 DOTDOT follow-up + NODE_PATTERN_LIT manual emit. 修复: `try_pattern_range` helper (C-side parser.c) / `parse_pattern_primary` + DOTDOT follow-up (jhyy-side parser.jhyy) + manual emit NODE_PATTERN_LIT (C-side codegen.c) + manual emit NODE_PATTERN_LIT/NODE_INT (jhyy-side codegen.jhyy). 新增 `compiler/tests/examples/match_range.jhyy` integration test (regress 54/54 PASS, 3 skip). Stage 2 byte-equal 闭环 hold.
- **W-054 sizeof IL `%t0` undefined 误报 RESOLVED via W-053 chain** — 真因 = W-053 fix 路径上, 把 `qbe_type_of` (i8→'w' widening) 应用到 data section 时, word-packed const array 的 byte 25 落到 7th word 的 2nd byte (= 0), 期望值 122 错误. 修复: `src/ir.c` 拆 `qbe_type_of` (SSA widen 必 word-sized, QBE 拒 'b'/'h') vs 新 `qbe_data_type_of` (data section 字节 packed, const array 字节寻址正确). W-054 不需要单独修, 作为 W-053 fix chain 副作用消除.
- **v1.6.0 Stage 3 char UTF-8 2-byte BMP** (commit `b0e9c3c`) — `scan_char` / `lex_scan_char` UTF-8 lead byte (0x80/0xE0/0xF0) + continuation; `decode_char_literal` 返 uint32_t; sema NODE_CHAR PRIM_U8 → PRIM_I32; codegen NODE_CHAR drop truncation. 新增 `char_utf8_basic.jhyy` (3 个 2-byte BMP) integration test. 3-byte / 4-byte codepoint 显式 lex reject 推 v2.x (per `workarounds.md` W-057 🟡 DEFERRED v2.x 新登).
- **v0.7 7A enum match 穷尽性检查 + 7B 顶层 const 数组** — `compiler/src0/parser.jhyy` + `compiler/src0/sema.jhyy` 同步 enum match check + const 数组 init list 解析 + codegen data section emit.

### D.12 v1.7 W-055 pointer arith + W-056 UTF-8 + float suffix + W-042 + W-021/W-051 docs

**v1.7 sprint 增量 (2026-08-27 ~ 2026-08-28; 含 v1.7.0 5 段 + v1.7.1 patch 5 + v1.7.2 patch 6 + v1.7.3 final 16):**

- **W-055 spec §9.5 指针算术 4 形式真修** (v1.7.0 Stage 2 commits `6216138`+`187e8ab` 2026-08-28) — `*T + int` / `*T - int` / `int + *T` / `*T - *T` / `p[n]` 全 ship. sema + codegen 镜像 src + src0. 3 诊断 test (`ptr_arith_basic.jhyy` / `_diff.jhyy` / `_subscript.jhyy`) 进 default regress. Stage 2 N=3 byte-equal closure 保留. 后续推 v2.x = pointer comparison `p < q` + bounds check (`&mut` lifetime).
- **W-056 char UTF-8 2-byte BMP ship** (v1.7.0 Stage 3 2026-08-27, 跟 v1.6.0 Stage 3 一并) — spec §4.4 BMP-only 限制明确. 3-byte / 4-byte codepoint 推 v2.x (per `workarounds.md` W-057).
- **Float suffix `f32` / `f64` 显式** (v1.7.0 Stage 5 2026-08-28, commit `c04c546`) — spec §4.5 字面量族扩 `1.0f32` / `1.0f64` / `1.0f` 显式后缀.
- **W-042 link_with_gcc 失败诊断增强** (v1.7.1 patch A1 2026-08-28) — Tier 1 invoke_buf echo (v1.5.6) + Tier 2 stderr capture via pipe (v1.7.1 patch A1) + Tier 3 post-link .exe stat (v1.7.1 patch A1) 全链 ship.
- **match arm parity fix** (v1.7.1 patch A2) — C-side `cg_expr` 加 NODE_ASSIGN case → 委托 cg_stmt (cg_stmt.c:1949 完整 handle 所有 target). jhyy-side src0/codegen.jhyy:1880 早就合并所有 stmt cases, 一直正确. C-side 是真 parity gap, v1.7.1 patch A2 真修.
- **enum match arm tag check** (v1.7.1 patch A3) — `compiler/tests/examples/enum_match_arm_tag_check.jhyy` 验证 enum variant 短名 pattern + tag compare parity src + src0.
- **u32 隐式字面量推断** (v1.7.1 patch A4) — sema NODE_LET 加 int literal coerce — decl 是 int primitive 时, 自动 coerce literal init 到 decl type. 8 primitive (i8/i16/i32/i64/u8/u16/u32/u64) 全 ship (v1.7.3 patch A4 加 u32_let_inferred_5.jhyy 补 i8/i16/u8/u16 4 个 primitive 缺漏).
- **W-021 / W-051 docs RESOLVED** (v1.7.1 patch B1+B2) — WiX Bal.wixext 永久 workaround 化 + MSI deferred CA → HKLM RunOnce 永久 workaround 化, workarounds.md 标 ✅ RESOLVED permanent workaround shipped (not removed per `feedback_document_workarounds_in_docs.md`).
- **NODE_SIZEOF src0 parity** (v1.7.2 patch A1) — `compiler/src0/codegen.jhyy` + `compiler/src0/sema.jhyy` 镜像 src/codegen.c + src/sema.c, Stage 2 byte-equal closure 保留.
- **NODE_PATTERN_ENUM spill src0 parity** (v1.7.2 patch A2) — `compiler/src0/codegen.jhyy` NODE_PATTERN_ENUM emit 镜像 src/codegen.c, Stage 2 byte-equal closure 保留.
- **sizeof 数据布局 promote** (v1.7.2 patch A3) — `sizeof_basic.jhyy` + `sizeof_derived.jhyy` 集成测试, 进 default regress.
- **min_enum fix** (v1.7.2 patch A4) — `compiler/tests/examples/min_enum.jhyy` 验证 enum short-name pattern + tag compare parity.
- **gdb_pretty 注释更新** (v1.7.2 patch B3) — `gdb_pretty_test.jhyy:15-18` 注释 "deferred to v1.8" outdated 标记 (v1.7.3 patch A7 注释再更新 nested_struct_dwarf.jhyy deferred to v1.8 due to W-061).
- **W-006 / W-007 / W-042 / W-051 docs** (v1.7.2 patch B4) — workarounds.md 章节 doc 修订, ACTIVE → RESOLVED 标记同步.
- **v1.7.3 FINAL 16 候选 ship** (2026-08-28) — 7 new test (6 SKIP due to W-059/060/061 真 bug 推 v1.8, 1 PASS = u32_let_inferred_5) + 5 spec 修订 + 4 workarounds (W-055 stale fix + W-057/058/059/060/061 新登). src/src0 改 0 行, binary baseline lock hold (jhyy.exe `c140708d...` / jhyy_stage0.exe `a7673a35...` / N=4 closure sha 不变). 后续 sprint = v2.x ‖ v3.x 并行启动 (per `docs/plans/roadmap/v2-v3-parallel-sprint-plan.md`).

---

## 附录 E：v1.x 已知限制 (MVP 边界, v1.3.0 更新)

| # | 严重度 | 描述 | 影响 |
|---|--------|------|------|
| **P3** | MVP 边界 | `#[inline]` 仅展开 body 是单条 `return <expr>;` 的 fn | struct return / 多 stmt / if-else / 循环 body → fall back `call` (per changelog § v1.3.5) |
| **P3** | MVP 边界 | `#[inline]` 递归调用 → fall back `call $name` | 编译器行为正确,只是不展开 |
| **P3** | MVP 边界 | `defer` 不支持 `defer { block; }` 块语法 | v3.x 候选 |
| **P3** | MVP 边界 | `defer` 不触发跨循环 / 内联 / 嵌套 block | v3.x 候选 |
| **P3** | MVP 边界 | OR pattern 仅支持 enum variant | tuple / struct pattern v3.x |
| **P3** | MVP 边界 | OR pattern 两边必须绑同名 + 同类型 | `Some(x) \| Some(y)` 拒绝 |
| **P3** | MVP 边界 | 嵌套 OR (`A \| B \| C`) 不支持 | v3.x 候选 |
| **P3** | MVP 边界 | 嵌套 pattern 二层+ (`Some(Some(Some(x)))`) 不支持 | v3.x 候选 |
| **P3** | MVP 边界 | guard pattern (`Some(x) if x > 0`) 不支持 | v3.x 候选 |

---

**规范版本**: v1.3.0（frozen）
**变更**: 此版本后任何破坏性语法/语义改动必须先走 RFC 流程
**来源**: v1.1.0 (2026-06-26) + v1.3.x 语法糖 Phase 4 (2026-08-12 ~ 2026-08-13 ship 6 sprint)
