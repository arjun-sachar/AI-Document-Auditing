"""
Import helper for AI Document Auditing components
This module handles the complex import structure and provides a clean interface
"""

import sys
import os
from pathlib import Path

# Add src to Python path and set up proper package structure
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Create a simple package structure to avoid relative import issues
import importlib.util
import types

def create_module_from_file(module_name, file_path):
    """Create a module from a file path"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Try to import components with fallback handling
def get_ai_components():
    """Get AI components with graceful fallback"""
    components = {
        'ArticleGenerator': None,
        'KnowledgeBase': None,
        'CitationValidator': None,
        'ContextValidator': None,
        'ConfidenceScorer': None,
        'NLPProcessor': None,
        'AnthropicClient': None,
        'DocumentParser': None,
        'KnowledgeBaseBuilder': None,
        'available': False,
        'partial_available': False
    }
    
    # Try to import basic components first (without heavy ML dependencies)
    basic_components_loaded = False
    try:
        # Import basic utility components first
        from utils.document_parser import DocumentParser
        from utils.knowledge_base_builder import KnowledgeBaseBuilder
        components['DocumentParser'] = DocumentParser
        components['KnowledgeBaseBuilder'] = KnowledgeBaseBuilder
        basic_components_loaded = True
        print("✅ Basic utility components loaded")
    except Exception as e:
        print(f"⚠️  Could not load basic utility components: {e}")
    
    # Try to import LLM client
    try:
        from llm.anthropic_client import AnthropicClient
        components['AnthropicClient'] = AnthropicClient
        print("✅ LLM client loaded")
    except Exception as e:
        print(f"⚠️  Could not load LLM client: {e}")
    
    # Try to import article generation components
    try:
        from article_generator.generator import ArticleGenerator
        from article_generator.knowledge_base import KnowledgeBase
        components['ArticleGenerator'] = ArticleGenerator
        components['KnowledgeBase'] = KnowledgeBase
        print("✅ Article generation components loaded")
    except Exception as e:
        print(f"⚠️  Could not load article generation components: {e}")
    
    # Try to import validation components (these have heavy ML dependencies)
    validation_loaded = False
    try:
        from validation.citation_validator import CitationValidator
        from validation.confidence_scorer import ConfidenceScorer
        components['CitationValidator'] = CitationValidator
        components['ConfidenceScorer'] = ConfidenceScorer
        validation_loaded = True
        print("✅ Basic validation components loaded")
    except Exception as e:
        print(f"⚠️  Could not load basic validation components: {e}")
    
    # Try to import NLP processor (this has heavy dependencies)
    try:
        from validation.nlp_processor import NLPProcessor
        components['NLPProcessor'] = NLPProcessor
        print("✅ NLP processor loaded")
    except Exception as e:
        print(f"⚠️  Could not load NLP processor (heavy ML dependencies): {e}")
    
    # Try to import context validator (this has the heaviest dependencies)
    try:
        from validation.context_validator import ContextValidator
        components['ContextValidator'] = ContextValidator
        print("✅ Context validator loaded")
    except Exception as e:
        print(f"⚠️  Could not load context validator (PyTorch/transformers dependencies): {e}")
    
    # Determine availability
    if basic_components_loaded and components['AnthropicClient'] and components['ArticleGenerator']:
        components['available'] = True
        print("✅ Core AI components available - full functionality enabled")
    elif basic_components_loaded:
        components['partial_available'] = True
        print("✅ Partial AI components available - basic functionality enabled")
    else:
        print("⚠️  No AI components available - running in mock mode")
        
    return components

def initialize_ai_components(components):
    """Initialize AI components with error handling"""
    if not components['available'] and not components['partial_available']:
        return None, False
    
    try:
        initialized_components = {}
        
        # Initialize basic components
        if components['DocumentParser']:
            initialized_components['document_parser'] = components['DocumentParser']()
            print("✅ Document parser initialized")
        
        if components['KnowledgeBaseBuilder']:
            initialized_components['kb_builder'] = components['KnowledgeBaseBuilder']()
            print("✅ Knowledge base builder initialized")
        
        # Initialize LLM client
        if components['AnthropicClient']:
            # Get API key from environment
            import os
            api_key = os.environ.get('OPENROUTER_API_KEY')
            if api_key:
                initialized_components['llm_client'] = components['AnthropicClient'](api_key=api_key)
                print("✅ LLM client initialized with API key")
            else:
                print("⚠️  No API key found for LLM client")
                initialized_components['llm_client'] = None
        
        # Initialize article generation components
        if components['ArticleGenerator'] and components['KnowledgeBase']:
            initialized_components['ArticleGenerator'] = components['ArticleGenerator']
            initialized_components['KnowledgeBase'] = components['KnowledgeBase']
            print("✅ Article generation components initialized")
        
        # Initialize validation components (if available)
        if components['NLPProcessor']:
            initialized_components['nlp_processor'] = components['NLPProcessor']()
            print("✅ NLP processor initialized")
        
        if components['CitationValidator'] and components['NLPProcessor'] and components['AnthropicClient']:
            initialized_components['citation_validator'] = components['CitationValidator'](
                initialized_components['nlp_processor'], 
                initialized_components['llm_client']
            )
            print("✅ Citation validator initialized")
        
        if components['ContextValidator'] and components['NLPProcessor'] and components['AnthropicClient']:
            initialized_components['context_validator'] = components['ContextValidator'](
                initialized_components['nlp_processor'], 
                initialized_components['llm_client']
            )
            print("✅ Context validator initialized")
        
        if components['ConfidenceScorer']:
            initialized_components['confidence_scorer'] = components['ConfidenceScorer']()
            print("✅ Confidence scorer initialized")
        
        # Set defaults for missing components
        for key in ['llm_client', 'nlp_processor', 'citation_validator', 'context_validator', 'confidence_scorer', 'document_parser', 'kb_builder', 'ArticleGenerator', 'KnowledgeBase']:
            if key not in initialized_components:
                initialized_components[key] = None
        
        success = components['available'] or components['partial_available']
        return initialized_components, success
        
    except Exception as e:
        print(f"⚠️  Could not initialize AI components: {e}")
        print("   Falling back to mock implementations")
        return None, False
