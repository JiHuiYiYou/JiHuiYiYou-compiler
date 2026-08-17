# Changelog — v1.5.0 (umbrella: Windows installer)

> **承接**: v1.4.7 shipped (regress 三跑合并 + CI workflow 简化).
> **目标**: 用户下载 `jhyy-installer-X.Y.Z.exe` 双击 → next-next-finish 装好 jhyy + qbe.exe, 系统 PATH 自动配, 用户零配置。
> **scope**: WiX 4/7 + Burn bundle + MSI; Windows-only; per `docs/plans/v1/v1.5.0任务清单 + 概要设计.md`。
> **本 umbrella 涵盖 5 + 2 个 sprint**: v1.5.1 / v1.5.2 / v1.5.3 / v1.5.4 / v1.5.5 / v1.5.6 / v1.5.6-patch2, 各 sprint 状态如下。

---

## Sprint 状态总览

| Sprint | 状态 | Commit | 摘要 |
|--------|------|--------|------|
| **v1.5.1** | ✅ done | `73dd3cb` | WiX 4/7 工具链 + 项目结构 (`installer/` 目录 + `_stub/` smoke test) + `build.ps1` 编排 |
| **v1.5.2** | ✅ done | `165e650` | `compiler/jhyy-compiler.wxs` 写完; `wix msi validate` 0 ICE errors (ICE43/ICE57/ICE80 全过) |
| **v1.5.3** | ✅ done | `6ea1c62` | `Bundle.wxs` (Burn bundle) + `Theme.xml` + `Bundle.zh-CN.wxl` + `banner.bmp`; `jhyy-installer-1.5.3.exe` (1.6MB) 生成 |
| **v1.5.4** | ✅ done | (1a9dd9b) | VSCode ext auto-install + `.jhyy` file association + Start Menu Documentation/Quick Start 增强; `wix msi validate` 0 ICE errors |
| **v1.5.5** | ✅ done | (this commit) | GH Actions release workflow (tag v* + workflow_dispatch) + winget + scoop manifest reference + SHA256 生成 + Release notes 模板; v1.5.0 umbrella ship 闭环 |
| **v1.5.6** | ✅ done | (this commit) | `jh_gcc_path()` 4-tier 探测收敛跨 3 文件 MSYS2 探测逻辑; W-029 ACTIVE (Windows 4-tier + Linux placeholder); regress.py / release.yml 删 MSYS2 探测段 |
| **v1.5.6-patch2** | ✅ done | (this commit) | VSCode Code Runner 集成 — `configure-coderunner.ps1` (parse + add + re-serialize settings.json); `install-vsix.bat` 升级 3 步 (jhyy-lang + Code Runner + settings.json); MSI Component `ConfigureCodeRunnerPS1` (新 GUID); winget 1.5.6 复制自 1.5.5 |

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

## v1.5.5 — GH Actions release workflow + 第三方 manifest (本 commit)

### 完成定义

- ✅ `.github/workflows/release.yml` — 14-step GH Actions workflow (checkout + MSYS2 + WiX + make stage0 + make + regress + bundle + SHA256 verify + release notes + MSI validate + release create + dry-run summary)
- ✅ `installer/gen-sha256.ps1` — `Get-FileHash` 扫 build-artifacts → `SHA256.txt` (sha256sum-compatible 格式, UTF-8 no BOM)
- ✅ `installer/build.ps1` — bundle target 自动调 gen-sha256 (本地 build 一并产出 SHA256.txt)
- ✅ `installer/changelog-template.md` — Release notes 模板 (VERSION / ISO_DATE / URL 占位符, GH Actions 替换)
- ✅ winget 3 manifest (`installer/winget/manifests/j/JiHuiYiYou/JHYY/1.5.5/JiHuiYiYou.JHYY{.yaml, .installer.yaml, .locale.en-US.yaml}`)
- ✅ scoop 1 manifest (`installer/scoop/jhyy.json`)
- ✅ `installer/README.md` — 加 "发布流程" 段 (本地 build / tag push / workflow_dispatch dry-run / manifest publish deferred)
- ✅ `.gitignore` — 加 `installer/SHA256.txt` / `installer/**/SHA256.txt`
- ⚠️ **Real GH Actions workflow_dispatch dry-run** 在 commit 后跑 (per `feedback_auto_push_after_commit.md`, 等 user 触发); RC tag `v1.5.5-rc1` 也等 user 决策
- ⚠️ **winget + scoop manifest publish** 推到 v2.x (per plan 决策-11; 当前仅 reference, no PR 到 winget-pkgs / ScoopInstaller/Main)
- ⚠️ **Dev placeholder GUID (`BBCCEEFC-...`)** 没替换真 GUID — 当前 manifest 用占位符; v1.5.0 ship 前 user 决策时机

