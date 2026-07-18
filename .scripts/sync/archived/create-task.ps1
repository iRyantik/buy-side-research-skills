# Headless task creation — VBS wrapper, no window ever
$vbsPath  = "$PSScriptRoot\sync-sessions-hidden.vbs"
$psPath   = "$PSScriptRoot\sync-sessions.ps1"

# Create VBS launcher if missing
@"
' Headless launcher — runs sync-sessions.ps1 with zero UI, no flash, no window
CreateObject("WScript.Shell").Run "powershell.exe -NoLogo -ExecutionPolicy Bypass -File ""$psPath""", 0, False
"@ | Out-File -FilePath $vbsPath -Encoding ASCII

# Remove existing task if any
schtasks.exe /delete /tn "ClaudeCodeAutoSync" /f 2>&1 | Out-Null

# Create: wscript.exe runs VBS, VBS launches PowerShell hidden
$schtasksArgs = @(
    "/create",
    "/tn", "ClaudeCodeAutoSync",
    "/tr", "wscript.exe `"$vbsPath`"",
    "/sc", "minute",
    "/mo", "1",
    "/f"
)

& schtasks.exe $schtasksArgs 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    # Silent success
} else {
    Write-Host "ERROR: Failed to create sync task (code $LASTEXITCODE)" -ForegroundColor Red
}
