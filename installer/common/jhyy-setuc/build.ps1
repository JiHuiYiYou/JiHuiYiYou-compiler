# installer/common/jhyy-setuc/build.ps1
#
# Build the jhyy-setuc tool (UserChoice Hash writer).
# Output: installer/common/jhyy-setuc/bin/Release/net8.0-windows/jhyy-setuc.exe
#
# Used by:
#   - install-configure-all.bat (during MSI install)
#   - manual-fix-userchoice.ps1 (for existing installs)
#   - manual-fix-icon-cache.ps1 (v1.8.2 manual Path B fix)

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$csproj = Join-Path $ScriptDir "jhyy-setuc.csproj"

if (-not (Test-Path $csproj)) {
    Write-Error "csproj not found: $csproj"
    exit 1
}

Write-Host "[jhyy-setuc build] Building jhyy-setuc..."
dotnet build -c Release --nologo $csproj 2>&1 | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) {
    Write-Error "[jhyy-setuc build] dotnet build failed: $LASTEXITCODE"
    exit $LASTEXITCODE
}

$exe = Join-Path $ScriptDir "bin/Release/net8.0-windows/jhyy-setuc.exe"
if (-not (Test-Path $exe)) {
    Write-Error "[jhyy-setuc build] Output not found: $exe"
    exit 1
}
Write-Host "[jhyy-setuc build] OK: $exe"
exit 0