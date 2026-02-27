@echo off
setlocal
chcp 65001 >nul

cd /d "%~dp0"
echo [INFO] Minecraft local panel launcher

if not exist ".venv\Scripts\python.exe" (
  echo [INFO] Creating virtual environment...
  py -3 -m venv .venv
)

call ".venv\Scripts\activate.bat"

python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt

if errorlevel 1 (
  echo [ERROR] Failed to install dependencies.
  pause
  exit /b 1
)

echo [INFO] Starting main.py...
python main.py

pause
