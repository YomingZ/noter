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
from gui_launcher.settings_manager import SettingsManager, CONFIG_DIR, SETTINGS_FILE
from gui_launcher.widget_factory import WidgetFactory
from gui_launcher.log_panel import LogPanel
from gui_launcher.drop_area import DropArea
from gui_launcher.file_card import FileCard
from gui_launcher.file_list_area import FileListArea
from gui_launcher.title_bar import CustomTitleBar
from gui_launcher.settings_page import SettingsPage

settings_manager = SettingsManager()


# ============================================================================
# 工作线程
# ============================================================================

class WorkerThread(QThread):
    """Thin signal-forwarder: reads settings → delegates to ProcessingService → emits signals."""
    progress = pyqtSignal(Path, int, str)
    log = pyqtSignal(str, str)
    finished_all = pyqtSignal(bool, str)

    def __init__(self, files, provider, output_format, output_dir,
                 obsidian_template=None, obsidian_course=None, obsidian_vault=None):
        super().__init__()
        self.files = files
        self.provider = provider
        self.output_format = output_format
        self.output_dir = output_dir
        self.obsidian_template = obsidian_template
        self.obsidian_course = obsidian_course
        self.obsidian_vault = obsidian_vault
        self._svc = None

    def cancel(self):
        if self._svc:
            self._svc.cancel()

    def run(self):
        import sys
        src_dir = str(SCRIPT_DIR / "src")
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)

        try:
            from pdf_summarizer.processing_service import ProcessingService
        except ImportError as e:
            self.log.emit(f"导入模块失败: {e}", "error")
            self.finished_all.emit(False, "模块导入失败")
            return

        ai_config = {
            "provider": settings_manager.get("ai", "provider", default="kimi"),
            "api_key": settings_manager.get("ai", "api_key", default=""),
            "model": settings_manager.get("ai", "model", default="moonshot-v1-8k"),
            "base_url": settings_manager.get("ai", "base_url", default=""),
            "temperature": settings_manager.get("ai", "temperature", default=0.7),
        }

        self._svc = ProcessingService(
            provider=self.provider,
            output_format=self.output_format,
            output_dir=Path(self.output_dir),
            obsidian_template=Path(self.obsidian_template) if self.obsidian_template else None,
            obsidian_course=self.obsidian_course,
            obsidian_vault=Path(self.obsidian_vault) if self.obsidian_vault else None,
        )

        try:
            self._svc.configure_ai(ai_config)
        except ValueError as e:
            self.log.emit(str(e), "error")
            self.finished_all.emit(False, str(e))
            return

        total = len(self.files)
        success_count = 0

        for result in self._svc.process_batch(self.files):
            fp = result.input_file or Path("unknown")

            if not result.success:
                error_msg = result.error_message or "未知错误"
                self.progress.emit(fp, 0, "failed")
                self.log.emit(f"失败: {error_msg[:300]}", "error")
                continue

            self.progress.emit(fp, 100, "completed")
            self.log.emit(f"完成: {fp.name}", "success")
            success_count += 1

        if success_count == total:
            self.finished_all.emit(True, f"成功处理 {success_count}/{total}")
        else:
            self.finished_all.emit(False, f"成功 {success_count}/{total}")


# ============================================================================
# 主窗口
# ============================================================================

