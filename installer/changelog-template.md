# JHYY ${VERSION} Release

> **Release date**: ${ISO_DATE}
> **Download**: [jhyy-installer-${VERSION}.exe](${INSTALLER_URL}) (~30MB Burn bundle — v1.8.x 起含 .NET 8 Desktop Runtime embed;v1.5.x = ~1.6MB 无 .NET 8)
> **SHA256**: 见 [SHA256.txt](${SHA256_URL})
> **Compatibility**: Windows 10 1809+ / Windows 11 / Windows Server 2019+ (x64)

## 安装

双击 `jhyy-installer-${VERSION}.exe` → next-next-finish。需要 admin 权限 (per-machine MSI 写 HKLM PATH)。

装完 `where jhyy` 应返回 `C:\Program Files\JHYY\bin\jhyy.exe`。

**前置**: 装完会提示用户装 [MSYS2](https://www.msys2.org/) + ucrt64 GCC (jhyy 编 .jhyy → .exe 需要 qbe + gcc link)。Welcome page 已说明。

## 主要改动 (v${VERSION})

<!-- 手动从 docs/logs/v1/changelog-v1.${MINOR}.0.md 复制当前 sprint 段 -->

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