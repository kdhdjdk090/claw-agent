"""LL Council - Multi-model orchestration inspired by Karpathy's ll-council.

This module implements a council of multiple AI models that vote on responses.
The council aggregates responses and returns the consensus answer.
"""

from __future__ import annotations

import json
import os
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Callable

import httpx

# Default free models available on OpenRouter - OPTIMIZED TOP TIER
# Priority order based on performance: Reasoning > Coding > Chat > Speed
OPENROUTER_MODELS = [
    # 🥇 TIER 1: MOST POWERFUL (Priority)
    "deepseek/deepseek-v3",                   # 🥇 Best overall - Massive MoE 600B+
    "qwen/qwen3-80b",                         # 🥈 Best balance - Power + Speed
    "meta-llama/llama-3.3-70b-instruct",      # 🥉 Most consistent & reliable
    
    # ⭐ TIER 2: SPECIALIZED
    "qwen/qwen-2.5-coder-32b-instruct",       # 💻 Coding specialist
    "deepseek/deepseek-r1",                   # 🧮 Reasoning / Math specialist
    
    # ⚡ TIER 3: FAST + EFFICIENT
    "google/gemma-3-12b-it",                  # ⚡ Fast & capable
    "openai/gpt-4o-mini",                     # 🎯 Reliable general purpose
    "anthropic/claude-3-haiku-20240307",      # 🎭 Natural conversation
]

# Alibaba Cloud models (1M free tokens each via DashScope)
from .alibaba_cloud import ALIBABA_CLOUD_MODELS
ALIBABA_MODELS = ALIBABA_CLOUD_MODELS  # 6 top Alibaba models

# ChatGPT models via g4f MCP bridge (no API key needed)
from .chatgpt_mcp import MCP_CHATGPT_MODELS
CHATGPT_MODELS = MCP_CHATGPT_MODELS  # 3 ChatGPT models

# CometAPI models (500+ models via single API key)
from .cometapi import COMETAPI_MODELS
COMET_MODELS = COMETAPI_MODELS  # 4 CometAPI models

# COMBINED COUNCIL - OpenRouter + Alibaba Cloud + ChatGPT + CometAPI
DEFAULT_COUNCIL_MODELS = OPENROUTER_MODELS + ALIBABA_MODELS + CHATGPT_MODELS + COMET_MODELS  # 21 models total!

# Model priority tiers for intelligent routing
MODEL_TIERS = {
    "tier_1_premium": [
        "deepseek/deepseek-v3",
        "qwen/qwen3-80b",
        "meta-llama/llama-3.3-70b-instruct",
    ],
    "tier_2_specialized": [
        "qwen/qwen-2.5-coder-32b-instruct",
        "deepseek/deepseek-r1",
    ],
    "tier_3_fast": [
        "google/gemma-3-12b-it",
        "openai/gpt-4o-mini",
        "anthropic/claude-3-haiku-20240307",
    ],
}

# Specialized model routing - which model is best for what task
TASK_MODEL_MAP = {
    "coding": "qwen/qwen-2.5-coder-32b-instruct",
    "reasoning": "deepseek/deepseek-r1",
    "math": "deepseek/deepseek-r1",
    "chat": "anthropic/claude-3-haiku-20240307",
    "creative": "meta-llama/llama-3.3-70b-instruct",
    "fast": "google/gemma-3-12b-it",
    "general": "deepseek/deepseek-v3",
}

# OpenRouter API configuration
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# Council configuration
COUNCIL_THRESHOLD = float(os.environ.get("COUNCIL_THRESHOLD", "0.6"))  # 60% consensus
COUNCIL_MODELS_ENV = os.environ.get("COUNCIL_MODELS", "")
if COUNCIL_MODELS_ENV:
    DEFAULT_COUNCIL_MODELS = [m.strip() for m in COUNCIL_MODELS_ENV.split(",")]


@dataclass
class CouncilResponse:
    """Response from a single council member."""
    model: str
    content: str
    token_count: int = 0
    latency_ms: float = 0
    error: str = ""


@dataclass
class CouncilResult:
    """Aggregated result from the council vote."""
    consensus_answer: str
    all_responses: list[CouncilResponse]
    votes: dict[str, int]
    consensus_percentage: float
    total_tokens: int
    total_cost: float


