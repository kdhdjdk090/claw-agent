"""Enhanced file editing — multi-line atomic edits, patch application."""

from __future__ import annotations

import difflib
from pathlib import Path


def multi_edit_file(path: str, edits: str) -> str:
    """Apply multiple edits to a file atomically.
    
    edits format: JSON array of {"old": "...", "new": "..."} objects.
    All edits must match exactly or none are applied.
    """
    import json

    p = Path(path).expanduser().resolve()
    if not p.exists():
        return f"Error: file not found: {p}"

    try:
        edit_list = json.loads(edits)
    except json.JSONDecodeError as e:
        return f"Error: invalid JSON in edits: {e}"

    content = p.read_text(encoding="utf-8", errors="replace")

    # Validate all edits first
    for i, edit in enumerate(edit_list):
        old = edit.get("old", "")
        if not old:
            return f"Error: edit {i} has empty 'old' string"
        count = content.count(old)
        if count == 0:
            return f"Error: edit {i} 'old' string not found in file"
        if count > 1:
            return f"Error: edit {i} 'old' string found {count} times — must be unique"

    # Apply all edits
    for edit in edit_list:
        content = content.replace(edit["old"], edit.get("new", ""), 1)

    p.write_text(content, encoding="utf-8")
    return f"Applied {len(edit_list)} edits to {p}"


def insert_at_line(path: str, line_number: int, text: str) -> str:
    """Insert text at a specific line number (1-based)."""
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return f"Error: file not found: {p}"

    lines = p.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)

    idx = max(0, min(line_number - 1, len(lines)))
    if not text.endswith("\n"):
        text += "\n"
    lines.insert(idx, text)

    p.write_text("".join(lines), encoding="utf-8")
    return f"Inserted at line {line_number} in {p}"


def diff_files(path_a: str, path_b: str) -> str:
    """Show unified diff between two files."""
    a = Path(path_a).expanduser().resolve()
    b = Path(path_b).expanduser().resolve()

    if not a.exists():
        return f"Error: {a} not found"
    if not b.exists():
        return f"Error: {b} not found"

    a_lines = a.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    b_lines = b.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)

    diff = difflib.unified_diff(a_lines, b_lines, fromfile=str(a), tofile=str(b))
    result = "".join(diff)
    return result if result else "Files are identical."
