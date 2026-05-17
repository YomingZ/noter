"""Vault scanning service — GUI-free layer between UI and VaultIndexer.

This is the seam that lets GUI code call vault operations
without importing or instantiating VaultIndexer directly.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

from pdf_summarizer.vault_indexer import VaultIndexer, VaultError, VaultNotFoundError, CourseNotFoundError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VaultScanResult:
    """Immutable result of a vault scan operation."""

    success: bool
    courses: list[str] = field(default_factory=list)
    vault_root: Path = field(default_factory=lambda: Path("."))
    corrected_path: bool = False
    error_message: str = ""


@dataclass(frozen=True)
class VaultResolveResult:
    """Immutable result of a course-path resolution."""

    success: bool
    course_path: Path = field(default_factory=lambda: Path("."))
    error_message: str = ""


class VaultService:
    """GUI-free vault operations facade.

    Wraps VaultIndexer with error handling and immutable results.
    No PyQt dependency — fully unit-testable with tmp_path.
    """

    def scan_courses(self, vault_path: Path) -> VaultScanResult:
        """Scan vault and return sorted course names.

        Auto-detects vault root if given a subdirectory path.
        Returns VaultScanResult (never raises).
        """
        vault_path = Path(vault_path)

        if not vault_path.exists():
            return VaultScanResult(
                success=False,
                error_message=f"路径不存在: {vault_path}",
            )

        if not vault_path.is_dir():
            return VaultScanResult(
                success=False,
                error_message=f"不是目录: {vault_path}",
            )

        try:
            indexer = VaultIndexer(vault_path)
            corrected = indexer.vault_root != vault_path

            mapping = indexer.scan()
            courses = sorted(mapping.keys())

            return VaultScanResult(
                success=True,
                courses=courses,
                vault_root=indexer.vault_root,
                corrected_path=corrected,
            )
        except VaultNotFoundError as e:
            return VaultScanResult(
                success=False,
                error_message=str(e),
            )
        except VaultError as e:
            return VaultScanResult(
                success=False,
                error_message=str(e),
            )
        except Exception as e:
            logger.exception("Unexpected error scanning vault")
            return VaultScanResult(
                success=False,
                error_message=f"扫描失败: {e}",
            )

    def resolve_course(self, vault_root: Path, course_name: str) -> VaultResolveResult:
        """Resolve course name to absolute directory path.

        Returns VaultResolveResult (never raises).
        """
        try:
            indexer = VaultIndexer(vault_root)
            path = indexer.resolve_course_path(course_name)
            return VaultResolveResult(
                success=True,
                course_path=path,
            )
        except CourseNotFoundError as e:
            return VaultResolveResult(
                success=False,
                error_message=str(e),
            )
        except VaultError as e:
            return VaultResolveResult(
                success=False,
                error_message=str(e),
            )
        except Exception as e:
            logger.exception("Unexpected error resolving course")
            return VaultResolveResult(
                success=False,
                error_message=f"解析课程路径失败: {e}",
            )
