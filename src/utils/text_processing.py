"""Text processing utilities."""

import re
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path


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


def extract_citations(text: str) -> List[str]:
    """Extract citations from text.
    
    Args:
        text: Input text
        
    Returns:
        List of extracted citations
    """
    citations = []
    
    # Common citation patterns
    patterns = [
        r'\[Source \d+\]',  # [Source 1], [Source 2], etc.
        r'\[\d+\]',         # [1], [2], etc.
        r'\([^)]*\d+[^)]*\)',  # (Author, 2023), etc.
        r'"[^"]*"',         # Quoted text
        r'\b(?:according to|as stated by|in the words of)\s+[^.]*',  # Attribution phrases
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        citations.extend(matches)
    
    # Remove duplicates
    citations = list(set(citations))
    
    return citations


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
