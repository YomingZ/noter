"""Tests for summarizer module."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from pdf_summarizer.summarizer import Summarizer
from pdf_summarizer.models import AIProvider, ProcessResult, PDFDocument, PDFPage


class TestSummarizer:
    """Test cases for Summarizer."""

    def test_summarizer_initialization(self):
        """Test Summarizer initializes correctly."""
        summarizer = Summarizer(provider=AIProvider.OPENAI)
        assert summarizer.provider == AIProvider.OPENAI

    def test_extract_list_items_numbered(self):
        """Test extracting numbered list items."""
        summarizer = Summarizer(provider=AIProvider.OPENAI)
        text = "1. First item\n2. Second item\n3. Third item"
        items = summarizer._extract_list_items(text)

        assert len(items) == 3
        assert items[0] == "First item"
        assert items[1] == "Second item"
        assert items[2] == "Third item"

    def test_extract_list_items_bulleted(self):
        """Test extracting bulleted list items."""
        summarizer = Summarizer(provider=AIProvider.OPENAI)
        text = "- First item\n- Second item\n- Third item"
        items = summarizer._extract_list_items(text)

        assert len(items) == 3
        assert items[0] == "First item"

    def test_extract_sections(self):
        """Test extracting sections from markdown text."""
        summarizer = Summarizer(provider=AIProvider.OPENAI)
        text = """### Section 1
Content for section 1.

### Section 2
Content for section 2."""

        sections = summarizer._extract_sections(text)

        assert len(sections) == 2
        assert sections[0].title == "Section 1"
        assert sections[1].title == "Section 2"


class TestProcessResult:
    """Test ProcessResult model."""

    def test_process_result_defaults(self):
        """Test ProcessResult default values."""
        result = ProcessResult(input_file=Path("test.pdf"))
        assert result.success is True
        assert result.error_message is None
        assert result.pages_processed == 0

    def test_process_result_failure(self):
        """Test ProcessResult failure state."""
        result = ProcessResult(
            input_file=Path("test.pdf"),
            success=False,
            error_message="Test error"
        )
        assert result.success is False
        assert result.error_message == "Test error"
