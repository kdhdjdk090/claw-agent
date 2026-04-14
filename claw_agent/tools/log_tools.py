"""Log tools — log parsing, tailing, and pattern search."""

from __future__ import annotations

import re
from pathlib import Path


def parse_log(file_path: str, level: str = "", pattern: str = "", last_n: int = 100) -> str:
    """Parse a log file with optional level and pattern filters.

    Args:
        file_path: Path to the log file.
        level: Filter by log level (e.g., ERROR, WARN, INFO, DEBUG).
        pattern: Regex pattern to match lines.
        last_n: Max lines to return (default 100).
    """
    fp = Path(file_path).expanduser().resolve()
    if not fp.is_file():
        return f"Error: File not found — {file_path}"

    try:
        lines = fp.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as e:
        return f"Error reading file: {e}"

    filtered = lines
    if level:
        lvl = level.upper()
        filtered = [l for l in filtered if lvl in l.upper()]
    if pattern:
        try:
            rx = re.compile(pattern, re.IGNORECASE)
            filtered = [l for l in filtered if rx.search(l)]
        except re.error as e:
            return f"Error: Bad regex — {e}"

    total = len(filtered)
    shown = filtered[-last_n:]
    header = f"Log: {fp.name} — {total} matching lines"
    if total > last_n:
        header += f" (showing last {last_n})"
    return header + "\n\n" + "\n".join(shown)


def tail_file(file_path: str, lines: int = 50) -> str:
    """Return the last N lines of a file.

    Args:
        file_path: Path to the file.
        lines: Number of lines to return (default 50, max 500).
    """
    fp = Path(file_path).expanduser().resolve()
    if not fp.is_file():
        return f"Error: File not found — {file_path}"

    n = min(max(lines, 1), 500)
    try:
        all_lines = fp.read_text(encoding="utf-8", errors="replace").splitlines()
        tail = all_lines[-n:]
        header = f"Last {len(tail)} lines of {fp.name}"
        if len(all_lines) > n:
            header += f" ({len(all_lines)} total)"
        return header + "\n\n" + "\n".join(tail)
    except Exception as e:
        return f"Error: {e}"


def search_logs(directory: str = ".", pattern: str = "error|exception|traceback",
                extensions: str = ".log,.txt", max_results: int = 50) -> str:
    """Search for patterns across log files in a directory.

    Args:
        directory: Directory to search.
        pattern: Regex pattern to match (default: error|exception|traceback).
        extensions: Comma-separated file extensions to search (default: .log,.txt).
        max_results: Max matching lines to return (default 50).
    """
    root = Path(directory).expanduser().resolve()
    if not root.is_dir():
        return f"Error: Not a directory — {directory}"

    exts = [e.strip().lower() for e in extensions.split(",")]
    try:
        rx = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        return f"Error: Bad regex — {e}"

    results: list[str] = []
    files_searched = 0

    for ext in exts:
        glob_pat = f"**/*{ext}" if ext.startswith(".") else f"**/*.{ext}"
        for fp in sorted(root.glob(glob_pat)):
            if not fp.is_file() or fp.stat().st_size > 50 * 1024 * 1024:  # skip >50MB
                continue
            files_searched += 1
            try:
                for i, line in enumerate(fp.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                    if rx.search(line):
                        rel = fp.relative_to(root)
                        results.append(f"{rel}:{i}: {line.strip()[:200]}")
                        if len(results) >= max_results:
                            break
            except Exception:
                continue
            if len(results) >= max_results:
                break

    if not results:
        return f"No matches for /{pattern}/ in {files_searched} files under {root.name}/"

    header = f"Found {len(results)} matches across {files_searched} files"
    if len(results) >= max_results:
        header += f" (capped at {max_results})"
    return header + "\n\n" + "\n".join(results)
