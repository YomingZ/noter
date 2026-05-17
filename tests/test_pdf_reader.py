"""Tests for PDF reader module."""

import pytest
from pathlib import Path

from pdf_summarizer.pdf_reader import PDFReader
from pdf_summarizer.models import PDFDocument


class TestPDFReader:
    """Test cases for PDFReader."""

    def test_reader_initialization(self):
        """Test PDFReader initializes with default values."""
        reader = PDFReader()
        assert reader.max_pages == 0
        assert reader.min_page_text == 50

    def test_reader_custom_values(self):
        """Test PDFReader with custom values."""
        reader = PDFReader(max_pages=10, min_page_text=100)
        assert reader.max_pages == 10
        assert reader.min_page_text == 100

    def test_read_nonexistent_file(self):
        """Test reading a nonexistent file raises error."""
        reader = PDFReader()
        with pytest.raises(FileNotFoundError):
            reader.read(Path("nonexistent.pdf"))

    def test_read_non_pdf_file(self, tmp_path):
        """Test reading a non-PDF file raises error."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Hello World")

        reader = PDFReader()
        with pytest.raises(ValueError, match="Not a PDF file"):
            reader.read(txt_file)


# Fixtures for integration tests
@pytest.fixture
def sample_pdf_path():
    """Path to a sample PDF file for testing."""
    # Add a sample PDF to tests/fixtures/ for integration testing
    return None
