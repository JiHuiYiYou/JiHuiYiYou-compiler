<#
  gen-toolchain-wxs.ps1 - v4.1.0 toolchain MSI fragment generator

  Turns installer/build-artifacts/toolchain-manifest.json (produced by
  collect-toolchain.ps1) into a WiX <Fragment> that adds the bundled
  toolchain to the compiler MSI.

  Why a generator instead of a hand-written .wxs: the toolchain is ~380
  files. Hand-maintaining that is not an option, and the file set changes
  whenever MSYS2 is updated.

  Why a separate source file instead of one big .wxs: `wix build` accepts
  multiple source files (Package in one, Fragment in the other) and merges
  them. If a WiX version ever refuses that, build.ps1 falls back to
  appending the fragment to a copy of the main .wxs - <Fragment> is a
  top-level element, so appending is valid.

  Deterministic GUIDs (important for upgrades):
    Component GUID = UUIDv5(namespace, "component:<dir>|<sorted file names>")
    so it is stable across rebuilds, but changes when the file set of that
    directory changes (which is exactly when WiX/ICE wants it to change).
    Per-directory components (one Component per directory) because MSI
    requires all files of a Component to live in the same directory.

  ASCII-only on purpose (Windows PowerShell 5.1 reads BOM-less .ps1 as
  ANSI code page and mangles non-ASCII into parse errors).

  Usage:
    pwsh -NoProfile -ExecutionPolicy Bypass -File installer/scripts/gen-toolchain-wxs.ps1
#>
[CmdletBinding()]
param(
    [string]$ManifestPath = "installer/build-artifacts/toolchain-manifest.json",
    [string]$OutWxs       = "installer/build-artifacts/wix/jhyy-toolchain.generated.wxs",
    [string]$InstallDirName = "toolchain"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $repoRoot

if (-not (Test-Path $ManifestPath)) { throw "toolchain manifest not found: $ManifestPath (run collect-toolchain.ps1 first)" }
$mf = [System.IO.File]::ReadAllText((Resolve-Path $ManifestPath).Path, [System.Text.Encoding]::UTF8) | ConvertFrom-Json

# --------------------------------------------------------------------------
# Deterministic UUID v5 (RFC 4122) - no external dependency.
# --------------------------------------------------------------------------
$JHY_NS = "6f1c2a3e-9b47-4d58-8a61-0c2e5f7d3b90"   # fixed project namespace

function New-UuidV5([string]$name) {
    $nsHex = ($JHY_NS -replace '-', '')
    $nsBytes = New-Object byte[] 16
    for ($i = 0; $i -lt 16; $i++) { $nsBytes[$i] = [Convert]::ToByte($nsHex.Substring($i * 2, 2), 16) }
    $nameBytes = [System.Text.Encoding]::UTF8.GetBytes($name)
    $buf = New-Object byte[] ($nsBytes.Length + $nameBytes.Length)
    [Array]::Copy($nsBytes, 0, $buf, 0, $nsBytes.Length)
    [Array]::Copy($nameBytes, 0, $buf, $nsBytes.Length, $nameBytes.Length)
    $sha = [System.Security.Cryptography.SHA1]::Create()
    $hash = $sha.ComputeHash($buf)
    $sha.Dispose()
    $b = New-Object byte[] 16
    [Array]::Copy($hash, 0, $b, 0, 16)
    $b[6] = [byte](($b[6] -band 0x0F) -bor 0x50)   # version 5
    $b[8] = [byte](($b[8] -band 0x3F) -bor 0x80)   # variant 10xx
    $hex = ($b | ForEach-Object { $_.ToString("x2") }) -join ''
    return ("{0}-{1}-{2}-{3}-{4}" -f $hex.Substring(0,8), $hex.Substring(8,4), $hex.Substring(12,4), $hex.Substring(16,4), $hex.Substring(20,12))
}

function ConvertTo-Id([string]$s) {
    $t = $s -replace '[^A-Za-z0-9_]', '_'
    if ($t.Length -gt 48) {
        $sha = [System.Security.Cryptography.SHA1]::Create()
        $h = ($sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($s)) | ForEach-Object { $_.ToString("x2") }) -join ''
        $sha.Dispose()
        $t = $t.Substring(0, 40) + "_" + $h.Substring(0, 8)
    }
    if ($t -match '^[0-9]') { $t = "_" + $t }
    return $t
}

# WiX identifiers should be <= 72 chars (WIX1026 warns above that). The
# toolchain has deeply nested paths (lib/gcc/x86_64-w64-mingw32/15.2.0/include)
# and long file names (avx10_2_512convertintrin.h), so a naive
# "TcF" + dirId + "_" + name blows past the limit. When it does, replace the
# name part with a hash of the full relative path (still unique, still stable).
function New-FileId([string]$dirId, [string]$name, [string]$fullPath) {
    $id = "TcF" + $dirId + "_" + (ConvertTo-Id $name)
    if ($id.Length -le 70) { return $id }
    $sha = [System.Security.Cryptography.SHA1]::Create()
    $h = ($sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($fullPath)) | ForEach-Object { $_.ToString("x2") }) -join ''
    $sha.Dispose()
    $keep = 70 - 3 - 1 - 8
    if ($keep -lt 4) { $keep = 4 }
    return "TcF" + $dirId.Substring(0, [Math]::Min($dirId.Length, $keep)) + "_" + $h.Substring(0, 8)
}

