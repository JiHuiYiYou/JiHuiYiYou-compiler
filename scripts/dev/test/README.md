# scripts/dev/test/

E2E test 入口 (跟 `compiler/tests/` 单元测试区分 — 这里是 MSYS2 / Windows env 集成测试)。

| 脚本 | 用途 |
|------|------|
| `test-gcc.cmd` | 验证 MSYS2 + ucrt64 GCC toolchain 完整 (gcc/qbe/jhyy 三件套可 PATH 找到) |
| `test-orchestrator.bat` | 模拟 post-v1.5.10 orchestrator 3 步骤 (含 inline `code --install-extension`) |
| `test-vsix.bat` | v1.5.9 时代的 .vsix install 测试入口 (superseded by orchestrator, 保留用于 legacy 调试) |

调用方式 (MSYS2 bash):
```bash
cmd //c scripts/dev/test/test-gcc.cmd
cmd //c scripts/dev/test/test-orchestrator.bat
```

新 E2E 测试脚本应放此处, 不写到 `compiler/tests/` (后者是 .jhyy 单元测试)。