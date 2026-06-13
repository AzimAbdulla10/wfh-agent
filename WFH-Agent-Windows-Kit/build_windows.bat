@echo off
echo ========================================
echo WFH Agent - Windows Build Script
echo ========================================
echo.

echo 1. Installing required libraries...
pip install PySide6 requests pyinstaller

echo.
echo 2. Building standalone executable...
pyinstaller --onefile --noconsole --name wfh-agent main.py

echo.
echo ========================================
echo DONE!
echo Your file is in the 'dist' folder.
echo ========================================
pause
