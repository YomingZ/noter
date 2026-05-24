"""PDF text extraction module with advanced features.

Supports:
- Searchable text extraction with layout preservation
- OCR fallback for scanned/image-based PDFs
- Table extraction and Markdown conversion
- LaTeX formula enhancement (Unicode → LaTeX)
- Page image extraction for multimodal AI
"""

import io
import base64
import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pdfplumber

from pdf_summarizer.models import (
    PDFDocument,
    PDFPage,
    ContentBlock,
    Chapter,
    HeadingLevel,
)
from pdf_summarizer.config import config

logger = logging.getLogger(__name__)

try:
    from pdf2image import convert_from_path as _pdf2image_convert
    from PIL import Image
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


@dataclass
class FontInfo:
    """Font information for text analysis."""
    size: float
    is_bold: bool = False
    count: int = 1


class PDFExtractor:
    """
    Advanced PDF text extractor with structure preservation.

    Features:
    - Extract searchable text layer
    - Handle multi-column layouts
    - Detect heading hierarchy by font size
    - Remove headers/footers/page numbers
    - Preserve chapter structure
    """

    # Common header/footer patterns
    HEADER_FOOTER_PATTERNS = [
        r'^\s*\d+\s*$',                    # 单独的页码
        r'^\s*第\s*\d+\s*页\s*$',          # 第 X 页
        r'^\s*Page\s*\d+\s*$',             # Page X
        r'^\s*-\s*\d+\s*-\s*$',            # - X -
        r'^\s*\d+\s*/\s*\d+\s*$',          # X/Y
    ]

    # Title indicators in Chinese
    TITLE_PATTERNS = [
        r'^第[一二三四五六七八九十\d]+[章节部篇]',
        r'^[一二三四五六七八九十]+[、.]',
        r'^\d+[\.、]\s*\S+',
        r'^[A-Z][A-Z\s]+$',                # 全大写英文标题
    ]

    def __init__(
        self,
        max_pages: int = 0,
        min_page_text: int = 50,
        detect_structure: bool = True,
        remove_headers_footers: bool = True,
        font_size_threshold: float = 1.2,
        enable_ocr: bool = True,
        extract_tables: bool = True,
        enhance_formulas: bool = True,
        extract_images: bool = False,
        ocr_languages: str = 'chi_sim+eng',
        min_text_threshold: int = 100,
    ):
        self.max_pages = max_pages or config.settings.max_pages
        self.min_page_text = min_page_text or config.settings.min_page_text
        self.detect_structure = detect_structure
        self.remove_headers_footers = remove_headers_footers
        self.font_size_threshold = font_size_threshold
        self.enable_ocr = enable_ocr
        self.extract_tables = extract_tables
        self.enhance_formulas = enhance_formulas
        self.extract_images = extract_images
        self.ocr_languages = ocr_languages
        self.min_text_threshold = min_text_threshold

        # Analyzed font statistics
        self._body_font_size: Optional[float] = None
        self._font_sizes: dict[float, int] = defaultdict(int)

        self._ocr_warning_logged = False

    def extract(self, pdf_path: Path) -> list[Chapter]:
        """
        Extract PDF and return structured chapters.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            List of Chapter objects with hierarchical content
        """
        document = self.read(pdf_path)
        return document.chapters if document.chapters else self._create_default_chapter(document)

    def read(self, file_path: Path) -> PDFDocument:
        """Read a PDF file and extract text with structure.

        Automatically detects scanned PDFs and falls back to OCR.
        Extracts tables, enhances formulas, and optionally extracts images.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        if not file_path.suffix.lower() == ".pdf":
            raise ValueError(f"Not a PDF file: {file_path}")

        logger.info(f"Reading PDF: {file_path}")

        pages: list[PDFPage] = []
        all_blocks: list[ContentBlock] = []
        total_pages_in_file = 0
        is_scanned = False

        with pdfplumber.open(file_path) as pdf:
            total_pages_in_file = len(pdf.pages)
            pages_to_process = (
                min(self.max_pages, total_pages_in_file)
                if self.max_pages > 0
                else total_pages_in_file
            )

            if self.detect_structure:
                self._analyze_fonts(pdf.pages[:pages_to_process])

            for i, page in enumerate(pdf.pages[:pages_to_process]):
                page_number = i + 1
                page_blocks = self._extract_page_blocks(page, page_number)

                if page_blocks:
                    page_text = "\n\n".join(b.text for b in page_blocks if b.text.strip())

                    if len(page_text) >= self.min_page_text:
                        if self.enhance_formulas:
                            page_text = self._enhance_formulas(page_text)

                        pages.append(PDFPage(
                            page_number=page_number,
                            text=page_text,
                            content_blocks=page_blocks,
                        ))
                        all_blocks.extend(page_blocks)
                        logger.debug(f"Page {page_number}: {len(page_text)} chars")
                    else:
                        logger.debug(
                            f"Page {page_number} has only {len(page_text)} chars"
                        )

        total_chars = sum(len(p.text) for p in pages)
        if total_chars < self.min_text_threshold and self.enable_ocr:
            logger.info(
                f"Only {total_chars} chars extracted — PDF may be scanned. "
                f"Trying OCR..."
            )
            ocr_pages = self._ocr_pages(file_path, total_pages_in_file)
            if ocr_pages:
                pages = ocr_pages
                is_scanned = True
                all_blocks = []
                for p in pages:
                    all_blocks.extend(p.content_blocks)
                logger.info(f"OCR extracted {len(pages)} pages successfully")

        if not is_scanned and self.extract_tables:
            pages = self._extract_tables_from_pages(file_path, pages)
            all_blocks = []
            for p in pages:
                all_blocks.extend(p.content_blocks)

        if self.extract_images and PDF2IMAGE_AVAILABLE:
            pages = self._extract_page_images(file_path, pages)

        chapters = self._build_chapters(all_blocks) if self.detect_structure else []

        document = PDFDocument(
            file_path=file_path,
            file_name=file_path.name,
            total_pages=total_pages_in_file,
            pages=pages,
            chapters=chapters,
            is_scanned=is_scanned,
        )

        logger.info(
            f"Extracted {len(pages)} pages, {document.total_chars} chars, "
            f"{len(chapters)} chapters"
            f"{', scanned PDF (OCR)' if is_scanned else ''}"
        )

        return document

    def _analyze_fonts(self, pages) -> None:
        """Analyze font sizes across pages to determine body text size."""
        font_counts: dict[float, int] = defaultdict(int)

        for page in pages:
            chars = page.chars
            for char in chars:
                if 'size' in char:
                    # Round to nearest 0.5 for grouping
                    size = round(char['size'] * 2) / 2
                    font_counts[size] += 1

        if font_counts:
            # Body text is usually the most common font size
            self._body_font_size = max(font_counts, key=font_counts.get)
            self._font_sizes = dict(font_counts)
            logger.debug(f"Detected body font size: {self._body_font_size}")

    def _extract_page_blocks(self, page, page_number: int) -> list[ContentBlock]:
        """Extract content blocks from a single page."""
        blocks: list[ContentBlock] = []

        # Extract text with layout preservation
        text = page.extract_text(layout=True) or ""
        if not text.strip():
            return blocks

        # Get words with font information
        words = page.extract_words(
            extra_attrs=['fontname', 'size'],
            keep_blank_chars=True,
        )

        # Group words into lines by vertical position
        lines = self._group_words_to_lines(words)

        # Filter out headers and footers
        if self.remove_headers_footers:
            lines = self._filter_headers_footers(lines, page)

        # Convert lines to content blocks with heading detection
        current_block_lines: list[dict] = []
        current_block_type = "paragraph"

        for line in lines:
            line_type = self._detect_line_type(line)

            if line_type != current_block_type and current_block_lines:
                # Save current block
                block = self._create_block(current_block_lines, page_number)
                if block:
                    blocks.append(block)
                current_block_lines = []

            current_block_lines.append(line)
            current_block_type = line_type

        # Don't forget the last block
        if current_block_lines:
            block = self._create_block(current_block_lines, page_number)
            if block:
                blocks.append(block)

        return blocks

    def _group_words_to_lines(self, words: list[dict]) -> list[dict]:
        """Group words into lines based on vertical position."""
        if not words:
            return []

        # Sort by top position, then by left position
        sorted_words = sorted(words, key=lambda w: (round(w.get('top', 0)), w.get('x0', 0)))

        lines: list[dict] = []
        current_line: list[dict] = []
        current_top = None
        line_tolerance = 3  # pixels

        for word in sorted_words:
            word_top = round(word.get('top', 0))

            if current_top is None:
                current_top = word_top

            if abs(word_top - current_top) <= line_tolerance:
                current_line.append(word)
            else:
                # Start new line
                if current_line:
                    lines.append(self._merge_line_words(current_line))
                current_line = [word]
                current_top = word_top

        if current_line:
            lines.append(self._merge_line_words(current_line))

        return lines

    def _merge_line_words(self, words: list[dict]) -> dict:
        """Merge words in a line into a single line dict."""
        if not words:
            return {}

        text = " ".join(w.get('text', '') for w in words)
        sizes = [w.get('size', 12) for w in words if w.get('size')]
        avg_size = sum(sizes) / len(sizes) if sizes else 12

        # Check if any word is bold
        is_bold = any(
            'bold' in str(w.get('fontname', '')).lower()
            for w in words
        )

        return {
            'text': text,
            'size': avg_size,
            'is_bold': is_bold,
            'top': min(w.get('top', 0) for w in words),
        }

    def _filter_headers_footers(self, lines: list[dict], page) -> list[dict]:
        """Remove header and footer lines."""
        if not lines:
            return lines

        page_height = page.height
        header_threshold = page_height * 0.1  # Top 10%
        footer_threshold = page_height * 0.9  # Bottom 10%

        filtered = []
        for line in lines:
            text = line.get('text', '').strip()
            top = line.get('top', 0)

            # Check if in header/footer zone
            if top < header_threshold or top > footer_threshold:
                # Check if it matches header/footer patterns
                if any(re.match(p, text) for p in self.HEADER_FOOTER_PATTERNS):
                    continue

            # Also filter by content patterns
            if any(re.match(p, text) for p in self.HEADER_FOOTER_PATTERNS):
                if len(text) < 10:  # Only short matches
                    continue

            filtered.append(line)

        return filtered

    def _detect_line_type(self, line: dict) -> str:
        """Detect the type of a line (heading, paragraph, list)."""
        text = line.get('text', '').strip()
        size = line.get('size', 12)
        is_bold = line.get('is_bold', False)

        if not text:
            return "paragraph"

        # Check for list items
        if re.match(r'^[-•*·]\s+', text) or re.match(r'^\d+[\.、\)]\s+', text):
            return "list"

        # Check for heading based on font size
        if self._body_font_size:
            size_ratio = size / self._body_font_size

            if size_ratio >= self.font_size_threshold * 2:
                return "title"
            elif size_ratio >= self.font_size_threshold * 1.5:
                return "heading1"
            elif size_ratio >= self.font_size_threshold:
                return "heading2"
            elif size_ratio >= 1.1:
                return "heading3"

        # Check for bold as heading indicator
        if is_bold and len(text) < 100:
            return "heading2"

        # Check for title patterns
        if any(re.match(p, text) for p in self.TITLE_PATTERNS):
            return "heading1"

        return "paragraph"

    def _create_block(self, lines: list[dict], page_number: int) -> Optional[ContentBlock]:
        """Create a content block from lines."""
        if not lines:
            return None

        text = "\n".join(line.get('text', '') for line in lines).strip()
        if not text:
            return None

        # Determine block type and heading level
        line_types = [self._detect_line_type(line) for line in lines]
        primary_type = max(set(line_types), key=line_types.count)

        if primary_type == "title":
            block_type = "heading"
            heading_level = HeadingLevel.TITLE
        elif primary_type == "heading1":
            block_type = "heading"
            heading_level = HeadingLevel.H1
        elif primary_type == "heading2":
            block_type = "heading"
            heading_level = HeadingLevel.H2
        elif primary_type == "heading3":
            block_type = "heading"
            heading_level = HeadingLevel.H3
        elif primary_type == "list":
            block_type = "list"
            heading_level = HeadingLevel.BODY
        else:
            block_type = "paragraph"
            heading_level = HeadingLevel.BODY

        avg_size = sum(line.get('size', 12) for line in lines) / len(lines)
        is_bold = any(line.get('is_bold', False) for line in lines)

        return ContentBlock(
            text=text,
            block_type=block_type,
            heading_level=heading_level,
            page_number=page_number,
            font_size=avg_size,
            is_bold=is_bold,
        )

    def _build_chapters(self, blocks: list[ContentBlock]) -> list[Chapter]:
        """Build chapters from content blocks based on headings."""
        chapters: list[Chapter] = []
        current_chapter: Optional[Chapter] = None

        for block in blocks:
            if block.block_type == "heading":
                # Save previous chapter
                if current_chapter:
                    chapters.append(current_chapter)

                # Start new chapter
                level = HeadingLevel.H1
                if block.heading_level == HeadingLevel.TITLE:
                    level = HeadingLevel.TITLE
                elif block.heading_level == HeadingLevel.H2:
                    level = HeadingLevel.H2
                elif block.heading_level == HeadingLevel.H3:
                    level = HeadingLevel.H3

                current_chapter = Chapter(
                    title=block.text,
                    level=level,
                    content_blocks=[],
                    page_start=block.page_number,
                )
            elif current_chapter:
                current_chapter.content_blocks.append(block)
                current_chapter.page_end = block.page_number

        # Don't forget the last chapter
        if current_chapter:
            chapters.append(current_chapter)

        return chapters

    def _create_default_chapter(self, document: PDFDocument) -> list[Chapter]:
        """Create a default chapter when no structure is detected."""
        all_blocks = []
        for page in document.pages:
            all_blocks.extend(page.content_blocks)

        return [Chapter(
            title=document.file_name,
            level=HeadingLevel.TITLE,
            content_blocks=all_blocks,
            page_start=1,
            page_end=document.total_pages,
        )]

    def _ocr_pages(self, pdf_path: Path, total_pages: int) -> list[PDFPage]:
        """Fallback OCR extraction for scanned/image-based PDFs.

        Converts PDF pages to images, then uses Tesseract OCR to extract text.
        Falls back gracefully if OCR dependencies are unavailable.
        """
        if not TESSERACT_AVAILABLE or not PDF2IMAGE_AVAILABLE:
            if not self._ocr_warning_logged:
                logger.warning(
                    "OCR not available. Install: pip install pytesseract pdf2image Pillow\n"
                    "Also install Tesseract-OCR: https://github.com/UB-Mannheim/tesseract/wiki"
                )
                self._ocr_warning_logged = True
            return []

        try:
            images = _pdf2image_convert(
                pdf_path,
                first_page=1,
                last_page=total_pages,
                dpi=300,
            )
        except Exception as e:
            logger.error(f"Failed to convert PDF to images: {e}")
            return []

        ocr_pages: list[PDFPage] = []
        for i, img in enumerate(images):
            page_number = i + 1
            try:
                text = pytesseract.image_to_string(
                    img,
                    lang=self.ocr_languages,
                    config='--psm 6'
                )
                if text.strip():
                    if self.enhance_formulas:
                        text = self._enhance_formulas(text)
                    page = PDFPage(
                        page_number=page_number,
                        text=text,
                        content_blocks=[ContentBlock(
                            text=text,
                            block_type="paragraph",
                            page_number=page_number,
                        )],
                    )
                    ocr_pages.append(page)
                    logger.debug(f"OCR page {page_number}: {len(text)} chars")
                else:
                    logger.debug(f"OCR page {page_number}: no text found")
            except Exception as e:
                logger.error(f"OCR failed on page {page_number}: {e}")

        return ocr_pages

    def _table_to_markdown(self, table_data: list[list]) -> str:
        """Convert pdfplumber table data to Markdown table format."""
        if not table_data or len(table_data) < 1:
            return ""

        rows = []
        for row in table_data:
            clean_row = [
                (cell or "").strip().replace("\n", " ")
                for cell in row
            ]
            rows.append(clean_row)

        col_count = max(len(r) for r in rows) if rows else 0
        if col_count == 0:
            return ""

        for r in rows:
            while len(r) < col_count:
                r.append("")

        md_lines = []
        md_lines.append("| " + " | ".join(rows[0]) + " |")
        md_lines.append("| " + " | ".join(["---"] * col_count) + " |")
        for row in rows[1:]:
            md_lines.append("| " + " | ".join(row) + " |")

        return "\n".join(md_lines)

    def _extract_tables_from_pages(
        self, pdf_path: Path, pages: list[PDFPage]
    ) -> list[PDFPage]:
        """Extract tables from PDF pages and add as structured ContentBlocks."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_number = page.page_number
                    page_index = page_number - 1

                    if page_index >= len(pages):
                        continue

                    existing_page = pages[page_index]
                    tables = page.extract_tables()

                    for table_data in tables:
                        if table_data and len(table_data) >= 2:
                            md_table = self._table_to_markdown(table_data)
                            if md_table:
                                table_block = ContentBlock(
                                    text=md_table,
                                    block_type="table",
                                    page_number=page_number,
                                )
                                existing_page.content_blocks.append(table_block)
                                existing_page.has_table = True

                                existing_page.text += f"\n\n[表格]\n{md_table}"
        except Exception as e:
            logger.warning(f"Table extraction failed for {pdf_path}: {e}")

        return pages

    def _enhance_formulas(self, text: str) -> str:
        """Convert Unicode math symbols to LaTeX commands.

        Improves AI understanding by normalizing mathematical notation.
        """
        replacements = [
            ('α', '\\alpha'), ('β', '\\beta'), ('γ', '\\gamma'),
            ('δ', '\\delta'), ('ε', '\\varepsilon'), ('θ', '\\theta'),
            ('λ', '\\lambda'), ('μ', '\\mu'), ('π', '\\pi'),
            ('σ', '\\sigma'), ('τ', '\\tau'), ('φ', '\\phi'),
            ('ψ', '\\psi'), ('ω', '\\omega'), ('Γ', '\\Gamma'),
            ('Δ', '\\Delta'), ('Θ', '\\Theta'), ('Λ', '\\Lambda'),
            ('Π', '\\Pi'), ('Σ', '\\Sigma'), ('Φ', '\\Phi'),
            ('Ψ', '\\Psi'), ('Ω', '\\Omega'),
            ('∫', '\\int '), ('∬', '\\iint '), ('∭', '\\iiint '),
            ('∑', '\\sum '), ('∏', '\\prod '), ('∂', '\\partial '),
            ('∇', '\\nabla '), ('√', '\\sqrt '), ('∞', '\\infty '),
            ('→', '\\to '), ('⇒', '\\Rightarrow '), ('⇔', '\\Leftrightarrow '),
            ('≠', '\\neq '), ('≤', '\\leq '), ('≥', '\\geq '),
            ('±', '\\pm '), ('∓', '\\mp '), ('×', '\\times '),
            ('÷', '\\div '), ('≈', '\\approx '), ('≡', '\\equiv '),
            ('∈', '\\in '), ('∉', '\\notin '), ('⊂', '\\subset '),
            ('⊃', '\\supset '), ('∩', '\\cap '), ('∪', '\\cup '),
            ('∅', '\\emptyset '), ('∀', '\\forall '), ('∃', '\\exists '),
            ('ℏ', '\\hbar '), ('ħ', '\\hbar '),
            ('⊗', '\\otimes '), ('⊕', '\\oplus '),
            ('†', '\\dagger '), ('⟨', '\\langle '), ('⟩', '\\rangle '),
        ]

        for unicode_char, latex_cmd in replacements:
            text = text.replace(unicode_char, latex_cmd)

        text = re.sub(
            r'(?<![\\$])\b([a-zA-Z])(?=_\{|\^\{)',
            r'\\\1',
            text
        )

        return text

    def _extract_page_images(
        self, pdf_path: Path, pages: list[PDFPage]
    ) -> list[PDFPage]:
        """Extract each page as a base64-encoded PNG image.

        Images are stored in PDFPage.images_base64 for multimodal AI processing.
        """
        if not PDF2IMAGE_AVAILABLE:
            return pages

        try:
            images = _pdf2image_convert(
                pdf_path,
                first_page=1,
                last_page=len(pages),
                dpi=150,
            )
            for i, img in enumerate(images):
                if i < len(pages):
                    buf = io.BytesIO()
                    img.save(buf, format="PNG", optimize=True)
                    b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
                    pages[i].images_base64.append(b64_str)
                    logger.debug(
                        f"Page {pages[i].page_number}: image {len(b64_str)} bytes"
                    )
        except Exception as e:
            logger.warning(f"Image extraction failed for {pdf_path}: {e}")

        return pages

    def read_directory(
        self,
        directory: Path,
        recursive: bool = False,
    ) -> list[PDFDocument]:
        """Read all PDF files from a directory."""
        directory = Path(directory)
        if not directory.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")

        pattern = "**/*.pdf" if recursive else "*.pdf"
        pdf_files = sorted(directory.glob(pattern))

        if not pdf_files:
            logger.warning(f"No PDF files found in: {directory}")
            return []

        logger.info(f"Found {len(pdf_files)} PDF files in {directory}")

        documents: list[PDFDocument] = []
        for pdf_file in pdf_files:
            try:
                doc = self.read(pdf_file)
                documents.append(doc)
            except Exception as e:
                logger.error(f"Failed to read {pdf_file}: {e}")

        return documents


# Backward compatibility alias
PDFReader = PDFExtractor


def read_pdf(file_path: Path, **kwargs) -> PDFDocument:
    """Convenience function to read a PDF file."""
    extractor = PDFExtractor(**kwargs)
    return extractor.read(file_path)


def extract_chapters(pdf_path: Path, **kwargs) -> list[Chapter]:
    """Convenience function to extract chapters from PDF."""
    extractor = PDFExtractor(**kwargs)
    return extractor.extract(pdf_path)
