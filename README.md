# PDF 课件智能总结工具

基于 AI 的 PDF 课件智能总结工具，支持批量处理 PDF 文件，调用 OpenAI/Claude/Kimi API 提取重点知识，生成结构化的 Word 备考笔记。

## 功能特性

- 📄 **PDF 文本提取** - 使用 pdfplumber 高效提取 PDF 文本
- 🤖 **多 AI 提供商支持** - 支持 OpenAI、Claude、Kimi 等 AI 服务
- 📝 **结构化笔记生成** - 自动生成包含核心概念、知识点、复习建议的笔记
- 📁 **批量处理** - 支持批量处理整个文件夹的 PDF 文件
- 💾 **Word 输出** - 输出格式化的 Word 文档 (.docx)
- ⚙️ **灵活配置** - 支持 YAML 配置文件和 .env 环境变量
- 🖱️ **拖拽运行** - 支持拖拽 PDF 文件到脚本一键生成

## 快速开始（拖拽模式）

### Windows 用户

1. **初始化项目**（仅需一次）
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   pip install -e .
   python 创建桌面快捷方式.py
   ```

2. **使用方法**
   - 将 PDF 文件拖拽到 `一键生成笔记.bat` 或桌面快捷方式上
   - 生成的笔记保存在 `notes/` 文件夹

### macOS 用户

1. **初始化项目**（仅需一次）
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -e .
   python3 创建桌面快捷方式.py
   ```

2. **使用方法**
   - 双击 `一键生成笔记.command` 或将 PDF 拖拽到图标上
   - 生成的笔记保存在 `notes/` 文件夹

### Linux 用户

1. **初始化项目**（仅需一次）
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -e .
   python3 创建桌面快捷方式.py
   ```

2. **使用方法**
   - 双击桌面快捷方式或将 PDF 拖拽到图标上
   - 生成的笔记保存在 `notes/` 文件夹

## 安装

### 前置要求

- Python 3.9 或更高版本
- pip 包管理器

### 安装步骤

1. 克隆或下载项目

```bash
cd noter
```

2. 创建虚拟环境（推荐）

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. 安装依赖

```bash
pip install -e .
```

## 配置

### 1. 配置 API 密钥

复制 `.env.example` 到 `.env` 并填入你的 API 密钥：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# OpenAI API
OPENAI_API_KEY=sk-your-openai-api-key-here

# 或 Claude API
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here

# 或 Kimi API
KIMI_API_KEY=your-kimi-api-key-here

# 默认提供商
DEFAULT_PROVIDER=openai
```

### 2. 配置应用设置（可选）

复制并编辑配置文件：

```bash
cp config/settings.yaml.example config/settings.yaml
```

### 3. 自定义提示词（可选）

编辑 `config/prompts.yaml` 可以自定义 AI 总结的提示词模板。

## 使用方法

### 检查配置

```bash
pdf-summarizer config-check
```

### 处理单个 PDF 文件

```bash
# 使用默认提供商
pdf-summarizer process path/to/your.pdf

# 指定 AI 提供商
pdf-summarizer process path/to/your.pdf --provider claude

# 指定输出路径
pdf-summarizer process path/to/your.pdf --output notes.docx
```

### 批量处理目录

```bash
# 处理目录下所有 PDF
pdf-summarizer batch path/to/pdfs/

# 递归处理子目录
pdf-summarizer batch path/to/pdfs/ --recursive

# 指定 AI 提供商
pdf-summarizer batch path/to/pdfs/ --provider kimi
```

### 命令行选项

```
pdf-summarizer [OPTIONS] COMMAND

Commands:
  process       处理单个PDF文件
  batch         批量处理目录中的PDF文件
  config-check  检查配置状态

Options:
  --version     显示版本信息
  --verbose     显示详细日志
```

## 输出示例

生成的 Word 文档包含以下结构：

```
课程笔记
来源: example.pdf

核心概念
1. 第一个核心概念...
2. 第二个核心概念...

知识点详解
### 概念定义
...

### 关键特征
...

重点难点
- 考点一
- 考点二

复习建议
- 建议一
- 建议二
```

## 项目结构

```
noter/
├── src/pdf_summarizer/     # 源代码
│   ├── cli.py              # 命令行入口
│   ├── config.py           # 配置管理
│   ├── pdf_reader.py       # PDF 读取
│   ├── ai_client.py        # AI 客户端
│   ├── summarizer.py       # 总结逻辑
│   ├── docx_writer.py      # Word 输出
│   └── models.py           # 数据模型
├── config/                 # 配置文件
│   ├── settings.yaml.example
│   └── prompts.yaml
├── tests/                  # 测试文件
├── .env.example           # API 密钥模板
├── requirements.txt       # 依赖列表
├── pyproject.toml         # 项目配置
└── README.md
```

## 支持的 AI 提供商

| 提供商 | 标识 | 默认模型 |
|--------|------|----------|
| OpenAI | `openai` | gpt-4o |
| Claude | `claude` | claude-sonnet-4-6-20250514 |
| Kimi | `kimi` | moonshot-v1-8k |

## 开发

### 运行测试

```bash
pip install -e ".[dev]"
pytest
```

### 代码结构说明

- `PDFReader` - PDF 文本提取，使用 pdfplumber 库
- `BaseAIClient` - AI 客户端抽象基类，支持扩展新提供商
- `Summarizer` - 核心处理逻辑，协调各模块工作
- `DocxWriter` - Word 文档生成，使用 python-docx 库

## 许可证

MIT License
