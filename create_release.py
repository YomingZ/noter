#!/usr/bin/env python3
"""
创建发布包 - 打包项目用于分发

使用方法：
    python create_release.py

将创建一个包含所有必要文件的 zip 压缩包。
"""

import os
import sys
import shutil
import zipfile
from pathlib import Path
from datetime import datetime


def get_script_dir() -> Path:
    """获取脚本目录"""
    return Path(__file__).parent.resolve()


def clean_build_files():
    """清理构建文件"""
    script_dir = get_script_dir()

    # 要删除的目录（不包括 venv，因为可能正在使用）
    dirs_to_remove = [
        "build",
        "dist",
        ".pytest_cache",
        "output/.cache",
        "output/.stats",
        "output/.state",
    ]

    # 要删除的文件模式
    patterns_to_remove = [
        "*.egg-info",
        "*.pyc",
        "*.pyo",
    ]

    for dir_name in dirs_to_remove:
        path = script_dir / dir_name
        if path.exists() and path.is_dir():
            try:
                shutil.rmtree(path)
                print(f"  删除目录: {dir_name}")
            except PermissionError:
                print(f"  [跳过] {dir_name} (权限不足)")

    for pattern in patterns_to_remove:
        for path in script_dir.glob(pattern):
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                print(f"  删除: {path.name}")
            except PermissionError:
                print(f"  [跳过] {path.name} (权限不足)")

    # 删除所有 __pycache__（排除 venv 目录）
    for pycache in script_dir.rglob("__pycache__"):
        # 跳过 venv 目录内的缓存
        if "venv" in str(pycache):
            continue
        try:
            shutil.rmtree(pycache)
        except PermissionError:
            pass


def create_release_package():
    """创建发布包"""
    script_dir = get_script_dir()
    release_dir = script_dir / "release"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"PDF笔记生成器_{timestamp}"
    package_dir = release_dir / package_name

    print("=" * 60)
    print("创建发布包")
    print("=" * 60)
    print()

    # 清理
    print("[1/4] 清理构建文件...")
    clean_build_files()
    print()

    # 创建目录
    print("[2/4] 创建发布目录...")
    package_dir.mkdir(parents=True, exist_ok=True)
    print(f"  创建: {package_dir}")
    print()

    # 要包含的文件
    print("[3/4] 复制文件...")

    files_to_include = [
        # 安装脚本
        "install.bat",
        "install.sh",
        "uninstall.bat",
        "uninstall.sh",

        # 拖拽运行脚本
        "一键生成笔记.bat",
        "一键生成笔记.command",
        "一键生成笔记.sh",
        "创建桌面快捷方式.py",

        # GUI
        "gui_launcher.py",
        "build_gui.py",
        "启动GUI.bat",

        # 配置文件
        ".env.example",
        "requirements.txt",
        "pyproject.toml",
        "README.md",
        "快速开始.md",

        # 源代码
        "src/",
        "config/",
    ]

    # 要排除的模式
    exclude_patterns = [
        "__pycache__",
        "*.pyc",
        "*.pyo",
        ".pytest_cache",
    ]

    def should_exclude(path: Path) -> bool:
        """检查是否应该排除"""
        for pattern in exclude_patterns:
            if pattern.startswith("*"):
                if path.match(pattern):
                    return True
            else:
                if pattern in str(path):
                    return True
        return False

    for item in files_to_include:
        src = script_dir / item

        if not src.exists():
            print(f"  [跳过] {item} 不存在")
            continue

        dst = package_dir / item

        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)

            # 复制目录，排除特定文件
            def ignore_patterns(directory, files):
                ignored = []
                for f in files:
                    file_path = Path(directory) / f
                    if should_exclude(file_path):
                        ignored.append(f)
                return ignored

            shutil.copytree(src, dst, ignore=ignore_patterns)
            print(f"  [OK] 复制目录: {item}")
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"  [OK] 复制文件: {item}")

    print()

    # 创建压缩包
    print("[4/4] 创建压缩包...")

    zip_path = release_dir / f"{package_name}.zip"

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in package_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(release_dir)
                zipf.write(file_path, arcname)

    print(f"  [OK] 创建: {zip_path}")
    print()

    # 删除临时目录
    shutil.rmtree(package_dir)

    # 计算文件大小
    size_mb = zip_path.stat().st_size / (1024 * 1024)

    print("=" * 60)
    print("发布包创建完成！")
    print("=" * 60)
    print()
    print(f"文件: {zip_path}")
    print(f"大小: {size_mb:.2f} MB")
    print()
    print("分发方法:")
    print("  1. 将 zip 文件发送给用户")
    print("  2. 用户解压后运行 install.bat (Windows) 或 install.sh (Mac/Linux)")
    print()


if __name__ == "__main__":
    create_release_package()
