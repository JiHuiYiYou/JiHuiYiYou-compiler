# JHYY Installer (v1.5+)

Windows 引导式安装器 — 把 JHYY 编译器装到 `C:\Program Files\JHYY\`, 自动配 PATH, 用户零配置。

## 当前状态 (v1.5.2)

✅ **v1.5.2 done** — `compiler/jhyy-compiler.wxs` 写出, `build.ps1 compiler` 跑通, `jhyy-compiler-1.0.0.msi` (991KB) 生成, **`wix msi validate` 0 ICE errors** (ICE43/ICE57/ICE80 全过).

**v1.5.2 scope (已完成)**:
- jhyy.exe + qbe.exe → `C:\Program Files\JHYY\bin\`
- 系统 PATH (HKLM, per-machine) 自动加 `bin/`
- HKLM `SOFTWARE\JiHuiYiYou\JHYY` 写 InstallDir + Version
- 开始菜单 shortcut (HKCU registry KeyPath, per ICE43/57)
- 双语 RTF license (中英)
- 中文 UI strings (`Locale.zh-CN.wxl`)
- Launch condition 检测 MSYS2 + GCC (warn only, 不 block install — `力度 1 检测+引导` per user 决策)
- WiX 4 语法 (`<Package>` 顶层 `<Launch>`, `Bitness="always64"`, `<String Value="..."/>`, `<ui:WixUI>`)
- 64-bit Package (via `wix build -arch x64`, per ICE80)

**未完成** (后续 sprint):
- v1.5.3: `Bundle.wxs` (Burn bundle 链 compiler MSI + 检测 + 自动装 MSYS2)
- v1.5.4: UI 装修 + VSCode ext 组件
- v1.5.5: GH Actions release workflow + 第三方 manifest

**v1.5.2 install verification status**:
- ✅ `wix msi validate` clean (all standard ICEs pass)
- ⚠️ **手动 install/uninstall 验证需要在交互式 desktop session 跑** (per-machine MSI 要求 UAC elevation, headless bash 里 `Start-Process -Verb RunAs` 不会触发 prompt). 验证步骤:
  ```powershell
  # 交互式 PowerShell (有 desktop 的话)
  msiexec /i installer/build-artifacts/jhyy-compiler-1.0.0.msi /passive /l*v install.log
  # 期望: UAC prompt → accept → 文件装到 C:\Program Files\JHYY\bin\, PATH 自动加
  where jhyy  # → C:\Program Files\JHYY\bin\jhyy.exe
  jhyy --version  # → 1.4.6 (or current)
  # 卸载 (Settings → Apps 或 msiexec /x)
  ```

## 目录结构

```
installer/
├── build.ps1             ← PowerShell 编排 (v1.5.1 起)
├── _stub/                ← minimal smoke test (v1.5.1)
│   ├── stub.wxs          ← minimal Package definition
│   └── stub.msi          ← build 产物 (gitignored, build 后存在)
├── common/               ← 共享资源 (license + bitmap)
│   └── license.rtf       ← 双语 license (中英)
├── compiler/             ← v1.5.2 主 MSI (done)
│   ├── jhyy-compiler.wxs ← Package / Feature / Component definitions
│   └── Locale.zh-CN.wxl  ← 中文 UI string
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

### Compiler MSI build (v1.5.2)

```powershell
# 拷贝 jhyy.exe + qbe.exe → installer/build-artifacts/bin/, 编译 MSI
powershell -File installer/build.ps1 compiler
# 期望: [OK] installer/build-artifacts/jhyy-compiler-1.0.0.msi built (991KB)

# 验证 (走全部 standard ICE)
wix msi validate installer/build-artifacts/jhyy-compiler-1.0.0.msi
# 期望: 无 output, exit 0 (all ICEs pass)
```

### 产物

- `installer/_stub/stub.msi` (~28KB) — minimal stub, 不参与实际 installer
- `installer/build-artifacts/jhyy-compiler-X.Y.Z.msi` (~991KB) — 主 MSI, 装 jhyy.exe + qbe.exe
- `installer/build-artifacts/*.wixpdb` — WiX 调试符号 (gitignored)

## v1.5.3+ 计划

v1.5.3 写 `Bundle.wxs` (Burn bundle), 自动检测 MSYS2 + GCC, 没装则引导用户装。v1.5.4 加 UI 装修 + VSCode ext 组件, v1.5.5 加 GH Actions release workflow + 第三方 manifest。预期产物 `jhyy-installer-X.Y.Z.exe` (Burn bundle, 链 compiler MSI + 可选 MSYS2 检测逻辑)。

## 关联文档

- [`docs/plans/v1/v1.5.0任务清单 + 概要设计.md`](../docs/plans/v1/v1.5.0任务清单 + 概要设计.md) — 完整 5-sprint 计划 + 决策点
- [`docs/internal/build.md`](../docs/internal/build.md) — 编译器构建 (本 README 是 installer 构建)

## 工具链决策

- **PowerShell 不是 .cmd**: WiX 4/7 官方文档示例走 PowerShell, 现代 Windows dev convention 通用; MSYS2 bash 调 .cmd 时 arg passing 有 quirk, .ps1 更稳。
- **WiX 4/7 不是 WiX 3**: `wix build` CLI 取代 v3 的 candle + light + burn 三步, 一行命令搞定。
- **`wix.toml` 不存在**: plan 列了但 WiX 4/7 不需要 (那是 MSBuild 风格, CLI 路径走 `wix build` 加 -d / -b 参数即可)。
- **code signing 推到 v2.x**: v1.5.0 ship 时不签 Authenticode, 用户看到 "Unknown Publisher" warning, 文档告诉用户 "More info → Run anyway"。
