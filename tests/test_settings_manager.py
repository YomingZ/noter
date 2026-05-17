"""Tests for SettingsManager module — extracted from gui_launcher.py and settings_dialog.py."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestSettingsManagerInit:
    """Behavior: SettingsManager initializes with default values."""

    def test_creates_with_default_settings(self, tmp_path):
        from gui_launcher.settings_manager import SettingsManager

        with patch('gui_launcher.settings_manager.SETTINGS_FILE', tmp_path / 'settings.json'):
            with patch('gui_launcher.settings_manager.CONFIG_DIR', tmp_path):
                mgr = SettingsManager()

        assert mgr.get("ai", "provider") == "kimi"
        assert mgr.get("output", "format") == "docx"

    def test_loads_existing_settings(self, tmp_path):
        from gui_launcher.settings_manager import SettingsManager

        settings_file = tmp_path / 'settings.json'
        settings_data = {"ai": {"provider": "openai", "api_key": "test-key"}, "output": {"format": "obsidian"}}
        settings_file.write_text(json.dumps(settings_data), encoding='utf-8')

        with patch('gui_launcher.settings_manager.SETTINGS_FILE', settings_file):
            with patch('gui_launcher.settings_manager.CONFIG_DIR', tmp_path):
                mgr = SettingsManager()

        assert mgr.get("ai", "provider") == "openai"
        assert mgr.get("ai", "api_key") == "test-key"

    def test_no_pyqt_dependency(self):
        import sys
        blocked = {k for k in sys.modules if k.startswith("PyQt")}
        for mod in blocked:
            del sys.modules[mod]

        from gui_launcher.settings_manager import SettingsManager
        assert SettingsManager is not None


class TestSettingsManagerGetSet:
    """Behavior: get/set methods access nested dict."""

    def test_get_single_key(self, tmp_path):
        from gui_launcher.settings_manager import SettingsManager

        with patch('gui_launcher.settings_manager.SETTINGS_FILE', tmp_path / 's.json'):
            with patch('gui_launcher.settings_manager.CONFIG_DIR', tmp_path):
                mgr = SettingsManager()

        result = mgr.get("ai", "provider")
        assert result == "kimi"

    def test_get_nested_key(self, tmp_path):
        from gui_launcher.settings_manager import SettingsManager

        with patch('gui_launcher.settings_manager.SETTINGS_FILE', tmp_path / 's.json'):
            with patch('gui_launcher.settings_manager.CONFIG_DIR', tmp_path):
                mgr = SettingsManager()

        result = mgr.get("storage", "keep_markdown")
        assert result is True

    def test_get_missing_key_returns_default(self, tmp_path):
        from gui_launcher.settings_manager import SettingsManager

        with patch('gui_launcher.settings_manager.SETTINGS_FILE', tmp_path / 's.json'):
            with patch('gui_launcher.settings_manager.CONFIG_DIR', tmp_path):
                mgr = SettingsManager()

        result = mgr.get("nonexistent", "key", default="fallback")
        assert result == "fallback"

    def test_set_and_get_roundtrip(self, tmp_path):
        from gui_launcher.settings_manager import SettingsManager

        with patch('gui_launcher.settings_manager.SETTINGS_FILE', tmp_path / 's.json'):
            with patch('gui_launcher.settings_manager.CONFIG_DIR', tmp_path):
                mgr = SettingsManager()
                mgr.set("ai", "model", "gpt-4o")

        assert mgr.get("ai", "model") == "gpt-4o"

    def test_set_creates_nested_structure(self, tmp_path):
        from gui_launcher.settings_manager import SettingsManager

        with patch('gui_launcher.settings_manager.SETTINGS_FILE', tmp_path / 's.json'):
            with patch('gui_launcher.settings_manager.CONFIG_DIR', tmp_path):
                mgr = SettingsManager()
                mgr.set("new_section", "nested", "value", 42)

        assert mgr.get("new_section", "nested", "value") == 42


class TestSettingsManagerSaveLoad:
    """Behavior: save/load persist to JSON file."""

    def test_save_creates_file(self, tmp_path):
        from gui_launcher.settings_manager import SettingsManager

        settings_file = tmp_path / 'settings.json'

        with patch('gui_launcher.settings_manager.SETTINGS_FILE', settings_file):
            with patch('gui_launcher.settings_manager.CONFIG_DIR', tmp_path):
                mgr = SettingsManager()
                mgr.set("ai", "api_key", "my-secret-key")
                mgr.save()

        assert settings_file.exists()
        loaded = json.loads(settings_file.read_text(encoding='utf-8'))
        assert loaded["ai"]["api_key"] != "my-secret-key"  # should be encrypted

    def test_load_decrypts_api_key(self, tmp_path):
        from gui_launcher.settings_manager import SettingsManager
        import base64

        encrypted = base64.b64encode(b"secret-key").decode()
        settings_data = {"ai": {"api_key": encrypted}}
        settings_file = tmp_path / 'settings.json'
        settings_file.write_text(json.dumps(settings_data), encoding='utf-8')

        with patch('gui_launcher.settings_manager.SETTINGS_FILE', settings_file):
            with patch('gui_launcher.settings_manager.CONFIG_DIR', tmp_path):
                mgr = SettingsManager()

        assert mgr.get("ai", "api_key") == "secret-key"

    def test_handles_corrupted_file_gracefully(self, tmp_path):
        from gui_launcher.settings_manager import SettingsManager

        settings_file = tmp_path / 'settings.json'
        settings_file.write_text("{invalid json}", encoding='utf-8')

        with patch('gui_launcher.settings_manager.SETTINGS_FILE', settings_file):
            with patch('gui_launcher.settings_manager.CONFIG_DIR', tmp_path):
                mgr = SettingsManager()

        assert mgr.get("ai", "provider") == "kimi"


class TestSettingsManagerProfiles:
    """Behavior: profile system supports multiple configurations."""

    def test_get_profiles_includes_default(self, tmp_path):
        from gui_launcher.settings_manager import SettingsManager

        profiles_dir = tmp_path / 'profiles'
        profiles_dir.mkdir(parents=True, exist_ok=True)

        with patch('gui_launcher.settings_manager.SETTINGS_FILE', tmp_path / 's.json'):
            with patch('gui_launcher.settings_manager.CONFIG_DIR', tmp_path):
                mgr = SettingsManager()
                mgr.profiles_dir = profiles_dir

        profiles = mgr.get_profiles()
        assert "默认配置" in profiles

    def test_save_and_load_profile(self, tmp_path):
        from gui_launcher.settings_manager import SettingsManager

        profiles_dir = tmp_path / 'profiles'
        profiles_dir.mkdir(parents=True, exist_ok=True)

        with patch('gui_launcher.settings_manager.SETTINGS_FILE', tmp_path / 's.json'):
            with patch('gui_launcher.settings_manager.CONFIG_DIR', tmp_path):
                mgr = SettingsManager.__new__(SettingsManager)
                mgr.profiles_dir = profiles_dir
                mgr.current_profile = "默认配置"
                mgr.settings = {"ai": {"provider": "openai"}}

                mgr.save_profile("work")
                assert (profiles_dir / "work.json").exists()

    def test_delete_profile_removes_file(self, tmp_path):
        from gui_launcher.settings_manager import SettingsManager

        profiles_dir = tmp_path / 'profiles'
        profiles_dir.mkdir(parents=True, exist_ok=True)
        (profiles_dir / "temp.json").write_text("{}")

        with patch('gui_launcher.settings_manager.SETTINGS_FILE', tmp_path / 's.json'):
            with patch('gui_launcher.settings_manager.CONFIG_DIR', tmp_path):
                mgr = SettingsManager.__new__(SettingsManager)
                mgr.profiles_dir = profiles_dir
                mgr.current_profile = "默认配置"
                mgr.settings = {}

                result = mgr.delete_profile("temp")
                assert result is True
                assert not (profiles_dir / "temp.json").exists()


class TestSettingsManagerHelpers:
    """Behavior: helper methods."""

    def test_has_api_key_returns_true_when_set(self, tmp_path):
        from gui_launcher.settings_manager import SettingsManager

        with patch('gui_launcher.settings_manager.SETTINGS_FILE', tmp_path / 's.json'):
            with patch('gui_launcher.settings_manager.CONFIG_DIR', tmp_path):
                mgr = SettingsManager()
                mgr.set("ai", "api_key", "key-123")

        assert mgr.has_api_key() is True

    def test_has_api_key_returns_false_when_empty(self, tmp_path):
        from gui_launcher.settings_manager import SettingsManager

        with patch('gui_launcher.settings_manager.SETTINGS_FILE', tmp_path / 's.json'):
            with patch('gui_launcher.settings_manager.CONFIG_DIR', tmp_path):
                mgr = SettingsManager()
                mgr.set("ai", "api_key", "")

        assert mgr.has_api_key() is False

    def test_has_api_key_returns_false_when_missing(self, tmp_path):
        from gui_launcher.settings_manager import SettingsManager

        with patch('gui_launcher.settings_manager.SETTINGS_FILE', tmp_path / 's.json'):
            with patch('gui_launcher.settings_manager.CONFIG_DIR', tmp_path):
                mgr = SettingsManager()
                if "ai" in mgr.settings and "api_key" in mgr.settings["ai"]:
                    del mgr.settings["ai"]["api_key"]

        assert mgr.has_api_key() is False

    def test_get_models_for_provider(self, tmp_path):
        from gui_launcher.settings_manager import SettingsManager

        with patch('gui_launcher.settings_manager.SETTINGS_FILE', tmp_path / 's.json'):
            with patch('gui_launcher.settings_manager.CONFIG_DIR', tmp_path):
                mgr = SettingsManager()

        models = mgr.get_models_for_provider("openai")
        assert "gpt-4o" in models

    def test_get_models_for_unknown_provider_returns_empty(self, tmp_path):
        from gui_launcher.settings_manager import SettingsManager

        with patch('gui_launcher.settings_manager.SETTINGS_FILE', tmp_path / 's.json'):
            with patch('gui_launcher.settings_manager.CONFIG_DIR', tmp_path):
                mgr = SettingsManager()

        models = mgr.get_models_for_provider("unknown")
        assert models == []

    def test_merge_defaults_fills_missing_keys(self, tmp_path):
        from gui_launcher.settings_manager import SettingsManager

        settings_file = tmp_path / 'settings.json'
        settings_file.write_text(json.dumps({"ai": {}}), encoding='utf-8')

        with patch('gui_launcher.settings_manager.SETTINGS_FILE', settings_file):
            with patch('gui_launcher.settings_manager.CONFIG_DIR', tmp_path):
                mgr = SettingsManager()

        assert mgr.get("ai", "provider") == "kimi"