### 核心机制

#### 1. 双触发 release workflow

- **push tag `v*`** → 自动 build + upload + create Release (make_latest: true); `v1.5.5-rc1` 这种 RC tag 自动 mark prerelease
- **`workflow_dispatch`** (manual) → escape hatch, dry_run=true 时 build 但不 upload 不 create Release

#### 2. 14-step workflow 流水线

| Step | 工具 | 说明 |
|------|------|------|
| 1 | `pwsh` | Compute VERSION + IS_RC + JHY_TAG_NAME (push 走 `github.ref_name`, dispatch 走 `inputs.version`; 始终 strip leading `v`) |
| 2 | `actions/checkout@v4` | Checkout (submodules: recursive for qbe/) |
| 3 | `msys2/setup-msys2@v2` | 装 gcc / make / qbe / python / zip |
| 4 | `pwsh` env= | Install WiX 4/7 + 3 extension (Util / UI / Bal) |
| 5 | msys2 bash | `make stage0` (C 端 bootstrap binary) |
| 6 | msys2 bash | `make` (jhyy.exe production binary) |
| 7 | msys2 bash | `python regress.py --all` (gated — must PASS, 是 release gate) |
| 8 | pwsh env=JHY_VERSION | `powershell -File installer/build.ps1 bundle` (Burn + MSI + .vsix + SHA256) |
| 9 | pwsh | Verify SHA256.txt 内容 (3 产物 hash 都对) |
| 10 | pwsh | Generate release-notes.md (从 changelog-template.md 替换占位符) |
| 11 | pwsh | `wix msi validate` (0 ICE errors 必须) |
| 12 | pwsh (dry_run) | Confirm artifacts present (5 file) |
| 13 | `softprops/action-gh-release@v2` | Create Release + upload 4 assets |
| 14 | pwsh (dry_run) | Summary 输出 |

#### 3. PowerShell `$GITHUB_ENV` write (踩坑)

- `Out-File -Encoding utf8` 在 Windows PowerShell 5.1 加 UTF-8 BOM, GH parser 解析 $GITHUB_ENV 时 BOM 出错 → 用 `Add-Content` (BOM-safe 路径) 替代
- bash `${VERSION}` 占位符在 MSYS2 bash 不展开 `${{ env.VERSION }}` (那是 GH 表达式, 仅在 yaml 解析时替换); 实际 bash step 跑时 `VERSION` 已经通过 $GITHUB_ENV export, 直接用 `$VERSION` 即可
- pwsh step 用 `$env:VERSION` 读 (PowerShell env var syntax), 不 `$VERSION`

#### 4. winget + scoop manifest (reference, no publish)

- **winget multi-file manifest** (v1.5.0 schema): version + installer + locale en-US 三个 YAML 在 `manifests/j/JiHuiYiYou/JHYY/1.5.5/`; `InstallerSha256` 是 `<FILL_AT_RELEASE_TIME_FROM_SHA256.txt>` placeholder (release 时 CI 替换)
- **scoop manifest** (`jhyy.json`): Burn bundle URL + sha256 placeholder + 3 个 Start Menu shortcut + autoupdate (regex 抓 GH release tag)
- **chocolatey 推 v2.x**: 用户决策 (per `ask_user` 选项 "只写 winget + scoop"); choco manifest 复杂 (admin shell + install script)

