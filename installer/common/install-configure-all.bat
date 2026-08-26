@echo off
rem installer/common/install-configure-all.bat : JHYY master post-install orchestrator
rem
rem Sprint v1.5.7-rc1: MSI deferred ExeCommand CustomActions systematically fail
rem with error 1721 on this system (CreateProcess argv parser mis-tokenizes cmd.exe
rem /c chains with embedded escaped quotes). Debugged over 3 MSI builds.
rem
rem Pivot: HKLM RunOnce registry entry pointing at this .bat. Windows fires
rem RunOnce at next user logon in USER context (not SYSTEM), avoiding all
rem deferred-CA issues:
rem   - HKCU writes work (user has write access to own hive)
rem   - child process spawning works (CreateProcess in user context)
rem   - powershell.exe runs in user's interactive session
rem
rem Steps performed (orchestration only - no code --install-extension):
rem   1. install-configure-env.ps1: set MSYS2_PATH_TYPE=inherit (User scope env)
rem   2. install-configure-vscode.ps1: write VSCode defaultProfile + bash MSYS2 entry
rem
rem Step 3 (install-vsix.bat: install jhyy-lang + Code Runner extensions) is
rem INTENTIONALLY SKIPPED from this orchestrator. `code --install-extension`
rem requires VSCode to be installed and the user to have run `code` once to
rem register the CLI shim with PATH. Running it from a RunOnce context at
rem user logon (before the user has opened VSCode) frequently crashes or hangs
rem with exit 255. User can install the .vsix manually via:
rem     code --install-extension "C:\Program Files\JHYY\vscode-ext\jhyy-lang-1.5.7.vsix"
rem     code --install-extension formulahendry.code-runner
rem Documented in changelog-v1.5.0.md.
rem
rem Exit codes:
rem   0  all steps ran (individual failures don't block)
rem   1  .bat itself missing required files
rem
rem IMPORTANT: This file is ASCII-only. cmd.exe on Chinese Windows uses GBK
rem codepage; non-ASCII chars in .bat content get parsed as multi-byte sequences
rem and break command tokenization.

setlocal

set "BIN_DIR=%~dp0"
set "INSTALL_DIR=%BIN_DIR%..\"
if "%INSTALL_DIR:~-1%"=="\" set "INSTALL_DIR=%INSTALL_DIR:~0,-1%"

echo [install-configure-all] BIN_DIR=%BIN_DIR%
echo [install-configure-all] INSTALL_DIR=%INSTALL_DIR%

rem 1. MSYS2_PATH_TYPE=inherit (User scope env var)
if not exist "%BIN_DIR%install-configure-env.ps1" (
    echo [install-configure-all] ERROR: install-configure-env.ps1 missing
    exit /b 1
)
echo [install-configure-all] Setting MSYS2_PATH_TYPE=inherit (User scope)...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%BIN_DIR%install-configure-env.ps1"

rem 2. VSCode defaultProfile + bash (MSYS2) profile entry
if not exist "%BIN_DIR%install-configure-vscode.ps1" (
    echo [install-configure-all] ERROR: install-configure-vscode.ps1 missing
    exit /b 1
)
echo [install-configure-all] Configuring VSCode terminal profile...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%BIN_DIR%install-configure-vscode.ps1"

echo [install-configure-all] DONE.
exit /b 0