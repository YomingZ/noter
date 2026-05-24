"""Processing service — GUI-free batch PDF processing logic.

Extracted from WorkerThread.run() to enable unit testing.
No PyQt dependency. All business logic lives here.
"""

import logging
import os
from pathlib import Path
from typing import Generator

from pdf_summarizer.models import AIProvider, ProcessResult
from pdf_summarizer.summarizer import Summarizer
from pdf_summarizer.config import config

logger = logging.getLogger(__name__)


class ProcessingService:
    """GUI-free batch processing orchestrator.

    Accepts AI config as a dict (not from settings_manager).
    Creates Summarizer instances for each file.
    Yields ProcessResult objects via generator.
    """

    def __init__(
        self,
        provider: str,
        output_format: str,
        output_dir: Path,
        obsidian_template: Path | None = None,
        obsidian_course: str | None = None,
        obsidian_vault: Path | None = None,
    ):
        self.provider = provider
        self.output_format = output_format
        self.output_dir = Path(output_dir)
        self.obsidian_template = obsidian_template
        self.obsidian_course = obsidian_course
        self.obsidian_vault = obsidian_vault
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def configure_ai(self, ai_config: dict):
        """Apply AI configuration: env vars + global config object.

        Args:
            ai_config: dict with keys:
                provider, api_key, model, base_url, temperature
        """
        provider = ai_config.get("provider", "kimi")
        api_key = ai_config.get("api_key", "")

        if not api_key:
            raise ValueError("未配置 API Key，请在设置中配置")

        os.environ["KIMI_API_KEY"] = api_key if provider == "kimi" else ""
        os.environ["OPENAI_API_KEY"] = api_key if provider == "openai" else ""
        os.environ["ANTHROPIC_API_KEY"] = api_key if provider == "anthropic" else ""
        os.environ["DEEPSEEK_API_KEY"] = api_key if provider == "deepseek" else ""

        model = ai_config.get("model", "deepseek-chat")
        base_url = ai_config.get("base_url", "")

        if provider == "kimi":
            config.kimi_api_key = api_key
            config.kimi_model = model
            if base_url:
                config.kimi_base_url = base_url
        elif provider == "openai":
            config.openai_api_key = api_key
            config.openai_model = model
            if base_url:
                config.openai_base_url = base_url
        elif provider == "anthropic":
            config.anthropic_api_key = api_key
            config.anthropic_model = model
        elif provider == "deepseek":
            config.deepseek_api_key = api_key
            config.deepseek_model = model
            if base_url:
                config.deepseek_base_url = base_url

        config.default_provider = provider
        config.temperature = ai_config.get("temperature", 0.7)

    def process_one(self, file_path: Path) -> ProcessResult:
        """Process a single PDF file.

        Returns ProcessResult with success/failure info.
        """
        file_path = Path(file_path)
        provider_enum = AIProvider(self.provider)

        summarizer = Summarizer(
            provider=provider_enum,
            output_dir=self.output_dir,
        )

        result = summarizer.process(
            file_path,
            output_format=self.output_format,
            template_path=self.obsidian_template,
            course_name=self.obsidian_course,
            vault_root=self.obsidian_vault,
        )

        return result

    def process_batch(self, files: list[Path]) -> Generator[ProcessResult, None, None]:
        """Process multiple files, yielding one result at a time.

        Respects cancel flag set by cancel().
        """
        total = len(files)
        success_count = 0

        for file_path in files:
            if self._cancelled:
                break

            try:
                result = self.process_one(file_path)
                yield result

                if result.success:
                    success_count += 1

            except Exception as e:
                error_result = ProcessResult(
                    input_file=file_path,
                    success=False,
                    error_message=str(e),
                )
                yield error_result
                self._write_error_log(file_path, str(e))

    def _write_error_log(self, file_path: Path, error_message: str):
        import traceback

        log_file = self.output_dir / "error.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*50}\n处理文件: {file_path}\n")
            f.write(f"错误: {error_message}\n")
            f.write(traceback.format_exc())
