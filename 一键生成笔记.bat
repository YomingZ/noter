@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================================
:: PDF 备考笔记一键生成器 - Windows 版本
:: 使用方法：将 PDF 文件拖拽到此脚本图标上
:: 支持批量处理多个文件
:: ============================================================

title PDF 备考笔记生成器

:: 设置颜色
color 0A

:: 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: 显示欢迎信息
echo.
echo ╔════════════════════════════════════════════════════╗
echo ║      PDF 备考笔记一键生成器 v1.0                   ║
echo ║      支持: OpenAI / Claude / Kimi                   ║
echo ╚════════════════════════════════════════════════════╝
echo.

:: 检查是否有拖拽的文件
if "%~1"=="" (
    echo [提示] 使用方法：
    echo        1. 将 PDF 文件拖拽到此脚本图标上
    echo        2. 或在命令行运行: 一键生成笔记.bat 文件.pdf
    echo.
    echo [可选] 你也可以输入 PDF 路径：
    echo.
    set /p "PDF_PATH=请输入 PDF 文件路径: "
    if "!PDF_PATH!"=="" (
        echo [错误] 未指定 PDF 文件
        goto :end
    )
    set "PDF_FILES=!PDF_PATH!"
) else (
    set "PDF_FILES=%*"
)

:: 检查虚拟环境
if not exist "venv\Scripts\activate.bat" (
    echo.
    echo [错误] 未找到虚拟环境！
    echo.
    echo 请先运行以下命令初始化项目：
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -e .
    echo.
    goto :end
)

:: 激活虚拟环境
echo [1/4] 激活虚拟环境...
call venv\Scripts\activate.bat

:: 检查配置文件
if not exist ".env" (
    if exist ".env.example" (
        echo.
        echo [警告] 未找到 .env 配置文件
        echo        请先配置 API 密钥：
        echo.
        echo   1. 复制 .env.example 为 .env
        echo   2. 编辑 .env 填入你的 API Key
        echo   3. 重新运行此脚本
        echo.
        echo 是否现在运行配置向导？ [Y/N]
        set /p "RUN_CONFIG="
        if /i "!RUN_CONFIG!"=="Y" (
            pdf-summarizer config --setup
            goto :end
        )
        goto :end
    )
)

:: 创建输出目录
set "OUTPUT_DIR=%SCRIPT_DIR%notes"
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"
echo [2/4] 输出目录: %OUTPUT_DIR%
echo.

:: 统计文件数量
set file_count=0
for %%f in (%PDF_FILES%) do (
    set /a file_count+=1
)

echo [3/4] 准备处理 !file_count! 个 PDF 文件...
echo        ─────────────────────────────────────
echo.

:: 处理每个文件
set success_count=0
set fail_count=0

for %%f in (%PDF_FILES%) do (
    set "pdf_file=%%~f"

    :: 检查文件是否存在
    if not exist "!pdf_file!" (
        echo [跳过] 文件不存在: %%~nxf
        goto :next_file
    )

    :: 检查是否为 PDF
    if /i not "%%~xf"==".pdf" (
        echo [跳过] 非 PDF 文件: %%~nxf
        goto :next_file
    )

    echo [处理] %%~nxf
    echo        ─────────────────────────────────────

    :: 运行 PDF Summarizer
    pdf-summarizer process "!pdf_file!" -p kimi -o "%OUTPUT_DIR%\%%~nf_笔记.docx" 2>&1

    if !errorlevel! equ 0 (
        echo        [完成] ✓ 已生成: %%~nf_笔记.docx
        set /a success_count+=1
    ) else (
        echo        [失败] ✗ 处理出错
        set /a fail_count+=1
    )

    echo.
    :next_file
)

:: 显示结果
echo ╔════════════════════════════════════════════════════╗
echo ║                    处理完成                         ║
echo ╠════════════════════════════════════════════════════╣
echo ║  成功: !success_count! 个文件                        ║
echo ║  失败: !fail_count! 个文件                           ║
echo ╠════════════════════════════════════════════════════╣
echo ║  输出目录: %OUTPUT_DIR%                              ║
echo ╚════════════════════════════════════════════════════╝

:: 打开输出目录
echo.
echo 按任意键打开输出目录，或关闭窗口退出...
pause >nul
explorer "%OUTPUT_DIR%"

:end
echo.
echo 按任意键退出...
pause >nul
