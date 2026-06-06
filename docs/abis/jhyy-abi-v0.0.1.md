# JHYY ABI 白皮书 v0.0.1

**日期**: 2026-06-05
**状态**: 草案 — 基于编译器 v0.0.2 实现反推
**目标**: 在自举和 OS 开发前锁定 ABI，避免反复推翻

---

## 1. 目标平台

| 项目 | 选择 |
|------|------|
| **架构** | x86-64 (AMD64) |
| **目标三元组** | `amd64_win` → Windows x64 PE / MinGW COFF |
| **汇编格式** | GAS (GNU Assembler)，QBE 后端输出 |
| **链接器** | GNU ld (via GCC) |
| **运行时** | MinGW ucrt64 (Windows Universal CRT) |

**决策记录**: 不急于切换 ELF64。当前 PE/MinGW COFF 路径已验证可通过
`qbe -t amd64_win` + `gcc` 生成可执行文件。OS 阶段再评估是否需要
freestanding ELF 目标。

---

## 2. 类型布局

### 2.1 原始类型 (Primitives)

| JHYY | C 等价 | sizeof | alignof | QBE | 备注 |
|------|--------|--------|---------|-----|------|
| `i8` | `int8_t` | 1 | 1 | `w` | 加载后零扩展为 word |
| `i16` | `int16_t` | 2 | 2 | `w` | 加载后零扩展为 word |
| `i32` | `int32_t` | 4 | 4 | `w` | |
| `i64` | `int64_t` | 8 | 8 | `l` | |
| `u8` | `uint8_t` | 1 | 1 | `w` | 同 i8，无符号 |
| `u16` | `uint16_t` | 2 | 2 | `w` | 同 i16，无符号 |
| `u32` | `uint32_t` | 4 | 4 | `w` | |
| `u64` | `uint64_t` | 8 | 8 | `l` | |
| `f32` | `float` | 4 | 4 | `s` | IEEE 754 binary32 |
| `f64` | `double` | 8 | 8 | `d` | IEEE 754 binary64 |
| `bool` | `_Bool` | 1 | 1 | `w` | 仅取值 0 或 1 |

**关键规则**:
- 所有原始类型的 `alignof(T) == sizeof(T)`（bool 除外，bool 为 1）
- 子 word 类型 (i8/u8/i16/u16/bool) 在 QBE SSA 中提升为 `w` (32-bit word)
- 内存中的 sub-word store/load 当前使用 `storew`/`loadw`，**未做边界掩码**
  - 未来应在 store 时截断、load 时做符号/零扩展 (`extsb`, `extub`, `extsh`, `extuh`)

### 2.2 指针 `*T`

```
sizeof(*T)  = 8
alignof(*T) = 8
QBE type    = l
```

64 位平面地址空间。空指针为整数 0。指针算术以 `sizeof(T)` 为步长。

### 2.3 切片 `[*]T` (未完整实现)

```
sizeof([*]T)  = 16
alignof([*]T) = 8
布局: { ptr: *T (offset 0, 8B), len: u64 (offset 8, 8B) }
QBE type      = l (仅指针部分)
```

### 2.4 定长数组 `[T; N]` (未完整实现)

```
sizeof([T; N])  = N × sizeof(T)  （无 padding）
alignof([T; N]) = alignof(T)
```

### 2.5 结构体 `struct`

#### 布局算法

```
offset = 0
max_align = 1
for each field (按声明顺序):
    align = alignof(field_type)
    offset = align_up(offset, align)     // 对齐到字段对齐边界
    field.offset = offset
    offset += sizeof(field_type)
    max_align = max(max_align, align)
total_size = align_up(offset, max_align)  // 尾部对齐到最大字段对齐
```

#### 示例

```rust
type Point = struct { x: i32, y: i32 }
// sizeof = 8, alignof = 4
// x: offset 0, size 4
// y: offset 4, size 4

type Mixed = struct { a: i8, b: i64, c: i32 }
// sizeof = 24, alignof = 8
// a: offset 0, size 1  (padding 7 bytes)
// b: offset 8, size 8
// c: offset 16, size 4 (padding 4 bytes to align total)
```

#### 结构体相等性

**名义相等** (nominal typing): 两个结构体类型当且仅当 `name` (Sym 指针) 相同时才视为同一类型。
字段布局相同但声明名不同的 struct 是**不同类型**。

### 2.6 枚举 `enum`

#### 布局算法

```
tag_size = 4                           // i32 tag
max_payload_size = max(各变体 payload 的 sizeof)
max_payload_align = max(各变体 payload 的 alignof)
total_align = max(max_payload_align, 4)

payload_offset = align_up(tag_size, max_payload_align)
total_size = align_up(payload_offset + max_payload_size, total_align)
```

