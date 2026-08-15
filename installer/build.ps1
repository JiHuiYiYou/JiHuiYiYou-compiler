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
#   MSI package version MUST be major.minor.build.revision with each < 65536
#   and only digits. git describe output (e.g. v1.0.0-107-g73dd3cb) is invalid
#   for MSI — strip git suffix and use only major.minor.build.
#   Override via $env:JHY_VERSION = "1.5.2" for release builds.
if (-not $env:JHY_VERSION) {
    try {
        $rawVer = (& git describe --tags --always 2>$null) -as [string]
        if ($rawVer) {
            # Strip leading 'v' and git suffix: "v1.0.0-107-g73dd3cb" -> "1.0.0"
            $clean = $rawVer -replace '^v', '' -replace '-.*$', ''
            $parts = $clean.Split('.')
            if ($parts.Length -ge 3) {
                $env:JHY_VERSION = "$($parts[0]).$($parts[1]).$($parts[2])"
            } else {
                $env:JHY_VERSION = $clean
            }
        }
    } catch { }
}
if (-not $env:JHY_VERSION) { $env:JHY_VERSION = "1.5.2" }
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
        Write-Host "[build.ps1] === compiler MSI build (v1.5.2) ==="
        # 1. prepare bin/ payload (jhyy.exe + qbe.exe)
        $binDir = "installer/build-artifacts/bin"
        if (-not (Test-Path $binDir)) { New-Item -ItemType Directory -Path $binDir -Force | Out-Null }
        Copy-Item -Path "compiler/build/bin/jhyy.exe" -Destination "$binDir/jhyy.exe" -Force
        Copy-Item -Path "qbe/qbe.exe" -Destination "$binDir/qbe.exe" -Force
        # 2. build MSI via WiX 4/7
        #   bindpath bin/ -> jhyy.exe + qbe.exe
        #   bindpath common/ -> license.rtf
        #   loc Locale.zh-CN.wxl for Chinese UI strings
        #   -ext WixUtilExtension for WixUI_Minimal dialog set
        & wix build `
            installer/compiler/jhyy-compiler.wxs `
            -arch x64 `
            -b "bin=$binDir" `
            -b "common=installer/common" `
            -loc "installer/compiler/Locale.zh-CN.wxl" `
            -ext WixToolset.Util.wixext -ext WixToolset.UI.wixext `
            -d "JHY_VERSION=$($env:JHY_VERSION)" `
            -o "installer/build-artifacts/jhyy-compiler-$($env:JHY_VERSION).msi"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] compiler MSI build failed."
            exit 1
        }
        Write-Host "[OK] installer/build-artifacts/jhyy-compiler-$($env:JHY_VERSION).msi built"
        exit 0
    }
    "bundle" {
        Write-Host "[build.ps1] === Burn bundle build (v1.5.3) ==="
        # 1. ensure compiler MSI is built first (bundle chains it)
        $msiPath = "installer/build-artifacts/jhyy-compiler-$($env:JHY_VERSION).msi"
        if (-not (Test-Path $msiPath)) {
            Write-Host "[build.ps1] compiler MSI missing, building first..."
            & powershell -NoProfile -ExecutionPolicy Bypass -File $PSCommandPath compiler
            if ($LASTEXITCODE -ne 0) {
                Write-Host "[ERROR] compiler MSI build failed, aborting bundle build"
                exit 1
            }
        }
        # 2. build Burn bundle via wix build - outputs .exe
        #   -ext <Bal.dll> for WixStandardBootstrapperApplication
        #   bindpath msi/ -> jhyy-compiler-*.msi payload
        #   bindpath common/ -> license.rtf
        #   loc Bundle.zh-CN.wxl for Chinese UI strings
        #
        #   NOTE: `wix extension add -g WixToolset.Bal.wixext` ships the DLL
        #   named WixToolset.BootstrapperApplications.wixext.dll (NOT
        #   WixToolset.Bal.wixext.dll). The wix CLI extension-name lookup
        #   fails on Windows 7.0.0+b8977d6 (WIX0144). Workaround: reference
        #   the DLL by absolute path.
        $balDll = "$env:USERPROFILE\.wix\extensions\WixToolset.Bal.wixext\7.0.0\wixext7\WixToolset.BootstrapperApplications.wixext.dll"
        if (-not (Test-Path $balDll)) {
            Write-Host "[ERROR] Bal extension DLL not found at: $balDll"
            Write-Host "Run:  wix extension add -g WixToolset.Bal.wixext"
            exit 1
        }
        & wix build `
            installer/Bundle.wxs `
            -arch x64 `
            -b "msi=installer/build-artifacts" `
            -b "common=installer/common" `
            -loc "installer/Bundle.zh-CN.wxl" `
            -ext "$balDll" `
            -d "JHY_VERSION=$($env:JHY_VERSION)" `
            -d "JHY_COMPILER_MSI_PATH=installer\build-artifacts\jhyy-compiler-$($env:JHY_VERSION).msi" `
            -d "JHY_THEME_XML_PATH=installer\Theme.xml" `
            -d "JHY_LICENSE_RTF_PATH=installer\common\license.rtf" `
            -d "JHY_LOGO_BMP_PATH=installer\banner.bmp" `
            -o "installer/build-artifacts/jhyy-installer-$($env:JHY_VERSION).exe"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] bundle build failed."
            exit 1
        }
        Write-Host "[OK] installer/build-artifacts/jhyy-installer-$($env:JHY_VERSION).exe built"
        exit 0
    }
}

Write-Host "[ERROR] unreachable"
exit 1
