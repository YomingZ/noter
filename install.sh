#!/bin/bash
# ============================================================
# PDF 备考笔记生成器 - macOS/Linux 安装脚本
#
# 功能：
#   - 自动检测 Python 环境
#   - 创建虚拟环境
#   - 安装所有依赖
#   - 创建桌面快捷方式
#   - 配置文件初始化
#
# 使用方法：
#   chmod +x install.sh
#   ./install.sh
# ============================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 获取脚本目录
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$INSTALL_DIR"

# 显示欢迎信息
clear
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║       📚 PDF 备考笔记生成器 - 安装向导                    ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║       版本: 1.0.0                                          ║${NC}"
echo -e "${CYAN}║       支持: macOS / Linux                                  ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 检测操作系统
OS="$(uname -s)"
case "$OS" in
    Darwin*)
        OS_NAME="macOS"
        ;;
    Linux*)
        OS_NAME="Linux"
        ;;
    *)
        OS_NAME="$OS"
        ;;
esac

echo -e "${BLUE}检测到系统: ${OS_NAME}${NC}"
echo ""

# 步骤计数
STEP=0
TOTAL=6

# ============================================================
# 步骤 1: 检测 Python
# ============================================================
((STEP++))
echo -e "${GREEN}[$STEP/$TOTAL] 检测 Python 环境...${NC}"
echo "        ─────────────────────────────────────────────"

# 检测 Python 3
PYTHON_CMD=""
for cmd in python3 python; do
    if command -v $cmd &> /dev/null; then
        version=$($cmd --version 2>&1 | awk '{print $2}')
        major=$(echo $version | cut -d. -f1)
        minor=$(echo $version | cut -d. -f2)

        if [ "$major" -ge 3 ] && [ "$minor" -ge 9 ]; then
            PYTHON_CMD=$cmd
            echo -e "        ${GREEN}[✓] Python 版本: $version${NC}"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo -e "        ${RED}[✗] 未检测到 Python 3.9+${NC}"
    echo ""
    echo "        请先安装 Python 3.9 或更高版本："
    echo ""
    if [ "$OS" = "Darwin" ]; then
        echo "          brew install python3"
    else
        echo "          sudo apt install python3 python3-pip python3-venv"
        echo "          # 或"
        echo "          sudo dnf install python3 python3-pip"
    fi
    echo ""
    exit 1
fi

# 检测 pip
if ! $PYTHON_CMD -m pip --version &> /dev/null; then
    echo -e "        ${RED}[✗] pip 不可用${NC}"
    exit 1
fi
echo -e "        ${GREEN}[✓] pip 已安装${NC}"
echo ""

# ============================================================
# 步骤 2: 创建虚拟环境
# ============================================================
((STEP++))
echo -e "${GREEN}[$STEP/$TOTAL] 创建虚拟环境...${NC}"
echo "        ─────────────────────────────────────────────"

if [ -d "venv" ]; then
    echo -e "        ${YELLOW}[!] 虚拟环境已存在${NC}"
    read -p "        是否重新创建？(y/N): " RECREATE

    if [ "$RECREATE" = "y" ] || [ "$RECREATE" = "Y" ]; then
        echo "        正在删除旧的虚拟环境..."
        rm -rf venv
    else
        echo "        跳过创建步骤"
        echo ""
        goto skip_venv
    fi
fi

echo "        正在创建虚拟环境..."
$PYTHON_CMD -m venv venv

if [ ! -f "venv/bin/activate" ]; then
    echo -e "        ${RED}[✗] 虚拟环境创建失败${NC}"
    exit 1
fi

echo -e "        ${GREEN}[✓] 虚拟环境创建成功${NC}"

:skip_venv
echo ""

# ============================================================
# 步骤 3: 安装依赖
# ============================================================
((STEP++))
echo -e "${GREEN}[$STEP/$TOTAL] 安装依赖包...${NC}"
echo "        ─────────────────────────────────────────────"

# 激活虚拟环境
source venv/bin/activate

# 升级 pip
echo "        升级 pip..."
pip install --upgrade pip -q

# 安装依赖
echo "        安装核心依赖..."
pip install -e . -q

if [ $? -ne 0 ]; then
    echo -e "        ${YELLOW}[!] 部分依赖安装失败，尝试单独安装...${NC}"
    pip install pdfplumber python-docx openai anthropic typer pydantic pydantic-settings python-dotenv pyyaml rich tqdm
fi

echo -e "        ${GREEN}[✓] 依赖安装完成${NC}"
echo ""

# ============================================================
# 步骤 4: 配置文件初始化
# ============================================================
((STEP++))
echo -e "${GREEN}[$STEP/$TOTAL] 配置文件初始化...${NC}"
echo "        ─────────────────────────────────────────────"

# 创建 .env 文件
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "        ${GREEN}[✓] 已创建 .env 配置文件${NC}"
    else
        echo -e "        ${YELLOW}[!] 未找到 .env.example，跳过${NC}"
    fi
else
    echo -e "        ${YELLOW}[!] .env 文件已存在${NC}"
fi

