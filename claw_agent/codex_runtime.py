"""Codex-style role-based deliberation runtime for Claw Agent.

Implements a sequential pipeline of specialized AI roles (planner, coder,
reviewer, critic, synthesizer) using free models from OpenRouter and Alibaba
Cloud, with optional ChatGPT premium mode.

Each role sees the accumulated output of prior roles, producing a structured
multi-perspective analysis of any task.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class RoleMessage:
    """Output from a single role in the deliberation pipeline."""
    role: str
    model: str
    content: str
    latency_ms: float = 0
    error: str = ""


@dataclass
class CodexTaskResult:
    """Aggregated result from the full role-based deliberation."""
    final_answer: str
    plan: str = ""
    implementation: str = ""
    review: str = ""
    critique: str = ""
    tool_actions: list[dict[str, Any]] = field(default_factory=list)
    raw_messages: list[RoleMessage] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Role model assignments — list[str] per role for primary + fallbacks
# ---------------------------------------------------------------------------

FREE_ROLE_MODELS: dict[str, dict[str, list[str]]] = {
    "openrouter": {
        "planner":     ["qwen/qwen3-235b-a22b:free", "meta-llama/llama-3.3-70b-instruct:free"],
        "coder":       ["qwen/qwen3-coder:free", "qwen/qwen3-235b-a22b:free"],
        "reviewer":    ["meta-llama/llama-3.3-70b-instruct:free", "google/gemma-4-27b-it:free"],
        "critic":      ["nousresearch/hermes-3-llama-3.1-405b:free", "google/gemma-4-27b-it:free"],
        "tool":        ["qwen/qwen3-coder:free", "qwen/qwen3-235b-a22b:free"],
        "synthesizer": ["qwen/qwen3-235b-a22b:free", "meta-llama/llama-3.3-70b-instruct:free"],
    },
    "alibaba": {
        "planner":     ["qwen3.5-397b-a17b", "qwen3-235b-a22b"],
        "coder":       ["qwen3-coder-480b-a35b-instruct", "qwen3-coder-plus"],
        "reviewer":    ["qwen3.5-397b-a17b", "qwen-plus"],
        "critic":      ["qwen-plus", "qwen3-235b-a22b"],
        "tool":        ["qwen3-coder-plus", "qwen3-coder-480b-a35b-instruct"],
        "synthesizer": ["qwen3-max", "qwen3.5-397b-a17b"],
    },
}

PREMIUM_ROLE_MODELS: dict[str, list[str]] = {
    "planner":     ["chatgpt/gpt-4o"],
    "coder":       ["chatgpt/gpt-4o"],
    "reviewer":    ["chatgpt/gpt-4o"],
    "critic":      ["chatgpt/gpt-4o"],
    "tool":        ["chatgpt/gpt-4o"],
    "synthesizer": ["chatgpt/gpt-4o"],
}


# ---------------------------------------------------------------------------
# Role system prompts
# ---------------------------------------------------------------------------

ROLE_PROMPTS: dict[str, str] = {
    "planner": (
        "You are a PLANNER agent. Given a user's task, create a clear, step-by-step "
        "execution plan. Break down complex tasks into concrete sub-tasks. "
        "Identify file changes needed, dependencies, and potential risks. "
        "Output a numbered plan with clear deliverables for each step. "
        "Be specific about file paths and function names when possible."
    ),
    "coder": (
        "You are a CODER agent. Given a plan from the planner, write the actual "
        "implementation code. Follow the plan step by step. Use idiomatic, clean code. "
        "Include all necessary imports. Show complete file contents or precise diffs. "
        "If the plan has multiple files, handle them in order. "
        "Do NOT explain the code unless asked — just write it."
    ),
    "reviewer": (
        "You are a CODE REVIEWER agent. Given the planner's plan and the coder's "
        "implementation, review the code for:\n"
        "- Correctness: does it actually implement the plan?\n"
        "- Bugs: edge cases, off-by-one, null handling, race conditions\n"
        "- Security: injection, path traversal, auth gaps (OWASP Top 10)\n"
        "- Style: naming, structure, idiomatic patterns\n"
        "List specific issues with file:line references. "
        "If the code is good, say so briefly."
    ),
    "critic": (
        "You are a CRITIC agent (devil's advocate). Challenge the approach:\n"
        "- Is this the right solution? Are there simpler alternatives?\n"
        "- What assumptions might be wrong?\n"
        "- What will break at scale or under edge cases?\n"
        "- Is the scope right — too much or too little?\n"
        "Be constructive but ruthless. If it's solid, acknowledge that."
    ),
    "tool": (
        "You are a TOOL PLANNER agent. Given the full deliberation, produce a JSON "
        "array of workspace actions to execute. Each action is an object with:\n"
        '  {"action": "read_file"|"write_file"|"replace_in_file"|"run_command",\n'
        '   "path": "relative/path",  (for file ops)\n'
        '   "content": "...",          (for write_file)\n'
        '   "old": "...", "new": "...",  (for replace_in_file)\n'
        '   "command": "..."           (for run_command)}\n'
        "Output ONLY the JSON array. No explanation."
    ),
    "synthesizer": (
        "You are a SYNTHESIZER agent. You receive the outputs from all prior roles: "
        "the plan, the implementation, the review, and the critique. "
        "Produce a single, coherent final answer that:\n"
        "1. Incorporates the best parts of the implementation\n"
        "2. Addresses issues raised by the reviewer\n"
        "3. Considers the critic's challenges\n"
        "4. Is ready to present to the user as a complete response\n"
        "If the task was code, include the final corrected code. "
        "If it was a question, give the synthesized answer."
    ),
}

# Roles in execution order (tool only runs when execute=True)
_ACTIVE_ROLES = ("planner", "coder", "reviewer", "critic")
_SYNTHESIS_ROLE = "synthesizer"
_TOOL_ROLE = "tool"

# Heuristic thresholds for council activation
_SIMPLE_MAX_WORDS = 15
_SIMPLE_KEYWORDS = frozenset({
    "what", "who", "when", "where", "how much", "define", "meaning",
    "hello", "hi", "hey", "thanks", "thank you",
})
_COMPLEX_KEYWORDS = frozenset({
    "build", "create", "implement", "refactor", "design", "architect",
    "debug", "fix", "optimize", "migrate", "deploy", "test", "review",
    "write", "generate", "scaffold", "setup", "configure", "integrate",
})


# ---------------------------------------------------------------------------
# Model backends (ABC + concrete implementations)
# ---------------------------------------------------------------------------

class ModelBackend(ABC):
    """Abstract interface for sending prompts to an LLM."""

    @abstractmethod
    def chat(self, model: str, system_prompt: str, user_prompt: str) -> RoleMessage:
        ...

    def close(self) -> None:
        pass


class OpenRouterBackend(ModelBackend):
    """Backend using OpenRouter's free-tier models via REST API."""

    API_BASE = "https://openrouter.ai/api/v1/chat/completions"
    INTER_ROLE_DELAY = 4.0  # seconds between calls to avoid rate limits
    MAX_429_RETRIES = 3     # retry count for rate-limit responses
    INITIAL_BACKOFF = 5.0   # seconds for first 429 retry

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is required for OpenRouter backend")
        self._client = __import__("httpx").Client(timeout=120)
        self._last_call = 0.0

    def chat(self, model: str, system_prompt: str, user_prompt: str) -> RoleMessage:
        # Rate-limit guard
        elapsed = time.time() - self._last_call
        if elapsed < self.INTER_ROLE_DELAY:
            time.sleep(self.INTER_ROLE_DELAY - elapsed)

        backoff = self.INITIAL_BACKOFF
        last_error = ""

        for attempt in range(1 + self.MAX_429_RETRIES):
            start = time.time()
            try:
                resp = self._client.post(
                    self.API_BASE,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://github.com/claw-agent",
                        "X-Title": "Claw Agent Codex",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.7,
                        "max_tokens": 4096,
                    },
                )
                self._last_call = time.time()
                latency = (time.time() - start) * 1000

                if resp.status_code in (429, 402):
                    last_error = f"{'Rate limited' if resp.status_code == 429 else 'Payment required'} ({model})"
                    if attempt < self.MAX_429_RETRIES:
                        time.sleep(backoff)
                        backoff *= 2
                        continue
                    return RoleMessage(
                        role="", model=model, content="",
                        latency_ms=latency,
                        error=last_error,
                    )

                if resp.status_code != 200:
                    return RoleMessage(
                        role="", model=model, content="",
                        latency_ms=latency,
                        error=f"HTTP {resp.status_code}: {resp.text[:200]}",
                    )

                data = resp.json()
                content = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )
                return RoleMessage(role="", model=model, content=content, latency_ms=latency)

            except Exception as e:
                latency = (time.time() - start) * 1000
                return RoleMessage(
                    role="", model=model, content="",
                    latency_ms=latency, error=str(e),
                )

        # Should not reach here, but just in case
        return RoleMessage(role="", model=model, content="", latency_ms=0, error=last_error)

    def close(self) -> None:
        self._client.close()


