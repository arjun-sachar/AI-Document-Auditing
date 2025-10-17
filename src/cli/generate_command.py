"""Article generation command implementation."""

import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from src.article_generator.knowledge_base import KnowledgeBase
from src.article_generator.generator import ArticleGenerator
from src.llm.anthropic_client import AnthropicClient
from src.llm.model_selector import ModelSelector
from src.utils.file_handlers import FileHandler
from config.settings import get_settings


console = Console()


def generate_article_command(
    ctx,
    knowledge_base: str,
    topic: str,
    output: str,
    length: str,
    style: str,
    max_sources: int,
    no_citations: bool
):
    """Generate an article from a knowledge base."""
    
    settings = ctx.obj['settings']
    
    try:
        # Display generation parameters
        display_generation_info(knowledge_base, topic, length, style, max_sources, no_citations)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Load knowledge base
            task1 = progress.add_task("Loading knowledge base...", total=None)
            kb = KnowledgeBase(Path(knowledge_base))
            progress.update(task1, description="Knowledge base loaded ✓")
            
            # Initialize components
            task2 = progress.add_task("Initializing article generator...", total=None)
            
            # Initialize model selector and get generation model
            model_selector = ModelSelector(Path("config/model_config.yaml"))
            generation_models = model_selector.get_generation_models()
            
            # Initialize LLM client for article generation
            generation_llm = AnthropicClient(
                provider=generation_models['article'].provider,
                api_key=generation_models['article'].api_key,
                model_name=generation_models['article'].name,
                base_url=generation_models['article'].base_url
            )
            
            # Initialize article generator
            article_generator = ArticleGenerator(generation_llm, kb)
            progress.update(task2, description="Article generator initialized ✓")
            
            # Generate article
            task3 = progress.add_task("Generating article...", total=None)
            
            article_config = {
                'topic': topic,
                'length': length,
                'style': style,
                'max_sources': max_sources,
                'include_citations': not no_citations
            }
            
            article = article_generator.generate_article(
                topic=topic,
                length=length,
                style=style,
                include_citations=not no_citations,
                max_sources=max_sources
            )
            progress.update(task3, description="Article generated ✓")
            
            # Save article
            task4 = progress.add_task("Saving article...", total=None)
            if output:
                output_path = Path(output)
            else:
                # Generate default filename
                safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_topic = safe_topic.replace(' ', '_').lower()
                output_path = settings.output_dir / f"article_{safe_topic}.md"
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save the article
            file_handler = FileHandler()
            file_handler.save_text(article['content'], output_path)
            
            # Also save full article data with sources for validation
            metadata_path = output_path.with_suffix('.json')
            full_article_data = {
                'topic': topic,
                'content': article['content'],
                'word_count': article['metadata']['word_count'],
                'citations_count': len(article['citations']),
                'sources_used': len(article['sources']),
                'sources': article['sources'],  # Include full source data
                'citations': article['citations'],  # Include citation data
                'generation_timestamp': article['metadata']['generated_at'],
                'generation_config': article_config,
                'knowledge_base_path': knowledge_base,
                'metadata': article['metadata']
            }
            file_handler.save_json(full_article_data, metadata_path)
            
            progress.update(task4, description="Article saved ✓")
        
        # Display results
        display_generation_results(article, output_path, metadata_path)
        
    except Exception as e:
        console.print(f"[bold red]Error generating article:[/bold red] {e}")
        raise click.Abort()


def display_generation_info(knowledge_base: str, topic: str, length: str, style: str, max_sources: int, no_citations: bool):
    """Display generation parameters."""
    
    info_table = Table(title="Article Generation Parameters", show_header=True, header_style="bold blue")
    info_table.add_column("Parameter", style="cyan", no_wrap=True)
    info_table.add_column("Value", style="white")
    
    info_table.add_row("Knowledge Base", knowledge_base)
    info_table.add_row("Topic", topic)
    info_table.add_row("Length", length.title())
    info_table.add_row("Style", style.title())
    info_table.add_row("Max Sources", str(max_sources))
    info_table.add_row("Include Citations", "No" if no_citations else "Yes")
    
    console.print(info_table)
    console.print()


