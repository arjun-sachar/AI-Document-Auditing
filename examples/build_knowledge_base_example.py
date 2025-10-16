#!/usr/bin/env python3
"""Example of building knowledge base from document folder."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.knowledge_base_builder import KnowledgeBaseBuilder
from rich.console import Console
from rich.table import Table
from rich.panel import Panel


def example_build_knowledge_base():
    """Example of building knowledge base from documents."""
    
    console = Console()
    
    console.print(Panel(
        "Knowledge Base Builder Example",
        style="bold blue"
    ))
    
    # Initialize builder
    builder = KnowledgeBaseBuilder()
    
    # Example: Build from a folder (replace with your actual folder path)
    folder_path = "White Papers, Studies, POVs, Conference Pres"  # Your folder name
    output_path = "data/knowledge_bases/white_papers_kb.json"
    
    console.print(f"[bold green]Building knowledge base from:[/bold green] {folder_path}")
    
    try:
        # First, get folder statistics
        console.print("\n[bold yellow]Analyzing folder...[/bold yellow]")
        stats = builder.get_folder_statistics(folder_path)
        
        # Display folder statistics
        stats_table = Table(title="Folder Statistics")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="white")
        
        stats_table.add_row("Total Files", f"{stats['total_files']:,}")
        stats_table.add_row("Supported Files", f"{stats['supported_files']:,}")
        stats_table.add_row("Total Size", f"{stats['total_size'] / (1024*1024):.1f} MB")
        stats_table.add_row("Supported Size", f"{stats['supported_size'] / (1024*1024):.1f} MB")
        
        console.print(stats_table)
        
        # Show file types
        if stats['file_types']:
            types_table = Table(title="File Types Found")
            types_table.add_column("Extension", style="cyan")
            types_table.add_column("Count", style="white")
            types_table.add_column("Percentage", style="green")
            
            total_files = stats['total_files']
            for ext, count in sorted(stats['file_types'].items()):
                percentage = (count / total_files * 100) if total_files > 0 else 0
                types_table.add_row(
                    ext if ext else "no extension",
                    str(count),
                    f"{percentage:.1f}%"
                )
            
            console.print(types_table)
        
        # Build knowledge base
        console.print("\n[bold yellow]Building knowledge base...[/bold yellow]")
        
        build_stats = builder.build_from_folder(
            folder_path=folder_path,
            output_path=output_path,
            include_extensions=['.pdf', '.docx', '.doc', '.txt', '.md'],  # Focus on main formats
            exclude_patterns=['*draft*', '*temp*', '*backup*'],  # Exclude drafts
            max_file_size=50 * 1024 * 1024,  # 50MB limit
            recursive=True
        )
        
        # Display build results
        results_table = Table(title="Build Results")
        results_table.add_column("Metric", style="cyan")
        results_table.add_column("Value", style="white")
        
        results_table.add_row("Documents Found", str(build_stats['build_stats']['total_documents_found']))
        results_table.add_row("Successfully Processed", str(build_stats['build_stats']['successfully_processed']))
        results_table.add_row("Errors", str(build_stats['build_stats']['errors']))
        results_table.add_row("Knowledge Base Entries", str(build_stats['total_entries']))
        
        console.print(results_table)
        
        console.print(f"\n[bold green]✓ Knowledge base built successfully![/bold green]")
        console.print(f"[dim]Output saved to: {output_path}[/dim]")
        
        # Show usage example
        usage_text = f"""
Now you can use this knowledge base to generate articles:

1. Generate an article:
   python -m src.cli.main generate -kb {output_path} -t "AI Research Trends"

2. Validate citations in an article:
   python -m src.cli.main validate -a your_article.pdf -kb {output_path}

3. Update the knowledge base with new documents:
   python -m src.cli.main build -f "{folder_path}" -o {output_path} --force-update
        """.strip()
        
        usage_panel = Panel(
            usage_text,
            title="[bold blue]Next Steps[/bold blue]",
            border_style="blue",
            padding=(1, 2)
        )
        
        console.print(usage_panel)
        
    except FileNotFoundError:
        console.print(f"[bold red]Folder not found: {folder_path}[/bold red]")
        console.print("\n[bold yellow]Please create the folder and add some documents, or update the path in this script.[/bold yellow]")
        
        # Show example of creating a test folder
        console.print("\n[bold]Example: Creating a test folder with sample documents[/bold]")
        
        test_folder = Path("test_documents")
        test_folder.mkdir(exist_ok=True)
        
        # Create sample documents
        sample_docs = [
            ("ai_research_paper.txt", "AI Research Paper\n\nThis paper discusses artificial intelligence trends [Source 1].\nThe findings show significant progress [Source 2]."),
            ("machine_learning_study.txt", "Machine Learning Study\n\nRecent studies in machine learning [Source 3] demonstrate new capabilities.\nThe research indicates promising results [Source 4]."),
            ("data_science_pov.txt", "Data Science POV\n\nOur point of view on data science trends [Source 5].\nThe analysis reveals important insights [Source 6].")
        ]
        
        for filename, content in sample_docs:
            (test_folder / filename).write_text(content)
        
        console.print(f"[green]Created test folder: {test_folder}[/green]")
        console.print("You can now run the script with this test folder.")
        
    except Exception as e:
        console.print(f"[bold red]Error building knowledge base: {e}[/bold red]")


def show_build_options():
    """Show available build options."""
    
    console = Console()
    
    options_text = """
[bold]Knowledge Base Build Options:[/bold]

[bold cyan]File Extensions:[/bold]
  --extensions pdf,docx,doc,txt,md,rtf

[bold cyan]Exclude Patterns:[/bold]
  --exclude "*draft*","*temp*","*backup*"

[bold cyan]File Size Limits:[/bold]
  --max-size 52428800  (50MB in bytes)

[bold cyan]Recursive Search:[/bold]
  --no-recursive       (disable subdirectory search)

[bold cyan]Force Update:[/bold]
  --force-update       (reprocess all documents)

[bold]Example Commands:[/bold]

1. Build from White Papers folder:
   python -m src.cli.main build -f "White Papers, Studies, POVs, Conference Pres" -o kb.json

2. Build only PDF and DOCX files:
   python -m src.cli.main build -f documents/ -o kb.json --extensions pdf,docx

3. Exclude draft files:
   python -m src.cli.main build -f documents/ -o kb.json --exclude "*draft*","*temp*"

4. Update existing knowledge base:
   python -m src.cli.main build -f documents/ -o existing_kb.json --force-update
    """
    
    options_panel = Panel(
        options_text,
        title="[bold blue]Build Command Options[/bold blue]",
        border_style="blue",
        padding=(1, 2)
    )
    
    console.print(options_panel)


if __name__ == "__main__":
    show_build_options()
    print("\n" + "="*60)
    example_build_knowledge_base()
