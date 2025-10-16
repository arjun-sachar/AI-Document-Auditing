"""Prompt templates for article generation."""

from typing import Dict, Any


class PromptTemplates:
    """Manages prompt templates for different article generation tasks."""
    
    def get_article_generation_prompt(
        self,
        topic: str,
        context: str,
        length: str = "medium",
        style: str = "academic",
        include_citations: bool = True
    ) -> str:
        """Generate prompt for article creation.
        
        Args:
            topic: Article topic
            context: Source context
            length: Article length (short, medium, long)
            style: Writing style (academic, journalistic, technical)
            include_citations: Whether to include citations
            
        Returns:
            Formatted prompt string
        """
        length_guidelines = {
            "short": "approximately 500-800 words",
            "medium": "approximately 1000-1500 words", 
            "long": "approximately 2000-3000 words"
        }
        
        style_guidelines = {
            "academic": "Use formal academic language, include proper citations, and maintain an objective tone.",
            "journalistic": "Use clear, accessible language suitable for general audiences. Include engaging introductions and clear conclusions.",
            "technical": "Use precise technical language with detailed explanations. Include relevant technical details and specifications."
        }
        
        citation_instruction = ""
        if include_citations:
            citation_instruction = """
IMPORTANT CITATION REQUIREMENTS:
- Include proper citations for all claims and facts
- Use format: [Source X] where X is the source number from the context
- Ensure all citations are accurate and properly attributed
- Do not fabricate or misquote information from the sources
"""
        
        prompt = f"""You are an expert writer tasked with creating a high-quality article on the following topic:

TOPIC: {topic}

ARTICLE REQUIREMENTS:
- Length: {length_guidelines.get(length, "1000-1500 words")}
- Style: {style_guidelines.get(style, "academic")}
- Ensure accuracy and factual correctness
- Maintain logical flow and structure
{citation_instruction}

SOURCE CONTEXT:
{context}

INSTRUCTIONS:
1. Write a comprehensive, well-structured article on the given topic
2. Use information from the provided sources to support your arguments
3. Ensure all claims are backed by the source material
4. Maintain proper academic integrity and avoid plagiarism
5. Include an engaging introduction and a strong conclusion
6. Use clear headings and subheadings to organize content
7. Ensure the article is informative and valuable to readers

Please generate the article now:"""

        return prompt
    
    def get_citation_extraction_prompt(self, article_content: str) -> str:
        """Generate prompt for extracting citations from article.
        
        Args:
            article_content: The article content to analyze
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""Analyze the following article and extract all citations and quoted material.

ARTICLE CONTENT:
{article_content}

INSTRUCTIONS:
1. Identify all instances where the author references external sources
2. Extract any direct quotes or paraphrased content
3. Note the context around each citation
4. Identify potential issues with citation accuracy

Please provide your analysis in the following JSON format:
{{
    "citations": [
        {{
            "text": "quoted or referenced text",
            "context": "surrounding context",
            "type": "direct_quote|paraphrase|reference",
            "potential_issues": ["list of any potential problems"]
        }}
    ]
}}"""

        return prompt
    
    def get_context_validation_prompt(
        self,
        citation: str,
        source_content: str,
        article_context: str
    ) -> str:
        """Generate prompt for validating citation context.
        
        Args:
            citation: The citation to validate
            source_content: Original source content
            article_context: Context from the article
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are tasked with validating whether a citation is accurate and properly used in context.

CITATION TO VALIDATE:
{citation}

ARTICLE CONTEXT:
{article_context}

ORIGINAL SOURCE CONTENT:
{source_content}

VALIDATION TASKS:
1. Check if the citation is word-for-word accurate
2. Verify that the citation maintains the original meaning and context
3. Identify any potential misquotes or out-of-context usage
4. Assess whether the citation supports the claim being made

Please provide your analysis in the following JSON format:
{{
    "is_accurate": true/false,
    "accuracy_score": 0.0-1.0,
    "context_preserved": true/false,
    "context_score": 0.0-1.0,
    "issues_found": ["list of specific issues"],
    "overall_confidence": 0.0-1.0,
    "explanation": "detailed explanation of your assessment"
}}"""

        return prompt
    
    def get_confidence_scoring_prompt(
        self,
        validation_results: str,
        article_metadata: Dict[str, Any]
    ) -> str:
        """Generate prompt for calculating overall confidence scores.
        
        Args:
            validation_results: Results from citation validation
            article_metadata: Article metadata
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""Based on the following validation results, calculate an overall confidence score for the article's accuracy and reliability.

VALIDATION RESULTS:
{validation_results}

ARTICLE METADATA:
- Topic: {article_metadata.get('topic', 'Unknown')}
- Word Count: {article_metadata.get('word_count', 0)}
- Citations Count: {article_metadata.get('citations_count', 0)}
- Sources Used: {article_metadata.get('sources_used', 0)}

SCORING CRITERIA:
1. Citation accuracy (40% weight)
2. Context preservation (30% weight)  
3. Source reliability (20% weight)
4. Overall coherence (10% weight)

Please provide your assessment in the following JSON format:
{{
    "overall_confidence": 0.0-1.0,
    "citation_accuracy_score": 0.0-1.0,
    "context_preservation_score": 0.0-1.0,
    "source_reliability_score": 0.0-1.0,
    "coherence_score": 0.0-1.0,
    "recommendations": ["list of recommendations for improvement"],
    "risk_factors": ["list of potential risk factors or concerns"]
}}"""

        return prompt
