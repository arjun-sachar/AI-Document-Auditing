"""Usage examples for the AI Document Auditing System."""

import json
from pathlib import Path
from src.article_generator.generator import ArticleGenerator
from src.article_generator.knowledge_base import KnowledgeBase
from src.validation.citation_validator import CitationValidator
from src.validation.context_validator import ContextValidator
from src.validation.nlp_processor import NLPProcessor
from src.validation.confidence_scorer import ConfidenceScorer
from src.llm.anthropic_client import AnthropicClient
from src.llm.model_selector import ModelSelector


def example_article_generation():
    """Example of generating an article from a knowledge base."""
    
    print("=== Article Generation Example ===")
    
    # Initialize components
    model_selector = ModelSelector(Path("config/model_config.yaml"))
    model_config = model_selector.get_model_config()
    
    llm_client = AnthropicClient(
        provider=model_config.provider,
        api_key=model_config.api_key,
        model_name=model_config.name,
        base_url=model_config.base_url
    )
    
    # Load knowledge base
    kb = KnowledgeBase(Path("examples/sample_knowledge_base.json"))
    
    # Initialize article generator
    generator = ArticleGenerator(llm_client, kb)
    
    # Generate article
    try:
        article_data = generator.generate_article(
            topic="Climate Change and Renewable Energy",
            length="medium",
            style="academic",
            include_citations=True,
            max_sources=5
        )
        
        print(f"Generated article with {article_data['metadata']['word_count']} words")
        print(f"Used {article_data['metadata']['sources_used']} sources")
        print(f"Included {article_data['metadata']['citations_count']} citations")
        
        # Save article
        output_path = Path("examples/generated_article.md")
        generator.save_article(article_data, output_path)
        print(f"Article saved to: {output_path}")
        
    except Exception as e:
        print(f"Error generating article: {e}")


def example_citation_validation():
    """Example of validating citations in an article."""
    
    print("\n=== Citation Validation Example ===")
    
    # Initialize components
    model_selector = ModelSelector(Path("config/model_config.yaml"))
    validation_models = model_selector.get_validation_models()
    
    citation_llm = AnthropicClient(
        provider=validation_models['citation'].provider,
        api_key=validation_models['citation'].api_key,
        model_name=validation_models['citation'].name,
        base_url=validation_models['citation'].base_url
    )
    
    nlp_processor = NLPProcessor()
    citation_validator = CitationValidator(nlp_processor, citation_llm)
    
    # Load article and knowledge base
    with open("examples/sample_article.md", "r") as f:
        article_content = f.read()
    
    kb = KnowledgeBase(Path("examples/sample_knowledge_base.json"))
    kb_sources = kb.search("", max_results=100)
    
    # Extract citations
    citations = nlp_processor.extract_citations(article_content)
    print(f"Found {len(citations)} citations in article")
    
    # Validate citations
    try:
        validation_results = citation_validator.validate_citations(
            article_content, kb_sources, confidence_threshold=0.8
        )
        
        accurate_count = sum(1 for r in validation_results if r.is_accurate)
        print(f"Validation complete: {accurate_count}/{len(validation_results)} citations are accurate")
        
        # Display results
        for i, result in enumerate(validation_results[:3], 1):  # Show first 3
            print(f"\nCitation {i}:")
            print(f"  Text: {result.citation_text[:50]}...")
            print(f"  Accurate: {result.is_accurate}")
            print(f"  Confidence: {result.confidence:.2f}")
            print(f"  Source Found: {result.source_found}")
            
    except Exception as e:
        print(f"Error validating citations: {e}")


