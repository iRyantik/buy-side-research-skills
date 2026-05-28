@echo off
setlocal

set "SCRIPT_PATH=%~1"
if "%SCRIPT_PATH%"=="" (
    1>&2 echo Blocked by hook launcher: missing target .ps1 path.
    exit /b 64
)
shift

set "PS_EXE="
if exist "%ProgramFiles%\PowerShell\7\pwsh.exe" set "PS_EXE=%ProgramFiles%\PowerShell\7\pwsh.exe"
if not defined PS_EXE if exist "%ProgramW6432%\PowerShell\7\pwsh.exe" set "PS_EXE=%ProgramW6432%\PowerShell\7\pwsh.exe"
if not defined PS_EXE for %%I in (pwsh.exe) do if not "%%~$PATH:I"=="" set "PS_EXE=%%~$PATH:I"

if not defined PS_EXE (
    if exist "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" set "PS_EXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
)

if not defined PS_EXE (
    for %%I in (powershell.exe) do if not "%%~$PATH:I"=="" set "PS_EXE=%%~$PATH:I"
)

if not defined PS_EXE (
    1>&2 echo Blocked by hook launcher: unable to locate PowerShell. Install PowerShell 7 ^(`pwsh`^) or ensure Windows PowerShell is available on PATH.
    exit /b 2
)

"%PS_EXE%" -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_PATH%" %*
exit /b %ERRORLEVEL%
