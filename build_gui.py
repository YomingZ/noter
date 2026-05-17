#!/usr/bin/env python3
"""
GUI 打包脚本 - 使用 PyInstaller 打包为独立可执行文件

支持平台:
- Windows: 生成 .exe 文件
- macOS: 生成 .app 文件
- Linux: 生成可执行文件

使用方法:
    python build_gui.py          # 打包 GUI 版本
    python build_gui.py --cli    # 同时打包 CLI 版本
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path


def get_script_dir() -> Path:
    """获取脚本目录"""
    return Path(__file__).parent.resolve()


def check_pyinstaller():
    """检查 PyInstaller 是否安装"""
    try:
        import PyInstaller
        print(f"✓ PyInstaller 版本: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("✗ PyInstaller 未安装")
        print("\n请先安装:")
        print("  pip install pyinstaller")
        return False


def create_icon():
    """创建默认图标（如果不存在）"""
    script_dir = get_script_dir()

    # 检查是否已有图标
    icon_ico = script_dir / "icon.ico"
    icon_icns = script_dir / "icon.icns"
    icon_png = script_dir / "icon.png"

    if icon_ico.exists() or icon_icns.exists() or icon_png.exists():
        print("✓ 图标文件已存在")
        return True

    # 创建简单的 PNG 图标（需要 Pillow）
    try:
        from PIL import Image, ImageDraw, ImageFont

        # 创建一个简单的图标
        size = 256
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 绘制背景圆形
        draw.ellipse([20, 20, size-20, size-20], fill='#4CAF50')

        # 绘制书本图标
        draw.rectangle([60, 80, 196, 176], fill='white', outline='#2E7D32', width=3)
        draw.line([128, 80, 128, 176], fill='#2E7D32', width=2)

        # 保存
        img.save(icon_png, 'PNG')
        print(f"✓ 已创建默认图标: {icon_png}")

        # 转换为其他格式
        system = platform.system()

        if system == "Windows":
            # 转换为 ICO
            img.save(icon_ico, 'ICO', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
            print(f"✓ 已创建 ICO 图标: {icon_ico}")

        elif system == "Darwin":
            # macOS 需要 icns，暂时使用 PNG
            print("  提示: macOS 可使用 iconutil 创建 .icns 文件")

        return True

    except ImportError:
        print("⚠ Pillow 未安装，跳过图标创建")
        print("  可安装: pip install Pillow")
        return False


def build_gui():
    """打包 GUI 版本"""
    script_dir = get_script_dir()
    system = platform.system()

    print("\n" + "=" * 50)
    print("打包 GUI 版本")
    print("=" * 50)

    # 构建参数
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=PDF笔记生成器",
        "--onefile",
        "--windowed",  # 不显示控制台窗口
        "--noconfirm",
        "--clean",
    ]

    # 添加图标
    if system == "Windows":
        icon_path = script_dir / "icon.ico"
        if icon_path.exists():
            cmd.extend(["--icon", str(icon_path)])

    elif system == "Darwin":
        icon_path = script_dir / "icon.icns"
        if icon_path.exists():
            cmd.extend(["--icon", str(icon_path)])

    # 添加数据文件
    config_dir = script_dir / "config"
    if config_dir.exists():
        cmd.extend(["--add-data", f"{config_dir}:config"])

    # 添加隐藏导入
    hidden_imports = [
        "pdf_summarizer",
        "pdfplumber",
        "docx",
        "openai",
        "anthropic",
        "yaml",
        "tqdm",
        "rich",
        "pydantic",
        "pydantic_settings",
    ]

    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])

    # 添加入口文件
    cmd.append(str(script_dir / "gui_launcher.py"))

    print(f"\n执行命令:")
    print(" ".join(cmd[:5]) + " ...")

    # 执行打包
    result = subprocess.run(cmd, cwd=script_dir)

    if result.returncode == 0:
        print("\n✓ GUI 打包成功！")

        # 显示输出位置
        dist_dir = script_dir / "dist"
        if system == "Windows":
            exe_file = dist_dir / "PDF笔记生成器.exe"
        elif system == "Darwin":
            exe_file = dist_dir / "PDF笔记生成器.app"
        else:
            exe_file = dist_dir / "PDF笔记生成器"

        if exe_file.exists():
            print(f"  输出文件: {exe_file}")

        return True
    else:
        print("\n✗ GUI 打包失败")
        return False


def build_cli():
    """打包 CLI 版本"""
    script_dir = get_script_dir()

    print("\n" + "=" * 50)
    print("打包 CLI 版本")
    print("=" * 50)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=pdf-summarizer",
        "--onefile",
        "--console",  # 显示控制台
        "--noconfirm",
        "--clean",
    ]

    # 添加数据文件
    config_dir = script_dir / "config"
    if config_dir.exists():
        cmd.extend(["--add-data", f"{config_dir}:config"])

    # 添加入口点
    cmd.extend(["--hidden-import", "pdf_summarizer.cli"])

    # 创建入口脚本
    entry_script = script_dir / "_cli_entry.py"
    entry_script.write_text('''
from pdf_summarizer.cli import app
if __name__ == "__main__":
    app()
''')

    cmd.append(str(entry_script))

    print(f"\n执行命令:")
    print(" ".join(cmd[:5]) + " ...")

    result = subprocess.run(cmd, cwd=script_dir)

    # 清理临时文件
    if entry_script.exists():
        entry_script.unlink()

    if result.returncode == 0:
        print("\n✓ CLI 打包成功！")
        return True
    else:
        print("\n✗ CLI 打包失败")
        return False


def create_dist_package():
    """创建分发包"""
    script_dir = get_script_dir()
    dist_dir = script_dir / "dist"
    release_dir = dist_dir / "release"

    system = platform.system()

    print("\n" + "=" * 50)
    print("创建分发包")
    print("=" * 50)

    # 创建 release 目录
    release_dir.mkdir(parents=True, exist_ok=True)

    # 复制必要文件
    files_to_copy = [
        ".env.example",
        "README.md",
    ]

    for file_name in files_to_copy:
        src = script_dir / file_name
        if src.exists():
            dst = release_dir / file_name
            shutil.copy2(src, dst)
            print(f"  复制: {file_name}")

    # 创建默认配置
    config_release = release_dir / "config"
    config_release.mkdir(exist_ok=True)

    config_src = script_dir / "config"
    if config_src.exists():
        for f in config_src.glob("*"):
            if not (config_release / f.name).exists():
                shutil.copy2(f, config_release / f.name)

    # 创建启动脚本
    if system == "Windows":
        bat_content = '''@echo off
chcp 65001 >nul
echo 正在启动 PDF 笔记生成器...
"%~dp0PDF笔记生成器.exe"
pause
'''
        with open(release_dir / "启动.bat", "w", encoding="utf-8") as f:
            f.write(bat_content)

    else:
        sh_content = '''#!/bin/bash
cd "$(dirname "$0")"
./PDF笔记生成器 "$@"
'''
        sh_path = release_dir / "启动.sh"
        with open(sh_path, "w", encoding="utf-8") as f:
            f.write(sh_content)
        os.chmod(sh_path, 0o755)

    # 复制可执行文件
    if system == "Windows":
        exe_src = dist_dir / "PDF笔记生成器.exe"
    elif system == "Darwin":
        exe_src = dist_dir / "PDF笔记生成器.app"
    else:
        exe_src = dist_dir / "PDF笔记生成器"

    if exe_src.exists():
        exe_dst = release_dir / exe_src.name
        if exe_dst.exists():
            if exe_dst.is_dir():
                shutil.rmtree(exe_dst)
            else:
                exe_dst.unlink()
        shutil.copytree(exe_src, exe_dst) if exe_src.is_dir() else shutil.copy2(exe_src, exe_dst)
        print(f"  复制: {exe_src.name}")

    print(f"\n✓ 分发包已创建: {release_dir}")
    return True


def main():
    """主函数"""
    print("=" * 50)
    print("PDF 备考笔记生成器 - 打包工具")
    print("=" * 50)
    print(f"系统: {platform.system()}")
    print(f"Python: {sys.version.split()[0]}")
    print()

    # 检查 PyInstaller
    if not check_pyinstaller():
        return 1

    # 创建图标
    create_icon()

    # 解析参数
    build_cli_too = "--cli" in sys.argv

    # 打包 GUI
    if not build_gui():
        return 1

    # 打包 CLI（可选）
    if build_cli_too:
        if not build_cli():
            return 1

    # 创建分发包
    create_dist_package()

    print("\n" + "=" * 50)
    print("打包完成！")
    print("=" * 50)
    print()
    print("使用方法:")
    print("  1. 将 dist/release 文件夹复制到目标电脑")
    print("  2. 运行「启动」脚本或直接运行可执行文件")
    print("  3. 首次使用请配置 .env 文件中的 API 密钥")

    return 0


if __name__ == "__main__":
    sys.exit(main())
