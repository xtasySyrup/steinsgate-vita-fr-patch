@echo off
chcp 65001 > nul
cd /d "%~dp0"
where py > nul 2>&1
if %errorlevel%==0 (
    py -3 appliquer_patch.py %*
) else (
    python appliquer_patch.py %*
)
if errorlevel 9009 echo Python 3 est introuvable. Installez-le depuis https://www.python.org/downloads/
pause
