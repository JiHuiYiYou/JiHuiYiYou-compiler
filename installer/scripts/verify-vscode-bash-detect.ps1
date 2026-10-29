# verify-vscode-bash-detect.ps1 - gate for the VSCode terminal profile detection
#
# The installer writes a VSCode terminal profile pointing at a bash it
# detects. If that detection silently breaks (path changes, function edited
# wrongly, the profile ends up pointing at a bash that does not exist), the
# user gets "the terminal profile is not available" in VSCode - a SILENT
# failure with no error anywhere.
#
# So: extract the real Find-Bash function out of the install script and run
# it. Whatever it returns must be a file that actually exists.
#
# ASCII-only on purpose (Windows PowerShell 5.1 reads .ps1 as ANSI when
# there is no BOM - see the sibling scripts).
#
# Usage:
#   pwsh -NoProfile -ExecutionPolicy Bypass -File installer/scripts/verify-vscode-bash-detect.ps1

$ErrorActionPreference = "Continue"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $repoRoot

$scriptPath = "installer/scripts/common/install-configure-vscode.ps1"
$src = Get-Content -Path $scriptPath -Raw -Encoding UTF8

# The function starts with "function Find-Bash" and ends with a "}" that is
# alone on its line.
$start = $src.IndexOf("function Find-Bash")
if ($start -lt 0) {
    Write-Host "[FAIL] $scriptPath has no 'function Find-Bash' - the VSCode profile would never be written" -ForegroundColor Red
    exit 1
}
$end = $src.IndexOf("`n}", $start)
if ($end -lt 0) {
    Write-Host "[FAIL] could not find the end of Find-Bash in $scriptPath" -ForegroundColor Red
    exit 1
}
$fn = $src.Substring($start, $end - $start + 2)

try {
    Invoke-Expression $fn
} catch {
    Write-Host "[FAIL] Find-Bash does not parse: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

$bash = Find-Bash
if (-not $bash) {
    # No bash on this machine at all (a bare Windows box). The install
    # script is supposed to skip the profile in that case - so this is the
    # EXPECTED behaviour, not a failure.
    Write-Host "[PASS] no bash on this machine - install-configure-vscode.ps1 correctly skips the profile" -ForegroundColor Green
    exit 0
}

if (-not (Test-Path $bash)) {
    Write-Host "[FAIL] Find-Bash returned a path that does not exist: $bash" -ForegroundColor Red
    exit 1
}
if (-not ($bash -like "*bash.exe")) {
    Write-Host "[FAIL] Find-Bash returned something that is not bash.exe: $bash" -ForegroundColor Red
    exit 1
}

# The profile the install script writes must point at the SAME bash we found.
if ($src -notmatch [regex]::Escape('path = $bashExe')) {
    Write-Host "[FAIL] install-configure-vscode.ps1 does not use the detected path (`"path = `$bashExe`") - it may still be hardcoded" -ForegroundColor Red
    exit 1
}

Write-Host "[PASS] Find-Bash -> $bash (exists)" -ForegroundColor Green
exit 0
