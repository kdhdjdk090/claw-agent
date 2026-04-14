"""Project detection + package installation tools."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def get_project_info(directory: str = ".") -> str:
    """Detect project type, frameworks, main scripts, dependencies, and build commands.

    Scans the given directory for package.json, requirements.txt, Cargo.toml,
    go.mod, pyproject.toml, etc. and reports what it finds.
    """
    root = Path(directory).expanduser().resolve()
    if not root.is_dir():
        return f"Error: not a directory — {directory}"

    info: dict = {"root": str(root), "project_types": [], "frameworks": [], "scripts": {}, "deps": {}}

    # ── Python ──
    pyproject = root / "pyproject.toml"
    setup_py = root / "setup.py"
    setup_cfg = root / "setup.cfg"
    req_txt = root / "requirements.txt"

    if pyproject.exists():
        info["project_types"].append("Python (pyproject.toml)")
        try:
            text = pyproject.read_text(encoding="utf-8")
            if "django" in text.lower():
                info["frameworks"].append("Django")
            if "flask" in text.lower():
                info["frameworks"].append("Flask")
            if "fastapi" in text.lower():
                info["frameworks"].append("FastAPI")
        except Exception:
            pass
    if setup_py.exists():
        info["project_types"].append("Python (setup.py)")
    if req_txt.exists():
        info["project_types"].append("Python (requirements.txt)")
        try:
            deps = [l.strip() for l in req_txt.read_text(encoding="utf-8").splitlines()
                    if l.strip() and not l.startswith("#")]
            info["deps"]["pip"] = deps[:30]
        except Exception:
            pass

    # ── Node / JavaScript / TypeScript ──
    pkg_json = root / "package.json"
    if pkg_json.exists():
        info["project_types"].append("Node.js (package.json)")
        try:
            pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
            info["scripts"] = pkg.get("scripts", {})
            all_deps = {}
            for k in ("dependencies", "devDependencies"):
                all_deps.update(pkg.get(k, {}))
            info["deps"]["npm"] = list(all_deps.keys())[:40]
            for fw in ("react", "vue", "angular", "svelte", "next", "nuxt", "express", "nestjs"):
                if fw in all_deps:
                    info["frameworks"].append(fw)
        except Exception:
            pass

    # ── Rust ──
    cargo = root / "Cargo.toml"
    if cargo.exists():
        info["project_types"].append("Rust (Cargo.toml)")

    # ── Go ──
    gomod = root / "go.mod"
    if gomod.exists():
        info["project_types"].append("Go (go.mod)")

    # ── Java / Kotlin ──
    for fn in ("pom.xml", "build.gradle", "build.gradle.kts"):
        if (root / fn).exists():
            info["project_types"].append(f"JVM ({fn})")
            break

    # ── Docker ──
    if (root / "Dockerfile").exists() or (root / "docker-compose.yml").exists():
        info["project_types"].append("Docker")

    # ── Git info ──
    git_dir = root / ".git"
    if git_dir.exists():
        info["git"] = True
        try:
            branch = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True, text=True, cwd=str(root), timeout=5,
            )
            info["git_branch"] = branch.stdout.strip()
        except Exception:
            pass

    if not info["project_types"]:
        info["project_types"].append("Unknown / no recognized project files")

    # Format output
    lines = [f"Project: {root.name}", f"Root: {root}", ""]
    lines.append(f"Types: {', '.join(info['project_types'])}")
    if info["frameworks"]:
        lines.append(f"Frameworks: {', '.join(info['frameworks'])}")
    if info.get("git"):
        lines.append(f"Git branch: {info.get('git_branch', '?')}")
    if info["scripts"]:
        lines.append("\nScripts:")
        for k, v in list(info["scripts"].items())[:15]:
            lines.append(f"  {k}: {v}")
    if info["deps"]:
        lines.append("\nDependencies:")
        for mgr, deps in info["deps"].items():
            lines.append(f"  {mgr}: {len(deps)} packages")
            for d in deps[:10]:
                lines.append(f"    - {d}")
            if len(deps) > 10:
                lines.append(f"    ... +{len(deps) - 10} more")
    return "\n".join(lines)


def install_packages(
    packages: str,
    manager: str = "auto",
    directory: str = ".",
) -> str:
    """Install packages using pip, npm, or cargo.

    Args:
        packages: Space-separated package names (e.g. 'requests flask').
        manager: 'pip', 'npm', 'cargo', or 'auto' (detect from project).
        directory: Working directory.
    """
    if not packages.strip():
        return "Error: no packages specified."

    root = Path(directory).expanduser().resolve()
    pkg_list = packages.strip().split()

    if manager == "auto":
        if (root / "package.json").exists() or (root / "node_modules").exists():
            manager = "npm"
        elif (root / "Cargo.toml").exists():
            manager = "cargo"
        else:
            manager = "pip"

    if manager == "pip":
        cmd = ["pip", "install"] + pkg_list
    elif manager == "npm":
        cmd = ["npm", "install"] + pkg_list
    elif manager == "cargo":
        cmd = ["cargo", "add"] + pkg_list
    else:
        return f"Error: unknown manager '{manager}'."

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=str(root), timeout=120,
        )
        output = result.stdout + result.stderr
        if result.returncode == 0:
            return f"✅ Installed: {', '.join(pkg_list)} ({manager})\n{output[-2000:]}"
        else:
            return f"❌ Install failed (exit {result.returncode}):\n{output[-3000:]}"
    except subprocess.TimeoutExpired:
        return "Error: install timed out after 120s."
    except FileNotFoundError:
        return f"Error: '{manager}' command not found. Is it installed and on PATH?"
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"
