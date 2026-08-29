# JHYY VS Code Extension (`jhyy-lang`)

VS Code 语言扩展 — `.jhyy` 文件的语法高亮 + 原生 run / compile 命令。

> **Last updated**: v1.8.3 (2026-08-29) — `jhyy-lang-1.8.3.vsix` shipped,跟 compiler v1.8.3 / installer v1.8.3 / `.jhyy` 文件图标闭环(per installer v1.8.1 windres embed 修复)。最新 vsix 见 [`installer/build-artifacts/jhyy-lang-1.8.3.vsix`](../installer/build-artifacts/)。

## 定位

| 能力 | 实现 |
|------|------|
| **语法高亮** | TextMate grammar (`syntaxes/jhyy.tmLanguage.json`) — 关键字 / 字面量 / 类型 / 注释 / FFI / 运算符 |
| **文件图标** | `.jhyy` 文件在 Explorer 显示品牌图标(navy `#1a1a2e` + mint `#00d4aa`,来源 `icon.png` / `icon.svg`)|
| **原生 runFile 命令** | `jhyy.runFile` (Ctrl+F5) — 编译并跑当前 `.jhyy` 文件,在 JHYY 集成终端输出 |
| **原生 compileOnly 命令** | `jhyy.compileOnly` — 仅编译,不运行(用于 codegen 调试) |
| **快捷键** | Ctrl+F5 在 `.jhyy` 文件激活时绑 `jhyy.runFile`(可在 VSCode Keyboard Shortcuts 覆盖) |

> **不包含**: 调试器 / LSP server / IntelliSense / hover 文档 — 这些是 v2.x / v3.x 后续 sprint(v3.x 才有 inline asm 调试需求)。

## 当前版本

| 文件 | 版本 | 备注 |
|------|------|------|
| [`vscode-ext/package.json`](package.json) | `0.1.0`(manifest 模板, **不动**)| 这是 vsce manifest 的内部 version 字段,**由 [`installer/vscode-ext/package.ps1`](../installer/vscode-ext/) 在 build 期间按 `JHY_VERSION` 注入到 `.vsix` 的 `package.json`**。`package.json` 本身不修改 — 它是单 canonical source,vsix 内部 version 跟 compiler/installer 对齐(v1.8.x vsix → `1.8.3`)。 |
| [`installer/build-artifacts/jhyy-lang-1.8.3.vsix`](../installer/build-artifacts/) | `1.8.3` | shipped via GH Actions release workflow |
| [`vscode-ext/jhyy-lang-*.vsix`](.) | 0.1.0 → 1.8.3 | 历史 build 残留(`vsce package` 各次 ship 的本地副本,gitignored 但因 `vscode-ext/` 误 commit 留下 9 个版本) |

> **历史 vsix**: `vscode-ext/jhyy-lang-*.vsix` 9 个版本(`0.1.0` / `1.5.6` / `1.5.7-rc1` / `1.5.7` / `1.5.8` / `1.5.9` / `1.5.10` / `1.8.0` / `1.8.3`)是开发期 `vsce package` 误 commit,应 gitignore 但实际跟踪,v2.0 sprint 启动前清理。

## 命令清单

| 命令 ID | 标题 | 图标 | 快捷键 |
|---------|------|------|--------|
| `jhyy.runFile` | Run JHYY File | `$(play)` | Ctrl+F5 |
| `jhyy.compileOnly` | Compile JHYY File (no run) | `$(tools)` | (无默认键绑定) |

两个命令都在 `.jhyy` 文件激活时出现在编辑器标题栏(`editor/title` menu group,`when: resourceExtname == .jhyy`),runFile 还出现在 run group。

## 配置项

`settings.json` 加 `jhyy.*` 段:

| 配置键 | 默认值 | 说明 |
|--------|--------|------|
| `jhyy.run.executor` | `"jhyy run"` | 编译运行命令模板;`{file}` 占位符替换为绝对路径 |
| `jhyy.run.executorPath` | `""` | `jhyy.exe` 绝对路径;空 = 用 PATH(推荐);填 = 覆盖 PATH |
| `jhyy.run.terminalName` | `"JHYY"` | 复用终端名(避免每次 Ctrl+F5 开新 tab) |
| `jhyy.run.saveBeforeRun` | `true` | 跑前保存 dirty doc |

例:在 `settings.json` 自定 executor 走 `compiler/build/bin/jhyy.exe`:
```json
{
  "jhyy.run.executorPath": "C:/Users/liuzhen/Desktop/coding/JiHuiYiYou/compiler/build/bin/jhyy.exe",
  "jhyy.run.executor": "{executorPath} run {file}"
}
```

## 安装方式

### 方法 1: 手动 install(开发期)

