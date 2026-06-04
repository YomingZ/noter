# 📚 PDF 笔记生成器（Noter）

> 🎯 基于 AI 的 PDF 课件智能总结工具 — 拖进去，笔记出来！

支持 **Kimi / OpenAI / Claude / DeepSeek** 多 AI 提供商，可输出 **Word / Markdown / HTML / Obsidian 笔记**。
提供 **GUI 图形界面**、**命令行批量处理**、**拖拽即生成** 三种使用方式。

---

## ✨ 功能亮点

| 功能 | 说明 |
|------|------|
| 📄 **PDF 智能提取** | 高精度文本提取，支持章节结构识别和图片 OCR |
| 🤖 **多 AI 提供商** | Kimi / OpenAI / Claude / DeepSeek / 自定义，一键切换 |
| 📝 **多种输出格式** | Word (.docx)、Markdown (.md)、HTML、Obsidian 笔记 |
| 📁 **批量处理** | 一次拖入最多 50 个 PDF，自动排队处理 |
| 🏛️ **Obsidian 深度集成** | 自动扫描 Vault 课程结构，模板驱动笔记生成 |
| 🔍 **模板智能分析** | AI 自动分析模板风格 → 优化提示词 → 提升笔记质量 |
| 📐 **LaTeX 公式修复** | 自动修复公式格式，保证 Obsidian 中完美渲染 |
| 🎨 **现代化 GUI** | Windows 11 风格界面，支持浅色/深色主题切换 |
| ⚡ **拖拽即生成** | 把 PDF 拖到桌面图标上，一键生成无需开软件 |
| 📊 **冲刺模式** | 专为考试设计的精简笔记生成模式 |

---

## 🚀 快速安装（Windows）

### 前置要求

