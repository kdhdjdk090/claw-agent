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

# Default models available on NVIDIA NIM - OPTIMIZED TOP TIER - QWEN3.5+ PRIORITY
# Priority order: Qwen3.5+ variants > Reasoning > Coding > Chat > Speed
NVIDIA_MODELS = [
    # 🥇 TIER 1: QWEN3.5+ MODELS (HIGHEST PRIORITY)
    "qwen/qwen3.5-397b-a17b",        # 🏆 Qwen3.5+ - Best overall

    # 🥈 TIER 2: MOST POWERFUL
    "qwen/qwen3-next-80b-a3b-instruct",  # 🥇 Best Qwen reasoning
    "meta/llama-3.3-70b-instruct",  # 🥈 Most consistent & reliable
    "nvidia/nemotron-4-340b-instruct",  # 🥉 Large NVIDIA reasoning model

    # ⭐ TIER 3: SPECIALIZED
    "qwen/qwen3-coder-480b-a35b-instruct",  # 💻 Coding specialist
    "google/gemma-4-27b-it",  # 🧮 Newest Gemma 4

    # ⚡ TIER 4: FAST + EFFICIENT
    "google/gemma-3-12b-it",  # ⚡ Fast & capable
    "google/gemma-3-27b-it",  # 🎯 Larger Gemma
    "google/gemma-4-31b-it",  # 🎭 Newest Gemma 4 31B
]

OPENROUTER_MODELS = NVIDIA_MODELS

# Alibaba Cloud models (1M free tokens each via DashScope)
from .alibaba_cloud import ALIBABA_CLOUD_MODELS
ALIBABA_MODELS = ALIBABA_CLOUD_MODELS  # 6 top Alibaba models

# ChatGPT models via g4f MCP bridge (requires Puter.js API key)
from .chatgpt_mcp import MCP_CHATGPT_MODELS
CHATGPT_MODELS = MCP_CHATGPT_MODELS  # 3 ChatGPT models

# CometAPI models (500+ models via single API key)
from .cometapi import COMETAPI_MODELS
COMET_MODELS = COMETAPI_MODELS  # 4 CometAPI models

_PROVIDER_LABELS = {
    "nvidia": "NVIDIA NIM",
    "openrouter": "NVIDIA NIM",
    "alibaba": "Alibaba Cloud",
    "chatgpt": "ChatGPT/g4f",
    "cometapi": "CometAPI",
}


def _provider_key_for_model(model: str) -> str:
    if model in ALIBABA_MODELS:
        return "alibaba"
    if model in CHATGPT_MODELS:
        return "chatgpt"
    if model in COMET_MODELS:
        return "cometapi"
    return "nvidia"


def _provider_label(provider_key: str) -> str:
    return _PROVIDER_LABELS[provider_key]


def _group_provider_errors(responses: list["CouncilResponse"]) -> dict[str, list["CouncilResponse"]]:
    grouped: dict[str, list["CouncilResponse"]] = {key: [] for key in _PROVIDER_LABELS}
    for response in responses:
        grouped[_provider_key_for_model(response.model)].append(response)
    return grouped


def _is_nvidia_session_blocker(error: str) -> bool:
    normalized = error.lower()
    return (
        "http 429" in normalized
        or "temporarily rate-limited upstream" in normalized
        or "http 401" in normalized
        or "nvidia api key not configured" in normalized
    )


_is_openrouter_session_blocker = _is_nvidia_session_blocker


def _build_default_council() -> list[str]:
    """Auto-detect configured providers and build council roster.

    Only includes providers whose API keys are actually set,
    so the council doesn't waste time on guaranteed-to-fail requests.
    """
    models: list[str] = []

    # Alibaba Cloud — include if DashScope key present
    from .alibaba_cloud import _get_dashscope_key
    if _get_dashscope_key():
        models.extend(ALIBABA_MODELS)

    # NVIDIA NIM — include only when a key is configured.
    if os.environ.get("NVIDIA_API_KEY", "") or os.environ.get("NIM_API_KEY", "") or os.environ.get("OPENROUTER_API_KEY", ""):
        models.extend(NVIDIA_MODELS)

    # CometAPI — include only if COMETAPI_KEY is set
    from .cometapi import COMETAPI_KEY as _ck
    if _ck:
        models.extend(COMET_MODELS)

    # ChatGPT/g4f — currently requires Puter.js API key.
    # Disabled by default; re-enable when key is configured.
    # models.extend(CHATGPT_MODELS)

    return models or list(NVIDIA_MODELS)


