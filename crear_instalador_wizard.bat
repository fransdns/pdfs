@echo off
title Creador de Instalador Wizard - Editor de Boletas PDF
cd /d "%~dp0"

echo ================================================================
echo   CREADOR DE INSTALADOR PROFESIONAL WIZARD (Windows 11 / 10)
echo ================================================================
echo.
echo Este proceso creara un unico instalador 'Setup.exe' comercial
echo con asistente de instalacion ("Siguiente > Instalar"), icono en el
echo Escritorio y desinstalador limpio para tu cliente.
echo.

:: 1. Instalar requerimientos y PyInstaller
echo [Paso 1/3] Verificando entorno de compilacion de Python...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] No se pudieron verificar las librerias de Python.
    pause
    exit /b %errorlevel%
)

:: 2. Compilar aplicacion en modo carpeta optimizada (--onedir)
echo.
echo [Paso 2/3] Compilando la aplicacion para el instalador (PyInstaller onedir)...
echo           (Por favor espera un par de minutos...)
echo.

if exist "dist\EditorBoletasPDF" rmdir /s /q "dist\EditorBoletasPDF"

python -m PyInstaller --noconfirm --clean ^
    --name "EditorBoletasPDF" ^
    --windowed ^
    --onedir ^
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

:: 3. Generar instalador con Inno Setup (ISCC)
echo.
echo [Paso 3/3] Buscando Inno Setup Compiler (ISCC)...

set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist "%LocalAppData%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"

if defined ISCC (
    echo [INFO] Inno Setup encontrado en: "%ISCC%"
    echo [INFO] Generando archivo de instalacion profesional...
    "%ISCC%" "instalador_config.iss"
    if %errorlevel% equ 0 (
        echo.
        echo ================================================================
        echo   [EXITO TOTAL] Instalador Wizard generado exitosamente!
        echo.
        echo   Ubicacion del instalador listo para entregar a tu cliente:
        echo   dist_instalador\Instalador_EditorBoletas_Setup.exe
        echo.
        echo   Ese unico archivo .exe lo copias y se lo entregas a tu cliente.
        echo   Tu cliente le hara doble clic, se abrira el asistente en espanol
        echo   y le dejara el programa instalado con acceso en su Escritorio.
        echo ================================================================
        echo.
    ) else (
        echo [ERROR] Ocurrio un fallo al compilar con Inno Setup.
    )
) else (
    echo.
    echo ================================================================
    echo   [AVISO] Los archivos del programa fueron preparados con exito,
    echo   pero Inno Setup 6 aun no esta instalado en esta laptop.
    echo.
    echo   Para obtener el archivo final 'Instalador_EditorBoletas_Setup.exe':
    echo   1. Descarga Inno Setup gratis (5 MB) desde:
    echo      https://jrsoftware.org/isdl.php (clic en 'Inno Setup 6')
    echo   2. Instalalo (solo toma 30 segundos).
    echo   3. Vuelve a ejecutar este archivo 'crear_instalador_wizard.bat'
    echo      o haz clic derecho en 'instalador_config.iss' y elige 'Compile'.
    echo ================================================================
    echo.
)

pause
