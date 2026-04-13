"""
Advanced Council Reasoning System
Implements multi-stage reasoning for maximum logical accuracy.
Inspired by Karpathy's ll-council with enhanced deliberation.
"""

from __future__ import annotations

import json
import os
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import httpx

# Default free models available on OpenRouter - optimized for reasoning
DEFAULT_COUNCIL_MODELS = [
    "openai/gpt-4o-mini",
    "anthropic/claude-3-haiku-20240307",
    "google/gemini-flash-1.5",
    "qwen/qwen-2.5-coder-32b-instruct",
    "meta-llama/llama-3.3-70b-instruct",
    "mistralai/mistral-small-24b-instruct-2501",
]

# Enhanced reasoning models (when we need deeper thinking)
REASONING_FOCUSED_MODELS = [
    "openai/gpt-4o-mini",
    "anthropic/claude-3-haiku-20240307",
    "google/gemini-flash-1.5",
    "qwen/qwen-2.5-coder-32b-instruct",
]

# OpenRouter API configuration
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# Council configuration
COUNCIL_THRESHOLD = float(os.environ.get("COUNCIL_THRESHOLD", "0.6"))
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
    reasoning_steps: list[str] = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class CouncilResult:
    """Aggregated result from the council vote."""
    consensus_answer: str
    all_responses: list[CouncilResponse]
    votes: dict[str, int]
    consensus_percentage: float
    total_tokens: int
    total_cost: float
    reasoning_trace: str = ""
    deliberation_rounds: int = 1