class AlibabaBackend(ModelBackend):
    """Backend using Alibaba Cloud DashScope (OpenAI-compatible) API."""

    INTER_ROLE_DELAY = 0.0  # Alibaba has generous rate limits

    def __init__(self, api_key: str | None = None):
        from .alibaba_cloud import _get_dashscope_key, DASHSCOPE_API_BASE
        self.api_key = api_key or _get_dashscope_key()
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY is required for Alibaba backend")
        self.api_base = DASHSCOPE_API_BASE + "/chat/completions"
        self._client = __import__("httpx").Client(timeout=120)
        self._last_call = 0.0

    def chat(self, model: str, system_prompt: str, user_prompt: str) -> RoleMessage:
        elapsed = time.time() - self._last_call
        if elapsed < self.INTER_ROLE_DELAY:
            time.sleep(self.INTER_ROLE_DELAY - elapsed)

        start = time.time()
        try:
            resp = self._client.post(
                self.api_base,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 4096,
                    "enable_thinking": False,
                },
            )
            self._last_call = time.time()
            latency = (time.time() - start) * 1000

            if resp.status_code != 200:
                return RoleMessage(
                    role="", model=model, content="",
                    latency_ms=latency,
                    error=f"HTTP {resp.status_code}: {resp.text[:200]}",
                )

            data = resp.json()
            content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            return RoleMessage(role="", model=model, content=content, latency_ms=latency)

        except Exception as e:
            latency = (time.time() - start) * 1000
            return RoleMessage(
                role="", model=model, content="",
                latency_ms=latency, error=str(e),
            )

    def close(self) -> None:
        self._client.close()