#### 内存布局

```
+--------+-----------+-------------------+
| tag    | padding   | payload           |
| i32    | (可变)    | (max_payload_size)|
| 4 bytes|           |                   |
+--------+-----------+-------------------+
|<-- payload_offset -->|
|<------------- total_size ------------->|
```

#### 变体 tag 分配

从 0 开始，按声明顺序递增。第一个变体 tag=0，第二个 tag=1，以此类推。

#### 示例

```rust
type Option = enum { Some(i32), None }
// sizeof = 12, alignof = 4
// tag_size = 4, max_payload_size = 4, max_payload_align = 4
// payload_offset = align_up(4, 4) = 4
// total_size = align_up(4 + 4, 4) = 8
// (实际实现中: total_size = 8 时有对齐问题，当前代码生成 min 4)

type Result = enum { Ok(i64), Err(i32) }
// sizeof = 16, alignof = 8
// tag_size = 4, max_payload_size = 8, max_payload_align = 8
// payload_offset = align_up(4, 8) = 8
// total_size = align_up(8 + 8, 8) = 16
```

#### 枚举相等性

**名义相等** (nominal typing): 同 struct。

### 2.7 类型别名 `type Name = T`

透明别名。`sizeof`、`alignof`、相等性均穿透到 underlying type。

### 2.8 函数类型 `fn(T1, T2) -> Ret`

```
sizeof(fn)  = 8   (函数指针)
alignof(fn) = 8
```

### 2.9 Unit `()`

```
sizeof(())  = 0
alignof(()) = 1
```

零大小类型。不占用栈空间，不生成 ret 值。

---

## 3. 函数调用约定

### 3.1 底层约定 (继承 Windows x64)

JHYY 编译器通过 QBE 的 `-t amd64_win` 目标继承 **Microsoft x64 Calling Convention**:

| 规则 | 描述 |
|------|------|
| **整型参数** | 前 4 个: RCX, RDX, R8, R9；其余: 栈 (从右向左 push) |
| **浮点参数** | 前 4 个: XMM0-XMM3；其余: 栈 |
| **返回值** | 整型: RAX；浮点: XMM0 |
| **调用者清理** | caller cleans stack |
| **Shadow space** | 调用者在栈上预留 32 字节 (由 QBE 自动处理) |
| **栈对齐** | 16 字节对齐 (call 指令前) |
| **保留寄存器** | RBX, RBP, RDI, RSI, RSP, R12-R15, XMM6-XMM15 |
| **易失寄存器** | RAX, RCX, RDX, R8-R11, XMM0-XMM5 |

### 3.2 JHYY 层面的参数传递

#### 当前规则 (v0.0.2)

1. **所有参数类型必须是标量**: i8-u64, f32/f64, bool, 指针
2. **结构体和枚举不直接按值传递**: 调用者分配栈空间，传递指针
3. **参数在函数体内映射为 SSA 临时量**:
   ```
   %t0 =w copy %param_name     ; 将 QBE 参数复制到 SSA temp
   ```
4. **切片和定长数组当前不支持作为参数类型**

#### 参数求值顺序

**未定义** (由编译器决定)。当前实现: 从左到右。

### 3.3 返回值

| 返回类型 | 约定 |
|---------|------|
| 原始类型 (i8-u64, f32/f64, bool) | 直接放在 RAX/XMM0 中返回 |
| 指针 | 放在 RAX 中返回 |
| struct/enum | **不直接支持按值返回**，调用者通过隐式指针参数接收 |
| `()` (void) | 不生成 ret 值，函数尾部 `ret` 无操作数 |

#### 表达式导向的函数返回

```rust
fn add(a: i32, b: i32) -> i32 {
    a + b       // 最后一个表达式不加 return，即为返回值
}

fn early_exit(n: i32) -> i32 {
    if n < 0 {
        return 0;   // 提前返回用 return
    }
    n * 2
}
```

编译为:
```qbe
export function w $add(w %a, w %b) {
@start0
    %t0 =w copy %a
    %t1 =w copy %b
    %t2 =w add %t0, %t1
    ret %t2
}
```

### 3.4 名称修饰 (Name Mangling)

**当前规则**: `$` + 函数名

```
jhyy: fn main_jhyy() -> i32 { 0 }
asm:  $main_jhyy
```

- 无命名空间/模块前缀
- 无类型编码
- 无重载支持
- 与 C 的链接: `extern fn` 声明直接使用 C 符号名 (不加 `$` 前缀... 实际当前实现 extern 函数体为空，链接由 GCC 完成时需要 C 符号名)

