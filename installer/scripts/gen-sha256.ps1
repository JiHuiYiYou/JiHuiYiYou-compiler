# installer/scripts/gen-sha256.ps1 - Generate SHA256.txt for build artifacts (v1.5.5)
#
# Sprint v1.5.5: GH Actions release workflow consumes this file to:
#   - Upload SHA256.txt as Release asset
#   - Fill InstallerSha256 in winget manifest (per-version filled by CI)
#
# Scans installer/build-artifacts/ for .exe / .msi / .vsix and writes
# installer/SHA256.txt in `<hash>  <filename>` format (2 spaces, like
# `sha256sum` output) so `sha256sum -c SHA256.txt` works downstream.
#
# Usage:
#   powershell -File installer/scripts/gen-sha256.ps1           # default: installer/build-artifacts/
#   powershell -File installer/scripts/gen-sha256.ps1 -ArtifactsDir <dir>  # override
#
# Exit codes:
#   0  SHA256.txt written (or already up-to-date)
#   1  no build artifacts found (nothing to hash)
#
# Why PowerShell Get-FileHash (not `sha256sum`): GitHub Actions Windows runners
# don't have `sha256sum` on PATH by default; `Get-FileHash` is built-in.

[CmdletBinding()]
param(
    [string]$ArtifactsDir = "installer/build-artifacts",
    [string]$OutputFile   = "installer/SHA256.txt"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $ArtifactsDir)) {
    Write-Host "[ERROR] artifacts dir not found: $ArtifactsDir"
    exit 1
}

# Glob: .exe / .msi / .vsix (Burn bundle + MSI + VSCode ext, the 3 release artifacts).
#   Note: PS Get-ChildItem -Include with multiple patterns needs Path wildcard;
#   we use Where-Object -contains on Extension which is reliable cross-version.
$exts = @(".exe", ".msi", ".vsix")
$files = Get-ChildItem -Path $ArtifactsDir -File |
         Where-Object { $exts -contains $_.Extension } |
         Sort-Object Name

if ($files.Count -eq 0) {
    Write-Host "[ERROR] no .exe/.msi/.vsix files in $ArtifactsDir"
    Write-Host "Run installer/build.ps1 bundle first."
    exit 1
}

# Build <hash>  <filename> lines (sha256sum format)
$lines = foreach ($f in $files) {
    $hash = (Get-FileHash -Path $f.FullName -Algorithm SHA256).Hash.ToLower()
    "{0}  {1}" -f $hash, $f.Name
}

# Write (UTF-8 no BOM; LF line endings; `sha256sum -c` is BOM/CRLF-sensitive).
#
# Why LF not CRLF: Windows PowerShell [IO.File]::WriteAllLines uses Environment.NewLine
# which is CRLF on Windows. But `sha256sum -c` on Linux (scoop CI uses Linux container,
# per plan v1.5.5 autoupdate regex matches SHA256.txt format with LF only) treats the
# `\r` as part of the filename → "No such file or directory" error. Fix: build a single
# string joined with explicit `\n`, then WriteAllText with UTF-8 no BOM.
#
# See memory feedback_qbe_crlf_root_cause — same root cause (Windows fopen "w" / PS
# default newline) applies to any UTF-8 line-oriented file consumed by Linux tooling.
$outDir = Split-Path -Parent $OutputFile
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
# Build a single string with explicit LF; trailing newline for POSIX compatibility
$content = ($lines -join "`n") + "`n"
[System.IO.File]::WriteAllText($OutputFile, $content, $utf8NoBom)

Write-Host "[OK] $OutputFile written ($($files.Count) entries)"
foreach ($f in $files) {
    $hash = (Get-FileHash -Path $f.FullName -Algorithm SHA256).Hash.ToLower()
    Write-Host "    $hash  $($f.Name)"
}
exit 0