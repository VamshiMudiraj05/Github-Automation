"""Anthropic Claude LLM Provider using Messages API."""

import logging
import time
from typing import Optional
import requests

from src.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger("agent.providers.anthropic")


class AnthropicProvider(LLMProvider):
    """Integrates with Anthropic Messages API (e.g. claude-3-5-sonnet-20241022)."""

    URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, api_key: Optional[str], model: str = "claude-3-5-sonnet-20241022", timeout: int = 60):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_mode: bool = False,
        temperature: Optional[float] = None,
    ) -> LLMResponse:
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not configured.")

        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "temperature": 0.2 if temperature is None else temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_instruction:
            payload["system"] = system_instruction

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        max_attempts = 4
        backoff = 2
        for attempt in range(1, max_attempts + 1):
            try:
                response = requests.post(self.URL, headers=headers, json=payload, timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    content_blocks = data.get("content", [])
                    text = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
                    usage = data.get("usage", {})
                    return LLMResponse(
                        content=text,
                        prompt_tokens=usage.get("input_tokens", 0),
                        completion_tokens=usage.get("output_tokens", 0),
                        raw_response=data,
                    )
                elif response.status_code in (429, 529) and attempt < max_attempts:
                    logger.warning("Anthropic rate limited (%d). Retrying in %d seconds...", response.status_code, backoff)
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    raise RuntimeError(f"Anthropic API error ({response.status_code}): {response.text}")
            except requests.RequestException as e:
                if attempt == max_attempts:
                    raise RuntimeError(f"Anthropic connection failed after {max_attempts} attempts: {e}")
                time.sleep(backoff)
                backoff *= 2

        raise RuntimeError("Anthropic API call failed unexpectedly.")

    def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            resp = self.generate("Ping. Respond with 'PONG'.", temperature=0.0)
            return bool(resp.content)
        except Exception as e:
            logger.error("Anthropic health check failed: %s", e)
            return False
