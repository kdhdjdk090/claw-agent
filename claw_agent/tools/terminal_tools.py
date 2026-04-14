"""Persistent terminal sessions — async command execution with output retrieval."""

from __future__ import annotations

import subprocess
import threading
import time
import uuid
from dataclasses import dataclass, field
from io import StringIO
from typing import Optional


@dataclass
class TerminalSession:
    """A persistent terminal session that captures output."""
    id: str
    process: Optional[subprocess.Popen] = None
    output: StringIO = field(default_factory=StringIO)
    is_alive: bool = True
    started_at: float = field(default_factory=time.time)
    command: str = ""


# Active sessions
_sessions: dict[str, TerminalSession] = {}


def _output_reader(session: TerminalSession):
    """Background thread to read process stdout."""
    proc = session.process
    if not proc or not proc.stdout:
        return
    try:
        for line in proc.stdout:
            session.output.write(line)
    except Exception:
        pass
    finally:
        session.is_alive = False


def terminal_run_async(command: str, cwd: str = ".") -> str:
    """Run a command in a persistent async terminal session.

    Returns a session ID to retrieve output later with terminal_get_output.
    """
    session_id = str(uuid.uuid4())
    try:
        proc = subprocess.Popen(
            ["powershell", "-NoProfile", "-Command", command],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            text=True,
            cwd=cwd,
            bufsize=1,
        )
        session = TerminalSession(id=session_id, process=proc, command=command)
        _sessions[session_id] = session

        # Start output reader thread
        reader = threading.Thread(target=_output_reader, args=(session,), daemon=True)
        reader.start()

        return f"Terminal session started.\nID: {session_id}\nCommand: {command}\nUse terminal_get_output('{session_id}') to check output."
    except Exception as e:
        return f"Error starting terminal: {e}"


def terminal_get_output(session_id: str) -> str:
    """Get output from an async terminal session."""
    session = _sessions.get(session_id)
    if not session:
        return f"No terminal session with ID: {session_id}"

    output = session.output.getvalue()
    status = "running" if session.is_alive else "finished"
    elapsed = time.time() - session.started_at

    lines = output.splitlines()
    if len(lines) > 200:
        # Truncate to last 200 lines
        output = "\n".join(lines[-200:])
        output = f"[... truncated {len(lines) - 200} lines ...]\n" + output

    return f"Terminal [{status}] (elapsed: {elapsed:.1f}s)\nCommand: {session.command}\n---\n{output}"


def terminal_send(session_id: str, text: str) -> str:
    """Send input to a running terminal session."""
    session = _sessions.get(session_id)
    if not session:
        return f"No terminal session with ID: {session_id}"
    if not session.is_alive or not session.process or not session.process.stdin:
        return "Terminal session is not running."
    try:
        session.process.stdin.write(text + "\n")
        session.process.stdin.flush()
        return f"Sent to terminal {session_id}: {text}"
    except Exception as e:
        return f"Error sending input: {e}"


def terminal_kill(session_id: str) -> str:
    """Kill a terminal session."""
    session = _sessions.get(session_id)
    if not session:
        return f"No terminal session with ID: {session_id}"
    if session.process:
        try:
            session.process.kill()
        except Exception:
            pass
    session.is_alive = False
    output = session.output.getvalue()
    del _sessions[session_id]
    return f"Terminal {session_id} killed.\nFinal output ({len(output)} chars captured)."


def terminal_list() -> str:
    """List all active terminal sessions."""
    if not _sessions:
        return "No active terminal sessions."
    lines = ["Active terminals:"]
    for sid, s in _sessions.items():
        status = "running" if s.is_alive else "finished"
        elapsed = time.time() - s.started_at
        lines.append(f"  {sid[:12]}… [{status}] {elapsed:.0f}s — {s.command[:60]}")
    return "\n".join(lines)
