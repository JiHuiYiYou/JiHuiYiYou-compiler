# Changelog — v1.5.0 (umbrella: Windows installer)

> **承接**: v1.4.7 shipped (regress 三跑合并 + CI workflow 简化).
> **目标**: 用户下载 `jhyy-installer-X.Y.Z.exe` 双击 → next-next-finish 装好 jhyy + qbe.exe, 系统 PATH 自动配, 用户零配置。
> **scope**: WiX 4/7 + Burn bundle + MSI; Windows-only; per `docs/plans/v1/v1.5.0任务清单 + 概要设计.md`。
> **本 umbrella 涵盖 5 个 sprint**: v1.5.1 / v1.5.2 / v1.5.3 / v1.5.4 / v1.5.5, 各 sprint 状态如下。

---

## Sprint 状态总览

| Sprint | 状态 | Commit | 摘要 |
|--------|------|--------|------|
| **v1.5.1** | ✅ done | `73dd3cb` | WiX 4/7 工具链 + 项目结构 (`installer/` 目录 + `_stub/` smoke test) + `build.ps1` 编排 |
| **v1.5.2** | ✅ done | `165e650` | `compiler/jhyy-compiler.wxs` 写完; `wix msi validate` 0 ICE errors (ICE43/ICE57/ICE80 全过) |
| **v1.5.3** | ✅ done | `6ea1c62` | `Bundle.wxs` (Burn bundle) + `Theme.xml` + `Bundle.zh-CN.wxl` + `banner.bmp`; `jhyy-installer-1.5.3.exe` (1.6MB) 生成 |
| **v1.5.4** | ✅ done | (this commit) | VSCode ext auto-install + `.jhyy` file association + Start Menu Documentation/Quick Start 增强; `wix msi validate` 0 ICE errors |
| **v1.5.5** | ⏳ pending | — | GH Actions release workflow + 第三方 manifest (winget / scoop / choco) + SHA256 发布 |

---

## v1.5.3 — Burn bundle (本 commit)

### 完成定义

