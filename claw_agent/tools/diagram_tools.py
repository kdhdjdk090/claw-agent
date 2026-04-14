"""Diagram tools — Mermaid diagram rendering/generation."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


MERMAID_EXAMPLES = {
    "flowchart": "flowchart TD\n    A[Start] --> B{Decision}\n    B -->|Yes| C[Do Thing]\n    B -->|No| D[Skip]\n    C --> E[End]\n    D --> E",
    "sequence": "sequenceDiagram\n    Alice->>Bob: Hello\n    Bob-->>Alice: Hi back\n    Alice->>Bob: How are you?\n    Bob-->>Alice: Great!",
    "class": "classDiagram\n    class Animal {\n        +String name\n        +makeSound()\n    }\n    class Dog {\n        +fetch()\n    }\n    Animal <|-- Dog",
    "state": "stateDiagram-v2\n    [*] --> Idle\n    Idle --> Running: start\n    Running --> Idle: stop\n    Running --> Error: fail\n    Error --> Idle: reset",
    "er": "erDiagram\n    USER ||--o{ ORDER : places\n    ORDER ||--|{ LINE_ITEM : contains\n    PRODUCT ||--o{ LINE_ITEM : includes",
    "gantt": "gantt\n    title Project Plan\n    dateFormat YYYY-MM-DD\n    section Phase 1\n    Design :a1, 2024-01-01, 30d\n    section Phase 2\n    Build :a2, after a1, 60d",
}


def render_mermaid(code: str, output_path: str = "", format: str = "svg") -> str:
    """Render a Mermaid diagram to SVG or PNG.

    Requires mmdc (mermaid-cli) installed globally:
        npm install -g @mermaid-js/mermaid-cli

    If mmdc is not available, returns the raw Mermaid code for manual rendering.
    """
    if format not in ("svg", "png", "pdf"):
        format = "svg"

    # Check if mmdc is available
    try:
        subprocess.run(["mmdc", "--version"], capture_output=True, timeout=5)
    except FileNotFoundError:
        return (
            f"mmdc (mermaid-cli) not found. Install with: npm install -g @mermaid-js/mermaid-cli\n\n"
            f"Raw Mermaid code:\n```mermaid\n{code}\n```"
        )

    # Write to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False, encoding="utf-8") as f:
        f.write(code)
        input_path = f.name

    if not output_path:
        output_path = str(Path(tempfile.gettempdir()) / f"diagram.{format}")

    try:
        r = subprocess.run(
            ["mmdc", "-i", input_path, "-o", output_path, "-f", format],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode == 0:
            return f"Diagram rendered to: {output_path}"
        return f"Render error: {r.stderr or r.stdout}"
    except Exception as e:
        return f"Error: {e}"
    finally:
        Path(input_path).unlink(missing_ok=True)


def mermaid_template(diagram_type: str = "flowchart") -> str:
    """Get a Mermaid diagram template. Types: flowchart, sequence, class, state, er, gantt."""
    template = MERMAID_EXAMPLES.get(diagram_type.lower())
    if template:
        return f"Mermaid {diagram_type} template:\n\n```mermaid\n{template}\n```"
    types = ", ".join(MERMAID_EXAMPLES.keys())
    return f"Unknown diagram type: {diagram_type}. Available: {types}"