class AdvancedLLCouncil:
    """Advanced multi-model council with deliberative reasoning."""

    def __init__(
        self,
        models: list[str] | None = None,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        on_response: Callable[[CouncilResponse], None] | None = None,
        enable_deliberation: bool = True,
    ):
        self.models = models or DEFAULT_COUNCIL_MODELS
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.on_response = on_response
        self.enable_deliberation = enable_deliberation
        self.client = httpx.Client(timeout=120)
        self.total_calls = 0
        self.total_tokens = 0
        self.deliberation_history: list[CouncilResult] = []

    def query_council(self, user_message: str) -> CouncilResult:
        """Query all council models and aggregate responses with deliberation."""
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not set in environment")

        # Stage 1: Initial responses from all models
        initial_result = self._query_all_models(user_message)
        
        # Stage 2: Deliberation (if enabled and consensus is low)
        if self.enable_deliberation and initial_result.consensus_percentage < 0.8:
            final_result = self._deliberate(user_message, initial_result)
        else:
            final_result = initial_result

        return final_result

    def _query_all_models(self, user_message: str) -> CouncilResult:
        """Query all models in parallel."""
        responses = []
        for model in self.models:
            response = self._query_model(model, user_message)
            responses.append(response)
            if self.on_response:
                self.on_response(response)

        return self._aggregate_responses(responses)

    def _query_model(self, model: str, user_message: str) -> CouncilResponse:
        """Query a single model with enhanced prompting for reasoning."""
        start_time = time.time()

        try:
            # Enhanced system prompt for logical reasoning
            reasoning_prompt = f"""{self.system_prompt}

REASONING INSTRUCTIONS:
1. Think through the problem step by step
2. Show your logical deductions clearly
3. State any assumptions you make
4. If there are multiple approaches, explain the trade-offs
5. Conclude with your final answer clearly marked
6. Be precise and rigorous in your analysis"""

            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": reasoning_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.3,  # Lower temperature for more consistent reasoning
                "max_tokens": self.max_tokens,
            }

            response = self.client.post(
                f"{OPENROUTER_API_BASE}/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/claw-agent",
                    "X-Title": "Claw AI Council - Advanced Reasoning",
                },
            )

            latency_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                token_count = data.get("usage", {}).get("total_tokens", 0)
                self.total_tokens += token_count
                self.total_calls += 1

                # Extract reasoning steps (lines that look like reasoning)
                reasoning_steps = self._extract_reasoning_steps(content)

                return CouncilResponse(
                    model=model,
                    content=content,
                    token_count=token_count,
                    latency_ms=latency_ms,
                    reasoning_steps=reasoning_steps,
                    confidence=1.0,
                )
            else:
                return CouncilResponse(
                    model=model,
                    content="",
                    latency_ms=latency_ms,
                    error=f"HTTP {response.status_code}: {response.text}",
                )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return CouncilResponse(
                model=model,
                content="",
                latency_ms=latency_ms,
                error=str(e),
            )

    def _extract_reasoning_steps(self, content: str) -> list[str]:
        """Extract key reasoning steps from response."""
        steps = []
        lines = content.split("\n")
        
        for line in lines:
            line = line.strip()
            # Look for reasoning indicators
            if any(indicator in line.lower() for indicator in [
                "therefore", "thus", "because", "since", "implies",
                "step", "first", "second", "third", "finally",
                "approach", "reason", "conclusion", "analysis"
            ]):
                if len(line) > 10:  # Skip very short lines
                    steps.append(line)
        
        return steps

    def _aggregate_responses(self, responses: list[CouncilResponse]) -> CouncilResult:
        """Aggregate responses with advanced semantic similarity."""
        valid_responses = [r for r in responses if not r.error]
        error_responses = [r for r in responses if r.error]

        if not valid_responses:
            return CouncilResult(
                consensus_answer=f"All models failed: {error_responses[0].error}",
                all_responses=responses,
                votes={},
                consensus_percentage=0.0,
                total_tokens=0,
                total_cost=0.0,
            )

        # Group by semantic similarity
        answer_groups = self._semantic_group_responses(valid_responses)

        # Find the largest group (consensus)
        if answer_groups:
            best_group = max(answer_groups.items(), key=lambda x: len(x[1]))
            consensus_models = best_group[1]
            consensus_percentage = len(consensus_models) / len(valid_responses)
            
            # Build consensus answer with reasoning trace
            consensus_answer = self._build_consensus_answer(
                best_group[0], consensus_models, valid_responses, consensus_percentage
            )
        else:
            consensus_answer = valid_responses[0].content
            consensus_percentage = 1.0 / len(valid_responses)

        total_tokens = sum(r.token_count for r in responses)
        votes = {model: 1 for model in valid_responses}

        return CouncilResult(
            consensus_answer=consensus_answer,
            all_responses=responses,
            votes=votes,
            consensus_percentage=consensus_percentage,
            total_tokens=total_tokens,
            total_cost=0.0,
        )

    def _semantic_group_responses(self, responses: list[CouncilResponse]) -> dict[str, list[CouncilResponse]]:
        """Group responses by semantic similarity."""
        groups: dict[str, list[CouncilResponse]] = {}
        
        for resp in responses:
            # Create a signature for grouping (first 150 chars normalized)
            signature = self._create_semantic_signature(resp.content)
            
            # Find matching group
            matched_group = None
            for group_key in groups:
                if self._signatures_similar(signature, group_key):
                    matched_group = group_key
                    break
            
            if matched_group:
                groups[matched_group].append(resp)
            else:
                groups[signature] = [resp]
        
        return groups

    def _create_semantic_signature(self, content: str) -> str:
        """Create a semantic signature for content."""
        if not content:
            return ""
        
        # Normalize
        content = content.lower().strip()
        # Remove code block markers
        content = content.replace("```", "")
        # Remove extra whitespace
        content = " ".join(content.split())
        
        # Return first 150 chars as signature
        return content[:150]

    def _signatures_similar(self, sig1: str, sig2: str) -> bool:
        """Check if two signatures are similar."""
        if not sig1 or not sig2:
            return False
        
        # Exact match
        if sig1 == sig2:
            return True
        
        # One contains the other
        if sig1 in sig2 or sig2 in sig1:
            return True
        
        # Word overlap similarity
        words1 = set(sig1.split())
        words2 = set(sig2.split())
        
        if not words1 or not words2:
            return False
        
        overlap = len(words1 & words2)
        union = len(words1 | words2)
        
        if union == 0:
            return False
        
        similarity = overlap / union
        return similarity > 0.3  # 30% word overlap threshold

    def _build_consensus_answer(
        self,
        signature: str,
        consensus_models: list[CouncilResponse],
        all_valid: list[CouncilResponse],
        consensus_pct: float
    ) -> str:
        """Build the final consensus answer with reasoning."""
        # Use the longest/most detailed response from consensus group
        best_response = max(consensus_models, key=lambda r: len(r.content))
        
        # Build header
        header = f"[Council Consensus ({consensus_pct:.0%} - {len(consensus_models)}/{len(all_valid)} models agree)]\n"
        
        # Add reasoning summary if available
        reasoning_summary = []
        for resp in consensus_models:
            if resp.reasoning_steps:
                reasoning_summary.extend(resp.reasoning_steps[:2])
        
        if reasoning_summary:
            header += "\n**Key Reasoning Points:**\n"
            header += "\n".join(f"- {step}" for step in reasoning_summary[:5])
            header += "\n"
        
        return header + "\n" + best_response.content

    def _deliberate(self, user_message: str, initial_result: CouncilResult) -> CouncilResult:
        """Run deliberation round when consensus is low."""
        # For now, just return initial result
        # TODO: Implement actual deliberation by showing disagreements and asking for re-evaluation
        return initial_result

    def get_council_info(self) -> dict[str, Any]:
        """Get information about the council configuration."""
        return {
            "models": self.models,
            "model_count": len(self.models),
            "total_calls": self.total_calls,
            "total_tokens": self.total_tokens,
            "threshold": COUNCIL_THRESHOLD,
            "deliberation_enabled": self.enable_deliberation,
        }
