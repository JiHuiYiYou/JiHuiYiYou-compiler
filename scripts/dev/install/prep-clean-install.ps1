# scripts/dev/install/prep-clean-install.ps1 — kill stragglers + check env before v1.5.9 install
$ErrorActionPreference = "Continue"

Write-Host "=== Kill any running jhyy processes ==="
# 2026-10-30:原来还带 qbe —— QBE 已于 v2.16.0 从编译器移除(本轮还把 qbe/
# 目录删干净了)⇒ 那个进程名永远匹配不到,留着只会误导。
$procs = Get-Process -Name jhyy -ErrorAction SilentlyContinue
if ($procs) {
    $procs | Stop-Process -Force
    Write-Host "  Killed: $($procs.Name -join ', ')"
} else {
    Write-Host "  (none running)"
}

Write-Host ""
Write-Host "=== Existing JHYY MSIs ==="
$existing = Get-Package | Where-Object { $_.Name -like '*JHYY*' }
$existing | ForEach-Object { Write-Host "  $($_.Name) v$($_.Version)" }

Write-Host ""
Write-Host "=== INSTALLDIR state ==="
$dir = "C:\Program Files\JHYY"
if (Test-Path $dir) {
    $items = @(Get-ChildItem $dir -Recurse -Force -ErrorAction SilentlyContinue)
    Write-Host "  $dir exists, $($items.Count) entries"
} else {
    Write-Host "  (missing)"
}

Write-Host ""
Write-Host "=== RunOnce queue ==="
$ro = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce" -ErrorAction SilentlyContinue
$ro.PSObject.Properties | Where-Object { $_.Name -like '*jhyy*' -or $_.Value -like '*JHYY*' } | ForEach-Object {
    Write-Host "  $($_.Name) = $($_.Value)"
}