**已知问题**: JHYY 函数导出为 `$name` (QBE `export function`)，但调用 `extern fn` C 函数时使用的是 `call $c_fn_name`，这给 C 函数名也加了 `$` 前缀。在未来模块系统中需要修正。

---

## 4. 内存模型

### 4.1 栈分配

| 场景 | 分配方式 | QBE 指令 |
|------|---------|---------|
| `let mut x: T = v` | 栈槽 | `%s =l alloc8 <max(4, sizeof(T))>` |
| struct 字面量 | 栈槽 | `%s =l alloc8 <struct_size>` |
| enum 构造 | 栈槽 | `%s =l alloc8 <enum_size>` |
| for 循环变量 | 栈槽 (hardcoded i32) | `%s =l alloc4 4` |

**最小栈槽**: 4 字节 (`alloc4 4`)，即使 T 的 sizeof 为 1。

**栈空间生命周期**: 函数作用域内有效。编译器不插入栈保护/金丝雀。

### 4.2 不可变绑定

```
let x = 42;   →  %x =w copy 42     (纯 SSA，无栈分配)
```

不可变变量直接作为 SSA 临时量，不分配栈空间。**不能取地址** (`&x` 编译通过但行为未定义)。

### 4.3 Arena 堆分配 (运行时)

Arena 不在编译器内部实现，而是通过调用运行时 C 函数:

```c
// runtime/runtime.c
typedef struct { char *start; char *cur; char *end; } Arena;
// sizeof(Arena) = 24

void  arena_new(Arena *a, size_t size);       // malloc + 初始化
void *arena_alloc(Arena *a, size_t size, size_t align);  // bump allocate
void  arena_reset(Arena *a);                   // cur = start
void  arena_destroy(Arena *a);                 // free(start)
```

**Arena 不自动析构**: 用户负责调用 `arena_destroy`。未来可能支持 `defer` 或在 Arena 离开作用域时自动释放。

---

## 5. 程序入口

### 5.1 启动流程

```
1. C 运行时初始化 (GCC 链接的 crt)
2. main(argc, argv)  →  runtime.c
3. main() 调用 main_jhyy()
4. main_jhyy() 返回值 →  main() 的返回值 → 进程退出码
```

```c
// runtime/runtime.c
int main(int argc, char **argv) {
    (void)argc;
    (void)argv;
    return main_jhyy();
}
```

### 5.2 用户入口

```rust
// 每个 JHYY 程序必须定义
fn main_jhyy() -> i32 {
    0   // 返回 0 表示成功
}
```

- 返回值类型必须是 `i32` 或可隐式转换为 `i32`
- 命令行参数: 当前版本不传递给 `main_jhyy`，未来通过 `os::args()` 获取
- 当前无 `main` 函数重载或 `#[start]` attribute

---

## 6. QBE IL 映射速查

### 6.1 指令映射

| JHYY 表达式 | QBE IL | 宽度由 |
|------------|--------|--------|
| `42` | `%tN =w copy 42` | 类型推断 |
| `a + b` | `%tN =w add %tA, %tB` | 操作数类型 |
| `a - b` | `%tN =w sub %tA, %tB` | |
| `a * b` | `%tN =w mul %tA, %tB` | |
| `a / b` (有符号) | `%tN =w div %tA, %tB` | |
| `a % b` (有符号) | `%tN =w rem %tA, %tB` | |
| `-a` | `%tN =w sub 0, %tA` | |
| `a == b` | `%tN =w ceqw %tA, %tB` | 结果总是 w |
| `a != b` | `%tN =w cnew %tA, %tB` | |
| `a < b` (有符号) | `%tN =w csltw %tA, %tB` | |
| `a <= b` (有符号) | `%tN =w cslew %tA, %tB` | |
| `a > b` (有符号) | `%tN =w csgtw %tA, %tB` | |
| `a >= b` (有符号) | `%tN =w csgew %tA, %tB` | |
| `a && b` | `%tN =w and %tA, %tB` | **注意**: 非短路求值 |
| `a \|\| b` | `%tN =w or %tA, %tB` | **注意**: 非短路求值 |
| `a & b` | `%tN =w and %tA, %tB` | |
| `a \| b` | `%tN =w or %tA, %tB` | |
| `a ^ b` | `%tN =w xor %tA, %tB` | |
| `a << b` | `%tN =w shl %tA, %tB` | |
| `a >> b` (有符号) | `%tN =w shr %tA, %tB` | |
| `~a` | `%tN =w xor %tA, -1` | |
| `!a` | `%tN =w ceqw %tA, 0` | 结果总是 w |
| `*ptr` | `%tN =w loadw %ptr` | 目标类型 |
| `*ptr = val` | `storew %val, %ptr` | 值类型 |
| `f(args)` | `%tN =w call $f(w %a, l %b)` | 返回类型 |
| `if/else` (表达式) | `jnz` + `jmp` + `phi` | |
| `match` | 链式 `jnz` + `jmp` + `phi` | |

