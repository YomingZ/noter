"""Tests for LaTeX normalization in Obsidian note generation."""

import pytest

from pdf_summarizer.obsidian_generator import ObsidianNoteGenerator


normalize = ObsidianNoteGenerator._normalize_dollar_blocks


class TestNormalizeDollarBlocks:
    """Behavior: _normalize_dollar_blocks fixes malformed $$ delimiters."""

    def test_standalone_unchanged(self):
        text = "$$\nE = mc^2\n$$"
        assert normalize(text) == text

    def test_inline_split(self):
        text = "x = $$E = mc^2$$ is famous"
        result = normalize(text)
        assert "$$" in result
        assert "E = mc^2" in result

    def test_open_on_same_line(self):
        text = "$$\nE = mc^2\n$$"
        assert normalize(text) == text

    def test_no_dollars(self):
        text = "plain text"
        assert normalize(text) == text

    def test_mixed_case(self):
        text = "a\n$$\nb\n$$c$$\nd\n$$"
        result = normalize(text)
        assert "$$" in result
        assert result.count("$$") % 2 == 0

    def test_double_at_start(self):
        text = "$$\\psi(x) = A e^{ikx}$$"
        result = normalize(text)
        assert "$$" in result
        assert "\\psi" in result or "\\\\psi" in result

    def test_fix_latex_for_obsidian_preserves_hell(self):
        text = "\\hat{H}\\Psi = E\\Psi"
        result = ObsidianNoteGenerator._fix_latex_for_obsidian(text)
        assert result is not None
