"""Obsidian note generation using template-based AI prompting."""

import logging
import re
from collections import OrderedDict
from pathlib import Path
from typing import Optional

from pdf_summarizer.models import PDFDocument, ProcessResult, ContentPart
from pdf_summarizer.vault_indexer import VaultIndexer, VaultNotFoundError

logger = logging.getLogger(__name__)

CHARS_PER_TOKEN = 1.5
MAX_TEMPLATE_CACHE_SIZE = 10

IMAGES_DIR_NAME = "_images"


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

        placeholder = "{{content}}"
        has_placeholder = placeholder in template_content

        full_text = document.get_full_text()
        estimated_tokens = len(full_text) / CHARS_PER_TOKEN

        raw_response: str
        if estimated_tokens > self._max_tokens:
            raw_response = self._generate_with_chunking(full_text, template_content, has_placeholder, use_cache)
        else:
            user_prompt = self._build_prompt(template_content, full_text, has_placeholder)
            raw_response = self._call_ai_with_retry(user_prompt, use_cache)

        images_dir: Optional[Path] = None
        if document.has_images():
            target_dir = self._resolve_target_dir(vault_root, course_name)
            images_dir = self._save_vault_images(document, target_dir)
            if images_dir:
                rel_path = images_dir.relative_to(target_dir)
                raw_response = self._inject_image_references(raw_response, rel_path, pages_total=len(document.pages))

        if has_placeholder:
            before, after = template_content.split(placeholder, 1)
            fixed_content = ObsidianNoteGenerator._fix_latex_for_obsidian(raw_response)
            final_content = before + "\n" + fixed_content + "\n" + after
            output_file = self._write_to_vault(
                final_content, vault_root, course_name,
                output_name or document.file_path.stem,
            )
        else:
            output_file = self._write_to_vault(
                raw_response, vault_root, course_name,
                output_name or document.file_path.stem,
            )

        result.output_file = output_file
        result.success = True
        logger.info("Obsidian note saved to: %s", output_file)
        return result

    def _resolve_target_dir(self, vault_root: Path, course_name: str) -> Path:
        indexer = VaultIndexer(vault_root)
        return indexer.resolve_course_path(course_name)

    def _generate_with_chunking(
        self, full_text: str, template_content: str, has_placeholder: bool, use_cache: bool
    ) -> str:
        logger.info(
            "Content too large (%.0f tokens), chunking...",
            len(full_text) / CHARS_PER_TOKEN,
        )

        chunks = self._split_text_into_chunks(full_text)

        partial_summaries = []
        for i, chunk in enumerate(chunks):
            logger.info("Processing chunk %d/%d...", i + 1, len(chunks))
            if i == 0:
                chunk_prompt = self._build_prompt(template_content, chunk, has_placeholder)
            else:
                chunk_prompt = (
                    "以下是课件内容的一部分（第{}部分/共{}部分），请继续生成对应的笔记内容：\n\n{}"
                ).format(i + 1, len(chunks), chunk)

            summary = self._call_ai_with_retry(chunk_prompt, use_cache)
            partial_summaries.append(summary)

        if len(partial_summaries) == 1:
            return partial_summaries[0]

        merge_prompt = (
            "以下是一份长笔记被拆分为多个部分生成的结果。\n"
            "请将它们合并成一份完整、连贯、结构清晰的学习笔记。\n"
            "注意：删除重复的标题和过渡性文字，保证内容流畅。\n\n"
        )
        for i, s in enumerate(partial_summaries):
            merge_prompt += f"--- 第{i + 1}部分 ---\n{s}\n\n"

        return self._call_ai_with_retry(merge_prompt, use_cache)

    @staticmethod
    def _split_text_into_chunks(text: str, max_chars: Optional[int] = None) -> list[str]:
        if max_chars is None:
            max_chars = 8000

        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) > max_chars and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks if chunks else [text]

    def _save_vault_images(self, document: PDFDocument, target_dir: Path) -> Optional[Path]:
        images_dir = target_dir / IMAGES_DIR_NAME
        images_dir.mkdir(parents=True, exist_ok=True)

        saved_count = 0
        for page in document.pages:
            for idx, b64_img in enumerate(page.images_base64):
                try:
                    import base64
                    img_data = base64.b64decode(b64_img)
                    img_filename = f"page{page.page_number:03d}_{idx:02d}.png"
                    img_path = images_dir / img_filename
                    with open(img_path, "wb") as f:
                        f.write(img_data)
                    saved_count += 1
                except Exception as e:
                    logger.warning("Failed to save image from page %d: %s", page.page_number, e)

        if saved_count > 0:
            logger.info("Saved %d images to %s", saved_count, images_dir)
            return images_dir
        return None

    @staticmethod
    def _inject_image_references(text: str, rel_path: Path, pages_total: int = 1) -> str:
        lines = text.split("\n")
        result = []
        image_inserted = False

        for line in lines:
            stripped = line.strip()

            if re.match(r'^!\[\[', stripped):
                result.append(line)
                continue

            if not image_inserted and re.match(r'^# ', stripped):
                result.append(line)
                result.append("")
                for pno in range(1, pages_total + 1):
                    result.append(f"![[{rel_path}/page{pno:03d}_00.png]]")
                result.append("")
                image_inserted = True
                continue

            result.append(line)

        if not image_inserted:
            result.append("")
            for pno in range(1, pages_total + 1):
                result.append(f"![[{rel_path}/page{pno:03d}_00.png]]")
            result.append("")

        return "\n".join(result)

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

    def _build_prompt(self, template_content: str, content_text: str, has_placeholder: bool) -> str:
        from pdf_summarizer.config import config
        from pdf_summarizer.summarizer import Summarizer

        prompts = config.load_prompts()
        obsidian_cfg = prompts.get("obsidian_template", {})

        if has_placeholder:
            instruction_template = (
                "{template_content}\n\n"
                "请根据以下课件内容，为 {{content}} 占位符位置生成笔记正文。\n\n"
                "课件内容：\n{content}"
            )
            structure_skeleton = self._extract_template_structure(template_content, aggressive=True)
            return instruction_template.replace(
                "{template_content}", structure_skeleton
            ).replace("{content}", content_text)

        instruction_template = obsidian_cfg.get(
            "template_instruction",
            "请参考以下模板格式：\n{template_content}\n\n课件内容：\n{content}"
        )

        structure_skeleton = self._extract_template_structure(template_content)
        user_prompt = instruction_template.replace(
            "{template_content}", structure_skeleton
        ).replace("{content}", content_text)

        estimated_tokens = len(user_prompt) / CHARS_PER_TOKEN
        if estimated_tokens > self._max_tokens:
            logger.info(
                "Content too large (%.0f tokens), further truncating template...",
                estimated_tokens,
            )
            structure_skeleton = self._extract_template_structure(
                template_content, aggressive=True
            )
            user_prompt = instruction_template.replace(
                "{template_content}", structure_skeleton
            ).replace("{content}", content_text)

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
            max_tokens=16384,
        )

        if not raw_response or not raw_response.strip():
            logger.warning("AI returned empty, retrying once...")
            raw_response = self._ai_generate(
                system_prompt=system,
                user_prompt=user_prompt,
                use_cache=False,
                max_tokens=16384,
            )

        if not raw_response or not raw_response.strip():
            raise ValueError("AI 返回内容为空，请重试。")

        return raw_response

    @staticmethod
    def _fix_latex_for_obsidian(text: str) -> str:
        text = ObsidianNoteGenerator._fix_escaped_dollars(text)
        text = ObsidianNoteGenerator._convert_parenthesis_environments(text)
        text = ObsidianNoteGenerator._convert_begin_end_environments(text)
        text = ObsidianNoteGenerator._normalize_dollar_blocks(text)
        text = ObsidianNoteGenerator._fix_unbalanced_braces(text)
        text = ObsidianNoteGenerator._fix_cases_environment(text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    @staticmethod
    def _fix_cases_environment(text: str) -> str:
        text = re.sub(r'\\end\{cases(?!\})', r'\\end{cases}', text)
        text = re.sub(r'\n\$\$\n(\\begin\{cases\})', r'\n\1', text)
        text = re.sub(r'(\\end\{cases\})\n\$\$\n\$\$', r'\1\n$$', text)
        return text

    @staticmethod
    def _normalize_dollar_blocks(text: str) -> str:
        lines = text.split('\n')
        result = []
        in_block = False
        pending_content = []

        for line in lines:
            parts = line.split('$$')

            if len(parts) == 1:
                if in_block:
                    pending_content.append(line)
                else:
                    result.append(line)
                continue

            nonempty_parts = [p for p in parts if p.strip()]
            isolated_dd_count = len(parts) - 1

            if not in_block:
                before = parts[0]
                if before.strip():
                    result.append(before)

                if isolated_dd_count >= 2:
                    result.append('$$')
                    inner = parts[1]
                    if inner.strip():
                        result.append(inner.strip())
                    result.append('$$')
                    after = ''.join(parts[2:])
                    if after.strip():
                        result.append(after)
                elif isolated_dd_count == 1:
                    after = parts[1]
                    if after.strip():
                        pending_content = [after.strip()]
                    else:
                        pending_content = []
                    result.append('$$')
                    in_block = True
            else:
                before = parts[0]
                after = parts[-1] if len(parts) > 1 else ''

                if before.strip():
                    pending_content.append(before)

                if isolated_dd_count == 1:
                    result.extend(pending_content)
                    result.append('$$')
                    pending_content = []
                    in_block = False
                    if after.strip():
                        result.append(after)
                elif isolated_dd_count >= 2:
                    result.extend(pending_content)
                    result.append('$$')
                    inner = parts[1]
                    if inner.strip():
                        result.append(inner.strip())
                    if len(parts) > 2:
                        result.append('$$')
                        remaining = ''.join(parts[2:])
                        if remaining.strip():
                            result.append(remaining)
                    pending_content = []
                    in_block = False

        if in_block and pending_content:
            result.extend(pending_content)
            result.append('$$')

        return '\n'.join(result)

    @staticmethod
    def _fix_escaped_dollars(text: str) -> str:
        text = re.sub(r'\\\$', '\\\\', text)
        return text

    @staticmethod
    def _convert_parenthesis_environments(text: str) -> str:
        text = re.sub(
            r'\\\((.*?)\\\)',
            lambda m: '$' + m.group(1).strip() + '$',
            text,
            flags=re.DOTALL,
        )
        text = re.sub(
            r'\\\[(.*?)\\\]',
            lambda m: '$$\n' + m.group(1).strip() + '\n$$',
            text,
            flags=re.DOTALL,
        )
        return text

    @staticmethod
    def _fix_unbalanced_braces(text: str) -> str:
        lines = text.split('\n')
        result = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('$$') and stripped.endswith('$$') and len(stripped) > 4:
                inner = stripped[2:-2].strip()
                open_n = inner.count('{')
                close_n = inner.count('}')
                if open_n > close_n:
                    inner += '}' * (open_n - close_n)
                elif close_n > open_n:
                    inner = '{' * (close_n - open_n) + inner
                result.append(f'$${inner}$$')
            else:
                open_n = line.count('{')
                close_n = line.count('}')
                if open_n > close_n:
                    is_formula = '$' in line
                    if is_formula:
                        line += '}' * (open_n - close_n)
                result.append(line)
        return '\n'.join(result)

    LATEX_ENVIRONMENTS_SIMPLE = {
        'equation', 'equation*', 'displaymath'
    }

    LATEX_ENVIRONMENTS_COMPLEX = {
        'align', 'align*', 'aligned',
        'gather', 'gather*', 'split',
        'matrix', 'bmatrix', 'pmatrix', 'vmatrix', 'Vmatrix',
        'cases', 'array',
    }

    @staticmethod
    def _convert_begin_end_environments(text: str) -> str:
        for env in ObsidianNoteGenerator.LATEX_ENVIRONMENTS_SIMPLE:
            pattern = re.compile(
                r'\\begin\{' + re.escape(env) + r'\}(.*?)\\end\{' + re.escape(env) + r'\}',
                re.DOTALL
            )
            text = pattern.sub(lambda m: '$$\n' + m.group(1).strip() + '\n$$', text)

        for env in ObsidianNoteGenerator.LATEX_ENVIRONMENTS_COMPLEX:
            pattern = re.compile(
                r'\\begin\{' + re.escape(env) + r'\}(.*?)\\end\{' + re.escape(env) + r'\}',
                re.DOTALL
            )
            text = pattern.sub(
                lambda m: '$$\n\\begin{' + env + '}\n' + m.group(1).strip() + '\n\\end{' + env + '\n$$',
                text,
            )

        return text

    @staticmethod
    def _write_to_vault(
        raw_response: str,
        vault_root: Path,
        course_name: str,
        output_name: str,
    ) -> Path:
        fixed_content = ObsidianNoteGenerator._fix_latex_for_obsidian(raw_response)

        indexer = VaultIndexer(vault_root)
        target_dir = indexer.resolve_course_path(course_name)
        target_dir.mkdir(parents=True, exist_ok=True)
        output_file = target_dir / f"{output_name}.md"
        output_file.write_text(fixed_content, encoding="utf-8")
        return output_file

    @staticmethod
    def _extract_template_structure(template_content: str, aggressive: bool = False) -> str:
        lines = template_content.split("\n")
        skeleton_lines = []
        for line in lines:
            stripped = line.strip()

            if aggressive:
                if stripped.startswith("#"):
                    level = len(stripped.split()[0]) if stripped.split() else 1
                    skeleton_lines.append("#" * level + " ")
                elif stripped == "":
                    skeleton_lines.append("")
                continue

            if stripped.startswith("#"):
                level = len(stripped.split()[0]) if stripped.split() else 1
                skeleton_lines.append("#" * level + " ")
            elif stripped.startswith("---"):
                skeleton_lines.append(line)
            elif stripped.startswith("```"):
                skeleton_lines.append(line)
            elif stripped.startswith("$$"):
                skeleton_lines.append(line)
            elif stripped.startswith("|"):
                if stripped.count("|") >= 3 and "--" in stripped:
                    skeleton_lines.append(line)
                elif not any(c.isalnum() for c in stripped.replace("|", "").replace(" ", "")):
                    skeleton_lines.append(line)
                else:
                    parts = stripped.split("|")
                    skeleton_lines.append("| " + " | ".join([""] * (len(parts) - 2)) + " |")
            elif stripped.startswith("![[") or stripped.startswith("【"):
                skeleton_lines.append(line)
            elif stripped.startswith("- ["):
                skeleton_lines.append("- [ ] ")
            elif stripped.startswith("- ") or stripped.startswith("* "):
                skeleton_lines.append("- ")
            elif stripped.startswith("> "):
                skeleton_lines.append("> ")
            elif stripped == "":
                skeleton_lines.append("")

        return "\n".join(skeleton_lines)
