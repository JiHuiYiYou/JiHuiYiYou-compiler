# installer/common/configure-coderunner.ps1 — write code-runner.executorMap to VSCode user settings.json
#
# Sprint v1.5.6-patch2: 让用户装完 JHYY 后,VSCode 右键 "Run Code" 对 .jhyy 文件
# 直接工作 (不需要手动装 Code Runner extension + 手动写 executorMap)。
#
# 行为:
#   1. 检测 VSCode user settings.json 路径 (per-user, %APPDATA%\Code\User\settings.json)
#   2. 不存在 → 创建 (含只 code-runner 的新文件)
#   3. 存在 → parse, 添加/更新 4 个 code-runner key,保留其他所有 key/value
#   4. 原子写 (temp + Move-Item),BOM-less UTF-8 匹配 VSCode 默认格式
#
# 兼容: PowerShell 5.1 (Windows 10 ships)。
#
# 设计动机:
#   - 文本 patch 在嵌套 block end 场景下太脆弱 (regex 不能可靠识别 top-level vs inner),
#     会产出非法 JSON。
#   - ConvertTo-Json 会**重写**格式 (缩进 / 引号 / 转义), 但保证 JSON 合法 + 所有键保留。
#     用户手工调的 fontFamily 等值**字符级保留**(只换 escape 形式,如 ' → ',语义等价)。
#     4 个 code-runner key 的插入**确定性**成功。

[CmdletBinding()]
param(
    [string]$JHY_DIR = ""
)

$ErrorActionPreference = "Stop"

# === Constants ===
$vscode_user_dir = Join-Path $env:APPDATA "Code\User"
$settings_path = Join-Path $vscode_user_dir "settings.json"

# === 1. Decide path ===
if (-not (Test-Path $vscode_user_dir)) {
    Write-Host "[INFO] VSCode user dir not found at $vscode_user_dir"
    Write-Host "[INFO] Skipping code-runner config (VSCode not installed / not yet run)"
    exit 0
}

# === 2. Load existing settings (or null) ===
$raw = $null
$parsed = $null
$existed = Test-Path $settings_path
if ($existed) {
    $raw = Get-Content -Path $settings_path -Raw -Encoding UTF8
    if (-not [string]::IsNullOrWhiteSpace($raw)) {
        try {
            $parsed = $raw | ConvertFrom-Json
        } catch {
            Write-Host "[ERROR] Failed to parse existing settings.json: $_"
            Write-Host "[INFO] settings.json preserved as-is. User must fix manually."
            exit 1
        }
    }
}

# === 3. Ensure $parsed is PSCustomObject (ConvertFrom-Json returns $null for empty input) ===
if ($null -eq $parsed) {
    $parsed = New-Object PSObject
}

# === 4. Build / update code-runner keys ===
# 4a. executorMap: dict with jhyy mapping
$current_map = $parsed.'code-runner.executorMap'
if ($null -eq $current_map) {
    $current_map = New-Object PSObject
}
if (-not ($current_map.PSObject.Properties.Name -contains 'jhyy')) {
    $current_map | Add-Member -NotePropertyName 'jhyy' -NotePropertyValue 'cd $dirWithoutTrailingSlash && jhyy run $fileName' -Force
}
$parsed | Add-Member -NotePropertyName 'code-runner.executorMap' -NotePropertyValue $current_map -Force

# 4b. simple bool keys
$parsed | Add-Member -NotePropertyName 'code-runner.runInTerminal' -NotePropertyValue $true -Force
$parsed | Add-Member -NotePropertyName 'code-runner.saveFileBeforeRun' -NotePropertyValue $true -Force
$parsed | Add-Member -NotePropertyName 'code-runner.clearPreviousOutput' -NotePropertyValue $true -Force

# === 5. Re-serialize ===
# Depth 10 handles typical nested objects (java.configuration.runtimes array of objects,
# terminal profiles, etc.). PowerShell 5.1 ConvertTo-Json max depth default = 2.
$new_content = $parsed | ConvertTo-Json -Depth 10

# === 6. Write atomically (BOM-less UTF-8 to match VSCode's own format) ===
try {
    $temp_path = "$settings_path.tmp"
    $utf8_no_bom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($temp_path, $new_content, $utf8_no_bom)
    Move-Item -Path $temp_path -Destination $settings_path -Force
} catch {
    Write-Host "[ERROR] Failed to write settings.json: $_"
    exit 1
}

Write-Host "[OK] Wrote code-runner.executorMap to $settings_path"
if ($JHY_DIR) {
    Write-Host "[INFO] JHYY install dir: $JHY_DIR"
}
exit 0
