# 编译器架构

> 编译器**只有一份实现**：`compiler/src0/*.jhyy`（30 个模块，约 36.5K 行）。
> `compiler/src/*.c`（C 端）已于 v4.0.21 删除 —— 仓里不存在「双实现 parity」这回事。
>
> 语言语义 ⇒ [`docs/abis/jhyy-lang-spec-v4.0.0.md`](../abis/jhyy-lang-spec-v4.0.0.md)；
> 类型布局与调用约定 ⇒ [`docs/abis/jhyy-abi-v4.0.0.md`](../abis/jhyy-abi-v4.0.0.md)。
> 本文件只讲**编译器自己**怎么组织的。

---

## 流水线

```
.jhyy 源码
  ↓  lexer.jhyy            字节流 → Token 流
  ↓  parser.jhyy           Token → AST
  ↓  sema.jhyy             AST → 标注 AST（类型检查 / 符号解析 / 常量折叠）
  ↓  codegen.jhyy          标注 AST → IL 文本（QBE 风格），**累积在内存 StringBuilder 里**
  ↓  codegen_amd64_inmem.jhyy
                           IL 文本 → lex_il → parse_and_emit → peephole → .s
  ↓  gcc (as + ld)         .s → .exe (PE/COFF) / ELF
```

**没有 QBE 进程**：QBE 工具链在 v4.0.0 完全移除。前端仍发「QBE 风格的 IL 文本」，
但那是**自研后端的私有中间表示**，不落盘、不 spawn 外部二进制。

> ⚠️ `JHY_WRITE_IL=1` 会让 `.il` 落盘 —— 但它**还会换编译路径** ⇒ 要做「改动前后是否
> 漂移」的对拍就比 `.s`，别拿它产出的 `.il` 比。

---

## 源文件清单

### 前端

| 文件 | 行数 | 职责 |
|---|---:|---|
| `lexer.jhyy` | 954 | 字节流 → Token 流 |
| `parser.jhyy` | 4117 | Token → AST；**single-pass，不支持 forward reference** |
| `ast.jhyy` | 1685 | 节点定义 + arena 分配 |
| `sema.jhyy` | 3528 | 类型检查、符号解析、常量折叠 |
| `types.jhyy` | 550 | 类型表示 + `type_size` / `type_align` |
| `symtab.jhyy` | 427 | 符号表（开放寻址 + 线性探测，64-bit FNV-1a） |
| `mono.jhyy` | 1451 | 泛型单态化 |
| `ir.jhyy` | 960 | IR 构造 + QBE 宽度字母映射 |
| `ffi.jhyy` | 71 | extern 声明处理 |
| `arena.jhyy` | 161 | arena 分配器 |
| `util.jhyy` | 374 | 通用工具 |
| `target_dispatch.jhyy` | 186 | `--target=` 分发（4 个三元组） |

### 后端（自研 amd64）

| 文件 | 行数 | 职责 |
|---|---:|---|
| `codegen.jhyy` | 5918 | AST → IL 文本（前端到中间表示的主干） |
| `codegen_amd64.jhyy` | 515 | 后端编排（in-mem / file-path 两条入口） |
| `codegen_amd64_inmem.jhyy` | 183 | 内存内 7 步编排：`lex_il` → `regalloc_clear_global` → `parse_and_emit` → `peephole_fold_with_len` → 写 `.s` |
| `codegen_amd64_lexer.jhyy` | 2266 | IL 文本 → `ILToken[]` |
| `codegen_amd64_emit_call.jhyy` | 2768 | 调用 / 实参 / 返回值 / volatile |
| `codegen_amd64_emit_ctrl.jhyy` | 841 | 序言 / 尾声 / 跳转 / 帧尺寸 |
| `codegen_amd64_emit_mem.jhyy` | 822 | 访存 / load / store / alloc |
| `codegen_amd64_emit_sse.jhyy` | 400 | 浮点发射 |
| `codegen_amd64_state.jhyy` | 2549 | 发射状态机（temp 表 / 槽位 / 帧） |
| `codegen_amd64_peephole.jhyy` | 797 | peephole 折叠（**4096 字节上限**是已知限制） |
| `codegen_amd64_regalloc.jhyy` | 972 | XMM 寄存器分配（**已实现但未接** —— `regalloc_init` / `regalloc_run` 被注释掉） |
| `codegen_amd64_rcache.jhyy` | 670 | **v4.4.0 阶段一**：通用寄存器缓存（位置映射 + 前瞻窗口）—— **已接进调度，但默认关** ⇒ 产物逐字节不变 |
| `codegen_amd64_xmm_argalloc.jhyy` | 267 | XMM 实参分配 |

### ABI

| 文件 | 行数 | 职责 |
|---|---:|---|
| `abi_amd64_win.jhyy` | 313 | Windows x64 调用约定 |
| `abi_amd64_win_freestanding.jhyy` | 93 | UEFI / 裸机 |
| `abi_amd64_sysv.jhyy` | 584 | SysV ABI（8-class §A.4 分类 + sret helper） |
| `abi_amd64_sysv_freestanding.jhyy` | 88 | SysV freestanding |

### 其它

