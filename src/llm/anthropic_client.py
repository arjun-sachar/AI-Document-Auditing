"""Anthropic API client with support for open-source alternatives via OpenRouter."""

import logging
import time
from typing import Dict, List, Optional, Any, Union
import requests
import json
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Response from LLM API."""
    content: str
    model: str
    usage: Dict[str, int]
    response_time: float
    success: bool
    error: Optional[str] = None


class AnthropicClient:
    """Client for interacting with Anthropic models via various providers."""
    
    def __init__(
        self,
        provider: str = "openrouter",
        api_key: Optional[str] = None,
        model_name: str = "anthropic/claude-3-haiku",
        base_url: Optional[str] = None
    ):
        """Initialize the LLM client.
        
        Args:
            provider: Provider to use ('anthropic', 'openrouter', 'openai', 'local')
            api_key: API key for the provider
            model_name: Model name to use
            base_url: Custom base URL (optional)
        """
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        
        # Check for missing or placeholder API key
        if not api_key or api_key.startswith('${') or api_key == 'your_openrouter_api_key_here':
            raise ValueError(
                f"Missing or invalid API key for {provider}. "
                f"Please set the appropriate environment variable or update your configuration.\n"
                f"For {provider}, you need to set: {self._get_env_var_name(provider)}"
            )
        
        # Configure endpoints and headers based on provider
        self._configure_provider()
        
        logger.info(f"Initialized {provider} client with model: {model_name}")
    
    def _get_env_var_name(self, provider: str) -> str:
        """Get the environment variable name for a provider."""
        env_var_map = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "openai": "OPENAI_API_KEY",
            "local": "No API key needed for local provider"
        }
        return env_var_map.get(provider, f"{provider.upper()}_API_KEY")
    
    def _configure_provider(self) -> None:
        """Configure provider-specific settings."""
        if self.provider == "anthropic":
            self.base_url = self.base_url or "https://api.anthropic.com/v1"
            self.headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
        elif self.provider == "openrouter":
            self.base_url = self.base_url or "https://openrouter.ai/api/v1"
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/your-repo",  # Replace with your repo
                "X-Title": "AI Document Auditing System"
            }
        elif self.provider == "openai":
            self.base_url = self.base_url or "https://api.openai.com/v1"
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        elif self.provider == "local":
            self.base_url = self.base_url or "http://localhost:11434"
            self.headers = {
                "Content-Type": "application/json"
            }
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def generate_text(
        self,
        prompt: str,
        max_tokens: int = 4000,
        temperature: float = 0.1,
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate text using the configured LLM.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            system_prompt: Optional system prompt
            
        Returns:
            Generated text
        """
        response = self.generate_text_with_metadata(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt
        )
        
        return response.content
    
    def generate_text_with_metadata(
        self,
        prompt: str,
        max_tokens: int = 4000,
        temperature: float = 0.1,
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """Generate text with full metadata.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            system_prompt: Optional system prompt
            
        Returns:
            LLMResponse object with metadata
        """
        start_time = time.time()
        
        try:
            logger.info(f"Making API call to {self.provider} with model {self.model_name}")
            logger.debug(f"Prompt length: {len(prompt)} characters")
            logger.debug(f"API key present: {bool(self.api_key)}")
            if self.api_key:
                logger.debug(f"API key starts with: {self.api_key[:10]}...")
            
            if self.provider == "anthropic":
                response = self._call_anthropic_api(prompt, max_tokens, temperature, system_prompt)
            elif self.provider == "openrouter":
                response = self._call_openrouter_api(prompt, max_tokens, temperature, system_prompt)
            elif self.provider == "openai":
                response = self._call_openai_api(prompt, max_tokens, temperature, system_prompt)
            elif self.provider == "local":
                response = self._call_local_api(prompt, max_tokens, temperature, system_prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
            logger.info(f"API call successful, response length: {len(response.get('content', ''))} characters")
            
            response_time = time.time() - start_time
            
            return LLMResponse(
                content=response.get('content', ''),
                model=self.model_name,
                usage=response.get('usage', {}),
                response_time=response_time,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            response_time = time.time() - start_time
            
            return LLMResponse(
                content="",
                model=self.model_name,
                usage={},
                response_time=response_time,
                success=False,
                error=str(e)
            )
    
    def _call_anthropic_api(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str]
    ) -> Dict[str, Any]:
        """Call Anthropic API directly."""
        data = {
            "model": self.model_name,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        if system_prompt:
            data["system"] = system_prompt
        
        response = requests.post(
            f"{self.base_url}/messages",
            headers=self.headers,
            json=data,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        return {
            'content': result['content'][0]['text'],
            'usage': {
                'input_tokens': result['usage']['input_tokens'],
                'output_tokens': result['usage']['output_tokens']
            }
        }
    
    def _call_openrouter_api(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str]
    ) -> Dict[str, Any]:
        """Call OpenRouter API (supports Anthropic models)."""
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        data = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=data,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        return {
            'content': result['choices'][0]['message']['content'],
            'usage': {
                'input_tokens': result['usage'].get('prompt_tokens', 0),
                'output_tokens': result['usage'].get('completion_tokens', 0)
            }
        }
    
    def _call_openai_api(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str]
    ) -> Dict[str, Any]:
        """Call OpenAI API."""
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        data = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=data,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        return {
            'content': result['choices'][0]['message']['content'],
            'usage': {
                'input_tokens': result['usage'].get('prompt_tokens', 0),
                'output_tokens': result['usage'].get('completion_tokens', 0)
            }
        }
    
    def _call_local_api(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str]
    ) -> Dict[str, Any]:
        """Call local API (e.g., Ollama)."""
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        data = {
            "model": self.model_name,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            headers=self.headers,
            json=data,
            timeout=60  # Longer timeout for local models
        )
        
        response.raise_for_status()
        result = response.json()
        
        return {
            'content': result['response'],
            'usage': {
                'input_tokens': result.get('prompt_eval_count', 0),
                'output_tokens': result.get('eval_count', 0)
            }
        }
    
    def test_connection(self) -> bool:
        """Test the connection to the LLM provider.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            test_response = self.generate_text(
                prompt="Hello, this is a connection test.",
                max_tokens=10,
                temperature=0.0
            )
            
            logger.info("LLM connection test successful")
            return len(test_response) > 0
            
        except Exception as e:
            logger.error(f"LLM connection test failed: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model.
        
        Returns:
            Dictionary with model information
        """
        return {
            'provider': self.provider,
            'model_name': self.model_name,
            'base_url': self.base_url,
            'supports_system_prompt': self.provider in ['anthropic', 'openrouter', 'openai'],
            'supports_streaming': False,  # Simplified for this implementation
            'max_tokens': 4000 if 'haiku' in self.model_name else 8000
        }
