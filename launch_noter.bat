@echo off
chcp 65001 >nul 2>&1
title PDF笔记生成器
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8

set "LOG_FILE=%TEMP%\noter_launch.log"
echo [%DATE% %TIME%] Starting Noter... > "%LOG_FILE%"

:: 1. 优先使用虚拟环境中的 Python (GUI模式)
if exist "venv\Scripts\pythonw.exe" (
    echo [%DATE% %TIME%] Found pythonw.exe in venv >> "%LOG_FILE%"
    start "" "venv\Scripts\pythonw.exe" "gui_launcher.py"
    echo [%DATE% %TIME%] Launched with pythonw.exe, exit code: %ERRORLEVEL% >> "%LOG_FILE%"
    exit /b 0
)

:: 2. 从 PATH 中查找 pythonw.exe
echo [%DATE% %TIME%] venv pythonw not found, trying PATH... >> "%LOG_FILE%"
set "PYTHONW="
for %%X in (pythonw.exe) do set "PYTHONW=%%~$PATH:X"
if defined PYTHONW (
    echo [%DATE% %TIME%] Found pythonw.exe at: %PYTHONW% >> "%LOG_FILE%"
    start "" "%PYTHONW%" "gui_launcher.py"
    exit /b 0
)

:: 3. 从 PATH 中查找 python.exe (fallback)
set "PYTHON="
for %%X in (python.exe) do set "PYTHON=%%~$PATH:X"
if defined PYTHON (
    echo [%DATE% %TIME%] Found python.exe at: %PYTHON% >> "%LOG_FILE%"
    start "" "%PYTHON%" "gui_launcher.py"
    exit /b 0
)

:: 4. 全部失败
echo [%DATE% %TIME%] ERROR: No Python found! >> "%LOG_FILE%"
echo [错误] 找不到 Python 环境。
echo 请双击 install.bat 完成安装。
echo 错误日志: %LOG_FILE%
pause
exit /b 1
