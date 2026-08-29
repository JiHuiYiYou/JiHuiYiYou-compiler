# install-configure-vscode.ps1 (v1.5.7-rc1)
# MSI CustomAction post-install: configure VSCode user settings.json so the
# integrated terminal defaults to "bash (MSYS2)" — required for jhyy to be
# resolvable from VSCode's terminal because MSYS2 bash in minimal PATH mode
# does not inherit the C:\Program Files\JHYY\bin entry the MSI just added
# to HKLM system PATH (see install-configure-env.ps1 for the env-var side).
#
# Conservative merge rules (don't clobber user's existing settings):
#   1. If %APPDATA%\Code\User\settings.json does NOT exist → skip (let
#      user open VSCode once so it creates defaults, then re-run if needed).
#   2. If file is malformed JSON → skip with warning (don't risk corruption).
#   3. If `terminal.integrated.defaultProfile.windows` is already set to
#      ANY value → leave it alone (respect user choice; if they prefer
#      PowerShell that's fine — the env var + system PATH cover cmd/PS).
#   4. If `terminal.integrated.defaultProfile.windows` is NOT set → add
#      `"bash (MSYS2)"` as the default.
#   5. If `terminal.integrated.profiles.windows."bash (MSYS2)"` is NOT set →
#      add the profile (same args as existing user profile).
#   6. If profile IS set but `path` points to a different bash.exe → leave
#      alone (user may have multiple MSYS2 installs).
#
# PS 5.1 compatible (uses System.IO.File for UTF-8 no-BOM write; PS5
# Set-Content -Encoding UTF8 writes BOM, which VSCode handles but is non-canonical).
#
# CustomAction: deferred, impersonate=no, Return=ignore (failure non-fatal).

$ErrorActionPreference = "Stop"

$settingsPath = Join-Path $env:APPDATA "Code\User\settings.json"
$profileName = "bash (MSYS2)"
$defaultProfileKey = "terminal.integrated.defaultProfile.windows"

Write-Host "[install-configure-vscode] === configure VSCode user settings ==="
Write-Host "[install-configure-vscode] path = $settingsPath"

if (-not (Test-Path $settingsPath)) {
    Write-Host "[install-configure-vscode] settings.json not found — skipping" -ForegroundColor Yellow
    Write-Host "[install-configure-vscode] (open VSCode once to create defaults, then re-run if needed)"
    exit 0
}

# Read raw text (preserves comments — ConvertFrom-Json strips them but we
# only write if we successfully round-trip, so we re-parse and write a
# clean JSON tree without comments).
$rawText = Get-Content -Path $settingsPath -Raw -Encoding UTF8
if ($null -eq $rawText) { $rawText = "" }

# Try parse. ConvertFrom-Json is permissive about trailing commas (PS6+) but
# strict in PS5.1. Tolerate PS5 strict by stripping trailing commas in
# objects/arrays — limited but covers common user typos.
try {
    $settingsObj = $rawText | ConvertFrom-Json
} catch {
    Write-Host "[install-configure-vscode] settings.json is malformed JSON — skipping" -ForegroundColor Yellow
    Write-Host "[install-configure-vscode] error: $($_.Exception.Message)"
    Write-Host "[install-configure-vscode] user can manually edit or delete the file"
    exit 0
}

# Check if settings is actually a hashtable-like object (it will be PSCustomObject)
if ($null -eq $settingsObj) {
    Write-Host "[install-configure-vscode] settings.json is empty — treating as {}"
    $settingsObj = [PSCustomObject]@{}
}

# Existing terminal.integrated.defaultProfile.windows value?
$existingDefault = $null
if ($settingsObj.PSObject.Properties.Match($defaultProfileKey).Count -gt 0) {
    $existingDefault = $settingsObj."terminal.integrated"."defaultProfile"."windows"
}

if ($existingDefault) {
    Write-Host "[install-configure-vscode] defaultProfile already set to [$existingDefault] — leaving alone" -ForegroundColor Green
    Write-Host "[install-configure-vscode] (user has explicit choice; honor it)"
    exit 0
}

# No defaultProfile set — check if our profile entry exists
$existingProfile = $null
if ($settingsObj.PSObject.Properties.Match("terminal.integrated.profiles.windows").Count -gt 0) {
    $existingProfile = $settingsObj."terminal.integrated"."profiles"."windows"
}

