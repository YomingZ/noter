"""AI API client module supporting multiple providers with rate limiting, caching, and multimodal."""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from pdf_summarizer.models import AIProvider, AIConfig, ContentPart
from pdf_summarizer.config import config
from pdf_summarizer.rate_limiter import get_rate_limiter
from pdf_summarizer.cache import CacheManager

logger = logging.getLogger(__name__)

# Global cache instance
_cache: Optional[CacheManager] = None


def get_cache() -> CacheManager:
    """Get the global cache instance."""
    global _cache
    if _cache is None:
        _cache = CacheManager()
    return _cache


class BaseAIClient(ABC):
    """Abstract base class for AI clients with rate limiting and caching."""

    def __init__(self, api_key: str, model: str, provider: str, **kwargs):
        self.api_key = api_key
        self.model = model
        self.provider = provider
        self.temperature = kwargs.get("temperature", 0.3)
        self.max_tokens = kwargs.get("max_tokens", 4096)
        self._rate_limiter = get_rate_limiter()
        self._cache = get_cache()

    @abstractmethod
    def _call_api(self, system_prompt: str, user_prompt: str) -> str:
        """Internal method to call the actual API."""
        pass

    @abstractmethod
    def _call_multimodal_api(
        self, system_prompt: str, content_parts: list[ContentPart]
    ) -> str:
        """Internal method to call the actual API with multimodal input."""
        pass

    def supports_vision(self) -> bool:
        """Check if the current model supports vision/multimodal input."""
        vision_models = {
            "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
            "claude": ["claude-sonnet-4", "claude-opus-4", "claude-3-5-sonnet", "claude-3-opus"],
        }
        provider_models = vision_models.get(self.provider, [])
        return any(vm in self.model for vm in provider_models)

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate text completion with rate limiting and caching."""
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        if self._cache is not None:
            cached = self._cache.get(full_prompt, self.provider, self.model)
            if cached is not None:
                return cached

        estimated_tokens = len(full_prompt) // 2 + self.max_tokens // 2
        wait_time = self._rate_limiter.acquire(self.provider, estimated_tokens)
        if wait_time > 0:
            logger.debug(f"Rate limit wait: {wait_time:.2f}s for {self.provider}")

        try:
            response = self._call_api(system_prompt, user_prompt)

            if self._cache is not None:
                self._cache.set(full_prompt, self.provider, self.model, response)

            return response

        finally:
            self._rate_limiter.release(self.provider, estimated_tokens)

    def generate_multimodal(
        self, system_prompt: str, content_parts: list[ContentPart]
    ) -> str:
        """Generate text with multimodal input (text + images), with rate limiting and caching.

        Args:
            system_prompt: System-level instruction
            content_parts: List of ContentPart items (text and/or images)

        Returns:
            Generated text response
        """
        text_parts = [p.text or "" for p in content_parts if p.type == "text"]
        full_prompt = f"{system_prompt}\n\n{' '.join(text_parts)}"

        if self._cache is not None:
            cached = self._cache.get(full_prompt, self.provider, self.model)
            if cached is not None:
                return cached

        estimated_tokens = len(full_prompt) // 2 + self.max_tokens // 2
        wait_time = self._rate_limiter.acquire(self.provider, estimated_tokens)
        if wait_time > 0:
            logger.debug(f"Rate limit wait: {wait_time:.2f}s for {self.provider}")

        try:
            response = self._call_multimodal_api(system_prompt, content_parts)

            if self._cache is not None:
                self._cache.set(full_prompt, self.provider, self.model, response)

            return response

        finally:
            self._rate_limiter.release(self.provider, estimated_tokens)

    def _validate_api_key(self):
        """Validate that API key is configured."""
        if not self.api_key:
            raise ValueError(
                f"API key not configured for {self.provider}. "
                f"Please set the appropriate environment variable."
            )


class OpenAIClient(BaseAIClient):
    """OpenAI API client with multimodal support."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        base_url: str = "https://api.openai.com/v1",
        **kwargs,
    ):
        super().__init__(api_key, model, "openai", **kwargs)
        self.base_url = base_url
        self._validate_api_key()

    def _call_api(self, system_prompt: str, user_prompt: str) -> str:
        """Generate text using OpenAI API."""
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)

        logger.info(f"Calling OpenAI API with model: {self.model}")

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        return response.choices[0].message.content

    def _call_multimodal_api(
        self, system_prompt: str, content_parts: list[ContentPart]
    ) -> str:
        """Generate text with multimodal input using OpenAI API."""
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)

        logger.info(f"Calling OpenAI multimodal API with model: {self.model}")

        openai_content = [part.to_openai_format() for part in content_parts]

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": openai_content},
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        return response.choices[0].message.content


