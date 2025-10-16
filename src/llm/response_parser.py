"""Response parsing and processing utilities for LLM outputs."""

import json
import re
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class ParsedResponse:
    """Structured representation of parsed LLM response."""
    content: str
    structured_data: Optional[Dict[str, Any]] = None
    confidence_scores: Optional[Dict[str, float]] = None
    citations: List[str] = None
    issues: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.citations is None:
            self.citations = []
        if self.issues is None:
            self.issues = []
        if self.metadata is None:
            self.metadata = {}


class ResponseParser:
    """Parses and processes LLM responses for various tasks."""
    
    def __init__(self):
        """Initialize response parser."""
        self.json_patterns = [
            r'```json\s*(\{.*?\})\s*```',  # JSON in code blocks
            r'```\s*(\{.*?\})\s*```',     # JSON in generic code blocks
            r'(\{[^{}]*"[^"]*"[^{}]*\})', # Simple JSON objects
            r'(\{.*\})',                   # Any JSON-like structure
        ]
        
        self.citation_patterns = [
            r'\[Source \d+\]',
            r'\[\d+\]',
            r'\([^)]*\d+[^)]*\)',
            r'"[^"]*"',
        ]
    
    def parse_validation_response(self, response: str) -> ParsedResponse:
        """Parse validation response from LLM.
        
        Args:
            response: Raw LLM response
            
        Returns:
            ParsedResponse object
        """
        # Try to extract structured data
        structured_data = self._extract_json_from_response(response)
        
        # Extract confidence scores
        confidence_scores = self._extract_confidence_scores(response)
        
        # Extract citations
        citations = self._extract_citations(response)
        
        # Extract issues
        issues = self._extract_issues(response)
        
        return ParsedResponse(
            content=response,
            structured_data=structured_data,
            confidence_scores=confidence_scores,
            citations=citations,
            issues=issues,
            metadata={'parsing_method': 'validation_response'}
        )
    
    def parse_citation_response(self, response: str) -> ParsedResponse:
        """Parse citation validation response.
        
        Args:
            response: Raw LLM response
            
        Returns:
            ParsedResponse object
        """
        # Try to extract structured data
        structured_data = self._extract_json_from_response(response)
        
        # Extract confidence scores
        confidence_scores = self._extract_confidence_scores(response)
        
        # Extract issues
        issues = self._extract_issues(response)
        
        return ParsedResponse(
            content=response,
            structured_data=structured_data,
            confidence_scores=confidence_scores,
            issues=issues,
            metadata={'parsing_method': 'citation_response'}
        )
    
    def parse_context_response(self, response: str) -> ParsedResponse:
        """Parse context validation response.
        
        Args:
            response: Raw LLM response
            
        Returns:
            ParsedResponse object
        """
        # Try to extract structured data
        structured_data = self._extract_json_from_response(response)
        
        # Extract confidence scores
        confidence_scores = self._extract_confidence_scores(response)
        
        # Extract issues
        issues = self._extract_issues(response)
        
        return ParsedResponse(
            content=response,
            structured_data=structured_data,
            confidence_scores=confidence_scores,
            issues=issues,
            metadata={'parsing_method': 'context_response'}
        )
    
    def parse_confidence_response(self, response: str) -> ParsedResponse:
        """Parse confidence scoring response.
        
        Args:
            response: Raw LLM response
            
        Returns:
            ParsedResponse object
        """
        # Try to extract structured data
        structured_data = self._extract_json_from_response(response)
        
        # Extract confidence scores
        confidence_scores = self._extract_confidence_scores(response)
        
        # Extract recommendations
        recommendations = self._extract_recommendations(response)
        
        # Extract risk factors
        risk_factors = self._extract_risk_factors(response)
        
        return ParsedResponse(
            content=response,
            structured_data=structured_data,
            confidence_scores=confidence_scores,
            issues=risk_factors,
            metadata={
                'parsing_method': 'confidence_response',
                'recommendations': recommendations
            }
        )
    
    def _extract_json_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract JSON data from response text.
        
        Args:
            response: Response text
            
        Returns:
            Parsed JSON data or None
        """
        for pattern in self.json_patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            for match in matches:
                try:
                    # Clean up the match
                    json_str = match.strip()
                    if json_str.startswith('{') and json_str.endswith('}'):
                        return json.loads(json_str)
                except json.JSONDecodeError:
                    continue
        
        return None
    
    def _extract_confidence_scores(self, response: str) -> Dict[str, float]:
        """Extract confidence scores from response.
        
        Args:
            response: Response text
            
        Returns:
            Dictionary of confidence scores
        """
        confidence_scores = {}
        
        # Look for various confidence score patterns
        patterns = [
            r'confidence["\s]*:[\s]*([0-9.]+)',
            r'confidence["\s]*=[\s]*([0-9.]+)',
            r'score["\s]*:[\s]*([0-9.]+)',
            r'accuracy["\s]*:[\s]*([0-9.]+)',
            r'similarity["\s]*:[\s]*([0-9.]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            for match in matches:
                try:
                    score = float(match)
                    if 0.0 <= score <= 1.0:
                        confidence_scores[f'score_{len(confidence_scores)}'] = score
                except ValueError:
                    continue
        
        return confidence_scores
    
    def _extract_citations(self, response: str) -> List[str]:
        """Extract citations from response.
        
        Args:
            response: Response text
            
        Returns:
            List of extracted citations
        """
        citations = []
        
        for pattern in self.citation_patterns:
            matches = re.findall(pattern, response)
            citations.extend(matches)
        
        # Remove duplicates and clean up
        citations = list(set(citations))
        return citations
    
    def _extract_issues(self, response: str) -> List[str]:
        """Extract issues or problems from response.
        
        Args:
            response: Response text
            
        Returns:
            List of issues
        """
        issues = []
        
        # Look for issue patterns
        issue_patterns = [
            r'issues["\s]*:[\s]*\[(.*?)\]',
            r'problems["\s]*:[\s]*\[(.*?)\]',
            r'concerns["\s]*:[\s]*\[(.*?)\]',
            r'risks["\s]*:[\s]*\[(.*?)\]',
        ]
        
        for pattern in issue_patterns:
            matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
            for match in matches:
                # Parse list items
                items = re.findall(r'"([^"]*)"', match)
                issues.extend(items)
        
        # Also look for bullet points or numbered lists
        list_patterns = [
            r'[-*]\s*([^\\n]+)',
            r'\d+\.\s*([^\\n]+)',
        ]
        
        for pattern in list_patterns:
            matches = re.findall(pattern, response)
            for match in matches:
                if any(keyword in match.lower() for keyword in ['issue', 'problem', 'concern', 'risk', 'error']):
                    issues.append(match.strip())
        
        return list(set(issues))
    
    def _extract_recommendations(self, response: str) -> List[str]:
        """Extract recommendations from response.
        
        Args:
            response: Response text
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Look for recommendation patterns
        rec_patterns = [
            r'recommendations["\s]*:[\s]*\[(.*?)\]',
            r'suggestions["\s]*:[\s]*\[(.*?)\]',
            r'improvements["\s]*:[\s]*\[(.*?)\]',
        ]
        
        for pattern in rec_patterns:
            matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
            for match in matches:
                # Parse list items
                items = re.findall(r'"([^"]*)"', match)
                recommendations.extend(items)
        
        return list(set(recommendations))
    
    def _extract_risk_factors(self, response: str) -> List[str]:
        """Extract risk factors from response.
        
        Args:
            response: Response text
            
        Returns:
            List of risk factors
        """
        risk_factors = []
        
        # Look for risk factor patterns
        risk_patterns = [
            r'risk_factors["\s]*:[\s]*\[(.*?)\]',
            r'risks["\s]*:[\s]*\[(.*?)\]',
            r'concerns["\s]*:[\s]*\[(.*?)\]',
        ]
        
        for pattern in risk_patterns:
            matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
            for match in matches:
                # Parse list items
                items = re.findall(r'"([^"]*)"', match)
                risk_factors.extend(items)
        
        return list(set(risk_factors))
    
    def validate_parsed_response(self, parsed_response: ParsedResponse) -> bool:
        """Validate that parsed response contains expected data.
        
        Args:
            parsed_response: Parsed response to validate
            
        Returns:
            True if response is valid, False otherwise
        """
        if not parsed_response.content:
            return False
        
        # Check if we have structured data
        if parsed_response.structured_data is None:
            logger.warning("No structured data found in response")
        
        # Check if we have confidence scores
        if parsed_response.confidence_scores is None or not parsed_response.confidence_scores:
            logger.warning("No confidence scores found in response")
        
        return True
    
    def merge_parsed_responses(self, responses: List[ParsedResponse]) -> ParsedResponse:
        """Merge multiple parsed responses.
        
        Args:
            responses: List of parsed responses to merge
            
        Returns:
            Merged ParsedResponse
        """
        if not responses:
            return ParsedResponse(content="")
        
        # Combine content
        combined_content = "\n\n".join([r.content for r in responses])
        
        # Merge structured data
        combined_structured = {}
        for response in responses:
            if response.structured_data:
                combined_structured.update(response.structured_data)
        
        # Merge confidence scores
        combined_confidence = {}
        for response in responses:
            if response.confidence_scores:
                combined_confidence.update(response.confidence_scores)
        
        # Combine citations
        combined_citations = []
        for response in responses:
            combined_citations.extend(response.citations or [])
        combined_citations = list(set(combined_citations))
        
        # Combine issues
        combined_issues = []
        for response in responses:
            combined_issues.extend(response.issues or [])
        combined_issues = list(set(combined_issues))
        
        # Merge metadata
        combined_metadata = {}
        for response in responses:
            if response.metadata:
                combined_metadata.update(response.metadata)
        
        return ParsedResponse(
            content=combined_content,
            structured_data=combined_structured if combined_structured else None,
            confidence_scores=combined_confidence if combined_confidence else None,
            citations=combined_citations,
            issues=combined_issues,
            metadata=combined_metadata
        )
