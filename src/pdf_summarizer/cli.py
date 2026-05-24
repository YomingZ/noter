"""Command-line interface for PDF Summarizer."""

import logging
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from pdf_summarizer import __version__
from pdf_summarizer.models import AIProvider, BatchResult
from pdf_summarizer.summarizer import Summarizer
from pdf_summarizer.config import config
from pdf_summarizer.cli_wizard import _run_config_wizard

app = typer.Typer(
    name="pdf-summarizer",
    help="PDF课件智能总结工具 - 使用AI提取重点知识并生成Word备考笔记",
)
console = Console()


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def version_callback(value: bool):
    """Show version and exit."""
    if value:
        console.print(f"[bold blue]pdf-summarizer[/] version: {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=version_callback,
        help="Show version and exit.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Enable verbose logging.",
    ),
):
    """PDF Summarizer - PDF课件智能总结工具"""
    setup_logging(verbose)


@app.command()
def process(
    pdf_path: Path = typer.Argument(
        ...,
        help="PDF文件路径",
        exists=True,
    ),
    provider: str = typer.Option(
        "openai",
        "--provider",
        "-p",
        help="AI提供商: openai, claude, kimi, deepseek",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="输出文件路径",
    ),
    template: Optional[Path] = typer.Option(
        None,
        "--template",
        "-t",
        help="模板文件路径：Word模板(.docx) 或 Obsidian笔记模板(.md)",
        exists=False,
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="禁用缓存，强制重新生成",
    ),
    output_format: str = typer.Option(
        "docx",
        "--format",
        "-f",
        help="输出格式: docx, md, html, obsidian",
    ),
    course_name: Optional[str] = typer.Option(
        None,
        "--course",
        "-c",
        help="课程名称（obsidian 模式必填，用于匹配 vault 中的课程文件夹）",
    ),
    vault_root: Optional[Path] = typer.Option(
        None,
        "--vault",
        "-v",
        help="Obsidian vault 根目录路径（obsidian 模式必填）",
        exists=False,
    ),
    latex: bool = typer.Option(
        False,
        "--latex",
        help="启用 LaTeX 公式渲染（使用 Pandoc，仅 docx 模式）",
    ),
):
    """处理单个PDF文件并生成总结笔记。"""
    try:
        ai_provider = AIProvider(provider)
    except ValueError:
        console.print(f"[red]错误: 不支持的AI提供商 '{provider}'[/]")
        console.print("支持的提供商: openai, claude, kimi, deepseek")
        raise typer.Exit(1)

    # Validate obsidian-specific params
    if output_format == "obsidian":
        errors = []
        if not template:
            errors.append("obsidian 模式需要 --template（笔记模板 .md 文件）")
        if not course_name:
            errors.append("obsidian 模式需要 --course（课程名称）")
        if not vault_root:
            errors.append("obsidian 模式需要 --vault（Obsidian vault 路径）")
        if errors:
            console.print("[red]参数错误:[/]")
            for e in errors:
                console.print(f"  • {e}")
            raise typer.Exit(1)
        if template and not template.exists():
            console.print(f"[red]错误: 模板文件不存在: {template}[/]")
            raise typer.Exit(1)

    # Check template (Word docx mode)
    if template and output_format != "obsidian" and not template.exists():
        console.print(f"[yellow]警告: 模板文件不存在: {template}[/]")
        console.print("[yellow]将使用默认样式[/]")
        template = None

    # Check Pandoc for LaTeX
    if latex:
        from pdf_summarizer.latex_renderer import check_pandoc_installation
        pandoc_info = check_pandoc_installation()
        if not pandoc_info['available']:
            console.print("[yellow]警告: 未安装 Pandoc，LaTeX 渲染不可用[/]")
            console.print("[yellow]将使用 Unicode 近似替代[/]")
            latex = False

    summarizer = Summarizer(
        provider=ai_provider,
        template_path=template if output_format != "obsidian" else None,
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("正在处理PDF...", total=None)

        result = summarizer.process(
            pdf_path=pdf_path,
            output_name=output.stem if output else None,
            use_cache=not no_cache,
            output_format=output_format,
            template_path=template if output_format == "obsidian" else None,
            course_name=course_name if output_format == "obsidian" else None,
            vault_root=vault_root if output_format == "obsidian" else None,
        )

        # Handle LaTeX rendering
        if result.success and latex and output_format == 'docx':
            progress.update(task, description="渲染 LaTeX 公式...")
            from pdf_summarizer.latex_renderer import FormulaWriter

            # Read the generated content and re-render
            writer = FormulaWriter(use_pandoc=True)

            # Get the summary content
            from pdf_summarizer.output_formats import MarkdownWriter
            from pdf_summarizer.models import SummaryOutput

            # Create a temp summary with raw response
            temp_summary = SummaryOutput(
                source_file=result.input_file.name,
                raw_response=result.output_file.read_text(encoding='utf-8') if result.output_file else "",
            )

            # Write with LaTeX support
            md_path = result.output_file.with_suffix('.md')
            MarkdownWriter().write(temp_summary, md_path)
            writer.write_with_formulas(
                md_path.read_text(encoding='utf-8'),
                result.output_file,
                format='docx',
            )
            md_path.unlink(missing_ok=True)

    if result.success:
        console.print("[green]✓ 处理完成![/]")
        console.print(f"  输入: {result.input_file}")
        console.print(f"  输出: {result.output_file}")
        console.print(f"  处理页数: {result.pages_processed}")
        if output_format == "obsidian":
            console.print("  [dim]💡 打开 Obsidian 即可查看[/]")
        if latex:
            console.print(f"  [dim]LaTeX 公式已渲染[/]")
    else:
        console.print(f"[red]✗ 处理失败: {result.error_message}[/]")
        raise typer.Exit(1)


@app.command()
def batch(
    directory: Path = typer.Argument(
        ...,
        help="包含PDF文件的目录路径",
        exists=True,
    ),
    provider: str = typer.Option(
        "openai",
        "--provider",
        "-p",
        help="AI提供商: openai, claude, kimi, deepseek",
    ),
    recursive: bool = typer.Option(
        False,
        "--recursive",
        "-r",
        help="递归处理子目录",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="输出目录（默认: ./output）",
    ),
    output_format: str = typer.Option(
        "docx",
        "--format",
        "-f",
        help="输出格式: docx, md, html（obsidian 暂不支持批量模式）",
    ),
    incremental: bool = typer.Option(
        True,
        "--incremental/--full",
        help="增量处理（跳过已处理的文件）",
    ),
    subject: Optional[str] = typer.Option(
        None,
        "--subject",
        "-s",
        help="指定学科: math, physics, computer, economics, language, law, medicine",
    ),
    no_progress: bool = typer.Option(
        False,
        "--no-progress",
        help="禁用进度条",
    ),
):
    """批量处理目录中的所有PDF文件。"""
    try:
        ai_provider = AIProvider(provider)
    except ValueError:
        console.print(f"[red]错误: 不支持的AI提供商 '{provider}'[/]")
        console.print("支持的提供商: openai, claude, kimi, deepseek")
        raise typer.Exit(1)

    if output_format == "obsidian":
        console.print("[red]batch 模式暂不支持 obsidian 格式。[/]")
        console.print("请使用单文件模式：pdf-summarizer process <file.pdf> -f obsidian ...")
        raise typer.Exit(1)

    summarizer = Summarizer(
        provider=ai_provider,
        output_dir=output_dir,
        subject=subject,
    )

    console.print(f"[blue]扫描目录: {directory}[/]")
    if recursive:
        console.print("[blue]模式: 递归处理子目录[/]")
    if incremental:
        console.print("[blue]模式: 增量处理（跳过已处理文件）[/]")
    if output_format != "docx":
        console.print(f"[blue]输出格式: {output_format}[/]")

    batch_result = summarizer.process_batch(
        directory,
        recursive=recursive,
        show_progress=not no_progress,
        incremental=incremental,
        output_format=output_format,
    )

    # Show results table
    console.print()

    if batch_result.total_files == 0:
        console.print("[yellow]未找到需要处理的 PDF 文件[/]")
        return

    table = Table(title=f"处理结果 (成功: {batch_result.successful}, 失败: {batch_result.failed}, 跳过: {batch_result.skipped})")
    table.add_column("状态", width=8)
    table.add_column("文件名", style="cyan")
    table.add_column("页数", justify="right")
    table.add_column("输出/错误", style="dim")

    for result in batch_result.results:
        if result.success:
            status = "[green]✓ 成功[/]"
            output = str(result.output_file.name) if result.output_file else "-"
            pages = str(result.pages_processed)
        elif result.skipped:
            status = "[dim]○ 跳过[/]"
            output = "已处理"
            pages = "-"
        else:
            status = "[red]✗ 失败[/]"
            output = result.error_message[:40] + "..." if result.error_message and len(result.error_message) > 40 else result.error_message or "Unknown error"
            pages = "-"

        table.add_row(status, result.input_file.name, pages, output)

    console.print(table)

    # Summary
    if batch_result.failed > 0:
        console.print(f"\n[yellow]⚠ {batch_result.failed} 个文件处理失败，请查看 output 目录中的错误日志[/]")
    else:
        console.print(f"\n[green]✓ 全部处理完成！[/]")

    console.print(f"[dim]输出目录: {summarizer.output_dir}[/]")


@app.command("config")
def config_check(
    setup: bool = typer.Option(
        False,
        "--setup",
        "-s",
        help="启动交互式配置向导",
    ),
):
    """检查配置状态或启动配置向导。"""
    if setup:
        _run_config_wizard()
        return

    settings = config.settings

    table = Table(title="API 配置状态")
    table.add_column("提供商", style="cyan")
    table.add_column("API Key", style="green")
    table.add_column("模型", style="blue")
    table.add_column("状态", style="yellow")

    # Check API keys
    providers = [
        ("OpenAI", settings.openai_api_key, settings.openai_model),
        ("Claude", settings.anthropic_api_key, settings.anthropic_model),
        ("Kimi", settings.kimi_api_key, settings.kimi_model),
        ("DeepSeek", settings.deepseek_api_key, settings.deepseek_model),
    ]

    for name, key, model in providers:
        status = "[green]✓ 已配置[/]" if key else "[red]✗ 未配置[/]"
        key_display = f"{key[:8]}..." if key and len(key) > 8 else key or "N/A"
        table.add_row(name, key_display, model, status)

    console.print(table)

    # Show rate limiter and cache stats
    try:
        from pdf_summarizer.ai_client import get_provider_stats
        stats = get_provider_stats()

        # Cache stats
        cache_stats = stats.get('cache', {})
        console.print(f"\n[bold]缓存状态[/]")
        console.print(f"  目录: {cache_stats.get('cache_dir', 'N/A')}")
        console.print(f"  条目数: {cache_stats.get('total_entries', 0)}")
        console.print(f"  大小: {cache_stats.get('total_size_mb', 0)} MB")

    except Exception as e:
        console.print(f"\n[yellow]无法获取缓存状态: {e}[/]")

    console.print(f"\n默认提供商: [bold]{settings.default_provider}[/]")
    console.print(f"输出目录: [bold]{settings.output_directory}[/]")
    console.print(f"\n[dim]提示: 使用 --setup 参数启动配置向导[/]")


@app.command()
def cache(
    action: str = typer.Argument(
        "stats",
        help="操作: stats(统计), clear(清空), expire(清理过期)",
    ),
):
    """管理缓存。"""
    from pdf_summarizer.cache import CacheManager, get_cache
    from pdf_summarizer.ai_client import get_provider_stats

    cache_manager = get_cache()

    if action == "stats":
        stats = get_provider_stats()
        cache_stats = stats.get('cache', {})

        table = Table(title="缓存统计")
        table.add_column("项目", style="cyan")
        table.add_column("值", style="green")
        table.add_row("缓存目录", str(cache_stats.get('cache_dir', 'N/A')))
        table.add_row("缓存条目", str(cache_stats.get('total_entries', 0)))
        table.add_row("缓存大小", f"{cache_stats.get('total_size_mb', 0)} MB")

        console.print(table)

        # Rate limiter stats
        rate_stats = stats.get('rate_limits', {})
        if rate_stats:
            console.print("\n[bold]请求统计[/]")
            for provider, data in rate_stats.items():
                console.print(f"  {provider}: {data.get('total_requests', 0)} 次请求, 等待 {data.get('total_wait_time', 0)}s")

    elif action == "clear":
        import shutil
        cache_dir = cache_manager.cache_dir
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
            console.print(f"[green]✓ 已清空缓存目录: {cache_dir}[/]")
        else:
            console.print("[yellow]缓存目录不存在[/]")

    elif action == "expire":
        removed = cache_manager.clear_expired()
        console.print(f"[green]✓ 已清理 {removed} 个过期缓存[/]")

    else:
        console.print(f"[red]未知操作: {action}[/]")
        console.print("支持的操作: stats, clear, expire")


@app.command()
def analyze(
    exam_dir: Path = typer.Argument(
        ...,
        help="包含往届考题 PDF 的目录",
        exists=True,
    ),
    course_pdf: Optional[Path] = typer.Option(
        None,
        "--course",
        "-c",
        help="课程课件 PDF（用于知识点关联）",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="输出文件路径（默认: ./output/考前预测.md）",
    ),
):
    """分析往届考题，预测考点。"""
    from pdf_summarizer.exam_analyzer import ExamQuestionAnalyzer
    from pdf_summarizer.pdf_reader import PDFExtractor

    console.print(f"[blue]分析往届考题目录: {exam_dir}[/]")

    analyzer = ExamQuestionAnalyzer()
    extractor = PDFExtractor()

    # Process exam PDFs
    total_questions = 0
    for pdf_file in sorted(exam_dir.glob("*.pdf")):
        console.print(f"  处理: {pdf_file.name}")

        try:
            doc = extractor.read(pdf_file)
            text = doc.get_full_text()

            questions = analyzer.extract_questions_from_text(
                text,
                source=pdf_file.stem,
            )
            total_questions += len(questions)

        except Exception as e:
            console.print(f"  [red]错误: {e}[/]")

    console.print(f"\n[green]✓ 提取了 {total_questions} 道题目[/]")

    # Analyze course content if provided
    if course_pdf:
        console.print(f"\n[blue]分析课程课件: {course_pdf}[/]")

        try:
            doc = extractor.read(course_pdf)
            course_content = doc.get_full_text()

            analyzer.analyze_knowledge_points(course_content)
            analyzer.correlate_questions_with_kp()

        except Exception as e:
            console.print(f"[red]错误: {e}[/]")

    # Generate predictions
    predictions = analyzer.get_exam_prediction(top_n=15)

    if not predictions:
        console.print("[yellow]未能生成预测，请检查考题文件格式[/]")
        return

    # Show predictions table
    table = Table(title="🔥 考前重点预测")
    table.add_column("排名", justify="right", width=4)
    table.add_column("知识点", style="cyan")
    table.add_column("预测分", justify="right")
    table.add_column("考题数", justify="right")
    table.add_column("题型", style="dim")

    for i, pred in enumerate(predictions, 1):
        types_str = ", ".join(pred['question_types'][:2])
        table.add_row(
            str(i),
            pred['knowledge_point'],
            str(pred['score']),
            str(pred['exam_count']),
            types_str,
        )

    console.print(table)

    # Generate study guide
    output_path = output or Path("./output/考前预测.md")
    guide = analyzer.generate_study_guide(course_pdf.stem if course_pdf else "")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(guide)

    console.print(f"\n[green]✓ 学习指南已保存: {output_path}[/]")


@app.command()
def convert(
    input_file: Path = typer.Argument(
        ...,
        help="Markdown 文件路径",
        exists=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="输出文件路径",
    ),
    to_pdf: bool = typer.Option(
        False,
        "--pdf",
        help="转换为 PDF（需要 LaTeX）",
    ),
):
    """使用 Pandoc 转换 Markdown（支持 LaTeX 公式）。"""
    from pdf_summarizer.latex_renderer import PandocConverter, check_pandoc_installation

    # Check Pandoc
    pandoc_info = check_pandoc_installation()

    if not pandoc_info['available']:
        console.print("[red]错误: 未安装 Pandoc[/]")
        console.print("\n安装方法:")
        console.print("  Windows: winget install --id JohnMacFarlane.Pandoc")
        console.print("  Mac: brew install pandoc")
        console.print("  Linux: sudo apt install pandoc")
        raise typer.Exit(1)

    console.print(f"[dim]Pandoc 版本: {pandoc_info['version']}[/]")

    converter = PandocConverter()

    # Determine output path
    if output:
        output_path = output
    elif to_pdf:
        output_path = input_file.with_suffix('.pdf')
    else:
        output_path = input_file.with_suffix('.docx')

    console.print(f"[blue]转换: {input_file} -> {output_path}[/]")

    if to_pdf:
        if not pandoc_info['pdf_support']:
            console.print("[yellow]警告: 未检测到 LaTeX，PDF 转换可能失败[/]")

        success = converter.markdown_to_pdf(input_file, output_path)
    else:
        success = converter.markdown_to_word(input_file, output_path)

    if success:
        console.print(f"[green]✓ 转换成功: {output_path}[/]")
    else:
        console.print("[red]✗ 转换失败[/]")
        raise typer.Exit(1)


@app.command()
def stats(
    history: bool = typer.Option(
        False,
        "--history",
        "-h",
        help="显示历史统计记录",
    ),
    summary: bool = typer.Option(
        False,
        "--summary",
        "-s",
        help="显示总体统计摘要",
    ),
):
    """查看处理统计和成本估算。"""
    from pdf_summarizer.stats import StatsManager

    manager = StatsManager()

    if summary:
        summary_data = manager.get_summary()
        if not summary_data:
            console.print("[yellow]暂无统计数据[/]")
            return

        table = Table(title="总体统计")
        table.add_column("项目", style="cyan")
        table.add_column("值", style="green")

        table.add_row("处理会话数", str(summary_data.get("total_sessions", 0)))
        table.add_row("处理文件数", str(summary_data.get("total_files", 0)))
        table.add_row("处理页数", str(summary_data.get("total_pages", 0)))
        table.add_row("总Token数", f"{summary_data.get('total_tokens', 0):,}")
        table.add_row("累计成本 (USD)", f"${summary_data.get('total_cost_usd', 0):.4f}")
        table.add_row("累计成本 (CNY)", f"¥{summary_data.get('total_cost_cny', 0):.2f}")

        console.print(table)
        return

    if history:
        history_data = manager.get_history(limit=10)
        if not history_data:
            console.print("[yellow]暂无历史记录[/]")
            return

        table = Table(title="历史统计记录")
        table.add_column("时间", style="cyan")
        table.add_column("文件数", justify="right")
        table.add_column("页数", justify="right")
        table.add_column("Token", justify="right")
        table.add_column("成本", style="yellow")

        for h in history_data:
            start = h.get("start_time", "")[:16]
            files = h.get("files_processed", 0)
            pages = h.get("total_pages", 0)
            tokens = h.get("total_tokens_input", 0) + h.get("total_tokens_output", 0)
            cost = h.get("estimated_cost_cny", 0)

            table.add_row(start, str(files), str(pages), f"{tokens:,}", f"¥{cost:.2f}")

        console.print(table)
        return

    # Show usage
    console.print("[bold]统计命令用法：[/]")
    console.print("  pdf-summarizer stats --summary   # 总体统计")
    console.print("  pdf-summarizer stats --history   # 历史记录")


@app.command()
def template(
    output: Path = typer.Option(
        Path("./custom_template.docx"),
        "--output",
        "-o",
        help="模板输出路径",
    ),
):
    """导出 Word 模板文件供自定义。"""
    from pdf_summarizer.default_template import create_default_template

    create_default_template(output)
    console.print(f"[green]✓ 模板已导出: {output}[/]")
    console.print()
    console.print("[bold]使用方法：[/]")
    console.print(f"  1. 用 Word 打开 {output}")
    console.print("  2. 修改样式（字体、颜色、间距等）")
    console.print("  3. 保存文件")
    console.print(f"  4. 使用模板: pdf-summarizer process file.pdf --template {output}")


if __name__ == "__main__":
    app()
