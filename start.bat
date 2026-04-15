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
echo   Sitemap:            http://localhost:3000/sitemap.xml
echo   WebSocket:          ws://localhost:3000/ws/pedidos
echo.
echo   Presiona Ctrl+C para detener el servidor.
echo   ============================================
echo.
cd /d "%~dp0"
python run.py
pause
pause
