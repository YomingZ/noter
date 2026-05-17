"""Tests for FileListArea — extracted file list component."""

import pytest
from pathlib import Path


class TestFileListAreaCreation:
    """Behavior: FileListArea is a QScrollArea with file management."""

    def test_is_scroll_area(self, qtbot):
        from gui_launcher.file_list_area import FileListArea

        area = FileListArea()
        qtbot.addWidget(area)

        assert area is not None

    def test_starts_empty(self, qtbot):
        from gui_launcher.file_list_area import FileListArea

        area = FileListArea()
        qtbot.addWidget(area)

        assert len(area.get_files()) == 0

    def test_has_files_changed_signal(self, qtbot):
        from gui_launcher.file_list_area import FileListArea

        area = FileListArea()
        qtbot.addWidget(area)

        assert hasattr(area, 'filesChanged')


class TestFileListAreaAddFile:
    """Behavior: add_file() creates a FileCard and emits signal."""

    def test_add_single_file(self, qtbot, tmp_path):
        from gui_launcher.file_list_area import FileListArea

        pdf = tmp_path / "test.pdf"
        pdf.write_text("fake")

        area = FileListArea()
        qtbot.addWidget(area)

        area.add_file(pdf)
        assert len(area.get_files()) == 1
        assert area.get_files()[0] == pdf

    def test_add_multiple_files(self, qtbot, tmp_path):
        from gui_launcher.file_list_area import FileListArea

        area = FileListArea()
        qtbot.addWidget(area)

        for i in range(3):
            pdf = tmp_path / f"file{i}.pdf"
            pdf.write_text("fake")
            area.add_file(pdf)

        assert len(area.get_files()) == 3


class TestFileListAreaClearFiles:
    """Behavior: clear_files() removes all cards."""

    def test_clear_empty_list(self, qtbot):
        from gui_launcher.file_list_area import FileListArea

        area = FileListArea()
        qtbot.addWidget(area)

        area.clear_files()
        assert len(area.get_files()) == 0

    def test_clear_with_files(self, qtbot, tmp_path):
        from gui_launcher.file_list_area import FileListArea

        area = FileListArea()
        qtbot.addWidget(area)

        pdf = tmp_path / "test.pdf"
        pdf.write_text("fake")
        area.add_file(pdf)
        assert len(area.get_files()) == 1

        area.clear_files()
        assert len(area.get_files()) == 0


class TestFileListAreaUpdateCard:
    """Behavior: update_card_status() updates specific card."""

    def test_update_existing_card(self, qtbot, tmp_path):
        from gui_launcher.file_list_area import FileListArea

        area = FileListArea()
        qtbot.addWidget(area)

        pdf = tmp_path / "test.pdf"
        pdf.write_text("fake")
        area.add_file(pdf)

        area.update_card_status(pdf, "processing", 50)

        cards = area.file_cards
        assert len(cards) == 1
        assert cards[0].status == "processing"

    def test_update_nonexistent_card_no_error(self, qtbot):
        from gui_launcher.file_list_area import FileListArea

        area = FileListArea()
        qtbot.addWidget(area)

        area.update_card_status(Path("/nonexistent.pdf"), "processing", 50)
        assert len(area.get_files()) == 0
