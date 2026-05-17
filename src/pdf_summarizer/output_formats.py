"""Multiple output format support - Markdown, HTML, and Word."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional

from pdf_summarizer.models import SummaryOutput

logger = logging.getLogger(__name__)


class OutputWriter(ABC):
    """Abstract base class for output writers."""

    @abstractmethod
    def write(self, summary: SummaryOutput, output_path: Path) -> Path:
        """Write summary to file."""
        pass


class MarkdownWriter(OutputWriter):
    """Write summary as Markdown file."""

    def write(self, summary: SummaryOutput, output_path: Path) -> Path:
        """Write summary to Markdown file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            f"# {summary.source_file}",
            "",
            f"**来源**: {summary.source_file}",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "---",
            "",
        ]

        if summary.raw_response:
            # Use raw response directly
            lines.append(summary.raw_response)
        else:
            # Build from structured data
            if summary.core_concepts:
                lines.append("## 核心概念")
                lines.append("")
                for i, concept in enumerate(summary.core_concepts, 1):
                    lines.append(f"{i}. {concept}")
                lines.append("")

            for section in summary.sections:
                lines.append(f"## {section.title}")
                lines.append("")
                lines.append(section.content)
                lines.append("")

            if summary.key_points:
                lines.append("## 要点总结")
                lines.append("")
                for point in summary.key_points:
                    lines.append(f"- {point}")
                lines.append("")

            if summary.review_tips:
                lines.append("## 补充说明")
                lines.append("")
                for tip in summary.review_tips:
                    lines.append(f"- {tip}")
                lines.append("")

        content = "\n".join(lines)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Markdown saved: {output_path}")
        return output_path