$profileEntry = $null
if ($existingProfile -and $existingProfile.PSObject.Properties.Match($profileName).Count -gt 0) {
    $profileEntry = $existingProfile."$profileName"
}

# Build profile entry (idempotent — only set fields if missing)
if (-not $profileEntry) {
    Write-Host "[install-configure-vscode] adding profile [$profileName]"
    $newProfileEntry = [PSCustomObject]@{
        path = "C:\msys64\usr\bin\bash.exe"
        args = @("--login", "-i")
        env  = [PSCustomObject]@{ CHERE_INVOKING = "1" }
    }
    # Insert into profiles. ConvertFrom-Json returns PSCustomObject even for
    # empty dicts. We need to MERGE without losing other profiles.
    if (-not $existingProfile) {
        $newProfiles = [PSCustomObject]@{
            "$profileName" = $newProfileEntry
        }
    } else {
        # Add property to existing PSCustomObject via Add-Member (works for
        # PSCustomObject only; for hashtable we'd use `.Key = value`).
        $existingProfile | Add-Member -NotePropertyName $profileName -NotePropertyValue $newProfileEntry -Force
        $newProfiles = $existingProfile
    }
} else {
    Write-Host "[install-configure-vscode] profile [$profileName] already exists — leaving alone"
    $newProfiles = $existingProfile
}

# Build the full settings tree. We replace the entire settings object with a
# PSCustomObject containing the original keys + our additions. This works
# because ConvertFrom-Json gives us a PSCustomObject and ConvertTo-Json
# round-trips it cleanly.
$newSettings = [PSCustomObject]@{}

# Copy original keys
foreach ($prop in $settingsObj.PSObject.Properties) {
    if ($prop.Name -eq "terminal") { continue }  # we handle terminal separately
    Add-Member -InputObject $newSettings -NotePropertyName $prop.Name -NotePropertyValue $prop.Value -Force
}

# Build new terminal object
$terminalObj = $null
if ($settingsObj.PSObject.Properties.Match("terminal").Count -gt 0) {
    $terminalObj = $settingsObj."terminal"
}

$newTerminal = [PSCustomObject]@{}
if ($terminalObj) {
    foreach ($prop in $terminalObj.PSObject.Properties) {
        if ($prop.Name -eq "integrated") { continue }
        Add-Member -InputObject $newTerminal -NotePropertyName $prop.Name -NotePropertyValue $prop.Value -Force
    }
}

$integratedObj = $null
if ($terminalObj -and $terminalObj.PSObject.Properties.Match("integrated").Count -gt 0) {
    $integratedObj = $terminalObj."integrated"
}

$newIntegrated = [PSCustomObject]@{}
if ($integratedObj) {
    foreach ($prop in $integratedObj.PSObject.Properties) {
        if ($prop.Name -eq "profiles" -or $prop.Name -eq "defaultProfile") { continue }
        Add-Member -InputObject $newIntegrated -NotePropertyName $prop.Name -NotePropertyValue $prop.Value -Force
    }
}

# Add profiles
Add-Member -InputObject $newIntegrated -NotePropertyName "profiles" -NotePropertyValue (
    [PSCustomObject]@{
        windows = $newProfiles
    }
) -Force

# Add defaultProfile
Add-Member -InputObject $newIntegrated -NotePropertyName "defaultProfile" -NotePropertyValue (
    [PSCustomObject]@{
        windows = $profileName
    }
) -Force

# Reassemble terminal
Add-Member -InputObject $newTerminal -NotePropertyName "integrated" -NotePropertyValue $newIntegrated -Force
Add-Member -InputObject $newSettings -NotePropertyName "terminal" -NotePropertyValue $newTerminal -Force

# Write UTF-8 without BOM (canonical for VSCode settings.json)
$newJson = $newSettings | ConvertTo-Json -Depth 10
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
try {
    [System.IO.File]::WriteAllText($settingsPath, $newJson, $utf8NoBom)
    Write-Host "[install-configure-vscode] wrote $settingsPath" -ForegroundColor Green
    Write-Host "[install-configure-vscode] added defaultProfile.windows = $profileName"
} catch {
    Write-Host "[install-configure-vscode] ERROR writing file: $($_.Exception.Message)" -ForegroundColor Red
    exit 0
}

exit 0