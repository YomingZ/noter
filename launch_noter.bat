@echo off
chcp 65001 >nul 2>&1
title PDF笔记生成器
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8

:: 1. 优先使用虚拟环境中的 Python
if exist "venv\Scripts\pythonw.exe" (
    start "" /B "venv\Scripts\pythonw.exe" "gui_launcher.py"
    exit /b 0
)

:: 2. 从 PATH 中查找 pythonw.exe
set "PYTHONW="
for %%X in (pythonw.exe) do set "PYTHONW=%%~$PATH:X"
if defined PYTHONW (
    start "" /B "%PYTHONW%" "gui_launcher.py"
    exit /b 0
)

:: 3. 从 PATH 中查找 python.exe
set "PYTHON="
for %%X in (python.exe) do set "PYTHON=%%~$PATH:X"
if defined PYTHON (
    start "" /B "%PYTHON%" "gui_launcher.py"
    exit /b 0
)

:: 4. 全部失败
echo [错误] 找不到 Python 环境。
echo 请双击 install.bat 完成安装。
pause
exit /b 1
