"""Widget Factory — Windows 11 Fluent Design UI component factory."""

from PyQt6.QtWidgets import (
    QFrame, QLabel, QLineEdit, QComboBox, QPushButton,
    QCheckBox, QHBoxLayout, QVBoxLayout, QSlider,
)
from PyQt6.QtCore import Qt

from gui_launcher.theme import Theme


class WidgetFactory:
    """Unified UI component factory with Windows 11 styling."""

    LABEL_WIDTH = 80

    @staticmethod
    def create_group(title: str) -> QFrame:
        """Create a card-style group with title header."""
        group = QFrame()
        group.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.get('bg_secondary')};
                border: 1px solid {Theme.get('border_light')};
                border-radius: 4px;
            }}
        """)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 600;
            color: {Theme.get('text_primary')};
            background: transparent;
        """)
        layout.addWidget(title_label)

        return group

    @staticmethod
    def create_label(text: str, width: int = LABEL_WIDTH) -> QLabel:
        label = QLabel(text)
        label.setFixedWidth(width)
        label.setStyleSheet(
            f"font-size: 12px; color: {Theme.get('text_primary')}; "
            f"background: transparent;"
        )
        return label

    @staticmethod
    def create_sublabel(text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(
            f"font-size: 11px; color: {Theme.get('text_tertiary')}; "
            f"background: transparent;"
        )
        return label

    @staticmethod
    def create_input(placeholder: str = "", password: bool = False) -> QLineEdit:
        le = QLineEdit()
        le.setPlaceholderText(placeholder)
        if password:
            le.setEchoMode(QLineEdit.EchoMode.Password)
        le.setStyleSheet(f"""
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
                font-size: 12px;
            }}
        """)
        return le

    @staticmethod
    def create_combo(items: list) -> QComboBox:
        combo = QComboBox()
        combo.addItems(items)
        combo.setStyleSheet(f"""
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
                padding: 4px;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 5px 8px;
                border-radius: 2px;
            }}
        """)
        return combo

    @staticmethod
    def create_button(text: str, primary: bool = False) -> QPushButton:
        btn = QPushButton(text)
        if primary:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {Theme.gradient_accent()};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 7px 18px;
                    font-size: 12px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {Theme.ACCENT_PRIMARY_DARK};
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Theme.get('bg_tertiary')};
                    color: {Theme.get('text_primary')};
                    border: 1px solid {Theme.get('border_light')};
                    border-radius: 4px;
                    padding: 7px 16px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: {Theme.get('surface_2')};
                    border-color: {Theme.ACCENT_PRIMARY};
                }}
            """)
        return btn

    @staticmethod
    def create_checkbox(text: str, checked: bool = False) -> QCheckBox:
        cb = QCheckBox(text)
        cb.setChecked(checked)
        cb.setStyleSheet(f"""
            QCheckBox {{
                font-size: 12px;
                color: {Theme.get('text_primary')};
                spacing: 6px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid {Theme.get('border')};
                background-color: {Theme.get('bg_tertiary')};
            }}
            QCheckBox::indicator:checked {{
                background-color: {Theme.ACCENT_PRIMARY};
                border-color: {Theme.ACCENT_PRIMARY};
            }}
            QCheckBox::indicator:hover {{
                border-color: {Theme.ACCENT_PRIMARY};
            }}
        """)
        return cb

    @staticmethod
    def create_slider() -> QSlider:
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {Theme.get('bg_tertiary')};
                height: 4px;
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {Theme.ACCENT_PRIMARY};
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {Theme.ACCENT_HOVER};
                width: 18px;
                height: 18px;
                margin: -7px 0;
            }}
            QSlider::sub-page:horizontal {{
                background: {Theme.gradient_accent()};
                border-radius: 2px;
            }}
        """)
        return slider

    @staticmethod
    def create_row(label_text: str, widget, connect=None):
        row = QHBoxLayout()
        row.setSpacing(10)
        label = WidgetFactory.create_label(label_text)
        row.addWidget(label)
        if hasattr(widget, 'currentIndexChanged') and connect:
            widget.currentIndexChanged.connect(connect)
        if hasattr(widget, 'setMinimumWidth'):
            widget.setMinimumWidth(200)
        row.addWidget(widget, 1)
        return row

    @staticmethod
    def create_segmented_control(
        options: list[tuple[str, str]],
        default_key: str = "",
        callback=None,
    ) -> tuple[QFrame, dict]:
        """Create a Windows-style segmented control from QPushButtons.

        Returns (container_frame, {key: button}) for state tracking.
        """
        segments = {}
        container = QFrame()
        container.setFixedHeight(34)
        container.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        count = len(options)
        for i, (key, label) in enumerate(options):
            btn = QPushButton(label)
            btn.setFixedHeight(32)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

            radius = "4px" if count == 1 else (
                "4px 0 0 4px" if i == 0 else (
                    "0 4px 4px 0" if i == count - 1 else "0"
                )
            )

            active = key == default_key
            btn.setStyleSheet(WidgetFactory._seg_style(active, radius))
            btn.clicked.connect(lambda checked, k=key: WidgetFactory._seg_toggle(k, segments, callback))
            layout.addWidget(btn, 1)
            segments[key] = btn

        return container, segments

    @staticmethod
    def _seg_style(active: bool, radius: str) -> str:
        if active:
            return f"""
                QPushButton {{
                    background: {Theme.gradient_accent()};
                    color: white;
                    border: none;
                    border-radius: {radius};
                    font-size: 12px;
                    font-weight: 600;
                }}
            """
        return f"""
            QPushButton {{
                background-color: {Theme.get('bg_tertiary')};
                color: {Theme.get('text_secondary')};
                border: 1px solid {Theme.get('border_light')};
                border-radius: {radius};
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {Theme.get('surface_2')};
                color: {Theme.get('text_primary')};
                border-color: {Theme.ACCENT_PRIMARY};
            }}
        """

    @staticmethod
    def _seg_toggle(active_key: str, segments: dict, callback=None):
        count = len(segments)
        for i, (key, btn) in enumerate(segments.items()):
            radius = "4px" if count == 1 else (
                "4px 0 0 4px" if i == 0 else (
                    "0 4px 4px 0" if i == count - 1 else "0"
                )
            )
            active = key == active_key
            btn.setStyleSheet(WidgetFactory._seg_style(active, radius))
        if callback:
            callback(active_key)
