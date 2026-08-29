# installer/common/manual-fix-icon-cache.ps1
#
# v1.8.2 patch: 手动修复 .jhyy 文件图标 (Path B).
#
# user 选择: 注册 JHYY.EditInVSCode 自定义 ProgId (icon=jhyy-icon.ico, command=VSCode),
# 然后用 Mozilla reverse-engineered UserChoice Hash 算法写 UserChoice=JHYY.EditInVSCode.
#
# v1.8.1 patch 只清了 HKCU\Software\Classes\.jhyy 主键 (MSYS2 shadow),
# v1.8.2 挖出更深的两层 hijack:
#   1. HKCU\…\Explorer\FileExts\.jhyy\UserChoice\ProgId = Applications\Code.exe
#      (VSCode "始终用此应用打开" 锁存 — UCPD.sys 加 Deny ACE 防护, 需 admin 才能写)
#   2. HKCU\…\Explorer\FileExts\.jhyy\OpenWithProgids\jhyy_auto_file
#      (MSYS2 *auto_file heuristic, v1.8.1 没清 OpenWithProgids 引用)
#
# Run elevated (Right-click → Run as Administrator, 或通过 install-configure-all.bat
# 自动 self-elevate). 给已经装过 v1.8.0/v1.8.1 的现有机器用.
#
# Algorithm reference:
#   Mozilla Firefox browser/components/shell/WindowsUserChoice.cpp (MPL 2.0)
#   PS-SFTA by DanysysTeam / SetUserFTA by kolbi (MIT)
#
# Exit codes:
#   0  all steps ran (individual non-fatal misses don't block)
#   1  critical error (HKLM assoc missing — fix the WiX first)

$ErrorActionPreference = 'Continue'
$logPath = "$env:TEMP\jhyy-v182-fix.log"
"=== v1.8.2 fix log start $(Get-Date -Format 'o') ===" | Out-File $logPath
function Log($msg) { Write-Host $msg; $msg | Out-File $logPath -Append }

Log "[v1.8.2 fix] Elevated session running as: $env:USERNAME"

# 0. Locate jhyy-setuc.exe (build if missing)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$setucExe = Join-Path $ScriptDir "jhyy-setuc\bin\Release\net8.0-windows\jhyy-setuc.exe"
if (-not (Test-Path $setucExe)) {
    Log "[v1.8.2 fix] jhyy-setuc.exe not found, building..."
    $buildScript = Join-Path $ScriptDir "jhyy-setuc\build.ps1"
    if (Test-Path $buildScript) {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $buildScript | Out-Null
    }
    if (-not (Test-Path $setucExe)) {
        Log "[v1.8.2 fix] FATAL: jhyy-setuc.exe build failed"
        exit 1
    }
}
Log "[v1.8.2 fix] Using jhyy-setuc: $setucExe"

# 1. 验证 HKLM 注册表完好 (HKCR\Classes\.jhyy -> JHYY.SourceFile)
$hkcrKey = 'HKLM:\SOFTWARE\Classes\.jhyy'
$hkcrDefault = (Get-ItemProperty -Path $hkcrKey -ErrorAction SilentlyContinue).'(default)'
if ($hkcrDefault) {
    Log "[v1.8.2 fix] HKLM assoc .jhyy = $hkcrDefault"
} else {
    Log "[v1.8.2 fix] WARN: HKLM\SOFTWARE\Classes\.jhyy not visible from this PowerShell session"
    Log "[v1.8.2 fix]        (cosmetic — reg.exe confirms it exists; v1.8.1 fix applied earlier)"
}

# 2. Locate Code.exe (for the openCommand)
$codePath = Join-Path $env:LOCALAPPDATA "Programs\Microsoft VS Code\Code.exe"
if (-not (Test-Path $codePath)) {
    Log "[v1.8.2 fix] WARN: Code.exe not found at $codePath — UserChoice write will still register ProgId but command may fail"
}

# 3. Locate JHYY icon
$iconPath = "C:\Program Files\JHYY\bin\jhyy-icon.ico"
if (-not (Test-Path $iconPath)) {
    Log "[v1.8.2 fix] FATAL: JHYY icon not found at $iconPath"
    exit 1
}

