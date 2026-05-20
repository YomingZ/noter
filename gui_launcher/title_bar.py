"""CustomTitleBar — macOS-inspired traffic light controls with frameless drag."""

from PyQt6.QtCore import Qt, pyqtSignal, QRect, QTimer
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QWidget, QSizePolicy,
)
from PyQt6.QtGui import QPainter, QColor, QPen, QFont

from gui_launcher.theme import Theme


class TrafficLightButton(QWidget):
    """macOS-style traffic light dot with hover icon."""

    clicked = pyqtSignal()

    COLORS = {
        "close":  ("#FF5F57", "#FF5F57", "#4C1E1E"),  # normal, hover, icon
        "minimize": ("#FFBD2E", "#FFBD2E", "#4C3D1E"),
        "maximize": ("#28C840", "#28C840", "#1E4C28"),
    }

    HOVER_ICONS = {
        "close": "×",
        "minimize": "─",
        "maximize": "+",
    }

    def __init__(self, btn_type: str, parent=None):
        super().__init__(parent)
        self._type = btn_type
        self._color, self._hover_color, self._icon_color = self.COLORS[btn_type]
        self._hover_icon = self.HOVER_ICONS[btn_type]
        self._hovered = False
        self.setFixedSize(14, 14)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        cx, cy = rect.center().x(), rect.center().y()
        r = 6  # radius

        # ── Dot ──
        color = QColor(self._color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(rect.center(), r, r)

        # ── Hover icon ──
        if self._hovered:
            painter.setPen(QColor(self._icon_color))
            font = QFont("Segoe UI", 8, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(
                QRect(cx - 5, cy - 5, 10, 10),
                Qt.AlignmentFlag.AlignCenter,
                self._hover_icon,
            )

        painter.end()


class CustomTitleBar(QFrame):
    """自定义标题栏 — macOS traffic lights + back button + drag."""

    backClicked = pyqtSignal()

    def __init__(self, parent=None, show_back: bool = False):
        super().__init__(parent)
        self.parent_window = parent
        self._press_pos = None
        self._show_back = show_back
        self.setup_ui()

    def setup_ui(self):
        self.setFixedHeight(44)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.get('bg_primary')};
                border: none;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 0, 0)
        layout.setSpacing(8)

        # ── Traffic lights ──
        self.traffic_close = TrafficLightButton("close")
        self.traffic_close.clicked.connect(self.on_close)
        layout.addWidget(self.traffic_close)

        self.traffic_min = TrafficLightButton("minimize")
        self.traffic_min.clicked.connect(self.on_minimize)
        layout.addWidget(self.traffic_min)

        self.traffic_max = TrafficLightButton("maximize")
        self.traffic_max.clicked.connect(self.on_maximize)
        layout.addWidget(self.traffic_max)

        layout.addSpacing(12)

        # ── Back button ──
        self.back_btn = QPushButton("←")
        self.back_btn.setFixedSize(28, 28)
        self.back_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Theme.ACCENT_PRIMARY};
                border: 1px solid transparent;
                border-radius: 14px;
                font-size: 16px;
                font-weight: 300;
            }}
            QPushButton:hover {{
                background-color: {Theme.get('bg_tertiary')};
                border-color: {Theme.get('border_light')};
            }}
        """)
        self.back_btn.clicked.connect(self.backClicked.emit)
        self.back_btn.setVisible(self._show_back)
        layout.addWidget(self.back_btn)

        # ── Center title ──
        layout.addStretch()

        self.title_label = QLabel("PDF 备考笔记生成器")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 500;
            color: {Theme.get('text_secondary')};
            background: transparent;
            letter-spacing: 0.3px;
        """)
        layout.addWidget(self.title_label)

        layout.addStretch()

        # Spacer to balance traffic light width on the right
        spacer = QWidget()
        spacer.setFixedWidth(14 * 3 + 8 + 12)  # 3 lights + spacing + indent
        layout.addWidget(spacer)

    def set_show_back(self, show: bool):
        self._show_back = show
        self.back_btn.setVisible(show)

    def set_title(self, title: str):
        self.title_label.setText(title)

    def on_minimize(self):
        if self.parent_window:
            self.parent_window.showMinimized()

    def on_maximize(self):
        if self.parent_window:
            if self.parent_window.isMaximized():
                self.parent_window.showNormal()
            else:
                self.parent_window.showMaximized()

    def on_close(self):
        if self.parent_window:
            self.parent_window.close()

    # ── Window dragging ──

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = (
                event.globalPosition().toPoint()
                - self.parent_window.frameGeometry().topLeft()
            )

    def mouseMoveEvent(self, event):
        if self._press_pos and self.parent_window:
            self.parent_window.move(
                event.globalPosition().toPoint() - self._press_pos
            )

    def mouseDoubleClickEvent(self, event):
        self.on_maximize()

    def paintEvent(self, event):
        """Override paint to draw a subtle bottom border."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(Theme.get('border_light')))
        pen.setWidthF(0.5)
        painter.setPen(pen)
        painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        painter.end()
