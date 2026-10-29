@echo off
REM ===========================================================================
REM  jhyy-bash.cmd - open a bash shell with jhyy on the PATH.
REM
REM  Why this exists:
REM    VSCode's built-in "bash (MSYS2)" terminal profile has a HARD-CODED path
REM    (C:\msys64\usr\bin\bash.exe) and does not fall back to another bash -
REM    so a user with MSYS2 somewhere else gets "the terminal profile is not
REM    available". This launcher finds a bash itself (MSYS2 -> Git for
REM    Windows -> PATH) and starts it with JHYY\bin on the PATH.
REM
REM  It also sets MSYS2_PATH_TYPE=inherit, because an MSYS2 bash in minimal
REM  PATH mode ignores the Windows PATH - and the MSI just added
REM  C:\Program Files\JHYY\bin there (that is where jhyy.exe lives).
REM
REM  ASCII-only on purpose: this file runs under the system code page
REM  (GBK on a Chinese Windows), and non-ASCII bytes in a .cmd get mangled.
REM ===========================================================================
setlocal

set "JHYY_BIN=%~dp0"
REM MSYS2's minimal PATH mode ignores the Windows PATH -> force inherit
set "MSYS2_PATH_TYPE=inherit"
REM Put JHYY\bin first so `jhyy` resolves inside the shell
set "PATH=%JHYY_BIN%;%PATH%"

if exist "%MSYS2_ROOT%\usr\bin\bash.exe" (
    "%MSYS2_ROOT%\usr\bin\bash.exe" --login -i
    goto :done
)
if exist "C:\msys64\usr\bin\bash.exe" (
    "C:\msys64\usr\bin\bash.exe" --login -i
    goto :done
)
if exist "%ProgramFiles%\Git\bin\bash.exe" (
    "%ProgramFiles%\Git\bin\bash.exe" --login -i
    goto :done
)
if exist "%ProgramFiles(x86)%\Git\bin\bash.exe" (
    "%ProgramFiles(x86)%\Git\bin\bash.exe" --login -i
    goto :done
)
where bash.exe >nul 2>&1
if not errorlevel 1 (
    bash.exe --login -i
    goto :done
)

echo [jhyy-bash] No bash.exe found (looked at MSYS2_ROOT, C:\msys64, Git for Windows, PATH).
echo [jhyy-bash] Install MSYS2 from https://www.msys2.org/ or Git for Windows.
echo [jhyy-bash] jhyy.exe itself is already on the system PATH, so cmd/PowerShell work.
exit /b 1

:done
endlocal
