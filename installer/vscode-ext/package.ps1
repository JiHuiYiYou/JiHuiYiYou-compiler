# installer/vscode-ext/package.ps1 - VSCode extension packager (v1.5.4)
#
# Sprint v1.5.4: 把 vscode-ext/ 打成 .vsix 让 MSI 装到用户 VSCode.
# Bumps version in package.json to match $env:JHY_VERSION (e.g. 1.5.4)
# so MSI file naming 跟 compiler MSI 一致 (用户看到 jhyy-lang-1.5.4.vsix).
#
# Usage:
#   powershell -File installer/vscode-ext/package.ps1
#   JHY_VERSION=1.5.4 powershell -File installer/vscode-ext/package.ps1
#
# Env vars:
#   JHY_VERSION    installer version (default: git describe, fallback 1.5.3)
#
# Exit codes:
#   0  build OK
#   1  build failed

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

# 1. version detection (跟 installer/build.ps1 一致)
#    vsix filename uses $JHY_VERSION_DISPLAY (with optional -rcN suffix) when
#    set by parent installer/build.ps1 — keeps the .vsix name aligned with
#    the MSI/bundle filenames for RC releases (e.g. jhyy-lang-1.5.5-rc1.vsix).
#    Falls back to JHY_VERSION (numeric) for local builds / no override.
if (-not $env:JHY_VERSION) {
    try {
        $rawVer = (& git describe --tags --always 2>$null) -as [string]
        if ($rawVer) {
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
if (-not $env:JHY_VERSION) { $env:JHY_VERSION = "1.5.3" }
$JHY_VERSION_DISPLAY = if ($env:JHY_VERSION_DISPLAY) { $env:JHY_VERSION_DISPLAY } else { $env:JHY_VERSION }

# 2. verify vsce
$vsce = Get-Command vsce -ErrorAction SilentlyContinue
if (-not $vsce) {
    Write-Host "[ERROR] vsce not found in PATH."
    Write-Host "Install via:  npm install -g @vscode/vsce"
    exit 1
}

# 3. patch package.json version (in-place string replace, 避免 JSON reformat 污染 diff)
#    原始 file 4 空格缩进, "version":  "X.Y.Z" 格式 (note: "version" 后面两个空格,
#    历史 set-content 残留). 用 regex 改 first occurrence.
$pkgPath = "vscode-ext/package.json"
$origContent = Get-Content $pkgPath -Raw
$origVersion = ([regex]::Match($origContent, '"version"\s*:\s*"([^"]+)"')).Groups[1].Value
#   PowerShell gotcha: `'$1$2'` interpolation expands $1 / $2 as variables.
#   Workaround: 用 MatchEvaluator 委托, 闭包捕获 $env:JHY_VERSION.
$patchedContent = [regex]::Replace($origContent, '"version"\s*:\s*"[^"]+"', {
    param($m)
    return '"version": "' + $env:JHY_VERSION + '"'
})
Set-Content -Path $pkgPath -Value $patchedContent -NoNewline
Write-Host "[package.ps1] version: $origVersion -> $($env:JHY_VERSION)"

# 3.5. tsc compile (skip if no src/, 兼容 manifest-only 扩展历史 build)
$srcDir = "vscode-ext/src"
if (Test-Path $srcDir) {
    Write-Host "[package.ps1] compiling TypeScript..."
    if (-not (Test-Path "vscode-ext/node_modules")) {
        Write-Host "[package.ps1] installing devDependencies (one-time)..."
        Push-Location "vscode-ext"
        try { & npm install --no-audit --no-fund --omit=optional 2>&1 | Out-Host }
        finally { Pop-Location }
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] npm install failed in vscode-ext/"
            exit 1
        }
    }
    if (-not (Get-Command npx -ErrorAction SilentlyContinue)) {
        Write-Host "[ERROR] npx not found in PATH. Install Node.js."
        exit 1
    }
    Push-Location "vscode-ext"
    try { & npx --no-install tsc -p . 2>&1 | Out-Host }
    finally { Pop-Location }
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] tsc failed; aborting vsce package"
        exit 1
    }
}

# 4. cd vscode-ext/ 然后 package (vsce 默认 cwd 找 package.json)
Push-Location "vscode-ext"
try {
    # vsce 把 WARNING 当 error stream 输出, PowerShell RemoteException 会让
    # $ErrorActionPreference="Stop" 终止进程. 临时改 Continue 让 warning 不致命.
    $prevPref = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $output = & vsce package --no-git-tag-version 2>&1
    } finally {
        $ErrorActionPreference = $prevPref
    }
    # vsce returns nonzero on warnings (LICENSE / .vscodeignore) but still
    # writes the .vsix. Check file presence instead of exit code.
    # vsce always names the output after package.json's version field (which
    # we patched to JHY_VERSION numeric). For RC releases, vsix filename
    # must match MSI/bundle (e.g. jhyy-lang-1.5.5-rc1.vsix), so we rename
    # the file after vsce produces it (vsce has no --output flag).
    $vsceOutputVsix = "jhyy-lang-$($env:JHY_VERSION).vsix"
    if (-not (Test-Path $vsceOutputVsix)) {
        Write-Host "[ERROR] vsce package failed (no .vsix produced):"
        $output | ForEach-Object { Write-Host "  $_" }
        exit 1
    }
    $displayVsix = "jhyy-lang-$JHY_VERSION_DISPLAY.vsix"
    if ($JHY_VERSION_DISPLAY -ne $env:JHY_VERSION -and (Test-Path $vsceOutputVsix)) {
        # Rename-Item -Force does NOT overwrite on Windows (only clears ReadOnly
        # attribute). If a previous build left $displayVsix around, the rename
        # fails with "Cannot create a file when that file already exists." Workaround:
        # delete the destination first, then rename. Captured 2026-08-26
        # (v1.5.7-rc1 build retry loop).
        if (Test-Path $displayVsix) { Remove-Item -Path $displayVsix -Force }
        Rename-Item -Path $vsceOutputVsix -NewName $displayVsix
    }
    $output | Where-Object { $_ -match 'WARNING' } | ForEach-Object {
        Write-Host "[WARN] $_"
    }
} finally {
    Pop-Location
    # revert package.json (avoid leaving dirty working tree)
    Set-Content -Path $pkgPath -Value $origContent -NoNewline
}

# 5. move to build-artifacts
#    After step 4 rename, the vsix filename matches DISPLAY version
#    (e.g. jhyy-lang-1.5.5-rc1.vsix) — same as MSI/bundle filenames.
$vsix = "vscode-ext/jhyy-lang-$JHY_VERSION_DISPLAY.vsix"
if (-not (Test-Path $vsix)) {
    Write-Host "[ERROR] vsix not found at $vsix"
    exit 1
}
$destDir = "installer/build-artifacts"
if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
Copy-Item $vsix "$destDir/jhyy-lang-$JHY_VERSION_DISPLAY.vsix" -Force
Write-Host "[OK] $destDir/jhyy-lang-$JHY_VERSION_DISPLAY.vsix built"

exit 0