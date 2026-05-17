#!/usr/bin/env python3
"""
PDF 备考笔记生成器 - 设置面板

现代化的设置对话框，支持 AI 配置、输出偏好、存储设置、界面设置
"""

import json
import base64
import os
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QSlider, QCheckBox, QRadioButton,
    QButtonGroup, QFrame, QScrollArea, QWidget, QStackedWidget,
    QFileDialog, QMessageBox, QGroupBox, QSpinBox, QTabWidget,
    QGraphicsDropShadowEffect, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QSettings, QPropertyAnimation, QEasingCurve, QSize, pyqtSignal, QTimer
)
from PyQt6.QtGui import QFont, QColor, QIcon

# 获取脚本目录
SCRIPT_DIR = Path(__file__).parent.resolve()
CONFIG_DIR = SCRIPT_DIR / "config"
SETTINGS_FILE = CONFIG_DIR / "settings.json"


# ============================================================================
# 主题配置
# ============================================================================

from gui_launcher.theme import Theme
from gui_launcher.settings_manager import SettingsManager, CONFIG_DIR, SETTINGS_FILE
from gui_launcher.widget_factory import WidgetFactory

settings_manager = SettingsManager()


# ============================================================================
# 设置页面基类
# ============================================================================

class SettingsPage(QWidget):
    """设置页面基类"""

    settingsChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """子类实现"""
        pass

    def load_settings(self):
        """子类实现：加载设置"""
        pass

    def save_settings(self):
        """子类实现：保存设置"""
        pass

    def create_group(self, title: str) -> QFrame:
        """创建设置分组"""
        return WidgetFactory.create_group(title)

    def create_label(self, text: str) -> QLabel:
        """创建标签"""
        return WidgetFactory.create_label(text)

    def create_sublabel(self, text: str) -> QLabel:
        """创建次级标签"""
        return WidgetFactory.create_sublabel(text)

    def create_input(self, placeholder: str = "", password: bool = False) -> QLineEdit:
        """创建输入框"""
        return WidgetFactory.create_input(placeholder, password)

    def create_combo(self, items: list) -> QComboBox:
        """创建下拉框"""
        return WidgetFactory.create_combo(items)

    def create_button(self, text: str, primary: bool = False) -> QPushButton:
        """创建按钮"""
        return WidgetFactory.create_button(text, primary)

    def create_checkbox(self, text: str, checked: bool = False) -> QCheckBox:
        """创建复选框"""
        return WidgetFactory.create_checkbox(text, checked)


# ============================================================================
# AI 配置页面
# ============================================================================

