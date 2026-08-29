$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$src = Join-Path $repoRoot "compiler\build\bin\jhyy.exe"
$dst = "C:\Program Files\JHYY\bin\jhyy.exe"
try {
    Copy-Item -Path $src -Destination $dst -Force
    Write-Host "OK: copied $src -> $dst"
    Write-Host "New SHA: $((Get-FileHash $dst -Algorithm SHA256).Hash)"
} catch {
    Write-Host "FAIL: $_"
    exit 1
}
