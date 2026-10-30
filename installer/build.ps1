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
#   JHY_VERSION    installer version (default: git describe, fallback 1.8.3-dev)
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
#
# v4.1.0 fix: the RC-suffix regex is tightened from ([a-z]+\d+) to (rc\d+).
#   Why: `git describe --tags` output looks like "v4.0.19-9-gee35744", and
#   the old pattern matched the trailing GIT HASH ("gee" + "35744") as an
#   RC suffix => clean="4.0.19-9", suffix="-gee35744"
#   => JHY_VERSION_DISPLAY became "4.0.19-gee35744"
#   => the .vsix / .msi / installer.exe FILE NAMES all carried that fake
#   suffix. Nobody noticed because release.yml passes JHY_VERSION explicitly
#   from the tag; only LOCAL builds (the git-describe branch) hit it.
#   Now only a real "-rcN" counts as an RC suffix.
function _split_rc_suffix($verIn, [ref]$suffixOut) {
    if ($verIn -match '^(.+?)-(rc\d+)$') {
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
#   Override via $env:JHY_VERSION = "1.8.3" for release builds.
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
if (-not $env:JHY_VERSION) { $env:JHY_VERSION = "1.8.3" }
# Display version includes RC suffix for filenames + display names.
# MSI ProductVersion (passed via -d JHY_VERSION) must stay numeric (no "-rc1").
$JHY_VERSION_DISPLAY = "$($env:JHY_VERSION)$JHY_VERSION_RC_SUFFIX"
Write-Host "[build.ps1] target=$Target version=$($env:JHY_VERSION) display=$JHY_VERSION_DISPLAY rc_suffix=$JHY_VERSION_RC_SUFFIX"

# Detect PowerShell host: prefer pwsh (7+) for `switch` block syntax that some
# Windows PowerShell 5.1 builds (e.g. GH Actions Windows-2022 5.1.20348) reject.
# Fall back to Windows PowerShell 5.1 if pwsh isn't installed (e.g. local dev
# box without PowerShell 7).
# Use if/else (NOT `?:` ternary — 5.1 doesn't support `?:`; pwsh 7 does).
if (Get-Command pwsh -ErrorAction SilentlyContinue) {
    $script:PsExe = 'pwsh'
} else {
    $script:PsExe = 'powershell'
}
Write-Host "[build.ps1] psHost=$script:PsExe"

# v1.8.3.3 fix (W-067): when running under GitHub Actions ($env:GITHUB_ENV
# is set + writable), export JHY_VERSION_DISPLAY so release.yml can read it
# instead of mirroring the strip-to-3 logic in two places (drift risk).
# Single source of truth = this script's `$JHY_VERSION_DISPLAY` assignment
# above (line ~87). Local runs without $env:GITHUB_ENV are unaffected.
if ($env:GITHUB_ENV -and (Test-Path -Path $env:GITHUB_ENV -IsValid)) {
    try {
        "JHY_VERSION_DISPLAY=$JHY_VERSION_DISPLAY" | Add-Content -Path $env:GITHUB_ENV -ErrorAction Stop
        Write-Host "[build.ps1] exported JHY_VERSION_DISPLAY=$JHY_VERSION_DISPLAY to GITHUB_ENV"
    } catch {
        Write-Host "[WARN] could not export JHY_VERSION_DISPLAY to GITHUB_ENV: $_"
    }
}

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
        & wix build installer/wix/_archive/stub.wxs -d "JHY_VERSION=$($env:JHY_VERSION)" -o installer/wix/_archive/stub.msi
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] stub build failed."
            exit 1
        }
        Write-Host "[OK] installer/wix/_archive/stub.msi built"
        exit 0
    }
    "compiler" {
        Write-Host "[build.ps1] === compiler MSI build (v1.5.4 + v4.0.0 QBE removed) ==="
        # 1. prepare bin/ payload (jhyy.exe; qbe.exe removed in v4.0.0)
        $binDir = "installer/build-artifacts/bin"
        if (-not (Test-Path $binDir)) { New-Item -ItemType Directory -Path $binDir -Force | Out-Null }
        Copy-Item -Path "compiler/build/bin/jhyy.exe" -Destination "$binDir/jhyy.exe" -Force

        # 1a. v1.5.6 W-043: ship runtime.c + jhyy_helpers.c into bin\
        #   installer-layout jhyy.exe (jh_paths_init layout a) builds
        #   "<bindir>\runtime.c" + "<bindir>\jhyy_helpers.c" paths from
        #   sibling bindpath layout. Without these, gcc link fails because the
        #   cmdline lists them but the files are absent on disk. Regress
        #   uses source-tree layout (b) so this only manifests in fresh
        #   installs. See docs/workarounds.md § W-043.
        #   v1.5.6 W-044: also ship runtime.h (runtime.c line 1 does
        #   #include "runtime.h", gcc resolves from runtime.c's dir).
        Copy-Item -Path "compiler/runtime/runtime.c"    -Destination "$binDir/runtime.c"       -Force
        Copy-Item -Path "compiler/runtime/runtime.h"    -Destination "$binDir/runtime.h"       -Force
        Copy-Item -Path "compiler/src0/jhyy_helpers.c" -Destination "$binDir/jhyy_helpers.c"  -Force

        # 1b. v4.0.16 (W-103): ship the std lib modules into bin\std\.
        #   `import <mod>;` falls back to <bindir>\std\ when the module isn't
        #   next to the main file (jh_path_stdlib → jh_paths_init layout a).
        #   Without this, an installed jhyy.exe can't import ANY std module
        #   (source-tree layout (b) finds <root>\compiler\src0\std\ instead).
        $stdDir = "$binDir/std"
        if (-not (Test-Path $stdDir)) { New-Item -ItemType Directory -Path $stdDir -Force | Out-Null }
        Copy-Item -Path "compiler/src0/std/*.jhyy" -Destination "$stdDir/" -Force

        # 1c. v1.5.8: recolored WiX default UI assets (replaces rev 2 navy bg).
        #   jhyy-banner.bmp   - 493x58 default WiX banner, red→mint + J logo
        #                       at disc position (replaces rev 2 navy+mint title).
        #   jhyy-welcome.bmp  - 493x312 default WiX welcome, red→mint + J logo
        #                       (96x96 mint box tight around 80x80 J logo at
        #                        upper-LEFT disc position).
        #   jhyy-icon.ico     - ARPPRODUCTICON + .jhyy FileAssoc DefaultIcon
        # Generated by installer/scripts/build-jhyy-icons.ps1 (icon.svg → BMP + ICO).
        # Files are read by WiX at build time only (embedded in MSI Binary
        # table); no <File> Component references them, so they are NOT installed.
        if (-not (Test-Path "installer/assets/icons/jhyy-icon.ico") -or -not (Test-Path "installer/assets/bitmaps/jhyy-welcome.bmp")) {
            Write-Host "[build.ps1] regenerating installer UI assets from icon.svg..."
            & $script:PsExe -NoProfile -ExecutionPolicy Bypass -File "installer/scripts/build-jhyy-icons.ps1"
            if ($LASTEXITCODE -ne 0) {
                Write-Host "[ERROR] UI asset generation failed (run installer/scripts/build-jhyy-icons.ps1 manually)"
                exit 1
            }
        }
        Copy-Item -Path "installer/assets/icons/jhyy-icon.ico"    -Destination "$binDir/jhyy-icon.ico"    -Force
        Copy-Item -Path "installer/assets/bitmaps/jhyy-banner.bmp"  -Destination "$binDir/jhyy-banner.bmp"  -Force
        Copy-Item -Path "installer/assets/bitmaps/jhyy-welcome.bmp" -Destination "$binDir/jhyy-welcome.bmp" -Force

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
            & $script:PsExe -NoProfile -ExecutionPolicy Bypass -File "installer/vscode-ext/package.ps1"
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

        # 2a. v1.8.3.1+: build jhyy-setuc.exe (UserChoice Hash writer, .NET 8).
        #   WiX .wxs ships 4 files from installer/common/jhyy-setuc/bin/Release/net8.0-windows/
        #   (jhyy-setuc.exe + .dll + .deps.json + .runtimeconfig.json — .NET 8 apphost model).
        #   bin/ + obj/ are gitignored, so fresh CI checkout has nothing — must build here
        #   before WiX compile (otherwise WIX0103 "Cannot find File ..." errors at line 496+).
        #   Re-run is idempotent: dotnet build skips when up-to-date. No SKIP flag — jhyy-setuc
        #   is required by the deferred CustomAction (JHYYSetUCForAllUsers).
        Write-Host "[build.ps1] building jhyy-setuc.exe (.NET 8 UserChoice writer)..."
        & $script:PsExe -NoProfile -ExecutionPolicy Bypass -File "installer/common/jhyy-setuc/build.ps1"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] jhyy-setuc build failed, aborting MSI build"
            exit 1
        }
        $setucBin = "installer/common/jhyy-setuc/bin/Release/net8.0-windows"
        foreach ($f in @("jhyy-setuc.exe", "jhyy-setuc.dll", "jhyy-setuc.deps.json", "jhyy-setuc.runtimeconfig.json")) {
            if (-not (Test-Path "$setucBin/$f")) {
                Write-Host "[ERROR] jhyy-setuc build did not produce $f (expected at $setucBin)"
                exit 1
            }
        }

        # 2b. v4.1.0: collect the bundled toolchain (gcc + binutils + CRT +
        #   header closure) and generate its WiX fragment.
        #
        #   This is what removes the "you must install MSYS2 first" gate:
        #   the MSI now ships a minimal native ucrt64 toolchain under
        #   <INSTALLDIR>\toolchain\, so a bare Windows machine can compile
        #   .jhyy programs.
        #
        #   Two scripts:
        #     collect-toolchain.ps1 - copies the pinned file set out of the
        #       local MSYS2, computes the runtime-DLL closure and the C
        #       header closure, and pre-compiles runtime.o / jhyy_helpers.o
        #       WITH THE COLLECTED gcc (so the .o matches the bundled ABI).
        #     gen-toolchain-wxs.ps1 - turns the collected manifest into a
        #       WiX <Fragment> (378 files, one Component per directory).
        #
        #   The fragment is passed to `wix build` as a SECOND source file
        #   (Package in the main .wxs, Fragment in the generated one).
        #   If a WiX version refuses multi-source builds, the fallback is to
        #   append the fragment to a copy of the main .wxs - <Fragment> is a
        #   top-level element, so appending is valid.
        #
        #   NOTE: keep these comments ASCII. This file has no BOM and the
        #   repo runs it under pwsh (UTF-8); Windows PowerShell 5.1 would
        #   read it as ANSI and mangle non-ASCII into parse errors.
        Write-Host "[build.ps1] collecting bundled toolchain (v4.1.0)..."
        $collectArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "installer/scripts/collect-toolchain.ps1")
        if ($env:JHY_MSYS2_ROOT) {
            # The GitHub runner image ships an OLD MSYS2 at C:\mingw64 (gcc
            # 15.2.0) that sits FIRST on the Windows PATH, while
            # setup-msys2 installs a FRESH one (gcc 16.2.0) elsewhere. So the
            # PATH-based discovery inside a plain pwsh step picks the stale
            # toolchain - and the version pin then rejects it. The MSYS2-shell
            # steps know the right root (`cygpath -w /`); they export it as
            # JHY_MSYS2_ROOT, and we pass it down explicitly.
            $collectArgs += @("-MsysRoot", $env:JHY_MSYS2_ROOT)
            Write-Host "[build.ps1] using MSYS2 root: $env:JHY_MSYS2_ROOT"
        }
        if ($env:JHY_ALLOW_TOOLCHAIN_DRIFT) {
            # Local dev escape hatch: the pinned gcc version in
            # installer/toolchain/manifest.json is the RELEASE gate (it must
            # match the CI/release machine). A developer whose local MSYS2
            # differs can build with a warning instead of a hard failure.
            # The shipped SOURCES.txt still reports the ACTUAL package
            # versions, so the provenance stays truthful.
            $collectArgs += "-AllowVersionDrift"
            Write-Host "[build.ps1] JHY_ALLOW_TOOLCHAIN_DRIFT is set -> local toolchain version mismatch is a WARNING, not an error"
        }
        & $script:PsExe @collectArgs
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] toolchain collection failed, aborting MSI build"
            exit 1
        }
        Write-Host "[build.ps1] generating toolchain WiX fragment..."
        & $script:PsExe -NoProfile -ExecutionPolicy Bypass -File "installer/scripts/gen-toolchain-wxs.ps1"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] toolchain wxs generation failed, aborting MSI build"
            exit 1
        }
        $toolchainWxs = "installer/build-artifacts/wix/jhyy-toolchain.generated.wxs"
        $toolchainDir = "installer/build-artifacts/toolchain"
        if (-not (Test-Path $toolchainWxs))  { Write-Host "[ERROR] missing $toolchainWxs"; exit 1 }
        if (-not (Test-Path $toolchainDir))  { Write-Host "[ERROR] missing $toolchainDir"; exit 1 }
        foreach ($o in @("runtime.o", "jhyy_helpers.o")) {
            if (-not (Test-Path "$binDir/$o")) { Write-Host "[ERROR] missing prebuilt $o in $binDir"; exit 1 }
        }

        # 3. build MSI via WiX 4/7
        #   bindpath bin/        -> jhyy.exe (sole production binary, v4.0.0 QBE removed) + runtime.{c,h} + jhyy_helpers.c + UI assets
        #   bindpath common/     -> license.rtf + install-configure-all.bat + 2 .ps1 helpers
        #   bindpath vscode-ext/ -> jhyy-lang-X.Y.Z.vsix
        #   loc Locale.zh-CN.wxl for Chinese UI strings
        #   -ext WixUtilExtension for WixUI_Minimal dialog set
        #   (v1.5.10: install-vsix.bat + configure-coderunner.ps1 removed — see
        #   install-configure-all.bat inline `code --install-extension` step.)
        & wix build `
            installer/wix/compiler/jhyy-compiler.wxs `
            $toolchainWxs `
            -arch x64 `
            -b "bin=$binDir" `
            -b "common=installer/common" `
            -b "assets=installer/assets" `
            -b "scripts=installer/scripts" `
            -b "vscode-ext=$vscodeExtDir" `
            -b "toolchain=$toolchainDir" `
            -loc "installer/wix/compiler/Locale.zh-CN.wxl" `
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
        #
        # v4.1.2 (W-166): this used to be "build the MSI only if it is MISSING"
        # => a STALE MSI was silently reused. So after editing the compiler and
        # rebuilding jhyy.exe, `build.ps1 bundle` still chained the OLD
        # compiler into the bundle. Measured: after changing the help text in
        # main.jhyy and rebuilding jhyy.exe, the MSI sha256 was byte-identical
        # to the previous run (d32bb524...) => it still held the old binary.
        # (CI is unaffected: a fresh checkout has no MSI => always rebuilt.
        #  But EVERY local build hit this trap.)
        #
        # Fix: not just "does it exist" but "is any input newer than it" --
        # compiler binary / bridge C sources / WiX sources / UI assets / VSIX /
        # bundled toolchain. Any newer input => stale => rebuild.
        $msiPath = "installer/build-artifacts/jhyy-compiler-$JHY_VERSION_DISPLAY.msi"
        $msiNeedsBuild = $false
        $msiWhy = ""
        if (-not (Test-Path $msiPath)) {
            $msiNeedsBuild = $true
            $msiWhy = "MSI missing"
        } else {
            $msiTime = (Get-Item $msiPath).LastWriteTimeUtc
            # NOTE: do NOT use installer/build-artifacts/bin as an input -- it
            # holds the COPIES the MSI build puts there, so their timestamps are
            # always newer than the MSI => the MSI would look stale forever.
            $msiInputs = @(
                "compiler/build/bin/jhyy.exe",
                "compiler/src0/jhyy_helpers.c",
                "compiler/runtime/runtime.c"
            )
            foreach ($dir in @("installer/wix", "installer/assets",
                               "installer/build-artifacts/vscode-ext",
                               "installer/build-artifacts/toolchain")) {
                if (Test-Path $dir) {
                    $msiInputs += (Get-ChildItem $dir -Recurse -File -ErrorAction SilentlyContinue |
                                    ForEach-Object { $_.FullName })
                }
            }
            foreach ($f in $msiInputs) {
                if (Test-Path $f) {
                    if ((Get-Item $f).LastWriteTimeUtc -gt $msiTime) {
                        $msiNeedsBuild = $true
                        $msiWhy = "an input is newer than the MSI: $f"
                        break
                    }
                }
            }
        }
        if ($msiNeedsBuild) {
            Write-Host "[build.ps1] compiler MSI needs a rebuild ($msiWhy) -- building first..."
            # Pass the ORIGINAL JHY_VERSION (with RC suffix if any) to the sub-script
            # so it can recompute RC_SUFFIX + DISPLAY internally. Without this,
            # sub-script sees JHY_VERSION=1.5.5 (already stripped by parent) and
            # cannot reconstruct the -rc1 suffix for filenames.
            $savedJHY = $env:JHY_VERSION
            $env:JHY_VERSION = "$($env:JHY_VERSION)$JHY_VERSION_RC_SUFFIX"
            & $script:PsExe -NoProfile -ExecutionPolicy Bypass -File $PSCommandPath compiler
            $rc = $LASTEXITCODE
            $env:JHY_VERSION = $savedJHY
            if ($rc -ne 0) {
                Write-Host "[ERROR] compiler MSI build failed, aborting bundle build"
                exit 1
            }
        } else {
            Write-Host "[build.ps1] compiler MSI is up to date, reusing it."
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
        #
        #   v4.1.0: 版本号**不再写死**。原来写的是 ...\Bal.wixext\7.0.0\wixext7\...
        #   ⇒ runner 上的 WiX 一升级(7.0.1 / 7.1.x / 8.x)路径就找不到
        #   ⇒ **release 构建在 Burn bundle 这步失败**(实测 2026-10-29:
        #   v4.0.22 的发布就死在这儿 —— MSI 都已经编好了,挂在最后一步)。
        #   改成**扫目录**:任何版本目录下的那个 DLL 都认(取最新的一个)。
        #
        #   ⚠️ 用户目录**不**只从 $env:USERPROFILE 取 —— 那个变量在某些 shell
        #   (MSYS2 / CI 的某些步骤)里是空的 ⇒ Join-Path 会直接报「参数 Path
        #   是空值」。用 .NET 的 GetFolderPath 兜底(Windows 上永远正确)。
        $userProfile = $env:USERPROFILE
        if (-not $userProfile) { $userProfile = [Environment]::GetFolderPath("UserProfile") }
        if (-not $userProfile -and $env:HOMEDRIVE -and $env:USERNAME) {
            $userProfile = Join-Path $env:HOMEDRIVE "Users\$env:USERNAME"
        }
        if (-not $userProfile) {
            Write-Host "[ERROR] cannot resolve the user profile directory (USERPROFILE / GetFolderPath both empty)"
            exit 1
        }
        $balRoot = Join-Path $userProfile ".wix\extensions\WixToolset.Bal.wixext"
        $balDll = $null
        if (Test-Path $balRoot) {
            $hit = Get-ChildItem -Path $balRoot -Recurse -Filter "WixToolset.BootstrapperApplications.wixext.dll" -ErrorAction SilentlyContinue |
                   Sort-Object FullName -Descending | Select-Object -First 1
            if ($hit) { $balDll = $hit.FullName }
        }
        if (-not $balDll) {
            Write-Host "[ERROR] Bal extension DLL not found under: $balRoot"
            Write-Host "Run:  wix extension add -g WixToolset.Bal.wixext"
            exit 1
        }
        Write-Host "[build.ps1] using Bal extension: $balDll"
        & wix build `
            installer/wix/Bundle.wxs `
            -arch x64 `
            -b "msi=installer/build-artifacts" `
            -b "common=installer/common" `
            -b "assets=installer/assets" `
            -loc "installer/wix/Bundle.zh-CN.wxl" `
            -ext "$balDll" `
            -ext WixToolset.Util.wixext `
            -d "JHY_VERSION=$($env:JHY_VERSION)" `
            -d "JHY_COMPILER_MSI_PATH=installer\build-artifacts\jhyy-compiler-$JHY_VERSION_DISPLAY.msi" `
            -d "JHY_THEME_XML_PATH=installer\wix\Theme.xml" `
            -d "JHY_LICENSE_RTF_PATH=installer\assets\license.rtf" `
            -d "JHY_LOGO_BMP_PATH=installer\assets\icons\jhyy-logo-128.png" `
            -d "JHY_THEME_WXL_PATH=installer\wix\Bundle.zh-CN.wxl" `
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
        & $script:PsExe -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot/scripts/gen-sha256.ps1"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[WARN] SHA256 generation failed (build still succeeded)"
        }
        exit 0
    }
}

Write-Host "[ERROR] unreachable"
exit 1
