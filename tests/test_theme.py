"""Tests for Theme module — extracted from gui_launcher.py and settings_dialog.py."""

import pytest
import sys


class TestThemeConstants:
    """Behavior: theme color constants are defined."""

    def test_accent_blue_defined(self):
        from gui_launcher.theme import Theme

        assert Theme.ACCENT_BLUE == "#4A6CF7"

    def test_success_green_defined(self):
        from gui_launcher.theme import Theme

        assert Theme.SUCCESS_GREEN == "#34C759"

    def test_light_dict_has_all_keys(self):
        from gui_launcher.theme import Theme

        expected_keys = {
            'bg_primary', 'bg_secondary', 'bg_tertiary', 'bg_elevated',
            'border', 'border_light', 'text_primary', 'text_secondary', 'text_tertiary',
        }
        assert expected_keys.issubset(Theme.LIGHT.keys())

    def test_dark_dict_has_all_keys(self):
        from gui_launcher.theme import Theme

        expected_keys = {
            'bg_primary', 'bg_secondary', 'bg_tertiary', 'bg_elevated',
            'border', 'border_light', 'text_primary', 'text_secondary', 'text_tertiary',
        }
        assert expected_keys.issubset(Theme.DARK.keys())


class TestThemeGetMethod:
    """Behavior: get() returns correct colors based on mode."""

    def test_default_light_mode_returns_light_colors(self):
        from gui_launcher.theme import Theme

        Theme.DARK_MODE = False
        assert Theme.get('bg_primary') == '#FAF8F5'
        assert Theme.get('text_primary') == '#2D2A24'

    def test_dark_mode_returns_dark_colors(self):
        from gui_launcher.theme import Theme

        Theme.DARK_MODE = True
        assert Theme.get('bg_primary') == '#1C1B2B'
        assert Theme.get('text_primary') == '#EEEDF2'

    def test_unknown_key_returns_black_fallback(self):
        from gui_launcher.theme import Theme

        Theme.DARK_MODE = False
        assert Theme.get('nonexistent_key') == '#000000'

    def test_reset_to_light_after_test(self):
        from gui_launcher.theme import Theme

        Theme.DARK_MODE = False
        assert Theme.DARK_MODE is False


class TestThemeToggle:
    """Behavior: toggle() switches between light and dark."""

    def test_toggle_from_light_to_dark(self):
        from gui_launcher.theme import Theme

        Theme.DARK_MODE = False
        Theme.toggle()
        assert Theme.DARK_MODE is True

    def test_toggle_from_dark_to_light(self):
        from gui_launcher.theme import Theme

        Theme.DARK_MODE = True
        Theme.toggle()
        assert Theme.DARK_MODE is False

    def test_toggle_twice_returns_to_original(self):
        from gui_launcher.theme import Theme

        original = Theme.DARK_MODE
        Theme.toggle()
        Theme.toggle()
        assert Theme.DARK_MODE == original


class TestThemeNoPyQtDependency:
    """Behavior: Theme module has zero PyQt imports."""

    def test_import_without_pyqt(self):
        blocked = {k for k in sys.modules if k.startswith("PyQt")}
        for mod in blocked:
            del sys.modules[mod]

        from gui_launcher.theme import Theme
        assert Theme is not None
        assert Theme.ACCENT_BLUE == "#4A6CF7"

    def test_get_works_without_qt_event_loop(self):
        from gui_launcher.theme import Theme

        result = Theme.get('bg_primary')
        assert isinstance(result, str)
        assert len(result) == 7  # hex color #XXXXXX
