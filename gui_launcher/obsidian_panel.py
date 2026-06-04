"""ObsidianPanel — step-by-step vault configuration with wizard-style cards."""

from pathlib import Path
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QSizePolicy,
)

from gui_launcher.theme import Theme
from gui_launcher.template_editor import TemplateEditor


class StepCard(QFrame):
    """A single step card with numbered badge and content area."""

    def __init__(self, step_num: str, title: str, hint: str = "", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.get('surface_1')};
                border: 1px solid {Theme.get('border_lighter')};
                border-radius: 4px;
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        # Number badge
        badge = QLabel(step_num)
        badge.setFixedSize(28, 28)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            f"background-color: {Theme.ACCENT_PRIMARY}; color: white; "
            f"border-radius: 14px; font-size: 13px; font-weight: 700; "
            f"border: none;"
        )
        layout.addWidget(badge)

        # Content
        content_col = QVBoxLayout()
        content_col.setSpacing(2)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"font-size: 13px; font-weight: 500; color: {Theme.get('text_primary')}; "
            f"background: transparent;"
        )
        content_col.addWidget(title_label)

        if hint:
            hint_label = QLabel(hint)
            hint_label.setStyleSheet(
                f"font-size: 11px; color: {Theme.get('text_tertiary')}; "
                f"background: transparent;"
            )
            content_col.addWidget(hint_label)

        layout.addLayout(content_col, 1)
        self._content_layout = layout

    def add_widget(self, widget):
        from PyQt6.QtWidgets import QLayout
        if isinstance(widget, QLayout):
            self._content_layout.addLayout(widget)
        else:
            self._content_layout.addWidget(widget)


