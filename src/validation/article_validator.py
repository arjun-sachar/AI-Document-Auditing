"""Article-level validation utilities.

This module validates generated articles for:
- Prompt separation (no prompt instructions in article)
- Proper quotation formatting (balanced quotes, no nested quotes)
- Word count compliance with target ranges
- Context rating sanity checks (range, consistency, realistic values)

Used to ensure article quality before presentation to users.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ArticleValidationIssue:
    """Represents a validation issue detected in an article."""

    code: str
    message: str
    severity: str = "error"
    evidence: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
        }
        if self.evidence:
            data["evidence"] = self.evidence
        return data


class ArticleValidator:
    """Validates structural quality of generated articles."""

    DEFAULT_LENGTH_RANGES: Dict[str, Tuple[int, int]] = {
        "short": (500, 800),
        "medium": (1000, 1500),
        "long": (2000, 3000),
    }

    PROMPT_PHRASES = [
        "critical citation requirements",
        "mandatory citation examples",
        "critical format requirements",
        "citation placement rules",
        "critical quote context requirements",
        "please generate the article now",
        "you previously generated an article",
        "count your words as you write",
        "do not start the article",
    ]

    def __init__(self, length_ranges: Optional[Dict[str, Tuple[int, int]]] = None) -> None:
        self.length_ranges = length_ranges or self.DEFAULT_LENGTH_RANGES

    def validate(
        self,
        article_content: str,
        metadata: Optional[Dict[str, Any]] = None,
        prompt_text: Optional[str] = None,
        *,
        length: str = "medium",
        style: Optional[str] = None,
        include_citations: bool = True,
    ) -> Dict[str, Any]:
        """Validate structural integrity of an article."""

        metadata = metadata or {}
        article_content = article_content or ""

        word_count = self._count_words(article_content)
        issues: List[ArticleValidationIssue] = []

        # Word count compliance
        length_issue = self._check_word_count(word_count, length)
        if length_issue:
            issues.append(length_issue)

        # Prompt leakage detection
        prompt_issues = self._detect_prompt_leakage(article_content, prompt_text)
        issues.extend(prompt_issues)

        # Quote formatting validation
        issues.extend(self._check_quote_formatting(article_content, include_citations))

        # Context rating sanity checks
        context_issues, context_metrics = self._evaluate_context_rating(
            article_content,
            metadata,
            word_count,
            include_citations,
        )
        issues.extend(context_issues)

        passed = not any(issue.severity == "error" for issue in issues)

        result = {
            "passed": passed,
            "issues": [issue.to_dict() for issue in issues],
            "metrics": {
                "word_count": word_count,
                "target_range": self.length_ranges.get(length, self.DEFAULT_LENGTH_RANGES["medium"]),
                "source_reference_count": context_metrics.get("source_reference_count", 0),
                "citations_with_quotes": context_metrics.get("citations_with_quotes", 0),
                "citation_density": context_metrics.get("citation_density"),
                "overall_context_rating": context_metrics.get("overall_context_rating"),
                "expected_context_rating": context_metrics.get("expected_context_rating"),
                "style": style,
                "include_citations": include_citations,
            },
            "evaluated_at": datetime.utcnow().isoformat() + "Z",
            "length": length,
            "style": style,
        }

        return result

    @staticmethod
    def _count_words(text: str) -> int:
        return len(re.findall(r"\b\w+\b", text))

    def _check_word_count(self, word_count: int, length: str) -> Optional[ArticleValidationIssue]:
        target_min, target_max = self.length_ranges.get(length, self.DEFAULT_LENGTH_RANGES["medium"])
        if word_count < target_min or word_count > target_max:
            return ArticleValidationIssue(
                code="word_count_non_compliant",
                message=(
                    f"Article word count {word_count} is outside the target range "
                    f"{target_min}-{target_max}."
                ),
                severity="error",
            )
        return None

    def _detect_prompt_leakage(
        self,
        article_content: str,
        prompt_text: Optional[str],
    ) -> List[ArticleValidationIssue]:
        issues: List[ArticleValidationIssue] = []

        if not article_content:
            return issues

        article_normalized = re.sub(r"\s+", " ", article_content.lower())

        detected_phrases: List[str] = []
        for phrase in self.PROMPT_PHRASES:
            if phrase in article_normalized:
                detected_phrases.append(phrase)

        if prompt_text:
            prompt_normalized = re.sub(r"\s+", " ", prompt_text.lower())
            for fragment in self._extract_prompt_fragments(prompt_normalized):
                if fragment in article_normalized:
                    detected_phrases.append(fragment)

        unique_phrases = sorted(set(detected_phrases))
        if unique_phrases:
            evidence = unique_phrases[:3]
            issues.append(
                ArticleValidationIssue(
                    code="prompt_leakage",
                    message=(
                        "Article appears to include instructions or fragments from the generation prompt."
                    ),
                    severity="error",
                    evidence=", ".join(evidence),
                )
            )

        return issues

    def _extract_prompt_fragments(self, prompt_text: str) -> List[str]:
        fragments: List[str] = []
        if not prompt_text:
            return fragments

        for match in re.finditer(r"[a-z0-9][a-z0-9\s]{24,120}", prompt_text):
            fragment = match.group(0).strip()
            word_count = len(fragment.split())
            if word_count < 5:
                continue
            if sum(ch.isalpha() for ch in fragment) < 15:
                continue
            fragments.append(fragment)

        # Deduplicate while preserving order and cap the total fragments analysed
        seen = set()
        unique_fragments: List[str] = []
        for fragment in fragments:
            if fragment not in seen:
                seen.add(fragment)
                unique_fragments.append(fragment)
            if len(unique_fragments) >= 10:
                break

        return unique_fragments

    def _check_quote_formatting(
        self,
        article_content: str,
        include_citations: bool,
    ) -> List[ArticleValidationIssue]:
        issues: List[ArticleValidationIssue] = []

        double_quote_count = article_content.count('"')
        if double_quote_count % 2 != 0:
            issues.append(
                ArticleValidationIssue(
                    code="unbalanced_quotes",
                    message="Detected unbalanced double quotes in the article.",
                    severity="error",
                )
            )

        smart_open = article_content.count("“")
        smart_close = article_content.count("”")
        if smart_open != smart_close:
            issues.append(
                ArticleValidationIssue(
                    code="unbalanced_smart_quotes",
                    message="Detected mismatched smart quotes (opening vs closing).",
                    severity="warning",
                )
            )

        if re.search(r'""', article_content):
            issues.append(
                ArticleValidationIssue(
                    code="empty_or_nested_quotes",
                    message="Detected empty or nested double quotes.",
                    severity="warning",
                )
            )

        if re.search(r'"[^"\n]*\[Source\s+\d+\]', article_content):
            issues.append(
                ArticleValidationIssue(
                    code="quote_contains_source_marker",
                    message="Source markers must be placed outside quotation marks.",
                    severity="error",
                )
            )

        if include_citations:
            source_only_refs: List[str] = []
            for match in re.finditer(r"\[Source\s+\d+\]", article_content):
                window_start = max(0, match.start() - 120)
                preceding_text = article_content[window_start:match.start()]
                if '"' not in preceding_text:
                    source_only_refs.append(match.group(0))

            if source_only_refs:
                issues.append(
                    ArticleValidationIssue(
                        code="source_reference_without_quote",
                        message="Found source references without surrounding quoted text.",
                        severity="error",
                        evidence=", ".join(sorted(set(source_only_refs))[:3]),
                    )
                )

        return issues

    def _evaluate_context_rating(
        self,
        article_content: str,
        metadata: Dict[str, Any],
        word_count: int,
        include_citations: bool,
    ) -> Tuple[List[ArticleValidationIssue], Dict[str, Any]]:
        issues: List[ArticleValidationIssue] = []
        metrics: Dict[str, Any] = {}

        overall_rating = metadata.get("overall_context_rating")
        details = metadata.get("context_rating_details") or {}

        source_refs = re.findall(r"\[Source\s+\d+\]", article_content, flags=re.IGNORECASE)
        citations_with_quotes = 0
        for match in re.finditer(r"\[Source\s+\d+\]", article_content, flags=re.IGNORECASE):
            window_start = max(0, match.start() - 120)
            preceding_text = article_content[window_start:match.start()]
            if '"' in preceding_text:
                citations_with_quotes += 1

        citation_density = 0.0
        if word_count > 0:
            citation_density = citations_with_quotes / max(1, word_count / 200)

        metrics["source_reference_count"] = len(source_refs)
        metrics["citations_with_quotes"] = citations_with_quotes
        metrics["citation_density"] = round(citation_density, 3)
        metrics["overall_context_rating"] = overall_rating

        expected_rating = None
        if details:
            try:
                expected_rating = (
                    details.get("citation_quality", 0.0) * 0.5
                    + details.get("source_reference_validity", 0.0) * 0.3
                    + details.get("content_source_alignment", 0.0) * 0.2
                )
            except Exception:
                expected_rating = None
        if expected_rating is None and details:
            # Fallback for details that may already contain overall rating
            expected_rating = details.get("overall_rating")

        metrics["expected_context_rating"] = expected_rating

        if overall_rating is not None:
            if not 0.0 <= overall_rating <= 1.0:
                issues.append(
                    ArticleValidationIssue(
                        code="context_rating_out_of_range",
                        message="Overall context rating must be between 0 and 1.",
                        severity="error",
                    )
                )

            if expected_rating is not None and abs(overall_rating - expected_rating) > 0.15:
                issues.append(
                    ArticleValidationIssue(
                        code="context_rating_mismatch",
                        message=(
                            "Overall context rating deviates from the component scores "
                            f"(overall {overall_rating:.2f} vs expected {expected_rating:.2f})."
                        ),
                        severity="warning",
                    )
                )

            if len(source_refs) == 0 and overall_rating > 0.2:
                issues.append(
                    ArticleValidationIssue(
                        code="context_rating_without_sources",
                        message="Non-zero context rating reported despite missing source references.",
                        severity="error",
                    )
                )

            if citation_density < 0.35 and word_count > 400 and overall_rating > 0.7:
                issues.append(
                    ArticleValidationIssue(
                        code="context_rating_unrealistic",
                        message="Context rating appears too high for the detected citation coverage.",
                        severity="warning",
                    )
                )

        elif include_citations and word_count > 0:
            issues.append(
                ArticleValidationIssue(
                    code="context_rating_missing",
                    message="Context rating is missing from metadata.",
                    severity="warning",
                )
            )

        return issues, metrics

