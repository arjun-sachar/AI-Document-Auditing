"""Main article generation logic."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from llm.anthropic_client import AnthropicClient
from utils.text_processing import preprocess_text, extract_citations
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
        
        # Add source numbers to sources for proper citation mapping
        for i, source in enumerate(relevant_sources, 1):
            source['source_number'] = i
        
        # Create context from sources
        context = self._create_context(relevant_sources)
        
        # Generate article using LLM
        article_content = self._generate_content(
            topic, context, length, style, include_citations
        )
        
        # Validate word count and regenerate if necessary
        article_content = self._validate_word_count(article_content, length, topic, context, style, include_citations)
        
        # Generate a catchy title from the article content
        article_title = self._generate_title(article_content, topic)
        
        # Extract and validate citations
        citations = []
        if include_citations:
            # Try LLM-based extraction first, fallback to regex
            from utils.text_processing import extract_citations_with_llm, extract_citations
            citations = extract_citations_with_llm(article_content, self.llm_client)
            if not citations:
                citations = extract_citations(article_content)
            
            citations = self._validate_citations(citations, relevant_sources)
            
            # Post-process citations to ensure they have source references
            article_content = self._add_missing_source_references(article_content, citations, relevant_sources)
        
        # Create metadata
        metadata = {
            "topic": topic,
            "length": length,
            "style": style,
            "generated_at": datetime.now().isoformat(),
            "sources_used": len(relevant_sources),
            "citations_count": len(citations),
            "model_used": self.llm_client.model_name,
            "word_count": len(article_content.split()),
            "overall_context_rating": self._calculate_overall_context_rating(article_content, relevant_sources),
            "context_rating_details": self._get_context_rating_details(article_content, relevant_sources)
        }
        
        result = {
            "title": article_title,
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
            
            # Optimize content length based on context window capacity
            # Claude 3.5 Haiku has 200k token context window - we can use much more!
            content = source.get('content', '')
            
            # Use longer content per source since we have massive context window available
            max_chars_per_source = 5000  # Increased from 2000 to 5000
            
            if len(content) > max_chars_per_source:
                content = content[:max_chars_per_source] + f"... [Content truncated at {max_chars_per_source} chars for processing efficiency]"
            
            source_text += f"Content: {content}\n"
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
    
    def _validate_word_count(self, article_content: str, length: str, topic: str, context: str, style: str, include_citations: bool) -> str:
        """Validate and adjust word count if necessary.
        
        Args:
            article_content: Generated article content
            length: Target length (short, medium, long)
            topic: Article topic
            context: Source context
            style: Writing style
            include_citations: Whether to include citations
            
        Returns:
            Article content with correct word count
        """
        word_count = len(article_content.split())
        
        # Define target word ranges
        length_ranges = {
            "short": (500, 800),
            "medium": (1000, 1500),
            "long": (2000, 3000)
        }
        
        target_min, target_max = length_ranges.get(length, (1000, 1500))
        
        # If word count is within range, return as is
        if target_min <= word_count <= target_max:
            logger.info(f"Article word count ({word_count}) is within target range ({target_min}-{target_max})")
            return article_content
        
        # If word count is too short or too long, regenerate with adjusted instructions
        logger.warning(f"Article word count ({word_count}) is outside target range ({target_min}-{target_max}). Regenerating...")
        
        # Create adjusted prompt for word count
        adjustment_prompt = f"""You previously generated an article that was {word_count} words, but the requirement is {target_min}-{target_max} words.

TOPIC: {topic}

ARTICLE REQUIREMENTS:
- Length: EXACTLY {target_min}-{target_max} words (CRITICAL REQUIREMENT)
- Style: {style}
- Ensure accuracy and factual correctness
- Maintain logical flow and structure

SOURCE CONTEXT:
{context}

INSTRUCTIONS:
1. Write a comprehensive article that is EXACTLY {target_min}-{target_max} words
2. Use information from the provided sources to support your arguments
3. Ensure all claims are backed by the source material
4. Count your words carefully and adjust content length accordingly
5. If too short, add more detail and analysis
6. If too long, be more concise while maintaining quality

