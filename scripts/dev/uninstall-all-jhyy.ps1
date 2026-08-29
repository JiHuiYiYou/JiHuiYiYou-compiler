# tmp/uninstall-all-jhyy.ps1 — uninstall all JHYY MSI products for clean-slate test
# DESTRUCTIVE: removes all MSI-registered JHYY installations. Run only for testing.
# NOT committed (tmp/ is gitignored).

$ErrorActionPreference = "Continue"

$products = Get-WmiObject Win32_Product | Where-Object { $_.Name -like '*JHYY*' }
Write-Host "Found $($products.Count) JHYY products to uninstall:"
$products | ForEach-Object { Write-Host "  $($_.IdentifyingNumber)  v$($_.Version)" }
Write-Host ""

$failed = @()
foreach ($p in $products) {
    Write-Host "Uninstalling $($p.IdentifyingNumber) ..." -NoNewline
    $proc = Start-Process msiexec -ArgumentList "/x $($p.IdentifyingNumber) /quiet /norestart" -Wait -PassThru -NoNewWindow
    $code = $proc.ExitCode
    if ($code -eq 0 -or $code -eq 3010) {
        Write-Host " exit=$code [OK]"
    } else {
        Write-Host " exit=$code [FAIL]"
        $failed += $p.IdentifyingNumber
    }
}

Write-Host ""
$remaining = @(Get-WmiObject Win32_Product | Where-Object { $_.Name -like '*JHYY*' })
Write-Host "Remaining JHYY products: $($remaining.Count)"
if ($remaining.Count -gt 0) {
    $remaining | ForEach-Object { Write-Host "  $($_.IdentifyingNumber)  v$($_.Version)" }
}

if ($failed.Count -gt 0) {
    Write-Host ""
    Write-Host "Failed uninstalls (retry individually): $($failed -join ', ')"
    exit 1
}
exit 0
