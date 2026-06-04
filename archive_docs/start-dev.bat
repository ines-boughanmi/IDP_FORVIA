@echo off
REM IDP Analytics Platform - Development Start Script (Windows)
REM Run both backend and frontend servers with one command

echo.
echo ========================================
echo IDP Analytics Platform - Starting...
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed. Please install Python 3.8+
    pause
    exit /b 1
)

REM Check if Node is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo Error: Node.js is not installed. Please install Node.js 16+
    pause
    exit /b 1
)

echo Python found: 
python --version
echo Node found:
node --version
echo.

REM Start backend in new window
echo Starting Django backend...
start cmd /k cd backend ^& python manage.py runserver
echo Backend is starting...
timeout /t 3 /nobreak
echo.

REM Start frontend in new window
echo Starting React frontend...
start cmd /k cd frontend ^& npm run dev
echo Frontend is starting...
echo.

echo ========================================
echo Both services should be opening...
echo ========================================
echo.
echo Frontend: http://localhost:5173
echo Backend API: http://localhost:8000/api
echo Admin: http://localhost:8000/admin
echo.
echo Close the terminal windows to stop services.
pause
