# JHYY v0.5.0 Changelog

## 版本目标

完成 Phase 1 关键修复与开发者工具链:
- 修复 v0.4.0 隐藏的 codegen bug (if/else void, ptr 运算, phi 标签)
- 实现 break/continue
- 浮点算术
- 锁定 ABI v1.0.0
- 提供 Claude Code MCP 服务

---

## Sprint 5A: Bug 修复与新功能

### 5A.1 浮点算术 codegen

| Bug | 描述 | 修复 |
|-----|------|------|
| f32/f64 `+ - * /` | 使用整数 opcode (add/sub/mul/div) | 改用 `adds`/`subs`/`muls`/`divs` (f32) 和 `addd`/`subd`/`muld`/`divd` (f64) |

**实现**:
- `cg_binary` 中根据操作数类型 (`KIND_FLOAT`/`KIND_DOUBLE`) 选对应 QBE opcode
- 浮点字面量在 NODE_LET 推断时与声明类型对齐 (f32→s_, f64→d_)

### 5A.2 `*ptr = *ptr - expr` sema 类型推断

| Bug | 描述 | 修复 |
|-----|------|------|
| `*p = *p - 1` 报类型错 | 右侧 LHS 推断时用 *p 的值类型，但二元运算要求两侧独立 | NODE_ASSIGN 中显式注释 LHS/RHS 独立推断；本次未修改逻辑（实际修复见 5A.5）|

### 5A.3 if/else void 分支 phi 错误

| Bug | 描述 | 修复 |
|-----|------|------|
| `if c { f = 1; }` (无 else) 中 phi 填充 i32 而非 void | cg_if 中未判断 n->type 是否 void | void 时直接 `return v;` 不发 phi |

### 5A.4 嵌套 if/else if/else phi 前驱块错误

| Bug | 描述 | 修复 |
|-----|------|------|
| `if a { if b { ... } else { ... } } else { ... }` 中内层 if merge 块直接 jmp 外层 merge，phi 用错的 label | 内层 if 的 fallthrough 干扰了外层 phi 前驱 | pre-allocate trampoline 块 `ep`，内层 if 跳 ep → ep 跳外层 merge |

### 5A.5 if-as-block-return-value 修复 (此版本关键 bug)

| Bug | 描述 | 修复 |
|-----|------|------|
| `fn f() -> i32 { if x { 0 } else { 1 } }` 返回 0 (空值) | cg_block 收到 NODE_IF 作为最后语句时，调用 cg_stmt 不返回值，导致 last 永远为空 | 扩展 cg_block，对 NODE_IF/NODE_MATCH/NODE_BLOCK 也调用 cg_expr 捕获值 |

**触发场景**: big_test.jhyy 压力测试发现 v0.4.0 隐藏 bug
**测试**: `_min_clamp_pos.jhyy` / `clamp_pos` / `t_negate` / `t_clamp` / etc. 共 ~30 个函数

### 5A.6 break/continue 支持

| 功能 | 描述 |
|------|------|
| `break;` | 跳出最近 while/for |
| `continue;` | while: 跳回 hdr；for: 跳到 i++ (`incr_b` 单独块) |

**实现**:
- Lexer: 新 TOKEN_BREAK / TOKEN_CONTINUE
- Parser: parse_break / parse_continue
- AST: NODE_BREAK / NODE_CONTINUE
- Sema: loop_depth 验证 (必须 > 0)
- Codegen: CGContext 加 `loop_starts[]`/`loop_ends[]`/`loop_continues[]` 三栈

**关键设计**: for 循环必须用单独的 `incr_b` 块（不能合并到 body 或 hdr），否则 `continue` 跳过 i++ 导致死循环。

### 5A.7 临时文件清理

删除 v0.2 遗留的 `_test_*.jhyy` 等调试文件 (`.gitignore` 已加 pattern 防止再次提交)。

---

## Sprint 5B: ABI 白皮书 v1.0.0

**路径**: `docs/abis/jhyy-abi-v1.0.0.md`

**v0.0.1 → v1.0.0 变更**:
- 锁定 struct pass-by-value (sret + stack copy)
- 锁定多文件模块系统 (无命名空间)
- FFI 多参数 / 文件 I/O
- break/continue 跳转目标表
- 短路求值实现细节
- 新增已知限制 (切片, struct 跨 FFI, 浮点 fmod, callbacks, etc.)
- 版本兼容承诺 (本锁定版本 v1.0.0 不可变)

---

## Sprint 5C: Claude Code MCP 服务

**路径**: `mcp-jhyy/`

**7 个工具**:
| 工具 | 功能 |
|------|------|
| `jhyy_compile` | 编译 .jhyy 文件为 .exe |
| `jhyy_run` | 编译并运行 |
| `jhyy_check` | 仅做语法/语义检查 |
| `jhyy_get_il` | 返回生成的 QBE IL 文本 |
| `jhyy_lang_ref` | 关键词搜索 spec_data.json |
| `jhyy_abi_info` | 关键词搜索 abi_data.json |
| `jhyy_format` | 简单格式化 (v0.5.0 最小实现) |

