"""Tests for SettingsPage (gui_launcher) — extracted settings page component."""

import pytest


class TestSettingsPageCreation:
    """Behavior: SettingsPage is a QWidget with settings UI."""

    def test_is_qwidget(self, qtbot):
        from gui_launcher.settings_page import SettingsPage

        page = SettingsPage()
        qtbot.addWidget(page)

        assert page is not None

    def test_has_settings_saved_signal(self, qtbot):
        from gui_launcher.settings_page import SettingsPage

        page = SettingsPage()
        qtbot.addWidget(page)

        assert hasattr(page, 'settingsSaved')

    def test_has_label_width_constant(self, qtbot):
        from gui_launcher.settings_page import SettingsPage

        page = SettingsPage()
        qtbot.addWidget(page)

        assert hasattr(page, 'LABEL_WIDTH')
        assert page.LABEL_WIDTH == 80

    def test_has_input_min_width_constant(self, qtbot):
        from gui_launcher.settings_page import SettingsPage

        page = SettingsPage()
        qtbot.addWidget(page)

        assert hasattr(page, 'INPUT_MIN_WIDTH')
        assert page.INPUT_MIN_WIDTH == 200


class TestSettingsPageUI:
    """Behavior: SettingsPage creates proper UI elements."""

    def test_has_provider_combo(self, qtbot):
        from gui_launcher.settings_page import SettingsPage
        from PyQt6.QtWidgets import QComboBox

        page = SettingsPage()
        qtbot.addWidget(page)

        combos = page.findChildren(QComboBox)
        provider_combos = [c for c in combos if c.count() > 0]
        assert len(provider_combos) >= 1

    def test_has_api_key_input(self, qtbot):
        from gui_launcher.settings_page import SettingsPage
        from PyQt6.QtWidgets import QLineEdit

        page = SettingsPage()
        qtbot.addWidget(page)

        inputs = page.findChildren(QLineEdit)
        assert len(inputs) >= 1


class TestSettingsPageMethods:
    """Behavior: SettingsPage has required methods."""

    def test_has_create_group_method(self, qtbot):
        from gui_launcher.settings_page import SettingsPage

        page = SettingsPage()
        qtbot.addWidget(page)

        assert hasattr(page, 'create_group')
        assert callable(page.create_group)

    def test_has_create_label_method(self, qtbot):
        from gui_launcher.settings_page import SettingsPage

        page = SettingsPage()
        qtbot.addWidget(page)

        assert hasattr(page, 'create_label')
        assert callable(page.create_label)

    def test_has_create_input_method(self, qtbot):
        from gui_launcher.settings_page import SettingsPage

        page = SettingsPage()
        qtbot.addWidget(page)

        assert hasattr(page, 'create_input')
        assert callable(page.create_input)

    def test_has_load_settings_method(self, qtbot):
        from gui_launcher.settings_page import SettingsPage

        page = SettingsPage()
        qtbot.addWidget(page)

        assert hasattr(page, 'load_settings')
        assert callable(page.load_settings)

    def test_has_save_settings_method(self, qtbot):
        from gui_launcher.settings_page import SettingsPage

        page = SettingsPage()
        qtbot.addWidget(page)

        assert hasattr(page, 'save_settings')
        assert callable(page.save_settings)


class TestSettingsPageFactoryDelegation:
    """Behavior: Delegates to WidgetFactory for component creation."""

    def test_create_group_returns_qframe(self, qtbot):
        from gui_launcher.settings_page import SettingsPage
        from PyQt6.QtWidgets import QFrame

        page = SettingsPage()
        qtbot.addWidget(page)

        result = page.create_group("测试组")
        assert isinstance(result[0], QFrame)

    def test_create_label_returns_qlabel(self, qtbot):
        from gui_launcher.settings_page import SettingsPage
        from PyQt6.QtWidgets import QLabel

        page = SettingsPage()
        qtbot.addWidget(page)

        label = page.create_label("测试标签")
        assert isinstance(label, QLabel)

    def test_create_input_returns_qlineedit(self, qtbot):
        from gui_launcher.settings_page import SettingsPage
        from PyQt6.QtWidgets import QLineEdit

        page = SettingsPage()
        qtbot.addWidget(page)

        input_widget = page.create_input("占位符")
        assert isinstance(input_widget, QLineEdit)
