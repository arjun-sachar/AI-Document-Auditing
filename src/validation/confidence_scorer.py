"""Confidence scoring algorithms for validation results.

This module calculates overall confidence scores by combining:
- Citation accuracy (40% weight)
- Context preservation (30% weight)
- Source reliability (20% weight)
- Scholarly coherence (10% weight)

Confidence scores range from 0.0-1.0 and are classified as:
- High: ≥0.8
- Medium: 0.6-0.79
- Low: <0.6
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.preprocessing import StandardScaler


logger = logging.getLogger(__name__)


@dataclass
class ConfidenceScore:
    """Confidence score result."""
    overall_confidence: float
    citation_accuracy_score: float
    context_preservation_score: float
    source_reliability_score: float
    coherence_score: float
    risk_factors: List[str]
    recommendations: List[str]
    detailed_breakdown: Dict[str, float]


class ConfidenceScorer:
    """Calculates confidence scores for document validation results."""
    
    def __init__(self):
        """Initialize confidence scorer."""
        self.scaler = StandardScaler()
        self.classifier = None
        self.feature_weights = {
            'citation_accuracy': 0.4,
            'context_preservation': 0.3,
            'source_reliability': 0.2,
            'text_coherence': 0.1
        }
    
    def calculate_overall_confidence(
        self,
        citation_results: List[Dict[str, Any]],
        context_results: List[Dict[str, Any]],
        article_metadata: Dict[str, Any],
        source_metadata: List[Dict[str, Any]] = None
    ) -> ConfidenceScore:
        """Calculate overall confidence score for document validation.
        
        Args:
            citation_results: Results from citation validation
            context_results: Results from context validation
            article_metadata: Article metadata
            source_metadata: Source metadata (optional)
            
        Returns:
            ConfidenceScore object
        """
        logger.info("Calculating overall confidence score")
        
        # Calculate individual component scores
        citation_score = self._calculate_citation_accuracy_score(citation_results)
        context_score = self._calculate_context_preservation_score(context_results)
        source_score = self._calculate_source_reliability_score(source_metadata)
        coherence_score = self._calculate_text_coherence_score(article_metadata)
        
        # Calculate weighted overall score
        overall_confidence = (
            citation_score * self.feature_weights['citation_accuracy'] +
            context_score * self.feature_weights['context_preservation'] +
            source_score * self.feature_weights['source_reliability'] +
            coherence_score * self.feature_weights['text_coherence']
        )
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(
            citation_results, context_results, article_metadata
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            citation_score, context_score, source_score, coherence_score
        )
        
        # Create detailed breakdown
        detailed_breakdown = {
            'citation_accuracy': citation_score,
            'context_preservation': context_score,
            'source_reliability': source_score,
            'text_coherence': coherence_score,
            'weighted_overall': overall_confidence
        }
        
        return ConfidenceScore(
            overall_confidence=overall_confidence,
            citation_accuracy_score=citation_score,
            context_preservation_score=context_score,
            source_reliability_score=source_score,
            coherence_score=coherence_score,
            risk_factors=risk_factors,
            recommendations=recommendations,
            detailed_breakdown=detailed_breakdown
        )
    
    def _calculate_citation_accuracy_score(
        self,
        citation_results: List[Dict[str, Any]]
    ) -> float:
        """Calculate citation accuracy score.
        
        Args:
            citation_results: Citation validation results (can be dicts or objects)
            
        Returns:
            Citation accuracy score between 0 and 1
        """
        if not citation_results:
            return 0.0
        
        def get_value(result, key, default=0.0):
            """Get value from result, handling both dict and object types."""
            if isinstance(result, dict):
                return result.get(key, default)
            else:
                return getattr(result, key, default)
        
        total_citations = len(citation_results)
        accurate_citations = sum(1 for r in citation_results if get_value(r, 'is_accurate', False))
        
        # Base accuracy ratio
        accuracy_ratio = accurate_citations / total_citations if total_citations > 0 else 0.0
        
        # Factor in confidence scores
        confidence_scores = [get_value(r, 'confidence', 0.0) for r in citation_results]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        # Combine accuracy and confidence (weighted: 60% accuracy ratio, 40% average confidence)
        # This ensures that both accuracy (exact matches) and confidence (quality of matches) matter
        final_score = (accuracy_ratio * 0.6) + (avg_confidence * 0.4)
        
        return min(1.0, max(0.0, final_score))
    
    def _calculate_context_preservation_score(
        self,
        context_results: List[Dict[str, Any]]
    ) -> float:
        """Calculate context preservation score.
        
        Args:
            context_results: Context validation results (can be dicts or objects)
            
        Returns:
            Context preservation score between 0 and 1
        """
        if not context_results:
            return 0.0
        
        def get_value(result, key, default=0.0):
            """Get value from result, handling both dict and object types."""
            if isinstance(result, dict):
                return result.get(key, default)
            else:
                return getattr(result, key, default)
        
        # Count citations with preserved context
        preserved_count = sum(1 for r in context_results if get_value(r, 'context_preserved', False))
        total_count = len(context_results)
        
        # Base preservation ratio
        preservation_ratio = preserved_count / total_count if total_count > 0 else 0.0
        
        # Factor in similarity scores (context similarity and semantic similarity)
        context_similarity_scores = [get_value(r, 'context_similarity_score', 0.0) for r in context_results]
        semantic_similarity_scores = [get_value(r, 'semantic_similarity_score', 0.0) for r in context_results]
        avg_context_similarity = sum(context_similarity_scores) / len(context_similarity_scores) if context_similarity_scores else 0.0
        avg_semantic_similarity = sum(semantic_similarity_scores) / len(semantic_similarity_scores) if semantic_similarity_scores else 0.0
        avg_similarity = (avg_context_similarity + avg_semantic_similarity) / 2.0
        
        # Factor in confidence scores from validation
        confidence_scores = [get_value(r, 'confidence', 0.0) for r in context_results]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        # Combine preservation ratio (40%), similarity (40%), and confidence (20%)
        final_score = (preservation_ratio * 0.4) + (avg_similarity * 0.4) + (avg_confidence * 0.2)
        
        return min(1.0, max(0.0, final_score))
    
    def _calculate_source_reliability_score(
        self,
        source_metadata: List[Dict[str, Any]] = None
    ) -> float:
        """Calculate source reliability score.
        
        Args:
            source_metadata: Source metadata (optional)
            
        Returns:
            Source reliability score between 0 and 1
        """
        if not source_metadata:
            return 0.8  # Default score when no source metadata available
        
        # Simple reliability scoring based on available metadata
        reliability_factors = []
        
        for source in source_metadata:
            source_score = 0.5  # Base score
            
            # Check for URL (indicates web source)
            if source.get('url'):
                source_score += 0.2
            
            # Check for author information
            if source.get('author'):
                source_score += 0.1
            
            # Check for publication date
            if source.get('publication_date'):
                source_score += 0.1
            
            # Check for source type (academic, news, etc.)
            source_type = source.get('type', '').lower()
            if source_type in ['academic', 'peer-reviewed', 'journal']:
                source_score += 0.1
            elif source_type in ['news', 'magazine']:
                source_score += 0.05
            
            reliability_factors.append(source_score)
        
        # Return average reliability score
        return sum(reliability_factors) / len(reliability_factors)
    
    def _calculate_text_coherence_score(
        self,
        article_metadata: Dict[str, Any]
    ) -> float:
        """Calculate text coherence score.
        
        Args:
            article_metadata: Article metadata
            
        Returns:
            Text coherence score between 0 and 1
        """
        # Simple coherence scoring based on article characteristics
        coherence_score = 0.7  # Base score
        
        word_count = article_metadata.get('word_count', 0)
        citations_count = article_metadata.get('citations_count', 0)
        sources_used = article_metadata.get('sources_used', 0)
        
        # Factor in citation density (appropriate number of citations)
        if word_count > 0:
            citation_density = citations_count / word_count * 1000  # citations per 1000 words
            if 5 <= citation_density <= 20:  # Reasonable citation density
                coherence_score += 0.1
            elif citation_density > 20:  # Too many citations
                coherence_score -= 0.1
        
        # Factor in source diversity
        if sources_used >= 3:  # Good source diversity
            coherence_score += 0.1
        elif sources_used < 2:  # Limited sources
            coherence_score -= 0.1
        
        # Factor in article length
        if 500 <= word_count <= 3000:  # Reasonable length
            coherence_score += 0.1
        elif word_count < 200:  # Too short
            coherence_score -= 0.1
        
        return min(1.0, max(0.0, coherence_score))
    
    def _identify_risk_factors(
        self,
        citation_results: List[Dict[str, Any]],
        context_results: List[Dict[str, Any]],
        article_metadata: Dict[str, Any]
    ) -> List[str]:
        """Identify risk factors in the document.
        
        Args:
            citation_results: Citation validation results
            context_results: Context validation results
            article_metadata: Article metadata
            
        Returns:
            List of identified risk factors
        """
        risk_factors = []
        
        def get_value(result, key, default=0.0):
            """Get value from result, handling both dict and object types."""
            if isinstance(result, dict):
                return result.get(key, default)
            else:
                return getattr(result, key, default)
        
        # Citation-related risks
        if citation_results:
            inaccurate_citations = sum(1 for r in citation_results if not get_value(r, 'is_accurate', False))
            if inaccurate_citations > len(citation_results) * 0.3:  # More than 30% inaccurate
                risk_factors.append("High number of inaccurate citations")
            
            low_confidence_citations = sum(1 for r in citation_results if get_value(r, 'confidence', 0) < 0.5)
            if low_confidence_citations > len(citation_results) * 0.3:  # More than 30% low confidence
                risk_factors.append(f"{low_confidence_citations} citations with low confidence scores (<50%)")
            
            # Check for citations with zero confidence
            zero_confidence = sum(1 for r in citation_results if get_value(r, 'confidence', 0) == 0.0)
            if zero_confidence > 0:
                risk_factors.append(f"{zero_confidence} citations with zero confidence (unvalidated)")
        
        # Context-related risks
        if context_results:
            context_issues = sum(1 for r in context_results if not get_value(r, 'context_preserved', False))
            if context_issues > len(context_results) * 0.2:  # More than 20% with context issues
                risk_factors.append(f"{context_issues} citations with context preservation issues")
            
            low_context_confidence = sum(1 for r in context_results if get_value(r, 'confidence', 0) < 0.6)
            if low_context_confidence > len(context_results) * 0.3:
                risk_factors.append(f"{low_context_confidence} citations with low context confidence")
        
        # Article structure risks
        word_count = article_metadata.get('word_count', 0)
        citations_count = article_metadata.get('citations_count', 0)
        
        if word_count < 200:
            risk_factors.append("Article is very short, may lack sufficient detail")
        
        if citations_count == 0:
            risk_factors.append("No citations found in article")
        elif citations_count < 2:
            risk_factors.append("Very few citations, limited source support")
        
        return risk_factors
    
    def _generate_recommendations(
        self,
        citation_score: float,
        context_score: float,
        source_score: float,
        coherence_score: float
    ) -> List[str]:
        """Generate recommendations for improvement.
        
        Args:
            citation_score: Citation accuracy score
            context_score: Context preservation score
            source_score: Source reliability score
            coherence_score: Text coherence score
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if citation_score < 0.7:
            recommendations.append("Improve citation accuracy by verifying quotes and references")
        
        if context_score < 0.7:
            recommendations.append("Ensure citations preserve original context and meaning")
        
        if source_score < 0.6:
            recommendations.append("Use more reliable and authoritative sources")
        
        if coherence_score < 0.6:
            recommendations.append("Improve article structure and coherence")
        
        # General recommendations
        if all(score < 0.8 for score in [citation_score, context_score, source_score, coherence_score]):
            recommendations.append("Consider comprehensive review and revision of the article")
        
        if not recommendations:
            recommendations.append("Article meets quality standards - no specific improvements needed")
        
        return recommendations
    
    def calculate_confidence_interval(
        self,
        confidence_score: float,
        sample_size: int,
        confidence_level: float = 0.95
    ) -> Tuple[float, float]:
        """Calculate confidence interval for the score.
        
        Args:
            confidence_score: Point estimate of confidence
            sample_size: Number of samples used in calculation
            confidence_level: Desired confidence level (default 95%)
            
        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        if sample_size <= 1:
            return (confidence_score, confidence_score)
        
        # Simple confidence interval calculation
        # Using normal approximation for binomial proportion
        z_score = 1.96 if confidence_level == 0.95 else 2.576  # 99% CI
        
        standard_error = np.sqrt((confidence_score * (1 - confidence_score)) / sample_size)
        margin_of_error = z_score * standard_error
        
        lower_bound = max(0.0, confidence_score - margin_of_error)
        upper_bound = min(1.0, confidence_score + margin_of_error)
        
        return (lower_bound, upper_bound)
