# Email-Intelligence daily review scheduler (Windows Task Scheduler): 05:00 / 13:00 / 21:00 Mon-Sat.
# Usage: powershell -ExecutionPolicy Bypass -File install_windows.ps1
# Uninstall: powershell -ExecutionPolicy Bypass -File install_windows.ps1 -Unregister
param([switch]$Unregister)
$ErrorActionPreference = 'Stop'

$TaskName = 'CC-EmailIntel-Review'
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent   # .scripts/email-intelligence -> workspace
$Script = Join-Path $PSScriptRoot 'run_email_intel.py'
$LogDir = Join-Path $Root 'daily\logs'
$Runner = Join-Path $PSScriptRoot 'run_email_intel_windows.cmd'

if ($Unregister) {
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Output "Unregistered task $TaskName"
    } else {
        Write-Output "Task $TaskName does not exist."
    }
    exit 0
}

# Resolve Python: prefer the py launcher, then the python on PATH.
$Py = $null
$pyLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($pyLauncher) {
    try { $Py = (& py -3 -c "import sys; print(sys.executable)" 2>$null | Select-Object -First 1).Trim() } catch {}
}
if (-not $Py) {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) { $Py = $pythonCmd.Source }
}
if (-not $Py -or -not (Test-Path $Py)) {
    Write-Error 'Python not found (needs py -3 or python on PATH). Install Python 3.12 first.'
}

if (-not (Test-Path $Script)) { Write-Error "Entry script missing: $Script" }
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

# Generate a hidden-window cmd runner (absolute paths + log redirection).
$runnerLines = @(
    '@echo off',
    "set ROOT=$Root",
    "set PY=$Py",
    'set LOG=%ROOT%\daily\logs\email-intel-review.log',
    'mkdir "%ROOT%\daily\logs" 2>nul',
    '"%PY%" -u "%ROOT%\.scripts\email-intelligence\run_email_intel.py" review --workspace "%ROOT%" >> "%LOG%" 2>&1'
)
$runnerLines | Set-Content -LiteralPath $Runner -Encoding ASCII

# 05:00 / 13:00 / 21:00 Mon-Sat; catch up if missed; max 2 hours; ignore new if already running.
$Days = @('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday')
$Trigger = @(
    New-ScheduledTaskTrigger -Weekly -DaysOfWeek $Days -At 05:00
    New-ScheduledTaskTrigger -Weekly -DaysOfWeek $Days -At 13:00
    New-ScheduledTaskTrigger -Weekly -DaysOfWeek $Days -At 21:00
)
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 2) -MultipleInstances IgnoreNew
$Action = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument ('/c ""{0}""' -f $Runner) -WorkingDirectory $Root
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description 'Email Intelligence daily review: scan email, generate brief/panel (09:30 Mon-Sat)' -Force | Out-Null

Write-Output "Installed task $TaskName (05:00 / 13:00 / 21:00, Mon-Sat)"
Write-Output "Runner: $Runner"
Write-Output "Log: $LogDir\email-intel-review.log"
Write-Output "Manual trigger: Start-ScheduledTask -TaskName $TaskName"
