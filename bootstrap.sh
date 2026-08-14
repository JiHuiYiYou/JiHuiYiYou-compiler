#!/bin/bash
# bootstrap.sh -- One-command clone-and-use setup for the JHYY compiler.
#
# Builds compiler/build/bin/jhyy.exe from C source, then runs the regression
# suite so you know everything is wired up. Safe to re-run.
#
# Requires:
#   * MSYS2 (ucrt64) -- installs GCC + binutils
#     https://www.msys2.org/
#   * Python on PATH (for regress.py)

set -e
cd "$(dirname "$0")"

GCC="/c/msys64/ucrt64/bin/gcc.exe"
SRC="compiler/src"
BIN="compiler/build/bin/jhyy.exe"

echo "=== JHYY bootstrap ==="

if [ ! -x "$GCC" ]; then
    echo "[ERROR] GCC not found at $GCC"
    echo "Install MSYS2 from https://www.msys2.org/ then: pacman -S mingw-w64-ucrt-x86_64-gcc"
    exit 1
fi

echo "[1/4] Building $BIN ..."
"$GCC" -std=c11 -Wall -Wextra $SRC/*.c -o "$BIN" -I "$SRC"

# 刚构建的二进制就是新基准 — 不重锁 baseline 的话, regress 会因 sha 漂移
# early-abort, 一个测试都不跑却报 "failures".
echo "[2/4] Locking regress baseline to freshly built binary ..."
python mcp-jhyy/jhyy_regress.py --save-baseline --binary "$BIN"

echo "[3/4] Running regression suite ..."
python compiler/build/bin/regress.py || echo "[WARN] Regression reported failures - see output above."

echo "[4/4] Bootstrap complete."
echo
echo "Next steps:"
echo "  * In this terminal:    jhyy run compiler/tests/examples/hello.jhyy"
echo "  * In VSCode:          open hello.jhyy, press Ctrl+Shift+B to run"
echo "  * Run a task:         Ctrl+Shift+P, \"Tasks: Run Task\", \"JHYY: Run\""
echo "  * Re-bootstrap:       ./bootstrap.sh"
