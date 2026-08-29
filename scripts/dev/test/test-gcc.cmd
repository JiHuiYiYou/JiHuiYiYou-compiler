@echo off
setlocal
set "REPO_ROOT=%~dp0..\.."
"C:\msys64\ucrt64\bin\gcc.exe" dungeon_game.s "%REPO_ROOT%\compiler\runtime\runtime.c" "%REPO_ROOT%\compiler\src0\jhyy_helpers.c" -o dungeon_game_test.exe -lm
echo Exit: %ERRORLEVEL%