class LLCouncil:
    """Multi-model council that queries multiple models and aggregates responses."""

    def __init__(
        self,
        models: list[str] | None = None,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        on_response: Callable[[CouncilResponse], None] | None = None,
    ):
        self.models = models or DEFAULT_COUNCIL_MODELS
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.on_response = on_response
        self.client = httpx.Client(timeout=120)
        self.total_calls = 0
        self.total_tokens = 0

    def query_council(self, user_message: str) -> CouncilResult:
        """Query all council models and aggregate responses.
        
        Gracefully handles partial failures — if some providers fail
        (e.g. invalid API key), still returns results from working ones.
        """
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not set in environment")

        # Query all models
        responses = []
        for model in self.models:
            response = self._query_model(model, user_message)
            responses.append(response)
            if self.on_response:
                self.on_response(response)

        # Check for partial failures and warn
        valid = [r for r in responses if not r.error]
        errors = [r for r in responses if r.error]

        if errors and valid:
            # Group errors by provider for cleaner reporting
            alibaba_errors = [r for r in errors if r.model in ALIBABA_MODELS]
            chatgpt_errors = [r for r in errors if r.model in CHATGPT_MODELS]
            cometapi_errors = [r for r in errors if r.model in COMET_MODELS]
            openrouter_errors = [r for r in errors if r.model not in ALIBABA_MODELS and r.model not in CHATGPT_MODELS and r.model not in COMET_MODELS]

            warnings = []
            if alibaba_errors:
                warnings.append(f"Alibaba Cloud: {len(alibaba_errors)} model(s) failed ({alibaba_errors[0].error})")
            if chatgpt_errors:
                warnings.append(f"ChatGPT/g4f: {len(chatgpt_errors)} model(s) failed ({chatgpt_errors[0].error})")
            if cometapi_errors:
                warnings.append(f"CometAPI: {len(cometapi_errors)} model(s) failed ({cometapi_errors[0].error})")
            if openrouter_errors:
                warnings.append(f"OpenRouter: {len(openrouter_errors)} model(s) failed ({openrouter_errors[0].error})")

            # Still aggregate the working responses
            result = self._aggregate_responses(responses)
            # Prepend warning to consensus answer
            warning_str = " | ".join(warnings)
            result.consensus_answer = f"⚠️ Partial council ({len(valid)}/{len(responses)} models responded) [{warning_str}]\n\n{result.consensus_answer}"
            return result

        # Find consensus based on semantic similarity and content overlap
        result = self._aggregate_responses(responses)
        return result

    def _query_model(self, model: str, user_message: str) -> CouncilResponse:
        """Query a single model in the council (OpenRouter, Alibaba, ChatGPT, or CometAPI)."""
        start_time = time.time()

        try:
            # Check if this is an Alibaba Cloud model
            is_alibaba = model in ALIBABA_MODELS
            is_chatgpt = model in CHATGPT_MODELS
            is_cometapi = model in COMET_MODELS

            if is_cometapi:
                # Use CometAPI gateway
                from .cometapi import CometAPIClient, COMETAPI_KEY
                if not COMETAPI_KEY:
                    return CouncilResponse(
                        model=model,
                        content="",
                        latency_ms=0,
                        error="CometAPI key not configured",
                    )
                client = CometAPIClient()
                result = client.query(model, user_message, self.system_prompt)
                client.close()

                return CouncilResponse(
                    model=model,
                    content=result.content,
                    token_count=result.token_count,
                    latency_ms=result.latency_ms,
                    error=result.error,
                )
            elif is_chatgpt:
                # Use ChatGPT via g4f MCP bridge
                from .chatgpt_mcp import ChatGPTMCPClient
                client = ChatGPTMCPClient()
                result = client.query(model, user_message, self.system_prompt)
                client.close()

                return CouncilResponse(
                    model=model,
                    content=result.content,
                    token_count=result.token_count,
                    latency_ms=result.latency_ms,
                    error=result.error,
                )
            elif is_alibaba:
                # Use Alibaba Cloud API
                from .alibaba_cloud import AlibabaCloudClient, DASHSCOPE_API_KEY
                if not DASHSCOPE_API_KEY:
                    return CouncilResponse(
                        model=model,
                        content="",
                        latency_ms=0,
                        error="Alibaba API key not configured",
                    )
                
                client = AlibabaCloudClient()
                result = client.query(model, user_message, self.system_prompt)
                
                return CouncilResponse(
                    model=model,
                    content=result.content,
                    token_count=result.token_count,
                    latency_ms=result.latency_ms,
                    error=result.error,
                )
            else:
                # Use OpenRouter API
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                }

                response = self.client.post(
                    f"{OPENROUTER_API_BASE}/chat/completions",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://github.com/claw-agent",
                        "X-Title": "Claw AI Council",
                    },
                )

                latency_ms = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    token_count = data.get("usage", {}).get("total_tokens", 0)
                    self.total_tokens += token_count
                    self.total_calls += 1

                    return CouncilResponse(
                        model=model,
                        content=content,
                        token_count=token_count,
                        latency_ms=latency_ms,
                    )
                else:
                    return CouncilResponse(
                        model=model,
                        content="",
                        latency_ms=latency_ms,
                        error=f"HTTP {response.status_code}: {response.text[:200]}",
                    )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return CouncilResponse(
                model=model,
                content="",
                latency_ms=latency_ms,
                error=str(e)[:200],
            )

    def _aggregate_responses(self, responses: list[CouncilResponse]) -> CouncilResult:
        """Aggregate council responses and find consensus."""
        # Filter out errors
        valid_responses = [r for r in responses if not r.error]
        error_responses = [r for r in responses if r.error]

        if not valid_responses:
            # All models failed — show grouped errors by provider
            alibaba_errs = [r for r in error_responses if r.model in ALIBABA_MODELS]
            openrouter_errs = [r for r in error_responses if r.model not in ALIBABA_MODELS]
            
            parts = []
            if alibaba_errs:
                parts.append(f"Alibaba Cloud ({len(alibaba_errs)} models): {alibaba_errs[0].error}")
            if openrouter_errs:
                parts.append(f"OpenRouter ({len(openrouter_errs)} models): {openrouter_errs[0].error}")
            
            error_summary = " | ".join(parts) if parts else error_responses[0].error
            
            return CouncilResult(
                consensus_answer=f"❌ All {len(error_responses)} council models failed.\n{error_summary}\n\nTip: Run /doctor to validate your API keys.",
                all_responses=responses,
                votes={},
                consensus_percentage=0.0,
                total_tokens=0,
                total_cost=0.0,
            )

        # Simple consensus: find most common themes
        # For coding tasks, look for similar code patterns
        # For general tasks, find semantically similar answers
        
        # Group by similarity (simplified: exact match or contains)
        answer_groups: dict[str, list[str]] = {}
        for resp in valid_responses:
            content_normalized = self._normalize_content(resp.content)
            
            # Find similar group
            matched_group = None
            for group_key in answer_groups:
                if self._is_similar(content_normalized, group_key):
                    matched_group = group_key
                    break
            
            if matched_group:
                answer_groups[matched_group].append(resp.model)
            else:
                answer_groups[content_normalized[:100]] = [resp.model]

        # Find the largest group (consensus)
        best_group = max(answer_groups.items(), key=lambda x: len(x[1]))
        consensus_answer_text = best_group[0]
        voting_models = best_group[1]
        
        # Find the full response for the consensus
        for resp in valid_responses:
            if self._normalize_content(resp.content).startswith(consensus_answer_text):
                consensus_answer_text = resp.content
                break

        consensus_percentage = len(voting_models) / len(valid_responses) if valid_responses else 0
        total_tokens = sum(r.token_count for r in responses)
        
        # Free models on OpenRouter are actually free (no cost)
        total_cost = 0.0

        # Build votes dictionary
        votes = {model: len(models) for model, models in answer_groups.items()}

        # If consensus is strong enough, return the consensus answer
        if consensus_percentage >= COUNCIL_THRESHOLD:
            final_answer = f"[Council Consensus ({consensus_percentage:.0%}) - {len(voting_models)}/{len(valid_responses)} models agree]\n\n{consensus_answer_text}"
        else:
            # No strong consensus - return majority vote with alternatives
            alternatives = []
            for group_key, group_models in answer_groups.items():
                if group_key != consensus_answer_text:
                    alternatives.append(f"\n[{group_models[0]}] {group_key[:200]}...")
            
            final_answer = f"[Council Vote - No consensus ({consensus_percentage:.0%})]\n\n**Majority:** {consensus_answer_text[:500]}\n\n**Alternatives:**{''.join(alternatives[:3])}"

        return CouncilResult(
            consensus_answer=final_answer,
            all_responses=responses,
            votes=votes,
            consensus_percentage=consensus_percentage,
            total_tokens=total_tokens,
            total_cost=total_cost,
        )

    def _normalize_content(self, content: str) -> str:
        """Normalize content for comparison."""
        if not content:
            return ""
        # Remove whitespace, code blocks markers, etc.
        content = content.strip()
        content = content.replace("```", "")
        content = " ".join(content.split())
        return content.lower()

    def _is_similar(self, content1: str, content2: str) -> bool:
        """Check if two contents are semantically similar."""
        if not content1 or not content2:
            return False
        
        # Exact match or one contains the other
        if content1 == content2:
            return True
        if content1 in content2 or content2 in content1:
            return True
        
        # Check first 100 chars similarity
        prefix_len = min(100, len(content1), len(content2))
        prefix1 = content1[:prefix_len]
        prefix2 = content2[:prefix_len]
        
        # Simple character-level similarity
        if prefix1 and prefix2:
            matches = sum(c1 == c2 for c1, c2 in zip(prefix1, prefix2))
            similarity = matches / max(len(prefix1), len(prefix2))
            return similarity > 0.7
        
        return False

    def get_council_info(self) -> dict[str, Any]:
        """Get information about the council configuration."""
        openrouter_count = len(OPENROUTER_MODELS)
        alibaba_count = len(ALIBABA_MODELS)
        return {
            "providers": ["OpenRouter", "Alibaba Cloud (DashScope)"],
            "total_models": len(self.models),
            "openrouter_models": openrouter_count,
            "alibaba_models": alibaba_count,
            "total_calls": self.total_calls,
            "total_tokens": self.total_tokens,
            "threshold": COUNCIL_THRESHOLD,
        }