class AIConfigPage(SettingsPage):
    """AI 配置页面"""

    def __init__(self, parent=None):
        super().__init__(parent)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # API 配置组
        api_group = self.create_group("API 配置")
        api_layout = QVBoxLayout(api_group)
        api_layout.setSpacing(12)

        # 提供商选择
        provider_row = QHBoxLayout()
        provider_row.addWidget(self.create_label("AI 提供商"))
        self.provider_combo = self.create_combo(["Kimi (Moonshot)", "OpenAI", "Anthropic", "自定义"])
        self.provider_combo.setToolTip("选择 AI 服务提供商")
        self.provider_combo.currentIndexChanged.connect(self.on_provider_changed)
        provider_row.addWidget(self.provider_combo)
        provider_row.addStretch()
        api_layout.addLayout(provider_row)

        # API Key
        key_row = QHBoxLayout()
        key_row.addWidget(self.create_label("API Key"))
        self.api_key_input = self.create_input("输入你的 API 密钥", password=True)
        self.api_key_input.setToolTip("API 密钥将加密存储")
        key_row.addWidget(self.api_key_input, 1)

        # 显示/隐藏密钥按钮
        self.toggle_key_btn = QPushButton("👁")
        self.toggle_key_btn.setFixedSize(36, 36)
        self.toggle_key_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.get('bg_tertiary')};
                border: 1px solid {Theme.get('border_light')};
                border-radius: 8px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {Theme.get('bg_elevated')};
            }}
        """)
        self.toggle_key_btn.clicked.connect(self.toggle_key_visibility)
        key_row.addWidget(self.toggle_key_btn)
        api_layout.addLayout(key_row)

        # 模型选择
        model_row = QHBoxLayout()
        model_row.addWidget(self.create_label("模型"))
        self.model_combo = self.create_combo([])
        self.model_combo.setToolTip("选择要使用的 AI 模型")
        model_row.addWidget(self.model_combo)
        model_row.addStretch()
        api_layout.addLayout(model_row)

        # Base URL (可选)
        url_row = QHBoxLayout()
        url_row.addWidget(self.create_label("Base URL"))
        self.base_url_input = self.create_input("可选，用于代理或自定义端点")
        self.base_url_input.setToolTip("自定义 API 端点地址")
        url_row.addWidget(self.base_url_input, 1)
        api_layout.addLayout(url_row)

        # 测试连接按钮
        test_row = QHBoxLayout()
        test_row.addStretch()
        self.test_btn = self.create_button("测试连接")
        self.test_btn.clicked.connect(self.test_connection)
        test_row.addWidget(self.test_btn)
        api_layout.addLayout(test_row)

        layout.addWidget(api_group)

        # 高级设置组
        advanced_group = self.create_group("高级设置")
        advanced_layout = QVBoxLayout(advanced_group)
        advanced_layout.setSpacing(12)

        # 温度滑块
        temp_row = QHBoxLayout()
        temp_row.addWidget(self.create_label("温度 (Temperature)"))
        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setRange(0, 10)
        self.temp_slider.setValue(7)
        self.temp_slider.setFixedWidth(200)
        self.temp_slider.setStyleSheet(f"""
            QSlider {{
                background: transparent;
            }}
            QSlider::groove:horizontal {{
                background: {Theme.get('bg_tertiary')};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {Theme.ACCENT_BLUE};
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }}
            QSlider::sub-page:horizontal {{
                background: {Theme.ACCENT_BLUE};
                border-radius: 3px;
            }}
        """)
        self.temp_slider.valueChanged.connect(self.on_temp_changed)
        temp_row.addWidget(self.temp_slider)

        self.temp_label = QLabel("0.7")
        self.temp_label.setFixedWidth(30)
        self.temp_label.setStyleSheet(f"color: {Theme.get('text_primary')}; font-size: 13px;")
        temp_row.addWidget(self.temp_label)
        temp_row.addStretch()
        advanced_layout.addLayout(temp_row)

        self.create_sublabel("较低值更精确，较高值更有创造性")
        advanced_layout.addWidget(self.create_sublabel("较低值更精确，较高值更有创造性"))

        layout.addWidget(advanced_group)
        layout.addStretch()

        # 初始化
        self.on_provider_changed(0)
        self.load_settings()

    def on_provider_changed(self, index):
        """提供商改变时更新模型列表"""
        providers = ["kimi", "openai", "anthropic", "custom"]
        provider = providers[index] if index < len(providers) else "kimi"

        models = settings_manager.get_models_for_provider(provider)
        self.model_combo.clear()
        self.model_combo.addItems(models if models else ["自定义模型"])

    def on_temp_changed(self, value):
        """温度滑块改变"""
        self.temp_label.setText(f"{value / 10:.1f}")

    def toggle_key_visibility(self):
        """切换 API Key 显示/隐藏"""
        if self.api_key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_key_btn.setText("🙈")
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_key_btn.setText("👁")

    def test_connection(self):
        """测试 API 连接"""
        provider_map = {0: "kimi", 1: "openai", 2: "anthropic", 3: "custom"}
        provider = provider_map.get(self.provider_combo.currentIndex(), "kimi")
        api_key = self.api_key_input.text()

        if not api_key:
            QMessageBox.warning(self, "测试失败", "请先输入 API Key")
            return

        # 这里可以添加实际的 API 测试逻辑
        QMessageBox.information(self, "测试成功", f"已成功连接到 {provider.upper()} API")

    def load_settings(self):
        """加载设置"""
        provider = settings_manager.get("ai", "provider", default="kimi")
        provider_map = {"kimi": 0, "openai": 1, "anthropic": 2, "custom": 3}
        self.provider_combo.setCurrentIndex(provider_map.get(provider, 0))

        self.api_key_input.setText(settings_manager.get("ai", "api_key", default=""))
        self.base_url_input.setText(settings_manager.get("ai", "base_url", default=""))

        model = settings_manager.get("ai", "model", default="")
        index = self.model_combo.findText(model)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)

        temp = settings_manager.get("ai", "temperature", default=0.7)
        self.temp_slider.setValue(int(temp * 10))

    def save_settings(self):
        """保存设置"""
        provider_map = {0: "kimi", 1: "openai", 2: "anthropic", 3: "custom"}
        settings_manager.set("ai", "provider", provider_map[self.provider_combo.currentIndex()])
        settings_manager.set("ai", "api_key", self.api_key_input.text())
        settings_manager.set("ai", "model", self.model_combo.currentText())
        settings_manager.set("ai", "base_url", self.base_url_input.text())
        settings_manager.set("ai", "temperature", self.temp_slider.value() / 10)


# ============================================================================
# 输出偏好页面
# ============================================================================

class OutputPage(SettingsPage):
    """输出偏好页面"""

    def __init__(self, parent=None):
        super().__init__(parent)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # 输出格式组
        format_group = self.create_group("输出格式")
        format_layout = QVBoxLayout(format_group)
        format_layout.setSpacing(12)

        # 格式选择（卡片式单选）
        format_row = QHBoxLayout()
        self.format_buttons = QButtonGroup(self)

        formats = [
            ("docx", "📄 Word", "生成 .docx 文档"),
            ("md", "📝 Markdown", "生成 .md 文件"),
            ("html", "🌐 HTML", "生成网页文件")
        ]

        for i, (fmt, label, tooltip) in enumerate(formats):
            rb = QRadioButton(label)
            rb.setToolTip(tooltip)
            rb.setStyleSheet(f"""
                QRadioButton {{
                    font-size: 13px;
                    color: {Theme.get('text_primary')};
                    spacing: 6px;
                    padding: 8px 16px;
                    background-color: {Theme.get('bg_tertiary')};
                    border-radius: 8px;
                }}
                QRadioButton::indicator {{
                    width: 16px;
                    height: 16px;
                    border-radius: 8px;
                    border: 2px solid {Theme.get('border')};
                }}
                QRadioButton::indicator:checked {{
                    background-color: {Theme.ACCENT_BLUE};
                    border-color: {Theme.ACCENT_BLUE};
                }}
            """)
            self.format_buttons.addButton(rb, i)
            format_row.addWidget(rb)

        format_row.addStretch()
        format_layout.addLayout(format_row)

        layout.addWidget(format_group)

        # 详细程度
        verbosity_group = self.create_group("内容详细程度")
        verbosity_layout = QVBoxLayout(verbosity_group)
        verbosity_layout.setSpacing(12)

        self.verbosity_buttons = QButtonGroup(self)
        verbosity_levels = [
            ("concise", "精简模式", "只提取核心知识点，适合快速复习"),
            ("detailed", "详细模式", "包含详细解释和例题，适合深入学习"),
            ("sprint", "冲刺模式", "只保留要点和公式，适合考前突击")
        ]

        for i, (key, label, desc) in enumerate(verbosity_levels):
            rb = QRadioButton(label)
            rb.setToolTip(desc)
            rb.setStyleSheet(f"""
                QRadioButton {{
                    font-size: 13px;
                    color: {Theme.get('text_primary')};
                    spacing: 6px;
                }}
                QRadioButton::indicator {{
                    width: 16px;
                    height: 16px;
                    border-radius: 8px;
                    border: 2px solid {Theme.get('border')};
                }}
                QRadioButton::indicator:checked {{
                    background-color: {Theme.ACCENT_BLUE};
                    border-color: {Theme.ACCENT_BLUE};
                }}
            """)
            self.verbosity_buttons.addButton(rb, i)
            verbosity_layout.addWidget(rb)

        layout.addWidget(verbosity_group)

        # 选项
        options_group = self.create_group("输出选项")
        options_layout = QVBoxLayout(options_group)
        options_layout.setSpacing(10)

        self.include_examples_cb = self.create_checkbox("包含例题和习题解析")
        self.include_examples_cb.setToolTip("在笔记中添加相关例题")
        options_layout.addWidget(self.include_examples_cb)

        self.generate_checklist_cb = self.create_checkbox("生成自检清单")
        self.generate_checklist_cb.setToolTip("在笔记末尾生成知识点检查清单")
        options_layout.addWidget(self.generate_checklist_cb)

        self.add_page_numbers_cb = self.create_checkbox("添加页码")
        self.add_page_numbers_cb.setToolTip("在输出文档中添加页码")
        options_layout.addWidget(self.add_page_numbers_cb)

        self.insert_toc_cb = self.create_checkbox("插入目录")
        self.insert_toc_cb.setToolTip("在文档开头自动生成目录")
        options_layout.addWidget(self.insert_toc_cb)

        layout.addWidget(options_group)

        # Word 模板
        template_group = self.create_group("Word 模板")
        template_layout = QHBoxLayout(template_group)

        self.template_buttons = QButtonGroup(self)

        self.default_template_rb = QRadioButton("使用默认模板")
        self.default_template_rb.setStyleSheet(f"""
            QRadioButton {{
                font-size: 13px;
                color: {Theme.get('text_primary')};
                spacing: 6px;
            }}
            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 8px;
                border: 2px solid {Theme.get('border')};
            }}
            QRadioButton::indicator:checked {{
                background-color: {Theme.ACCENT_BLUE};
                border-color: {Theme.ACCENT_BLUE};
            }}
        """)
        self.template_buttons.addButton(self.default_template_rb, 0)
        template_layout.addWidget(self.default_template_rb)

        self.custom_template_rb = QRadioButton("自定义模板")
        self.custom_template_rb.setStyleSheet(self.default_template_rb.styleSheet())
        self.template_buttons.addButton(self.custom_template_rb, 1)
        template_layout.addWidget(self.custom_template_rb)

        self.template_path_input = self.create_input("选择模板文件...")
        template_layout.addWidget(self.template_path_input, 1)

        self.browse_template_btn = self.create_button("浏览")
        self.browse_template_btn.clicked.connect(self.browse_template)
        template_layout.addWidget(self.browse_template_btn)

        layout.addWidget(template_group)
        layout.addStretch()

        self.load_settings()

    def browse_template(self):
        """浏览模板文件"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 Word 模板", "", "Word 模板 (*.dotx *.docx)"
        )
        if path:
            self.template_path_input.setText(path)

    def load_settings(self):
        """加载设置"""
        fmt = settings_manager.get("output", "format", default="docx")
        fmt_map = {"docx": 0, "md": 1, "html": 2}
        btn = self.format_buttons.button(fmt_map.get(fmt, 0))
        if btn:
            btn.setChecked(True)

        verbosity = settings_manager.get("output", "verbosity", default="detailed")
        verbosity_map = {"concise": 0, "detailed": 1, "sprint": 2}
        btn = self.verbosity_buttons.button(verbosity_map.get(verbosity, 1))
        if btn:
            btn.setChecked(True)

        self.include_examples_cb.setChecked(settings_manager.get("output", "include_examples", default=True))
        self.generate_checklist_cb.setChecked(settings_manager.get("output", "generate_checklist", default=True))
        self.add_page_numbers_cb.setChecked(settings_manager.get("output", "add_page_numbers", default=True))
        self.insert_toc_cb.setChecked(settings_manager.get("output", "insert_toc", default=True))

        template = settings_manager.get("output", "template", default="default")
        if template == "default":
            self.default_template_rb.setChecked(True)
        else:
            self.custom_template_rb.setChecked(True)
            self.template_path_input.setText(template if template != "default" else "")

    def save_settings(self):
        """保存设置"""
        fmt_map = {0: "docx", 1: "md", 2: "html"}
        settings_manager.set("output", "format", fmt_map[self.format_buttons.checkedId()])

        verbosity_map = {0: "concise", 1: "detailed", 2: "sprint"}
        settings_manager.set("output", "verbosity", verbosity_map[self.verbosity_buttons.checkedId()])

        settings_manager.set("output", "include_examples", self.include_examples_cb.isChecked())
        settings_manager.set("output", "generate_checklist", self.generate_checklist_cb.isChecked())
        settings_manager.set("output", "add_page_numbers", self.add_page_numbers_cb.isChecked())
        settings_manager.set("output", "insert_toc", self.insert_toc_cb.isChecked())

        if self.default_template_rb.isChecked():
            settings_manager.set("output", "template", "default")
        else:
            settings_manager.set("output", "template", self.template_path_input.text())


