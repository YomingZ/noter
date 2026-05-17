"""Tests for FileCard — extracted file card component."""

import pytest
from pathlib import Path


class TestFileCardCreation:
    """Behavior: FileCard is a QFrame with file info display."""

    def test_is_qframe(self, qtbot):
        from gui_launcher.file_card import FileCard

        card = FileCard(Path("/test/file.pdf"))
        qtbot.addWidget(card)

        assert card is not None

    def test_stores_file_path(self, qtbot):
        from gui_launcher.file_card import FileCard

        test_path = Path("/test/my_document.pdf")
        card = FileCard(test_path)
        qtbot.addWidget(card)

        assert card.file_path == test_path

    def test_shows_filename(self, qtbot):
        from gui_launcher.file_card import FileCard
        from PyQt6.QtWidgets import QLabel

        card = FileCard(Path("/test/report.pdf"))
        qtbot.addWidget(card)

        labels = card.findChildren(QLabel)
        texts = [l.text() for l in labels]
        assert "report.pdf" in texts

    def test_has_fixed_height(self, qtbot):
        from gui_launcher.file_card import FileCard

        card = FileCard(Path("/test/file.pdf"))
        qtbot.addWidget(card)

        assert card.height() >= 50

    def test_default_status_is_pending(self, qtbot):
        from gui_launcher.file_card import FileCard

        card = FileCard(Path("/test/file.pdf"))
        qtbot.addWidget(card)

        assert card.status == "pending"


class TestFileSizeFormatting:
    """Behavior: _format_size() converts bytes to human-readable format."""

    def test_formats_bytes(self, qtbot):
        from gui_launcher.file_card import FileCard

        card = FileCard(Path("/test/file.pdf"))
        qtbot.addWidget(card)

        result = card._format_size(500)
        assert "500.0 B" == result

    def test_formats_kilobytes(self, qtbot):
        from gui_launcher.file_card import FileCard

        card = FileCard(Path("/test/file.pdf"))
        qtbot.addWidget(card)

        result = card._format_size(2048)
        assert "KB" in result

    def test_formats_megabytes(self, qtbot):
        from gui_launcher.file_card import FileCard

        card = FileCard(Path("/test/file.pdf"))
        qtbot.addWidget(card)

        result = card._format_size(5 * 1024 * 1024)
        assert "MB" in result

    def test_formats_gigabytes(self, qtbot):
        from gui_launcher.file_card import FileCard

        card = FileCard(Path("/test/file.pdf"))
        qtbot.addWidget(card)

        result = card._format_size(2 * 1024 * 1024 * 1024)
        assert "GB" in result


class TestFileCardStatus:
    """Behavior: set_status() updates display based on status."""

    def test_pending_status_shows_text(self, qtbot):
        from gui_launcher.file_card import FileCard
        from PyQt6.QtWidgets import QLabel

        card = FileCard(Path("/test/file.pdf"))
        qtbot.addWidget(card)

        card.set_status("pending")

        labels = card.findChildren(QLabel)
        status_labels = [l for l in labels if l.text() in ("待处理", "处理中", "完成", "失败")]
        assert any(l.text() == "待处理" for l in status_labels)

    def test_processing_status_shows_text(self, qtbot):
        from gui_launcher.file_card import FileCard
        from PyQt6.QtWidgets import QLabel

        card = FileCard(Path("/test/file.pdf"))
        qtbot.addWidget(card)

        card.set_status("processing")

        labels = card.findChildren(QLabel)
        status_labels = [l for l in labels if l.text() in ("待处理", "处理中", "完成", "失败")]
        assert any(l.text() == "处理中" for l in status_labels)

    def test_completed_status_shows_text(self, qtbot):
        from gui_launcher.file_card import FileCard
        from PyQt6.QtWidgets import QLabel

        card = FileCard(Path("/test/file.pdf"))
        qtbot.addWidget(card)

        card.set_status("completed")

        labels = card.findChildren(QLabel)
        status_labels = [l for l in labels if l.text() in ("待处理", "处理中", "完成", "失败")]
        assert any(l.text() == "完成" for l in status_labels)

    def test_failed_status_shows_text(self, qtbot):
        from gui_launcher.file_card import FileCard
        from PyQt6.QtWidgets import QLabel

        card = FileCard(Path("/test/file.pdf"))
        qtbot.addWidget(card)

        card.set_status("failed")

        labels = card.findChildren(QLabel)
        status_labels = [l for l in labels if l.text() in ("待处理", "处理中", "完成", "失败")]
        assert any(l.text() == "失败" for l in status_labels)


class TestFileCardProgress:
    """Behavior: Progress bar updates with status changes."""

    def test_progress_bar_exists(self, qtbot):
        from gui_launcher.file_card import FileCard
        from PyQt6.QtWidgets import QProgressBar

        card = FileCard(Path("/test/file.pdf"))
        qtbot.addWidget(card)

        bars = card.findChildren(QProgressBar)
        assert len(bars) == 1

    def test_initial_progress_is_zero(self, qtbot):
        from gui_launcher.file_card import FileCard
        from PyQt6.QtWidgets import QProgressBar

        card = FileCard(Path("/test/file.pdf"))
        qtbot.addWidget(card)

        bar = card.findChildren(QProgressBar)[0]
        assert bar.value() == 0

    def test_progress_updates_with_status(self, qtbot):
        from gui_launcher.file_card import FileCard
        from PyQt6.QtWidgets import QProgressBar

        card = FileCard(Path("/test/file.pdf"))
        qtbot.addWidget(card)

        card.set_status("processing", 50)

        bar = card.findChildren(QProgressBar)[0]
        assert bar.value() == 50

    def test_completed_sets_full_progress(self, qtbot):
        from gui_launcher.file_card import FileCard
        from PyQt6.QtWidgets import QProgressBar

        card = FileCard(Path("/test/file.pdf"))
        qtbot.addWidget(card)

        card.set_status("completed", 100)

        bar = card.findChildren(QProgressBar)[0]
        assert bar.value() == 100


class TestFileCardState:
    """Behavior: Internal state management."""

    def test_status_attribute_updated(self, qtbot):
        from gui_launcher.file_card import FileCard

        card = FileCard(Path("/test/file.pdf"))
        qtbot.addWidget(card)

        card.set_status("processing", 75)

        assert card.status == "processing"
        assert card.progress == 75

    def test_unknown_status_falls_back_to_pending(self, qtbot):
        from gui_launcher.file_card import FileCard

        card = FileCard(Path("/test/file.pdf"))
        qtbot.addWidget(card)

        card.set_status("unknown_status")

        assert card.status == "unknown_status"
