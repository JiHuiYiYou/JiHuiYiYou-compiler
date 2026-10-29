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

**lang-spec 覆盖审计** —— 把 `jhyy-lang-spec-v4.0.0.md`(1071 行)逐条拆成可观察行为、
每条配一个探针扫全量测试语料(228 个 `.jhyy`)⇒ 得出 17 个「零命中」探针,逐个复核
⇒ **补 49 条回归门**(6 个 std lib 真身覆盖 + 11 个 spec 正向行为 + 31 个错误诊断门
+ 1 个聚合比较字段类型矩阵)。**补测试的过程本身挖出 14 个真缺陷并全部真修**:

- **std lib 三处真缺陷**(此前 6 个 std 模块的测试全是 inline 副本 ⇒ 改真身零覆盖):
  字节循环写穿 **4n** 字节(`*(p as *i32) = v` 的 store 宽度跟 pointee 走 ⇒ 请求 n 字节
  实际写 4n)/ `import string;` 编译失败 / arena 分配互相踩 ⇒ AV
- **命名与作用域四个真缺陷**:同作用域 shadowing 让编译器崩溃(0xC0000005)/ 重名
  fn·type·const·参数 ⇒ 空指针写崩溃(改为编译期报错)/ match arm 不开作用域 ⇒
  **payload 被静默丢弃**/ 重名 import ⇒ 崩溃 + 重名类型参数 ⇒ 误导性错误链
- **浮点与指针**:浮点↔指针**不是按位重解释**(改为数值转换 + 饱和语义)/
  数组类型的 struct 字段**没被拷贝**/ 整数→浮点 conv 表丢符号性(f32 目标拿到 f64 位模式)/
  IL lexer 缺 `'u'` 分支 ⇒ `ultof`/`uwtof` 是**死 op**/ f64·f32 字面量解析**丢掉指数**
  (≥1e16 的浮点常量全错)/ `emit_conv_ultof` 算法把最低位清零
- **自举闭环门验错了代**(W-147):旧逻辑验的是**锚点**的不动点、`mv` 装出去的却是
  **没被验过**的第 1 代 ⇒ 改成**迭代到不动点**(门从「验锚点」升级成「验装出去的那个产物」)
- **MCP 工具三条真缺陷**:`jhyy_workarounds` 计数不可信(13 条幽灵条目)/ `jhyy_get_il`
  从来没成功过 / 两份 env 构造器分叉 ⇒ regress 报 207/277 假失败
- **三处「门没在验它声称在验的东西」**:EXPECT-ERROR 在编译意外成功时判 PASS /
  `#[no_std]` 零覆盖(链接行写错入口符号 ⇒ 100% 链不过)/ `&&T` 的报错路径是死代码 /
  `*argv` 只 load 1 字节 ⇒ 验的是「堆地址最低字节 ≠ 0」的**假信号**

**台账**:ACTIVE 桶**两次清空** ⇒ **0 ACTIVE / 0 DEFERRED**;XFAIL 也归零。

**回归**:257 PASS + 0 XFAIL + 0 failed + 20 SKIP(277 total,新增 49 条)·
artifact_checks 14 PASS · closure_check PASS(v2.s == v3.s)· fixed_point 17 PASS。

> ⚠️ **本版仍需要 MSYS2 + ucrt64 GCC**(链接 .jhyy → .exe 用)。
> **v4.1.0 起 installer 自带工具链,不再需要** —— 见下一版发布说明。

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