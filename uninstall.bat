@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================================
:: PDF 备考笔记生成器 - Windows 卸载脚本
:: ============================================================

title PDF 备考笔记生成器 - 卸载向导
color 0C

:: 获取脚本目录
set "INSTALL_DIR=%~dp0"
cd /d "%INSTALL_DIR%"

cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║       📚 PDF 备考笔记生成器 - 卸载向导                    ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

:: 确认卸载
echo [警告] 此操作将：
echo.
echo        - 删除虚拟环境 (venv/)
echo        - 删除输出目录 (notes/)
echo        - 删除缓存文件 (.cache/, __pycache__/)
echo        - 删除桌面快捷方式
echo        - 删除编译文件 (*.pyc, *.pyo)
echo.
echo        [保留] 以下文件将被保留：
echo        - 配置文件 (.env, config/)
echo        - 生成的笔记 (可手动删除 notes/)
echo        - 安装脚本和源代码
echo.

set /p "CONFIRM=确定要卸载吗？(yes/N): "
if /i not "!CONFIRM!"=="yes" (
    echo.
    echo 已取消卸载操作。
    pause
    exit /b 0
)

echo.
echo ════════════════════════════════════════════════════════════
echo 开始卸载...
echo ════════════════════════════════════════════════════════════
echo.

:: 1. 删除虚拟环境
if exist "venv" (
    echo [1/5] 删除虚拟环境...
    rmdir /s /q venv
    echo       [✓] venv 已删除
) else (
    echo [1/5] 虚拟环境不存在，跳过
)

:: 2. 删除缓存
echo [2/5] 删除缓存文件...
if exist "output\.cache" rmdir /s /q "output\.cache"
if exist "output\.stats" rmdir /s /q "output\.stats"
if exist "output\.state" rmdir /s /q "output\.state"
for /d /r %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
del /s /q *.pyc >nul 2>&1
del /s /q *.pyo >nul 2>&1
echo       [✓] 缓存已清理

:: 3. 删除构建文件
echo [3/5] 删除构建文件...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "*.egg-info" rmdir /s /q *.egg-info
echo       [✓] 构建文件已删除

:: 4. 删除桌面快捷方式
echo [4/5] 删除桌面快捷方式...

:: 查找桌面路径
set "DESKTOP="
if exist "%USERPROFILE%\Desktop" (
    set "DESKTOP=%USERPROFILE%\Desktop"
) else if exist "%USERPROFILE%\OneDrive\Desktop" (
    set "DESKTOP=%USERPROFILE%\OneDrive\Desktop"
) else if exist "%USERPROFILE%\OneDrive\桌面" (
    set "DESKTOP=%USERPROFILE%\OneDrive\桌面"
)

if not "!DESKTOP!"=="" (
    if exist "!DESKTOP!\PDF笔记生成器.lnk" (
        del "!DESKTOP!\PDF笔记生成器.lnk"
        echo       [✓] 已删除桌面快捷方式
    )
    if exist "!DESKTOP!\PDF笔记生成器(GUI).lnk" (
        del "!DESKTOP!\PDF笔记生成器(GUI).lnk"
        echo       [✓] 已删除 GUI 快捷方式
    )
)

:: 5. 清理空目录
echo [5/5] 清理空目录...
if exist "notes" (
    dir /b notes | findstr "^" >nul
    if errorlevel 1 (
        rmdir notes
        echo       [✓] notes 目录已删除
    ) else (
        echo       [!] notes 目录不为空，已保留
    )
)

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                    ✅ 卸载完成                             ║
echo ╠════════════════════════════════════════════════════════════╣
echo ║                                                            ║
echo ║  以下文件/文件夹已保留，可手动删除：                       ║
echo ║    - .env (API 配置)                                       ║
echo ║    - config/ (配置文件)                                    ║
echo ║    - notes/ (生成的笔记，如果不为空)                       ║
echo ║    - install.bat / uninstall.bat (安装/卸载脚本)           ║
echo ║                                                            ║
echo ║  如需完全删除，请手动删除整个项目文件夹。                  ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

set /p "OPEN_DIR=是否打开项目目录？(Y/n): "
if /i not "!OPEN_DIR!"=="n" (
    explorer "!INSTALL_DIR!"
)

pause
exit /b 0
