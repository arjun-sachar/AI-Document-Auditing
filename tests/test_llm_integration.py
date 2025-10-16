"""Tests for LLM integration modules."""

import pytest
from pathlib import Path
from src.llm.model_selector import ModelSelector, ModelConfig


class TestModelSelector:
    """Test model selection functionality."""
    
    def test_get_model_config(self):
        """Test getting model configuration."""
        config_path = Path("config/model_config.yaml")
        selector = ModelSelector(config_path)
        
        # Test default model
        config = selector.get_model_config()
        
        assert isinstance(config, ModelConfig)
        assert config.name is not None
        assert config.provider is not None
        assert config.max_tokens > 0
        assert 0.0 <= config.temperature <= 1.0
    
    def test_get_available_models(self):
        """Test getting available models."""
        config_path = Path("config/model_config.yaml")
        selector = ModelSelector(config_path)
        
        available_models = selector.get_available_models()
        
        assert isinstance(available_models, dict)
        assert len(available_models) > 0
        
        # Check that each provider has models
        for provider, models in available_models.items():
            assert isinstance(models, list)
            assert len(models) > 0
    
    def test_get_validation_models(self):
        """Test getting validation models."""
        config_path = Path("config/model_config.yaml")
        selector = ModelSelector(config_path)
        
        validation_models = selector.get_validation_models()
        
        assert isinstance(validation_models, dict)
        assert 'citation' in validation_models
        assert 'context' in validation_models
        assert 'scoring' in validation_models
        
        # Check that all validation models are configured
        for task, config in validation_models.items():
            assert isinstance(config, ModelConfig)
            assert config.name is not None
    
    def test_get_generation_models(self):
        """Test getting generation models."""
        config_path = Path("config/model_config.yaml")
        selector = ModelSelector(config_path)
        
        generation_models = selector.get_generation_models()
        
        assert isinstance(generation_models, dict)
        assert 'article' in generation_models
        assert 'query' in generation_models
        assert 'extraction' in generation_models
        
        # Check that all generation models are configured
        for task, config in generation_models.items():
            assert isinstance(config, ModelConfig)
            assert config.name is not None
    
    def test_recommend_model_for_task(self):
        """Test model recommendation for tasks."""
        config_path = Path("config/model_config.yaml")
        selector = ModelSelector(config_path)
        
        # Test different budget preferences
        config_low = selector.recommend_model_for_task("generation", "low")
        config_balanced = selector.recommend_model_for_task("generation", "balanced")
        config_high = selector.recommend_model_for_task("generation", "high")
        
        assert isinstance(config_low, ModelConfig)
        assert isinstance(config_balanced, ModelConfig)
        assert isinstance(config_high, ModelConfig)
        
        # Test specific task types
        citation_config = selector.recommend_model_for_task("citation")
        context_config = selector.recommend_model_for_task("context")
        
        assert isinstance(citation_config, ModelConfig)
        assert isinstance(context_config, ModelConfig)
    
    def test_get_cost_estimate(self):
        """Test cost estimation."""
        config_path = Path("config/model_config.yaml")
        selector = ModelSelector(config_path)
        
        config = selector.get_model_config()
        cost = selector.get_cost_estimate(config, 1000, 500)
        
        assert isinstance(cost, float)
        assert cost >= 0.0
    
    def test_compare_models(self):
        """Test model comparison."""
        config_path = Path("config/model_config.yaml")
        selector = ModelSelector(config_path)
        
        available_models = selector.get_available_models()
        
        # Get first few models from first provider
        first_provider = list(available_models.keys())[0]
        first_models = available_models[first_provider][:2]
        
        comparison = selector.compare_models(first_models, first_provider)
        
        assert isinstance(comparison, dict)
        assert len(comparison) == len(first_models)
        
        for model_name, model_info in comparison.items():
            assert isinstance(model_info, dict)
            assert 'provider' in model_info
            assert 'max_tokens' in model_info
            assert 'cost_per_token' in model_info


class TestModelConfig:
    """Test model configuration."""
    
    def test_model_config_creation(self):
        """Test ModelConfig creation."""
        config = ModelConfig(
            name="test-model",
            provider="test-provider",
            max_tokens=4000,
            temperature=0.1,
            cost_per_token=0.001
        )
        
        assert config.name == "test-model"
        assert config.provider == "test-provider"
        assert config.max_tokens == 4000
        assert config.temperature == 0.1
        assert config.cost_per_token == 0.001
        assert config.base_url is None
        assert config.api_key is None
    
    def test_model_config_with_optional_fields(self):
        """Test ModelConfig with optional fields."""
        config = ModelConfig(
            name="test-model",
            provider="test-provider",
            max_tokens=4000,
            temperature=0.1,
            cost_per_token=0.001,
            base_url="https://api.test.com",
            api_key="test-key"
        )
        
        assert config.base_url == "https://api.test.com"
        assert config.api_key == "test-key"
