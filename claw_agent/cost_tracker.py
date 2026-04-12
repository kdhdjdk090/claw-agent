"""Token and cost tracking for local Ollama usage."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class TurnMetrics:
    turn_number: int
    timestamp: float
    duration_ms: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    tool_calls: int
    model: str


@dataclass
class CostTracker:
    """Track token usage, timing, and tool calls per session."""

    turns: list[TurnMetrics] = field(default_factory=list)
    session_start: float = field(default_factory=time.time)

    @property
    def total_prompt_tokens(self) -> int:
        return sum(t.prompt_tokens for t in self.turns)

    @property
    def total_completion_tokens(self) -> int:
        return sum(t.completion_tokens for t in self.turns)

    @property
    def total_tokens(self) -> int:
        return sum(t.total_tokens for t in self.turns)

    @property
    def total_tool_calls(self) -> int:
        return sum(t.tool_calls for t in self.turns)

    @property
    def total_turns(self) -> int:
        return len(self.turns)

    @property
    def elapsed_seconds(self) -> float:
        return time.time() - self.session_start

    def record_turn(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        tool_calls: int,
        duration_ms: float,
        model: str,
    ) -> None:
        self.turns.append(TurnMetrics(
            turn_number=len(self.turns) + 1,
            timestamp=time.time(),
            duration_ms=duration_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            tool_calls=tool_calls,
            model=model,
        ))

    def summary(self) -> str:
        elapsed = self.elapsed_seconds
        lines = [
            f"Session: {self.total_turns} turns in {elapsed:.1f}s",
            f"Tokens: {self.total_prompt_tokens:,} prompt + {self.total_completion_tokens:,} completion = {self.total_tokens:,} total",
            f"Tool calls: {self.total_tool_calls}",
            f"Cost: FREE (local Ollama)",
        ]
        if self.turns:
            avg_ms = sum(t.duration_ms for t in self.turns) / len(self.turns)
            lines.append(f"Avg response: {avg_ms:.0f}ms")
        return "\n".join(lines)

    def detailed_breakdown(self) -> str:
        lines = ["Turn | Tokens | Tools | Time | Model"]
        lines.append("-----|--------|-------|------|------")
        for t in self.turns:
            lines.append(
                f" {t.turn_number:3d} | {t.total_tokens:6,} | {t.tool_calls:5d} | {t.duration_ms:5.0f}ms | {t.model}"
            )
        lines.append("")
        lines.append(self.summary())
        return "\n".join(lines)
