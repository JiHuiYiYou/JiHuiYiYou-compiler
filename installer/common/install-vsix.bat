@echo off
rem installer/common/install-vsix.bat : JHYY post-install VSCode wiring
rem
rem Sprint v1.5.4: 由 MSI CustomAction 调用, deferred (after InstallFiles).
rem 检测 `code` (VSCode CLI) 在 PATH, 装了 → `code --install-extension` 装 .vsix.
rem 没装 → silent skip (返回 0, 不阻塞 MSI).
rem
rem Sprint v1.5.6-patch2 (Code Runner integration):
rem   1. install jhyy-lang .vsix
rem   2. install Code Runner extension (formulahendry.code-runner)
rem   3. write code-runner.executorMap → jhyy run mapping to VSCode user
rem      settings.json via PowerShell script (configure-coderunner.ps1)
rem
rem Per-machine install: VSCode extension 装到所有用户. 需要 admin (HKLM scope).
rem
rem Args (passed via CustomActionData):
rem   /VSIX:"<path-to-vsix>"     必需, jhyy-lang .vsix 路径
rem   /CONFIGURE_PS1:"<path>"    必需, configure-coderunner.ps1 路径
rem   /JHY_DIR:"<install-dir>"   必需, JHYY 安装目录 (写入 settings.json 注释用)
rem
rem Exit codes:
rem   0  success / skip (VSCode not found / install failed gracefully)
rem   1  hard error (only if arg missing)

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
if "%CONFIGURE_PS1%"=="" (
    echo [WARN] /CONFIGURE_PS1 arg missing, skipping settings.json configuration
)
if "%JHY_DIR%"=="" (
    echo [WARN] /JHY_DIR arg missing, settings.json configuration will lack install dir hint
)

rem detect VSCode CLI in PATH (used by all 3 steps below)
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

rem === Step 2: install Code Runner extension ===
if "%CODE_FOUND%"=="1" (
    code --install-extension formulahendry.code-runner --force
    if errorlevel 1 (
        echo [WARN] code --install-extension formulahendry.code-runner failed (exit %ERRORLEVEL%), continuing
    ) else (
        echo [OK] Code Runner extension installed: formulahendry.code-runner
    )
) else (
    echo [INFO] VSCode CLI ('code') not detected in PATH, skipping Code Runner install.
    echo [INFO] User can install manually: code --install-extension formulahendry.code-runner
)

rem === Step 3: write code-runner.executorMap to VSCode user settings.json ===
if "%CONFIGURE_PS1%"=="" goto :settings_done
if not exist "%CONFIGURE_PS1%" (
    echo [WARN] configure-coderunner.ps1 not found at %CONFIGURE_PS1%, skipping settings.json config
    goto :settings_done
)
rem PowerShell 5.1 ships with Windows 10+. Pass -JHY_DIR so settings.json write
rem is associated with the install (informational only).
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%CONFIGURE_PS1%" -JHY_DIR "%JHY_DIR%"
if errorlevel 1 (
    echo [WARN] configure-coderunner.ps1 failed (exit %ERRORLEVEL%), continuing MSI install
) else (
    echo [OK] VSCode settings.json configured (code-runner.executorMap)
)

:settings_done
exit /b 0
