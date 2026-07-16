# setup-autosync.ps1
# One-click setup for auto session sync. No admin required.
# Run once on each Windows machine.

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup Auto Sync" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. subst S: auto-mount at login (HKCU, no admin)
Write-Host "[1/3] subst S: auto-mount at login" -ForegroundColor Yellow
$substCmd = "subst S: `"C:\Users\$env:USERNAME\OneDrive - <CompanyName>\CC research workspace`""
Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "MapResearchDrive" -Value $substCmd
Write-Host "  done" -ForegroundColor Green

# 2. Create startup script that runs sync on login (with delay for OneDrive)
Write-Host "[2/3] Create auto-sync startup script" -ForegroundColor Yellow
$syncScriptPath = "$PSScriptRoot\sync-sessions.ps1"
$startupScript = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\ClaudeSync.cmd"

@"
@echo off
REM Wait 60s for OneDrive to finish syncing
timeout /t 60 /nobreak > nul
powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File "$syncScriptPath"
"@ | Out-File -FilePath $startupScript -Encoding ASCII

Write-Host "  done" -ForegroundColor Green

# 3. Verify
Write-Host "[3/3] Verify setup" -ForegroundColor Yellow
Write-Host "  subst S: in HKCU Run: $(if (Get-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name 'MapResearchDrive' -ErrorAction SilentlyContinue) { 'YES' } else { 'NO' })" -ForegroundColor Gray
Write-Host "  Startup script: $(if (Test-Path $startupScript) { 'YES' } else { 'NO' })" -ForegroundColor Gray

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "What happens automatically:" -ForegroundColor White
Write-Host "  1. Login -> S: mounts (subst)" -ForegroundColor Gray
Write-Host "  2. Login -> 60s delay -> sessions sync (pull + push)" -ForegroundColor Gray
Write-Host ""
Write-Host "Manual sync before switching PC now:" -ForegroundColor Yellow
Write-Host "  .\.scripts\sync\sync-sessions.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "ALWAYS open VS Code from S:\" -ForegroundColor Cyan