### 6.2 比较运算的类型限定

所有比较指令当前硬编码为 **有符号 word 比较** (`csltw`, `cslew`, `csgtw`, `csgew`, `ceqw`, `cnew`)。

**已知限制**:
- 无符号比较 (`cultw`, `culew`, `cugtw`, `cugew`) 未实现
- 64 位比较 (`csltl`, `ceql`) 未实现（`u64`/`i64` 的比较会错误地使用 `w` 版本）
- 浮点比较 (`cunelts`, `cuneqtd` 等) 未实现

### 6.3 移位运算的宽度

`shl`/`shr` 当前使用 `w` 宽度 (`%tN =w shl %tA, %tB`)。64 位移位应在 `l` 宽度下操作。

---

## 7. FFI (Foreign Function Interface)

### 7.1 extern fn 声明

```rust
extern fn puts(s: *u8) -> i32;
extern fn malloc(size: u64) -> *u8;
```

- `extern fn` 不生成函数体
- 参数类型限于标量 (i8-u64, 指针, bool)
- 调用时使用 QBE `call $name(...)`
- 链接时由 GCC 解析符号

### 7.2 从 C 调用 JHYY

```c
// runtime.c 中
extern int main_jhyy(void);   // JHYY 函数以 C 可见符号导出
int result = main_jhyy();
```

JHYY 导出的函数以 `$name` QBE 导出 → 汇编符号为 `name` (GAS for Windows 去除 `$` 前缀的细节由 QBE 处理)。

### 7.3 ABI 边界规则

| 方向 | 支持的参数类型 |
|------|-------------|
| JHYY → C | i32, i64, *T (指针) |
| C → JHYY | i32 (返回值) |
| JHYY → JHYY | 全部标量类型 |

**不支持**: struct/enum 按值传递跨 FFI 边界、浮点参数跨 FFI (未测试)、变参函数。

---

## 8. 已知局限与待解决 (v0.0.2)

### 8.1 阻塞自举的关键问题

| # | 问题 | 影响 | 方向 |
|---|------|------|------|
| A1 | 结构体不能按值传递/返回 | 不能用 struct 做函数参数 | 实现 C ABI 兼容的 struct passing |
| A2 | Hash 表查找不稳定 (P0) | 符号解析偶发失败 | 重写 symtab 或修复 FNV-1a |
| A3 | 无符号/64位/浮点比较未实现 | u32/u64/f32/f64 的比较结果错误 | 按 QBE 类型选正确比较指令 |
| A4 | 名称修饰过于简单 ($name) | 无模块隔离，符号冲突 | 设计模块级名称修饰方案 |
| A5 | sub-word 类型无截断/扩展 | i8/u8/i16/u16 运算可能带垃圾高位 | load 时加 ext, store 时截断 |

### 8.2 暂不阻碍但需注意

| # | 问题 |
|---|------|
| B1 | `&&` / `||` 是逐位运算，非短路求值 |
| B2 | for 循环变量 hardcoded 为 i32 (4 字节) |
| B3 | 无栈溢出保护/金丝雀 |
| B4 | 切片 `[*]T` 布局已定义但无 codegen |
| B5 | 定长数组 `[T; N]` 布局已定义但无 codegen |
| B6 | 无线程模型/TLS 约定 |
| B7 | 无 DWARF 调试信息 |

---

## 9. 版本兼容性承诺

### 9.1 此版本锁定的内容 (不会变)

- 原始类型的 sizeof/alignof
- 指针大小 (64-bit)
- struct 字段对齐和排列算法
- enum 的 tag (i32, offset 0) 布局

### 9.2 后续版本可能改变的内容

- 名称修饰方案 (引入模块前缀)
- 函数调用约定中 struct/enum 的传递方式
- 运行时入口 (可能支持 `argv` 传递)
- 栈分配的最小粒度 (当前 4 字节)

### 9.3 变更流程

任何 ABI 级变更必须:
1. 更新此文档
2. 更新版本号 (v0.0.1 → v0.1.0)
3. 在 `docs/logs/` 中追加迁移说明

---

## 附录: QBE 类型宽度对照

```
QBE 'b' (byte)   — 未使用 (sub-word 类型提升为 w)
QBE 'h' (half)   — 未使用
QBE 'w' (word)   — i8, i16, i32, u8, u16, u32, bool
QBE 'l' (long)   — i64, u64, *T, fn ptr
QBE 's' (single) — f32
QBE 'd' (double) — f64
```
