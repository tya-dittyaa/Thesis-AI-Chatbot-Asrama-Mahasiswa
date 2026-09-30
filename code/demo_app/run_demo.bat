@echo off
echo Starting Binus Square AI Virtual Receptionist Demo...
cd /d "%~dp0\.."
call venv\Scripts\activate
venv\Scripts\python.exe -m streamlit run demo_app\app.py
pause
