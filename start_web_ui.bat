@echo off
REM Azure Document Translation - Start Web UI

echo ============================================================
echo Azure Document Translation Web UI
echo ============================================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo No virtual environment found. Creating one...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if requirements are installed
echo Checking dependencies...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt
    echo.
)

REM Check if .env exists
if not exist ".env" (
    echo WARNING: .env file not found!
    echo Please copy .env.template to .env and add your Azure credentials.
    echo.
    pause
    exit /b 1
)

REM Start the application
echo Starting web server...
echo.
echo ============================================================
echo Web UI will be available at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo ============================================================
echo.

python app.py

pause
