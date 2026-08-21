@echo off
title CampaignForge v3.0
color 0A

:: Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found. Please install Python 3.7+.
    pause
    exit /b 1
)

:: Install dependencies
if exist requirements.txt (
    python -m pip install -r requirements.txt >nul 2>&1
) else (
    python -m pip install Flask==2.3.3 flask-cors==4.0.1 >nul 2>&1
)

:: Create directories
if not exist templates mkdir templates
if not exist uploads mkdir uploads
if not exist reports mkdir reports

:: Start the application
echo Starting CampaignForge v3.0...
echo Dashboard: http://localhost:80/app
start python app.py

timeout /t 2 >nul
echo Application started in background.
echo.
pause