class ChatGPTLoginBackend(ModelBackend):
    """Premium backend wrapping the existing ChatGPT MCP bridge."""

    def __init__(self):
        from .chatgpt_mcp import ChatGPTMCPClient
        self._client = ChatGPTMCPClient()

    def chat(self, model: str, system_prompt: str, user_prompt: str) -> RoleMessage:
        start = time.time()
        try:
            resp = self._client.query(
                model=model,
                prompt=user_prompt,
                system_prompt=system_prompt,
            )
            latency = (time.time() - start) * 1000
            if resp.error:
                return RoleMessage(
                    role="", model=model, content="",
                    latency_ms=latency, error=resp.error,
                )
            return RoleMessage(role="", model=model, content=resp.content, latency_ms=latency)
        except Exception as e:
            latency = (time.time() - start) * 1000
            return RoleMessage(
                role="", model=model, content="",
                latency_ms=latency, error=str(e),
            )

    def close(self) -> None:
        self._client.close()


# ---------------------------------------------------------------------------
# Workspace — safe file/command access within a root directory
# ---------------------------------------------------------------------------

class Workspace:
    """Sandboxed workspace for file operations and command execution.

    All file paths are resolved relative to *root* and must stay inside it.
    """

    # Commands that are never allowed
    _BLOCKED_COMMANDS = frozenset({
        "rm -rf /", "rm -rf /*", "mkfs", "dd if=", ":(){:|:&};:",
        "format c:", "del /s /q c:\\",
    })

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            raise ValueError(f"Workspace root does not exist: {self.root}")

    def _resolve(self, rel_path: str) -> Path:
        """Resolve a relative path and ensure it stays inside the workspace."""
        resolved = (self.root / rel_path).resolve()
        if not str(resolved).startswith(str(self.root)):
            raise PermissionError(
                f"Path escape blocked: {rel_path!r} resolves outside workspace"
            )
        return resolved

    def read_file(self, rel_path: str, max_bytes: int = 64_000) -> str:
        p = self._resolve(rel_path)
        if not p.is_file():
            return f"[file not found: {rel_path}]"
        text = p.read_text(encoding="utf-8", errors="replace")
        if len(text) > max_bytes:
            text = text[:max_bytes] + f"\n... [truncated at {max_bytes} bytes]"
        return text

    def write_file(self, rel_path: str, content: str) -> str:
        p = self._resolve(rel_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"Wrote {len(content)} bytes to {rel_path}"

    def replace_in_file(self, rel_path: str, old: str, new: str) -> str:
        p = self._resolve(rel_path)
        if not p.is_file():
            return f"[file not found: {rel_path}]"
        text = p.read_text(encoding="utf-8")
        if old not in text:
            return f"[old string not found in {rel_path}]"
        count = text.count(old)
        text = text.replace(old, new, 1)
        p.write_text(text, encoding="utf-8")
        return f"Replaced 1 of {count} occurrences in {rel_path}"

    def run_command(self, command: str, timeout: int = 30) -> str:
        # Safety check
        cmd_lower = command.lower().strip()
        for blocked in self._BLOCKED_COMMANDS:
            if blocked in cmd_lower:
                return f"[BLOCKED: dangerous command refused: {command!r}]"

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.root),
            )
            output = result.stdout
            if result.stderr:
                output += "\n[stderr]\n" + result.stderr
            if result.returncode != 0:
                output += f"\n[exit code: {result.returncode}]"
            return output[:16_000] if len(output) > 16_000 else output
        except subprocess.TimeoutExpired:
            return f"[command timed out after {timeout}s]"
        except Exception as e:
            return f"[command error: {e}]"


