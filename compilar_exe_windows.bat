@echo off
title Compilador a .EXE - Editor de Boletas PDF
cd /d "%~dp0"

echo ================================================================
echo   COMPILADOR AUTOMATICO A .EXE (Editor de Boletas PDF)
echo ================================================================
echo.
echo Este script creara un archivo .EXE independiente y listo para usar
echo que podras entregar directamente al usuario final.
echo.

:: 1. Verificar instalacion de dependencias y PyInstaller
echo [1/3] Verificando e instalando PyInstaller y requerimientos...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Hubo un problema al preparar las dependencias de Python.
    pause
    exit /b %errorlevel%
)

:: 2. Compilar con PyInstaller en un unico .EXE
echo.
echo [2/3] Compilando la aplicacion en un unico .EXE portable...
echo       (Esto puede tardar un par de minutos, por favor espera...)
echo.

python -m PyInstaller --noconfirm --clean ^
    --name "EditorBoletasPDF" ^
    --windowed ^
    --onefile ^
    --add-data "invoice_template.html;." ^
    --collect-all weasyprint ^
    --collect-all pdfplumber ^
    gui_app.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Fallo la compilacion con PyInstaller.
    pause
    exit /b %errorlevel%
)

:: 3. Confirmacion de finalizacion
echo.
echo ================================================================
echo   [EXITO] Compilacion completada satisfactoriamente!
echo.
echo   Tu archivo ejecutable final esta en:
echo   dist\EditorBoletasPDF.exe
echo.
echo   Ese unico archivo .exe contiene todo (Python, interfaz, plantilla
echo   y librerias de PDF). Solo debes copiarlo y entregarlo al usuario!
echo ================================================================
echo.
pause
