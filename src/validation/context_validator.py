"""Context validation for quotes and citations."""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
import numpy as np

from .nlp_processor import NLPProcessor
from ..llm.anthropic_client import AnthropicClient


logger = logging.getLogger(__name__)


@dataclass
class ContextValidationResult:
    """Result of context validation."""
    citation_text: str
    original_context: str
    article_context: str
    context_preserved: bool
    context_similarity_score: float
    semantic_similarity_score: float
    meaning_preserved: bool
    issues: List[str] = None
    confidence: float = 0.0
    detailed_analysis: str = ""
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []


class ContextValidator:
    """Validates that citations preserve original context and meaning."""
    
    def __init__(
        self,
        nlp_processor: NLPProcessor,
        llm_client: AnthropicClient,
        model_name: str = "all-MiniLM-L6-v2"
    ):
        """Initialize context validator.
        
        Args:
            nlp_processor: NLP processing utilities
            llm_client: LLM client for advanced validation
            model_name: Sentence transformer model name
        """
        self.nlp_processor = nlp_processor
        self.llm_client = llm_client
        self.sentence_model = SentenceTransformer(model_name)
        self.similarity_threshold = 0.7
    
    def validate_context(
        self,
        citations: List[str],
        sources: List[Dict[str, Any]],
        article_content: str
    ) -> List[ContextValidationResult]:
        """Validate context preservation for all citations.
        
        Args:
            citations: List of citations to validate
            sources: Source materials
            article_content: Full article content
            
        Returns:
            List of context validation results
        """
        logger.info(f"Starting context validation for {len(citations)} citations")
        
        # Try batch context validation first (much more efficient)
        if len(citations) > 1:
            logger.info(f"Attempting batch context validation for {len(citations)} citations")
            
            # For large numbers of citations, process in chunks to avoid token limits
            chunk_size = 15  # Process 15 citations at a time (context validation uses more tokens)
            all_batch_results = []
            
            for i in range(0, len(citations), chunk_size):
                chunk = citations[i:i + chunk_size]
                logger.info(f"Processing context validation chunk {i//chunk_size + 1}/{(len(citations)-1)//chunk_size + 1}: {len(chunk)} citations")
                
                batch_results = self._validate_context_batch(chunk, sources, article_content)
                if batch_results:
                    all_batch_results.extend(batch_results)
                else:
                    logger.warning(f"Batch context validation failed for chunk {i//chunk_size + 1}, falling back to individual validation")
                    # Fallback to individual validation for this chunk
                    for citation in chunk:
                        source_match = self._find_source_for_citation(citation, sources)
                        if source_match:
                            result = self._validate_single_context(citation, source_match, article_content)
                            all_batch_results.append(result)
                        else:
                            result = ContextValidationResult(
                                citation_text=citation,
                                original_context="",
                                article_context=self._extract_article_context(citation, article_content),
                                context_preserved=False,
                                context_similarity_score=0.0,
                                semantic_similarity_score=0.0,
                                meaning_preserved=False,
                                issues=["Source not found for citation"],
                                confidence=0.0,
                                detailed_analysis="Unable to validate context - source not found"
                            )
                            all_batch_results.append(result)
            
            logger.info(f"Batch context validation completed for {len(all_batch_results)} citations")
            return all_batch_results
        
        # Fallback to individual validation
        validation_results = []
        for citation in citations:
            # Find the source that contains this citation
            source_match = self._find_source_for_citation(citation, sources)
            
            if source_match:
                result = self._validate_single_context(
                    citation, source_match, article_content
                )
                validation_results.append(result)
            else:
                # Create result for unmatched citation
                result = ContextValidationResult(
                    citation_text=citation,
                    original_context="",
                    article_context=self._extract_article_context(citation, article_content),
                    context_preserved=False,
                    context_similarity_score=0.0,
                    semantic_similarity_score=0.0,
                    meaning_preserved=False,
                    issues=["Source not found for citation"],
                    confidence=0.0,
                    detailed_analysis="Unable to validate context - source not found"
                )
                validation_results.append(result)
        
        logger.info(f"Context validation complete for {len(validation_results)} citations")
        return validation_results
    
    def _validate_context_batch(
        self,
        citations: List[str],
        sources: List[Dict[str, Any]],
        article_content: str
    ) -> Optional[List[ContextValidationResult]]:
        """Validate multiple citations' context preservation in a single LLM call.
        
        Args:
            citations: List of citations to validate
            sources: Available source materials
            article_content: Full article content
            
        Returns:
            List of context validation results or None if batch validation fails
        """
        try:
            # Create context from sources (only once for all citations)
            source_context = "\n\n".join([
                f"Source {i+1}: {source.get('content', '')[:1000]}"
                for i, source in enumerate(sources[:5])  # Limit context size
            ])
            
            # Format citations with their article context for batch processing
            citations_with_context = []
            for i, citation in enumerate(citations, 1):
                article_context = self._extract_article_context(citation, article_content)
                citations_with_context.append(f"{i}. Citation: {citation}\n   Article Context: {article_context}")
            
            citations_text = "\n\n".join(citations_with_context)
            
            prompt = f"""You are a context analysis expert. Analyze whether the following citations preserve their original context and meaning when used in the article.

CITATIONS TO ANALYZE:
{citations_text}

SOURCE MATERIALS:
{source_context}

CRITICAL: You must respond with ONLY valid JSON. No explanations, no markdown, no additional text. Start with {{ and end with }}.

Return your analysis in this exact JSON format:
{{
    "results": [
        {{
            "citation_number": 1,
            "citation_text": "exact citation text",
            "context_preserved": true,
            "meaning_preserved": true,
            "confidence": 0.8,
            "issues": [],
            "analysis": "The citation maintains original meaning and context"
        }},
        {{
            "citation_number": 2,
            "citation_text": "exact citation text",
            "context_preserved": false,
            "meaning_preserved": false,
            "confidence": 0.3,
            "issues": ["Context changed", "Meaning altered"],
            "analysis": "The citation context and meaning have been altered"
        }}
    ]
}}"""

            response = self.llm_client.generate_text(
                prompt=prompt,
                max_tokens=12000,  # Much larger response for many citations
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
            
            # Try to fix common JSON issues
            try:
                result = json.loads(response_clean)
            except json.JSONDecodeError as e:
                # Try to fix common JSON issues
                logger.warning(f"JSON parsing failed: {e}. Attempting to fix common issues...")
                
                # Fix trailing commas
                response_clean = re.sub(r',\s*}', '}', response_clean)
                response_clean = re.sub(r',\s*]', ']', response_clean)
                
                # Fix unescaped quotes in strings
                response_clean = re.sub(r'(?<!\\)"(?=[^,}\]\s]*[,}\]])', '\\"', response_clean)
                
                try:
                    result = json.loads(response_clean)
                except json.JSONDecodeError as e2:
                    logger.error(f"JSON parsing still failed after fixes: {e2}")
                    logger.error(f"Response preview: {response_clean[:500]}...")
                    return None
            
            # Convert to ContextValidationResult objects
            validation_results = []
            for item in result.get('results', []):
                # Find original context from source
                citation_text = item.get('citation_text', '')
                source_match = self._find_source_for_citation(citation_text, sources)
                original_context = self._extract_source_context(citation_text, source_match.get('content', '')) if source_match else ""
                article_context = self._extract_article_context(citation_text, article_content)
                
                validation_result = ContextValidationResult(
                    citation_text=citation_text,
                    original_context=original_context,
                    article_context=article_context,
                    context_preserved=item.get('context_preserved', False),
                    context_similarity_score=0.8 if item.get('context_preserved', False) else 0.2,
                    semantic_similarity_score=0.8 if item.get('meaning_preserved', False) else 0.2,
                    meaning_preserved=item.get('meaning_preserved', False),
                    issues=item.get('issues', []),
                    confidence=item.get('confidence', 0.0),
                    detailed_analysis=item.get('analysis', '')
                )
                validation_results.append(validation_result)
            
            logger.info(f"Batch context validation successful for {len(validation_results)} citations")
            return validation_results
            
        except Exception as e:
            logger.error(f"Batch context validation failed: {e}")
            return None
    
    def _find_source_for_citation(
        self,
        citation: str,
        sources: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Find the source that contains the given citation.
        
        Args:
            citation: Citation to find
            sources: Available sources
            
        Returns:
            Matching source or None
        """
        citation_normalized = self.nlp_processor.normalize_text(citation)
        
        for source in sources:
            source_content = source.get('content', '')
            if citation_normalized in self.nlp_processor.normalize_text(source_content):
                return source
        
        return None
    
    def _validate_single_context(
        self,
        citation: str,
        source: Dict[str, Any],
        article_content: str
    ) -> ContextValidationResult:
        """Validate context for a single citation.
        
        Args:
            citation: Citation to validate
            source: Source material containing the citation
            article_content: Full article content
            
        Returns:
            Context validation result
        """
        # Extract original context from source
        original_context = self._extract_original_context(citation, source['content'])
        
        # Extract article context around citation
        article_context = self._extract_article_context(citation, article_content)
        
        # Calculate semantic similarity
        semantic_score = self._calculate_semantic_similarity(
            original_context, article_context
        )
        
        # Calculate context similarity (broader context)
        context_score = self._calculate_context_similarity(
            citation, original_context, article_context
        )
        
        # Use LLM for detailed analysis
        llm_analysis = self._analyze_with_llm(
            citation, original_context, article_context
        )
        
        # Determine if context is preserved
        context_preserved = (
            semantic_score >= self.similarity_threshold and
            context_score >= self.similarity_threshold and
            llm_analysis.get('context_preserved', False)
        )
        
        # Calculate overall confidence
        confidence = (
            semantic_score * 0.4 +
            context_score * 0.3 +
            llm_analysis.get('confidence', 0.0) * 0.3
        )
        
        return ContextValidationResult(
            citation_text=citation,
            original_context=original_context,
            article_context=article_context,
            context_preserved=context_preserved,
            context_similarity_score=context_score,
            semantic_similarity_score=semantic_score,
            meaning_preserved=llm_analysis.get('meaning_preserved', False),
            issues=llm_analysis.get('issues', []),
            confidence=confidence,
            detailed_analysis=llm_analysis.get('analysis', '')
        )
    
    def _extract_original_context(
        self,
        citation: str,
        source_content: str,
        context_window: int = 200
    ) -> str:
        """Extract original context around citation in source.
        
        Args:
            citation: Citation text
            source_content: Source content
            context_window: Number of characters around citation
            
        Returns:
            Original context string
        """
        # Find citation position in source
        citation_pos = source_content.lower().find(citation.lower())
        
        if citation_pos == -1:
            return ""
        
        # Extract context around citation
        start = max(0, citation_pos - context_window)
        end = min(len(source_content), citation_pos + len(citation) + context_window)
        
        return source_content[start:end].strip()
    
    def _extract_article_context(
        self,
        citation: str,
        article_content: str,
        context_window: int = 200
    ) -> str:
        """Extract article context around citation.
        
        Args:
            citation: Citation text
            article_content: Article content
            context_window: Number of characters around citation
            
        Returns:
            Article context string
        """
        # Find citation position in article
        citation_pos = article_content.lower().find(citation.lower())
        
        if citation_pos == -1:
            return ""
        
        # Extract context around citation
        start = max(0, citation_pos - context_window)
        end = min(len(article_content), citation_pos + len(citation) + context_window)
        
        return article_content[start:end].strip()
    
    def _extract_source_context(self, citation: str, source_content: str, context_window: int = 200) -> str:
        """Extract source context around citation.
        
        Args:
            citation: Citation text
            source_content: Source content
            context_window: Number of characters around citation
            
        Returns:
            Source context string
        """
        # Find citation position in source
        citation_pos = source_content.lower().find(citation.lower())
        
        if citation_pos == -1:
            return ""
        
        # Extract context around citation
        start = max(0, citation_pos - context_window)
        end = min(len(source_content), citation_pos + len(citation) + context_window)
        
        return source_content[start:end].strip()
    
    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0 and 1
        """
        if not text1 or not text2:
            return 0.0
        
        try:
            # Generate embeddings
            embeddings = self.sentence_model.encode([text1, text2])
            
            # Calculate cosine similarity
            similarity = np.dot(embeddings[0], embeddings[1]) / (
                np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
            )
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            return 0.0
    
    def _calculate_context_similarity(
        self,
        citation: str,
        original_context: str,
        article_context: str
    ) -> float:
        """Calculate broader context similarity.
        
        Args:
            citation: Citation text
            original_context: Original context from source
            article_context: Context from article
            
        Returns:
            Context similarity score
        """
        # Remove the citation itself from both contexts for comparison
        original_without_citation = original_context.replace(citation, "").strip()
        article_without_citation = article_context.replace(citation, "").strip()
        
        # Calculate semantic similarity of the surrounding context
        return self._calculate_semantic_similarity(
            original_without_citation, article_without_citation
        )
    
    def _analyze_with_llm(
        self,
        citation: str,
        original_context: str,
        article_context: str
    ) -> Dict[str, Any]:
        """Use LLM for detailed context analysis.
        
        Args:
            citation: Citation text
            original_context: Original context from source
            article_context: Context from article
            
        Returns:
            LLM analysis result
        """
        prompt = f"""You are a context analysis expert. Analyze whether the following citation preserves the original context and meaning when used in the article.

CITATION:
{citation}

ORIGINAL CONTEXT (from source):
{original_context}

ARTICLE CONTEXT (how it's used):
{article_context}

CRITICAL: You must respond with ONLY valid JSON. No explanations, no markdown, no additional text. Start with {{ and end with }}.

Return your analysis in this exact JSON format:
{{
    "context_preserved": true,
    "meaning_preserved": true,
    "confidence": 0.8,
    "issues": [],
    "analysis": "The citation maintains the original meaning and context"
}}"""

        try:
            response = self.llm_client.generate_text(
                prompt=prompt,
                max_tokens=500,
                temperature=0.0
            )
            
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
            logger.error(f"LLM context analysis failed: {e}")
            return {
                'context_preserved': False,
                'meaning_preserved': False,
                'confidence': 0.0,
                'issues': ['LLM analysis failed'],
                'analysis': 'Unable to analyze context due to technical error'
            }
