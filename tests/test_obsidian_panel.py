"""Tests for ObsidianPanel — extracted GUI component."""

import pytest
from pathlib import Path


class TestObsidianPanelCreation:
    """Behavior: panel creates all 3 controls and exposes them."""

    def test_panel_is_widget(self, qtbot):
        from gui_launcher.obsidian_panel import ObsidianPanel

        panel = ObsidianPanel()
        qtbot.addWidget(panel)
        assert panel is not None

    def test_exposes_template_edit(self, qtbot):
        from gui_launcher.obsidian_panel import ObsidianPanel
        from PyQt6.QtWidgets import QLineEdit

        panel = ObsidianPanel()
        qtbot.addWidget(panel)
        assert hasattr(panel, "template_edit")
        assert isinstance(panel.template_edit, QLineEdit)

    def test_exposes_vault_edit(self, qtbot):
        from gui_launcher.obsidian_panel import ObsidianPanel
        from PyQt6.QtWidgets import QLineEdit

        panel = ObsidianPanel()
        qtbot.addWidget(panel)
        assert hasattr(panel, "vault_edit")
        assert isinstance(panel.vault_edit, QLineEdit)

    def test_exposes_course_combo(self, qtbot):
        from gui_launcher.obsidian_panel import ObsidianPanel
        from PyQt6.QtWidgets import QComboBox

        panel = ObsidianPanel()
        qtbot.addWidget(panel)
        assert hasattr(panel, "course_combo")
        assert isinstance(panel.course_combo, QComboBox)


class TestObsidianPanelDataAccess:
    """Behavior: reading values from controls returns current state."""

    def test_get_values_returns_three_strings(self, qtbot):
        from gui_launcher.obsidian_panel import ObsidianPanel

        panel = ObsidianPanel()
        qtbot.addWidget(panel)
        panel.template_edit.setText("/path/to/template.md")
        panel.vault_edit.setText("E:\\obsidian\\vault")
        panel.course_combo.setCurrentText("量子化学")

        vals = panel.get_values()

        assert len(vals) == 3
        template, course, vault = vals
        assert template == "/path/to/template.md"
        assert course == "量子化学"
        assert vault == "E:\\obsidian\\vault"

    def test_get_values_empty_by_default(self, qtbot):
        from gui_launcher.obsidian_panel import ObsidianPanel

        panel = ObsidianPanel()
        qtbot.addWidget(panel)
        template, course, vault = panel.get_values()

        assert template == ""
        assert course == ""
        assert vault == ""

    def test_set_values_populates_controls(self, qtbot):
        from gui_launcher.obsidian_panel import ObsidianPanel

        panel = ObsidianPanel()
        qtbot.addWidget(panel)
        panel.set_values(
            template="C:\\templates\\note.md",
            vault="E:\\obsidian\\collegenote",
            course="微积分",
        )

        assert panel.template_edit.text() == "C:\\templates\\note.md"
        assert panel.vault_edit.text() == "E:\\obsidian\\collegenote"
        assert panel.course_combo.currentText() == "微积分"


class TestObsidianPanelActiveToggle:
    """Behavior: toggling active state changes appearance."""

    def test_set_active_true_shows_frame(self, qtbot):
        from gui_launcher.obsidian_panel import ObsidianPanel

        panel = ObsidianPanel()
        qtbot.addWidget(panel)
        panel.set_active(True)

        assert panel.isVisible() is True


class TestObsidianPanelSignals:
    """Behavior: panel emits signals for user interactions."""

    def test_emit_browse_template_on_click(self, qtbot):
        from gui_launcher.obsidian_panel import ObsidianPanel
        from unittest.mock import Mock

        panel = ObsidianPanel()
        qtbot.addWidget(panel)
        handler = Mock()
        panel.browse_template_requested.connect(handler)

        panel._on_browse_template()

        handler.assert_called_once()

    def test_emit_browse_vault_on_click(self, qtbot):
        from gui_launcher.obsidian_panel import ObsidianPanel
        from unittest.mock import Mock

        panel = ObsidianPanel()
        qtbot.addWidget(panel)
        handler = Mock()
        panel.browse_vault_requested.connect(handler)

        panel._on_browse_vault()

        handler.assert_called_once()

    def test_populate_courses_updates_combo(self, qtbot):
        from gui_launcher.obsidian_panel import ObsidianPanel

        panel = ObsidianPanel()
        qtbot.addWidget(panel)
        panel.populate_courses(["calculus", "quantum", "linear"])

        assert panel.course_combo.count() == 3
        assert panel.course_combo.itemText(0) == "calculus"
        assert panel.course_combo.itemText(2) == "linear"

    def test_populate_courses_preserves_selection(self, qtbot):
        from gui_launcher.obsidian_panel import ObsidianPanel

        panel = ObsidianPanel()
        qtbot.addWidget(panel)
        panel.course_combo.setCurrentText("quantum")
        panel.populate_courses(["calculus", "quantum", "linear"])

        assert panel.course_combo.currentText() == "quantum"


class TestObsidianPanelIsQWidget:
    """Behavior: ObsidianPanel is a proper QWidget subclass."""

    def test_can_add_to_layout(self, qtbot):
        from gui_launcher.obsidian_panel import ObsidianPanel
        from PyQt6.QtWidgets import QVBoxLayout, QWidget

        parent = QWidget()
        layout = QVBoxLayout(parent)
        panel = ObsidianPanel()
        layout.addWidget(panel)

        assert panel.parent() is parent or panel.parentWidget() is not None
