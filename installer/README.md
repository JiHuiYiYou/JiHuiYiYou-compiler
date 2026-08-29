# JHYY Installer (v1.8.x)

Windows 引导式安装器 — 把 JHYY 编译器装到 `C:\Program Files\JHYY\`, 自动配 PATH, 用户零配置。

> **Last updated**: v1.8.3 (2026-08-29) — v1.x 终结 installer 真修闭环(UCPD.sys bypass + `.jhyy` 图标真修 + WiX CustomAction 静默失败 fallback)。详见下方 § v1.8.x 节。最新 shipped 产物: `jhyy-compiler-1.8.3.msi` (~995KB) + `jhyy-installer-1.8.3.exe` (~30MB, 含 .NET 8 Desktop Runtime embed) + `jhyy-lang-1.8.3.vsix`。SHA256 见 [`installer/SHA256.txt`](SHA256.txt)。

## 当前状态 (v1.8.3 shipped)

✅ **v1.5.2 done** — `compiler/jhyy-compiler.wxs` 写出, `build.ps1 compiler` 跑通, `jhyy-compiler-1.0.0.msi` (991KB) 生成, **`wix msi validate` 0 ICE errors** (ICE43/ICE57/ICE80 全过).

✅ **v1.5.3 done** — `Bundle.wxs` 写出, `build.ps1 bundle` 跑通, `jhyy-installer-1.5.3.exe` (1.6MB) 生成。Burn bundle 走 standard `WixStandardBootstrapperApplication` UI (next-next-finish, RTF license, MSYS2 prereq 提示在 Welcome page, post-install 提示在 Success page)。

✅ **v1.5.4 done** — VSCode ext auto-install (`.vsix` + CustomAction `code --install-extension`), `.jhyy` file association (双击 → `jhyy run file.jhyy`), Start Menu 增强 (Documentation / Quick Start 走 Internet Shortcut `.url`)。`wix msi validate` 0 ICE errors。
> **superseded by v1.5.7-rc1 / v1.5.10**: CustomAction 走 deferred cmd.exe 链触发 1721 错位;RunOnce 接管 + inline `code --install-extension` 是当前实现 (见 `install-configure-all.bat`)。

✅ **v1.5.5 done** — GitHub Actions release workflow (`.github/workflows/release.yml`, tag `v*` + manual `workflow_dispatch`), 第三方 manifest reference (winget 3 文件 + scoop 1 文件, schema 校验通过, no actual publish), `installer/gen-sha256.ps1` 写 SHA256.txt, `installer/changelog-template.md` Release notes 模板。`tag v*` push → 自动 build + upload + Release; RC tag 自动 mark prerelease; workflow_dispatch dry-run 入口作为 escape hatch。

✅ **v1.5.7-rc1 done** — JHYY brand UI assets (navy `#1a1a2e` + mint `#00d4aa`) generated from `vscode-ext/icon.svg` via `installer/build-jhyy-icons.ps1`: multi-size `.ico` (16+32+48+64+128+256) for ARPPRODUCTICON + Start Menu shortcut + .jhyy FileAssoc, `jhyy-banner.bmp` (493x58) for WixUI_Minimal top banner, `jhyy-welcome.bmp` (493x312) for welcome dialog content. JhyyIconFile Component ships .ico to INSTALLDIR\bin\. Replaces default Windows disc icon + red banner with brand-consistent visuals.

---

## v1.8.x — installer 真修 + Windows UserChoice/UCPD.sys 闭环 (2026-08-28 → 2026-08-29)

> v1.8.x 在 v1.7.x installer 闭环基础上,深度解决 Windows 10 Feb 2024+ 引入的 UCPD.sys kernel filter + UserChoice hash 限制对 `.jhyy` 文件关联/VSCode ext 装/Start Menu shortcut 的硬阻塞。共 7 个 fix commit (含 v1.8.0 umbrella,patch v1.8.1 / v1.8.2 / v1.8.2 patch update / v1.8.3 / v1.8.3.1 / v1.8.3.2)。

### v1.8.1 — `.jhyy` 文件图标真修 (commit `de4f219`, 2026-08-29)

