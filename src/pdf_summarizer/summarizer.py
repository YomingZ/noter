"""Core summarization orchestrator — thin coordinator over sub-modules."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from tqdm import tqdm

from pdf_summarizer.models import (
    AIProvider,
    PDFDocument,
    ProcessResult,
    BatchResult,
    ContentPart,
)
from pdf_summarizer.pdf_reader import PDFExtractor
from pdf_summarizer.ai_client import (
    generate_summary,
    generate_multimodal_summary,
    create_client,
    BaseAIClient,
)
from pdf_summarizer.docx_writer import DocxWriter
from pdf_summarizer.output_formats import write_summary
from pdf_summarizer.config import config
from pdf_summarizer.chunking import ChapterChunker, PageChunker
from pdf_summarizer.summary_parser import SummaryParser
from pdf_summarizer.obsidian_generator import ObsidianNoteGenerator

logger = logging.getLogger(__name__)

CHARS_PER_TOKEN = 1.5

MODEL_TOKEN_LIMITS = {
    "moonshot-v1-8k": 6000,
    "moonshot-v1-32k": 28000,
    "moonshot-v1-128k": 100000,
    "gpt-4o": 120000,
    "gpt-4o-mini": 120000,
    "claude-sonnet-4-6-20250514": 180000,
    "claude-opus-4-7": 180000,
}


class Summarizer:
    """Thin orchestrator: reads PDF → delegates to sub-modules → writes output."""

    def __init__(
        self,
        provider: AIProvider = AIProvider.OPENAI,
        output_dir: Optional[Path] = None,
        max_chunk_tokens: Optional[int] = None,
        template_path: Optional[Path] = None,
        subject: Optional[str] = None,
        ai_client: Optional[BaseAIClient] = None,
    ):
        self.provider = provider
        self.output_dir = output_dir or config.ensure_output_dir()
        self.pdf_reader = PDFExtractor(extract_images=True)
        self.docx_writer = DocxWriter(template_path=template_path)
        self.max_chunk_tokens = max_chunk_tokens
        self.template_path = template_path
        self.subject = subject
        self._detected_subject: Optional[str] = None

        max_tokens = self._get_max_content_tokens()
        self.parser = SummaryParser()
        self.chapter_chunker = ChapterChunker(max_tokens=max_tokens)
        self.page_chunker = PageChunker(max_tokens=max_tokens)

        if ai_client is not None:
            self._ai_client = ai_client
        else:
            self._ai_client = create_client(provider)

        self.obsidian_generator = ObsidianNoteGenerator(
            ai_generate_fn=self._ai_generate,
            max_content_tokens=max_tokens,
        )

    def _get_max_content_tokens(self) -> int:
        if self.max_chunk_tokens:
            return self.max_chunk_tokens
        model = self._get_model_name()
        for key, limit in MODEL_TOKEN_LIMITS.items():
            if key in model:
                return limit
        return 6000

    def _get_model_name(self) -> str:
        ai_config = config.get_ai_config(self.provider)
        return ai_config.get("model", "")

    def _ai_generate(self, system_prompt: str, user_prompt: str,
                     use_cache: bool = True, max_tokens: Optional[int] = None) -> str:
        if max_tokens is not None:
            old_max = self._ai_client.max_tokens
            self._ai_client.max_tokens = max_tokens
            try:
                return self._ai_client.generate(system_prompt, user_prompt, use_cache=use_cache)
            finally:
                self._ai_client.max_tokens = old_max
        return self._ai_client.generate(system_prompt, user_prompt, use_cache=use_cache)

    def _build_multimodal_parts(self, document: PDFDocument) -> list[ContentPart]:
        """Build ContentPart list with text and images for multimodal AI.

        Includes page images when available and the model supports vision.
        """
        parts: list[ContentPart] = []

        full_text = document.get_full_text()
        text_with_tables = full_text

        parts.append(ContentPart(
            type="text",
            text=text_with_tables,
        ))

        if self._ai_client.supports_vision() and document.has_images():
            for page in document.pages:
                for b64_img in page.images_base64:
                    parts.append(ContentPart(
                        type="image",
                        image_base64=b64_img,
                    ))

        return parts

    def process(
        self,
        pdf_path: Path,
        output_name: Optional[str] = None,
        use_cache: bool = True,
        output_format: str = "docx",
        template_path: Optional[Path] = None,
        course_name: Optional[str] = None,
        vault_root: Optional[Path] = None,
    ) -> ProcessResult:
        pdf_path = Path(pdf_path)
        result = ProcessResult(input_file=pdf_path)

        try:
            logger.info("Processing: %s", pdf_path)
            document = self.pdf_reader.read(pdf_path)
            result.pages_processed = len(document.pages)

            if not document.pages:
                raise ValueError("No valid pages extracted from PDF")

            if output_format == "obsidian":
                return self.obsidian_generator.generate(
                    document=document,
                    template_path=template_path,
                    course_name=course_name,
                    vault_root=vault_root,
                    output_name=output_name,
                    use_cache=use_cache,
                )

            if self.subject:
                self._detected_subject = self.subject
            else:
                self._detected_subject = config.detect_subject(document.get_full_text())

            if self._detected_subject and self._detected_subject != "default":
                logger.info("Using subject-specific prompts for: %s", self._detected_subject)

            logger.info("Generating summary using %s...", self.provider.value)

            raw_response = self._generate_with_chunking(document, use_cache)

            model_name = self._get_model_name()
            summary = self.parser.parse(document.file_name, raw_response)

            summary.metadata = {
                'title': pdf_path.stem,
                'source': document.file_name,
                'pages': len(document.pages),
                'chapters': len(document.chapters) if document.chapters else 0,
                'model': model_name,
                'provider': self.provider.value,
                'subject': self._detected_subject,
            }

            output_name = output_name or pdf_path.stem
            ext = {"md": ".md", "markdown": ".md", "html": ".html", "docx": ".docx"}.get(output_format, ".docx")
            output_file = self.output_dir / f"{output_name}_笔记{ext}"
            write_summary(summary, output_file, format=output_format)

            result.output_file = output_file
            result.success = True
            logger.info("Summary saved to: %s", output_file)

        except Exception as e:
            result.success = False
            result.error_message = str(e)
            logger.error("Failed to process %s: %s", pdf_path, e)

        return result

    def _generate_with_chunking(self, document: PDFDocument, use_cache: bool = True) -> str:
        full_text = document.get_full_text()
        estimated_tokens = len(full_text) / CHARS_PER_TOKEN
        max_tokens = self._get_max_content_tokens()

        user_prompt = None
        if self._detected_subject and self._detected_subject != "default":
            user_prompt = config.get_subject_prompt(self._detected_subject)

        has_images = document.has_images()
        supports_vision = self._ai_client.supports_vision()
        use_multimodal = has_images and supports_vision

        if estimated_tokens <= max_tokens:
            if use_multimodal:
                content_parts = self._build_multimodal_parts(document)
                logger.info("Using multimodal generation with %d parts", len(content_parts))
                return generate_multimodal_summary(
                    content_parts=content_parts,
                    provider=self.provider,
                    use_cache=use_cache,
                )
            return generate_summary(
                content=full_text,
                provider=self.provider,
                use_cache=use_cache,
                user_prompt=user_prompt,
            )

        if use_multimodal:
            logger.info(
                "Content too large for multimodal (%.0f tokens), falling back to text-only",
                estimated_tokens,
            )

        logger.info(
            "Content too large (%.0f tokens), chunking with max %d tokens...",
            estimated_tokens, max_tokens,
        )

        chunker = self._select_chunker(document)
        chunks = chunker.split(document)

        partial_summaries = []
        for chunk in chunks:
            summary = chunker._summarize_chunk(chunk, self._ai_generate)
            partial_summaries.append(summary)

        if len(partial_summaries) == 1:
            return partial_summaries[0]

        logger.info("Merging %d partial summaries...", len(partial_summaries))
        return chunker.merge(partial_summaries, ai_generate_fn=self._ai_generate)

    def _select_chunker(self, document: PDFDocument):
        if document.chapters:
            return self.chapter_chunker
        return self.page_chunker

    def process_batch(
        self,
        directory: Path,
        recursive: bool = False,
        show_progress: bool = True,
        incremental: bool = True,
        output_format: str = "docx",
    ) -> BatchResult:
        from pdf_summarizer.incremental import IncrementalProcessor

        directory = Path(directory)
        if not directory.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")

        pattern = "**/*.pdf" if recursive else "*.pdf"
        pdf_files = sorted(directory.glob(pattern))

        if not pdf_files:
            logger.warning("No PDF files found in: %s", directory)
            return BatchResult()

        logger.info("Found %d PDF files in %s", len(pdf_files), directory)

        incremental_proc = IncrementalProcessor() if incremental else None

        if incremental_proc:
            to_process, already_done = incremental_proc.filter_new_files(pdf_files)
        else:
            to_process = pdf_files
            already_done = []

        batch_result = BatchResult()

        for pdf_file in already_done:
            existing_output = incremental_proc.get_output_path(pdf_file)
            batch_result.add_result(ProcessResult(
                input_file=pdf_file,
                output_file=existing_output,
                success=True,
                skipped=True,
            ))

        if not to_process:
            logger.info("All files already processed (incremental mode)")
            return batch_result

        error_log_path = self.output_dir / f"errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        iterator = tqdm(
            to_process,
            desc="Processing PDFs",
            disable=not show_progress,
            unit="file",
        )

        for pdf_file in iterator:
            iterator.set_postfix_str(pdf_file.name[:20])

            try:
                result = self.process(pdf_file, output_format=output_format)

                if incremental_proc and result.success and result.output_file:
                    incremental_proc.mark_processed(pdf_file, result.output_file)

            except Exception as e:
                result = ProcessResult(
                    input_file=pdf_file,
                    success=False,
                    error_message=str(e),
                )
                self._log_error(error_log_path, pdf_file, str(e))

            batch_result.add_result(result)

        logger.info(
            "Batch processing complete: %d succeeded, %d failed, %d skipped",
            batch_result.successful, batch_result.failed, batch_result.skipped,
        )

        if batch_result.failed > 0:
            logger.warning("Error log saved to: %s", error_log_path)

        return batch_result

    @staticmethod
    def _log_error(log_path: Path, pdf_file: Path, error_message: str):
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {pdf_file}\n")
            f.write(f"  Error: {error_message}\n\n")
