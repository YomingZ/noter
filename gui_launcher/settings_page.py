"""SettingsPage (gui_launcher) — polished settings with segmented controls."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QComboBox, QLineEdit, QPushButton,
    QSlider, QCheckBox, QMessageBox, QFileDialog, QInputDialog,
)
from PyQt6.QtGui import QFont

from gui_launcher.theme import Theme
from gui_launcher.settings_manager import SettingsManager, CONFIG_DIR, SETTINGS_FILE
from gui_launcher.widget_factory import WidgetFactory

settings_manager = SettingsManager()


class SettingsPage(QWidget):
    """设置页面 — card-based layout with segmented controls."""

    settingsSaved = pyqtSignal()
    applyClicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._seg_state = {}  # {group_key: active_value}
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{
                background: transparent; width: 6px; margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {Theme.get('scrollbar')}; border-radius: 3px; min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {Theme.get('scrollbar_hover')};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 20, 28, 28)
        layout.setSpacing(18)

        # ── 返回按钮 ──
        back_row = QHBoxLayout()
        back_row.setSpacing(12)

        self.back_btn = QPushButton("← 返回")
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.setFixedHeight(32)
        self.back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.ACCENT_PRIMARY};
                border: 1px solid {Theme.ACCENT_PRIMARY};
                border-radius: 4px;
                padding: 0 16px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {Theme.ACCENT_PRIMARY};
                color: white;
            }}
        """)
        self.back_btn.clicked.connect(self._on_back_clicked)
        back_row.addWidget(self.back_btn)
        back_row.addStretch()

        title_label = QLabel("⚙️ 设置")
        title_label.setStyleSheet(
            f"font-size: 18px; font-weight: 600; color: {Theme.get('text_primary')}; "
            f"background: transparent;"
        )
        back_row.addWidget(title_label)
        back_row.addStretch()

        layout.addLayout(back_row)
        layout.addSpacing(8)

        # ── Profile ──
        profile_group, profile_layout = self.create_group("📂 配置文件")
        profile_layout.setSpacing(0)

        profile_row = QHBoxLayout()
        profile_row.setSpacing(10)

        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(180)
        self.profile_combo.addItems(settings_manager.get_profiles())
        self.profile_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {Theme.get('bg_tertiary')};
                border: 1px solid {Theme.get('border_light')};
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
                color: {Theme.get('text_primary')};
                min-width: 160px;
            }}
            QComboBox::drop-down {{ border: none; width: 24px; }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {Theme.get('text_secondary')};
            }}
            QComboBox QAbstractItemView {{
                background-color: {Theme.get('bg_elevated')};
                color: {Theme.get('text_primary')};
                border: 1px solid {Theme.get('border')};
                border-radius: 4px;
                selection-background-color: {Theme.ACCENT_PRIMARY};
                selection-color: white;
            }}
        """)
        self.profile_combo.currentTextChanged.connect(self.on_profile_changed)

        p_label = QLabel("当前配置:")
        p_label.setStyleSheet(f"color: {Theme.get('text_primary')}; font-size: 13px; font-weight: 450; background: transparent;")
        profile_row.addWidget(p_label)
        profile_row.addWidget(self.profile_combo)
        profile_row.addStretch()

        self.save_profile_btn = QPushButton("💾 另存为")
        self.save_profile_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.get('bg_tertiary')};
                color: {Theme.get('text_primary')};
                border: 1px solid {Theme.get('border_light')};
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 12px;
            }}
            QPushButton:hover {{ background-color: {Theme.get('surface_2')}; border-color: {Theme.ACCENT_PRIMARY}; }}
        """)
        self.save_profile_btn.clicked.connect(self.save_current_profile)
        profile_row.addWidget(self.save_profile_btn)

        self.delete_profile_btn = QPushButton("🗑️ 删除")
        self.delete_profile_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.ERROR_RED};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 12px;
            }}
            QPushButton:hover {{ background-color: {Theme.ERROR_RED_DARK}; }}
        """)
        self.delete_profile_btn.clicked.connect(self.delete_current_profile)
        profile_row.addWidget(self.delete_profile_btn)

        profile_layout.addLayout(profile_row)
        layout.addWidget(profile_group)

        # ── AI Config ──
        ai_group, ai_layout = self.create_group("🤖 AI 配置")
        ai_layout.setSpacing(14)

        self.provider_combo = self.create_combo(["Kimi (Moonshot)", "OpenAI", "Anthropic", "自定义"])
        ai_layout.addLayout(self._create_row("提供商", self.provider_combo, connect=self.on_provider_changed))

        key_widget = QWidget()
        key_layout = QHBoxLayout(key_widget)
        key_layout.setContentsMargins(0, 0, 0, 0)
        key_layout.setSpacing(8)
        self.api_key_input = self.create_input("输入 API 密钥", password=True)
        key_layout.addWidget(self.api_key_input, 1)
        self.toggle_key_btn = QPushButton("👁")
        self.toggle_key_btn.setFixedSize(32, 32)
        self.toggle_key_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.get('bg_tertiary')};
                border: 1px solid {Theme.get('border_light')};
                border-radius: 4px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {Theme.get('surface_2')};
                border-color: {Theme.ACCENT_PRIMARY};
            }}
        """)
        self.toggle_key_btn.clicked.connect(self.toggle_key_visibility)
        key_layout.addWidget(self.toggle_key_btn)
        ai_layout.addLayout(self._create_row("API Key", key_widget))

        self.model_combo = self.create_combo([])
        ai_layout.addLayout(self._create_row("模型", self.model_combo))

        self.base_url_input = self.create_input("可选，代理地址")
        ai_layout.addLayout(self._create_row("Base URL", self.base_url_input))

        temp_widget = QWidget()
        temp_layout = QHBoxLayout(temp_widget)
        temp_layout.setContentsMargins(0, 0, 0, 0)
        temp_layout.setSpacing(10)
        self.temp_slider = WidgetFactory.create_slider()
        self.temp_slider.setRange(0, 10)
        self.temp_slider.setValue(7)
        self.temp_slider.setMinimumWidth(180)
        self.temp_slider.valueChanged.connect(self.on_temp_changed)
        temp_layout.addWidget(self.temp_slider, 1)
        self.temp_label = QLabel("0.7")
        self.temp_label.setFixedWidth(35)
        self.temp_label.setStyleSheet(
            f"color: {Theme.get('text_primary')}; font-size: 13px; font-weight: 500; background: transparent;"
        )
        temp_layout.addWidget(self.temp_label)
        ai_layout.addLayout(self._create_row("自由度", temp_widget))

        layout.addWidget(ai_group)

        # ── Output ──
        output_group, output_layout = self.create_group("📄 输出设置")
        output_layout.setSpacing(14)

        # Format: segmented control
        fmt_seg, self._fmt_seg_btns = WidgetFactory.create_segmented_control(
            [("docx", "Word"), ("md", "Markdown"), ("html", "HTML"), ("obsidian", "Obsidian")],
            default_key="docx",
            callback=self._on_format_seg_changed,
        )
        output_layout.addLayout(self._create_row("格式", fmt_seg))

        # Verbosity: segmented control
        verb_seg, self._verb_seg_btns = WidgetFactory.create_segmented_control(
            [("concise", "精简"), ("detailed", "详细"), ("sprint", "冲刺")],
            default_key="detailed",
        )
        self._verbosity_key = "detailed"
        output_layout.addLayout(self._create_row("详细程度", verb_seg))

        opt_widget = QWidget()
        opt_layout = QHBoxLayout(opt_widget)
        opt_layout.setContentsMargins(0, 0, 0, 0)
        opt_layout.setSpacing(16)
        self.include_examples_cb = self.create_checkbox("包含例题")
        self.generate_checklist_cb = self.create_checkbox("生成自检清单")
        self.add_page_numbers_cb = self.create_checkbox("添加页码")
        opt_layout.addWidget(self.include_examples_cb)
        opt_layout.addWidget(self.generate_checklist_cb)
        opt_layout.addWidget(self.add_page_numbers_cb)
        opt_layout.addStretch()
        output_layout.addWidget(opt_widget)

        layout.addWidget(output_group)

        # ── Storage ──
        storage_group, storage_layout = self.create_group("💾 存储设置")
        storage_layout.setSpacing(14)

        folder_widget = QWidget()
        folder_layout = QHBoxLayout(folder_widget)
        folder_layout.setContentsMargins(0, 0, 0, 0)
        folder_layout.setSpacing(8)
        self.folder_input = self.create_input("")
        folder_layout.addWidget(self.folder_input, 1)
        self.browse_btn = self.create_button("浏览")
        self.browse_btn.clicked.connect(self.browse_folder)
        folder_layout.addWidget(self.browse_btn)
        storage_layout.addLayout(self._create_row("输出目录", folder_widget))

        self.keep_md_cb = self.create_checkbox("保留 Markdown 文件")
        storage_layout.addWidget(self.keep_md_cb)

        layout.addWidget(storage_group)

        # ── Interface ──
        interface_group, interface_layout = self.create_group("🎨 界面设置")
        interface_layout.setSpacing(14)

        theme_seg, self._theme_seg_btns = WidgetFactory.create_segmented_control(
            [("system", "跟随系统"), ("light", "浅色"), ("dark", "深色")],
            default_key="system",
            callback=self._on_theme_seg_changed,
        )
        interface_layout.addLayout(self._create_row("主题", theme_seg))

        layout.addWidget(interface_group)
        layout.addStretch()

        scroll.setWidget(container)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # ── Apply 按钮 ──
        apply_row = QHBoxLayout()
        apply_row.setContentsMargins(28, 0, 28, 12)
        apply_row.addStretch()

        self.apply_btn = QPushButton("应用")
        self.apply_btn.setFixedSize(100, 34)
        self.apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.apply_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.gradient_accent()};
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {Theme.ACCENT_PRIMARY_DARK};
            }}
        """)
        self.apply_btn.clicked.connect(self._on_apply_clicked)
        apply_row.addWidget(self.apply_btn)

        main_layout.addLayout(apply_row)

        # Auto-populate models
        self.on_provider_changed(0)

    # ── Segmented control callbacks ──

    def _on_format_seg_changed(self, key: str):
        pass  # Value read at save time

    def _on_theme_seg_changed(self, key: str):
        Theme.DARK_MODE = (key == "dark")
        main_window = self
        while main_window and not hasattr(main_window, 'apply_theme'):
            main_window = main_window.parent()
        if main_window and hasattr(main_window, 'apply_theme'):
            main_window.apply_theme()

    def _get_seg_active(self, segments: dict) -> str:
        """Get the active key from a segmented control."""
        for key, btn in segments.items():
            if "gradient" in btn.styleSheet():
                return key
        return list(segments.keys())[0] if segments else ""

    def _set_seg_active(self, segments: dict, key: str):
        """Programmatically set a segment active."""
        if key in segments:
            segments[key].click()

    # ── Factory delegates ──

    def _create_row(self, label_text: str, widget, connect=None):
        return WidgetFactory.create_row(label_text, widget, connect)

    def create_group(self, title: str):
        group = WidgetFactory.create_group(title)
        return group, group.layout()

    def create_input(self, placeholder: str = "", password: bool = False) -> QLineEdit:
        return WidgetFactory.create_input(placeholder, password)

    def create_combo(self, items: list) -> QComboBox:
        return WidgetFactory.create_combo(items)

    def create_button(self, text: str) -> QPushButton:
        return WidgetFactory.create_button(text)

    def create_checkbox(self, text: str) -> QCheckBox:
        return WidgetFactory.create_checkbox(text)

    # ── Handlers ──

    def on_provider_changed(self, index):
        providers = ["kimi", "openai", "anthropic", "custom"]
        provider = providers[index] if index < len(providers) else "kimi"
        models = settings_manager.get_models_for_provider(provider)
        current_idx = self.model_combo.currentIndex()
        self.model_combo.clear()
        self.model_combo.addItems(models if models else ["自定义模型"])

        base_urls = {
            "kimi": "https://api.moonshot.cn",
            "openai": "https://api.openai.com",
            "anthropic": "https://api.anthropic.com",
            "custom": "",
        }
        current_url = self.base_url_input.text().strip()
        default_urls = set(base_urls.values())
        if not current_url or current_url in default_urls:
            self.base_url_input.setText(base_urls.get(provider, ""))

    def on_temp_changed(self, value):
        self.temp_label.setText(f"{value / 10:.1f}")

    def toggle_key_visibility(self):
        if self.api_key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_key_btn.setText("🙈")
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_key_btn.setText("👁")

    def browse_folder(self):
        path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if path:
            self.folder_input.setText(path)

    def on_profile_changed(self, profile_name: str):
        if profile_name and profile_name != settings_manager.current_profile:
            if settings_manager.load_profile(profile_name):
                self.load_settings()
                # Find and refresh main window theme
                main_window = self
                while main_window and not hasattr(main_window, 'apply_theme'):
                    main_window = main_window.parent()
                if main_window and hasattr(main_window, 'apply_theme'):
                    main_window.apply_theme()

    def save_current_profile(self):
        name, ok = QInputDialog.getText(self, "保存配置", "请输入配置名称:")
        if ok and name:
            name = name.strip()
            if name and name != "默认配置":
                self.save_settings()
                settings_manager.save_profile(name)
                current = self.profile_combo.currentText()
                self.profile_combo.clear()
                self.profile_combo.addItems(settings_manager.get_profiles())
                self.profile_combo.setCurrentText(name)

    def delete_current_profile(self):
        current = self.profile_combo.currentText()
        if current == "默认配置":
            QMessageBox.warning(self, "无法删除", "不能删除默认配置")
            return
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除配置「{current}」吗?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if settings_manager.delete_profile(current):
                self.profile_combo.clear()
                self.profile_combo.addItems(settings_manager.get_profiles())
                self.profile_combo.setCurrentText("默认配置")
                settings_manager.load_profile("默认配置")
                self.load_settings()

    def load_settings(self):
        """Load settings from SettingsManager into all controls."""
        self.profile_combo.setCurrentText(settings_manager.current_profile)
        self.delete_profile_btn.setEnabled(settings_manager.current_profile != "默认配置")

        provider = settings_manager.get("ai", "provider", default="kimi")
        provider_map = {"kimi": 0, "openai": 1, "anthropic": 2, "custom": 3}
        self.provider_combo.setCurrentIndex(provider_map.get(provider, 0))
        self.api_key_input.setText(settings_manager.get("ai", "api_key", default=""))
        self.base_url_input.setText(settings_manager.get("ai", "base_url", default=""))
        model = settings_manager.get("ai", "model", default="")
        idx = self.model_combo.findText(model)
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)
        self.temp_slider.setValue(
            int(settings_manager.get("ai", "temperature", default=0.7) * 10)
        )

        # Format via segmented control
        fmt = settings_manager.get("output", "format", default="docx")
        if fmt in self._fmt_seg_btns:
            self._set_seg_active(self._fmt_seg_btns, fmt)

        # Verbosity via segmented control
        verb = settings_manager.get("output", "verbosity", default="detailed")
        if verb in self._verb_seg_btns:
            self._set_seg_active(self._verb_seg_btns, verb)

        self.include_examples_cb.setChecked(
            settings_manager.get("output", "include_examples", default=True)
        )
        self.generate_checklist_cb.setChecked(
            settings_manager.get("output", "generate_checklist", default=True)
        )
        self.add_page_numbers_cb.setChecked(
            settings_manager.get("output", "add_page_numbers", default=True)
        )

        self.folder_input.setText(
            settings_manager.get("storage", "output_folder", default="")
        )
        self.keep_md_cb.setChecked(
            settings_manager.get("storage", "keep_markdown", default=True)
        )

        theme = settings_manager.get("interface", "theme", default="system")
        if theme in self._theme_seg_btns:
            self._set_seg_active(self._theme_seg_btns, theme)

    def save_settings(self):
        """Save all control values to SettingsManager."""
        settings_manager.current_profile = self.profile_combo.currentText()

        provider_map = {0: "kimi", 1: "openai", 2: "anthropic", 3: "custom"}
        settings_manager.set(
            "ai", "provider", provider_map[self.provider_combo.currentIndex()]
        )
        settings_manager.set("ai", "api_key", self.api_key_input.text())
        settings_manager.set("ai", "model", self.model_combo.currentText())
        settings_manager.set("ai", "base_url", self.base_url_input.text())
        settings_manager.set(
            "ai", "temperature", self.temp_slider.value() / 10
        )

        # Format from segmented control
        fmt = self._get_seg_active(self._fmt_seg_btns) or "docx"
        settings_manager.set("output", "format", fmt)

        verb = self._get_seg_active(self._verb_seg_btns) or "detailed"
        settings_manager.set("output", "verbosity", verb)

        settings_manager.set(
            "output", "include_examples", self.include_examples_cb.isChecked()
        )
        settings_manager.set(
            "output", "generate_checklist", self.generate_checklist_cb.isChecked()
        )
        settings_manager.set(
            "output", "add_page_numbers", self.add_page_numbers_cb.isChecked()
        )

        settings_manager.set("storage", "output_folder", self.folder_input.text())
        settings_manager.set(
            "storage", "keep_markdown", self.keep_md_cb.isChecked()
        )

        theme = self._get_seg_active(self._theme_seg_btns) or "system"
        settings_manager.set("interface", "theme", theme)

        settings_manager.save()
        self.settingsSaved.emit()

    def _on_apply_clicked(self):
        """应用按钮：保存设置，通知主界面同步"""
        self.save_settings()
        self.applyClicked.emit()

    def _on_back_clicked(self):
        """返回按钮：先保存设置，再发射信号"""
        self.save_settings()
