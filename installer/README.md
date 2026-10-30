# JHYY Installer（Windows）

> **装机用户唯一入口文档。**
>
> **版本号与产物尺寸见 [`docs/FACTS.md`](../docs/FACTS.md) § 1** —— 不要在这里复述。

---

## 装什么

| 产物 | 说明 |
|---|---|
| `jhyy-installer-<ver>.exe` | **Burn bundle**（WiX）—— GUI 安装器：编译器 + `.jhyy` 文件关联 + VS Code 扩展 + PATH + 桌面/开始菜单快捷方式 + 文档 |
| `jhyy-compiler-<ver>.msi` | 同样内容的 **MSI** —— 无 GUI，供企业 / SCCM 分发 |

两个产物都**自带一份最小原生 ucrt64 工具链**（自 v4.1.0）⇒ **最终用户不需要 MSYS2**。

下载：GitHub Release（`JiHuiYiYou/JiHuiYiYou-compiler`）。也有 scoop / winget manifest：

- scoop ⇒ `installer/distribution/scoop/jhyy.json`
- winget ⇒ `installer/distribution/winget/manifests/j/JiHuiYiYou/JHYY/<ver>/`

---

## 目录结构

```
installer/
├── build.ps1                   构建入口(stub / compiler / bundle)
├── assets/
│   ├── license.rtf             MSI 的 EULA(版本号由 bump_version.py 刷)
│   ├── icons/                  品牌图标(.ico / .png 各尺寸)
│   └── bitmaps/                Burn 主题用的位图
├── common/
│   ├── install-configure-all.bat   RunOnce 的落地脚本(装完写 PATH / 文件关联)
│   ├── jhyy-bash.cmd               启动一个带 jhyy 的 bash
│   ├── jhyy-setuc/                 .NET 8 的 UserChoice 写器(UCPD.sys bypass)
│   ├── JHYY Documentation.url
│   └── JHYY Quick Start.url
├── scripts/
│   ├── collect-toolchain.ps1       采集工具链(求头闭包 / DLL 闭包 / 编预编 .o)
│   ├── gen-toolchain-wxs.ps1       manifest → WiX <Fragment>(GUID 用 UUIDv5 确定性生成)
│   ├── verify-toolchain.ps1        **常驻门**:可重定位 / 头闭包 / poisoned PATH / 无 PATH / windres / 预编 .o 字节一致
│   ├── verify-vscode-bash-detect.ps1   VSCode bash 探测的门
│   ├── build-jhyy-icons.ps1        把图标编进 jhyy.exe 的 PE 资源段
│   └── gen-sha256.ps1             生成 SHA256.txt
├── toolchain/                 内置工具链的清单 / 许可证 / manifest
│   └── README.md              工具链设计 ⇒ 完整说明在这
├── wix/
│   ├── compiler/jhyy-compiler.wxs   MSI 主文件
│   ├── Bundle.wxs                   Burn bundle
│   ├── Bundle.zh-CN.wxl / Theme.xml
│   └── _archive/                   历史 wxs(stub 等)
├── distribution/
│   ├── scoop/jhyy.json
│   └── winget/manifests/j/JiHuiYiYou/JHYY/<ver>/
├── release-notes/            每版的 release note 正文(release.yml 从这里取)
├── vscode-ext/package.ps1    把 vscode-ext/ 打成 .vsix
├── GUIDS.md                  **GUID 锁表** —— 改组件前必看
└── os/                       OS installer 的占位(OS 线尚未启动)
```

---

## 构建

```powershell
# stub：最小 WiX 冒烟测试
powershell -NoProfile -ExecutionPolicy Bypass -File installer/build.ps1 stub

# compiler：只出 MSI
powershell -NoProfile -ExecutionPolicy Bypass -File installer/build.ps1 compiler

# bundle：MSI + Burn bundle + VSIX + SHA256.txt
powershell -NoProfile -ExecutionPolicy Bypass -File installer/build.ps1 bundle
```

产物落在 **`installer/build-artifacts/`**（`bin/` · `toolchain/` · `wix/` · `vscode-ext/`）。

⚠️ `bundle` 依赖 `compiler/build/bin/jhyy.exe`（自举锚点）已存在 ⇒ 先 `make`。

### SHA256.txt

**是构建产物，不入仓**（`.gitignore` 里有 `installer/SHA256.txt`）。
`build.ps1 bundle` 生成它，`release.yml` 把它作为 Release asset 上传
（`releases/download/v<ver>/SHA256.txt`），并在发布前校验内容。

---

## 组件 GUID

[`GUIDS.md`](GUIDS.md) 是**锁表** —— WiX 的 Component GUID 一旦发布就不能改，
否则升级时新版本装不上。

**改组件内容前先看那张表**：新增组件要在表里登记一行（GUID 用 UUIDv5 确定性生成），
删除组件要把那行划掉。

---

## 工具链

`installer/toolchain/README.md` 是完整设计说明。三个要点：

1. **解析顺序**：`JHY_GCC` → `%JHYY_HOME%\env.txt` → **内置** → `C:\msys64` → PATH → 裸 `gcc`
   ⇒ 默认用内置那份（确定性 + 版本受控）。
2. **四个坑**（`ucrt64/` 那层不能改名 / 目录不能拍平 / `as.exe`+`ld.exe` 要放两份 /
   头闭包不能只收 `*.h`）⇒ 见 [`docs/internal/build.md`](../docs/internal/build.md) § 工具链。
3. **不打包 POSIX 层** —— 实测 MSYS2 的运行时不做「按树搬迁」⇒ 半残态。这条计划已作废。

---

## 相关

- 构建与门 ⇒ [`docs/internal/build.md`](../docs/internal/build.md)
- 版本号自动化 ⇒ [`docs/internal/build.md`](../docs/internal/build.md) § 版本号自动化
- release note 模板 ⇒ [`changelog-template.md`](changelog-template.md)
- 每版 release note ⇒ [`release-notes/`](release-notes/)
