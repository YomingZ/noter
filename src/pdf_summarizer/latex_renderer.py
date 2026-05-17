"""LaTeX formula rendering and Pandoc conversion support."""

import logging
import re
import subprocess
import shutil
from pathlib import Path
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)


class LaTeXProcessor:
    """
    Process LaTeX formulas in content.

    Features:
    - Extract LaTeX formulas
    - Convert between formats
    - Generate Word-compatible formulas
    """

    # LaTeX formula patterns
    INLINE_MATH = re.compile(r'\$([^\$]+)\$')
    DISPLAY_MATH = re.compile(r'\$\$([^\$]+)\$\$', re.DOTALL)
    LATEX_ENV = re.compile(r'\\begin\{(\w+)\}(.*?)\\end\{\1\}', re.DOTALL)

    def extract_formulas(self, content: str) -> List[Tuple[str, str, int, int]]:
        """
        Extract all LaTeX formulas from content.

        Returns:
            List of (formula, type, start, end) tuples
        """
        formulas = []

        # Display math $$...$$
        for match in self.DISPLAY_MATH.finditer(content):
            formulas.append((match.group(1), 'display', match.start(), match.end()))

        # Inline math $...$
        for match in self.INLINE_MATH.finditer(content):
            # Skip if already captured as display math
            in_display = any(
                match.start() >= f[2] and match.end() <= f[3]
                for f in formulas
            )
            if not in_display:
                formulas.append((match.group(1), 'inline', match.start(), match.end()))

        return formulas

    def clean_latex(self, formula: str) -> str:
        """Clean and normalize LaTeX formula."""
        # Remove extra whitespace
        formula = ' '.join(formula.split())
        return formula.strip()

    def to_word_omath(self, formula: str) -> str:
        """Convert LaTeX to Word OMML format (approximate)."""
        # Basic LaTeX to Word conversion
        conversions = {
            r'\\frac\{([^}]+)\}\{([^}]+)\}': r'(\1)/(\2)',
            r'\\sqrt\{([^}]+)\}': r'√(\1)',
            r'\\sqrt\[(\d+)\]\{([^}]+)\}': r'\1√(\2)',
            r'\\sum': '∑',
            r'\\prod': '∏',
            r'\\int': '∫',
            r'\\infty': '∞',
            r'\\alpha': 'α',
            r'\\beta': 'β',
            r'\\gamma': 'γ',
            r'\\delta': 'δ',
            r'\\epsilon': 'ε',
            r'\\theta': 'θ',
            r'\\lambda': 'λ',
            r'\\mu': 'μ',
            r'\\pi': 'π',
            r'\\sigma': 'σ',
            r'\\omega': 'ω',
            r'\\phi': 'φ',
            r'\\Delta': 'Δ',
            r'\\Omega': 'Ω',
            r'\\Phi': 'Φ',
            r'\\leq': '≤',
            r'\\geq': '≥',
            r'\\neq': '≠',
            r'\\approx': '≈',
            r'\\pm': '±',
            r'\\times': '×',
            r'\\div': '÷',
            r'\\cdot': '·',
            r'\\rightarrow': '→',
            r'\\leftarrow': '←',
            r'\\Rightarrow': '⇒',
            r'\\Leftarrow': '⇐',
            r'\\partial': '∂',
            r'\\nabla': '∇',
            r'\\forall': '∀',
            r'\\exists': '∃',
            r'\\in': '∈',
            r'\\notin': '∉',
            r'\\subset': '⊂',
            r'\\supset': '⊃',
            r'\\cup': '∪',
            r'\\cap': '∩',
            r'\\emptyset': '∅',
            r'\\therefore': '∴',
            r'\\because': '∵',
            r'\^': '^',
            r'_': '_',
        }

        result = formula
        for pattern, replacement in conversions.items():
            result = re.sub(pattern, replacement, result)

        # Handle subscripts and superscripts
        result = re.sub(r'\{([^}]+)\}', r'\1', result)

        return result

    def prepare_for_pandoc(self, content: str) -> str:
        """Prepare content with LaTeX for Pandoc conversion."""
        # Ensure display math uses $$ delimiters
        content = self.DISPLAY_MATH.sub(r'$$\1$$', content)

        # Ensure inline math uses $ delimiters
        content = self.INLINE_MATH.sub(r'$\1$', content)

        return content


