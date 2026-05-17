"""Obsidian vault scanning and course-to-path mapping with caching."""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

CACHE_FILE = ".vault_cache.json"
CACHE_MAX_AGE_HOURS = 24


class VaultError(Exception):
    """Base vault error."""


class VaultNotFoundError(VaultError):
    """Vault directory does not exist."""


class CourseNotFoundError(VaultError):
    """Course name not found in vault."""


class VaultIndexer:
    """Scan Obsidian vault and map course names to folder paths."""

    def __init__(self, vault_root: Path):
        self.vault_root = Path(vault_root)
        if not self.vault_root.is_dir():
            raise VaultNotFoundError(
                f"Vault directory not found: {vault_root}\n"
                f"请检查 --vault 参数指向的 Obsidian vault 路径是否正确。"
            )
        self.vault_root = self._detect_vault_root(self.vault_root)

    @staticmethod
    def _detect_vault_root(path: Path) -> Path:
        """Auto-detect vault root if user gave a deep subdirectory path.

        A valid vault root has category folders (each containing course folders).
        If the given path is a leaf directory (no such structure), walk up.
        """
        current = path
        while True:
            if VaultIndexer._looks_like_vault_root(current):
                if current != path:
                    logger.info(
                        "Auto-corrected vault root: %s → %s", path, current
                    )
                return current
            parent = current.parent
            if parent == current:
                break
            current = parent
        return path

    @staticmethod
    def _looks_like_vault_root(path: Path) -> bool:
        """Check if path looks like a vault root (has subdirs with .md files inside)."""
        note_dirs = 0
        for item in sorted(path.iterdir())[:20]:
            if not item.is_dir() or item.name.startswith("."):
                continue
            if VaultIndexer._has_md_files_recursive(item, depth=3):
                note_dirs += 1
        return note_dirs >= 1

    @staticmethod
    def _has_md_files_recursive(directory: Path, depth: int) -> bool:
        """Check if directory tree contains any .md files within given depth."""
        if depth <= 0:
            return False
        try:
            for f in directory.iterdir():
                if f.is_file() and f.suffix.lower() == ".md":
                    return True
                if f.is_dir() and not f.name.startswith(".") and depth > 1:
                    if VaultIndexer._has_md_files_recursive(f, depth - 1):
                        return True
        except (PermissionError, OSError):
            pass
        return False

    def scan(self) -> dict[str, str]:
        """Scan vault and return {course_name: "relative/path"} mapping.

        Recursively finds leaf directories that contain .md note files.
        Skips intermediate category/subcategory folders that have no notes.
        """
        mapping: dict[str, str] = {}

        for item in sorted(self.vault_root.iterdir()):
            if not item.is_dir() or item.name.startswith("."):
                continue
            self._scan_recursive(item, "", mapping)

        return mapping

    def _scan_recursive(self, current_dir: Path, prefix: str, mapping: dict):
        """Recursively scan directory tree for course folders.

        A folder is a "course" if it contains .md files directly.
        Otherwise it's treated as a category container and we descend.
        """
        has_notes = any(f.suffix.lower() == ".md" for f in current_dir.iterdir() if f.is_file())
        if has_notes:
            rel_path = f"{prefix}{current_dir.name}" if prefix else current_dir.name
            course_name = current_dir.name
            if course_name in mapping:
                logger.warning(
                    "Duplicate course name '%s' at '%s' and '%s'",
                    course_name, mapping[course_name], rel_path
                )
            else:
                mapping[course_name] = rel_path
            return

        for sub_dir in sorted(current_dir.iterdir()):
            if not sub_dir.is_dir() or sub_dir.name.startswith(".") or "概览" in sub_dir.name:
                continue
            new_prefix = f"{prefix}{current_dir.name}/" if prefix else f"{current_dir.name}/"
            self._scan_recursive(sub_dir, new_prefix, mapping)

    def resolve_course_path(self, course_name: str) -> Path:
        """Find vault path for a course. Exact match only.

        Raises CourseNotFoundError if no match, listing available courses.
        """
        mapping = self._load_with_cache()

        if course_name in mapping:
            return self.vault_root / mapping[course_name]

        # Build error message with available courses grouped by category
        available = self._group_by_category(mapping)
        categories = []
        for cat in sorted(available.keys()):
            courses = "  ".join(available[cat])
            categories.append(f"  {cat}/: {courses}")

        raise CourseNotFoundError(
            f"未找到课程「{course_name}」\n"
            f"vault 路径: {self.vault_root}\n\n"
            f"当前可用的课程：\n" + "\n".join(categories) + "\n\n"
            f"请检查 --course 参数是否与 vault 中的课程文件夹名称完全一致。"
        )

    def _load_with_cache(self) -> dict[str, str]:
        """Load course mapping, using cache if fresh enough."""
        cache = self._load_cache()
        if cache is not None:
            return cache

        # Scan and cache
        mapping = self.scan()
        self._save_cache(mapping)
        return mapping

    def _load_cache(self) -> Optional[dict[str, str]]:
        """Load cached vault index if it exists and is fresh."""
        cache_path = self.vault_root / CACHE_FILE
        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            timestamp = datetime.fromisoformat(data.get("timestamp", ""))
            age = datetime.now() - timestamp

            if age > timedelta(hours=CACHE_MAX_AGE_HOURS):
                logger.debug("Vault cache expired, rescanning...")
                return None

            return data.get("mapping", {})

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.debug("Invalid vault cache: %s", e)
            return None

    def _save_cache(self, mapping: dict[str, str]):
        """Cache vault index to file."""
        cache_path = self.vault_root / CACHE_FILE
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "vault_root": str(self.vault_root),
                        "mapping": mapping,
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
            logger.debug("Vault cache saved: %s", cache_path)
        except OSError as e:
            logger.warning("Failed to save vault cache: %s", e)

    @staticmethod
    def _group_by_category(mapping: dict[str, str]) -> dict[str, list[str]]:
        """Group courses by category for display."""
        grouped: dict[str, list[str]] = {}
        for course_name, rel_path in mapping.items():
            category = rel_path.split("/", 1)[0]
            grouped.setdefault(category, []).append(course_name)
        return grouped
