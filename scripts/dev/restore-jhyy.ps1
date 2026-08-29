$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$src = Join-Path $repoRoot "compiler\build\bin\jhyy.exe"
$dst = "C:\Program Files\JHYY\bin\jhyy.exe"
try {
    Copy-Item -Path $src -Destination $dst -Force
    Write-Host "OK: restored to HEAD's jhyy.exe (SHA $((Get-FileHash $dst -Algorithm SHA256).Hash.Substring(0,16)))"
} catch {
    Write-Host "FAIL: $_"
}