# 创建输出目录
mkdir -p notes
echo -e "        ${GREEN}[✓] 已创建 notes 输出目录${NC}"

# 复制配置文件
if [ ! -f "config/settings.yaml" ]; then
    if [ -f "config/settings.yaml.example" ]; then
        cp config/settings.yaml.example config/settings.yaml
        echo -e "        ${GREEN}[✓] 已创建 settings.yaml${NC}"
    fi
fi
echo ""

# ============================================================
# 步骤 5: 创建桌面快捷方式
# ============================================================
((STEP++))
echo -e "${GREEN}[$STEP/$TOTAL] 创建桌面快捷方式...${NC}"
echo "        ─────────────────────────────────────────────"

# 获取桌面目录
DESKTOP_DIR=""
if [ "$OS" = "Darwin" ]; then
    DESKTOP_DIR="$HOME/Desktop"
else
    DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
fi

if [ ! -d "$DESKTOP_DIR" ]; then
    echo -e "        ${YELLOW}[!] 无法找到桌面目录${NC}"
else
    echo "        正在创建快捷方式..."

    if [ "$OS" = "Darwin" ]; then
        # macOS: 创建 .app 包
        APP_PATH="$DESKTOP_DIR/PDF笔记生成器.app"
        mkdir -p "$APP_PATH/Contents/MacOS"

        # 创建启动脚本
        cat > "$APP_PATH/Contents/MacOS/applet" << EOF
#!/bin/bash
cd "$INSTALL_DIR"
source venv/bin/activate 2>/dev/null
exec "$INSTALL_DIR/一键生成笔记.command" "\$@"
EOF
        chmod +x "$APP_PATH/Contents/MacOS/applet"

        # 创建 Info.plist
        cat > "$APP_PATH/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>applet</string>
    <key>CFBundleName</key>
    <string>PDF笔记生成器</string>
    <key>CFBundleIdentifier</key>
    <string>com.pdfsummarizer.app</string>
</dict>
</plist>
EOF

        echo -e "        ${GREEN}[✓] 已创建应用程序: $APP_PATH${NC}"

    else
        # Linux: 创建 .desktop 文件
        DESKTOP_FILE="$DESKTOP_DIR/pdf-notes-generator.desktop"

        cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=PDF笔记生成器
Comment=PDF 备考笔记一键生成器
Exec="$INSTALL_DIR/一键生成笔记.sh" %F
Icon=document
Terminal=true
Categories=Office;Education;
MimeType=application/pdf;
EOF

        chmod +x "$DESKTOP_FILE"
        chmod +x "$INSTALL_DIR/一键生成笔记.sh"

        # 标记为可信任
        gio set "$DESKTOP_FILE" metadata::trusted true 2>/dev/null || true

        echo -e "        ${GREEN}[✓] 已创建桌面快捷方式${NC}"
    fi
fi
echo ""

# ============================================================
# 步骤 6: 安装完成
# ============================================================
((STEP++))
echo -e "${GREEN}[$STEP/$TOTAL] 安装完成！${NC}"
echo "        ─────────────────────────────────────────────"
echo ""

echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                    🎉 安装成功！                           ║${NC}"
echo -e "${CYAN}╠════════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║  安装位置: $INSTALL_DIR${NC}"
printf  "${CYAN}║%-60s║${NC}\n" ""
echo -e "${CYAN}╠════════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║                      使用方法                              ║${NC}"
echo -e "${CYAN}╠════════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║  方式一（拖拽模式）：                                      ║${NC}"
echo -e "${CYAN}║    1. 将 PDF 文件拖到桌面的「PDF笔记生成器」图标上        ║${NC}"
echo -e "${CYAN}║    2. 等待处理完成，笔记保存在 notes 文件夹               ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║  方式二（命令行）：                                        ║${NC}"
echo -e "${CYAN}║    source venv/bin/activate                                ║${NC}"
echo -e "${CYAN}║    pdf-summarizer process your_file.pdf -p kimi           ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}╠════════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║                    ⚠️ 重要提示                             ║${NC}"
echo -e "${CYAN}╠════════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║  首次使用请配置 API 密钥：                                 ║${NC}"
echo -e "${CYAN}║    1. 编辑 .env 文件填入 API Key                           ║${NC}"
echo -e "${CYAN}║    2. 或运行: pdf-summarizer config --setup               ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 询问是否配置 API
read -p "是否现在配置 API 密钥？(Y/n): " CONFIG_API
if [ "$CONFIG_API" != "n" ] && [ "$CONFIG_API" != "N" ]; then
    echo ""
    echo "正在启动配置向导..."
    pdf-summarizer config --setup
fi

# 询问是否打开项目目录
echo ""
read -p "是否打开项目目录？(Y/n): " OPEN_DIR
if [ "$OPEN_DIR" != "n" ] && [ "$OPEN_DIR" != "N" ]; then
    if [ "$OS" = "Darwin" ]; then
        open "$INSTALL_DIR"
    else
        xdg-open "$INSTALL_DIR" 2>/dev/null || true
    fi
fi

echo ""
echo "安装完成！按回车键退出..."
read
exit 0