**4 个资源**:
| URI | 内容 |
|-----|------|
| `jhyy://spec` | 语言规范 v0.5.0 (JSON) |
| `jhyy://abi` | ABI 信息 v1.0.0 (JSON) |
| `jhyy://examples` | 示例代码列表 |
| `jhyy://changelog` | 最新 changelog |

**注册**: `~/.claude.json` 加 `jhyy` MCP server 配置 (stdio, Python)。

**端到端验证**:
```python
# 通过 FastMCP client 测试成功
result = await session.call_tool('jhyy_run', {'file': 'compiler/tests/examples/hello.jhyy'})
# 返回: exit_code=42 (hello.jhyy 期望值)
```

---

## Sprint 5D: 全面测试与压力

### 5D.1 新增专项测试

| 测试 | 验证内容 | 期望 |
|------|---------|------|
| `break_continue.jhyy` | for/break/continue 组合 (sum odd < 10) | EXIT 25 |
| `float_arith.jhyy` | f64 `+ - * /` 算术 | EXIT 6 |
| `float_arith_f32.jhyy` | f32 算术 | EXIT 4 |
| `overflow.jhyy` | i32 整数溢出 (二补码环绕) | EXIT 1 |
| `nested_if.jhyy` | 5 层嵌套 if/else if | EXIT 500 |
| `void_if.jhyy` | if 无 else (void 分支) | EXIT 0 |
| `ptr_self_assign.jhyy` | `*p = *p + 1` 自赋值 | EXIT 70 |
| `big_array.jhyy` | 100 元素数组 (sum=5050) | EXIT 5050 |
| `fib30.jhyy` | 递归 fib(30) | EXIT 832040 |
| `big_test.jhyy` | 868 行综合压力 (57 sub-tests) | EXIT 12345 |

### 5D.2 回归套件

`compiler/build/bin/regress.py`:
- 扫描 `compiler/tests/examples/*.jhyy`
- 读 `// EXPECT: N` 注释
- 编译并运行，对比实际 exit code
- 报告 PASS/FAIL

**v0.5.0 终态**: 34/36 通过 (2 个 pre-existing failures: import_test/mylib，import 系统与外部 link 问题，不在 v0.5.0 scope)

### 5D.3 零警告构建

`main.c` 中 `cmd[2048]` 太小导致 `snprintf` 截断 warning — 改为 `cmd[4096]`，现在 `-Wall -Wextra` 零警告。

---

## 已知问题 (v0.5.0 仍未解决)

| # | 严重度 | 描述 |
|---|--------|------|
| **P2** | 缺失 | 切片 `[*]T` 有类型定义但无 codegen |
| **P2** | 不完整 | 浮点比较 (`==`/`!=`/`<`/...) 部分场景未完全类型化 |
| **P3** | 缺失 | 浮点 fmod (`%`) 未实现 |
| **P3** | 缺失 | struct/enum 跨 FFI 边界 (Windows x64 ABI 不兼容) |
| **P3** | 缺失 | 变参函数 (`printf` 的 `...`) 在 JHYY 侧需展开 |
| **P3** | 缺失 | 函数回调 (Phase 2 考虑) |
| **P3** | 缺失 | 模块系统无命名空间 (v0.4 多文件后符号冲突) |
| **P3** | 缺失 | import 路径不支持嵌套 (`utils::io`) |
| **P2** | pre-existing | import_test.jhyy 找不到 mylib.jhyy (路径 bug) |

---

## 文件变更统计

| 类别 | 文件 | 变更 |
|------|------|------|
| 编译器 | `compiler/src/ast.c/h` | NODE_BREAK/NODE_CONTINUE/NODE_CAST |
| | `compiler/src/lexer.c/h` | TOKEN_BREAK/TOKEN_CONTINUE |
| | `compiler/src/parser.c` | parse_break/parse_continue/cast |
| | `compiler/src/sema.c/h` | loop_depth, NODE_BREAK/NODE_CAST, float coerce |
| | `compiler/src/codegen.c` | +200 行: break/continue, void if, nested-if, ptr/bin, float arith, if-as-block-value 修复 |
| | `compiler/src/main.c` | cmd buffer 4096 |
| 测试 | `compiler/tests/examples/*.jhyy` | +10 个新测试 (含 868 行 big_test) |
| | `compiler/build/bin/regress.py` | Python 回归脚本 |
| 文档 | `docs/abis/jhyy-abi-v1.0.0.md` | 锁定 ABI |
| | `docs/logs/changelog-v0.5.0.md` | 本文件 |
| | `CLAUDE.md` | v0.5.0 状态表更新 |
| MCP | `mcp-jhyy/server.py` | FastMCP 入口 (7 tools + 4 resources) |
| | `mcp-jhyy/jhyy_runner.py` | subprocess 封装 |
| | `mcp-jhyy/abi_data.json` | ABI 数据 |
| | `mcp-jhyy/spec_data.json` | Lang spec 数据 |
| | `mcp-jhyy/README.md` | 使用说明 |
| 配置 | `~/.claude.json` | 注册 jhyy MCP server |

---

## 下一步 (v0.6.0 候选)

- 切片 `[*]T` codegen (P2)
- 模块命名空间 (P3)
- 浮点 fmod (P3)
- struct 跨 FFI (P3)
- C ABI 兼容的 struct passing (替换当前的 stack-copy)
