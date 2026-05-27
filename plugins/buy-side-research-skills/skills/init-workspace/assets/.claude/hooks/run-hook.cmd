@echo off
setlocal

set "SCRIPT_PATH=%~1"
if "%SCRIPT_PATH%"=="" (
    1>&2 echo Blocked by hook launcher: missing target hook path.
    exit /b 64
)
shift

:: Prefer Python version if available (cross-platform)
set "PY_PATH=%SCRIPT_PATH:.ps1=.py%"
if exist "%PY_PATH%" (
    for %%I in (python3.exe) do if not "%%~$PATH:I"=="" set "HAS_PYTHON=1"
    if not defined HAS_PYTHON for %%I in (python.exe) do if not "%%~$PATH:I"=="" set "HAS_PYTHON=1"
    if defined HAS_PYTHON (
        python "%PY_PATH%" %*
        exit /b %ERRORLEVEL%
    )
)

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
    1>&2 echo Blocked by hook launcher: unable to locate python or powershell. Install Python 3.10+ or PowerShell to enable workspace hooks.
    exit /b 2
)

"%PS_EXE%" -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_PATH%" %*
exit /b %ERRORLEVEL%
