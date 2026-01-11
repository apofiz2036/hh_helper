@echo off
chcp 65001 > nul
echo ========================================
echo      HH Helper - Парсер вакансий
echo ========================================
echo.
call venv\Scripts\activate.bat
python main.py
echo Работа завершена