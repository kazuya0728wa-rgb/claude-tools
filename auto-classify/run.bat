@echo off
rem DownloadAutoClassify entry point. ASCII only / CRLF. Do not add non-ASCII text.
rem Root cause fix 2026-07-07: bare python3 (MSIX alias) fails via Task Scheduler cmd path.
set "TOOLDIR=C:\Users\kazuy\.claude\tools\auto-classify"
set "PYEXE=C:\Users\kazuy\AppData\Local\Microsoft\WindowsApps\python.exe"
set "RUNLOG=%TOOLDIR%\logs\run.log"
if not exist "%TOOLDIR%\logs" mkdir "%TOOLDIR%\logs"
for %%A in ("%RUNLOG%") do if %%~zA GTR 1048576 move /y "%RUNLOG%" "%RUNLOG%.1" > nul
set "PYTHONUTF8=1"
echo [%date% %time%] run.bat start >> "%RUNLOG%"
"%PYEXE%" "%TOOLDIR%\run_main.py" >> "%RUNLOG%" 2>&1
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" goto :fail
echo [%date% %time%] run.bat done exit 0 >> "%RUNLOG%"
exit /b 0
:fail
echo [%date% %time%] run.bat FAILED errorlevel %RC% >> "%RUNLOG%"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%TOOLDIR%\notify_fail.ps1" -Task "DownloadAutoClassify" -Detail "run.bat errorlevel %RC%" >> "%RUNLOG%" 2>&1
exit /b 1
