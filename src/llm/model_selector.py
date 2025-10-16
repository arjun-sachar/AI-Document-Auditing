"""Model selection and configuration management."""

import yaml
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Try to import python-dotenv
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    name: str
    provider: str
    max_tokens: int
    temperature: float
    cost_per_token: float
    base_url: Optional[str] = None
    api_key: Optional[str] = None


class ModelSelector:
    """Manages model selection and configuration."""
    
    def __init__(self, config_path: Path):
        """Initialize model selector with configuration.
        
        Args:
            config_path: Path to model configuration YAML file
        """
        self.config_path = config_path
        
        # Try to load .env file if available
        if DOTENV_AVAILABLE:
            env_path = config_path.parent.parent / '.env'
            if env_path.exists():
                load_dotenv(env_path)
                logger.debug(f"Loaded environment variables from {env_path}")
            else:
                logger.debug(f".env file not found at {env_path}")
        else:
            logger.debug("python-dotenv not available, skipping .env loading")
        
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load model configuration from YAML file.
        
        Returns:
            Configuration dictionary
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_content = f.read()
            
            # Expand environment variables
            config_content = self._expand_env_vars(config_content)
            
            config = yaml.safe_load(config_content)
            logger.info(f"Loaded model configuration from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading model configuration: {e}")
            return self._get_default_config()
    
    def _expand_env_vars(self, text: str) -> str:
        """Expand environment variables in text.
        
        Args:
            text: Text with environment variable references like ${VAR_NAME}
            
        Returns:
            Text with environment variables expanded
        """
        def replace_var(match):
            var_name = match.group(1)
            env_value = os.environ.get(var_name)
            if env_value is None:
                logger.warning(f"Environment variable {var_name} not found, keeping placeholder")
                return match.group(0)
            logger.debug(f"Expanding {var_name} to: {env_value[:10]}...")
            return env_value
        
        return re.sub(r'\$\{([^}]+)\}', replace_var, text)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if file loading fails.
        
        Returns:
            Default configuration dictionary
        """
        return {
            'providers': {
                'openrouter': {
                    'api_key': '',
                    'base_url': 'https://openrouter.ai/api/v1',
                    'models': {
                        'claude-3-haiku': {
                            'name': 'anthropic/claude-3-haiku',
                            'max_tokens': 4000,
                            'temperature': 0.1,
                            'cost_per_token': 0.0005
                        }
                    }
                }
            },
            'defaults': {
                'provider': 'openrouter',
                'model': 'claude-3-haiku',
                'max_tokens': 4000,
                'temperature': 0.1
            }
        }
    
    def get_model_config(
        self,
        model_name: Optional[str] = None,
        provider: Optional[str] = None
    ) -> ModelConfig:
        """Get configuration for a specific model.
        
        Args:
            model_name: Name of the model (uses default if None)
            provider: Provider name (uses default if None)
            
        Returns:
            ModelConfig object
        """
        # Use defaults if not specified
        if not model_name:
            model_name = self.config['defaults']['model']
        if not provider:
            provider = self.config['defaults']['provider']
        
        # Get provider configuration
        provider_config = self.config['providers'].get(provider)
        if not provider_config:
            raise ValueError(f"Provider '{provider}' not found in configuration")
        
        # Get model configuration
        model_config = provider_config['models'].get(model_name)
        if not model_config:
            raise ValueError(f"Model '{model_name}' not found for provider '{provider}'")
        
        api_key = provider_config.get('api_key')
        logger.debug(f"API key for {provider}: {'Present' if api_key else 'Missing'}")
        if api_key:
            logger.debug(f"API key starts with: {api_key[:10] if len(api_key) >= 10 else api_key}...")
        
        return ModelConfig(
            name=model_config['name'],
            provider=provider,
            max_tokens=model_config.get('max_tokens', self.config['defaults']['max_tokens']),
            temperature=model_config.get('temperature', self.config['defaults']['temperature']),
            cost_per_token=model_config.get('cost_per_token', 0.0),
            base_url=provider_config.get('base_url'),
            api_key=api_key
        )
    
    def get_available_models(self, provider: Optional[str] = None) -> Dict[str, List[str]]:
        """Get list of available models.
        
        Args:
            provider: Specific provider to list models for (None for all)
            
        Returns:
            Dictionary mapping provider names to lists of model names
        """
        if provider:
            provider_config = self.config['providers'].get(provider)
            if provider_config:
                return {provider: list(provider_config['models'].keys())}
            else:
                return {}
        
        # Return all models for all providers
        available_models = {}
        for prov_name, prov_config in self.config['providers'].items():
            available_models[prov_name] = list(prov_config['models'].keys())
        
        return available_models
    
    def get_validation_models(self) -> Dict[str, ModelConfig]:
        """Get models recommended for validation tasks.
        
        Returns:
            Dictionary mapping task names to model configurations
        """
        validation_config = self.config.get('validation', {})
        
        validation_models = {}
        
        # Get citation validation model
        citation_model = validation_config.get('citation_model', 'claude-3-haiku')
        validation_models['citation'] = self.get_model_config(citation_model)
        
        # Get context validation model
        context_model = validation_config.get('context_model', 'claude-3-sonnet')
        validation_models['context'] = self.get_model_config(context_model)
        
        # Get confidence scoring model
        scoring_model = validation_config.get('scoring_model', 'claude-3-haiku')
        validation_models['scoring'] = self.get_model_config(scoring_model)
        
        return validation_models
    
    def get_generation_models(self) -> Dict[str, ModelConfig]:
        """Get models recommended for article generation.
        
        Returns:
            Dictionary mapping task names to model configurations
        """
        generation_config = self.config.get('generation', {})
        
        generation_models = {}
        
        # Get article generation model
        article_model = generation_config.get('article_model', 'claude-3-sonnet')
        generation_models['article'] = self.get_model_config(article_model)
        
        # Get knowledge base query model
        query_model = generation_config.get('query_model', 'claude-3-haiku')
        generation_models['query'] = self.get_model_config(query_model)
        
        # Get citation extraction model
        extraction_model = generation_config.get('extraction_model', 'claude-3-haiku')
        generation_models['extraction'] = self.get_model_config(extraction_model)
        
        return generation_models
    
    def recommend_model_for_task(
        self,
        task_type: str,
        budget_preference: str = "balanced"
    ) -> ModelConfig:
        """Recommend a model for a specific task.
        
        Args:
            task_type: Type of task ('generation', 'validation', 'citation', 'context')
            budget_preference: Budget preference ('low', 'balanced', 'high')
            
        Returns:
            Recommended ModelConfig
        """
        if task_type in ['citation', 'context']:
            models = self.get_validation_models()
            if task_type in models:
                return models[task_type]
        
        if task_type == 'generation':
            models = self.get_generation_models()
            return models.get('article', self.get_model_config())
        
        # Default recommendation based on budget preference
        if budget_preference == "low":
            return self.get_model_config('claude-3-haiku')
        elif budget_preference == "high":
            return self.get_model_config('claude-3-opus')
        else:  # balanced
            return self.get_model_config('claude-3-sonnet')
    
    def update_api_keys(self, api_keys: Dict[str, str]) -> None:
        """Update API keys in configuration.
        
        Args:
            api_keys: Dictionary mapping provider names to API keys
        """
        for provider, api_key in api_keys.items():
            if provider in self.config['providers']:
                self.config['providers'][provider]['api_key'] = api_key
                logger.info(f"Updated API key for provider: {provider}")
    
    def save_config(self, output_path: Optional[Path] = None) -> None:
        """Save current configuration to file.
        
        Args:
            output_path: Optional output path (uses original path if None)
        """
        save_path = output_path or self.config_path
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(save_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, indent=2)
        
        logger.info(f"Saved model configuration to {save_path}")
    
    def get_cost_estimate(
        self,
        model_config: ModelConfig,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Estimate cost for using a model.
        
        Args:
            model_config: Model configuration
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in dollars
        """
        total_tokens = input_tokens + output_tokens
        return total_tokens * model_config.cost_per_token
    
    def compare_models(
        self,
        model_names: List[str],
        provider: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Compare multiple models.
        
        Args:
            model_names: List of model names to compare
            provider: Provider to compare within (None for all)
            
        Returns:
            Dictionary with model comparisons
        """
        comparison = {}
        
        for model_name in model_names:
            try:
                config = self.get_model_config(model_name, provider)
                comparison[model_name] = {
                    'provider': config.provider,
                    'max_tokens': config.max_tokens,
                    'temperature': config.temperature,
                    'cost_per_token': config.cost_per_token,
                    'relative_cost': 'low' if config.cost_per_token < 0.001 else 'medium' if config.cost_per_token < 0.01 else 'high'
                }
            except ValueError as e:
                comparison[model_name] = {'error': str(e)}
        
        return comparison
