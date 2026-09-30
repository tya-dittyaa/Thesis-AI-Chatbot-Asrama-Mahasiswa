@echo off
echo Starting Binus Square AI Virtual Receptionist Demo...
cd /d "%~dp0\.."
call venv\Scripts\activate
streamlit run demo_app\app.py
pause
