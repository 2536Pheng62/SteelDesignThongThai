@echo off
echo ==================================================
echo Steel Structure Design App Setup
echo ==================================================
echo.

if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

echo Activating virtual environment and installing dependencies...
call .\.venv\Scripts\activate.bat
pip install -r requirements.txt

echo.
echo ==================================================
echo Setup Complete! Starting Application...
echo ==================================================
python main_app.py
pause
