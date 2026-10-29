# JHYY ${VERSION} Release

> **Release date**: ${ISO_DATE}
> **Download**: [jhyy-installer-${VERSION}.exe](${INSTALLER_URL}) (~55MB Burn bundle — 含 .NET 8 Desktop Runtime;v4.1.0 起另含内置 GCC 工具链)
> **SHA256**: 见 [SHA256.txt](${SHA256_URL})
> **Compatibility**: Windows 10 1809+ / Windows 11 / Windows Server 2019+ (x64)

## 安装

双击 `jhyy-installer-${VERSION}.exe` → next-next-finish。需要 admin 权限 (per-machine MSI 写 HKLM PATH)。

装完 `where jhyy` 应返回 `C:\Program Files\JHYY\bin\jhyy.exe`。

**前置**: **v4.1.0 起不需要** —— installer 自带一份最小原生 ucrt64 工具链
(gcc + binutils + CRT,装在 `C:\Program Files\JHYY\toolchain\`),装完即可
`jhyy compile hello.jhyy`。v4.1.0 之前需要自己装 [MSYS2](https://www.msys2.org/)
+ ucrt64 GCC。

**想用自己的 gcc?** 设 `JHY_GCC=<gcc.exe 全路径>`,或在 `%JHYY_HOME%\env.txt`
里写一行 `JHY_GCC=<gcc.exe 全路径>`。默认用内置那份(版本受控、产物可复现)。

## 主要改动 (v${VERSION})

${MAIN_CHANGES}

## 验证 (6 项)

1. `where jhyy` → `C:\Program Files\JHYY\bin\jhyy.exe`
2. `jhyy --help` → 首行 `jhyy compiler v${VERSION} (self-hosted)`
3. **在没装 MSYS2 的机器上**:`jhyy compile hello.jhyy` → 产出 hello.exe(链接用的是自带工具链)
4. 双击 `.jhyy` 文件 → `jhyy.exe run`
5. `code --list-extensions` → 含 `jhyy.jhyy-lang` (VSCode ext, 装了 VSCode 才生效)
6. Start Menu → JHYY → Documentation / Quick Start / Compiler

## 卸载

- Settings → Apps → JHYY Compiler → Uninstall
- 或 Burn: `jhyy-installer-${VERSION}.exe /uninstall`

## 已知问题

- ⚠️ **代码未签名** — Windows SmartScreen 弹 "Unknown publisher" warning, 选 "More info → Run anyway"。正式签名 (Authenticode) 待排期 (需 HSM / EV cert)
- ⚠️ **winget / scoop 还没提交到上游仓库** — 本仓里的 manifest 只是 *reference*; 要真能 `winget install` / `scoop install` 还得向上游提 PR (路径见下)
- ℹ️ **内置 gcc 的版本是钉死的** — 发行时钉的那个版本随包走(产物可复现)。想用更新或更旧的 gcc:设 `JHY_GCC`(见「安装」段)

## 完整 changelog

见 [`docs/logs/v4/changelog-v4.0.0.md`](https://github.com/JiHuiYiYou/JiHuiYiYou-compiler/blob/main/docs/logs/v4/changelog-v4.0.0.md)(v4.x 的 umbrella;各版本的段都在里面)

## 第三方包管理 (manifest reference, 尚未提交到上游)

- **winget**: `installer/distribution/winget/manifests/j/JiHuiYiYou/JHYY/${VERSION}/` — 3 manifest 文件 (version + installer + locale en-US)
- **scoop**: `installer/distribution/scoop/jhyy.json` — single-file manifest

实际 PR 到 [winget-pkgs](https://github.com/microsoft/winget-pkgs) / [ScoopInstaller/Main](https://github.com/ScoopInstaller/Main) 待排期 (per `docs/plans/v1/v1.5.0任务清单 + 概要设计.md` 决策-11)。
