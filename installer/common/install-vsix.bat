@echo off
rem installer/common/install-vsix.bat : JHYY VSCode extension auto-installer
rem
rem Sprint v1.5.4: 由 MSI CustomAction 调用, deferred (after InstallFiles).
rem 检测 `code` (VSCode CLI) 在 PATH, 装了 → `code --install-extension` 装 .vsix.
rem 没装 → silent skip (返回 0, 不阻塞 MSI).
rem
rem Per-machine install: VSCode extension 装到所有用户. 需要 admin (HKLM scope).
rem
rem Args (passed via CustomActionData):
rem   /VSIX:"<path-to-vsix>"   必需, MSI 传给 deferred CA
rem
rem Exit codes:
rem   0  success / skip (VSCode not found / install failed gracefully)
rem   1  hard error (only if arg missing)

setlocal EnableDelayedExpansion

set "VSIX="
:parse_args
if "%~1"=="" goto args_done
if /i "%~1"=="/VSIX" (
    set "VSIX=%~2"
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
if not exist "%VSIX%" (
    echo [ERROR] VSIX not found at %VSIX%
    exit /b 1
)

rem detect VSCode CLI in PATH
where code >nul 2>&1
if errorlevel 1 (
    echo [INFO] VSCode CLI ('code') not detected in PATH, skipping extension install.
    echo [INFO] User can install manually: code --install-extension "%VSIX%"
    exit /b 0
)

rem install extension for all users (needs admin, MSI 已 elevate)
code --install-extension "%VSIX%" --force
if errorlevel 1 (
    echo [WARN] code --install-extension failed (exit %ERRORLEVEL%), continuing MSI install
    exit /b 0
)

echo [OK] VSCode extension installed: %VSIX%
exit /b 0