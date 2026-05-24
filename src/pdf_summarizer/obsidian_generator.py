"""Obsidian note generation using template-based AI prompting."""

import logging
import re
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

        placeholder = "{{content}}"
        has_placeholder = placeholder in template_content

        user_prompt = self._build_prompt(template_content, document)

        raw_response = self._call_ai_with_retry(user_prompt, use_cache)

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

        structure_skeleton = self._extract_template_structure(template_content)
        user_prompt = instruction_template.replace(
            "{template_content}", structure_skeleton
        ).replace("{content}", full_text)

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
    def _fix_latex_for_obsidian(text: str) -> str:
        text = ObsidianNoteGenerator._remove_double_dollar_blocks(text)

        text = ObsidianNoteGenerator._fix_escaped_dollars(text)

        text = ObsidianNoteGenerator._convert_parenthesis_environments(text)

        text = ObsidianNoteGenerator._convert_begin_end_environments(text)

        text = ObsidianNoteGenerator._clean_backtick_formulas(text)

        lines = text.split('\n')
        result = []
        in_formula_block = False
        formula_lines = []

        for line in lines:
            stripped = line.strip()

            if stripped == '\\[':
                in_formula_block = True
                formula_lines = []
                continue

            if stripped == '\\]':
                if in_formula_block and formula_lines:
                    raw_content = '\n'.join(formula_lines)
                    cleaned = ObsidianNoteGenerator._clean_latex_display(raw_content)
                    if cleaned:
                        result.append(f'$${cleaned}$$')
                in_formula_block = False
                formula_lines = []
                continue

            if in_formula_block:
                formula_lines.append(stripped)
                continue

            if (stripped.startswith('$$') and stripped.endswith('$$')
                    and len(stripped) > 4):
                inner = stripped[2:-2].strip()
                cleaned = ObsidianNoteGenerator._clean_latex_display(inner)
                if cleaned:
                    result.append(f'$${cleaned}$$')
                continue

            if (ObsidianNoteGenerator._looks_like_latex(stripped)
                    and not stripped.startswith('$')
                    and not stripped.startswith('`')
                    and not stripped.startswith('|')
                    and not stripped.startswith('>')
                    and not stripped.startswith('-')
                    and not stripped.startswith('*')
                    and not stripped.startswith('\\')):
                cleaned = ObsidianNoteGenerator._clean_latex_content(stripped)
                if cleaned:
                    result.append(f'$${cleaned}$$')
                continue

            result.append(line)

        text = '\n'.join(result)
        text = ObsidianNoteGenerator._clean_inline_formulas(text)
        text = ObsidianNoteGenerator._cleanup_remaining_issues(text)

        text = ObsidianNoteGenerator._fix_missing_braces(text)

        text = ObsidianNoteGenerator._post_cleanup(text)

        return text.strip()

    @staticmethod
    def _clean_backtick_formulas(text: str) -> str:
        pattern = re.compile(r'`([^`]*\$[^`]*)`')

        def clean_backtick_match(m):
            content = m.group(1)
            cleaned = ObsidianNoteGenerator._clean_latex_content(content)
            if cleaned:
                is_display = (
                    '\\frac' in cleaned or
                    '\\int' in cleaned or
                    '\\sum' in cleaned or
                    len(cleaned) > 30
                )
                if is_display:
                    return f'$${cleaned}$$'
                else:
                    return f'${cleaned}$'
            return m.group(0)

        text = pattern.sub(clean_backtick_match, text)
        return text

    @staticmethod
    def _cleanup_remaining_issues(text: str) -> str:
        text = re.sub(r'\\\\hat', r'\\hat', text)
        text = re.sub(r'\\\\frac', r'\\frac', text)
        text = re.sub(r'\\\\partial', r'\\partial', text)
        text = re.sub(r'\\\\Psi', r'\\Psi', text)
        text = re.sub(r'\\\\hbar', r'\\hbar', text)
        text = re.sub(r'\\\\lambda', r'\\lambda', text)
        text = re.sub(r'\\\\sigma', r'\\sigma', text)
        text = re.sub(r'\\\\infty', r'\\infty', text)
        return text

    @staticmethod
    def _fix_missing_braces(content: str) -> str:
        open_n = content.count('{')
        close_n = content.count('}')
        if open_n <= close_n:
            return content

        fixed = re.sub(
            r'(\^\{[^}]*\})(\s*\\[a-zA-Z]+)',
            r'\1}\2',
            content
        )

        if fixed.count('}') > fixed.count('{'):
            return content

        return fixed

    @staticmethod
    def _post_cleanup(text: str) -> str:
        text = re.sub(r'\)+\s*(\$\$)', r')\1', text)
        text = re.sub(r'\((\$\$)', r'\1', text)
        text = re.sub(r'(\$\$)\)', r'\1)', text)
        text = re.sub(r'([（(])\s*\$\$(.+?)\$\$\s*([）)])', r'\1$\2$\3', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text

    @staticmethod
    def _convert_parenthesis_environments(text: str) -> str:
        pattern = re.compile(r'\\\((.*?)\\\)', re.DOTALL)

        def convert_paren_match(m):
            content = m.group(1).strip()
            cleaned = ObsidianNoteGenerator._clean_latex_content(content)
            if not cleaned:
                return m.group(0)

            needs_display = (
                '\\int ' in cleaned or
                '\\sum ' in cleaned or
                '\\prod ' in cleaned or
                '\\begin{' in cleaned or
                cleaned.count('\\frac') >= 2 or
                cleaned.count('\\') >= 4 or
                len(cleaned) > 50
            )

            if needs_display:
                return f'$${cleaned}$$'
            else:
                return f'${cleaned}$'

        text = pattern.sub(convert_paren_match, text)
        return text

    @staticmethod
    def _fix_escaped_dollars(text: str) -> str:
        text = re.sub(r'\\\$frac', r'\\frac', text)
        text = re.sub(r'\\\$partial', r'\\partial', text)
        text = re.sub(r'\\\$Psi', r'\\Psi', text)
        text = re.sub(r'\\\$hat', r'\\hat', text)
        text = re.sub(r'\\\$hbar', r'\\hbar', text)
        text = re.sub(r'\\\$lambda', r'\\lambda', text)
        text = re.sub(r'\\\$sigma', r'\\sigma', text)
        text = re.sub(r'\\\$infty', r'\\infty', text)
        text = re.sub(r'\\\$pi', r'\\pi', text)
        text = re.sub(r'\\\$exp', r'\\exp', text)
        text = re.sub(r'\\\$left', r'\\left', text)
        text = re.sub(r'\\\$right', r'\\right', text)
        text = re.sub(r'\\\$alpha', r'\\alpha', text)
        text = re.sub(r'\\\$beta', r'\\beta', text)
        text = re.sub(r'\\\$gamma', r'\\gamma', text)
        text = re.sub(r'\\\$delta', r'\\delta', text)
        text = re.sub(r'\\\$theta', r'\\theta', text)
        text = re.sub(r'\\\$omega', r'\\omega', text)
        text = re.sub(r'\\\$phi', r'\\phi', text)
        text = re.sub(r'\)\\s*\\\$', ')', text)
        text = re.sub(r'\\\$\\\)', r'\\)', text)
        text = re.sub(r'\\\$\)\\\)', r'\\)', text)
        text = re.sub(r'\\\$\)', r'\\)', text)
        text = re.sub(r'\\\$\\', r'\\', text)
        text = re.sub(r'\\\$', '', text)
        return text

    @staticmethod
    def _clean_latex_display(content: str) -> str:
        content = content.strip()

        content = re.sub(r'\$\^(\*)', r'^\1', content)
        content = re.sub(r'\$\{', '{', content)
        content = re.sub(r'\}\$', '}', content)
        content = re.sub(r'(?<=[a-zA-Z0-9})\]])\$(?=[a-zA-Z{(])', '', content)
        content = re.sub(r'(?<=[a-zA-Z0-9=])\$(?=[\(])', '', content)
        content = re.sub(r'(?<=\^)\$(?=[a-zA-Z*])', '', content)
        content = re.sub(r'(?<=[a-zA-Z])\$\^', '^', content)
        content = re.sub(r'\$\(', '(', content)
        content = re.sub(r'(?<=\w)\$(?=\w)', '', content)

        content = re.sub(r'\$\s*\$', '', content)
        content = re.sub(r'(?<!\\)\$\\([a-zA-Z]+)', r'\\\1', content)

        content = re.sub(r'\$\{', '{', content)
        content = re.sub(r'\}\$', '}', content)
        content = re.sub(r'\$_', '_', content)
        content = re.sub(r'_\$', '_', content)
        content = re.sub(r'\$\^', '^', content)
        content = re.sub(r'^\$', '^', content)
        content = re.sub(r'\^(\$\w)', lambda m: '^' + m.group(1).replace('$', ''), content)
        content = re.sub(r'\^(\$\*)', r'^*', content)
        content = re.sub(r'\{(\$\w)', lambda m: '{' + m.group(1).replace('$', ''), content)
        content = re.sub(r'(\w)\$(\{)', r'\1\2', content)

        content = re.sub(r'(?<=[a-zA-Z0-9})\]_])\$(?=[a-zA-Z{])', '', content)
        content = re.sub(r'(?<=[a-zA-Z0-9})\]])\$(?=\d)', '', content)
        content = re.sub(r'(?<=\d)\$(?=[a-zA-Z{])', '', content)
        content = re.sub(r'(?<=[a-zA-Z])\$(?=[(\[])', '', content)
        content = re.sub(r'(?<=[)\]])\$(?=[a-zA-Z\d])', '', content)
        content = re.sub(r'(?<=\^)\$(?=[a-zA-Z*])', '', content)
        content = re.sub(r'(?<=[a-zA-Z])\$\^', '^', content)

        content = re.sub(r'\$(?=[=\s,;:\]\)\}])', '', content)
        content = re.sub(r'(?<=[=\s,;:\[\(])\$', '', content)

        content = content.replace('$\\', '\\')
        content = content.replace('\\$ ', ' ')
        content = content.replace('\\$', '\\')

        content = re.sub(r'(?<!\\)\$(?=[a-zA-Z])', '', content)

        content = re.sub(r'^\$|\$$', '', content)

        content = re.sub(r'\|\|', '|', content)
        content = re.sub(r'\\\|', '|', content)

        content = re.sub(r'\s+', ' ', content)

        content = content.replace('$', '')

        return content.strip()

    @staticmethod
    def _clean_inline_formulas(text: str) -> str:
        lines = text.split('\n')
        result = []
        for line in lines:
            if '$$' in line:
                result.append(line)
                continue

            cleaned_line = ObsidianNoteGenerator._fix_inline_formula_dollars(line)
            result.append(cleaned_line)

        return '\n'.join(result)

    @staticmethod
    def _fix_inline_formula_dollars(line: str) -> str:
        if '$' not in line:
            return line

        if '$$' in line:
            return line

        result = []
        i = 0
        while i < len(line):
            if line[i] == '$':
                end = line.find('$', i + 1)
                if end == -1:
                    result.append(line[i:])
                    break
                inner = line[i+1:end]
                cleaned = ObsidianNoteGenerator._clean_latex_content(inner)
                if cleaned:
                    result.append(f'${cleaned}$')
                else:
                    result.append(line[i:end+1])
                i = end + 1
            else:
                result.append(line[i])
                i += 1

        return ''.join(result)

    @staticmethod
    def _preprocess_inline_dollars(text: str) -> str:
        lines = text.split('\n')
        result = []
        for line in lines:
            if '$$' in line or line.strip().startswith('$$'):
                result.append(line)
                continue

            line = re.sub(r'(?<=[a-zA-Z0-9})\]])\s*\$(?=\s*[\\a-zA-Z{])', '', line)
            line = re.sub(r'(?<=[a-zA-Z])\s*\$(?=\s*[(\[])', '', line)

            result.append(line)
        return '\n'.join(result)

    @staticmethod
    def _remove_double_dollar_blocks(text: str) -> str:
        pattern = r'\$\$\s*\n\s*\$\$(.+?)\$\$\s*\n\s*\$\$'
        text = re.sub(pattern, lambda m: '$$' + m.group(1).strip() + '$$', text, flags=re.DOTALL)

        text = re.sub(r'\$\$\s*\n\s*\$\$', '$$', text)
        return text

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
            text = pattern.sub(lambda m: '$$' + m.group(1).strip() + '$$', text)

        for env in ObsidianNoteGenerator.LATEX_ENVIRONMENTS_COMPLEX:
            pattern = re.compile(
                r'\\begin\{' + re.escape(env) + r'\}(.*?)\\end\{' + re.escape(env) + r'\}',
                re.DOTALL
            )
            text = pattern.sub(lambda m: '$$\n\\begin{' + env + '}\n' + m.group(1).strip() + '\n\\end{' + env + '\n$$', text)

        return text

    @staticmethod
    def _clean_latex_content(content: str) -> str:
        content = content.strip()

        content = re.sub(r'\$\s*\$', '', content)

        content = re.sub(r'(?<!\\)\$\\([a-zA-Z]+)', r'\\\1', content)

        content = re.sub(r'\$\{', '{', content)
        content = re.sub(r'\}\$', '}', content)
        content = re.sub(r'\$_', '_', content)
        content = re.sub(r'_\$', '_', content)
        content = re.sub(r'\$\^', '^', content)
        content = re.sub(r'^\$', '^', content)
        content = re.sub(r'\^(\$\w)', lambda m: '^' + m.group(1).replace('$', ''), content)
        content = re.sub(r'\^(\$\*)', r'^*', content)
        content = re.sub(r'\{(\$\w)', lambda m: '{' + m.group(1).replace('$', ''), content)
        content = re.sub(r'(\w)\$(\{)', r'\1\2', content)

        content = re.sub(r'(?<=[a-zA-Z0-9})\]_])\$(?=[a-zA-Z{])', '', content)
        content = re.sub(r'(?<=[a-zA-Z0-9})\]])\$(?=\d)', '', content)
        content = re.sub(r'(?<=\d)\$(?=[a-zA-Z{])', '', content)
        content = re.sub(r'(?<=[a-zA-Z])\$(?=[(\[])', '', content)
        content = re.sub(r'(?<=[)\]])\$(?=[a-zA-Z\d])', '', content)
        content = re.sub(r'(?<=\^)\$(?=[a-zA-Z*])', '', content)
        content = re.sub(r'(?<=[a-zA-Z])\$\^', '^', content)

        content = re.sub(r'\$(?=[=\s,;:\]\)\}])', '', content)
        content = re.sub(r'(?<=[=\s,;:\[\(])\$', '', content)

        content = content.replace('$\\', '\\')
        content = content.replace('\\$ ', ' ')
        content = content.replace('\\$', '\\')

        content = re.sub(r'(?<!\\)\$(?=[a-zA-Z])', '', content)

        content = re.sub(r'^\$|\$$', '', content)

        content = re.sub(r'\s+', ' ', content)

        return content.strip()

    @staticmethod
    def _looks_like_latex(text: str) -> bool:
        if len(text) < 5:
            return False
        latex_indicators = [
            r'\\frac', r'\\sum', r'\\prod', r'\\int', r'\\sqrt',
            r'\\lim', r'\\sin', r'\\cos', r'\\tan', r'\\log',
            r'\\exp', r'\\ln', r'\\alpha', r'\\beta', r'\\gamma',
            r'\\delta', r'\\theta', r'\\lambda', r'\\pi', r'\\sigma',
            r'\\psi', r'\\phi', r'\\omega', r'\\partial', r'\\nabla',
            r'\\infty', r'\\cdot', r'\\times', r'\\pm', r'\\leq',
            r'\\geq', r'\\left', r'\\right', r'\\mathbf', r'\\mathrm',
            r'\\begin\{', r'\\end\{', r'\\hbar', r'\\quad',
        ]
        count = sum(1 for pattern in latex_indicators if pattern in text)
        return count >= 2 or (count >= 1 and '\\' in text and '{' in text)

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
