"""Notebook tool — execute Python code in a subprocess."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


def notebook_run(code: str, timeout: int = 30) -> str:
    """Execute a Python code snippet and return its output.
    
    This is like a Jupyter notebook cell — run any Python code and see results.
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(code)
        tmp_path = f.name

    try:
        result = subprocess.run(
            ["python", tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += result.stderr
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"
        return output.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return f"Error: code execution timed out after {timeout}s"
    except Exception as e:
        return f"Error: {e}"
    finally:
        Path(tmp_path).unlink(missing_ok=True)
