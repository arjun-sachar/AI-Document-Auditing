"""Article validation command implementation."""

import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text
import json

from ..validation.citation_validator import CitationValidator
from ..validation.context_validator import ContextValidator
from ..validation.nlp_processor import NLPProcessor
from ..validation.confidence_scorer import ConfidenceScorer
from ..article_generator.knowledge_base import KnowledgeBase
from ..llm.anthropic_client import AnthropicClient
from ..llm.model_selector import ModelSelector
from ..utils.file_handlers import FileHandler
from config.settings import get_settings


console = Console()


def validate_article_command(
    ctx,
    article: str,
    knowledge_base: str,
    output: str,
    confidence_threshold: float,
    detailed_report: bool
):
    """Validate citations and context in an article."""
    
    settings = ctx.obj['settings']
    
    try:
        # Display validation parameters
        display_validation_info(article, knowledge_base, confidence_threshold)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Load article
            task1 = progress.add_task("Loading article...", total=None)
            file_handler = FileHandler()
            
            # Check if it's a supported document format
            if file_handler.is_document_supported(article):
                article_data = file_handler.load_document(article)
                article_content = article_data['content']
                progress.update(task1, description=f"Document loaded ✓ ({article_data.get('total_pages', 1)} pages)")
            else:
                article_content = file_handler.load_text(article)
                progress.update(task1, description="Article loaded ✓")
            
            # Load knowledge base
            task2 = progress.add_task("Loading knowledge base...", total=None)
            kb = KnowledgeBase(Path(knowledge_base))
            progress.update(task2, description="Knowledge base loaded ✓")
            
            # Initialize components
            task3 = progress.add_task("Initializing validation components...", total=None)
            
            # Initialize NLP processor
            nlp_processor = NLPProcessor()
            
            # Initialize LLM clients
            model_selector = ModelSelector(Path("config/model_config.yaml"))
            validation_models = model_selector.get_validation_models()
            
            citation_llm = AnthropicClient(
                provider=validation_models['citation'].provider,
                api_key=validation_models['citation'].api_key,
                model_name=validation_models['citation'].name,
                base_url=validation_models['citation'].base_url
            )
            
            context_llm = AnthropicClient(
                provider=validation_models['context'].provider,
                api_key=validation_models['context'].api_key,
                model_name=validation_models['context'].name,
                base_url=validation_models['context'].base_url
            )
            
            # Initialize validators
            citation_validator = CitationValidator(nlp_processor, citation_llm)
            context_validator = ContextValidator(nlp_processor, context_llm)
            confidence_scorer = ConfidenceScorer()
            
            progress.update(task3, description="Validation components initialized ✓")
            
            # Extract citations
            task4 = progress.add_task("Extracting citations...", total=None)
            citations = nlp_processor.extract_citations(article_content)
            progress.update(task4, description=f"Found {len(citations)} citations ✓")
            
            # Validate citations
            task5 = progress.add_task("Validating citations...", total=None)
            kb_sources = kb.search("", max_results=100)  # Get all sources for validation
            citation_results = citation_validator.validate_citations(
                article_content, kb_sources, confidence_threshold
            )
            progress.update(task5, description="Citation validation completed ✓")
            
            # Validate context
            task6 = progress.add_task("Validating context...", total=None)
            context_results = context_validator.validate_context(
                citations, kb_sources, article_content
            )
            progress.update(task6, description="Context validation completed ✓")
            
            # Calculate confidence scores
            task7 = progress.add_task("Calculating confidence scores...", total=None)
            article_metadata = {
                'topic': 'Unknown',
                'word_count': len(article_content.split()),
                'citations_count': len(citations),
                'sources_used': len(kb_sources)
            }
            
            confidence_score = confidence_scorer.calculate_overall_confidence(
                citation_results, context_results, article_metadata, kb_sources
            )
            progress.update(task7, description="Confidence scoring completed ✓")
            
            # Save results
            task8 = progress.add_task("Saving validation results...", total=None)
            if output:
                output_path = Path(output)
            else:
                output_path = settings.results_dir / f"validation_results_{Path(article).stem}.json"
            
            # Prepare results
            validation_results = {
                'article_path': article,
                'knowledge_base_path': knowledge_base,
                'validation_timestamp': progress._tasks[0].start_time.isoformat() if progress._tasks else None,
                'confidence_threshold': confidence_threshold,
                'overall_confidence': confidence_score.overall_confidence,
                'citation_results': [result.__dict__ for result in citation_results],
                'context_results': [result.__dict__ for result in context_results],
                'confidence_breakdown': confidence_score.detailed_breakdown,
                'risk_factors': confidence_score.risk_factors,
                'recommendations': confidence_score.recommendations,
                'article_metadata': article_metadata
            }
            
            file_handler.save_json(validation_results, output_path)
            progress.update(task8, description="Validation results saved ✓")
        
        # Display results
        display_validation_results(
            confidence_score, citation_results, context_results, output_path, detailed_report
        )
        
    except Exception as e:
        console.print(f"[bold red]Error validating article:[/bold red] {e}")
        raise click.Abort()


