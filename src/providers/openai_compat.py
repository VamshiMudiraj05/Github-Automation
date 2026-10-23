"""OpenAI and OpenAI-compatible API provider (DeepSeek, Groq, local Ollama, etc.)."""

import logging
import time
from typing import Optional
import requests

from src.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger("agent.providers.openai")


class OpenAICompatProvider(LLMProvider):
    """Integrates with OpenAI-compatible Chat Completion API endpoints."""

    def __init__(
        self,
        api_key: Optional[str],
        model: str = "gpt-4o-mini",
        base_url: Optional[str] = None,
        timeout: int = 60,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = (base_url or "https://api.openai.com/v1").rstrip("/")
        self.timeout = timeout

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_mode: bool = False,
        temperature: Optional[float] = None,
    ) -> LLMResponse:
        if not self.api_key and "localhost" not in self.base_url and "127.0.0.1" not in self.base_url:
            raise ValueError("OPENAI_API_KEY environment variable is not configured.")

        url = f"{self.base_url}/chat/completions"

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2 if temperature is None else temperature,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key or 'no-key'}",
        }

        max_attempts = 4
        backoff = 2
        for attempt in range(1, max_attempts + 1):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    choices = data.get("choices", [])
                    if not choices:
                        raise RuntimeError(f"OpenAI returned no choices: {data}")
                    content = choices[0].get("message", {}).get("content", "")
                    usage = data.get("usage", {})
                    return LLMResponse(
                        content=content,
                        prompt_tokens=usage.get("prompt_tokens", 0),
                        completion_tokens=usage.get("completion_tokens", 0),
                        raw_response=data,
                    )
                elif response.status_code in (429, 503) and attempt < max_attempts:
                    logger.warning("OpenAI rate limited (%d). Retrying in %d seconds...", response.status_code, backoff)
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    raise RuntimeError(f"OpenAI API error ({response.status_code}): {response.text}")
            except requests.RequestException as e:
                if attempt == max_attempts:
                    raise RuntimeError(f"OpenAI connection failed after {max_attempts} attempts: {e}")
                time.sleep(backoff)
                backoff *= 2

        raise RuntimeError("OpenAI API call failed unexpectedly.")

    def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            resp = self.generate("Ping. Respond with 'PONG'.", temperature=0.0)
            return bool(resp.content)
        except Exception as e:
            logger.error("OpenAI health check failed: %s", e)
            return False
