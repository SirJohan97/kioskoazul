@echo off
echo.
echo   ============================================
echo    Kiosko Azul - Sistema Unificado
echo   ============================================
echo.
echo   Arrancando servidor en http://localhost:3000
echo.
echo   Pagina principal:   http://localhost:3000
echo   Menu:               http://localhost:3000/menu.html
echo   Panel Admin:        http://localhost:3000/admin-login.html
echo   API Docs:           http://localhost:3000/docs
echo.
echo   Presiona Ctrl+C para detener el servidor.
echo   ============================================
echo.
cd /d "%~dp0"
call .\venv\Scripts\activate.bat
python backend.py
pause