def display_generation_results(article, output_path: Path, metadata_path: Path):
    """Display generation results."""
    
    # Article statistics
    stats_table = Table(title="Article Statistics", show_header=True, header_style="bold green")
    stats_table.add_column("Metric", style="cyan", no_wrap=True)
    stats_table.add_column("Value", style="white")
    
    stats_table.add_row("Topic", article['metadata']['topic'])
    stats_table.add_row("Word Count", str(article['metadata']['word_count']))
    stats_table.add_row("Citations", str(len(article['citations'])))
    stats_table.add_row("Sources Used", str(len(article['sources'])))
    
    console.print(stats_table)
    
    # Sources used
    if article['sources']:
        sources_table = Table(title="Sources Used", show_header=True, header_style="bold yellow")
        sources_table.add_column("Source", style="cyan", max_width=60)
        sources_table.add_column("Relevance", style="white")
        
        for source in article['sources'][:10]:  # Show top 10 sources
            source_title = source.get('title', 'Unknown')[:60]
            relevance_score = source.get('relevance_score', 0)
            sources_table.add_row(source_title, f"{relevance_score:.2f}")
        
        console.print()
        console.print(sources_table)
        
        if len(article['sources']) > 10:
            console.print(f"[dim]... and {len(article['sources']) - 10} more sources[/dim]")
    
    # Summary
    summary_info = f"""
Article Topic: {article['metadata']['topic']}
Word Count: {article['metadata']['word_count']:,} words
Citations: {len(article['citations'])} citations
Sources: {len(article['sources'])} sources used
Generated: {article['metadata']['generated_at']}
    """.strip()
    
    summary_panel = Panel(
        summary_info,
        title="[bold blue]Generation Summary[/bold blue]",
        border_style="blue",
        padding=(1, 2)
    )
    
    console.print()
    console.print(summary_panel)
    
    console.print()
    console.print(f"[bold green]✓ Article generated successfully![/bold green]")
    console.print(f"[dim]Article saved to: {output_path}[/dim]")
    console.print(f"[dim]Metadata saved to: {metadata_path}[/dim]")


def display_usage_examples():
    """Display usage examples."""
    
    examples_text = Text()
    examples_text.append("Usage Examples:\n", style="bold green")
    
    examples_text.append("1. Generate a medium-length academic article:\n", style="bold")
    examples_text.append("   python -m src.cli.main generate -kb knowledge_bases/white_papers.json -t 'AI Research Trends'\n\n")
    
    examples_text.append("2. Generate a short journalistic article:\n", style="bold")
    examples_text.append("   python -m src.cli.main generate -kb kb.json -t 'Climate Change' -l short -s journalistic\n\n")
    
    examples_text.append("3. Generate article with specific output file:\n", style="bold")
    examples_text.append("   python -m src.cli.main generate -kb kb.json -t 'Technology Trends' -o my_article.md\n\n")
    
    examples_text.append("4. Generate article without citations:\n", style="bold")
    examples_text.append("   python -m src.cli.main generate -kb kb.json -t 'Future of AI' --no-citations\n\n")
    
    examples_text.append("5. Limit sources used in generation:\n", style="bold")
    examples_text.append("   python -m src.cli.main generate -kb kb.json -t 'Data Science' --max-sources 5\n\n")
    
    examples_text.append("Available lengths: short, medium, long\n", style="italic")
    examples_text.append("Available styles: academic, journalistic, technical", style="italic")
    
    examples_panel = Panel(
        examples_text,
        title="[bold blue]Article Generation Examples[/bold blue]",
        border_style="blue",
        padding=(1, 2)
    )
    
    console.print(examples_panel)