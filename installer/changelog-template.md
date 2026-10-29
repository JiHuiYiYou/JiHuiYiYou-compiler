# JHYY ${VERSION} Release

> **Release date**: ${ISO_DATE}
> **Download**: [jhyy-installer-${VERSION}.exe](${INSTALLER_URL}) (~30MB Burn bundle — v1.8.x 起含 .NET 8 Desktop Runtime embed;v4.1.0 起另含内置工具链)
> **SHA256**: 见 [SHA256.txt](${SHA256_URL})
> **Compatibility**: Windows 10 1809+ / Windows 11 / Windows Server 2019+ (x64)

## 安装

双击 `jhyy-installer-${VERSION}.exe` → next-next-finish。需要 admin 权限 (per-machine MSI 写 HKLM PATH)。

装完 `where jhyy` 应返回 `C:\Program Files\JHYY\bin\jhyy.exe`。

**前置**: **v4.1.0 起不需要** —— installer 自带一份最小原生 ucrt64 工具链
(gcc + binutils + CRT,装在 `C:\Program Files\JHYY\toolchain\`),装完即可
`jhyy build hello.jhyy`。v4.1.0 之前需要自己装 [MSYS2](https://www.msys2.org/)
+ ucrt64 GCC。

**想用自己的 gcc?** 设 `JHY_GCC=<gcc.exe 全路径>`,或在 `%JHYY_HOME%\env.txt`
里写一行 `JHY_GCC=<gcc.exe 全路径>`。默认用内置那份(版本受控、产物可复现)。

## 主要改动 (v${VERSION})

**installer 自带工具链** —— 从这一版起,装机用户**不需要 MSYS2**也能编译 `.jhyy`。

之前 MSI 里有 `<Launch Condition="Installed OR MSYS2_GCC_FOUND">` + 4 路 MSYS2 探测
⇒ **没装 MSYS2 的机器根本装不上这个编译器**;装上了的人用的也是**他自己那份** gcc
⇒ 版本不受控,且「PATH 顺序 ⇒ 链接失败且 stderr 零输出」那个坑照样发作。

- **内置一份最小原生 MSYS2 ucrt64 工具链**(gcc + binutils + CRT + 编译器自用的头文件
  闭包,379 个文件 / 92 MB 原始)⇒ MSI 27 MB、installer.exe 54 MB。
- **默认用内置那份**:解析顺序 `JHY_GCC` → `%JHYY_HOME%\env.txt` → **内置** →
  `C:\msys64` → PATH → 裸 `gcc` ⇒ 确定性 + 版本受控 + **不依赖用户 PATH 形态**。
- **两条护栏**:链接失败时必打一行 `using gcc: <path> (source: bundled|JHY_GCC|env.txt|
  msys2|PATH)`(解析结果**可见**);installer **不**代写 `env.txt`(留给用户显式覆盖)。
- **预编 `.o`**:随包发 `runtime.o` / `jhyy_helpers.o` ⇒ 每次链接 5045 ms → **531 ms**。
- **TMP 护栏**:spawn gcc 前补 `TMP`/`TEMP`/`TMPDIR`(gcc 在这三个全 unset 时把中间
  产物写到 cwd ⇒ 只读目录下链接失败)。
- **拆门槛**:删掉 MSI 的 LaunchCondition 与 4 路 MSYS2 探测。
- **合规**:随包发各包许可证原文 + `SOURCES.txt`(实际装着的包版本 + 上游源码获取方式)。
- **7 条常驻门**(可重定位 / 头闭包 / poisoned PATH / 无 PATH / windres / 预编 `.o`
  字节一致 / DLL 闭包)⇒ 在 gcc 15.2.0 与 gcc 16.2.0 上都 7/7 PASS。

> ⚠️ **破坏性变更**:默认 gcc 从「你自己机器上的 MSYS2」变成「内置那份」。
> 想用回自己的:`JHY_GCC=<gcc.exe 全路径>` 或在 `%JHYY_HOME%\env.txt` 里写一行
> `JHY_GCC=<gcc.exe 全路径>`。

顺带修的既有 bug:MSI 的 Bal 扩展 DLL 路径写死了 WiX 版本 ⇒ **WiX 一升级,发版就挂在
最后一步**(实测 v4.0.22 的发布就死在这儿,MSI 都编好了)⇒ 改成扫目录。

## 验证 (5 项)

1. `where jhyy` → `C:\Program Files\JHYY\bin\jhyy.exe`
2. `jhyy --version` → `${VERSION}`
3. 双击 `.jhyy` 文件 → `jhyy.exe run`
4. `code --list-extensions` → 含 `jhyy.jhyy-lang` (VSCode ext, 装了 VSCode 才生效)
5. Start Menu → JHYY → Documentation / Quick Start / Compiler

## 卸载

- Settings → Apps → JHYY Compiler → Uninstall
- 或 Burn: `jhyy-installer-${VERSION}.exe /uninstall`

## 已知问题

- ⚠️ **代码未签名** — Windows SmartScreen 弹 "Unknown publisher" warning, 选 "More info → Run anyway"。正式签名 (Authenticode) 推到 v2.x (需 HSM / EV cert)
- ⚠️ **MSYS2 + ucrt64 GCC 不在 bundle 里** — Welcome page 引导用户装, 不自动装 (~85MB toolchain 太重, 走力度 1 检测+引导决策)
- ⚠️ **Dev placeholder GUID** — 内部测试用 `A1B2C3D4-...` / `BBCCEEFC-...` GUID; 真发布前替换为 uuidgen 出的真 GUID (见 `.wxs` 注释)

## 完整 changelog

见 [`docs/logs/v1/changelog-v1.${MINOR}.0.md`](https://github.com/JiHuiYiYou/JiHuiYiYou-compiler/blob/main/docs/logs/v1/changelog-v1.${MINOR}.0.md)

## 第三方包管理 (manifest reference, no publish yet)

- **winget**: `installer/winget/manifests/j/JiHuiYiYou/JHYY/${VERSION}/` — 3 manifest 文件 (version + installer + locale en-US)
- **scoop**: `installer/scoop/jhyy.json` — single-file manifest

实际 PR 到 [winget-pkgs](https://github.com/microsoft/winget-pkgs) / [ScoopInstaller/Main](https://github.com/ScoopInstaller/Main) 推到 v2.x (per `docs/plans/v1/v1.5.0任务清单 + 概要设计.md` 决策-11)。