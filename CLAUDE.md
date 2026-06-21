# CLAUDE.md — JHYY (机会翼游) 编译器项目

## 项目身份

JHYY 是一门自研静态类型系统编程语言。终极目标：用 JHYY 写 JHYY 的 IDE、用 JHYY 写 OS kernel、编译器自举（自己编译自己）。

当前阶段：**Phase 1** — 用 C 语言实现第一个 JHYY 编译器（宿主编译器）。

---

## 关键路径 (绝对路径，Windows 格式)

```c
// 编译器
C:/Users/liuzhen/Desktop/coding/JiHuiYiYou/compiler/src/*.c
C:/Users/liuzhen/Desktop/coding/JiHuiYiYou/compiler/src/*.h

// 工具链
C:/msys64/ucrt64/bin/gcc.exe          // GCC 15.2.0 (MSYS2 ucrt64)
C:/Users/liuzhen/Desktop/coding/JiHuiYiYou/qbe/qbe.exe   // QBE (vendor, -t amd64_win)

// Git
/d/Program Files/Git/bin/git.exe      // Git 2.53.0

// 文档
C:/Users/liuzhen/Desktop/coding/JiHuiYiYou/docs/
```

---

## 构建 & 运行

### 编译编译器

```bash
/c/msys64/ucrt64/bin/gcc.exe -std=c11 -Wall -Wextra \
    compiler/src/*.c \
    -o compiler/build/bin/jhyy.exe \
    -I compiler/src
```

### 编译 .jhyy 程序

```bash
./compiler/build/bin/jhyy.exe compile <file.jhyy> -o <output_name>
```

### 编译并运行

```bash
./compiler/build/bin/jhyy.exe run <file.jhyy>
# 注意: Windows 下 system() 路径有 bug (P1)，run 子命令可能失败
# 临时替代: compile 后手动 ./output.exe
```

### 手动验证流水线

```bash
# 1. 查看生成的 QBE IL
cat compiler/build/bin/<output>.il

# 2. 手动调用 QBE
./qbe/qbe.exe -t amd64_win -o output.s output.il

# 3. 手动链接
/c/msys64/ucrt64/bin/gcc.exe output.s compiler/runtime/runtime.c -o output.exe

# 4. 检查退出码
./output.exe; echo $?
```

---

## 编译器架构

### 流水线

```
.jhyy → Lexer → Token流 → Parser → AST → Sema → 标注AST → Codegen → QBE IL → QBE → 汇编(.s) → GCC → .exe
```

### 模块清单 (19 个源文件)

| 文件 | 行数 | 职责 |
|------|------|------|
| `arena.c/h` | ~150 | Bump allocator (编译器内部使用) |
| `lexer.c/h` | ~400 | 词法分析: 源码 → Token 流 (50+ token 类型) |
| `ast.c/h` | ~400 | AST: 35 种节点类型 (tagged union) |
| `types.c/h` | ~250 | 类型系统: 原始类型/指针/切片/数组/struct/enum/func/alias |
| `symtab.c/h` | ~120 | 符号表: FNV-1a hash, 链式作用域 |
| `parser.c/h` | ~750 | 递归下降 + Pratt 表达式解析 |
| `sema.c/h` | ~500 | 语义分析: 类型检查/推断, 3 遍遍历 |
| `ir.c/h` | ~250 | IR 构建器: QBE IL 文本生成 |
| `codegen.c/h` | ~550 | AST → QBE IL 发射 |
| `main.c` | ~150 | CLI 入口, 驱动流水线, 调用 QBE + GCC |
| `runtime/runtime.c` | ~50 | 运行时: arena allocator + main → main_jhyy 入口 |
| `runtime/runtime.h` | ~25 | 运行时头文件 |

### 流水线调用顺序 (main.c)

```
read_file → arena_init → lexer_init → parser_init → parser_parse
→ sema_init → sema_check → ir_init → cg_module
→ write .il → system("qbe ...") → system("gcc ...")
```

---

## 关键设计细节

### QBE 后端 (Windows 独有坑)

