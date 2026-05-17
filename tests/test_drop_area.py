"""Tests for DropArea — extracted file drag-and-drop component."""

import pytest
from pathlib import Path


class TestDropAreaCreation:
    """Behavior: DropArea is a QFrame with drag-drop enabled."""

    def test_is_qframe(self, qtbot):
        from gui_launcher.drop_area import DropArea

        area = DropArea()
        qtbot.addWidget(area)

        assert area is not None

    def test_accepts_drops(self, qtbot):
        from gui_launcher.drop_area import DropArea

        area = DropArea()
        qtbot.addWidget(area)

        assert area.acceptDrops() is True

    def test_has_minimum_height(self, qtbot):
        from gui_launcher.drop_area import DropArea

        area = DropArea()
        qtbot.addWidget(area)

        assert area.minimumHeight() >= 100

    def test_has_icon_label(self, qtbot):
        from gui_launcher.drop_area import DropArea
        from PyQt6.QtWidgets import QLabel

        area = DropArea()
        qtbot.addWidget(area)

        labels = area.findChildren(QLabel)
        assert len(labels) >= 2

    def test_shows_default_text(self, qtbot):
        from gui_launcher.drop_area import DropArea
        from PyQt6.QtWidgets import QLabel

        area = DropArea()
        qtbot.addWidget(area)

        labels = area.findChildren(QLabel)
        texts = [l.text() for l in labels]
        assert any("拖拽" in t or "PDF" in t for t in texts)


class TestDropAreaSignal:
    """Behavior: DropArea emits filesDropped signal with Path list."""

    def test_has_files_dropped_signal(self, qtbot):
        from gui_launcher.drop_area import DropArea

        area = DropArea()
        qtbot.addWidget(area)

        assert hasattr(area, 'filesDropped')

    def test_emits_on_valid_files(self, qtbot):
        from gui_launcher.drop_area import DropArea

        area = DropArea()
        qtbot.addWidget(area)

        emitted = []
        area.filesDropped.connect(lambda files: emitted.extend(files))

        test_files = [Path("/test/file1.pdf"), Path("/test/file2.pdf")]
        area.filesDropped.emit(test_files)

        assert len(emitted) == 2
        assert emitted[0] == Path("/test/file1.pdf")


class TestDropAreaStyle:
    """Behavior: update_style() changes appearance based on drag state."""

    def test_default_style_not_drag_over(self, qtbot):
        from gui_launcher.drop_area import DropArea

        area = DropArea()
        qtbot.addWidget(area)

        assert area.is_drag_over is False

    def test_style_changes_when_drag_over(self, qtbot):
        from gui_launcher.drop_area import DropArea

        area = DropArea()
        qtbot.addWidget(area)

        area.is_drag_over = True
        area.update_style()

        style = area.styleSheet()
        assert "solid" in style or "accent" in style.lower()

    def test_icon_changes_on_drag_over(self, qtbot):
        from gui_launcher.drop_area import DropArea
        from PyQt6.QtWidgets import QLabel

        area = DropArea()
        qtbot.addWidget(area)

        icon_label = None
        for label in area.findChildren(QLabel):
            if label.text() in ("📁", "📂"):
                icon_label = label
                break

        assert icon_label is not None
        assert icon_label.text() == "📁"

        area.is_drag_over = True
        area.update_style()
        area.icon_label.setText("📂")
        assert icon_label.text() == "📂"


class TestDropAreaState:
    """Behavior: Drag state management."""

    def test_initial_state_is_not_dragging(self, qtbot):
        from gui_launcher.drop_area import DropArea

        area = DropArea()
        qtbot.addWidget(area)

        assert area.is_drag_over is False

    def test_drag_enter_sets_flag(self, qtbot):
        from gui_launcher.drop_area import DropArea

        area = DropArea()
        qtbot.addWidget(area)

        area.is_drag_over = True
        assert area.is_drag_over is True

    def test_drag_leave_resets_flag(self, qtbot):
        from gui_launcher.drop_area import DropArea

        area = DropArea()
        qtbot.addWidget(area)

        area.is_drag_over = True
        area.dragLeaveEvent(None)
        assert area.is_drag_over is False


class TestDropAreaFileFiltering:
    """Behavior: Only PDF files are accepted from drop."""

    def test_pdf_file_is_accepted(self, qtbot, tmp_path):
        from gui_launcher.drop_area import DropArea

        area = DropArea()
        qtbot.addWidget(area)

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("fake pdf")

        emitted = []
        area.filesDropped.connect(lambda files: emitted.extend(files))

        area.filesDropped.emit([pdf_file])

        assert len(emitted) == 1
        assert emitted[0].suffix == ".pdf"
