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
REM
REM IMPORTANT: this file must stay pure ASCII. cmd.exe under Chinese
REM Windows uses CP936 by default and cannot parse UTF-8 multi-byte
REM sequences in REM comments -- it tries to execute fragments of the
REM comment as commands and aborts. Run "python -c '...'" before
REM committing if any edit added non-ASCII characters.

setlocal enabledelayedexpansion
cd /d "%~dp0"

REM When double-clicked, cmd.exe starts with /c and the window closes
REM the moment the script exits -- user sees nothing. In that case,
REM pause before exit; from an already-open terminal, do not pause.
REM Use pure string-substitution (no `echo %cmdcmdline% | find`): the
REM pipe spawns a child cmd which dies on MSYS2 bash because it
REM inherits a Unix-style PATH.
REM CI / scripts running `cmd /c bootstrap.cmd` can pass --no-pause.
set "PAUSE_ON_EXIT="
set "CL=%cmdcmdline%"
if not "!CL:%~nx0=!"=="!CL!" set "PAUSE_ON_EXIT=1"
if /i "%~1"=="--no-pause" set "PAUSE_ON_EXIT="

set "GCC=C:\msys64\ucrt64\bin\gcc.exe"
set "SRC=compiler\src"
set "BIN=compiler\build\bin\jhyy.exe"

echo === JHYY bootstrap ===

if not exist "%GCC%" (
    echo [ERROR] GCC not found at %GCC%
    echo Install MSYS2 from https://www.msys2.org/ then: pacman -S mingw-w64-ucrt-x86_64-gcc
    goto :fail
)

echo [1/3] Building %BIN% ...
"%GCC%" -std=c11 -Wall -Wextra %SRC%\*.c -o %BIN% -I %SRC%
if errorlevel 1 (
    echo [ERROR] Build failed. See output above.
    goto :fail
)

echo [2/3] Running regression suite (~1 min) ...
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
if defined PAUSE_ON_EXIT pause
exit /b 0

:fail
if defined PAUSE_ON_EXIT pause
exit /b 1