**根因**: WiX `jhyy-compiler.wxs` 的 `(default)` registry value 写错位(`HKCR\.jhyy\(default)="JHYY.SourceFile"` 漏),加 MSYS2 HKCU `OpenWithProgids` shadow 优先级覆盖。`.jhyy` 文件在 Explorer 里仍走 MSYS2 `notepad.exe`,不显示品牌图标。

**修复**:
1. WiX `<RegistryValue Name="(default)" Value="JHYY.SourceFile" ... Type="string" />` 改正位置(`<RegistryKey Root="HKCR" Key=".jhyy">` 内 `<RegistryValue Type="string">`,非 `<RegistryKey>` attribute)。
2. `installer/common/install-configure-all.bat` 加 HKCU `Software\Classes\OpenWithProgids\.jhyy` shadow 写("per-user override 优先级 > HKCR machine-wide"),避免 MSYS2 shadow。
3. `installer/build-jhyy-icons.ps1` 新增 `windres` step — 把 `installer/jhyy-icon.ico` 16x16 embed 进 `compiler/build/bin/jhyy.exe`(PE 资源段),Explorer 在 `jhyy.exe` 进程上下文显示品牌图标而非默认白方块。

### v1.8.2 — VSCode UserChoice hijack + MSYS2 OpenWithProgids shadow 真修 (commit `31d2687`, 2026-08-29)

**根因**: v1.5.10 RunOnce + `code --install-extension` 在 Win10 21H2+ 上工作,但 Win10 22H2+ 引入 `code.exe` 自身 UserChoice 路径(`HKCU\Software\Classes\Applications\code.exe`)+ MSYS2 `OpenWithProgids` shadow,把 `code` CLI 实际指向 MSYS2 bin,RunOnce inline 装 VSCode ext 静默失败。→ 新 W-062。

