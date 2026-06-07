# JHYY Changelog v0.3.0

> 发布日期: 2026-06-08
> 自 v0.2.1 以来的变更

---

## 核心实现: 定长数组 `[T; N]`

### Sprint 3A: 数组完整 codegen

#### 新增 AST 节点
- **`NODE_ARRAY_TYPE`**: 数组类型注解 `[T; N]`
  - Struct: `{ Node *elem_type; Node *count_expr; }`
- **`NODE_ARRAY_LIT`**: 数组字面量 `[1, 2, 3]`
  - Struct: `{ Node **elems; size_t nelems; }`

#### Parser
- `parse_type`: 修复 `[T; N]` 类型解析 → 创建 `NODE_ARRAY_TYPE` 节点
- `prefix_array_lit`: 新增 `[1, 2, 3]` 语法解析 (逗号分隔元素列表)
- `TOKEN_LBRACKET`: 注册 `prefix_array_lit` 作为前缀处理器

#### Sema
- `resolve_type_node`: 处理 `NODE_ARRAY_TYPE` → 调用 `type_array()`
- `infer_type`: 处理 `NODE_INDEX` → 返回数组元素类型
- `infer_type`: 处理 `NODE_ARRAY_LIT` → 推断元素公共类型 + 创建数组类型

#### Codegen
- **`NODE_INDEX`**: 基地址 + 索引 × sizeof(T) → QBE load/store
  - 编译期常量索引折叠为直接偏移计算
  - 运行时索引: `extsw` + `mul` + `add` 计算地址
- **`NODE_ARRAY_LIT`**: alloc 栈空间 + 逐元素 store
- **`arr[i] = val`**: NODE_ASSIGN 中处理 NODE_INDEX 目标 — 计算地址 + store
- **数组变量**: 全部使用栈分配 (不再用 SSA temp)
- **`NODE_LET` 双重分配修复**: 数组字面量初始化时不重复分配

### 支持的功能
- `let arr = [10, 20, 30];` — 数组字面量类型推断
- `let mut arr: [i32; 3] = [7, 8, 9];` — 带类型注解
- `arr[0]`, `arr[i]` — 下标读写
- `arr[i] = val` — 下标赋值
- 数组在函数参数/let 绑定/赋值等所有上下文正常工作

---

## Bug 修复

### Bug 1: Pratt 解析器运算符优先级 (P2)
- **问题**: `*p = *p - expr` 报 `type mismatch: *i32 vs i32`
- **根因**: `-`, `*`, `&` 作为双角色 token (前缀+中缀) 时全都注册为 `PREC_UNARY`，导致 `*p - 20` 被解析为 `*(p - 20)` 而非 `(*p) - 20`
- **修复**: 将中缀优先级改为正确值：
  - `TOKEN_MINUS`: `PREC_UNARY` → `PREC_TERM`
  - `TOKEN_STAR`: `PREC_UNARY` → `PREC_FACTOR`
  - `TOKEN_AMP`: `PREC_UNARY` → `PREC_BIT_AND`
- 前缀处理内部仍使用 `PREC_UNARY` 解析操作数，不受影响

### Bug 2: 嵌套 if/else if/else phi 块标签 (P2)
- **问题**: `if/else if/else` 链编译时 QBE 报错 `predecessors not matched in phi`
- **根因**: 外层 if 的 phi 引用 `@else_block` 作为前驱，但实际跳转到 merge 的块是内层 if 的 `@merge` 块
- **修复**: 在 else 分支末尾添加 trampoline 块 (`@ep`)，确保 phi 前驱始终是直接前驱

### Bug 3: if/else void 分支 phi 类型
- **问题**: (已由之前的 void 返回类型处理 + phi qbe_type 默认值修复解决)
- 无需额外修改

### Bug 4: 浮点字面量 codegen 硬编码 0.0 (P3)
- **问题**: 所有浮点字面量生成 `... copy 0.0`，忽略实际数值
- **修复**: 格式化为 QBE `d_`/`s_` 字面量:
  - 普通值: `d_3.14`, `s_1.5`
  - NaN: `d_nan`, `s_nan`
  - ±Inf: `d_+inf`, `d_-inf`
  - 使用 `%.17g` 确保 IEEE 754 双精度往返

---

## 附加修复

### `ir_emit_alloc` 对齐值
- **问题**: 非标准大小数组 (如 `[i32; 5]` = 20 bytes) 生成 `alloc20 20`，QBE 仅支持 4/8/16 对齐
- **修复**: 自动选择合适的对齐值 (≤4→4, ≤8→8, >8→16) 并向上取整大小

### `sema NODE_CALL` 参数类型推断
- **问题**: `arr[i]` 直接作为函数参数 (如 `printf("...", arr[0])`) 时 NODE_INDEX 的表达式类型未解析，导致 codegen 收到 NULL 类型→ 返回空 IRVal → QBE IL 中出现 NUL 字节
- **修复**: `NODE_CALL` 的 `infer_type` 递归推断所有参数类型

---

## 测试

### 集成测试: 13/13 全部通过

| 测试 | 验证内容 | 结果 |
|------|---------|------|
| hello | 基础流水线 | EXIT:42 ✅ |
| demo | 全面特性 | EXIT:0 ✅ |
| pointer | 指针操作 | EXIT:100 ✅ |
| struct | 结构体 | EXIT:30 ✅ |
| match | 模式匹配 | EXIT:20 ✅ |
| forloop | for 循环 | EXIT:10 ✅ |
| return_type | return 类型检查 | EXIT:100 ✅ |
| logical | &&/\|\| 短路 | 5/5 通过 ✅ |
| import_test | 模块导入 | EXIT:72 ✅ |
| dungeon_game | 地牢游戏端到端 | 编译通过 ✅ |
| array_test | 数组字面量/下标/类型注解 | 6/6 通过 ✅ |
| bug1_ptr_bin | `*p = *p - expr` 修复验证 | val=30 ✅ |
| bug2_if_phi | 嵌套 if/else phi 修复验证 | result=300 ✅ |
| float_test | 浮点字面量正确生成 | 编译通过 ✅ |

### 新增测试文件
- `array_test.jhyy` — 数组专项测试 (字面量/下标读写/类型注解/赋值)
- `bug1_ptr_bin.jhyy` — Bug 1 修复验证
- `bug2_if_phi.jhyy` — Bug 2 修复验证
- `float_test.jhyy` — Bug 4 修复验证

---

## 统计

- 编译器 C 源码: ~3700 行
- AST 节点类型: 37 (新增 2)
- 修改文件: `ast.h`, `ast.c`, `parser.c`, `sema.c`, `codegen.c`, `ir.c`
- 集成测试: 14 个 .jhyy 程序
