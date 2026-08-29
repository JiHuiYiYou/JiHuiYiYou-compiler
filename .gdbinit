# JHYY .gdbinit — auto-source the pretty printer for any gdb session
# started from the project root.
#
# Per docs/plans/v1/v1.4.0任务清单 + 概要设计.md § v1.4.3:
#   "仓库 .gdbinit 只做 auto-source, 不覆盖用户配置 (不用 `set print ...` 等)"
#
# Usage from project root:
#   gdb ./gdb_pretty_test.exe
#   (gdb) jhyy-load-types compiler/tests/examples/gdb_pretty_test.jhyy
#   (gdb) b gdb_pretty_test.jhyy:65
#   (gdb) r
#   (gdb) jhyy-pretty $rbp-72 Point
#
# NOTE on auto-load safe-path: gdb refuses to auto-load .gdbinit unless
# the path is in `auto-load safe-path`. Add to ~/.gdbinit once:
#   add-auto-load-safe-path C:/Users/liuzhen/Desktop/coding/JiHuiYiYou
# (Or use `source .gdbinit` from gdb directly.)

python
import os
# gdb's Python doesn't expose `__file__`. Try gdb current objfile's
# compilation dir as a fallback, otherwise just hardcode the relative
# path (project root cwd).
pretty = "compiler/src0/scripts/dev/gdb_pretty.py"
if not os.path.exists(pretty):
    # Try to derive from the current working directory
    pretty = os.path.join(os.getcwd(), "compiler", "src0", "scripts", "dev", "gdb_pretty.py")
if os.path.exists(pretty):
    gdb.execute(f"source {pretty}")
    print(f"[.gdbinit] auto-sourced {pretty}")
else:
    print(f"[.gdbinit] gdb_pretty.py not found (cwd={os.getcwd()})")
end