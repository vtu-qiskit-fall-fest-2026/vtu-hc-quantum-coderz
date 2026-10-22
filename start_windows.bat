@echo off
cd /d "%~dp0"
python -m pip install -r requirements-classical.txt
if errorlevel 1 (
  echo Classical dependencies could not be installed. Check the Python and pip setup.
  pause
  exit /b 1
)
python -m uvicorn server:app --reload
pause

