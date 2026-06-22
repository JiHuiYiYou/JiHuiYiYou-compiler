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

> **本节已被 lang-spec v1.0.0 附录 C 取代**。phase-2 启动条件（lang-spec § 附录 C 行 1132-1137）：
> - ✅ 本 spec 覆盖的全部特性在 v0.6 编译器中可用
> - ✅ 已知限制（P2/P3）有 fallback 路径（详见 lang-spec 附录 B + abi § 11.1）
> - ⏳ 至少 5 个 sprint 验证（实际编译器源用 JHYY 写一遍，过回归）
> - ⏳ Stage 0/1/2 自举验证（C 编译器编译 JHYY 编译器源码）

> **事实（v0.6 changelog 验证）**：lang-spec 附录 C 行 1100-1113 列的 9 个 C 模块 → JHYY 子集映射**全部 ✓**，即每个 C 编译器模块都能用 v1.0.0 spec 表达。phase-2 启动门槛的语言特性部分**已达成**。
>
> **遗留 P3 限制（lang-spec 附录 B 追更后）**：
> - 变参函数（printf `...`）：JHYY 侧需手动展开，自举可手写 wrapper
> - 函数回调（JHYY 函数指针 → C 调用）：phase-2 考虑
> - 嵌套 import `utils::io`：v0.6+ 候选（v0.6 sprint 6B 未实现，仍 P3）
> - struct/enum 跨 FFI 边界：sprint 6D 部分修 pointer-to-struct，全 ABI 兼容 phase-2 处理
> - 浮点 fmod / NaN/Inf 极端行为：仍 P3，自举可绕过

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
| 手动链表/动态数组 | `arena_alloc(a, size as i64)` + `arena_alloc` + linked list（**jhyy 无泛型**，不能用 `arena.alloc::<T>()`） |
| `malloc`/`free` | `libc_malloc` / `libc_free` FFI（**jhyy 无 `Arena::new` 自动析构**，调用方负责 `arena_free`） |
| `strcmp`, `strncpy` | 自行实现或 FFI |
| `fprintf(stderr, ...)` | FFI `libc_fputs` 拼好的字符串（**JHYY 侧不能直接调用变参 fprintf**，见 lang-spec 附录 B P3） |
| `fopen`, `fread`, `fclose` | FFI `libc_fopen` 等 |

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
