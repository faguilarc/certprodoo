@echo off
title Reiniciar Servicio Odoo 14
color 0A

echo ==========================================
echo   Reiniciando servicio: odoo-server-14.0
echo ==========================================
echo.

echo [1/3] Deteniendo el servicio...
net stop "odoo-server-14.0"
if %errorlevel% neq 0 (
    echo ERROR: No se pudo detener el servicio. Asegurate de tener permisos de administrador.
    pause
    exit /b
)

echo [2/3] Esperando 2 segundos...
timeout /t 2 /nobreak >nul

echo [3/3] Iniciando el servicio...
net start "odoo-server-14.0"
if %errorlevel% neq 0 (
    echo ERROR: No se pudo iniciar el servicio.
    pause
    exit /b
)

echo.
echo ==========================================
echo   Servicio reiniciado correctamente
echo ==========================================
pause