1. **临时变量必须带字母前缀**: `%t0`, `%t1`... 不能用 `%0`, `%1` (QBE Windows 构建拒绝纯数字)
2. **缩进必须是空格**: 4 个空格，不能用 tab (QBE Windows 构建 tab 解析有 bug)
3. **QBE 参数顺序**: `qbe -o output.s input.il` (输出在前，和常见 CLI 相反)
4. **目标平台**: `-t amd64_win` (Windows x64 PE)，不是默认的 `amd64_sysv` (Linux ELF)

### AST 节点

- 所有节点是 `Node` struct + variant data (紧跟 Node 在 arena 中分配)
- `ACCESSOR` 宏模式: `node_xxx_data(Node*)` 返回 variant data 指针
- 构造函数命名: `ast_new_xxx(Arena*, SourceLoc, ...)`

### 类型推断规则

- 参数必须标注类型
- 局部变量自动推断 (从 init 表达式)
- 函数返回类型: 标注优先，标注为 `()` 时从函数体推断

### 符号表

- 开放寻址 + 线性探测, 64-bit FNV-1a hash
- 2 的幂大小, 负载因子 0.75 自动扩容
- `symtab_insert_sym()` 用于桥接 parser 和 sema 的 Sym

### 作用域管理

- Parser 和 Sema 各有独立的作用域链
- Parser: `parse_func` push → `parse_block` push → `parse_stmt` → ... → pop
- Sema: `check_func_decl` push → `infer_type(block)` → ... → pop
- Sema 的 `nlocals` 不会在 pop 时自动清理，需在 `check_func_decl` 入口手动置零

---

## 编码约定

