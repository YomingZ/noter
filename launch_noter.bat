@echo off
chcp 65001 >nul 2>&1
cd /d "e:\noter"
set PYTHONIOENCODING=utf-8
start "" /B "C:\Users\ASUS\AppData\Local\Programs\Python\Python313\pythonw.exe" "e:\noter\gui_launcher.py"