def run_role_council(task: str, workspace_root: str | None = None) -> str:
    """Run the Codex-style role-based council (planner→coder→reviewer→critic→synthesizer).

    This is a convenience wrapper around :class:`codex_runtime.CodexRuntime`
    that can be called from the CLI or other modules without wiring up the
    full Agent class.

    Returns the synthesised final answer as a plain string.
    """
    from .codex_runtime import CodexRuntime

    rt = CodexRuntime(workspace_root=workspace_root or os.getcwd())
    try:
        result = rt.run_task(task)
        return result.final_answer
    finally:
        rt.close()


# Lazy singleton — computed on first access (after env is loaded)
_DEFAULT_COUNCIL: list[str] | None = None


def _get_default_council() -> list[str]:
    """Return cached default council, building on first call."""
    global _DEFAULT_COUNCIL, DEFAULT_COUNCIL_MODELS
    if _DEFAULT_COUNCIL is None:
        _DEFAULT_COUNCIL = _build_default_council()
        DEFAULT_COUNCIL_MODELS = _DEFAULT_COUNCIL
    return _DEFAULT_COUNCIL

# Model priority tiers for intelligent routing - QWEN3.5+ FIRST
MODEL_TIERS = {
    "tier_1_qwen35_plus": [
        "qwen/qwen3.5-397b-a17b",
        "qwen/qwen3.5-397b-a17b:free",
    ],
    "tier_2_premium": [
        "deepseek/deepseek-v3",
        "qwen/qwen3-80b",
        "meta-llama/llama-3.3-70b-instruct",
    ],
    "tier_3_specialized": [
        "qwen/qwen-2.5-coder-32b-instruct",
        "deepseek/deepseek-r1",
    ],
    "tier_4_fast": [
        "google/gemma-3-12b-it",
        "openai/gpt-4o-mini",
        "anthropic/claude-3-haiku-20240307",
    ],
}

# Specialized model routing - QWEN3.5+ IS THE DEFAULT FOR ALL TASKS
TASK_MODEL_MAP = {
    "coding": "qwen/qwen3.5-397b-a17b",      # Qwen3.5+ handles all coding
    "reasoning": "qwen/qwen3.5-397b-a17b",   # Qwen3.5+ for all reasoning
    "math": "qwen/qwen3.5-397b-a17b",        # Qwen3.5+ for math
    "chat": "qwen/qwen3.5-397b-a17b",        # Qwen3.5+ for chat
    "creative": "qwen/qwen3.5-397b-a17b",    # Qwen3.5+ for creative
    "fast": "google/gemma-3-12b-it",         # Only use Gemma for speed
    "general": "qwen/qwen3.5-397b-a17b",     # Qwen3.5+ default for everything
}

# NVIDIA NIM API configuration
OPENROUTER_API_BASE = "https://integrate.api.nvidia.com"

def _get_openrouter_key() -> str:
    """Lazily read NVIDIA key so _load_project_env() has time to run."""
    return os.environ.get("NVIDIA_API_KEY", "") or os.environ.get("NIM_API_KEY", "") or os.environ.get("OPENROUTER_API_KEY", "")

# Council configuration
COUNCIL_THRESHOLD = float(os.environ.get("COUNCIL_THRESHOLD", "0.6"))  # 60% consensus
COUNCIL_MODELS_ENV = os.environ.get("COUNCIL_MODELS", "")
if COUNCIL_MODELS_ENV:
    DEFAULT_COUNCIL_MODELS: list[str] = [m.strip() for m in COUNCIL_MODELS_ENV.split(",")]
