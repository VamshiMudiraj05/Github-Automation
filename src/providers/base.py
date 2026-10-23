"""Base interface and data models for LLM providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResponse:
    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    raw_response: Optional[dict] = None


class LLMProvider(ABC):
    """Abstract interface to ensure model portability."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_mode: bool = False,
        temperature: Optional[float] = None,
    ) -> LLMResponse:
        """Generate a response from the underlying model."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verify API key and connectivity."""
        pass