### Plan / Sprint / 文件改动

| 文件 | 改动 |
|------|------|
| `.github/workflows/release.yml` | NEW (~230 行) — 14-step GH Actions workflow |
| `installer/gen-sha256.ps1` | NEW (~55 行) — SHA256.txt 生成 |
| `installer/changelog-template.md` | NEW (~50 行) — Release notes 模板 |
| `installer/winget/manifests/j/JiHuiYiYou/JHYY/1.5.5/JiHuiYiYou.JHYY.yaml` | NEW (~15 行) — version manifest |
| `installer/winget/manifests/j/JiHuiYiYou/JHYY/1.5.5/JiHuiYiYou.JHYY.installer.yaml` | NEW (~25 行) — installer manifest |
| `installer/winget/manifests/j/JiHuiYiYou/JHYY/1.5.5/JiHuiYiYou.JHYY.locale.en-US.yaml` | NEW (~30 行) — locale en-US |
| `installer/scoop/jhyy.json` | NEW (~50 行) — scoop manifest |
| `installer/build.ps1` | +13 / -1 行 — bundle target 调 gen-sha256.ps1 |
| `installer/README.md` | +40 / -10 行 — v1.5.5 status + 发布流程段 |
| `docs/logs/v1/changelog-v1.5.0.md` | +110 / -10 行 — v1.5.5 section (本 commit) |
| `.gitignore` | +2 行 — `installer/SHA256.txt` / `installer/**/SHA256.txt` |

### 验证 (本 commit — 本地)

```
$ powershell -File installer/gen-sha256.ps1
[OK] installer/SHA256.txt written (8 entries)
    6429a1833b2b486c46482b779f193b9ea124979075727e98f82d968d8253ba5d  jhyy-compiler-1.5.4.msi
    0b8dd1a88c4f52a5ca75c890c0b148f4b8d2b0729d943da27bf585f52932714d  jhyy-installer-1.5.4.exe
    2666c769d5abed6b5eed8c3aa9ecbf38d4df09d0821ce9ac2dac1c336567d216  jhyy-lang-1.5.4.vsix
    ...

$ sha256sum installer/build-artifacts/jhyy-installer-1.5.4.exe
0b8dd1a88c4f52a5ca75c890c0b148f4b8d2b0729d943da27bf585f52932714d *installer/build-artifacts/jhyy-installer-1.5.4.exe
# (matches line in SHA256.txt ✓)

$ python -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml'))"
# 14 steps valid ✓

$ python -c "import json; json.load(open('installer/scoop/jhyy.json'))"
# valid ✓

$ python -c "import yaml; [yaml.safe_load(open(f'.../JHYY/1.5.5/JiHuiYiYou.JHYY{x}.yaml')) for x in ['', '.installer', '.locale.en-US']]"
# all 3 valid ✓

$ python regress.py
PASS 53/53, 0 fail, 3 skipped
# baseline 守门 ✓
```

### GH Actions workflow_dispatch dry-run (推送后)

```bash
gh workflow run release.yml -f version=1.5.5-rc1 -f dry_run=true
# 期望: GH Actions UI run → 14 step 全 green → 无 Release 创建 → summary 在 console
```

### 已知 workarounds (已入 `docs/internal/workarounds.md`)