# --------------------------------------------------------------------------
# Directory tree
# --------------------------------------------------------------------------
# The manifest lists directories that actually hold files. Their ANCESTORS
# (e.g. "LICENSES" for "LICENSES/binutils") must exist as <Directory>
# elements too, otherwise the subtree would never be emitted.
$filesByDir = @{}
foreach ($d in $mf.dirs) { $filesByDir[$d.path] = @($d.files) }

$allPaths = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::Ordinal)
foreach ($k in $filesByDir.Keys) { [void]$allPaths.Add($k) }
# add ancestors
$queue = New-Object System.Collections.ArrayList
foreach ($k in @($allPaths)) { [void]$queue.Add($k) }
while ($queue.Count -gt 0) {
    $p = $queue[0]; $queue.RemoveAt(0)
    if ([string]::IsNullOrEmpty($p)) { continue }
    $idx = $p.LastIndexOf('/')
    if ($idx -lt 0) { continue }
    $parent = $p.Substring(0, $idx)
    if (-not $allPaths.Contains($parent)) {
        [void]$allPaths.Add($parent)
        [void]$queue.Add($parent)
    }
}

$byParent = @{}
foreach ($p in $allPaths) {
    if ([string]::IsNullOrEmpty($p)) { continue }          # the root is the tree root
    $idx = $p.LastIndexOf('/')
    $parent = if ($idx -lt 0) { "" } else { $p.Substring(0, $idx) }
    if (-not $byParent.ContainsKey($parent)) { $byParent[$parent] = New-Object System.Collections.ArrayList }
    [void]$byParent[$parent].Add($p)
}

function Get-DirId([string]$path) {
    if ([string]::IsNullOrEmpty($path)) { return "TcRoot" }
    return "TcD" + (ConvertTo-Id ($path -replace '/', '_'))
}

$lines = New-Object System.Collections.Generic.List[string]
$compIds = New-Object System.Collections.Generic.List[string]

$lines.Add('<?xml version="1.0" encoding="utf-8"?>')
$lines.Add('<!--')
$lines.Add('  GENERATED FILE - do not edit.')
$lines.Add('  Produced by installer/scripts/gen-toolchain-wxs.ps1 from')
$lines.Add('  installer/build-artifacts/toolchain-manifest.json')
$lines.Add("  gcc $($mf.gcc_version) / $($mf.target) / $($mf.file_count) files / $([math]::Round($mf.total_bytes/1MB,1)) MB")
$lines.Add('-->')
$lines.Add('<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs">')
$lines.Add('  <Fragment>')
$lines.Add('    <DirectoryRef Id="INSTALLDIR">')

function Emit-Dir([string]$path, [string]$indent) {
    $id = Get-DirId $path
    $name = if ([string]::IsNullOrEmpty($path)) { $InstallDirName } else { ($path -split '/')[-1] }
    $fs = if ([string]::IsNullOrEmpty($path)) { "!(bindpath.toolchain)" } else { "!(bindpath.toolchain)\" + ($path -replace '/', '\') }
    $lines.Add("$indent<Directory Id=`"$id`" Name=`"$name`" FileSource=`"$fs`">")

    if ($filesByDir.ContainsKey($path)) {
        $files = $filesByDir[$path]
        $names = @($files | ForEach-Object { $_.name } | Sort-Object)
        $compId = "TcC" + $id
        $guid = New-UuidV5 ("component:" + $path + "|" + ($names -join ","))
        $lines.Add("$indent  <Component Id=`"$compId`" Bitness=`"always64`" Guid=`"$guid`">")
        $first = $true
        $prefix = if ([string]::IsNullOrEmpty($path)) {
            "!(bindpath.toolchain)\"
        } else {
            "!(bindpath.toolchain)\" + ($path -replace '/', '\') + "\"
        }
        foreach ($f in $files) {
            $fid = New-FileId $id $f.name ("$path/$($f.name)")
            $kp = if ($first) { " KeyPath=`"yes`"" } else { "" }
            # The Source must be the FULL path. WiX 4 does NOT use
            # <Directory FileSource="..."> as a base for relative File
            # Source paths - a bare filename resolves against the CURRENT
            # DIRECTORY of the wix build and fails with WIX0103. The
            # existing components in jhyy-compiler.wxs use the same
            # full-path form (e.g. Source="!(bindpath.bin)\std\arena.jhyy").
            $src = $prefix + $f.name
            $lines.Add("$indent    <File Id=`"$fid`" Source=`"$src`"$kp />")
            $first = $false
        }
        $lines.Add("$indent  </Component>")
        $compIds.Add($compId)
    }

    if ($byParent.ContainsKey($path)) {
        foreach ($child in ($byParent[$path] | Sort-Object)) { Emit-Dir $child ($indent + "  ") }
    }
    $lines.Add("$indent</Directory>")
}

Emit-Dir "" "      "

$lines.Add('    </DirectoryRef>')
$lines.Add('')
$lines.Add('    <ComponentGroup Id="JHYYToolchain">')
foreach ($c in $compIds) { $lines.Add("      <ComponentRef Id=`"$c`" />") }
$lines.Add('    </ComponentGroup>')
$lines.Add('  </Fragment>')
$lines.Add('</Wix>')

$outDir = Split-Path $OutWxs -Parent
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }
$lines | Set-Content -Path $OutWxs -Encoding utf8

$mb = [math]::Round($mf.total_bytes / 1MB, 1)
Write-Host "[gen-toolchain-wxs] wrote $OutWxs ($($mf.file_count) files / $($compIds.Count) components / $mb MB)"
