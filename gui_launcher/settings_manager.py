"""SettingsManager module — unified configuration management.

Extracted from gui_launcher.py and settings_dialog.py to eliminate DRY violation.
Supports: JSON persistence, API key encryption (Fernet), profile system.
Zero PyQt dependency.
"""

import base64
import json
import os
from pathlib import Path
from typing import Any, Dict, List

CONFIG_DIR = Path.home() / ".noter"
SETTINGS_FILE = CONFIG_DIR / "settings.json"
KEY_FILE = CONFIG_DIR / ".encryption_key"


def _get_fernet():
    """Get a Fernet encryptor with a machine-bound key.

    Key is derived from machine hostname + random salt stored in config dir.
    This ensures the encrypted data is bound to this machine.
    """
    try:
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    except ImportError:
        return None

    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)

    if KEY_FILE.exists():
        with open(KEY_FILE, 'rb') as f:
            key = f.read()
    else:
        salt = os.urandom(16)
        hostname = os.uname().nodename if hasattr(os, 'uname') else os.environ.get('COMPUTERNAME', 'unknown')
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=600000)
        key = base64.urlsafe_b64encode(kdf.derive(hostname.encode()))
        KEY_FILE.write_bytes(key)

    return Fernet(key)


def _encrypt(text: str) -> str:
    """Encrypt text using Fernet. Falls back to empty string on failure."""
    if not text:
        return ""
    f = _get_fernet()
    if f is None:
        return text
    try:
        return f.encrypt(text.encode()).decode()
    except Exception:
        return text


def _decrypt(text: str) -> str:
    """Decrypt text using Fernet. Returns original text on failure."""
    if not text:
        return ""
    f = _get_fernet()
    if f is None:
        return text
    try:
        return f.decrypt(text.encode()).decode()
    except Exception:
        return text


class SettingsManager:
    """设置管理器 - 单例模式，支持多配置文件"""

    _instance = None
    _initialized = False

    DEFAULT_SETTINGS = {
        "ai": {
            "provider": "kimi",
            "api_key": "",
            "model": "moonshot-v1-8k",
            "base_url": "",
            "temperature": 0.7
        },
        "output": {
            "format": "docx",
            "verbosity": "detailed",
            "include_examples": True,
            "generate_checklist": True,
            "add_page_numbers": True,
            "insert_toc": True,
        },
        "storage": {
            "output_folder": "",
            "keep_markdown": True,
            "obsidian_vault_default": "",
        },
        "interface": {
            "theme": "system",
            "remember_last_folder": True,
        }
    }

    PROVIDER_MODELS = {
        "kimi": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
        "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "anthropic": ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
        "deepseek": ["deepseek-chat", "deepseek-reasoner"],
        "custom": []
    }

    def __new__(cls):
        """单例模式：确保全局只有一个实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.settings: Dict[str, Any] = {}
        self.current_profile = "默认配置"
        self.profiles_dir = CONFIG_DIR / "profiles"
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.load()

    def get_profiles(self) -> List[str]:
        """获取所有配置文件列表"""
        profiles = ["默认配置"]
        if self.profiles_dir.exists():
            for f in self.profiles_dir.glob("*.json"):
                profiles.append(f.stem)
        return profiles

    def save_profile(self, name: str):
        """保存当前配置为新配置文件"""
        if name == "默认配置":
            return

        try:
            self.profiles_dir.mkdir(parents=True, exist_ok=True)
            profile_file = self.profiles_dir / f"{name}.json"

            settings_copy = json.loads(json.dumps(self.settings))

            if settings_copy.get("ai", {}).get("api_key"):
                encrypted = _encrypt(settings_copy["ai"]["api_key"])
                if encrypted:
                    settings_copy["ai"]["api_key"] = encrypted

            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(settings_copy, f, indent=2, ensure_ascii=False)

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to save profile '{name}': {e}")
            raise

    def load_profile(self, name: str) -> bool:
        """加载指定配置文件"""
        if name == "默认配置":
            self.load()
            return True
        profile_file = self.profiles_dir / f"{name}.json"
        if profile_file.exists():
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                if self.settings.get("ai", {}).get("api_key"):
                    self.settings["ai"]["api_key"] = _decrypt(self.settings["ai"]["api_key"])
                self._merge_defaults()
                self.current_profile = name
                return True
            except Exception:
                return False
        return False

    def delete_profile(self, name: str) -> bool:
        """删除配置文件"""
        if name == "默认配置":
            return False
        profile_file = self.profiles_dir / f"{name}.json"
        if profile_file.exists():
            profile_file.unlink()
            return True
        return False

    def load(self):
        """加载设置"""
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                if self.settings.get("ai", {}).get("api_key"):
                    self.settings["ai"]["api_key"] = _decrypt(self.settings["ai"]["api_key"])
            except Exception:
                self.settings = self.DEFAULT_SETTINGS.copy()
        else:
            self.settings = self.DEFAULT_SETTINGS.copy()
        self._merge_defaults()

    def _merge_defaults(self):
        """合并默认值"""
        def merge(target, source):
            for key, value in source.items():
                if key not in target:
                    target[key] = value
                elif isinstance(value, dict):
                    merge(target[key], value)

        merge(self.settings, self.DEFAULT_SETTINGS)

    def save(self):
        """保存设置"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        settings_copy = json.loads(json.dumps(self.settings))
        if settings_copy.get("ai", {}).get("api_key"):
            settings_copy["ai"]["api_key"] = _encrypt(settings_copy["ai"]["api_key"])
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings_copy, f, indent=2, ensure_ascii=False)

    def get(self, *keys, default=None):
        value = self.settings
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
        return value if value is not None else default

    def set(self, *keys_and_value):
        keys = list(keys_and_value[:-1])
        value = keys_and_value[-1]
        target = self.settings
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        target[keys[-1]] = value

    def has_api_key(self) -> bool:
        return bool(self.settings.get("ai", {}).get("api_key"))

    def get_models_for_provider(self, provider: str) -> List[str]:
        return self.PROVIDER_MODELS.get(provider, [])

    @classmethod
    def reset_instance(cls):
        """重置单例实例（主要用于测试）"""
        cls._instance = None
        cls._initialized = False


# 全局单例实例（推荐使用）
settings_manager = SettingsManager()
