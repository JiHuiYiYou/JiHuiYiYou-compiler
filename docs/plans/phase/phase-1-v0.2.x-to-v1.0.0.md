# JHYY 全版本路线图 (v0.2.x → v1.0.0)

## Context

基于两份自举准备文档（现均已删除） (`自举准备大纲.md`、`自举注意事项.md`) 和当前语言能力现状制定。

**核心原则**:
1. 严格按依赖顺序推进，不做跳跃式开发
2. 每个版本有明确的"完成标准"和回归测试
3. v0.5.0 是自举前最后的"质量门禁"
4. 自举采用三代验证法（Stage 0/1/2）

---

## 当前状态快照 (v0.2.1)

### 已具备
| 能力 | 状态 |
|------|------|
| 基本类型 (i8-u64, f32/f64, bool) | ✅ |
| 指针 `*T`、取地址 `&`、解引用 `*` | ✅ |
| 控制流 (if/else, while, for, return) | ✅ |
| 结构体定义/字面量/字段访问/指针字段访问 `->` | ✅ |
| 枚举定义/变体构造/match 表达式 | ✅ |
| 函数 (参数/返回/递归/类型检查) | ✅ |
| FFI (extern fn) — puts/printf/scanf | ✅ |
| 短路求值 `&&` `||` | ✅ |
| 类型感知 for 循环 | ✅ |
| 统一 enum 内存布局 | ✅ |
| UTF-8 控制台 I/O | ✅ |
| 单级 import | ✅ |
| LCG 伪随机数 | ✅ |

### 已知限制
| 限制 | 严重度 |
|------|--------|
| 定长数组 `[T; N]` 有类型无 codegen | 阻塞自举 |
| 结构体不支持按值传递/返回 | 阻塞自举 |
| 仅单级 import、无多文件编译 | 阻塞自举 |
| 浮点字面量 codegen 硬编码 0.0 | 低 |
| 无 break/continue | 中 |
| `*ptr = *ptr - expr` 一行写法 sema bug | 中 |
| 嵌套 if/else if/else phi 块标签 bug | 中 |
| if/else void 分支 phi 填充类型错误 | 中 |

---

## v0.2.x — 地牢小游戏与 bug 修复 (当前)

### 目标
完成地牢文字 Rogue 游戏，修复过程中暴露的编译器 bug。

### 已完成
- [x] LCG 随机数生成 (`randRange`)
- [x] `scanf` 控制台输入
- [x] 地牢游戏 (`dungeon_game.jhyy`): 5 种房间、3 种怪物、战斗系统
- [x] 修复: void 函数 QBE 输出 NUL 字节 (`codegen.c` export function 头)
- [x] 修复: `ir_emit_call` void 返回 NUL 字节
- [x] 修复: `ir_emit_phi` void 类型 NUL 字节

### 待完成
- [ ] 清理 `compiler/tests/examples/_test_*.jhyy` (15 个临时文件)
- [ ] 清理 `compiler/build/_*.txt` (历史调试日志)
- [ ] 将地牢游戏新发现的 3 个 codegen bug 列入正式修复清单

---

## v0.3.0 — 数据存储与管理能力

### 目标
使语言具备存储和管理集合数据的能力——这是编写编译器的物理基础。编译器需要数组存储 Token 流、AST 节点、符号表桶。

### Sprint 3A: 定长数组 `[T; N]` 完整实现

**涉及文件**: `types.c`, `sema.c`, `codegen.c`, `parser.c`

#### 3A.1 数组类型解析与语义
- 语法: `let arr: [i32; 10];`（类型标注）或 `let arr = [1, 2, 3];`（字面量推断）
- sema 支持 `KIND_ARRAY` 的 sizeof/alignof 计算
- 类型推断从数组字面量推导长度和元素类型

#### 3A.2 数组下标访问 `arr[i]`
- 语法: `arr[index]`
- 新增 AST 节点: `NODE_INDEX`（已定义？需确认）
- Codegen: 基地址 + 索引 × sizeof(T)，生成 QBE load/store

```
let x = arr[i];   →   %addr =l add %arr_base, %offset
                       %x =w loadw %addr
arr[i] = val;     →   %addr =l add %arr_base, %offset
                       storew %val, %addr
```

- 可选: 边界检查（debug 模式），编译期常量索引可直接计算偏移

#### 3A.3 数组字面量
- 语法: `let arr = [1, 2, 3, 4, 5];`
- 类型推断为 `[i32; 5]`
- Codegen: alloc 栈空间，逐个元素 store