**修复 (Path B: 自定 ProgId `JHYY.SourceFile`)**:
1. 不依赖 `code` CLI;`installer/compiler/jhyy-compiler.wxs` 加自定 ProgId `JHYY.SourceFile`(`HKCR\JHYY.SourceFile\shell\open\command = "jhyy.exe run \"%1\""`)。
2. `installer/common/install-configure-all.bat` 写 UserChoice hash(Mozilla reverse-engineered SHA256 algorithm,port C#,存到 `installer/common/jhyy-setuc/Program.cs`——见 v1.8.3 的 jhyy-setuc CLI 化)。
3. MSYS2 HKCU `Software\Classes\OpenWithProgids\.jhyy` shadow 加显式清,避免 path collision。

### v1.8.2 patch update — UCPD.sys 真实限制识别 (commit `f44c764`, 2026-08-29)

**根因**: v1.8.2 装的 `jhyy-setuc.exe` CLI args 处理有 bug(`%1` 在 deferred CustomAction 里 unwrap 错位),导致 32 位 hash 算错,Win10 22H2+ 上仍被 UCPD.sys Deny ACE 阻断。→ 新 W-063(UCPD.sys 真实 kernel filter 限制)。

**修复**:
1. `installer/common/jhyy-setuc/Program.cs` CLI args parse 用 `static int Main(string[] args)`,`args[0]` 判断 `--system-context` 走 system-context 路径(line 420-422);非 system-context 时按 `argv[0]` / `argv[1]` 严格拆 `ext` / `progid`(Program.cs line 430-436,7 元素 usage)。
2. `workarounds.md` 加 W-063 entry: UCPD.sys 是 Win10 Feb 2024+ 引入的 `UserChoice` kernel-level Deny ACE,non-admin 直接写 `HKCU\...\UserChoice` 触发 Access Denied。绕过路径 = SYSTEM-context CustomAction(v1.8.3 真修)+ Mozilla Hash 正确算法。

### v1.8.3 — WiX MSI SYSTEM-context CustomAction 写 per-user UserChoice (commit `a134a80`, 2026-08-29)

**根因**: v1.8.2 path B 在 HKCU 上写 UserChoice hash,per-user 有效但被 UCPD.sys kernel filter(`HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.jhyy\UserChoice` ACL 加 `Deny Write NT AUTHORITY\SYSTEM + INTERACTIVE`)阻断。

**修复 (真正的 SYSTEM-context bypass)**:
1. `installer/compiler/jhyy-compiler.wxs` 加 `<CustomAction Id="JHYYSetUCForAllUsers" Directory="INSTALLDIR" ExeCommand="[JHYYSetUCCmd]" Execute="deferred" Impersonate="no" Return="ignore" />`(wxs line 323-328)— `Impersonate="no"` 让 MSI 在 SYSTEM token 下跑,绕过 UCPD.sys Deny ACE;`Return="ignore"` 让 CustomAction 静默失败不 roll back MSI install(v1.8.3.1 修复 fallback 给 install-configure-all.bat 处理)。
2. `jhyy-setuc.exe` 编译为 .NET 8 self-contained CLI(`installer/common/jhyy-setuc/build.ps1`),ship 4 文件:`jhyy-setuc.exe` + `jhyy-setuc.dll` + `jhyy-setuc.deps.json` + `jhyy-setuc.runtimeconfig.json`,全部进 `INSTALLDIR\bin\`。
3. WiX compile 传 `JHY_DOTNET8_RUNTIME_EXE_PATH` 环境变量指向 `dotnet-runtime-8.0.30-win-x64.exe`(`installer/build-artifacts/dotnet/` 缓存,download 一次),让 CustomAction binary 链 .NET 8 运行时。

### v1.8.3.1 — 真修 WiX CustomAction 静默失败 (commit `ba071d8`, 2026-08-29)

**根因**: v1.8.3 ship 后实测,`JHYYSetUCForAllUsers` CustomAction 在某些主机静默返回 exit 0 但 `HKCU\UserChoice` 未写。原因 = `JHY_SETUC` BinaryKey resolve 在 WiX 4/7 `wix build` 上首次跑失败(bug in Property → Binary 表的 late-bind resolution)。

**修复 (3-attempt fallback)**:
1. 第一次尝试:`<CustomAction BinaryKey="JHY_SETUC" ...>` 走标准 Property `Binary` 表引用。
2. 失败回退:`<CustomAction FileKey="FILEREF_JHYY_SETUC_EXE" ...>` 走 `<File Id="FILEREF_JHYY_SETUC_EXE" Source="$(var.JHYYSetUCPath)\jhyy-setuc.exe" />` 显式 FileKey。
3. 最终回退:`installer/common/install-configure-all.bat` 检测 CustomAction 没写 → 改 inline `jhyy-setuc.exe set-uc .jhyy JHYY.SourceFile`(per-user HKCU 写,即使 UCPD.sys 阻断也至少给 MSYS2 OpenWithProgids shadow 让 file association 走 jhyy.exe 而非 notepad)。

### v1.8.3.2 — license RTF 文本对齐 (commit `4fa3945`, 2026-08-29)

**改动**: `installer/common/license.rtf` 顶部 `Version 1.5.0` → `Version 1.8.3`,对齐 v1.8.3 installer ship 产物。WiX `LicenseFile` 引用不变(`license.rtf` 路径不动)。

### .NET 8 runtime chain

v1.8.3 起,Burn bundle 必须 embed `.NET 8 Desktop Runtime`(`dotnet-runtime-8.0.30-win-x64.exe`,~80MB)— 因为 `jhyy-setuc.exe` 是 .NET 8 self-contained 但 MSI CustomAction 需要 `.NET 8 runtime present` 才能拉起。bundle 内部:
1. WiX 编译期:`wix build` 读 `JHY_DOTNET8_RUNTIME_EXE_PATH` 环境变量,把 .NET 8 runtime exe 包进 bundle。
2. 安装期:Burn detect 用户机器缺 .NET 8 Desktop Runtime → 装 bundle 内嵌 runtime → MSI install → MSI SYSTEM-context CustomAction 拉 jhyy-setuc.exe 写 UserChoice。
3. 卸载期:`jhyy-setuc.exe clear-uc .jhyy` 清 UserChoice + 清 HKCU shadow,确保卸载干净。

**总 bundle 大小**:v1.8.0 = ~1.6MB → v1.8.3 = ~30MB(增加 ~28MB 用于 .NET 8 Desktop Runtime)。`installer/SHA256.txt` 记录实际大小。

### `installer/common/jhyy-setuc/` 子目录

新建(2026-08-29),内含:
- `Program.cs` — .NET 8 console app,Mozilla reverse-engineered SHA256 hash algorithm + 写 `HKCU\UserChoice` + `HKCU\OpenWithProgids` + SYSTEM-context fallback
- `build.ps1` — `dotnet publish -c Release -r win-x64 --self-contained true /p:PublishSingleFile=false` → 产出 4 文件 .NET 8 bundle(进 `INSTALLDIR\bin\`)
- `jhyy-setuc.csproj` — .NET 8 project,`net8.0-windows` TFM

CLI 用法:
```
jhyy-setuc.exe set-uc <ext> <progid>     # 写 HKCU\UserChoice + HKCU\OpenWithProgids
jhyy-setuc.exe clear-uc <ext>            # 清 HKCU\UserChoice(卸载用)
jhyy-setuc.exe set-shadow <ext> <progid> # 仅清 MSYS2 HKCU OpenWithProgids shadow(per-user 路径覆盖)
```

### `installer/common/manual-fix-icon-cache.ps1`

新建(2026-08-29),用户手动 cache refresh helper —— Explorer 图标 cache 在某些 Win10 22H2+ 主机即使 registry 改对仍不刷新 brand icon。脚本跑 `ie4uinit.exe -show` + `taskkill /IM explorer.exe /F` + `start explorer.exe` 三步强制刷新。

不在 installer 自动跑(避免 UAC 二次弹窗),README 引导用户手动跑。详细调用见 `docs/internal/build.md` § 图标 cache。

### W-NNN 状态变化 (per `docs/internal/workarounds.md`)

| W-NNN | v1.8.0 ship | v1.8.3 ship |
|-------|-------------|-------------|
| W-059 (defer codegen silent crash) | ✅ RESOLVED 2026-08-28 | ✅ RESOLVED |
| W-060 (enum variant payload ABI) | ❌ INVALID 2026-08-28 | ❌ INVALID |
| W-061 (nested struct field offset) | ❌ INVALID 2026-08-28 | ❌ INVALID |
| W-062 (UserChoice/MSYS2 shadow 真修) | 🟡 DEFERRED v1.8 | ✅ RESOLVED 2026-08-29 (v1.8.3.1 闭环) |
| W-063 (UCPD.sys kernel filter) | 🟡 DEFERRED v1.8 | ✅ RESOLVED 2026-08-29 (v1.8.3 真修) |

**当前 ACTIVE user-space workaround 数**:0。**DEFERRED-to-v2.x**:2(W-057 UTF-8 3/4-byte codepoint + W-058 vendor QBE 缺 `remd`/`rems`)。**永久**:1(W-021 WiX Bal.wixext DLL 命名)。

**v1.5.5 scope (已完成)**:
- `.github/workflows/release.yml` — GH Actions release workflow (14 steps: checkout + MSYS2 + WiX + make stage0 + make + regress + bundle + SHA256 verify + release notes + MSI validate + release create + dry-run summary)
- `installer/gen-sha256.ps1` — SHA256.txt 生成 (sha256sum-compatible 格式, UTF-8 no BOM); `build.ps1 bundle` 自动调
- `installer/changelog-template.md` — Release notes 模板 (VERSION / ISO_DATE / URL 占位符)
- `installer/winget/manifests/j/JiHuiYiYou/JHYY/1.5.5/` — winget multi-file manifest (version + installer + locale en-US); InstallerSha256 在 release 时由 CI 填
- `installer/scoop/jhyy.json` — scoop manifest v3 schema (Burn bundle install + shortcuts + autoupdate)
- 关键 fix: bash `${VERSION}` 占位符在 MSYS2 bash 不展开 → 改 `${{ env.VERSION }}` ($env:VERSION in pwsh); `Add-Content` 写 GH Actions env file (no BOM 比 Out-File -Encoding utf8 稳)

**v1.5.4 scope (已完成)**:
- `installer/vscode-ext/package.ps1` — VSCode ext 打包 (vsce package + version patch)
- ~~`installer/common/install-vsix.bat` — 检测 `code` 命令 + 装 .vsix 脚本 (CustomAction deferred 调用)~~ → **superseded in v1.5.10**, deleted (dead code since v1.5.7 — parser bug; RunOnce inline replaces it)
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

**v1.8.3 install verification status**:
- ✅ `wix msi validate` clean (all standard ICEs pass)
- ✅ Burn bundle manifest 验证 (内嵌 MSI / theme.xml / thm.wxl / logo.png / license.rtf / wixstdba.exe payload 全部齐全 + .vsix chain via MSI embedded payload + .NET 8 Desktop Runtime 链 .NET 8 exe 内嵌)
- ✅ **v1.8.3 install/uninstall 验证已在交互式 desktop session 跑**(per W-062 / W-063 真修 commit `a134a80` / `ba071d8`,SYSTEM-context CustomAction + 3-attempt fallback)。验证步骤:
  ```powershell
  # 交互式 PowerShell (有 desktop 的话)
  jhyy-installer-1.8.3.exe  # 双击也行, Burn 弹 welcome dialog + .NET 8 runtime 检测/装
  # 期望: Welcome → Install → UAC → Progress(可能含 .NET 8 runtime 装) → Success → Close
  # 期望 (post-install):
  #   1. where jhyy  → C:\Program Files\JHYY\bin\jhyy.exe
  #   2. jhyy --version  → 1.8.3
  #   3. 双击 hello.jhyy  → jhyy.exe run (file association + brand icon)
  #   4. code --list-extensions  → 含 jhyy.jhyy-lang (VSCode ext 自动装, 若有 code)
  #   5. Start Menu → JHYY → Documentation / Quick Start / Compiler
  #   6. reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.jhyy\UserChoice" → 含 JHYY.SourceFile hash
  # 卸载 (Settings → Apps 或 Burn /uninstall)
  #   → jhyy-setuc.exe clear-uc .jhyy 清 UserChoice + HKCU OpenWithProgids shadow
  ```

## 目录结构

```
installer/
├── build.ps1             ← PowerShell 编排 (v1.5.1 起;v1.8.3 加 jhyy-setuc.exe build + .NET 8 runtime chain + if/else host detection PS5.1 兼容)
├── _stub/                ← minimal smoke test (v1.5.1)
│   ├── stub.wxs          ← minimal Package definition
│   └── stub.msi          ← build 产物 (gitignored, build 后存在)
├── common/               ← 共享资源 (license + bitmap + post-install scripts + jhyy-setuc)
│   ├── license.rtf       ← 双语 license (中英) (v1.8.3.2 顶部 Version 1.8.3)
│   ├── install-configure-all.bat    ← post-install batch (RunOnce + inline `code --install-extension` + jhyy-setuc shadow clear)
│   ├── install-configure-env.ps1    ← 环境变量配置 helper
│   ├── install-configure-vscode.ps1 ← VSCode ext 单独 helper
│   ├── JHYY Documentation.url / JHYY Quick Start.url ← Internet Shortcut (Start Menu)
│   ├── manual-fix-icon-cache.ps1    ← 手动 cache refresh helper (v1.8.3 加)
│   └── jhyy-setuc/                   ← v1.8.3 新增 .NET 8 CLI (UserChoice hash writer)
│       ├── Program.cs
│       ├── jhyy-setuc.csproj
│       ├── build.ps1
│       └── (build 产物: jhyy-setuc.exe / .dll / .deps.json / .runtimeconfig.json)
├── jhyy-icon-{16,32,48,64,128,256}.png  ← brand icon PNGs (v1.5.7-rc1)
├── jhyy-icon.ico         ← multi-size .ico (ARPPRODUCTICON + FileAssoc + Start Menu)
├── jhyy-file-icon.svg    ← .jhyy 文件关联专用 SVG 图标 (v1.8.1 加)
├── jhyy-banner.bmp       ← MSI dialog top banner (493x58, brand)
├── jhyy-welcome.bmp      ← MSI welcome dialog content (493x312, brand)
├── jhyy-logo-{64,128}.png ← 品牌 logo PNG (辅助 ARPPRODUCTICON multi-size)
├── build-jhyy-icons.ps1  ← regenerates .ico + BMPs from vscode-ext/icon.svg
├── gen-sha256.ps1        ← SHA256.txt 生成 (sha256sum-compatible, UTF-8 no BOM)
├── changelog-template.md ← Release notes 模板
├── GUIDS.md              ← WiX ProductCode / UpgradeCode / Component GUIDs 锁
├── compiler/             ← v1.5.2 主 MSI (done;v1.8.3 加 SYSTEM-context CustomAction)
│   ├── jhyy-compiler.wxs ← Package / Feature / Component + JHYYSetUCForAllUsers CustomAction
│   └── Locale.zh-CN.wxl  ← 中文 UI string
├── vscode-ext/           ← v1.5.4 done (VSCode extension)
│   ├── package.ps1       ← vsce package 脚本 (v1.8.3 加 `windres` embed jhyy-icon.ico 16x16)
│   ├── jhyy-lang-X.Y.Z.vsix  ← build 产物 (gitignored)
│   └── (build 完产物在 installer/build-artifacts/)
├── os/                   ← jhyy_OS placeholder (后续 OS sprint 填)
│   ├── .gitkeep
│   └── README.md
├── scoop/                ← scoop manifest v3 (reference only, deferred v2.x publish)
│   └── jhyy.json
├── winget/               ← winget multi-file manifest scaffold (deferred v2.x publish)
│   └── manifests/j/JiHuiYiYou/JHYY/
│       ├── 1.5.5/        ← 3 manifest 文件占位 (installer + locale en-US + version) — 已存在,未真 publish
│       └── 1.5.6/        ← 3 manifest 文件占位,同上
├── Theme.xml             ← Burn custom theme (Welcome/Progress/Modify/Success/Failure page)
├── Bundle.wxs            ← Burn bundle, 链 JHYYCompilerMsi + .NET 8 Desktop Runtime
├── Bundle.zh-CN.wxl      ← 中文 UI strings
├── SHA256.txt            ← 三件产物 SHA256 (gitignored → **checked in**,per release 更新;36 行:1.0.0 → 1.8.3)
└── README.md             ← 本文件
```

> **注意**: `installer/SHA256.txt` 当前 **checked in**(gitignored 状态有变更),每 release 手工跑 `gen-sha256.ps1` 重新生成并 commit。`installer/build-artifacts/` 内 build log + .NET 8 runtime cache + 历史 verify-step*.ps1 / _install-*.log 是 v1.5.4 调试残留,本次未清理(留作 v2.x 决定)。

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
- `installer/build-artifacts/jhyy-compiler-X.Y.Z.msi` (~995KB) — 主 MSI, 装 jhyy.exe + qbe.exe + jhyy-setuc.exe (v1.8.3+) + .vsix + file association + Start Menu
- `installer/build-artifacts/jhyy-installer-X.Y.Z.exe` (**v1.5.x = ~1.6MB;v1.8.x = ~30MB**, 含 .NET 8 Desktop Runtime embed) — Burn bundle (installer wrapper)
- `installer/build-artifacts/jhyy-lang-X.Y.Z.vsix` (~13KB) — VSCode extension (v1.8.x 起含 brand icon + runFile/compileOnly commands)
- `installer/build-artifacts/*.wixpdb` — WiX 调试符号 (gitignored)
- `installer/SHA256.txt` — 3 产物 SHA256 (**checked in**, per release `gen-sha256.ps1` 更新;1.0.0 → 1.8.3 共 36 行)
- `installer/build-artifacts/dotnet/` — .NET 8 Desktop Runtime cache (`dotnet-runtime-8.0.30-win-x64.exe`,v1.8.3 起 bundle 内嵌)

## v1.8.x 发布流程

### 本地 build (任意版本, v1.8.x)

```powershell
# 单一入口 (v1.8.x 起: build jhyy-setuc.exe 在前 + .NET 8 runtime chain 在后)
JHY_VERSION=1.8.3 powershell -File installer/build.ps1 bundle
# 期望产出: installer/build-artifacts/jhyy-installer-1.8.3.exe (~30MB, 含 .NET 8 Desktop Runtime)
#           + jhyy-compiler-1.8.3.msi (~995KB, 含 jhyy-setuc.exe 4 文件 bundle)
#           + jhyy-lang-1.8.3.vsix (~13KB)
#           + SHA256.txt (4 产物)
```

### GitHub Actions — tag 触发 (正式 release)

```bash
git tag v1.8.3
git push origin v1.8.3
# GH Actions 自动: build jhyy.exe → regress (102/102+4 baseline) → build.ps1 bundle (含 jhyy-setuc + .NET 8)
#                  → SHA256 → release notes → upload 4 assets → create GitHub Release
# 期望: GitHub Release "JHYY 1.8.3" 标 latest, 4 个 asset (.exe / .msi / .vsix / SHA256.txt)
```

### GitHub Actions — RC dry-run (workflow_dispatch)

```bash
gh workflow run release.yml -f version=1.8.3-rc1 -f dry_run=false
# 期望: GH Release "JHYY 1.8.3-rc1 [RC]" 标 prerelease
```

### GitHub Actions — 完全 dry-run (build 闭环, 不上传)

```bash
gh workflow run release.yml -f version=1.8.3-rc1 -f dry_run=true
# 期望: build 跑通 + SHA256 生成, 但不 upload 不 create release; summary 在 GH Actions UI
```

### 第三方 manifest publish (deferred v2.x)

- **winget**: `installer/winget/manifests/j/JiHuiYiYou/JHYY/${VERSION}/` 3 文件 — 实际 PR 到 [winget-pkgs](https://github.com/microsoft/winget-pkgs) 推到 v2.x
- **scoop**: `installer/scoop/jhyy.json` — 实际 PR 到 [ScoopInstaller/Main](https://github.com/ScoopInstaller/Main) 推到 v2.x

⚠️ **Manifest 文件是 reference (no publish)**: 当前 CI 仅生成 SHA256.txt 给 Release asset; manifest 文件的 `InstallerSha256` 字段是 `<FILL_AT_RELEASE_TIME_FROM_SHA256.txt>` placeholder, 推 v2.x 前需要 (a) 真发布 GUID 替换 dev placeholder + (b) CI step 读 SHA256 填 manifest + (c) manifest 跟 release 同 PR。

## 后续 v2.x 计划 (deferred, 不在 v1.x scope)

- winget 3 文件 manifest 真发布到 [winget-pkgs](https://github.com/microsoft/winget-pkgs)(当前 `installer/winget/manifests/j/JiHuiYiYou/` 仅 `JiHuiYiYou` 占位目录,`JHYY/${VERSION}/` 三件 manifest 待 v2.x 填)
- scoop 真发布到 [ScoopInstaller/Main](https://github.com/ScoopInstaller/Main)(`installer/scoop/jhyy.json` 待真发布)
- code signing: v1.x 不签 Authenticode,v2.0 加 self-signed + cert chain
- WiX CustomAction 走 BAFunctions: v1.8.x 走 SYSTEM-context CustomAction + `jhyy-setuc.exe`,v2.x 重构成 Burn BAFunctions(inline C# DLL)
- 集成 `compiler/src0/*.jhyy` 编译产出 `jhyy_v1.exe.exe` 进 installer (v1.x 仅 `jhyy.exe` C 端 binary,v2.x 转 self-host 二进制)

## 关联文档

- [`docs/plans/v1/v1.5.0任务清单 + 概要设计.md`](../docs/plans/v1/v1.5.0任务清单 + 概要设计.md) — 完整 5-sprint 计划 + 决策点
- [`docs/internal/build.md`](../docs/internal/build.md) — 编译器构建 (本 README 是 installer 构建)

## 工具链决策

- **PowerShell 不是 .cmd**: WiX 4/7 官方文档示例走 PowerShell, 现代 Windows dev convention 通用; MSYS2 bash 调 .cmd 时 arg passing 有 quirk, .ps1 更稳。
- **WiX 4/7 不是 WiX 3**: `wix build` CLI 取代 v3 的 candle + light + burn 三步, 一行命令搞定。
- **`wix.toml` 不存在**: plan 列了但 WiX 4/7 不需要 (那是 MSBuild 风格, CLI 路径走 `wix build` 加 -d / -b 参数即可)。
- **code signing 推到 v2.x**: v1.5.0 ship 时不签 Authenticode, 用户看到 "Unknown Publisher" warning, 文档告诉用户 "More info → Run anyway"。