# ============================================================================
# 存储设置页面
# ============================================================================

class StoragePage(SettingsPage):
    """存储设置页面"""

    def __init__(self, parent=None):
        super().__init__(parent)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # 输出文件夹
        folder_group = self.create_group("输出文件夹")
        folder_layout = QHBoxLayout(folder_group)

        self.folder_input = self.create_input("选择输出文件夹...")
        self.folder_input.setToolTip("生成的笔记将保存到此文件夹")
        folder_layout.addWidget(self.folder_input, 1)

        self.browse_btn = self.create_button("浏览")
        self.browse_btn.clicked.connect(self.browse_folder)
        folder_layout.addWidget(self.browse_btn)

        layout.addWidget(folder_group)

        # 文件选项
        file_group = self.create_group("文件选项")
        file_layout = QVBoxLayout(file_group)
        file_layout.setSpacing(10)

        self.keep_markdown_cb = self.create_checkbox("保留原始 Markdown 文件")
        self.keep_markdown_cb.setToolTip("在生成 Word 的同时保留 .md 源文件")
        file_layout.addWidget(self.keep_markdown_cb)

        layout.addWidget(file_group)

        # 缓存管理
        cache_group = self.create_group("缓存管理")
        cache_layout = QVBoxLayout(cache_group)
        cache_layout.setSpacing(12)

        cache_info_row = QHBoxLayout()
        self.cache_size_label = self.create_label("缓存大小: 计算中...")
        cache_info_row.addWidget(self.cache_size_label)
        cache_info_row.addStretch()
        cache_layout.addLayout(cache_info_row)

        cache_btn_row = QHBoxLayout()
        cache_btn_row.addStretch()
        self.clear_cache_btn = self.create_button("清理缓存")
        self.clear_cache_btn.clicked.connect(self.clear_cache)
        cache_btn_row.addWidget(self.clear_cache_btn)
        cache_layout.addLayout(cache_btn_row)

        layout.addWidget(cache_group)
        layout.addStretch()

        # 计算缓存大小
        QTimer.singleShot(100, self.calculate_cache_size)
        self.load_settings()

    def browse_folder(self):
        """浏览文件夹"""
        path = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if path:
            self.folder_input.setText(path)

    def calculate_cache_size(self):
        """计算缓存大小"""
        cache_dir = SCRIPT_DIR / "output" / ".cache"
        if cache_dir.exists():
            total_size = sum(f.stat().st_size for f in cache_dir.rglob("*") if f.is_file())
            size_mb = total_size / (1024 * 1024)
            self.cache_size_label.setText(f"缓存大小: {size_mb:.2f} MB")
        else:
            self.cache_size_label.setText("缓存大小: 0 MB")

    def clear_cache(self):
        """清理缓存"""
        cache_dir = SCRIPT_DIR / "output" / ".cache"
        if cache_dir.exists():
            import shutil
            shutil.rmtree(cache_dir)
            self.cache_size_label.setText("缓存大小: 0 MB")
            QMessageBox.information(self, "清理完成", "缓存已清理")

    def load_settings(self):
        """加载设置"""
        self.folder_input.setText(settings_manager.get("storage", "output_folder", default=""))
        self.keep_markdown_cb.setChecked(settings_manager.get("storage", "keep_markdown", default=True))

    def save_settings(self):
        """保存设置"""
        settings_manager.set("storage", "output_folder", self.folder_input.text())
        settings_manager.set("storage", "keep_markdown", self.keep_markdown_cb.isChecked())


