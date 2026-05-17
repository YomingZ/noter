#!/bin/bash
# ============================================================
# PDF 备考笔记一键生成器 - Linux 版本
# 使用方法：
#   1. 将 PDF 文件拖拽到脚本图标上
#   2. 或在终端运行: ./一键生成笔记.sh 文件.pdf
#   3. 或双击运行（需要 .desktop 文件）
# 支持批量处理多个文件
# ============================================================

# 设置编码
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 显示欢迎信息
clear
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      PDF 备考笔记一键生成器 v1.0                   ║${NC}"
echo -e "${BLUE}║      支持: OpenAI / Claude / Kimi                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# 检查参数
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}[提示] 使用方法：${NC}"
    echo "       方法1: 将 PDF 文件拖拽到脚本图标上"
    echo "       方法2: 在终端运行: ./一键生成笔记.sh 文件.pdf"
    echo ""
    echo "[可选] 请输入 PDF 文件路径（回车跳过）："
    read -r PDF_INPUT

    if [ -z "$PDF_INPUT" ]; then
        echo -e "${YELLOW}[信息] 未指定文件，启动交互模式...${NC}"
        PDF_FILES=""
    else
        PDF_FILES="$PDF_INPUT"
    fi
else
    PDF_FILES="$@"
fi

# 检查虚拟环境
if [ ! -f "venv/bin/activate" ]; then
    echo ""
    echo -e "${RED}[错误] 未找到虚拟环境！${NC}"
    echo ""
    echo "请先运行以下命令初始化项目："
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -e ."
    echo ""
    echo "按回车键退出..."
    read -r
    exit 1
fi

# 激活虚拟环境
echo -e "${GREEN}[1/4] 激活虚拟环境...${NC}"
source venv/bin/activate

# 检查配置文件
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo ""
        echo -e "${YELLOW}[警告] 未找到 .env 配置文件${NC}"
        echo "       请先配置 API 密钥！"
        echo ""
        echo "是否现在运行配置向导？(y/n)"
        read -r RUN_CONFIG

        if [ "$RUN_CONFIG" = "y" ] || [ "$RUN_CONFIG" = "Y" ]; then
            pdf-summarizer config --setup
            echo ""
            echo "配置完成！请重新运行此脚本。"
            echo "按回车键退出..."
            read -r
            exit 0
        else
            echo "按回车键退出..."
            read -r
            exit 1
        fi
    fi
fi

# 创建输出目录
OUTPUT_DIR="$SCRIPT_DIR/notes"
mkdir -p "$OUTPUT_DIR"
echo -e "${GREEN}[2/4] 输出目录: $OUTPUT_DIR${NC}"
echo ""

# 检测文件管理器
open_folder() {
    local folder="$1"
    if command -v xdg-open &> /dev/null; then
        xdg-open "$folder" &
    elif command -v nautilus &> /dev/null; then
        nautilus "$folder" &
    elif command -v dolphin &> /dev/null; then
        dolphin "$folder" &
    elif command -v thunar &> /dev/null; then
        thunar "$folder" &
    else
        echo "输出目录: $folder"
    fi
}

# 处理文件
if [ -z "$PDF_FILES" ]; then
    # 无文件参数，进入交互模式
    echo -e "${GREEN}[3/4] 启动交互模式...${NC}"
    echo ""

    # 显示选项
    echo "请选择操作："
    echo "  1. 处理单个 PDF 文件"
    echo "  2. 批量处理文件夹"
    echo "  3. 查看配置状态"
    echo "  4. 配置 API 密钥"
    echo "  5. 退出"
    echo ""
    read -p "请输入选项 (1-5): " choice

    case $choice in
        1)
            read -p "请输入 PDF 文件路径: " pdf_path
            if [ -f "$pdf_path" ]; then
                pdf-summarizer process "$pdf_path" -p kimi -o "$OUTPUT_DIR"
            else
                echo -e "${RED}[错误] 文件不存在${NC}"
            fi
            ;;
        2)
            read -p "请输入文件夹路径: " folder_path
            if [ -d "$folder_path" ]; then
                pdf-summarizer batch "$folder_path" -p kimi -o "$OUTPUT_DIR"
            else
                echo -e "${RED}[错误] 目录不存在${NC}"
            fi
            ;;
        3)
            pdf-summarizer config
            ;;
        4)
            pdf-summarizer config --setup
            ;;
        5)
            exit 0
            ;;
        *)
            echo -e "${RED}[错误] 无效选项${NC}"
            ;;
    esac
else
    # 有文件参数，处理拖拽的文件
    file_count=0
    success_count=0
    fail_count=0

    # 统计文件数
    for pdf_file in $PDF_FILES; do
        ((file_count++))
    done

    echo -e "${GREEN}[3/4] 准备处理 $file_count 个 PDF 文件...${NC}"
    echo "       ─────────────────────────────────────"
    echo ""

    for pdf_file in $PDF_FILES; do
        # 处理 file:// 协议
        pdf_file="${pdf_file#file://}"
        # URL 解码
        pdf_file=$(printf '%b' "${pdf_file//%/\\x}")

        # 检查文件是否存在
        if [ ! -f "$pdf_file" ]; then
            echo -e "${YELLOW}[跳过] 文件不存在: $(basename "$pdf_file")${NC}"
            continue
        fi

        # 检查是否为 PDF
        filename=$(basename "$pdf_file")
        extension="${filename##*.}"

        if [ "${extension,,}" != "pdf" ]; then
            echo -e "${YELLOW}[跳过] 非 PDF 文件: $filename${NC}"
            continue
        fi

        # 获取不带扩展名的文件名
        name_without_ext="${filename%.*}"

        echo -e "${BLUE}[处理] $filename${NC}"
        echo "       ─────────────────────────────────────"

        # 运行 PDF Summarizer
        if pdf-summarizer process "$pdf_file" -p kimi -o "$OUTPUT_DIR/${name_without_ext}_笔记.docx" 2>&1; then
            echo -e "       ${GREEN}[完成] ✓ 已生成: ${name_without_ext}_笔记.docx${NC}"
            ((success_count++))
        else
            echo -e "       ${RED}[失败] ✗ 处理出错${NC}"
            ((fail_count++))
        fi

        echo ""
    done

    # 显示结果
    echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                    处理完成                         ║${NC}"
    echo -e "${BLUE}╠════════════════════════════════════════════════════╣${NC}"
    echo -e "${BLUE}║  成功: ${GREEN}$success_count${BLUE 个文件                         ║${NC}"
    echo -e "${BLUE}║  失败: ${RED}$fail_count${BLUE 个文件                            ║${NC}"
    echo -e "${BLUE}╠════════════════════════════════════════════════════╣${NC}"
    echo -e "${BLUE}║  输出目录: $OUTPUT_DIR                               ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
fi

# 打开输出目录
echo ""
echo "按回车键打开输出目录，或关闭窗口退出..."
read -r
open_folder "$OUTPUT_DIR"