| 文件 | 行数 | 职责 |
|---|---:|---|
| `main.jhyy` | 2054 | CLI 入口（`compile` / `build` / `run` / `dump`） |
| `codegen_amd64_peephole.jhyy` | 797 | （见上） |
| `std/*.jhyy` | 8 个模块 | `mem` `fmt` `io` `math` `string` `vec` `os` `arena` |

---

## 关键设计细节

### AST 节点

- 所有节点是 `Node` struct + variant data（紧跟 Node 在 arena 中分配）
- `ACCESSOR` 宏模式：`node_xxx_data(Node*)` 返回 variant data 指针
- 构造函数命名：`ast_new_xxx(Arena*, SourceLoc, ...)`
- 共 **57 种 `NodeKind`**（`0..56`），定义在 `compiler/src0/ast.jhyy`
  （常量函数 `NODE_xxx() -> i32`）

### 类型系统

```
KIND_PRIMITIVE   i8/u8/i16/u16/i32/u32/i64/u64/f32/f64/bool
KIND_POINTER     *T
KIND_SLICE       [*]T
KIND_ARRAY       [T; N]
KIND_STRUCT      struct { ... }
KIND_ENUM        enum { ... }
KIND_CAP         Cap<T>       (8 字节)
KIND_PHANTOM     PhantomData<T> (0 字节)
KIND_REF         &T / &mut T
KIND_FUNC        (T1, T2) -> R
KIND_ALIAS       type X = ...
KIND_VOID        ()
```

IR 宽度字母（`data_qt_of`）：`b`(i8/u8/bool) · `h`(i16/u16) · `w`(i32/u32) ·
`l`(i64/u64/指针) · `s`(f32) · `d`(f64)。

### 类型推断规则

- **参数必须标注类型**
- 局部变量自动推断（从 init 表达式）
- 函数返回类型：标注优先，标注为 `()` 时从函数体推断

### 符号表

- 开放寻址 + 线性探测，64-bit FNV-1a hash
- 2 的幂大小，负载因子 0.75 自动扩容
- `Sym.module`（NULL = main）→ 用于 `$mod__name` mangle
- `Sym.is_extern` → FFI 声明，emit 时不 mangle

### 作用域管理

- Parser 和 Sema 各有独立的作用域链
- Parser：`parse_func` push → `parse_block` push → … → pop
- Sema：`check_func_decl` push → `infer_type(block)` → … → pop
- Sema 的 `nlocals` **不会**在 pop 时自动清理 ⇒ 需在 `check_func_decl` 入口手动置零
- **每个 match arm 是独立作用域**（W-151 修的：arm 的模式绑定是**新绑定**，会遮住外层同名变量）

---

## ABI 关键决策（Windows x64）

1. **struct 按值传参** —— 调用方分配栈拷贝，逐字段复制；大于寄存器宽度的字段走内存
2. **struct 返回值走 sret** —— 调用方分配返回槽，隐式传递指针为第一个参数；被调用方写完 `ret`
3. **slice 布局** —— `[*]T` = `{ptr: *T, len: i64}`，共 16 字节
4. **模块命名 mangle** —— 跨模块函数 emit 成 `$mod__name`；`extern fn` 不 mangle
5. **实参寄存器** —— MS x64 的整数与浮点实参**共用一个位置计数器**（RCX/RDX/R8/R9 ‖ XMM0-3）

完整 ABI 锁定在 [`docs/abis/jhyy-abi-v4.0.0.md`](../abis/jhyy-abi-v4.0.0.md)。

---

## 寄存器分配：两个模块，别搞混

| 模块 | 状态 | 说明 |
|---|---|---|
| `codegen_amd64_regalloc.jhyy` | **已实现但未接** | XMM 专用分配器；`regalloc_init` / `regalloc_run` 在 `codegen_amd64.jhyy` 里被注释掉 |
| `codegen_amd64_rcache.jhyy` | **已接，默认关** | v4.4.0 阶段一：通用寄存器缓存（位置映射 + 前瞻窗口）；默认关 ⇒ **产物逐字节不变** |

⇒ 「后端把每个 SSA temp 物化成栈槽」这件事的解药是 **rcache**（v4.4.0 阶段二 =
emit 层消费寄存器），不是那个被注释掉的 XMM 分配器。

对拍工具：`scripts/dev/regalloc_reference.py` —— **独立写的第二套实现**，
用来验证主实现（合格候选 / 池满计数逐项相同）。

---

## 自举机制

`compiler/build/bin/jhyy.exe` 是 **git 跟踪**的产物（fresh clone 里就有），
它**自己**编 `compiler/src0/main.jhyy`。`make` 的闭环门比的是**跨代 `.s` 逐字节相同**
（迭代到不动点），而不是 `.il`。

⇒ 改 `compiler/src0/*.jhyy` 的代价见
[`CONTRIBUTING.md`](../../CONTRIBUTING.md) § 工作规约「jhyy 编译器本身的特殊规则」。

---

## 相关

- 构建 / 门 / 工具链 ⇒ [`docs/internal/build.md`](build.md)
- 事实（回归数 / 排期）⇒ [`docs/FACTS.md`](../FACTS.md)
- 台账 ⇒ [`docs/workarounds.md`](../workarounds.md)
