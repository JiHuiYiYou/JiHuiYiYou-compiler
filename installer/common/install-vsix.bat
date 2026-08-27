@echo off
rem installer/common/install-vsix.bat : JHYY post-install VSCode wiring
rem
rem Sprint v1.5.4: invoked by MSI CustomAction (later via RunOnce orchestrator).
rem Detects `code` (VSCode CLI) in PATH, runs `code --install-extension` for
rem the .vsix. If VSCode not installed -> silent skip (returns 0, no abort).
rem
rem Sprint v1.5.9 (Native play button):
rem   The .vsix now bundles a Run JHYY File play button via contributed command
rem   (menus.editor/title/run + Terminal.sendText, ms-python.python pattern).
rem   Replaces former Code Runner + executorMap integration (v1.5.6-patch2).
rem   /CONFIGURE_PS1 and /JHY_DIR args still accepted for WiX compat but no
rem   longer invoked.
rem
rem Per-machine install: VSCode extension installed to all users. Needs admin
rem (HKLM scope) for `code --install-extension` to write system extensions dir.
rem
rem Args (passed via RunOnce / CustomActionData):
rem   /VSIX:"<path-to-vsix>"     required, jhyy-lang .vsix path
rem   /CONFIGURE_PS1:"<path>"    accepted for WiX compat; no longer invoked
rem   /JHY_DIR:"<install-dir>"   accepted for WiX compat; no longer used
rem
rem Exit codes:
rem   0  success / skip (VSCode not found / install failed gracefully)
rem   1  hard error (only if arg missing)
rem
rem IMPORTANT: This file is ASCII-only. cmd.exe on Chinese Windows uses GBK
rem codepage; non-ASCII chars in .bat content get parsed as multi-byte sequences
rem and break command tokenization.

setlocal EnableDelayedExpansion

set "VSIX="
set "CONFIGURE_PS1="
set "JHY_DIR="
:parse_args
if "%~1"=="" goto args_done
if /i "%~1"=="/VSIX" (
    set "VSIX=%~2"
    shift
    shift
    goto parse_args
)
if /i "%~1"=="/CONFIGURE_PS1" (
    set "CONFIGURE_PS1=%~2"
    shift
    shift
    goto parse_args
)
if /i "%~1"=="/JHY_DIR" (
    set "JHY_DIR=%~2"
    shift
    shift
    goto parse_args
)
shift
goto parse_args

:args_done
if "%VSIX%"=="" (
    echo [ERROR] /VSIX arg missing
    exit /b 1
)
rem /CONFIGURE_PS1 and /JHY_DIR accepted but unused since v1.5.9 (WiX compat)

rem detect VSCode CLI in PATH
where code >nul 2>&1
set "CODE_FOUND=0"
if not errorlevel 1 set "CODE_FOUND=1"

rem === Step 1: install jhyy-lang .vsix ===
if exist "%VSIX%" (
    if "%CODE_FOUND%"=="1" (
        code --install-extension "%VSIX%" --force
        if errorlevel 1 (
            echo [WARN] code --install-extension for %VSIX% failed (exit %ERRORLEVEL%), continuing
        ) else (
            echo [OK] VSCode extension installed: %VSIX%
        )
    ) else (
        echo [INFO] VSCode CLI ('code') not detected in PATH, skipping jhyy-lang extension install.
        echo [INFO] User can install manually: code --install-extension "%VSIX%"
    )
) else (
    echo [WARN] VSIX not found at %VSIX%, skipping jhyy-lang extension install
)

exit /b 0
