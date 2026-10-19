@echo off
title SearchJobs Bot - Escucha en Tiempo Real
color 0b
echo ========================================================
echo   INICIANDO BOT DE TELEGRAM EN TIEMPO REAL
echo   Pedro Job Hunter (@UbedaBot)
echo ========================================================
echo.
cd /d "%~dp0"
py -3 src\bot_listener.py
if %ERRORLEVEL% NEQ 0 (
    "C:\Users\pubes\AppData\Local\Programs\Python\Python313\python.exe" src\bot_listener.py
)
pause
