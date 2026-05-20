# 📚 PDF 笔记生成器（Noter）

基于 AI 的 PDF 课件智能总结工具，支持 **拖拽生成**、**GUI 交互式操作**、**命令行批量处理**。
支持 Kimi / OpenAI / Claude 等 AI 服务，可输出 **Word 文档** 或 **Obsidian 笔记**。

---

## ✨ 功能特性

- 📄 **PDF 文本提取** — 使用 pdfplumber 高效提取 PDF 文本
- 🤖 **多 AI 提供商** — 支持 Kimi、OpenAI、Claude
- 📝 **多种输出格式** — Word (.docx)、Markdown (.md)、HTML、**Obsidian 笔记**
- 📁 **批量处理** — 支持批量处理整个文件夹的 PDF
- 🖱️ **拖拽模式** — 将 PDF 拖到图标上即生成，无需打开软件
- 🎨 **GUI 图形界面** — 现代化的 Windows 11 风格界面
- 🏛️ **Obsidian 集成** — 直接输出到 Obsidian Vault 的指定课程文件夹

---

## 🚀 快速安装（Windows）

### 前置要求

- **Windows 10/11**
- **Python 3.9 或更高版本**（[下载 Python](https://www.python.org/downloads/)）
  - 安装时请勾选 **"Add Python to PATH"**

### 安装步骤

**方式一：一键安装（推荐）**

双击项目目录中的 `install.bat`，脚本会自动：

1. ✅ 检测 Python 环境
2. ✅ 创建虚拟环境（venv）
3. ✅ 安装所有依赖
4. ✅ 创建桌面快捷方式
5. ✅ 引导配置 API 密钥和 Obsidian Vault 路径

> 💡 **提示**：安装完成后，桌面上会出现两个快捷方式：
> - **PDF笔记生成器** — 拖拽模式（将 PDF 拖到图标上）
> - **PDF笔记生成器(GUI)** — 图形界面（双击打开）

**方式二：手动安装**

```bash
# 1. 创建虚拟环境
python -m venv venv

# 2. 激活虚拟环境
venv\Scripts\activate

# 3. 安装依赖
pip install -e .
```

---

## ⚙️ 配置

### 1. 配置 API 密钥

复制 `.env.example` 为 `.env`，填入你的 API 密钥：

```bash
copy .env.example .env
```

编辑 `.env` 文件：

```ini
# Kimi（推荐，性价比高）
KIMI_API_KEY=your-kimi-api-key-here

# 或 OpenAI
OPENAI_API_KEY=sk-your-openai-api-key-here

# 或 Claude
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here

# 默认 AI 提供商
DEFAULT_PROVIDER=kimi
```

> 🔑 **获取 API Key**：
> - Kimi：[https://platform.moonshot.cn/](https://platform.moonshot.cn/)
> - OpenAI：[https://platform.openai.com/](https://platform.openai.com/)
> - Claude：[https://console.anthropic.com/](https://console.anthropic.com/)

### 2. 配置 Obsidian Vault（可选）

如果使用 Obsidian 输出模式，需要配置 Vault 路径：

- **GUI 模式**：在界面的 Obsidian 面板中填写 Vault 根目录路径
- **安装时配置**：运行 `install.bat` 时选择配置 Vault 路径

> Vault 结构要求：
> ```
> 📁 Obsidian/
>  ├── 📁 Chemistry/          ← 学科分类文件夹
>  │   ├── 📁 Quantum-Chemistry/  ← 课程文件夹
>  │   │   └── qmLecture 4.md
>  │   └── 📁 Organic-Chemistry/
>  └── 📁 Mathematics/
>      └── 📁 Calculus/
> ```

---

## 🎯 使用方法

### 方式一：拖拽模式（最快）

1. 将 PDF 文件拖到桌面 **「PDF笔记生成器」** 图标上
2. 程序自动处理，生成的笔记保存在 `notes/` 文件夹
3. 支持同时拖拽多个 PDF 文件批量处理

### 方式二：GUI 图形界面（推荐）

1. 双击桌面 **「PDF笔记生成器(GUI)」** 图标
2. 在界面中：

   | 步骤 | 操作 |
   |------|------|
   | ① | 拖拽 PDF 文件到拖放区域，或点击选择文件 |
   | ② | 选择 AI 提供商（Kimi / OpenAI / Claude） |
   | ③ | 选择输出格式（Word / Markdown / HTML / **Obsidian**） |
   | ④ | 选择 Obsidian 笔记模板和 Vault 路径（仅 Obsidian 模式） |
   | ⑤ | 点击 **「开始生成」** |

3. 处理完成后，可在设置的输出文件夹中找到笔记

### 方式三：命令行模式

```bash
# 激活虚拟环境
venv\Scripts\activate

# 处理单个 PDF（生成 Word 文档）
pdf-summarizer process 课件.pdf

# 指定 AI 提供商
pdf-summarizer process 课件.pdf --provider kimi

# 生成 Obsidian 笔记
pdf-summarizer process 课件.pdf \
    --format obsidian \
    --template config/templates/quantum-template.md \
    --course "量子化学" \
    --vault "E:\Obsidian\collegenote"

# 批量处理目录
pdf-summarizer batch PDF课件文件夹/
```

---

## 📖 输出格式说明

### Word 文档（docx）

默认输出格式，包含结构化笔记：
- 核心概念与定义
- 知识点详解
- 重点难点
- 复习建议

### Obsidian 笔记（obsidian）

输出格式化的 Markdown 笔记，直接保存到 Obsidian Vault：

```
📁 Vault/Chemistry/Quantum-Chemistry/
  └── qmLecture 4.md          ← AI 生成的笔记
```

**Obsidian 模式的特殊功能：**
- 笔记模板驱动（自定义 `.md` 模板）
- LaTeX 公式自动修复（`\(...\)` → `$...$`，清除多余 `$`）
- 公式规范检查（大括号匹配、`\$` 转义清理）
- 详细规则见 [config/latex_format_rules.md](config/latex_format_rules.md)

---

## 📁 项目结构

```
noter/
├── gui_launcher.py              # GUI 入口
├── gui_launcher/                # GUI 组件
│   ├── obsidian_panel.py        # Obsidian 配置面板
│   ├── settings_page.py         # 设置页面
│   └── ...
├── src/pdf_summarizer/          # 核心代码
│   ├── cli.py                   # 命令行入口
│   ├── obsidian_generator.py    # Obsidian 笔记生成 + LaTeX 修复
│   ├── vault_indexer.py         # Obsidian Vault 扫描
│   └── ...
├── config/                      # 配置文件
│   ├── prompts.yaml             # AI 提示词模板
│   ├── latex_format_rules.md    # LaTeX 格式规范（发给 AI 参考）
│   └── templates/               # 笔记模板
├── install.bat                  # 一键安装脚本
├── uninstall.bat                # 卸载脚本
├── launch_noter.bat             # 启动 GUI
└── 一键生成笔记.bat             # 拖拽启动入口
```

---

## ❓ 常见问题

### Q: 打开软件后提示"未配置 API Key"？

A: 点击界面右上角的 **「设置」** 按钮，在 AI 设置页面填入你的 API Key。

### Q: Obsidian 模式下的公式乱码？

A: 程序已内置 LaTeX 修复功能，会自动处理常见的公式格式问题。详细规则见 [config/latex_format_rules.md](config/latex_format_rules.md)。

### Q: 找不到输出文件？

A: 默认输出在项目目录的 `notes/` 文件夹。可在设置中自定义输出路径。

### Q: 批量处理时某个文件失败？

A: 程序会跳过失败的文件继续处理，日志会显示具体错误原因。

---

## 📝 许可证

MIT License
