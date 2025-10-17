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
        confidence_threshold: float = 0.8,
        citations: Optional[List[str]] = None
    ) -> List[CitationValidationResult]:
        """Validate all citations in an article.
        
        Args:
            article_content: The article content to validate
            sources: Source materials used
            confidence_threshold: Minimum confidence threshold
            citations: Pre-extracted citations (optional, will extract if not provided)
            
        Returns:
            List of validation results for each citation
        """
        logger.info("Starting citation validation")
        
        # Use provided citations or extract them
        if citations is None:
            citations = self._extract_citations(article_content)
            logger.info(f"Extracted {len(citations)} citations to validate")
        else:
            logger.info(f"Using {len(citations)} pre-extracted citations for validation")
        
        # No longer limiting citations since batch processing is efficient
        logger.info(f"Processing all {len(citations)} citations using batch validation")
        
        validation_results = []
        
        # Try batch validation first (more efficient)
        if len(citations) > 1:
            logger.info(f"Attempting batch validation for {len(citations)} citations")
            
            # For large numbers of citations, process in chunks to avoid token limits
            chunk_size = 20  # Process 20 citations at a time
            all_batch_results = []
            
            for i in range(0, len(citations), chunk_size):
                chunk = citations[i:i + chunk_size]
                logger.info(f"Processing citation chunk {i//chunk_size + 1}/{(len(citations)-1)//chunk_size + 1}: {len(chunk)} citations")
                
                batch_results = self._validate_citations_batch(chunk, sources)
                if batch_results:
                    all_batch_results.extend(batch_results)
                else:
                    logger.warning(f"Batch validation failed for chunk {i//chunk_size + 1}, falling back to individual validation")
                    # Fallback to individual validation for this chunk
                    for citation in chunk:
                        result = self._validate_single_citation(citation, sources)
                        all_batch_results.append(result)
            
            validation_results = all_batch_results
        else:
            # Single citation - use individual validation
            for i, citation in enumerate(citations, 1):
                logger.info(f"Validating citation {i}/{len(citations)}: {citation[:50]}...")
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
    
    def _validate_citations_batch(
        self,
        citations: List[str],
        sources: List[Dict[str, Any]]
    ) -> Optional[List[CitationValidationResult]]:
        """Validate multiple citations in a single LLM call.
        
        Args:
            citations: List of citations to validate
            sources: Available source materials
            
        Returns:
            List of validation results or None if batch validation fails
        """
        try:
            # Create context from sources (only once for all citations)
            source_context = "\n\n".join([
                f"Source {i+1}: {source.get('content', '')[:1000]}"
                for i, source in enumerate(sources[:5])  # Limit context size
            ])
            
            # Format citations for batch processing
            citations_text = "\n".join([
                f"{i+1}. {citation}" for i, citation in enumerate(citations)
            ])
            
            prompt = f"""You are a citation validation expert. Analyze the following citations and determine their accuracy based on the provided sources.

CITATIONS TO VALIDATE:
{citations_text}

SOURCE MATERIALS:
{source_context}

CRITICAL: You must respond with ONLY valid JSON. No explanations, no markdown, no additional text. Start with {{ and end with }}.

Return your analysis in this exact JSON format:
{{
    "results": [
        {{
            "citation_number": 1,
            "citation_text": "exact citation text from list",
            "is_accurate": true,
            "accuracy_score": 0.8,
            "source_found": true,
            "source_id": "entry_1_1234",
            "issues": [],
            "confidence": 0.8
        }},
        {{
            "citation_number": 2,
            "citation_text": "exact citation text from list",
            "is_accurate": false,
            "accuracy_score": 0.2,
            "source_found": false,
            "source_id": null,
            "issues": ["Citation not found in sources"],
            "confidence": 0.2
        }}
    ]
}}"""

            response = self.llm_client.generate_text(
                prompt=prompt,
                max_tokens=8000,  # Much larger response for many citations
                temperature=0.0
            )
            
            # Parse JSON response with better error handling
            import json
            response_clean = response.strip()
            
            # Try to extract JSON from response if it's wrapped in other text
            if not response_clean.startswith('{'):
                # Look for JSON in the response
                start_idx = response_clean.find('{')
                end_idx = response_clean.rfind('}')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    response_clean = response_clean[start_idx:end_idx+1]
            
            result = json.loads(response_clean)
            
            # Convert to CitationValidationResult objects
            validation_results = []
            for item in result.get('results', []):
                validation_result = CitationValidationResult(
                    citation_text=item.get('citation_text', ''),
                    is_accurate=item.get('is_accurate', False),
                    accuracy_score=item.get('accuracy_score', 0.0),
                    exact_match=False,  # Not applicable for batch processing
                    fuzzy_match_score=0.0,  # Not applicable for batch processing
                    source_found=item.get('source_found', False),
                    source_id=item.get('source_id'),
                    issues=item.get('issues', []),
                    confidence=item.get('confidence', 0.0)
                )
                validation_results.append(validation_result)
            
            logger.info(f"Batch validation successful for {len(validation_results)} citations")
            return validation_results
            
        except Exception as e:
            logger.error(f"Batch validation failed: {e}")
            return None
    
    def _extract_citations(self, text: str) -> List[str]:
        """Extract potential citations from text with improved quote detection.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of extracted citation strings
        """
        citations = []
        
        # Enhanced patterns for better quote detection
        enhanced_patterns = [
            # Direct quotes with quotation marks
            r'"([^"]{20,200})"',  # Quoted text 20-200 chars
            r'"([^"]{50,500})"',  # Longer quotes 50-500 chars
            
            # Source references
            r'\[Source \d+\]',  # [Source X] references
            
            # According to patterns
            r'According to [^.]{10,100}\.',  # According to X.
            r'Research from [^.]{10,100}\.',  # Research from X.
            r'Studies show [^.]{10,100}\.',  # Studies show X.
            
            # Statistical/percentage patterns
            r'\d+% of [^.]{5,50}\.',  # X% of Y.
            r'\d+ out of \d+ [^.]{5,50}\.',  # X out of Y Z.
            
            # Specific phrase patterns that are likely citations
            r'(?:the|a|an) \w+ (?:study|research|survey|report|analysis) [^.]{10,100}\.',
            r'(?:findings|results|data) [^.]{10,100}\.',
            
            # Names and titles that suggest citations
            r'(?:Dr\.|Professor|Mr\.|Ms\.) [A-Z][a-z]+ [A-Z][a-z]+[^.]{5,50}\.',
        ]
        
        # Combine with existing patterns
        all_patterns = self.citation_patterns + enhanced_patterns
        
        for pattern in all_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            citations.extend(matches)
        
        # Remove duplicates and clean up
        citations = list(set(citations))
        citations = [self._clean_citation(c) for c in citations]
        
        # Filter out very short or very long citations (likely not real quotes)
        citations = [c for c in citations if 10 <= len(c) <= 500]
        
        # Remove citations that are just common words/phrases
        common_phrases = {
            'according to', 'research shows', 'studies indicate', 'findings suggest',
            'data shows', 'results indicate', 'analysis reveals', 'survey shows'
        }
        citations = [c for c in citations if not any(phrase in c.lower() for phrase in common_phrases)]
        
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
        # Handle [Source X] format citations differently
        if re.match(r'\[Source \d+\]', citation):
            return self._validate_source_reference(citation, sources)
        
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
    
    def _validate_source_reference(
        self,
        citation: str,
        sources: List[Dict[str, Any]]
    ) -> CitationValidationResult:
        """Validate a [Source X] reference against available sources.
        
        Args:
            citation: [Source X] format citation
            sources: Available source materials
            
        Returns:
            Validation result
        """
        # Extract source number from [Source X] format
        match = re.match(r'\[Source (\d+)\]', citation)
        if not match:
            return CitationValidationResult(
                citation_text=citation,
                is_accurate=False,
                accuracy_score=0.0,
                exact_match=False,
                fuzzy_match_score=0.0,
                source_found=False,
                issues=["Invalid source reference format"],
                confidence=0.0
            )
        
        source_number = int(match.group(1))
        
        # Check if we have a source with this number
        # Sources should be indexed starting from 1 in the context
        if source_number <= len(sources):
            source = sources[source_number - 1]  # Convert to 0-based index
            return CitationValidationResult(
                citation_text=citation,
                is_accurate=True,
                accuracy_score=1.0,
                exact_match=True,
                fuzzy_match_score=1.0,
                source_found=True,
                source_id=source.get('id'),
                confidence=1.0
            )
        else:
            return CitationValidationResult(
                citation_text=citation,
                is_accurate=False,
                accuracy_score=0.0,
                exact_match=False,
                fuzzy_match_score=0.0,
                source_found=False,
                issues=[f"Source {source_number} not found in available sources"],
                confidence=0.0
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
        
        prompt = f"""You are a citation validation expert. Analyze the following citation and determine its accuracy based on the provided sources.

CITATION TO VALIDATE:
{citation}

SOURCE MATERIALS:
{source_context}

CRITICAL: You must respond with ONLY valid JSON. No explanations, no markdown, no additional text. Start with {{ and end with }}.

Return your analysis in this exact JSON format:
{{
    "is_accurate": true,
    "accuracy_score": 0.8,
    "source_found": true,
    "source_id": "entry_1_1234",
    "issues": [],
    "confidence": 0.8
}}"""

        try:
            response = self.llm_client.generate_text(
                prompt=prompt,
                max_tokens=500,
                temperature=0.0
            )
            
            # Parse JSON response with better error handling
            import json
            response_clean = response.strip()
            
            # Try to extract JSON from response if it's wrapped in other text
            if not response_clean.startswith('{'):
                # Look for JSON in the response
                start_idx = response_clean.find('{')
                end_idx = response_clean.rfind('}')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    response_clean = response_clean[start_idx:end_idx+1]
            
            result = json.loads(response_clean)
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
