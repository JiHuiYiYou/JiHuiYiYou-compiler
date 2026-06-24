# JHYY v0.4.0 Changelog

## 版本目标

使语言具备编写复杂编译器的工程化能力 — 结构体按值传递、多文件协作。

---

## Sprint 4A: 结构体按值传递

### 新增功能

| 功能 | 描述 |
|------|------|
| struct 作为函数参数 (值传递) | 调用方分配栈拷贝，逐字段复制，传递指针给被调用方 |
| struct 作为返回值 (sret) | 调用方分配返回槽，隐式传递指针为第一参数，被调用方写入 |
| struct 赋值 `a = b` | 逐字段复制 (含嵌套 struct) |

### 实现细节

- **cg_copy_struct**: 新辅助函数，遍历 struct 字段，生成 load/store 指令对，递归处理嵌套 struct
- **ir_emit_call_void**: 新 IR 发射函数，用于 sret 调用 (无需返回值)
- **CGContext 扩展**: 新增 `sret_slot` 和 `has_sret` 字段
- **NODE_IDENT 修复**: struct 类型标识符直接返回地址而非 load 值
- **NODE_LET 修复**: 非 mutable struct 也使用栈分配
- **NODE_RETURN sret**: 复制到返回槽后 emit bare ret
- **cg_func**: sret 函数签名添加隐藏指针参数 `l %ret`

### 文件变更

| 文件 | 变更 |
|------|------|
| `compiler/src/codegen.c` | +150 行: cg_copy_struct, NODE_CALL/NODE_IDENT/NODE_LET/NODE_ASSIGN/NODE_RETURN/cg_func 修改 |
| `compiler/src/ir.c` | +15 行: ir_emit_call_void |
| `compiler/src/ir.h` | +1 行: ir_emit_call_void 声明 |

---

## Sprint 4B: 多文件编译

### 新增功能

| 功能 | 描述 |
|------|------|
| 传递性 import | A import B, B import C 完全支持 |
| 循环 import 检测 | 记录访问路径, 检测循环引用并报错 |
| 多文件 CLI | `jhyy compile a.jhyy b.jhyy -o output` |
| cmd_build 修复 | 增加 resolve_imports 调用 |

### 实现细节

- **resolve_one_import**: 递归解析单个 import 文件, 处理嵌套 import
- **resolve_imports**: 重构为调用 resolve_one_import, 收集并合并所有声明
- **访问列表持久化**: 使用 calloc 分配 visited 数组, 防止栈变量悬垂指针
- **声明顺序**: 导入的声明排在主模块声明之前, 确保 sema Pass 3 先设置导入函数的类型

### 文件变更

| 文件 | 变更 |
|------|------|
| `compiler/src/main.c` | +120 行: resolve_one_import, resolve_imports 重构, 多文件 CLI |

---

## Sprint 4C: FFI 增强

### 新增功能

| 功能 | 描述 |
|------|------|
| FFI 多参数调用验证 | 4 参数 `printf(fmt, a, b, c)` 测试通过 |
| 文件 I/O FFI 验证 | `fopen`/`fclose` 测试通过 |

### 新增测试

| 测试 | 预期 | 结果 |
|------|------|------|
| `ffi_multi.jhyy` | EXIT:42, stdout: "three numbers: 10 20 30" | ✅ |
| `ffi_file.jhyy` | EXIT:0, 文件创建成功 | ✅ |

---

## 集成测试结果

| 测试 | 预期 | 结果 |
|------|------|------|
| `hello.jhyy` | EXIT:42 | ✅ |
| `demo.jhyy` | EXIT:0 | ✅ |
| `struct.jhyy` | EXIT:30 | ✅ |
| `pointer.jhyy` | EXIT:100 | ✅ |
| `match.jhyy` | EXIT:20 | ✅ |
| `forloop.jhyy` | EXIT:10 | ✅ |
| `import_test.jhyy` | EXIT:72 | ✅ |
| `logical.jhyy` | EXIT:0 | ✅ |
| `return_type.jhyy` | EXIT:100 | ✅ |
| `dungeon_game.jhyy` | EXIT:0 | ✅ |
| `struct_val_pass.jhyy` | EXIT:35 | ✅ NEW |
| `struct_val_ret.jhyy` | EXIT:15 | ✅ NEW |
| `struct_val_assign.jhyy` | EXIT:30 | ✅ NEW |
| `multi_file/main.jhyy` | EXIT:60 | ✅ NEW |
| `ffi_multi.jhyy` | EXIT:42 | ✅ NEW |
| `ffi_file.jhyy` | EXIT:0 | ✅ NEW |

**16/16 测试全部通过**

---

## 已知限制 (延后至后续版本)

- 切片 `[*]T` 有类型定义但无 codegen (P2)
- 浮点算术运算 (P2, codegen 使用整数 opcode)
- struct FFI 传递 (C struct ABI 匹配)
- break/continue 支持