else:
    DEFAULT_COUNCIL_MODELS: list[str] = []  # Populated lazily via _get_default_council()


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
        self.models = models or _get_default_council()
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.on_response = on_response
        self.client = httpx.Client(timeout=120)
        self.total_calls = 0
        self.total_tokens = 0
        self._disabled_providers: dict[str, str] = {}

    def _has_alternative_provider(self, provider_key: str) -> bool:
        return any(_provider_key_for_model(model) != provider_key for model in self.models)

    def _disable_provider_for_session(self, provider_key: str, reason: str) -> None:
        self._disabled_providers[provider_key] = reason
        self.models = [
            model for model in self.models
            if _provider_key_for_model(model) != provider_key
        ]

    def query_council(self, user_message: str) -> CouncilResult:
        """Query all council models and aggregate responses.
        
        Gracefully handles partial failures — if some providers fail
        (e.g. invalid API key), still returns results from working ones.
        """
        # Query all models (missing keys are handled per-provider in _query_model)
        responses = []
        models_to_query = list(self.models)
        for i, model in enumerate(models_to_query):
            provider_key = _provider_key_for_model(model)
            if provider_key in self._disabled_providers:
                continue

            # Delay between consecutive NVIDIA requests (429 rate limits)
            if i > 0 and provider_key == "nvidia":
                prev = models_to_query[i - 1]
                if _provider_key_for_model(prev) == "nvidia":
                    time.sleep(3)

            response = self._query_model(model, user_message)

            if (
                provider_key == "nvidia"
                and response.error
                and self._has_alternative_provider(provider_key)
                and _is_nvidia_session_blocker(response.error)
            ):
                self._disable_provider_for_session(provider_key, response.error)
                continue

            responses.append(response)
            if self.on_response:
                self.on_response(response)

        # Check for partial failures and warn
        valid = [r for r in responses if not r.error]
        errors = [r for r in responses if r.error]

        if errors and valid:
            # Group errors by provider for cleaner reporting
            grouped_errors = _group_provider_errors(errors)

            warnings = []
            for provider_key, provider_errors in grouped_errors.items():
                if provider_errors:
                    warnings.append(
                        f"{_provider_label(provider_key)}: {len(provider_errors)} model(s) failed ({provider_errors[0].error})"
                    )

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
        """Query a single model in the council (NVIDIA NIM, Alibaba, ChatGPT, or CometAPI)."""
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
                from .alibaba_cloud import AlibabaCloudClient, _get_dashscope_key
                if not _get_dashscope_key():
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
                # Use NVIDIA NIM API
                if not _get_openrouter_key():
                    return CouncilResponse(
                        model=model,
                        content="",
                        latency_ms=0,
                        error="NVIDIA API key not configured",
                    )
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
                        "Authorization": f"Bearer {_get_openrouter_key()}",
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
            grouped_errors = _group_provider_errors(error_responses)

            parts = []
            for provider_key, provider_errors in grouped_errors.items():
                if provider_errors:
                    parts.append(
                        f"{_provider_label(provider_key)} ({len(provider_errors)} models): {provider_errors[0].error}"
                    )
            
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
        
        # Free models on NVIDIA NIM are actually free (no cost)
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
        provider_counts = Counter(_provider_key_for_model(model) for model in self.models)
        return {
            "providers": [
                _provider_label(provider_key)
                for provider_key in _PROVIDER_LABELS
                if provider_counts.get(provider_key, 0)
            ],
            "total_models": len(self.models),
            "nvidia_models": provider_counts.get("nvidia", 0),
            "alibaba_models": provider_counts.get("alibaba", 0),
            "chatgpt_models": provider_counts.get("chatgpt", 0),
            "cometapi_models": provider_counts.get("cometapi", 0),
            "disabled_providers": {
                _provider_label(provider_key): reason
                for provider_key, reason in self._disabled_providers.items()
            },
            "total_calls": self.total_calls,
            "total_tokens": self.total_tokens,
            "threshold": COUNCIL_THRESHOLD,
        }
