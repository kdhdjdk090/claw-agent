"""File system tools — read, write, list, find."""

from __future__ import annotations

import os
from pathlib import Path

# Default workspace root - can be overridden by agent
_WORKSPACE_ROOT: Path | None = None


def set_workspace_root(root: str | Path | None) -> None:
    """Set the workspace root for path traversal protection.
    
    All file operations will be constrained to this directory.
    Call this at agent initialization.
    
    Args:
        root: Workspace root path, or None to disable protection
    """
    global _WORKSPACE_ROOT
    _WORKSPACE_ROOT = Path(root).resolve() if root else None


def _validate_path(path: str | Path, must_be_in_workspace: bool = True) -> Path:
    """Validate and resolve a path with security checks.
    
    Args:
        path: Path to validate
        must_be_in_workspace: If True and workspace is set, verify path is within workspace
    
    Returns:
        Resolved Path object
        
    Raises:
        SecurityError: If path traversal is detected
    """
    resolved = Path(path).expanduser().resolve()
    
    # Check for path traversal if workspace root is set
    if must_be_in_workspace and _WORKSPACE_ROOT:
        try:
            resolved.relative_to(_WORKSPACE_ROOT)
        except ValueError:
            raise ValueError(
                f"Path traversal detected: {path} is outside workspace {_WORKSPACE_ROOT}"
            )
    
    return resolved


def read_file(path: str, start_line: int | None = None, end_line: int | None = None) -> str:
    """Read a file with path traversal protection.
    
    Args:
        path: File path to read
        start_line: Optional start line (1-indexed)
        end_line: Optional end line (inclusive)
    
    Returns:
        File contents or error message
    """
    try:
        p = _validate_path(path)
    except ValueError as e:
        return f"Error: {e}"
    
    if not p.exists():
        return f"Error: file not found: {p}"
    if not p.is_file():
        return f"Error: not a file: {p}"

    lines = p.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)

    if start_line is not None or end_line is not None:
        s = (start_line or 1) - 1
        e = end_line or len(lines)
        lines = lines[s:e]

    return "".join(lines)


def write_file(path: str, content: str) -> str:
    """Write a file with path traversal protection.
    
    Args:
        path: File path to write
        content: Content to write
    
    Returns:
        Success message or error
    """
    try:
        p = _validate_path(path)
    except ValueError as e:
        return f"Error: {e}"
    
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} bytes to {p}"


def list_directory(path: str = ".") -> str:
    """List directory contents with path traversal protection.
    
    Args:
        path: Directory path to list
    
    Returns:
        Directory listing or error message
    """
    try:
        p = _validate_path(path)
    except ValueError as e:
        return f"Error: {e}"
    
    if not p.exists():
        return f"Error: directory not found: {p}"
    if not p.is_dir():
        return f"Error: not a directory: {p}"

    entries = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
    lines = []
    for entry in entries:
        name = entry.name + ("/" if entry.is_dir() else "")
        lines.append(name)
    return "\n".join(lines) if lines else "(empty directory)"


def find_files(pattern: str, directory: str = ".") -> str:
    """Find files matching a pattern with path traversal protection.
    
    Args:
        pattern: Glob pattern to match
        directory: Directory to search in
    
    Returns:
        List of matching files or error message
    """
    try:
        p = _validate_path(directory)
    except ValueError as e:
        return f"Error: {e}"
    
    if not p.exists():
        return f"Error: directory not found: {p}"

    matches = sorted(str(m.relative_to(p)) for m in p.glob(pattern) if m.is_file())
    if not matches:
        return "No files matched."
    # Cap at 200 results
    if len(matches) > 200:
        matches = matches[:200]
        matches.append(f"... and more (showing first 200)")
    return "\n".join(matches)
