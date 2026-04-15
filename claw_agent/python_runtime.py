"""Helpers for launching the current Python runtime reliably."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def get_python_executable() -> str:
    """Return the best Python executable for subprocess-based tools."""
    candidates: list[str] = []

    if sys.executable:
        candidates.append(sys.executable)

    python_on_path = shutil.which("python")
    if python_on_path:
        candidates.append(python_on_path)

    for candidate in candidates:
        if not candidate:
            continue
        try:
            if Path(candidate).exists():
                return candidate
        except OSError:
            continue

    return sys.executable or "python"


def python_command(*args: str) -> list[str]:
    """Build a subprocess command that uses the active Python interpreter."""
    return [get_python_executable(), *args]