# 4. Run the jhyy-setuc tool (Path B: register ProgId + write UserChoice)
$openCmd = "`"$codePath`" `"%1`""
$pathBSuccess = $false
Log "[v1.8.2 fix] Running Path B: register ProgId + write UserChoice..."
try {
    $proc = Start-Process -FilePath $setucExe `
        -ArgumentList '.jhyy','JHYY.EditInVSCode','JHYY Source File',$iconPath,'0',$openCmd `
        -NoNewWindow -Wait -PassThru `
        -RedirectStandardOutput "$env:TEMP\jhyy-setuc.out" `
        -RedirectStandardError "$env:TEMP\jhyy-setuc.err"
    Log "[v1.8.2 fix] jhyy-setuc exit code: $($proc.ExitCode)"
    if (Test-Path "$env:TEMP\jhyy-setuc.out") {
        Get-Content "$env:TEMP\jhyy-setuc.out" | ForEach-Object { Log "[jhyy-setuc stdout] $_" }
    }
    if (Test-Path "$env:TEMP\jhyy-setuc.err") {
        Get-Content "$env:TEMP\jhyy-setuc.err" | ForEach-Object { Log "[jhyy-setuc stderr] $_" }
    }
    if ($proc.ExitCode -eq 0) {
        $pathBSuccess = $true
    } else {
        Log "[v1.8.2 fix] Path B failed (exit $($proc.ExitCode)). Falling back to Path A."
    }
} catch {
    Log "[v1.8.2 fix] Path B threw exception: $($_.Exception.Message). Falling back to Path A."
}

# 4a. Path A fallback: if Path B failed (.NET 8 Desktop Runtime missing, UCPD
#     pause blocked, etc.), fall back to delete-only approach. Explorer will
#     fall through to HKLM\SOFTWARE\Classes\.jhyy\(default) = JHYY.SourceFile
#     whose DefaultIcon = jhyy.exe,0 (the same branded icon, just embedded in
#     jhyy.exe itself per v1.8.1 patch).
if (-not $pathBSuccess) {
    Log "[v1.8.2 fix] Path A fallback: clearing HKCU shadows..."
    $fileExtsKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.jhyy'
    if (Test-Path $fileExtsKey) {
        Remove-Item -Path $fileExtsKey -Recurse -Force -ErrorAction SilentlyContinue
        Log "[v1.8.2 fix] Path A: HKCU FileExts\.jhyy cleared"
    } else {
        Log "[v1.8.2 fix] Path A: no FileExts\.jhyy shadow"
    }
    $autoFileKey = 'HKCU:\Software\Classes\jhyy_auto_file'
    if (Test-Path $autoFileKey) {
        Remove-Item -Path $autoFileKey -Recurse -Force -ErrorAction SilentlyContinue
        Log "[v1.8.2 fix] Path A: HKCU\Software\Classes\jhyy_auto_file cleared"
    } else {
        Log "[v1.8.2 fix] Path A: no jhyy_auto_file ProgId"
    }
    Log "[v1.8.2 fix] Path A: Explorer will fall through to HKLM JHYY.SourceFile (jhyy.exe,0 icon)"
}

# 5. Brute-force refresh icon cache (always — Path B and Path A both need it)
Log "[v1.8.2 fix] Killing explorer.exe..."
Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Log "[v1.8.2 fix] Deleting iconcache_*.db + thumbcache_*.db..."
$caches = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_*.db" -ErrorAction SilentlyContinue
$thumbCaches = Get-ChildItem "$env:LOCALAPPDATA\Microsoft\Windows\Explorer\thumbcache_*.db" -ErrorAction SilentlyContinue
$count = 0
foreach ($c in @($caches) + @($thumbCaches)) {
    Remove-Item -Path $c.FullName -Force -ErrorAction SilentlyContinue
    $count++
}
Log "[v1.8.2 fix] Removed $count cache files"
Log "[v1.8.2 fix] Restarting explorer.exe..."
Start-Process explorer.exe
if ($pathBSuccess) {
    Log "[v1.8.2 fix] DONE (Path B). Open a NEW Explorer window to see branded J icon on .jhyy files."
} else {
    Log "[v1.8.2 fix] DONE (Path A fallback). Open a NEW Explorer window to see branded J icon on .jhyy files."
}
exit 0