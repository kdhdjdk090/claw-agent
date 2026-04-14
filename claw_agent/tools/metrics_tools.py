"""Metrics tools — code metrics, LOC, complexity, file stats."""

from __future__ import annotations

import ast
import os
from pathlib import Path

# Language extension mapping
LANG_MAP = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript", ".jsx": "JSX",
    ".tsx": "TSX", ".java": "Java", ".kt": "Kotlin", ".go": "Go", ".rs": "Rust",
    ".c": "C", ".cpp": "C++", ".h": "C/C++ Header", ".cs": "C#", ".rb": "Ruby",
    ".php": "PHP", ".swift": "Swift", ".r": "R", ".scala": "Scala",
    ".html": "HTML", ".css": "CSS", ".scss": "SCSS", ".json": "JSON",
    ".yaml": "YAML", ".yml": "YAML", ".xml": "XML", ".md": "Markdown",
    ".sql": "SQL", ".sh": "Shell", ".ps1": "PowerShell", ".bat": "Batch",
    ".toml": "TOML", ".lua": "Lua", ".dart": "Dart", ".vue": "Vue",
    ".svelte": "Svelte",
}

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
             ".tox", ".mypy_cache", ".pytest_cache", "target", ".next", ".nuxt"}


def count_lines(directory: str = ".", include: str = "", exclude_dirs: str = "") -> str:
    """Count lines of code by language.

    Args:
        directory: Root directory to scan.
        include: Comma-separated extensions to include (blank = all known).
        exclude_dirs: Extra directories to skip (comma-separated).
    """
    root = Path(directory).expanduser().resolve()
    if not root.is_dir():
        return f"Error: Not a directory — {directory}"

    inc_exts = set()
    if include:
        inc_exts = {e.strip().lower() if e.strip().startswith(".") else f".{e.strip().lower()}" for e in include.split(",")}

    extra_skip = set()
    if exclude_dirs:
        extra_skip = {d.strip() for d in exclude_dirs.split(",")}
    skip = SKIP_DIRS | extra_skip

    stats: dict[str, dict] = {}  # lang -> {files, code, blank, comment}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip]
        for fname in filenames:
            ext = Path(fname).suffix.lower()
            if inc_exts and ext not in inc_exts:
                continue
            lang = LANG_MAP.get(ext)
            if not lang:
                continue
            fp = Path(dirpath) / fname
            try:
                lines = fp.read_text(encoding="utf-8", errors="replace").splitlines()
                code = blank = comment = 0
                for line in lines:
                    stripped = line.strip()
                    if not stripped:
                        blank += 1
                    elif stripped.startswith(("#", "//", "/*", "*", "<!--")):
                        comment += 1
                    else:
                        code += 1
                if lang not in stats:
                    stats[lang] = {"files": 0, "code": 0, "blank": 0, "comment": 0}
                stats[lang]["files"] += 1
                stats[lang]["code"] += code
                stats[lang]["blank"] += blank
                stats[lang]["comment"] += comment
            except Exception:
                continue

    if not stats:
        return f"No source files found in {root.name}/"

    # Sort by code lines descending
    sorted_langs = sorted(stats.items(), key=lambda x: x[1]["code"], reverse=True)
    total = {"files": 0, "code": 0, "blank": 0, "comment": 0}
    rows = []
    for lang, s in sorted_langs:
        rows.append(f"  {lang:<18} {s['files']:>5} files  {s['code']:>7} code  {s['blank']:>6} blank  {s['comment']:>6} comment")
        for k in total:
            total[k] += s[k]

    header = f"Lines of code — {root.name}/\n{'=' * 70}"
    footer = f"\n{'─' * 70}\n  {'TOTAL':<18} {total['files']:>5} files  {total['code']:>7} code  {total['blank']:>6} blank  {total['comment']:>6} comment"
    return header + "\n" + "\n".join(rows) + footer


def code_complexity(file_path: str) -> str:
    """Compute cyclomatic complexity for a Python file.

    Args:
        file_path: Path to a .py file.
    """
    fp = Path(file_path).expanduser().resolve()
    if not fp.is_file():
        return f"Error: File not found — {file_path}"
    if fp.suffix != ".py":
        return "Error: Only Python files (.py) supported."

    try:
        source = fp.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(fp))
    except SyntaxError as e:
        return f"Syntax error: {e}"

    results = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            complexity = _calc_complexity(node)
            rating = "low" if complexity <= 5 else "moderate" if complexity <= 10 else "high" if complexity <= 20 else "very high"
            results.append((node.name, node.lineno, complexity, rating))

    if not results:
        return f"{fp.name}: No functions found."

    results.sort(key=lambda x: x[2], reverse=True)
    lines = [f"Cyclomatic complexity — {fp.name}\n"]
    for name, lineno, cc, rating in results:
        indicator = "✓" if cc <= 10 else "⚠" if cc <= 20 else "✗"
        lines.append(f"  {indicator} {name} (line {lineno}): {cc} ({rating})")

    avg = sum(r[2] for r in results) / len(results)
    lines.append(f"\nAverage: {avg:.1f}  |  Functions: {len(results)}")
    return "\n".join(lines)


def file_type_stats(directory: str = ".") -> str:
    """Show file type distribution in a directory.

    Args:
        directory: Root directory to scan.
    """
    root = Path(directory).expanduser().resolve()
    if not root.is_dir():
        return f"Error: Not a directory — {directory}"

    ext_counts: dict[str, int] = {}
    ext_sizes: dict[str, int] = {}
    total_files = 0

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            ext = Path(fname).suffix.lower() or "(no ext)"
            fp = Path(dirpath) / fname
            try:
                size = fp.stat().st_size
            except OSError:
                size = 0
            ext_counts[ext] = ext_counts.get(ext, 0) + 1
            ext_sizes[ext] = ext_sizes.get(ext, 0) + size
            total_files += 1

    if not ext_counts:
        return f"No files found in {root.name}/"

    sorted_exts = sorted(ext_counts.items(), key=lambda x: x[1], reverse=True)
    lines = [f"File types — {root.name}/ ({total_files} files)\n"]
    for ext, count in sorted_exts[:30]:
        size_kb = ext_sizes[ext] / 1024
        lang = LANG_MAP.get(ext, "")
        lang_str = f" ({lang})" if lang else ""
        lines.append(f"  {ext:<10}{lang_str:<20} {count:>5} files  {size_kb:>8.1f} KB")

    return "\n".join(lines)


# ---- Internals ----

def _calc_complexity(node: ast.AST) -> int:
    """Count decision points in an AST node."""
    cc = 1  # Base complexity
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
            cc += 1
        elif isinstance(child, ast.ExceptHandler):
            cc += 1
        elif isinstance(child, ast.BoolOp):
            cc += len(child.values) - 1
        elif isinstance(child, ast.Assert):
            cc += 1
        elif isinstance(child, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            cc += 1
    return cc
