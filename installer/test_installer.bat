@echo off
echo Testing MGR-S Installer...

REM Check if Inno Setup is installed
where ISCC >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Inno Setup not found. Please install Inno Setup 6 from http://www.jrsoftware.org/isdl.php
    pause
    exit /b 1
)

REM Build the installer
call install.bat
if %ERRORLEVEL% neq 0 (
    echo Installation failed
    pause
    exit /b %ERRORLEVEL%
)

echo Installer created successfully in Output\
pause
