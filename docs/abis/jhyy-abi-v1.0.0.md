# JHYY ABI 白皮书 v1.0.0

**日期**: 2026-06-17
**状态**: 锁定 — 基于编译器 v0.4.0 / v0.5.0 实现
**目标**: 锁定自举前的最终 ABI，所有 Phase 1 后续版本必须兼容
**取代**: v0.0.1

---

## 1. 目标平台

| 项目 | 选择 |
|------|------|
| **架构** | x86-64 (AMD64) |
| **目标三元组** | `amd64_win` → Windows x64 PE / MinGW COFF |
| **汇编格式** | GAS (GNU Assembler)，QBE 后端输出 |
| **链接器** | GNU ld (via GCC) |
| **运行时** | MinGW ucrt64 (Windows Universal CRT) |
| **中间表示** | QBE IL (`-t amd64_win`) |

**决策记录**:
- 唯一目标是 Windows x64。Linux ELF64 需等 Phase 3 (v0.7.0+)
- 32 位 x86 永久不支持
- ARM/ARM64/WASM 不在 Phase 1 范围内
- OS 阶段再评估 freestanding 目标

---

## 2. 类型布局

### 2.1 原始类型 (Primitives)

| JHYY | C 等价 | sizeof | alignof | QBE | 备注 |
|------|--------|--------|---------|-----|------|
| `i8` | `int8_t` | 1 | 1 | `w` | 加载时符号扩展 (`extsb`) |
| `i16` | `int16_t` | 2 | 2 | `w` | 加载时符号扩展 (`extsh`) |
| `i32` | `int32_t` | 4 | 4 | `w` | |
| `i64` | `int64_t` | 8 | 8 | `l` | |
| `u8` | `uint8_t` | 1 | 1 | `w` | 加载时零扩展 (`extub`) |
| `u16` | `uint16_t` | 2 | 2 | `w` | 加载时零扩展 (`extuh`) |
| `u32` | `uint32_t` | 4 | 4 | `w` | |
| `u64` | `uint64_t` | 8 | 8 | `l` | |
| `f32` | `float` | 4 | 4 | `s` | IEEE 754 binary32 |
| `f64` | `double` | 8 | 8 | `d` | IEEE 754 binary64 |
| `bool` | `_Bool` | 1 | 1 | `w` | 仅取值 0 或 1 |
| `char` | `char` (UTF-8 byte) | 1 | 1 | `w` | 内部为 `i8` |

**关键规则**:
- 所有原始类型的 `alignof(T) == sizeof(T)` (bool/char 除外)
- 子 word 类型 (i8/u8/i16/u16/bool/char) 在 QBE SSA 中提升为 `w` (32-bit word)
- **v0.2.1 起**: sub-word load/store 使用 `extsb`/`extub`/`extsh`/`extuh` 显式扩展
- `i32` 算术溢出是**定义行为**: 二进制补码环绕，无运行时检查
- 浮点立即数格式化为 QBE 字面量 (`s_3.14`, `d_2.71`)

### 2.2 指针 `*T`

```
sizeof(*T)  = 8
alignof(*T) = 8
QBE type    = l
```

64 位平面地址空间。空指针为整数 0。指针算术以 `sizeof(T)` 为步长。

### 2.3 切片 `[*]T`

```
sizeof([*]T)  = 16
alignof([*]T) = 8
布局: { data: *T (offset 0, 8B), len: u64 (offset 8, 8B) }
QBE type      = l (仅指针部分)
```

**当前状态**: **v0.6.0 sprint 6A 已完整实现 codegen**。按 struct pass-by-value sret 处理（与 v0.4 ABI 一致）。支持：切片字面量、数组 decay（`[*]u8` decay 自字符串字面量）、索引、子切片（`s[i..j]`）、`len(s)`。

### 2.4 定长数组 `[T; N]`

```
sizeof([T; N])  = N × sizeof(T)  (无填充)
alignof([T; N]) = alignof(T)
```

