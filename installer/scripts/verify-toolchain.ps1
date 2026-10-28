<#
  verify-toolchain.ps1 - v4.1.0 bundled toolchain gates

  Verifies that a collected toolchain (installer/build-artifacts/toolchain)
  is actually SELF-CONTAINED and RELOCATABLE. Everything here is a gate
  that used to have zero coverage: before v4.1.0 the shipped compiler
  simply borrowed the user's MSYS2, and nobody ever checked that a
  toolchain could be shipped at all.

  Gates:
    T1 RELOCATABLE  - copy the toolchain to a random path (with a space in
                       it, like "C:\Program Files\...") and compile + link +
                       RUN a hello world there. Proves there is no absolute
                       path dependency on the build machine.
    T2 HEADERS      - compile runtime.c + jhyy_helpers.c using ONLY the
                       staged toolchain. Proves the header closure is
                       complete (including .inl files!).
    T3 POISONED PATH- compile+link+run with a PATH that has MSYS2's POSIX
                       layer (/usr/bin, which provides an ld.exe that cannot
                       link PE objects) in FRONT. This is the exact shape of
                       a real user machine, and it is the gate that caught
                       the "collect2 picks up the wrong ld => link fails
                       with zero output" bug.
    T4 NO PATH      - same, with MSYS2 scrubbed out of PATH entirely.
    T5 WINDRES      - run windres from the staged toolchain (the compiler
                       runs it on EVERY link; if it is missing, every
                       compile fails, not just the ones that want an icon).
    T6 PREBUILT .o  - the shipped prebuilt .o must be byte-identical to a
                       fresh build with the staged toolchain.

  ASCII-only on purpose: Windows PowerShell 5.1 reads BOM-less .ps1 files
  using the ANSI code page, which mangles non-ASCII into parse errors.

  Usage:
    pwsh -NoProfile -ExecutionPolicy Bypass -File installer/scripts/verify-toolchain.ps1
#>
[CmdletBinding()]
param(
    [string]$ToolchainDir = "installer/build-artifacts/toolchain",
    [string]$OutDir       = "installer/build-artifacts"
)

$ErrorActionPreference = "Continue"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $repoRoot

$failures = New-Object System.Collections.ArrayList
function Say($msg) { Write-Host "[verify-toolchain] $msg" }
function Gate($name, $ok, $detail) {
    if ($ok) { Write-Host "  [PASS] $name" }
    else {
        Write-Host "  [FAIL] $name - $detail"
        [void]$failures.Add("$name - $detail")
    }
}
# Run a native command and capture output WITHOUT the Windows PowerShell
# 5.1 "NativeCommandError" trap (a native exe writing to stderr would
# otherwise terminate the script under $ErrorActionPreference = Stop).
function Invoke-Native($exe, $argList) {
    $old = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $out = & $exe @argList 2>&1 | ForEach-Object { $_.ToString() }
        return @{ code = $LASTEXITCODE; out = ($out -join "`n") }
    } finally { $ErrorActionPreference = $old }
}

$tc = (Resolve-Path $ToolchainDir).Path
$gcc = Join-Path $tc "bin\gcc.exe"
if (-not (Test-Path $gcc)) { throw "no staged toolchain at $tc (run collect-toolchain.ps1 first)" }
Say "toolchain: $tc"