# ---------------------------------------------------------------------------
# CodexRuntime — the main orchestrator
# ---------------------------------------------------------------------------

def _detect_provider() -> str:
    """Auto-detect the best free provider based on available API keys."""
    provider = os.environ.get("COUNCIL_PROVIDER", "auto").strip().lower()
    if provider in ("openrouter", "alibaba", "chatgpt"):
        return provider

    # Auto mode: prefer OpenRouter (larger free model selection), fall back to Alibaba
    if os.environ.get("OPENROUTER_API_KEY", ""):
        return "openrouter"
    from .alibaba_cloud import _get_dashscope_key
    if _get_dashscope_key():
        return "alibaba"
    return "openrouter"  # will fail at backend init with a clear error


class CodexRuntime:
    """Role-based deliberation runtime inspired by OpenAI Codex.

    Runs a sequential pipeline: planner → coder → reviewer → critic → synthesizer.
    Each role uses a specialized model and sees all prior role outputs.
    """

    def __init__(
        self,
        workspace_root: str | Path | None = None,
        backend_mode: str = "free",
    ):
        self.backend_mode = backend_mode
        self._workspace = Workspace(workspace_root or os.getcwd())

        # Select backend and model map
        if backend_mode == "chatgpt":
            self._provider = "chatgpt"
            self._backend: ModelBackend = ChatGPTLoginBackend()
            self._role_models = PREMIUM_ROLE_MODELS
        else:
            self._provider = _detect_provider()
            if self._provider == "alibaba":
                self._backend = AlibabaBackend()
                self._role_models = FREE_ROLE_MODELS["alibaba"]
            else:
                self._backend = OpenRouterBackend()
                self._role_models = FREE_ROLE_MODELS["openrouter"]

    # -- Heuristics ----------------------------------------------------------

    @staticmethod
    def should_use_council(user_message: str) -> bool:
        """Return True if the message is complex enough to warrant full council."""
        lower = user_message.lower()
        words = lower.split()

        def _has_keyword(keywords: frozenset[str]) -> bool:
            """Word-boundary match to avoid false positives like 'latest' matching 'test'."""
            return any(re.search(rf'\b{re.escape(kw)}\b', lower) for kw in keywords)

        if len(words) <= _SIMPLE_MAX_WORDS:
            # Check for complex keywords even in short messages
            if _has_keyword(_COMPLEX_KEYWORDS):
                return True
            # Simple greeting / factual question
            if _has_keyword(_SIMPLE_KEYWORDS):
                return False
        # Longer messages or those with complex keywords → council
        if _has_keyword(_COMPLEX_KEYWORDS):
            return True
        # Default: use council for anything over the word threshold
        return len(words) > _SIMPLE_MAX_WORDS

    # -- Role execution -------------------------------------------------------

    def _ask_role(self, role: str, user_prompt: str) -> RoleMessage:
        """Send a prompt to the model assigned to *role*, with fallback.

        If all models on the primary backend fail with rate-limit errors and
        a secondary provider is available, attempts a cross-provider fallback.
        """
        system_prompt = ROLE_PROMPTS.get(role, "You are a helpful assistant.")
        models = self._role_models.get(role, ["qwen/qwen3-235b-a22b:free"])

        last_msg: RoleMessage | None = None
        all_rate_limited = True

        for model in models:
            msg = self._backend.chat(model, system_prompt, user_prompt)
            msg.role = role
            if not msg.error:
                return msg
            last_msg = msg
            if "rate limit" not in (msg.error or "").lower():
                all_rate_limited = False

        # Cross-provider fallback: if OpenRouter is rate-limited, try Alibaba
        if all_rate_limited and self._provider == "openrouter":
            try:
                dashscope_key = os.environ.get("DASHSCOPE_API_KEY", "")
                if dashscope_key:
                    fallback = AlibabaBackend(api_key=dashscope_key)
                    fallback_models = FREE_ROLE_MODELS["alibaba"].get(role, [])
                    for fb_model in fallback_models:
                        fb_msg = fallback.chat(fb_model, system_prompt, user_prompt)
                        fb_msg.role = role
                        if not fb_msg.error:
                            fallback.close()
                            return fb_msg
                        last_msg = fb_msg
                    fallback.close()
            except Exception:
                pass  # Alibaba fallback not available

        # All models failed — return last error with friendly message
        if last_msg:
            if all_rate_limited:
                last_msg.error = (
                    "All models rate-limited. Try again in ~30s, "
                    "or set COUNCIL_PROVIDER=alibaba for Alibaba Cloud fallback."
                )
            last_msg.role = role
            return last_msg
        return RoleMessage(role=role, model="unknown", content="", error="no models configured")

    def _repo_context(self) -> str:
        """Read common project files for context (truncated to 4K each)."""
        context_files = ["README.md", "pyproject.toml", "package.json", "Cargo.toml"]
        parts: list[str] = []
        for fname in context_files:
            content = self._workspace.read_file(fname, max_bytes=4096)
            if not content.startswith("[file not found"):
                parts.append(f"=== {fname} ===\n{content}")
        return "\n\n".join(parts) if parts else "(no project context files found)"

    # -- Main pipeline --------------------------------------------------------

    def run_task(
        self,
        user_message: str,
        execute: bool = False,
    ) -> CodexTaskResult:
        """Run the full role-based deliberation pipeline.

        If the message is simple, uses a single synthesizer call.
        Otherwise runs: planner → coder → reviewer → critic → synthesizer.

        When *execute* is True, also runs the tool planner and executes actions.
        """
        raw: list[RoleMessage] = []
        repo_ctx = self._repo_context()

        # --- Fast path: simple query → single model call ---
        if not self.should_use_council(user_message):
            msg = self._ask_role("synthesizer", user_message)
            raw.append(msg)
            return CodexTaskResult(
                final_answer=msg.content or f"[error: {msg.error}]",
                raw_messages=raw,
            )

        # --- Full deliberation pipeline ---
        context = f"## Project Context\n{repo_ctx}\n\n## User Task\n{user_message}"

        # 1. Planner
        plan_msg = self._ask_role("planner", context)
        raw.append(plan_msg)
        plan_text = plan_msg.content or "(planner failed)"

        # 2. Coder
        coder_prompt = (
            f"{context}\n\n## Plan (from Planner)\n{plan_text}\n\n"
            "Now implement the plan. Write the code."
        )
        code_msg = self._ask_role("coder", coder_prompt)
        raw.append(code_msg)
        code_text = code_msg.content or "(coder failed)"

        # 3. Reviewer
        review_prompt = (
            f"{context}\n\n## Plan\n{plan_text}\n\n"
            f"## Implementation (from Coder)\n{code_text}\n\n"
            "Review this implementation."
        )
        review_msg = self._ask_role("reviewer", review_prompt)
        raw.append(review_msg)
        review_text = review_msg.content or "(reviewer failed)"

        # 4. Critic
        critic_prompt = (
            f"{context}\n\n## Plan\n{plan_text}\n\n"
            f"## Implementation\n{code_text}\n\n"
            f"## Review\n{review_text}\n\n"
            "Challenge this approach."
        )
        critic_msg = self._ask_role("critic", critic_prompt)
        raw.append(critic_msg)
        critic_text = critic_msg.content or "(critic failed)"

        # 5. Tool planner (only when execute=True)
        tool_actions: list[dict[str, Any]] = []
        if execute:
            tool_prompt = (
                f"{context}\n\n## Plan\n{plan_text}\n\n"
                f"## Implementation\n{code_text}\n\n"
                f"## Review\n{review_text}\n\n"
                f"## Critique\n{critic_text}\n\n"
                "Produce the JSON array of workspace actions."
            )
            tool_msg = self._ask_role("tool", tool_prompt)
            raw.append(tool_msg)
            tool_actions = self._parse_tool_actions(tool_msg.content or "[]")

        # 6. Synthesizer
        synth_prompt = (
            f"## User Task\n{user_message}\n\n"
            f"## Plan\n{plan_text}\n\n"
            f"## Implementation\n{code_text}\n\n"
            f"## Review\n{review_text}\n\n"
            f"## Critique\n{critic_text}\n\n"
            "Synthesize the final answer."
        )
        synth_msg = self._ask_role("synthesizer", synth_prompt)
        raw.append(synth_msg)

        result = CodexTaskResult(
            final_answer=synth_msg.content or f"[synthesis failed: {synth_msg.error}]",
            plan=plan_text,
            implementation=code_text,
            review=review_text,
            critique=critic_text,
            tool_actions=tool_actions,
            raw_messages=raw,
        )

        # Execute tool actions if requested
        if execute and tool_actions:
            self.execute_actions(tool_actions)

        return result

    # -- Tool execution -------------------------------------------------------

    @staticmethod
    def _parse_tool_actions(text: str) -> list[dict[str, Any]]:
        """Extract a JSON array from the tool planner's output."""
        # Try to find JSON array in the text
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if not match:
            return []
        try:
            actions = json.loads(match.group())
            if isinstance(actions, list):
                return actions
        except json.JSONDecodeError:
            pass
        return []

    def execute_actions(self, actions: list[dict[str, Any]]) -> list[dict[str, str]]:
        """Execute workspace actions from the tool planner."""
        results: list[dict[str, str]] = []
        for action in actions:
            act = action.get("action", "")
            try:
                if act == "read_file":
                    out = self._workspace.read_file(action["path"])
                elif act == "write_file":
                    out = self._workspace.write_file(action["path"], action["content"])
                elif act == "replace_in_file":
                    out = self._workspace.replace_in_file(
                        action["path"], action["old"], action["new"],
                    )
                elif act == "run_command":
                    out = self._workspace.run_command(action["command"])
                else:
                    out = f"[unknown action: {act}]"
            except (PermissionError, KeyError, ValueError) as e:
                out = f"[action error: {e}]"
            results.append({"action": act, "result": out})
        return results

    # -- Cleanup --------------------------------------------------------------

    def close(self) -> None:
        """Release backend resources."""
        self._backend.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
