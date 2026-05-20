"""FileCard — 文件卡片组件 with avatar circles and animated progress."""

import math
from pathlib import Path

from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QWidget,
)
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QFont

from gui_launcher.theme import Theme


# ── Deterministic color palette for avatars ──
AVATAR_GRADIENTS = [
    ("#D4A047", "#B8863A"),  # Amber
    ("#4A6CF7", "#3451DB"),  # Blue
    ("#7C5CBF", "#5E3D9E"),  # Purple
    ("#2EAF7D", "#239063"),  # Emerald
    ("#E8634A", "#CC4A32"),  # Coral
    ("#5AB0D6", "#3E94BC"),  # Sky
    ("#D94F8C", "#BF3070"),  # Rose
    ("#6B8C5E", "#537048"),  # Sage
]


def _avatar_colors(name: str) -> tuple:
    """Deterministic color pair from filename."""
    idx = abs(hash(name)) % len(AVATAR_GRADIENTS)
    return AVATAR_GRADIENTS[idx]


class FileCard(QFrame):
    """文件卡片 — 显示文件信息、状态、进度 with rich visuals."""

    def __init__(self, file_path: Path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self._status = "pending"
        self._progress_value = 0
        self._anim_progress = 0  # for smooth animation target
        self.setup_ui()

    def setup_ui(self):
        self.setFixedHeight(72)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_card_style()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 16, 10)
        layout.setSpacing(12)

        # ── Avatar circle with initial ──
        self.avatar = _AvatarLabel(
            self.file_path.stem[0].upper() if self.file_path.stem else "?",
            _avatar_colors(self.file_path.stem or "file"),
        )
        self.avatar.setFixedSize(44, 44)
        layout.addWidget(self.avatar)

        # ── Info column ──
        info_col = QVBoxLayout()
        info_col.setSpacing(3)

        self.name_label = QLabel(self.file_path.name)
        self.name_label.setStyleSheet(
            f"font-size: 13.5px; font-weight: 500; color: {Theme.get('text_primary')}; "
            f"background: transparent;"
        )
        self.name_label.setWordWrap(False)
        self.name_label.setMinimumWidth(80)
        info_col.addWidget(self.name_label)

        # Size + status row
        meta_row = QHBoxLayout()
        meta_row.setSpacing(8)

        size_str = self._format_size(
            self.file_path.stat().st_size if self.file_path.exists() else 0
        )
        self.size_label = QLabel(size_str)
        self.size_label.setStyleSheet(
            f"font-size: 11.5px; color: {Theme.get('text_tertiary')}; "
            f"background: transparent;"
        )
        meta_row.addWidget(self.size_label)

        meta_row.addStretch()

        info_col.addLayout(meta_row)
        layout.addLayout(info_col, 1)

        # ── Status column ──
        status_col = QVBoxLayout()
        status_col.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        status_col.setSpacing(4)

        self.status_dot = QLabel("●")
        self.status_dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_dot.setFixedSize(16, 16)
        status_col.addWidget(self.status_dot)

        self.status_label = QLabel("待处理")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.status_label.setStyleSheet(
            f"font-size: 11px; color: {Theme.get('text_tertiary')}; "
            f"background: transparent;"
        )
        status_col.addWidget(self.status_label)

        # 现在设置初始状态（必须在 status_dot 和 status_label 定义之后）
        self._apply_status_visuals("pending")

        layout.addLayout(status_col)

        # ── Compact progress bar ──
        self.progress_container = QFrame()
        self.progress_container.setFixedSize(64, 4)
        self.progress_container.setStyleSheet(
            f"background-color: {Theme.get('bg_tertiary')}; "
            f"border-radius: 2px; border: none;"
        )
        prog_layout = QHBoxLayout(self.progress_container)
        prog_layout.setContentsMargins(0, 0, 0, 0)
        prog_layout.setSpacing(0)

        self.progress_fill = QFrame()
        self.progress_fill.setFixedWidth(0)
        self.progress_fill.setStyleSheet(
            f"background-color: {Theme.ACCENT_PRIMARY}; "
            f"border-radius: 2px; border: none;"
        )
        prog_layout.addWidget(self.progress_fill)
        prog_layout.addStretch()

        layout.addWidget(self.progress_container)

        # ── Hover effect ──
        self._hover_showing = False

    def _update_card_style(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.get('surface_1')};
                border: 1px solid {Theme.get('border_light')};
                border-radius: 4px;
            }}
            QFrame:hover {{
                border-color: {Theme.get('border')};
            }}
        """)

    def _format_size(self, size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def _apply_status_visuals(self, status: str):
        """Update status dot color and label text."""
        styles = {
            "pending":     (Theme.get('text_tertiary'), "待处理"),
            "processing":  (Theme.ACCENT_PRIMARY,       "处理中"),
            "completed":   (Theme.SUCCESS_GREEN,        "已完成"),
            "failed":      (Theme.ERROR_RED,            "失败"),
        }
        dot_color, label = styles.get(status, styles["pending"])
        self.status_dot.setStyleSheet(
            f"font-size: 10px; color: {dot_color}; background: transparent;"
        )
        self.status_label.setText(label)

    def set_status(self, status: str, progress: int = 0):
        """Update card status with smooth progress animation."""
        self._status = status
        self._apply_status_visuals(status)

        # Smooth progress animation
        self._animate_progress(progress)

        # Update progress fill color on completion/failure
        chunk_color = {
            "processing": Theme.ACCENT_PRIMARY,
            "completed":  Theme.SUCCESS_GREEN,
            "failed":     Theme.ERROR_RED,
        }.get(status, Theme.ACCENT_PRIMARY)
        self.progress_fill.setStyleSheet(
            f"background-color: {chunk_color}; border-radius: 2px; border: none;"
        )

    def _animate_progress(self, target: int):
        """Smoothly animate progress bar to target value."""
        self._progress_target = target
        # Use a simple step approach since QPropertyAnimation on width is tricky
        # without a custom widget. We'll do a 10-step eased animation.
        self._anim_step = 0
        self._anim_start = self.progress_fill.width()
        self._anim_total_steps = 15
        self._anim_timer = self.startTimer(20)

    def timerEvent(self, event):
        """Step the progress animation."""
        if self._anim_step >= self._anim_total_steps:
            self.killTimer(event.timerId())
            final_w = int(64 * self._progress_target / 100)
            self.progress_fill.setFixedWidth(final_w)
            return

        self._anim_step += 1
        t = self._anim_step / self._anim_total_steps
        # Ease-out cubic
        eased = 1 - math.pow(1 - t, 3)
        current_w = self._anim_start + eased * (
            int(64 * self._progress_target / 100) - self._anim_start
        )
        self.progress_fill.setFixedWidth(int(current_w))

    # ── Hover lift effect ──
    def enterEvent(self, event):
        self._hover_showing = True
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.get('surface_2')};
                border: 1px solid {Theme.get('border')};
                border-radius: 4px;
            }}
        """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover_showing = False
        self._update_card_style()
        super().leaveEvent(event)


class _AvatarLabel(QLabel):
    """Circular avatar with gradient background."""

    def __init__(self, letter: str, colors: tuple, parent=None):
        super().__init__(parent)
        self._letter = letter[0].upper()
        self._color1, self._color2 = colors
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(44, 44)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        r = min(rect.width(), rect.height())
        painter.setPen(Qt.PenStyle.NoPen)

        # Gradient fill
        gradient = QColor(self._color1)
        painter.setBrush(gradient)
        painter.drawEllipse(0, 0, r, r)

        # Subtle inner highlight
        highlight = QColor(self._color2)
        highlight.setAlpha(60)
        painter.setBrush(highlight)
        painter.drawEllipse(2, 2, r - 4, r - 4)

        # Letter
        painter.setPen(QColor("#FFFFFF"))
        font = QFont("Microsoft YaHei", 15, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._letter)

        painter.end()
