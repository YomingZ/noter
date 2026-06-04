"""Template Editor Dialog for Obsidian note templates."""

from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLabel, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from gui_launcher.theme import Theme


class TemplateEditor(QDialog):
    """Dialog for editing Markdown note templates."""

    def __init__(
        self,
        template_path: Optional[Path] = None,
        parent=None
    ):
        super().__init__(parent)
        self.template_path = template_path
        self.original_content = ""
        self.setWindowTitle("笔记模板编辑器")
        self.setMinimumSize(800, 600)
        self._setup_ui()
        self._load_template()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header info
        info_label = QLabel(
            "编辑笔记模板，使用 {{content}} 占位符标记笔记内容插入位置"
        )
        info_label.setStyleSheet(
            f"font-size: 12px; color: {Theme.get('text_secondary')};"
            f"background: transparent;"
        )
        layout.addWidget(info_label)

        # Text edit
        self.text_edit = QTextEdit()
        font = QFont("Consolas", 10)
        self.text_edit.setFont(font)
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Theme.get('bg_secondary')};
                color: {Theme.get('text_primary')};
                border: 1px solid {Theme.get('border')};
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }}
        """)
        layout.addWidget(self.text_edit, 1)

        # Button row
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.save_btn = QPushButton("保存")
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.ACCENT_PRIMARY};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {Theme.ACCENT_PRIMARY_DARK};
            }}
        """)
        self.save_btn.clicked.connect(self._save_template)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.get('bg_tertiary')};
                color: {Theme.get('text_primary')};
                border: 1px solid {Theme.get('border')};
                border-radius: 4px;
                padding: 8px 20px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {Theme.get('bg_elevated')};
            }}
        """)
        self.cancel_btn.clicked.connect(self._on_cancel)

        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        layout.addLayout(button_layout)

    def _load_template(self):
        if self.template_path and self.template_path.exists():
            try:
                self.original_content = self.template_path.read_text(encoding="utf-8")
                self.text_edit.setPlainText(self.original_content)
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "加载失败",
                    f"无法加载模板文件: {str(e)}"
                )

    def _save_template(self):
        if not self.template_path:
            # Ask where to save
            path, _ = QFileDialog.getSaveFileName(
                self,
                "保存模板",
                "",
                "Markdown 文件 (*.md)"
            )
            if not path:
                return
            self.template_path = Path(path)

        try:
            content = self.text_edit.toPlainText()
            self.template_path.write_text(content, encoding="utf-8")
            self.original_content = content
            QMessageBox.information(
                self,
                "保存成功",
                "模板已成功保存！"
            )
            self.accept()
        except Exception as e:
            QMessageBox.warning(
                self,
                "保存失败",
                f"无法保存模板文件: {str(e)}"
            )

    def _on_cancel(self):
        current = self.text_edit.toPlainText()
        if current != self.original_content:
            reply = QMessageBox.question(
                self,
                "确认退出",
                "模板内容已修改，是否要保存？",
                QMessageBox.StandardButton.Yes |
                QMessageBox.StandardButton.No |
                QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._save_template()
            elif reply == QMessageBox.StandardButton.No:
                self.reject()
        else:
            self.reject()

    def get_edited_content(self) -> str:
        return self.text_edit.toPlainText()
