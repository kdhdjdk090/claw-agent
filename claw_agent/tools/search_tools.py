"""Search tool — grep across files."""

from __future__ import annotations

import re
from pathlib import Path


def grep_search(pattern: str, directory: str = ".", include: str | None = None) -> str:
    """Search for a regex pattern in files under a directory."""
    root = Path(directory).expanduser().resolve()
    if not root.exists():
        return f"Error: directory not found: {root}"

    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        return f"Error: invalid regex: {e}"

    glob_pattern = include or "*"
    matches: list[str] = []
    max_matches = 200

    for filepath in root.rglob(glob_pattern):
        if not filepath.is_file():
            continue
        # Skip binary / hidden / common noise
        if any(part.startswith(".") for part in filepath.parts):
            continue
        if filepath.suffix in (".pyc", ".pyo", ".exe", ".dll", ".so", ".bin", ".lock"):
            continue

        try:
            text = filepath.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for i, line in enumerate(text.splitlines(), 1):
            if regex.search(line):
                rel = filepath.relative_to(root)
                matches.append(f"{rel}:{i}: {line.rstrip()}")
                if len(matches) >= max_matches:
                    matches.append(f"... (stopped at {max_matches} results)")
                    return "\n".join(matches)

    return "\n".join(matches) if matches else "No matches found."
