# installer/build.ps1 - JHYY installer build orchestrator (WiX 4/7)
#
# Sprint v1.5.1: minimal stub-only build (verify toolchain).
# Sprint v1.5.2: adds compiler/jhyy-compiler.wxs - real MSI.
# Sprint v1.5.3: adds Bundle.wxs - Burn bundle (.exe wrapper).
#
# Why PowerShell not cmd: WiX 4/7 official docs use PowerShell; modern Windows
# dev convention; easier to invoke from MSYS bash + GitHub Actions Windows runner
# (both handle ps1 cleanly via `powershell -File` or `pwsh -File`).
#
# Usage:
#   powershell -File installer\build.ps1            # build stub (default)
#   powershell -File installer\build.ps1 stub       # explicit stub
#   powershell -File installer\build.ps1 compiler   # build jhyy-compiler-*.msi (v1.5.2)
#   powershell -File installer\build.ps1 bundle     # build jhyy-installer-*.exe (v1.5.3)
#
# Env vars:
#   JHY_VERSION    installer version (default: git describe, fallback 1.5.1-dev)
#   SKIP_VSIX      1 to skip vscode-ext pack (v1.5.4+)
#
# Exit codes:
#   0  build OK
#   1  build failed
#   2  bad args

[CmdletBinding()]
param(
    [ValidateSet("stub", "compiler", "bundle")]
    [string]$Target = "stub"
)

$ErrorActionPreference = "Stop"

# 1. version detection
if (-not $env:JHY_VERSION) {
    try {
        $ver = (& git describe --tags --always 2>$null) -as [string]
        if ($ver) { $env:JHY_VERSION = $ver }
    } catch { }
}
if (-not $env:JHY_VERSION) { $env:JHY_VERSION = "1.5.1-dev" }
Write-Host "[build.ps1] target=$Target version=$($env:JHY_VERSION)"

# 2. verify wix CLI
$wixCmd = Get-Command wix -ErrorAction SilentlyContinue
if (-not $wixCmd) {
    Write-Host "[ERROR] wix CLI not found in PATH."
    Write-Host "Install via:  dotnet tool install --global wix"
    Write-Host "Then:         setx PATH `"$env:PATH;$env:USERPROFILE\.dotnet\tools`""
    exit 1
}
& wix --version | Out-Null
if ($LASTEXITCODE -ne 0) { exit 1 }

# 3. dispatch
switch ($Target) {
    "stub" {
        Write-Host "[build.ps1] === stub build (smoke test, v1.5.1) ==="
        & wix build installer/_stub/stub.wxs -d "JHY_VERSION=$($env:JHY_VERSION)" -o installer/_stub/stub.msi
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] stub build failed."
            exit 1
        }
        Write-Host "[OK] installer/_stub/stub.msi built"
        exit 0
    }
    "compiler" {
        Write-Host "[build.ps1] === compiler MSI build (v1.5.2, not yet implemented) ==="
        Write-Host "[TODO] v1.5.2: implement installer/compiler/jhyy-compiler.wxs"
        exit 1
    }
    "bundle" {
        Write-Host "[build.ps1] === Burn bundle build (v1.5.3, not yet implemented) ==="
        Write-Host "[TODO] v1.5.3: implement installer/Bundle.wxs"
        exit 1
    }
}

Write-Host "[ERROR] unreachable"
exit 1
