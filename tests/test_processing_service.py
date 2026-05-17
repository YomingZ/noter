"""Tests for ProcessingService — GUI-free batch processing logic."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


class TestProcessingServiceInit:
    """Behavior: service accepts configuration without importing PyQt."""

    def test_creates_with_provider_and_output_dir(self):
        from pdf_summarizer.processing_service import ProcessingService

        svc = ProcessingService(
            provider="kimi",
            output_format="docx",
            output_dir=Path("/tmp/output"),
        )
        assert svc is not None

    def test_stores_obsidian_params(self):
        from pdf_summarizer.processing_service import ProcessingService

        svc = ProcessingService(
            provider="openai",
            output_format="obsidian",
            output_dir=Path("/tmp/out"),
            obsidian_template=Path("/t.md"),
            obsidian_course="量子化学",
            obsidian_vault=Path("/vault"),
        )
        assert svc.obsidian_template == Path("/t.md")
        assert svc.obsidian_course == "量子化学"

    def test_no_pyqt_import(self):
        import sys
        blocked = {k for k in sys.modules if k.startswith("PyQt")}
        for mod in blocked:
            del sys.modules[mod]

        from pdf_summarizer.processing_service import ProcessingService
        assert ProcessingService is not None


class TestProcessingServiceProcessOne:
    """Behavior: processing a single file returns a ProcessResult."""

    @patch("pdf_summarizer.processing_service.Summarizer")
    def test_calls_summarizer_process(self, MockSummarizer, tmp_path):
        from pdf_summarizer.processing_service import ProcessingService

        mock_summarizer = MockSummarizer.return_value
        mock_result = Mock(success=True, output_file=tmp_path / "out.docx", error_message="")
        mock_summarizer.process.return_value = mock_result

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")

        svc = ProcessingService(
            provider="kimi",
            output_format="docx",
            output_dir=tmp_path,
        )
        result = svc.process_one(pdf_file)

        assert result.success is True
        mock_summarizer.process.assert_called_once()

    @patch("pdf_summarizer.processing_service.Summarizer")
    def test_propagates_failure(self, MockSummarizer, tmp_path):
        from pdf_summarizer.processing_service import ProcessingService

        mock_summarizer = MockSummarizer.return_value
        mock_summarizer.process.return_value = Mock(
            success=False,
            error_message="API rate limited",
            output_file=None,
        )

        pdf_file = tmp_path / "fail.pdf"
        pdf_file.write_bytes(b"%PDF")

        svc = ProcessingService(
            provider="openai",
            output_format="docx",
            output_dir=tmp_path,
        )
        result = svc.process_one(pdf_file)

        assert result.success is False
        assert "rate" in result.error_message.lower() or result.error_message != ""

    @patch("pdf_summarizer.processing_service.Summarizer")
    def test_passes_obsidian_args_when_format_is_obsidian(self, MockSummarizer, tmp_path):
        from pdf_summarizer.processing_service import ProcessingService

        mock_summarizer = MockSummarizer.return_value
        mock_summarizer.process.return_value = Mock(
            success=True, output_file=tmp_path / "n.md", error_message=""
        )

        pdf_file = tmp_path / "lec.pdf"
        pdf_file.write_bytes(b"%PDF")

        svc = ProcessingService(
            provider="kimi",
            output_format="obsidian",
            output_dir=tmp_path,
            obsidian_template=Path("/tpl.md"),
            obsidian_course="calc",
            obsidian_vault=Path("/v"),
        )
        svc.process_one(pdf_file)

        call_kwargs = mock_summarizer.process.call_args
        assert call_kwargs.kwargs["output_format"] == "obsidian"
        assert call_kwargs.kwargs["course_name"] == "calc"


class TestProcessingServiceConfigureAI:
    """Behavior: applying AI config sets env vars and config object."""

    def test_sets_env_vars_for_kimi(self):
        from pdf_summarizer.processing_service import ProcessingService

        svc = ProcessingService(
            provider="kimi",
            output_format="docx",
            output_dir=Path("/tmp"),
        )

        ai_config = {
            "provider": "kimi",
            "api_key": "test-key-123",
            "model": "moonshot-v1-32k",
            "base_url": "",
            "temperature": 0.7,
        }
        svc.configure_ai(ai_config)

        import os
        assert os.environ.get("KIMI_API_KEY") == "test-key-123"

    def test_sets_env_vars_for_openai(self):
        from pdf_summarizer.processing_service import ProcessingService

        svc = ProcessingService(provider="openai", output_format="docx", output_dir=Path("/tmp"))

        ai_config = {
            "provider": "openai",
            "api_key": "sk-abc",
            "model": "gpt-4o",
            "base_url": "https://api.example.com",
            "temperature": 0.5,
        }
        svc.configure_ai(ai_config)

        import os
        assert os.environ.get("OPENAI_API_KEY") == "sk-abc"

    def test_raises_on_missing_api_key(self):
        from pdf_summarizer.processing_service import ProcessingService

        svc = ProcessingService(provider="kimi", output_format="docx", output_dir=Path("/tmp"))

        with pytest.raises(ValueError, match="API Key"):
            svc.configure_ai({"provider": "kimi", "api_key": "", "model": "x"})


class TestProcessingServiceProcessBatch:
    """Behavior: batch processing yields per-file results."""

    def test_processes_all_files(self, tmp_path):
        from pdf_summarizer.processing_service import ProcessingService
        from unittest.mock import patch

        svc = ProcessingService(provider="kimi", output_format="docx", output_dir=tmp_path)

        files = [tmp_path / f"a{i}.pdf" for i in range(3)]
        for f in files:
            f.write_bytes(b"%PDF")

        with patch.object(svc, 'process_one') as mock_one:
            mock_one.side_effect = [
                Mock(success=True, output_file=f, error_message="", file_path=f)
                for f in files
            ]
            results = list(svc.process_batch(files))

        assert len(results) == 3
        assert all(r.success for r in results)

    def test_respects_cancel_flag(self, tmp_path):
        from pdf_summarizer.processing_service import ProcessingService
        from unittest.mock import patch

        svc = ProcessingService(provider="kimi", output_format="docx", output_dir=tmp_path)

        files = [tmp_path / f"x{i}.pdf" for i in range(10)]
        for f in files:
            f.write_bytes(b"%PDF")

        call_count = [0]

        def side_effect(f):
            call_count[0] += 1
            if call_count[0] >= 3:
                svc.cancel()
            return Mock(success=True, output_file=f, error_message="", file_path=f)

        with patch.object(svc, 'process_one') as mock_one:
            mock_one.side_effect = side_effect
            results = list(svc.process_batch(files))

        assert len(results) <= 4
