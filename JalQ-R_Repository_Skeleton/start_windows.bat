@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo Full quantum installation failed. Try: python -m pip install -r requirements-classical.txt
  pause
  exit /b 1
)
python -m uvicorn server:app --reload
pause

