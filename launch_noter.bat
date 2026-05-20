@echo off
chcp 65001 >nul 2>&1
title PDF笔记生成器

:: 设置工作目录为脚本所在位置
cd /d "%~dp0"

:: 设置 Python 编码
set PYTHONIOENCODING=utf-8

:: 1. 优先使用虚拟环境中的 Python
if exist "venv\Scripts\pythonw.exe" (
    start "" /B "venv\Scripts\pythonw.exe" "%~dp0gui_launcher.py"
    exit /b 0
)

:: 2. 尝试从 PATH 中查找 pythonw
for %%i in (pythonw.exe) do set "PYTHONW_PATH=%%~$PATH:i"
if defined PYTHONW_PATH (
    start "" /B "%PYTHONW_PATH%" "%~dp0gui_launcher.py"
    exit /b 0
)

:: 3. 尝试 python.exe 作为后备
for %%i in (python.exe) do set "PYTHON_PATH=%%~$PATH:i"
if defined PYTHON_PATH (
    start "" /B "%PYTHON_PATH%" "%~dp0gui_launcher.py"
    exit /b 0
)

:: 4. 全部失败，提示用户
echo [错误] 找不到 Python 环境。
echo.
echo 请运行 install.bat 完成安装，或手动安装 Python 3.9+。
pause
exit /b 1
