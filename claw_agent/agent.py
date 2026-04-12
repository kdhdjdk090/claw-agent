"""Core agent loop with streaming - orchestrates Ollama + tool execution.

Supports both blocking chat() and streaming stream_chat() for CLI/UI use.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from typing import Any, Callable, Generator

import httpx

from .tools import TOOL_REGISTRY, OLLAMA_TOOL_DEFINITIONS
from .permissions import PermissionContext, GATED_TOOLS
from .sessions import Session
from .cost_tracker import CostTracker
from .hooks import HookRunner

SYSTEM_PROMPT_TEMPLATE = """\
You are Claw, an expert autonomous AI coding agent running on model "{model}".
You have deep expertise in all programming languages, frameworks, databases, DevOps, cloud, \
system administration, and software engineering. You act decisively — you NEVER ask questions.
When asked what model you are, say you are Claw running on "{model}" {mode_label}.

WORKSPACE: {cwd}
PLATFORM: {platform}

TOOLS (26):
  File: read_file, write_file, list_directory, find_files
  Shell: run_command, powershell
  Search: grep_search
  Edit: replace_in_file, multi_edit_file, insert_at_line, diff_files
  Web: web_fetch, web_search
  Agent: run_subagent, plan_and_execute
  Tasks: task_create, task_update, task_list, task_get
  Code: notebook_run
  Context: get_workspace_context, git_diff, git_log
  Utility: sleep, config_get, config_set

SUPERPOWERS — your approach to any task:
1. EXPLORE first: list_directory, find_files, grep_search, get_workspace_context to map the codebase.
2. UNDERSTAND: read_file relevant files. Read imports, types, tests. Understand before editing.
3. PLAN: For complex tasks, use task_create to track steps. For massive tasks, use plan_and_execute.
4. ACT: write_file, replace_in_file, multi_edit_file, run_command. Make changes precisely.
5. VERIFY: read_file the result. Run tests with run_command. Check git_diff. Confirm correctness.

