# mcp-jhyy — Claude Code MCP 服务

> 让 Claude Code 直接操作 JHYY：编译、运行、看中间表示、查台账、跑回归。
>
> 本文件是**服务使用者**的说明书；agent 侧的路由规则在
> [`server.py`](server.py) 顶部的 `JHYY_INSTRUCTIONS`（MCP 一启动 Claude 就读到）。

---

## 安装

### 1. Python 依赖

```bash
pip install fastmcp
```

⚠️ **装的是 `fastmcp`，不是 `mcp[cli]`** —— `server.py` 写的是
`from fastmcp import FastMCP`（**顶层** `fastmcp` 模块），而顶层 `fastmcp` 是
**独立于**官方 `mcp` 包的另一个发行包（`fastmcp` 的依赖是 `fastmcp-slim`）。
官方 `mcp` 只提供带前缀的 `mcp.server.fastmcp` ⇒ `pip install mcp[cli]`
装完仍然 `ModuleNotFoundError: No module named 'fastmcp'`。

自检：

```bash
python -c "import fastmcp; print(fastmcp.__version__)"
```

⚠️ 别用 `python -c "import mcp"` 自检 —— 查的是另一个包，会给假绿灯。

### 2. 注册到 Claude Code

编辑 `C:\Users\<用户名>\.claude.json`（Windows）：

```json
{
  "mcpServers": {
    "jhyy": {
      "command": "python",
      "args": ["C:/path/to/JiHuiYiYou/mcp-jhyy/server.py"]
    }
  }
}
```

重启 Claude Code 后，问一句「用 `jhyy_check` 检查 hello.jhyy 的语法」——
能调用并返回结果就说明加载成功。

也可以直接跑端到端测试（不需要 Claude Code）：

```bash
python -c "import sys; sys.path.insert(0,'mcp-jhyy'); \
from jhyy_runner import compile_and_run; \
print(compile_and_run('compiler/tests/examples/hello.jhyy'))"
# => {'ok': True, 'exit_code': 42, 'stdout': '', ...}
```

> ⚠️ `mcp-jhyy` 带连字符 ⇒ **不是合法的 Python 包名** ⇒ 不能
> `from mcp_jhyy.jhyy_runner import …`。用 `sys.path.insert` 或直接跑脚本。

---

## 工具（11 个）

### 编译 & 运行

| 工具 | 用途 |
|---|---|
| `jhyy_run` | 编译 + 链接 + 执行，返回 exit code / stdout |
| `jhyy_compile` | 只编译 |
| `jhyy_check` | 只做语法 / 语义检查，返回结构化错误列表 |
| `jhyy_get_il` | 取中间表示（调试 codegen 用；需要 `JHY_WRITE_IL=1`） |

### 验证

| 工具 | 用途 |
|---|---|
| `jhyy_regress` | 跑回归，返回 PASS/FAIL 列表 |
| `jhyy_il_diff` | 两个 `.il` 的 byte-equal 检查 + 上下文 diff |
| `jhyy_selfhost_check` | 一键自举闭环验证（v1→v2→v3→v4） |

### 查询

| 工具 | 用途 |
|---|---|
| `jhyy_workarounds` | 查 W-NNN workaround 的状态 / 详情（实时读台账） |
| `jhyy_lang_ref` | 查语言规范（关键词搜索） |
| `jhyy_abi_info` | 查 ABI 信息（`sret` / `struct pass` / `FFI` …） |
| `jhyy_format` | 简单格式化（最小占位实现） |

### 资源（4 个）

`jhyy://spec` · `jhyy://abi` · `jhyy://examples` · `jhyy://changelog`

---

## 路径解析

`jhyy_runner.py` 的 `JHYY_ROOT` **由脚本位置自动推导**
（`Path(__file__).resolve().parents[1]`）⇒ **换机器不用改任何东西**。

---

## 排障

| 症状 | 原因 / 解法 |
|---|---|
| `ModuleNotFoundError: No module named 'fastmcp'` | 环境没装 `fastmcp` ⇒ `pip install fastmcp` |
| MCP 没加载 | `~/.claude.json` 的路径对不对；手工 `python <path>/server.py` 看 stderr |
| `jhyy_run` 报 `Executable not found` | `compiler/build/bin/jhyy.exe` 不存在 ⇒ 先 `make` |
| 输出有 GBK 编码错误 | `jhyy_runner.py` 用 `encoding="utf-8", errors="replace"` ⇒ 工具返回的 JSON 是 UTF-8，Windows 终端显示可能乱码 |
| `jhyy_regress` 超时 | 全量回归要 5–10 分钟，MCP 侧有 600s 硬超时 ⇒ 走 `Bash(python regress.py …)` + `run_in_background` |

---

## 开发

```bash
# pytest(需要 pip —— 本机默认 python 没有,用 miniconda 的)
C:/Users/liuzhen/miniconda3/python.exe -m pytest mcp-jhyy/tests -q
```

测试文件（9 个）：`test_abi_info` · `test_env` · `test_get_il` · `test_il_diff` ·
`test_lang_ref` · `test_ntstatus` · `test_regress` · `test_selfhost_check` ·
`test_workarounds`。

`jhyy_ntstatus.py` 是**内部 helper**（NTSTATUS 解析），**未注册**成 MCP 工具。

---

## 相关

- 台账（`jhyy_workarounds` 读的就是它）⇒ [`docs/workarounds.md`](../docs/workarounds.md)
- 语言规范 / ABI ⇒ [`docs/abis/`](../docs/abis/)
- 编译器架构 ⇒ [`docs/internal/architecture.md`](../docs/internal/architecture.md)