- **Windows 10/11**
- **Python 3.9 或更高版本**（[下载 Python](https://www.python.org/downloads/)）
  - 安装时请勾选 **"Add Python to PATH"**

### 方式一：一键安装（推荐）

双击项目目录中的 `install.bat`，脚本会自动完成全部配置：

```
✅ 检测 Python 环境
✅ 创建虚拟环境（venv）
✅ 安装所有依赖
✅ 创建桌面快捷方式
✅ 引导配置 API 密钥和 Obsidian Vault 路径
```

安装完成后，桌面上会出现两个快捷方式：

| 快捷方式 | 用途 |
|---------|------|
| **PDF笔记生成器** | 🖱️ 拖拽模式 — 将 PDF 拖到图标上直接生成 |
| **PDF笔记生成器(GUI)** | 🎨 图形界面 — 双击打开完整功能界面 |

### 方式二：手动安装

```bash
# 1. 创建虚拟环境
python -m venv venv

# 2. 激活虚拟环境
venv\Scripts\activate

# 3. 安装依赖
pip install -e .
```

---

## ⚙️ 配置指南

### 1️⃣ 配置 API 密钥（必须）

复制 `.env.example` 为 `.env`，填入你的 API 密钥：

```bash
copy .env.example .env
```

编辑 `.env` 文件：

```ini
# Kimi（推荐，性价比高）
KIMI_API_KEY=your-kimi-api-key-here

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key-here

# Claude
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here

# DeepSeek（高性价比）
DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here

# 默认 AI 提供商
DEFAULT_PROVIDER=kimi
```

> 🔑 **获取 API Key**：
> - Kimi：[https://platform.moonshot.cn/](https://platform.moonshot.cn/)
> - OpenAI：[https://platform.openai.com/](https://platform.openai.com/)
> - Claude：[https://console.anthropic.com/](https://console.anthropic.com/)
> - DeepSeek：[https://platform.deepseek.com/](https://platform.deepseek.com/)

> 💡 **提示**：首次启动 GUI 时，如果未配置 API Key，会自动弹出引导提示。

### 2️⃣ Obsidian Vault 配置（可选）

使用 Obsidian 输出模式时，需要配置 Vault 路径：

```
📁 collegenote/                     ← Vault 根目录
  ├── 📁 Physics/
  │   ├── 📁 University-Physics-2/  ← 课程文件夹
  │   │   └── Electric Current.md  ← 生成的笔记
  │   └── 📁 ...
  ├── 📁 Chemistry/
  │   ├── 📁 Organic-Chemistry/
  └── 📁 Mathematics/
```

---

## 🎯 使用方法

### 方式一：GUI 图形界面（推荐）

双击桌面 **「PDF笔记生成器(GUI)」** 图标启动。

#### 主界面操作流程

```
┌─────────────────────────────────────────────────┐
│  📄 拖拽 PDF 文件到此处                                 │
│  （或点击选择文件）                                      │
├─────────────────────────────────────────────────┤
│  🤖 AI 提供商  [Kimi ▼]   📝 输出格式  [Obsidian ▼]  │
├─────────────────────────────────────────────────┤
│  📝 Obsidian 笔记生成                                    │
│  ┌─ Step 1: 选择笔记模板 ──────────────────────┐        │
│  │  [选择模板] [编辑] [🔍 分析]                   │       │
│  └──────────────────────────────────────────────┘        │
│  ┌─ Step 2: Vault 路径 ─────────────────────────┐       │
│  │  [浏览]                                         │      │
│  └──────────────────────────────────────────────┘        │
│  ┌─ Step 3: 课程名称 ───────────────────────────┐       │
│  │  [🎓 选择或输入课程...]                           │      │
│  └──────────────────────────────────────────────┘        │
│  ┌─ Step 4: 笔记名称 ───────────────────────────┐       │
│  │  [自定义文件名（可选）]                              │      │
│  └──────────────────────────────────────────────┘        │
├─────────────────────────────────────────────────┤
│  日志面板（实时显示处理进度）                              │
├─────────────────────────────────────────────────┤
│              [❓]  [取消]  [开始生成]                 │
└─────────────────────────────────────────────────┘
```

**步骤详解：**

| 步骤 | 操作 | 说明 |
|:---:|------|------|
| ① | 拖入 PDF | 将课件 PDF 拖入上方区域，或点击选择文件 |
| ② | 选择 AI 提供商 | Kimi / OpenAI / Claude / DeepSeek |
| ③ | 选择输出格式 | Word / Markdown / HTML / **Obsidian** |
| ④ | 配置模板（Obsidian） | 选择 .md 模板文件，点击「🔍 分析」自动优化 |
| ⑤ | 配置 Vault（Obsidian） | 选择 Obsidian 库根目录，自动加载课程列表 |
| ⑥ | 选择课程 | 从 Vault 自动扫描的课程列表中选择 |
| ⑦ | 点击「开始生成」 | 🚀 等待处理完成 |

### 方式二：拖拽模式（最快）

将 PDF 文件直接拖到桌面 **「PDF笔记生成器」** 图标上，程序自动处理并生成笔记。

- 支持同时拖拽多个 PDF 批量处理
- 生成的笔记默认保存在 `Desktop/Noter_Notes/` 目录

### 方式三：命令行模式

```bash
# 激活虚拟环境
venv\Scripts\activate

# 处理单个 PDF（生成 Word 文档）
pdf-summarizer process 课件.pdf

# 指定 AI 提供商和输出格式
pdf-summarizer process 课件.pdf --provider deepseek --format obsidian

# 生成 Obsidian 笔记（带模板和课程信息）
pdf-summarizer process 课件.pdf \
    --format obsidian \
    --template custom-template.md \
    --course "量子化学" \
    --vault "E:\Obsidian\collegenote"

# 批量处理整个目录
pdf-summarizer batch PDF课件文件夹/

# 交互式向导模式（新手推荐）
pdf-summarizer wizard
```

---

## 🔍 模板智能分析系统

Noter 的特色功能 — **AI 驱动的模板分析引擎**，让你的笔记风格始终如一。

### 工作流程

```
┌──────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────┐
│ 选择模板  │ → │ 规则引擎扫描  │ → │ AI 深度分析   │ → │ 配置确认  │
│  .md 文件 │   │ 12项特征检测 │   │ 风格识别+建议 │   │ 用户调整  │
└──────────┘   └──────────────┘   └──────────────┘   └──────────┘
```

### 检测内容

| 检测项 | 说明 |
|------|------|
| ✅ YAML Front Matter | 元数据管理标准化 |
| ✅ 核心主题摘要 | 快速理解笔记要点 |
| ✅ 重要概念表格 | 构建知识框架 |
| ✅ 中文习题标题 | 规范化题目格式 |
| ✅ 子问题格式 | 结构化嵌套问题 |
| ✅ 解答标记 | 清晰区分题目答案 |
| ✅ `\boxed{}` 答案 | LaTeX 框选重点结果 |
| ✅ 要点提示框 | 教学价值突出 |
| ✅ 跨笔记双链接 | 构建知识网络 |
| ✅ 题型总结表 | 复习效率提升 |
| ✅ 公式速查表 | 快速查阅公式 |

### 使用方式

1. 在 GUI 中选择 Obsidian 格式
2. 点击「选择模板」选择一个 `.md` 模板文件
3. 点击「**🔍 分析**」按钮
4. AI 自动分析模板风格 → 弹出配置确认对话框
5. 确认或调整配置 → 点击「应用」
6. 开始生成笔记

> 💡 分析结果会自动缓存，同一模板再次分析无需重复调用 AI。

---

## 🏛️ Obsidian 笔记特殊功能

### 模板编辑器

内置 Markdown 模板编辑器，支持直接创建和编辑模板文件：

- 语法高亮（Markdown 语法）
- 实时编辑保存
- 支持从零创建新模板

### LaTeX 公式自动修复

针对 Obsidian 特有的 LaTeX 渲染规则，自动处理：

- `\(...\)` → `$...$` 行内公式转换
- `\[...\]` → `$$...$$` 块级公式转换
- 大括号匹配检查和修复（`cases` 环境等）
- 多余 `\$` 转义清理
- `\begin{align}` 等环境保护

### 输出笔记结构

生成的笔记遵循模板结构，包含：

```markdown
---
title: 课程名称
date: 2024-01-01
tags: [课程, 笔记]
---

# 标题

## 核心概念

...

## 知识点详解

...

## 习题与解答

1. **题目**
   - 子问题 a
   - 子问题 b
   > [!answer]-
   > \boxed{答案}
```

---

## 🎨 GUI 界面特性

| 特性 | 说明 |
|------|------|
| 🎯 **Windows 11 风格** | 圆角、阴影、分割控件、现代化配色 |
| 🌓 **深色/浅色主题** | 跟随系统或手动切换 |
| 📋 **实时日志面板** | 终端风格日志，支持错误/成功/信息分级 |
| 📂 **文件列表管理** | 拖拽排序、删除、进度显示 |
| 🏷️ **配置文件系统** | 多配置文件保存/切换，设置持久化 |
| 🔑 **API Key 安全存储** | Fernet 加密存储，非明文保存 |
| 🎬 **页面过渡动画** | 滑动切换、淡入展开等流畅动画 |
| ❓ **帮助系统** | 内置常见问题解答弹窗 |

### 设置页面

| 配置项 | 说明 |
|-------|------|
| 🤖 **AI 配置** | 提供商、API Key、模型、Base URL、温度 |
| 📄 **输出设置** | 格式、详细程度（精简/详细/冲刺）、例题/清单/页码 |
| 💾 **存储设置** | 输出目录、Obsidian Vault、保留 Markdown 副本 |
| 🎨 **界面设置** | 主题（跟随系统/浅色/深色） |
| 📂 **配置文件** | 多配置保存/切换/删除 |

---

## 📁 项目结构

```
noter/
├── gui_launcher.py                 # GUI 主入口
├── gui_launcher/                   # GUI 组件包
│   ├── obsidian_panel.py          # Obsidian 配置面板
│   ├── settings_page.py           # 设置页面
│   ├── settings_manager.py        # 设置管理器（单例+加密）
│   ├── drop_area.py               # 文件拖放区域
│   ├── file_list_area.py          # 文件列表管理
│   ├── file_card.py               # 文件卡片组件
│   ├── log_panel.py               # 日志面板
│   ├── template_editor.py         # 模板编辑器
│   ├── template_config_dialog.py  # 模板分析配置对话框
│   ├── template_analysis_integration.py  # 模板分析与主窗口集成
│   ├── theme.py                   # 主题系统
│   ├── widget_factory.py          # UI 组件工厂
│   └── title_bar.py               # 自定义标题栏
├── src/pdf_summarizer/            # 核心库
│   ├── cli.py                     # 命令行入口
│   ├── cli_wizard.py              # 交互式向导
│   ├── processing_service.py      # 处理服务（统一调度）
│   ├── ai_client.py               # AI 客户端（多提供商）
│   ├── obsidian_generator.py      # Obsidian 笔记生成
│   ├── template_analyzer.py       # 模板分析引擎
│   ├── pdf_reader.py              # PDF 读取
│   ├── summarizer.py              # 内容总结
│   ├── summary_parser.py          # 总结解析
│   ├── docx_writer.py             # Word 文档生成
│   ├── latex_renderer.py          # LaTeX 渲染
│   ├── latex_to_omml.py           # LaTeX → OMML 转换
│   ├── vault_indexer.py           # Vault 扫描索引
│   ├── vault_service.py           # Vault 服务
│   ├── rate_limiter.py            # API 速率限制
│   ├── cache.py                   # 缓存管理器
│   ├── chunking.py                # 文本分块
│   ├── config.py                  # 配置管理
│   ├── models.py                  # 数据模型
│   ├── exam_analyzer.py           # 考试分析
│   ├── incremental.py             # 增量处理
│   └── output_formats.py          # 输出格式定义
├── config/                        # 配置文件
│   ├── prompts.yaml              # AI 提示词模板
│   ├── prompts_subjects.yaml     # 学科专属提示词
│   ├── latex_format_rules.md     # LaTeX 格式规范
│   └── profiles/                  # 用户配置文件
├── tests/                         # 测试套件
│   └── *.py                      # 24 个测试文件
├── assets/                        # 资源文件
│   └── *.ico / *.png             # 应用图标
├── install.bat                    # 一键安装脚本
├── uninstall.bat                  # 卸载脚本
├── launch_noter.bat               # 启动 GUI
├── 一键生成笔记.bat               # 拖拽启动入口
├── pyproject.toml                 # 项目配置
└── requirements.txt               # 依赖清单
```

---

## 📝 输出格式说明

### Word 文档 (.docx)

默认输出格式，包含结构化笔记：
- 核心概念与定义
- 知识点详解
- 重点难点标注
- 复习建议

### Markdown (.md)

纯 Markdown 格式，适合在任意编辑器中浏览。

### HTML

网页格式，可直接在浏览器中查看。

### Obsidian 笔记

针对 Obsidian 优化的 Markdown 笔记：
- **模板驱动** — 使用自定义 .md 模板控制输出风格
- **YAML Front Matter** — 自动生成元数据（标题、日期、标签）
- **双向链接** — `[[WikiLink]]` 格式支持知识网络
- **LaTeX 公式** — `$...$` / `$$...$$` Obsidian 原生渲染
- **Callout 提示框** — `> [!answer]-` 等增强可读性

---

## 🧪 测试

项目包含 24+ 个测试文件，覆盖核心功能：

```bash
# 激活虚拟环境后运行测试
pytest tests/

# 带覆盖率报告
pytest tests/ --cov=src/pdf_summarizer --cov-report=html
```

---

## ❓ 常见问题

### Q: 打开软件后提示"未配置 API Key"？

A: 首次启动时会自动弹窗引导配置。如果跳过了，点击界面中的 **「⚙️ 设置」** 按钮或在底部操作栏点击 **「❓」** 查看帮助。

### Q: 支持哪些 AI 提供商？

A: 支持 **Kimi**（推荐，高性价比）、**OpenAI**（GPT-4o）、**Claude**（Sonnet）、**DeepSeek**（高性价比），以及自定义兼容 OpenAI 接口的服务。

### Q: 生成的笔记格式不对怎么办？

A: 使用 **Obsidian 模式** 时，建议先选择一个已有的优质笔记作为模板，点击「**🔍 分析**」让 AI 自动识别并优化。

### Q: 生成的笔记在哪里？

A: 默认保存在 `Desktop/Noter_Notes/` 目录。可在「⚙️ 设置」→「存储设置」中自定义输出目录。

### Q: Obsidian 模式下公式乱码？

A: 程序内置了 LaTeX 修复功能，会自动处理常见格式问题。详细规范见 [config/latex_format_rules.md](config/latex_format_rules.md)。

### Q: 批量处理时某个文件失败了？

A: 程序会跳过失败的文件继续处理，日志面板会显示具体错误原因。

---

## 📋 开发计划

- [x] 基础 PDF 提取与 AI 总结
- [x] 多 AI 提供商支持
- [x] Obsidian 笔记集成
- [x] 模板智能分析系统
- [x] LaTeX 公式自动修复
- [x] 深色/浅色主题
- [x] 配置文件管理系统
- [ ] 自定义输出模板市场
- [ ] 多语言笔记生成支持
- [ ] 移动端适配（iOS/Android Shortcuts）

---

## 📄 许可证

MIT License © 2024 YomingZ

---

<p align="center">
  <b>如果这个项目对你有帮助，欢迎给个 ⭐️ Star！</b>
</p>
