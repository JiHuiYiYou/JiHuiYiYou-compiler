# 2026-10-30 修:原来只上溯 **2 级** ⇒ 落到 <repo>/scripts ⇒ 拼出的源路径
#   scripts\dev\compiler\build\bin\jhyy.exe 根本不存在 ⇒ 这个脚本从来跑不通。
#   copy-jhyy.ps1 用的是 3 级(对的)⇒ 两边对齐。
$repoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
$src = Join-Path $repoRoot "compiler\build\bin\jhyy.exe"
$dst = "C:\Program Files\JHYY\bin\jhyy.exe"
try {
    Copy-Item -Path $src -Destination $dst -Force
    Write-Host "OK: restored to HEAD's jhyy.exe (SHA $((Get-FileHash $dst -Algorithm SHA256).Hash.Substring(0,16)))"
} catch {
    Write-Host "FAIL: $_"
}
