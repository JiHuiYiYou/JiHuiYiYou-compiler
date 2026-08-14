@echo off
REM bootstrap.cmd -- One-command clone-and-use setup for the JHYY compiler.
REM
REM Builds compiler/build/bin/jhyy.exe from C source, then runs the regression
REM suite so you know everything is wired up. Safe to re-run.
REM
REM Requires:
REM   * MSYS2 (ucrt64) at C:\msys64\ -- installs GCC + binutils
REM     Download: https://www.msys2.org/
REM   * Python on PATH (for regress.py)

setlocal
cd /d "%~dp0"

set "GCC=C:\msys64\ucrt64\bin\gcc.exe"
set "SRC=compiler\src"
set "BIN=compiler\build\bin\jhyy.exe"

echo === JHYY bootstrap ===

if not exist "%GCC%" (
    echo [ERROR] GCC not found at %GCC%
    echo Install MSYS2 from https://www.msys2.org/ then: pacman -S mingw-w64-ucrt-x86_64-gcc
    exit /b 1
)

echo [1/4] Building %BIN% ...
"%GCC%" -std=c11 -Wall -Wextra %SRC%\*.c -o %BIN% -I %SRC%
if errorlevel 1 (
    echo [ERROR] Build failed. See output above.
    exit /b 1
)

REM 刚构建的二进制就是新基准 — 不重锁 baseline 的话, regress 会因 sha 漂移
REM early-abort, 一个测试都不跑却报 "failures".
echo [2/4] Locking regress baseline to freshly built binary ...
python mcp-jhyy\jhyy_regress.py --save-baseline --binary %BIN%
if errorlevel 1 (
    echo [ERROR] Could not save baseline. Is Python on PATH?
    exit /b 1
)

echo [3/4] Running regression suite ...
python compiler\build\bin\regress.py
if errorlevel 1 (
    echo [WARN] Regression reported failures - see output above.
)

echo [4/4] Bootstrap complete.
echo.
echo Next steps:
echo   * In this terminal:    jhyy run compiler\tests\examples\hello.jhyy
echo   * In VSCode:          open hello.jhyy, press Ctrl+Shift+B to run
echo   * Run a task:         Ctrl+Shift+P, "Tasks: Run Task", "JHYY: Run"
echo   * Re-bootstrap:       bootstrap.cmd