- **W-022 (新增) Add-Content vs Out-File -Encoding utf8 for $GITHUB_ENV**: Windows PowerShell 5.1 `Out-File -Encoding utf8` 加 UTF-8 BOM, GH parser 解析 $GITHUB_ENV fail; workaround `Add-Content` (BOM-safe)
- **W-023 (新增) MSYS2 bash `${VAR}` 不展开 `${{ env.X }}`**: GH 表达式仅 yaml 解析时替换; bash step 要 `echo $VAR` 拿 export 过的 env var, 不 `${VAR}` 占位符
- **W-024 (新增) `Out-File -Encoding utf8` BOM in PowerShell**: 影响所有写 UTF-8 文本场景 (changelog-template.md, gen-sha256.txt, release-notes.md), 改 `[System.IO.File]::WriteAllLines(..., $utf8NoBom)` 或 `Set-Content -NoNewline`
- **W-025 (新增) qbe/ gitlink 无 .gitmodules — release.yml `submodules: recursive` 失败 + installer/build.ps1 hardcoded `qbe/qbe.exe`**: qbe/ 在 v1.5.5 之前是 dangling gitlink (无 .gitmodules), checkout 拿不到 qbe.exe source; fix vendoring qbe/ 到 repo (`cd qbe && make`), release.yml 删 `submodules: recursive`; regress 跟 local build 都 verify vendored copy 完整 (sha256sum 比对 qbe.exe binary). (commit `9ed97c9` 周边的 W-025 follow-up, 2026-08-15 same-day)
- **W-026 (新增) regress.py `[:80]` stderr 截断隐藏真实 QBE/gcc 错误**: CI FAIL 只 print `[:80]` 截断后 stderr, link error 看不见; fix 改成完整 stderr 输出, 加 CI-friendly 标记. (commit `0d58efe`, 2026-08-15)
- **W-027 (新增) `setup-msys2@v2` 把 MSYS2 装在 `$RUNNER_TEMP\msys64` (CI = `D:\a\_temp\msys64`), 不在 `C:\msys64`**: 硬编码 `C:\msys64\ucrt64\bin` 找不到 gcc; v1-v7 (7 iters) 各种探测方法全 FAIL, v8 final 改用 deterministic `$RUNNER_TEMP` (CI) / `C:\msys64` (local) + known bin subdirs `ucrt64/bin` + `usr/bin`, no subprocess call. (commit `4623a3b` v8 final)
- **W-028 (新增) Windows process exit code 是 8-bit (mod 256), EXPECT 注释里的值 > 255 在 CI regress FAIL**: `kernel32!ExitProcess` exit code 只取低 8 bit (`exit code & 0xFF`), EXPECT 注释里的 `1000042` 等大值在 CI 显示成 `got=106` 不是 `got=1000042`; v1 (commit `6d2ab8f`) 加 `if sys.platform == "win32"` 改 mod 256 comparison, 但 MSYS2-launched Python `sys.platform == "cygwin"`, v1 不触发; v2 (commit `03f58c6`) 扩展为 `sys.platform in ("win32", "cygwin", "msys")`, CI 53/53 PASS.

### Ship 验证 (v1.5.5 stable, 2026-08-15)