#### 3A.4 数组作为函数参数
- 语法: `fn process(data: [i32; 100]) { ... }`
- 传递方式: 栈拷贝（整个数组复制到参数栈空间）

### Sprint 3B: 字符串字面量稳定化

- 确保字符串位于只读段（QBE data section → `.rodata`）
- 转义序列完整体验: `\n \t \r \0 \\ \" \xHH`
- Unicode 支持验证 (中文、emoji)

### Sprint 3C: 已知 Bug 修复

- [ ] `*ptr = *ptr - expr` sema 类型推断 bug
- [ ] 嵌套 if/else if/else phi 前驱块标签错误
- [ ] if/else void 分支 phi 填充 `%t0` 类型错误
- [ ] 临时文件清理

### v0.3.0 验收标准

| # | 标准 |
|---|------|
| 1 | `let arr: [i32; 100];` 编译通过，可以读写元素 |
| 2 | 数组字面量 `[1,2,3]` 正常工作 |
| 3 | 数组作为函数参数传递 |
| 4 | gcc 编译编译器零警告 |
| 5 | 所有现有测试通过 (回归) |
| 6 | 新增数组专项测试 ≥ 3 个 |
| 7 | 地牢游戏可正常编译运行 |

---

## v0.4.0 — 结构化编程能力

### 目标
使语言具备编写复杂编译器的工程化能力——结构体按值传递、多文件协作。

### Sprint 4A: 结构体按值传递

**涉及文件**: `sema.c`, `codegen.c`, `types.c`

#### 4A.1 结构体作为函数参数（值传递）

```rust
type Point = struct { x: i32, y: i32 };

fn distance(p: Point) -> i32 { ... }
// 调用: let d = distance(my_point);
// 行为: 整个 Point (8 字节) 复制到参数栈空间
```

- **实现要点**:
  - 调用方: 分配栈空间，逐字段 store（按偏移）
  - 被调用方: 参数映射为栈指针，字段访问通过偏移 load
  - QBE: 结构体按值传递在 Microsoft x64 ABI 中，≤8 字节用寄存器、>8 字节用隐式指针
  - Phase 1 策略: **全部栈拷贝**（调用方 alloc + 逐字段 store，传指针）

#### 4A.2 结构体作为返回值

```rust
fn make_point(x: i32, y: i32) -> Point {
    Point { x: x, y: y }
}
```

- **实现要点**:
  - 调用方在调用前分配返回槽栈空间
  - 隐式传递返回槽指针给被调用方
  - 被调用方将结果写入返回槽

#### 4A.3 结构体赋值

```rust
let mut a = Point { x: 1, y: 2 };
let b = Point { x: 3, y: 4 };
a = b;   // 逐字段复制（memcpy 语义）
```

- Codegen: 按 type_size 计算，逐 word/long store

### Sprint 4B: 多文件编译机制

#### 4B.1 增强 import 解析
- 支持二级 import（A import B，B import C）
- 循环 import 检测（记录已加载模块路径，拒绝重复加载）
- import 错误信息包含文件名和行号

#### 4B.2 多文件命令行输入

```bash
jhyy compile src/main.jhyy src/lexer.jhyy src/parser.jhyy -o jhyy_self
```

- CLI 接受多个输入文件
- 按参数顺序解析、合并 AST
- 符号跨文件可见（同一全局作用域）

#### 4B.3 模块路径解析
- 当前目录查找 `./module.jhyy`
- 标准库目录查找（`./lib/` 或环境变量 `JHYY_PATH`）

### Sprint 4C: FFI 能力增强

- 支持多参数 FFI 调用（≥3 个参数）
- 验证 `extern fn fprintf(file: *u8, fmt: *u8, val: i32) -> i32;`
- 验证常用 C 标准库调用: `fopen`, `fclose`, `fread`, `fwrite`
- 新增 FFI 测试用例

### v0.4.0 验收标准

| # | 标准 |
|---|------|
| 1 | 结构体按值传递给函数，值正确 |
| 2 | 函数返回结构体，值正确 |
| 3 | 结构体赋值 `a = b`，值正确 |
| 4 | 二级 import 正常工作 |
| 5 | 多文件编译生成单一可执行文件 |
| 6 | FFI ≥3 参数调用正常 |
| 7 | 所有现有测试通过 |
| 8 | 编译器规模测试: 编译一个 10 文件、500+ 行的 JHYY 程序 |

---

## v0.5.0 — 自举前质量门禁

