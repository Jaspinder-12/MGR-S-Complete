@echo off
echo Testing MGR-S UI...
python test_ui.py
if %ERRORLEVEL% neq 0 (
    echo UI test failed
    pause
    exit /b %ERRORLEVEL%
)
echo UI test passed
pause
