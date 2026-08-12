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

set "GCC=C:\msys64\ucrt64\bin\gcc.exe"
set "SRC=compiler\src"
set "BIN=compiler\build\bin\jhyy.exe"

echo === JHYY bootstrap ===

if not exist "%GCC%" (
    echo [ERROR] GCC not found at %GCC%
    echo Install MSYS2 from https://www.msys2.org/ then: pacman -S mingw-w64-ucrt-x86_64-gcc
    exit /b 1
)

echo [1/3] Building %BIN% ...
"%GCC%" -std=c11 -Wall -Wextra %SRC%\*.c -o %BIN% -I %SRC%
if errorlevel 1 (
    echo [ERROR] Build failed. See output above.
    exit /b 1
)

echo [2/3] Running regression suite ...
python compiler\build\bin\regress.py
if errorlevel 1 (
    echo [WARN] Regression reported failures - see output above.
)

echo [3/3] Bootstrap complete.
echo.
echo Next steps:
echo   * In this terminal:    jhyy run compiler\tests\examples\hello.jhyy
echo   * In VSCode:          open hello.jhyy, press Ctrl+Shift+B to run
echo   * Run a task:         Ctrl+Shift+P, "Tasks: Run Task", "JHYY: Run"
echo   * Re-bootstrap:       bootstrap.cmd
