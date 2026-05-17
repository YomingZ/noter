"""Tests for SummaryParser."""

import pytest

from pdf_summarizer.summary_parser import SummaryParser
from pdf_summarizer.models import SummaryOutput, SummarySection


class TestSummaryParser:
    def test_parse_markdown_sections(self):
        parser = SummaryParser()
        text = """### Section 1
Content for section 1.

### Section 2
Content for section 2."""

        result = parser.parse("test.pdf", text)

        assert len(result.sections) == 2
        assert result.sections[0].title == "Section 1"
        assert result.sections[0].content.strip() == "Content for section 1."
        assert result.sections[1].title == "Section 2"

    def test_parse_chinese_markers(self):
        parser = SummaryParser()
        text = """【定义】这是定义内容

【定理】这是定理内容

【注意】注意事项"""

        result = parser.parse("test.pdf", text)

        assert len(result.sections) == 3
        section_titles = [s.title for s in result.sections]
        assert "定义" in section_titles
        assert "定理" in section_titles
        assert "注意" in section_titles

    def test_extract_inline_markers(self):
        parser = SummaryParser()
        text = """【定义】函数是映射。

【定理】中值定理的内容。

【注意】连续性条件。"""

        result = parser.parse("test.pdf", text)

        assert len(result.sections) == 3
        titles = [s.title for s in result.sections]
        assert any("定义" in t for t in titles)
        assert any("定理" in t for t in titles)
        assert any("注意" in t for t in titles)

    def test_extract_list_items_numbered(self):
        items = SummaryParser._extract_list_items(
            "1. First item\n2. Second item\n3. Third item"
        )
        assert len(items) == 3
        assert items[0] == "First item"
        assert items[2] == "Third item"

    def test_extract_list_items_bulleted(self):
        items = SummaryParser._extract_list_items(
            "- First item\n- Second item\n- Third item"
        )
        assert len(items) == 3
        assert items[0] == "First item"

    def test_extract_list_items_mixed(self):
        items = SummaryParser._extract_list_items(
            "- Bullet\n2. Numbered\n* Asterisk"
        )
        assert len(items) == 3

    def test_extract_list_items_empty(self):
        assert SummaryParser._extract_list_items("") == []
        assert SummaryParser._extract_list_items("no list here") == []

    def test_extract_sections_hierarchical(self):
        sections = SummaryParser._extract_sections(
            "# Title\n\n## Sub\ncontent\n### Deep\nmore"
        )
        assert len(sections) >= 2
        assert sections[0].title == "Title"

    def test_raw_response_preserved(self):
        parser = SummaryParser()
        raw = "Raw AI response here"
        result = parser.parse("file.pdf", raw)
        assert result.raw_response == raw
        assert result.source_file == "file.pdf"

    def test_empty_text(self):
        parser = SummaryParser()
        result = parser.parse("empty.pdf", "")
        assert len(result.sections) == 0
