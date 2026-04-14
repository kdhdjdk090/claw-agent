"""Code intelligence tools — find references, rename symbols across codebase."""

from __future__ import annotations

import os
import re
from pathlib import Path

CODE_EXTS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".c", ".cpp", ".h", ".hpp",
    ".cs", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala", ".vue",
    ".svelte", ".html", ".css", ".scss", ".less", ".json", ".yaml", ".yml",
    ".toml", ".md", ".sql", ".sh", ".bash", ".ps1", ".bat",
}

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", "env",
    ".next", ".nuxt", "dist", "build", "target", ".tox", ".mypy_cache",
    ".pytest_cache", "coverage", ".cache", ".idea", ".vs",
}


def _iter_code_files(directory: str):
    """Yield code files, skipping ignored dirs."""
    root = Path(directory).expanduser().resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            fp = Path(dirpath) / fn
            if fp.suffix.lower() in CODE_EXTS:
                yield fp


def find_references(symbol: str, directory: str = ".", include_pattern: str = "") -> str:
    """Find all references to a symbol (function, class, variable) across codebase.

    Uses word-boundary matching so 'init' won't match 'initialize'.
    Returns file paths, line numbers, and context for each occurrence.
    """
    if not symbol or not symbol.strip():
        return "Error: symbol name is required."

    root = Path(directory).expanduser().resolve()
    if not root.is_dir():
        return f"Error: Not a directory — {directory}"

    pattern = re.compile(r'\b' + re.escape(symbol) + r'\b')
    results = []
    file_count = 0

    for fp in _iter_code_files(str(root)):
        if include_pattern:
            if not fp.match(include_pattern) and include_pattern not in str(fp):
                continue
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        file_count += 1
        matches_in_file = []

        for i, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                matches_in_file.append(f"  L{i}: {line.rstrip()}")

        if matches_in_file:
            rel = fp.relative_to(root) if fp.is_relative_to(root) else fp
            results.append(f"{rel} ({len(matches_in_file)} refs)")
            results.extend(matches_in_file[:20])
            if len(matches_in_file) > 20:
                results.append(f"  ... +{len(matches_in_file) - 20} more")

    if not results:
        return f"No references to '{symbol}' found in {file_count} files."

    total = sum(1 for r in results if r.startswith("  L"))
    header = f"References to '{symbol}': {total} occurrences across {len([r for r in results if not r.startswith('  ')])} files (searched {file_count} files)\n"
    return header + "\n".join(results)


def rename_symbol(
    old_name: str,
    new_name: str,
    directory: str = ".",
    include_pattern: str = "",
    dry_run: bool = True,
) -> str:
    """Rename a symbol across all code files in the workspace.

    Args:
        old_name: Current symbol name.
        new_name: New symbol name.
        directory: Root directory to search.
        include_pattern: Optional glob/substring filter for files.
        dry_run: If True (default), preview changes without writing. Set False to apply.
    """
    if not old_name or not new_name:
        return "Error: both old_name and new_name are required."
    if old_name == new_name:
        return "Error: old_name and new_name are identical."

    root = Path(directory).expanduser().resolve()
    if not root.is_dir():
        return f"Error: Not a directory — {directory}"

    pattern = re.compile(r'\b' + re.escape(old_name) + r'\b')
    changes = []

    for fp in _iter_code_files(str(root)):
        if include_pattern:
            if not fp.match(include_pattern) and include_pattern not in str(fp):
                continue
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        new_text, count = pattern.subn(new_name, text)
        if count > 0:
            rel = fp.relative_to(root) if fp.is_relative_to(root) else fp
            changes.append((fp, rel, count, new_text))

    if not changes:
        return f"No occurrences of '{old_name}' found."

    total = sum(c for _, _, c, _ in changes)
    lines = [f"{'[DRY RUN] ' if dry_run else ''}Rename '{old_name}' → '{new_name}': {total} replacements in {len(changes)} files\n"]

    for fp, rel, count, new_text in changes:
        lines.append(f"  {rel} — {count} replacement{'s' if count > 1 else ''}")
        if not dry_run:
            fp.write_text(new_text, encoding="utf-8")

    if dry_run:
        lines.append("\n⚠ Dry run — no files changed. Set dry_run=False to apply.")
    else:
        lines.append(f"\n✓ {total} replacements applied in {len(changes)} files.")

    return "\n".join(lines)
