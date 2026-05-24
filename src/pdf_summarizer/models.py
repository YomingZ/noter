"""Pydantic data models for PDF Summarizer."""

import base64
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class AIProvider(str, Enum):
    """Supported AI providers."""
    OPENAI = "openai"
    CLAUDE = "claude"
    KIMI = "kimi"


class AIConfig(BaseModel):
    """AI provider configuration."""
    provider: AIProvider = AIProvider.OPENAI
    model: str = "gpt-4o"
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=100)


class HeadingLevel(int, Enum):
    """Heading level enumeration."""
    TITLE = 0      # 文档标题
    H1 = 1         # 章节标题
    H2 = 2         # 小节标题
    H3 = 3         # 子节标题
    BODY = 4       # 正文


class ContentBlock(BaseModel):
    """A block of content with metadata."""
    text: str
    block_type: str = "paragraph"  # paragraph, heading, list, code, table
    heading_level: HeadingLevel = HeadingLevel.BODY
    page_number: int = 0
    font_size: Optional[float] = None
    is_bold: bool = False
    char_count: int = 0

    def model_post_init(self, __context):
        if not self.char_count:
            self.char_count = len(self.text)


class Chapter(BaseModel):
    """A chapter/section in the document."""
    title: str
    level: HeadingLevel = HeadingLevel.H1
    content_blocks: list[ContentBlock] = []
    page_start: int = 0
    page_end: int = 0

    @property
    def text(self) -> str:
        """Get full text of the chapter."""
        return "\n\n".join(
            block.text for block in self.content_blocks
            if block.text.strip()
        )

    @property
    def char_count(self) -> int:
        """Get total character count."""
        return sum(block.char_count for block in self.content_blocks)


class PDFPage(BaseModel):
    """Single PDF page content."""
    page_number: int
    text: str
    char_count: int = 0
    content_blocks: list[ContentBlock] = []
    images_base64: list[str] = []
    has_table: bool = False

    def model_post_init(self, __context):
        if not self.char_count:
            self.char_count = len(self.text)


class PDFDocument(BaseModel):
    """PDF document model."""
    file_path: Path
    file_name: str
    total_pages: int
    pages: list[PDFPage] = []
    chapters: list[Chapter] = []
    total_chars: int = 0
    is_scanned: bool = False

    def model_post_init(self, __context):
        if not self.total_chars:
            self.total_chars = sum(p.char_count for p in self.pages)

    def get_full_text(self) -> str:
        """Get all text from all pages."""
        if self.chapters:
            parts = []
            for ch in self.chapters:
                parts.append(f"## {ch.title}\n\n{ch.text}")
                for block in ch.content_blocks:
                    if block.block_type == "table":
                        parts.append(f"\n[表格]\n{block.text}\n")
            return "\n\n".join(parts)
        parts = []
        for p in self.pages:
            page_header = f"--- 第 {p.page_number} 页 ---"
            page_text = p.text
            for block in p.content_blocks:
                if block.block_type == "table" and block.text not in page_text:
                    page_text += f"\n\n[表格]\n{block.text}"
            parts.append(f"{page_header}\n{page_text}")
        return "\n\n".join(parts)

    def get_chapters_text(self) -> list[dict]:
        """Get chapters as list of dicts for AI processing."""
        return [
            {"title": ch.title, "content": ch.text, "level": ch.level.value}
            for ch in self.chapters
        ]

    def has_images(self) -> bool:
        """Check if any page has extracted images."""
        return any(p.images_base64 for p in self.pages)


class ContentPart(BaseModel):
    """A part of multimodal content (text or image) for AI requests."""
    type: str = "text"
    text: Optional[str] = None
    image_base64: Optional[str] = None

    def to_openai_format(self) -> dict:
        if self.type == "image":
            return {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{self.image_base64}"
                }
            }
        return {"type": "text", "text": self.text or ""}

    def to_claude_format(self) -> dict:
        if self.type == "image":
            return {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": self.image_base64 or "",
                }
            }
        return {"type": "text", "text": self.text or ""}


class SummarySection(BaseModel):
    """A section in the summary."""
    title: str
    content: str
    level: int = 1  # Heading level (1-6)


class SummaryOutput(BaseModel):
    """Structured summary output."""
    source_file: str
    core_concepts: list[str] = []
    sections: list[SummarySection] = []
    key_points: list[str] = []
    review_tips: list[str] = []
    raw_response: Optional[str] = None
    metadata: dict = {}  # Additional metadata for document generation


class ProcessResult(BaseModel):
    """Result of processing a single PDF."""
    input_file: Path
    output_file: Optional[Path] = None
    success: bool = True
    skipped: bool = False
    error_message: Optional[str] = None
    pages_processed: int = 0
    tokens_used: int = 0


class BatchResult(BaseModel):
    """Result of batch processing."""
    total_files: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    results: list[ProcessResult] = []

    def add_result(self, result: ProcessResult):
        """Add a processing result."""
        self.results.append(result)
        self.total_files += 1
        if result.skipped:
            self.skipped += 1
        elif result.success:
            self.successful += 1
        else:
            self.failed += 1
