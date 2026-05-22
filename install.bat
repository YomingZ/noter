@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================================
:: PDF 备考笔记生成器 - Windows 安装脚本
::
:: 功能：
::   - 自动检测 Python 环境
::   - 创建虚拟环境
::   - 安装所有依赖
::   - 创建桌面快捷方式
::   - 配置文件初始化
::
:: 使用方法：双击运行此脚本
:: ============================================================

title PDF 备考笔记生成器 - 安装向导
color 0A

:: 获取脚本目录
set "INSTALL_DIR=%~dp0"
cd /d "%INSTALL_DIR%"

:: 清屏并显示欢迎信息
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║       📚 PDF 备考笔记生成器 - 安装向导                    ║
echo ║                                                            ║
echo ║       版本: 1.0.0                                          ║
echo ║       支持: Windows 10/11                                  ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

:: 步骤计数
set /a STEP=0
set /a TOTAL=6

:: ============================================================
:: 步骤 1: 检测 Python
:: ============================================================
set /a STEP+=1
echo [!STEP!/!TOTAL!] 检测 Python 环境...
echo         ─────────────────────────────────────────────

:: 检测 Python 3.9+
python --version >nul 2>&1
if errorlevel 1 (
    echo         [✗] 未检测到 Python
    echo.
    echo         请先安装 Python 3.9 或更高版本：
    echo         https://www.python.org/downloads/
    echo.
    echo         安装时请勾选 "Add Python to PATH"
    echo.
    goto :error_exit
)

:: 获取 Python 版本
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo         [✓] Python 版本: !PYTHON_VERSION!

:: 检测 pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo         [✗] pip 不可用
    goto :error_exit
)
echo         [✓] pip 已安装
echo.

:: ============================================================
:: 步骤 2: 创建虚拟环境
:: ============================================================
set /a STEP+=1
echo [!STEP!/!TOTAL!] 创建虚拟环境...
echo         ─────────────────────────────────────────────

if exist "venv" (
    echo         [!] 虚拟环境已存在
    set /p "RECREATE=        是否重新创建？(y/N): "
    if /i "!RECREATE!"=="y" (
        echo         正在删除旧的虚拟环境...
        rmdir /s /q venv
    ) else (
        echo         跳过创建步骤
        goto :skip_venv
    )
)

echo         正在创建虚拟环境...
python -m venv venv

if not exist "venv\Scripts\activate.bat" (
    echo         [✗] 虚拟环境创建失败
    goto :error_exit
)

echo         [✓] 虚拟环境创建成功

:skip_venv
echo.

:: ============================================================
:: 步骤 3: 安装依赖
:: ============================================================
set /a STEP+=1
echo [!STEP!/!TOTAL!] 安装依赖包...
echo         ─────────────────────────────────────────────

:: 激活虚拟环境
call venv\Scripts\activate.bat

:: 升级 pip
echo         升级 pip...
python -m pip install --upgrade pip -q

:: 安装依赖
echo         安装核心依赖...
pip install -e . -q

if errorlevel 1 (
    echo         [✗] 依赖安装失败
    echo         尝试单独安装...
    pip install pdfplumber python-docx openai anthropic typer pydantic pydantic-settings python-dotenv pyyaml rich tqdm
)

echo         [✓] 依赖安装完成
echo.

:: ============================================================
:: 步骤 4: 配置文件初始化
:: ============================================================
set /a STEP+=1
echo [!STEP!/!TOTAL!] 配置文件初始化...
echo         ─────────────────────────────────────────────

:: 创建 .env 文件
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo         [✓] 已创建 .env 配置文件
    ) else (
        echo         [!] 未找到 .env.example，跳过
    )
) else (
    echo         [!] .env 文件已存在
)

:: 创建输出目录
if not exist "notes" mkdir notes
echo         [✓] 已创建 notes 输出目录

:: 复制配置文件
if not exist "config\settings.yaml" (
    if exist "config\settings.yaml.example" (
        copy config\settings.yaml.example config\settings.yaml >nul
        echo         [✓] 已创建 settings.yaml
    )
)
echo.

:: ============================================================
:: 步骤 5: 创建桌面快捷方式
:: ============================================================
set /a STEP+=1
echo [!STEP!/!TOTAL!] 创建桌面快捷方式...
echo         ─────────────────────────────────────────────

:: 查找桌面路径
set "DESKTOP="
if exist "%USERPROFILE%\Desktop" (
    set "DESKTOP=%USERPROFILE%\Desktop"
) else if exist "%USERPROFILE%\OneDrive\Desktop" (
    set "DESKTOP=%USERPROFILE%\OneDrive\Desktop"
) else if exist "%USERPROFILE%\OneDrive\桌面" (
    set "DESKTOP=%USERPROFILE%\OneDrive\桌面"
)

if "!DESKTOP!"=="" (
    echo         [!] 无法找到桌面路径
    goto :skip_shortcut
)

