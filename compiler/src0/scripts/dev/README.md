# compiler/src0/scripts/dev/

src0/ 专属 debug helper 脚本 (与根目录 `scripts/dev/` 的 install/build/bench/test
脚本语义不同)。

## 当前内容

- `gdb_pretty.py` — GDB pretty-printer for JHYY 运行时类型
  (Arena / Node / Token / Sym 等 struct 字段 human-readable 打印)。
  调用: `source compiler/src0/scripts/dev/gdb_pretty.py` 进 `.gdbinit` 或 gdb 会话。
  ref: `.gdbinit` (项目根)。

## 跟根 scripts/dev/ 的区别

| 路径 | 用途 | 例 |
|------|------|----|
| `scripts/dev/` (根) | install / build / bench / test 操作脚本 | `install/check-elev.ps1`, `bench/self_host_bench.sh`, `test/test-orchestrator.bat` |
| `compiler/src0/scripts/dev/` | src0 源码相关的开发辅助 | `gdb_pretty.py` (JHYY struct pretty-print) |

不要混淆。Phase 5 (polish) 会进一步子分类 `scripts/dev/` 根为 `install/`, `build/`, `bench/`, `test/`。