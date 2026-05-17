"""Obsidian note generation using template-based AI prompting."""

import logging
from collections import OrderedDict
from pathlib import Path
from typing import Optional

from pdf_summarizer.models import PDFDocument, ProcessResult
from pdf_summarizer.vault_indexer import VaultIndexer, VaultNotFoundError

logger = logging.getLogger(__name__)

CHARS_PER_TOKEN = 1.5
MAX_TEMPLATE_CACHE_SIZE = 10


class ObsidianNoteGenerator:
    """Generates Obsidian notes in vault using AI and template reference."""

    def __init__(self, ai_generate_fn, max_content_tokens: int = 6000):
        self._ai_generate = ai_generate_fn
        self._max_tokens = max_content_tokens
        self._template_cache: OrderedDict[str, str] = OrderedDict()

    def generate(
        self,
        document: PDFDocument,
        template_path: Path,
        course_name: str,
        vault_root: Path,
        output_name: Optional[str] = None,
        use_cache: bool = True,
    ) -> ProcessResult:
        """Generate an Obsidian note and write it to the vault.

        Args:
            document: The parsed PDF document
            template_path: Path to the .md template file
            course_name: Course name for vault folder matching
            vault_root: Obsidian vault root path
            output_name: Output filename (without extension)
            use_cache: Whether to cache AI responses

        Returns:
            ProcessResult with the output file path on success
        """
        result = ProcessResult(input_file=document.file_path)
        result.pages_processed = len(document.pages)

        template_path = Path(template_path)
        vault_root = Path(vault_root)

        self._validate_inputs(template_path, vault_root)

        template_content = self._load_template(template_path)
        user_prompt = self._build_prompt(template_content, document)

        raw_response = self._call_ai_with_retry(user_prompt, use_cache)

        output_file = self._write_to_vault(
            raw_response, vault_root, course_name,
            output_name or document.file_path.stem,
        )

        result.output_file = output_file
        result.success = True
        logger.info("Obsidian note saved to: %s", output_file)
        return result

    def _validate_inputs(self, template_path: Path, vault_root: Path):
        if not template_path.exists():
            raise FileNotFoundError(
                f"模板文件不存在: {template_path}\n"
                f"请检查 --template 参数。"
            )
        if not vault_root.is_dir():
            raise VaultNotFoundError(
                f"Vault 目录不存在: {vault_root}\n"
                f"请检查 --vault 参数。"
            )

    def _load_template(self, template_path: Path) -> str:
        template_key = str(template_path.resolve())
        if template_key in self._template_cache:
            self._template_cache.move_to_end(template_key)
            return self._template_cache[template_key]

        content = template_path.read_text(encoding="utf-8")
        self._template_cache[template_key] = content

        if len(self._template_cache) > MAX_TEMPLATE_CACHE_SIZE:
            evicted_key, _ = self._template_cache.popitem(last=False)
            logger.debug("Evicted oldest template from cache: %s", evicted_key)

        return content

    def _build_prompt(self, template_content: str, document: PDFDocument) -> str:
        from pdf_summarizer.config import config

        prompts = config.load_prompts()
        obsidian_cfg = prompts.get("obsidian_template", {})
        system = obsidian_cfg.get(
            "system_prompt",
            "你是一位大学授课教授，正在制作课程讲稿笔记。"
        )
        instruction_template = obsidian_cfg.get(
            "template_instruction",
            "请参考以下模板格式：\n{template_content}\n\n课件内容：\n{content}"
        )

        full_text = document.get_full_text()
        user_prompt = instruction_template.replace(
            "{template_content}", template_content
        ).replace("{content}", full_text)

        estimated_tokens = len(user_prompt) / CHARS_PER_TOKEN
        if estimated_tokens > self._max_tokens:
            logger.info(
                "Content too large (%.0f tokens), sending template structure only...",
                estimated_tokens,
            )
            structure_skeleton = self._extract_template_structure(template_content)
            user_prompt = instruction_template.replace(
                "{template_content}", structure_skeleton
            ).replace("{content}", full_text)

        return user_prompt

    def _call_ai_with_retry(self, user_prompt: str, use_cache: bool) -> str:
        from pdf_summarizer.config import config

        prompts = config.load_prompts()
        obsidian_cfg = prompts.get("obsidian_template", {})
        system = obsidian_cfg.get(
            "system_prompt",
            "你是一位大学授课教授，正在制作课程讲稿笔记。"
        )

        raw_response = self._ai_generate(
            system_prompt=system,
            user_prompt=user_prompt,
            use_cache=use_cache,
        )

        if not raw_response or not raw_response.strip():
            logger.warning("AI returned empty, retrying once...")
            raw_response = self._ai_generate(
                system_prompt=system,
                user_prompt=user_prompt,
                use_cache=False,
            )

        if not raw_response or not raw_response.strip():
            raise ValueError("AI 返回内容为空，请重试。")

        return raw_response

    @staticmethod
    def _write_to_vault(
        raw_response: str,
        vault_root: Path,
        course_name: str,
        output_name: str,
    ) -> Path:
        indexer = VaultIndexer(vault_root)
        target_dir = indexer.resolve_course_path(course_name)
        target_dir.mkdir(parents=True, exist_ok=True)
        output_file = target_dir / f"{output_name}.md"
        output_file.write_text(raw_response, encoding="utf-8")
        return output_file

    @staticmethod
    def _extract_template_structure(template_content: str) -> str:
        lines = template_content.split("\n")
        skeleton_lines = []
        for line in lines:
            stripped = line.strip()
            if (stripped.startswith("#")
                    or stripped.startswith("---")
                    or stripped.startswith("|")
                    or stripped.startswith("- ")
                    or stripped.startswith("* ")
                    or stripped.startswith(">")
                    or stripped.startswith("$")
                    or stripped.startswith("![[")
                    or stripped.startswith("```")
                    or stripped.startswith("\\")
                    or stripped == ""
                    or stripped.startswith("【")):
                skeleton_lines.append(line)
        return "\n".join(skeleton_lines)
