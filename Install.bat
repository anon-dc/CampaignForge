@echo off
title CampaignForge v3.0 - Installer
color 0A

echo ============================================================
echo    CampaignForge v3.0 - Installation
echo ============================================================
echo.

:: Check Python
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed.
    echo.
    echo Download Python 3.7+ from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH"
    pause
    exit /b 1
)
python --version
echo.

:: Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
echo.

:: Install dependencies
echo Installing dependencies...
if exist requirements.txt (
    python -m pip install -r requirements.txt
) else (
    python -m pip install Flask==2.3.3 flask-cors==4.0.1
)
echo.

:: Create directories
echo Creating directories...
if not exist templates mkdir templates
if not exist uploads mkdir uploads
if not exist reports mkdir reports
echo.

:: Create requirements.txt if missing
if not exist requirements.txt (
    echo Creating requirements.txt...
    echo Flask==2.3.3 > requirements.txt
    echo flask-cors==4.0.1 >> requirements.txt
    echo.
)

:: Check template files
echo Checking template files...
if not exist templates\index.html echo [WARNING] templates/index.html missing
if not exist templates\app.html echo [WARNING] templates/app.html missing
if not exist templates\tracking.html echo [WARNING] templates/tracking.html missing
echo.

echo ============================================================
echo    Installation Complete!
echo ============================================================
echo.
echo To start the application, run:
echo   start.bat
echo.
pause