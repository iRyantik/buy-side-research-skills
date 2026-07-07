' Headless launcher ??? runs sync-sessions.ps1 with zero UI, no flash, no window
CreateObject("WScript.Shell").Run "powershell.exe -NoLogo -ExecutionPolicy Bypass -File ""S:\.scripts\sync\sync-sessions.ps1""", 0, False
