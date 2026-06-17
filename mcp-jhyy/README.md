# JHYY MCP Server

让 Claude Code 能编译、运行、检查 JHYY 程序的 MCP (Model Context Protocol) 服务。

## 安装

### 1. 安装依赖

```bash
pip install mcp[cli]
```

`mcp[cli]` 提供 FastMCP。`jhyy_runner.py` 仅用 Python 标准库。

### 2. 注册到 Claude Code

编辑 `C:\Users\liuzhen\.claude.json`（Windows）：

```json
{
  "mcpServers": {
    "fetch-mcp": { ... },
    "jhyy": {
      "command": "python",
      "args": ["C:/Users/liuzhen/Desktop/coding/JiHuiYiYou/mcp-jhyy/server.py"]
    }
  }
}
```

### 3. 重启 Claude Code

MCP 服务在 Claude Code 启动时加载。

## 工具

### jhyy_compile
编译 .jhyy 文件为可执行文件。

### jhyy_run
编译并运行 .jhyy 文件，返回运行结果（stdout / stderr / exit code）。

### jhyy_check
仅做语法/语义检查，不生成可执行文件。返回结构化错误列表。

### jhyy_get_il
编译并返回生成的 QBE IL 文本（用于调试 codegen）。

### jhyy_lang_ref
查询语言规范（关键词搜索 `spec_data.json`）。

### jhyy_abi_info
查询 ABI 信息（关键词搜索 `abi_data.json`）。

### jhyy_format
简单的代码格式化（v0.5.0 最小实现）。

## 资源

| URI | 内容 |
|-----|------|
| `jhyy://spec` | 语言规范 v0.5.0 (JSON) |
| `jhyy://abi` | ABI 信息 v1.0.0 (JSON) |
| `jhyy://examples` | 示例代码列表 |
| `jhyy://changelog` | 最新 changelog |

## 目录结构

```
mcp-jhyy/
├── server.py         # MCP 入口 (FastMCP)
├── jhyy_runner.py    # subprocess 封装 + 诊断解析
├── abi_data.json     # ABI 数据 (从 v1.0.0 白皮书提取)
├── spec_data.json    # 语言规范数据 (从 v0.5.0 spec 提取)
└── README.md         # 本文件
```

## 端到端示例

```
User: 写一段 .jhyy 代码计算 fib(30) 并运行

Claude:
1. 写入 fib_test.jhyy
2. 调用 jhyy_run("fib_test.jhyy")
3. 返回: { ok: true, exit_code: 0, stdout: "fib(30) = 832040\n", ... }
```

## 限制

- 仅支持 Windows x64（与 JHYY 编译器当前目标一致）
- jhyy_format 仅为最小占位实现
- 编译/运行结果通过 `subprocess.run` 同步获取
