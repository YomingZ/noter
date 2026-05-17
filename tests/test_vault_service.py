"""Tests for VaultService — GUI-free vault scanning layer."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from pdf_summarizer.vault_service import VaultService, VaultScanResult


class TestVaultServiceScanCourses:
    """Behavior: scanning a vault returns sorted course names."""

    def test_returns_sorted_course_names(self, tmp_path):
        vault = tmp_path / "vault"
        (vault / "math" / "calculus").mkdir(parents=True)
        (vault / "math" / "calculus" / "note.md").write_text("# calc", encoding="utf-8")
        (vault / "math" / "linear").mkdir(parents=True)
        (vault / "math" / "linear" / "note.md").write_text("# linear", encoding="utf-8")
        (vault / "chem" / "quantum").mkdir(parents=True)
        (vault / "chem" / "quantum" / "note.md").write_text("# qm", encoding="utf-8")

        service = VaultService()
        result = service.scan_courses(vault)

        assert result.success is True
        assert result.courses == ["calculus", "linear", "quantum"]
        assert result.vault_root == vault

    def test_auto_detects_vault_root_from_subdirectory(self, tmp_path):
        vault = tmp_path / "vault"
        (vault / "courseA").mkdir(parents=True)
        (vault / "courseA" / "n.md").write_text("a", encoding="utf-8")

        deep_path = vault / "courseA"

        service = VaultService()
        result = service.scan_courses(deep_path)

        assert result.success is True
        assert result.vault_root == vault
        assert result.corrected_path is True

    def test_returns_empty_on_invalid_path(self):
        service = VaultService()
        result = service.scan_courses(Path("Z:/nonexistent/vault"))

        assert result.success is False
        assert result.courses == []
        assert result.error_message != ""

    def test_returns_empty_on_non_directory(self, tmp_path):
        not_a_dir = tmp_path / "file.txt"
        not_a_dir.write_text("hello", encoding="utf-8")

        service = VaultService()
        result = service.scan_courses(not_a_dir)

        assert result.success is False

    def test_skips_empty_directories(self, tmp_path):
        vault = tmp_path / "vault"
        has_notes = vault / "has_notes"
        has_notes.mkdir(parents=True)
        (has_notes / "note.md").write_text("# n", encoding="utf-8")
        (vault / "empty_folder").mkdir(parents=True)

        service = VaultService()
        result = service.scan_courses(vault)

        assert result.courses == ["has_notes"]

    def test_result_is_immutable_dataclass(self, tmp_path):
        vault = tmp_path / "v"
        course_dir = vault / "c"
        course_dir.mkdir(parents=True)
        (course_dir / "n.md").write_text("x", encoding="utf-8")

        service = VaultService()
        result = service.scan_courses(vault)

        assert hasattr(result, "success")
        assert hasattr(result, "courses")
        assert hasattr(result, "vault_root")
        assert hasattr(result, "corrected_path")
        assert hasattr(result, "error_message")


class TestVaultServiceResolveCourse:
    """Behavior: resolving a course name returns its absolute path."""

    def test_resolves_existing_course(self, tmp_path):
        vault = tmp_path / "vault"
        course_dir = vault / "math" / "calculus"
        course_dir.mkdir(parents=True)
        (course_dir / "note.md").write_text("# calc", encoding="utf-8")

        service = VaultService()
        result = service.resolve_course(vault, "calculus")

        assert result.success is True
        assert result.course_path == course_dir

    def test_fails_for_missing_course(self, tmp_path):
        vault = tmp_path / "vault"
        (vault / "math" / "calc").mkdir(parents=True)
        (vault / "math" / "calc" / "n.md").write_text("x", encoding="utf-8")

        service = VaultService()
        result = service.resolve_course(vault, "nonexistent")

        assert result.success is False
        assert "nonexistent" in result.error_message


class TestVaultServiceNoPyQtDependency:
    """VaultService must be importable without PyQt6."""

    def test_import_without_pyqt(self):
        import importlib
        import sys

        blocked = {k for k in sys.modules if k.startswith("PyQt")}
        for mod in blocked:
            del sys.modules[mod]

        import pdf_summarizer.vault_service as vs
        importlib.reload(vs)
        assert hasattr(vs, "VaultService")
