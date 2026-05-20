"""LogPanel — terminal-inspired log viewer with level filtering and copy."""

import datetime

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QSizePolicy,
)
from PyQt6.QtGui import QColor, QFont

from gui_launcher.theme import Theme


class LogPanel(QFrame):
    """日志面板 — terminal monospace styling, level filtering, copy support."""

    logMessage = pyqtSignal(str, str)

    LEVEL_STYLES = {
        "error":   ("●", "#FF3B30"),
        "success": ("●", "#34C759"),
        "info":    ("●", "#8B8580"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        # Each entry: (timestamp_str, level, message_text)
        self._log_entries: list[tuple[str, str, str]] = []
        self._filter = "all"
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet(
            f"QFrame {{ background-color: {Theme.get('bg_secondary')}; "
            f"border-radius: 4px; border: 1px solid {Theme.get('border_light')}; }}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # ── Header ──
        header = QHBoxLayout()
        header.setSpacing(8)

        title = QLabel("日志")
        title.setStyleSheet(
            f"font-size: 12px; font-weight: 600; color: {Theme.get('text_secondary')}; "
            f"background: transparent; letter-spacing: 0.3px;"
        )
        header.addWidget(title)
        header.addStretch()

        # Filter chips
        self._filter_btns = {}
        for f_key, f_label in [("all", "全部"), ("success", "成功"), ("error", "错误")]:
            btn = QPushButton(f_label)
            btn.setFixedHeight(24)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(self._filter_btn_style(f_key == "all"))
            btn.clicked.connect(lambda checked, k=f_key: self._set_filter(k))
            header.addWidget(btn)
            self._filter_btns[f_key] = btn

        # Copy button
        copy_btn = QPushButton("📋")
        copy_btn.setFixedSize(28, 24)
        copy_btn.setToolTip("复制全部日志")
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.get('text_tertiary')};
                border: 1px solid {Theme.get('border_light')};
                border-radius: 4px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {Theme.get('bg_tertiary')};
                color: {Theme.get('text_primary')};
            }}
        """)
        copy_btn.clicked.connect(self._copy_logs)
        header.addWidget(copy_btn)

        layout.addLayout(header)

        # ── Log area ──
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(80)
        self.log_text.setMaximumHeight(140)
        self.log_text.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding
        )
        self._apply_editor_style()
        layout.addWidget(self.log_text)

    def _apply_editor_style(self):
        bg = Theme.get('bg_primary') if not Theme.DARK_MODE else '#151426'
        fg = Theme.get('text_primary')
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {bg};
                border: 1px solid {Theme.get('border_light')};
                border-radius: 4px;
                padding: 8px 10px;
                font-family: "Cascadia Code", "JetBrains Mono", "Consolas", "Microsoft YaHei", monospace;
                font-size: 12px;
                color: {fg};
            }}
        """)

    def _filter_btn_style(self, active: bool) -> str:
        if active:
            return f"""
                QPushButton {{
                    background-color: {Theme.ACCENT_PRIMARY};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 600;
                    padding: 0 10px;
                }}
            """
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.get('text_tertiary')};
                border: 1px solid {Theme.get('border_light')};
                border-radius: 4px;
                font-size: 11px;
                padding: 0 10px;
            }}
            QPushButton:hover {{
                background-color: {Theme.get('bg_tertiary')};
                color: {Theme.get('text_primary')};
            }}
        """

    def _set_filter(self, level: str):
        self._filter = level
        for key, btn in self._filter_btns.items():
            btn.setStyleSheet(self._filter_btn_style(key == level))
        self._rebuild_display()

    def _rebuild_display(self):
        """Re-render log with current filter from stored entries."""
        self.log_text.clear()
        for ts, level, msg in self._log_entries:
            if self._filter == "all" or self._filter == level:
                self._append_formatted(ts, level, msg)

    def _append_formatted(self, ts: str, level: str, message: str):
        """Append a single HTML-formatted log line."""
        dot, color = self.LEVEL_STYLES.get(level, ("●", "#8B8580"))
        ts_color = Theme.get('text_tertiary')
        html = (
            f'<span style="color: {ts_color}">{ts}</span>'
            f' <span style="color: {color}">{dot}</span>'
            f' {message}'
        )
        self.log_text.append(html)
        # Auto-scroll
        sb = self.log_text.verticalScrollBar()
        sb.setValue(sb.maximum())

    def append_log(self, message: str, level: str = "info"):
        """Store and display a timestamped log entry."""
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self._log_entries.append((ts, level, message))

        if self._filter == "all" or self._filter == level:
            self._append_formatted(ts, level, message)

    def clear_logs(self):
        self._log_entries.clear()
        self.log_text.clear()

    def get_text(self) -> str:
        return "\n".join(f"[{l.upper()}] {m}" for _, l, m in self._log_entries)

    def _copy_logs(self):
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            return
        text = "\n".join(
            f"{ts} [{l.upper()}] {m}" for ts, l, m in self._log_entries
        )
        app.clipboard().setText(text)
        self.append_log("日志已复制到剪贴板", "info")
