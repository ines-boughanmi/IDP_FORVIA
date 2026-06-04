@echo off
REM Quick Start Script for IDP Monitoring Django Application
REM This script sets up and runs the Django development server

echo ========================================
echo IDP Monitoring - Django Application
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Install/upgrade dependencies
echo Installing dependencies...
pip install -q -r requirements.txt
echo.

REM Run migrations
echo Applying database migrations...
python manage.py migrate --noinput > nul
echo.

REM Start development server
echo ========================================
echo Starting Django development server...
echo ========================================
echo.
echo Server will be available at: http://127.0.0.1:8000/
echo Admin panel available at: http://127.0.0.1:8000/admin/
echo.
echo Press Ctrl+C to stop the server
echo.

python manage.py runserver
