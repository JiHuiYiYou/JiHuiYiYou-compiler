# tmp/uninstall-v2.ps1 — uninstall all JHYY via Get-Package (auto-elevation)
$ErrorActionPreference = "Continue"

$pkgs = Get-Package | Where-Object { $_.Name -like '*JHYY*' }
Write-Host "Found $($pkgs.Count) JHYY packages:"
$pkgs | ForEach-Object { Write-Host "  $($_.Name)  $($_.Version)" }
Write-Host ""

$failed = @()
foreach ($p in $pkgs) {
    Write-Host "Uninstalling $($p.Name) v$($p.Version) ..." -NoNewline
    try {
        $p | Uninstall-Package -ErrorAction Stop
        Write-Host " [OK]"
    } catch {
        Write-Host " [FAIL] $($_.Exception.Message)"
        $failed += $p.Name
    }
}

Write-Host ""
$remaining = @(Get-Package | Where-Object { $_.Name -like '*JHYY*' })
Write-Host "Remaining: $($remaining.Count)"
if ($remaining.Count -gt 0) {
    $remaining | ForEach-Object { Write-Host "  $($_.Name)  $($_.Version)" }
}

if ($failed.Count -gt 0) {
    Write-Host ""
    Write-Host "Failed: $($failed -join ', ')"
    exit 1
}
exit 0