- ✅ GH Actions dispatch #31877795241 (push tag v1.5.5) — 全 14 step green: regress 53/53 PASS, Burn bundle + MSI + .vsix build, SHA256 verify, MSI validate (0 ICE), release publish
- ✅ GitHub Release [v1.5.5](https://github.com/JiHuiYiYou/JiHuiYiYou-compiler/releases/tag/v1.5.5) created — Latest, 4 assets (jhyy-installer-1.5.5.exe 1.6MB / jhyy-compiler-1.5.5.msi 962KB / jhyy-lang-1.5.5.vsix 4KB / SHA256.txt)
- ✅ RC release [v1.5.5-rc1](https://github.com/JiHuiYiYou/JiHuiYiYou-compiler/releases/tag/v1.5.5-rc1) 保留 — Pre-release, 4 assets with -rc1 suffix
- ✅ 6 installer pipeline fixes 串联: W-028 v2 (regress cygwin) + vsce install (release.yml) + RC version strip (build.ps1) + sub-script RC suffix + vsix DISPLAY version + .wxs DISPLAY references + dry_run gate boolean fix

## v1.5.6 — `jh_gcc_path()` 4-tier 探测收敛跨 3 文件 MSYS2 探测逻辑 (本 commit)

### 完成定义

- ✅ `compiler/src0/jhyy_helpers.c` — `jh_gcc_path()` (Windows 4-tier + Linux placeholder) + `jh_gcc_invoke()` 包装 (~118 行新增)
- ✅ `compiler/src0/main.jhyy` — `link_with_gcc` 改用 `jh_gcc_invoke` (替代裸 `system("gcc ...")` 拼 cmd_buf), cmd_buf 不再前缀 GCC_PATH()
- ✅ 5 个新测试 `compiler/tests/examples/_jh_gcc_p1.jhyy` ... `_p5.jhyy` — 探测优先级黑盒验证 (5/5 PASS)
- ✅ `mcp-jhyy/jhyy_regress.py` — `_build_subprocess_env` 删 W-027 v4 MSYS2 探测段 (~30 行), 仅保留基础 env; 新增 `SETENV` 注释 directive 注入 env var 到 test
- ✅ `.github/workflows/release.yml` — 删 "Propagate MSYS2 paths to subprocess PATH" step (12 行); Run regress 注释更新指向 W-027/W-029 superseder
- ✅ `.gitignore` — 加 `compiler/tests/examples/_tmp_jhyy_home/` (p2 测试 env.txt setup 目录)
- ✅ `docs/internal/workarounds.md` — W-027 标 "RESOLVED → SUPERSEDED by W-029"; 新增 W-029 ACTIVE 记录新设计
- ⚠️ **Linux/macOS 跨平台探测** (Priority 4 SearchPathA / 多 magic 路径) 推迟到 v2.x manifest lite sprint (per `feedback_compiler_toolchain_path_resolution` 类型 4 升级)
- ⚠️ **p4/p5 严格测试** (SearchPathA / fallback "gcc") 推迟到 v2.x (本机测试环境无法构造 magic 全不存在的状态)
- ⚠️ **Real GH Actions CI dry-run** 等 commit 后 user 触发 (per `feedback_auto_push_after_commit.md`)

### 核心机制

#### 1. `jh_gcc_path()` 4-tier 优先级探测

| Priority | 来源 | 场景 |
|----------|------|------|
| 1 | `JHY_GCC` env | user/CI 显式 override (测试 + CI 最常用) |
| 2 | `$JHYY_HOME\env.txt` KEY=VALUE | 单用户配置 (装时探测结果写入) |
| 3 | Windows MSYS2 magic 3 项 | `C:\msys64\ucrt64\bin\gcc.exe` 等, 本机默认 |
| 4 | `SearchPathA` PATH 探测 | Win32 API 替代 W-027 v8 的 shutil.which / cmd where (no subprocess) |
| 5 (fallback) | literal `"gcc"` | 走 Windows PATH 解析 (跟 W-027 v8 之前一致) |

Static buf 缓存, 启动一次性 resolve, 后续多次读返回 const char*. Linux/macOS 占位符 `#ifdef _WIN32` 之外返回 `"gcc"` (v2.x 填跨平台探测).

#### 2. `jh_gcc_invoke()` system() 包装

```c
int jh_gcc_invoke(char *out_buf, int out_size, const char *args) {
    return snprintf(out_buf, (size_t)out_size, "\"%s\" %s", jh_gcc_path(), args);
}
```

`main.jhyy link_with_gcc` 改用:
```jhyy
let invoke_buf = malloc(16384 as i64);
let _wrote = jh_gcc_invoke(invoke_buf, 16384 as i32, args_start);
let r = system(invoke_buf);
```

替代之前 `system("gcc <args>")` 裸调用, GCC_PATH() 前缀从 main.jhyy 移到 jh_gcc_invoke 内部 (一处真理).

#### 3. SETENV directive (regress.py 新增)

`// SETENV: KEY=VALUE` 注释行被 regress.py 解析, 注入到 `_build_subprocess_env()` 输出 env dict, 然后用 `env=test_env` 跑 compile + run subprocess. 之前需要 bash pre-step `export JHY_GCC=...` 才能验证 env 行为, 现在 inline 在 .jhyy 源里 — test 跟 source 一起版本控制.

5 个测试都用 SETENV (除 p3 不设 env 走 magic). p1 SETENV `JHY_GCC=C:\msys64\ucrt64\bin\gcc.exe` (magic 第 1 项) → Priority 1 命中直接通过.

#### 4. regress.py + release.yml cleanup

- `_build_subprocess_env()` 删 W-027 v4 整段 (shutil.which / RUNNER_TEMP / MSYS2 root 探测), 只剩 TMP/SystemRoot 基础 env. ~30 行 → 0 行.
- "Propagate MSYS2 paths to subprocess PATH" step 整段删 (12 行). release.yml 从 13 step → 12 step.
- 删后逻辑: jhyy.exe 启动时自己调 jh_gcc_path() 探测 gcc 路径, Python / GH Actions 不再操心 MSYS2 在哪. 跨 3 文件 8 个版本的 workaround (W-027 v1-v8) 全部收敛到 jhyy.exe 内部一处.

### 已知 workarounds (已入 `docs/internal/workarounds.md`)

- **W-027 (RESOLVED → SUPERSEDED by W-029)** `setup-msys2@v2` 装 MSYS2 到 `$RUNNER_TEMP\msys64` (CI) / `C:\msys64` (local): 跨 3 文件 8 个版本探测逻辑收敛到 jhyy.exe `jh_gcc_path()` 内部, regress.py / release.yml 不再 prepend MSYS2 bin 到 PATH
- **W-028 (RESOLVED)** Windows process exit code 8-bit (mod 256): v1.5.5 实施, v1.5.6 保持
- **W-029 (新增 ACTIVE)** jhyy.exe toolchain 探测收敛: `jh_gcc_path()` 4-tier + `jh_gcc_invoke()` 包装替代 v1.0.0 跨 3 文件 MSYS2 探测逻辑. Linux/macOS 跨平台探测推迟 v2.x
- **W-030 (RESOLVED)** WiX 4 Theme.xml schema — Font 顶层 / 删 Weight bold / 加 FontId / Caption 替 Title
- **W-031 (RESOLVED)** MSI LaunchCondition 4-source probe + INSTALLDIR resolution `<SetProperty>` 替 `<SetDirectory>`
- **W-032 (RESOLVED → SUPERSEDED by W-033)** 试图加独立 `<Page Name="License">` — 错方向, wixstdba 默认 license 整合在 Install page
- **W-033 (RESOLVED — v1.5.6 hotfix)** Theme.xml XML 1.0 well-formedness (line 10 comment `--` 违 spec) + WiX 4 thmutil schema + wixstdba 默认控件名 (EulaAcceptCheckbox / InstallButton / InstallCancelButton / EulaRichedit) + Bundle.zh-CN.wxl string IDs 全对齐 (InstallAcceptCheckbox / InstallInstallButton / InstallCancelButton 等). 修后 `v1.5.6-rc1.exe` 静默模式 exit 0 + UI 模式 Burn log 走到 i199 detect complete. 完全基于 wixstdba 默认 RtfTheme.xml / RtfTheme.wxl 重写, 加 MSYS2 prereq warning (Install page) + post-install hint (Success page) JHYY customization. 详见 `docs/internal/workarounds.md` W-033

### 后续工作 (v1.5.0 umbrella ship)

- ✅ v1.5.5 done → v1.5.0 umbrella 5/5 sprint 全部 ship
- **真 GUID 替换** (dev placeholder → uuidgen): v1.5.0 ship 前 user 决策; 改 `.wxs` + manifest (InstallerSha256 跟 ProductCode 都关联)
- **v1.5.0 ship tag** + GitHub Release 标 "stable"
- **winget + scoop manifest publish** 推到 v2.x (per 决策-11)
- **Authenticode code signing** 推到 v2.x (需 HSM / EV cert)

---

## v1.5.6-patch2 — VSCode Code Runner 集成 (本 commit)

### 完成定义

- ✅ `installer/common/configure-coderunner.ps1` (NEW, ~80 行) — 解析 + 加 4 个 code-runner key + re-serialize
- ✅ `installer/common/install-vsix.bat` — 升级 3 步 (jhyy-lang vsix + Code Runner + settings.json)
- ✅ `installer/compiler/jhyy-compiler.wxs` — 新 Component `ConfigureCodeRunnerPS1` (GUID `F7A2D6E0-...`);SetProperty 加 `/CONFIGURE_PS1` + `/JHY_DIR` args
- ✅ `installer/GUIDS.md` — 加 Component GUID 条目
- ✅ `installer/winget/manifests/j/JiHuiYiYou/JHYY/1.5.6/` — 复制 1.5.5, 改 version + ReleaseNotes
- ✅ `docs/plans/v1/v1.5.6任务清单 + 概要设计.md` — 加 patch2 段
- ✅ `docs/internal/workarounds.md` — 加 W-041 entry (RESOLVED)
- ⚠️ **MSI smoke build** + **Burn bundle smoke build** + **真机 install 验证** 等 user 触发

### 核心机制

#### 1. `configure-coderunner.ps1` — parse + add + re-serialize

PowerShell 5.1 脚本,处理 5 场景:

| 场景 | 输入 | 输出 |
|------|------|------|
| no-op | 用户的 43-key settings.json | 字节级重排,语义等价 + 43 key 全保留 |
| partial | 41-key 文件 (executorMap 在,3 simple key 缺) | 4 key 全到位,其他保留 |
| fresh | `Code\User\` 是空目录 | 4-key 新文件 |
| VSCode 没装 | `%APPDATA%\Code\User\` 不存在 | silent skip, exit 0 |
| Malformed JSON | 用户手工改坏了 | exit 1 + 文件 byte 级保留 |

**算法选型:** parse + Add-Member + ConvertTo-Json -Depth 10,**不**用 targeted text patch (text patch 在嵌套 block end 场景 regex 不能可靠识别)。

#### 2. `install-vsix.bat` 3 步流程

```
Step 1: code --install-extension <jhyy-lang.vsix> --force
Step 2: code --install-extension formulahendry.code-runner --force
Step 3: powershell -File <configure-coderunner.ps1> -JHY_DIR <INSTALLDIR>
```

每个步骤独立 try/fail-soft (exit 0 + warn log),任一失败不阻塞 MSI。

#### 3. MSI Component `ConfigureCodeRunnerPS1`

- GUID `F7A2D6E0-9B3C-4D1A-9E5F-3C7B8A2D6E01` (新生成)
- Source `!(bindpath.common)\configure-coderunner.ps1` (MSI build 时从 `installer/common/` 拉)
- Directory="BinDir" (装到 `INSTALLDIR\bin\configure-coderunner.ps1`)
- CustomAction `InstallVSCodeExtCmd` 加 2 args:`/CONFIGURE_PS1="[INSTALLDIR]bin\configure-coderunner.ps1"` `/JHY_DIR="[INSTALLDIR]"`

### 已知 workarounds (已入 `docs/internal/workarounds.md`)

- **W-041 (新增 RESOLVED in v1.5.6-patch2)** VSCode Code Runner 集成: `configure-coderunner.ps1` parse + add + re-serialize 算法 (`install-vsix.bat` 3 步流程; MSI Component `ConfigureCodeRunnerPS1`)。永久 work around — PowerShell 5.1 兼容,Windows 10+ ships。

### 后续工作 (patch2 ship 后)

- ⚠️ **MSI smoke build + 真机 install 验证** 等 user 触发 (headless bash 跑不了 per-machine MSI UAC)
- ⚠️ **winget 1.5.5 保留**,1.5.6 是新 dir (per Windows winget 不允许覆盖已 publish manifest)
- v2.x installer 升级时把 PowerShell 脚本链打包到 `installer/vscode/` 子目录,避免根 `common/` 过度膨胀
- v2.x 跨平台时 `configure-coderunner.ps1` 需要 macOS/Linux 分支 (`$env:APPDATA` 不存在 → `$XDG_CONFIG_HOME` / `$HOME/Library/Application Support`)

---

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