### 目标
修复所有已知 bug，完成 ABI 手册，制作 Claude Code MCP 服务——为自举做最后的品质保障。

### Sprint 5A: 全部 Bug 修复

#### 扫描范围
1. CLAUDE.md 中登记的已知 bug
2. 地牢游戏中暴露的 codegen bug
3. 单元测试和集成测试覆盖不到的边界条件

#### 待修清单
- [ ] `*ptr = *ptr - expr` sema 类型推断
- [ ] 嵌套 if/else if/else phi 块标签
- [ ] if/else void 分支 phi 类型
- [ ] 浮点字面量 codegen（至少支持 f32/f64 基本运算）
- [ ] break/continue 支持（或确认自举不需要）
- [ ] 大整数溢出行为明确定义
- [ ] 空指针解引用行为

#### 修复流程
1. 每个 bug → 独立 commit
2. 每个 bug → 至少 1 个回归测试
3. 修复全部后运行完整测试套件

### Sprint 5B: ABI 白皮书 v1.0

**输出文件**: `docs/abis/jhyy-abi-v1.0.0.md`

**内容要求**:
1. 全部类型布局 (primitive/pointer/array/struct/enum/slice)
2. sizeof/alignof 完全定义
3. 函数调用约定 (参数传递、返回值、struct passing)
4. QBE IL 指令映射速查表（完整版）
5. FFI 边界规则
6. 名称修饰方案
7. 内存模型 (栈/静态数据/Arena)
8. 版本兼容性承诺
9. Windows x64 PE 特定行为
10. 与 C ABI 的互操作细节

### Sprint 5C: Claude Code MCP 服务

**目标**: 让 Claude Code 能规范、准确地编写 `.jhyy` 代码。

**技术选型**: Python FastMCP（用户指定）

#### 5C.1 MCP 服务功能

| 工具 | 功能 |
|------|------|
| `jhyy_compile` | 编译 .jhyy 文件，返回编译结果和错误信息 |
| `jhyy_run` | 编译并运行，返回 stdout/stderr 和退出码 |
| `jhyy_check` | 仅做语法+语义检查（不生成代码），快速验证 |
| `jhyy_format` | 查看/验证语法正确性 |
| `jhyy_lang_ref` | 查询语言规范（关键字、类型、语法规则） |
| `jhyy_abi_info` | 查询 ABI 信息（类型大小、布局、调用约定） |

#### 5C.2 MCP 资源

| 资源 | 内容 |
|------|------|
| `jhyy://spec/v0.5.0` | 语言规范全文 |
| `jhyy://abi/v1.0.0` | ABI 白皮书全文 |
| `jhyy://stdlib` | 标准库文档 |
| `jhyy://examples/` | 示例代码目录 |

#### 5C.3 实现要点

```python
# 核心: 调用 jhyy.exe，解析输出
# 使用 subprocess 调用编译器
# 结构化错误输出 (JSON)
# 提供 MCP tool 给 Claude 调用
```

- 编译/运行工具自动处理路径和编码
- 错误信息结构化解析（文件名、行号、列号、消息）
- 集成到 Claude Code 的 MCP 配置

### Sprint 5D: 全面测试

#### 5D.1 回归测试
- 全部现有单元测试 (282)
- 全部集成测试 (12+)
- 地牢游戏端到端

#### 5D.2 新增专项测试
| 测试 | 内容 |
|------|------|
| `array.jhyy` | 数组声明/读写/字面量/传参 |
| `struct_val.jhyy` | 结构体按值传递/返回/赋值 |
| `multi_file/` | 多文件编译测试套件 |
| `ffi_multi.jhyy` | 多参数 FFI |

#### 5D.3 压力测试
- 编译一个包含所有语言特性的综合测试（≥300 行）
- 递归深度测试（Fibonacci 30+）
- 大数组测试 ([i32; 10000])

### v0.5.0 验收标准

| # | 标准 |
|---|------|
| 1 | 零已知 bug |
| 2 | 全部测试通过 |
| 3 | ABI 白皮书 v1.0 完成 |
| 4 | MCP 服务可正常调用 |
| 5 | Claude Code 可通过 MCP 编译和运行 .jhyy |
| 6 | 压力测试通过 |

---

## v1.0.0 — 自举

### 目标
用 JHYY 编写 JHYY 编译器，并验证自举闭环。

### 移植策略: 自底向上，依赖优先

#### 阶段 1: 基础设施层
**目录**: `compiler/src0/`