**v0.3.0 起完整实现**: 字面量 `[1, 2, 3]`、类型注解 `[i32; 3]`、下标读写 `arr[i]`、下标赋值 `arr[i] = val`。
栈分配: `alloc4 N*4` (i32) / `alloc8 N*8` (i64) / 等。

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

#### 嵌套结构体

嵌套 struct 平坦化为单层布局:
```rust
type Inner = struct { a: i32, b: i32 }
type Outer = struct { x: i32, inner: Inner, y: i32 }
// sizeof = 16, alignof = 4
// x: offset 0, size 4
// inner: offset 4, size 8
// y: offset 12, size 4
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

**v0.4.0 起的完整规则**:

| 参数类型 | 传递方式 |
|---------|---------|
| 标量 (i8-u64, f32/f64, bool, char, 指针) | 按值直接传递 (QBE 参数) |
| `[T; N]` 定长数组 | **v0.4.0 起**: 调用方在栈上分配副本，传递副本地址 (类似 struct) |
| `struct` | **v0.4.0 起**: 调用方在栈上分配副本，**逐字段**复制，传递副本地址 (隐式 `l` 参数) |
| `enum` | 同 struct: 副本地址 |
| `[*]T` 切片 | P2，未实现 codegen |

**实现细节 (struct pass-by-value)**:
```
调用方 (caller):
1. alloc 副本栈槽: %copy =l alloc8 sizeof(struct)
2. cg_copy_struct(struct_type, %copy, src_addr)   // 逐字段复制
3. 传递 %copy 作为参数 (类型 `l`)

被调用方 (callee):
1. 函数签名: function w $foo(l %struct_param)
2. 复制到 SSA: %t0 =l copy %struct_param
3. %t0 即为 struct 的 "地址", 字段访问: %t1 =w loadw %t0  (x 字段)
```

**实现细节 (struct return via sret)**:
```
调用方:
1. alloc 返回槽: %ret_slot =l alloc8 sizeof(struct)
2. 将 %ret_slot 作为**第一个**参数 (隐式)
3. call_void: call $foo(l %ret_slot, ...)  // 无返回值
4. 表达式结果 = %ret_slot

被调用方:
1. 函数签名: function $foo(l %ret, ...)  // 第一个参数是 sret 槽
2. 内部使用: %ret 作为 struct 的 "地址"
3. return 语句: cg_copy_struct(struct_type, %ret, src_addr); ret
4. 函数末尾: ret (无值)
```

### 3.3 返回值

| 返回类型 | 约定 |
|---------|------|
| 标量 (i8-u64, f32/f64, bool) | 直接放在 RAX/XMM0 中返回 |
| 指针 | 放在 RAX 中返回 |
| `struct` / `enum` | **v0.4.0 起**: 通过隐式 sret 指针参数返回 (见 3.2) |
| `()` (void) | 不生成 ret 值，函数尾部 `ret` 无操作数 |
| `[T; N]` 定长数组 | **v0.4.0 起**: 通过 sret 传递 (类似 struct) |

**表达式导向的函数返回**:
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

**v0.5.0 修复**: if/while/for 块作为函数体的最后表达式时正确捕获其值 (之前只捕获 NODE_EXPR_STMT)。

### 3.4 参数求值顺序

**未定义** (由编译器决定)。当前实现: 从左到右。

### 3.5 名称修饰 (Name Mangling)

**当前规则**: `$` + 函数名

```
jhyy: fn main_jhyy() -> i32 { 0 }
asm:  $main_jhyy
```

- 无命名空间/模块前缀
- 无类型编码
- 无重载支持
- 多文件编译 (`v0.4.0`): 所有 .jhyy 文件的函数共享同一全局命名空间
- 模块 import: 当前未对模块内函数加前缀 (可能造成冲突)

**已知问题 (P3)**: ~~JHYY 函数导出为 `$name` (QBE `export function`)，但调用 `extern fn` C 函数时使用的是 `call $c_fn_name`，这给 C 函数名也加了 `$` 前缀。~~ **v0.6.0 sprint 6D.7 已修复**：`Sym.is_extern` 字段 + codegen 检查，extern fn 直接 emit 原名（不加 `$` 前缀）。

---

## 4. 内存模型

### 4.1 栈分配

| 场景 | 分配方式 | QBE 指令 |
|------|---------|---------|
| `let mut x: T = v` | 栈槽 | `%s =l alloc4/8 <sizeof(T)>` |
| `let x: T = v` (immutable) | SSA temp **OR** 栈槽 (类型 ≥ 8 字节) | `copy` 或 `alloc` |
| struct 字面量 | 栈槽 | `%s =l alloc8 <struct_size>` |
| enum 构造 | 栈槽 | `%s =l alloc8 <enum_size>` |
| `[T; N]` 数组 | 栈槽 | `%s =l alloc4/8 <N*sizeof(T)>` |
| for 循环变量 | 栈槽 (i32/i64) | `%s =l alloc4/8 4/8` |
| struct 参数副本 | 栈槽 (caller) | `%s =l alloc8 <struct_size>` |
| struct 返回槽 | 栈槽 (caller) | `%s =l alloc8 <struct_size>` |

**最小栈槽**: 4 字节 (`alloc4 4`)，即使 T 的 sizeof 为 1。

**栈空间生命周期**: 函数作用域内有效。编译器不插入栈保护/金丝雀。

### 4.2 不可变绑定

```
let x = 42;   →  %x =w copy 42     (纯 SSA，无栈分配)
let s = "hello";  →  %s =l copy $str0  (字符串字面量为 data 段)
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

