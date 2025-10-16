"""Tests for validation modules."""

import pytest
from pathlib import Path
from src.validation.nlp_processor import NLPProcessor
from src.validation.confidence_scorer import ConfidenceScorer


class TestNLPProcessor:
    """Test NLP processing functionality."""
    
    def test_normalize_text(self):
        """Test text normalization."""
        processor = NLPProcessor()
        
        text = "This is a TEST with UPPERCASE and punctuation!"
        normalized = processor.normalize_text(text)
        
        assert normalized == "this is a test with uppercase and punctuation"
    
    def test_extract_citations(self):
        """Test citation extraction."""
        processor = NLPProcessor()
        
        text = "According to research [Source 1], the findings show that 'climate change is real' [2]."
        citations = processor.extract_citations(text)
        
        assert "[Source 1]" in citations
        assert "[2]" in citations
        assert '"climate change is real"' in citations
    
    def test_split_into_sentences(self):
        """Test sentence splitting."""
        processor = NLPProcessor()
        
        text = "This is sentence one. This is sentence two! This is sentence three?"
        sentences = processor.split_into_sentences(text)
        
        assert len(sentences) == 3
        assert "This is sentence one" in sentences
        assert "This is sentence two" in sentences
        assert "This is sentence three" in sentences
    
    def test_analyze_text(self):
        """Test comprehensive text analysis."""
        processor = NLPProcessor()
        
        text = "Climate change is a global challenge. It affects weather patterns worldwide."
        analysis = processor.analyze_text(text)
        
        assert analysis.word_count > 0
        assert analysis.sentence_count == 2
        assert len(analysis.sentences) == 2
        assert len(analysis.tokens) > 0


class TestConfidenceScorer:
    """Test confidence scoring functionality."""
    
    def test_calculate_citation_accuracy_score(self):
        """Test citation accuracy score calculation."""
        scorer = ConfidenceScorer()
        
        citation_results = [
            {"is_accurate": True, "confidence": 0.9},
            {"is_accurate": True, "confidence": 0.8},
            {"is_accurate": False, "confidence": 0.3},
            {"is_accurate": True, "confidence": 0.85}
        ]
        
        score = scorer._calculate_citation_accuracy_score(citation_results)
        
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be above 0.5 since most citations are accurate
    
    def test_calculate_context_preservation_score(self):
        """Test context preservation score calculation."""
        scorer = ConfidenceScorer()
        
        context_results = [
            {"context_preserved": True, "semantic_similarity_score": 0.9},
            {"context_preserved": True, "semantic_similarity_score": 0.8},
            {"context_preserved": False, "semantic_similarity_score": 0.4},
            {"context_preserved": True, "semantic_similarity_score": 0.85}
        ]
        
        score = scorer._calculate_context_preservation_score(context_results)
        
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be above 0.5 since most contexts are preserved
    
    def test_calculate_overall_confidence(self):
        """Test overall confidence score calculation."""
        scorer = ConfidenceScorer()
        
        citation_results = [
            {"is_accurate": True, "confidence": 0.9},
            {"is_accurate": True, "confidence": 0.8}
        ]
        
        context_results = [
            {"context_preserved": True, "semantic_similarity_score": 0.9},
            {"context_preserved": True, "semantic_similarity_score": 0.8}
        ]
        
        article_metadata = {
            "word_count": 1000,
            "citations_count": 2,
            "sources_used": 5
        }
        
        confidence_score = scorer.calculate_overall_confidence(
            citation_results, context_results, article_metadata
        )
        
        assert 0.0 <= confidence_score.overall_confidence <= 1.0
        assert confidence_score.citation_accuracy_score > 0.0
        assert confidence_score.context_preservation_score > 0.0
        assert len(confidence_score.recommendations) > 0
    
    def test_identify_risk_factors(self):
        """Test risk factor identification."""
        scorer = ConfidenceScorer()
        
        citation_results = [
            {"is_accurate": False, "confidence": 0.3},  # Low confidence
            {"is_accurate": False, "confidence": 0.2}   # Low confidence
        ]
        
        context_results = [
            {"context_preserved": False},
            {"context_preserved": False}
        ]
        
        article_metadata = {
            "word_count": 100,  # Very short
            "citations_count": 0  # No citations
        }
        
        risk_factors = scorer._identify_risk_factors(
            citation_results, context_results, article_metadata
        )
        
        assert len(risk_factors) > 0
        assert any("inaccurate" in risk.lower() for risk in risk_factors)
        assert any("short" in risk.lower() for risk in risk_factors)
    
    def test_generate_recommendations(self):
        """Test recommendation generation."""
        scorer = ConfidenceScorer()
        
        # Low scores should generate recommendations
        recommendations = scorer._generate_recommendations(0.3, 0.4, 0.5, 0.6)
        
        assert len(recommendations) > 0
        assert any("citation" in rec.lower() for rec in recommendations)
        assert any("context" in rec.lower() for rec in recommendations)
        
        # High scores should have fewer recommendations
        recommendations_high = scorer._generate_recommendations(0.9, 0.9, 0.9, 0.9)
        
        assert len(recommendations_high) <= len(recommendations)
