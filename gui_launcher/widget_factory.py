"""Widget Factory — polished UI component factory matching the Scholarly Warmth theme."""

from PyQt6.QtWidgets import (
    QFrame, QLabel, QLineEdit, QComboBox, QPushButton,
    QCheckBox, QHBoxLayout, QVBoxLayout, QSlider,
)
from PyQt6.QtCore import Qt

from gui_launcher.theme import Theme


class WidgetFactory:
    """Unified UI component factory with warm academic styling."""

    LABEL_WIDTH = 80

    @staticmethod
    def create_group(title: str) -> QFrame:
        """Create a card-style group with title header."""
        group = QFrame()
        group.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.get('bg_secondary')};
                border: 1px solid {Theme.get('border_light')};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(14)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {Theme.get('text_primary')};
            background: transparent;
            letter-spacing: 0.3px;
        """)
        layout.addWidget(title_label)

        return group

    @staticmethod
    def create_label(text: str, width: int = LABEL_WIDTH) -> QLabel:
        label = QLabel(text)
        label.setFixedWidth(width)
        label.setStyleSheet(
            f"font-size: 13px; color: {Theme.get('text_primary')}; "
            f"background: transparent; font-weight: 450;"
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
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 13px;
                color: {Theme.get('text_primary')};
                min-height: 20px;
            }}
            QLineEdit:focus {{
                border-color: {Theme.ACCENT_AMBER};
            }}
            QLineEdit::placeholder {{
                color: {Theme.get('text_tertiary')};
                font-size: 12.5px;
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
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                color: {Theme.get('text_primary')};
                min-width: 140px;
            }}
            QComboBox:hover {{ border-color: {Theme.get('border')}; }}
            QComboBox::drop-down {{ border: none; width: 26px; }}
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
                border-radius: 8px;
                selection-background-color: {Theme.ACCENT_AMBER};
                selection-color: white;
                padding: 4px;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 6px 10px;
                border-radius: 4px;
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
                    border-radius: 8px;
                    padding: 10px 22px;
                    font-size: 13px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {Theme.ACCENT_AMBER_DARK};
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Theme.get('bg_tertiary')};
                    color: {Theme.get('text_primary')};
                    border: 1px solid {Theme.get('border_light')};
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background-color: {Theme.get('surface_2')};
                    border-color: {Theme.get('border')};
                }}
            """)
        return btn

    @staticmethod
    def create_checkbox(text: str, checked: bool = False) -> QCheckBox:
        cb = QCheckBox(text)
        cb.setChecked(checked)
        cb.setStyleSheet(f"""
            QCheckBox {{
                font-size: 13px;
                color: {Theme.get('text_primary')};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 5px;
                border: 2px solid {Theme.get('border')};
                background-color: {Theme.get('bg_tertiary')};
            }}
            QCheckBox::indicator:checked {{
                background-color: {Theme.ACCENT_AMBER};
                border-color: {Theme.ACCENT_AMBER};
            }}
            QCheckBox::indicator:hover {{
                border-color: {Theme.ACCENT_AMBER};
            }}
        """)
        return cb

    @staticmethod
    def create_slider() -> QSlider:
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {Theme.get('bg_tertiary')};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {Theme.ACCENT_AMBER};
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {Theme.ACCENT_AMBER_DARK};
                width: 20px;
                height: 20px;
                margin: -7px 0;
            }}
            QSlider::sub-page:horizontal {{
                background: {Theme.gradient_accent()};
                border-radius: 3px;
            }}
        """)
        return slider

    @staticmethod
    def create_row(label_text: str, widget, connect=None):
        row = QHBoxLayout()
        row.setSpacing(12)
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
        """Create a macOS-style segmented control from QPushButtons.

        Returns (container_frame, {key: button}) for state tracking.
        """
        segments = {}
        container = QFrame()
        container.setFixedHeight(38)
        container.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)

        count = len(options)
        for i, (key, label) in enumerate(options):
            btn = QPushButton(label)
            btn.setFixedHeight(34)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

            # Rounded ends for first/last
            radius = "8px" if count == 1 else (
                "8px 0 0 8px" if i == 0 else (
                    "0 8px 8px 0" if i == count - 1 else "0"
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
                    font-size: 12.5px;
                    font-weight: 600;
                }}
            """
        return f"""
            QPushButton {{
                background-color: {Theme.get('bg_tertiary')};
                color: {Theme.get('text_secondary')};
                border: 1px solid {Theme.get('border_light')};
                border-radius: {radius};
                font-size: 12.5px;
            }}
            QPushButton:hover {{
                background-color: {Theme.get('surface_2')};
                color: {Theme.get('text_primary')};
            }}
        """

    @staticmethod
    def _seg_toggle(active_key: str, segments: dict, callback=None):
        count = len(segments)
        for i, (key, btn) in enumerate(segments.items()):
            radius = "8px" if count == 1 else (
                "8px 0 0 8px" if i == 0 else (
                    "0 8px 8px 0" if i == count - 1 else "0"
                )
            )
            active = key == active_key
            btn.setStyleSheet(WidgetFactory._seg_style(active, radius))
        if callback:
            callback(active_key)
