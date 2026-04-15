"""Package tools — dependency management across ecosystems."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ..python_runtime import python_command


def list_dependencies(directory: str = ".", ecosystem: str = "auto") -> str:
    """List project dependencies.

    Args:
        directory: Project root.
        ecosystem: "auto", "pip", "npm", "cargo", "go".
    """
    root = Path(directory).expanduser().resolve()
    if not root.is_dir():
        return f"Error: Not a directory — {directory}"

    eco = ecosystem
    if eco == "auto":
        eco = _detect_ecosystem(root)
        if not eco:
            return "Error: Could not detect package ecosystem. Specify 'ecosystem' explicitly."

    if eco == "pip":
        return _pip_list(root)
    elif eco == "npm":
        return _npm_list(root)
    elif eco == "cargo":
        return _cargo_list(root)
    elif eco == "go":
        return _go_list(root)
    else:
        return f"Error: Unknown ecosystem '{eco}'. Supported: pip, npm, cargo, go"


def check_outdated(directory: str = ".", ecosystem: str = "auto") -> str:
    """Check for outdated dependencies.

    Args:
        directory: Project root.
        ecosystem: "auto", "pip", "npm", "cargo", "go".
    """
    root = Path(directory).expanduser().resolve()
    eco = ecosystem
    if eco == "auto":
        eco = _detect_ecosystem(root)
        if not eco:
            return "Error: Could not detect package ecosystem."

    cmds = {
        "pip": python_command("-m", "pip", "list", "--outdated", "--format=columns"),
        "npm": ["npm", "outdated"],
        "cargo": ["cargo", "outdated"],
        "go": ["go", "list", "-u", "-m", "all"],
    }
    cmd = cmds.get(eco)
    if not cmd:
        return f"Error: Unknown ecosystem '{eco}'."

    try:
        result = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, timeout=60)
        output = (result.stdout or result.stderr).strip()
        if not output:
            return f"✓ All {eco} dependencies are up to date."
        return f"Outdated {eco} dependencies:\n\n{output}"
    except FileNotFoundError:
        return f"Error: {cmd[0]} not found."
    except subprocess.TimeoutExpired:
        return "Error: Timed out after 60s."


def audit_dependencies(directory: str = ".", ecosystem: str = "auto") -> str:
    """Audit dependencies for known security vulnerabilities.

    Args:
        directory: Project root.
        ecosystem: "auto", "pip", "npm".
    """
    root = Path(directory).expanduser().resolve()
    eco = ecosystem
    if eco == "auto":
        eco = _detect_ecosystem(root)
        if not eco:
            return "Error: Could not detect package ecosystem."

    cmds = {
        "pip": python_command("-m", "pip_audit"),
        "npm": ["npm", "audit"],
    }
    cmd = cmds.get(eco)
    if not cmd:
        return f"Error: Audit not supported for '{eco}'. Supported: pip, npm"

    try:
        result = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, timeout=90)
        output = (result.stdout + "\n" + result.stderr).strip()
        if result.returncode == 0 and eco == "pip":
            return f"✓ No vulnerabilities found in {eco} dependencies."
        return f"Security audit ({eco}):\n\n{output}"
    except FileNotFoundError:
        tool = "pip-audit" if eco == "pip" else cmd[0]
        return f"Error: {tool} not found. Install it first."
    except subprocess.TimeoutExpired:
        return "Error: Audit timed out after 90s."


# ---- Internals ----

def _detect_ecosystem(root: Path) -> str | None:
    if (root / "requirements.txt").exists() or (root / "pyproject.toml").exists() or (root / "setup.py").exists():
        return "pip"
    if (root / "package.json").exists():
        return "npm"
    if (root / "Cargo.toml").exists():
        return "cargo"
    if (root / "go.mod").exists():
        return "go"
    return None


def _pip_list(root: Path) -> str:
    # Try requirements.txt first
    req = root / "requirements.txt"
    if req.exists():
        content = req.read_text(encoding="utf-8", errors="replace").strip()
        lines = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith("#")]
        return f"pip dependencies ({len(lines)} from requirements.txt):\n" + "\n".join(f"  {l}" for l in lines)
    # Fallback to pip freeze
    try:
        result = subprocess.run(python_command("-m", "pip", "freeze"), cwd=str(root), capture_output=True, text=True, timeout=30)
        pkgs = [l for l in result.stdout.strip().splitlines() if l.strip()]
        return f"pip dependencies ({len(pkgs)} installed):\n" + "\n".join(f"  {p}" for p in pkgs[:50])
    except Exception as e:
        return f"Error listing pip deps: {e}"


def _npm_list(root: Path) -> str:
    pkg_json = root / "package.json"
    if pkg_json.exists():
        try:
            pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
            deps = pkg.get("dependencies", {})
            dev = pkg.get("devDependencies", {})
            lines = [f"npm dependencies ({len(deps)} prod, {len(dev)} dev):"]
            if deps:
                lines.append("\nProduction:")
                for name, ver in sorted(deps.items()):
                    lines.append(f"  {name}: {ver}")
            if dev:
                lines.append("\nDev:")
                for name, ver in sorted(dev.items()):
                    lines.append(f"  {name}: {ver}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error reading package.json: {e}"
    return "Error: No package.json found."


def _cargo_list(root: Path) -> str:
    try:
        result = subprocess.run(["cargo", "tree", "--depth=1"], cwd=str(root), capture_output=True, text=True, timeout=30)
        return f"Cargo dependencies:\n\n{result.stdout.strip()}"
    except Exception as e:
        return f"Error: {e}"


def _go_list(root: Path) -> str:
    try:
        result = subprocess.run(["go", "list", "-m", "all"], cwd=str(root), capture_output=True, text=True, timeout=30)
        mods = result.stdout.strip().splitlines()
        return f"Go modules ({len(mods)}):\n" + "\n".join(f"  {m}" for m in mods[:50])
    except Exception as e:
        return f"Error: {e}"
