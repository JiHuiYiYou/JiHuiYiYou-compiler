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

# Helper: extract RC suffix from version string, leave $clean without suffix.
# Examples: "1.5.5-rc1" -> $clean="1.5.5", suffix="-rc1"
#           "1.5.5"     -> $clean="1.5.5", suffix=""
#           "1.5.5-rc10" -> $clean="1.5.5", suffix="-rc10"
#           "v1.5.5-rc1" -> $clean="1.5.5", suffix="-rc1" (caller strips 'v' first)
function _split_rc_suffix($verIn, [ref]$suffixOut) {
    if ($verIn -match '^(.+?)-([a-z]+\d+)$') {
        $suffixOut.Value = "-" + $matches[2]
        return $matches[1]
    }
    $suffixOut.Value = ""
    return $verIn
}

# 1. version detection
#   MSI package version MUST be major.minor.build.revision with each < 65536
#   and only digits. git describe output (e.g. v1.0.0-107-g73dd3cb) is invalid
#   for MSI — strip git suffix and use only major.minor.build.
#   RC tag (e.g. v1.5.5-rc1) has -rcN suffix — extract separately so MSI version
#   stays numeric ("1.5.5") while display name + filename keep "-rc1" suffix.
#   Override via $env:JHY_VERSION = "1.5.2" for release builds.
$JHY_VERSION_RC_SUFFIX = ""
if (-not $env:JHY_VERSION) {
    try {
        $rawVer = (& git describe --tags --always 2>$null) -as [string]
        if ($rawVer) {
            $clean = $rawVer -replace '^v', ''
            $clean = _split_rc_suffix $clean ([ref]$JHY_VERSION_RC_SUFFIX)
            # Strip git suffix: "1.5.5-107-g73dd3cb" -> "1.5.5"
            $clean = $clean -replace '-.*$', ''
            $parts = $clean.Split('.')
            if ($parts.Length -ge 3) {
                $env:JHY_VERSION = "$($parts[0]).$($parts[1]).$($parts[2])"
            } else {
                $env:JHY_VERSION = $clean
            }
        }
    } catch { }
} else {
    # Override path: $env:JHY_VERSION may already contain RC suffix
    # (e.g. release.yml sets JHY_VERSION=1.5.5-rc1 from ${{ env.VERSION }}).
    $verIn = $env:JHY_VERSION -replace '^v', ''
    $verIn = _split_rc_suffix $verIn ([ref]$JHY_VERSION_RC_SUFFIX)
    $parts = $verIn.Split('.')
    if ($parts.Length -ge 3) {
        $env:JHY_VERSION = "$($parts[0]).$($parts[1]).$($parts[2])"
    } else {
        $env:JHY_VERSION = $verIn
    }
}
if (-not $env:JHY_VERSION) { $env:JHY_VERSION = "1.5.2" }
# Display version includes RC suffix for filenames + display names.
# MSI ProductVersion (passed via -d JHY_VERSION) must stay numeric (no "-rc1").
$JHY_VERSION_DISPLAY = "$($env:JHY_VERSION)$JHY_VERSION_RC_SUFFIX"
Write-Host "[build.ps1] target=$Target version=$($env:JHY_VERSION) display=$JHY_VERSION_DISPLAY rc_suffix=$JHY_VERSION_RC_SUFFIX"

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
        Write-Host "[build.ps1] === compiler MSI build (v1.5.4) ==="
        # 1. prepare bin/ payload (jhyy.exe + qbe.exe)
        $binDir = "installer/build-artifacts/bin"
        if (-not (Test-Path $binDir)) { New-Item -ItemType Directory -Path $binDir -Force | Out-Null }
        Copy-Item -Path "compiler/build/bin/jhyy.exe" -Destination "$binDir/jhyy.exe" -Force
        # qbe.exe resolution (W-025): prefer local qbe/qbe.exe (vendored source
        # — always present post v1.5.5). PATH fallback retained for safety.
        $qbeLocal = "qbe/qbe.exe"
        $qbeOnPath = (Get-Command qbe.exe -ErrorAction SilentlyContinue)
        if (Test-Path $qbeLocal) {
            Copy-Item -Path $qbeLocal -Destination "$binDir/qbe.exe" -Force
            Write-Host "[OK] qbe.exe from local source ($qbeLocal)"
        } elseif ($qbeOnPath) {
            Copy-Item -Path $qbeOnPath.Source -Destination "$binDir/qbe.exe" -Force
            Write-Host "[OK] qbe.exe from PATH ($($qbeOnPath.Source))"
        } else {
            Write-Host "[ERROR] qbe.exe not found: run `cd qbe && make` to build from vendored source"
            exit 1
        }

        # 1a. v1.5.6 W-043: ship runtime.c + jhyy_helpers.c into bin\
        #   installer-layout jhyy.exe (jh_paths_init layout a) builds
        #   "<bindir>\runtime.c" + "<bindir>\jhyy_helpers.c" paths from
        #   sibling qbe.exe. Without these, gcc link fails because the
        #   cmdline lists them but the files are absent on disk. Regress
        #   uses source-tree layout (b) so this only manifests in fresh
        #   installs. See docs/internal/workarounds.md § W-043.
        #   v1.5.6 W-044: also ship runtime.h (runtime.c line 1 does
        #   #include "runtime.h", gcc resolves from runtime.c's dir).
        Copy-Item -Path "compiler/runtime/runtime.c"    -Destination "$binDir/runtime.c"       -Force
        Copy-Item -Path "compiler/runtime/runtime.h"    -Destination "$binDir/runtime.h"       -Force
        Copy-Item -Path "compiler/src0/jhyy_helpers.c" -Destination "$binDir/jhyy_helpers.c"  -Force

        # 1c. v1.5.8: recolored WiX default UI assets (replaces rev 2 navy bg).
        #   jhyy-banner.bmp   - 493x58 default WiX banner, red→mint + J logo
        #                       at disc position (replaces rev 2 navy+mint title).
        #   jhyy-welcome.bmp  - 493x312 default WiX welcome, red→mint + J logo
        #                       (96x96 mint box tight around 80x80 J logo at
        #                        upper-LEFT disc position).
        #   jhyy-icon.ico     - ARPPRODUCTICON + .jhyy FileAssoc DefaultIcon
        # Generated by installer/build-jhyy-icons.ps1 (icon.svg → BMP + ICO).
        # Files are read by WiX at build time only (embedded in MSI Binary
        # table); no <File> Component references them, so they are NOT installed.
        if (-not (Test-Path "installer/jhyy-icon.ico") -or -not (Test-Path "installer/jhyy-welcome.bmp")) {
            Write-Host "[build.ps1] regenerating installer UI assets from icon.svg..."
            & powershell -NoProfile -ExecutionPolicy Bypass -File "installer/build-jhyy-icons.ps1"
            if ($LASTEXITCODE -ne 0) {
                Write-Host "[ERROR] UI asset generation failed (run installer/build-jhyy-icons.ps1 manually)"
                exit 1
            }
        }
        Copy-Item -Path "installer/jhyy-icon.ico"    -Destination "$binDir/jhyy-icon.ico"    -Force
        Copy-Item -Path "installer/jhyy-banner.bmp"  -Destination "$binDir/jhyy-banner.bmp"  -Force
        Copy-Item -Path "installer/jhyy-welcome.bmp" -Destination "$binDir/jhyy-welcome.bmp" -Force

        # 1b. v1.5.4: package VSCode extension (.vsix) for MSI payload
        #   Skippable via SKIP_VSIX=1 (e.g. for quick MSI rebuild without vsix)
        #   Pass JHY_VERSION_DISPLAY (with -rcN suffix) so vsix filename
        #   matches the MSI/bundle (e.g. jhyy-lang-1.5.5-rc1.vsix). Without
        #   this, package.ps1 falls back to JHY_VERSION (numeric, e.g. 1.5.5)
        #   and the Copy-Item below fails to find the RC-tagged vsix.
        if (-not $env:SKIP_VSIX) {
            Write-Host "[build.ps1] packaging VSCode extension (.vsix)..."
            $savedDisplay = $env:JHY_VERSION_DISPLAY
            $env:JHY_VERSION_DISPLAY = $JHY_VERSION_DISPLAY
            & powershell -NoProfile -ExecutionPolicy Bypass -File "installer/vscode-ext/package.ps1"
            $rc = $LASTEXITCODE
            $env:JHY_VERSION_DISPLAY = $savedDisplay
            if ($rc -ne 0) {
                Write-Host "[ERROR] vsix packaging failed, aborting MSI build"
                exit 1
            }
        }

        # 2. prepare vscode-ext/ bindpath dir for MSI (holds .vsix)
        #   Reuse build-artifacts dir: package.ps1 already copied vsix there,
        #   but MSI bindpath should be a stable location so we re-point.
        #   NOTE: SKIP_VSIX=1 is NOT a valid skip for the MSI build — the
        #   VSCodeExtVSIX Component unconditionally references the .vsix file
        #   via KeyPath, so the file MUST exist even when the user wanted to
        #   skip vscode packaging. To truly skip vscode packaging, exclude
        #   the JHYYVSCodeExt ComponentGroupRef from the Feature (manual edit).
        #   Bug captured 2026-08-26 (v1.5.7-rc1): SKIP_VSIX flow used to abort
        #   here with ItemNotFound. Now still aborts but with clearer comment.
        $vscodeExtDir = "installer/build-artifacts/vscode-ext"
        if (-not (Test-Path $vscodeExtDir)) { New-Item -ItemType Directory -Path $vscodeExtDir -Force | Out-Null }
        if (-not (Test-Path "installer/build-artifacts/jhyy-lang-$JHY_VERSION_DISPLAY.vsix")) {
            Write-Host "[ERROR] .vsix missing — run build.ps1 without SKIP_VSIX=1, or exclude JHYYVSCodeExt from Feature"
            exit 1
        }
        Copy-Item -Path "installer/build-artifacts/jhyy-lang-$JHY_VERSION_DISPLAY.vsix" `
                  -Destination "$vscodeExtDir/jhyy-lang-$JHY_VERSION_DISPLAY.vsix" -Force

        # 3. build MSI via WiX 4/7
        #   bindpath bin/        -> jhyy.exe + qbe.exe + runtime.{c,h} + jhyy_helpers.c + UI assets
        #   bindpath common/     -> license.rtf + install-configure-all.bat + 2 .ps1 helpers
        #   bindpath vscode-ext/ -> jhyy-lang-X.Y.Z.vsix
        #   loc Locale.zh-CN.wxl for Chinese UI strings
        #   -ext WixUtilExtension for WixUI_Minimal dialog set
        #   (v1.5.10: install-vsix.bat + configure-coderunner.ps1 removed — see
        #   install-configure-all.bat inline `code --install-extension` step.)
        & wix build `
            installer/compiler/jhyy-compiler.wxs `
            -arch x64 `
            -b "bin=$binDir" `
            -b "common=installer/common" `
            -b "vscode-ext=$vscodeExtDir" `
            -loc "installer/compiler/Locale.zh-CN.wxl" `
            -ext WixToolset.Util.wixext -ext WixToolset.UI.wixext `
            -d "JHY_VERSION=$($env:JHY_VERSION)" `
            -d "JHY_VERSION_DISPLAY=$JHY_VERSION_DISPLAY" `
            -o "installer/build-artifacts/jhyy-compiler-$JHY_VERSION_DISPLAY.msi"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] compiler MSI build failed."
            exit 1
        }
        Write-Host "[OK] installer/build-artifacts/jhyy-compiler-$JHY_VERSION_DISPLAY.msi built"
        exit 0
    }
    "bundle" {
        Write-Host "[build.ps1] === Burn bundle build (v1.5.3, v1.8.3 patch) ==="
        # 1. ensure compiler MSI is built first (bundle chains it)
        $msiPath = "installer/build-artifacts/jhyy-compiler-$JHY_VERSION_DISPLAY.msi"
        if (-not (Test-Path $msiPath)) {
            Write-Host "[build.ps1] compiler MSI missing, building first..."
            # Pass the ORIGINAL JHY_VERSION (with RC suffix if any) to the sub-script
            # so it can recompute RC_SUFFIX + DISPLAY internally. Without this,
            # sub-script sees JHY_VERSION=1.5.5 (already stripped by parent) and
            # cannot reconstruct the -rc1 suffix for filenames.
            $savedJHY = $env:JHY_VERSION
            $env:JHY_VERSION = "$($env:JHY_VERSION)$JHY_VERSION_RC_SUFFIX"
            & powershell -NoProfile -ExecutionPolicy Bypass -File $PSCommandPath compiler
            $rc = $LASTEXITCODE
            $env:JHY_VERSION = $savedJHY
            if ($rc -ne 0) {
                Write-Host "[ERROR] compiler MSI build failed, aborting bundle build"
                exit 1
            }
        }
        # 1a. v1.8.3: ensure .NET 8 Desktop Runtime exe is downloaded for
        #     Bundle chain. Source: official MS dotnetcli mirror.
        #     Path: installer/build-artifacts/dotnet/dotnet-runtime-8.0.30-win-x64.exe
        #     Why 8.0.30: latest 8.0 LTS patch as of 2026-08-29 (verified via
        #     https://dotnetcli.azureedge.net/dotnet/Runtime/8.0/latest.version).
        #     If the file exists from a previous build, skip download (CI caching).
        $dotnet8Exe = "installer/build-artifacts/dotnet/dotnet-runtime-8.0.30-win-x64.exe"
        $dotnet8Dir = Split-Path -Parent $dotnet8Exe
        if (-not (Test-Path $dotnet8Exe)) {
            if (-not (Test-Path $dotnet8Dir)) {
                New-Item -ItemType Directory -Path $dotnet8Dir -Force | Out-Null
            }
            Write-Host "[build.ps1] downloading .NET 8 Desktop Runtime 8.0.30 (~28MB)..."
            try {
                Invoke-WebRequest -Uri "https://dotnetcli.azureedge.net/dotnet/Runtime/8.0.30/dotnet-runtime-8.0.30-win-x64.exe" `
                                  -OutFile $dotnet8Exe `
                                  -UseBasicParsing `
                                  -ErrorAction Stop
            } catch {
                Write-Host "[ERROR] .NET 8 runtime download failed: $($_.Exception.Message)"
                Write-Host "Manually download from https://dotnet.microsoft.com/download/dotnet/8.0 and place at: $dotnet8Exe"
                exit 1
            }
            if (-not (Test-Path $dotnet8Exe)) {
                Write-Host "[ERROR] .NET 8 runtime download returned no file"
                exit 1
            }
            Write-Host "[OK] .NET 8 runtime downloaded: $dotnet8Exe"
        } else {
            Write-Host "[OK] .NET 8 runtime already cached: $dotnet8Exe"
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
            -ext WixToolset.Util.wixext `
            -d "JHY_VERSION=$($env:JHY_VERSION)" `
            -d "JHY_COMPILER_MSI_PATH=installer\build-artifacts\jhyy-compiler-$JHY_VERSION_DISPLAY.msi" `
            -d "JHY_THEME_XML_PATH=installer\Theme.xml" `
            -d "JHY_LICENSE_RTF_PATH=installer\common\license.rtf" `
            -d "JHY_LOGO_BMP_PATH=installer\logo.png" `
            -d "JHY_THEME_WXL_PATH=installer\Bundle.zh-CN.wxl" `
            -d "JHY_DOTNET8_RUNTIME_EXE_PATH=$dotnet8Exe" `
            -o "installer/build-artifacts/jhyy-installer-$JHY_VERSION_DISPLAY.exe"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] bundle build failed."
            exit 1
        }
        Write-Host "[OK] installer/build-artifacts/jhyy-installer-$JHY_VERSION_DISPLAY.exe built"

        # v1.5.5: also generate SHA256.txt for the 3 release artifacts
        # (Burn bundle + MSI + VSCode ext). Called from CI as a separate step
        # too (release.yml), but doing it here means `JHY_VERSION=1.5.5
        # powershell -File installer/build.ps1 bundle` produces both .exe and
        # SHA256.txt in one go for local smoke testing.
        & powershell -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot/gen-sha256.ps1"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[WARN] SHA256 generation failed (build still succeeded)"
        }
        exit 0
    }
}

Write-Host "[ERROR] unreachable"
exit 1