class ObsidianPanel(QFrame):
    """Self-contained Obsidian config panel: template + vault + course.

    Displays as a sequence of step cards for clear visual guidance.
    """

    browse_template_requested = pyqtSignal()
    browse_vault_requested = pyqtSignal()
    courses_reload_requested = pyqtSignal()
    template_analysis_requested = pyqtSignal(str)  # Emits template path when analysis requested
    template_analyzed = pyqtSignal(object)  # Emits TemplateAnalysisResult when complete

    def __init__(self, parent=None):
        super().__init__(parent)
        self._analysis_result = None  # Store completed analysis
        self._build_ui()

    def _build_ui(self):
        self.setVisible(False)  # hidden until obsidian format selected
        self.setStyleSheet(
            f"QFrame {{ background-color: {Theme.get('bg_secondary')}; "
            f"border-radius: 4px; border: 1px solid {Theme.get('border_light')}; }}"
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 14)
        outer.setSpacing(10)

        # ── Header ──
        header = QHBoxLayout()
        header.setSpacing(8)

        icon = QLabel("📝")
        icon.setStyleSheet("font-size: 16px; background: transparent;")
        header.addWidget(icon)

        title = QLabel("Obsidian 笔记生成")
        title.setStyleSheet(
            f"font-size: 14px; font-weight: 600; color: {Theme.get('text_primary')}; "
            f"background: transparent;"
        )
        header.addWidget(title)

        header.addStretch()

        self.status_badge = QLabel("未配置")
        self.status_badge.setStyleSheet(self._badge_style("inactive"))
        header.addWidget(self.status_badge)

        outer.addLayout(header)

        # ── Step 1: Template ──
        s1 = StepCard("1", "选择笔记模板", "已有 Obsidian 笔记的 .md 文件，作为格式参考")
        self.template_edit = QLineEdit()
        self.template_edit.setPlaceholderText("点击右侧按钮选择 .md 模板文件...")
        self.template_edit.setStyleSheet(self._input_style())
        self.template_edit.textChanged.connect(self._update_status)
        s1_row = QHBoxLayout()
        s1_row.setSpacing(6)
        s1_row.addWidget(self.template_edit, 1)

        t_btn = QPushButton("选择模板")
        t_btn.setFixedHeight(34)
        t_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        t_btn.setStyleSheet(self._btn_style())
        t_btn.clicked.connect(self._on_browse_template)
        s1_row.addWidget(t_btn)
        
        edit_btn = QPushButton("编辑")
        edit_btn.setFixedHeight(34)
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.setStyleSheet(self._btn_style())
        edit_btn.clicked.connect(self._on_edit_template)
        s1_row.addWidget(edit_btn)

        analyze_btn = QPushButton("🔍 分析")
        analyze_btn.setFixedHeight(34)
        analyze_btn.setToolTip("AI 智能分析模板并优化生成配置\n\n"
                               "分析模板风格、检测缺失特征、\n"
                               "生成个性化提示词，提升笔记质量\n\n"
                               "💡 提示：请先选择模板文件后再点击")
        analyze_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                padding: 0 12px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        analyze_btn.clicked.connect(self._on_analyze_template)
        self.analyze_btn = analyze_btn
        s1_row.addWidget(analyze_btn)
        
        s1.add_widget(s1_row)
        outer.addWidget(s1)

        # ── Step 2: Vault ──
        s2 = StepCard("2", "Vault 路径", "Obsidian 库的根目录（collegenote）")
        v_row = QHBoxLayout()
        v_row.setSpacing(6)

        self.vault_edit = QLineEdit()
        self.vault_edit.setPlaceholderText("粘贴或浏览选择 Vault 根目录...")
        self.vault_edit.setStyleSheet(self._input_style())
        self.vault_edit.textChanged.connect(self._update_status)
        v_row.addWidget(self.vault_edit, 1)

        v_btn = QPushButton("浏览")
        v_btn.setFixedHeight(34)
        v_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        v_btn.setStyleSheet(self._btn_style())
        v_btn.clicked.connect(self._on_browse_vault)
        v_row.addWidget(v_btn)

        self.reload_btn = QPushButton("↻")
        self.reload_btn.setFixedSize(36, 34)
        self.reload_btn.setToolTip("刷新课程列表")
        self.reload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reload_btn.setStyleSheet(self._btn_style())
        self.reload_btn.clicked.connect(self._on_reload_courses)
        v_row.addWidget(self.reload_btn)

        s2.add_widget(v_row)
        outer.addWidget(s2)

        # ── Step 3: Course ──
        s3 = StepCard("3", "课程名称", "从 vault 加载的课程列表，或手动输入")
        self.course_combo = QComboBox()
        self.course_combo.setEditable(True)
        self.course_combo.setPlaceholderText("🎓 输入或选择课程...")
        self.course_combo.lineEdit().setPlaceholderText("如: 量子化学")
        self.course_combo.setStyleSheet(self._combo_style())
        self.course_combo.currentTextChanged.connect(self._update_status)
        s3.add_widget(self.course_combo)
        outer.addWidget(s3)

        # ── Step 4: Note Name ──
        s4 = StepCard("4", "笔记名称", "自定义生成笔记的文件名（可选，默认使用 PDF 文件名）")
        self.note_name_edit = QLineEdit()
        self.note_name_edit.setPlaceholderText("如：第一章_量子力学基础（留空则使用 PDF 文件名）")
        self.note_name_edit.setStyleSheet(self._input_style())
        s4.add_widget(self.note_name_edit)
        outer.addWidget(s4)

    # ── Style helpers ──

    @staticmethod
    def _input_style() -> str:
        return f"""
            QLineEdit {{
                background-color: {Theme.get('bg_tertiary')};
                border: 1px solid {Theme.get('border_light')};
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 12px;
                color: {Theme.get('text_primary')};
                min-height: 18px;
            }}
            QLineEdit:focus {{
                border-color: {Theme.ACCENT_PRIMARY};
            }}
            QLineEdit::placeholder {{
                color: {Theme.get('text_tertiary')};
            }}
        """

    @staticmethod
    def _btn_style() -> str:
        return f"""
            QPushButton {{
                background-color: {Theme.get('bg_tertiary')};
                color: {Theme.get('text_primary')};
                border: 1px solid {Theme.get('border_light')};
                border-radius: 4px;
                font-size: 12px;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background-color: {Theme.get('bg_elevated')};
                border-color: {Theme.ACCENT_PRIMARY};
            }}
        """

    @staticmethod
    def _combo_style() -> str:
        return f"""
            QComboBox {{
                background-color: {Theme.get('bg_tertiary')};
                border: 1px solid {Theme.get('border_light')};
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 12px;
                color: {Theme.get('text_primary')};
                min-width: 140px;
            }}
            QComboBox:hover {{ border-color: {Theme.ACCENT_PRIMARY}; }}
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
        """

    @staticmethod
    def _badge_style(state: str) -> str:
        if state == "ready":
            return (
                f"background-color: {Theme.SUCCESS_GREEN}; color: white; "
                f"border-radius: 4px; padding: 2px 10px; font-size: 11px; font-weight: 600;"
            )
        return (
            f"background-color: {Theme.get('bg_tertiary')}; color: {Theme.get('text_tertiary')}; "
            f"border-radius: 4px; padding: 2px 10px; font-size: 11px;"
        )

    # ── Public API ──

    def _update_status(self):
        t = self.template_edit.text().strip()
        v = self.vault_edit.text().strip()
        c = self.course_combo.currentText().strip()

        # Update analyze button state
        if hasattr(self, 'analyze_btn'):
            self.analyze_btn.setEnabled(bool(t) and Path(t).exists())

        if t and v and c:
            if self._analysis_result:
                self.status_badge.setText("已分析 ✓")
                self.status_badge.setStyleSheet(
                    f"background-color: #27ae60; color: white; "
                    f"border-radius: 4px; padding: 2px 10px; font-size: 11px; font-weight: 600;"
                )
            else:
                self.status_badge.setText("就绪")
                self.status_badge.setStyleSheet(self._badge_style("ready"))
        else:
            self.status_badge.setText("未配置")
            self.status_badge.setStyleSheet(self._badge_style("inactive"))

    def _on_browse_template(self):
        self.browse_template_requested.emit()

    def _on_analyze_template(self):
        """Trigger template analysis workflow."""
        template_path = self.template_edit.text().strip()
        if not template_path or not Path(template_path).exists():
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "模板未找到",
                "请先选择一个有效的模板文件，然后再进行分析。"
            )
            return

        # Emit signal to parent (main window) to handle async analysis
        self.template_analysis_requested.emit(template_path)

    def set_analysis_result(self, result):
        """Store and display analysis result.

        Args:
            result: TemplateAnalysisResult from TemplateAnalyzer
        """
        self._analysis_result = result
        self._update_status()
        self.template_analyzed.emit(result)

    def get_analysis_result(self):
        """Get stored analysis result."""
        return self._analysis_result

    def _on_edit_template(self):
        template_path = self.template_edit.text().strip()
        if template_path and Path(template_path).exists():
            editor = TemplateEditor(Path(template_path), parent=self)
            editor.exec()
        elif template_path:
            # File doesn't exist but path is provided
            editor = TemplateEditor(Path(template_path), parent=self)
            editor.exec()
        else:
            # No template selected, create new
            editor = TemplateEditor(None, parent=self)
            if editor.exec() and editor.template_path:
                self.template_edit.setText(str(editor.template_path))

    def _on_browse_vault(self):
        self.browse_vault_requested.emit()

    def _on_reload_courses(self):
        self.courses_reload_requested.emit()

    def get_values(self):
        """Return (template_path, course_name, vault_path, note_name, analysis_result)."""
        return (
            self.template_edit.text().strip(),
            self.course_combo.currentText().strip(),
            self.vault_edit.text().strip(),
            self.note_name_edit.text().strip() or None,
            self._analysis_result,  # New: include analysis result
        )

    def set_values(self, *, template: str = "", vault: str = "", course: str = "", note_name: str = ""):
        self.template_edit.setText(template)
        self.vault_edit.setText(vault)
        if course:
            self.course_combo.setCurrentText(course)
        if note_name:
            self.note_name_edit.setText(note_name)

    def set_active(self, active: bool):
        """P1-4: Obsidian 面板动画展开/收起"""
        if active == self.isVisible():
            return
        if active:
            self.show()
            self.raise_()
            # 展开动画：使用 QGraphicsOpacityEffect
            from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
            from PyQt6.QtWidgets import QGraphicsOpacityEffect
            self._opacity_effect = QGraphicsOpacityEffect()
            self._opacity_effect.setOpacity(0.0)
            self.setGraphicsEffect(self._opacity_effect)
            self._opacity_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
            self._opacity_anim.setDuration(200)
            self._opacity_anim.setStartValue(0.0)
            self._opacity_anim.setEndValue(1.0)
            self._opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._opacity_anim.start()
        else:
            self.hide()

    def populate_courses(self, courses: list[str]):
        """Replace combo items while preserving current selection."""
        current = self.course_combo.currentText()
        self.course_combo.clear()
        self.course_combo.addItems(courses)
        if current and current in courses:
            self.course_combo.setCurrentText(current)
