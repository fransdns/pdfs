@echo off
title Creador de Instalador Wizard - Editor de Boletas PDF
cd /d "%~dp0"

echo ================================================================
echo   CREADOR DE INSTALADOR PROFESIONAL WIZARD (Windows 11 / 10)
echo ================================================================
echo.

:: Detectar ejecutable de Python
set "PYTHON_EXE="

python -c "import sys; print(sys.version)" >nul 2>&1
if %errorlevel% equ 0 set "PYTHON_EXE=python"

if not defined PYTHON_EXE (
    py -c "import sys; print(sys.version)" >nul 2>&1
    if %errorlevel% equ 0 set "PYTHON_EXE=py"
)

if not defined PYTHON_EXE (
    for /d %%D in ("%LocalAppData%\Programs\Python\Python*") do (
        if exist "%%D\python.exe" set "PYTHON_EXE=%%D\python.exe"
    )
)
if not defined PYTHON_EXE (
    for /d %%D in ("%ProgramFiles%\Python*") do (
        if exist "%%D\python.exe" set "PYTHON_EXE=%%D\python.exe"
    )
)

if not defined PYTHON_EXE (
    echo [ERROR] No se encontro Python instalado en esta laptop.
    echo.
    echo Para solucionarlo:
    echo  1. Ve a: https://www.python.org/downloads/
    echo  2. Descarga e instala Python
    echo  3. IMPORTANTE: Marca la casilla "[X] Add python.exe to PATH"
    echo  4. Vuelve a ejecutar este archivo.
    echo.
    pause
    exit /b 1
)

echo [INFO] Python detectado: %PYTHON_EXE%

:: 0. Verificar e instalar GTK3 Runtime (requerido para compilar WeasyPrint en Windows)
set "GTK_BIN="
if exist "C:\Program Files\GTK3-Runtime Win64\bin\libgobject-2.0-0.dll" set "GTK_BIN=C:\Program Files\GTK3-Runtime Win64\bin"
if not defined GTK_BIN if exist "C:\Program Files (x86)\GTK3-Runtime Win64\bin\libgobject-2.0-0.dll" set "GTK_BIN=C:\Program Files (x86)\GTK3-Runtime Win64\bin"

if not defined GTK_BIN (
    echo.
    echo ================================================================
    echo   [ACCION REQUERIDA] Falta GTK3 Runtime en esta laptop
    echo ================================================================
    echo   WeasyPrint requiere las librerias nativas de GTK3 (Pango y Cairo)
    echo   para generar PDFs. Se necesita instalarlo UNA SOLA VEZ en esta
    echo   laptop de compilacion (luego PyInstaller las empaqueta dentro del
    echo   instalador final, por lo que tu cliente NO tendra que instalarlo).
    echo.
    echo   Descargando instalador de GTK3 Runtime automaticamente...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object Net.WebClient).DownloadFile('https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases/download/2022-01-04/gtk3-runtime-3.24.31-2022-01-04-ts-win64.exe', 'gtk3_installer.exe')"
    
    if exist "gtk3_installer.exe" (
        echo.
        echo   [INFO] Se abrira el instalador de GTK3.
        echo   Por favor dale 'Siguiente', 'Instalar' y 'Finalizar'.
        start /wait gtk3_installer.exe
        del /f /q "gtk3_installer.exe" >nul 2>&1
    ) else (
        echo   [AVISO] No se pudo descargar automaticamente.
        echo   Por favor descargalo manualmente desde este enlace:
        echo   https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases/download/2022-01-04/gtk3-runtime-3.24.31-2022-01-04-ts-win64.exe
        pause
    )

    if exist "C:\Program Files\GTK3-Runtime Win64\bin\libgobject-2.0-0.dll" (
        set "GTK_BIN=C:\Program Files\GTK3-Runtime Win64\bin"
    ) else (
        echo.
        echo [ERROR] GTK3 aun no se detecta. Por favor completa su instalacion y vuelve a ejecutar.
        pause
        exit /b 1
    )
)

echo [INFO] GTK3 detectado en: %GTK_BIN%
echo.

:: 1. Instalar requerimientos y PyInstaller
echo [Paso 1/3] Verificando entorno de compilacion de Python...
%PYTHON_EXE% -m pip install --upgrade pip
%PYTHON_EXE% -m pip install -r requirements.txt
%PYTHON_EXE% -m pip install pyinstaller

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] No se pudieron verificar las librerias de Python.
    pause
    exit /b %errorlevel%
)

:: 2. Compilar aplicacion en modo carpeta optimizada (--onedir) con todas las DLLs de GTK3 empaquetadas
echo.
echo [Paso 2/3] Compilando la aplicacion y empaquetando librerias graficas...
echo           (Por favor espera un momento...)
echo.

if exist "dist\EditorBoletasPDF" rmdir /s /q "dist\EditorBoletasPDF"

%PYTHON_EXE% -m PyInstaller --noconfirm --clean ^
    --name "EditorBoletasPDF" ^
    --windowed ^
    --onedir ^
    --add-data "invoice_template.html;." ^
    --add-data "qr_code.png;." ^
    --add-binary "%GTK_BIN%\*.dll;." ^
    --collect-all weasyprint ^
    --collect-all pdfplumber ^
    gui_app.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Fallo la compilacion con PyInstaller.
    pause
    exit /b %errorlevel%
)

:: Asegurar copias de seguridad de las DLLs en las rutas internas
echo [INFO] Asegurando DLLs de soporte en el paquete distribuible...
xcopy /y /q "%GTK_BIN%\*.dll" "dist\EditorBoletasPDF\" >nul 2>&1
if exist "dist\EditorBoletasPDF\_internal" (
    xcopy /y /q "%GTK_BIN%\*.dll" "dist\EditorBoletasPDF\_internal\" >nul 2>&1
)

:: 3. Generar instalador con Inno Setup (ISCC)
echo.
echo [Paso 3/3] Buscando Inno Setup Compiler (ISCC)...

set "ISCC="
:: Probar comando en PATH
where iscc >nul 2>&1 && for /f "delims=" %%I in ('where iscc') do set "ISCC=%%I"

:: Rutas estándar comunes
if not defined ISCC if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%LocalAppData%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles(x86)%\Inno Setup 5\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 5\ISCC.exe"

:: Buscar en el Registro de Windows
if not defined ISCC (
    for /f "tokens=2*" %%A in ('reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1" /v "InstallLocation" 2^>nul') do (
        if exist "%%B\ISCC.exe" set "ISCC=%%B\ISCC.exe"
    )
)
if not defined ISCC (
    for /f "tokens=2*" %%A in ('reg query "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1" /v "InstallLocation" 2^>nul') do (
        if exist "%%B\ISCC.exe" set "ISCC=%%B\ISCC.exe"
    )
)

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
        echo   Este instalador contiene TODO (Python, interfaz, Weasyprint y
        echo   todas las DLLs graficas). Tu cliente NO necesita instalar nada!
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
