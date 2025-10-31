"""Text processing utilities.

This module provides utilities for:
- Text preprocessing and normalization
- Citation extraction from articles (regex and LLM-based)
- Quote text cleaning and source marker removal
- Text similarity calculations
"""

import logging
import re
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


def preprocess_text(text: str) -> str:
    """Preprocess text for analysis.
    
    Args:
        text: Input text
        
    Returns:
        Preprocessed text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?;:\-()"\']', ' ', text)
    
    # Normalize quotes
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    
    return text.strip()


def extract_citations(text: str) -> List[Dict[str, Any]]:
    """Extract citations by finding [Source X] markers and looking backward for the quote.
    
    The correct approach: Find [Source X] markers, then look BEFORE them to extract
    the quoted text that the source is referencing.
    
    Args:
        text: Input text
        
    Returns:
        List of citation objects with text and position data
    """
    citations = []
    
    # Find all [Source X] markers in the text
    source_pattern = r'\[Source\s+(\d+)\]'
    
    for match in re.finditer(source_pattern, text, re.IGNORECASE):
        source_number = int(match.group(1))
        source_marker_start = match.start()
        source_marker_end = match.end()
        
        # Look backward from the source marker to find the quote
        text_before_source = text[:source_marker_start]
        
        # Try to find the quote that precedes this source marker
        # Pattern 1: Look for quoted text immediately before [Source X]
        # Example: "this is a quote" [Source 1]
        quote_pattern = r'"([^"]+)"\s*$'
        quote_match = re.search(quote_pattern, text_before_source)
        
        if quote_match:
            # Found a quote before the source marker
            quote_text = quote_match.group(1).strip()
            quote_start = quote_match.start()
            quote_end = quote_match.end()
            
            # Only include if quote is substantial (at least 15 words)
            word_count = len(quote_text.split())
            if word_count < 15:
                logger.debug(f"Skipping short quote ({word_count} words): {quote_text[:50]}...")
                continue
            
            citation_obj = {
                "text": f'"{quote_text}"',  # Include the quotes in the text
                "type": "quoted_text",
                "position": {
                    "start": quote_start,
                    "end": source_marker_end  # Include the source marker in the position
                },
                "validated": False,
                "source_found": False,
                "confidence": 0.0,
                "source_number": source_number,
                "context": "",
                "validation_notes": ""
            }
            
            citations.append(citation_obj)
            logger.debug(f"Extracted citation: {quote_text[:80]}... [Source {source_number}]")
        else:
            # No quote found - this is likely a source-only reference, skip it
            logger.debug(f"Skipping source-only reference [Source {source_number}] at position {source_marker_start}")
            continue
    
    # Remove duplicate citations (same position)
    unique_citations = []
    seen_positions = set()
    for citation in citations:
        pos_key = (citation["position"]["start"], citation["position"]["end"])
        if pos_key not in seen_positions:
            unique_citations.append(citation)
            seen_positions.add(pos_key)
    
    logger.info(f"Extracted {len(unique_citations)} unique citations from text")
    return unique_citations


def extract_citations_with_llm(text: str, llm_client=None) -> List[Dict[str, Any]]:
    """Extract citations using LLM for more sophisticated analysis.
    
    Args:
        text: Input text
        llm_client: LLM client for advanced extraction
        
    Returns:
        List of citation objects with enhanced analysis
    """
    if not llm_client:
        # Fallback to regex-based extraction
        return extract_citations(text)
    
    try:
        from article_generator.prompt_templates import PromptTemplates
        prompt_templates = PromptTemplates()
        prompt = prompt_templates.get_citation_extraction_prompt(text)
        
        # Get LLM response
        response = llm_client.generate_text_with_metadata(
            prompt=prompt,
            max_tokens=4000,
            temperature=0.1
        )
        
        if not response.success:
            logger.warning(f"LLM citation extraction failed: {response.error}")
            return extract_citations(text)
        
        # Parse JSON response
        import json
        try:
            result = json.loads(response.content)
            citations = result.get("citations", [])
            
            # Convert LLM response to standard format
            formatted_citations = []
            for citation in citations:
                formatted_citation = {
                    "text": citation.get("text", ""),
                    "type": citation.get("type", "reference"),
                    "position": {
                        "start": citation.get("position_start", 0),
                        "end": citation.get("position_end", 0)
                    },
                    "validated": False,
                    "source_found": False,
                    "confidence": citation.get("confidence", 0.0),
                    "source_number": None,
                    "context": citation.get("context", ""),
                    "validation_notes": citation.get("validation_notes", "")
                }
                
                # Extract source number from source_reference field
                source_ref = citation.get("source_reference", "")
                if source_ref:
                    source_match = re.search(r'(?:Source\s+)?(\d+)', source_ref, re.IGNORECASE)
                    if source_match:
                        formatted_citation["source_number"] = int(source_match.group(1))
                
                # Clean the citation text - remove any source markers that might be included
                citation_text = formatted_citation.get("text", "")
                if citation_text:
                    # Remove source markers from text
                    citation_text = re.sub(r'\s*\[Source\s+\d+\]', '', citation_text)
                    citation_text = re.sub(r'\s*\(Source\s+\d+\)', '', citation_text)
                    citation_text = re.sub(r'\s*\[\?\]', '', citation_text)
                    # If text is empty after cleaning, skip this citation
                    if not citation_text.strip() or citation_text.strip() == '""':
                        continue
                    formatted_citation["text"] = citation_text.strip()
                
                formatted_citations.append(formatted_citation)
            
            logger.info(f"LLM extracted {len(formatted_citations)} citations")
            return formatted_citations
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM citation response: {e}")
            return extract_citations(text)
            
    except Exception as e:
        logger.warning(f"LLM citation extraction error: {e}")
        return extract_citations(text)


def normalize_text(text: str) -> str:
    """Normalize text for comparison.
    
    Args:
        text: Input text
        
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove punctuation (keep basic sentence structure)
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Remove extra spaces
    text = text.strip()
    
    return text


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences.
    
    Args:
        text: Input text
        
    Returns:
        List of sentences
    """
    if not text:
        return []
    
    # Simple sentence splitting (in a real implementation, use spaCy or NLTK)
    sentences = re.split(r'[.!?]+', text)
    
    # Clean up and filter
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
    
    return sentences


def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate simple text similarity.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score between 0 and 1
    """
    if not text1 or not text2:
        return 0.0
    
    # Normalize texts
    text1_norm = normalize_text(text1)
    text2_norm = normalize_text(text2)
    
    # Split into words
    words1 = set(text1_norm.split())
    words2 = set(text2_norm.split())
    
    if not words1 and not words2:
        return 1.0
    if not words1 or not words2:
        return 0.0
    
    # Calculate Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union


