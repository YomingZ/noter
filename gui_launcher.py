#!/usr/bin/env python3
"""
PDF 备考笔记生成器 - 现代化 GUI 启动器

基于 PyQt6 的专业级界面设计
设计语言参考: Apple Design / Notion / Linear
"""

import sys
import os
from pathlib import Path
from typing import List, Optional
import json
import base64
import io
import webbrowser

# 修复终端中文乱码 (P0-3)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QProgressBar, QTextEdit,
    QComboBox, QFrame, QScrollArea, QSizePolicy,
    QGraphicsDropShadowEffect, QSpacerItem, QStackedWidget,
    QSlider, QCheckBox, QRadioButton, QButtonGroup, QLineEdit,
    QMessageBox, QInputDialog
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QSize, QPropertyAnimation,
    QEasingCurve, QPoint, QRect, QTimer, pyqtProperty, QObject
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QPainter, QPen, QBrush,
    QFontDatabase, QLinearGradient
)

# 获取脚本目录
SCRIPT_DIR = Path(__file__).parent.resolve()
CONFIG_DIR = SCRIPT_DIR / "config"
SETTINGS_FILE = CONFIG_DIR / "settings.json"


# ============================================================================
# Apple 风格颜色系统
# ============================================================================

from gui_launcher.theme import Theme
from gui_launcher.settings_manager import SettingsManager, settings_manager, CONFIG_DIR, SETTINGS_FILE
from gui_launcher.widget_factory import WidgetFactory
from gui_launcher.log_panel import LogPanel
from gui_launcher.drop_area import DropArea
from gui_launcher.file_card import FileCard
from gui_launcher.file_list_area import FileListArea
from gui_launcher.settings_page import SettingsPage


# ============================================================================
# 工作线程
# ============================================================================

class WorkerThread(QThread):
    """Thin signal-forwarder: reads settings → delegates to ProcessingService → emits signals."""
    progress = pyqtSignal(Path, int, str)
    log = pyqtSignal(str, str)
    finished_all = pyqtSignal(bool, str)

    def __init__(self, files, provider, output_format, output_dir,
                 obsidian_template=None, obsidian_course=None, obsidian_vault=None,
                 obsidian_note_name=None, obsidian_analysis=None):
        super().__init__()
        self.files = files
        self.provider = provider
        self.output_format = output_format
        self.output_dir = output_dir
        self.obsidian_template = obsidian_template
        self.obsidian_course = obsidian_course
        self.obsidian_vault = obsidian_vault
        self.obsidian_note_name = obsidian_note_name
        self.obsidian_analysis = obsidian_analysis
        self._svc = None

    def cancel(self):
        if self._svc:
            self._svc.cancel()

    def run(self):
        import sys
        import traceback
        self.log.emit("📦 WorkerThread 启动...", "info")
        src_dir = str(SCRIPT_DIR / "src")
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)

        try:
            from pdf_summarizer.processing_service import ProcessingService
            self.log.emit("✅ 模块导入成功", "info")
        except ImportError as e:
            self.log.emit(f"❌ 导入模块失败: {e}", "error")
            self.finished_all.emit(False, "模块导入失败")
            return

        ai_config = {
            "provider": settings_manager.get("ai", "provider", default="kimi"),
            "api_key": settings_manager.get("ai", "api_key", default=""),
            "model": settings_manager.get("ai", "model", default="moonshot-v1-8k"),
            "base_url": settings_manager.get("ai", "base_url", default=""),
            "temperature": settings_manager.get("ai", "temperature", default=0.7),
        }
        self.log.emit(f"🔑 API Key: {'已配置' if ai_config['api_key'] else '未配置'}", "info")

        try:
            self._svc = ProcessingService(
                provider=self.provider,
                output_format=self.output_format,
                output_dir=Path(self.output_dir),
                obsidian_template=Path(self.obsidian_template) if self.obsidian_template else None,
                obsidian_course=self.obsidian_course,
                obsidian_vault=Path(self.obsidian_vault) if self.obsidian_vault else None,
                obsidian_note_name=self.obsidian_note_name,
                obsidian_analysis=self.obsidian_analysis,
            )
            self.log.emit(f"✅ ProcessingService 创建成功 (格式: {self.output_format})", "info")

            try:
                self._svc.configure_ai(ai_config)
                self.log.emit("✅ AI 配置完成", "info")
            except ValueError as e:
                self.log.emit(f"❌ AI 配置失败: {e}", "error")
                self.finished_all.emit(False, str(e))
                return

            total = len(self.files)
            success_count = 0
            self.log.emit(f"📄 开始处理 {total} 个文件...", "info")

            for idx, result in enumerate(self._svc.process_batch(self.files), 1):
                fp = result.input_file or Path("unknown")
                self.log.emit(f"[{idx}/{total}] 处理: {fp.name}", "info")

                if not result.success:
                    error_msg = result.error_message or "未知错误"
                    self.progress.emit(fp, 0, "failed")
                    self.log.emit(f"❌ 失败: {error_msg[:300]}", "error")
                    continue

                self.progress.emit(fp, 100, "completed")
                self.log.emit(f"✅ 完成: {fp.name}", "success")
                success_count += 1

            if success_count == total:
                self.finished_all.emit(True, f"成功处理 {success_count}/{total}")
            else:
                self.finished_all.emit(False, f"成功 {success_count}/{total}")

        except Exception as e:
            error_detail = traceback.format_exc()
            self.log.emit(f"💥 处理异常: {e}", "error")
            self.log.emit(error_detail, "error")
            self.finished_all.emit(False, f"处理失败: {e}")


