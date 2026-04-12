"""File system tools — read, write, list, find."""

from __future__ import annotations

import os
from pathlib import Path


def read_file(path: str, start_line: int | None = None, end_line: int | None = None) -> str:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return f"Error: file not found: {p}"
    if not p.is_file():
        return f"Error: not a file: {p}"

    lines = p.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)

    if start_line is not None or end_line is not None:
        s = (start_line or 1) - 1
        e = end_line or len(lines)
        lines = lines[s:e]

    return "".join(lines)


def write_file(path: str, content: str) -> str:
    p = Path(path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} bytes to {p}"


def list_directory(path: str = ".") -> str:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return f"Error: directory not found: {p}"
    if not p.is_dir():
        return f"Error: not a directory: {p}"

    entries = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
    lines = []
    for entry in entries:
        name = entry.name + ("/" if entry.is_dir() else "")
        lines.append(name)
    return "\n".join(lines) if lines else "(empty directory)"


def find_files(pattern: str, directory: str = ".") -> str:
    p = Path(directory).expanduser().resolve()
    if not p.exists():
        return f"Error: directory not found: {p}"

    matches = sorted(str(m.relative_to(p)) for m in p.glob(pattern) if m.is_file())
    if not matches:
        return "No files matched."
    # Cap at 200 results
    if len(matches) > 200:
        matches = matches[:200]
        matches.append(f"... and more (showing first 200)")
    return "\n".join(matches)
