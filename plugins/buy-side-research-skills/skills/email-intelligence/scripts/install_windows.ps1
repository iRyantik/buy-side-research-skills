# Email-Intelligence 每日 review 定时（Windows 计划任务）：09:30 周一~六
# 用法：powershell -ExecutionPolicy Bypass -File install_windows.ps1
# 卸载：powershell -ExecutionPolicy Bypass -File install_windows.ps1 -Unregister
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
        Write-Output "已卸载计划任务 $TaskName"
    } else {
        Write-Output "计划任务 $TaskName 不存在，无需卸载"
    }
    exit 0
}

# 解析 Python（优先 py 启动器，其次 PATH 中的 python）
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
    Write-Error '未找到 Python（需要 py -3 或 python 可用）。请先安装 Python 3.12 并加入 PATH。'
}

if (-not (Test-Path $Script)) { Write-Error "入口脚本不存在: $Script" }
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

# 生成隐藏窗口的 cmd runner（绝对路径 + 日志重定向，避免计划任务可见窗口）
$runnerLines = @(
    '@echo off',
    "set ROOT=$Root",
    "set PY=$Py",
    'set LOG=%ROOT%\daily\logs\email-intel-review.log',
    'mkdir "%ROOT%\daily\logs" 2>nul',
    '"%PY%" -u "%ROOT%\.scripts\email-intelligence\run_email_intel.py" review --workspace "%ROOT%" >> "%LOG%" 2>&1'
)
$runnerLines | Set-Content -LiteralPath $Runner -Encoding ASCII

# 09:30 周一~六；错过则补跑；最长 2 小时；同一时间不重复启动
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday,Saturday -At 09:30
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 2) -MultipleInstances IgnoreNew
$Action = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument ('/c ""{0}""' -f $Runner) -WorkingDirectory $Root
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description 'Email Intelligence 每日 review：扫描邮件、生成 brief/panel（09:30 周一~六）' -Force | Out-Null

Write-Output "已安装计划任务 $TaskName（09:30，周一~六）"
Write-Output "入口：$Runner"
Write-Output "日志：$LogDir\email-intel-review.log"
Write-Output "手动触发：Start-ScheduledTask -TaskName $TaskName"
