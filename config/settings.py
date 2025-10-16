"""Application settings and configuration management."""

import os
from pathlib import Path
from typing import Optional, Dict, Any
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application settings
    app_name: str = "AI Document Auditing System"
    version: str = "1.0.0"
    debug: bool = False
    
    # Data paths
    data_dir: Path = Path("data")
    knowledge_base_dir: Path = Path("data/knowledge_bases")
    articles_dir: Path = Path("data/generated_articles")
    results_dir: Path = Path("data/validation_results")
    
    # LLM Configuration
    llm_provider: str = "openrouter"  # openrouter, anthropic, openai, local
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    default_model: str = "anthropic/claude-3-haiku"
    max_tokens: int = 4000
    temperature: float = 0.1
    
    # Validation settings
    citation_confidence_threshold: float = 0.8
    context_confidence_threshold: float = 0.7
    exact_match_weight: float = 0.4
    semantic_similarity_weight: float = 0.3
    context_preservation_weight: float = 0.3
    
    # NLP settings
    spacy_model: str = "en_core_web_sm"
    sentence_transformer_model: str = "all-MiniLM-L6-v2"
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # API settings
    request_timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "allow"
    }


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
        # Ensure data directories exist
        _settings.data_dir.mkdir(exist_ok=True)
        _settings.knowledge_base_dir.mkdir(exist_ok=True)
        _settings.articles_dir.mkdir(exist_ok=True)
        _settings.results_dir.mkdir(exist_ok=True)
    return _settings


def update_settings(**kwargs: Any) -> None:
    """Update global settings with new values."""
    global _settings
    if _settings is None:
        _settings = Settings()
    
    for key, value in kwargs.items():
        if hasattr(_settings, key):
            setattr(_settings, key, value)
