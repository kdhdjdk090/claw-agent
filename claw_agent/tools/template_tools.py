"""Template tools — lightweight string-template rendering."""

from __future__ import annotations

import re
from pathlib import Path


_VAR_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def tpl_render(template: str, variables: str) -> str:
    """Render a string template by substituting ``{{ var }}`` placeholders.

    Parameters
    ----------
    template : str
        Template string with ``{{ varname }}`` placeholders.
    variables : str
        JSON-encoded dict of variable→value mappings.
    """
    import json

    try:
        vmap = json.loads(variables)
    except json.JSONDecodeError as exc:
        return f"Invalid JSON for variables: {exc}"

    if not isinstance(vmap, dict):
        return "Variables must be a JSON object (dict)."

    def _sub(m: re.Match) -> str:
        key = m.group(1)
        return str(vmap.get(key, m.group(0)))

    result = _VAR_RE.sub(_sub, template)

    missing = [k for k in _VAR_RE.findall(result)]
    note = ""
    if missing:
        note = f"\n\n⚠ Un-substituted placeholders: {', '.join(missing)}"
    return result + note


def tpl_list_vars(template: str) -> str:
    """Extract all ``{{ var }}`` placeholder names from a template string."""
    matches = _VAR_RE.findall(template)
    if not matches:
        return "No {{ var }} placeholders found in the template."
    unique = list(dict.fromkeys(matches))
    return f"Found {len(unique)} variable(s):\n" + "\n".join(f"  • {v}" for v in unique)


def tpl_render_file(template_path: str, variables: str, output_path: str = "") -> str:
    """Read a template file, substitute variables, and optionally write the result.

    Parameters
    ----------
    template_path : str
        Path to the template file.
    variables : str
        JSON-encoded dict of variable→value mappings.
    output_path : str
        If provided, write the rendered result here.  Otherwise return it.
    """
    import json

    tp = Path(template_path).expanduser().resolve()
    if not tp.exists():
        return f"Template file not found: {template_path}"

    text = tp.read_text(encoding="utf-8")

    try:
        vmap = json.loads(variables)
    except json.JSONDecodeError as exc:
        return f"Invalid JSON for variables: {exc}"
    if not isinstance(vmap, dict):
        return "Variables must be a JSON object (dict)."

    def _sub(m: re.Match) -> str:
        key = m.group(1)
        return str(vmap.get(key, m.group(0)))

    result = _VAR_RE.sub(_sub, text)

    if output_path:
        op = Path(output_path).expanduser().resolve()
        op.parent.mkdir(parents=True, exist_ok=True)
        op.write_text(result, encoding="utf-8")
        return f"Rendered template written to {op}"

    if len(result) > 12_000:
        return result[:12_000] + f"\n\n... (truncated, total {len(result)} chars)"
    return result
