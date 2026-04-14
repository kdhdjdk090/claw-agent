"""Diff tools — unified diffs, directory comparison."""

from __future__ import annotations

import difflib
import os
from pathlib import Path


def file_diff(file_a: str, file_b: str, context_lines: int = 3) -> str:
    """Generate a unified diff between two files.

    Args:
        file_a: Path to the original file.
        file_b: Path to the modified file.
        context_lines: Number of context lines around changes (default 3).
    """
    path_a = Path(file_a).expanduser().resolve()
    path_b = Path(file_b).expanduser().resolve()

    if not path_a.exists():
        return f"Error: File not found — {file_a}"
    if not path_b.exists():
        return f"Error: File not found — {file_b}"

    try:
        lines_a = path_a.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        lines_b = path_b.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    except Exception as exc:
        return f"Error reading files: {exc}"

    diff = difflib.unified_diff(
        lines_a, lines_b,
        fromfile=str(path_a),
        tofile=str(path_b),
        n=context_lines,
    )
    result = "".join(diff)
    if not result:
        return f"Files are identical: {path_a.name} == {path_b.name}"

    # Count changes
    added = sum(1 for line in result.splitlines() if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in result.splitlines() if line.startswith("-") and not line.startswith("---"))

    header = f"Diff: {path_a.name} → {path_b.name} (+{added} -{removed})\n\n"
    if len(result) > 15000:
        result = result[:15000] + "\n... (diff truncated)"
    return header + result


def compare_dirs(dir_a: str, dir_b: str, extensions: str = "") -> str:
    """Compare two directories — list files only in A, only in B, and common with differences.

    Args:
        dir_a: Path to first directory.
        dir_b: Path to second directory.
        extensions: Comma-separated filter (e.g. '.py,.js'). Empty = all files.
    """
    path_a = Path(dir_a).expanduser().resolve()
    path_b = Path(dir_b).expanduser().resolve()

    if not path_a.is_dir():
        return f"Error: Not a directory — {dir_a}"
    if not path_b.is_dir():
        return f"Error: Not a directory — {dir_b}"

    ext_filter = set()
    if extensions:
        for ext in extensions.split(","):
            ext = ext.strip()
            if not ext.startswith("."):
                ext = "." + ext
            ext_filter.add(ext.lower())

    def collect_files(base: Path) -> dict[str, Path]:
        files = {}
        for f in base.rglob("*"):
            if f.is_file():
                rel = f.relative_to(base).as_posix()
                if ext_filter and f.suffix.lower() not in ext_filter:
                    continue
                files[rel] = f
        return files

    files_a = collect_files(path_a)
    files_b = collect_files(path_b)

    only_a = sorted(set(files_a) - set(files_b))
    only_b = sorted(set(files_b) - set(files_a))
    common = sorted(set(files_a) & set(files_b))

    # Check common files for differences
    different = []
    identical = []
    for rel in common:
        try:
            content_a = files_a[rel].read_bytes()
            content_b = files_b[rel].read_bytes()
            if content_a != content_b:
                different.append(rel)
            else:
                identical.append(rel)
        except Exception:
            different.append(rel)

    lines = [
        f"Directory comparison:",
        f"  A: {path_a}",
        f"  B: {path_b}",
        f"  Filter: {extensions or 'all files'}",
        "",
        f"Only in A ({len(only_a)}):",
    ]
    for f in only_a[:50]:
        lines.append(f"  - {f}")
    if len(only_a) > 50:
        lines.append(f"  ... and {len(only_a) - 50} more")

    lines.append(f"\nOnly in B ({len(only_b)}):")
    for f in only_b[:50]:
        lines.append(f"  + {f}")
    if len(only_b) > 50:
        lines.append(f"  ... and {len(only_b) - 50} more")

    lines.append(f"\nDifferent ({len(different)}):")
    for f in different[:50]:
        lines.append(f"  ~ {f}")
    if len(different) > 50:
        lines.append(f"  ... and {len(different) - 50} more")

    lines.append(f"\nIdentical: {len(identical)} files")
    lines.append(f"Total: {len(files_a)} files in A, {len(files_b)} files in B")

    return "\n".join(lines)
