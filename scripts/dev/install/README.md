# scripts/dev/install/

JHYY installer / uninstall / 升级相关的开发脚本 (需要 admin / MSYS2 env)。

| 脚本 | 用途 | 触发时机 |
|------|------|----------|
| `check-elev.ps1` | 检查当前 session 是否 admin (返回 ASCII 0/1) | 任何 install 流程的前置 |
| `copy-jhyy.ps1` | 把 `compiler/build/bin/jhyy.exe` 复制到 `C:\Program Files\JHYY\bin\` (需要 admin) | dev 调试 jhyy.exe binary 后快速 reinstall |
| `restore-jhyy.ps1` | 同 copy-jhyy, 但从 `tmp/` 备份恢复旧 binary | 调试过程中 binary 被破坏后回退 |
| `prep-clean-install.ps1` | install 前清理 MSI / 服务 / 残留注册表 (clean-slate 测试) | E2E install 测试前置 |
| `uninstall-all-jhyy.ps1` | **DESTRUCTIVE** — 卸载所有 MSI 注册的 JHYY 产品 | clean-slate 测试 |
| `uninstall-v2.ps1` | 用 `Get-Package` auto-elevation 卸载所有 JHYY | 同上 (新方法, 免手动 UAC) |
| `diag-uninstall.ps1` | 诊断 1603 MSI failure + 检查 INSTALLDIR 状态 | MSI install 失败时调试 |

**不要**把这些脚本路径硬编码到任何 installer / installer 文档。全部用 `$PSScriptRoot` 派生相对路径。
**不要**放进 installer/ 目录 — 这些是 dev-only 操作, 不随 installer ship。