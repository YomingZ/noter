"""Configuration management for PDF Summarizer."""

import logging
import os
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

from pdf_summarizer.models import AIProvider

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment and config files."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # OpenAI Configuration
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"

    # Anthropic Configuration
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6-20250514"

    # Kimi Configuration
    kimi_api_key: str = ""
    kimi_base_url: str = "https://api.moonshot.cn/v1"
    kimi_model: str = "moonshot-v1-8k"

    # DeepSeek Configuration
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # Default Provider
    default_provider: str = "openai"

    # Output Settings
    output_directory: str = "./output"

    # PDF Settings
    max_pages: int = 0
    min_page_text: int = 50

    # AI Settings
    temperature: float = 0.3
    max_tokens: int = 4096

    # Cache Settings
    cache_enabled: bool = True
    cache_max_age_hours: int = 24

    # Rate Limit Settings
    max_concurrent_requests: int = 3


class ConfigManager:
    """Manages application configuration."""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path("config")
        self._settings: Optional[Settings] = None
        self._prompts: Optional[dict[str, str]] = None
        self._yaml_config: Optional[dict[str, Any]] = None

    @property
    def settings(self) -> Settings:
        """Get application settings."""
        if self._settings is None:
            load_dotenv()
            self._settings = Settings()
        return self._settings

    def load_yaml_config(self) -> dict[str, Any]:
        """Load configuration from YAML file."""
        if self._yaml_config is not None:
            return self._yaml_config

        config_file = self.config_dir / "settings.yaml"
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                self._yaml_config = yaml.safe_load(f) or {}
        else:
            self._yaml_config = {}
        return self._yaml_config

    def load_prompts(self, subject: str = None) -> dict[str, str]:
        """Load prompt templates from YAML file."""
        if self._prompts is not None:
            return self._prompts

        prompts_file = self.config_dir / "prompts.yaml"
        subjects_file = self.config_dir / "prompts_subjects.yaml"

        # Try to load subjects file first
        if subjects_file.exists():
            with open(subjects_file, "r", encoding="utf-8") as f:
                self._prompts = yaml.safe_load(f) or {}
        elif prompts_file.exists():
            with open(prompts_file, "r", encoding="utf-8") as f:
                self._prompts = yaml.safe_load(f) or {}
        else:
            self._prompts = self._get_default_prompts()
        return self._prompts

    def get_subject_prompt(self, subject: str) -> str:
        """Get prompt for a specific subject."""
        prompts = self.load_prompts()
        subjects = prompts.get("subjects", {})

        if subject in subjects:
            return subjects[subject].get("prompt", prompts.get("summary_prompt", ""))

        return prompts.get("summary_prompt", "")

    def detect_subject(self, content: str) -> str:
        """Detect subject from content keywords."""
        prompts = self.load_prompts()
        subjects = prompts.get("subjects", {})

        content_lower = content.lower()

        for subject_key, subject_data in subjects.items():
            keywords = subject_data.get("keywords", [])
            matches = sum(1 for kw in keywords if kw in content_lower)
            if matches >= 2:  # At least 2 keyword matches
                logger.info(f"Detected subject: {subject_data.get('name', subject_key)}")
                return subject_key

        return "default"

    def _get_default_prompts(self) -> dict[str, str]:
        """Get default prompt templates."""
        return {
            "system_prompt": "你是一位专业的教育内容分析师，擅长从课件中提取重点知识并生成结构化的学习笔记。",
            "summary_prompt": "请分析以下课件内容，生成结构化的备考笔记：\n\n{content}",
        }

    def get_ai_config(self, provider: Optional[AIProvider] = None) -> dict[str, Any]:
        """Get AI configuration for specified provider."""
        settings = self.settings
        provider = provider or AIProvider(settings.default_provider)

        config = {
            "provider": provider,
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens,
        }

        if provider == AIProvider.OPENAI:
            config["api_key"] = settings.openai_api_key
            config["base_url"] = settings.openai_base_url
            config["model"] = settings.openai_model
        elif provider == AIProvider.CLAUDE:
            config["api_key"] = settings.anthropic_api_key
            config["model"] = settings.anthropic_model
        elif provider == AIProvider.KIMI:
            config["api_key"] = settings.kimi_api_key
            config["base_url"] = settings.kimi_base_url
            config["model"] = settings.kimi_model
        elif provider == AIProvider.DEEPSEEK:
            config["api_key"] = settings.deepseek_api_key
            config["base_url"] = settings.deepseek_base_url
            config["model"] = settings.deepseek_model

        return config

    def get_output_dir(self) -> Path:
        """Get output directory path."""
        return Path(self.settings.output_directory).resolve()

    def ensure_output_dir(self) -> Path:
        """Ensure output directory exists and return path."""
        output_dir = self.get_output_dir()
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir


# Global config instance
config = ConfigManager()