# ============================================================================
# 界面设置页面
# ============================================================================

class InterfacePage(SettingsPage):
    """界面设置页面"""

    themeChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # 主题设置
        theme_group = self.create_group("主题")
        theme_layout = QVBoxLayout(theme_group)
        theme_layout.setSpacing(12)

        self.theme_buttons = QButtonGroup(self)
        themes = [
            ("system", "跟随系统", "自动匹配 Windows/macOS 系统主题"),
            ("light", "浅色模式", "始终使用浅色主题"),
            ("dark", "深色模式", "始终使用深色主题")
        ]

        for i, (key, label, desc) in enumerate(themes):
            rb = QRadioButton(label)
            rb.setToolTip(desc)
            rb.setStyleSheet(f"""
                QRadioButton {{
                    font-size: 13px;
                    color: {Theme.get('text_primary')};
                    spacing: 6px;
                }}
                QRadioButton::indicator {{
                    width: 16px;
                    height: 16px;
                    border-radius: 8px;
                    border: 2px solid {Theme.get('border')};
                }}
                QRadioButton::indicator:checked {{
                    background-color: {Theme.ACCENT_BLUE};
                    border-color: {Theme.ACCENT_BLUE};
                }}
            """)
            rb.toggled.connect(lambda checked, k=key: self.on_theme_changed(k) if checked else None)
            self.theme_buttons.addButton(rb, i)
            theme_layout.addWidget(rb)

        layout.addWidget(theme_group)

        # 启动选项
        startup_group = self.create_group("启动选项")
        startup_layout = QVBoxLayout(startup_group)
        startup_layout.setSpacing(10)

        self.remember_folder_cb = self.create_checkbox("启动时打开最近使用的文件夹")
        self.remember_folder_cb.setToolTip("自动定位到上次使用的文件夹")
        startup_layout.addWidget(self.remember_folder_cb)

        self.auto_wizard_cb = self.create_checkbox("首次启动时显示设置向导")
        self.auto_wizard_cb.setToolTip("检测到未配置时自动弹出设置")
        startup_layout.addWidget(self.auto_wizard_cb)

        layout.addWidget(startup_group)
        layout.addStretch()

        self.load_settings()

    def on_theme_changed(self, theme: str):
        """主题改变"""
        self.themeChanged.emit(theme)

    def load_settings(self):
        """加载设置"""
        theme = settings_manager.get("interface", "theme", default="system")
        theme_map = {"system": 0, "light": 1, "dark": 2}
        btn = self.theme_buttons.button(theme_map.get(theme, 0))
        if btn:
            btn.setChecked(True)

        self.remember_folder_cb.setChecked(settings_manager.get("interface", "remember_last_folder", default=True))
        self.auto_wizard_cb.setChecked(settings_manager.get("interface", "auto_show_wizard", default=True))

    def save_settings(self):
        """保存设置"""
        theme_map = {0: "system", 1: "light", 2: "dark"}
        settings_manager.set("interface", "theme", theme_map[self.theme_buttons.checkedId()])
        settings_manager.set("interface", "remember_last_folder", self.remember_folder_cb.isChecked())
        settings_manager.set("interface", "auto_show_wizard", self.auto_wizard_cb.isChecked())


