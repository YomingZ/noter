@echo off
chcp 65001 >nul
cd /d "%~dp0"

:: 1. venv 优先
if exist "venv\Scripts\pythonw.exe" (
    start "" /B "venv\Scripts\pythonw.exe" gui_launcher.py
    exit /b 0
)

:: 2. 从 PATH 查找
set "PYTHONW="
for %%X in (pythonw.exe) do set "PYTHONW=%%~$PATH:X"
if defined PYTHONW (
    start "" /B "%PYTHONW%" gui_launcher.py
    exit /b 0
)

:: 3. 后备
set "PYTHON="
for %%X in (python.exe) do set "PYTHON=%%~$PATH:X"
if defined PYTHON (
    start "" /B "%PYTHON%" gui_launcher.py
    exit /b 0
)

echo [错误] 找不到 Python 环境，请运行 install.bat 安装。
pause
