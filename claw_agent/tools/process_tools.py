"""Process management tools — list, inspect, and kill processes."""

from __future__ import annotations

import os
import signal
import subprocess
import sys


def list_processes(filter_name: str = "", limit: int = 50) -> str:
    """List running processes, optionally filtered by name.

    Args:
        filter_name: Substring to filter process names (case-insensitive).
        limit: Max number of processes to return.
    """
    try:
        if sys.platform == "win32":
            cmd = ["tasklist", "/FO", "CSV", "/NH"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            lines = []
            for row in result.stdout.strip().splitlines():
                parts = [p.strip('"') for p in row.split('","')]
                if len(parts) >= 5:
                    name, pid, session, num, mem = parts[0], parts[1], parts[2], parts[3], parts[4]
                    if filter_name and filter_name.lower() not in name.lower():
                        continue
                    lines.append(f"  {pid:>8}  {mem:>12}  {name}")
            if not lines:
                return f"No processes found{' matching ' + repr(filter_name) if filter_name else ''}."
            header = f"{'PID':>10}  {'Memory':>12}  Name\n"
            return header + "\n".join(lines[:limit])
        else:
            cmd = ["ps", "aux"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            lines = []
            for row in result.stdout.strip().splitlines()[1:]:
                if filter_name and filter_name.lower() not in row.lower():
                    continue
                lines.append(row)
            if not lines:
                return f"No processes found{' matching ' + repr(filter_name) if filter_name else ''}."
            header = result.stdout.strip().splitlines()[0] + "\n"
            return header + "\n".join(lines[:limit])

    except Exception as e:
        return f"Error listing processes: {type(e).__name__}: {e}"


def kill_process(pid: int, force: bool = False) -> str:
    """Kill a process by PID.

    Args:
        pid: Process ID to kill.
        force: If True, force-kill (SIGKILL / taskkill /F).
    """
    if pid <= 0:
        return "Error: invalid PID."

    try:
        if sys.platform == "win32":
            cmd = ["taskkill", "/PID", str(pid)]
            if force:
                cmd.append("/F")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            output = (result.stdout + result.stderr).strip()
            if result.returncode == 0:
                return f"✅ Killed process {pid}.\n{output}"
            else:
                return f"❌ Failed to kill process {pid}:\n{output}"
        else:
            sig = signal.SIGKILL if force else signal.SIGTERM
            os.kill(pid, sig)
            return f"✅ Sent {'SIGKILL' if force else 'SIGTERM'} to process {pid}."

    except ProcessLookupError:
        return f"Error: no process with PID {pid}."
    except PermissionError:
        return f"Error: permission denied to kill PID {pid}."
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"
