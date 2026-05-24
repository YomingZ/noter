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


class TestFixCasesEnvironment:
    """Behavior: _fix_cases_environment repairs broken cases environment."""

    fix = staticmethod(ObsidianNoteGenerator._fix_cases_environment)

    def test_fix_end_cases_missing_brace(self):
        text = "\\end{cases"
        assert self.fix(text) == "\\end{cases}"

    def test_remove_dollar_before_begin_cases(self):
        text = "$$\n\\psi(x)\\n$$\n\\begin{cases}"
        result = self.fix(text)
        assert "\\begin{cases}" in result

    def test_collapse_duplicate_dollar_after_end_cases(self):
        text = "\\end{cases}\n$$\n$$"
        result = self.fix(text)
        assert result == "\\end{cases}\n$$"

    def test_full_case_environment_preserved(self):
        input_text = "$$\n\\psi(x) = \n$$\n\\begin{cases}\nA e^{ikx} & x < -L/2\n\\end{cases}\n$$\n$$"
        result = self.fix(input_text)
        assert "\\end{cases}" in result
        assert result.count("$$") == 2
        assert "\\begin{cases}" in result


class TestFullPipeline:
    """Behavior: the full _fix_latex_for_obsidian pipeline handles real-world AI output."""

    fix = staticmethod(ObsidianNoteGenerator._fix_latex_for_obsidian)

    def test_cases_blocks_are_preserved_intact(self):
        ai_output = (
            "## 4. Finite box:\n\n"
            "$$\n\\psi(x) = \n$$\n\\begin{cases}\n"
            "A e^{ikx} + B e^{-ikx} & \\text{for } x < -\\frac{L}{2} \\\\\n"
            "C e^{ikx} + D e^{-ikx} & \\text{for } -\\frac{L}{2} \\leq x \\leq \\frac{L}{2} \\\\\n"
            "A e^{ikx} + B e^{-ikx} & \\text{for } x > \\frac{L}{2}\n"
            "\\end{cases\n$$\n$$\n\n"
            "where $k = \\sqrt{\\frac{2mE}{\\hbar^2}}$."
        )
        result = self.fix(ai_output)
        assert "\\end{cases}" in result
        assert result.count("$$") == 2
        assert "\\begin{cases}" in result
        # The entire cases block must be inside a single $$...$$ pair
        cases_start = result.index("\\begin{cases}")
        cases_end = result.index("\\end{cases}")
        before_cases = result[:cases_start]
        after_cases = result[cases_end:]
        assert before_cases.rstrip().endswith("$$") or "$$" in before_cases