def example_context_validation():
    """Example of validating context preservation."""
    
    print("\n=== Context Validation Example ===")
    
    # Initialize components
    model_selector = ModelSelector(Path("config/model_config.yaml"))
    validation_models = model_selector.get_validation_models()
    
    context_llm = AnthropicClient(
        provider=validation_models['context'].provider,
        api_key=validation_models['context'].api_key,
        model_name=validation_models['context'].name,
        base_url=validation_models['context'].base_url
    )
    
    nlp_processor = NLPProcessor()
    context_validator = ContextValidator(nlp_processor, context_llm)
    
    # Load article and knowledge base
    with open("examples/sample_article.md", "r") as f:
        article_content = f.read()
    
    kb = KnowledgeBase(Path("examples/sample_knowledge_base.json"))
    kb_sources = kb.search("", max_results=100)
    
    # Extract citations
    citations = nlp_processor.extract_citations(article_content)
    
    # Validate context
    try:
        context_results = context_validator.validate_context(
            citations, kb_sources, article_content
        )
        
        preserved_count = sum(1 for r in context_results if r.context_preserved)
        print(f"Context validation complete: {preserved_count}/{len(context_results)} citations preserve context")
        
        # Display results
        for i, result in enumerate(context_results[:3], 1):  # Show first 3
            print(f"\nContext Validation {i}:")
            print(f"  Citation: {result.citation_text[:50]}...")
            print(f"  Context Preserved: {result.context_preserved}")
            print(f"  Semantic Similarity: {result.semantic_similarity_score:.2f}")
            print(f"  Confidence: {result.confidence:.2f}")
            
    except Exception as e:
        print(f"Error validating context: {e}")


def example_confidence_scoring():
    """Example of calculating confidence scores."""
    
    print("\n=== Confidence Scoring Example ===")
    
    # Initialize components
    confidence_scorer = ConfidenceScorer()
    nlp_processor = NLPProcessor()
    
    # Load article and knowledge base
    with open("examples/sample_article.md", "r") as f:
        article_content = f.read()
    
    kb = KnowledgeBase(Path("examples/sample_knowledge_base.json"))
    kb_sources = kb.search("", max_results=100)
    
    # Simulate validation results (in real usage, these would come from actual validation)
    citation_results = [
        {"is_accurate": True, "confidence": 0.9, "source_found": True},
        {"is_accurate": True, "confidence": 0.85, "source_found": True},
        {"is_accurate": False, "confidence": 0.3, "source_found": False},
        {"is_accurate": True, "confidence": 0.8, "source_found": True}
    ]
    
    context_results = [
        {"context_preserved": True, "semantic_similarity_score": 0.9, "confidence": 0.85},
        {"context_preserved": True, "semantic_similarity_score": 0.8, "confidence": 0.8},
        {"context_preserved": False, "semantic_similarity_score": 0.4, "confidence": 0.3},
        {"context_preserved": True, "semantic_similarity_score": 0.85, "confidence": 0.82}
    ]
    
    article_metadata = {
        "topic": "Climate Change",
        "word_count": len(article_content.split()),
        "citations_count": 4,
        "sources_used": len(kb_sources)
    }
    
    # Calculate confidence score
    try:
        confidence_score = confidence_scorer.calculate_overall_confidence(
            citation_results, context_results, article_metadata, kb_sources
        )
        
        print(f"Overall Confidence Score: {confidence_score.overall_confidence:.2f}")
        print(f"Citation Accuracy: {confidence_score.citation_accuracy_score:.2f}")
        print(f"Context Preservation: {confidence_score.context_preservation_score:.2f}")
        print(f"Source Reliability: {confidence_score.source_reliability_score:.2f}")
        print(f"Text Coherence: {confidence_score.coherence_score:.2f}")
        
        print(f"\nRisk Factors: {len(confidence_score.risk_factors)}")
        for risk in confidence_score.risk_factors:
            print(f"  - {risk}")
        
        print(f"\nRecommendations: {len(confidence_score.recommendations)}")
        for rec in confidence_score.recommendations:
            print(f"  - {rec}")
            
    except Exception as e:
        print(f"Error calculating confidence score: {e}")