### 4.4 struct 复制语义

`a = b` (a, b 是 struct) 逐字段复制 (含嵌套 struct):

```c
// cg_copy_struct 实现思路
for each field f in struct:
    dst_f_addr = dst + f.offset
    src_f_addr = src + f.offset
    if f.type is struct: recurse
    else: load f from src_f_addr, store to dst_f_addr
```

**不允许浅拷贝**: JHYY struct 不含指针字段 (当前语法不允许)，所以 "浅拷贝" 和 "深拷贝" 没有区别。

### 4.5 数组复制

`a = b` (a, b 是 `[T; N]`) **v0.4.0 起**: 数组字面量值传递，复制整个数组到新栈槽。运行时 memcpy 不存在 (栈内 alloc + 逐元素 store)。

---

## 5. 控制流

### 5.1 if/else 表达式

```jhyy
let x = if cond { a } else { b };
```

编译为 SSA 形式:
```qbe
    %cond =w ...
    jnz %cond, @then, @else
@then
    %tA =w ...  (a 的值)
    jmp @merge
@else
    %tB =w ...  (b 的值)
    jmp @ep
@ep
    jmp @merge  ; trampoline, 避免 else 块内 fallthrough 干扰 phi
@merge
    %result =w phi @then %tA, @ep %tB
```

**v0.5.0 修复 (nested else-if)**: 嵌套 `if/else if` 链中，内层 if 的 merge 块必须 fall through 到外层的 trampoline 块，而不是直接 jmp 到外层 merge (避免错误的 phi 前驱)。

**v0.5.0 修复 (void if)**: `if/else` 中任一分支是 void 时，整个 if 表达式类型为 void，**不**生成 phi (`ret` 也不需要值)。

### 5.2 短路求值 (`&&`, `||`)

```jhyy
a && b    // a 为 false 时跳过 b
a || b    // a 为 true 时跳过 b
```

编译为分支跳转:
```qbe
    %a =w ...
    jnz %a, @then, @else  ; && 时 then=继续, else=短路
@then
    %b =w ...
    jmp @merge
@else
    ; 短路, 不计算 b
    jmp @merge
@merge
    %result =w phi ...
```

### 5.3 循环 (while, for)

**while 循环**:
```qbe
@loop_hdr
    %cond =w ...
    jnz %cond, @body, @loop_end
@body
    ...
    jmp @loop_hdr
@loop_end
    ...
```

**for 循环**: 三个块 (header / body / increment):
```qbe
@loop_hdr
    %i =w phi @entry %start, @incr %i_next
    %cond =w csltw %i, %end
    jnz %cond, @body, @loop_end
@body
    ...
    jmp @incr
@incr                       ; v0.5.0 起单独的块
    %i_next =w add %i, 1
    jmp @loop_hdr
@loop_end
    ...
```

