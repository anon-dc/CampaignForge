@echo off
title CampaignForge v3.0 - Complete Setup
color 0A

:: Check for admin rights
net session >nul 2>&1
if errorlevel 1 (
    echo ============================================================
    echo    CampaignForge v3.0 - Administrator Required
    echo ============================================================
    echo.
    echo This application requires Administrator privileges to use port 80.
    echo.
    echo Please close this window and run as Administrator:
    echo   1. Right-click this file
    echo   2. Select "Run as administrator"
    echo.
    pause
    exit /b 1
)

:: Run the installer
call install.bat

:: Check if installation was successful
if errorlevel 1 (
    echo.
    echo [ERROR] Installation failed.
    pause
    exit /b 1
)

:: Start the application
call run.bat