"""Memory tools — persistent knowledge across sessions.

Three scopes:
  - user:    ~/.claw-agent/memories/       (survive all sessions)
  - session: ~/.claw-agent/memories/session/  (cleared per session)
  - repo:    <workspace>/.claw-agent/memories/ (per-project)
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

MEMORY_ROOT = Path.home() / ".claw-agent" / "memories"


def _resolve(path: str, workspace: str = ".") -> Path:
    """Resolve a memory path to the real filesystem path."""
    clean = path.strip("/").removeprefix("memories").strip("/")
    if clean.startswith("repo/"):
        return Path(workspace).resolve() / ".claw-agent" / "memories" / clean[5:]
    return MEMORY_ROOT / clean


def memory_view(path: str = "/memories/", workspace: str = ".") -> str:
    """View contents of a memory file or list a directory."""
    target = _resolve(path, workspace)
    if target.is_dir():
        entries = []
        for item in sorted(target.iterdir()):
            name = item.name + ("/" if item.is_dir() else "")
            entries.append(name)
        return "\n".join(entries) if entries else "(empty directory)"
    if target.is_file():
        return target.read_text(encoding="utf-8")
    return f"Not found: {path}"


def memory_create(path: str, content: str, workspace: str = ".") -> str:
    """Create a new memory file. Fails if it already exists."""
    target = _resolve(path, workspace)
    if target.exists():
        return f"Error: {path} already exists. Use memory_update to modify."
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Created: {path} ({len(content)} chars)"


def memory_update(path: str, old_str: str, new_str: str, workspace: str = ".") -> str:
    """Replace exact text in a memory file (must match exactly once)."""
    target = _resolve(path, workspace)
    if not target.is_file():
        return f"Error: {path} not found"
    text = target.read_text(encoding="utf-8")
    count = text.count(old_str)
    if count == 0:
        return "Error: old_str not found in file"
    if count > 1:
        return f"Error: old_str found {count} times (must be unique)"
    text = text.replace(old_str, new_str, 1)
    target.write_text(text, encoding="utf-8")
    return f"Updated: {path}"


def memory_insert(path: str, line: int, text: str, workspace: str = ".") -> str:
    """Insert text at a specific line (0-based). 0 = beginning."""
    target = _resolve(path, workspace)
    if not target.is_file():
        return f"Error: {path} not found"
    lines = target.read_text(encoding="utf-8").splitlines(keepends=True)
    line = max(0, min(line, len(lines)))
    lines.insert(line, text if text.endswith("\n") else text + "\n")
    target.write_text("".join(lines), encoding="utf-8")
    return f"Inserted at line {line} in {path}"


def memory_delete(path: str, workspace: str = ".") -> str:
    """Delete a memory file or directory."""
    target = _resolve(path, workspace)
    if not target.exists():
        return f"Not found: {path}"
    if target.is_dir():
        shutil.rmtree(target)
        return f"Deleted directory: {path}"
    target.unlink()
    return f"Deleted: {path}"


def memory_rename(old_path: str, new_path: str, workspace: str = ".") -> str:
    """Rename/move a memory file or directory within the same scope."""
    src = _resolve(old_path, workspace)
    dst = _resolve(new_path, workspace)
    if not src.exists():
        return f"Not found: {old_path}"
    if dst.exists():
        return f"Error: {new_path} already exists"
    dst.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dst)
    return f"Renamed: {old_path} → {new_path}"


def memory(command: str, path: str = "/memories/", content: str = "",
           old_str: str = "", new_str: str = "", line: int = 0,
           text: str = "", old_path: str = "", new_path: str = "",
           workspace: str = ".") -> str:
    """Unified memory tool — persistent notes across sessions.

    Commands: view, create, str_replace, insert, delete, rename
    Scopes: /memories/ (user), /memories/session/ (temp), /memories/repo/ (project)
    """
    cmd = command.lower().strip()
    if cmd == "view":
        return memory_view(path, workspace)
    elif cmd == "create":
        return memory_create(path, content, workspace)
    elif cmd == "str_replace":
        return memory_update(path, old_str, new_str, workspace)
    elif cmd == "insert":
        return memory_insert(path, line, text, workspace)
    elif cmd == "delete":
        return memory_delete(path, workspace)
    elif cmd == "rename":
        return memory_rename(old_path, new_path, workspace)
    else:
        return f"Unknown command: {command}. Use: view, create, str_replace, insert, delete, rename"
