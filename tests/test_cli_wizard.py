"""Tests for cli_wizard extracted module."""
import pytest


class TestCliWizardImport:
    """Behavior: cli_wizard module loads correctly."""

    def test_import_module(self):
        import pdf_summarizer.cli_wizard
        assert hasattr(pdf_summarizer.cli_wizard, "_run_config_wizard")

    def test_cli_imports_wizard(self):
        from pdf_summarizer.cli import app
        from pdf_summarizer.cli_wizard import _run_config_wizard
        assert callable(_run_config_wizard)
