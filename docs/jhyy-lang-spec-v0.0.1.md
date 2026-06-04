# 机会翼游 (JHYY) 语言规范 v0.0.1

## 概述

**JHYY**（机会翼游）是一门静态类型的、表达式导向的编译型系统编程语言。语法借鉴 Rust，后端使用 QBE（Quick Backend），编译器宿主语言为 C。

### 编译流水线

```
.jhyy → Lexer → Parser → AST → Semantic Analysis → QBE IL → Assembly → Executable
```

### 平台

- **开发环境**: Windows 10 + MSYS2
- **编译器**: GCC 15.2.0 (C 语言编写)
- **后端**: QBE (`-t amd64_win`)
- **运行时**: `compiler/runtime/runtime.c`（Arena 内存管理 + main 入口）

---

## 1. 程序结构

### 1.1 入口点

每个 JHYY 程序必须定义一个 `main_jhyy` 函数，运行时 `main()` 会调用它，其返回值作为进程退出码。

```rust
fn main_jhyy() -> i32 {
    0   // 返回 0 表示成功
}
```

### 1.2 源文件后缀

`.jhyy`

### 1.3 注释

```rust
// 单行注释
/* 块注释（可嵌套） */
```

---

## 2. 类型系统

### 2.1 基本类型

| 类型 | 含义 | 对应 QBE |
|------|------|----------|
| `i8` | 8 位有符号整数 | `b` |
| `i16` | 16 位有符号整数 | `h` |
| `i32` | 32 位有符号整数 | `w` |
| `i64` | 64 位有符号整数 | `l` |
| `u8` | 8 位无符号整数 | `b` |
| `u16` | 16 位无符号整数 | `h` |
| `u32` | 32 位无符号整数 | `w` |
| `u64` | 64 位无符号整数 | `l` |
| `f32` | 32 位浮点数 | `s` |
| `f64` | 64 位浮点数 | `d` |
| `bool` | 布尔值 | `w` |

### 2.2 类型推导

`let` 绑定的类型从初始化表达式自动推导，无需显式标注。可选标注语法 `let x: Type = expr;` 已在 parser 中支持，但类型检查可能不完整。

### 2.3 整数字面量后缀

```
42i8, 100i64, 255u8, 1u16
```

---

## 3. 变量与绑定

### 3.1 不可变绑定

```rust
let x = 42;
let y = x + 1;
```

- 不可变变量的值直接作为 SSA 临时量，不分配栈空间
- 不可重新赋值

### 3.2 可变绑定

```rust
let mut counter = 0;
counter = 10;
```

- 可变变量在栈上分配空间
- 可以通过 `=` 重新赋值

### 3.3 复合赋值

```rust
counter += 5;   // counter = counter + 5
counter -= 2;   // counter = counter - 2
counter *= 3;   // counter = counter * 3
counter /= 4;   // counter = counter / 4
counter %= 5;   // counter = counter % 5
```

---

## 4. 表达式

### 4.1 字面量

```rust
// 整数（各种进制）
let dec = 42;          // 十进制
let hex = 0xFF;        // 十六进制
let oct = 0o77;        // 八进制
let bin = 0b1010;      // 二进制

// 浮点
let pi = 3.14;
let half = 0.5;

// 布尔
let yes = true;
let no = false;

// 字符
let ch = 'a';
let nl = '\n';

// 字符串
let s = "hello";
```

### 4.2 算术运算

| 运算符 | 含义 |
|--------|------|
| `+` | 加法 |
| `-` | 减法 |
| `*` | 乘法 |
| `/` | 除法 |
| `%` | 取模 |
| `-expr` | 取负（一元） |

### 4.3 比较运算

| 运算符 | 含义 |
|--------|------|
| `==` | 等于 |
| `!=` | 不等于 |
| `<` | 小于 |
| `>` | 大于 |
| `<=` | 小于等于 |
| `>=` | 大于等于 |

返回 `bool` 类型。

### 4.4 逻辑运算

| 运算符 | 含义 |
|--------|------|
| `&&` | 逻辑与 |
| `\|\|` | 逻辑或 |
| `!` | 逻辑非（一元） |

### 4.5 位运算

| 运算符 | 含义 |
|--------|------|
| `&` | 按位与 |
| `\|` | 按位或 |
| `^` | 按位异或 |
| `<<` | 左移 |
| `>>` | 右移 |
| `~` | 按位取反（一元） |