- ✅ `installer/Bundle.wxs` 写完 (Burn `<Bundle>` + `WixStandardBootstrapperApplication` + `<Chain>` 链 compiler MSI)
- ✅ `installer/Theme.xml` 写完 (Welcome/Progress/Modify/Success/Failure page, MSYS2 prereq 提示 + https://www.msys2.org/ 链接)
- ✅ `installer/Bundle.zh-CN.wxl` 写完 (中文 UI strings)
- ✅ `installer/banner.bmp` 生成 (256x64 24-bit BMP, Burn 内部转 PNG)
- ✅ `installer/common/license.rtf` (Burn + MSI 共享)
- ✅ `build.ps1 bundle` 入口 (自动 chain compiler MSI build if missing)
- ✅ `jhyy-installer-X.Y.Z.exe` 产物 (1.6MB, PE32+ x86-64 Windows GUI)
- ✅ Burn bundle manifest 验证 (wix-burndata.xml: MSI / theme.xml / thm.wxl / logo.png / license.rtf / wixstdba.exe payload 全部齐全)
- ⚠️ 手动 install verification 留 v1.5.5 release 验证 (per-machine MSI 要 UAC elevation, headless bash 触发不了 prompt)

### 核心机制

- **Burn bundle 结构**: `<Bundle>` 顶层 + `<BootstrapperApplication>` wrapper + `<bal:WixStandardBootstrapperApplication>` child (per WiX 4 / BalCompiler.cs ParsePossibleKeyPathElement case "BootstrapperApplication" 要求 BA 子元素必须在 wrapper 内)
- **`Theme="rtfLicense"`** 配 `LicenseFile="license.rtf"` (RTF license dialog); 可选 `ThemeFile="Theme.xml"` 覆盖默认布局加 MSYS2 提示
- **`wix build -arch x64`** 一致性 (Bundle 跟 MSI 都是 64-bit)
- **Bal extension DLL 通过绝对路径引** (workaround): `wix extension add -g WixToolset.Bal.wixext` 装的 DLL 文件名是 `WixToolset.BootstrapperApplications.wixext.dll` (不是 `WixToolset.Bal.wixext.dll`), wix CLI 7.0.0+b8977d6 的 `-ext WixToolset.Bal.wixext` 名字查找会 WIX0144 fail, workaround 是 -ext 传 DLL 绝对路径。详细见 `docs/internal/workarounds.md`
- **力度 1 检测+引导** (per user 决策 2026-08-14): Burn 不打包 GCC toolchain; Welcome page 提示用户先装 MSYS2; Success page 提示 post-install 步骤
- **`JHYY_BUNDLE_INSTALL=1`** MsiProperty 传到 MSI (让 MSI 知道被 Burn chain 装的, 可以用来调 UI/behavior; 当前 MSI 不读这 property, 留作未来扩展)

### Bundle 体积拆分 (v1.5.3)

| Payload | 大小 | 说明 |
|---------|------|------|
| Burn stub (wixstdba.exe) | ~600KB | Bal extension native exe (标准 BA) |
| `jhyy-compiler-X.Y.Z.msi` (embedded) | 991KB | v1.5.2 主 MSI |
| `license.rtf` (embedded) | ~50KB | 双语 RTF |
| `theme.xml` (embedded) | ~5KB | Burn custom theme |
| `thm.wxl` (embedded) | ~3KB | 中文 localization |
| `logo.png` (embedded, BMP→PNG 自动) | ~3KB | banner 图像 |
| Bundle stub / metadata | ~50KB | Burn engine stub |
| **总计** | **~1.6MB** | 不含 GCC toolchain (力度 1 决策) |

### Plan / Sprint / 文件改动

| 文件 | 改动 |
|------|------|
| `installer/Bundle.wxs` | NEW (113 行) — Burn bundle definition |
| `installer/Theme.xml` | NEW (113 行) — Burn custom theme |
| `installer/Bundle.zh-CN.wxl` | NEW (60 行) — 中文 UI strings |
| `installer/banner.bmp` | NEW (49KB, 256x64 24-bit) — banner logo |
| `installer/build.ps1` | +49 / -3 行 — bundle 入口 + Bal extension 路径 workaround |
| `installer/README.md` | +36 / -17 行 — v1.5.3 status + bundle build 步骤 + Bundle 验证说明 |

### 验证 (本 commit)

```
$ powershell -File installer\build.ps1 bundle
[build.ps1] target=bundle version=1.5.3
[build.ps1] === Burn bundle build (v1.5.3) ===
[build.ps1] compiler MSI missing, building first...
[OK] installer/build-artifacts/jhyy-compiler-1.5.3.msi built
[OK] installer/build-artifacts/jhyy-installer-1.5.3.exe built

$ file installer/build-artifacts/jhyy-installer-1.5.3.exe
PE32+ executable for MS Windows 6.00 (GUI), x86-64, ... 9 sections

$ # Bundle manifest 验证
$ unzip -p installer/build-artifacts/jhyy-installer-1.5.3.wixpdb wix-burndata.xml | head -c 2000
<BurnManifest ...>
  <Chain><MsiPackage Id="JHYYCompilerMsi" ... ProductCode="{A3614406-...}" Version="1.5.3" />
```

Bundle manifest 含:
- `<WixBundleProperties>` UpgradeCode=`B1C2D3E4-...`, DisplayName="JHYY Installer", Scope=perMachine
- `<WixStdbaInformation>` LicenseFile="license.rtf"
- `<Chain>` 1 MsiPackage "JHYYCompilerMsi" v1.5.3 + ProductCode=A3614406-...
- 6 个 UX payload (thm.xml / thm.wxl / logo.png / license.rtf / wixstdba.exe / BootstrapperApplicationData.xml)
- `WixAttachedContainer` (529KB) 嵌入 MSI

### 已知 workarounds (已入 `docs/internal/workarounds.md`)

- **W-001 Bal extension DLL 绝对路径引用**: WiX 7.0.0+b8977d6 CLI 的 `-ext WixToolset.Bal.wixext` 名字查找 WIX0144 fail (DLL 名是 `WixToolset.BootstrapperApplications.wixext.dll`, 不是预期命名), workaround 是 -ext 传 DLL 绝对路径。
- **W-XXX Bundle 验证留 release 阶段**: headless bash 无法跑 interactive install (per-machine MSI 要 UAC elevation); 完整 install/uninstall 验证推到 v1.5.5 release 时跑。

---

## v1.5.2 (commit `165e650`)

### 完成定义

- ✅ `installer/compiler/jhyy-compiler.wxs` 写完 (Package / Feature / 4 Components)
- ✅ `installer/compiler/Locale.zh-CN.wxl` 写完 (中文 UI strings)
- ✅ `installer/build.ps1 compiler` 入口
- ✅ `jhyy-compiler-X.Y.Z.msi` 产物 (991KB)
- ✅ **`wix msi validate` 0 ICE errors** (ICE43/ICE57/ICE80 全过, 全部 100+ ICEs clean)
- ✅ JhyyExe + QbeExe + JhyyExeShortcut + LicenseFile 4 个 Component (全 `Bitness="always64"` 一致性)
- ⚠️ 手动 install verification 留 v1.5.5 release 验证

### 核心机制

- **per-machine MSI** (Scope=perMachine, HKLM 写 PATH + registry, 需 admin)
- **Bitness="always64"** on all Components (per ICE80: Package 不能 mix 32-bit / 64-bit Components)
- **ICE43/ICE57 fix**: Start Menu shortcut Component 用 HKCU registry KeyPath (per-user data 不能配 file KeyPath)
- **Launch condition** 检测 MSYS2 + GCC (`Installed OR MSYS2_GCC_FOUND`, warn only 不 block install)
- **`wix build -arch x64`** 配所有 64-bit Components (per ICE80)

---

## v1.5.1 (commit `73dd3cb`)

### 完成定义

- ✅ WiX 4/7 工具链 (`dotnet tool install --global wix`) + `WixToolset.Util.wixext` + `WixToolset.UI.wixext`
- ✅ `installer/` 目录结构 (build.ps1 + _stub/ + common/ + compiler/ + os/ + vscode-ext/)
- ✅ `_stub/stub.wxs` minimal Package definition (smoke test)
- ✅ `installer/build.ps1` 编排 (stub / compiler / bundle 三 target)
- ✅ `_stub/stub.msi` 产物 (~28KB) — 验证 wix 工具链能跑

### 关键决策

- **PowerShell 不是 .cmd**: WiX 4/7 官方文档示例走 PowerShell; MSYS2 bash 调 .cmd 时 arg passing 有 quirk, .ps1 更稳
- **`wix build` CLI** 取代 v3 的 candle + light + burn 三步
- **`.gitignore` installer artifacts**: `installer/*.msi` / `*.exe` / `*.vsix` / `*.wixpdb` / `*.wixlib` 全部 gitignored (build 产物不入库)

---

## v1.5.4 — VSCode ext + File association + Start Menu 增强 (本 commit)

### 完成定义

- ✅ `installer/vscode-ext/package.ps1` — VSCode ext 打包 (vsce package + version patch)
- ✅ `installer/common/install-vsix.bat` — 检测 `code` 命令 + `code (with install-extension flag) <vsix>` 脚本 (CustomAction deferred 调用)
- ✅ `installer/common/JHYY Documentation.url` + `JHYY Quick Start.url` — Internet Shortcut files (绕开 ICE03 URL-not-allowed-in-shortcut)
- ✅ `installer/compiler/jhyy-compiler.wxs` 改完: 3 个新 ComponentGroup (`JHYYVSCodeExt` / `JHYYFileAssoc` / `JHYYURLShortcuts`) + CustomAction `InstallVSCodeExt` (deferred, after InstallFiles, Return="ignore")
- ✅ `build.ps1 compiler` 自动 chain vsce package + 准备 vscode-ext/ bindpath (`SKIP_VSIX=1` 跳过 escape hatch)
- ✅ `jhyy-installer-1.5.4.exe` (1.6MB Burn bundle) + `jhyy-compiler-1.5.4.msi` (995KB) + `jhyy-lang-1.5.4.vsix` (4KB) 3 产物齐
- ✅ **`wix msi validate` 0 ICE errors** (ICE03 / ICE43 / ICE57 / ICE80 全过)

### 核心机制

- **VSCode ext 自动装**: build.ps1 调 `package.ps1` → vsce 把 vscode-ext/ 打 .vsix + 改 version; MSI 把 .vsix 当 payload 装到 `INSTALLDIR\vscode-ext\`; CustomAction `InstallVSCodeExt` deferred (after InstallFiles) 调 `cmd /c install-vsix.bat /VSIX:...`; .bat 检测 `where code >nul 2>&1` 找不到就 silent skip (`code --install-extension` 没装直接退出); Return="ignore" 让装失败不阻塞 MSI (per-machine MSI 已经 admin elevation 过了)
- **`.jhyy` file association**: MSI ComponentGroup `JHYYFileAssoc` 写 `HKCR\.jhyy` (default=`JHYY.SourceFile`) + `HKCR\JHYY.SourceFile\shell\open\command` (default=`"[INSTALLDIR]bin\jhyy.exe" run "%1"`); 双击 .jhyy → jhyy.exe run. RegistryKey 用 `ForceCreateOnInstall="yes"` (WiX 4 Id 必备)
- **Start Menu 增强**: 3 个 shortcut (Compiler / Documentation / Quick Start); Docs / Quick Start 用 Internet Shortcut `.url` 文件 (WiX 4 ICE03 不允许 Shortcut.Target 是 URL); 写 `INSTALLDIR\common\JHYY Documentation.url` + `JHYY Quick Start.url` (Windows 认 `.url` 后缀自动用 default browser 打开)
- **CustomAction deferred**: WiX 4 要求 Property + ExeCommand 双 attribute; ComSpec 是 reserved property 改名 `JHYY_COMSPEC`; `<SetProperty>` 在 execute sequence 提前 define `InstallVSCodeExtCmd` property (deferred CA 无 property context)

### WiX 4 schema 关键 fix (踩坑)

| Error | Root cause | Fix |
|-------|-----------|-----|
| WIX0012 `Property ComSpec` (lowercase) | ComSpec 是 reserved | 改 `JHYY_COMSPEC` |
| WIX0144 `WixToolset.Util.wixext not found` | extensions uninstalled | `wix extension add -g WixToolset.Util.wixext` + UI |
| WIX0104 (XML comment `--` invalid) | `code --install-extension` XML 不允许 | 改 `code (with install-extension flag)` |
| WIX0037 CustomAction `ExeCommand` alone | WiX 4 要 Property + ExeCommand | 加 `<SetProperty>` |
| WIX0400 Custom element inner text `NOT Installed` | Condition 是 attribute | 改 `<Custom Action="..." Condition="..." />` |
| ICE03 `Invalid registry path` (`\.jhyy`) | RegPath 类型无 leading backslash | 改 `.jhyy` |
| ICE03 `Bad shortcut target` (URL) | Shortcut.Target 不允许 URL | 用 Internet Shortcut `.url` 文件 |
| WIX0037 RegistryKey Id without `ForceCreateOnInstall` | WiX 4 Id 必备 | 加 `ForceCreateOnInstall="yes"` |
| WIX0004 `RemoveRegistryValue` has `Action` | WiX 4 自动 remove | 删 `Action="removeOnUninstall"` |

### PowerShell 踩坑 (vsce package 脚本)

- **`$1` interpolation bug**: `'$1' + $env:JHY_VERSION + '$2'` 在 regex.Replace 替换字符串里 `$1` 被 PS 当变量解析为空; 改用 `MatchEvaluator` delegate `[regex]::Replace($content, 'pattern', { param($m) return '"version": "' + $env:JHY_VERSION + '"' })`
- **`ErrorActionPreference="Stop"` kills on vsce warnings**: vsce 写 warning 到 stderr → PowerShell RemoteException → Stop 模式下 script 死; vsce 调用前后包 `$ErrorActionPreference = "Continue"` + try/finally
- **vsce missing LICENSE / .vscodeignore**: 拷 project root LICENSE 到 vscode-ext/ + 写空 .vscodeignore

### Bundle 体积拆分 (v1.5.4)

| Payload | 大小 | v1.5.3 → v1.5.4 变化 |
|---------|------|---------------------|
| Burn stub (wixstdba.exe) | ~600KB | 同 |
| `jhyy-compiler-X.Y.Z.msi` (embedded) | 995KB | +4KB (新增 .vsix + .url + install-vsix.bat + registry entries) |
| `license.rtf` (embedded) | ~50KB | 同 |
| `theme.xml` (embedded) | ~5KB | 同 |
| `thm.wxl` (embedded) | ~3KB | 同 |
| `logo.png` (embedded) | ~3KB | 同 |
| Bundle stub / metadata | ~50KB | 同 |
| **总计** | **~1.6MB** | +4KB (在四舍五入误差内) |

### Plan / Sprint / 文件改动

| 文件 | 改动 |
|------|------|
| `installer/vscode-ext/package.ps1` | NEW (~70 行) — vsce package + version patch + revert working tree |
| `installer/common/install-vsix.bat` | NEW (~25 行) — 检测 `code` 命令 + `code (with install-extension flag)` |
| `installer/common/JHYY Documentation.url` | NEW (2 行) — Internet Shortcut |
| `installer/common/JHYY Quick Start.url` | NEW (2 行) — Internet Shortcut |
| `installer/compiler/jhyy-compiler.wxs` | +85 / -3 行 — 3 ComponentGroup + CustomAction + Property + SetProperty |
| `installer/build.ps1` | +30 / -2 行 — vsce package + vscode-ext bindpath + SKIP_VSIX escape hatch |
| `installer/README.md` | +20 / -15 行 — v1.5.4 status + scope + verification |
| `vscode-ext/package.json` | +2 行 — repository + license field |
| `vscode-ext/.vscodeignore` | NEW (~20 行) — silence vsce warning |
| `vscode-ext/LICENSE` | NEW — copy from project root |

### 验证 (本 commit)

```
$ powershell -File installer/build.ps1 compiler
[package.ps1] version: 0.1.0 -> 1.5.4
[OK] installer/build-artifacts/jhyy-lang-1.5.4.vsix built
[OK] installer/build-artifacts/jhyy-compiler-1.5.4.msi built

$ wix msi validate installer/build-artifacts/jhyy-compiler-1.5.4.msi
EXIT=0 (no output, all standard ICEs pass)

$ powershell -File installer/build.ps1 bundle
[OK] installer/build-artifacts/jhyy-installer-1.5.4.exe built

$ file installer/build-artifacts/jhyy-installer-1.5.4.exe
PE32+ executable for MS Windows 6.00 (GUI), x86-64

$ # Bundle manifest 验证 (用 Python zipfile 读 .wixpdb, MSYS2 无 unzip)
$ python -c "import zipfile,re; \
  d=zipfile.ZipFile('installer/build-artifacts/jhyy-installer-1.5.4.wixpdb').read('wix-burndata.xml').decode(); \
  m=re.search(r'<MsiPackage[^>]*Id=\"JHYYCompilerMsi\"[^>]*>',d); print(m.group(0)[:200])"
<MsiPackage Id="JHYYCompilerMsi" Cache="keep"
            CacheId="{BBCCEEFC-6163-46BF-B72C-7B20E6812960}v1.5.4"
            InstallSize="1308080" Size="995328"
            Scope="perMachine" Permanent="yes" Vital="yes"
            ProductCode="{BBCCEEFC-6163-46BF-B72C-7B20E6812960}"
            Language="2052" Version="1.5.4"
            UpgradeCode="{A1B2C3D4-E5F6-7890-1234-567890ABCDEF}">

Bundle manifest 含:
- `<RelatedBundle>` UpgradeCode=`B1C2D3E4-F5A6-7890-1234-567890ABCDEF` (Bundle 的 UpgradeCode)
- 5 个 UX payload (thm.xml / thm.wxl / logo.png / license.rtf / wixstdba.exe)
- `<Chain>` 1 MsiPackage "JHYYCompilerMsi" v1.5.4 + ProductCode=`BBCCEEFC-...` + MSI UpgradeCode=`A1B2C3D4-...`
- 1 个 MsiProperty `JHYY_BUNDLE_INSTALL=1` (留给 MSI 知道被 Burn chain 装的)
- MSI InstallSize=1.3MB (含 .vsix + .url + install-vsix.bat)
- Bundle Size=995KB (MSI 压缩后), InstallSize=1.3MB (解压后)
```

### 已知 workarounds (已入 `docs/internal/workarounds.md`)

- 无新 workaround; v1.5.4 9 个 WiX 4 schema fix 都是 inline 修正 (comment 解释在 .wxs 里)

### 后续工作 (v1.5.5)

- GH Actions release workflow (`.github/workflows/release.yml` — tag `v*` → build installer → upload to Release + SHA256)
- 3 份第三方 manifest (winget / scoop / choco)
- `installer/SHA256.txt` 生成 + `changelog-template.md` Release notes 模板
- 本地 dry-run (`v1.5.0-rc1` tag) + 交互式 desktop session manual install/uninstall 验证 (headless bash 跑不了 per-machine UAC)

---

---

## v1.5.5 (待启动)

按 plan v1.5.5 是 0.6 sprint: 构建流程 + GH Actions + 第三方 manifest。

门槛: v1.5.4 跑通

工作:
- `build.cmd` 完善 (--version / --sign / --skip-vsix flag)
- `.github/workflows/release.yml` (tag `v*` → install WiX → build installer → upload to GitHub Release → 生成 SHA256)
- 3 份第三方 manifest (winget / scoop / choco) 写完待 publish
- `installer/SHA256.txt` 生成
- `installer/changelog-template.md` (Release notes 模板)
- 本地 dry-run (`v1.5.0-rc1` tag, GH Actions 跑)
- `installer/README.md` 完善 (怎么构建 + 怎么上传 + 怎么 smoke test)

---

## 关联文档

- [`docs/plans/v1/v1.5.0任务清单 + 概要设计.md`](../../plans/v1/v1.5.0任务清单 + 概要设计.md) — 完整 5-sprint 计划 + 决策点
- [`docs/internal/workarounds.md`](../../internal/workarounds.md) — v1.5 Burn / MSI / WiX 工具链已知 workaround
- [`installer/README.md`](../../../installer/README.md) — installer 构建步骤 + 验证清单

## Sprint 决策记录

- **决策 D1** (2026-08-14 user 决策): Burn bundle 不打包 GCC toolchain, 走"检测+引导"力度 1 (welcome dialog 提示用户装 MSYS2 + ucrt64 GCC)
- **决策 D2** (2026-08-14): Bundle 走 standard WixStdBA UI, 不写 custom BAFunctions (simple + 文档化 + 跨版本稳)
- **决策 D3** (2026-08-15): Bal extension DLL 通过绝对路径引 (workaround WiX CLI 7.0.0+b8977d6 名字查找 WIX0144)
- **决策 D4** (2026-08-15): v1.5.5 release 时再跑 manual install/uninstall verification (headless bash 跑不了 per-machine MSI UAC)