Please generate the article with the correct word count:"""

        try:
            adjusted_content = self.llm_client.generate_text(
                prompt=adjustment_prompt,
                max_tokens=4000,
                temperature=0.1
            ).strip()
            
            new_word_count = len(adjusted_content.split())
            logger.info(f"Regenerated article word count: {new_word_count}")
            
            return adjusted_content
            
        except Exception as e:
            logger.warning(f"Failed to regenerate article for word count: {e}")
            return article_content  # Return original if regeneration fails
    
    def _generate_title(self, article_content: str, topic: str) -> str:
        """Generate a catchy title from article content.
        
        Args:
            article_content: The generated article content
            topic: Original topic
            
        Returns:
            Generated title
        """
        # Extract first few sentences for title generation
        sentences = article_content.split('.')[:3]
        content_preview = '. '.join(sentences) + '.'
        
        title_prompt = f"""Generate a catchy, engaging title for this article based on its content.

ARTICLE CONTENT PREVIEW:
{content_preview}

ORIGINAL TOPIC: {topic}

REQUIREMENTS:
- Title should be 6-12 words
- Should be engaging and clickable
- Should capture the main theme
- Should be professional but not boring
- Avoid generic phrases like "Analysis of" or "Overview of"

Generate only the title, no other text:"""

        try:
            title = self.llm_client.generate_text(
                prompt=title_prompt,
                max_tokens=50,
                temperature=0.7
            ).strip()
            
            # Clean up the title
            title = title.strip('"').strip("'").strip()
            if not title or len(title) < 5:
                # Fallback to topic-based title
                words = topic.split()[:6]
                title = ' '.join(words)
            
            return title
            
        except Exception as e:
            logger.warning(f"Failed to generate title: {e}")
            # Fallback to topic-based title
            words = topic.split()[:6]
            return ' '.join(words)
    
    def _validate_citations(
        self,
        citations: List[Dict[str, Any]],
        sources: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Validate extracted citations against source materials.
        
        Args:
            citations: List of extracted citation objects with position data
            sources: Source materials used
            
        Returns:
            List of validated citations with metadata
        """
        validated_citations = []
        
        for citation in citations:
            citation_text = citation["text"]
            
            # Initialize citation info with position data
            citation_info = {
                "text": citation_text,
                "type": citation.get("type", "unknown"),
                "position": citation["position"],
                "validated": True,
                "source_found": False,
                "confidence": 0.0,
                "source_number": None
            }
            
            # Enhanced citation validation - check for quotes and references
            best_match = None
            best_confidence = 0.0
            
            logger.debug(f"Validating citation: '{citation_text}'")
            
            for source in sources:
                source_content = source.get('content', '')
                source_lower = source_content.lower()
                citation_lower = citation_text.lower()
                
                logger.debug(f"Checking against source {source.get('source_number')}: {source_content[:100]}...")
                
                # Check for exact quote matches (in quotes)
                if citation_lower.startswith('"') and citation_lower.endswith('"'):
                    # Extract the quote without quotes
                    quote_text = citation_lower.strip('"').strip()
                    
                    logger.debug(f"Checking quote match: '{quote_text}'")
                    
                    # Try exact match first
                    if quote_text in source_lower:
                        logger.debug(f"Found exact quote match in source {source.get('source_number')}")
                        citation_info["source_found"] = True
                        citation_info["confidence"] = 0.9  # Very high confidence for exact quotes
                        citation_info["source_number"] = source.get('source_number')
                        best_match = source
                        best_confidence = 0.9
                        break
                    
                    # Try partial match for long quotes (sometimes quotes are truncated)
                    elif len(quote_text) > 20:
                        # Check if first 20 characters match
                        quote_start = quote_text[:20].lower()
                        if quote_start in source_lower:
                            logger.debug(f"Found partial quote match in source {source.get('source_number')}")
                            citation_info["source_found"] = True
                            citation_info["confidence"] = 0.8  # High confidence for partial quote matches
                            citation_info["source_number"] = source.get('source_number')
                            best_match = source
                            best_confidence = 0.8
                            break
                    
                    # Try word-by-word matching for short phrases
                    elif len(quote_text.split()) <= 5:
                        quote_words = quote_text.split()
                        source_words = source_lower.split()
                        
                        # Check if all words from quote appear in source (in order)
                        if len(quote_words) > 0:
                            word_matches = 0
                            for word in quote_words:
                                if word in source_words:
                                    word_matches += 1
                            
                            if word_matches == len(quote_words):
                                logger.debug(f"Found word-by-word match in source {source.get('source_number')}")
                                citation_info["source_found"] = True
                                citation_info["confidence"] = 0.7  # Good confidence for word matches
                                citation_info["source_number"] = source.get('source_number')
                                best_match = source
                                best_confidence = 0.7
                                break
                
                # Check for source reference matches [Source X]
                elif citation_lower.startswith('[source') and citation_lower.endswith(']'):
                    # Extract source number
                    try:
                        source_num = int(citation_lower.split()[1].rstrip(']'))
                        if source.get('source_number') == source_num:
                            citation_info["source_found"] = True
                            citation_info["confidence"] = 0.8  # High confidence for correct source reference
                            citation_info["source_number"] = source_num
                            best_match = source
                            best_confidence = 0.8
                            break
                    except (ValueError, IndexError):
                        pass
                
                # Check for partial text matches
                elif citation_lower in source_lower:
                    confidence = 0.7  # Good confidence for partial matches
                    if confidence > best_confidence:
                        best_match = source
                        best_confidence = confidence
                
                # Check for semantic similarity
                elif self._calculate_similarity(citation_text, source_content) > 0.6:
                    confidence = 0.6  # Medium confidence for similar content
                    if confidence > best_confidence:
                        best_match = source
                        best_confidence = confidence
            
            # Apply best match if found
            if best_match and best_confidence > 0.5:
                citation_info["source_found"] = True
                citation_info["confidence"] = best_confidence
                citation_info["source_number"] = best_match.get('source_number')
            
            validated_citations.append(citation_info)
        
        return validated_citations
    
    def _add_missing_source_references(self, article_content: str, citations: List[Dict[str, Any]], sources: List[Dict[str, Any]]) -> str:
        """Add missing source references to quotes that don't have them, preventing duplicates.
        
        Args:
            article_content: The article content
            citations: List of validated citations
            sources: List of sources
            
        Returns:
            Article content with added source references
        """
        import re
        
        # First, clean up any malformed citations
        article_content = self._clean_malformed_citations(article_content)
        
        # Find quotes that don't have source references
        quote_pattern = r'"([^"]*)"'
        quotes = list(re.finditer(quote_pattern, article_content))
        
        # Process quotes in reverse order to avoid position shifts
        for quote_match in reversed(quotes):
            quote_text = quote_match.group(1)
            quote_start = quote_match.start()
            quote_end = quote_match.end()
            
            # Check if this quote already has a source reference after it
            after_quote = article_content[quote_end:quote_end + 30]
            if not re.search(r'\[Source \d+\]', after_quote):
                # Find the best matching source for this quote
                best_source = None
                best_confidence = 0.0
                
                for source in sources:
                    source_content = source.get('content', '').lower()
                    quote_lower = quote_text.lower()
                    
                    if quote_lower in source_content:
                        best_source = source
                        best_confidence = 0.9
                        break
                    elif len(quote_text.split()) <= 5:
                        quote_words = quote_text.split()
                        source_words = source_content.split()
                        word_matches = sum(1 for word in quote_words if word in source_words)
                        if word_matches == len(quote_words) and word_matches > best_confidence:
                            best_source = source
                            best_confidence = 0.7
                
                # Add source reference if we found a match
                if best_source and best_confidence > 0.5:
                    source_num = best_source.get('source_number')
                    if source_num:
                        # Insert source reference after the quote
                        article_content = (article_content[:quote_end] + 
                                         f" [Source {source_num}]" + 
                                         article_content[quote_end:])
        
        return article_content
    
    def _clean_malformed_citations(self, article_content: str) -> str:
        """Clean up malformed citations like [?], [Source], [Source X] [X], etc.
        
        Args:
            article_content: The article content
            
        Returns:
            Cleaned article content
        """
        import re
        
        # Remove [?] citations
        article_content = re.sub(r'\[\?\]', '', article_content)
        
        # Remove standalone [Source] without numbers
        article_content = re.sub(r'\[Source\]', '', article_content)
        
        # Fix duplicate citations like [Source 1] [1] -> [Source 1]
        article_content = re.sub(r'\[Source (\d+)\] \[\1\]', r'[Source \1]', article_content)
        
        # Fix mixed citations like [Source 1] [2] -> [Source 1]
        article_content = re.sub(r'\[Source (\d+)\] \[\d+\]', r'[Source \1]', article_content)
        
        # Remove standalone numbers in brackets that aren't source references
        article_content = re.sub(r'(?<!Source )\[\d+\]', '', article_content)
        
        # Clean up extra spaces
        article_content = re.sub(r'\s+', ' ', article_content)
        
        return article_content
    
    def _calculate_overall_context_rating(self, article_content: str, sources: List[Dict[str, Any]]) -> float:
        """Calculate overall context rating for the article against knowledge base.
        
        Args:
            article_content: The article content
            sources: List of sources used
            
        Returns:
            Overall context rating between 0 and 1
        """
        if not sources:
            return 0.0
        
        # Extract all citations from the article
        from utils.text_processing import extract_citations_with_llm, extract_citations
        citations = extract_citations_with_llm(article_content, self.llm_client)
        if not citations:
            citations = extract_citations(article_content)
        
        # Also check for source references like (Source X) or [Source X]
        import re
        source_refs = re.findall(r'\(Source\s+(\d+)\)|\[Source\s+(\d+)\]', article_content, re.IGNORECASE)
        source_numbers = [int(ref[0] or ref[1]) for ref in source_refs]
        
        logger.info(f"Found {len(citations)} citations and {len(source_numbers)} source references")
        
        if not citations and not source_numbers:
            logger.warning("No citations or source references found in article")
            return 0.0
        
        # Calculate citation-based rating
        citation_rating = 0.0
        if citations:
            total_confidence = 0.0
            valid_citations = 0
            
            for citation in citations:
                citation_text = citation["text"]
                best_confidence = 0.0
                
                # Check against all sources
                for source in sources:
                    source_content = source.get('content', '').lower()
                    citation_lower = citation_text.lower()
                    
                    # Check for exact matches
                    if citation_lower in source_content:
                        best_confidence = max(best_confidence, 0.9)
                    elif len(citation_text.split()) <= 5:
                        # Word-by-word matching for short phrases
                        quote_words = citation_text.split()
                        source_words = source_content.split()
                        word_matches = sum(1 for word in quote_words if word in source_words)
                        if word_matches == len(quote_words):
                            best_confidence = max(best_confidence, 0.7)
                
                total_confidence += best_confidence
                if best_confidence > 0:
                    valid_citations += 1
            
            if valid_citations > 0:
                citation_coverage = valid_citations / len(citations)
                average_confidence = total_confidence / len(citations)
                citation_rating = (citation_coverage * 0.4) + (average_confidence * 0.6)
        
        # Calculate source reference rating
        source_ref_rating = 0.0
        if source_numbers:
            # Check if referenced sources exist in the knowledge base
            valid_sources = 0
            for source_num in source_numbers:
                if 1 <= source_num <= len(sources):
                    valid_sources += 1
            
            source_ref_rating = valid_sources / len(source_numbers) if source_numbers else 0.0
        
        # Calculate content-source alignment rating
        content_alignment_rating = 0.0
        if sources:
            # Check if article content aligns with source topics
            article_words = set(article_content.lower().split())
            source_words = set()
            for source in sources:
                source_content = source.get('content', '')
                source_words.update(source_content.lower().split())
            
            # Calculate word overlap
            common_words = article_words.intersection(source_words)
            if len(article_words) > 0:
                content_alignment_rating = len(common_words) / len(article_words)
        
        # Combine ratings with weights
        overall_rating = (
            citation_rating * 0.5 +      # Citation quality (50%)
            source_ref_rating * 0.3 +    # Source reference validity (30%)
            content_alignment_rating * 0.2  # Content-source alignment (20%)
        )
        
        logger.info(f"Overall context rating: {overall_rating:.2f} (citation: {citation_rating:.2f}, source_ref: {source_ref_rating:.2f}, alignment: {content_alignment_rating:.2f})")
        
        return min(overall_rating, 1.0)  # Cap at 1.0
    
    def _get_context_rating_details(self, article_content: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get detailed context rating breakdown for explanation.
        
        Args:
            article_content: The article content
            sources: List of sources used
            
        Returns:
            Dictionary with detailed rating breakdown
        """
        if not sources:
            return {
                "overall_rating": 0.0,
                "citation_quality": 0.0,
                "source_reference_validity": 0.0,
                "content_source_alignment": 0.0,
                "citations_found": 0,
                "source_references_found": 0,
                "valid_sources_referenced": 0,
                "total_sources_available": len(sources),
                "explanation": "No sources available for validation"
            }
        
        # Extract citations and source references
        from utils.text_processing import extract_citations_with_llm, extract_citations
        citations = extract_citations_with_llm(article_content, self.llm_client)
        if not citations:
            citations = extract_citations(article_content)
        import re
        source_refs = re.findall(r'\(Source\s+(\d+)\)|\[Source\s+(\d+)\]', article_content, re.IGNORECASE)
        source_numbers = [int(ref[0] or ref[1]) for ref in source_refs]
        
        # Calculate citation quality
        citation_quality = 0.0
        if citations:
            total_confidence = 0.0
            valid_citations = 0
            
            for citation in citations:
                citation_text = citation["text"]
                best_confidence = 0.0
                
                for source in sources:
                    source_content = source.get('content', '').lower()
                    citation_lower = citation_text.lower()
                    
                    if citation_lower in source_content:
                        best_confidence = max(best_confidence, 0.9)
                    elif len(citation_text.split()) <= 5:
                        quote_words = citation_text.split()
                        source_words = source_content.split()
                        word_matches = sum(1 for word in quote_words if word in source_words)
                        if word_matches == len(quote_words):
                            best_confidence = max(best_confidence, 0.7)
                
                total_confidence += best_confidence
                if best_confidence > 0:
                    valid_citations += 1
            
            if valid_citations > 0:
                citation_coverage = valid_citations / len(citations)
                average_confidence = total_confidence / len(citations)
                citation_quality = (citation_coverage * 0.4) + (average_confidence * 0.6)
        
        # Calculate source reference validity
        source_reference_validity = 0.0
        valid_sources_referenced = 0
        if source_numbers:
            for source_num in source_numbers:
                if 1 <= source_num <= len(sources):
                    valid_sources_referenced += 1
            source_reference_validity = valid_sources_referenced / len(source_numbers) if source_numbers else 0.0
        
        # Calculate content-source alignment
        content_source_alignment = 0.0
        if sources:
            article_words = set(article_content.lower().split())
            source_words = set()
            for source in sources:
                source_content = source.get('content', '')
                source_words.update(source_content.lower().split())
            
            common_words = article_words.intersection(source_words)
            if len(article_words) > 0:
                content_source_alignment = len(common_words) / len(article_words)
        
        # Calculate overall rating
        overall_rating = (
            citation_quality * 0.5 +
            source_reference_validity * 0.3 +
            content_source_alignment * 0.2
        )
        
        # Generate explanation
        explanation_parts = []
        if citation_quality > 0.7:
            explanation_parts.append("Strong citation quality with direct quotes from sources")
        elif citation_quality > 0.4:
            explanation_parts.append("Moderate citation quality with some source validation")
        else:
            explanation_parts.append("Low citation quality - few or no validated citations")
        
        if source_reference_validity > 0.7:
            explanation_parts.append("Most source references are valid")
        elif source_reference_validity > 0.4:
            explanation_parts.append("Some source references are valid")
        else:
            explanation_parts.append("Few or no valid source references")
        
        if content_source_alignment > 0.7:
            explanation_parts.append("High content-source alignment")
        elif content_source_alignment > 0.4:
            explanation_parts.append("Moderate content-source alignment")
        else:
            explanation_parts.append("Low content-source alignment")
        
        explanation = ". ".join(explanation_parts) + "."
        
        return {
            "overall_rating": min(overall_rating, 1.0),
            "citation_quality": citation_quality,
            "source_reference_validity": source_reference_validity,
            "content_source_alignment": content_source_alignment,
            "citations_found": len(citations),
            "source_references_found": len(source_numbers),
            "valid_sources_referenced": valid_sources_referenced,
            "total_sources_available": len(sources),
            "explanation": explanation,
            "detailed_breakdown": {
                "direct_quotations": {
                    "count": len([c for c in citations if c.get("type") == "quoted_text"]),
                    "accuracy_score": citation_quality,
                    "explanation": f"Found {len([c for c in citations if c.get('type') == 'quoted_text'])} direct quotations with {citation_quality:.1%} accuracy"
                },
                "context_citations": {
                    "count": len([c for c in citations if c.get("type") in ["attribution", "reference"]]),
                    "validity_score": source_reference_validity,
                    "explanation": f"Found {len([c for c in citations if c.get('type') in ['attribution', 'reference']])} context citations with {source_reference_validity:.1%} validity"
                },
                "source_coverage": {
                    "sources_referenced": valid_sources_referenced,
                    "total_sources": len(sources),
                    "coverage_score": valid_sources_referenced / len(sources) if sources else 0,
                    "explanation": f"Referenced {valid_sources_referenced} out of {len(sources)} available sources"
                },
                "content_alignment": {
                    "alignment_score": content_source_alignment,
                    "explanation": f"Article content shows {content_source_alignment:.1%} alignment with source material"
                }
            }
        }
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts."""
        from utils.text_processing import calculate_text_similarity
        return calculate_text_similarity(text1, text2)
    
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
