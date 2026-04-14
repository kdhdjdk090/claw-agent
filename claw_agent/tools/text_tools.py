"""Text tools — word count, markdown→HTML, template rendering."""

from __future__ import annotations

import html
import os
import re
import string
from pathlib import Path


def word_count(text_or_file: str) -> str:
    """Count words, lines, characters, and sentences in text or a file.

    Args:
        text_or_file: Raw text string or path to a text file.
    """
    path = Path(text_or_file).expanduser().resolve()
    if path.exists() and path.is_file():
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            source = path.name
        except Exception as exc:
            return f"Error reading file: {exc}"
    else:
        text = text_or_file
        source = "input"

    lines = text.splitlines()
    words = text.split()
    chars = len(text)
    chars_no_space = len(text.replace(" ", "").replace("\t", "").replace("\n", ""))
    sentences = len(re.findall(r"[.!?]+", text))
    paragraphs = len([p for p in re.split(r"\n\s*\n", text) if p.strip()])

    # Reading time (~200 WPM)
    read_min = max(1, round(len(words) / 200))

    return (
        f"Text stats ({source}):\n"
        f"  Words:      {len(words):,}\n"
        f"  Lines:      {len(lines):,}\n"
        f"  Characters: {chars:,} (no spaces: {chars_no_space:,})\n"
        f"  Sentences:  {sentences:,}\n"
        f"  Paragraphs: {paragraphs:,}\n"
        f"  Reading:    ~{read_min} min"
    )


def markdown_to_html(markdown_text: str) -> str:
    """Convert Markdown text to HTML.

    Supports headers, bold, italic, code blocks, links, lists, and blockquotes.
    Uses Python-Markdown if available, otherwise a basic regex converter.
    """
    # Try python-markdown first
    try:
        import markdown
        result = markdown.markdown(
            markdown_text,
            extensions=["fenced_code", "tables", "nl2br", "sane_lists"],
        )
        return result
    except ImportError:
        pass

    # Basic regex-based converter
    text = markdown_text

    # Fenced code blocks
    text = re.sub(r"```(\w*)\n(.*?)```", r"<pre><code>\2</code></pre>", text, flags=re.DOTALL)

    # Headers
    text = re.sub(r"^######\s+(.+)$", r"<h6>\1</h6>", text, flags=re.MULTILINE)
    text = re.sub(r"^#####\s+(.+)$", r"<h5>\1</h5>", text, flags=re.MULTILINE)
    text = re.sub(r"^####\s+(.+)$", r"<h4>\1</h4>", text, flags=re.MULTILINE)
    text = re.sub(r"^###\s+(.+)$", r"<h3>\1</h3>", text, flags=re.MULTILINE)
    text = re.sub(r"^##\s+(.+)$", r"<h2>\1</h2>", text, flags=re.MULTILINE)
    text = re.sub(r"^#\s+(.+)$", r"<h1>\1</h1>", text, flags=re.MULTILINE)

    # Bold and italic
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)

    # Inline code
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)

    # Links
    text = re.sub(r"\[([^\]]+)\]\(([^\)]+)\)", r'<a href="\2">\1</a>', text)

    # Blockquotes
    text = re.sub(r"^>\s+(.+)$", r"<blockquote>\1</blockquote>", text, flags=re.MULTILINE)

    # Horizontal rule
    text = re.sub(r"^---+$", "<hr>", text, flags=re.MULTILINE)

    # Line breaks → paragraphs
    text = re.sub(r"\n\n+", "</p><p>", text)
    text = f"<p>{text}</p>"
    text = text.replace("<p></p>", "")

    return text


def render_template(template: str, variables: str = "{}") -> str:
    """Render a simple string template with variable substitution.

    Uses Python format-style placeholders: {name}, {count}, etc.
    Variables are passed as a JSON object string.

    Args:
        template: Template string with {placeholder} markers.
        variables: JSON string of key-value pairs, e.g. '{"name": "World", "count": 42}'
    """
    import json

    try:
        vars_dict = json.loads(variables)
    except json.JSONDecodeError as exc:
        return f"Error parsing variables JSON: {exc}"

    if not isinstance(vars_dict, dict):
        return "Error: Variables must be a JSON object (dict)"

    try:
        result = template.format(**vars_dict)
        return result
    except KeyError as exc:
        available = ", ".join(vars_dict.keys())
        return f"Error: Missing variable {exc}. Available: {available}"
    except Exception as exc:
        return f"Error rendering template: {exc}"