**v0.5.0 关键修复**: `for` 循环中 `continue` 跳转到 `@incr` (跳过 body 直接到 i++)，而 `while` 循环中 `continue` 跳转到 `@loop_hdr` (重新测试条件)。这两者**不能共用**一个 continue 目标。

### 5.4 break / continue

| 循环类型 | `break` 目标 | `continue` 目标 |
|---------|------------|----------------|
| `while` | `@loop_end` | `@loop_hdr` (重新测试) |
| `for`   | `@loop_end` | `@incr` (i++) |

**实现**: CGContext 维护 `loop_starts[]`, `loop_ends[]`, `loop_continues[]` 三个栈，循环嵌套时 push/pop。

**Sema 验证**: `break`/`continue` 必须在循环内 (`loop_depth > 0`)，否则编译错误。

---

## 6. 算术、比较、位运算

### 6.1 QBE 指令映射

| JHYY 表达式 | QBE IL | 宽度规则 |
|------------|--------|---------|
| `a + b` | `add` | 操作数类型 |
| `a - b` | `sub` | |
| `a * b` | `mul` | |
| `a / b` (有符号) | `div` | |
| `a % b` (有符号) | `rem` | |
| `a / b` (无符号) | `udiv` | |
| `a % b` (无符号) | `urem` | |
| `-a` | `sub 0, %a` | |
| `a == b` | `ceqw` / `ceql` / `ceqs` / `ceqd` | 类型感知 |
| `a != b` | `cnew` / `cnel` / `cnes` / `cned` | |
| `a < b` (有符号) | `csltw` / `csltl` | |
| `a <= b` (有符号) | `cslew` / `cslel` | |
| `a > b` (有符号) | `csgtw` / `csgtl` | |
| `a >= b` (有符号) | `csgew` / `csgel` | |
| `a < b` (无符号) | `cultw` / `cultl` | |
| `a <= b` (无符号) | `culew` / `culel` | |
| `a > b` (无符号) | `cugtw` / `cugtl` | |
| `a >= b` (无符号) | `cugew` / `cugel` | |
| 浮点比较 | `cuelts` / `cueltd` / `cseqs` / `cseqd` 等 | |
| `a && b` | `jnz %a, @then_b, @short_circuit` | **v0.2.1 起**: 短路求值 |
| `a \|\| b` | `jnz %a, @short_circuit, @then_b` | |
| `a & b` | `and` | |
| `a \| b` | `or` | |
| `a ^ b` | `xor` | |
| `a << b` | `shl` | |
| `a >> b` (有符号) | `sar` | |
| `a >> b` (无符号) | `shr` | |
| `~a` | `xor -1, %a` | |
| `!a` (bool) | `ceqw %a, 0` 或 `cnel` | |

### 6.2 类型感知的指令选择 (v0.2.1 起)

`v0.2.1` 起，比较指令按操作数类型选择宽度:
- `i32/u32`/`f32` → `w`/`s` 系列
- `i64/u64`/`f64` → `l`/`d` 系列

64 位移位 (`i64`/`u64`) 使用 `l` 宽度 (`shll`, `shrl`, `sarl`)。

### 6.3 浮点算术 (v0.5.0 起)

`v0.5.0` 起，浮点 `+ - * /` 使用 QBE `add`/`sub`/`mul`/`div` 配合 `s` (f32) / `d` (f64) 宽度。
浮点比较 (v0.5.0 待完善): 暂未完整实现，浮点 `==`/`!=` 当前使用 `cnes`/`cned` 风格。
浮点字面量: v0.3.0 起格式化为 `s_3.14` (f32) / `d_2.71` (f64) 字面量。

### 6.4 类型转换 (`as`)

`v0.5.0` 起实现:
- 整数扩宽: `extsw` / `extuw` / `extsh` / `extsb` / `extub` (i32→i64 等)
- 浮点 ↔ 整数: `dtosi` / `dtosl` / `stosi` / `stosl` / `swtof` / `sltof` / `uwtof` / `ultof`
- 浮点互转: `exts` (f32→f64) / `truncd` (f64→f32)

