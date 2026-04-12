"""Session persistence — save/load/resume conversations."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

DEFAULT_SESSION_DIR = Path.home() / ".claw-agent" / "sessions"


@dataclass
class Session:
    session_id: str = field(default_factory=lambda: uuid4().hex[:12])
    model: str = ""
    messages: list[dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    total_turns: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    tags: list[str] = field(default_factory=list)
    title: str = ""

    def auto_title(self) -> str:
        """Generate a title from the first user message."""
        for msg in self.messages:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str) and content.strip():
                    return content.strip()[:60]
        return "Untitled session"


def save_session(session: Session, directory: Path | None = None) -> Path:
    target = directory or DEFAULT_SESSION_DIR
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"{session.session_id}.json"

    data = {
        "session_id": session.session_id,
        "model": session.model,
        "messages": session.messages,
        "created_at": session.created_at,
        "updated_at": time.time(),
        "total_turns": session.total_turns,
        "input_tokens": session.input_tokens,
        "output_tokens": session.output_tokens,
        "tags": session.tags,
        "title": session.title or session.auto_title(),
    }
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    return path


def load_session(session_id: str, directory: Path | None = None) -> Session:
    target = directory or DEFAULT_SESSION_DIR
    path = target / f"{session_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Session not found: {session_id}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return Session(
        session_id=data["session_id"],
        model=data.get("model", ""),
        messages=data.get("messages", []),
        created_at=data.get("created_at", 0),
        updated_at=data.get("updated_at", 0),
        total_turns=data.get("total_turns", 0),
        input_tokens=data.get("input_tokens", 0),
        output_tokens=data.get("output_tokens", 0),
        tags=data.get("tags", []),
        title=data.get("title", ""),
    )


def list_sessions(directory: Path | None = None) -> list[Session]:
    target = directory or DEFAULT_SESSION_DIR
    if not target.exists():
        return []
    sessions = []
    for path in sorted(target.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            sessions.append(Session(
                session_id=data["session_id"],
                model=data.get("model", ""),
                messages=data.get("messages", []),
                created_at=data.get("created_at", 0),
                updated_at=data.get("updated_at", 0),
                total_turns=data.get("total_turns", 0),
                input_tokens=data.get("input_tokens", 0),
                output_tokens=data.get("output_tokens", 0),
                tags=data.get("tags", []),
                title=data.get("title", ""),
            ))
        except (json.JSONDecodeError, KeyError):
            continue
    return sessions


def delete_session(session_id: str, directory: Path | None = None) -> bool:
    target = directory or DEFAULT_SESSION_DIR
    path = target / f"{session_id}.json"
    if path.exists():
        path.unlink()
        return True
    return False
