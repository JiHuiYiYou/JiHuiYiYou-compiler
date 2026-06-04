# Phase 2: 自举 — 用 jhyy 重写编译器

> 目标：将 C 编译器 1:1 移植到 jhyy 语言，实现编译器编译自身
> 预计：约 4 周
> 前置：Phase 1 完成 (C 编译器可用)
> 产出：自举的 jhyy 编译器 (`jhyy_1`)

---

## 自举定义

```
C编译器 编译 jhyy源码 → jhyy_0 (第一代自举编译器)
jhyy_0 编译 jhyy源码 → jhyy_1 (第二代)
diff(jhyy_0的输出, jhyy_1的输出) → 完全相同 = 自举成功🏆
```

---

## Step 2.0: 确认 Phase 1 编译器支持自举所需全部特性

在开始移植前，检查清单:

- [ ] 整数类型 (i32, i64, u8 等)
- [ ] bool 类型
- [ ] 指针 `*T`
- [ ] 切片 `[*]T`
- [ ] struct 定义和字面量
- [ ] enum 定义和 match
- [ ] 函数 (含递归)
- [ ] let 绑定 (可变和不可变)
- [ ] if/else 表达式
- [ ] while 循环
- [ ] match 表达式 (字面量、枚举、通配符)
- [ ] Arena 类型和方法
- [ ] FFI (调用 libc)
- [ ] import 模块系统
- [ ] 字符串字面量
- [ ] 类型推断 (局部)
- [ ] struct 字段访问
- [ ] 嵌套作用域
- [ ] return 语句

缺失的特性 → 先补充实现。

---

## Step 2.1: 创建 `compiler/src0/` 目录

```
compiler/src0/
├── main.jhyy          # CLI 入口
├── arena.jhyy         # 编译器内部 arena
├── diagnostics.jhyy   # 错误报告
├── lexer.jhyy         # 词法分析
├── parser.jhyy        # 解析器
├── ast.jhyy           # AST 类型定义
├── types.jhyy         # 类型系统
├── symtab.jhyy        # 符号表
├── sema.jhyy          # 语义分析
├── ir.jhyy            # IR 构建器
├── codegen.jhyy       # QBE 代码生成
├── util.jhyy          # 工具函数
└── ffi.jhyy           # FFI 声明
```

---

## Step 2.2: 按模块逐个移植

### 移植映射

| C 模式 | jhyy 改写 |
|--------|----------|
| `typedef struct { ... } Node;` | `type Node = struct { ... };` |
| `switch (node->kind) { ... }` | `match node.kind { NODE_X => ... }` |
| 手动链表/动态数组 | `arena.alloc::<T>()` + `arena.alloc_slice::<T>(n)` |
| `malloc`/`free` | `Arena::new(size)` → 离开作用域自动销毁 |
| `strcmp`, `strncpy` | 自行实现或 FFI |
| `fprintf(stderr, ...)` | FFI `fprintf` |
| `fopen`, `fread`, `fclose` | FFI 或直接用系统调用 |

### 移植顺序 (按依赖关系从下到上)

```
1. util.jhyy          (无依赖: StringBuilder, 哈希表, 字符串)
2. arena.jhyy         (无依赖: bump allocator)
3. diagnostics.jhyy   (依赖 util)
4. ast.jhyy           (依赖 arena)
5. types.jhyy         (依赖 ast, arena)
6. symtab.jhyy        (依赖 types, arena)
7. lexer.jhyy         (依赖 diagnostics, arena)
8. parser.jhyy        (依赖 lexer, ast, types, arena)
9. sema.jhyy          (依赖 ast, types, symtab, diagnostics)
10. ir.jhyy           (依赖 types, arena)
11. codegen.jhyy      (依赖 ast, types, ir, symtab)
12. main.jhyy         (依赖所有模块 + ffi.jhyy)
```

### 每个模块的移植步骤

1. 翻译类型定义 (C struct → jhyy type)
2. 翻译函数签名 (C func → jhyy fn)
3. 翻译函数体 (C → jhyy, 用 match 改写 switch)
4. 用 jhyy arena 改写所有 malloc/free
5. 编译测试

---

## Step 2.3: FFI 声明

