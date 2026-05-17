#!/bin/bash
# ============================================================
# PDF 备考笔记生成器 - macOS/Linux 卸载脚本
# ============================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# 获取脚本目录
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$INSTALL_DIR"

# 检测操作系统
OS="$(uname -s)"

clear
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║       📚 PDF 备考笔记生成器 - 卸载向导                    ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 确认卸载
echo -e "${YELLOW}[警告] 此操作将：${NC}"
echo ""
echo "       - 删除虚拟环境 (venv/)"
echo "       - 删除输出目录 (notes/)"
echo "       - 删除缓存文件 (.cache/, __pycache__/)"
echo "       - 删除桌面快捷方式"
echo "       - 删除编译文件 (*.pyc, *.pyo)"
echo ""
echo -e "${GREEN}       [保留] 以下文件将被保留：${NC}"
echo "       - 配置文件 (.env, config/)"
echo "       - 生成的笔记 (可手动删除 notes/)"
echo "       - 安装脚本和源代码"
echo ""

read -p "确定要卸载吗？(yes/N): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo ""
    echo "已取消卸载操作。"
    exit 0
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "开始卸载..."
echo "════════════════════════════════════════════════════════════"
echo ""

# 1. 删除虚拟环境
echo "[1/5] 删除虚拟环境..."
if [ -d "venv" ]; then
    rm -rf venv
    echo -e "      ${GREEN}[✓] venv 已删除${NC}"
else
    echo "      虚拟环境不存在，跳过"
fi

# 2. 删除缓存
echo "[2/5] 删除缓存文件..."
rm -rf output/.cache output/.stats output/.state 2>/dev/null
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null
echo -e "      ${GREEN}[✓] 缓存已清理${NC}"

# 3. 删除构建文件
echo "[3/5] 删除构建文件..."
rm -rf build dist *.egg-info 2>/dev/null
echo -e "      ${GREEN}[✓] 构建文件已删除${NC}"

# 4. 删除桌面快捷方式
echo "[4/5] 删除桌面快捷方式..."

# 获取桌面目录
if [ "$OS" = "Darwin" ]; then
    DESKTOP_DIR="$HOME/Desktop"
    APP_PATH="$DESKTOP_DIR/PDF笔记生成器.app"

    if [ -d "$APP_PATH" ]; then
        rm -rf "$APP_PATH"
        echo -e "      ${GREEN}[✓] 已删除应用程序${NC}"
    fi
else
    DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
    DESKTOP_FILE="$DESKTOP_DIR/pdf-notes-generator.desktop"

    if [ -f "$DESKTOP_FILE" ]; then
        rm -f "$DESKTOP_FILE"
        echo -e "      ${GREEN}[✓] 已删除桌面快捷方式${NC}"
    fi
fi

# 5. 清理空目录
echo "[5/5] 清理空目录..."
if [ -d "notes" ]; then
    if [ -z "$(ls -A notes 2>/dev/null)" ]; then
        rmdir notes
        echo -e "      ${GREEN}[✓] notes 目录已删除${NC}"
    else
        echo -e "      ${YELLOW}[!] notes 目录不为空，已保留${NC}"
    fi
fi

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                    ✅ 卸载完成                             ║${NC}"
echo -e "${CYAN}╠════════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║  以下文件/文件夹已保留，可手动删除：                       ║${NC}"
echo -e "${CYAN}║    - .env (API 配置)                                       ║${NC}"
echo -e "${CYAN}║    - config/ (配置文件)                                    ║${NC}"
echo -e "${CYAN}║    - notes/ (生成的笔记，如果不为空)                       ║${NC}"
echo -e "${CYAN}║    - install.sh / uninstall.sh (安装/卸载脚本)             ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║  如需完全删除，请手动删除整个项目文件夹。                  ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

read -p "是否打开项目目录？(Y/n): " OPEN_DIR
if [ "$OPEN_DIR" != "n" ] && [ "$OPEN_DIR" != "N" ]; then
    if [ "$OS" = "Darwin" ]; then
        open "$INSTALL_DIR"
    else
        xdg-open "$INSTALL_DIR" 2>/dev/null || true
    fi
fi

exit 0