def example_document_parsing():
    """Example of document parsing functionality."""
    
    print("\n=== Document Parsing Example ===")
    
    from src.utils.document_parser import DocumentParser
    from src.utils.file_handlers import FileHandler
    
    # Initialize document parser
    parser = DocumentParser()
    
    # Show supported formats
    supported_formats = parser.get_supported_formats()
    print(f"Supported document formats: {', '.join(supported_formats)}")
    
    # Example with text file
    test_content = """
    This is a sample research paper.
    
    According to recent studies [Source 1], climate change is accelerating.
    The research shows that temperatures are rising [Source 2].
    
    Conclusions: Immediate action is required [Source 3].
    """
    
    # Create a test file
    test_file = Path("examples/sample_research.txt")
    test_file.write_text(test_content)
    
    try:
        # Parse document
        document_data = parser.parse_document(test_file)
        print(f"\nParsed document:")
        print(f"  File extension: {document_data['file_extension']}")
        print(f"  Total words: {document_data['total_words']}")
        print(f"  Parsing method: {document_data['parsing_method']}")
        
        # Extract citations
        citations = parser.extract_citations_from_document(test_file)
        print(f"\nFound {len(citations)} citations:")
        for i, citation in enumerate(citations, 1):
            print(f"  {i}. {citation['text']}")
            print(f"     Position: {citation['position']}")
            print(f"     Context: {citation['context'][:50]}...")
        
        # Use FileHandler for document processing
        handler = FileHandler()
        extracted_text = handler.extract_text_from_document(test_file)
        print(f"\nExtracted text length: {len(extracted_text)} characters")
        
    finally:
        # Clean up test file
        if test_file.exists():
            test_file.unlink()
    
    print("\nNote: For PDF and DOCX files, the system will extract text, metadata, and page information.")


def example_knowledge_base_operations():
    """Example of knowledge base operations."""
    
    print("\n=== Knowledge Base Operations Example ===")
    
    # Load knowledge base
    kb = KnowledgeBase(Path("examples/sample_knowledge_base.json"))
    
    # Get statistics
    stats = kb.get_statistics()
    print(f"Knowledge base contains {stats['total_entries']} entries")
    print(f"Total content length: {stats['total_content_length']} characters")
    print(f"Average content length: {stats['average_content_length']:.0f} characters")
    
    # Search for relevant entries
    search_results = kb.search("renewable energy", max_results=3)
    print(f"\nFound {len(search_results)} relevant entries for 'renewable energy':")
    
    for i, result in enumerate(search_results, 1):
        print(f"\n{i}. {result['title']}")
        print(f"   Relevance Score: {result['relevance_score']:.2f}")
        print(f"   Content Preview: {result['content'][:100]}...")
    
    # Add new entry
    new_entry_id = kb.add_entry(
        title="Climate Change Adaptation Strategies",
        content="Climate change adaptation involves adjusting to actual or expected climate effects to moderate harm or exploit beneficial opportunities. Key strategies include infrastructure improvements, ecosystem-based adaptation, and community-based adaptation approaches.",
        url="https://unfccc.int/topics/adaptation-and-resilience",
        metadata={"author": "UNFCCC", "type": "international_organization"}
    )
    
    print(f"\nAdded new entry with ID: {new_entry_id}")
    print(f"Knowledge base now contains {len(kb.entries)} entries")


def run_all_examples():
    """Run all examples."""
    
    print("AI Document Auditing System - Usage Examples")
    print("=" * 50)
    
    try:
        # Note: These examples require proper API keys and model configuration
        # Uncomment the examples you want to run:
        
        # example_knowledge_base_operations()
        # example_document_parsing()
        # example_article_generation()
        # example_citation_validation()
        # example_context_validation()
        # example_confidence_scoring()
        
        print("\nTo run examples, uncomment the desired functions in run_all_examples()")
        print("Make sure to configure your API keys in config/model_config.yaml first")
        
    except Exception as e:
        print(f"Error running examples: {e}")


if __name__ == "__main__":
    run_all_examples()
