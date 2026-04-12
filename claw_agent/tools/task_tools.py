"""Task management — structured async task tracking."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

TASK_DIR = Path.home() / ".claw-agent" / "tasks"


@dataclass
class Task:
    task_id: str = field(default_factory=lambda: uuid4().hex[:8])
    title: str = ""
    status: str = "pending"  # pending, in_progress, completed, failed
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    result: str = ""
    steps: list[str] = field(default_factory=list)
    parent_id: str = ""


def _save(task: Task) -> Path:
    TASK_DIR.mkdir(parents=True, exist_ok=True)
    path = TASK_DIR / f"{task.task_id}.json"
    path.write_text(json.dumps(asdict(task), indent=2), encoding="utf-8")
    return path


def _load(task_id: str) -> Task | None:
    path = TASK_DIR / f"{task_id}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return Task(**data)


def task_create(title: str, steps: str = "") -> str:
    """Create a new task with optional steps (newline-separated)."""
    step_list = [s.strip() for s in steps.split("\n") if s.strip()] if steps else []
    task = Task(title=title, steps=step_list)
    _save(task)
    return f"Created task {task.task_id}: {title}" + (
        f" ({len(step_list)} steps)" if step_list else ""
    )


def task_update(task_id: str, status: str = "", result: str = "") -> str:
    """Update a task's status and/or result."""
    task = _load(task_id)
    if not task:
        return f"Error: task {task_id} not found"
    if status:
        task.status = status
    if result:
        task.result = result
    task.updated_at = time.time()
    _save(task)
    return f"Updated task {task_id}: status={task.status}"


def task_list(status_filter: str = "") -> str:
    """List all tasks, optionally filtered by status."""
    TASK_DIR.mkdir(parents=True, exist_ok=True)
    tasks = []
    for path in sorted(TASK_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            t = Task(**data)
            if status_filter and t.status != status_filter:
                continue
            tasks.append(t)
        except Exception:
            continue

    if not tasks:
        return "No tasks found." + (f" (filter: {status_filter})" if status_filter else "")

    lines = []
    for t in tasks[:20]:
        icon = {"pending": "( )", "in_progress": "(.)", "completed": "(*)", "failed": "(X)"}.get(t.status, "?")
        lines.append(f"  {icon} [{t.task_id}] {t.title} ({t.status})")
    return "\n".join(lines)


def task_get(task_id: str) -> str:
    """Get details of a specific task."""
    task = _load(task_id)
    if not task:
        return f"Error: task {task_id} not found"
    lines = [
        f"Task: {task.title}",
        f"ID: {task.task_id}",
        f"Status: {task.status}",
        f"Created: {time.ctime(task.created_at)}",
    ]
    if task.steps:
        lines.append("Steps:")
        for i, step in enumerate(task.steps, 1):
            lines.append(f"  {i}. {step}")
    if task.result:
        lines.append(f"Result: {task.result}")
    return "\n".join(lines)
