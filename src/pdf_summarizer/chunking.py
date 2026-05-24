"""Document chunking strategies for AI processing.

Splits large documents into chunks that fit within model token limits,
then merges partial summaries back into a complete result.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from pdf_summarizer.models import Chapter, PDFDocument, PDFPage

logger = logging.getLogger(__name__)

CHARS_PER_TOKEN = 1.5


class ChunkingStrategy(ABC):
    """Abstract base class for document chunking strategies."""

    def __init__(self, max_tokens: int = 6000):
        self.max_tokens = max_tokens
        self._max_chars = int(max_tokens * CHARS_PER_TOKEN)

    @abstractmethod
    def split(self, document: PDFDocument) -> list[str]:
        """Split document into text chunks for AI processing."""

    def merge(self, partial_summaries: list[str], ai_generate_fn=None) -> str:
        """Merge multiple partial summaries into one.

        Falls back to simple concatenation when no AI function is provided.
        Uses AI merge when available for coherent result.
        """
        if len(partial_summaries) == 1:
            return partial_summaries[0]

        if ai_generate_fn is None:
            return "\n\n---\n\n".join(
                f"### 部分 {i + 1}\n\n{s}"
                for i, s in enumerate(partial_summaries)
            )

        logger.info("Merging %d partial summaries...", len(partial_summaries))

        from pdf_summarizer.config import config
        prompts = config.load_prompts()
        system = prompts.get("system_prompt", "你是一位专业的教育内容分析师。")
        merge_prompt = prompts.get(
            "merge_prompt",
            "以下是课件多个部分的总结笔记，请将它们合并整理成一份完整的结构化笔记：\n\n{content}"
        )

        combined = "\n\n---\n\n".join(
            f"### 部分 {i + 1}\n\n{s}"
            for i, s in enumerate(partial_summaries)
        )

        return ai_generate_fn(
            system_prompt=system,
            user_prompt=merge_prompt.replace("{content}", combined),
        )

    def _summarize_chunk(self, content: str, ai_generate_fn) -> str:
        """Summarize a single chunk using the provided AI generate function."""
        from pdf_summarizer.config import config

        prompts = config.load_prompts()
        system = prompts.get("system_prompt", "你是一位专业的教育内容分析师。")
        chunk_prompt = prompts.get(
            "chunk_prompt",
            "请分析以下课件内容片段，提取重点知识并生成结构化笔记：\n\n{content}"
        )

        return ai_generate_fn(
            system_prompt=system,
            user_prompt=chunk_prompt.replace("{content}", content),
        )


class ChapterChunker(ChunkingStrategy):
    """Chunks document by chapter/section structure."""

    def split(self, document: PDFDocument) -> list[str]:
        if not document.chapters:
            return []

        chunks: list[str] = []
        current_chunk = ""

        for chapter in document.chapters:
            chapter_text = f"## {chapter.title}\n\n{chapter.text}"

            if len(current_chunk) + len(chapter_text) > self._max_chars:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = chapter_text
            else:
                current_chunk += "\n\n" + chapter_text

        if current_chunk:
            chunks.append(current_chunk)

        return chunks


class PageChunker(ChunkingStrategy):
    """Chunks document by pages (fallback when no chapter structure)."""

    def split(self, document: PDFDocument) -> list[str]:
        if not document.pages:
            return []

        chunks: list[str] = []
        current_chunk = ""

        for page in document.pages:
            page_text = f"--- 第 {page.page_number} 页 ---\n{page.text}"

            if len(current_chunk) + len(page_text) > self._max_chars:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = page_text
            else:
                current_chunk += "\n\n" + page_text

        if current_chunk:
            chunks.append(current_chunk)

        return chunks
