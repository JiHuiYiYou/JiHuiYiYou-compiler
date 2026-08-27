# install-configure-env.ps1 (v1.5.7-rc1)
# MSI CustomAction post-install: set MSYS2_PATH_TYPE=inherit at User env scope.
#
# Why: MSYS2 bash defaults to MSYS2_PATH_TYPE=minimal (/etc/profile line 28),
# which does NOT inherit Windows user/system PATH — only 4 hardcoded Windows
# system paths. After MSI installs jhyy.exe to C:\Program Files\JHYY\bin and
# adds it to HKLM system PATH, MSYS2 bash still cannot find jhyy because
# minimal mode ignores the new PATH entry.
#
# Setting MSYS2_PATH_TYPE=inherit makes MSYS2 bash pick up the full Windows
# PATH, so jhyy.exe is resolvable from any MSYS2 shell.
#
# This is the SECOND of two MSYS2 mitigations — the other is the .bashrc PATH
# export, but that only fires if the user opens MSYS2 bash at least once
# after install (bashrc is per-user). The env var fires for ALL new MSYS2
# bash sessions, no first-launch needed.
#
# User-scope env var: no admin required.
# Idempotent: skip if already "inherit".
#
# CustomAction: deferred, impersonate=no, Return=ignore (failure non-fatal
# per v1.5.2 pattern; v1.5.7-rc1 rev 2 pivot — install-vsix.bat superseded
# in v1.5.10, this orchestrator now runs from HKLM RunOnce instead).

$ErrorActionPreference = "Stop"

$envVarName = "MSYS2_PATH_TYPE"
$envVarValue = "inherit"

Write-Host "[install-configure-env] === set $envVarName = $envVarValue (User scope) ==="

$current = [System.Environment]::GetEnvironmentVariable($envVarName, "User")
Write-Host "[install-configure-env] current User $envVarName = [$current]"

if ($current -eq $envVarValue) {
    Write-Host "[install-configure-env] already set, nothing to do" -ForegroundColor Green
    exit 0
}

try {
    [System.Environment]::SetEnvironmentVariable($envVarName, $envVarValue, "User")
    Write-Host "[install-configure-env] wrote User $envVarName = $envVarValue" -ForegroundColor Green
} catch {
    Write-Host "[install-configure-env] ERROR: $($_.Exception.Message)" -ForegroundColor Red
    # Non-fatal — install proceeds without MSYS2 PATH inherit. User can run
    # add_jhyy_to_user_path.ps1 manually OR the .bashrc export will catch it.
    exit 0
}

# Verify
$verify = [System.Environment]::GetEnvironmentVariable($envVarName, "User")
Write-Host "[install-configure-env] verified: $envVarName = [$verify]"
exit 0