class HTMLWriter(OutputWriter):
    """Write summary as HTML file with styling."""

    HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script>
        MathJax = {{
            tex: {{
                inlineMath: [['$', '$'], ['\\(', '\\)']],
                displayMath: [['$$', '$$'], ['\\[', '\\]']],
                processEscapes: true,
            }},
            svg: {{
                fontCache: 'global',
            }},
        }};
    </script>
    <script type="text/javascript" id="MathJax-script" async
        src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js">
    </script>
    <style>
        @page {{
            size: A4;
            margin: 2.5cm 2cm 2.5cm 2cm;
            @bottom-center {{
                content: counter(page);
                font-size: 10pt;
                color: #999;
            }}
        }}
        body {{
            font-family: "Times New Roman", "STSong", "SimSun", serif;
            max-width: 750px;
            margin: 0 auto;
            padding: 20px;
            color: #222;
            line-height: 1.7;
            font-size: 12pt;
        }}
        .lecture-title {{
            text-align: center;
            font-size: 22pt;
            font-weight: bold;
            color: #000;
            margin-bottom: 5px;
            letter-spacing: 2px;
        }}
        .lecture-subtitle {{
            text-align: center;
            font-size: 14pt;
            color: #555;
            margin-bottom: 30px;
        }}
        .meta {{
            text-align: center;
            color: #888;
            font-size: 10pt;
            margin-bottom: 25px;
            font-family: "Microsoft YaHei", sans-serif;
        }}
        h1 {{
            font-size: 16pt;
            font-weight: bold;
            color: #000;
            margin-top: 28px;
            margin-bottom: 12px;
            padding-bottom: 6px;
            border-bottom: 1px solid #ccc;
        }}
        h2 {{
            font-size: 13pt;
            font-weight: bold;
            color: #333;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        h3 {{
            font-size: 12pt;
            font-weight: bold;
            color: #444;
            margin-top: 16px;
            margin-bottom: 8px;
        }}
        p {{
            text-align: justify;
            margin: 8px 0;
            text-indent: 2em;
        }}
        .formula {{
            font-family: "Times New Roman", "Consolas", monospace;
            text-align: center;
            margin: 12px auto;
            padding: 8px 0;
            font-size: 12pt;
            text-indent: 0;
        }}
        .definition {{
            margin: 10px 0;
            padding: 8px 15px;
            border-left: 3px solid #333;
            background: #f9f9f9;
        }}
        .definition strong {{
            font-weight: bold;
        }}
        .theorem {{
            margin: 10px 0;
            padding: 8px 15px;
            border: 1px solid #ccc;
            background: #fafafa;
        }}
        .theorem strong {{
            font-weight: bold;
        }}
        .note {{
            margin: 10px 0;
            padding: 8px 15px;
            background: #f5f5f5;
            font-size: 11pt;
        }}
        .note strong {{
            font-weight: bold;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 11pt;
        }}
        table th {{
            background: #f0f0f0;
            border: 1px solid #ccc;
            padding: 8px 10px;
            font-weight: bold;
            text-align: center;
        }}
        table td {{
            border: 1px solid #ccc;
            padding: 6px 10px;
            text-align: left;
        }}
        ul, ol {{
            padding-left: 30px;
            margin: 8px 0;
        }}
        li {{
            margin: 4px 0;
        }}
        hr {{
            border: none;
            border-top: 1px solid #ddd;
            margin: 25px 0;
        }}
        .page-break {{
            page-break-before: always;
        }}
        @media print {{
            body {{
                padding: 0;
                max-width: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="lecture-title">{title}</div>
    <div class="meta">
        来源: {source} | 生成时间: {datetime}
    </div>
    <hr>
    {content}
</body>
</html>
"""

    def write(self, summary: SummaryOutput, output_path: Path) -> Path:
        """Write summary to HTML file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert content to HTML
        content_html = self._markdown_to_html(summary.raw_response or "")

        html = self.HTML_TEMPLATE.format(
            title=summary.source_file,
            source=summary.source_file,
            datetime=datetime.now().strftime('%Y-%m-%d %H:%M'),
            content=content_html,
        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        logger.info(f"HTML saved: {output_path}")
        return output_path

    def _markdown_to_html(self, md: str) -> str:
        """Convert Markdown to HTML with special formatting."""
        import re

        html = md

        # Convert section markers 【xxx】 to styled divs
        html = re.sub(
            r'【([^】]+)】',
            lambda m: self._format_section(m.group(1)),
            html
        )

        # Convert headers
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

        # Convert bullet lists
        lines = html.split('\n')
        in_list = False
        result = []

        for line in lines:
            if re.match(r'^[-•*]\s', line):
                if not in_list:
                    result.append('<ul>')
                    in_list = True
                item = re.sub(r'^[-•*]\s', '', line)
                result.append(f'<li>{item}</li>')
            elif re.match(r'^\d+[\.、\)]\s', line):
                if not in_list:
                    result.append('<ol>')
                    in_list = True
                item = re.sub(r'^\d+[\.、\)]\s', '', line)
                result.append(f'<li>{item}</li>')
            else:
                if in_list:
                    result.append('</ul>' if result[-2].startswith('<li>') else '</ol>')
                    in_list = False
                result.append(line)

        if in_list:
            result.append('</ul>')

        html = '\n'.join(result)

        # Convert paragraphs
        html = re.sub(r'\n\n', '</p><p>', html)

        return f'<p>{html}</p>'

    def _format_section(self, title: str) -> str:
        """Format section title."""
        return f'<h2>{title}</h2>'


def get_writer(format: str) -> OutputWriter:
    """Get appropriate writer for format."""
    writers = {
        'md': MarkdownWriter,
        'markdown': MarkdownWriter,
        'html': HTMLWriter,
        'docx': None,  # Use DocxWriter
    }

    writer_class = writers.get(format.lower())
    if writer_class is None:
        raise ValueError(f"Unsupported format: {format}")

    return writer_class()


def write_summary(
    summary: SummaryOutput,
    output_path: Path,
    format: str = 'docx',
) -> Path:
    """
    Write summary to file in specified format.

    Args:
        summary: Summary output data
        output_path: Output file path
        format: Output format (md, html, docx)

    Returns:
        Path to written file
    """
    format = format.lower()

    if format in ('md', 'markdown'):
        writer = MarkdownWriter()
        if not output_path.suffix:
            output_path = output_path.with_suffix('.md')
        return writer.write(summary, output_path)

    elif format == 'html':
        writer = HTMLWriter()
        if not output_path.suffix:
            output_path = output_path.with_suffix('.html')
        return writer.write(summary, output_path)

    else:
        from pdf_summarizer.docx_writer import DocxWriter
        writer = DocxWriter()
        if not output_path.suffix:
            output_path = output_path.with_suffix('.docx')
        return writer.write(summary, output_path)
