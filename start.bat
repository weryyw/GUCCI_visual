@echo off
:: Переходим в папку, где лежит сам батник, чтобы пути не сбивались
cd /d "%~dp0"

:: Проверяем, существует ли папка с библиотеками
if not exist "venv\Lib\site-packages" (
    echo [ERROR] Papka venv ne naidena! Zapusti snachala ustanovku bibliotek.
    pause
    exit /b
)

echo [SYSTEM] Zapusk Minecraft Launchera...
echo [SYSTEM] Dlya otkrytiya vizualnogo menu nazhmi Right Shift v igre.

:: Задаем путь к библиотекам и запускаем Python-скрипт
set PYTHONPATH=%CD%\venv\Lib\site-packages
python minecraft_fabric_launcher.py

:: Если скрипт закроется с ошибкой, консоль не схлопнется сразу
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Skript zavershilsya s oshibkoi! Kod: %errorlevel%
    pause
)
