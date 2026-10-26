@echo off
title Editor de Boletas PDF (Modo Consola)
cd /d "%~dp0"

echo ========================================================
echo   Editor y Regenerador de Boletas PDF (Modo Terminal)
echo ========================================================
echo.

python invoice_generator.py

if %errorlevel% neq 0 (
    echo.
    echo Ocurrio un error al ejecutar el programa.
    echo Asegurate de haber instalado las dependencias con:
    echo     pip install -r requirements.txt
    echo.
)

pause
