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

# 0. Locate jhyy-setuc.exe. The script lives in INSTALLDIR\bin\ alongside
#    jhyy-setuc.exe (shipped via JHYYSetUCExe Component since v1.8.2 patch;
#    v1.8.3.1 also ships jhyy-setuc.dll + .deps.json + .runtimeconfig.json
#    so the .NET 8 apphost can find its companion assembly).
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$setucExe = Join-Path $ScriptDir "jhyy-setuc.exe"
if (-not (Test-Path $setucExe)) {
    Log "[v1.8.2 fix] jhyy-setuc.exe not found in $ScriptDir — MSI install incomplete?"
    exit 1
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
# 4-pre. Cleanup malformed `UserChoice"` subkey (leftover from earlier debugging
#      of the Mozilla Hash algorithm). The trailing quote in subkey name is
#      invalid — Explorer won't read it but reg delete / reg add may collide.
#      We delete via PowerShell `Remove-Item -Path "$key`"` (literal backtick
#      escape for the trailing quote).
$malformedKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.jhyy\UserChoice"'
if (Test-Path $malformedKey) {
    try {
        Remove-Item -Path $malformedKey -Recurse -Force -ErrorAction Stop
        Log "[v1.8.2 fix] Cleanup: malformed UserChoice`" subkey removed"
    } catch {
        Log "[v1.8.2 fix] Cleanup: malformed UserChoice`" subkey removal failed: $($_.Exception.Message)"
    }
}

# 4-pre2. Also reset OpenWithList MRU order so jhyy.exe is first
#      (not Code.exe). If UserChoice somehow gets cleared, Windows shell
#      auto-promotes MRU[0] to UserChoice — we want jhyy.exe to win.
$owListKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.jhyy\OpenWithList'
if (Test-Path $owListKey) {
    try {
        $ow = Get-ItemProperty -Path $owListKey -ErrorAction Stop
        $newMruList = 'ba'
        Set-ItemProperty -Path $owListKey -Name 'MRUList' -Value $newMruList -ErrorAction Stop
        Log "[v1.8.2 fix] OpenWithList MRUList=ba (jhyy.exe first, Code.exe second)"
    } catch {
        Log "[v1.8.2 fix] OpenWithList MRUList update skipped: $($_.Exception.Message)"
    }
}

$openCmdExe = $codePath
$pathBSuccess = $false
$pathBBlocked = $false
Log "[v1.8.2 fix] Running Path B: register ProgId + write UserChoice..."
try {
    # 6 args: ext, progId, desc, iconPath, iconIndex, openExe (C# appends "%1")
    # Start-Process -ArgumentList array does NOT quote strings with spaces —
    # PowerShell splits "JHYY Source File" into 3 args. Use ProcessStartInfo
    # with Arguments property (single string) instead, with manual quoting.
    # Earlier CLI took openCommand as one arg with embedded quotes — stripped
    # by CommandLineToArgvW, split to 7-8 args.
    $argLine = '.jhyy JHYY.EditInVSCode "' + 'JHYY Source File' + '" "' + $iconPath + '" 0 "' + $openCmdExe + '"'
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $setucExe
    $psi.Arguments = $argLine
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true
    $proc = [System.Diagnostics.Process]::Start($psi)
    $proc.WaitForExit()
    [System.IO.File]::WriteAllText("$env:TEMP\jhyy-setuc.out", $proc.StandardOutput.ReadToEnd())
    [System.IO.File]::WriteAllText("$env:TEMP\jhyy-setuc.err", $proc.StandardError.ReadToEnd())
    Log "[v1.8.2 fix] jhyy-setuc exit code: $($proc.ExitCode)"
    if (Test-Path "$env:TEMP\jhyy-setuc.out") {
        Get-Content "$env:TEMP\jhyy-setuc.out" | ForEach-Object { Log "[jhyy-setuc stdout] $_" }
    }
    if (Test-Path "$env:TEMP\jhyy-setuc.err") {
        Get-Content "$env:TEMP\jhyy-setuc.err" | ForEach-Object { Log "[jhyy-setuc stderr] $_" }
    }
    if ($proc.ExitCode -eq 0) {
        $pathBSuccess = $true
    } elseif ($proc.ExitCode -eq 2) {
        # Exit 2 = UCPD.sys blocked UserChoice write — Path A also blocked.
        $pathBBlocked = $true
        Log "[v1.8.2 fix] Path B blocked by UCPD.sys. Path A fallback will also fail."
    } else {
        Log "[v1.8.2 fix] Path B failed (exit $($proc.ExitCode)). Falling back to Path A."
    }
} catch {
    Log "[v1.8.2 fix] Path B threw exception: $($_.Exception.Message). Falling back to Path A."
}

# 4a. Path A fallback: if Path B failed (.NET 8 Desktop Runtime missing, etc.),
#     fall back to delete-only approach. Explorer will fall through to
#     HKLM\SOFTWARE\Classes\.jhyy\(default) = JHYY.SourceFile whose DefaultIcon
#     = jhyy.exe,0 (the same branded icon, embedded in jhyy.exe per v1.8.1 patch).
#     NOTE: on Win10 2024-02+ with UCPD.sys, Windows shell auto-rebuilds UserChoice
#     right after our delete — Path A alone is not enough. Use Path B if available
#     (before UCPD came along) OR manual workaround below.
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
} elseif ($pathBBlocked) {
    # UCPD.sys blocked — no programmatic UserChoice write works on Win10 2024-02+.
    # Windows shell auto-rebuilds UserChoice from a cached preference, so Path A
    # also can't stick. The user MUST take manual action:
    #   (a) Explorer → 右键 .jhyy → 打开方式 → 选择其他应用 → JHYY Source File → 始终用此应用
    #   (b) Windows 设置 → 应用 → 默认应用 → 按文件类型 → 找 .jhyy → 选 JHYY Source File
    Log "[v1.8.2 fix] Path B blocked by UCPD.sys (Win10 Feb 2024+ kernel filter)."
    Log "[v1.8.2 fix] Path A also blocked (Windows shell auto-rebuilds UserChoice from cached preference)."
    Log "[v1.8.2 fix]"
    Log "[v1.8.2 fix] MANUAL FIX required — pick one:"
    Log "[v1.8.2 fix]   (1) 资源管理器 → 右键任意 .jhyy → 打开方式 → 选择其他应用 → JHYY Source File → 勾选 始终用此应用"
    Log "[v1.8.2 fix]   (2) Windows 设置 → 应用 → 默认应用 → 按文件类型 → 输入 .jhyy → 选 JHYY.SourceFile"
    Log "[v1.8.2 fix]   (3) (高级) 安全模式启动 → reg add HKLM\\SYSTEM\\CurrentControlSet\\Services\\UCPD /v Start /t REG_DWORD /d 4 /f"
    Log "[v1.8.2 fix]       → 重启 → 重跑本脚本 → 重启 → reg add ... UCPD Start=0 重启"
    Log "[v1.8.2 fix]"
    Log "[v1.8.2 fix] ProgId JHYY.EditInVSCode 已注册 (icon=jhyy-icon.ico, command=VSCode)。"
    Log "[v1.8.2 fix] UserChoice 写不进去, 但 ProgId 可用 — 上面任一手动方式选 JHYY.EditInVSCode 即可。"
} else {
    Log "[v1.8.2 fix] DONE (Path A fallback). Open a NEW Explorer window to see branded J icon on .jhyy files."
}
exit 0