# vscode-ext — JHYY VS Code 扩展（`jhyy-lang`）

> `.jhyy` 文件的语法高亮 + 原生 run / compile 命令。

---

## 功能

| 能力 | 说明 |
|---|---|
| 语法高亮 | TextMate grammar（`source.jhyy`） |
| ▶ `Run JHYY File` | 编译并运行当前 `.jhyy`；快捷键 `Ctrl+F5` |
| ⚙ `Compile JHYY File (no run)` | 只编译不运行 |

两个命令都在 `.jhyy` 文件激活时出现在编辑器标题栏（`editor/title` 菜单组，
条件 `resourceExtname == .jhyy`），`Run` 还会出现在 run 组。

> **不含**：调试器 / LSP server / IntelliSense / hover 文档。

---

## 配置项

| 键 | 作用 |
|---|---|
| `jhyy.run.executor` | 调用的可执行文件（默认 `jhyy`） |
| `jhyy.run.executorPath` | 可执行文件的完整路径（覆盖 `executor`） |
| `jhyy.run.terminalName` | 集成终端的名字 |
| `jhyy.run.saveBeforeRun` | 运行前先保存 |

---

## 打包

```powershell
# 版本号取自 $env:JHY_VERSION（发版时由 installer/build.ps1 传入）
powershell -NoProfile -ExecutionPolicy Bypass -File installer/vscode-ext/package.ps1
```

⇒ 产出 `jhyy-lang-<版本>.vsix`。

⚠️ `package.json` 里的 `"version": "0.1.0"` 是 **manifest 模板的内部字段，不动**
—— 打包时脚本按 `$JHY_VERSION` 原地替换它（避免 JSON 重排版污染 diff）。

**版本号与产物名见 [`docs/internal/FACTS.md`](../docs/internal/FACTS.md) § 1。**

---

## 终端 / bash

VSCode 的终端 profile 指向**探测到的** bash（不是 VSCode 自带那个写死路径的
`bash (MSYS2)` profile —— 它**不会**回落到别的 bash）。探测顺序：
`$env:MSYS2_ROOT` → `C:\msys64` → MSYS2 注册表的 `InstallLocation`
→ Git for Windows → PATH。探测不到就**不改用户的 VSCode 设置**。

安装器还会装一个 `jhyy-bash.cmd`（`<INSTALLDIR>\bin\`）—— 自己找 bash 并启动，
顺带把 `JHYY\bin` 塞进 PATH 并设 `MSYS2_PATH_TYPE=inherit`。

门：`installer/scripts/verify-vscode-bash-detect.ps1`。
设计说明 ⇒ [`installer/toolchain/README.md`](../installer/toolchain/README.md) § 二期结论。

---

## 相关

- 安装器 ⇒ [`installer/README.md`](../installer/README.md)
- 语言规范（语法高亮要对着它写）⇒ [`docs/abis/jhyy-lang-spec-v4.0.0.md`](../docs/abis/jhyy-lang-spec-v4.0.0.md)