# ============================================================================
# 主窗口
# ============================================================================

class ModernMainWindow(QMainWindow):
    """Windows 11 风格主窗口"""

    def __init__(self):
        super().__init__()
        self.selected_files: List[Path] = []
        self.worker: Optional[WorkerThread] = None

        self.setup_window()
        self.setup_ui()
        self.apply_theme()

        # 初始化模板分析集成系统
        self._setup_template_analysis_system()

        # P0-1: 首次使用引导弹窗
        self._show_welcome_if_first_run()

        # P0-2: 未配置 API Key 时在启动后提示
        QTimer.singleShot(500, self._check_api_key_and_prompt)

    def setup_window(self):
        from PyQt6.QtGui import QIcon
        self.setWindowTitle("PDF 备考笔记生成器")
        self.setMinimumSize(680, 750)
        self.resize(720, 800)

        # 设置自定义图标（任务栏和Alt+Tab显示）
        icon_path = "assets/noter_icon_v3.ico"
        if Path(icon_path).exists():
            self.setWindowIcon(QIcon(icon_path))

        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.availableGeometry()
            x = (geometry.width() - self.width()) // 2
            y = (geometry.height() - self.height()) // 2
            self.move(x, y)

    def setup_ui(self):
        self.main_container = QFrame()
        self.main_container.setObjectName("mainContainer")
        self.setCentralWidget(self.main_container)

        main_layout = QVBoxLayout(self.main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 页面容器（Windows原生标题栏，无需自定义）
        self.pages = QStackedWidget()
        main_layout.addWidget(self.pages)

        # 主页面
        self.main_page = self.create_main_page()
        self.pages.addWidget(self.main_page)

        # 设置页面
        self.settings_page = SettingsPage()
        self.settings_page.settingsSaved.connect(self.on_settings_saved)
        self.settings_page.applyClicked.connect(self.on_apply_clicked)
        self.pages.addWidget(self.settings_page)

        # 加载默认 Obsidian Vault 路径（每次启动用默认值覆盖）
        default_vault = settings_manager.get("storage", "obsidian_vault_default", default="")
        if default_vault:
            self.obsidian_panel.vault_edit.setText(default_vault)
        
        # 同步所有设置到主界面
        self._sync_settings_to_main()

        # 默认显示主页面
        self.pages.setCurrentIndex(0)

    def create_main_page(self) -> QWidget:
        page = QWidget()
        outer_layout = QVBoxLayout(page)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{ background: transparent; width: 6px; margin: 0; }}
            QScrollBar::handle:vertical {{ background: {Theme.get('scrollbar')}; border-radius: 3px; min-height: 30px; }}
            QScrollBar::handle:vertical:hover {{ background: {Theme.get('scrollbar_hover')}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(24, 16, 24, 24)
        layout.setSpacing(16)

        # 拖放区域
        self.drop_area = DropArea()
        self.drop_area.filesDropped.connect(self.on_files_dropped)
        layout.addWidget(self.drop_area)

        # 文件列表
        self.file_list = FileListArea()
        self.file_list.setFixedHeight(140)
        self.file_list.filesChanged.connect(self.on_files_changed)
        layout.addWidget(self.file_list)

        # 选项区域
        options_frame = QFrame()
        options_frame.setStyleSheet(f"QFrame {{ background-color: {Theme.get('bg_secondary')}; border: 1px solid {Theme.get('border_light')}; border-radius: 4px; }}")
        options_layout = QHBoxLayout(options_frame)
        options_layout.setContentsMargins(16, 12, 16, 12)
        options_layout.setSpacing(24)

        provider_layout = QVBoxLayout()
        provider_layout.setSpacing(4)
        provider_label = QLabel("AI 提供商")
        provider_label.setStyleSheet(f"font-size: 12px; color: {Theme.get('text_secondary')}; background: transparent;")
        provider_layout.addWidget(provider_label)
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["kimi", "openai", "claude", "deepseek"])
        self.provider_combo.setStyleSheet(self._combo_style())
        provider_layout.addWidget(self.provider_combo)
        options_layout.addLayout(provider_layout)

        format_layout = QVBoxLayout()
        format_layout.setSpacing(4)
        format_label = QLabel("输出格式")
        format_label.setStyleSheet(f"font-size: 12px; color: {Theme.get('text_secondary')}; background: transparent;")
        format_layout.addWidget(format_label)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["docx", "md", "html", "obsidian"])
        self.format_combo.setStyleSheet(self._combo_style())
        format_layout.addWidget(self.format_combo)
        options_layout.addLayout(format_layout)

        options_layout.addStretch()

        # 设置按钮
        self.settings_btn = QPushButton("⚙️ 设置")
        self.settings_btn.setFixedSize(90, 32)
        self.settings_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {Theme.get('bg_tertiary')}; color: {Theme.get('text_primary')}; border: 1px solid {Theme.get('border')}; border-radius: 4px; font-size: 13px; }}
            QPushButton:hover {{ background-color: {Theme.get('bg_elevated')}; border-color: {Theme.ACCENT_PRIMARY}; }}
        """)
        self.settings_btn.clicked.connect(self.show_settings_page)
        options_layout.addWidget(self.settings_btn)

        # 主题切换
        self.theme_btn = QPushButton("🌙")
        self.theme_btn.setFixedSize(32, 32)
        self.theme_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {Theme.get('bg_tertiary')}; border: 1px solid {Theme.get('border')}; border-radius: 4px; font-size: 14px; }}
            QPushButton:hover {{ background-color: {Theme.get('bg_elevated')}; border-color: {Theme.ACCENT_PRIMARY}; }}
        """)
        self.theme_btn.clicked.connect(self.toggle_theme)
        options_layout.addWidget(self.theme_btn)

        layout.addWidget(options_frame)

        from gui_launcher.obsidian_panel import ObsidianPanel
        self.obsidian_panel = ObsidianPanel()
        self.obsidian_panel.browse_template_requested.connect(self._browse_obsidian_template)
        self.obsidian_panel.browse_vault_requested.connect(self._browse_obsidian_vault)
        self.obsidian_panel.courses_reload_requested.connect(self._reload_obsidian_courses)
        # 连接模板分析信号
        self.obsidian_panel.template_analysis_requested.connect(self._on_template_analysis_requested)
        layout.addWidget(self.obsidian_panel)

        # 连接格式切换事件
        self.format_combo.currentTextChanged.connect(self._on_format_changed)

        # 日志面板
        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel, 1)

        scroll.setWidget(scroll_content)
        outer_layout.addWidget(scroll, 1)

        # 底部操作栏 - 固定在窗口底部，不随滚动
        action_bar = QFrame()
        action_bar.setObjectName("fixedActionBar")
        action_bar.setStyleSheet(f"""
            QFrame#fixedActionBar {{
                background-color: {Theme.get('bg_primary')};
                border-top: 1px solid {Theme.get('border_light')};
                padding: 0;
            }}
            QFrame#fixedActionBar:hover {{
                background-color: {Theme.get('bg_elevated')};
            }}
        """)
        action_bar.setFixedHeight(60)

        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, -2)
        action_bar.setGraphicsEffect(shadow)

        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(24, 12, 24, 12)
        action_layout.setSpacing(12)

        action_layout.addStretch()

        # P2-14: 帮助按钮
        help_btn = QPushButton("❓")
        help_btn.setFixedSize(36, 36)
        help_btn.setToolTip("帮助 / 使用说明")
        help_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; color: {Theme.get('text_secondary')}; border: 1px solid {Theme.get('border_light')}; border-radius: 4px; font-size: 16px; }}
            QPushButton:hover {{ background-color: {Theme.get('bg_tertiary')}; border-color: {Theme.ACCENT_PRIMARY}; }}
        """)
        help_btn.clicked.connect(self._show_help_dialog)
        action_layout.addWidget(help_btn)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setFixedSize(80, 36)
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {Theme.get('bg_secondary')}; color: {Theme.get('text_primary')}; border: 1px solid {Theme.get('border')}; border-radius: 4px; font-size: 13px; }}
            QPushButton:hover {{ background-color: {Theme.get('bg_tertiary')}; border-color: {Theme.ACCENT_PRIMARY}; }}
            QPushButton:disabled {{ color: {Theme.get('text_tertiary')}; }}
        """)
        self.cancel_btn.clicked.connect(self.cancel_processing)
        self.cancel_btn.setEnabled(False)
        action_layout.addWidget(self.cancel_btn)

        self.start_btn = QPushButton("开始生成")
        self.start_btn.setFixedSize(120, 36)
        self.start_btn.setStyleSheet(f"""
            QPushButton {{ background: {Theme.gradient_accent()}; color: white; border: none; border-radius: 4px; font-size: 13px; font-weight: 600; }}
            QPushButton:hover {{ background-color: {Theme.ACCENT_PRIMARY_DARK}; }}
            QPushButton:disabled {{ background: {Theme.get('bg_tertiary')}; color: {Theme.get('text_tertiary')}; }}
        """)
        self.start_btn.clicked.connect(self.start_processing)
        action_layout.addWidget(self.start_btn)

        outer_layout.addWidget(action_bar)

        return page

    def _combo_style(self) -> str:
        return f"""
            QComboBox {{ background-color: {Theme.get('bg_tertiary')}; color: {Theme.get('text_primary')}; border: 1px solid {Theme.get('border_light')}; border-radius: 4px; padding: 6px 12px; font-size: 13px; min-width: 90px; }}
            QComboBox:hover {{ border-color: {Theme.ACCENT_PRIMARY}; }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox::down-arrow {{ image: none; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 5px solid {Theme.get('text_secondary')}; }}
            QComboBox QAbstractItemView {{ background-color: {Theme.get('bg_elevated')}; color: {Theme.get('text_primary')}; border: 1px solid {Theme.get('border')}; border-radius: 4px; selection-background-color: {Theme.ACCENT_PRIMARY}; }}
        """

    def apply_theme(self):
        bg = Theme.get('bg_primary')
        self.main_container.setStyleSheet(f"""
            #mainContainer {{ background-color: {bg}; }}
        """)
        self.setWindowTitle("PDF 备考笔记生成器")
        self.theme_btn.setText("☀️" if Theme.DARK_MODE else "🌙")

    def toggle_theme(self):
        Theme.toggle()
        self.apply_theme()
        self.drop_area.update_style()
        self.provider_combo.setStyleSheet(self._combo_style())
        self.format_combo.setStyleSheet(self._combo_style())

    def show_settings_page(self):
        self.settings_page.load_settings()
        self.setWindowTitle("设置 - PDF 备考笔记生成器")
        self._animate_page_switch(1)

    def _animate_page_switch(self, index: int):
        """P2-13: 页面滑动切换动画"""
        if self.pages.currentIndex() == index:
            return
        # 使用 QPropertyAnimation 对 pages 做位置偏移
        current_w = self.pages.currentWidget()
        next_w = self.pages.widget(index)
        if not current_w or not next_w:
            self.pages.setCurrentIndex(index)
            return

        direction = 1 if index > self.pages.currentIndex() else -1
        offset = self.width() * direction

        next_w.setGeometry(0, 0, self.pages.width(), self.pages.height())
        next_w.move(offset, 0)

        self._page_anim = QPropertyAnimation(self.pages, b"pos")
        self._page_anim.setDuration(250)
        self._page_anim.setStartValue(QPoint(-offset, 0))
        self._page_anim.setEndValue(QPoint(0, 0))
        self._page_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.pages.setCurrentIndex(index)
        self._page_anim.start()

    def _on_format_changed(self, fmt: str):
        is_obsidian = fmt == "obsidian"
        self.obsidian_panel.set_active(is_obsidian)
        if is_obsidian:
            self._reload_obsidian_courses()

    def _browse_obsidian_template(self):
        """Open file dialog to select an Obsidian markdown template."""
        from PyQt6.QtWidgets import QFileDialog
        default_vault = settings_manager.get("storage", "obsidian_vault_default", default="")
        start_dir = default_vault if default_vault and Path(default_vault).is_dir() else str(Path.home())
        path, _ = QFileDialog.getOpenFileName(
            self, "选择笔记模板", start_dir,
            "Markdown 文件 (*.md);;所有文件 (*)"
        )
        if path:
            self.obsidian_panel.template_edit.setText(path)

    def _browse_obsidian_vault(self):
        """Open folder dialog to select Obsidian vault directory."""
        from PyQt6.QtWidgets import QFileDialog
        default_vault = settings_manager.get("storage", "obsidian_vault_default", default="")
        start_dir = default_vault if default_vault and Path(default_vault).is_dir() else str(Path.home())
        path = QFileDialog.getExistingDirectory(
            self, "选择 Obsidian Vault 目录", start_dir
        )
        if path:
            self.obsidian_panel.vault_edit.setText(path)

    def _reload_obsidian_courses(self):
        """Scan vault and populate course name dropdown."""
        vault_path = self.obsidian_panel.vault_edit.text().strip()
        if not vault_path or not Path(vault_path).is_dir():
            return
        from pdf_summarizer.vault_service import VaultService

        service = VaultService()
        result = service.scan_courses(Path(vault_path))

        if not result.success:
            self.on_log(f"扫描 vault 失败: {result.error_message}", "error")
            return

        if result.corrected_path:
            self.obsidian_panel.vault_edit.setText(str(result.vault_root))
            self.on_log(f"已自动定位到 Vault 根目录: {result.vault_root.name}", "info")

        courses = result.courses
        self.obsidian_panel.populate_courses(courses)
        if courses:
            self.on_log(f"已加载 {len(courses)} 个课程: {', '.join(courses[:5])}{'...' if len(courses) > 5 else ''}", "info")

    def _setup_template_analysis_system(self):
        """初始化模板分析集成系统"""
        import logging
        from gui_launcher.template_analysis_integration import TemplateAnalysisIntegration

        self.logger = logging.getLogger(__name__)
        self.on_log("🔧 正在初始化模板分析系统...", "info")

        # 创建集成实例
        self.template_integration = TemplateAnalysisIntegration(self)

        # 尝试初始化 AI 函数（延迟到首次使用时再检查）
        try:
            self._initialize_ai_for_analysis()
            self.on_log("✅ 模板分析系统就绪", "success")
        except Exception as e:
            self.on_log(f"⚠️ 模板分析系统部分功能受限: {e}", "warning")
            self.logger.warning(f"Template analysis system limited: {e}")

    def _initialize_ai_for_analysis(self):
        """为模板分析器初始化 AI 生成函数"""
        import asyncio
        import logging

        self.logger = logging.getLogger(__name__)

        async def ai_generate_fn(system_prompt: str, user_prompt: str, **kwargs) -> str:
            """AI 生成函数包装器"""
            self.logger.info(f"[TemplateAnalysis] AI 调用开始 - max_tokens={kwargs.get('max_tokens', 'default')}")

            try:
                from src.pdf_summarizer.ai_client import AIClient

                # 获取当前配置的 AI 客户端
                client = AIClient()

                self.logger.info("[TemplateAnalysis] AI 客户端已创建")

                # 调用生成接口
                response = await client.generate(
                    system_prompt=system_prompt,
                    prompt=user_prompt,
                    **kwargs
                )

                result_text = response.content if hasattr(response, 'content') else str(response)
                self.logger.info(f"[TemplateAnalysis] AI 响应成功 - 长度: {len(result_text)} 字符")
                return result_text

            except Exception as e:
                self.logger.error(f"[TemplateAnalysis] AI 调用失败: {e}", exc_info=True)
                raise

        # 初始化分析器的 AI 函数
        self.template_integration.initialize_analyzer(ai_generate_fn)
        self.logger.info("✅ [TemplateAnalysis] AI 函数已绑定到分析器")

    def _on_template_analysis_requested(self, template_path: str):
        """处理模板分析请求 - 带详细日志"""
        import asyncio
        from pathlib import Path
        import time

        start_time = time.time()
        self.on_log(f"\n{'='*60}", "info")
        self.on_log(f"🔍 [模板分析] 收到分析请求", "info")
        self.on_log(f"   📄 模板路径: {template_path}", "info")
        self.on_log(f"   ⏱️ 开始时间: {time.strftime('%H:%M:%S')}", "info")
        self.on_log(f"{'='*60}\n", "info")

        # 验证文件存在
        template_file = Path(template_path)
        if not template_file.exists():
            self.on_log(f"❌ [模板分析] 错误：文件不存在", "error")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "文件未找到", f"无法找到模板文件:\n{template_path}")
            return

        file_size = template_file.stat().st_size
        self.on_log(f"✅ [模板分析] 文件验证通过", "success")
        self.on_log(f"   📊 文件大小: {file_size / 1024:.1f} KB", "info")

        # 禁用按钮防止重复点击
        if hasattr(self.obsidian_panel, 'analyze_btn'):
            self.obsidian_panel.analyze_btn.setEnabled(False)
            self.obsidian_panel.analyze_btn.setText("⏳ 分析中...")

        self.on_log(f"⏳ [模板分析] 正在启动异步分析任务...", "info")

        # 创建并启动异步任务
        async def run_analysis():
            try:
                await self.template_integration.on_analysis_requested(template_path)
            except Exception as e:
                self.on_log(f"❌ [模板分析] 异步任务异常: {e}", "error")
                import traceback
                self.on_log(traceback.format_exc(), "error")
            finally:
                # 恢复按钮状态
                if hasattr(self.obsidian_panel, 'analyze_btn'):
                    self.obsidian_panel.analyze_btn.setEnabled(True)
                    self.obsidian_panel.analyze_btn.setText("🔍 分析")

                elapsed = time.time() - start_time
                self.on_log(f"\n{'='*60}", "info")
                self.on_log(f"✅ [模板分析] 流程完成 | 总耗时: {elapsed:.2f}s", "success")
                self.on_log(f"{'='*60}\n", "info")

        # 在事件循环中运行异步任务
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果已经在运行的事件循环中，使用 create_task
                asyncio.create_task(run_analysis())
            else:
                # 否则直接运行
                loop.run_until_complete(run_analysis())
        except RuntimeError:
            # 如果没有事件循环，创建新的
            asyncio.run(run_analysis())

    def show_main_page(self):
        self.setWindowTitle("PDF 备考笔记生成器")
        self._animate_page_switch(0)

    def on_settings_saved(self):
        self._sync_settings_to_main()
        self.show_main_page()

    def on_apply_clicked(self):
        self._sync_settings_to_main()
        self.statusBar().showMessage("✅ 设置已应用", 3000)

    def _sync_settings_to_main(self):
        """从 settings_manager 同步值到主界面控件。"""
        fmt = settings_manager.get("output", "format", default="docx")
        self.format_combo.setCurrentText(fmt)

        provider = settings_manager.get("ai", "provider", default="kimi")
        provider_map = {"kimi": "kimi", "openai": "openai", "anthropic": "claude", "deepseek": "deepseek"}
        mapped = provider_map.get(provider, "kimi")
        self.provider_combo.setCurrentText(mapped)

        # P1-6: Vault 路径自动同步到 Obsidian 面板
        vault_default = settings_manager.get("storage", "obsidian_vault_default", default="")
        if vault_default and hasattr(self, 'obsidian_panel'):
            current_vault = self.obsidian_panel.vault_edit.text().strip()
            if not current_vault:
                self.obsidian_panel.vault_edit.setText(vault_default)

    # ═══════════════════════════════════════════
    # P0-1: 首次使用引导弹窗
    # ═══════════════════════════════════════════
    def _show_welcome_if_first_run(self):
        """首次运行时显示欢迎引导弹窗。"""
        first_run = settings_manager.get("app", "first_run_completed", default=False)
        if first_run:
            return

        from PyQt6.QtWidgets import QDialog, QTextEdit, QVBoxLayout

        dialog = QDialog(self)
        dialog.setWindowTitle("🚀 欢迎使用 PDF 笔记生成器 (Noter)")
        dialog.setMinimumSize(520, 420)
        dialog.resize(540, 440)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel("🚀 欢迎使用 Noter！")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #2c3e50;")
        layout.addWidget(title)

        guide_text = QTextEdit()
        guide_text.setReadOnly(True)
        guide_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                padding: 12px;
                font-size: 13px;
                color: #333;
            }
        """)
        guide_text.setHtml("""
        <h3>📋 三步快速上手</h3>
        <ol>
        <li><b>拖入 PDF 文件</b> — 将课件 PDF 拖入上方区域，支持批量处理</li>
        <li><b>配置 AI</b> — 点击「⚙️ 设置」填入 API Key（支持 Kimi / OpenAI / Claude / DeepSeek）</li>
        <li><b>选择格式生成</b> — 选择输出格式，点击「开始生成」即可</li>
        </ol>

        <h3>📝 Obsidian 笔记模式</h3>
        <p>将「输出格式」切换为 <b>Obsidian</b>，可配置模板、Vault 路径和课程名称，
        直接输出到您的 Obsidian 知识库中。</p>

        <h3>🔍 模板分析</h3>
        <p>在 Obsidian 模式下选择 .md 模板后，点击「<b>🔍 分析</b>」按钮，
        AI 会自动识别模板风格并优化生成提示词。</p>

        <hr>
        <p style="color: #666; font-size: 12px;">
        💡 提示：所有设置可在「⚙️ 设置」页面中随时修改和保存。</p>
        """)
        layout.addWidget(guide_text, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        got_it_btn = QPushButton("👌 我知道了，开始使用")
        got_it_btn.setFixedSize(180, 36)
        got_it_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2980b9);
                color: white; border: none; border-radius: 4px;
                font-size: 13px; font-weight: 600;
            }
            QPushButton:hover { background-color: #2471a3; }
        """)
        got_it_btn.clicked.connect(dialog.accept)
        btn_row.addWidget(got_it_btn)
        layout.addLayout(btn_row)

        dialog.exec()

        # 标记已完成首次引导
        settings_manager.set("app", "first_run_completed", True)
        settings_manager.save()

    # ═══════════════════════════════════════════
    # P0-2: 检测 API Key 并提示
    # ═══════════════════════════════════════════
    def _check_api_key_and_prompt(self):
        """检测未配置 API Key 时弹出提示。"""
        if settings_manager.has_api_key():
            return

        reply = QMessageBox.question(
            self,
            "🔑 配置 API Key",
            "检测到您还没有配置 AI API Key。\n\n"
            "需要 AI 服务来生成笔记，请先配置 API Key。\n\n"
            "是否现在前往设置页面进行配置？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.show_settings_page()
            # 在设置页面上高亮 API Key 输入框
            self.settings_page.api_key_input.setFocus()

    # ═══════════════════════════════════════════
    # P2-14: 帮助按钮
    # ═══════════════════════════════════════════
    def _show_help_dialog(self):
        """显示帮助信息弹窗。"""
        from PyQt6.QtWidgets import QDialog, QTextEdit, QVBoxLayout

        dialog = QDialog(self)
        dialog.setWindowTitle("❓ 帮助 - Noter 使用说明")
        dialog.setMinimumSize(480, 380)
        dialog.resize(500, 400)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                padding: 12px;
                font-size: 13px;
                color: #333;
            }
        """)
        help_text.setHtml("""
        <h3>❓ 常见问题</h3>

        <p><b>Q: 需要什么 API Key？</b></p>
        <p>支持 Kimi / OpenAI / Claude / DeepSeek，在「⚙️ 设置」中配置。</p>

        <p><b>Q: 支持哪些输出格式？</b></p>
        <p>Word (.docx)、Markdown (.md)、HTML、Obsidian 笔记。</p>

        <p><b>Q: 如何使用模板分析功能？</b></p>
        <p>选择 Obsidian 格式 → 选择 .md 模板 → 点击「🔍 分析」按钮。</p>

        <p><b>Q: 批量处理支持多少文件？</b></p>
        <p>最多支持同时处理 50 个 PDF 文件。</p>

        <p><b>Q: 如何修改输出目录？</b></p>
        <p>在「⚙️ 设置」→「存储设置」中修改「输出目录」。</p>

        <hr>
        <p style="color: #666; font-size: 12px;">
        🔗 更多信息请访问 GitHub 仓库</p>
        """)
        layout.addWidget(help_text, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.setFixedSize(90, 34)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db; color: white;
                border: none; border-radius: 4px; font-size: 13px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        close_btn.clicked.connect(dialog.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        dialog.exec()

    def on_files_dropped(self, files: List[Path]):
        for f in files:
            self.file_list.add_file(f)
        self.selected_files = self.file_list.get_files()

    def on_files_changed(self):
        self.selected_files = self.file_list.get_files()
        self.drop_area.set_file_count(len(self.selected_files))

    def start_processing(self):
        if not self.selected_files:
            self.statusBar().showMessage("请先选择 PDF 文件", 3000)
            return

        # 检查 API Key
        if not settings_manager.has_api_key():
            self.statusBar().showMessage("❌ 未配置 API Key，请先点击「设置」配置", 5000)
            return

        # 清空日志
        self.log_panel.clear_logs()

        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.statusBar().showMessage("🚀 开始处理...", 3000)

        # 获取输出目录（P2-11: 未配置时默认输出到桌面）
        output_folder = settings_manager.get("storage", "output_folder", default="")
        if output_folder:
            output_dir = Path(output_folder)
        else:
            output_dir = Path.home() / "Desktop" / "Noter_Notes"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Obsidian 模式参数
        fmt = self.format_combo.currentText()
        if fmt == "obsidian":
            obsidian_template, obsidian_course, obsidian_vault, obsidian_note_name, obsidian_analysis = self.obsidian_panel.get_values()
        else:
            obsidian_template, obsidian_course, obsidian_vault, obsidian_note_name, obsidian_analysis = None, None, None, None, None

        # 显示调试信息
        self.log_panel.append_log("🚀 开始处理...", "info")
        self.log_panel.append_log(f"文件数量: {len(self.selected_files)}", "info")
        self.log_panel.append_log(f"输出格式: {fmt}", "info")

        # 创建并启动工作线程
        self.worker = WorkerThread(
            self.selected_files,
            self.provider_combo.currentText(),
            fmt,
            output_dir,
            obsidian_template=obsidian_template,
            obsidian_course=obsidian_course,
            obsidian_vault=obsidian_vault,
            obsidian_note_name=obsidian_note_name,
            obsidian_analysis=obsidian_analysis,
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.log.connect(self.on_log)
        self.worker.finished_all.connect(self.on_finished)
        self.worker.start()

    def cancel_processing(self):
        """P2-10: 取消按钮带视觉反馈"""
        if hasattr(self, 'worker') and self.worker:
            self.cancel_btn.setEnabled(False)
            self.cancel_btn.setText("⏹ 正在取消...")
            self.log_panel.append_log("⏹ 正在取消处理...", "info")
            self.worker.cancel()
            self.worker.wait(1000)
            if self.worker.isRunning():
                self.worker.terminate()
            self.cancel_btn.setText("取消")
            self.log_panel.append_log("⏹ 已取消处理", "info")

    def on_progress(self, file_path: Path, progress: int, status: str):
        self.file_list.update_card_status(file_path, status, progress)

    def on_log(self, message: str, level: str):
        if level == "error":
            self.statusBar().showMessage(f"❌ {message}", 5000)
        elif level == "success":
            self.statusBar().showMessage(f"✅ {message}", 3000)
        else:
            self.statusBar().showMessage(message, 3000)

        self.log_panel.append_log(message, level)

    def on_finished(self, success: bool, message: str):
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        if hasattr(self, 'worker'):
            self.worker = None
        self.statusBar().showMessage(message, 5000)

        level = "success" if success else "error"
        self.log_panel.append_log(message, level)

        output_folder = settings_manager.get("storage", "output_folder", default="")
        output_dir = Path(output_folder) if output_folder else Path.home() / "Desktop" / "Noter_Notes"
        self.log_panel.append_log(f"文件保存位置: {output_dir}", "info")

        # P1-7: 处理完成弹窗通知
        if success:
            reply = QMessageBox.information(
                self,
                "✅ 处理完成",
                f"{message}\n\n📂 文件已保存至:\n{output_dir}\n\n是否打开输出目录查看？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                os.startfile(output_dir)
        else:
            log_file = output_dir / "error.log"
            if log_file.exists():
                self.log_panel.append_log(f"详细错误信息请查看: {log_file}", "info")


# ============================================================================
# 应用入口
# ============================================================================

def main():
    import traceback

    def exception_hook(exc_type, exc_value, exc_tb):
        """全局异常处理钩子"""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return

        error_msg = f"💥 程序发生未处理的异常:\n\n"
        error_msg += f"类型: {exc_type.__name__}\n"
        error_msg += f"信息: {exc_value}\n\n"
        error_msg += "详细堆栈:\n"
        error_msg += "".join(traceback.format_exception(exc_type, exc_value, exc_tb))

        print(error_msg)

        try:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                None,
                "程序错误",
                f"程序遇到错误需要关闭：\n\n{exc_type.__name__}: {exc_value}\n\n请查看日志获取详细信息。",
                QMessageBox.StandardButton.Ok,
            )
        except Exception:
            pass

    sys.excepthook = exception_hook

    from PyQt6.QtGui import QIcon
    Theme.init_from_system()

    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    app.setApplicationName("PDF 备考笔记生成器")

    # 设置应用级图标（任务栏、Alt+Tab等）
    icon_path = Path(__file__).parent / "assets" / "noter_icon_v3.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    window = ModernMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
