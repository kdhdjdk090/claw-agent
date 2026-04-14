"""Snippet tools — save, load, and search reusable code snippets."""

from __future__ import annotations

import json
import time
from pathlib import Path

_SNIPPET_DIR = Path.home() / ".claw" / "snippets"


def _ensure_dir() -> Path:
    _SNIPPET_DIR.mkdir(parents=True, exist_ok=True)
    return _SNIPPET_DIR


def save_snippet(name: str, code: str, language: str = "", tags: str = "") -> str:
    """Save a named code snippet for later reuse.

    Parameters
    ----------
    name : str
        Unique identifier for the snippet (alphanumeric + hyphens/underscores).
    code : str
        The snippet content.
    language : str
        Programming language label (e.g. ``python``, ``javascript``).
    tags : str
        Comma-separated tags for searchability.
    """
    import re as _re

    if not _re.match(r"^[\w-]+$", name):
        return "Name must contain only letters, digits, hyphens, or underscores."

    d = _ensure_dir()
    fp = d / f"{name}.json"
    payload = {
        "name": name,
        "language": language.strip().lower() or "text",
        "tags": [t.strip().lower() for t in tags.split(",") if t.strip()],
        "code": code,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    fp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return f"Snippet '{name}' saved ({len(code)} chars, lang={payload['language']})"


def load_snippet(name: str) -> str:
    """Retrieve a previously saved snippet by name."""
    fp = _ensure_dir() / f"{name}.json"
    if not fp.exists():
        return f"Snippet '{name}' not found."
    try:
        data = json.loads(fp.read_text(encoding="utf-8"))
        hdr = f"# Snippet: {data['name']}  (lang={data.get('language','?')})\n"
        hdr += f"# Tags: {', '.join(data.get('tags', []))}\n"
        hdr += f"# Saved: {data.get('created','?')}\n\n"
        return hdr + data.get("code", "")
    except (json.JSONDecodeError, KeyError) as exc:
        return f"Error reading snippet: {exc}"


def search_snippets(query: str) -> str:
    """Search saved snippets by name, language, or tag (case-insensitive).

    Parameters
    ----------
    query : str
        Search term matched against snippet names, language, and tags.
    """
    d = _ensure_dir()
    q = query.lower()
    hits: list[str] = []

    for fp in sorted(d.glob("*.json")):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        searchable = " ".join([
            data.get("name", ""),
            data.get("language", ""),
            " ".join(data.get("tags", [])),
            data.get("code", "")[:200],
        ]).lower()

        if q in searchable:
            lang = data.get("language", "?")
            tags = ", ".join(data.get("tags", [])) or "none"
            lines = data.get("code", "").count("\n") + 1
            hits.append(f"  • {data['name']}  [lang={lang}]  tags=[{tags}]  {lines} lines")

    if not hits:
        return f"No snippets matching '{query}'."
    return f"Found {len(hits)} snippet(s):\n" + "\n".join(hits[:30])