CRITICAL RULES:
1. NEVER ask the user to clarify. Use tools to figure it out yourself.
2. Use "." or "{cwd}" for the current directory. Use relative paths.
3. Read files before editing. Verify changes after making them.
4. Be concise in final responses. Summarize what you did and what changed.
5. STOP when you have answered the question or completed the task. Do NOT keep calling tools.
6. If a tool returns an error, empty, "(no output)", or "[exit code: N]" with N≠0, DO NOT call it again. Move on or STOP.
7. If run_command returns "(no output)", it succeeded silently. Do NOT re-run it.
8. NEVER run the same tool more than twice in a row. If it didn't work twice, STOP and explain.
9. NEVER run "claw" or any command that spawns this agent recursively.
10. Complete the task thoroughly. Use as many tool calls as needed — you have a generous budget.
11. NEVER fabricate URLs, file paths, or content. Only use real data from tool results.
12. NEVER re-explore something you already explored. If you listed a directory, don't list it again.
13. When asked "is everything working" or "check all features", run tests ONCE, report results, STOP.
14. On Windows: the shell is cmd.exe. Use cmd commands: `dir`, `type`, `findstr`, `for`. NEVER use `wc`, `head`, `tail`, `cat`, `grep`, `awk`, `sed` (Unix-only). NEVER use PowerShell cmdlets like `Get-ChildItem`, `Select-String`, `Measure-Object` — they will fail. To count files use `dir /s /b *.py | find /c /v ""`. To search text use `findstr /s /i "pattern" *.py`.
15. For multi-file changes, edit each file in sequence. Verify the final state.
16. When debugging: read error messages carefully, grep for the error, find the root cause.
17. When refactoring: understand all callers before changing a function signature.
18. If you see 'SYSTEM: STOP' in a tool result, respond with text only — no more tools.
"""

MAX_ITERATIONS = 200
OLLAMA_BASE = "http://localhost:11434"
# When total token count exceeds this, auto-compact the conversation
MAX_CONTEXT_TOKENS = 200_000
# Start compacting at 50% of the hard context ceiling to avoid overflow.
AUTO_COMPACT_THRESHOLD = MAX_CONTEXT_TOKENS // 2
# Keep the system message + last N messages after compaction
COMPACT_KEEP_RECENT = 8

# Project config files loaded into system prompt (searched in cwd, then parents)
CONFIG_FILES = ("MEMORY.md", "SOUL.md", ".claw")


def _load_project_context() -> str:
    """Load MEMORY.md, SOUL.md, and .claw from the workspace into the system prompt."""
    parts = []
    cwd = os.getcwd()
    for filename in CONFIG_FILES:
        # Search cwd, then up to 3 parent dirs
        search = cwd
        for _ in range(4):
            path = os.path.join(search, filename)
            if os.path.isfile(path):
                try:
                    with open(path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read(4000)  # cap at 4K per file
                    parts.append(f"\n--- {filename} ---\n{content.strip()}")
                except OSError:
                    pass
                break
            parent = os.path.dirname(search)
            if parent == search:
                break
            search = parent
    return "\n".join(parts)


def _load_claw_config() -> dict:
    """Load and parse .claw JSON config. Returns settings dict (empty if no config)."""
    cwd = os.getcwd()
    search = cwd
    for _ in range(4):
        path = os.path.join(search, ".claw")
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.loads(f.read())
                if isinstance(data, dict):
                    return data
            except (json.JSONDecodeError, OSError):
                pass
            break
        parent = os.path.dirname(search)
        if parent == search:
            break
        search = parent
    return {}

# Commands that must never be executed (anti-recursion + safety)
BLOCKED_COMMANDS = (
    "claw",
    "claw ",
    "python -m claw_agent",
    "python claw_agent",
    "python bridge.py",
    "python src/bridge.py",
)

def _is_repetitive(text: str, min_chunk: int = 40, min_repeats: int = 3) -> bool:
    """Detect if streamed text ends with a repeating pattern (model stuck in loop)."""
    if len(text) < min_chunk * min_repeats:
        return False
    # Check if the last min_chunk chars appear min_repeats+ times in the tail
    tail = text[-(min_chunk * (min_repeats + 1)):]
    pattern = text[-min_chunk:]
    return tail.count(pattern) >= min_repeats


_TOOL_CALL_RE = re.compile(
    r'(?:```(?:json)?\s*)?'
    r'\{\s*"name"\s*:\s*"(\w+)"\s*,\s*"arguments"\s*:\s*(\{[^}]*\})\s*\}'
    r'(?:\s*```)?',
    re.DOTALL,
)

# --- Event types for streaming ---
class StreamEvent:
    """Base event emitted during streaming."""
    pass

class TextDelta(StreamEvent):
    def __init__(self, text: str):
        self.text = text

class ToolCallStart(StreamEvent):
    def __init__(self, name: str, arguments: dict):
        self.name = name
        self.arguments = arguments

class ToolCallEnd(StreamEvent):
    def __init__(self, name: str, result: str, duration_ms: float):
        self.name = name
        self.result = result
        self.duration_ms = duration_ms

class TurnComplete(StreamEvent):
    def __init__(self, content: str, prompt_tokens: int, completion_tokens: int):
        self.content = content
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens

class AgentDone(StreamEvent):
    def __init__(self, final_text: str):
        self.final_text = final_text


class Agent:
    """Autonomous agent with streaming support."""

    def __init__(
        self,
        model: str = "deepseek-v3.1:671b-cloud",
        base_url: str = OLLAMA_BASE,
        permissions: PermissionContext | None = None,
        session: Session | None = None,
        on_tool_call: Callable[[str, dict], None] | None = None,
        on_tool_result: Callable[[str, str], None] | None = None,
        confirm_fn: Callable[[], bool] | None = None,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=300)
        self.permissions = permissions or PermissionContext.default()
        self.session = session or Session(model=model)
        self.cost = CostTracker()
        self._confirm_fn = confirm_fn
        self._hooks = HookRunner.load()  # Cache hooks once at init (M1)

        # Determine mode label for system prompt
        is_local_ollama = "localhost" in self.base_url or "127.0.0.1" in self.base_url
        self._mode_label = "via local Ollama" if is_local_ollama else "via Cloud API"

        # H4: Load and apply .claw project config
        claw_config = _load_claw_config()
        if claw_config:
            if "model" in claw_config and model == "deepseek-v3.1:671b-cloud":
                # Only override if user didn't explicitly pick a model
                self.model = claw_config["model"]
            if "auto_approve" in claw_config:
                self.permissions.auto_approve = bool(claw_config["auto_approve"])
            if "max_iterations" in claw_config:
                # Store per-instance override
                self._max_iterations = min(int(claw_config["max_iterations"]), 200)
            else:
                self._max_iterations = MAX_ITERATIONS
            if "blocked_commands" in claw_config:
                # Extend blocked tools from config
                extra_denies = frozenset(
                    t.strip() for t in claw_config.get("blocked_tools", [])
                )
                if extra_denies:
                    self.permissions.deny_names = self.permissions.deny_names | extra_denies
        else:
            self._max_iterations = MAX_ITERATIONS

        self._compacted = False
        # Build system prompt from template + project files (MEMORY.md, SOUL.md, .claw)
        project_ctx = _load_project_context()
        system_content = SYSTEM_PROMPT_TEMPLATE.format(
            cwd=os.getcwd(), 
            model=self.model, 
            platform=sys.platform,
            mode_label=self._mode_label
        )
        if project_ctx:
            system_content += "\n\nPROJECT CONTEXT (loaded from workspace files):" + project_ctx
        self.messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_content},
        ]
        self._on_tool_call = on_tool_call
        self._on_tool_result = on_tool_result

    # ---- public: blocking --------------------------------------------------

    def chat(self, user_message: str) -> str:
        """Blocking chat - collects all streaming events, returns final text."""
        final = ""
        for event in self.stream_chat(user_message):
            if isinstance(event, AgentDone):
                final = event.final_text
        return final

    # ---- public: streaming -------------------------------------------------

    def stream_chat(self, user_message: str) -> Generator[StreamEvent, None, None]:
        """Stream events as the agent thinks, calls tools, and responds."""
        self.messages.append({"role": "user", "content": user_message})
        self.session.total_turns += 1
        yield from self._stream_loop()
        # Sync full conversation (minus original system prompt) to session for persistence
        # H7: Preserve compaction summaries (role=system, not index 0) so resumed sessions have context
        self.session.messages = [m for m in self.messages[1:] if not (m.get("role") == "system" and "CONVERSATION COMPACTED" not in m.get("content", ""))]
        # C3: Sync token counts to session so they persist on save
        self.session.input_tokens = self.cost.total_prompt_tokens
        self.session.output_tokens = self.cost.total_completion_tokens

    # ---- internal ----------------------------------------------------------

    def _compact_if_needed(self):
        """Auto-compact when the live session is approaching the context ceiling."""
        # H5: Use estimated current context size (chars/4), but also honor the
        # latest provider-reported token count when available.
        total_chars = sum(len(str(m.get("content", ""))) for m in self.messages)
        est_tokens = total_chars // 4
        recorded_tokens = self.cost.turns[-1].total_tokens if self.cost.turns else 0
        compact_pressure = max(est_tokens, recorded_tokens)
        if compact_pressure < AUTO_COMPACT_THRESHOLD:
            return
        # Keep system message (index 0) + last COMPACT_KEEP_RECENT messages
        if len(self.messages) <= COMPACT_KEEP_RECENT + 1:
            return
        system = self.messages[0]
        old = self.messages[1:-COMPACT_KEEP_RECENT]
        recent = self.messages[-COMPACT_KEEP_RECENT:]

        # Build a summary of discarded messages
        summary_parts = []
        for m in old:
            role = m.get("role", "?")
            content = m.get("content", "")
            if role == "tool":
                summary_parts.append(f"[tool result: {content[:100]}]")
            elif role == "assistant":
                tc = m.get("tool_calls")
                if tc:
                    names = [t.get("function", {}).get("name", "?") for t in tc]
                    summary_parts.append(f"[called tools: {', '.join(names)}]")
                if content:
                    summary_parts.append(f"[assistant: {content[:150]}]")
            elif role == "user":
                summary_parts.append(f"[user: {content[:150]}]")

        summary = "CONVERSATION COMPACTED - earlier context summary:\n" + "\n".join(summary_parts)
        self.messages = [system, {"role": "system", "content": summary}] + recent
        # Clear recorded turns so token count resets
        self.cost.turns.clear()
        self._compacted = True

    def _stream_loop(self) -> Generator[StreamEvent, None, None]:
        # ---- Loop protection (fresh per user message) ----
        total_errors = 0
        empty_results = 0  # tools returning no output / "(no output)"
        tool_call_counts: dict[str, int] = {}  # per-tool call counter
        total_tool_calls = 0  # absolute cap across entire turn
        consecutive_same_tool = 0
        last_tool_name = ""
        MAX_TOOLS_PER_ITERATION = 15  # cap tool calls per single LLM response
        MAX_TOTAL_TOOL_CALLS = 200    # absolute cap across all iterations

        for iteration in range(self._max_iterations):
            # Auto-compact to avoid context overflow
            self._compact_if_needed()

            start = time.time()

            # --- Streaming request to Ollama ---
            payload = {
                "model": self.model,
                "messages": self.messages,
                "tools": OLLAMA_TOOL_DEFINITIONS,
                "stream": True,
            }

            collected_content = ""
            tool_calls: list[dict] = []
            prompt_tokens = 0
            completion_tokens = 0

            with self.client.stream(
                "POST", f"{self.base_url}/api/chat", json=payload, timeout=300
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    msg = chunk.get("message", {})

                    # Accumulate text content + stream deltas
                    delta = msg.get("content", "")
                    if delta:
                        collected_content += delta
                        yield TextDelta(delta)

                    # Detect repetitive text (model stuck in generation loop)
                    if _is_repetitive(collected_content):
                        collected_content = collected_content[:-(40 * 2)]  # trim repeated tail
                        break

                    # Accumulate tool calls
                    if msg.get("tool_calls"):
                        tool_calls.extend(msg["tool_calls"])

                    # Final chunk has done=true with token counts
                    if chunk.get("done"):
                        prompt_tokens = chunk.get("prompt_eval_count", 0)
                        completion_tokens = chunk.get("eval_count", 0)

            duration_ms = (time.time() - start) * 1000

            # --- Cap tool calls BEFORE building history ---
            if tool_calls:
                # Cap per-iteration (Ollama can batch 15+ in one response)
                if len(tool_calls) > MAX_TOOLS_PER_ITERATION:
                    tool_calls = tool_calls[:MAX_TOOLS_PER_ITERATION]
                # Absolute total cap across all iterations
                remaining = MAX_TOTAL_TOOL_CALLS - total_tool_calls
                if remaining <= 0:
                    # Build assistant msg without tool_calls so model knows to stop
                    self.messages.append({"role": "assistant", "content": collected_content or "(tool budget exhausted)"})
                    self.messages.append({"role": "system", "content": "SYSTEM: STOP — tool call budget exhausted. Summarize and respond now."})
                    yield TurnComplete(collected_content, prompt_tokens, completion_tokens)
                    yield AgentDone("[Stopped: tool call budget exhausted]")
                    return
                if len(tool_calls) > remaining:
                    tool_calls = tool_calls[:remaining]
                total_tool_calls += len(tool_calls)

            # Build the assistant message for history (with CAPPED tool_calls only)
            assistant_msg: dict[str, Any] = {"role": "assistant", "content": collected_content}
            if tool_calls:
                assistant_msg["tool_calls"] = tool_calls
            self.messages.append(assistant_msg)

            yield TurnComplete(collected_content, prompt_tokens, completion_tokens)

            # --- Execute tool calls if any ---
            if tool_calls:

                # Track tool results for circuit breakers
                msgs_before = len(self.messages)
                yield from self._execute_tool_calls(tool_calls)
                self.cost.record_turn(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                    tool_calls=len(tool_calls),
                    duration_ms=duration_ms,
                    model=self.model,
                )

                # --- Circuit breaker checks on tool results ---
                _EMPTY_PATTERNS = {'', 'None', 'null', '(no output)', 'no output'}
                new_msgs = self.messages[msgs_before:]
                for tm in new_msgs:
                    if tm.get("role") != "tool":
                        continue
                    content = tm.get("content", "")
                    stripped = content.strip()
                    # Only match ACTUAL tool failures, not content that happens to contain "error"
                    is_err = bool(
                        re.search(r'^(?:Error:|Permission denied:|Blocked:)', stripped, re.I | re.M)
                        or re.search(r'not recognized as an internal or external command', content, re.I)
                        or re.search(r'\[exit code:\s*(?:[2-9]|\d{2,})\]', content)
                        or re.search(r'^Traceback \(most recent call last\):', stripped, re.M)
                    )
                    is_empty = len(stripped) == 0 or stripped in _EMPTY_PATTERNS
                    if is_err:
                        total_errors += 1
                    if is_empty:
                        empty_results += 1

                # Track per-tool call counts + consecutive repetition
                tc_names = [tc.get("function", {}).get("name", "") for tc in tool_calls]
                for tn in tc_names:
                    tool_call_counts[tn] = tool_call_counts.get(tn, 0) + 1
                # Consecutive = same DOMINANT tool across iterations (not within batch)
                dominant = max(set(tc_names), key=tc_names.count) if tc_names else ""
                if dominant == last_tool_name:
                    consecutive_same_tool += 1
                else:
                    consecutive_same_tool = 0
                last_tool_name = dominant

                # --- Hard stops ---
                if total_errors >= 8:
                    self.messages.append({"role": "system", "content": "SYSTEM: STOP — too many tool errors. Respond with what you know."})
                    yield AgentDone("[Stopped: too many tool errors]")
                    return
                if empty_results >= 5:
                    self.messages.append({"role": "system", "content": "SYSTEM: STOP — tools returning empty/no output. Respond with what you know."})
                    yield AgentDone("[Stopped: repeated empty tool results]")
                    return
                if consecutive_same_tool >= 8:
                    self.messages.append({"role": "system", "content": f"SYSTEM: STOP — you called '{last_tool_name}' 9+ iterations in a row. Respond to the user now."})
                    yield AgentDone(f"[Stopped: '{last_tool_name}' called repeatedly]")
                    return
                # Per-tool budget: run_command max 30, others max 50
                for tn, count in tool_call_counts.items():
                    limit = 30 if tn == "run_command" else 50
                    if count >= limit:
                        self.messages.append({"role": "system", "content": f"SYSTEM: STOP — '{tn}' called {count} times this turn. Summarize and respond now."})
                        yield AgentDone(f"[Stopped: '{tn}' used {count} times]")
                        return

                continue

            # Fallback: parse tool calls from text
            parsed = self._parse_tool_calls_from_text(collected_content)
            if parsed:
                for name, args in parsed:
                    yield from self._run_single_tool(name, args)
                self.cost.record_turn(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                    tool_calls=len(parsed),
                    duration_ms=duration_ms,
                    model=self.model,
                )
                continue

            # No tool calls — agent is done
            self.cost.record_turn(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                tool_calls=0,
                duration_ms=duration_ms,
                model=self.model,
            )
            yield AgentDone(collected_content or "[No response]")
            return

        # Iteration limit reached — give model one last chance to summarize WITHOUT tools
        self.messages.append({"role": "system", "content": "SYSTEM: Tool call limit reached. Summarize your findings and respond to the user now. Do NOT call any more tools."})
        try:
            start = time.time()
            payload = {
                "model": self.model,
                "messages": self.messages,
                "stream": True,
                # NO tools — force text-only response
            }
            collected_summary = ""
            prompt_tokens = completion_tokens = 0
            with self.client.stream(
                "POST", f"{self.base_url}/api/chat", json=payload, timeout=120
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    msg = chunk.get("message", {})
                    delta = msg.get("content", "")
                    if delta:
                        collected_summary += delta
                        yield TextDelta(delta)
                    if _is_repetitive(collected_summary):
                        break
                    if chunk.get("done"):
                        prompt_tokens = chunk.get("prompt_eval_count", 0)
                        completion_tokens = chunk.get("eval_count", 0)
            duration_ms = (time.time() - start) * 1000
            self.messages.append({"role": "assistant", "content": collected_summary})
            self.cost.record_turn(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                tool_calls=0,
                duration_ms=duration_ms,
                model=self.model,
            )
            yield AgentDone(collected_summary or "[Agent hit iteration limit]")
        except Exception:
            yield AgentDone("[Agent hit iteration limit - task may be incomplete.]")

    def _execute_tool_calls(self, tool_calls: list[dict]) -> Generator[StreamEvent, None, None]:
        for tc in tool_calls:
            fn = tc.get("function", {})
            name = fn.get("name", "")
            arguments = fn.get("arguments", {})
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {}
            yield from self._run_single_tool(name, arguments)

    def _run_single_tool(self, name: str, arguments: dict) -> Generator[StreamEvent, None, None]:
        # Guard: reject tool calls with hallucinated/spam arguments
        for v in arguments.values():
            sv = str(v)
            if any(spam in sv.lower() for spam in (".com复制", "开奖", "赛车", "彩票")):
                yield ToolCallStart(name, arguments)
                yield ToolCallEnd(name, "Rejected: hallucinated spam in arguments", 0)
                self.messages.append({"role": "tool", "content": "Error: invalid arguments rejected"})
                return

        # C1: Enforce permission gating for GATED_TOOLS
        if name in GATED_TOOLS:
            desc = f"{name}({', '.join(f'{k}={str(v)[:60]}' for k, v in arguments.items())})"
            if not self.permissions.request_permission(name, desc, self._confirm_fn):
                yield ToolCallStart(name, arguments)
                yield ToolCallEnd(name, f"Permission denied: user declined '{name}'", 0)
                self.messages.append({"role": "tool", "content": f"Permission denied: user declined '{name}'"})
                return

        # Run pre-hooks (may deny the tool call) — use cached hooks (M1)
        hook_result = self._hooks.run_pre_hooks(name, arguments)
        if not hook_result.allow:
            yield ToolCallStart(name, arguments)
            yield ToolCallEnd(name, f"Blocked by hook: {hook_result.message}", 0)
            self.messages.append({"role": "tool", "content": f"Blocked by hook: {hook_result.message}"})
            return

        yield ToolCallStart(name, arguments)
        start = time.time()

        if self.permissions.blocks(name):
            result = f"Permission denied: tool '{name}' is blocked."
            self.permissions.denials.append({"tool": name, "reason": "blocked"})
        elif name == "run_command":
            cmd = arguments.get("command", "")
            # Block recursive self-execution
            cmd_stripped = cmd.strip().lower()
            if any(cmd_stripped.startswith(bc) or cmd_stripped == bc.strip() for bc in BLOCKED_COMMANDS):
                result = f"Blocked: cannot run '{cmd}' (recursive self-execution)"
            else:
                # C2: Actually enforce dangerous command blocking
                warning = self.permissions.check_command_safety(cmd)
                if warning and not self.permissions.auto_approve:
                    if self._confirm_fn:
                        sys.stderr.write(f"\n⚠ {warning}\n")
                        if not self._confirm_fn():
                            result = f"Blocked: user declined dangerous command — {warning}"
                            self.permissions.denials.append({"tool": name, "reason": warning})
                            dur = (time.time() - start) * 1000
                            self.messages.append({"role": "tool", "content": result})
                            yield ToolCallEnd(name, result, dur)
                            return
                    else:
                        # No confirm_fn — block by default for safety
                        result = f"Blocked: {warning} (no confirmation handler)"
                        self.permissions.denials.append({"tool": name, "reason": warning})
                        dur = (time.time() - start) * 1000
                        self.messages.append({"role": "tool", "content": result})
                        yield ToolCallEnd(name, result, dur)
                        return
                result = self._execute_tool(name, arguments)
        else:
            result = self._execute_tool(name, arguments)

        # Run post-hooks (notification only) — use cached hooks (M1)
        self._hooks.run_post_hooks(name, arguments, result)

        dur = (time.time() - start) * 1000
        # Truncate tool results stored in history to keep context manageable
        hist_result = result if len(result) <= 8000 else result[:8000] + "\n... [truncated for context]"
        self.messages.append({"role": "tool", "content": hist_result})

        if self._on_tool_call:
            self._on_tool_call(name, arguments)
        if self._on_tool_result:
            self._on_tool_result(name, result[:500])

        yield ToolCallEnd(name, result, dur)

    def _parse_tool_calls_from_text(self, text: str) -> list[tuple[str, dict]]:
        results = []
        for match in _TOOL_CALL_RE.finditer(text):
            name = match.group(1)
            if name in TOOL_REGISTRY:
                try:
                    args = json.loads(match.group(2))
                    results.append((name, args))
                except json.JSONDecodeError:
                    pass
        return results

    def _execute_tool(self, name: str, arguments: dict) -> str:
        handler = TOOL_REGISTRY.get(name)
        if handler is None:
            return f"Error: unknown tool '{name}'"
        try:
            result = handler(**arguments)
            text = str(result)
            if len(text) > 30_000:
                text = text[:30_000] + "\n... [truncated]"
            return text
        except Exception as exc:
            return f"Error running {name}: {exc}"
