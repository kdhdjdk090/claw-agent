"""Documentation tools — extract signatures, generate docstrings, auto-README."""

from __future__ import annotations

import ast
import os
import re
from pathlib import Path


def extract_signatures(filepath: str) -> str:
    """Extract function/class signatures from a Python file.

    Returns a compact overview of all public callables.
    """
    path = Path(filepath).expanduser().resolve()
    if not path.exists():
        return f"File not found: {filepath}"
    if path.suffix != ".py":
        return f"Only Python files are supported (got {path.suffix})"

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        return f"Syntax error in {filepath}: {exc}"

    sigs: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
            args_str = _format_args(node.args)
            ret = ""
            if node.returns:
                ret = f" -> {ast.dump(node.returns)}"
            sigs.append(f"  {prefix}def {node.name}({args_str}){ret}")
        elif isinstance(node, ast.ClassDef):
            bases = ", ".join(ast.dump(b) for b in node.bases) if node.bases else ""
            sigs.append(f"  class {node.name}({bases})" if bases else f"  class {node.name}")

    if not sigs:
        return f"No functions or classes found in {filepath}"
    return f"Signatures in {path.name}:\n" + "\n".join(sigs)


def _format_args(args: ast.arguments) -> str:
    """Format function arguments into a compact string."""
    parts: list[str] = []
    defaults_offset = len(args.args) - len(args.defaults)
    for i, arg in enumerate(args.args):
        ann = f": {ast.dump(arg.annotation)}" if arg.annotation else ""
        default_idx = i - defaults_offset
        default = f"=..." if default_idx >= 0 and default_idx < len(args.defaults) else ""
        parts.append(f"{arg.arg}{ann}{default}")
    if args.vararg:
        parts.append(f"*{args.vararg.arg}")
    for kw in args.kwonlyargs:
        ann = f": {ast.dump(kw.annotation)}" if kw.annotation else ""
        parts.append(f"{kw.arg}{ann}")
    if args.kwarg:
        parts.append(f"**{args.kwarg.arg}")
    return ", ".join(parts)


def generate_docstring(filepath: str, function_name: str = "") -> str:
    """Generate a docstring template for a Python function or all functions in a file."""
    path = Path(filepath).expanduser().resolve()
    if not path.exists():
        return f"File not found: {filepath}"

    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return f"Syntax error: {exc}"

    results: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if function_name and node.name != function_name:
            continue

        existing = ast.get_docstring(node)
        if existing:
            if function_name:
                return f"{node.name} already has a docstring: {existing[:120]}..."
            continue

        args = [a.arg for a in node.args.args if a.arg != "self"]
        doc_lines = [f'    """{node.name}: TODO description.', ""]
        for a in args:
            doc_lines.append(f"    Args:")
            break
        for a in args:
            doc_lines.append(f"        {a}: TODO.")
        if node.returns:
            doc_lines.append("")
            doc_lines.append("    Returns:")
            doc_lines.append("        TODO.")
        doc_lines.append('    """')
        results.append(f"def {node.name}:\n" + "\n".join(doc_lines))

    if not results:
        return f"No un-docstringed functions found in {filepath}" + (
            f" matching '{function_name}'" if function_name else ""
        )
    return "Suggested docstrings:\n\n" + "\n\n".join(results)


def generate_readme(directory: str) -> str:
    """Generate a README.md skeleton from project structure and code analysis."""
    root = Path(directory).expanduser().resolve()
    if not root.is_dir():
        return f"Not a directory: {directory}"

    project_name = root.name

    # Detect language / framework
    indicators: dict[str, str] = {}
    if (root / "pyproject.toml").exists() or (root / "setup.py").exists():
        indicators["python"] = "Python"
    if (root / "package.json").exists():
        indicators["node"] = "Node.js"
    if (root / "go.mod").exists():
        indicators["go"] = "Go"
    if (root / "Cargo.toml").exists():
        indicators["rust"] = "Rust"

    tech = ", ".join(indicators.values()) or "Unknown"

    # Count source files
    exts = {".py": 0, ".js": 0, ".ts": 0, ".go": 0, ".rs": 0}
    for p in root.rglob("*"):
        if p.suffix in exts:
            exts[p.suffix] += 1
    file_stats = ", ".join(f"{ext}: {c}" for ext, c in exts.items() if c > 0) or "no source files"

    # Find entry points
    entries: list[str] = []
    for name in ("main.py", "__main__.py", "index.js", "index.ts", "main.go", "main.rs", "app.py"):
        if (root / name).exists() or any(root.rglob(name)):
            entries.append(name)

    readme = [
        f"# {project_name}",
        "",
        f"> Tech: {tech}",
        "",
        "## Overview",
        "",
        "TODO: Describe what this project does.",
        "",
        "## Project Structure",
        "",
        f"Source files: {file_stats}",
    ]
    if entries:
        readme.append(f"Entry points: {', '.join(entries)}")

    readme.extend([
        "",
        "## Installation",
        "",
        "```bash",
        "# TODO: installation steps",
        "```",
        "",
        "## Usage",
        "",
        "```bash",
        "# TODO: usage examples",
        "```",
        "",
        "## License",
        "",
        "TODO",
        "",
    ])

    return "\n".join(readme)
