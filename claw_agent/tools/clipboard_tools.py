"""System clipboard tools — copy and read clipboard content."""

from __future__ import annotations

import subprocess
import sys


def clipboard_copy(text: str) -> str:
    """Copy text to the system clipboard.

    Args:
        text: The text to copy.
    """
    if not text:
        return "Error: nothing to copy — text is empty."

    try:
        if sys.platform == "win32":
            process = subprocess.Popen(
                ["clip"],
                stdin=subprocess.PIPE,
                timeout=5,
            )
            process.communicate(input=text.encode("utf-16le"))
            if process.returncode == 0:
                preview = text[:120] + ("…" if len(text) > 120 else "")
                return f"✅ Copied {len(text):,} chars to clipboard.\nPreview: {preview}"
            return "❌ clip command failed."

        elif sys.platform == "darwin":
            process = subprocess.Popen(
                ["pbcopy"],
                stdin=subprocess.PIPE,
                timeout=5,
            )
            process.communicate(input=text.encode("utf-8"))
            if process.returncode == 0:
                preview = text[:120] + ("…" if len(text) > 120 else "")
                return f"✅ Copied {len(text):,} chars to clipboard.\nPreview: {preview}"
            return "❌ pbcopy failed."

        else:
            for cmd in (["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]):
                try:
                    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, timeout=5)
                    process.communicate(input=text.encode("utf-8"))
                    if process.returncode == 0:
                        preview = text[:120] + ("…" if len(text) > 120 else "")
                        return f"✅ Copied {len(text):,} chars to clipboard.\nPreview: {preview}"
                except FileNotFoundError:
                    continue
            return "❌ No clipboard tool found. Install xclip or xsel."

    except Exception as e:
        return f"Error copying to clipboard: {type(e).__name__}: {e}"


def clipboard_read() -> str:
    """Read the current contents of the system clipboard."""
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["powershell", "-Command", "Get-Clipboard"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            content = result.stdout
        elif sys.platform == "darwin":
            result = subprocess.run(
                ["pbpaste"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            content = result.stdout
        else:
            for cmd in (["xclip", "-selection", "clipboard", "-o"], ["xsel", "--clipboard", "--output"]):
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        content = result.stdout
                        break
                except FileNotFoundError:
                    continue
            else:
                return "❌ No clipboard tool found. Install xclip or xsel."

        if not content or not content.strip():
            return "Clipboard is empty."

        if len(content) > 10_000:
            return f"Clipboard ({len(content):,} chars, truncated):\n{content[:10000]}…"
        return f"Clipboard ({len(content):,} chars):\n{content}"

    except Exception as e:
        return f"Error reading clipboard: {type(e).__name__}: {e}"
