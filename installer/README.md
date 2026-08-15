# JHYY Installer (v1.5+)

Windows 引导式安装器 — 把 JHYY 编译器装到 `C:\Program Files\JHYY\`, 自动配 PATH, 用户零配置。

## 当前状态 (v1.5.5)

✅ **v1.5.2 done** — `compiler/jhyy-compiler.wxs` 写出, `build.ps1 compiler` 跑通, `jhyy-compiler-1.0.0.msi` (991KB) 生成, **`wix msi validate` 0 ICE errors** (ICE43/ICE57/ICE80 全过).

✅ **v1.5.3 done** — `Bundle.wxs` 写出, `build.ps1 bundle` 跑通, `jhyy-installer-1.5.3.exe` (1.6MB) 生成。Burn bundle 走 standard `WixStandardBootstrapperApplication` UI (next-next-finish, RTF license, MSYS2 prereq 提示在 Welcome page, post-install 提示在 Success page)。

✅ **v1.5.4 done** — VSCode ext auto-install (`.vsix` + CustomAction `code --install-extension`), `.jhyy` file association (双击 → `jhyy run file.jhyy`), Start Menu 增强 (Documentation / Quick Start 走 Internet Shortcut `.url`)。`wix msi validate` 0 ICE errors。

✅ **v1.5.5 done** — GitHub Actions release workflow (`.github/workflows/release.yml`, tag `v*` + manual `workflow_dispatch`), 第三方 manifest reference (winget 3 文件 + scoop 1 文件, schema 校验通过, no actual publish), `installer/gen-sha256.ps1` 写 SHA256.txt, `installer/changelog-template.md` Release notes 模板。`tag v*` push → 自动 build + upload + Release; RC tag 自动 mark prerelease; workflow_dispatch dry-run 入口作为 escape hatch。

**v1.5.5 scope (已完成)**:
- `.github/workflows/release.yml` — GH Actions release workflow (14 steps: checkout + MSYS2 + WiX + make stage0 + make + regress + bundle + SHA256 verify + release notes + MSI validate + release create + dry-run summary)
- `installer/gen-sha256.ps1` — SHA256.txt 生成 (sha256sum-compatible 格式, UTF-8 no BOM); `build.ps1 bundle` 自动调
- `installer/changelog-template.md` — Release notes 模板 (VERSION / ISO_DATE / URL 占位符)
- `installer/winget/manifests/j/JiHuiYiYou/JHYY/1.5.5/` — winget multi-file manifest (version + installer + locale en-US); InstallerSha256 在 release 时由 CI 填
- `installer/scoop/jhyy.json` — scoop manifest v3 schema (Burn bundle install + shortcuts + autoupdate)
- 关键 fix: bash `${VERSION}` 占位符在 MSYS2 bash 不展开 → 改 `${{ env.VERSION }}` ($env:VERSION in pwsh); `Add-Content` 写 GH Actions env file (no BOM 比 Out-File -Encoding utf8 稳)

**v1.5.4 scope (已完成)**:
- `installer/vscode-ext/package.ps1` — VSCode ext 打包 (vsce package + version patch)
- `installer/common/install-vsix.bat` — 检测 `code` 命令 + 装 .vsix 脚本 (CustomAction deferred 调用)
- `installer/common/JHYY Documentation.url` + `JHYY Quick Start.url` — Internet Shortcut files (MSI Shortcut.Target 不允许 URL, 用 .url 文件)
- `installer/compiler/jhyy-compiler.wxs` 新增 ComponentGroups: `JHYYVSCodeExt` (.vsix payload), `JHYYFileAssoc` (HKCR\.jhyy ProgID + shell\open\command), `JHYYURLShortcuts` (.url files)
- CustomAction `InstallVSCodeExt` (deferred, after InstallFiles, Return="ignore", ComSpec registry search)
- `build.ps1 compiler` 自动 chain vsce package + 准备 vscode-ext/ bindpath
- 关键 fix: WiX 4 ICE03 (`Invalid registry path` — leading backslash 不允许, `\.jhyy` 改 `.jhyy`); ICE03 (`Bad shortcut target` — URL 不允许, 改用 Internet Shortcut `.url` 文件); RegistryKey Id 需 `ForceCreateOnInstall="yes"` 才允许 attribute; RemoveRegistryValue 无 `Action` attribute

**v1.5.3 scope (已完成)**:
- `installer/Bundle.wxs` — Burn bundle, 链 `JHYYCompilerMsi` (v1.5.2 MSI)
- `installer/Theme.xml` — Burn custom theme (Welcome/Progress/Modify/Success/Failure page, MSYS2 prereq 提示 + https://www.msys2.org/ 链接)
- `installer/Bundle.zh-CN.wxl` — 中文 UI strings (跟 v1.5.2 Locale 同步)
- `installer/banner.bmp` — 256x64 24-bit logo BMP (Burn 内部转 PNG)
- `installer/common/license.rtf` — 双语 RTF license (Burn + MSI 共享)
- `build.ps1 bundle` 入口 (chain compiler MSI build if missing)
- `wix build -arch x64` (per ICE80 一致性)
- Theme=`rtfLicense` + LicenseFile=`license.rtf` 配 RTF license dialog
- 关键 fix: `<bal:WixStandardBootstrapperApplication>` 必须在 `<BootstrapperApplication>` wrapper 内 (per BalCompiler.cs ParsePossibleKeyPathElement case "BootstrapperApplication"), 缺 `Theme` 属性 → WIX0010; Theme enum 选 `rtfLicense` (跟 RTF LicenseFile 配套)

**v1.5.3 design decisions**:
- **力度 1 检测+引导** (per user 决策 2026-08-14): Burn 不打包 GCC toolchain (~85MB 太重, 不在 v1.5 scope); 检测 MSYS2 + ucrt64 GCC, 装了 → 正常装 compiler MSI; 没装 → Welcome page 提示用户先装 MSYS2 (https://www.msys2.org/); 装完 compiler MSI 后, Success page 提示: "装 MSYS2 后用 jhyy 编 .jhyy"
- **Bundle 走 standard WixStdBA UI** (不再写 custom BAFunctions): simple, 文档化, 跨版本稳; 留给 v1.5.4 装修 + v2.x BAFunctions 升级
- **Bal extension DLL 通过绝对路径引** (workaround): `wix extension add -g WixToolset.Bal.wixext` 装的 DLL 文件名是 `WixToolset.BootstrapperApplications.wixext.dll` (不是 `WixToolset.Bal.wixext.dll`), wix CLI 7.0.0+b8977d6 的 `-ext WixToolset.Bal.wixext` 名字查找会 WIX0144 fail, workaround 是 -ext 传 DLL 绝对路径。详细见 `docs/internal/workarounds.md`

**未完成** (后续 sprint):
- v1.5.5: GH Actions release workflow + 第三方 manifest (winget / scoop / choco) + SHA256

**v1.5.4 install verification status**:
- ✅ `wix msi validate` clean (all standard ICEs pass)
- ✅ Burn bundle manifest 验证 (内嵌 MSI / theme.xml / thm.wxl / logo.png / license.rtf / wixstdba.exe payload 全部齐全 + .vsix chain via MSI embedded payload)
- ⚠️ **手动 install/uninstall 验证需要在交互式 desktop session 跑** (per-machine MSI 要求 UAC elevation, headless bash 里 `Start-Process -Verb RunAs` 不会触发 prompt). 验证步骤:
  ```powershell
  # 交互式 PowerShell (有 desktop 的话)
  jhyy-installer-1.5.4.exe  # 双击也行, Burn 弹 welcome dialog
  # 期望: Welcome → Install → UAC → Progress → Success → Close
  # 期望 (post-install):
  #   1. where jhyy  → C:\Program Files\JHYY\bin\jhyy.exe
  #   2. jhyy --version  → 1.5.4
  #   3. 双击 hello.jhyy  → jhyy.exe run (file association)
  #   4. code --list-extensions  → 含 jhyy.jhyy-lang (VSCode ext 自动装, 若有 code)
  #   5. Start Menu → JHYY → Documentation / Quick Start / Compiler
  # 卸载 (Settings → Apps 或 Burn /uninstall)
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
├── vscode-ext/           ← v1.5.4 done (VSCode extension)
│   ├── package.ps1       ← vsce package 脚本
│   ├── jhyy-lang-X.Y.Z.vsix  ← build 产物 (gitignored)
│   └── (build 完产物在 installer/build-artifacts/)
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
- `installer/build-artifacts/jhyy-compiler-X.Y.Z.msi` (~995KB) — 主 MSI, 装 jhyy.exe + qbe.exe + .vsix + file association + Start Menu
- `installer/build-artifacts/jhyy-installer-X.Y.Z.exe` (~1.6MB) — Burn bundle (installer wrapper)
- `installer/build-artifacts/jhyy-lang-X.Y.Z.vsix` (~4KB) — VSCode extension
- `installer/build-artifacts/*.wixpdb` — WiX 调试符号 (gitignored)
- `installer/SHA256.txt` — 3 产物 SHA256 (gitignored; build 完自动生成)

