"""Profiling tools — time commands, memory usage, benchmark comparison."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

from ..validation import validate_command, SecurityError


def time_command(command: str, runs: int = 3) -> str:
    """Time a shell command over N runs and report min/avg/max.

    Args:
        command: Shell command to time.
        runs: Number of iterations (default 3, max 20).
    """
    # Validate command before execution
    try:
        validate_command(command)
    except SecurityError as e:
        return f"[BLOCKED: {e}]"
    
    runs = max(1, min(int(runs), 20))
    times: list[float] = []

    for i in range(runs):
        start = time.perf_counter()
        try:
            result = subprocess.run(
                command,
                shell=True,  # Required for shell features, validated above
                capture_output=True,
                timeout=120,
            )
        except subprocess.TimeoutExpired:
            return f"Command timed out after 120s on run {i + 1}/{runs}"
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    avg = sum(times) / len(times)
    mn = min(times)
    mx = max(times)

    lines = [
        f"Command: {command}",
        f"Runs: {runs}",
        f"Min:  {mn:.4f}s",
        f"Avg:  {avg:.4f}s",
        f"Max:  {mx:.4f}s",
    ]
    if runs > 1:
        spread = mx - mn
        lines.append(f"Spread: {spread:.4f}s")

    return "\n".join(lines)


def memory_usage(filepath: str) -> str:
    """Estimate memory usage of a Python script by running it with tracemalloc.

    Returns peak and current memory after execution.
    """
    path = Path(filepath).expanduser().resolve()
    if not path.exists():
        return f"File not found: {filepath}"
    if path.suffix != ".py":
        return "Only Python scripts are supported."

    wrapper = (
        "import tracemalloc, importlib.util, sys\n"
        "tracemalloc.start()\n"
        f"spec = importlib.util.spec_from_file_location('_target', r'{path}')\n"
        "mod = importlib.util.module_from_spec(spec)\n"
        "try:\n"
        "    spec.loader.exec_module(mod)\n"
        "except SystemExit:\n"
        "    pass\n"
        "current, peak = tracemalloc.get_traced_memory()\n"
        "tracemalloc.stop()\n"
        f"print(f'current={{current/1024/1024:.2f}} MB')\n"
        f"print(f'peak={{peak/1024/1024:.2f}} MB')\n"
    )

    try:
        result = subprocess.run(
            [sys.executable, "-c", wrapper],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(path.parent),
        )
    except subprocess.TimeoutExpired:
        return "Script timed out after 60s."

    if result.returncode != 0:
        err = result.stderr.strip()[-500:] if result.stderr else "unknown error"
        return f"Script failed:\n{err}"

    return f"Memory usage for {path.name}:\n{result.stdout.strip()}"


def benchmark(command_a: str, command_b: str, runs: int = 5) -> str:
    """Compare two commands by timing both and reporting the difference.

    Args:
        command_a: First command.
        command_b: Second command.
        runs: Iterations per command (default 5, max 20).
    """
    runs = max(1, min(int(runs), 20))

    def _measure(cmd: str) -> list[float]:
        ts: list[float] = []
        for _ in range(runs):
            start = time.perf_counter()
            try:
                subprocess.run(cmd, shell=True, capture_output=True, timeout=120)
            except subprocess.TimeoutExpired:
                ts.append(120.0)
            ts.append(time.perf_counter() - start)
        return ts

    ta = _measure(command_a)
    tb = _measure(command_b)

    avg_a = sum(ta) / len(ta)
    avg_b = sum(tb) / len(tb)

    if avg_a < avg_b:
        faster = "A"
        pct = ((avg_b - avg_a) / avg_b) * 100
    else:
        faster = "B"
        pct = ((avg_a - avg_b) / avg_a) * 100

    lines = [
        f"Benchmark ({runs} runs each):",
        f"  A: {command_a}",
        f"     avg {avg_a:.4f}s  (min {min(ta):.4f}s, max {max(ta):.4f}s)",
        f"  B: {command_b}",
        f"     avg {avg_b:.4f}s  (min {min(tb):.4f}s, max {max(tb):.4f}s)",
        f"",
        f"  Winner: {faster} is {pct:.1f}% faster",
    ]
    return "\n".join(lines)
