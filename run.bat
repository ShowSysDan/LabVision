@echo off
REM ArtsVision Monitor Dashboard - Startup Script for Windows

echo Starting ArtsVision Monitor Dashboard...
echo =========================================

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing dependencies...
pip install -q -r requirements.txt

REM Check if .env exists
if not exist ".env" (
    echo WARNING: .env file not found!
    echo Copying .env.example to .env...
    copy .env.example .env
    echo Please edit .env with your API credentials before running again.
    pause
    exit /b 1
)

REM Run the application
echo.
echo Starting server...
echo Dashboard will be available at: http://localhost:5000
echo Press Ctrl+C to stop
echo.

python app.py
pause
