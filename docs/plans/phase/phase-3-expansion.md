# Phase 3: 语言扩展

> 目标：在自举基础上扩展语言能力, 使 jhyy 成为完整的系统编程语言
> 预计：约 6-8 周
> 前置：Phase 2 完成 (自举成功)
> 产出：功能丰富的 jhyy 语言 + 标准库

---

## Sprint 3a: 浮点类型

### 改动范围

- `lexer`: 浮点字面量 `3.14` `3.14f32` (Phase 1 应已支持)
- `types`: f32 ↔ QBE `s`, f64 ↔ QBE `d`
- `codegen`: 浮点算术 (`adds`, `subs`, `muls`, `divs` / `addd`...)
- `codegen`: 浮点比较 (`cges`, `cgts`, `cles`, `clts`, `cnes`, `ceqs`)
- `codegen`: 整数浮点互转 (`stosi`, `dtosi` / `sitod`, `uitos`...)

### 测试
```rust
fn main_jhyy() -> i32 {
    let a: f64 = 3.14;
    let b = a * 2.0;        // b: f64 = 6.28
    let c = b as i32;       // c = 6
    c
}
```

### 验收标准
- [ ] f32/f64 字面量解析
- [ ] 浮点四则运算、比较
- [ ] 整数浮点互转
- [ ] 浮点作函数参数和返回值

---

## Sprint 3b: 泛型 (单态化)

### 设计

```rust
fn max<T>(a: T, b: T) -> T {
    if a > b { a } else { b }
}

let x = max::<i32>(3, 5);    // 生成 max_i32
let y = max::<i64>(100, 200); // 生成 max_i64

type Vec<T> = struct { data: *T, len: i32, cap: i32 };
type Option<T> = enum { Some(T), None };
```

单态化在 sema 之后、codegen 之前执行: 收集所有泛型调用 → 为每种具体类型参数组合生成专用 AST → 替换原调用。

### 实现步骤

1. **语法**: `fn name<T, U>(...)` 和 `name::<T>(args)`
2. **泛型参数存储在 AST**: 类型参数列表挂在函数声明节点上
3. **调用处收集具体类型**: AST 遍历, 找到泛型函数调用
4. **单态化**: 为每种 `(函数, 类型参数组合)` 生成副本
5. **类型检查**: 在单态化后的 AST 上执行 (而非泛型 AST)

### 验收标准
- [ ] 泛型函数定义和调用
- [ ] 泛型 struct 和 enum
- [ ] 多个类型参数 `fn foo<A, B>()`
- [ ] 泛型参数推断 (可从实参推断时省略 `::<T>`)
- [ ] 单态化后 IR 正确

---

## Sprint 3c: 闭包

### 设计 (Phase 3 简化版)

```rust
fn make_adder(n: i32) -> fn(i32) -> i32 {
    |x: i32| { x + n }     // 按值捕获 n
}

let add5 = make_adder(5);
let r = add5(10);   // 15
```

编译为: 闭包结构体 `{ fn_ptr, captured_n }` + 合成函数 `__closure_add5(env, x)`。

### 验收标准
- [ ] 闭包捕获局部变量 (按值)
- [ ] 闭包作为参数和返回值
- [ ] 多变量捕获

---

## Sprint 3d: 错误恢复

当前编译器遇到第一个错误即停止。改为: **利用 `;` 和 `}` 作同步点**, 跳过 token 直到同步点。

```
Parser 错误 → 报告 → 跳到下一个 ; 或 } → 继续解析
Sema 错误  → 报告 → 返回 type_error() → 抑制级联错误
```

### 验收标准
- [ ] 单文件多个语法错误全部报告
- [ ] 单文件多个类型错误全部报告
- [ ] 不出现级联/虚假错误

---

## Sprint 3e: 标准库

### 模块

