"""DropArea — 文件拖放区域组件 with animated feedback and file count badge."""

import math
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog, QSizePolicy,
)
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QFont

from gui_launcher.theme import Theme


class DropArea(QFrame):
    """文件拖放区域 — 支持拖拽 PDF 文件和点击选择文件。

    Features:
    - Subtle gradient background
    - Dashed/solid border with color transition on drag
    - Gentle border pulse animation when idle
    - File count badge when files are present
    """

    filesDropped = pyqtSignal(list)

    FILE_LIMIT = 50

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.is_drag_over = False
        self._pulse_phase = 0.0
        self._file_count = 0
        self._setup_timers()
        self.setup_ui()

    def _setup_timers(self):
        """Idle border pulse: subtle breathing effect."""
        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(40)  # ~25 fps
        self._pulse_timer.timeout.connect(self._pulse_step)
        self._pulse_timer.start()

    def _pulse_step(self):
        """Advance pulse phase and repaint."""
        self._pulse_phase += 0.03
        if self._pulse_phase > 6.283:  # 2π
            self._pulse_phase = 0.0
        if not self.is_drag_over:
            self.update()

    def setup_ui(self):
        self.setMinimumHeight(170)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.update_style()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(6)

        # Icon area
        self.icon_label = QLabel(self)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("background: transparent;")
        self.icon_label.setFixedHeight(56)
        layout.addWidget(self.icon_label)

        # Text
        self.main_text = QLabel("拖拽 PDF 文件到此处")
        self.main_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_text.setStyleSheet(
            f"font-size: 16px; font-weight: 600; color: {Theme.get('text_primary')}; "
            f"background: transparent; letter-spacing: 0.5px;"
        )
        layout.addWidget(self.main_text)

        self.sub_text = QLabel("或点击选择文件  ·  支持批量处理")
        self.sub_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sub_text.setStyleSheet(
            f"font-size: 12.5px; color: {Theme.get('text_tertiary')}; "
            f"background: transparent;"
        )
        layout.addWidget(self.sub_text)

        # File count badge — hidden until files present
        self.badge = QLabel(self)
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge.setFixedSize(28, 28)
        self.badge.move(20, 16)
        self.badge.setStyleSheet(
            f"background-color: {Theme.ACCENT_AMBER}; color: white; "
            f"border-radius: 14px; font-size: 11px; font-weight: 700; "
            f"border: 2px solid {Theme.get('bg_primary') if not Theme.DARK_MODE else '#1C1B2B'};"
        )
        self.badge.hide()

        self._update_icon()

    def _update_icon(self):
        """Render upload icon as text for theme-aware appearance."""
        if self.is_drag_over:
            self.icon_label.setText("📂")
            self.icon_label.setStyleSheet(
                "font-size: 44px; background: transparent; "
                "font-weight: 400;"
            )
        else:
            self.icon_label.setText("📄")
            self.icon_label.setStyleSheet(
                "font-size: 40px; background: transparent; "
                "font-weight: 400;"
            )

    def update_style(self):
        """Refresh border and background."""
        self.update()

    def set_file_count(self, count: int):
        """Update the file count badge."""
        self._file_count = count
        if count > 0:
            self.badge.setText(str(min(count, 99)))
            self.badge.show()
            # Pulse badge to draw attention
            self.main_text.setText(f"已添加 {count} 个文件  —  继续添加或开始生成")
            self.sub_text.setText("再次拖拽或点击可添加更多文件")
        else:
            self.badge.hide()
            self.main_text.setText("拖拽 PDF 文件到此处")
            self.sub_text.setText("或点击选择文件  ·  支持批量处理")

    def paintEvent(self, event):
        """Custom paint with animated border and gradient background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(2, 2, -2, -2)
        radius = 16

        # ── Background gradient ──
        bg = Theme.get('bg_secondary')
        if self.is_drag_over:
            # Accent-tinted background on drag
            accent_color = QColor(Theme.ACCENT_AMBER)
            accent_color.setAlpha(20)  # very subtle tint
            painter.setBrush(accent_color)
        else:
            painter.setBrush(QColor(bg))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, radius, radius)

        # ── Border ──
        if self.is_drag_over:
            pen_color = QColor(Theme.ACCENT_AMBER)
            pen_style = Qt.PenStyle.SolidLine
            pen_width = 2
        else:
            # Breathing opacity on dashed border
            alpha = 140 + int(60 * (0.5 + 0.5 * math.sin(self._pulse_phase)))
            pen_color = QColor(Theme.get('border'))
            pen_color.setAlpha(alpha)
            pen_style = Qt.PenStyle.DashLine
            pen_width = 1

        pen = QPen(pen_color)
        pen.setStyle(pen_style)
        pen.setWidth(pen_width)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, radius, radius)

        # ── Drag-over glow ──
        if self.is_drag_over:
            glow = QColor(Theme.ACCENT_AMBER)
            glow.setAlpha(30)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(glow)
            painter.drawRoundedRect(rect.adjusted(-4, -4, 4, 4), radius + 2, radius + 2)

        painter.end()

    # ── Drag events ──

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self.is_drag_over = True
            self._update_icon()
            self.update()
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.is_drag_over = False
        self._update_icon()
        self.update()

    def dropEvent(self, event):
        self.is_drag_over = False
        self._update_icon()
        self.update()

        files = []
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_file() and path.suffix.lower() == '.pdf':
                files.append(path)
            elif path.is_dir():
                files.extend(path.glob('*.pdf'))

        # Enforce limit
        if len(files) > self.FILE_LIMIT:
            files = files[:self.FILE_LIMIT]

        if files:
            self.filesDropped.emit(files)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.select_files()

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择 PDF 文件", "", "PDF 文件 (*.pdf)"
        )
        if files:
            self.filesDropped.emit([Path(f) for f in files])
