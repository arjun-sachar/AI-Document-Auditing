"""Citation validation and accuracy checking."""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from fuzzywuzzy import fuzz, process

from .nlp_processor import NLPProcessor
from ..llm.anthropic_client import AnthropicClient


logger = logging.getLogger(__name__)


@dataclass
class CitationValidationResult:
    """Result of citation validation."""
    citation_text: str
    is_accurate: bool
    accuracy_score: float
    exact_match: bool
    fuzzy_match_score: float
    source_found: bool
    source_id: Optional[str] = None
    issues: List[str] = None
    confidence: float = 0.0
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []


class CitationValidator:
    """Validates citations for accuracy and proper attribution."""
    
    def __init__(self, nlp_processor: NLPProcessor, llm_client: AnthropicClient):
        """Initialize citation validator.
        
        Args:
            nlp_processor: NLP processing utilities
            llm_client: LLM client for advanced validation
        """
        self.nlp_processor = nlp_processor
        self.llm_client = llm_client
        self.citation_patterns = [
            r'\[Source \d+\]',  # [Source 1], [Source 2], etc.
            r'\[\d+\]',         # [1], [2], etc.
            r'\([^)]*\d+[^)]*\)',  # (Author, 2023), etc.
            r'"[^"]*"',         # Quoted text
            r'\b(?:according to|as stated by|in the words of)\s+[^.]*',  # Attribution phrases
        ]
    
    def validate_citations(
        self,
        article_content: str,
        sources: List[Dict[str, Any]],
        confidence_threshold: float = 0.8
    ) -> List[CitationValidationResult]:
        """Validate all citations in an article.
        
        Args:
            article_content: The article content to validate
            sources: Source materials used
            confidence_threshold: Minimum confidence threshold
            
        Returns:
            List of validation results for each citation
        """
        logger.info("Starting citation validation")
        
        # Extract citations from article
        citations = self._extract_citations(article_content)
        logger.info(f"Found {len(citations)} citations to validate")
        
        validation_results = []
        
        for citation in citations:
            result = self._validate_single_citation(citation, sources)
            validation_results.append(result)
        
        # Filter by confidence threshold
        high_confidence_results = [
            r for r in validation_results if r.confidence >= confidence_threshold
        ]
        
        logger.info(
            f"Validation complete: {len(high_confidence_results)}/{len(validation_results)} "
            f"citations above confidence threshold"
        )
        
        return validation_results
    
    def _extract_citations(self, text: str) -> List[str]:
        """Extract potential citations from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of extracted citation strings
        """
        citations = []
        
        for pattern in self.citation_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            citations.extend(matches)
        
        # Remove duplicates and clean up
        citations = list(set(citations))
        citations = [self._clean_citation(c) for c in citations]
        
        return citations
    
    def _clean_citation(self, citation: str) -> str:
        """Clean and normalize citation text.
        
        Args:
            citation: Raw citation text
            
        Returns:
            Cleaned citation text
        """
        # Remove extra whitespace
        citation = re.sub(r'\s+', ' ', citation.strip())
        
        # Remove common citation markers for text extraction
        citation = re.sub(r'^\[Source \d+\]\s*', '', citation)
        citation = re.sub(r'^\[\d+\]\s*', '', citation)
        
        return citation
    
    def _validate_single_citation(
        self,
        citation: str,
        sources: List[Dict[str, Any]]
    ) -> CitationValidationResult:
        """Validate a single citation against source materials.
        
        Args:
            citation: Citation to validate
            sources: Available source materials
            
        Returns:
            Validation result
        """
        # Check for exact matches first
        exact_match, exact_source_id = self._find_exact_match(citation, sources)
        
        if exact_match:
            return CitationValidationResult(
                citation_text=citation,
                is_accurate=True,
                accuracy_score=1.0,
                exact_match=True,
                fuzzy_match_score=1.0,
                source_found=True,
                source_id=exact_source_id,
                confidence=1.0
            )
        
        # Check for fuzzy matches
        fuzzy_match_score, fuzzy_source_id = self._find_fuzzy_match(citation, sources)
        
        if fuzzy_match_score > 0.8:
            return CitationValidationResult(
                citation_text=citation,
                is_accurate=True,
                accuracy_score=fuzzy_match_score,
                exact_match=False,
                fuzzy_match_score=fuzzy_match_score,
                source_found=True,
                source_id=fuzzy_source_id,
                confidence=fuzzy_match_score
            )
        
        # Use LLM for advanced validation
        llm_result = self._validate_with_llm(citation, sources)
        
        return CitationValidationResult(
            citation_text=citation,
            is_accurate=llm_result.get('is_accurate', False),
            accuracy_score=llm_result.get('accuracy_score', 0.0),
            exact_match=False,
            fuzzy_match_score=fuzzy_match_score,
            source_found=llm_result.get('source_found', False),
            source_id=llm_result.get('source_id'),
            issues=llm_result.get('issues', []),
            confidence=llm_result.get('confidence', 0.0)
        )
    
    def _find_exact_match(
        self,
        citation: str,
        sources: List[Dict[str, Any]]
    ) -> Tuple[bool, Optional[str]]:
        """Find exact matches for citation in sources.
        
        Args:
            citation: Citation to match
            sources: Source materials
            
        Returns:
            Tuple of (found, source_id)
        """
        citation_normalized = self.nlp_processor.normalize_text(citation)
        
        for source in sources:
            source_content = source.get('content', '')
            if citation_normalized in self.nlp_processor.normalize_text(source_content):
                return True, source.get('id')
        
        return False, None
    
    def _find_fuzzy_match(
        self,
        citation: str,
        sources: List[Dict[str, Any]],
        threshold: float = 0.8
    ) -> Tuple[float, Optional[str]]:
        """Find fuzzy matches for citation in sources.
        
        Args:
            citation: Citation to match
            sources: Source materials
            threshold: Minimum similarity threshold
            
        Returns:
            Tuple of (best_score, source_id)
        """
        best_score = 0.0
        best_source_id = None
        
        for source in sources:
            source_content = source.get('content', '')
            
            # Extract potential matching text from source
            potential_matches = self._extract_potential_matches(citation, source_content)
            
            for match in potential_matches:
                score = fuzz.ratio(citation.lower(), match.lower()) / 100.0
                if score > best_score:
                    best_score = score
                    best_source_id = source.get('id')
        
        if best_score >= threshold:
            return best_score, best_source_id
        
        return 0.0, None
    
    def _extract_potential_matches(self, citation: str, source_content: str) -> List[str]:
        """Extract potential matching text segments from source.
        
        Args:
            citation: Citation to match
            source_content: Source content to search
            
        Returns:
            List of potential matching text segments
        """
        # Simple approach: extract sentences that contain similar words
        citation_words = set(citation.lower().split())
        sentences = self.nlp_processor.split_into_sentences(source_content)
        
        potential_matches = []
        for sentence in sentences:
            sentence_words = set(sentence.lower().split())
            overlap = len(citation_words.intersection(sentence_words))
            
            if overlap >= len(citation_words) * 0.5:  # At least 50% word overlap
                potential_matches.append(sentence)
        
        return potential_matches
    
    def _validate_with_llm(
        self,
        citation: str,
        sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Use LLM for advanced citation validation.
        
        Args:
            citation: Citation to validate
            sources: Source materials
            
        Returns:
            LLM validation result
        """
        # Create context from sources
        source_context = "\n\n".join([
            f"Source {i+1}: {source.get('content', '')[:1000]}"
            for i, source in enumerate(sources[:5])  # Limit context size
        ])
        
        prompt = f"""Analyze the following citation and determine its accuracy based on the provided sources.

CITATION TO VALIDATE:
{citation}

SOURCE MATERIALS:
{source_context}

Please provide your analysis in JSON format:
{{
    "is_accurate": true/false,
    "accuracy_score": 0.0-1.0,
    "source_found": true/false,
    "source_id": "source_id_if_found",
    "issues": ["list of specific issues"],
    "confidence": 0.0-1.0
}}"""

        try:
            response = self.llm_client.generate_text(
                prompt=prompt,
                max_tokens=500,
                temperature=0.0
            )
            
            # Parse JSON response
            import json
            result = json.loads(response.strip())
            return result
            
        except Exception as e:
            logger.error(f"LLM validation failed: {e}")
            return {
                'is_accurate': False,
                'accuracy_score': 0.0,
                'source_found': False,
                'issues': ['LLM validation failed'],
                'confidence': 0.0
            }
