@echo off
for /f "delims=" %%i in ('python3 "C:\Users\kazuy\Projects\auto-classify\run_classify.py"') do (
    powershell.exe -NoProfile -EncodedCommand %%i
)
