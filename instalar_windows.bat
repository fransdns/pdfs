@echo off
title Instalador de Dependencias - Editor de Boletas PDF
cd /d "%~dp0"

echo ========================================================
echo   Instalando dependencias para Editor de Boletas PDF
echo ========================================================
echo.

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
if %errorlevel% equ 0 (
    echo ========================================================
    echo   [EXITO] Dependencias instaladas correctamente.
    echo   Ahora puedes hacer doble clic en 'run_gui.bat'
    echo ========================================================
) else (
    echo ========================================================
    echo   [AVISO] Hubo un problema al instalar las dependencias.
    echo   Revisa tu conexion o permisos de administrador.
    echo ========================================================
)
echo.
pause
