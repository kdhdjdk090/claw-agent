"""Lint tools — run formatters and linters on source code."""

from __future__ import annotations

import subprocess
from pathlib import Path

from ..python_runtime import python_command


_FORMATTERS = {
    ".py": {"cmd": python_command("-m", "black", "--quiet"), "name": "black"},
    ".js": {"cmd": ["npx", "prettier", "--write"], "name": "prettier"},
    ".ts": {"cmd": ["npx", "prettier", "--write"], "name": "prettier"},
    ".jsx": {"cmd": ["npx", "prettier", "--write"], "name": "prettier"},
    ".tsx": {"cmd": ["npx", "prettier", "--write"], "name": "prettier"},
    ".json": {"cmd": ["npx", "prettier", "--write"], "name": "prettier"},
    ".css": {"cmd": ["npx", "prettier", "--write"], "name": "prettier"},
    ".html": {"cmd": ["npx", "prettier", "--write"], "name": "prettier"},
    ".go": {"cmd": ["gofmt", "-w"], "name": "gofmt"},
    ".rs": {"cmd": ["rustfmt"], "name": "rustfmt"},
}

_LINTERS = {
    ".py": {"cmd": python_command("-m", "ruff", "check"), "name": "ruff"},
    ".js": {"cmd": ["npx", "eslint"], "name": "eslint"},
    ".ts": {"cmd": ["npx", "eslint"], "name": "eslint"},
    ".jsx": {"cmd": ["npx", "eslint"], "name": "eslint"},
    ".tsx": {"cmd": ["npx", "eslint"], "name": "eslint"},
    ".go": {"cmd": ["go", "vet"], "name": "go vet"},
    ".rs": {"cmd": ["cargo", "clippy", "--"], "name": "clippy"},
}


def format_code(file_path: str, formatter: str = "auto") -> str:
    """Run a code formatter on a file.

    Args:
        file_path: Path to source file.
        formatter: "auto" (detect by extension), or explicit name like "black", "prettier", "gofmt", "rustfmt".
    """
    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        return f"Error: File not found — {file_path}"

    ext = path.suffix.lower()

    if formatter == "auto":
        info = _FORMATTERS.get(ext)
        if not info:
            return f"Error: No formatter configured for '{ext}'. Supported: {', '.join(sorted(_FORMATTERS))}"
        cmd = info["cmd"] + [str(path)]
        name = info["name"]
    else:
        cmd = [formatter, str(path)]
        name = formatter

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return f"✓ Formatted {path.name} with {name}"
        else:
            return f"Formatter {name} returned code {result.returncode}:\n{(result.stderr or result.stdout).strip()}"
    except FileNotFoundError:
        return f"Error: {name} not found. Is it installed?"
    except subprocess.TimeoutExpired:
        return f"Error: {name} timed out after 30s."


def lint_check(file_path: str, linter: str = "auto") -> str:
    """Run a linter on a file and return diagnostics.

    Args:
        file_path: Path to source file.
        linter: "auto" (detect by extension), or explicit name.
    """
    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        return f"Error: File not found — {file_path}"

    ext = path.suffix.lower()

    if linter == "auto":
        info = _LINTERS.get(ext)
        if not info:
            return f"Error: No linter configured for '{ext}'. Supported: {', '.join(sorted(_LINTERS))}"
        cmd = info["cmd"] + [str(path)]
        name = info["name"]
    else:
        cmd = [linter, str(path)]
        name = linter

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        output = (result.stdout + "\n" + result.stderr).strip()
        if result.returncode == 0:
            return f"✓ {name}: No issues in {path.name}"
        else:
            lines = output.splitlines()
            count = len([l for l in lines if l.strip()])
            return f"✗ {name}: {count} issue(s) in {path.name}\n\n{output}"
    except FileNotFoundError:
        return f"Error: {name} not found. Is it installed?"
    except subprocess.TimeoutExpired:
        return f"Error: {name} timed out after 60s."


def auto_fix_lint(file_path: str, linter: str = "auto") -> str:
    """Run a linter with auto-fix enabled.

    Args:
        file_path: Path to source file.
        linter: "auto" (detect by extension), or explicit name.
    """
    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        return f"Error: File not found — {file_path}"

    ext = path.suffix.lower()

    fix_cmds = {
        ".py": {"cmd": python_command("-m", "ruff", "check", "--fix"), "name": "ruff --fix"},
        ".js": {"cmd": ["npx", "eslint", "--fix"], "name": "eslint --fix"},
        ".ts": {"cmd": ["npx", "eslint", "--fix"], "name": "eslint --fix"},
        ".jsx": {"cmd": ["npx", "eslint", "--fix"], "name": "eslint --fix"},
        ".tsx": {"cmd": ["npx", "eslint", "--fix"], "name": "eslint --fix"},
        ".rs": {"cmd": ["cargo", "clippy", "--fix", "--allow-dirty", "--"], "name": "clippy --fix"},
    }

    if linter == "auto":
        info = fix_cmds.get(ext)
        if not info:
            return f"Error: No auto-fix linter for '{ext}'. Supported: {', '.join(sorted(fix_cmds))}"
        cmd = info["cmd"] + [str(path)]
        name = info["name"]
    else:
        cmd = [linter, "--fix", str(path)]
        name = f"{linter} --fix"

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        output = (result.stdout + "\n" + result.stderr).strip()
        if result.returncode == 0:
            return f"✓ Auto-fixed {path.name} with {name}"
        else:
            return f"Auto-fix partial for {path.name}:\n{output}"
    except FileNotFoundError:
        return f"Error: {name} not found. Is it installed?"
    except subprocess.TimeoutExpired:
        return f"Error: {name} timed out after 60s."
