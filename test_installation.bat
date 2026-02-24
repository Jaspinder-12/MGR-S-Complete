@echo off

echo Testing MGR-S installation...

echo.
echo 1. Checking if MGR-S is installed in J:\MGR-S...
if not exist "J:\MGR-S\mgrs_gui.py" (
    echo MGR-S not installed in J:\MGR-S.
    echo Please install the application first.
    pause
    exit /b 1
) else (
    echo MGR-S found in J:\MGR-S.
)

echo.
echo 2. Checking if Python is installed...
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python not installed.
    echo Please install Python 3.6 or later.
    pause
    exit /b 1
) else (
    for /f "tokens=2" %%i in ('python --version') do set "PYTHON_VERSION=%%i"
    echo Python %PYTHON_VERSION% found.
)

echo.
echo 3. Testing mgrs_gui.py...
python "J:\MGR-S\mgrs_gui.py" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error running mgrs_gui.py.
    pause
    exit /b 1
) else (
    echo mgrs_gui.py is running.
)

echo.
echo All tests passed. MGR-S is correctly installed and running.
pause
