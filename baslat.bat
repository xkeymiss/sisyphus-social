@echo off
title Sisyphus Social
cls
echo ======================================================
echo   SISYPHUS SOCIAL - Baslatiliyor...
echo ======================================================
echo.
cd /d "%~dp0"

echo [1/2] Eski oturumlar temizleniyor (Port 5000)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo [2/2] Sisyphus Social baslatiliyor ve tarayici aciliyor...
echo.
py run.py

pause