1. **`arena.jhyy`** — Bump Allocator
   - 从 `runtime.c` 迁移 `arena_alloc` / `arena_reset` / `arena_destroy`
   - 通过 FFI 调用 `malloc`/`free` 获取原始内存
   - 验证: 1000 次分配+reset 循环

2. **`util.jhyy`** — 工具函数
   - 字符串处理: `str_eq`, `str_len`, `str_copy`
   - 哈希表: FNV-1a 64-bit, 开放寻址+线性探测
   - 动态数组: push/pop/grow
   - 确定性排序（关键: 保证生成代码顺序一致）

#### 阶段 2: 核心数据结构
3. **`ast.jhyy`** — AST 节点定义 (tagged union, 35+ variants)
4. **`types.jhyy`** — 类型系统
5. **`symtab.jhyy`** — 符号表

#### 阶段 3: 编译器前端
6. **`lexer.jhyy`** — 词法分析
7. **`parser.jhyy`** — 递归下降 + Pratt 表达式解析
8. **`sema.jhyy`** — 语义分析（3 遍遍历）

#### 阶段 4: 编译器后端
9. **`ir.jhyy`** — IR 构建器（QBE IL 文本生成）
10. **`codegen.jhyy`** — AST → QBE IL 发射
11. **`main.jhyy`** — CLI 驱动（调用 QBE + GCC）

### 代码转换规范

| C 原语 | JHYY 等价 |
|--------|----------|
| `malloc/free` | Arena allocator |
| `NULL` 检查 | `Option` 枚举或显式 i32 错误码 |
| `switch-case` | `match` 表达式 |
| `struct Node*` (指针传递) | struct 按值传递（栈拷贝） |
| `#include` | `import` 模块 |
| `printf` 调试 | `extern fn printf` FFI |

### 验证方案: 三代验证法

```
Stage 0:  C 编译器 (jhyy.exe)
            ↓ 编译 src0/*.jhyy
Stage 1:  jhyy_0.exe (第一代 JHYY 编译器)
            ↓ 编译 src0/*.jhyy  
Stage 2:  jhyy_1.exe (第二代 JHYY 编译器)
            ↓ 编译 src0/*.jhyy
Stage 3:  jhyy_2.exe (第三代 JHYY 编译器)

验证: diff(jhyy_1.il, jhyy_2.il) → 完全一致 = 自举成功
      或: sha256(jhyy_1.exe) == sha256(jhyy_2.exe)
```

### 风险控制

| 风险 | 缓解措施 |
|------|---------|
| 哈希迭代顺序不确定 → 生成代码不一致 | 符号表遍历前排序 |
| 未初始化变量 → 幽灵 bug | 代码审查 + 显式初始化所有变量 |
| FFI 不稳定 → 无法读写文件 | v0.4.0 充分验证 FFI |
| 编译器自身 bug → 编译出错误的编译器 | 三代验证 + 回归测试 |

### v1.0.0 验收标准

| # | 标准 |
|---|------|
| 1 | `jhyy_0` 能成功编译 `src0/` 生成 `jhyy_1` |
| 2 | `jhyy_1` 能成功编译 `src0/` 生成 `jhyy_2` |
| 3 | `jhyy_1.exe` 与 `jhyy_2.exe` 完全一致（字节级） |
| 4 | 全部原有集成测试通过（用自举编译器编译） |
| 5 | 编译速度：完整编译 ≤ 30 秒（参考 C 版 0.5 秒） |

---

## 版本依赖关系图

```
v0.2.1 (当前) ─── 地牢游戏 + 基础组件
    │
    ▼
v0.3.0 ─── 数组 codegen ──────────────┐
    │                                   │
    ▼                                   │
v0.4.0 ─── struct 按值传递 + 多文件 ──┐│
    │                                  ││
    ▼                                  ▼▼
v0.5.0 ─── 全 bug 修复 + ABI + MCP ──→ 质量门禁
    │
    ▼
v1.0.0 ─── 自举闭环
```

## 执行原则

1. **禁止跳跃**: 必须按 v0.3 → v0.4 → v0.5 → v1.0 顺序，前一个版本是后一个版本的硬依赖
2. **每个版本完成后再开下一个**: 避免半成品累积
3. **持续回归**: 每次修改后运行全部现有测试
4. **最小化改动**: 不重构、不加"可能有用"的功能
5. **文档同步**: 代码改动后立即更新 logs文件夹的开发文件、 CLAUDE.md 和 lang-spec
