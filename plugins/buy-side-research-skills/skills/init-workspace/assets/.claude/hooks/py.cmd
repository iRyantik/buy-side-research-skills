@echo off
REM py.cmd — Cross-machine Python locator for Claude Code hooks
REM Tries common Python installations across machines

REM Try PATH first
python  --version >nul 2>&1 && (python  %* & exit /b 0)
python3 --version >nul 2>&1 && (python3 %* & exit /b 0)
py      --version >nul 2>&1 && (py      %* & exit /b 0)

REM Fallback: machine-specific install paths
set "FOUND="
for %%p in (
    "C:\ProgramData\anaconda3\python.exe"
    "C:\Users\%USERNAME%\anaconda3\python.exe"
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe"
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe"
    "C:\Users\%USERNAME%\.local\bin\python.exe"
) do (
    if not defined FOUND (
        if exist %%p (
            set "FOUND=%%~p"
            %%~p %*
            exit /b 0
        )
    )
)

echo [py.cmd] Python not found on this machine >&2
exit /b 1
