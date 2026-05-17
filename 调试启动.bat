@echo off
cd /d "%~dp0"
echo Starting GUI...
"C:\Users\ASUS\AppData\Local\Programs\Python\Python313\pythonw.exe" gui_launcher.py
if errorlevel 1 (
    echo Failed with error code %errorlevel%
    echo Trying with python.exe instead...
    "C:\Users\ASUS\AppData\Local\Programs\Python\Python313\python.exe" gui_launcher.py
)
echo Done.
pause
