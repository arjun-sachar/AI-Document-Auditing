"""NLP processing utilities for text analysis."""

import re
import logging
import spacy
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class TextAnalysis:
    """Result of text analysis."""
    sentences: List[str]
    tokens: List[str]
    entities: List[Dict[str, Any]]
    sentiment: float
    readability_score: float
    word_count: int
    sentence_count: int


class NLPProcessor:
    """Handles natural language processing tasks."""
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        """Initialize NLP processor.
        
        Args:
            model_name: spaCy model name to use
        """
        self.model_name = model_name
        try:
            self.nlp = spacy.load(model_name)
            logger.info(f"Loaded spaCy model: {model_name}")
        except OSError:
            logger.error(f"spaCy model '{model_name}' not found. Please install it with: python -m spacy download {model_name}")
            raise
    
    def normalize_text(self, text: str) -> str:
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
    
    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences.
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        if not text:
            return []
        
        doc = self.nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents]
        
        # Filter out very short sentences (likely artifacts)
        sentences = [s for s in sentences if len(s) > 10]
        
        return sentences
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities from text.
        
        Args:
            text: Input text
            
        Returns:
            List of entity dictionaries
        """
        if not text:
            return []
        
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            entity_info = {
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char,
                'confidence': 1.0  # spaCy doesn't provide confidence scores
            }
            entities.append(entity_info)
        
        return entities
    
    def tokenize_text(self, text: str) -> List[str]:
        """Tokenize text into words.
        
        Args:
            text: Input text
            
        Returns:
            List of tokens
        """
        if not text:
            return []
        
        doc = self.nlp(text)
        tokens = [token.text for token in doc if not token.is_space]
        
        return tokens
    
    def analyze_text(self, text: str) -> TextAnalysis:
        """Perform comprehensive text analysis.
        
        Args:
            text: Input text
            
        Returns:
            TextAnalysis object with results
        """
        if not text:
            return TextAnalysis(
                sentences=[],
                tokens=[],
                entities=[],
                sentiment=0.0,
                readability_score=0.0,
                word_count=0,
                sentence_count=0
            )
        
        doc = self.nlp(text)
        
        # Extract sentences
        sentences = [sent.text.strip() for sent in doc.sents]
        sentences = [s for s in sentences if len(s) > 10]
        
        # Extract tokens
        tokens = [token.text for token in doc if not token.is_space]
        
        # Extract entities
        entities = []
        for ent in doc.ents:
            entity_info = {
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char
            }
            entities.append(entity_info)
        
        # Calculate sentiment (simplified)
        sentiment = self._calculate_sentiment(doc)
        
        # Calculate readability score (simplified)
        readability_score = self._calculate_readability(text)
        
        return TextAnalysis(
            sentences=sentences,
            tokens=tokens,
            entities=entities,
            sentiment=sentiment,
            readability_score=readability_score,
            word_count=len(tokens),
            sentence_count=len(sentences)
        )
    
    def _calculate_sentiment(self, doc) -> float:
        """Calculate sentiment score for document.
        
        Args:
            doc: spaCy document
            
        Returns:
            Sentiment score between -1 and 1
        """
        # Simple sentiment calculation based on positive/negative words
        # In a real implementation, you'd use a proper sentiment analysis model
        
        positive_words = {'good', 'great', 'excellent', 'positive', 'beneficial', 'improve', 'success'}
        negative_words = {'bad', 'terrible', 'negative', 'harmful', 'worse', 'fail', 'problem'}
        
        positive_count = sum(1 for token in doc if token.text.lower() in positive_words)
        negative_count = sum(1 for token in doc if token.text.lower() in negative_words)
        
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words == 0:
            return 0.0
        
        sentiment = (positive_count - negative_count) / total_sentiment_words
        return max(-1.0, min(1.0, sentiment))
    
    def _calculate_readability(self, text: str) -> float:
        """Calculate readability score.
        
        Args:
            text: Input text
            
        Returns:
            Readability score (higher = more readable)
        """
        if not text:
            return 0.0
        
        # Simple readability calculation (Flesch Reading Ease approximation)
        words = len(text.split())
        sentences = len([s for s in text.split('.') if s.strip()])
        
        if sentences == 0:
            return 0.0
        
        # Average words per sentence
        avg_words_per_sentence = words / sentences
        
        # Simple scoring (lower average words per sentence = higher readability)
        readability = max(0, 100 - (avg_words_per_sentence - 10) * 2)
        
        return min(100, readability)
    
    def extract_citations(self, text: str) -> List[str]:
        """Extract potential citations from text.
        
        Args:
            text: Input text
            
        Returns:
            List of extracted citations
        """
        citations = []
        
        # Common citation patterns
        patterns = [
            r'\[Source \d+\]',  # [Source 1]
            r'\[\d+\]',         # [1]
            r'\([^)]*\d+[^)]*\)',  # (Author, 2023)
            r'"[^"]*"',         # Quoted text
            r'\b(?:according to|as stated by|in the words of)\s+[^.]*',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            citations.extend(matches)
        
        # Remove duplicates
        citations = list(set(citations))
        
        return citations
    
    def find_similar_phrases(
        self,
        target_phrase: str,
        text: str,
        similarity_threshold: float = 0.8
    ) -> List[Dict[str, Any]]:
        """Find phrases similar to target in text.
        
        Args:
            target_phrase: Phrase to search for
            text: Text to search in
            similarity_threshold: Minimum similarity threshold
            
        Returns:
            List of similar phrases with positions
        """
        similar_phrases = []
        
        # Split text into overlapping windows
        words = text.split()
        target_words = target_phrase.split()
        window_size = len(target_words)
        
        for i in range(len(words) - window_size + 1):
            window = ' '.join(words[i:i + window_size])
            
            # Calculate simple similarity (word overlap)
            window_words = set(window.lower().split())
            target_words_set = set(target_words)
            
            overlap = len(window_words.intersection(target_words_set))
            similarity = overlap / len(target_words_set)
            
            if similarity >= similarity_threshold:
                phrase_info = {
                    'text': window,
                    'similarity': similarity,
                    'start_pos': i,
                    'end_pos': i + window_size
                }
                similar_phrases.append(phrase_info)
        
        return similar_phrases
