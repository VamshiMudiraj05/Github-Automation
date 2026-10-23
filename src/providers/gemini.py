"""Google Gemini LLM Provider using official REST API endpoint."""

import json
import logging
import time
from typing import Optional
import requests

from src.providers.base import LLMProvider, LLMResponse

logger = logging.getLogger("agent.providers.gemini")


class GeminiProvider(LLMProvider):
    """Integrates with Google Gemini API models (e.g. gemini-2.5-flash, gemini-1.5-pro)."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, api_key: Optional[str], model: str = "gemini-3.5-flash", timeout: int = 60):
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
            raise ValueError("GEMINI_API_KEY environment variable is not configured.")

        url = f"{self.BASE_URL}/{self.model}:generateContent?key={self.api_key}"
        
        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        
        generation_config = {
            "temperature": 0.2 if temperature is None else temperature,
            "maxOutputTokens": 8192,
        }
        if json_mode:
            generation_config["responseMimeType"] = "application/json"

        payload = {
            "contents": contents,
            "generationConfig": generation_config,
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "role": "user",
                "parts": [{"text": system_instruction}]
            }

        headers = {"Content-Type": "application/json"}

        # Retry loop for transient network or 429 rate limit issues
        max_attempts = 4
        backoff = 2
        for attempt in range(1, max_attempts + 1):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        raise RuntimeError(f"Gemini returned no candidates: {data}")
                    content_parts = candidates[0].get("content", {}).get("parts", [])
                    text = "".join(p.get("text", "") for p in content_parts)
                    usage = data.get("usageMetadata", {})
                    return LLMResponse(
                        content=text,
                        prompt_tokens=usage.get("promptTokenCount", 0),
                        completion_tokens=usage.get("candidatesTokenCount", 0),
                        raw_response=data,
                    )
                elif response.status_code in (429, 503):
                    # If high demand, fallback to gemini-3.5-flash-lite or retry
                    if "lite" not in self.model and attempt >= 2:
                        logger.warning("Gemini model %s busy (%d). Falling back to gemini-3.5-flash-lite...", self.model, response.status_code)
                        url = f"{self.BASE_URL}/gemini-3.5-flash-lite:generateContent?key={self.api_key}"
                    else:
                        logger.warning("Gemini rate limited (%d). Retrying in %d seconds...", response.status_code, backoff)
                        time.sleep(backoff)
                        backoff *= 2
                else:
                    error_text = response.text
                    raise RuntimeError(f"Gemini API error ({response.status_code}): {error_text}")
            except requests.RequestException as e:
                if attempt == max_attempts:
                    raise RuntimeError(f"Gemini connection failed after {max_attempts} attempts: {e}")
                time.sleep(backoff)
                backoff *= 2

        raise RuntimeError("Gemini API call failed unexpectedly.")

    def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            resp = self.generate("Ping. Respond with 'PONG'.", temperature=0.0)
            return bool(resp.content)
        except Exception as e:
            logger.error("Gemini health check failed: %s", e)
            return False
