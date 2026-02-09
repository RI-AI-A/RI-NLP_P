"""LLM Service - Unified interface for LLM backends"""
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import structlog
import ollama
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from .config import nlp_config

logger = structlog.get_logger()


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class LLMResponse:
    """LLM response container"""
    content: str
    provider: str
    model: str
    tokens_used: int = 0
    latency_ms: float = 0.0
    cached: bool = False


class LLMCache:
    """Simple in-memory cache for LLM responses"""
    
    def __init__(self, enabled: bool = True, max_size: int = 1000):
        self.enabled = enabled
        self.max_size = max_size
        self.cache: Dict[str, str] = {}
        self.access_times: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[str]:
        """Get cached response"""
        if not self.enabled:
            return None
        
        if key in self.cache:
            self.access_times[key] = time.time()
            logger.debug("Cache hit", key=key[:50])
            return self.cache[key]
        
        return None
    
    def set(self, key: str, value: str):
        """Cache a response"""
        if not self.enabled:
            return
        
        # Evict oldest if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.access_times.items(), key=lambda x: x[1])[0]
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
        
        self.cache[key] = value
        self.access_times[key] = time.time()
        logger.debug("Cached response", key=key[:50])
    
    def clear(self):
        """Clear the cache"""
        self.cache.clear()
        self.access_times.clear()


class LLMService:
    """Unified LLM service supporting multiple backends"""
    
    def __init__(self):
        self.config = nlp_config
        self.provider = LLMProvider(self.config.llm_provider)
        self.cache = LLMCache(enabled=self.config.enable_llm_caching)
        
        # Initialize clients
        self.ollama_client = None
        self.openai_client = None
        self.anthropic_client = None
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize LLM clients based on provider"""
        try:
            if self.provider == LLMProvider.OLLAMA:
                # Ollama client is initialized per-request
                logger.info("Using Ollama provider", 
                           model=self.config.llm_model,
                           base_url=self.config.llm_base_url)
            
            elif self.provider == LLMProvider.OPENAI:
                if not self.config.openai_api_key:
                    raise ValueError("OpenAI API key not configured")
                self.openai_client = AsyncOpenAI(api_key=self.config.openai_api_key)
                logger.info("Using OpenAI provider", model=self.config.llm_model)
            
            elif self.provider == LLMProvider.ANTHROPIC:
                if not self.config.anthropic_api_key:
                    raise ValueError("Anthropic API key not configured")
                self.anthropic_client = AsyncAnthropic(api_key=self.config.anthropic_api_key)
                logger.info("Using Anthropic provider", model=self.config.llm_model)
            
        except Exception as e:
            logger.error("Failed to initialize LLM client", error=str(e))
            raise
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False
    ) -> LLMResponse:
        """
        Generate text using the configured LLM
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (overrides config)
            max_tokens: Max tokens to generate (overrides config)
            json_mode: Force JSON output
            
        Returns:
            LLMResponse object
        """
        start_time = time.time()
        
        # Check cache
        cache_key = f"{system_prompt}|{prompt}|{temperature}|{max_tokens}"
        cached_response = self.cache.get(cache_key)
        if cached_response:
            return LLMResponse(
                content=cached_response,
                provider=self.provider.value,
                model=self.config.llm_model,
                cached=True,
                latency_ms=0.0
            )
        
        # Use config defaults if not specified
        temperature = temperature if temperature is not None else self.config.llm_temperature
        max_tokens = max_tokens if max_tokens is not None else self.config.llm_max_tokens
        
        try:
            # Route to appropriate backend
            if self.provider == LLMProvider.OLLAMA:
                response = await self._generate_ollama(
                    prompt, system_prompt, temperature, max_tokens, json_mode
                )
            elif self.provider == LLMProvider.OPENAI:
                response = await self._generate_openai(
                    prompt, system_prompt, temperature, max_tokens, json_mode
                )
            elif self.provider == LLMProvider.ANTHROPIC:
                response = await self._generate_anthropic(
                    prompt, system_prompt, temperature, max_tokens, json_mode
                )
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            response.latency_ms = latency_ms
            
            # Cache the response
            self.cache.set(cache_key, response.content)
            
            logger.info("LLM generation completed",
                       provider=self.provider.value,
                       latency_ms=round(latency_ms, 2),
                       tokens=response.tokens_used)
            
            return response
            
        except Exception as e:
            logger.error("LLM generation failed", error=str(e), provider=self.provider.value)
            raise
    
    async def _generate_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        json_mode: bool
    ) -> LLMResponse:
        """Generate using Ollama"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        options = {
            "temperature": temperature,
            "num_predict": max_tokens,
        }
        
        # Use JSON format if requested
        format_param = "json" if json_mode else None
        
        response = ollama.chat(
            model=self.config.llm_model,
            messages=messages,
            options=options,
            format=format_param
        )
        
        content = response['message']['content']
        
        # Estimate tokens (rough approximation)
        tokens_used = len(content.split()) + len(prompt.split())
        
        return LLMResponse(
            content=content,
            provider="ollama",
            model=self.config.llm_model,
            tokens_used=tokens_used
        )
    
    async def _generate_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        json_mode: bool
    ) -> LLMResponse:
        """Generate using OpenAI"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        kwargs = {
            "model": self.config.llm_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        
        response = await self.openai_client.chat.completions.create(**kwargs)
        
        content = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        
        return LLMResponse(
            content=content,
            provider="openai",
            model=self.config.llm_model,
            tokens_used=tokens_used
        )
    
    async def _generate_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        json_mode: bool
    ) -> LLMResponse:
        """Generate using Anthropic"""
        kwargs = {
            "model": self.config.llm_model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        response = await self.anthropic_client.messages.create(**kwargs)
        
        content = response.content[0].text
        tokens_used = response.usage.input_tokens + response.usage.output_tokens
        
        return LLMResponse(
            content=content,
            provider="anthropic",
            model=self.config.llm_model,
            tokens_used=tokens_used
        )
    
    async def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate structured JSON output
        
        Args:
            prompt: User prompt (should request JSON output)
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            
        Returns:
            Parsed JSON dictionary
        """
        response = await self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            json_mode=True
        )
        
        try:
            # Parse JSON response
            parsed = json.loads(response.content)
            return parsed
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON response", 
                        error=str(e), 
                        content=response.content[:200])
            
            # Try to extract JSON from markdown code blocks
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            try:
                return json.loads(content.strip())
            except:
                raise ValueError(f"Could not parse JSON from LLM response: {response.content[:200]}")


# Singleton instance
_llm_service = None


def get_llm_service() -> LLMService:
    """Get or create LLM service singleton"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
