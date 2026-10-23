"""Factory for resolving and instantiating configured LLMProvider."""

from src.config import LLMConfig
from src.providers.base import LLMProvider
from src.providers.gemini import GeminiProvider
from src.providers.openai_compat import OpenAICompatProvider
from src.providers.anthropic import AnthropicProvider
from src.providers.mock_provider import MockLLMProvider


def get_llm_provider(config: LLMConfig) -> LLMProvider:
    """Return an initialized LLMProvider instance based on configuration."""
    provider_name = (config.provider or "gemini").lower()

    if provider_name == "gemini":
        return GeminiProvider(api_key=config.api_key, model=config.model)
    elif provider_name in ("openai", "deepseek", "groq"):
        return OpenAICompatProvider(
            api_key=config.api_key,
            model=config.model,
            base_url=config.base_url,
        )
    elif provider_name == "anthropic":
        return AnthropicProvider(api_key=config.api_key, model=config.model)
    elif provider_name in ("mock", "test", "offline"):
        return MockLLMProvider(model=config.model)
    else:
        raise ValueError(
            f"Unsupported LLM provider '{config.provider}'. "
            "Supported providers: gemini, openai, deepseek, groq, anthropic, mock."
        )
