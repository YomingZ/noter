"""Parse raw AI responses into structured SummaryOutput objects."""

import logging
import re
from typing import Optional

from pdf_summarizer.models import SummaryOutput, SummarySection

logger = logging.getLogger(__name__)


class SummaryParser:
    """Parses AI-generated text into structured summary output."""

    def parse(self, source_file: str, raw_response: str) -> SummaryOutput:
        """Parse AI response into structured summary."""
        summary = SummaryOutput(
            source_file=source_file,
            raw_response=raw_response,
        )

        sections = self._extract_sections(raw_response)

        if not sections:
            sections = self._extract_chinese_sections(raw_response)

        summary.sections = sections

        for section in sections:
            content = section.content
            title_lower = section.title.lower()

            if "【定义】" in content:
                summary.core_concepts.extend(
                    self._extract_marker_content(content, "【定义】")
                )
            if "【定理】" in content or "【性质】" in content:
                summary.key_points.extend(
                    self._extract_marker_content(content, "【定理】|【性质】")
                )
            if "【注意】" in content:
                summary.review_tips.extend(
                    self._extract_marker_content(content, "【注意】")
                )

        if not summary.key_points:
            summary.key_points = self._extract_key_points_fallback(sections)
        if not summary.review_tips:
            summary.review_tips = self._extract_review_tips_fallback(sections)

        return summary

    def _extract_key_points_fallback(self, sections: list[SummarySection]) -> list[str]:
        key_point_keywords = ["重点", "要点", "关键", "核心", "重要", "公式", "结论"]
        items = []
        for section in sections:
            title_lower = section.title.lower()
            if any(kw in title_lower or kw in section.title for kw in key_point_keywords):
                list_items = self._extract_list_items(section.content)
                if list_items:
                    items.extend(list_items)
                elif section.content.strip():
                    items.append(section.content.strip())
        return items[:10]

    def _extract_review_tips_fallback(self, sections: list[SummarySection]) -> list[str]:
        review_keywords = ["注意", "易错", "提示", "提醒", "常见错误", "陷阱"]
        items = []
        for section in sections:
            title_lower = section.title.lower()
            if any(kw in title_lower or kw in section.title for kw in review_keywords):
                list_items = self._extract_list_items(section.content)
                if list_items:
                    items.extend(list_items)
                elif section.content.strip():
                    items.append(section.content.strip())
        return items[:10]

    @staticmethod
    def _extract_marker_content(text: str, marker: str) -> list[str]:
        items = []
        pattern = rf'({marker})\s*[：:]\s*([^\n]+(?:\n(?!【)[^\n]+)*)'
        for match in re.finditer(pattern, text):
            content = match.group(2).strip()
            if content:
                items.append(content)
        return items

    @staticmethod
    def _extract_chinese_sections(text: str) -> list[SummarySection]:
        sections = []
        pattern = r'【([^】]+)】'

        parts = re.split(pattern, text)
        current_title = ""

        for i, part in enumerate(parts):
            if i % 2 == 1:
                current_title = part.strip()
            elif current_title and part.strip():
                sections.append(SummarySection(
                    title=current_title,
                    content=part.strip(),
                    level=1,
                ))

        return sections

    @staticmethod
    def _extract_sections(text: str) -> list[SummarySection]:
        sections = []
        pattern = r"^(#{1,3})\s+(.+)$"
        lines = text.split("\n")

        current_title = ""
        current_content = []
        current_level = 1

        for line in lines:
            match = re.match(pattern, line)
            if match:
                if current_title:
                    sections.append(SummarySection(
                        title=current_title,
                        content="\n".join(current_content).strip(),
                        level=current_level,
                    ))

                current_level = len(match.group(1))
                current_title = match.group(2).strip()
                current_content = []
            else:
                current_content.append(line)

        if current_title:
            sections.append(SummarySection(
                title=current_title,
                content="\n".join(current_content).strip(),
                level=current_level,
            ))

        return sections

    @staticmethod
    def _extract_list_items(text: str) -> list[str]:
        items = []
        lines = text.split("\n")

        for line in lines:
            line = line.strip()
            if re.match(r"^[\d]+[\.、\)]\s*", line) or re.match(r"^[-•*]\s*", line):
                cleaned = re.sub(r"^[\d]+[\.、\)]\s*|^[-•*]\s*", "", line)
                if cleaned:
                    items.append(cleaned)

        return items
