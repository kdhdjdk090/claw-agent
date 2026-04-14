"""Browser tools — open URLs, basic web browsing capabilities."""

from __future__ import annotations

import webbrowser
import subprocess
from pathlib import Path


def open_browser(url: str) -> str:
    """Open a URL in the user's default web browser."""
    if not url.startswith(("http://", "https://", "file://")):
        url = "https://" + url
    try:
        webbrowser.open(url)
        return f"Opened in browser: {url}"
    except Exception as e:
        return f"Error opening browser: {e}"


def open_file_in_browser(file_path: str) -> str:
    """Open a local HTML file in the default browser."""
    p = Path(file_path).expanduser().resolve()
    if not p.exists():
        return f"File not found: {file_path}"
    if p.suffix.lower() not in (".html", ".htm", ".svg", ".pdf"):
        return f"Warning: {p.suffix} may not render in browser. Opening anyway."
    url = p.as_uri()
    try:
        webbrowser.open(url)
        return f"Opened in browser: {p.name}"
    except Exception as e:
        return f"Error: {e}"
