"""Tests for new PDF reader features: tables, formulas, OCR, images."""

import pytest
from pathlib import Path

from pdf_summarizer.pdf_reader import PDFExtractor
from pdf_summarizer.models import PDFDocument, PDFPage, ContentBlock, HeadingLevel


class TestFormulaEnhancement:
    """Behavior: _enhance_formulas converts Unicode math to LaTeX."""

    def test_greek_letters(self):
        extractor = PDFExtractor()
        result = extractor._enhance_formulas("α β γ π σ")
        assert "\\alpha" in result
        assert "\\beta" in result
        assert "\\gamma" in result
        assert "\\pi" in result
        assert "\\sigma" in result

    def test_integral_sum(self):
        extractor = PDFExtractor()
        result = extractor._enhance_formulas("∫ f(x) dx, ∑ x_i")
        assert "\\int " in result
        assert "\\sum " in result

    def test_relations(self):
        extractor = PDFExtractor()
        result = extractor._enhance_formulas("a ≠ b, c ≤ d, e ≥ f")
        assert "\\neq " in result
        assert "\\leq " in result
        assert "\\geq " in result

    def test_empty_string(self):
        extractor = PDFExtractor()
        assert extractor._enhance_formulas("") == ""

    def test_no_formulas(self):
        extractor = PDFExtractor()
        text = "纯中文文本，没有数学符号"
        assert extractor._enhance_formulas(text) == text


class TestTableToMarkdown:
    """Behavior: _table_to_markdown converts pdfplumber table to Markdown."""

    def test_simple_table(self):
        extractor = PDFExtractor()
        table = [["Name", "Value"], ["A", "1"], ["B", "2"]]
        result = extractor._table_to_markdown(table)

        assert "| Name | Value |" in result
        assert "| --- | --- |" in result
        assert "| A | 1 |" in result
        assert "| B | 2 |" in result

    def test_empty_table(self):
        extractor = PDFExtractor()
        assert extractor._table_to_markdown([]) == ""
        assert extractor._table_to_markdown(None) == ""

    def test_header_only_table(self):
        extractor = PDFExtractor()
        result = extractor._table_to_markdown([["only header"]])
        assert "only header" in result

    def test_table_with_empty_cells(self):
        extractor = PDFExtractor()
        table = [["A", "B", "C"], ["1", "", "3"]]
        result = extractor._table_to_markdown(table)
        assert "| 1 |  | 3 |" in result

    def test_irregular_row_lengths(self):
        extractor = PDFExtractor()
        table = [["A", "B"], ["1", "2", "3", "4"]]
        result = extractor._table_to_markdown(table)
        assert "| 1 | 2 | 3 | 4 |" in result


class TestImageExtraction:
    """Behavior: _extract_page_images handles pages with/without images."""

    def test_no_images_when_pdf2image_unavailable(self, monkeypatch):
        monkeypatch.setattr("pdf_summarizer.pdf_reader.PDF2IMAGE_AVAILABLE", False)
        extractor = PDFExtractor()
        pages = [PDFPage(page_number=1, text="test")]
        result = extractor._extract_page_images(Path("dummy.pdf"), pages)
        assert len(result[0].images_base64) == 0


class TestContentPart:
    """Behavior: ContentPart model works for OpenAI and Claude formats."""

    def test_text_part_openai(self):
        from pdf_summarizer.models import ContentPart
        part = ContentPart(type="text", text="hello")
        fmt = part.to_openai_format()
        assert fmt == {"type": "text", "text": "hello"}

    def test_text_part_claude(self):
        from pdf_summarizer.models import ContentPart
        part = ContentPart(type="text", text="hello")
        fmt = part.to_claude_format()
        assert fmt == {"type": "text", "text": "hello"}

    def test_image_part_openai(self):
        from pdf_summarizer.models import ContentPart
        part = ContentPart(type="image", image_base64="abc123")
        fmt = part.to_openai_format()
        assert fmt["type"] == "image_url"
        assert "abc123" in fmt["image_url"]["url"]

    def test_image_part_claude(self):
        from pdf_summarizer.models import ContentPart
        part = ContentPart(type="image", image_base64="abc123")
        fmt = part.to_claude_format()
        assert fmt["type"] == "image"
        assert fmt["source"]["data"] == "abc123"
