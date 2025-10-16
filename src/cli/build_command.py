"""Knowledge base build command implementation."""

import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from ..utils.knowledge_base_builder import KnowledgeBaseBuilder
from config.settings import get_settings


console = Console()


def build_knowledge_base_command(
    ctx,
    folder_path: str,
    output: str,
    extensions: str,
    exclude: str,
    max_size: int,
    recursive: bool,
    force_update: bool,
    allow_large_files: bool
):
    """Build knowledge base from document folder."""
    
    settings = ctx.obj['settings']
    
    try:
        # Display build parameters
        display_build_info(folder_path, output, extensions, exclude, max_size, recursive)
        
        # Parse extensions and exclusions
        include_extensions = None
        if extensions:
            include_extensions = [f".{ext.strip().lstrip('.')}" for ext in extensions.split(',')]
        
        exclude_patterns = None
        if exclude:
            exclude_patterns = [pattern.strip() for pattern in exclude.split(',')]
        
        # Adjust max_size if large files are allowed
        if allow_large_files and max_size == 500 * 1024 * 1024:  # Default value
            max_size = 2 * 1024 * 1024 * 1024  # 2GB for large files
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Initialize builder
            task1 = progress.add_task("Initializing knowledge base builder...", total=None)
            builder = KnowledgeBaseBuilder()
            progress.update(task1, description="Knowledge base builder initialized ✓")
            
            # Set output path
            if output:
                output_path = Path(output)
            else:
                # Generate default filename
                folder_name = Path(folder_path).name
                safe_name = "".join(c for c in folder_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_name = safe_name.replace(' ', '_').lower()
                output_path = settings.kb_dir / f"{safe_name}_kb.json"
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Get folder statistics first
            task2 = progress.add_task("Analyzing folder contents...", total=None)
            try:
                stats = builder.get_folder_statistics(folder_path)
                progress.update(task2, description=f"Found {stats['total_files']} files, {stats['supported_files']} supported ✓")
            except Exception as e:
                progress.update(task2, description=f"Analysis failed: {e}")
                stats = {'total_files': 0, 'supported_files': 0}
            
            # Build knowledge base
            task3 = progress.add_task("Building knowledge base...", total=None)
            
            if force_update or not output_path.exists():
                metadata = builder.build_from_folder(
                    folder_path=folder_path,
                    output_path=output_path,
                    include_extensions=include_extensions,
                    exclude_patterns=exclude_patterns,
                    max_file_size=max_size,
                    recursive=recursive
                )
            else:
                metadata = builder.update_knowledge_base(
                    knowledge_base_path=output_path,
                    folder_path=folder_path,
                    force_update=force_update
                )
            
            progress.update(task3, description="Knowledge base built ✓")
        
        # Display results
        display_build_results(metadata, output_path, stats)
        
    except Exception as e:
        console.print(f"[bold red]Error building knowledge base:[/bold red] {e}")
        raise click.Abort()


def display_build_info(folder_path: str, output: str, extensions: str, exclude: str, max_size: int, recursive: bool):
    """Display build parameters."""
    
    info_table = Table(title="Knowledge Base Build Parameters", show_header=True, header_style="bold blue")
    info_table.add_column("Parameter", style="cyan", no_wrap=True)
    info_table.add_column("Value", style="white")
    
    info_table.add_row("Source Folder", folder_path)
    info_table.add_row("Output", output or "Auto-generated")
    info_table.add_row("Extensions", extensions or "All supported")
    info_table.add_row("Exclude Patterns", exclude or "None")
    info_table.add_row("Max File Size", f"{max_size / (1024 * 1024):.0f} MB")
    info_table.add_row("Recursive Search", "Yes" if recursive else "No")
    
    console.print(info_table)
    console.print()


def display_build_results(metadata, output_path: Path, folder_stats):
    """Display build results."""
    
    # Build statistics
    build_stats = metadata.get('build_stats', {})
    
    stats_table = Table(title="Build Statistics", show_header=True, header_style="bold green")
    stats_table.add_column("Metric", style="cyan", no_wrap=True)
    stats_table.add_column("Value", style="white")
    
    stats_table.add_row("Total Documents Found", str(build_stats.get('total_documents_found', 0)))
    stats_table.add_row("Successfully Processed", str(build_stats.get('successfully_processed', 0)))
    stats_table.add_row("Errors", str(build_stats.get('errors', 0)))
    stats_table.add_row("Total Entries Created", str(metadata.get('total_entries', 0)))
    
    console.print(stats_table)
    
    # File type statistics
    file_type_stats = build_stats.get('file_type_statistics', {})
    if file_type_stats:
        type_table = Table(title="File Type Statistics", show_header=True, header_style="bold yellow")
        type_table.add_column("Extension", style="cyan", no_wrap=True)
        type_table.add_column("Count", style="white")
        type_table.add_column("Successful", style="green")
        type_table.add_column("Failed", style="red")
        type_table.add_column("Total Size", style="white")
        
        for ext, stats in sorted(file_type_stats.items()):
            size_mb = stats['total_size'] / (1024 * 1024)
            type_table.add_row(
                ext or "No extension",
                str(stats['count']),
                str(stats['successful']),
                str(stats['failed']),
                f"{size_mb:.1f} MB"
            )
        
        console.print()
        console.print(type_table)
    
    # Summary
    summary_info = f"""
Knowledge Base: {metadata.get('title', 'Unknown')}
Total Entries: {metadata.get('total_entries', 0)}
Source Folder: {metadata.get('source_folder', 'Unknown')}
Created: {metadata.get('created_at', 'Unknown')}
Version: {metadata.get('version', 'Unknown')}
    """.strip()
    
    summary_panel = Panel(
        summary_info,
        title="[bold blue]Knowledge Base Summary[/bold blue]",
        border_style="blue",
        padding=(1, 2)
    )
    
    console.print()
    console.print(summary_panel)
    
    console.print()
    console.print(f"[bold green]✓ Knowledge base built successfully![/bold green]")
    console.print(f"[dim]Knowledge base saved to: {output_path}[/dim]")
    
    if build_stats.get('errors', 0) > 0:
        console.print(f"[bold yellow]⚠ {build_stats['errors']} file(s) could not be processed[/bold yellow]")


def display_usage_examples():
    """Display usage examples."""
    
    examples_text = Text()
    examples_text.append("Usage Examples:\n", style="bold green")
    
    examples_text.append("1. Build knowledge base from folder:\n", style="bold")
    examples_text.append("   python -m src.cli.main build -f documents/\n\n")
    
    examples_text.append("2. Specify output file:\n", style="bold")
    examples_text.append("   python -m src.cli.main build -f documents/ -o my_kb.json\n\n")
    
    examples_text.append("3. Include only specific file types:\n", style="bold")
    examples_text.append("   python -m src.cli.main build -f documents/ -e pdf,docx,txt\n\n")
    
    examples_text.append("4. Exclude certain patterns:\n", style="bold")
    examples_text.append("   python -m src.cli.main build -f documents/ -x '*draft*,*temp*'\n\n")
    
    examples_text.append("5. Process large files:\n", style="bold")
    examples_text.append("   python -m src.cli.main build -f documents/ --allow-large-files\n\n")
    
    examples_text.append("6. Force update existing knowledge base:\n", style="bold")
    examples_text.append("   python -m src.cli.main build -f documents/ --force-update\n\n")
    
    examples_panel = Panel(
        examples_text,
        title="[bold blue]Knowledge Base Build Examples[/bold blue]",
        border_style="blue",
        padding=(1, 2)
    )
    
    console.print(examples_panel)