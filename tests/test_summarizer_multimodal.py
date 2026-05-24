"""Tests for summarizer multimodal integration."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from pdf_summarizer.summarizer import Summarizer
from pdf_summarizer.models import AIProvider, PDFDocument, PDFPage, Chapter, ContentPart


class TestMultimodalBuilding:
    """Behavior: _build_multimodal_parts constructs correct ContentPart list."""

    def test_text_only_when_no_images(self):
        summarizer = Summarizer(provider=AIProvider.OPENAI)
        summarizer._ai_client = MagicMock()
        summarizer._ai_client.supports_vision.return_value = True

        doc = PDFDocument(
            file_path=Path("test.pdf"),
            file_name="test.pdf",
            total_pages=1,
            pages=[PDFPage(page_number=1, text="course content")],
        )

        parts = summarizer._build_multimodal_parts(doc)
        assert len(parts) == 1
        assert parts[0].type == "text"

    def test_includes_images_when_available(self):
        summarizer = Summarizer(provider=AIProvider.OPENAI)
        summarizer._ai_client = MagicMock()
        summarizer._ai_client.supports_vision.return_value = True

        doc = PDFDocument(
            file_path=Path("test.pdf"),
            file_name="test.pdf",
            total_pages=1,
            pages=[PDFPage(
                page_number=1,
                text="course content",
                images_base64=["img1", "img2"],
            )],
        )

        parts = summarizer._build_multimodal_parts(doc)
        assert len(parts) == 3  # 1 text + 2 images
        assert parts[0].type == "text"
        assert parts[1].type == "image"
        assert parts[1].image_base64 == "img1"
        assert parts[2].type == "image"
        assert parts[2].image_base64 == "img2"

    def test_no_images_when_vision_not_supported(self):
        summarizer = Summarizer(provider=AIProvider.KIMI)
        summarizer._ai_client = MagicMock()
        summarizer._ai_client.supports_vision.return_value = False

        doc = PDFDocument(
            file_path=Path("test.pdf"),
            file_name="test.pdf",
            total_pages=1,
            pages=[PDFPage(
                page_number=1,
                text="course content",
                images_base64=["img1"],
            )],
        )

        parts = summarizer._build_multimodal_parts(doc)
        assert len(parts) == 1
        assert parts[0].type == "text"


class TestPDFDocumentMultimodalHelpers:
    """Behavior: PDFDocument.has_images and is_scanned work correctly."""

    def test_has_images_true(self):
        doc = PDFDocument(
            file_path=Path("test.pdf"),
            file_name="test.pdf",
            total_pages=1,
            pages=[PDFPage(page_number=1, text="t", images_base64=["img"])],
        )
        assert doc.has_images() is True

    def test_has_images_false(self):
        doc = PDFDocument(
            file_path=Path("test.pdf"),
            file_name="test.pdf",
            total_pages=1,
            pages=[PDFPage(page_number=1, text="t")],
        )
        assert doc.has_images() is False

    def test_is_scanned_default_false(self):
        doc = PDFDocument(
            file_path=Path("test.pdf"),
            file_name="test.pdf",
            total_pages=1,
            pages=[PDFPage(page_number=1, text="t")],
        )
        assert doc.is_scanned is False
