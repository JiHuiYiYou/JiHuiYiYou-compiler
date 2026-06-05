# JHYY (机会翼游) — 自研编程语言

JHYY 是一门静态类型的、表达式导向的编译型系统编程语言。编译器用 C 编写，后端 QBE，目标 x86-64 Windows。

## 快速开始

### 1. 环境要求

- Windows 10+ / MSYS2 (ucrt64)
- GCC via MSYS2: `C:\msys64\ucrt64\bin\gcc.exe`

### 2. 构建编译器

```bash
git clone <this-repo>
cd JiHuiYiYou

# 编译 jhyy 编译器
gcc -std=c11 -Wall -Wextra compiler/src/*.c -o compiler/build/bin/jhyy.exe -I compiler/src
```

### 3. 添加到 PATH

将 `JiHuiYiYou\compiler\build\bin\` 加入系统环境变量 `PATH`，之后可在任意目录使用 `jhyy` 命令。

### 4. Hello World

```rust
// hello.jhyy
extern fn puts(s: *u8) -> i32;

fn main_jhyy() -> i32 {
    puts("Hello, world!");
    0
}
```

```bash
jhyy run hello.jhyy
# 输出: Hello, world!
```

## 命令行

```bash
jhyy compile <file.jhyy> [-o name]   # 编译为 .exe
jhyy run     <file.jhyy>             # 编译并运行
jhyy build   <file.jhyy> [-o name]   # 仅生成 QBE IL (.il 文件)
jhyy                                  # 打印帮助
```

## VS Code 配置

### 一键安装语言扩展

将 `vscode-ext/` 文件夹拷贝到 VS Code 扩展目录：

```
# PowerShell（管理员）
Copy-Item vscode-ext $env:USERPROFILE\.vscode\extensions\jhyy-lang -Recurse
```

或直接拖拽 `vscode-ext` 到 `C:\Users\<用户名>\.vscode\extensions\` 并重命名为 `jhyy-lang`。

### 安装 Code Runner（获得 ▶ 按钮）

1. VS Code 扩展商店搜索 `Code Runner`（`formulahendry.code-runner`）
2. 安装后重启 VS Code

### 配置 Code Runner 快捷键

`Ctrl+,` → 右上角 `{}` 打开 `settings.json`，加入：

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

`Ctrl+K Ctrl+S` → 右上角 `{}` 打开 `keybindings.json`，加入 F6 快捷键：

```json
[
    {
        "key": "f6",
        "command": "code-runner.run",
        "when": "editorLangId == jhyy"
    }
]
```

### 使用方式

| 方式 | 操作 |
|------|------|
| ▶ 按钮 | 编辑器右上角 → Run Code |
| F6 | 编译并运行当前 .jhyy 文件 |
| Ctrl+Shift+B | VS Code 默认构建任务（运行当前文件） |
| Ctrl+Shift+P → "JHYY: Compile" | 只编译 |

## 语言特性速览

```rust
// 函数
fn add(a: i32, b: i32) -> i32 { a + b }

// 变量（不可变 / 可变）
let x = 42;
let mut y = 10;
y += 1;

// 控制流
if x > 0 { "positive" } else { "zero or negative" }
while y > 0 { y -= 1; }
for i in 0..10 { /* ... */ }

// 结构体 & 枚举
type Point = struct { x: i32, y: i32 };
type Option = enum { Some(i32), None };

// 模式匹配
let val = match x {
    1 => "one",
    2 | 3 => "two or three",
    _ => "other"
};

// 指针
let p = &x;
*p = 100;

// 外部函数
extern fn puts(s: *u8) -> i32;

// 模块导入
import mylib;
```

## 项目结构

```
├── compiler/
│   ├── src/          # C 编译器源码 (19 个源文件)
│   ├── runtime/      # C 运行时 (Arena + main 入口)
│   └── tests/
│       ├── unit/     # C 单元测试
│       └── examples/ # .jhyy 集成测试
├── vscode-ext/       # VS Code 语言扩展
├── qbe/              # Vendored QBE 后端
├── docs/
│   ├── plans/        # 阶段计划
│   ├── logs/         # 开发日志
│   ├── jhyy-abi-v0.0.1.md
│   └── jhyy-lang-spec-v0.0.1.md
└── .vscode/          # VS Code 项目配置（tasks、推荐扩展）
```

## License

MIT
