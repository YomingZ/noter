"""FileListArea — 文件列表区域组件，从 ModernMainWindow 抽取。"""

from pathlib import Path
from typing import List

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QScrollArea,
    QWidget,
    QVBoxLayout,
)

from gui_launcher.theme import Theme
from gui_launcher.file_card import FileCard


class FileListArea(QScrollArea):
    """文件列表 — 管理文件卡片的添加、清除和状态更新。"""

    filesChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_cards: List[FileCard] = []
        self.setup_ui()

    def setup_ui(self):
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet(f"""
            QScrollArea {{ background-color: transparent; border: none; }}
            QScrollBar:vertical {{ background-color: transparent; width: 6px; }}
            QScrollBar::handle:vertical {{ background-color: {Theme.get('border')}; border-radius: 3px; min-height: 30px; }}
        """)

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.setWidget(self.container)

        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(0, 0, 8, 0)
        self.layout.setSpacing(8)
        self.layout.addStretch()

    def add_file(self, file_path: Path):
        card = FileCard(file_path)
        self.file_cards.append(card)
        self.layout.insertWidget(self.layout.count() - 1, card)
        self.filesChanged.emit()

    def clear_files(self):
        for card in self.file_cards:
            card.deleteLater()
        self.file_cards.clear()
        self.filesChanged.emit()

    def get_files(self) -> List[Path]:
        return [card.file_path for card in self.file_cards]

    def update_card_status(self, file_path: Path, status: str, progress: int = 0):
        for card in self.file_cards:
            if card.file_path == file_path:
                card.set_status(status, progress)
                break