class ClaudeClient(BaseAIClient):
    """Anthropic Claude API client with multimodal support."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6-20250514", **kwargs):
        super().__init__(api_key, model, "claude", **kwargs)
        self._validate_api_key()

    def _call_api(self, system_prompt: str, user_prompt: str) -> str:
        """Generate text using Anthropic Claude API."""
        from anthropic import Anthropic

        client = Anthropic(api_key=self.api_key)

        logger.info(f"Calling Claude API with model: {self.model}")

        response = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt},
            ],
        )

        return response.content[0].text

    def _call_multimodal_api(
        self, system_prompt: str, content_parts: list[ContentPart]
    ) -> str:
        """Generate text with multimodal input using Claude API."""
        from anthropic import Anthropic

        client = Anthropic(api_key=self.api_key)

        logger.info(f"Calling Claude multimodal API with model: {self.model}")

        claude_content = [part.to_claude_format() for part in content_parts]

        response = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt,
            messages=[
                {"role": "user", "content": claude_content},
            ],
        )

        return response.content[0].text


class KimiClient(BaseAIClient):
    """Kimi (Moonshot) API client."""

    def __init__(
        self,
        api_key: str,
        model: str = "moonshot-v1-8k",
        base_url: str = "https://api.moonshot.cn/v1",
        **kwargs,
    ):
        super().__init__(api_key, model, "kimi", **kwargs)
        self.base_url = base_url
        self._validate_api_key()

    def _call_api(self, system_prompt: str, user_prompt: str) -> str:
        """Generate text using Kimi API (OpenAI-compatible)."""
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)

        logger.info(f"Calling Kimi API with model: {self.model}")

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        return response.choices[0].message.content

    def _call_multimodal_api(
        self, system_prompt: str, content_parts: list[ContentPart]
    ) -> str:
        """Kimi falls back to text-only for multimodal requests."""
        text = "\n".join(
            p.text or "" for p in content_parts if p.type == "text"
        )
        if any(p.type == "image" for p in content_parts):
            logger.warning("Kimi does not support image input, using text only")
        return self._call_api(system_prompt, text)


# Provider configurations
PROVIDER_CONFIGS = {
    AIProvider.OPENAI: {
        'client_class': OpenAIClient,
        'default_model': 'gpt-4o',
        'base_url': 'https://api.openai.com/v1',
    },
    AIProvider.CLAUDE: {
        'client_class': ClaudeClient,
        'default_model': 'claude-sonnet-4-6-20250514',
    },
    AIProvider.KIMI: {
        'client_class': KimiClient,
        'default_model': 'moonshot-v1-8k',
        'base_url': 'https://api.moonshot.cn/v1',
    },
}


def create_client(provider: AIProvider, **kwargs) -> BaseAIClient:
    """
    Factory function to create AI client based on provider.

    Args:
        provider: AI provider enum value
        **kwargs: Additional arguments (api_key, model, temperature, etc.)

    Returns:
        Configured AI client instance
    """
    ai_config = config.get_ai_config(provider)
    ai_config.update(kwargs)

    if provider not in PROVIDER_CONFIGS:
        raise ValueError(f"Unsupported AI provider: {provider}")

    provider_config = PROVIDER_CONFIGS[provider]
    client_class = provider_config['client_class']

    # Build client arguments
    client_kwargs = {
        'api_key': ai_config['api_key'],
        'model': ai_config['model'],
        'temperature': ai_config['temperature'],
        'max_tokens': ai_config['max_tokens'],
    }

    # Add base_url if supported
    if 'base_url' in provider_config:
        client_kwargs['base_url'] = ai_config.get('base_url', provider_config['base_url'])

    return client_class(**client_kwargs)


def generate_summary(
    content: str,
    provider: AIProvider = AIProvider.OPENAI,
    system_prompt: Optional[str] = None,
    user_prompt: Optional[str] = None,
    use_cache: bool = True,
) -> str:
    """
    Generate summary using AI provider with caching and rate limiting.

    Args:
        content: The content to summarize
        provider: AI provider to use
        system_prompt: Optional system prompt override
        user_prompt: Optional user prompt override
        use_cache: Whether to use caching (default: True)

    Returns:
        Generated summary text
    """
    prompts = config.load_prompts()

    system = system_prompt or prompts.get(
        "system_prompt",
        "你是一位专业的教育内容分析师。"
    )
    user = user_prompt or prompts.get(
        "summary_prompt",
        "请总结以下内容：\n\n{content}"
    ).replace('{content}', content)

    client = create_client(provider)

    # Temporarily disable cache if requested
    if not use_cache:
        client._cache = None

    return client.generate(system, user)


def generate_multimodal_summary(
    content_parts: list[ContentPart],
    provider: AIProvider = AIProvider.OPENAI,
    system_prompt: Optional[str] = None,
    use_cache: bool = True,
) -> str:
    """Generate summary with multimodal input (text + images).

    Use when PDF contains images/diagrams that should be analyzed by AI.

    Args:
        content_parts: List of ContentPart (text and/or image_base64)
        provider: AI provider to use (must support vision)
        system_prompt: Optional system prompt override
        use_cache: Whether to use caching

    Returns:
        Generated summary text
    """
    prompts = config.load_prompts()

    system = system_prompt or prompts.get(
        "system_prompt",
        "你是一位专业的教育内容分析师。"
    )

    client = create_client(provider)

    if not client.supports_vision():
        has_images = any(p.type == "image" for p in content_parts)
        if has_images:
            logger.warning(
                f"{provider.value} model {client.model} does not support vision. "
                f"Falling back to text-only."
            )

    if not use_cache:
        client._cache = None

    return client.generate_multimodal(system, content_parts)


def get_provider_stats() -> dict:
    """Get statistics for all providers."""
    rate_limiter = get_rate_limiter()
    cache = get_cache()

    return {
        'rate_limits': rate_limiter.get_all_stats(),
        'cache': cache.get_stats(),
    }