class PandocConverter:
    """
    Convert documents using Pandoc.

    Supports:
    - Markdown to Word (with LaTeX)
    - Word to PDF
    - Custom templates
    """

    def __init__(self):
        self.pandoc_path = self._find_pandoc()

    def _find_pandoc(self) -> Optional[str]:
        """Find Pandoc executable."""
        return shutil.which('pandoc')

    def is_available(self) -> bool:
        """Check if Pandoc is available."""
        return self.pandoc_path is not None

    def markdown_to_word(
        self,
        input_path: Path,
        output_path: Path,
        template: Optional[Path] = None,
        reference_doc: Optional[Path] = None,
    ) -> bool:
        """
        Convert Markdown to Word using Pandoc.

        Args:
            input_path: Path to input Markdown file
            output_path: Path to output Word file
            template: Optional Pandoc template
            reference_doc: Optional Word reference document for styles

        Returns:
            True if successful
        """
        if not self.is_available():
            logger.warning("Pandoc not available, cannot convert")
            return False

        cmd = [
            self.pandoc_path,
            str(input_path),
            '-f', 'markdown+tex_math_dollars+tex_math_single_backslash',
            '-t', 'docx',
            '-o', str(output_path),
            '--mathml',  # Convert math to MathML for Word
        ]

        if reference_doc and reference_doc.exists():
            cmd.extend(['--reference-doc', str(reference_doc)])

        if template and template.exists():
            cmd.extend(['--template', str(template)])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            logger.info(f"Pandoc conversion successful: {output_path}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Pandoc conversion failed: {e.stderr}")
            return False

    def markdown_to_pdf(
        self,
        input_path: Path,
        output_path: Path,
        via_latex: bool = True,
    ) -> bool:
        """
        Convert Markdown to PDF.

        Args:
            input_path: Path to input Markdown file
            output_path: Path to output PDF file
            via_latex: Use LaTeX engine for better math support

        Returns:
            True if successful
        """
        if not self.is_available():
            return False

        cmd = [
            self.pandoc_path,
            str(input_path),
            '-f', 'markdown+tex_math_dollars',
            '-o', str(output_path),
        ]

        if via_latex:
            cmd.extend([
                '--pdf-engine=xelatex',
                '-V', 'CJKmainfont=Microsoft YaHei',
            ])

        try:
            subprocess.run(cmd, capture_output=True, check=True)
            logger.info(f"PDF generated: {output_path}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"PDF generation failed: {e.stderr}")
            return False


class FormulaWriter:
    """
    Write documents with proper formula rendering.

    Supports multiple strategies:
    1. Native Word math (OMML)
    2. Markdown + Pandoc conversion
    3. Unicode approximation
    """

    def __init__(self, use_pandoc: bool = True):
        self.use_pandoc = use_pandoc
        self.latex_processor = LaTeXProcessor()
        self.pandoc = PandocConverter()

    def write_with_formulas(
        self,
        content: str,
        output_path: Path,
        format: str = 'docx',
        style: str = 'pandoc',
    ) -> Path:
        """
        Write content with LaTeX formulas.

        Args:
            content: Content with LaTeX formulas
            output_path: Output file path
            format: Output format (docx, md, html, pdf)
            style: Formula style ('pandoc', 'unicode', 'latex')

        Returns:
            Path to output file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == 'md' or style == 'latex':
            # Keep LaTeX as-is for Markdown
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return output_path

        if format == 'docx' and style == 'pandoc' and self.use_pandoc:
            # Use Pandoc for best LaTeX support
            return self._write_via_pandoc(content, output_path)

        # Convert to Unicode for basic Word support
        converted = self._convert_to_unicode(content)

        if format == 'docx':
            from pdf_summarizer.docx_writer import DocxWriter
            from pdf_summarizer.models import SummaryOutput

            summary = SummaryOutput(
                source_file="",
                raw_response=converted,
            )
            writer = DocxWriter()
            return writer.write(summary, output_path)

        # HTML or other formats
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(converted)

        return output_path

    def _write_via_pandoc(self, content: str, output_path: Path) -> Path:
        """Write via Pandoc for best formula support."""
        # First write to temporary Markdown
        temp_md = output_path.with_suffix('.temp.md')
        with open(temp_md, 'w', encoding='utf-8') as f:
            f.write(content)

        try:
            # Try to get reference template
            from pdf_summarizer.default_template import get_default_template_path
            template_path = get_default_template_path()
        except:
            template_path = None

        # Convert with Pandoc
        success = self.pandoc.markdown_to_word(
            temp_md,
            output_path,
            reference_doc=template_path,
        )

        # Cleanup temp file
        temp_md.unlink(missing_ok=True)

        if success:
            return output_path

        # Fallback to Unicode
        logger.warning("Pandoc conversion failed, using Unicode approximation")
        return self.write_with_formulas(
            content, output_path, 'docx', 'unicode'
        )

    def _convert_to_unicode(self, content: str) -> str:
        """Convert LaTeX formulas to Unicode approximations."""
        formulas = self.latex_processor.extract_formulas(content)

        # Sort by position (reverse) to replace without affecting positions
        formulas.sort(key=lambda x: x[2], reverse=True)

        result = content
        for formula, formula_type, start, end in formulas:
            unicode_formula = self.latex_processor.to_word_omath(formula)
            result = result[:start] + unicode_formula + result[end:]

        return result


def enhance_with_latex(content: str, output_path: Path, format: str = 'docx') -> Path:
    """
    Convenience function to write content with LaTeX support.

    Args:
        content: Content with LaTeX formulas
        output_path: Output file path
        format: Output format

    Returns:
        Path to output file
    """
    writer = FormulaWriter(use_pandoc=True)
    return writer.write_with_formulas(content, output_path, format)


def check_pandoc_installation() -> dict:
    """Check Pandoc installation and capabilities."""
    pandoc = PandocConverter()

    result = {
        'available': pandoc.is_available(),
        'path': pandoc.pandoc_path,
        'version': None,
        'pdf_support': False,
    }

    if result['available']:
        try:
            version_result = subprocess.run(
                [pandoc.pandoc_path, '--version'],
                capture_output=True,
                text=True,
            )
            result['version'] = version_result.stdout.split('\n')[0]

            # Check for LaTeX
            latex_available = shutil.which('xelatex') is not None
            result['pdf_support'] = latex_available

        except Exception as e:
            logger.warning(f"Failed to get Pandoc info: {e}")

    return result
