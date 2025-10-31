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
            "short": "EXACTLY 500-800 words (strict requirement)",
            "medium": "EXACTLY 1000-1500 words (strict requirement)", 
            "long": "EXACTLY 2000-3000 words (strict requirement)"
        }
        
        style_guidelines = {
            "academic": "ACADEMIC STYLE: Use formal academic language with complex sentence structures, passive voice, and scholarly terminology. Include extensive citations and maintain an objective, analytical tone. Use phrases like 'research indicates', 'studies demonstrate', 'analysis reveals'.",
            "journalistic": "JOURNALISTIC STYLE: Use clear, accessible language suitable for general audiences. Write in active voice with short, punchy sentences. Include engaging hooks, human interest elements, and clear conclusions. Use phrases like 'according to sources', 'officials report', 'experts say'.",
            "technical": "TECHNICAL STYLE: Use precise technical language with detailed explanations and specifications. Include technical jargon, acronyms, and detailed procedural information. Focus on how things work rather than why. Use phrases like 'the system operates', 'the process involves', 'the mechanism functions'."
        }
        
        citation_instruction = ""
        if include_citations:
            citation_instruction = """
CRITICAL CITATION REQUIREMENTS:
- You MUST use DIRECT QUOTES from the provided sources whenever possible
- For EVERY claim, fact, statistic, or direct quote, include proper citations
- Use format: "exact quote from source" [Source X] 
- Do not paraphrase the source material, always use the exact quote from the source.
- IF not using exact quotes summarize using context from articles and quotes being used to create source material
- For STATISTICS, always cite with direct quote: "79% of organizations" [Source X]
- For SPECIFIC FINDINGS, cite: Research indicates [Source X] that...
- NEVER make claims without proper citation
- Ensure all citations are accurate and properly attributed
- Do not fabricate or misquote information from the sources

MANDATORY CITATION EXAMPLES:
- Direct quote: "The pandemic accelerated digital transformation" [Source 1]
- Statistics: "79% of state CIOs reported increased AI adoption" [Source 3]
- Research findings: "A 2025 survey found that organizations are prioritizing AI" [Source 4]
- Paraphrase: According to recent studies [Source 2], organizations are prioritizing...

CRITICAL REQUIREMENTS:
- Each citation must reference a valid source number from the provided context
- Do not use [Source 0] or numbers higher than the available sources
- PREFER direct quotes over paraphrasing when the exact wording is important
- Use quotation marks around ALL direct quotes from sources
- EVERY quote must be followed by [Source X] - this is MANDATORY
- MINIMUM REQUIREMENT: You must cite at least 1 different source explicitly

MANDATORY CITATION FORMAT RULES:
- Use ONLY the format: [Source X] where X is a number
- NEVER use formats like: [?], [Source], [X] alone, or [Source X] [X]
- Each citation must be UNIQUE - do not repeat the same citation multiple times
- Do not mix citation formats - use ONLY [Source X] format
- NEVER add additional citations after [Source X] - one citation per claim only
- NEVER duplicate citations - each claim gets ONE citation only
- Each paragraph should contain at least one citation
"""
        
        prompt = f"""You are an expert writer tasked with creating a high-quality article on the following topic:

TOPIC: {topic}

ARTICLE REQUIREMENTS:
- Length: {length_guidelines.get(length, "1000-1500 words")}
- Style: {style_guidelines.get(style, "academic")}
- Ensure accuracy and factual correctness
- Maintain logical flow and structure
- CRITICAL: Count your words as you write and ensure you meet the exact word count requirement
- CRITICAL: For technical articles, provide detailed explanations, specifications, and comprehensive coverage
- CRITICAL: Do not stop writing until you reach the minimum word count requirement
- CRITICAL: If you find yourself short on words, expand on technical details, provide more examples, or add additional sections
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
8. DO NOT start with phrases like "Here is an article" or "This article will" - begin directly with the content
9. Write in a professional, engaging tone from the first sentence

Please generate the article now:"""

        return prompt
    
    def get_citation_extraction_prompt(self, article_content: str) -> str:
        """Generate prompt for extracting citations from article.
        
        Args:
            article_content: The article content to analyze
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are an expert citation analyst. Analyze the following article and extract ALL citations, quotes, and source references with maximum precision.

ARTICLE CONTENT:
{article_content}

CRITICAL EXTRACTION REQUIREMENTS:
1. **Direct Quotes**: Look for text enclosed in quotation marks ("...") followed by source references
2. **Source References**: Find patterns like [Source X], (Source X), [X], (X), or similar formats
3. **Attribution Phrases**: Identify phrases like "According to...", "Research shows...", "Studies indicate..."
4. **Statistical Claims**: Extract any numbers, percentages, or data points with their sources
5. **Paraphrased Content**: Find content that appears to summarize or restate source material
6. **Implicit References**: Look for content that suggests external sources without explicit citations

MALFORMED CITATION HANDLING:
- **SKIP**: [?], [Source] without numbers, [Source X] [X] duplicates
- **CLEAN**: [Source 1] [2] mixed citations -> [Source 1]
- **IGNORE**: Standalone numbers [X] that aren't source references
- **PRIORITIZE**: Only extract properly formatted [Source X] citations

SPECIFIC PATTERNS TO DETECT:
- Quoted text: "exact quote" [Source X]
- Parenthetical citations: (Source X), (X)
- Bracket citations: [Source X], [X]
- Attribution phrases: According to [Source X], Research by [Source X]
- Statistical data: "79% of organizations" [Source X]
- Study references: "A 2025 study found..." [Source X]

EXTRACTION INSTRUCTIONS:
1. **Scan systematically**: Go through the article paragraph by paragraph
2. **Identify all citations**: Don't miss any source references or quotes
3. **Extract context**: Include the surrounding sentence for each citation
4. **Classify types**: Determine if it's a direct quote, paraphrase, or reference
5. **Note position**: Record where each citation appears in the text
6. **Validate format**: Check if citations follow proper formatting

Please provide your analysis in the following JSON format:
{{
    "citations": [
        {{
            "text": "exact quoted text or referenced content",
            "context": "full sentence containing the citation",
            "type": "direct_quote|paraphrase|reference|statistical|attribution",
            "source_reference": "Source X or [X] format found",
            "position_start": character_position_start,
            "position_end": character_position_end,
            "confidence": 0.0-1.0,
            "validation_notes": "any issues or observations about this citation"
        }}
    ],
    "summary": {{
        "total_citations_found": number,
        "direct_quotes": number,
        "source_references": number,
        "potential_issues": ["list of any problems detected"],
        "citation_coverage": "assessment of how well the article cites sources"
    }}
}}

IMPORTANT: Be thorough and precise. Extract EVERY citation, quote, and source reference you can find. Even partial or poorly formatted citations should be included."""

        return prompt
    
    def get_context_validation_prompt(
        self,
        citation: str,
        source_content: str,
        article_context: str
    ) -> str:
        """Generate prompt for validating citation context with enhanced analysis.
        
        Args:
            citation: The citation to validate
            source_content: Original source content
            article_context: Context from the article
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are an expert citation analyst tasked with comprehensive validation of citation accuracy and context.

CITATION TO VALIDATE:
"{citation}"

ARTICLE CONTEXT (surrounding text):
{article_context}

ORIGINAL SOURCE CONTENT:
{source_content}

COMPREHENSIVE VALIDATION ANALYSIS:

1. **EXACT QUOTE VERIFICATION**:
   - Check if the citation appears word-for-word in the source
   - Identify any omissions, additions, or modifications
   - Note punctuation and capitalization differences
   - Assess quote accuracy on a scale of 0.0-1.0

2. **CONTEXTUAL ACCURACY**:
   - Verify the citation maintains the original meaning
   - Check if surrounding context in the article aligns with source context
   - Identify any misleading or out-of-context usage
   - Assess whether the citation supports the article's claim

3. **SEMANTIC ANALYSIS**:
   - Evaluate if the citation's meaning is preserved
   - Check for any subtle changes that alter interpretation
   - Assess the appropriateness of the citation for the article's argument
   - Identify potential bias or selective quoting

4. **ATTRIBUTION VERIFICATION**:
   - Confirm the citation is properly attributed
   - Check if source information is accurate
   - Verify the citation format follows academic standards

5. **OVERALL ASSESSMENT**:
   - Determine overall confidence in the citation's validity
   - Identify specific strengths and weaknesses
   - Provide actionable feedback for improvement

Please provide your analysis in the following JSON format:
{{
    "is_accurate": true/false,
    "accuracy_score": 0.0-1.0,
    "context_preserved": true/false,
    "context_score": 0.0-1.0,
    "semantic_integrity": 0.0-1.0,
    "attribution_correct": true/false,
    "issues_found": ["specific issues with detailed descriptions"],
    "strengths": ["positive aspects of the citation"],
    "overall_confidence": 0.0-1.0,
    "detailed_explanation": "comprehensive analysis explaining your assessment",
    "recommendations": ["suggestions for improvement if needed"]
}}"""

        return prompt
    
    def get_confidence_scoring_prompt(
        self,
        validation_results: str,
        article_metadata: Dict[str, Any]
    ) -> str:
        """Generate prompt for calculating comprehensive confidence scores with detailed analysis.
        
        Args:
            validation_results: Results from citation validation
            article_metadata: Article metadata
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are an expert academic reviewer tasked with comprehensive confidence assessment of an article's accuracy, reliability, and scholarly integrity.

VALIDATION RESULTS:
{validation_results}

ARTICLE METADATA:
- Topic: {article_metadata.get('topic', 'Unknown')}
- Word Count: {article_metadata.get('word_count', 0)}
- Citations Count: {article_metadata.get('citations_count', 0)}
- Sources Used: {article_metadata.get('sources_used', 0)}
- Style: {article_metadata.get('style', 'Unknown')}
- Length: {article_metadata.get('length', 'Unknown')}

COMPREHENSIVE CONFIDENCE ASSESSMENT:

1. **CITATION ACCURACY ANALYSIS** (40% weight):
   - Evaluate precision of direct quotes
   - Assess paraphrasing accuracy
   - Check source attribution correctness
   - Identify any misquotes or distortions
   - Score: 0.0-1.0 based on citation precision

2. **CONTEXT PRESERVATION EVALUATION** (30% weight):
   - Verify citations maintain original meaning
   - Check for out-of-context usage
   - Assess contextual appropriateness
   - Evaluate argumentative support
   - Score: 0.0-1.0 based on context integrity

3. **SOURCE RELIABILITY ASSESSMENT** (20% weight):
   - Evaluate source credibility and authority
   - Check source diversity and balance
   - Assess recency and relevance
   - Verify source accessibility
   - Score: 0.0-1.0 based on source quality

4. **SCHOLARLY COHERENCE ANALYSIS** (10% weight):
   - Evaluate logical flow and argumentation
   - Check consistency of claims and evidence
   - Assess academic writing standards
   - Verify topic coverage completeness
   - Score: 0.0-1.0 based on scholarly rigor

5. **RISK FACTOR IDENTIFICATION**:
   - Identify potential bias or selective citation
   - Flag misleading or incomplete information
   - Note any ethical concerns
   - Assess potential for misinterpretation

6. **IMPROVEMENT RECOMMENDATIONS**:
   - Suggest specific citation improvements
   - Recommend additional sources if needed
   - Identify areas requiring clarification
   - Propose structural enhancements

Please provide your comprehensive assessment in the following JSON format:
{{
    "overall_confidence": 0.0-1.0,
    "detailed_scores": {{
        "citation_accuracy": 0.0-1.0,
        "context_preservation": 0.0-1.0,
        "source_reliability": 0.0-1.0,
        "scholarly_coherence": 0.0-1.0
    }},
    "confidence_level": "High|Medium|Low",
    "strengths": ["specific positive aspects"],
    "weaknesses": ["specific areas of concern"],
    "risk_factors": ["potential issues with detailed descriptions"],
    "recommendations": ["actionable improvement suggestions"],
    "detailed_explanation": "comprehensive analysis of your assessment",
    "academic_standards_compliance": "assessment of adherence to scholarly standards"
}}"""

        return prompt
