@echo off
echo Installing MGR-S using Inno Setup...
"C:\Users\Jass2\AppData\Local\Programs\Inno Setup 6\ISCC.exe" mgrs_setup.iss
if %ERRORLEVEL% neq 0 (
    echo Installation failed
    pause
    exit /b %ERRORLEVEL%
)
echo Installation successful. The installer is located in Output\
pause