### 6.5 整数溢出 (定义行为)

`i32` 加减乘的溢出是**二进制补码环绕**，不抛错，不做运行时检查:
```rust
let a: i32 = 2147483647;  // i32 max
let b: i32 = a + 2;        // 环绕到 -2147483647 (0x80000001)
```

**未来**: 调试模式可加 `-ftrapv` 类似选项触发 trap。

---

## 7. FFI (Foreign Function Interface)

### 7.1 extern fn 声明

```jhyy
extern fn puts(s: *u8) -> i32;
extern fn printf(fmt: *u8, ...) -> i32;
extern fn fopen(path: *u8, mode: *u8) -> *u8;
```

- `extern fn` 不生成函数体
- 参数和返回类型限于标量 (i8-u64, 指针, f32/f64, bool)
- 调用时使用 QBE `call $name(...)`
- 链接时由 GCC 解析符号

### 7.2 多参数 FFI (v0.4.0 验证)

```jhyy
extern fn printf(fmt: *u8, a: i32, b: i32, c: i32) -> i32;

fn main_jhyy() -> i32 {
    printf("three: %d %d %d\n", 10, 20, 30);
    0
}
```

参数顺序与声明顺序一致；前 4 个标量走 RCX/RDX/R8/R9 寄存器，剩余走栈。

### 7.3 文件 I/O FFI (v0.4.0)

```jhyy
extern fn fopen(path: *u8, mode: *u8) -> *u8;
extern fn fclose(file: *u8) -> i32;

fn main_jhyy() -> i32 {
    let f = fopen("test.txt", "w");
    if f == (0 as *u8) { return 1; }
    fclose(f);
    0
}
```

返回的指针 (`*u8`) 可与 `0` 比较 (`0 as *u8` 显式转换)。

### 7.4 FFI 边界规则 (v1.0.0)

| 方向 | 支持的参数类型 | 支持的返回类型 |
|------|-------------|------------|
| JHYY → C | i8-i64, u8-u64, f32, f64, *T, bool, char | i8-i64, u8-u64, f32, f64, *T, bool |
| C → JHYY | 同上 (通过 `extern fn` 声明) | 同上 |
| JHYY → JHYY | **全部** (含 struct pass-by-value) | **全部** (含 struct sret) |

**不支持**:
- struct/enum 按值跨 FFI 边界 (Windows x64 ABI 复杂，当前未实现)
- 变参函数 (`printf` 的 `...` 在 JHYY 侧需要逐参数列出)
- 回调函数 (P3，Phase 2 考虑)

### 7.5 字符串字面量

JHYY 字符串字面量是 UTF-8 字节序列，存储在 QBE `data` 段:
```qbe
data $str0 = { b "hello", b 0 }
```

通过 `l` (64-bit pointer) 传递给 C 函数。C 函数收到的是 NUL-terminated UTF-8 字符串 (兼容 C `char*` 约定)。

控制台 UTF-8 输出: `runtime.c` 在 `main` 开头调用 `SetConsoleOutputCP(65001)` (Windows only)。

---

## 8. 模块系统 (v0.4.0 起)

### 8.1 导入语法

```jhyy
import mylib;        // 导入 mylib.jhyy
import utils::io;    // (预留) 嵌套模块
```

- `import` 必须在文件**顶部** (所有 `fn`/`struct` 声明之前)
- 模块路径相对于**主文件所在目录**
- 多文件编译: `jhyy compile main.jhyy lib_a.jhyy lib_b.jhyy -o output`

### 8.2 导入解析算法

```
visited = {}     // 已处理模块
in_progress = {} // 正在处理 (循环检测)

work_list = [main_file 中的所有 import]

while work_list:
    pop mod
    if mod in visited: continue
    if mod in in_progress: ERROR 循环依赖
    in_progress.add(mod)
    
    读取 mod.jhyy, parse, 检查其 import 声明
    把 mod.jhyy 的非 import 声明加入 merged_decls
    把 mod.jhyy 的 import 加入 work_list
    
    visited.add(mod)
    in_progress.remove(mod)
```