1. **C11 标准**: `-std=c11 -Wall -Wextra`，零警告
2. **所有路径用 `/`**: 不用 `\`（即使在 Windows 上）
3. **文档用 `.md`**: 禁止 `.docx`、`.pdf`
4. **日志**: `docs/logs/` 下每个 sprint 一个 `.md`
5. **测试文件**: `compiler/tests/examples/*.jhyy`（集成测试），`compiler/tests/unit/*.c`（单元测试）
6. **禁止提交**: `.exe`, `.il`, `.s`, `.o` 等构建产物 (已在 `.gitignore`)
7. **修改范围最小化**: 不顺手重构，不添加"可能将来有用"的代码

---

## 当前状态 (v0.6.0)

### 已实现的语言特性

| 特性 | 状态 |
|------|------|
| 整数/浮点/字符串/字符/布尔字面量 | 完成 |
| 浮点字面量 codegen (f32/f64) | 完成 (v0.3) |
| 浮点算术 `+ - * /` (f32/f64) | 完成 (v0.5) |
| `let` / `let mut` 变量绑定 | 完成 |
| 定长数组 `[T; N]`: 字面量/类型注解/下标读写 | 完成 (v0.3) |
| 切片 `[*]T`: 字面量/index/subrange/len | 完成 (v0.6) |
| 二元运算 (算术/比较/位运算) | 完成 |
| `&&` / `||` 短路求值 | 完成 |
| 一元运算 (`-`, `!`, `~`) | 完成 |
| 类型转换 `as` (整数/浮点互转, 扩宽/截断) | 完成 (v0.5) |
| `if`/`else` 表达式 (含嵌套 if/else if, void 分支) | 完成 |
| `while` 循环 (含 break/continue) | 完成 (v0.5 加 break/continue) |
| `for i in start..end` 循环 (类型感知, break/continue) | 完成 |
| `break;` / `continue;` | 完成 (v0.5) |
| 函数 (参数/返回/递归/return 类型检查) | 完成 |
| `return` 提前返回 | 完成 |
| 块表达式 `{ ... }` | 完成 |
| 指针 `&x`, `*ptr`, `*ptr = val` | 完成 |
| struct 定义/字面量/字段访问 | 完成 |
| struct 按值传递/返回/赋值 | 完成 (v0.4) |
| enum 定义/变体构造 (一致内存布局) | 完成 |
| `match` 表达式 (字面量/通配符/范围) | 完成 |
| `extern fn` FFI 声明 (含 printf, 文件 I/O) | 完成 |
| FFI 多参数调用 (≥3 参数) | 完成 (v0.4) |
| import 模块系统 (含传递性导入) | 完成 (v0.4) |
| 多文件 CLI 输入 | 完成 (v0.4) |
| 模块命名空间 `mod::fn()` | 完成 (v0.6) |
| `as` 类型转换: `*T ↔ i64/u64` | 完成 (v0.6) |
| Claude Code MCP 服务 (7 工具 + 4 资源) | 完成 (v0.5) |
| Stage 0 自举试点 (`arena.jhyy` 翻译) | 完成 (v0.6) |
| FFI 多参数调用 (≥3 参数) | 完成 (v0.4) |
| 控制台输出 (中文 UTF-8 + 数字 printf) | 完成 |
| Arena allocator (via FFI) | 完成 |
| struct 字段通过指针访问 (`ptr->field`) | 完成 |
| 复合赋值 (`+=`, `-=`, `*=`, `/=`, `%=`) | 完成 |
| import 模块系统 (含传递性导入) | 完成 (v0.4) |
| 多文件 CLI 输入 | 完成 (v0.4) |
| Claude Code MCP 服务 (7 工具 + 4 资源) | 完成 (v0.5) |

### 已知限制

| # | 严重度 | 描述 |
|---|--------|------|
| **P2** | 不完整 | 浮点比较 (`==`/`<`/...) 部分场景未完全类型化 |
| **P3** | 缺失 | 浮点 fmod (`%`) 未实现 |
| **P3** | 缺失 | struct/enum 跨 FFI 边界 (Windows x64 ABI 不兼容) |
| **P3** | 缺失 | 变参函数 (`printf` 的 `...`) 在 JHYY 侧需展开 |
| **P3** | 缺失 | 函数回调 (Phase 2 考虑) |
| **P3** | 缺失 | Windows 下部分 Unix 命令 (rm) 不可用 |

**v0.6 解决**：
- ✅ 切片 `[*]T` codegen
- ✅ 模块命名空间 (`mod::fn()`)

### 已修复 (v0.5.0)

| # | 描述 |
|---|------|
| — | **浮点算术 codegen**: f32/f64 `+ - * /` 使用 `adds`/`subs`/`muls`/`divs`/`addd`/`subd`/`muld`/`divd` |
| — | **类型转换 `as`**: 整数扩宽 (exts), 浮点↔整数 (dtosi/sltof), 浮点互转 (exts/truncd) |
| — | **if/else void 分支修复**: 无值分支时不发 phi |
| — | **嵌套 if/else if phi 修复**: 预分配 trampoline 块 `ep` 避免前驱块标签错 |
| — | **if-as-block-return-value 修复 (关键 bug)**: cg_block 对 NODE_IF/NODE_MATCH/NODE_BLOCK 也调用 cg_expr 捕获值 |
| — | **break/continue**: while/for 循环支持, for 循环单独 `incr_b` 块 |
| — | **i32 整数溢出**: 定义为二补码环绕, 行为有测试覆盖 |
| — | **零警告构建**: main.c cmd buffer 2048 → 4096 修复 snprintf 截断 warning |
| — | **新增 10 个专项测试**: break_continue, float_arith, fib30, big_array, overflow, nested_if, void_if, ptr_self_assign, big_test |
| — | **Python 回归脚本**: `compiler/build/bin/regress.py` 自动运行所有 .jhyy 测试 |
| — | **ABI 白皮书 v1.0.0**: 锁定 struct pass-by-value, 多文件, FFI, break/continue |
| — | **MCP 服务**: 7 工具 (compile/run/check/get_il/lang_ref/abi_info/format) + 4 资源 |

### 已修复 (v0.6.0)

| # | 描述 |
|---|------|
| — | **切片 `[*]T` 完整 codegen**: 字面量/index/subrange/len/array decay |
| — | **模块命名空间**: `mod::fn()` 限定调用 + Sym.module 字段 + `$mod__name` mangle |
| — | **`as` 类型转换补全**: `*T ↔ i64` 互转 |
| — | **NODE_ADDR_OF 修复**: SSA temp 取址时 spill 到新栈 slot |
| — | **NODE_DEREF 修复**: pointer-to-struct 返回指针本身（by-address）|
| — | **NODE_FIELD 修复**: pointer-to-struct field access 用正确 qbe_type |
| — | **NODE_ASSIGN 新增 NODE_FIELD**: `(*ptr).field = val` 现在生效 |
| — | **extern fn 不再 mangle**: `arena.jhyy` 的 `extern fn malloc` 直接 emit 原名 |
| — | **resolve_imports dir fallback**: 主文件路径无 slash 时回退到 `"."` |
| — | **regress.py 跳过库文件**: 无 `main_jhyy` 的文件 SKIP，不算 failed |
| — | **Stage 0 翻译**: `compiler/jhyy-src/arena.jhyy`（arena.c → JHYY），验证自举能力 |
| — | **新增 7 个测试**: slice_*, namespace_dup, cast_ptr_to_int |
| — | **43/46 回归通过**（3 skipped = 库文件） |

### 已修复 (v0.4.0)

| # | 描述 |
|---|------|
| — | **struct 按值传递**: 调用方分配栈拷贝, `cg_copy_struct` 逐字段复制 |
| — | **struct 返回值 (sret)**: 调用方分配返回槽, 隐式传递指针, 被调用方写入 |
| — | **struct 赋值**: `a = b` 逐字段复制 (含嵌套 struct) |
| — | **NODE_IDENT struct 修复**: 返回地址而非 load 值 |
| — | **NODE_LET struct 修复**: 不 mutable struct 也使用栈分配 |
| — | **NODE_RETURN sret**: 复制到返回槽后 emit bare ret |
| — | **cg_func sret header**: sret 函数签名添加隐藏指针参数 |
| — | **传递性 import**: 递归解析, 循环检测, 访问列表持久化 |
| — | **多文件 CLI**: `jhyy compile a.jhyy b.jhyy -o output` |
| — | **cmd_build 修复**: 增加 `resolve_imports` 调用 |
| — | **新增辅助函数**: `cg_copy_struct`, `ir_emit_call_void`, `resolve_one_import` |
| — | **CGContext 扩展**: `sret_slot`, `has_sret` 字段 |

### 已修复 (v0.3.0)

| # | 描述 |
|---|------|
| **Bug 1** | Pratt 解析器优先级: `-`/`*`/`&` 双角色 token 使用 PREC_TERM/FACTOR/BIT_AND 而非 PREC_UNARY |
| **Bug 2** | 嵌套 if/else if/else phi 前驱块标签错误 — 添加 trampoline 块 |
| **Bug 3** | if/else void 分支 phi 类型错误 — 已通过 void 返回类型处理修复 |
| **Bug 4** | 浮点字面量 codegen 硬编码 0.0 — 格式化为 QBE `d_`/`s_` 字面量 |
| — | **ir_emit_alloc**: QBE 对齐值修复 (仅支持 4/8/16) |
| — | **sema NODE_CALL**: 参数类型推断递归 (修复 `arr[i]` 直接作为函数参数) |
| — | **定长数组 `[T; N]`**: 完整 codegen (类型注解/字面量/下标读写/赋值) |
| — | 新增 AST 节点: `NODE_ARRAY_TYPE`, `NODE_ARRAY_LIT` |

### 已修复 (v0.2.1)

| # | 描述 |
|---|------|
| P0-A | symtab FNV-1a → 开放寻址 + 线性探测 |
| P0-B | sub-word 类型 (i8/u8/i16/u16) load/store 使用正确宽度 |
| P0-C | 比较指令类型感知 (signed/unsigned × w/l) |
| P0-D | 64 位移位使用正确宽度 |
| P1 | Windows `jhyy run` path_to_win() 修复 |
| P1 | return 语句类型正确传播，函数体类型检查修复 |
| P2 | `&&`/`||` 短路求值 (分支跳转 + phi) |
| P2 | enum payload_offset 存储在 Type 中，sema/codegen 一致 |
| P2 | for 循环变量类型感知 (使用 type_size + qbe_type_of) |
| — | 控制台 UTF-8 输出 (SetConsoleOutputCP) |
| — | 字符串转义序列 (\\n, \\t, \\r, \\0, \\\\, \\\", \\xHH) |
| — | 函数体已有 return 时不再重复 emit ret |

---

## 测试验证

### 运行单元测试

```bash
# 每个 test_*.c 需要独立编译运行
/c/msys64/ucrt64/bin/gcc.exe -std=c11 -Wall -Wextra \
    compiler/tests/unit/test_lexer.c compiler/src/lexer.c compiler/src/arena.c \
    -o compiler/build/bin/test_lexer.exe -I compiler/src && \
    ./compiler/build/bin/test_lexer.exe

# test_sprint1b 需要链接多个模块:
/c/msys64/ucrt64/bin/gcc.exe -std=c11 -Wall -Wextra \
    compiler/tests/unit/test_sprint1b.c \
    compiler/src/arena.c compiler/src/types.c compiler/src/symtab.c compiler/src/ast.c \
    -o compiler/build/bin/test_sprint1b.exe -I compiler/src && \
    ./compiler/build/bin/test_sprint1b.exe

# test_parser 和 test_sema 同理 (需要 lexer + parser + symtab + ast + arena)
```

### 集成测试

| 测试 | 预期 | 验证内容 |
|------|------|---------|
| `hello.jhyy` | EXIT:42 | 基础流水线 |
| `demo.jhyy` | EXIT:0 | 全部 v0.0.1 特性 |
| `pointer.jhyy` | EXIT:100 | `&x`, `*p = val` |
| `struct.jhyy` | EXIT:30 | struct 定义+字面量+字段访问 |
| `match.jhyy` | EXIT:20 | match 字面量+通配符 |
| `forloop.jhyy` | EXIT:10 | for 循环 (0+0+1+2+3+4) |
| `helloworld.jhyy` | stdout: "Hello, world!" | 控制台输出 |
| `import_test.jhyy` | EXIT:72 | import 模块系统 |
| `print_num.jhyy` | stdout: "计算结果: 42" | printf 数字输出 |
| `chinese.jhyy` | stdout: "你好，世界！" | UTF-8 中文输出 |
| `return_type.jhyy` | EXIT:100 | return 类型检查 + printf |
| `logical.jhyy` | EXIT:0 | && / \|\| 短路求值 |

### 修改代码后的验证步骤

1. `gcc` 编译零警告
2. `hello.jhyy` 编译运行 → EXIT:42
3. `demo.jhyy` 编译运行 → EXIT:0
4. 各特性测试编译运行 → 预期退出码
5. 如果改了 codegen: 目视检查 `.il` 文件 (QBE IL 语法正确性)
6. 如果改了 sema: 检查错误消息是否包含文件名和行号

---

## 相关文档

| 文档 | 路径 |
|------|------|
| 语言规范 | `docs/jhyy-lang-spec-v0.0.1.md` (latest: v0.2.1) |
| ABI 白皮书 | `docs/abis/jhyy-abi-v1.0.0.md` (locked) |
| Phase 0 计划 | `docs/plans/phase-0-skeleton.md` |
| Phase 1 计划 | `docs/plans/phase-1-c-compiler.md` |
| Phase 2 计划 | `docs/plans/phase-2-self-hosting.md` |
| Phase 3 计划 | `docs/plans/phase-3-expansion.md` |
| v0.5.0 changelog | `docs/logs/changelog-v0.5.0.md` |
| v0.4.0 changelog | `docs/logs/changelog-v0.4.0.md` |
| v0.3.0 changelog | `docs/logs/changelog-v0.3.0.md` |
| v0.0.1 changelog | `docs/changelog-v0.0.1.md` |
| MCP 服务 | `mcp-jhyy/` |
| Sprint 日志 | `docs/logs/` |