def find_text_matches(
    target_text: str,
    source_text: str,
    similarity_threshold: float = 0.8
) -> List[Dict[str, Any]]:
    """Find similar text segments in source.
    
    Args:
        target_text: Text to search for
        source_text: Text to search in
        similarity_threshold: Minimum similarity threshold
        
    Returns:
        List of matches with similarity scores
    """
    matches = []
    
    # Split source into sentences
    sentences = split_into_sentences(source_text)
    
    for i, sentence in enumerate(sentences):
        similarity = calculate_text_similarity(target_text, sentence)
        
        if similarity >= similarity_threshold:
            matches.append({
                'text': sentence,
                'similarity': similarity,
                'position': i,
                'start_char': source_text.find(sentence),
                'end_char': source_text.find(sentence) + len(sentence)
            })
    
    # Sort by similarity score
    matches.sort(key=lambda x: x['similarity'], reverse=True)
    
    return matches


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract keywords from text.
    
    Args:
        text: Input text
        max_keywords: Maximum number of keywords to extract
        
    Returns:
        List of keywords
    """
    if not text:
        return []
    
    # Normalize text
    text = normalize_text(text)
    
    # Split into words
    words = text.split()
    
    # Remove common stop words (simplified list)
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'between', 'among', 'is', 'are',
        'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do',
        'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
        'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
        'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
    }
    
    # Filter words
    filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
    
    # Count word frequency
    word_counts = {}
    for word in filtered_words:
        word_counts[word] = word_counts.get(word, 0) + 1
    
    # Sort by frequency
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Return top keywords
    keywords = [word for word, count in sorted_words[:max_keywords]]
    
    return keywords


def clean_markdown(text: str) -> str:
    """Clean markdown formatting from text.
    
    Args:
        text: Markdown text
        
    Returns:
        Cleaned plain text
    """
    if not text:
        return ""
    
    # Remove markdown headers
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    
    # Remove bold and italic formatting
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    
    # Remove links
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    # Remove code blocks
    text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # Remove horizontal rules
    text = re.sub(r'^[-*_]{3,}$', '', text, flags=re.MULTILINE)
    
    # Clean up whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text.strip()


def format_citation(citation: str, citation_style: str = "apa") -> str:
    """Format citation according to specified style.
    
    Args:
        citation: Raw citation text
        citation_style: Citation style (apa, mla, chicago)
        
    Returns:
        Formatted citation
    """
    if not citation:
        return ""
    
    # Simple formatting (in a real implementation, use a proper citation formatter)
    if citation_style.lower() == "apa":
        # APA style formatting
        return f"({citation})"
    elif citation_style.lower() == "mla":
        # MLA style formatting
        return f"({citation})"
    elif citation_style.lower() == "chicago":
        # Chicago style formatting
        return f"({citation})"
    else:
        # Default formatting
        return f"[{citation}]"
