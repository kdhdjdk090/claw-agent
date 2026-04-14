"""Diagnostic tools — syntax checking, lint errors, compile errors."""

from __future__ import annotations

import subprocess
import json
import os
from pathlib import Path


def get_errors(file_paths: list[str] | None = None, workspace: str = ".") -> str:
    """Get compile or lint errors for files. Runs appropriate linter based on file type.

    If file_paths is None or empty, scans the workspace root for common error sources.
    """
    root = Path(workspace).expanduser().resolve()
    results: list[str] = []

    targets: list[Path] = []
    if file_paths:
        for fp in file_paths:
            p = Path(fp).expanduser().resolve()
            if p.exists():
                targets.append(p)
            else:
                results.append(f"⚠ Not found: {fp}")
    else:
        # Auto-detect: collect Python and JS/TS files
        for ext in (".py", ".js", ".ts", ".tsx", ".jsx"):
            targets.extend(root.glob(f"**/*{ext}"))

    if not targets:
        return "No files to check."

    # Group by type
    py_files = [t for t in targets if t.suffix == ".py"]
    js_ts_files = [t for t in targets if t.suffix in (".js", ".ts", ".tsx", ".jsx")]

    # Python: try py_compile for syntax, then flake8
    for pf in py_files[:50]:  # cap at 50
        rel = pf.relative_to(root) if pf.is_relative_to(root) else pf
        # Quick syntax check
        try:
            r = subprocess.run(
                ["python", "-m", "py_compile", str(pf)],
                capture_output=True, text=True, timeout=10,
                cwd=str(root),
            )
            if r.returncode != 0:
                err = (r.stderr or r.stdout).strip()
                results.append(f"[SYNTAX] {rel}: {err}")
        except Exception:
            pass

    if py_files:
        # Try flake8
        try:
            fargs = ["python", "-m", "flake8", "--max-line-length=120",
                      "--select=E,W,F"] + [str(f) for f in py_files[:50]]
            r = subprocess.run(fargs, capture_output=True, text=True, timeout=30, cwd=str(root))
            if r.stdout.strip():
                results.append("[FLAKE8]")
                for line in r.stdout.strip().splitlines()[:40]:
                    results.append(f"  {line}")
        except FileNotFoundError:
            pass
        except Exception:
            pass

    # JS/TS: try quick node syntax check
    for jf in js_ts_files[:30]:
        rel = jf.relative_to(root) if jf.is_relative_to(root) else jf
        try:
            r = subprocess.run(
                ["node", "--check", str(jf)],
                capture_output=True, text=True, timeout=10,
                cwd=str(root),
            )
            if r.returncode != 0:
                err = (r.stderr or r.stdout).strip()
                results.append(f"[SYNTAX] {rel}: {err}")
        except FileNotFoundError:
            break  # node not available
        except Exception:
            pass

    if not results:
        n = len(py_files) + len(js_ts_files)
        return f"No errors found in {n} file(s)."
    return "\n".join(results)


def check_syntax(file_path: str) -> str:
    """Check a single file for syntax errors. Returns 'OK' or the error."""
    p = Path(file_path).expanduser().resolve()
    if not p.exists():
        return f"Error: File not found — {file_path}"

    if p.suffix == ".py":
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read()
            compile(source, str(p), "exec")
            return f"OK — {p.name} has no syntax errors."
        except SyntaxError as e:
            return f"SyntaxError at line {e.lineno}: {e.msg}"

    elif p.suffix == ".json":
        try:
            with open(p, "r", encoding="utf-8") as f:
                json.load(f)
            return f"OK — {p.name} is valid JSON."
        except json.JSONDecodeError as e:
            return f"JSONError at line {e.lineno}: {e.msg}"

    elif p.suffix in (".js", ".ts", ".tsx", ".jsx"):
        try:
            r = subprocess.run(
                ["node", "--check", str(p)],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode == 0:
                return f"OK — {p.name} has no syntax errors."
            return (r.stderr or r.stdout).strip()
        except FileNotFoundError:
            return "node not found — cannot check JS/TS syntax."
        except Exception as e:
            return f"Error: {e}"

    return f"No syntax checker for {p.suffix} files."
