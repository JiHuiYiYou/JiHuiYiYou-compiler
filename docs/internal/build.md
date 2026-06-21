# 构建与运行

> JHYY 编译器构建、.jhyy 程序编译与运行、手动验证流水线。

## 关键路径

```
C:/Users/liuzhen/Desktop/coding/JiHuiYiYou/
├── compiler/src/*.c        # 编译器源
├── compiler/runtime/       # 运行时（main → main_jhyy 桥接）
├── compiler/jhyy-src/      # Stage 0 自举翻译（arena.jhyy 等）
├── compiler/tests/         # 测试
│   ├── examples/*.jhyy     # 集成测试
│   └── unit/*.c            # 单元测试
├── qbe/qbe.exe             # QBE IL 编译器（vendor）
├── mcp-jhyy/               # Claude Code MCP 服务
└── docs/                   # 文档
```

工具：
- GCC：`/c/msys64/ucrt64/bin/gcc.exe` (15.2.0 MSYS2 ucrt64)
- QBE：`./qbe/qbe.exe -t amd64_win`
- Git：`/d/Program Files/Git/bin/git.exe`

---

## 编译编译器

```bash
/c/msys64/ucrt64/bin/gcc.exe -std=c11 -Wall -Wextra \
    compiler/src/*.c \
    -o compiler/build/bin/jhyy.exe \
    -I compiler/src
```

构建产物在 `compiler/build/bin/jhyy.exe`。`-Wall -Wextra` 必须零警告。

---

## 编译 .jhyy 程序

```bash
./compiler/build/bin/jhyy.exe compile <file.jhyy> -o <output_name>
```

支持多文件（v0.4+）：
```bash
./compiler/build/bin/jhyy.exe compile main.jhyy lib_a.jhyy lib_b.jhyy -o output
```

---

## 编译并运行

```bash
./compiler/build/bin/jhyy.exe run <file.jhyy>
```

> **注意**：Windows 下 `system()` 路径有 P1 bug，`run` 子命令可能失败。临时替代：先 `compile`，再手动 `./output.exe`。

---

## 手动验证流水线

当需要排查 codegen / QBE / 链接问题时，手动走一遍：

```bash
# 1. 编译 .jhyy → 生成 QBE IL（停在这一步）
./compiler/build/bin/jhyy.exe compile test.jhyy -o test

# 2. 查看 QBE IL
cat compiler/build/bin/test.il

# 3. 手动调用 QBE
./qbe/qbe.exe -t amd64_win -o test.s compiler/build/bin/test.il

# 4. 手动链接
/c/msys64/ucrt64/bin/gcc.exe test.s compiler/runtime/runtime.c -o test.exe

# 5. 检查退出码
./test.exe; echo $?
```

---

## 回归测试

```bash
python compiler/build/bin/regress.py
```

自动运行 `compiler/tests/examples/*.jhyy` 所有测试，输出：
```
===== 43/46 passed, 0 failed, 3 skipped =====
```

无 `main_jhyy` 的库文件（`mylib.jhyy`、`ns_dup_*.jhyy`）自动 SKIP，不计入 passed/failed。

---

## 单元测试

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

---

## 修改代码后的验证步骤

1. `gcc` 编译零警告
2. `hello.jhyy` 编译运行 → EXIT:42
3. `demo.jhyy` 编译运行 → EXIT:0
4. 改动涉及的相关特性测试编译运行 → 预期退出码
5. 改了 codegen：目视检查 `.il` 文件（QBE IL 语法正确性）
6. 改了 sema：检查错误消息是否包含文件名和行号
7. 全量回归：`python compiler/build/bin/regress.py`

---

## QBE 后端坑（Windows 独有）

1. **临时变量必须带字母前缀**：`%t0`, `%t1`... 不能用 `%0`, `%1`（QBE Windows 构建拒绝纯数字）
2. **缩进必须是空格**：4 空格，不能用 tab（QBE Windows 构建 tab 解析有 bug）
3. **QBE 参数顺序**：`qbe -o output.s input.il`（输出在前，和常见 CLI 相反）
4. **目标平台**：`-t amd64_win`（Windows x64 PE），不是默认的 `amd64_sysv`（Linux ELF）

见 `docs/internal/architecture.md` 中 codegen 相关章节。
