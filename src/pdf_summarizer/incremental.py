"""Incremental processing module - only process new/modified files."""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Set, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FileRecord:
    """Record of a processed file."""
    path: str
    size: int
    modified_time: float
    content_hash: str
    processed_time: str
    output_path: str


class IncrementalProcessor:
    """
    Track processed files and only process new/modified ones.

    Features:
    - Track file modifications by size, mtime, and content hash
    - Skip already processed files
    - Support force reprocessing
    """

    def __init__(self, state_dir: Optional[Path] = None):
        self.state_dir = state_dir or Path("./output/.state")
        self.state_file = self.state_dir / "processed_files.json"
        self._records: dict[str, FileRecord] = {}
        self._load_state()

    def _load_state(self):
        """Load processed files state from disk."""
        if self.state_file.exists():
            try:
                with open(self.state_file, encoding="utf-8") as f:
                    data = json.load(f)
                    for path, record in data.items():
                        self._records[path] = FileRecord(**record)
                logger.debug(f"Loaded {len(self._records)} file records")
            except Exception as e:
                logger.warning(f"Failed to load state: {e}")

    def _save_state(self):
        """Save processed files state to disk."""
        self.state_dir.mkdir(parents=True, exist_ok=True)

        data = {
            path: {
                "path": r.path,
                "size": r.size,
                "modified_time": r.modified_time,
                "content_hash": r.content_hash,
                "processed_time": r.processed_time,
                "output_path": r.output_path,
            }
            for path, r in self._records.items()
        }

        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _compute_hash(self, file_path: Path) -> str:
        """Compute content hash for a file."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()[:16]

    def needs_processing(self, file_path: Path) -> bool:
        """Check if a file needs to be processed."""
        file_key = str(file_path.resolve())

        if file_key not in self._records:
            return True

        record = self._records[file_key]

        # Check file size
        current_size = file_path.stat().st_size
        if current_size != record.size:
            return True

        # Check modification time
        current_mtime = file_path.stat().st_mtime
        if current_mtime != record.modified_time:
            # Double check with content hash
            current_hash = self._compute_hash(file_path)
            if current_hash != record.content_hash:
                return True

        # Check if output exists
        output_path = Path(record.output_path)
        if not output_path.exists():
            return True

        return False

    def get_output_path(self, file_path: Path) -> Optional[Path]:
        """Get existing output path for a processed file."""
        file_key = str(file_path.resolve())
        if file_key in self._records:
            return Path(self._records[file_key].output_path)
        return None

    def mark_processed(
        self,
        file_path: Path,
        output_path: Path,
    ):
        """Mark a file as processed."""
        file_key = str(file_path.resolve())

        self._records[file_key] = FileRecord(
            path=file_key,
            size=file_path.stat().st_size,
            modified_time=file_path.stat().st_mtime,
            content_hash=self._compute_hash(file_path),
            processed_time=datetime.now().isoformat(),
            output_path=str(output_path.resolve()),
        )

        self._save_state()
        logger.debug(f"Marked as processed: {file_path.name}")

    def filter_new_files(
        self,
        files: List[Path],
        force: bool = False,
    ) -> tuple[List[Path], List[Path]]:
        """
        Filter files into new/modified and already processed.

        Returns:
            Tuple of (files_to_process, already_processed)
        """
        if force:
            return files, []

        to_process = []
        already_processed = []

        for f in files:
            if self.needs_processing(f):
                to_process.append(f)
            else:
                already_processed.append(f)

        logger.info(
            f"Incremental: {len(to_process)} to process, "
            f"{len(already_processed)} already done"
        )

        return to_process, already_processed

    def clear(self):
        """Clear all processed records."""
        self._records.clear()
        if self.state_file.exists():
            self.state_file.unlink()
        logger.info("Cleared all incremental processing records")

    def get_stats(self) -> dict:
        """Get statistics about processed files."""
        return {
            "total_processed": len(self._records),
            "state_file": str(self.state_file),
        }
