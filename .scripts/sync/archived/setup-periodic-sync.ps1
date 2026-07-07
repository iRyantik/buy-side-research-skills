# setup-periodic-sync.ps1
# Add a scheduled task that runs sync every 10 minutes

$ErrorActionPreference = "Stop"

$taskName = 'ClaudeCodeAutoSync'
$scriptPath = "$PSScriptRoot\sync-sessions.ps1"

# Remove existing task if any
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Removing existing task..."
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Create action: run sync script silently
$action = New-ScheduledTaskAction -Execute 'powershell.exe' `
    -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`""

# Create trigger: every 10 minutes, indefinite
$trigger = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes 10) `
    -RepetitionDuration (New-TimeSpan -Days 36500)

# Settings: hidden, run on battery, survive network drops
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -Hidden `
    -MultipleInstances IgnoreNew

# Principal: run as current user
$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

# Register
Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description 'Auto-sync Claude Code sessions every 10 min' | Out-Null

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Periodic Sync Setup Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$task = Get-ScheduledTask -TaskName $taskName
Write-Host "  Task Name : $($task.TaskName)"
Write-Host "  State     : $($task.State)"
Write-Host "  Interval  : Every 10 minutes"
Write-Host ""
Write-Host "Sync now runs:" -ForegroundColor White
Write-Host "  1. At login (60s delay) - from previous setup" -ForegroundColor Gray
Write-Host "  2. Every 10 minutes (background, silent)" -ForegroundColor Gray
Write-Host ""
Write-Host "You no longer need to do anything. It just works." -ForegroundColor Green
