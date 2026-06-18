# JHYY MCP Server

让 Claude Code 能**编译、运行、检查 JHYY 程序**的 MCP (Model Context Protocol) 服务器。

装上之后，Claude Code 在帮你写 `.jhyy` 代码时，能自动调用编译器查语法错、跑回归、看生成的 QBE IL、查语言规范 / ABI 信息，省去手动跑 `jhyy compile && ./a.out` 的来回。

## 工作原理

```
你："写一段 fib(30) 的递归代码并跑一下"
Claude Code → 自动调用 MCP 工具
  ├── jhyy_check("fib.jhyy")          → 语法/语义检查
  ├── jhyy_compile("fib.jhyy")        → 调 jhyy.exe compile
  ├── jhyy_run("fib.jhyy")            → 编译并执行，返回 exit_code / stdout
  ├── jhyy_get_il("fib.jhyy")         → 返回 QBE IL（调试 codegen 用）
  └── 输出: "fib(30) = 832040, exit_code 0"
```

## 快速开始

### 前提条件

- 已安装 [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
- 已安装 Python 3.8+
- 已构建 JHYY 编译器（`compiler/build/bin/jhyy.exe` 存在）

### 1. 安装 Python 依赖

```bash
pip install mcp[cli]
```

`mcp[cli]` 提供 FastMCP。`jhyy_runner.py` 仅用 Python 标准库。

### 2. 注册到 Claude Code

编辑 `C:\Users\<用户名>\.claude.json`（Windows）：

```json
{
  "mcpServers": {
    "jhyy": {
      "command": "python",
      "args": ["C:/Users/liuzhen/Desktop/coding/JiHuiYiYou/mcp-jhyy/server.py"]
    }
  }
}
```

> 把路径改成你本地的 `mcp-jhyy/server.py` 绝对路径。

### 3. 验证安装

重启 Claude Code 后，在任何目录下问：

```
"列出 JHYY 编译器版本"
```

如果 Claude 能调用 `jhyy_check` 之类工具并返回结果，说明 MCP 已正常加载。

也可以直接跑端到端测试（无需 Claude Code）：

```bash
python -c "from mcp_jhyy.jhyy_runner import compile_and_run; print(compile_and_run('compiler/tests/examples/hello.jhyy'))"
# => {'ok': True, 'exit_code': 42, 'stdout': '', ...}
```

## 在多个项目中使用

JHYY MCP 是**全局注册**的（写在 `~/.claude.json` 里），装一次即可在所有目录使用，不需要每个项目都装。

如果你的 `jhyy.exe` 路径在 `jhyy_runner.py` 里硬编码的位置（默认 `C:/Users/liuzhen/Desktop/coding/JiHuiYiYou/compiler/build/bin/jhyy.exe`），搬家后需改 `mcp-jhyy/jhyy_runner.py` 顶部的 `JHYY_ROOT` 常量，然后重启 Claude Code。

## 可用工具

### 编译 & 运行

| 工具 | 何时使用 | 备注 |
|------|---------|------|
| `jhyy_compile` | 把 `.jhyy` 编译成 `.exe` | 输出二进制路径可指定 |
| `jhyy_run` | 编译并运行，返回 exit code / stdout | 完整 E2E |
| `jhyy_check` | 只做语法/语义检查，不生成二进制 | 返回结构化错误列表 |
| `jhyy_get_il` | 编译并返回 QBE IL 文本 | 调试 codegen 用 |

### 语言 & ABI 查询

| 工具 | 何时使用 | 示例 |
|------|---------|------|
| `jhyy_lang_ref` | 查语言规范（关键词搜索） | `"match"`, `"for"`, `"as"` |
| `jhyy_abi_info` | 查 ABI 信息 | `"sret"`, `"struct pass"`, `"FFI"` |

### 工具类

| 工具 | 何时使用 | 备注 |
|------|---------|------|
| `jhyy_format` | 简单格式化 | v0.5.0 最小占位实现 |

Claude Code 会根据工具描述中的触发条件**自动判断何时调用**，无需你手动指定。

## 资源

| URI | 内容 |
|-----|------|
| `jhyy://spec` | 语言规范 v0.5.0 (JSON) |
| `jhyy://abi` | ABI 信息 v1.0.0 (JSON) |
| `jhyy://examples` | 示例代码列表 |
| `jhyy://changelog` | 最新 changelog |

## 数据

| 类别 | 来源 | 文件 |
|------|------|------|
| 语言规范 | `docs/abis/jhyy-lang-spec-v0.2.1.md` | `spec_data.json` |
| ABI 信息 | `docs/abis/jhyy-abi-v1.0.0.md` | `abi_data.json` |
| 集成测试 | `compiler/tests/examples/*.jhyy` | 由 `jhyy_run` 动态读 |

## 项目结构

```
mcp-jhyy/
├── server.py              # MCP 服务器主程序（FastMCP 入口，7 tools + 4 resources）
├── jhyy_runner.py         # subprocess 封装（compile / run / check / get_il）
├── spec_data.json         # 语言规范数据（从 v0.2.1 spec 提取）
├── abi_data.json          # ABI 数据（从 v1.0.0 白皮书提取）
└── README.md              # 本文件
```

## 维护

### 更新语言规范 / ABI 数据

`spec_data.json` 和 `abi_data.json` 是从 `docs/` 下的 markdown 提取的快照。手动更新步骤：

1. 编辑 `docs/abis/jhyy-lang-spec-*.md` 或 `docs/abis/jhyy-abi-*.md`
2. 重新提取 JSON（目前是手编，未来 v0.6+ 考虑写自动提取脚本）
3. 重启 Claude Code 让 MCP 重新加载

### 添加新工具

1. 在 `server.py` 里加 `@mcp.tool()` 装饰的函数
2. 工具描述要写清"何时使用"和参数语义（Claude 靠这个判断自动调用）
3. 重启 Claude Code

## 端到端示例

```
User: 写一段 .jhyy 代码计算 fib(30) 并运行

Claude:
1. 写入 fib_test.jhyy
2. 调用 jhyy_run("fib_test.jhyy")
3. 返回: { ok: true, exit_code: 0, stdout: "fib(30) = 832040\n", ... }
```

## 常见问题

**Q: 启动 Claude Code 后 MCP 没有加载？**
A: 确认 `~/.claude.json` 里的 `jhyy` 配置路径正确。运行 `python C:/path/to/mcp-jhyy/server.py` 看是否有 Python 错误。

**Q: 显示 `ModuleNotFoundError: No module named 'mcp'`？**
A: MCP 主机用的 Python 环境没装 `mcp[cli]`。用对应环境的 `pip install mcp[cli]` 重装。`server.py` 是 `python` 启动的，确保 `python -c "import mcp"` 能成功。

**Q: `jhyy_run` 报 `Executable not found`？**
A: 检查 `mcp-jhyy/jhyy_runner.py` 顶部的 `JHYY_ROOT` 是否对应当前项目根。`compiler/build/bin/jhyy.exe` 必须存在（先 `gcc compiler/src/*.c -o ...` 编译）。

**Q: 如何确认 MCP 正在工作？**
A: 在 Claude Code 中问："用 jhyy_check 检查 hello.jhyy 的语法"。如果 Claude 调用了工具并返回结果，说明 MCP 正常工作。

**Q: 输出有 GBK 编码错误？**
A: `jhyy_runner.py` 用了 `encoding="utf-8", errors="replace"`，Windows GBK 终端显示中文可能乱码但工具返回的 JSON 是 UTF-8 没问题。

## 限制

- 仅支持 Windows x64（与 JHYY 编译器当前目标一致）
- `jhyy_format` 仅为最小占位实现
- 编译/运行结果通过 `subprocess.run` 同步获取，大程序可能 timeout