```powershell
# 在 VSCode integrated terminal 或 PowerShell
code --install-extension C:\path\to\JiHuiYiYou\installer\build-artifacts\jhyy-lang-1.8.3.vsix
# 验证:
code --list-extensions | Select-String jhyy
# => jhyy.jhyy-lang
```

### 方法 2: installer 自动装(用户级)

走 [`installer/`](../installer/) — MSI post-install RunOnce (`install-configure-all.bat`) inline `code --install-extension` 自动跑。**Win10 22H2+ 上 v1.5.10 之前有 bug**(W-062),v1.8.2 起改走自定 ProgId `JHYY.SourceFile`(不依赖 `code` CLI),v1.8.3 起 SYSTEM-context CustomAction + 3-attempt fallback 闭环。

### 方法 3: VSCode Marketplace(未来)

> **deferred v2.x** — 当前未 publish 到 [VSCode Marketplace](https://marketplace.visualstudio.com/);v2.x 决定 publish 还是继续 ship-only-via-installer。

## 从源码 build

```powershell
# 前置: Node.js + npm (v18+) + @vscode/vsce
cd vscode-ext
npm install           # 装 @types/vscode + typescript 等 devDeps
npx tsc               # 编译 src/extension.ts → out/extension.js
npx vsce package      # 产 jhyy-lang-<version>.vsix (默认用 package.json version, v1.8.x 由 installer/vscode-ext/package.ps1 注入)
```

或者用 installer 一行 build:

```powershell
# 在项目根
powershell -File installer/build.ps1 bundle
# 自动: build jhyy.exe → compile vscode-ext → 注入 version → 产 jhyy-lang-X.Y.Z.vsix
```

## 目录结构

```
vscode-ext/
├── package.json              # vsce manifest (version 0.1.0, vsix 内部 version 由 build script 注入)
├── package-lock.json         # 依赖锁
├── tsconfig.json             # TypeScript 编译配置
├── .vscodeignore             # vsce package 排除规则
├── icon.png / icon.svg       # 品牌图标(Explorer 显示 + marketplace listing)
├── src/
│   └── extension.ts          # 入口 — 注册 runFile + compileOnly commands + TextMate grammar binding
├── syntaxes/
│   └── jhyy.tmLanguage.json  # TextMate grammar (scope: source.jhyy)
├── out/                      # tsc 编译产物 (gitignored)
│   └── extension.js
├── node_modules/             # npm install 产物 (gitignored)
└── *.vsix                    # 历史 vsce package 误 commit 残留 (gitignored but actually tracked)
```

## 与 installer / compiler 闭环

| 工具 | 角色 | 来源 |
|------|------|------|
| `compiler/src/*.c` / `compiler/src0/*.jhyy` | 编译 `.jhyy` → `.exe` | 仓库内 |
| `compiler/build/bin/jhyy.exe` | 编译产物(C 端) | `make` 或 `installer/build.ps1 compiler` 触发 |
| `installer/common/jhyy-setuc/` | .NET 8 CLI,写 UserChoice hash | 仓库内 |
| `installer/build-artifacts/jhyy-lang-1.8.3.vsix` | VSCode ext 装包 | `installer/vscode-ext/package.ps1` build |
| VSCode Marketplace(未来 v2.x)| publish 入口 | deferred |

详细见 [`docs/internal/build.md`](../docs/internal/build.md) § 构建 + [`installer/README.md`](../installer/README.md) § v1.8.x。

## 已知 limitation

- ❌ 无 LSP server(IntelliSense / hover / go-to-def) — v2.x / v3.x 加
- ❌ 无调试器 — v3.x OS sprint 加(配合 `jhyy_OS` Debug ABI per `../jhyy_OS/docs/v0.0.4-debug-abi.md`)
- ⚠️ `package.json` version `0.1.0` 不修改 — vsix 内部 version 注入逻辑在 `installer/vscode-ext/package.ps1`,改 `package.json` 会导致 `vsce package` 默认行为走 0.1.0 而非 installer 注入
- ⚠️ `vscode-ext/*.vsix` 历史误 commit 9 个版本未清理 — v2.0 sprint 启动前 `git rm` + `.gitignore` 加 `*.vsix` 例外处理

## 关联文档

- [`installer/README.md`](../installer/README.md) — installer v1.8.x 节(W-062/W-063 闭环)
- [`docs/internal/build.md`](../docs/internal/build.md) — 从源码 build vscode-ext 步骤
- [`docs/logs/v1/changelog-v1.8.0.md`](../docs/logs/v1/changelog-v1.8.0.md) — v1.8.x 完整 changelog(vscode-ext 改动在 § v1.8.1 `windres` embed + § v1.8.2 ProgId 路径)