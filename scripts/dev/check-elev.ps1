$id = [Security.Principal.WindowsIdentity]::GetCurrent()
$pr = New-Object Security.Principal.WindowsPrincipal($id)
$isAdmin = $pr.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
Write-Host "IsAdmin=$isAdmin"
Write-Host "PID=$($id.User.Value)"
Write-Host "TokenType=$($id.GetType().Name)"