def display_validation_info(article: str, knowledge_base: str, confidence_threshold: float):
    """Display validation parameters."""
    
    info_table = Table(title="Validation Parameters", show_header=True, header_style="bold blue")
    info_table.add_column("Parameter", style="cyan", no_wrap=True)
    info_table.add_column("Value", style="white")
    
    info_table.add_row("Article", article)
    info_table.add_row("Knowledge Base", knowledge_base)
    info_table.add_row("Confidence Threshold", f"{confidence_threshold:.2f}")
    
    console.print(info_table)
    console.print()


def display_validation_results(
    confidence_score,
    citation_results,
    context_results,
    output_path: Path,
    detailed_report: bool
):
    """Display validation results."""
    
    # Overall confidence score
    confidence_color = "green" if confidence_score.overall_confidence >= 0.8 else "yellow" if confidence_score.overall_confidence >= 0.6 else "red"
    
    overall_panel = Panel(
        Text(f"{confidence_score.overall_confidence:.2f}", style=f"bold {confidence_color}"),
        title="[bold blue]Overall Confidence Score[/bold blue]",
        border_style=confidence_color,
        padding=(1, 2)
    )
    
    console.print(overall_panel)
    
    # Confidence breakdown
    breakdown_table = Table(title="Confidence Breakdown", show_header=True, header_style="bold green")
    breakdown_table.add_column("Component", style="cyan", no_wrap=True)
    breakdown_table.add_column("Score", style="white")
    breakdown_table.add_column("Status", style="white")
    
    breakdown_table.add_row(
        "Citation Accuracy",
        f"{confidence_score.citation_accuracy_score:.2f}",
        "✓" if confidence_score.citation_accuracy_score >= 0.8 else "⚠" if confidence_score.citation_accuracy_score >= 0.6 else "✗"
    )
    
    breakdown_table.add_row(
        "Context Preservation",
        f"{confidence_score.context_preservation_score:.2f}",
        "✓" if confidence_score.context_preservation_score >= 0.8 else "⚠" if confidence_score.context_preservation_score >= 0.6 else "✗"
    )
    
    breakdown_table.add_row(
        "Source Reliability",
        f"{confidence_score.source_reliability_score:.2f}",
        "✓" if confidence_score.source_reliability_score >= 0.8 else "⚠" if confidence_score.source_reliability_score >= 0.6 else "✗"
    )
    
    breakdown_table.add_row(
        "Text Coherence",
        f"{confidence_score.coherence_score:.2f}",
        "✓" if confidence_score.coherence_score >= 0.8 else "⚠" if confidence_score.coherence_score >= 0.6 else "✗"
    )
    
    console.print(breakdown_table)
    
    # Citation validation results
    if citation_results:
        citation_table = Table(title="Citation Validation Results", show_header=True, header_style="bold yellow")
        citation_table.add_column("Citation", style="cyan", max_width=40)
        citation_table.add_column("Accuracy", style="white")
        citation_table.add_column("Confidence", style="white")
        citation_table.add_column("Source Found", style="white")
        citation_table.add_column("Issues", style="white")
        
        for result in citation_results[:10]:  # Show top 10
            citation_text = result.citation_text[:40] + "..." if len(result.citation_text) > 40 else result.citation_text
            accuracy = "✓" if result.is_accurate else "✗"
            confidence = f"{result.confidence:.2f}"
            source_found = "✓" if result.source_found else "✗"
            issues = ", ".join(result.issues[:2]) if result.issues else "None"
            
            citation_table.add_row(citation_text, accuracy, confidence, source_found, issues)
        
        console.print()
        console.print(citation_table)
    
    # Risk factors
    if confidence_score.risk_factors:
        risk_text = Text()
        risk_text.append("Risk Factors Identified:\n", style="bold red")
        for i, risk in enumerate(confidence_score.risk_factors, 1):
            risk_text.append(f"{i}. {risk}\n", style="red")
        
        risk_panel = Panel(
            risk_text,
            title="[bold red]Risk Factors[/bold red]",
            border_style="red",
            padding=(1, 2)
        )
        
        console.print()
        console.print(risk_panel)
    
    # Recommendations
    if confidence_score.recommendations:
        rec_text = Text()
        rec_text.append("Recommendations:\n", style="bold green")
        for i, rec in enumerate(confidence_score.recommendations, 1):
            rec_text.append(f"{i}. {rec}\n", style="green")
        
        rec_panel = Panel(
            rec_text,
            title="[bold green]Recommendations[/bold green]",
            border_style="green",
            padding=(1, 2)
        )
        
        console.print()
        console.print(rec_panel)
    
    console.print()
    console.print(f"[bold green]✓ Validation completed successfully![/bold green]")
    console.print(f"[dim]Results saved to: {output_path}[/dim]")
    
    if detailed_report:
        console.print(f"[dim]Use a JSON viewer to examine the detailed report.[/dim]")
