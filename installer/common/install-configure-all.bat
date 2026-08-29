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
rem Steps performed:
rem   1. install-configure-env.ps1: set MSYS2_PATH_TYPE=inherit (User scope env)
rem   2. install-configure-vscode.ps1: write VSCode defaultProfile + bash MSYS2 entry
rem   3. (v1.5.10) inline `code --install-extension <vsix>` if VSCode CLI in PATH
rem
rem Step 3 re-evaluates v1.5.7's "RunOnce `code` exit 255" concern: empirically
rem the issue was a parser bug in install-vsix.bat (dead code), NOT a RunOnce
rem context issue. `code.cmd` shim works fine in RunOnce context if VSCode has
rem been installed. `where code` detects missing CLI -> silent skip.
rem User can still install manually:
rem     code --install-extension "C:\Program Files\JHYY\vscode-ext\jhyy-lang-X.Y.Z.vsix" --force
rem
rem Exit codes:
rem   0  all steps ran (individual failures don't block)
rem   1  .bat itself missing required files
rem
rem IMPORTANT: This file is ASCII-only. cmd.exe on Chinese Windows uses GBK
rem codepage; non-ASCII chars in .bat content get parsed as multi-byte sequences
rem and break command tokenization.

setlocal EnableDelayedExpansion

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

rem 3. (v1.5.10) Auto-install jhyy-lang .vsix into VSCode
rem Skip if `code` CLI not in PATH (VSCode not installed yet) — non-fatal.
where code >nul 2>&1
if errorlevel 1 (
    echo [install-configure-all] VSCode CLI 'code' not in PATH, skipping jhyy-lang extension install.
    echo [install-configure-all] User can install manually after opening VSCode once:
    echo [install-configure-all]   code --install-extension "%INSTALL_DIR%\vscode-ext\jhyy-lang-*.vsix" --force
) else (
    for %%F in ("%INSTALL_DIR%\vscode-ext\*.vsix") do (
        echo [install-configure-all] code --install-extension "%%F" --force
        code --install-extension "%%F" --force
        if errorlevel 1 (
            echo [install-configure-all] WARN: code --install-extension for %%F failed (exit !ERRORLEVEL!), continuing
        ) else (
            echo [install-configure-all] OK: VSCode extension installed: %%F
        )
    )
)

rem 4. (v1.8.1 patch) Cleanup HKCU\Software\Classes\.jhyy shadow.
rem    MSYS2 / Git Bash registers HKCU\Software\Classes\.<ext> = "<name>_auto_file"
rem    whenever it sees a `chmod +x <ext>` invocation, which shadows the
rem    per-machine MSI-installed HKCR\.jhyy\(default) = "JHYY.SourceFile".
rem    Without this cleanup, Explorer still picks the MSYS2 auto-class file
rem    (no DefaultIcon) and falls back to the white-document icon.
rem    Idempotent: reg delete on an absent key returns errorlevel 1, which we ignore.
rem    For users wanting the icon NOW without logoff/logon: run from admin shell
rem    "reg delete \"HKCU\Software\Classes\.jhyy\" /f" + "ie4uinit.exe -show".
reg.exe delete "HKCU\Software\Classes\.jhyy" /f >nul 2>&1
if errorlevel 1 (
    echo [install-configure-all] HKCU shadow cleanup: no .jhyy shadow present (exit !ERRORLEVEL!), continuing
) else (
    echo [install-configure-all] OK: HKCU\Software\Classes\.jhyy shadow cleared
)

echo [install-configure-all] DONE.
exit /b 0