:: 使用 PowerShell 创建快捷方式
echo         正在创建快捷方式...

:: CLI 快捷方式
set "SHORTCUT_PATH=!DESKTOP!\PDF笔记生成器.lnk"
powershell -Command ^
    "$ws = New-Object -ComObject WScript.Shell; ^
     $s = $ws.CreateShortcut('!SHORTCUT_PATH!'); ^
     $s.TargetPath = '!INSTALL_DIR!一键生成笔记.bat'; ^
     $s.WorkingDirectory = '!INSTALL_DIR!'; ^
     $s.Description = 'PDF备考笔记生成器'; ^
     $s.Save()"

echo         [✓] 已创建桌面快捷方式: PDF笔记生成器

:: GUI 快捷方式（如果存在）
if exist "gui_launcher.py" (
    set "GUI_SHORTCUT=!DESKTOP!\PDF笔记生成器(GUI).lnk"
    powershell -Command ^
        "$ws = New-Object -ComObject WScript.Shell; ^
         $s = $ws.CreateShortcut('!GUI_SHORTCUT!'); ^
         $s.TargetPath = '!INSTALL_DIR!launch_noter.bat'; ^
         $s.WorkingDirectory = '!INSTALL_DIR!'; ^
         $s.Description = 'PDF备考笔记生成器 GUI版'; ^
         $s.Save()"
    echo         [✓] 已创建 GUI 快捷方式
)

:skip_shortcut
echo.

:: ============================================================
:: 步骤 6: 安装完成
:: ============================================================
set /a STEP+=1
echo [!STEP!/!TOTAL!] 安装完成！
echo         ─────────────────────────────────────────────
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                    🎉 安装成功！                           ║
echo ╠════════════════════════════════════════════════════════════╣
echo ║                                                            ║
echo ║  安装位置: !INSTALL_DIR!                                   ║
echo ║                                                            ║
echo ╠════════════════════════════════════════════════════════════╣
echo ║                      使用方法                              ║
echo ╠════════════════════════════════════════════════════════════╣
echo ║                                                            ║
echo ║  方式一（拖拽模式）：                                      ║
echo ║    1. 将 PDF 文件拖到桌面的「PDF笔记生成器」图标上        ║
echo ║    2. 等待处理完成，笔记保存在 notes 文件夹               ║
echo ║                                                            ║
echo ║  方式二（GUI 模式）：                                      ║
echo ║    1. 双击桌面「PDF笔记生成器(GUI)」图标                  ║
echo ║    2. 选择 PDF 文件，点击「开始生成」                      ║
echo ║                                                            ║
echo ║  方式三（命令行）：                                        ║
echo ║    pdf-summarizer process your_file.pdf -p kimi          ║
echo ║                                                            ║
echo ╠════════════════════════════════════════════════════════════╣
echo ║                    ⚠️ 重要提示                             ║
echo ╠════════════════════════════════════════════════════════════╣
echo ║                                                            ║
echo ║  首次使用请配置 API 密钥：                                 ║
echo ║                                                            ║
echo ║    1. 打开项目目录中的 .env 文件                          ║
echo ║    2. 填入你的 Kimi/OpenAI/Claude API Key                  ║
echo ║    3. 或运行: pdf-summarizer config --setup               ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

:: 询问是否配置 API
set /p "CONFIG_API=是否现在配置 API 密钥？(Y/n): "
if /i not "!CONFIG_API!"=="n" (
    echo.
    echo 正在启动配置向导...
    pdf-summarizer config --setup
)

:: 询问是否配置 Obsidian Vault 路径
echo.
set /p "CONFIG_VAULT=是否配置 Obsidian Vault 路径？(y/N): "
if /i "!CONFIG_VAULT!"=="y" (
    echo.
    echo 请输入你的 Obsidian Vault 根目录路径
    echo （例如：C:\Users\用户名\Obsidian\collegenote）
    echo.
    set /p "VAULT_PATH=> "
    if not "!VAULT_PATH!"=="" (
        if exist "!VAULT_PATH!" (
            echo         [✓] Vault 路径有效
            echo.
            echo 路径已记录。启动 GUI 后会自动填充此路径。
            echo 你也可以稍后在 GUI 的设置页面中修改。
        ) else (
            echo         [!] 路径不存在，可稍后在 GUI 中手动设置
        )
    )
)

:: 询问是否打开项目目录
echo.
set /p "OPEN_DIR=是否打开项目目录？(Y/n): "
if /i not "!OPEN_DIR!"=="n" (
    explorer "!INSTALL_DIR!"
)

goto :success_exit

:: ============================================================
:: 错误处理
:: ============================================================
:error_exit
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                    ❌ 安装失败                             ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 请检查错误信息，解决问题后重新运行安装脚本。
echo.
pause
exit /b 1

:success_exit
echo.
echo 按任意键退出安装向导...
pause >nul
exit /b 0
