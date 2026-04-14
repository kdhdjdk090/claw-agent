"""In-session todo / task-tracking — lightweight, non-persistent."""

from __future__ import annotations

import json
from typing import Any

# Session-scoped store — resets every conversation
_TODOS: dict[int, dict[str, Any]] = {}
_NEXT_ID = 1


def manage_todos(
    action: str = "list",
    todo_id: int | None = None,
    title: str = "",
    status: str = "not-started",
) -> str:
    """Manage an in-session todo list (not persisted to disk).

    Args:
        action: One of list, add, update, remove, clear.
        todo_id: Required for update / remove.
        title: Required for add; optional for update (to rename).
        status: One of not-started, in-progress, completed.
    """
    global _NEXT_ID

    action = action.lower().strip()

    if action == "list":
        if not _TODOS:
            return "Todo list is empty."
        lines = ["# In-Session Todos\n"]
        icons = {"not-started": "⬜", "in-progress": "🔄", "completed": "✅"}
        for tid in sorted(_TODOS):
            t = _TODOS[tid]
            icon = icons.get(t["status"], "⬜")
            lines.append(f"{icon} #{tid} [{t['status']}] {t['title']}")
        stats = {}
        for t in _TODOS.values():
            stats[t["status"]] = stats.get(t["status"], 0) + 1
        lines.append(f"\nTotal: {len(_TODOS)} — " +
                      ", ".join(f"{v} {k}" for k, v in sorted(stats.items())))
        return "\n".join(lines)

    if action == "add":
        if not title:
            return "Error: title is required for 'add'."
        tid = _NEXT_ID
        _NEXT_ID += 1
        _TODOS[tid] = {"title": title, "status": status}
        return f"✅ Added todo #{tid}: {title}"

    if action == "update":
        if todo_id is None or todo_id not in _TODOS:
            return f"Error: invalid todo_id {todo_id}."
        if title:
            _TODOS[todo_id]["title"] = title
        if status in ("not-started", "in-progress", "completed"):
            _TODOS[todo_id]["status"] = status
        t = _TODOS[todo_id]
        return f"Updated #{todo_id}: [{t['status']}] {t['title']}"

    if action == "remove":
        if todo_id is None or todo_id not in _TODOS:
            return f"Error: invalid todo_id {todo_id}."
        removed = _TODOS.pop(todo_id)
        return f"Removed #{todo_id}: {removed['title']}"

    if action == "clear":
        count = len(_TODOS)
        _TODOS.clear()
        _NEXT_ID = 1
        return f"Cleared {count} todo(s)."

    return f"Error: unknown action '{action}'. Use list, add, update, remove, or clear."
