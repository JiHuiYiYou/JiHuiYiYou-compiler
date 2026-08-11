# mcp-jhyy — Claude Code 项目指令

本文件是 `mcp-jhyy/` 子目录的局部 Claude Code 指令。**只在 Claude Code 工作目录为 `mcp-jhyy/` 时加载**（用户实际开发在项目根，本文件主要给"打开 mcp-jhyy/ 看源码"场景使用）。

`jhyy` MCP server 的 `instructions` 字段（`mcp-jhyy/server.py` 顶部的 `JHYY_INSTRUCTIONS`）才是真正的运行时触发信号——MCP 一启动 Claude 就读到，比 CLAUDE.md 更直接。**本文件是冗余备份，万一 MCP 启动失败 / `instructions` 字段不生效时兜底**。

## 工具路由

| 用户要做的事 | 用这个工具 |
|------------|----------|
| 写完 .jhyy 跑一下看行为 | `jhyy_run` |
| 只检查语法 / 语义（不生成二进制） | `jhyy_check` |
| 改 codegen 后看生成的 QBE IL | `jhyy_get_il` |
| 查 "JHYY 支持 X 吗 / 怎么写 Y" | `jhyy_lang_ref` |
| 查 ABI / struct 传参 / FFI / 调用约定 | `jhyy_abi_info` |
| 格式化 .jhyy 源码 | `jhyy_format` |
| 跑回归 / 验证 baseline 没破 | `jhyy_regress` |
| 比两个 .il / Stage 1 byte-equal | `jhyy_il_diff` |
| 验证自举闭环 (v1→v2→v3 byte-equal) | `jhyy_selfhost_check` |
| 搜 workarounds / "W-XXX 状态?" | `jhyy_workarounds` |
| 列出 / 读示例代码 | 资源 `jhyy://examples` |
| 读最新 changelog | 资源 `jhyy://changelog` |

## 严禁走旁路

| ❌ 别这样做 | ✅ 改用 |
|------------|--------|
| `Bash("jhyy.exe compile foo.jhyy && ./foo")` | `jhyy_run` |
| `Bash("python regress*.py")` 跑回归 | `jhyy_regress` |
| `Bash("sha256sum *.il")` 比 .il | `jhyy_il_diff` |
| 手写 bash chain 跑 v1→v2→v3 验证 | `jhyy_selfhost_check` |
| `grep -A 5 "W-XXX" docs/internal/workarounds.md` | `jhyy_workarounds` |
| `Read("docs/abis/jhyy-lang-spec-v0.2.1.md")` 答语法问题 | `jhyy_lang_ref` |
| `Read("compiler/build/bin/foo.il")` 看 IL | `jhyy_get_il` |
| `Bash("cat ...il")` 抄 IL 出来 | `jhyy_get_il`（直接返回文本） |
| `Read("docs/internal/workarounds.md")` 查 W-XXX | `jhyy_workarounds` |
| 手动 `subprocess.run([...])` 走 subprocess | 永远走 MCP 工具 |

## 触发示例

- "写个 fib(30) 跑一下" → 写文件 → `jhyy_run`
- "这段 .jhyy 语法对吗" → `jhyy_check`
- "改完 codegen，看看 IL 长啥样" → `jhyy_get_il`
- "JHYY 的 struct 怎么按值传" → `jhyy_abi_info`（不要去翻 ABI markdown）
- "match 支持范围模式吗" → `jhyy_lang_ref`
- "回归还稳吗" → `jhyy_regress`（默认 enforce_baseline_hash=True 防 phantom binary）
- "v1.il 跟 v2.il 还一致吗" → `jhyy_il_diff`（一次返回 sha + 行数 + 首差异 context）
- "自举闭环还在吗" → `jhyy_selfhost_check`（一键 v1→v2→v3→v4 byte-equal）
- "W-005 现在状态" → `jhyy_workarounds("W-005")`（不用 grep workarounds.md）

## MCP 不稳定时的回退

如果 `jhyy_*` 工具调用失败（ModuleNotFoundError、Connection refused、timeout 等），按以下顺序回退：

1. **编译/运行类**（`jhyy_run` / `jhyy_compile` / `jhyy_check`）：用 Bash 直接调 `compiler/build/bin/jhyy.exe`
2. **查 IL**（`jhyy_get_il`）：用 `Read("compiler/build/bin/<name>.il")` 或 `Bash("cat ...")`
3. **查语言规范 / ABI**（`jhyy_lang_ref` / `jhyy_abi_info`）：用 `Read("docs/abis/jhyy-lang-spec-v0.2.1.md")` 等对应文档
4. **报错给用户**："MCP 不可用，已用回退方式完成。如果持续失败检查 `~/.claude.json` 的 `jhyy` 配置和 Python `mcp[cli]` 是否安装"
