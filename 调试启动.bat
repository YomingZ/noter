@echo off
chcp 65001 >nul
cd /d "%~dp0"

:: 1. 优先使用虚拟环境中的 Python
if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" gui_launcher.py
    if errorlevel 1 pause
    exit /b 0
)

:: 2. 尝试 python 命令
python gui_launcher.py
if errorlevel 1 (
    echo.
    echo [错误] 找不到 Python 环境。
    echo 请运行 install.bat 完成安装，或手动安装 Python 3.9+。
    pause
)
