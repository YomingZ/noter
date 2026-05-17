"""Tests for WidgetFactory — extracted UI widget factory methods."""

import pytest


class TestWidgetFactoryCreateGroup:
    """Behavior: create_group() produces a styled QFrame."""

    def test_returns_qframe(self, qtbot):
        from gui_launcher.widget_factory import WidgetFactory

        group = WidgetFactory.create_group("Test Title")
        qtbot.addWidget(group)

        assert group is not None

    def test_contains_title_label(self, qtbot):
        from gui_launcher.widget_factory import WidgetFactory
        from PyQt6.QtWidgets import QLabel

        group = WidgetFactory.create_group("AI Config")
        qtbot.addWidget(group)

        labels = group.findChildren(QLabel)
        texts = [l.text() for l in labels]
        assert "AI Config" in texts


class TestWidgetFactoryCreateLabel:
    """Behavior: create_label() produces a styled QLabel."""

    def test_returns_qlabel_with_text(self, qtbot):
        from gui_launcher.widget_factory import WidgetFactory

        label = WidgetFactory.create_label("API Key")
        qtbot.addWidget(label)

        assert label.text() == "API Key"

    def test_respects_width_parameter(self, qtbot):
        from gui_launcher.widget_factory import WidgetFactory

        label = WidgetFactory.create_label("Name", width=120)
        qtbot.addWidget(label)

        assert label.width() >= 120 or label.minimumWidth() == 120


class TestWidgetFactoryCreateInput:
    """Behavior: create_input() produces a styled QLineEdit."""

    def test_returns_qlineedit(self, qtbot):
        from gui_launcher.widget_factory import WidgetFactory

        input_widget = WidgetFactory.create_input()
        qtbot.addWidget(input_widget)

        assert input_widget is not None

    def test_sets_placeholder_text(self, qtbot):
        from gui_launcher.widget_factory import WidgetFactory

        input_widget = WidgetFactory.create_input("Enter API Key")
        qtbot.addWidget(input_widget)

        assert input_widget.placeholderText() == "Enter API Key"

    def test_password_mode_hides_text(self, qtbot):
        from gui_launcher.widget_factory import WidgetFactory
        from PyQt6.QtWidgets import QLineEdit

        input_widget = WidgetFactory.create_input(password=True)
        qtbot.addWidget(input_widget)

        assert input_widget.echoMode() == QLineEdit.EchoMode.Password

    def test_normal_mode_shows_text(self, qtbot):
        from gui_launcher.widget_factory import WidgetFactory
        from PyQt6.QtWidgets import QLineEdit

        input_widget = WidgetFactory.create_input(password=False)
        qtbot.addWidget(input_widget)

        assert input_widget.echoMode() == QLineEdit.EchoMode.Normal


class TestWidgetFactoryCreateCombo:
    """Behavior: create_combo() produces a styled QComboBox."""

    def test_returns_qcombobox(self, qtbot):
        from gui_launcher.widget_factory import WidgetFactory

        combo = WidgetFactory.create_combo(["a", "b", "c"])
        qtbot.addWidget(combo)

        assert combo.count() == 3

    def test_populates_items(self, qtbot):
        from gui_launcher.widget_factory import WidgetFactory

        items = ["Kimi", "OpenAI", "Anthropic"]
        combo = WidgetFactory.create_combo(items)
        qtbot.addWidget(combo)

        for i, item in enumerate(items):
            assert combo.itemText(i) == item

    def test_empty_items_creates_empty_combo(self, qtbot):
        from gui_launcher.widget_factory import WidgetFactory

        combo = WidgetFactory.create_combo([])
        qtbot.addWidget(combo)

        assert combo.count() == 0


class TestWidgetFactoryCreateButton:
    """Behavior: create_button() produces a styled QPushButton."""

    def test_returns_qpushbutton(self, qtbot):
        from gui_launcher.widget_factory import WidgetFactory

        btn = WidgetFactory.create_button("Save")
        qtbot.addWidget(btn)

        assert btn.text() == "Save"

    def test_primary_button_has_text(self, qtbot):
        from gui_launcher.widget_factory import WidgetFactory

        btn = WidgetFactory.create_button("Submit", primary=True)
        qtbot.addWidget(btn)

        assert btn.text() == "Submit"

    def test_secondary_button_has_text(self, qtbot):
        from gui_launcher.widget_factory import WidgetFactory

        btn = WidgetFactory.create_button("Cancel", primary=False)
        qtbot.addWidget(btn)

        assert btn.text() == "Cancel"


class TestWidgetFactoryCreateCheckbox:
    """Behavior: create_checkbox() produces a styled QCheckBox."""

    def test_returns_qcheckbox(self, qtbot):
        from gui_launcher.widget_factory import WidgetFactory

        cb = WidgetFactory.create_checkbox("Enable feature")
        qtbot.addWidget(cb)

        assert cb.text() == "Enable feature"

    def test_checked_by_default_when_specified(self, qtbot):
        from gui_launcher.widget_factory import WidgetFactory

        cb = WidgetFactory.create_checkbox("Auto-save", checked=True)
        qtbot.addWidget(cb)

        assert cb.isChecked() is True

    def test_unchecked_by_default(self, qtbot):
        from gui_launcher.widget_factory import WidgetFactory

        cb = WidgetFactory.create_checkbox("Debug mode")
        qtbot.addWidget(cb)

        assert cb.isChecked() is False


class TestWidgetFactoryCreateSublabel:
    """Behavior: create_sublabel() produces a smaller secondary label."""

    def test_returns_qlabel(self, qtbot):
        from gui_launcher.widget_factory import WidgetFactory

        label = WidgetFactory.create_sublabel("Hint text")
        qtbot.addWidget(label)

        assert label.text() == "Hint text"


class TestWidgetFactoryCreateRow:
    """Behavior: _create_row() creates a horizontal layout with label + widget."""

    def test_returns_qlayout(self, qtbot):
        from gui_launcher.widget_factory import WidgetFactory
        from PyQt6.QtWidgets import QLineEdit, QWidget

        widget = QLineEdit()
        row = WidgetFactory.create_row("Label:", widget)
        qtbot.addWidget(QWidget())  # need parent for layout

        assert row is not None
        assert row.count() >= 2  # label + widget
