"""Utility tools — sleep, config, powershell, ask_user, tool_search."""

from __future__ import annotations

import json
import os
import subprocess
import time
from typing import Callable

# Global ask-user callback set by CLI so the tool can prompt interactively.
# Falls back to stdin if not set (works in non-interactive/pipe mode).
_ASK_USER_FN: Callable[[str, list[str]], str] | None = None


def register_ask_user_fn(fn: Callable[[str, list[str]], str]) -> None:
    """Register the user-input callback used by ask_user()."""
    global _ASK_USER_FN
    _ASK_USER_FN = fn


def sleep_tool(seconds: int = 5) -> str:
    """Pause execution for a specified duration. Useful for polling or waiting."""
    seconds = min(max(1, seconds), 60)  # clamp 1–60
    time.sleep(seconds)
    return f"Slept for {seconds} seconds."


def config_get(key: str | None = None) -> str:
    """Read agent configuration. Returns all config or a specific key."""
    config_path = os.path.join(os.path.expanduser("~"), ".claw-agent", "config.json")
    if not os.path.exists(config_path):
        return json.dumps({"model": "deepseek-v3.1:671b-cloud", "base_url": "http://localhost:11434"}, indent=2)
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    if key:
        return json.dumps({key: config.get(key, "(not set)")}, indent=2)
    return json.dumps(config, indent=2)


def config_set(key: str, value: str) -> str:
    """Set an agent configuration value. Persisted to ~/.claw-agent/config.json."""
    config_dir = os.path.join(os.path.expanduser("~"), ".claw-agent")
    config_path = os.path.join(config_dir, "config.json")
    os.makedirs(config_dir, exist_ok=True)
    config: dict = {}
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    config[key] = value
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    return f"Set {key} = {value}"


def ask_user(question: str, options: list[str] | None = None) -> str:
    """Ask the user a clarifying question and return their answer.
    
    Use this when you genuinely need user input to proceed — for example,
    when choosing between multiple valid approaches or confirming a destructive action.
    Do NOT use to ask about file contents; read them yourself.
    
    options: optional list of suggested answers (shown as numbered choices).
    """
    global _ASK_USER_FN
    if _ASK_USER_FN is not None:
        return _ASK_USER_FN(question, options or [])
    # Fallback: plain stdin read (for non-interactive / piped mode)
    prompt = question
    if options:
        choices = "\n".join(f"  {i+1}. {o}" for i, o in enumerate(options))
        prompt = f"{question}\n{choices}"
    try:
        print(f"\n❓ {prompt}\n> ", end="", flush=True)
        answer = input()
        return answer.strip() or "(no answer)"
    except (EOFError, KeyboardInterrupt):
        return "(user cancelled)"


def tool_search(query: str) -> str:
    """Search available tools by name or description.
    
    Returns a list of matching tool names and their descriptions.
    Use this to discover what tools are available before deciding which to use.
    """
    from ..tools import TOOL_REGISTRY, OLLAMA_TOOL_DEFINITIONS
    query_lower = query.strip().lower()
    # Build name→description map from tool definitions
    desc_map: dict[str, str] = {}
    for td in OLLAMA_TOOL_DEFINITIONS:
        fn = td.get("function", {})
        name = fn.get("name", "")
        desc = fn.get("description", "")
        if name:
            desc_map[name] = desc
    results = []
    for name in sorted(TOOL_REGISTRY.keys()):
        desc = desc_map.get(name, "")
        if query_lower in name.lower() or query_lower in desc.lower():
            results.append(f"  {name}: {desc}")
    if not results:
        return f"No tools matched '{query}'. Available tools: {', '.join(sorted(TOOL_REGISTRY.keys()))}"
    return f"Tools matching '{query}' ({len(results)}):\n" + "\n".join(results)


def powershell(command: str, cwd: str | None = None) -> str:
    """Execute a PowerShell command. Only works on Windows. 120s timeout."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True,
            timeout=120,
            cwd=cwd or None,
        )
        stdout = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
        stderr = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
        output = ""
        if stdout:
            output += stdout
        if stderr:
            output += stderr
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"
        return output.strip() or "(no output)"
    except FileNotFoundError:
        return "Error: PowerShell is not available on this system."
    except subprocess.TimeoutExpired:
        return "Error: PowerShell command timed out after 120 seconds."
    except Exception as exc:
        return f"Error: {exc}"
