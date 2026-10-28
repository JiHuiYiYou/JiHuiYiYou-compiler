<#
  collect-toolchain.ps1 - v4.1.0 bundled toolchain collector

  Picks the subset of the local MSYS2 UCRT64 GCC toolchain that the JHYY
  compiler actually needs, and stages it as installer payload, so that a
  machine WITHOUT MSYS2 can still compile .jhyy programs.

  Design doc (Chinese): installer/toolchain/README.md

  Output (default: installer/build-artifacts/):
    toolchain/                     -> <INSTALLDIR>\toolchain\
      bin/                         gcc as ld ar dlltool windres strip nm objdump ranlib + runtime DLLs
      lib/                         crt2.o + CRT / win32 import libs
      lib/gcc/<target>/<ver>/      cc1 collect2 libgcc.a crt*.o + runtime DLLs + gcc's own headers
      include/                     header closure (deps(runtime.c) U deps(jhyy_helpers.c))
      LICENSES/                    per-package license texts (GPL redistribution duty)
      SOURCES.txt                  package / version / upstream / how to get the source
    toolchain-manifest.json        what was actually collected (+ sha256) - input for gen-toolchain-wxs.ps1
    bin/runtime.o                  prebuilt object (saves ~4.5s of C recompilation per link)
    bin/jhyy_helpers.o

  Hard constraints of this design:
    * The directory layout MUST mirror ucrt64. gcc derives cc1 / collect2 /
      as / ld from its own location; flattening the tree breaks it. The
      staged copy must stay relocatable (bin/gcc.exe must work from any
      directory on any drive).
    * Runtime DLLs are discovered AUTOMATICALLY by scanning the import
      tables of every shipped exe (objdump -p), minus the Windows system
      DLLs. Hand-written lists rot the moment MSYS2 changes.
      The DLLs are copied into BOTH bin/ and lib/gcc/<target>/<ver>/ -
      cc1.exe lives in the latter, and a DLL that is not next to its exe
      gets resolved from PATH, i.e. from the USER's MSYS2, i.e. an ABI
      mismatch and a very confusing crash.
    * The header closure is generated (gcc -M -E), never hand-picked.
    * A gcc version that does not match the pinned manifest is a HARD
      failure, not a warning: reproducible artifacts require it.

  NOTE: this file is intentionally ASCII-only. Windows PowerShell 5.1
  reads BOM-less .ps1 files using the ANSI code page (GBK on a Chinese
  Windows), which mangles non-ASCII characters into parse errors. pwsh
  (PowerShell 7) defaults to UTF-8 and would be fine, but the installer
  build must run everywhere. Keep this file ASCII; put prose in the .md.

  Usage:
    pwsh -NoProfile -ExecutionPolicy Bypass -File installer/scripts/collect-toolchain.ps1
    pwsh ... -MsysRoot C:\msys64 -OutDir installer/build-artifacts
