@echo off
schtasks /create /tn "ClaudeCodeAutoSync" /tr "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File \"S:\.scripts\sync\sync-sessions.ps1\"" /sc minute /mo 10 /f
echo Exit code: %ERRORLEVEL%
pause
