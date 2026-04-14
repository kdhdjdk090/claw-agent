"""Backup tools — create, restore, and list timestamped file backups."""

from __future__ import annotations

import shutil
import time
from pathlib import Path

_BACKUP_DIR = Path.home() / ".claw" / "backups"


def _ensure_dir() -> Path:
    _BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    return _BACKUP_DIR


def backup_file(filepath: str) -> str:
    """Create a timestamped backup copy of a file.

    Backups are stored in ``~/.claw/backups/<filename>.<timestamp>``
    """
    src = Path(filepath).expanduser().resolve()
    if not src.exists():
        return f"File not found: {filepath}"
    if not src.is_file():
        return f"Not a file: {filepath}"

    d = _ensure_dir()
    ts = time.strftime("%Y%m%d_%H%M%S")
    dst = d / f"{src.name}.{ts}"
    shutil.copy2(str(src), str(dst))
    size = dst.stat().st_size
    return f"Backed up {src.name} → {dst.name}  ({size:,} bytes)"


def restore_backup(backup_name: str, restore_to: str) -> str:
    """Restore a file from a named backup.

    Parameters
    ----------
    backup_name : str
        The backup filename (as shown by ``list_backups``).
    restore_to : str
        Destination path to restore the file to.
    """
    d = _ensure_dir()
    src = d / backup_name

    if not src.exists():
        return f"Backup not found: {backup_name}"

    dst = Path(restore_to).expanduser().resolve()
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src), str(dst))
    return f"Restored {backup_name} → {dst}"


def list_backups(filename: str = "") -> str:
    """List available backups, optionally filtered by original filename.

    Parameters
    ----------
    filename : str
        If provided, only show backups whose name starts with this value.
    """
    d = _ensure_dir()
    files = sorted(d.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)

    if filename:
        files = [f for f in files if f.name.startswith(filename)]

    if not files:
        label = f" for '{filename}'" if filename else ""
        return f"No backups found{label}."

    lines: list[str] = []
    for f in files[:40]:
        sz = f.stat().st_size
        mt = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(f.stat().st_mtime))
        lines.append(f"  {f.name}  ({sz:,} bytes, {mt})")

    return f"{len(files)} backup(s):\n" + "\n".join(lines)
