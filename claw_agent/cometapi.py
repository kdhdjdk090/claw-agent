"""CometAPI Integration for Claw AI Council.

Integrates CometAPI's 500+ model gateway with the LLM council.
Uses OpenAI-compatible endpoint at https://api.cometapi.com/v1.
Single API key provides access to GPT, Claude, Gemini, and more.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass

import httpx

# CometAPI Key - must be set via environment variable
COMETAPI_KEY = os.environ.get("COMETAPI_KEY", "")
COMETAPI_BASE = "https://api.cometapi.com/v1"

# Top CometAPI models for the council (prefixed with 'cometapi/')
COMETAPI_MODELS = [
    # 🥇 TIER 1: FLAGSHIP MODELS
    "cometapi/gpt-4.1",                  # OpenAI flagship
    "cometapi/claude-sonnet-4-20250514",  # Anthropic Sonnet 4
    "cometapi/gemini-2.5-flash",          # Google fast + capable

    # ⭐ TIER 2: REASONING / DEEP THINKING
    "cometapi/o4-mini",                   # OpenAI reasoning
    "cometapi/claude-sonnet-4-20250514",  # (already listed, skip duplicate below)
]

# De-duplicate: keep unique entries only
COMETAPI_MODELS = list(dict.fromkeys([
    "cometapi/gpt-4.1",
    "cometapi/claude-sonnet-4-20250514",
    "cometapi/gemini-2.5-flash",
    "cometapi/o4-mini",
]))

# Map council name → CometAPI model ID
_MODEL_MAP = {
    "cometapi/gpt-4.1": "gpt-4.1",
    "cometapi/claude-sonnet-4-20250514": "claude-sonnet-4-20250514",
    "cometapi/gemini-2.5-flash": "gemini-2.5-flash",
    "cometapi/o4-mini": "o4-mini",
}


@dataclass
class CometAPIResponse:
    """Response from CometAPI."""
    model: str
    content: str
    token_count: int = 0
    latency_ms: float = 0
    error: str = ""


class CometAPIClient:
    """Client for CometAPI (OpenAI-compatible gateway to 500+ models)."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or COMETAPI_KEY
        if not self.api_key:
            raise ValueError("COMETAPI_KEY environment variable is required")
        self.client = httpx.Client(timeout=120)
        self.total_calls = 0
        self.total_tokens = 0

    def close(self):
        """Close the underlying HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def query(self, model: str, prompt: str, system_prompt: str = "") -> CometAPIResponse:
        """Query a single CometAPI model."""
        start = time.time()

        # Resolve council name to CometAPI model ID
        api_model = _MODEL_MAP.get(model, model.removeprefix("cometapi/"))

        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": api_model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2048,
            }

            response = self.client.post(
                f"{COMETAPI_BASE}/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )

            latency_ms = (time.time() - start) * 1000

            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                token_count = data.get("usage", {}).get("total_tokens", 0)
                self.total_tokens += token_count
                self.total_calls += 1

                return CometAPIResponse(
                    model=model,
                    content=content,
                    token_count=token_count,
                    latency_ms=latency_ms,
                )
            else:
                error_text = response.text[:200]
                return CometAPIResponse(
                    model=model,
                    content="",
                    latency_ms=latency_ms,
                    error=f"CometAPI HTTP {response.status_code}: {error_text}",
                )
        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            return CometAPIResponse(
                model=model,
                content="",
                latency_ms=latency_ms,
                error=f"CometAPI error: {e}",
            )
