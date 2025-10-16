"""Main article generation logic."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..llm.anthropic_client import AnthropicClient
from ..utils.text_processing import preprocess_text, extract_citations
from .knowledge_base import KnowledgeBase
from .prompt_templates import PromptTemplates


logger = logging.getLogger(__name__)


class ArticleGenerator:
    """Generates articles from knowledge bases using LLM integration."""
    
    def __init__(self, llm_client: AnthropicClient, knowledge_base: KnowledgeBase):
        """Initialize the article generator.
        
        Args:
            llm_client: Configured LLM client for text generation
            knowledge_base: Knowledge base instance for source material
        """
        self.llm_client = llm_client
        self.knowledge_base = knowledge_base
        self.prompt_templates = PromptTemplates()
        
    def generate_article(
        self,
        topic: str,
        length: str = "medium",  # short, medium, long
        style: str = "academic",  # academic, journalistic, technical
        include_citations: bool = True,
        max_sources: int = 10
    ) -> Dict[str, Any]:
        """Generate an article on the given topic.
        
        Args:
            topic: The topic to write about
            length: Desired article length
            style: Writing style
            include_citations: Whether to include citations
            max_sources: Maximum number of sources to use
            
        Returns:
            Dictionary containing the generated article and metadata
        """
        logger.info(f"Generating article on topic: {topic}")
        
        # Retrieve relevant knowledge base entries
        relevant_sources = self.knowledge_base.search(topic, max_results=max_sources)
        logger.info(f"Found {len(relevant_sources)} relevant sources")
        
        if not relevant_sources:
            raise ValueError(f"No relevant sources found for topic: {topic}")
        
        # Create context from sources
        context = self._create_context(relevant_sources)
        
        # Generate article using LLM
        article_content = self._generate_content(
            topic, context, length, style, include_citations
        )
        
        # Extract and validate citations
        citations = []
        if include_citations:
            citations = extract_citations(article_content)
            citations = self._validate_citations(citations, relevant_sources)
        
        # Create metadata
        metadata = {
            "topic": topic,
            "length": length,
            "style": style,
            "generated_at": datetime.now().isoformat(),
            "sources_used": len(relevant_sources),
            "citations_count": len(citations),
            "model_used": self.llm_client.model_name,
            "word_count": len(article_content.split())
        }
        
        result = {
            "content": article_content,
            "metadata": metadata,
            "sources": relevant_sources,
            "citations": citations
        }
        
        logger.info(f"Article generated successfully with {len(citations)} citations")
        return result
    
    def _create_context(self, sources: List[Dict[str, Any]]) -> str:
        """Create context string from source materials.
        
        Args:
            sources: List of source documents
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, source in enumerate(sources, 1):
            source_text = f"Source {i}:\n"
            source_text += f"Title: {source.get('title', 'Unknown')}\n"
            source_text += f"Content: {source.get('content', '')}\n"
            if 'url' in source:
                source_text += f"URL: {source['url']}\n"
            source_text += "\n" + "="*50 + "\n\n"
            context_parts.append(source_text)
        
        return "\n".join(context_parts)
    
    def _generate_content(
        self,
        topic: str,
        context: str,
        length: str,
        style: str,
        include_citations: bool
    ) -> str:
        """Generate article content using LLM.
        
        Args:
            topic: Article topic
            context: Source context
            length: Article length
            style: Writing style
            include_citations: Whether to include citations
            
        Returns:
            Generated article content
        """
        prompt = self.prompt_templates.get_article_generation_prompt(
            topic=topic,
            context=context,
            length=length,
            style=style,
            include_citations=include_citations
        )
        
        logger.info(f"Generating article with prompt length: {len(prompt)} characters")
        logger.debug(f"Prompt preview: {prompt[:500]}...")
        
        response = self.llm_client.generate_text(
            prompt=prompt,
            max_tokens=4000,
            temperature=0.1
        )
        
        logger.info(f"Generated response length: {len(response)} characters")
        if not response.strip():
            logger.warning("Received empty response from LLM!")
        
        return response.strip()
    
    def _validate_citations(
        self,
        citations: List[str],
        sources: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Validate extracted citations against source materials.
        
        Args:
            citations: List of extracted citation strings
            sources: Source materials used
            
        Returns:
            List of validated citations with metadata
        """
        validated_citations = []
        
        for citation in citations:
            # Simple validation - in a real implementation, this would be more sophisticated
            citation_info = {
                "text": citation,
                "validated": True,  # Placeholder
                "source_found": False,
                "confidence": 0.0
            }
            
            # Check if citation appears in any source
            for source in sources:
                if citation.lower() in source.get('content', '').lower():
                    citation_info["source_found"] = True
                    citation_info["confidence"] = 0.8  # Placeholder
                    break
            
            validated_citations.append(citation_info)
        
        return validated_citations
    
    def save_article(self, article_data: Dict[str, Any], output_path: Path) -> None:
        """Save generated article to file.
        
        Args:
            article_data: Generated article data
            output_path: Path to save the article
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as markdown
        markdown_content = self._format_as_markdown(article_data)
        output_path.write_text(markdown_content, encoding='utf-8')
        
        # Save metadata as JSON
        metadata_path = output_path.with_suffix('.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(article_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Article saved to {output_path}")
    
    def _format_as_markdown(self, article_data: Dict[str, Any]) -> str:
        """Format article data as markdown.
        
        Args:
            article_data: Article data dictionary
            
        Returns:
            Formatted markdown content
        """
        metadata = article_data.get('metadata', {})
        
        markdown = f"# {metadata.get('topic', 'Untitled Article')}\n\n"
        markdown += f"*Generated on {metadata.get('generated_at', 'Unknown')}*\n\n"
        markdown += f"**Word Count:** {metadata.get('word_count', 0)}\n"
        markdown += f"**Sources Used:** {metadata.get('sources_used', 0)}\n"
        markdown += f"**Citations:** {metadata.get('citations_count', 0)}\n\n"
        markdown += "---\n\n"
        
        markdown += article_data['content']
        
        if article_data.get('citations'):
            markdown += "\n\n## Citations\n\n"
            for i, citation in enumerate(article_data['citations'], 1):
                markdown += f"{i}. {citation.get('text', '')}\n"
        
        if article_data.get('sources'):
            markdown += "\n\n## Sources\n\n"
            for i, source in enumerate(article_data['sources'], 1):
                markdown += f"{i}. **{source.get('title', 'Unknown')}**\n"
                if 'url' in source:
                    markdown += f"   - URL: {source['url']}\n"
        
        return markdown