### 4.6 块表达式

```
let val = {
    let a = 10;
    let b = 20;
    a + b    // 最后一个表达式是块的值
};
```

块的类型是最后一个表达式的类型。

### 4.7 if-else 表达式

```rust
let max = if a > b { a } else { b };
```

- 有 else 分支 → 表达式，返回两个分支的共同类型
- 无 else 分支 → 语句，类型为 `()`

### 4.8 函数调用

```rust
let result = function_name(arg1, arg2);
```

---

## 5. 控制流

### 5.1 if 语句

```rust
if score >= 90 {
    grade = 4;
} else if score >= 80 {
    grade = 3;
} else if score >= 70 {
    grade = 2;
} else {
    grade = 0;
}
```

### 5.2 while 循环

```rust
let mut i = 0;
while i < 10 {
    i = i + 1;
}
```

循环体最后不需要分号。

### 5.3 early return

```rust
fn early_example(n: i32) -> i32 {
    if n < 0 {
        return 0;      // 提前返回
    }
    n * 2              // 正常返回值（不加 return）
}
```

---

## 6. 函数

### 6.1 函数定义

```rust
fn function_name(param1: Type1, param2: Type2) -> ReturnType {
    // 函数体
    // 最后一个表达式是返回值（不加 return）
}
```

### 6.2 无参数 / 无返回值

```rust
fn no_params() -> i32 {
    42
}

fn no_return() {
    // 隐式返回 ()
}
```

### 6.3 外部函数

```rust
extern fn puts(s: *i32) -> i32;
```

外部函数只声明不定义，由链接时提供符号。

### 6.4 递归

直接或间接调用自身的函数。函数名在编译器内部会**在解析体之前**注册，递归调用工作正常。

```rust
fn fib(n: i32) -> i32 {
    if n <= 1 {
        return n;
    }
    fib(n - 1) + fib(n - 2)
}
```

---

## 7. 类型声明（骨架）

语法已支持，codegen 尚未实现：

```rust
// 类型别名
type Age = i32;

// 结构体（字段解析未实现）
type Point = struct { }

// 枚举（变体解析未实现）
type Color = enum { }
```

---

## 8. 编译器使用

### 8.1 命令行

```bash
# 查看帮助
jhyy

# 编译为可执行文件
jhyy compile <file.jhyy> [-o output]

# 编译并运行
jhyy run <file.jhyy>
```

### 8.2 手动编译步骤

```bash
# 1. 生成 QBE IL
jhyy compile source.jhyy -o output

# 2. QBE → 汇编
qbe.exe -t amd64_win -o output.s output.il

# 3. 链接
gcc output.s compiler/runtime/runtime.c -o output.exe
```

### 8.3 构建编译器

```bash
gcc compiler/src/*.c -o compiler/build/bin/jhyy.exe -I compiler/src
```

---

## 9. 与 Rust 的主要差异

| 特性 | Rust | JHYY v0.0.1 |
|------|------|-------------|
| 最后表达式 | 不加 `;` 即为返回值 | 不加 `return` 即为返回值 |
| `return` 使用 | 用于提前返回 | 用于提前返回 |
| `let mut` | 可变绑定 | 栈分配 + 可变 |
| 类型标注 | `let x: i32 = 1;` | 同语法，部分支持 |
| 代码块 | `{ ... }` | 同语法 |
| for 循环 | `for x in iter` | `for x in start..end`（codegen 未实现） |
| match | 完整模式匹配 | 语法骨架，codegen 未实现 |

---

## 10. 示例程序

完整示例: `compiler/tests/examples/demo.jhyy`

```rust
// 阶乘
fn factorial(n: i32) -> i32 {
    let mut result = 1;
    let mut i = 1;
    while i <= n {
        result = result * i;
        i = i + 1;
    }
    result
}

// 斐波那契（递归）
fn fibonacci(n: i32) -> i32 {
    if n <= 1 {
        return n;
    }
    fibonacci(n - 1) + fibonacci(n - 2)
}

// 主入口
fn main_jhyy() -> i32 {
    let f5 = factorial(5);     // 120
    let fib = fibonacci(10);   // 55

    let mut counter = 1;
    counter += 2;
    counter *= 3;

    0
}
```