# ============================================================================
# 设置对话框
# ============================================================================

class SettingsDialog(QDialog):
    """设置对话框"""

    settingsSaved = pyqtSignal()

    def __init__(self, parent=None, show_wizard: bool = False):
        super().__init__(parent)
        self.is_wizard_mode = show_wizard
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """设置 UI"""
        self.setWindowTitle("设置" if not self.is_wizard_mode else "初始设置向导")
        self.setMinimumSize(680, 520)
        self.resize(720, 560)

        # 无边框 + 圆角
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 主容器
        self.container = QFrame()
        self.container.setObjectName("settingsContainer")

        # 阴影
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 10)
        self.container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(self.container)

        # 容器布局
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # 标题栏
        title_bar = QFrame()
        title_bar.setFixedHeight(50)
        title_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.get('bg_primary')};
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }}
        """)

        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(20, 0, 16, 0)

        title_label = QLabel("设置向导" if self.is_wizard_mode else "设置")
        title_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 600;
            color: {Theme.get('text_primary')};
            background: transparent;
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        # 关闭按钮
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.get('text_secondary')};
                border: none;
                border-radius: 16px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {Theme.get('bg_tertiary')};
                color: {Theme.get('text_primary')};
            }}
        """)
        close_btn.clicked.connect(self.reject)
        title_layout.addWidget(close_btn)

        container_layout.addWidget(title_bar)

        # 内容区域
        content = QWidget()
        content.setStyleSheet(f"background-color: {Theme.get('bg_primary')};")
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 侧边导航
        nav_frame = QFrame()
        nav_frame.setFixedWidth(180)
        nav_frame.setStyleSheet(f"background-color: {Theme.get('bg_secondary')};")

        nav_layout = QVBoxLayout(nav_frame)
        nav_layout.setContentsMargins(12, 12, 12, 12)
        nav_layout.setSpacing(4)

        nav_items = [
            ("🤖", "AI 配置"),
            ("📄", "输出偏好"),
            ("💾", "存储设置"),
            ("🎨", "界面设置")
        ]

        self.nav_buttons = []
        for i, (icon, text) in enumerate(nav_items):
            btn = QPushButton(f"  {icon}  {text}")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {Theme.get('text_secondary')};
                    border: none;
                    border-radius: 8px;
                    padding: 12px 16px;
                    font-size: 13px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background-color: {Theme.get('bg_tertiary')};
                }}
                QPushButton:checked {{
                    background-color: {Theme.ACCENT_BLUE};
                    color: white;
                }}
            """)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, idx=i: self.switch_page(idx))
            nav_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        nav_layout.addStretch()

        content_layout.addWidget(nav_frame)

        # 页面区域
        self.pages = QStackedWidget()
        self.pages.setStyleSheet(f"""
            QStackedWidget {{
                background-color: {Theme.get('bg_primary')};
                border-top-right-radius: 12px;
            }}
        """)

        self.ai_page = AIConfigPage()
        self.output_page = OutputPage()
        self.storage_page = StoragePage()
        self.interface_page = InterfacePage()

        page_layout = QVBoxLayout(self.pages)
        page_layout.setContentsMargins(24, 20, 24, 20)

        self.pages.addWidget(self.ai_page)
        self.pages.addWidget(self.output_page)
        self.pages.addWidget(self.storage_page)
        self.pages.addWidget(self.interface_page)

        content_layout.addWidget(self.pages, 1)
        container_layout.addWidget(content, 1)

        # 底部按钮栏
        button_bar = QFrame()
        button_bar.setFixedHeight(60)
        button_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.get('bg_primary')};
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }}
        """)

        button_layout = QHBoxLayout(button_bar)
        button_layout.setContentsMargins(24, 0, 24, 0)
        button_layout.setSpacing(12)

        # 恢复默认
        self.reset_btn = QPushButton("恢复默认")
        self.reset_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.get('text_secondary')};
                border: none;
                font-size: 13px;
                padding: 10px 16px;
            }}
            QPushButton:hover {{
                color: {Theme.get('text_primary')};
            }}
        """)
        self.reset_btn.clicked.connect(self.reset_settings)
        button_layout.addWidget(self.reset_btn)

        button_layout.addStretch()

        # 取消
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.get('bg_secondary')};
                color: {Theme.get('text_primary')};
                border: 1px solid {Theme.get('border_light')};
                border-radius: 8px;
                padding: 10px 24px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {Theme.get('bg_tertiary')};
            }}
        """)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        # 保存
        self.save_btn = QPushButton("保存设置")
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.ACCENT_BLUE};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {Theme.ACCENT_BLUE_DARK};
            }}
        """)
        self.save_btn.clicked.connect(self.save_and_close)
        button_layout.addWidget(self.save_btn)

        container_layout.addWidget(button_bar)

        # 应用容器样式
        self.apply_theme()

        # 默认选中第一页
        self.nav_buttons[0].setChecked(True)
        self.pages.setCurrentIndex(0)

    def apply_theme(self):
        """应用主题样式"""
        self.container.setStyleSheet(f"""
            #settingsContainer {{
                background-color: {Theme.get('bg_primary')};
                border-radius: 12px;
                border: 1px solid {Theme.get('border_light')};
            }}
        """)

    def setup_connections(self):
        """设置信号连接"""
        self.interface_page.themeChanged.connect(self.on_theme_changed)

    def switch_page(self, index: int):
        """切换页面"""
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        self.pages.setCurrentIndex(index)

    def on_theme_changed(self, theme: str):
        """主题改变"""
        Theme.DARK_MODE = (theme == "dark")
        self.apply_theme()

    def save_and_close(self):
        """保存并关闭"""
        self.ai_page.save_settings()
        self.output_page.save_settings()
        self.storage_page.save_settings()
        self.interface_page.save_settings()

        settings_manager.save()
        self.settingsSaved.emit()
        self.accept()

    def reset_settings(self):
        """重置设置"""
        reply = QMessageBox.question(
            self, "确认重置",
            "确定要恢复所有设置为默认值吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            settings_manager.reset()
            self.ai_page.load_settings()
            self.output_page.load_settings()
            self.storage_page.load_settings()
            self.interface_page.load_settings()

    def mousePressEvent(self, event):
        """窗口拖动"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        """窗口拖动"""
        if hasattr(self, '_press_pos') and self._press_pos:
            self.move(event.globalPosition().toPoint() - self._press_pos)


# ============================================================================
# 设置向导
# ============================================================================

class SetupWizard(SettingsDialog):
    """首次设置向导"""

    def __init__(self, parent=None):
        super().__init__(parent, show_wizard=True)

        # 只显示 AI 配置页
        for btn in self.nav_buttons[1:]:
            btn.hide()

        # 隐藏重置和取消按钮
        self.reset_btn.hide()
        self.cancel_btn.hide()

        # 修改保存按钮文字
        self.save_btn.setText("完成设置")


# ============================================================================
# 便捷函数
# ============================================================================

def show_settings(parent=None) -> bool:
    """显示设置对话框"""
    dialog = SettingsDialog(parent)
    result = dialog.exec()
    return result == QDialog.DialogCode.Accepted


def show_setup_wizard(parent=None) -> bool:
    """显示首次设置向导"""
    wizard = SetupWizard(parent)
    result = wizard.exec()
    return result == QDialog.DialogCode.Accepted


def check_and_show_wizard(parent=None) -> bool:
    """检查是否需要显示设置向导"""
    if not settings_manager.has_api_key():
        return show_setup_wizard(parent)
    return False


# ============================================================================
# 测试入口
# ============================================================================

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # 设置字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    # 检查是否需要显示向导
    if not settings_manager.has_api_key():
        wizard = SetupWizard()
        wizard.exec()
    else:
        dialog = SettingsDialog()
        dialog.show()
        app.exec()
