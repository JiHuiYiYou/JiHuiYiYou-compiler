@echo off
rem Simulate the post-v1.5.10 orchestrator: 3 steps incl. code --install-extension.
setlocal EnableDelayedExpansion

set "BIN_DIR=%~dp0..\..\installer\common"
set "INSTALL_DIR=C:\Program Files\JHYY"

echo === Step 3 simulation only ===
where code
echo code exit: %ERRORLEVEL%
if errorlevel 1 (
    echo SKIPPED: code not in PATH
) else (
    for %%F in ("%INSTALL_DIR%\vscode-ext\*.vsix") do (
        echo RUNNING: code --install-extension "%%F" --force
        code --install-extension "%%F" --force
        echo EXIT: !ERRORLEVEL!
    )
)
echo === DONE ===