```rust
// compiler/src0/ffi.jhyy

// ─── 文件操作 ───
extern fn fopen(path: [*]u8, mode: [*]u8) -> *u8;         // FILE*
extern fn fread(buf: *u8, size: i64, count: i64, fp: *u8) -> i64;
extern fn fwrite(buf: *u8, size: i64, count: i64, fp: *u8) -> i64;
extern fn fclose(fp: *u8) -> i32;
extern fn fprintf(fp: *u8, fmt: [*]u8, ...) -> i32;

// ─── 内存 ───
extern fn malloc(size: i64) -> *u8;
extern fn free(p: *u8);
extern fn memcpy(dst: *u8, src: *u8, n: i64) -> *u8;
extern fn memset(s: *u8, c: i32, n: i64) -> *u8;

// ─── 字符串 ───
extern fn strlen(s: [*]u8) -> i64;
extern fn strcmp(a: [*]u8, b: [*]u8) -> i32;

// ─── 系统 ───
extern fn system(cmd: [*]u8) -> i32;
extern fn exit(code: i32);
```

如果 Phase 1 不支持变参 FFI (fprintf 的 `...`), 则:
- 写 C helper 包装变参调用
- 或在 jhyy 中自实现格式化

---

## Step 2.4: 首次编译

```bash
# 用 C 编译器编译 jhyy 编译器源码
./compiler/build/bin/jhyy compile compiler/src0/main.jhyy -o compiler/build/bin/jhyy_0

# 验证 jhyy_0 工作正常
./compiler/build/bin/jhyy_0 compile compiler/tests/examples/hello.jhyy -o /tmp/hello
/tmp/hello
echo $?   # → 42
```

---

## Step 2.5: 自举验证脚本

```bash
#!/bin/bash
# compiler/tests/bootstrap/verify.sh
set -e

JHY_C=./compiler/build/bin/jhyy       # C 编译器
JHY_0=./compiler/build/bin/jhyy_0     # 第一代自举
JHY_1=./compiler/build/bin/jhyy_1     # 第二代自举
SRC=compiler/src0/main.jhyy

# Step 1: C编译器 → jhyy_0
echo "=== Step 1: Building jhyy_0 with C compiler ==="
$JHY_C compile $SRC -o $JHY_0

# Step 2: jhyy_0 → 编译自身 → jhyy_1
echo "=== Step 2: Building jhyy_1 with jhyy_0 ==="
$JHY_0 compile $SRC -o $JHY_1

# Step 3: 比较 IL 输出
echo "=== Step 3: Comparing IL outputs ==="
TEST_FILE=compiler/tests/examples/fib_rec.jhyy
$JHY_0 build $TEST_FILE -o build/il/fib_0.il
$JHY_1 build $TEST_FILE -o build/il/fib_1.il

if diff build/il/fib_0.il build/il/fib_1.il > /dev/null; then
    echo "PASS: IL outputs identical — self-hosting verified!"
else
    echo "FAIL: IL outputs differ"
    diff build/il/fib_0.il build/il/fib_1.il
    exit 1
fi

# Step 4: 运行完整测试套件
echo "=== Step 4: Running test suite with jhyy_1 ==="
# ... 运行所有测试
echo "All tests passed!"
```

---

## 常见问题和对策

| 问题 | 对策 |
|------|------|
| jhyy_0 和 jhyy_1 输出不一致 | 二分法逐模块定位; 检查未初始化内存; 确保哈希表迭代顺序稳定 |
| jhyy 编译器比 C 版慢很多 | 可接受; 自举意义 > 性能; Phase 3 加优化 |
| 缺少某个 libc 函数的 FFI | 补充声明; 或写 C helper |
| 变参 FFI 不支持 | C helper 包装; 或自实现格式化 |

---

## Phase 2 完成标准

- [ ] 所有 12 个模块移植到 jhyy
- [ ] C 编译器成功编译 jhyy 源码 → `jhyy_0`
- [ ] `jhyy_0` 成功编译自身 → `jhyy_1`
- [ ] `jhyy_0` 和 `jhyy_1` 对相同输入产生相同 IL
- [ ] `jhyy_1` 通过完整测试套件
- [ ] 自举验证脚本自动化运行
