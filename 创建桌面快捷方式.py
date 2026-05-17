#!/usr/bin/env python3
"""
创建桌面快捷方式 - 跨平台工具

功能：
- Windows: 创建 .lnk 快捷方式
- macOS: 创建 .app 应用包
- Linux: 创建 .desktop 文件

使用方法：
    python 创建桌面快捷方式.py

运行后会在桌面创建指向"一键生成笔记"脚本的快捷方式。
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path


def get_script_dir() -> Path:
    """获取脚本所在目录"""
    return Path(__file__).parent.resolve()


def get_desktop_dir() -> Path:
    """获取桌面目录"""
    system = platform.system()

    if system == "Windows":
        # Windows 桌面
        desktop = Path.home() / "Desktop"
        if not desktop.exists():
            desktop = Path.home() / "OneDrive" / "桌面"
        if not desktop.exists():
            desktop = Path.home() / "OneDrive" / "Desktop"
        return desktop

    elif system == "Darwin":
        # macOS 桌面
        return Path.home() / "Desktop"

    else:
        # Linux 桌面
        desktop = Path.home() / "Desktop"
        if not desktop.exists():
            # 尝试从配置文件获取
            try:
                result = subprocess.run(
                    ["xdg-user-dir", "DESKTOP"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    desktop = Path(result.stdout.strip())
            except:
                pass
        return desktop


def create_windows_shortcut():
    """创建 Windows 快捷方式"""
    script_dir = get_script_dir()
    desktop_dir = get_desktop_dir()

    # 快捷方式目标
    bat_file = script_dir / "一键生成笔记.bat"
    if not bat_file.exists():
        print(f"错误: 找不到脚本文件 {bat_file}")
        return False

    # 快捷方式路径
    shortcut_path = desktop_dir / "PDF笔记生成器.lnk"

    print(f"正在创建 Windows 快捷方式...")
    print(f"  目标: {bat_file}")
    print(f"  位置: {shortcut_path}")

    # 使用 PowerShell 创建快捷方式
    ps_script = f'''
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{bat_file}"
$Shortcut.WorkingDirectory = "{script_dir}"
$Shortcut.Description = "PDF 备考笔记一键生成器"
$Shortcut.IconLocation = "{bat_file},0"
$Shortcut.Save()
'''

    try:
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"\n✓ 快捷方式已创建: {shortcut_path}")
            return True
        else:
            print(f"错误: {result.stderr}")
            return False

    except Exception as e:
        print(f"创建快捷方式失败: {e}")

        # 备选方案：创建 .url 文件
        print("尝试创建 URL 快捷方式...")
        url_path = desktop_dir / "PDF笔记生成器.url"

        with open(url_path, "w", encoding="utf-8") as f:
            f.write(f"""[InternetShortcut]
URL=file:///{bat_file.as_posix()}
IconIndex=0
""")
        print(f"\n✓ URL 快捷方式已创建: {url_path}")
        return True


def create_macos_app():
    """创建 macOS 应用包"""
    script_dir = get_script_dir()
    desktop_dir = get_desktop_dir()

    # 脚本文件
    command_file = script_dir / "一键生成笔记.command"

    # 应用包路径
    app_name = "PDF笔记生成器.app"
    app_path = desktop_dir / app_name
    contents_path = app_path / "Contents"
    macos_path = contents_path / "MacOS"

    print(f"正在创建 macOS 应用包...")
    print(f"  位置: {app_path}")

    try:
        # 创建应用包结构
        macos_path.mkdir(parents=True, exist_ok=True)

        # 创建可执行脚本
        exec_script = macos_path / "applet"

        script_content = f'''#!/bin/bash
cd "{script_dir}"
source venv/bin/activate 2>/dev/null || true
exec "{command_file}" "$@"
'''

        with open(exec_script, "w", encoding="utf-8") as f:
            f.write(script_content)

        os.chmod(exec_script, 0o755)

        # 创建 Info.plist
        plist_path = contents_path / "Info.plist"
        plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>applet</string>
    <key>CFBundleName</key>
    <string>PDF笔记生成器</string>
    <key>CFBundleDisplayName</key>
    <string>PDF笔记生成器</string>
    <key>CFBundleIdentifier</key>
    <string>com.pdfsummarizer.app</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
</dict>
</plist>
'''

        with open(plist_path, "w", encoding="utf-8") as f:
            f.write(plist_content)

        # 确保原始脚本有执行权限
        if command_file.exists():
            os.chmod(command_file, 0o755)

        print(f"\n✓ 应用包已创建: {app_path}")
        print("\n提示: 首次运行可能需要在「系统偏好设置 > 安全性与隐私」中允许运行")
        return True

    except Exception as e:
        print(f"创建应用包失败: {e}")
        return False


def create_linux_desktop():
    """创建 Linux .desktop 文件"""
    script_dir = get_script_dir()
    desktop_dir = get_desktop_dir()

    # 脚本文件
    sh_file = script_dir / "一键生成笔记.sh"

    # desktop 文件路径
    desktop_file = desktop_dir / "pdf-notes-generator.desktop"

    print(f"正在创建 Linux 快捷方式...")
    print(f"  位置: {desktop_file}")

    # .desktop 文件内容
    desktop_content = f'''[Desktop Entry]
Version=1.0
Type=Application
Name=PDF笔记生成器
Comment=PDF 备考笔记一键生成器
Exec="{sh_file}" %F
Icon=document
Terminal=true
Categories=Office;Education;
StartupNotify=true
MimeType=application/pdf;
'''

    try:
        with open(desktop_file, "w", encoding="utf-8") as f:
            f.write(desktop_content)

        # 设置执行权限
        os.chmod(desktop_file, 0o755)

        # 确保脚本有执行权限
        if sh_file.exists():
            os.chmod(sh_file, 0o755)

        # 标记为可信任
        try:
            subprocess.run(["gio", "set", str(desktop_file), "metadata::trusted", "true"],
                         capture_output=True)
        except:
            pass

        print(f"\n✓ 快捷方式已创建: {desktop_file}")
        print("\n提示: 如果图标不显示，请右键点击 -> 允许启动")
        return True

    except Exception as e:
        print(f"创建快捷方式失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 50)
    print("   PDF 备考笔记生成器 - 创建桌面快捷方式")
    print("=" * 50)
    print()

    system = platform.system()
    print(f"检测到系统: {system}")
    print(f"项目目录: {get_script_dir()}")
    print(f"桌面目录: {get_desktop_dir()}")
    print()

    # 检查桌面目录是否存在
    desktop_dir = get_desktop_dir()
    if not desktop_dir.exists():
        print(f"错误: 桌面目录不存在: {desktop_dir}")
        return

    # 根据系统创建快捷方式
    if system == "Windows":
        success = create_windows_shortcut()
    elif system == "Darwin":
        success = create_macos_app()
    elif system == "Linux":
        success = create_linux_desktop()
    else:
        print(f"不支持的系统: {system}")
        return

    print()
    if success:
        print("=" * 50)
        print("   快捷方式创建成功！")
        print("=" * 50)
        print()
        print("使用方法:")
        print("  1. 在桌面找到「PDF笔记生成器」图标")
        print("  2. 将 PDF 文件拖拽到图标上")
        print("  3. 等待处理完成，查看 notes/ 文件夹")
    else:
        print("快捷方式创建失败，请手动创建")


if __name__ == "__main__":
    main()
