@echo off
rem test-gcc.cmd — 验证 MSYS2 + ucrt64 GCC toolchain 完整(gcc + jhyy 两件套)
rem
rem 2026-10-30 修:
rem   ① REPO_ROOT 原来上溯 2 级 ⇒ 落到 <repo>\scripts ⇒ 拼出的路径全错
rem   ② 编译目标 `dungeon_game.s` 根本不存在(那是 .jhyy 的编译产物,不是源)
rem      ⇒ 这个脚本从来跑不通
rem   ③ 原意是「gcc/qbe/jhyy 三件套」,但 QBE 已于 v2.16.0 从编译器移除
rem      (本轮还把 qbe/ 目录删干净了)⇒ 变「两件套」
rem
rem ⚠️ 故意**不**调 `jhyy --version` —— 那个命令从来就不存在(W-165)。
setlocal
set "REPO_ROOT=%~dp0..\..\.."
set "GCC=C:\msys64\ucrt64\bin\gcc.exe"
set "JHYY=%REPO_ROOT%\compiler\build\bin\jhyy.exe"

echo === gcc ===
if not exist "%GCC%" (
    echo MISSING: %GCC%
    exit /b 1
)
"%GCC%" --version | findstr /C:"gcc"
if errorlevel 1 (
    echo FAIL: gcc 跑不起来
    exit /b 1
)

echo === jhyy ===
if not exist "%JHYY%" (
    echo MISSING: %JHYY%
    exit /b 1
)
echo OK: %JHYY%

echo === OK: gcc + jhyy 两件套都在 ===
exit /b 0