### 8.3 名称空间

**当前实现**: 所有模块共享同一全局命名空间。`import` 仅做**声明引入**，不引入命名空间前缀。
```jhyy
// main.jhyy
import mylib;
fn use_helper() -> i32 { helper(42) }  // 直接调用 mylib 中的 helper

// mylib.jhyy
fn helper(x: i32) -> i32 { x + 1 }
```

**限制**: 不同模块中同名函数会**冲突** (后定义覆盖前者)。模块系统 v2.0 (Phase 2) 将引入命名空间。

### 8.4 错误信息

循环 import 报错:
```
error: circular import: a.jhyy -> b.jhyy -> a.jhyy
```

---

## 9. 程序入口

### 9.1 启动流程

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
    SetConsoleOutputCP(65001);  // UTF-8 console
    return main_jhyy();
}
```

### 9.2 用户入口

```jhyy
fn main_jhyy() -> i32 {
    0   // 返回 0 表示成功
}
```

- 返回值类型必须是 `i32`
- 命令行参数: 当前版本不传递给 `main_jhyy`，未来通过 `os::args()` 获取
- 当前无 `main` 函数重载或 `#[start]` attribute

### 9.3 退出码

| 值 | 含义 |
|----|------|
| 0 | 成功 |
| 1-127 | 用户定义 (测试 assertion 失败等) |
| 128+N | 被信号 N 终止 (Unix 约定，Windows 行为不同) |
| 256+ | 高位被截断为 8 位 (bash 限制) — **Python/原生 API 不截断** |

---

## 10. QBE IL 映射速查

### 10.1 字面量

| JHYY 字面量 | QBE |
|------------|-----|
| `42` | `42` (i32) |
| `2147483647` | `2147483647` (i32) |
| `0xFF` | `255` (无前缀) |
| `3.14` (f32) | `s_3.14` |
| `2.71` (f64) | `d_2.71` |
| `"hello"` | `l $strN` (data 段) |
| `true` | `1` |
| `false` | `0` |

### 10.2 变量和分配

| 场景 | QBE |
|------|-----|
| `let x = 42` | `%tN =w copy 42` |
| `let mut x: i32 = 42` | `%slot =l alloc4 4`<br>`storew 42, %slot`<br>`%tN =w loadw %slot` |
| `let arr: [i32; 3] = [1, 2, 3]` | `%slot =l alloc4 12`<br>`storew 1, %slot`<br>`storew 2, %slot+4`<br>`storew 3, %slot+8` |
| `let p: Point = Point{x: 1, y: 2}` | `%slot =l alloc8 8`<br>`storew 1, %slot` (x)<br>`storew 2, %slot+4` (y) |

### 10.3 字符串

```qbe
data $str0 = { b "hello world", b 0 }
```

JHYY 字符串字面量在 QBE data 段中以 UTF-8 + NUL 终止符存储。

### 10.4 控制流

| 构造 | QBE 模式 |
|------|---------|
| `if c { A } else { B }` | `jnz %c, @then, @else` + phi |
| `while c { body }` | `@loop_hdr: jnz %c, @body, @loop_end` |
| `for i in s..e { body }` | 三块 (hdr/body/incr) + 范围检查 |
| `break` | `jmp @loop_end` |
| `continue` (while) | `jmp @loop_hdr` |
| `continue` (for) | `jmp @incr` |
| `return v` | `ret %v` (或 sret 模式下 `cg_copy_struct` + `ret`) |

### 10.5 内存操作

| 构造 | QBE |
|------|-----|
| `&x` (mutable) | `%tN =l copy %slot` |
| `&x` (immutable) | **未定义** (无栈地址) |
| `*p` (i32) | `%tN =w loadw %p` |
| `*p = v` (i32) | `storew %v, %p` |
| `arr[i]` (i32 元素) | `%idx =w mul %i, 4`<br>`%addr =l add %arr, %idx`<br>`%val =w loadw %addr` |
| `arr[i] = v` | `%idx =w mul %i, 4`<br>`%addr =l add %arr, %idx`<br>`storew %v, %addr` |
| `ptr->field` | `%addr =l add %ptr, field_offset`<br>`%val =w loadw %addr` |

