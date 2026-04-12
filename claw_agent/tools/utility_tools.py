"""Utility tools — sleep, config, powershell (ported from Rust crate)."""

from __future__ import annotations

import json
import os
import subprocess
import time


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
