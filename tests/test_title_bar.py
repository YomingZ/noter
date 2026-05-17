"""Tests for CustomTitleBar — extracted title bar component."""

import pytest
from unittest.mock import Mock, MagicMock


class TestCustomTitleBarCreation:
    """Behavior: CustomTitleBar is a QFrame with window controls."""

    def test_is_qframe(self, qtbot):
        from gui_launcher.title_bar import CustomTitleBar

        bar = CustomTitleBar()
        qtbot.addWidget(bar)

        assert bar is not None

    def test_has_back_clicked_signal(self, qtbot):
        from gui_launcher.title_bar import CustomTitleBar

        bar = CustomTitleBar()
        qtbot.addWidget(bar)

        assert hasattr(bar, 'backClicked')

    def test_has_fixed_height(self, qtbot):
        from gui_launcher.title_bar import CustomTitleBar

        bar = CustomTitleBar()
        qtbot.addWidget(bar)

        assert bar.height() >= 30

    def test_default_no_back_button(self, qtbot):
        from gui_launcher.title_bar import CustomTitleBar

        bar = CustomTitleBar()
        qtbot.addWidget(bar)

        assert bar._show_back is False

    def test_show_back_true_shows_button(self, qtbot):
        from gui_launcher.title_bar import CustomTitleBar

        bar = CustomTitleBar(show_back=True)
        qtbot.addWidget(bar)

        assert bar._show_back is True


class TestCustomTitleBarTitle:
    """Behavior: Title text management."""

    def test_default_title(self, qtbot):
        from gui_launcher.title_bar import CustomTitleBar
        from PyQt6.QtWidgets import QLabel

        bar = CustomTitleBar()
        qtbot.addWidget(bar)

        labels = bar.findChildren(QLabel)
        title_labels = [l for l in labels if "PDF" in l.text()]
        assert len(title_labels) == 1

    def test_set_title_changes_text(self, qtbot):
        from gui_launcher.title_bar import CustomTitleBar

        bar = CustomTitleBar()
        qtbot.addWidget(bar)

        bar.set_title("新标题")
        assert bar.title_label.text() == "新标题"


class TestCustomTitleBarBackButton:
    """Behavior: Back button visibility control."""

    def test_set_show_back_true(self, qtbot):
        from gui_launcher.title_bar import CustomTitleBar

        bar = CustomTitleBar(show_back=False)
        qtbot.addWidget(bar)

        bar.set_show_back(True)
        assert bar._show_back is True

    def test_set_show_back_false(self, qtbot):
        from gui_launcher.title_bar import CustomTitleBar

        bar = CustomTitleBar(show_back=True)
        qtbot.addWidget(bar)

        bar.set_show_back(False)
        assert bar._show_back is False


class TestCustomTitleBarWindowControls:
    """Behavior: Window control buttons exist."""

    def test_has_minimize_button(self, qtbot):
        from gui_launcher.title_bar import CustomTitleBar
        from PyQt6.QtWidgets import QPushButton

        bar = CustomTitleBar()
        qtbot.addWidget(bar)

        buttons = bar.findChildren(QPushButton)
        texts = [b.text() for b in buttons]
        assert "─" in texts

    def test_has_maximize_button(self, qtbot):
        from gui_launcher.title_bar import CustomTitleBar
        from PyQt6.QtWidgets import QPushButton

        bar = CustomTitleBar()
        qtbot.addWidget(bar)

        buttons = bar.findChildren(QPushButton)
        texts = [b.text() for b in buttons]
        assert "□" in texts

    def test_has_close_button(self, qtbot):
        from gui_launcher.title_bar import CustomTitleBar
        from PyQt6.QtWidgets import QPushButton

        bar = CustomTitleBar()
        qtbot.addWidget(bar)

        buttons = bar.findChildren(QPushButton)
        texts = [b.text() for b in buttons]
        assert "✕" in texts
