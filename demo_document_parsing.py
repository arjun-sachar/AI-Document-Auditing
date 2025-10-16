#!/usr/bin/env python3
"""Demo script showing document parsing capabilities."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.document_parser import DocumentParser
from utils.file_handlers import FileHandler
from rich.console import Console
from rich.table import Table
from rich.panel import Panel


def demo_document_parsing():
    """Demonstrate document parsing capabilities."""
    
    console = Console()
    
    console.print(Panel(
        "AI Document Auditing System - Document Parsing Demo",
        style="bold blue"
    ))
    
    # Initialize components
    parser = DocumentParser()
    handler = FileHandler()
    
    # Show supported formats
    formats_table = Table(title="Supported Document Formats")
    formats_table.add_column("Format", style="cyan")
    formats_table.add_column("Extension", style="green")
    formats_table.add_column("Description", style="white")
    
    format_descriptions = {
        '.pdf': 'Portable Document Format - Academic papers, reports',
        '.docx': 'Microsoft Word (new format) - Research papers, articles',
        '.doc': 'Microsoft Word (legacy) - Older documents',
        '.txt': 'Plain text - Simple text documents',
        '.md': 'Markdown - Formatted text with markup',
        '.rtf': 'Rich Text Format - Formatted documents'
    }
    
    for ext in parser.get_supported_formats():
        formats_table.add_row(
            ext.upper().replace('.', ''),
            ext,
            format_descriptions.get(ext, 'Document format')
        )
    
    console.print(formats_table)
    
    # Demo with sample file
    sample_file = Path("examples/sample_research_paper.txt")
    
    if sample_file.exists():
        console.print(f"\n[bold green]Demo: Parsing {sample_file}[/bold green]")
        
        try:
            # Parse document
            document_data = parser.parse_document(sample_file)
            
            # Show document info
            info_table = Table(title="Document Information")
            info_table.add_column("Property", style="cyan")
            info_table.add_column("Value", style="white")
            
            info_table.add_row("File Path", str(document_data['file_path']))
            info_table.add_row("File Extension", document_data['file_extension'])
            info_table.add_row("File Size", f"{document_data['file_size']:,} bytes")
            info_table.add_row("Total Words", f"{document_data['total_words']:,}")
            info_table.add_row("Parsing Method", document_data['parsing_method'])
            
            console.print(info_table)
            
            # Extract citations
            console.print(f"\n[bold yellow]Extracting citations...[/bold yellow]")
            citations = parser.extract_citations_from_document(sample_file)
            
            if citations:
                citations_table = Table(title=f"Found {len(citations)} Citations")
                citations_table.add_column("Citation", style="cyan", max_width=30)
                citations_table.add_column("Position", style="green")
                citations_table.add_column("Context Preview", style="white", max_width=40)
                
                for citation in citations[:10]:  # Show first 10
                    context_preview = citation['context'][:40] + "..." if len(citation['context']) > 40 else citation['context']
                    citations_table.add_row(
                        citation['text'],
                        str(citation['position']),
                        context_preview
                    )
                
                console.print(citations_table)
            else:
                console.print("[yellow]No citations found in the document[/yellow]")
            
            # Show content preview
            content_preview = document_data['content'][:500] + "..." if len(document_data['content']) > 500 else document_data['content']
            
            console.print(Panel(
                content_preview,
                title="[bold blue]Document Content Preview[/bold blue]",
                border_style="blue"
            ))
            
        except Exception as e:
            console.print(f"[bold red]Error parsing document: {e}[/bold red]")
    
    else:
        console.print(f"[yellow]Sample file not found: {sample_file}[/yellow]")
        console.print("Creating a simple test file...")
        
        # Create a simple test file
        test_content = """
        This is a test document with some citations.
        
        According to recent research [Source 1], the findings are significant.
        The study shows that [Source 2] confirms our hypothesis.
        
        Additional evidence [Source 3] supports these conclusions.
        """
        
        test_file = Path("test_document.txt")
        test_file.write_text(test_content)
        
        try:
            document_data = parser.parse_document(test_file)
            console.print(f"[green]Successfully parsed test document with {document_data['total_words']} words[/green]")
            
            citations = parser.extract_citations_from_document(test_file)
            console.print(f"[green]Found {len(citations)} citations in test document[/green]")
            
        finally:
            # Clean up
            if test_file.exists():
                test_file.unlink()
    
    # Show usage examples
    console.print(Panel(
        """
[bold]Usage Examples:[/bold]

1. Parse any supported document:
   python -c "from src.utils.document_parser import DocumentParser; p = DocumentParser(); print(p.parse_document('your_file.pdf'))"

2. Extract text from document:
   python -c "from src.utils.file_handlers import extract_text_from_document; print(extract_text_from_document('your_file.docx'))"

3. Extract citations with location info:
   python -c "from src.utils.file_handlers import extract_citations_from_document; citations = extract_citations_from_document('your_file.pdf'); print(citations)"

4. Validate document with CLI:
   python -m src.cli.main validate -a your_file.pdf -kb examples/sample_knowledge_base.json

[bold]Note:[/bold] For PDF and DOCX files, the system will extract:
- Text content from all pages/sections
- Document metadata (author, title, creation date)
- Page/paragraph location information for citations
- Table data (for DOCX files)
        """,
        title="[bold blue]How to Use Document Parsing[/bold blue]",
        border_style="blue"
    ))


if __name__ == "__main__":
    demo_document_parsing()
