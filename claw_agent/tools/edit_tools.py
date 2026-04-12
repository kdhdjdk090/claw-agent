"""Edit tool — surgical string replacement in files."""

from __future__ import annotations

from pathlib import Path


def replace_in_file(path: str, old_string: str, new_string: str) -> str:
    """Replace an exact string in a file. old_string must appear exactly once."""
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return f"Error: file not found: {p}"
    if not p.is_file():
        return f"Error: not a file: {p}"

    content = p.read_text(encoding="utf-8", errors="replace")
    count = content.count(old_string)

    if count == 0:
        return "Error: old_string not found in file."
    if count > 1:
        return f"Error: old_string found {count} times — must be unique. Add more context."

    new_content = content.replace(old_string, new_string, 1)
    p.write_text(new_content, encoding="utf-8")
    return f"Replaced 1 occurrence in {p}"
