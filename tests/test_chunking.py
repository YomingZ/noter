"""Tests for chunking strategies."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from pdf_summarizer.chunking import (
    ChunkingStrategy,
    ChapterChunker,
    PageChunker,
)
from pdf_summarizer.models import PDFDocument, PDFPage, Chapter


class TestChapterChunker:
    def test_split_by_chapters(self):
        doc = PDFDocument(
            file_path=Path("test.pdf"),
            file_name="test.pdf",
            total_pages=10,
            chapters=[
                Chapter(title="Ch1", content="Content 1"),
                Chapter(title="Ch2", content="Content 2"),
            ],
        )
        chunker = ChapterChunker(max_tokens=100000)
        chunks = chunker.split(doc)

        assert len(chunks) >= 1
        assert "Ch1" in chunks[0]

    def test_merge_single_chunk(self):
        chunker = ChapterChunker()
        result = chunker.merge(["only one"])
        assert result == "only one"

    def test_merge_multiple_chunks_without_ai(self):
        chunker = ChapterChunker()
        result = chunker.merge(["part A", "part B"], ai_generate_fn=None)

        assert "部分 1" in result
        assert "part A" in result
        assert "部分 2" in result
        assert "part B" in result

    def test_split_empty_chapters(self):
        doc = PDFDocument(
            file_path=Path("test.pdf"),
            file_name="test.pdf",
            total_pages=5,
            chapters=[],
            pages=[PDFPage(page_number=1, text="page content")],
        )
        chunker = ChapterChunker()
        chunks = chunker.split(doc)
        assert chunks == []

    def test_split_groups_small_chapters(self):
        doc = PDFDocument(
            file_path=Path("test.pdf"),
            file_name="test.pdf",
            total_pages=3,
            chapters=[
                Chapter(title="A", content="x" * 10),
                Chapter(title="B", content="x" * 10),
                Chapter(title="C", content="x" * 10),
            ],
        )
        chunker = ChapterChunker(max_tokens=1)
        chunks = chunker.split(doc)

        assert len(chunks) >= 1
        assert all("##" in c for c in chunks)


class TestPageChunker:
    def test_split_by_pages(self):
        doc = PDFDocument(
            file_path=Path("test.pdf"),
            file_name="test.pdf",
            total_pages=3,
            pages=[
                PDFPage(page_number=1, text="Page 1"),
                PDFPage(page_number=2, text="Page 2"),
                PDFPage(page_number=3, text="Page 3"),
            ],
        )
        chunker = PageChunker(max_tokens=100000)
        chunks = chunker.split(doc)

        assert len(chunks) >= 1
        assert any("第 1 页" in c for c in chunks)

    def test_merge_single(self):
        chunker = PageChunker()
        assert chunker.merge(["solo"]) == "solo"

    def test_split_empty_pages(self):
        doc = PDFDocument(
            file_path=Path("test.pdf"),
            file_name="test.pdf",
            total_pages=0,
            pages=[],
        )
        chunker = PageChunker()
        assert chunker.split(doc) == []


class TestChunkingStrategyABC:
    def test_cannot_instantiate_abc(self):
        with pytest.raises(TypeError):
            ChunkingStrategy()

    def test_subclass_must_implement_split(self):
        with pytest.raises(TypeError, match="abstract method 'split'"):
            class BadChunker(ChunkingStrategy):
                def merge(self, partials, ai_fn=None):
                    return ""
            BadChunker()  # type: ignore[arg-type]
