"""Alibaba Cloud (DashScope) API Integration for Claw AI Council.

Integrates Alibaba Cloud's free quota models with OpenRouter council.
Uses DashScope API (OpenAI-compatible endpoint).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Callable

import httpx

# Alibaba Cloud API Key - lazy read so _load_project_env() has time to run
def _get_dashscope_key() -> str:
    return os.environ.get("DASHSCOPE_API_KEY", "")
DASHSCOPE_API_BASE = os.environ.get(
    "DASHSCOPE_API_BASE",
    "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
)

# Best Alibaba Cloud models from free quota (1M tokens each)
ALIBABA_CLOUD_MODELS = [
    # 🏆 BEST CODER
    "qwen3-coder-480b-a35b-instruct",   # 480B - Best coding model
    
    # 🥇 MOST POWERFUL FLAGSHIP
    "qwen3.5-397b-a17b",               # 397B - Newest flagship
    "qwen3-max",                        # Top flagship
    
    # 🧮 REASONING
    "qwen3-235b-a22b",                 # 235B - Deep reasoning
    
    # ⭐ CODING SPECIALIST
    "qwen3-coder-plus",                # Coding expert
    
    # ⚡ FAST BALANCED
    "qwen-plus",                       # Fast & capable
]

# Task-specific routing for Alibaba models
ALIBABA_TASK_ROUTING = {
    "coding": "qwen3-coder-480b-a35b-instruct",
    "complex_reasoning": "qwen3.5-397b-a17b",
    "general": "qwen3-max",
    "fast": "qwen-plus",
}


@dataclass
class AlibabaResponse:
    """Response from Alibaba Cloud model."""
    model: str
    content: str
    token_count: int = 0
    latency_ms: float = 0
    error: str = ""


class AlibabaCloudClient:
    """Client for Alibaba Cloud (DashScope) API."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or _get_dashscope_key()
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY environment variable is required")
        self.client = httpx.Client(timeout=60)
        self.total_calls = 0
        self.total_tokens = 0

    def close(self):
        """Close the underlying HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def query(self, model: str, prompt: str, system_prompt: str = "") -> AlibabaResponse:
        """Query a single Alibaba Cloud model."""
        import time
        start = time.time()

        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2048,
            }

            response = self.client.post(
                f"{DASHSCOPE_API_BASE}/chat/completions",
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

                return AlibabaResponse(
                    model=model,
                    content=content,
                    token_count=token_count,
                    latency_ms=latency_ms,
                )
            else:
                return AlibabaResponse(
                    model=model,
                    content="",
                    latency_ms=latency_ms,
                    error=f"HTTP {response.status_code}: {response.text[:200]}",
                )

        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            return AlibabaResponse(
                model=model,
                content="",
                latency_ms=latency_ms,
                error=str(e)[:200],
            )

    def query_best_for_task(self, prompt: str, system_prompt: str = "", task_type: str = "general") -> AlibabaResponse:
        """Query the best Alibaba model for the given task type."""
        model = ALIBABA_TASK_ROUTING.get(task_type, ALIBABA_TASK_ROUTING["general"])
        return self.query(model, prompt, system_prompt)

    def get_model_info(self) -> dict[str, Any]:
        """Get info about configured Alibaba models."""
        return {
            "provider": "Alibaba Cloud (DashScope)",
            "models": ALIBABA_CLOUD_MODELS,
            "model_count": len(ALIBABA_CLOUD_MODELS),
            "total_calls": self.total_calls,
            "total_tokens": self.total_tokens,
            "quota_remaining": "1,000,000 tokens per model (free tier)",
        }