#>
[CmdletBinding()]
param(
    [string]$MsysRoot = "",
    [string]$OutDir   = "installer/build-artifacts",
    [switch]$SkipObjectFiles,
    # Downgrade the gcc-version mismatch from a hard failure to a warning.
    # Used by CI, whose rolling runner image carries whatever MSYS2 is
    # current: the toolchain GATES (relocatable, header closure, poisoned
    # PATH) are version-independent and must run on every build, but the
    # PIN is only enforced where we actually ship (release.yml).
    [switch]$AllowVersionDrift
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $repoRoot

function Say($msg) { Write-Host "[collect-toolchain] $msg" }

# --- 0. manifest -----------------------------------------------------------
# Read as UTF-8 explicitly: Windows PowerShell 5.1's Get-Content defaults to
# the ANSI code page (GBK on a Chinese Windows), which mangles the manifest's
# non-ASCII notes into invalid JSON.
$manifestPath = "installer/toolchain/manifest.json"
if (-not (Test-Path $manifestPath)) { throw "manifest not found: $manifestPath" }
$mf = [System.IO.File]::ReadAllText((Resolve-Path $manifestPath).Path, [System.Text.Encoding]::UTF8) | ConvertFrom-Json

if (-not $MsysRoot) {
    if ($env:MSYS2_ROOT) { $MsysRoot = $env:MSYS2_ROOT }
    else { $MsysRoot = $mf.toolchain.default_msys2_root }
}
$ucrt       = Join-Path $MsysRoot "ucrt64"
$gccExe     = Join-Path $ucrt "bin\gcc.exe"
$objdumpExe = Join-Path $ucrt "bin\objdump.exe"
if (-not (Test-Path $gccExe))     { throw "gcc not found: $gccExe (install MSYS2 ucrt64, or pass -MsysRoot)" }
if (-not (Test-Path $objdumpExe)) { throw "objdump not found: $objdumpExe" }

# --- 1. version gate (hard failure) ----------------------------------------
$gccVer = (& $gccExe -dumpversion 2>$null | Select-Object -First 1).Trim()
if ($gccVer -ne $mf.toolchain.gcc_version) {
    $msg = ("gcc version mismatch: manifest pins {0}, this machine has {1} ({2})." -f $mf.toolchain.gcc_version, $gccVer, $gccExe)
    if ($AllowVersionDrift) {
        Say ("WARNING: " + $msg + " -- allowed by -AllowVersionDrift (CI only; release builds are strict).")
    } else {
        throw ($msg + "`n  Reproducible artifacts require both to agree - update" +
               " installer/toolchain/manifest.json and re-run.")
    }
}
Say "gcc $gccVer @ $ucrt"

$target = (& $gccExe -dumpmachine 2>$null | Select-Object -First 1).Trim()
if ($target -ne $mf.toolchain.target) {
    throw "target mismatch: manifest pins $($mf.toolchain.target), this gcc is $target"
}

# gcc's own version directory (lib/gcc/<target>/<ver>/) - ask gcc, never hardcode.
# NOTE: the argument MUST be quoted. PowerShell splits a bare
# "-print-file-name=libgcc.a" token at the '=' when handing it to a native
# exe, so gcc would receive "-print-file-name=libgcc" and answer "libgcc".
$libgccA = (& $gccExe '-print-file-name=libgcc.a' 2>$null | Select-Object -First 1).Trim()
if (-not $libgccA -or $libgccA -eq "libgcc.a") { throw "cannot locate libgcc.a via $gccExe" }
$gccVerDir = Split-Path (Split-Path $libgccA -Parent) -Leaf
$gccLibRel = "lib/gcc/$target/$gccVerDir"
Say "gcc lib dir: $gccLibRel"

# --- 2. clean output -------------------------------------------------------
$tcOut  = Join-Path $OutDir "toolchain"
$binOut = Join-Path $OutDir "bin"
if (Test-Path $tcOut) { Remove-Item -Recurse -Force $tcOut }
New-Item -ItemType Directory -Force -Path $tcOut  | Out-Null
New-Item -ItemType Directory -Force -Path $binOut | Out-Null

function Copy-TC($relPath, $srcRoot) {
    $src = Join-Path $srcRoot $relPath
    if (-not (Test-Path $src)) { throw "missing toolchain file: $src" }
    $dst = Join-Path $tcOut ($relPath -replace '/', '\')
    $dstDir = Split-Path $dst -Parent
    if (-not (Test-Path $dstDir)) { New-Item -ItemType Directory -Force -Path $dstDir | Out-Null }
    Copy-Item -Path $src -Destination $dst -Force
}

# --- 3. payload files ------------------------------------------------------
foreach ($f in $mf.files.bin)     { Copy-TC "bin/$f" $ucrt }
foreach ($f in $mf.files.gcc_lib) { Copy-TC "$gccLibRel/$f" $ucrt }
foreach ($f in $mf.files.crt_lib) { Copy-TC "lib/$f" $ucrt }
# Extra copies of bin/ tools INTO the gcc lib dir: gcc and collect2 look
# these up BY BARE NAME, and their own search paths do not contain bin/ in
# the MSYS2 layout - so without these copies they resolve through PATH and
# can pick up a foreign ld (=> link fails with zero output).
foreach ($f in $mf.files.gcc_lib_from_bin) {
    $src = Join-Path $ucrt "bin\$f"
    if (-not (Test-Path $src)) { throw "missing toolchain file: $src" }
    $dst = Join-Path $tcOut "$gccLibRel\$f"
    Copy-Item -Path $src -Destination $dst -Force
}
Say "copied $($mf.files.bin.Count) bin + $($mf.files.gcc_lib.Count) gcc-lib + $($mf.files.crt_lib.Count) crt-lib + $($mf.files.gcc_lib_from_bin.Count) extra bin->gcc-lib"

# --- 4. runtime DLL closure (scan import tables) ---------------------------
# The closure must be TRANSITIVE. objdump -p shows only DIRECT imports, and
# a direct-only scan misses e.g. libintl-8.dll -> libiconv-2.dll: ship
# without libiconv and as/ld/windres fail to load on any machine that does
# not already have MSYS2 (which is exactly the machine we are shipping for).
# So: worklist over the exes AND over every DLL we pull in.
$system32 = Join-Path $env:SystemRoot "System32"
$work = New-Object System.Collections.ArrayList
[void]$work.Add((Join-Path $ucrt "bin\gcc.exe"))
foreach ($f in $mf.files.bin)     { [void]$work.Add((Join-Path $ucrt "bin\$f")) }
foreach ($f in $mf.files.gcc_lib) { [void]$work.Add((Join-Path $ucrt "$gccLibRel\$f")) }

$dllSet = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
while ($work.Count -gt 0) {
    $cur = $work[0]
    $work.RemoveAt(0)
    if (-not (Test-Path $cur)) { continue }
    $dump = & $objdumpExe -p $cur 2>$null
    foreach ($line in $dump) {
        if ($line -match '^\s*DLL Name:\s*(\S+)\s*$') {
            $dll = $Matches[1]
            if (Test-Path (Join-Path $system32 $dll)) { continue }   # ships with Windows
            # API set DLLs (api-ms-win-*, ext-ms-win-*) are virtual: there is
            # no such file in System32, the loader resolves them from the API
            # set schema. They ship with Windows, so they are not our problem.
            if ($dll -match '^(api-ms-win-|ext-ms-win-)') { continue }
            if ($dllSet.Add($dll)) {
                [void]$work.Add((Join-Path $ucrt "bin\$dll"))   # scan it too
            }
        }
    }
}
if ($dllSet.Count -eq 0) { throw "DLL closure came out empty - objdump output format changed?" }
Say "runtime DLL closure: $($dllSet.Count) dll(s) -> $([string]::Join(', ', @($dllSet | Sort-Object)))"

foreach ($dll in $dllSet) {
    $src = Join-Path $ucrt "bin\$dll"
    if (-not (Test-Path $src)) {
        throw "DLL '$dll' is required by the toolchain but missing from $ucrt\bin - refusing to ship a broken toolchain"
    }
    Copy-Item -Path $src -Destination (Join-Path $tcOut "bin\$dll") -Force
    Copy-Item -Path $src -Destination (Join-Path $tcOut "$gccLibRel\$dll") -Force
}

# --- 5. header closure -----------------------------------------------------
# jhyy emits ASSEMBLY, not C. The only C the linker ever compiles is the two
# fixed bridge files (runtime.c, jhyy_helpers.c). So the header requirement
# is exactly their dependency closure - NOT the whole ucrt64/include tree
# (135 MB). Measured: ~300 headers / 7.6 MB.
#
# Classification is by the ACTUAL path gcc resolved (gcc -M -E prints real
# paths), matched against an ORDERED list of roots. Order matters: the gcc
# include dirs live UNDER $ucrt, so the ucrt root would swallow them.
$gccLibAbs  = "$ucrt\lib\gcc\$target\$gccVerDir"
$gccIncAbs  = "$gccLibAbs\include"
$gccFixAbs  = "$gccLibAbs\include-fixed"
$sysIncAbs  = "$ucrt\include"
$roots = @(
    @{ root = "$gccIncAbs\"; cat = "gcc"      },
    @{ root = "$gccFixAbs\"; cat = "gccfixed" },
    @{ root = "$sysIncAbs\"; cat = "sys"      },
    @{ root = "$gccLibAbs\"; cat = "gccother" }
)

$closure = New-Object 'System.Collections.Generic.List[object]'
$seen    = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
foreach ($rel in $mf.headers.closure_inputs) {
    $abs = Join-Path $repoRoot ($rel -replace '/', '\')
    if (-not (Test-Path $abs)) { throw "closure input not found: $abs" }
    $raw  = (& $gccExe -M -E $abs 2>$null) -join "`n"
    $flat = $raw -replace "\\\r?\n", " "        # drop line-continuation backslashes
    foreach ($tok in ($flat -split '\s+')) {
        if (-not $tok) { continue }
        # Do NOT filter by extension here. The UCRT headers pull in .inl
        # files (stdio.h does `#include <swprintf.inl>`), and a "*.h only"
        # filter silently drops them - the toolchain then fails to compile
        # its own runtime.c with "swprintf.inl: No such file or directory".
        # Membership is decided by the root matching below, which keeps only
        # files that really live in the toolchain.
        $p = ($tok -replace '/', '\')
        foreach ($r in $roots) {
            if ($p.StartsWith($r.root, [StringComparison]::OrdinalIgnoreCase)) {
                $name = $p.Substring($r.root.Length)
                $key  = $r.cat + "|" + $name
                if ($seen.Add($key)) {
                    $closure.Add([pscustomobject]@{ cat = $r.cat; name = $name; src = $p })
                }
                break
            }
        }
    }
}
# gcc's own headers: explicit backstop against version drift
foreach ($h in $mf.headers.extra_gcc_internal) {
    $p = Join-Path $gccIncAbs $h
    if (Test-Path $p) {
        $key = "gcc|$h"
        if ($seen.Add($key)) { $closure.Add([pscustomobject]@{ cat = "gcc"; name = $h; src = $p }) }
    } else {
        Say "  (skip missing gcc-internal header $h)"
    }
}
Say "header closure: $($closure.Count) file(s)"

$destFor = @{
    "sys"      = "include"
    "gcc"      = "$gccLibRel\include"
    "gccfixed" = "$gccLibRel\include-fixed"
    "gccother" = $gccLibRel
}
foreach ($h in $closure) {
    if (-not (Test-Path $h.src)) { throw "closure header vanished: $($h.src)" }
    $dst = Join-Path $tcOut (Join-Path $destFor[$h.cat] $h.name)
    $dstDir = Split-Path $dst -Parent
    if (-not (Test-Path $dstDir)) { New-Item -ItemType Directory -Force -Path $dstDir | Out-Null }
    Copy-Item -Path $h.src -Destination $dst -Force
}

# --- 6. licenses + SOURCES.txt (GPL redistribution duty) -------------------
$licOut = Join-Path $tcOut "LICENSES"
New-Item -ItemType Directory -Force -Path $licOut | Out-Null
$licDirs = @(@($mf.licenses.required) + @($mf.licenses.optional))
foreach ($dir in $licDirs) {
    $src = Join-Path $ucrt "share\licenses\$dir"
    if (Test-Path $src) {
        $dst = Join-Path $licOut $dir
        New-Item -ItemType Directory -Force -Path $dst | Out-Null
        Copy-Item -Path (Join-Path $src "*") -Destination $dst -Force -Recurse
    } elseif (@($mf.licenses.required) -contains $dir) {
        throw "required license directory missing: $src (GPL redistribution duty - cannot skip)"
    } else {
        Say "  (no license dir for $dir - optional)"
    }
}
$srcLines = New-Object 'System.Collections.Generic.List[string]'
$srcLines.Add("JHYY bundled toolchain - sources")
$srcLines.Add("================================")
$srcLines.Add("")
$srcLines.Add("The JHYY installer (v4.1.0+) ships a minimal, relocatable subset of the")
$srcLines.Add("MSYS2 UCRT64 GCC toolchain. The files under toolchain/ are redistributed")
$srcLines.Add("verbatim from the packages listed below. Each package's license text is")
$srcLines.Add("shipped under toolchain/LICENSES/ next to this file.")
$srcLines.Add("")
$srcLines.Add("MSYS2 packages (source of all binaries below):")
$srcLines.Add("  https://repo.msys2.org/   (source tarballs under /sources/)")
$srcLines.Add("")
foreach ($p in $mf.packages) {
    $srcLines.Add(("  {0} {1}" -f $p.name, $p.version))
    $srcLines.Add(("    license: {0}" -f $p.license))
    $srcLines.Add(("    source : https://repo.msys2.org/sources/{0}/" -f $p.name))
}
$srcLines.Add("")
$srcLines.Add("GCC itself: https://gcc.gnu.org/  (GPL-3.0-or-later WITH GCC Runtime")
$srcLines.Add("Library Exception 3.1 - see LICENSES/gcc-libs/RUNTIME.LIBRARY.EXCEPTION)")
$srcLines.Add("")
$srcLines.Add("To obtain the corresponding source code for any of the above, download the")
$srcLines.Add("package source tarball from the MSYS2 source repository URL given for it")
$srcLines.Add("(a .tar.zst under https://repo.msys2.org/sources/<package>/), or the")
$srcLines.Add("matching upstream release tarball for GCC.")
$srcLines | Set-Content -Path (Join-Path $tcOut "SOURCES.txt") -Encoding utf8

# --- 7. prebuilt objects (kills the 4.5s per-link C recompilation) ---------
# Must be built with the COLLECTED gcc: the .o and the gcc that links it
# have to be the same version / same ABI.
if (-not $SkipObjectFiles) {
    $tcGcc = Join-Path $tcOut "bin\gcc.exe"
    Say "building prebuilt objects with the collected gcc..."
    $objs = @(
        @{ src = "compiler/runtime/runtime.c";    out = "runtime.o" },
        @{ src = "compiler/src0/jhyy_helpers.c"; out = "jhyy_helpers.o" }
    )
    foreach ($o in $objs) {
        $srcAbs = Join-Path $repoRoot ($o.src -replace '/', '\')
        $outAbs = Join-Path $binOut $o.out
        & $tcGcc -std=c11 -Wall -Wextra -g0 -c $srcAbs -o $outAbs
        if ($LASTEXITCODE -ne 0) { throw "failed to build $($o.out) with the collected gcc" }
        if (-not (Test-Path $outAbs)) { throw "gcc reported success but $($o.out) is missing" }
    }
    Say "built runtime.o + jhyy_helpers.o"
}

# --- 8. output manifest (input for gen-toolchain-wxs.ps1) -------------------
# NOTE: compare against the ABSOLUTE toolchain root. Get-ChildItem returns
# absolute FullName; substringing with a relative root length chops the
# wrong number of characters and silently mangles every path.
$tcOutAbs = [System.IO.Path]::GetFullPath($tcOut)
$dirMap = @{}
Get-ChildItem -Path $tcOut -Recurse -File | ForEach-Object {
    $rel = $_.FullName.Substring($tcOutAbs.Length + 1) -replace '\\', '/'
    $dir = ""
    if ($rel.Contains('/')) { $dir = $rel.Substring(0, $rel.LastIndexOf('/')) }
    if (-not $dirMap.ContainsKey($dir)) { $dirMap[$dir] = New-Object System.Collections.ArrayList }
    [void]$dirMap[$dir].Add([pscustomobject]@{
        name   = $_.Name
        size   = $_.Length
        sha256 = (Get-FileHash -Path $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    })
}
$dirs = @()
foreach ($k in ($dirMap.Keys | Sort-Object)) {
    $files = @($dirMap[$k] | Sort-Object { $_.name.ToLowerInvariant() })
    $dirs += [pscustomobject]@{ path = $k; files = $files }
}
$allFiles = Get-ChildItem -Path $tcOut -Recurse -File
$outManifest = [pscustomobject]@{
    schema          = 1
    gcc_version     = $gccVer
    target          = $target
    gcc_version_dir = $gccVerDir
    total_bytes     = ($allFiles | Measure-Object -Property Length -Sum).Sum
    dir_count       = $dirs.Count
    file_count      = $allFiles.Count
    dirs            = $dirs
}
$outManifestPath = Join-Path $OutDir "toolchain-manifest.json"
$outManifest | ConvertTo-Json -Depth 6 | Set-Content -Path $outManifestPath -Encoding utf8

$mb = [math]::Round($outManifest.total_bytes / 1MB, 1)
Say ("done: {0} files / {1} dirs / {2} MB raw" -f $outManifest.file_count, $outManifest.dir_count, $mb)
Say "manifest: $outManifestPath"
