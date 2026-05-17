"""Tests for LogPanel — extracted logging widget from ModernMainWindow."""

import pytest


class TestLogPanelCreation:
    """Behavior: LogPanel is a QWidget with a read-only text area."""

    def test_is_widget(self, qtbot):
        from gui_launcher.log_panel import LogPanel

        panel = LogPanel()
        qtbot.addWidget(panel)

        assert panel is not None

    def test_has_text_edit(self, qtbot):
        from gui_launcher.log_panel import LogPanel
        from PyQt6.QtWidgets import QTextEdit

        panel = LogPanel()
        qtbot.addWidget(panel)

        text_edits = panel.findChildren(QTextEdit)
        assert len(text_edits) >= 1

    def test_text_edit_is_read_only(self, qtbot):
        from gui_launcher.log_panel import LogPanel
        from PyQt6.QtWidgets import QTextEdit

        panel = LogPanel()
        qtbot.addWidget(panel)

        text_edit = panel.findChild(QTextEdit)
        assert text_edit.isReadOnly()


class TestLogPanelAppend:
    """Behavior: append_log() adds timestamped, color-coded entries."""

    def test_append_info_message(self, qtbot):
        from gui_launcher.log_panel import LogPanel

        panel = LogPanel()
        qtbot.addWidget(panel)

        panel.append_log("Processing file", "info")

        text = panel.get_text()
        assert "Processing file" in text

    def test_append_error_message(self, qtbot):
        from gui_launcher.log_panel import LogPanel

        panel = LogPanel()
        qtbot.addWidget(panel)

        panel.append_log("API Error", "error")

        text = panel.get_text()
        assert "API Error" in text

    def test_append_success_message(self, qtbot):
        from gui_launcher.log_panel import LogPanel

        panel = LogPanel()
        qtbot.addWidget(panel)

        panel.append_log("Done", "success")

        text = panel.get_text()
        assert "Done" in text

    def test_includes_timestamp(self, qtbot):
        from gui_launcher.log_panel import LogPanel
        import re

        panel = LogPanel()
        qtbot.addWidget(panel)

        panel.append_log("test message", "info")

        text = panel.get_text()
        timestamp_pattern = r'\d{2}:\d{2}:\d{2}'
        assert re.search(timestamp_pattern, text), f"Expected timestamp in: {text}"

    def test_multiple_entries_accumulate(self, qtbot):
        from gui_launcher.log_panel import LogPanel

        panel = LogPanel()
        qtbot.addWidget(panel)

        panel.append_log("First", "info")
        panel.append_log("Second", "error")
        panel.append_log("Third", "success")

        text = panel.get_text()
        assert "First" in text
        assert "Second" in text
        assert "Third" in text


class TestLogPanelClear:
    """Behavior: clear_logs() removes all entries."""

    def test_clear_removes_all_text(self, qtbot):
        from gui_launcher.log_panel import LogPanel

        panel = LogPanel()
        qtbot.addWidget(panel)

        panel.append_log("Some log", "info")
        assert len(panel.get_text()) > 0

        panel.clear_logs()

        assert panel.get_text().strip() == ""

    def test_clear_on_empty_is_safe(self, qtbot):
        from gui_launcher.log_panel import LogPanel

        panel = LogPanel()
        qtbot.addWidget(panel)

        panel.clear_logs()
        assert panel.get_text().strip() == ""


class TestLogPanelSignal:
    """Behavior: LogPanel emits signals for external handling."""

    def test_emits_log_signal_on_append(self, qtbot):
        from gui_launcher.log_panel import LogPanel

        panel = LogPanel()
        qtbot.addWidget(panel)

        messages = []
        panel.logMessage.connect(lambda msg, lvl: messages.append((msg, lvl)))

        panel.append_log("Test signal", "info")

        assert len(messages) == 1
        assert messages[0] == ("Test signal", "info")


class TestLogLevelPrefix:
    """Behavior: Different log levels get different visual prefixes."""

    def test_info_prefix(self, qtbot):
        from gui_launcher.log_panel import LogPanel

        panel = LogPanel()
        qtbot.addWidget(panel)

        panel.append_log("msg", "info")
        text = panel.get_text()
        assert "[ℹ️]" in text or "[i]" in text.lower() or "info" in text.lower()

    def test_error_prefix(self, qtbot):
        from gui_launcher.log_panel import LogPanel

        panel = LogPanel()
        qtbot.addWidget(panel)

        panel.append_log("msg", "error")
        text = panel.get_text()
        assert "[❌]" in text or "[err]" in text.lower() or "error" in text.lower()

    def test_success_prefix(self, qtbot):
        from gui_launcher.log_panel import LogPanel

        panel = LogPanel()
        qtbot.addWidget(panel)

        panel.append_log("msg", "success")
        text = panel.get_text()
        assert "[✅]" in text or "[ok]" in text.lower() or "success" in text.lower()