| 模块 | 功能 |
|------|------|
| `io.jhyy` | 文件读写, stdin/stdout/stderr |
| `fmt.jhyy` | 格式化字符串 (自实现, 不依赖 libc printf 变参) |
| `arena.jhyy` | Arena allocator (纯 jhyy 实现) |
| `string.jhyy` | 字符串操作 (拼接, 查找, 比较, 切片) |
| `math.jhyy` | 数学函数 (sin, cos, sqrt, pow — FFI libm) |
| `os.jhyy` | 系统调用 (open, read, write, exit) |
| `vec.jhyy` | 泛型动态数组 `Vec<T>` |
| `map.jhyy` | 泛型哈希表 `Map<K, V>` |
| `mem.jhyy` | 内存操作 (memcpy, memcmp, memset) |

### 验收标准
- [ ] 每个模块有源码和文档
- [ ] jhyy 编译器自身使用标准库中的 io 和 string(而非原始 FFI)
- [ ] 标准库测试覆盖

---

## Sprint 3f: 基本优化

在 AST → IR 之间加入优化 pass:

| Pass | 内容 | 复杂度 |
|------|------|--------|
| 常量折叠 | `1 + 2*3` → `7` (编译期求值) | 低 |
| 代数化简 | `x + 0 → x`, `x * 1 → x`, `x * 0 → 0` | 低 |
| 死代码消除 | `if false { X } else { Y }` → `Y` | 低 |
| 不可达代码消除 | `return x; dead_code;` → 删除 dead_code | 中 |

### 验收标准
- [ ] 常量折叠: 编译期求值
- [ ] 代数化简: 恒等/零元消除
- [ ] 不破坏正确性 (全量回归通过)

---

## Sprint 3g: 内联汇编

```rust
fn outb(port: u16, value: u8) {
    asm {
        "out %al, %dx"
        : /* 无输出 */
        : "d"(port), "a"(value)
    };
}
```

QBE 不原生支持内联汇编。方案: IR 层记录 asm 块 → 在最终 `.s` 文件中插入对应汇编。

> **对齐 phase-2.5**：phase-3 sprint 3g 跟 phase-2.5 自写 QBE 后端**顺序敏感**。如果 phase-2.5 已完成（自写 QBE + 确定性寄存器分配），sprint 3g 的 asm 块插入走自写后端的"escape hatch"路径；如果 phase-2.5 未完成，仍走 C 版 QBE 工具链的 .s 输出路径。具体顺序由 user 后续决定。

### 验收标准
- [ ] asm 块语法解析正确
- [ ] 汇编代码嵌入最终 `.s` 输出
- [ ] 测试: I/O 端口读写

---

## Sprint 3h: 包管理器

```bash
jhyy new my_project       # 创建项目
jhyy build                # 构建 (读 jhyy.toml)
jhyy test                 # 运行测试
```

### jhyy.toml

```toml
[project]
name = "my_app"
version = "0.1.0"

[dependencies]
io = "0.1"
fmt = "0.1"
```

### 验收标准
- [ ] `jhyy new` 创建项目骨架
- [ ] `jhyy build` 读取依赖并编译
- [ ] 基本依赖管理

---

## Phase 3 完成标准

| 特性 | 来源 |
|------|------|
| 整数、bool、指针 | Phase 1 |
| struct、enum、match | Phase 1 |
| Arena 内存管理 | Phase 1 |
| 模块系统、FFI | Phase 1 |
| 浮点类型 | Sprint 3a |
| 泛型 (单态化) | Sprint 3b |
| 闭包 | Sprint 3c |
| 错误恢复 | Sprint 3d |
| 标准库 (9 模块) | Sprint 3e |
| 基本优化 pass | Sprint 3f |
| 内联汇编 | Sprint 3g |
| 包管理器 | Sprint 3h |

完成后 jhyy 是一门功能完善的系统编程语言：**自举能力已在 phase-2 完成**，phase-3 新增语言特性（浮点/泛型/闭包/标准库/优化/包管理/内联汇编）。
