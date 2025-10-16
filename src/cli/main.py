"""Main CLI entry point."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .generate_command import generate_article_command
from .validate_command import validate_article_command
from .build_command import build_knowledge_base_command
from ..utils.logging_config import setup_logging
from config.settings import get_settings


console = Console()


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--log-file', type=click.Path(), help='Log file path')
@click.pass_context
def main(ctx, debug, log_file):
    """AI Document Auditing System - Generate and validate articles with confidence scoring."""
    
    # Initialize settings
    settings = get_settings()
    
    # Setup logging
    log_level = "DEBUG" if debug else settings.log_level
    setup_logging(log_level=log_level, log_file=log_file)
    
    # Store settings in context
    ctx.ensure_object(dict)
    ctx.obj['settings'] = settings
    
    # Display welcome message
    if not ctx.invoked_subcommand:
        display_welcome()


def display_welcome():
    """Display welcome message."""
    welcome_text = Text()
    welcome_text.append("AI Document Auditing System", style="bold blue")
    welcome_text.append("\n\n", style="white")
    welcome_text.append("Generate articles from knowledge bases and validate citations with confidence scoring.\n\n", style="white")
    welcome_text.append("Commands:", style="bold green")
    welcome_text.append("\n  build     - Build knowledge base from document folder", style="white")
    welcome_text.append("\n  generate  - Generate an article from a knowledge base", style="white")
    welcome_text.append("\n  validate  - Validate citations and context in an article", style="white")
    welcome_text.append("\n\n", style="white")
    welcome_text.append("Use --help with any command for more information.", style="italic white")
    
    panel = Panel(
        welcome_text,
        title="[bold blue]Welcome[/bold blue]",
        border_style="blue",
        padding=(1, 2)
    )
    
    console.print(panel)


@main.command()
@click.option('--folder', '-f',
              type=click.Path(exists=True, path_type=str),
              required=True,
              help='Path to folder containing documents')
@click.option('--output', '-o',
              type=click.Path(path_type=str),
              help='Output file path for the knowledge base JSON')
@click.option('--extensions', '-e',
              help='Comma-separated list of file extensions to include (e.g., pdf,docx,txt)')
@click.option('--exclude', '-x',
              help='Comma-separated list of patterns to exclude (e.g., *draft*,*temp*)')
@click.option('--max-size', '-s',
              type=int,
              default=500 * 1024 * 1024,  # 500MB
              help='Maximum file size in bytes (default: 500MB)')
@click.option('--no-recursive', is_flag=True,
              help='Do not search subdirectories recursively')
@click.option('--force-update', is_flag=True,
              help='Force update existing knowledge base')
@click.option('--allow-large-files', is_flag=True,
              help='Allow processing of very large files (>200MB) with warnings')
@click.pass_context
def build(ctx, folder, output, extensions, exclude, max_size, no_recursive, force_update, allow_large_files):
    """Build knowledge base from document folder."""
    build_knowledge_base_command(
        ctx=ctx,
        folder_path=folder,
        output=output,
        extensions=extensions,
        exclude=exclude,
        max_size=max_size,
        recursive=not no_recursive,
        force_update=force_update,
        allow_large_files=allow_large_files
    )


@main.command()
@click.option('--knowledge-base', '-kb', 
              type=click.Path(exists=True, path_type=str),
              required=True,
              help='Path to knowledge base JSON file')
@click.option('--topic', '-t',
              required=True,
              help='Topic for the article')
@click.option('--output', '-o',
              type=click.Path(path_type=str),
              help='Output file path for the generated article')
@click.option('--length', '-l',
              type=click.Choice(['short', 'medium', 'long']),
              default='medium',
              help='Article length')
@click.option('--style', '-s',
              type=click.Choice(['academic', 'journalistic', 'technical']),
              default='academic',
              help='Writing style')
@click.option('--max-sources', '-ms',
              type=int,
              default=10,
              help='Maximum number of sources to use')
@click.option('--no-citations', is_flag=True,
              help='Generate article without citations')
@click.pass_context
def generate(ctx, knowledge_base, topic, output, length, style, max_sources, no_citations):
    """Generate an article from a knowledge base."""
    generate_article_command(
        ctx=ctx,
        knowledge_base=knowledge_base,
        topic=topic,
        output=output,
        length=length,
        style=style,
        max_sources=max_sources,
        no_citations=no_citations
    )


@main.command()
@click.option('--article', '-a',
              type=click.Path(exists=True, path_type=str),
              required=True,
              help='Path to article file to validate (supports PDF, DOCX, DOC, TXT, MD, RTF)')
@click.option('--knowledge-base', '-kb',
              type=click.Path(exists=True, path_type=str),
              required=True,
              help='Path to knowledge base JSON file')
@click.option('--output', '-o',
              type=click.Path(path_type=str),
              help='Output file path for validation results')
@click.option('--confidence-threshold', '-ct',
              type=float,
              default=0.8,
              help='Confidence threshold for validation')
@click.option('--detailed-report', is_flag=True,
              help='Generate detailed validation report')
@click.pass_context
def validate(ctx, article, knowledge_base, output, confidence_threshold, detailed_report):
    """Validate citations and context in an article."""
    validate_article_command(
        ctx=ctx,
        article=article,
        knowledge_base=knowledge_base,
        output=output,
        confidence_threshold=confidence_threshold,
        detailed_report=detailed_report
    )


if __name__ == '__main__':
    main()
