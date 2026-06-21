# 测试

> 集成测试清单 + 运行方法。详细每条 .jhyy 的预期值见 `compiler/tests/examples/`。

## 集成测试位置

`compiler/tests/examples/*.jhyy`（主目录 + 子目录 `multi_file/` / `namespace/` / `arena_test/`）。

回归脚本：`python compiler/build/bin/regress.py`，自动跑所有有 `main_jhyy` 的 .jhyy。

---

## 经典测试（v0.0.1–v0.2.1）

| 测试 | 预期 | 验证内容 |
|------|------|---------|
| `hello.jhyy` | EXIT:42 | 基础流水线 |
| `demo.jhyy` | EXIT:0 | 全部 v0.0.1 特性 |
| `pointer.jhyy` | EXIT:100 | `&x`, `*p = val` |
| `struct.jhyy` | EXIT:30 | struct 定义+字面量+字段访问 |
| `match.jhyy` | EXIT:20 | match 字面量+通配符 |
| `forloop.jhyy` | EXIT:10 | for 循环 (0+0+1+2+3+4) |
| `helloworld.jhyy` | stdout: "Hello, world!" | 控制台输出 |
| `chinese.jhyy` | stdout: "你好，世界！" | UTF-8 中文输出 |
| `print_num.jhyy` | stdout: "计算结果: 42" | printf 数字输出 |
| `return_type.jhyy` | EXIT:100 | return 类型检查 + printf |
| `logical.jhyy` | EXIT:0 | && / \|\| 短路求值 |
| `import_test.jhyy` | EXIT:72 | import 模块系统 |
| `dungeon_game.jhyy` | EXIT:0 | 综合 demo |

## v0.3 专项（数组 + bug 修复）

- `array_test.jhyy` — `[T; N]` 字面量/下标/赋值
- `bug1_ptr_bin.jhyy` — Bug 1 回归
- `bug2_if_phi.jhyy` — Bug 2 回归
- `bug3_void_if.jhyy` / `bug3_void_exact.jhyy` — Bug 3 回归
- `float_test.jhyy` — 浮点字面量

## v0.4 专项（struct pass-by-value + 多文件 + FFI）

- `struct_val_pass.jhyy` — struct 作为函数参数
- `struct_val_ret.jhyy` — 函数返回 struct
- `struct_val_assign.jhyy` — struct 赋值
- `multi_file/main.jhyy` + `lib_a.jhyy` + `lib_b.jhyy` + `lib_c.jhyy` — 传递性 import
- `ffi_multi.jhyy` — 3+ 参数 FFI
- `ffi_file.jhyy` — 文件 I/O

## v0.5 专项（浮点算术 + break/continue + 类型转换）

- `break_continue.jhyy` — while/for break/continue
- `float_arith.jhyy` / `float_arith_f32.jhyy` — 浮点 `+ - * /`
- `void_if.jhyy` — void 分支
- `nested_if.jhyy` — 嵌套 if/else
- `overflow.jhyy` — i32 二补码环绕
- `fib30.jhyy` — 递归压力
- `big_array.jhyy` — 大数组
- `big_test.jhyy` — 综合压力
- `ptr_self_assign.jhyy` — 指针自赋值

## v0.6 专项（切片 + 命名空间 + `as` 指针）

- `slice_literal.jhyy` — 切片字面量
- `slice_index.jhyy` — 切片下标
- `slice_subrange.jhyy` — 切片子范围
- `slice_len.jhyy` — 切片长度
- `array_to_slice.jhyy` — 数组 → 切片 decay
- `slice_iterate.jhyy` — 切片遍历
- `namespace/main.jhyy` + `mod_a.jhyy` + `mod_b.jhyy` — `mod::fn()` 命名空间
- `namespace_dup.jhyy` + `ns_dup_a.jhyy` + `ns_dup_b.jhyy` — 同名函数跨模块
- `cast_ptr_to_int.jhyy` — `*T ↔ i64` 互转
- `arena_test/arena_test.jhyy` + `arena.jhyy` — Stage 0 自举验证

## 库文件（SKIP，不计入 passed/failed）

- `mylib.jhyy`
- `multi_file/lib_a.jhyy`, `lib_b.jhyy`, `lib_c.jhyy`
- `namespace/mod_a.jhyy`, `mod_b.jhyy`
- `ns_dup_a.jhyy`, `ns_dup_b.jhyy`
- `arena_test/arena.jhyy`

无 `fn main_jhyy` → 回归脚本自动 SKIP。

---

## 运行方法

### 全量回归

```bash
python compiler/build/bin/regress.py
```

输出示例：
```
===== 43/46 passed, 0 failed, 3 skipped =====
```

### 单个测试

```bash
./compiler/build/bin/jhyy.exe compile compiler/tests/examples/hello.jhyy -o hello
./hello.exe; echo $?     # 期望 42
```

### 单元测试（不常用）

```bash
# 单文件单元测试（独立编译运行）
/c/msys64/ucrt64/bin/gcc.exe -std=c11 -Wall -Wextra \
    compiler/tests/unit/test_lexer.c compiler/src/lexer.c compiler/src/arena.c \
    -o compiler/build/bin/test_lexer.exe -I compiler/src && \
    ./compiler/build/bin/test_lexer.exe

# test_sprint1b 需要链接多个模块
/c/msys64/ucrt64/bin/gcc.exe -std=c11 -Wall -Wextra \
    compiler/tests/unit/test_sprint1b.c \
    compiler/src/arena.c compiler/src/types.c compiler/src/symtab.c compiler/src/ast.c \
    -o compiler/build/bin/test_sprint1b.exe -I compiler/src && \
    ./compiler/build/bin/test_sprint1b.exe
```
