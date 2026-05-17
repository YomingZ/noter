"""Tests for ObsidianNoteGenerator."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from pdf_summarizer.obsidian_generator import ObsidianNoteGenerator
from pdf_summarizer.models import PDFDocument, PDFPage, ProcessResult


@pytest.fixture
def mock_ai_generate():
    return Mock(return_value="# Generated Note\n\nContent here")


@pytest.fixture
def sample_document():
    return PDFDocument(
        file_path=Path("Lecture1.pdf"),
        file_name="Lecture1.pdf",
        total_pages=5,
        pages=[PDFPage(page_number=i, text=f"Page {i} content") for i in range(1, 6)],
    )


class TestObsidianNoteGenerator:
    def test_generate_calls_ai_and_writes_file(
        self, mock_ai_generate, sample_document, tmp_path
    ):
        template_path = tmp_path / "template.md"
        template_path.write_text("# {title}\n\n{content}", encoding="utf-8")

        vault_root = tmp_path / "vault"
        vault_root.mkdir()
        course_dir = vault_root / "collegenote" / "math" / "calculus"
        course_dir.mkdir(parents=True)

        gen = ObsidianNoteGenerator(ai_generate_fn=mock_ai_generate)

        with patch("pdf_summarizer.obsidian_generator.VaultIndexer") as MockIndexer:
            mock_indexer = MockIndexer.return_value
            mock_indexer.resolve_course_path.return_value = course_dir

            result = gen.generate(
                document=sample_document,
                template_path=template_path,
                course_name="微积分",
                vault_root=vault_root,
                output_name="Lecture1",
            )

        assert isinstance(result, ProcessResult)
        assert result.success is True
        assert result.output_file.name == "Lecture1.md"
        assert result.output_file.exists()

        content = result.output_file.read_text(encoding="utf-8")
        assert "Generated Note" in content or "Content here" in content

    def test_missing_template_raises(self, mock_ai_generate, sample_document, tmp_path):
        gen = ObsidianNoteGenerator(ai_generate_fn=mock_ai_generate)

        with pytest.raises(FileNotFoundError, match="模板文件不存在"):
            gen.generate(
                document=sample_document,
                template_path=tmp_path / "nonexistent.md",
                course_name="test",
                vault_root=tmp_path,
            )

    def test_invalid_vault_raises(self, mock_ai_generate, sample_document, tmp_path):
        template_path = tmp_path / "template.md"
        template_path.write_text("# Template", encoding="utf-8")

        gen = ObsidianNoteGenerator(ai_generate_fn=mock_ai_generate)

        with pytest.raises(Exception, match="Vault"):
            gen.generate(
                document=sample_document,
                template_path=template_path,
                course_name="test",
                vault_root=tmp_path / "no_such_vault",
            )

    def test_empty_ai_response_retries(self, sample_document, tmp_path):
        ai_mock = Mock(side_effect=["", "# Valid"])
        template_path = tmp_path / "template.md"
        template_path.write_text("# T", encoding="utf-8")

        vault_root = tmp_path / "vault"
        vault_root.mkdir()
        course_dir = vault_root / "course"
        course_dir.mkdir()

        gen = ObsidianNoteGenerator(ai_generate_fn=ai_mock)

        with patch("pdf_summarizer.obsidian_generator.VaultIndexer") as MockIndexer:
            MockIndexer.return_value.resolve_course_path.return_value = course_dir
            result = gen.generate(
                document=sample_document,
                template_path=template_path,
                course_name="c",
                vault_root=vault_root,
            )

        assert result.success is True

    def test_persistent_empty_response_raises(self, sample_document, tmp_path):
        ai_mock = Mock(return_value="")
        template_path = tmp_path / "template.md"
        template_path.write_text("# T", encoding="utf-8")

        vault_root = tmp_path / "vault"
        vault_root.mkdir()
        course_dir = vault_root / "course"
        course_dir.mkdir()

        gen = ObsidianNoteGenerator(ai_generate_fn=ai_mock)

        with patch("pdf_summarizer.obsidian_generator.VaultIndexer") as MockIndexer:
            MockIndexer.return_value.resolve_course_path.return_value = course_dir
            with pytest.raises(ValueError, match="内容为空"):
                gen.generate(
                    document=sample_document,
                    template_path=template_path,
                    course_name="c",
                    vault_root=vault_root,
                )

    def test_template_cache_lru_eviction(self, mock_ai_generate, sample_document, tmp_path):
        template_path = tmp_path / "template.md"
        template_path.write_text("# Template", encoding="utf-8")

        gen = ObsidianNoteGenerator(
            ai_generate_fn=mock_ai_generate, max_content_tokens=10
        )
        gen._template_cache  # trigger init

        for i in range(15):
            t = tmp_path / f"t{i}.md"
            t.write_text(f"# Template {i}", encoding="utf-8")
            gen._load_template(t)

        assert len(gen._template_cache) <= 10

    @staticmethod
    def _extract_template_structure_keeps_structure():
        input_text = """# Title

## Section

| Col1 | Col2 |
|------|------|

- Item 1
- Item 2

Long paragraph that should be stripped.

> Blockquote

$$ formula $$

```code block```
"""
        from pdf_summarizer.obsidian_generator import ObsidianNoteGenerator
        result = ObsidianNoteGenerator._extract_template_structure(input_text)

        assert "# Title" in result
        assert "## Section" in result
        assert "| Col1 |" in result
        assert "- Item 1" in result
        assert "> Blockquote" in result
        assert "$$ formula $$" in result
        assert "Long paragraph that should be stripped" not in result
