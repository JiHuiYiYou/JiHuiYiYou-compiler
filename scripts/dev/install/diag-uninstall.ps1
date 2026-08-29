# tmp/diag-uninstall.ps1 — diagnose 1603 failure + check INSTALLDIR state
$ErrorActionPreference = "Continue"

Write-Host "=== INSTALLDIR state ==="
$dir = "C:\Program Files\JHYY"
if (Test-Path $dir) {
    Get-ChildItem $dir -Recurse -Force | Select-Object FullName, Length | Format-Table -AutoSize
} else {
    Write-Host "  (does not exist)"
}

Write-Host ""
Write-Host "=== Sample verbose uninstall log (first GUID) ==="
$first = (Get-WmiObject Win32_Product | Where-Object { $_.Name -like '*JHYY*' } | Select-Object -First 1).IdentifyingNumber
$log = "$env:TEMP\jhyy-uninst.log"
Write-Host "  GUID: $first"
Write-Host "  Log:  $log"
Write-Host ""
& msiexec /x $first /l*v $log /quiet /norestart 2>&1 | Out-Null
$exit = $LASTEXITCODE
Write-Host "Exit: $exit"
Write-Host ""
Write-Host "=== Last 40 lines of log (look for error) ==="
if (Test-Path $log) {
    Get-Content $log -Tail 40
} else {
    Write-Host "  (no log written)"
}
