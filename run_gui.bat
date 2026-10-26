@echo off
title Editor de Boletas PDF (Modo Grafico)
cd /d "%~dp0"

echo ========================================================
echo   Iniciando Editor y Regenerador de Boletas PDF...
echo ========================================================

python gui_app.py

if %errorlevel% neq 0 (
    echo.
    echo Ocurrio un error al ejecutar la aplicacion.
    echo Asegurate de haber instalado las dependencias con:
    echo     pip install -r requirements.txt
    echo.
    pause
)