class ModernMainWindow(QMainWindow):
    """现代风格主窗口"""

    def __init__(self):
        super().__init__()
        self.selected_files: List[Path] = []
        self.worker: Optional[WorkerThread] = None

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setup_window()
        self.setup_ui()
        self.apply_theme()

    def setup_window(self):
        self.setWindowTitle("PDF 备考笔记生成器")
        self.setMinimumSize(680, 680)
        self.resize(720, 760)
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

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 10)
        self.main_container.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(self.main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 标题栏
        self.title_bar = CustomTitleBar(self)
        self.title_bar.backClicked.connect(self.show_main_page)
        main_layout.addWidget(self.title_bar)

        # 页面容器
        self.pages = QStackedWidget()
        main_layout.addWidget(self.pages)

        # 主页面
        self.main_page = self.create_main_page()
        self.pages.addWidget(self.main_page)

        # 设置页面
        self.settings_page = SettingsPage()
        self.settings_page.settingsSaved.connect(self.on_settings_saved)
        self.pages.addWidget(self.settings_page)

        # 加载已保存的 Obsidian vault 路径
        saved_vault = settings_manager.get("storage", "obsidian_vault", default="")
        if saved_vault:
            self.obsidian_panel.vault_edit.setText(saved_vault)

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
        options_frame.setStyleSheet(f"QFrame {{ background-color: {Theme.get('bg_secondary')}; border-radius: 12px; }}")
        options_layout = QHBoxLayout(options_frame)
        options_layout.setContentsMargins(16, 12, 16, 12)
        options_layout.setSpacing(24)

        provider_layout = QVBoxLayout()
        provider_layout.setSpacing(4)
        provider_label = QLabel("AI 提供商")
        provider_label.setStyleSheet(f"font-size: 12px; color: {Theme.get('text_secondary')}; background: transparent;")
        provider_layout.addWidget(provider_label)
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["kimi", "openai", "claude"])
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
        self.settings_btn.setFixedSize(90, 36)
        self.settings_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {Theme.get('bg_tertiary')}; color: {Theme.get('text_primary')}; border: none; border-radius: 10px; font-size: 13px; }}
            QPushButton:hover {{ background-color: {Theme.get('bg_elevated')}; }}
        """)
        self.settings_btn.clicked.connect(self.show_settings_page)
        options_layout.addWidget(self.settings_btn)

        # 主题切换
        self.theme_btn = QPushButton("🌙")
        self.theme_btn.setFixedSize(36, 36)
        self.theme_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {Theme.get('bg_tertiary')}; border: none; border-radius: 18px; font-size: 14px; }}
            QPushButton:hover {{ background-color: {Theme.get('bg_elevated')}; }}
        """)
        self.theme_btn.clicked.connect(self.toggle_theme)
        options_layout.addWidget(self.theme_btn)

        layout.addWidget(options_frame)

        from gui_launcher.obsidian_panel import ObsidianPanel
        self.obsidian_panel = ObsidianPanel()
        self.obsidian_panel.browse_template_requested.connect(self._browse_obsidian_template)
        self.obsidian_panel.browse_vault_requested.connect(self._browse_obsidian_vault)
        self.obsidian_panel.courses_reload_requested.connect(self._reload_obsidian_courses)
        layout.addWidget(self.obsidian_panel)

        # 连接格式切换事件
        self.format_combo.currentTextChanged.connect(self._on_format_changed)

        # 日志面板
        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel, 1)

        # 底部操作栏
        action_bar = QFrame()
        action_bar.setStyleSheet("background: transparent;")
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(12)

        action_layout.addStretch()

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setFixedSize(80, 44)
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {Theme.get('bg_secondary')}; color: {Theme.get('text_primary')}; border: 1px solid {Theme.get('border')}; border-radius: 12px; font-size: 14px; }}
            QPushButton:hover {{ background-color: {Theme.get('bg_tertiary')}; }}
            QPushButton:disabled {{ color: {Theme.get('text_tertiary')}; }}
        """)
        self.cancel_btn.clicked.connect(self.cancel_processing)
        self.cancel_btn.setEnabled(False)
        action_layout.addWidget(self.cancel_btn)

        self.start_btn = QPushButton("开始生成")
        self.start_btn.setFixedSize(120, 44)
        self.start_btn.setStyleSheet(f"""
            QPushButton {{ background: {Theme.gradient_accent()}; color: white; border: none; border-radius: 12px; font-size: 14px; font-weight: 600; }}
            QPushButton:hover {{ background-color: {Theme.ACCENT_AMBER_DARK}; }}
            QPushButton:disabled {{ background: {Theme.get('bg_tertiary')}; color: {Theme.get('text_tertiary')}; }}
        """)
        self.start_btn.clicked.connect(self.start_processing)
        action_layout.addWidget(self.start_btn)

        layout.addWidget(action_bar)

        scroll.setWidget(scroll_content)
        outer_layout.addWidget(scroll)
        return page

    def _combo_style(self) -> str:
        return f"""
            QComboBox {{ background-color: {Theme.get('bg_tertiary')}; color: {Theme.get('text_primary')}; border: 1px solid {Theme.get('border_light')}; border-radius: 8px; padding: 8px 12px; font-size: 13px; min-width: 90px; }}
            QComboBox:hover {{ border-color: {Theme.get('border')}; }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox::down-arrow {{ image: none; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 5px solid {Theme.get('text_secondary')}; }}
            QComboBox QAbstractItemView {{ background-color: {Theme.get('bg_elevated')}; color: {Theme.get('text_primary')}; border: 1px solid {Theme.get('border')}; border-radius: 8px; selection-background-color: {Theme.ACCENT_BLUE}; }}
        """

    def apply_theme(self):
        bg = Theme.get('bg_primary')
        self.main_container.setStyleSheet(f"""
            #mainContainer {{ background-color: {bg}; border-radius: 12px; border: 1px solid {Theme.get('border_light')}; }}
        """)
        self.title_bar.setStyleSheet(f"QFrame {{ background-color: {bg}; border: none; border-top-left-radius: 12px; border-top-right-radius: 12px; }}")
        self.theme_btn.setText("☀️" if Theme.DARK_MODE else "🌙")

    def toggle_theme(self):
        Theme.toggle()
        self.apply_theme()
        self.drop_area.update_style()
        self.provider_combo.setStyleSheet(self._combo_style())
        self.format_combo.setStyleSheet(self._combo_style())

    def show_settings_page(self):
        self.settings_page.load_settings()
        self.title_bar.set_show_back(True)
        self.title_bar.set_title("设置")
        # Fade-style page switch via opacity animation
        self._animate_page_switch(1)

    def _animate_page_switch(self, index: int):
        """Smooth crossfade page transition using window opacity."""
        if self.pages.currentIndex() == index:
            return
        # Quick opacity fade for smooth feel
        self._page_anim = QPropertyAnimation(self, b"windowOpacity")
        self._page_anim.setDuration(120)
        self._page_anim.setStartValue(0.92)
        self._page_anim.setEndValue(1.0)
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
        path, _ = QFileDialog.getOpenFileName(
            self, "选择笔记模板", str(Path.home()),
            "Markdown 文件 (*.md);;所有文件 (*)"
        )
        if path:
            self.obsidian_panel.template_edit.setText(path)

    def _browse_obsidian_vault(self):
        """Open folder dialog to select Obsidian vault directory."""
        from PyQt6.QtWidgets import QFileDialog
        path = QFileDialog.getExistingDirectory(
            self, "选择 Obsidian Vault 目录", str(Path.home())
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

    def show_main_page(self):
        self.title_bar.set_show_back(False)
        self.title_bar.set_title("PDF 备考笔记生成器")
        self._animate_page_switch(0)

    def on_settings_saved(self):
        self.show_main_page()

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

        # 获取输出目录（使用用户配置的或默认的 notes 目录）
        output_folder = settings_manager.get("storage", "output_folder", default="")
        if output_folder:
            output_dir = Path(output_folder)
        else:
            output_dir = SCRIPT_DIR / "notes"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Obsidian 模式参数
        fmt = self.format_combo.currentText()
        if fmt == "obsidian":
            obsidian_template, obsidian_course, obsidian_vault = self.obsidian_panel.get_values()
        else:
            obsidian_template, obsidian_course, obsidian_vault = None, None, None
        # 保存 vault 路径供下次使用
        if obsidian_vault:
            settings_manager.set("storage", "obsidian_vault", obsidian_vault)

        # 创建并启动工作线程
        self.worker = WorkerThread(
            self.selected_files,
            self.provider_combo.currentText(),
            fmt,
            output_dir,
            obsidian_template=obsidian_template,
            obsidian_course=obsidian_course,
            obsidian_vault=obsidian_vault,
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.log.connect(self.on_log)
        self.worker.finished_all.connect(self.on_finished)
        self.worker.start()

    def cancel_processing(self):
        if hasattr(self, 'worker') and self.worker:
            self.worker.cancel()
            self.worker.wait(1000)  # 等待1秒
            if self.worker.isRunning():
                self.worker.terminate()

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
        output_dir = Path(output_folder) if output_folder else SCRIPT_DIR / "notes"
        self.log_panel.append_log(f"文件保存位置: {output_dir}", "info")

        if not success:
            log_file = output_dir / "error.log"
            if log_file.exists():
                self.log_panel.append_log(f"详细错误信息请查看: {log_file}", "info")


# ============================================================================
# 应用入口
# ============================================================================

def main():
    Theme.init_from_system()

    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    app.setApplicationName("PDF 备考笔记生成器")

    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    window = ModernMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
