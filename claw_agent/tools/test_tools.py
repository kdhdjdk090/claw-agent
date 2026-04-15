"""Test tools — run tests, parse results, generate stubs."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

from ..python_runtime import python_command


def run_tests(directory: str = ".", framework: str = "auto", pattern: str = "") -> str:
    """Detect and run the project's test suite.

    Args:
        directory: Project root directory.
        framework: "auto", "pytest", "jest", "go", "cargo", "unittest", "mocha".
        pattern: Optional filter pattern (e.g. test name or file glob).
    """
    root = Path(directory).expanduser().resolve()
    if not root.is_dir():
        return f"Error: Not a directory — {directory}"

    detected = framework
    if detected == "auto":
        detected = _detect_framework(root)
        if not detected:
            return "Error: Could not detect test framework. Specify 'framework' explicitly."

    cmd_map = {
        "pytest": python_command("-m", "pytest", "-v"),
        "unittest": python_command("-m", "unittest", "discover", "-v"),
        "jest": ["npx", "jest", "--verbose"],
        "mocha": ["npx", "mocha", "--recursive"],
        "go": ["go", "test", "-v", "./..."],
        "cargo": ["cargo", "test"],
    }

    cmd = cmd_map.get(detected)
    if not cmd:
        return f"Error: Unknown framework '{detected}'. Supported: {', '.join(cmd_map)}"

    if pattern:
        if detected == "pytest":
            cmd.extend(["-k", pattern])
        elif detected in ("jest", "mocha"):
            cmd.extend(["--grep", pattern])
        elif detected == "go":
            cmd.extend(["-run", pattern])

    try:
        result = subprocess.run(
            cmd, cwd=str(root), capture_output=True, text=True, timeout=120
        )
        output = result.stdout + ("\n" + result.stderr if result.stderr else "")
        status = "PASSED" if result.returncode == 0 else "FAILED"
        return f"Framework: {detected}\nStatus: {status}\nReturn code: {result.returncode}\n\n{output.strip()}"
    except FileNotFoundError:
        return f"Error: Command not found — {cmd[0]}. Is {detected} installed?"
    except subprocess.TimeoutExpired:
        return "Error: Tests timed out after 120 seconds."


def parse_test_output(output: str) -> str:
    """Parse test output into structured pass/fail summary.

    Handles pytest, jest, go test, and cargo test formats.
    """
    lines = output.strip().splitlines()
    passed = failed = skipped = errors = 0
    failures = []

    for line in lines:
        low = line.lower().strip()
        # pytest: "PASSED", "FAILED", "ERROR"
        if " passed" in low and ("failed" in low or "error" in low or "passed" in low):
            m = re.search(r"(\d+)\s+passed", low)
            if m:
                passed = int(m.group(1))
            m = re.search(r"(\d+)\s+failed", low)
            if m:
                failed = int(m.group(1))
            m = re.search(r"(\d+)\s+error", low)
            if m:
                errors = int(m.group(1))
            m = re.search(r"(\d+)\s+skipped", low)
            if m:
                skipped = int(m.group(1))
        # jest: "Tests: X passed, Y failed"
        elif low.startswith("tests:"):
            m = re.search(r"(\d+)\s+passed", low)
            if m:
                passed = int(m.group(1))
            m = re.search(r"(\d+)\s+failed", low)
            if m:
                failed = int(m.group(1))
        # go: "--- FAIL:", "--- PASS:"
        elif low.startswith("--- fail:"):
            failed += 1
            failures.append(line.strip())
        elif low.startswith("--- pass:"):
            passed += 1
        # generic FAIL/PASS markers
        elif "FAILED" in line and "::" in line:
            failures.append(line.strip())

    total = passed + failed + skipped + errors
    parts = [
        f"Total: {total}",
        f"Passed: {passed}",
        f"Failed: {failed}",
    ]
    if skipped:
        parts.append(f"Skipped: {skipped}")
    if errors:
        parts.append(f"Errors: {errors}")

    result = " | ".join(parts)
    if failures:
        result += "\n\nFailures:\n" + "\n".join(f"  ✗ {f}" for f in failures[:20])
    return result


def generate_test_stub(source_file: str, framework: str = "auto") -> str:
    """Generate a test file skeleton for a source file.

    Reads function/class names and creates test stubs.
    """
    path = Path(source_file).expanduser().resolve()
    if not path.exists():
        return f"Error: File not found — {source_file}"

    ext = path.suffix.lower()
    content = path.read_text(encoding="utf-8", errors="replace")

    if ext == ".py":
        return _python_test_stub(path, content, framework)
    elif ext in (".js", ".ts", ".jsx", ".tsx"):
        return _js_test_stub(path, content, framework)
    elif ext == ".go":
        return _go_test_stub(path, content)
    else:
        return f"Error: Unsupported language '{ext}' for test generation."


# ---- Internals ----

def _detect_framework(root: Path) -> str | None:
    if (root / "pytest.ini").exists() or (root / "pyproject.toml").exists() or (root / "setup.cfg").exists():
        return "pytest"
    if (root / "package.json").exists():
        try:
            pkg = json.loads((root / "package.json").read_text())
            deps = {**pkg.get("devDependencies", {}), **pkg.get("dependencies", {})}
            if "jest" in deps:
                return "jest"
            if "mocha" in deps:
                return "mocha"
        except Exception:
            pass
        return "jest"
    if (root / "go.mod").exists():
        return "go"
    if (root / "Cargo.toml").exists():
        return "cargo"
    # fallback: look for test_*.py
    if list(root.rglob("test_*.py")):
        return "pytest"
    return None


def _python_test_stub(path: Path, content: str, framework: str) -> str:
    funcs = re.findall(r"^def\s+(\w+)\s*\(", content, re.MULTILINE)
    classes = re.findall(r"^class\s+(\w+)", content, re.MULTILINE)
    module = path.stem

    lines = [f'"""Tests for {module}."""\n', f"import pytest\nfrom {module} import *\n\n"]
    for cls in classes:
        lines.append(f"class Test{cls}:")
        lines.append(f"    def test_{cls.lower()}_init(self):")
        lines.append(f"        # TODO: test {cls} initialization")
        lines.append(f"        pass\n\n")
    for fn in funcs:
        if fn.startswith("_"):
            continue
        lines.append(f"def test_{fn}():")
        lines.append(f"    # TODO: test {fn}")
        lines.append(f"    pass\n\n")
    return "\n".join(lines) if (funcs or classes) else f"# No functions/classes found in {path.name}"


def _js_test_stub(path: Path, content: str, framework: str) -> str:
    exports = re.findall(r"export\s+(?:function|const|class)\s+(\w+)", content)
    if not exports:
        exports = re.findall(r"(?:function|const|class)\s+(\w+)", content)
    module = path.stem

    lines = [f"import {{ {', '.join(exports[:10])} }} from './{module}';\n"]
    lines.append(f"describe('{module}', () => {{")
    for name in exports[:10]:
        lines.append(f"  test('{name} should work', () => {{")
        lines.append(f"    // TODO: test {name}")
        lines.append(f"    expect(true).toBe(true);")
        lines.append(f"  }});\n")
    lines.append("});")
    return "\n".join(lines) if exports else f"// No exports found in {path.name}"


def _go_test_stub(path: Path, content: str) -> str:
    pkg = re.search(r"^package\s+(\w+)", content, re.MULTILINE)
    pkg_name = pkg.group(1) if pkg else "main"
    funcs = re.findall(r"^func\s+(\w+)\s*\(", content, re.MULTILINE)

    lines = [f"package {pkg_name}\n", 'import "testing"\n']
    for fn in funcs:
        if fn.startswith("Test") or fn.startswith("_"):
            continue
        lines.append(f"func Test{fn}(t *testing.T) {{")
        lines.append(f"\t// TODO: test {fn}")
        lines.append(f"}}\n")
    return "\n".join(lines) if funcs else f"// No functions found in {path.name}"
