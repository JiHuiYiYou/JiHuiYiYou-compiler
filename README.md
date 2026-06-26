<div align="center">

# JHYY

### 机会翼游 — 自研静态类型编译型系统编程语言

**Statically typed. Expression-oriented. Compiled to native via QBE.**

[![Version](https://img.shields.io/badge/version-v0.5.1-blue)](docs/logs/v0/changelog-v0.5.0.md)
[![Phase](https://img.shields.io/badge/phase-1%20(C%20host)-yellow)](#路线图)
[![Backend](https://img.shields.io/badge/backend-QBE-orange)](#)
[![Platform](https://img.shields.io/badge/platform-Windows%20x64-lightgrey)](#)
[![License](https://img.shields.io/badge/license-MIT-green)](#license)

[快速开始](#快速开始) · [语言特性](#语言特性) · [命令行](#命令行) · [VS Code](#vs-code-集成) · [文档](#文档) · [路线图](#路线图)

</div>

---

## 这是什么

JHYY 是一门自研的、静态类型的、表达式导向的编译型系统编程语言。**编译器用 C 编写** (Phase 1)，后端走 [QBE](https://c9x.me/compile/) 输出 x86-64 Windows 机器码。

**终极目标**: 用 JHYY 写 JHYY 的 IDE、写 OS kernel、**编译器自举**（用 JHYY 编译 JHYY）。

## 一段代码看语法

```rust
// 函数、变量、控制流、struct、match、指针、FFI 一次展示
type Point = struct { x: i32, y: i32 };

fn dist_sq(a: Point, b: Point) -> i32 {
    let dx = a.x - b.x;
    let dy = b.y - a.y;
    dx * dx + dy * dy
}

fn classify(n: i32) -> *u8 {
    match n {
        0          => "zero",
        1..=9      => "single digit",
        10 | 20    => "round number",
        _          => "other",
    }
}

fn main_jhyy() -> i32 {
    let p = Point { x: 3, y: 4 };
    let q = Point { x: 0, y: 0 };
    printf("d² = %d\n", dist_sq(p, q));
    printf("%s\n", classify(42));
    0
}
```

## 快速开始

### 环境要求

- Windows 10+ / MSYS2 (ucrt64)
- `C:\msys64\ucrt64\bin\gcc.exe` (GCC 15+)
- 已 vendor 在 `qbe/` 的 QBE (Windows x64 target)

### 构建编译器

```bash
git clone https://github.com/JiHuiYiYou/JiHuiYiYou-compiler
cd JiHuiYiYou-compiler

/c/msys64/ucrt64/bin/gcc.exe -std=c11 -Wall -Wextra \
    compiler/src/*.c \
    -o compiler/build/bin/jhyy.exe \
    -I compiler/src
```

> 推荐把 `compiler/build/bin/` 加入 `PATH`，下文假定 `jhyy` 已可用。

### Hello World

```rust
// hello.jhyy
extern fn puts(s: *u8) -> i32;

fn main_jhyy() -> i32 {
    puts("Hello, world!");
    0
}
```

```bash
jhyy compile hello.jhyy -o hello
./hello.exe
# => Hello, world!
```

### 跑测试

```bash
python compiler/build/bin/regress.py
# => 34/36 passed, 2 failed  (import_test 已知问题)
```

## 语言特性 (v0.5.1)

| 类别 | 支持 |
|------|------|
| **类型** | `i8/i16/i32/i64`, `u8/u16/u32/u64`, `f32/f64`, `bool`, `*T`, `[T; N]`, `struct`, `enum` |
| **类型转换** | `as` 关键字 — 整数/浮点互转、扩宽/截断 |
| **控制流** | `if`/`else` (含表达式值), `while`, `for start..end`, `break`, `continue`, `match` (字面量/范围/通配符) |
| **逻辑** | `&&` / `\|\|` 短路求值, `!` / `~` 一元运算 |
| **函数** | 头等函数、递归、复合赋值 (`+=` `-=` `*=` `/=` `%=`) |
| **模块** | `import`、传递性导入、多文件编译 |
| **FFI** | `extern fn` 调用 C (printf、文件 I/O、多参数) |
| **内存** | 运行时 Arena 分配器 |

完整变更历史见 [changelog-v0.5.0](docs/logs/v0/changelog-v0.5.0.md)。

## 命令行

```bash
jhyy compile <file.jhyy> [-o name]   # 编译为 .exe
jhyy run     <file.jhyy>             # 编译并运行
jhyy build   <file.jhyy> [-o name]   # 仅生成 QBE IL (.il 文件)
jhyy check   <file.jhyy>             # 仅做语法/语义检查
jhyy                                  # 打印帮助
```

## VS Code 集成

### 安装语言扩展

将 `vscode-ext/` 文件夹拷贝到 VS Code 扩展目录：

```powershell
# PowerShell（管理员）
Copy-Item vscode-ext $env:USERPROFILE\.vscode\extensions\jhyy-lang -Recurse
```

或直接拖拽 `vscode-ext` 到 `C:\Users\<用户名>\.vscode\extensions\` 并重命名为 `jhyy-lang`。

### 安装 Code Runner（获得 ▶ 按钮）

1. VS Code 扩展商店搜索 `Code Runner`（`formulahendry.code-runner`）
2. 安装后重启 VS Code

### 配置 Code Runner

`Ctrl+,` → 右上角 `{}` 打开 `settings.json`：

```json
{
    "code-runner.executorMap": {
        "jhyy": "cd $dirWithoutTrailingSlash && jhyy run $fileName"
    },
    "code-runner.runInTerminal": true,
    "code-runner.saveFileBeforeRun": true,
    "code-runner.clearPreviousOutput": true
}
```

`Ctrl+K Ctrl+S` → `keybindings.json` 加 F6 快捷键：

```json
[
    {
        "key": "f6",
        "command": "code-runner.run",
        "when": "editorLangId == jhyy"
    }
]
```

### 快捷键

| 操作 | 触发方式 |
|------|---------|
| ▶ 按钮 | 编辑器右上角 → Run Code |
| **F6** | 编译并运行当前 .jhyy 文件 |
| Ctrl+Shift+B | VS Code 默认构建任务（运行当前文件） |
| Ctrl+Shift+P → "JHYY: Compile" | 只编译 |

## 文档

### 规范 & ABI

| 文档 | 路径 |
|------|------|
| 语言规范 (latest) | [`docs/abis/jhyy-lang-spec-v0.2.1.md`](docs/abis/jhyy-lang-spec-v0.2.1.md) |
| ABI 白皮书 (locked v1.0.0) | [`docs/abis/jhyy-abi-v1.0.0.md`](docs/abis/jhyy-abi-v1.0.0.md) |
| 早期 ABI 草案 (v0.0.1) | [`docs/abis/jhyy-abi-v0.0.1.md`](docs/abis/jhyy-abi-v0.0.1.md) |
| 早期语言规范 (v0.0.1) | [`docs/abis/jhyy-lang-spec-v0.0.1.md`](docs/abis/jhyy-lang-spec-v0.0.1.md) |

### 路线图 & 计划

| 文档 | 路径 |
|------|------|
| **总规划 v0.2.x → v1.0.0** | [`docs/plans/phase/phase-1-v0.2.x-to-v1.0.0.md`](docs/plans/phase/phase-1-v0.2.x-to-v1.0.0.md) |
| Phase 0 — Skeleton | [`docs/plans/phase/phase-0-skeleton.md`](docs/plans/phase/phase-0-skeleton.md) |
| **Phase 1 — C 编译器 (当前)** | [`docs/plans/phase/phase-1-c-compiler.md`](docs/plans/phase/phase-1-c-compiler.md) |
| Phase 2 — 自举 | [`docs/plans/phase/phase-2-self-hosting.md`](docs/plans/phase/phase-2-self-hosting.md) |
| Phase 2.5 — QBE 完整重写 | [`docs/plans/phase/phase-2.5-qbe-rewrite.md`](docs/plans/phase/phase-2.5-qbe-rewrite.md) |
| Phase 3 — 扩展 | [`docs/plans/phase/phase-3-expansion.md`](docs/plans/phase/phase-3-expansion.md) |

### 变更日志

| 版本 | 文档 |
|------|------|
| **v0.5.0 (最新)** | [`docs/logs/v0/changelog-v0.5.0.md`](docs/logs/v0/changelog-v0.5.0.md) |
| v0.4.0 | [`docs/logs/v0/changelog-v0.4.0.md`](docs/logs/v0/changelog-v0.4.0.md) |
| v0.3.0 | [`docs/logs/v0/changelog-v0.3.0.md`](docs/logs/v0/changelog-v0.3.0.md) |
| v0.2.1 | [`docs/logs/v0/changelog-v0.2.1.md`](docs/logs/v0/changelog-v0.2.1.md) |
| v0.0.1 | [`docs/logs/v0/changelog-v0.0.1.md`](docs/logs/v0/changelog-v0.0.1.md) |

Sprint 实施日志: [`docs/logs/v0/sprint-*.md`](docs/logs/v0/) (sprint-1a ~ 1g)

### 工具 & 集成

| 工具 | 路径 |
|------|------|
| Claude Code MCP 服务 | [`mcp-jhyy/`](mcp-jhyy/) — 7 tools + 4 resources |
| MCP 使用说明 | [`mcp-jhyy/README.md`](mcp-jhyy/README.md) |
| VS Code 语言扩展 | [`vscode-ext/`](vscode-ext/) |

## 路线图

| 阶段 | 内容 | 状态 |
|------|------|------|
| **Phase 1** | C 宿主编译器达到自举门槛 | **进行中** (v0.5.1) |
| Phase 2 | 用 JHYY 重写编译器（自举，Stage 0/1/2 验证） | 未开始 |
| Phase 3 | OS kernel、IDE、扩展生态 | 未开始 |

### v0.6.0 候选

- 切片 `[*]T` codegen
- 浮点 fmod (`%`)
- 模块命名空间
- C ABI 兼容的 struct 传递

## 项目结构

```
├── compiler/
│   ├── src/                    # C 编译器源码 (19 个源文件)
│   ├── runtime/                # C 运行时 (Arena + main 入口)
│   └── tests/
│       ├── unit/               # C 单元测试
│       └── examples/           # .jhyy 集成测试
├── vscode-ext/                 # VS Code 语言扩展
├── qbe/                        # Vendored QBE 后端
├── mcp-jhyy/                   # Claude Code MCP 集成
├── docs/                       # 规范、ABI、计划、变更日志
│   ├── abis/                   # 语言规范 + ABI 白皮书
│   ├── plans/                  # 阶段计划 + 版本任务清单
│   └── logs/                   # 变更日志 + Sprint 实施日志
└── .vscode/                    # VS Code 项目配置 (tasks、推荐扩展)
```

## Contributors

- **人类作者**: JHYY ([JHYY@local](https://github.com/JiHuiYiYou))
- **AI 协作**: [MiniMax-M3](https://MiniMax) — 通过 [Claude Code](https://claude.ai/code) CLI 工作流参与设计、编码、调试、文档

> 自 v0.6 起所有 sprint 的实现 + 文档由 JHYY + MiniMax-M3 协作完成。MiniMax-M3 是 [MiniMax](https://MiniMax) 出品的基础模型，**不是** Anthropic Claude / OpenAI GPT 系列。

## License

[MIT](LICENSE)