---

## 11. 已知局限 (v1.0.0 锁定)

### 11.1 阻塞自举的关键问题 (Phase 2 必须解决)

| # | 问题 | 影响 | 状态 |
|---|------|------|------|
| ~~A1~~ | ~~结构体不能按值传递/返回~~ | ~~不能用 struct 做函数参数~~ | **v0.4.0 已修复** |
| ~~A2~~ | ~~切片 `[*]T` 无 codegen~~ | ~~不能使用 string/slice 类型~~ | **v0.6.0 sprint 6A 已修复**（按 struct pass-by-value sret 处理） |
| A3 | struct 跨 FFI 边界 | 不能调用 C 函数传 struct | P3 |
| ~~A4~~ | ~~名称修饰无模块前缀~~ | ~~多文件模块符号冲突~~ | **v0.6.0 sprint 6B 已修复**（`$mod__name` mangle + `Sym.module` 字段） |
| A5 | 浮点比较和某些运算不完整 | f32/f64 部分运算结果错误 | P3（v0.5 sprint 5A 修了大部分，NaN/Inf 极端行为仍未规约） |

### 11.2 暂不阻碍但需注意

| # | 问题 |
|---|------|
| B1 | 浮点算术: `+ - * /` 已实现, `%` (fmod) 未实现 |
| B2 | 浮点比较: 暂未完全类型化, 部分场景可能退化 |
| B3 | `&&` / `||` 短路求值 (v0.2.1 起) 已实现，但只支持标量 |
| B4 | for 循环变量类型感知 (v0.2.1 起) 已实现 |
| B5 | 无栈溢出保护/金丝雀 |
| B6 | 无线程模型/TLS 约定 |
| B7 | 无 DWARF 调试信息 |
| B8 | `printf` 变参在 JHYY 侧需逐参数列出 (不支持 `...`) |
| B9 | 无 RAII / 自动析构 |

### 11.3 ABI 兼容承诺

任何 Phase 1 后续 v0.5.x / v0.6.x 版本**不得**改变本文件锁定的内容。变更必须:
1. 升级 ABI 主版本号 (v1.0.0 → v1.1.0)
2. 在 `docs/changelog-vX.Y.Z.md` 记录
3. 提供迁移路径

---

## 12. 版本历史

| 版本 | 日期 | 主要变更 |
|------|------|---------|
| v0.0.1 | 2026-06-05 | 初稿，基于 v0.0.2 |
| v1.0.0 | 2026-06-17 | 锁定: struct pass-by-value, sret, 多文件, FFI 增强, break/continue, 浮点算术, void if |

---

## 附录 A: 与 C ABI 的兼容性

JHYY 函数**不**与 C ABI 100% 兼容:
- struct pass-by-value 使用 **JHYY 自有约定** (栈副本 + 逐字段复制), 与 Windows x64 ABI 不同
- 跨 FFI 调用 C 函数时，必须只使用标量/指针参数
- C 代码调用 JHYY 函数时，JHYY 函数必须遵循 C 可见的命名 (`$name` 去掉 `$` 后)

要从 C 调用 JHYY 函数:
```c
extern int main_jhyy(void);   // JHYY 导出符号 = main_jhyy (无 $ 前缀)
int result = main_jhyy();
```

## 附录 B: 调试技巧

1. **查看生成的 QBE IL**: `cat output.il` 或 `jhyy compile ... -o output && cat output.il`
2. **手动调用 QBE**: `qbe/qbe.exe -t amd64_win -o output.s output.il`
3. **查看汇编**: `cat output.s`
4. **最小化测试**: 从失败的 .jhyy 抽出最小复现到独立的 .jhyy 文件
5. **回归测试**: `python compiler/build/bin/regress.py` 跑全部 43 个集成测试（v0.6.0 验证 43/46 passed, 3 skipped 库文件）
