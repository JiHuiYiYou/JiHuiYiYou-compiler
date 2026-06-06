# JHYY Changelog v0.2.1

> 发布日期: 2026-06-07
> 自 v0.1.0 (Phase 1 初始版本) 以来的变更

---

## Bug 修复

### P0 (致命)
- **P0-A**: symtab 重写 — 从链表哈希改为开放寻址 + 线性探测 (64-bit FNV-1a, 负载因子 0.75)
- **P0-B**: sub-word 类型 (i8/u8/i16/u16) load/store 使用正确宽度指令 (loadsb/loadub/storeb 等)
- **P0-C**: 比较指令类型感知 — 根据 signed/unsigned 和 word/long 选择正确的 QBE 比较指令
- **P0-D**: 64 位移位使用正确宽度 (l 而非 w)

### P1 (功能)
- **P1-A**: Windows `jhyy run` 路径修复 — `path_to_win()` 应用于 compile() 中所有路径
- **P1-B**: return 语句类型传播修复 — `NODE_RETURN` 不再总是设置 void 类型，函数体类型检查正确
- **P1-B 补充**: 函数体已有显式 return 时，codegen 不再重复 emit ret 指令

### P2 (语义)
- **P2-A**: `&&` / `||` 短路求值 — 使用分支跳转 + phi 汇合替代逐位 and/or
- **P2-B**: enum payload_offset 一致性 — 存储在 Type.enum_type 中，sema 计算，codegen 直接使用
- **P2-C**: for 循环变量类型感知 — 使用 type_size() 和 qbe_type_of() 替代硬编码 i32

---

## 新特性

### 控制台输出
- **UTF-8 支持**: runtime.c 添加 `SetConsoleOutputCP(65001)`，中文输出不再乱码
- **printf 支持**: 通过 `extern fn printf(fmt: *u8, val: i32) -> i32` 输出格式化文本和数字
- **字符串转义序列**: 完整支持 `\n`, `\t`, `\r`, `\0`, `\\`, `\"`, `\xHH`

### 语言特性完善
- 短路逻辑运算符 `&&` / `||`
- for 循环变量支持任意整数类型 (u8, i64 等)
- enum 变体在含不同对齐 payload 时内存布局一致
- 函数体 `return expr;` 类型正确推断

---

## 测试

### 单元测试: 282/282 全部通过
- test_lexer: 153/153 ✅
- test_sprint1b: 50/50 ✅
- test_parser: 58/58 ✅
- test_sema: 21/21 ✅

### 集成测试: 12/12 全部通过
| 测试 | 验证内容 | 结果 |
|------|---------|------|
| hello | 基础流水线 | EXIT:42 ✅ |
| demo | 全面特性 | EXIT:0 ✅ |
| pointer | 指针操作 | EXIT:100 ✅ |
| struct | 结构体 | EXIT:30 ✅ |
| match | 模式匹配 | EXIT:20 ✅ |
| forloop | for 循环 | EXIT:10 ✅ |
| helloworld | 控制台输出 | Hello, world! ✅ |
| import_test | 模块导入 | EXIT:72 ✅ |
| print_num | printf 数字 | 计算结果: 42 ✅ |
| chinese | UTF-8 中文 | 你好，世界！ ✅ |
| return_type | return 类型检查 | EXIT:100 ✅ |
| logical | &&/\|\| 短路 | 5/5 通过 ✅ |

---

## 已知问题 (延后)

| # | 描述 |
|---|------|
| P3 | 切片 `[*]T` 和定长数组 `[T; N]` 有类型定义但无 codegen |
| P3 | 浮点字面量 codegen 硬编码为 0.0 |
| P3 | 临时调试文件 `_test_*.jhyy` (15 个) 待清理 |

---

## 统计

- 编译器 C 源码: ~3400 行 (10 个 .c + 10 个 .h)
- 运行时: ~45 行
- 单元测试: ~300 行 (4 个测试文件)
- 集成测试: 12 个 .jhyy 程序
