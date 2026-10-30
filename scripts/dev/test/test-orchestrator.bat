@echo off
rem Simulate the post-v1.5.10 orchestrator's vsix step (code --install-extension).
rem
rem 2026-10-30 修:
rem   ① header 说「3 steps」但脚本只做第 3 步(它自己的 echo 就写着
rem      「Step 3 simulation only」)⇒ 改成如实描述
rem   ② BIN_DIR 上溯 2 级(落到 scripts\)而且**根本没被用到** ⇒ 删掉
rem
rem ⚠️ 真正的 3 步在 installer/common/install-configure-all.bat 里(v1.5.10 起
rem    vsix 安装已内联在那儿,不再走独立的 install-vsix.bat —— 那个脚本已删)。
setlocal EnableDelayedExpansion

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