# A hello.c whose exit code is distinctive: 42.
$work = Join-Path $env:TEMP ("jhyy-tc-verify-" + [Guid]::NewGuid().ToString("N").Substring(0,8))
New-Item -ItemType Directory -Force -Path $work | Out-Null
try {
    $hello = Join-Path $work "hello.c"
    @'
#include <stdio.h>
int main(void) { printf("jhyy-toolchain-ok\n"); return 42; }
'@ | Set-Content -Path $hello -Encoding ascii

    # ---------------------------------------------------------------- T1
    # Relocate to a path WITH A SPACE (the install dir is "C:\Program Files\JHYY").
    $relocated = Join-Path $work "Program Files JHYY toolchain"
    Copy-Item -Path $tc -Destination $relocated -Recurse -Force
    $rgcc = Join-Path $relocated "bin\gcc.exe"
    $helloExe = Join-Path $work "hello.exe"
    $r = Invoke-Native $rgcc @($hello, "-o", $helloExe)
    if ($r.code -ne 0) {
        Gate "T1 relocate + build" $false $r.out
    } else {
        $rr = Invoke-Native $helloExe @()
        $ok = ($rr.code -eq 42) -and ($rr.out -like "*jhyy-toolchain-ok*")
        Gate "T1 relocate + build + run" $ok ("exit=" + $rr.code + " out=" + $rr.out)
    }

    # ---------------------------------------------------------------- T2
    # The compiler's own C sources must compile with ONLY the staged
    # toolchain. The staged gcc's sysroot IS its include/ dir, so an
    # incomplete closure fails right here.
    $o1 = Join-Path $work "closure.o"
    $r = Invoke-Native $rgcc @("-std=c11", "-Wall", "-Wextra", "-g0", "-c", "compiler/runtime/runtime.c", "-o", $o1)
    Gate "T2 header closure (runtime.c)" ($r.code -eq 0) $r.out
    $o2 = Join-Path $work "closure2.o"
    $r = Invoke-Native $rgcc @("-std=c11", "-Wall", "-Wextra", "-g0", "-c", "compiler/src0/jhyy_helpers.c", "-o", $o2)
    Gate "T2 header closure (jhyy_helpers.c)" ($r.code -eq 0) $r.out

    # ---------------------------------------------------------------- T3
    # POISONED PATH. gcc spawns "as" and collect2 spawns "ld" BY BARE NAME
    # unless the toolchain's own gcc lib dir provides them. If those names
    # resolve through PATH, a user with MSYS2 installed gets whatever ld
    # their PATH has first - e.g. MSYS2's POSIX /usr/bin/ld.exe, which
    # cannot link PE objects => "ld returned 9 exit status" with ZERO
    # output. This gate reproduces exactly that.
    $savedPath = $env:PATH
    try {
        $poison = @()
        foreach ($p in @("C:\msys64\usr\bin", "C:\msys64\mingw64\bin")) {
            if (Test-Path $p) { $poison += $p }
        }
        if ($poison.Count -eq 0) { Say "  (no MSYS2 dirs found to poison PATH with - skipping T3)" }
        else {
            $env:PATH = ($poison -join ";") + ";" + $savedPath
            $outExe = Join-Path $work "poisoned.exe"
            $r = Invoke-Native $rgcc @($hello, "-o", $outExe)
            $buildOk = ($r.code -eq 0)
            $runCode = -1
            $runOut = ""
            if ($buildOk) {
                $rr = Invoke-Native $outExe @()
                $runCode = $rr.code; $runOut = $rr.out
            }
            Gate "T3 builds+runs with a poisoned PATH" ($buildOk -and $runCode -eq 42) `
                 ("build=" + $buildOk + " exit=" + $runCode + " out=" + $r.out)
        }
    } finally { $env:PATH = $savedPath }

    # ---------------------------------------------------------------- T4
    # And with MSYS2 removed from PATH completely.
    $savedPath = $env:PATH
    try {
        $env:PATH = (($env:PATH -split ';') |
                     Where-Object { $_ -and $_ -notmatch 'msys64' -and $_ -notmatch 'MSYS' }) -join ';'
        $npExe = Join-Path $work "nopath.exe"
        $r = Invoke-Native $rgcc @($hello, "-o", $npExe)
        $buildOk = ($r.code -eq 0)
        $runCode = -1
        if ($buildOk) {
            $rr = Invoke-Native $npExe @()
            $runCode = $rr.code
        }
        Gate "T4 builds+runs with MSYS2 scrubbed from PATH" ($buildOk -and $runCode -eq 42) `
             ("build=" + $buildOk + " exit=" + $runCode + " out=" + $r.out)
    } finally { $env:PATH = $savedPath }

    # ---------------------------------------------------------------- T5
    # windres runs on EVERY link; a missing windres makes every compile
    # fail (jh_gcc_invoke poisons the link line on purpose).
    $windres = Join-Path $relocated "bin\windres.exe"
    $icoSrc  = "installer/assets/icons/jhyy-icon.ico"
    if (-not (Test-Path $windres)) {
        Gate "T5 windres present" $false $windres
    } elseif (-not (Test-Path $icoSrc)) {
        Gate "T5 windres runs" $false "icon source missing: $icoSrc"
    } else {
        # Use the REAL icon the compiler embeds (a hand-made fake .ico is
        # not a valid ICO and windres rejects it - that would be a false
        # failure of the gate, not of the toolchain).
        $ico = Join-Path $work "t.ico"
        Copy-Item -Path $icoSrc -Destination $ico -Force
        # windres pre-processes the .rc through "gcc -E", where '\' is an
        # escape character => the .rc must use forward slashes.
        $icoFwd = $ico -replace '\\', '/'
        $rcFile = Join-Path $work "t.rc"
        ("1 ICON `"$icoFwd`"") | Set-Content -Path $rcFile -Encoding ascii
        $rcObj = Join-Path $work "t.o"
        $r = Invoke-Native $windres @("-i", $rcFile, "-O", "coff", "-o", $rcObj)
        Gate "T5 windres runs" (($r.code -eq 0) -and (Test-Path $rcObj)) $r.out
    }

    # ---------------------------------------------------------------- T6
    # The shipped prebuilt .o must be reproducible with the staged toolchain.
    $prebuilt = Join-Path $OutDir "bin\runtime.o"
    if (Test-Path $prebuilt) {
        $rebuilt = Join-Path $work "runtime-rebuilt.o"
        $r = Invoke-Native $rgcc @("-std=c11", "-Wall", "-Wextra", "-g0", "-c", "compiler/runtime/runtime.c", "-o", $rebuilt)
        $same = $false
        if ($r.code -eq 0 -and (Test-Path $rebuilt)) {
            $a = (Get-FileHash $prebuilt -Algorithm SHA256).Hash
            $b = (Get-FileHash $rebuilt  -Algorithm SHA256).Hash
            $same = ($a -eq $b)
        }
        Gate "T6 shipped .o is byte-identical to a fresh build" $same "staged-toolchain rebuild differs from the shipped .o"
    } else {
        Say "  (skip T6: no prebuilt runtime.o in $OutDir\bin)"
    }
} finally {
    Remove-Item -Recurse -Force $work -ErrorAction SilentlyContinue
}

if ($failures.Count -gt 0) {
    Write-Host ""
    Write-Host "[verify-toolchain] $($failures.Count) gate(s) FAILED:"
    foreach ($f in $failures) { Write-Host "  - $f" }
    exit 1
}
Write-Host "[verify-toolchain] all gates PASS"
exit 0
