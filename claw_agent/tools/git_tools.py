"""Enhanced git tools — beyond basic diff/log already in context_tools."""

from __future__ import annotations

import subprocess
from pathlib import Path


def _git(args: list[str], cwd: str = ".") -> tuple[int, str]:
    """Run a git command and return (returncode, output)."""
    try:
        r = subprocess.run(
            ["git"] + args,
            capture_output=True, text=True, timeout=30,
            cwd=cwd,
        )
        return r.returncode, (r.stdout + r.stderr).strip()
    except FileNotFoundError:
        return -1, "git not found on PATH."
    except Exception as e:
        return -1, str(e)


def get_changed_files(cwd: str = ".") -> str:
    """Get all changed files — staged, unstaged, and untracked."""
    lines = ["Changed files:"]

    # Staged
    rc, out = _git(["diff", "--cached", "--name-status"], cwd)
    if rc == 0 and out:
        lines.append("\n[Staged]")
        for ln in out.splitlines():
            lines.append(f"  {ln}")

    # Unstaged (modified)
    rc, out = _git(["diff", "--name-status"], cwd)
    if rc == 0 and out:
        lines.append("\n[Unstaged]")
        for ln in out.splitlines():
            lines.append(f"  {ln}")

    # Untracked
    rc, out = _git(["ls-files", "--others", "--exclude-standard"], cwd)
    if rc == 0 and out:
        lines.append("\n[Untracked]")
        for ln in out.splitlines()[:50]:
            lines.append(f"  ? {ln}")
        total = len(out.splitlines())
        if total > 50:
            lines.append(f"  ... and {total - 50} more")

    # Merge conflicts
    rc, out = _git(["diff", "--name-only", "--diff-filter=U"], cwd)
    if rc == 0 and out:
        lines.append("\n[Merge Conflicts]")
        for ln in out.splitlines():
            lines.append(f"  ! {ln}")

    if len(lines) == 1:
        return "Working tree clean — no changes."
    return "\n".join(lines)


def git_stash(action: str = "list", message: str = "", cwd: str = ".") -> str:
    """Manage git stash. Actions: list, push, pop, apply, drop."""
    if action == "list":
        rc, out = _git(["stash", "list"], cwd)
        return out or "No stashes."
    elif action == "push":
        args = ["stash", "push"]
        if message:
            args += ["-m", message]
        rc, out = _git(args, cwd)
        return out
    elif action == "pop":
        rc, out = _git(["stash", "pop"], cwd)
        return out
    elif action == "apply":
        rc, out = _git(["stash", "apply"], cwd)
        return out
    elif action == "drop":
        rc, out = _git(["stash", "drop"], cwd)
        return out
    return f"Unknown stash action: {action}. Use list/push/pop/apply/drop."


def git_branch(action: str = "list", name: str = "", cwd: str = ".") -> str:
    """Manage branches. Actions: list, create, switch, delete, current."""
    if action == "list":
        rc, out = _git(["branch", "-a", "--no-color"], cwd)
        return out or "No branches."
    elif action == "current":
        rc, out = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd)
        return f"Current branch: {out}"
    elif action == "create":
        if not name:
            return "Error: branch name required."
        rc, out = _git(["checkout", "-b", name], cwd)
        return out
    elif action == "switch":
        if not name:
            return "Error: branch name required."
        rc, out = _git(["checkout", name], cwd)
        return out
    elif action == "delete":
        if not name:
            return "Error: branch name required."
        rc, out = _git(["branch", "-d", name], cwd)
        return out
    return f"Unknown branch action: {action}. Use list/create/switch/delete/current."


def git_blame(file_path: str, start_line: int = 1, end_line: int = 50, cwd: str = ".") -> str:
    """Show git blame for a file region."""
    p = Path(file_path)
    if not p.exists():
        return f"File not found: {file_path}"
    args = ["blame", f"-L{start_line},{end_line}", "--no-color", str(p)]
    rc, out = _git(args, cwd)
    return out


def git_show_commit(ref: str = "HEAD", cwd: str = ".") -> str:
    """Show details of a commit."""
    rc, out = _git(["show", "--stat", "--no-color", ref], cwd)
    if len(out) > 5000:
        out = out[:5000] + "\n... [truncated]"
    return out
