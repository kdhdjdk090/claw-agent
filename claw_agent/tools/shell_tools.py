"""Shell tool — run commands locally."""

from __future__ import annotations

import os
import subprocess
import sys


def run_command(command: str, cwd: str | None = None) -> str:
    """Execute a shell command with a 120-second timeout.

    On Windows uses cmd.exe (shell=True default).
    Handles surrogate characters in output gracefully.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            timeout=120,
            cwd=cwd or None,
        )
        # Decode with surrogate handling to avoid UnicodeEncodeError
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
    except subprocess.TimeoutExpired:
        return "Error: command timed out after 120 seconds."
    except Exception as exc:
        return f"Error: {exc}"
