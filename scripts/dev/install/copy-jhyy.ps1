$repoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
$src = Join-Path $repoRoot "compiler\build\bin\jhyy.exe"
$dst = "C:\Program Files\JHYY\bin\jhyy.exe"

# Need admin (BUILTIN\Users ACL on "C:\Program Files\JHYY\bin" is ReadAndExecute only).
# Verify before destructive ops; PowerShell-ise fail-fast.
$id = [Security.Principal.WindowsIdentity]::GetCurrent()
$pr = New-Object Security.Principal.WindowsPrincipal($id)
if (-not $pr.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "FAIL: not elevated. Right-click PowerShell → Run as Administrator, then re-run."
    exit 1
}

if (-not (Test-Path $src)) { Write-Host "FAIL: source not found: $src"; exit 1 }
if (-not (Test-Path $dst)) { Write-Host "FAIL: target not found: $dst (is JHYY installed?)"; exit 1 }

$srcSha = (Get-FileHash $src -Algorithm SHA256).Hash
$dstSha = (Get-FileHash $dst -Algorithm SHA256).Hash
Write-Host "Source : $src"
Write-Host "  SHA : $srcSha"
Write-Host "Target : $dst"
Write-Host "  SHA : $dstSha  (current installed)"

if ($srcSha -eq $dstSha) {
    Write-Host "OK: already up-to-date (shas identical), nothing to do."
    exit 0
}

# Backup current installed binary (timestamp suffix so multiple backups coexist).
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
$bak = "$dst.v$dstSha.SubString(0,8).bak.$ts"
try {
    Copy-Item -Path $dst -Destination $bak -Force
    Write-Host "Backup : $bak"
} catch {
    Write-Host "FAIL: backup failed: $_"; exit 1
}

# Overwrite + verify.
try {
    Copy-Item -Path $src -Destination $dst -Force
    $newSha = (Get-FileHash $dst -Algorithm SHA256).Hash
    if ($newSha -ne $srcSha) {
        Write-Host "FAIL: post-copy SHA mismatch (expected $srcSha, got $newSha)"
        exit 1
    }
    Write-Host "OK: copied. New SHA: $newSha"
    Write-Host "Rollback: Copy-Item '$bak' '$dst' -Force"
} catch {
    Write-Host "FAIL: copy failed: $_"
    Write-Host "  Rollback: Copy-Item '$bak' '$dst' -Force"
    exit 1
}