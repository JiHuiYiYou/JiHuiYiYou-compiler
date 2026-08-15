# JHYY Installer (v1.5+)

Windows 引导式安装器 — 把 JHYY 编译器装到 `C:\Program Files\JHYY\`, 自动配 PATH, 用户零配置。

## 当前状态 (v1.5.1)

**只完成 toolchain smoke test** — 装好 WiX 4/7 (`dotnet tool install --global wix`), 建好目录结构, `build.ps1` 跑通一个 minimal `stub.msi` (~28KB) 验证 WiX 工具链 + .wxs 语法 baseline。

**未完成** (后续 sprint):
- v1.5.2: 写 `compiler/jhyy-compiler.wxs` (主 MSI 定义)
- v1.5.3: 写 `Bundle.wxs` (Burn bundle 链 compiler MSI)
- v1.5.4: UI 装修 + VSCode ext 组件
- v1.5.5: GH Actions release workflow + 第三方 manifest

## 目录结构

```
installer/
├── build.ps1             ← PowerShell 编排 (v1.5.1 起)
├── _stub/                ← minimal smoke test (v1.5.1)
│   ├── stub.wxs          ← minimal Package definition
│   └── stub.msi          ← build 产物 (gitignored, build 后存在)
├── common/               ← 共享资源 (license + bitmap)
│   └── license.rtf       ← 双语 license (中英)
├── compiler/             ← v1.5.2 待建 (jhyy-compiler.wxs 主 MSI)
├── vscode-ext/           ← v1.5.4 待建 (VSCode extension component)
├── os/                   ← jhyy_OS placeholder (后续 OS sprint 填)
│   ├── .gitkeep
│   └── README.md
└── README.md             ← 本文件
```

## 如何构建 (v1.5.1 现在能跑的部分)

### 前置

```powershell
# WiX 4/7 工具链 (一次性)
dotnet tool install --global wix
# PATH 持久化
setx PATH "$env:PATH;$env:USERPROFILE\.dotnet\tools"
# 验证
wix --version
# 期望: 7.0.0+ (实际我们 spot check 是 7.0.0+b8977d6)
```

### Smoke build

```powershell
# 从项目根
cd C:\path\to\JiHuiYiYou
powershell -File installer/build.ps1 stub
# 期望: [OK] installer/_stub/stub.msi built (28KB)
```

### 产物

- `installer/_stub/stub.msi` (~28KB) — minimal stub, 不参与实际 installer
- `installer/_stub/stub.wixpdb` — WiX 调试符号 (gitignored)

## v1.5.2+ 计划

v1.5.2 写 `compiler/jhyy-compiler.wxs` (Product / Package / Directory / Component / Feature), Files.wxs 映射 jhyy.exe + qbe.exe + binutils 子集, registry.wxs 写系统 PATH (HKLM, 要 admin)。预期产物 `jhyy-compiler-x.y.z.msi` (~35MB, 含 binutils)。

## 关联文档

- [`docs/plans/v1/v1.5.0任务清单 + 概要设计.md`](../docs/plans/v1/v1.5.0任务清单 + 概要设计.md) — 完整 5-sprint 计划 + 决策点
- [`docs/internal/build.md`](../docs/internal/build.md) — 编译器构建 (本 README 是 installer 构建)

## 工具链决策

- **PowerShell 不是 .cmd**: WiX 4/7 官方文档示例走 PowerShell, 现代 Windows dev convention 通用; MSYS2 bash 调 .cmd 时 arg passing 有 quirk, .ps1 更稳。
- **WiX 4/7 不是 WiX 3**: `wix build` CLI 取代 v3 的 candle + light + burn 三步, 一行命令搞定。
- **`wix.toml` 不存在**: plan 列了但 WiX 4/7 不需要 (那是 MSBuild 风格, CLI 路径走 `wix build` 加 -d / -b 参数即可)。
- **code signing 推到 v2.x**: v1.5.0 ship 时不签 Authenticode, 用户看到 "Unknown Publisher" warning, 文档告诉用户 "More info → Run anyway"。
