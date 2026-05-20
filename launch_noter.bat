@echo off
chcp 65001 >nul 2>&1
title PDF笔记生成器

:: 设置工作目录为脚本所在位置
cd /d "%~dp0"

:: 设置 Python 编码
set PYTHONIOENCODING=utf-8

:: 检查 Python 是否存在
if not exist "C:\Users\ASUS\AppData\Local\Programs\Python\Python313\pythonw.exe" (
    echo [错误] 找不到 Python，请先安装 Python 3.13
    pause
    exit /b 1
)

:: 启动 GUI（使用 pythonw.exe 避免黑窗口）
start "" /B "C:\Users\ASUS\AppData\Local\Programs\Python\Python313\pythonw.exe" "%~dp0gui_launcher.py"