## v1.5.5+ 发布流程

### 本地 build (任意版本)

```powershell
# 单一入口
JHY_VERSION=1.5.5 powershell -File installer/build.ps1 bundle
# 期望产出: installer/build-artifacts/jhyy-installer-1.5.5.exe + jhyy-compiler-1.5.5.msi + jhyy-lang-1.5.5.vsix + SHA256.txt
```

### GitHub Actions — tag 触发 (正式 release)

```bash
git tag v1.5.5
git push origin v1.5.5
# GH Actions 自动: build jhyy.exe → regress → build.ps1 bundle → SHA256 → release notes → upload 4 assets → create GitHub Release
# 期望: GitHub Release "JHYY 1.5.5" 标 latest, 4 个 asset (.exe / .msi / .vsix / SHA256.txt)
```

### GitHub Actions — RC dry-run (workflow_dispatch)

```bash
gh workflow run release.yml -f version=1.5.5-rc1 -f dry_run=false
# 期望: GH Release "JHYY 1.5.5-rc1 [RC]" 标 prerelease
```

### GitHub Actions — 完全 dry-run (build 闭环, 不上传)

```bash
gh workflow run release.yml -f version=1.5.5-rc1 -f dry_run=true
# 期望: build 跑通 + SHA256 生成, 但不 upload 不 create release; summary 在 GH Actions UI
```

### 第三方 manifest publish (deferred v2.x)

- **winget**: `installer/winget/manifests/j/JiHuiYiYou/JHYY/${VERSION}/` 3 文件 — 实际 PR 到 [winget-pkgs](https://github.com/microsoft/winget-pkgs) 推到 v2.x
- **scoop**: `installer/scoop/jhyy.json` — 实际 PR 到 [ScoopInstaller/Main](https://github.com/ScoopInstaller/Main) 推到 v2.x

⚠️ **Manifest 文件是 reference (no publish)**: 当前 CI 仅生成 SHA256.txt 给 Release asset; manifest 文件的 `InstallerSha256` 字段是 `<FILL_AT_RELEASE_TIME_FROM_SHA256.txt>` placeholder, 推 v2.x 前需要 (a) 真发布 GUID 替换 dev placeholder + (b) CI step 读 SHA256 填 manifest + (c) manifest 跟 release 同 PR。

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
