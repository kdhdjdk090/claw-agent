"""Workspace context — detect project info, git status, etc."""

from __future__ import annotations

import subprocess
from pathlib import Path


def get_workspace_context(directory: str = ".") -> str:
    """Gather comprehensive workspace context info."""
    root = Path(directory).expanduser().resolve()
    sections = []

    # Basic info
    sections.append(f"Workspace: {root}")

    # Detect project type
    markers = {
        "pyproject.toml": "Python",
        "package.json": "Node.js",
        "Cargo.toml": "Rust",
        "go.mod": "Go",
        "pom.xml": "Java (Maven)",
        "build.gradle": "Java (Gradle)",
        "Gemfile": "Ruby",
        "composer.json": "PHP",
        "CMakeLists.txt": "C/C++ (CMake)",
        "Makefile": "Make",
        "Dockerfile": "Docker",
    }
    detected = []
    for marker, lang in markers.items():
        if (root / marker).exists():
            detected.append(lang)
    if detected:
        sections.append(f"Stack: {', '.join(detected)}")

    # File counts
    ext_counts: dict[str, int] = {}
    for f in root.rglob("*"):
        if f.is_file() and not any(p.startswith(".") for p in f.relative_to(root).parts):
            ext = f.suffix.lower() or "(no ext)"
            ext_counts[ext] = ext_counts.get(ext, 0) + 1
    top_exts = sorted(ext_counts.items(), key=lambda x: -x[1])[:10]
    if top_exts:
        sections.append("Files by type: " + ", ".join(f"{ext}={n}" for ext, n in top_exts))

    # Git info
    try:
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, cwd=str(root), timeout=5
        ).stdout.strip()
        if branch:
            sections.append(f"Git branch: {branch}")

        status = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, cwd=str(root), timeout=5
        ).stdout.strip()
        if status:
            changed = len(status.splitlines())
            sections.append(f"Git changes: {changed} files modified")
        else:
            sections.append("Git: clean working tree")
    except Exception:
        sections.append("Git: not a repository")

    return "\n".join(sections)


def git_diff(directory: str = ".", staged: bool = False) -> str:
    """Show git diff of current changes."""
    root = Path(directory).expanduser().resolve()
    cmd = ["git", "diff"]
    if staged:
        cmd.append("--staged")
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=str(root), timeout=10
        )
        diff = result.stdout.strip()
        return diff if diff else "No changes."
    except Exception as e:
        return f"Error: {e}"


def git_log(directory: str = ".", count: int = 10) -> str:
    """Show recent git commits."""
    root = Path(directory).expanduser().resolve()
    try:
        result = subprocess.run(
            ["git", "log", f"--oneline", f"-{count}"],
            capture_output=True, text=True, cwd=str(root), timeout=10
        )
        return result.stdout.strip() or "No commits."
    except Exception as e:
        return f"Error: {e}"
